from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict
import asyncio
import os
import requests
import hmac
import hashlib
import json
import jwt
import time
from contextlib import asynccontextmanager

from .database import get_db, create_tables, AsyncSessionLocal
from .models import GitHubIssue, DevinSession, GitHubUser, Repository
from .github_client import GitHubClient
from .devin_client import DevinClient

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    await sync_user_repositories()
    yield

app = FastAPI(lifespan=lifespan)

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

github_client = GitHubClient()
devin_client = None
try:
    devin_client = DevinClient()
except ValueError as e:
    print(f"Warning: Devin client not initialized: {e}")
    devin_client = None

async def sync_user_repositories():
    """Sync repositories for all GitHub users with installation_id"""
    print("Starting repository sync for all GitHub users...")
    
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(GitHubUser))
            users = result.scalars().all()
            
            for user in users:
                if not user.installation_id:
                    print(f"Skipping user {user.username} - no installation_id")
                    continue
                    
                print(f"Syncing repositories for user: {user.username}")
                
                try:
                    repositories = github_client.get_installation_repositories(user.installation_id)
                    
                    for repo_data in repositories:
                        repo_name = repo_data.get('name')
                        if not repo_name:
                            continue
                            
                        existing_repo_result = await db.execute(
                            select(Repository).where(
                                Repository.name == repo_name,
                                Repository.github_user == user.id
                            )
                        )
                        existing_repo = existing_repo_result.scalar_one_or_none()
                        
                        if existing_repo:
                            print(f"  Repository {repo_name} already exists, updating...")
                        else:
                            new_repo = Repository(
                                name=repo_name,
                                github_user=user.id
                            )
                            db.add(new_repo)
                            print(f"  Added new repository: {repo_name}")
                    
                    await db.commit()
                    print(f"Successfully synced repositories for {user.username}")
                    
                except Exception as e:
                    print(f"Error syncing repositories for user {user.username}: {e}")
                    await db.rollback()
                    continue
                    
        except Exception as e:
            print(f"Error during repository sync: {e}")
            
    print("Repository sync completed")

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/test-github")
async def test_github():
    """Test GitHub API integration without database"""
    try:
        issues = github_client.get_repository_issues("octocat", "Hello-World", "open")
        return {
            "status": "success",
            "message": "GitHub API working",
            "issues_count": len(issues),
            "sample_issue": issues[0] if issues else None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"GitHub API error: {str(e)}"
        }

@app.get("/test-devin")
async def test_devin():
    """Test Devin API integration without database"""
    try:
        if not devin_client:
            return {
                "status": "error",
                "message": "Devin API not available - client not initialized",
                "session_created": False
            }
        
        prompt = devin_client.generate_scope_prompt(
            "Sample Issue Title",
            "This is a sample issue description for testing the Devin API integration.",
            "octocat/Hello-World"
        )
        
        session_data = devin_client.create_session(prompt)
        
        if session_data:
            return {
                "status": "success",
                "message": "Devin API working",
                "session_created": True,
                "session_id": session_data.get("session_id", "unknown"),
                "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt
            }
        else:
            return {
                "status": "error",
                "message": "Failed to create Devin session",
                "session_created": False
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Devin API error: {str(e)}",
            "session_created": False
        }

@app.get("/issues/{owner}/{repo}")
async def get_repository_issues(
    owner: str, 
    repo: str, 
    request: Request,
    state: str = "open",
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get issues from a GitHub repository and store them in database"""
    try:
        github_token = request.headers.get('X-GitHub-Token')
        
        if github_token:
            client = GitHubClient(token=github_token)
        else:
            client = github_client
            
        issues = client.get_repository_issues(owner, repo, state)
        
        filtered_issues = [issue for issue in issues if 'pull_request' not in issue]
        limited_issues = filtered_issues[:limit] if filtered_issues else []
        
        stored_issues = []
        for issue in limited_issues:
            try:
                print(f"Processing issue: {issue['id']} - {issue['title']}")
                result = await db.execute(
                    select(GitHubIssue).where(GitHubIssue.github_issue_id == issue["id"])
                )
                existing_issue = result.scalar_one_or_none()
                
                if existing_issue:
                    print(f"Updating existing issue: {existing_issue.id}")
                    existing_issue.title = issue["title"]
                    existing_issue.body = issue.get("body", "")
                    existing_issue.state = issue["state"]
                    existing_issue.repository = f"{owner}/{repo}"
                    existing_issue.html_url = issue["html_url"]
                    existing_issue.ref_id_number = issue.get("number", 0)
                    stored_issue = existing_issue
                else:
                    print(f"Creating new issue: {issue['id']}")
                    new_issue = GitHubIssue(
                        github_issue_id=issue["id"],
                        title=issue["title"],
                        body=issue.get("body", ""),
                        state=issue["state"],
                        repository=f"{owner}/{repo}",
                        html_url=issue["html_url"],
                        ref_id_number=issue.get("number", 0)
                    )
                    db.add(new_issue)
                    stored_issue = new_issue
                
                print("Committing to database...")
                await db.commit()
                print("Refreshing stored issue...")
                await db.refresh(stored_issue)
                
                print("Getting issue state...")
                issue_state = await stored_issue.get_state(db)
                print(f"Issue state: {issue_state}")
                
                stored_issues.append({
                    "id": stored_issue.id,
                    "github_issue_id": stored_issue.github_issue_id,
                    "number": issue["number"],
                    "ref_id_number": stored_issue.ref_id_number or 0,
                    "html_url": issue["html_url"],
                    "title": stored_issue.title,
                    "body": stored_issue.body,
                    "state": stored_issue.state,
                    "repository": stored_issue.repository,
                    "issue_state": issue_state,
                    "created_at": stored_issue.created_at,
                    "updated_at": stored_issue.updated_at
                })
                print(f"Successfully processed issue: {issue['id']}")
            except Exception as e:
                print(f"Error processing issue {issue['id']}: {str(e)}")
                print(f"Error type: {type(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                raise e
        
        return {
            "repository": f"{owner}/{repo}",
            "issues": stored_issues
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch issues: {str(e)}")

@app.post("/issues/{issue_id}/scope")
async def scope_issue(
    issue_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Create a Devin session to scope an issue and assign confidence score"""
    result = await db.execute(
        select(GitHubIssue).where(GitHubIssue.id == issue_id)
    )
    issue = result.scalar_one_or_none()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    if not devin_client:
        raise HTTPException(status_code=503, detail="Devin API not available")
    
    prompt = devin_client.generate_scope_prompt(
        issue.title, 
        issue.body, 
        issue.repository
    )
    
    session_title = f"(scope) {issue.title}"
    session_data = devin_client.create_session(prompt, title=session_title)
    
    if not session_data:
        raise HTTPException(status_code=500, detail="Failed to create Devin session")
    
    devin_session = DevinSession(
        github_issue_id=issue.id,
        session_id=session_data.get("session_id", ""),
        session_type="scope",
        status="pending"
    )
    db.add(devin_session)
    await db.commit()
    await db.refresh(devin_session)
    
    return {
        "session_id": devin_session.session_id,
        "status": devin_session.status,
        "issue_id": issue_id
    }

@app.get("/issues/{issue_id}")
async def get_issue_with_confidence(
    issue_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get issue details with current confidence score for polling"""
    result = await db.execute(
        select(GitHubIssue).where(GitHubIssue.id == issue_id)
    )
    issue = result.scalar_one_or_none()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    scope_result = await db.execute(
        select(DevinSession).where(
            DevinSession.github_issue_id == issue.id,
            DevinSession.session_type == "scope"
        ).order_by(DevinSession.created_at.desc())
    )
    scope_session = scope_result.scalars().first()
    
    current_confidence = "not yet"
    
    if scope_session and scope_session.confidence_score is not None:
        current_confidence = scope_session.confidence_score
    elif scope_session and devin_client:
        print(f"DEBUG: Polling Devin API for session {scope_session.session_id}")
        devin_status = devin_client.get_session_status(scope_session.session_id)
        print(f"DEBUG: Devin API response type: {type(devin_status)}")
        print(f"DEBUG: Devin API response keys: {list(devin_status.keys()) if isinstance(devin_status, dict) else 'Not a dict'}")
        if devin_status and "structured_output" in devin_status:
            structured_output = devin_status["structured_output"]
            print(f"DEBUG: Structured output found: {structured_output}")
            print(f"DEBUG: Structured output type: {type(structured_output)}")
            if isinstance(structured_output, dict) and "confidence_score" in structured_output:
                confidence_score = structured_output["confidence_score"]
                print(f"DEBUG: Confidence score extracted: {confidence_score}")
                scope_session.confidence_score = confidence_score
                if "action_plan" in structured_output:
                    scope_session.action_plan = structured_output["action_plan"]
                if "analysis" in structured_output:
                    scope_session.result = structured_output["analysis"]
                await db.commit()
                current_confidence = confidence_score
            else:
                print(f"DEBUG: No confidence_score in structured_output or not a dict")
                print(f"DEBUG: structured_output keys: {list(structured_output.keys()) if isinstance(structured_output, dict) else 'Not a dict'}")
        else:
            print(f"DEBUG: No structured_output in devin_status or devin_status is None")
    
    return {
        "issue_id": issue.id,
        "title": issue.title,
        "current_confidence": current_confidence,
        "analysis": scope_session.result if scope_session and scope_session.result else None
    }

@app.post("/issues/{issue_id}/execute")
async def execute_issue(
    issue_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Create a Devin session to execute an issue based on action plan"""
    result = await db.execute(
        select(GitHubIssue).where(GitHubIssue.id == issue_id)
    )
    issue = result.scalar_one_or_none()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    scope_result = await db.execute(
        select(DevinSession).where(
            DevinSession.github_issue_id == issue.id,
            DevinSession.session_type == "scope"
        ).order_by(DevinSession.created_at.desc())
    )
    scope_session = scope_result.scalars().first()
    
    if not scope_session or not scope_session.action_plan:
        raise HTTPException(
            status_code=400, 
            detail="Issue must be scoped first with an action plan"
        )
    
    if not devin_client:
        raise HTTPException(status_code=503, detail="Devin API not available")
    
    prompt = devin_client.generate_execution_prompt(
        issue.title,
        issue.body,
        scope_session.action_plan,
        issue.repository
    )
    
    session_data = devin_client.create_session(prompt)
    
    if not session_data:
        raise HTTPException(status_code=500, detail="Failed to create Devin session")
    
    devin_session = DevinSession(
        github_issue_id=issue.id,
        session_id=session_data.get("session_id", ""),
        session_type="execute",
        status="pending"
    )
    db.add(devin_session)
    await db.commit()
    await db.refresh(devin_session)
    
    return {
        "session_id": devin_session.session_id,
        "status": devin_session.status,
        "issue_id": issue_id
    }

@app.get("/sessions/{session_id}")
async def get_session_status(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the status of a Devin session"""
    result = await db.execute(
        select(DevinSession).where(DevinSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    devin_status = None
    if devin_client:
        devin_status = devin_client.get_session_status(session_id)
    
    if devin_status:
        session.status = devin_status.get("status", session.status)
        if "confidence_score" in devin_status:
            session.confidence_score = devin_status["confidence_score"]
        if "action_plan" in devin_status:
            session.action_plan = devin_status["action_plan"]
        if "result" in devin_status:
            session.result = devin_status["result"]
        
        await db.commit()
        await db.refresh(session)
    
    return {
        "session_id": session.session_id,
        "github_issue_id": session.github_issue_id,
        "session_type": session.session_type,
        "status": session.status,
        "confidence_score": session.confidence_score,
        "action_plan": session.action_plan,
        "result": session.result,
        "created_at": session.created_at,
        "updated_at": session.updated_at
    }

@app.get("/user/repos")
async def get_user_repositories(request: Request):
    """Get user's accessible repositories using GitHub token"""
    try:
        github_token = request.headers.get('X-GitHub-Token')
        
        if not github_token:
            raise HTTPException(status_code=400, detail="GitHub token is required")
        
        client = GitHubClient(token=github_token)
        
        user_url = f"{client.base_url}/user"
        repos_url = f"{client.base_url}/user/repos"
        
        user_response = requests.get(user_url, headers=client.headers)
        repos_response = requests.get(repos_url, headers=client.headers, params={"per_page": 50, "sort": "updated"})
        
        if user_response.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid GitHub token")
        
        user_response.raise_for_status()
        repos_response.raise_for_status()
        
        user_data = user_response.json()
        repos_data = repos_response.json()
        
        return {
            "user": {
                "login": user_data.get("login"),
                "name": user_data.get("name"),
                "avatar_url": user_data.get("avatar_url")
            },
            "repositories": [
                {
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "owner": repo["owner"]["login"],
                    "private": repo["private"],
                    "description": repo.get("description", ""),
                    "updated_at": repo.get("updated_at", "")
                }
                for repo in repos_data
            ]
        }
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"GitHub API error: {str(e)}")

@app.get("/github-app-status")
async def get_github_app_status():
    """Get GitHub App authentication status and configuration"""
    try:
        app_id = os.getenv("Github_App_app_id")
        private_key = os.getenv("GITHUB_PEM")
        installation_id = os.getenv("github_app_install_id")
        
        if not app_id or not private_key or not installation_id:
            return {
                "configured": False,
                "message": "GitHub App not configured",
                "missing_credentials": [
                    key for key, value in {
                        "Github_App_app_id": app_id,
                        "GITHUB_PEM": private_key,
                        "github_app_install_id": installation_id
                    }.items() if not value
                ],
                "note": "Please configure GitHub App credentials to use GitHub App authentication"
            }
        
        try:
            client = GitHubClient(app_id=app_id, private_key=private_key, installation_id=installation_id)
            test_url = f"{client.base_url}/app/installations/{installation_id}"
            response = requests.get(test_url, headers=client.headers)
            
            if response.status_code == 200:
                installation_data = response.json()
                return {
                    "configured": True,
                    "message": "GitHub App authentication working",
                    "app_id": app_id,
                    "installation_id": installation_id,
                    "account": installation_data.get("account", {}).get("login", "Unknown"),
                    "permissions": installation_data.get("permissions", {}),
                    "repository_selection": installation_data.get("repository_selection", "unknown")
                }
            else:
                return {
                    "configured": False,
                    "message": "GitHub App authentication failed",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        except Exception as auth_error:
            return {
                "configured": False,
                "message": "GitHub App authentication error",
                "error": str(auth_error)
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking GitHub App status: {str(e)}")

@app.post("/test-devin-issue-url")
async def test_devin_issue_url():
    """Test creating a Devin session with just a GitHub issue URL"""
    if not devin_client:
        raise HTTPException(status_code=503, detail="Devin API not available")
    
    issue_url = "https://github.com/alexandertmills/devin-issues-automation/issues/7"
    
    github_token = None
    if github_client and hasattr(github_client, 'headers') and 'Authorization' in github_client.headers:
        auth_header = github_client.headers['Authorization']
        if auth_header.startswith('token '):
            github_token = auth_header[6:]  # Remove "token " prefix
    
    prompt_url_only = f"""
Please analyze this GitHub issue and provide a confidence score for how actionable it is.

Repository: alexandertmills/devin-issues-automation
Issue URL: {issue_url}

Please fetch the issue details from the repository and provide:
1. A confidence score (0-100) for how well-defined and actionable this issue is
2. A brief analysis of what needs to be done

Format your response as:
CONFIDENCE_SCORE: [0-100]
ANALYSIS: [Your analysis]
"""
    
    session_data_url = devin_client.create_session(prompt_url_only)
    
    return {
        "test_type": "url_only",
        "issue_url": issue_url,
        "session_data": session_data_url,
        "prompt_used": prompt_url_only
    }

@app.post("/test-devin-issue-content")
async def test_devin_issue_content():
    """Test creating a Devin session with full issue content"""
    if not devin_client:
        raise HTTPException(status_code=503, detail="Devin API not available")
    
    issue_title = "Needs moar cowbell."
    issue_body = "Cowbell. It needs moar of it!!"
    issue_url = "https://github.com/alexandertmills/devin-issues-automation/issues/7"
    repo_name = "alexandertmills/devin-issues-automation"
    
    prompt_with_content = f"""
Please analyze this GitHub issue and provide a confidence score for how actionable it is.

Repository: {repo_name}
Issue URL: {issue_url}
Issue Title: {issue_title}
Issue Description: {issue_body}

Please provide:
1. A confidence score (0-100) for how well-defined and actionable this issue is
2. A brief analysis of what needs to be done

Format your response as:
CONFIDENCE_SCORE: [0-100]
ANALYSIS: [Your analysis]
"""
    
    session_data_content = devin_client.create_session(prompt_with_content)
    
    return {
        "test_type": "full_content",
        "issue_url": issue_url,
        "issue_title": issue_title,
        "issue_body": issue_body,
        "session_data": session_data_content,
        "prompt_used": prompt_with_content
    }

@app.post("/test-devin-approaches-comparison")
async def test_devin_approaches_comparison():
    """Compare URL-only vs full-content approaches for Devin issue analysis"""
    if not devin_client:
        raise HTTPException(status_code=503, detail="Devin API not available")
    
    url_result = await test_devin_issue_url()
    content_result = await test_devin_issue_content()
    
    return {
        "comparison": {
            "url_only_approach": url_result,
            "full_content_approach": content_result
        },
        "summary": "Testing whether Devin can access GitHub repos via URL vs needs full content"
    }

@app.get("/dashboard")
async def get_dashboard_data(db: AsyncSession = Depends(get_db)):
    """Get dashboard data with issues and their associated sessions"""
    issues_result = await db.execute(select(GitHubIssue))
    issues = issues_result.scalars().all()
    
    dashboard_data = []
    for issue in issues:
        scope_result = await db.execute(
            select(DevinSession).where(
                DevinSession.github_issue_id == issue.id,
                DevinSession.session_type == "scope"
            ).order_by(DevinSession.created_at.desc()).limit(1)
        )
        scope_session = scope_result.scalar_one_or_none()
        
        exec_result = await db.execute(
            select(DevinSession).where(
                DevinSession.github_issue_id == issue.id,
                DevinSession.session_type == "execute"
            ).order_by(DevinSession.created_at.desc()).limit(1)
        )
        exec_session = exec_result.scalar_one_or_none()
        
        dashboard_data.append({
            "issue": {
                "id": issue.id,
                "github_issue_id": issue.github_issue_id,
                "title": issue.title,
                "body": issue.body,
                "state": issue.state,
                "repository": issue.repository,
                "issue_state": await issue.get_state(db),
                "created_at": issue.created_at,
                "updated_at": issue.updated_at
            },
            "scope_session": {
                "session_id": scope_session.session_id if scope_session else None,
                "status": scope_session.status if scope_session else None,
                "confidence_score": scope_session.confidence_score if scope_session else None,
                "action_plan": scope_session.action_plan if scope_session else None,
                "result": scope_session.result if scope_session else None,
                "created_at": scope_session.created_at if scope_session else None
            } if scope_session else None,
            "execution_session": {
                "session_id": exec_session.session_id if exec_session else None,
                "status": exec_session.status if exec_session else None,
                "result": exec_session.result if exec_session else None,
                "created_at": exec_session.created_at if exec_session else None
            } if exec_session else None
        })
    
    return {"dashboard": dashboard_data}


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify the webhook signature from GitHub"""
    if not signature or not secret:
        return False
    
    expected_signature = "sha256=" + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)


async def handle_installation_event(payload: Dict) -> Dict:
    """Handle GitHub App installation events"""
    action = payload.get("action")
    installation = payload.get("installation", {})
    installation_id = installation.get("id")
    
    if action == "created":
        print(f"GitHub App installed on installation ID: {installation_id}")
        repositories = payload.get("repositories", [])
        for repo in repositories:
            print(f"App installed on repository: {repo.get('full_name')}")
    
    elif action == "deleted":
        print(f"GitHub App uninstalled from installation ID: {installation_id}")
    
    return {"status": "success", "action": action, "installation_id": installation_id}


async def handle_issue_event(payload: Dict) -> Dict:
    """Handle GitHub issue events"""
    action = payload.get("action")
    issue = payload.get("issue", {})
    repository = payload.get("repository", {})
    
    issue_data = {
        "github_issue_id": issue.get("id"),
        "title": issue.get("title"),
        "body": issue.get("body", ""),
        "state": issue.get("state"),
        "repository": repository.get("full_name"),
        "number": issue.get("number")
    }
    
    print(f"Issue {action}: #{issue_data['number']} {issue_data['title']} in {issue_data['repository']}")
    
    return {"status": "success", "action": action, "issue": issue_data}


@app.post("/webhook")
async def github_webhook(request: Request):
    """Handle GitHub webhook events"""
    try:
        signature = request.headers.get("X-Hub-Signature-256")
        event_type = request.headers.get("X-GitHub-Event")
        delivery_id = request.headers.get("X-GitHub-Delivery")
        
        payload_bytes = await request.body()
        
        webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
        if webhook_secret and not verify_webhook_signature(payload_bytes, signature, webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        payload = json.loads(payload_bytes.decode())
        
        print(f"Received webhook: {event_type} (delivery: {delivery_id})")
        
        if event_type == "installation":
            return await handle_installation_event(payload)
        elif event_type == "issues":
            return await handle_issue_event(payload)
        elif event_type == "issue_comment":
            comment = payload.get("comment", {})
            issue = payload.get("issue", {})
            print(f"Issue comment {payload.get('action')}: {comment.get('body', '')[:100]}... on issue #{issue.get('number')}")
            return {"status": "success", "event": "issue_comment"}
        elif event_type == "ping":
            return {"status": "success", "message": "Webhook ping received", "zen": payload.get("zen")}
        else:
            print(f"Unhandled webhook event: {event_type}")
            return {"status": "success", "event": event_type, "message": "Event received but not handled"}
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")


@app.get("/webhook/status")
async def webhook_status():
    """Check webhook configuration status"""
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    
    return {
        "webhook_secret_configured": bool(webhook_secret),
        "supported_events": ["installation", "issues", "issue_comment", "ping"],
        "webhook_endpoint": "/webhook",
        "signature_verification": "enabled" if webhook_secret else "disabled",
        "note": "Configure GITHUB_WEBHOOK_SECRET environment variable for signature verification"
    }

@app.get("/app/repositories")
async def get_app_repositories():
    """Get repositories accessible to the GitHub App installation and sync to database"""
    try:
        if not github_client or not hasattr(github_client, 'app_id'):
            raise HTTPException(status_code=503, detail="GitHub App not configured")
        
        repositories = github_client.get_installation_repositories(github_client.installation_id)
        
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(GitHubUser).where(GitHubUser.installation_id == github_client.installation_id)
                )
                user = result.scalar_one_or_none()
                
                if user:
                    for repo_data in repositories:
                        repo_name = repo_data.get('name')
                        if not repo_name:
                            continue
                            
                        existing_repo_result = await db.execute(
                            select(Repository).where(
                                Repository.name == repo_name,
                                Repository.github_user == user.id
                            )
                        )
                        existing_repo = existing_repo_result.scalar_one_or_none()
                        
                        if not existing_repo:
                            # Create new repository
                            new_repo = Repository(
                                name=repo_name,
                                github_user=user.id
                            )
                            db.add(new_repo)
                    
                    await db.commit()
            except Exception as e:
                print(f"Error syncing repositories to database: {e}")
                await db.rollback()
        
        return {
            "repositories": [
                {
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "owner": repo["owner"]["login"],
                    "private": repo["private"],
                    "description": repo.get("description", "")
                }
                for repo in repositories
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching repositories: {str(e)}")

@app.post("/app/repositories/sync")
async def sync_repositories():
    """Manually trigger repository sync for all GitHub users"""
    try:
        await sync_user_repositories()
        return {"message": "Repository sync completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing repositories: {str(e)}")

@app.post("/verify-installation")
async def verify_installation(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Verify GitHub App installation ID and add new user"""
    try:
        data = await request.json()
        installation_id = data.get("installation_id")
        
        if not installation_id:
            raise HTTPException(status_code=400, detail="Installation ID is required")
        
        app_id = os.getenv("Github_App_app_id")
        private_key = os.getenv("GITHUB_PEM")
        
        if not app_id or not private_key:
            raise HTTPException(status_code=503, detail="GitHub App not configured")
        
        try:
            now = int(time.time())
            payload = {
                'iat': now,
                'exp': now + 600,  # 10 minutes
                'iss': app_id
            }
            jwt_token = jwt.encode(payload, private_key, algorithm='RS256')
            
            test_url = f"https://api.github.com/app/installations/{installation_id}"
            headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get(test_url, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid installation ID")
            
            installation_data = response.json()
            username = installation_data.get("account", {}).get("login")
            
            if not username:
                raise HTTPException(status_code=400, detail="Could not fetch username from installation")
            
            result = await db.execute(
                select(GitHubUser).where(GitHubUser.username == username)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                existing_user.installation_id = installation_id
                await db.commit()
                return {"success": True, "username": username, "message": "User updated successfully"}
            else:
                new_user = GitHubUser(
                    username=username,
                    installation_id=installation_id
                )
                db.add(new_user)
                await db.commit()
                return {"success": True, "username": username, "message": "User added successfully"}
                
        except requests.RequestException as e:
            raise HTTPException(status_code=400, detail=f"Failed to verify installation: {str(e)}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")

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
from contextlib import asynccontextmanager

from .database import get_db, create_tables
from .models import GitHubIssue, DevinSession
from .github_client import GitHubClient
from .devin_client import DevinClient

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
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
            result = await db.execute(
                select(GitHubIssue).where(GitHubIssue.github_issue_id == issue["id"])
            )
            existing_issue = result.scalar_one_or_none()
            
            if existing_issue:
                existing_issue.title = issue["title"]
                existing_issue.body = issue.get("body", "")
                existing_issue.state = issue["state"]
                existing_issue.repository = f"{owner}/{repo}"
                existing_issue.html_url = issue["html_url"]
                stored_issue = existing_issue
            else:
                new_issue = GitHubIssue(
                    github_issue_id=issue["id"],
                    title=issue["title"],
                    body=issue.get("body", ""),
                    state=issue["state"],
                    repository=f"{owner}/{repo}",
                    html_url=issue["html_url"]
                )
                db.add(new_issue)
                stored_issue = new_issue
            
            await db.commit()
            await db.refresh(stored_issue)
            
            issue_state = await stored_issue.get_state(db)
            
            stored_issues.append({
                "id": stored_issue.id,
                "github_issue_id": stored_issue.github_issue_id,
                "number": issue["number"],
                "html_url": issue["html_url"],
                "title": stored_issue.title,
                "body": stored_issue.body,
                "state": stored_issue.state,
                "repository": stored_issue.repository,
                "issue_state": issue_state,
                "created_at": stored_issue.created_at,
                "updated_at": stored_issue.updated_at
            })
        
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
    
    session_data = devin_client.create_session(prompt)
    
    if not session_data:
        raise HTTPException(status_code=500, detail="Failed to create Devin session")
    
    devin_session = DevinSession(
        github_issue=issue.github_issue_id,
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
            DevinSession.github_issue == issue.github_issue_id,
            DevinSession.session_type == "scope"
        ).order_by(DevinSession.created_at.desc())
    )
    scope_session = scope_result.scalar_one_or_none()
    
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
        github_issue=issue.github_issue_id,
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
        "github_issue_id": session.github_issue,
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
        app_id = os.getenv("GITHUB_APP_ID")
        private_key = os.getenv("GITHUB_APP_PRIVATE_KEY")
        installation_id = os.getenv("GITHUB_APP_INSTALLATION_ID")
        
        if not app_id or not private_key or not installation_id:
            return {
                "configured": False,
                "message": "GitHub App not configured",
                "missing_credentials": [
                    key for key, value in {
                        "GITHUB_APP_ID": app_id,
                        "GITHUB_APP_PRIVATE_KEY": private_key,
                        "GITHUB_APP_INSTALLATION_ID": installation_id
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

@app.get("/dashboard")
async def get_dashboard_data(db: AsyncSession = Depends(get_db)):
    """Get dashboard data with issues and their associated sessions"""
    issues_result = await db.execute(select(GitHubIssue))
    issues = issues_result.scalars().all()
    
    dashboard_data = []
    for issue in issues:
        scope_result = await db.execute(
            select(DevinSession).where(
                DevinSession.github_issue == issue.github_issue_id,
                DevinSession.session_type == "scope"
            ).order_by(DevinSession.created_at.desc())
        )
        scope_session = scope_result.scalar_one_or_none()
        
        exec_result = await db.execute(
            select(DevinSession).where(
                DevinSession.github_issue == issue.github_issue_id,
                DevinSession.session_type == "execute"
            ).order_by(DevinSession.created_at.desc())
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

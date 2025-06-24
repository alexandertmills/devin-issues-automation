from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg
import httpx
import os
from typing import List, Dict, Any

app = FastAPI()

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/api/issues")
async def get_issues() -> List[Dict[str, Any]]:
    github_token = os.getenv("github_access_token")
    if not github_token:
        raise HTTPException(status_code=500, detail="GitHub access token not configured")
    
    repo_owner = "alexandertmills"
    repo_name = "devin-issues-automation"
    
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            issues_data = response.json()
            
            formatted_issues = []
            for issue in issues_data:
                formatted_issue = {
                    "id": issue["id"],
                    "number": issue["number"],
                    "title": issue["title"],
                    "body": issue["body"],
                    "state": issue["state"],
                    "created_at": issue["created_at"],
                    "updated_at": issue["updated_at"],
                    "html_url": issue["html_url"],
                    "user": {
                        "login": issue["user"]["login"],
                        "avatar_url": issue["user"]["avatar_url"]
                    },
                    "labels": [{"name": label["name"], "color": label["color"]} for label in issue["labels"]],
                    "assignees": [{"login": assignee["login"]} for assignee in issue["assignees"]]
                }
                formatted_issues.append(formatted_issue)
            
            return formatted_issues
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"GitHub API error: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching issues: {str(e)}")

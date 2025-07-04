import os
import jwt
import time
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class GitHubClient:
    def __init__(self, token: str = None, app_id: str = None, private_key: str = None, installation_id: str = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.app_id = app_id or os.getenv("Github_App_app_id")
        self.private_key = private_key or os.getenv("GITHUB_PEM")
        self.installation_id = installation_id or os.getenv("github_app_install_id")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        
        if self.app_id and self.private_key and self.installation_id:
            self._setup_app_authentication()
        elif self.token:
            self.headers["Authorization"] = f"token {self.token}"
    
    def _setup_app_authentication(self):
        """Set up GitHub App authentication"""
        try:
            jwt_token = self._generate_jwt()
            
            installation_token = self._get_installation_token(jwt_token)
            
            if installation_token:
                self.headers["Authorization"] = f"token {installation_token}"
                return True
        except Exception as e:
            print(f"Error setting up GitHub App authentication: {e}")
            return False
        
        return False
    
    def _generate_jwt(self) -> str:
        """Generate JWT for GitHub App authentication"""
        now = int(time.time())
        payload = {
            'iat': now,
            'exp': now + 600,  # 10 minutes
            'iss': self.app_id
        }
        
        return jwt.encode(payload, self.private_key, algorithm='RS256')
    
    def _get_installation_token(self, jwt_token: str) -> Optional[str]:
        """Get installation access token using JWT"""
        url = f"{self.base_url}/app/installations/{self.installation_id}/access_tokens"
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            return response.json().get('token')
        except requests.RequestException as e:
            print(f"Error getting installation token: {e}")
            return None
    
    def get_repository_issues(self, owner: str, repo: str, state: str = "open") -> List[Dict]:
        """Get issues from a GitHub repository"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues"
        params = {"state": state, "per_page": 100}
        
        try:
            print(f"Fetching issues from: {url}")
            print(f"Headers: {self.headers}")
            response = requests.get(url, headers=self.headers, params=params)
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text[:500]}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching issues: {e}")
            print(f"Response status: {getattr(e.response, 'status_code', 'No response')}")
            print(f"Response text: {getattr(e.response, 'text', 'No response text')}")
            return []
    
    def get_issue(self, owner: str, repo: str, issue_number: int) -> Optional[Dict]:
        """Get a specific issue from GitHub"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching issue {issue_number}: {e}")
            return None
    
    def get_installation_repositories(self, installation_id: str) -> List[Dict]:
        """Get repositories accessible to a GitHub App installation"""
        repositories = []
        page = 1
        per_page = 100
        
        while True:
            url = f"{self.base_url}/installation/repositories"
            params = {"per_page": per_page, "page": page}
            
            try:
                temp_client = GitHubClient(
                    app_id=self.app_id,
                    private_key=self.private_key, 
                    installation_id=installation_id
                )
                
                response = requests.get(url, headers=temp_client.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                repositories.extend(data.get('repositories', []))
                
                if len(data.get('repositories', [])) < per_page:
                    break
                    
                page += 1
                
            except requests.RequestException as e:
                print(f"Error fetching installation repositories for {installation_id}: {e}")
                break
                
        return repositories

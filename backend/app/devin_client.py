import os
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class DevinClient:
    def __init__(self):
        self.api_key = os.getenv("DEVIN_SERVICE_API_KEY")
        if not self.api_key:
            raise ValueError("DEVIN_SERVICE_API_KEY environment variable must be set")
        self.base_url = "https://api.devin.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def create_session(self, prompt: str, title: str = None) -> Optional[Dict]:
        """Create a new Devin session"""
        url = f"{self.base_url}/sessions"
        payload = {
            "prompt": prompt,
            "unlisted": True
        }
        if title:
            payload["title"] = title
        
        try:
            print(f"Making request to: {url}")
            print(f"API key present: {'Yes' if self.api_key else 'No'}")
            print(f"API key length: {len(self.api_key) if self.api_key else 0}")
            response = requests.post(url, headers=self.headers, json=payload)
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error creating Devin session: {e}")
            print(f"Response status code: {getattr(e.response, 'status_code', 'N/A')}")
            print(f"Response text: {getattr(e.response, 'text', 'N/A')}")
            return None
    
    def get_session_status(self, session_id: str) -> Optional[Dict]:
        """Get the status of a Devin session"""
        url = f"{self.base_url}/sessions/{session_id}"
        
        get_headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            print(f"DEBUG: Making GET request to: {url}")
            print(f"DEBUG: Headers: {get_headers}")
            response = requests.get(url, headers=get_headers)
            print(f"DEBUG: Response status code: {response.status_code}")
            print(f"DEBUG: Response headers: {dict(response.headers)}")
            if response.status_code != 200:
                print(f"DEBUG: Response text: {response.text}")
            response.raise_for_status()
            result = response.json()
            print(f"DEBUG: Successfully retrieved session data with keys: {list(result.keys())}")
            return result
        except requests.RequestException as e:
            print(f"Error getting session status: {e}")
            print(f"DEBUG: Request URL was: {url}")
            print(f"DEBUG: Request headers were: {get_headers}")
            return None
    
    def generate_scope_prompt(self, issue_title: str, issue_body: str, repo_name: str) -> str:
        """Generate a prompt for scoping an issue with structured output"""
        return f"""
Please analyze this GitHub issue and provide a confidence score for how well-defined and actionable it is. Update the structured output immediately when you have your analysis.

IMPORTANT: Do NOT open any pull requests or make any code changes. This is only an evaluation task.

Repository: {repo_name}
Issue Title: {issue_title}
Issue Description: {issue_body}

Please provide your analysis in this structured output format:
{{
    "confidence_score": 85,
    "complexity": "Medium",
    "action_plan": "Detailed step-by-step plan for implementation",
    "analysis": "Brief analysis of the issue"
}}

The confidence_score should be a number from 0-100 representing how well-defined and actionable this issue is.
Complexity should be "Low", "Medium", or "High".
Please update the structured output as soon as you complete your analysis.

Remember: This is ONLY an evaluation - do not implement anything or create pull requests.
"""
    
    def generate_execution_prompt(self, issue_title: str, issue_body: str, action_plan: str, repo_name: str) -> str:
        """Generate a prompt for executing an issue"""
        return f"""
Please implement the solution for this GitHub issue based on the action plan provided.

Repository: {repo_name}
Issue Title: {issue_title}
Issue Description: {issue_body}

Action Plan:
{action_plan}

Please implement the solution and create a pull request.
"""

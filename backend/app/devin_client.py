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
    
    def create_session(self, prompt: str, structured_output_schema: Optional[Dict] = None) -> Optional[Dict]:
        """Create a new Devin session with optional structured output"""
        url = f"{self.base_url}/sessions"
        payload = {
            "prompt": prompt
        }
        
        if structured_output_schema:
            payload["structured_output"] = structured_output_schema
        
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
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting session status: {e}")
            return None
    
    def generate_scope_prompt(self, issue_title: str, issue_body: str, repo_name: str) -> str:
        """Generate a prompt for scoping an issue"""
        return f"""
Please analyze this GitHub issue and provide:
1. A confidence score (0-100) for how well-defined and actionable this issue is
2. A detailed action plan for implementing the solution
3. An estimate of complexity (Low/Medium/High)

Repository: {repo_name}
Issue Title: {issue_title}
Issue Description: {issue_body}

Please provide your analysis in the following format:
CONFIDENCE_SCORE: [0-100]
COMPLEXITY: [Low/Medium/High]
ACTION_PLAN: [Detailed step-by-step plan]
"""
    
    def get_confidence_scoring_schema(self) -> Dict:
        """Get structured output schema for confidence scoring"""
        return {
            "type": "object",
            "properties": {
                "confidence_score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Confidence score (0-100) for how well-defined and actionable this issue is"
                },
                "analysis": {
                    "type": "string",
                    "description": "Brief analysis of what needs to be done"
                }
            },
            "required": ["confidence_score", "analysis"]
        }
    
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

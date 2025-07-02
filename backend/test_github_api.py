import requests
from app.github_client import GitHubClient
import os
from dotenv import load_dotenv

load_dotenv()

def test_github_api():
    """Test GitHub API integration without database"""
    print("Testing GitHub API integration...")
    
    try:
        client = GitHubClient()
        issues = client.get_repository_issues("octocat", "Hello-World", "open")
        
        print(f"✅ Successfully fetched {len(issues)} issues from octocat/Hello-World")
        
        if issues:
            sample_issue = issues[0]
            print(f"Sample issue: #{sample_issue.get('number')} - {sample_issue.get('title')}")
            print(f"Issue ID: {sample_issue.get('id')}")
            print(f"State: {sample_issue.get('state')}")
            print(f"HTML URL: {sample_issue.get('html_url')}")
            
            required_fields = ['id', 'title', 'body', 'state', 'html_url']
            missing_fields = [field for field in required_fields if field not in sample_issue]
            
            if missing_fields:
                print(f"⚠️  Missing fields in GitHub API response: {missing_fields}")
            else:
                print("✅ All required fields present in GitHub API response")
                
        return True
        
    except Exception as e:
        print(f"❌ GitHub API test failed: {e}")
        return False

if __name__ == "__main__":
    test_github_api()

#!/usr/bin/env python3

import sys
sys.path.append('.')
from app.github_client import GitHubClient

def test_github_api():
    """Test GitHub API integration directly"""
    print('=== Testing GitHub API Integration ===')
    
    try:
        client = GitHubClient()
        print('✅ GitHubClient initialized successfully')
        
        issues = client.get_repository_issues('alexandertmills', 'devin-issues-automation', 'open')
        print(f'✅ Found {len(issues)} open issues in repository')
        
        test_issue = None
        for issue in issues:
            if 'Test Issue for API Integration' in issue.get('title', ''):
                test_issue = issue
                break
        
        if test_issue:
            print(f'✅ Found test issue: "{test_issue["title"]}"')
            print(f'   Issue #{test_issue["number"]}: {test_issue["html_url"]}')
            print(f'   Body: "{test_issue.get("body", "No body")}"')
            print(f'   State: {test_issue["state"]}')
            
            title = test_issue["title"]
            body = test_issue.get("body", "")
            
            print('\n=== Issue Analysis ===')
            print(f'Title: "{title}"')
            print(f'Description: "{body}"')
            
            is_test_issue = "test" in title.lower() and "api" in title.lower()
            has_clear_purpose = "integration" in title.lower() or "endpoint" in body.lower()
            mentions_verification = "verify" in body.lower() or "working" in body.lower()
            
            print(f'✅ Clearly a test issue: {is_test_issue}')
            print(f'✅ Has clear purpose: {has_clear_purpose}')
            print(f'✅ Mentions verification: {mentions_verification}')
            
            return {
                'success': True,
                'issue_found': True,
                'issue_data': test_issue,
                'analysis': {
                    'is_test_issue': is_test_issue,
                    'has_clear_purpose': has_clear_purpose,
                    'mentions_verification': mentions_verification
                }
            }
        else:
            print('ℹ️  Test issue not found in repository')
            print('Available issues:')
            for i, issue in enumerate(issues[:5]):
                print(f'  {i+1}. #{issue["number"]}: {issue["title"]}')
            
            return {
                'success': True,
                'issue_found': False,
                'total_issues': len(issues),
                'sample_issues': [{'number': i['number'], 'title': i['title']} for i in issues[:3]]
            }
            
    except Exception as e:
        print(f'❌ GitHub API test failed: {e}')
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    result = test_github_api()
    
    print('\n=== Test Summary ===')
    if result['success']:
        if result.get('issue_found'):
            print('✅ GitHub API integration working')
            print('✅ Test issue found and analyzed')
            print('🎯 Ready for confidence assessment')
        else:
            print('✅ GitHub API integration working')
            print('ℹ️  Test issue not found, but system is functional')
    else:
        print('❌ GitHub API integration failed')
        print(f'Error: {result.get("error", "Unknown error")}')

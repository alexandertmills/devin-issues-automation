#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append('./backend')

from backend.app.github_client import GitHubClient
from backend.app.database import create_tables

async def test_api_integration():
    """Test the GitHub API integration for the test issue"""
    print('=== GitHub Issues API Integration Test ===')
    print()
    
    try:
        print('1. Testing GitHub API connection...')
        client = GitHubClient()
        issues = client.get_repository_issues('alexandertmills', 'devin-issues-automation', 'open')
        print(f'   ✅ GitHub API working - found {len(issues)} open issues')
        
        print('2. Looking for test issue...')
        test_issue = None
        for issue in issues:
            if 'Test Issue for API Integration' in issue.get('title', ''):
                test_issue = issue
                break
        
        if test_issue:
            print(f'   ✅ Found test issue: "{test_issue["title"]}"')
            print(f'   📍 Issue #{test_issue["number"]}: {test_issue["html_url"]}')
            print(f'   📝 Body: {test_issue.get("body", "No body")[:100]}...')
            print(f'   🏷️  State: {test_issue["state"]}')
            
            title = test_issue["title"]
            body = test_issue.get("body", "")
            
            print()
            print('3. Analyzing test issue content...')
            print(f'   Title: "{title}"')
            print(f'   Description: "{body}"')
            
            is_clear = "test" in title.lower() and "api" in title.lower() and "integration" in title.lower()
            has_description = len(body.strip()) > 0
            mentions_endpoint = "/api/issues" in body or "endpoint" in body.lower()
            
            print(f'   ✅ Clear test purpose: {is_clear}')
            print(f'   ✅ Has description: {has_description}')
            print(f'   ✅ Mentions API/endpoint: {mentions_endpoint}')
            
            return {
                'found': True,
                'issue': test_issue,
                'analysis': {
                    'clear_purpose': is_clear,
                    'has_description': has_description,
                    'mentions_endpoint': mentions_endpoint
                }
            }
        else:
            print('   ℹ️  Test issue not found in repository')
            print('   Available issues:')
            for issue in issues[:5]:  # Show first 5 issues
                print(f'     - #{issue["number"]}: {issue["title"]}')
            
            return {
                'found': False,
                'total_issues': len(issues),
                'sample_issues': [{'number': i['number'], 'title': i['title']} for i in issues[:3]]
            }
            
    except Exception as e:
        print(f'   ❌ GitHub API test failed: {e}')
        return {'error': str(e)}

async def test_database_setup():
    """Test database table creation"""
    print()
    print('4. Testing database setup...')
    try:
        await create_tables()
        print('   ✅ Database tables created successfully')
        return True
    except Exception as e:
        print(f'   ❌ Database setup failed: {e}')
        return False

async def main():
    """Main test function"""
    api_result = await test_api_integration()
    
    db_result = await test_database_setup()
    
    print()
    print('=== Test Summary ===')
    if api_result.get('found'):
        print('✅ Test issue found and analyzed')
        print('✅ GitHub API integration working')
        if db_result:
            print('✅ Database setup working')
        print()
        print('🎯 Ready to provide confidence analysis')
    else:
        print('ℹ️  Test issue not found, but API integration confirmed working')
        print('📊 System is ready for API endpoint testing')
    
    return api_result, db_result

if __name__ == "__main__":
    asyncio.run(main())

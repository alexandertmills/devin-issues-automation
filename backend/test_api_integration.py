#!/usr/bin/env python3
"""
Comprehensive test for the /issues/{owner}/{repo} API endpoint integration.
This test verifies GitHub API integration and database functionality.
"""

import asyncio
import sys
import os
sys.path.append('.')

from app.main import app
from app.github_client import GitHubClient
from app.database import get_db, create_tables
from app.models import GitHubIssue
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import requests
import json

async def test_github_api_connectivity():
    """Test 1: Verify GitHub API connectivity"""
    print("\n=== Test 1: GitHub API Connectivity ===")
    
    try:
        client = GitHubClient()
        issues = client.get_repository_issues('octocat', 'Hello-World', 'open')
        print(f"✅ Successfully fetched {len(issues)} issues from octocat/Hello-World")
        
        if issues:
            sample = issues[0]
            required_fields = ['id', 'title', 'body', 'state', 'html_url', 'number']
            missing = [f for f in required_fields if f not in sample]
            if missing:
                print(f"⚠️  Missing fields: {missing}")
                return False
            else:
                print("✅ All required fields present in GitHub API response")
                print(f"   Sample: #{sample.get('number')} - {sample.get('title', '')[:50]}...")
                return True
        else:
            print("⚠️  No issues returned from GitHub API")
            return False
            
    except Exception as e:
        print(f"❌ GitHub API test failed: {e}")
        return False

async def test_database_setup():
    """Test 2: Verify database setup and connectivity"""
    print("\n=== Test 2: Database Setup ===")
    
    try:
        await create_tables()
        print("✅ Database tables created/verified successfully")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def test_endpoint_with_requests(base_url="http://localhost:8001"):
    """Test 3: Test the actual /issues endpoint via HTTP requests"""
    print(f"\n=== Test 3: HTTP Endpoint Testing (Base URL: {base_url}) ===")
    
    test_cases = [
        {
            "name": "Public repo - octocat/Hello-World",
            "owner": "octocat",
            "repo": "Hello-World",
            "params": {"limit": 3}
        },
        {
            "name": "Public repo with different state",
            "owner": "octocat", 
            "repo": "Hello-World",
            "params": {"state": "closed", "limit": 2}
        },
        {
            "name": "Invalid repository",
            "owner": "nonexistent",
            "repo": "invalid-repo-name-12345",
            "params": {"limit": 1},
            "expect_error": True
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n  Testing: {test_case['name']}")
        
        try:
            url = f"{base_url}/issues/{test_case['owner']}/{test_case['repo']}"
            response = requests.get(url, params=test_case['params'], timeout=10)
            
            if test_case.get('expect_error'):
                if response.status_code >= 400:
                    print(f"    ✅ Expected error received: {response.status_code}")
                    results.append(True)
                else:
                    print(f"    ❌ Expected error but got: {response.status_code}")
                    results.append(False)
            else:
                if response.status_code == 200:
                    data = response.json()
                    issues_count = len(data.get('issues', []))
                    print(f"    ✅ Success: {issues_count} issues returned")
                    
                    if data.get('issues'):
                        sample = data['issues'][0]
                        print(f"    Sample: #{sample.get('number')} - {sample.get('title', '')[:40]}...")
                        
                        required_fields = ['id', 'github_issue_id', 'title', 'state', 'repository', 'html_url']
                        missing = [f for f in required_fields if f not in sample]
                        if missing:
                            print(f"    ⚠️  Missing response fields: {missing}")
                        else:
                            print(f"    ✅ All required response fields present")
                    
                    results.append(True)
                else:
                    print(f"    ❌ HTTP Error: {response.status_code}")
                    print(f"    Response: {response.text[:200]}...")
                    results.append(False)
                    
        except requests.exceptions.RequestException as e:
            print(f"    ❌ Request failed: {e}")
            results.append(False)
        except Exception as e:
            print(f"    ❌ Unexpected error: {e}")
            results.append(False)
    
    return all(results)

def test_authentication_methods(base_url="http://localhost:8001"):
    """Test 4: Test different authentication methods"""
    print(f"\n=== Test 4: Authentication Methods ===")
    
    print("\n  Testing default authentication...")
    try:
        url = f"{base_url}/issues/octocat/Hello-World"
        response = requests.get(url, params={"limit": 1}, timeout=10)
        if response.status_code == 200:
            print("    ✅ Default authentication working")
            default_auth_works = True
        else:
            print(f"    ❌ Default authentication failed: {response.status_code}")
            default_auth_works = False
    except Exception as e:
        print(f"    ❌ Default authentication error: {e}")
        default_auth_works = False
    
    print("\n  Testing invalid token handling...")
    try:
        headers = {"X-GitHub-Token": "invalid_token_12345"}
        url = f"{base_url}/issues/octocat/Hello-World"
        response = requests.get(url, headers=headers, params={"limit": 1}, timeout=10)
        if response.status_code >= 400:
            print("    ✅ Invalid token properly rejected")
            invalid_token_handled = True
        else:
            print(f"    ⚠️  Invalid token not rejected: {response.status_code}")
            invalid_token_handled = False
    except Exception as e:
        print(f"    ❌ Invalid token test error: {e}")
        invalid_token_handled = False
    
    return default_auth_works and invalid_token_handled

async def run_all_tests():
    """Run all tests and provide summary"""
    print("🚀 Starting API Integration Tests for /issues/{owner}/{repo} endpoint")
    print("=" * 70)
    
    results = []
    
    results.append(await test_github_api_connectivity())
    
    results.append(await test_database_setup())
    
    print("\n📝 Note: HTTP endpoint tests require the FastAPI server to be running")
    print("   Start server with: poetry run fastapi dev app/main.py --port 8001")
    
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    test_names = [
        "GitHub API Connectivity",
        "Database Setup"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {name}: {status}")
    
    passed = sum(results)
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic tests PASSED! Ready for HTTP endpoint testing.")
    else:
        print("💥 Some tests FAILED. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

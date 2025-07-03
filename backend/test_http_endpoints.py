#!/usr/bin/env python3
"""
HTTP endpoint testing for the /issues/{owner}/{repo} API.
This script tests the actual HTTP endpoints and requires the server to be running.
"""

import requests
import json
import sys
import time

def test_health_check(base_url="http://localhost:8000"):
    """Test the health check endpoint first"""
    print("=== Testing Health Check ===")
    
    try:
        response = requests.get(f"{base_url}/healthz", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                print("✅ Health check passed")
                return True
            else:
                print(f"❌ Health check returned unexpected data: {data}")
                return False
        else:
            print(f"❌ Health check failed with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running on port 8001?")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_issues_endpoint(base_url="http://localhost:8000"):
    """Test the main /issues/{owner}/{repo} endpoint"""
    print("\n=== Testing /issues/{owner}/{repo} Endpoint ===")
    
    test_cases = [
        {
            "name": "Basic public repo test",
            "owner": "octocat",
            "repo": "Hello-World", 
            "params": {"limit": 3, "state": "open"},
            "expect_success": True
        },
        {
            "name": "Closed issues test",
            "owner": "octocat",
            "repo": "Hello-World",
            "params": {"limit": 2, "state": "closed"},
            "expect_success": True
        },
        {
            "name": "Large limit test",
            "owner": "octocat", 
            "repo": "Hello-World",
            "params": {"limit": 50},
            "expect_success": True
        },
        {
            "name": "Invalid repository test",
            "owner": "nonexistent-user-12345",
            "repo": "nonexistent-repo-12345",
            "params": {"limit": 1},
            "expect_success": False
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n  🧪 {test_case['name']}")
        
        try:
            url = f"{base_url}/issues/{test_case['owner']}/{test_case['repo']}"
            response = requests.get(url, params=test_case['params'], timeout=15)
            
            print(f"     Status: {response.status_code}")
            
            if test_case['expect_success']:
                if response.status_code == 200:
                    data = response.json()
                    issues = data.get('issues', [])
                    repository = data.get('repository', '')
                    
                    print(f"     ✅ Success: {len(issues)} issues returned")
                    print(f"     Repository: {repository}")
                    
                    if issues:
                        sample = issues[0]
                        print(f"     Sample: #{sample.get('number')} - {sample.get('title', '')[:40]}...")
                        
                        required_fields = ['id', 'github_issue_id', 'title', 'state', 'repository', 'html_url', 'number']
                        missing_fields = [f for f in required_fields if f not in sample]
                        
                        if missing_fields:
                            print(f"     ⚠️  Missing fields: {missing_fields}")
                        else:
                            print(f"     ✅ All required fields present")
                        
                        if isinstance(sample.get('github_issue_id'), int):
                            print(f"     ✅ github_issue_id is integer: {sample['github_issue_id']}")
                        else:
                            print(f"     ⚠️  github_issue_id not integer: {sample.get('github_issue_id')}")
                        
                        if sample.get('repository') == f"{test_case['owner']}/{test_case['repo']}":
                            print(f"     ✅ Repository field correct")
                        else:
                            print(f"     ⚠️  Repository field mismatch: {sample.get('repository')}")
                    
                    results.append(True)
                else:
                    print(f"     ❌ Expected success but got {response.status_code}")
                    print(f"     Response: {response.text[:200]}...")
                    results.append(False)
            else:
                if response.status_code >= 400:
                    print(f"     ✅ Expected error received: {response.status_code}")
                    results.append(True)
                else:
                    print(f"     ❌ Expected error but got success: {response.status_code}")
                    results.append(False)
                    
        except requests.exceptions.Timeout:
            print(f"     ❌ Request timeout")
            results.append(False)
        except Exception as e:
            print(f"     ❌ Request error: {e}")
            results.append(False)
    
    return results

def test_authentication_scenarios(base_url="http://localhost:8000"):
    """Test different authentication scenarios"""
    print("\n=== Testing Authentication Scenarios ===")
    
    scenarios = [
        {
            "name": "No authentication (default GitHub App)",
            "headers": {},
            "expect_success": True
        },
        {
            "name": "Invalid GitHub token",
            "headers": {"X-GitHub-Token": "invalid_token_12345"},
            "expect_success": False
        },
        {
            "name": "Empty GitHub token",
            "headers": {"X-GitHub-Token": ""},
            "expect_success": True  # Should fall back to default
        }
    ]
    
    results = []
    
    for scenario in scenarios:
        print(f"\n  🔐 {scenario['name']}")
        
        try:
            url = f"{base_url}/issues/octocat/Hello-World"
            response = requests.get(
                url, 
                headers=scenario['headers'], 
                params={"limit": 1},
                timeout=10
            )
            
            print(f"     Status: {response.status_code}")
            
            if scenario['expect_success']:
                if response.status_code == 200:
                    data = response.json()
                    print(f"     ✅ Success: {len(data.get('issues', []))} issues")
                    results.append(True)
                else:
                    print(f"     ❌ Expected success but got {response.status_code}")
                    results.append(False)
            else:
                if response.status_code >= 400:
                    print(f"     ✅ Expected error received")
                    results.append(True)
                else:
                    print(f"     ❌ Expected error but got success")
                    results.append(False)
                    
        except Exception as e:
            print(f"     ❌ Request error: {e}")
            results.append(False)
    
    return results

def main():
    """Main test runner"""
    print("🚀 HTTP Endpoint Testing for /issues/{owner}/{repo}")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    health_ok = test_health_check(base_url)
    if not health_ok:
        print("\n💥 Server health check failed. Cannot proceed with endpoint tests.")
        print("Please start the server with: poetry run fastapi dev app/main.py --port 8000")
        return False
    
    issues_results = test_issues_endpoint(base_url)
    
    auth_results = test_authentication_scenarios(base_url)
    
    print("\n" + "=" * 60)
    print("📊 HTTP ENDPOINT TEST SUMMARY")
    print("=" * 60)
    
    all_results = [health_ok] + issues_results + auth_results
    passed = sum(all_results)
    total = len(all_results)
    
    print(f"Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Issues Endpoint Tests: {sum(issues_results)}/{len(issues_results)} passed")
    print(f"Authentication Tests: {sum(auth_results)}/{len(auth_results)} passed")
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All HTTP endpoint tests PASSED!")
        return True
    else:
        print("💥 Some HTTP endpoint tests FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

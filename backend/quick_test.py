#!/usr/bin/env python3
"""
Quick test to verify the /issues endpoint is working after model fixes
"""

import requests
import json

def test_basic_endpoint():
    """Test the basic endpoint functionality"""
    print("🧪 Testing /issues/octocat/Hello-World endpoint...")
    
    try:
        url = "http://localhost:8001/issues/octocat/Hello-World"
        response = requests.get(url, params={"limit": 2}, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'issues' in data:
                issues_count = len(data['issues'])
                print(f"✅ SUCCESS: {issues_count} issues returned")
                
                if data['issues']:
                    issue = data['issues'][0]
                    title = issue.get('title', '')[:50]
                    number = issue.get('number', 'N/A')
                    print(f"   Sample: #{number} - {title}...")
                    
                    required_fields = ['id', 'github_issue_id', 'title', 'state', 'repository', 'html_url']
                    missing = [f for f in required_fields if f not in issue]
                    if missing:
                        print(f"   ⚠️  Missing fields: {missing}")
                    else:
                        print(f"   ✅ All required fields present")
                
                return True
            else:
                print("❌ FAILED: No 'issues' field in response")
                print(f"Response keys: {list(data.keys())}")
                return False
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"Raw response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ FAILED: Cannot connect to server. Is it running on port 8001?")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_endpoint()
    if success:
        print("\n🎉 Basic endpoint test PASSED! Ready for full testing.")
    else:
        print("\n💥 Basic endpoint test FAILED. Need to investigate further.")

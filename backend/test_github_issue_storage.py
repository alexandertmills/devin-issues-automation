import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

async def test_github_issue_storage():
    """Test storing a fake GitHub issue directly in the database"""
    print("Testing GitHub issue storage with updated schema...")
    
    database_url = os.getenv("NEON_DATABASE_URL")
    if not database_url:
        raise ValueError("NEON_DATABASE_URL environment variable is not set")
    
    conn = await asyncpg.connect(database_url)
    
    try:
        columns = await conn.fetch('''
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'github_issues'
            ORDER BY ordinal_position
        ''')
        
        print("github_issues table columns:")
        for row in columns:
            print(f"  {row['column_name']}: {row['data_type']}")
        
        html_url_exists = any(row['column_name'] == 'html_url' for row in columns)
        if not html_url_exists:
            print("❌ html_url column still missing!")
            return False
        
        print("✅ html_url column exists")
        
        fake_issue_id = 999999999
        fake_html_url = "https://github.com/test/repo/issues/1"
        
        await conn.execute('''
            INSERT INTO github_issues 
            (github_issue_id, title, body, state, repository, html_url, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (github_issue_id) DO UPDATE SET
                title = EXCLUDED.title,
                body = EXCLUDED.body,
                state = EXCLUDED.state,
                repository = EXCLUDED.repository,
                html_url = EXCLUDED.html_url,
                updated_at = EXCLUDED.updated_at
        ''', fake_issue_id, "Test Issue", "This is a test issue body", "open", 
             "test/repo", fake_html_url, datetime.utcnow(), datetime.utcnow())
        
        print(f"✅ Successfully stored fake GitHub issue #{fake_issue_id}")
        
        stored_issue = await conn.fetchrow('''
            SELECT github_issue_id, title, body, state, repository, html_url
            FROM github_issues 
            WHERE github_issue_id = $1
        ''', fake_issue_id)
        
        if stored_issue:
            print("✅ Retrieved stored issue:")
            print(f"  ID: {stored_issue['github_issue_id']}")
            print(f"  Title: {stored_issue['title']}")
            print(f"  State: {stored_issue['state']}")
            print(f"  Repository: {stored_issue['repository']}")
            print(f"  HTML URL: {stored_issue['html_url']}")
            
            if stored_issue['html_url'] == fake_html_url:
                print("✅ html_url field stored correctly!")
                return True
            else:
                print(f"❌ html_url mismatch: expected {fake_html_url}, got {stored_issue['html_url']}")
                return False
        else:
            print("❌ Failed to retrieve stored issue")
            return False
            
    except Exception as e:
        print(f"❌ GitHub issue storage test failed: {e}")
        return False
    finally:
        await conn.close()

if __name__ == "__main__":
    success = asyncio.run(test_github_issue_storage())
    if success:
        print("\n🎉 GitHub issue storage test PASSED!")
    else:
        print("\n💥 GitHub issue storage test FAILED!")

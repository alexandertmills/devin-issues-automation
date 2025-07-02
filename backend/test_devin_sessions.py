import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid

load_dotenv()

async def test_devin_session_storage():
    """Test creating fake DevinSession records in the database"""
    print("Testing DevinSession database storage...")
    
    database_url = os.getenv("NEON_DATABASE_URL")
    if not database_url:
        raise ValueError("NEON_DATABASE_URL environment variable is not set")
    
    conn = await asyncpg.connect(database_url)
    
    try:
        fake_session_id = f"test-session-{uuid.uuid4().hex[:8]}"
        fake_github_issue_id = 12345  # Using the old schema column name
        
        await conn.execute('''
            INSERT INTO devin_sessions 
            (github_issue_id, session_id, session_type, status, confidence_score, action_plan, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ''', fake_github_issue_id, fake_session_id, "scope", "completed", 85.5, 
             "1. Analyze the issue\n2. Create implementation plan\n3. Test the solution", 
             datetime.utcnow(), datetime.utcnow())
        
        print(f"✅ Successfully created fake scope session: {fake_session_id}")
        
        fake_execute_session_id = f"test-execute-{uuid.uuid4().hex[:8]}"
        await conn.execute('''
            INSERT INTO devin_sessions 
            (github_issue_id, session_id, session_type, status, result, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''', fake_github_issue_id, fake_execute_session_id, "execute", "completed", 
             "Successfully implemented the requested feature", 
             datetime.utcnow(), datetime.utcnow())
        
        print(f"✅ Successfully created fake execute session: {fake_execute_session_id}")
        
        sessions = await conn.fetch('''
            SELECT session_id, session_type, status, confidence_score, action_plan, result
            FROM devin_sessions 
            WHERE github_issue_id = $1
            ORDER BY created_at DESC
        ''', fake_github_issue_id)
        
        print(f"✅ Retrieved {len(sessions)} sessions from database:")
        for session in sessions:
            print(f"  - {session['session_type']} session {session['session_id']}: {session['status']}")
            if session['confidence_score']:
                print(f"    Confidence: {session['confidence_score']}")
            if session['action_plan']:
                print(f"    Action plan: {session['action_plan'][:50]}...")
            if session['result']:
                print(f"    Result: {session['result'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ DevinSession storage test failed: {e}")
        return False
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_devin_session_storage())

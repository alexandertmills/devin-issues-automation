import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid

load_dotenv()

async def create_more_test_sessions():
    """Create additional test DevinSession records for different scenarios"""
    print("Creating additional test DevinSession records...")
    
    database_url = os.getenv("NEON_DATABASE_URL")
    if not database_url:
        raise ValueError("NEON_DATABASE_URL environment variable is not set")
    
    conn = await asyncpg.connect(database_url)
    
    try:
        test_cases = [
            {'issue_id': 11111, 'title': 'Fix login bug', 'confidence': 92.0},
            {'issue_id': 22222, 'title': 'Add dark mode', 'confidence': 78.5},
            {'issue_id': 33333, 'title': 'Optimize database queries', 'confidence': 85.0}
        ]
        
        for case in test_cases:
            scope_session_id = f"scope-{uuid.uuid4().hex[:8]}"
            exec_session_id = f"exec-{uuid.uuid4().hex[:8]}"
            
            await conn.execute('''
                INSERT INTO devin_sessions 
                (github_issue_id, session_id, session_type, status, confidence_score, action_plan, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ''', case['issue_id'], scope_session_id, "scope", "completed", case['confidence'], 
                 f"Action plan for: {case['title']}\n1. Analyze requirements\n2. Design solution\n3. Implement changes", 
                 datetime.utcnow(), datetime.utcnow())
            
            await conn.execute('''
                INSERT INTO devin_sessions 
                (github_issue_id, session_id, session_type, status, result, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''', case['issue_id'], exec_session_id, "execute", "completed", 
                 f"Successfully resolved: {case['title']}", 
                 datetime.utcnow(), datetime.utcnow())
            
            print(f"✅ Created sessions for issue {case['issue_id']}: {case['title']}")
        
        count = await conn.fetchval('SELECT COUNT(*) FROM devin_sessions')
        print(f"✅ Total DevinSession records in database: {count}")
        
        scope_count = await conn.fetchval("SELECT COUNT(*) FROM devin_sessions WHERE session_type = 'scope'")
        exec_count = await conn.fetchval("SELECT COUNT(*) FROM devin_sessions WHERE session_type = 'execute'")
        
        print(f"  - Scope sessions: {scope_count}")
        print(f"  - Execute sessions: {exec_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create additional test sessions: {e}")
        return False
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_more_test_sessions())

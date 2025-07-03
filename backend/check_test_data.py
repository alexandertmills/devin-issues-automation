import asyncio
from app.database import AsyncSessionLocal
from app.models import GitHubIssue, DevinSession
from sqlalchemy import select

async def check_existing_data():
    async with AsyncSessionLocal() as db:
        issues_result = await db.execute(select(GitHubIssue))
        issues = issues_result.scalars().all()
        print(f'Found {len(issues)} existing issues in database')
        
        for issue in issues[:3]:  # Show first 3 issues
            print(f'  Issue {issue.id}: {issue.title} ({issue.state})')
        
        sessions_result = await db.execute(select(DevinSession))
        sessions = sessions_result.scalars().all()
        print(f'Found {len(sessions)} existing sessions in database')
        
        for session in sessions[:3]:  # Show first 3 sessions
            print(f'  Session {session.id}: {session.session_type} - {session.status}')

if __name__ == "__main__":
    asyncio.run(check_existing_data())

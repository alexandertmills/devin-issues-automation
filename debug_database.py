#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append('./backend')

from backend.app.database import get_db, AsyncSessionLocal
from backend.app.models import GitHubIssue, DevinSession
from sqlalchemy import select, func

async def debug_database():
    """Debug database contents to understand duplicate entries"""
    print('=== Database Debug Analysis ===')
    
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(func.count(GitHubIssue.id)))
            total_issues = result.scalar()
            print(f'Total GitHubIssue records: {total_issues}')
            
            result = await db.execute(
                select(GitHubIssue.github_issue_id, func.count(GitHubIssue.id))
                .group_by(GitHubIssue.github_issue_id)
                .having(func.count(GitHubIssue.id) > 1)
            )
            duplicates = result.fetchall()
            
            if duplicates:
                print(f'Found {len(duplicates)} duplicate github_issue_id values:')
                for github_issue_id, count in duplicates:
                    print(f'  github_issue_id {github_issue_id}: {count} records')
                    
                    detail_result = await db.execute(
                        select(GitHubIssue).where(GitHubIssue.github_issue_id == github_issue_id)
                    )
                    duplicate_records = detail_result.fetchall()
                    for record in duplicate_records:
                        print(f'    ID: {record.id}, Title: "{record.title[:50]}...", Created: {record.created_at}')
            else:
                print('No duplicate github_issue_id values found')
            
            result = await db.execute(select(GitHubIssue).limit(10))
            all_issues = result.scalars().all()
            print(f'\nFirst 10 GitHubIssue records:')
            for issue in all_issues:
                print(f'  ID: {issue.id}, GitHub ID: {issue.github_issue_id}, Title: "{issue.title[:50]}..."')
            
            result = await db.execute(select(func.count(DevinSession.id)))
            total_sessions = result.scalar()
            print(f'\nTotal DevinSession records: {total_sessions}')
            
            if total_sessions > 0:
                result = await db.execute(select(DevinSession).limit(5))
                sessions = result.scalars().all()
                print('First 5 DevinSession records:')
                for session in sessions:
                    print(f'  ID: {session.id}, GitHub Issue ID: {session.github_issue_id}, Type: {session.session_type}')
            
        except Exception as e:
            print(f'Database debug failed: {e}')
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_database())

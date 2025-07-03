#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append('./backend')

from backend.app.database import AsyncSessionLocal
from backend.app.models import GitHubIssue, DevinSession
from sqlalchemy import select, func

async def debug_devin_sessions():
    """Debug DevinSession records to find multiple rows issue"""
    print('=== DevinSession Debug Analysis ===')
    
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(
                    DevinSession.github_issue_id, 
                    DevinSession.session_type,
                    func.count(DevinSession.id)
                )
                .group_by(DevinSession.github_issue_id, DevinSession.session_type)
                .having(func.count(DevinSession.id) > 1)
            )
            duplicates = result.fetchall()
            
            if duplicates:
                print(f'Found {len(duplicates)} duplicate github_issue_id + session_type combinations:')
                for github_issue_id, session_type, count in duplicates:
                    print(f'  github_issue_id {github_issue_id}, session_type "{session_type}": {count} records')
                    
                    detail_result = await db.execute(
                        select(DevinSession).where(
                            DevinSession.github_issue_id == github_issue_id,
                            DevinSession.session_type == session_type
                        ).order_by(DevinSession.created_at.desc())
                    )
                    duplicate_records = detail_result.scalars().all()
                    for record in duplicate_records:
                        print(f'    ID: {record.id}, Session ID: {record.session_id}, Status: {record.status}, Created: {record.created_at}')
            else:
                print('No duplicate github_issue_id + session_type combinations found')
            
            result = await db.execute(
                select(DevinSession).where(DevinSession.session_type == "scope")
                .order_by(DevinSession.github_issue_id, DevinSession.created_at.desc())
            )
            scope_sessions = result.scalars().all()
            print(f'\nAll scope sessions ({len(scope_sessions)} total):')
            for session in scope_sessions:
                print(f'  ID: {session.id}, GitHub Issue ID: {session.github_issue_id}, Session ID: {session.session_id}, Status: {session.status}')
            
            result = await db.execute(select(GitHubIssue))
            all_issues = result.scalars().all()
            print(f'\nTesting get_state() query for each GitHubIssue:')
            for issue in all_issues:
                print(f'  Testing GitHubIssue ID: {issue.id}, GitHub ID: {issue.github_issue_id}')
                try:
                    result = await db.execute(
                        select(DevinSession).where(
                            DevinSession.github_issue_id == issue.id,
                            DevinSession.session_type == "scope"
                        ).order_by(DevinSession.created_at.desc())
                    )
                    sessions = result.scalars().all()
                    print(f'    Found {len(sessions)} scope sessions')
                    if len(sessions) > 1:
                        print(f'    ⚠️  Multiple scope sessions found - this will cause scalar_one_or_none() error')
                        for s in sessions:
                            print(f'      Session ID: {s.id}, Created: {s.created_at}')
                    
                    result = await db.execute(
                        select(DevinSession).where(
                            DevinSession.github_issue_id == issue.id,
                            DevinSession.session_type == "scope"
                        ).order_by(DevinSession.created_at.desc())
                    )
                    most_recent = result.scalar_one_or_none()
                    print(f'    ✅ scalar_one_or_none() succeeded')
                except Exception as e:
                    print(f'    ❌ scalar_one_or_none() failed: {e}')
            
        except Exception as e:
            print(f'DevinSession debug failed: {e}')
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_devin_sessions())

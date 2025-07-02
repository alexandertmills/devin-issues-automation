import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def add_missing_column():
    database_url = os.getenv("NEON_DATABASE_URL")
    if not database_url:
        raise ValueError("NEON_DATABASE_URL environment variable is not set")
    
    conn = await asyncpg.connect(database_url)
    
    try:
        result = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'github_issues' AND column_name = 'html_url'
        """)
        
        if not result:
            await conn.execute('ALTER TABLE github_issues ADD COLUMN html_url VARCHAR;')
            print('Added html_url column to github_issues table')
        else:
            print('html_url column already exists')
            
    except Exception as e:
        print(f'Error: {e}')
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_missing_column())

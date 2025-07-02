import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def add_html_url_column():
    """Add missing html_url column to github_issues table"""
    database_url = os.getenv("NEON_DATABASE_URL")
    if not database_url:
        raise ValueError("NEON_DATABASE_URL environment variable is not set")
    
    conn = await asyncpg.connect(database_url)
    
    try:
        result = await conn.fetchval('''
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'github_issues' AND column_name = 'html_url'
        ''')
        
        if result > 0:
            print("html_url column already exists")
            return
        
        await conn.execute('''
            ALTER TABLE github_issues 
            ADD COLUMN html_url VARCHAR NULL
        ''')
        
        print("✅ Successfully added html_url column to github_issues table")
        
        columns = await conn.fetch('''
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'github_issues'
            ORDER BY ordinal_position
        ''')
        
        print("Updated github_issues table columns:")
        for row in columns:
            print(f"  {row['column_name']}: {row['data_type']}")
            
    except Exception as e:
        print(f"❌ Failed to add html_url column: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_html_url_column())

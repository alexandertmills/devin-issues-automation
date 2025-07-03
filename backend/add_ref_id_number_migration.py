import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def add_ref_id_number_column():
    """Add ref_id_number column to github_issues table"""
    database_url = os.getenv("NEON_DATABASE_URL")
    if not database_url:
        raise ValueError("NEON_DATABASE_URL environment variable is not set")
    
    conn = await asyncpg.connect(database_url)
    
    try:
        result = await conn.fetchval('''
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'github_issues' AND column_name = 'ref_id_number'
        ''')
        
        if result > 0:
            print("ref_id_number column already exists")
            return
        
        await conn.execute('''
            ALTER TABLE github_issues 
            ADD COLUMN ref_id_number INTEGER DEFAULT 0
        ''')
        
        print("✅ Successfully added ref_id_number column to github_issues table")
        
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
        print(f"❌ Failed to add ref_id_number column: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_ref_id_number_column())

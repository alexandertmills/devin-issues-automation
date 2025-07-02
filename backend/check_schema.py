import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_schema():
    database_url = os.getenv('NEON_DATABASE_URL')
    if not database_url:
        raise ValueError("NEON_DATABASE_URL environment variable is not set")
    
    conn = await asyncpg.connect(database_url)
    
    try:
        result = await conn.fetch('''
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'github_issues'
            ORDER BY ordinal_position
        ''')
        
        print('github_issues table columns:')
        for row in result:
            print(f'  {row["column_name"]}: {row["data_type"]}')
        
        result2 = await conn.fetch('''
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'devin_sessions'
            ORDER BY ordinal_position
        ''')
        
        print('\ndevin_sessions table columns:')
        for row in result2:
            print(f'  {row["column_name"]}: {row["data_type"]}')
            
    except Exception as e:
        print(f'Error: {e}')
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_schema())

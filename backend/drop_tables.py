import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def drop_tables():
    database_url = os.getenv("NEON_DATABASE_URL")
    if not database_url:
        raise ValueError("NEON_DATABASE_URL environment variable is not set")
    
    conn = await asyncpg.connect(database_url)
    
    await conn.execute('DROP TABLE IF EXISTS devin_sessions CASCADE;')
    await conn.execute('DROP TABLE IF EXISTS github_issues CASCADE;')
    print('Tables dropped successfully')
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(drop_tables())

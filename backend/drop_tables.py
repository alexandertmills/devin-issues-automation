import asyncio
import asyncpg

async def drop_tables():
    conn = await asyncpg.connect(
        host='ep-sweet-breeze-a84hge8c-pooler.eastus2.azure.neon.tech',
        database='neondb',
        user='neondb_owner',
        password='npg_iw4GofnvpQ3m',
        ssl='require'
    )
    
    await conn.execute('DROP TABLE IF EXISTS devin_sessions CASCADE;')
    await conn.execute('DROP TABLE IF EXISTS github_issues CASCADE;')
    print('Tables dropped successfully')
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(drop_tables())

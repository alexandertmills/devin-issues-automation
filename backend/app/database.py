import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from .models import Base

load_dotenv()

DATABASE_URL = os.getenv("NEON_DATABASE_URL")

if not DATABASE_URL:
    pghost = os.getenv("NEON_CREDS_PGHOST")
    pgdatabase = os.getenv("NEON_CREDS_PGDATABASE") 
    pguser = os.getenv("NEON_CREDS_PGUSER")
    pgpassword = os.getenv("NEON_CREDS_PGPASSWORD")
    pgsslmode = os.getenv("NEON_CREDS_PGSSLMODE", "require")
    
    if all([pghost, pgdatabase, pguser, pgpassword]):
        DATABASE_URL = f"postgresql://{pguser}:{pgpassword}@{pghost}/{pgdatabase}?sslmode={pgsslmode}"
        print(f"Constructed database URL from individual Neon credentials")
    else:
        missing_creds = []
        if not pghost: missing_creds.append("NEON_CREDS_PGHOST")
        if not pgdatabase: missing_creds.append("NEON_CREDS_PGDATABASE")
        if not pguser: missing_creds.append("NEON_CREDS_PGUSER")
        if not pgpassword: missing_creds.append("NEON_CREDS_PGPASSWORD")
        
        raise ValueError(
            f"Neither NEON_DATABASE_URL nor individual Neon credentials are properly set. "
            f"Missing: {', '.join(missing_creds)}"
        )

ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://").replace("?sslmode=require", "")

engine = create_async_engine(
    ASYNC_DATABASE_URL, 
    echo=True, 
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "ssl": "require",
        "prepared_statement_cache_size": 0,
        "server_settings": {
            "application_name": "devin_issues_app"
        }
    }
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from .models import Base

load_dotenv()

neon_host = "ep-sweet-breeze-a84hge8c-pooler.eastus2.azure.neon.tech"
neon_db = "neondb"
neon_user = "neondb_owner"
neon_password = "npg_iw4GofnvpQ3m"

DATABASE_URL = f"postgresql://{neon_user}:{neon_password}@{neon_host}/{neon_db}"

if not DATABASE_URL:
    raise ValueError("NEON_DATABASE_URL environment variable is not set")

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

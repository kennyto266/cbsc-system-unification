"""
CBSC Strategy Management System Database Configuration
CBSC 策略管理系統數據庫配置

Database connection and session management
數據庫連接和會話管理
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from .config import settings

# Create async database engine
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.debug,
    future=True
)

# Create session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create base model class
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


async def get_db():
    """
    Get database session
    獲取數據庫會話
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
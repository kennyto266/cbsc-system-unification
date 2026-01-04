"""
Database configuration and session management.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
from .config import settings


# Create async engine
# For SQLite: sqlite+aiosqlite:///./cbsc.db
# For PostgreSQL: postgresql+asyncpg://user:password@host:port/database
engine_url = settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
engine_url = engine_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    engine_url,
    echo=settings.DEBUG,
    future=True,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that yields database sessions.

    Usage in FastAPI:
        @app.get("/users/")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database - create all tables"""
    async with engine.begin() as conn:
        # Import all models here to ensure they are registered with Base
        from models import user
        # Import other models as needed
        # from models import strategy, backtest
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections"""
    await engine.dispose()

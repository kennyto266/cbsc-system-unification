"""
Database connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class Database:
    """
    Database manager for the strategies module
    """

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = None
        self.SessionLocal = None
        self._connected = False

    def connect(self):
        """
        Initialize database connection
        """
        if self._connected:
            return

        logger.info(f"Connecting to database: {self.db_url}")

        # Create engine
        self.engine = create_engine(
            self.db_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        self._connected = True
        logger.info("Database connected successfully")

    def disconnect(self):
        """
        Close database connection
        """
        if self.engine:
            self.engine.dispose()
            self._connected = False
            logger.info("Database disconnected")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session with automatic cleanup
        """
        if not self._connected:
            raise RuntimeError("Database not connected. Call connect() first.")

        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def get_db_sync(self) -> Generator[Session, None, None]:
        """
        Get database session for sync context (FastAPI dependency)
        """
        if not self._connected:
            raise RuntimeError("Database not connected. Call connect() first.")

        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    async def get_db_async(self) -> Generator[Session, None, None]:
        """
        Get database session for async context
        """
        if not self._connected:
            raise RuntimeError("Database not connected. Call connect() first.")

        # For async compatibility, we yield a sync session
        # In production, consider using asyncpg + sqlalchemy async
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def create_tables(self):
        """
        Create all tables based on models
        """
        if not self._connected:
            raise RuntimeError("Database not connected. Call connect() first.")

        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")

    def health_check(self) -> dict:
        """
        Check database health
        """
        if not self._connected:
            return {"status": "unhealthy", "message": "Not connected"}

        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
                return {"status": "healthy", "message": "Database accessible"}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "message": str(e)}
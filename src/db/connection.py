"""
Database Connection Manager

Handles database connection pooling, optimization, and session management.
"""

import logging
import time
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event, Engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """Database connection manager with optimized pooling"""

    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo_sql: bool = False
    ):
        """
        Initialize database connection manager.

        Args:
            database_url: Database connection URL
            pool_size: Size of the connection pool
            max_overflow: Max overflow connections
            pool_timeout: Connection acquisition timeout (seconds)
            pool_recycle: Connection recycle time (seconds)
            echo_sql: Whether to echo SQL statements
        """
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo_sql = echo_sql

        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[scoped_session] = None
        self.logger = logging.getLogger(__name__)

    def create_engine(self) -> Engine:
        """
        Create optimized database engine with connection pooling.

        Returns:
            SQLAlchemy Engine instance
        """
        if self.engine is not None:
            return self.engine

        # Determine database type from URL
        is_postgresql = "postgresql" in self.database_url
        is_sqlite = "sqlite" in self.database_url

        # Build connect args based on database type
        connect_args = {}
        if is_postgresql:
            connect_args = {
                "application_name": "cbsc_quant_trading",
                "connect_timeout": 10,
            }
            # SSL settings (optional, configure based on environment)
            # connect_args.update({
            #     "sslmode": "require",
            # })

        # Create engine with QueuePool
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=self.pool_recycle,  # Recycle connections after N seconds
            pool_timeout=self.pool_timeout,  # Wait N seconds for connection
            echo=self.echo_sql,
            connect_args=connect_args,
        )

        # Setup connection event listeners
        self._setup_connection_listeners(is_sqlite)

        # Create session factory
        self.SessionLocal = scoped_session(
            sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
        )

        self.logger.info(f"Database engine created: pool_size={self.pool_size}, max_overflow={self.max_overflow}")
        return self.engine

    def _setup_connection_listeners(self, is_sqlite: bool = False):
        """Setup connection event listeners for monitoring"""

        @event.listens_for(self.engine, "connect")
        def set_connection_params(dbapi_connection, connection_record):
            """Set connection parameters"""
            if is_sqlite:
                # SQLite optimizations
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=-10000")  # 10MB cache
                cursor.close()

        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Record query start time"""
            context._query_start_time = time.time()

        @event.listens_for(self.engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log slow queries"""
            total = time.time() - context._query_start_time
            if total > 1.0:  # Log queries taking > 1 second
                self.logger.warning(
                    f"Slow query ({total:.3f}s): {statement[:200]}..."
                )

        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Log connection checkout from pool"""
            self.logger.debug("Connection checked out from pool")

        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Log connection checkin to pool"""
            self.logger.debug("Connection returned to pool")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get database session context manager.

        Yields:
            SQLAlchemy Session instance

        Example:
            with db_manager.get_session() as session:
                user = session.query(User).first()
        """
        if self.SessionLocal is None:
            self.create_engine()

        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def get_db_session(self) -> Generator[Session, None, None]:
        """
        Get database session for FastAPI dependency injection.

        Yields:
            SQLAlchemy Session instance

        Example:
            @app.get("/users")
            def get_users(db: Session = Depends(db_manager.get_db_session)):
                return db.query(User).all()
        """
        if self.SessionLocal is None:
            self.create_engine()

        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def health_check(self) -> dict:
        """
        Check database and connection pool health.

        Returns:
            Health check result dict
        """
        try:
            if self.engine is None:
                return {
                    "status": "unhealthy",
                    "error": "Database engine not initialized"
                }

            with self.get_session() as session:
                session.execute("SELECT 1")

            pool = self.engine.pool
            return {
                "status": "healthy",
                "pool_size": self.pool_size,
                "max_overflow": self.max_overflow,
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "database_url": self._safe_url()
            }
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def _safe_url(self) -> str:
        """Return safe URL without password"""
        if "://" not in self.database_url:
            return self.database_url

        parts = self.database_url.split("://")
        if len(parts) != 2:
            return self.database_url

        scheme, rest = parts
        if "@" in rest:
            credentials, host_port = rest.split("@", 1)
            username = credentials.split(":")[0]
            return f"{scheme}://{username}:***@{host_port}"
        return f"{scheme}://***"

    def close(self):
        """Close all database connections and dispose engine"""
        if self.SessionLocal is not None:
            self.SessionLocal.close()
            self.SessionLocal = None

        if self.engine is not None:
            self.engine.dispose()
            self.engine = None
            self.logger.info("Database connections closed")

    def __enter__(self):
        """Context manager entry"""
        self.create_engine()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Global database manager instance (will be initialized with actual config)
_global_db_manager: Optional[DatabaseConnectionManager] = None


def get_db_manager() -> DatabaseConnectionManager:
    """Get global database manager instance"""
    global _global_db_manager
    if _global_db_manager is None:
        # Default configuration - should be overridden with actual settings
        _global_db_manager = DatabaseConnectionManager(
            database_url="sqlite:///cbsc_trading.db",  # Default, should be configured
            pool_size=10,
            max_overflow=5
        )
    return _global_db_manager


def init_db(
    database_url: str,
    pool_size: int = 20,
    max_overflow: int = 10,
    echo_sql: bool = False
) -> DatabaseConnectionManager:
    """
    Initialize global database manager.

    Args:
        database_url: Database connection URL
        pool_size: Size of the connection pool
        max_overflow: Max overflow connections
        echo_sql: Whether to echo SQL statements

    Returns:
        DatabaseConnectionManager instance
    """
    global _global_db_manager
    _global_db_manager = DatabaseConnectionManager(
        database_url=database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        echo_sql=echo_sql
    )
    _global_db_manager.create_engine()
    return _global_db_manager

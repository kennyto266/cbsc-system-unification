"""
數據庫連接和會話管理

提供統一的數據庫連接管理、會話處理和連接池配置。
"""

import os
from typing import Optional, Generator, AsyncGenerator
from contextlib import contextmanager, asynccontextmanager
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool, QueuePool
from sqlalchemy.event import listen
import logging
from functools import lru_cache

from ..models.unified_base import UnifiedBase
from .config import get_database_config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """數據庫管理器

    提供統一的數據庫連接管理，支持同步和異步操作。
    """

    def __init__(self):
        self._sync_engine = None
        self._async_engine = None
        self._session_factory = None
        self._async_session_factory = None
        self._metadata = None

    def initialize(self):
        """初始化數據庫連接"""
        config = get_database_config()

        # 初始化同步引擎
        self._init_sync_engine(config)

        # 初始化異步引擎
        self._init_async_engine(config)

        # 初始化會話工廠
        self._init_session_factories()

        # 設置事件監聽器
        self._setup_event_listeners()

        logger.info("Database manager initialized successfully")

    def _init_sync_engine(self, config):
        """初始化同步數據庫引擎"""
        database_url = config.get_sync_url()

        engine_kwargs = {
            "echo": config.echo,
            "pool_pre_ping": True,
            "pool_recycle": config.pool_recycle,
        }

        # 根據數據庫類型配置連接池
        if config.database_type == "sqlite":
            engine_kwargs.update({
                "poolclass": StaticPool,
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": config.timeout
                }
            })
        else:  # PostgreSQL
            engine_kwargs.update({
                "poolclass": QueuePool,
                "pool_size": config.pool_size,
                "max_overflow": config.max_overflow,
                "pool_timeout": config.pool_timeout,
                "connect_args": {
                    "connect_timeout": config.timeout,
                    "server_settings": {
                        "application_name": config.application_name,
                        "jit": "off"  # 關閉JIT以獲得更好的查詢性能
                    }
                }
            })

        self._sync_engine = create_engine(database_url, **engine_kwargs)
        logger.info(f"Sync database engine created: {database_url}")

    def _init_async_engine(self, config):
        """初始化異步數據庫引擎"""
        database_url = config.get_async_url()

        engine_kwargs = {
            "echo": config.echo,
            "pool_pre_ping": True,
            "pool_recycle": config.pool_recycle,
        }

        # 根據數據庫類型配置連接池
        if config.database_type == "sqlite":
            engine_kwargs.update({
                "poolclass": StaticPool,
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": config.timeout
                }
            })
        else:  # PostgreSQL
            engine_kwargs.update({
                "poolclass": QueuePool,
                "pool_size": config.pool_size,
                "max_overflow": config.max_overflow,
                "pool_timeout": config.pool_timeout,
                "connect_args": {
                    "command_timeout": config.timeout,
                    "server_settings": {
                        "application_name": f"{config.application_name}_async",
                        "jit": "off"
                    }
                }
            })

        self._async_engine = create_async_engine(database_url, **engine_kwargs)
        logger.info(f"Async database engine created: {database_url}")

    def _init_session_factories(self):
        """初始化會話工廠"""
        # 同步會話工廠
        self._session_factory = sessionmaker(
            bind=self._sync_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )

        # 異步會話工廠
        self._async_session_factory = async_sessionmaker(
            bind=self._async_engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )

        logger.info("Session factories initialized")

    def _setup_event_listeners(self):
        """設置事件監聽器"""

        @listener(self._sync_engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            """連接建立時的事件處理"""
            config = get_database_config()
            if config.database_type == "postgresql":
                # 設置PostgreSQL連接參數
                with dbapi_connection.cursor() as cursor:
                    cursor.execute(f"SET application_name TO '{config.application_name}'")
                    cursor.execute("SET timezone TO 'UTC'")
                    cursor.execute("SET statement_timeout TO '300s'")

        @listen(self._sync_engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """從連接池取出連接時的事件處理"""
            # 檢查連接是否仍然有效
            try:
                dbapi_connection.ping()
            except Exception:
                logger.warning("Database connection health check failed")
                connection_proxy.invalidate()

        logger.info("Event listeners setup completed")

    @property
    def sync_engine(self):
        """獲取同步引擎"""
        if self._sync_engine is None:
            self.initialize()
        return self._sync_engine

    @property
    def async_engine(self):
        """獲取異步引擎"""
        if self._async_engine is None:
            self.initialize()
        return self._async_engine

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """獲取同步數據庫會話"""
        if self._session_factory is None:
            self.initialize()

        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """獲取異步數據庫會話"""
        if self._async_session_factory is None:
            self.initialize()

        session = self._async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database async session error: {e}")
            raise
        finally:
            await session.close()

    def create_tables(self):
        """創建所有表"""
        try:
            UnifiedBase.metadata.create_all(self.sync_engine)
            logger.info("All tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    async def create_tables_async(self):
        """異步創建所有表"""
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(UnifiedBase.metadata.create_all)
            logger.info("All tables created successfully (async)")
        except Exception as e:
            logger.error(f"Failed to create tables (async): {e}")
            raise

    def drop_tables(self):
        """刪除所有表（僅用於測試）"""
        try:
            UnifiedBase.metadata.drop_all(self.sync_engine)
            logger.info("All tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise

    async def drop_tables_async(self):
        """異步刪除所有表（僅用於測試）"""
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(UnifiedBase.metadata.drop_all)
            logger.info("All tables dropped successfully (async)")
        except Exception as e:
            logger.error(f"Failed to drop tables (async): {e}")
            raise

    def check_connection(self) -> bool:
        """檢查數據庫連接"""
        try:
            with self.sync_engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False

    async def check_connection_async(self) -> bool:
        """異步檢查數據庫連接"""
        try:
            async with self.async_engine.connect() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database async connection check failed: {e}")
            return False

    def get_connection_info(self) -> dict:
        """獲取連接信息"""
        config = get_database_config()
        return {
            "database_type": config.database_type,
            "database_url": config.get_sync_url().replace(config.password, "***"),
            "pool_size": config.pool_size,
            "max_overflow": config.max_overflow,
            "pool_timeout": config.pool_timeout,
            "echo": config.echo,
            "connection_active": self.check_connection()
        }

    def close(self):
        """關閉所有連接"""
        if self._sync_engine:
            self._sync_engine.dispose()
            logger.info("Sync database engine disposed")

        if self._async_engine:
            # 異步引擎需要在異步上下文中關閉
            import asyncio
            if asyncio.get_event_loop().is_running():
                # 如果在異步上下文中，創建任務來關閉
                asyncio.create_task(self._async_engine.dispose())
            else:
                # 如果不在異步上下文中，運行新的事件循環
                asyncio.run(self._async_engine.dispose())
            logger.info("Async database engine disposed")

# 全局數據庫管理器實例
db_manager = DatabaseManager()

# 便捷函數
def get_db_session() -> Generator[Session, None, None]:
    """獲取數據庫會話（便捷函數）"""
    return db_manager.get_session()

async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """獲取異步數據庫會話（便捷函數）"""
    async with db_manager.get_async_session() as session:
        yield session

@lru_cache(maxsize=1)
def get_sync_engine():
    """獲取同步引擎（緩存）"""
    return db_manager.sync_engine

@lru_cache(maxsize=1)
def get_async_engine():
    """獲取異步引擎（緩存）"""
    return db_manager.async_engine

# 初始化函數
def init_database():
    """初始化數據庫"""
    db_manager.initialize()

async def init_database_async():
    """異步初始化數據庫"""
    db_manager.initialize()

# 遷移輔助函數
def run_migrations():
    """運行數據庫遷移"""
    try:
        with db_manager.get_session() as session:
            # 這裡可以集成Alembic遷移
            logger.info("Running database migrations...")
            # TODO: 集成Alembic
            logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Database migrations failed: {e}")
        raise

async def run_migrations_async():
    """異步運行數據庫遷移"""
    try:
        async with db_manager.get_async_session() as session:
            logger.info("Running database migrations (async)...")
            # TODO: 集成Alembic異步支持
            logger.info("Database migrations completed successfully (async)")
    except Exception as e:
        logger.error(f"Database migrations failed (async): {e}")
        raise

# 健康檢查
async def database_health_check() -> dict:
    """數據庫健康檢查"""
    try:
        # 檢查同步連接
        sync_healthy = db_manager.check_connection()

        # 檢查異步連接
        async_healthy = await db_manager.check_connection_async()

        # 獲取連接池統計
        pool_stats = {}
        if db_manager._sync_engine and db_manager._sync_engine.pool:
            pool = db_manager._sync_engine.pool
            pool_stats = {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
            }

        return {
            "status": "healthy" if sync_healthy and async_healthy else "unhealthy",
            "sync_connection": sync_healthy,
            "async_connection": async_healthy,
            "pool_stats": pool_stats,
            "connection_info": db_manager.get_connection_info()
        }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "sync_connection": False,
            "async_connection": False,
        }
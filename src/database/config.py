"""
數據庫配置管理

提供數據庫連接配置、環境變量管理和配置驗證功能。
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """數據庫配置類"""

    # 基本連接信息
    database_type: str = "postgresql"  # postgresql, sqlite
    host: str = "localhost"
    port: int = 5432
    database: str = "cbsc_strategy"  # Match docker-compose.yml
    username: str = "cbsc_user"
    password: str = "cbsc_password"
    schema: str = "public"

    # 連接池配置
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600  # 1小時

    # 連接配置
    timeout: int = 30
    echo: bool = False
    application_name: str = "cbsc_unified"

    # SSL配置
    ssl_mode: Optional[str] = None  # disable, allow, prefer, require, verify-ca, verify-full
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_ca: Optional[str] = None

    # 高級配置
    connection_limit: Optional[int] = None
    statement_timeout: int = 300  # 5分鐘
    idle_in_transaction_session_timeout: int = 600  # 10分鐘

    # 備份和復制
    backup_enabled: bool = False
    backup_retention_days: int = 30
    replication_enabled: bool = False

    # 性能調優
    shared_buffers: Optional[str] = None  # PostgreSQL設置
    effective_cache_size: Optional[str] = None
    work_mem: Optional[str] = None
    maintenance_work_mem: Optional[str] = None

    # 監控和日誌
    log_min_duration_statement: int = 1000  # 毫秒
    log_checkpoints: bool = True
    log_connections: bool = True
    log_disconnections: bool = True

    def __post_init__(self):
        """初始化後處理"""
        # 從環境變量加載配置
        self._load_from_env()
        # 驗證配置
        self._validate_config()

    def _load_from_env(self):
        """從環境變量加載配置"""
        env_mappings = {
            "CBSC_DB_TYPE": "database_type",
            "CBSC_DB_HOST": "host",
            "CBSC_DB_PORT": "port",
            "CBSC_DB_NAME": "database",
            "CBSC_DB_USER": "username",
            "CBSC_DB_PASSWORD": "password",
            "CBSC_DB_SCHEMA": "schema",
            "CBSC_DB_POOL_SIZE": "pool_size",
            "CBSC_DB_MAX_OVERFLOW": "max_overflow",
            "CBSC_DB_POOL_TIMEOUT": "pool_timeout",
            "CBSC_DB_POOL_RECYCLE": "pool_recycle",
            "CBSC_DB_TIMEOUT": "timeout",
            "CBSC_DB_ECHO": "echo",
            "CBSC_DB_APP_NAME": "application_name",
            "CBSC_DB_SSL_MODE": "ssl_mode",
            "CBSC_DB_SSL_CERT": "ssl_cert",
            "CBSC_DB_SSL_KEY": "ssl_key",
            "CBSC_DB_SSL_CA": "ssl_ca",
            "CBSC_DB_CONNECTION_LIMIT": "connection_limit",
            "CBSC_DB_STATEMENT_TIMEOUT": "statement_timeout",
            "CBSC_DB_IDLE_TIMEOUT": "idle_in_transaction_session_timeout",
            "CBSC_DB_BACKUP_ENABLED": "backup_enabled",
            "CBSC_DB_BACKUP_RETENTION": "backup_retention_days",
            "CBSC_DB_REPLICATION_ENABLED": "replication_enabled",
        }

        for env_var, attr_name in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # 類型轉換
                current_value = getattr(self, attr_name)
                if isinstance(current_value, bool):
                    setattr(self, attr_name, env_value.lower() in ("true", "1", "yes", "on"))
                elif isinstance(current_value, int):
                    setattr(self, attr_name, int(env_value))
                else:
                    setattr(self, attr_name, env_value)

        # 特殊處理：SQLite配置
        if self.database_type == "sqlite":
            self.database = os.getenv("CBSC_DB_PATH", self.database)
            # SQLite不需要連接池配置
            self.pool_size = 1
            self.max_overflow = 0

    def _validate_config(self):
        """驗證配置"""
        errors = []

        # 驗證必需字段
        if self.database_type not in ["postgresql", "sqlite"]:
            errors.append(f"Unsupported database type: {self.database_type}")

        if self.database_type == "postgresql":
            if not self.host:
                errors.append("Host is required for PostgreSQL")
            if not self.username:
                errors.append("Username is required for PostgreSQL")
            if not self.database:
                errors.append("Database name is required for PostgreSQL")
            if self.port < 1 or self.port > 65535:
                errors.append("Port must be between 1 and 65535")

        elif self.database_type == "sqlite":
            if not self.database:
                errors.append("Database file path is required for SQLite")

        # 驗證連接池配置
        if self.pool_size < 1:
            errors.append("Pool size must be at least 1")
        if self.max_overflow < 0:
            errors.append("Max overflow cannot be negative")
        if self.pool_timeout < 0:
            errors.append("Pool timeout cannot be negative")
        if self.pool_recycle < 0:
            errors.append("Pool recycle cannot be negative")

        # 驗證超時配置
        if self.timeout < 0:
            errors.append("Timeout cannot be negative")
        if self.statement_timeout < 0:
            errors.append("Statement timeout cannot be negative")

        if errors:
            error_msg = "Database configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            raise ValueError(error_msg)

    def get_sync_url(self) -> str:
        """獲取同步數據庫連接URL"""
        if self.database_type == "postgresql":
            url = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
            if self.schema != "public":
                url += f"?options=-csearch_path%3D{self.schema}"
        elif self.database_type == "sqlite":
            url = f"sqlite:///{self.database}"
        else:
            raise ValueError(f"Unsupported database type: {self.database_type}")

        return url

    def get_async_url(self) -> str:
        """獲取異步數據庫連接URL"""
        if self.database_type == "postgresql":
            url = f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
            if self.schema != "public":
                url += f"?options=-csearch_path%3D{self.schema}"
        elif self.database_type == "sqlite":
            url = f"sqlite+aiosqlite:///{self.database}"
        else:
            raise ValueError(f"Unsupported database type: {self.database_type}")

        return url

    def get_connection_args(self) -> Dict[str, Any]:
        """獲取連接參數"""
        if self.database_type == "postgresql":
            args = {
                "connect_timeout": self.timeout,
                "server_settings": {
                    "application_name": self.application_name,
                    "jit": "off",
                    "statement_timeout": f"{self.statement_timeout}s",
                }
            }

            # SSL配置
            if self.ssl_mode:
                ssl_config = {"sslmode": self.ssl_mode}
                if self.ssl_cert:
                    ssl_config["sslcert"] = self.ssl_cert
                if self.ssl_key:
                    ssl_config["sslkey"] = self.ssl_key
                if self.ssl_ca:
                    ssl_config["sslrootcert"] = self.ssl_ca
                args.update(ssl_config)

            return args

        elif self.database_type == "sqlite":
            return {
                "check_same_thread": False,
                "timeout": self.timeout
            }

        return {}

    def get_pool_args(self) -> Dict[str, Any]:
        """獲取連接池參數"""
        if self.database_type == "sqlite":
            return {
                "poolclass": "sqlalchemy.pool.StaticPool",
                "connect_args": {"check_same_thread": False, "timeout": self.timeout}
            }

        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": True
        }

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典（隱藏敏感信息）"""
        return {
            "database_type": self.database_type,
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "password": "***" if self.password else None,
            "schema": self.schema,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "timeout": self.timeout,
            "echo": self.echo,
            "application_name": self.application_name,
            "ssl_mode": self.ssl_mode,
        }

    def get_postgres_config(self) -> Dict[str, str]:
        """獲取PostgreSQL配置建議"""
        if self.database_type != "postgresql":
            return {}

        return {
            "shared_buffers": self.shared_buffers or "256MB",
            "effective_cache_size": self.effective_cache_size or "1GB",
            "work_mem": self.work_mem or "4MB",
            "maintenance_work_mem": self.maintenance_work_mem or "64MB",
            "log_min_duration_statement": str(self.log_min_duration_statement),
            "log_checkpoints": "on" if self.log_checkpoints else "off",
            "log_connections": "on" if self.log_connections else "off",
            "log_disconnections": "on" if self.log_disconnections else "off",
            "jit": "off",  # 關閉JIT以獲得更好的OLTP性能
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "DatabaseConfig":
        """從字典創建配置"""
        # 過濾掉不存在的字段
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_dict = {k: v for k, v in config_dict.items() if k in valid_fields}
        return cls(**filtered_dict)

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """從環境變量創建配置"""
        return cls()

@lru_cache(maxsize=1)
def get_database_config() -> DatabaseConfig:
    """獲取數據庫配置（緩存）"""
    return DatabaseConfig.from_env()

def create_test_config() -> DatabaseConfig:
    """創建測試配置"""
    return DatabaseConfig(
        database_type="sqlite",
        database=":memory:",
        echo=True,
        pool_size=1,
        max_overflow=0
    )

def create_development_config() -> DatabaseConfig:
    """創建開發配置"""
    return DatabaseConfig(
        database_type=os.getenv("CBSC_DB_TYPE", "postgresql"),
        host=os.getenv("CBSC_DB_HOST", "localhost"),
        port=int(os.getenv("CBSC_DB_PORT", "5432")),
        database=os.getenv("CBSC_DB_NAME", "cbsc_dev"),
        username=os.getenv("CBSC_DB_USER", "cbsc_dev"),
        password=os.getenv("CBSC_DB_PASSWORD", "dev_password"),
        echo=os.getenv("CBSC_DB_ECHO", "false").lower() == "true",
        pool_size=5,
        max_overflow=10
    )

def create_production_config() -> DatabaseConfig:
    """創建生產配置"""
    return DatabaseConfig(
        database_type="postgresql",
        host=os.getenv("CBSC_DB_HOST", "localhost"),
        port=int(os.getenv("CBSC_DB_PORT", "5432")),
        database=os.getenv("CBSC_DB_NAME", "cbsc_prod"),
        username=os.getenv("CBSC_DB_USER", "cbsc_prod_user"),
        password=os.getenv("CBSC_DB_PASSWORD", ""),
        echo=False,
        pool_size=20,
        max_overflow=30,
        pool_timeout=60,
        ssl_mode="require",
        backup_enabled=True,
        backup_retention_days=90,
        shared_buffers="1GB",
        effective_cache_size="4GB",
        work_mem="16MB",
        maintenance_work_mem="128MB"
    )

# 配置驗證函數
def validate_database_connection(config: DatabaseConfig) -> tuple[bool, Optional[str]]:
    """驗證數據庫連接配置"""
    try:
        if config.database_type == "postgresql":
            # 檢查PostgreSQL連接參數
            if not config.host:
                return False, "PostgreSQL host is required"
            if not config.username:
                return False, "PostgreSQL username is required"
            if not config.database:
                return False, "PostgreSQL database name is required"
            if config.port < 1 or config.port > 65535:
                return False, "PostgreSQL port must be between 1 and 65535"

        elif config.database_type == "sqlite":
            # 檢查SQLite路徑
            if not config.database:
                return False, "SQLite database path is required"
            # 檢查目錄是否存在
            import os
            db_dir = os.path.dirname(config.database)
            if db_dir and not os.path.exists(db_dir):
                return False, f"SQLite database directory does not exist: {db_dir}"

        return True, None

    except Exception as e:
        return False, f"Configuration validation error: {str(e)}"

# 環境檢測
def detect_environment() -> str:
    """檢測運行環境"""
    env = os.getenv("CBSC_ENV", "development").lower()

    if env in ["prod", "production"]:
        return "production"
    elif env in ["test", "testing"]:
        return "test"
    elif env in ["dev", "development"]:
        return "development"
    else:
        logger.warning(f"Unknown environment: {env}, using development")
        return "development"

def get_config_for_environment(env: Optional[str] = None) -> DatabaseConfig:
    """根據環境獲取配置"""
    if env is None:
        env = detect_environment()

    if env == "production":
        return create_production_config()
    elif env == "test":
        return create_test_config()
    else:
        return create_development_config()
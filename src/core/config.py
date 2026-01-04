"""
CBSC Strategy Management System Configuration
CBSC 策略管理系統配置

Unified configuration system with structured settings.
統一的配置系統，提供結構化的設置。
"""

import os
from pathlib import Path
from typing import List, Optional, Union

# Try importing from pydantic_settings (pydantic v2), fallback to pydantic (v1)
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field, field_validator as validator
    PYDANTIC_V2 = True
except ImportError:
    try:
        from pydantic import BaseSettings, validator, Field
        PYDANTIC_V2 = False
    except ImportError:
        BaseSettings = object  # Ultimate fallback
        Field = lambda **kwargs: kwargs.get("default", None)
        PYDANTIC_V2 = False


class APISettings(BaseSettings):
    """API server configuration"""

    if PYDANTIC_V2:
        model_config = SettingsConfigDict(
            env_prefix="API_",
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore"
        )
    else:
        class Config:
            env_prefix = "API_"
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False

    title: str = Field(default="CBSC Trading Platform API", description="API title")
    version: str = Field(default="2.0.0", description="API version")
    description: str = Field(default="CBSC量化交易策略管理平台", description="API description")
    prefix: str = Field(default="/api/v1", description="API route prefix")

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # CORS settings - include network IP for LAN access
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "http://192.168.1.5:3000",
            "http://192.168.1.5:3006",
            "http://10.5.0.2:3000",
            "http://localhost:3005",
            "http://localhost:8888",
            "null"  # Support for file:// protocol (opening HTML directly)
        ],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default=["*"])
    cors_allow_headers: List[str] = Field(default=["*"])

    # Validator for CORS_ORIGINS to handle both string and list formats
    if PYDANTIC_V2:
        @validator("cors_origins", mode="before")
        @classmethod
        def parse_cors_origins_v2(cls, v: Union[str, List[str]]) -> List[str]:
            if isinstance(v, str):
                # Try to parse as JSON array first
                import json
                try:
                    return json.loads(v)
                except:
                    return [i.strip() for i in v.split(",")]
            return v
    else:
        @validator("cors_origins", pre=True)
        @classmethod
        def parse_cors_origins_v1(cls, v: Union[str, List[str]]) -> List[str]:
            if isinstance(v, str):
                import json
                try:
                    return json.loads(v)
                except:
                    return [i.strip() for i in v.split(",")]
            return v

    # Pagination
    default_page_size: int = Field(default=20, ge=1, le=100)
    max_page_size: int = Field(default=100, ge=1, le=1000)


class DatabaseSettings(BaseSettings):
    """Database configuration"""

    if PYDANTIC_V2:
        model_config = SettingsConfigDict(
            env_prefix="DB_",
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore"
        )
    else:
        class Config:
            env_prefix = "DB_"
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False

    url: str = Field(default="postgresql://cbsc_user:cbsc_password@localhost:5432/cbsc_strategy", description="Database URL")
    echo: bool = Field(default=False, description="Echo SQL queries")

    # Connection pool
    pool_size: int = Field(default=20, ge=1, le=100)
    max_overflow: int = Field(default=10, ge=0, le=50)
    pool_recycle: int = Field(default=3600, description="Pool recycle time in seconds")
    pool_pre_ping: bool = Field(default=True, description="Validate connections before use")

    # Performance
    slow_query_threshold: float = Field(default=1.0, description="Slow query threshold (seconds)")


class CacheSettings(BaseSettings):
    """Cache configuration"""

    if PYDANTIC_V2:
        model_config = SettingsConfigDict(
            env_prefix="CACHE_",
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore"
        )
    else:
        class Config:
            env_prefix = "CACHE_"
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False

    enabled: bool = Field(default=True, description="Enable caching")
    backend: str = Field(default="redis", description="Cache backend (redis, memory)")

    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL")

    # Cache TTL (seconds)
    default_ttl: int = Field(default=3600, description="Default cache TTL")
    short_ttl: int = Field(default=300, description="Short TTL (5 minutes)")
    long_ttl: int = Field(default=86400, description="Long TTL (24 hours)")

    # Local cache settings
    memory_max_size: int = Field(default=1000, description="LRU cache max size")


class AuthSettings(BaseSettings):
    """Authentication configuration"""

    if PYDANTIC_V2:
        model_config = SettingsConfigDict(
            env_prefix="AUTH_",
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore"
        )
    else:
        class Config:
            env_prefix = "AUTH_"
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False

    secret_key: str = Field(default="change-me-in-production", description="JWT secret key")
    algorithm: str = Field(default="HS256", description="JWT algorithm")

    # Token expiration (seconds)
    access_token_expire: int = Field(default=86400, description="Access token expiration (24 hours)")
    refresh_token_expire: int = Field(default=604800, description="Refresh token expiration (7 days)")

    # MFA
    mfa_enabled: bool = Field(default=False, description="Enable multi-factor authentication")

    # Rate limiting
    max_login_attempts: int = Field(default=5, description="Max login attempts")
    lockout_duration: int = Field(default=900, description="Lockout duration (seconds)")


class InfluxDBSettings(BaseSettings):
    """InfluxDB configuration"""

    if PYDANTIC_V2:
        model_config = SettingsConfigDict(
            env_prefix="INFLUXDB_",
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore"
        )
    else:
        class Config:
            env_prefix = "INFLUXDB_"
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False

    url: str = Field(default="http://localhost:8086", description="InfluxDB URL")
    token: str = Field(default="", description="InfluxDB token")
    org: str = Field(default="CBSC-Development", description="InfluxDB organization")
    bucket: str = Field(default="strategy_metrics", description="Default bucket")
    timeout: int = Field(default=10000, description="Request timeout (ms)")


class MonitoringSettings(BaseSettings):
    """Monitoring configuration"""

    if PYDANTIC_V2:
        model_config = SettingsConfigDict(
            env_prefix="MONITORING_",
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore"
        )
    else:
        class Config:
            env_prefix = "MONITORING_"
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False

    enabled: bool = Field(default=True, description="Enable monitoring")
    prometheus_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, description="Metrics endpoint port")


class Settings(BaseSettings):
    """
    Main CBSC configuration.
    主配置類。

    Usage:
        settings = Settings()
        db_url = settings.database.url
        api_host = settings.api.host
    """

    if PYDANTIC_V2:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore"
        )
    else:
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False

    # Application
    app_name: str = "CBSC Strategy Management System"
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = False

    # File Upload
    upload_dir: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Project paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    src_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)

    # Sub-configurations (nested settings)
    api: APISettings = Field(default_factory=APISettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    influxdb: InfluxDBSettings = Field(default_factory=InfluxDBSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"

    def get_api_url(self) -> str:
        """Get full API URL"""
        return f"http://{self.api.host}:{self.api.port}{self.api.prefix}"

    # Backwards compatibility - expose old-style attributes
    @property
    def api_host(self) -> str:
        return self.api.host

    @property
    def api_port(self) -> int:
        return self.api.port

    @property
    def api_prefix(self) -> str:
        return self.api.prefix

    @property
    def database_url(self) -> str:
        return self.database.url

    @property
    def redis_url(self) -> str:
        return self.cache.redis_url

    @property
    def jwt_secret(self) -> str:
        return self.auth.secret_key

    @property
    def jwt_algorithm(self) -> str:
        return self.auth.algorithm

    @property
    def influxdb_url(self) -> str:
        return self.influxdb.url

    @property
    def influxdb_token(self) -> str:
        return self.influxdb.token

    @property
    def influxdb_org(self) -> str:
        return self.influxdb.org

    @property
    def influxdb_bucket(self) -> str:
        return self.influxdb.bucket


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def init_settings(**kwargs) -> Settings:
    """Initialize settings with custom values"""
    global _settings
    _settings = Settings(**kwargs)
    return _settings


# Create default settings instance for backwards compatibility
settings = get_settings()

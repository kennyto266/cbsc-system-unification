"""
Configuration Data Models

Pydantic - based configuration models with type validation and serialization.
"""

import os
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class Environment(str, Enum):
    """Supported deployment environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseConfig(BaseModel):
    """Database configuration with PostgreSQL settings."""

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="quant_system", description="Database name")
    user: str = Field(default="quant_user", description="Database user")
    password: str = Field(default="", description="Database password")
    ssl_mode: str = Field(default="prefer", description="SSL mode")
    pool_size: int = Field(default=20, description="Connection pool size")
    max_overflow: int = Field(default=30, description="Maximum overflow connections")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    pool_recycle: int = Field(default=3600, description="Pool recycle time in seconds")
    echo: bool = Field(default=False, description="Enable SQL logging")

    @validator("password")
    def validate_password(cls, v):
        if not v:
            v = os.getenv("DB_PASSWORD", "quant_password")
        return v

    @property
    def url(self) -> str:
        """Generate database URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisConfig(BaseModel):
    """Redis configuration with clustering support."""

    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database number")
    password: str = Field(default="", description="Redis password")
    max_connections: int = Field(default=100, description="Maximum connections")
    retry_on_timeout: bool = Field(default=True, description="Retry on timeout")
    socket_timeout: int = Field(default=5, description="Socket timeout")
    socket_connect_timeout: int = Field(default=5, description="Connection timeout")
    max_memory: str = Field(default="512mb", description="Maximum memory")
    max_memory_policy: str = Field(default="allkeys - lru", description="Memory policy")

    @validator("password")
    def validate_password(cls, v):
        if not v:
            v = os.getenv("REDIS_PASSWORD", "redis_password")
        return v

    @property
    def url(self) -> str:
        """Generate Redis URL."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class APIConfig(BaseModel):
    """API configuration for external services."""

    base_url: str = Field(
        default="http://18.180.162.113:9191", description="API base URL"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retries")
    retry_delay: float = Field(default=1.0, description="Retry delay in seconds")
    rate_limit: int = Field(default=100, description="Rate limit per minute")
    chunk_size: int = Field(default=1000, description="Chunk size for bulk requests")

    # Stock API specific
    stock_api_url: str = Field(default="", description="Stock API URL")
    stock_api_timeout: int = Field(default=10, description="Stock API timeout")

    @validator("stock_api_url")
    def validate_stock_api_url(cls, v):
        if not v:
            v = os.getenv("STOCK_API_URL", "http://18.180.162.113:9191 / inst / getInst")
        return v


class TradingConfig(BaseModel):
    """Trading system configuration."""

    enabled: bool = Field(default=True, description="Enable trading")
    environment: str = Field(default="SIMULATE", description="Trading environment")
    max_position_size: float = Field(
        default=100000, description="Maximum position size"
    )
    risk_limit: float = Field(default=0.02, description="Risk limit (2%)")
    max_drawdown: float = Field(default=0.15, description="Maximum drawdown (15%)")

    # Futu API settings
    futu_host: str = Field(default="127.0.0.1", description="Futu API host")
    futu_port: int = Field(default=11111, description="Futu API port")
    futu_env: str = Field(default="SIMULATE", description="Futu environment")

    # Trading hours
    market_open: str = Field(default="09:30", description="Market open time")
    market_close: str = Field(default="16:00", description="Market close time")
    lunch_start: str = Field(default="12:00", description="Lunch break start")
    lunch_end: str = Field(default="13:00", description="Lunch break end")

    # Strategy settings
    default_sharpe_threshold: float = Field(
        default=1.0, description="Sharpe ratio threshold"
    )
    risk_free_rate: float = Field(default=0.03, description="Risk - free rate (3%)")

    # Batch processing
    batch_size: int = Field(default=10, description="Batch processing size")
    max_workers: int = Field(default=100, description="Maximum workers")


class MonitoringConfig(BaseModel):
    """Monitoring and observability configuration."""

    enabled: bool = Field(default=True, description="Enable monitoring")

    # Prometheus
    prometheus_port: int = Field(default=9090, description="Prometheus port")
    prometheus_host: str = Field(default="localhost", description="Prometheus host")
    metrics_path: str = Field(default="/metrics", description="Metrics endpoint")

    # Grafana
    grafana_port: int = Field(default=3000, description="Grafana port")
    grafana_host: str = Field(default="localhost", description="Grafana host")
    grafana_user: str = Field(default="admin", description="Grafana username")
    grafana_password: str = Field(default="admin", description="Grafana password")

    # Alerting
    alertmanager_port: int = Field(default=9093, description="AlertManager port")
    alert_webhook_url: str = Field(default="", description="Alert webhook URL")

    # Jaeger tracing
    jaeger_port: int = Field(default=16686, description="Jaeger UI port")
    jaeger_agent_port: int = Field(default=6831, description="Jaeger agent port")

    @validator("grafana_password")
    def validate_grafana_password(cls, v):
        if not v or v == "admin":
            v = os.getenv("GRAFANA_PASSWORD", "admin")
        return v


class SecurityConfig(BaseModel):
    """Security configuration."""

    secret_key: str = Field(default="", description="Secret key for sessions")
    jwt_secret_key: str = Field(default="", description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration: int = Field(default=3600, description="JWT expiration in seconds")

    # SSL / TLS
    ssl_enabled: bool = Field(default=False, description="Enable SSL")
    ssl_cert_path: str = Field(default="", description="SSL certificate path")
    ssl_key_path: str = Field(default="", description="SSL private key path")

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, description="Rate limit requests")
    rate_limit_window: int = Field(
        default=60, description="Rate limit window (seconds)"
    )

    # Access control
    allowed_ips: List[str] = Field(
        default_factory=list, description="Allowed IP addresses"
    )
    blocked_ips: List[str] = Field(
        default_factory=list, description="Blocked IP addresses"
    )

    @validator("secret_key")
    def validate_secret_key(cls, v):
        if not v:
            v = os.getenv("SECRET_KEY", "your_secret_key_for_sessions_here")
        return v

    @validator("jwt_secret_key")
    def validate_jwt_secret_key(cls, v):
        if not v:
            v = os.getenv("JWT_SECRET_KEY", "your_jwt_secret_key_here")
        return v


class TelegramConfig(BaseModel):
    """Telegram bot configuration."""

    enabled: bool = Field(default=False, description="Enable Telegram bot")
    token: str = Field(default="", description="Bot token")
    allowed_user_ids: str = Field(default="", description="Allowed user IDs")
    allowed_chat_ids: str = Field(default="", description="Allowed chat IDs")
    bot_owner_user_id: str = Field(default="", description="Bot owner user ID")

    @validator("token")
    def validate_token(cls, v):
        if not v:
            v = os.getenv("TELEGRAM_BOT_TOKEN", "")
        return v

    @validator("allowed_user_ids")
    def validate_allowed_user_ids(cls, v):
        if not v:
            v = os.getenv("TG_ALLOWED_USER_IDS", "")
        return v

    @validator("bot_owner_user_id")
    def validate_bot_owner_user_id(cls, v):
        if not v:
            v = os.getenv("BOT_OWNER_USER_ID", "")
        return v


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: LogLevel = Field(default=LogLevel.INFO, description="Log level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format",
    )
    file_path: str = Field(default="logs / quant_system.log", description="Log file path")
    max_file_size: str = Field(default="100MB", description="Maximum log file size")
    backup_count: int = Field(default=5, description="Number of backup files")
    rotation: str = Field(
        default="daily", description="Log rotation (daily / weekly / monthly)"
    )

    # Structured logging
    json_enabled: bool = Field(default=True, description="Enable JSON logging")
    include_traceback: bool = Field(
        default=True, description="Include traceback in logs"
    )

    # External logging
    elasticsearch_enabled: bool = Field(
        default=False, description="Enable Elasticsearch logging"
    )
    elasticsearch_url: str = Field(default="", description="Elasticsearch URL")


class SystemConfig(BaseModel):
    """Main system configuration."""

    environment: Environment = Field(
        default=Environment.DEVELOPMENT, description="Environment"
    )
    debug: bool = Field(default=False, description="Debug mode")
    name: str = Field(
        default="Hong Kong Quantitative Trading System", description="System name"
    )
    version: str = Field(default="1.0.0", description="System version")

    # Core configurations
    database: DatabaseConfig = Field(
        default_factory=DatabaseConfig, description="Database config"
    )
    redis: RedisConfig = Field(default_factory=RedisConfig, description="Redis config")
    api: APIConfig = Field(default_factory=APIConfig, description="API config")
    trading: TradingConfig = Field(
        default_factory=TradingConfig, description="Trading config"
    )
    monitoring: MonitoringConfig = Field(
        default_factory=MonitoringConfig, description="Monitoring config"
    )
    security: SecurityConfig = Field(
        default_factory=SecurityConfig, description="Security config"
    )
    telegram: TelegramConfig = Field(
        default_factory=TelegramConfig, description="Telegram config"
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig, description="Logging config"
    )

    # Feature flags
    features: Dict[str, bool] = Field(
        default_factory=lambda: {
            "backtesting": True,
            "real_time_trading": False,
            "portfolio_optimization": True,
            "risk_management": True,
            "technical_indicators": True,
            "fundamental_analysis": True,
            "market_sentiment": True,
            "economic_data": True,
        },
        description="Feature flags",
    )

    class Config:
        """Pydantic configuration."""

        extra = "allow"  # Allow additional fields
        env_prefix = "QUANT_"  # Environment variable prefix
        case_sensitive = False

"""
統一配置管理系統
Unified Configuration Management for Hong Kong Quantitative Trading System

This module provides centralized configuration management using Pydantic settings
with environment variable support, validation, and type safety.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Dict, Any
import os

from pydantic import Field, validator
try:
    from pydantic_settings import BaseSettings
    from pydantic_settings.sources import SettingsSourceDict
except ImportError:
    from pydantic import BaseSettings
    from pydantic.env_settings import SettingsSourceDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    url: str = Field(
        default="sqlite:///./quant_system.db",
        description="Database connection URL"
    )
    echo: bool = Field(
        default=False,
        description="Enable SQLAlchemy query logging"
    )
    pool_size: int = Field(
        default=5,
        description="Database connection pool size"
    )
    max_overflow: int = Field(
        default=10,
        description="Maximum database connection overflow"
    )

    class Config:
        env_prefix = "DB_"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""

    host: str = Field(
        default="localhost",
        description="Redis server host"
    )
    port: int = Field(
        default=6379,
        description="Redis server port"
    )
    db: int = Field(
        default=0,
        description="Redis database number"
    )
    password: Optional[str] = Field(
        default=None,
        description="Redis server password"
    )
    ssl: bool = Field(
        default=False,
        description="Enable Redis SSL connection"
    )

    @property
    def url(self) -> str:
        """Construct Redis URL from settings."""
        auth = f":{self.password}@" if self.password else ""
        ssl_scheme = "rediss" if self.ssl else "redis"
        return f"{ssl_scheme}://{auth}{self.host}:{self.port}/{self.db}"

    class Config:
        env_prefix = "REDIS_"


class APISettings(BaseSettings):
    """API server configuration settings."""

    host: str = Field(
        default="0.0.0.0",
        description="API server host"
    )
    port: int = Field(
        default=8000,
        description="API server port"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    reload: bool = Field(
        default=False,
        description="Enable auto-reload"
    )
    workers: int = Field(
        default=1,
        description="Number of worker processes"
    )
    access_log: bool = Field(
        default=True,
        description="Enable access logging"
    )

    # Security settings
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    allowed_origins: List[str] = Field(
        default=["*"],
        description="CORS allowed origins"
    )

    # Rate limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    rate_limit_requests: int = Field(
        default=100,
        description="Rate limit requests per minute"
    )

    @validator("allowed_origins", pre=True)
    def parse_allowed_origins(cls, v):
        """Parse allowed origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_prefix = "API_"


class DataSettings(BaseSettings):
    """Data source and processing settings."""

    # Central API settings
    central_api_base_url: str = Field(
        default="http://18.180.162.113:9191",
        description="Central API base URL for stock data"
    )
    central_api_timeout: int = Field(
        default=30,
        description="Central API request timeout in seconds"
    )
    central_api_max_retries: int = Field(
        default=3,
        description="Maximum number of API request retries"
    )

    # Government data settings
    gov_data_enabled: bool = Field(
        default=True,
        description="Enable government data sources"
    )
    gov_data_cache_ttl: int = Field(
        default=3600,
        description="Government data cache TTL in seconds"
    )

    # Data processing settings
    max_data_points: int = Field(
        default=10000,
        description="Maximum data points to process"
    )
    data_validation_enabled: bool = Field(
        default=True,
        description="Enable data validation"
    )

    # Cache settings
    cache_enabled: bool = Field(
        default=True,
        description="Enable data caching"
    )
    cache_ttl: int = Field(
        default=300,
        description="Default cache TTL in seconds"
    )

    class Config:
        env_prefix = "DATA_"


class TradingSettings(BaseSettings):
    """Trading system configuration settings."""

    # Risk management
    max_position_size: float = Field(
        default=0.1,
        description="Maximum position size as percentage of portfolio"
    )
    max_drawdown: float = Field(
        default=0.2,
        description="Maximum allowed drawdown"
    )
    risk_free_rate: float = Field(
        default=0.03,
        description="Risk-free rate for Sharpe ratio calculation"
    )

    # Trading parameters
    default_universe: List[str] = Field(
        default=["0700.HK", "0939.HK", "1398.HK", "0388.HK"],
        description="Default trading universe"
    )
    min_sharpe_ratio: float = Field(
        default=0.5,
        description="Minimum acceptable Sharpe ratio"
    )

    # Execution settings
    order_timeout: int = Field(
        default=30,
        description="Order execution timeout in seconds"
    )
    slippage_tolerance: float = Field(
        default=0.001,
        description="Slippage tolerance as percentage"
    )

    # Simulation settings
    simulation_enabled: bool = Field(
        default=True,
        description="Enable trading simulation"
    )
    paper_trading: bool = Field(
        default=True,
        description="Enable paper trading mode"
    )

    @validator("default_universe", pre=True)
    def parse_universe(cls, v):
        """Parse trading universe from string or list."""
        if isinstance(v, str):
            return [symbol.strip() for symbol in v.split(",")]
        return v

    class Config:
        env_prefix = "TRADING_"


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    level: str = Field(
        default="INFO",
        description="Logging level"
    )
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )

    # File logging
    file_enabled: bool = Field(
        default=True,
        description="Enable file logging"
    )
    file_path: str = Field(
        default="logs/quant_system.log",
        description="Log file path"
    )
    file_max_size: int = Field(
        default=10485760,  # 10MB
        description="Maximum log file size in bytes"
    )
    file_backup_count: int = Field(
        default=5,
        description="Number of log file backups"
    )

    # Structured logging
    structured: bool = Field(
        default=True,
        description="Enable structured logging"
    )

    # Performance logging
    performance_enabled: bool = Field(
        default=True,
        description="Enable performance logging"
    )

    @validator("level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()

    class Config:
        env_prefix = "LOG_"


class MonitoringSettings(BaseSettings):
    """Monitoring and performance settings."""

    enabled: bool = Field(
        default=True,
        description="Enable monitoring"
    )

    # Metrics collection
    metrics_enabled: bool = Field(
        default=True,
        description="Enable metrics collection"
    )
    metrics_port: int = Field(
        default=9090,
        description="Metrics server port"
    )

    # Health checks
    health_check_enabled: bool = Field(
        default=True,
        description="Enable health checks"
    )
    health_check_interval: int = Field(
        default=60,
        description="Health check interval in seconds"
    )

    # Performance monitoring
    performance_monitoring: bool = Field(
        default=True,
        description="Enable performance monitoring"
    )

    # Alerting
    alert_enabled: bool = Field(
        default=True,
        description="Enable alerting"
    )
    alert_webhook_url: Optional[str] = Field(
        default=None,
        description="Alert webhook URL"
    )

    class Config:
        env_prefix = "MONITORING_"


class Settings(BaseSettings):
    """Main application settings class."""

    # Application settings
    app_name: str = Field(
        default="Hong Kong Quantitative Trading System",
        description="Application name"
    )
    app_version: str = Field(
        default="2.1.0",
        description="Application version"
    )
    environment: str = Field(
        default="development",
        description="Application environment"
    )

    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    api: APISettings = Field(default_factory=APISettings)
    data: DataSettings = Field(default_factory=DataSettings)
    trading: TradingSettings = Field(default_factory=TradingSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)

    # Development settings
    debug: bool = Field(default=False, description="Enable debug mode")
    testing: bool = Field(default=False, description="Enable testing mode")

    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment setting."""
        valid_envs = ["development", "testing", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Invalid environment: {v}. Must be one of {valid_envs}")
        return v.lower()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceDict,
            env_settings: SettingsSourceDict,
            file_secret_settings: SettingsSourceDict,
        ):
            """Customize settings sources for precedence."""
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience functions
def get_database_url() -> str:
    """Get database URL."""
    return get_settings().database.url


def get_redis_url() -> str:
    """Get Redis URL."""
    return get_settings().redis.url


def is_development() -> bool:
    """Check if running in development mode."""
    return get_settings().environment == "development"


def is_production() -> bool:
    """Check if running in production mode."""
    return get_settings().environment == "production"


def is_testing() -> bool:
    """Check if running in testing mode."""
    return get_settings().testing or get_settings().environment == "testing"


# Environment-specific overrides
class DevelopmentSettings(Settings):
    """Development environment settings."""

    api: APISettings = APISettings(
        host="127.0.0.1",
        port=8000,
        debug=True,
        reload=True
    )
    logging: LoggingSettings = LoggingSettings(
        level="DEBUG",
        file_enabled=False
    )


class ProductionSettings(Settings):
    """Production environment settings."""

    api: APISettings = APISettings(
        host="0.0.0.0",
        port=8000,
        debug=False,
        workers=4
    )
    logging: LoggingSettings = LoggingSettings(
        level="INFO",
        file_enabled=True,
        structured=True
    )
    monitoring: MonitoringSettings = MonitoringSettings(
        enabled=True,
        metrics_enabled=True,
        alert_enabled=True
    )


class TestingSettings(Settings):
    """Testing environment settings."""

    database: DatabaseSettings = DatabaseSettings(
        url="sqlite:///:memory:",
        echo=False
    )
    redis: RedisSettings = RedisSettings(
        host="localhost",
        port=16379,  # Different port for testing
        db=15  # Separate database for testing
    )
    api: APISettings = APISettings(
        host="127.0.0.1",
        port=8001,
        debug=True
    )
    logging: LoggingSettings = LoggingSettings(
        level="DEBUG",
        file_enabled=False
    )
    testing: bool = True


def get_settings_by_environment(environment: str) -> Settings:
    """Get settings for specific environment."""
    settings_map = {
        "development": DevelopmentSettings,
        "production": ProductionSettings,
        "testing": TestingSettings,
    }
    settings_class = settings_map.get(environment, Settings)
    return settings_class()
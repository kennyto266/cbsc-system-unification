"""
Risk Management API v2 - Configuration
======================================

Configuration settings for the risk management API.

Author: CBSC Risk Management Team
Version: 2.0.0
"""

from pydantic import BaseSettings, Field
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings
    """

    # API Configuration
    api_title: str = Field(default="CBSC Risk Management API", env="API_TITLE")
    api_version: str = Field(default="2.0.0", env="API_VERSION")
    debug: bool = Field(default=False, env="DEBUG")

    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8002, env="PORT")
    reload: bool = Field(default=False, env="RELOAD")

    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./risk_management.db",
        env="DATABASE_URL"
    )

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )

    # JWT Configuration
    jwt_secret_key: str = Field(
        default="your-secret-key-here",
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Risk Engine Configuration
    risk_calculation_interval: int = Field(
        default=60,
        env="RISK_CALCULATION_INTERVAL"
    )  # seconds

    var_confidence_levels: List[float] = Field(
        default=[0.95, 0.99],
        env="VAR_CONFIDENCE_LEVELS"
    )

    es_confidence_levels: List[float] = Field(
        default=[0.95, 0.99],
        env="ES_CONFIDENCE_LEVELS"
    )

    volatility_windows: List[int] = Field(
        default=[21, 63, 252],  # 1 month, 3 months, 1 year
        env="VOLATILITY_WINDOWS"
    )

    max_drawdown_window: int = Field(
        default=252,
        env="MAX_DRAWDOWN_WINDOW"
    )  # days

    # Alert Configuration
    alert_enabled: bool = Field(default=True, env="ALERT_ENABLED")
    alert_cooldown_period: int = Field(
        default=300,
        env="ALERT_COOLDOWN_PERIOD"
    )  # seconds

    # WebSocket Configuration
    websocket_host: str = Field(default="0.0.0.0", env="WEBSOCKET_HOST")
    websocket_port: int = Field(default=8003, env="WEBSOCKET_PORT")
    websocket_max_connections: int = Field(
        default=1000,
        env="WEBSOCKET_MAX_CONNECTIONS"
    )

    # Dynamic Adjustment Configuration
    dynamic_adjustment_enabled: bool = Field(
        default=True,
        env="DYNAMIC_ADJUSTMENT_ENABLED"
    )

    volatility_target: float = Field(
        default=0.15,
        env="VOLATILITY_TARGET"
    )

    rebalance_threshold: float = Field(
        default=0.05,
        env="REBALANCE_THRESHOLD"
    )

    # InfluxDB Configuration
    influxdb_host: str = Field(default="localhost", env="INFLUXDB_HOST")
    influxdb_port: int = Field(default=8086, env="INFLUXDB_PORT")
    influxdb_database: str = Field(default="risk_metrics", env="INFLUXDB_DATABASE")
    influxdb_username: str = Field(default="", env="INFLUXDB_USERNAME")
    influxdb_password: str = Field(default="", env="INFLUXDB_PASSWORD")

    # Rate Limiting
    rate_limits: dict = Field(
        default={
            "default": "100/hour",
            "alerts": "50/hour",
            "reports": "20/hour",
            "adjustments": "20/hour"
        },
        env="RATE_LIMITS"
    )

    # Cache Configuration
    cache_ttl: int = Field(default=300, env="CACHE_TTL")  # seconds

    # File Storage
    reports_dir: str = Field(
        default="./reports",
        env="REPORTS_DIR"
    )

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")

    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["*"],
        env="CORS_ORIGINS"
    )

    cors_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE"],
        env="CORS_METHODS"
    )

    cors_headers: List[str] = Field(
        default=["*"],
        env="CORS_HEADERS"
    )

    # Monitoring
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")

    # Security
    allowed_hosts: List[str] = Field(
        default=["*"],
        env="ALLOWED_HOSTS"
    )

    max_request_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        env="MAX_REQUEST_SIZE"
    )

    # Integration
    cbsc_api_url: str = Field(
        default="http://localhost:3003",
        env="CBSC_API_URL"
    )

    cbsc_api_timeout: int = Field(
        default=30,
        env="CBSC_API_TIMEOUT"
    )  # seconds

    # Feature Flags
    enable_real_time_monitoring: bool = Field(
        default=True,
        env="ENABLE_REAL_TIME_MONITORING"
    )

    enable_stress_testing: bool = Field(
        default=True,
        env="ENABLE_STRESS_TESTING"
    )

    enable_recommendations: bool = Field(
        default=True,
        env="ENABLE_RECOMMENDATIONS"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False
        # Allow parsing of comma-separated lists
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> any:
            if field_name in ["cors_origins", "cors_methods", "cors_headers", "allowed_hosts"]:
                return [x.strip() for x in raw_val.split(",")]
            elif field_name == "var_confidence_levels" or field_name == "es_confidence_levels":
                return [float(x.strip()) for x in raw_val.split(",")]
            elif field_name == "volatility_windows":
                return [int(x.strip()) for x in raw_val.split(",")]
            return cls.json_loads(raw_val) if raw_val else None


# Create global settings instance
settings = Settings()


def create_directories():
    """
    Create necessary directories
    """
    dirs_to_create = [
        settings.reports_dir,
        "./logs",
        "./temp"
    ]

    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def setup_logging():
    """
    Setup logging configuration
    """
    import logging.config

    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "default",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "": {
                "level": settings.log_level,
                "handlers": ["console"]
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }

    # Add file handler if log file is specified
    if settings.log_file:
        log_config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": settings.log_level,
            "formatter": "detailed",
            "filename": settings.log_file,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
        log_config["loggers"][""]["handlers"].append("file")

    logging.config.dictConfig(log_config)
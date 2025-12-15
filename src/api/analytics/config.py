"""
Configuration for Analytics API
"""
from typing import Optional
from pydantic import BaseSettings
import os


class AnalyticsConfig(BaseSettings):
    """Configuration settings for Analytics API"""

    # Database settings
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/cbsc")

    # Redis cache settings
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    cache_ttl_default: int = 300  # 5 minutes
    cache_ttl_performance: int = 3600  # 1 hour
    cache_ttl_portfolio: int = 900  # 15 minutes

    # WebSocket settings
    websocket_port: int = int(os.getenv("WEBSOCKET_PORT", "8765"))
    websocket_ping_interval: int = 30  # seconds
    max_connections: int = 1000

    # Performance calculation settings
    risk_free_rate: float = 0.02  # 2% annual
    trading_days_per_year: int = 252
    benchmark_symbol: str = "SPY"

    # Data limits
    max_historical_days: int = 365 * 5  # 5 years max
    max_data_points: int = 10000
    default_period_days: int = 365

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_prefix = "ANALYTICS_"
        case_sensitive = False


# Global config instance
config = AnalyticsConfig()
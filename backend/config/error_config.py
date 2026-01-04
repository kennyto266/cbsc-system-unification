"""
Error handling configuration for the CBSC Trading System.

Centralizes all retry, circuit breaker, and error handling settings.
"""

import os
from typing import Optional


class ErrorHandlingConfig:
    """Configuration for error handling and retry behavior."""

    def __init__(self):
        # Retry configuration
        self.max_retry_attempts = int(os.getenv("MAX_RETRY_ATTEMPTS", "5"))
        self.retry_base_delay = float(os.getenv("RETRY_BASE_DELAY", "1.0"))
        self.retry_max_delay = float(os.getenv("RETRY_MAX_DELAY", "60.0"))
        self.retry_exponential_base = float(os.getenv("RETRY_EXPONENTIAL_BASE", "2.0"))
        self.retry_jitter_enabled = True
        self.retry_jitter_factor = 0.1

        # Circuit breaker configuration
        self.circuit_breaker_enabled = True
        self.circuit_breaker_failure_threshold = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5"))
        self.circuit_breaker_success_threshold = 2
        self.circuit_breaker_timeout = float(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60.0"))
        self.circuit_breaker_half_open_timeout = 30.0
        self.circuit_breaker_min_requests = 3

        # API configuration
        self.api_timeout = float(os.getenv("API_TIMEOUT", "30.0"))
        self.api_connect_timeout = 10.0
        self.api_read_timeout = 30.0

        # Service-specific configurations
        self.yfinance_retry_attempts = 3
        self.yfinance_timeout = 30.0

        self.database_retry_attempts = 3
        self.database_connection_timeout = 5.0
        self.database_pool_size = 10

        # Rate limiting configuration
        self.rate_limit_enabled = True
        self.rate_limit_requests_per_minute = 100
        self.rate_limit_burst = 20

        # Logging configuration
        self.error_logging_enabled = True
        self.error_log_include_traceback = True
        self.error_log_include_context = True

        # Monitoring configuration
        self.metrics_enabled = True
        self.metrics_retention_hours = 24


# Global configuration instance
_config: Optional[ErrorHandlingConfig] = None


def get_error_config() -> ErrorHandlingConfig:
    """
    Get the global error handling configuration.

    Returns:
        ErrorHandlingConfig instance
    """
    global _config
    if _config is None:
        _config = ErrorHandlingConfig()
    return _config


def set_error_config(config: ErrorHandlingConfig):
    """
    Set the global error handling configuration.

    Args:
        config: The configuration to use
    """
    global _config
    _config = config


# Service-specific configuration presets

YFINANCE_CONFIG = {
    "max_attempts": 3,
    "base_delay": 2.0,
    "timeout": 30.0,
    "circuit_breaker_threshold": 5,
}

DATABASE_CONFIG = {
    "max_attempts": 3,
    "base_delay": 1.0,
    "timeout": 5.0,
    "circuit_breaker_threshold": 3,
}

CLAUDE_API_CONFIG = {
    "max_attempts": 5,
    "base_delay": 5.0,
    "timeout": 60.0,
    "circuit_breaker_threshold": 10,
}

WEBSOCKET_CONFIG = {
    "max_attempts": 3,
    "base_delay": 1.0,
    "timeout": 10.0,
}


def get_service_config(service_name: str) -> dict:
    """
    Get configuration for a specific service.

    Args:
        service_name: Name of the service (yfinance, database, claude_api, websocket)

    Returns:
        Dictionary with service-specific configuration
    """
    configs = {
        "yfinance": YFINANCE_CONFIG,
        "database": DATABASE_CONFIG,
        "claude_api": CLAUDE_API_CONFIG,
        "websocket": WEBSOCKET_CONFIG,
    }
    return configs.get(service_name, {})

"""
Centralized Configuration Management System

This module provides enterprise - grade configuration management for the
Hong Kong Quantitative Trading System.

Features:
- Hierarchical configuration with inheritance
- Environment - specific configurations
- Hot - reload capabilities
- Type validation and security
- Configuration backup and rollback
- Audit trail and monitoring
"""

from .loader import ConfigLoader
from .manager import ConfigManager
from .models import (
    APIConfig,
    DatabaseConfig,
    MonitoringConfig,
    RedisConfig,
    SecurityConfig,
    TradingConfig,
)
from .schema import ConfigSchema
from .validator import ConfigValidator

__all__ = [
    "ConfigManager",
    "ConfigSchema",
    "ConfigValidator",
    "ConfigLoader",
    "DatabaseConfig",
    "RedisConfig",
    "APIConfig",
    "TradingConfig",
    "MonitoringConfig",
    "SecurityConfig",
]

# Version information
__version__ = "1.0.0"
__author__ = "Hong Kong Quantitative Trading System"

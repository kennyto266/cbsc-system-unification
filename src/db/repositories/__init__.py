"""
Repository Pattern Data Access Layer

Provides repository classes for data access with CRUD operations,
querying, and caching support.
"""

from .base import BaseRepository
from .strategy import (
    StrategyRepository,
    StrategyParameterRepository,
    StrategyPerformanceRepository,
    StrategySignalRepository
)
from .market_data import CBSCMarketDataRepository
from .user import UserRepository, UserSessionRepository

__all__ = [
    # Base
    "BaseRepository",

    # Strategy repositories
    "StrategyRepository",
    "StrategyParameterRepository",
    "StrategyPerformanceRepository",
    "StrategySignalRepository",

    # Market data
    "CBSCMarketDataRepository",

    # User repositories
    "UserRepository",
    "UserSessionRepository",
]

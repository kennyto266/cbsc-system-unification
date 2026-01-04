"""
Database Access Layer for CBSC Quantitative Trading System

Provides ORM models, repository pattern, caching, and connection management.
"""

from .connection import (
    DatabaseConnectionManager,
    get_db_manager,
    init_db
)
from .models import Base, Strategy, StrategyParameter, CBSCMarketData, StrategyPerformance, StrategySignal, User, UserSession
from .repositories import (
    BaseRepository,
    StrategyRepository,
    StrategyParameterRepository,
    StrategyPerformanceRepository,
    StrategySignalRepository,
    CBSCMarketDataRepository,
    UserRepository,
    UserSessionRepository
)
from .cache import (
    CacheManager,
    cached,
    CachedRepositoryMixin,
    get_cache_manager,
    init_cache
)

__all__ = [
    # Connection management
    "DatabaseConnectionManager",
    "get_db_manager",
    "init_db",

    # ORM models
    "Base",
    "Strategy",
    "StrategyParameter",
    "CBSCMarketData",
    "StrategyPerformance",
    "StrategySignal",
    "User",
    "UserSession",

    # Repositories
    "BaseRepository",
    "StrategyRepository",
    "StrategyParameterRepository",
    "StrategyPerformanceRepository",
    "StrategySignalRepository",
    "CBSCMarketDataRepository",
    "UserRepository",
    "UserSessionRepository",

    # Caching
    "CacheManager",
    "cached",
    "CachedRepositoryMixin",
    "get_cache_manager",
    "init_cache",
]

"""
Analytics API module for CBSC system
"""

from .analytics_router import router
from .services.performance_service import PerformanceCalculationService, PerformanceCacheService
from .services.portfolio_service import PortfolioAnalysisService
from .services.realtime_service import realtime_service, RealTimeDataService
from .models.analytics import (
    PerformanceMetrics,
    ReturnsData,
    PortfolioOverview,
    Timeframe,
    RealTimeUpdate,
    AssetAllocation,
    SectorAllocation
)

__all__ = [
    # Router
    "router",

    # Services
    "PerformanceCalculationService",
    "PerformanceCacheService",
    "PortfolioAnalysisService",
    "realtime_service",
    "RealTimeDataService",

    # Models
    "PerformanceMetrics",
    "ReturnsData",
    "PortfolioOverview",
    "Timeframe",
    "RealTimeUpdate",
    "AssetAllocation",
    "SectorAllocation"
]
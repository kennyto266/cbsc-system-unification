"""
Analytics API Router
Provides endpoints for strategy performance analytics, historical data, and portfolio metrics
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .services.performance import PerformanceService
from .services.portfolio import PortfolioService
from .cache import AnalyticsCache
from .background import calculate_metrics_background
from ..auth import get_current_user
from ..database import get_db

# Initialize router
router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Initialize services
performance_service = PerformanceService()
portfolio_service = PortfolioService()
cache = AnalyticsCache()


class Period(str, Enum):
    """Time period options for analytics"""
    DAY = "1D"
    WEEK = "1W"
    MONTH = "1M"
    THREE_MONTHS = "3M"
    SIX_MONTHS = "6M"
    YEAR = "1Y"
    ALL = "ALL"


class Granularity(str, Enum):
    """Data granularity options"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# Pydantic models for responses
class PerformanceMetrics(BaseModel):
    """Performance metrics response model"""
    strategy_id: str
    period: str
    total_return: float = Field(..., description="Total return percentage")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    sortino_ratio: Optional[float] = Field(None, description="Sortino ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    volatility: float = Field(..., description="Annualized volatility")
    calmar_ratio: Optional[float] = Field(None, description="Calmar ratio")
    win_rate: float = Field(..., description="Win rate percentage")
    profit_factor: float = Field(..., description="Profit factor")
    avg_trade_duration: float = Field(..., description="Average trade duration in days")
    beta: Optional[float] = Field(None, description="Beta relative to benchmark")
    alpha: Optional[float] = Field(None, description="Alpha relative to benchmark")

    class Config:
        schema_extra = {
            "example": {
                "strategy_id": "momentum_001",
                "period": "1M",
                "total_return": 12.5,
                "sharpe_ratio": 1.85,
                "sortino_ratio": 2.1,
                "max_drawdown": -8.3,
                "volatility": 15.2,
                "calmar_ratio": 1.51,
                "win_rate": 65.4,
                "profit_factor": 1.95,
                "avg_trade_duration": 2.4,
                "beta": 0.85,
                "alpha": 3.2
            }
        }


class HistoricalDataPoint(BaseModel):
    """Historical data point model"""
    date: datetime
    value: float
    benchmark: Optional[float] = None
    volume: Optional[float] = None
    positions: Optional[int] = None


class HistoricalDataResponse(BaseModel):
    """Historical data response model"""
    strategy_id: str
    granularity: str
    data: List[HistoricalDataPoint]
    total_points: int
    has_more: bool


class AssetAllocation(BaseModel):
    """Asset allocation model"""
    symbol: str
    name: str
    value: float
    weight: float
    target_weight: float
    sector: str
    change: float
    change_percent: float


class SectorAllocation(BaseModel):
    """Sector allocation model"""
    name: str
    value: float
    weight: float
    target_weight: float
    assets: List[str]


class PortfolioAnalytics(BaseModel):
    """Portfolio analytics response model"""
    total_value: float
    cash: float
    invested: float
    available_margin: float
    day_change: float
    day_change_percent: float
    total_return: float
    total_return_percent: float
    assets: List[AssetAllocation]
    sectors: List[SectorAllocation]
    var_95: Optional[float] = None
    cvar_95: Optional[float] = None
    correlations: Optional[Dict[str, float]] = None


class RealTimeMetrics(BaseModel):
    """Real-time metrics model"""
    strategy_id: str
    status: str
    current_positions: int
    total_exposure: float
    leverage: float
    daily_pnl: float
    unrealized_pnl: float
    realized_pnl: float
    last_updated: datetime
    market_value: float


# Endpoints

@router.get("/performance/{strategy_id}", response_model=PerformanceMetrics)
async def get_strategy_performance(
    strategy_id: str,
    period: Period = Query(Period.MONTH, description="Time period for analysis"),
    benchmark: Optional[str] = Query(None, description="Benchmark symbol for comparison"),
    include_risk_metrics: bool = Query(True, description="Include risk metrics in response"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get comprehensive performance metrics for a strategy

    Args:
        strategy_id: Unique identifier for the strategy
        period: Time period for analysis
        benchmark: Optional benchmark symbol
        include_risk_metrics: Whether to include risk metrics

    Returns:
        PerformanceMetrics object with calculated metrics
    """
    # Check cache first
    cache_key = f"perf:{strategy_id}:{period}:{benchmark or 'none'}"
    cached_result = await cache.get(cache_key)

    if cached_result:
        return PerformanceMetrics.parse_obj(cached_result)

    try:
        # Calculate performance metrics
        metrics = await performance_service.calculate_performance(
            strategy_id=strategy_id,
            period=period.value,
            benchmark=benchmark,
            include_risk_metrics=include_risk_metrics,
            db=db
        )

        # Cache the result
        await cache.set(cache_key, metrics.dict(), ttl=3600)  # 1 hour cache

        # Schedule background refresh for next time
        background_tasks.add_task(
            calculate_metrics_background,
            strategy_id=strategy_id,
            period=period.value
        )

        return metrics

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate performance metrics: {str(e)}"
        )


@router.get("/history/{strategy_id}", response_model=HistoricalDataResponse)
async def get_strategy_history(
    strategy_id: str,
    start_date: datetime = Query(..., description="Start date for historical data"),
    end_date: datetime = Query(..., description="End date for historical data"),
    granularity: Granularity = Query(Granularity.DAILY, description="Data granularity"),
    metrics: List[str] = Query(["pnl"], description="Metrics to include"),
    limit: int = Query(1000, le=10000, description="Maximum number of data points"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get historical time-series data for a strategy

    Args:
        strategy_id: Unique identifier for the strategy
        start_date: Start date for data
        end_date: End date for data
        granularity: Data granularity
        metrics: List of metrics to include
        limit: Maximum number of data points
        offset: Pagination offset

    Returns:
        HistoricalDataResponse with time-series data
    """
    try:
        # Validate date range
        if end_date <= start_date:
            raise HTTPException(
                status_code=400,
                detail="End date must be after start date"
            )

        # Check date range limits (max 2 years)
        if (end_date - start_date).days > 730:
            raise HTTPException(
                status_code=400,
                detail="Date range cannot exceed 2 years"
            )

        # Get historical data
        data, total_count = await performance_service.get_historical_data(
            strategy_id=strategy_id,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity.value,
            metrics=metrics,
            limit=limit,
            offset=offset,
            db=db
        )

        return HistoricalDataResponse(
            strategy_id=strategy_id,
            granularity=granularity.value,
            data=data,
            total_points=total_count,
            has_more=offset + limit < total_count
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch historical data: {str(e)}"
        )


@router.get("/portfolio", response_model=PortfolioAnalytics)
async def get_portfolio_analytics(
    user_id: Optional[str] = Query(None, description="User ID (defaults to current user)"),
    include_correlations: bool = Query(False, description="Include correlation matrix"),
    risk_level: str = Query("95%", enum=["90%", "95%", "99%"], description="VaR confidence level"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get aggregated portfolio analytics

    Args:
        user_id: User ID (defaults to current user)
        include_correlations: Whether to include correlation matrix
        risk_level: Confidence level for VaR calculation

    Returns:
        PortfolioAnalytics with portfolio metrics
    """
    # Use current user if not specified
    target_user_id = user_id or current_user["user_id"]

    # Check cache
    cache_key = f"portfolio:{target_user_id}:{risk_level}:{include_correlations}"
    cached_result = await cache.get(cache_key)

    if cached_result:
        return PortfolioAnalytics.parse_obj(cached_result)

    try:
        # Get portfolio analytics
        analytics = await portfolio_service.get_portfolio_analytics(
            user_id=target_user_id,
            include_correlations=include_correlations,
            risk_level=risk_level,
            db=db
        )

        # Cache the result
        await cache.set(cache_key, analytics.dict(), ttl=900)  # 15 minutes cache

        return analytics

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch portfolio analytics: {str(e)}"
        )


@router.get("/realtime/{strategy_id}", response_model=RealTimeMetrics)
async def get_realtime_metrics(
    strategy_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get real-time metrics for a strategy

    Args:
        strategy_id: Unique identifier for the strategy

    Returns:
        RealTimeMetrics with current strategy state
    """
    try:
        # Get real-time metrics (very short cache)
        cache_key = f"realtime:{strategy_id}"
        cached_result = await cache.get(cache_key, ttl=60)  # 1 minute cache

        if cached_result:
            return RealTimeMetrics.parse_obj(cached_result)

        metrics = await performance_service.get_realtime_metrics(
            strategy_id=strategy_id,
            db=db
        )

        # Cache with short TTL
        await cache.set(cache_key, metrics.dict(), ttl=60)

        return metrics

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch real-time metrics: {str(e)}"
        )


@router.post("/refresh/{strategy_id}")
async def refresh_strategy_metrics(
    strategy_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Force refresh of strategy metrics

    Args:
        strategy_id: Unique identifier for the strategy

    Returns:
        Confirmation message
    """
    try:
        # Invalidate cache for all periods
        periods = [p.value for p in Period]
        for period in periods:
            cache_key = f"perf:{strategy_id}:{period}"
            await cache.delete(cache_key)

        # Schedule background calculation
        for period in periods:
            background_tasks.add_task(
                calculate_metrics_background,
                strategy_id=strategy_id,
                period=period
            )

        return JSONResponse(
            content={"message": "Metrics refresh scheduled"},
            status_code=202
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh metrics: {str(e)}"
        )


@router.get("/cache/stats")
async def get_cache_stats(
    current_user: dict = Depends(get_current_user)
):
    """Get cache statistics for monitoring"""
    try:
        stats = await cache.get_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cache stats: {str(e)}"
        )
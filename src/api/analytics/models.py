"""
Analytics API Models
Pydantic models for request/response validation
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# Performance Metrics Models
class PerformanceMetricsResponse(BaseModel):
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


# Portfolio Analytics Models
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


# Real-time Metrics Models
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


# Request Models
class PerformanceRequest(BaseModel):
    """Performance metrics request model"""
    strategy_id: str
    period: str = Field("1M", enum=["1D", "1W", "1M", "3M", "6M", "1Y", "ALL"])
    benchmark: Optional[str] = None
    include_risk_metrics: bool = True


class HistoryRequest(BaseModel):
    """Historical data request model"""
    strategy_id: str
    start_date: datetime
    end_date: datetime
    granularity: str = Field("daily", enum=["daily", "weekly", "monthly"])
    metrics: List[str] = ["pnl"]
    limit: int = Field(1000, le=10000)
    offset: int = Field(0, ge=0)


class PortfolioRequest(BaseModel):
    """Portfolio analytics request model"""
    user_id: Optional[str] = None
    include_correlations: bool = False
    risk_level: str = Field("95%", enum=["90%", "95%", "99%"])


# Response Wrapper Models
class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Cache Models
class CacheStats(BaseModel):
    """Cache statistics model"""
    connected: bool
    memory_used: int
    memory_human: str
    total_keys: int
    key_counts: Dict[str, int]
    hit_rate: float
    connections: int
    uptime_seconds: int


class TaskStatus(BaseModel):
    """Background task status model"""
    status: str  # "running", "completed", "failed", "not_found"
    task_id: Optional[int] = None
    done: Optional[bool] = None
    cancelled: Optional[bool] = None
    cached: Optional[bool] = None
    cached_at: Optional[datetime] = None
    error: Optional[str] = None


# Batch Request Models
class BatchPerformanceRequest(BaseModel):
    """Batch performance request model"""
    strategy_ids: List[str]
    period: str = Field("1M", enum=["1D", "1W", "1M", "3M", "6M", "1Y", "ALL"])
    benchmark: Optional[str] = None
    include_risk_metrics: bool = True


class BatchPerformanceResponse(BaseModel):
    """Batch performance response model"""
    results: List[PerformanceMetricsResponse]
    failed: List[Dict[str, str]]  # strategy_id: error message


# Comparison Models
class BenchmarkComparison(BaseModel):
    """Benchmark comparison model"""
    benchmark_symbol: str
    benchmark_name: str
    correlation: float
    beta: float
    alpha: float
    tracking_error: float
    information_ratio: float


class PerformanceComparison(BaseModel):
    """Performance comparison between strategies"""
    strategy1_id: str
    strategy2_id: str
    period: str
    correlation: float
    relative_performance: float
    rolling_correlation: List[Dict[str, float]]  # date, correlation
    outperformance_periods: int
    underperformance_periods: int


# Risk Metrics Models
class RiskMetrics(BaseModel):
    """Risk metrics model"""
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    max_drawdown: float
    volatility: float
    downside_deviation: float
    upside_capture: float
    downside_capture: float


class StressTestResult(BaseModel):
    """Stress test result model"""
    scenario: str
    portfolio_value_before: float
    portfolio_value_after: float
    loss_amount: float
    loss_percentage: float
    worst_performing_asset: str
    worst_performing_loss: float


# Export all models
__all__ = [
    # Performance Models
    "PerformanceMetricsResponse",
    "HistoricalDataPoint",
    "HistoricalDataResponse",

    # Portfolio Models
    "AssetAllocation",
    "SectorAllocation",
    "PortfolioAnalytics",

    # Real-time Models
    "RealTimeMetrics",

    # Request Models
    "PerformanceRequest",
    "HistoryRequest",
    "PortfolioRequest",

    # Response Models
    "APIResponse",
    "ErrorResponse",

    # Utility Models
    "CacheStats",
    "TaskStatus",

    # Batch Models
    "BatchPerformanceRequest",
    "BatchPerformanceResponse",

    # Comparison Models
    "BenchmarkComparison",
    "PerformanceComparison",

    # Risk Models
    "RiskMetrics",
    "StressTestResult"
]
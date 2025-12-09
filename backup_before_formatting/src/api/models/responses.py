"""
API Response Models
API 響應數據模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    success: bool = Field(..., description="Whether the request was successful")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Unique request identifier")


class ErrorResponse(BaseResponse):
    """Error response model."""

    success: bool = Field(default=False, description="Always false for error responses")
    error: Dict[str, Any] = Field(..., description="Error details including type, message, and code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")

    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "timestamp": "2025-01-01T12:00:00Z",
                "request_id": "req_123456789",
                "error": {
                    "type": "ValidationError",
                    "message": "Invalid parameter value",
                    "code": "VAL_001"
                },
                "details": {
                    "parameter": "symbol",
                    "value": "INVALID"
                }
            }
        }


class HealthResponse(BaseResponse):
    """Health check response model."""

    status: str = Field(..., description="System health status")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Deployment environment")
    services: Dict[str, str] = Field(..., description="Status of dependent services")
    uptime_seconds: Optional[float] = Field(None, description="System uptime in seconds")


class TechnicalIndicatorResponse(BaseResponse):
    """Technical indicator calculation response model."""

    symbol: str = Field(..., description="Stock symbol")
    indicators: Dict[str, Any] = Field(..., description="Calculated technical indicators")
    data_points: int = Field(..., description="Number of data points processed")
    timeframe: str = Field(..., description="Data timeframe used")


class AnalysisResponse(BaseResponse):
    """Stock analysis response model."""

    symbol: str = Field(..., description="Analyzed stock symbol")
    analysis_type: str = Field(..., description="Type of analysis performed")
    timeframe: str = Field(..., description="Analysis timeframe")
    data: Dict[str, Any] = Field(..., description="Analysis results")
    indicators: List[str] = Field(..., description="Indicators used in analysis")
    summary: str = Field(..., description="Analysis summary")
    confidence_score: Optional[float] = Field(None, description="Confidence in analysis (0-1)")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "timestamp": "2025-01-01T12:00:00Z",
                "symbol": "0700.HK",
                "analysis_type": "technical",
                "timeframe": "daily",
                "data": {
                    "trend": "bullish",
                    "support_level": 450.0,
                    "resistance_level": 550.0,
                    "rsi": 65.4
                },
                "indicators": ["RSI", "MACD", "Bollinger"],
                "summary": "Stock shows bullish trend with RSI indicating slight overbought condition",
                "confidence_score": 0.75
            }
        }


class OptimizationResponse(BaseResponse):
    """Strategy optimization response model."""

    symbol: str = Field(..., description="Stock symbol")
    strategy: str = Field(..., description="Optimized strategy name")
    best_parameters: Dict[str, Any] = Field(..., description="Optimal parameter values")
    performance_metrics: Dict[str, float] = Field(..., description="Performance metrics")
    optimization_results: List[Dict[str, Any]] = Field(..., description="All optimization results")
    iterations: int = Field(..., description="Number of iterations performed")
    convergence: bool = Field(..., description="Whether optimization converged")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "symbol": "0700.HK",
                "strategy": "RSI_Mean_Reversion",
                "best_parameters": {
                    "rsi_period": 14,
                    "overbought_threshold": 70,
                    "oversold_threshold": 30
                },
                "performance_metrics": {
                    "total_return": 0.25,
                    "sharpe_ratio": 1.15,
                    "max_drawdown": -0.08,
                    "win_rate": 0.65
                },
                "optimization_results": [],
                "iterations": 100,
                "convergence": True
            }
        }


class BacktestResponse(BaseResponse):
    """Backtest results response model."""

    symbol: str = Field(..., description="Stock symbol")
    strategy: str = Field(..., description="Backtested strategy")
    parameters: Dict[str, Any] = Field(..., description="Strategy parameters used")
    performance_summary: Dict[str, float] = Field(..., description="Performance summary")
    trades: List[Dict[str, Any]] = Field(..., description="List of executed trades")
    equity_curve: List[Dict[str, Any]] = Field(..., description="Equity curve data points")
    risk_metrics: Dict[str, float] = Field(..., description="Risk analysis metrics")
    benchmark_comparison: Optional[Dict[str, float]] = Field(None, description="Benchmark comparison")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "symbol": "0700.HK",
                "strategy": "RSI_Mean_Reversion",
                "parameters": {"rsi_period": 14},
                "performance_summary": {
                    "total_return": 0.25,
                    "annual_return": 0.18,
                    "sharpe_ratio": 1.15,
                    "max_drawdown": -0.08,
                    "win_rate": 0.65
                },
                "trades": [],
                "equity_curve": [],
                "risk_metrics": {
                    "volatility": 0.15,
                    "beta": 1.2,
                    "alpha": 0.05
                },
                "benchmark_comparison": {
                    "vs_hsi": 0.03,
                    "outperformance": 0.12
                }
            }
        }


class BatchBacktestResponse(BaseResponse):
    """Batch backtest results response model."""

    request_id: str = Field(..., description="Batch request identifier")
    total_symbols: int = Field(..., description="Total number of symbols processed")
    results: List[BacktestResponse] = Field(..., description="Individual backtest results")
    aggregate_metrics: Dict[str, float] = Field(..., description="Aggregate performance metrics")
    top_performers: List[Dict[str, Any]] = Field(..., description="Top performing symbols")
    processing_time_seconds: float = Field(..., description="Total processing time")


class MultiStrategyResponse(BaseResponse):
    """Multi-strategy analysis response model."""

    symbol: str = Field(..., description="Stock symbol")
    strategies: List[Dict[str, Any]] = Field(..., description="Strategy results and comparisons")
    optimal_strategy: str = Field(..., description="Best performing strategy")
    recommendation: Dict[str, Any] = Field(..., description="Investment recommendation")
    correlation_matrix: Dict[str, float] = Field(..., description="Strategy correlation matrix")


class PortfolioOptimizationResponse(BaseResponse):
    """Portfolio optimization response model."""

    optimal_weights: Dict[str, float] = Field(..., description="Optimal portfolio weights")
    expected_return: float = Field(..., description="Expected portfolio return")
    expected_volatility: float = Field(..., description="Expected portfolio volatility")
    sharpe_ratio: float = Field(..., description="Portfolio Sharpe ratio")
    risk_contributions: Dict[str, float] = Field(..., description="Risk contribution by asset")
    efficient_frontier: List[Dict[str, float]] = Field(..., description="Efficient frontier points")


class RiskAnalysisResponse(BaseResponse):
    """Risk analysis response model."""

    symbol: str = Field(..., description="Stock symbol")
    risk_metrics: Dict[str, float] = Field(..., description="Calculated risk metrics")
    var_estimate: float = Field(..., description="Value at Risk estimate")
    cvar_estimate: float = Field(..., description="Conditional Value at Risk estimate")
    drawdown_analysis: Dict[str, Any] = Field(..., description="Drawdown analysis")
    scenario_analysis: Optional[List[Dict[str, Any]]] = Field(None, description="Scenario analysis results")
    risk_rating: str = Field(..., description="Overall risk rating")


class MarketDataResponse(BaseResponse):
    """Market data response model."""

    symbol: str = Field(..., description="Stock symbol")
    data: Dict[str, Any] = Field(..., description="Requested market data")
    timeframe: str = Field(..., description="Data timeframe")
    data_points: int = Field(..., description="Number of data points returned")
    last_updated: datetime = Field(..., description="Last data update timestamp")


class PerformanceMonitoringResponse(BaseResponse):
    """Performance monitoring response model."""

    system_metrics: Dict[str, Any] = Field(..., description="System performance metrics")
    response_times: Dict[str, float] = Field(..., description="API response times")
    error_rates: Dict[str, float] = Field(..., description="Error rates by endpoint")
    active_connections: int = Field(..., description="Active API connections")
    resource_usage: Dict[str, float] = Field(..., description="Resource usage statistics")


class UserInfoResponse(BaseResponse):
    """User information response model."""

    user_id: str = Field(..., description="User identifier")
    permissions: List[str] = Field(..., description="User permissions")
    account_type: str = Field(..., description="Account type")
    rate_limits: Dict[str, Any] = Field(..., description="Rate limit information")


class TradingRecommendationResponse(BaseResponse):
    """Trading recommendation response model."""

    symbol: str = Field(..., description="Stock symbol")
    recommendation: str = Field(..., description="Buy/Sell/Hold recommendation")
    confidence: float = Field(..., description="Confidence level (0-1)")
    target_price: Optional[float] = Field(None, description="Target price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    time_horizon: str = Field(..., description="Recommended holding period")
    reasoning: str = Field(..., description="Reasoning behind recommendation")
    risk_factors: List[str] = Field(..., description="Key risk factors")


class AnalyticsDashboardResponse(BaseResponse):
    """Analytics dashboard data response model."""

    portfolio_summary: Dict[str, Any] = Field(..., description="Portfolio overview")
    recent_performance: List[Dict[str, Any]] = Field(..., description="Recent performance data")
    risk_exposure: Dict[str, float] = Field(..., description="Risk exposure by category")
    market_sentiment: Dict[str, Any] = Field(..., description="Market sentiment indicators")
    alerts: List[Dict[str, Any]] = Field(..., description="Active alerts and notifications")

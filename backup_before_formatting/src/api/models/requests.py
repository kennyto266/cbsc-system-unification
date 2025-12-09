"""
API Request Models
API 請求數據模型
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class MultiStrategyOptimizeRequest(BaseModel):
    """Multi-strategy optimization request model."""

    symbol: str = Field(..., description="Stock symbol (e.g., '0700.HK')")
    strategies: List[str] = Field(..., description="List of strategy names to optimize")
    lookback_days: int = Field(default=252, description="Number of days to look back for data")
    optimization_target: str = Field(default="sharpe_ratio", description="Optimization target metric")

    @validator('strategies')
    def validate_strategies(cls, v):
        """Validate strategy names."""
        if not v:
            raise ValueError("At least one strategy must be specified")
        # Add more validation logic as needed
        return v

    @validator('lookback_days')
    def validate_lookback_days(cls, v):
        """Validate lookback period."""
        if v <= 0:
            raise ValueError("Lookback days must be positive")
        if v > 3650:  # 10 years max
            raise ValueError("Lookback days cannot exceed 3650")
        return v


class StrategyCompareRequest(BaseModel):
    """Strategy comparison request model."""

    symbol: str = Field(..., description="Stock symbol (e.g., '0700.HK')")
    strategies: Dict[str, Dict[str, Any]] = Field(..., description="Dictionary of strategy configurations")
    benchmark: Optional[str] = Field(default=None, description="Benchmark symbol for comparison")

    @validator('strategies')
    def validate_strategies(cls, v):
        """Validate strategy configurations."""
        if len(v) < 2:
            raise ValueError("At least two strategies must be provided for comparison")
        # Add more validation logic as needed
        return v


class AnalysisRequest(BaseModel):
    """Stock analysis request model."""

    symbol: str = Field(..., description="Stock symbol (e.g., '0700.HK')")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis to perform")
    indicators: List[str] = Field(default=[], description="List of technical indicators to include")
    timeframe: str = Field(default="daily", description="Data timeframe (daily, weekly, monthly)")

    @validator('analysis_type')
    def validate_analysis_type(cls, v):
        """Validate analysis type."""
        valid_types = ["comprehensive", "technical", "fundamental", "sentiment"]
        if v not in valid_types:
            raise ValueError(f"Analysis type must be one of {valid_types}")
        return v

    @validator('timeframe')
    def validate_timeframe(cls, v):
        """Validate timeframe."""
        valid_timeframes = ["daily", "weekly", "monthly", "hourly"]
        if v not in valid_timeframes:
            raise ValueError(f"Timeframe must be one of {valid_timeframes}")
        return v


class OptimizeRequest(BaseModel):
    """Strategy optimization request model."""

    symbol: str = Field(..., description="Stock symbol (e.g., '0700.HK')")
    strategy: str = Field(..., description="Strategy name to optimize")
    parameters: Dict[str, Any] = Field(..., description="Parameter ranges for optimization")
    objective: str = Field(default="sharpe_ratio", description="Optimization objective")
    max_iterations: int = Field(default=100, description="Maximum optimization iterations")

    @validator('parameters')
    def validate_parameters(cls, v):
        """Validate optimization parameters."""
        if not v:
            raise ValueError("Parameters cannot be empty")
        # Add parameter validation logic
        return v

    @validator('max_iterations')
    def validate_max_iterations(cls, v):
        """Validate maximum iterations."""
        if v <= 0:
            raise ValueError("Max iterations must be positive")
        if v > 10000:
            raise ValueError("Max iterations cannot exceed 10000")
        return v


class BatchBacktestRequest(BaseModel):
    """Batch backtest request model."""

    symbols: List[str] = Field(..., description="List of stock symbols to backtest")
    strategy: str = Field(..., description="Strategy name to backtest")
    parameters: Dict[str, Any] = Field(..., description="Strategy parameters")
    start_date: Optional[str] = Field(default=None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD)")
    rebalance_frequency: str = Field(default="monthly", description="Rebalancing frequency")

    @validator('symbols')
    def validate_symbols(cls, v):
        """Validate symbol list."""
        if not v:
            raise ValueError("At least one symbol must be specified")
        if len(v) > 100:
            raise ValueError("Cannot process more than 100 symbols in batch")
        return v

    @validator('strategy')
    def validate_strategy(cls, v):
        """Validate strategy name."""
        if not v:
            raise ValueError("Strategy cannot be empty")
        return v

    @validator('rebalance_frequency')
    def validate_rebalance_frequency(cls, v):
        """Validate rebalancing frequency."""
        valid_frequencies = ["daily", "weekly", "monthly", "quarterly"]
        if v not in valid_frequencies:
            raise ValueError(f"Rebalancing frequency must be one of {valid_frequencies}")
        return v


class TechnicalIndicatorRequest(BaseModel):
    """Technical indicator calculation request model."""

    symbol: str = Field(..., description="Stock symbol")
    indicators: List[str] = Field(..., description="List of technical indicators to calculate")
    timeframe: str = Field(default="daily", description="Timeframe for data")
    period: Optional[int] = Field(default=None, description="Period for indicators (if applicable)")

    @validator('indicators')
    def validate_indicators(cls, v):
        """Validate indicator list."""
        if not v:
            raise ValueError("At least one indicator must be specified")
        # Add indicator validation logic
        return v


class PortfolioOptimizationRequest(BaseModel):
    """Portfolio optimization request model."""

    symbols: List[str] = Field(..., description="List of symbols in portfolio")
    objective: str = Field(default="max_sharpe", description="Portfolio optimization objective")
    constraints: Dict[str, Any] = Field(default={}, description="Portfolio constraints")
    risk_free_rate: float = Field(default=0.03, description="Risk-free rate")

    @validator('symbols')
    def validate_symbols(cls, v):
        """Validate portfolio symbols."""
        if len(v) < 2:
            raise ValueError("Portfolio must contain at least 2 symbols")
        if len(v) > 50:
            raise ValueError("Portfolio cannot contain more than 50 symbols")
        return v

    @validator('objective')
    def validate_objective(cls, v):
        """Validate optimization objective."""
        valid_objectives = ["max_sharpe", "min_variance", "max_return", "equal_weight"]
        if v not in valid_objectives:
            raise ValueError(f"Objective must be one of {valid_objectives}")
        return v


class RiskAnalysisRequest(BaseModel):
    """Risk analysis request model."""

    symbol: str = Field(..., description="Stock symbol")
    analysis_types: List[str] = Field(default=["all"], description="Types of risk analysis to perform")
    confidence_level: float = Field(default=0.95, description="Confidence level for risk metrics")
    time_horizon: int = Field(default=252, description="Time horizon in trading days")

    @validator('analysis_types')
    def validate_analysis_types(cls, v):
        """Validate risk analysis types."""
        valid_types = ["var", "cvar", "drawdown", "volatility", "beta", "correlation", "all"]
        for analysis_type in v:
            if analysis_type not in valid_types:
                raise ValueError(f"Analysis type '{analysis_type}' is not valid")
        return v

    @validator('confidence_level')
    def validate_confidence_level(cls, v):
        """Validate confidence level."""
        if not 0.8 <= v <= 0.99:
            raise ValueError("Confidence level must be between 0.8 and 0.99")
        return v


class MarketDataRequest(BaseModel):
    """Market data request model."""

    symbol: str = Field(..., description="Stock symbol")
    start_date: Optional[str] = Field(default=None, description="Start date")
    end_date: Optional[str] = Field(default=None, description="End date")
    data_types: List[str] = Field(default=["price", "volume"], description="Types of market data")
    timeframe: str = Field(default="daily", description="Data timeframe")

    @validator('data_types')
    def validate_data_types(cls, v):
        """Validate data types."""
        valid_types = ["price", "volume", "dividends", "splits", "news"]
        for data_type in v:
            if data_type not in valid_types:
                raise ValueError(f"Data type '{data_type}' is not valid")
        return v

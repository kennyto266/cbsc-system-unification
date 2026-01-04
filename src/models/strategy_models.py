"""
Strategy data models using Pydantic and SQLAlchemy
策略數據模型 (Pydantic + SQLAlchemy)
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field, validator
from pydantic.config import ConfigDict

# Enums
class StrategyType(str, Enum):
    """Strategy type enumeration"""
    TECHNICAL_INDICATORS = "technical_indicators"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    VOLUME = "volume"
    VOLATILITY = "volatility"
    FUNDAMENTAL = "fundamental"
    QUANTITATIVE = "quantitative"
    PORTFOLIO = "portfolio"
    ARBITRAGE = "arbitrage"
    MACRO = "macro"

class StrategyStatus(str, Enum):
    """Strategy status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    ARCHIVED = "archived"

class RiskTolerance(str, Enum):
    """Risk tolerance levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

class BacktestType(str, Enum):
    """Backtest type enumeration"""
    STANDARD = "standard"
    RISK_MANAGEMENT = "risk_management"
    STRESS_TEST = "stress_test"
    MONTE_CARLO = "monte_carlo"

# Base Models
class TimestampedModel(BaseModel):
    """Base model with timestamp fields"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )

# Strategy Models
class StrategyCategoryBase(BaseModel):
    """Strategy category base model"""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    level: int = Field(default=1, ge=1)
    is_active: bool = True

class StrategyCategory(StrategyCategoryBase, TimestampedModel):
    """Strategy category model"""
    id: int

class StrategyBase(BaseModel):
    """Strategy base model"""
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    strategy_type: StrategyType
    version: str = Field(default="1.0.0", min_length=1, max_length=20)
    is_active: bool = True
    is_system: bool = False
    author_id: Optional[str] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    version_number: int = Field(default=1, ge=1)
    metadata: Optional[Dict[str, Any]] = None
    config_schema: Optional[Dict[str, Any]] = None
    parameters_template: Optional[Dict[str, Any]] = None

    @validator('code')
    def validate_code(cls, v):
        """Validate strategy code format"""
        import re
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
            raise ValueError('Code must start with letter and contain only alphanumeric characters and underscores')
        return v

class Strategy(StrategyBase, TimestampedModel):
    """Strategy model"""
    id: str

class StrategyConfigBase(BaseModel):
    """Strategy configuration base model"""
    strategy_id: str
    user_id: str
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    custom_parameters: Dict[str, Any] = Field(default_factory=dict)
    risk_tolerance: RiskTolerance = RiskTolerance.MEDIUM
    max_position_size: float = Field(default=100000.0, gt=0)
    stop_loss_percent: float = Field(default=5.0, ge=0, le=100)
    take_profit_percent: Optional[float] = Field(None, ge=0, le=100)
    leverage_ratio: float = Field(default=1.0, gt=0)
    rebalance_frequency: str = Field(default="daily", min_length=1)
    min_trade_interval: int = Field(default=300, ge=0)
    max_drawdown_limit: float = Field(default=20.0, ge=0, le=100)
    volatility_target: Optional[float] = Field(None, ge=0, le=100)
    correlation_limit: float = Field(default=0.7, ge=0, le=1)
    is_active: bool = True
    is_simulation: bool = True
    auto_execute: bool = False
    notification_settings: Optional[Dict[str, Any]] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    version: int = Field(default=1, ge=1)
    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

    @validator('custom_parameters')
    def validate_custom_parameters(cls, v):
        """Validate custom parameters are not empty"""
        if not v:
            raise ValueError('Custom parameters cannot be empty')
        return v

class StrategyConfig(StrategyConfigBase, TimestampedModel):
    """Strategy configuration model"""
    id: str

# Backtest Models
class BacktestResultBase(BaseModel):
    """Backtest result base model"""
    strategy_id: str
    strategy_config_id: Optional[str] = None
    user_id: str
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    backtest_type: BacktestType = BacktestType.STANDARD
    start_date: date
    end_date: date
    initial_capital: float = Field(..., gt=0)
    final_capital: float = Field(..., ge=0)
    total_return: float
    annualized_return: Optional[float] = None
    max_drawdown: float = Field(..., le=0)
    max_drawdown_duration: Optional[int] = Field(None, ge=0)
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None
    information_ratio: Optional[float] = None
    beta: Optional[float] = None
    alpha: Optional[float] = None
    tracking_error: Optional[float] = None
    volatility: Optional[float] = None
    downside_deviation: Optional[float] = None
    var_95: Optional[float] = None
    var_99: Optional[float] = None
    expected_shortfall: Optional[float] = None
    win_rate: float = Field(..., ge=0, le=1)
    profit_factor: Optional[float] = None
    recovery_factor: Optional[float] = None
    payoff_ratio: Optional[float] = None
    average_win: Optional[float] = None
    average_loss: Optional[float] = None
    largest_win: Optional[float] = None
    largest_loss: Optional[float] = None
    total_trades: int = Field(..., ge=0)
    winning_trades: int = Field(..., ge=0)
    losing_trades: int = Field(..., ge=0)
    average_trade_duration: Optional[float] = None
    commission_total: float = Field(default=0.0, ge=0)
    slippage_total: float = Field(default=0.0, ge=0)
    benchmark_return: Optional[float] = None
    benchmark_volatility: Optional[float] = None
    correlation_with_benchmark: Optional[float] = None
    monthly_returns: Optional[List[float]] = None
    yearly_returns: Optional[List[float]] = None
    rolling_returns: Optional[List[float]] = None
    trade_distribution: Optional[Dict[str, Any]] = None
    risk_metrics: Optional[Dict[str, Any]] = None
    performance_attribution: Optional[Dict[str, Any]] = None
    sector_allocation: Optional[Dict[str, Any]] = None
    regional_allocation: Optional[Dict[str, Any]] = None
    scenarios_tested: Optional[List[str]] = None
    stress_test_results: Optional[Dict[str, Any]] = None
    monte_carlo_results: Optional[Dict[str, Any]] = None
    status: str = Field(default="completed")
    error_message: Optional[str] = None
    execution_time_seconds: Optional[int] = Field(None, ge=0)
    data_points_analyzed: Optional[int] = Field(None, ge=0)
    parameters_used: Optional[Dict[str, Any]] = None
    market_conditions: Optional[Dict[str, Any]] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    version: int = Field(default=1, ge=1)
    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

    @validator('winning_trades', 'losing_trades')
    def validate_trade_counts(cls, v, values, field):
        """Validate trade counts"""
        if 'total_trades' in values:
            total_trades = values['total_trades']
            if v > total_trades:
                raise ValueError(f'{field.name} cannot exceed total_trades')
        return v

    @validator('final_capital')
    def validate_final_capital(cls, v, values):
        """Validate final capital against initial capital"""
        if 'initial_capital' in values:
            initial_capital = values['initial_capital']
            if v < 0:
                raise ValueError('Final capital cannot be negative')
            if v < initial_capital * 0.9:  # Allow up to 90% loss
                raise ValueError('Final capital loss exceeds 90%')
        return v

class BacktestResult(BacktestResultBase, TimestampedModel):
    """Backtest result model"""
    id: str

# Performance Record Models
class PerformanceRecordBase(BaseModel):
    """Performance record base model"""
    strategy_id: str
    strategy_config_id: Optional[str] = None
    user_id: str
    record_date: date
    record_time: datetime
    portfolio_value: float = Field(..., ge=0)
    cash_balance: float = Field(..., ge=0)
    invested_value: float = Field(..., ge=0)
    daily_return: float
    daily_return_pct: float
    cumulative_return: float
    cumulative_return_pct: float
    running_max_drawdown: float = Field(..., le=0)
    running_sharpe_ratio: Optional[float] = None
    running_volatility: Optional[float] = None
    running_var: Optional[float] = None
    positions_count: int = Field(..., ge=0)
    active_positions: int = Field(..., ge=0)
    long_positions: int = Field(..., ge=0)
    short_positions: int = Field(..., ge=0)
    sector_exposure: Optional[Dict[str, float]] = None
    country_exposure: Optional[Dict[str, float]] = None
    currency_exposure: Optional[Dict[str, float]] = None
    risk_metrics: Optional[Dict[str, Any]] = None
    greeks: Optional[Dict[str, float]] = None
    correlation_matrix: Optional[Dict[str, Any]] = None
    beta_portfolio: Optional[float] = None
    tracking_error: Optional[float] = None
    information_ratio: Optional[float] = None
    turnover_rate: Optional[float] = None
    trading_volume: float = Field(..., ge=0)
    commissions: float = Field(default=0.0, ge=0)
    slippage: float = Field(default=0.0, ge=0)
    margin_used: float = Field(default=0.0, ge=0)
    margin_available: Optional[float] = None
    leverage_ratio: float = Field(default=1.0, ge=0)
    risk_score: Optional[float] = None
    performance_score: Optional[float] = None
    efficiency_score: Optional[float] = None
    alerts_triggered: Optional[List[str]] = None
    benchmark_comparison: Optional[Dict[str, Any]] = None
    market_conditions: Optional[Dict[str, Any]] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    version: int = Field(default=1, ge=1)
    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

    @validator('active_positions', 'long_positions', 'short_positions')
    def validate_position_counts(cls, v, values, field):
        """Validate position counts"""
        if 'positions_count' in values:
            positions_count = values['positions_count']
            if v > positions_count:
                raise ValueError(f'{field.name} cannot exceed positions_count')
        return v

    @validator('portfolio_value')
    def validate_portfolio_value(cls, v, values):
        """Validate portfolio value composition"""
        if 'cash_balance' in values and 'invested_value' in values:
            cash_balance = values['cash_balance']
            invested_value = values['invested_value']
            if abs(v - (cash_balance + invested_value)) > 0.01:
                raise ValueError('Portfolio value must equal cash_balance + invested_value')
        return v

class PerformanceRecord(PerformanceRecordBase, TimestampedModel):
    """Performance record model"""
    id: str

# API Request/Response Models
class StrategyCreateRequest(BaseModel):
    """Strategy creation request"""
    strategy_data: StrategyBase
    categories: Optional[List[str]] = None

class StrategyUpdateRequest(BaseModel):
    """Strategy update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    strategy_type: Optional[StrategyType] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class StrategyConfigCreateRequest(BaseModel):
    """Strategy configuration creation request"""
    config_data: StrategyConfigBase

class StrategyConfigUpdateRequest(BaseModel):
    """Strategy configuration update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    custom_parameters: Optional[Dict[str, Any]] = None
    risk_tolerance: Optional[RiskTolerance] = None
    max_position_size: Optional[float] = Field(None, gt=0)
    stop_loss_percent: Optional[float] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None
    is_simulation: Optional[bool] = None
    auto_execute: Optional[bool] = None

class BacktestCreateRequest(BaseModel):
    """Backtest creation request"""
    backtest_data: BacktestResultBase
    initial_capital: float = Field(..., gt=0)

# Response Models
class PaginatedResponse(BaseModel):
    """Paginated response model"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool

class StrategyResponse(BaseModel):
    """Strategy response model"""
    strategy: Strategy
    categories: Optional[List[StrategyCategory]] = None

class StrategyConfigResponse(BaseModel):
    """Strategy configuration response model"""
    config: StrategyConfig
    strategy: Optional[Strategy] = None

class BacktestSummaryResponse(BaseModel):
    """Backtest summary response model"""
    backtest: BacktestResult
    strategy: Optional[Strategy] = None
    config: Optional[StrategyConfig] = None

class PerformanceMetricsResponse(BaseModel):
    """Performance metrics response model"""
    strategy_id: str
    strategy_name: str
    current_value: float
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: Optional[float]
    volatility: Optional[float]
    win_rate: float
    total_trades: int
    last_updated: datetime
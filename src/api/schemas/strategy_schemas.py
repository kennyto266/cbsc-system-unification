"""
Strategy Schemas
Pydantic schemas for strategy API validation and serialization
Phase 3.1 - 實現策略數據模型
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field, validator, HttpUrl, root_validator
import re


# Enums (matching SQLAlchemy enums)
class StrategyType(str, Enum):
    """Strategy type enumeration"""
    TECHNICAL = "technical"
    MOMENTUM = "momentum"
    VOLUME = "volume"
    PORTFOLIO = "portfolio"
    FUNDAMENTAL = "fundamental"
    COMBINATION = "combination"


class StrategyStatus(str, Enum):
    """Strategy status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    TESTING = "testing"


class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class TimeFrame(str, Enum):
    """Time frame enumeration"""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"


class InstanceStatus(str, Enum):
    """Strategy instance status"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class BacktestStatus(str, Enum):
    """Backtest status"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    class Config:
        orm_mode = True
        validate_assignment = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None,
        }


# Strategy Category schemas
class StrategyCategoryBase(BaseSchema):
    """Base strategy category schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=500, description="Category description")
    parent_id: Optional[UUID] = Field(None, description="Parent category ID")
    icon: Optional[str] = Field(None, max_length=50, description="Icon name")
    color: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$', description="Hex color code")
    sort_order: int = Field(0, description="Sort order")
    is_active: bool = Field(True, description="Is category active")


class StrategyCategoryCreate(StrategyCategoryBase):
    """Schema for creating strategy category"""
    pass


class StrategyCategoryUpdate(BaseSchema):
    """Schema for updating strategy category"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$')
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class StrategyCategoryResponse(StrategyCategoryBase):
    """Strategy category response schema"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    children_count: int = Field(0, description="Number of child categories")
    strategies_count: int = Field(0, description="Number of strategies in category")


# Strategy schemas
class StrategyBase(BaseSchema):
    """Base strategy schema"""
    name: str = Field(..., min_length=1, max_length=200, description="Strategy name")
    slug: str = Field(..., min_length=1, max_length=200, description="URL-friendly name")
    description: Optional[str] = Field(None, max_length=2000, description="Strategy description")
    strategy_type: StrategyType = Field(..., description="Strategy type")
    status: StrategyStatus = Field(StrategyStatus.DRAFT, description="Strategy status")

    # Category and classification
    category_id: Optional[UUID] = Field(None, description="Category ID")
    tags: Optional[List[str]] = Field(default_factory=list, description="Strategy tags")

    # Configuration
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Strategy configuration")
    default_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Default parameters")
    parameter_schema: Optional[Dict[str, Any]] = Field(None, description="Parameter validation schema")

    # Performance and risk
    risk_level: RiskLevel = Field(RiskLevel.MEDIUM, description="Risk level")
    expected_return: Optional[float] = Field(None, ge=-100, le=1000, description="Expected annual return (%)")
    max_drawdown: Optional[float] = Field(None, ge=0, le=100, description="Maximum drawdown (%)")
    sharpe_ratio: Optional[float] = Field(None, ge=-10, le=10, description="Sharpe ratio")
    win_rate: Optional[float] = Field(None, ge=0, le=100, description="Win rate (%)")

    # Trading parameters
    timeframes: Optional[List[TimeFrame]] = Field(default_factory=list, description="Supported timeframes")
    symbols: Optional[List[str]] = Field(default_factory=list, description="Tradable symbols")
    exchanges: Optional[List[str]] = Field(default_factory=list, description="Supported exchanges")
    min_capital: Optional[float] = Field(None, gt=0, description="Minimum capital requirement")

    # Metadata
    version: str = Field("1.0.0", description="Strategy version")
    is_public: bool = Field(False, description="Public visibility")
    is_template: bool = Field(False, description="Template strategy")
    featured: bool = Field(False, description="Featured in gallery")

    @validator('slug')
    def validate_slug(cls, v):
        """Validate slug format"""
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v

    @validator('symbols')
    def validate_symbols(cls, v):
        """Validate symbols format"""
        if v:
            for symbol in v:
                if not re.match(r'^[A-Z0-9.-]+$', symbol):
                    raise ValueError(f'Invalid symbol format: {symbol}')
        return v or []

    @validator('config')
    def validate_config(cls, v):
        """Validate configuration is a dictionary"""
        if v is not None and not isinstance(v, dict):
            raise ValueError('Configuration must be a dictionary')
        return v


class StrategyCreate(StrategyBase):
    """Schema for creating strategy"""
    pass


class StrategyUpdate(BaseSchema):
    """Schema for updating strategy"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[StrategyStatus] = None
    category_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None
    default_parameters: Optional[Dict[str, Any]] = None
    parameter_schema: Optional[Dict[str, Any]] = None
    risk_level: Optional[RiskLevel] = None
    expected_return: Optional[float] = Field(None, ge=-100, le=1000)
    max_drawdown: Optional[float] = Field(None, ge=0, le=100)
    sharpe_ratio: Optional[float] = Field(None, ge=-10, le=10)
    win_rate: Optional[float] = Field(None, ge=0, le=100)
    timeframes: Optional[List[TimeFrame]] = None
    symbols: Optional[List[str]] = None
    exchanges: Optional[List[str]] = None
    min_capital: Optional[float] = Field(None, gt=0)
    is_public: Optional[bool] = None
    is_template: Optional[bool] = None
    featured: Optional[bool] = None

    @validator('slug')
    def validate_slug(cls, v):
        """Validate slug format"""
        if v is not None and not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v


class StrategyResponse(StrategyBase):
    """Strategy response schema"""
    id: UUID
    author_id: UUID
    usage_count: int = Field(0, description="Usage count")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating")
    rating_count: int = Field(0, description="Number of ratings")
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]

    # Related objects
    category: Optional[StrategyCategoryResponse] = None
    author_name: Optional[str] = None
    versions_count: int = Field(0, description="Number of versions")
    instances_count: int = Field(0, description="Number of instances")
    backtests_count: int = Field(0, description="Number of backtests")


class StrategyListResponse(BaseSchema):
    """Strategy list response schema"""
    strategies: List[StrategyResponse]
    total: int = Field(..., description="Total number of strategies")
    page: int = Field(..., ge=1, description="Current page number")
    size: int = Field(..., ge=1, le=100, description="Page size")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


# Strategy Version schemas
class StrategyVersionBase(BaseSchema):
    """Base strategy version schema"""
    version: str = Field(..., min_length=1, max_length=20, description="Version string")
    changelog: Optional[str] = Field(None, max_length=2000, description="Version changelog")
    config: Dict[str, Any] = Field(..., description="Complete configuration")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parameter values")
    is_major: bool = Field(False, description="Major version (breaking changes)")
    is_stable: bool = Field(False, description="Stable release")
    benchmark_data: Optional[Dict[str, Any]] = None
    test_results: Optional[Dict[str, Any]] = None


class StrategyVersionCreate(StrategyVersionBase):
    """Schema for creating strategy version"""
    strategy_id: UUID = Field(..., description="Strategy ID")


class StrategyVersionResponse(StrategyVersionBase):
    """Strategy version response schema"""
    id: UUID
    strategy_id: UUID
    created_by: Optional[UUID] = None
    created_at: datetime
    creator_name: Optional[str] = None


# Strategy Instance schemas
class StrategyInstanceBase(BaseSchema):
    """Base strategy instance schema"""
    name: str = Field(..., min_length=1, max_length=200, description="Instance name")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Runtime parameters")
    symbols: Optional[List[str]] = Field(None, description="Trading symbols")
    capital_allocation: Optional[float] = Field(None, gt=0, description="Allocated capital")
    position_sizing: Optional[Dict[str, Any]] = Field(None, description="Position sizing rules")
    is_paper_trading: bool = Field(True, description="Paper trading mode")
    auto_trade: bool = Field(False, description="Automatic trading")
    signal_notifications: Optional[Dict[str, Any]] = Field(None, description="Notification settings")
    risk_settings: Optional[Dict[str, Any]] = Field(None, description="Risk management settings")


class StrategyInstanceCreate(StrategyInstanceBase):
    """Schema for creating strategy instance"""
    strategy_id: UUID = Field(..., description="Strategy ID")


class StrategyInstanceUpdate(BaseSchema):
    """Schema for updating strategy instance"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    parameters: Optional[Dict[str, Any]] = None
    symbols: Optional[List[str]] = None
    capital_allocation: Optional[float] = Field(None, gt=0)
    position_sizing: Optional[Dict[str, Any]] = None
    status: Optional[InstanceStatus] = None
    is_paper_trading: Optional[bool] = None
    auto_trade: Optional[bool] = None
    signal_notifications: Optional[Dict[str, Any]] = None
    risk_settings: Optional[Dict[str, Any]] = None


class StrategyInstanceResponse(StrategyInstanceBase):
    """Strategy instance response schema"""
    id: UUID
    strategy_id: UUID
    user_id: UUID
    status: InstanceStatus

    # Performance tracking
    start_equity: Optional[float] = None
    current_equity: Optional[float] = None
    total_return: Optional[float] = None
    daily_return: Optional[float] = None
    current_drawdown: Optional[float] = None
    var_95: Optional[float] = None

    # State
    last_signal: Optional[Dict[str, Any]] = None
    current_positions: Optional[Dict[str, Any]] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    last_signal_at: Optional[datetime] = None

    # Related objects
    strategy: Optional[StrategyResponse] = None
    trades_count: int = Field(0, description="Number of trades")


# Backtest schemas
class BacktestBase(BaseSchema):
    """Base backtest schema"""
    name: str = Field(..., min_length=1, max_length=200, description="Backtest name")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Strategy parameters")
    symbols: List[str] = Field(..., min_items=1, description="Test symbols")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: float = Field(100000, gt=0, description="Initial capital")

    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Validate end date is after start date"""
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

    @validator('symbols')
    def validate_symbols(cls, v):
        """Validate symbols format"""
        for symbol in v:
            if not re.match(r'^[A-Z0-9.-]+$', symbol):
                raise ValueError(f'Invalid symbol format: {symbol}')
        return v


class BacktestCreate(BacktestBase):
    """Schema for creating backtest"""
    strategy_id: UUID = Field(..., description="Strategy ID")


class BacktestResponse(BacktestBase):
    """Backtest response schema"""
    id: UUID
    strategy_id: UUID
    user_id: UUID
    status: BacktestStatus

    # Performance results
    final_equity: Optional[float] = None
    total_return: Optional[float] = None
    annualized_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    volatility: Optional[float] = None
    var_95: Optional[float] = None
    expected_shortfall: Optional[float] = None

    # Risk-adjusted metrics
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None

    # Trading statistics
    total_trades: Optional[int] = None
    winning_trades: Optional[int] = None
    losing_trades: Optional[int] = None
    win_rate: Optional[float] = None
    avg_win: Optional[float] = None
    avg_loss: Optional[float] = None
    profit_factor: Optional[float] = None

    # Benchmark comparison
    benchmark_return: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    information_ratio: Optional[float] = None

    # Detailed results
    equity_curve: Optional[List[Dict[str, Any]]] = None
    trade_history: Optional[List[Dict[str, Any]]] = None
    monthly_returns: Optional[Dict[str, float]] = None

    # Metadata
    error_message: Optional[str] = None
    computation_time: Optional[float] = None
    created_at: datetime

    # Related objects
    strategy: Optional[StrategyResponse] = None


# Performance schemas
class StrategyPerformanceBase(BaseSchema):
    """Base strategy performance schema"""
    date: date = Field(..., description="Performance date")
    daily_return: Optional[float] = None
    cumulative_return: Optional[float] = None
    annualized_return: Optional[float] = None
    volatility: Optional[float] = None
    max_drawdown: Optional[float] = None
    current_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None
    benchmark_return: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    tracking_error: Optional[float] = None
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    avg_trade_return: Optional[float] = None
    trade_count: Optional[int] = None
    equity: Optional[float] = None
    exposure: Optional[float] = None
    leverage: Optional[float] = None


class StrategyPerformanceResponse(StrategyPerformanceBase):
    """Strategy performance response schema"""
    id: UUID
    strategy_id: UUID
    created_at: datetime


# Trade schemas
class TradeBase(BaseSchema):
    """Base trade schema"""
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol")
    direction: str = Field(..., regex=r'^(long|short)$', description="Trade direction")
    quantity: float = Field(..., gt=0, description="Trade quantity")
    entry_price: float = Field(..., gt=0, description="Entry price")
    exit_price: Optional[float] = Field(None, gt=0, description="Exit price")
    entry_time: datetime = Field(..., description="Entry time")
    exit_time: Optional[datetime] = Field(None, description="Exit time")
    exit_reason: Optional[str] = Field(None, max_length=50, description="Exit reason")
    signal_confidence: Optional[float] = Field(None, ge=0, le=1, description="Signal confidence")
    strategy_notes: Optional[str] = Field(None, max_length=1000, description="Strategy notes")

    @validator('exit_time')
    def validate_exit_time(cls, v, values):
        """Validate exit time is after entry time"""
        if v is not None and 'entry_time' in values and v <= values['entry_time']:
            raise ValueError('Exit time must be after entry time')
        return v


class TradeResponse(TradeBase):
    """Trade response schema"""
    id: UUID
    instance_id: Optional[UUID] = None
    backtest_id: Optional[UUID] = None

    # Calculated fields
    entry_value: Optional[float] = None
    exit_value: Optional[float] = None
    gross_pnl: Optional[float] = None
    fees: Optional[float] = Field(0, description="Trading fees")
    net_pnl: Optional[float] = None
    return_pct: Optional[float] = None
    duration: Optional[int] = None

    created_at: datetime


# Query and filter schemas
class StrategyFilter(BaseSchema):
    """Strategy query filters"""
    search: Optional[str] = Field(None, description="Search term")
    strategy_type: Optional[StrategyType] = None
    status: Optional[StrategyStatus] = None
    category_id: Optional[UUID] = None
    risk_level: Optional[RiskLevel] = None
    is_public: Optional[bool] = None
    is_template: Optional[bool] = None
    featured: Optional[bool] = None
    tags: Optional[List[str]] = None
    author_id: Optional[UUID] = None
    min_sharpe: Optional[float] = Field(None, ge=-10, le=10)
    max_drawdown_max: Optional[float] = Field(None, ge=0, le=100)
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class BacktestFilter(BaseSchema):
    """Backtest query filters"""
    strategy_id: Optional[UUID] = None
    status: Optional[BacktestStatus] = None
    symbols: Optional[List[str]] = None
    start_date_after: Optional[date] = None
    start_date_before: Optional[date] = None
    min_return: Optional[float] = None
    max_drawdown_max: Optional[float] = None
    min_sharpe: Optional[float] = None


# Pagination schemas
class PaginationParams(BaseSchema):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")

    @property
    def offset(self) -> int:
        """Calculate offset"""
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        """Get limit"""
        return self.size


class PaginationResponse(BaseSchema):
    """Pagination response metadata"""
    total: int = Field(..., description="Total items")
    page: int = Field(..., ge=1, description="Current page")
    size: int = Field(..., ge=1, description="Page size")
    total_pages: int = Field(..., ge=0, description="Total pages")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")

    @classmethod
    def create(cls, total: int, page: int, size: int) -> "PaginationResponse":
        """Create pagination response"""
        total_pages = (total + size - 1) // size
        return cls(
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
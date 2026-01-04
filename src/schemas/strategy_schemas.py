"""
Strategy Management Pydantic Schemas
策略管理的 Pydantic 模式定義

用於API請求和響應的驗證
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union, Literal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, validator, HttpUrl, root_validator
from pydantic.config import ConfigDict

from ..models.strategy_models_v2 import (
    StrategyType, StrategyStatus, RiskLevel, TimeFrame,
    Strategy, StrategyCategory, StrategyInstance, StrategyPerformance
)


# Enums for schemas
class DirectionEnum(str, Enum):
    """Trade direction enum"""
    LONG = "long"
    SHORT = "short"


class ExitReasonEnum(str, Enum):
    """Exit reason enum"""
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    SIGNAL = "signal"
    MANUAL = "manual"
    EXPIRED = "expired"


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )


# Category schemas
class StrategyCategoryCreate(BaseSchema):
    """Schema for creating a strategy category"""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=500, description="Category description")
    parent_id: Optional[UUID] = Field(None, description="Parent category ID")
    icon: Optional[str] = Field(None, max_length=50, description="Icon name")
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code")
    sort_order: Optional[int] = Field(0, ge=0, description="Sort order")
    is_active: Optional[bool] = Field(True, description="Active status")

    @validator('name')
    def validate_name(cls, v):
        """Validate category name"""
        if not v or not v.strip():
            raise ValueError('Category name cannot be empty')
        return v.strip()


class StrategyCategoryUpdate(BaseSchema):
    """Schema for updating a strategy category"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    parent_id: Optional[UUID] = None
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class StrategyCategoryResponse(BaseSchema):
    """Schema for strategy category response"""
    id: UUID
    name: str
    description: Optional[str]
    parent_id: Optional[UUID]
    icon: Optional[str]
    color: Optional[str]
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    children: List['StrategyCategoryResponse'] = Field(default_factory=list)
    strategy_count: Optional[int] = Field(None, description="Number of strategies in this category")

    # Config for forward reference
    model_config = ConfigDict(from_attributes=True)


# Strategy Parameter Schemas
class StrategyParameterSchema(BaseSchema):
    """Schema for strategy parameter definition"""
    name: str = Field(..., description="Parameter name")
    type: Literal["string", "number", "boolean", "integer", "array", "object"] = Field(..., description="Parameter type")
    default: Any = Field(..., description="Default value")
    description: Optional[str] = Field(None, description="Parameter description")
    required: bool = Field(True, description="Whether parameter is required")
    min_value: Optional[Union[int, float]] = Field(None, description="Minimum value for numeric types")
    max_value: Optional[Union[int, float]] = Field(None, description="Maximum value for numeric types")
    options: Optional[List[Any]] = Field(None, description="Allowed values for enum-like parameters")
    unit: Optional[str] = Field(None, description="Unit of measurement")

    @validator('min_value', 'max_value')
    def validate_numeric_range(cls, v, values):
        """Validate numeric range constraints"""
        if v is not None and 'type' in values:
            param_type = values['type']
            if param_type not in ['number', 'integer']:
                raise ValueError(f'Numeric constraints only valid for number/integer types, got {param_type}')
        return v

    @validator('default')
    def validate_default_value(cls, v, values):
        """Validate default value matches parameter type"""
        if 'type' in values:
            param_type = values['type']
            type_map = {
                'string': str,
                'number': (int, float),
                'boolean': bool,
                'integer': int,
                'array': list,
                'object': dict
            }
            expected_type = type_map.get(param_type)
            if expected_type and not isinstance(v, expected_type):
                raise ValueError(f'Default value type {type(v)} does not match parameter type {param_type}')
        return v


# Strategy Create/Update Schemas
class StrategyCreate(BaseSchema):
    """Schema for creating a strategy"""
    name: str = Field(..., min_length=1, max_length=200, description="Strategy name")
    slug: Optional[str] = Field(None, max_length=200, pattern=r'^[a-z0-9-]+$',
                            description="URL-friendly slug")
    description: Optional[str] = Field(None, max_length=2000, description="Strategy description")
    strategy_type: StrategyType = Field(..., description="Strategy type")
    category_id: Optional[UUID] = Field(None, description="Category ID")
    tags: Optional[List[str]] = Field(default_factory=list, description="Strategy tags")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Strategy configuration")
    default_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict,
                                                   description="Default parameter values")
    parameter_schema: Optional[List[StrategyParameterSchema]] = Field(None,
                                                     description="Parameter validation schema")
    risk_level: Optional[RiskLevel] = Field(RiskLevel.MEDIUM, description="Risk level")
    expected_return: Optional[float] = Field(None, ge=-100, le=1000, description="Expected annual return (%)")
    max_drawdown: Optional[float] = Field(None, ge=0, le=100, description="Maximum historical drawdown (%)")
    sharpe_ratio: Optional[float] = Field(None, ge=0, description="Sharpe ratio")
    win_rate: Optional[float] = Field(None, ge=0, le=100, description="Win rate percentage")
    timeframes: Optional[List[TimeFrame]] = Field(default_factory=list, description="Supported timeframes")
    symbols: Optional[List[str]] = Field(default_factory=list, description="Tradable symbols")
    exchanges: Optional[List[str]] = Field(default_factory=list, description="Supported exchanges")
    min_capital: Optional[float] = Field(None, gt=0, description="Minimum capital requirement")
    is_public: Optional[bool] = Field(False, description="Public visibility")
    is_template: Optional[bool] = Field(False, description="Template strategy")

    @validator('name')
    def validate_name(cls, v):
        """Validate strategy name"""
        if not v or not v.strip():
            raise ValueError('Strategy name cannot be empty')
        return v.strip()

    @validator('slug', always=True)
    def generate_slug(cls, v, values):
        """Generate slug from name if not provided"""
        if v is None and 'name' in values:
            import re
            # Convert name to slug-friendly format
            name = values['name'].lower()
            # Replace spaces and special characters with hyphens
            slug = re.sub(r'[^a-z0-9]+', '-', name)
            # Remove leading/trailing hyphens
            slug = slug.strip('-')
            # Remove multiple consecutive hyphens
            slug = re.sub(r'-+', '-', slug)
            return slug
        return v

    @validator('symbols', 'exchanges')
    def validate_symbol_lists(cls, v):
        """Validate symbol and exchange lists"""
        if v is not None:
            # Ensure all items are non-empty strings
            validated = [s.upper().strip() for s in v if s and s.strip()]
            return validated
        return v

    @validator('config', 'default_parameters')
    def validate_json_fields(cls, v):
        """Validate JSON fields"""
        if v is not None and not isinstance(v, dict):
            raise ValueError('Configuration and parameters must be dictionaries')
        return v


class StrategyUpdate(BaseSchema):
    """Schema for updating a strategy"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, max_length=200, pattern=r'^[a-z0-9-]+$')
    description: Optional[str] = Field(None, max_length=2000)
    strategy_type: Optional[StrategyType] = None
    category_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None
    default_parameters: Optional[Dict[str, Any]] = None
    parameter_schema: Optional[List[StrategyParameterSchema]] = None
    risk_level: Optional[RiskLevel] = None
    expected_return: Optional[float] = Field(None, ge=-100, le=1000)
    max_drawdown: Optional[float] = Field(None, ge=0, le=100)
    sharpe_ratio: Optional[float] = Field(None, ge=0)
    win_rate: Optional[float] = Field(None, ge=0, le=100)
    timeframes: Optional[List[TimeFrame]] = None
    symbols: Optional[List[str]] = None
    exchanges: Optional[List[str]] = None
    min_capital: Optional[float] = Field(None, gt=0)
    status: Optional[StrategyStatus] = None
    is_public: Optional[bool] = None
    is_template: Optional[bool] = None
    featured: Optional[bool] = None


class StrategyResponse(BaseSchema):
    """Schema for strategy response"""
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    strategy_type: StrategyType
    status: StrategyStatus
    category_id: Optional[UUID]
    category: Optional[StrategyCategoryResponse] = None
    tags: List[str]
    config: Optional[Dict[str, Any]]
    default_parameters: Optional[Dict[str, Any]]
    parameter_schema: Optional[List[StrategyParameterSchema]]
    risk_level: RiskLevel
    expected_return: Optional[float]
    max_drawdown: Optional[float]
    sharpe_ratio: Optional[float]
    win_rate: Optional[float]
    timeframes: List[str]
    symbols: List[str]
    exchanges: List[str]
    min_capital: Optional[float]
    version: str
    author_id: UUID
    is_public: bool
    is_template: bool
    featured: bool
    usage_count: int
    rating: Optional[float]
    rating_count: int
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]

    # Additional computed fields
    backtest_count: Optional[int] = Field(None, description="Number of backtests")
    avg_return: Optional[float] = Field(None, description="Average return from backtests")
    popularity_score: Optional[float] = Field(None, description="Popularity score")


# Strategy Instance Schemas
class StrategyInstanceCreate(BaseSchema):
    """Schema for creating a strategy instance"""
    strategy_id: UUID = Field(..., description="Strategy ID")
    name: str = Field(..., min_length=1, max_length=200, description="Instance name")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Runtime parameters")
    symbols: Optional[List[str]] = Field(default_factory=list, description="Trading symbols")
    capital_allocation: float = Field(..., gt=0, description="Allocated capital")
    position_sizing: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Position sizing rules")
    risk_settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Risk management settings")
    is_paper_trading: Optional[bool] = Field(True, description="Paper trading mode")
    auto_trade: Optional[bool] = Field(False, description="Automatic trading")
    signal_notifications: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Notification settings")

    @validator('name')
    def validate_name(cls, v):
        """Validate instance name"""
        if not v or not v.strip():
            raise ValueError('Instance name cannot be empty')
        return v.strip()

    @validator('symbols')
    def validate_symbols(cls, v):
        """Validate symbols list"""
        if v is not None:
            validated = [s.upper().strip() for s in v if s and s.strip()]
            return validated
        return v


class StrategyInstanceUpdate(BaseSchema):
    """Schema for updating a strategy instance"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    parameters: Optional[Dict[str, Any]] = None
    symbols: Optional[List[str]] = None
    capital_allocation: Optional[float] = Field(None, gt=0)
    position_sizing: Optional[Dict[str, Any]] = None
    risk_settings: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, pattern=r'^(stopped|running|paused|error)$')
    is_paper_trading: Optional[bool] = None
    auto_trade: Optional[bool] = None
    signal_notifications: Optional[Dict[str, Any]] = None


class StrategyInstanceResponse(BaseSchema):
    """Schema for strategy instance response"""
    id: UUID
    strategy_id: UUID
    strategy: Optional[StrategyResponse] = None
    user_id: UUID
    name: str
    parameters: Optional[Dict[str, Any]]
    symbols: List[str]
    capital_allocation: float
    position_sizing: Optional[Dict[str, Any]]
    status: str
    last_signal: Optional[Dict[str, Any]]
    current_positions: Optional[List[Dict[str, Any]]]
    start_equity: Optional[float]
    current_equity: Optional[float]
    total_return: Optional[float]
    daily_return: Optional[float]
    risk_settings: Optional[Dict[str, Any]]
    current_drawdown: Optional[float]
    var_95: Optional[float]
    is_paper_trading: bool
    auto_trade: bool
    signal_notifications: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    stopped_at: Optional[datetime]
    last_signal_at: Optional[datetime]

    # Computed fields
    roi_percentage: Optional[float] = Field(None, description="Return on investment percentage")
    daily_pnl: Optional[float] = Field(None, description="Daily P&L")
    risk_metrics: Optional[Dict[str, Any]] = Field(None, description="Current risk metrics")


# Strategy Performance Schemas
class StrategyPerformanceResponse(BaseSchema):
    """Schema for strategy performance response"""
    id: UUID
    strategy_id: UUID
    date: datetime

    # Return metrics
    daily_return: Optional[float]
    cumulative_return: Optional[float]
    annualized_return: Optional[float]

    # Risk metrics
    volatility: Optional[float]
    max_drawdown: Optional[float]
    current_drawdown: Optional[float]

    # Risk-adjusted returns
    sharpe_ratio: Optional[float]
    sortino_ratio: Optional[float]
    calmar_ratio: Optional[float]

    # Benchmark comparison
    benchmark_return: Optional[float]
    alpha: Optional[float]
    beta: Optional[float]
    tracking_error: Optional[float]

    # Trading metrics
    win_rate: Optional[float]
    profit_factor: Optional[float]
    avg_trade_return: Optional[float]
    trade_count: Optional[int]

    # Portfolio metrics
    equity: Optional[float]
    exposure: Optional[float]
    leverage: Optional[float]

    created_at: datetime


# Trade Schemas
class TradeCreate(BaseSchema):
    """Schema for creating a trade record"""
    instance_id: UUID = Field(..., description="Strategy instance ID")
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol")
    direction: DirectionEnum = Field(..., description="Trade direction")
    quantity: float = Field(..., gt=0, description="Trade quantity")
    entry_price: float = Field(..., gt=0, description="Entry price")
    entry_time: datetime = Field(..., description="Entry timestamp")
    exit_price: Optional[float] = Field(None, gt=0, description="Exit price")
    exit_time: Optional[datetime] = Field(None, description="Exit timestamp")
    exit_reason: Optional[ExitReasonEnum] = None
    signal_confidence: Optional[float] = Field(None, ge=0, le=1, description="Signal confidence")
    strategy_notes: Optional[str] = Field(None, max_length=1000, description="Strategy notes")

    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate trading symbol"""
        if not v or not v.strip():
            raise ValueError('Symbol cannot be empty')
        return v.upper().strip()

    @root_validator(skip_on_failure=True)
    def validate_exit_fields(cls, values):
        """Validate exit fields consistency"""
        exit_price = values.get('exit_price')
        exit_time = values.get('exit_time')

        # If one exit field is provided, both should be
        if (exit_price is None) != (exit_time is None):
            raise ValueError('Exit price and exit time must both be provided or both be None')

        return values

    @validator('exit_time')
    def validate_exit_time(cls, v, values):
        """Validate exit time is after entry time"""
        if v is not None and 'entry_time' in values:
            if v <= values['entry_time']:
                raise ValueError('Exit time must be after entry time')
        return v


class TradeResponse(BaseSchema):
    """Schema for trade response"""
    id: UUID
    instance_id: UUID
    backtest_id: Optional[UUID]
    symbol: str
    direction: str
    quantity: float
    entry_price: float
    exit_price: Optional[float]
    entry_time: datetime
    exit_time: Optional[datetime]
    duration: Optional[int]  # Duration in minutes
    entry_value: Optional[float]
    exit_value: Optional[float]
    gross_pnl: Optional[float]
    fees: float
    net_pnl: Optional[float]
    return_pct: Optional[float]
    exit_reason: Optional[str]
    signal_confidence: Optional[float]
    strategy_notes: Optional[str]
    created_at: datetime

    # Computed fields
    is_open: bool = Field(..., description="Whether trade is still open")
    pnl_percentage: Optional[float] = Field(None, description="P&L as percentage")
    holding_period: Optional[str] = Field(None, description="Human-readable holding period")


# Query and Filter Schemas
class StrategyFilters(BaseSchema):
    """Schema for strategy query filters"""
    strategy_type: Optional[StrategyType] = None
    status: Optional[StrategyStatus] = None
    category_id: Optional[UUID] = None
    risk_level: Optional[RiskLevel] = None
    is_public: Optional[bool] = None
    is_template: Optional[bool] = None
    author_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    min_return: Optional[float] = None
    max_drawdown_limit: Optional[float] = Field(None, ge=0, le=100)
    featured: Optional[bool] = None
    search: Optional[str] = Field(None, min_length=1, description="Search in name and description")

    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags filter"""
        if v is not None:
            return [tag.strip().lower() for tag in v if tag and tag.strip()]
        return v


class PaginationParams(BaseSchema):
    """Schema for pagination parameters"""
    page: int = Field(1, ge=1, description="Page number (1-based)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$", description="Sort order")

    @property
    def offset(self) -> int:
        """Calculate offset for database query"""
        return (self.page - 1) * self.page_size


class StrategyListResponse(BaseSchema):
    """Schema for paginated strategy list response"""
    items: List[StrategyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


# Bulk Operation Schemas
class StrategyBulkUpdate(BaseSchema):
    """Schema for bulk strategy updates"""
    strategy_ids: List[UUID] = Field(..., min_items=1, description="List of strategy IDs")
    updates: StrategyUpdate = Field(..., description="Update fields to apply")

    @validator('strategy_ids')
    def validate_strategy_ids(cls, v):
        """Validate strategy IDs list"""
        # Remove duplicates
        unique_ids = list(set(v))
        if len(unique_ids) != len(v):
            raise ValueError("Strategy IDs list contains duplicates")
        return unique_ids


class StrategyDuplicateRequest(BaseSchema):
    """Schema for strategy duplication"""
    name: str = Field(..., min_length=1, max_length=200, description="New strategy name")
    slug: Optional[str] = Field(None, max_length=200, pattern=r'^[a-z0-9-]+$')
    description: Optional[str] = Field(None, max_length=2000)
    copy_parameters: bool = Field(True, description="Copy parameter settings")
    copy_backtests: bool = Field(False, description="Copy backtest history")
    update_parameters: Optional[Dict[str, Any]] = Field(None, description="Parameters to update in copy")

    @validator('slug', always=True)
    def generate_slug(cls, v, values):
        """Generate slug from name if not provided"""
        if v is None and 'name' in values:
            import re
            name = values['name'].lower()
            slug = re.sub(r'[^a-z0-9]+', '-', name)
            slug = slug.strip('-')
            slug = re.sub(r'-+', '-', slug)
            return slug
        return v


# Export all schemas
__all__ = [
    # Category schemas
    'StrategyCategoryCreate',
    'StrategyCategoryUpdate',
    'StrategyCategoryResponse',

    # Strategy schemas
    'StrategyParameterSchema',
    'StrategyCreate',
    'StrategyUpdate',
    'StrategyResponse',

    # Instance schemas
    'StrategyInstanceCreate',
    'StrategyInstanceUpdate',
    'StrategyInstanceResponse',

    # Performance schemas
    'StrategyPerformanceResponse',

    # Trade schemas
    'TradeCreate',
    'TradeResponse',

    # Query schemas
    'StrategyFilters',
    'PaginationParams',
    'StrategyListResponse',

    # Bulk operation schemas
    'StrategyBulkUpdate',
    'StrategyDuplicateRequest',

    # Enums
    'DirectionEnum',
    'ExitReasonEnum',
]
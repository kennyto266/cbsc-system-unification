"""
Data models for CBSC Trading API SDK
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class TokenRequest(BaseModel):
    """Token request model"""
    grant_type: str = Field(default="client_credentials", description="Grant type")
    client_id: str = Field(..., description="Client ID")
    client_secret: str = Field(..., description="Client secret")
    scope: Optional[str] = Field(default=None, description="Request scope")


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str = Field(..., description="Access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(default=None, description="Refresh token")
    scope: Optional[str] = Field(default=None, description="Granted scope")


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str = Field(..., description="Refresh token")


class UserLogin(BaseModel):
    """User login model"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class UserCreate(BaseModel):
    """User creation model"""
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Password")
    full_name: Optional[str] = Field(default=None, description="Full name")
    is_active: bool = Field(default=True, description="User active status")
    is_superuser: bool = Field(default=False, description="Superuser status")

    @validator('email')
    def email_must_be_valid(cls, v):
        if '@' not in v:
            raise ValueError('Email must be valid')
        return v


class User(BaseModel):
    """User model"""
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: Optional[str] = Field(default=None, description="Full name")
    is_active: bool = Field(default=True, description="User active status")
    is_superuser: bool = Field(default=False, description="Superuser status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class StrategyType(str, Enum):
    """Strategy type enumeration"""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    ARBITRAGE = "arbitrage"
    RSI = "RSI"
    MACD = "MACD"
    CUSTOM = "custom"


class StrategyCreate(BaseModel):
    """Strategy creation model"""
    name: str = Field(..., description="Strategy name")
    type: StrategyType = Field(..., description="Strategy type")
    description: Optional[str] = Field(default=None, description="Strategy description")
    config: Dict[str, Any] = Field(default_factory=dict, description="Strategy configuration")
    is_active: bool = Field(default=True, description="Strategy active status")
    risk_level: Optional[int] = Field(default=5, ge=1, le=10, description="Risk level (1-10)")


class Strategy(BaseModel):
    """Strategy model"""
    id: int = Field(..., description="Strategy ID")
    name: str = Field(..., description="Strategy name")
    type: StrategyType = Field(..., description="Strategy type")
    description: Optional[str] = Field(default=None, description="Strategy description")
    config: Dict[str, Any] = Field(default_factory=dict, description="Strategy configuration")
    is_active: bool = Field(default=True, description="Strategy active status")
    risk_level: int = Field(default=5, ge=1, le=10, description="Risk level (1-10)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    performance: Optional[Dict[str, Any]] = Field(default=None, description="Performance metrics")


class Symbol(BaseModel):
    """Symbol model"""
    symbol: str = Field(..., description="Symbol code")
    name: str = Field(..., description="Symbol name")
    exchange: str = Field(..., description="Exchange name")
    sector: Optional[str] = Field(default=None, description="Sector")
    market_cap: Optional[float] = Field(default=None, description="Market capitalization")
    price: Optional[float] = Field(default=None, description="Current price")
    change: Optional[float] = Field(default=None, description="Price change")
    change_percent: Optional[float] = Field(default=None, description="Price change percentage")
    volume: Optional[int] = Field(default=None, description="Trading volume")


class Quote(BaseModel):
    """Quote model"""
    symbol: str = Field(..., description="Symbol code")
    price: float = Field(..., description="Current price")
    bid: float = Field(..., description="Bid price")
    ask: float = Field(..., description="Ask price")
    volume: int = Field(..., description="Volume")
    timestamp: datetime = Field(..., description="Quote timestamp")


class OrderSide(str, Enum):
    """Order side enumeration"""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    PARTIALLY_FILLED = "partially_filled"


class OrderCreate(BaseModel):
    """Order creation model"""
    symbol: str = Field(..., description="Symbol code")
    side: OrderSide = Field(..., description="Order side")
    order_type: OrderType = Field(..., description="Order type")
    quantity: int = Field(..., gt=0, description="Order quantity")
    price: Optional[float] = Field(default=None, description="Order price (for limit orders)")
    stop_price: Optional[float] = Field(default=None, description="Stop price (for stop orders)")


class Order(BaseModel):
    """Order model"""
    id: int = Field(..., description="Order ID")
    symbol: str = Field(..., description="Symbol code")
    side: OrderSide = Field(..., description="Order side")
    order_type: OrderType = Field(..., description="Order type")
    quantity: int = Field(..., description="Order quantity")
    price: Optional[float] = Field(default=None, description="Order price")
    stop_price: Optional[float] = Field(default=None, description="Stop price")
    status: OrderStatus = Field(..., description="Order status")
    filled_quantity: int = Field(default=0, description="Filled quantity")
    average_price: Optional[float] = Field(default=None, description="Average fill price")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class Position(BaseModel):
    """Position model"""
    symbol: str = Field(..., description="Symbol code")
    quantity: int = Field(..., description="Position quantity")
    average_price: float = Field(..., description="Average entry price")
    market_value: float = Field(..., description="Current market value")
    unrealized_pnl: float = Field(..., description="Unrealized profit/loss")
    unrealized_pnl_percent: float = Field(..., description="Unrealized P&L percentage")


class Portfolio(BaseModel):
    """Portfolio model"""
    total_value: float = Field(..., description="Total portfolio value")
    cash_balance: float = Field(..., description="Cash balance")
    positions: List[Position] = Field(default_factory=list, description="List of positions")
    daily_pnl: float = Field(..., description="Daily profit/loss")
    total_pnl: float = Field(..., description="Total profit/loss")
    total_pnl_percent: float = Field(..., description="Total P&L percentage")


class BacktestCreate(BaseModel):
    """Backtest creation model"""
    symbol: str = Field(..., description="Symbol code")
    strategy: Dict[str, Any] = Field(..., description="Strategy configuration")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: float = Field(default=100000.0, description="Initial capital")


class Backtest(BaseModel):
    """Backtest model"""
    id: int = Field(..., description="Backtest ID")
    symbol: str = Field(..., description="Symbol code")
    strategy: Dict[str, Any] = Field(..., description="Strategy configuration")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: float = Field(..., description="Initial capital")
    final_capital: float = Field(..., description="Final capital")
    total_return: float = Field(..., description="Total return")
    sharpe_ratio: Optional[float] = Field(default=None, description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    trades_count: int = Field(..., description="Number of trades")
    win_rate: float = Field(..., description="Win rate")
    status: str = Field(..., description="Backtest status")
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")


class WebhookEventType(str, Enum):
    """Webhook event type enumeration"""
    STRATEGY_CREATED = "strategy.created"
    STRATEGY_UPDATED = "strategy.updated"
    STRATEGY_DELETED = "strategy.deleted"
    ORDER_CREATED = "order.created"
    ORDER_FILLED = "order.filled"
    ORDER_CANCELLED = "order.cancelled"
    PORTFOLIO_UPDATED = "portfolio.updated"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"


class WebhookCreate(BaseModel):
    """Webhook creation model"""
    url: str = Field(..., description="Webhook URL")
    events: List[WebhookEventType] = Field(..., description="Event types to subscribe")
    description: Optional[str] = Field(default=None, description="Webhook description")
    is_active: bool = Field(default=True, description="Webhook active status")
    secret: Optional[str] = Field(default=None, description="Webhook secret")


class Webhook(BaseModel):
    """Webhook model"""
    id: int = Field(..., description="Webhook ID")
    url: str = Field(..., description="Webhook URL")
    events: List[WebhookEventType] = Field(..., description="Event types")
    description: Optional[str] = Field(default=None, description="Webhook description")
    is_active: bool = Field(default=True, description="Webhook active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class APIResponse(BaseModel):
    """Generic API response model"""
    success: bool = Field(default=True, description="Request success status")
    message: str = Field(default="操作成功", description="Response message")
    data: Optional[Any] = Field(default=None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    total: Optional[int] = Field(default=None, description="Total count for paginated responses")
    skip: Optional[int] = Field(default=None, description="Skip count for paginated responses")
    limit: Optional[int] = Field(default=None, description="Limit count for paginated responses")
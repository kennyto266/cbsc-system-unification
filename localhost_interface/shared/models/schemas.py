"""
共享數據模型和Pydantic schemas
定義前後端之間通信的數據結構
"""

from datetime import datetime, date
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
import numpy as np

# 角色枚舉
class UserRole(str, Enum):
    ADMIN = "admin"
    TRADER = "trader"
    ANALYST = "analyst"
    GUEST = "guest"

# 交易信號類型
class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    NEUTRAL = "neutral"

# 市場狀態
class MarketStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    POST_MARKET = "post_market"
    HOLIDAY = "holiday"

# 數據源類型
class DataSourceType(str, Enum):
    HIBOR = "hibor"
    EXCHANGE_RATE = "exchange_rate"
    MONETARY_BASE = "monetary_base"
    LIQUIDITY = "liquidity"
    EFBN = "efbn"
    RMB_LIQUIDITY = "rmb_liquidity"

# 技術指標類型
class IndicatorType(str, Enum):
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER_BANDS = "bollinger_bands"
    STOCHASTIC = "stochastic"
    WILLIAMS_R = "williams_r"
    ROC = "roc"
    MOVING_AVERAGE = "moving_average"

# === 用戶認證相關 ===
class User(BaseModel):
    """用戶模型"""
    username: str
    full_name: str
    email: str
    role: UserRole
    permissions: List[str]
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None

class Token(BaseModel):
    """JWT令牌響應"""
    access_token: str
    token_type: str
    expires_in: int
    user: User

# === 市場數據相關 ===
class MarketDataPoint(BaseModel):
    """市場數據點"""
    symbol: str
    timestamp: datetime
    price: float
    volume: int
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    close: Optional[float] = None

class NonPriceData(BaseModel):
    """非價格信號數據"""
    source: DataSourceType
    timestamp: datetime
    value: float
    unit: str
    description: Optional[str] = None

# === 技術指標相關 ===
class TechnicalIndicator(BaseModel):
    """技術指標"""
    name: IndicatorType
    symbol: str
    timestamp: datetime
    value: float
    parameters: Dict[str, Any]
    signal_type: SignalType
    confidence: float = Field(ge=0, le=1)  # 0-1之間的置信度

class IndicatorParameters(BaseModel):
    """指標參數"""
    rsi_period: int = Field(default=14, ge=1, le=100)
    rsi_oversold: float = Field(default=30, ge=0, le=100)
    rsi_overbought: float = Field(default=70, ge=0, le=100)
    rsi_weight: float = Field(default=0.4, ge=0, le=1)
    macd_fast: int = Field(default=12, ge=1, le=50)
    macd_slow: int = Field(default=26, ge=1, le=100)
    macd_signal: int = Field(default=9, ge=1, le=30)
    macd_weight: float = Field(default=0.3, ge=0, le=1)
    bb_period: int = Field(default=20, ge=1, le=50)
    bb_std: float = Field(default=2.0, ge=0.5, le=5.0)
    bb_weight: float = Field(default=0.3, ge=0, le=1)

# === 交易信號相關 ===
class TradingSignal(BaseModel):
    """交易信號"""
    id: str
    symbol: str
    signal_type: SignalType
    strength: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    price_at_signal: float
    timestamp: datetime
    source_indicators: List[str]
    strategy_name: str
    parameters: Dict[str, Any]
    expiry_time: Optional[datetime] = None
    is_active: bool = True

class SignalFilter(BaseModel):
    """信號過濾器"""
    symbol: Optional[str] = None
    signal_type: Optional[SignalType] = None
    min_strength: float = Field(default=0.0, ge=0, le=1)
    min_confidence: float = Field(default=0.0, ge=0, le=1)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

# === 策略相關 ===
class StrategyConfig(BaseModel):
    """策略配置"""
    name: str
    description: str
    symbols: List[str]
    parameters: Dict[str, Any]
    indicators: List[IndicatorType]
    risk_limits: Dict[str, float]
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class StrategyPerformance(BaseModel):
    """策略性能"""
    strategy_id: str
    symbol: str
    total_return: float
    annualized_return: float
    sortino_ratio: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    win_rate: float
    total_trades: int
    avg_trade_return: float
    volatility: float
    var_95: float  # 95% VaR
    cvar_95: float  # 95% CVaR
    last_updated: datetime

# === 回測相關 ===
class BacktestRequest(BaseModel):
    """回測請求"""
    strategy_config: StrategyConfig
    start_date: date
    end_date: date
    initial_capital: float = Field(default=1000000, gt=0)
    commission: float = Field(default=0.001, ge=0)
    slippage: float = Field(default=0.0001, ge=0)
    rebalance_frequency: str = Field(default="daily")
    benchmark_symbol: Optional[str] = None

class BacktestResult(BaseModel):
    """回測結果"""
    request_id: str
    strategy_name: str
    symbol: str
    period_start: date
    period_end: date

    # 基本統計
    total_return: float
    annualized_return: float
    volatility: float

    # 風險調整收益
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float

    # 回撤分析
    max_drawdown: float
    max_drawdown_duration: int
    avg_drawdown: float
    recovery_time: int

    # 交易統計
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_trade_return: float
    avg_winning_trade: float
    avg_losing_trade: float
    profit_factor: float

    # 資產曲線
    equity_curve: List[float]
    benchmark_curve: Optional[List[float]] = None

    # 詳細交易記錄
    trades: List[Dict[str, Any]]

    # 性能指標
    alpha: float
    beta: float
    information_ratio: float
    treynor_ratio: float

    # 時間戳
    created_at: datetime
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None  # 秒

# === 風險管理相關 ===
class RiskMetrics(BaseModel):
    """風險指標"""
    symbol: str
    timestamp: datetime

    # 當前風險
    current_position: float
    unrealized_pnl: float
    realized_pnl: float
    daily_var: float
    portfolio_var: float

    # 風險限制
    position_limit: float
    loss_limit: float
    var_limit: float

    # 風險警告
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    warnings: List[str]

    # 止損和止盈
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None

class RiskAlert(BaseModel):
    """風險警報"""
    id: str
    symbol: str
    alert_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None

# === 性能分析相關 ===
class PerformanceMetrics(BaseModel):
    """性能指標"""
    period_start: date
    period_end: date

    # 收益指標
    total_return: float
    daily_returns: List[float]
    monthly_returns: List[float]

    # 風險指標
    volatility: float
    downside_volatility: float
    skewness: float
    kurtosis: float

    # 風險調整收益
    sharpe_ratio: float
    sortino_ratio: float
    information_ratio: float

    # 回撤指標
    max_drawdown: float
    max_drawdown_duration: int
    current_drawdown: float

    # 基準比較
    alpha: float
    beta: float
    tracking_error: float
    up_capture: float
    down_capture: float

    # 統計檢驗
    t_statistic: Optional[float] = None
    p_value: Optional[float] = None

    last_updated: datetime

# === WebSocket消息相關 ===
class WebSocketMessage(BaseModel):
    """WebSocket消息基類"""
    type: str
    timestamp: datetime
    data: Dict[str, Any]

class SubscriptionMessage(WebSocketMessage):
    """訂閱消息"""
    type: str = "subscribe"
    symbol: str
    message_type: str  # signals, market_data, performance, risk

class DataUpdateMessage(WebSocketMessage):
    """數據更新消息"""
    type: str
    symbol: str
    update_type: str

# === 系統狀態相關 ===
class SystemStatus(BaseModel):
    """系統狀態"""
    status: str  # healthy, degraded, down
    timestamp: datetime
    uptime: float  # 運行時間（秒）

    # 服務狀態
    trading_service: bool
    data_service: bool
    websocket_service: bool
    database_service: bool

    # 性能指標
    cpu_usage: float
    memory_usage: float
    disk_usage: float

    # 連接統計
    active_websockets: int
    active_sessions: int

    # 錯誤統計
    error_rate: float
    last_error: Optional[str] = None

class HealthCheckResponse(BaseModel):
    """健康檢查響應"""
    status: str
    timestamp: datetime
    services: Dict[str, Any]
    version: str = "1.0.0"

# === 配置相關 ===
class SystemConfig(BaseModel):
    """系統配置"""
    market_data_sources: List[str]
    supported_symbols: List[str]
    default_timeframes: List[str]
    max_concurrent_backtests: int
    websocket_rate_limit: int

    # 風險限制
    max_position_size: float
    max_daily_loss: float
    max_var_percentage: float

    # 數據保留政策
    data_retention_days: int
    log_retention_days: int

# === 驗證器 ===
@validator('period_end', pre=True, always=True)
def validate_date_range(cls, v, values):
    if 'period_start' in values and v <= values['period_start']:
        raise ValueError('end_date must be after start_date')
    return v

@validator('confidence', pre=True, always=True)
def validate_confidence(cls, v):
    if not 0 <= v <= 1:
        raise ValueError('confidence must be between 0 and 1')
    return v

@validator('strength', pre=True, always=True)
def validate_strength(cls, v):
    if not 0 <= v <= 1:
        raise ValueError('strength must be between 0 and 1')
    return v

# === 類型別名 ===
NumericArray = Union[List[float], np.ndarray]
PriceData = Dict[str, Union[float, int, str, datetime]]
SignalData = Dict[str, Any]
OptimizationResult = Dict[str, Any]
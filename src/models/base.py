"""
港股量化交易 AI Agent 系统基础数据模型

定义系统中的核心数据模型，包括市场数据、交易信号、投资组合等。
所有模型都基于Pydantic，提供数据验证和序列化功能。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel as PydanticBaseModel, Field, validator, root_validator, model_validator

class SignalType(str, Enum):
    """交易信号类型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class AgentStatus(str, Enum):
    """Agent状态"""
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    STOPPED = "stopped"

class MessageType(str, Enum):
    """消息类型"""
    SIGNAL = "signal"
    DATA = "data"
    CONTROL = "control"
    HEARTBEAT = "heartbeat"

class BaseModel(PydanticBaseModel):
    """基础模型类"""

    class Config:
        # 使用枚举值而不是枚举名称
        use_enum_values = True

        allow_population_by_field_name = True

        validate_assignment = True

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }

class MarketData(BaseModel):
    """市场数据模型"""
    symbol: str = Field(..., description="交易代码")
    timestamp: datetime = Field(..., description="时间戳")
    open_price: Decimal = Field(..., gt=0, description="开盘价")
    high_price: Decimal = Field(..., gt=0, description="最高价")
    low_price: Decimal = Field(..., gt=0, description="最低价")
    close_price: Decimal = Field(..., gt=0, description="收盘价")
    volume: int = Field(..., ge=0, description="成交量")
    turnover: Optional[Decimal] = Field(None, ge=0, description="成交额")

class TradingSignal(BaseModel):
    """交易信号模型"""
    symbol: str = Field(..., description="交易代码")
    signal_type: SignalType = Field(..., description="信号类型")
    strength: float = Field(..., ge=-1, le=1, description="信号强度")
    timestamp: datetime = Field(..., description="信号时间戳")
    price: Decimal = Field(..., gt=0, description="信号价格")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

class Holding(BaseModel):
    """持仓模型"""
    symbol: str = Field(..., description="交易代码")
    quantity: int = Field(..., description="持仓数量")
    entry_price: Decimal = Field(..., gt=0, description="入场价格")
    entry_date: datetime = Field(..., description="入场日期")
    current_price: Optional[Decimal] = Field(None, description="当前价格")
    market_value: Optional[Decimal] = Field(None, description="市值")
    unrealized_pnl: Optional[Decimal] = Field(None, description="未实现损益")

class Portfolio(BaseModel):
    """投资组合模型"""
    holdings: List[Holding] = Field(default_factory=list, description="持仓列表")
    cash: Decimal = Field(..., ge=0, description="现金余额")
    total_value: Optional[Decimal] = Field(None, description="总资产")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")

class RiskMetrics(BaseModel):
    """风险指标模型"""
    volatility: float = Field(..., ge=0, description="波动率")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    max_drawdown: float = Field(..., le=0, description="最大回撤")
    var_95: Optional[float] = Field(None, description="95% VaR")
    beta: Optional[float] = Field(None, description="贝塔系数")
    tracking_error: Optional[float] = Field(None, description="跟踪误差")
    calculated_at: datetime = Field(default_factory=datetime.now, description="计算时间")

class PerformanceMetrics(BaseModel):
    """性能指标模型"""
    total_return: float = Field(..., description="总收益率")
    annualized_return: Optional[float] = Field(None, description="年化收益率")
    win_rate: float = Field(..., ge=0, le=1, description="胜率")
    profit_factor: Optional[float] = Field(None, description="盈利因子")
    total_trades: int = Field(..., ge=0, description="总交易次数")
    winning_trades: int = Field(..., ge=0, description="盈利交易次数")
    period_start: datetime = Field(..., description="统计开始时间")
    period_end: datetime = Field(..., description="统计结束时间")
"""
港股量化交易 AI Agent 系统基础数据模型

定义系统中的核心数据模型，包括市场数据、交易信号、投资组合等。
所有模型都基于Pydantic，提供数据验证和序列化功能。
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import (
    Field,
    model_validator,
    root_validator,
    validator,
)


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
        # 允许字段别名
        allow_population_by_field_name = True
        # 验证赋值
        validate_assignment = True
        # 使用UTC时间
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
        }


class MarketData(BaseModel):
    """市场数据模型"""

    symbol: str = Field(..., description="股票代码")
    timestamp: datetime = Field(..., description="时间戳")
    open_price: Decimal = Field(..., gt=0, description="开盘价")
    high_price: Decimal = Field(..., gt=0, description="最高价")
    low_price: Decimal = Field(..., gt=0, description="最低价")
    close_price: Decimal = Field(..., gt=0, description="收盘价")
    volume: int = Field(..., ge=0, description="成交量")
    turnover: Optional[Decimal] = Field(None, description="成交额")
    market_cap: Optional[Decimal] = Field(None, description="市值")
    pe_ratio: Optional[Decimal] = Field(None, description="市盈率")
    pb_ratio: Optional[Decimal] = Field(None, description="市净率")
    dividend_yield: Optional[Decimal] = Field(None, description="股息率")

    @validator("high_price")
    def high_price_must_be_highest(cls, v, values):
        """验证最高价是最高价格"""
        if "low_price" in values and "open_price" in values and "close_price" in values:
            if v < max(
                values["low_price"], values["open_price"], values["close_price"]
            ):
                raise ValueError("最高价必须高于其他价格")
        return v

    @validator("low_price")
    def low_price_must_be_lowest(cls, v, values):
        """验证最低价是最低价格"""
        if (
            "high_price" in values
            and "open_price" in values
            and "close_price" in values
        ):
            if v > min(
                values["high_price"], values["open_price"], values["close_price"]
            ):
                raise ValueError("最低价必须低于其他价格")
        return v


class TradingSignal(BaseModel):
    """交易信号模型"""

    signal_id: str = Field(..., description="信号ID")
    symbol: str = Field(..., description="股票代码")
    signal_type: SignalType = Field(..., description="信号类型")
    confidence_score: float = Field(..., ge=0, le=1, description="置信度")
    timestamp: datetime = Field(..., description="生成时间")
    reasoning: str = Field(..., description="决策理由")
    target_price: Optional[Decimal] = Field(None, gt=0, description="目标价格")
    stop_loss: Optional[Decimal] = Field(None, gt=0, description="止损价格")
    take_profit: Optional[Decimal] = Field(None, gt=0, description="止盈价格")
    position_size: Optional[int] = Field(None, ge=0, description="建议仓位大小")
    risk_reward_ratio: Optional[float] = Field(None, description="风险回报比")
    source_agent: str = Field(..., description="信号来源Agent")

    @validator("stop_loss")
    def stop_loss_validation(cls, v, values):
        """验证止损价格逻辑"""
        if v and "target_price" in values and values["target_price"]:
            if (
                values.get("signal_type") == SignalType.BUY
                and v >= values["target_price"]
            ):
                raise ValueError("买入信号的止损价必须低于目标价")
            elif (
                values.get("signal_type") == SignalType.SELL
                and v <= values["target_price"]
            ):
                raise ValueError("卖出信号的止损价必须高于目标价")
        return v


class Holding(BaseModel):
    """持仓模型"""

    symbol: str = Field(..., description="股票代码")
    quantity: int = Field(..., ge=0, description="持有数量")
    average_cost: Decimal = Field(..., gt=0, description="平均成本")
    current_price: Decimal = Field(..., gt=0, description="当前价格")
    market_value: Decimal = Field(..., ge=0, description="市值")
    unrealized_pnl: Decimal = Field(..., description="未实现盈亏")
    unrealized_pnl_pct: Decimal = Field(..., description="未实现盈亏百分比")
    purchase_date: date = Field(..., description="购买日期")
    last_updated: datetime = Field(..., description="最后更新时间")

    @model_validator(mode="after")
    def calculate_derived_fields(self):
        """计算衍生字段"""
        if self.quantity and self.average_cost and self.current_price:
            self.market_value = self.quantity * self.current_price
            cost_basis = self.quantity * self.average_cost
            self.unrealized_pnl = self.market_value - cost_basis
            self.unrealized_pnl_pct = (
                (self.unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else 0
            )

        return self


class PerformanceMetrics(BaseModel):
    """绩效指标模型"""

    total_return: Decimal = Field(..., description="总收益率")
    annualized_return: Decimal = Field(..., description="年化收益率")
    volatility: Decimal = Field(..., ge=0, description="波动率")
    sharpe_ratio: Decimal = Field(..., description="夏普比率")
    sortino_ratio: Optional[Decimal] = Field(None, description="索提诺比率")
    max_drawdown: Decimal = Field(..., le=0, description="最大回撤")
    calmar_ratio: Optional[Decimal] = Field(None, description="卡尔玛比率")
    win_rate: Decimal = Field(..., ge=0, le=1, description="胜率")
    profit_factor: Optional[Decimal] = Field(None, description="盈利因子")
    start_date: date = Field(..., description="统计开始日期")
    end_date: date = Field(..., description="统计结束日期")

    @validator("end_date")
    def end_date_after_start_date(cls, v, values):
        """验证结束日期晚于开始日期"""
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("结束日期必须晚于开始日期")
        return v


class RiskMetrics(BaseModel):
    """风险指标模型"""

    portfolio_id: str = Field(..., description="投资组合ID")
    var_95: Decimal = Field(..., description="95% VaR")
    var_99: Decimal = Field(..., description="99% VaR")
    expected_shortfall: Decimal = Field(..., description="期望损失")
    sharpe_ratio: Decimal = Field(..., description="夏普比率")
    max_drawdown: Decimal = Field(..., le=0, description="最大回撤")
    volatility: Decimal = Field(..., ge=0, description="波动率")
    beta: Decimal = Field(..., description="贝塔系数")
    tracking_error: Optional[Decimal] = Field(None, description="跟踪误差")
    information_ratio: Optional[Decimal] = Field(None, description="信息比率")
    calculation_date: datetime = Field(..., description="计算日期")
    confidence_level: float = Field(..., ge=0, le=1, description="置信水平")

    @validator("var_99")
    def var_99_greater_than_var_95(cls, v, values):
        """验证99% VaR大于95% VaR"""
        if "var_95" in values and v <= values["var_95"]:
            raise ValueError("99% VaR必须大于95% VaR")
        return v


class Portfolio(BaseModel):
    """投资组合模型"""

    portfolio_id: str = Field(..., description="投资组合ID")
    name: str = Field(..., description="投资组合名称")
    total_value: Decimal = Field(..., gt=0, description="总价值")
    cash_balance: Decimal = Field(..., ge=0, description="现金余额")
    holdings: List[Holding] = Field(default_factory=list, description="持仓列表")
    risk_metrics: Optional[RiskMetrics] = Field(None, description="风险指标")
    performance_metrics: Optional[PerformanceMetrics] = Field(
        None, description="绩效指标"
    )
    created_date: datetime = Field(..., description="创建日期")
    last_rebalanced: Optional[datetime] = Field(None, description="最后再平衡日期")
    target_allocation: Dict[str, float] = Field(
        default_factory=dict, description="目标配置"
    )
    actual_allocation: Dict[str, float] = Field(
        default_factory=dict, description="实际配置"
    )

    @validator("cash_balance")
    def cash_balance_not_exceed_total_value(cls, v, values):
        """验证现金余额不超过总价值"""
        if "total_value" in values and v > values["total_value"]:
            raise ValueError("现金余额不能超过总价值")
        return v

    def calculate_total_holdings_value(self) -> Decimal:
        """计算持仓总价值"""
        return sum(holding.market_value for holding in self.holdings)

    def calculate_cash_ratio(self) -> float:
        """计算现金比例"""
        if self.total_value == 0:
            return 0.0
        return float(self.cash_balance / self.total_value)

    def calculate_holdings_ratio(self) -> float:
        """计算持仓比例"""
        if self.total_value == 0:
            return 0.0
        return float(self.calculate_total_holdings_value() / self.total_value)


class AgentInfo(BaseModel):
    """Agent信息模型"""

    agent_id: str = Field(..., description="Agent ID")
    agent_type: str = Field(..., description="Agent类型")
    status: AgentStatus = Field(..., description="Agent状态")
    last_heartbeat: datetime = Field(..., description="最后心跳时间")
    cpu_usage: float = Field(..., ge=0, le=100, description="CPU使用率")
    memory_usage: float = Field(..., ge=0, le=100, description="内存使用率")
    messages_processed: int = Field(..., ge=0, description="已处理消息数")
    error_count: int = Field(..., ge=0, description="错误计数")
    uptime: float = Field(..., ge=0, description="运行时间（秒）")
    version: str = Field(..., description="Agent版本")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="配置信息")


class SystemMetrics(BaseModel):
    """系统指标模型"""

    timestamp: datetime = Field(..., description="时间戳")
    active_agents: int = Field(..., ge=0, description="活跃Agent数量")
    total_messages_processed: int = Field(..., ge=0, description="总处理消息数")
    system_cpu_usage: float = Field(..., ge=0, le=100, description="系统CPU使用率")
    system_memory_usage: float = Field(..., ge=0, le=100, description="系统内存使用率")
    redis_memory_usage: float = Field(..., ge=0, le=100, description="Redis内存使用率")
    queue_lengths: Dict[str, int] = Field(default_factory=dict, description="队列长度")
    error_rate: float = Field(..., ge=0, le=1, description="错误率")
    throughput: float = Field(..., ge=0, description="吞吐量（消息 / 秒）")
    latency_p95: float = Field(..., ge=0, description="95 % 延迟（毫秒）")
    latency_p99: float = Field(..., ge=0, description="99 % 延迟（毫秒）")


# 导出所有模型
__all__ = [
    "BaseModel",
    "SignalType",
    "AgentStatus",
    "MessageType",
    "MarketData",
    "TradingSignal",
    "Holding",
    "PerformanceMetrics",
    "RiskMetrics",
    "Portfolio",
    "AgentInfo",
    "SystemMetrics",
]

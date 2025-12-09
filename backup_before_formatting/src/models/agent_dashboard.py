"""
港股量化交易 AI Agent 系统 - Agent仪表板数据模型

定义仪表板所需的数据模型，包括Agent状态、策略信息、绩效指标等。
扩展现有模型以支持仪表板的完整功能需求。
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, model_validator

from .base import AgentInfo, AgentStatus
from .base import BaseModel as PydanticBaseModel
from .base import SignalType


class StrategyType(str, Enum):
    """交易策略类型"""

    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    ARBITRAGE = "arbitrage"
    MARKET_MAKING = "market_making"
    TREND_FOLLOWING = "trend_following"
    STATISTICAL_ARBITRAGE = "statistical_arbitrage"
    MACHINE_LEARNING = "machine_learning"


class StrategyStatus(str, Enum):
    """策略状态"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    PAUSED = "paused"
    ERROR = "error"


class PerformancePeriod(str, Enum):
    """绩效统计周期"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ALL_TIME = "all_time"


class ControlActionType(str, Enum):
    """控制操作类型"""

    START = "start"
    STOP = "stop"
    RESTART = "restart"
    PAUSE = "pause"
    RESUME = "resume"
    UPDATE_PARAMETERS = "update_parameters"
    SWITCH_STRATEGY = "switch_strategy"


class ActionStatus(str, Enum):
    """操作状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionResult(BaseModel):
    """操作结果"""

    success: bool
    message: str
    error_code: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class StrategyParameter(BaseModel):
    """策略参数"""

    name: str
    value: Union[str, int, float, bool]
    type: str  # "string", "number", "boolean", "array"
    description: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    options: Optional[List[str]] = None


class BacktestMetrics(BaseModel):
    """回测指标"""

    total_return: float = Field(..., description="总收益率")
    annualized_return: float = Field(..., description="年化收益率")
    volatility: float = Field(..., description="波动率")
    sharpe_ratio: float = Field(..., description="夏普比率")
    max_drawdown: float = Field(..., description="最大回撤")
    win_rate: float = Field(..., description="胜率")
    profit_factor: float = Field(..., description="盈利因子")
    trades_count: int = Field(..., description="交易次数")
    avg_trade_duration: float = Field(..., description="平均持仓时间（天）")
    backtest_period_start: date = Field(..., description="回测开始日期")
    backtest_period_end: date = Field(..., description="回测结束日期")
    benchmark_return: Optional[float] = Field(None, description="基准收益率")
    alpha: Optional[float] = Field(None, description="Alpha")
    beta: Optional[float] = Field(None, description="Beta")
    information_ratio: Optional[float] = Field(None, description="信息比率")


class LiveMetrics(BaseModel):
    """实盘指标"""

    current_return: float = Field(..., description="当前收益率")
    daily_pnl: float = Field(..., description="当日盈亏")
    unrealized_pnl: float = Field(..., description="未实现盈亏")
    realized_pnl: float = Field(..., description="已实现盈亏")
    current_drawdown: float = Field(..., description="当前回撤")
    positions_count: int = Field(..., description="持仓数量")
    exposure_ratio: float = Field(..., description="仓位比例")
    last_trade_time: Optional[datetime] = Field(None, description="最后交易时间")
    live_period_start: datetime = Field(..., description="实盘开始时间")


class StrategyInfo(BaseModel):
    """策略信息"""

    strategy_id: str = Field(..., description="策略ID")
    strategy_name: str = Field(..., description="策略名称")
    strategy_type: StrategyType = Field(..., description="策略类型")
    status: StrategyStatus = Field(..., description="策略状态")
    description: Optional[str] = Field(None, description="策略描述")

    # 策略参数
    parameters: List[StrategyParameter] = Field(
        default_factory=list, description="策略参数"
    )

    # 回测结果
    backtest_metrics: Optional[BacktestMetrics] = Field(None, description="回测指标")

    # 实盘表现
    live_metrics: Optional[LiveMetrics] = Field(None, description="实盘指标")

    # 元数据
    version: str = Field("1.0.0", description="策略版本")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="创建时间"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="最后更新时间"
    )
    last_backtest: Optional[datetime] = Field(None, description="最后回测时间")

    # 风险指标
    risk_level: str = Field("medium", description="风险等级: low / medium / high")
    max_position_size: float = Field(0.1, description="最大仓位比例")
    stop_loss_threshold: Optional[float] = Field(None, description="止损阈值")


class PerformanceMetrics(BaseModel):
    """绩效指标"""

    agent_id: str = Field(..., description="Agent ID")
    calculation_period: PerformancePeriod = Field(..., description="统计周期")

    # 核心绩效指标
    sharpe_ratio: float = Field(..., description="夏普比率")
    total_return: float = Field(..., description="总收益率")
    annualized_return: float = Field(..., description="年化收益率")
    volatility: float = Field(..., description="波动率")
    max_drawdown: float = Field(..., description="最大回撤")

    # 交易统计
    win_rate: float = Field(..., description="胜率")
    profit_factor: float = Field(..., description="盈利因子")
    trades_count: int = Field(..., description="交易次数")
    avg_win: float = Field(..., description="平均盈利")
    avg_loss: float = Field(..., description="平均亏损")

    # 风险指标
    var_95: float = Field(..., description="95% VaR")
    var_99: float = Field(..., description="99% VaR")
    cvar_95: float = Field(..., description="95% CVaR")
    beta: float = Field(..., description="Beta")
    alpha: float = Field(..., description="Alpha")

    # 时间信息
    calculation_date: datetime = Field(
        default_factory=datetime.utcnow, description="计算日期"
    )
    period_start: datetime = Field(..., description="统计期间开始")
    period_end: datetime = Field(..., description="统计期间结束")

    # 基准对比
    benchmark_return: Optional[float] = Field(None, description="基准收益率")
    excess_return: Optional[float] = Field(None, description="超额收益")
    information_ratio: Optional[float] = Field(None, description="信息比率")

    # 其他指标
    calmar_ratio: Optional[float] = Field(None, description="卡尔玛比率")
    sortino_ratio: Optional[float] = Field(None, description="索提诺比率")
    treynor_ratio: Optional[float] = Field(None, description="特雷诺比率")


class ResourceUsage(BaseModel):
    """资源使用情况"""

    agent_id: str = Field(..., description="Agent ID")

    # CPU和内存使用
    cpu_usage: float = Field(..., ge=0, le=100, description="CPU使用率 (%)")
    memory_usage: float = Field(..., ge=0, le=100, description="内存使用率 (%)")
    memory_used_mb: float = Field(..., ge=0, description="已使用内存 (MB)")
    memory_total_mb: float = Field(..., ge=0, description="总内存 (MB)")

    # 网络和IO
    network_in_mbps: float = Field(0.0, ge=0, description="网络入流量 (Mbps)")
    network_out_mbps: float = Field(0.0, ge=0, description="网络出流量 (Mbps)")
    disk_io_mbps: float = Field(0.0, ge=0, description="磁盘IO (Mbps)")

    # 消息处理
    messages_per_second: float = Field(0.0, ge=0, description="消息处理速度 (msg / s)")
    queue_length: int = Field(0, ge=0, description="队列长度")

    # 时间戳
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="记录时间")


class AgentControlAction(BaseModel):
    """Agent控制操作"""

    action_id: str = Field(..., description="操作ID")
    agent_id: str = Field(..., description="Agent ID")
    action_type: ControlActionType = Field(..., description="操作类型")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="操作参数")

    # 状态信息
    status: ActionStatus = Field(ActionStatus.PENDING, description="操作状态")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="创建时间"
    )
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    # 结果信息
    result: Optional[ActionResult] = Field(None, description="操作结果")
    error_message: Optional[str] = Field(None, description="错误信息")

    # 执行者信息
    initiated_by: str = Field("system", description="发起者")
    requires_confirmation: bool = Field(False, description="是否需要确认")


class AgentDashboardData(BaseModel):
    """Agent仪表板数据"""

    agent_id: str = Field(..., description="Agent ID")
    agent_type: str = Field(..., description="Agent类型")

    # 基础状态信息
    status: AgentStatus = Field(..., description="Agent状态")
    last_heartbeat: datetime = Field(..., description="最后心跳时间")
    uptime_seconds: float = Field(..., description="运行时间（秒）")

    # 策略信息
    current_strategy: Optional[StrategyInfo] = Field(None, description="当前策略")
    available_strategies: List[StrategyInfo] = Field(
        default_factory=list, description="可用策略"
    )

    # 绩效指标
    performance_metrics: Optional[PerformanceMetrics] = Field(
        None, description="绩效指标"
    )
    performance_history: List[PerformanceMetrics] = Field(
        default_factory=list, description="绩效历史"
    )

    # 资源使用
    resource_usage: Optional[ResourceUsage] = Field(None, description="资源使用情况")

    # 控制操作
    recent_actions: List[AgentControlAction] = Field(
        default_factory=list, description="最近操作"
    )
    pending_actions: List[AgentControlAction] = Field(
        default_factory=list, description="待处理操作"
    )

    # 统计信息
    messages_processed: int = Field(0, description="已处理消息数")
    error_count: int = Field(0, description="错误计数")
    last_error: Optional[str] = Field(None, description="最后错误信息")

    # 配置信息
    configuration: Dict[str, Any] = Field(default_factory=dict, description="配置信息")
    version: str = Field("1.0.0", description="Agent版本")

    # 时间戳
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="最后更新时间"
    )


class DashboardSummary(BaseModel):
    """仪表板总览"""

    total_agents: int = Field(..., description="总Agent数量")
    active_agents: int = Field(..., description="活跃Agent数量")
    error_agents: int = Field(..., description="错误Agent数量")

    # 系统整体绩效
    system_sharpe_ratio: float = Field(..., description="系统整体夏普比率")
    system_total_return: float = Field(..., description="系统总收益率")
    system_max_drawdown: float = Field(..., description="系统最大回撤")

    # 资源使用汇总
    total_cpu_usage: float = Field(..., description="总CPU使用率")
    total_memory_usage: float = Field(..., description="总内存使用率")
    total_messages_processed: int = Field(..., description="总处理消息数")

    # 活跃策略
    active_strategies: int = Field(..., description="活跃策略数量")
    strategy_types: Dict[str, int] = Field(
        default_factory=dict, description="策略类型分布"
    )

    # 时间信息
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="最后更新时间"
    )


class DashboardAlert(BaseModel):
    """仪表板告警"""

    alert_id: str = Field(..., description="告警ID")
    agent_id: Optional[str] = Field(None, description="相关Agent ID")
    alert_type: str = Field(..., description="告警类型")
    severity: str = Field(..., description="严重程度: info / warning / error / critical")

    # 告警内容
    title: str = Field(..., description="告警标题")
    message: str = Field(..., description="告警消息")
    description: Optional[str] = Field(None, description="详细描述")

    # 状态信息
    status: str = Field("active", description="告警状态: active / acknowledged / resolved")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="创建时间"
    )
    acknowledged_at: Optional[datetime] = Field(None, description="确认时间")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")

    # 操作信息
    acknowledged_by: Optional[str] = Field(None, description="确认者")
    resolved_by: Optional[str] = Field(None, description="解决者")

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


# 扩展现有的AgentInfo模型
class ExtendedAgentInfo(AgentInfo):
    """扩展的Agent信息模型"""

    # 策略信息
    current_strategy: Optional[StrategyInfo] = Field(None, description="当前策略")

    # 绩效指标
    performance_metrics: Optional[PerformanceMetrics] = Field(
        None, description="绩效指标"
    )

    # 资源使用
    resource_usage: Optional[ResourceUsage] = Field(None, description="资源使用情况")

    # 控制操作
    recent_actions: List[AgentControlAction] = Field(
        default_factory=list, description="最近操作"
    )


__all__ = [
    "StrategyType",
    "StrategyStatus",
    "PerformancePeriod",
    "ControlActionType",
    "ActionStatus",
    "ActionResult",
    "StrategyParameter",
    "BacktestMetrics",
    "LiveMetrics",
    "StrategyInfo",
    "PerformanceMetrics",
    "ResourceUsage",
    "AgentControlAction",
    "AgentDashboardData",
    "DashboardSummary",
    "DashboardAlert",
    "ExtendedAgentInfo",
]

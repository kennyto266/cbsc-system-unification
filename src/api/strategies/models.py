"""
统一数据模型
Unified Data Models

职责：
- 定义核心数据结构
- 提供数据转换方法
- 确保数据一致性
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class StrategyType(str, Enum):
    """策略类型"""
    DIRECT_RSI = "direct_rsi"
    DUAL_RSI = "dual_rsi"
    COMPOSITE = "composite"
    CUSTOM = "custom"


class StrategyStatus(str, Enum):
    """策略状态"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SignalType(str, Enum):
    """信号类型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class Strategy(BaseModel):
    """策略模型"""
    id: str = Field(default_factory=lambda: f"strategy_{uuid.uuid4().hex[:12]}")
    name: str
    description: str
    strategy_type: StrategyType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: StrategyStatus = StrategyStatus.INACTIVE
    is_active: bool = False
    user_id: int
    risk_level: RiskLevel = RiskLevel.MEDIUM
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    last_executed: Optional[datetime] = None

    model_config = {"from_attributes": True, "use_enum_values": True}


class StrategySignal(BaseModel):
    """策略信号"""
    signal_id: str = Field(default_factory=lambda: f"signal_{uuid.uuid4().hex[:12]}")
    strategy_id: str
    strategy_type: StrategyType
    signal_type: SignalType
    strength: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)
    market_data: Dict[str, Any] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True, "use_enum_values": True}


class StrategyPerformance(BaseModel):
    """策略性能"""
    strategy_id: str
    total_return: float = 0.0
    annual_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    calmar_ratio: float = 0.0
    total_trades: int = 0
    profit_trades: int = 0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    daily_pnl: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.now)

    model_config = {"from_attributes": True}


class StrategyExecution(BaseModel):
    """策略执行"""
    execution_id: str = Field(default_factory=lambda: f"exec_{uuid.uuid4().hex[:12]}")
    strategy_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    execution_mode: str = Field(default="backtest", pattern="^(backtest|real_time)$")
    data_source: Optional[str] = None
    signals: List[StrategySignal] = Field(default_factory=list)
    performance: Optional[StrategyPerformance] = None
    error_message: Optional[str] = None
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True, "use_enum_values": True}


class User(BaseModel):
    """用户模型"""
    id: int
    username: str
    email: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class StrategyTemplate(BaseModel):
    """策略模板"""
    id: str = Field(default_factory=lambda: f"template_{uuid.uuid4().hex[:12]}")
    name: str
    description: str
    strategy_type: StrategyType
    category: str
    default_parameters: Dict[str, Any] = Field(default_factory=dict)
    parameter_constraints: Dict[str, Any] = Field(default_factory=dict)
    is_system_template: bool = True
    created_by: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = {"from_attributes": True, "use_enum_values": True}


class StrategyParameters(BaseModel):
    """策略参数"""
    rsi_period: int = Field(default=14, ge=2, le=100)
    rsi_oversold: float = Field(default=30.0, ge=0.0, le=100.0)
    rsi_overbought: float = Field(default=70.0, ge=0.0, le=100.0)
    stop_loss: float = Field(default=0.05, ge=0.0, le=1.0)
    take_profit: float = Field(default=0.1, ge=0.0, le=1.0)
    position_size: float = Field(default=1.0, gt=0.0)
    leverage: float = Field(default=1.0, ge=1.0, le=100.0)


class StrategyExecutionRequest(BaseModel):
    """策略执行请求"""
    strategy_id: str
    execution_mode: str = Field(default="backtest", pattern="^(backtest|real_time)$")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    data_source: Optional[str] = None
    parameters_override: Optional[Dict[str, Any]] = None


class StrategyExecutionResult(BaseModel):
    """策略执行结果"""
    execution_id: str
    strategy_id: str
    success: bool
    execution_time: float
    signals_generated: int
    performance_metrics: Optional[Dict[str, float]] = None
    error_message: Optional[str] = None
    execution_details: Dict[str, Any] = Field(default_factory=dict)


class CreateStrategyRequest(BaseModel):
    """创建策略请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    strategy_type: StrategyType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    template_id: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.MEDIUM


class UpdateStrategyRequest(BaseModel):
    """更新策略请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    parameters: Optional[Dict[str, Any]] = None
    status: Optional[StrategyStatus] = None
    is_active: Optional[bool] = None
    risk_level: Optional[RiskLevel] = None


class StrategyListResponse(BaseModel):
    """策略列表响应"""
    strategies: List[Strategy]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class StrategyDetailResponse(BaseModel):
    """策略详情响应"""
    strategy: Strategy
    recent_signals: List[StrategySignal] = Field(default_factory=list)
    performance: Optional[StrategyPerformance] = None
    execution_history: List[StrategyExecution] = Field(default_factory=list)
    risk_metrics: Optional[Dict[str, float]] = None


class BatchStrategyOperation(BaseModel):
    """批量策略操作"""
    strategy_ids: List[str]
    operation: str = Field(..., pattern="^(activate|deactivate|delete|execute)$")
    parameters: Optional[Dict[str, Any]] = None


class StrategyOptimizationRequest(BaseModel):
    """策略优化请求"""
    strategy_id: str
    optimization_type: str = Field(default="grid_search", pattern="^(grid_search|random_search|bayesian)$")
    parameter_ranges: Dict[str, List[float]]
    objective_function: str = Field(default="sharpe_ratio", pattern="^(sharpe_ratio|total_return|profit_factor)$")
    constraints: Optional[Dict[str, Any]] = None


class StrategyOptimizationResult(BaseModel):
    """策略优化结果"""
    strategy_id: str
    optimization_id: str
    best_parameters: Dict[str, Any]
    best_performance: float
    optimization_history: List[Dict[str, Any]]
    optimization_time: float
    success: bool


class CBSCStrategyTemplate(StrategyTemplate):
    """CBSC策略模板扩展"""
    algorithm_description: Optional[str] = None
    market_conditions: List[str] = Field(default_factory=list)
    recommended_timeframes: List[str] = Field(default_factory=list)
    risk_disclaimer: Optional[str] = None


class DataCompatibilityAdapter:
    """数据兼容性适配器"""

    @staticmethod
    def convert_legacy_strategy(legacy_data: Dict[str, Any]) -> Strategy:
        """转换旧版策略数据"""
        return Strategy(
            id=legacy_data.get("id", f"legacy_{uuid.uuid4().hex[:12]}"),
            name=legacy_data.get("name", "Legacy Strategy"),
            description=legacy_data.get("description", ""),
            strategy_type=StrategyType(legacy_data.get("strategy_type", "custom")),
            parameters=legacy_data.get("parameters", {}),
            status=StrategyStatus(legacy_data.get("status", "inactive")),
            is_active=legacy_data.get("is_active", False),
            user_id=legacy_data.get("user_id", 0),
            risk_level=RiskLevel(legacy_data.get("risk_level", "medium")),
            created_at=legacy_data.get("created_at", datetime.now()),
            updated_at=legacy_data.get("updated_at"),
            last_executed=legacy_data.get("last_executed")
        )


class StrategyTemplates:
    """策略模板管理"""

    _templates: Dict[str, CBSCStrategyTemplate] = {}

    @classmethod
    def register_template(cls, template: CBSCStrategyTemplate) -> None:
        """注册模板"""
        cls._templates[template.id] = template

    @classmethod
    def get_template(cls, template_id: str) -> Optional[CBSCStrategyTemplate]:
        """获取模板"""
        return cls._templates.get(template_id)

    @classmethod
    def get_all_templates(cls) -> List[CBSCStrategyTemplate]:
        """获取所有模板"""
        return list(cls._templates.values())

    @classmethod
    def get_templates_by_type(cls, strategy_type: StrategyType) -> List[CBSCStrategyTemplate]:
        """按类型获取模板"""
        return [t for t in cls._templates.values() if t.strategy_type == strategy_type]


# 预定义的CBSC策略模板
RSI_TEMPLATE = CBSCStrategyTemplate(
    id="rsi_strategy_template",
    name="RSI策略模板",
    description="基于相对强弱指数的经典策略",
    strategy_type=StrategyType.DIRECT_RSI,
    category="技术分析",
    default_parameters={
        "rsi_period": 14,
        "rsi_oversold": 30,
        "rsi_overbought": 70,
        "stop_loss": 0.05,
        "take_profit": 0.1
    },
    parameter_constraints={
        "rsi_period": {"min": 2, "max": 100, "type": "integer"},
        "rsi_oversold": {"min": 0, "max": 50, "type": "float"},
        "rsi_overbought": {"min": 50, "max": 100, "type": "float"},
        "stop_loss": {"min": 0.01, "max": 0.5, "type": "float"},
        "take_profit": {"min": 0.02, "max": 1.0, "type": "float"}
    },
    algorithm_description="使用RSI指标识别超买超卖信号",
    market_conditions=["震荡市场", "趋势市场"],
    recommended_timeframes=["1小时", "4小时", "日线"]
)

DUAL_RSI_TEMPLATE = CBSCStrategyTemplate(
    id="dual_rsi_strategy_template",
    name="双RSI策略模板",
    description="使用快慢双RSI系统的增强策略",
    strategy_type=StrategyType.DUAL_RSI,
    category="技术分析",
    default_parameters={
        "fast_rsi_period": 7,
        "slow_rsi_period": 21,
        "signal_threshold": 0.7,
        "stop_loss": 0.04,
        "take_profit": 0.08
    },
    parameter_constraints={
        "fast_rsi_period": {"min": 2, "max": 20, "type": "integer"},
        "slow_rsi_period": {"min": 10, "max": 50, "type": "integer"},
        "signal_threshold": {"min": 0.5, "max": 1.0, "type": "float"},
        "stop_loss": {"min": 0.01, "max": 0.5, "type": "float"},
        "take_profit": {"min": 0.02, "max": 1.0, "type": "float"}
    },
    algorithm_description="结合快速和慢速RSI指标生成更可靠的信号",
    market_conditions=["趋势市场", "高波动性市场"],
    recommended_timeframes=["15分钟", "1小时", "4小时"]
)

# 注册默认模板
StrategyTemplates.register_template(RSI_TEMPLATE)
StrategyTemplates.register_template(DUAL_RSI_TEMPLATE)
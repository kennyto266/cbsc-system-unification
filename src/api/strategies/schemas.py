"""
API响应模型
API Response Schemas

职责：
- 定义API请求和响应格式
- 数据验证和序列化
- API文档生成支持
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field, field_validator
from .models import (
    Strategy, StrategySignal, StrategyPerformance, StrategyExecution,
    StrategyType, StrategyStatus, RiskLevel, SignalType
)

T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """基础响应模型"""
    success: bool = True
    data: Optional[T] = None
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    items: List[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int


# 请求模型
class StrategyCreate(BaseModel):
    """创建策略请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    strategy_type: StrategyType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    template_id: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.MEDIUM

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('策略名称不能为空')
        return v.strip()


class StrategyUpdate(BaseModel):
    """更新策略请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    parameters: Optional[Dict[str, Any]] = None
    status: Optional[StrategyStatus] = None
    is_active: Optional[bool] = None
    risk_level: Optional[RiskLevel] = None


class ExecutionRequest(BaseModel):
    """执行策略请求"""
    strategy_id: str
    execution_mode: str = Field("backtest", pattern="^(backtest|real_time)$")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    data_source: Optional[str] = None
    parameters_override: Optional[Dict[str, Any]] = None


class StrategyControlRequest(BaseModel):
    """策略控制请求"""
    action: str = Field(..., pattern="^(enable|disable|start|stop|pause)$")
    reason: Optional[str] = None
    confirm: bool = False


class BatchStrategyOperation(BaseModel):
    """批量策略操作请求"""
    strategy_ids: List[str] = Field(..., min_length=1, max_length=100)
    operation: str = Field(..., pattern="^(activate|deactivate|delete|execute)$")
    parameters: Optional[Dict[str, Any]] = None
    confirm: bool = False


class UserPreferences(BaseModel):
    """用户偏好设置"""
    default_strategy_type: Optional[StrategyType] = None
    risk_tolerance: RiskLevel = RiskLevel.MEDIUM
    notification_settings: Dict[str, bool] = Field(default_factory=dict)
    dashboard_layout: Dict[str, Any] = Field(default_factory=dict)
    auto_refresh_interval: int = Field(30, ge=5, le=300)


# 响应模型
class StrategyResponse(BaseModel):
    """策略响应"""
    id: str
    name: str
    description: str
    strategy_type: StrategyType
    status: StrategyStatus
    is_active: bool
    user_id: int
    risk_level: RiskLevel
    created_at: datetime
    updated_at: Optional[datetime]
    last_executed: Optional[datetime]
    performance_summary: Optional[Dict[str, float]] = None

    model_config = {"from_attributes": True, "use_enum_values": True}


class StrategyListResponse(PaginatedResponse[StrategyResponse]):
    """策略列表响应"""
    pass


class StrategyDetailResponse(BaseModel):
    """策略详情响应"""
    strategy: StrategyResponse
    recent_signals: List[StrategySignal] = Field(default_factory=list)
    performance: Optional[StrategyPerformance] = None
    execution_history: List[StrategyExecution] = Field(default_factory=list)
    risk_metrics: Optional[Dict[str, float]] = None

    model_config = {"from_attributes": True, "use_enum_values": True}


class ExecutionResponse(BaseModel):
    """执行响应"""
    execution_id: str
    strategy_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    estimated_completion: Optional[datetime]
    progress: float = Field(0.0, ge=0.0, le=1.0)

    model_config = {"from_attributes": True}


class ExecutionStatusResponse(BaseModel):
    """执行状态响应"""
    execution_id: str
    strategy_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    progress: float
    current_step: str
    error_message: Optional[str] = None
    performance_summary: Optional[Dict[str, float]] = None

    model_config = {"from_attributes": True}


class PerformanceMetrics(BaseModel):
    """性能指标"""
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    calmar_ratio: float
    total_trades: int
    profit_trades: int
    avg_profit: float
    avg_loss: float
    daily_pnl: float = 0.0
    last_updated: datetime

    model_config = {"from_attributes": True}


class ExecutionReport(BaseModel):
    """执行报告"""
    execution_id: str
    strategy_id: str
    report_type: str
    generated_at: datetime
    time_range: Dict[str, datetime]
    summary: Dict[str, Any]
    detailed_metrics: PerformanceMetrics
    trade_analysis: Dict[str, Any]
    risk_analysis: Dict[str, Any]
    recommendations: List[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class DashboardResponse(BaseModel):
    """仪表板响应"""
    total_strategies: int
    active_strategies: int
    total_return: float
    daily_pnl: float
    best_performing: Optional[StrategyResponse]
    worst_performing: Optional[StrategyResponse]
    recent_signals: List[StrategySignal] = Field(default_factory=list)
    market_overview: Dict[str, Any] = Field(default_factory=dict)
    performance_chart: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = {"from_attributes": True, "use_enum_values": True}


class ControlResponse(BaseModel):
    """控制响应"""
    strategy_id: str
    success: bool
    action: str
    previous_status: bool
    new_status: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    requires_confirmation: bool = False


class OperationHistoryResponse(BaseModel):
    """操作历史响应"""
    strategy_id: str
    operations: List[Dict[str, Any]]
    total_count: int
    has_more: bool

    model_config = {"from_attributes": True}


class StrategyRecommendations(BaseModel):
    """策略推荐"""
    user_id: int
    recommended_strategies: List[Dict[str, Any]]
    based_on: List[str]  # 推荐依据
    confidence_scores: Dict[str, float]
    last_updated: datetime = Field(default_factory=datetime.now)

    model_config = {"from_attributes": True}


class WebSocketMessage(BaseModel):
    """WebSocket消息"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: Optional[int] = None
    strategy_id: Optional[str] = None


class RealTimeUpdate(BaseModel):
    """实时更新"""
    strategy_updates: List[Dict[str, Any]]
    market_data: Dict[str, Any]
    signals: List[StrategySignal]
    alerts: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {"from_attributes": True, "use_enum_values": True}


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error: Dict[str, Any]
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ValidationError(BaseModel):
    """验证错误"""
    field: str
    message: str
    value: Any


class BadRequestResponse(ErrorResponse):
    """错误请求响应"""
    error: Dict[str, Any] = Field(default_factory=lambda: {
        "code": "BAD_REQUEST",
        "type": "validation_error"
    })
    details: List[ValidationError] = Field(default_factory=list)


class NotFoundResponse(ErrorResponse):
    """未找到响应"""
    error: Dict[str, Any] = Field(default_factory=lambda: {
        "code": "NOT_FOUND",
        "type": "resource_not_found"
    })


class UnauthorizedResponse(ErrorResponse):
    """未授权响应"""
    error: Dict[str, Any] = Field(default_factory=lambda: {
        "code": "UNAUTHORIZED",
        "type": "authentication_failed"
    })


class ForbiddenResponse(ErrorResponse):
    """禁止访问响应"""
    error: Dict[str, Any] = Field(default_factory=lambda: {
        "code": "FORBIDDEN",
        "type": "permission_denied"
    })


class InternalServerErrorResponse(ErrorResponse):
    """内部服务器错误响应"""
    error: Dict[str, Any] = Field(default_factory=lambda: {
        "code": "INTERNAL_SERVER_ERROR",
        "type": "server_error"
    })


# Health check响应
class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    uptime: float
    services: Dict[str, str]
    timestamp: datetime = Field(default_factory=datetime.now)


# Feature flag响应
class FeatureFlagsResponse(BaseModel):
    """功能标志响应"""
    features: Dict[str, bool]
    user_id: int
    last_updated: datetime = Field(default_factory=datetime.now)


# Analytics响应
class AnalyticsDataResponse(BaseModel):
    """分析数据响应"""
    data_points: List[Dict[str, Any]]
    metrics: Dict[str, float]
    time_range: Dict[str, datetime]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}
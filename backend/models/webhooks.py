"""
Webhook模型
"""

from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class WebhookEvent(str, Enum):
    """Webhook事件类型"""
    STRATEGY_CREATED = "strategy.created"
    STRATEGY_UPDATED = "strategy.updated"
    STRATEGY_DELETED = "strategy.deleted"
    STRATEGY_BACKTEST_STARTED = "strategy.backtest.started"
    STRATEGY_BACKTEST_COMPLETED = "strategy.backtest.completed"
    PORTFOLIO_CREATED = "portfolio.created"
    PORTFOLIO_UPDATED = "portfolio.updated"
    PORTFOLIO_DELETED = "portfolio.deleted"
    TRADE_EXECUTED = "trade.executed"
    TRADE_FAILED = "trade.failed"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    API_KEY_CREATED = "api_key.created"
    API_KEY_UPDATED = "api_key.updated"
    API_KEY_DELETED = "api_key.deleted"
    SYSTEM_MAINTENANCE = "system.maintenance"
    SYSTEM_ERROR = "system.error"

class WebhookStatus(str, Enum):
    """Webhook状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    FAILED = "failed"

class WebhookEndpoint(BaseModel):
    """Webhook端点"""
    id: str = Field(..., description="Webhook端点ID")
    url: str = Field(..., description="回调URL")
    description: Optional[str] = Field(None, description="Webhook描述")
    events: List[WebhookEvent] = Field(..., description="订阅的事件类型")
    secret: Optional[str] = Field(None, description="签名验证密钥")
    status: WebhookStatus = Field(default=WebhookStatus.ACTIVE, description="Webhook状态")
    retry_config: Optional[Dict[str, Any]] = Field(None, description="重试配置")
    headers: Optional[Dict[str, str]] = Field(None, description="自定义请求头")
    timeout: int = Field(default=30, description="请求超时时间(秒)")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    last_triggered: Optional[datetime] = Field(None, description="最后触发时间")
    delivery_count: int = Field(default=0, description="投递次数")
    failure_count: int = Field(default=0, description="失败次数")

    @validator('url')
    def validate_url(cls, v):
        if not v.strip():
            raise ValueError('URL不能为空')
        # 基本URL格式验证
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL必须以http://或https://开头')
        return v.strip()

    @validator('events')
    def validate_events(cls, v):
        if not v:
            raise ValueError('至少需要订阅一个事件')
        return v

    @validator('timeout')
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError('超时时间必须大于0')
        if v > 300:  # 最大5分钟
            raise ValueError('超时时间不能超过300秒')
        return v

class WebhookEndpointCreate(BaseModel):
    """创建Webhook端点请求"""
    url: str = Field(..., description="回调URL")
    description: Optional[str] = Field(None, description="Webhook描述")
    events: List[WebhookEvent] = Field(..., description="订阅的事件类型")
    headers: Optional[Dict[str, str]] = Field(None, description="自定义请求头")
    timeout: int = Field(default=30, description="请求超时时间(秒)")

    @validator('url')
    def validate_url(cls, v):
        if not v.strip():
            raise ValueError('URL不能为空')
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL必须以http://或https://开头')
        return v.strip()

    @validator('events')
    def validate_events(cls, v):
        if not v:
            raise ValueError('至少需要订阅一个事件')
        return v

    @validator('timeout')
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError('超时时间必须大于0')
        if v > 300:
            raise ValueError('超时时间不能超过300秒')
        return v

class WebhookEndpointUpdate(BaseModel):
    """更新Webhook端点请求"""
    url: Optional[str] = Field(None, description="回调URL")
    description: Optional[str] = Field(None, description="Webhook描述")
    events: Optional[List[WebhookEvent]] = Field(None, description="订阅的事件类型")
    status: Optional[WebhookStatus] = Field(None, description="Webhook状态")
    headers: Optional[Dict[str, str]] = Field(None, description="自定义请求头")
    timeout: Optional[int] = Field(None, description="请求超时时间(秒)")

    @validator('url')
    def validate_url(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('URL不能为空')
            if not (v.startswith('http://') or v.startswith('https://')):
                raise ValueError('URL必须以http://或https://开头')
            return v.strip()
        return v

    @validator('events')
    def validate_events(cls, v):
        if v is not None and not v:
            raise ValueError('至少需要订阅一个事件')
        return v

    @validator('timeout')
    def validate_timeout(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError('超时时间必须大于0')
            if v > 300:
                raise ValueError('超时时间不能超过300秒')
        return v

class WebhookEndpointResponse(BaseModel):
    """Webhook端点响应"""
    id: str = Field(..., description="Webhook端点ID")
    url: str = Field(..., description="回调URL")
    description: Optional[str] = Field(None, description="Webhook描述")
    events: List[WebhookEvent] = Field(..., description="订阅的事件类型")
    status: WebhookStatus = Field(..., description="Webhook状态")
    timeout: int = Field(..., description="请求超时时间(秒)")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_triggered: Optional[datetime] = Field(None, description="最后触发时间")
    delivery_count: int = Field(..., description="投递次数")
    failure_count: int = Field(..., description="失败次数")

class WebhookDeliveryStatus(str, Enum):
    """Webhook投递状态"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"

class WebhookDelivery(BaseModel):
    """Webhook投递记录"""
    id: str = Field(..., description="投递记录ID")
    endpoint_id: str = Field(..., description="Webhook端点ID")
    event_type: WebhookEvent = Field(..., description="事件类型")
    event_data: Dict[str, Any] = Field(..., description="事件数据")
    status: WebhookDeliveryStatus = Field(..., description="投递状态")
    attempt: int = Field(..., description="尝试次数")
    max_attempts: int = Field(..., description="最大尝试次数")
    response_status: Optional[int] = Field(None, description="HTTP响应状态码")
    response_body: Optional[str] = Field(None, description="响应内容")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    delivered_at: Optional[datetime] = Field(None, description="投递时间")
    next_retry_at: Optional[datetime] = Field(None, description="下次重试时间")

class WebhookEventPayload(BaseModel):
    """Webhook事件负载"""
    event_id: str = Field(..., description="事件ID")
    event_type: WebhookEvent = Field(..., description="事件类型")
    timestamp: datetime = Field(default_factory=datetime.now, description="事件时间戳")
    data: Dict[str, Any] = Field(..., description="事件数据")
    signature: Optional[str] = Field(None, description="事件签名")

class WebhookRetryConfig(BaseModel):
    """Webhook重试配置"""
    max_attempts: int = Field(default=3, description="最大重试次数")
    initial_delay: int = Field(default=1, description="初始延迟(秒)")
    max_delay: int = Field(default=60, description="最大延迟(秒)")
    backoff_multiplier: float = Field(default=2.0, description="退避倍数")
    retryable_status_codes: List[int] = Field(
        default=[500, 502, 503, 504],
        description="可重试的HTTP状态码"
    )

    @validator('max_attempts')
    def validate_max_attempts(cls, v):
        if v < 1:
            raise ValueError('最大重试次数必须大于0')
        if v > 10:
            raise ValueError('最大重试次数不能超过10')
        return v

    @validator('initial_delay')
    def validate_initial_delay(cls, v):
        if v < 1:
            raise ValueError('初始延迟必须大于0秒')
        return v

    @validator('max_delay')
    def validate_max_delay(cls, v):
        if v < 1:
            raise ValueError('最大延迟必须大于0秒')
        return v

    @validator('backoff_multiplier')
    def validate_backoff_multiplier(cls, v):
        if v <= 1.0:
            raise ValueError('退避倍数必须大于1.0')
        return v

class WebhookStats(BaseModel):
    """Webhook统计信息"""
    endpoint_id: str = Field(..., description="Webhook端点ID")
    total_deliveries: int = Field(default=0, description="总投递次数")
    successful_deliveries: int = Field(default=0, description="成功投递次数")
    failed_deliveries: int = Field(default=0, description="失败投递次数")
    pending_deliveries: int = Field(default=0, description="待投递次数")
    success_rate: float = Field(default=0.0, description="成功率")
    average_response_time: float = Field(default=0.0, description="平均响应时间(毫秒)")
    last_delivery_time: Optional[datetime] = Field(None, description="最后投递时间")
    last_success_time: Optional[datetime] = Field(None, description="最后成功时间")
    last_failure_time: Optional[datetime] = Field(None, description="最后失败时间")

class WebhookBatch(BaseModel):
    """批量Webhook操作"""
    endpoint_ids: List[str] = Field(..., description="Webhook端点ID列表")
    action: str = Field(..., description="操作类型")
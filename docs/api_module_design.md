# API模块化结构设计文档

## 概述

本文档设计了一个全新的模块化API架构，解决现有系统中的功能重叠、代码重复和架构混乱问题。新架构遵循单一职责原则，提供清晰的分层结构和高度可维护性。

## 设计原则

### 1. 单一职责原则 (SRP)
- 每个模块只负责一个明确的功能域
- 避免功能交叉和职责混淆

### 2. 依赖倒置原则 (DIP)
- 高层模块不依赖低层模块
- 通过抽象接口定义依赖关系

### 3. 开闭原则 (OCP)
- 对扩展开放，对修改关闭
- 通过插件化架构支持功能扩展

### 4. 接口隔离原则 (ISP)
- 客户端不应依赖不需要的接口
- 提供细粒度的功能接口

## 新架构目录结构

```
src/api/strategies/
├── __init__.py          # 模块路由聚合
├── base.py              # 基础CRUD操作
├── execution.py         # 策略执行引擎
├── personal.py          # 用户个性化功能
├── websocket.py         # WebSocket处理
├── models.py            # 数据模型定义
├── schemas.py           # Pydantic schemas
├── services/            # 业务服务层
│   ├── __init__.py
│   ├── strategy_service.py      # 策略业务服务
│   ├── execution_service.py     # 执行业务服务
│   ├── personal_service.py      # 个性化服务
│   ├── template_service.py      # 模板管理服务
│   └── analytics_service.py     # 分析计算服务
├── repositories/        # 数据访问层
│   ├── __init__.py
│   ├── strategy_repository.py   # 策略数据访问
│   ├── execution_repository.py  # 执行数据访问
│   └── user_repository.py       # 用户数据访问
├── utils/               # 工具模块
│   ├── __init__.py
│   ├── validators.py           # 验证工具
│   ├── permissions.py          # 权限管理
│   ├── cache.py               # 缓存工具
│   └── errors.py              # 错误处理
└── config/              # 配置模块
    ├── __init__.py
    ├── settings.py            # 配置设置
    └── constants.py           # 常量定义
```

## 核心模块设计

### 1. `__init__.py` - 模块路由聚合

```python
"""
策略管理API模块 - 统一路由入口
Strategy Management API Module - Unified Router Entry
"""

from fastapi import APIRouter
from .base import router as base_router
from .execution import router as execution_router
from .personal import router as personal_router
from .websocket import router as websocket_router

# 创建主路由器
router = APIRouter(prefix="/api/strategies", tags=["策略管理"])

# 注册子路由
router.include_router(base_router, prefix="/base", tags=["基础操作"])
router.include_router(execution_router, prefix="/execution", tags=["策略执行"])
router.include_router(personal_router, prefix="/personal", tags=["个性化功能"])
router.include_router(websocket_router, prefix="/ws", tags=["实时通信"])

__all__ = ["router"]
```

### 2. `base.py` - 基础CRUD操作

```python
"""
策略基础CRUD操作
Strategy Base CRUD Operations

职责：
- 策略的增删改查
- 策略列表和详情
- 基础验证和权限检查
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from .services.strategy_service import StrategyService
from .services.template_service import TemplateService
from .utils.permissions import require_strategy_permission
from .utils.validators import validate_strategy_request
from .schemas import (
    StrategyCreate, StrategyUpdate, StrategyResponse,
    StrategyListResponse, StrategyDetailResponse
)

router = APIRouter()

@router.get("/", response_model=StrategyListResponse)
async def list_strategies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    strategy_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    strategy_service: StrategyService = Depends()
):
    """获取策略列表"""
    return await strategy_service.list_strategies(
        page=page, page_size=page_size,
        strategy_type=strategy_type, status=status
    )

@router.post("/", response_model=StrategyResponse, status_code=201)
async def create_strategy(
    request: StrategyCreate,
    strategy_service: StrategyService = Depends()
):
    """创建策略"""
    await validate_strategy_request(request)
    return await strategy_service.create_strategy(request)

@router.get("/{strategy_id}", response_model=StrategyDetailResponse)
async def get_strategy(
    strategy_id: str,
    strategy_service: StrategyService = Depends()
):
    """获取策略详情"""
    return await strategy_service.get_strategy_detail(strategy_id)

@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: str,
    request: StrategyUpdate,
    strategy_service: StrategyService = Depends()
):
    """更新策略"""
    await require_strategy_permission(strategy_id, "update")
    return await strategy_service.update_strategy(strategy_id, request)

@router.delete("/{strategy_id}", status_code=204)
async def delete_strategy(
    strategy_id: str,
    strategy_service: StrategyService = Depends()
):
    """删除策略"""
    await require_strategy_permission(strategy_id, "delete")
    await strategy_service.delete_strategy(strategy_id)
```

### 3. `execution.py` - 策略执行引擎

```python
"""
策略执行引擎
Strategy Execution Engine

职责：
- 策略执行管理
- 执行状态跟踪
- 性能分析和报告
"""

from fastapi import APIRouter, Depends, BackgroundTasks
from .services.execution_service import ExecutionService
from .services.analytics_service import AnalyticsService
from .utils.permissions import require_strategy_permission
from .schemas import (
    ExecutionRequest, ExecutionResponse, ExecutionStatusResponse,
    PerformanceMetrics, ExecutionReport
)

router = APIRouter()

@router.post("/{strategy_id}/execute", response_model=ExecutionResponse)
async def execute_strategy(
    strategy_id: str,
    request: ExecutionRequest,
    background_tasks: BackgroundTasks,
    execution_service: ExecutionService = Depends()
):
    """执行策略"""
    await require_strategy_permission(strategy_id, "execute")
    return await execution_service.execute_strategy(
        strategy_id, request, background_tasks
    )

@router.get("/{strategy_id}/executions/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(
    strategy_id: str,
    execution_id: str,
    execution_service: ExecutionService = Depends()
):
    """获取执行状态"""
    return await execution_service.get_execution_status(execution_id)

@router.post("/{strategy_id}/stop")
async def stop_strategy_execution(
    strategy_id: str,
    execution_id: Optional[str] = None,
    execution_service: ExecutionService = Depends()
):
    """停止策略执行"""
    await require_strategy_permission(strategy_id, "control")
    return await execution_service.stop_execution(strategy_id, execution_id)

@router.get("/{strategy_id}/performance", response_model=PerformanceMetrics)
async def get_strategy_performance(
    strategy_id: str,
    time_range: int = Query(30, ge=1, le=365),
    analytics_service: AnalyticsService = Depends()
):
    """获取策略性能指标"""
    return await analytics_service.calculate_performance_metrics(
        strategy_id, time_range
    )

@router.get("/{strategy_id}/reports", response_model=ExecutionReport)
async def get_strategy_report(
    strategy_id: str,
    report_type: str = Query("summary"),
    analytics_service: AnalyticsService = Depends()
):
    """获取策略报告"""
    return await analytics_service.generate_strategy_report(
        strategy_id, report_type
    )
```

### 4. `personal.py` - 用户个性化功能

```python
"""
用户个性化功能
Personal Features

职责：
- 个人仪表板
- 用户偏好设置
- 策略推荐
- 操作历史
"""

from fastapi import APIRouter, Depends
from .services.personal_service import PersonalService
from .services.strategy_service import StrategyService
from .utils.permissions import get_current_user
from .schemas import (
    DashboardResponse, UserPreferences, StrategyControlRequest,
    OperationHistoryResponse, StrategyRecommendations
)

router = APIRouter()

@router.get("/dashboard", response_model=DashboardResponse)
async def get_personal_dashboard(
    current_user = Depends(get_current_user),
    personal_service: PersonalService = Depends()
):
    """获取个人仪表板"""
    return await personal_service.get_dashboard_data(current_user.id)

@router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user = Depends(get_current_user),
    personal_service: PersonalService = Depends()
):
    """获取用户偏好设置"""
    return await personal_service.get_user_preferences(current_user.id)

@router.put("/preferences")
async def update_user_preferences(
    preferences: UserPreferences,
    current_user = Depends(get_current_user),
    personal_service: PersonalService = Depends()
):
    """更新用户偏好设置"""
    return await personal_service.update_user_preferences(
        current_user.id, preferences
    )

@router.post("/strategies/{strategy_id}/control")
async def control_strategy(
    strategy_id: str,
    request: StrategyControlRequest,
    current_user = Depends(get_current_user),
    personal_service: PersonalService = Depends()
):
    """控制策略"""
    return await personal_service.control_strategy(
        current_user.id, strategy_id, request
    )

@router.get("/strategies/{strategy_id}/history", response_model=OperationHistoryResponse)
async def get_strategy_history(
    strategy_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user = Depends(get_current_user),
    personal_service: PersonalService = Depends()
):
    """获取策略操作历史"""
    return await personal_service.get_strategy_history(
        current_user.id, strategy_id, limit
    )

@router.get("/recommendations", response_model=StrategyRecommendations)
async def get_strategy_recommendations(
    current_user = Depends(get_current_user),
    personal_service: PersonalService = Depends()
):
    """获取策略推荐"""
    return await personal_service.get_strategy_recommendations(current_user.id)
```

### 5. `websocket.py` - WebSocket处理

```python
"""
WebSocket实时通信
WebSocket Real-time Communication

职责：
- 实时数据推送
- 策略状态更新
- 市场数据广播
- 连接管理
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
import asyncio
from .services.websocket_service import WebSocketService
from .utils.permissions import authenticate_websocket

router = APIRouter()

@router.websocket("/realtime/{user_id}")
async def websocket_realtime_endpoint(
    websocket: WebSocket,
    user_id: int,
    websocket_service: WebSocketService = Depends()
):
    """实时数据WebSocket端点"""
    await authenticate_websocket(websocket, user_id)
    await websocket_service.handle_connection(websocket, user_id)

@router.websocket("/strategy/{strategy_id}")
async def websocket_strategy_updates(
    websocket: WebSocket,
    strategy_id: str,
    websocket_service: WebSocketService = Depends()
):
    """策略特定更新WebSocket端点"""
    await authenticate_websocket(websocket, strategy_id=strategy_id)
    await websocket_service.handle_strategy_connection(websocket, strategy_id)
```

## 服务层设计

### 1. `services/strategy_service.py`

```python
"""
策略业务服务
Strategy Business Service

职责：
- 策略业务逻辑
- 数据验证和转换
- 权限检查
- 缓存管理
"""

from typing import List, Optional, Dict, Any
from ..repositories.strategy_repository import StrategyRepository
from ..repositories.user_repository import UserRepository
from ..utils.cache import cache_manager
from ..utils.validators import StrategyValidator
from ..models import Strategy, StrategyType, StrategyStatus
from ..schemas import StrategyCreate, StrategyUpdate, StrategyResponse

class StrategyService:
    def __init__(
        self,
        strategy_repo: StrategyRepository,
        user_repo: UserRepository,
        validator: StrategyValidator
    ):
        self.strategy_repo = strategy_repo
        self.user_repo = user_repo
        self.validator = validator
        self.cache = cache_manager

    async def list_strategies(
        self,
        page: int = 1,
        page_size: int = 20,
        strategy_type: Optional[str] = None,
        status: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取策略列表"""
        # 缓存键
        cache_key = f"strategies:list:{page}:{page_size}:{strategy_type}:{status}:{user_id}"

        # 尝试从缓存获取
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result

        # 从数据库获取
        strategies, total_count = await self.strategy_repo.list_strategies(
            page=page, page_size=page_size,
            strategy_type=strategy_type, status=status,
            user_id=user_id
        )

        result = {
            "strategies": [StrategyResponse.from_orm(s) for s in strategies],
            "total_count": total_count,
            "page": page,
            "page_size": page_size
        }

        # 缓存结果
        await self.cache.set(cache_key, result, ttl=300)  # 5分钟缓存

        return result

    async def create_strategy(self, request: StrategyCreate) -> StrategyResponse:
        """创建策略"""
        # 验证请求
        await self.validator.validate_create_request(request)

        # 检查名称唯一性
        if await self.strategy_repo.name_exists(request.name, request.user_id):
            raise ValueError(f"策略名称已存在: {request.name}")

        # 创建策略对象
        strategy = Strategy(
            name=request.name,
            description=request.description,
            strategy_type=request.strategy_type,
            parameters=request.parameters,
            user_id=request.user_id,
            status=StrategyStatus.INACTIVE,
            is_active=False
        )

        # 保存到数据库
        strategy = await self.strategy_repo.create(strategy)

        # 清除相关缓存
        await self._clear_user_strategy_cache(request.user_id)

        return StrategyResponse.from_orm(strategy)

    async def get_strategy_detail(self, strategy_id: str) -> Dict[str, Any]:
        """获取策略详情"""
        # 缓存键
        cache_key = f"strategy:detail:{strategy_id}"

        # 尝试从缓存获取
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result

        # 从数据库获取
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise ValueError(f"策略不存在: {strategy_id}")

        # 获取相关信息
        recent_signals = await self.strategy_repo.get_recent_signals(strategy_id)
        performance = await self.strategy_repo.get_performance(strategy_id)
        execution_history = await self.strategy_repo.get_execution_history(strategy_id)

        result = {
            "strategy": StrategyResponse.from_orm(strategy),
            "recent_signals": recent_signals,
            "performance": performance,
            "execution_history": execution_history
        }

        # 缓存结果
        await self.cache.set(cache_key, result, ttl=600)  # 10分钟缓存

        return result

    async def update_strategy(
        self,
        strategy_id: str,
        request: StrategyUpdate
    ) -> StrategyResponse:
        """更新策略"""
        # 获取现有策略
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise ValueError(f"策略不存在: {strategy_id}")

        # 验证更新请求
        await self.validator.validate_update_request(request, strategy)

        # 检查名称唯一性（如果更新了名称）
        if request.name and request.name != strategy.name:
            if await self.strategy_repo.name_exists(request.name, strategy.user_id):
                raise ValueError(f"策略名称已存在: {request.name}")

        # 更新字段
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(strategy, field, value)

        # 保存更新
        strategy = await self.strategy_repo.update(strategy)

        # 清除相关缓存
        await self._clear_strategy_cache(strategy_id)
        await self._clear_user_strategy_cache(strategy.user_id)

        return StrategyResponse.from_orm(strategy)

    async def delete_strategy(self, strategy_id: str) -> None:
        """删除策略"""
        # 获取策略信息
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise ValueError(f"策略不存在: {strategy_id}")

        # 检查是否正在运行
        if await self.strategy_repo.is_running(strategy_id):
            raise ValueError("无法删除正在运行的策略")

        # 删除策略及相关数据
        await self.strategy_repo.delete(strategy_id)

        # 清除相关缓存
        await self._clear_strategy_cache(strategy_id)
        await self._clear_user_strategy_cache(strategy.user_id)

    async def _clear_strategy_cache(self, strategy_id: str) -> None:
        """清除策略相关缓存"""
        patterns = [
            f"strategy:detail:{strategy_id}",
            f"strategy:performance:{strategy_id}",
            f"strategy:signals:{strategy_id}"
        ]
        for pattern in patterns:
            await self.cache.delete(pattern)

    async def _clear_user_strategy_cache(self, user_id: int) -> None:
        """清除用户策略相关缓存"""
        pattern = f"strategies:list:*:*:*:*:{user_id}"
        await self.cache.delete_pattern(pattern)
```

## 数据模型统一设计

### `models.py` - 核心数据模型

```python
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

class Strategy(BaseModel):
    """策略模型"""
    id: str
    name: str
    description: str
    strategy_type: StrategyType
    parameters: Dict[str, Any]
    status: StrategyStatus
    is_active: bool
    user_id: int
    risk_level: RiskLevel = RiskLevel.MEDIUM
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_executed: Optional[datetime] = None

    class Config:
        orm_mode = True

class StrategySignal(BaseModel):
    """策略信号"""
    signal_id: str
    strategy_id: str
    strategy_type: StrategyType
    signal_type: str  # BUY, SELL, HOLD
    strength: float
    confidence: float
    timestamp: datetime
    market_data: Dict[str, Any]
    parameters: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True

class StrategyPerformance(BaseModel):
    """策略性能"""
    strategy_id: str
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

    class Config:
        orm_mode = True

class StrategyExecution(BaseModel):
    """策略执行"""
    execution_id: str
    strategy_id: str
    status: str  # running, completed, failed, stopped
    start_time: datetime
    end_time: Optional[datetime] = None
    execution_mode: str  # backtest, real_time
    data_source: Optional[str] = None
    signals: List[StrategySignal] = []
    performance: Optional[StrategyPerformance] = None
    error_message: Optional[str] = None
    execution_metadata: Dict[str, Any] = {}

    class Config:
        orm_mode = True

class User(BaseModel):
    """用户模型"""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True

class StrategyTemplate(BaseModel):
    """策略模板"""
    id: str
    name: str
    description: str
    strategy_type: StrategyType
    category: str
    default_parameters: Dict[str, Any]
    parameter_constraints: Dict[str, Any]
    is_system_template: bool = True
    created_by: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True
```

### `schemas.py` - API响应模型

```python
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
from pydantic import BaseModel, Field, validator
from .models import Strategy, StrategySignal, StrategyPerformance, StrategyExecution

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
    parameters: Dict[str, Any]
    template_id: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.MEDIUM

    @validator('name')
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
    execution_mode: str = Field("backtest", regex="^(backtest|real_time)$")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    data_source: Optional[str] = None
    parameters_override: Optional[Dict[str, Any]] = None

# 响应模型
class StrategyResponse(BaseModel):
    """策略响应"""
    id: str
    name: str
    description: str
    strategy_type: StrategyType
    status: StrategyStatus
    is_active: bool
    risk_level: RiskLevel
    created_at: datetime
    updated_at: Optional[datetime]
    last_executed: Optional[datetime]
    performance_summary: Optional[Dict[str, float]] = None

    class Config:
        orm_mode = True

class StrategyDetailResponse(BaseModel):
    """策略详情响应"""
    strategy: StrategyResponse
    recent_signals: List[StrategySignal]
    performance: Optional[StrategyPerformance]
    execution_history: List[StrategyExecution]
    risk_metrics: Optional[Dict[str, float]]

    class Config:
        orm_mode = True

class ExecutionResponse(BaseModel):
    """执行响应"""
    execution_id: str
    strategy_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    estimated_completion: Optional[datetime]
    progress: float = Field(0.0, ge=0.0, le=1.0)

    class Config:
        orm_mode = True

class DashboardResponse(BaseModel):
    """仪表板响应"""
    total_strategies: int
    active_strategies: int
    total_return: float
    daily_pnl: float
    best_performing: Optional[StrategyResponse]
    worst_performing: Optional[StrategyResponse]
    recent_signals: List[StrategySignal]
    market_overview: Dict[str, Any]
    performance_chart: List[Dict[str, Any]]

class UserPreferences(BaseModel):
    """用户偏好设置"""
    default_strategy_type: Optional[StrategyType] = None
    risk_tolerance: RiskLevel = RiskLevel.MEDIUM
    notification_settings: Dict[str, bool]
    dashboard_layout: Dict[str, Any]
    auto_refresh_interval: int = Field(30, ge=5, le=300)

class StrategyControlRequest(BaseModel):
    """策略控制请求"""
    action: str = Field(..., regex="^(enable|disable|start|stop|pause)$")
    reason: Optional[str] = None
    confirm: bool = False

class ControlResponse(BaseModel):
    """控制响应"""
    strategy_id: str
    success: bool
    action: str
    previous_status: bool
    new_status: bool
    message: str
    timestamp: datetime
    requires_confirmation: bool = False
```

## 工具模块设计

### `utils/permissions.py` - 权限管理

```python
"""
权限管理工具
Permission Management Utilities

职责：
- 用户身份验证
- 策略权限检查
- 操作权限验证
"""

from fastapi import Depends, HTTPException, status
from typing import Optional, Callable
from functools import wraps
from ..repositories.user_repository import UserRepository

class PermissionManager:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_current_user(self) -> User:
        """获取当前用户"""
        # 实现JWT token验证
        pass

    async def require_authentication(self) -> User:
        """要求用户认证"""
        user = await self.get_current_user()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未授权访问"
            )
        return user

    async def check_strategy_permission(
        self,
        strategy_id: str,
        user: User,
        action: str
    ) -> bool:
        """检查策略权限"""
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            return False

        # 检查是否为策略所有者
        if strategy.user_id != user.id:
            # 检查是否为管理员
            if not user.is_admin:
                return False

        # 检查操作权限
        if action == "delete" and strategy.is_active:
            return False

        return True

# 依赖注入函数
async def get_current_user() -> User:
    """获取当前用户依赖"""
    permission_manager = get_permission_manager()
    return await permission_manager.require_authentication()

async def require_strategy_permission(
    strategy_id: str,
    action: str
) -> None:
    """策略权限检查装饰器"""
    async def checker(user: User = Depends(get_current_user)):
        permission_manager = get_permission_manager()
        has_permission = await permission_manager.check_strategy_permission(
            strategy_id, user, action
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权限执行操作: {action}"
            )
        return user
    return checker
```

### `utils/cache.py` - 缓存管理

```python
"""
缓存管理工具
Cache Management Utilities

职责：
- 缓存操作封装
- 缓存策略管理
- 缓存失效处理
"""

import json
import redis.asyncio as redis
from typing import Any, Optional, List, Dict
from datetime import timedelta

class CacheManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.default_ttl = 300  # 5分钟

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            # 缓存错误不影响主流程
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            await self.redis.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的所有缓存"""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            return 0

    async def invalidate_user_cache(self, user_id: int) -> None:
        """清除用户相关缓存"""
        patterns = [
            f"strategies:list:*:*:*:*:{user_id}",
            f"dashboard:*:{user_id}",
            f"preferences:{user_id}"
        ]
        for pattern in patterns:
            await self.delete_pattern(pattern)

    async def invalidate_strategy_cache(self, strategy_id: str) -> None:
        """清除策略相关缓存"""
        patterns = [
            f"strategy:*:{strategy_id}",
            f"execution:*:{strategy_id}",
            f"performance:*:{strategy_id}"
        ]
        for pattern in patterns:
            await self.delete_pattern(pattern)

# 全局缓存管理器实例
cache_manager = CacheManager("redis://localhost:6379/0")
```

## 迁移策略

### 阶段1: 基础架构搭建
1. 创建新的目录结构
2. 实现核心服务层
3. 统一数据模型
4. 建立工具模块

### 阶段2: 功能迁移
1. 迁移基础CRUD到`base.py`
2. 迁移执行功能到`execution.py`
3. 迁移个性化功能到`personal.py`
4. 迁移WebSocket功能到`websocket.py`

### 阶段3: 路由整合
1. 更新主路由器
2. 实现向后兼容
3. 添加版本控制
4. 更新API文档

### 阶段4: 清理和优化
1. 删除旧代码
2. 性能优化
3. 测试完善
4. 文档更新

## 优势总结

### 1. 清晰的职责分离
- 每个模块只负责明确的功能域
- 服务层与数据层分离
- 业务逻辑与API端点分离

### 2. 高度可维护性
- 模块化设计便于维护
- 统一的代码风格和结构
- 完善的错误处理机制

### 3. 良好的扩展性
- 插件化架构支持功能扩展
- 清晰的接口定义
- 松耦合的模块设计

### 4. 提升开发效率
- 减少代码重复
- 统一的开发模式
- 完善的工具支持

### 5. 增强测试性
- 模块化便于单元测试
- 依赖注入支持mock
- 清晰的接口定义

---

*设计文档生成时间: 2025-12-10*
*设计人员: Claude Code Assistant*
*版本: 1.0*
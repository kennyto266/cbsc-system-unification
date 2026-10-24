# API模块设计文档
## API Module Design Document

## 目录
1. [概述](#概述)
2. [架构设计](#架构设计)
3. [分层架构](#分层架构)
4. [依赖注入设计](#依赖注入设计)
5. [统一数据模型](#统一数据模型)
6. [权限控制设计](#权限控制设计)
7. [缓存策略设计](#缓存策略设计)
8. [WebSocket集成设计](#websocket集成设计)
9. [模块结构图](#模块结构图)
10. [API路由设计](#api路由设计)
11. [设计原则](#设计原则)
12. [实施建议](#实施建议)

## 概述

基于对现有代码的分析，设计一个统一、可扩展的API模块架构。通过分析发现，`src/api/strategies/`目录已经实现了一个较好的统一架构基础，但仍需进一步完善和优化。

**架构现状**：
- ✅ **基础架构已实现**：`src/api/strategies/`包含模块化的目录结构
- ✅ **服务层分离**：execution_service.py、personal_service.py等业务服务已实现
- ✅ **数据模型统一**：models.py提供了标准化数据结构
- ✅ **缓存管理**：cache_manager.py实现了统一的缓存策略
- ✅ **WebSocket支持**：websocket_service.py提供实时通信能力

**需要完善的部分**：
- 🔧 Repository层需要进一步抽象和统一
- 🔧 Controller层需要规范化
- 🔧 权限控制系统需要完善
- 🔧 API响应格式需要标准化
- 🔧 错误处理机制需要统一

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        API Gateway                          │
│                    (统一入口点 /api/v1)                      │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                     Controller Layer                        │
│  (处理HTTP请求，参数验证，响应序列化)                        │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Strategy      │   Execution     │      WebSocket          │
│   Controller    │   Controller    │      Controller         │
└─────────────────┴─────────────────┴─────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                          │
│    (业务逻辑实现，事务管理，缓存协调)                        │
├─────────────────┬─────────────────┬─────────────────────────┤
│  Strategy       │   Execution     │      Personal           │
│  Service        │   Service       │      Service            │
└─────────────────┴─────────────────┴─────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                     Repository Layer                        │
│      (数据访问抽象，ORM操作，查询优化)                       │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Strategy      │   Execution     │      Cache              │
│   Repository    │   Repository    │      Repository         │
└─────────────────┴─────────────────┴─────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure                           │
│  (数据库、缓存、消息队列、监控等基础服务)                    │
└─────────────────────────────────────────────────────────────┘
```

### 核心设计理念

1. **分层解耦**：清晰的职责分离，每层只处理自己的逻辑
2. **依赖注入**：通过DI容器管理依赖，提高可测试性
3. **统一接口**：标准化的CRUD操作和业务接口
4. **插件化设计**：支持功能模块的独立开发和部署
5. **异步优先**：充分利用异步编程提高并发性能

## 分层架构

### 1. Controller层 (控制器层)

**职责**：
- 接收和验证HTTP请求
- 调用Service层处理业务逻辑
- 序列化响应数据
- 处理错误和异常

**设计模式**：
```python
# src/api/strategies/controllers/base_controller.py
from abc import ABC
from typing import TypeVar, Generic, Type, List
from fastapi import APIRouter, Depends, Query
from ..services.base_service import BaseService
from ..schemas import BaseResponse, PaginatedResponse

T = TypeVar('T')  # Model Type
C = TypeVar('C')  # Create Schema Type
U = TypeVar('U')  # Update Schema Type
R = TypeVar('R')  # Response Schema Type

class BaseController(Generic[T, C, U, R], ABC):
    """基础控制器"""

    def __init__(self, service: BaseService, router: APIRouter):
        self.service = service
        self.router = router
        self._register_routes()

    def _register_routes(self):
        """注册标准CRUD路由"""
        self.router.add_api_route(
            "/",
            self.list_items,
            methods=["GET"],
            response_model=PaginatedResponse[R]
        )
        self.router.add_api_route(
            "/",
            self.create_item,
            methods=["POST"],
            response_model=BaseResponse[R]
        )
        self.router.add_api_route(
            "/{item_id}",
            self.get_item,
            methods=["GET"],
            response_model=BaseResponse[R]
        )
        self.router.add_api_route(
            "/{item_id}",
            self.update_item,
            methods=["PUT"],
            response_model=BaseResponse[R]
        )
        self.router.add_api_route(
            "/{item_id}",
            self.delete_item,
            methods=["DELETE"]
        )
```

### 2. Service层 (服务层)

**职责**：
- 实现核心业务逻辑
- 协调多个Repository
- 管理事务
- 缓存策略实施
- 业务规则验证

**基础服务类**：
```python
# src/api/strategies/services/base_service.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from ..repositories.base_repository import BaseRepository
from ..utils.cache import CacheManager
from ..utils.events import EventBus
from ..utils.permissions import PermissionChecker

class BaseService(Generic[ModelType], ABC):
    """基础服务类"""

    def __init__(
        self,
        repository: BaseRepository,
        cache_manager: CacheManager,
        event_bus: EventBus,
        permission_checker: PermissionChecker
    ):
        self.repo = repository
        self.cache = cache_manager
        self.events = event_bus
        self.permission = permission_checker

    async def get_by_id(self, item_id: str) -> Optional[ModelType]:
        """根据ID获取项"""
        # 先查缓存
        cache_key = f"{self.__class__.__name__}:{item_id}"
        cached_item = await self.cache.get(cache_key)
        if cached_item:
            return cached_item

        # 查数据库
        item = await self.repo.get_by_id(item_id)
        if item:
            # 更新缓存
            await self.cache.set(cache_key, item, ttl=300)

        return item

    async def create(self, item_data: Dict[str, Any]) -> ModelType:
        """创建项"""
        # 权限检查
        await self.permission.check_create_permission(item_data)

        # 创建
        item = await self.repo.create(item_data)

        # 清除相关缓存
        await self._clear_list_cache()

        # 发布事件
        await self.events.emit("item_created", {
            "type": self.__class__.__name__,
            "item_id": item.id
        })

        return item

    async def update(self, item_id: str, update_data: Dict[str, Any]) -> ModelType:
        """更新项"""
        # 权限检查
        await self.permission.check_update_permission(item_id)

        # 更新
        item = await self.repo.update(item_id, update_data)

        # 清除缓存
        cache_key = f"{self.__class__.__name__}:{item_id}"
        await self.cache.delete(cache_key)
        await self._clear_list_cache()

        # 发布事件
        await self.events.emit("item_updated", {
            "type": self.__class__.__name__,
            "item_id": item_id
        })

        return item
```

### 3. Repository层 (仓储层)

**职责**：
- 抽象数据访问
- ORM操作封装
- 查询优化
- 数据库连接管理

**基础仓储类**：
```python
# src/api/strategies/repositories/base_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TypeVar
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

ModelType = TypeVar('ModelType')

class BaseRepository(Generic[ModelType], ABC):
    """基础仓储类"""

    def __init__(self, db_session: Session, model_class: Type[ModelType]):
        self.db = db_session
        self.model_class = model_class

    async def create(self, obj_data: Dict[str, Any]) -> ModelType:
        """创建记录"""
        db_obj = self.model_class(**obj_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get_by_id(self, item_id: str) -> Optional[ModelType]:
        """根据ID获取记录"""
        stmt = select(self.model_class).where(
            self.model_class.id == item_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """获取多条记录"""
        stmt = select(self.model_class)

        # 应用过滤器
        if filters:
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    stmt = stmt.where(getattr(self.model_class, field) == value)

        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
```

## 依赖注入设计

使用FastAPI的依赖注入系统，结合自定义DI容器实现更灵活的管理。

```python
# src/api/strategies/container.py
from dependency_injector import containers, providers
from ..services import StrategyService, ExecutionService
from ..repositories import StrategyRepository, ExecutionRepository
from ..utils import CacheManager, EventBus, PermissionChecker

class Container(containers.DeclarativeContainer):
    """依赖注入容器"""

    # Configuration
    config = providers.Configuration()

    # Database
    db = providers.Singleton(create_db_session, config.db.url)

    # Cache
    cache = providers.Singleton(
        CacheManager,
        redis_url=config.redis.url
    )

    # Event Bus
    events = providers.Singleton(EventBus)

    # Permission Checker
    permissions = providers.Singleton(PermissionChecker)

    # Repositories
    strategy_repo = providers.Factory(
        StrategyRepository,
        db_session=db,
        model_class=StrategyModel
    )

    execution_repo = providers.Factory(
        ExecutionRepository,
        db_session=db,
        model_class=ExecutionModel
    )

    # Services
    strategy_service = providers.Factory(
        StrategyService,
        repository=strategy_repo,
        cache_manager=cache,
        event_bus=events,
        permission_checker=permissions
    )

    execution_service = providers.Factory(
        ExecutionService,
        repository=execution_repo,
        cache_manager=cache,
        event_bus=events,
        permission_checker=permissions
    )

# 初始化容器
container = Container()
container.config.from_yaml("config.yaml")
```

## 统一数据模型

### 1. 基础模型类

```python
# src/api/strategies/models/base.py
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class BaseModel(Base):
    """基础模型类"""
    __abstract__ = True

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    def soft_delete(self):
        """软删除"""
        self.is_deleted = True
        self.updated_at = datetime.utcnow()
```

### 2. 统一响应模型

```python
# src/api/strategies/schemas/responses.py
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, List
from datetime import datetime

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    """基础响应模型"""
    success: bool = True
    data: Optional[T] = None
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None

class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    error_code: str
    message: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

## 权限控制设计

### 1. RBAC权限模型

```python
# src/api/strategies/models/permissions.py
from sqlalchemy import Column, String, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship

class Role(BaseModel):
    """角色表"""
    __tablename__ = "roles"

    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    permissions = Column(JSON)  # 权限列表
    is_system_role = Column(Boolean, default=False)

    users = relationship("UserRole", back_populates="role")

class Permission(BaseModel):
    """权限表"""
    __tablename__ = "permissions"

    name = Column(String(100), unique=True, nullable=False)
    resource = Column(String(50), nullable=False)  # 资源类型
    action = Column(String(50), nullable=False)    # 操作类型
    description = Column(String(200))

class UserRole(BaseModel):
    """用户角色关联表"""
    __tablename__ = "user_roles"

    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    role_id = Column(String(36), ForeignKey("roles.id"), primary_key=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(String(36), ForeignKey("users.id"))

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")
```

### 2. 权限装饰器

```python
# src/api/strategies/utils/decorators.py
from functools import wraps
from fastapi import HTTPException, Depends
from .permissions import PermissionChecker

def require_permission(resource: str, action: str):
    """权限检查装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=401, detail="未认证")

            # 检查权限
            permission_checker = PermissionChecker()
            has_permission = await permission_checker.check_user_permission(
                current_user.id, resource, action
            )

            if not has_permission:
                raise HTTPException(
                    status_code=403,
                    detail=f"没有权限执行 {action} 操作"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@require_permission("strategy", "create")
async def create_strategy(
    request: StrategyCreate,
    current_user: User = Depends(get_current_user)
):
    """创建策略"""
    pass
```

## 缓存策略设计

### 1. 多级缓存架构

```python
# src/api/strategies/utils/cache.py
from abc import ABC, abstractmethod
from typing import Any, Optional
import redis
import json
from datetime import timedelta

class CacheBackend(ABC):
    """缓存后端接口"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass

    @abstractmethod
    async def clear_pattern(self, pattern: str) -> None:
        pass

class RedisBackend(CacheBackend):
    """Redis缓存后端"""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def get(self, key: str) -> Optional[Any]:
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        serialized = json.dumps(value, default=str)
        if ttl:
            await self.redis.setex(key, ttl, serialized)
        else:
            await self.redis.set(key, serialized)

class CacheManager:
    """缓存管理器"""

    def __init__(self, backend: CacheBackend):
        self.backend = backend
        self.local_cache = {}  # L1缓存（内存）
        self.stats = {
            "hits": 0,
            "misses": 0
        }

    async def get(self, key: str) -> Optional[Any]:
        # L1缓存检查
        if key in self.local_cache:
            self.stats["hits"] += 1
            return self.local_cache[key]

        # L2缓存检查
        value = await self.backend.get(key)
        if value:
            self.stats["hits"] += 1
            # 更新L1缓存
            self.local_cache[key] = value
            return value

        self.stats["misses"] += 1
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        l1_ttl: int = 60  # L1缓存默认60秒
    ) -> None:
        # 更新L1缓存
        self.local_cache[key] = value

        # 更新L2缓存
        await self.backend.set(key, value, ttl)

    async def invalidate(self, pattern: str) -> None:
        """清除缓存"""
        # 清除L1缓存
        keys_to_remove = [
            k for k in self.local_cache.keys()
            if self._match_pattern(k, pattern)
        ]
        for key in keys_to_remove:
            del self.local_cache[key]

        # 清除L2缓存
        await self.backend.clear_pattern(pattern)
```

### 2. 缓存策略配置

```python
# src/api/strategies/config/cache.py
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class CacheConfig:
    """缓存配置"""
    # 默认TTL（秒）
    default_ttl: int = 300

    # 特定资源的TTL配置
    ttl_config: Dict[str, int] = None

    # 缓存键前缀
    key_prefix: str = "cbsc_api"

    # 是否启用L1缓存
    enable_l1_cache: bool = True

    # L1缓存最大条目数
    l1_max_size: int = 1000

    def __post_init__(self):
        if self.ttl_config is None:
            self.ttl_config = {
                "strategy_list": 60,       # 策略列表缓存1分钟
                "strategy_detail": 300,    # 策略详情缓存5分钟
                "execution_status": 30,    # 执行状态缓存30秒
                "performance_metrics": 600, # 性能指标缓存10分钟
                "user_permissions": 1800,  # 用户权限缓存30分钟
            }
```

## WebSocket集成设计

### 1. 连接管理

```python
# src/api/strategies/websocket/manager.py
from typing import Dict, List, Set
from fastapi import WebSocket
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # 活跃连接 {user_id: {connection_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

        # 订阅关系 {channel: {user_ids}}
        self.subscriptions: Dict[str, Set[str]] = {}

        # 连接元数据
        self.connection_metadata: Dict[str, Dict] = {}

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        connection_id: str
    ):
        """建立连接"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}

        self.active_connections[user_id][connection_id] = websocket

        # 保存连接元数据
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "subscriptions": set()
        }

    def disconnect(self, user_id: str, connection_id: str):
        """断开连接"""
        if user_id in self.active_connections:
            self.active_connections[user_id].pop(connection_id, None)

            # 如果用户没有其他连接，清理订阅
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                self._cleanup_user_subscriptions(user_id)

        # 清理元数据
        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]

    async def subscribe(self, user_id: str, connection_id: str, channel: str):
        """订阅频道"""
        # 更新连接元数据
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["subscriptions"].add(channel)

        # 更新订阅关系
        if channel not in self.subscriptions:
            self.subscriptions[channel] = set()
        self.subscriptions[channel].add(user_id)

    async def unsubscribe(self, user_id: str, connection_id: str, channel: str):
        """取消订阅"""
        # 更新连接元数据
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["subscriptions"].discard(channel)

        # 更新订阅关系
        if channel in self.subscriptions:
            self.subscriptions[channel].discard(user_id)

            # 如果没有订阅者，删除频道
            if not self.subscriptions[channel]:
                del self.subscriptions[channel]

    async def broadcast_to_channel(self, channel: str, message: dict):
        """向频道广播消息"""
        if channel not in self.subscriptions:
            return

        # 构建消息
        message_data = {
            "type": "broadcast",
            "channel": channel,
            "data": message,
            "timestamp": datetime.utcnow().isoformat()
        }

        # 发送给所有订阅用户
        for user_id in self.subscriptions[channel]:
            await self.send_to_user(user_id, message_data)

    async def send_to_user(self, user_id: str, message: dict):
        """发送消息给特定用户"""
        if user_id not in self.active_connections:
            return

        message_json = json.dumps(message, default=str)

        # 发送给用户的所有连接
        connections_to_remove = []
        for connection_id, websocket in self.active_connections[user_id].items():
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                # 连接已断开，标记清理
                connections_to_remove.append(connection_id)

        # 清理无效连接
        for connection_id in connections_to_remove:
            self.disconnect(user_id, connection_id)
```

### 2. 消息处理

```python
# src/api/strategies/websocket/handlers.py
from typing import Dict, Any
from ..events import EventBus
from ..utils.auth import authenticate_websocket

class WebSocketHandler:
    """WebSocket消息处理器"""

    def __init__(self, manager: ConnectionManager, event_bus: EventBus):
        self.manager = manager
        self.event_bus = event_bus
        self.handlers = {
            "subscribe": self._handle_subscribe,
            "unsubscribe": self._handle_unsubscribe,
            "ping": self._handle_ping,
            "strategy_control": self._handle_strategy_control,
        }

        # 注册事件监听
        self._register_event_handlers()

    async def handle_message(
        self,
        websocket: WebSocket,
        user_id: str,
        connection_id: str,
        message: Dict[str, Any]
    ):
        """处理接收到的消息"""
        message_type = message.get("type")

        if message_type in self.handlers:
            await self.handlers[message_type](
                websocket, user_id, connection_id, message
            )
        else:
            await self._send_error(
                websocket,
                f"未知消息类型: {message_type}"
            )

    async def _handle_subscribe(
        self,
        websocket: WebSocket,
        user_id: str,
        connection_id: str,
        message: Dict[str, Any]
    ):
        """处理订阅请求"""
        channel = message.get("channel")
        if not channel:
            await self._send_error(websocket, "订阅频道不能为空")
            return

        # 验证权限
        if not await self._check_subscription_permission(user_id, channel):
            await self._send_error(websocket, "没有权限订阅该频道")
            return

        await self.manager.subscribe(user_id, connection_id, channel)

        await websocket.send_json({
            "type": "subscribe_success",
            "channel": channel
        })

    async def _handle_strategy_control(
        self,
        websocket: WebSocket,
        user_id: str,
        connection_id: str,
        message: Dict[str, Any]
    ):
        """处理策略控制请求"""
        strategy_id = message.get("strategy_id")
        action = message.get("action")

        # 验证权限
        has_permission = await self._check_strategy_permission(
            user_id, strategy_id, action
        )

        if not has_permission:
            await self._send_error(websocket, "没有权限执行该操作")
            return

        # 发布策略控制事件
        await self.event_bus.emit("strategy_control", {
            "strategy_id": strategy_id,
            "action": action,
            "user_id": user_id,
            "connection_id": connection_id
        })
```

## 模块结构图

```
src/api/strategies/
├── __init__.py                 # 模块入口，路由注册
├── controllers/                # 控制器层
│   ├── __init__.py
│   ├── base_controller.py     # 基础控制器
│   ├── strategy_controller.py # 策略控制器
│   ├── execution_controller.py# 执行控制器
│   ├── personal_controller.py # 个性化功能控制器
│   └── websocket_controller.py# WebSocket控制器
├── services/                   # 服务层
│   ├── __init__.py
│   ├── base_service.py        # 基础服务类
│   ├── strategy_service.py    # 策略服务
│   ├── execution_service.py   # 执行服务
│   ├── personal_service.py    # 个性化服务
│   ├── websocket_service.py   # WebSocket服务
│   └── business/              # 业务服务
│       ├── user_service.py
│       ├── permission_service.py
│       └── audit_service.py
├── repositories/               # 仓储层
│   ├── __init__.py
│   ├── base_repository.py     # 基础仓储
│   ├── strategy_repository.py # 策略仓储
│   ├── execution_repository.py# 执行仓储
│   └── cache_repository.py    # 缓存仓储
├── models/                     # 数据模型
│   ├── __init__.py
│   ├── base.py               # 基础模型
│   ├── strategy.py           # 策略模型
│   ├── execution.py          # 执行模型
│   ├── user.py               # 用户模型
│   └── permissions.py        # 权限模型
├── schemas/                    # API模式
│   ├── __init__.py
│   ├── requests/             # 请求模式
│   │   ├── strategy.py
│   │   ├── execution.py
│   │   └── personal.py
│   ├── responses/            # 响应模式
│   │   ├── base.py
│   │   ├── strategy.py
│   │   └── execution.py
│   └── common.py             # 通用模式
├── utils/                      # 工具模块
│   ├── __init__.py
│   ├── auth.py               # 认证工具
│   ├── permissions.py        # 权限工具
│   ├── cache.py              # 缓存工具
│   ├── validators.py         # 验证器
│   ├── errors.py             # 错误处理
│   └── decorators.py         # 装饰器
├── config/                     # 配置
│   ├── __init__.py
│   ├── settings.py           # 设置
│   ├── cache.py              # 缓存配置
│   └── database.py           # 数据库配置
├── websocket/                  # WebSocket
│   ├── __init__.py
│   ├── manager.py            # 连接管理
│   ├── handlers.py           # 消息处理
│   └── events.py             # 事件定义
└── database/                   # 数据库
    ├── __init__.py
    ├── migrations/           # 数据库迁移
    ├── seeds/               # 种子数据
    └── views/               # 视图定义
```

## API路由设计

### 1. 版本化路由

```
/api/v1/
├── strategies/                 # 策略管理
│   ├── GET    /              # 获取策略列表
│   ├── POST   /              # 创建策略
│   ├── GET    /{id}          # 获取策略详情
│   ├── PUT    /{id}          # 更新策略
│   ├── DELETE /{id}          # 删除策略
│   ├── POST   /{id}/execute  # 执行策略
│   ├── POST   /{id}/stop     # 停止策略
│   ├── GET    /{id}/status   # 获取策略状态
│   ├── GET    /{id}/metrics  # 获取性能指标
│   ├── POST   /{id}/clone    # 克隆策略
│   └── POST   /batch         # 批量操作
├── executions/                # 执行管理
│   ├── GET    /              # 获取执行历史
│   ├── GET    /{id}          # 获取执行详情
│   ├── POST   /{id}/cancel   # 取消执行
│   └── GET    /{id}/logs     # 获取执行日志
├── templates/                 # 策略模板
│   ├── GET    /              # 获取模板列表
│   ├── GET    /{id}          # 获取模板详情
│   └── POST   /{id}/use      # 使用模板创建策略
├── personal/                  # 个性化功能
│   ├── GET    /preferences   # 获取用户偏好
│   ├── PUT    /preferences   # 更新用户偏好
│   ├── GET    /dashboard     # 获取仪表板数据
│   └── GET    /recommendations # 获取推荐
├── users/                     # 用户管理
│   ├── GET    /profile       # 获取用户资料
│   ├── PUT    /profile       # 更新用户资料
│   ├── GET    /permissions   # 获取用户权限
│   └── GET    /activity      # 获取用户活动
└── ws/                        # WebSocket端点
    ├── /strategies           # 策略实时更新
    ├── /executions           # 执行实时状态
    └── /notifications        # 通知推送
```

### 2. 路由注册

```python
# src/api/strategies/router.py
from fastapi import APIRouter
from .controllers import (
    StrategyController,
    ExecutionController,
    PersonalController,
    WebSocketController
)

# 创建主路由器
api_router = APIRouter(prefix="/api/v1")

# 注册模块路由
api_router.include_router(
    StrategyController().router,
    prefix="/strategies",
    tags=["strategies"]
)

api_router.include_router(
    ExecutionController().router,
    prefix="/executions",
    tags=["executions"]
)

api_router.include_router(
    PersonalController().router,
    prefix="/personal",
    tags=["personal"]
)

api_router.include_router(
    WebSocketController().router,
    prefix="/ws",
    tags=["websocket"]
)
```

## 设计原则

### 1. 单一职责原则 (SRP)

每个类和模块都有明确的单一职责：

- **Controller**: 只负责HTTP请求处理
- **Service**: 只负责业务逻辑实现
- **Repository**: 只负责数据访问
- **Model**: 只负责数据结构定义

### 2. 开闭原则 (OCP)

系统对扩展开放，对修改关闭：

```python
# 示例：策略类型扩展
class StrategyTypeRegistry:
    """策略类型注册表"""

    def __init__(self):
        self._strategies = {}

    def register(self, strategy_type: str, strategy_class: Type[BaseStrategy]):
        """注册新的策略类型"""
        self._strategies[strategy_type] = strategy_class

    def get_strategy(self, strategy_type: str) -> Type[BaseStrategy]:
        """获取策略类"""
        if strategy_type not in self._strategies:
            raise ValueError(f"未知的策略类型: {strategy_type}")
        return self._strategies[strategy_type]

# 扩展新策略类型不需要修改现有代码
registry = StrategyTypeRegistry()
registry.register("rsi", RSIStrategy)
registry.register("macd", MACDStrategy)
registry.register("custom", CustomStrategy)
```

### 3. 依赖倒置原则 (DIP)

高层模块不依赖低层模块，都依赖于抽象：

```python
# 抽象接口
class CacheInterface(Protocol):
    async def get(self, key: str) -> Optional[Any]: ...
    async def set(self, key: str, value: Any, ttl: Optional[int] = None): ...

# 高层模块依赖抽象
class ServiceLayer:
    def __init__(self, cache: CacheInterface):
        self.cache = cache  # 依赖抽象，不是具体实现

# 可以注入不同的实现
redis_cache = RedisCache()
memory_cache = MemoryCache()
service1 = ServiceLayer(redis_cache)
service2 = ServiceLayer(memory_cache)
```

### 4. 接口隔离原则 (ISP)

不应该强迫客户端依赖它们不使用的接口：

```python
# 不好的设计 - 大而全的接口
class StrategyService(ABC):
    @abstractmethod
    async def create(self): ...
    @abstractmethod
    async def execute(self): ...
    @abstractmethod
    async def optimize(self): ...
    @abstractmethod
    async def backtest(self): ...

# 好的设计 - 小而专的接口
class Creatable(Protocol):
    async def create(self): ...

class Executable(Protocol):
    async def execute(self): ...

class Optimizable(Protocol):
    async def optimize(self): ...

class Backtestable(Protocol):
    async def backtest(self): ...

# 类只实现需要的接口
class SimpleStrategy:
    async def create(self): ...  # 只实现创建功能

class AdvancedStrategy:
    async def create(self): ...
    async def execute(self): ...
    async def optimize(self): ...
    async def backtest(self): ...
```

## 实施建议

### 1. 迁移策略

1. **并行运行期**
   - 保持现有API运行
   - 新架构并行开发
   - 逐步迁移功能模块

2. **功能模块迁移顺序**
   - 策略管理（基础CRUD）
   - 执行管理（状态控制）
   - 个性化功能
   - 实时通信（WebSocket）

3. **数据迁移**
   - 使用统一的数据模型适配器
   - 实现数据兼容性检查
   - 提供回滚机制

### 2. 性能优化建议

1. **数据库优化**
   - 添加适当的索引
   - 使用数据库连接池
   - 实现读写分离

2. **缓存优化**
   - 热数据预加载
   - 缓存预热策略
   - 缓存穿透防护

3. **API优化**
   - 实现请求合并
   - 批量操作接口
   - 响应压缩

### 3. 监控和日志

1. **性能监控**
   - API响应时间监控
   - 数据库查询性能
   - 缓存命中率统计

2. **业务监控**
   - 策略执行成功率
   - 用户行为分析
   - 错误率统计

3. **日志规范**
   - 结构化日志格式
   - 请求追踪ID
   - 日志级别管理

### 4. 安全建议

1. **认证授权**
   - JWT Token刷新机制
   - 权限细粒度控制
   - API访问频率限制

2. **数据安全**
   - 敏感数据加密
   - SQL注入防护
   - XSS防护

3. **网络安全**
   - HTTPS强制使用
   - CORS策略配置
   - 请求大小限制

## 总结

本设计文档提供了一个统一、可扩展的API模块架构，通过分层设计、依赖注入、统一接口等设计模式，解决了现有代码重复、耦合度高的问题。新架构具有良好的可维护性、可测试性和可扩展性，能够支持业务的快速发展。

实施过程中需要注意平滑迁移，保证系统稳定运行，同时逐步优化性能和完善监控体系。建议采用敏捷开发方式，分阶段实施，及时收集反馈并调整设计。
---
name: dependency-optimization
title: 依賴注入實現與循環依賴消除
status: in_progress
phase: 4
priority: P0
created: 2025-12-24T12:05:52Z
updated: 2025-12-25T02:15:00Z
started: 2025-12-25T02:15:00Z
estimated_hours: 64
actual_hours: 4
assignee: TBD
dependencies: ["005-backend-consolidation"]
github:
  issue: 78
  url: https://github.com/kennyto266/cbsc-system-unification/issues/78
---

# Task 006: 依賴注入實現與循環依賴消除

## 概述

消除模塊間的循環依賴，實現依賴注入容器，建立清晰的模塊邊界和接口定義。

## 詳細描述

### 循環依賴分析

#### 已識別的循環依賴

1. **frontend → backend/src 循環**
   ```
   frontend/src/api/ → backend/api/
   frontend/src/api/ → src/api/
   src/strategies/ → backend/api/
   ```

2. **模型層循環**
   ```
   backend/models/ → src/models/
   src/models/ → backend/models/
   ```

3. **服務層循環**
   ```
   backend/services/ → src/services/
   src/services/ → backend/services/
   ```

#### 依賴規則定義

```
允許的依賴方向:
┌─────────────┐
│  Frontend   │
└──────┬──────┘
       │ HTTP/WebSocket
       ▼
┌─────────────┐
│  API Layer  │  (backend/api/)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Services   │  (backend/services/)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Models   │  (backend/models/)
└─────────────┘

禁止的依賴:
✗ Services → API
✗ Models → Services
✗ 跨層級直接調用
```

### 依賴注入實現

#### 1. 依賴注入容器

```python
# backend/core/container.py
from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject
from backend.core.database import AsyncSessionLocal
from backend.services.auth_service import AuthService
from backend.services.strategy_service import StrategyService
from backend.services.backtest_service import BacktestService

class Container(containers.DeclarativeContainer):
    """Dependency injection container"""

    # Configuration
    config = providers.Configuration()

    # Database
    database = providers.Singleton(AsyncSessionLocal)

    # Services
    auth_service = providers.Factory(
        AuthService,
        db=database
    )

    strategy_service = providers.Factory(
        StrategyService,
        db=database
    )

    backtest_service = providers.Factory(
        BacktestService,
        db=database,
        strategy_service=strategy_service
    )

# Global container instance
container = Container()
```

#### 2. 使用依賴注入

```python
# backend/api/v2/auth/routes.py
from fastapi import APIRouter, Depends
from dependency_injector.wiring import Provide, inject
from backend.core.container import Container
from backend.services.auth_service import AuthService
from backend.schemas.auth import LoginRequest, TokenResponse

router = APIRouter()

@router.post("/login")
@inject
async def login(
    credentials: LoginRequest,
    auth_service: AuthService = Depends(Provide[Container.auth_service])
) -> TokenResponse:
    """Login endpoint with injected service"""
    return await auth_service.login(credentials.username, credentials.password)
```

#### 3. 模塊接口定義

```python
# backend/services/interfaces/strategy_service_interface.py
from abc import ABC, abstractmethod
from typing import List, Optional
from backend.schemas.strategy import StrategyCreate, StrategyResponse

class IStrategyService(ABC):
    """Strategy service interface"""

    @abstractmethod
    async def create(
        self,
        user_id: int,
        data: StrategyCreate
    ) -> StrategyResponse:
        """Create a new strategy"""
        pass

    @abstractmethod
    async def get_by_id(
        self,
        strategy_id: int,
        user_id: int
    ) -> Optional[StrategyResponse]:
        """Get strategy by ID"""
        pass

    @abstractmethod
    async def list(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[StrategyResponse]:
        """List strategies"""
        pass

# 實現類
class StrategyService(IStrategyService):
    """Concrete strategy service implementation"""
    # ... implementation
```

### 模塊解耦策略

#### 1. 抽象層引入

```python
# backend/core/interfaces.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class DatabaseProvider(Protocol):
    """Database provider protocol"""
    async def get(self, model, id): ...
    async def create(self, model, **kwargs): ...
    async def update(self, model, id, **kwargs): ...
    async def delete(self, model, id): ...

@runtime_checkable
class CacheProvider(Protocol):
    """Cache provider protocol"""
    async def get(self, key: str): ...
    async def set(self, key: str, value: any, ttl: int): ...
    async def delete(self, key: str): ...
```

#### 2. 事件驅動解耦

```python
# backend/core/events.py
from typing import Callable, Dict, List
from dataclasses import dataclass

@dataclass
class Event:
    """Base event class"""
    name: str
    data: dict

class EventBus:
    """Simple event bus for decoupling"""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_name: str, handler: Callable):
        """Subscribe to event"""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(handler)

    async def publish(self, event: Event):
        """Publish event"""
        handlers = self._subscribers.get(event.name, [])
        for handler in handlers:
            await handler(event.data)

# Global event bus
event_bus = EventBus()

# Usage in services
class StrategyService:
    async def create_strategy(self, data):
        strategy = await self.db.create(Strategy, **data)
        # Publish event instead of direct dependency
        await event_bus.publish(Event("strategy.created", {
            "strategy_id": strategy.id,
            "user_id": strategy.user_id
        }))
        return strategy

# Other services subscribe to events
class NotificationService:
    def __init__(self):
        event_bus.subscribe("strategy.created", self.on_strategy_created)

    async def on_strategy_created(self, data):
        # Send notification without direct dependency
        await self.send_notification(data["user_id"], "Strategy created!")
```

### 循環依賴檢測

#### 檢測腳本

```python
# scripts/detect_circular_deps.py
import ast
import os
from collections import defaultdict, deque

class ImportAnalyzer(ast.NodeVisitor):
    """AST visitor to detect imports"""

    def __init__(self, filepath):
        self.filepath = filepath
        self.imports = set()
        self.module_path = self._get_module_path(filepath)

    def _get_module_path(self, filepath):
        """Convert filepath to module path"""
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        rel_path = os.path.relpath(filepath, root)
        return rel_path.replace(os.sep, '.')[:-3]  # Remove .py

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.add(node.module.split('.')[0])
        self.generic_visit(node)

def detect_circular_dependencies(root_dir):
    """Detect circular dependencies in Python project"""
    graph = defaultdict(set)
    modules = set()

    # Build dependency graph
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                analyzer = ImportAnalyzer(filepath)
                with open(filepath, 'r', encoding='utf-8') as f:
                    analyzer.visit(ast.parse(f.read()))
                modules.add(analyzer.module_path)
                graph[analyzer.module_path].update(analyzer.imports)

    # Detect cycles using DFS
    def has_cycle(node, visited=None, rec_stack=None):
        if visited is None:
            visited = set()
        if rec_stack is None:
            rec_stack = set()

        visited.add(node)
        rec_stack.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in modules:  # Skip external modules
                continue
            if neighbor not in visited:
                if has_cycle(neighbor, visited, rec_stack):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.remove(node)
        return False

    # Check all modules
    cycles = []
    for module in modules:
        if has_cycle(module):
            cycles.append(module)

    return cycles

if __name__ == "__main__":
    backend_dir = "backend"
    src_dir = "src"

    print("Checking for circular dependencies...")
    backend_cycles = detect_circular_dependencies(backend_dir)
    src_cycles = detect_circular_dependencies(src_dir)

    if backend_cycles:
        print(f"Circular dependencies found in backend/: {backend_cycles}")
    else:
        print("No circular dependencies in backend/")

    if src_cycles:
        print(f"Circular dependencies found in src/: {src_cycles}")
    else:
        print("No circular dependencies in src/")
```

## 驗收標準

### 交付物

- [ ] **依賴注入容器**
  - Container 配置
  - 服務註冊
  - 作用域管理

- [ ] **模塊接口定義**
  - 服務接口協議
  - 抽象基類
  - 類型提示

- [ ] **事件總線實現**
  - EventBus 類
  - 事件訂閱/發布
  - 事件處理器

- [ ] **檢測工具**
  - 循環依賴檢測腳本
  - 依賴圖生成
  - CI 集成

### 質量門檻

- 零循環依賴
- 依賴圖清晰無歧義
- 所有服務可獨立測試
- 接口文檔完整

## 依賴關係

### 前置任務
- Task 005: 後端 API 統一

### 後續任務
- Task 008: 測試與質量保證

## 執行步驟

1. **第 1-3 天: 依賴分析**
   - 運行檢測腳本
   - 繪製依賴圖
   - 識別關鍵循環

2. **第 4-7 天: 依賴注入實現**
   - 創建容器
   - 重構服務層
   - 配置依賴注入

3. **第 8-10 天: 接口抽象**
   - 定義服務接口
   - 實現協議類
   - 事件驅動解耦

4. **第 11-14 天: 驗證和測試**
   - 消除所有循環依賴
   - 獨立測試每個模塊
   - CI 集成檢測

## 風險與緩解

| 風險 | 緩解措施 |
|------|----------|
| 重構破壞功能 | 完整的回歸測試 |
| 接口設計不當 | 迭代設計，提前審查 |
| 性能下降 | 基準測試，監控關鍵路徑 |

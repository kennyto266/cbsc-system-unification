# Task #006: 依賴優化實施文件

**創建時間**: 2025-12-25T02:15:00Z
**任務狀態**: 🟢 in_progress
**實施階段**: Phase 1/3

---

## 已完成的工作

### 1. 基礎設施 ✅

#### 依賴注入容器
**文件**: `src/core/container.py`

```python
# 創建的組件:
- CoreContainer: 核心依賴注入容器
- ServiceContainer: 服務層依賴注入容器
- APIContainer: API層依賴注入容器
- 輔助函數: get_db_session, get_event_bus
```

#### 服務接口
**文件**: `src/services/interfaces/__init__.py`

```python
# 定義的接口:
- IService: 基礎服務接口
- IAuthService: 認證服務接口
- IStrategyService: 策略服務接口
- IBacktestService: 回測服務接口
- IDataService: 數據服務接口
- INotificationService: 通知服務接口
- ICacheService: 緩存服務接口
- IRepository: 基礎倉儲接口
```

#### 循環依賴檢測腳本
**文件**: `scripts/detect_circular_deps.py`

```bash
# 使用方法:
python scripts/detect_circular_deps.py src backend --output dependency-report.json

# 功能:
- AST 解析分析導入
- 依賴圖構建
- 循環依賴檢測
- 生成 JSON 報告
```

---

## 接下來的實施步驟

### Phase 1: 依賴清理 (1-2天)

#### 1.1 前端依賴清理

**移除重複的庫**:

```diff
# frontend/package.json

# 重複的手勢庫
- "react-use-gesture": "^9.1.3"  # 移除 (已棄用)

# 重複的圖表庫
- "recharts": "^2.15.4"  # 移除 (使用 chart.js)
- "@ant-design/plots": "^1.2.5"  # 移除 (使用 chart.js)

# 重複的拖拽庫
- "react-rnd": "^10.5.2"  # 移除 (使用 react-dnd)
```

**執行命令**:
```bash
cd frontend
npm uninstall react-use-gesture recharts @ant-design/plots react-rnd
npm install
```

#### 1.2 後端依賴清理

**移除棄用的庫**:

```diff
# src/requirements.txt

# 棄用的 Redis 客戶端
- aioredis==2.0.1  # 已合併到 redis

# 重複的 HTTP 客戶端
- aiohttp==3.9.1  # 使用 httpx 統一
```

**更新 requirements.txt**:
```bash
# 創建開發依賴文件
cat > requirements-dev.txt << 'EOF'
# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Code Quality
black==23.11.0
isort==5.12.0
flake8==6.1.0
mypy==1.7.1

# Type Stubs
types-requests
types-redis
EOF
```

---

### Phase 2: 依賴注入實施 (2-3天)

#### 2.1 註冊服務到容器

**更新 `src/core/container.py`**:

```python
from ..services.auth_service import AuthService
from ..services.strategy_service import StrategyService
from ..services.backtest_service import BacktestService

class ServiceContainer(containers.DeclarativeContainer):
    # ... existing code ...

    # Register services
    auth_service = providers.Factory(
        AuthService,
        db=core.database_session,
        event_bus=core.event_bus
    )

    strategy_service = providers.Factory(
        StrategyService,
        db=core.database_session,
        event_bus=core.event_bus
    )

    backtest_service = providers.Factory(
        BacktestService,
        db=core.database_session,
        event_bus=core.event_bus,
        strategy_service=strategy_service
    )
```

#### 2.2 更新 API 端點使用依賴注入

**示例**: `src/api/auth/routes.py`

```python
from fastapi import APIRouter, Depends
from dependency_injector.wiring import Provide, inject

from ...core.container import ServiceContainer
from ...services.interfaces import IAuthService

router = APIRouter()

@router.post("/login")
@inject
async def login(
    username: str,
    password: str,
    auth_service: IAuthService = Depends[Provide[ServiceContainer.auth_service]]
):
    return await auth_service.login(username, password)
```

#### 2.3 重構現有服務實現接口

**更新 `src/services/auth_service.py`**:

```python
from .interfaces import IAuthService, ServiceResponse

class AuthService(IAuthService):
    """Authentication service implementation"""

    async def initialize(self) -> None:
        """Initialize service"""
        pass

    async def shutdown(self) -> None:
        """Shutdown service"""
        pass

    def health_check(self) -> bool:
        """Check service health"""
        return True

    async def login(
        self,
        username: str,
        password: str
    ) -> ServiceResponse[Dict]:
        """Login user"""
        # Implementation...
```

---

### Phase 3: 循環依賴消除 (2-3天)

#### 3.1 運行檢測腳本

```bash
# 檢測循環依賴
python scripts/detect_circular_deps.py src backend -v

# 輸出 JSON 報告
python scripts/detect_circular_deps.py src backend -o dependency-report.json
```

#### 3.2 重構消除循環

**策略 1: 提取公共模塊**

```
Before:
  frontend/src/api/ → backend/api/
  backend/api/ → frontend/src/api/

After:
  frontend/src/api/ → shared/types/
  backend/api/ → shared/types/
```

**策略 2: 使用事件驅動**

```
Before:
  Service A → Service B
  Service B → Service A  # 循環!

After:
  Service A → EventBus
  EventBus → Service B
  Service B → EventBus
  EventBus → Service A
```

**策略 3: 引入接口抽象**

```
Before:
  Service A → Service B  # 直接依賴
  Service B → Service A  # 循環!

After:
  Service A → IServiceB  # 依賴接口
  Service B → IServiceA  # 依賴接口
  ImplementationA implements IServiceA
  ImplementationB implements IServiceB
```

---

## 驗收標準

### 依賴清理
- [ ] 前端移除 5+ 個重複依賴
- [ ] 後端移除 2+ 個重複依賴
- [ ] node_modules 減少 20%+
- [ ] pip install 時間減少 15%+

### 依賴注入
- [ ] 所有服務實現接口
- [ ] 所有 API 端點使用依賴注入
- [ ] 容器正確註冊所有服務
- [ ] 服務可獨立測試

### 循環依賴消除
- [ ] 檢測腳本報告 0 個循環
- [ ] 模塊依賴圖清晰
- [ ] 服務間無直接循環引用

---

## 預計時間表

| 階段 | 任務 | 工時 | 狀態 |
|------|------|------|------|
| Phase 1 | 依賴清理 | 8-12h | 🟡 待開始 |
| Phase 2 | 依賴注入 | 16-24h | 🟡 待開始 |
| Phase 3 | 循環消除 | 12-18h | 🟡 待開始 |
| 總計 | | 36-54h | |

---

## 下一步行動

1. **立即執行**: 移除前端重複依賴
2. **並行開始**: 移除後端重複依賴
3. **協調進行**: 開始依賴注入實施

---

*實施文件創建於 2025-12-25T02:15:00Z*

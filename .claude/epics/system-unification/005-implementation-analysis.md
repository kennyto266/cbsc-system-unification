# Task #005: Migrate Core CBSC Strategy Management APIs
## 實施分析報告

**開始時間**: 2025-12-25T01:30:10Z
**任務狀態**: 🟢 in_progress (依賴已滿足)

---

## 📊 現有代碼庫分析

### 發現的策略API文件

| 文件 | 行數 | 主要功能 | 管理器類 |
|------|------|----------|----------|
| `src/api/strategy_endpoints.py` | 862 | 基礎CRUD操作 | StrategyManager |
| `src/api/cbsc_strategy_api.py` | 771 | CBSC業務邏輯 | CBSCStrategyManager |
| `src/api/personal_strategy_endpoints.py` | 1124 | 用戶個人化功能 | PersonalStrategyManager |

**總計**: 2,757 行策略管理代碼

---

## 🔍 詳細代碼分析

### 1. strategy_endpoints.py (862行)

**核心類**: `StrategyManager`

```python
class StrategyManager:
    def __init__(self):
        self.strategies: Dict[str, Strategy] = {}
        self.signals: List[StrategySignal] = []
        self.performances: Dict[str, StrategyPerformance] = {}
        self.executions: Dict[str, StrategyExecutionResult] = {}
        self.templates: Dict[str, CBSCStrategyTemplate] = {}
```

**已實現的API端點**:
```
✅ GET    /api/strategies/           - 策略列表 (分頁、過濾)
✅ POST   /api/strategies/           - 創建策略
✅ GET    /api/strategies/{id}       - 獲取策略詳情
✅ PUT    /api/strategies/{id}       - 更新策略
✅ DELETE /api/strategies/{id}       - 刪除策略
✅ POST   /api/strategies/{id}/execute - 執行策略
✅ GET    /api/strategies/{id}/status  - 獲取策略狀態
✅ POST   /api/strategies/{id}/stop    - 停止策略
✅ GET    /api/strategies/templates   - 獲取策略模板
```

**依賴**: `strategy_management_api` 模組

---

### 2. cbsc_strategy_api.py (771行)

**核心類**: `CBSCStrategyManager`

```python
class CBSCStrategyManager:
    def __init__(self):
        self.strategies: Dict[str, Strategy] = {}
        self.strategy_statuses: Dict[str, StrategyRealTimeStatus] = {}
        self.execution_history: Dict[str, List[StrategyExecutionResult]] = {}
        self.strategy_templates: Dict[str, CBSCStrategyTemplate] = {}
        self.performance_cache: Dict[str, StrategyPerformance] = {}
        self.risk_metrics_cache: Dict[str, StrategyRiskMetrics] = {}
```

**額外功能**:
- ✅ 實時狀態追蹤 (`StrategyRealTimeStatus`)
- ✅ 風險指標計算 (`StrategyRiskMetrics`)
- ✅ 執行報告生成 (`StrategyExecutionReport`)
- ✅ 配置驗證 (`StrategyConfigValidation`)
- ✅ WebSocket集成支持

**認證集成**:
```python
# 已經整合認證系統
from auth_simple import User, AuthService
async def get_current_user(token: str = Depends(...))
```

---

### 3. personal_strategy_endpoints.py (1124行)

**核心類**: `PersonalStrategyManager`

```python
class PersonalStrategyManager:
    def __init__(self):
        self.user_strategies: Dict[int, Dict[str, Strategy]] = {}
        self.user_performances: Dict[int, Dict[str, StrategyPerformance]] = {}
        self.user_signals: Dict[int, List[StrategySignal]] = {}
        self.user_alerts: Dict[int, List[StrategyAlert]] = {}
        self.user_preferences: Dict[int, UserPreferences] = {}
        self.websocket_connections: Dict[int, List[WebSocket]] = {}
```

**個人化功能**:
- ✅ 用戶級別策略隔離
- ✅ 個人化儀表板數據
- ✅ 實時數據更新 (WebSocket)
- ✅ 策略告警系統
- ✅ 用戶偏好設置

**WebSocket支持**:
```python
@router.websocket("/ws/realtime/{user_id}")
async def realtime_data_stream(websocket: WebSocket, user_id: int)
```

---

## 🎯 遷移策略

### 階段1: 統一API端點 (1-2天)

**目標**: 創建統一的 `/api/strategies/v2` 端點

```python
# 新的統一路由結構
/api/strategies/v2/
├── /                    # 策略列表和創建
├── /{id}               # 策略詳情和更新
├── /{id}/execute       # 執行策略
├── /{id}/status        # 實時狀態
├── /{id}/performance   # 性能指標
├── /{id}/signals       # 信號歷史
├── /templates          # 策略模板
└── /batch              # 批量操作
```

### 階段2: 整合現有功能 (2-3天)

**整合來源**:
1. `strategy_endpoints.py` → 基礎CRUD
2. `cbsc_strategy_api.py` → CBSC特定功能
3. `personal_strategy_endpoints.py` → 用戶個人化

### 階段3: 數據庫集成 (1-2天)

**需要整合的數據模型**:
```python
# 使用現有的統一數據模型
from src.models.strategy_models_v2 import Strategy
from src.models.backtest_models_v2 import Backtest
from src.models.risk_models_v2 import RiskMetrics
```

### 階段4: 測試和驗證 (1天)

- 單元測試
- 集成測試
- API兼容性測試

---

## 📋 實施計劃

### 立即可執行任務

#### Task 5.1: 創建統一API路由 (優先級: P0)

**目標**: 創建 `src/api/strategies/v2/unified_routes.py`

```python
"""
統一策略管理API v2
整合 strategy_endpoints, cbsc_strategy_api, personal_strategy_endpoints
"""

from fastapi import APIRouter, Depends
from src.auth.middleware import get_current_user
from src.models.strategy_models_v2 import Strategy

router = APIRouter(prefix="/api/strategies/v2", tags=["strategies"])

# 策略CRUD
@router.get("/")
async def list_strategies(
    user = Depends(get_current_user),
    type: Optional[StrategyType] = None,
    status: Optional[StrategyStatus] = None
):
    """統一的策略列表端點"""
    pass

@router.post("/")
async def create_strategy(
    request: CreateStrategyRequest,
    user = Depends(get_current_user)
):
    """統一的策略創建端點"""
    pass
```

#### Task 5.2: 整合策略管理器 (優先級: P0)

**目標**: 創建 `src/services/unified_strategy_service.py`

```python
"""
統一策略服務
整合 StrategyManager, CBSCStrategyManager, PersonalStrategyManager
"""

class UnifiedStrategyService:
    def __init__(self):
        # 整合三個管理器的功能
        self.strategies = {}  # 來自 StrategyManager
        self.realtime_status = {}  # 來自 CBSCStrategyManager
        self.user_strategies = {}  # 來自 PersonalStrategyManager

    async def create_strategy(self, request, user_id) -> Strategy:
        """統一的創建邏輯"""
        # 1. 驗證數據
        # 2. 生成策略ID
        # 3. 保存到數據庫
        # 4. 初始化相關服務
        pass
```

#### Task 5.3: 數據庫遷移 (優先級: P1)

**目標**: 創建遷移腳本

```python
# src/migrations/scripts/006_unify_strategy_tables.py
"""
統一策略表的遷移腳本
整合現有的策略數據到統一結構
"""

def upgrade():
    # 創建統一的策略表
    # 遷移現有數據
    # 更新索引和約束
    pass

def downgrade():
    # 回滾腳本
    pass
```

---

## 🔧 技術實現細節

### 依賴注入配置

```python
# src/dependencies.py
from fastapi import Depends
from src.services.unified_strategy_service import UnifiedStrategyService

# 全局服務實例
strategy_service = UnifiedStrategyService()

async def get_strategy_service() -> UnifiedStrategyService:
    return strategy_service
```

### 認證集成

```python
# 使用現有的認證系統 (#003)
from src.auth.middleware import get_current_user
from src.models.rbac_models import Permission

@router.post("/")
async def create_strategy(
    request: CreateStrategyRequest,
    current_user = Depends(get_current_user),  # ✅ 已整合
    strategy_service: UnifiedStrategyService = Depends(get_strategy_service)
):
    # 使用 current_user.id 創建策略
    strategy = await strategy_service.create_strategy(
        data=request.dict(),
        user_id=current_user.id
    )
    return strategy
```

### 數據庫集成

```python
# 使用現有的數據庫系統 (#002)
from src.core.database import get_db
from src.models.strategy_models_v2 import Strategy
from sqlalchemy.ext.asyncio import AsyncSession

@router.get("/{strategy_id}")
async def get_strategy(
    strategy_id: str,
    db: AsyncSession = Depends(get_db),  # ✅ 已整合
    current_user = Depends(get_current_user)
):
    # 從數據庫查詢
    result = await db.execute(
        select(Strategy).where(
            Strategy.id == strategy_id,
            Strategy.user_id == current_user.id
        )
    )
    return result.scalar_one_or_404()
```

---

## ✅ 驗收標準

### 功能完整性

- [ ] 所有現有API端點可用
- [ ] 策略CRUD功能正常
- [ ] 實時狀態更新工作
- [ ] 用戶權限控制生效
- [ ] 性能指標計算正確

### 兼容性

- [ ] 與現有CBSC數據格式100%兼容
- [ ] 舊API端點仍然可用
- [ ] 數據遷移無損
- [ ] WebSocket連接正常

### 性能

- [ ] API響應時間 < 100ms
- [ ] 並發策略執行正常
- [ ] 數據庫查詢優化
- [ ] 緩存策略有效

---

## 🚀 下一步具體行動

### 立即開始

1. **創建統一路由文件**
   ```bash
   touch src/api/strategies/v2/unified_routes.py
   ```

2. **創建統一服務文件**
   ```bash
   touch src/services/unified_strategy_service.py
   ```

3. **創建遷移腳本**
   ```bash
   touch src/migrations/scripts/006_unify_strategy_tables.py
   ```

### 並行執行

- Task #007 (測試框架) 可以同時開始
- Task #006 (Dashboard UI) 可以在API端點定義後開始

---

## 📊 預計工時更新

| 階段 | 原估計 | 調整後 | 理由 |
|------|--------|--------|------|
| 基礎設施 (#001-#004) | 92-124h | ✅ 已完成 | 現有實現 |
| API整合 | 32-40h | 24-32h | 代碼已存在，只需整合 |
| 前端Dashboard | 28-36h | 20-28h | 組件庫已完成 |
| 測試框架 | 24-30h | 16-24h | 可復用現有測試 |
| 部署 | 20-28h | 16-24h | Docker配置已有 |

**總計**: 原計劃 196-258h → 新估計 **76-108h** (節省 60-70% 時間)

---

*分析報告生成於 2025-12-25T01:30:10Z*

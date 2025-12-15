# CBSC 策略管理系統架構分析報告

## 概述

本文檔對CBSC量化交易策略管理系統的架構進行深入分析，識別當前架構的優缺點，並提出改進建議。

## 當前架構概覽

### 1. 架構層次

```
┌─────────────────────────────────────────────────────┐
│                 前端展示層 (Frontend)                  │
│  • React Dashboard                                  │
│  • 策略管理界面                                       │
│  • 實時監控組件                                       │
└─────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────┐
│                 API網關層 (API Gateway)              │
│  • FastAPI路由                                       │
│  • 認證授權                                           │
│  • 請求限流                                           │
└─────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────┐
│               策略服務層 (Strategy Service)          │
│  • Strategy Service                                 │
│  • Enhanced Strategy Service                        │
│  • Unified Strategy Service                         │
└─────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────┐
│               執行引擎層 (Execution Engine)          │
│  • Strategy Execution Engine                        │
│  • WebSocket Service                                │
│  • Task Queue                                       │
└─────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────┐
│               數據存儲層 (Data Storage)              │
│  • PostgreSQL (主數據庫)                            │
│  • Redis (緩存)                                      │
│  • InfluxDB (時序數據)                              │
└─────────────────────────────────────────────────────┘
```

### 2. 核心組件分析

#### 2.1 策略模型層

**位置**: `src/api/strategies/models.py`

**主要類**:
- `Strategy`: 策略主體模型
- `StrategySignal`: 策略信號模型
- `StrategyPerformance`: 策略性能模型
- `StrategyType`: 策略類型枚舉

**優點**:
- 使用Pydantic提供數據驗證
- 清晰的枚舉定義
- 支持靈活的參數存儲

**問題**:
- 缺少策略版本控制
- 參數結構過於靈活，缺乏類型安全
- 沒有策略依賴關係管理

#### 2.2 策略服務層

**位置**:
- `src/api/strategies/services/strategy_service.py`
- `src/api/strategies/services/enhanced_strategy_service.py`
- `src/api/unified_strategy_service.py`

**主要功能**:
- 策略CRUD操作
- 策略執行管理
- 緩存管理
- 權限控制

**發現的問題**:

1. **多個並行的策略服務**:
   - 存在3個不同的策略服務實現
   - 功能重疊，導致維護困難
   - 沒有清晰的職責劃分

2. **服務耦合度高**:
   - 服務直接依賴具體的Repository實現
   - 難以進行單元測試
   - 不便於替換存儲層實現

3. **缺乏統一的錯誤處理**:
   - 每個服務有自己的錯誤處理方式
   - 錯誤消息不一致
   - 難以進行全局錯誤監控

#### 2.3 策略執行引擎

**位置**: `src/api/strategy_execution_engine.py`

**主要特性**:
- 支持多種執行模式（回測、實時、模擬交易）
- 抽象的市場數據提供者接口
- 執行狀態管理

**問題**:
1. **執行引擎與策略緊耦合**
2. **缺乏執行結果的持久化機制**
3. **沒有完整的錯誤恢復機制**

#### 2.4 API端點層

**位置**:
- `src/api/strategy_endpoints.py`
- `src/api/unified_strategy_endpoints.py`
- `src/api/strategies/router.py`

**問題**:
1. **路由定義分散**
2. **API版本控制缺失**
3. **文檔生成不完整**

## 架構問題總結

### 1. 設計問題

#### 1.1 單一職責原則違反
- 多個策略服務承擔相似職責
- 執行引擎承擔過多職責
- API端點混合業務邏輯

#### 1.2 開放封閉原則違反
- 添加新策略類型需要修改核心代碼
- 數據模型擴展困難

#### 1.3 依賴倒置原則違反
- 高層模塊依賴低層模塊
- 難以進行單元測試和模擬

### 2. 實現問題

#### 2.1 代碼重複
- 多處相似的CRUD操作
- 重複的驗證邏輯
- 重複的錯誤處理

#### 2.2 缺乏抽象
- 沒有統一的接口定義
- 策略執行流程固化
- 擴展性差

#### 2.3 狀態管理混亂
- 策略狀態轉換不清晰
- 並發控制缺失
- 事務管理不完整

### 3. 運維問題

#### 3.1 監控不足
- 缺乏關鍵指標監控
- 日誌結構不統一
- 性能瓶頸難以定位

#### 3.2 可維護性差
- 組件間緊耦合
- 配置管理分散
- 部署流程複雜

## 改進建議

### 1. 架構重構方案

#### 1.1 引入DDD（領域驅動設計）

```python
# 領域層 (Domain Layer)
class StrategyDomainService:
    """策略領域服務，包含核心業務邏輯"""
    pass

class StrategyRepository(ABC):
    """策略倉儲接口"""
    @abstractmethod
    async def save(self, strategy: Strategy) -> None:
        pass

    @abstractmethod
    async def find_by_id(self, strategy_id: str) -> Optional[Strategy]:
        pass

# 應用層 (Application Layer)
class StrategyApplicationService:
    """策略應用服務，編排領域服務"""
    def __init__(self,
                 repository: StrategyRepository,
                 execution_engine: ExecutionEngine):
        self.repository = repository
        self.execution_engine = execution_engine
```

#### 1.2 實現CQRS（命令查詢職責分離）

```python
# 命令端
class StrategyCommandHandler:
    async def handle_create_strategy(self, command: CreateStrategyCommand):
        # 處理策略創建命令
        pass

    async def handle_update_strategy(self, command: UpdateStrategyCommand):
        # 處理策略更新命令
        pass

# 查詢端
class StrategyQueryHandler:
    async def handle_get_strategy(self, query: GetStrategyQuery):
        # 處理策略查詢
        pass

    async def handle_list_strategies(self, query: ListStrategiesQuery):
        # 處理策略列表查詢
        pass
```

#### 1.3 引入事件驅動架構

```python
# 領域事件
class StrategyCreated(DomainEvent):
    def __init__(self, strategy_id: str, user_id: int):
        self.strategy_id = strategy_id
        self.user_id = user_id
        self.timestamp = datetime.now()

class StrategyExecuted(DomainEvent):
    def __init__(self, strategy_id: str, result: ExecutionResult):
        self.strategy_id = strategy_id
        self.result = result
        self.timestamp = datetime.now()

# 事件處理器
class EventHandler:
    async def handle(self, event: DomainEvent):
        # 處理領域事件
        pass
```

### 2. 具體改進措施

#### 2.1 統一策略服務

```python
class UnifiedStrategyService:
    """統一的策略管理服務"""

    def __init__(self,
                 command_handler: StrategyCommandHandler,
                 query_handler: StrategyQueryHandler,
                 event_bus: EventBus):
        self.command_handler = command_handler
        self.query_handler = query_handler
        self.event_bus = event_bus

    async def create_strategy(self, request: CreateStrategyRequest) -> Strategy:
        command = CreateStrategyCommand(**request.dict())
        return await self.command_handler.handle(command)

    async def get_strategy(self, strategy_id: str) -> Strategy:
        query = GetStrategyQuery(strategy_id=strategy_id)
        return await self.query_handler.handle(query)
```

#### 2.2 改進執行引擎

```python
class ExecutionEngine:
    """改進的策略執行引擎"""

    def __init__(self,
                 strategy_registry: StrategyRegistry,
                 market_data_provider: MarketDataProvider,
                 execution_store: ExecutionStore):
        self.strategy_registry = strategy_registry
        self.market_data_provider = market_data_provider
        self.execution_store = execution_store

    async def execute_strategy(self,
                             strategy_id: str,
                             execution_request: ExecutionRequest) -> ExecutionResult:
        # 1. 獲取策略定義
        strategy = await self.strategy_registry.get(strategy_id)

        # 2. 驗證執行請求
        self._validate_request(strategy, execution_request)

        # 3. 創建執行上下文
        context = ExecutionContext(
            strategy=strategy,
            request=execution_request,
            data_provider=self.market_data_provider
        )

        # 4. 執行策略
        result = await self._execute_with_context(context)

        # 5. 持久化執行結果
        await self.execution_store.save_result(strategy_id, result)

        return result
```

#### 2.3 實現策略工廠模式

```python
class StrategyFactory:
    """策略工廠，負責創建策略實例"""

    _strategies = {
        "direct_rsi": DirectRSIStrategy,
        "dual_rsi": DualRSIStrategy,
        "composite": CompositeStrategy,
        "ai_ml": AIMLStrategy,
    }

    @classmethod
    def create_strategy(cls, strategy_type: str, config: Dict) -> IStrategy:
        if strategy_type not in cls._strategies:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        strategy_class = cls._strategies[strategy_type]
        return strategy_class.from_config(config)

    @classmethod
    def register_strategy(cls, strategy_type: str, strategy_class: Type[IStrategy]):
        """註冊新的策略類型"""
        cls._strategies[strategy_type] = strategy_class
```

### 3. 數據模型改進

#### 3.1 策略版本控制

```python
class StrategyVersion(BaseModel):
    """策略版本"""
    strategy_id: str
    version: int
    config: Dict[str, Any]
    created_at: datetime
    created_by: int
    changelog: Optional[str] = None
    is_active: bool = True

class Strategy(BaseModel):
    """改進的策略模型"""
    id: str
    name: str
    description: str
    strategy_type: StrategyType
    current_version: int
    versions: List[StrategyVersion] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

#### 3.2 策略依賴管理

```python
class StrategyDependency(BaseModel):
    """策略依賴"""
    strategy_id: str
    depends_on: str  # 依賴的策略ID
    dependency_type: str  # data, signal, execution
    config_mapping: Dict[str, str] = Field(default_factory=dict)

class StrategyGraph:
    """策略依賴圖"""

    def __init__(self):
        self.dependencies: Dict[str, List[StrategyDependency]] = {}

    def add_dependency(self, dependency: StrategyDependency):
        if dependency.strategy_id not in self.dependencies:
            self.dependencies[dependency.strategy_id] = []
        self.dependencies[dependency.strategy_id].append(dependency)

    def get_execution_order(self, strategy_ids: List[str]) -> List[str]:
        # 拓撲排序，獲取執行順序
        pass
```

### 4. 性能優化建議

#### 4.1 緩存策略

```python
class StrategyCacheManager:
    """策略緩存管理器"""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.cache_ttl = timedelta(minutes=30)

    async def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        cache_key = f"strategy:{strategy_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return Strategy.parse_raw(cached)
        return None

    async def cache_strategy(self, strategy: Strategy):
        cache_key = f"strategy:{strategy.id}"
        await self.redis.setex(
            cache_key,
            self.cache_ttl,
            strategy.json()
        )
```

#### 4.2 批量操作優化

```python
class StrategyBatchProcessor:
    """策略批量處理器"""

    async def process_signals(self, signals: List[StrategySignal]):
        """批量處理策略信號"""
        # 按策略類型分組
        signals_by_strategy = self._group_by_strategy(signals)

        # 並行處理
        tasks = []
        for strategy_id, strategy_signals in signals_by_strategy.items():
            task = self._process_strategy_signals(strategy_id, strategy_signals)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return results
```

## 實施計劃

### 第一階段：基礎重構（2-3週）
1. 統一策略服務接口
2. 實現基礎的領域模型
3. 重構數據存儲層

### 第二階段：核心功能改進（3-4週）
1. 實現CQRS模式
2. 重構執行引擎
3. 添加策略版本控制

### 第三階段：高級特性（4-5週）
1. 實現事件驅動架構
2. 添加策略依賴管理
3. 性能優化

### 第四階段：完善和測試（2-3週）
1. 完善文檔
2. 全面測試
3. 性能基準測試

## 風險評估

### 高風險
- 數據遷移複雜性
- 現有功能兼容性
- 性能影響

### 中風險
- 學習曲線
- 開發時間延長
- 測試覆蓋率

### 低風險
- 新功能開發
- 代碼維護性
- 系統可擴展性

## 總結

CBSC策略管理系統當前架構存在多個設計和實現問題，主要包括服務重疊、耦合度高、缺乏抽象等。通過引入DDD、CQRS、事件驅動等架構模式，可以顯著改善系統的可維護性、可擴展性和可測試性。

建議的改進方案需要分階段實施，以降低風險並確保系統穩定性。重構過程中需要特別注意數據遷移和向後兼容性問題。

通過這些改進，CBSC系統將具備：
- 清晰的職責劃分
- 更好的可擴展性
- 更高的代碼質量
- 更強的系統可靠性
- 更優的性能表現
# Phase 5.1 - 增強回測引擎實現文檔

## 概述

本文檔描述了Phase 5.1增強回測引擎的完整實現，包括4種回測模式、並行處理、數據庫集成和API服務。

## 系統架構

```
┌─────────────────────┐
│     Frontend UI     │
└─────────┬───────────┘
          │ HTTP/WebSocket
          ▼
┌─────────────────────┐
│   Backtest API      │  (FastAPI, Port 3004)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ UniversalBacktest   │
│      Engine         │
└─────────┬───────────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
┌─────────┐ ┌─────────┐
│PostgreSQL│ │ InfluxDB │
│ (Results)│ │ (Metrics)│
└─────────┘ └─────────┘
    │           │
    ▼           ▼
┌─────────────────────┐
│     Redis Cache     │
└─────────────────────┘
```

## 核心組件

### 1. UniversalBacktestEngine

主要回測引擎，支持4種回測模式：

```python
from src.backtest.universal_backtest_engine import (
    UniversalBacktestEngine,
    BacktestType,
    TaskPriority
)

# 初始化引擎
engine = UniversalBacktestEngine(
    postgres_dsn="postgresql://user:pass@localhost/backtest",
    influxdb_url="http://localhost:8086",
    redis_url="redis://localhost:6379/0",
    max_workers=4
)

await engine.initialize()

# 提交回測任務
task_id = await engine.submit_backtest(
    strategy_config={
        'strategy_id': 'momentum_strategy',
        'strategy_name': 'Momentum Strategy',
        'parameters': {
            'lookback': 20,
            'threshold': 0.02
        }
    },
    backtest_type=BacktestType.RISK_MANAGED,
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    initial_capital=1000000,
    priority=TaskPriority.HIGH
)
```

### 2. 回測模式

#### 2.1 標準回測 (Standard)
基礎的歷史數據回測，計算基本性能指標。

```python
task_id = await engine.submit_backtest(
    strategy_config=strategy_config,
    backtest_type=BacktestType.STANDARD,
    # ... 其他參數
)
```

#### 2.2 風險管理回測 (Risk-Managed)
集成實時風險監控和動態調整。

```python
task_id = await engine.submit_backtest(
    strategy_config=strategy_config,
    backtest_type=BacktestType.RISK_MANAGED,
    # 風�險參數
    var_limit=0.02,  # 2% daily VaR
    max_drawdown_limit=0.15,  # 15% max drawdown
    leverage_limit=2.0,  # 2x leverage max
)
```

#### 2.3 壓力測試 (Stress Test)
測試策略在極端市場情況下的表現。

```python
task_id = await engine.submit_backtest(
    strategy_config=strategy_config,
    backtest_type=BacktestType.STRESS_TEST,
    stress_scenarios=[
        "2008_crisis",      # 金融危機
        "covid_crash",      # COVID-19崩盤
        "dot_com_bubble",   # 互联网泡沫
        "custom_scenario"   # 自定義情境
    ]
)
```

#### 2.4 蒙地卡羅模擬 (Monte Carlo)
通過隨機路徑生成評估策略的概率分布。

```python
from src.backtest.monte_carlo import MCSimulationConfig

mc_config = MCSimulationConfig(
    n_simulations=10000,      # 模擬次數
    time_horizon=252,         # 交易日數
    confidence_levels=[0.90, 0.95, 0.99],
    return_method='bootstrap'
)

task_id = await engine.submit_backtest(
    strategy_config=strategy_config,
    backtest_type=BacktestType.MONTE_CARLO,
    monte_carlo_config=mc_config
)
```

### 3. 並行處理器

ParallelProcessor提供高性能並行執行：

```python
from src.backtest.parallel_processor import (
    ParallelProcessor,
    ExecutionMode,
    parallel_map
)

# 初始化並行處理器
processor = ParallelProcessor(
    max_workers=8,
    execution_mode=ExecutionMode.THREAD,
    enable_resource_monitoring=True
)

await processor.initialize()

# 並行處理多個任務
tasks = []
for i in range(10):
    task_id = await processor.submit_task(
        task_id=f"task_{i}",
        func=my_backtest_function,
        args=(strategy_config,),
        priority=5 if i < 3 else 2  # 前3個高優先級
    )
    tasks.append(task_id)

# 等待完成
results = await processor.wait_for_completion(tasks)
```

### 4. 數據庫集成

#### 4.1 PostgreSQL存儲

存儲回測結果和元數據：

```sql
-- 查看策略性能摘要
SELECT * FROM strategy_performance_summary
WHERE strategy_type = 'momentum'
ORDER BY avg_sharpe_ratio DESC;

-- 查看最新回測活動
SELECT * FROM recent_backtest_activity
LIMIT 20;

-- 查看頂級策略排名
SELECT * FROM top_performing_strategies
WHERE backtest_count >= 5;
```

#### 4.2 InfluxDB時序數據

存儲性能指標和風險度量：

```python
from src.backtest.influxdb_integration import InfluxDBManager, PerformanceMetric

# 初始化InfluxDB管理器
manager = InfluxDBManager(
    url="http://localhost:8086",
    token="your-token",
    org="cbsc",
    bucket="backtest_metrics"
)

await manager.initialize()

# 寫入性能指標
metrics = [
    PerformanceMetric(
        task_id="task_123",
        strategy_id="momentum_001",
        timestamp=datetime.now(),
        portfolio_value=1050000,
        daily_return=0.01,
        volatility_30d=0.15,
        sharpe_30d=1.2
    )
]

await manager.write_performance_metrics(metrics)

# 查詢性能數據
df = await manager.query_performance_metrics(
    task_id="task_123",
    fields=["portfolio_value", "sharpe_30d"]
)
```

### 5. 緩存服務

Redis緩存避免重複計算：

```python
from src.services.cache_service import (
    BacktestCache,
    CacheKey,
    cache_backtest_result
)

# 初始化緩存
cache = BacktestCache(
    redis_url="redis://localhost:6379/0",
    memory_size_mb=512,
    default_ttl=timedelta(days=7)
)

await cache.initialize()

# 手動緩存使用
cache_key = CacheKey(
    strategy_id="momentum_001",
    strategy_config={"lookback": 20},
    backtest_type="risk_managed",
    # ... 其他參數
)

# 檢查緩存
cached_result = await cache.get(cache_key)
if cached_result is None:
    # 執行回測
    result = await run_backtest()
    # 存入緩存
    await cache.set(cache_key, result, tags=["momentum", "high_priority"])

# 裝飾器方式自動緩存
@cache_backtest_result(ttl=timedelta(hours=24))
async def run_backtest_with_cache(config):
    # 回測邏輯
    pass
```

### 6. API服務

RESTful API端點：

```python
import requests

# 提交回測
response = requests.post("http://localhost:3004/api/v1/backtest", json={
    "strategy_id": "momentum_strategy",
    "strategy_name": "Momentum Strategy",
    "strategy_config": {
        "lookback": 20,
        "threshold": 0.02
    },
    "backtest_type": "risk_managed",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 1000000
})

task_id = response.json()["task_id"]

# 查詢狀態
status = requests.get(f"http://localhost:3004/api/v1/backtest/{task_id}/status")
print(status.json())

# 獲取結果
result = requests.get(f"http://localhost:3004/api/v1/backtest/{task_id}/result")
print(result.json())

# 批量提交
batch_response = requests.post("http://localhost:3004/api/v1/backtest/batch", json={
    "backtests": [
        {"strategy_id": "strategy1", "backtest_type": "standard", ...},
        {"strategy_id": "strategy2", "backtest_type": "monte_carlo", ...}
    ],
    "parallel": True
})
```

WebSocket實時更新：

```python
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    print(f"Update: {data['type']} - {data.get('task_id', '')}")

ws = websocket.WebSocketApp(
    "ws://localhost:3004/ws",
    on_message=on_message
)
ws.run_forever()
```

## 性能優化

### 1. 並行處理

- **多線程**：適合I/O密集型任務
- **多進程**：適合CPU密集型任務
- **資源監控**：動態調整並行度

```python
# CPU密集型使用多進程
processor = ParallelProcessor(
    execution_mode=ExecutionMode.PROCESS,
    max_workers=mp.cpu_count()
)

# I/O密集型使用多線程
processor = ParallelProcessor(
    execution_mode=ExecutionMode.THREAD,
    max_workers=32  # 可以高於CPU核心數
)
```

### 2. 緩存策略

- **結果緩存**：避免重複回測
- **數據緩存**：緩存市場數據
- **多級緩存**：內存 + Redis

```python
# 預熱常用配置
common_configs = [
    {"strategy_id": "momentum_20", "backtest_type": "standard"},
    {"strategy_id": "momentum_50", "backtest_type": "risk_managed"},
]

await warm_cache(cache, strategy_configs, common_configs)
```

### 3. 數據庫優化

- **分區表**：按時間分區大表
- **索引**：關鍵查詢字段建立索引
- **批量操作**：減少數據庫往返

```sql
-- 分區表示例
CREATE TABLE backtest_results_y2024 PARTITION OF backtest_results
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- 查詢優化
EXPLAIN ANALYZE
SELECT * FROM backtest_results
WHERE strategy_id = 'momentum_001'
  AND created_at > '2024-01-01'
ORDER BY sharpe_ratio DESC
LIMIT 10;
```

## 監控和日誌

### 1. 性能指標

```python
# 獲取引擎統計
stats = await engine.get_statistics()
print(f"Completed: {stats['stats']['completed_tasks']}")
print(f"Failed: {stats['stats']['failed_tasks']}")
print(f"Cache hit rate: {stats['stats']['cache_hits'] / (stats['stats']['cache_hits'] + stats['stats']['cache_misses']):.2%}")

# 獲取緩存統計
cache_stats = await cache.get_stats()
print(f"Cache size: {cache_stats.total_size_bytes / 1024 / 1024:.1f} MB")
print(f"Hit rate: {cache_stats.hit_rate:.2%}")
```

### 2. 錯誤處理

```python
# 任務失敗重試
task = BacktestTask(
    max_retries=3,  # 最多重試3次
    retry_count=0
)

# 異常捕獲
try:
    result = await engine.run_backtest(strategy, data)
except TimeoutError:
    logger.error("Backtest timed out")
except MemoryError:
    logger.error("Insufficient memory")
except Exception as e:
    logger.error(f"Backtest failed: {e}", exc_info=True)
```

### 3. 日誌配置

```python
import logging

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backtest.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("backtest")
```

## 最佳實踐

### 1. 任務設計

- **原子性**：每個任務獨立可重試
- **冪等性**：多次執行結果一致
- **超時控制**：防止長時間運行

```python
# 良好的任務設計
async def run_backtest_task(config):
    # 參數驗證
    if not validate_config(config):
        raise ValueError("Invalid configuration")

    # 資源檢查
    if not check_resources():
        raise ResourceError("Insufficient resources")

    # 執行回測
    result = await execute_backtest(config)

    return result
```

### 2. 策略開發

- **模塊化**：清晰的策略接口
- **可測試**：單元測試覆蓋
- **文檔**：完整的策略說明

```python
class BacktestStrategy(ABC):
    @abstractmethod
    async def initialize(self, config):
        """初始化策略"""
        pass

    @abstractmethod
    async def process_data(self, data):
        """處理數據"""
        pass

    @abstractmethod
    async def generate_signals(self):
        """生成交易信號"""
        pass
```

### 3. 資源管理

- **監控使用量**：CPU、內存、磁盤
- **限制並發度**：避免系統過載
- **清理資源**：及時釋放不用的資源

```python
# 資源監控
import psutil

def monitor_resources():
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    logger.info(f"CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%")

    if memory.percent > 90:
        logger.warning("High memory usage detected")
```

## 故障排除

### 常見問題

1. **任務超時**
   - 檢查數據量是否過大
   - 增加超時時間
   - 優化算法

2. **內存不足**
   - 減少並行任務數
   - 使用流式處理
   - 增加系統內存

3. **數據庫連接失敗**
   - 檢查連接字符串
   - 確認服務運行
   - 檢查防火牆設置

4. **緩存未命中**
   - 檢查緩存配置
   - 驗證緩存鍵生成
   - 清理過期緩存

### 調試技巧

```python
# 開啟詳細日誌
import logging
logging.getLogger("backtest").setLevel(logging.DEBUG)

# 使用調試器
import pdb; pdb.set_trace()

# 性能分析
import cProfile
cProfile.run("my_backtest_function()", "profile.stats")
```

## 未來擴展

1. **分布式計算**：支持多機集群
2. **GPU加速**：深度學習策略
3. **實時回測**：流式數據處理
4. **可視化**：交互式報告
5. **自動化**：策略自動優化

## 總結

Phase 5.1增強回測引擎提供了：

- ✅ 4種回測模式（標準、風險管理、壓力測試、蒙地卡羅）
- ✅ 高性能並行處理
- ✅ PostgreSQL和InfluxDB集成
- ✅ Redis緩存系統
- ✅ RESTful API和WebSocket
- ✅ 完整的測試覆蓋
- ✅ 詳細的文檔說明

系統設計考慮了可擴展性、高性能和易用性，為量化策略回測提供了強大的基礎設施。
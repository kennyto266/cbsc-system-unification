# Strategy Factory Best Practices Guide
# 策略工廠最佳實踐指南

## 概述

本文檔提供了使用 Strategy Factory v2.0 的最佳實踐建議，幫助開發者構建高效、可靠、可維護的交易策略系統。

## 架構原則

### 1. 單一職責原則
每個策略類應該專注於一個特定的交易邏輯：

```python
# ✅ 好的設計 - 專注於移動平均交叉
class MACrossoverStrategy(BaseTechnicalIndicatorStrategy):
    """移動平均交叉策略"""
    STRATEGY_NAME = "ma_crossover"
    # ... 實現

# ❌ 避免 - 混合多種邏輯
class MultiSignalStrategy(BaseStrategy):
    """混合多種信號 - 違反單一職責"""
    # 包含MA、RSI、MACD等多種邏輯
```

### 2. 開閉原則
對擴展開放，對修改關閉：

```python
# ✅ 使用工廠模式擴展新策略
VOLUME_STRATEGIES = {
    "obv": OBVStrategy,
    "vwap": VWAPStrategy,
    "mfi": MFIStrategy,
    "new_volume_indicator": NewVolumeStrategy  # 新策略只需添加
}

# ❌ 避免修改核心工廠代碼
```

### 3. 依賴注入
通過配置參數注入依賴：

```python
# ✅ 好的設計
strategy = factory.create_strategy("ma_crossover", {
    "fast_period": 10,
    "slow_period": 20,
    "symbols": ["AAPL"],
    "data_provider": custom_provider  # 注入自定義數據源
})

# ❌ 避免硬編碼依賴
```

## 性能優化

### 1. 策略實例管理

```python
# ✅ 重用策略實例
class StrategyManager:
    def __init__(self):
        self._strategy_cache = {}

    def get_strategy(self, name: str, config: dict):
        key = f"{name}_{hash(tuple(sorted(config.items())))}"
        if key not in self._strategy_cache:
            self._strategy_cache[key] = create_strategy(name, config)
        return self._strategy_cache[key]

# ❌ 避免重複創建相同實例
```

### 2. 批量操作

```python
# ✅ 使用批量創建
configs = [
    {"name": "ma_crossover", "fast_period": 10},
    {"name": "rsi", "period": 14},
    {"name": "adx", "period": 14}
]
strategies = factory.create_strategy_batch(configs)

# ❌ 避免循環創建
strategies = []
for config in configs:
    strategy = factory.create_strategy(config["name"], config)
    strategies.append(strategy)
```

### 3. 數據預處理

```python
# ✅ 預處理和緩存數據
class DataCache:
    def __init__(self):
        self._cache = {}

    def get_data(self, symbol: str, period: int):
        if symbol not in self._cache:
            self._cache[symbol] = self._load_data(symbol)
        return self._cache[symbol].tail(period)

# ❌ 避免每次執行都重新加載數據
```

## 配置管理

### 1. 環境分離

```python
# ✅ 使用配置文件
# config/production.json
{
    "strategies": {
        "ma_crossover": {
            "fast_period": 20,
            "slow_period": 50
        }
    }
}

# config/development.json
{
    "strategies": {
        "ma_crossover": {
            "fast_period": 10,
            "slow_period": 20
        }
    }
}
```

### 2. 參數驗證

```python
# ✅ 創建前驗證
result = factory.validate_strategy_config("ma_crossover", config)
if not result['valid']:
    raise ValueError(f"無效配置: {result['errors']}")

strategy = factory.create_strategy("ma_crossover", config)

# ❌ 避免創建後發現錯誤
```

### 3. 默認配置

```python
# ✅ 提供合理的默認值
DEFAULT_CONFIGS = {
    "ma_crossover": {
        "fast_period": 10,
        "slow_period": 20,
        "symbols": ["SPY"]
    }
}

# 使用默認配置
config = DEFAULT_CONFIGS["ma_crossover"].copy()
config.update(user_config)
```

## 錯誤處理

### 1. 優雅降級

```python
# ✅ 策略執行失敗時返回空信號
class RobustStrategy(BaseStrategy):
    def execute(self, data):
        try:
            return super().execute(data)
        except Exception as e:
            logger.error(f"策略執行失敗: {e}")
            return {
                "strategy_name": self.STRATEGY_NAME,
                "results": {symbol: {"signals": pd.DataFrame()} for symbol in data},
                "error": str(e)
            }
```

### 2. 資源清理

```python
# ✅ 使用上下文管理器
class StrategyContext:
    def __enter__(self):
        self.strategy = create_strategy("ma_crossover", config)
        return self.strategy

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 清理資源
        if hasattr(self.strategy, 'cleanup'):
            self.strategy.cleanup()

# 使用
with StrategyContext() as strategy:
    result = strategy.execute(data)
```

### 3. 超時控制

```python
# ✅ 設置執行超時
import signal
from contextlib import contextmanager

@contextmanager
def timeout_context(seconds):
    def timeout_handler(signum, frame):
        raise TimeoutError(f"操作超時 ({seconds}秒)")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        signal.alarm(0)

# 使用
try:
    with timeout_context(5):
        result = strategy.execute(data)
except TimeoutError:
    logger.error("策略執行超時")
```

## 測試策略

### 1. 單元測試

```python
# ✅ 測試策略邏輯
def test_ma_crossover_signal_generation():
    # 準備測試數據
    data = create_test_data()

    # 創建策略
    strategy = create_strategy("ma_crossover", {
        "fast_period": 5,
        "slow_period": 10
    })

    # 驗證信號生成
    signals = strategy.generate_signals(data)

    # 斷言
    assert "ma_signal" in signals.columns
    assert len(signals) == len(data)
```

### 2. 集成測試

```python
# ✅ 測試工廠集成
def test_factory_integration():
    factory = StrategyFactoryV2()

    # 測試批量創建
    configs = [
        {"name": "ma_crossover", "fast_period": 10},
        {"name": "rsi", "period": 14}
    ]

    strategies = factory.create_strategy_batch(configs)

    # 驗證所有策略都能執行
    data = {"TEST": create_test_data()}
    for strategy in strategies:
        result = strategy.execute(data)
        assert "results" in result
```

### 3. 性能測試

```python
# ✅ 測試執行性能
def test_strategy_performance():
    strategy = create_strategy("ma_crossover", config)
    data = create_large_dataset()

    start_time = time.time()
    result = strategy.execute(data)
    execution_time = time.time() - start_time

    # 斷言性能要求
    assert execution_time < 1.0, "執行時間超過1秒"
```

## 監控和日誌

### 1. 結構化日誌

```python
# ✅ 使用結構化日誌
import structlog

logger = structlog.get_logger()

class LoggingStrategy(BaseStrategy):
    def execute(self, data):
        logger.info(
            "strategy_execution_started",
            strategy=self.STRATEGY_NAME,
            symbols=list(data.keys()),
            data_points={symbol: len(df) for symbol, df in data.items()}
        )

        result = super().execute(data)

        logger.info(
            "strategy_execution_completed",
            strategy=self.STRATEGY_NAME,
            execution_time=result["execution_time"],
            signals_generated=sum(len(r["signals"]) for r in result["results"].values())
        )

        return result
```

### 2. 性能指標

```python
# ✅ 收集性能指標
from prometheus_client import Counter, Histogram

strategy_executions = Counter(
    'strategy_executions_total',
    'Total strategy executions',
    ['strategy_name', 'status']
)

execution_duration = Histogram(
    'strategy_execution_duration_seconds',
    'Strategy execution duration',
    ['strategy_name']
)

class MetricsStrategy(BaseStrategy):
    def execute(self, data):
        start_time = time.time()

        try:
            result = super().execute(data)
            strategy_executions.labels(
                strategy_name=self.STRATEGY_NAME,
                status='success'
            ).inc()
            return result
        except Exception as e:
            strategy_executions.labels(
                strategy_name=self.STRATEGY_NAME,
                status='error'
            ).inc()
            raise
        finally:
            execution_duration.labels(
                strategy_name=self.STRATEGY_NAME
            ).observe(time.time() - start_time)
```

### 3. 健康檢查

```python
# ✅ 實現健康檢查端點
class StrategyHealthCheck:
    def __init__(self, factory: StrategyFactoryV2):
        self.factory = factory

    def check_health(self) -> dict:
        health_status = {
            "status": "healthy",
            "strategies": {},
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            # 測試每個策略類型
            for strategy_type in StrategyType:
                strategies = self.factory.get_strategies_by_type(strategy_type)
                if strategies:
                    # 嘗試創建一個實例
                    strategy_name = list(strategies.keys())[0]
                    try:
                        strategy = self.factory.create_strategy(strategy_name, {})
                        health_status["strategies"][strategy_type.value] = "ok"
                    except Exception as e:
                        health_status["strategies"][strategy_type.value] = f"error: {e}"
                        health_status["status"] = "degraded"

            return health_status
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
```

## 部署建議

### 1. 容器化

```dockerfile
# ✅ 多階段構建
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY src/ ./src/

# 非root用戶
RUN useradd --create-home --shell /bin/bash strategy
USER strategy

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 配置管理

```yaml
# ✅ Kubernetes配置示例
apiVersion: v1
kind: ConfigMap
metadata:
  name: strategy-config
data:
  config.yaml: |
    strategies:
      ma_crossover:
        fast_period: 20
        slow_period: 50
      rsi:
        period: 14
        oversold: 30
        overbought: 70
```

### 3. 資源限制

```yaml
# ✅ 資源限制
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: strategy-service
    image: strategy-service:latest
    resources:
      requests:
        memory: "512Mi"
        cpu: "250m"
      limits:
        memory: "1Gi"
        cpu: "500m"
```

## 總結

遵循這些最佳實踐可以幫助您：

1. **提高性能**：通過合理的緩存、批量操作和資源管理
2. **增強可靠性**：通過完善的錯誤處理和優雅降級
3. **簡化維護**：通過清晰的架構設計和全面的測試
4. **便於監控**：通過結構化日誌和性能指標
5. **支持擴展**：通過模塊化設計和配置管理

始終記住：簡單性是關鍵。在添加復雜性之前，先考慮是否真的需要它。
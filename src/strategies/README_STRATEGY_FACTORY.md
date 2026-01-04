# Strategy Factory v2.0 Usage Guide
# 策略工廠使用指南

## 概述

Strategy Factory v2.0 是一個統一的策略創建和管理工廠，支持所有類型的交易策略：

- **技術指標策略** (Technical Indicator)
- **動量策略** (Momentum)
- **成交量策略** (Volume)
- **遺留策略** (Legacy - 向後兼容)

## 基本使用

### 1. 導入策略工廠

```python
from strategies.enhanced_factory_v2 import (
    StrategyFactoryV2,
    create_strategy,
    get_available_strategies,
    get_strategies_by_type
)

# 或者使用全局實例
from strategies.enhanced_factory_v2 import strategy_factory
```

### 2. 獲取可用策略

```python
# 獲取所有策略
all_strategies = get_available_strategies()
print(f"Total strategies: {len(all_strategies)}")

# 顯示策略列表
for name, metadata in all_strategies.items():
    print(f"{name}: {metadata.description} ({metadata.strategy_type.value})")
```

### 3. 按類型獲取策略

```python
from strategies.enhanced_factory import StrategyType

# 獲取技術指標策略
technical_strategies = get_strategies_by_type(StrategyType.TECHNICAL_ANALYSIS)
print(f"Technical strategies: {list(technical_strategies.keys())}")

# 獲取動量策略
momentum_strategies = get_strategies_by_type(StrategyType.MOMENTUM)
print(f"Momentum strategies: {list(momentum_strategies.keys())}")

# 獲取成交量策略
volume_strategies = get_strategies_by_type(StrategyType.VOLUME)
print(f"Volume strategies: {list(volume_strategies.keys())}")
```

### 4. 創建策略實例

#### 基本創建

```python
# 創建MA交叉策略
ma_strategy = create_strategy("ma_crossover", {
    "fast_period": 10,
    "slow_period": 20,
    "symbols": ["SPY", "QQQ"],
    "position_size": 0.1
})

# 創建ADX策略
adx_strategy = create_strategy("adx", {
    "period": 14,
    "trend_threshold": 25,
    "symbols": ["SPY"]
})

# 創建OBV策略
obv_strategy = create_strategy("obv", {
    "ma_period": 20,
    "divergence_period": 10,
    "symbols": ["SPY"]
})
```

#### 使用工廠實例

```python
factory = StrategyFactoryV2()

# 獲取策略信息
metadata = factory.get_strategy_info("ma_crossover")
print(f"Strategy: {metadata.name}")
print(f"Type: {metadata.strategy_type}")
print(f"Description: {metadata.description}")

# 創建策略
strategy = factory.create_strategy("ma_crossover", {
    "fast_period": 12,
    "slow_period": 26,
    "symbols": ["SPY", "QQQ", "IWM"],
    "position_size": 0.05
}, instance_id="my_strategy_001")
```

### 5. 批量創建策略

```python
configs = [
    {
        "name": "ma_crossover",
        "fast_period": 10,
        "slow_period": 20,
        "symbols": ["SPY"]
    },
    {
        "name": "adx",
        "period": 14,
        "trend_threshold": 25,
        "symbols": ["SPY"]
    },
    {
        "name": "rsi",
        "period": 14,
        "oversold_threshold": 30,
        "overbought_threshold": 70,
        "symbols": ["SPY"]
    }
]

strategies = factory.create_strategy_batch(configs)
print(f"Created {len(strategies)} strategies")
```

## 高級功能

### 1. 策略配置驗證

```python
# 驗證配置
config = {"period": 14, "trend_threshold": 25}
result = factory.validate_strategy_config("adx", config)

if result['valid']:
    print("Configuration is valid")
else:
    print("Configuration errors:")
    for error in result['errors']:
        print(f"  - {error}")
```

### 2. 策略搜索

```python
# 搜索移動平均相關策略
ma_strategies = factory.search_strategies("ma")
print(f"Found {len(ma_strategies)} MA strategies")

# 搜索成交量相關策略
volume_strategies = factory.search_strategies("volume")
print(f"Found {len(volume_strategies)} volume strategies")
```

### 3. 配置模板導出

```python
# 導出策略配置模板
template = factory.export_strategy_config("ma_crossover")

print("Strategy Configuration Template:")
print(f"Name: {template['name']}")
print(f"Type: {template['type']}")
print(f"Parameters: {template['parameters']}")
print(f"Required: {template['required_parameters']}")
print(f"Optional: {template['optional_parameters']}")
```

### 4. 策略統計

```python
# 獲取工廠統計
stats = factory.get_strategy_stats()

print(f"Total strategies: {stats['total_strategies']}")
print("Strategies by type:")
for strategy_type, count in stats['by_type'].items():
    print(f"  {strategy_type}: {count}")
```

## 策略執行

### 1. 準備數據

```python
import pandas as pd
import numpy as np

# 創建測試數據
def create_sample_data():
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    data = []

    for date in dates:
        price = 100 + np.random.normal(0, 2)
        data.append({
            "date": date,
            "open": price,
            "high": price * (1 + abs(np.random.normal(0, 0.02))),
            "low": price * (1 - abs(np.random.normal(0, 0.02))),
            "close": price,
            "volume": np.random.randint(1000000, 5000000)
        })

    df = pd.DataFrame(data)
    df.set_index("date", inplace=True)
    return df

data = {"SPY": create_sample_data()}
```

### 2. 執行單個策略

```python
# 創建並執行策略
strategy = create_strategy("ma_crossover", {
    "fast_period": 10,
    "slow_period": 20,
    "symbols": ["SPY"]
})

result = strategy.execute(data)

print(f"Strategy: {result['strategy_name']}")
print(f"Execution time: {result['execution_time']}")
print(f"Results: {list(result['results'].keys())}")
```

### 3. 執行多個策略

```python
# 批量創建策略
configs = [
    {"name": "ma_crossover", "fast_period": 10, "slow_period": 20},
    {"name": "adx", "period": 14, "trend_threshold": 25},
    {"name": "obv", "ma_period": 20, "divergence_period": 10}
]

strategies = factory.create_strategy_batch(configs)

# 執行所有策略
for strategy in strategies:
    result = strategy.execute(data)
    print(f"{strategy.STRATEGY_NAME}: Generated signals")
```

## 可用策略列表

### 技術指標策略

- `ma_crossover`: 移動平均線交叉策略
- `rsi`: 相對強弱指標策略
- `macd`: 移動平均收斂發散策略
- `bollinger_bands`: 布林帶策略

### 動量策略

- `adx`: 平均方向指標策略
- `sar`: 抛物線SAR策略

### 成交量策略

- `obv`: 能量潮策略
- `vwap`: 成交量加權平均價格策略
- `mfi`: 資金流指標策略

### 遺留策略

- `adx_legacy`: 遺留ADX策略
- `obv_legacy`: 遺留OBV策略
- `vwap_legacy`: 遺留VWAP策略
- `mfi_legacy`: 遺留MFI策略
- `vpt`: 價量趨勢策略

## 最佳實踐

### 1. 配置驗證

```python
# 創建策略前始終驗證配置
result = factory.validate_strategy_config("ma_crossover", config)
if not result['valid']:
    raise ValueError(f"Invalid configuration: {result['errors']}")
```

### 2. 錯誤處理

```python
try:
    strategy = factory.create_strategy("ma_crossover", config)
except ValueError as e:
    logger.error(f"Failed to create strategy: {e}")
    # 使用默認配置或跳過該策略
```

### 3. 資源管理

```python
# 清理策略實例緩存
factory.cleanup_strategy_instances()

# 適免創建過多實例
if len(factory._strategy_instances) > 100:
    factory.cleanup_strategy_instances()
```

### 4. 配置模板

```python
# 使用配置模板確保參數正確
template = factory.export_strategy_config("ma_crossover")
default_config = template["parameters"]

# 基於模板創建自定義配置
custom_config = default_config.copy()
custom_config["fast_period"] = 8
custom_config["slow_period"] = 16

strategy = factory.create_strategy("ma_crossover", custom_config)
```

## 注意事項

1. **策略名稱區分大小寫**
2. **必需參數必須提供**
3. **參數範圍會自動驗證**
4. **遺留策略用於向後兼容**
5. **批量創建時無效配置會被跳過**

## 故障排除

### 常見錯誤

1. **Strategy 'xxx' not found**
   - 檢查策略名稱是否正確
   - 使用 `get_available_strategies()` 查看可用策略

2. **Missing required parameter**
   - 檢查必需參數列表
   - 使用 `export_strategy_config()` 查看默認參數

3. **Parameter must be of type**
   - 檢查參數類型是否正確
   - 參考可選參數定義

4. **Failed to create strategy**
   - 檢查配置參數
   - 查看具體錯誤信息
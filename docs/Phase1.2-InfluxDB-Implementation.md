# InfluxDB 時序數據庫實現文檔
# InfluxDB Time-Series Database Implementation

## 概述 / Overview

本文檔描述了 CBSC 量化交易策略管理系統的 InfluxDB 時序數據庫配置和實現。該實現包括市場數據存儲、策略性能指標、風險指標以及系統監控。

This document describes the InfluxDB time-series database configuration and implementation for the CBSC quantitative trading strategy management system. The implementation includes market data storage, strategy performance metrics, risk indicators, and system monitoring.

## 架構 / Architecture

### 組件結構 / Component Structure

```
src/
├── config/
│   └── influxdb_config.py          # 配置管理 / Configuration Management
├── services/
│   ├── influxdb_client.py          # InfluxDB 客戶端 / InfluxDB Client
│   ├── influxdb_monitoring.py      # 監控服務 / Monitoring Service
│   └── influxdb_retention_manager.py # 保留策略管理 / Retention Policy Manager
├── utils/
│   └── influxdb_utils.py           # 實用工具函數 / Utility Functions
├── migrations/scripts/
│   └── 005_influxdb_schema_setup.py # Schema 設置腳本 / Schema Setup Script
└── tests/
    └── test_influxdb_integration.py # 集成測試 / Integration Tests
```

## 配置 / Configuration

### 環境變量 / Environment Variables

```bash
# InfluxDB 連接配置
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_influxdb_token
INFLUXDB_ORG=cbsc

# 性能配置
INFLUXDB_BATCH_SIZE=1000
INFLUXDB_FLUSH_INTERVAL=1000

# 緩存配置
REDIS_CLIENT=redis://localhost:6379
INFLUXDB_CACHE_ENABLED=true
```

### 存儲桶配置 / Bucket Configuration

| 存儲桶 / Bucket | 描述 / Description | 保留期 / Retention | 分片時長 / Shard Duration |
|----------------|-------------------|-------------------|-------------------------|
| market_data_raw | 原始市場數據（分鐘級） | 90 天 | 1 天 |
| market_data_hourly | 小時級聚合市場數據 | 2 年 | 7 天 |
| market_data_daily | 日級聚合市場數據 | 10 年 | 30 天 |
| strategy_performance | 策略性能指標 | 5 年 | 7 天 |
| risk_metrics | 風險計算結果 | 5 年 | 7 天 |
| trading_signals | 交易信號 | 2 年 | 1 天 |
| system_metrics | 系統監控指標 | 30 天 | 1 小時 |

## 使用方法 / Usage

### 初始化 / Initialization

```python
from src.services.influxdb_client import create_influxdb_manager
from src.config.influxdb_config import get_config

# 加載配置
config = get_config()

# 創建並初始化管理器
manager = await create_influxdb_manager(config.connection)
```

### 寫入市場數據 / Writing Market Data

```python
from src.utils.influxdb_utils import MarketDataWriter

# 創建寫入器
writer = MarketDataWriter(manager)

# 寫入 OHLCV 數據
ohlcv_data = [
    {
        "timestamp": datetime.utcnow(),
        "open": 150.0,
        "high": 155.0,
        "low": 149.0,
        "close": 152.0,
        "volume": 1000000
    }
]

await writer.write_ohlcv(
    symbol="AAPL",
    exchange="NASDAQ",
    ohlcv_data=ohlcv_data
)
```

### 查詢數據 / Querying Data

```python
from src.utils.influxdb_utils import DataQueryHelper

# 創建查詢助手
query_helper = DataQueryHelper(manager)

# 查詢價格數據
prices = await query_helper.get_symbol_prices(
    symbol="AAPL",
    start=datetime.utcnow() - timedelta(days=30)
)
```

### 寫入策略性能 / Writing Strategy Performance

```python
from src.utils.influxdb_utils import StrategyPerformanceWriter

# 創建性能寫入器
perf_writer = StrategyPerformanceWriter(manager)

# 寫入每日回報
returns = [(datetime.utcnow(), 0.01)]
await perf_writer.write_daily_returns(
    strategy_id="strategy-001",
    strategy_name="My Strategy",
    returns=returns
)
```

### 監控和健康檢查 / Monitoring and Health Checks

```python
from src.services.influxdb_monitoring import InfluxDBMonitor

# 創建監控器
monitor = InfluxDBMonitor(manager)

# 開始監控
await monitor.start_monitoring()

# 獲取指標摘要
metrics = monitor.get_metrics_summary()
print(metrics)

# 停止監控
await monitor.stop_monitoring()
```

## 數據模型 / Data Models

### 市場數據 / Market Data

```
Measurement: stock_price
Tags:
  - symbol: 股票代碼
  - exchange: 交易所
  - currency: 貨幣
  - market: 市場類型
Fields:
  - open: 開盤價
  - high: 最高價
  - low: 最低價
  - close: 收盤價
  - volume: 成交量
  - vwap: 成交量加權平均價
```

### 策略性能 / Strategy Performance

```
Measurement: strategy_returns
Tags:
  - strategy_id: 策略 ID
  - strategy_name: 策略名稱
  - frequency: 計算頻率
Fields:
  - daily_return: 日回報率
  - total_return: 總回報率
  - excess_return: 超額回報
  - volatility: 波動率
  - sharpe_ratio: 夏普比率
```

### 風險指標 / Risk Metrics

```
Measurement: strategy_risk
Tags:
  - strategy_id: 策略 ID
  - risk_type: 風險類型
  - confidence_level: 置信水平
Fields:
  - value: 風險指標值
  - var: 風險值
  - expected_shortfall: 預期損失
  - maximum_drawdown: 最大回撤
```

## 數據保留策略 / Data Retention Policies

### 自動下採樣 / Automatic Downsampling

系統自動實施以下下採樣策略：

1. **原始到小時級**：每小時運行一次，將原始分鐘數據聚合為小時數據
2. **小時級到日級**：每天運行一次，將小時數據聚合為日數據
3. **策略性能聚合**：每周運行一次，聚合策略性能指標

### 數據清理 / Data Cleanup

- 系統指標：30 天後自動刪除
- 原始市場數據：90 天後自動刪除（已下採樣）
- 交易信號：2 年後自動刪除
- 策略和風險數據：5 年後自動刪除

## 性能優化 / Performance Optimization

### 批量操作 / Batch Operations

- 寫入操作使用批量處理，默認批量大小為 1000
- 異步寫入提高吞吐量
- 自動重試機制處理臨時故障

### 緩存策略 / Caching Strategy

- 最新價格緩存 60 秒
- 策略摘要緩存 5 分鐘
- 市場概覽緩存 10 分鐘
- 查詢結果緩存 3 分鐘

### 查詢優化 / Query Optimization

- 使用適當的時間範圍限制
- 利用標籤索引加速查詢
- 預聚合常用指標

## 監控和警報 / Monitoring and Alerts

### 健康檢查 / Health Checks

系統自動監控以下組件：

1. **InfluxDB 連接**：響應時間、可用性
2. **Redis 緩存**：連接狀態、性能指標
3. **系統資源**：CPU、內存、磁盤使用率

### 性能指標 / Performance Metrics

- 寫入操作計數和延遲
- 查詢響應時間
- 錯誤率
- 數據點計數

## 測試 / Testing

### 運行集成測試 / Running Integration Tests

```bash
# 安裝依賴
pip install -r requirements.txt

# 設置環境變量
export INFLUXDB_TOKEN=your_token

# 運行測試
python tests/test_influxdb_integration.py
```

### 測試覆蓋 / Test Coverage

- 存儲桶創建和配置
- 數據寫入和讀取
- 並發操作
- 錯誤處理
- 性能指標收集
- 數據質量驗證

## 故障排除 / Troubleshooting

### 常見問題 / Common Issues

1. **連接失敗**：檢查 InfluxDB URL 和 Token
2. **寫入失敗**：驗證存儲桶權限和數據格式
3. **查詢慢**：檢查時間範圍和索引使用
4. **內存使用高**：調整批量大小和刷新間隔

### 日志級別 / Log Levels

```python
import logging
logging.getLogger('influxdb_client').setLevel(logging.INFO)
```

## 安全考慮 / Security Considerations

### Token 管理 / Token Management

- 使用環境變量存儲 Token
- 定期輪換認證令牌
- 使用最小權限原則

### 網絡安全 / Network Security

- 在生產環境中使用 HTTPS
- 配置防火牆規則
- 限制網絡訪問

## 擴展和維護 / Scaling and Maintenance

### 水平擴展 / Horizontal Scaling

- 配置多個 InfluxDB 節點
- 使用負載均衡器
- 分片策略

### 維護任務 / Maintenance Tasks

```python
# 創建保留策略管理器
from src.services.influxdb_retention_manager import InfluxDBRetentionManager

retention_manager = InfluxDBRetentionManager(client, org)

# 應用保留策略
await retention_manager.apply_retention_policies()

# 獲取保留狀態
status = await retention_manager.get_retention_status()
```

## 版本歷史 / Version History

- **v1.0.0** (2025-12-18): 初始實現
  - 基本連接和寫入功能
  - 監控和保留策略
  - 實用工具函數

## 貢獻 / Contributing

提交更改前請確保：

1. 所有測試通過
2. 代碼遵循項目風格指南
3. 添加適當的文檔
4. 更新相關的測試用例

## 許可證 / License

本項目採用 MIT 許可證。

---

*最後更新：2025-12-18*
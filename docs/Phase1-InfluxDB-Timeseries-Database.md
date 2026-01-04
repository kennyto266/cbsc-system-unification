# Phase 1.2 InfluxDB時序數據庫配置文檔

## 概述

本文檔描述了CBSC量化策略管理系統中InfluxDB時序數據庫的完整配置，包括數據架構設計、性能優化、數據保留策略和系統整合。

## 架構設計

### 1. 數據庫架構

```
┌─────────────────────────────────────────────────────────────┐
│                     CBSC 時序數據架構                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  市場數據層   │    │  策略數據層   │    │  系統數據層   │ │
│  │             │    │             │    │             │ │
│  │ • OHLCV數據  │    │ • 性能指標    │    │ • API性能    │ │
│  │ • 技術指標   │    │ • 風險指標    │    │ • 數據庫性能   │ │
│  │ • 交易信號   │    │ • 交易統計    │    │ • 系統監控    │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                        InfluxDB 2.7                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   原始數據桶   │  │   聚合數據桶   │  │   性能數據桶   │     │
│  │ 90天保留期   │  │  2年保留期    │  │  5年保留期    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 2. 核心組件

#### 2.1 InfluxDB服務
- **版本**: InfluxDB 2.7
- **端口**: 8086
- **組織**: cbsc
- **主桶**: market_data

#### 2.2 輔助服務
- **Telegraf**: 數據收集和監控
- **Kapacitor**: 告警和數據處理
- **Grafana**: 數據可視化
- **Redis**: 緩存和會話存儲

## 數據模型設計

### 1. 市場數據模型

#### 1.1 股票價格數據 (stock_price)
```flux
stock_price,symbol=AAPL,exchange=NASDAQ,currency=USD,data_source=yahoo,quality=real_time
  open=150.25,high=152.75,low=149.50,close=152.10,volume=52341000 1609459200000000000
```

**標籤 (Tags)**:
- `symbol`: 股票代碼
- `exchange`: 交易所名稱
- `currency`: 貨幣代碼
- `data_source`: 數據源
- `quality`: 數據質量標記

**字段 (Fields)**:
- `open`: 開盤價
- `high`: 最高價
- `low`: 最低價
- `close`: 收盤價
- `volume`: 成交量
- `vwap`: 成交量加權平均價

#### 1.2 技術指標 (technical_indicators)
```flux
technical_indicators,symbol=AAPL,indicator_type=ma,indicator_name=SMA_20,timeframe=1d
  value=152.34,signal=neutral,confidence=0.75 1609459200000000000
```

**標籤**:
- `symbol`: 股票代碼
- `indicator_type`: 指標類型
- `indicator_name`: 指標名稱
- `timeframe`: 時間框架

**字段**:
- `value`: 指標值
- `signal`: 交易信號
- `confidence`: 信號置信度
- `upper_band`: 上軌（如布林帶）
- `lower_band`: 下軌（如布林帶）

### 2. 策略性能模型

#### 2.1 策略回報 (strategy_returns)
```flux
strategy_returns,strategy_id=strategy-001,strategy_name=MA_Crossover,user_id=admin-001
  total_return=0.1523,daily_return=0.0012,alpha=0.0234,beta=0.9876 1609459200000000000
```

#### 2.2 風險指標 (strategy_risk)
```flux
strategy_risk,strategy_id=strategy-001,risk_type=var,confidence_level=95,time_horizon=1
  value=0.0234,var_95=0.0212,expected_shortfall=0.0256,max_drawdown=0.0821 1609459200000000000
```

### 3. 系統監控模型

#### 3.1 API性能 (api_performance)
```flux
api_performance,endpoint=/api/strategies,method=GET,status_code=200
  response_time=125.5,request_count=100,error_rate=0.02 1609459200000000000
```

## 數據保留策略

### 1. 桶配置

| 桶名稱 | 保留期 | 用途 | 分片持續時間 |
|--------|--------|------|-------------|
| market_data_raw | 90天 | 原始市場數據（分鐘級） | 1天 |
| market_data_hourly | 2年 | 聚合市場數據（小時級） | 7天 |
| market_data_daily | 10年 | 聚合市場數據（日級） | 30天 |
| strategy_performance | 5年 | 策略性能指標 | 7天 |
| risk_metrics | 5年 | 風險指標數據 | 7天 |
| trading_signals | 2年 | 交易信號和訂單 | 1天 |
| system_metrics | 30天 | 系統監控指標 | 1小時 |

### 2. 降採樣任務

#### 2.1 分鐘級到小時級
- 執行頻率：每小時
- 聚合規則：
  - Open: 首個值
  - High: 最大值
  - Low: 最小值
  - Close: 最後值
  - Volume: 總和

#### 2.2 小時級到日級
- 執行頻率：每日
- 聚合規則：同上

### 3. 自動清理任務

- 原始市場數據：90天後自動刪除
- 系統指標：30天後自動刪除
- 技術指標：保留最新值，清理歷史值

## 性能優化

### 1. 查詢優化

#### 1.1 索引策略
對高頻查詢標籤建立索引：
- symbol
- exchange
- strategy_id
- user_id
- indicator_type

#### 1.2 查詢模式優化
```flux
// ✅ 優化查詢 - 使用時間範圍限制
from(bucket: "market_data_raw")
  |> range(start: -1h)
  |> filter(fn: (r) => r.symbol == "AAPL")
  |> filter(fn: (r) => r._measurement == "stock_price")
  |> last()

// ❌ 避免全表掃描
from(bucket: "market_data_raw")
  |> filter(fn: (r) => r.symbol == "AAPL")  // 缺少時間範圍
```

### 2. 寫入優化

#### 2.1 批量寫入
- 批次大小：1000個數據點
- 刷新間隔：1000毫秒
- 使用異步寫入模式

#### 2.2 連接池配置
- 最大連接數：10
- 連接超時：30秒
- 重試次數：3次

### 3. 壓縮策略
- 啟用GZIP壓縮（閾值：1000字節）
- 使用Protocol Buffers序列化

## 系統整合

### 1. 與PostgreSQL整合

#### 1.1 元數據存儲
- PostgreSQL存儲：策略定義、用戶信息、配置數據
- InfluxDB存儲：時序數據、性能指標、監控數據

#### 1.2 數據同步
```python
# 策略元數據查詢示例
async def get_strategy_with_performance(strategy_id: str):
    # 從PostgreSQL獲取策略信息
    strategy = await postgres.fetch_one(
        "SELECT * FROM strategies WHERE id = $1", strategy_id
    )

    # 從InfluxDB獲取性能數據
    performance = await influxdb.query(
        measurement="strategy_returns",
        tags={"strategy_id": strategy_id},
        time_range="-30d"
    )

    return {
        "strategy": strategy,
        "performance": performance.to_dict('records')
    }
```

### 2. 與Redis整合

#### 2.1 緩存策略
- 最新價格：60秒TTL
- 策略摘要：5分鐘TTL
- 市場概覽：10分鐘TTL

#### 2.2 實時數據流
```python
# Redis + InfluxDB 實時寫入
async def write_market_data_stream(data: Dict):
    # 1. 緩存到Redis（快速訪問）
    cache_key = f"price:{data['symbol']}"
    await redis.setex(cache_key, 60, json.dumps(data))

    # 2. 批量寫入InfluxDB（持久化）
    await influxdb.write_market_data([data])
```

### 3. 與監控系統整合

#### 3.1 Prometheus集成
- InfluxDB指標導出
- Grafana儀表板配置
- 告警規則設置

#### 3.2 日志聚合
- 使用ELK Stack
- 結構化日志輸出
- 錯誤追蹤和報警

## 部署指南

### 1. 環境準備

#### 1.1 系統要求
- CPU: 4核心以上
- 內存: 8GB以上
- 硬盤: 100GB以上SSD
- 網絡: 千兆網絡

#### 1.2 Docker部署
```bash
# 創建環境變量文件
cat > .env << EOF
INFLUXDB_TOKEN=your-super-secret-token
INFLUXDB_PASSWORD=your-super-secret-password
POSTGRES_PASSWORD=your-postgres-password
GRAFANA_PASSWORD=your-grafana-password
EOF

# 啟動InfluxDB服務
docker-compose -f docker-compose.influxdb.yml up -d
```

### 2. 初始化腳本

#### 2.1 創建桶和保留策略
```bash
# 執行初始化腳本
python scripts/influxdb-setup.py

# 或使用Flux腳本
docker exec -it cbsc-influxdb influx apply \
  --file /app/scripts/setup-retention-policies.flux
```

#### 2.2 配置用戶和權限
```bash
# 創建讀寫用戶
influx user create \
  --org cbsc \
  --name cbsc_writer \
  --password ${WRITER_PASSWORD}

# 設置權限
influx auth create \
  --org cbsc \
  --all-access \
  --description "Full access token"
```

### 3. 數據遷移

#### 3.1 從CSV導入
```python
import pandas as pd
from influxdb_client import InfluxDBClient

# 讀取CSV文件
df = pd.read_csv("market_data.csv")

# 轉換為InfluxDB格式
data_points = []
for _, row in df.iterrows():
    data_points.append({
        "measurement": "stock_price",
        "timestamp": pd.to_datetime(row["timestamp"]),
        "tags": {
            "symbol": row["symbol"],
            "exchange": row["exchange"]
        },
        "fields": {
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": int(row["volume"])
        }
    })

# 批量寫入
client = InfluxDBClient(url="http://localhost:8086", token="your-token")
write_api = client.write_api()
write_api.write(bucket="market_data_raw", org="cbsc", record=data_points)
```

#### 3.2 從其他時序數據庫遷移
```python
# 從OpenTSDB遷移示例
def migrate_from_opentsdb(opentsdb_url: str):
    query = {
        "start": "1y-ago",
        "queries": [
            {
                "aggregator": "none",
                "metric": "stock_price"
            }
        ]
    }

    response = requests.post(f"{opentsdb_url}/api/query", json=query)
    data = response.json()

    # 轉換並寫入InfluxDB
    # ... 轉換邏輯 ...
```

## 監控和維護

### 1. 性能監控

#### 1.1 關鍵指標
- 寫入吞吐量（點/秒）
- 查詢響應時間
- 磁盤使用率
- 內存使用率
- CPU使用率

#### 1.2 Grafana儀表板
```json
{
  "dashboard": {
    "title": "InfluxDB Performance",
    "panels": [
      {
        "title": "Write Throughput",
        "type": "graph",
        "targets": [
          {
            "query": "from(bucket: \"system_metrics\") |> range(start: -1h) |> filter(fn: (r) => r._measurement == \"influxdb_write\")"
          }
        ]
      }
    ]
  }
}
```

### 2. 告警配置

#### 2.1 告警規則
```yaml
# alertmanager.yml
route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://localhost:5001/alerts'
```

#### 2.2 InfluxDB告警任務
```flux
option task = {
    name: "influxdb_health_check",
    every: 1m,
}

from(bucket: "system_metrics")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "influxdb_health")
  |> filter(fn: (r) => r.status != "pass")
  |> map(fn: (r) => ({
      r with
      _level: "crit",
      _message: "InfluxDB health check failed"
    }))
  |> monitor.notify(
    data: {"topic": "influxdb_alerts"},
    endpoint: {
      url: "http://alertmanager:9093/api/v1/alerts",
      method: "POST"
    }
  )
```

### 3. 備份和恢復

#### 3.1 數據備份
```bash
# 備份元數據
influx backup /backup/influxdb-$(date +%Y%m%d) \
  --token ${INFLUXDB_TOKEN} \
  --org cbsc

# 備份配置
docker exec cbsc-influxdb influx backup /backup/config-$(date +%Y%m%d)
```

#### 3.2 數據恢復
```bash
# 恢復數據
influx restore /backup/influxdb-20231201 \
  --token ${INFLUXDB_TOKEN} \
  --org cbsc \
  --bucket market_data_raw
```

## 故障排除

### 1. 常見問題

#### 1.1 連接問題
```bash
# 檢查InfluxDB狀態
docker logs cbsc-influxdb

# 檢查網絡連接
curl -f http://localhost:8086/health

# 檢查端口
netstat -tlnp | grep 8086
```

#### 1.2 性能問題
```bash
# 檢查查詢性能
influx query 'from(bucket: "_internal") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "query_log")'

# 檢查寫入性能
influx query 'from(bucket: "_internal") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "write")'
```

#### 1.3 磁盤空間問題
```bash
# 檢查磁盤使用
df -h /var/lib/influxdb2

# 清理舊數據
influx delete \
  --bucket market_data_raw \
  --org cbsc \
  --start 2023-01-01T00:00:00Z \
  --stop 2023-02-01T00:00:00Z \
  --predicate "_measurement=\"stock_price\""
```

### 2. 日志分析

#### 2.1 啟用詳細日志
```yaml
# influxdb.conf
[logger]
  level = "debug"
  format = "auto"
```

#### 2.2 查看錯誤日志
```bash
# InfluxDB日志
docker logs cbsc-influxdb | grep ERROR

# 應用日志
docker logs cbsc-influx-data-processor | grep ERROR
```

## 最佳實踐

### 1. 數據建模
- 使用標籤進行索引查詢
- 將高基數數據放在字段中
- 保持標籤值簡短且穩定
- 避免使用特殊字符

### 2. 查詢優化
- 始終使用時間範圍過濾
- 避免SELECT *查詢
- 使用聚合減少數據量
- 預計算常用聚合

### 3. 寫入優化
- 批量寫入數據
- 使用一致的時間戳
- 避免頻繁的小批量寫入
- 監控寫入延遲

### 4. 運維建議
- 定期監控系統指標
- 設置自動告警
- 定期執行備份
- 保持系統更新

## 參考資源

- [InfluxDB 2.7 文檔](https://docs.influxdata.com/influxdb/v2.7/)
- [Flux 查詢語言](https://docs.influxdata.com/influxdb/cloud/query-data/flux/)
- [InfluxDB 客戶端庫](https://github.com/influxdata/influxdb-client-python)
- [Grafana 儀表板](https://grafana.com/docs/grafana/latest/datasources/influxdb/)

---

*文檔版本: v1.0*
*最後更新: 2025-01-18*
*維護者: CBSC開發團隊*
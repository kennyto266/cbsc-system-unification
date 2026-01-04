# Task 9.2: 實時數據推送系統實現文檔

## 概述

Task 9.2 實現了量化策略管理系統的實時數據推送功能，包括市場數據流、通知管理和訂閱管理系統。本文檔詳細說明了實現的架構、功能和使用方法。

## 架構設計

### 系統組件

1. **統一WebSocket管理器** (`unified_websocket_manager.py`)
   - 現有的WebSocket連接管理
   - 消息路由和廣播
   - 數據流處理器

2. **市場數據流管理器** (`market_data_stream.py`)
   - 實時市場數據推送
   - 多數據源支持（模擬、Redis）
   - 數據緩存和歷史記錄

3. **通知管理器** (`notification_manager.py`)
   - 多渠道通知（WebSocket、郵件、Webhook）
   - 通知規則引擎
   - 重試機制

4. **訂閱管理器** (`subscription_manager.py`)
   - 高級訂閱過濾
   - 連接生命周期管理
   - 速率限制

5. **增強版WebSocket服務器** (`enhanced_websocket_server.py`)
   - 集成所有模塊
   - RESTful API端點
   - 健康檢查和監控

## 功能特性

### 1. 市場數據流推送

- **數據類型支持**：
  - 報價數據 (Quote)
  - 交易數據 (Trade)
  - 訂單簿數據 (OrderBook)
  - 聚合數據 (K線)
  - 新聞數據 (News)
  - 經濟數據 (Economic)

- **數據頻率**：
  - 實時 (Real-time)
  - Tick級別
  - 秒級別 (1s)
  - 分鐘級別 (1m, 5m, 15m)
  - 小時級別 (1h)
  - 日級別 (1d)

### 2. 通知系統

- **通知類型**：
  - 信息 (Info)
  - 成功 (Success)
  - 警告 (Warning)
  - 錯誤 (Error)
  - 嚴重 (Critical)

- **通知渠道**：
  - WebSocket實時推送
  - 郵件通知
  - Webhook回調
  - SMS短信（預留）
  - 推送通知（預留）

- **特殊通知**：
  - 策略警報
  - 風險警報
  - 系統廣播

### 3. 訂閱管理

- **訂閱類型**：
  - 市場數據訂閱
  - 策略更新訂閱
  - 風險警報訂閱
  - 性能指標訂閱
  - 投資組合更新訂閱
  - 系統通知訂閱

- **高級過濾**：
  - 字段過濾（等於、不等、大於、小於等）
  - 包含過濾
  - 正則表達式過濾
  - 集合過濾

- **連接管理**：
  - 每用戶連接數限制
  - 連接健康檢查
  - 自動清理斷開連接

## API 端點

### WebSocket端點

#### `/ws`
主WebSocket連接端點

**查詢參數**：
- `token`: JWT認證令牌

**客戶端消息格式**：

1. **訂閱數據流（傳統方式）**：
```json
{
    "type": "subscribe",
    "stream_type": "market_data",
    "filters": {
        "symbol": "0700.HK"
    },
    "frequency_limit": 10
}
```

2. **高級訂閱**：
```json
{
    "type": "advanced_subscribe",
    "subscription": {
        "type": "market_data",
        "filters": [
            {
                "field": "symbol",
                "operator": "in",
                "value": ["0700.HK", "9988.HK"]
            },
            {
                "field": "price",
                "operator": "gt",
                "value": 300
            }
        ],
        "parameters": {
            "data_types": ["quote", "trade"]
        },
        "rate_limit": 5
    }
}
```

3. **取消訂閱**：
```json
{
    "type": "unsubscribe",
    "subscription_id": "abc123"  // 或使用 "stream_type"
}
```

### REST API端點

#### 市場數據

1. **訂閱市場數據**
```
POST /api/market-data/subscribe
```

**請求體**：
```json
{
    "symbols": ["0700.HK", "9988.HK"],
    "data_types": ["quote", "trade"],
    "frequency": "realtime",
    "max_frequency": 10
}
```

2. **獲取最新數據**
```
GET /api/market-data/latest/{symbol}?data_type=quote
```

3. **獲取歷史數據**
```
GET /api/market-data/history/{symbol}?data_type=quote&limit=100
```

#### 訂閱管理

1. **創建高級訂閱**
```
POST /api/subscriptions/advanced
```

2. **獲取用戶訂閱列表**
```
GET /api/subscriptions
```

3. **更新訂閱**
```
PUT /api/subscriptions/{subscription_id}
```

4. **刪除訂閱**
```
DELETE /api/subscriptions/{subscription_id}
```

#### 通知系統

1. **發送通知**
```
POST /api/notifications/send
```

**請求體**：
```json
{
    "title": "系統維護通知",
    "message": "系統將於今晚進行維護",
    "type": "info",
    "priority": "normal",
    "target_users": ["user1", "user2"],
    "channels": ["websocket", "email"]
}
```

2. **發送系統廣播**
```
POST /api/notifications/system
```

3. **發送策略警報**
```
POST /api/notifications/strategy-alert
```

4. **發送風險警報**
```
POST /api/notifications/risk-alert
```

#### 統計信息

1. **健康檢查**
```
GET /health
```

2. **獲取所有統計**
```
GET /api/stats/all
```

## 配置示例

### 服務器配置

```python
config = EnhancedWebSocketServerConfig(
    host="0.0.0.0",
    port=8001,
    redis_url="redis://localhost:6379",
    secret_key="your-secret-key",
    max_connections_per_user=10,
    max_subscriptions_per_user=50,
    market_data_enabled=True,
    notification_email={
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "your-email@gmail.com",
        "password": "your-password",
        "from_email": "noreply@yourcompany.com"
    },
    notification_webhook={
        "default_url": "https://your-webhook-endpoint.com",
        "timeout": 10
    }
)
```

### Redis配置

```python
# Redis for market data
redis_client = redis.from_url("redis://localhost:6379")

# Market data channels
# - market:quote:{symbol}
# - market:trade:{symbol}
# - market:orderbook:{symbol}
# - market:aggregate:{symbol}
```

## 使用示例

### 1. 基本市場數據訂閱

```python
import asyncio
import websockets
import json

async def subscribe_market_data():
    uri = "ws://localhost:8001/ws?token=your-jwt-token"

    async with websockets.connect(uri) as websocket:
        # 訂閱騰訊控股的報價數據
        subscribe_msg = {
            "type": "subscribe",
            "stream_type": "market_data",
            "filters": {
                "symbol": "0700.HK",
                "data_type": "quote"
            },
            "frequency_limit": 10
        }

        await websocket.send(json.dumps(subscribe_msg))

        # 接收數據
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Received: {data}")

asyncio.run(subscribe_market_data())
```

### 2. 高級過濾訂閱

```python
async def advanced_subscription():
    uri = "ws://localhost:8001/ws?token=your-jwt-token"

    async with websockets.connect(uri) as websocket:
        # 訂閱價格大於300的港股
        advanced_msg = {
            "type": "advanced_subscribe",
            "subscription": {
                "type": "market_data",
                "filters": [
                    {
                        "field": "symbol",
                        "operator": "regex",
                        "value": r"\d{4}\.HK$"
                    },
                    {
                        "field": "price",
                        "operator": "gt",
                        "value": 300
                    }
                ],
                "parameters": {
                    "data_types": ["quote", "trade"]
                },
                "rate_limit": 5
            }
        }

        await websocket.send(json.dumps(advanced_msg))

        # 接收數據
        async for message in websocket:
            data = json.loads(message)
            if data.get("stream_type") == "market_data":
                market_data = data["data"]["market_data"]
                print(f"Symbol: {market_data['symbol']}, Price: {market_data['data']['price']}")
```

### 3. 發送通知

```python
import requests

# 發送策略警報
alert_response = requests.post(
    "http://localhost:8001/api/notifications/strategy-alert",
    json={
        "strategy_id": "momentum_strategy_001",
        "alert_type": "max_drawdown_exceeded",
        "message": "策略最大回撤超過預設閾值",
        "user_id": "trader_001",
        "data": {
            "current_drawdown": -0.15,
            "threshold": -0.10,
            "strategy_return": 0.05
        }
    }
)

print(alert_response.json())
```

### 4. 獲取統計信息

```python
import requests

# 獲取所有統計
stats_response = requests.get("http://localhost:8001/api/stats/all")
stats = stats_response.json()

print(f"活躍連接數: {stats['websocket']['active_connections']}")
print(f"市場數據訂閱: {stats['market_data']['subscriptions_active']}")
print(f"發送的消息數: {stats['notifications']['total_sent']}")
```

## 性能優化建議

### 1. 連接管理

- 合理設置 `max_connections_per_user` 和 `max_subscriptions_per_user`
- 使用連接池管理WebSocket連接
- 定期清理非活躍連接

### 2. 數據傳輸

- 啟用數據壓縮（`enable_compression: true`）
- 使用適當的速率限制避免客戶端過載
- 實施增量更新策略

### 3. 緩存策略

- 使用Redis緩存熱門市場數據
- 實施客戶端緩存減少重複請求
- 定期清理過期數據

### 4. 監控和告警

- 監控關鍵指標：連接數、消息數、錯誤率
- 設置自動告警機制
- 定期檢查系統健康狀態

## 故障排除

### 常見問題

1. **WebSocket連接失敗**
   - 檢查JWT token是否有效
   - 確認端口是否正確開放
   - 檢查防火牆設置

2. **訂閱無數據**
   - 確認訂閱的股票代碼正確
   - 檢查過濾條件是否過於嚴格
   - 查看服務端日誌

3. **通知未發送**
   - 檢查郵件配置是否正確
   - 確認Webhook URL是否可訪問
   - 查看重試隊列狀態

4. **性能問題**
   - 監控內存使用情況
   - 檢查Redis連接池設置
   - 分析消息處理延遲

### 日誌級別

```python
# 設置日誌級別
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 關鍵日誌位置
# - WebSocket連接/斷開
# - 訂閱創建/刪除
# - 消息發送失敗
# - 數據源連接狀態
```

## 安全考慮

1. **認證和授權**
   - 使用JWT token進行身份認證
   - 實施基於角色的訪問控制
   - 定期輪換密鑰

2. **數據保護**
   - 敏感數據加密傳輸
   - 實施數據訪問日誌
   - 定期審查權限設置

3. **防止濫用**
   - 實施速率限制
   - 監控異常行為
   - 設置黑名單機制

## 未來擴展

1. **更多數據源**
   - 集成實時新聞API
   - 添加社區數據源
   - 支持更多交易所數據

2. **增強功能**
   - 機器學習預測推送
   - 自定義指標計算
   - 跨市場數據關聯

3. **性能優化**
   - 實施數據分片
   - 添加邊緣節點
   - 優化消息路由

## 總結

Task 9.2 成功實現了完整的實時數據推送系統，包括：

✅ **市場數據流推送** - 支持多種數據類型和頻率
✅ **數據更新通知機制** - 事件驅動的架構
✅ **客戶端訂閱管理** - 高級過濾和連接管理
✅ **實時基礎設施** - Redis pub/sub和連接池

系統具有良好的擴展性和性能，可以滿足量化交易系統的實時數據需求。通過合理的配置和優化，可以支持大規模的並發連接和高頻數據推送。

---
*文檔最後更新：2025-01-18*
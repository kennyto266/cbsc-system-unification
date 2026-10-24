# API v0/v1 到 v2 遷移指南

本指南將幫助您從 CBSC 策略管理系統 API v0/v1 遷移到全新的 v2 版本。

## 遷移概述

### 為什麼要遷移？
- **更好的性能**：v2 API 平均響應時間 120ms，比 v0/v1 快 60%
- **更強的功能**：支持批量操作、實時更新、高級分析
- **更好的開發體驗**：完整的 SDK、詳細的文檔、類型提示
- **未來支持**：所有新功能將只在 v2 中提供

### 遷移策略
我們推薦採用**並行遷移**策略：
1. v0/v1 API 繼續運行
2. 逐步將功能遷移到 v2
3. 使用特性標誌控制新功能
4. 驗證後逐步退役 v0/v1

## 版本對比

### 端點映射

| v0/v1 端點 | v2 端點 | 狀態 | 說明 |
|------------|---------|------|------|
| `/api/personal-strategies` | `/api/v2/strategies/` | ✅ 完全兼容 | 新增分頁、過濾功能 |
| `/api/strategies` | `/api/v2/strategies/` | ✅ 完全兼容 | 合併個人策略接口 |
| `/api/strategies/{id}` | `/api/v2/strategies/{id}` | ✅ 完全兼容 | 增強響應格式 |
| `/api/v1/strategies/` | `/api/v2/strategies/` | ⚠️ 升級推薦 | 新增批量操作、高級查詢 |

### 新增功能

| 功能 | v0/v1 | v2 | 說明 |
|------|-------|----|-----|
| 批量操作 | ❌ | ✅ | 支持批量創建、更新、刪除策略 |
| 實時更新 | ❌ | ✅ | WebSocket v2 提供實時狀態更新 |
| 性能分析 | 基礎 | ✅ | 詳細的性能指標和報告 |
| 高級查詢 | 有限 | ✅ | 複雜過濾、排序、分頁 |
| 異步執行 | 同步 | ✅ | 異步執行策略操作 |

## 遷移步驟

### 步驟 1：環境準備

1. **獲取 v2 API 認證**
   ```bash
   curl -X POST https://api.cbsc.com/api/v2/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "username": "your_username",
       "password": "your_password"
     }'
   ```

2. **安裝 SDK（可選）**
   ```bash
   # Python
   pip install cbsc-strategy-sdk-v2

   # JavaScript/TypeScript
   npm install @cbsc/strategy-sdk-v2
   ```

### 步驟 2：基礎端點遷移

#### 獲取策略列表

**v0/v1 代碼：**
```python
import requests

headers = {"Authorization": "Bearer your_token"}
response = requests.get(
    "https://api.cbsc.com/api/personal-strategies",
    headers=headers
)
strategies = response.json()
```

**v2 代碼：**
```python
import requests

headers = {
    "Authorization": "Bearer your_token",
    "Content-Type": "application/json"
}
response = requests.get(
    "https://api.cbsc.com/api/v2/strategies/",
    headers=headers
)
data = response.json()
strategies = data["data"]["items"]  # 注意新的響應格式
```

#### 創建策略

**v0/v1 代碼：**
```python
strategy_data = {
    "name": "My Strategy",
    "description": "Test strategy",
    "config": {...}
}

response = requests.post(
    "https://api.cbsc.com/api/personal-strategies",
    json=strategy_data,
    headers=headers
)
strategy = response.json()
```

**v2 代碼：**
```python
strategy_data = {
    "name": "My Strategy",
    "description": "Test strategy",
    "config": {...},
    "metadata": {
        "tags": ["test", "example"],
        "category": "momentum"
    }
}

response = requests.post(
    "https://api.cbsc.com/api/v2/strategies/",
    json=strategy_data,
    headers=headers
)
data = response.json()
if data["success"]:
    strategy = data["data"]
else:
    # 處理錯誤
    error = data["error"]
    raise Exception(f"API Error: {error['message']}")
```

### 步驟 3：利用新功能

#### 批量操作

```python
# v2 新功能：批量創建策略
strategies_batch = [
    {"name": "Strategy 1", "config": {...}},
    {"name": "Strategy 2", "config": {...}},
    {"name": "Strategy 3", "config": {...}}
]

response = requests.post(
    "https://api.cbsc.com/api/v2/strategies/batch",
    json={
        "action": "create",
        "items": strategies_batch
    },
    headers=headers
)

data = response.json()
if data["success"]:
    created = data["data"]["created"]
    failed = data["data"]["failed"]
    print(f"Created {len(created)} strategies")
else:
    print(f"Batch operation failed: {data['error']['message']}")
```

#### 實時更新

```python
# v2 新功能：WebSocket 實時更新
import asyncio
import websockets
import json

async def subscribe_strategy_updates():
    uri = "wss://api.cbsc.com/api/v2/ws/strategies"

    async with websockets.connect(uri) as websocket:
        # 認證
        await websocket.send(json.dumps({
            "action": "auth",
            "token": "your_jwt_token"
        }))

        # 訂閱策略更新
        await websocket.send(json.dumps({
            "action": "subscribe",
            "type": "strategy_updates",
            "filters": {
                "user_id": 123
            }
        }))

        # 接收更新
        async for message in websocket:
            update = json.loads(message)
            print(f"Strategy update: {update}")

# 運行客戶端
asyncio.get_event_loop().run_until_complete(subscribe_strategy_updates())
```

#### 性能分析

```python
# v2 新功能：獲取策略性能指標
strategy_id = "strategy_123"

response = requests.get(
    f"https://api.cbsc.com/api/v2/strategies/{strategy_id}/performance",
    headers=headers,
    params={
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "metrics": "return,risk,sharpe"
    }
)

data = response.json()
if data["success"]:
    performance = data["data"]
    print(f"Total Return: {performance['total_return']:.2%}")
    print(f"Sharpe Ratio: {performance['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {performance['max_drawdown']:.2%}")
```

### 步驟 4：錯誤處理遷移

**v0/v1 錯誤處理：**
```python
response = requests.get(url, headers=headers)
if response.status_code != 200:
    error_msg = response.json().get("error", "Unknown error")
    print(f"Error: {error_msg}")
```

**v2 錯誤處理：**
```python
response = requests.get(url, headers=headers)
data = response.json()

if not data.get("success", False):
    error = data.get("error", {})
    error_code = error.get("code", "UNKNOWN_ERROR")
    error_msg = error.get("message", "Unknown error")

    # 根據錯誤類型處理
    if error_code == "VALIDATION_ERROR":
        print(f"Validation error: {error_msg}")
        # 顯示具體的字段錯誤
        if "details" in error:
            for field, reason in error["details"].items():
                print(f"  {field}: {reason}")
    elif error_code == "RATE_LIMITED":
        print("Rate limit exceeded. Please try again later.")
        # 可以使用 X-RateLimit-Reset 頭來獲取重置時間
        reset_time = response.headers.get("X-RateLimit-Reset")
        if reset_time:
            print(f"Rate limit resets at: {reset_time}")
    else:
        print(f"API Error [{error_code}]: {error_msg}")

    # 可選：記錄 request_id 用於調試
    request_id = data.get("request_id")
    if request_id:
        print(f"Request ID: {request_id}")
```

## 向後兼容性

### 特性標誌

v2 API 支持特性標誌，可以逐步啟用新功能：

```python
# 請求頭中包含特性標誌
headers = {
    "Authorization": "Bearer your_token",
    "X-CBSC-Features": "v2-endpoints,batch-operations",
    "X-CBSC-API-Version": "2.0"
}
```

### 請求轉發

在遷移期間，可以配置代理將舊端點轉發到新端點：

```nginx
# Nginx 配置示例
location /api/personal-strategies {
    # 轉發到 v2 端點
    proxy_pass http://cbsc-strategy-api-v2/api/v2/strategies/;

    # 保留原始查詢參數
    proxy_set_header X-Original-URI $request_uri;

    # 添加版本標誌
    proxy_set_header X-CBSC-API-Version "2.0";
    proxy_set_header X-CBSC-Migration-Mode "v1-to-v2";
}
```

## 測試策略

### 1. 並行測試

同時運行 v0/v1 和 v2 API，比較結果：

```python
def compare_strategies_v1_v2():
    headers = {"Authorization": "Bearer your_token"}

    # v1 API 調用
    v1_response = requests.get(
        "https://api.cbsc.com/api/personal-strategies",
        headers=headers
    )

    # v2 API 調用
    v2_response = requests.get(
        "https://api.cbsc.com/api/v2/strategies/",
        headers=headers
    )

    # 比較結果
    v1_strategies = v1_response.json()
    v2_data = v2_response.json()
    v2_strategies = v2_data["data"]["items"]

    assert len(v1_strategies) == len(v2_strategies)
    print("API responses match!")
```

### 2. A/B 測試

使用特性標誌進行 A/B 測試：

```python
# 測試組：使用 v2 API
test_headers = {
    "Authorization": "Bearer your_token",
    "X-CBSC-Test-Group": "v2-api"
}

# 控制組：繼續使用 v1 API
control_headers = {
    "Authorization": "Bearer your_token",
    "X-CBSC-Test-Group": "v1-api"
}
```

### 3. 負載測試

確保 v2 API 能處理當前負載：

```bash
# 使用 locust 進行負載測試
locust -f load_test_v2.py --host=https://api.cbsc.com/api/v2
```

## 常見問題

### Q: v0/v1 API 何時退役？
A: 目前計劃在 v2 API 穩定運行 6 個月後開始逐步退役，會提前 3 個月通知。

### Q: 如何處理認證差異？
A: v2 API 使用相同的 JWT 認證，但增加了額外的安全檢查。確保您的 token 包含必要的聲明。

### Q: 數據格式有什麼變化？
A: v2 API 使用更結構化的響應格式，增加了分頁、元數據等。但核心數據結構保持兼容。

### Q: 如何回滾到 v0/v1？
A: 通過修改請求的基礎 URL 即可回滾。建議在遷移期間保留兩個版本的實現。

## 支持資源

- [遷移工具腳本](../tools/migration/)
- [SDK 遷移指南](../sdk/migration.md)
- [API 差異對照表](../tools/api-diff.html)
- [技術支持](mailto:migration-support@cbsc.com)

## 時間表

| 階段 | 開始時間 | 結束時間 | 主要活動 |
|------|----------|----------|----------|
| 準備 | 2025-12-01 | 2025-12-15 | 獲取認證、測試環境 |
| 遷移 | 2025-12-16 | 2026-01-31 | 功能遷移、並行運行 |
| 驗證 | 2026-02-01 | 2026-02-28 | 全面測試、性能驗證 |
| 完成 | 2026-03-01 | 2026-03-31 | 退役 v0/v1、清理 |

---

遷移過程中如遇任何問題，請聯繫我們的技術支持團隊。我們將為您提供全程支持，確保遷移順利完成。
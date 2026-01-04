# CBSC API 使用示例

本文檔提供了CBSC量化交易系統API的詳細使用示例，涵蓋常見用例和最佳實踐。

## 目錄

- [認證](#認證)
- [策略管理](#策略管理)
- [策略執行](#策略執行)
- [市場數據](#市場數據)
- [回測分析](#回測分析)
- [風險管理](#風險管理)
- [WebSocket實時數據](#websocket實時數據)
- [錯誤處理](#錯誤處理)

## 認證

### 1. 用戶登錄

```python
import requests

# 登錄獲取token
login_data = {
    "username": "your-email@example.com",
    "password": "YourSecurePassword123!"
}

response = requests.post(
    "https://api.cbsc.com/v2/auth/login",
    json=login_data
)

if response.status_code == 200:
    auth_data = response.json()
    access_token = auth_data["access_token"]
    refresh_token = auth_data["refresh_token"]
    print("登錄成功")
else:
    print("登錄失敗:", response.json())
```

```javascript
// JavaScript/Node.js 示例
const response = await fetch('https://api.cbsc.com/v2/auth/login', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        username: 'your-email@example.com',
        password: 'YourSecurePassword123!'
    })
});

const authData = await response.json();
const token = authData.access_token;
```

### 2. 刷新Token

```python
# 使用refresh token獲取新的access token
refresh_data = {
    "refresh_token": refresh_token
}

response = requests.post(
    "https://api.cbsc.com/v2/auth/refresh",
    json=refresh_data
)

if response.status_code == 200:
    new_token = response.json()["access_token"]
    access_token = new_token  # 更新token
```

### 3. 設置認證頭

```python
# 設置用於API請求的認證頭
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "API-Version": "2.0"
}
```

## 策略管理

### 1. 創建技術分析策略

```python
# 創建RSI策略
strategy_data = {
    "name": "RSI超賣反轉策略",
    "description": "基於RSI指標的超賣反轉策略，當RSI低於30時買入",
    "type": "technical",
    "parameters": {
        "rsi_period": 14,
        "rsi_oversold": 30,
        "rsi_overbought": 70
    },
    "risk_settings": {
        "max_position_size": 0.1,
        "stop_loss": 0.05,
        "take_profit": 0.15
    },
    "symbols": ["AAPL", "MSFT", "GOOGL"]
}

response = requests.post(
    "https://api.cbsc.com/v2/strategies",
    json=strategy_data,
    headers=headers
)

strategy = response.json()
print(f"策略創建成功，ID: {strategy['id']}")
```

### 2. 獲取策略列表

```python
# 獲取策略列表（分頁）
params = {
    "page": 1,
    "page_size": 20,
    "sort_by": "created_at",
    "sort_order": "desc",
    "filter_status": "active"
}

response = requests.get(
    "https://api.cbsc.com/v2/strategies",
    params=params,
    headers=headers
)

data = response.json()
for strategy in data["data"]:
    print(f"策略: {strategy['name']}, 狀態: {strategy['status']}")
```

### 3. 獲取策略詳情

```python
# 獲取策略詳情（包含性能指標和執行歷史）
strategy_id = "str_001"
params = {
    "include": "performance,executions,backtests"
}

response = requests.get(
    f"https://api.cbsc.com/v2/strategies/{strategy_id}",
    params=params,
    headers=headers
)

strategy_detail = response.json()
print(f"策略名稱: {strategy_detail['name']}")
print(f"總收益率: {strategy_detail['performance']['total_return']}%")
print(f"夏普比率: {strategy_detail['performance']['sharpe_ratio']}")
```

### 4. 更新策略

```python
# 更新策略參數
strategy_id = "str_001"
update_data = {
    "parameters": {
        "rsi_period": 21,  # 修改RSI週期
        "rsi_oversold": 25,
        "rsi_overbought": 75
    },
    "risk_settings": {
        "max_position_size": 0.15,  # 調整最大持倉
        "stop_loss": 0.04
    }
}

response = requests.put(
    f"https://api.cbsc.com/v2/strategies/{strategy_id}",
    json=update_data,
    headers=headers
)

if response.status_code == 200:
    print("策略更新成功")
```

### 5. 批量操作策略

```python
# 批量啟用策略
strategy_ids = ["str_001", "str_002", "str_003"]
params = {
    "operation": "activate"
}

response = requests.post(
    "https://api.cbsc.com/v2/strategies/batch",
    params=params,
    json=strategy_ids,
    headers=headers
)

result = response.json()
print(f"成功: {result['successful']}, 失敗: {result['failed']}")
```

## 策略執行

### 1. 運行回測

```python
# 創建回測任務
strategy_id = "str_001"
backtest_request = {
    "strategy_id": strategy_id,
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 100000,
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "commission": 0.001,
    "slippage": 0.0001
}

response = requests.post(
    "https://api.cbsc.com/v2/backtest/run",
    json=backtest_request,
    headers=headers
)

if response.status_code == 202:
    backtest_id = response.json()["backtest_id"]
    print(f"回測已開始，ID: {backtest_id}")
```

### 2. 獲取回測結果

```python
# 獲取回測結果
import time

backtest_id = "bt_001"

# 輪詢直到回測完成
while True:
    response = requests.get(
        f"https://api.cbsc.com/v2/backtest/{backtest_id}",
        headers=headers
    )
    
    result = response.json()
    
    if result["status"] == "completed":
        print("回測完成!")
        performance = result["performance"]
        print(f"總收益率: {performance['total_return']:.2f}%")
        print(f"夏普比率: {performance['sharpe_ratio']:.2f}")
        print(f"最大回撤: {performance['max_drawdown']:.2f}%")
        break
    elif result["status"] == "failed":
        print("回測失敗:", result.get("error_message"))
        break
    
    time.sleep(5)  # 等待5秒後再查詢
```

### 3. 實時執行策略

```python
# 實時交易執行
strategy_id = "str_001"
execution_request = {
    "execution_mode": "paper_trading",  # 或 "live_trading"
    "start_date": "2024-01-01T00:00:00Z",
    "initial_capital": 50000,
    "symbols": ["AAPL", "MSFT"]
}

response = requests.post(
    f"https://api.cbsc.com/v2/strategies/{strategy_id}/executions",
    json=execution_request,
    headers=headers
)

if response.status_code == 202:
    execution_id = response.json()["execution_id"]
    print(f"策略執行已啟動，ID: {execution_id}")
```

### 4. 監控執行狀態

```python
# 獲取執行狀態
execution_id = "exec_001"

response = requests.get(
    f"https://api.cbsc.com/v2/strategies/str_001/executions/{execution_id}",
    headers=headers
)

execution = response.json()
print(f"執行狀態: {execution['status']}")
print(f"進度: {execution['progress']}%")
print(f"開始時間: {execution['start_time']}")

# 獲取執行結果
if execution["status"] == "completed":
    results = execution["results"]
    print(f"最終資金: ${results['final_capital']:,.2f}")
    print(f"總收益: {results['total_return']:.2f}%")
```

## 市場數據

### 1. 獲取歷史數據

```python
# 獲取蘋果股票日線數據
symbol = "AAPL"
params = {
    "interval": "1d",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "page": 1,
    "page_size": 50
}

response = requests.get(
    f"https://api.cbsc.com/v2/market-data/{symbol}/history",
    params=params,
    headers=headers
)

data = response.json()
print(f"獲取到 {len(data['data'])} 條數據")

# 轉換為pandas DataFrame
import pandas as pd

df = pd.DataFrame(data["data"])
df["timestamp"] = pd.to_datetime(df["timestamp"])
df.set_index("timestamp", inplace=True)
print(df.head())
```

### 2. 獲取實時數據

```python
# 獲取實時報價
symbols = ["AAPL", "MSFT", "GOOGL"]

for symbol in symbols:
    response = requests.get(
        f"https://api.cbsc.com/v2/market-data/{symbol}/realtime",
        params={"fields": "price,change,volume,bid,ask"},
        headers=headers
    )
    
    quote = response.json()
    print(f"{symbol}: ${quote['price']:.2f} ({quote['change']:+.2f}, {quote['change_percent']:+.2f}%)")
```

### 3. 批量獲取實時數據

```python
# 批量獲取多個股票的實時數據
params = {
    "symbols": "AAPL,MSFT,GOOGL,TSLA,META",
    "fields": "price,change,change_percent,volume"
}

response = requests.get(
    "https://api.cbsc.com/v2/market-data/bulk/realtime",
    params=params,
    headers=headers
)

data = response.json()
for symbol, quote in data["data"].items():
    print(f"{symbol}: ${quote['price']:.2f}")
```

## 經濟指標

### 1. 獲取美聯儲利率

```python
# 獲取Fed Funds利率歷史數據
params = {
    "start_date": "2023-01-01",
    "end_date": "2024-01-01"
}

response = requests.get(
    "https://api.cbsc.com/v2/economic-indicators/Fed_Funds/data",
    params=params,
    headers=headers
)

data = response.json()
print(f"最新Fed Funds利率: {data['statistics']['latest']:.2f}%")
print(f"變化: {data['statistics']['change']:+.2f}%")
```

### 2. 獲取HIBOR利率

```python
# 獲取3個月HIBOR利率
params = {
    "tenor": "3M",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
}

response = requests.get(
    "https://api.cbsc.com/v2/economic-indicators/hibor",
    params=params,
    headers=headers
)

data = response.json()
latest_rate = data["statistics"]["latest"]
print(f"最新3M HIBOR: {latest_rate:.2f}%")
```

### 3. 經濟指標儀表板

```python
# 獲取關鍵經濟指標儀表板
params = {
    "indicators": "Fed_Funds,HIBOR,CPI,Unemployment"
}

response = requests.get(
    "https://api.cbsc.com/v2/economic-indicators/dashboard",
    params=params,
    headers=headers
)

dashboard = response.json()
for indicator, data in dashboard["dashboard"].items():
    print(f"{indicator}: {data['value']} ({data['change']:+.2f})")
```

## 風險管理

### 1. 計算投資組合VaR

```python
# 計算投資組合風險價值
portfolio_data = {
    "portfolio": {
        "positions": [
            {
                "symbol": "AAPL",
                "quantity": 100,
                "current_price": 195.50
            },
            {
                "symbol": "MSFT",
                "quantity": 50,
                "current_price": 410.20
            },
            {
                "symbol": "GOOGL",
                "quantity": 30,
                "current_price": 145.80
            }
        ]
    },
    "confidence_level": 0.95,
    "time_horizon": 1
}

response = requests.post(
    "https://api.cbsc.com/v2/risk/var",
    json=portfolio_data,
    headers=headers
)

var_result = response.json()
print(f"投資組合價值: ${var_result['portfolio_value']:,.2f}")
print(f"95% VaR (1天): ${var_result['var_value']:,.2f}")
print(f"VaR佔比: {var_result['var_percent']:.2f}%")
```

### 2. 獲取投資組合風險指標

```python
# 獲取當前投資組合的風險指標
response = requests.get(
    "https://api.cbsc.com/v2/risk/portfolio",
    headers=headers
)

risk_metrics = response.json()
print(f"總風險: {risk_metrics['total_risk']:.2%}")
print(f"系統性風險: {risk_metrics['systematic_risk']:.2%}")
print(f"非系統性風險: {risk_metrics['unsystematic_risk']:.2%}")
print(f"Beta: {risk_metrics['beta']:.2f}")
print(f"夏普比率: {risk_metrics['sharpe_ratio']:.2f}")
```

## WebSocket實時數據

### Python WebSocket示例

```python
import websocket
import json
import threading

def on_message(ws, message):
    data = json.loads(message)
    print(f"收到實時更新: {data}")

def on_error(ws, error):
    print(f"WebSocket錯誤: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket連接關閉")

def on_open(ws):
    print("WebSocket連接成功")
    # 訂閱實時數據
    subscribe_msg = {
        "action": "subscribe",
        "channels": ["market_data", "executions"],
        "symbols": ["AAPL", "MSFT", "GOOGL"]
    }
    ws.send(json.dumps(subscribe_msg))

# 創建WebSocket連接
ws = websocket.WebSocketApp(
    "wss://api.cbsc.com/v2/ws",
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close,
    header=["Authorization: Bearer " + access_token]
)

# 在後台線程運行
wst = threading.Thread(target=ws.run_forever)
wst.daemon = True
wst.start()

# 保持程序運行
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ws.close()
```

### JavaScript WebSocket示例

```javascript
// 創建WebSocket連接
const ws = new WebSocket('wss://api.cbsc.com/v2/ws', [], {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

ws.onopen = () => {
    console.log('WebSocket連接成功');
    
    // 訂閱市場數據
    ws.send(JSON.stringify({
        action: 'subscribe',
        channels: ['market_data'],
        symbols: ['AAPL', 'MSFT', 'GOOGL']
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('實時數據:', data);
    
    // 處理不同類型的數據
    if (data.type === 'quote') {
        updateQuoteUI(data);
    } else if (data.type === 'execution') {
        updateExecutionUI(data);
    }
};

ws.onerror = (error) => {
    console.error('WebSocket錯誤:', error);
};

ws.onclose = () => {
    console.log('WebSocket連接關閉');
    
    // 實現自動重連
    setTimeout(() => {
        connectWebSocket();
    }, 5000);
};

// 處理網絡斷開
window.addEventListener('offline', () => {
    ws.close();
});

window.addEventListener('online', () => {
    connectWebSocket();
});
```

## 錯誤處理

### 統一錯誤處理函數

```python
def handle_api_error(response):
    """統一處理API錯誤"""
    if response.status_code == 200:
        return response.json()
    
    error_data = response.json()
    error_code = error_data.get("error", {}).get("code", "UNKNOWN_ERROR")
    error_message = error_data.get("error", {}).get("message", "Unknown error")
    
    if response.status_code == 401:
        # Token過期，嘗試刷新
        if refresh_token():
            # 重新發送請求
            headers["Authorization"] = f"Bearer {access_token}"
            return response.request.__class__(
                response.request.method,
                response.request.url,
                json=response.request.json,
                headers=headers
            ).json()
    
    elif response.status_code == 429:
        # 頻率限制，等待後重試
        retry_after = error_data.get("error", {}).get("details", {}).get("retry_after", 60)
        print(f"請求頻率超限，等待 {retry_after} 秒後重試")
        time.sleep(retry_after)
        # 重新發送請求...
    
    else:
        print(f"API錯誤 [{error_code}]: {error_message}")
        raise Exception(f"API請求失敗: {error_message}")

# 使用示例
try:
    response = requests.get(url, headers=headers)
    data = handle_api_error(response)
except Exception as e:
    print(f"請求失敗: {e}")
```

### 指數退避重試

```python
import time
import random

def api_request_with_retry(url, method="GET", max_retries=3, **kwargs):
    """帶指數退避的重試機制"""
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, **kwargs)
            
            # 成功或客戶端錯誤（4xx）不重試
            if response.status_code < 500:
                return response
                
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            print(f"請求失敗: {e}")
        
        # 指數退避：2^attempt 秒 + 隨機抖動
        delay = (2 ** attempt) + random.uniform(0, 1)
        print(f"第 {attempt + 1} 次重試，等待 {delay:.2f} 秒")
        time.sleep(delay)
    
    return response

# 使用示例
response = api_request_with_retry(
    "https://api.cbsc.com/v2/strategies",
    headers=headers,
    params={"page": 1, "page_size": 20}
)
```

## 最佳實踐

### 1. 連接池管理

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 創建帶重試的session
session = requests.Session()

# 配置重試策略
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST", "PUT", "DELETE"]
)

# 配置連接池
adapter = HTTPAdapter(
    max_retries=retry_strategy,
    pool_connections=10,  # 連接池大小
    pool_maxsize=20       # 最大連接數
)

session.mount("https://", adapter)
session.mount("http://", adapter)

# 使用session發送請求
response = session.get(
    "https://api.cbsc.com/v2/strategies",
    headers=headers
)
```

### 2. 緩存策略

```python
from functools import lru_cache
import time

class CBSCAPIClient:
    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self._cache = {}
        self._cache_ttl = 300  # 5分鐘緩存
    
    def _is_cache_valid(self, key):
        """檢查緩存是否有效"""
        if key not in self._cache:
            return False
        
        timestamp, _ = self._cache[key]
        return time.time() - timestamp < self._cache_ttl
    
    @lru_cache(maxsize=100)
    def get_historical_data(self, symbol, interval, start_date, end_date):
        """獲取歷史數據（帶緩存）"""
        cache_key = f"{symbol}_{interval}_{start_date}_{end_date}"
        
        if self._is_cache_valid(cache_key):
            _, data = self._cache[cache_key]
            return data
        
        response = requests.get(
            f"https://api.cbsc.com/v2/market-data/{symbol}/history",
            params={
                "interval": interval,
                "start_date": start_date,
                "end_date": end_date
            },
            headers=self.headers
        )
        
        data = response.json()
        self._cache[cache_key] = (time.time(), data)
        return data
```

### 3. 批量請求優化

```python
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

async def fetch_multiple_symbols(symbols, headers):
    """異步獲取多個股票數據"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for symbol in symbols:
            task = fetch_symbol_data(session, symbol, headers)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results

async def fetch_symbol_data(session, symbol, headers):
    """獲取單個股票數據"""
    async with session.get(
        f"https://api.cbsc.com/v2/market-data/{symbol}/realtime",
        headers=headers
    ) as response:
        return await response.json()

# 使用示例
symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "META"]
data = await fetch_multiple_symbols(symbols, headers)
for quote in data:
    print(f"{quote['symbol']}: ${quote['price']:.2f}")
```

### 4. 日誌記錄

```python
import logging

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CBSC_API")

def api_request(method, url, **kwargs):
    """帶日誌的API請求"""
    start_time = time.time()
    
    logger.info(f"發送 {method} 請求到 {url}")
    
    try:
        response = requests.request(method, url, **kwargs)
        elapsed = time.time() - start_time
        
        logger.info(
            f"請求完成: {response.status_code} "
            f"耗時 {elapsed:.2f}s "
            f"大小 {len(response.content)} bytes"
        )
        
        return response
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"請求失敗: {e} 耗時 {elapsed:.2f}s")
        raise
```

## 測試示例

### 使用pytest進行API測試

```python
import pytest
import requests
from unittest.mock import Mock, patch

class TestCBSCAPI:
    @pytest.fixture
    def client(self):
        return CBSCAPIClient("test_token")
    
    @pytest.fixture
    def mock_response(self):
        mock = Mock()
        mock.status_code = 200
        mock.json.return_value = {
            "data": [],
            "pagination": {"page": 1, "pageSize": 20, "total": 0}
        }
        return mock
    
    @patch('requests.get')
    def test_get_strategies(self, mock_get, client, mock_response):
        """測試獲取策略列表"""
        mock_get.return_value = mock_response
        
        strategies = client.get_strategies()
        
        assert strategies["data"] == []
        assert strategies["pagination"]["page"] == 1
        mock_get.assert_called_once()
    
    def test_create_strategy_validation(self, client):
        """測試策略創建驗證"""
        # 缺少必要字段
        with pytest.raises(ValueError):
            client.create_strategy({"name": "測試策略"})
        
        # 無效的策略類型
        with pytest.raises(ValueError):
            client.create_strategy({
                "name": "測試策略",
                "type": "invalid_type",
                "parameters": {}
            })

# 集成測試
@pytest.mark.integration
def test_strategy_workflow():
    """測試完整的策略工作流程"""
    client = CBSCAPIClient(get_test_token())
    
    # 1. 創建策略
    strategy = client.create_strategy({
        "name": "測試策略",
        "type": "technical",
        "parameters": {"period": 20}
    })
    
    strategy_id = strategy["id"]
    
    # 2. 更新策略
    client.update_strategy(strategy_id, {
        "parameters": {"period": 30}
    })
    
    # 3. 執行回測
    backtest = client.run_backtest({
        "strategy_id": strategy_id,
        "start_date": "2023-01-01",
        "end_date": "2023-12-31"
    })
    
    # 4. 驗證結果
    assert backtest["status"] in ["completed", "started"]
    
    # 5. 清理
    client.delete_strategy(strategy_id)
```

## 常見問題

### Q: 如何處理大數據量的分頁？

A: 使用游標分頁而不是偏移分頁：

```python
def get_all_data(endpoint, params=None, max_pages=100):
    """獲取所有分頁數據"""
    all_data = []
    page = 1
    
    while page <= max_pages:
        params = params or {}
        params["page"] = page
        params["page_size"] = 100  # 使用最大頁面大小
        
        response = requests.get(endpoint, params=params, headers=headers)
        data = response.json()
        
        all_data.extend(data["data"])
        
        # 檢查是否還有更多數據
        if not data["pagination"]["hasNext"]:
            break
        
        page += 1
    
    return all_data
```

### Q: 如何實現優雅的關閉？

A: 使用上下文管理器：

```python
from contextlib import contextmanager

@contextmanager
def cbsc_session(token):
    """CBSC API會話上下文管理器"""
    session = CBSCAPIClient(token)
    try:
        yield session
    finally:
        session.cleanup()  # 清理資源，關閉連接

# 使用示例
with cbsc_session(token) as api:
    strategies = api.get_strategies()
    # 自動清理資源
```

### Q: 如何監控API使用情況？

A: 實現使用情況跟蹤：

```python
class APIMonitor:
    def __init__(self):
        self.requests = 0
        self.errors = 0
        self.start_time = time.time()
    
    def record_request(self, success=True):
        self.requests += 1
        if not success:
            self.errors += 1
    
    def get_stats(self):
        elapsed = time.time() - self.start_time
        return {
            "requests": self.requests,
            "errors": self.errors,
            "error_rate": self.errors / max(self.requests, 1),
            "requests_per_second": self.requests / elapsed
        }

monitor = APIMonitor()

# 在每個請求後記錄
response = requests.get(url, headers=headers)
monitor.record_request(response.status_code == 200)
```

## 聯繫支持

如果遇到問題或需要幫助：

- 技術文檔: https://docs.cbsc.com/api
- API參考: https://api.cbsc.com/docs
- 技術支持郵箱: api-support@cbsc.com
- 社區論壇: https://community.cbsc.com
- 狀態頁: https://status.cbsc.com
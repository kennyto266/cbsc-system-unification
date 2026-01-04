# CBSC API SDK 文檔

本文檔介紹CBSC量化交易系統API的官方SDK使用方法。

## 目錄

- [Python SDK](#python-sdk)
- [JavaScript/Node.js SDK](#javascriptnodejs-sdk)
- [其他語言SDK](#其他語言sdk)
- [SDK最佳實踐](#sdk最佳實踐)

## Python SDK

### 安裝

```bash
pip install cbsc-api
```

或從源碼安裝：

```bash
git clone https://github.com/cbsc/cbsc-python-sdk.git
cd cbsc-python-sdk
pip install -e .
```

### 快速開始

```python
from cbsc_api import CBSCClient

# 初始化客戶端
client = CBSCClient(
    api_key="your-api-key",
    secret_key="your-secret-key",
    sandbox=True  # 測試環境
)

# 或者使用token
client = CBSCClient(token="your-jwt-token")

# 獲取策略列表
strategies = client.strategies.list()
print(f"找到 {len(strategies)} 個策略")
```

### 認證

```python
from cbsc_api import CBSCClient

# 使用API Key認證
client = CBSCClient(
    api_key="your-api-key",
    secret_key="your-secret-key"
)

# 使用JWT Token認證
client = CBSCClient(token="your-jwt-token")

# 自動刷新token
client = CBSCClient(
    token="your-jwt-token",
    refresh_token="your-refresh-token",
    auto_refresh=True
)
```

### 策略管理

#### 創建策略

```python
from cbsc_api.models import StrategyCreate, RiskSettings

# 創建技術分析策略
strategy = StrategyCreate(
    name="RSI策略",
    description="基於RSI的超賣反轉策略",
    type="technical",
    parameters={
        "rsi_period": 14,
        "rsi_oversold": 30
    },
    risk_settings=RiskSettings(
        max_position_size=0.1,
        stop_loss=0.05
    ),
    symbols=["AAPL", "MSFT"]
)

created = client.strategies.create(strategy)
print(f"策略ID: {created.id}")
```

#### 獲取策略

```python
# 獲取策略列表
strategies = client.strategies.list(
    page=1,
    page_size=20,
    type="technical",
    status="active",
    sort_by="created_at"
)

# 獲取策略詳情
strategy = client.strategies.get("str_001", include="performance,executions")

# 搜索策略
results = client.strategies.search("移動平均")
```

#### 更新策略

```python
from cbsc_api.models import StrategyUpdate

update = StrategyUpdate(
    name="更新後的策略名稱",
    parameters={
        "rsi_period": 21  # 修改參數
    }
)

client.strategies.update("str_001", update)
```

#### 刪除策略

```python
# 普通刪除（檢查是否有活躍執行）
client.strategies.delete("str_001")

# 強制刪除
client.strategies.delete("str_001", force=True)

# 批量刪除
client.strategies.batch_delete(["str_001", "str_002"])
```

### 策略執行

#### 運行回測

```python
from cbsc_api.models import BacktestRequest

backtest = BacktestRequest(
    strategy_id="str_001",
    start_date="2023-01-01",
    end_date="2023-12-31",
    initial_capital=100000,
    symbols=["AAPL", "MSFT"]
)

# 提交回測
job = client.backtest.run(backtest)
print(f"回測ID: {job.id}")

# 獲取結果
result = client.backtest.get_result(job.id)
print(f"總收益: {result.performance.total_return}%")
```

#### 實時執行

```python
from cbsc_api.models import ExecutionRequest, ExecutionMode

# 模擬交易
execution = ExecutionRequest(
    strategy_id="str_001",
    mode=ExecutionMode.PAPER_TRADING,
    initial_capital=50000,
    symbols=["AAPL"]
)

job = client.strategies.execute(execution)

# 監控執行
def on_execution_update(execution):
    print(f"執行進度: {execution.progress}%")

client.strategies.monitor(job.id, callback=on_execution_update)
```

### 市場數據

```python
# 獲取歷史數據
data = client.market_data.get_history(
    symbol="AAPL",
    interval="1d",
    start_date="2024-01-01",
    end_date="2024-01-31"
)

# 轉換為pandas DataFrame
df = data.to_dataframe()

# 獲取實時數據
quote = client.market_data.get_realtime("AAPL")

# 批量獲取實時數據
quotes = client.market_data.get_bulk_realtime(["AAPL", "MSFT", "GOOGL"])
```

### 經濟指標

```python
# 獲取Fed利率
fed_rates = client.economic_indicators.get_data(
    indicator="Fed_Funds",
    start_date="2023-01-01"
)

# 獲取HIBOR
hibor = client.economic_indicators.get_hibor(tenor="3M")

# 經濟儀表板
dashboard = client.economic_indicators.get_dashboard()
```

### 風險管理

```python
from cbsc_api.models import VaRRequest, Portfolio

portfolio = Portfolio([
    {"symbol": "AAPL", "quantity": 100, "price": 195.50},
    {"symbol": "MSFT", "quantity": 50, "price": 410.20}
])

var_request = VaRRequest(
    portfolio=portfolio,
    confidence_level=0.95
)

var_result = client.risk.calculate_var(var_request)
print(f"95% VaR: ${var_result.var_value}")
```

### WebSocket

```python
from cbsc_api.websocket import CBSCWebSocket

def on_message(data):
    if data.type == "quote":
        print(f"收到報價: {data.symbol} ${data.price}")
    elif data.type == "execution":
        print(f"執行更新: {data.execution_id}")

# 連接WebSocket
ws = CBSCWebSocket(token="your-token")

# 訂閱數據流
ws.subscribe_quotes(["AAPL", "MSFT"])
ws.subscribe_executions()

# 設置消息處理器
ws.on_message = on_message

# 啟動連接
ws.connect()

# 保持運行
import time
while True:
    time.sleep(1)
```

### 異步支持

```python
import asyncio
from cbsc_api import AsyncCBSCClient

async def main():
    client = AsyncCBSCClient(token="your-token")
    
    # 並發獲取多個策略
    tasks = [
        client.strategies.get(f"str_{i:03d}")
        for i in range(1, 11)
    ]
    strategies = await asyncio.gather(*tasks)
    
    # 並發執行回測
    backtest_tasks = []
    for strategy in strategies:
        backtest = BacktestRequest(
            strategy_id=strategy.id,
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        task = client.backtest.run_async(backtest)
        backtest_tasks.append(task)
    
    results = await asyncio.gather(*backtest_tasks)
    
    await client.close()

asyncio.run(main())
```

### 錯誤處理

```python
from cbsc_api.exceptions import CBSCError, AuthenticationError, RateLimitError

try:
    strategies = client.strategies.list()
except AuthenticationError:
    print("認證失敗，請檢查token")
except RateLimitError as e:
    print(f"請求頻率超限，等待 {e.retry_after} 秒")
    time.sleep(e.retry_after)
except CBSCError as e:
    print(f"API錯誤: {e.message} (代碼: {e.code})")
except Exception as e:
    print(f"未知錯誤: {e}")
```

### 日誌配置

```python
import logging
from cbsc_api import CBSCClient

# 配置日誌
logging.basicConfig(level=logging.INFO)

# 客戶端會自動記錄請求日誌
client = CBSCClient(token="your-token")

# 自定義日誌處理
logger = logging.getLogger("cbsc_api")
logger.addHandler(logging.FileHandler("cbsc_api.log"))
```

## JavaScript/Node.js SDK

### 安裝

```bash
npm install @cbsc/api
# 或
yarn add @cbsc/api
```

### 快速開始

```javascript
const { CBSCClient } = require('@cbsc/api');

// 初始化客戶端
const client = new CBSCClient({
    token: 'your-jwt-token',
    sandbox: true  // 測試環境
});

// 異步獲取策略列表
async function getStrategies() {
    try {
        const strategies = await client.strategies.list();
        console.log(`找到 ${strategies.data.length} 個策略`);
    } catch (error) {
        console.error('獲取策略失敗:', error);
    }
}

getStrategies();
```

### TypeScript支持

```typescript
import { CBSCClient, StrategyCreate, ExecutionMode } from '@cbsc/api';

const client = new CBSCClient({
    token: 'your-jwt-token'
});

// 創建策略
const strategy: StrategyCreate = {
    name: 'RSI策略',
    type: 'technical',
    parameters: {
        rsi_period: 14,
        rsi_oversold: 30
    },
    riskSettings: {
        maxPositionSize: 0.1,
        stopLoss: 0.05
    }
};

const created = await client.strategies.create(strategy);
console.log(`策略ID: ${created.id}`);
```

### 認證

```javascript
// 使用Token
const client = new CBSCClient({
    token: 'your-jwt-token'
});

// 使用API Key
const client = new CBSCClient({
    apiKey: 'your-api-key',
    secretKey: 'your-secret-key'
});

// 自動刷新Token
const client = new CBSCClient({
    token: 'your-jwt-token',
    refreshToken: 'your-refresh-token',
    autoRefresh: true
});
```

### 策略管理

```javascript
// 創建策略
const strategy = await client.strategies.create({
    name: '移動平均策略',
    type: 'technical',
    parameters: {
        shortPeriod: 10,
        longPeriod: 30
    },
    symbols: ['AAPL', 'MSFT']
});

// 獲取策略列表
const strategies = await client.strategies.list({
    type: 'technical',
    status: 'active',
    page: 1,
    pageSize: 20
});

// 獲取策略詳情
const detail = await client.strategies.get('str_001', {
    include: ['performance', 'executions']
});

// 更新策略
await client.strategies.update('str_001', {
    parameters: {
        shortPeriod: 20  // 修改參數
    }
});

// 刪除策略
await client.strategies.delete('str_001');
```

### 策略執行

```javascript
// 運行回測
const backtestJob = await client.backtest.run({
    strategyId: 'str_001',
    startDate: '2023-01-01',
    endDate: '2023-12-31',
    initialCapital: 100000,
    symbols: ['AAPL', 'MSFT']
});

// 等待回測完成
const result = await client.backtest.waitForResult(backtestJob.id);
console.log(`總收益: ${result.performance.totalReturn}%`);

// 實時執行
const execution = await client.strategies.execute({
    strategyId: 'str_001',
    mode: ExecutionMode.PAPER_TRADING,
    initialCapital: 50000
});

// 監控執行
client.strategies.onExecutionUpdate(execution.id, (update) => {
    console.log(`進度: ${update.progress}%`);
});
```

### 市場數據

```javascript
// 獲取歷史數據
const history = await client.marketData.getHistory('AAPL', {
    interval: '1d',
    startDate: '2024-01-01',
    endDate: '2024-01-31'
});

// 獲取實時數據
const quote = await client.marketData.getRealtime('AAPL');

// 批量獲取
const quotes = await client.marketData.getBulkRealtime([
    'AAPL', 'MSFT', 'GOOGL'
]);
```

### WebSocket

```javascript
const { CBSCWebSocket } = require('@cbsc/api');

const ws = new CBSCWebSocket({
    token: 'your-token'
});

// 訂閱市場數據
ws.subscribe('quotes', {
    symbols: ['AAPL', 'MSFT', 'GOOGL']
});

// 監聽消息
ws.on('quote', (data) => {
    console.log(`${data.symbol}: $${data.price}`);
});

ws.on('execution', (data) => {
    console.log(`執行更新: ${data.executionId}`);
});

// 連接
ws.connect();
```

### React Hook

```jsx
import React, { useEffect, useState } from 'react';
import { useCBSCClient } from '@cbsc/api/react';

function StrategyList() {
    const client = useCBSCClient();
    const [strategies, setStrategies] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function loadStrategies() {
            try {
                const response = await client.strategies.list();
                setStrategies(response.data);
            } catch (error) {
                console.error('加載策略失敗:', error);
            } finally {
                setLoading(false);
            }
        }

        loadStrategies();
    }, [client]);

    if (loading) return <div>加載中...</div>;

    return (
        <ul>
            {strategies.map(strategy => (
                <li key={strategy.id}>
                    {strategy.name} - {strategy.status}
                </li>
            ))}
        </ul>
    );
}
```

### 錯誤處理

```javascript
const { CBSCError, AuthenticationError, RateLimitError } = require('@cbsc/api');

try {
    const strategies = await client.strategies.list();
} catch (error) {
    if (error instanceof AuthenticationError) {
        console.log('認證失敗');
    } else if (error instanceof RateLimitError) {
        console.log(`請求超限，等待 ${error.retryAfter} 秒`);
        setTimeout(() => {
            // 重試請求
        }, error.retryAfter * 1000);
    } else if (error instanceof CBSCError) {
        console.log(`API錯誤: ${error.message}`);
    } else {
        console.log('未知錯誤:', error);
    }
}
```

## 其他語言SDK

### Go SDK

```go
package main

import (
    "fmt"
    "github.com/cbsc/cbsc-go-sdk"
)

func main() {
    // 初始化客戶端
    client := cbsc.NewClient("your-jwt-token")
    
    // 獲取策略列表
    strategies, err := client.Strategies.List()
    if err != nil {
        panic(err)
    }
    
    fmt.Printf("找到 %d 個策略\n", len(strategies.Data))
}
```

### Java SDK

```java
import com.cbsc.api.CBSCClient;
import com.cbsc.api.model.Strategy;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        // 初始化客戶端
        CBSCClient client = new CBSCClient("your-jwt-token");
        
        try {
            // 獲取策略列表
            List<Strategy> strategies = client.getStrategies().list();
            System.out.println("找到 " + strategies.size() + " 個策略");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

### C# SDK

```csharp
using CBSC.API;
using CBSC.API.Models;
using System;
using System.Threading.Tasks;

class Program
{
    static async Task Main(string[] args)
    {
        // 初始化客戶端
        var client = new CBSCClient("your-jwt-token");
        
        try
        {
            // 獲取策略列表
            var strategies = await client.Strategies.ListAsync();
            Console.WriteLine($"找到 {strategies.Data.Count} 個策略");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"錯誤: {ex.Message}");
        }
    }
}
```

### PHP SDK

```php
<?php

require_once 'vendor/autoload.php';

use CBSC\API\Client;

// 初始化客戶端
$client = new Client([
    'token' => 'your-jwt-token'
]);

try {
    // 獲取策略列表
    $strategies = $client->strategies()->list();
    echo "找到 " . count($strategies['data']) . " 個策略\n";
} catch (Exception $e) {
    echo "錯誤: " . $e->getMessage() . "\n";
}
```

### Ruby SDK

```ruby
require 'cbsc_api'

# 初始化客戶端
client = CBSC::Client.new(token: 'your-jwt-token')

begin
  # 獲取策略列表
  strategies = client.strategies.list
  puts "找到 #{strategies['data'].size} 個策略"
rescue CBSC::Error => e
  puts "錯誤: #{e.message}"
end
```

## SDK最佳實踐

### 1. 連接池管理

```python
# Python - 配置連接池
from cbsc_api import CBSCClient

client = CBSCClient(
    token="your-token",
    pool_connections=10,  # 連接池大小
    pool_maxsize=20       # 最大連接數
)
```

### 2. 重試機制

```javascript
// JavaScript - 自動重試配置
const client = new CBSCClient({
    token: 'your-token',
    retry: {
        retries: 3,
        factor: 2,
        minTimeout: 1000,
        maxTimeout: 30000
    }
});
```

### 3. 緩存策略

```python
# Python - 內置緩存
from cbsc_api import CBSCClient
from cbsc_api.cache import MemoryCache

cache = MemoryCache(ttl=300)  # 5分鐘緩存
client = CBSCClient(
    token="your-token",
    cache=cache
)

# 帶緩存的請求
data = client.market_data.get_history("AAPL", use_cache=True)
```

### 4. 批量操作

```python
# Python - 批量請求
from cbsc_api.utils import batch_request

symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "META"]

# 並發獲取多個股票數據
results = batch_request(
    lambda symbol: client.market_data.get_realtime(symbol),
    symbols,
    max_workers=5
)
```

### 5. 流式處理

```python
# Python - 流式獲取大量數據
for batch in client.market_data.stream_history(
    symbol="AAPL",
    interval="1m",
    start_date="2024-01-01",
    end_date="2024-12-31",
    batch_size=1000
):
    process_batch(batch)  # 處理每批數據
```

### 6. 配置管理

```python
# Python - 從配置文件加載
from cbsc_api import CBSCClient
import yaml

# 加載配置
with open("cbsc_config.yaml", "r") as f:
    config = yaml.safe_load(f)

# 創建客戶端
client = CBSCClient(
    token=config["api"]["token"],
    base_url=config["api"]["base_url"],
    timeout=config["api"]["timeout"],
    retries=config["api"]["retries"]
)
```

### 7. 測試支持

```python
# Python - Mock服務器
from cbsc_api.testing import MockServer
import pytest

@pytest.fixture
def mock_server():
    server = MockServer()
    server.add_response(
        "/strategies",
        {"data": [], "pagination": {"page": 1, "total": 0}}
    )
    server.start()
    yield server
    server.stop()

def test_list_strategies(mock_server):
    client = CBSCClient(
        token="test-token",
        base_url=mock_server.url
    )
    
    strategies = client.strategies.list()
    assert strategies["data"] == []
```

### 8. 性能監控

```python
# Python - 性能指標
from cbsc_api.monitoring import PerformanceMonitor

monitor = PerformanceMonitor()
client = CBSCClient(
    token="your-token",
    monitor=monitor
)

# 獲取性能統計
stats = monitor.get_stats()
print(f"平均響應時間: {stats['avg_response_time']}ms")
print(f"請求總數: {stats['total_requests']}")
```

## SDK版本控制

所有SDK都遵循語義化版本控制（SemVer）：

- **主版本號**：不兼容的API修改
- **次版本號**：向下兼容的功能性新增
- **修訂號**：向下兼容的問題修正

建議在項目中鎖定次版本號：

```bash
# Python
pip install cbsc-api>=2.0.0,<3.0.0

# JavaScript
npm install @cbsc/api@^2.0.0

# Go
go get github.com/cbsc/cbsc-go-sdk@v2.0.0
```

## 獲取幫助

- 文檔: https://docs.cbsc.com/sdk
- 示例代碼: https://github.com/cbsc/sdk-examples
- 問題報告: https://github.com/cbsc/{sdk-name}/issues
- 社區討論: https://community.cbsc.com
- 技術支持: sdk-support@cbsc.com
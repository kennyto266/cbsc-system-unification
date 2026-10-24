# CBSC Trading API Python SDK

官方 Python SDK 用于访问 CBSC 交易平台 API。

## 安装

```bash
pip install cbsc-trading-api
```

## 快速开始

```python
import os
from cbsc_trading_api import CBSCClient

# 初始化客户端
client = CBSCClient(
    base_url="https://api.cbsc.com",
    client_id=os.getenv("CBSC_CLIENT_ID"),
    client_secret=os.getenv("CBSC_CLIENT_SECRET")
)

# 获取访问令牌
token = client.auth.get_token()
print(f"Access token: {token.access_token}")

# 获取账户信息
accounts = client.users.get_users()
print(f"Accounts: {accounts}")

# 获取策略列表
strategies = client.strategies.get_strategies()
print(f"Strategies: {strategies}")

# 获取市场数据
symbols = client.market_data.get_symbols()
print(f"Market symbols: {symbols}")
```

## 认证

SDK 支持 OAuth2 客户端凭据模式进行认证：

```python
from cbsc_trading_api import CBSCClient

# 使用客户端凭据
client = CBSCClient(
    base_url="https://api.cbsc.com",
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# 或者使用已存在的令牌
client = CBSCClient(
    base_url="https://api.cbsc.com",
    access_token="your_access_token"
)
```

## API 功能

### 认证 (Authentication)
- `get_token()` - 获取访问令牌
- `refresh_token()` - 刷新访问令牌
- `login()` - 用户登录
- `register()` - 用户注册

### 用户管理 (Users)
- `get_users()` - 获取用户列表
- `get_user(user_id)` - 获取用户详情
- `create_user(user_data)` - 创建用户
- `update_user(user_id, user_data)` - 更新用户
- `delete_user(user_id)` - 删除用户

### 策略管理 (Strategies)
- `get_strategies()` - 获取策略列表
- `get_strategy(strategy_id)` - 获取策略详情
- `create_strategy(strategy_data)` - 创建策略
- `update_strategy(strategy_id, strategy_data)` - 更新策略
- `delete_strategy(strategy_id)` - 删除策略
- `backtest_strategy(strategy_id, backtest_data)` - 策略回测
- `get_strategy_performance(strategy_id)` - 获取策略表现

### 投资组合 (Portfolio)
- `get_portfolio()` - 获取投资组合
- `get_positions()` - 获取持仓
- `create_order(order_data)` - 创建订单
- `get_orders()` - 获取订单列表
- `get_order(order_id)` - 获取订单详情
- `cancel_order(order_id)` - 取消订单

### 市场数据 (Market Data)
- `get_symbols()` - 获取交易品种列表
- `get_symbol(symbol)` - 获取品种详情
- `get_symbol_data(symbol)` - 获取品种数据
- `get_symbol_quote(symbol)` - 获取实时报价
- `search_symbols(query)` - 搜索品种
- `get_historical_data(symbol, params)` - 获取历史数据

### 回测 (Backtests)
- `create_backtest(backtest_data)` - 创建回测任务
- `get_backtests()` - 获取回测列表
- `get_backtest(backtest_id)` - 获取回测详情
- `delete_backtest(backtest_id)` - 删除回测
- `cancel_backtest(backtest_id)` - 取消回测

### Webhooks
- `get_webhooks()` - 获取 Webhook 列表
- `create_webhook(webhook_data)` - 创建 Webhook
- `get_webhook(webhook_id)` - 获取 Webhook 详情
- `update_webhook(webhook_id, webhook_data)` - 更新 Webhook
- `delete_webhook(webhook_id)` - 删除 Webhook
- `test_webhook(webhook_id)` - 测试 Webhook
- `get_webhook_stats(webhook_id)` - 获取 Webhook 统计

## 错误处理

SDK 提供了完整的错误处理：

```python
from cbsc_trading_api.exceptions import (
    CBSCAPIError,
    AuthenticationError,
    RateLimitError,
    NotFoundError
)

try:
    strategies = client.strategies.get_strategies()
except AuthenticationError:
    print("认证失败，请检查客户端凭据")
except RateLimitError as e:
    print(f"请求频率限制，请在 {e.retry_after} 秒后重试")
except NotFoundError:
    print("请求的资源不存在")
except CBSCAPIError as e:
    print(f"API 错误: {e.message}")
```

## 分页

对于支持分页的端点，SDK 提供了便捷的分页处理：

```python
# 获取所有策略（自动处理分页）
all_strategies = []
page = 1
while True:
    response = client.strategies.get_strategies(skip=(page-1)*100, limit=100)
    all_strategies.extend(response.data)
    if len(response.data) < 100:
        break
    page += 1

print(f"总共 {len(all_strategies)} 个策略")
```

## 异步支持

SDK 也支持异步操作：

```python
import asyncio
from cbsc_trading_api import AsyncCBSCClient

async def main():
    client = AsyncCBSCClient(
        base_url="https://api.cbsc.com",
        client_id="your_client_id",
        client_secret="your_client_secret"
    )

    # 异步获取数据
    strategies = await client.strategies.get_strategies()
    users = await client.users.get_users()

    await client.close()

# 运行异步代码
asyncio.run(main())
```

## 开发

```bash
# 克隆仓库
git clone https://github.com/cbsc/trading-api-python-sdk.git
cd trading-api-python-sdk

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black .
flake8 .

# 类型检查
mypy cbsc_trading_api
```

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 支持

- 文档: https://docs.cbsc.com/api/python
- 问题报告: https://github.com/cbsc/trading-api-python-sdk/issues
- 邮件支持: api-support@cbsc.com
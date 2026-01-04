# Phase 5.2 回测API服务文档

## 概述

Phase 5.2 回测API服务是CBSC量化交易系统的核心组件，提供完整的策略回测功能，集成了风险管理、异步任务处理、结果缓存和性能监控等高级特性。

## 系统架构

### 核心组件

1. **回测API v2** (`backtest_api_v2.py`)
   - RESTful API接口
   - 异步任务管理
   - 批量回测支持
   - WebSocket实时更新

2. **配置验证器** (`backtest_validator.py`)
   - 策略参数验证
   - 风险设置检查
   - 数据范围验证
   - 权限控制

3. **任务队列系统** (`task_queue.py`)
   - Redis异步队列
   - 优先级处理
   - 任务重试机制
   - 分布式执行

4. **结果缓存系统** (`result_cache.py`)
   - 多层缓存架构
   - 数据压缩
   - 分页支持
   - 自动过期

5. **性能监控** (`api_monitoring.py`)
   - 请求追踪
   - 速率限制
   - 性能分析
   - 告警系统

6. **模板管理** (`template_manager.py`)
   - 模板CRUD操作
   - 版本控制
   - 协作功能
   - 模板市场

## API 接口

### 基础URL
```
http://localhost:8002/api/v2
```

### 认证

API使用基于JWT的认证机制。在请求头中包含：
```
Authorization: Bearer <jwt_token>
```

### 1. 创建回测任务

**POST** `/backtest`

创建新的回测任务。

#### 请求体

```json
{
  "strategy": {
    "name": "MA Crossover Strategy",
    "type": "ma_cross",
    "symbols": ["AAPL", "GOOGL", "MSFT"],
    "parameters": {
      "short_period": 20,
      "long_period": 50,
      "signal_threshold": 0.01
    }
  },
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-12-31T00:00:00Z",
  "initial_capital": "1000000",
  "commission_rate": "0.001",
  "slippage_rate": "0.0005",
  "enable_risk_management": true,
  "var_limit": "0.02",
  "max_drawdown_limit": "0.15",
  "leverage_limit": "2.0",
  "position_size_limit": "0.3",
  "backtest_type": "risk_managed",
  "enable_stress_testing": true,
  "enable_monte_carlo": false,
  "monte_carlo_simulations": 1000,
  "priority": "normal",
  "callback_url": "https://your-app.com/webhook/backtest-complete",
  "metadata": {
    "portfolio_id": "portfolio_123",
    "notes": "Q1 2024 strategy test"
  }
}
```

#### 响应

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "progress": 0.0,
  "created_at": "2024-12-18T10:00:00Z",
  "estimated_completion": "2024-12-18T10:10:00Z"
}
```

### 2. 批量回测

**POST** `/backtest/batch`

创建多个回测任务。

#### 请求体

```json
{
  "requests": [
    {
      "strategy": {
        "name": "MA Crossover",
        "type": "ma_cross",
        "symbols": ["AAPL"],
        "parameters": {"short_period": 10, "long_period": 30}
      },
      "start_date": "2024-01-01",
      "end_date": "2024-03-31",
      "initial_capital": "1000000"
    },
    {
      "strategy": {
        "name": "RSI Strategy",
        "type": "rsi_oversold",
        "symbols": ["GOOGL"],
        "parameters": {"rsi_period": 14, "oversold_level": 30}
      },
      "start_date": "2024-01-01",
      "end_date": "2024-03-31",
      "initial_capital": "1000000"
    }
  ],
  "parallel_execution": true,
  "max_concurrent": 3
}
```

#### 响应

返回任务信息数组，每个任务包含task_id和状态。

### 3. 查询任务状态

**GET** `/backtest/{task_id}`

获取任务执行状态。

#### 响应

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 0.65,
  "created_at": "2024-12-18T10:00:00Z",
  "started_at": "2024-12-18T10:00:05Z",
  "completed_at": null,
  "estimated_completion": "2024-12-18T10:06:30Z"
}
```

### 4. 获取详细进度

**GET** `/backtest/{task_id}/status`

获取任务的详细进度信息。

#### 响应

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 0.65,
  "current_step": "Running backtest simulation",
  "created_at": "2024-12-18T10:00:00Z",
  "started_at": "2024-12-18T10:00:05Z",
  "estimated_completion": "2024-12-18T10:06:30Z"
}
```

### 5. 取消任务

**DELETE** `/backtest/{task_id}`

取消正在运行的任务。

#### 响应

```json
{
  "message": "Task cancelled successfully",
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 6. 获取回测结果

**GET** `/backtest/{task_id}/result`

获取回测结果。

#### 查询参数

- `include_details`: 是否包含详细结果 (默认: false)
- `page`: 分页页码 (默认: 1)
- `size`: 每页大小 (默认: 50, 最大: 1000)

#### 响应

```json
{
  "summary": {
    "result_id": "result_550e8400-e29b-41d4-a716-446655440000",
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "strategy_name": "MA Crossover Strategy",
    "symbols": ["AAPL", "GOOGL", "MSFT"],
    "backtest_type": "risk_managed",
    "period": ["2024-01-01T00:00:00Z", "2024-12-31T00:00:00Z"],
    "total_return": 0.1567,
    "annualized_return": 0.1567,
    "volatility": 0.1872,
    "sharpe_ratio": 0.8368,
    "max_drawdown": -0.0823,
    "calmar_ratio": 1.9041,
    "var_95": -0.0198,
    "var_99": -0.0287,
    "expected_shortfall_95": -0.0256,
    "total_trades": 156,
    "win_rate": 0.6538,
    "profit_factor": 1.78,
    "execution_time": 285.43,
    "created_at": "2024-12-18T10:00:00Z"
  },
  "details": {
    "equity_curve": {
      "2024-01-01": 1000000,
      "2024-01-02": 1001234,
      "..."
    },
    "returns": {
      "2024-01-02": 0.001234,
      "..."
    },
    "positions": [
      {
        "symbol": "AAPL",
        "quantity": 1000,
        "entry_price": 150.25,
        "current_price": 152.75,
        "entry_date": "2024-01-05",
        "market_value": 152750,
        "unrealized_pnl": 2500,
        "return_pct": 0.01664
      }
    ],
    "trades": [
      {
        "timestamp": "2024-01-05T10:30:00Z",
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 1000,
        "price": 150.25,
        "commission": 150.25,
        "slippage": 75.13
      }
    ],
    "risk_metrics": {
      "var_metrics": {
        "var_95%": -0.0198,
        "var_99%": -0.0287
      },
      "drawdown_metrics": {
        "max_drawdown": -0.0823,
        "average_drawdown": -0.0156,
        "current_drawdown": -0.0123
      }
    },
    "stress_test_results": {
      "2008_crisis": {
        "scenario_loss": -0.2543,
        "portfolio_impact": -254300,
        "var_breach": true,
        "recovery_time": 180
      }
    }
  },
  "task_info": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "execution_time": 285.43
  }
}
```

### 7. 获取回测模板

**GET** `/backtest/templates`

获取可用的回测模板列表。

#### 查询参数

- `category`: 按类别筛选
- `tags`: 按标签筛选 (多个标签用逗号分隔)
- `public_only`: 仅显示公共模板

#### 响应

```json
{
  "items": [
    {
      "id": "tpl_123",
      "name": "MA Crossover Strategy",
      "description": "基于移动平均线交叉的趋势跟踪策略",
      "category": "trend_following",
      "tags": ["trend", "ma", "cross"],
      "created_by": "user123",
      "is_public": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 50
}
```

### 8. 创建回测模板

**POST** `/backtest/templates`

创建新的回测模板。

#### 请求体

```json
{
  "name": "Custom Strategy Template",
  "description": "自定义策略模板",
  "category": "custom",
  "strategy_template": {
    "type": "custom",
    "code": "def strategy(date, data, state):\n    return positions"
  },
  "default_parameters": {
    "param1": 100,
    "param2": 0.05
  },
  "risk_settings": {
    "var_limit": 0.02,
    "max_drawdown": 0.15
  },
  "tags": ["custom", "experimental"],
  "created_by": "user123",
  "is_public": false
}
```

### 9. 获取用户回测历史

**GET** `/backtest/user/{user_id}`

获取特定用户的回测历史。

#### 查询参数

- `status`: 按状态筛选
- `limit`: 返回数量限制

#### 响应

```json
{
  "items": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "progress": 1.0,
      "created_at": "2024-12-18T10:00:00Z",
      "completed_at": "2024-12-18T10:05:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 50
}
```

### 10. 获取统计信息

**GET** `/backtest/statistics`

获取回测统计和分析数据。

#### 查询参数

- `period`: 统计周期 (7d, 30d, 90d, 1y)
- `user_id`: 用户ID

#### 响应

```json
{
  "period": "30d",
  "total_tasks": 45,
  "completed_tasks": 42,
  "failed_tasks": 3,
  "success_rate": 0.9333,
  "performance_metrics": {
    "avg_total_return": 0.1256,
    "avg_sharpe_ratio": 1.234,
    "avg_max_drawdown": -0.0892
  },
  "task_types": {
    "standard": 10,
    "risk_managed": 30,
    "stress_test": 3,
    "monte_carlo": 2
  }
}
```

## 使用示例

### Python客户端示例

```python
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

class BacktestAPIClient:
    def __init__(self, base_url="http://localhost:8002/api/v2", token=None):
        self.base_url = base_url
        self.token = token
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.token}"} if self.token else {}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def create_backtest(self, strategy_config, start_date, end_date, **kwargs):
        """创建回测任务"""
        url = f"{self.base_url}/backtest"
        data = {
            "strategy": strategy_config,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            **kwargs
        }

        async with self.session.post(url, json=data) as response:
            return await response.json()

    async def get_task_status(self, task_id):
        """获取任务状态"""
        url = f"{self.base_url}/backtest/{task_id}"
        async with self.session.get(url) as response:
            return await response.json()

    async def get_result(self, task_id, include_details=False):
        """获取回测结果"""
        url = f"{self.base_url}/backtest/{task_id}/result"
        params = {"include_details": include_details}
        async with self.session.get(url, params=params) as response:
            return await response.json()

    async def wait_for_completion(self, task_id, timeout=3600):
        """等待任务完成"""
        start_time = datetime.utcnow()

        while True:
            task = await self.get_task_status(task_id)

            if task["status"] in ["completed", "failed", "cancelled"]:
                return task

            if (datetime.utcnow() - start_time).total_seconds() > timeout:
                raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")

            await asyncio.sleep(5)

    async def run_backtest(self, strategy_config, start_date, end_date, **kwargs):
        """运行完整的回测流程"""
        # 创建任务
        task = await self.create_backtest(strategy_config, start_date, end_date, **kwargs)
        task_id = task["task_id"]

        # 等待完成
        task = await self.wait_for_completion(task_id)

        if task["status"] != "completed":
            raise Exception(f"Backtest failed: {task.get('error_message', 'Unknown error')}")

        # 获取结果
        result = await self.get_result(task_id, include_details=True)
        return result


# 使用示例
async def example_backtest():
    # MA交叉策略配置
    strategy_config = {
        "name": "MA Crossover",
        "type": "ma_cross",
        "symbols": ["AAPL", "GOOGL", "MSFT"],
        "parameters": {
            "short_period": 20,
            "long_period": 50,
            "signal_threshold": 0.01
        }
    }

    # 时间范围
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    # 运行回测
    async with BacktestAPIClient() as client:
        result = await client.run_backtest(
            strategy_config=strategy_config,
            start_date=start_date,
            end_date=end_date,
            initial_capital="1000000",
            enable_risk_management=True,
            backtest_type="risk_managed"
        )

        # 打印结果
        print(f"总收益率: {result['summary']['total_return']:.2%}")
        print(f"夏普比率: {result['summary']['sharpe_ratio']:.2f}")
        print(f"最大回撤: {result['summary']['max_drawdown']:.2%}")
        print(f"总交易次数: {result['summary']['total_trades']}")
        print(f"胜率: {result['summary']['win_rate']:.2%}")

# 运行示例
asyncio.run(example_backtest())
```

### JavaScript客户端示例

```javascript
class BacktestAPIClient {
    constructor(baseUrl = 'http://localhost:8002/api/v2', token = null) {
        this.baseUrl = baseUrl;
        this.token = token;
    }

    async request(method, endpoint, data = null, params = null) {
        const url = new URL(`${this.baseUrl}${endpoint}`);

        // 添加查询参数
        if (params) {
            Object.entries(params).forEach(([key, value]) => {
                url.searchParams.append(key, value);
            });
        }

        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };

        if (this.token) {
            options.headers['Authorization'] = `Bearer ${this.token}`;
        }

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);
        return await response.json();
    }

    async createBacktest(strategyConfig, startDate, endDate, options = {}) {
        return this.request('POST', '/backtest', {
            strategy: strategyConfig,
            start_date: startDate,
            end_date: endDate,
            ...options
        });
    }

    async getTaskStatus(taskId) {
        return this.request('GET', `/backtest/${taskId}`);
    }

    async getResult(taskId, includeDetails = false) {
        return this.request('GET', `/backtest/${taskId}/result`, null, {
            include_details: includeDetails
        });
    }

    async waitForCompletion(taskId, timeout = 3600000) { // 默认1小时超时
        const startTime = Date.now();

        return new Promise((resolve, reject) => {
            const checkStatus = async () => {
                try {
                    const task = await this.getTaskStatus(taskId);

                    if (['completed', 'failed', 'cancelled'].includes(task.status)) {
                        resolve(task);
                        return;
                    }

                    if (Date.now() - startTime > timeout) {
                        reject(new Error(`Task ${taskId} did not complete within ${timeout}ms`));
                        return;
                    }

                    setTimeout(checkStatus, 5000);
                } catch (error) {
                    reject(error);
                }
            };

            checkStatus();
        });
    }

    async runBacktest(strategyConfig, startDate, endDate, options = {}) {
        // 创建任务
        const task = await this.createBacktest(strategyConfig, startDate, endDate, options);
        const taskId = task.task_id;

        // 等待完成
        const completedTask = await this.waitForCompletion(taskId);

        if (completedTask.status !== 'completed') {
            throw new Error(`Backtest failed: ${completedTask.error_message || 'Unknown error'}`);
        }

        // 获取结果
        const result = await this.getResult(taskId, true);
        return result;
    }
}

// 使用示例
async function runExampleBacktest() {
    const client = new BacktestAPIClient();

    // MA交叉策略配置
    const strategyConfig = {
        name: 'MA Crossover',
        type: 'ma_cross',
        symbols: ['AAPL', 'GOOGL', 'MSFT'],
        parameters: {
            short_period: 20,
            long_period: 50,
            signal_threshold: 0.01
        }
    };

    // 时间范围
    const startDate = '2024-01-01T00:00:00Z';
    const endDate = '2024-12-31T00:00:00Z';

    try {
        // 运行回测
        const result = await client.runBacktest(
            strategyConfig,
            startDate,
            endDate,
            {
                initial_capital: '1000000',
                enable_risk_management: true,
                backtest_type: 'risk_managed'
            }
        );

        // 打印结果
        console.log(`总收益率: ${(result.summary.total_return * 100).toFixed(2)}%`);
        console.log(`夏普比率: ${result.summary.sharpe_ratio.toFixed(2)}`);
        console.log(`最大回撤: ${(result.summary.max_drawdown * 100).toFixed(2)}%`);
        console.log(`总交易次数: ${result.summary.total_trades}`);
        console.log(`胜率: ${(result.summary.win_rate * 100).toFixed(2)}%`);

    } catch (error) {
        console.error('回测失败:', error.message);
    }
}

// 运行示例
runExampleBacktest();
```

## 错误处理

API使用标准HTTP状态码：

- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未授权
- `403 Forbidden`: 禁止访问
- `404 Not Found`: 资源不存在
- `429 Too Many Requests`: 请求过于频繁
- `500 Internal Server Error`: 服务器内部错误

错误响应格式：

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "strategy.symbols",
      "reason": "At least one symbol must be specified"
    }
  },
  "timestamp": "2024-12-18T10:00:00Z"
}
```

## 速率限制

API实施以下速率限制：

- 普通端点: 60次/分钟
- 回测创建: 10次/分钟
- 批量回测: 2次/分钟

超出限制将返回`429`状态码和以下响应头：

- `X-RateLimit-Limit`: 限制总数
- `X-RateLimit-Remaining`: 剩余次数
- `X-RateLimit-Reset`: 重置时间

## WebSocket实时更新

连接WebSocket以接收实时更新：

```javascript
const ws = new WebSocket('ws://localhost:8002/ws/backtest/{task_id}');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Update:', data);
};
```

消息格式：

```json
{
    "type": "progress_update",
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "progress": 0.75,
    "current_step": "Calculating risk metrics"
}
```

## 最佳实践

1. **异步处理**: 始终使用异步方式处理回测请求，避免阻塞
2. **进度轮询**: 合理设置轮询间隔（建议5-10秒）
3. **错误重试**: 实现指数退避的重试机制
4. **结果缓存**: 利用缓存系统减少重复请求
5. **批量操作**: 对多个回测使用批量接口
6. **资源清理**: 及时取消不需要的任务

## 部署说明

### 环境要求

- Python 3.8+
- Redis 6.0+
- PostgreSQL 12+ (可选，用于持久化存储)

### 环境变量

```bash
REDIS_URL=redis://localhost:6379
API_HOST=0.0.0.0
API_PORT=8002
MAX_WORKERS=10
ENABLE_MONITORING=true
CACHE_TTL=3600
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:3004
ENVIRONMENT=production
```

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY .env .

EXPOSE 8002

CMD ["python", "-m", "uvicorn", "src.api.backtest_service:app", "--host", "0.0.0.0", "--port", "8002"]
```

### Kubernetes部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backtest-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backtest-api
  template:
    metadata:
      labels:
        app: backtest-api
    spec:
      containers:
      - name: backtest-api
        image: cbsc/backtest-api:v2.0
        ports:
        - containerPort: 8002
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
---
apiVersion: v1
kind: Service
metadata:
  name: backtest-api-service
spec:
  selector:
    app: backtest-api
  ports:
  - port: 8002
    targetPort: 8002
  type: LoadBalancer
```

## 监控和告警

系统提供多种监控指标：

### Prometheus指标

- `http_requests_total`: HTTP请求总数
- `http_request_duration_seconds`: 请求响应时间
- `http_requests_active`: 活跃请求数
- `http_error_rate`: 错误率

### 系统指标

- CPU使用率
- 内存使用率
- 磁盘使用率
- 任务队列长度

### 告警规则

- 高响应时间 (>5秒)
- 高错误率 (>5%)
- 队列积压 (>1000任务)
- 服务不可用

## 故障排除

### 常见问题

1. **Redis连接失败**
   ```
   解决方案：检查Redis服务状态和网络连接
   ```

2. **任务执行超时**
   ```
   解决方案：增加超时时间或优化策略代码
   ```

3. **内存使用过高**
   ```
   解决方案：调整缓存配置或增加内存
   ```

4. **回测失败**
   ```
   解决方案：检查策略参数和数据可用性
   ```

### 日志位置

- 应用日志: `/var/log/backtest-api/`
- 错误日志: `/var/log/backtest-api/error.log`
- 访问日志: `/var/log/backtest-api/access.log`

## 版本更新

### v2.0.0 (当前版本)

- ✅ 异步任务队列
- ✅ 结果缓存系统
- ✅ 性能监控
- ✅ 模板管理
- ✅ 批量回测
- ✅ WebSocket支持

### 计划功能 (v2.1.0)

- [ ] 分布式回测
- [ ] 实时数据源集成
- [ ] 可视化图表
- [ ] 策略性能归因
- [ ] 多资产组合优化

## 技术支持

如有问题或需要技术支持，请联系：

- 邮箱: dev-team@cbsc.com
- 文档: https://docs.cbsc.com/backtest-api
- GitHub: https://github.com/cbsc/backtest-api
- 钉钉群: 12345678
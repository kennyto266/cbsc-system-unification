# API参考文档

## 基础信息

### 基础URL
```
http://localhost:8000
```

### 认证
- API Key认证：在请求头中添加 `X-API-Key`
- Bearer Token认证：在请求头中添加 `Authorization: Bearer <token>`

## 系统管理API

### 获取系统健康状态
```http
GET /health
```

### 获取系统状态
```http
GET /status
```

## Agent管理API

### 获取所有Agent状态
```http
GET /agents/status
```

### 启动Agent
```http
POST /agents/{agent_id}/start
```

### 停止Agent
```http
POST /agents/{agent_id}/stop
```

## 数据管理API

### 获取所有数据源状态
```http
GET /data/sources
```

### 更新数据
```http
POST /data/update
```

## 策略管理API

### 获取所有策略
```http
GET /strategies
```

### 运行策略回测
```http
POST /strategies/backtest
```

## 风险管理API

### 获取当前风险水平
```http
GET /risk/current
```

### 设置风险限制
```http
POST /risk/limits
```

## 投资组合管理API

### 获取当前投资组合
```http
GET /portfolio/current
```

### 重新平衡投资组合
```http
POST /portfolio/rebalance
```

## 监控和告警API

### 获取系统指标
```http
GET /monitoring/metrics
```

### 获取活跃告警
```http
GET /alerts/active
```

## 配置管理API

### 获取所有配置
```http
GET /config
```

### 更新配置
```http
PUT /config/{config_section}
```

## 示例代码

### Python示例
```python
import requests

BASE_URL = "http://localhost:8000"
HEADERS = {"X-API-Key": "your-api-key"}

# 获取系统状态
response = requests.get(f"{BASE_URL}/status", headers=HEADERS)
print(response.json())
```

### cURL示例
```bash
# 获取系统状态
curl -X GET "http://localhost:8000/status" -H "X-API-Key: your-api-key"

# 启动Agent
curl -X POST "http://localhost:8000/agents/quantitative_analyst/start" -H "X-API-Key: your-api-key"
```
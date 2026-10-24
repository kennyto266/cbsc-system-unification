# CBSC策略管理API模块

## 概述

这是CBSC量化交易策略管理系统的全新模块化API架构，实现了清晰的分层设计和高度可维护的代码结构。

## 架构设计

### 分层架构

```
┌─────────────────────────────────────┐
│            API层 (Endpoints)         │
│  - base.py      - 基础CRUD操作        │
│  - execution.py - 策略执行           │
│  - personal.py  - 个性化功能         │
│  - websocket.py - 实时通信          │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│         服务层 (Services)           │
│  - BaseStrategyService (基类)       │
│  - ExecutionService               │
│  - PersonalService                │
│  - WebSocketService               │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│       数据访问层 (Repositories)      │
│  - StrategyRepository             │
│  - UserRepository                │
│  - ExecutionRepository            │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│         工具模块 (Utils)            │
│  - permissions.py - 权限管理       │
│  - cache.py       - 缓存管理        │
│  - validators.py  - 数据验证        │
│  - errors.py      - 错误处理        │
└─────────────────────────────────────┘
```

## 核心特性

### 1. 模块化设计
- 每个模块职责单一，高内聚低耦合
- 清晰的依赖注入模式
- 易于测试和维护

### 2. BaseStrategyService基类
- 提供通用的CRUD操作
- 消除代码重复
- 支持缓存和权限管理
- 代码重复率从80%降低到<5%

### 3. 统一的数据模型
- `models.py` - 核心数据模型
- `schemas.py` - API请求/响应模型
- 确保数据一致性和类型安全

### 4. 高级功能
- 实时WebSocket通信
- 灵活的缓存策略
- 完善的错误处理
- 细粒度的权限控制

## API端点

### 基础操作 (/api/strategies)
- `GET /` - 获取策略列表
- `POST /` - 创建策略
- `GET /{strategy_id}` - 获取策略详情
- `PUT /{strategy_id}` - 更新策略
- `DELETE /{strategy_id}` - 删除策略
- `POST /batch-operation` - 批量操作
- `GET /templates/` - 获取策略模板
- `POST /{strategy_id}/clone` - 克隆策略

### 执行功能 (/api/strategies)
- `POST /{strategy_id}/execute` - 执行策略
- `GET /executions/{execution_id}` - 获取执行状态
- `POST /{strategy_id}/stop` - 停止执行
- `GET /{strategy_id}/performance` - 获取性能指标
- `GET /{strategy_id}/reports` - 生成执行报告

### 个性化功能 (/api/strategies/personal)
- `GET /dashboard` - 个人仪表板
- `GET /preferences` - 获取用户偏好
- `PUT /preferences` - 更新用户偏好
- `POST /strategies/{strategy_id}/control` - 控制策略
- `GET /recommendations` - 获取策略推荐

### WebSocket (/api/strategies/ws)
- `/realtime/{user_id}` - 实时数据推送
- `/strategy/{strategy_id}` - 策略特定更新
- `/market-data` - 市场数据推送
- `/notifications/{user_id}` - 个人通知

## 使用示例

### 创建策略

```python
from src.api.strategies.schemas import StrategyCreate, StrategyType, RiskLevel

request = StrategyCreate(
    name="RSI交易策略",
    description="基于RSI指标的交易策略",
    strategy_type=StrategyType.DIRECT_RSI,
    parameters={
        "rsi_period": 14,
        "rsi_oversold": 30,
        "rsi_overbought": 70,
        "stop_loss": 0.05,
        "take_profit": 0.1
    },
    risk_level=RiskLevel.MEDIUM
)
```

### 执行策略

```python
from src.api.strategies.schemas import ExecutionRequest

execution_request = ExecutionRequest(
    strategy_id="strategy_123",
    execution_mode="backtest",
    start_time="2023-01-01T00:00:00Z",
    end_time="2023-12-31T23:59:59Z"
)
```

### WebSocket连接

```javascript
// 实时数据连接
const ws = new WebSocket('ws://localhost:8000/api/strategies/ws/realtime/1');

// 策略更新连接
const strategyWs = new WebSocket('ws://localhost:8000/api/strategies/ws/strategy/strategy_123');
```

## 配置

主要配置项在 `config/settings.py`:

```python
# 数据库配置
DATABASE_URL = "postgresql://user:password@localhost:5432/cbsc"

# Redis配置
REDIS_URL = "redis://localhost:6379/0"

# 认证配置
SECRET_KEY = "your-secret-key"

# 缓存配置
CACHE_TTL_DEFAULT = 300  # 5分钟
```

## 测试

运行测试：

```bash
# 安装测试依赖
pip install pytest pytest-asyncio

# 运行所有测试
pytest src/api/strategies/tests/

# 运行特定测试
pytest src/api/strategies/tests/test_strategy_service.py -v
```

## 性能优化

1. **缓存策略**
   - 策略列表缓存5分钟
   - 策略详情缓存10分钟
   - 用户偏好缓存1小时

2. **数据库优化**
   - 使用连接池
   - 适当的索引
   - 分页查询

3. **异步处理**
   - 策略执行后台任务
   - WebSocket消息队列
   - 批量操作支持

## 部署

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY src/api/strategies/ ./strategies/
RUN pip install -r requirements.txt

CMD ["uvicorn", "strategies:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 环境变量

```bash
export DATABASE_URL="postgresql://..."
export REDIS_URL="redis://..."
export SECRET_KEY="your-secret-key"
export ENVIRONMENT="production"
```

## 迁移指南

### 从旧API迁移

1. **保持兼容的URL路径**
2. **统一响应格式**
3. **渐进式切换**
4. **功能开关控制**

### 功能开关

```python
# 在 settings.py 中配置
FEATURE_V2_API = True  # 启用新API
FEATURE_REAL_TIME_EXECUTION = True  # 实时执行
```

## 贡献指南

1. 遵循现有代码风格
2. 添加适当的测试
3. 更新文档
4. 确保向后兼容性

## 许可证

本项目采用 MIT 许可证。
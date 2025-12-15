# Analytics API

高性能的策略分析API，提供实时和历史策略性能指标、投资组合分析和风险管理功能。

## 功能特性

### 📊 性能分析
- 策略性能指标计算（夏普比率、最大回撤、波动率等）
- 支持多时间周期（1D、1W、1M、3M、6M、1Y、ALL）
- 基准比较和相关性分析
- 风险调整后收益指标

### 📈 历史数据
- 时间序列数据查询
- 可配置粒度（日、周、月）
- 高效分页支持
- 多指标组合查询

### 💼 投资组合分析
- 资产配置分解
- 行业分布分析
- 风险价值(VaR)计算
- 相关性矩阵

### ⚡ 实时指标
- 当前持仓追踪
- 实时盈亏计算
- 暴露和杠杆监控
- 50ms响应时间

### 🚀 性能优化
- Redis缓存层
- 异步后台计算
- 数据库查询优化
- 支持1000并发请求

## API端点

### 1. 策略性能指标

```http
GET /api/analytics/performance/{strategy_id}
```

**查询参数：**
- `period`: 时间周期 (1D, 1W, 1M, 3M, 6M, 1Y, ALL)
- `benchmark`: 基准代码（可选）
- `include_risk_metrics`: 是否包含风险指标

**响应示例：**
```json
{
  "strategy_id": "momentum_001",
  "period": "1M",
  "total_return": 12.5,
  "sharpe_ratio": 1.85,
  "sortino_ratio": 2.1,
  "max_drawdown": -8.3,
  "volatility": 15.2,
  "calmar_ratio": 1.51,
  "win_rate": 65.4,
  "profit_factor": 1.95,
  "avg_trade_duration": 2.4,
  "beta": 0.85,
  "alpha": 3.2
}
```

### 2. 历史数据

```http
GET /api/analytics/history/{strategy_id}
```

**查询参数：**
- `start_date`: 开始日期
- `end_date`: 结束日期
- `granularity`: 数据粒度 (daily, weekly, monthly)
- `metrics`: 指标列表
- `limit`: 数据点数量
- `offset`: 分页偏移

### 3. 投资组合分析

```http
GET /api/analytics/portfolio
```

**查询参数：**
- `user_id`: 用户ID（可选）
- `include_correlations`: 是否包含相关性矩阵
- `risk_level`: VaR置信水平 (90%, 95%, 99%)

### 4. 实时指标

```http
GET /api/analytics/realtime/{strategy_id}
```

**响应示例：**
```json
{
  "strategy_id": "momentum_001",
  "status": "active",
  "current_positions": 10,
  "total_exposure": 500000,
  "leverage": 2.0,
  "daily_pnl": 1250,
  "unrealized_pnl": 5000,
  "realized_pnl": -250,
  "last_updated": "2024-01-15T10:30:00Z",
  "market_value": 500000
}
```

### 5. 刷新缓存

```http
POST /api/analytics/refresh/{strategy_id}
```

强制重新计算策略指标并更新缓存。

## 缓存策略

### TTL配置
- 性能指标（1D）: 5分钟
- 性能指标（1W）: 30分钟
- 性能指标（1M）: 1小时
- 实时数据: 1分钟
- 投资组合数据: 15分钟

### 缓存键格式
- 性能指标: `perf:{strategy_id}:{period}`
- 实时数据: `realtime:{strategy_id}`
- 投资组合: `portfolio:{user_id}`

### 缓存失效
- 交易执行时自动失效
- 手动刷新API
- 基于标签的批量失效

## 性能指标

### 响应时间目标
- 缓存查询: < 100ms
- 实时指标: < 50ms
- 历史数据: < 500ms
- 复杂计算: < 2s

### 并发处理
- 支持1000并发请求
- 连接池: 20个连接
- 队列深度: 100
- 超时: 30s

## 后台任务

### 定期更新
- 性能指标: 每5分钟
- 投资组合数据: 每15分钟
- 缓存清理: 每小时

### 任务类型
- `calculate_performance`: 计算策略性能
- `calculate_portfolio`: 计算投资组合指标
- `update_correlations`: 更新相关性矩阵
- `cache_warmup`: 缓存预热

## 数据库架构

### 主要表
- `performance_metrics_cache`: 性能指标缓存
- `historical_aggregates`: 历史聚合数据
- `asset_correlations`: 资产相关性
- `portfolio_snapshots`: 投资组合快照

### 索引优化
- 复合索引: `(strategy_id, period, calculated_at)`
- 分区表: 按日期分区历史数据
- 查询优化: 覆盖索引

## 部署要求

### 基础设施
- **数据库**: MySQL 8.0+ 或 PostgreSQL 12+
- **缓存**: Redis 6.0+
- **任务队列**: Celery + Redis/RabbitMQ
- **监控**: Prometheus + Grafana

### 环境变量
```bash
# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=20

# 数据库配置
DATABASE_URL=mysql://user:pass@localhost/analytics

# 任务队列
CELERY_BROKER_URL=redis://localhost:6379/1

# 性能配置
MAX_CONCURRENT_REQUESTS=1000
CACHE_TTL_DEFAULT=3600
```

## 监控和日志

### 关键指标
- API响应时间
- 缓存命中率
- 数据库查询性能
- 错误率

### 日志级别
- `DEBUG`: 请求详情
- `INFO`: 业务事件
- `WARNING`: 性能问题
- `ERROR`: 系统错误

### 健康检查
```http
GET /api/analytics/health
GET /api/analytics/cache/stats
```

## 测试

### 运行测试
```bash
# 单元测试
pytest src/api/analytics/tests/test_analytics_api.py -v

# 集成测试
pytest src/api/analytics/tests/test_integration.py -v

# 性能测试
pytest src/api/analytics/tests/test_performance.py -v
```

### 测试覆盖率
```bash
pytest --cov=src/api/analytics --cov-report=html
```

## API文档

### Swagger UI
访问 `http://localhost:8000/docs` 查看交互式API文档。

### OpenAPI规范
```http
GET /api/analytics/openapi.json
```

## 安全考虑

### 认证
- JWT token验证
- 用户权限检查
- API速率限制

### 数据保护
- SQL注入防护
- 参数验证
- 输出过滤

## 故障排查

### 常见问题

1. **缓存命中率低**
   - 检查TTL配置
   - 验证缓存键格式
   - 监控缓存大小

2. **响应时间慢**
   - 检查数据库索引
   - 优化查询语句
   - 增加缓存

3. **计算结果错误**
   - 验证数据源
   - 检查计算逻辑
   - 对比基准值

### 调试模式
```bash
REACT_APP_DEBUG_ANALYTICS=true
```

## 版本更新

### v1.0.0
- 初始版本发布
- 基础性能分析功能
- Redis缓存实现

### 计划功能
- 机器学习预测
- 更多风险指标
- 自定义报告
- 实时流处理

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 编写测试
4. 提交PR
5. 代码审查

## 许可证

MIT License
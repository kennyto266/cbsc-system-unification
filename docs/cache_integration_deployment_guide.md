# 缓存系统集成部署指南

## 概述

本文档描述了CBSC策略管理系统中缓存系统的完整集成和部署方案。该系统基于统一的CacheManager实现，支持L1（内存）和L2（Redis）多级缓存。

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Layer     │    │  Monitoring     │    │   Grafana       │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │Strategies   │ │───▶│ │Prometheus   │ │───▶│ │Dashboard    │ │
│ │Execution    │ │    │ │Metrics      │ │    │ │Cache        │ │
│ │Personal     │ │    │ │Collector    │ │    │ │Performance  │ │
│ │WebSocket    │ │    │ └─────────────┘ │    │ │Monitoring   │ │
│ └─────────────┘ │    │                 │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │                 │
│ │CacheManager │ │◀───│ │Health Check │ │    │                 │
│ │- L1 Memory  │ │    │ │API          │ │    │                 │
│ │- L2 Redis   │ │    │ │Performance  │ │    │                 │
│ │- Metrics    │ │    │ │Analysis     │ │    │                 │
│ │- Strategies │ │    │ └─────────────┘ │    │                 │
│ └─────────────┘ │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│   Data Layer    │
│                 │
│ ┌─────────────┐ │
│ │   Redis     │ │
│ │   Server    │ │
│ └─────────────┘ │
│                 │
│ ┌─────────────┐ │
│ │ PostgreSQL  │ │
│ │   Database  │ │
│ └─────────────┘ │
└─────────────────┘
```

## 核心组件

### 1. CacheManager (src/services/cache_manager.py)
- **功能**: 统一的缓存管理系统
- **特性**:
  - 多级缓存支持 (L1内存 + L2 Redis)
  - 基于策略的缓存管理
  - 自动TTL过期
  - 数据压缩
  - 性能指标收集
  - 模式匹配清理

### 2. 缓存策略 (src/services/cache_strategy.py)
- **Strategy**: 策略数据 (5分钟TTL, L2缓存)
- **Performance**: 性能数据 (30秒TTL, L1缓存)
- **User**: 用户数据 (1分钟TTL, L1+L2缓存)
- **Config**: 配置数据 (10分钟TTL, L2缓存)
- **MarketData**: 市场数据 (5秒TTL, L1缓存)

### 3. 监控系统 (src/monitoring/cache_metrics.py)
- **Prometheus指标导出**:
  - `cache_hits_total` - 缓存命中次数
  - `cache_misses_total` - 缓存未命中次数
  - `cache_hit_rate` - 缓存命中率
  - `cache_memory_bytes` - 内存使用量
  - `cache_operation_duration_seconds` - 操作延迟

### 4. API端点 (src/api/monitoring/cache_monitoring.py)
- `/monitoring/cache/health` - 健康检查
- `/monitoring/cache/metrics` - Prometheus指标
- `/monitoring/cache/stats` - 详细统计
- `/monitoring/cache/performance` - 性能分析

## 部署配置

### 1. 环境变量配置

```bash
# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# 缓存配置
CACHE_DEFAULT_MEMORY_SIZE=1000
CACHE_ENABLE_REDIS=true
CACHE_COMPRESSION_THRESHOLD=512

# 监控配置
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
METRICS_ENABLED=true
```

### 2. Docker配置

```yaml
# docker-compose.cache.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: cbsc-redis
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - cbsc-network

  prometheus:
    image: prom/prometheus:latest
    container_name: cbsc-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    networks:
      - cbsc-network

  grafana:
    image: grafana/grafana:latest
    container_name: cbsc-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    networks:
      - cbsc-network

volumes:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  cbsc-network:
    driver: bridge
```

### 3. Prometheus配置

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'cbsc-api'
    static_configs:
      - targets: ['localhost:3004']
    metrics_path: '/monitoring/cache/metrics'
    scrape_interval: 5s

  - job_name: 'cbsc-health'
    static_configs:
      - targets: ['localhost:3004']
    metrics_path: '/monitoring/cache/health'
    scrape_interval: 30s
```

## 部署步骤

### 1. 环境准备

```bash
# 1. 安装依赖
pip install prometheus-client cachetools redis

# 2. 启动Redis
docker run -d --name cbsc-redis \
  -p 6379:6379 \
  redis:7-alpine \
  redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru

# 3. 启动监控系统
docker-compose -f docker-compose.cache.yml up -d
```

### 2. 应用配置

```python
# src/main.py - 应用初始化
from src.services.cache_manager import initialize_cache_manager
from src.monitoring.cache_metrics import initialize_cache_metrics

async def init_cache_system():
    """初始化缓存系统"""
    # 初始化缓存管理器
    cache_manager = initialize_cache_manager(
        redis_host=os.getenv("REDIS_HOST", "localhost"),
        redis_port=int(os.getenv("REDIS_PORT", 6379)),
        enable_redis=os.getenv("CACHE_ENABLE_REDIS", "true").lower() == "true",
        default_memory_size=int(os.getenv("CACHE_DEFAULT_MEMORY_SIZE", 1000))
    )

    # 初始化指标收集器
    metrics_collector = initialize_cache_metrics()

    return cache_manager, metrics_collector
```

### 3. API集成

```python
# src/api/main.py - 添加监控路由
from fastapi import FastAPI
from src.api.monitoring.cache_monitoring import router as cache_monitoring_router

app = FastAPI()

# 添加缓存监控路由
app.include_router(cache_monitoring_router)
```

## 性能验证

### 1. 运行集成测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio psutil

# 运行集成测试
pytest tests/test_cache_integration.py -v

# 运行压力测试
pytest tests/test_cache_stress.py -v
```

### 2. 性能基准

运行压力测试验证以下性能指标：

```bash
cd tests
python test_cache_stress.py
```

**预期结果**:
- 缓存命中率 > 75%
- 内存使用 < 1GB
- TPS > 1000 ops/s
- P95响应时间 < 100ms

### 3. 监控验证

访问以下端点验证监控系统：

```bash
# 健康检查
curl http://localhost:3004/monitoring/cache/health

# 指标导出
curl http://localhost:3004/monitoring/cache/metrics

# 统计信息
curl http://localhost:3004/monitoring/cache/stats
```

## Grafana仪表板

### 1. 导入仪表板

```bash
# 使用API导入仪表板
curl -X POST \
  http://admin:admin@localhost:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @monitoring/grafana/cache-dashboard.json
```

### 2. 仪表板功能

导入的仪表板包含以下面板：

1. **概览面板**
   - 总命中数/未命中数
   - 平均命中率
   - 内存使用量
   - Redis连接状态

2. **性能趋势**
   - 操作速率趋势
   - 各策略命中率
   - 内存使用趋势
   - 响应时间分布

3. **分析面板**
   - 热点数据分布
   - 错误率分析
   - 缓存效率统计

## 运维管理

### 1. 缓存管理API

```bash
# 清理缓存
curl -X POST "http://localhost:3004/monitoring/cache/clear?strategy=user"

# 缓存预热
curl -X POST "http://localhost:3004/monitoring/cache/warmup?strategy=strategy&keys=key1,key2,key3"

# 导出缓存数据
curl -X GET "http://localhost:3004/monitoring/cache/export?strategy=user"
```

### 2. 监控告警

```yaml
# prometheus_alerts.yml
groups:
  - name: cache_alerts
    rules:
      - alert: CacheHitRateLow
        expr: avg(cache_hit_rate) < 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "缓存命中率过低"
          description: "平均缓存命中率 {{ $value }} 低于50%"

      - alert: CacheMemoryHigh
        expr: sum(cache_memory_bytes) / (1024*1024*1024) > 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "缓存内存使用过高"
          description: "缓存内存使用 {{ $value }}GB 超过1GB"

      - alert: RedisConnectionDown
        expr: redis_connected == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis连接断开"
          description: "Redis连接已断开，缓存系统降级运行"
```

### 3. 故障排查

**常见问题及解决方案**:

1. **Redis连接失败**
   ```bash
   # 检查Redis状态
   docker logs cbsc-redis

   # 测试连接
   redis-cli -h localhost -p 6379 ping
   ```

2. **内存使用过高**
   ```bash
   # 检查缓存统计
   curl http://localhost:3004/monitoring/cache/stats

   # 清理大缓存策略
   curl -X POST "http://localhost:3004/monitoring/cache/clear?strategy=performance"
   ```

3. **命中率过低**
   ```bash
   # 分析访问模式
   curl http://localhost:3004/monitoring/cache/performance

   # 调整缓存策略
   # 编辑 src/services/cache_strategy.py
   # 优化TTL和缓存级别设置
   ```

## 性能优化建议

### 1. 缓存策略优化

- **高频数据**: 使用L1缓存，短TTL (30-60秒)
- **静态数据**: 使用L2缓存，长TTL (5-10分钟)
- **用户数据**: 使用L1+L2缓存，中等TTL (1-2分钟)
- **大型对象**: 启用压缩，阈值256-512字节

### 2. Redis配置优化

```redis
# redis.conf 关键配置
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### 3. 应用层优化

- 使用批量操作减少网络开销
- 实现缓存预热机制
- 优化键设计避免热点问题
- 定期清理过期数据

## 验证清单

部署完成后，验证以下项目：

- [ ] Redis服务正常启动
- [ ] Prometheus指标正常采集
- [ ] Grafana仪表板正常显示
- [ ] 缓存健康检查通过
- [ ] 集成测试全部通过
- [ ] 压力测试达到性能指标
- [ ] 监控告警正常工作
- [ ] API端点响应正常

完成上述验证后，缓存系统即可正式投入使用。
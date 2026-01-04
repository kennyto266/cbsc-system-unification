# 统一缓存管理系统

## 概述

本模块提供了一个统一的缓存管理系统，支持多级缓存（L1内存缓存 + L2 Redis缓存），具有以下特性：

- **多级缓存架构**：L1（内存）+ L2（Redis）
- **灵活的缓存策略**：预定义的策略和自定义策略支持
- **自动TTL过期**：基于时间和访问模式的过期机制
- **批量操作**：支持批量设置、获取和清理
- **性能监控**：内置指标收集和Prometheus导出
- **健康检查**：自动监控缓存系统健康状态
- **便捷装饰器**：简化函数级缓存的使用

## 快速开始

### 1. 初始化缓存管理器

```python
from src.services import initialize_cache_manager, get_cache_manager

# 初始化全局缓存管理器
cache_manager = initialize_cache_manager(
    redis_host="localhost",
    redis_port=6379,
    redis_db=0,
    enable_redis=True,
    default_memory_size=1000
)

# 或者直接获取全局实例
cache_manager = get_cache_manager()
```

### 2. 基础缓存操作

```python
from src.services import get_cache_manager

cache_manager = get_cache_manager()

# 设置缓存
cache_manager.set("strategy", "strategy_123", strategy_data, ttl=300)

# 获取缓存
data = cache_manager.get("strategy", "strategy_123")

# 检查是否存在
exists = cache_manager.exists("strategy", "strategy_123")

# 删除缓存
cache_manager.delete("strategy", "strategy_123")

# 批量清理（支持通配符）
deleted = cache_manager.clear_pattern("strategy", "strategy_*")
```

### 3. 使用装饰器简化缓存

```python
from src.services import cached, invalidate_cache

# 缓存函数结果
@cached("strategy", ttl=60)
def get_strategy_data(strategy_id: str):
    # 复杂的数据库查询
    return load_strategy_from_db(strategy_id)

# 自动失效缓存
@invalidate_cache("strategy", "strategy_*")
def update_strategy(strategy_id: str, data: dict):
    # 更新数据库
    return update_strategy_in_db(strategy_id, data)

# 基于参数的缓存
from src.services import cache_on_arguments

@cache_on_arguments("performance", ttl=30)
def calculate_metrics(data, period="1d"):
    return complex_calculation(data, period)
```

### 4. 集成到Manager类

```python
from src.services import StrategyManagerCacheMixin, cached_method

class MyStrategyManager(StrategyManagerCacheMixin):
    def __init__(self):
        super().__init__()
        # 自动初始化缓存功能

    @cached_method("strategy", ttl=300)
    def get_strategy(self, strategy_id: str):
        return self._load_from_database(strategy_id)

    # 使用混入提供的专用方法
    def get_user_strategies_cached(self, user_id: int):
        # 尝试从缓存获取
        cached = self.get_user_strategy_list_cache(user_id)
        if cached:
            return cached

        # 加载并缓存
        strategies = self._load_user_strategies(user_id)
        self.set_user_strategy_list_cache(user_id, strategies, ttl=120)
        return strategies
```

## 缓存策略

系统提供了预定义的缓存策略，针对不同类型的数据优化：

| 策略名称 | TTL | 缓存级别 | 用途 |
|---------|-----|---------|------|
| strategy | 5分钟 | L2_ONLY | 策略数据（较大） |
| performance | 30秒 | L1_ONLY | 性能数据（高频访问） |
| user | 1分钟 | L1_L2 | 用户数据（需要持久化） |
| config | 10分钟 | L2_ONLY | 配置数据（相对静态） |
| market_data | 5秒 | L1_ONLY | 市场数据（实时更新） |
| session | 30分钟 | L1_L2 | 会话数据 |
| realtime_signals | 1秒 | L1_ONLY | 实时信号（极高频） |
| api_stats | 1小时 | L2_ONLY | API统计数据 |

### 自定义策略

```python
from src.services import CacheStrategy, CacheLevel, EvictionPolicy

# 创建自定义策略
custom_strategy = CacheStrategy(
    name="custom",
    ttl_seconds=600,
    cache_level=CacheLevel.L1_L2,
    max_memory_items=500,
    eviction_policy=EvictionPolicy.LRU,
    enable_compression=True,
    compression_threshold=1024
)

# 注册策略
cache_manager.register_strategy(custom_strategy)
```

## 监控和指标

### 1. 启用监控

```python
from src.services import setup_monitoring

# 启用缓存监控
setup_monitoring(
    enable_metrics=True,
    enable_health_checks=True,
    metrics_interval=60
)
```

### 2. 获取缓存指标

```python
from src.services import get_cache_manager, get_metrics_collector

# 获取实时指标
cache_manager = get_cache_manager()
metrics = cache_manager.get_metrics("strategy")
print(f"命中率: {metrics.hit_rate:.2%}")
print(f"平均获取时间: {metrics.avg_get_time:.4f}s")

# 获取历史指标
collector = get_metrics_collector()
snapshots = collector.get_recent_snapshots("strategy", minutes=60)
agg_stats = collector.get_aggregated_stats("strategy", hours=24)
```

### 3. Prometheus指标导出

```python
from src.services import get_prometheus_exporter

exporter = get_prometheus_exporter()
prometheus_metrics = exporter.export_metrics()

# 可以在HTTP端点中暴露
from flask import Flask
app = Flask(__name__)

@app.route('/metrics')
def metrics():
    return exporter.export_metrics(), 200, {'Content-Type': 'text/plain'}
```

### 4. 健康检查

```python
from src.services import get_health_checker

health_checker = get_health_checker()
health_status = health_checker.check_health()

if health_status["overall_status"] == "unhealthy":
    for alert in health_status["alerts"]:
        print(f"告警: {alert['message']}")
```

## 高级功能

### 1. 批量操作

```python
from src.services import BatchCacheHelper

# 批量获取
strategies = BatchCacheHelper.batch_get_strategies(["s1", "s2", "s3"])

# 批量设置
data = {"s1": {...}, "s2": {...}}
success_count = BatchCacheHelper.batch_set_strategies(data, ttl=300)

# 批量失效
deleted = BatchCacheHelper.batch_invalidate_strategies(["s1", "s2"])
```

### 2. 异步支持

```python
from src.services import AsyncCacheAdapter, get_async_adapter
import asyncio

# 异步缓存操作
adapter = get_async_adapter()

async def example():
    value = await adapter.get("strategy", "key")
    await adapter.set("strategy", "key", value, ttl=300)
    await adapter.delete("strategy", "key")
```

### 3. 缓存预热

```python
def warm_up_strategy_cache(strategy_ids: List[str]):
    """预热策略缓存"""
    cache_manager = get_cache_manager()

    def data_loader(ids):
        results = {}
        for sid in ids:
            results[sid] = load_strategy_from_db(sid)
        return results

    count = cache_manager.warm_up("strategy", data_loader, strategy_ids)
    print(f"预热完成: {count}/{len(strategy_ids)}")
```

## 最佳实践

### 1. 选择合适的缓存策略

- **高频访问的数据**：使用L1_ONLY策略，如性能指标、实时信号
- **大型数据**：使用L2_ONLY策略，启用压缩
- **用户会话数据**：使用L1_L2策略，保证持久化和快速访问
- **配置数据**：使用L2_ONLY策略，较长TTL

### 2. 设置合理的TTL

- **实时数据**：5-60秒
- **用户数据**：1-30分钟
- **策略数据**：5-10分钟
- **配置数据**：10分钟-1小时

### 3. 监控关键指标

- **命中率**：目标 > 70%
- **平均响应时间**：目标 < 1ms（L1），< 5ms（L2）
- **内存使用率**：监控并设置合理的限制
- **Redis连接**：确保连接稳定

### 4. 缓存失效策略

- 在数据更新时主动失效相关缓存
- 使用模式匹配批量清理相关缓存
- 定期清理过期和低频访问的数据

## 故障排除

### 1. Redis连接失败

系统会自动降级到纯内存缓存模式：

```python
# 检查Redis状态
cache_info = cache_manager.get_cache_info()
if not cache_info["redis_connected"]:
    print("Redis未连接，使用纯内存缓存")
```

### 2. 内存使用过高

- 减少内存缓存的最大条目数
- 启用数据压缩
- 使用L2_ONLY策略转移数据到Redis

### 3. 缓存命中率低

- 检查TTL设置是否过短
- 分析访问模式，优化缓存键设计
- 使用预热策略提高初始命中率

## API参考

详细的API文档请参考各模块的docstring：

- `CacheManager`: 核心缓存管理器
- `CacheStrategy`: 缓存策略配置
- `cached`: 缓存装饰器
- `StrategyManagerCacheMixin`: Manager类缓存混入
- `CacheMetricsCollector`: 指标收集器
- `PrometheusMetricsExporter`: Prometheus导出器
- `CacheHealthChecker`: 健康检查器
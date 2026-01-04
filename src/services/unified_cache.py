"""
Unified Cache Service
====================

Complete caching solution combining all cache implementations:
- Multi-tier caching (L1-L4)
- Redis and InfluxDB integration
- Async operations
- Decorators and mixins
- Monitoring and alerting
- Thread-safe operations
"""

from .cache_manager import (
    CacheManager,
    MemoryCache,
    RedisCache,
    get_cache_manager,
)

from .cache_strategy import (
    CacheStrategy,
    CacheLevel,
    CacheStrategies,
    CacheKeys,
    CacheMetrics,
    EvictionPolicy,
)

from .cache_decorators import (
    cached,
    async_cached,
    method_cached,
    invalidate_cache,
    cache_with_fallback,
    timed_cache,
    cache_on_arguments,
    cached_result,
    BatchCache,
    create_batch_cache,
)

from .cache_integration import (
    CacheMixin,
    StrategyManagerCacheMixin,
    AsyncCacheAdapter,
    get_async_adapter,
    cached_method,
    invalidate_cache_method,
    BatchCacheHelper,
)

from .cache_monitoring import (
    CacheSnapshot,
    CacheMetricsCollector,
    PrometheusMetricsExporter,
    CacheHealthChecker,
    get_metrics_collector,
    get_prometheus_exporter,
    get_health_checker,
    setup_monitoring,
    check_redis_health,
    check_cache_hit_rates,
    check_memory_usage,
)

__all__ = [
    # Core
    "CacheManager",
    "MemoryCache",
    "RedisCache",
    "get_cache_manager",

    # Strategy
    "CacheStrategy",
    "CacheLevel",
    "CacheStrategies",
    "CacheKeys",
    "CacheMetrics",
    "EvictionPolicy",

    # Decorators
    "cached",
    "async_cached",
    "method_cached",
    "invalidate_cache",
    "cache_with_fallback",
    "timed_cache",
    "cache_on_arguments",
    "cached_result",
    "BatchCache",
    "create_batch_cache",

    # Integration
    "CacheMixin",
    "StrategyManagerCacheMixin",
    "AsyncCacheAdapter",
    "get_async_adapter",
    "cached_method",
    "invalidate_cache_method",
    "BatchCacheHelper",

    # Monitoring
    "CacheSnapshot",
    "CacheMetricsCollector",
    "PrometheusMetricsExporter",
    "CacheHealthChecker",
    "get_metrics_collector",
    "get_prometheus_exporter",
    "get_health_checker",
    "setup_monitoring",
    "check_redis_health",
    "check_cache_hit_rates",
    "check_memory_usage",
]

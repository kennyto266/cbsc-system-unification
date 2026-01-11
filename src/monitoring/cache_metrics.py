"""
缓存监控指标
Cache Monitoring Metrics

实现Prometheus指标导出，收集缓存系统的性能数据
"""

import time
import logging
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from prometheus_client.core import REGISTRY as DEFAULT_REGISTRY
from ..services.cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


class CacheMetricsCollector:
    """
    缓存指标收集器

    收集并导出缓存系统的Prometheus指标
    """

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        初始化指标收集器

        Args:
            registry: Prometheus注册表，默认使用全局注册表
        """
        self.registry = registry or DEFAULT_REGISTRY

        # 定义Prometheus指标
        self._define_metrics()

        # 注册指标
        self._register_metrics()

        # 缓存管理器引用
        self.cache_manager = get_cache_manager()

        # 上次更新时间
        self.last_update_time = 0
        self.update_interval = 30  # 30秒更新一次

    def _define_metrics(self):
        """定义Prometheus指标"""

        # 缓存操作指标
        self.cache_hits_total = Counter(
            'cache_hits_total',
            'Total number of cache hits',
            ['strategy', 'cache_level'],
            registry=self.registry
        )

        self.cache_misses_total = Counter(
            'cache_misses_total',
            'Total number of cache misses',
            ['strategy', 'cache_level'],
            registry=self.registry
        )

        self.cache_sets_total = Counter(
            'cache_sets_total',
            'Total number of cache sets',
            ['strategy', 'cache_level'],
            registry=self.registry
        )

        self.cache_deletes_total = Counter(
            'cache_deletes_total',
            'Total number of cache deletes',
            ['strategy', 'cache_level'],
            registry=self.registry
        )

        # 缓存性能指标
        self.cache_operation_duration_seconds = Histogram(
            'cache_operation_duration_seconds',
            'Cache operation duration in seconds',
            ['strategy', 'operation', 'cache_level'],
            registry=self.registry,
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
        )

        # 缓存大小指标
        self.cache_memory_bytes = Gauge(
            'cache_memory_bytes',
            'Cache memory usage in bytes',
            ['strategy', 'cache_type'],
            registry=self.registry
        )

        self.cache_items_count = Gauge(
            'cache_items_count',
            'Number of items in cache',
            ['strategy', 'cache_type'],
            registry=self.registry
        )

        # 缓存健康指标
        self.cache_hit_rate = Gauge(
            'cache_hit_rate',
            'Cache hit rate (0-1)',
            ['strategy'],
            registry=self.registry
        )

        self.cache_error_rate = Gauge(
            'cache_error_rate',
            'Cache error rate (0-1)',
            ['strategy', 'error_type'],
            registry=self.registry
        )

        # Redis特定指标
        self.redis_connected = Gauge(
            'redis_connected',
            'Redis connection status (1 if connected, 0 if not)',
            registry=self.registry
        )

        self.redis_memory_bytes = Gauge(
            'redis_memory_bytes',
            'Redis memory usage in bytes',
            registry=self.registry
        )

        self.redis_connections = Gauge(
            'redis_connections',
            'Number of connected Redis clients',
            registry=self.registry
        )

    def _register_metrics(self):
        """注册指标到Prometheus"""
        try:
            # 如果使用自定义注册表，需要手动注册
            if self.registry is not DEFAULT_REGISTRY:
                for metric in [
                    self.cache_hits_total,
                    self.cache_misses_total,
                    self.cache_sets_total,
                    self.cache_deletes_total,
                    self.cache_operation_duration_seconds,
                    self.cache_memory_bytes,
                    self.cache_items_count,
                    self.cache_hit_rate,
                    self.cache_error_rate,
                    self.redis_connected,
                    self.redis_memory_bytes,
                    self.redis_connections
                ]:
                    self.registry.register(metric)

            logger.info("Cache metrics registered successfully")

        except Exception as e:
            logger.error(f"Failed to register cache metrics: {e}")

    def update_metrics(self):
        """更新缓存指标"""
        try:
            current_time = time.time()

            # 限制更新频率
            if current_time - self.last_update_time < self.update_interval:
                return

            # 获取缓存信息
            cache_info = self.cache_manager.get_cache_info()

            # 更新Redis连接状态
            redis_connected = 1 if cache_info.get("redis_connected", False) else 0
            self.redis_connected.set(redis_connected)

            # 更新Redis特定指标
            if redis_connected and "redis_info" in cache_info:
                redis_info = cache_info["redis_info"]
                self.redis_memory_bytes.set(redis_info.get("used_memory_bytes", 0))
                self.redis_connections.set(redis_info.get("connected_clients", 0))

            # 更新策略级别指标
            total_metrics = cache_info.get("total_metrics", {})
            overall_hit_rate = total_metrics.get("overall_hit_rate", 0.0)

            # 更新各策略的指标
            strategies = self.cache_manager.list_strategies()
            for strategy_name, strategy in strategies.items():
                metrics = self.cache_manager.get_metrics(strategy_name)

                # 更新操作计数
                labels = {'strategy': strategy_name}

                # 这些指标需要增量更新，这里简化处理
                # 实际生产环境中应该从上次记录的值开始累加

                # 更新命中率
                hit_rate = metrics.hit_rate
                self.cache_hit_rate.labels(strategy=strategy_name).set(hit_rate)

                # 更新内存缓存大小
                memory_caches = cache_info.get("memory_caches", {})
                if strategy_name in memory_caches:
                    memory_info = memory_caches[strategy_name]
                    self.cache_items_count.labels(
                        strategy=strategy_name,
                        cache_type='memory'
                    ).set(memory_info.get("size", 0))

                    # 估算内存使用（简化）
                    estimated_memory = memory_info.get("size", 0) * 1024  # 假设每项1KB
                    self.cache_memory_bytes.labels(
                        strategy=strategy_name,
                        cache_type='memory'
                    ).set(estimated_memory)

            self.last_update_time = current_time

        except Exception as e:
            logger.error(f"Failed to update cache metrics: {e}")

    def record_cache_hit(self, strategy: str, cache_level: str, duration: float):
        """记录缓存命中"""
        self.cache_hits_total.labels(strategy=strategy, cache_level=cache_level).inc()
        self.cache_operation_duration_seconds.labels(
            strategy=strategy,
            operation='get',
            cache_level=cache_level
        ).observe(duration)

    def record_cache_miss(self, strategy: str, cache_level: str, duration: float):
        """记录缓存未命中"""
        self.cache_misses_total.labels(strategy=strategy, cache_level=cache_level).inc()
        self.cache_operation_duration_seconds.labels(
            strategy=strategy,
            operation='get',
            cache_level=cache_level
        ).observe(duration)

    def record_cache_set(self, strategy: str, cache_level: str, duration: float):
        """记录缓存设置"""
        self.cache_sets_total.labels(strategy=strategy, cache_level=cache_level).inc()
        self.cache_operation_duration_seconds.labels(
            strategy=strategy,
            operation='set',
            cache_level=cache_level
        ).observe(duration)

    def record_cache_delete(self, strategy: str, cache_level: str, duration: float):
        """记录缓存删除"""
        self.cache_deletes_total.labels(strategy=strategy, cache_level=cache_level).inc()
        self.cache_operation_duration_seconds.labels(
            strategy=strategy,
            operation='delete',
            cache_level=cache_level
        ).observe(duration)

    def record_cache_error(self, strategy: str, error_type: str, error_count: int = 1):
        """记录缓存错误"""
        # 计算错误率（简化实现）
        total_operations = (
            self.cache_hits_total.labels(strategy=strategy, cache_level='total')._value._value +
            self.cache_misses_total.labels(strategy=strategy, cache_level='total')._value._value +
            self.cache_sets_total.labels(strategy=strategy, cache_level='total')._value._value
        )

        if total_operations > 0:
            error_rate = error_count / total_operations
            self.cache_error_rate.labels(strategy=strategy, error_type=error_type).set(error_rate)

    def get_metrics_export(self) -> str:
        """
        获取Prometheus格式的指标导出

        Returns:
            Prometheus格式的指标字符串
        """
        try:
            # 更新指标
            self.update_metrics()

            # 生成导出
            return generate_latest(self.registry).decode('utf-8')

        except Exception as e:
            logger.error(f"Failed to generate metrics export: {e}")
            return "# Failed to generate metrics\n"


# 全局指标收集器实例
_metrics_collector: Optional[CacheMetricsCollector] = None


def get_metrics_collector() -> CacheMetricsCollector:
    """获取全局指标收集器实例"""
    global _metrics_collector

    if _metrics_collector is None:
        _metrics_collector = CacheMetricsCollector()

    return _metrics_collector


def initialize_cache_metrics(registry: Optional[CollectorRegistry] = None) -> CacheMetricsCollector:
    """
    初始化缓存指标收集器

    Args:
        registry: Prometheus注册表

    Returns:
        指标收集器实例
    """
    global _metrics_collector

    _metrics_collector = CacheMetricsCollector(registry)

    logger.info("Cache metrics collector initialized")

    return _metrics_collector


# 便捷函数
def record_cache_hit(strategy: str, cache_level: str, duration: float):
    """记录缓存命中（便捷函数）"""
    get_metrics_collector().record_cache_hit(strategy, cache_level, duration)


def record_cache_miss(strategy: str, cache_level: str, duration: float):
    """记录缓存未命中（便捷函数）"""
    get_metrics_collector().record_cache_miss(strategy, cache_level, duration)


def record_cache_set(strategy: str, cache_level: str, duration: float):
    """记录缓存设置（便捷函数）"""
    get_metrics_collector().record_cache_set(strategy, cache_level, duration)


def record_cache_delete(strategy: str, cache_level: str, duration: float):
    """记录缓存删除（便捷函数）"""
    get_metrics_collector().record_cache_delete(strategy, cache_level, duration)


def record_cache_error(strategy: str, error_type: str, error_count: int = 1):
    """记录缓存错误（便捷函数）"""
    get_metrics_collector().record_cache_error(strategy, error_type, error_count)


def get_metrics_export() -> str:
    """获取指标导出（便捷函数）"""
    return get_metrics_collector().get_metrics_export()
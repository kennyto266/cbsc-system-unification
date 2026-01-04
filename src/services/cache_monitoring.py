"""
缓存监控指标
Cache Monitoring Metrics

提供缓存性能监控和指标收集功能，支持Prometheus格式导出。
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque

from .cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


@dataclass
class CacheSnapshot:
    """缓存快照数据"""
    timestamp: datetime
    strategy_name: str
    hits: int
    misses: int
    sets: int
    deletes: int
    memory_size: int
    redis_size: Optional[int] = None
    hit_rate: float = 0.0
    avg_get_time: float = 0.0
    avg_set_time: float = 0.0


class CacheMetricsCollector:
    """
    缓存指标收集器

    定期收集和存储缓存性能指标。
    """

    def __init__(self, collection_interval: int = 60, max_snapshots: int = 1440):
        """
        初始化指标收集器

        Args:
            collection_interval: 收集间隔（秒）
            max_snapshots: 最大快照数量（24小时的数据）
        """
        self.collection_interval = collection_interval
        self.max_snapshots = max_snapshots

        # 存储历史快照
        self.snapshots: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_snapshots))

        # 聚合统计
        self.aggregated_stats: Dict[str, Dict] = defaultdict(dict)

        # 收集线程
        self._collector_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.RLock()

        # 回调函数
        self._callbacks: List[Callable[[CacheSnapshot], None]] = []

    def start(self):
        """开始收集指标"""
        if self._running:
            logger.warning("Metrics collector already running")
            return

        self._running = True
        self._collector_thread = threading.Thread(
            target=self._collect_loop,
            name="CacheMetricsCollector",
            daemon=True
        )
        self._collector_thread.start()
        logger.info(f"Cache metrics collector started (interval: {self.collection_interval}s)")

    def stop(self):
        """停止收集指标"""
        if not self._running:
            return

        self._running = False
        if self._collector_thread and self._collector_thread.is_alive():
            self._collector_thread.join(timeout=5)
        logger.info("Cache metrics collector stopped")

    def add_callback(self, callback: Callable[[CacheSnapshot], None]):
        """添加指标回调函数"""
        self._callbacks.append(callback)

    def get_recent_snapshots(self, strategy_name: str, minutes: int = 60) -> List[CacheSnapshot]:
        """
        获取最近的快照

        Args:
            strategy_name: 策略名称
            minutes: 时间范围（分钟）

        Returns:
            快照列表
        """
        with self._lock:
            snapshots = list(self.snapshots[strategy_name])
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            return [s for s in snapshots if s.timestamp >= cutoff_time]

    def get_aggregated_stats(self, strategy_name: str, hours: int = 24) -> Dict[str, Any]:
        """
        获取聚合统计

        Args:
            strategy_name: 策略名称
            hours: 时间范围（小时）

        Returns:
            聚合统计数据
        """
        snapshots = self.get_recent_snapshots(strategy_name, minutes=hours * 60)

        if not snapshots:
            return {}

        # 计算聚合指标
        total_hits = sum(s.hits for s in snapshots)
        total_misses = sum(s.misses for s in snapshots)
        total_sets = sum(s.sets for s in snapshots)
        total_deletes = sum(s.deletes for s in snapshots)

        avg_hit_rate = sum(s.hit_rate for s in snapshots) / len(snapshots)
        avg_memory_size = sum(s.memory_size for s in snapshots) / len(snapshots)

        # 计算趋势
        if len(snapshots) >= 2:
            recent_hit_rate = snapshots[-1].hit_rate
            previous_hit_rate = snapshots[-2].hit_rate
            hit_rate_trend = recent_hit_rate - previous_hit_rate
        else:
            hit_rate_trend = 0

        return {
            "strategy_name": strategy_name,
            "time_range_hours": hours,
            "snapshot_count": len(snapshots),
            "total_hits": total_hits,
            "total_misses": total_misses,
            "total_sets": total_sets,
            "total_deletes": total_deletes,
            "avg_hit_rate": avg_hit_rate,
            "avg_memory_size": avg_memory_size,
            "hit_rate_trend": hit_rate_trend,
            "last_updated": snapshots[-1].timestamp if snapshots else None
        }

    def _collect_loop(self):
        """指标收集循环"""
        while self._running:
            try:
                self._collect_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                time.sleep(self.collection_interval)

    def _collect_metrics(self):
        """收集指标"""
        cache_manager = get_cache_manager()
        all_metrics = cache_manager.get_metrics()  # 获取所有策略的指标

        for strategy_name, metrics in all_metrics.items():
            # 创建快照
            snapshot = CacheSnapshot(
                timestamp=datetime.now(),
                strategy_name=strategy_name,
                hits=metrics.hits,
                misses=metrics.misses,
                sets=metrics.sets,
                deletes=metrics.deletes,
                memory_size=metrics.memory_size,
                redis_size=metrics.redis_size,
                hit_rate=metrics.hit_rate,
                avg_get_time=metrics.avg_get_time,
                avg_set_time=metrics.avg_set_time
            )

            # 存储快照
            with self._lock:
                self.snapshots[strategy_name].append(snapshot)

            # 调用回调函数
            for callback in self._callbacks:
                try:
                    callback(snapshot)
                except Exception as e:
                    logger.error(f"Error in metrics callback: {e}")


class PrometheusMetricsExporter:
    """
    Prometheus指标导出器

    将缓存指标转换为Prometheus格式。
    """

    def __init__(self, metrics_collector: CacheMetricsCollector):
        self.metrics_collector = metrics_collector

    def export_metrics(self) -> str:
        """
        导出Prometheus格式的指标

        Returns:
            Prometheus格式的指标字符串
        """
        lines = []

        # 获取当前缓存信息
        cache_manager = get_cache_manager()
        cache_info = cache_manager.get_cache_info()

        # 导出基础指标
        lines.extend(self._export_basic_metrics(cache_info))

        # 导出各策略指标
        all_metrics = cache_manager.get_metrics()
        for strategy_name, metrics in all_metrics.items():
            lines.extend(self._export_strategy_metrics(strategy_name, metrics))

        # 导出聚合指标
        lines.extend(self._export_aggregated_metrics())

        return "\n".join(lines)

    def _export_basic_metrics(self, cache_info: Dict) -> List[str]:
        """导出基础指标"""
        metrics = []
        timestamp = int(time.time() * 1000)

        # Redis连接状态
        metrics.append(
            f'cbsc_cache_redis_connected {int(cache_info.get("redis_connected", False))} {timestamp}'
        )

        # 内存缓存数量
        metrics.append(
            f'cbsc_cache_memory_caches {len(cache_info.get("memory_caches", {}))} {timestamp}'
        )

        # 策略数量
        metrics.append(
            f'cbsc_cache_strategies {cache_info.get("strategies_count", 0)} {timestamp}'
        )

        # 总体统计
        total_metrics = cache_info.get("total_metrics", {})
        metrics.append(
            f'cbsc_cache_total_hits {total_metrics.get("total_hits", 0)} {timestamp}'
        )
        metrics.append(
            f'cbsc_cache_total_misses {total_metrics.get("total_misses", 0)} {timestamp}'
        )
        metrics.append(
            f'cbsc_cache_total_sets {total_metrics.get("total_sets", 0)} {timestamp}'
        )
        metrics.append(
            f'cbsc_cache_total_deletes {total_metrics.get("total_deletes", 0)} {timestamp}'
        )
        metrics.append(
            f'cbsc_cache_overall_hit_rate {total_metrics.get("overall_hit_rate", 0)} {timestamp}'
        )

        # Redis信息
        redis_info = cache_info.get("redis_info", {})
        if redis_info.get("connected"):
            metrics.append(
                f'cbsc_redis_memory_bytes {redis_info.get("used_memory_bytes", 0)} {timestamp}'
            )
            metrics.append(
                f'cbsc_redis_total_commands {redis_info.get("total_commands_processed", 0)} {timestamp}'
            )
            metrics.append(
                f'cbsc_redis_keyspace_hits {redis_info.get("keyspace_hits", 0)} {timestamp}'
            )
            metrics.append(
                f'cbsc_redis_keyspace_misses {redis_info.get("keyspace_misses", 0)} {timestamp}'
            )

        return metrics

    def _export_strategy_metrics(self, strategy_name: str, metrics) -> List[str]:
        """导出策略指标"""
        lines = []
        timestamp = int(time.time() * 1000)

        # 策略标签
        labels = f'strategy="{strategy_name}"'

        # 基础指标
        lines.append(f'cbsc_cache_strategy_hits{{{labels}}} {metrics.hits} {timestamp}')
        lines.append(f'cbsc_cache_strategy_misses{{{labels}}} {metrics.misses} {timestamp}')
        lines.append(f'cbsc_cache_strategy_sets{{{labels}}} {metrics.sets} {timestamp}')
        lines.append(f'cbsc_cache_strategy_deletes{{{labels}}} {metrics.deletes} {timestamp}')
        lines.append(f'cbsc_cache_strategy_evictions{{{labels}}} {metrics.evictions} {timestamp}')
        lines.append(f'cbsc_cache_strategy_hit_rate{{{labels}}} {metrics.hit_rate} {timestamp}')
        lines.append(f'cbsc_cache_strategy_avg_get_time{{{labels}}} {metrics.avg_get_time} {timestamp}')
        lines.append(f'cbsc_cache_strategy_avg_set_time{{{labels}}} {metrics.avg_set_time} {timestamp}')

        # 大小指标
        lines.append(f'cbsc_cache_strategy_memory_size{{{labels}}} {metrics.memory_size} {timestamp}')
        lines.append(f'cbsc_cache_strategy_redis_size{{{labels}}} {metrics.redis_size or 0} {timestamp}')

        # 错误指标
        lines.append(f'cbsc_cache_strategy_get_errors{{{labels}}} {metrics.get_errors} {timestamp}')
        lines.append(f'cbsc_cache_strategy_set_errors{{{labels}}} {metrics.set_errors} {timestamp}')

        return lines

    def _export_aggregated_metrics(self) -> List[str]:
        """导出聚合指标"""
        lines = []
        timestamp = int(time.time() * 1000)

        # 获取24小时聚合统计
        all_metrics = get_cache_manager().get_metrics()
        for strategy_name in all_metrics.keys():
            agg_stats = self.metrics_collector.get_aggregated_stats(strategy_name, hours=24)

            if agg_stats:
                labels = f'strategy="{strategy_name}"'

                # 24小时统计
                lines.append(
                    f'cbsc_cache_24h_total_hits{{{labels}}} {agg_stats["total_hits"]} {timestamp}'
                )
                lines.append(
                    f'cbsc_cache_24h_total_misses{{{labels}}} {agg_stats["total_misses"]} {timestamp}'
                )
                lines.append(
                    f'cbsc_cache_24h_avg_hit_rate{{{labels}}} {agg_stats["avg_hit_rate"]} {timestamp}'
                )
                lines.append(
                    f'cbsc_cache_24h_hit_rate_trend{{{labels}}} {agg_stats["hit_rate_trend"]} {timestamp}'
                )

        return lines


class CacheHealthChecker:
    """
    缓存健康检查器

    监控缓存系统的健康状态并触发告警。
    """

    def __init__(self):
        self.health_checks: List[Callable[[], Dict[str, Any]]] = []
        self.alert_callbacks: List[Callable[[str, Dict], None]] = []

    def add_health_check(self, check_func: Callable[[], Dict[str, Any]]):
        """添加健康检查函数"""
        self.health_checks.append(check_func)

    def add_alert_callback(self, callback: Callable[[str, Dict], None]):
        """添加告警回调函数"""
        self.alert_callbacks.append(callback)

    def check_health(self) -> Dict[str, Any]:
        """执行健康检查"""
        results = {
            "overall_status": "healthy",
            "checks": {},
            "alerts": [],
            "timestamp": datetime.now().isoformat()
        }

        all_healthy = True

        for check_func in self.health_checks:
            try:
                check_result = check_func()
                check_name = check_func.__name__
                results["checks"][check_name] = check_result

                if not check_result.get("healthy", True):
                    all_healthy = False
                    alert_msg = check_result.get("message", "Health check failed")
                    results["alerts"].append({
                        "check": check_name,
                        "severity": check_result.get("severity", "warning"),
                        "message": alert_msg
                    })

                    # 触发告警回调
                    for callback in self.alert_callbacks:
                        try:
                            callback(check_name, check_result)
                        except Exception as e:
                            logger.error(f"Error in alert callback: {e}")

            except Exception as e:
                logger.error(f"Health check error: {e}")
                all_healthy = False

        results["overall_status"] = "healthy" if all_healthy else "unhealthy"
        return results


# 预定义的健康检查函数
def check_redis_health() -> Dict[str, Any]:
    """检查Redis健康状态"""
    cache_manager = get_cache_manager()
    cache_info = cache_manager.get_cache_info()

    redis_connected = cache_info.get("redis_connected", False)
    redis_info = cache_info.get("redis_info", {})

    if not redis_connected:
        return {
            "healthy": False,
            "severity": "critical",
            "message": "Redis is not connected"
        }

    # 检查Redis内存使用
    used_memory = redis_info.get("used_memory_bytes", 0)
    if used_memory > 1024 * 1024 * 1024:  # 1GB
        return {
            "healthy": False,
            "severity": "warning",
            "message": f"Redis memory usage is high: {used_memory / 1024 / 1024:.2f} MB"
        }

    # 检查命中率
    hits = redis_info.get("keyspace_hits", 0)
    misses = redis_info.get("keyspace_misses", 0)
    total = hits + misses
    if total > 0:
        hit_rate = hits / total
        if hit_rate < 0.5:
            return {
                "healthy": False,
                "severity": "warning",
                "message": f"Redis hit rate is low: {hit_rate:.2%}"
            }

    return {"healthy": True}


def check_cache_hit_rates() -> Dict[str, Any]:
    """检查缓存命中率"""
    cache_manager = get_cache_manager()
    all_metrics = cache_manager.get_metrics()

    low_hit_rate_strategies = []

    for strategy_name, metrics in all_metrics.items():
        total_requests = metrics.hits + metrics.misses
        if total_requests > 100:  # 至少100次请求
            hit_rate = metrics.hit_rate
            if hit_rate < 0.3:  # 命中率低于30%
                low_hit_rate_strategies.append({
                    "strategy": strategy_name,
                    "hit_rate": hit_rate,
                    "total_requests": total_requests
                })

    if low_hit_rate_strategies:
        return {
            "healthy": False,
            "severity": "warning",
            "message": f"Low hit rate for strategies: {[s['strategy'] for s in low_hit_rate_strategies]}",
            "details": low_hit_rate_strategies
        }

    return {"healthy": True}


def check_memory_usage() -> Dict[str, Any]:
    """检查内存使用"""
    import psutil

    process = psutil.Process()
    memory_info = process.memory_info()
    memory_percent = process.memory_percent()

    if memory_percent > 80:  # 内存使用超过80%
        return {
            "healthy": False,
            "severity": "critical",
            "message": f"High memory usage: {memory_percent:.1f}%",
            "details": {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024
            }
        }

    return {"healthy": True}


# 全局实例
_metrics_collector: Optional[CacheMetricsCollector] = None
_prometheus_exporter: Optional[PrometheusMetricsExporter] = None
_health_checker: Optional[CacheHealthChecker] = None


def get_metrics_collector() -> CacheMetricsCollector:
    """获取全局指标收集器"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = CacheMetricsCollector()
        _metrics_collector.start()
    return _metrics_collector


def get_prometheus_exporter() -> PrometheusMetricsExporter:
    """获取全局Prometheus导出器"""
    global _prometheus_exporter
    if _prometheus_exporter is None:
        collector = get_metrics_collector()
        _prometheus_exporter = PrometheusMetricsExporter(collector)
    return _prometheus_exporter


def get_health_checker() -> CacheHealthChecker:
    """获取全局健康检查器"""
    global _health_checker
    if _health_checker is None:
        _health_checker = CacheHealthChecker()
        # 添加默认的健康检查
        _health_checker.add_health_check(check_redis_health)
        _health_checker.add_health_check(check_cache_hit_rates)
        _health_checker.add_health_check(check_memory_usage)
    return _health_checker


def setup_monitoring(
    enable_metrics: bool = True,
    enable_health_checks: bool = True,
    metrics_interval: int = 60
):
    """
    设置缓存监控

    Args:
        enable_metrics: 是否启用指标收集
        enable_health_checks: 是否启用健康检查
        metrics_interval: 指标收集间隔（秒）
    """
    if enable_metrics:
        collector = get_metrics_collector()
        if collector.collection_interval != metrics_interval:
            collector.stop()
            collector.collection_interval = metrics_interval
            collector.start()
        logger.info("Cache metrics monitoring enabled")

    if enable_health_checks:
        health_checker = get_health_checker()
        logger.info("Cache health checking enabled")


__all__ = [
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
    "check_memory_usage"
]
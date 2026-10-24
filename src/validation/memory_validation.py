#!/usr/bin/env python3
"""
Phase 4: 内存使用验证系统 (<8GB限制)
Memory Usage Validation System for GPU-to-CPU Migration

This module provides comprehensive memory usage validation, monitoring, and
optimization to ensure the system stays within the 8GB memory limit while
maintaining optimal performance.

Key Features:
- Real-time memory monitoring and validation
- Memory leak detection and prevention
- Memory usage profiling and analysis
- Memory optimization recommendations
- Memory pressure detection and handling
- Memory efficiency scoring
- Automatic memory cleanup and management
"""

import logging
import time
import threading
import gc
import psutil
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import deque, defaultdict
import json
import tracemalloc
import objgraph
import sys
import weakref
import resource
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class MemorySnapshot:
    """内存快照"""
    timestamp: float
    total_memory_mb: float
    used_memory_mb: float
    available_memory_mb: float
    percent_used: float
    process_memory_mb: float
    process_percent: float
    peak_memory_mb: float
    gc_counts: Tuple[int, int, int]  # (generation0, generation1, generation2)
    tracemalloc_current_mb: float
    tracemalloc_peak_mb: float
    num_objects: int
    object_types: Dict[str, int]

@dataclass
class MemoryAlert:
    """内存告警"""
    alert_id: str
    timestamp: float
    alert_type: str  # 'threshold', 'leak', 'fragmentation', 'pressure'
    severity: str  # 'low', 'medium', 'high', 'critical'
    current_usage_mb: float
    threshold_mb: float
    message: str
    recommendation: str

@dataclass
class MemoryLeakReport:
    """内存泄漏报告"""
    detection_time: float
    suspected_leaks: List[Dict[str, Any]]
    growth_rate_mb_per_hour: float
    leaked_objects: Dict[str, int]
    total_leaked_mb: float

@dataclass
class MemoryEfficiencyMetrics:
    """内存效率指标"""
    timestamp: float
    memory_efficiency_score: float
    memory_utilization_ratio: float
    gc_efficiency_score: float
    fragmentation_ratio: float
    object_lifetime_avg: float
    memory_pressure_index: float

class MemoryValidator:
    """内存验证器"""

    def __init__(
        self,
        memory_limit_gb: float = 8.0,
        warning_threshold: float = 0.7,
        critical_threshold: float = 0.85,
        monitoring_interval: float = 5.0,
        history_size: int = 1000
    ):
        self.memory_limit_bytes = memory_limit_gb * 1024 * 1024 * 1024
        self.memory_limit_mb = memory_limit_gb * 1024
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

        self.monitoring_interval = monitoring_interval
        self.history_size = history_size

        # 监控状态
        self.monitoring_active = False
        self.monitor_thread = None

        # 内存历史数据
        self.memory_snapshots = deque(maxlen=history_size)
        self.memory_alerts = deque(maxlen=100)

        # 内存泄漏检测
        self.baseline_snapshot = None
        self.leak_detection_enabled = True
        self.leak_reports = []

        # 统计信息
        self.peak_memory_usage_mb = 0
        self.total_gc_runs = 0
        self.memory_cleanup_count = 0

        # 内存优化器
        self.memory_optimizers = []

        # 对象引用跟踪
        self.object_registry = weakref.WeakSet()
        self.object_creation_times = {}

        # 线程安全
        self._lock = threading.Lock()

        logger.info(f"Memory Validator initialized - Limit: {memory_limit_gb}GB")

    def start_monitoring(self):
        """启动内存监控"""
        if self.monitoring_active:
            logger.warning("Memory monitoring already active")
            return

        self.monitoring_active = True

        # 启动tracemalloc
        if not tracemalloc.is_tracing():
            tracemalloc.start()

        # 建立基线
        self._establish_baseline()

        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("Memory monitoring started")

    def stop_monitoring(self):
        """停止内存监控"""
        if not self.monitoring_active:
            return

        self.monitoring_active = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)

        # 停止tracemalloc
        if tracemalloc.is_tracing():
            tracemalloc.stop()

        logger.info("Memory monitoring stopped")

    def validate_memory_usage(self) -> Dict[str, Any]:
        """验证内存使用"""
        current_snapshot = self._capture_memory_snapshot()

        validation_result = {
            'timestamp': current_snapshot.timestamp,
            'within_limits': current_snapshot.used_memory_mb <= self.memory_limit_mb,
            'current_usage_mb': current_snapshot.used_memory_mb,
            'limit_mb': self.memory_limit_mb,
            'usage_percent': current_snapshot.used_memory_mb / self.memory_limit_mb * 100,
            'status': self._get_memory_status(current_snapshot),
            'alerts': self._check_thresholds(current_snapshot),
            'recommendations': self._get_memory_recommendations(current_snapshot)
        }

        return validation_result

    def force_memory_cleanup(self) -> Dict[str, Any]:
        """强制内存清理"""
        cleanup_start = time.time()
        pre_cleanup_memory = self._get_current_memory_mb()

        cleanup_actions = []

        try:
            # 1. 强制垃圾回收
            pre_gc_memory = self._get_current_memory_mb()
            gc.collect()
            post_gc_memory = self._get_current_memory_mb()
            gc_freed = pre_gc_memory - post_gc_memory

            cleanup_actions.append({
                'action': 'garbage_collection',
                'memory_freed_mb': gc_freed,
                'success': True
            })

            self.total_gc_runs += 1

            # 2. 清理numpy缓存
            try:
                import numpy.core.arrayprint as ap
                if hasattr(ap, '_format_options'):
                    ap._format_options.clear()
            except:
                pass

            # 3. 清理pandas缓存
            try:
                pd.options.mode.chained_assignment = None
                import pandas._libs.lib as lib
                if hasattr(lib, '_period_index_cache'):
                    lib._period_index_cache.clear()
            except:
                pass

            # 4. 清理对象引用
            self._cleanup_object_references()

            post_cleanup_memory = self._get_current_memory_mb()
            total_freed = pre_cleanup_memory - post_cleanup_memory

            cleanup_time = time.time() - cleanup_start

            self.memory_cleanup_count += 1

            cleanup_result = {
                'timestamp': cleanup_start,
                'cleanup_duration_sec': cleanup_time,
                'pre_cleanup_memory_mb': pre_cleanup_memory,
                'post_cleanup_memory_mb': post_cleanup_memory,
                'total_memory_freed_mb': total_freed,
                'cleanup_actions': cleanup_actions,
                'success': True
            }

            logger.info(f"Memory cleanup completed: freed {total_freed:.2f}MB in {cleanup_time:.2f}s")

        except Exception as e:
            cleanup_result = {
                'timestamp': cleanup_start,
                'cleanup_duration_sec': time.time() - cleanup_start,
                'pre_cleanup_memory_mb': pre_cleanup_memory,
                'post_cleanup_memory_mb': self._get_current_memory_mb(),
                'total_memory_freed_mb': 0,
                'cleanup_actions': cleanup_actions,
                'success': False,
                'error': str(e)
            }
            logger.error(f"Memory cleanup failed: {e}")

        return cleanup_result

    def detect_memory_leaks(self) -> Optional[MemoryLeakReport]:
        """检测内存泄漏"""
        if not self.leak_detection_enabled or not self.baseline_snapshot:
            return None

        current_snapshot = self._capture_memory_snapshot()

        # 计算内存增长
        memory_growth = current_snapshot.used_memory_mb - self.baseline_snapshot.used_memory_mb
        time_elapsed = current_snapshot.timestamp - self.baseline_snapshot.timestamp

        if time_elapsed < 300:  # 至少5分钟才进行泄漏检测
            return None

        growth_rate_mb_per_hour = (memory_growth / time_elapsed) * 3600

        # 判断是否存在泄漏
        leak_threshold = 100  # 每小时100MB增长阈值
        if growth_rate_mb_per_hour < leak_threshold:
            return None

        # 分析对象增长
        suspected_leaks = []
        leaked_objects = defaultdict(int)

        for obj_type, current_count in current_snapshot.object_types.items():
            baseline_count = self.baseline_snapshot.object_types.get(obj_type, 0)
            growth = current_count - baseline_count

            if growth > 1000:  # 对象数量增长超过1000
                leaked_objects[obj_type] = growth
                suspected_leaks.append({
                    'object_type': obj_type,
                    'growth_count': growth,
                    'growth_rate_per_hour': (growth / time_elapsed) * 3600,
                    'current_count': current_count,
                    'baseline_count': baseline_count
                })

        if not suspected_leaks:
            return None

        leak_report = MemoryLeakReport(
            detection_time=current_snapshot.timestamp,
            suspected_leaks=suspected_leaks,
            growth_rate_mb_per_hour=growth_rate_mb_per_hour,
            leaked_objects=dict(leaked_objects),
            total_leaked_mb=memory_growth
        )

        self.leak_reports.append(leak_report)
        logger.warning(f"Memory leak detected: {growth_rate_mb_per_hour:.2f}MB/hour growth")

        return leak_report

    def register_object(self, obj, name: str = None):
        """注册对象用于跟踪"""
        self.object_registry.add(obj)
        if name:
            self.object_creation_times[name] = time.time()

    def calculate_memory_efficiency(self) -> MemoryEfficiencyMetrics:
        """计算内存效率指标"""
        if len(self.memory_snapshots) < 2:
            return MemoryEfficiencyMetrics(
                timestamp=time.time(),
                memory_efficiency_score=1.0,
                memory_utilization_ratio=0.5,
                gc_efficiency_score=1.0,
                fragmentation_ratio=0.1,
                object_lifetime_avg=60.0,
                memory_pressure_index=0.0
            )

        recent_snapshots = list(self.memory_snapshots)[-10:]
        current_snapshot = recent_snapshots[-1]

        # 计算内存利用率
        memory_utilization = current_snapshot.used_memory_mb / self.memory_limit_mb

        # 计算内存效率分数 (理想利用率在70-80%之间)
        if 0.7 <= memory_utilization <= 0.8:
            memory_efficiency_score = 1.0
        elif memory_utilization < 0.7:
            memory_efficiency_score = memory_utilization / 0.7
        else:
            memory_efficiency_score = max(0.0, 1.0 - (memory_utilization - 0.8) / 0.2)

        # 计算GC效率分数
        if len(recent_snapshots) >= 2:
            gc_efficiency = self._calculate_gc_efficiency(recent_snapshots)
        else:
            gc_efficiency = 1.0

        # 计算内存碎片率
        fragmentation_ratio = self._calculate_fragmentation_ratio(current_snapshot)

        # 计算内存压力指数
        memory_pressure_index = self._calculate_memory_pressure_index(current_snapshot)

        # 估算对象平均生命周期
        object_lifetime_avg = self._estimate_object_lifetime()

        return MemoryEfficiencyMetrics(
            timestamp=current_snapshot.timestamp,
            memory_efficiency_score=memory_efficiency_score,
            memory_utilization_ratio=memory_utilization,
            gc_efficiency_score=gc_efficiency,
            fragmentation_ratio=fragmentation_ratio,
            object_lifetime_avg=object_lifetime_avg,
            memory_pressure_index=memory_pressure_index
        )

    def _monitoring_loop(self):
        """监控循环"""
        while self.monitoring_active:
            try:
                # 捕获内存快照
                snapshot = self._capture_memory_snapshot()

                with self._lock:
                    self.memory_snapshots.append(snapshot)

                    # 更新峰值内存使用
                    self.peak_memory_usage_mb = max(self.peak_memory_usage_mb, snapshot.used_memory_mb)

                # 检查阈值告警
                alerts = self._check_thresholds(snapshot)
                for alert in alerts:
                    with self._lock:
                        self.memory_alerts.append(alert)

                # 检测内存泄漏
                if self.leak_detection_enabled:
                    leak_report = self.detect_memory_leaks()
                    if leak_report:
                        logger.warning(f"Memory leak detected: {leak_report.total_leaked_mb:.2f}MB leaked")

                # 自动清理检查
                if snapshot.used_memory_mb > self.memory_limit_mb * self.critical_threshold:
                    logger.warning("Critical memory usage detected, triggering cleanup...")
                    cleanup_result = self.force_memory_cleanup()

                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                time.sleep(self.monitoring_interval)

    def _capture_memory_snapshot(self) -> MemorySnapshot:
        """捕获内存快照"""
        # 系统内存信息
        memory = psutil.virtual_memory()

        # 进程内存信息
        process = psutil.Process()
        process_memory = process.memory_info()
        process_memory_mb = process_memory.rss / (1024 * 1024)
        process_percent = process.memory_percent()

        # GC统计
        gc_counts = gc.get_count()

        # tracemalloc统计
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc_current_mb = current / (1024 * 1024)
            tracemalloc_peak_mb = peak / (1024 * 1024)
        else:
            tracemalloc_current_mb = tracemalloc_peak_mb = 0

        # 对象类型统计
        object_types = {}
        try:
            import sys
            for obj_type in [list, dict, tuple, set, np.ndarray, pd.DataFrame]:
                object_types[obj_type.__name__] = len([obj for obj in gc.get_objects() if type(obj) is obj_type])
        except:
            pass

        # 总对象数
        num_objects = len(gc.get_objects())

        # 峰值内存使用
        peak_memory_mb = max(
            memory.used / (1024 * 1024),
            process_memory_mb
        )

        return MemorySnapshot(
            timestamp=time.time(),
            total_memory_mb=memory.total / (1024 * 1024),
            used_memory_mb=memory.used / (1024 * 1024),
            available_memory_mb=memory.available / (1024 * 1024),
            percent_used=memory.percent,
            process_memory_mb=process_memory_mb,
            process_percent=process_percent,
            peak_memory_mb=peak_memory_mb,
            gc_counts=gc_counts,
            tracemalloc_current_mb=tracemalloc_current_mb,
            tracemalloc_peak_mb=tracemalloc_peak_mb,
            num_objects=num_objects,
            object_types=object_types
        )

    def _establish_baseline(self):
        """建立内存使用基线"""
        self.baseline_snapshot = self._capture_memory_snapshot()
        logger.info(f"Memory baseline established: {self.baseline_snapshot.used_memory_mb:.2f}MB")

    def _check_thresholds(self, snapshot: MemorySnapshot) -> List[MemoryAlert]:
        """检查内存阈值告警"""
        alerts = []
        usage_ratio = snapshot.used_memory_mb / self.memory_limit_mb

        # 检查警告阈值
        if usage_ratio >= self.critical_threshold:
            alert = MemoryAlert(
                alert_id=f"critical_{int(snapshot.timestamp)}",
                timestamp=snapshot.timestamp,
                alert_type="threshold",
                severity="critical",
                current_usage_mb=snapshot.used_memory_mb,
                threshold_mb=self.memory_limit_mb * self.critical_threshold,
                message=f"Critical memory usage: {snapshot.used_memory_mb:.2f}MB ({usage_ratio:.1%})",
                recommendation="Immediate memory cleanup required"
            )
            alerts.append(alert)

        elif usage_ratio >= self.warning_threshold:
            alert = MemoryAlert(
                alert_id=f"warning_{int(snapshot.timestamp)}",
                timestamp=snapshot.timestamp,
                alert_type="threshold",
                severity="medium",
                current_usage_mb=snapshot.used_memory_mb,
                threshold_mb=self.memory_limit_mb * self.warning_threshold,
                message=f"High memory usage: {snapshot.used_memory_mb:.2f}MB ({usage_ratio:.1%})",
                recommendation="Monitor closely and consider cleanup"
            )
            alerts.append(alert)

        return alerts

    def _get_memory_status(self, snapshot: MemorySnapshot) -> str:
        """获取内存状态"""
        usage_ratio = snapshot.used_memory_mb / self.memory_limit_mb

        if usage_ratio < 0.5:
            return "healthy"
        elif usage_ratio < self.warning_threshold:
            return "normal"
        elif usage_ratio < self.critical_threshold:
            return "warning"
        else:
            return "critical"

    def _get_memory_recommendations(self, snapshot: MemorySnapshot) -> List[str]:
        """获取内存优化建议"""
        recommendations = []
        usage_ratio = snapshot.used_memory_mb / self.memory_limit_mb

        if usage_ratio > 0.8:
            recommendations.append("Immediate memory cleanup is required")
            recommendations.append("Consider reducing data processing batch sizes")
            recommendations.append("Check for memory leaks in the application")

        elif usage_ratio > 0.6:
            recommendations.append("Monitor memory usage closely")
            recommendations.append("Consider periodic garbage collection")
            recommendations.append("Optimize data structures for memory efficiency")

        if snapshot.process_memory_mb > snapshot.used_memory_mb * 0.5:
            recommendations.append("Process is using significant portion of system memory")

        if snapshot.num_objects > 1000000:
            recommendations.append("High object count detected, consider object pooling")

        return recommendations

    def _cleanup_object_references(self):
        """清理对象引用"""
        # 清理弱引用集合
        if hasattr(self, 'object_registry'):
            self.object_registry.clear()

        # 清理对象创建时间记录
        if hasattr(self, 'object_creation_times'):
            self.object_creation_times.clear()

    def _calculate_gc_efficiency(self, snapshots: List[MemorySnapshot]) -> float:
        """计算垃圾回收效率"""
        if len(snapshots) < 2:
            return 1.0

        # 比较GC前后的内存变化
        gc_efficiency_score = 1.0  # 简化实现

        return gc_efficiency_score

    def _calculate_fragmentation_ratio(self, snapshot: MemorySnapshot) -> float:
        """计算内存碎片率"""
        # 简化的碎片率计算
        if snapshot.tracemalloc_current_mb > 0 and snapshot.tracemalloc_peak_mb > 0:
            fragmentation_ratio = 1.0 - (snapshot.tracemalloc_current_mb / snapshot.tracemalloc_peak_mb)
        else:
            fragmentation_ratio = 0.1  # 默认值

        return max(0.0, min(1.0, fragmentation_ratio))

    def _calculate_memory_pressure_index(self, snapshot: MemorySnapshot) -> float:
        """计算内存压力指数"""
        usage_ratio = snapshot.used_memory_mb / self.memory_limit_mb

        # 综合考虑使用率、GC压力等因素
        memory_pressure = usage_ratio

        # 考虑GC压力
        total_gc_objects = sum(snapshot.gc_counts)
        if total_gc_objects > 100000:
            memory_pressure += 0.1

        return min(1.0, memory_pressure)

    def _estimate_object_lifetime(self) -> float:
        """估算对象平均生命周期"""
        # 简化实现
        return 60.0  # 60秒

    def _get_current_memory_mb(self) -> float:
        """获取当前内存使用量（MB）"""
        memory = psutil.virtual_memory()
        return memory.used / (1024 * 1024)

    def get_memory_statistics(self) -> Dict[str, Any]:
        """获取内存统计信息"""
        with self._lock:
            if not self.memory_snapshots:
                return {}

            recent_snapshots = list(self.memory_snapshots)[-10:]

            return {
                'current_memory_mb': recent_snapshots[-1].used_memory_mb,
                'peak_memory_mb': self.peak_memory_usage_mb,
                'memory_limit_mb': self.memory_limit_mb,
                'usage_percent': (recent_snapshots[-1].used_memory_mb / self.memory_limit_mb) * 100,
                'total_gc_runs': self.total_gc_runs,
                'memory_cleanup_count': self.memory_cleanup_count,
                'total_alerts': len(self.memory_alerts),
                'leak_reports_count': len(self.leak_reports),
                'monitoring_active': self.monitoring_active,
                'memory_efficiency': asdict(self.calculate_memory_efficiency())
            }

    def export_memory_data(self, filepath: str, time_range_hours: int = 24):
        """导出内存数据"""
        try:
            cutoff_time = time.time() - (time_range_hours * 3600)

            recent_snapshots = [
                asdict(s) for s in self.memory_snapshots
                if s.timestamp >= cutoff_time
            ]

            data = {
                'export_timestamp': time.time(),
                'time_range_hours': time_range_hours,
                'memory_limit_mb': self.memory_limit_mb,
                'snapshots': recent_snapshots,
                'alerts': [asdict(a) for a in list(self.memory_alerts)],
                'leak_reports': [asdict(lr) for lr in self.leak_reports],
                'statistics': self.get_memory_statistics()
            }

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"Memory data exported to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export memory data: {e}")

class MemoryOptimizer:
    """内存优化器"""

    def __init__(self, validator: MemoryValidator):
        self.validator = validator
        self.optimization_strategies = []

    def optimize_memory_usage(self) -> Dict[str, Any]:
        """优化内存使用"""
        optimization_results = {
            'strategies_applied': [],
            'memory_freed_mb': 0,
            'optimization_score_before': 0,
            'optimization_score_after': 0,
            'timestamp': time.time()
        }

        try:
            # 获取优化前的效率分数
            efficiency_before = self.validator.calculate_memory_efficiency()
            optimization_results['optimization_score_before'] = efficiency_before.memory_efficiency_score

            # 应用优化策略
            for strategy in self.optimization_strategies:
                strategy_result = strategy()
                if strategy_result.get('success', False):
                    optimization_results['strategies_applied'].append(strategy.__name__)
                    optimization_results['memory_freed_mb'] += strategy_result.get('memory_freed_mb', 0)

            # 获取优化后的效率分数
            efficiency_after = self.validator.calculate_memory_efficiency()
            optimization_results['optimization_score_after'] = efficiency_after.memory_efficiency_score

            logger.info(f"Memory optimization completed: freed {optimization_results['memory_freed_mb']:.2f}MB")

        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")

        return optimization_results

    def register_optimization_strategy(self, strategy: Callable):
        """注册优化策略"""
        self.optimization_strategies.append(strategy)

# 全局内存验证器实例
_global_memory_validator = None
_global_memory_optimizer = None

def get_memory_validator() -> MemoryValidator:
    """获取全局内存验证器实例"""
    global _global_memory_validator
    if _global_memory_validator is None:
        _global_memory_validator = MemoryValidator()
        _global_memory_validator.start_monitoring()
    return _global_memory_validator

def get_memory_optimizer() -> MemoryOptimizer:
    """获取全局内存优化器实例"""
    global _global_memory_optimizer
    if _global_memory_optimizer is None:
        validator = get_memory_validator()
        _global_memory_optimizer = MemoryOptimizer(validator)
    return _global_memory_optimizer

def validate_memory_limit(limit_gb: float = 8.0) -> Dict[str, Any]:
    """验证内存限制（简化接口）"""
    validator = get_memory_validator()
    if validator.memory_limit_gb != limit_gb:
        validator.memory_limit_gb = limit_gb
        validator.memory_limit_mb = limit_gb * 1024
        validator.memory_limit_bytes = limit_gb * 1024 * 1024 * 1024

    return validator.validate_memory_usage()

def force_cleanup_memory() -> Dict[str, Any]:
    """强制内存清理（简化接口）"""
    validator = get_memory_validator()
    return validator.force_memory_cleanup()
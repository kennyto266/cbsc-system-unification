#!/usr/bin/env python3
"""
性能监控和报告系统
Performance monitoring and reporting system
"""

import time
import psutil
import threading
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    category: str = "general"

@dataclass
class SystemResource:
    """系统资源指标"""
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    disk_usage_percent: float
    timestamp: datetime

class PerformanceMonitor:
    """
    性能监控器

    提供实时的性能监控和报告功能
    """

    def __init__(self, monitoring_interval: float = 1.0):
        self.monitoring_interval = monitoring_interval
        self.metrics: List[PerformanceMetric] = []
        self.system_resources: List[SystemResource] = []
        self.operation_times: Dict[str, List[float]] = {}
        self.cache_stats: Dict[str, Any] = {}
        self.parallel_stats: Dict[str, Any] = {}
        self.gpu_stats: Dict[str, Any] = {}

        # 监控线程
        self.monitoring_active = False
        self.monitor_thread = None

        # 性能基准
        self.baseline_metrics: Dict[str, float] = {}

        logger.info("Performance monitor initialized")

    def start_monitoring(self):
        """开始性能监控"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("Performance monitoring stopped")

    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring_active:
            try:
                # 收集系统资源信息
                self._collect_system_resources()

                # 收集特定性能指标
                self._collect_performance_metrics()

                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)

    def _collect_system_resources(self):
        """收集系统资源信息"""
        try:
            # CPU和内存
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()

            # 磁盘使用
            disk = psutil.disk_usage('/')

            resource = SystemResource(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_gb=memory.used / 1e9,
                memory_available_gb=memory.available / 1e9,
                disk_usage_percent=disk.percent,
                timestamp=datetime.now()
            )

            self.system_resources.append(resource)

            # 保持最近1000条记录
            if len(self.system_resources) > 1000:
                self.system_resources = self.system_resources[-1000:]

        except Exception as e:
            logger.error(f"Error collecting system resources: {e}")

    def _collect_performance_metrics(self):
        """收集性能指标"""
        try:
            # 收集缓存统计
            self._collect_cache_stats()

            # 收集并行计算统计
            self._collect_parallel_stats()

            # 收集GPU统计
            self._collect_gpu_stats()

        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")

    def _collect_cache_stats(self):
        """收集缓存统计"""
        try:
            from .high_performance_cache import global_cache
            cache_stats = global_cache.get_comprehensive_stats()

            self.cache_stats = {
                'timestamp': datetime.now().isoformat(),
                'overall_hit_rate': cache_stats['overall_stats']['hit_rate'],
                'l1_cache_size': cache_stats['layer_stats']['l1_cache']['size'],
                'l2_cache_size': cache_stats['layer_stats']['l2_cache']['size'],
                'total_requests': cache_stats['overall_stats']['total_requests']
            }

        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Error collecting cache stats: {e}")

    def _collect_parallel_stats(self):
        """收集并行计算统计"""
        try:
            from .parallel_optimizer import global_parallel_optimizer
            parallel_stats = global_parallel_optimizer.get_performance_stats()

            self.parallel_stats = {
                'timestamp': datetime.now().isoformat(),
                'optimal_workers': parallel_stats['worker_configuration']['optimal_workers'],
                'success_rate': parallel_stats['task_statistics']['success_rate'],
                'tasks_per_second': parallel_stats['task_statistics']['tasks_per_second']
            }

        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Error collecting parallel stats: {e}")

    def _collect_gpu_stats(self):
        """收集GPU统计"""
        try:
            from .gpu_manager import get_gpu_manager
            gpu_manager = get_gpu_manager()
            gpu_stats = gpu_manager.get_backend_info()

            self.gpu_stats = {
                'timestamp': datetime.now().isoformat(),
                'backend_type': gpu_stats.get('backend_type', 'Unknown'),
                'gpu_available': gpu_stats.get('gpu_environment', {}).get('available', False)
            }

        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Error collecting GPU stats: {e}")

    def record_operation_time(self, operation_name: str, execution_time: float):
        """记录操作时间"""
        if operation_name not in self.operation_times:
            self.operation_times[operation_name] = []

        self.operation_times[operation_name].append(execution_time)

        # 保持最近100条记录
        if len(self.operation_times[operation_name]) > 100:
            self.operation_times[operation_name] = self.operation_times[operation_name][-100:]

    def record_metric(self, name: str, value: float, unit: str = "", category: str = "general"):
        """记录性能指标"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            category=category
        )

        self.metrics.append(metric)

        # 保持最近1000条记录
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]

    def set_baseline(self, operation_name: str, baseline_time: float):
        """设置性能基准"""
        self.baseline_metrics[operation_name] = baseline_time
        logger.info(f"Baseline set for {operation_name}: {baseline_time:.3f}s")

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能总结"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'monitoring_active': self.monitoring_active,
            'operation_performance': {},
            'system_resources': {},
            'cache_performance': self.cache_stats,
            'parallel_performance': self.parallel_stats,
            'gpu_performance': self.gpu_stats
        }

        # 操作性能统计
        for operation, times in self.operation_times.items():
            if times:
                baseline = self.baseline_metrics.get(operation)
                avg_time = sum(times) / len(times)
                improvement = None

                if baseline:
                    improvement = ((baseline - avg_time) / baseline) * 100

                summary['operation_performance'][operation] = {
                    'total_executions': len(times),
                    'average_time': avg_time,
                    'min_time': min(times),
                    'max_time': max(times),
                    'baseline_time': baseline,
                    'improvement_percent': improvement,
                    'last_execution': times[-1]
                }

        # 系统资源统计
        if self.system_resources:
            recent_resources = self.system_resources[-10:]  # 最近10条记录

            avg_cpu = sum(r.cpu_percent for r in recent_resources) / len(recent_resources)
            avg_memory = sum(r.memory_percent for r in recent_resources) / len(recent_resources)

            summary['system_resources'] = {
                'average_cpu_percent': avg_cpu,
                'average_memory_percent': avg_memory,
                'peak_memory_gb': max(r.memory_used_gb for r in recent_resources),
                'current_cpu': recent_resources[-1].cpu_percent,
                'current_memory': recent_resources[-1].memory_percent
            }

        return summary

    def generate_performance_report(self) -> str:
        """生成性能报告"""
        summary = self.get_performance_summary()

        report_lines = [
            "=" * 80,
            "性能优化报告",
            "Performance Optimization Report",
            "=" * 80,
            f"报告时间: {summary['timestamp']}",
            f"监控状态: {'活跃' if summary['monitoring_active'] else '停止'}",
            "",
            "系统资源使用情况",
            "-" * 40,
        ]

        if summary['system_resources']:
            resources = summary['system_resources']
            report_lines.extend([
                f"平均CPU使用率: {resources['average_cpu_percent']:.1f}%",
                f"平均内存使用率: {resources['average_memory_percent']:.1f}%",
                f"峰值内存使用: {resources['peak_memory_gb']:.2f} GB",
                f"当前CPU使用率: {resources['current_cpu']:.1f}%",
                f"当前内存使用率: {resources['current_memory']:.1f}%",
            ])

        report_lines.extend([
            "",
            "操作性能分析",
            "-" * 40,
        ])

        for operation, stats in summary['operation_performance'].items():
            report_lines.append(f"\n操作: {operation}")
            report_lines.append(f"  执行次数: {stats['total_executions']}")
            report_lines.append(f"  平均时间: {stats['average_time']:.3f}s")
            report_lines.append(f"  最短时间: {stats['min_time']:.3f}s")
            report_lines.append(f"  最长时间: {stats['max_time']:.3f}s")

            if stats['baseline_time']:
                report_lines.append(f"  基准时间: {stats['baseline_time']:.3f}s")
                if stats['improvement_percent'] is not None:
                    if stats['improvement_percent'] > 0:
                        report_lines.append(f"  性能提升: {stats['improvement_percent']:.1f}% ✅")
                    else:
                        report_lines.append(f"  性能下降: {abs(stats['improvement_percent']):.1f}% ❌")

        # 缓存性能
        if summary['cache_performance']:
            cache = summary['cache_performance']
            report_lines.extend([
                "",
                "缓存性能",
                "-" * 40,
                f"整体命中率: {cache.get('overall_hit_rate', 0):.1%}",
                f"L1缓存大小: {cache.get('l1_cache_size', 0)} 项",
                f"L2缓存大小: {cache.get('l2_cache_size', 0)} 项",
                f"总请求次数: {cache.get('total_requests', 0)}",
            ])

        # 并行计算性能
        if summary['parallel_performance']:
            parallel = summary['parallel_performance']
            report_lines.extend([
                "",
                "并行计算性能",
                "-" * 40,
                f"最优工作线程数: {parallel.get('optimal_workers', 'Unknown')}",
                f"任务成功率: {parallel.get('success_rate', 0):.1%}",
                f"任务处理速度: {parallel.get('tasks_per_second', 0):.1f} 任务/秒",
            ])

        # GPU性能
        if summary['gpu_performance']:
            gpu = summary['gpu_performance']
            report_lines.extend([
                "",
                "GPU性能",
                "-" * 40,
                f"后端类型: {gpu.get('backend_type', 'Unknown')}",
                f"GPU可用: {'是' if gpu.get('gpu_available', False) else '否'}",
            ])

        report_lines.extend([
            "",
            "=" * 80,
        ])

        return "\n".join(report_lines)

    def export_metrics(self, filepath: str):
        """导出性能指标到文件"""
        try:
            data = {
                'summary': self.get_performance_summary(),
                'metrics': [asdict(m) for m in self.metrics],
                'system_resources': [asdict(r) for r in self.system_resources],
                'operation_times': self.operation_times,
                'baseline_metrics': self.baseline_metrics
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)

            logger.info(f"Performance metrics exported to {filepath}")

        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")

    def compare_with_baseline(self, operation_name: str, current_time: float) -> Dict[str, Any]:
        """与基准时间比较"""
        baseline = self.baseline_metrics.get(operation_name)

        if not baseline:
            return {
                'operation': operation_name,
                'baseline_available': False,
                'message': 'No baseline available for comparison'
            }

        improvement = ((baseline - current_time) / baseline) * 100
        speedup = baseline / current_time

        return {
            'operation': operation_name,
            'baseline_time': baseline,
            'current_time': current_time,
            'improvement_percent': improvement,
            'speedup_factor': speedup,
            'faster': improvement > 0,
            'baseline_available': True
        }

# 全局性能监控器
_global_performance_monitor = None

def get_performance_monitor(monitoring_interval: float = 1.0) -> PerformanceMonitor:
    """获取全局性能监控器"""
    global _global_performance_monitor
    if _global_performance_monitor is None:
        _global_performance_monitor = PerformanceMonitor(monitoring_interval)
    return _global_performance_monitor

def start_global_monitoring():
    """启动全局监控"""
    monitor = get_performance_monitor()
    monitor.start_monitoring()

def stop_global_monitoring():
    """停止全局监控"""
    monitor = get_performance_monitor()
    monitor.stop_monitoring()

def record_operation(operation_name: str, execution_time: float):
    """记录操作时间到全局监控器"""
    monitor = get_performance_monitor()
    monitor.record_operation_time(operation_name, execution_time)
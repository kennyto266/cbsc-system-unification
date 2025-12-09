#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU性能監控和內存管理系統
"""

import psutil
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

@dataclass
class GPUMetrics:
    """GPU性能指標"""
    timestamp: datetime
    gpu_utilization: float  # GPU利用率 (%)
    memory_used: float      # 已使用內存 (MB)
    memory_total: float     # 總內存 (MB)
    temperature: float      # GPU溫度 (°C)
    power_usage: float      # 功耗 (W)
    compute_capability: float  # 計算性能指標

@dataclass
class CPUMetrics:
    """CPU性能指標"""
    timestamp: datetime
    cpu_percent: float      # CPU利用率 (%)
    memory_percent: float   # 內存利用率 (%)
    memory_used: float      # 已使用內存 (MB)
    memory_total: float     # 總內存 (MB)
    cpu_count: int          # CPU核心數

@dataclass
class OptimizationMetrics:
    """優化任務指標"""
    task_id: str
    strategy_type: str
    parameters_tested: int
    execution_time: float
    strategies_per_second: float
    memory_peak: float
    gpu_utilized: bool
    success_rate: float

class PerformanceMonitor:
    """性能監控器"""

    def __init__(self, monitoring_interval: float = 1.0):
        self.monitoring_interval = monitoring_interval
        self.is_monitoring = False
        self.monitoring_thread = None

        # 指標存儲
        self.gpu_metrics_history: List[GPUMetrics] = []
        self.cpu_metrics_history: List[CPUMetrics] = []
        self.optimization_history: List[OptimizationMetrics] = []

        # 回調函數
        self.callbacks: Dict[str, List[Callable]] = {
            'warning': [],
            'critical': [],
            'completion': []
        }

        # 閾值設定
        self.thresholds = {
            'gpu_utilization_warning': 90.0,
            'gpu_utilization_critical': 95.0,
            'memory_usage_warning': 80.0,
            'memory_usage_critical': 90.0,
            'temperature_warning': 80.0,
            'temperature_critical': 85.0
        }

    def start_monitoring(self):
        """開始監控"""
        if self.is_monitoring:
            logger.warning("Monitoring already started")
            return

        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """停止監控"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)
        logger.info("Performance monitoring stopped")

    def _monitoring_loop(self):
        """監控循環"""
        while self.is_monitoring:
            try:
                # 收集GPU指標
                gpu_metrics = self._collect_gpu_metrics()
                if gpu_metrics:
                    self.gpu_metrics_history.append(gpu_metrics)
                    self._check_gpu_thresholds(gpu_metrics)

                # 收集CPU指標
                cpu_metrics = self._collect_cpu_metrics()
                if cpu_metrics:
                    self.cpu_metrics_history.append(cpu_metrics)
                    self._check_cpu_thresholds(cpu_metrics)

                # 保持歷史記錄在合理範圍內（最多1000個記錄）
                if len(self.gpu_metrics_history) > 1000:
                    self.gpu_metrics_history = self.gpu_metrics_history[-1000:]
                if len(self.cpu_metrics_history) > 1000:
                    self.cpu_metrics_history = self.cpu_metrics_history[-1000:]

                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(self.monitoring_interval)

    def _collect_gpu_metrics(self) -> Optional[GPUMetrics]:
        """收集GPU指標"""
        try:
            import cupy as cp

            # 獲取GPU信息
            mempool = cp.get_default_memory_pool()
            device = cp.cuda.Device()

            # 計算內存使用
            memory_used_bytes = mempool.used_bytes()
            memory_total_bytes = mempool.total_bytes()

            # 轉換為MB
            memory_used_mb = memory_used_bytes / (1024 * 1024)
            memory_total_mb = memory_total_bytes / (1024 * 1024)

            # 計算利用率（簡化版本）
            gpu_utilization = 0.0
            if memory_total_mb > 0:
                gpu_utilization = (memory_used_mb / memory_total_mb) * 100

            metrics = GPUMetrics(
                timestamp=datetime.now(),
                gpu_utilization=gpu_utilization,
                memory_used=memory_used_mb,
                memory_total=memory_total_mb,
                temperature=0.0,  # 需要nvidia-ml-py來獲取溫度
                power_usage=0.0,  # 需要nvidia-ml-py來獲取功耗
                compute_capability=1.0  # 簡化指標
            )

            return metrics

        except ImportError:
            # CuPy不可用，返回空指標
            return None
        except Exception as e:
            logger.error(f"Failed to collect GPU metrics: {e}")
            return None

    def _collect_cpu_metrics(self) -> CPUMetrics:
        """收集CPU指標"""
        try:
            # CPU利用率
            cpu_percent = psutil.cpu_percent(interval=None)

            # 內存信息
            memory = psutil.virtual_memory()
            memory_used_mb = memory.used / (1024 * 1024)
            memory_total_mb = memory.total / (1024 * 1024)

            metrics = CPUMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used=memory_used_mb,
                memory_total=memory_total_mb,
                cpu_count=psutil.cpu_count()
            )

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect CPU metrics: {e}")
            # 返回默認值
            return CPUMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used=0.0,
                memory_total=0.0,
                cpu_count=0
            )

    def _check_gpu_thresholds(self, metrics: GPUMetrics):
        """檢查GPU閾值"""
        warnings = []
        criticals = []

        # GPU利用率檢查
        if metrics.gpu_utilization >= self.thresholds['gpu_utilization_critical']:
            criticals.append(f"GPU utilization critical: {metrics.gpu_utilization:.1f}%")
        elif metrics.gpu_utilization >= self.thresholds['gpu_utilization_warning']:
            warnings.append(f"GPU utilization high: {metrics.gpu_utilization:.1f}%")

        # 內存使用檢查
        if metrics.memory_total > 0:
            memory_usage_percent = (metrics.memory_used / metrics.memory_total) * 100
            if memory_usage_percent >= self.thresholds['memory_usage_critical']:
                criticals.append(f"GPU memory usage critical: {memory_usage_percent:.1f}%")
            elif memory_usage_percent >= self.thresholds['memory_usage_warning']:
                warnings.append(f"GPU memory usage high: {memory_usage_percent:.1f}%")

        # 觸發回調
        for critical in criticals:
            self._trigger_callback('critical', critical)

        for warning in warnings:
            self._trigger_callback('warning', warning)

    def _check_cpu_thresholds(self, metrics: CPUMetrics):
        """檢查CPU閾值"""
        # CPU利用率檢查
        if metrics.cpu_percent >= self.thresholds['gpu_utilization_critical']:
            self._trigger_callback('critical', f"CPU utilization critical: {metrics.cpu_percent:.1f}%")
        elif metrics.cpu_percent >= self.thresholds['gpu_utilization_warning']:
            self._trigger_callback('warning', f"CPU utilization high: {metrics.cpu_percent:.1f}%")

        # 內存使用檢查
        if metrics.memory_percent >= self.thresholds['memory_usage_critical']:
            self._trigger_callback('critical', f"CPU memory usage critical: {metrics.memory_percent:.1f}%")
        elif metrics.memory_percent >= self.thresholds['memory_usage_warning']:
            self._trigger_callback('warning', f"CPU memory usage high: {metrics.memory_percent:.1f}%")

    def record_optimization_metrics(self, metrics: OptimizationMetrics):
        """記錄優化任務指標"""
        self.optimization_history.append(metrics)

        # 保持歷史記錄在合理範圍內
        if len(self.optimization_history) > 100:
            self.optimization_history = self.optimization_history[-100:]

        # 觸發完成回調
        self._trigger_callback('completion', f"Optimization completed: {metrics.task_id}")

    def add_callback(self, event_type: str, callback: Callable[[str], None]):
        """添加回調函數"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)

    def _trigger_callback(self, event_type: str, message: str):
        """觸發回調函數"""
        for callback in self.callbacks.get(event_type, []):
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def get_performance_summary(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """獲取性能摘要"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)

        # 過濾指標
        recent_gpu = [m for m in self.gpu_metrics_history if m.timestamp >= cutoff_time]
        recent_cpu = [m for m in self.cpu_metrics_history if m.timestamp >= cutoff_time]

        summary = {
            'duration_minutes': duration_minutes,
            'gpu_samples': len(recent_gpu),
            'cpu_samples': len(recent_cpu),
            'optimization_tasks': len(self.optimization_history)
        }

        # GPU統計
        if recent_gpu:
            gpu_utils = [m.gpu_utilization for m in recent_gpu]
            memory_utils = [m.memory_used / m.memory_total * 100 if m.memory_total > 0 else 0 for m in recent_gpu]

            summary.update({
                'gpu_utilization': {
                    'mean': sum(gpu_utils) / len(gpu_utils),
                    'max': max(gpu_utils),
                    'min': min(gpu_utils)
                },
                'gpu_memory_usage': {
                    'mean': sum(memory_utils) / len(memory_utils),
                    'max': max(memory_utils),
                    'min': min(memory_utils)
                }
            })

        # CPU統計
        if recent_cpu:
            cpu_utils = [m.cpu_percent for m in recent_cpu]
            memory_utils = [m.memory_percent for m in recent_cpu]

            summary.update({
                'cpu_utilization': {
                    'mean': sum(cpu_utils) / len(cpu_utils),
                    'max': max(cpu_utils),
                    'min': min(cpu_utils)
                },
                'cpu_memory_usage': {
                    'mean': sum(memory_utils) / len(memory_utils),
                    'max': max(memory_utils),
                    'min': min(memory_utils)
                }
            })

        return summary

    def export_metrics(self, filepath: str):
        """導出指標到文件"""
        try:
            data = {
                'export_time': datetime.now().isoformat(),
                'gpu_metrics': [
                    {
                        'timestamp': m.timestamp.isoformat(),
                        'gpu_utilization': m.gpu_utilization,
                        'memory_used': m.memory_used,
                        'memory_total': m.memory_total,
                        'temperature': m.temperature,
                        'power_usage': m.power_usage
                    } for m in self.gpu_metrics_history
                ],
                'cpu_metrics': [
                    {
                        'timestamp': m.timestamp.isoformat(),
                        'cpu_percent': m.cpu_percent,
                        'memory_percent': m.memory_percent,
                        'memory_used': m.memory_used,
                        'memory_total': m.memory_total,
                        'cpu_count': m.cpu_count
                    } for m in self.cpu_metrics_history
                ],
                'optimization_metrics': [
                    {
                        'task_id': m.task_id,
                        'strategy_type': m.strategy_type,
                        'parameters_tested': m.parameters_tested,
                        'execution_time': m.execution_time,
                        'strategies_per_second': m.strategies_per_second,
                        'memory_peak': m.memory_peak,
                        'gpu_utilized': m.gpu_utilized,
                        'success_rate': m.success_rate
                    } for m in self.optimization_history
                ]
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Metrics exported to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")

class MemoryManager:
    """內存管理器"""

    def __init__(self):
        self.allocations: Dict[str, Dict[str, Any]] = {}
        self.total_allocated = 0.0
        self.cleanup_callbacks: List[Callable] = []

    def allocate_gpu_memory(self, allocation_id: str, size_mb: float, purpose: str = ""):
        """分配GPU內存"""
        try:
            import cupy as cp

            # 創建一個指定大小的數組
            array = cp.zeros(int(size_mb * 1024 * 1024 // 4), dtype=cp.float32)

            self.allocations[allocation_id] = {
                'array': array,
                'size_mb': size_mb,
                'purpose': purpose,
                'created_at': datetime.now(),
                'type': 'gpu'
            }

            self.total_allocated += size_mb
            logger.info(f"GPU memory allocated: {size_mb:.2f}MB for {purpose} (ID: {allocation_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to allocate GPU memory: {e}")
            return False

    def free_allocation(self, allocation_id: str):
        """釋放指定分配"""
        if allocation_id in self.allocations:
            allocation = self.allocations[allocation_id]

            try:
                if allocation['type'] == 'gpu':
                    import cupy as cp
                    del allocation['array']
                    cp.get_default_memory_pool().free_all_blocks()

                self.total_allocated -= allocation['size_mb']
                del self.allocations[allocation_id]

                logger.info(f"Memory freed: {allocation_id} ({allocation['size_mb']:.2f}MB)")
                return True

            except Exception as e:
                logger.error(f"Failed to free allocation {allocation_id}: {e}")
                return False

        return False

    def free_all(self):
        """釋放所有分配"""
        allocation_ids = list(self.allocations.keys())
        for allocation_id in allocation_ids:
            self.free_allocation(allocation_id)

        # 執行清理回調
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Cleanup callback error: {e}")

    def get_memory_usage(self) -> Dict[str, Any]:
        """獲取內存使用情況"""
        gpu_usage = self._get_gpu_memory_info()
        cpu_usage = self._get_cpu_memory_info()

        return {
            'gpu_memory': gpu_usage,
            'cpu_memory': cpu_usage,
            'managed_allocations': {
                'count': len(self.allocations),
                'total_mb': self.total_allocated,
                'allocations': {
                    alloc_id: {
                        'size_mb': alloc['size_mb'],
                        'purpose': alloc['purpose'],
                        'created_at': alloc['created_at'].isoformat()
                    } for alloc_id, alloc in self.allocations.items()
                }
            }
        }

    def _get_gpu_memory_info(self) -> Dict[str, Any]:
        """獲取GPU內存信息"""
        try:
            import cupy as cp
            mempool = cp.get_default_memory_pool()

            return {
                'used_mb': mempool.used_bytes() / (1024 * 1024),
                'total_mb': mempool.total_bytes() / (1024 * 1024),
                'free_mb': (mempool.total_bytes() - mempool.used_bytes()) / (1024 * 1024),
                'utilization_percent': (mempool.used_bytes() / mempool.total_bytes() * 100) if mempool.total_bytes() > 0 else 0
            }

        except ImportError:
            return {'available': False}
        except Exception as e:
            logger.error(f"Failed to get GPU memory info: {e}")
            return {'error': str(e)}

    def _get_cpu_memory_info(self) -> Dict[str, Any]:
        """獲取CPU內存信息"""
        try:
            memory = psutil.virtual_memory()
            return {
                'used_mb': memory.used / (1024 * 1024),
                'total_mb': memory.total / (1024 * 1024),
                'free_mb': memory.available / (1024 * 1024),
                'utilization_percent': memory.percent
            }

        except Exception as e:
            logger.error(f"Failed to get CPU memory info: {e}")
            return {'error': str(e)}

    def add_cleanup_callback(self, callback: Callable):
        """添加清理回調"""
        self.cleanup_callbacks.append(callback)

# 全局實例
_performance_monitor = None
_memory_manager = None

def get_performance_monitor() -> PerformanceMonitor:
    """獲取性能監控器實例"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

def get_memory_manager() -> MemoryManager:
    """獲取內存管理器實例"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
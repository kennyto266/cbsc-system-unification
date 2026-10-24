#!/usr/bin/env python3
"""
Phase 3: 动态分块大小优化算法
Dynamic Chunk Size Optimization Algorithm for GPU-to-CPU Migration

This module implements intelligent dynamic chunking algorithms that adapt to
system resources, data characteristics, and performance requirements for
optimal CPU parallel processing efficiency.

Key Features:
- Real-time performance-based chunk size adaptation
- Memory-aware dynamic allocation
- Multi-objective optimization (speed, memory, efficiency)
- System load responsive chunking
- Historical performance learning
"""

import logging
import time
import threading
import psutil
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import deque
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import json
import datetime
import math

logger = logging.getLogger(__name__)

@dataclass
class ChunkPerformanceMetrics:
    """分块性能指标"""
    chunk_size: int
    processing_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    throughput_items_per_sec: float
    efficiency_score: float
    timestamp: float
    data_characteristics: Dict[str, Any]

@dataclass
class OptimizationTarget:
    """优化目标配置"""
    primary_objective: str  # 'speed', 'memory', 'efficiency', 'balanced'
    max_memory_mb: float
    target_cpu_utilization: float
    min_throughput: float
    priority_weight: Dict[str, float]  # 权重分配

class DynamicChunkOptimizer:
    """动态分块大小优化器 - 智能自适应系统"""

    def __init__(
        self,
        initial_chunk_size: int = 1000,
        min_chunk_size: int = 100,
        max_chunk_size: int = 10000,
        optimization_target: OptimizationTarget = None,
        learning_window: int = 50,
        adaptation_interval: float = 5.0
    ):
        self.initial_chunk_size = initial_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

        # 默认优化目标
        if optimization_target is None:
            self.optimization_target = OptimizationTarget(
                primary_objective='balanced',
                max_memory_mb=6144,  # 6GB限制
                target_cpu_utilization=85.0,
                min_throughput=1000.0,
                priority_weight={
                    'speed': 0.4,
                    'memory': 0.3,
                    'efficiency': 0.3
                }
            )
        else:
            self.optimization_target = optimization_target

        self.learning_window = learning_window
        self.adaptation_interval = adaptation_interval

        # 性能历史数据
        self.performance_history = deque(maxlen=learning_window * 2)
        self.chunk_size_history = deque(maxlen=learning_window)

        # 当前状态
        self.current_chunk_size = initial_chunk_size
        self.last_adaptation_time = time.time()
        self.performance_stability_score = 0.0

        # 系统监控
        self.monitoring_active = False
        self.monitor_thread = None
        self.system_metrics_history = deque(maxlen=100)

        # 优化统计
        self.adaptation_count = 0
        self.performance_improvements = 0
        self.total_chunks_processed = 0

        # 线程安全
        self._lock = threading.Lock()

        logger.info(f"Dynamic Chunk Optimizer initialized - Initial chunk: {initial_chunk_size}")

    def start_monitoring(self):
        """启动性能监控"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Chunk optimizer monitoring started")

    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("Chunk optimizer monitoring stopped")

    def get_optimal_chunk_size(
        self,
        data_size: int,
        operation_type: str = 'general',
        estimated_complexity: float = 1.0
    ) -> int:
        """获取最优分块大小"""
        with self._lock:
            # 基于数据特征的初始估算
            base_chunk_size = self._estimate_base_chunk_size(
                data_size, operation_type, estimated_complexity
            )

            # 应用历史学习
            adjusted_chunk_size = self._apply_historical_learning(base_chunk_size)

            # 系统资源约束
            constrained_chunk_size = self._apply_system_constraints(adjusted_chunk_size)

            # 平滑处理，避免剧烈变化
            final_chunk_size = self._smooth_chunk_size_transition(constrained_chunk_size)

            # 更新当前状态
            self.current_chunk_size = final_chunk_size
            self.chunk_size_history.append(final_chunk_size)

            logger.debug(f"Optimal chunk size: {final_chunk_size} (data_size: {data_size})")
            return final_chunk_size

    def record_chunk_performance(
        self,
        chunk_size: int,
        processing_time: float,
        memory_usage_mb: float,
        items_processed: int,
        data_characteristics: Dict[str, Any] = None
    ):
        """记录分块性能"""
        with self._lock:
            # 计算性能指标
            cpu_usage = psutil.cpu_percent(interval=None)
            throughput = items_processed / processing_time if processing_time > 0 else 0
            efficiency_score = self._calculate_efficiency_score(
                throughput, memory_usage_mb, cpu_usage
            )

            # 创建性能记录
            metrics = ChunkPerformanceMetrics(
                chunk_size=chunk_size,
                processing_time=processing_time,
                memory_usage_mb=memory_usage_mb,
                cpu_usage_percent=cpu_usage,
                throughput_items_per_sec=throughput,
                efficiency_score=efficiency_score,
                timestamp=time.time(),
                data_characteristics=data_characteristics or {}
            )

            # 添加到历史记录
            self.performance_history.append(metrics)
            self.total_chunks_processed += items_processed

            # 检查是否需要自适应调整
            if self._should_adapt():
                self._adapt_chunk_size()

            logger.debug(f"Recorded performance: chunk={chunk_size}, "
                        f"throughput={throughput:.1f} items/s, "
                        f"efficiency={efficiency_score:.3f}")

    def _estimate_base_chunk_size(
        self,
        data_size: int,
        operation_type: str,
        estimated_complexity: float
    ) -> int:
        """基于数据特征估算基础分块大小"""
        # 系统核心数
        cpu_cores = multiprocessing.cpu_count()

        # 基础分块大小计算
        if operation_type == 'technical_indicators':
            # 技术指标计算：CPU密集型，适中分块
            base_size = max(
                self.min_chunk_size,
                min(self.max_chunk_size, data_size // (cpu_cores * 2))
            )
        elif operation_type == 'data_processing':
            # 数据处理：IO密集型，较大分块
            base_size = max(
                self.min_chunk_size,
                min(self.max_chunk_size, data_size // cpu_cores)
            )
        elif operation_type == 'memory_intensive':
            # 内存密集型：较小分块
            base_size = max(
                self.min_chunk_size,
                min(self.max_chunk_size, data_size // (cpu_cores * 4))
            )
        else:
            # 通用处理
            base_size = max(
                self.min_chunk_size,
                min(self.max_chunk_size, data_size // (cpu_cores * 1.5))
            )

        # 复杂度调整
        complexity_factor = 1.0 / math.sqrt(estimated_complexity)
        base_size = int(base_size * complexity_factor)

        return max(self.min_chunk_size, min(self.max_chunk_size, base_size))

    def _apply_historical_learning(self, base_chunk_size: int) -> int:
        """应用历史学习数据调整分块大小"""
        if len(self.performance_history) < 5:
            return base_chunk_size

        # 分析最近的性能趋势
        recent_metrics = list(self.performance_history)[-10:]

        # 计算不同分块大小的性能
        chunk_performance = {}
        for metrics in recent_metrics:
            chunk_size = metrics.chunk_size
            if chunk_size not in chunk_performance:
                chunk_performance[chunk_size] = []
            chunk_performance[chunk_size].append(metrics.efficiency_score)

        if not chunk_performance:
            return base_chunk_size

        # 找到性能最好的分块大小
        best_chunk_size = base_chunk_size
        best_performance = 0

        for chunk_size, performances in chunk_performance.items():
            avg_performance = np.mean(performances)
            if avg_performance > best_performance:
                best_performance = avg_performance
                best_chunk_size = chunk_size

        # 应用学习率，避免过快调整
        learning_rate = 0.3
        adjusted_size = int(
            base_size * (1 - learning_rate) + best_chunk_size * learning_rate
        )

        return max(self.min_chunk_size, min(self.max_chunk_size, adjusted_size))

    def _apply_system_constraints(self, chunk_size: int) -> int:
        """应用系统资源约束"""
        # 获取当前系统状态
        memory_info = psutil.virtual_memory()
        cpu_usage = psutil.cpu_percent(interval=None)

        # 内存约束
        available_memory_mb = memory_info.available / 1024 / 1024
        memory_safety_margin = 0.3  # 30%安全边际
        max_memory_per_chunk = (
            available_memory_mb * (1 - memory_safety_margin) /
            multiprocessing.cpu_count()
        )

        # 估算每个数据项的内存使用
        estimated_memory_per_item = 0.1  # KB，保守估算
        max_chunk_by_memory = int(
            (max_memory_per_chunk * 1024) / estimated_memory_per_item
        )

        # CPU负载约束
        if cpu_usage > self.optimization_target.target_cpu_utilization:
            # CPU负载高，减少分块大小
            chunk_size = int(chunk_size * 0.7)
        elif cpu_usage < self.optimization_target.target_cpu_utilization * 0.5:
            # CPU负载低，可以增加分块大小
            chunk_size = int(chunk_size * 1.3)

        # 应用内存约束
        chunk_size = min(chunk_size, max_chunk_by_memory)

        return max(self.min_chunk_size, min(self.max_chunk_size, chunk_size))

    def _smooth_chunk_size_transition(self, new_chunk_size: int) -> int:
        """平滑分块大小过渡，避免剧烈变化"""
        if len(self.chunk_size_history) < 2:
            return new_chunk_size

        # 计算变化率
        recent_sizes = list(self.chunk_size_history)[-5:]
        avg_recent_size = np.mean(recent_sizes)

        # 限制变化幅度
        max_change_ratio = 1.5  # 最多变化50%
        min_change_ratio = 0.67  # 最少变化33%

        if new_chunk_size > avg_recent_size:
            new_chunk_size = min(
                new_chunk_size,
                int(avg_recent_size * max_change_ratio)
            )
        else:
            new_chunk_size = max(
                new_chunk_size,
                int(avg_recent_size * min_change_ratio)
            )

        return new_chunk_size

    def _calculate_efficiency_score(
        self,
        throughput: float,
        memory_usage_mb: float,
        cpu_usage_percent: float
    ) -> float:
        """计算综合效率分数"""
        # 速度分数
        speed_score = min(1.0, throughput / self.optimization_target.min_throughput)

        # 内存效率分数（内存使用越少越好）
        memory_efficiency = max(
            0.0,
            1.0 - (memory_usage_mb / self.optimization_target.max_memory_mb)
        )

        # CPU效率分数（CPU使用率接近目标为好）
        cpu_efficiency = 1.0 - abs(
            cpu_usage_percent - self.optimization_target.target_cpu_utilization
        ) / 100.0

        # 加权综合分数
        weights = self.optimization_target.priority_weight
        efficiency_score = (
            weights['speed'] * speed_score +
            weights['memory'] * memory_efficiency +
            weights['efficiency'] * cpu_efficiency
        )

        return efficiency_score

    def _should_adapt(self) -> bool:
        """判断是否应该进行自适应调整"""
        current_time = time.time()

        # 时间间隔检查
        if current_time - self.last_adaptation_time < self.adaptation_interval:
            return False

        # 性能数据量检查
        if len(self.performance_history) < 10:
            return False

        # 性能稳定性检查
        recent_performances = [
            m.efficiency_score for m in list(self.performance_history)[-5:]
        ]
        performance_std = np.std(recent_performances)

        # 如果性能稳定但有提升空间，则进行调整
        if performance_std < 0.1:  # 性能稳定
            avg_performance = np.mean(recent_performances)
            if avg_performance < 0.8:  # 有提升空间
                return True

        return False

    def _adapt_chunk_size(self):
        """自适应调整分块大小"""
        recent_metrics = list(self.performance_history)[-20:]

        # 分析当前性能
        current_efficiency = np.mean([m.efficiency_score for m in recent_metrics])

        # 尝试不同分块大小
        test_sizes = [
            int(self.current_chunk_size * 0.8),
            int(self.current_chunk_size * 1.0),
            int(self.current_chunk_size * 1.2)
        ]

        # 基于历史数据预测最佳分块大小
        size_performance = {}
        for size in test_sizes:
            similar_size_metrics = [
                m for m in self.performance_history
                if abs(m.chunk_size - size) < size * 0.1
            ]

            if similar_size_metrics:
                size_performance[size] = np.mean([m.efficiency_score for m in similar_size_metrics])
            else:
                size_performance[size] = current_efficiency

        # 选择最佳分块大小
        best_size = max(size_performance.keys(), key=lambda k: size_performance[k])

        # 应用调整
        if size_performance[best_size] > current_efficiency * 1.05:  # 5%提升阈值
            self.current_chunk_size = best_size
            self.adaptation_count += 1
            self.performance_improvements += 1
            self.last_adaptation_time = time.time()

            logger.info(f"Adapted chunk size: {self.current_chunk_size} "
                       f"(performance improvement: {size_performance[best_size]:.3f})")

    def _monitoring_loop(self):
        """系统监控循环"""
        while self.monitoring_active:
            try:
                # 收集系统指标
                cpu_usage = psutil.cpu_percent(interval=0.5)
                memory_info = psutil.virtual_memory()

                system_metrics = {
                    'timestamp': time.time(),
                    'cpu_usage': cpu_usage,
                    'memory_usage_mb': memory_info.used / 1024 / 1024,
                    'memory_percent': memory_info.percent,
                    'available_memory_mb': memory_info.available / 1024 / 1024
                }

                self.system_metrics_history.append(system_metrics)

                # 检查是否需要紧急调整
                if memory_info.percent > 90:  # 内存使用过高
                    with self._lock:
                        self.current_chunk_size = max(
                            self.min_chunk_size,
                            int(self.current_chunk_size * 0.7)
                        )
                    logger.warning("High memory usage detected, reducing chunk size")

                time.sleep(1.0)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5.0)

    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        with self._lock:
            stats = {
                'current_chunk_size': self.current_chunk_size,
                'initial_chunk_size': self.initial_chunk_size,
                'adaptation_count': self.adaptation_count,
                'performance_improvements': self.performance_improvements,
                'total_chunks_processed': self.total_chunks_processed,
                'performance_history_size': len(self.performance_history),
                'chunk_size_history_size': len(self.chunk_size_history),
                'monitoring_active': self.monitoring_active,
                'optimization_target': asdict(self.optimization_target)
            }

            # 计算性能趋势
            if len(self.performance_history) >= 10:
                recent_metrics = list(self.performance_history)[-10:]
                early_metrics = list(self.performance_history)[:10]

                recent_avg_efficiency = np.mean([m.efficiency_score for m in recent_metrics])
                early_avg_efficiency = np.mean([m.efficiency_score for m in early_metrics])

                stats['efficiency_improvement'] = (
                    (recent_avg_efficiency - early_avg_efficiency) / early_avg_efficiency * 100
                )

                stats['recent_avg_throughput'] = np.mean([m.throughput_items_per_sec for m in recent_metrics])
                stats['recent_avg_memory_usage'] = np.mean([m.memory_usage_mb for m in recent_metrics])

            return stats

    def export_optimization_data(self, filepath: str):
        """导出优化数据"""
        try:
            data = {
                'timestamp': datetime.datetime.now().isoformat(),
                'stats': self.get_optimization_stats(),
                'performance_history': [asdict(m) for m in self.performance_history],
                'chunk_size_history': list(self.chunk_size_history),
                'system_metrics_history': list(self.system_metrics_history)
            }

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"Optimization data exported to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export optimization data: {e}")

    def load_optimization_data(self, filepath: str):
        """加载优化数据"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # 恢复性能历史
            if 'performance_history' in data:
                self.performance_history = deque(
                    [ChunkPerformanceMetrics(**m) for m in data['performance_history']],
                    maxlen=self.learning_window * 2
                )

            # 恢复分块大小历史
            if 'chunk_size_history' in data:
                self.chunk_size_history = deque(
                    data['chunk_size_history'],
                    maxlen=self.learning_window
                )

            logger.info(f"Optimization data loaded from {filepath}")

        except Exception as e:
            logger.error(f"Failed to load optimization data: {e}")

# 全局优化器实例
_global_optimizer = None

def get_chunk_optimizer() -> DynamicChunkOptimizer:
    """获取全局分块优化器实例"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = DynamicChunkOptimizer()
        _global_optimizer.start_monitoring()
    return _global_optimizer

def optimize_chunk_size(
    data_size: int,
    operation_type: str = 'general',
    estimated_complexity: float = 1.0
) -> int:
    """获取最优分块大小（简化接口）"""
    optimizer = get_chunk_optimizer()
    return optimizer.get_optimal_chunk_size(data_size, operation_type, estimated_complexity)

def record_performance(
    chunk_size: int,
    processing_time: float,
    memory_usage_mb: float,
    items_processed: int,
    data_characteristics: Dict[str, Any] = None
):
    """记录性能数据（简化接口）"""
    optimizer = get_chunk_optimizer()
    optimizer.record_chunk_performance(
        chunk_size, processing_time, memory_usage_mb, items_processed, data_characteristics
    )

def get_optimization_statistics() -> Dict[str, Any]:
    """获取优化统计信息（简化接口）"""
    optimizer = get_chunk_optimizer()
    return optimizer.get_optimization_stats()
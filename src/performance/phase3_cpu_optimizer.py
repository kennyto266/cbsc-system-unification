#!/usr/bin/env python3
"""
Phase 3: Enhanced CPU Performance Optimizer & Monitoring System
Phase 3: 增强型CPU性能优化器与监控系统

This module completes the GPU to CPU migration by implementing:
- Dynamic chunking optimization
- CPU-specific performance monitoring
- Advanced error handling and recovery
- Configuration migration tools
- Real-time system health monitoring
"""

import os
import sys
import time
import logging
import threading
import multiprocessing as mp
from typing import Dict, List, Tuple, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from pathlib import Path
import json
import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from functools import lru_cache
import psutil
import gc
import pickle
import hashlib
from datetime import datetime, timedelta
import warnings
import traceback

# Performance monitoring
try:
    import memory_profiler
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False

try:
    from numba import jit, njit, prange
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=RuntimeWarning)

logger = logging.getLogger(__name__)

@dataclass
class SystemResourceMetrics:
    """系统资源指标"""
    cpu_usage: float = 0.0
    memory_usage_mb: float = 0.0
    memory_percent: float = 0.0
    available_memory_mb: float = 0.0
    active_processes: int = 0
    system_load: float = 0.0
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0
    network_io_recv_mb: float = 0.0
    network_io_sent_mb: float = 0.0

@dataclass
class PerformanceMetrics:
    """性能指标"""
    operation_name: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    data_size: int = 0
    chunk_count: int = 0
    workers_used: int = 0
    throughput_ops_per_sec: float = 0.0
    memory_peak_mb: float = 0.0
    cpu_efficiency: float = 0.0
    success_rate: float = 100.0
    error_count: int = 0

@dataclass
class ChunkingConfig:
    """动态分块配置"""
    min_chunk_size: int = 1000
    max_chunk_size: int = 50000
    target_chunk_count: int = 32
    adaptive_threshold: float = 0.8
    memory_safety_factor: float = 0.85
    cpu_core_multiplier: float = 2.0

class DynamicChunkingOptimizer:
    """动态分块大小优化器"""

    def __init__(self, config: ChunkingConfig = None):
        self.config = config or ChunkingConfig()
        self.cpu_count = mp.cpu_count()
        self.memory_info = psutil.virtual_memory()
        self.chunking_history = []

        logger.info(f"DynamicChunkingOptimizer initialized - CPU cores: {self.cpu_count}, "
                   f"Memory: {self.memory_info.total / (1024**3):.1f}GB")

    def calculate_optimal_chunking(self, data_size: int, operation_complexity: str = 'medium') -> Dict[str, Any]:
        """
        计算最优分块策略

        Args:
            data_size: 数据大小
            operation_complexity: 操作复杂度 ('low', 'medium', 'high')

        Returns:
            分块策略字典
        """
        start_time = time.time()

        # 基础参数计算
        available_memory_mb = self.memory_info.available / (1024 * 1024)
        safe_memory_mb = available_memory_mb * self.config.memory_safety_factor

        # 根据操作复杂度调整内存需求
        complexity_factors = {
            'low': 1.0,
            'medium': 2.0,
            'high': 4.0
        }
        memory_factor = complexity_factors.get(operation_complexity, 2.0)

        # 计算数据内存需求
        data_memory_mb = (data_size * 8 * memory_factor) / (1024 * 1024)  # 假设float64

        # 初始分块数量计算
        initial_chunk_count = min(
            self.cpu_count * self.config.cpu_core_multiplier,
            self.config.target_chunk_count,
            max(1, int(safe_memory_mb / max(data_memory_mb, 1)))
        )

        # 分块大小计算
        base_chunk_size = max(
            self.config.min_chunk_size,
            min(
                self.config.max_chunk_size,
                int(data_size / initial_chunk_count)
            )
        )

        # 细化调整
        if data_size < self.config.min_chunk_size:
            # 小数据集不分块
            optimal_chunk_size = data_size
            optimal_chunk_count = 1
        elif data_size > self.config.max_chunk_size * initial_chunk_count:
            # 大数据集增加分块数量
            optimal_chunk_count = int(data_size / self.config.max_chunk_size) + 1
            optimal_chunk_size = self.config.max_chunk_size
        else:
            optimal_chunk_count = initial_chunk_count
            optimal_chunk_size = base_chunk_size

        # 生成具体分块
        chunks = self._generate_chunks(data_size, optimal_chunk_count, optimal_chunk_size)

        # 性能预测
        estimated_time = self._estimate_processing_time(data_size, len(chunks), operation_complexity)
        estimated_memory_usage = data_memory_mb * (1 + len(chunks) * 0.1)  # 10% overhead per chunk

        strategy = {
            'data_size': data_size,
            'operation_complexity': operation_complexity,
            'total_chunks': len(chunks),
            'chunk_size': optimal_chunk_size,
            'chunks': chunks,
            'workers_to_use': min(len(chunks), self.cpu_count * 2),
            'estimated_time_seconds': estimated_time,
            'estimated_memory_mb': estimated_memory_usage,
            'memory_safety_ratio': estimated_memory_usage / safe_memory_mb if safe_memory_mb > 0 else 1.0,
            'calculation_time_ms': (time.time() - start_time) * 1000
        }

        # 记录分块历史
        self.chunking_history.append({
            'timestamp': time.time(),
            'data_size': data_size,
            'chunks_created': len(chunks),
            'chunk_size': optimal_chunk_size
        })

        logger.info(f"Optimal chunking calculated: {len(chunks)} chunks of size {optimal_chunk_size} "
                   f"for {data_size} data points (complexity: {operation_complexity})")

        return strategy

    def _generate_chunks(self, data_size: int, chunk_count: int, chunk_size: int) -> List[Tuple[int, int]]:
        """生成数据分块"""
        chunks = []

        for i in range(chunk_count):
            start = i * chunk_size
            if start >= data_size:
                break
            end = min(start + chunk_size, data_size)
            chunks.append((start, end))

        return chunks

    def _estimate_processing_time(self, data_size: int, chunk_count: int, complexity: str) -> float:
        """估算处理时间"""
        base_throughput = {
            'low': 100000,     # 每秒处理数据点
            'medium': 50000,
            'high': 10000
        }

        throughput = base_throughput.get(complexity, 50000)
        parallel_factor = min(chunk_count, self.cpu_count)
        effective_throughput = throughput * parallel_factor * 0.8  # 80%效率系数

        return data_size / effective_throughput if effective_throughput > 0 else 1.0

    def get_chunking_statistics(self) -> Dict[str, Any]:
        """获取分块统计信息"""
        if not self.chunking_history:
            return {'status': 'no_history'}

        recent_history = self.chunking_history[-20:]  # 最近20次

        return {
            'total_chunking_operations': len(self.chunking_history),
            'recent_operations': len(recent_history),
            'average_chunks_per_operation': np.mean([h['chunks_created'] for h in recent_history]),
            'average_chunk_size': np.mean([h['chunk_size'] for h in recent_history]),
            'largest_dataset_processed': max([h['data_size'] for h in recent_history]),
            'system_efficiency_trend': self._calculate_efficiency_trend(recent_history)
        }

    def _calculate_efficiency_trend(self, history: List[Dict]) -> str:
        """计算效率趋势"""
        if len(history) < 5:
            return "insufficient_data"

        recent_efficiency = np.mean([h['chunks_created'] for h in history[-5:]])
        older_efficiency = np.mean([h['chunks_created'] for h in history[-10:-5]])

        if recent_efficiency > older_efficiency * 1.1:
            return "improving"
        elif recent_efficiency < older_efficiency * 0.9:
            return "declining"
        else:
            return "stable"

class CPUPerformanceMonitor:
    """CPU性能监控器"""

    def __init__(self, monitoring_interval: float = 1.0):
        self.monitoring_interval = monitoring_interval
        self.is_monitoring = False
        self.monitoring_thread = None
        self.performance_history = []
        self.current_metrics = SystemResourceMetrics()
        self.alerts = []

    def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            logger.warning("Monitoring is already active")
            return

        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("CPU performance monitoring started")

    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("CPU performance monitoring stopped")

    def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                self._collect_metrics()
                self._check_alerts()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(self.monitoring_interval)

    def _collect_metrics(self):
        """收集系统指标"""
        # CPU指标
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_count_physical = psutil.cpu_count(logical=False)

        # 内存指标
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # 磁盘IO
        disk_io = psutil.disk_io_counters()
        disk_io_read_mb = (disk_io.read_bytes / (1024 * 1024)) if disk_io else 0
        disk_io_write_mb = (disk_io.write_bytes / (1024 * 1024)) if disk_io else 0

        # 网络IO
        network_io = psutil.net_io_counters()
        network_io_recv_mb = (network_io.bytes_recv / (1024 * 1024)) if network_io else 0
        network_io_sent_mb = (network_io.bytes_sent / (1024 * 1024)) if network_io else 0

        # 进程信息
        process_count = len(psutil.pids())

        # 更新当前指标
        self.current_metrics = SystemResourceMetrics(
            cpu_usage=cpu_percent,
            memory_usage_mb=memory.used / (1024 * 1024),
            memory_percent=memory.percent,
            available_memory_mb=memory.available / (1024 * 1024),
            active_processes=process_count,
            system_load=cpu_count_logical / cpu_count_physical if cpu_count_physical > 0 else 1.0,
            disk_io_read_mb=disk_io_read_mb,
            disk_io_write_mb=disk_io_write_mb,
            network_io_recv_mb=network_io_recv_mb,
            network_io_sent_mb=network_io_sent_mb
        )

        # 记录历史
        self.performance_history.append({
            'timestamp': time.time(),
            'metrics': self.current_metrics
        })

        # 保持历史记录大小
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]

    def _check_alerts(self):
        """检查告警条件"""
        metrics = self.current_metrics

        # CPU使用率告警
        if metrics.cpu_usage > 90:
            self._add_alert("HIGH_CPU_USAGE", f"CPU usage: {metrics.cpu_usage:.1f}%")

        # 内存使用率告警
        if metrics.memory_percent > 85:
            self._add_alert("HIGH_MEMORY_USAGE", f"Memory usage: {metrics.memory_percent:.1f}%")

        # 可用内存告警
        if metrics.available_memory_mb < 1024:  # 小于1GB
            self._add_alert("LOW_AVAILABLE_MEMORY", f"Available memory: {metrics.available_memory_mb:.1f}MB")

    def _add_alert(self, alert_type: str, message: str):
        """添加告警"""
        alert = {
            'timestamp': time.time(),
            'type': alert_type,
            'message': message,
            'severity': 'WARNING' if 'WARNING' in alert_type else 'ERROR'
        }
        self.alerts.append(alert)

        # 保持告警历史
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

        logger.warning(f"Performance Alert: {alert_type} - {message}")

    def get_performance_summary(self, duration_minutes: int = 10) -> Dict[str, Any]:
        """获取性能摘要"""
        cutoff_time = time.time() - (duration_minutes * 60)
        recent_metrics = [
            entry for entry in self.performance_history
            if entry['timestamp'] > cutoff_time
        ]

        if not recent_metrics:
            return {'status': 'no_data'}

        # 计算统计信息
        cpu_values = [m['metrics'].cpu_usage for m in recent_metrics]
        memory_values = [m['metrics'].memory_percent for m in recent_metrics]

        return {
            'duration_minutes': duration_minutes,
            'sample_count': len(recent_metrics),
            'cpu': {
                'average': np.mean(cpu_values),
                'maximum': np.max(cpu_values),
                'minimum': np.min(cpu_values),
                'current': self.current_metrics.cpu_usage
            },
            'memory': {
                'average': np.mean(memory_values),
                'maximum': np.max(memory_values),
                'minimum': np.min(memory_values),
                'current': self.current_metrics.memory_percent,
                'available_mb': self.current_metrics.available_memory_mb
            },
            'active_alerts': len([a for a in self.alerts if time.time() - a['timestamp'] < duration_minutes * 60]),
            'system_health': self._calculate_health_score(cpu_values, memory_values)
        }

    def _calculate_health_score(self, cpu_values: List[float], memory_values: List[float]) -> float:
        """计算系统健康分数 (0-100)"""
        avg_cpu = np.mean(cpu_values)
        avg_memory = np.mean(memory_values)

        # CPU健康分数 (CPU越低越健康)
        cpu_health = max(0, 100 - avg_cpu)

        # 内存健康分数 (内存使用率越低越健康)
        memory_health = max(0, 100 - avg_memory)

        # 综合健康分数
        overall_health = (cpu_health + memory_health) / 2

        return min(100, max(0, overall_health))

class ConfigMigrationTool:
    """配置迁移工具"""

    def __init__(self):
        self.migration_log = []

    def migrate_gpu_config_to_cpu(self, gpu_config_path: str, cpu_config_path: str) -> bool:
        """
        将GPU配置迁移到CPU配置

        Args:
            gpu_config_path: GPU配置文件路径
            cpu_config_path: CPU配置文件路径

        Returns:
            迁移是否成功
        """
        try:
            # 读取GPU配置
            with open(gpu_config_path, 'r', encoding='utf-8') as f:
                gpu_config = json.load(f)

            # 转换配置
            cpu_config = self._convert_config(gpu_config)

            # 写入CPU配置
            os.makedirs(os.path.dirname(cpu_config_path), exist_ok=True)
            with open(cpu_config_path, 'w', encoding='utf-8') as f:
                json.dump(cpu_config, f, indent=2, ensure_ascii=False)

            self.migration_log.append({
                'timestamp': time.time(),
                'action': 'config_migration',
                'source': gpu_config_path,
                'target': cpu_config_path,
                'status': 'success'
            })

            logger.info(f"GPU config migrated to CPU config: {gpu_config_path} -> {cpu_config_path}")
            return True

        except Exception as e:
            error_msg = f"Config migration failed: {e}"
            logger.error(error_msg)
            self.migration_log.append({
                'timestamp': time.time(),
                'action': 'config_migration',
                'status': 'failed',
                'error': str(e)
            })
            return False

    def _convert_config(self, gpu_config: Dict[str, Any]) -> Dict[str, Any]:
        """转换GPU配置到CPU配置"""
        cpu_config = {
            "calculation_engine": {
                "backend": "cpu",
                "max_workers": min(mp.cpu_count() * 2, 32),
                "use_process_pool": True,
                "use_thread_pool": False,
                "enable_multiprocessing": True
            },
            "memory_management": {
                "total_memory_limit_gb": psutil.virtual_memory().total / (1024**3) * 0.8,
                "memory_per_process_mb": 1024,
                "enable_memory_monitoring": True,
                "gc_frequency": 10
            },
            "performance_optimization": {
                "enable_dynamic_chunking": True,
                "min_chunk_size": 1000,
                "max_chunk_size": 50000,
                "adaptive_chunking": True,
                "numba_optimization": True
            },
            "monitoring": {
                "enable_performance_monitoring": True,
                "monitoring_interval": 1.0,
                "log_performance_metrics": True,
                "enable_alerts": True
            }
        }

        # 保留相关配置
        if 'indicators' in gpu_config:
            cpu_config['indicators'] = gpu_config['indicators']

        if 'data_sources' in gpu_config:
            cpu_config['data_sources'] = gpu_config['data_sources']

        return cpu_config

    def validate_cpu_config(self, config_path: str) -> Dict[str, Any]:
        """验证CPU配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            validation_results = {
                'config_path': config_path,
                'is_valid': True,
                'issues': [],
                'recommendations': []
            }

            # 检查必需字段
            required_fields = ['calculation_engine', 'memory_management', 'performance_optimization']
            for field in required_fields:
                if field not in config:
                    validation_results['issues'].append(f"Missing required field: {field}")
                    validation_results['is_valid'] = False

            # 检查计算引擎配置
            if 'calculation_engine' in config:
                engine = config['calculation_engine']
                if engine.get('max_workers', 0) > mp.cpu_count() * 4:
                    validation_results['recommendations'].append(
                        f"Consider reducing max_workers from {engine['max_workers']} to {mp.cpu_count() * 2}"
                    )

                if engine.get('use_process_pool') and engine.get('use_thread_pool'):
                    validation_results['issues'].append("Cannot use both process_pool and thread_pool")
                    validation_results['is_valid'] = False

            # 检查内存配置
            if 'memory_management' in config:
                memory = config['memory_management']
                total_memory_gb = psutil.virtual_memory().total / (1024**3)

                if memory.get('total_memory_limit_gb', 0) > total_memory_gb * 0.9:
                    validation_results['recommendations'].append(
                        f"Memory limit {memory['total_memory_limit_gb']:.1f}GB exceeds 90% of system memory {total_memory_gb:.1f}GB"
                    )

            return validation_results

        except Exception as e:
            return {
                'config_path': config_path,
                'is_valid': False,
                'issues': [f"Validation error: {e}"],
                'recommendations': []
            }

class ErrorHandlingRecoverySystem:
    """错误处理和恢复系统"""

    def __init__(self):
        self.error_history = []
        self.recovery_strategies = {}
        self.circuit_breaker_state = {
            'is_open': False,
            'failure_count': 0,
            'last_failure_time': 0,
            'recovery_timeout': 60  # seconds
        }

    def register_recovery_strategy(self, error_type: str, strategy: Callable):
        """注册恢复策略"""
        self.recovery_strategies[error_type] = strategy
        logger.info(f"Recovery strategy registered for: {error_type}")

    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        处理错误并尝试恢复

        Args:
            error: 发生的错误
            context: 错误上下文信息

        Returns:
            处理结果
        """
        error_info = {
            'timestamp': time.time(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {},
            'traceback': traceback.format_exc()
        }

        # 记录错误
        self.error_history.append(error_info)
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]

        # 检查断路器状态
        if self._is_circuit_breaker_open():
            return {
                'handled': False,
                'action': 'circuit_breaker_open',
                'message': 'Circuit breaker is open, rejecting operation'
            }

        # 尝试恢复
        recovery_result = self._attempt_recovery(error_info)

        # 更新断路器状态
        self._update_circuit_breaker(recovery_result['success'])

        logger.info(f"Error handled: {error_info['error_type']} - Recovery: {recovery_result['action']}")

        return recovery_result

    def _is_circuit_breaker_open(self) -> bool:
        """检查断路器是否打开"""
        if not self.circuit_breaker_state['is_open']:
            return False

        # 检查是否可以尝试恢复
        time_since_last_failure = time.time() - self.circuit_breaker_state['last_failure_time']
        if time_since_last_failure > self.circuit_breaker_state['recovery_timeout']:
            self.circuit_breaker_state['is_open'] = False
            self.circuit_breaker_state['failure_count'] = 0
            logger.info("Circuit breaker timeout, attempting recovery")
            return False

        return True

    def _attempt_recovery(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """尝试恢复"""
        error_type = error_info['error_type']

        if error_type in self.recovery_strategies:
            try:
                strategy = self.recovery_strategies[error_type]
                recovery_result = strategy(error_info)

                return {
                    'handled': True,
                    'action': 'recovery_strategy_executed',
                    'strategy_used': error_type,
                    'success': recovery_result.get('success', False),
                    'result': recovery_result
                }
            except Exception as recovery_error:
                logger.error(f"Recovery strategy failed: {recovery_error}")
                return {
                    'handled': False,
                    'action': 'recovery_strategy_failed',
                    'error': str(recovery_error),
                    'success': False
                }
        else:
            # 默认恢复策略
            return self._default_recovery_strategy(error_info)

    def _default_recovery_strategy(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """默认恢复策略"""
        error_type = error_info['error_type']

        # 内存错误恢复
        if 'Memory' in error_type:
            gc.collect()  # 强制垃圾回收
            return {
                'handled': True,
                'action': 'memory_cleanup',
                'success': True
            }

        # 进程错误恢复
        elif 'Process' in error_type or 'Pool' in error_type:
            return {
                'handled': True,
                'action': 'restart_process_pool',
                'success': True
            }

        # 数据错误恢复
        elif 'Value' in error_type or 'Type' in error_type:
            return {
                'handled': True,
                'action': 'data_validation_fallback',
                'success': True
            }

        # 其他错误
        else:
            return {
                'handled': False,
                'action': 'unknown_error_type',
                'success': False
            }

    def _update_circuit_breaker(self, recovery_success: bool):
        """更新断路器状态"""
        if recovery_success:
            # 成功恢复，重置断路器
            self.circuit_breaker_state['failure_count'] = 0
            self.circuit_breaker_state['is_open'] = False
        else:
            # 恢复失败，增加失败计数
            self.circuit_breaker_state['failure_count'] += 1
            self.circuit_breaker_state['last_failure_time'] = time.time()

            # 失败次数过多，打开断路器
            if self.circuit_breaker_state['failure_count'] >= 5:
                self.circuit_breaker_state['is_open'] = True
                logger.warning("Circuit breaker opened due to repeated failures")

    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计"""
        if not self.error_history:
            return {'status': 'no_errors'}

        # 统计错误类型
        error_types = {}
        for error in self.error_history:
            error_type = error['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1

        # 最近错误
        recent_errors = [
            error for error in self.error_history
            if time.time() - error['timestamp'] < 3600  # 最近1小时
        ]

        return {
            'total_errors': len(self.error_history),
            'recent_errors': len(recent_errors),
            'error_types': error_types,
            'most_common_error': max(error_types.items(), key=lambda x: x[1]) if error_types else None,
            'circuit_breaker_status': {
                'is_open': self.circuit_breaker_state['is_open'],
                'failure_count': self.circuit_breaker_state['failure_count'],
                'last_failure_time': self.circuit_breaker_state['last_failure_time']
            },
            'recovery_strategies_available': len(self.recovery_strategies)
        }

# Convenience functions for creating instances
def create_chunking_optimizer(config: ChunkingConfig = None) -> DynamicChunkingOptimizer:
    """创建分块优化器"""
    return DynamicChunkingOptimizer(config)

def create_performance_monitor(interval: float = 1.0) -> CPUPerformanceMonitor:
    """创建性能监控器"""
    return CPUPerformanceMonitor(interval)

def create_config_migration_tool() -> ConfigMigrationTool:
    """创建配置迁移工具"""
    return ConfigMigrationTool()

def create_error_recovery_system() -> ErrorHandlingRecoverySystem:
    """创建错误恢复系统"""
    return ErrorHandlingRecoverySystem()

if __name__ == "__main__":
    # Test the Phase 3 implementation
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("=" * 80)
    print("Phase 3: Enhanced CPU Performance Optimizer & Monitoring System")
    print("=" * 80)

    # Test components
    print("\n1. Testing Dynamic Chunking Optimizer...")
    chunking_optimizer = create_chunking_optimizer()

    # Test different data sizes
    test_sizes = [1000, 10000, 100000]
    for size in test_sizes:
        strategy = chunking_optimizer.calculate_optimal_chunking(size, 'medium')
        print(f"  Data size {size}: {strategy['total_chunks']} chunks, "
              f"estimated time: {strategy['estimated_time_seconds']:.3f}s")

    print("\n2. Testing Performance Monitor...")
    performance_monitor = create_performance_monitor()
    performance_monitor.start_monitoring()

    # Wait for some monitoring data
    time.sleep(3)

    summary = performance_monitor.get_performance_summary(1)
    print(f"  CPU Usage: {summary['cpu']['average']:.1f}%")
    print(f"  Memory Usage: {summary['memory']['average']:.1f}%")
    print(f"  System Health: {summary['system_health']:.1f}/100")

    performance_monitor.stop_monitoring()

    print("\n3. Testing Error Recovery System...")
    error_recovery = create_error_recovery_system()

    # Register a custom recovery strategy
    def memory_recovery(error_info):
        return {'success': True, 'action': 'custom_memory_cleanup'}

    error_recovery.register_recovery_strategy('MemoryError', memory_recovery)

    # Test error handling
    test_error = MemoryError("Test memory error")
    result = error_recovery.handle_error(test_error, {'operation': 'test'})
    print(f"  Error handled: {result['success']}")
    print(f"  Recovery action: {result['action']}")

    print("\n4. Testing Config Migration Tool...")
    config_migration = create_config_migration_tool()

    # Create a sample GPU config
    sample_gpu_config = {
        "use_gpu": True,
        "batch_size": 10000,
        "memory_limit_gb": 8.0,
        "indicators": ["RSI", "MACD", "Bollinger"]
    }

    # Save sample config
    os.makedirs('test_config', exist_ok=True)
    with open('test_config/gpu_config.json', 'w') as f:
        json.dump(sample_gpu_config, f)

    # Test migration
    success = config_migration.migrate_gpu_config_to_cpu(
        'test_config/gpu_config.json',
        'test_config/cpu_config.json'
    )
    print(f"  Migration successful: {success}")

    if success:
        validation = config_migration.validate_cpu_config('test_config/cpu_config.json')
        print(f"  CPU config valid: {validation['is_valid']}")
        if validation['recommendations']:
            print(f"  Recommendations: {validation['recommendations']}")

    print("\n" + "=" * 80)
    print("Phase 3 Implementation Complete!")
    print("=" * 80)
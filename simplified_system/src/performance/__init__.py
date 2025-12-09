#!/usr / bin / env python3
"""
性能优化模块
Performance Optimization Module

提供高性能缓存、并行计算和GPU加速功能
"""

from .gpu_manager import get_gpu_environment, get_gpu_manager
from .high_performance_cache import cached_operation, global_cache
from .parallel_optimizer import global_parallel_optimizer, parallel_execute
from .performance_monitor import (
    get_performance_monitor,
    start_global_monitoring,
    stop_global_monitoring,
)

__all__ = [
    "global_cache",
    "cached_operation",
    "global_parallel_optimizer",
    "parallel_execute",
    "get_gpu_manager",
    "get_gpu_environment",
    "get_performance_monitor",
    "start_global_monitoring",
    "stop_global_monitoring",
]

__version__ = "1.0.0"

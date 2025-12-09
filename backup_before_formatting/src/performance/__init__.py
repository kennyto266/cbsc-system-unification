"""
港股量化交易系统 - 性能优化模块

该模块提供全面的性能优化工具，包括：
- 性能分析和分析器
- 多层缓存系统
- I / O优化
- 懒加载
- 连接池管理

主要功能：
- 实时性能监控
- CPU和内存使用分析
- 数据访问优化
- 并发性能提升
- 资源池化
"""

from .cache_layer import CacheManager, LRUCache, MultiLevelCache, TTLCache
from .connection_pool import (
    ConnectionManager,
    DatabaseConnectionPool,
    HTTPConnectionPool,
)
from .io_optimizer import AsyncIOBatchProcessor, DatabaseQueryOptimizer, IOOptimizer
from .lazy_loader import DataFrameLazyLoader, LazyLoader, MemoryManagedLoader
from .profiler import Profiler, ProfileResult

__all__ = [
    "Profiler",
    "ProfileResult",
    "LRUCache",
    "TTLCache",
    "MultiLevelCache",
    "CacheManager",
    "IOOptimizer",
    "AsyncIOBatchProcessor",
    "DatabaseQueryOptimizer",
    "LazyLoader",
    "DataFrameLazyLoader",
    "MemoryManagedLoader",
    "HTTPConnectionPool",
    "DatabaseConnectionPool",
    "ConnectionManager",
]

__version__ = "1.0.0"

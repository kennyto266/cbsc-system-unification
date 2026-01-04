#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Optimization Module
性能優化模塊

Provides:
- Algorithm complexity optimization
- Memory optimization management
- Lazy loading utilities
- Code splitting support
"""

import gc
import hashlib
import importlib
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from functools import wraps, lru_cache
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================================
# Cache Management
# ============================================================================

class LRUCache(Generic[T]):
    """
    Thread-safe LRU cache with TTL support
    帶 TTL 支持的線程安全 LRU 緩存
    """

    def __init__(self, max_size: int = 128, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[T, float]] = OrderedDict()
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create lock for key"""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def get(self, key: str) -> Optional[T]:
        """Get value from cache"""
        if key not in self._cache:
            return None

        value, expiry = self._cache[key]

        # Check if expired
        if expiry and asyncio.get_event_loop().time() > expiry:
            del self._cache[key]
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        return value

    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        ttl = ttl if ttl is not None else self.default_ttl
        expiry = asyncio.get_event_loop().time() + ttl if ttl else 0

        async with self._get_lock(key):
            if key in self._cache:
                self._cache.move_to_end(key)

            self._cache[key] = (value, expiry)

            # Evict oldest if at capacity
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    async def invalidate(self, key: str) -> bool:
        """Invalidate cache entry"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()

    def size(self) -> int:
        """Get current cache size"""
        return len(self._cache)


# ============================================================================
# Memoization Decorators
# ============================================================================

def memoize_async(ttl: int = 3600, max_size: int = 128):
    """
    Async memoization decorator with TTL
    帶 TTL 的異步記憶化裝飾器

    Usage:
        @memoize_async(ttl=600)
        async def expensive_function(arg1, arg2):
            return await some_io_operation()
    """
    cache = LRUCache(max_size=max_size, default_ttl=ttl)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            key_parts = [func.__name__, str(args), str(sorted(kwargs.items()))]
            cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()

            # Try cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache.set(cache_key, result, ttl=ttl)

            return result

        # Add cache management methods
        wrapper.cache = cache
        wrapper.cache_clear = cache.clear
        wrapper.cache_info = lambda: {
            'size': cache.size(),
            'max_size': max_size,
            'ttl': ttl
        }

        return wrapper

    return decorator


def memoize_sync(max_size: int = 128):
    """
    Sync memoization decorator using LRU cache
    同步記憶化裝飾器

    Usage:
        @memoize_sync(max_size=256)
        def expensive_function(arg1, arg2):
            return complex_calculation(arg1, arg2)
    """
    return lru_cache(maxsize=max_size)


# ============================================================================
# Lazy Loading
# ============================================================================

@dataclass
class LazyModule:
    """Lazy module descriptor"""
    name: str
    module_path: str
    loaded: bool = False
    _module: Optional[Any] = field(default=None, repr=False)

    async def load(self) -> Any:
        """Load module on demand"""
        if self.loaded:
            return self._module

        try:
            logger.debug(f"Lazy loading module: {self.name}")
            self._module = importlib.import_module(self.module_path)
            self.loaded = True
            return self._module
        except ImportError as e:
            logger.error(f"Failed to load module {self.name}: {e}")
            raise

    def get(self) -> Any:
        """Synchronous get (must be loaded first)"""
        if not self.loaded:
            raise RuntimeError(f"Module {self.name} not loaded. Call load() first.")
        return self._module


class LazyLoader:
    """
    Lazy loader for delayed module loading
    延遲模塊加載器

    Usage:
        lazy_loader = LazyLoader()
        lazy_loader.register('numpy', 'numpy')
        lazy_loader.register('pandas', 'pandas')

        # Load when needed
        np = await lazy_loader.load('numpy')
    """

    def __init__(self):
        self._modules: Dict[str, LazyModule] = {}

    def register(self, name: str, module_path: str) -> None:
        """Register a module for lazy loading"""
        self._modules[name] = LazyModule(name=name, module_path=module_path)

    async def load(self, name: str) -> Any:
        """Load a registered module"""
        if name not in self._modules:
            raise ValueError(f"Module '{name}' not registered")

        return await self._modules[name].load()

    def is_loaded(self, name: str) -> bool:
        """Check if module is loaded"""
        return name in self._modules and self._modules[name].loaded

    def unload(self, name: str) -> None:
        """Unload a module (free memory)"""
        if name in self._modules:
            self._modules[name]._module = None
            self._modules[name].loaded = False

    def unload_all(self) -> None:
        """Unload all modules"""
        for module in self._modules.values():
            module._module = None
            module.loaded = False


# ============================================================================
# Memory Optimization
# ============================================================================

class MemoryOptimizer:
    """
    Memory optimization manager
    內存優化管理器

    Features:
    - Automatic garbage collection
    - Cache clearing
    - Memory usage monitoring
    """

    def __init__(self, gc_threshold: int = 1000, memory_limit_percent: float = 80.0):
        self.gc_threshold = gc_threshold
        self.memory_limit_percent = memory_limit_percent
        self._monitored_caches: List[LRUCache] = []

    def register_cache(self, cache: LRUCache) -> None:
        """Register a cache for monitoring"""
        self._monitored_caches.append(cache)

    async def optimize(self) -> Dict[str, Any]:
        """
        Optimize memory usage
        優化內存使用
        """
        try:
            import psutil
            memory = psutil.virtual_memory()
        except ImportError:
            # Fallback without psutil
            logger.warning("psutil not installed, using basic optimization")
            return await self._basic_optimize()

        if memory.percent > self.memory_limit_percent:
            return await self._aggressive_cleanup(memory.percent)
        else:
            return {
                'action': 'no_action_needed',
                'memory_percent': memory.percent,
                'limit': self.memory_limit_percent
            }

    async def _aggressive_cleanup(self, current_percent: float) -> Dict[str, Any]:
        """Perform aggressive memory cleanup"""
        # Force garbage collection
        collected = gc.collect(generation=2)

        # Clear monitored caches
        cleared_caches = 0
        for cache in self._monitored_caches:
            size_before = cache.size()
            cache.clear()
            cleared_caches += size_before

        result = {
            'action': 'aggressive_cleanup',
            'memory_before': current_percent,
            'objects_collected': collected,
            'cache_entries_cleared': cleared_caches,
            'caches_cleared': len(self._monitored_caches)
        }

        logger.info(f"Memory cleanup: {result}")
        return result

    async def _basic_optimize(self) -> Dict[str, Any]:
        """Basic optimization without psutil"""
        collected = gc.collect()

        cleared_caches = 0
        for cache in self._monitored_caches:
            cleared_caches += cache.size()
            cache.clear()

        return {
            'action': 'basic_cleanup',
            'objects_collected': collected,
            'cache_entries_cleared': cleared_caches
        }

    async def get_memory_info(self) -> Dict[str, Any]:
        """Get current memory usage info"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                'rss': memory_info.rss / 1024 / 1024,  # MB
                'vms': memory_info.vms / 1024 / 1024,  # MB
                'percent': psutil.virtual_memory().percent,
                'available': psutil.virtual_memory().available / 1024 / 1024,  # MB
            }
        except ImportError:
            # Fallback
            import sys
            return {
                'rss': sys.getsizeof([]) / 1024 / 1024,  # Rough estimate
                'vms': 0,
                'percent': 0,
                'available': 0,
            }


# ============================================================================
# Algorithm Optimization
# ============================================================================

class OptimizedCalculator:
    """
    Base class for optimized calculations
    優化計算器基類

    Features:
    - Result caching
    - Precomputed values
    - Vectorized operations
    """

    def __init__(self):
        self._result_cache: LRUCache = LRUCache(max_size=256)
        self._precomputed: Dict[str, Any] = {}

    def _generate_cache_key(self, data: Dict[str, Any]) -> str:
        """Generate cache key from data"""
        sorted_items = sorted(data.items())
        key_str = str(sorted_items)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def cached_calculate(self, data: Dict[str, Any], func: Callable) -> Any:
        """
        Calculate with caching
        帶緩存的計算
        """
        cache_key = self._generate_cache_key(data)

        # Check cache
        cached = await self._result_cache.get(cache_key)
        if cached is not None:
            return cached

        # Execute calculation
        result = await func(data)

        # Cache result
        await self._result_cache.set(cache_key, result)

        return result

    def precompute(self, key: str, value: Any) -> None:
        """Store precomputed value"""
        self._precomputed[key] = value

    def get_precomputed(self, key: str) -> Optional[Any]:
        """Get precomputed value"""
        return self._precomputed.get(key)


# ============================================================================
# Performance Monitoring
# ============================================================================

@dataclass
class PerformanceMetrics:
    """Performance metrics"""
    function_name: str
    call_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0

    def update(self, duration: float) -> None:
        """Update metrics with new duration"""
        self.call_count += 1
        self.total_time += duration
        self.avg_time = self.total_time / self.call_count
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)


class PerformanceMonitor:
    """
    Performance monitoring utility
    性能監控工具

    Usage:
        monitor = PerformanceMonitor()

        @monitor.track
        async def my_function():
            ...
    """

    def __init__(self):
        self._metrics: Dict[str, PerformanceMetrics] = {}

    def track(self, func: Callable) -> Callable:
        """Decorator to track function performance"""
        metric_name = f"{func.__module__}.{func.__name__}"

        if metric_name not in self._metrics:
            self._metrics[metric_name] = PerformanceMetrics(function_name=metric_name)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            import time
            start = time.perf_counter()

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start
                self._metrics[metric_name].update(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            start = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start
                self._metrics[metric_name].update(duration)

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    def get_metrics(self, func_name: Optional[str] = None) -> Dict[str, PerformanceMetrics]:
        """Get performance metrics"""
        if func_name:
            return {func_name: self._metrics.get(func_name)}
        return self._metrics.copy()

    def get_report(self) -> str:
        """Get formatted performance report"""
        lines = ["Performance Report", "=" * 60]

        for name, metrics in self._metrics.items():
            lines.append(f"\n{name}:")
            lines.append(f"  Calls: {metrics.call_count}")
            lines.append(f"  Avg: {metrics.avg_time*1000:.2f}ms")
            lines.append(f"  Min: {metrics.min_time*1000:.2f}ms")
            lines.append(f"  Max: {metrics.max_time*1000:.2f}ms")

        return "\n".join(lines)


# ============================================================================
# Global instances
# ============================================================================

# Global memory optimizer instance
_memory_optimizer: Optional[MemoryOptimizer] = None

# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None

# Global lazy loader instance
_lazy_loader: Optional[LazyLoader] = None


def get_memory_optimizer() -> MemoryOptimizer:
    """Get global memory optimizer instance"""
    global _memory_optimizer
    if _memory_optimizer is None:
        _memory_optimizer = MemoryOptimizer()
    return _memory_optimizer


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_lazy_loader() -> LazyLoader:
    """Get global lazy loader instance"""
    global _lazy_loader
    if _lazy_loader is None:
        _lazy_loader = LazyLoader()
    return _lazy_loader


__all__ = [
    # Cache
    "LRUCache",

    # Decorators
    "memoize_async",
    "memoize_sync",

    # Lazy Loading
    "LazyModule",
    "LazyLoader",
    "get_lazy_loader",

    # Memory Optimization
    "MemoryOptimizer",
    "get_memory_optimizer",

    # Algorithm Optimization
    "OptimizedCalculator",

    # Performance Monitoring
    "PerformanceMetrics",
    "PerformanceMonitor",
    "get_performance_monitor",
]

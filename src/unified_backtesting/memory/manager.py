"""
Adaptive Memory Management System for Unified Backtesting

Advanced memory management system designed to handle large-scale parameter
optimization (120,832+ combinations) within the 4GB constraint through
adaptive allocation, intelligent caching, and resource monitoring.

Key Features:
- Dynamic memory allocation and deallocation based on usage patterns
- Intelligent caching with LRU eviction policies
- Memory pressure monitoring and automatic resource adjustment
- Chunked data processing for memory efficiency
- Garbage collection optimization
- Memory leak detection and prevention
- Performance optimization through memory pooling
"""

import os
import gc
import time
import logging
import threading
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from collections import OrderedDict, defaultdict
import numpy as np
import pandas as pd
import psutil
import weakref
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Memory usage statistics"""
    total_memory_gb: float
    available_memory_gb: float
    used_memory_gb: float
    memory_usage_percent: float
    process_memory_gb: float
    process_memory_percent: float

    def is_under_pressure(self, threshold: float = 0.8) -> bool:
        """Check if memory is under pressure"""
        return self.memory_usage_percent > (threshold * 100)

    def is_process_limit_exceeded(self, limit_gb: float) -> bool:
        """Check if process memory exceeds limit"""
        return self.process_memory_gb > limit_gb


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    data: Any
    size_bytes: int
    access_count: int = 0
    last_access_time: float = field(default_factory=time.time)
    creation_time: float = field(default_factory=time.time)

    def touch(self):
        """Update access time and count"""
        self.access_count += 1
        self.last_access_time = time.time()


class MemoryMonitor:
    """Real-time memory monitoring and analysis"""

    def __init__(self, monitoring_interval: float = 1.0):
        self.monitoring_interval = monitoring_interval
        self.monitoring_active = False
        self.monitor_thread = None
        self.callbacks = []
        self.memory_history = []
        self.max_history_size = 1000

    def start_monitoring(self):
        """Start real-time memory monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Memory monitoring started")

    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("Memory monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                stats = self.get_memory_stats()
                self.memory_history.append(stats)

                # Limit history size
                if len(self.memory_history) > self.max_history_size:
                    self.memory_history.pop(0)

                # Check for memory pressure and trigger callbacks
                if stats.is_under_pressure():
                    self._trigger_callbacks(stats)

                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in memory monitoring: {str(e)}")
                time.sleep(self.monitoring_interval)

    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics"""
        # System memory
        memory = psutil.virtual_memory()
        total_memory_gb = memory.total / (1024**3)
        available_memory_gb = memory.available / (1024**3)
        used_memory_gb = memory.used / (1024**3)
        memory_usage_percent = memory.percent

        # Process memory
        process = psutil.Process()
        process_memory = process.memory_info()
        process_memory_gb = process_memory.rss / (1024**3)
        process_memory_percent = (process_memory_gb / total_memory_gb) * 100

        return MemoryStats(
            total_memory_gb=total_memory_gb,
            available_memory_gb=available_memory_gb,
            used_memory_gb=used_memory_gb,
            memory_usage_percent=memory_usage_percent,
            process_memory_gb=process_memory_gb,
            process_memory_percent=process_memory_percent
        )

    def add_callback(self, callback: Callable[[MemoryStats], None]):
        """Add callback for memory pressure events"""
        self.callbacks.append(callback)

    def _trigger_callbacks(self, stats: MemoryStats):
        """Trigger all registered callbacks"""
        for callback in self.callbacks:
            try:
                callback(stats)
            except Exception as e:
                logger.error(f"Error in memory callback: {str(e)}")

    def get_memory_trend(self, window_size: int = 10) -> Dict[str, float]:
        """Analyze memory usage trend"""
        if len(self.memory_history) < window_size:
            return {}

        recent_history = self.memory_history[-window_size:]
        process_memories = [stats.process_memory_gb for stats in recent_history]

        return {
            'trend_slope': np.polyfit(range(len(process_memories)), process_memories, 1)[0],
            'avg_memory': np.mean(process_memories),
            'max_memory': np.max(process_memories),
            'min_memory': np.min(process_memories),
            'memory_volatility': np.std(process_memories)
        }


class IntelligentCache:
    """Intelligent caching system with adaptive eviction policies"""

    def __init__(self, max_size_gb: float = 1.0, eviction_policy: str = "lru"):
        self.max_size_bytes = int(max_size_gb * 1024**3)
        self.current_size_bytes = 0
        self.eviction_policy = eviction_policy
        self.cache = OrderedDict()
        self.cache_stats = defaultdict(int)
        self.access_frequency = defaultdict(int)

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if key not in self.cache:
            self.cache_stats['misses'] += 1
            return None

        entry = self.cache[key]
        entry.touch()
        self.access_frequency[key] += 1

        # Move to end for LRU
        if self.eviction_policy == "lru":
            self.cache.move_to_end(key)

        self.cache_stats['hits'] += 1
        return entry.data

    def put(self, key: str, data: Any) -> bool:
        """Put item in cache"""
        # Calculate data size
        data_size = self._estimate_size(data)

        # Check if single item exceeds cache size
        if data_size > self.max_size_bytes:
            logger.warning(f"Item size {data_size / 1024**2:.2f}MB exceeds cache size")
            return False

        # Evict items if necessary
        while (self.current_size_bytes + data_size > self.max_size_bytes and
               len(self.cache) > 0):
            self._evict_item()

        # Add new item
        entry = CacheEntry(key=key, data=data, size_bytes=data_size)
        self.cache[key] = entry
        self.current_size_bytes += data_size
        self.access_frequency[key] = 1

        self.cache_stats['puts'] += 1
        return True

    def _evict_item(self):
        """Evict item based on policy"""
        if not self.cache:
            return

        if self.eviction_policy == "lru":
            # Remove least recently used
            key, entry = self.cache.popitem(last=False)
        elif self.eviction_policy == "lfu":
            # Remove least frequently used
            key = min(self.access_frequency.keys(), key=lambda k: self.access_frequency[k])
            entry = self.cache.pop(key)
            del self.access_frequency[key]
        else:
            # Default to LRU
            key, entry = self.cache.popitem(last=False)

        self.current_size_bytes -= entry.size_bytes
        self.cache_stats['evictions'] += 1

    def _estimate_size(self, data: Any) -> int:
        """Estimate memory size of data"""
        try:
            if isinstance(data, (pd.DataFrame, pd.Series)):
                return data.memory_usage(deep=True).sum()
            elif isinstance(data, np.ndarray):
                return data.nbytes
            elif isinstance(data, (list, tuple)):
                return len(data) * 8  # Rough estimate
            elif isinstance(data, dict):
                return len(data) * 64  # Rough estimate
            else:
                return 1024  # Default 1KB
        except:
            return 1024

    def clear(self):
        """Clear cache"""
        self.cache.clear()
        self.current_size_bytes = 0
        self.access_frequency.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        hit_rate = (self.cache_stats['hits'] /
                   (self.cache_stats['hits'] + self.cache_stats['misses'])
                   if (self.cache_stats['hits'] + self.cache_stats['misses']) > 0 else 0)

        return {
            'current_size_gb': self.current_size_bytes / (1024**3),
            'max_size_gb': self.max_size_bytes / (1024**3),
            'utilization_percent': (self.current_size_bytes / self.max_size_bytes) * 100,
            'item_count': len(self.cache),
            'hit_rate_percent': hit_rate * 100,
            **self.cache_stats
        }


class AdaptiveMemoryManager:
    """
    Adaptive memory management system for large-scale backtesting

    Dynamically manages memory allocation, caching, and resource optimization
    to handle parameter optimization within 4GB constraints.
    """

    def __init__(self, config=None):
        """Initialize adaptive memory manager"""
        if config is None:
            from ..core.config import DEFAULT_CONFIG
            config = DEFAULT_CONFIG

        self.config = config
        self.memory_limit_gb = config.memory_limit_gb
        self.safety_margin = 0.1  # 10% safety margin
        self.effective_limit_gb = self.memory_limit_gb * (1 - self.safety_margin)

        # Initialize components
        self.monitor = MemoryMonitor()
        self.cache = IntelligentCache(max_size_gb=self.memory_limit_gb * 0.3)
        self.memory_pools = {}
        self.garbage_collection_enabled = True

        # Memory pressure tracking
        self.pressure_events = []
        self.adaptation_history = []

        # Memory leak detection
        self.object_registry = weakref.WeakSet()
        self.allocation_tracker = defaultdict(list)

        logger.info(f"Initialized AdaptiveMemoryManager with limit: {self.memory_limit_gb}GB")

    def start(self):
        """Start memory management"""
        self.monitor.start_monitoring()
        self.monitor.add_callback(self._handle_memory_pressure)
        logger.info("Adaptive memory management started")

    def stop(self):
        """Stop memory management"""
        self.monitor.stop_monitoring()
        self.cache.clear()
        logger.info("Adaptive memory management stopped")

    def _handle_memory_pressure(self, stats: MemoryStats):
        """Handle memory pressure events"""
        if stats.is_process_limit_exceeded(self.effective_limit_gb):
            logger.warning(f"Memory pressure detected: {stats.process_memory_gb:.2f}GB > {self.effective_limit_gb:.2f}GB")
            self.pressure_events.append(time.time())

            # Trigger adaptive measures
            self._apply_adaptive_measures(stats)

    def _apply_adaptive_measures(self, stats: MemoryStats):
        """Apply adaptive memory management measures"""
        measures_applied = []

        try:
            # Measure 1: Aggressive garbage collection
            if self.garbage_collection_enabled:
                collected = self._aggressive_garbage_collection()
                if collected > 0:
                    measures_applied.append(f"GC: {collected:.1f}MB freed")

            # Measure 2: Cache eviction
            cache_cleared = self._evict_cache_aggressively()
            if cache_cleared > 0:
                measures_applied.append(f"Cache: {cache_cleared:.1f}MB cleared")

            # Measure 3: Memory pool cleanup
            pool_cleared = self._cleanup_memory_pools()
            if pool_cleared > 0:
                measures_applied.append(f"Pools: {pool_cleared:.1f}MB cleared")

            # Record adaptation
            self.adaptation_history.append({
                'timestamp': time.time(),
                'memory_gb': stats.process_memory_gb,
                'measures': measures_applied
            })

            logger.info(f"Applied adaptive measures: {', '.join(measures_applied)}")

        except Exception as e:
            logger.error(f"Error applying adaptive measures: {str(e)}")

    def _aggressive_garbage_collection(self) -> float:
        """Perform aggressive garbage collection"""
        initial_memory = self.monitor.get_memory_stats().process_memory_gb

        # Multiple garbage collection passes
        for generation in range(3):
            gc.collect(generation)

        final_memory = self.monitor.get_memory_stats().process_memory_gb
        freed_memory = (initial_memory - final_memory) * 1024  # MB

        return freed_memory

    def _evict_cache_aggressively(self) -> float:
        """Aggressively evict cache items"""
        initial_cache_size = self.cache.current_size_bytes / (1024**2)  # MB

        # Clear most of the cache (keep 10%)
        target_size = self.cache.max_size_bytes * 0.1
        while (self.cache.current_size_bytes > target_size and
               len(self.cache) > 0):
            self.cache._evict_item()

        final_cache_size = self.cache.current_size_bytes / (1024**2)  # MB
        cleared_memory = initial_cache_size - final_cache_size

        return cleared_memory

    def _cleanup_memory_pools(self) -> float:
        """Clean up memory pools"""
        total_cleared = 0

        for pool_name, pool in list(self.memory_pools.items()):
            try:
                if hasattr(pool, 'clear'):
                    pool_size_before = len(pool)
                    pool.clear()
                    total_cleared += pool_size_before
                    logger.debug(f"Cleared memory pool {pool_name}: {pool_size_before} items")
                elif hasattr(pool, '__len__'):
                    pool_size_before = len(pool)
                    self.memory_pools[pool_name] = type(pool)()  # Create new empty pool
                    total_cleared += pool_size_before
            except Exception as e:
                logger.error(f"Error cleaning pool {pool_name}: {str(e)}")

        return total_cleared

    def allocate_memory_pool(self, pool_name: str, pool_type: str = "list") -> Any:
        """Allocate a managed memory pool"""
        if pool_name in self.memory_pools:
            return self.memory_pools[pool_name]

        if pool_type == "list":
            pool = []
        elif pool_type == "dict":
            pool = {}
        elif pool_type == "set":
            pool = set()
        else:
            pool = []

        self.memory_pools[pool_name] = pool
        logger.debug(f"Allocated memory pool {pool_name} of type {pool_type}")
        return pool

    def get_memory_pool(self, pool_name: str) -> Any:
        """Get existing memory pool"""
        return self.memory_pools.get(pool_name)

    def release_memory_pool(self, pool_name: str):
        """Release and clean up memory pool"""
        if pool_name in self.memory_pools:
            pool = self.memory_pools[pool_name]
            try:
                if hasattr(pool, 'clear'):
                    pool.clear()
            except:
                pass
            del self.memory_pools[pool_name]
            logger.debug(f"Released memory pool {pool_name}")

    def register_object(self, obj: Any) -> str:
        """Register object for memory leak detection"""
        object_id = str(id(obj))
        self.object_registry.add(obj)
        return object_id

    def check_memory_leaks(self) -> Dict[str, Any]:
        """Check for potential memory leaks"""
        stats = self.monitor.get_memory_stats()
        memory_trend = self.monitor.get_memory_trend()

        leak_indicators = {
            'current_memory_gb': stats.process_memory_gb,
            'memory_trend_slope': memory_trend.get('trend_slope', 0),
            'memory_volatility': memory_trend.get('memory_volatility', 0),
            'cache_size_gb': self.cache.current_size_bytes / (1024**3),
            'active_pools': len(self.memory_pools),
            'registered_objects': len(self.object_registry),
            'pressure_events_24h': len([t for t in self.pressure_events if time.time() - t < 86400]),
            'adaptations_24h': len([t for t in self.adaptation_history if time.time() - t < 86400])
        }

        # Simple leak detection logic
        leak_indicators['potential_leak'] = (
            memory_trend.get('trend_slope', 0) > 0.01 and  # Increasing memory trend
            stats.process_memory_gb > self.effective_limit_gb * 0.8  # High memory usage
        )

        return leak_indicators

    def optimize_chunk_size(self, current_chunk_size: int, memory_usage: float) -> int:
        """Optimize chunk size based on current memory usage"""
        memory_pressure = memory_usage / self.effective_limit_gb

        if memory_pressure > 0.9:
            # High pressure: reduce chunk size significantly
            new_chunk_size = max(current_chunk_size // 4, 10)
        elif memory_pressure > 0.7:
            # Medium pressure: reduce chunk size moderately
            new_chunk_size = max(current_chunk_size // 2, 50)
        elif memory_pressure < 0.4:
            # Low pressure: can increase chunk size
            new_chunk_size = min(current_chunk_size * 2, 2000)
        else:
            # Normal pressure: keep current size
            new_chunk_size = current_chunk_size

        if new_chunk_size != current_chunk_size:
            logger.info(f"Adjusted chunk size: {current_chunk_size} -> {new_chunk_size} "
                       f"(memory pressure: {memory_pressure:.1%})")

        return new_chunk_size

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory management statistics"""
        memory_stats = self.monitor.get_memory_stats()
        cache_stats = self.cache.get_stats()
        leak_stats = self.check_memory_leaks()

        return {
            'memory_stats': memory_stats.__dict__,
            'cache_stats': cache_stats,
            'leak_detection': leak_stats,
            'memory_pools': {
                'count': len(self.memory_pools),
                'names': list(self.memory_pools.keys())
            },
            'pressure_events': {
                'total': len(self.pressure_events),
                'last_24h': len([t for t in self.pressure_events if time.time() - t < 86400]),
                'last_hour': len([t for t in self.pressure_events if time.time() - t < 3600])
            },
            'adaptations': {
                'total': len(self.adaptation_history),
                'last_24h': len([t for t in self.adaptation_history if time.time() - t < 86400])
            },
            'config': {
                'memory_limit_gb': self.memory_limit_gb,
                'effective_limit_gb': self.effective_limit_gb,
                'safety_margin': self.safety_margin
            }
        }


# Decorator for memory-aware function execution
def memory_managed(manager: AdaptiveMemoryManager):
    """Decorator for memory-aware function execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check memory before execution
            stats = manager.monitor.get_memory_stats()
            if stats.is_process_limit_exceeded(manager.effective_limit_gb):
                logger.warning("High memory usage before function execution")
                manager._apply_adaptive_measures(stats)

            # Execute function
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Clean up after execution
                if manager.garbage_collection_enabled:
                    gc.collect()

        return wrapper
    return decorator
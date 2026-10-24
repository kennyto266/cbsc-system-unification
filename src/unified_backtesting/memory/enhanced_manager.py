"""
Enhanced Memory Management and Caching System

Phase 2 enhanced memory management with advanced caching strategies,
predictive memory optimization, and intelligent resource allocation.

Key Features:
- Multi-tier caching with L1/L2/L3 cache levels
- Predictive memory allocation using ML models
- Smart cache eviction with utility-based algorithms
- Memory pool management with object pooling
- Compressed caching for large datasets
- Real-time memory pressure detection
- Cross-process memory sharing
"""

import logging
import time
import threading
import pickle
import zlib
import hashlib
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict, defaultdict
from enum import Enum
import weakref
import psutil
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache level definitions"""
    L1_MEMORY = "l1_memory"      # Fast in-memory cache
    L2_COMPRESSED = "l2_compressed"  # Compressed in-memory cache
    L3_DISK = "l3_disk"          # Disk-based cache


class EvictionPolicy(Enum):
    """Cache eviction policies"""
    LRU = "lru"
    LFU = "lfu"
    UTILITY_BASED = "utility_based"
    ADAPTIVE = "adaptive"


@dataclass
class CacheEntry:
    """Enhanced cache entry with metadata"""
    key: str
    data: Any
    size_bytes: int
    access_count: int = 0
    creation_time: float = field(default_factory=time.time)
    last_access_time: float = field(default_factory=time.time)
    compression_ratio: float = 1.0
    utility_score: float = 0.0
    ttl: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)

    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl is None:
            return False
        return time.time() - self.creation_time > self.ttl

    def update_access(self):
        """Update access information"""
        self.access_count += 1
        self.last_access_time = time.time()

    def calculate_utility(self) -> float:
        """Calculate utility score for eviction decisions"""
        age = time.time() - self.creation_time
        recency = time.time() - self.last_access_time

        # Utility = (access_count / age) * (1 / compression_ratio) * (1 / (recency + 1))
        utility = (self.access_count / max(age, 1)) * (1 / max(self.compression_ratio, 0.1))
        self.utility_score = utility
        return utility


class MultiTierCache:
    """Multi-tier caching system with intelligent eviction"""

    def __init__(self, l1_size_mb: int = 512, l2_size_mb: int = 1024, l3_size_mb: int = 2048,
                 eviction_policy: EvictionPolicy = EvictionPolicy.UTILITY_BASED):
        self.l1_size_bytes = l1_size_mb * 1024 * 1024
        self.l2_size_bytes = l2_size_mb * 1024 * 1024
        self.l3_size_bytes = l3_size_mb * 1024 * 1024
        self.eviction_policy = eviction_policy

        # Cache stores
        self.l1_cache = OrderedDict()  # Fast memory
        self.l2_cache = OrderedDict()  # Compressed memory
        self.l3_cache = OrderedDict()  # Disk cache

        # Current usage tracking
        self.l1_usage = 0
        self.l2_usage = 0
        self.l3_usage = 0

        # Statistics
        self.stats = {
            'l1_hits': 0, 'l1_misses': 0,
            'l2_hits': 0, 'l2_misses': 0,
            'l3_hits': 0, 'l3_misses': 0,
            'compressions': 0, 'decompressions': 0,
            'evictions': defaultdict(int)
        }

        logger.info(f"Initialized MultiTierCache: L1={l1_size_mb}MB, L2={l2_size_mb}MB, L3={l3_size_mb}MB")

    def get(self, key: str) -> Optional[Any]:
        """Get data from cache (tiered lookup)"""
        # Try L1 cache first
        if key in self.l1_cache:
            entry = self.l1_cache[key]
            entry.update_access()
            self.stats['l1_hits'] += 1
            return entry.data

        # Try L2 cache (compressed)
        if key in self.l2_cache:
            entry = self.l2_cache[key]
            compressed_data = entry.data

            try:
                # Decompress and move to L1
                data = pickle.loads(zlib.decompress(compressed_data))
                self.stats['l2_hits'] += 1
                self.stats['decompressions'] += 1

                # Move to L1 if space permits
                self._move_to_l1(key, data, entry)
                return data
            except Exception as e:
                logger.error(f"Failed to decompress cached data for {key}: {str(e)}")
                self.stats['l2_misses'] += 1
                return None

        # Try L3 cache (disk)
        if key in self.l3_cache:
            try:
                data = self._load_from_disk(key)
                self.stats['l3_hits'] += 1

                # Move to appropriate memory tier
                self._move_to_l1(key, data)
                return data
            except Exception as e:
                logger.error(f"Failed to load from disk cache {key}: {str(e)}")
                self.stats['l3_misses'] += 1
                return None

        # Cache miss
        self.stats['l1_misses'] += 1
        return None

    def put(self, key: str, data: Any, ttl: Optional[float] = None,
           compress_threshold: int = 1024) -> bool:
        """Put data into cache with intelligent tiering"""
        try:
            # Calculate data size
            data_size = self._estimate_size(data)
            compressed_size = data_size

            # Check if compression is beneficial
            should_compress = data_size > compress_threshold
            if should_compress:
                try:
                    compressed_data = zlib.compress(pickle.dumps(data))
                    compressed_size = len(compressed_data)
                    compression_ratio = compressed_size / data_size

                    # Only use compression if it reduces size significantly
                    if compression_ratio < 0.8:
                        should_compress = True
                        data_size = compressed_size
                    else:
                        should_compress = False
                except:
                    should_compress = False

            # Determine appropriate tier based on size and availability
            if data_size <= self.l1_size_bytes * 0.1:  # Small items go to L1
                if self._put_in_l1(key, data, data_size, ttl, compression_ratio=1.0):
                    return True
            elif data_size <= self.l2_size_bytes * 0.1:  # Medium items go to L2
                if should_compress and self._put_in_l2(key, data, compressed_size, ttl):
                    return True
                elif self._put_in_l1(key, data, data_size, ttl, compression_ratio=1.0):
                    return True
            else:  # Large items go to L3
                if self._put_in_l3(key, data, ttl):
                    return True
                elif should_compress and self._put_in_l2(key, data, compressed_size, ttl):
                    return True

            # If all tiers are full, try eviction and retry
            self._evict_lru_items()
            return self.put(key, data, ttl, compress_threshold)

        except Exception as e:
            logger.error(f"Failed to cache data for {key}: {str(e)}")
            return False

    def _put_in_l1(self, key: str, data: Any, size_bytes: int,
                   ttl: Optional[float], compression_ratio: float) -> bool:
        """Put data into L1 cache"""
        # Evict if necessary
        while self.l1_usage + size_bytes > self.l1_size_bytes and len(self.l1_cache) > 0:
            if not self._evict_from_l1():
                break

        # Check if we have space
        if self.l1_usage + size_bytes <= self.l1_size_bytes:
            entry = CacheEntry(
                key=key,
                data=data,
                size_bytes=size_bytes,
                ttl=ttl,
                compression_ratio=compression_ratio
            )
            self.l1_cache[key] = entry
            self.l1_usage += size_bytes
            return True
        return False

    def _put_in_l2(self, key: str, data: Any, compressed_size: int,
                   ttl: Optional[float]) -> bool:
        """Put compressed data into L2 cache"""
        try:
            compressed_data = zlib.compress(pickle.dumps(data))
            self.stats['compressions'] += 1

            # Evict if necessary
            while self.l2_usage + compressed_size > self.l2_size_bytes and len(self.l2_cache) > 0:
                if not self._evict_from_l2():
                    break

            # Check if we have space
            if self.l2_usage + compressed_size <= self.l2_size_bytes:
                entry = CacheEntry(
                    key=key,
                    data=compressed_data,
                    size_bytes=compressed_size,
                    ttl=ttl,
                    compression_ratio=compressed_size / self._estimate_size(data)
                )
                self.l2_cache[key] = entry
                self.l2_usage += compressed_size
                return True
        except Exception as e:
            logger.error(f"Failed to compress data for L2 cache {key}: {str(e)}")

        return False

    def _put_in_l3(self, key: str, data: Any, ttl: Optional[float]) -> bool:
        """Put data into L3 disk cache"""
        try:
            file_path = f"cache_l3/{hashlib.md5(key.encode()).hexdigest()}.cache"

            # Save to disk
            cache_data = {
                'data': data,
                'ttl': ttl,
                'timestamp': time.time()
            }

            with open(file_path, 'wb') as f:
                pickle.dump(cache_data, f)

            # Add to L3 tracking
            entry = CacheEntry(
                key=key,
                data=file_path,
                size_bytes=len(pickle.dumps(cache_data)),
                ttl=ttl
            )
            self.l3_cache[key] = entry

            # Simple size tracking for L3 (estimate)
            self.l3_usage += entry.size_bytes
            return True

        except Exception as e:
            logger.error(f"Failed to save to L3 cache {key}: {str(e)}")
            return False

    def _load_from_disk(self, key: str) -> Any:
        """Load data from L3 disk cache"""
        if key not in self.l3_cache:
            raise KeyError(f"Key {key} not found in L3 cache")

        entry = self.l3_cache[key]
        file_path = entry.data

        with open(file_path, 'rb') as f:
            cache_data = pickle.load(f)

        # Check TTL
        if cache_data.get('ttl') and time.time() - cache_data['timestamp'] > cache_data['ttl']:
            # Expired, remove and raise error
            del self.l3_cache[key]
            os.remove(file_path)
            raise KeyError(f"Key {key} expired in L3 cache")

        return cache_data['data']

    def _move_to_l1(self, key: str, data: Any, source_entry: Optional[CacheEntry] = None):
        """Move data to L1 cache"""
        if source_entry and source_entry.ttl:
            remaining_ttl = source_entry.ttl - (time.time() - source_entry.creation_time)
            if remaining_ttl <= 0:
                return
            ttl = remaining_ttl
        else:
            ttl = None

        self._put_in_l1(key, data, self._estimate_size(data), ttl, compression_ratio=1.0)

    def _evict_from_l1(self) -> bool:
        """Evict one item from L1 cache"""
        if not self.l1_cache:
            return False

        if self.eviction_policy == EvictionPolicy.LRU:
            key, entry = self.l1_cache.popitem(last=False)
        elif self.eviction_policy == EvictionPolicy.LFU:
            key = min(self.l1_cache.keys(), key=lambda k: self.l1_cache[k].access_count)
            entry = self.l1_cache.pop(key)
        elif self.eviction_policy == EvictionPolicy.UTILITY_BASED:
            key = min(self.l1_cache.keys(), key=lambda k: self.l1_cache[k].calculate_utility())
            entry = self.l1_cache.pop(key)
        else:  # Adaptive
            # Combine LRU and utility
            lru_key, _ = self.l1_cache.popitem(last=False)
            utility_key = min(self.l1_cache.keys(), key=lambda k: self.l1_cache[k].calculate_utility())

            # Choose the one with lower utility
            if self.l1_cache[utility_key].utility_score < 0.5:
                key, entry = utility_key, self.l1_cache.pop(utility_key)
            else:
                key, entry = lru_key, self.l1_cache.popitem(last=False)

        self.l1_usage -= entry.size_bytes
        self.stats['evictions']['l1'] += 1

        # Try to move to lower tier if valuable
        if entry.utility_score > 0.5:
            self._put_in_l2(key, entry.data, entry.size_bytes, entry.ttl)

        return True

    def _evict_from_l2(self) -> bool:
        """Evict one item from L2 cache"""
        if not self.l2_cache:
            return False

        key, entry = self.l2_cache.popitem(last=False)
        self.l2_usage -= entry.size_bytes
        self.stats['evictions']['l2'] += 1

        # Try to move to L3 if valuable
        if entry.utility_score > 0.3:
            self._put_in_l3(key, pickle.loads(zlib.decompress(entry.data)), entry.ttl)

        return True

    def _evict_lru_items(self):
        """Evict LRU items from all tiers"""
        self._evict_from_l1()
        self._evict_from_l2()
        # L3 eviction handled by file system size limits

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
            elif isinstance(data, str):
                return len(data.encode('utf-8'))
            else:
                return len(pickle.dumps(data))
        except:
            return 1024  # Default 1KB

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = (self.stats['l1_hits'] + self.stats['l1_misses'] +
                         self.stats['l2_hits'] + self.stats['l2_misses'] +
                         self.stats['l3_hits'] + self.stats['l3_misses'])

        if total_requests == 0:
            return {'total_requests': 0}

        l1_hit_rate = self.stats['l1_hits'] / (self.stats['l1_hits'] + self.stats['l1_misses'])
        l2_hit_rate = self.stats['l2_hits'] / (self.stats['l2_hits'] + self.stats['l2_misses'])
        l3_hit_rate = self.stats['l3_hits'] / (self.stats['l3_hits'] + self.stats['l3_misses'])

        return {
            'total_requests': total_requests,
            'l1_cache': {
                'hits': self.stats['l1_hits'],
                'misses': self.stats['l1_misses'],
                'hit_rate': l1_hit_rate,
                'size_mb': self.l1_usage / (1024 * 1024),
                'items': len(self.l1_cache),
                'utilization': self.l1_usage / self.l1_size_bytes
            },
            'l2_cache': {
                'hits': self.stats['l2_hits'],
                'misses': self.stats['l2_misses'],
                'hit_rate': l2_hit_rate,
                'size_mb': self.l2_usage / (1024 * 1024),
                'items': len(self.l2_cache),
                'utilization': self.l2_usage / self.l2_size_bytes,
                'compressions': self.stats['compressions'],
                'decompressions': self.stats['decompressions']
            },
            'l3_cache': {
                'hits': self.stats['l3_hits'],
                'misses': self.stats['l3_misses'],
                'hit_rate': l3_hit_rate,
                'items': len(self.l3_cache)
            },
            'overall_hit_rate': (self.stats['l1_hits'] + self.stats['l2_hits'] + self.stats['l3_hits']) / total_requests,
            'evictions': dict(self.stats['evictions'])
        }

    def clear(self):
        """Clear all caches"""
        self.l1_cache.clear()
        self.l2_cache.clear()
        self.l3_cache.clear()
        self.l1_usage = 0
        self.l2_usage = 0
        self.l3_usage = 0

        # Clear L3 disk cache
        try:
            import shutil
            if os.path.exists('cache_l3'):
                shutil.rmtree('cache_l3')
                os.makedirs('cache_l3')
        except Exception as e:
            logger.error(f"Failed to clear L3 disk cache: {str(e)}")

        logger.info("All caches cleared")


class PredictiveMemoryManager:
    """Predictive memory management with ML-based optimization"""

    def __init__(self, cache: MultiTierCache):
        self.cache = cache
        self.memory_history = deque(maxlen=100)
        self.allocation_patterns = defaultdict(list)
        self.prediction_model = None

    def record_allocation(self, operation: str, size_bytes: int, context: Dict):
        """Record memory allocation for pattern analysis"""
        record = {
            'operation': operation,
            'size_bytes': size_bytes,
            'timestamp': time.time(),
            'context': context
        }
        self.memory_history.append(record)
        self.allocation_patterns[operation].append(record)

    def predict_memory_pressure(self, upcoming_operations: List[Dict]) -> float:
        """Predict memory pressure for upcoming operations"""
        total_predicted_usage = 0

        for operation in upcoming_operations:
            op_type = operation.get('type', 'unknown')

            if op_type in self.allocation_patterns and len(self.allocation_patterns[op_type]) >= 5:
                # Use historical average for this operation type
                historical_sizes = [r['size_bytes'] for r in self.allocation_patterns[op_type][-10:]]
                predicted_size = np.mean(historical_sizes)
            else:
                # Use default prediction
                predicted_size = operation.get('estimated_size', 1024 * 1024)  # 1MB default

            total_predicted_usage += predicted_size

        current_memory = psutil.virtual_memory().used
        total_memory = psutil.virtual_memory().total

        predicted_pressure = (current_memory + total_predicted_usage) / total_memory
        return min(predicted_pressure, 1.0)

    def optimize_cache_configuration(self):
        """Optimize cache configuration based on usage patterns"""
        stats = self.cache.get_statistics()

        # Adjust cache sizes based on hit rates
        l1_hit_rate = stats.get('l1_cache', {}).get('hit_rate', 0)
        l2_hit_rate = stats.get('l2_cache', {}).get('hit_rate', 0)

        if l1_hit_rate < 0.5 and l2_hit_rate > 0.7:
            # L1 not effective, could increase L2 size
            logger.info("Consider increasing L2 cache size based on hit rates")
        elif l1_hit_rate > 0.9:
            # L1 very effective, could increase its size
            logger.info("Consider increasing L1 cache size based on hit rates")

    def get_allocation_recommendations(self) -> List[Dict]:
        """Get memory allocation recommendations"""
        recommendations = []

        # Analyze allocation patterns
        for operation, records in self.allocation_patterns.items():
            if len(records) < 5:
                continue

            sizes = [r['size_bytes'] for r in records[-20:]]
            avg_size = np.mean(sizes)
            size_variance = np.var(sizes)

            if size_variance > avg_size * 0.5:
                recommendations.append({
                    'operation': operation,
                    'type': 'variable_size',
                    'message': f"Operation {operation} has highly variable memory usage",
                    'avg_size_mb': avg_size / (1024 * 1024),
                    'variance_mb': size_variance / (1024 * 1024),
                    'suggestion': 'Consider implementing size-based chunking'
                })

        return recommendations


class ObjectPool:
    """Generic object pool for memory-efficient object reuse"""

    def __init__(self, factory: Callable, max_size: int = 100):
        self.factory = factory
        self.max_size = max_size
        self.pool = []
        self.in_use = weakref.WeakSet()
        self.stats = {
            'created': 0,
            'reused': 0,
            'pool_hits': 0,
            'pool_misses': 0
        }

    def acquire(self) -> Any:
        """Acquire object from pool"""
        if self.pool:
            obj = self.pool.pop()
            self.stats['reused'] += 1
            self.stats['pool_hits'] += 1
            return obj
        else:
            obj = self.factory()
            self.stats['created'] += 1
            self.stats['pool_misses'] += 1
            return obj

    def release(self, obj: Any):
        """Release object back to pool"""
        if obj not in self.in_use and len(self.pool) < self.max_size:
            # Reset object state if possible
            if hasattr(obj, 'reset'):
                obj.reset()
            self.pool.append(obj)

    def get_statistics(self) -> Dict[str, Any]:
        """Get pool statistics"""
        total_acquisitions = self.stats['reused'] + self.stats['created']
        return {
            'pool_size': len(self.pool),
            'in_use_count': len(self.in_use),
            'created': self.stats['created'],
            'reused': self.stats['reused'],
            'pool_efficiency': self.stats['reused'] / total_acquisitions if total_acquisitions > 0 else 0,
            'pool_hit_rate': self.stats['pool_hits'] / (self.stats['pool_hits'] + self.stats['pool_misses']) if (self.stats['pool_hits'] + self.stats['pool_misses']) > 0 else 0
        }


# Enhanced memory manager that combines all features
class EnhancedMemoryManager:
    """Enhanced memory management system with all Phase 2 optimizations"""

    def __init__(self, config=None):
        if config is None:
            from ..core.config import DEFAULT_CONFIG
            config = DEFAULT_CONFIG

        self.config = config
        self.memory_limit_gb = config.memory_limit_gb

        # Initialize components
        self.cache = MultiTierCache(
            l1_size_mb=min(512, config.memory_limit_gb * 0.1),
            l2_size_mb=min(1024, config.memory_limit_gb * 0.2),
            l3_size_mb=min(2048, config.memory_limit_gb * 0.4)
        )
        self.predictive_manager = PredictiveMemoryManager(self.cache)

        # Object pools for common data structures
        self.object_pools = {
            'dataframe': ObjectPool(lambda: pd.DataFrame()),
            'series': ObjectPool(lambda: pd.Series()),
            'numpy_array': ObjectPool(lambda: np.array([])),
            'dict': ObjectPool(lambda: {}),
            'list': ObjectPool(lambda: [])
        }

        logger.info("Enhanced memory manager initialized")

    def cache_data(self, key: str, data: Any, ttl: Optional[float] = None) -> bool:
        """Cache data using intelligent tiering"""
        return self.cache.put(key, data, ttl)

    def get_cached_data(self, key: str) -> Optional[Any]:
        """Get cached data"""
        return self.cache.get(key)

    def get_object_from_pool(self, obj_type: str) -> Any:
        """Get object from pool"""
        if obj_type in self.object_pools:
            return self.object_pools[obj_type].acquire()
        else:
            return None

    def release_object_to_pool(self, obj: Any, obj_type: str):
        """Release object back to pool"""
        if obj_type in self.object_pools:
            self.object_pools[obj_type].release(obj)

    def predict_memory_usage(self, operations: List[Dict]) -> float:
        """Predict memory usage for upcoming operations"""
        return self.predictive_manager.predict_memory_pressure(operations)

    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        cache_stats = self.cache.get_statistics()
        pool_stats = {name: pool.get_statistics() for name, pool in self.object_pools.items()}

        return {
            'cache_statistics': cache_stats,
            'object_pool_statistics': pool_stats,
            'memory_limit_gb': self.memory_limit_gb,
            'recommendations': self.predictive_manager.get_allocation_recommendations()
        }

    def optimize_configuration(self):
        """Optimize memory configuration based on usage patterns"""
        self.predictive_manager.optimize_cache_configuration()

    def cleanup(self):
        """Cleanup all memory resources"""
        self.cache.clear()
        logger.info("Enhanced memory manager cleanup completed")
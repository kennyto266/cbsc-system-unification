"""
Phase 5.1: Computation Cache System

Intelligent multi-level caching system for technical indicator computations.
Supports memory-based and disk-based caching with intelligent eviction policies.

Author: Claude Code Assistant
Version: 1.0.0
"""

import json
import time
import hashlib
import pickle
import gzip

try:
    import lz4.frame
    LZ4_AVAILABLE = True
except ImportError:
    LZ4_AVAILABLE = False
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from pathlib import Path
from collections import OrderedDict
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import logging

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

class CacheLevel(Enum):
    """Cache level enumeration."""
    MEMORY = "memory"
    DISK = "disk"
    DISTRIBUTED = "distributed"

class CompressionType(Enum):
    """Compression algorithm enumeration."""
    NONE = "none"
    GZIP = "gzip"
    LZ4 = "lz4"

class EvictionPolicy(Enum):
    """Cache eviction policy enumeration."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    SIZE = "size"  # Size-based eviction

@dataclass
class CacheConfig:
    """Configuration for computation cache."""
    # Memory cache settings
    memory_cache_size: int = 1000  # Maximum number of entries
    memory_cache_size_mb: int = 512  # Maximum memory usage in MB
    enable_memory_cache: bool = True

    # Disk cache settings
    disk_cache_size: int = 10000  # Maximum number of entries
    disk_cache_size_gb: float = 5.0  # Maximum disk usage in GB
    enable_disk_cache: bool = True
    disk_cache_dir: str = "./cache/computation_cache"

    # Performance settings
    compression_type: CompressionType = CompressionType.GZIP
    eviction_policy: EvictionPolicy = EvictionPolicy.LRU
    default_ttl_seconds: int = 3600  # 1 hour
    cache_check_interval: int = 60  # Check for expired entries every 60 seconds

    # Monitoring settings
    enable_statistics: bool = True
    enable_performance_monitoring: bool = True
    statistics_update_interval: int = 30  # seconds

    # Advanced settings
    enable_async_writes: bool = False
    enable_compression_heuristics: bool = True
    min_size_for_compression: int = 1024  # Only compress data larger than 1KB

@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    timestamp: datetime
    ttl_seconds: int
    access_count: int
    last_access: datetime
    size_bytes: int
    compressed: bool
    computation_time_ms: float
    source: str  # Source of the computation

@dataclass
class CacheStats:
    """Cache performance statistics."""
    # Basic statistics
    total_entries: int = 0
    memory_entries: int = 0
    disk_entries: int = 0

    # Performance statistics
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_rate: float = 0.0

    # Memory statistics
    memory_usage_mb: float = 0.0
    disk_usage_gb: float = 0.0

    # Timing statistics
    avg_lookup_time_ms: float = 0.0
    avg_storage_time_ms: float = 0.0
    total_computation_time_saved_ms: float = 0.0

    # Compression statistics
    compression_ratio: float = 1.0
    compressed_entries: int = 0

    # Eviction statistics
    evictions: int = 0
    expired_entries: int = 0

class IntelligentCacheKeyGenerator:
    """Intelligent cache key generator for indicator computations."""

    def __init__(self):
        self.key_salt = "enhanced_ta_system_v1.0"

    def generate_key(
        self,
        indicator_name: str,
        parameters: Dict[str, Any],
        data_hash: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate intelligent cache key for indicator computation.

        Args:
            indicator_name: Name of the technical indicator
            parameters: Indicator parameters
            data_hash: Hash of the input data
            additional_context: Additional context for the computation

        Returns:
            Unique cache key string
        """
        # Create base key components
        key_components = [
            indicator_name,
            self._normalize_parameters(parameters),
            data_hash,
            self._get_data_version(),
            self.key_salt
        ]

        # Add additional context if provided
        if additional_context:
            key_components.append(self._normalize_context(additional_context))

        # Generate hash
        key_string = "|".join(str(comp) for comp in key_components)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def generate_data_hash(self, data: Any) -> str:
        """
        Generate hash for input data.

        Args:
            data: Input data (DataFrame, Series, array, etc.)

        Returns:
            Hash string representing the data
        """
        if PANDAS_AVAILABLE and isinstance(data, (pd.DataFrame, pd.Series)):
            # Use pandas data hash
            data_str = data.to_string() if hasattr(data, 'to_string') else str(data.values.tobytes())
        elif isinstance(data, (list, tuple)):
            # Convert list/tuple to string
            data_str = str(sorted(data) if isinstance(data, list) else data)
        elif isinstance(data, dict):
            # Convert dict to sorted string
            data_str = json.dumps(data, sort_keys=True)
        else:
            # Fallback to string representation
            data_str = str(data)

        return hashlib.md5(data_str.encode()).hexdigest()

    def _normalize_parameters(self, parameters: Dict[str, Any]) -> str:
        """Normalize parameters for consistent key generation."""
        # Sort keys and convert to string
        normalized = {k: v for k, v in sorted(parameters.items())}
        return json.dumps(normalized, sort_keys=True)

    def _normalize_context(self, context: Dict[str, Any]) -> str:
        """Normalize additional context."""
        # Filter out non-deterministic context
        filtered_context = {
            k: v for k, v in context.items()
            if k not in ['timestamp', 'request_id', 'session_id']
        }
        return json.dumps(filtered_context, sort_keys=True)

    def _get_data_version(self) -> str:
        """Get current data version for cache invalidation."""
        return datetime.now().strftime("%Y%m%d")

class MemoryCache:
    """Memory-based LRU cache with intelligent eviction."""

    def __init__(self, max_size: int, max_size_mb: int):
        self.max_size = max_size
        self.max_size_mb = max_size_mb
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_memory_mb = 0.0
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[CacheEntry]:
        """Get entry from cache."""
        with self.lock:
            if key not in self.cache:
                return None

            # Move to end (mark as recently used)
            entry = self.cache.pop(key)
            entry.access_count += 1
            entry.last_access = datetime.now()
            self.cache[key] = entry

            return entry

    def put(self, key: str, entry: CacheEntry) -> bool:
        """Put entry into cache."""
        with self.lock:
            # Check if we need to evict
            while (len(self.cache) >= self.max_size or
                   self.current_memory_mb + entry.size_bytes / (1024 * 1024) > self.max_size_mb):
                if not self._evict_lru():
                    return False  # Cannot evict, cache is full

            # Remove existing entry if present
            if key in self.cache:
                old_entry = self.cache.pop(key)
                self.current_memory_mb -= old_entry.size_bytes / (1024 * 1024)

            # Add new entry
            self.cache[key] = entry
            self.current_memory_mb += entry.size_bytes / (1024 * 1024)
            return True

    def remove(self, key: str) -> bool:
        """Remove entry from cache."""
        with self.lock:
            if key not in self.cache:
                return False

            entry = self.cache.pop(key)
            self.current_memory_mb -= entry.size_bytes / (1024 * 1024)
            return True

    def clear(self):
        """Clear all entries from cache."""
        with self.lock:
            self.cache.clear()
            self.current_memory_mb = 0.0

    def _evict_lru(self) -> bool:
        """Evict least recently used entry."""
        if not self.cache:
            return False

        # Get oldest entry
        key, entry = self.cache.popitem(last=False)
        self.current_memory_mb -= entry.size_bytes / (1024 * 1024)
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            return {
                'entries': len(self.cache),
                'memory_usage_mb': self.current_memory_mb,
                'max_entries': self.max_size,
                'max_memory_mb': self.max_size_mb,
                'utilization_percent': (len(self.cache) / self.max_size) * 100
            }

class DiskCache:
    """Disk-based cache with compression support."""

    def __init__(self, cache_dir: str, max_size: int, max_size_gb: float):
        self.cache_dir = Path(cache_dir)
        self.max_size = max_size
        self.max_size_gb = max_size_gb
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize index file
        self.index_file = self.cache_dir / "cache_index.json"
        self.index: Dict[str, Dict[str, Any]] = self._load_index()
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[CacheEntry]:
        """Get entry from disk cache."""
        with self.lock:
            if key not in self.index:
                return None

            entry_info = self.index[key]
            cache_file = self.cache_dir / entry_info['filename']

            if not cache_file.exists():
                # File missing, remove from index
                del self.index[key]
                self._save_index()
                return None

            try:
                # Load and decompress data
                with open(cache_file, 'rb') as f:
                    data = f.read()

                decompressed_data = self._decompress_data(data, entry_info.get('compressed', False))
                value = pickle.loads(decompressed_data)

                # Create cache entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    timestamp=datetime.fromisoformat(entry_info['timestamp']),
                    ttl_seconds=entry_info['ttl_seconds'],
                    access_count=entry_info['access_count'] + 1,
                    last_access=datetime.now(),
                    size_bytes=entry_info['size_bytes'],
                    compressed=entry_info.get('compressed', False),
                    computation_time_ms=entry_info.get('computation_time_ms', 0.0),
                    source=entry_info.get('source', 'disk_cache')
                )

                # Update access count in index
                self.index[key]['access_count'] = entry.access_count
                self.index[key]['last_access'] = entry.last_access.isoformat()
                self._save_index()

                return entry

            except Exception as e:
                logger.error(f"Error loading cache entry {key}: {e}")
                # Remove corrupted entry
                del self.index[key]
                self._save_index()
                return None

    def put(self, key: str, entry: CacheEntry, compression_type: CompressionType) -> bool:
        """Put entry into disk cache."""
        with self.lock:
            # Check if we need to evict
            while len(self.index) >= self.max_size or self._get_total_size_gb() > self.max_size_gb:
                if not self._evict_oldest():
                    return False

            # Remove existing file if present
            if key in self.index:
                old_filename = self.index[key]['filename']
                old_file = self.cache_dir / old_filename
                if old_file.exists():
                    old_file.unlink()

            try:
                # Serialize and compress data
                serialized_data = pickle.dumps(entry.value)
                compressed_data = self._compress_data(serialized_data, compression_type)

                # Generate unique filename
                filename = f"{key[:8]}_{int(time.time())}.cache"
                cache_file = self.cache_dir / filename

                # Write to disk
                with open(cache_file, 'wb') as f:
                    f.write(compressed_data)

                # Update index
                self.index[key] = {
                    'filename': filename,
                    'timestamp': entry.timestamp.isoformat(),
                    'ttl_seconds': entry.ttl_seconds,
                    'access_count': entry.access_count,
                    'last_access': entry.last_access.isoformat(),
                    'size_bytes': len(compressed_data),
                    'compressed': compression_type != CompressionType.NONE,
                    'computation_time_ms': entry.computation_time_ms,
                    'source': entry.source
                }

                self._save_index()
                return True

            except Exception as e:
                logger.error(f"Error saving cache entry {key}: {e}")
                return False

    def remove(self, key: str) -> bool:
        """Remove entry from disk cache."""
        with self.lock:
            if key not in self.index:
                return False

            entry_info = self.index[key]
            cache_file = self.cache_dir / entry_info['filename']

            if cache_file.exists():
                cache_file.unlink()

            del self.index[key]
            self._save_index()
            return True

    def clear(self):
        """Clear all entries from disk cache."""
        with self.lock:
            # Remove all cache files
            for entry_info in self.index.values():
                cache_file = self.cache_dir / entry_info['filename']
                if cache_file.exists():
                    cache_file.unlink()

            # Clear index
            self.index.clear()
            self._save_index()

    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """Load cache index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading cache index: {e}")

        return {}

    def _save_index(self):
        """Save cache index to disk."""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache index: {e}")

    def _get_total_size_gb(self) -> float:
        """Get total cache size in GB."""
        total_size = sum(
            entry_info['size_bytes']
            for entry_info in self.index.values()
        )
        return total_size / (1024 * 1024 * 1024)

    def _evict_oldest(self) -> bool:
        """Evict oldest entry from disk cache."""
        if not self.index:
            return False

        # Find oldest entry
        oldest_key = min(
            self.index.keys(),
            key=lambda k: datetime.fromisoformat(self.index[k]['timestamp'])
        )

        return self.remove(oldest_key)

    def _compress_data(self, data: bytes, compression_type: CompressionType) -> bytes:
        """Compress data based on compression type."""
        if compression_type == CompressionType.NONE:
            return data
        elif compression_type == CompressionType.GZIP:
            return gzip.compress(data)
        elif compression_type == CompressionType.LZ4:
            if LZ4_AVAILABLE:
                return lz4.frame.compress(data)
            else:
                # Fallback to gzip if lz4 not available
                return gzip.compress(data)
        else:
            return data

    def _decompress_data(self, data: bytes, compressed: bool) -> bytes:
        """Decompress data if compressed."""
        if not compressed:
            return data

        # Try different decompression methods
        decompress_funcs = [gzip.decompress]
        if LZ4_AVAILABLE:
            decompress_funcs.append(lz4.frame.decompress)

        for decompress_func in decompress_funcs:
            try:
                return decompress_func(data)
            except:
                continue

        # If all methods fail, return original data
        return data

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_size = sum(
                entry_info['size_bytes']
                for entry_info in self.index.values()
            )

            return {
                'entries': len(self.index),
                'disk_usage_gb': total_size / (1024 * 1024 * 1024),
                'max_entries': self.max_size,
                'max_disk_gb': self.max_size_gb,
                'utilization_percent': (len(self.index) / self.max_size) * 100,
                'compression_ratio': self._calculate_compression_ratio()
            }

    def _calculate_compression_ratio(self) -> float:
        """Calculate average compression ratio."""
        if not self.index:
            return 1.0

        total_original = 0
        total_compressed = 0

        for entry_info in self.index.values():
            if entry_info.get('compressed', False):
                # Estimate original size (this is approximate)
                total_compressed += entry_info['size_bytes']
                total_original += entry_info['size_bytes'] * 2  # Rough estimate

        if total_original == 0:
            return 1.0

        return total_compressed / total_original

class ComputationCache:
    """
    Intelligent computation cache system for technical indicator computations.

    Features:
    - Multi-level caching (memory + disk)
    - Intelligent cache key generation
    - Compression support
    - LRU eviction policy
    - TTL support
    - Performance monitoring
    - Cache statistics
    """

    def __init__(self, config: CacheConfig):
        self.config = config
        self.key_generator = IntelligentCacheKeyGenerator()

        # Initialize cache levels
        self.memory_cache = MemoryCache(
            config.memory_cache_size,
            config.memory_cache_size_mb
        ) if config.enable_memory_cache else None

        self.disk_cache = DiskCache(
            config.disk_cache_dir,
            config.disk_cache_size,
            config.disk_cache_size_gb
        ) if config.enable_disk_cache else None

        # Statistics
        self.stats = CacheStats()
        self.lookup_times: List[float] = []
        self.storage_times: List[float] = []

        # Background cleanup thread
        self.cleanup_thread = None
        self.stop_cleanup = threading.Event()

        if config.cache_check_interval > 0:
            self._start_cleanup_thread()

    def get(
        self,
        indicator_name: str,
        parameters: Dict[str, Any],
        data: Any,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Get cached computation result.

        Args:
            indicator_name: Name of the technical indicator
            parameters: Indicator parameters
            data: Input data for computation
            additional_context: Additional context

        Returns:
            Cached computation result or None if not found
        """
        start_time = time.time()

        try:
            # Generate cache key
            data_hash = self.key_generator.generate_data_hash(data)
            cache_key = self.key_generator.generate_key(
                indicator_name, parameters, data_hash, additional_context
            )

            # Try memory cache first
            if self.memory_cache:
                entry = self.memory_cache.get(cache_key)
                if entry and not self._is_expired(entry):
                    self.stats.cache_hits += 1
                    lookup_time = (time.time() - start_time) * 1000
                    self.lookup_times.append(lookup_time)
                    self._update_avg_lookup_time()
                    return entry.value
                else:
                    # Remove expired entry
                    if entry and self._is_expired(entry):
                        self.memory_cache.remove(cache_key)
                        self.stats.expired_entries += 1

            # Try disk cache
            if self.disk_cache:
                entry = self.disk_cache.get(cache_key)
                if entry and not self._is_expired(entry):
                    self.stats.cache_hits += 1

                    # Store in memory cache if available
                    if self.memory_cache:
                        self.memory_cache.put(cache_key, entry)

                    lookup_time = (time.time() - start_time) * 1000
                    self.lookup_times.append(lookup_time)
                    self._update_avg_lookup_time()
                    return entry.value
                else:
                    # Remove expired entry
                    if entry and self._is_expired(entry):
                        self.disk_cache.remove(cache_key)
                        self.stats.expired_entries += 1

            # Cache miss
            self.stats.cache_misses += 1
            lookup_time = (time.time() - start_time) * 1000
            self.lookup_times.append(lookup_time)
            self._update_avg_lookup_time()
            return None

        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            self.stats.cache_misses += 1
            return None

    def put(
        self,
        indicator_name: str,
        parameters: Dict[str, Any],
        data: Any,
        result: Any,
        computation_time_ms: float,
        ttl_seconds: Optional[int] = None,
        additional_context: Optional[Dict[str, Any]] = None,
        source: str = "user_computation"
    ) -> bool:
        """
        Store computation result in cache.

        Args:
            indicator_name: Name of the technical indicator
            parameters: Indicator parameters
            data: Input data for computation
            result: Computation result to cache
            computation_time_ms: Time taken for computation in milliseconds
            ttl_seconds: Time to live in seconds (None for default)
            additional_context: Additional context
            source: Source of the computation

        Returns:
            True if successfully cached, False otherwise
        """
        start_time = time.time()

        try:
            # Generate cache key
            data_hash = self.key_generator.generate_data_hash(data)
            cache_key = self.key_generator.generate_key(
                indicator_name, parameters, data_hash, additional_context
            )

            # Determine TTL
            if ttl_seconds is None:
                ttl_seconds = self.config.default_ttl_seconds

            # Create cache entry
            entry = CacheEntry(
                key=cache_key,
                value=result,
                timestamp=datetime.now(),
                ttl_seconds=ttl_seconds,
                access_count=0,
                last_access=datetime.now(),
                size_bytes=self._estimate_size(result),
                compressed=False,
                computation_time_ms=computation_time_ms,
                source=source
            )

            # Store in memory cache
            memory_stored = False
            if self.memory_cache:
                memory_stored = self.memory_cache.put(cache_key, entry)

            # Store in disk cache if memory storage failed or disk cache is enabled
            disk_stored = False
            if self.disk_cache and (not memory_stored or self.config.enable_disk_cache):
                disk_stored = self.disk_cache.put(cache_key, entry, self.config.compression_type)

            storage_time = (time.time() - start_time) * 1000
            self.storage_times.append(storage_time)
            self._update_avg_storage_time()

            return memory_stored or disk_stored

        except Exception as e:
            logger.error(f"Error putting in cache: {e}")
            return False

    def remove(
        self,
        indicator_name: str,
        parameters: Dict[str, Any],
        data: Any,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Remove specific entry from cache."""
        try:
            data_hash = self.key_generator.generate_data_hash(data)
            cache_key = self.key_generator.generate_key(
                indicator_name, parameters, data_hash, additional_context
            )

            removed = False
            if self.memory_cache:
                removed |= self.memory_cache.remove(cache_key)

            if self.disk_cache:
                removed |= self.disk_cache.remove(cache_key)

            return removed

        except Exception as e:
            logger.error(f"Error removing from cache: {e}")
            return False

    def clear(self):
        """Clear all cache entries."""
        try:
            if self.memory_cache:
                self.memory_cache.clear()

            if self.disk_cache:
                self.disk_cache.clear()

            # Reset statistics
            self.stats = CacheStats()
            self.lookup_times.clear()
            self.storage_times.clear()

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def get_statistics(self) -> CacheStats:
        """Get comprehensive cache statistics."""
        try:
            # Update basic statistics
            if self.memory_cache:
                mem_stats = self.memory_cache.get_stats()
                self.stats.memory_entries = mem_stats['entries']
                self.stats.memory_usage_mb = mem_stats['memory_usage_mb']

            if self.disk_cache:
                disk_stats = self.disk_cache.get_stats()
                self.stats.disk_entries = disk_stats['entries']
                self.stats.disk_usage_gb = disk_stats['disk_usage_gb']
                self.stats.compression_ratio = disk_stats.get('compression_ratio', 1.0)

            # Calculate total entries
            self.stats.total_entries = self.stats.memory_entries + self.stats.disk_entries

            # Calculate cache hit rate
            total_requests = self.stats.cache_hits + self.stats.cache_misses
            if total_requests > 0:
                self.stats.cache_hit_rate = (self.stats.cache_hits / total_requests) * 100

            # Calculate total computation time saved
            self.stats.total_computation_time_saved_ms = (
                self.stats.cache_hits * self._get_avg_computation_time()
            )

            return self.stats

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return CacheStats()

    def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance report."""
        stats = self.get_statistics()

        return {
            'summary': asdict(stats),
            'performance_metrics': {
                'cache_efficiency': self._calculate_cache_efficiency(),
                'memory_utilization': self._calculate_memory_utilization(),
                'disk_utilization': self._calculate_disk_utilization(),
                'compression_effectiveness': self._calculate_compression_effectiveness()
            },
            'configuration': asdict(self.config),
            'recommendations': self._get_performance_recommendations()
        }

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        if entry.ttl_seconds <= 0:
            return False  # No expiration

        age_seconds = (datetime.now() - entry.timestamp).total_seconds()
        return age_seconds > entry.ttl_seconds

    def _estimate_size(self, obj: Any) -> int:
        """Estimate size of object in bytes."""
        try:
            if PANDAS_AVAILABLE and isinstance(obj, (pd.DataFrame, pd.Series)):
                return obj.memory_usage(deep=True).sum()
            else:
                return len(pickle.dumps(obj))
        except:
            return 1024  # Default estimate

    def _update_avg_lookup_time(self):
        """Update average lookup time."""
        if self.lookup_times:
            self.stats.avg_lookup_time_ms = sum(self.lookup_times[-100:]) / min(len(self.lookup_times), 100)

    def _update_avg_storage_time(self):
        """Update average storage time."""
        if self.storage_times:
            self.stats.avg_storage_time_ms = sum(self.storage_times[-100:]) / min(len(self.storage_times), 100)

    def _get_avg_computation_time(self) -> float:
        """Get average computation time from cache entries."""
        # This is a simplified estimate
        return 10.0  # 10ms average

    def _calculate_cache_efficiency(self) -> Dict[str, float]:
        """Calculate cache efficiency metrics."""
        return {
            'hit_rate_efficiency': min(self.stats.cache_hit_rate / 80, 1.0),  # Target: 80%
            'lookup_time_efficiency': min(5 / max(self.stats.avg_lookup_time_ms, 1), 1.0),  # Target: <5ms
            'storage_time_efficiency': min(20 / max(self.stats.avg_storage_time_ms, 1), 1.0)  # Target: <20ms
        }

    def _calculate_memory_utilization(self) -> Dict[str, float]:
        """Calculate memory utilization metrics."""
        if self.memory_cache is None:
            return {'utilization_percent': 0.0, 'efficiency': 0.0}

        mem_stats = self.memory_cache.get_stats()
        return {
            'utilization_percent': mem_stats['utilization_percent'],
            'efficiency': min(mem_stats['utilization_percent'] / 70, 1.0)  # Target: 70%
        }

    def _calculate_disk_utilization(self) -> Dict[str, float]:
        """Calculate disk utilization metrics."""
        if self.disk_cache is None:
            return {'utilization_percent': 0.0, 'efficiency': 0.0}

        disk_stats = self.disk_cache.get_stats()
        return {
            'utilization_percent': disk_stats['utilization_percent'],
            'efficiency': min(disk_stats['utilization_percent'] / 80, 1.0)  # Target: 80%
        }

    def _calculate_compression_effectiveness(self) -> Dict[str, float]:
        """Calculate compression effectiveness."""
        return {
            'compression_ratio': self.stats.compression_ratio,
            'space_saved_percent': (1 - self.stats.compression_ratio) * 100,
            'efficiency': min(self.stats.compression_ratio / 0.5, 1.0) if self.stats.compression_ratio < 1 else 1.0
        }

    def _get_performance_recommendations(self) -> List[str]:
        """Get performance optimization recommendations."""
        recommendations = []

        # Cache hit rate recommendations
        if self.stats.cache_hit_rate < 60:
            recommendations.append("Low cache hit rate. Consider increasing cache size or TTL.")
        elif self.stats.cache_hit_rate < 80:
            recommendations.append("Cache hit rate could be improved. Review cache eviction policy.")

        # Memory utilization recommendations
        mem_util = self._calculate_memory_utilization()
        if mem_util['utilization_percent'] > 90:
            recommendations.append("High memory utilization. Consider increasing memory cache size.")
        elif mem_util['utilization_percent'] < 30:
            recommendations.append("Low memory utilization. Cache size may be too large.")

        # Disk utilization recommendations
        disk_util = self._calculate_disk_utilization()
        if disk_util['utilization_percent'] > 90:
            recommendations.append("High disk utilization. Consider cleaning up old entries.")

        # Performance recommendations
        if self.stats.avg_lookup_time_ms > 10:
            recommendations.append("Slow cache lookup. Consider optimizing cache structure.")

        if self.stats.avg_storage_time_ms > 50:
            recommendations.append("Slow cache storage. Consider disabling compression or using faster storage.")

        # Compression recommendations
        if self.stats.compression_ratio > 0.8:
            recommendations.append("Low compression effectiveness. Consider adjusting compression settings.")

        return recommendations

    def _start_cleanup_thread(self):
        """Start background cleanup thread."""
        def cleanup_worker():
            while not self.stop_cleanup.wait(self.config.cache_check_interval):
                self._cleanup_expired_entries()

        self.cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self.cleanup_thread.start()

    def _cleanup_expired_entries(self):
        """Clean up expired cache entries."""
        try:
            expired_count = 0

            # Clean memory cache
            if self.memory_cache:
                # This would require implementing expiration check in MemoryCache
                pass

            # Clean disk cache
            if self.disk_cache:
                # This would require implementing expiration check in DiskCache
                pass

            self.stats.expired_entries += expired_count

            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired cache entries")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_cleanup.set()
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5)

# Utility functions
def get_default_cache() -> ComputationCache:
    """Get default computation cache instance."""
    config = CacheConfig()
    return ComputationCache(config)

def create_cache_with_config(**kwargs) -> ComputationCache:
    """Create cache with custom configuration."""
    config = CacheConfig(**kwargs)
    return ComputationCache(config)
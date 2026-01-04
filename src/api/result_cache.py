"""
Backtest Result Caching System
==============================

Intelligent caching system for backtest results with support for:
- Result summary caching
- Large data pagination
- Cache invalidation
- Performance optimization

Author: CBSC Quant Team
Version: 1.0.0
"""

import asyncio
import json
import hashlib
import logging
import pickle
import gzip
import zlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass, asdict
import redis
import redis.asyncio as redis_async
import pandas as pd
import numpy as np
from functools import wraps
import aiofiles
import os

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration"""
    redis_url: str = "redis://localhost:6379"
    default_ttl: int = 3600  # 1 hour
    summary_ttl: int = 86400  # 24 hours
    large_data_ttl: int = 604800  # 7 days
    max_memory_usage: int = 1024 * 1024 * 1024  # 1GB
    compression_enabled: bool = True
    compression_level: int = 6
    cache_dir: str = "./cache"
    enable_disk_cache: bool = True
    disk_cache_limit: int = 10 * 1024 * 1024 * 1024  # 10GB


@dataclass
class CacheEntry:
    """Cache entry metadata"""
    key: str
    size: int
    created_at: datetime
    accessed_at: datetime
    access_count: int
    ttl: int
    compressed: bool
    location: str  # "memory", "redis", or "disk"
    checksum: str


class ResultCache:
    """Advanced caching system for backtest results"""

    def __init__(self, config: Optional[CacheConfig] = None):
        """
        Initialize cache system

        Args:
            config: Cache configuration
        """
        self.config = config or CacheConfig()
        self.redis: Optional[redis_async.Redis] = None
        self.redis_sync = redis.Redis.from_url(self.config.redis_url, decode_responses=False)

        # Memory cache
        self.memory_cache: Dict[str, Tuple[Any, CacheEntry]] = {}
        self.memory_usage = 0

        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "memory_hits": 0,
            "redis_hits": 0,
            "disk_hits": 0,
            "compressions": 0,
            "evictions": 0
        }

        # Cache policies
        self.cache_policies = {
            "summary": self._cache_summary_policy,
            "equity_curve": self._cache_equity_curve_policy,
            "trades": self._cache_trades_policy,
            "risk_metrics": self._cache_risk_metrics_policy,
            "full_result": self._cache_full_result_policy
        }

        # Ensure cache directory exists
        if self.config.enable_disk_cache:
            os.makedirs(self.config.cache_dir, exist_ok=True)

    async def initialize(self):
        """Initialize cache system"""
        # Connect to Redis
        self.redis = await redis_async.from_url(self.config.redis_url, decode_responses=False)

        # Test connection
        try:
            await self.redis.ping()
            logger.info("Connected to Redis for caching")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

        # Clean up expired entries
        await self.cleanup_expired()

        logger.info("Cache system initialized")

    async def close(self):
        """Close cache connections"""
        if self.redis:
            await self.redis.close()
        self.redis_sync.close()

    async def get(
        self,
        key: str,
        data_type: str = "full_result",
        use_memory: bool = True,
        use_redis: bool = True,
        use_disk: bool = True
    ) -> Optional[Any]:
        """
        Get data from cache

        Args:
            key: Cache key
            data_type: Type of data for policy selection
            use_memory: Check memory cache
            use_redis: Check Redis cache
            use_disk: Check disk cache

        Returns:
            Cached data or None
        """
        # Try memory cache first
        if use_memory and key in self.memory_cache:
            data, entry = self.memory_cache[key]
            entry.accessed_at = datetime.utcnow()
            entry.access_count += 1
            self.stats["hits"] += 1
            self.stats["memory_hits"] += 1
            logger.debug(f"Cache hit (memory): {key}")
            return data

        # Try Redis cache
        if use_redis:
            data = await self._get_from_redis(key)
            if data is not None:
                self.stats["hits"] += 1
                self.stats["redis_hits"] += 1
                logger.debug(f"Cache hit (Redis): {key}")

                # Store in memory if appropriate
                if self._should_cache_in_memory(key, data):
                    await self._store_in_memory(key, data, data_type)
                return data

        # Try disk cache
        if use_disk and self.config.enable_disk_cache:
            data = await self._get_from_disk(key)
            if data is not None:
                self.stats["hits"] += 1
                self.stats["disk_hits"] += 1
                logger.debug(f"Cache hit (disk): {key}")

                # Store in memory if appropriate
                if self._should_cache_in_memory(key, data):
                    await self._store_in_memory(key, data, data_type)
                return data

        # Cache miss
        self.stats["misses"] += 1
        logger.debug(f"Cache miss: {key}")
        return None

    async def set(
        self,
        key: str,
        data: Any,
        data_type: str = "full_result",
        ttl: Optional[int] = None,
        force_memory: bool = False
    ):
        """
        Store data in cache

        Args:
            key: Cache key
            data: Data to cache
            data_type: Type of data for policy selection
            ttl: Time to live (seconds)
            force_memory: Force storage in memory
        """
        # Apply cache policy
        policy = self.cache_policies.get(data_type, self._cache_full_result_policy)
        locations = await policy(key, data, ttl or self.config.default_ttl)

        # Store based on policy
        if force_memory or "memory" in locations:
            await self._store_in_memory(key, data, data_type, ttl)

        if "redis" in locations:
            await self._store_in_redis(key, data, ttl)

        if "disk" in locations and self.config.enable_disk_cache:
            await self._store_in_disk(key, data, ttl)

        logger.debug(f"Cached: {key} -> {locations}")

    async def delete(self, key: str):
        """Delete from all cache locations"""
        # Remove from memory
        if key in self.memory_cache:
            entry = self.memory_cache[key][1]
            self.memory_usage -= entry.size
            del self.memory_cache[key]

        # Remove from Redis
        await self.redis.delete(key)

        # Remove from disk
        disk_path = os.path.join(self.config.cache_dir, f"{key}.cache")
        if os.path.exists(disk_path):
            os.remove(disk_path)

        logger.debug(f"Deleted from cache: {key}")

    async def clear(self, pattern: Optional[str] = None):
        """Clear cache entries"""
        if pattern:
            # Clear matching entries
            # Memory
            keys_to_delete = [k for k in self.memory_cache.keys() if pattern in k]
            for key in keys_to_delete:
                await self.delete(key)

            # Redis
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break

            # Disk
            for filename in os.listdir(self.config.cache_dir):
                if pattern in filename:
                    os.remove(os.path.join(self.config.cache_dir, filename))
        else:
            # Clear all
            self.memory_cache.clear()
            self.memory_usage = 0
            await self.redis.flushdb()

            if self.config.enable_disk_cache:
                for filename in os.listdir(self.config.cache_dir):
                    if filename.endswith('.cache'):
                        os.remove(os.path.join(self.config.cache_dir, filename))

        logger.info(f"Cleared cache: {pattern or 'all'}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            **self.stats,
            "hit_rate": hit_rate,
            "memory_entries": len(self.memory_cache),
            "memory_usage_mb": self.memory_usage / (1024 * 1024),
            "redis_info": await self._get_redis_info()
        }

    async def cleanup_expired(self):
        """Clean up expired cache entries"""
        # Clean memory cache
        now = datetime.utcnow()
        expired_keys = [
            key for key, (_, entry) in self.memory_cache.items()
            if now - entry.created_at > timedelta(seconds=entry.ttl)
        ]

        for key in expired_keys:
            await self.delete(key)
            self.stats["evictions"] += 1

        # Clean disk cache
        if self.config.enable_disk_cache:
            for filename in os.listdir(self.config.cache_dir):
                if filename.endswith('.cache'):
                    filepath = os.path.join(self.config.cache_dir, filename)
                    # Check file age
                    file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_age > timedelta(days=7):  # Remove files older than 7 days
                        os.remove(filepath)
                        logger.debug(f"Removed expired disk cache: {filename}")

    async def _get_from_redis(self, key: str) -> Optional[Any]:
        """Get data from Redis"""
        try:
            data = await self.redis.get(key)
            if data:
                # Decompress if needed
                if data.startswith(b'COMP:'):
                    data = gzip.decompress(data[5:])
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Error getting from Redis: {e}")
        return None

    async def _store_in_redis(self, key: str, data: Any, ttl: int):
        """Store data in Redis"""
        try:
            # Serialize data
            serialized = pickle.dumps(data)

            # Compress if enabled and data is large enough
            if self.config.compression_enabled and len(serialized) > 1024:
                compressed = gzip.compress(serialized, compresslevel=self.config.compression_level)
                if len(compressed) < len(serialized):
                    serialized = b'COMP:' + compressed
                    self.stats["compressions"] += 1

            # Store with TTL
            await self.redis.setex(key, ttl, serialized)

        except Exception as e:
            logger.error(f"Error storing in Redis: {e}")

    async def _get_from_disk(self, key: str) -> Optional[Any]:
        """Get data from disk cache"""
        try:
            disk_path = os.path.join(self.config.cache_dir, f"{key}.cache")
            async with aiofiles.open(disk_path, 'rb') as f:
                data = await f.read()

            # Decompress if needed
            if data.startswith(b'COMP:'):
                data = gzip.decompress(data[5:])

            return pickle.loads(data)

        except Exception as e:
            logger.debug(f"Error getting from disk: {e}")
            return None

    async def _store_in_disk(self, key: str, data: Any, ttl: int):
        """Store data on disk"""
        try:
            disk_path = os.path.join(self.config.cache_dir, f"{key}.cache")

            # Serialize data
            serialized = pickle.dumps(data)

            # Compress if enabled
            if self.config.compression_enabled:
                compressed = gzip.compress(serialized, compresslevel=self.config.compression_level)
                serialized = b'COMP:' + compressed
                self.stats["compressions"] += 1

            # Write to disk
            async with aiofiles.open(disk_path, 'wb') as f:
                await f.write(serialized)

        except Exception as e:
            logger.error(f"Error storing on disk: {e}")

    async def _store_in_memory(self, key: str, data: Any, data_type: str, ttl: Optional[int] = None):
        """Store data in memory"""
        # Check if we have space
        data_size = len(pickle.dumps(data))

        if data_size > self.config.max_memory_usage:
            logger.warning(f"Data too large for memory cache: {key}")
            return

        # Evict if necessary
        while self.memory_usage + data_size > self.config.max_memory_usage:
            await self._evict_lru()

        # Create entry
        entry = CacheEntry(
            key=key,
            size=data_size,
            created_at=datetime.utcnow(),
            accessed_at=datetime.utcnow(),
            access_count=1,
            ttl=ttl or self.config.default_ttl,
            compressed=False,
            location="memory",
            checksum=hashlib.md5(pickle.dumps(data)).hexdigest()
        )

        # Store
        self.memory_cache[key] = (data, entry)
        self.memory_usage += data_size

    def _should_cache_in_memory(self, key: str, data: Any) -> bool:
        """Check if data should be cached in memory"""
        data_size = len(pickle.dumps(data))

        # Don't cache very large data in memory
        if data_size > 10 * 1024 * 1024:  # 10MB
            return False

        # Check if we have space
        if self.memory_usage + data_size > self.config.max_memory_usage * 0.8:
            return False

        return True

    async def _evict_lru(self):
        """Evict least recently used entry from memory"""
        if not self.memory_cache:
            return

        # Find LRU entry
        lru_key = min(self.memory_cache.keys(), key=lambda k: self.memory_cache[k][1].accessed_at)

        # Remove it
        entry = self.memory_cache[lru_key][1]
        self.memory_usage -= entry.size
        del self.memory_cache[lru_key]
        self.stats["evictions"] += 1

        logger.debug(f"Evicted from memory: {lru_key}")

    async def _get_redis_info(self) -> Dict[str, Any]:
        """Get Redis information"""
        try:
            info = await self.redis.info()
            return {
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "connected_clients": info.get("connected_clients", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except:
            return {}

    # Cache policies
    async def _cache_summary_policy(self, key: str, data: Any, ttl: int) -> List[str]:
        """Cache policy for result summaries"""
        # Cache in all locations
        return ["memory", "redis", "disk"]

    async def _cache_equity_curve_policy(self, key: str, data: Any, ttl: int) -> List[str]:
        """Cache policy for equity curve data"""
        # Cache in Redis and disk (can be large)
        return ["redis", "disk"]

    async def _cache_trades_policy(self, key: str, data: Any, ttl: int) -> List[str]:
        """Cache policy for trade data"""
        # Cache in Redis and disk
        return ["redis", "disk"]

    async def _cache_risk_metrics_policy(self, key: str, data: Any, ttl: int) -> List[str]:
        """Cache policy for risk metrics"""
        # Cache in all locations
        return ["memory", "redis", "disk"]

    async def _cache_full_result_policy(self, key: str, data: Any, ttl: int) -> List[str]:
        """Cache policy for full backtest results"""
        # Cache in Redis and disk (full results can be very large)
        return ["redis", "disk"]


# Cache decorator
def cached(
    key_func: Optional[Callable] = None,
    ttl: Optional[int] = None,
    data_type: str = "full_result",
    cache_instance: Optional[ResultCache] = None
):
    """
    Decorator to cache function results

    Args:
        key_func: Function to generate cache key from arguments
        ttl: Time to live in seconds
        data_type: Type of data for cache policy
        cache_instance: Cache instance to use
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                cache_key = f"{func.__name__}:{hashlib.md5(str(args + tuple(sorted(kwargs.items()))).encode()).hexdigest()}"

            # Use provided cache or create default
            cache = cache_instance or ResultCache()
            if not cache.redis:
                await cache.initialize()

            # Try to get from cache
            result = await cache.get(cache_key, data_type=data_type)
            if result is not None:
                return result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache.set(cache_key, result, data_type=data_type, ttl=ttl)

            return result

        return wrapper
    return decorator


# Pagination helper for large datasets
async def paginate_result(
    cache: ResultCache,
    base_key: str,
    data: Union[List, pd.DataFrame],
    page: int = 1,
    page_size: int = 100,
    ttl: Optional[int] = None
) -> Dict[str, Any]:
    """
    Paginate and cache large result datasets

    Args:
        cache: Cache instance
        base_key: Base cache key
        data: Data to paginate
        page: Page number (1-based)
        page_size: Items per page
        ttl: Cache TTL

    Returns:
        Paginated result with metadata
    """
    total_items = len(data)
    total_pages = (total_items + page_size - 1) // page_size

    if page > total_pages:
        return {
            "data": [],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": False,
                "has_prev": page > 1
            }
        }

    # Calculate slice indices
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_items)

    # Cache page key
    page_key = f"{base_key}:page:{page}"

    # Try to get from cache
    page_data = await cache.get(page_key, data_type="page")
    if page_data is None:
        # Slice data
        if isinstance(data, pd.DataFrame):
            page_data = data.iloc[start_idx:end_idx].to_dict('records')
        else:
            page_data = data[start_idx:end_idx]

        # Cache page
        await cache.set(page_key, page_data, data_type="page", ttl=ttl)

    return {
        "data": page_data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


# Example usage
if __name__ == "__main__":
    async def example_usage():
        # Create cache instance
        cache = ResultCache()
        await cache.initialize()

        try:
            # Cache some data
            result_data = {
                "total_return": 0.15,
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.08,
                "equity_curve": pd.Series([100, 105, 110, 108, 115]),
                "trades": [{"symbol": "AAPL", "price": 150, "quantity": 100}] * 1000
            }

            # Store with different data types
            await cache.set("backtest:123:summary", result_data["total_return"], "summary")
            await cache.set("backtest:123:equity", result_data["equity_curve"], "equity_curve")
            await cache.set("backtest:123:trades", result_data["trades"], "trades")

            # Retrieve from cache
            cached_return = await cache.get("backtest:123:summary")
            print(f"Cached return: {cached_return}")

            # Paginate trades
            paginated = await paginate_result(
                cache,
                "backtest:123:trades",
                result_data["trades"],
                page=1,
                page_size=100
            )
            print(f"Trade page 1: {len(paginated['data'])} trades")

            # Get statistics
            stats = await cache.get_stats()
            print(f"Cache stats: {stats}")

        finally:
            await cache.close()

    # Run example
    asyncio.run(example_usage())
"""
Cache Service for VectorBT Multiprocess Engine
============================================

Provides Redis-based caching with intelligent cache management,
optimization, and performance monitoring.
"""

import redis
import pickle
import json
import hashlib
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import aioredis
import time
import threading
from functools import wraps
import numpy as np
import pandas as pd
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class CacheLevel(str, Enum):
    """Cache levels for different data types"""
    MEMORY = "memory"      # Fast in-memory cache
    REDIS = "redis"        # Distributed Redis cache
    DISK = "disk"          # Persistent disk cache


@dataclass
class CacheKey:
    """Cache key structure"""
    strategy_id: str
    strategy_config: Dict[str, Any]
    backtest_type: str
    start_date: str
    end_date: str
    initial_capital: float
    commission_rate: float
    slippage_rate: float

    def to_hash(self) -> str:
        """Generate hash key from cache key"""
        # Create deterministic string representation
        key_dict = asdict(self)
        key_str = json.dumps(key_dict, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(key_str.encode('utf-8')).hexdigest()


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    data: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    ttl: Optional[timedelta] = None
    size_bytes: Optional[int] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.size_bytes is None:
            self.size_bytes = len(pickle.dumps(self.data))


@dataclass
class CacheStats:
    """Cache statistics"""
    total_entries: int = 0
    total_size_bytes: int = 0
    hit_rate: float = 0.0
    miss_rate: float = 0.0
    eviction_count: int = 0
    last_cleanup: Optional[datetime] = None


class BacktestCache:
    """
    Multi-level caching system for backtest results
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        memory_size_mb: int = 256,
        default_ttl: timedelta = timedelta(days=7),
        cleanup_interval: timedelta = timedelta(hours=1)
    ):
        """
        Initialize cache service

        Args:
            redis_url: Redis connection URL
            memory_size_mb: Maximum memory cache size in MB
            default_ttl: Default time-to-live for cache entries
            cleanup_interval: Interval for cache cleanup
        """
        self.redis_url = redis_url
        self.memory_size_mb = memory_size_mb
        self.memory_size_bytes = memory_size_mb * 1024 * 1024
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval

        # Initialize caches
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.redis_cache: Optional[Cache] = None

        # Statistics
        self.stats = CacheStats()
        self.hit_count = 0
        self.miss_count = 0

        # Cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize cache components"""
        try:
            # Initialize Redis cache
            self.redis_cache = Cache(
                Cache.REDIS,
                endpoint=self.redis_url,
                serializer=PickleSerializer(),
                ttl=self.default_ttl.total_seconds()
            )

            # Test Redis connection
            await self.redis_cache.set("test", "value")
            await self.redis_cache.delete("test")
            logger.info("Redis cache initialized successfully")

        except Exception as e:
            logger.warning(f"Redis cache initialization failed: {e}")
            self.redis_cache = None

        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Cache service initialized")

    async def get(
        self,
        cache_key: CacheKey,
        cache_level: CacheLevel = CacheLevel.MEMORY,
        fallback: bool = True
    ) -> Optional[Any]:
        """
        Get value from cache

        Args:
            cache_key: Cache key
            cache_level: Primary cache level to check
            fallback: Whether to fallback to other cache levels

        Returns:
            Cached value or None if not found
        """
        key_hash = cache_key.to_hash()
        value = None

        # Try primary cache level first
        if cache_level == CacheLevel.MEMORY:
            value = await self._get_from_memory(key_hash)
            if value is None and fallback:
                value = await self._get_from_redis(key_hash)
        elif cache_level == CacheLevel.REDIS:
            value = await self._get_from_redis(key_hash)
            if value is None and fallback:
                value = await self._get_from_memory(key_hash)

        # Update statistics
        if value is not None:
            self.hit_count += 1
            await self._update_access_stats(key_hash)
        else:
            self.miss_count += 1

        # Update hit/miss rates
        total = self.hit_count + self.miss_count
        if total > 0:
            self.stats.hit_rate = self.hit_count / total
            self.stats.miss_rate = self.miss_count / total

        return value

    async def set(
        self,
        cache_key: CacheKey,
        value: Any,
        cache_level: CacheLevel = CacheLevel.MEMORY,
        ttl: Optional[timedelta] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Set value in cache

        Args:
            cache_key: Cache key
            value: Value to cache
            cache_level: Cache level to store in
            ttl: Custom TTL for entry
            tags: Tags for categorization

        Returns:
            True if successful
        """
        key_hash = cache_key.to_hash()
        ttl = ttl or self.default_ttl
        now = datetime.now()

        # Create cache entry
        entry = CacheEntry(
            data=value,
            created_at=now,
            accessed_at=now,
            ttl=ttl,
            tags=tags or []
        )

        success = False

        # Store in specified cache level
        if cache_level == CacheLevel.MEMORY:
            success = await self._set_in_memory(key_hash, entry)
        elif cache_level == CacheLevel.REDIS and self.redis_cache:
            success = await self._set_in_redis(key_hash, entry, ttl)

        # Also store in fallback cache if different
        if success and fallback and cache_level == CacheLevel.MEMORY and self.redis_cache:
            await self._set_in_redis(key_hash, entry, ttl)
        elif success and fallback and cache_level == CacheLevel.REDIS:
            await self._set_in_memory(key_hash, entry)

        # Update statistics
        if success:
            self.stats.total_entries += 1
            self.stats.total_size_bytes += entry.size_bytes or 0

        return success

    async def delete(self, cache_key: CacheKey) -> bool:
        """
        Delete entry from all cache levels

        Args:
            cache_key: Cache key to delete

        Returns:
            True if deleted from at least one level
        """
        key_hash = cache_key.to_hash()
        deleted = False

        # Delete from memory
        if key_hash in self.memory_cache:
            del self.memory_cache[key_hash]
            deleted = True

        # Delete from Redis
        if self.redis_cache:
            try:
                await self.redis_cache.delete(key_hash)
                deleted = True
            except Exception as e:
                logger.warning(f"Failed to delete from Redis: {e}")

        return deleted

    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """
        Invalidate cache entries by tags

        Args:
            tags: Tags to match

        Returns:
            Number of entries invalidated
        """
        invalidated = 0

        # Invalidate from memory cache
        to_delete = []
        for key_hash, entry in self.memory_cache.items():
            if any(tag in entry.tags for tag in tags):
                to_delete.append(key_hash)

        for key_hash in to_delete:
            del self.memory_cache[key_hash]
            invalidated += 1

        # Redis would require a more complex approach
        # For now, just log the request
        logger.info(f"Invalidated {invalidated} entries with tags: {tags}")

        return invalidated

    async def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        self.stats.total_entries = len(self.memory_cache)
        self.stats.total_size_bytes = sum(
            entry.size_bytes or 0 for entry in self.memory_cache.values()
        )
        return self.stats

    async def _get_from_memory(self, key_hash: str) -> Optional[Any]:
        """Get value from memory cache"""
        entry = self.memory_cache.get(key_hash)
        if entry is not None:
            # Check TTL
            if entry.ttl and (datetime.now() - entry.created_at) > entry.ttl:
                del self.memory_cache[key_hash]
                return None

            # Update access stats
            entry.accessed_at = datetime.now()
            entry.access_count += 1
            return entry.data
        return None

    async def _get_from_redis(self, key_hash: str) -> Optional[Any]:
        """Get value from Redis cache"""
        if not self.redis_cache:
            return None

        try:
            value = await self.redis_cache.get(key_hash)
            return value
        except Exception as e:
            logger.warning(f"Redis get failed: {e}")
            return None

    async def _set_in_memory(self, key_hash: str, entry: CacheEntry) -> bool:
        """Set value in memory cache"""
        try:
            # Check memory limit
            current_size = sum(
                e.size_bytes or 0 for e in self.memory_cache.values()
            )

            if current_size + entry.size_bytes > self.memory_size_bytes:
                # Evict least recently used entries
                await self._evict_lru(entry.size_bytes or 0)

            self.memory_cache[key_hash] = entry
            return True
        except Exception as e:
            logger.error(f"Memory cache set failed: {e}")
            return False

    async def _set_in_redis(self, key_hash: str, entry: CacheEntry, ttl: timedelta) -> bool:
        """Set value in Redis cache"""
        if not self.redis_cache:
            return False

        try:
            await self.redis_cache.set(key_hash, entry, ttl=int(ttl.total_seconds()))
            return True
        except Exception as e:
            logger.warning(f"Redis set failed: {e}")
            return False

    async def _update_access_stats(self, key_hash: str):
        """Update access statistics for entry"""
        entry = self.memory_cache.get(key_hash)
        if entry:
            entry.accessed_at = datetime.now()
            entry.access_count += 1

    async def _evict_lru(self, required_space: int):
        """Evict least recently used entries to free space"""
        # Sort by last access time
        sorted_entries = sorted(
            self.memory_cache.items(),
            key=lambda x: x[1].accessed_at
        )

        freed_space = 0
        for key_hash, entry in sorted_entries:
            del self.memory_cache[key_hash]
            freed_space += entry.size_bytes or 0
            self.stats.eviction_count += 1

            if freed_space >= required_space:
                break

    async def _cleanup_loop(self):
        """Periodic cleanup of expired entries"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval.total_seconds())
                await self._cleanup_expired()
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")

    async def _cleanup_expired(self):
        """Remove expired entries from cache"""
        now = datetime.now()
        expired_keys = []

        for key_hash, entry in self.memory_cache.items():
            if entry.ttl and (now - entry.created_at) > entry.ttl:
                expired_keys.append(key_hash)

        for key_hash in expired_keys:
            del self.memory_cache[key_hash]

        self.stats.last_cleanup = now
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

    async def close(self):
        """Close cache service"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        if self.redis_cache:
            await self.redis_cache.close()

        logger.info("Cache service closed")


# Cache decorators for easy use
def cache_backtest_result(ttl: timedelta = timedelta(days=7)):
    """
    Decorator to cache backtest function results

    Args:
        ttl: Time-to-live for cache entries
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract cache key from parameters
            if len(args) > 0 and hasattr(args[0], '__dict__'):
                # First arg is self, check if it has cache
                if hasattr(args[0], 'cache'):
                    cache = args[0].cache
                    # Create cache key from function arguments
                    cache_key = CacheKey(
                        strategy_id=kwargs.get('strategy_id', ''),
                        strategy_config=kwargs.get('strategy_config', {}),
                        backtest_type=kwargs.get('backtest_type', 'standard'),
                        start_date=str(kwargs.get('start_date', '')),
                        end_date=str(kwargs.get('end_date', '')),
                        initial_capital=kwargs.get('initial_capital', 1000000),
                        commission_rate=kwargs.get('commission_rate', 0.001),
                        slippage_rate=kwargs.get('slippage_rate', 0.0005)
                    )

                    # Try to get from cache
                    cached_result = await cache.get(cache_key)
                    if cached_result is not None:
                        return cached_result

                    # Execute function and cache result
                    result = await func(*args, **kwargs)
                    await cache.set(cache_key, result, ttl=ttl)
                    return result

            # No cache available, execute normally
            return await func(*args, **kwargs)

        return wrapper
    return decorator


# Utility functions for cache management
async def warm_cache(
    cache: BacktestCache,
    strategy_configs: List[Dict[str, Any]],
    common_parameters: List[Dict[str, Any]]
):
    """
    Warm cache with common backtest configurations

    Args:
        cache: Cache instance
        strategy_configs: List of strategy configurations
        common_parameters: List of common backtest parameters
    """
    logger.info("Starting cache warm-up")

    warmed_count = 0
    for strategy_config in strategy_configs:
        for params in common_parameters:
            # Create cache key
            cache_key = CacheKey(
                strategy_id=strategy_config.get('strategy_id', ''),
                strategy_config=strategy_config,
                backtest_type=params.get('backtest_type', 'standard'),
                start_date=str(params.get('start_date', '')),
                end_date=str(params.get('end_date', '')),
                initial_capital=params.get('initial_capital', 1000000),
                commission_rate=params.get('commission_rate', 0.001),
                slippage_rate=params.get('slippage_rate', 0.0005)
            )

            # Check if already cached
            if await cache.get(cache_key) is None:
                # This would trigger actual backtest execution
                # For warm-up, we might use pre-computed results
                logger.debug(f"Cache entry missing for {cache_key.strategy_id}")
                # In production, you would trigger the backtest here

        warmed_count += 1

    logger.info(f"Cache warm-up completed for {warmed_count} strategies")


async def analyze_cache_usage(cache: BacktestCache) -> Dict[str, Any]:
    """
    Analyze cache usage patterns

    Args:
        cache: Cache instance

    Returns:
        Usage analysis
    """
    stats = await cache.get_stats()

    # Analyze memory cache
    if cache.memory_cache:
        # Calculate access patterns
        access_counts = [entry.access_count for entry in cache.memory_cache.values()]
        avg_access = np.mean(access_counts) if access_counts else 0

        # Calculate age distribution
        now = datetime.now()
        ages = [(now - entry.created_at).total_seconds() / 3600
                for entry in cache.memory_cache.values()]
        avg_age = np.mean(ages) if ages else 0

        # Most accessed entries
        most_accessed = sorted(
            cache.memory_cache.items(),
            key=lambda x: x[1].access_count,
            reverse=True
        )[:5]

        analysis = {
            'total_entries': stats.total_entries,
            'total_size_mb': stats.total_size_bytes / (1024 * 1024),
            'hit_rate': stats.hit_rate,
            'miss_rate': stats.miss_rate,
            'eviction_count': stats.eviction_count,
            'avg_access_count': avg_access,
            'avg_age_hours': avg_age,
            'most_accessed': [
                {'key': key[:16], 'access_count': entry.access_count}
                for key, entry in most_accessed
            ]
        }
    else:
        analysis = {
            'total_entries': 0,
            'total_size_mb': 0,
            'hit_rate': stats.hit_rate,
            'miss_rate': stats.miss_rate,
            'eviction_count': stats.eviction_count
        }

    return analysis


# Example usage
async def example_cache_usage():
    """Example of using the cache service"""
    # Initialize cache
    cache = BacktestCache(
        redis_url="redis://localhost:6379/1",
        memory_size_mb=128,
        default_ttl=timedelta(hours=24)
    )

    try:
        await cache.initialize()

        # Create test data
        test_result = {
            'task_id': 'test-123',
            'total_return': 0.15,
            'sharpe_ratio': 1.2,
            'max_drawdown': -0.08,
            'equity_curve': pd.Series([1000000 * (1 + 0.001 * i) for i in range(100)])
        }

        # Create cache key
        cache_key = CacheKey(
            strategy_id="momentum_strategy",
            strategy_config={'lookback': 20, 'threshold': 0.02},
            backtest_type="standard",
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_capital=1000000,
            commission_rate=0.001,
            slippage_rate=0.0005
        )

        # Store in cache
        success = await cache.set(cache_key, test_result, tags=['momentum', 'test'])
        print(f"Cache set: {success}")

        # Retrieve from cache
        cached_result = await cache.get(cache_key)
        print(f"Cached result: {cached_result is not None}")

        if cached_result:
            print(f"Total return: {cached_result['total_return']:.2%}")

        # Get cache statistics
        stats = await cache.get_stats()
        print(f"Cache stats: entries={stats.total_entries}, hit_rate={stats.hit_rate:.2%}")

        # Analyze usage
        usage = await analyze_cache_usage(cache)
        print(f"Usage analysis: {usage}")

    finally:
        await cache.close()


if __name__ == "__main__":
    asyncio.run(example_cache_usage())
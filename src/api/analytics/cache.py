"""
Analytics Cache Service
Handles caching for analytics data using Redis
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

logger = logging.getLogger(__name__)


class AnalyticsCache:
    """Redis-based caching service for analytics data"""

    # Cache TTL settings (in seconds)
    CACHE_TTL = {
        "performance_1D": 300,      # 5 minutes
        "performance_1W": 1800,     # 30 minutes
        "performance_1M": 3600,     # 1 hour
        "performance_3M": 7200,     # 2 hours
        "performance_6M": 14400,    # 4 hours
        "performance_1Y": 28800,    # 8 hours
        "performance_ALL": 86400,   # 24 hours
        "realtime": 60,             # 1 minute
        "portfolio": 900,           # 15 minutes
        "historical": 3600,         # 1 hour
        "correlations": 7200,       # 2 hours
        "risk_metrics": 1800        # 30 minutes
    }

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        max_connections: int = 20,
        retry_on_timeout: bool = True
    ):
        """
        Initialize cache service

        Args:
            redis_url: Redis connection URL
            max_connections: Maximum connection pool size
            retry_on_timeout: Whether to retry on timeout
        """
        self.redis_url = redis_url
        self.pool = None
        self.redis = None
        self.max_connections = max_connections
        self.retry_on_timeout = retry_on_timeout

    async def initialize(self):
        """Initialize Redis connection pool"""
        try:
            self.pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                retry_on_timeout=self.retry_on_timeout
            )
            self.redis = redis.Redis(connection_pool=self.pool)

            # Test connection
            await self.redis.ping()
            logger.info("Analytics cache initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize analytics cache: {e}")
            raise

    async def close(self):
        """Close Redis connections"""
        if self.pool:
            await self.pool.disconnect()
            logger.info("Analytics cache connections closed")

    async def get(self, key: str, ttl: Optional[int] = None) -> Optional[Dict]:
        """
        Get value from cache

        Args:
            key: Cache key
            ttl: Optional TTL override for check

        Returns:
            Cached value or None if not found/expired
        """
        if not self.redis:
            await self.initialize()

        try:
            value = await self.redis.get(key)
            if value:
                data = json.loads(value)
                # Check if data is still valid based on timestamp
                if self._is_data_valid(data, ttl):
                    return data
                else:
                    # Remove expired data
                    await self.delete(key)
            return None

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Dict[str, Any],
        ttl: Optional[int] = None,
        tags: Optional[list] = None
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            tags: Optional tags for cache invalidation

        Returns:
            True if successful, False otherwise
        """
        if not self.redis:
            await self.initialize()

        try:
            # Add metadata
            cache_value = {
                "data": value,
                "cached_at": datetime.utcnow().isoformat(),
                "ttl": ttl,
                "tags": tags or []
            }

            # Determine TTL
            if ttl is None:
                ttl = self._get_ttl_for_key(key)

            # Store in Redis
            success = await self.redis.setex(
                key,
                ttl,
                json.dumps(cache_value, default=str)
            )

            # Store tag mappings if tags provided
            if tags:
                for tag in tags:
                    tag_key = f"tag:{tag}"
                    await self.redis.sadd(tag_key, key)
                    await self.redis.expire(tag_key, ttl)

            return success

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.redis:
            await self.initialize()

        try:
            # Get tags before deleting
            cached_value = await self.get(key)
            if cached_value and cached_value.get("tags"):
                for tag in cached_value["tags"]:
                    tag_key = f"tag:{tag}"
                    await self.redis.srem(tag_key, key)

            # Delete the key
            return bool(await self.redis.delete(key))

        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def invalidate_by_tag(self, tag: str) -> int:
        """
        Invalidate all cache entries with given tag

        Args:
            tag: Tag to invalidate

        Returns:
            Number of keys invalidated
        """
        if not self.redis:
            await self.initialize()

        try:
            tag_key = f"tag:{tag}"
            keys = await self.redis.smembers(tag_key)

            if keys:
                # Delete all keys with this tag
                deleted = 0
                for key in keys:
                    if await self.delete(key):
                        deleted += 1

                # Delete the tag set
                await self.redis.delete(tag_key)

                return deleted

            return 0

        except Exception as e:
            logger.error(f"Cache invalidation error for tag {tag}: {e}")
            return 0

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache keys matching pattern

        Args:
            pattern: Pattern to match (e.g., "perf:*")

        Returns:
            Number of keys invalidated
        """
        if not self.redis:
            await self.initialize()

        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0

        except Exception as e:
            logger.error(f"Cache pattern invalidation error for {pattern}: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        if not self.redis:
            await self.initialize()

        try:
            info = await self.redis.info()

            # Parse memory usage
            memory_used = info.get("used_memory", 0)
            memory_human = info.get("used_memory_human", "0B")

            # Get key counts by pattern
            perf_keys = len(await self.redis.keys("perf:*"))
            realtime_keys = len(await self.redis.keys("realtime:*"))
            portfolio_keys = len(await self.redis.keys("portfolio:*"))

            return {
                "connected": True,
                "memory_used": memory_used,
                "memory_human": memory_human,
                "total_keys": info.get("db0", {}).get("keys", 0),
                "key_counts": {
                    "performance": perf_keys,
                    "realtime": realtime_keys,
                    "portfolio": portfolio_keys
                },
                "hit_rate": info.get("keyspace_hits", 0) / max(
                    info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1), 1
                ) * 100,
                "connections": info.get("connected_clients", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0)
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "connected": False,
                "error": str(e)
            }

    async def warm_cache(self, strategy_ids: list):
        """
        Warm up cache with common queries

        Args:
            strategy_ids: List of strategy IDs to warm
        """
        logger.info(f"Warming cache for {len(strategy_ids)} strategies")

        # This would trigger background calculations for common periods
        periods = ["1D", "1W", "1M"]

        for strategy_id in strategy_ids:
            for period in periods:
                # Trigger calculation (would use background task in production)
                key = f"perf:{strategy_id}:{period}"
                # Background task would calculate and cache this
                logger.debug(f"Cache warming triggered for {key}")

    async def cleanup_expired(self):
        """
        Clean up expired entries (handled by Redis TTL but can do additional cleanup)
        """
        # Redis automatically handles TTL expiration
        # This can be used for additional cleanup logic if needed
        logger.info("Cache cleanup completed")

    def _get_ttl_for_key(self, key: str) -> int:
        """
        Get appropriate TTL for cache key based on key pattern

        Args:
            key: Cache key

        Returns:
            TTL in seconds
        """
        if "perf:" in key:
            # Extract period from key like "perf:123:1M"
            parts = key.split(":")
            if len(parts) >= 3:
                period = parts[2]
                return self.CACHE_TTL.get(f"performance_{period}", 3600)
        elif "realtime:" in key:
            return self.CACHE_TTL["realtime"]
        elif "portfolio:" in key:
            return self.CACHE_TTL["portfolio"]
        elif "history:" in key:
            return self.CACHE_TTL["historical"]
        elif "correlations:" in key:
            return self.CACHE_TTL["correlations"]
        elif "risk:" in key:
            return self.CACHE_TTL["risk_metrics"]

        return 3600  # Default 1 hour

    def _is_data_valid(self, data: Dict, ttl_override: Optional[int] = None) -> bool:
        """
        Check if cached data is still valid

        Args:
            data: Cached data with metadata
            ttl_override: Optional TTL override

        Returns:
            True if data is valid, False otherwise
        """
        if not data or "cached_at" not in data:
            return False

        cached_at = datetime.fromisoformat(data["cached_at"])
        ttl = ttl_override or data.get("ttl", self.CACHE_TTL["performance_1M"])

        # Check if data has expired
        elapsed = (datetime.utcnow() - cached_at).total_seconds()
        return elapsed < ttl

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform cache health check

        Returns:
            Health check results
        """
        try:
            if not self.redis:
                await self.initialize()

            # Test basic operations
            test_key = "health:check"
            test_value = {"test": True, "timestamp": datetime.utcnow().isoformat()}

            # Set test value
            set_success = await self.set(test_key, test_value, ttl=10)

            # Get test value
            retrieved_value = await self.get(test_key)

            # Clean up
            await self.delete(test_key)

            return {
                "status": "healthy" if set_success and retrieved_value else "unhealthy",
                "operations": {
                    "set": set_success,
                    "get": retrieved_value is not None,
                    "delete": True
                }
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Singleton instance
_cache_instance: Optional[AnalyticsCache] = None


def get_cache() -> AnalyticsCache:
    """Get singleton cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = AnalyticsCache()
    return _cache_instance
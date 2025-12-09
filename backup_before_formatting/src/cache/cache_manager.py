"""
Cache Manager - Smart Caching System
緩存管理器 - 智能緩存系統
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union, List

from ..core.config import get_settings
from ..core.logging import get_logger, log_performance
from ..core.exceptions import ResourceError
from .redis_client import RedisClient
from .memory_cache import MemoryCache


class CacheManager:
    """
    Smart cache manager supporting both Redis and memory caching
    智能緩存管理器，支持 Redis 和內存緩存
    """

    def __init__(self, redis_client: Optional[RedisClient] = None):
        """
        Initialize cache manager.

        Args:
            redis_client: Optional Redis client instance
        """
        self.settings = get_settings()
        self.logger = get_logger("cache.manager")

        # Initialize cache backends
        self.redis_client = redis_client or self._create_redis_client()
        self.memory_cache = MemoryCache()

        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'redis_hits': 0,
            'memory_hits': 0,
            'redis_errors': 0,
            'memory_errors': 0,
            'total_operations': 0
        }

        self.logger.info(
            "Cache manager initialized",
            redis_enabled=self.redis_client is not None,
            memory_enabled=True
        )

    def _create_redis_client(self) -> Optional[RedisClient]:
        """Create Redis client if available."""
        try:
            return RedisClient(
                host=self.settings.redis.host,
                port=self.settings.redis.port,
                db=self.settings.redis.db,
                password=self.settings.redis.password,
                ssl=self.settings.redis.ssl
            )
        except Exception as e:
            self.logger.warning(f"Failed to create Redis client: {e}")
            return None

    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """
        Generate intelligent cache key.

        Args:
            prefix: Cache key prefix
            **kwargs: Parameters to include in key

        Returns:
            Generated cache key
        """
        try:
            # Sort parameters for consistent key generation
            key_data = json.dumps(kwargs, sort_keys=True, default=str)
            hash_obj = hashlib.md5(f"{prefix}:{key_data}".encode())
            return f"quant:{prefix}:{hash_obj.hexdigest()}"
        except Exception as e:
            self.logger.debug(f"Failed to generate cache key: {e}")
            # Fallback to simple key
            return f"quant:{prefix}:{hash(str(kwargs))}"

    @log_performance("cache_get")
    def get(self, key: str) -> Optional[Any]:
        """
        Get data from cache.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found
        """
        self.stats['total_operations'] += 1

        try:
            # Try Redis first
            if self.redis_client:
                try:
                    data = self.redis_client.get(key)
                    if data is not None:
                        self.stats['hits'] += 1
                        self.stats['redis_hits'] += 1
                        self.logger.debug("Cache hit from Redis", key=key)
                        return data
                except Exception as e:
                    self.stats['redis_errors'] += 1
                    self.logger.debug(f"Redis get error: {e}")

            # Fallback to memory cache
            data = self.memory_cache.get(key)
            if data is not None:
                self.stats['hits'] += 1
                self.stats['memory_hits'] += 1
                self.logger.debug("Cache hit from memory", key=key)
                return data

            # Cache miss
            self.stats['misses'] += 1
            self.logger.debug("Cache miss", key=key)
            return None

        except Exception as e:
            self.logger.error(f"Cache get operation failed: {e}", key=key)
            self.stats['misses'] += 1
            return None

    @log_performance("cache_set")
    def set(
        self,
        key: str,
        data: Any,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Set data in cache.

        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds (default from settings)
            tags: Optional tags for cache invalidation

        Returns:
            True if successful, False otherwise
        """
        self.stats['total_operations'] += 1

        try:
            # Use default TTL if not provided
            if ttl is None:
                ttl = self.settings.data.cache_ttl

            success = True

            # Set in Redis
            if self.redis_client:
                try:
                    self.redis_client.set(key, data, ttl, tags)
                    self.logger.debug("Data cached in Redis", key=key, ttl=ttl)
                except Exception as e:
                    self.stats['redis_errors'] += 1
                    self.logger.debug(f"Redis set error: {e}")
                    success = False

            # Always set in memory cache as backup
            try:
                self.memory_cache.set(key, data, ttl, tags)
                self.logger.debug("Data cached in memory", key=key, ttl=ttl)
            except Exception as e:
                self.stats['memory_errors'] += 1
                self.logger.debug(f"Memory cache set error: {e}")
                success = False

            return success

        except Exception as e:
            self.logger.error(f"Cache set operation failed: {e}", key=key)
            return False

    def delete(self, key: str) -> bool:
        """
        Delete data from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            success = True

            # Delete from Redis
            if self.redis_client:
                try:
                    self.redis_client.delete(key)
                    self.logger.debug("Data deleted from Redis", key=key)
                except Exception as e:
                    self.stats['redis_errors'] += 1
                    self.logger.debug(f"Redis delete error: {e}")
                    success = False

            # Delete from memory cache
            try:
                self.memory_cache.delete(key)
                self.logger.debug("Data deleted from memory", key=key)
            except Exception as e:
                self.stats['memory_errors'] += 1
                self.logger.debug(f"Memory cache delete error: {e}")
                success = False

            return success

        except Exception as e:
            self.logger.error(f"Cache delete operation failed: {e}", key=key)
            return False

    def delete_by_pattern(self, pattern: str) -> int:
        """
        Delete cache entries by pattern.

        Args:
            pattern: Pattern to match keys

        Returns:
            Number of keys deleted
        """
        try:
            deleted_count = 0

            # Delete from Redis
            if self.redis_client:
                try:
                    redis_deleted = self.redis_client.delete_by_pattern(pattern)
                    deleted_count += redis_deleted
                    self.logger.info(
                        "Keys deleted from Redis",
                        pattern=pattern,
                        count=redis_deleted
                    )
                except Exception as e:
                    self.stats['redis_errors'] += 1
                    self.logger.debug(f"Redis pattern delete error: {e}")

            # Delete from memory cache
            try:
                memory_deleted = self.memory_cache.delete_by_pattern(pattern)
                deleted_count += memory_deleted
                self.logger.info(
                    "Keys deleted from memory",
                    pattern=pattern,
                    count=memory_deleted
                )
            except Exception as e:
                self.stats['memory_errors'] += 1
                self.logger.debug(f"Memory cache pattern delete error: {e}")

            return deleted_count

        except Exception as e:
            self.logger.error(f"Cache pattern delete operation failed: {e}", pattern=pattern)
            return 0

    def delete_by_tags(self, tags: List[str]) -> int:
        """
        Delete cache entries by tags.

        Args:
            tags: List of tags to match

        Returns:
            Number of keys deleted
        """
        try:
            deleted_count = 0

            # Delete from Redis
            if self.redis_client:
                try:
                    redis_deleted = self.redis_client.delete_by_tags(tags)
                    deleted_count += redis_deleted
                    self.logger.info(
                        "Keys deleted from Redis by tags",
                        tags=tags,
                        count=redis_deleted
                    )
                except Exception as e:
                    self.stats['redis_errors'] += 1
                    self.logger.debug(f"Redis tag delete error: {e}")

            # Delete from memory cache
            try:
                memory_deleted = self.memory_cache.delete_by_tags(tags)
                deleted_count += memory_deleted
                self.logger.info(
                    "Keys deleted from memory by tags",
                    tags=tags,
                    count=memory_deleted
                )
            except Exception as e:
                self.stats['memory_errors'] += 1
                self.logger.debug(f"Memory cache tag delete error: {e}")

            return deleted_count

        except Exception as e:
            self.logger.error(f"Cache tag delete operation failed: {e}", tags=tags)
            return 0

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise
        """
        try:
            # Check Redis first
            if self.redis_client:
                try:
                    if self.redis_client.exists(key):
                        return True
                except Exception as e:
                    self.stats['redis_errors'] += 1
                    self.logger.debug(f"Redis exists error: {e}")

            # Check memory cache
            return self.memory_cache.exists(key)

        except Exception as e:
            self.logger.error(f"Cache exists operation failed: {e}", key=key)
            return False

    def clear_all(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if successful, False otherwise
        """
        try:
            success = True

            # Clear Redis
            if self.redis_client:
                try:
                    self.redis_client.clear_all()
                    self.logger.info("Redis cache cleared")
                except Exception as e:
                    self.stats['redis_errors'] += 1
                    self.logger.debug(f"Redis clear error: {e}")
                    success = False

            # Clear memory cache
            try:
                self.memory_cache.clear_all()
                self.logger.info("Memory cache cleared")
            except Exception as e:
                self.stats['memory_errors'] += 1
                self.logger.debug(f"Memory cache clear error: {e}")
                success = False

            return success

        except Exception as e:
            self.logger.error(f"Cache clear operation failed: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        stats = {
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'redis_hits': self.stats['redis_hits'],
            'memory_hits': self.stats['memory_hits'],
            'redis_errors': self.stats['redis_errors'],
            'memory_errors': self.stats['memory_errors'],
            'total_operations': self.stats['total_operations']
        }

        # Add backend-specific stats
        if self.redis_client:
            stats['redis'] = self.redis_client.get_stats()

        stats['memory'] = self.memory_cache.get_stats()
        stats['redis_connected'] = self.redis_client is not None

        return stats

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on cache backends.

        Returns:
            Health check results
        """
        health = {
            'overall': 'healthy',
            'redis': 'not_configured',
            'memory': 'healthy'
        }

        # Check Redis health
        if self.redis_client:
            try:
                redis_health = self.redis_client.health_check()
                health['redis'] = redis_health['status']
                if redis_health['status'] != 'healthy':
                    health['overall'] = 'degraded'
            except Exception as e:
                health['redis'] = 'unhealthy'
                health['overall'] = 'degraded'
                self.logger.error(f"Redis health check failed: {e}")

        # Check memory cache health
        try:
            memory_health = self.memory_cache.health_check()
            health['memory'] = memory_health['status']
            if memory_health['status'] != 'healthy':
                health['overall'] = 'degraded'
        except Exception as e:
            health['memory'] = 'unhealthy'
            health['overall'] = 'unhealthy'
            self.logger.error(f"Memory cache health check failed: {e}")

        return health

    def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries.

        Returns:
            Number of entries cleaned up
        """
        cleaned_count = 0

        try:
            # Clean memory cache
            memory_cleaned = self.memory_cache.cleanup_expired()
            cleaned_count += memory_cleaned
            self.logger.info("Memory cache cleanup completed", cleaned_count=memory_cleaned)

            # Redis handles TTL automatically, but we can still check
            if self.redis_client:
                try:
                    redis_cleaned = self.redis_client.cleanup_expired()
                    cleaned_count += redis_cleaned
                    self.logger.info("Redis cleanup completed", cleaned_count=redis_cleaned)
                except Exception as e:
                    self.logger.debug(f"Redis cleanup error: {e}")

        except Exception as e:
            self.logger.error(f"Cache cleanup operation failed: {e}")

        return cleaned_count


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    Get global cache manager instance.

    Returns:
        CacheManager instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def reset_cache_manager():
    """Reset global cache manager instance."""
    global _cache_manager
    _cache_manager = None
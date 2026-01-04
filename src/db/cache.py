"""
Data Access Cache Manager

Provides caching functionality for database queries using Redis.
"""

import hashlib
import json
import logging
import pickle
from functools import wraps
from typing import Any, Optional, Callable, TypeVar

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheManager:
    """Redis-based cache manager for database queries"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 3600,
        key_prefix: str = "cbsc_cache"
    ):
        """
        Initialize cache manager.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live in seconds
            key_prefix: Prefix for all cache keys
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self._redis_client = None

    @property
    def redis_client(self):
        """Lazy load Redis client"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, caching disabled")
            return None

        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=False,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                # Test connection
                self._redis_client.ping()
                logger.info("Redis cache connected")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._redis_client = None

        return self._redis_client

    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_hash = hashlib.md5(
            json.dumps(key_data, sort_keys=True, default=str).encode()
        ).hexdigest()
        return f"{self.key_prefix}:{prefix}:{key_hash}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached data.

        Args:
            key: Cache key

        Returns:
            Cached data or None
        """
        if not self.redis_client:
            return None

        try:
            data = self.redis_client.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ) -> bool:
        """
        Set cached data.

        Args:
            key: Cache key
            value: Data to cache
            ttl: Time-to-live in seconds

        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            ttl = ttl or self.default_ttl
            data = pickle.dumps(value)
            return self.redis_client.setex(key, ttl, data)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete cached data.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern.

        Args:
            pattern: Key pattern to match

        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0

        try:
            keys = self.redis_client.keys(f"{self.key_prefix}:{pattern}*")
            if keys:
                return self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
        return 0

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False

    def health_check(self) -> dict:
        """
        Check cache health.

        Returns:
            Health status dict
        """
        if not self.redis_client:
            return {
                "status": "disabled",
                "message": "Redis not available"
            }

        try:
            start_time = time.time()
            self.redis_client.ping()
            latency = (time.time() - start_time) * 1000

            info = self.redis_client.info()
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "memory_used": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "uptime_days": info.get("uptime_in_days")
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def flush_all(self) -> bool:
        """Clear all cached data with the key prefix"""
        if not self.redis_client:
            return False

        try:
            keys = self.redis_client.keys(f"{self.key_prefix}:*")
            if keys:
                self.redis_client.delete(*keys)
            logger.info(f"Flushed {len(keys)} cache entries")
            return True
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False


import time


def cached(
    prefix: str,
    ttl: int = 3600,
    cache_manager: CacheManager = None
):
    """
    Decorator for caching function results.

    Args:
        prefix: Cache key prefix
        ttl: Time-to-live in seconds
        cache_manager: CacheManager instance (uses default if None)

    Example:
        @cached("strategy_by_id", ttl=1800)
        def get_strategy(strategy_id: str):
            return db.query(Strategy).get(strategy_id)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Use provided cache manager or default
            cm = cache_manager or CacheManager()

            # Generate cache key
            cache_key = cm._make_key(prefix, func.__name__, *args, **kwargs)

            # Try to get from cache
            cached_result = cm.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cm.set(cache_key, result, ttl)
            logger.debug(f"Cache miss: {cache_key}")
            return result

        # Add cache management methods to wrapper
        wrapper.cache_clear = lambda: cm.clear_pattern(f"{prefix}:*")
        wrapper.cache_key_prefix = prefix

        return wrapper

    return decorator


class CachedRepositoryMixin:
    """Mixin class for adding caching to repositories"""

    def __init__(self, *args, cache_manager: CacheManager = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_manager = cache_manager or CacheManager()

    def _cache_key(self, operation: str, *args, **kwargs) -> str:
        """Generate cache key for repository operation"""
        model_name = self.model.__name__.lower()
        return self.cache_manager._make_key(
            f"{model_name}:{operation}",
            *args,
            **kwargs
        )

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get data from cache"""
        return self.cache_manager.get(key)

    def _set_cached(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set data in cache"""
        return self.cache_manager.set(key, value, ttl)

    def _delete_cached(self, key: str) -> bool:
        """Delete data from cache"""
        return self.cache_manager.delete(key)

    def _clear_model_cache(self):
        """Clear all cache entries for this model"""
        model_name = self.model.__name__.lower()
        self.cache_manager.clear_pattern(f"{model_name}:*")


# Global cache manager instance
_global_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager()
    return _global_cache_manager


def init_cache(
    redis_url: str = "redis://localhost:6379/0",
    default_ttl: int = 3600,
    key_prefix: str = "cbsc_cache"
) -> CacheManager:
    """
    Initialize global cache manager.

    Args:
        redis_url: Redis connection URL
        default_ttl: Default time-to-live in seconds
        key_prefix: Prefix for all cache keys

    Returns:
        CacheManager instance
    """
    global _global_cache_manager
    _global_cache_manager = CacheManager(
        redis_url=redis_url,
        default_ttl=default_ttl,
        key_prefix=key_prefix
    )
    return _global_cache_manager

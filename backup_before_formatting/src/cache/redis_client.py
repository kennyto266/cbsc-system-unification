"""
Redis Client Wrapper
Redis 客戶端包裝器
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from ..core.logging import get_logger
from ..core.exceptions import ResourceError


class RedisClient:
    """
    Redis client wrapper with error handling and fallback mechanisms
    Redis 客戶端包裝器，包含錯誤處理和降級機制
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        ssl: bool = False,
        socket_timeout: int = 5,
        retry_on_timeout: bool = True,
        max_connections: int = 20
    ):
        """
        Initialize Redis client.

        Args:
            host: Redis server host
            port: Redis server port
            db: Database number
            password: Redis password
            ssl: Enable SSL connection
            socket_timeout: Socket timeout in seconds
            retry_on_timeout: Retry on timeout
            max_connections: Maximum connection pool size
        """
        if not REDIS_AVAILABLE:
            raise ResourceError("Redis is not available. Install redis-py package.")

        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.ssl = ssl
        self.logger = get_logger("cache.redis")

        # Connection statistics
        self.stats = {
            'connections': 0,
            'errors': 0,
            'operations': 0,
            'last_error': None,
            'last_error_time': None
        }

        # Initialize Redis client
        self.client = self._create_client()
        self._test_connection()

    def _create_client(self) -> redis.Redis:
        """Create Redis client with connection pooling."""
        try:
            pool = redis.ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                ssl=self.ssl,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=20,
                decode_responses=True
            )

            client = redis.Redis(
                connection_pool=pool,
                decode_responses=True
            )

            self.stats['connections'] += 1
            self.logger.info(
                "Redis client created",
                host=self.host,
                port=self.port,
                db=self.db,
                ssl=self.ssl
            )

            return client

        except Exception as e:
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            self.stats['last_error_time'] = datetime.now().isoformat()

            self.logger.error(
                "Failed to create Redis client",
                host=self.host,
                port=self.port,
                error=str(e)
            )

            raise ResourceError(f"Failed to create Redis client: {e}")

    def _test_connection(self) -> bool:
        """Test Redis connection."""
        try:
            self.client.ping()
            self.logger.info("Redis connection test successful")
            return True
        except Exception as e:
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            self.stats['last_error_time'] = datetime.now().isoformat()

            self.logger.error(f"Redis connection test failed: {e}")
            raise ResourceError(f"Redis connection failed: {e}")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis.

        Args:
            key: Redis key

        Returns:
            Stored value or None if key doesn't exist
        """
        try:
            self.stats['operations'] += 1

            value = self.client.get(key)
            if value is not None:
                # Try to deserialize JSON
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value

            return None

        except Exception as e:
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            self.stats['last_error_time'] = datetime.now().isoformat()

            self.logger.debug(f"Redis get error: {e}", key=key)
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Set value in Redis.

        Args:
            key: Redis key
            value: Value to store
            ttl: Time to live in seconds
            tags: Optional tags for cache invalidation

        Returns:
            True if successful, False otherwise
        """
        try:
            self.stats['operations'] += 1

            # Serialize value
            if not isinstance(value, str):
                value = json.dumps(value, default=str)

            # Set with or without TTL
            if ttl is not None:
                result = self.client.setex(key, ttl, value)
            else:
                result = self.client.set(key, value)

            # Store tags if provided
            if tags:
                self._store_tags(key, tags)

            return bool(result)

        except Exception as e:
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            self.stats['last_error_time'] = datetime.now().isoformat()

            self.logger.debug(f"Redis set error: {e}", key=key)
            return False

    def _store_tags(self, key: str, tags: List[str]):
        """Store tags for a key."""
        try:
            for tag in tags:
                tag_key = f"tag:{tag}"
                self.client.sadd(tag_key, key)
                # Set TTL for tag key
                self.client.expire(tag_key, 86400)  # 24 hours
        except Exception as e:
            self.logger.debug(f"Failed to store tags: {e}", key=key, tags=tags)

    def delete(self, key: str) -> bool:
        """
        Delete key from Redis.

        Args:
            key: Redis key to delete

        Returns:
            True if key was deleted, False otherwise
        """
        try:
            self.stats['operations'] += 1

            # Remove tags first
            self._remove_tags(key)

            # Delete the key
            result = self.client.delete(key)
            return bool(result)

        except Exception as e:
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            self.stats['last_error_time'] = datetime.now().isoformat()

            self.logger.debug(f"Redis delete error: {e}", key=key)
            return False

    def _remove_tags(self, key: str):
        """Remove tags for a key."""
        try:
            # Find all tags that contain this key
            tag_keys = self.client.keys("tag:*")
            for tag_key in tag_keys:
                self.client.srem(tag_key, key)
        except Exception as e:
            self.logger.debug(f"Failed to remove tags: {e}", key=key)

    def delete_by_pattern(self, pattern: str) -> int:
        """
        Delete keys matching pattern.

        Args:
            pattern: Pattern to match keys

        Returns:
            Number of keys deleted
        """
        try:
            self.stats['operations'] += 1

            keys = self.client.keys(f"*{pattern}*")
            if keys:
                # Remove tags for all keys
                for key in keys:
                    self._remove_tags(key)

                # Delete keys
                return self.client.delete(*keys)

            return 0

        except Exception as e:
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            self.stats['last_error_time'] = datetime.now().isoformat()

            self.logger.debug(f"Redis pattern delete error: {e}", pattern=pattern)
            return 0

    def delete_by_tags(self, tags: List[str]) -> int:
        """
        Delete keys by tags.

        Args:
            tags: List of tags to match

        Returns:
            Number of keys deleted
        """
        try:
            self.stats['operations'] += 1

            # Collect all keys with the specified tags
            all_keys: Set[str] = set()
            for tag in tags:
                tag_key = f"tag:{tag}"
                keys = self.client.smembers(tag_key)
                all_keys.update(keys)
                # Clean up tag set
                self.client.delete(tag_key)

            if all_keys:
                # Delete all matching keys
                return self.client.delete(*all_keys)

            return 0

        except Exception as e:
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            self.stats['last_error_time'] = datetime.now().isoformat()

            self.logger.debug(f"Redis tag delete error: {e}", tags=tags)
            return 0

    def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis.

        Args:
            key: Redis key to check

        Returns:
            True if key exists, False otherwise
        """
        try:
            self.stats['operations'] += 1
            return bool(self.client.exists(key))
        except Exception as e:
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            self.stats['last_error_time'] = datetime.now().isoformat()

            self.logger.debug(f"Redis exists error: {e}", key=key)
            return False

    def clear_all(self) -> bool:
        """
        Clear all keys in current database.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.stats['operations'] += 1
            self.client.flushdb()
            self.logger.info("Redis database cleared")
            return True
        except Exception as e:
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            self.stats['last_error_time'] = datetime.now().isoformat()

            self.logger.error(f"Redis clear error: {e}")
            return False

    def cleanup_expired(self) -> int:
        """
        Clean up expired keys.

        Note: Redis handles TTL automatically, but we can still check
        for any orphaned tag keys.

        Returns:
            Number of keys cleaned up
        """
        try:
            self.stats['operations'] += 1

            # Clean up empty tag sets
            tag_keys = self.client.keys("tag:*")
            cleaned_count = 0

            for tag_key in tag_keys:
                if not self.client.exists(tag_key):
                    continue

                # Check if tag set is empty
                if not self.client.smembers(tag_key):
                    self.client.delete(tag_key)
                    cleaned_count += 1

            if cleaned_count > 0:
                self.logger.info("Cleaned up empty tag sets", count=cleaned_count)

            return cleaned_count

        except Exception as e:
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            self.stats['last_error_time'] = datetime.now().isoformat()

            self.logger.debug(f"Redis cleanup error: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get Redis client statistics.

        Returns:
            Dictionary with statistics
        """
        try:
            # Get Redis info
            redis_info = self.client.info() if self.client else {}

            stats = self.stats.copy()
            stats.update({
                'redis_info': {
                    'used_memory': redis_info.get('used_memory_human', 'N/A'),
                    'connected_clients': redis_info.get('connected_clients', 0),
                    'total_commands_processed': redis_info.get('total_commands_processed', 0),
                    'keyspace_hits': redis_info.get('keyspace_hits', 0),
                    'keyspace_misses': redis_info.get('keyspace_misses', 0),
                },
                'server': {
                    'host': self.host,
                    'port': self.port,
                    'db': self.db,
                    'ssl': self.ssl
                }
            })

            # Calculate hit rate if Redis info available
            hits = redis_info.get('keyspace_hits', 0)
            misses = redis_info.get('keyspace_misses', 0)
            total = hits + misses
            if total > 0:
                stats['hit_rate'] = round((hits / total) * 100, 2)
            else:
                stats['hit_rate'] = 0

            return stats

        except Exception as e:
            self.logger.debug(f"Failed to get Redis stats: {e}")
            return self.stats.copy()

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Redis connection.

        Returns:
            Health check results
        """
        try:
            # Test connection
            start_time = time.time()
            self.client.ping()
            response_time = round((time.time() - start_time) * 1000, 2)  # ms

            # Get basic info
            info = self.client.info()

            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', 'N/A'),
                'uptime_seconds': info.get('uptime_in_seconds', 0)
            }

        except Exception as e:
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            self.stats['last_error_time'] = datetime.now().isoformat()

            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_error_time': self.stats['last_error_time']
            }

    def close(self):
        """Close Redis connection."""
        try:
            if hasattr(self.client, 'close'):
                self.client.close()
            self.logger.info("Redis connection closed")
        except Exception as e:
            self.logger.debug(f"Error closing Redis connection: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
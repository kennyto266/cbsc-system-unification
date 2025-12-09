"""
Memory Cache Implementation
內存緩存實現
"""

import json
import time
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from ..core.logging import get_logger


class MemoryCache:
    """
    Thread-safe in-memory cache with TTL and tag support
    線程安全的內存緩存，支持 TTL 和標籤
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize memory cache.

        Args:
            max_size: Maximum number of items to cache
        """
        self.max_size = max_size
        self.logger = get_logger("cache.memory")

        # Thread lock for thread safety
        self._lock = threading.RLock()

        # Cache storage
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._tags: Dict[str, Set[str]] = {}

        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0,
            'errors': 0,
            'current_size': 0,
            'peak_size': 0
        }

        self.logger.info("Memory cache initialized", max_size=max_size)

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        try:
            with self._lock:
                if key not in self._cache:
                    self.stats['misses'] += 1
                    return None

                item = self._cache[key]

                # Check expiration
                if time.time() > item['expires']:
                    del self._cache[key]
                    # Remove from tags
                    self._remove_from_tags(key)
                    self.stats['misses'] += 1
                    self.logger.debug("Cache item expired", key=key)
                    return None

                self.stats['hits'] += 1
                self.logger.debug("Cache hit", key=key)

                # Update last access time
                item['last_accessed'] = time.time()

                return item['data']

        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Memory cache get error: {e}", key=key)
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            tags: Optional tags for cache invalidation

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                current_time = time.time()
                expires = current_time + ttl

                # Check if we need to evict items
                if len(self._cache) >= self.max_size and key not in self._cache:
                    self._evict_items()

                # Store the item
                self._cache[key] = {
                    'data': value,
                    'created': current_time,
                    'expires': expires,
                    'last_accessed': current_time,
                    'ttl': ttl,
                    'tags': tags or []
                }

                # Update tags
                if tags:
                    self._add_to_tags(key, tags)

                self.stats['sets'] += 1
                self.stats['current_size'] = len(self._cache)
                self.stats['peak_size'] = max(self.stats['peak_size'], len(self._cache))

                self.logger.debug(
                    "Item cached",
                    key=key,
                    ttl=ttl,
                    size=len(self._cache)
                )

                return True

        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Memory cache set error: {e}", key=key)
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False otherwise
        """
        try:
            with self._lock:
                if key in self._cache:
                    del self._cache[key]
                    self._remove_from_tags(key)
                    self.stats['deletes'] += 1
                    self.stats['current_size'] = len(self._cache)
                    self.logger.debug("Item deleted", key=key)
                    return True
                return False

        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Memory cache delete error: {e}", key=key)
            return False

    def delete_by_pattern(self, pattern: str) -> int:
        """
        Delete keys matching pattern.

        Args:
            pattern: Pattern to match keys

        Returns:
            Number of keys deleted
        """
        try:
            with self._lock:
                keys_to_delete = [
                    key for key in self._cache.keys()
                    if pattern in key
                ]

                for key in keys_to_delete:
                    del self._cache[key]
                    self._remove_from_tags(key)

                deleted_count = len(keys_to_delete)
                self.stats['deletes'] += deleted_count
                self.stats['current_size'] = len(self._cache)

                if deleted_count > 0:
                    self.logger.info(
                        "Items deleted by pattern",
                        pattern=pattern,
                        count=deleted_count
                    )

                return deleted_count

        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Memory cache pattern delete error: {e}", pattern=pattern)
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
            with self._lock:
                # Collect all keys with the specified tags
                keys_to_delete: Set[str] = set()
                for tag in tags:
                    if tag in self._tags:
                        keys_to_delete.update(self._tags[tag])

                # Delete the keys
                deleted_count = 0
                for key in keys_to_delete:
                    if key in self._cache:
                        del self._cache[key]
                        deleted_count += 1

                # Clean up tag references
                for tag in tags:
                    if tag in self._tags:
                        del self._tags[tag]

                self.stats['deletes'] += deleted_count
                self.stats['current_size'] = len(self._cache)

                if deleted_count > 0:
                    self.logger.info(
                        "Items deleted by tags",
                        tags=tags,
                        count=deleted_count
                    )

                return deleted_count

        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Memory cache tag delete error: {e}", tags=tags)
            return 0

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists and is not expired, False otherwise
        """
        try:
            with self._lock:
                if key not in self._cache:
                    return False

                item = self._cache[key]
                if time.time() > item['expires']:
                    del self._cache[key]
                    self._remove_from_tags(key)
                    return False

                return True

        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Memory cache exists error: {e}", key=key)
            return False

    def clear_all(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                cleared_count = len(self._cache)
                self._cache.clear()
                self._tags.clear()

                self.stats['current_size'] = 0
                self.logger.info("Memory cache cleared", count=cleared_count)
                return True

        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Memory cache clear error: {e}")
            return False

    def cleanup_expired(self) -> int:
        """
        Clean up expired entries.

        Returns:
            Number of entries cleaned up
        """
        try:
            with self._lock:
                current_time = time.time()
                expired_keys = [
                    key for key, item in self._cache.items()
                    if current_time > item['expires']
                ]

                for key in expired_keys:
                    del self._cache[key]
                    self._remove_from_tags(key)

                cleaned_count = len(expired_keys)
                self.stats['current_size'] = len(self._cache)

                if cleaned_count > 0:
                    self.logger.info("Expired items cleaned up", count=cleaned_count)

                return cleaned_count

        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Memory cache cleanup error: {e}")
            return 0

    def _add_to_tags(self, key: str, tags: List[str]):
        """Add key to tag sets."""
        for tag in tags:
            if tag not in self._tags:
                self._tags[tag] = set()
            self._tags[tag].add(key)

    def _remove_from_tags(self, key: str):
        """Remove key from all tag sets."""
        # Find which tags contain this key
        tags_to_remove_from = []
        for tag, keys in self._tags.items():
            if key in keys:
                tags_to_remove_from.append(tag)

        # Remove from each tag
        for tag in tags_to_remove_from:
            self._tags[tag].discard(key)
            if not self._tags[tag]:  # Remove empty tag sets
                del self._tags[tag]

    def _evict_items(self):
        """Evict least recently used items to make space."""
        if not self._cache:
            return

        # Sort items by last accessed time
        sorted_items = sorted(
            self._cache.items(),
            key=lambda x: x[1]['last_accessed']
        )

        # Evict oldest 20% of items
        evict_count = max(1, len(self._cache) // 5)
        evicted_keys = [key for key, _ in sorted_items[:evict_count]]

        for key in evicted_keys:
            del self._cache[key]
            self._remove_from_tags(key)

        self.stats['evictions'] += len(evicted_keys)
        self.stats['current_size'] = len(self._cache)

        self.logger.info(
            "Items evicted due to size limit",
            count=len(evicted_keys),
            max_size=self.max_size
        )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory cache statistics.

        Returns:
            Dictionary with statistics
        """
        with self._lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

            return {
                'hit_rate': round(hit_rate, 2),
                'total_requests': total_requests,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'sets': self.stats['sets'],
                'deletes': self.stats['deletes'],
                'evictions': self.stats['evictions'],
                'errors': self.stats['errors'],
                'current_size': self.stats['current_size'],
                'peak_size': self.stats['peak_size'],
                'max_size': self.max_size,
                'tags_count': len(self._tags)
            }

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on memory cache.

        Returns:
            Health check results
        """
        try:
            with self._lock:
                # Test basic operations
                test_key = f"health_check_{int(time.time())}"
                test_value = {"test": True, "timestamp": time.time()}

                # Test set
                self.set(test_key, test_value, ttl=10)

                # Test get
                retrieved = self.get(test_key)

                # Test delete
                deleted = self.delete(test_key)

                # Check memory usage
                memory_usage = self._estimate_memory_usage()

                status = {
                    'status': 'healthy' if retrieved and deleted else 'unhealthy',
                    'operations_test': 'passed' if retrieved and deleted else 'failed',
                    'current_size': self.stats['current_size'],
                    'max_size': self.max_size,
                    'memory_usage_bytes': memory_usage,
                    'error_count': self.stats['errors']
                }

                return status

        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'error_count': self.stats['errors']
            }

    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage in bytes."""
        try:
            import sys

            total_size = 0

            # Cache items
            for key, item in self._cache.items():
                total_size += sys.getsizeof(key)
                total_size += sys.getsizeof(item)
                total_size += sys.getsizeof(item.get('data'))

            # Tags
            for tag, keys in self._tags.items():
                total_size += sys.getsizeof(tag)
                total_size += sys.getsizeof(keys)

            return total_size

        except Exception:
            return -1  # Unable to calculate

    def get_keys(self, pattern: Optional[str] = None) -> List[str]:
        """
        Get list of all keys or keys matching pattern.

        Args:
            pattern: Optional pattern to filter keys

        Returns:
            List of keys
        """
        try:
            with self._lock:
                keys = list(self._cache.keys())
                if pattern:
                    keys = [key for key in keys if pattern in key]
                return keys

        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Memory cache get keys error: {e}", pattern=pattern)
            return []

    def get_tags(self) -> List[str]:
        """
        Get list of all tags.

        Returns:
            List of tags
        """
        try:
            with self._lock:
                return list(self._tags.keys())

        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Memory cache get tags error: {e}")
            return []
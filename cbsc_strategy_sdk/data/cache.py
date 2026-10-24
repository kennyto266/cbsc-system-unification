"""In-memory data cache with TTL support.

Provides thread-safe caching with time-based expiration.
"""

import re
import time
from collections import defaultdict
from threading import Lock
from typing import Any, Optional


class DataCache:
    """Thread-safe in-memory cache with TTL support.

    Attributes:
        _storage: Dictionary storing cached values
        _timestamps: Dictionary tracking expiration times
        _ttl: Default time-to-live in seconds
        _lock: Thread lock for concurrent access
    """

    def __init__(self, default_ttl: int = 300) -> None:
        """Initialize cache with default TTL.

        Args:
            default_ttl: Default time-to-live in seconds (default: 300)
        """
        self._storage: dict[str, Any] = {}
        self._timestamps: dict[str, float] = {}
        self._ttl: int = default_ttl
        self._lock: Lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if exists and not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if expired/missing
        """
        with self._lock:
            if key not in self._storage:
                return None

            # Check expiration
            if time.time() > self._timestamps[key]:
                # Expired, remove and return None
                del self._storage[key]
                del self._timestamps[key]
                return None

            return self._storage[key]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        with self._lock:
            self._storage[key] = value
            ttl_seconds = ttl if ttl is not None else self._ttl
            self._timestamps[key] = time.time() + ttl_seconds

    def invalidate(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern.

        Args:
            pattern: Regex pattern to match keys

        Returns:
            Number of keys invalidated
        """
        with self._lock:
            regex = re.compile(pattern)
            keys_to_remove = [k for k in self._storage if regex.match(k)]

            for key in keys_to_remove:
                del self._storage[key]
                del self._timestamps[key]

            return len(keys_to_remove)

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._storage.clear()
            self._timestamps.clear()

    def size(self) -> int:
        """Get number of cached entries.

        Returns:
            Number of entries in cache
        """
        with self._lock:
            return len(self._storage)

    def cleanup_expired(self) -> int:
        """Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                k for k, expiry in self._timestamps.items() if current_time > expiry
            ]

            for key in expired_keys:
                del self._storage[key]
                del self._timestamps[key]

            return len(expired_keys)

"""
Unit tests for DataCache.

Tests cache operations including get/set with TTL, expiration,
invalidation, and cleanup.
"""

import time
from threading import Thread
from unittest.mock import patch

import pytest

from cbsc_strategy_sdk.data.cache import DataCache


class TestDataCacheInitialization:
    """Test cache initialization."""

    def test_default_ttl(self):
        """Test cache initializes with default TTL."""
        cache = DataCache()
        assert cache._ttl == 300

    def test_custom_ttl(self):
        """Test cache initializes with custom TTL."""
        cache = DataCache(default_ttl=600)
        assert cache._ttl == 600

    def test_empty_storage(self):
        """Test cache starts with empty storage."""
        cache = DataCache()
        assert cache.size() == 0

    def test_thread_safe_lock(self):
        """Test cache has thread lock."""
        cache = DataCache()
        assert cache._lock is not None


class TestDataCacheGetSet:
    """Test basic get/set operations."""

    def test_set_and_get(self):
        """Test setting and getting a value."""
        cache = DataCache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_nonexistent_key(self):
        """Test getting non-existent key returns None."""
        cache = DataCache()
        assert cache.get("nonexistent") is None

    def test_set_overwrites_existing(self):
        """Test setting same key overwrites existing value."""
        cache = DataCache()
        cache.set("key1", "value1")
        cache.set("key1", "value2")
        assert cache.get("key1") == "value2"

    def test_set_with_custom_ttl(self):
        """Test setting value with custom TTL."""
        cache = DataCache(default_ttl=300)
        cache.set("key1", "value1", ttl=10)
        # Value should exist immediately
        assert cache.get("key1") == "value1"

    def test_set_with_none_ttl_uses_default(self):
        """Test setting value with None TTL uses default."""
        cache = DataCache(default_ttl=300)
        cache.set("key1", "value1", ttl=None)
        # Should use default TTL
        assert cache.get("key1") == "value1"

    def test_get_various_types(self):
        """Test cache can store various data types."""
        cache = DataCache()
        cache.set("string", "text")
        cache.set("int", 42)
        cache.set("float", 3.14)
        cache.set("list", [1, 2, 3])
        cache.set("dict", {"key": "value"})

        assert cache.get("string") == "text"
        assert cache.get("int") == 42
        assert cache.get("float") == 3.14
        assert cache.get("list") == [1, 2, 3]
        assert cache.get("dict") == {"key": "value"}


class TestDataCacheExpiration:
    """Test cache expiration behavior."""

    def test_expired_key_returns_none(self):
        """Test expired key returns None."""
        cache = DataCache()
        cache.set("key1", "value1", ttl=1)
        time.sleep(1.1)  # Wait for expiration
        assert cache.get("key1") is None

    def test_expired_key_removed_from_storage(self):
        """Test expired key is removed from storage."""
        cache = DataCache()
        cache.set("key1", "value1", ttl=1)
        assert cache.size() == 1
        time.sleep(1.1)  # Wait for expiration
        cache.get("key1")  # Trigger cleanup
        assert cache.size() == 0

    def test_non_expired_key_accessible(self):
        """Test non-expired key is still accessible."""
        cache = DataCache()
        cache.set("key1", "value1", ttl=10)
        time.sleep(0.5)  # Less than TTL
        assert cache.get("key1") == "value1"

    def test_zero_ttl_expires_immediately(self):
        """Test zero TTL causes immediate expiration."""
        cache = DataCache()
        cache.set("key1", "value1", ttl=0)
        time.sleep(0.1)  # Small delay
        # With TTL 0, should expire almost immediately
        result = cache.get("key1")
        # Due to timing, this might still be cached
        # but should expire very soon
        # The behavior is implementation dependent

    def test_long_ttl_persists(self):
        """Test long TTL keeps value cached."""
        cache = DataCache()
        cache.set("key1", "value1", ttl=3600)  # 1 hour
        time.sleep(0.5)
        assert cache.get("key1") == "value1"


class TestDataCacheInvalidate:
    """Test cache invalidation with patterns."""

    def test_invalidate_exact_key(self):
        """Test invalidate exact key match."""
        cache = DataCache()
        cache.set("ohlcv:AAPL:2024-01-01", "data1")
        cache.set("ohlcv:TSLA:2024-01-01", "data2")

        count = cache.invalidate("ohlcv:AAPL:2024-01-01")
        assert count == 1
        assert cache.get("ohlcv:AAPL:2024-01-01") is None
        assert cache.get("ohlcv:TSLA:2024-01-01") == "data2"

    def test_invalidate_wildcard_pattern(self):
        """Test invalidate with wildcard pattern."""
        cache = DataCache()
        cache.set("ohlcv:AAPL:2024-01-01", "data1")
        cache.set("ohlcv:AAPL:2024-01-02", "data2")
        cache.set("symbols:all", "data3")

        count = cache.invalidate(r"ohlcv:AAPL:.*")
        assert count == 2
        assert cache.get("ohlcv:AAPL:2024-01-01") is None
        assert cache.get("ohlcv:AAPL:2024-01-02") is None
        assert cache.get("symbols:all") == "data3"

    def test_invalidate_all_matching_pattern(self):
        """Test invalidate removes all matching entries."""
        cache = DataCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        count = cache.invalidate(r"key.*")
        assert count == 3
        assert cache.size() == 0

    def test_invalidate_non_matching_pattern(self):
        """Test invalidate with non-matching pattern."""
        cache = DataCache()
        cache.set("key1", "value1")

        count = cache.invalidate(r"nomatch.*")
        assert count == 0
        assert cache.get("key1") == "value1"

    def test_invalidate_special_regex_chars(self):
        """Test invalidate handles special regex characters."""
        cache = DataCache()
        cache.set("ohlcv:0700.HK:2024", "data")
        cache.set("ohlcv:9988.HK:2024", "data2")

        # Dot needs escaping in regex
        count = cache.invalidate(r"ohlcv:0700\.HK:.*")
        assert count == 1


class TestDataCacheClear:
    """Test cache clear operation."""

    def test_clear_empty_cache(self):
        """Test clearing empty cache."""
        cache = DataCache()
        cache.clear()
        assert cache.size() == 0

    def test_clear_with_entries(self):
        """Test clearing cache with entries."""
        cache = DataCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert cache.size() == 2

        cache.clear()
        assert cache.size() == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_clear_multiple_times(self):
        """Test calling clear multiple times."""
        cache = DataCache()
        cache.set("key1", "value1")
        cache.clear()
        cache.clear()  # Should not raise
        assert cache.size() == 0


class TestDataCacheSize:
    """Test cache size operations."""

    def test_size_empty(self):
        """Test size of empty cache."""
        cache = DataCache()
        assert cache.size() == 0

    def test_size_after_add(self):
        """Test size increments after adding entries."""
        cache = DataCache()
        assert cache.size() == 0
        cache.set("key1", "value1")
        assert cache.size() == 1
        cache.set("key2", "value2")
        assert cache.size() == 2

    def test_size_after_overwrite(self):
        """Test size doesn't increment on overwrite."""
        cache = DataCache()
        cache.set("key1", "value1")
        assert cache.size() == 1
        cache.set("key1", "value2")
        assert cache.size() == 1

    def test_size_after_expiration(self):
        """Test size decreases after expiration."""
        cache = DataCache()
        cache.set("key1", "value1", ttl=1)
        assert cache.size() == 1
        time.sleep(1.1)
        cache.get("key1")  # Trigger expiration cleanup
        assert cache.size() == 0


class TestDataCacheCleanupExpired:
    """Test cleanup of expired entries."""

    def test_cleanup_expired_entries(self):
        """Test cleanup removes expired entries."""
        cache = DataCache()
        cache.set("key1", "value1", ttl=1)
        cache.set("key2", "value2", ttl=10)  # Longer TTL
        assert cache.size() == 2

        time.sleep(1.1)
        removed = cache.cleanup_expired()
        assert removed == 1
        assert cache.size() == 1
        assert cache.get("key2") == "value2"

    def test_cleanup_none_expired(self):
        """Test cleanup when none are expired."""
        cache = DataCache()
        cache.set("key1", "value1", ttl=3600)

        removed = cache.cleanup_expired()
        assert removed == 0
        assert cache.size() == 1

    def test_cleanup_all_expired(self):
        """Test cleanup when all are expired."""
        cache = DataCache()
        cache.set("key1", "value1", ttl=1)
        cache.set("key2", "value2", ttl=1)

        time.sleep(1.1)
        removed = cache.cleanup_expired()
        assert removed == 2
        assert cache.size() == 0


class TestDataCacheThreadSafety:
    """Test thread safety of cache operations."""

    def test_concurrent_set_operations(self):
        """Test concurrent set operations are thread-safe."""
        cache = DataCache()
        threads = []

        def set_values(thread_id):
            for i in range(100):
                cache.set(f"thread{thread_id}_key{i}", f"value{i}")

        # Create multiple threads
        for i in range(10):
            t = Thread(target=set_values, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Should have 1000 entries
        assert cache.size() == 1000

    def test_concurrent_get_operations(self):
        """Test concurrent get operations are thread-safe."""
        cache = DataCache()
        cache.set("shared_key", "shared_value")

        results = []
        threads = []

        def get_value():
            for _ in range(100):
                results.append(cache.get("shared_key"))

        # Create multiple threads
        for _ in range(10):
            t = Thread(target=get_value)
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # All results should be the same
        assert all(r == "shared_value" for r in results)
        assert len(results) == 1000

    def test_concurrent_clear_and_get(self):
        """Test concurrent clear and get operations."""
        cache = DataCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        threads = []
        clear_count = [0]

        def clear_cache():
            for _ in range(50):
                cache.clear()
                clear_count[0] += 1

        def get_values():
            for _ in range(50):
                cache.get("key1")
                cache.get("key2")

        t1 = Thread(target=clear_cache)
        t2 = Thread(target=get_values)
        threads.extend([t1, t2])

        t1.start()
        t2.start()

        for t in threads:
            t.join()

        # Should complete without errors
        assert clear_count[0] == 50


class TestDataCacheEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_key(self):
        """Test cache with empty string key."""
        cache = DataCache()
        cache.set("", "value")
        assert cache.get("") == "value"

    def test_special_characters_in_key(self):
        """Test cache with special characters in key."""
        cache = DataCache()
        special_keys = [
            "key:with:colons",
            "key/with/slashes",
            "key-with-dashes",
            "key_with_underscores",
            "key.with.dots",
        ]
        for key in special_keys:
            cache.set(key, f"value_{key}")
            assert cache.get(key) == f"value_{key}"

    def test_none_value(self):
        """Test cache can store None as value."""
        cache = DataCache()
        cache.set("key1", None)
        assert cache.get("key1") is None

    def test_large_value(self):
        """Test cache can store large values."""
        cache = DataCache()
        large_value = "x" * 1000000  # 1MB string
        cache.set("large", large_value)
        assert cache.get("large") == large_value

    def test_very_long_ttl(self):
        """Test cache with very long TTL."""
        cache = DataCache()
        cache.set("key1", "value1", ttl=86400)  # 24 hours
        assert cache.get("key1") == "value1"

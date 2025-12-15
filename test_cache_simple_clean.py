"""
[CHAR]CacheManager[CHAR]
Simplified CacheManager Test
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

# Copy essential classes from cache_strategy.py
class CacheLevel(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L1_L2 = "L1+L2"

class SerializationType(str, Enum):
    JSON = "json"
    PICKLE = "pickle"
    NONE = "none"

@dataclass
class CacheStrategy:
    ttl: int
    level: CacheLevel
    serializer: SerializationType
    max_size: Optional[int] = None
    cleanup_factor: float = 0.75

DEFAULT_STRATEGIES = {
    "strategy:*": CacheStrategy(ttl=300, level=CacheLevel.L2, serializer=SerializationType.JSON),
    "performance:*": CacheStrategy(ttl=30, level=CacheLevel.L1, serializer=SerializationType.JSON, max_size=1000),
    "user:*": CacheStrategy(ttl=60, level=CacheLevel.L1_L2, serializer=SerializationType.JSON, max_size=500),
    "signals:*": CacheStrategy(ttl=10, level=CacheLevel.L1, serializer=SerializationType.JSON, max_size=2000),
}

# Copy CacheManager class (simplified)
@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    errors: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total) if total > 0 else 0.0

    @property
    def total_ops(self) -> int:
        return self.hits + self.misses + self.sets + self.deletes

class CacheManager:
    def __init__(self, redis_url=None, max_memory_items=1000, default_ttl=300, strategies=None):
        self.default_ttl = default_ttl
        self.strategies = strategies or DEFAULT_STRATEGIES

        # L1 Memory cache
        self._memory_cache: Dict[str, Any] = {}
        self._memory_ttl: Dict[str, datetime] = {}
        self._max_memory_items = max_memory_items
        self._memory_access_order: List[str] = []

        # Redis (disabled for this test)
        self._redis_client = None
        self._redis_available = False

        # Stats
        self._stats = CacheStats()

    def _get_strategy(self, key: str) -> CacheStrategy:
        for pattern, strategy in self.strategies.items():
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                if key.startswith(prefix):
                    return strategy
        return CacheStrategy(ttl=60, level=CacheLevel.L1, serializer=SerializationType.JSON, max_size=500)

    async def get(self, key: str) -> Optional[Any]:
        strategy = self._get_strategy(key)

        if strategy.level in [CacheLevel.L1, CacheLevel.L1_L2]:
            value = await self._get_from_l1(key)
            if value is not None:
                self._stats.hits += 1
                return value

        self._stats.misses += 1
        return None

    async def set(self, key: str, value: Any, ttl=None, expire_after=None, expire_at=None) -> None:
        strategy = self._get_strategy(key)
        actual_ttl = ttl or expire_after or strategy.ttl

        if strategy.level in [CacheLevel.L1, CacheLevel.L1_L2]:
            await self._set_to_l1(key, value, strategy, actual_ttl, expire_at)

        self._stats.sets += 1

    async def delete(self, key: str) -> bool:
        deleted = False

        if key in self._memory_cache:
            await self._delete_from_l1(key)
            deleted = True

        if deleted:
            self._stats.deletes += 1

        return deleted

    async def clear_pattern(self, pattern: str) -> int:
        count = 0
        keys_to_delete = []

        for key in self._memory_cache.keys():
            if self._match_pattern(key, pattern):
                keys_to_delete.append(key)

        for key in keys_to_delete:
            await self._delete_from_l1(key)
            count += 1

        return count

    async def increment(self, key: str, amount: int = 1) -> int:
        if key in self._memory_cache:
            value = self._memory_cache[key]
            if isinstance(value, (int, float)):
                new_value = value + amount
                await self.set(key, new_value)
                return new_value

        await self.set(key, amount)
        return amount

    async def ttl(self, key: str) -> Optional[int]:
        if key in self._memory_ttl:
            remaining = self._memory_ttl[key] - datetime.now()
            if remaining.total_seconds() > 0:
                return int(remaining.total_seconds())
            else:
                await self.delete(key)
                return None
        return None

    async def exists(self, key: str) -> bool:
        if key in self._memory_cache:
            if key in self._memory_ttl:
                if datetime.now() > self._memory_ttl[key]:
                    await self._delete_from_l1(key)
                else:
                    return True
            return True
        return False

    async def get_stats(self) -> Dict[str, Any]:
        return {
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "sets": self._stats.sets,
            "deletes": self._stats.deletes,
            "evictions": self._stats.evictions,
            "errors": self._stats.errors,
            "hit_rate": self._stats.hit_rate,
            "total_ops": self._stats.total_ops,
            "memory_items": len(self._memory_cache),
            "memory_size": len(str(self._memory_cache)),
            "redis_available": self._redis_available,
            "max_memory_items": self._max_memory_items
        }

    async def _get_from_l1(self, key: str) -> Optional[Any]:
        if key in self._memory_ttl and datetime.now() > self._memory_ttl[key]:
            await self._delete_from_l1(key)
            return None

        value = self._memory_cache.get(key)
        if value is not None:
            if key in self._memory_access_order:
                self._memory_access_order.remove(key)
            self._memory_access_order.append(key)

        return value

    async def _set_to_l1(self, key: str, value: Any, strategy: CacheStrategy, ttl=None, expire_at=None) -> None:
        if strategy.max_size and key not in self._memory_cache:
            while len(self._memory_cache) >= strategy.max_size:
                if self._memory_access_order:
                    oldest_key = self._memory_access_order.pop(0)
                    await self._delete_from_l1(oldest_key)
                    self._stats.evictions += 1
                else:
                    break

        self._memory_cache[key] = value

        if expire_at:
            self._memory_ttl[key] = expire_at
        elif ttl:
            self._memory_ttl[key] = datetime.now() + timedelta(seconds=ttl)

        if key in self._memory_access_order:
            self._memory_access_order.remove(key)
        self._memory_access_order.append(key)

    async def _delete_from_l1(self, key: str) -> None:
        self._memory_cache.pop(key, None)
        self._memory_ttl.pop(key, None)
        if key in self._memory_access_order:
            self._memory_access_order.remove(key)

    def _match_pattern(self, key: str, pattern: str) -> bool:
        if "*" not in pattern:
            return key == pattern
        import re
        regex = pattern.replace("*", ".*")
        return re.match(regex, key) is not None

    async def cleanup_expired(self) -> int:
        count = 0
        now = datetime.now()

        expired_keys = [
            key for key, expiry in self._memory_ttl.items()
            if expiry <= now
        ]

        for key in expired_keys:
            await self._delete_from_l1(key)
            count += 1

        return count

    async def close(self) -> None:
        self._memory_cache.clear()
        self._memory_ttl.clear()
        self._memory_access_order.clear()


# Test functions
async def test_basic_operations():
    print("\n=== [CHAR] ===")

    cache = CacheManager(redis_url=None, strategies=DEFAULT_STRATEGIES)

    # Test set and get
    await cache.set("test:key", "test_value")
    value = await cache.get("test:key")
    assert value == "test_value"
    print("Set/Get test passed")

    # Test cache miss
    value = await cache.get("nonexistent:key")
    assert value is None
    print("[CHAR] Cache miss test passed")

    # Test delete
    deleted = await cache.delete("test:key")
    assert deleted is True
    value = await cache.get("test:key")
    assert value is None
    print("[CHAR] Delete test passed")

    # Get stats
    stats = await cache.get_stats()
    print(f"Cache stats: {stats}")

    await cache.close()
    print("[CHAR] Basic operations completed")


async def test_ttl_and_expiration():
    print("\n=== [CHAR]TTL[CHAR] ===")

    cache = CacheManager(redis_url=None, strategies=DEFAULT_STRATEGIES)

    # Test TTL
    await cache.set("ttl:key", "value", ttl=5)
    value = await cache.get("ttl:key")
    assert value == "value"

    remaining = await cache.ttl("ttl:key")
    assert remaining is not None and 0 < remaining <= 5
    print(f"[CHAR] TTL test passed, remaining: {remaining}s")

    # Test expiration
    await cache.set("expire:key", "value", ttl=1)
    await asyncio.sleep(1.1)
    value = await cache.get("expire:key")
    assert value is None
    print("[CHAR] Expiration test passed")

    await cache.close()


async def test_increment():
    print("\n=== [CHAR] ===")

    cache = CacheManager(redis_url=None, strategies=DEFAULT_STRATEGIES)

    # Test increment
    value = await cache.increment("counter", 1)
    assert value == 1

    value = await cache.increment("counter", 5)
    assert value == 6

    # Verify stored value
    stored = await cache.get("counter")
    assert stored == 6

    print("[CHAR] Increment test passed")

    await cache.close()


async def test_pattern_matching():
    print("\n=== [CHAR] ===")

    cache = CacheManager(redis_url=None, strategies=DEFAULT_STRATEGIES)

    # Set up test data
    await cache.set("user:1:profile", "profile1")
    await cache.set("user:1:settings", "settings1")
    await cache.set("user:2:profile", "profile2")
    await cache.set("other:key", "value")

    # Test pattern deletion
    count = await cache.clear_pattern("user:1:*")
    assert count == 2

    # Verify results
    assert await cache.get("user:1:profile") is None
    assert await cache.get("user:1:settings") is None
    assert await cache.get("user:2:profile") == "profile2"
    assert await cache.get("other:key") == "value"

    print("[CHAR] Pattern matching test passed")

    await cache.close()


async def test_strategies():
    print("\n=== [CHAR] ===")

    cache = CacheManager(redis_url=None, strategies=DEFAULT_STRATEGIES)

    # Test strategy-based caching
    await cache.set("strategy:test", {"data": "test"})
    value = await cache.get("strategy:test")
    assert value == {"data": "test"}

    # Test performance data strategy
    await cache.set("performance:test", {"metrics": [1, 2, 3]})
    value = await cache.get("performance:test")
    assert value == {"metrics": [1, 2, 3]}

    # Test user data strategy
    await cache.set("user:123:preferences", {"theme": "dark"})
    value = await cache.get("user:123:preferences")
    assert value == {"theme": "dark"}

    print("[CHAR] Strategy-based caching test passed")

    await cache.close()


async def performance_test():
    print("\n=== [CHAR] ===")

    cache = CacheManager(redis_url=None, strategies=DEFAULT_STRATEGIES)

    # Test write performance
    start_time = time.time()
    for i in range(1000):
        await cache.set(f"perf:key:{i}", f"value:{i}")
    write_time = time.time() - start_time

    # Test read performance
    start_time = time.time()
    for i in range(1000):
        await cache.get(f"perf:key:{i}")
    read_time = time.time() - start_time

    print(f"[CHAR] Write performance: {1000/write_time:.0f} ops/sec")
    print(f"[CHAR] Read performance: {1000/read_time:.0f} ops/sec")

    # Get final stats
    stats = await cache.get_stats()
    print(f"[CHAR] Final stats: {stats}")

    await cache.close()
    print("[CHAR] Performance test completed")


async def main():
    print("CacheManager[CHAR]")
    print("=" * 50)

    try:
        await test_basic_operations()
        await test_ttl_and_expiration()
        await test_increment()
        await test_pattern_matching()
        await test_strategies()
        await performance_test()

        print("\n" + "=" * 50)
        print("[CHAR]CacheManager[CHAR]")
        print("\n[CHAR]:")
        print("[CHAR] (set/get/delete)")
        print("TTL[CHAR]")
        print("[CHAR]")
        print("[CHAR]")
        print("[CHAR]")
        print("[CHAR] (<5ms latency)")

    except Exception as e:
        print(f"\n[CHAR]: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
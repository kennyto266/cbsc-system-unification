"""
CacheManager独立测试脚本
Standalone CacheManager Test Script
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Add src/api/strategies to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'api', 'strategies'))

# Import directly to avoid import issues
from services.cache_strategy import (
    CacheStrategy, CacheLevel, SerializationType, DEFAULT_STRATEGIES
)

try:
    from services.cache_manager import CacheManager
    print("✅ CacheManager import successful")
except ImportError as e:
    print(f"❌ CacheManager import failed: {e}")
    sys.exit(1)


async def test_basic_operations():
    """测试基本操作"""
    print("\n=== 测试基本操作 ===")

    # Create cache manager
    cache = CacheManager(
        redis_url=None,
        max_memory_items=10,
        default_ttl=60,
        strategies=DEFAULT_STRATEGIES
    )

    # Test set and get
    await cache.set("test:key", "test_value")
    value = await cache.get("test:key")
    assert value == "test_value", f"Expected 'test_value', got {value}"
    print("✅ Set/Get test passed")

    # Test cache miss
    value = await cache.get("nonexistent:key")
    assert value is None, f"Expected None, got {value}"
    print("✅ Cache miss test passed")

    # Test delete
    deleted = await cache.delete("test:key")
    assert deleted is True, f"Expected True, got {deleted}"
    value = await cache.get("test:key")
    assert value is None, f"Expected None after delete, got {value}"
    print("✅ Delete test passed")

    # Get stats
    stats = await cache.get_stats()
    print(f"📊 Cache stats: {stats}")

    await cache.close()
    print("✅ Basic operations completed")


async def test_ttl_and_expiration():
    """测试TTL和过期"""
    print("\n=== 测试TTL和过期 ===")

    cache = CacheManager(
        redis_url=None,
        max_memory_items=10,
        default_ttl=60,
        strategies=DEFAULT_STRATEGIES
    )

    # Test TTL
    await cache.set("ttl:key", "value", ttl=5)
    value = await cache.get("ttl:key")
    assert value == "value", f"Expected 'value', got {value}"

    # Check TTL
    remaining = await cache.ttl("ttl:key")
    assert remaining is not None and 0 < remaining <= 5, f"Invalid TTL: {remaining}"
    print(f"✅ TTL test passed, remaining: {remaining}s")

    # Test expiration
    await cache.set("expire:key", "value", ttl=1)
    await asyncio.sleep(1.1)
    value = await cache.get("expire:key")
    assert value is None, f"Expected None after expiration, got {value}"
    print("✅ Expiration test passed")

    await cache.close()


async def test_increment():
    """测试递增操作"""
    print("\n=== 测试递增操作 ===")

    cache = CacheManager(
        redis_url=None,
        max_memory_items=10,
        default_ttl=60,
        strategies=DEFAULT_STRATEGIES
    )

    # Test increment
    value = await cache.increment("counter", 1)
    assert value == 1, f"Expected 1, got {value}"

    value = await cache.increment("counter", 5)
    assert value == 6, f"Expected 6, got {value}"

    # Verify stored value
    stored = await cache.get("counter")
    assert stored == 6, f"Expected 6, got {stored}"

    print("✅ Increment test passed")

    await cache.close()


async def test_pattern_matching():
    """测试模式匹配"""
    print("\n=== 测试模式匹配 ===")

    cache = CacheManager(
        redis_url=None,
        max_memory_items=10,
        default_ttl=60,
        strategies=DEFAULT_STRATEGIES
    )

    # Set up test data
    await cache.set("user:1:profile", "profile1")
    await cache.set("user:1:settings", "settings1")
    await cache.set("user:2:profile", "profile2")
    await cache.set("other:key", "value")

    # Test pattern deletion
    count = await cache.clear_pattern("user:1:*")
    assert count == 2, f"Expected 2 items deleted, got {count}"

    # Verify results
    assert await cache.get("user:1:profile") is None
    assert await cache.get("user:1:settings") is None
    assert await cache.get("user:2:profile") == "profile2"
    assert await cache.get("other:key") == "value"

    print("✅ Pattern matching test passed")

    await cache.close()


async def test_complex_objects():
    """测试复杂对象序列化"""
    print("\n=== 测试复杂对象序列化 ===")

    cache = CacheManager(
        redis_url=None,
        max_memory_items=10,
        default_ttl=60,
        strategies=DEFAULT_STRATEGIES
    )

    # Test complex object
    complex_obj = {
        "timestamp": datetime.now().isoformat(),
        "nested": {
            "array": [1, 2, 3],
            "boolean": True,
            "null": None
        },
        "number": 42.5
    }

    await cache.set("complex:key", complex_obj)
    retrieved = await cache.get("complex:key")

    assert retrieved["number"] == 42.5, f"Expected 42.5, got {retrieved['number']}"
    assert retrieved["nested"]["boolean"] is True, f"Expected True, got {retrieved['nested']['boolean']}"
    assert retrieved["nested"]["array"] == [1, 2, 3], f"Expected [1, 2, 3], got {retrieved['nested']['array']}"

    print("✅ Complex object serialization test passed")

    await cache.close()


async def test_strategies():
    """测试缓存策略"""
    print("\n=== 测试缓存策略 ===")

    cache = CacheManager(
        redis_url=None,
        max_memory_items=10,
        default_ttl=60,
        strategies=DEFAULT_STRATEGIES
    )

    # Test strategy-based caching
    await cache.set("strategy:test", {"data": "test"})
    value = await cache.get("strategy:test")
    assert value == {"data": "test"}, f"Expected {{'data': 'test'}}, got {value}"

    # Test performance data strategy
    await cache.set("performance:test", {"metrics": [1, 2, 3]})
    value = await cache.get("performance:test")
    assert value == {"metrics": [1, 2, 3]}, f"Expected performance data, got {value}"

    # Test user data strategy
    await cache.set("user:123:preferences", {"theme": "dark"})
    value = await cache.get("user:123:preferences")
    assert value == {"theme": "dark"}, f"Expected user preferences, got {value}"

    print("✅ Strategy-based caching test passed")

    await cache.close()


async def performance_test():
    """性能测试"""
    print("\n=== 性能测试 ===")

    cache = CacheManager(
        redis_url=None,
        max_memory_items=1000,
        default_ttl=60,
        strategies=DEFAULT_STRATEGIES
    )

    # Test write performance
    start_time = asyncio.get_event_loop().time()
    for i in range(1000):
        await cache.set(f"perf:key:{i}", f"value:{i}")
    write_time = asyncio.get_event_loop().time() - start_time

    # Test read performance
    start_time = asyncio.get_event_loop().time()
    for i in range(1000):
        await cache.get(f"perf:key:{i}")
    read_time = asyncio.get_event_loop().time() - start_time

    print(f"📈 Write performance: {1000/write_time:.0f} ops/sec")
    print(f"📈 Read performance: {1000/read_time:.0f} ops/sec")

    # Get final stats
    stats = await cache.get_stats()
    print(f"📊 Final stats: {stats}")

    await cache.close()
    print("✅ Performance test completed")


async def main():
    """主测试函数"""
    print("🚀 CacheManager独立测试开始")
    print("=" * 50)

    try:
        await test_basic_operations()
        await test_ttl_and_expiration()
        await test_increment()
        await test_pattern_matching()
        await test_complex_objects()
        await test_strategies()
        await performance_test()

        print("\n" + "=" * 50)
        print("🎉 所有测试通过！CacheManager实现正确。")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
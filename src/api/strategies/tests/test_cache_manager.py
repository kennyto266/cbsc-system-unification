"""
CacheManager单元测试
Unit Tests for CacheManager
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.strategies.services.cache_manager import CacheManager
from src.api.strategies.services.cache_strategy import (
    CacheStrategy, CacheLevel, SerializationType, DEFAULT_STRATEGIES
)


class TestCacheManager:
    """CacheManager测试类"""

    @pytest.fixture
    def cache_manager(self):
        """创建CacheManager实例（不使用Redis）"""
        return CacheManager(
            redis_url=None,
            max_memory_items=10,
            default_ttl=60,
            strategies=DEFAULT_STRATEGIES
        )

    @pytest.fixture
    def cache_manager_with_redis(self):
        """创建带有Redis模拟的CacheManager实例"""
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = 1
        mock_redis.exists.return_value = 0
        mock_redis.incrby.return_value = 5
        mock_redis.ttl.return_value = 60
        mock_redis.keys.return_value = []
        mock_redis.info.return_value = {"used_memory": 1024, "db0": {"keys": 0}}

        with patch('redis.asyncio.from_url', return_value=mock_redis):
            manager = CacheManager(
                redis_url="redis://localhost:6379",
                max_memory_items=10,
                default_ttl=60,
                strategies=DEFAULT_STRATEGIES
            )
            manager._redis_client = mock_redis
            manager._redis_available = True
            return manager

    @pytest.mark.asyncio
    async def test_set_and_get_memory_cache(self, cache_manager):
        """测试内存缓存的设置和获取"""
        # 设置缓存
        await cache_manager.set("test:key", "test_value", ttl=30)

        # 获取缓存
        value = await cache_manager.get("test:key")
        assert value == "test_value"

        # 检查统计
        stats = await cache_manager.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0
        assert stats["sets"] == 1

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_manager):
        """测试缓存未命中"""
        value = await cache_manager.get("nonexistent:key")
        assert value is None

        stats = await cache_manager.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, cache_manager):
        """测试TTL过期"""
        # 设置短TTL的缓存
        await cache_manager.set("expire:key", "value", ttl=1)

        # 立即获取应该成功
        value = await cache_manager.get("expire:key")
        assert value == "value"

        # 等待过期
        await asyncio.sleep(1.1)

        # 再次获取应该失败
        value = await cache_manager.get("expire:key")
        assert value is None

    @pytest.mark.asyncio
    async def test_lru_eviction(self, cache_manager):
        """测试LRU淘汰策略"""
        # 设置较小的缓存大小
        strategy = CacheStrategy(
            ttl=300,
            level=CacheLevel.L1,
            serializer=SerializationType.JSON,
            max_size=3
        )

        # 添加3个项目
        await cache_manager.set("key1", "value1")
        await cache_manager.set("key2", "value2")
        await cache_manager.set("key3", "value3")

        # 访问key1使其成为最近使用
        await cache_manager.get("key1")

        # 添加第4个项目，应该淘汰key2
        await cache_manager.set("key4", "value4")

        # key1应该还在（最近访问过）
        assert await cache_manager.get("key1") == "value1"

        # key2应该被淘汰
        assert await cache_manager.get("key2") is None

        # key3和key4应该还在
        assert await cache_manager.get("key3") == "value3"
        assert await cache_manager.get("key4") == "value4"

    @pytest.mark.asyncio
    async def test_increment_operation(self, cache_manager):
        """测试递增操作"""
        # 初始递增
        value = await cache_manager.increment("counter", 1)
        assert value == 1

        # 再次递增
        value = await cache_manager.increment("counter", 5)
        assert value == 6

        # 验证值
        stored_value = await cache_manager.get("counter")
        assert stored_value == 6

    @pytest.mark.asyncio
    async def test_increment_with_redis(self, cache_manager_with_redis):
        """测试Redis递增操作"""
        cache_manager = cache_manager_with_redis

        # 使用Redis的INCR操作
        value = await cache_manager.increment("redis_counter", 3)
        assert value == 3

        # 验证Redis方法被调用
        cache_manager._redis_client.incrby.assert_called_with("redis_counter", 3)

    @pytest.mark.asyncio
    async def test_delete_cache(self, cache_manager):
        """测试删除缓存"""
        # 设置缓存
        await cache_manager.set("delete:key", "value")
        assert await cache_manager.get("delete:key") == "value"

        # 删除缓存
        deleted = await cache_manager.delete("delete:key")
        assert deleted is True

        # 验证已删除
        assert await cache_manager.get("delete:key") is None

    @pytest.mark.asyncio
    async def test_clear_pattern(self, cache_manager):
        """测试批量删除模式匹配"""
        # 设置多个缓存项
        await cache_manager.set("user:1:profile", "profile1")
        await cache_manager.set("user:1:settings", "settings1")
        await cache_manager.set("user:2:profile", "profile2")
        await cache_manager.set("other:key", "value")

        # 删除user:1相关的缓存
        count = await cache_manager.clear_pattern("user:1:*")
        assert count == 2

        # 验证删除结果
        assert await cache_manager.get("user:1:profile") is None
        assert await cache_manager.get("user:1:settings") is None
        assert await cache_manager.get("user:2:profile") == "profile2"
        assert await cache_manager.get("other:key") == "value"

    @pytest.mark.asyncio
    async def test_exists_check(self, cache_manager):
        """测试键存在性检查"""
        # 设置缓存
        await cache_manager.set("exists:key", "value")

        # 检查存在的键
        exists = await cache_manager.exists("exists:key")
        assert exists is True

        # 检查不存在的键
        exists = await cache_manager.exists("nonexistent:key")
        assert exists is False

    @pytest.mark.asyncio
    async def test_get_ttl(self, cache_manager):
        """测试获取剩余TTL"""
        # 设置带TTL的缓存
        await cache_manager.set("ttl:key", "value", ttl=60)

        # 获取TTL
        remaining = await cache_manager.ttl("ttl:key")
        assert remaining is not None
        assert 0 < remaining <= 60

        # 获取不存在键的TTL
        remaining = await cache_manager.ttl("nonexistent:key")
        assert remaining is None

    @pytest.mark.asyncio
    async def test_strategy_based_caching(self, cache_manager):
        """测试基于策略的缓存"""
        # 策略数据应该使用JSON序列化
        await cache_manager.set("strategy:test", {"data": "test"})
        value = await cache_manager.get("strategy:test")
        assert value == {"data": "test"}

        # 验证使用了正确的策略
        from src.api.strategies.services.cache_strategy import get_strategy_for_key
        strategy = get_strategy_for_key("strategy:test", DEFAULT_STRATEGIES)
        assert strategy.level == CacheLevel.L2
        assert strategy.serializer == SerializationType.JSON

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, cache_manager):
        """测试清理过期缓存"""
        # 设置一些过期的缓存
        await cache_manager.set("expired1", "value1", ttl=1)
        await cache_manager.set("expired2", "value2", ttl=1)
        await cache_manager.set("valid", "value3", ttl=60)

        # 等待部分缓存过期
        await asyncio.sleep(1.1)

        # 清理过期缓存
        cleaned = await cache_manager.cleanup_expired()
        assert cleaned >= 2  # 至少清理了2个过期项

        # 验证有效缓存还在
        assert await cache_manager.get("valid") == "value3"

    @pytest.mark.asyncio
    async def test_cache_stats(self, cache_manager):
        """测试缓存统计"""
        # 执行一些操作
        await cache_manager.set("stat1", "value1")
        await cache_manager.get("stat1")  # hit
        await cache_manager.get("nonexistent")  # miss
        await cache_manager.delete("stat1")  # delete

        # 获取统计信息
        stats = await cache_manager.get_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 1
        assert stats["deletes"] == 1
        assert stats["hit_rate"] == 0.5  # 1 hit / (1 hit + 1 miss)
        assert stats["memory_items"] == 0  # 删除后应该为0

    @pytest.mark.asyncio
    async def test_complex_object_serialization(self, cache_manager):
        """测试复杂对象序列化"""
        complex_obj = {
            "timestamp": datetime.now(),
            "nested": {
                "array": [1, 2, 3],
                "boolean": True,
                "null": None
            },
            "number": 42.5
        }

        # 设置复杂对象
        await cache_manager.set("complex:key", complex_obj)

        # 获取并验证
        retrieved = await cache_manager.get("complex:key")
        assert retrieved["number"] == 42.5
        assert retrieved["nested"]["boolean"] is True
        assert retrieved["nested"]["array"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_cache_with_redis_fallback(self, cache_manager_with_redis):
        """测试Redis降级处理"""
        cache_manager = cache_manager_with_redis

        # 模拟Redis连接失败
        cache_manager._redis_available = False

        # 应该降级到内存缓存
        await cache_manager.set("fallback:key", "value")
        value = await cache_manager.get("fallback:key")
        assert value == "value"

        # 验证没有调用Redis
        cache_manager._redis_client.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_close_cache_manager(self, cache_manager_with_redis):
        """测试关闭缓存管理器"""
        cache_manager = cache_manager_with_redis

        # 关闭管理器
        await cache_manager.close()

        # 验证Redis连接已关闭
        cache_manager._redis_client.close.assert_called_once()
        assert cache_manager._redis_available is False
        assert len(cache_manager._memory_cache) == 0

    @pytest.mark.asyncio
    async def test_default_strategy_fallback(self, cache_manager):
        """测试默认策略回退"""
        # 对于没有特定策略的键，应该使用默认策略
        await cache_manager.set("unknown:prefix:key", "value")
        value = await cache_manager.get("unknown:prefix:key")
        assert value == "value"

        # 验证使用了默认策略（L1级别）
        assert "unknown:prefix:key" in cache_manager._memory_cache
"""
緩存管理測試
Cache Manager Tests
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from ..utils.cache import CacheManager


class TestCacheManager:
    """緩存管理器測試類"""

    @pytest.fixture
    def cache_manager(self):
        """創建緩存管理器fixture"""
        return CacheManager()

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache_manager):
        """測試設置和獲取緩存"""
        key = "test_key"
        value = {"data": "test_value"}

        # 設置緩存
        await cache_manager.set(key, value)

        # 獲取緩存
        result = await cache_manager.get(key)

        assert result is not None
        assert result["data"] == "test_value"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache_manager):
        """測試獲取不存在的鍵"""
        result = await cache_manager.get("nonexistent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, cache_manager):
        """測試設置帶TTL的緩存"""
        key = "test_ttl_key"
        value = "test_value"

        # 設置短TTL的緩存
        await cache_manager.set(key, value, ttl=0.1)  # 0.1秒

        # 立即獲取應該成功
        result = await cache_manager.get(key)
        assert result == "test_value"

        # 等待TTL過期
        await asyncio.sleep(0.2)

        # 再次獲取應該返回None
        result = await cache_manager.get(key)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, cache_manager):
        """測試刪除緩存"""
        key = "test_delete_key"
        value = "test_value"

        # 設置緩存
        await cache_manager.set(key, value)

        # 驗證緩存存在
        result = await cache_manager.get(key)
        assert result == "test_value"

        # 刪除緩存
        await cache_manager.delete(key)

        # 驗證緩存已刪除
        result = await cache_manager.get(key)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, cache_manager):
        """測試刪除不存在的鍵"""
        # 不應該拋出異常
        await cache_manager.delete("nonexistent_key")

    @pytest.mark.asyncio
    async def test_clear_all(self, cache_manager):
        """測試清空所有緩存"""
        # 設置多個緩存
        for i in range(5):
            await cache_manager.set(f"key_{i}", f"value_{i}")

        # 驗證緩存存在
        for i in range(5):
            result = await cache_manager.get(f"key_{i}")
            assert result == f"value_{i}"

        # 清空所有緩存
        await cache_manager.clear_all()

        # 驗證所有緩存已清空
        for i in range(5):
            result = await cache_manager.get(f"key_{i}")
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_pattern(self, cache_manager):
        """測試按模式刪除緩存"""
        # 設置不同模式的緩存
        await cache_manager.set("user:1", "user_1")
        await cache_manager.set("user:2", "user_2")
        await cache_manager.set("strategy:1", "strategy_1")
        await cache_manager.set("strategy:2", "strategy_2")
        await cache_manager.set("other_key", "other_value")

        # 刪除用戶相關的緩存
        await cache_manager.delete_pattern("user:*")

        # 驗證用戶緩存已刪除
        assert await cache_manager.get("user:1") is None
        assert await cache_manager.get("user:2") is None

        # 驗證其他緩存仍存在
        assert await cache_manager.get("strategy:1") == "strategy_1"
        assert await cache_manager.get("strategy:2") == "strategy_2"
        assert await cache_manager.get("other_key") == "other_value"

    @pytest.mark.asyncio
    async def test_exists(self, cache_manager):
        """測試檢查緩存是否存在"""
        key = "test_exists_key"
        value = "test_value"

        # 初始狀態
        assert not await cache_manager.exists(key)

        # 設置緩存
        await cache_manager.set(key, value)

        # 檢查存在
        assert await cache_manager.exists(key)

        # 刪除緩存
        await cache_manager.delete(key)

        # 檢查不存在
        assert not await cache_manager.exists(key)

    @pytest.mark.asyncio
    async def test_increment(self, cache_manager):
        """測試遞增操作"""
        key = "test_increment_key"

        # 初始遞增
        result = await cache_manager.increment(key, 1)
        assert result == 1

        # 再次遞增
        result = await cache_manager.increment(key, 5)
        assert result == 6

        # 驗證值
        value = await cache_manager.get(key)
        assert value == 6

    @pytest.mark.asyncio
    async def test_increment_nonexistent_key(self, cache_manager):
        """測試對不存在的鍵進行遞增"""
        key = "test_nonexistent_increment"

        # 對不存在的鍵遞增應該從0開始
        result = await cache_manager.increment(key, 3)
        assert result == 3

        # 驗證值
        value = await cache_manager.get(key)
        assert value == 3

    @pytest.mark.asyncio
    async def test_ttl(self, cache_manager):
        """測試獲取TTL"""
        key = "test_ttl_key"

        # 設置帶TTL的緩存
        await cache_manager.set(key, "value", ttl=60)

        # 獲取TTL
        ttl = await cache_manager.ttl(key)
        assert ttl is not None
        assert 50 <= ttl <= 60  # 允許一些時間誤差

        # 對不存在的鍵獲取TTL
        ttl_none = await cache_manager.ttl("nonexistent_key")
        assert ttl_none is None

    @pytest.mark.asyncio
    async def test_set_with_datetime_ttl(self, cache_manager):
        """測試使用datetime設置TTL"""
        key = "test_datetime_ttl_key"
        value = "test_value"

        # 設置未來的過期時間
        expire_at = datetime.now() + timedelta(seconds=60)
        await cache_manager.set(key, value, expire_at=expire_at)

        # 獲取應該成功
        result = await cache_manager.get(key)
        assert result == "test_value"

        # 獲取TTL
        ttl = await cache_manager.ttl(key)
        assert ttl is not None
        assert 50 <= ttl <= 60

    @pytest.mark.asyncio
    async def test_overwrite_cache(self, cache_manager):
        """測試覆蓋緩存"""
        key = "test_overwrite_key"

        # 設置初始值
        await cache_manager.set(key, "initial_value")
        result = await cache_manager.get(key)
        assert result == "initial_value"

        # 覆蓋值
        await cache_manager.set(key, "overwritten_value")
        result = await cache_manager.get(key)
        assert result == "overwritten_value"

    @pytest.mark.asyncio
    async def test_complex_data_types(self, cache_manager):
        """測試複雜數據類型"""
        key = "test_complex_key"
        complex_value = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "datetime": datetime.now(),
            "none": None,
            "boolean": True
        }

        # 設置複雜數據
        await cache_manager.set(key, complex_value)

        # 獲取並驗證
        result = await cache_manager.get(key)

        assert result is not None
        assert result["list"] == [1, 2, 3]
        assert result["dict"]["nested"] == "value"
        assert result["none"] is None
        assert result["boolean"] is True

    @pytest.mark.asyncio
    async def test_concurrent_access(self, cache_manager):
        """測試並發訪問"""
        key = "test_concurrent_key"

        # 並發設置
        tasks = []
        for i in range(10):
            task = cache_manager.set(f"{key}_{i}", f"value_{i}")
            tasks.append(task)

        await asyncio.gather(*tasks)

        # 並發獲取
        get_tasks = []
        for i in range(10):
            task = cache_manager.get(f"{key}_{i}")
            get_tasks.append(task)

        results = await asyncio.gather(*get_tasks)

        # 驗證結果
        for i, result in enumerate(results):
            assert result == f"value_{i}"

    @pytest.mark.asyncio
    async def test_cache_size_limit(self, cache_manager):
        """測試緩存大小限制"""
        # 創建有限大小的緩存
        limited_cache = CacheManager(max_size=3)

        # 添加超過限制的項目
        await limited_cache.set("key1", "value1")
        await limited_cache.set("key2", "value2")
        await limited_cache.set("key3", "value3")
        await limited_cache.set("key4", "value4")  # 應該淘汰最早的項目

        # 驗證最早的項目被淘汰
        assert await limited_cache.get("key1") is None
        assert await limited_cache.get("key2") == "value2"
        assert await limited_cache.get("key3") == "value3"
        assert await limited_cache.get("key4") == "value4"

    @pytest.mark.asyncio
    async def test_get_stats(self, cache_manager):
        """測試獲取緩存統計"""
        # 添加一些緩存項目
        await cache_manager.set("key1", "value1")
        await cache_manager.set("key2", "value2")
        await cache_manager.set("key3", "value3")

        # 獲取一些項目
        await cache_manager.get("key1")
        await cache_manager.get("nonexistent")

        # 獲取統計
        stats = await cache_manager.get_stats()

        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
        assert stats["sets"] == 3
        assert stats["size"] >= 2  # 至少有2個項目


if __name__ == "__main__":
    # 運行測試
    asyncio.run(pytest.main([__file__, "-v"]))
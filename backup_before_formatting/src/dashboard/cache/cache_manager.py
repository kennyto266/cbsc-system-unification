"""
緩存管理器
港股量化交易系統 - 緩存模組

提供統一的緩存管理功能，支持內存緩存、Redis緩存和LRU緩存策略。

主要功能:
- 內存緩存管理
- Redis緩存集成
- LRU緩存策略
- 緩存裝飾器
- 緩存失效機制
- 多級緩存支持
"""

import hashlib
import json
import logging
import pickle
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class MemoryCache:
    """內存緩存實現"""

    def __init__(self, max_size: int = 1000):
        """
        初始化內存緩存

        Args:
            max_size: 最大緩存項數量
        """
        self.max_size = max_size
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_order: List[str] = []

    def _is_expired(self, item: Dict[str, Any]) -> bool:
        """檢查緩存項是否過期"""
        if "ttl" not in item or item["ttl"] is None:
            return False
        return time.time() > item["created_at"] + item["ttl"]

    def _update_access_order(self, key: str):
        """更新訪問順序"""
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

    def get(self, key: str) -> Any:
        """
        獲取緩存值

        Args:
            key: 緩存鍵

        Returns:
            緩存值，如果不存在或過期則返回None
        """
        if key not in self.cache:
            return None

        item = self.cache[key]

        # 檢查過期
        if self._is_expired(item):
            self.delete(key)
            return None

        # 更新訪問順序
        self._update_access_order(key)

        return item["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        設置緩存值

        Args:
            key: 緩存鍵
            value: 緩存值
            ttl: 生存時間（秒），None表示不過期
        """
        # 如果緩存已滿，刪除最少使用的項
        if len(self.cache) >= self.max_size:
            self._evict_lru()

        self.cache[key] = {"value": value, "created_at": time.time(), "ttl": ttl}
        self._update_access_order(key)

    def delete(self, key: str):
        """刪除緩存項"""
        if key in self.cache:
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)

    def _evict_lru(self):
        """刪除最少最近使用的項"""
        if self.access_order:
            oldest_key = self.access_order[0]
            self.delete(oldest_key)

    def clear(self):
        """清空所有緩存"""
        self.cache.clear()
        self.access_order.clear()

    def size(self) -> int:
        """獲取緩存項數量"""
        return len(self.cache)

    def keys(self) -> List[str]:
        """獲取所有緩存鍵"""
        return list(self.cache.keys())


class LRUCache:
    """LRU緩存實現"""

    def __init__(self, capacity: int = 100):
        """
        初始化LRU緩存

        Args:
            capacity: 緩存容量
        """
        self.capacity = capacity
        self.cache: Dict[str, Any] = {}
        self.order: List[str] = []

    def get(self, key: str) -> Any:
        """獲取緩存值"""
        if key not in self.cache:
            return None

        # 更新使用順序
        self.order.remove(key)
        self.order.append(key)

        return self.cache[key]

    def set(self, key: str, value: Any):
        """設置緩存值"""
        if key in self.cache:
            # 更新現有項
            self.order.remove(key)
            self.order.append(key)
            self.cache[key] = value
        else:
            # 添加新項
            if len(self.cache) >= self.capacity:
                # 刪除最少最近使用的項
                oldest_key = self.order.pop(0)
                del self.cache[oldest_key]

            self.cache[key] = value
            self.order.append(key)

    def delete(self, key: str):
        """刪除緩存項"""
        if key in self.cache:
            del self.cache[key]
            if key in self.order:
                self.order.remove(key)

    def clear(self):
        """清空所有緩存"""
        self.cache.clear()
        self.order.clear()


class RedisCache:
    """Redis緩存實現"""

    def __init__(self, redis_adapter):
        """
        初始化Redis緩存

        Args:
            redis_adapter: Redis適配器實例
        """
        self.redis = redis_adapter
        self.prefix = "cache:"

    def _get_key(self, key: str) -> str:
        """獲取帶前綴的緩存鍵"""
        return f"{self.prefix}{key}"

    def get(self, key: str) -> Any:
        """
        獲取緩存值

        Args:
            key: 緩存鍵

        Returns:
            緩存值，如果不存在則返回None
        """
        try:
            return self.redis.get(self._get_key(key))
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        設置緩存值

        Args:
            key: 緩存鍵
            value: 緩存值
            ttl: 生存時間（秒），None表示不過期
        """
        try:
            self.redis.set(self._get_key(key), value, ttl)
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    def delete(self, key: str):
        """刪除緩存項"""
        try:
            self.redis.delete(self._get_key(key))
        except Exception as e:
            logger.error(f"Redis delete error: {e}")

    def clear(self):
        """清空所有緩存"""
        try:
            self.redis.clear(f"{self.prefix}*")
        except Exception as e:
            logger.error(f"Redis clear error: {e}")

    def exists(self, key: str) -> bool:
        """檢查緩存鍵是否存在"""
        try:
            return self.redis.exists(self._get_key(key))
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False


class CacheManager:
    """
    統一緩存管理器

    支持內存緩存、Redis緩存和LRU緩存的統一管理。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, redis_adapter=None):
        """
        初始化緩存管理器

        Args:
            config: 緩存配置
            redis_adapter: Redis適配器實例
        """
        self.config = config or {}
        self.memory_cache = MemoryCache(
            max_size=self.config.get("memory_max_size", 1000)
        )
        self.lru_cache = LRUCache(capacity=self.config.get("lru_capacity", 100))
        self.redis_cache = None
        self.default_ttl = self.config.get("default_ttl", 3600)  # 1小時

        # 如果提供了Redis適配器，初始化Redis緩存
        if redis_adapter:
            self.redis_cache = RedisCache(redis_adapter)
            logger.info("Redis緩存已配置")

    def get(self, key: str, cache_type: str = "memory") -> Any:
        """
        獲取緩存值

        Args:
            key: 緩存鍵
            cache_type: 緩存類型 (memory / lru / redis)

        Returns:
            緩存值
        """
        if cache_type == "memory":
            return self.memory_cache.get(key)
        elif cache_type == "lru":
            return self.lru_cache.get(key)
        elif cache_type == "redis":
            if self.redis_cache:
                return self.redis_cache.get(key)
            else:
                logger.warning("Redis緩存未配置，使用內存緩存")
                return self.memory_cache.get(key)
        else:
            raise ValueError(f"不支持的緩存類型: {cache_type}")

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        cache_type: str = "memory",
    ):
        """
        設置緩存值

        Args:
            key: 緩存鍵
            value: 緩存值
            ttl: 生存時間（秒）
            cache_type: 緩存類型
        """
        ttl = ttl or self.default_ttl

        if cache_type == "memory":
            self.memory_cache.set(key, value, ttl)
        elif cache_type == "lru":
            self.lru_cache.set(key, value)
        elif cache_type == "redis":
            if self.redis_cache:
                self.redis_cache.set(key, value, ttl)
            else:
                logger.warning("Redis緩存未配置，使用內存緩存")
                self.memory_cache.set(key, value, ttl)
        else:
            raise ValueError(f"不支持的緩存類型: {cache_type}")

    def delete(self, key: str, cache_type: str = "memory"):
        """刪除緩存項"""
        if cache_type == "memory":
            self.memory_cache.delete(key)
        elif cache_type == "lru":
            self.lru_cache.delete(key)
        elif cache_type == "redis":
            if self.redis_cache:
                self.redis_cache.delete(key)
            else:
                self.memory_cache.delete(key)
        else:
            raise ValueError(f"不支持的緩存類型: {cache_type}")

    def clear(self, cache_type: str = "memory"):
        """清空所有緩存"""
        if cache_type == "memory":
            self.memory_cache.clear()
        elif cache_type == "lru":
            self.lru_cache.clear()
        elif cache_type == "redis":
            if self.redis_cache:
                self.redis_cache.clear()
            else:
                self.memory_cache.clear()
        else:
            raise ValueError(f"不支持的緩存類型: {cache_type}")

    def get_stats(self) -> Dict[str, Any]:
        """
        獲取緩存統計信息

        Returns:
            統計信息字典
        """
        return {
            "memory_cache": {
                "size": self.memory_cache.size(),
                "max_size": self.memory_cache.max_size,
            },
            "lru_cache": {
                "size": len(self.lru_cache.cache),
                "capacity": self.lru_cache.capacity,
            },
            "redis_cache": {"available": self.redis_cache is not None},
            "default_ttl": self.default_ttl,
        }


def cache_decorator(
    cache_manager: CacheManager,
    key_prefix: str = "",
    ttl: Optional[int] = None,
    cache_type: str = "memory",
):
    """
    緩存裝飾器

    Args:
        cache_manager: 緩存管理器實例
        key_prefix: 緩存鍵前綴
        ttl: 緩存生存時間
        cache_type: 緩存類型

    使用示例:
        @cache_decorator(cache_manager, key_prefix="user:", ttl=3600)
        async def get_user(user_id: str):
            return await fetch_user_from_db(user_id)
    """

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成緩存鍵
            cache_key = f"{key_prefix}{func.__name__}"
            if args:
                cache_key += f":{hashlib.sha256(str(args).encode()).hexdigest()[:8]}"
            if kwargs:
                cache_key += f":{hashlib.sha256(str(kwargs).encode()).hexdigest()[:8]}"

            # 嘗試從緩存獲取
            cached_result = cache_manager.get(cache_key, cache_type)
            if cached_result is not None:
                logger.debug(f"緩存命中: {cache_key}")
                return cached_result

            # 執行函數
            result = await func(*args, **kwargs)

            # 設置緩存
            cache_manager.set(cache_key, result, ttl, cache_type)
            logger.debug(f"緩存設置: {cache_key}")

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 生成緩存鍵
            cache_key = f"{key_prefix}{func.__name__}"
            if args:
                cache_key += f":{hashlib.sha256(str(args).encode()).hexdigest()[:8]}"
            if kwargs:
                cache_key += f":{hashlib.sha256(str(kwargs).encode()).hexdigest()[:8]}"

            # 嘗試從緩存獲取
            cached_result = cache_manager.get(cache_key, cache_type)
            if cached_result is not None:
                logger.debug(f"緩存命中: {cache_key}")
                return cached_result

            # 執行函數
            result = func(*args, **kwargs)

            # 設置緩存
            cache_manager.set(cache_key, result, ttl, cache_type)
            logger.debug(f"緩存設置: {cache_key}")

            return result

        # 根據函數類型返回包裝器
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 便利函數
def create_cache_manager(
    memory_max_size: int = 1000,
    lru_capacity: int = 100,
    default_ttl: int = 3600,
    redis_adapter=None,
) -> CacheManager:
    """
    創建緩存管理器的便利函數

    Args:
        memory_max_size: 內存緩存最大大小
        lru_capacity: LRU緩存容量
        default_ttl: 默認生存時間
        redis_adapter: Redis適配器實例

    Returns:
        CacheManager實例
    """
    config = {
        "memory_max_size": memory_max_size,
        "lru_capacity": lru_capacity,
        "default_ttl": default_ttl,
    }

    return CacheManager(config, redis_adapter)


if __name__ == "__main__":
    # 測試示例
    import asyncio

    # 創建緩存管理器
    cache_manager = create_cache_manager(
        memory_max_size=100, lru_capacity=50, default_ttl=60
    )

    # 測試內存緩存
    cache_manager.set("test_key", "test_value", ttl=30)
    result = cache_manager.get("test_key")
    print(f"內存緩存測試: {result}")

    # 測試LRU緩存
    cache_manager.set("lru_key", "lru_value", cache_type="lru")
    result = cache_manager.get("lru_key", cache_type="lru")
    print(f"LRU緩存測試: {result}")

    # 測試緩存裝飾器
    @cache_decorator(cache_manager, key_prefix="func:", ttl=30)
    def test_func(x: int):
        print(f"執行函數: x={x}")
        return x * 2

    result1 = test_func(5)  # 第一次調用，執行函數
    result2 = test_func(5)  # 第二次調用，使用緩存
    print(f"緩存裝飾器測試: {result1}, {result2}")

    # 獲取統計信息
    stats = cache_manager.get_stats()
    print(f"緩存統計: {stats}")

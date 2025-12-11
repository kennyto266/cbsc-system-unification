"""
缓存管理工具
Cache Management Utilities

职责：
- 缓存操作封装
- 缓存策略管理
- 缓存失效处理

This module provides a unified cache management system with L1 (memory) and L2 (Redis) caching.
"""

import json
import asyncio
from typing import Any, Optional, List, Dict, Union
from datetime import datetime, timedelta
import logging
from functools import wraps

# Import the new cache manager
from ...services.cache_manager import CacheManager as BaseCacheManager, CacheKeys as BaseCacheKeys

logger = logging.getLogger(__name__)


class CacheManager(BaseCacheManager):
    """
    增强的缓存管理器

    继承自BaseCacheManager，提供异步接口和向后兼容性。
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0", use_memory: bool = True):
        """
        初始化缓存管理器

        Args:
            redis_url: Redis连接URL
            use_memory: 是否使用内存缓存作为fallback
        """
        # Parse Redis URL
        import urllib.parse
        parsed = urllib.parse.urlparse(redis_url)

        # Initialize base cache manager
        super().__init__(
            redis_host=parsed.hostname or "localhost",
            redis_port=parsed.port or 6379,
            redis_db=int(parsed.path[1:]) if parsed.path and parsed.path[1:] else 0,
            redis_password=parsed.password,
            enable_redis=use_memory,  # Keep the same logic as before
            default_memory_size=1000
        )

        # Store legacy settings for compatibility
        self.redis_url = redis_url
        self.use_memory = use_memory
        self.default_ttl = 300  # 5 minutes

    # ========================================================================
    # 异步适配器方法 (Async Adapter Methods)
    # 这些方法提供与旧版本的异步接口兼容性
    # ========================================================================

    async def _get_redis_client(self):
        """获取Redis客户端（兼容性方法）"""
        return self._redis_cache

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存（异步版本）

        Args:
            key: 缓存键

        Returns:
            缓存值或None
        """
        # Try to determine strategy from key pattern
        strategy_name = self._infer_strategy_from_key(key)
        return super().get(strategy_name, key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存（异步版本）

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）

        Returns:
            是否成功
        """
        strategy_name = self._infer_strategy_from_key(key)
        return super().set(strategy_name, key, value, ttl or self.default_ttl)

    async def delete(self, key: str) -> bool:
        """
        删除缓存（异步版本）

        Args:
            key: 缓存键

        Returns:
            是否成功
        """
        strategy_name = self._infer_strategy_from_key(key)
        return super().delete(strategy_name, key)

    async def delete_pattern(self, pattern: str) -> int:
        """
        删除匹配模式的所有缓存（异步版本）

        Args:
            pattern: 匹配模式

        Returns:
            删除的数量
        """
        # This is a simplified implementation
        # In a real scenario, we'd need to determine which strategy to use
        total_deleted = 0
        for strategy_name in ["user", "strategy", "performance", "config"]:
            deleted = super().clear_pattern(strategy_name, pattern)
            total_deleted += deleted
        return total_deleted

    async def exists(self, key: str) -> bool:
        """
        检查缓存是否存在（异步版本）

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        strategy_name = self._infer_strategy_from_key(key)
        return super().exists(strategy_name, key)

    async def expire(self, key: str, ttl: int) -> bool:
        """
        设置缓存过期时间（异步版本）

        Args:
            key: 缓存键
            ttl: 过期时间（秒）

        Returns:
            是否成功
        """
        # Get current value and set with new TTL
        value = await self.get(key)
        if value is not None:
            return await self.set(key, value, ttl)
        return False

    async def ttl(self, key: str) -> int:
        """
        获取缓存剩余时间（异步版本）

        Args:
            key: 缓存键

        Returns:
            剩余时间（秒），-1表示永不过期，-2表示不存在
        """
        strategy_name = self._infer_strategy_from_key(key)
        return super().get_ttl(strategy_name, key)

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        递增缓存值（异步版本）

        Args:
            key: 缓存键
            amount: 递增量

        Returns:
            递增后的值
        """
        # Get current value
        current = await self.get(key)
        if current is None:
            new_value = amount
        elif isinstance(current, int):
            new_value = current + amount
        else:
            logger.warning(f"Cannot increment non-integer value for key: {key}")
            return None

        # Set new value
        if await self.set(key, new_value):
            return new_value
        return None

    async def get_multiple(self, keys: List[str]) -> Dict[str, Any]:
        """
        批量获取缓存（异步版本）

        Args:
            keys: 缓存键列表

        Returns:
            键值对字典
        """
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def set_multiple(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        批量设置缓存（异步版本）

        Args:
            mapping: 键值对字典
            ttl: 过期时间（秒）

        Returns:
            是否成功
        """
        success = True
        for key, value in mapping.items():
            if not await self.set(key, value, ttl):
                success = False
        return success

    async def clear_all(self) -> bool:
        """
        清空所有缓存（异步版本）

        Returns:
            是否成功
        """
        # Clear all strategies
        success = True
        for strategy_name in ["user", "strategy", "performance", "config", "market_data", "session", "realtime_signals", "api_stats"]:
            # Clear memory caches
            if strategy_name in self._memory_caches:
                self._memory_caches[strategy_name].clear()

        # Clear Redis if available
        if self._redis_cache and self._redis_cache.is_connected():
            try:
                import redis.asyncio as redis_async
                redis_client = redis_async.from_url(self.redis_url)
                await redis_client.flushdb()
                await redis_client.close()
            except Exception as e:
                logger.error(f"Failed to clear Redis: {e}")
                success = False

        return success

    async def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息（异步版本）

        Returns:
            统计信息
        """
        base_stats = self.get_cache_info()

        # Format for legacy compatibility
        return {
            "memory_cache": {
                "keys_count": sum(cache.size() for cache in self._memory_caches.values()),
                "use_memory": self.use_memory
            },
            "redis": {
                "connected": base_stats.get("redis_connected", False),
                "url": self.redis_url
            }
        }

    def _infer_strategy_from_key(self, key: str) -> str:
        """
        从键推断策略名称

        Args:
            key: 缓存键

        Returns:
            策略名称
        """
        key_lower = key.lower()

        if any(keyword in key_lower for keyword in ["strategy", "strategies"]):
            return "strategy"
        elif any(keyword in key_lower for keyword in ["user", "preferences", "dashboard"]):
            return "user"
        elif any(keyword in key_lower for keyword in ["performance", "metrics"]):
            return "performance"
        elif any(keyword in key_lower for keyword in ["config", "template"]):
            return "config"
        elif any(keyword in key_lower for keyword in ["market", "symbol"]):
            return "market_data"
        elif any(keyword in key_lower for keyword in ["session"]):
            return "session"
        elif any(keyword in key_lower for keyword in ["signal", "realtime"]):
            return "realtime_signals"
        elif any(keyword in key_lower for keyword in ["api", "stats"]):
            return "api_stats"
        else:
            # Default strategy
            return "user"


# 全局缓存管理器实例
cache_manager = CacheManager()


# 缓存装饰器
def cache_result(
    key_prefix: str,
    ttl: int = 300,
    use_args: bool = True,
    use_kwargs: bool = True
):
    """
    缓存函数结果装饰器

    Args:
        key_prefix: 缓存键前缀
        ttl: 过期时间（秒）
        use_args: 是否使用位置参数生成键
        use_kwargs: 是否使用关键字参数生成键
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = key_prefix
            if use_args and args:
                cache_key += ":" + ":".join(str(arg) for arg in args)
            if use_kwargs and kwargs:
                sorted_kwargs = sorted(kwargs.items())
                cache_key += ":" + ":".join(f"{k}={v}" for k, v in sorted_kwargs)

            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 执行函数
            result = await func(*args, **kwargs)

            # 缓存结果
            await cache_manager.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


# 缓存失效装饰器
def invalidate_cache(patterns: List[str]):
    """
    缓存失效装饰器

    Args:
        patterns: 要失效的缓存模式列表
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 执行函数
            result = await func(*args, **kwargs)

            # 失效相关缓存
            for pattern in patterns:
                await cache_manager.delete_pattern(pattern)

            return result

        return wrapper
    return decorator


# 常用缓存键模式
class CacheKeys:
    """缓存键模式"""

    STRATEGY_DETAIL = "cbsc:strategy:detail:{strategy_id}"
    STRATEGY_LIST = "cbsc:strategies:list:{page}:{page_size}:{type}:{status}:{user_id}"
    USER_PREFERENCES = "cbsc:user:preferences:{user_id}"
    DASHBOARD_DATA = "cbsc:user:dashboard:{user_id}"
    EXECUTION_STATUS = "cbsc:execution:status:{execution_id}"
    PERFORMANCE_METRICS = "cbsc:strategy:performance:metrics:{strategy_id}:{time_range}"
    USER_STRATEGIES = "cbsc:user:strategies:{user_id}"
    TEMPLATE_LIST = "cbsc:templates:list:{type}"

    @classmethod
    def strategy_detail(cls, strategy_id: str) -> str:
        return cls.STRATEGY_DETAIL.format(strategy_id=strategy_id)

    @classmethod
    def strategy_list(cls, **kwargs) -> str:
        return cls.STRATEGY_LIST.format(
            page=kwargs.get("page", 1),
            page_size=kwargs.get("page_size", 20),
            type=kwargs.get("type", ""),
            status=kwargs.get("status", ""),
            user_id=kwargs.get("user_id", "")
        )

    @classmethod
    def user_preferences(cls, user_id: int) -> str:
        return cls.USER_PREFERENCES.format(user_id=user_id)

    @classmethod
    def dashboard_data(cls, user_id: int) -> str:
        return cls.DASHBOARD_DATA.format(user_id=user_id)
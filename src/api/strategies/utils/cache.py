"""
缓存管理工具
Cache Management Utilities

职责：
- 缓存操作封装
- 缓存策略管理
- 缓存失效处理

Simplified cache manager for strategy module testing.
"""

import asyncio
from typing import Any, Optional, List, Dict, Union
from datetime import datetime, timedelta
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class CacheKeys:
    """缓存键常量"""
    STRATEGY_LIST = "strategies:list"
    STRATEGY_DETAIL = "strategy:detail"
    STRATEGY_PERFORMANCE = "strategy:performance"
    STRATEGY_SIGNALS = "strategy:signals"
    TEMPLATES_LIST = "templates:list"
    USER_PREFERENCES = "user:preferences"
    EXECUTION_STATUS = "execution:status"


class CacheManager:
    """
    简化的内存缓存管理器
    Simplified in-memory cache manager for testing
    """

    def __init__(self):
        self._cache = {}
        self._ttl = {}
        self._default_ttl = 300  # 5 minutes

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        # Check TTL
        if key in self._ttl and datetime.now() > self._ttl[key]:
            await self.delete(key)
            return None

        return self._cache.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        self._cache[key] = value

        if ttl is not None:
            self._ttl[key] = datetime.now() + timedelta(seconds=ttl)
        else:
            self._ttl[key] = datetime.now() + timedelta(seconds=self._default_ttl)

    async def delete(self, key: str) -> None:
        """删除缓存"""
        self._cache.pop(key, None)
        self._ttl.pop(key, None)

    async def delete_pattern(self, pattern: str) -> None:
        """删除匹配模式的缓存"""
        import fnmatch

        keys_to_delete = []
        for key in self._cache.keys():
            if fnmatch.fnmatch(key, pattern):
                keys_to_delete.append(key)

        for key in keys_to_delete:
            await self.delete(key)

    async def clear_all(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        self._ttl.clear()

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        value = await self.get(key)
        return value is not None

    def get_size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)

    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            "total_keys": len(self._cache),
            "expired_keys": len([
                k for k, exp in self._ttl.items()
                if datetime.now() > exp
            ]),
            "memory_usage": len(str(self._cache))  # Rough estimate
        }


def cache_result(ttl: int = 300, key_func=None):
    """
    缓存装饰器
    Cache decorator for function results
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"

            # Try to get from cache
            cache_manager = wrapper._cache_manager if hasattr(wrapper, '_cache_manager') else None
            if cache_manager:
                cached_result = await cache_manager.get(cache_key)
                if cached_result is not None:
                    return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            if cache_manager:
                await cache_manager.set(cache_key, result, ttl)

            return result

        # Add cache manager setter
        def set_cache_manager(manager):
            wrapper._cache_manager = manager

        wrapper.set_cache_manager = set_cache_manager
        return wrapper
    return decorator
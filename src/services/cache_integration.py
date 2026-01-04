"""
缓存集成适配器
Cache Integration Adapter

将新的统一缓存系统集成到现有的Manager类中。
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Union, Callable

from .cache_manager import CacheManager, get_cache_manager
from .cache_decorators import cached, invalidate_cache
from .cache_strategy import CacheStrategies

logger = logging.getLogger(__name__)


class CacheMixin:
    """
    缓存混入类

    为Manager类提供缓存功能。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache_manager = get_cache_manager()
        self._cache_enabled = True

    def enable_cache(self, enabled: bool = True):
        """启用或禁用缓存"""
        self._cache_enabled = enabled

    def cache_get(self, strategy_name: str, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        if not self._cache_enabled:
            return default
        return self._cache_manager.get(strategy_name, key, default)

    def cache_set(self, strategy_name: str, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        if not self._cache_enabled:
            return False
        return self._cache_manager.set(strategy_name, key, value, ttl)

    def cache_delete(self, strategy_name: str, key: str) -> bool:
        """删除缓存值"""
        if not self._cache_enabled:
            return False
        return self._cache_manager.delete(strategy_name, key)

    def cache_clear_pattern(self, strategy_name: str, pattern: str) -> int:
        """清除匹配模式的缓存"""
        if not self._cache_enabled:
            return 0
        return self._cache_manager.clear_pattern(strategy_name, pattern)

    def cache_exists(self, strategy_name: str, key: str) -> bool:
        """检查缓存是否存在"""
        if not self._cache_enabled:
            return False
        return self._cache_manager.exists(strategy_name, key)


class StrategyManagerCacheMixin(CacheMixin):
    """
    策略管理器缓存混入

    专门为策略管理器优化的缓存功能。
    """

    # 策略相关的缓存键
    CACHE_KEYS = {
        "strategy": "strategy_{id}",
        "strategy_performance": "strategy_performance_{id}",
        "strategy_list": "strategy_list_{user_id}",
        "strategy_list_all": "strategy_list_all",
        "strategy_parameters": "strategy_parameters_{id}",
        "strategy_status": "strategy_status_{id}",
        "execution_results": "execution_results_{id}",
        "backtest_results": "backtest_results_{id}",
        "market_data": "market_data_{symbol}_{interval}",
        "user_preferences": "user_preferences_{user_id}",
        "dashboard_data": "dashboard_data_{user_id}"
    }

    def get_strategy_cache(self, strategy_id: str) -> Optional[Dict]:
        """获取策略缓存"""
        return self.cache_get("strategy", f"strategy_{strategy_id}")

    def set_strategy_cache(self, strategy_id: str, strategy_data: Dict, ttl: int = 300) -> bool:
        """设置策略缓存"""
        return self.cache_set("strategy", f"strategy_{strategy_id}", strategy_data, ttl)

    def invalidate_strategy_cache(self, strategy_id: str) -> bool:
        """失效策略相关缓存"""
        patterns = [
            f"strategy_{strategy_id}",
            f"strategy_performance_{strategy_id}",
            f"strategy_parameters_{strategy_id}",
            f"strategy_status_{strategy_id}",
            f"execution_results_{strategy_id}",
            f"backtest_results_{strategy_id}"
        ]
        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.cache_clear_pattern("strategy", pattern)
            total_deleted += self.cache_clear_pattern("performance", pattern)
            total_deleted += self.cache_clear_pattern("api_stats", pattern)
        return total_deleted > 0

    def get_strategy_performance_cache(self, strategy_id: str) -> Optional[Dict]:
        """获取策略性能缓存"""
        return self.cache_get("performance", f"strategy_performance_{strategy_id}")

    def set_strategy_performance_cache(self, strategy_id: str, performance_data: Dict, ttl: int = 60) -> bool:
        """设置策略性能缓存"""
        return self.cache_set("performance", f"strategy_performance_{strategy_id}", performance_data, ttl)

    def get_user_strategy_list_cache(self, user_id: Union[int, str]) -> Optional[List[Dict]]:
        """获取用户策略列表缓存"""
        return self.cache_get("user", f"strategies_{user_id}")

    def set_user_strategy_list_cache(self, user_id: Union[int, str], strategy_list: List[Dict], ttl: int = 120) -> bool:
        """设置用户策略列表缓存"""
        return self.cache_set("user", f"strategies_{user_id}", strategy_list, ttl)

    def invalidate_user_cache(self, user_id: Union[int, str]) -> int:
        """失效用户相关缓存"""
        patterns = [
            f"strategies_{user_id}",
            f"dashboard_{user_id}",
            f"user_{user_id}"
        ]
        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.cache_clear_pattern("user", pattern)
        return total_deleted

    def get_market_data_cache(self, symbol: str, interval: str = "1d") -> Optional[Dict]:
        """获取市场数据缓存"""
        return self.cache_get("market_data", f"{symbol}_{interval}")

    def set_market_data_cache(self, symbol: str, interval: str, data: Dict, ttl: int = 5) -> bool:
        """设置市场数据缓存"""
        return self.cache_set("market_data", f"{symbol}_{interval}", data, ttl)

    def get_user_dashboard_cache(self, user_id: Union[int, str]) -> Optional[Dict]:
        """获取用户仪表板缓存"""
        return self.cache_get("user", f"dashboard_{user_id}")

    def set_user_dashboard_cache(self, user_id: Union[int, str], dashboard_data: Dict, ttl: int = 30) -> bool:
        """设置用户仪表板缓存"""
        return self.cache_set("user", f"dashboard_{user_id}", dashboard_data, ttl)

    def get_user_preferences_cache(self, user_id: Union[int, str]) -> Optional[Dict]:
        """获取用户偏好设置缓存"""
        return self.cache_get("user", f"preferences_{user_id}")

    def set_user_preferences_cache(self, user_id: Union[int, str], preferences: Dict, ttl: int = 600) -> bool:
        """设置用户偏好设置缓存"""
        return self.cache_set("user", f"preferences_{user_id}", preferences, ttl)


class AsyncCacheAdapter:
    """
    异步缓存适配器

    为异步API提供缓存支持。
    """

    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self._cache_manager = cache_manager or get_cache_manager()

    async def get(self, strategy_name: str, key: str, default: Any = None) -> Any:
        """异步获取缓存值"""
        # 在线程池中执行同步的缓存操作
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._cache_manager.get,
            strategy_name,
            key,
            default
        )

    async def set(self, strategy_name: str, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """异步设置缓存值"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._cache_manager.set,
            strategy_name,
            key,
            value,
            ttl
        )

    async def delete(self, strategy_name: str, key: str) -> bool:
        """异步删除缓存值"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._cache_manager.delete,
            strategy_name,
            key
        )

    async def clear_pattern(self, strategy_name: str, pattern: str) -> int:
        """异步清除匹配模式的缓存"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._cache_manager.clear_pattern,
            strategy_name,
            pattern
        )

    async def exists(self, strategy_name: str, key: str) -> bool:
        """异步检查缓存是否存在"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._cache_manager.exists,
            strategy_name,
            key
        )


def cached_method(strategy_name: str, ttl: Optional[int] = None, key_prefix: str = ""):
    """
    方法缓存装饰器（专门用于类方法）

    Args:
        strategy_name: 缓存策略名称
        ttl: TTL（秒）
        key_prefix: 键前缀

    Example:
        class MyManager(StrategyManagerCacheMixin):
            @cached_method("strategy", ttl=60)
            def get_strategy_data(self, strategy_id: str):
                return self.load_from_database(strategy_id)
    """
    def decorator(method: Callable) -> Callable:
        def wrapper(self, *args, **kwargs) -> Any:
            if not hasattr(self, '_cache_enabled') or not self._cache_enabled:
                return method(self, *args, **kwargs)

            # 构建缓存键
            key_parts = [key_prefix or method.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)

            # 尝试从缓存获取
            cache_manager = get_cache_manager()
            cached_result = cache_manager.get(strategy_name, cache_key)

            if cached_result is not None:
                return cached_result

            # 执行方法并缓存结果
            try:
                result = method(self, *args, **kwargs)
                cache_manager.set(strategy_name, cache_key, result, ttl)
                return result
            except Exception as e:
                logger.error(f"Error in cached method {method.__name__}: {e}")
                raise

        return wrapper
    return decorator


def invalidate_cache_method(strategy_name: str, pattern_template: str = ""):
    """
    方法缓存失效装饰器

    Args:
        strategy_name: 缓存策略名称
        pattern_template: 模式模板，可以使用方法参数

    Example:
        class MyManager(StrategyManagerCacheMixin):
            @invalidate_cache_method("strategy", "strategy_{id}")
            def update_strategy(self, strategy_id: str, data: dict):
                return self.update_in_database(strategy_id, data)
    """
    def decorator(method: Callable) -> Callable:
        def wrapper(self, *args, **kwargs) -> Any:
            # 执行方法
            try:
                result = method(self, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in invalidate_cache method {method.__name__}: {e}")
                raise

            # 失效缓存
            if hasattr(self, '_cache_enabled') and self._cache_enabled:
                try:
                    cache_manager = get_cache_manager()

                    # 构建模式
                    if pattern_template:
                        # 尝试格式化模板
                        try:
                            pattern = pattern_template.format(*args, **kwargs)
                        except (KeyError, IndexError):
                            # 格式化失败，使用原始模板
                            pattern = pattern_template
                    else:
                        # 使用方法名作为模式
                        pattern = method.__name__

                    cache_manager.clear_pattern(strategy_name, pattern)

                except Exception as e:
                    logger.warning(f"Failed to invalidate cache for {strategy_name}: {e}")

            return result

        return wrapper
    return decorator


# 全局异步缓存适配器实例
_async_adapter: Optional[AsyncCacheAdapter] = None


def get_async_adapter() -> AsyncCacheAdapter:
    """获取全局异步缓存适配器"""
    global _async_adapter
    if _async_adapter is None:
        _async_adapter = AsyncCacheAdapter()
    return _async_adapter


# 批量缓存操作辅助函数
class BatchCacheHelper:
    """批量缓存操作辅助类"""

    @staticmethod
    def batch_get_strategies(strategy_ids: List[str]) -> Dict[str, Optional[Dict]]:
        """批量获取策略缓存"""
        cache_manager = get_cache_manager()
        results = {}
        for strategy_id in strategy_ids:
            results[strategy_id] = cache_manager.get("strategy", f"strategy_{strategy_id}")
        return results

    @staticmethod
    def batch_set_strategies(strategies: Dict[str, Dict], ttl: int = 300) -> int:
        """批量设置策略缓存"""
        cache_manager = get_cache_manager()
        success_count = 0
        for strategy_id, strategy_data in strategies.items():
            if cache_manager.set("strategy", f"strategy_{strategy_id}", strategy_data, ttl):
                success_count += 1
        return success_count

    @staticmethod
    def batch_invalidate_strategies(strategy_ids: List[str]) -> int:
        """批量失效策略缓存"""
        cache_manager = get_cache_manager()
        total_deleted = 0
        for strategy_id in strategy_ids:
            patterns = [
                f"strategy_{strategy_id}",
                f"strategy_performance_{strategy_id}",
                f"strategy_parameters_{strategy_id}"
            ]
            for pattern in patterns:
                total_deleted += cache_manager.clear_pattern("strategy", pattern)
        return total_deleted


__all__ = [
    "CacheMixin",
    "StrategyManagerCacheMixin",
    "AsyncCacheAdapter",
    "get_async_adapter",
    "cached_method",
    "invalidate_cache_method",
    "BatchCacheHelper"
]
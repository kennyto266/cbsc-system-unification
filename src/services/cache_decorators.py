"""
缓存装饰器
Cache Decorators

提供便捷的缓存装饰器，简化函数缓存的使用。
"""

import functools
import hashlib
import json
import time
import logging
from typing import Any, Callable, Optional, Union, Tuple

from .cache_manager import get_cache_manager
from .cache_strategy import CacheStrategy, CacheLevel, EvictionPolicy

logger = logging.getLogger(__name__)


def cached(
    strategy_name: str,
    key_prefix: str = "",
    ttl: Optional[int] = None,
    key_builder: Optional[Callable[..., str]] = None,
    unless: Optional[Callable[..., bool]] = None,
    condition: Optional[Callable[..., bool]] = None
) -> Callable:
    """
    缓存装饰器

    Args:
        strategy_name: 缓存策略名称
        key_prefix: 缓存键前缀
        ttl: 自定义TTL（秒）
        key_builder: 自定义键构建函数
        unless: 当返回True时不缓存
        condition: 当返回True时才缓存

    Returns:
        装饰器函数

    Example:
        @cached("strategy", ttl=60)
        def get_strategy_data(strategy_id: str):
            return load_strategy_from_db(strategy_id)

        @cached("market_data", key_builder=lambda symbol, interval: f"{symbol}_{interval}")
        def get_market_data(symbol: str, interval: str):
            return fetch_market_data(symbol, interval)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 检查是否应该跳过缓存
            if unless and unless(*args, **kwargs):
                return func(*args, **kwargs)

            if condition and not condition(*args, **kwargs):
                return func(*args, **kwargs)

            # 构建缓存键
            cache_key = _build_cache_key(func, key_prefix, key_builder, *args, **kwargs)

            # 尝试从缓存获取
            cache_manager = get_cache_manager()
            cached_result = cache_manager.get(strategy_name, cache_key)

            if cached_result is not None:
                return cached_result

            # 执行函数并缓存结果
            try:
                result = func(*args, **kwargs)
                cache_manager.set(strategy_name, cache_key, result, ttl)
                return result
            except Exception as e:
                logger.error(f"Error in cached function {func.__name__}: {e}")
                raise

        return wrapper
    return decorator


def cached_result(
    strategy_name: str,
    result_key: str,
    ttl: Optional[int] = None
) -> Callable:
    """
    缓存函数结果的装饰器（简化版）

    Args:
        strategy_name: 缓存策略名称
        result_key: 固定的缓存键
        ttl: 自定义TTL（秒）

    Example:
        @cached_result("config", "app_config")
        def load_config():
            return load_configuration()
    """
    return cached(strategy_name, key_prefix=result_key, ttl=ttl)


def cache_on_arguments(
    strategy_name: str,
    ttl: Optional[int] = None,
    arg_names: Optional[list] = None
) -> Callable:
    """
    基于函数参数的缓存装饰器

    Args:
        strategy_name: 缓存策略名称
        ttl: 自定义TTL（秒）
        arg_names: 要包含在键中的参数名列表，None表示所有参数

    Example:
        @cache_on_arguments("performance", ttl=30)
        def calculate_metrics(data, period="1d"):
            return complex_calculation(data, period)
    """
    def key_builder(*args, **kwargs) -> str:
        # 过滤参数
        if arg_names is not None:
            # 获取函数参数名
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # 只使用指定的参数
            filtered_args = []
            for name in arg_names:
                if name in bound_args.arguments:
                    filtered_args.append(f"{name}={bound_args.arguments[name]}")

            return hashlib.md5(str(tuple(filtered_args)).encode()).hexdigest()

        # 使用所有参数
        return hashlib.md5(str((args, tuple(sorted(kwargs.items())))).encode()).hexdigest()

    def decorator(func: Callable) -> Callable:
        # 将key_builder绑定到函数以获取正确的签名
        nonlocal key_builder

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            cache_key = key_builder(*args, **kwargs)

            cache_manager = get_cache_manager()
            cached_result = cache_manager.get(strategy_name, cache_key)

            if cached_result is not None:
                return cached_result

            try:
                result = func(*args, **kwargs)
                cache_manager.set(strategy_name, cache_key, result, ttl)
                return result
            except Exception as e:
                logger.error(f"Error in cache_on_arguments function {func.__name__}: {e}")
                raise

        return wrapper
    return decorator


def invalidate_cache(
    strategy_name: str,
    key_pattern: Optional[str] = None,
    key_builder: Optional[Callable[..., str]] = None
) -> Callable:
    """
    缓存失效装饰器

    Args:
        strategy_name: 缓存策略名称
        key_pattern: 要失效的键模式
        key_builder: 键构建函数

    Example:
        @invalidate_cache("strategy", "strategy_*")
        def update_strategy(strategy_id: str, data: dict):
            return update_strategy_in_db(strategy_id, data)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 执行函数
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in invalidate_cache function {func.__name__}: {e}")
                raise

            # 失效缓存
            try:
                cache_manager = get_cache_manager()

                if key_pattern:
                    # 失效匹配模式的缓存
                    cache_manager.clear_pattern(strategy_name, key_pattern)
                elif key_builder:
                    # 构建特定键并失效
                    cache_key = key_builder(*args, **kwargs)
                    cache_manager.delete(strategy_name, cache_key)

            except Exception as e:
                logger.warning(f"Failed to invalidate cache for {strategy_name}: {e}")

            return result

        return wrapper
    return decorator


def cache_with_fallback(
    strategy_name: str,
    fallback_func: Callable,
    ttl: Optional[int] = None
) -> Callable:
    """
    带有回退函数的缓存装饰器

    Args:
        strategy_name: 缓存策略名称
        fallback_func: 缓存未命中时的回退函数
        ttl: 自定义TTL（秒）

    Example:
        @cache_with_fallback("market_data", fetch_from_exchange)
        def get_market_data(symbol: str):
            # 尝试从缓存获取，如果失败则调用fetch_from_exchange
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 首先尝试原始函数
            try:
                cache_manager = get_cache_manager()
                cache_key = _build_cache_key(func, "", None, *args, **kwargs)

                cached_result = cache_manager.get(strategy_name, cache_key)
                if cached_result is not None:
                    return cached_result

                result = func(*args, **kwargs)
                cache_manager.set(strategy_name, cache_key, result, ttl)
                return result

            except Exception as e:
                logger.warning(f"Primary function failed, using fallback: {e}")
                # 使用回退函数
                try:
                    return fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback function also failed: {fallback_error}")
                    raise

        return wrapper
    return decorator


def timed_cache(
    strategy_name: str,
    ttl: int,
    refresh_interval: Optional[int] = None
) -> Callable:
    """
    定时刷新缓存装饰器

    Args:
        strategy_name: 缓存策略名称
        ttl: 缓存TTL（秒）
        refresh_interval: 刷新间隔（秒），None表示不自动刷新

    Example:
        @timed_cache("config", ttl=3600, refresh_interval=300)  # 每小时刷新，每5分钟检查
        def get_global_config():
            return load_global_configuration()
    """
    last_refresh: Dict[str, float] = {}

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            cache_key = _build_cache_key(func, "", None, *args, **kwargs)
            cache_manager = get_cache_manager()

            current_time = time.time()
            last_time = last_refresh.get(cache_key, 0)

            # 检查是否需要刷新
            need_refresh = (
                refresh_interval and
                (current_time - last_time) >= refresh_interval
            )

            # 尝试从缓存获取
            cached_result = cache_manager.get(strategy_name, cache_key)

            if cached_result is not None and not need_refresh:
                return cached_result

            # 刷新缓存
            try:
                result = func(*args, **kwargs)
                cache_manager.set(strategy_name, cache_key, result, ttl)
                last_refresh[cache_key] = current_time
                return result
            except Exception as e:
                logger.error(f"Error in timed_cache function {func.__name__}: {e}")
                raise

        return wrapper
    return decorator


def async_cached(
    strategy_name: str,
    key_prefix: str = "",
    ttl: Optional[int] = None
) -> Callable:
    """
    异步函数缓存装饰器

    Args:
        strategy_name: 缓存策略名称
        key_prefix: 缓存键前缀
        ttl: 自定义TTL（秒）

    Example:
        @async_cached("api_stats", ttl=60)
        async def fetch_api_stats():
            return await fetch_stats_from_api()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            cache_key = _build_cache_key(func, key_prefix, None, *args, **kwargs)
            cache_manager = get_cache_manager()

            # 尝试从缓存获取
            cached_result = cache_manager.get(strategy_name, cache_key)
            if cached_result is not None:
                return cached_result

            # 执行异步函数并缓存结果
            try:
                result = await func(*args, **kwargs)
                cache_manager.set(strategy_name, cache_key, result, ttl)
                return result
            except Exception as e:
                logger.error(f"Error in async_cached function {func.__name__}: {e}")
                raise

        return wrapper
    return decorator


def _build_cache_key(
    func: Callable,
    prefix: str,
    key_builder: Optional[Callable[..., str]],
    *args,
    **kwargs
) -> str:
    """
    构建缓存键

    Args:
        func: 函数对象
        prefix: 键前缀
        key_builder: 自定义键构建函数
        *args: 函数位置参数
        **kwargs: 函数关键字参数

    Returns:
        缓存键
    """
    if key_builder:
        return key_builder(*args, **kwargs)

    # 默认键构建逻辑
    key_parts = [func.__module__, func.__name__]

    if prefix:
        key_parts.append(prefix)

    # 序列化参数
    try:
        # 尝试JSON序列化
        params_str = json.dumps([args, sorted(kwargs.items())], sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        key_parts.append(params_hash)
    except (TypeError, ValueError):
        # 如果无法JSON序列化，使用字符串表示
        params_str = str(args) + str(sorted(kwargs.items()))
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        key_parts.append(params_hash)

    return ":".join(key_parts)


# 类方法装饰器
def method_cached(
    strategy_name: str,
    key_prefix: str = "",
    ttl: Optional[int] = None,
    include_self: bool = False
) -> Callable:
    """
    类方法缓存装饰器

    Args:
        strategy_name: 缓存策略名称
        key_prefix: 缓存键前缀
        ttl: 自定义TTL（秒）
        include_self: 是否包含self在键中

    Example:
        class StrategyManager:
            @method_cached("strategy", include_self=False)
            def get_strategy(self, strategy_id: str):
                return self._load_strategy(strategy_id)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            # 构建参数
            cache_args = (self,) if include_self else args
            cache_kwargs = kwargs

            # 构建键
            key_parts = [func.__name__]
            if prefix:
                key_parts.insert(0, prefix)

            # 构建完整键
            cache_key = _build_cache_key(
                lambda *a, **k: ":".join(key_parts),
                "",
                None,
                *cache_args,
                **cache_kwargs
            )

            cache_manager = get_cache_manager()
            cached_result = cache_manager.get(strategy_name, cache_key)

            if cached_result is not None:
                return cached_result

            try:
                result = func(self, *args, **kwargs)
                cache_manager.set(strategy_name, cache_key, result, ttl)
                return result
            except Exception as e:
                logger.error(f"Error in method_cached function {func.__name__}: {e}")
                raise

        return wrapper
    return decorator


# 批量缓存操作
class BatchCache:
    """批量缓存操作辅助类"""

    def __init__(self, strategy_name: str):
        self.strategy_name = strategy_name
        self.cache_manager = get_cache_manager()
        self.operations = []

    def get(self, key: str) -> Any:
        """批量获取（暂不支持，返回单个）"""
        return self.cache_manager.get(self.strategy_name, key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """批量设置（延迟执行）"""
        self.operations.append(("set", key, value, ttl))

    def delete(self, key: str):
        """批量删除（延迟执行）"""
        self.operations.append(("delete", key, None, None))

    def clear_pattern(self, pattern: str):
        """批量模式清理（延迟执行）"""
        self.operations.append(("clear_pattern", pattern, None, None))

    def execute(self) -> int:
        """执行所有批量操作"""
        success_count = 0

        for op in self.operations:
            op_type = op[0]

            try:
                if op_type == "set":
                    _, key, value, ttl = op
                    if self.cache_manager.set(self.strategy_name, key, value, ttl):
                        success_count += 1
                elif op_type == "delete":
                    _, key, _, _ = op
                    if self.cache_manager.delete(self.strategy_name, key):
                        success_count += 1
                elif op_type == "clear_pattern":
                    _, pattern, _, _ = op
                    success_count += self.cache_manager.clear_pattern(self.strategy_name, pattern)
            except Exception as e:
                logger.error(f"Batch cache operation failed: {e}")

        self.operations.clear()
        return success_count

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.execute()


# 便捷函数
def create_batch_cache(strategy_name: str) -> BatchCache:
    """创建批量缓存操作对象"""
    return BatchCache(strategy_name)


__all__ = [
    "cached",
    "cached_result",
    "cache_on_arguments",
    "invalidate_cache",
    "cache_with_fallback",
    "timed_cache",
    "async_cached",
    "method_cached",
    "BatchCache",
    "create_batch_cache"
]
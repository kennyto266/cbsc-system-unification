"""
缓存管理工具
Cache Management Utilities

职责：
- 缓存操作封装
- 缓存策略管理
- 缓存失效处理
"""

import json
import asyncio
from typing import Any, Optional, List, Dict, Union
from datetime import datetime, timedelta
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class CacheManager:
    """缓存管理器"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", use_memory: bool = True):
        """
        初始化缓存管理器

        Args:
            redis_url: Redis连接URL
            use_memory: 是否使用内存缓存作为fallback
        """
        self.redis_url = redis_url
        self.use_memory = use_memory
        self.default_ttl = 300  # 5分钟
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self._redis_client = None

    async def _get_redis_client(self):
        """获取Redis客户端"""
        if self._redis_client is None:
            try:
                import redis.asyncio as redis
                self._redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # 测试连接
                await self._redis_client.ping()
                logger.info("Redis连接成功")
            except Exception as e:
                logger.warning(f"Redis连接失败，使用内存缓存: {e}")
                self._redis_client = None

        return self._redis_client

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存

        Args:
            key: 缓存键

        Returns:
            缓存值或None
        """
        # 尝试从Redis获取
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                value = await redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis获取缓存失败: {e}")

        # 从内存缓存获取
        if self.use_memory and key in self.memory_cache:
            cache_item = self.memory_cache[key]
            if datetime.now() < cache_item["expires_at"]:
                return cache_item["value"]
            else:
                # 过期，删除
                del self.memory_cache[key]

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）

        Returns:
            是否成功
        """
        ttl = ttl or self.default_ttl
        serialized_value = json.dumps(value, default=str)

        # 尝试设置到Redis
        redis_client = await self._get_redis_client()
        redis_success = False
        if redis_client:
            try:
                await redis_client.setex(key, ttl, serialized_value)
                redis_success = True
            except Exception as e:
                logger.error(f"Redis设置缓存失败: {e}")

        # 设置到内存缓存
        if self.use_memory:
            self.memory_cache[key] = {
                "value": value,
                "expires_at": datetime.now() + timedelta(seconds=ttl)
            }

        return redis_success or self.use_memory

    async def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否成功
        """
        # 从Redis删除
        redis_client = await self._get_redis_client()
        redis_success = False
        if redis_client:
            try:
                result = await redis_client.delete(key)
                redis_success = result > 0
            except Exception as e:
                logger.error(f"Redis删除缓存失败: {e}")

        # 从内存缓存删除
        memory_success = True
        if self.use_memory and key in self.memory_cache:
            del self.memory_cache[key]

        return redis_success or memory_success

    async def delete_pattern(self, pattern: str) -> int:
        """
        删除匹配模式的所有缓存

        Args:
            pattern: 匹配模式

        Returns:
            删除的数量
        """
        deleted_count = 0

        # 从Redis删除
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                keys = await redis_client.keys(pattern)
                if keys:
                    deleted_count = await redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"Redis批量删除缓存失败: {e}")

        # 从内存缓存删除
        if self.use_memory:
            keys_to_delete = []
            for key in self.memory_cache.keys():
                if self._match_pattern(key, pattern):
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self.memory_cache[key]
                deleted_count += 1

        return deleted_count

    async def exists(self, key: str) -> bool:
        """
        检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        # 检查Redis
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                return await redis_client.exists(key) > 0
            except Exception as e:
                logger.error(f"Redis检查缓存存在失败: {e}")

        # 检查内存缓存
        if self.use_memory and key in self.memory_cache:
            cache_item = self.memory_cache[key]
            if datetime.now() < cache_item["expires_at"]:
                return True
            else:
                del self.memory_cache[key]

        return False

    async def expire(self, key: str, ttl: int) -> bool:
        """
        设置缓存过期时间

        Args:
            key: 缓存键
            ttl: 过期时间（秒）

        Returns:
            是否成功
        """
        # Redis设置过期时间
        redis_client = await self._get_redis_client()
        redis_success = False
        if redis_client:
            try:
                result = await redis_client.expire(key, ttl)
                redis_success = result
            except Exception as e:
                logger.error(f"Redis设置过期时间失败: {e}")

        # 内存缓存设置过期时间
        memory_success = False
        if self.use_memory and key in self.memory_cache:
            self.memory_cache[key]["expires_at"] = datetime.now() + timedelta(seconds=ttl)
            memory_success = True

        return redis_success or memory_success

    async def ttl(self, key: str) -> int:
        """
        获取缓存剩余时间

        Args:
            key: 缓存键

        Returns:
            剩余时间（秒），-1表示永不过期，-2表示不存在
        """
        # Redis TTL
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                return await redis_client.ttl(key)
            except Exception as e:
                logger.error(f"Redis获取TTL失败: {e}")

        # 内存缓存TTL
        if self.use_memory and key in self.memory_cache:
            cache_item = self.memory_cache[key]
            remaining = (cache_item["expires_at"] - datetime.now()).total_seconds()
            return int(remaining) if remaining > 0 else -2

        return -2

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        递增缓存值

        Args:
            key: 缓存键
            amount: 递增量

        Returns:
            递增后的值
        """
        # Redis递增
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                return await redis_client.incrby(key, amount)
            except Exception as e:
                logger.error(f"Redis递增失败: {e}")

        # 内存缓存递增
        if self.use_memory:
            if key in self.memory_cache:
                if isinstance(self.memory_cache[key]["value"], int):
                    self.memory_cache[key]["value"] += amount
                    return self.memory_cache[key]["value"]
            else:
                self.memory_cache[key] = {
                    "value": amount,
                    "expires_at": datetime.now() + timedelta(seconds=self.default_ttl)
                }
                return amount

        return None

    async def get_multiple(self, keys: List[str]) -> Dict[str, Any]:
        """
        批量获取缓存

        Args:
            keys: 缓存键列表

        Returns:
            键值对字典
        """
        result = {}

        # 从Redis批量获取
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                values = await redis_client.mget(keys)
                for key, value in zip(keys, values):
                    if value:
                        result[key] = json.loads(value)
            except Exception as e:
                logger.error(f"Redis批量获取失败: {e}")

        # 补充从内存缓存获取
        if self.use_memory:
            for key in keys:
                if key not in result and key in self.memory_cache:
                    cache_item = self.memory_cache[key]
                    if datetime.now() < cache_item["expires_at"]:
                        result[key] = cache_item["value"]

        return result

    async def set_multiple(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        批量设置缓存

        Args:
            mapping: 键值对字典
            ttl: 过期时间（秒）

        Returns:
            是否成功
        """
        ttl = ttl or self.default_ttl
        success = True

        for key, value in mapping.items():
            if not await self.set(key, value, ttl):
                success = False

        return success

    def _match_pattern(self, key: str, pattern: str) -> bool:
        """
        简单的通配符匹配

        Args:
            key: 键
            pattern: 模式

        Returns:
            是否匹配
        """
        # 简单实现，支持*通配符
        import fnmatch
        return fnmatch.fnmatch(key, pattern)

    async def clear_all(self) -> bool:
        """
        清空所有缓存

        Returns:
            是否成功
        """
        # 清空Redis
        redis_client = await self._get_redis_client()
        redis_success = False
        if redis_client:
            try:
                await redis_client.flushdb()
                redis_success = True
            except Exception as e:
                logger.error(f"Redis清空失败: {e}")

        # 清空内存缓存
        self.memory_cache.clear()
        memory_success = True

        return redis_success or memory_success

    async def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息
        """
        stats = {
            "memory_cache": {
                "keys_count": len(self.memory_cache),
                "use_memory": self.use_memory
            },
            "redis": {
                "connected": False,
                "url": self.redis_url
            }
        }

        # Redis统计
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                info = await redis_client.info()
                stats["redis"] = {
                    "connected": True,
                    "url": self.redis_url,
                    "used_memory": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                    "total_commands_processed": info.get("total_commands_processed")
                }
            except Exception as e:
                logger.error(f"获取Redis统计失败: {e}")

        return stats

    def __del__(self):
        """析构函数，关闭Redis连接"""
        if self._redis_client:
            try:
                # 关闭Redis连接需要在异步环境中
                # 这里只是标记，实际关闭需要在使用的地方处理
                pass
            except:
                pass


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

    STRATEGY_DETAIL = "strategy:detail:{strategy_id}"
    STRATEGY_LIST = "strategies:list:{page}:{page_size}:{type}:{status}:{user_id}"
    USER_PREFERENCES = "preferences:{user_id}"
    DASHBOARD_DATA = "dashboard:data:{user_id}"
    EXECUTION_STATUS = "execution:status:{execution_id}"
    PERFORMANCE_METRICS = "performance:metrics:{strategy_id}:{time_range}"
    USER_STRATEGIES = "user:strategies:{user_id}"
    TEMPLATE_LIST = "templates:list:{type}"

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
import json
import logging
import os
import pickle
import time
from functools import wraps
from typing import Any, Optional, Union

import redis

logger = logging.getLogger("quant_system")


class CacheManager:
    """Redis缓存管理器"""

    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379 / 0")
        self.redis_client = redis.from_url(redis_url)
        self.default_ttl = int(os.getenv("CACHE_TTL", "3600"))  # 默认1小时

        # 测试连接
        try:
            self.redis_client.ping()
            logger.info("Redis cache connected successfully")
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}. Cache will be disabled.")
            self.redis_client = None

    def _is_connected(self) -> bool:
        """检查Redis连接状态"""
        return self.redis_client is not None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        if not self._is_connected():
            return False

        try:
            serialized_value = json.dumps(value, default=str)
            ttl_value = ttl or self.default_ttl
            return bool(self.redis_client.setex(key, ttl_value, serialized_value))
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self._is_connected():
            return None

        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._is_connected():
            return False

        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete failed for key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._is_connected():
            return False

        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists check failed for key {key}: {e}")
            return False

    def set_multiple(self, key_value_pairs: dict, ttl: Optional[int] = None) -> bool:
        """批量设置缓存"""
        if not self._is_connected():
            return False

        try:
            pipeline = self.redis_client.pipeline()
            ttl_value = ttl or self.default_ttl

            for key, value in key_value_pairs.items():
                serialized_value = json.dumps(value, default=str)
                pipeline.setex(key, ttl_value, serialized_value)

            pipeline.execute()
            return True
        except Exception as e:
            logger.error(f"Cache set_multiple failed: {e}")
            return False

    def get_multiple(self, keys: list) -> dict:
        """批量获取缓存"""
        if not self._is_connected():
            return {}

        try:
            values = self.redis_client.mget(keys)
            result = {}

            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to decode cached value for key {key}")

            return result
        except Exception as e:
            logger.error(f"Cache get_multiple failed: {e}")
            return {}

    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """增加计数器"""
        if not self._is_connected():
            return None

        try:
            return self.redis_client.incr(key, amount)
        except Exception as e:
            logger.error(f"Cache incr failed for key {key}: {e}")
            return None

    def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        if not self._is_connected():
            return False

        try:
            return bool(self.redis_client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Cache expire failed for key {key}: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的键"""
        if not self._is_connected():
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear_pattern failed for pattern {pattern}: {e}")
            return 0

    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        if not self._is_connected():
            return {"status": "disconnected"}

        try:
            info = self.redis_client.info()
            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human", "N / A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_keys": self.redis_client.dbsize(),
                "uptime_days": info.get("uptime_in_days", 0),
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"status": "error", "error": str(e)}


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """缓存装饰器"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            key_parts = [key_prefix or func.__name__]
            key_parts.extend([str(arg) for arg in args[1:]])  # 跳过self
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            cache_key = ":".join(key_parts)

            # 尝试从缓存获取
            cache_manager = (
                args[0].cache if hasattr(args[0], "cache") else cache_manager_global
            )
            cached_result = cache_manager.get(cache_key)

            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result

            # 执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            if result is not None:
                cache_manager.set(cache_key, result, ttl)
                logger.debug(f"Cached result for {cache_key}")

            return result

        return wrapper

    return decorator


# 全局实例
cache_manager_global = CacheManager()


# 便捷函数
def get_cache_manager():
    """获取缓存管理器实例"""
    return cache_manager_global

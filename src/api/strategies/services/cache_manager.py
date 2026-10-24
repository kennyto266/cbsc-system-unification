"""
统一缓存管理器
Unified Cache Manager

职责：
- 多级缓存管理（L1内存 + L2 Redis）
- TTL自动过期
- 批量清理
- 性能监控
- Redis降级支持
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from ..models import StrategyType, StrategyStatus, ExecutionStatus, SignalType
from .cache_strategy import CacheStrategy, CacheLevel, SerializationType, get_strategy_for_key

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """缓存统计信息"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    errors: int = 0

    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        total = self.hits + self.misses
        return (self.hits / total) if total > 0 else 0.0

    @property
    def total_ops(self) -> int:
        """总操作数"""
        return self.hits + self.misses + self.sets + self.deletes


class CacheManager:
    """
    统一缓存管理器

    支持多级缓存架构：
    - L1: 内存缓存（快速访问）
    - L2: Redis缓存（持久化、共享）
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        max_memory_items: int = 1000,
        default_ttl: int = 300,
        strategies: Optional[Dict[str, CacheStrategy]] = None
    ):
        """
        初始化缓存管理器

        Args:
            redis_url: Redis连接URL（可选）
            max_memory_items: 内存缓存最大条目数
            default_ttl: 默认TTL（秒）
            strategies: 自定义缓存策略（可选）
        """
        # 基础配置
        self.default_ttl = default_ttl
        self.strategies = strategies

        # L1内存缓存
        self._memory_cache: Dict[str, Any] = {}
        self._memory_ttl: Dict[str, datetime] = {}
        self._max_memory_items = max_memory_items
        self._memory_access_order: List[str] = []  # LRU访问顺序

        # L2 Redis客户端
        self._redis_client: Optional[redis.Redis] = None
        self._redis_available = False

        # 统计信息
        self._stats = CacheStats()

        # 初始化Redis（如果可用）
        if REDIS_AVAILABLE and redis_url:
            asyncio.create_task(self._init_redis(redis_url))

    async def _init_redis(self, redis_url: str) -> None:
        """初始化Redis连接"""
        try:
            self._redis_client = redis.from_url(redis_url, decode_responses=True)
            # 测试连接
            await self._redis_client.ping()
            self._redis_available = True
            logger.info("Redis连接成功")
        except Exception as e:
            logger.warning(f"Redis连接失败，降级到纯内存缓存: {e}")
            self._redis_available = False

    def _get_strategy(self, key: str) -> CacheStrategy:
        """获取键的缓存策略"""
        return get_strategy_for_key(key, self.strategies)

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        优先级：L1 → L2 → None
        """
        strategy = self._get_strategy(key)

        # 尝试从L1获取
        if strategy.level in [CacheLevel.L1, CacheLevel.L1_L2]:
            value = await self._get_from_l1(key)
            if value is not None:
                self._stats.hits += 1
                # 如果是L1_L2，检查是否需要回填L2
                if strategy.level == CacheLevel.L1_L2 and self._redis_available:
                    asyncio.create_task(self._set_to_l2(key, value, strategy))
                return value

        # 尝试从L2获取
        if strategy.level in [CacheLevel.L2, CacheLevel.L1_L2] and self._redis_available:
            value = await self._get_from_l2(key, strategy)
            if value is not None:
                self._stats.hits += 1
                # 回填L1
                if strategy.level == CacheLevel.L1_L2:
                    await self._set_to_l1(key, value, strategy)
                return value

        self._stats.misses += 1
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        expire_after: Optional[int] = None,
        expire_at: Optional[datetime] = None
    ) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒）
            expire_after: TTL（秒）-兼容参数
            expire_at: 绝对过期时间
        """
        strategy = self._get_strategy(key)
        actual_ttl = ttl or expire_after or strategy.ttl

        # 设置到L1
        if strategy.level in [CacheLevel.L1, CacheLevel.L1_L2]:
            await self._set_to_l1(key, value, strategy, actual_ttl, expire_at)

        # 设置到L2
        if strategy.level in [CacheLevel.L2, CacheLevel.L1_L2] and self._redis_available:
            await self._set_to_l2(key, value, strategy, actual_ttl, expire_at)

        self._stats.sets += 1

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        deleted = False

        # 从L1删除
        if key in self._memory_cache:
            await self._delete_from_l1(key)
            deleted = True

        # 从L2删除
        if self._redis_available:
            if await self._delete_from_l2(key):
                deleted = True

        if deleted:
            self._stats.deletes += 1

        return deleted

    async def clear_pattern(self, pattern: str) -> int:
        """
        批量清除匹配模式的缓存

        Args:
            pattern: 匹配模式（支持*通配符）

        Returns:
            删除的键数量
        """
        count = 0

        # 清除L1缓存
        keys_to_delete = []
        for key in self._memory_cache.keys():
            if self._match_pattern(key, pattern):
                keys_to_delete.append(key)

        for key in keys_to_delete:
            await self._delete_from_l1(key)
            count += 1

        # 清除L2缓存
        if self._redis_available:
            try:
                redis_pattern = pattern.replace('*', '*')
                keys = await self._redis_client.keys(redis_pattern)
                if keys:
                    await self._redis_client.delete(*keys)
                    count += len(keys)
            except Exception as e:
                logger.error(f"Redis批量删除失败: {e}")
                self._stats.errors += 1

        return count

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        # 先检查L1
        if key in self._memory_cache:
            # 检查TTL
            if key in self._memory_ttl:
                if datetime.now() > self._memory_ttl[key]:
                    await self._delete_from_l1(key)
                else:
                    return True
            return True

        # 检查L2
        if self._redis_available:
            try:
                return await self._redis_client.exists(key) > 0
            except Exception as e:
                logger.error(f"Redis exists检查失败: {e}")
                self._stats.errors += 1

        return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        递增缓存值（适用于数字类型）

        Args:
            key: 缓存键
            amount: 递增量（默认为1）

        Returns:
            递增后的值
        """
        # 尝试从L1获取并递增
        if key in self._memory_cache:
            value = self._memory_cache[key]
            if isinstance(value, (int, float)):
                new_value = value + amount
                await self.set(key, new_value)
                return new_value

        # 如果Redis可用，使用Redis的INCR操作
        if self._redis_available:
            try:
                new_value = await self._redis_client.incrby(key, amount)
                # 更新L1缓存
                strategy = self._get_strategy(key)
                if strategy.level in [CacheLevel.L1, CacheLevel.L1_L2]:
                    await self._set_to_l1(key, new_value, strategy)
                return new_value
            except Exception as e:
                logger.error(f"Redis递增操作失败: {e}")
                self._stats.errors += 1

        # 默认行为：设置初始值
        await self.set(key, amount)
        return amount

    async def ttl(self, key: str) -> Optional[int]:
        """
        获取键的剩余TTL（秒）

        Returns:
            剩余秒数，如果键不存在或没有TTL则返回None
        """
        # 检查L1 TTL
        if key in self._memory_ttl:
            remaining = self._memory_ttl[key] - datetime.now()
            if remaining.total_seconds() > 0:
                return int(remaining.total_seconds())
            else:
                await self.delete(key)
                return None

        # 检查Redis TTL
        if self._redis_available:
            try:
                ttl = await self._redis_client.ttl(key)
                if ttl >= 0:
                    return ttl
            except Exception as e:
                logger.error(f"Redis TTL查询失败: {e}")
                self._stats.errors += 1

        return None

    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "sets": self._stats.sets,
            "deletes": self._stats.deletes,
            "evictions": self._stats.evictions,
            "errors": self._stats.errors,
            "hit_rate": self._stats.hit_rate,
            "total_ops": self._stats.total_ops,
            "memory_items": len(self._memory_cache),
            "memory_size": len(str(self._memory_cache)),
            "redis_available": self._redis_available,
            "max_memory_items": self._max_memory_items
        }

        # 添加Redis统计（如果可用）
        if self._redis_available:
            try:
                info = await self._redis_client.info()
                stats["redis_memory"] = info.get("used_memory", 0)
                stats["redis_keys"] = info.get("db0", {}).get("keys", 0)
            except Exception as e:
                logger.error(f"Redis统计获取失败: {e}")

        return stats

    async def _get_from_l1(self, key: str) -> Optional[Any]:
        """从L1缓存获取"""
        # 检查TTL
        if key in self._memory_ttl and datetime.now() > self._memory_ttl[key]:
            await self._delete_from_l1(key)
            return None

        value = self._memory_cache.get(key)
        if value is not None:
            # 更新LRU顺序
            if key in self._memory_access_order:
                self._memory_access_order.remove(key)
            self._memory_access_order.append(key)

        return value

    async def _set_to_l1(
        self,
        key: str,
        value: Any,
        strategy: CacheStrategy,
        ttl: Optional[int] = None,
        expire_at: Optional[datetime] = None
    ) -> None:
        """设置到L1缓存"""
        # 检查大小限制
        if strategy.max_size and key not in self._memory_cache:
            while len(self._memory_cache) >= strategy.max_size:
                if self._memory_access_order:
                    oldest_key = self._memory_access_order.pop(0)
                    await self._delete_from_l1(oldest_key)
                    self._stats.evictions += 1
                else:
                    break

        # 设置值
        self._memory_cache[key] = value

        # 设置TTL
        if expire_at:
            self._memory_ttl[key] = expire_at
        elif ttl:
            self._memory_ttl[key] = datetime.now() + timedelta(seconds=ttl)

        # 更新LRU顺序
        if key in self._memory_access_order:
            self._memory_access_order.remove(key)
        self._memory_access_order.append(key)

    async def _delete_from_l1(self, key: str) -> None:
        """从L1缓存删除"""
        self._memory_cache.pop(key, None)
        self._memory_ttl.pop(key, None)
        if key in self._memory_access_order:
            self._memory_access_order.remove(key)

    async def _get_from_l2(self, key: str, strategy: CacheStrategy) -> Optional[Any]:
        """从L2缓存获取"""
        if not self._redis_available:
            return None

        try:
            serialized = await self._redis_client.get(key)
            if serialized:
                return self._deserialize(serialized, strategy.serializer)
        except Exception as e:
            logger.error(f"Redis获取失败: {e}")
            self._stats.errors += 1

        return None

    async def _set_to_l2(
        self,
        key: str,
        value: Any,
        strategy: CacheStrategy,
        ttl: Optional[int] = None,
        expire_at: Optional[datetime] = None
    ) -> None:
        """设置到L2缓存"""
        if not self._redis_available:
            return

        try:
            serialized = self._serialize(value, strategy.serializer)

            if expire_at:
                await self._redis_client.setex(
                    key,
                    int((expire_at - datetime.now()).total_seconds()),
                    serialized
                )
            elif ttl:
                await self._redis_client.setex(key, ttl, serialized)
            else:
                await self._redis_client.set(key, serialized)
        except Exception as e:
            logger.error(f"Redis设置失败: {e}")
            self._stats.errors += 1

    async def _delete_from_l2(self, key: str) -> bool:
        """从L2缓存删除"""
        if not self._redis_available:
            return False

        try:
            return await self._redis_client.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis删除失败: {e}")
            self._stats.errors += 1
            return False

    def _serialize(self, value: Any, method: SerializationType) -> str:
        """序列化值"""
        if method == SerializationType.JSON:
            return json.dumps(value, default=str)
        elif method == SerializationType.PICKLE:
            import pickle
            return pickle.dumps(value)
        elif method == SerializationType.NONE:
            return str(value)
        else:
            raise ValueError(f"不支持的序列化方法: {method}")

    def _deserialize(self, value: str, method: SerializationType) -> Any:
        """反序列化值"""
        if method == SerializationType.JSON:
            return json.loads(value)
        elif method == SerializationType.PICKLE:
            import pickle
            return pickle.loads(value)
        elif method == SerializationType.NONE:
            return value
        else:
            raise ValueError(f"不支持的反序列化方法: {method}")

    def _match_pattern(self, key: str, pattern: str) -> bool:
        """简单模式匹配"""
        if "*" not in pattern:
            return key == pattern
        # 将*转换为.*
        import re
        regex = pattern.replace("*", ".*")
        return re.match(regex, key) is not None

    async def cleanup_expired(self) -> int:
        """清理过期的缓存项"""
        count = 0
        now = datetime.now()

        # 清理L1过期项
        expired_keys = [
            key for key, expiry in self._memory_ttl.items()
            if expiry <= now
        ]

        for key in expired_keys:
            await self._delete_from_l1(key)
            count += 1

        return count

    async def close(self) -> None:
        """关闭缓存管理器"""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_available = False
            logger.info("Redis连接已关闭")

        # 清空内存缓存
        self._memory_cache.clear()
        self._memory_ttl.clear()
        self._memory_access_order.clear()
        logger.info("缓存管理器已关闭")
"""
统一缓存管理器

实现L1（内存）+ L2（Redis）多级缓存系统，为价格和非价格数据提供高性能缓存服务。

Task #31: Data Flow Unification - Price and Non-Price Integration
"""

import asyncio
import json
import logging
import pickle
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from collections import OrderedDict
from threading import RLock
import weakref

from src.api.cache_service import cache_service

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    timestamp: datetime
    ttl: Optional[timedelta] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return datetime.now() > (self.timestamp + self.ttl)

    def update_access(self):
        """更新访问信息"""
        self.access_count += 1
        self.last_accessed = datetime.now()

@dataclass
class CacheStats:
    """缓存统计信息"""
    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    evictions: int = 0
    sets: int = 0
    gets: int = 0

    @property
    def hit_rate(self) -> float:
        """总命中率"""
        total_requests = self.gets
        if total_requests == 0:
            return 0.0
        total_hits = self.l1_hits + self.l2_hits
        return (total_hits / total_requests) * 100

    @property
    def l1_hit_rate(self) -> float:
        """L1缓存命中率"""
        total_requests = self.l1_hits + self.l1_misses
        if total_requests == 0:
            return 0.0
        return (self.l1_hits / total_requests) * 100

    @property
    def l2_hit_rate(self) -> float:
        """L2缓存命中率"""
        total_requests = self.l2_hits + self.l2_misses
        if total_requests == 0:
            return 0.0
        return (self.l2_hits / total_requests) * 100

class LRUICache:
    """线程安全的LRU内存缓存"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = RLock()
        self._stats = CacheStats()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            entry = self.cache.get(key)

            if entry is None:
                self._stats.l1_misses += 1
                return None

            if entry.is_expired():
                del self.cache[key]
                self._stats.l1_misses += 1
                return None

            # 移动到末尾（最近使用）
            self.cache.move_to_end(key)
            entry.update_access()
            self._stats.l1_hits += 1

            return entry.value

    def put(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> None:
        """设置缓存值"""
        with self.lock:
            entry = CacheEntry(
                value=value,
                timestamp=datetime.now(),
                ttl=ttl
            )

            # 如果键已存在，更新值
            if key in self.cache:
                self.cache[key] = entry
                self.cache.move_to_end(key)
            else:
                # 检查是否需要驱逐
                while len(self.cache) >= self.max_size:
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    self._stats.evictions += 1

                self.cache[key] = entry

            self._stats.sets += 1

    def delete(self, key: str) -> bool:
        """删除缓存键"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()

    def size(self) -> int:
        """获取缓存大小"""
        with self.lock:
            return len(self.cache)

    def keys(self) -> List[str]:
        """获取所有键"""
        with self.lock:
            return list(self.cache.keys())

    def cleanup_expired(self) -> int:
        """清理过期条目"""
        with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]

            for key in expired_keys:
                del self.cache[key]

            return len(expired_keys)

    def get_stats(self) -> CacheStats:
        """获取统计信息"""
        return self._stats

class UnifiedCacheManager:
    """统一缓存管理器"""

    def __init__(
        self,
        l1_max_size: int = 1000,
        l2_enabled: bool = True,
        cleanup_interval: int = 300,
        default_ttl: Optional[timedelta] = None
    ):
        self.l1_cache = LRUICache(max_size=l1_max_size)
        self.l2_enabled = l2_enabled
        self.cleanup_interval = cleanup_interval
        self.default_ttl = default_ttl or timedelta(minutes=5)

        # 缓存配置
        self.cache_config = {
            'price_data': timedelta(minutes=1),
            'hkma_data': timedelta(hours=1),
            'sentiment_data': timedelta(minutes=15),
            'unified_data': timedelta(minutes=5),
            'backtest_results': timedelta(days=1),
            'quality_scores': timedelta(minutes=10)
        }

        # 启动清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()

        # 统计信息
        self._total_stats = CacheStats()
        self._last_stats_update = datetime.now()

        logger.info(f"统一缓存管理器初始化: L1大小={l1_max_size}, L2启用={l2_enabled}")

    async def get(
        self,
        key: str,
        cache_type: str = 'unified_data',
        use_l1: bool = True,
        use_l2: bool = True
    ) -> Optional[Any]:
        """获取缓存值（L1优先，然后L2）"""
        self._total_stats.gets += 1

        # L1缓存查找
        if use_l1:
            l1_value = self.l1_cache.get(key)
            if l1_value is not None:
                logger.debug(f"L1缓存命中: {key}")
                return l1_value

        # L2缓存查找
        if use_l2 and self.l2_enabled:
            try:
                # 检查是否已连接到Redis
                if await cache_service.is_connected():
                    l2_value = await self._get_from_l2(key, cache_type)
                    if l2_value is not None:
                        self._total_stats.l2_hits += 1
                        logger.debug(f"L2缓存命中: {key}")

                        # 提升到L1缓存
                        ttl = self.cache_config.get(cache_type, self.default_ttl)
                        self.l1_cache.put(key, l2_value, ttl)

                        return l2_value
                else:
                    self._total_stats.l2_misses += 1
                    logger.warning("L2缓存未连接，跳过Redis查询")

            except Exception as e:
                logger.error(f"L2缓存查询失败 {key}: {e}")
                self._total_stats.l2_misses += 1

        self._total_stats.l1_misses += 1
        self._total_stats.l2_misses += 1
        logger.debug(f"缓存未命中: {key}")
        return None

    async def set(
        self,
        key: str,
        value: Any,
        cache_type: str = 'unified_data',
        ttl: Optional[timedelta] = None,
        use_l1: bool = True,
        use_l2: bool = True
    ) -> bool:
        """设置缓存值（同时存储到L1和L2）"""
        try:
            ttl = ttl or self.cache_config.get(cache_type, self.default_ttl)

            # 存储到L1缓存
            if use_l1:
                self.l1_cache.put(key, value, ttl)

            # 存储到L2缓存
            if use_l2 and self.l2_enabled:
                if await cache_service.is_connected():
                    await self._store_in_l2(key, value, cache_type, ttl)
                else:
                    logger.warning("L2缓存未连接，仅存储到L1")

            self._total_stats.sets += 1
            logger.debug(f"缓存设置成功: {key}")
            return True

        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
            return False

    async def delete(self, key: str, use_l1: bool = True, use_l2: bool = True) -> bool:
        """删除缓存键"""
        try:
            # 从L1删除
            l1_deleted = False
            if use_l1:
                l1_deleted = self.l1_cache.delete(key)

            # 从L2删除
            l2_deleted = False
            if use_l2 and self.l2_enabled:
                if await cache_service.is_connected():
                    l2_deleted = await cache_service.delete(key)

            logger.debug(f"缓存删除: {key}, L1={l1_deleted}, L2={l2_deleted}")
            return l1_deleted or l2_deleted

        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """按模式清除缓存"""
        deleted_count = 0

        # L1模式清除
        l1_keys = self.l1_cache.keys()
        for key in l1_keys:
            if pattern in key:
                if self.l1_cache.delete(key):
                    deleted_count += 1

        # L2模式清除
        if self.l2_enabled and await cache_service.is_connected():
            l2_deleted = await cache_service.delete_pattern(f"*{pattern}*")
            deleted_count += l2_deleted

        logger.info(f"模式清除完成: {pattern}, 删除了 {deleted_count} 个缓存项")
        return deleted_count

    async def cache_unified_data_point(
        self,
        symbol: str,
        source: str,
        timestamp: Union[str, datetime],
        data_point: Dict[str, Any]
    ) -> bool:
        """缓存统一数据点"""
        try:
            if isinstance(timestamp, datetime):
                timestamp_str = timestamp.isoformat()
            else:
                timestamp_str = timestamp

            key = f"unified_point:{source}:{symbol}:{timestamp_str}"

            # 添加缓存元数据
            data_point['_cached_at'] = datetime.now().isoformat()
            data_point['_cache_key'] = key

            return await self.set(key, data_point, f"{source}_data")

        except Exception as e:
            logger.error(f"缓存统一数据点失败: {e}")
            return False

    async def get_unified_data_point(
        self,
        symbol: str,
        source: str,
        timestamp: Union[str, datetime]
    ) -> Optional[Dict[str, Any]]:
        """获取统一数据点"""
        try:
            if isinstance(timestamp, datetime):
                timestamp_str = timestamp.isoformat()
            else:
                timestamp_str = timestamp

            key = f"unified_point:{source}:{symbol}:{timestamp_str}"
            return await self.get(key, f"{source}_data")

        except Exception as e:
            logger.error(f"获取统一数据点失败: {e}")
            return None

    async def cache_unified_series(
        self,
        symbol: str,
        source: str,
        data_series: List[Dict[str, Any]]
    ) -> bool:
        """缓存统一数据序列"""
        try:
            key = f"unified_series:{source}:{symbol}"

            # 按时间戳排序
            sorted_series = sorted(
                data_series,
                key=lambda x: x.get('timestamp', '')
            )

            return await self.set(key, sorted_series, f"{source}_data")

        except Exception as e:
            logger.error(f"缓存统一数据序列失败: {e}")
            return False

    async def get_unified_series(
        self,
        symbol: str,
        source: str
    ) -> Optional[List[Dict[str, Any]]]:
        """获取统一数据序列"""
        try:
            key = f"unified_series:{source}:{symbol}"
            return await self.get(key, f"{source}_data")

        except Exception as e:
            logger.error(f"获取统一数据序列失败: {e}")
            return None

    async def cache_quality_result(
        self,
        data_type: str,
        symbol: str,
        quality_result: Dict[str, Any]
    ) -> bool:
        """缓存数据质量结果"""
        try:
            key = f"quality:{data_type}:{symbol}"
            return await self.set(key, quality_result, 'quality_scores')

        except Exception as e:
            logger.error(f"缓存质量结果失败: {e}")
            return False

    async def get_quality_result(
        self,
        data_type: str,
        symbol: str
    ) -> Optional[Dict[str, Any]]:
        """获取数据质量结果"""
        try:
            key = f"quality:{data_type}:{symbol}"
            return await self.get(key, 'quality_scores')

        except Exception as e:
            logger.error(f"获取质量结果失败: {e}")
            return None

    async def cache_backtest_result(
        self,
        strategy_id: str,
        backtest_data: Dict[str, Any]
    ) -> bool:
        """缓存回测结果"""
        try:
            key = f"backtest:{strategy_id}"
            return await self.set(key, backtest_data, 'backtest_results')

        except Exception as e:
            logger.error(f"缓存回测结果失败: {e}")
            return False

    async def get_backtest_result(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """获取回测结果"""
        try:
            key = f"backtest:{strategy_id}"
            return await self.get(key, 'backtest_results')

        except Exception as e:
            logger.error(f"获取回测结果失败: {e}")
            return None

    async def warm_cache(self, warmup_data: Dict[str, Any]) -> int:
        """缓存预热"""
        warmed_count = 0

        try:
            for cache_type, data_items in warmup_data.items():
                for key, value in data_items.items():
                    if await self.set(key, value, cache_type):
                        warmed_count += 1

            logger.info(f"缓存预热完成: 预热了 {warmed_count} 个缓存项")
            return warmed_count

        except Exception as e:
            logger.error(f"缓存预热失败: {e}")
            return warmed_count

    async def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        try:
            l1_info = {
                'size': self.l1_cache.size(),
                'max_size': self.l1_cache.max_size,
                'stats': self.l1_cache.get_stats().__dict__
            }

            l2_info = {}
            if self.l2_enabled:
                l2_info = await cache_service.get_cache_info()

            total_stats = {
                'l1_hits': self._total_stats.l1_hits,
                'l1_misses': self._total_stats.l1_misses,
                'l2_hits': self._total_stats.l2_hits,
                'l2_misses': self._total_stats.l2_misses,
                'total_hits': self._total_stats.l1_hits + self._total_stats.l2_hits,
                'total_requests': self._total_stats.gets,
                'hit_rate': self._total_stats.hit_rate,
                'l1_hit_rate': self._total_stats.l1_hit_rate,
                'l2_hit_rate': self._total_stats.l2_hit_rate,
                'evictions': self._total_stats.evictions,
                'sets': self._total_stats.sets
            }

            return {
                'l1_cache': l1_info,
                'l2_cache': l2_info,
                'total_stats': total_stats,
                'config': {
                    'cleanup_interval': self.cleanup_interval,
                    'default_ttl': self.default_ttl.total_seconds(),
                    'cache_config': {
                        k: v.total_seconds() for k, v in self.cache_config.items()
                    }
                }
            }

        except Exception as e:
            logger.error(f"获取缓存信息失败: {e}")
            return {'error': str(e)}

    async def cleanup_expired(self) -> int:
        """清理过期缓存"""
        try:
            l1_cleaned = self.l1_cache.cleanup_expired()

            l2_cleaned = 0
            if self.l2_enabled and await cache_service.is_connected():
                l2_cleaned = await cache_service.cleanup_expired_cache()

            total_cleaned = l1_cleaned + l2_cleaned
            logger.debug(f"清理过期缓存: L1={l1_cleaned}, L2={l2_cleaned}")
            return total_cleaned

        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")
            return 0

    def _start_cleanup_task(self):
        """启动清理任务"""
        if self.cleanup_interval > 0:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        """清理循环"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理任务异常: {e}")

    async def _get_from_l2(self, key: str, cache_type: str) -> Optional[Any]:
        """从L2缓存获取数据"""
        try:
            # 使用pickle序列化保持数据类型
            return await cache_service.get(key, use_pickle=True)
        except Exception as e:
            logger.error(f"L2缓存获取失败 {key}: {e}")
            return None

    async def _store_in_l2(
        self,
        key: str,
        value: Any,
        cache_type: str,
        ttl: timedelta
    ) -> None:
        """存储数据到L2缓存"""
        try:
            expire_seconds = int(ttl.total_seconds())
            # 使用pickle序列化保持数据类型
            await cache_service.set(key, value, expire=expire_seconds, use_pickle=True)
        except Exception as e:
            logger.error(f"L2缓存存储失败 {key}: {e}")

    async def close(self):
        """关闭缓存管理器"""
        try:
            # 取消清理任务
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass

            # 清空L1缓存
            self.l1_cache.clear()

            logger.info("统一缓存管理器已关闭")

        except Exception as e:
            logger.error(f"关闭缓存管理器失败: {e}")

# 创建全局统一缓存管理器实例
unified_cache_manager = UnifiedCacheManager()

# 导出主要类和实例
__all__ = [
    'UnifiedCacheManager',
    'unified_cache_manager',
    'CacheEntry',
    'CacheStats',
    'LRUICache'
]
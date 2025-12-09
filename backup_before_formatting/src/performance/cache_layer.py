"""
多层缓存系统

提供完整的缓存解决方案，包括：
- LRU缓存（最近最少使用）
- TTL缓存（超时时间）
- 多级缓存
- 分布式缓存支持
- 缓存预热和预取
- 智能失效策略
"""

import hashlib
import json
import logging
import pickle
import threading
import time
import weakref
import zlib
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    value: Any
    timestamp: float
    last_access: float
    access_count: int = 0
    ttl: Optional[float] = None
    compressed: bool = False

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl

    def access(self):
        """记录访问"""
        self.last_access = time.time()
        self.access_count += 1


class LRUCache(Generic[K, V]):
    """
    LRU（最近最少使用）缓存实现

    特点：
    - 固定大小限制
    - 自动淘汰最少使用的条目
    - 线程安全
    - O(1) 访问和更新
    """

    def __init__(
        self, maxsize: int = 128, on_evict: Optional[Callable[[K, V], None]] = None
    ):
        self.maxsize = maxsize
        self.on_evict = on_evict
        self._cache: OrderedDict[K, V] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """
        获取缓存值

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        with self._lock:
            if key in self._cache:
                # 移动到末尾（表示最近使用）
                value = self._cache.pop(key)
                self._cache[key] = value
                self._hits += 1
                return value
            else:
                self._misses += 1
                return default

    def put(self, key: K, value: V) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值

        Returns:
            True表示新插入，False表示更新
        """
        with self._lock:
            is_update = key in self._cache

            # 如果已存在，先移除
            if key in self._cache:
                old_value = self._cache.pop(key)
                if self.on_evict and not is_update:
                    self.on_evict(key, old_value)

            # 如果已达到最大容量，删除最早的条目
            if len(self._cache) >= self.maxsize and not is_update:
                oldest_key, oldest_value = self._cache.popitem(last=False)
                if self.on_evict:
                    self.on_evict(oldest_key, oldest_value)

            # 添加新条目
            self._cache[key] = value
            return not is_update

    def remove(self, key: K) -> bool:
        """
        删除缓存项

        Args:
            key: 缓存键

        Returns:
            True表示删除成功
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": self.size(),
                "maxsize": self.maxsize,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / total if total > 0 else 0,
            }


class TTLCache(Generic[K, V]):
    """
    TTL（超时时间）缓存实现

    特点：
    - 支持自动过期
    - 惰性删除（访问时检查）
    - 线程安全
    - 可配置过期时间
    """

    def __init__(
        self,
        maxsize: int = 128,
        default_ttl: float = 3600,
        cleanup_interval: float = 60,
    ):
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        self._cache: Dict[K, CacheEntry] = {}
        self._lock = threading.RLock()
        self._last_cleanup = time.time()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def _cleanup_expired(self):
        """清理过期条目"""
        now = time.time()
        if now - self._last_cleanup < self.cleanup_interval:
            return

        with self._lock:
            expired_keys = [k for k, entry in self._cache.items() if entry.is_expired()]

            for key in expired_keys:
                del self._cache[key]
                self._evictions += 1

            self._last_cleanup = now
            if expired_keys:
                logger.debug(f"清理了 {len(expired_keys)} 个过期缓存项")

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """
        获取缓存值

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        with self._lock:
            self._cleanup_expired()

            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired():
                    entry.access()
                    self._hits += 1
                    return entry.value
                else:
                    del self._cache[key]
                    self._evictions += 1

            self._misses += 1
            return default

    def put(self, key: K, value: V, ttl: Optional[float] = None) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）

        Returns:
            True表示成功
        """
        with self._lock:
            self._cleanup_expired()

            if len(self._cache) >= self.maxsize and key not in self._cache:
                # 删除最旧的条目
                oldest_key = min(
                    self._cache.keys(), key=lambda k: self._cache[k].last_access
                )
                del self._cache[oldest_key]
                self._evictions += 1

            self._cache[key] = CacheEntry(
                key=str(key),
                value=value,
                timestamp=time.time(),
                last_access=time.time(),
                ttl=ttl if ttl is not None else self.default_ttl,
            )
            return True

    def remove(self, key: K) -> bool:
        """删除缓存项"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            self._cleanup_expired()
            return len(self._cache)

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            self._cleanup_expired()
            total = self._hits + self._misses
            return {
                "size": self.size(),
                "maxsize": self.maxsize,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate": self._hits / total if total > 0 else 0,
            }


class MultiLevelCache(Generic[K, V]):
    """
    多级缓存系统

    结构：
    - L1: 内存LRU缓存（小容量，访问最快）
    - L2: 内存TTL缓存（中等容量，支持过期）
    - L3: 持久化缓存（大容量，支持持久化）

    特点：
    - 智能数据分布
    - 自动数据迁移
    - 命中率优化
    """

    def __init__(
        self,
        l1_size: int = 64,  # L1缓存大小
        l2_size: int = 512,  # L2缓存大小
        l2_ttl: float = 3600,  # L2缓存过期时间
        compression_threshold: int = 1024,  # 压缩阈值
        enable_persistence: bool = False,  # 是否启用持久化
        persist_file: Optional[str] = None,
    ):
        self.l1 = LRUCache[K, V](maxsize=l1_size)
        self.l2 = TTLCache[K, V](maxsize=l2_size, default_ttl=l2_ttl)
        self.compression_threshold = compression_threshold
        self.enable_persistence = enable_persistence
        self.persist_file = persist_file

        # 统计信息
        self._l1_hits = 0
        self._l2_hits = 0
        self._l3_hits = 0
        self._misses = 0
        self._promotions = 0  # L2 -> L1 提升次数
        self._demotions = 0  # L1 -> L2 降级次数

        # 加载持久化数据
        if self.enable_persistence and self.persist_file:
            self._load_from_disk()

    def _compress(self, data: Any) -> bytes:
        """压缩数据"""
        serialized = pickle.dumps(data)
        if len(serialized) < self.compression_threshold:
            return serialized
        return zlib.compress(serialized)

    def _decompress(self, data: bytes) -> Any:
        """解压缩数据"""
        try:
            # 尝试解压
            decompressed = zlib.decompress(data)
            return pickle.loads(decompressed)
        except zlib.error:
            # 如果解压失败，说明数据未压缩
            return pickle.loads(data)

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """
        获取缓存值（多级查询）

        查询顺序: L1 -> L2 -> L3
        """
        # 查询L1
        value = self.l1.get(key)
        if value is not None:
            self._l1_hits += 1
            return value

        # 查询L2
        value = self.l2.get(key)
        if value is not None:
            self._l2_hits += 1
            # 提升到L1
            self.l1.put(key, value)
            self._promotions += 1
            return value

        # 查询L3（持久化）
        if self.enable_persistence and self.persist_file:
            try:
                # 从文件加载数据
                with open(self.persist_file, "r") as f:
                    data = json.load(f)
                    if key in data:
                        value = self._decompress(data[key].encode("latin1"))
                        self._l3_hits += 1
                        # 提升到L2
                        self.l2.put(key, value)
                        return value
            except Exception as e:
                logger.warning(f"从持久化缓存加载失败: {e}")

        self._misses += 1
        return default

    def put(self, key: K, value: V) -> bool:
        """
        设置缓存值

        存储策略：
        1. 首先存储到L1
        2. L1满时，将最少使用的项降级到L2
        3. L2满时，将最旧的项持久化到L3
        """
        # 存储到L1
        self.l1.put(key, value)

        # 如果需要持久化
        if self.enable_persistence and self.persist_file:
            self._persist_to_disk(key, value)

        return True

    def _persist_to_disk(self, key: K, value: V):
        """持久化到磁盘"""
        try:
            # 读取现有数据
            data = {}
            if Path(self.persist_file).exists():
                with open(self.persist_file, "r") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = {}

            # 压缩并保存
            compressed = self._compress(value)
            data[key] = compressed.decode("latin1", errors="ignore")

            # 写入文件
            with open(self.persist_file, "w") as f:
                json.dump(data, f)

        except Exception as e:
            logger.warning(f"持久化缓存失败: {e}")

    def _load_from_disk(self):
        """从磁盘加载缓存"""
        if not self.persist_file or not Path(self.persist_file).exists():
            return

        try:
            with open(self.persist_file, "r") as f:
                data = json.load(f)

            # 预加载到L2（使用合理的默认TTL）
            loaded_count = 0
            for key, value in data.items():
                if loaded_count < self.l2.maxsize:
                    decompressed = self._decompress(value.encode("latin1"))
                    self.l2.put(key, decompressed)
                    loaded_count += 1

            logger.info(f"从持久化缓存加载了 {loaded_count} 个条目")

        except Exception as e:
            logger.warning(f"从持久化缓存加载失败: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取多级缓存统计信息"""
        l1_stats = self.l1.get_stats()
        l2_stats = self.l2.get_stats()

        total_hits = self._l1_hits + self._l2_hits + self._l3_hits
        total_requests = total_hits + self._misses

        return {
            "l1": {
                "size": l1_stats["size"],
                "maxsize": l1_stats["maxsize"],
                "hits": self._l1_hits,
                "hit_rate": self._l1_hits / total_requests if total_requests > 0 else 0,
            },
            "l2": {
                "size": l2_stats["size"],
                "maxsize": l2_stats["maxsize"],
                "hits": self._l2_hits,
                "evictions": l2_stats["evictions"],
                "hit_rate": self._l2_hits / total_requests if total_requests > 0 else 0,
            },
            "l3": {
                "hits": self._l3_hits,
                "hit_rate": self._l3_hits / total_requests if total_requests > 0 else 0,
            },
            "overall": {
                "total_hits": total_hits,
                "total_misses": self._misses,
                "overall_hit_rate": (
                    total_hits / total_requests if total_requests > 0 else 0
                ),
                "promotions": self._promotions,
                "demotions": self._demotions,
            },
        }

    def clear(self):
        """清空所有级别缓存"""
        self.l1.clear()
        self.l2.clear()
        if self.enable_persistence and self.persist_file:
            try:
                Path(self.persist_file).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"删除持久化文件失败: {e}")


class CacheManager:
    """
    缓存管理器

    统一管理多个缓存实例，支持：
    - 缓存分区
    - 自动预热
    - 缓存统计
    - 分布式缓存协调
    """

    def __init__(self):
        self._caches: Dict[str, MultiLevelCache] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.RLock()

    def create_cache(self, name: str, cache_config: Dict[str, Any]) -> MultiLevelCache:
        """
        创建新的缓存实例

        Args:
            name: 缓存名称
            cache_config: 缓存配置

        Returns:
            缓存实例
        """
        with self._lock:
            if name in self._caches:
                logger.warning(f"缓存 {name} 已存在，将覆盖")
            else:
                logger.info(f"创建缓存: {name}")

            self._caches[name] = MultiLevelCache(**cache_config)
            return self._caches[name]

    def get_cache(self, name: str) -> Optional[MultiLevelCache]:
        """获取缓存实例"""
        return self._caches.get(name)

    def preload_cache(
        self,
        cache_name: str,
        key_value_pairs: Iterable[Tuple[K, V]],
        async_mode: bool = True,
    ):
        """
        预加载缓存

        Args:
            cache_name: 缓存名称
            key_value_pairs: 键值对列表
            async_mode: 是否异步预加载
        """
        cache = self.get_cache(cache_name)
        if not cache:
            raise ValueError(f"缓存 {cache_name} 不存在")

        def _preload():
            for key, value in key_value_pairs:
                cache.put(key, value)

        if async_mode:
            self._executor.submit(_preload)
            logger.info(f"开始异步预加载缓存: {cache_name}")
        else:
            _preload()
            logger.info(f"完成同步预加载缓存: {cache_name}")

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有缓存的统计信息"""
        return {name: cache.get_stats() for name, cache in self._caches.items()}

    def clear_all(self):
        """清空所有缓存"""
        for name, cache in self._caches.items():
            cache.clear()
            logger.info(f"已清空缓存: {name}")


# 缓存装饰器
def cached(
    cache_instance: Union[MultiLevelCache, CacheManager],
    key_func: Optional[Callable] = None,
    cache_name: Optional[str] = None,
):
    """
    缓存装饰器

    Args:
        cache_instance: 缓存实例或管理器
        key_func: 自定义键生成函数
        cache_name: 缓存名称（用于缓存管理器）

    Usage:
        @cached(my_cache)
        def expensive_function(x, y):
            return x * y

        # 或使用缓存管理器
        cache_manager = CacheManager()
        cache_manager.create_cache("my_cache", {...})

        @cached(cache_manager, cache_name="my_cache")
        def another_function(a, b):
            return a + b
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认键生成：函数名 + 参数哈希
                key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
                cache_key = hashlib.sha256(key_data.encode()).hexdigest()

            # 获取缓存实例
            cache = cache_instance
            if isinstance(cache_instance, CacheManager):
                if not cache_name:
                    raise ValueError("使用CacheManager时必须指定cache_name")
                cache = cache_instance.get_cache(cache_name)
                if not cache:
                    raise ValueError(f"缓存 {cache_name} 不存在")

            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.put(cache_key, result)
            return result

        return wrapper

    return decorator


# 全局缓存管理器实例
_default_cache_manager = CacheManager()


def get_default_cache(
    name: str = "default", config: Optional[Dict] = None
) -> MultiLevelCache:
    """
    获取默认缓存实例

    Args:
        name: 缓存名称
        config: 缓存配置

    Returns:
        缓存实例
    """
    global _default_cache_manager

    cache = _default_cache_manager.get_cache(name)
    if cache is None:
        default_config = {
            "l1_size": 64,
            "l2_size": 512,
            "l2_ttl": 3600,
            "enable_persistence": False,
        }
        if config:
            default_config.update(config)
        cache = _default_cache_manager.create_cache(name, default_config)

    return cache


def cache_result(ttl: Optional[float] = 3600, maxsize: int = 128):
    """
    简单缓存装饰器（使用默认缓存）

    Args:
        ttl: 过期时间
        maxsize: 最大容量

    Usage:
        @cache_result(ttl=3600)
        def my_function(x):
            return x * 2
    """

    def decorator(func: Callable):
        cache = TTLCache(maxsize=maxsize, default_ttl=ttl)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成键
            key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            key = hashlib.sha256(key_data.encode()).hexdigest()

            # 尝试获取缓存
            result = cache.get(key)
            if result is not None:
                return result

            # 执行并缓存
            result = func(*args, **kwargs)
            cache.put(key, result)
            return result

        return wrapper

    return decorator

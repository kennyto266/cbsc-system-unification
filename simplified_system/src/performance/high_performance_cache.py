#!/usr / bin / env python3
"""
高性能缓存系统
High - performance cache system with multi - layer caching strategy
"""

import hashlib
import logging
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class LRUCache:
    """线程安全的LRU缓存实现"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            if key in self.cache:
                # 移到末尾（最近使用）
                value = self.cache.pop(key)
                self.cache[key] = value
                self.hits += 1
                return value
            self.misses += 1
            return None

    def put(self, key: str, value: Any) -> None:
        """存储缓存值"""
        with self.lock:
            if key in self.cache:
                # 更新现有值
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                # 删除最久未使用的值
                self.cache.popitem(last = False)
            self.cache[key] = value

    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
            }


class HighPerformanceCache:
    """
    高性能多层缓存系统

    特性:
    - 内存缓存 (LRU)
    - 指纹缓存 (避免重复计算)
    - 时间窗口缓存
    - 线程安全
    - 自动清理过期缓存
    """

    def __init__(self):
        # L1缓存: 内存缓存 (最热数据)
        self.l1_cache = LRUCache(max_size = 500)

        # L2缓存: 计算结果缓存 (中等热度数据)
        self.l2_cache = LRUCache(max_size = 2000)

        # L3缓存: 指纹缓存 (避免重复计算)
        self.fingerprints = LRUCache(max_size = 10000)

        # 时间窗口缓存
        self.time_window_cache = {}
        self.time_window_ttl = 300  # 5分钟

        # 缓存统计
        self.stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "fingerprint_hits": 0,
            "time_window_hits": 0,
            "total_requests": 0,
            "cache_misses": 0,
        }

        # 启动后台清理线程
        self.cleanup_thread = threading.Thread(
            target = self._cleanup_expired_cache, daemon = True
        )
        self.cleanup_thread.start()

        logger.info("High - performance cache system initialized")

    def generate_cache_key(
        self, data: pd.DataFrame, operation: str, params: Dict[str, Any]
    ) -> str:
        """生成缓存键"""
        try:
            # 使用数据指纹 + 操作 + 参数生成唯一键
            data_fingerprint = self._generate_data_fingerprint(data)
            params_str = str(sorted(params.items()))
            combined = f"{data_fingerprint}_{operation}_{params_str}"

            # 使用SHA256生成固定长度的键
            return hashlib.sha256(combined.encode()).hexdigest()[:32]

        except Exception as e:
            logger.warning(f"Failed to generate cache key: {e}")
            # 回退到简单键
            return f"{operation}_{len(data)}_{hash(str(params))}"

    def _generate_data_fingerprint(self, data: pd.DataFrame) -> str:
        """生成数据指纹"""
        try:
            # 使用数据的统计特征生成指纹
            if isinstance(data, pd.DataFrame):
                if len(data) == 0:
                    return "empty_df"

                # 选择关键特征
                features = [
                    len(data),
                    len(data.columns),
                    data.index[0] if len(data) > 0 else None,
                    data.index[-1] if len(data) > 0 else None,
                    (
                        data.iloc[0, 0]
                        if len(data) > 0 and len(data.columns) > 0
                        else None
                    ),
                    (
                        data.iloc[-1, 0]
                        if len(data) > 0 and len(data.columns) > 0
                        else None
                    ),
                    (
                        data.iloc[:, 0].mean()
                        if len(data) > 0 and len(data.columns) > 0
                        else None
                    ),
                    (
                        data.iloc[:, 0].std()
                        if len(data) > 0 and len(data.columns) > 0
                        else None
                    ),
                ]
                return hashlib.md5(str(features).encode()).hexdigest()[:16]
            else:
                return str(hash(str(data)))
        except Exception:
            return "unknown"

    def get(self, cache_key: str) -> Optional[Any]:
        """多层缓存获取"""
        self.stats["total_requests"] += 1

        # L1缓存检查
        result = self.l1_cache.get(cache_key)
        if result is not None:
            self.stats["l1_hits"] += 1
            return result

        # L2缓存检查
        result = self.l2_cache.get(cache_key)
        if result is not None:
            self.stats["l2_hits"] += 1
            # 提升到L1缓存
            self.l1_cache.put(cache_key, result)
            return result

        # 指纹缓存检查
        result = self.fingerprints.get(cache_key)
        if result is not None:
            self.stats["fingerprint_hits"] += 1
            return result

        # 时间窗口缓存检查
        result = self._get_time_window_cache(cache_key)
        if result is not None:
            self.stats["time_window_hits"] += 1
            return result

        self.stats["cache_misses"] += 1
        return None

    def put(
        self,
        cache_key: str,
        value: Any,
        cache_level: str = "auto",
        ttl: Optional[int] = None,
    ) -> None:
        """多层缓存存储"""
        try:
            # 根据数据大小和类型智能选择缓存层级
            if cache_level == "auto":
                cache_level = self._select_cache_level(value)

            if cache_level == "l1":
                self.l1_cache.put(cache_key, value)
            elif cache_level == "l2":
                self.l2_cache.put(cache_key, value)
            elif cache_level == "fingerprint":
                self.fingerprints.put(cache_key, value)

            # 如果指定了TTL，使用时间窗口缓存
            if ttl is not None:
                self._put_time_window_cache(cache_key, value, ttl)

        except Exception as e:
            logger.warning(f"Failed to cache data: {e}")

    def _select_cache_level(self, value: Any) -> str:
        """智能选择缓存层级"""
        try:
            # 根据数据大小和访问模式选择缓存层级
            if isinstance(value, (int, float, bool)):
                return "l1"  # 小数据放L1
            elif isinstance(value, (np.ndarray, pd.Series)):
                if value.size < 1000:
                    return "l1"
                else:
                    return "l2"
            elif isinstance(value, pd.DataFrame):
                if len(value) < 100:
                    return "l1"
                else:
                    return "l2"
            else:
                return "l2"
        except Exception:
            return "l2"

    def _get_time_window_cache(self, cache_key: str) -> Optional[Any]:
        """获取时间窗口缓存"""
        if cache_key in self.time_window_cache:
            entry = self.time_window_cache[cache_key]
            if time.time() - entry["timestamp"] < entry["ttl"]:
                return entry["value"]
            else:
                # 过期，删除
                del self.time_window_cache[cache_key]
        return None

    def _put_time_window_cache(self, cache_key: str, value: Any, ttl: int) -> None:
        """存储时间窗口缓存"""
        self.time_window_cache[cache_key] = {
            "value": value,
            "timestamp": time.time(),
            "ttl": ttl,
        }

    def _cleanup_expired_cache(self) -> None:
        """后台清理过期缓存"""
        while True:
            try:
                current_time = time.time()
                expired_keys = [
                    key
                    for key, entry in self.time_window_cache.items()
                    if current_time - entry["timestamp"] >= entry["ttl"]
                ]

                for key in expired_keys:
                    del self.time_window_cache[key]

                if expired_keys:
                    logger.debug(
                        f"Cleaned up {len(expired_keys)} expired cache entries"
                    )

                # 每30秒清理一次
                time.sleep(30)

            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
                time.sleep(30)

    def clear_all(self) -> None:
        """清空所有缓存"""
        self.l1_cache.clear()
        self.l2_cache.clear()
        self.fingerprints.clear()
        self.time_window_cache.clear()

        # 重置统计
        self.stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "fingerprint_hits": 0,
            "time_window_hits": 0,
            "total_requests": 0,
            "cache_misses": 0,
        }

        logger.info("All caches cleared")

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """获取综合缓存统计"""
        total_requests = self.stats["total_requests"]
        if total_requests == 0:
            hit_rate = 0
        else:
            total_hits = (
                self.stats["l1_hits"]
                + self.stats["l2_hits"]
                + self.stats["fingerprint_hits"]
                + self.stats["time_window_hits"]
            )
            hit_rate = total_hits / total_requests

        return {
            "overall_stats": {
                "total_requests": total_requests,
                "hit_rate": hit_rate,
                "cache_misses": self.stats["cache_misses"],
            },
            "layer_stats": {
                "l1_cache": self.l1_cache.get_stats(),
                "l2_cache": self.l2_cache.get_stats(),
                "fingerprint_cache": self.fingerprints.get_stats(),
                "time_window_cache": {"size": len(self.time_window_cache)},
            },
            "hit_distribution": {
                "l1_hits": self.stats["l1_hits"],
                "l2_hits": self.stats["l2_hits"],
                "fingerprint_hits": self.stats["fingerprint_hits"],
                "time_window_hits": self.stats["time_window_hits"],
            },
        }


# 全局缓存实例
global_cache = HighPerformanceCache()


def cached_operation(operation_name: str, ttl: Optional[int] = None):
    """缓存装饰器"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # 提取数据和参数
                data = args[0] if args else None
                params = kwargs

                # 生成缓存键
                if data is not None:
                    cache_key = global_cache.generate_cache_key(
                        data, operation_name, params
                    )
                else:
                    cache_key = f"{operation_name}_{hash(str(params))}"

                # 尝试从缓存获取
                cached_result = global_cache.get(cache_key)
                if cached_result is not None:
                    return cached_result

                # 执行函数
                result = func(*args, **kwargs)

                # 存储到缓存
                global_cache.put(cache_key, result, ttl = ttl)

                return result

            except Exception as e:
                logger.error(f"Error in cached operation {operation_name}: {e}")
                # 缓存失败时直接执行函数
                return func(*args, **kwargs)

        return wrapper

    return decorator


# 便利函数
def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计"""
    return global_cache.get_comprehensive_stats()


def clear_cache() -> None:
    """清空缓存"""
    global_cache.clear_all()

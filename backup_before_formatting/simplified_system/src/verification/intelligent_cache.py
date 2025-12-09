#!/usr/bin/env python3
"""
Phase 5: System Integration and Optimization
智能緩存系統 - Intelligent Cache System

提供多層級、智能TTL管理的高性能緩存系統。
支持：
- 自動TTL管理基於數據訪問模式
- 分層緩存架構
- 內存壓力感知清理
- 緩存預熱和預取
- 分布式緩存支持
"""

import asyncio
import time
import threading
import logging
import hashlib
import json
import pickle
import gzip
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict, deque
from pathlib import Path
import weakref
import psutil
import redis
from enum import Enum

# Setup logging
logger = logging.getLogger(__name__)

class CachePolicy(Enum):
    """緩存策略枚舉"""
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"
    ADAPTIVE = "adaptive"

class CacheLevel(Enum):
    """緩存級別枚舉"""
    MEMORY = "memory"
    DISK = "disk"
    DISTRIBUTED = "distributed"

@dataclass
class CacheEntry:
    """緩存條目數據結構"""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[float] = None
    size_bytes: int = 0
    compression_ratio: float = 1.0
    hit_count: int = 0
    miss_count: int = 0
    priority: int = 0  # 優先級，0=最低，9=最高
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """檢查是否過期"""
        if self.ttl is None:
            return False
        return time.time() > (self.created_at + self.ttl)

    def update_access(self):
        """更新訪問信息"""
        self.last_accessed = time.time()
        self.access_count += 1
        self.hit_count += 1

    def get_age_seconds(self) -> float:
        """獲取緩存年齡（秒）"""
        return time.time() - self.created_at

    def get_idle_seconds(self) -> float:
        """獲取空閒時間（秒）"""
        return time.time() - self.last_accessed

class AdaptiveTTLManager:
    """自適應TTL管理器"""

    def __init__(self):
        self.access_patterns = {}  # 訪問模式記錄
        self.hit_ratios = defaultdict(lambda: {'hits': 0, 'misses': 0})
        self.ttl_adjustments = {}
        self.base_ttls = {
            'source_auth': 300,      # 5分鐘
            'content_validation': 600,  # 10分鐘
            'behavioral_analysis': 1800,  # 30分鐘
            'composite': 900,        # 15分鐘
            'government_data': 1800,  # 30分鐘
            'stock_data': 300,       # 5分鐘
            'verification_result': 600  # 10分鐘
        }
        self.adjustment_factors = {
            'high_frequency': 2.0,   # 高頻訪問延長TTL
            'low_frequency': 0.5,    # 低頻訪問縮短TTL
            'volatile': 0.3,         # 易變數據縮短TTL
            'stable': 1.5            # 穩定數據延長TTL
        }

    def calculate_adaptive_ttl(self, key: str, data_type: str, access_history: List[float]) -> float:
        """計算自適應TTL"""
        base_ttl = self.base_ttls.get(data_type, 600)

        if len(access_history) < 3:
            return base_ttl

        # 分析訪問模式
        current_time = time.time()
        recent_accesses = [t for t in access_history if current_time - t < 3600]  # 最近1小時

        if len(recent_accesses) == 0:
            frequency_factor = self.adjustment_factors['low_frequency']
        elif len(recent_accesses) > 10:
            frequency_factor = self.adjustment_factors['high_frequency']
        else:
            frequency_factor = 1.0

        # 分析訪問間隔一致性
        if len(recent_accesses) > 2:
            intervals = [recent_accesses[i] - recent_accesses[i-1]
                        for i in range(1, len(recent_accesses))]
            interval_variance = sum((x - sum(intervals)/len(intervals))**2 for x in intervals) / len(intervals)

            if interval_variance < 60:  # 規律訪問
                stability_factor = self.adjustment_factors['stable']
            else:  # 不規律訪問
                stability_factor = self.adjustment_factors['volatile']
        else:
            stability_factor = 1.0

        # 計算最終TTL
        adaptive_ttl = base_ttl * frequency_factor * stability_factor

        # 限制TTL範圍
        min_ttl = base_ttl * 0.1
        max_ttl = base_ttl * 5.0
        adaptive_ttl = max(min_ttl, min(max_ttl, adaptive_ttl))

        # 記錄調整信息
        self.ttl_adjustments[key] = {
            'base_ttl': base_ttl,
            'adaptive_ttl': adaptive_ttl,
            'frequency_factor': frequency_factor,
            'stability_factor': stability_factor,
            'calculated_at': current_time
        }

        return adaptive_ttl

    def record_access(self, key: str, data_type: str, is_hit: bool):
        """記錄訪問"""
        if key not in self.access_patterns:
            self.access_patterns[key] = {
                'data_type': data_type,
                'access_times': [],
                'hits': 0,
                'misses': 0
            }

        pattern = self.access_patterns[key]
        pattern['access_times'].append(time.time())
        pattern['access_times'] = pattern['access_times'][-100:]  # 保留最近100次訪問

        if is_hit:
            pattern['hits'] += 1
            self.hit_ratios[data_type]['hits'] += 1
        else:
            pattern['misses'] += 1
            self.hit_ratios[data_type]['misses'] += 1

    def get_hit_ratio(self, data_type: str) -> float:
        """獲取命中率"""
        ratio = self.hit_ratios[data_type]
        total = ratio['hits'] + ratio['misses']
        return ratio['hits'] / total if total > 0 else 0.0

    def cleanup_old_records(self, max_age_hours: int = 24):
        """清理舊記錄"""
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)

        # 清理訪問模式記錄
        keys_to_remove = []
        for key, pattern in self.access_patterns.items():
            # 檢查最近訪問時間
            if pattern['access_times'] and pattern['access_times'][-1] < cutoff_time:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.access_patterns[key]
            if key in self.ttl_adjustments:
                del self.ttl_adjustments[key]

        logger.info(f"Cleaned up {len(keys_to_remove)} old access pattern records")

class MemoryPressureMonitor:
    """內存壓力監控器"""

    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.memory_thresholds = {
            'warning': 0.8,   # 80%
            'critical': 0.9,  # 90%
            'emergency': 0.95 # 95%
        }
        self.current_pressure = 0.0
        self.is_monitoring = False
        self.monitor_thread = None
        self.pressure_callbacks = []

    def get_memory_usage(self) -> float:
        """獲取當前內存使用率"""
        try:
            memory = psutil.virtual_memory()
            return memory.percent / 100.0
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return 0.0

    def get_cache_memory_usage(self) -> Dict[str, Any]:
        """獲取緩存內存使用情況"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': process.memory_percent()
            }
        except Exception as e:
            logger.error(f"Error getting cache memory usage: {e}")
            return {}

    def start_monitoring(self):
        """開始監控"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Memory pressure monitoring started")

    def stop_monitoring(self):
        """停止監控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Memory pressure monitoring stopped")

    def _monitor_loop(self):
        """監控循環"""
        while self.is_monitoring:
            try:
                self.current_pressure = self.get_memory_usage()

                # 檢查是否觸發回調
                for callback in self.pressure_callbacks:
                    callback(self.current_pressure)

                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                time.sleep(self.check_interval)

    def add_pressure_callback(self, callback: Callable[[float], None]):
        """添加壓力回調"""
        self.pressure_callbacks.append(callback)

    def get_pressure_level(self) -> str:
        """獲取壓力等級"""
        if self.current_pressure >= self.memory_thresholds['emergency']:
            return 'emergency'
        elif self.current_pressure >= self.memory_thresholds['critical']:
            return 'critical'
        elif self.current_pressure >= self.memory_thresholds['warning']:
            return 'warning'
        else:
            return 'normal'

class IntelligentCache:
    """智能緩存系統"""

    def __init__(self,
                 max_memory_mb: int = 512,
                 max_entries: int = 10000,
                 enable_compression: bool = True,
                 enable_disk_cache: bool = True,
                 enable_redis: bool = False,
                 redis_config: Optional[Dict[str, Any]] = None):

        # 配置參數
        self.max_memory_mb = max_memory_mb
        self.max_entries = max_entries
        self.enable_compression = enable_compression
        self.enable_disk_cache = enable_disk_cache
        self.enable_redis = enable_redis

        # 內存緩存
        self.memory_cache = OrderedDict()
        self.cache_index = {}  # key -> position in memory_cache

        # 磁盤緩存配置
        self.disk_cache_dir = Path("cache/disk_cache")
        self.disk_cache_dir.mkdir(parents=True, exist_ok=True)

        # Redis緩存配置
        self.redis_client = None
        if enable_redis and redis_config:
            try:
                self.redis_client = redis.Redis(**redis_config)
                self.redis_client.ping()  # 測試連接
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.warning(f"Redis initialization failed: {e}")
                self.enable_redis = False

        # TTL管理器
        self.ttl_manager = AdaptiveTTLManager()

        # 內存壓力監控
        self.memory_monitor = MemoryPressureMonitor()
        self.memory_monitor.add_pressure_callback(self._handle_memory_pressure)
        self.memory_monitor.start_monitoring()

        # 統計信息
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'compressions': 0,
            'disk_writes': 0,
            'disk_reads': 0,
            'redis_operations': 0,
            'memory_cleanups': 0
        }

        # 清理線程
        self.cleanup_thread = None
        self.stop_cleanup = threading.Event()
        self._start_cleanup_thread()

        logger.info(f"Intelligent Cache initialized - Memory: {max_memory_mb}MB, Entries: {max_entries}")

    def _start_cleanup_thread(self):
        """啟動清理線程"""
        def cleanup_loop():
            while not self.stop_cleanup.wait(60):  # 每分鐘清理一次
                try:
                    self._cleanup_expired_entries()
                    self._cleanup_memory_pressure()
                    self.ttl_manager.cleanup_old_records()
                except Exception as e:
                    logger.error(f"Cache cleanup error: {e}")

        self.cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self.cleanup_thread.start()

    def _handle_memory_pressure(self, pressure_level: float):
        """處理內存壓力"""
        if pressure_level >= 0.9:  # Critical
            logger.warning(f"High memory pressure: {pressure_level:.1%}")
            self._emergency_cleanup()
        elif pressure_level >= 0.8:  # Warning
            logger.info(f"Moderate memory pressure: {pressure_level:.1%}")
            self._moderate_cleanup()

    def _emergency_cleanup(self):
        """緊急清理"""
        target_size = len(self.memory_cache) // 2
        evicted = self._evict_lru_entries(target_size)
        self.stats['memory_cleanups'] += 1
        logger.info(f"Emergency cleanup: evicted {evicted} entries")

    def _moderate_cleanup(self):
        """中等清理"""
        target_size = int(len(self.memory_cache) * 0.8)
        evicted = self._evict_lru_entries(len(self.memory_cache) - target_size)
        logger.info(f"Moderate cleanup: evicted {evicted} entries")

    def _cleanup_expired_entries(self):
        """清理過期條目"""
        expired_keys = []
        current_time = time.time()

        for key, entry in self.memory_cache.items():
            if entry.is_expired():
                expired_keys.append(key)

        for key in expired_keys:
            self._remove_entry(key)

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired entries")

    def _cleanup_memory_pressure(self):
        """基於內存壓力清理"""
        # 檢查條目數量限制
        if len(self.memory_cache) > self.max_entries:
            excess = len(self.memory_cache) - self.max_entries
            self._evict_lru_entries(excess)

        # 檢查內存大小限制
        current_memory = self._get_memory_usage()
        if current_memory > self.max_memory_mb:
            # 清理到80%容量
            target_memory = self.max_memory_mb * 0.8
            self._evict_by_memory(target_memory)

    def _get_memory_usage(self) -> float:
        """獲取當前內存使用量（MB）"""
        try:
            total_size = 0
            for entry in self.memory_cache.values():
                total_size += entry.size_bytes
            return total_size / 1024 / 1024
        except Exception as e:
            logger.error(f"Error calculating memory usage: {e}")
            return 0.0

    def _evict_lru_entries(self, count: int) -> int:
        """使用LRU策略驅逐條目"""
        evicted = 0
        keys_to_remove = []

        # LRU順序：OrderedDict保持插入順序，我們需要根據last_accessed重新排序
        sorted_entries = sorted(self.memory_cache.items(), key=lambda x: x[1].last_accessed)

        for key, entry in sorted_entries:
            if evicted >= count:
                break
            keys_to_remove.append(key)
            evicted += 1

        for key in keys_to_remove:
            self._remove_entry(key)

        self.stats['evictions'] += evicted
        return evicted

    def _evict_by_memory(self, target_memory_mb: float):
        """基於內存使用量驅逐條目"""
        current_memory = self._get_memory_usage()
        if current_memory <= target_memory_mb:
            return

        # 按優先級和最後訪問時間排序
        def sort_key(item):
            key, entry = item
            return (entry.priority, entry.last_accessed)

        sorted_entries = sorted(self.memory_cache.items(), key=sort_key)
        freed_memory = 0

        for key, entry in sorted_entries:
            if current_memory - freed_memory <= target_memory_mb:
                break

            freed_memory += entry.size_bytes / 1024 / 1024
            self._remove_entry(key)

        logger.info(f"Evicted by memory: freed {freed_memory:.2f}MB")

    def _remove_entry(self, key: str):
        """移除緩存條目"""
        if key in self.memory_cache:
            del self.memory_cache[key]

        if key in self.cache_index:
            del self.cache_index[key]

        # 從磁盤緩存中移除
        if self.enable_disk_cache:
            try:
                disk_file = self.disk_cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.cache"
                if disk_file.exists():
                    disk_file.unlink()
            except Exception as e:
                logger.debug(f"Error removing disk cache entry: {e}")

        # 從Redis中移除
        if self.enable_redis and self.redis_client:
            try:
                self.redis_client.delete(f"cache:{key}")
            except Exception as e:
                logger.debug(f"Error removing Redis entry: {e}")

    def _serialize_value(self, value: Any) -> bytes:
        """序列化值"""
        try:
            data = pickle.dumps(value)

            if self.enable_compression:
                compressed = gzip.compress(data)
                compression_ratio = len(compressed) / len(data)

                # 只有在壓縮有效時才使用壓縮
                if compression_ratio < 0.9:
                    self.stats['compressions'] += 1
                    return compressed, compression_ratio

            return data, 1.0

        except Exception as e:
            logger.error(f"Error serializing value: {e}")
            raise

    def _deserialize_value(self, data: bytes, compression_ratio: float) -> Any:
        """反序列化值"""
        try:
            if compression_ratio < 1.0:
                # 解壓縮
                data = gzip.decompress(data)

            return pickle.loads(data)

        except Exception as e:
            logger.error(f"Error deserializing value: {e}")
            raise

    def get(self, key: str, data_type: str = "default") -> Optional[Any]:
        """獲取緩存值"""
        start_time = time.time()

        # 記錄訪問
        is_hit = key in self.memory_cache
        self.ttl_manager.record_access(key, data_type, is_hit)

        # 內存緩存查找
        if is_hit:
            entry = self.memory_cache[key]

            # 檢查是否過期
            if entry.is_expired():
                self._remove_entry(key)
                self.stats['misses'] += 1
                return None

            # 更新訪問信息
            entry.update_access()

            # 移動到OrderedDict末尾（最近使用）
            self.memory_cache.move_to_end(key)

            self.stats['hits'] += 1
            logger.debug(f"Cache hit: {key} (memory)")
            return entry.value

        # 磁盤緩存查找
        if self.enable_disk_cache:
            try:
                disk_file = self.disk_cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.cache"
                if disk_file.exists():
                    with open(disk_file, 'rb') as f:
                        entry_data = pickle.load(f)

                    entry = CacheEntry(**entry_data)

                    # 檢查是否過期
                    if not entry.is_expired():
                        # 重新加載到內存緩存
                        self._add_to_memory(key, entry)
                        self.stats['disk_reads'] += 1
                        self.stats['hits'] += 1
                        logger.debug(f"Cache hit: {key} (disk)")
                        return entry.value
                    else:
                        # 過期，刪除
                        disk_file.unlink()

            except Exception as e:
                logger.debug(f"Error reading disk cache: {e}")

        # Redis緩存查找
        if self.enable_redis and self.redis_client:
            try:
                redis_key = f"cache:{key}"
                data = self.redis_client.get(redis_key)

                if data:
                    entry_data = pickle.loads(data)
                    entry = CacheEntry(**entry_data)

                    if not entry.is_expired():
                        # 重新加載到內存緩存
                        self._add_to_memory(key, entry)
                        self.stats['redis_operations'] += 1
                        self.stats['hits'] += 1
                        logger.debug(f"Cache hit: {key} (redis)")
                        return entry.value
                    else:
                        # 過期，刪除
                        self.redis_client.delete(redis_key)

            except Exception as e:
                logger.debug(f"Error reading Redis cache: {e}")

        # 緩存未命中
        self.stats['misses'] += 1
        logger.debug(f"Cache miss: {key}")
        return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None,
            data_type: str = "default", priority: int = 0, tags: List[str] = None):
        """設置緩存值"""
        try:
            # 計算自適應TTL
            if ttl is None:
                access_history = self.ttl_manager.access_patterns.get(key, {}).get('access_times', [])
                ttl = self.ttl_manager.calculate_adaptive_ttl(key, data_type, access_history)

            # 序列化值
            serialized_data, compression_ratio = self._serialize_value(value)

            # 創建緩存條目
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                last_accessed=time.time(),
                ttl=ttl,
                size_bytes=len(serialized_data),
                compression_ratio=compression_ratio,
                priority=priority,
                tags=tags or []
            )

            # 添加到內存緩存
            self._add_to_memory(key, entry)

            # 異步寫入磁盤緩存
            if self.enable_disk_cache:
                self._write_to_disk_async(key, entry)

            # 異步寫入Redis
            if self.enable_redis and self.redis_client:
                self._write_to_redis_async(key, entry)

            logger.debug(f"Cache set: {key} (TTL: {ttl}s, Size: {entry.size_bytes} bytes)")

        except Exception as e:
            logger.error(f"Error setting cache: {e}")

    def _add_to_memory(self, key: str, entry: CacheEntry):
        """添加到內存緩存"""
        # 檢查是否需要驅逐條目
        if len(self.memory_cache) >= self.max_entries:
            self._evict_lru_entries(1)

        # 添加到緩存
        self.memory_cache[key] = entry
        self.cache_index[key] = entry
        self.memory_cache.move_to_end(key)

    def _write_to_disk_async(self, key: str, entry: CacheEntry):
        """異步寫入磁盤"""
        def write_task():
            try:
                disk_file = self.disk_cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.cache"
                with open(disk_file, 'wb') as f:
                    pickle.dump(entry.__dict__, f)
                self.stats['disk_writes'] += 1
            except Exception as e:
                logger.debug(f"Error writing to disk cache: {e}")

        # 在線程池中執行
        threading.Thread(target=write_task, daemon=True).start()

    def _write_to_redis_async(self, key: str, entry: CacheEntry):
        """異步寫入Redis"""
        def write_task():
            try:
                redis_key = f"cache:{key}"
                data = pickle.dumps(entry.__dict__)

                if entry.ttl:
                    self.redis_client.setex(redis_key, int(entry.ttl), data)
                else:
                    self.redis_client.set(redis_key, data)

                self.stats['redis_operations'] += 1
            except Exception as e:
                logger.debug(f"Error writing to Redis: {e}")

        # 在線程池中執行
        threading.Thread(target=write_task, daemon=True).start()

    def delete(self, key: str):
        """刪除緩存條目"""
        self._remove_entry(key)
        logger.debug(f"Cache deleted: {key}")

    def clear(self, pattern: Optional[str] = None):
        """清理緩存"""
        if pattern:
            # 刪除匹配模式的條目
            import fnmatch
            keys_to_remove = [key for key in self.memory_cache.keys() if fnmatch.fnmatch(key, pattern)]
            for key in keys_to_remove:
                self._remove_entry(key)
            logger.info(f"Cleared {len(keys_to_remove)} entries matching pattern: {pattern}")
        else:
            # 清空所有緩存
            count = len(self.memory_cache)
            self.memory_cache.clear()
            self.cache_index.clear()

            # 清空磁盤緩存
            if self.enable_disk_cache:
                try:
                    for file in self.disk_cache_dir.glob("*.cache"):
                        file.unlink()
                except Exception as e:
                    logger.debug(f"Error clearing disk cache: {e}")

            # 清空Redis
            if self.enable_redis and self.redis_client:
                try:
                    keys = self.redis_client.keys("cache:*")
                    if keys:
                        self.redis_client.delete(*keys)
                except Exception as e:
                    logger.debug(f"Error clearing Redis: {e}")

            logger.info(f"Cleared all cache entries ({count} total)")

    def get_stats(self) -> Dict[str, Any]:
        """獲取緩存統計信息"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0

        return {
            'entries_count': len(self.memory_cache),
            'memory_usage_mb': self._get_memory_usage(),
            'hit_rate': hit_rate,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'evictions': self.stats['evictions'],
            'compressions': self.stats['compressions'],
            'disk_writes': self.stats['disk_writes'],
            'disk_reads': self.stats['disk_reads'],
            'redis_operations': self.stats['redis_operations'],
            'memory_cleanups': self.stats['memory_cleanups'],
            'memory_pressure': self.memory_monitor.current_pressure,
            'memory_pressure_level': self.memory_monitor.get_pressure_level(),
            'cache_memory_info': self.memory_monitor.get_cache_memory_usage()
        }

    def get_ttl_stats(self) -> Dict[str, Any]:
        """獲取TTL統計信息"""
        return {
            'access_patterns_count': len(self.ttl_manager.access_patterns),
            'ttl_adjustments_count': len(self.ttl_manager.ttl_adjustments),
            'hit_ratios': {k: self.ttl_manager.get_hit_ratio(v)
                          for k, v in self.ttl_manager.hit_ratios.items()
                          if v['hits'] + v['misses'] > 0}
        }

    def warmup(self, data_loader: Callable[[str], Any], keys: List[str],
               data_type: str = "default", ttl: Optional[float] = None):
        """緩存預熱"""
        logger.info(f"Starting cache warmup for {len(keys)} keys")

        loaded_count = 0
        for key in keys:
            try:
                if key not in self.memory_cache:
                    value = data_loader(key)
                    if value is not None:
                        self.set(key, value, ttl, data_type)
                        loaded_count += 1
            except Exception as e:
                logger.warning(f"Error during warmup for key {key}: {e}")

        logger.info(f"Cache warmup completed: {loaded_count}/{len(keys)} keys loaded")

    def shutdown(self):
        """關閉緩存系統"""
        logger.info("Shutting down Intelligent Cache...")

        # 停止清理線程
        self.stop_cleanup.set()
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)

        # 停止內存監控
        self.memory_monitor.stop_monitoring()

        # 關閉Redis連接
        if self.redis_client:
            self.redis_client.close()

        logger.info("Intelligent Cache shutdown completed")

# 全局緩存實例
intelligent_cache = IntelligentCache(
    max_memory_mb=512,
    max_entries=10000,
    enable_compression=True,
    enable_disk_cache=True,
    enable_redis=False  # 可以在配置中啟用
)

# 便捷函數
def get_cached(key: str, data_type: str = "default") -> Optional[Any]:
    """獲取緩存值"""
    return intelligent_cache.get(key, data_type)

def set_cached(key: str, value: Any, ttl: Optional[float] = None,
               data_type: str = "default", priority: int = 0, tags: List[str] = None):
    """設置緩存值"""
    intelligent_cache.set(key, value, ttl, data_type, priority, tags)

def delete_cached(key: str):
    """刪除緩存值"""
    intelligent_cache.delete(key)

def clear_cached(pattern: Optional[str] = None):
    """清理緩存"""
    intelligent_cache.clear(pattern)

def get_cache_stats() -> Dict[str, Any]:
    """獲取緩存統計"""
    stats = intelligent_cache.get_stats()
    ttl_stats = intelligent_cache.get_ttl_stats()
    return {**stats, **ttl_stats}

if __name__ == "__main__":
    def test_intelligent_cache():
        """測試智能緩存系統"""
        print("Testing Intelligent Cache System...")

        # 測試基本操作
        print("\n1. Testing basic operations...")
        set_cached("test_key1", "test_value1", ttl=60, data_type="test")
        set_cached("test_key2", {"nested": "data"}, ttl=120, data_type="test")
        set_cached("test_key3", [1, 2, 3, 4, 5], ttl=180, data_type="list")

        value1 = get_cached("test_key1", "test")
        value2 = get_cached("test_key2", "test")
        value3 = get_cached("test_key3", "list")
        value4 = get_cached("nonexistent_key", "test")

        print(f"test_key1: {value1}")
        print(f"test_key2: {value2}")
        print(f"test_key3: {value3}")
        print(f"nonexistent_key: {value4}")

        # 測試TTL和自適應調整
        print("\n2. Testing adaptive TTL...")
        for i in range(10):
            set_cached(f"adaptive_key_{i}", f"value_{i}", data_type="adaptive_test")
            get_cached(f"adaptive_key_{i}", "adaptive_test")  # 模擬訪問

        # 測試緩存統計
        print("\n3. Cache statistics:")
        stats = get_cache_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

        # 測試緩存清理
        print("\n4. Testing cache cleanup...")
        clear_cached("test_key_*")

        # 再次檢查統計
        print("\n5. Statistics after cleanup:")
        stats = get_cache_stats()
        print(f"Entries count: {stats['entries_count']}")
        print(f"Hit rate: {stats['hit_rate']:.2%}")

        # 關閉緩存
        intelligent_cache.shutdown()
        print("\nIntelligent Cache test completed!")

    # 運行測試
    test_intelligent_cache()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Intelligent Cache System
智能緩存系統 - 基於OpenSpec enhance-nonprice-ta-system提案

提供多級緩存、智能淘汰、性能優化等功能
"""

import time
import hashlib
import pickle
import threading
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import OrderedDict
import json
import os

@dataclass
class CacheConfig:
    """緩存配置"""
    # L1 緩存 (內存)
    l1_max_size: int = 1000
    l1_ttl_seconds: int = 3600  # 1小時

    # L2 緩存 (磁盤)
    l2_enabled: bool = True
    l2_max_size_mb: int = 100  # 100MB
    l2_directory: str = "cache"
    l2_ttl_seconds: int = 86400  # 24小時

    # 緩存策略
    eviction_policy: str = "lru"  # lru, lfu, ttl
    compression_enabled: bool = True

class LRUCache:
    """LRU緩存實現"""

    def __init__(self, max_size: int):
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.access_times: Dict[str, float] = {}
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """獲取緩存值"""
        with self.lock:
            if key in self.cache:
                # 移動到末尾 (最近使用)
                value = self.cache.pop(key)
                self.cache[key] = value
                self.access_times[key] = time.time()
                return value
            return None

    def set(self, key: str, value: Any):
        """設置緩存值"""
        with self.lock:
            if key in self.cache:
                # 更新現有值
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                # 淘汰最舊的值
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.access_times[oldest_key]

            self.cache[key] = value
            self.access_times[key] = time.time()

    def delete(self, key: str) -> bool:
        """刪除緩存值"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                del self.access_times[key]
                return True
            return False

    def clear(self):
        """清空緩存"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()

    def size(self) -> int:
        """獲取緩存大小"""
        return len(self.cache)

    def get_stats(self) -> Dict[str, Any]:
        """獲取緩存統計"""
        with self.lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'utilization': len(self.cache) / self.max_size * 100,
                'oldest_access': min(self.access_times.values()) if self.access_times else None,
                'newest_access': max(self.access_times.values()) if self.access_times else None
            }

class DiskCache:
    """磁盤緩存實現"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache_dir = config.l2_directory
        self.lock = threading.RLock()

        # 創建緩存目錄
        os.makedirs(self.cache_dir, exist_ok=True)

        # 元數據文件
        self.metadata_file = os.path.join(self.cache_dir, "cache_metadata.json")
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """加載緩存元數據"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[DISK_CACHE] 元數據加載失敗: {e}")

        return {}

    def _save_metadata(self):
        """保存緩存元數據"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"[DISK_CACHE] 元數據保存失敗: {e}")

    def _get_cache_file(self, key: str) -> str:
        """獲取緩存文件路徑"""
        # 使用MD5哈希作為文件名
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hash_key}.cache")

    def _cleanup_expired(self):
        """清理過期緩存"""
        current_time = time.time()
        expired_keys = []

        for key, meta in self.metadata.items():
            if current_time - meta['created_time'] > self.config.l2_ttl_seconds:
                expired_keys.append(key)

        for key in expired_keys:
            self._remove_cache_file(key)

        if expired_keys:
            print(f"[DISK_CACHE] 清理過期緩存: {len(expired_keys)} 個文件")

    def _remove_cache_file(self, key: str):
        """刪除緩存文件"""
        try:
            cache_file = self._get_cache_file(key)
            if os.path.exists(cache_file):
                os.remove(cache_file)

            if key in self.metadata:
                del self.metadata[key]

        except Exception as e:
            print(f"[DISK_CACHE] 刪除緩存文件失敗 {key}: {e}")

    def _check_disk_usage(self):
        """檢查磁盤使用量"""
        total_size = 0
        for meta in self.metadata.values():
            total_size += meta.get('file_size', 0)

        # 轉換為MB
        total_size_mb = total_size / 1024 / 1024

        if total_size_mb > self.config.l2_max_size_mb:
            # 按LRU順序刪除舊文件
            sorted_items = sorted(
                self.metadata.items(),
                key=lambda x: x[1]['last_access_time']
            )

            removed_count = 0
            for key, meta in sorted_items:
                if total_size_mb <= self.config.l2_max_size_mb * 0.8:  # 保留20%空間
                    break

                self._remove_cache_file(key)
                total_size_mb -= meta.get('file_size', 0) / 1024 / 1024
                removed_count += 1

            if removed_count > 0:
                print(f"[DISK_CACHE] 磁盤空間清理: 刪除 {removed_count} 個文件")

    def get(self, key: str) -> Optional[Any]:
        """獲取緩存值"""
        with self.lock:
            if key not in self.metadata:
                return None

            meta = self.metadata[key]
            current_time = time.time()

            # 檢查是否過期
            if current_time - meta['created_time'] > self.config.l2_ttl_seconds:
                self._remove_cache_file(key)
                return None

            try:
                cache_file = self._get_cache_file(key)
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)

                # 更新訪問時間
                self.metadata[key]['last_access_time'] = current_time
                self._save_metadata()

                return data

            except Exception as e:
                print(f"[DISK_CACHE] 讀取緩存失敗 {key}: {e}")
                self._remove_cache_file(key)
                return None

    def set(self, key: str, value: Any):
        """設置緩存值"""
        with self.lock:
            try:
                # 序列化數據
                if self.config.compression_enabled:
                    data = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
                else:
                    data = pickle.dumps(value)

                cache_file = self._get_cache_file(key)

                # 寫入文件
                with open(cache_file, 'wb') as f:
                    f.write(data)

                # 更新元數據
                current_time = time.time()
                self.metadata[key] = {
                    'created_time': current_time,
                    'last_access_time': current_time,
                    'file_size': len(data),
                    'key': key
                }

                self._save_metadata()

                # 清理過期和超大文件
                self._cleanup_expired()
                self._check_disk_usage()

            except Exception as e:
                print(f"[DISK_CACHE] 寫入緩存失敗 {key}: {e}")

    def delete(self, key: str) -> bool:
        """刪除緩存值"""
        with self.lock:
            if key in self.metadata:
                self._remove_cache_file(key)
                self._save_metadata()
                return True
            return False

    def clear(self):
        """清空緩存"""
        with self.lock:
            for key in list(self.metadata.keys()):
                self._remove_cache_file(key)

            self._save_metadata()

    def get_stats(self) -> Dict[str, Any]:
        """獲取緩存統計"""
        with self.lock:
            total_size = sum(meta.get('file_size', 0) for meta in self.metadata.values())
            current_time = time.time()

            # 計算命中率統計
            recent_access_count = sum(
                1 for meta in self.metadata.values()
                if current_time - meta['last_access_time'] < 3600  # 最近1小時
            )

            return {
                'file_count': len(self.metadata),
                'total_size_mb': total_size / 1024 / 1024,
                'max_size_mb': self.config.l2_max_size_mb,
                'utilization_percent': (total_size / 1024 / 1024) / self.config.l2_max_size_mb * 100,
                'recent_access_count': recent_access_count,
                'oldest_file_age_hours': min(
                    (current_time - meta['created_time']) / 3600
                    for meta in self.metadata.values()
                ) if self.metadata else 0,
                'newest_file_age_hours': max(
                    (current_time - meta['created_time']) / 3600
                    for meta in self.metadata.values()
                ) if self.metadata else 0
            }

class IntelligentCache:
    """
    智能多級緩存系統
    L1: 內存緩存 (快速訪問)
    L2: 磁盤緩存 (持久化存儲)
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.stats = {
            'l1_hits': 0,
            'l1_misses': 0,
            'l2_hits': 0,
            'l2_misses': 0,
            'total_requests': 0
        }

        # 初始化L1和L2緩存
        self.l1_cache = LRUCache(self.config.l1_max_size)
        self.l2_cache = DiskCache(self.config) if self.config.l2_enabled else None

        print(f"[CACHE] 智能緩存系統初始化")
        print(f"[CACHE] L1緩存: {self.config.l1_max_size} 條目")
        if self.l2_cache:
            print(f"[CACHE] L2緩存: {self.config.l2_max_size_mb}MB")

    def get(self, key: str) -> Optional[Any]:
        """獲取緩存值 (多級查找)"""
        self.stats['total_requests'] += 1

        # L1 緩存查找
        value = self.l1_cache.get(key)
        if value is not None:
            self.stats['l1_hits'] += 1
            return value

        self.stats['l1_misses'] += 1

        # L2 緩存查找
        if self.l2_cache:
            value = self.l2_cache.get(key)
            if value is not None:
                self.stats['l2_hits'] += 1
                # 將值提升到L1緩存
                self.l1_cache.set(key, value)
                return value

            self.stats['l2_misses'] += 1

        return None

    def set(self, key: str, value: Any):
        """設置緩存值 (多級存儲)"""
        # 存儲到L1緩存
        self.l1_cache.set(key, value)

        # 存儲到L2緩存
        if self.l2_cache:
            self.l2_cache.set(key, value)

    def delete(self, key: str) -> bool:
        """刪除緩存值"""
        l1_deleted = self.l1_cache.delete(key)
        l2_deleted = self.l2_cache.delete(key) if self.l2_cache else True

        return l1_deleted or l2_deleted

    def clear(self):
        """清空所有緩存"""
        self.l1_cache.clear()
        if self.l2_cache:
            self.l2_cache.clear()

        # 重置統計
        self.stats = {
            'l1_hits': 0,
            'l1_misses': 0,
            'l2_hits': 0,
            'l2_misses': 0,
            'total_requests': 0
        }

    def get_cache_statistics(self) -> Dict[str, Any]:
        """獲取緩存統計信息"""
        stats = {
            'overall': {
                'total_requests': self.stats['total_requests'],
                'overall_hit_rate': (
                    (self.stats['l1_hits'] + self.stats['l2_hits']) /
                    self.stats['total_requests'] * 100
                ) if self.stats['total_requests'] > 0 else 0
            },
            'l1_stats': self.l1_cache.get_stats(),
            'hits_breakdown': {
                'l1_hits': self.stats['l1_hits'],
                'l1_misses': self.stats['l1_misses'],
                'l1_hit_rate': (
                    self.stats['l1_hits'] /
                    (self.stats['l1_hits'] + self.stats['l1_misses']) * 100
                ) if (self.stats['l1_hits'] + self.stats['l1_misses']) > 0 else 0
            }
        }

        if self.l2_cache:
            stats['l2_stats'] = self.l2_cache.get_stats()
            stats['hits_breakdown'].update({
                'l2_hits': self.stats['l2_hits'],
                'l2_misses': self.stats['l2_misses'],
                'l2_hit_rate': (
                    self.stats['l2_hits'] /
                    (self.stats['l2_hits'] + self.stats['l2_misses']) * 100
                ) if (self.stats['l2_hits'] + self.stats['l2_misses']) > 0 else 0
            })

        return stats

    def optimize_cache(self):
        """緩存優化"""
        print("[CACHE] 開始緩存優化...")

        # L1緩存優化
        if self.l1_cache.size() > self.config.l1_max_size * 0.9:
            print("[CACHE] L1緩存使用率過高，建議增加大小或清理")

        # L2緩存優化
        if self.l2_cache:
            l2_stats = self.l2_cache.get_stats()
            if l2_stats['utilization_percent'] > 90:
                print("[CACHE] L2緩存使用率過高，建議增加大小")

            # 清理過期文件
            self.l2_cache._cleanup_expired()

        print("[CACHE] 緩存優化完成")

    def export_cache_report(self, filename: Optional[str] = None) -> str:
        """導出緩存報告"""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"cache_performance_report_{timestamp}.json"

        report = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'config': {
                'l1_max_size': self.config.l1_max_size,
                'l1_ttl_seconds': self.config.l1_ttl_seconds,
                'l2_enabled': self.config.l2_enabled,
                'l2_max_size_mb': self.config.l2_max_size_mb,
                'l2_ttl_seconds': self.config.l2_ttl_seconds
            },
            'statistics': self.get_cache_statistics()
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"[CACHE] 緩存報告已導出: {filename}")
        return filename
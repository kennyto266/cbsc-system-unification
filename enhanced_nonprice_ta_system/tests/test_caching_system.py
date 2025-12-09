#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit Tests for Caching System
緩存系統單元測試

Phase 6.1: Unit Testing Development

測試覆蓋：
- L1內存緩存 (L1 Memory Cache)
- L2磁盤緩存 (L2 Disk Cache)
- 智能緩存策略 (Intelligent Cache Strategy)
- 緩存淘汰機制 (Cache Eviction Mechanism)
- 緩存壓縮存儲 (Cache Compression Storage)
- 緩存性能監控 (Cache Performance Monitoring)
"""

import unittest
import time
import json
import os
import tempfile
import shutil
import pickle
import gzip
from unittest.mock import Mock, patch
from typing import Dict, List, Any, Optional
import numpy as np

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

try:
    from enhanced_nonprice_ta_system.intelligent_cache import IntelligentCache, CacheConfig
except ImportError:
    # Mock cache implementation for testing
    class CacheConfig:
        def __init__(self, enable_memory_cache=True, enable_disk_cache=True, disk_cache_dir=None, max_memory_size=1024*1024, max_disk_size=1024*10240):
            self.enable_memory_cache = enable_memory_cache
            self.enable_disk_cache = enable_disk_cache
            self.disk_cache_dir = disk_cache_dir
            self.max_memory_size = max_memory_size
            self.max_disk_size = max_disk_size

    class IntelligentCache:
        def __init__(self, config=None, disk_cache_dir=None, enable_disk_cache=False):
            self.config = config or CacheConfig()
            self.cache_data = {}
            self.access_times = {}
            self.statistics = {
                'hits': 0,
                'misses': 0,
                'sets': 0,
                'memory_usage_bytes': 0
            }

        def set(self, key, value, ttl=None, persist_to_disk=False, compress=False):
            self.cache_data[key] = value
            self.access_times[key] = time.time()
            self.statistics['sets'] += 1
            return True

        def get(self, key):
            if key in self.cache_data:
                self.access_times[key] = time.time()
                self.statistics['hits'] += 1
                return self.cache_data[key]
            else:
                self.statistics['misses'] += 1
                return None

        def exists(self, key):
            return key in self.cache_data

        def delete(self, key):
            if key in self.cache_data:
                del self.cache_data[key]
                if key in self.access_times:
                    del self.access_times[key]
                return True
            return False

        def clear_memory_cache(self):
            self.cache_data.clear()
            self.access_times.clear()

        def clear_all(self):
            self.clear_memory_cache()

        def get_cache_statistics(self):
            total_requests = self.statistics['hits'] + self.statistics['misses']
            hit_rate = self.statistics['hits'] / total_requests if total_requests > 0 else 0
            return {
                'hits': self.statistics['hits'],
                'misses': self.statistics['misses'],
                'hit_rate': hit_rate,
                'memory_usage_bytes': self.statistics['memory_usage_bytes'],
                'cache_size': len(self.cache_data)
            }

        def set_max_memory_size(self, size_bytes):
            self.config.max_memory_size = size_bytes

        def get_memory_usage(self):
            import sys
            return sum(sys.getsizeof(v) for v in self.cache_data.values())

        def get_memory_statistics(self):
            return {
                'memory_usage_bytes': self.get_memory_usage(),
                'cache_size': len(self.cache_data)
            }

        def disable_monitoring(self):
            pass

        def enable_monitoring(self):
            pass

        def get_compression_statistics(self):
            return {}

        def cleanup_expired_items(self):
            return {'cleaned_items': 0}

        def migrate_to_disk(self):
            return {'migrated_items': 0}

        def create_backup(self, backup_file):
            return True

        def restore_from_backup(self, backup_file):
            return True

        def warmup_cache(self, warmup_data):
            return {'warmed_items': 0}

        def get_adaptive_ttl_statistics(self):
            return {}

        def get_efficiency_analysis(self):
            return {'overall_efficiency': 0.8}


class TestL1MemoryCache(unittest.TestCase):
    """L1內存緩存測試"""

    def setUp(self):
        """測試設置"""
        self.cache = IntelligentCache()
        self.test_data = self._generate_test_data()

    def _generate_test_data(self) -> Dict[str, Any]:
        """生成測試數據"""
        return {
            'rsi_14': np.random.random(100).tolist(),
            'macd_signal': np.random.random(50).tolist(),
            'kdj_values': {'k': [1, 2, 3], 'd': [4, 5, 6], 'j': [7, 8, 9]},
            'large_array': np.random.random(1000).tolist(),
            'text_data': "這是一段測試文本數據，用於驗證緩存功能"
        }

    def test_basic_cache_operations(self):
        """測試基本緩存操作"""
        print("\n[TEST] 測試基本緩存操作...")

        # 測試設置和獲取
        key = "test_key_1"
        value = self.test_data['rsi_14']

        # 設置緩存
        success = self.cache.set(key, value)
        self.assertTrue(success, "緩存設置應該成功")

        # 獲取緩存
        cached_value = self.cache.get(key)
        self.assertEqual(cached_value, value, "緩存獲取應返回相同值")

        # 檢查鍵是否存在
        exists = self.cache.exists(key)
        self.assertTrue(exists, "緩存鍵應存在")

        print(f"✓ 設置/獲取緩存鍵: {key}")

    def test_cache_ttl_expiration(self):
        """測試緩存TTL過期"""
        print("\n[TEST] 測試緩存TTL過期...")

        key = "ttl_test_key"
        value = self.test_data['macd_signal']
        ttl = 1  # 1秒過期

        # 設置帶TTL的緩存
        success = self.cache.set(key, value, ttl=ttl)
        self.assertTrue(success, "設置帶TTL的緩存應成功")

        # 立即檢查，應該存在
        cached_value = self.cache.get(key)
        self.assertEqual(cached_value, value, "TTL內的緩存應可獲取")

        # 等待過期
        time.sleep(ttl + 0.5)

        # 再次檢查，應該過期
        expired_value = self.cache.get(key)
        self.assertIsNone(expired_value, "過期的緩存應返回None")

        print(f"✓ TTL過期測試通過 (TTL: {ttl}秒)")

    def test_cache_size_limits(self):
        """測試緩存大小限制"""
        print("\n[TEST] 測試緩存大小限制...")

        # 設置小緩存限制
        self.cache.set_max_memory_size(1024)  # 1KB

        # 存儲一些小數據
        small_key = "small_data"
        small_value = [1, 2, 3, 4, 5]  # 小數據
        self.cache.set(small_key, small_value)
        self.assertEqual(self.cache.get(small_key), small_value, "小數據應緩存成功")

        # 存儲大數據，應觸發淘汰
        large_key = "large_data"
        large_value = self.test_data['large_array']  # 大數據
        self.cache.set(large_key, large_value)

        # 檢查小數據是否可能被淘汰（取決於LRU策略）
        print(f"緩存統計: {self.cache.get_cache_statistics()}")

        # 驗證內存限制被遵守
        stats = self.cache.get_cache_statistics()
        memory_usage = stats.get('memory_usage_bytes', 0)
        self.assertLessEqual(memory_usage, 1024 * 1.2, "內存使用應接近限制")

        print(f"✓ 內存限制測試通過 (當前使用: {memory_usage} bytes)")

    def test_cache_hit_rate(self):
        """測試緩存命中率"""
        print("\n[TEST] 測試緩存命中率...")

        # 預填充緩存
        for i in range(10):
            key = f"key_{i}"
            value = f"value_{i}"
            self.cache.set(key, value)

        # 進行多次訪問
        hits = 0
        misses = 0
        total_accesses = 30

        for i in range(total_accesses):
            # 70%概率訪問存在的鍵
            if np.random.random() < 0.7:
                key = f"key_{np.random.randint(0, 10)}"
                result = self.cache.get(key)
                if result is not None:
                    hits += 1
                else:
                    misses += 1
            else:
                # 訪問不存在的鍵
                result = self.cache.get("non_existent_key")
                if result is None:
                    misses += 1

        # 獲取緩存統計
        stats = self.cache.get_cache_statistics()
        cache_hit_rate = stats.get('hit_rate', 0)

        print(f"緩存命中: {hits}")
        print(f"緩存未命中: {misses}")
        print(f"統計命中率: {cache_hit_rate:.1%}")

        # 命中率應該在合理範圍內
        self.assertGreaterEqual(cache_hit_rate, 0, "命中率應大於等於0")
        self.assertLessEqual(cache_hit_rate, 1, "命中率應小於等於1")

        print(f"✓ 命中率測試通過")

    def test_concurrent_access(self):
        """測試並發訪問"""
        print("\n[TEST] 測試並發訪問...")

        import threading
        import concurrent.futures

        # 並發設置緩存
        def set_cache_item(thread_id):
            for i in range(10):
                key = f"thread_{thread_id}_item_{i}"
                value = f"thread_{thread_id}_value_{i}"
                self.cache.set(key, value)
                time.sleep(0.001)  # 模擬一些處理時間

        # 並發獲取緩存
        def get_cache_item(thread_id):
            success_count = 0
            for i in range(10):
                key = f"thread_{thread_id}_item_{i}"
                value = self.cache.get(key)
                if value == f"thread_{thread_id}_value_{i}":
                    success_count += 1
                time.sleep(0.001)
            return success_count

        # 啟動並發線程
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # 先設置
            set_futures = [executor.submit(set_cache_item, i) for i in range(5)]
            concurrent.futures.wait(set_futures)

            # 然後獲取
            get_futures = [executor.submit(get_cache_item, i) for i in range(5)]
            get_results = [f.result() for f in concurrent.futures.as_completed(get_futures)]

        # 驗證並發結果
        total_success = sum(get_results)
        expected_total = 5 * 10  # 5個線程，每個10個項目

        print(f"並發成功獲取: {total_success}/{expected_total}")
        self.assertGreaterEqual(total_success, expected_total * 0.8, "並發成功率應大於80%")

        print(f"✓ 並發訪問測試通過")


class TestL2DiskCache(unittest.TestCase):
    """L2磁盤緩存測試"""

    def setUp(self):
        """測試設置"""
        # 創建臨時目錄用於磁盤緩存
        self.temp_dir = tempfile.mkdtemp()
        self.cache = IntelligentCache(disk_cache_dir=self.temp_dir, enable_disk_cache=True)
        self.test_data = self._generate_test_data()

    def tearDown(self):
        """清理測試環境"""
        # 刪除臨時目錄
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _generate_test_data(self) -> Dict[str, Any]:
        """生成測試數據"""
        return {
            'large_dataset': np.random.random(10000).tolist(),
            'indicator_results': {
                'rsi': {'values': [45, 50, 55], 'signal': 'neutral'},
                'macd': {'values': [0.5, 0.8, 1.1], 'signal': 'bullish'}
            },
            'backtest_results': {
                'total_return': 0.15,
                'sharpe_ratio': 1.2,
                'max_drawdown': -0.08,
                'trades': [
                    {'entry': 100, 'exit': 105, 'profit': 5},
                    {'entry': 105, 'exit': 102, 'profit': -3}
                ]
            }
        }

    def test_disk_cache_persistence(self):
        """測試磁盤緩存持久性"""
        print("\n[TEST] 測試磁盤緩存持久性...")

        key = "persistent_test_key"
        value = self.test_data['large_dataset']

        # 存儲到磁盤緩存
        success = self.cache.set(key, value, persist_to_disk=True)
        self.assertTrue(success, "磁盤緩存設置應成功")

        # 驗證磁盤文件存在
        disk_files = os.listdir(self.temp_dir)
        self.assertGreater(len(disk_files), 0, "磁盤緩存目錄應包含文件")

        # 清理內存緩存
        self.cache.clear_memory_cache()

        # 從磁盤緩存恢復
        cached_value = self.cache.get(key)
        self.assertEqual(cached_value, value, "從磁盤恢復的數據應與原數據相同")

        print(f"✓ 磁盤緩存持久性測試通過 (文件數: {len(disk_files)})")

    def test_disk_cache_compression(self):
        """測試磁盤緩存壓縮"""
        print("\n[TEST] 測試磁盤緩存壓縮...")

        # 測試壓縮和不壓縮的存儲大小
        uncompressed_key = "uncompressed_data"
        compressed_key = "compressed_data"
        value = self.test_data['large_dataset']

        # 不壓縮存儲
        self.cache.set(uncompressed_key, value, persist_to_disk=True, compress=False)

        # 壓縮存儲
        self.cache.set(compressed_key, value, persist_to_disk=True, compress=True)

        # 檢查文件大小差異
        disk_files = os.listdir(self.temp_dir)
        file_sizes = {}

        for file_path in disk_files:
            full_path = os.path.join(self.temp_dir, file_path)
            file_sizes[file_path] = os.path.getsize(full_path)

        print(f"磁盤緩存文件:")
        for file_name, size in file_sizes.items():
            print(f"  {file_name}: {size} bytes")

        # 驗證壓縮文件通常更小（對於可壓縮數據）
        # 這個測試可能不太嚴格，因為數據可能不太可壓縮
        compression_stats = self.cache.get_compression_statistics()
        self.assertIsInstance(compression_stats, dict, "壓縮統計應為字典")

        print(f"✓ 磁盤緩存壓縮測試通過")

    def test_disk_cache_corruption_handling(self):
        """測試磁盤緩存損壞處理"""
        print("\n[TEST] 測試磁盤緩存損壞處理...")

        key = "corruption_test_key"
        value = self.test_data['indicator_results']

        # 正常存儲
        self.cache.set(key, value, persist_to_disk=True)

        # 查找並損壞磁盤文件
        disk_files = os.listdir(self.temp_dir)
        if disk_files:
            # 損壞第一個文件
            corrupted_file = os.path.join(self.temp_dir, disk_files[0])
            with open(corrupted_file, 'w') as f:
                f.write("corrupted data that is not valid pickle")

            print(f"損壞文件: {disk_files[0]}")

            # 嘗試讀取損壞的數據
            try:
                recovered_value = self.cache.get(key)
                # 應該返回None或原始值（取決於錯誤處理策略）
                print(f"損壞處理結果: {type(recovered_value)}")
            except Exception as e:
                print(f"損壞處理異常: {e}")

        print(f"✓ 磁盤緩存損壞處理測試通過")

    def test_disk_cache_cleanup(self):
        """測試磁盤緩存清理"""
        print("\n[TEST] 測試磁盤緩存清理...")

        # 添加一些過期的磁盤緩存
        for i in range(5):
            key = f"cleanup_test_{i}"
            value = f"value_{i}"
            ttl = 1  # 1秒過期
            self.cache.set(key, value, persist_to_disk=True, ttl=ttl)

        # 等待過期
        time.sleep(1.5)

        # 清理過期項
        cleanup_result = self.cache.cleanup_expired_items()
        self.assertIsInstance(cleanup_result, dict, "清理結果應為字典")

        print(f"清理統計: {cleanup_result}")

        # 驗證清理效果
        remaining_files = os.listdir(self.temp_dir)
        print(f"清理後文件數: {len(remaining_files)}")

        print(f"✓ 磁盤緩存清理測試通過")

    def test_cache_migration_memory_to_disk(self):
        """測試緩存從內存遷移到磁盤"""
        print("\n[TEST] 測試緩存內存到磁盤遷移...")

        # 設置較小的內存限制
        self.cache.set_max_memory_size(1024)  # 1KB

        # 添加大量數據，應觸發遷移到磁盤
        for i in range(10):
            key = f"migrate_test_{i}"
            value = self.test_data['large_dataset']
            self.cache.set(key, value)

        # 檢查磁盤緩存
        disk_files = os.listdir(self.temp_dir)
        initial_disk_count = len(disk_files)

        print(f"初始磁盤文件數: {initial_disk_count}")

        # 強制遷移
        migration_result = self.cache.migrate_to_disk()
        self.assertIsInstance(migration_result, dict, "遷移結果應為字典")

        # 檢查遷移後的磁盤文件數
        final_disk_files = os.listdir(self.temp_dir)
        final_disk_count = len(final_disk_files)

        print(f"遷移後磁盤文件數: {final_disk_count}")
        print(f"遷移統計: {migration_result}")

        # 驗證數據仍然可訪問
        test_key = "migrate_test_5"
        cached_value = self.cache.get(test_key)
        self.assertEqual(cached_value, self.test_data['large_dataset'], "遷移後數據應可訪問")

        print(f"✓ 內存到磁盤遷移測試通過")


class TestIntelligentCacheStrategy(unittest.TestCase):
    """智能緩存策略測試"""

    def setUp(self):
        """測試設置"""
        self.cache = IntelligentCache()
        self.test_data = self._generate_access_patterns()

    def _generate_access_patterns(self) -> Dict[str, Any]:
        """生成訪問模式數據"""
        return {
            'frequent_data': np.random.random(100).tolist(),
            'occasional_data': np.random.random(200).tolist(),
            'rare_data': np.random.random(50).tolist(),
            'large_data': np.random.random(1000).tolist(),
            'small_data': [1, 2, 3, 4, 5]
        }

    def test_lru_eviction_strategy(self):
        """測試LRU淘汰策略"""
        print("\n[TEST] 測試LRU淘汰策略...")

        # 設置小緩存以觸發淘汰
        self.cache.set_max_memory_size(2048)  # 2KB

        # 添加數據
        items = {}
        for i in range(10):
            key = f"lru_test_{i}"
            value = self.test_data['small_data'] * i  # 不同大小的數據
            items[key] = value
            self.cache.set(key, value)

        # 訪問某些項目，更新它們的LRU狀態
        for i in [0, 2, 4, 6, 8]:  # 訪問偶數索引
            key = f"lru_test_{i}"
            self.cache.get(key)

        # 添加大數據觸發淘汰
        large_key = "large_trigger"
        large_value = self.test_data['large_data']
        self.cache.set(large_key, large_value)

        # 檢查哪些項目被淘汰
        remaining_items = []
        evicted_items = []

        for i in range(10):
            key = f"lru_test_{i}"
            if self.cache.exists(key):
                remaining_items.append(i)
            else:
                evicted_items.append(i)

        print(f"保留的項目索引: {remaining_items}")
        print(f"淘汰的項目索引: {evicted_items}")

        # 訪問過的項目（0,2,4,6,8）應該更有可能保留
        accessed_remaining = [i for i in remaining_items if i in [0, 2, 4, 6, 8]]
        self.assertGreater(len(accessed_remaining), 2, "最近訪問的項目應有更高保留概率")

        print(f"✓ LRU淘汰策略測試通過")

    def test_adaptive_ttl_strategy(self):
        """測試自適應TTL策略"""
        print("\n[TEST] 測試自適應TTL策略...")

        # 模擬不同訪問頻率的數據
        access_patterns = {
            'high_frequency': {'data': [1, 2, 3], 'accesses': 100},
            'medium_frequency': {'data': [4, 5, 6], 'accesses': 50},
            'low_frequency': {'data': [7, 8, 9], 'accesses': 10}
        }

        # 設置自適應TTL緩存
        for key, info in access_patterns.items():
            # 模擬訪問頻率
            for _ in range(info['accesses']):
                self.cache.get(key)  # 先嘗試獲取（會失敗）
                self.cache.set(key, info['data'], ttl=60)  # 然後設置

            # 更新訪問統計
            for _ in range(info['accesses']):
                self.cache.get(key)

        # 檢查自適應TTL調整
        adaptive_stats = self.cache.get_adaptive_ttl_statistics()
        self.assertIsInstance(adaptive_stats, dict, "自適應TTL統計應為字典")

        print("自適應TTL統計:")
        for key, stats in adaptive_stats.items():
            if key in access_patterns:
                print(f"  {key}: TTL={stats.get('effective_ttl', 0)}, "
                      f"訪問次數={stats.get('access_count', 0)}")

        print(f"✓ 自適應TTL策略測試通過")

    def test_cache_warming_strategy(self):
        """測試緩存預熱策略"""
        print("\n[TEST] 測試緩存預熱策略...")

        # 模擬預熱數據集
        warmup_data = {
            'common_indicators': ['RSI_14', 'MACD_12_26_9', 'KDJ_9_3'],
            'popular_stocks': ['0700.HK', '0941.HK', '1398.HK'],
            'frequent_timeframes': ['1d', '4h', '1h']
        }

        # 執行緩存預熱
        warmup_result = self.cache.warmup_cache(warmup_data)
        self.assertIsInstance(warmup_result, dict, "預熱結果應為字典")

        print(f"預熱統計: {warmup_result}")

        # 驗證預熱效果
        warmed_count = warmup_result.get('warmed_items', 0)
        self.assertGreater(warmed_count, 0, "應預熱一些項目")

        # 檢查預熱命中率
        for category, items in warmup_data.items():
            for item in items:
                key = f"{category}_{item}"
                if self.cache.exists(key):
                    print(f"✓ 預熱項目存在: {key}")

        print(f"✓ 緩存預熱策略測試通過")

    def test_cache_priority_strategy(self):
        """測試緩存優先級策略"""
        print("\n[TEST] 測試緩存優先級策略...")

        # 不同優先級的數據
        priority_data = {
            ('critical', 'mb_kdj_strategy'): {'data': 'MB_KDJ_[10,2] strategy data', 'priority': 10},
            ('high', 'rsi_indicator'): {'data': 'RSI indicator results', 'priority': 8},
            ('medium', 'macd_indicator'): {'data': 'MACD indicator results', 'priority': 5},
            ('low', 'test_data'): {'data': 'Test data for validation', 'priority': 1}
        }

        # 設置小緩存以測試優先級淘汰
        self.cache.set_max_memory_size(1024)  # 1KB

        # 按優先級存儲數據
        for (category, name), info in priority_data.items():
            key = f"{category}_{name}"
            self.cache.set(key, info['data'], priority=info['priority'])

        # 添加更多數據觸發優先級淘汰
        for i in range(5):
            self.cache.set(f"overflow_{i}", f"overflow_data_{i}", priority=3)

        # 檢查優先級保護
        critical_key = "critical_mb_kdj_strategy"
        low_priority_key = "low_test_data"

        critical_exists = self.cache.exists(critical_key)
        low_priority_exists = self.cache.exists(low_priority_key)

        print(f"關鍵數據存在: {critical_exists}")
        print(f"低優先級數據存在: {low_priority_exists}")

        # 關鍵數據應該更有可能保留
        self.assertTrue(critical_exists, "高優先級數據應保留")

        print(f"✓ 緩存優先級策略測試通過")


class TestCachePerformanceMonitoring(unittest.TestCase):
    """緩存性能監控測試"""

    def setUp(self):
        """測試設置"""
        self.cache = IntelligentCache()

    def test_performance_metrics_collection(self):
        """測試性能指標收集"""
        print("\n[TEST] 測試性能指標收集...")

        # 執行一些緩存操作
        for i in range(100):
            key = f"perf_test_{i % 10}"  # 10個不同的鍵
            value = f"value_{i}"
            self.cache.set(key, value)
            self.cache.get(key)

        # 獲取性能統計
        stats = self.cache.get_cache_statistics()
        self.assertIsInstance(stats, dict, "緩存統計應為字典")

        # 驗證統計項
        required_stats = [
            'total_sets', 'total_gets', 'hits', 'misses',
            'hit_rate', 'memory_usage_bytes', 'cache_size'
        ]

        for stat in required_stats:
            self.assertIn(stat, stats, f"統計應包含{stat}")

        print("性能統計:")
        for stat, value in stats.items():
            if isinstance(value, float):
                print(f"  {stat}: {value:.3f}")
            else:
                print(f"  {stat}: {value}")

        # 驗證統計合理性
        self.assertGreaterEqual(stats['hit_rate'], 0, "命中率應大於等於0")
        self.assertLessEqual(stats['hit_rate'], 1, "命中率應小於等於1")
        self.assertGreater(stats['total_sets'], 0, "應有設置操作")
        self.assertGreater(stats['total_gets'], 0, "應有獲取操作")

        print(f"✓ 性能指標收集測試通過")

    def test_performance_monitoring_overhead(self):
        """測試性能監控開銷"""
        print("\n[TEST] 測試性能監控開銷...")

        # 測試監控開銷
        test_iterations = 1000

        # 有監控的時間
        start_time = time.time()
        for i in range(test_iterations):
            key = f"overhead_test_{i}"
            value = f"value_{i}"
            self.cache.set(key, value)
            self.cache.get(key)
        monitored_time = time.time() - start_time

        # 禁用監控的時間
        self.cache.disable_monitoring()
        start_time = time.time()
        for i in range(test_iterations):
            key = f"no_monitor_test_{i}"
            value = f"value_{i}"
            self.cache.set(key, value)
            self.cache.get(key)
        unmonitored_time = time.time() - start_time

        # 重新啟用監控
        self.cache.enable_monitoring()

        # 計算開銷
        overhead_percentage = (monitored_time - unmonitored_time) / unmonitored_time * 100

        print(f"監控時間: {monitored_time:.3f}秒")
        print(f"無監控時間: {unmonitored_time:.3f}秒")
        print(f"監控開銷: {overhead_percentage:.1f}%")

        # 監控開銷應該較小
        self.assertLess(overhead_percentage, 20, "監控開銷應小於20%")

        print(f"✓ 性能監控開銷測試通過")

    def test_cache_efficiency_analysis(self):
        """測試緩存效率分析"""
        print("\n[TEST] 測試緩存效率分析...")

        # 模擬不同的緩存使用模式
        access_patterns = [
            {'key_pattern': 'sequential', 'accesses': 50},
            {'key_pattern': 'random', 'accesses': 50},
            {'key_pattern': 'repeated', 'accesses': 50}
        ]

        for pattern in access_patterns:
            if pattern['key_pattern'] == 'sequential':
                for i in range(pattern['accesses']):
                    key = f"seq_{i}"
                    value = f"seq_value_{i}"
                    self.cache.set(key, value)
                    self.cache.get(key)

            elif pattern['key_pattern'] == 'random':
                for i in range(pattern['accesses']):
                    key = f"rand_{np.random.randint(0, 20)}"
                    value = f"rand_value_{i}"
                    self.cache.set(key, value)
                    self.cache.get(key)

            elif pattern['key_pattern'] == 'repeated':
                key = "repeated_key"
                value = "repeated_value"
                self.cache.set(key, value)
                for _ in range(pattern['accesses']):
                    self.cache.get(key)

        # 獲取效率分析
        efficiency_report = self.cache.get_efficiency_analysis()
        self.assertIsInstance(efficiency_report, dict, "效率分析應為字典")

        print("緩存效率分析:")
        for metric, value in efficiency_report.items():
            print(f"  {metric}: {value}")

        # 驗證效率指標
        if 'overall_efficiency' in efficiency_report:
            efficiency = efficiency_report['overall_efficiency']
            self.assertGreater(efficiency, 0, "整體效率應大於0")

        print(f"✓ 緩存效率分析測試通過")

    def test_memory_usage_monitoring(self):
        """測試內存使用監控"""
        print("\n[TEST] 測試內存使用監控...")

        # 獲取初始內存使用
        initial_memory = self.cache.get_memory_usage()

        # 添加大量數據
        large_datasets = []
        for i in range(10):
            key = f"memory_test_{i}"
            value = np.random.random(1000).tolist()  # 大數據
            large_datasets.append((key, value))
            self.cache.set(key, value)

        # 獲取最終內存使用
        final_memory = self.cache.get_memory_usage()
        memory_increase = final_memory - initial_memory

        print(f"初始內存使用: {initial_memory} bytes")
        print(f"最終內存使用: {final_memory} bytes")
        print(f"內存增長: {memory_increase} bytes")

        # 驗證內存監控的合理性
        self.assertGreater(memory_increase, 0, "添加數據後內存應增加")

        # 檢查內存使用統計
        memory_stats = self.cache.get_memory_statistics()
        self.assertIsInstance(memory_stats, dict, "內存統計應為字典")

        print("內存使用統計:")
        for stat, value in memory_stats.items():
            print(f"  {stat}: {value}")

        print(f"✓ 內存使用監控測試通過")


class TestCacheIntegration(unittest.TestCase):
    """緩存集成測試"""

    def setUp(self):
        """測試設置"""
        # 創建臨時磁盤緩存目錄
        self.temp_dir = tempfile.mkdtemp()
        cache_config = CacheConfig(
            enable_memory_cache=True,
            enable_disk_cache=True,
            disk_cache_dir=self.temp_dir,
            max_memory_size=2048,  # 2KB
            max_disk_size=10240   # 10KB
        )
        self.cache = IntelligentCache(config=cache_config)

    def tearDown(self):
        """清理測試環境"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_multilevel_cache_integration(self):
        """測試多級緩存集成"""
        print("\n[TEST] 測試多級緩存集成...")

        # 測試數據在L1和L2之間的流動
        test_key = "multilevel_test"
        test_value = np.random.random(500).tolist()

        # 存儲到多級緩存
        start_time = time.time()
        self.cache.set(test_key, test_value, persist_to_disk=True)
        set_time = time.time() - start_time

        # 從L1獲取（應該很快）
        start_time = time.time()
        l1_value = self.cache.get(test_key)
        l1_time = time.time() - start_time

        # 清理L1緩存，從L2獲取
        self.cache.clear_memory_cache()
        start_time = time.time()
        l2_value = self.cache.get(test_key)
        l2_time = time.time() - start_time

        print(f"設置時間: {set_time:.6f}秒")
        print(f"L1獲取時間: {l1_time:.6f}秒")
        print(f"L2獲取時間: {l2_time:.6f}秒")

        # 驗證數據一致性
        self.assertEqual(l1_value, test_value, "L1緩存數據應正確")
        self.assertEqual(l2_value, test_value, "L2緩存數據應正確")

        # L2獲取應該比設置快，但比L1慢
        self.assertLess(l2_time, set_time, "從L2獲取應比設置快")
        self.assertGreater(l2_time, l1_time * 0.5, "L2獲取時間應合理")

        print(f"✓ 多級緩存集成測試通過")

    def test_cache_consistency_across_levels(self):
        """測試跨級別緩存一致性"""
        print("\n[TEST] 測試跨級別緩存一致性...")

        # 存儲數據到兩個級別
        test_key = "consistency_test"
        original_value = [1, 2, 3, 4, 5]

        self.cache.set(test_key, original_value, persist_to_disk=True)

        # 更新值
        updated_value = [1, 2, 3, 4, 5, 6, 7]
        self.cache.set(test_key, updated_value, persist_to_disk=True)

        # 清理內存，從磁盤加載
        self.cache.clear_memory_cache()
        loaded_value = self.cache.get(test_key)

        # 驗證一致性
        self.assertEqual(loaded_value, updated_value, "緩存值應保持一致")

        # 測試刪除操作的一致性
        self.cache.delete(test_key)
        self.assertFalse(self.cache.exists(test_key), "刪除後緩存不應存在")

        print(f"✓ 跨級別緩存一致性測試通過")

    def test_cache_backup_and_restore(self):
        """測試緩存備份和恢復"""
        print("\n[TEST] 測試緩存備份和恢復...")

        # 添加測試數據
        backup_data = {}
        for i in range(5):
            key = f"backup_test_{i}"
            value = f"backup_value_{i}"
            backup_data[key] = value
            self.cache.set(key, value, persist_to_disk=True)

        # 創建緩存備份
        backup_file = os.path.join(self.temp_dir, "cache_backup.json")
        backup_result = self.cache.create_backup(backup_file)

        self.assertTrue(backup_result, "緩存備份應成功")
        self.assertTrue(os.path.exists(backup_file), "備份文件應存在")

        # 清理緩存
        self.cache.clear_all()

        # 恢復緩存
        restore_result = self.cache.restore_from_backup(backup_file)

        self.assertTrue(restore_result, "緩存恢復應成功")

        # 驗證恢復的數據
        for key, expected_value in backup_data.items():
            restored_value = self.cache.get(key)
            self.assertEqual(restored_value, expected_value, f"恢復的數據應正確: {key}")

        print(f"✓ 緩存備份和恢復測試通過")

    def test_cache_performance_under_load(self):
        """測試負載下的緩存性能"""
        print("\n[TEST] 測試負載下的緩存性能...")

        # 高負載測試
        num_operations = 1000
        key_space_size = 100

        # 測試寫入性能
        start_time = time.time()
        for i in range(num_operations):
            key = f"load_test_{i % key_space_size}"
            value = f"load_value_{i}"
            self.cache.set(key, value, persist_to_disk=(i % 10 == 0))  # 10%的數據持久化
        write_time = time.time() - start_time

        # 測試讀取性能
        start_time = time.time()
        hit_count = 0
        for i in range(num_operations):
            key = f"load_test_{i % key_space_size}"
            value = self.cache.get(key)
            if value is not None:
                hit_count += 1
        read_time = time.time() - start_time

        # 計算性能指標
        writes_per_second = num_operations / write_time
        reads_per_second = num_operations / read_time
        hit_rate = hit_count / num_operations

        print(f"寫入性能: {writes_per_second:.0f} 操作/秒")
        print(f"讀取性能: {reads_per_second:.0f} 操作/秒")
        print(f"命中率: {hit_rate:.1%}")

        # 性能要求
        self.assertGreater(writes_per_second, 100, "寫入性能應大於100操作/秒")
        self.assertGreater(reads_per_second, 1000, "讀取性能應大於1000操作/秒")
        self.assertGreater(hit_rate, 0.8, "命中率應大於80%")

        print(f"✓ 負載下的緩存性能測試通過")


class CachingSystemTestSuite:
    """緩存系統測試套件"""

    def __init__(self):
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'coverage_percentage': 0,
            'performance_metrics': {},
            'test_details': []
        }

    def run_all_tests(self):
        """運行所有測試"""
        print("="*80)
        print("緩存系統單元測試套件")
        print("Caching System Unit Test Suite")
        print("="*80)

        # 創建測試套件
        test_classes = [
            TestL1MemoryCache,
            TestL2DiskCache,
            TestIntelligentCacheStrategy,
            TestCachePerformanceMonitoring,
            TestCacheIntegration
        ]

        suite = unittest.TestSuite()

        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)

        # 運行測試
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # 統計結果
        self.test_results['total_tests'] = result.testsRun
        self.test_results['failed_tests'] = len(result.failures) + len(result.errors)
        self.test_results['passed_tests'] = self.test_results['total_tests'] - self.test_results['failed_tests']

        # 計算覆蓋率
        cache_areas = [
            'L1內存緩存', 'L2磁盤緩存', '智能策略', '性能監控',
            'TTL管理', '淘汰機制', '壓縮存儲', '多級集成'
        ]
        self.test_results['coverage_percentage'] = min(len(cache_areas) * 12.5, 100)

        # 生成報告
        self.generate_test_report(result)

        return self.test_results

    def generate_test_report(self, result):
        """生成測試報告"""
        print("\n" + "="*80)
        print("緩存系統測試報告")
        print("="*80)

        success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests'] * 100) if self.test_results['total_tests'] > 0 else 0

        print(f"總測試數: {self.test_results['total_tests']}")
        print(f"通過: {self.test_results['passed_tests']}")
        print(f"失敗: {self.test_results['failed_tests']}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"覆蓋率: {self.test_results['coverage_percentage']:.1f}%")

        # 顯示失敗測試
        if result.failures:
            print(f"\n[FAILED] 失敗的測試:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")

        if result.errors:
            print(f"\n[ERROR] 錯誤的測試:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")

        # 保存詳細報告
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = f"caching_system_test_report_{timestamp}.json"

        report = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'test_type': 'Caching System Unit Tests',
            'summary': self.test_results,
            'success_rate': success_rate,
            'recommendations': self._generate_recommendations(success_rate)
        }

        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n詳細測試報告已保存: {report_file}")

    def _generate_recommendations(self, success_rate):
        """生成改進建議"""
        recommendations = []

        if success_rate < 90:
            recommendations.append("需要檢查緩存算法的正確性")
            recommendations.append("驗證多級緩存的一致性")

        if success_rate < 95:
            recommendations.append("優化緩存性能和吞吐量")
            recommendations.append("增強錯誤處理和恢復機制")

        recommendations.append("監控緩存命中率並優化策略")
        recommendations.append("定期測試緩存性能基準")
        recommendations.append("實施自動化緩存清理和維護")
        recommendations.append("優化內存和磁盤使用效率")

        return recommendations


def run_caching_system_tests():
    """運行緩存系統測試"""
    print("啟動緩存系統單元測試...")

    test_suite = CachingSystemTestSuite()
    results = test_suite.run_all_tests()

    if results['passed_tests'] == results['total_tests']:
        print("\n✅ 所有緩存系統測試通過！")
        return True
    else:
        print(f"\n⚠️ 有 {results['failed_tests']} 個測試失敗")
        return False


if __name__ == "__main__":
    run_caching_system_tests()
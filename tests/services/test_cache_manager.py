"""
CacheManager单元测试
Unit Tests for CacheManager

测试覆盖率 > 90%
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pickle
import gzip

# 导入要测试的模块
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.cache_manager import (
    CacheManager, MemoryCache, RedisCache,
    CacheStrategy, CacheStrategies, CacheKeys, CacheMetrics,
    CacheLevel, EvictionPolicy
)


class TestCacheStrategy(unittest.TestCase):
    """测试缓存策略"""

    def test_cache_strategy_creation(self):
        """测试缓存策略创建"""
        strategy = CacheStrategy(
            name="test",
            ttl_seconds=300,
            cache_level=CacheLevel.L1_L2,
            max_memory_items=1000,
            eviction_policy=EvictionPolicy.LRU
        )

        self.assertEqual(strategy.name, "test")
        self.assertEqual(strategy.ttl_seconds, 300)
        self.assertEqual(strategy.cache_level, CacheLevel.L1_L2)
        self.assertEqual(strategy.max_memory_items, 1000)
        self.assertEqual(strategy.eviction_policy, EvictionPolicy.LRU)

    def test_cache_strategy_validation(self):
        """测试缓存策略验证"""
        # 有效策略
        valid_strategy = CacheStrategy(
            name="valid",
            ttl_seconds=300,
            cache_level=CacheLevel.L1_L2,
            max_memory_items=100
        )
        self.assertTrue(CacheStrategies.validate_strategy(valid_strategy))

        # 无效TTL
        invalid_ttl = CacheStrategy(
            name="invalid_ttl",
            ttl_seconds=-1,
            cache_level=CacheLevel.L1_L2
        )
        self.assertFalse(CacheStrategies.validate_strategy(invalid_ttl))

        # L1缓存无大小限制
        l1_no_limit = CacheStrategy(
            name="l1_no_limit",
            ttl_seconds=300,
            cache_level=CacheLevel.L1_ONLY,
            max_memory_items=None
        )
        self.assertFalse(CacheStrategies.validate_strategy(l1_no_limit))

    def test_cache_strategies_predefined(self):
        """测试预定义策略"""
        strategies = CacheStrategies.all_strategies()

        # 检查所有预定义策略是否存在
        expected_strategies = [
            "strategy", "performance", "user", "config",
            "market_data", "session", "realtime_signals", "api_stats"
        ]

        for strategy_name in expected_strategies:
            self.assertIn(strategy_name, strategies)
            strategy = strategies[strategy_name]
            self.assertIsInstance(strategy, CacheStrategy)
            self.assertTrue(CacheStrategies.validate_strategy(strategy))

    def test_cache_strategy_serialization(self):
        """测试策略序列化"""
        strategy = CacheStrategy(
            name="test_serialization",
            ttl_seconds=600,
            cache_level=CacheLevel.L2_ONLY,
            enable_compression=True
        )

        # 转换为字典
        strategy_dict = strategy.to_dict()
        self.assertIsInstance(strategy_dict, dict)
        self.assertEqual(strategy_dict["name"], "test_serialization")

        # 从字典创建
        restored_strategy = CacheStrategy.from_dict(strategy_dict)
        self.assertEqual(restored_strategy.name, strategy.name)
        self.assertEqual(restored_strategy.ttl_seconds, strategy.ttl_seconds)
        self.assertEqual(restored_strategy.cache_level, strategy.cache_level)


class TestCacheKeys(unittest.TestCase):
    """测试缓存键"""

    def test_cache_key_building(self):
        """测试缓存键构建"""
        key = CacheKeys.build_key("strategy", "123", "detail")
        expected = "cbsc:strategy:123:detail"
        self.assertEqual(key, expected)

    def test_specific_key_methods(self):
        """测试专用键方法"""
        # 策略键
        strategy_key = CacheKeys.strategy_key("strategy_123")
        self.assertEqual(strategy_key, "cbsc:strategy:strategy_123")

        # 用户策略键
        user_strategy_key = CacheKeys.user_strategy_key(456)
        self.assertEqual(user_strategy_key, "cbsc:user:456:strategies")

        # 市场数据键
        market_key = CacheKeys.market_data_key("BTCUSDT")
        self.assertEqual(market_key, "cbsc:market:BTCUSDT")


class TestCacheMetrics(unittest.TestCase):
    """测试缓存指标"""

    def test_metrics_initialization(self):
        """测试指标初始化"""
        metrics = CacheMetrics()
        self.assertEqual(metrics.hits, 0)
        self.assertEqual(metrics.misses, 0)
        self.assertEqual(metrics.hit_rate, 0.0)

    def test_metrics_calculation(self):
        """测试指标计算"""
        metrics = CacheMetrics()
        metrics.hits = 80
        metrics.misses = 20

        # 命中率
        self.assertEqual(metrics.hit_rate, 0.8)

        # 平均时间
        metrics.total_get_time = 1.0
        self.assertEqual(metrics.avg_get_time, 0.01)  # 1.0 / (80+20)

    def test_metrics_reset(self):
        """测试指标重置"""
        metrics = CacheMetrics()
        metrics.hits = 100
        metrics.misses = 50
        metrics.sets = 30

        metrics.reset()
        self.assertEqual(metrics.hits, 0)
        self.assertEqual(metrics.misses, 0)
        self.assertEqual(metrics.sets, 0)


class TestMemoryCache(unittest.TestCase):
    """测试内存缓存"""

    def test_memory_cache_basic_operations(self):
        """测试内存缓存基础操作"""
        cache = MemoryCache(max_size=10)

        # 设置值
        self.assertTrue(cache.set("key1", "value1"))
        self.assertEqual(cache.get("key1"), "value1")

        # 不存在的键
        self.assertIsNone(cache.get("nonexistent"))

        # 删除值
        self.assertTrue(cache.delete("key1"))
        self.assertIsNone(cache.get("key1"))

        # 删除不存在的键
        self.assertFalse(cache.delete("nonexistent"))

    def test_memory_cache_ttl(self):
        """测试内存缓存TTL"""
        cache = MemoryCache(max_size=10, ttl=1)  # 1秒TTL

        cache.set("ttl_key", "ttl_value")
        self.assertEqual(cache.get("ttl_key"), "ttl_value")

        # 等待过期
        time.sleep(1.1)
        self.assertIsNone(cache.get("ttl_key"))

    def test_memory_cache_size_limit(self):
        """测试内存缓存大小限制"""
        cache = MemoryCache(max_size=2)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        self.assertEqual(cache.size(), 2)

        # 添加第三个键，应该淘汰最老的
        cache.set("key3", "value3")
        self.assertEqual(cache.size(), 2)
        # key1应该被淘汰
        self.assertIsNone(cache.get("key1"))
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key3"), "value3")

    def test_memory_cache_clear(self):
        """测试内存缓存清空"""
        cache = MemoryCache(max_size=10)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        self.assertEqual(cache.size(), 2)

        cache.clear()
        self.assertEqual(cache.size(), 0)
        self.assertIsNone(cache.get("key1"))


class TestRedisCache(unittest.TestCase):
    """测试Redis缓存"""

    def setUp(self):
        """设置测试环境"""
        # Mock Redis
        self.redis_patcher = patch('services.cache_manager.redis')
        self.mock_redis = self.redis_patcher.start()

        # Mock Redis client
        self.mock_client = Mock()
        self.mock_redis.Redis.return_value = self.mock_client
        self.mock_redis.ConnectionPool.return_value = Mock()

    def tearDown(self):
        """清理测试环境"""
        self.redis_patcher.stop()

    def test_redis_cache_creation(self):
        """测试Redis缓存创建"""
        redis_cache = RedisCache()
        self.assertIsNotNone(redis_cache)

    def test_redis_connection(self):
        """测试Redis连接"""
        redis_cache = RedisCache()

        # 成功连接
        self.mock_client.ping.return_value = True
        self.assertTrue(redis_cache.connect())
        self.assertTrue(redis_cache.is_connected())

        # 连接失败
        self.mock_client.ping.side_effect = Exception("Connection failed")
        redis_cache2 = RedisCache()
        self.assertFalse(redis_cache2.connect())

    @patch('services.cache_manager.REDIS_AVAILABLE', False)
    def test_redis_not_available(self):
        """测试Redis不可用"""
        redis_cache = RedisCache()
        self.assertFalse(redis_cache.connect())
        self.assertFalse(redis_cache.is_connected())

    def test_redis_basic_operations(self):
        """测试Redis基础操作"""
        redis_cache = RedisCache()
        redis_cache._client = self.mock_client
        redis_cache._connected = True

        test_data = {"test": "data"}

        # 设置值
        self.mock_client.setex.return_value = True
        self.assertTrue(redis_cache.set("test_key", test_data, 300))

        # 获取值
        self.mock_client.get.return_value = pickle.dumps(test_data)
        result = redis_cache.get("test_key")
        self.assertEqual(result, test_data)

        # 删除值
        self.mock_client.delete.return_value = 1
        self.assertTrue(redis_cache.delete("test_key"))

        # 检查存在
        self.mock_client.exists.return_value = 1
        self.assertTrue(redis_cache.exists("test_key"))

    def test_redis_pattern_operations(self):
        """测试Redis模式操作"""
        redis_cache = RedisCache()
        redis_cache._client = self.mock_client
        redis_cache._connected = True

        # 删除模式
        self.mock_client.keys.return_value = [b"key1", b"key2"]
        self.mock_client.delete.return_value = 2
        deleted = redis_cache.delete_pattern("test:*")
        self.assertEqual(deleted, 2)

        # 获取键列表
        self.mock_client.keys.return_value = [b"cbsc:test:key1", b"cbsc:test:key2"]
        keys = redis_cache.keys("cbsc:test:*")
        self.assertEqual(len(keys), 2)
        self.assertIn("cbsc:test:key1", keys)


class TestCacheManager(unittest.TestCase):
    """测试缓存管理器"""

    def setUp(self):
        """设置测试环境"""
        # Mock Redis
        self.redis_patcher = patch('services.cache_manager.REDIS_AVAILABLE', True)
        self.redis_patcher.start()

    def tearDown(self):
        """清理测试环境"""
        self.redis_patcher.stop()

    def test_cache_manager_creation(self):
        """测试缓存管理器创建"""
        cache_manager = CacheManager(enable_redis=False)
        self.assertIsNotNone(cache_manager)
        self.assertFalse(cache_manager.enable_redis)

    def test_cache_strategy_registration(self):
        """测试策略注册"""
        cache_manager = CacheManager(enable_redis=False)

        custom_strategy = CacheStrategy(
            name="custom",
            ttl_seconds=600,
            cache_level=CacheLevel.L1_ONLY,
            max_memory_items=500
        )

        # 注册策略
        self.assertTrue(cache_manager.register_strategy(custom_strategy))
        self.assertEqual(cache_manager.get_strategy("custom"), custom_strategy)

        # 无效策略
        invalid_strategy = CacheStrategy(
            name="invalid",
            ttl_seconds=-1,
            cache_level=CacheLevel.L1_ONLY
        )
        self.assertFalse(cache_manager.register_strategy(invalid_strategy))

    def test_cache_operations_l1_only(self):
        """测试L1缓存操作"""
        cache_manager = CacheManager(enable_redis=False)

        # 获取预定义策略
        performance_strategy = cache_manager.get_strategy("performance")
        self.assertIsNotNone(performance_strategy)
        self.assertEqual(performance_strategy.cache_level, CacheLevel.L1_ONLY)

        # 设置值
        test_value = {"test": "data"}
        self.assertTrue(cache_manager.set("performance", "test_key", test_value))

        # 获取值
        retrieved = cache_manager.get("performance", "test_key")
        self.assertEqual(retrieved, test_value)

        # 检查存在
        self.assertTrue(cache_manager.exists("performance", "test_key"))

        # 删除值
        self.assertTrue(cache_manager.delete("performance", "test_key"))
        self.assertFalse(cache_manager.exists("performance", "test_key"))

    def test_cache_operations_with_custom_ttl(self):
        """测试自定义TTL"""
        cache_manager = CacheManager(enable_redis=False)

        test_value = "test_value"
        custom_ttl = 60

        # 设置自定义TTL
        self.assertTrue(cache_manager.set("user", "ttl_test", test_value, ttl=custom_ttl))
        self.assertEqual(cache_manager.get("user", "ttl_test"), test_value)

    def test_cache_pattern_clearing(self):
        """测试模式清理"""
        cache_manager = CacheManager(enable_redis=False)

        # 设置多个键
        cache_manager.set("user", "test:1", "value1")
        cache_manager.set("user", "test:2", "value2")
        cache_manager.set("user", "other:1", "value3")

        # 清理匹配模式
        deleted = cache_manager.clear_pattern("user", "test:*")
        self.assertGreaterEqual(deleted, 0)

        # 检查结果
        self.assertIsNone(cache_manager.get("user", "test:1"))
        self.assertIsNone(cache_manager.get("user", "test:2"))
        # other:1 应该还在
        self.assertEqual(cache_manager.get("user", "other:1"), "value3")

    def test_cache_metrics(self):
        """测试缓存指标"""
        cache_manager = CacheManager(enable_redis=False)

        # 执行一些操作
        cache_manager.set("user", "metrics_test", "value")
        cache_manager.get("user", "metrics_test")  # hit
        cache_manager.get("user", "nonexistent")  # miss

        # 获取指标
        metrics = cache_manager.get_metrics("user")
        self.assertIsInstance(metrics, CacheMetrics)
        self.assertGreater(metrics.sets, 0)
        self.assertGreater(metrics.hits, 0)
        self.assertGreater(metrics.misses, 0)

        # 重置指标
        cache_manager.reset_metrics("user")
        metrics_after_reset = cache_manager.get_metrics("user")
        self.assertEqual(metrics_after_reset.hits, 0)
        self.assertEqual(metrics_after_reset.misses, 0)

    def test_cache_info(self):
        """测试缓存信息"""
        cache_manager = CacheManager(enable_redis=False)

        info = cache_manager.get_cache_info()
        self.assertIsInstance(info, dict)
        self.assertIn("redis_enabled", info)
        self.assertIn("memory_caches", info)
        self.assertIn("strategies_count", info)
        self.assertIn("total_metrics", info)

        self.assertFalse(info["redis_enabled"])
        self.assertGreaterEqual(info["strategies_count"], 0)

    def test_cache_warm_up(self):
        """测试缓存预热"""
        cache_manager = CacheManager(enable_redis=False)

        def data_loader(keys):
            return {key: f"value_for_{key}" for key in keys}

        keys_to_warm = ["key1", "key2", "key3"]
        success_count = cache_manager.warm_up("user", data_loader, keys_to_warm)

        self.assertEqual(success_count, len(keys_to_warm))

        # 验证预热的数据
        for key in keys_to_warm:
            value = cache_manager.get("user", key)
            self.assertEqual(value, f"value_for_{key}")

    def test_cache_compression(self):
        """测试缓存压缩"""
        cache_manager = CacheManager(enable_redis=False)

        # 获取支持压缩的L1策略
        user_strategy = cache_manager.get_strategy("user")
        self.assertTrue(user_strategy.enable_compression)
        self.assertEqual(user_strategy.cache_level, CacheLevel.L1_L2)

        # 创建较大的数据
        large_data = "x" * 2000  # 超过默认压缩阈值

        # 设置数据
        self.assertTrue(cache_manager.set("user", "large_data", large_data))

        # 获取数据
        retrieved = cache_manager.get("user", "large_data")
        self.assertEqual(retrieved, large_data)

    def test_unknown_strategy(self):
        """测试未知策略"""
        cache_manager = CacheManager(enable_redis=False)

        # 未知策略应该返回默认值
        self.assertIsNone(cache_manager.get("unknown_strategy", "key"))
        self.assertFalse(cache_manager.set("unknown_strategy", "key", "value"))
        self.assertFalse(cache_manager.delete("unknown_strategy", "key"))
        self.assertFalse(cache_manager.exists("unknown_strategy", "key"))

    def test_cache_shutdown(self):
        """测试缓存关闭"""
        cache_manager = CacheManager(enable_redis=False)

        # 设置一些数据
        cache_manager.set("user", "shutdown_test", "value")

        # 关闭
        cache_manager.shutdown()

        # 验证清理完成
        self.assertFalse(cache_manager._running)


class TestCacheManagerIntegration(unittest.TestCase):
    """缓存管理器集成测试"""

    @patch('services.cache_manager.redis')
    def test_with_redis_mock(self, mock_redis):
        """测试与Redis模拟器的集成"""
        # Mock Redis client
        mock_client = Mock()
        mock_redis.Redis.return_value = mock_client
        mock_redis.ConnectionPool.return_value = Mock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = None
        mock_client.setex.return_value = True
        mock_client.delete.return_value = 0
        mock_client.exists.return_value = 0

        # 创建启用Redis的缓存管理器
        cache_manager = CacheManager(enable_redis=True)

        # 测试L2缓存策略
        strategy = cache_manager.get_strategy("strategy")
        self.assertEqual(strategy.cache_level, CacheLevel.L2_ONLY)

        # 测试操作
        test_value = {"test": "integration"}
        self.assertTrue(cache_manager.set("strategy", "integration_key", test_value))

        # 模拟Redis返回值
        mock_client.get.return_value = pickle.dumps(test_value)
        retrieved = cache_manager.get("strategy", "integration_key")
        self.assertEqual(retrieved, test_value)

    def test_performance_requirements(self):
        """测试性能要求（延迟<5ms）"""
        cache_manager = CacheManager(enable_redis=False)
        test_data = {"performance": "test"}

        # 测试设置延迟
        start_time = time.time()
        cache_manager.set("performance", "perf_key", test_data)
        set_time = (time.time() - start_time) * 1000  # 转换为毫秒

        # 测试获取延迟
        start_time = time.time()
        cache_manager.get("performance", "perf_key")
        get_time = (time.time() - start_time) * 1000

        # 验证延迟要求
        self.assertLess(set_time, 5.0, f"Set operation took {set_time:.2f}ms, should be < 5ms")
        self.assertLess(get_time, 5.0, f"Get operation took {get_time:.2f}ms, should be < 5ms")

    def test_concurrent_access(self):
        """测试并发访问"""
        cache_manager = CacheManager(enable_redis=False)
        results = []
        errors = []

        def worker(worker_id):
            try:
                for i in range(100):
                    key = f"worker_{worker_id}_key_{i}"
                    value = f"worker_{worker_id}_value_{i}"

                    # 设置
                    cache_manager.set("performance", key, value)

                    # 获取
                    retrieved = cache_manager.get("performance", key)
                    if retrieved != value:
                        errors.append(f"Worker {worker_id}: Expected {value}, got {retrieved}")

                    results.append(f"Worker {worker_id} completed iteration {i}")
            except Exception as e:
                errors.append(f"Worker {worker_id} error: {e}")

        # 创建多个线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 500, f"Expected 500 operations, got {len(results)}")

    def test_redis_fallback(self):
        """测试Redis降级到内存缓存"""
        # 模拟Redis不可用
        with patch('services.cache_manager.REDIS_AVAILABLE', False):
            cache_manager = CacheManager(enable_redis=True)
            self.assertFalse(cache_manager.enable_redis)

            # 应该仍然可以使用内存缓存
            test_value = {"fallback": "test"}
            self.assertTrue(cache_manager.set("user", "fallback_key", test_value))
            retrieved = cache_manager.get("user", "fallback_key")
            self.assertEqual(retrieved, test_value)


if __name__ == '__main__':
    # 运行所有测试
    unittest.main(verbosity=2)
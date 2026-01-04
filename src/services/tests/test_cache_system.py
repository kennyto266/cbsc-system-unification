"""
缓存系统测试
Cache System Tests

测试新的统一缓存系统的各项功能。
"""

import unittest
import time
from unittest.mock import Mock, patch

from ..cache_manager import CacheManager, MemoryCache, get_cache_manager
from ..cache_strategy import CacheStrategy, CacheLevel, CacheStrategies, EvictionPolicy
from ..cache_decorators import cached, cache_on_arguments
from ..cache_integration import StrategyManagerCacheMixin, cached_method
from ..cache_monitoring import CacheMetricsCollector, CacheHealthChecker


class TestMemoryCache(unittest.TestCase):
    """测试内存缓存"""

    def setUp(self):
        self.cache = MemoryCache(max_size=10, ttl=1)

    def test_set_and_get(self):
        """测试设置和获取"""
        self.cache.set("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")

    def test_get_nonexistent(self):
        """测试获取不存在的键"""
        self.assertIsNone(self.cache.get("nonexistent"))

    def test_ttl_expiration(self):
        """测试TTL过期"""
        self.cache.set("key1", "value1", ttl=0.1)
        time.sleep(0.2)
        self.assertIsNone(self.cache.get("key1"))

    def test_lru_eviction(self):
        """测试LRU淘汰"""
        # 填满缓存
        for i in range(10):
            self.cache.set(f"key{i}", f"value{i}")

        # 访问第一个键
        self.cache.get("key0")

        # 添加新键，应该淘汰最久未使用的
        self.cache.set("key10", "value10")

        # key0应该还在（因为被访问过）
        self.assertIsNotNone(self.cache.get("key0"))
        # key1应该被淘汰
        self.assertIsNone(self.cache.get("key1"))


class TestCacheManager(unittest.TestCase):
    """测试缓存管理器"""

    def setUp(self):
        # 使用内存缓存的配置
        self.manager = CacheManager(enable_redis=False)

    def tearDown(self):
        self.manager.shutdown()

    def test_basic_operations(self):
        """测试基础操作"""
        # 测试设置和获取
        self.assertTrue(self.manager.set("strategy", "key1", "value1"))
        self.assertEqual(self.manager.get("strategy", "key1"), "value1")

        # 测试存在性检查
        self.assertTrue(self.manager.exists("strategy", "key1"))

        # 测试删除
        self.assertTrue(self.manager.delete("strategy", "key1"))
        self.assertIsNone(self.manager.get("strategy", "key1"))

    def test_strategy_configuration(self):
        """测试策略配置"""
        strategy = CacheStrategies.get_strategy("strategy")
        self.assertIsNotNone(strategy)
        self.assertEqual(strategy.cache_level, CacheLevel.L2_ONLY)
        self.assertEqual(strategy.ttl_seconds, 300)

    def test_pattern_clear(self):
        """测试模式清理"""
        # 设置多个键
        self.manager.set("user", "user_1_data", "data1")
        self.manager.set("user", "user_2_data", "data2")
        self.manager.set("strategy", "strategy_data", "data3")

        # 清理用户数据
        deleted = self.manager.clear_pattern("user", "user_*")
        self.assertEqual(deleted, 2)

        # 验证清理结果
        self.assertIsNone(self.manager.get("user", "user_1_data"))
        self.assertIsNone(self.manager.get("user", "user_2_data"))
        self.assertIsNotNone(self.manager.get("strategy", "strategy_data"))

    def test_metrics(self):
        """测试指标统计"""
        # 执行一些操作
        self.manager.set("strategy", "key1", "value1")
        self.manager.get("strategy", "key1")  # hit
        self.manager.get("strategy", "key2")  # miss

        metrics = self.manager.get_metrics("strategy")
        self.assertEqual(metrics.hits, 1)
        self.assertEqual(metrics.misses, 1)
        self.assertEqual(metrics.sets, 1)


class TestCacheDecorators(unittest.TestCase):
    """测试缓存装饰器"""

    def setUp(self):
        # 清除全局缓存管理器
        import importlib
        import sys
        if 'src.services.cache_manager' in sys.modules:
            importlib.reload(sys.modules['src.services.cache_manager'])

    def test_cached_decorator(self):
        """测试缓存装饰器"""
        call_count = 0

        @cached("test", ttl=1)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # 第一次调用
        result1 = expensive_function(5)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count, 1)

        # 第二次调用应该使用缓存
        result2 = expensive_function(5)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count, 1)  # 没有增加

        # 等待TTL过期
        time.sleep(1.1)
        result3 = expensive_function(5)
        self.assertEqual(result3, 10)
        self.assertEqual(call_count, 2)  # 重新执行

    def test_cache_on_arguments(self):
        """测试基于参数的缓存"""
        call_count = 0

        @cache_on_arguments("test", ttl=10)
        def process_data(data, param="default"):
            nonlocal call_count
            call_count += 1
            return f"{data}_{param}"

        # 不同的参数应该有独立的缓存
        result1 = process_data("test", param="a")
        result2 = process_data("test", param="b")
        self.assertEqual(result1, "test_a")
        self.assertEqual(result2, "test_b")
        self.assertEqual(call_count, 2)

        # 相同参数应该使用缓存
        result3 = process_data("test", param="a")
        self.assertEqual(result3, "test_a")
        self.assertEqual(call_count, 2)


class TestCacheIntegration(unittest.TestCase):
    """测试缓存集成"""

    def test_strategy_manager_mixin(self):
        """测试策略管理器混入"""
        class TestManager(StrategyManagerCacheMixin):
            pass

        manager = TestManager()
        self.assertTrue(hasattr(manager, 'get_strategy_cache'))
        self.assertTrue(hasattr(manager, 'set_strategy_cache'))
        self.assertTrue(hasattr(manager, 'invalidate_strategy_cache'))

        # 测试缓存操作
        self.assertIsNone(manager.get_strategy_cache("test_id"))
        self.assertTrue(manager.set_strategy_cache("test_id", {"test": "data"}))
        self.assertEqual(manager.get_strategy_cache("test_id"), {"test": "data"})

    def test_cached_method_decorator(self):
        """测试方法缓存装饰器"""
        call_count = 0

        class TestManager(StrategyManagerCacheMixin):
            @cached_method("test", ttl=10)
            def get_data(self, key):
                nonlocal call_count
                call_count += 1
                return f"data_{key}"

        manager = TestManager()

        # 第一次调用
        result1 = manager.get_data("test")
        self.assertEqual(result1, "data_test")
        self.assertEqual(call_count, 1)

        # 第二次调用应该使用缓存
        result2 = manager.get_data("test")
        self.assertEqual(result2, "data_test")
        self.assertEqual(call_count, 1)


class TestCacheMonitoring(unittest.TestCase):
    """测试缓存监控"""

    def test_metrics_collector(self):
        """测试指标收集器"""
        collector = CacheMetricsCollector(collection_interval=0.1, max_snapshots=10)

        # 模拟缓存快照
        from ..cache_monitoring import CacheSnapshot
        snapshot = CacheSnapshot(
            timestamp=time.time(),
            strategy_name="test",
            hits=100,
            misses=20,
            sets=80,
            deletes=10,
            memory_size=1000,
            hit_rate=0.83
        )

        # 测试快照存储
        collector.snapshots["test"].append(snapshot)
        snapshots = collector.get_recent_snapshots("test", minutes=1)
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].hits, 100)

        # 测试聚合统计
        agg_stats = collector.get_aggregated_stats("test", hours=1)
        self.assertEqual(agg_stats["total_hits"], 100)
        self.assertEqual(agg_stats["total_misses"], 20)

        collector.stop()

    def test_health_checker(self):
        """测试健康检查器"""
        checker = CacheHealthChecker()
        alerts_received = []

        def alert_callback(check_name, check_result):
            alerts_received.append((check_name, check_result))

        checker.add_alert_callback(alert_callback)

        # 添加一个总是失败的健康检查
        def failing_check():
            return {
                "healthy": False,
                "severity": "warning",
                "message": "Test failure"
            }

        checker.add_health_check(failing_check)

        # 执行健康检查
        health_status = checker.check_health()

        self.assertEqual(health_status["overall_status"], "unhealthy")
        self.assertEqual(len(health_status["alerts"]), 1)
        self.assertEqual(len(alerts_received), 1)


class TestCacheStrategies(unittest.TestCase):
    """测试缓存策略"""

    def test_predefined_strategies(self):
        """测试预定义策略"""
        strategies = CacheStrategies.all_strategies()

        # 验证所有策略都存在
        expected_strategies = [
            "strategy", "performance", "user", "config",
            "market_data", "session", "realtime_signals", "api_stats"
        ]

        for name in expected_strategies:
            self.assertIn(name, strategies)
            strategy = strategies[name]
            self.assertIsNotNone(strategy)
            self.assertTrue(strategy.ttl_seconds > 0)

    def test_strategy_validation(self):
        """测试策略验证"""
        # 有效策略
        valid_strategy = CacheStrategy(
            name="valid",
            ttl_seconds=300,
            cache_level=CacheLevel.L1_L2,
            max_memory_items=100
        )
        self.assertTrue(CacheStrategies.validate_strategy(valid_strategy))

        # 无效策略（TTL为0）
        invalid_strategy = CacheStrategy(
            name="invalid",
            ttl_seconds=0,
            cache_level=CacheLevel.L1_L2
        )
        self.assertFalse(CacheStrategies.validate_strategy(invalid_strategy))

        # 无效策略（L1缓存没有最大条目数）
        invalid_strategy2 = CacheStrategy(
            name="invalid2",
            ttl_seconds=300,
            cache_level=CacheLevel.L1_ONLY
        )
        self.assertFalse(CacheStrategies.validate_strategy(invalid_strategy2))


if __name__ == "__main__":
    # 运行所有测试
    unittest.main(verbosity=2)
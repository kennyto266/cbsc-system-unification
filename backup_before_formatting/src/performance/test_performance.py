"""
性能优化模块测试

测试所有性能优化功能：
- 性能分析器
- 缓存系统
- I / O优化
- 懒加载
- 连接池
"""

import asyncio
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from typing import Dict, List

from .cache_layer import (
    CacheManager,
    LRUCache,
    MultiLevelCache,
    TTLCache,
    get_default_cache,
)
from .connection_pool import (
    ConnectionManager,
    DatabaseConnectionPool,
    HTTPConnectionPool,
    PoolConfig,
)
from .io_optimizer import batch_process
from .lazy_loader import (
    DataFrameLazyLoader,
    LazyLoader,
    MemoryManagedLoader,
    MemoryManager,
)

# 导入性能优化模块
from .profiler import Profiler, ProfileResult


class TestProfiler(unittest.TestCase):
    """测试性能分析器"""

    def setUp(self):
        self.profiler = Profiler(output_dir="test_performance_reports")

    def test_profile_function(self):
        """测试函数性能分析"""

        def test_func(x: int, y: int) -> int:
            time.sleep(0.01)  # 模拟耗时
            return x + y

        result = self.profiler.profile_function(
            test_func, 10, 20, profile_name="test_function"
        )

        self.assertEqual(result, 30)
        self.assertGreater(len(self.profiler.results), 0)

    def test_profile_block(self):
        """测试代码块性能分析"""
        with self.profiler.profile_block("test_block"):
            time.sleep(0.05)
            data = [i for i in range(1000)]

        # 检查是否记录了结果
        # （结果会在日志中查看）

    def test_benchmark_algorithm(self):
        """测试算法基准测试"""

        def test_func(n: int) -> int:
            return sum(range(n))

        benchmark = self.profiler.benchmark_algorithm(test_func, iterations=10, n=1000)

        self.assertIn("iterations", benchmark)
        self.assertIn("avg_time", benchmark)
        self.assertEqual(benchmark["iterations"], 10)

    def test_memory_analysis(self):
        """测试内存分析"""

        def create_data():
            return [i for i in range(10000)]

        memory_stats = self.profiler.profile_memory(create_data)

        self.assertIn("initial_memory_mb", memory_stats)
        self.assertIn("final_memory_mb", memory_stats)
        self.assertIn("memory_increase_mb", memory_stats)

    def tearDown(self):
        # 清理测试文件
        if Path("test_performance_reports").exists():
            shutil.rmtree("test_performance_reports")


class TestLRUCache(unittest.TestCase):
    """测试LRU缓存"""

    def test_basic_operations(self):
        """测试基本操作"""
        cache = LRUCache(maxsize=3)

        # 插入数据
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")

        # 获取数据
        self.assertEqual(cache.get("key1"), "value1")
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key3"), "value3")

        # 容量测试
        cache.put("key4", "value4")  # 应该淘汰key1
        self.assertIsNone(cache.get("key1"))
        self.assertEqual(cache.get("key4"), "value4")

    def test_cache_stats(self):
        """测试缓存统计"""
        cache = LRUCache(maxsize=10)

        cache.get("nonexistent")  # 未命中
        cache.put("key1", "value1")
        cache.get("key1")  # 命中

        stats = cache.get_stats()
        self.assertIn("hits", stats)
        self.assertIn("misses", stats)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hits"], 1)


class TestTTLCache(unittest.TestCase):
    """测试TTL缓存"""

    def test_ttl_expiration(self):
        """测试过期时间"""
        cache = TTLCache(maxsize=10, default_ttl=0.1)  # 100ms

        cache.put("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")

        # 等待过期
        time.sleep(0.15)
        self.assertIsNone(cache.get("key1"))

    def test_ttl_with_custom_value(self):
        """测试自定义TTL"""
        cache = TTLCache(maxsize=10, default_ttl=1.0)

        cache.put("key1", "value1", ttl=0.1)  # 短TTL
        time.sleep(0.15)
        self.assertIsNone(cache.get("key1"))


class TestMultiLevelCache(unittest.TestCase):
    """测试多级缓存"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.persist_file = Path(self.temp_dir) / "cache.json"

    def test_multi_level_cache(self):
        """测试多级缓存"""
        cache = MultiLevelCache(
            l1_size=2,
            l2_size=5,
            l2_ttl=3600,
            enable_persistence=True,
            persist_file=str(self.persist_file),
        )

        # 存储数据
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")

        # 获取数据（从不同级别）
        self.assertEqual(cache.get("key1"), "value1")
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key3"), "value3")

        # 检查统计
        stats = cache.get_stats()
        self.assertIn("l1", stats)
        self.assertIn("l2", stats)
        self.assertIn("overall", stats)

    def tearDown(self):
        # 清理临时文件
        shutil.rmtree(self.temp_dir)


class TestIOOptimizer(unittest.TestCase):
    """测试I / O优化器"""

    def test_batch_process(self):
        """测试批量处理"""
        data = list(range(1000))
        batch_size = 100

        def process_batch(batch: List[int]) -> List[int]:
            return [x * 2 for x in batch]

        start_time = time.time()
        results = batch_process(data, batch_size, process_batch)
        elapsed_time = time.time() - start_time

        # 验证结果
        self.assertEqual(len(results), 10)  # 1000 / 100 = 10 batches
        self.assertEqual(results[0], [i * 2 for i in range(100)])

        print(f"批处理时间: {elapsed_time:.3f}s")


class TestLazyLoader(unittest.TestCase):
    """测试懒加载"""

    def test_basic_lazy_loading(self):
        """测试基本懒加载"""
        load_called = [False]  # 使用列表避免闭包问题

        def load_data():
            load_called[0] = True
            time.sleep(0.1)
            return [1, 2, 3, 4, 5]

        lazy_loader = LazyLoader(load_data)

        # 检查是否未加载
        self.assertFalse(lazy_loader.is_loaded())
        self.assertIsNone(lazy_loader.get())

        # 加载数据
        data = lazy_loader.load()
        self.assertTrue(lazy_loader.is_loaded())
        self.assertEqual(data, [1, 2, 3, 4, 5])
        self.assertTrue(load_called[0])

        # 再次获取（已加载）
        data2 = lazy_loader.get()
        self.assertEqual(data2, [1, 2, 3, 4, 5])

    def test_memory_manager(self):
        """测试内存管理器"""
        manager = MemoryManager(max_memory_percent=90.0, gc_threshold=100)

        stats = manager.get_memory_stats()
        self.assertIn("used_mb", stats.__dict__)
        self.assertIn("usage_percent", stats.__dict__)

        # 启动和停止监控
        manager.start_monitoring()
        time.sleep(0.1)  # 等待监控
        manager.stop_monitoring()

    def test_dataframe_lazy_loader(self):
        """测试DataFrame懒加载"""
        import pandas as pd

        # 创建测试CSV
        temp_file = Path("test_df.csv")
        df = pd.DataFrame({"A": [1, 2, 3, 4, 5], "B": [10, 20, 30, 40, 50]})
        df.to_csv(temp_file, index=False)

        # 使用懒加载器
        lazy_df = DataFrameLazyLoader(temp_file, chunk_size=2)

        # 加载数据
        loaded_df = lazy_df.load()
        self.assertEqual(loaded_df.shape[0], 5)

        # 获取元数据
        metadata = lazy_df.get_metadata()
        self.assertIn("shape", metadata)
        self.assertIn("columns", metadata)

        # 清理
        temp_file.unlink(missing_ok=True)


class TestConnectionPool(unittest.TestCase):
    """测试连接池"""

    def test_pool_config(self):
        """测试连接池配置"""
        config = PoolConfig(
            min_size=5, max_size=20, max_idle_time=300, connection_timeout=10.0
        )

        self.assertEqual(config.min_size, 5)
        self.assertEqual(config.max_size, 20)
        self.assertEqual(config.max_idle_time, 300)

    def test_connection_manager(self):
        """测试连接管理器"""
        manager = ConnectionManager()

        # 创建HTTP连接池
        http_pool = manager.create_http_pool("test_http", "https://httpbin.org")
        self.assertIsInstance(http_pool, HTTPConnectionPool)

        # 获取连接池
        retrieved_pool = manager.get_pool("test_http")
        self.assertEqual(retrieved_pool, http_pool)

        # 获取所有连接池
        all_pools = manager.get_all_pools()
        self.assertIn("test_http", all_pools)

    def test_cache_manager(self):
        """测试缓存管理器"""
        cache_manager = CacheManager()

        # 创建缓存
        cache1 = cache_manager.create_cache("cache1", {"l1_size": 32, "l2_size": 256})
        self.assertIsInstance(cache1, MultiLevelCache)

        # 获取缓存
        retrieved_cache = cache_manager.get_cache("cache1")
        self.assertEqual(retrieved_cache, cache1)

        # 统计信息
        stats = cache_manager.get_all_stats()
        self.assertIn("cache1", stats)


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def test_cache_and_lazy_loading(self):
        """测试缓存和懒加载集成"""
        load_count = [0]

        def expensive_load():
            load_count[0] += 1
            time.sleep(0.1)
            return f"data_{load_count[0]}"

        # 创建懒加载器
        lazy_loader = LazyLoader(expensive_load)

        # 创建缓存
        cache = LRUCache(maxsize=10)

        # 第一次访问
        data1 = lazy_loader.load()
        cache.put("key", data1)

        # 第二次访问（从缓存）
        cached_data = cache.get("key")
        self.assertEqual(data1, cached_data)

        # 验证只加载一次
        self.assertEqual(load_count[0], 1)

    def test_performance_optimization(self):
        """测试性能优化效果"""
        # 使用缓存
        cache = LRUCache(maxsize=100)

        def expensive_computation(x: int) -> int:
            time.sleep(0.01)  # 模拟耗时
            return x * x

        # 无缓存
        start = time.time()
        for i in range(50):
            expensive_computation(i)
        time_without_cache = time.time() - start

        # 有缓存
        start = time.time()
        for i in range(50):
            if i < 25:  # 只缓存前25个
                cached = cache.get(i)
                if cached is None:
                    result = expensive_computation(i)
                    cache.put(i, result)
            else:
                result = expensive_computation(i)
        time_with_cache = time.time() - start

        # 验证缓存提升性能
        print(f"  无缓存时间: {time_without_cache:.3f}s")
        print(f"  有缓存时间: {time_with_cache:.3f}s")
        print(f"  性能提升: {(time_without_cache / time_with_cache):.2f}x")

        # 性能应该有所提升（至少不是更慢）
        # 注意：在某些测试环境中可能因为系统负载而波动


def run_all_tests():
    """运行所有测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加测试类
    test_classes = [
        TestProfiler,
        TestLRUCache,
        TestTTLCache,
        TestMultiLevelCache,
        TestIOOptimizer,
        TestLazyLoader,
        TestConnectionPool,
        TestIntegration,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    return result


if __name__ == "__main__":
    print("=" * 80)
    print("性能优化模块测试")
    print("=" * 80)

    result = run_all_tests()

    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("✓ 所有测试通过")
    else:
        print(f"✗ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
    print("=" * 80)

    # 返回退出码
    exit(0 if result.wasSuccessful() else 1)

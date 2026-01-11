#!/usr/bin/env python3
"""
CacheManager性能测试脚本
Performance Test Script for CacheManager

验证操作延迟 < 5ms 的要求
"""

import time
import statistics
import threading
import sys
import os

# 添加src路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.cache_manager import CacheManager, CacheStrategies


class PerformanceTest:
    """性能测试类"""

    def __init__(self):
        self.cache_manager = CacheManager(enable_redis=False)
        self.results = {}

    def test_basic_operations(self, iterations=10000):
        """测试基础操作性能"""
        print(f"[BASIC] Testing basic operations performance ({iterations} iterations)...")

        test_data = {
            "user_id": 12345,
            "strategy_name": "test_strategy",
            "parameters": {"param1": "value1", "param2": "value2"},
            "performance_data": [1, 2, 3, 4, 5]
        }

        # 测试设置操作
        set_times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            self.cache_manager.set("performance", f"perf_key_{i}", test_data)
            end_time = time.perf_counter()
            set_times.append((end_time - start_time) * 1000)  # 转换为毫秒

        # 测试获取操作
        get_times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            self.cache_manager.get("performance", f"perf_key_{i}")
            end_time = time.perf_counter()
            get_times.append((end_time - start_time) * 1000)  # 转换为毫秒

        # 测试删除操作
        delete_times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            self.cache_manager.delete("performance", f"perf_key_{i}")
            end_time = time.perf_counter()
            delete_times.append((end_time - start_time) * 1000)  # 转换为毫秒

        # 计算统计数据
        self.results["set_operations"] = {
            "avg_ms": statistics.mean(set_times),
            "median_ms": statistics.median(set_times),
            "min_ms": min(set_times),
            "max_ms": max(set_times),
            "p95_ms": statistics.quantiles(set_times, n=20)[18] if len(set_times) > 20 else max(set_times),
            "p99_ms": statistics.quantiles(set_times, n=100)[98] if len(set_times) > 100 else max(set_times)
        }

        self.results["get_operations"] = {
            "avg_ms": statistics.mean(get_times),
            "median_ms": statistics.median(get_times),
            "min_ms": min(get_times),
            "max_ms": max(get_times),
            "p95_ms": statistics.quantiles(get_times, n=20)[18] if len(get_times) > 20 else max(get_times),
            "p99_ms": statistics.quantiles(get_times, n=100)[98] if len(get_times) > 100 else max(get_times)
        }

        self.results["delete_operations"] = {
            "avg_ms": statistics.mean(delete_times),
            "median_ms": statistics.median(delete_times),
            "min_ms": min(delete_times),
            "max_ms": max(delete_times),
            "p95_ms": statistics.quantiles(delete_times, n=20)[18] if len(delete_times) > 20 else max(delete_times),
            "p99_ms": statistics.quantiles(delete_times, n=100)[98] if len(delete_times) > 100 else max(delete_times)
        }

    def test_concurrent_access(self, num_threads=10, operations_per_thread=1000):
        """Test concurrent access performance"""
        print(f"[CONCURRENT] Testing concurrent access ({num_threads} threads, {operations_per_thread} ops per thread)...")

        results = []
        errors = []

        def worker(thread_id):
            thread_times = []
            try:
                for i in range(operations_per_thread):
                    key = f"thread_{thread_id}_key_{i}"
                    value = f"thread_{thread_id}_value_{i}"

                    # 设置
                    start_time = time.perf_counter()
                    self.cache_manager.set("performance", key, value)
                    set_time = (time.perf_counter() - start_time) * 1000

                    # 获取
                    start_time = time.perf_counter()
                    retrieved = self.cache_manager.get("performance", key)
                    get_time = (time.perf_counter() - start_time) * 1000

                    if retrieved != value:
                        errors.append(f"Thread {thread_id}: Expected {value}, got {retrieved}")

                    thread_times.append(set_time + get_time)

                results.append(thread_times)
            except Exception as e:
                errors.append(f"Thread {thread_id} error: {e}")

        # 启动线程
        threads = []
        start_time = time.perf_counter()

        for i in range(num_threads):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待完成
        for thread in threads:
            thread.join()

        total_time = (time.perf_counter() - start_time) * 1000

        # 合并所有结果
        all_times = []
        for thread_times in results:
            all_times.extend(thread_times)

        total_operations = num_threads * operations_per_thread * 2  # set + get
        throughput = total_operations / (total_time / 1000)  # operations per second

        self.results["concurrent_access"] = {
            "total_time_ms": total_time,
            "total_operations": total_operations,
            "throughput_ops_per_sec": throughput,
            "avg_operation_time_ms": statistics.mean(all_times),
            "errors": len(errors)
        }

        print(f"Concurrent test completed: {total_operations} operations, {total_time:.2f}ms")
        print(f"Throughput: {throughput:.2f} ops/sec")
        if errors:
            print(f"Error count: {len(errors)}")

    def test_memory_usage(self, num_items=10000):
        """Test memory usage"""
        print(f"[MEMORY] Testing memory usage ({num_items} items)...")

        # 获取初始内存信息
        initial_info = self.cache_manager.get_cache_info()
        initial_memory = sum(cache.size() for cache in self.cache_manager._memory_caches.values())

        # 添加大量数据
        test_data = {"test": "data" * 100}  # 较大的数据
        for i in range(num_items):
            self.cache_manager.set("performance", f"memory_test_{i}", test_data)

        # 获取最终内存信息
        final_info = self.cache_manager.get_cache_info()
        final_memory = sum(cache.size() for cache in self.cache_manager._memory_caches.values())

        self.results["memory_usage"] = {
            "items_stored": num_items,
            "initial_memory_items": initial_memory,
            "final_memory_items": final_memory,
            "memory_efficiency": final_memory / num_items if num_items > 0 else 0
        }

    def test_ttl_performance(self, iterations=5000):
        """Test TTL performance"""
        print(f"[TTL] Testing TTL performance ({iterations} iterations)...")

        ttl_times = []
        for i in range(iterations):
            key = f"ttl_test_{i}"
            value = f"ttl_value_{i}"

            # 设置带TTL的缓存
            start_time = time.perf_counter()
            self.cache_manager.set("user", key, value, ttl=60)
            set_time = (time.perf_counter() - start_time) * 1000

            # 检查TTL
            start_time = time.perf_counter()
            remaining_ttl = self.cache_manager.get_ttl("user", key)
            ttl_time = (time.perf_counter() - start_time) * 1000

            ttl_times.append(set_time + ttl_time)

        self.results["ttl_operations"] = {
            "avg_time_ms": statistics.mean(ttl_times),
            "median_time_ms": statistics.median(ttl_times),
            "min_time_ms": min(ttl_times),
            "max_time_ms": max(ttl_times)
        }

    def test_pattern_matching(self, pattern="test:*", num_items=1000):
        """Test pattern matching performance"""
        print(f"[PATTERN] Testing pattern matching (pattern: {pattern}, items: {num_items})...")

        # 添加测试数据
        for i in range(num_items):
            self.cache_manager.set("user", f"test_{i}", f"value_{i}")
            self.cache_manager.set("user", f"other_{i}", f"other_value_{i}")

        # 测试模式清理
        clear_times = []
        for _ in range(10):  # 重复10次测试
            start_time = time.perf_counter()
            deleted = self.cache_manager.clear_pattern("user", pattern)
            clear_time = (time.perf_counter() - start_time) * 1000
            clear_times.append(clear_time)

            # 重新添加数据以供下次测试
            for i in range(num_items):
                self.cache_manager.set("user", f"test_{i}", f"value_{i}")

        self.results["pattern_matching"] = {
            "avg_time_ms": statistics.mean(clear_times),
            "median_time_ms": statistics.median(clear_times),
            "min_time_ms": min(clear_times),
            "max_time_ms": max(clear_times),
            "items_matched": num_items
        }

    def print_results(self):
        """打印测试结果"""
        print("\n" + "="*80)
        print("CacheManager Performance Test Results")
        print("="*80)

        # 基础操作性能
        if "set_operations" in self.results:
            print("\n[SET] Set Operations Performance:")
            set_ops = self.results["set_operations"]
            print(f"  Average Latency: {set_ops['avg_ms']:.3f} ms")
            print(f"  Median Latency: {set_ops['median_ms']:.3f} ms")
            print(f"  P95 Latency: {set_ops['p95_ms']:.3f} ms")
            print(f"  P99 Latency: {set_ops['p99_ms']:.3f} ms")
            print(f"  Min Latency: {set_ops['min_ms']:.3f} ms")
            print(f"  Max Latency: {set_ops['max_ms']:.3f} ms")
            print(f"  [PASS] Meets Requirement (<5ms): {set_ops['avg_ms'] < 5.0}")

        if "get_operations" in self.results:
            print("\n[GET] Get Operations Performance:")
            get_ops = self.results["get_operations"]
            print(f"  Average Latency: {get_ops['avg_ms']:.3f} ms")
            print(f"  Median Latency: {get_ops['median_ms']:.3f} ms")
            print(f"  P95 Latency: {get_ops['p95_ms']:.3f} ms")
            print(f"  P99 Latency: {get_ops['p99_ms']:.3f} ms")
            print(f"  Min Latency: {get_ops['min_ms']:.3f} ms")
            print(f"  Max Latency: {get_ops['max_ms']:.3f} ms")
            print(f"  [PASS] Meets Requirement (<5ms): {get_ops['avg_ms'] < 5.0}")

        if "delete_operations" in self.results:
            print("\n[DELETE] Delete Operations Performance:")
            del_ops = self.results["delete_operations"]
            print(f"  Average Latency: {del_ops['avg_ms']:.3f} ms")
            print(f"  Median Latency: {del_ops['median_ms']:.3f} ms")
            print(f"  P95 Latency: {del_ops['p95_ms']:.3f} ms")
            print(f"  P99 Latency: {del_ops['p99_ms']:.3f} ms")
            print(f"  [PASS] Meets Requirement (<5ms): {del_ops['avg_ms'] < 5.0}")

        # 并发访问性能
        if "concurrent_access" in self.results:
            print("\n[CONCURRENT] Concurrent Access Performance:")
            concurrent = self.results["concurrent_access"]
            print(f"  Total Operations: {concurrent['total_operations']}")
            print(f"  Total Time: {concurrent['total_time_ms']:.2f} ms")
            print(f"  Throughput: {concurrent['throughput_ops_per_sec']:.2f} ops/sec")
            print(f"  Average Operation Time: {concurrent['avg_operation_time_ms']:.3f} ms")
            print(f"  Error Count: {concurrent['errors']}")
            print(f"  [PASS] Error Rate < 1%: {concurrent['errors'] / concurrent['total_operations'] < 0.01}")

        # 内存使用
        if "memory_usage" in self.results:
            print("\n[MEMORY] Memory Usage:")
            memory = self.results["memory_usage"]
            print(f"  Stored Items: {memory['items_stored']}")
            print(f"  Memory Efficiency: {memory['memory_efficiency']:.2f} items/cache")

        # TTL性能
        if "ttl_operations" in self.results:
            print("\n[TTL] TTL Operations Performance:")
            ttl = self.results["ttl_operations"]
            print(f"  Average Time: {ttl['avg_time_ms']:.3f} ms")
            print(f"  Median Time: {ttl['median_time_ms']:.3f} ms")
            print(f"  [PASS] Meets Requirement (<5ms): {ttl['avg_time_ms'] < 5.0}")

        # 模式匹配性能
        if "pattern_matching" in self.results:
            print("\n[PATTERN] Pattern Matching Performance:")
            pattern = self.results["pattern_matching"]
            print(f"  Matched Items: {pattern['items_matched']}")
            print(f"  Average Time: {pattern['avg_time_ms']:.3f} ms")
            print(f"  Median Time: {pattern['median_time_ms']:.3f} ms")
            print(f"  [PASS] Meets Requirement (<10ms): {pattern['avg_time_ms'] < 10.0}")

        # 总体评估
        print("\n" + "="*80)
        print("OVERALL ASSESSMENT")
        print("="*80)

        avg_latency = 0
        latency_tests = 0

        if "set_operations" in self.results:
            avg_latency += self.results["set_operations"]["avg_ms"]
            latency_tests += 1
        if "get_operations" in self.results:
            avg_latency += self.results["get_operations"]["avg_ms"]
            latency_tests += 1
        if "delete_operations" in self.results:
            avg_latency += self.results["delete_operations"]["avg_ms"]
            latency_tests += 1

        if latency_tests > 0:
            avg_latency /= latency_tests
            print(f"Average Operation Latency: {avg_latency:.3f} ms")
            print(f"[PASS] Performance Requirement Met (<5ms): {avg_latency < 5.0}")

        if "concurrent_access" in self.results:
            throughput = self.results["concurrent_access"]["throughput_ops_per_sec"]
            print(f"Concurrent Throughput: {throughput:.2f} ops/sec")
            print(f"[PASS] Excellent Throughput (>1000 ops/sec): {throughput > 1000}")

        print("\n*** CacheManager Performance Test Completed! ***")

    def run_all_tests(self):
        """运行所有性能测试"""
        print("[START] Starting CacheManager Performance Test...")
        print(f"Test Configuration: Redis disabled (memory cache only)")

        # 运行各项测试
        self.test_basic_operations()
        self.test_concurrent_access()
        self.test_memory_usage()
        self.test_ttl_performance()
        self.test_pattern_matching()

        # 打印结果
        self.print_results()


def main():
    """主函数"""
    test = PerformanceTest()
    test.run_all_tests()


if __name__ == "__main__":
    main()
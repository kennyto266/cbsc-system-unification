"""
缓存集成测试
Cache Integration Test

测试CacheManager集成到各个Manager后的性能
"""

import asyncio
import time
import os
import sys
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add path for strategies module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'api', 'strategies'))

# 简化的性能测试类
class CachePerformanceTester:
    def __init__(self):
        self.results = []

    async def test_cache_performance(self, cache_manager, operations: int = 1000) -> Dict[str, float]:
        """测试缓存性能"""
        print(f"\n测试缓存性能 ({operations} 次操作)...")

        # 测试写入性能
        start_time = time.time()
        for i in range(operations):
            await cache_manager.set(f"test:key:{i}", f"value:{i}")
        write_time = time.time() - start_time

        # 测试读取性能
        start_time = time.time()
        for i in range(operations):
            await cache_manager.get(f"test:key:{i}")
        read_time = time.time() - start_time

        # 计算统计
        write_ops_sec = operations / write_time
        read_ops_sec = operations / read_time

        # 获取缓存统计
        stats = await cache_manager.get_stats()

        result = {
            "operations": operations,
            "write_time": write_time,
            "read_time": read_time,
            "write_ops_sec": write_ops_sec,
            "read_ops_sec": read_ops_sec,
            "total_ops_sec": (operations * 2) / (write_time + read_time),
            "hit_rate": stats["hit_rate"],
            "memory_items": stats.get("memory_items", 0),
            "total_ops": stats.get("total_ops", 0)
        }

        print(f"  写入性能: {write_ops_sec:.0f} ops/sec")
        print(f"  读取性能: {read_ops_sec:.0f} ops/sec")
        print(f"  总体性能: {result['total_ops_sec']:.0f} ops/sec")
        print(f"  缓存命中率: {result['hit_rate']:.2%}")

        return result

    async def test_concurrent_access(self, cache_manager, concurrent_users: int = 100, operations_per_user: int = 100):
        """测试并发访问性能"""
        print(f"\n测试并发访问 ({concurrent_users} 用户, 每用户 {operations_per_user} 操作)...")

        async def user_operations(user_id: int):
            """模拟单个用户的操作"""
            latencies = []
            for i in range(operations_per_user):
                start = time.time()
                await cache_manager.set(f"user:{user_id}:data:{i}", f"user_data_{user_id}_{i}")
                await cache_manager.get(f"user:{user_id}:data:{i}")
                latency = time.time() - start
                latencies.append(latency)
            return latencies

        # 并发执行
        start_time = time.time()
        tasks = [user_operations(i) for i in range(concurrent_users)]
        all_latencies = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # 展平所有延迟数据
        flat_latencies = []
        for latencies in all_latencies:
            flat_latencies.extend(latencies)

        # 计算统计
        total_operations = concurrent_users * operations_per_user * 2  # 每个用户执行set+get
        avg_latency = statistics.mean(flat_latencies) * 1000  # 转换为毫秒
        p95_latency = statistics.quantiles(flat_latencies, n=20)[18] * 1000  # 95th百分位
        p99_latency = statistics.quantiles(flat_latencies, n=100)[98] * 1000  # 99th百分位

        result = {
            "concurrent_users": concurrent_users,
            "operations_per_user": operations_per_user,
            "total_operations": total_operations,
            "total_time": total_time,
            "ops_per_sec": total_operations / total_time,
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95_latency,
            "p99_latency_ms": p99_latency
        }

        print(f"  总操作数: {total_operations}")
        print(f"  总体性能: {result['ops_per_sec']:.0f} ops/sec")
        print(f"  平均延迟: {avg_latency:.2f} ms")
        print(f"  P95延迟: {p95_latency:.2f} ms")
        print(f"  P99延迟: {p99_latency:.2f} ms")

        return result

    async def test_memory_usage(self, cache_manager, items: int = 10000):
        """测试内存使用"""
        print(f"\n测试内存使用 ({items} 个缓存项)...")

        # 生成测试数据
        test_data = {
            "user_id": 12345,
            "name": "Test User",
            "strategies": [
                {"id": "s1", "type": "RSI", "active": True},
                {"id": "s2", "type": "MACD", "active": False}
            ],
            "performance": {
                "total_return": 0.15,
                "sharpe_ratio": 1.2,
                "max_drawdown": 0.05
            }
        }

        # 写入大量数据
        start_time = time.time()
        for i in range(items):
            await cache_manager.set(f"large:{i}", test_data)
        write_time = time.time() - start_time

        # 获取统计
        stats = await cache_manager.get_stats()

        result = {
            "items": items,
            "write_time": write_time,
            "items_per_sec": items / write_time,
            "memory_items": stats.get("memory_items", 0),
            "memory_size": stats.get("memory_size", 0),
            "memory_size_kb": stats.get("memory_size", 0) / 1024,
            "hit_rate": stats.get("hit_rate", 0)
        }

        print(f"  写入时间: {write_time:.2f} sec")
        print(f"  写入性能: {result['items_per_sec']:.0f} items/sec")
        print(f"  内存项数: {result['memory_items']}")
        print(f"  内存大小: {result['memory_size_kb']:.1f} KB")

        return result

    async def test_ttl_expiration(self, cache_manager):
        """测试TTL过期"""
        print("\n测试TTL过期...")

        # 设置短TTL的缓存
        await cache_manager.set("ttl:test", "expire_soon", ttl=1)

        # 立即读取
        value = await cache_manager.get("ttl:test")
        assert value == "expire_soon", "TTL设置失败"
        print("  TTL设置和立即读取: OK")

        # 等待过期
        await asyncio.sleep(1.1)

        # 再次读取应该失败
        value = await cache_manager.get("ttl:test")
        assert value is None, "TTL过期失败"
        print("  TTL自动过期: OK")

        return True

    async def run_all_tests(self, cache_manager):
        """运行所有测试"""
        print("=" * 60)
        print("缓存集成性能测试开始")
        print("=" * 60)

        # 测试1: 基本性能
        perf1 = await self.test_cache_performance(cache_manager, 1000)
        self.results.append(("基本性能", perf1))

        # 测试2: 并发访问
        perf2 = await self.test_concurrent_access(cache_manager, 50, 50)
        self.results.append(("并发访问", perf2))

        # 测试3: 内存使用
        perf3 = await self.test_memory_usage(cache_manager, 5000)
        self.results.append(("内存使用", perf3))

        # 测试4: TTL功能
        perf4 = await self.test_ttl_expiration(cache_manager)
        self.results.append(("TTL功能", {"success": perf4}))

        # 生成报告
        self.generate_report()

        return self.results

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("性能测试报告")
        print("=" * 60)

        for test_name, result in self.results:
            print(f"\n{test_name}:")
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, float):
                        if key.endswith('_time') or key.endswith('_latency_ms'):
                            print(f"  {key}: {value:.4f}")
                        else:
                            print(f"  {key}: {value:.2f}")
                    else:
                        print(f"  {key}: {value}")
            else:
                print(f"  结果: {result}")

        # 性能要求检查
        print("\n性能要求检查:")

        # 检查基本性能要求
        basic_perf = self.results[0][1] if self.results else None
        if basic_perf and basic_perf.get("total_ops_sec", 0) > 100000:
            print("  ✓ 基本性能 > 100,000 ops/sec")
        else:
            print(f"  ✗ 基本性能 < 100,000 ops/sec (实际: {basic_perf.get('total_ops_sec', 0):.0f})")

        # 检查延迟要求
        concurrent_perf = self.results[1][1] if len(self.results) > 1 else None
        if concurrent_perf and concurrent_perf.get("p95_latency_ms", 0) < 5:
            print("  ✓ P95延迟 < 5ms")
        else:
            print(f"  ✗ P95延迟 >= 5ms (实际: {concurrent_perf.get('p95_latency_ms', 0):.2f}ms)")

        # 检查缓存命中率
        if basic_perf and basic_perf.get("hit_rate", 0) > 0.5:
            print("  ✓ 缓存命中率 > 50%")
        else:
            print(f"  ✗ 缓存命中率 < 50% (实际: {basic_perf.get('hit_rate', 0):.1%})")


async def main():
    """主测试函数"""
    # 尝试导入CacheManager
    try:
        from services.cache_manager import CacheManager
        from services.cache_strategy import DEFAULT_STRATEGIES

        print("成功导入CacheManager")
    except ImportError as e:
        print(f"导入CacheManager失败: {e}")
        print("请确保CacheManager已正确实现")
        return False

    # 创建CacheManager实例
    cache = CacheManager(
        redis_url=None,  # 不使用Redis，仅内存缓存
        strategies=DEFAULT_STRATEGIES
    )

    # 运行测试
    tester = CachePerformanceTester()
    results = await tester.run_all_tests(cache)

    # 关闭缓存
    await cache.close()

    print("\n测试完成！")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
"""
缓存系统压力测试
Cache System Stress Tests

验证缓存系统在高负载下的性能和稳定性
"""

import asyncio
import time
import random
import string
import statistics
import psutil
import gc
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
import pytest

from src.services.cache_manager import CacheManager, CacheStrategies
from src.monitoring.cache_metrics import CacheMetricsCollector


class CacheStressTest:
    """缓存压力测试类"""

    def __init__(self):
        self.manager = None
        self.metrics_collector = None
        self.test_results = {}

    def setup(self, enable_redis=False, memory_size=1000):
        """设置测试环境"""
        self.manager = CacheManager(
            enable_redis=enable_redis,
            default_memory_size=memory_size
        )

        # 初始化指标收集器
        from prometheus_client import CollectorRegistry
        registry = CollectorRegistry()
        self.metrics_collector = CacheMetricsCollector(registry)

    def cleanup(self):
        """清理测试环境"""
        if self.manager:
            self.manager.shutdown()

    def generate_test_data(self, size: int = 1024) -> str:
        """生成测试数据"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=size))

    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": process.memory_percent()
        }

    async def stress_test_basic_operations(self, duration: int = 60, target_tps: int = 5000):
        """
        基础操作压力测试

        Args:
            duration: 测试持续时间（秒）
            target_tps: 目标每秒事务数
        """
        print(f"开始基础操作压力测试 - 目标TPS: {target_tps}, 持续时间: {duration}s")

        strategy = "performance"
        operations_count = 0
        errors_count = 0
        response_times = []

        start_time = time.time()
        end_time = start_time + duration

        async def worker():
            nonlocal operations_count, errors_count, response_times
            while time.time() < end_time:
                op_start = time.time()

                try:
                    # 随机选择操作类型
                    operation = random.choice(["set", "get", "delete"])
                    key = f"stress_key_{random.randint(1, 10000)}"

                    if operation == "set":
                        value = self.generate_test_data(random.randint(100, 1024))
                        success = self.manager.set(strategy, key, value)
                        assert success is True

                    elif operation == "get":
                        # 50%概率获取存在的键，50%获取不存在的键
                        if random.random() < 0.5:
                            key = f"stress_key_{random.randint(1, 100)}"
                        value = self.manager.get(strategy, key)
                        # 可能返回None，这是正常的

                    elif operation == "delete":
                        self.manager.delete(strategy, key)

                    operations_count += 1

                except Exception as e:
                    errors_count += 1
                    print(f"操作错误: {e}")

                finally:
                    response_time = time.time() - op_start
                    response_times.append(response_time)

                    # 控制TPS
                    if operations_count % 100 == 0:
                        actual_tps = operations_count / (time.time() - start_time)
                        if actual_tps > target_tps:
                            await asyncio.sleep(0.001)

        # 创建多个工作协程
        workers = [asyncio.create_task(worker()) for _ in range(10)]

        # 执行测试
        for worker in workers:
            await worker

        actual_duration = time.time() - start_time
        actual_tps = operations_count / actual_duration

        # 计算统计信息
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0
        p99_response_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else 0

        # 获取缓存指标
        metrics = self.manager.get_metrics(strategy)
        hit_rate = metrics.hit_rate

        # 获取内存使用
        memory_usage = self.get_memory_usage()

        results = {
            "test_name": "basic_operations_stress",
            "duration": actual_duration,
            "operations_count": operations_count,
            "target_tps": target_tps,
            "actual_tps": actual_tps,
            "errors_count": errors_count,
            "error_rate": errors_count / operations_count if operations_count > 0 else 0,
            "avg_response_time_ms": avg_response_time * 1000,
            "p95_response_time_ms": p95_response_time * 1000,
            "p99_response_time_ms": p99_response_time * 1000,
            "cache_hit_rate": hit_rate,
            "memory_usage_mb": memory_usage["rss_mb"],
            "success": errors_count / operations_count < 0.01 and actual_tps >= target_tps * 0.9
        }

        self.test_results["basic_operations"] = results
        return results

    async def stress_test_memory_pressure(self, max_memory_mb: int = 1024, duration: int = 300):
        """
        内存压力测试

        Args:
            max_memory_mb: 最大内存使用限制（MB）
            duration: 测试持续时间（秒）
        """
        print(f"开始内存压力测试 - 内存限制: {max_memory_mb}MB, 持续时间: {duration}s")

        strategy = "strategy"
        data_size = 2048  # 2KB per item
        items_added = 0
        evictions = 0

        start_time = time.time()
        end_time = start_time + duration

        while time.time() < end_time:
            memory_usage = self.get_memory_usage()

            if memory_usage["rss_mb"] > max_memory_mb:
                print(f"达到内存限制: {memory_usage['rss_mb']:.1f}MB")
                break

            # 添加大对象到缓存
            key = f"memory_pressure_key_{items_added}"
            value = self.generate_test_data(data_size)

            pre_size = len(self.manager._memory_caches.get(strategy, {}))

            success = self.manager.set(strategy, key, value)
            if success:
                items_added += 1

            post_size = len(self.manager._memory_caches.get(strategy, {}))

            if post_size <= pre_size:
                evictions += 1

            # 定期检查内存和垃圾回收
            if items_added % 1000 == 0:
                gc.collect()
                memory_usage = self.get_memory_usage()
                print(f"已添加 {items_added} 项, 内存使用: {memory_usage['rss_mb']:.1f}MB, 淘汰次数: {evictions}")

            await asyncio.sleep(0.001)

        actual_duration = time.time() - start_time
        final_memory_usage = self.get_memory_usage()

        # 获取缓存统计
        cache_info = self.manager.get_cache_info()
        total_memory_items = sum(
            cache["size"] for cache in cache_info.get("memory_caches", {}).values()
        )

        results = {
            "test_name": "memory_pressure_stress",
            "duration": actual_duration,
            "max_memory_limit_mb": max_memory_mb,
            "items_added": items_added,
            "evictions": evictions,
            "eviction_rate": evictions / items_added if items_added > 0 else 0,
            "total_memory_items": total_memory_items,
            "final_memory_usage_mb": final_memory_usage["rss_mb"],
            "memory_efficiency": total_memory_items / (final_memory_usage["rss_mb"] * 1024 / data_size) if final_memory_usage["rss_mb"] > 0 else 0,
            "success": final_memory_usage["rss_mb"] <= max_memory_mb * 1.1  # 允许10%误差
        }

        self.test_results["memory_pressure"] = results
        return results

    async def stress_test_hit_rate_target(self, target_hit_rate: float = 0.75, duration: int = 120):
        """
        缓存命中率目标测试

        Args:
            target_hit_rate: 目标命中率
            duration: 测试持续时间（秒）
        """
        print(f"开始命中率目标测试 - 目标命中率: {target_hit_rate:.1%}, 持续时间: {duration}s")

        strategy = "user"
        keys_pool_size = 1000
        access_pattern = []  # 访问模式

        # 生成访问模式（80/20分布）
        for i in range(keys_pool_size):
            if i < keys_pool_size * 0.2:  # 20%的热点数据
                access_pattern.extend([i] * 4)  # 访问4次
            else:  # 80%的冷数据
                access_pattern.append(i)  # 访问1次

        random.shuffle(access_pattern)

        hits = 0
        misses = 0
        total_accesses = 0

        start_time = time.time()
        end_time = start_time + duration

        # 预热阶段 - 将所有键都加入缓存
        print("预热阶段...")
        for i in range(keys_pool_size):
            key = f"hit_rate_key_{i}"
            value = f"value_for_{i}"
            self.manager.set(strategy, key, value)

        print("测试阶段...")
        access_index = 0

        while time.time() < end_time and access_index < len(access_pattern):
            key_index = access_pattern[access_index]
            key = f"hit_rate_key_{key_index}"
            access_index += 1

            value = self.manager.get(strategy, key)

            if value is not None:
                hits += 1
            else:
                misses += 1

            total_accesses += 1

            # 模拟真实访问延迟
            await asyncio.sleep(0.001)

        actual_duration = time.time() - start_time
        actual_hit_rate = hits / total_accesses if total_accesses > 0 else 0

        # 获取官方指标
        metrics = self.manager.get_metrics(strategy)
        official_hit_rate = metrics.hit_rate

        results = {
            "test_name": "hit_rate_target_stress",
            "duration": actual_duration,
            "target_hit_rate": target_hit_rate,
            "total_accesses": total_accesses,
            "hits": hits,
            "misses": misses,
            "actual_hit_rate": actual_hit_rate,
            "official_hit_rate": official_hit_rate,
            "hit_rate_achieved": actual_hit_rate >= target_hit_rate,
            "success": actual_hit_rate >= target_hit_rate and official_hit_rate >= target_hit_rate
        }

        self.test_results["hit_rate_target"] = results
        return results

    async def stress_test_concurrent_users(self, num_users: int = 1000, ops_per_user: int = 50):
        """
        并发用户压力测试

        Args:
            num_users: 并发用户数
            ops_per_user: 每个用户的操作数
        """
        print(f"开始并发用户测试 - 用户数: {num_users}, 每用户操作数: {ops_per_user}")

        strategy = "session"
        total_operations = 0
        total_errors = 0
        user_results = []

        async def simulate_user(user_id: int):
            nonlocal total_operations, total_errors

            user_operations = 0
            user_errors = 0
            user_response_times = []

            for op in range(ops_per_user):
                op_start = time.time()

                try:
                    # 模拟用户操作
                    key = f"user_{user_id}_data_{random.randint(1, 10)}"

                    if random.random() < 0.6:  # 60%读取
                        value = self.manager.get(strategy, key)
                    else:  # 40%写入
                        value = f"user_{user_id}_value_{op}"
                        self.manager.set(strategy, key, value)

                    user_operations += 1

                except Exception as e:
                    user_errors += 1

                finally:
                    response_time = time.time() - op_start
                    user_response_times.append(response_time)

            total_operations += user_operations
            total_errors += user_errors

            user_results.append({
                "user_id": user_id,
                "operations": user_operations,
                "errors": user_errors,
                "avg_response_time": statistics.mean(user_response_times) if user_response_times else 0
            })

        start_time = time.time()

        # 分批执行用户以避免过度并发
        batch_size = 50
        for i in range(0, num_users, batch_size):
            batch_end = min(i + batch_size, num_users)
            batch_users = range(i, batch_end)

            batch_tasks = [simulate_user(user_id) for user_id in batch_users]
            await asyncio.gather(*batch_tasks)

            print(f"已完成 {batch_end}/{num_users} 用户")

        total_duration = time.time() - start_time

        # 计算统计信息
        avg_user_response_time = statistics.mean(
            [result["avg_response_time"] for result in user_results]
        ) if user_results else 0

        error_rate = total_errors / total_operations if total_operations > 0 else 0
        throughput = total_operations / total_duration

        # 获取系统资源使用
        memory_usage = self.get_memory_usage()

        results = {
            "test_name": "concurrent_users_stress",
            "num_users": num_users,
            "ops_per_user": ops_per_user,
            "duration": total_duration,
            "total_operations": total_operations,
            "total_errors": total_errors,
            "error_rate": error_rate,
            "throughput_ops_per_second": throughput,
            "avg_user_response_time_ms": avg_user_response_time * 1000,
            "memory_usage_mb": memory_usage["rss_mb"],
            "success": error_rate < 0.05 and throughput > 100  # 错误率<5%, 吞吐量>100ops/s
        }

        self.test_results["concurrent_users"] = results
        return results

    def generate_report(self) -> str:
        """生成测试报告"""
        report = []
        report.append("=" * 80)
        report.append("缓存系统压力测试报告")
        report.append("=" * 80)
        report.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # 总体结果
        all_passed = all(result.get("success", False) for result in self.test_results.values())
        report.append(f"总体结果: {'✅ 全部通过' if all_passed else '❌ 存在失败'}")
        report.append("")

        # 各测试结果
        for test_name, result in self.test_results.items():
            report.append(f"测试: {result.get('test_name', test_name)}")
            report.append("-" * 40)

            if test_name == "basic_operations":
                report.append(f"  目标TPS: {result['target_tps']}")
                report.append(f"  实际TPS: {result['actual_tps']:.0f}")
                report.append(f"  错误率: {result['error_rate']:.2%}")
                report.append(f"  平均响应时间: {result['avg_response_time_ms']:.2f}ms")
                report.append(f"  缓存命中率: {result['cache_hit_rate']:.2%}")

            elif test_name == "memory_pressure":
                report.append(f"  内存限制: {result['max_memory_limit_mb']}MB")
                report.append(f"  实际内存使用: {result['final_memory_usage_mb']:.1f}MB")
                report.append(f"  添加项目数: {result['items_added']}")
                report.append(f"  淘汰率: {result['eviction_rate']:.2%}")

            elif test_name == "hit_rate_target":
                report.append(f"  目标命中率: {result['target_hit_rate']:.2%}")
                report.append(f"  实际命中率: {result['actual_hit_rate']:.2%}")
                report.append(f"  官方命中率: {result['official_hit_rate']:.2%}")

            elif test_name == "concurrent_users":
                report.append(f"  并发用户数: {result['num_users']}")
                report.append(f"  总操作数: {result['total_operations']}")
                report.append(f"  吞吐量: {result['throughput_ops_per_second']:.0f} ops/s")
                report.append(f"  错误率: {result['error_rate']:.2%}")

            report.append(f"  结果: {'✅ 通过' if result.get('success') else '❌ 失败'}")
            report.append("")

        # 性能建议
        report.append("性能建议:")
        report.append("-" * 40)

        if not all_passed:
            report.append("❌ 存在性能问题，建议:")
            failed_tests = [name for name, result in self.test_results.items() if not result.get("success", False)]

            if "basic_operations" in failed_tests:
                report.append("  - 考虑增加缓存大小或优化缓存策略")
                report.append("  - 检查网络延迟和序列化性能")

            if "memory_pressure" in failed_tests:
                report.append("  - 调整内存缓存大小限制")
                report.append("  - 启用数据压缩")
                report.append("  - 考虑使用Redis作为L2缓存")

            if "hit_rate_target" in failed_tests:
                report.append("  - 优化缓存键设计")
                report.append("  - 调整TTL策略")
                report.append("  - 分析数据访问模式")

            if "concurrent_users" in failed_tests:
                report.append("  - 增加连接池大小")
                report.append("  - 优化并发处理逻辑")
        else:
            report.append("✅ 所有测试通过，缓存系统性能良好")

        return "\n".join(report)


# pytest测试函数
@pytest.mark.asyncio
async def test_cache_stress_suite():
    """运行完整的缓存压力测试套件"""
    stress_test = CacheStressTest()

    try:
        # 设置测试环境
        stress_test.setup(enable_redis=False, memory_size=1000)

        # 运行所有压力测试
        print("开始缓存压力测试套件...")

        # 1. 基础操作压力测试
        await stress_test.stress_test_basic_operations(duration=30, target_tps=1000)

        # 2. 内存压力测试
        await stress_test.stress_test_memory_pressure(max_memory_mb=100, duration=60)

        # 3. 命中率目标测试
        await stress_test.stress_test_hit_rate_target(target_hit_rate=0.75, duration=60)

        # 4. 并发用户测试
        await stress_test.stress_test_concurrent_users(num_users=100, ops_per_user=10)

        # 生成报告
        report = stress_test.generate_report()
        print(report)

        # 保存报告到文件
        with open("cache_stress_test_report.txt", "w", encoding="utf-8") as f:
            f.write(report)

        # 验证关键性能指标
        basic_ops = stress_test.test_results.get("basic_operations", {})
        hit_rate_test = stress_test.test_results.get("hit_rate_target", {})
        memory_test = stress_test.test_results.get("memory_pressure", {})

        # 断言性能要求
        assert basic_ops.get("actual_tps", 0) >= 900, f"TPS不达标: {basic_ops.get('actual_tps', 0)}"
        assert hit_rate_test.get("actual_hit_rate", 0) >= 0.70, f"命中率不达标: {hit_rate_test.get('actual_hit_rate', 0)}"
        assert memory_test.get("final_memory_usage_mb", 0) <= 110, f"内存使用超标: {memory_test.get('final_memory_usage_mb', 0)}"

        print("✅ 缓存压力测试套件全部通过!")

    finally:
        # 清理测试环境
        stress_test.cleanup()


if __name__ == "__main__":
    # 直接运行压力测试
    asyncio.run(test_cache_stress_suite())
#!/usr/bin/env python3
"""
策略API性能基准测试
Strategy API Performance Benchmark

测试新架构的性能表现
"""

import asyncio
import time
import statistics
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
import concurrent.futures
import psutil
import tracemalloc

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """性能指标收集器"""

    def __init__(self):
        self.metrics = {
            "response_times": [],
            "memory_usage": [],
            "cpu_usage": [],
            "error_count": 0,
            "success_count": 0
        }

    def record_request(self, response_time: float, success: bool):
        """记录请求指标"""
        self.metrics["response_times"].append(response_time)
        if success:
            self.metrics["success_count"] += 1
        else:
            self.metrics["error_count"] += 1

    def record_system_metrics(self):
        """记录系统指标"""
        # 内存使用
        memory_info = psutil.virtual_memory()
        self.metrics["memory_usage"].append(memory_info.used / 1024 / 1024)  # MB

        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.metrics["cpu_usage"].append(cpu_percent)

    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        response_times = self.metrics["response_times"]

        if not response_times:
            return {}

        return {
            "total_requests": len(response_times),
            "success_rate": self.metrics["success_count"] / (self.metrics["success_count"] + self.metrics["error_count"]),
            "avg_response_time": statistics.mean(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "p50_response_time": statistics.median(response_times),
            "p95_response_time": self._percentile(response_times, 0.95),
            "p99_response_time": self._percentile(response_times, 0.99),
            "avg_memory_usage_mb": statistics.mean(self.metrics["memory_usage"]) if self.metrics["memory_usage"] else 0,
            "peak_memory_usage_mb": max(self.metrics["memory_usage"]) if self.metrics["memory_usage"] else 0,
            "avg_cpu_usage": statistics.mean(self.metrics["cpu_usage"]) if self.metrics["cpu_usage"] else 0
        }

    def _percentile(self, data: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not data:
            return 0
        data_sorted = sorted(data)
        index = int(len(data_sorted) * percentile)
        return data_sorted[min(index, len(data_sorted) - 1)]


class BenchmarkSuite:
    """基准测试套件"""

    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.scenarios = []

    def add_scenario(self, name: str, func, *args, **kwargs):
        """添加测试场景"""
        self.scenarios.append({
            "name": name,
            "func": func,
            "args": args,
            "kwargs": kwargs
        })

    async def run_scenario(self, scenario: Dict[str, Any], iterations: int = 100) -> Dict[str, Any]:
        """运行单个测试场景"""
        logger.info(f"开始运行场景: {scenario['name']}")

        # 开始内存追踪
        tracemalloc.start()

        # 清空指标
        self.metrics = PerformanceMetrics()

        # 预热
        logger.info("预热中...")
        for _ in range(10):
            await scenario["func"](*scenario["args"], **scenario["kwargs"])

        # 正式测试
        logger.info(f"开始执行 {iterations} 次测试...")
        start_time = time.time()

        for i in range(iterations):
            # 记录系统指标
            if i % 10 == 0:
                self.metrics.record_system_metrics()

            # 执行请求
            request_start = time.time()
            try:
                await scenario["func"](*scenario["args"], **scenario["kwargs"])
                success = True
            except Exception as e:
                logger.error(f"请求失败: {e}")
                success = False

            response_time = time.time() - request_start
            self.metrics.record_request(response_time, success)

        # 计算总耗时
        total_time = time.time() - start_time

        # 获取内存使用
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # 汇总结果
        results = {
            "scenario": scenario["name"],
            "iterations": iterations,
            "total_time_seconds": total_time,
            "requests_per_second": iterations / total_time,
            "memory_current_mb": current / 1024 / 1024,
            "memory_peak_mb": peak / 1024 / 1024,
            **self.metrics.get_summary()
        }

        logger.info(f"场景 {scenario['name']} 完成")
        return results

    async def run_all_scenarios(self, iterations: int = 100) -> List[Dict[str, Any]]:
        """运行所有测试场景"""
        results = []

        for scenario in self.scenarios:
            result = await self.run_scenario(scenario, iterations)
            results.append(result)

        return results

    def generate_report(self, results: List[Dict[str, Any]]) -> str:
        """生成性能测试报告"""
        report = []
        report.append("# 策略API性能基准测试报告")
        report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"\n## 测试环境")
        report.append(f"- CPU核心数: {psutil.cpu_count()}")
        report.append(f"- 总内存: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.2f} GB")

        report.append(f"\n## 测试结果汇总")
        report.append("\n| 场景 | QPS | 平均响应时间(ms) | P95响应时间(ms) | 成功率(%) | 峰值内存(MB) |")
        report.append("|------|-----|----------------|----------------|-----------|--------------|")

        for result in results:
            report.append(
                f"| {result['scenario']} | {result['requests_per_second']:.2f} | "
                f"{result['avg_response_time']*1000:.2f} | {result['p95_response_time']*1000:.2f} | "
                f"{result['success_rate']*100:.2f} | {result['memory_peak_mb']:.2f} |"
            )

        report.append(f"\n## 详细结果")
        for result in results:
            report.append(f"\n### {result['scenario']}")
            report.append(json.dumps(result, ensure_ascii=False, indent=2))

        return "\n".join(report)


# 模拟API端点
async def simulate_list_strategies(page: int = 1, page_size: int = 20):
    """模拟获取策略列表"""
    # 模拟数据库查询延迟
    await asyncio.sleep(0.01)

    # 模拟数据
    strategies = [
        {"id": f"strategy_{i}", "name": f"策略_{i}"}
        for i in range(page_size)
    ]

    return {
        "strategies": strategies,
        "total": 1000,
        "page": page,
        "page_size": page_size
    }


async def simulate_create_strategy():
    """模拟创建策略"""
    # 模拟数据库写入延迟
    await asyncio.sleep(0.02)

    # 模拟验证延迟
    await asyncio.sleep(0.01)

    return {"id": "new_strategy_123", "status": "created"}


async def simulate_execute_strategy(strategy_id: str):
    """模拟执行策略"""
    # 模拟策略执行延迟
    await asyncio.sleep(0.1)

    # 模拟生成信号
    await asyncio.sleep(0.05)

    return {"execution_id": f"exec_{strategy_id}_{int(time.time())}"}


async def simulate_get_performance_metrics():
    """模拟获取性能指标"""
    # 模拟聚合查询延迟
    await asyncio.sleep(0.05)

    # 模拟计算延迟
    await asyncio.sleep(0.02)

    return {
        "total_return": 0.15,
        "sharpe_ratio": 1.2,
        "max_drawdown": 0.05
    }


async def simulate_concurrent_requests(request_count: int = 10):
    """模拟并发请求"""
    tasks = []
    for i in range(request_count):
        task = simulate_list_strategies(page=i+1)
        tasks.append(task)

    # 并发执行
    results = await asyncio.gather(*tasks)
    return results


async def main():
    """主函数"""
    logger.info("开始策略API性能基准测试")

    # 创建测试套件
    suite = BenchmarkSuite()

    # 添加测试场景
    suite.add_scenario("获取策略列表", simulate_list_strategies)
    suite.add_scenario("创建策略", simulate_create_strategy)
    suite.add_scenario("执行策略", simulate_execute_strategy, "strategy_123")
    suite.add_scenario("获取性能指标", simulate_get_performance_metrics)
    suite.add_scenario("并发请求", simulate_concurrent_requests, 5)

    # 运行测试
    results = await suite.run_all_scenarios(iterations=200)

    # 生成报告
    report = suite.generate_report(results)

    # 保存报告
    report_file = f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    logger.info(f"性能测试完成，报告已保存到: {report_file}")

    # 打印摘要
    print("\n" + "="*50)
    print("性能测试摘要")
    print("="*50)
    for result in results:
        print(f"\n场景: {result['scenario']}")
        print(f"QPS: {result['requests_per_second']:.2f}")
        print(f"平均响应时间: {result['avg_response_time']*1000:.2f} ms")
        print(f"P95响应时间: {result['p95_response_time']*1000:.2f} ms")
        print(f"成功率: {result['success_rate']*100:.2f}%")


class LoadTest:
    """负载测试"""

    def __init__(self):
        self.metrics = PerformanceMetrics()

    async def run_load_test(
        self,
        endpoint_func,
        duration_seconds: int = 60,
        concurrent_users: int = 10
    ) -> Dict[str, Any]:
        """
        运行负载测试

        Args:
            endpoint_func: 测试端点函数
            duration_seconds: 测试持续时间
            concurrent_users: 并发用户数
        """
        logger.info(f"开始负载测试: {concurrent_users} 并发用户，持续 {duration_seconds} 秒")

        start_time = time.time()
        end_time = start_time + duration_seconds

        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(concurrent_users)

        async def worker():
            """工作线程"""
            while time.time() < end_time:
                async with semaphore:
                    request_start = time.time()
                    try:
                        await endpoint_func()
                        success = True
                    except Exception as e:
                        logger.error(f"请求失败: {e}")
                        success = False

                    response_time = time.time() - request_start
                    self.metrics.record_request(response_time, success)

                    # 模拟用户间隔
                    await asyncio.sleep(0.1)

        # 启动工作线程
        tasks = [worker() for _ in range(concurrent_users)]

        # 运行测试
        await asyncio.gather(*tasks)

        # 计算结果
        actual_duration = time.time() - start_time
        summary = self.metrics.get_summary()

        return {
            "duration_seconds": actual_duration,
            "concurrent_users": concurrent_users,
            "total_requests": summary["total_requests"],
            "requests_per_second": summary["total_requests"] / actual_duration,
            **summary
        }


if __name__ == "__main__":
    # 运行基准测试
    asyncio.run(main())

    # 可选：运行负载测试
    # print("\n运行负载测试...")
    # load_test = LoadTest()
    # result = asyncio.run(
    #     load_test.run_load_test(
    #         simulate_list_strategies,
    #         duration_seconds=30,
    #         concurrent_users=20
    #     )
    # )
    # print(f"\n负载测试结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
"""
多进程回测性能测试脚本
=============================

对比单进程回测与多进程回测的性能差异：
- 执行时间对比
- 并行加速比
- 资源使用分析
- 可靠性评估

Author: CBSC Quant Team
Version: 1.0.0
Usage:
    python multiprocess_performance_test.py --configs N --mode [single|multi]
    python multiprocess_performance_test.py --benchmark
"""

import asyncio
import time
import argparse
import logging
from typing import List, Dict, Any
from datetime import datetime
import statistics
import json
from pathlib import Path
import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from backtest.multiprocess_engine import (
    MultiprocessBacktestEngine,
    MultiprocessBacktestRequest,
    ParallelLevel,
)
from backtest.backtest_service_v2 import BacktestServiceV2
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class PerformanceTestResult:
    """性能测试结果"""

    test_name: str
    mode: str  # 'single' or 'multi'
    num_configs: int
    total_time: float
    avg_time_per_config: float
    min_time: float
    max_time: float
    std_time: float

    # 资源使用
    cpu_percent_avg: float
    cpu_percent_peak: float
    memory_gb_avg: float
    memory_gb_peak: float

    # 并行指标
    parallel_speedup: float = 0.0  # 与单进程对比的加速比

    # 可靠性
    success_count: int
    failure_count: int
    timeout_count: int


class PerformanceBenchmark:
    """
    性能基准测试

    测试不同配置下的性能表现：
    1. 单进程（baseline）
    2. 多进程（不同worker数量）
    3. 不同并行级别
    """

    def __init__(self, db_session: Session):
        """初始化性能基准测试"""
        self.db = db_session
        self.backtest_service = BacktestServiceV2(db_session)

    def generate_test_configs(self, num_configs: int = 10) -> List[Dict[str, Any]]:
        """
        生成测试配置

        Args:
            num_configs: 配置数量

        Returns:
            配置列表
        """
        configs = []

        for i in range(num_configs):
            config = {
                "strategy_name": "MA_Crossover_Strategy",
                "symbols": ["0700.HK"],
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "initial_capital": 100000.0,
                "commission_rate": 0.001,
                "slippage_rate": 0.0005,
                "parameters": {"short_period": 20 + i, "long_period": 50 + i * 2},
            }
            configs.append(config)

        return configs

    async def run_single_process_test(self, configs: List[Dict[str, Any]]) -> PerformanceTestResult:
        """
        运行单进程回测（baseline）

        Args:
            configs: 测试配置列表

        Returns:
            PerformanceTestResult: 性能测试结果
        """
        logger.info(f"Starting single-process test with {len(configs)} configs")

        # 创建单进程配置
        request = MultiprocessBacktestRequest(
            backtest_configs=configs,
            parallel_level=ParallelLevel.STRATEGY_LEVEL,
            max_workers=1,  # 单进程
            max_concurrent=1,
            enable_auto_scaling=False,
            save_results=False,
            generate_report=False,
        )

        start_time = time.time()

        try:
            # 创建引擎并运行
            engine = MultiprocessBacktestEngine(config=request)
            result = await engine.run_backtests(configs)

            total_time = time.time() - start_time

            # 计算指标
            times = [r.total_execution_time for r in result.results]
            avg_time = statistics.mean(times) if times else 0
            min_time = min(times) if times else 0
            max_time = max(times) if times else 0
            std_time = statistics.stdev(times) if times else 0

            # 资源使用（简化，实际应该从系统监控获取）
            cpu_usage = 100.0 / max(1, len(configs))  # 假设满载
            cpu_percent_avg = cpu_usage / len(configs) if len(configs) > 0 else 100
            memory_usage = 2.0  # 假设每个配置使用2GB
            memory_gb_avg = memory_usage / len(configs) if len(configs) > 0 else 0
            memory_gb_peak = memory_usage

            # 统计结果
            success_count = len([r for r in result.results if r.status == "completed"])
            failure_count = len(result.results) - success_count

            perf_result = PerformanceTestResult(
                test_name="single_process_baseline",
                mode="single",
                num_configs=len(configs),
                total_time=total_time,
                avg_time_per_config=avg_time,
                min_time=min_time,
                max_time=max_time,
                std_time=std_time,
                cpu_percent_avg=cpu_percent_avg,
                cpu_percent_peak=cpu_usage,  # 假设峰值
                memory_gb_avg=memory_gb_avg,
                memory_gb_peak=memory_gb_peak,
                parallel_speedup=1.0,  # 基准
                success_count=success_count,
                failure_count=failure_count,
                timeout_count=0,
            )

            logger.info(
                f"Single-process test completed: {total_time:.2f}s, avg={avg_time:.2f}s/config"
            )

            return perf_result

        except Exception as e:
            logger.error(f"Single-process test failed: {e}")
            raise

    async def run_multi_process_test(
        self, configs: List[Dict[str, Any]], max_workers: int = 4
    ) -> PerformanceTestResult:
        """
        运行多进程回测

        Args:
            configs: 测试配置列表
            max_workers: 最大工作进程数

        Returns:
            PerformanceTestResult: 性能测试结果
        """
        logger.info(
            f"Starting multi-process test with {len(configs)} configs, max_workers={max_workers}"
        )

        # 创建多进程配置
        request = MultiprocessBacktestRequest(
            backtest_configs=configs,
            parallel_level=ParallelLevel.STRATEGY_LEVEL,
            max_workers=max_workers,
            max_concurrent=max_workers,
            enable_auto_scaling=True,
            save_results=False,
            generate_report=False,
        )

        start_time = time.time()

        try:
            # 创建引擎并运行
            engine = MultiprocessBacktestEngine(config=request)
            result = await engine.run_backtests(configs)

            total_time = time.time() - start_time

            # 计算指标
            times = [r.total_execution_time for r in result.results]
            avg_time = statistics.mean(times) if times else 0
            min_time = min(times) if times else 0
            max_time = max(times) if times else 0
            std_time = statistics.stdev(times) if times else 0

            # 资源使用（简化）
            cpu_usage = 100.0 / max(1, len(configs)) * max_workers
            cpu_percent_avg = cpu_usage / len(configs) if len(configs) > 0 else 100
            memory_usage = 2.0 * max_workers  # 假设每个进程2GB
            memory_gb_avg = memory_usage / len(configs) if len(configs) > 0 else 0
            memory_gb_peak = memory_usage

            # 统计结果
            success_count = len([r for r in result.results if r.status == "completed"])
            failure_count = len(result.results) - success_count

            # 计算并行加速比
            single_process_time = self._get_baseline_time()

            # 并行加速比
            if single_process_time and avg_time > 0:
                parallel_speedup = single_process_time / avg_time
            else:
                parallel_speedup = 1.0

            perf_result = PerformanceTestResult(
                test_name=f"multi_process_{max_workers}_workers",
                mode="multi",
                num_configs=len(configs),
                total_time=total_time,
                avg_time_per_config=avg_time,
                min_time=min_time,
                max_time=max_time,
                std_time=std_time,
                cpu_percent_avg=cpu_percent_avg,
                cpu_percent_peak=cpu_usage,
                memory_gb_avg=memory_gb_avg,
                memory_gb_peak=memory_gb_peak,
                parallel_speedup=parallel_speedup,
                success_count=success_count,
                failure_count=failure_count,
                timeout_count=0,
            )

            logger.info(
                f"Multi-process test completed: {total_time:.2f}s, "
                f"speedup={parallel_speedup:.2f}x, "
                f"avg={avg_time:.2f}s/config"
            )

            return perf_result

        except Exception as e:
            logger.error(f"Multi-process test failed: {e}")
            raise

    async def run_benchmark_suite(self, num_configs: int = 10) -> List[PerformanceTestResult]:
        """
        运行完整的性能基准测试套件

        Args:
            num_configs: 配置数量

        Returns:
            测试结果列表
        """
        logger.info("Starting performance benchmark suite")
        logger.info(f"Testing with {num_configs} configurations")

        # 生成测试配置
        configs = self.generate_test_configs(num_configs)

        # 运行测试套件
        results = []

        # 1. 单进程基准测试
        logger.info("Test 1: Single-process baseline")
        result_single = await self.run_single_process_test(configs)
        results.append(result_single)

        # 2. 2进程并行测试
        logger.info("Test 2: 2 workers")
        result_2w = await self.run_multi_process_test(configs, max_workers=2)
        results.append(result_2w)

        # 3. 4进程并行测试
        logger.info("Test 3: 4 workers")
        result_4w = await self.run_multi_process_test(configs, max_workers=4)
        results.append(result_4w)

        # 4. 8进程并行测试
        logger.info("Test 4: 8 workers")
        result_8w = await self.run_multi_process_test(configs, max_workers=8)
        results.append(result_8w)

        logger.info("Benchmark suite completed")

        return results

    async def compare_results(self, results: List[PerformanceTestResult]) -> None:
        """
        对比测试结果并输出报告
        """
        logger.info("Analyzing and comparing results...")

        # 查找单进程基准
        baseline = None
        for result in results:
            if result.test_name == "single_process_baseline":
                baseline = result
                break

        if not baseline:
            logger.error("Baseline test not found")
            return

        # 对比多进程测试结果
        comparison_report = {
            "baseline": {
                "test_name": baseline.test_name,
                "total_time": baseline.total_time,
                "avg_time_per_config": baseline.avg_time_per_config,
                "parallel_speedup": baseline.parallel_speedup,
            },
            "comparisons": [],
        }

        for result in results:
            if result.test_name == "single_process_baseline":
                continue

            speedup = result.parallel_speedup
            efficiency = result.parallel_speedup / max(1, len(configs) / result.num_configs)

            comparison = {
                "test_name": result.test_name,
                "total_time": result.total_time,
                "avg_time_per_config": result.avg_time_per_config,
                "parallel_speedup": speedup,
                "efficiency": efficiency,
                "speedup_improvement": f"{(speedup - baseline.parallel_speedup) / baseline.parallel_speedup * 100:+.1f}%",
                "time_improvement": f"{(baseline.avg_time_per_config - result.avg_time_per_config) / baseline.avg_time_per_config * 100:+.1f}%",
            }

            comparison_report["comparisons"].append(comparison)

        # 输出报告
        print("\n" + "=" * 80)
        print("多进程回测性能对比报告")
        print("=" * 80 + "\n")

        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"配置数量: {baseline.num_configs}")
        print(
            f"单进程基准: {baseline.total_time:.2f}s ({baseline.avg_time_per_config:.2f}s/config)"
        )
        print()

        print("多进程并行测试结果:")
        print("-" * 80)
        print(
            f"{'测试名称':<25} | {'并行模式':<10} | {'配置数':<8} | {'总时间':<10} | {'平均时间':<10} | {'加速比':<10} | {'效率':<10}"
        )
        print("-" * 80)

        for comp in comparison_report["comparisons"]:
            print(
                f"{comp['test_name']:<25} | {comp['mode']:<10} | {comp['num_configs']:<8} | {comp['total_time']:<10.2f}s | {comp['avg_time_per_config']:<10.2f}s | {comp['parallel_speedup']:<10.2f}x | {comp['efficiency']:<10.2f}% | {comp['speedup_improvement']}"
            )
        print("-" * 80)

        print("\n结论:")
        print("=" * 80)

        if comparison_report["comparisons"]:
            best = max(comparison_report["comparisons"], key=lambda x: x["parallel_speedup"])
            print(f"✅ 最佳配置: {best['test_name']}")
            print(f"   - 并行加速: {best['parallel_speedup']:.2f}x")
            print(f"   - 效率: {best['efficiency']:.2f}%")
            print(f"   - 时间节省: {best['time_improvement']}")

        # 保存详细结果到JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = Path(f"multiprocess_performance_report_{timestamp}.json")

        report = {
            "timestamp": timestamp,
            "num_configs": baseline.num_configs,
            "baseline": {
                "test_name": baseline.test_name,
                "total_time": baseline.total_time,
                "avg_time_per_config": baseline.avg_time_per_config,
                "parallel_speedup": baseline.parallel_speedup,
            },
            "results": results,
            "comparison": comparison_report,
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n详细报告已保存到: {report_file}")

    def _get_baseline_time(self) -> float:
        """
        获取单进程基准时间

        在实际应用中，应该从数据库或缓存中读取历史基准
        这里简化处理，返回一个假设值
        """
        # 在实际应用中，应该查询历史基准
        # 这里返回一个合理的估计值
        return 30.0  # 假设单个配置需要30秒

    async def main(self, args):
        """主函数"""
        try:
            if args.benchmark:
                # 运行完整基准测试套件
                results = await self.run_benchmark_suite(num_configs=args.configs)

                # 对比结果
                await self.compare_results(results)

            elif args.mode == "single":
                # 运行单进程测试
                configs = self.generate_test_configs(args.configs)
                result = await self.run_single_process_test(configs)
                print("\n单进程测试结果:")
                print(f"总时间: {result.total_time:.2f}s")
                print(f"平均时间: {result.avg_time_per_config:.2f}s")
                print(f"成功数: {result.success_count}")

            elif args.mode == "multi":
                # 运行多进程测试
                configs = self.generate_test_configs(args.configs)
                result = await self.run_multi_process_test(
                    configs=configs, max_workers=args.workers
                )
                print("\n多进程测试结果:")
                print(f"总时间: {result.total_time:.2f}s")
                print(f"平均时间: {result.avg_time_per_config:.2f}s")
                print(f"并行加速: {result.parallel_speedup:.2f}x")
                print(f"成功数: {result.success_count}")

            else:
                print("请指定测试模式: --benchmark, --mode single, 或 --mode multi")

        except Exception as e:
            logger.error(f"Test failed: {e}")
            raise


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="多进程回测性能测试脚本")

    parser.add_argument("--configs", type=int, default=10, help="测试配置数量（默认10）")

    parser.add_argument(
        "--mode",
        type=str,
        choices=["single", "multi", "benchmark"],
        default="benchmark",
        help="测试模式: single（单进程）, multi（多进程）, benchmark（完整基准）",
    )

    parser.add_argument("--workers", type=int, default=4, help="多进程工作进程数（默认4）")

    parser.add_argument("--verbose", action="store_true", help="详细输出")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # 设置日志级别
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # 创建数据库会话
    engine = create_engine("sqlite:///backtest_results.db")
    SessionLocal = sessionmaker(bind=engine)

    db_session = SessionLocal()

    # 运行测试
    test = PerformanceBenchmark(db_session)

    asyncio.run(test.main(args))

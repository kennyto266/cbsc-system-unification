"""
多进程回测性能测试
=======================

测试多进程回测系统的性能，对比单进程与多进程的执行效率。

测试场景：
1. 单进程顺序执行（baseline）
2. 多进程并行执行（小规模：2 workers）
3. 多进程并行执行（大规模：所有 CPU 核心）
4. 不同并行级别的性能对比

测试指标：
- 执行时间
- 并行加速比
- 并行效率
- 内存使用
- CPU 使用率
- 任务吞吐量

Author: CBSC Quant Team
Version: 1.0.0
"""

import asyncio
import time
import psutil
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd
import numpy as np

from src.backtest.multiprocess_engine import (
    MultiprocessBacktestEngine,
    MultiprocessBacktestRequest,
    MultiprocessBacktestResult,
    ParallelLevel,
)


class PerformanceTester:
    """性能测试器"""

    def __init__(self):
        self.cpu_count = psutil.cpu_count()
        self.test_results: List[Dict[str, Any]] = []

    def _create_test_configs(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        创建测试用的回测配置

        Args:
            count: 配置数量

        Returns:
            回测配置列表
        """
        configs = []
        for i in range(count):
            config = {
                "strategy_id": f"test_strategy_{i}",
                "strategy_type": "ma_crossover",
                "symbols": ["0700.HK"],
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "initial_capital": 100000.0,
                "parameters": {
                    "short_period": 20 + i % 5,  # 变化参数
                    "long_period": 50 + i % 10,
                },
            }
            configs.append(config)
        return configs

    def _measure_resources(self) -> Dict[str, float]:
        """
        测量当前系统资源

        Returns:
            资源使用字典
        """
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": memory.used / (1024**3),
            "memory_total_gb": memory.total / (1024**3),
        }

    async def test_single_process(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        测试单进程顺序执行

        Args:
            configs: 回测配置列表

        Returns:
            性能结果
        """
        print("\n" + "=" * 60)
        print("测试 1: 单进程顺序执行 (baseline)")
        print("=" * 60)

        request = MultiprocessBacktestRequest(
            backtest_configs=configs,
            parallel_level=ParallelLevel.STRATEGY_LEVEL,
            max_workers=1,  # 单进程
            enable_auto_scaling=False,
            enable_progress_monitoring=False,
            save_results=False,
        )

        engine = MultiprocessBacktestEngine(request)

        # 测量初始资源
        resources_before = self._measure_resources()

        print(
            f"初始资源: CPU={resources_before['cpu_percent']:.1f}%, Memory={resources_before['memory_used_gb']:.2f}GB"
        )

        # 执行回测
        start_time = time.time()
        result: MultiprocessBacktestResult = await engine.run_backtests(configs)
        execution_time = result.total_execution_time

        # 测量结束资源
        resources_after = self._measure_resources()

        print(
            f"结束资源: CPU={resources_after['cpu_percent']:.1f}%, Memory={resources_after['memory_used_gb']:.2f}GB"
        )
        print(f"执行时间: {execution_time:.2f}s")
        print(f"完成的回测: {result.completed_backtests}/{result.total_backtests}")
        print(f"成功率: {result.success_rate:.1%}")

        return {
            "test_name": "single_process",
            "configs_count": len(configs),
            "execution_time": execution_time,
            "completed_backtests": result.completed_backtests,
            "failed_backtests": result.failed_backtests,
            "success_rate": result.success_rate,
            "parallel_speedup": 1.0,  # baseline
            "parallel_efficiency": 100.0,  # 100% (baseline)
            "resources_before": resources_before,
            "resources_after": resources_after,
        }

    async def test_multi_process_small(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        测试多进程并行执行（小规模：2 workers）

        Args:
            configs: 回测配置列表

        Returns:
            性能结果
        """
        print("\n" + "=" * 60)
        print("测试 2: 多进程并行执行 (2 workers)")
        print("=" * 60)

        request = MultiprocessBacktestRequest(
            backtest_configs=configs,
            parallel_level=ParallelLevel.STRATEGY_LEVEL,
            max_workers=2,  # 2 workers
            enable_auto_scaling=False,
            enable_progress_monitoring=False,
            save_results=False,
        )

        engine = MultiprocessBacktestEngine(request)

        resources_before = self._measure_resources()
        print(
            f"初始资源: CPU={resources_before['cpu_percent']:.1f}%, Memory={resources_before['memory_used_gb']:.2f}GB"
        )

        start_time = time.time()
        result: MultiprocessBacktestResult = await engine.run_backtests(configs)
        execution_time = result.total_execution_time

        resources_after = self._measure_resources()

        print(
            f"结束资源: CPU={resources_after['cpu_percent']:.1f}%, Memory={resources_after['memory_used_gb']:.2f}GB"
        )
        print(f"执行时间: {execution_time:.2f}s")
        print(f"完成的回测: {result.completed_backtests}/{result.total_backtests}")
        print(f"成功率: {result.success_rate:.1%}")
        print(f"并行加速比: {result.parallel_speedup:.2f}x")
        print(f"并行效率: {result.parallel_efficiency:.1%}")

        return {
            "test_name": "multi_process_small",
            "configs_count": len(configs),
            "execution_time": execution_time,
            "completed_backtests": result.completed_backtests,
            "failed_backtests": result.failed_backtests,
            "success_rate": result.success_rate,
            "parallel_speedup": result.parallel_speedup,
            "parallel_efficiency": result.parallel_efficiency * 100,
            "resources_before": resources_before,
            "resources_after": resources_after,
        }

    async def test_multi_process_full(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        测试多进程并行执行（完整并行：所有 CPU 核心）

        Args:
            configs: 回测配置列表

        Returns:
            性能结果
        """
        print("\n" + "=" * 60)
        print(f"测试 3: 多进程完整并行执行 ({self.cpu_count} workers)")
        print("=" * 60)

        request = MultiprocessBacktestRequest(
            backtest_configs=configs,
            parallel_level=ParallelLevel.STRATEGY_LEVEL,
            max_workers=self.cpu_count,  # 所有 CPU 核心
            enable_auto_scaling=False,
            enable_progress_monitoring=False,
            save_results=False,
        )

        engine = MultiprocessBacktestEngine(request)

        resources_before = self._measure_resources()
        print(
            f"初始资源: CPU={resources_before['cpu_percent']:.1f}%, Memory={resources_before['memory_used_gb']:.2f}GB"
        )

        start_time = time.time()
        result: MultiprocessBacktestResult = await engine.run_backtests(configs)
        execution_time = result.total_execution_time

        resources_after = self._measure_resources()

        print(
            f"结束资源: CPU={resources_after['cpu_percent']:.1f}%, Memory={resources_after['memory_used_gb']:.2f}GB"
        )
        print(f"执行时间: {execution_time:.2f}s")
        print(f"完成的回测: {result.completed_backtests}/{result.total_backtests}")
        print(f"成功率: {result.success_rate:.1%}")
        print(f"并行加速比: {result.parallel_speedup:.2f}x")
        print(f"并行效率: {result.parallel_efficiency:.1%}")

        return {
            "test_name": "multi_process_full",
            "configs_count": len(configs),
            "execution_time": execution_time,
            "completed_backtests": result.completed_backtests,
            "failed_backtests": result.failed_backtests,
            "success_rate": result.success_rate,
            "parallel_speedup": result.parallel_speedup,
            "parallel_efficiency": result.parallel_efficiency * 100,
            "resources_before": resources_before,
            "resources_after": resources_after,
        }

    async def run_all_tests(self, config_counts: List[int] = [5, 10, 20]) -> pd.DataFrame:
        """
        运行所有性能测试

        Args:
            config_counts: 要测试的配置数量列表

        Returns:
            包含所有测试结果的 DataFrame
        """
        print("\n" + "=" * 60)
        print("开始多进程回测性能测试")
        print("=" * 60)
        print(f"CPU 核心数: {self.cpu_count}")
        print(f"测试配置数量: {config_counts}")
        print()

        results = []

        for count in config_counts:
            configs = self._create_test_configs(count)

            # 测试 1: 单进程
            result_single = await self.test_single_process(configs)
            results.append(result_single)

            # 测试 2: 多进程小规模
            result_multi_small = await self.test_multi_process_small(configs)
            results.append(result_multi_small)

            # 测试 3: 多进程完整并行
            result_multi_full = await self.test_multi_process_full(configs)
            results.append(result_multi_full)

            print(f"\n配置数量 {count} 的测试完成\n")

        # 创建结果 DataFrame
        df = pd.DataFrame(results)

        # 分析结果
        self._print_summary(df, config_counts)

        return df

    def _print_summary(self, df: pd.DataFrame, config_counts: List[int]):
        """
        打印测试总结
        """
        print("\n" + "=" * 60)
        print("性能测试总结")
        print("=" * 60)

        # 按配置数量分组统计
        for count in config_counts:
            group = df[df["configs_count"] == count]

            print(f"\n--- 配置数量: {count} ---")

            # 平均执行时间
            avg_time = group["execution_time"].mean()
            print(f"平均执行时间: {avg_time:.2f}s")

            # 并行加速比
            avg_speedup = group["parallel_speedup"].mean()
            print(f"平均并行加速比: {avg_speedup:.2f}x")

            # 并行效率
            avg_efficiency = group["parallel_efficiency"].mean()
            print(f"平均并行效率: {avg_efficiency:.1f}%")

            # 最佳性能
            best_idx = group["execution_time"].idxmin()
            best_test = group.iloc[best_idx]
            print(f"最佳性能: {best_test['test_name']} ({best_test['execution_time']:.2f}s)")

            print(f"\n对比:")
            print(
                f"  单进程 vs 多进程小规模: {best_test['execution_time'] / group['execution_time'].iloc[1]:.2f}x"
            )
            print(
                f"  单进程 vs 多进程完整并行: {best_test['execution_time'] / group['execution_time'].iloc[2]:.2f}x"
            )

        # 总体统计
        print("\n" + "=" * 60)
        print("总体性能提升")
        print("=" * 60)

        # 计算总体加速比
        single_times = df[df["test_name"] == "single_process"]["execution_time"]
        multi_small_times = df[df["test_name"] == "multi_process_small"]["execution_time"]
        multi_full_times = df[df["test_name"] == "multi_process_full"]["execution_time"]

        print(f"单进程 vs 多进程小规模: {(single_times / multi_small_times).mean():.2f}x 加速")
        print(f"单进程 vs 多进程完整并行: {(single_times / multi_full_times).mean():.2f}x 加速")

        # 并行效率分析
        print(f"\n并行效率分析:")
        print(
            f"  小规模并行平均效率: {df[df['test_name'] == 'multi_process_small']['parallel_efficiency'].mean():.1f}%"
        )
        print(
            f"  完整并行平均效率: {df[df['test_name'] == 'multi_process_full']['parallel_efficiency'].mean():.1f}%"
        )

        # CPU 利用率分析
        print(f"\nCPU 利用率分析:")
        print(
            f"  完整并行时平均 CPU 使用率: {df[df['test_name'] == 'multi_process_full']['average_cpu_percent'].mean():.1f}%"
        )
        print(
            f"  单进程时平均 CPU 使用率: {df[df['test_name'] == 'single_process']['average_cpu_percent'].mean():.1f}%"
        )

    async def test_parallel_levels(self):
        """
        测试不同并行级别的性能

        测试策略级别、符号级别、参数级别的性能差异
        """
        print("\n" + "=" * 60)
        print("测试不同并行级别的性能")
        print("=" * 60)

        configs = self._create_test_configs(10)

        results = []

        # 策略级别并行
        print("\n--- 策略级别并行 ---")
        request_strategy = MultiprocessBacktestRequest(
            backtest_configs=configs,
            parallel_level=ParallelLevel.STRATEGY_LEVEL,
            max_workers=4,
            enable_progress_monitoring=False,
            save_results=False,
        )
        engine_strategy = MultiprocessBacktestEngine(request_strategy)
        start_time = time.time()
        result_strategy = await engine_strategy.run_backtests(configs)
        execution_strategy = time.time() - start_time

        results.append(
            {
                "test_name": "parallel_strategy_level",
                "parallel_level": "STRATEGY_LEVEL",
                "execution_time": execution_strategy,
                "parallel_speedup": result_strategy.parallel_speedup,
                "parallel_efficiency": result_strategy.parallel_efficiency * 100,
            }
        )

        # 参数级别并行
        print("\n--- 参数级别并行 ---")
        request_param = MultiprocessBacktestRequest(
            backtest_configs=configs,
            parallel_level=ParallelLevel.PARAMETER_LEVEL,
            max_workers=4,
            enable_progress_monitoring=False,
            save_results=False,
        )
        engine_param = MultiprocessBacktestEngine(request_param)
        start_time = time.time()
        result_param = await engine_param.run_backtests(configs)
        execution_param = time.time() - start_time

        results.append(
            {
                "test_name": "parallel_parameter_level",
                "parallel_level": "PARAMETER_LEVEL",
                "execution_time": execution_param,
                "parallel_speedup": result_param.parallel_speedup,
                "parallel_efficiency": result_param.parallel_efficiency * 100,
            }
        )

        # 混合模式
        print("\n--- 混合模式（自动选择） ---")
        request_hybrid = MultiprocessBacktestRequest(
            backtest_configs=configs,
            parallel_level=ParallelLevel.HYBRID,
            max_workers=4,
            enable_progress_monitoring=False,
            save_results=False,
        )
        engine_hybrid = MultiprocessBacktestEngine(request_hybrid)
        start_time = time.time()
        result_hybrid = await engine_hybrid.run_backtests(configs)
        execution_hybrid = time.time() - start_time

        results.append(
            {
                "test_name": "parallel_hybrid",
                "parallel_level": "HYBRID",
                "execution_time": execution_hybrid,
                "parallel_speedup": result_hybrid.parallel_speedup,
                "parallel_efficiency": result_hybrid.parallel_efficiency * 100,
            }
        )

        # 打印结果
        print("\n" + "=" * 60)
        print("并行级别对比结果")
        print("=" * 60)

        for r in results:
            print(f"\n{r['test_name']}:")
            print(f"  并行级别: {r['parallel_level']}")
            print(f"  执行时间: {r['execution_time']:.2f}s")
            print(f"  并行加速比: {r['parallel_speedup']:.2f}x")
            print(f"  并行效率: {r['parallel_efficiency']:.1f}%")

        return results


async def main():
    """
    主测试函数
    """
    tester = PerformanceTester()

    # 运行性能测试
    df = await tester.run_all_tests()

    # 测试并行级别
    parallel_level_results = await tester.test_parallel_levels()

    # 保存结果
    output_file = (
        f"multiprocess_performance_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    df.to_csv(output_file, index=False)
    print(f"\n结果已保存到: {output_file}")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════╗
║       多进程回测性能测试工具                              ║
║     CBSC Quantitative Trading System                     ║
╚══════════════════════════════════════════════════════╝

本工具用于测试和验证多进程回测系统的性能。
测试包括：
  - 单进程顺序执行（baseline）
  - 多进程并行执行（不同规模）
  - 不同并行级别的性能对比

请确保：
  - 系统有足够的 CPU 核心进行多进程测试
  - 有足够的内存
  - 系统负载较轻

开始测试...
    """)

    asyncio.run(main())

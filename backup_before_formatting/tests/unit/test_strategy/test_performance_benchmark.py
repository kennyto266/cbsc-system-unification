import random
"""
技术指标性能基准测试

测试所有技术指标的性能特征，包括计算时间、内存使用和缓存效果。
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from src.strategy.indicators.engine import IndicatorEngine, default_engine


class PerformanceBenchmark:
    """性能基准测试类"""

    def __init__(self, data_sizes: List[int] = None):
        """初始化基准测试

        Args:
            data_sizes: 测试数据大小列表，默认[100, 500, 1000, 2000]
        """
        self.data_sizes = data_sizes or [100, 500, 1000, 2000]
        self.engine = IndicatorEngine(cache_size=1000)
        self.results: Dict[str, Any] = {}

    def generate_test_data(self, size: int) -> pd.DataFrame:
        """生成测试数据

        Args:
            size: 数据点数量

        Returns:
            测试数据
        """
        np.random.seed(42)
        dates = pd.date_range(start="2020 - 01 - 01", periods=size, freq="D")

        returns = np.random.normal(0.0005, 0.02, size)
        closes = [100.0]
        for ret in returns:
            closes.append(closes[-1] * (1 + ret))
        closes = np.array(closes[1:])

        highs = closes + np.random.uniform(0, 2.0, size)
        lows = closes - np.random.uniform(0, 2.0, size)
        volumes = np.random.randint(100000, 1000000, size)

        data = pd.DataFrame(
            {
                "date": dates,
                "open": closes + np.random.uniform(-0.5, 0.5, size),
                "high": highs,
                "low": np.minimum(lows, closes),
                "close": closes,
                "volume": volumes,
            }
        )

        return data

    def benchmark_single_indicator(
        self,
        indicator_name: str,
        data: pd.DataFrame,
        iterations: int = 100,
        **params: Any,
    ) -> Dict[str, float]:
        """测试单个指标性能

        Args:
            indicator_name: 指标名称
            data: 测试数据
            iterations: 迭代次数
            **params: 指标参数

        Returns:
            性能统计
        """
        times = []
        memory_usage = []

        # 预热
        for _ in range(5):
            self.engine.calculate(indicator_name, data, **params)

        # 正式测试
        for i in range(iterations):
            start = time.perf_counter()
            result = self.engine.calculate(indicator_name, data, **params)
            end = time.perf_counter()

            elapsed_ms = (end - start) * 1000
            times.append(elapsed_ms)

        times = np.array(times)

        return {
            "indicator": indicator_name,
            "data_points": len(data),
            "iterations": iterations,
            "mean_ms": float(np.mean(times)),
            "median_ms": float(np.median(times)),
            "min_ms": float(np.min(times)),
            "max_ms": float(np.max(times)),
            "std_ms": float(np.std(times)),
            "p95_ms": float(np.percentile(times, 95)),
            "p99_ms": float(np.percentile(times, 99)),
        }

    def benchmark_all_indicators(
        self,
        data_size: int = 1000,
        iterations: int = 100,
    ) -> Dict[str, Dict[str, float]]:
        """测试所有指标

        Args:
            data_size: 数据大小
            iterations: 迭代次数

        Returns:
            性能结果
        """
        data = self.generate_test_data(data_size)
        results = {}

        # 定义要测试的指标
        indicators = [
            ("sma", {"period": 20}),
            ("ema", {"period": 20}),
            ("wma", {"period": 20}),
            ("vwma", {"period": 20}),
            ("rsi", {"period": 14}),
            ("macd", {}),
        ]

        print(f"\n{'='*60}")
        print(f"测试数据大小: {data_size} 个数据点")
        print(f"迭代次数: {iterations}")
        print(f"{'='*60}\n")

        for name, params in indicators:
            try:
                print(f"测试指标: {name} {params}...", end=" ")
                result = self.benchmark_single_indicator(
                    name, data, iterations, **params
                )
                results[name] = result

                # 显示结果
                mean_time = result["mean_ms"]
                p95_time = result["p95_ms"]
                status = "✓" if p95_time < 5.0 else "⚠"
                print(f"{status} 平均: {mean_time:.3f}ms, P95: {p95_time:.3f}ms")

            except Exception as e:
                print(f"✗ 错误: {e}")
                results[name] = {"error": str(e)}

        return results

    def benchmark_scalability(self) -> Dict[str, List[Dict[str, Any]]]:
        """测试可扩展性（不同数据大小）

        Returns:
            可扩展性结果
        """
        results = {}

        for size in self.data_sizes:
            print(f"\n测试数据大小: {size}")
            size_results = self.benchmark_all_indicators(data_size=size, iterations=50)
            results[str(size)] = size_results

        return results

    def benchmark_cache_effectiveness(self) -> Dict[str, Any]:
        """测试缓存效果

        Returns:
            缓存测试结果
        """
        data = self.generate_test_data(1000)
        engine = IndicatorEngine(cache_size=100)

        print("\n缓存效果测试:")
        print("-" * 60)

        # 第一次计算（无缓存）
        start = time.perf_counter()
        result1 = engine.calculate("sma", data, period=20)
        time1 = (time.perf_counter() - start) * 1000

        # 第二次计算（有缓存）
        start = time.perf_counter()
        result2 = engine.calculate("sma", data, period=20)
        time2 = (time.perf_counter() - start) * 1000

        # 多次计算（有缓存）
        times = []
        for _ in range(100):
            start = time.perf_counter()
            engine.calculate("sma", data, period=20)
            times.append((time.perf_counter() - start) * 1000)

        print(f"首次计算: {time1:.3f}ms")
        print(f"缓存命中: {time2:.3f}ms")
        print(f"缓存命中(100次平均): {np.mean(times):.3f}ms")
        print(f"缓存加速比: {time1 / np.mean(times):.2f}x")

        stats = engine.get_stats()
        print("\n缓存统计:")
        print(f"  缓存命中: {stats['cache_hits']}")
        print(f"  缓存未命中: {stats['cache_misses']}")
        print(f"  命中率: {stats['cache_hit_rate']}")

        return {
            "first_calculation_ms": time1,
            "cached_calculation_ms": time2,
            "cached_average_ms": float(np.mean(times)),
            "speedup_ratio": time1 / np.mean(times),
            "cache_stats": stats,
        }

    def benchmark_batch_processing(self) -> Dict[str, Any]:
        """测试批量处理性能

        Returns:
            批量处理结果
        """
        data = self.generate_test_data(1000)
        indicators = [
            {"name": "sma", "params": {"period": 20}},
            {"name": "ema", "params": {"period": 20}},
            {"name": "rsi", "params": {"period": 14}},
            {"name": "macd", "params": {}},
        ]

        print("\n批量处理测试:")
        print("-" * 60)

        # 串行计算
        start = time.perf_counter()
        for config in indicators:
            default_engine.calculate(config["name"], data, **config["params"])
        serial_time = (time.perf_counter() - start) * 1000

        print(f"串行计算: {serial_time:.3f}ms")

        # 并行计算
        engine_parallel = IndicatorEngine(enable_parallel=True, max_workers=4)
        start = time.perf_counter()
        results = engine_parallel.calculate_multiple(indicators, data)
        parallel_time = (time.perf_counter() - start) * 1000

        print(f"并行计算: {parallel_time:.3f}ms")
        print(f"加速比: {serial_time / parallel_time:.2f}x")
        print(f"结果数量: {len(results)}")

        return {
            "serial_time_ms": serial_time,
            "parallel_time_ms": parallel_time,
            "speedup_ratio": serial_time / parallel_time,
            "indicators_count": len(indicators),
        }

    def run_full_benchmark(self) -> Dict[str, Any]:
        """运行完整基准测试

        Returns:
            完整测试结果
        """
        print("\n" + "=" * 60)
        print("技术指标性能基准测试")
        print("=" * 60)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        results = {
            "timestamp": timestamp,
            "data_sizes": self.data_sizes,
            "scalability": {},
            "cache": {},
            "batch": {},
        }

        # 1. 可扩展性测试
        print("\n### 1. 可扩展性测试 ###")
        results["scalability"] = self.benchmark_scalability()

        # 2. 缓存效果测试
        print("\n### 2. 缓存效果测试 ###")
        results["cache"] = self.benchmark_cache_effectiveness()

        # 3. 批量处理测试
        print("\n### 3. 批量处理测试 ###")
        results["batch"] = self.benchmark_batch_processing()

        # 4. 性能总结
        print("\n" + "=" * 60)
        print("性能总结")
        print("=" * 60)

        # 检查所有指标是否满足性能要求
        print("\n性能要求检查 (P95 < 5ms):")
        for size, size_results in results["scalability"].items():
            print(f"\n数据大小: {size}")
            all_passed = True
            for name, result in size_results.items():
                if "error" in result:
                    print(f"  {name}: 错误 - {result['error']}")
                    all_passed = False
                else:
                    p95 = result["p95_ms"]
                    status = "✓" if p95 < 5.0 else "✗"
                    print(f"  {name}: {p95:.3f}ms {status}")
                    if p95 >= 5.0:
                        all_passed = False

            if all_passed:
                print("  所有指标均满足性能要求 ✓")

        return results

    def save_results(self, results: Dict[str, Any], filename: str = None):
        """保存结果到文件

        Args:
            results: 测试结果
            filename: 文件名，默认使用时间戳
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S")
            filename = f"benchmark_results_{timestamp}.json"

        with open(filename, "w", encoding="utf - 8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n结果已保存到: {filename}")


def main():
    """主函数"""
    # 创建基准测试实例
    benchmark = PerformanceBenchmark(data_sizes=[100, 500, 1000, 2000])

    # 运行测试
    results = benchmark.run_full_benchmark()

    # 保存结果
    benchmark.save_results(results)

    print("\n" + "=" * 60)
    print("基准测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()

#!/usr / bin / env python3
"""
技術指標性能測試
Technical Indicators Performance Tests

測試各種技術指標的計算性能和資源使用
"""

import gc
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import memory_profiler
import numpy as np
import pandas as pd
import psutil
import pytest

# Add simplified_system to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "simplified_system"))

from src.indicators.core_indicators import CoreIndicators
from tests.factories.stock_data_factory import StockDataGenerator


@pytest.mark.performance
class TestTechnicalIndicatorsPerformance:
    """技術指標性能測試類"""

    @pytest.fixture
    def indicators(self):
        """創建技術指標實例"""
        return CoreIndicators()

    @pytest.fixture(
        params=[("small", 100), ("medium", 1000), ("large", 10000), ("xlarge", 50000)]
    )
    def test_data(self, request):
        """生成不同大小的測試數據"""
        size_name, size = request.param
        generator = StockDataGenerator(seed = 42)
        prices = generator.generate_price_series(100.0, size)
        return {"name": size_name, "size": size, "prices": prices}

    def test_sma_performance(self, indicators, test_data):
        """測試SMA計算性能"""
        prices = test_data["prices"]
        period = min(20, len(prices) // 4)

        # 預熱
        indicators.calculate_sma(prices[:10], 5)

        # 性能測試
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        indicators.calculate_sma(prices, period)

        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory

        # 性能斷言
        expected_max_time = test_data["size"] * 0.0001  # 每點0.1ms
        assert execution_time < expected_max_time, (
            f"SMA計算過慢: {execution_time:.4f}s "
            f"for {test_data['size']} points (expected < {expected_max_time:.4f}s)"
        )

        # 記錄性能指標
        performance_metrics = {
            "indicator": "SMA",
            "data_size": test_data["size"],
            "period": period,
            "execution_time": execution_time,
            "memory_usage_mb": memory_usage,
            "points_per_second": (
                test_data["size"] / execution_time
                if execution_time > 0
                else float("inf")
            ),
        }

        print(
            f"Performance metrics for {test_data['name']} data: {performance_metrics}"
        )

    def test_ema_performance(self, indicators, test_data):
        """測試EMA計算性能"""
        prices = test_data["prices"]
        period = min(26, len(prices) // 4)

        # 預熱
        indicators.calculate_ema(prices[:10], 12)

        start_time = time.time()
        indicators.calculate_ema(prices, period)
        end_time = time.time()

        execution_time = end_time - start_time
        expected_max_time = test_data["size"] * 0.00015  # EMA通常比SMA稍慢

        assert execution_time < expected_max_time, (
            f"EMA計算過慢: {execution_time:.4f}s " f"for {test_data['size']} points"
        )

    def test_rsi_performance(self, indicators, test_data):
        """測試RSI計算性能"""
        prices = test_data["prices"]
        period = min(14, len(prices) // 10)

        # 預熱
        indicators.calculate_rsi(prices[:50], 5)

        start_time = time.time()
        result = indicators.calculate_rsi(prices, period)
        end_time = time.time()

        execution_time = end_time - start_time
        expected_max_time = test_data["size"] * 0.0002  # RSI計算較複雜

        assert execution_time < expected_max_time, (
            f"RSI計算過慢: {execution_time:.4f}s " f"for {test_data['size']} points"
        )

        # 驗證RSI值範圍
        valid_rsi = result.dropna()
        if len(valid_rsi) > 0:
            assert valid_rsi.min() >= 0
            assert valid_rsi.max() <= 100

    def test_macd_performance(self, indicators, test_data):
        """測試MACD計算性能"""
        prices = test_data["prices"]
        if len(prices) < 50:
            pytest.skip("數據太少，跳過MACD測試")

        fast, slow, signal = 12, 26, 9

        # 預熱
        indicators.calculate_macd(prices[:50], 5, 10, 3)

        start_time = time.time()
        result = indicators.calculate_macd(prices, fast, slow, signal)
        end_time = time.time()

        execution_time = end_time - start_time
        expected_max_time = test_data["size"] * 0.0003  # MACD最複雜

        assert execution_time < expected_max_time, (
            f"MACD計算過慢: {execution_time:.4f}s " f"for {test_data['size']} points"
        )

        # 驗證結果結構
        assert "macd" in result
        assert "signal" in result
        assert "histogram" in result

    def test_bollinger_bands_performance(self, indicators, test_data):
        """測試布林帶計算性能"""
        prices = test_data["prices"]
        period = min(20, len(prices) // 4)
        std_dev = 2

        # 預熱
        indicators.calculate_bollinger_bands(prices[:50], 10, 2)

        start_time = time.time()
        result = indicators.calculate_bollinger_bands(prices, period, std_dev)
        end_time = time.time()

        execution_time = end_time - start_time
        expected_max_time = test_data["size"] * 0.00025

        assert execution_time < expected_max_time, (
            f"布林帶計算過慢: {execution_time:.4f}s " f"for {test_data['size']} points"
        )

        # 驗證布林帶邏輯
        valid_data = {k: v.dropna() for k, v in result.items()}

        if all(len(v) > 0 for v in valid_data.values()):
            min_len = min(len(v) for v in valid_data.values())
            upper = valid_data["upper_band"].iloc[:min_len]
            middle = valid_data["middle_band"].iloc[:min_len]
            lower = valid_data["lower_band"].iloc[:min_len]

            assert (upper >= middle).all()
            assert (middle >= lower).all()

    def test_concurrent_calculations(self, indicators, test_data):
        """測試併發指標計算"""
        import concurrent.futures

        prices = test_data["prices"]
        if len(prices) < 100:
            pytest.skip("數據太少，跳過併發測試")

        def calculate_indicator_safe(ind_func, *args):
            """線程安全的指標計算"""
            try:
                return ind_func(*args)
            except Exception as e:
                return None

        # 併發計算多個指標
        with concurrent.futures.ThreadPoolExecutor(max_workers = 4) as executor:
            futures = [
                executor.submit(
                    calculate_indicator_safe, indicators.calculate_sma, prices, 20
                ),
                executor.submit(
                    calculate_indicator_safe, indicators.calculate_ema, prices, 26
                ),
                executor.submit(
                    calculate_indicator_safe, indicators.calculate_rsi, prices, 14
                ),
                executor.submit(
                    calculate_indicator_safe,
                    indicators.calculate_macd,
                    prices,
                    12,
                    26,
                    9,
                ),
            ]

            start_time = time.time()
            results = [future.result(timeout = 30) for future in futures]
            end_time = time.time()

        execution_time = end_time - start_time

        # 驗證所有計算成功
        assert all(result is not None for result in results), "併發計算失敗"

        # 併發應該比串行更快（或至少不會慢太多）
        expected_max_time = test_data["size"] * 0.0005
        assert execution_time < expected_max_time, (
            f"併發計算過慢: {execution_time:.4f}s " f"for {test_data['size']} points"
        )


@pytest.mark.performance
@pytest.mark.benchmark
class TestIndicatorsBenchmarking:
    """技術指標基準測試"""

    @pytest.fixture
    def benchmark_data(self):
        """創建基準測試數據"""
        generator = StockDataGenerator(seed = 123)
        return {
            "small": generator.generate_price_series(100.0, 100),
            "medium": generator.generate_price_series(100.0, 1000),
            "large": generator.generate_price_series(100.0, 5000),
        }

    def benchmark_indicator_calculation(
        self, indicators, prices, indicator_func, *args
    ):
        """基準測試輔助函數"""
        # 預熱
        indicator_func(prices[: min(50, len(prices))], *[min(arg, 10) for arg in args])

        # 多次測試取平均值
        times = []
        for _ in range(5):
            gc.collect()  # 清理內存
            start_time = time.perf_counter()
            indicator_func(prices, *args)
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        avg_time = np.mean(times)
        std_time = np.std(times)

        return {
            "avg_time": avg_time,
            "std_time": std_time,
            "min_time": min(times),
            "max_time": max(times),
            "data_points": len(prices),
        }

    def test_sma_benchmark(self, benchmark_data):
        """SMA基準測試"""
        indicators = CoreIndicators()

        results = {}
        for size, prices in benchmark_data.items():
            period = min(20, len(prices) // 4)
            result = self.benchmark_indicator_calculation(
                indicators, prices, indicators.calculate_sma, period
            )
            result["size_category"] = size
            results[size] = result

        # 性能要求
        for size, result in results.items():
            points_per_second = result["data_points"] / result["avg_time"]
            print(f"SMA {size}: {points_per_second:.0f} points / sec")

            # 性能基準要求
            if size == "small":
                assert points_per_second > 50000, "小數據集SMA性能不足"
            elif size == "medium":
                assert points_per_second > 100000, "中數據集SMA性能不足"
            elif size == "large":
                assert points_per_second > 200000, "大數據集SMA性能不足"

    def test_rsi_benchmark(self, benchmark_data):
        """RSI基準測試"""
        indicators = CoreIndicators()

        results = {}
        for size, prices in benchmark_data.items():
            period = min(14, len(prices) // 10)
            if len(prices) < period * 2:
                continue

            result = self.benchmark_indicator_calculation(
                indicators, prices, indicators.calculate_rsi, period
            )
            result["size_category"] = size
            results[size] = result

        # 性能要求（RSI較複雜，要求稍低）
        for size, result in results.items():
            points_per_second = result["data_points"] / result["avg_time"]
            print(f"RSI {size}: {points_per_second:.0f} points / sec")

            if size == "small":
                assert points_per_second > 20000, "小數據集RSI性能不足"
            elif size == "medium":
                assert points_per_second > 50000, "中數據集RSI性能不足"
            elif size == "large":
                assert points_per_second > 80000, "大數據集RSI性能不足"

    def test_memory_usage_scaling(self):
        """測試內存使用擴展性"""
        indicators = CoreIndicators()
        generator = StockDataGenerator(seed = 456)

        sizes = [100, 500, 1000, 5000, 10000]
        memory_usage = []

        for size in sizes:
            prices = generator.generate_price_series(100.0, size)

            # 清理內存
            gc.collect()
            initial_memory = psutil.Process().memory_info().rss

            # 計算指標
            indicators.calculate_sma(prices, 20)
            indicators.calculate_ema(prices, 26)
            indicators.calculate_rsi(prices, 14)

            final_memory = psutil.Process().memory_info().rss
            memory_delta = final_memory - initial_memory

            memory_usage.append(
                {
                    "size": size,
                    "memory_bytes": memory_delta,
                    "memory_per_point": memory_delta / size,
                }
            )

            # 清理
            del prices
            gc.collect()

        # 驗證內存使用合理性
        for i, usage in enumerate(memory_usage[1:], 1):
            prev_usage = memory_usage[i - 1]
            size_ratio = usage["size"] / prev_usage["size"]
            memory_ratio = usage["memory_bytes"] / max(prev_usage["memory_bytes"], 1)

            # 內存增長應該是線性的或亞線性的
            assert memory_ratio <= size_ratio * 1.5, "內存使用增長過快"

        # 輸出內存使用統計
        print("Memory Usage Scaling:")
        for usage in memory_usage:
            print(f"Size {usage['size']}: {usage['memory_per_point']:.2f} bytes / point")


@pytest.mark.performance
@pytest.mark.memory
class TestMemoryProfiling:
    """內存分析測試"""

    @pytest.fixture
    def memory_profiler_data(self):
        """創建內存分析測試數據"""
        generator = StockDataGenerator(seed = 789)
        return generator.generate_price_series(100.0, 1000)

    @memory_profiler.profile
    def test_sma_memory_profile(self, memory_profiler_data):
        """SMA內存分析"""
        indicators = CoreIndicators()
        result = indicators.calculate_sma(memory_profiler_data, 20)
        return result

    @memory_profiler.profile
    def test_rsi_memory_profile(self, memory_profiler_data):
        """RSI內存分析"""
        indicators = CoreIndicators()
        result = indicators.calculate_rsi(memory_profiler_data, 14)
        return result

    def test_memory_leak_detection(self):
        """測試內存洩漏檢測"""
        indicators = CoreIndicators()
        generator = StockDataGenerator(seed = 999)

        # 執行多次計算，檢查內存是否洩漏
        initial_memory = psutil.Process().memory_info().rss

        for i in range(100):
            prices = generator.generate_price_series(100.0, 100)
            indicators.calculate_sma(prices, 20)
            indicators.calculate_ema(prices, 26)
            indicators.calculate_rsi(prices, 14)

            if i % 20 == 0:
                gc.collect()

        final_memory = psutil.Process().memory_info().rss
        memory_increase = final_memory - initial_memory

        # 內存增長應該在合理範圍內（小於100MB）
        assert (
            memory_increase < 100 * 1024 * 1024
        ), f"可能存在內存洩漏，增長: {memory_increase / 1024 / 1024:.2f}MB"

    def test_large_dataset_memory_efficiency(self):
        """測試大數據集內存效率"""
        indicators = CoreIndicators()
        generator = StockDataGenerator(seed = 111)

        # 生成大數據集
        large_prices = generator.generate_price_series(100.0, 50000)

        # 監控內存使用
        gc.collect()
        initial_memory = psutil.Process().memory_info().rss

        # 計算指標
        sma_result = indicators.calculate_sma(large_prices, 20)
        ema_result = indicators.calculate_ema(large_prices, 26)
        rsi_result = indicators.calculate_rsi(large_prices, 14)

        peak_memory = psutil.Process().memory_info().rss
        memory_used = peak_memory - initial_memory

        # 計算內存效率
        memory_per_point = memory_used / len(large_prices)

        # 內存效率要求：每點數據應使用少於1KB內存
        assert (
            memory_per_point < 1024
        ), f"內存效率不足: {memory_per_point:.2f} bytes / point"

        # 清理並驗證內存釋放
        del large_prices, sma_result, ema_result, rsi_result
        gc.collect()

        final_memory = psutil.Process().memory_info().rss
        memory_freed = peak_memory - final_memory

        # 應該釋放大部分內存
        assert memory_freed > memory_used * 0.8, "內存未充分釋放"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

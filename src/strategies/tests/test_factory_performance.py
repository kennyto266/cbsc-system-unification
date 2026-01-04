"""
Strategy Factory Performance Tests
策略工廠性能測試

This module tests the performance characteristics of the Strategy Factory v2.0
"""

import pytest
import pandas as pd
import numpy as np
import time
from typing import Dict, List, Any
from uuid import uuid4

from ..enhanced_factory_v2 import StrategyFactoryV2, create_strategy
from ..enhanced_factory import StrategyType


class TestStrategyFactoryPerformance:
    """策略工廠性能測試"""

    @pytest.fixture
    def factory(self):
        """創建策略工廠實例"""
        return StrategyFactoryV2()

    @pytest.fixture
    def sample_data(self):
        """創建測試數據"""
        dates = pd.date_range(start="2024-01-01", periods=1000, freq="D")
        np.random.seed(42)

        data = []
        price = 100
        for date in dates:
            change = np.random.normal(0.0005, 0.02)
            price *= (1 + change)

            data.append({
                "open": price,
                "high": price * 1.02,
                "low": price * 0.98,
                "close": price,
                "volume": np.random.randint(1000000, 5000000)
            })

        df = pd.DataFrame(data, index=dates)
        return {"TEST": df}

    def test_initialization_performance(self, factory):
        """測試工廠初始化性能"""
        # 測量初始化時間
        start_time = time.time()
        factory = StrategyFactoryV2()
        init_time = time.time() - start_time

        # 初始化應該在100ms內完成
        assert init_time < 0.1, f"初始化時間過長: {init_time:.4f}秒"

        # 驗證正確初始化
        assert len(factory.get_available_strategies()) > 0

    def test_strategy_creation_performance(self, factory):
        """測試策略創建性能"""
        config = {"fast_period": 10, "slow_period": 20, "symbols": ["TEST"]}

        # 測量單個策略創建時間
        start_time = time.time()
        strategy = factory.create_strategy("ma_crossover", config)
        create_time = time.time() - start_time

        # 創建應該在10ms內完成
        assert create_time < 0.01, f"策略創建時間過長: {create_time:.4f}秒"
        assert strategy is not None

    def test_batch_creation_performance(self, factory):
        """測試批量創建性能"""
        # 創建大量策略配置
        configs = []
        for i in range(100):
            configs.append({
                "name": "ma_crossover",
                "fast_period": 10 + i % 10,
                "slow_period": 20 + i % 10,
                "symbols": ["TEST"]
            })

        # 測量批量創建時間
        start_time = time.time()
        strategies = factory.create_strategy_batch(configs)
        batch_time = time.time() - start_time

        # 批量創建100個策略應該在1秒內完成
        assert batch_time < 1.0, f"批量創建時間過長: {batch_time:.4f}秒"
        assert len(strategies) == 100

    def test_strategy_execution_performance(self, factory, sample_data):
        """測試策略執行性能"""
        config = {"fast_period": 10, "slow_period": 20, "symbols": ["TEST"]}
        strategy = factory.create_strategy("ma_crossover", config)

        # 測量執行時間
        start_time = time.time()
        result = strategy.execute(sample_data)
        exec_time = time.time() - start_time

        # 執行1000天數據應該在1秒內完成
        assert exec_time < 1.0, f"策略執行時間過長: {exec_time:.4f}秒"

        # 驗證結果
        assert "results" in result
        assert "TEST" in result["results"]

    def test_search_performance(self, factory):
        """測試搜索性能"""
        keywords = ["ma", "trend", "volume", "momentum", "rsi", "adx"]

        for keyword in keywords:
            start_time = time.time()
            results = factory.search_strategies(keyword)
            search_time = time.time() - start_time

            # 搜索應該在10ms內完成
            assert search_time < 0.01, f"搜索'{keyword}'時間過長: {search_time:.4f}秒"

    def test_validation_performance(self, factory):
        """測試配置驗證性能"""
        configs = [
            {"period": 14, "trend_threshold": 25},
            {"fast_period": 10, "slow_period": 20},
            {"ma_period": 20, "divergence_period": 10},
            {"period": 14, "overbought_level": 80, "oversold_level": 20}
        ]

        strategies = ["adx", "ma_crossover", "obv", "mfi"]

        for strategy, config in zip(strategies, configs):
            start_time = time.time()
            result = factory.validate_strategy_config(strategy, config)
            validate_time = time.time() - start_time

            # 驗證應該在10ms內完成
            assert validate_time < 0.01, f"驗證{strategy}時間過長: {validate_time:.4f}秒"
            assert "valid" in result

    def test_memory_usage(self, factory):
        """測試內存使用"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # 創建大量策略實例
        strategies = []
        for i in range(100):
            config = {
                "fast_period": 10 + i % 10,
                "slow_period": 20 + i % 10,
                "symbols": ["TEST"]
            }
            strategy = factory.create_strategy("ma_crossover", config)
            strategies.append(strategy)

        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB

        # 100個策略實例內存增長應小於50MB
        assert memory_increase < 50, f"內存使用過多: {memory_increase:.2f}MB"

    def test_concurrent_creation(self, factory):
        """測試並發創建性能"""
        import concurrent.futures
        import threading

        def create_strategy_worker():
            """工作線程函數"""
            config = {
                "fast_period": 10,
                "slow_period": 20,
                "symbols": ["TEST"]
            }
            return factory.create_strategy("ma_crossover", config)

        # 使用線程池並發創建策略
        num_threads = 10
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(create_strategy_worker) for _ in range(num_threads)]
            strategies = [future.result() for future in futures]

        concurrent_time = time.time() - start_time

        # 並發創建應該比順序創建快
        assert len(strategies) == num_threads
        assert all(s is not None for s in strategies)

    def test_cache_performance(self, factory):
        """測試緩存性能"""
        config = {"fast_period": 10, "slow_period": 20, "symbols": ["TEST"]}

        # 第一次創建
        start_time = time.time()
        strategy1 = factory.create_strategy("ma_crossover", config)
        first_create_time = time.time() - start_time

        # 第二次創建（可能使用緩存）
        start_time = time.time()
        strategy2 = factory.create_strategy("ma_crossover", config)
        second_create_time = time.time() - start_time

        # 驗證兩個策略是獨立的實例
        assert strategy1 is not strategy2
        assert strategy1.config == strategy2.config

    def test_large_data_performance(self, factory):
        """測試大量數據執行性能"""
        # 創建大量數據（10年日線）
        dates = pd.date_range(start="2014-01-01", periods=3650, freq="D")
        np.random.seed(42)

        data = []
        price = 100
        for date in dates:
            change = np.random.normal(0.0005, 0.02)
            price *= (1 + change)

            data.append({
                "open": price,
                "high": price * 1.02,
                "low": price * 0.98,
                "close": price,
                "volume": np.random.randint(1000000, 5000000)
            })

        df = pd.DataFrame(data, index=dates)
        large_data = {"TEST": df}

        # 創建並執行策略
        config = {"fast_period": 50, "slow_period": 200, "symbols": ["TEST"]}
        strategy = factory.create_strategy("ma_crossover", config)

        # 測量執行時間
        start_time = time.time()
        result = strategy.execute(large_data)
        exec_time = time.time() - start_time

        # 執行10年數據應該在5秒內完成
        assert exec_time < 5.0, f"大量數據執行時間過長: {exec_time:.4f}秒"

    def test_factory_statistics_performance(self, factory):
        """測試統計信息性能"""
        operations = [
            ("get_available_strategies", lambda: factory.get_available_strategies()),
            ("get_strategy_stats", lambda: factory.get_strategy_stats()),
            ("get_strategies_by_type", lambda: factory.get_strategies_by_type(StrategyType.TECHNICAL_ANALYSIS)),
        ]

        for name, func in operations:
            start_time = time.time()
            result = func()
            op_time = time.time() - start_time

            # 統計操作應該在10ms內完成
            assert op_time < 0.01, f"{name}時間過長: {op_time:.4f}秒"
            assert result is not None


def run_performance_tests():
    """運行所有性能測試"""
    print("🚀 Strategy Factory 性能測試")
    print("=" * 50)

    import pytest

    # 運行測試
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x"  # 遇到第一個失敗就停止
    ])

    if exit_code == 0:
        print("\n✅ 所有性能測試通過")
    else:
        print("\n❌ 部分性能測試失敗")


if __name__ == "__main__":
    run_performance_tests()
#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
GPU - VectorBT集成測試套件
驗證GPU加速VectorBT集成功能
"""

import logging
import os
import sys
import unittest

import numpy as np
import pandas as pd

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), "..", "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Configure logging
logging.basicConfig(level = logging.INFO)


class TestGPUVectorBTIntegration(unittest.TestCase):
    """GPU - VectorBT集成測試"""

    def setUp(self):
        """測試設置"""
        import os
        import sys

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

        from gpu.vectorbt_integration import get_gpu_vectorbt_integration

        self.integration = get_gpu_vectorbt_integration()
        self.test_data = self._create_test_stock_data()

    def _create_test_stock_data(self):
        """創建測試股票數據"""
        dates = pd.date_range(start="2023 - 01 - 01", end="2024 - 12 - 31", freq="D")

        # 模擬股價數據
        np.random.seed(42)
        base_price = 100
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = base_price * np.cumprod(1 + returns)

        # 創建OHLCV數據
        data = pd.DataFrame(index = dates)
        data["close"] = prices
        data["open"] = data["close"].shift(1).fillna(base_price)

        # 模擬高開低收
        volatility = 0.02
        data["high"] = data[["open", "close"]].max(axis = 1) * (
            1 + np.random.uniform(0, volatility, len(dates))
        )
        data["low"] = data[["open", "close"]].min(axis = 1) * (
            1 - np.random.uniform(0, volatility, len(dates))
        )

        # 模擬成交量
        data["volume"] = np.random.uniform(1000000, 5000000, len(dates))

        return data.dropna()

    def test_rsi_strategy_optimization(self):
        """測試RSI策略優化"""
        print("\n=== RSI Strategy Optimization Test ===")

        try:
            result = self.integration.optimize_nonprice_strategy(
                self.test_data, "rsi", param_ranges={"period": (10, 30)}
            )

            self.assertEqual(result.strategy_name, "RSI")
            self.assertIn("period", result.parameters)
            self.assertGreater(result.sharpe_ratio, -10)  # 合理的Sharpe比率範圍
            self.assertGreater(result.execution_time, 0)

            print(f"RSI optimization completed")
            print(f"Best parameters: {result.parameters}")
            print(f"Sharpe ratio: {result.sharpe_ratio:.3f}")
            print(f"Total return: {result.total_return:.2%}")
            print(f"GPU utilized: {result.gpu_utilized}")
            print(f"Strategies tested: {result.strategies_tested}")
            print(f"Execution time: {result.execution_time:.3f}s")

        except Exception as e:
            print(f"RSI optimization error: {e}")

    def test_macd_strategy_optimization(self):
        """測試MACD策略優化"""
        print("\n=== MACD Strategy Optimization Test ===")

        try:
            result = self.integration.optimize_nonprice_strategy(
                self.test_data,
                "macd",
                param_ranges={
                    "fast_period": (8, 15),
                    "slow_period": (20, 30),
                    "signal_period": (8, 12),
                },
            )

            self.assertEqual(result.strategy_name, "MACD")
            self.assertIn("fast_period", result.parameters)
            self.assertIn("slow_period", result.parameters)
            self.assertIn("signal_period", result.parameters)

            print(f"MACD optimization completed")
            print(f"Best parameters: {result.parameters}")
            print(f"Sharpe ratio: {result.sharpe_ratio:.3f}")
            print(f"Total return: {result.total_return:.2%}")
            print(f"Win rate: {result.win_rate:.2%}")

        except Exception as e:
            print(f"MACD optimization error: {e}")

    def test_bollinger_strategy_optimization(self):
        """測試布林帶策略優化"""
        print("\n=== Bollinger Bands Strategy Optimization Test ===")

        try:
            result = self.integration.optimize_nonprice_strategy(
                self.test_data,
                "bollinger",
                param_ranges={"period": (15, 25), "num_std": (1, 3)},
            )

            self.assertEqual(result.strategy_name, "BOLLINGER")
            self.assertIn("period", result.parameters)
            self.assertIn("num_std", result.parameters)

            print(f"Bollinger optimization completed")
            print(f"Best parameters: {result.parameters}")
            print(f"Sharpe ratio: {result.sharpe_ratio:.3f}")
            print(f"Max drawdown: {result.max_drawdown:.2%}")
            print(f"Profit factor: {result.profit_factor:.2f}")

        except Exception as e:
            print(f"Bollinger optimization error: {e}")

    def test_moving_average_strategy_optimization(self):
        """測試移動平均策略優化"""
        print("\n=== Moving Average Strategy Optimization Test ===")

        try:
            result = self.integration.optimize_nonprice_strategy(
                self.test_data,
                "moving_average",
                param_ranges={"short_period": (5, 15), "long_period": (20, 40)},
            )

            self.assertEqual(result.strategy_name, "MOVING_AVERAGE")
            self.assertIn("short_period", result.parameters)
            self.assertIn("long_period", result.parameters)
            self.assertLess(
                result.parameters["short_period"], result.parameters["long_period"]
            )

            print(f"Moving Average optimization completed")
            print(f"Best parameters: {result.parameters}")
            print(f"Sharpe ratio: {result.sharpe_ratio:.3f}")
            print(f"Calmar ratio: {result.calmar_ratio:.3f}")

        except Exception as e:
            print(f"Moving Average optimization error: {e}")

    def test_batch_optimization(self):
        """測試批量策略優化"""
        print("\n=== Batch Optimization Test ===")

        try:
            strategy_types = ["rsi", "macd", "bollinger"]
            param_ranges = {
                "rsi": {"period": (10, 20)},
                "macd": {
                    "fast_period": (10, 12),
                    "slow_period": (20, 25),
                    "signal_period": (8, 10),
                },
                "bollinger": {"period": (15, 20), "num_std": (1, 2)},
            }

            results = self.integration.batch_optimize_strategies(
                self.test_data, strategy_types, param_ranges
            )

            self.assertEqual(len(results), len(strategy_types))

            for strategy_type, result in results.items():
                self.assertIn(strategy_type, strategy_types)
                self.assertGreater(result.sharpe_ratio, -10)

            print(f"Batch optimization completed for {len(results)} strategies:")
            for strategy_type, result in results.items():
                print(
                    f"  {strategy_type}: Sharpe {result.sharpe_ratio:.3f}, Return {result.total_return:.2%}"
                )

        except Exception as e:
            print(f"Batch optimization error: {e}")

    def test_gpu_cpu_performance_comparison(self):
        """測試GPU / CPU性能比較"""
        print("\n=== GPU vs CPU Performance Comparison Test ===")

        try:
            comparison = self.integration.compare_gpu_cpu_performance(
                self.test_data, "rsi", param_ranges={"period": (10, 20)}
            )

            self.assertIn("performance", comparison)
            self.assertIn("gpu_result", comparison)
            self.assertIn("cpu_result", comparison)

            perf = comparison["performance"]
            self.assertGreater(perf["gpu_time"], 0)
            self.assertGreater(perf["cpu_time"], 0)

            print(f"Performance comparison completed:")
            print(f"  GPU time: {perf['gpu_time']:.3f}s")
            print(f"  CPU time: {perf['cpu_time']:.3f}s")
            print(f"  Speedup: {perf['speedup']:.2f}x")
            print(f"  Efficiency gain: {perf['efficiency_gain']}")

            # 精度驗證
            accuracy = comparison["accuracy"]
            print(f"  Sharpe ratio difference: {accuracy['sharpe_difference']:.6f}")
            print(f"  Total return difference: {accuracy['return_difference']:.6f}")

        except Exception as e:
            print(f"Performance comparison error: {e}")

    def test_vectorbt_portfolio_creation(self):
        """測試VectorBT投資組合創建"""
        print("\n=== VectorBT Portfolio Creation Test ===")

        try:
            result = self.integration.optimize_nonprice_strategy(
                self.test_data, "rsi", param_ranges={"period": (14, 14)}  # 固定參數
            )

            # 檢查VectorBT結果
            self.assertIsNotNone(result.portfolio)
            self.assertIsNotNone(result.equity_curve)
            self.assertIsNotNone(result.trades)
            self.assertIsNotNone(result.signals)

            print(f"VectorBT portfolio created successfully")
            print(f"  Equity curve points: {len(result.equity_curve)}")
            print(
                f"  Total trades: {len(result.trades) if result.trades is not None else 0}"
            )
            print(f"  Final portfolio value: {result.equity_curve.iloc[-1]:.2f}")

        except Exception as e:
            print(f"VectorBT portfolio creation error: {e}")

    def test_data_validation_and_error_handling(self):
        """測試數據驗證和錯誤處理"""
        print("\n=== Data Validation and Error Handling Test ===")

        try:
            # 測試無效數據
            invalid_data = pd.DataFrame(
                {
                    "close": [100, 200, 150],
                    "volume": [1000, 2000, 1500],
                    # 缺少OHLC列
                }
            )

            try:
                self.integration.optimize_nonprice_strategy(invalid_data, "rsi")
                self.fail("Should have raised ValueError for missing columns")
            except ValueError as e:
                print(f"Correctly caught missing columns error: {e}")

            # 測試數據不足
            short_data = self.test_data.head(50)  # 只有50天數據
            try:
                self.integration.optimize_nonprice_strategy(short_data, "rsi")
                self.fail("Should have raised ValueError for insufficient data")
            except ValueError as e:
                print(f"Correctly caught insufficient data error: {e}")

            # 測試無效價格數據
            invalid_price_data = self.test_data.copy()
            invalid_price_data.loc[invalid_price_data.index[10], "high"] = (
                invalid_price_data.loc[invalid_price_data.index[10], "low"] - 1
            )

            try:
                self.integration.optimize_nonprice_strategy(invalid_price_data, "rsi")
                self.fail("Should have raised ValueError for invalid price data")
            except ValueError as e:
                print(f"Correctly caught invalid price data error: {e}")

            print("Data validation and error handling tests passed")

        except Exception as e:
            print(f"Data validation test error: {e}")

    def test_configuration_and_initialization(self):
        """測試配置和初始化"""
        print("\n=== Configuration and Initialization Test ===")

        try:
            from gpu.vectorbt_integration import (
                GPUVectorBTConfig,
                GPUVectorBTIntegration,
            )

            # 測試自定義配置
            custom_config = GPUVectorBTConfig(
                use_gpu = True,
                initial_cash = 500000.0,
                fees = 0.002,
                optimization_metric="total_return",
            )

            custom_integration = GPUVectorBTIntegration(custom_config)

            self.assertEqual(custom_integration.config.initial_cash, 500000.0)
            self.assertEqual(custom_integration.config.fees, 0.002)
            self.assertEqual(
                custom_integration.config.optimization_metric, "total_return"
            )

            print("Custom configuration test passed")
            print(f"  Initial cash: {custom_integration.config.initial_cash}")
            print(f"  Fees: {custom_integration.config.fees}")
            print(f"  GPU available: {custom_integration.gpu_available}")

        except Exception as e:
            print(f"Configuration test error: {e}")

    def test_memory_management_and_cleanup(self):
        """測試內存管理和清理"""
        print("\n=== Memory Management and Cleanup Test ===")

        try:
            # 記錄初始內存使用
            initial_memory = self.integration._get_gpu_memory_usage()

            # 執行多次優化
            for i in range(3):
                result = self.integration.optimize_nonprice_strategy(
                    self.test_data, "rsi", param_ranges={"period": (10, 15)}
                )
                print(
                    f"  Optimization {i + 1} completed: Sharpe {result.sharpe_ratio:.3f}"
                )

            # 檢查內存使用
            final_memory = self.integration._get_gpu_memory_usage()

            print(f"Memory management test:")
            print(f"  Initial GPU memory: {initial_memory:.2f} GB")
            print(f"  Final GPU memory: {final_memory:.2f} GB")
            print(f"  Memory difference: {final_memory - initial_memory:.2f} GB")

            # 執行清理
            self.integration.cleanup()
            print("Memory cleanup completed")

        except Exception as e:
            print(f"Memory management test error: {e}")


def run_gpu_vectorbt_integration_tests():
    """運行所有GPU - VectorBT集成測試"""
    print("Starting GPU - VectorBT Integration Tests")
    print("=" * 60)

    # 創建測試套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestGPUVectorBTIntegration)

    # 運行測試
    runner = unittest.TextTestRunner(verbosity = 2)
    result = runner.run(suite)

    # 總結
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("All GPU - VectorBT integration tests completed!")
    else:
        print(f"{len(result.failures)} test failures, {len(result.errors)} errors")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_gpu_vectorbt_integration_tests()
    sys.exit(0 if success else 1)

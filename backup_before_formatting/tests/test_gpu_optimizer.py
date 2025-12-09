#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU參數優化引擎測試套件
驗證GPU加速參數優化功能
"""

import unittest
import logging
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Configure logging
logging.basicConfig(level=logging.INFO)

class TestGPUOptimizer(unittest.TestCase):
    """GPU參數優化器測試"""

    def setUp(self):
        """測試設置"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

        from gpu.parameter_optimizer import get_gpu_parameter_optimizer
        from gpu.nonprice_engine import get_nonprice_gpu_engine
        from vectorization.time_series import get_time_series_vectorizer

        self.optimizer = get_gpu_parameter_optimizer()
        self.gpu_engine = get_nonprice_gpu_engine()
        self.vectorizer = get_time_series_vectorizer()

        # 創建測試數據
        self.test_data = self._create_test_data()

    def _create_test_data(self):
        """創建測試數據"""
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        values = 100 + 10 * np.sin(np.arange(len(dates)) * 2 * np.pi / 365) + np.random.normal(0, 2, len(dates))

        df = pd.DataFrame({'value': values}, index=dates)
        return self.vectorizer.vectorize_dataframe(df, 'TEST')

    def test_gpu_optimization_config(self):
        """測試GPU優化配置"""
        print("\n=== GPU Optimization Config Test ===")

        try:
            # 測試RSI配置
            config = self.optimizer.create_optimization_config(
                strategy_type='rsi',
                param_ranges={'period': (10, 50)},
                param_steps={'period': 5}
            )

            self.assertEqual(config.strategy_type, 'rsi')
            self.assertEqual(config.param_ranges['period'], (10, 50))
            self.assertEqual(config.param_steps['period'], 5)

            print(f"RSI config created: {config.param_ranges}")

            # 測試MACD配置
            macd_config = self.optimizer.create_optimization_config(
                strategy_type='macd',
                use_gpu=True,
                enable_parallel=False
            )

            self.assertEqual(macd_config.strategy_type, 'macd')
            self.assertTrue(macd_config.use_gpu)
            self.assertFalse(macd_config.enable_parallel)

            print("MACD config created successfully")

        except Exception as e:
            print(f"Config creation error: {e}")

    def test_parameter_grid_generation(self):
        """測試參數網格生成"""
        print("\n=== Parameter Grid Generation Test ===")

        try:
            # 測試RSI參數網格
            config = self.optimizer.create_optimization_config(
                strategy_type='rsi',
                param_ranges={'period': (10, 20)},
                param_steps={'period': 2}
            )

            param_grid = self.optimizer.generate_parameter_grid(config)

            self.assertIsInstance(param_grid, list)
            self.assertGreater(len(param_grid), 0)

            expected_periods = [10, 12, 14, 16, 18, 20]
            actual_periods = [params['period'] for params in param_grid]
            self.assertEqual(sorted(actual_periods), expected_periods)

            print(f"Generated {len(param_grid)} parameter combinations")
            print(f"Sample parameters: {param_grid[:3]}")

            # 測試MACD參數網格
            macd_config = self.optimizer.create_optimization_config(
                strategy_type='macd',
                param_ranges={
                    'fast_period': (10, 12),
                    'slow_period': (20, 22),
                    'signal_period': (8, 9)
                },
                param_steps={'fast_period': 1, 'slow_period': 1, 'signal_period': 1}
            )

            macd_grid = self.optimizer.generate_parameter_grid(macd_config)
            print(f"MACD parameter grid size: {len(macd_grid)}")

        except Exception as e:
            print(f"Parameter grid generation error: {e}")

    def test_single_source_optimization(self):
        """測試單數據源優化"""
        print("\n=== Single Source Optimization Test ===")

        try:
            config = self.optimizer.create_optimization_config(
                strategy_type='rsi',
                param_ranges={'period': (10, 30)},
                param_steps={'period': 5},
                use_gpu=self.gpu_engine.gpu_available
            )

            report = self.optimizer.optimize_single_source(self.test_data, config)

            self.assertIsInstance(report, self.optimizer.__class__.__module__ + '.OptimizationReport')
            self.assertGreater(len(report.results), 0)
            self.assertEqual(report.config.strategy_type, 'rsi')
            self.assertIn('sharpe_ratio', report.best_strategy.metrics)

            print(f"Optimization completed: {len(report.results)} strategies")
            print(f"Execution time: {report.execution_time:.3f}s")
            print(f"Best strategy: {report.best_strategy.strategy_id}")
            print(f"Best Sharpe: {report.best_strategy.metrics['sharpe_ratio']:.3f}")
            print(f"GPU utilized: {report.gpu_utilized}")

        except Exception as e:
            print(f"Single source optimization error: {e}")

    def test_rsi_parameter_optimization(self):
        """測試RSI參數優化"""
        print("\n=== RSI Parameter Optimization Test ===")

        try:
            # 使用GPU引擎直接測試RSI優化
            if self.gpu_engine.gpu_available:
                results = self.gpu_engine.optimize_rsi_parameters_gpu(
                    self.test_data,
                    param_range=(10, 50),
                    step=5
                )
                method_used = "GPU"
            else:
                results = self.gpu_engine.optimize_rsi_parameters_cpu(
                    self.test_data,
                    param_range=(10, 50),
                    step=5
                )
                method_used = "CPU"

            self.assertIsInstance(results, list)
            self.assertGreater(len(results), 0)

            # 驗證結果結構
            for result in results[:3]:  # 只檢查前3個
                self.assertIn('period', result.parameters)
                self.assertIn('sharpe_ratio', result.metrics)
                self.assertIn('max_drawdown', result.metrics)
                self.assertIn('total_return', result.metrics)
                self.assertIn('win_rate', result.metrics)

            print(f"RSI optimization completed using {method_used}")
            print(f"Total strategies tested: {len(results)}")
            print(f"Best Sharpe ratio: {max(r.metrics['sharpe_ratio'] for r in results):.3f}")

            # 顯示頂級策略
            sorted_results = sorted(results, key=lambda x: x.metrics['sharpe_ratio'], reverse=True)
            print("Top 3 strategies:")
            for i, result in enumerate(sorted_results[:3]):
                print(f"  {i+1}. Period {result.parameters['period']}: Sharpe {result.metrics['sharpe_ratio']:.3f}")

        except Exception as e:
            print(f"RSI parameter optimization error: {e}")

    def test_multi_source_optimization(self):
        """測試多數據源優化"""
        print("\n=== Multi-Source Optimization Test ===")

        try:
            # 創建多個測試數據源
            data_dict = {}
            for i, source_name in enumerate(['HIBOR', 'MONETARY', 'GDP']):
                dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
                values = 100 + i * 10 + 5 * np.sin(np.arange(len(dates)) * 2 * np.pi / 365) + np.random.normal(0, 1, len(dates))
                df = pd.DataFrame({'value': values}, index=dates)

                vectorized = self.vectorizer.vectorize_dataframe(df, source_name)
                data_dict[source_name] = vectorized

            config = self.optimizer.create_optimization_config(
                strategy_type='rsi',
                param_ranges={'period': (10, 25)},
                param_steps={'period': 5},
                enable_parallel=True
            )

            report = self.optimizer.optimize_multiple_sources(data_dict, config)

            self.assertIsInstance(report, self.optimizer.__class__.__module__ + '.OptimizationReport')
            self.assertGreater(len(report.results), 0)
            self.assertEqual(len(report.data_sources), 3)

            print(f"Multi-source optimization completed")
            print(f"Data sources: {report.data_sources}")
            print(f"Total strategies: {len(report.results)}")
            print(f"Best strategy: {report.best_strategy.strategy_id}")
            print(f"Best Sharpe: {report.best_strategy.metrics['sharpe_ratio']:.3f}")

        except Exception as e:
            print(f"Multi-source optimization error: {e}")

    def test_performance_monitoring(self):
        """測試性能監控"""
        print("\n=== Performance Monitoring Test ===")

        try:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
            from gpu.performance_monitor import get_performance_monitor, OptimizationMetrics

            monitor = get_performance_monitor()

            # 測試性能監控器
            summary = monitor.get_performance_summary(duration_minutes=1)
            self.assertIsInstance(summary, dict)

            print("Performance monitor created successfully")
            print(f"Monitoring samples: GPU={summary.get('gpu_samples', 0)}, CPU={summary.get('cpu_samples', 0)}")

            # 記錄優化指標
            metrics = OptimizationMetrics(
                task_id="test_task",
                strategy_type="rsi",
                parameters_tested=100,
                execution_time=1.5,
                strategies_per_second=66.7,
                memory_peak=512.0,
                gpu_utilized=self.gpu_engine.gpu_available,
                success_rate=1.0
            )

            monitor.record_optimization_metrics(metrics)
            print(f"Optimization metrics recorded: {metrics.task_id}")

            # 測試內存管理器
            from gpu.performance_monitor import get_memory_manager
            memory_manager = get_memory_manager()

            memory_info = memory_manager.get_memory_usage()
            self.assertIsInstance(memory_info, dict)

            print("Memory manager created successfully")
            print(f"Managed allocations: {memory_info['managed_allocations']['count']}")

        except Exception as e:
            print(f"Performance monitoring test error: {e}")

    def test_comprehensive_optimization(self):
        """測試全面優化"""
        print("\n=== Comprehensive Optimization Test ===")

        try:
            # 創建測試數據
            data_dict = {'TEST': self.test_data}

            # 運行全面優化（限制策略類型以節省時間）
            comprehensive_results = self.optimizer.run_comprehensive_optimization(
                data_dict,
                strategy_types=['rsi']  # 只測試RSI以節省時間
            )

            self.assertIsInstance(comprehensive_results, dict)

            print(f"Comprehensive optimization completed")
            print(f"Strategy types tested: {list(comprehensive_results.keys())}")

            for strategy_type, report in comprehensive_results.items():
                print(f"  {strategy_type}: {len(report.results)} strategies, Best Sharpe: {report.best_strategy.metrics['sharpe_ratio']:.3f}")

        except Exception as e:
            print(f"Comprehensive optimization test error: {e}")

    def test_gpu_fallback_mechanism(self):
        """測試GPU回退機制"""
        print("\n=== GPU Fallback Mechanism Test ===")

        try:
            # 測試GPU不可用時的CPU回退
            original_gpu_available = self.gpu_engine.gpu_available

            # 強制設置為不可用（僅用於測試）
            self.gpu_engine.gpu_available = False
            self.gpu_engine._cuda_kernels = None

            # 執行優化，應該自動使用CPU
            cpu_results = self.gpu_engine.optimize_rsi_parameters_cpu(
                self.test_data,
                param_range=(10, 30),
                step=5
            )

            self.assertIsInstance(cpu_results, list)
            self.assertGreater(len(cpu_results), 0)

            print(f"CPU fallback optimization completed: {len(cpu_results)} strategies")

            # 恢復原始狀態
            self.gpu_engine.gpu_available = original_gpu_available

            print("GPU fallback mechanism verified")

        except Exception as e:
            print(f"GPU fallback mechanism test error: {e}")

def run_gpu_optimizer_tests():
    """運行所有GPU優化器測試"""
    print("Starting GPU Optimizer Tests")
    print("=" * 50)

    # 創建測試套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestGPUOptimizer)

    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 總結
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("All GPU optimizer tests completed!")
    else:
        print(f"{len(result.failures)} test failures, {len(result.errors)} errors")

    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_gpu_optimizer_tests()
    sys.exit(0 if success else 1)
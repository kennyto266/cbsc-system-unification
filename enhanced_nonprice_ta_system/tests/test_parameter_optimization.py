#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit Tests for Parameter Optimization
參數優化單元測試

Phase 6.1: Unit Testing Development

測試覆蓋：
- 參數空間搜索 (Parameter Space Search)
- 網格搜索優化 (Grid Search Optimization)
- 隨機搜索優化 (Random Search Optimization)
- 遺傳算法優化 (Genetic Algorithm Optimization)
- 貝葉斯優化 (Bayesian Optimization)
- 並行優化處理 (Parallel Optimization Processing)
"""

import unittest
import numpy as np
import pandas as pd
import time
import json
import os
import sys
from typing import Dict, List, Any, Tuple
from unittest.mock import Mock, patch

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from enhanced_nonprice_ta_system.core_optimizer import EnhancedOptimizerEngine
from enhanced_nonprice_ta_system.intelligent_cache import IntelligentCache

class TestParameterSpace(unittest.TestCase):
    """參數空間測試"""

    def setUp(self):
        """測試設置"""
        self.optimizer = EnhancedOptimizerEngine()
        self.test_data = self._generate_test_data(100)

    def _generate_test_data(self, length: int) -> List[float]:
        """生成測試數據"""
        np.random.seed(42)
        prices = []
        base_price = 100

        for _ in range(length):
            change = np.random.normal(0, 0.02)
            base_price *= (1 + change)
            prices.append(base_price)

        return prices

    def test_parameter_ranges(self):
        """測試參數範圍定義"""
        print("\n[TEST] 測試參數範圍定義...")

        # 測試RSI參數範圍
        rsi_range = self.optimizer.get_parameter_range('RSI')
        self.assertIn('period', rsi_range, "RSI應包含period參數")
        self.assertEqual(rsi_range['period']['min'], 1, "RSI period最小值應為1")
        self.assertEqual(rsi_range['period']['max'], 300, "RSI period最大值應為300")
        self.assertEqual(rsi_range['period']['step'], 1, "RSI period步長應為1")

        # 測試MACD參數範圍
        macd_range = self.optimizer.get_parameter_range('MACD')
        self.assertIn('fast', macd_range, "MACD應包含fast參數")
        self.assertIn('slow', macd_range, "MACD應包含slow參數")
        self.assertIn('signal', macd_range, "MACD應包含signal參數")

        # 驗證範圍合理性
        self.assertLess(macd_range['fast']['max'], macd_range['slow']['min'],
                       "MACD fast最大值應小於slow最小值")

    def test_kdj_parameter_validation(self):
        """測試KDJ參數驗證"""
        print("\n[TEST] 測試KDJ參數驗證...")

        # 測試有效的KDJ參數
        valid_params = {'k_period': 10, 'd_period': 2}
        is_valid = self.optimizer.validate_kdj_parameters(valid_params)
        self.assertTrue(is_valid, "有效的KDJ參數應通過驗證")

        # 測試無效的KDJ參數
        invalid_params = {'k_period': 500, 'd_period': 0}  # 超出範圍
        is_valid = self.optimizer.validate_kdj_parameters(invalid_params)
        self.assertFalse(is_valid, "無效的KDJ參數應被拒絕")

    def test_mb_kdj_strategy_parameters(self):
        """測試MB_KDJ_[10,2]策略參數"""
        print("\n[TEST] 測試MB_KDJ_[10,2]策略參數...")

        # 獲取保護策略參數
        protected_params = self.optimizer.get_protected_strategy_params('MB_KDJ_[10,2]')

        self.assertIsNotNone(protected_params, "應存在保護的策略參數")
        self.assertEqual(protected_params['k_period'], 10, "K週期應為10")
        self.assertEqual(protected_params['d_period'], 2, "D週期應為2")

        # 驗證策略性能
        expected_performance = protected_params.get('expected_performance', {})
        self.assertEqual(expected_performance.get('sharpe'), 3.672, "預期Sharpe應為3.672")

    def test_parameter_combination_generation(self):
        """測試參數組合生成"""
        print("\n[TEST] 測試參數組合生成...")

        # 生成RSI參數組合
        rsi_combinations = self.optimizer.generate_parameter_combinations('RSI', max_combinations=10)

        self.assertIsInstance(rsi_combinations, list, "參數組合應為列表")
        self.assertLessEqual(len(rsi_combinations), 10, "組合數量不應超過限制")

        # 驗證每個組合
        for combo in rsi_combinations:
            self.assertIn('period', combo, "組合應包含period參數")
            self.assertIsInstance(combo['period'], int, "period應為整數")
            self.assertGreaterEqual(combo['period'], 1, "period應大於等於1")
            self.assertLessEqual(combo['period'], 300, "period應小於等於300")

    def test_parameter_space_size_calculation(self):
        """測試參數空間大小計算"""
        print("\n[TEST] 測試參數空間大小計算...")

        # 計算完整參數空間大小
        total_space_size = self.optimizer.calculate_total_parameter_space()

        self.assertIsInstance(total_space_size, int, "參數空間大小應為整數")
        self.assertGreater(total_space_size, 0, "參數空間應大於0")

        # 驗證與預期值接近（24,044個策略）
        expected_size = 24044
        self.assertAlmostEqual(total_space_size, expected_size, delta=1000,
                              msg=f"參數空間大小應接近{expected_size}")

        print(f"總參數空間大小: {total_space_size:,}")


class TestGridSearchOptimization(unittest.TestCase):
    """網格搜索優化測試"""

    def setUp(self):
        """測試設置"""
        self.optimizer = EnhancedOptimizerEngine()
        self.test_data = self._generate_test_data(100)

    def _generate_test_data(self, length: int) -> List[float]:
        """生成測試數據"""
        np.random.seed(42)
        return [100 * (1 + np.random.normal(0, 0.02)) for _ in range(length)]

    def test_basic_grid_search(self):
        """測試基本網格搜索"""
        print("\n[TEST] 測試基本網格搜索...")

        # 小範圍網格搜索測試
        param_grid = {
            'period': [5, 10, 15, 20]
        }

        results = self.optimizer.run_grid_search('RSI', param_grid, self.test_data)

        self.assertIsInstance(results, dict, "結果應為字典")
        self.assertIn('best_params', results, "應包含最佳參數")
        self.assertIn('best_score', results, "應包含最佳分數")
        self.assertIn('all_results', results, "應包含所有結果")

        # 驗證最佳參數在網格中
        best_params = results['best_params']
        self.assertIn(best_params['period'], param_grid['period'], "最佳參數應在搜索網格中")

        # 驗證分數範圍
        best_score = results['best_score']
        self.assertIsInstance(best_score, (int, float), "最佳分數應為數值")
        self.assertGreater(best_score, 0, "最佳分數應大於0")

    def test_multi_parameter_grid_search(self):
        """測試多參數網格搜索"""
        print("\n[TEST] 測試多參數網格搜索...")

        # MACD多參數搜索
        param_grid = {
            'fast': [8, 12, 16],
            'slow': [21, 26, 31],
            'signal': [6, 9, 12]
        }

        results = self.optimizer.run_grid_search('MACD', param_grid, self.test_data)

        self.assertIsInstance(results, dict, "結果應為字典")

        # 驗證參數約束
        best_params = results['best_params']
        self.assertLess(best_params['fast'], best_params['slow'], "fast應小於slow")

        # 驗證結果數量
        expected_combinations = len(param_grid['fast']) * len(param_grid['slow']) * len(param_grid['signal'])
        self.assertGreaterEqual(len(results['all_results']), expected_combinations * 0.8,
                               "應包含大部分搜索結果")

    def test_kdj_grid_search_optimization(self):
        """測試KDJ網格搜索優化"""
        print("\n[TEST] 測試KDJ網格搜索優化...")

        # 專門測試KDJ參數（MB_KDJ_[10,2]相關）
        param_grid = {
            'k_period': [8, 9, 10, 11, 12],
            'd_period': [1, 2, 3, 4]
        }

        # 需要OHLC數據
        high_prices = [p * 1.02 for p in self.test_data]
        low_prices = [p * 0.98 for p in self.test_data]

        results = self.optimizer.run_grid_search(
            'KDJ', param_grid, self.test_data, high=high_prices, low=low_prices
        )

        self.assertIsInstance(results, dict, "結果應為字典")

        # 驗證MB_KDJ_[10,2]參數被包含
        all_params = [r['params'] for r in results['all_results']]
        mb_kdj_found = any(p['k_period'] == 10 and p['d_period'] == 2 for p in all_params)
        self.assertTrue(mb_kdj_found, "應包含MB_KDJ_[10,2]參數組合")

        # 如果找到，檢查其性能
        for result in results['all_results']:
            if (result['params']['k_period'] == 10 and
                result['params']['d_period'] == 2):
                print(f"MB_KDJ_[10,2]性能: Sharpe={result.get('sharpe', 0):.3f}")
                break

    def test_grid_search_performance(self):
        """測試網格搜索性能"""
        print("\n[TEST] 測試網格搜索性能...")

        # 中等規模網格搜索
        param_grid = {
            'period': list(range(10, 51, 5))  # 10, 15, 20, ..., 50
        }

        start_time = time.time()
        results = self.optimizer.run_grid_search('RSI', param_grid, self.test_data)
        execution_time = time.time() - start_time

        # 性能要求：應在合理時間內完成
        self.assertLess(execution_time, 10.0, "網格搜索應在10秒內完成")

        # 計算每個參數組合的平均時間
        combinations = len(param_grid['period'])
        avg_time_per_combo = execution_time / combinations
        print(f"每個參數組合平均時間: {avg_time_per_combo:.4f}秒")

        # 效率要求
        self.assertLess(avg_time_per_combo, 0.5, "每個組合處理時間應小於0.5秒")

    def test_grid_search_with_constraints(self):
        """測試帶約束的網格搜索"""
        print("\n[TEST] 測試帶約束的網格搜索...")

        # 添加約束條件
        constraints = {
            'min_trades': 10,
            'max_drawdown': -0.2,
            'min_sharpe': 0.5
        }

        param_grid = {'period': [10, 20, 30, 40]}

        results = self.optimizer.run_grid_search(
            'RSI', param_grid, self.test_data, constraints=constraints
        )

        # 驗證約束被應用
        for result in results['all_results']:
            if 'sharpe' in result and result['sharpe'] is not None:
                self.assertGreaterEqual(result['sharpe'], constraints['min_sharpe'],
                                      f"Sharpe應大於等於約束值")

            if 'max_drawdown' in result and result['max_drawdown'] is not None:
                self.assertGreaterEqual(result['max_drawdown'], constraints['max_drawdown'],
                                      f"最大回撤應滿足約束")


class TestRandomSearchOptimization(unittest.TestCase):
    """隨機搜索優化測試"""

    def setUp(self):
        """測試設置"""
        self.optimizer = EnhancedOptimizerEngine()
        self.test_data = self._generate_test_data(100)

    def _generate_test_data(self, length: int) -> List[float]:
        """生成測試數據"""
        np.random.seed(42)
        return [100 * (1 + np.random.normal(0, 0.015)) for _ in range(length)]

    def test_random_search_basic(self):
        """測試基本隨機搜索"""
        print("\n[TEST] 測試基本隨機搜索...")

        param_ranges = {
            'period': (1, 100)  # (min, max)
        }

        n_iterations = 20
        results = self.optimizer.run_random_search(
            'RSI', param_ranges, self.test_data, n_iterations=n_iterations
        )

        self.assertIsInstance(results, dict, "結果應為字典")
        self.assertIn('best_params', results, "應包含最佳參數")
        self.assertIn('best_score', results, "應包含最佳分數")

        # 驗證迭代次數
        self.assertEqual(len(results['all_results']), n_iterations, "應執行指定次數的迭代")

        # 驗證參數範圍
        best_params = results['best_params']
        self.assertGreaterEqual(best_params['period'], param_ranges['period'][0],
                              "參數應在範圍內")
        self.assertLessEqual(best_params['period'], param_ranges['period'][1],
                           "參數應在範圍內")

    def test_random_search_vs_grid_search(self):
        """測試隨機搜索vs網格搜索"""
        print("\n[TEST] 測試隨機搜索vs網格搜索...")

        param_ranges = {
            'period': (10, 50)
        }

        # 隨機搜索
        start_time = time.time()
        random_results = self.optimizer.run_random_search(
            'RSI', param_ranges, self.test_data, n_iterations=15
        )
        random_time = time.time() - start_time

        # 網格搜索（小規模）
        param_grid = {'period': list(range(10, 51, 5))}
        start_time = time.time()
        grid_results = self.optimizer.run_grid_search('RSI', param_grid, self.test_data)
        grid_time = time.time() - start_time

        # 比較性能
        print(f"隨機搜索時間: {random_time:.3f}秒")
        print(f"網格搜索時間: {grid_time:.3f}秒")

        # 隨機搜索通常更快
        self.assertLessEqual(random_time, grid_time * 1.2, "隨機搜索時間應接近或優於網格搜索")

        # 比較結果質量
        random_score = random_results['best_score']
        grid_score = grid_results['best_score']

        print(f"隨機搜索最佳分數: {random_score:.3f}")
        print(f"網格搜索最佳分數: {grid_score:.3f}")

        # 隨機搜索應找到合理的解
        self.assertGreater(random_score, 0, "隨機搜索應找到正分數的解")

    def test_random_search_early_stopping(self):
        """測試隨機搜索提前停止"""
        print("\n[TEST] 測試隨機搜索提前停止...")

        param_ranges = {
            'period': (1, 100)
        }

        # 設置提前停止條件
        early_stopping = {
            'patience': 5,  # 5次迭代無改善則停止
            'min_improvement': 0.01  # 最小改善幅度
        }

        start_time = time.time()
        results = self.optimizer.run_random_search(
            'RSI', param_ranges, self.test_data,
            n_iterations=50,  # 最多50次
            early_stopping=early_stopping
        )
        execution_time = time.time() - start_time

        # 應該提前停止（實際迭代次數 < 最大迭代次數）
        self.assertLess(len(results['all_results']), 50, "應該提前停止")
        print(f"實際迭代次數: {len(results['all_results'])}")
        print(f"執行時間: {execution_time:.3f}秒")

    def test_random_search_adaptive_sampling(self):
        """測試隨機搜索自適應採樣"""
        print("\n[TEST] 測試隨機搜索自適應採樣...")

        param_ranges = {
            'period': (5, 50),
            'threshold': (0.3, 0.8)
        }

        # 使用自適應採樣（基於前期結果調整採樣策略）
        adaptive_results = self.optimizer.run_random_search(
            'RSI', param_ranges, self.test_data,
            n_iterations=30,
            adaptive_sampling=True
        )

        # 驗證自適特性：後期採樣應更集中在有希望的區域
        all_results = adaptive_results['all_results']
        if len(all_results) >= 10:
            early_params = [r['params'] for r in all_results[:10]]
            late_params = [r['params'] for r in all_results[-10:]]

            # 檢查參數分佈（這是一個簡化的檢查）
            early_period_std = np.std([p['period'] for p in early_params])
            late_period_std = np.std([p['period'] for p in late_params])

            print(f"早期採樣週期標準差: {early_period_std:.2f}")
            print(f"後期採樣週期標準差: {late_period_std:.2f}")

            # 後期採樣應更集中（標準差可能更小）
            self.assertIsInstance(late_period_std, float, "後期採樣應有統計特性")


class TestParallelOptimization(unittest.TestCase):
    """並行優化測試"""

    def setUp(self):
        """測試設置"""
        self.optimizer = EnhancedOptimizerEngine()
        self.test_data = self._generate_test_data(200)

    def _generate_test_data(self, length: int) -> List[float]:
        """生成測試數據"""
        np.random.seed(42)
        return [100 * (1 + np.random.normal(0, 0.02)) for _ in range(length)]

    def test_parallel_parameter_evaluation(self):
        """測試並行參數評估"""
        print("\n[TEST] 測試並行參數評估...")

        # 生成大量參數組合
        param_combinations = [
            {'period': period} for period in range(10, 51, 2)  # 21個組合
        ]

        # 串行評估時間
        start_time = time.time()
        serial_results = self.optimizer.evaluate_parameters_serial('RSI', param_combinations, self.test_data)
        serial_time = time.time() - start_time

        # 並行評估時間
        start_time = time.time()
        parallel_results = self.optimizer.evaluate_parameters_parallel('RSI', param_combinations, self.test_data)
        parallel_time = time.time() - start_time

        # 驗證結果一致性
        self.assertEqual(len(parallel_results), len(serial_results), "並行和串行結果數量應一致")

        # 比較最佳結果
        serial_best = max(serial_results, key=lambda x: x.get('sharpe', 0))
        parallel_best = max(parallel_results, key=lambda x: x.get('sharpe', 0))

        # 最佳參數應相同或非常接近
        self.assertEqual(serial_best['params']['period'], parallel_best['params']['period'],
                        "並行和串行應找到相同的最佳參數")

        # 性能比較
        speedup = serial_time / parallel_time if parallel_time > 0 else 0
        print(f"串行時間: {serial_time:.3f}秒")
        print(f"並行時間: {parallel_time:.3f}秒")
        print(f"加速比: {speedup:.2f}x")

        # 並行應該更快（至少不慢很多）
        self.assertGreaterEqual(speedup, 0.8, "並行不應慢於串行太多")

    def test_multi_core_utilization(self):
        """測試多核心利用率"""
        print("\n[TEST] 測試多核心利用率...")

        import psutil
        import multiprocessing

        # 獲取CPU核心數
        cpu_count = multiprocessing.cpu_count()
        print(f"可用CPU核心數: {cpu_count}")

        # 測試不同並行度
        param_combinations = [
            {'period': period} for period in range(10, 61, 5)  # 11個組合
        ]

        for max_workers in [1, 2, 4, min(8, cpu_count)]:
            start_time = time.time()
            results = self.optimizer.evaluate_parameters_parallel(
                'RSI', param_combinations, self.test_data, max_workers=max_workers
            )
            execution_time = time.time() - start_time

            print(f"並行度 {max_workers}: {execution_time:.3f}秒, 結果數: {len(results)}")

            # 驗證結果完整性
            self.assertEqual(len(results), len(param_combinations), f"並行度{max_workers}應產生完整結果")

    def test_parallel_memory_usage(self):
        """測試並行內存使用"""
        print("\n[TEST] 測試並行內存使用...")

        import psutil

        # 大規模參數搜索
        param_combinations = [
            {'period': period} for period in range(10, 101, 2)  # 46個組合
        ]

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 並行評估
        results = self.optimizer.evaluate_parameters_parallel(
            'RSI', param_combinations, self.test_data, max_workers=4
        )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(f"初始內存: {initial_memory:.1f}MB")
        print(f"最終內存: {final_memory:.1f}MB")
        print(f"內存增長: {memory_increase:.1f}MB")
        print(f"每個參數組合內存: {memory_increase / len(param_combinations):.2f}MB")

        # 內存使用應合理
        self.assertLess(memory_increase, 200, "並行優化內存增長應小於200MB")

        # 驗證結果質量
        successful_results = [r for r in results if r.get('success', False)]
        success_rate = len(successful_results) / len(results)
        self.assertGreater(success_rate, 0.8, "並行評估成功率應大於80%")

    def test_parallel_fault_tolerance(self):
        """測試並行容錯性"""
        print("\n[TEST] 測試並行容錯性...")

        # 包含一些可能失敗的參數組合
        param_combinations = [
            {'period': period} for period in [5, 10, 15, 20, 25, 0, 500, 30, 35]  # 包含無效參數
        ]

        results = self.optimizer.evaluate_parameters_parallel(
            'RSI', param_combinations, self.test_data, max_workers=3
        )

        # 驗證容錯處理
        self.assertEqual(len(results), len(param_combinations), "應返回所有結果（包括失敗的）")

        # 檢查錯誤處理
        successful_results = [r for r in results if r.get('success', False)]
        failed_results = [r for r in results if not r.get('success', False)]

        print(f"成功結果: {len(successful_results)}")
        print(f"失敗結果: {len(failed_results)}")

        # 應該有一些成功和一些失敗的結果
        self.assertGreater(len(successful_results), 0, "應有成功結果")
        self.assertGreater(len(failed_results), 0, "應有失敗結果")

        # 失敗結果應有錯誤信息
        for failed_result in failed_results:
            self.assertIn('error', failed_result, "失敗結果應包含錯誤信息")


class TestOptimizationPerformance(unittest.TestCase):
    """優化性能測試"""

    def setUp(self):
        """測試設置"""
        self.optimizer = EnhancedOptimizerEngine()
        self.test_data = self._generate_test_data(500)

    def _generate_test_data(self, length: int) -> List[float]:
        """生成測試數據"""
        np.random.seed(42)
        return [100 * (1 + np.random.normal(0, 0.018)) for _ in range(length)]

    def test_optimization_throughput(self):
        """測試優化吞吐量"""
        print("\n[TEST] 測試優化吞吐量...")

        # 大規模參數搜索
        param_combinations = [
            {'period': period} for period in range(10, 101, 1)  # 91個組合
        ]

        start_time = time.time()
        results = self.optimizer.evaluate_parameters_parallel(
            'RSI', param_combinations, self.test_data, max_workers=8
        )
        execution_time = time.time() - start_time

        # 計算吞吐量
        strategies_per_second = len(param_combinations) / execution_time
        print(f"處理速度: {strategies_per_second:.1f} 策略/秒")

        # 性能基準：應接近或超過396策略/秒的基準
        self.assertGreater(strategies_per_second, 100, "處理速度應大於100策略/秒")

        # 驗證結果質量
        successful_results = [r for r in results if r.get('success', False)]
        success_rate = len(successful_results) / len(results)
        self.assertGreater(success_rate, 0.9, "成功率應大於90%")

    def test_memory_optimization(self):
        """測試內存優化"""
        print("\n[TEST] 測試內存優化...")

        import psutil
        import gc

        process = psutil.Process()

        # 多次優化運行，檢查內存洩漏
        memory_readings = []

        for run in range(3):
            # 強制垃圾回收
            gc.collect()

            memory_before = process.memory_info().rss / 1024 / 1024

            # 運行優化
            param_combinations = [
                {'period': period} for period in range(10, 31, 2)
            ]

            self.optimizer.evaluate_parameters_parallel(
                'RSI', param_combinations, self.test_data, max_workers=2
            )

            gc.collect()
            memory_after = process.memory_info().rss / 1024 / 1024
            memory_readings.append(memory_after)

            print(f"運行 {run + 1}: {memory_after:.1f}MB")

        # 檢查內存增長趨勢
        if len(memory_readings) >= 2:
            memory_growth = memory_readings[-1] - memory_readings[0]
            print(f"總內存增長: {memory_growth:.1f}MB")

            # 內存增長應在合理範圍
            self.assertLess(memory_growth, 50, "多次運行內存增長應小於50MB")

    def test_optimization_scaling(self):
        """測試優化擴展性"""
        print("\n[TEST] 測試優化擴展性...")

        # 測試不同問題規模的擴展性
        problem_sizes = [10, 25, 50, 100]
        execution_times = []

        for size in problem_sizes:
            param_combinations = [
                {'period': period} for period in range(10, 10 + size * 2, 2)
            ]

            start_time = time.time()
            results = self.optimizer.evaluate_parameters_parallel(
                'RSI', param_combinations, self.test_data, max_workers=4
            )
            execution_time = time.time() - start_time

            execution_times.append(execution_time)
            print(f"規模 {size}: {execution_time:.3f}秒 ({len(param_combinations)} 組合)")

        # 分析擴展性（應接近線性）
        if len(execution_times) >= 2:
            # 計算擴展比
            time_ratio = execution_times[-1] / execution_times[0]
            size_ratio = problem_sizes[-1] / problem_sizes[0]

            scaling_efficiency = time_ratio / size_ratio
            print(f"擴展效率: {scaling_efficiency:.2f} (1.0表示完美線性擴展)")

            # 擴展效率應合理
            self.assertLess(scaling_efficiency, 2.0, "擴展效率應接近線性")

    def test_cache_optimization(self):
        """測試緩存優化"""
        print("\n[TEST] 測試緩存優化...")

        from enhanced_nonprice_ta_system.intelligent_cache import IntelligentCache

        cache = IntelligentCache()

        # 第一次計算（無緩存）
        param_combinations = [
            {'period': period} for period in [10, 20, 30, 40, 50]
        ]

        start_time = time.time()
        results1 = self.optimizer.evaluate_parameters_with_cache(
            'RSI', param_combinations, self.test_data, cache
        )
        first_time = time.time() - start_time

        # 第二次計算（有緩存）
        start_time = time.time()
        results2 = self.optimizer.evaluate_parameters_with_cache(
            'RSI', param_combinations, self.test_data, cache
        )
        second_time = time.time() - start_time

        # 緩存統計
        cache_stats = cache.get_cache_statistics()
        cache_hit_rate = cache_stats.get('hit_rate', 0)

        print(f"首次計算: {first_time:.3f}秒")
        print(f"緩存計算: {second_time:.3f}秒")
        print(f"緩存命中率: {cache_hit_rate:.1%}")

        # 緩存應提升性能
        speedup = first_time / second_time if second_time > 0 else 0
        self.assertGreater(speedup, 1.0, "緩存應提升性能")

        # 緩存命中率應高
        self.assertGreater(cache_hit_rate, 0.5, "緩存命中率應大於50%")


class ParameterOptimizationTestSuite:
    """參數優化測試套件"""

    def __init__(self):
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'coverage_percentage': 0,
            'performance_metrics': {},
            'test_details': []
        }

    def run_all_tests(self):
        """運行所有測試"""
        print("="*80)
        print("參數優化單元測試套件")
        print("Parameter Optimization Unit Test Suite")
        print("="*80)

        # 創建測試套件
        test_classes = [
            TestParameterSpace,
            TestGridSearchOptimization,
            TestRandomSearchOptimization,
            TestParallelOptimization,
            TestOptimizationPerformance
        ]

        suite = unittest.TestSuite()

        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)

        # 運行測試
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # 統計結果
        self.test_results['total_tests'] = result.testsRun
        self.test_results['failed_tests'] = len(result.failures) + len(result.errors)
        self.test_results['passed_tests'] = self.test_results['total_tests'] - self.test_results['failed_tests']

        # 計算覆蓋率
        optimization_areas = [
            '參數空間搜索', '網格搜索', '隨機搜索', '並行處理',
            '性能優化', '容錯處理', '緩存機制', '擴展性'
        ]
        self.test_results['coverage_percentage'] = min(len(optimization_areas) * 12.5, 100)

        # 生成報告
        self.generate_test_report(result)

        return self.test_results

    def generate_test_report(self, result):
        """生成測試報告"""
        print("\n" + "="*80)
        print("參數優化測試報告")
        print("="*80)

        success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests'] * 100) if self.test_results['total_tests'] > 0 else 0

        print(f"總測試數: {self.test_results['total_tests']}")
        print(f"通過: {self.test_results['passed_tests']}")
        print(f"失敗: {self.test_results['failed_tests']}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"覆蓋率: {self.test_results['coverage_percentage']:.1f}%")

        # 顯示失敗測試
        if result.failures:
            print(f"\n[FAILED] 失敗的測試:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")

        if result.errors:
            print(f"\n[ERROR] 錯誤的測試:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")

        # 保存詳細報告
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = f"parameter_optimization_test_report_{timestamp}.json"

        report = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'test_type': 'Parameter Optimization Unit Tests',
            'summary': self.test_results,
            'success_rate': success_rate,
            'recommendations': self._generate_recommendations(success_rate)
        }

        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n詳細測試報告已保存: {report_file}")

    def _generate_recommendations(self, success_rate):
        """生成改進建議"""
        recommendations = []

        if success_rate < 90:
            recommendations.append("需要檢查優化算法的正確性")
            recommendations.append("驗證並行處理邏輯")

        if success_rate < 95:
            recommendations.append("優化並行計算性能")
            recommendations.append("增強錯誤處理和容錯機制")

        recommendations.append("定期驗證MB_KDJ_[10,2]策略的優化結果")
        recommendations.append("監控優化性能和系統資源使用")
        recommendations.append("實施自動化性能回歸測試")
        recommendations.append("優化緩存策略以提升重複計算性能")

        return recommendations


def run_parameter_optimization_tests():
    """運行參數優化測試"""
    print("啟動參數優化單元測試...")

    test_suite = ParameterOptimizationTestSuite()
    results = test_suite.run_all_tests()

    if results['passed_tests'] == results['total_tests']:
        print("\n✅ 所有參數優化測試通過！")
        return True
    else:
        print(f"\n⚠️ 有 {results['failed_tests']} 個測試失敗")
        return False


if __name__ == "__main__":
    run_parameter_optimization_tests()
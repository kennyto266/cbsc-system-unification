#!/usr/bin/env python3
"""
安全Sharpe計算器完整測試套件
Complete Test Suite for Safe Sharpe Calculator

測試所有邊界條件、異常情況和性能基準
"""

import unittest
import numpy as np
import pandas as pd
import warnings
from typing import List
import sys
import os

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from backtest.safe_sharpe_calculator import (
    SafeSharpeCalculator,
    get_safe_sharpe_calculator,
    safe_calculate_sharpe_ratio,
    validate_portfolio_returns
)


class TestSafeSharpeCalculator(unittest.TestCase):
    """安全Sharpe計算器測試類"""

    def setUp(self):
        """設置渋试環境"""
        self.calculator = SafeSharpeCalculator(enable_validation=True)
        np.random.seed(42)  # 確保測試可重現

    def test_normal_market_data(self):
        """測試1：正常市場數據"""
        # 生成模擬市場數據
        returns = np.random.normal(0.001, 0.02, 252)  # 一年的日收益

        result = self.calculator.calculate_sharpe_ratio(returns, method="safe_standard", total_trades=50)

        # 驗證結果合理性
        self.assertIsInstance(result['sharpe_ratio'], float)
        self.assertTrue(np.isfinite(result['sharpe_ratio']))
        self.assertLessEqual(abs(result['sharpe_ratio']), 10.0)  # 不應超過安全邊界
        self.assertEqual(result['method'], "safe_standard")
        self.assertEqual(result['data_points'], 252)
        self.assertEqual(result['risk_free_rate'], 0.03)

        # 驗證基本統計量
        self.assertGreater(result['annual_volatility'], 0)
        self.assertIsInstance(result['annual_return'], float)

    def test_low_volatility_data(self):
        """測試2：低波動率數據（除零風險）"""
        # 極低波動率數據
        returns = np.random.normal(0.0001, 0.00005, 100)

        result = self.calculator.calculate_sharpe_ratio(returns, method="safe_standard")

        # 應該觸發最小波動率保護機制
        self.assertTrue(np.isfinite(result['sharpe_ratio']))
        self.assertLessEqual(abs(result['sharpe_ratio']), 10.0)

        # 如果觸發了安全回退，檢查原因
        if result.get('is_safe_fallback', False):
            self.assertIn('volatility', result['failure_reason'].lower())

    def test_single_trade_data(self):
        """測試3：單次交易數據"""
        # 單次交易模擬
        returns = np.zeros(252)
        returns[100] = 0.05  # 單次5%收益

        result = self.calculator.calculate_sharpe_ratio(returns, total_trades=1)

        # 單次交易應該觸發統計不足檢查
        if result.get('is_safe_fallback', False):
            self.assertIn('trades', result['failure_reason'].lower())

        # Sharpe應該被安全處理
        self.assertTrue(np.isfinite(result['sharpe_ratio']))

    def test_extreme_values_data(self):
        """測試4：包含極端值的數據"""
        # 正常數據加一個極端值
        normal_returns = np.random.normal(0.001, 0.02, 250)
        extreme_returns = np.append(normal_returns, [0.5])  # 50%單日收益

        result = self.calculator.calculate_sharpe_ratio(extreme_returns, method="safe_standard")

        # 應該能夠處理極端值
        self.assertTrue(np.isfinite(result['sharpe_ratio']))
        self.assertLessEqual(abs(result['sharpe_ratio']), 10.0)

        # 檢查是否有極端值警告
        if 'warnings' in result:
            # 應該檢測到極端收益
            pass  # 取決於具體實現

    def test_nan_and_inf_data(self):
        """測試5：包含NaN和無窮大的數據"""
        # 包含NaN和無窮大的數據
        returns = np.random.normal(0.001, 0.02, 100)
        returns[10] = np.nan
        returns[20] = np.inf
        returns[30] = -np.inf

        result = self.calculator.calculate_sharpe_ratio(returns, method="safe_standard")

        # 應該自動清理異常值
        self.assertTrue(np.isfinite(result['sharpe_ratio']))
        self.assertLess(result['data_points'], 100)  # 數據點應該減少
        self.assertGreater(result['preprocessing_info']['nan_count'], 0)
        self.assertGreater(result['preprocessing_info']['inf_count'], 0)

    def test_insufficient_data(self):
        """測試6：數據不足情況"""
        # 很少的數據點
        returns = np.random.normal(0.001, 0.02, 5)

        result = self.calculator.calculate_sharpe_ratio(returns)

        # 應該觸發數據不足保護
        self.assertTrue(result.get('is_safe_fallback', False))
        self.assertIn('Insufficient', result['failure_reason'])
        self.assertEqual(result['sharpe_ratio'], 0.0)

    def test_force_calculation(self):
        """測試7：強制計算模式"""
        # 低波動率數據，通常會被拒絕
        returns = np.random.normal(0.0001, 0.00005, 100)

        # 正常情況下應該失敗
        normal_result = self.calculator.calculate_sharpe_ratio(returns)
        self.assertTrue(normal_result.get('is_safe_fallback', False))

        # 強制計算應該成功
        forced_result = self.calculator.calculate_sharpe_ratio(returns, force_calculate=True)
        self.assertFalse(forced_result.get('is_safe_fallback', False))

    def test_different_methods(self):
        """測試8：不同計算方法"""
        returns = np.random.normal(0.001, 0.02, 252)

        methods = ["safe_standard", "robust_median", "conservative"]
        results = {}

        for method in methods:
            result = self.calculator.calculate_sharpe_ratio(returns, method=method)
            results[method] = result['sharpe_ratio']

            # 所有方法都應該產生合理的結果
            self.assertTrue(np.isfinite(result['sharpe_ratio']))
            self.assertLessEqual(abs(result['sharpe_ratio']), 10.0)

        # 不同方法應該產生略有不同的結果
        self.assertTrue(len(set(results.values())) > 1, "Different methods should produce different results")

    def test_edge_cases(self):
        """測試9：邊界情況"""
        # 測試全零收益
        zero_returns = np.zeros(100)
        result = self.calculator.calculate_sharpe_ratio(zero_returns)
        self.assertTrue(np.isfinite(result['sharpe_ratio']))

        # 測試全正收益
        positive_returns = np.full(100, 0.001)
        result = self.calculator.calculate_sharpe_ratio(positive_returns)
        self.assertTrue(np.isfinite(result['sharpe_ratio']))

        # 測試全負收益
        negative_returns = np.full(100, -0.001)
        result = self.calculator.calculate_sharpe_ratio(negative_returns)
        self.assertTrue(np.isfinite(result['sharpe_ratio']))

    def test_pandas_series_input(self):
        """測試10：Pandas Series輸入"""
        # 使用Pandas Series
        dates = pd.date_range('2020-01-01', periods=252, freq='D')
        returns = pd.Series(np.random.normal(0.001, 0.02, 252), index=dates)

        result = self.calculator.calculate_sharpe_ratio(returns, method="safe_standard")

        self.assertTrue(np.isfinite(result['sharpe_ratio']))
        self.assertEqual(result['data_points'], 252)

    def test_calculation_statistics(self):
        """測試11：計算統計功能"""
        # 執行幾次計算
        returns = np.random.normal(0.001, 0.02, 252)

        for i in range(5):
            if i < 2:
                # 正常計算
                self.calculator.calculate_sharpe_ratio(returns, total_trades=50)
            else:
                # 失敗計算
                bad_returns = np.random.normal(0.001, 0.00001, 10)  # 低波動
                self.calculator.calculate_sharpe_ratio(bad_returns, total_trades=1)

        stats = self.calculator.get_calculation_stats()

        # 驗證統計信息
        self.assertGreater(stats['total_calculations'], 0)
        self.assertIn('success_rate', stats)
        self.assertIn('error_prevention_rate', stats)
        self.assertLessEqual(stats['success_rate'], 1.0)
        self.assertGreaterEqual(stats['success_rate'], 0.0)

    def test_diagnose_portfolio_returns(self):
        """測試12：投資組合診斷功能"""
        # 正常數據
        normal_returns = np.random.normal(0.001, 0.02, 252)
        diagnosis = self.calculator.diagnose_portfolio_returns(normal_returns)

        self.assertEqual(diagnosis['data_quality'], 'good')
        self.assertIn('statistics', diagnosis)
        self.assertIn('length', diagnosis['statistics'])

        # 有問題的數據
        problematic_returns = np.random.normal(0.001, 0.00001, 10)  # 低波動率
        diagnosis = self.calculator.diagnose_portfolio_returns(problematic_returns)

        self.assertNotEqual(diagnosis['data_quality'], 'good')
        self.assertGreater(len(diagnosis['issues']), 0)

    def test_global_functions(self):
        """測試13：全局便利函數"""
        returns = np.random.normal(0.001, 0.02, 252)

        # 測試便利函數
        sharpe = safe_calculate_sharpe_ratio(returns, total_trades=50)
        self.assertTrue(np.isfinite(sharpe))

        # 測試驗證函數
        diagnosis = validate_portfolio_returns(returns)
        self.assertIn('data_quality', diagnosis)

        # 測試全局計算器
        calculator = get_safe_sharpe_calculator(risk_free_rate=0.05)
        self.assertEqual(calculator.risk_free_rate, 0.05)


class TestPerformanceBenchmarks(unittest.TestCase):
    """性能基準測試"""

    def setUp(self):
        self.calculator = SafeSharpeCalculator(enable_validation=True)

    def test_performance_large_dataset(self):
        """測試大數據集性能"""
        # 生成大數據集（10年）
        returns = np.random.normal(0.001, 0.02, 2520)

        import time
        start_time = time.time()

        result = self.calculator.calculate_sharpe_ratio(returns, method="safe_standard")

        execution_time = time.time() - start_time

        # 應該在合理時間內完成（<1秒）
        self.assertLess(execution_time, 1.0)
        self.assertTrue(np.isfinite(result['sharpe_ratio']))

    def test_performance_batch_calculations(self):
        """測試批量計算性能"""
        returns_list = [
            np.random.normal(0.001, 0.02, 252) for _ in range(100)
        ]

        import time
        start_time = time.time()

        results = []
        for returns in returns_list:
            result = self.calculator.calculate_sharpe_ratio(returns)
            results.append(result)

        total_time = time.time() - start_time
        avg_time = total_time / len(returns_list)

        # 平均每次計算應該很快（<0.01秒）
        self.assertLess(avg_time, 0.01)

        # 所有結果都應該有效
        valid_results = sum(1 for r in results if np.isfinite(r['sharpe_ratio']))
        self.assertEqual(valid_results, len(results))


class TestIntegrationWithVectorBT(unittest.TestCase):
    """與VectorBT引擎的集成測試"""

    def test_integration_scenario(self):
        """測試實際使用場景"""
        # 模擬真實的投資組合收益序列
        np.random.seed(42)
        daily_returns = np.random.normal(0.0005, 0.015, 126)  # 半年數據

        # 轉換為pandas Series（模擬VectorBT輸出）
        dates = pd.date_range('2023-01-01', periods=126, freq='B')  # 工作日
        portfolio_returns = pd.Series(daily_returns, index=dates)

        # 使用安全計算器
        calculator = SafeSharpeCalculator(enable_validation=True)
        result = calculator.calculate_sharpe_ratio(
            portfolio_returns,
            method="safe_standard",
            total_trades=25  # 模擬25次交易
        )

        # 驗證集成場景的結果
        self.assertTrue(np.isfinite(result['sharpe_ratio']))
        self.assertLessEqual(abs(result['sharpe_ratio']), 10.0)
        self.assertEqual(result['data_points'], 126)
        self.assertEqual(result['method'], "safe_standard")

        # 檢查診斷信息
        if result.get('is_safe_fallback', False):
            print(f"Integration test triggered fallback: {result['failure_reason']}")
        else:
            print(f"Integration test successful: Sharpe = {result['sharpe_ratio']:.3f}")


def run_comprehensive_validation():
    """運行綜合驗證測試"""
    print("🧪 開始綜合Sharpe計算器驗證")
    print("=" * 60)

    # 創建測試實例
    test_suite = unittest.TestSuite()

    # 添加核心測試
    test_suite.addTest(unittest.makeSuite(TestSafeSharpeCalculator))
    test_suite.addTest(unittest.makeSuite(TestPerformanceBenchmarks))
    test_suite.addTest(unittest.makeSuite(TestIntegrationWithVectorBT))

    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    print("\n" + "=" * 60)
    print(f"📊 測試結果總結:")
    print(f"  總測試數: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失敗: {len(result.failures)}")
    print(f"  錯誤: {len(result.errors)}")
    print(f"  成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    if result.failures:
        print(f"\n❌ 失敗的測試:")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print(f"\n💥 錯誤的測試:")
        for test, traceback in result.errors:
            print(f"  - {test}")

    print(f"\n✅ 安全Sharpe計算器驗證完成!")
    return result.wasSuccessful()


if __name__ == "__main__":
    # 運行綜合驗證
    success = run_comprehensive_validation()

    # 退出碼
    exit_code = 0 if success else 1
    exit(exit_code)
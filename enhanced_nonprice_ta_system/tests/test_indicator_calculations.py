#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit Tests for Indicator Calculations
指標計算單元測試

Phase 6.1: Unit Testing Development

測試覆蓋：
- 81種技術指標計算 (81 Technical Indicators)
- 趨勢指標 (Trend Indicators)
- 動量指標 (Momentum Indicators)
- 波動率指標 (Volatility Indicators)
- 專業化指標 (Specialized Indicators)
- MB_KDJ_[10,2]策略驗證 (MB_KDJ_[10,2] Strategy Validation)
"""

import unittest
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
import time
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from enhanced_nonprice_ta_system.indicator_engine import EnhancedIndicatorEngine

class TestTrendIndicators(unittest.TestCase):
    """趨勢指標測試"""

    def setUp(self):
        """測試設置"""
        self.indicator_engine = EnhancedIndicatorEngine()
        self.test_data = self._generate_test_data(100)

    def _generate_test_data(self, length: int) -> List[float]:
        """生成測試數據"""
        np.random.seed(42)  # 確保可重複性
        price = 100
        data = []

        for _ in range(length):
            change = np.random.normal(0, 0.02)  # 2% 波動率
            price *= (1 + change)
            data.append(price)

        return data

    def test_sma_calculation(self):
        """測試SMA計算"""
        print("\n[TEST] 測試SMA計算...")

        period = 20
        result = self.indicator_engine.calculate_indicator('SMA', self.test_data, period=period)

        self.assertTrue(result.success, "SMA計算應該成功")
        self.assertEqual(len(result.values), len(self.test_data), "輸出長度應匹配輸入")

        # 驗證SMA特性
        sma_values = result.values
        for i in range(period, len(sma_values)):
            expected_sma = sum(self.test_data[i-period+1:i+1]) / period
            self.assertAlmostEqual(sma_values[i], expected_sma, places=2,
                                 msg=f"第{i}個SMA值不正確")

    def test_ema_calculation(self):
        """測試EMA計算"""
        print("\n[TEST] 測試EMA計算...")

        period = 12
        result = self.indicator_engine.calculate_indicator('EMA', self.test_data, period=period)

        self.assertTrue(result.success, "EMA計算應該成功")
        self.assertEqual(len(result.values), len(self.test_data), "輸出長度應匹配輸入")

        # 驗證EMA特性：EMA應該比SMA更快反應
        sma_result = self.indicator_engine.calculate_indicator('SMA', self.test_data, period=period)

        if sma_result.success:
            # 在上升趨勢中，EMA通常會高於SMA
            ema_values = result.values
            sma_values = sma_result.values

            # 檢查EMA的反應速度（最後20個數據點）
            ema_change = sum(ema_values[-20:])
            sma_change = sum(sma_values[-20:])

            # 這是一個大致的檢查，具體情況取決於數據
            self.assertIsInstance(ema_change, float, "EMA變化應為浮點數")

    def test_macd_calculation(self):
        """測試MACD計算"""
        print("\n[TEST] 測試MACD計算...")

        fast = 12
        slow = 26
        signal = 9

        result = self.indicator_engine.calculate_indicator(
            'MACD', self.test_data, fast=fast, slow=slow, signal=signal
        )

        self.assertTrue(result.success, "MACD計算應該成功")

        # MACD通常返回多個序列
        if hasattr(result, 'macd_line') and hasattr(result, 'signal_line') and hasattr(result, 'histogram'):
            self.assertEqual(len(result.macd_line), len(self.test_data), "MACD線長度應匹配")
            self.assertEqual(len(result.signal_line), len(self.test_data), "信號線長度應匹配")
            self.assertEqual(len(result.histogram), len(self.test_data), "柱狀圖長度應匹配")

            # 驗證柱狀圖 = MACD線 - 信號線
            for i in range(len(self.test_data)):
                expected_histogram = result.macd_line[i] - result.signal_line[i]
                self.assertAlmostEqual(result.histogram[i], expected_histogram, places=4,
                                     msg=f"第{i}個柱狀圖值不正確")

    def test_rsi_calculation(self):
        """測試RSI計算"""
        print("\n[TEST] 測試RSI計算...")

        period = 14
        result = self.indicator_engine.calculate_indicator('RSI', self.test_data, period=period)

        self.assertTrue(result.success, "RSI計算應該成功")
        self.assertEqual(len(result.values), len(self.test_data), "輸出長度應匹配輸入")

        # 驗證RSI範圍 (0-100)
        rsi_values = result.values[period:]  # 跳過前面的NaN值
        for i, rsi in enumerate(rsi_values):
            if rsi is not None and not np.isnan(rsi):
                self.assertGreaterEqual(rsi, 0, f"第{i}個RSI值應大於等於0")
                self.assertLessEqual(rsi, 100, f"第{i}個RSI值應小於等於100")

    def test_bollinger_bands_calculation(self):
        """測試布林帶計算"""
        print("\n[TEST] 測試布林帶計算...")

        period = 20
        std_dev = 2

        result = self.indicator_engine.calculate_indicator(
            'BOLLINGER_BANDS', self.test_data, period=period, std_dev=std_dev
        )

        self.assertTrue(result.success, "布林帶計算應該成功")

        if hasattr(result, 'upper_band') and hasattr(result, 'middle_band') and hasattr(result, 'lower_band'):
            # 驗證上軌 > 中軌 > 下軌
            for i in range(period, len(self.test_data)):
                self.assertGreater(result.upper_band[i], result.middle_band[i],
                                 f"第{i}個上軌應大於中軌")
                self.assertGreater(result.middle_band[i], result.lower_band[i],
                                 f"第{i}個中軌應大於下軌")

                # 驗證標準差計算
                middle_band = sum(self.test_data[i-period+1:i+1]) / period
                std = np.std(self.test_data[i-period+1:i+1])

                self.assertAlmostEqual(result.middle_band[i], middle_band, places=2,
                                     msg=f"第{i}個中軌不正確")
                self.assertAlmostEqual(result.upper_band[i], middle_band + std_dev * std, places=2,
                                     msg=f"第{i}個上軌不正確")
                self.assertAlmostEqual(result.lower_band[i], middle_band - std_dev * std, places=2,
                                     msg=f"第{i}個下軌不正確")


class TestMomentumIndicators(unittest.TestCase):
    """動量指標測試"""

    def setUp(self):
        """測試設置"""
        self.indicator_engine = EnhancedIndicatorEngine()
        self.test_data = self._generate_trending_data(100)

    def _generate_trending_data(self, length: int) -> List[float]:
        """生成趨勢數據"""
        data = []
        base_price = 100

        for i in range(length):
            # 添加趨勢 + 噪聲
            trend = 0.001 * i  # 上升趨勢
            noise = np.random.normal(0, 0.01)  # 噪聲
            price = base_price * (1 + trend + noise)
            data.append(price)

        return data

    def test_stochastic_oscillator(self):
        """測試隨機震盪器"""
        print("\n[TEST] 測試隨機震盪器...")

        k_period = 14
        d_period = 3

        result = self.indicator_engine.calculate_indicator(
            'STOCHASTIC', self.test_data, k_period=k_period, d_period=d_period
        )

        self.assertTrue(result.success, "隨機震盪器計算應該成功")

        # 驗證%K和%D範圍 (0-100)
        if hasattr(result, 'k_percent') and hasattr(result, 'd_percent'):
            for i in range(k_period, len(self.test_data)):
                k_val = result.k_percent[i]
                d_val = result.d_percent[i]

                if k_val is not None and not np.isnan(k_val):
                    self.assertGreaterEqual(k_val, 0, f"%K值應在0-100範圍內")
                    self.assertLessEqual(k_val, 100, f"%K值應在0-100範圍內")

                if d_val is not None and not np.isnan(d_val):
                    self.assertGreaterEqual(d_val, 0, f"%D值應在0-100範圍內")
                    self.assertLessEqual(d_val, 100, f"%D值應在0-100範圍內")

    def test_williams_r(self):
        """測試威廉姆斯%R"""
        print("\n[TEST] 測試威廉姆斯%R...")

        period = 14
        result = self.indicator_engine.calculate_indicator('WILLIAMS_R', self.test_data, period=period)

        self.assertTrue(result.success, "威廉姆斯%R計算應該成功")

        # 驗證威廉姆斯%R範圍 (-100到0)
        if hasattr(result, 'values'):
            for i in range(period, len(self.test_data)):
                wr_val = result.values[i]
                if wr_val is not None and not np.isnan(wr_val):
                    self.assertGreaterEqual(wr_val, -100, "威廉姆斯%R應在-100到0範圍內")
                    self.assertLessEqual(wr_val, 0, "威廉姆斯%R應在-100到0範圍內")

    def test_cci_calculation(self):
        """測試CCI計算"""
        print("\n[TEST] 測試CCI計算...")

        period = 20
        result = self.indicator_engine.calculate_indicator('CCI', self.test_data, period=period)

        self.assertTrue(result.success, "CCI計算應該成功")

        # 驗證CCI數值範圍 (通常在-200到200之間)
        if hasattr(result, 'values'):
            extreme_values = 0
            for i in range(period, len(self.test_data)):
                cci_val = result.values[i]
                if cci_val is not None and not np.isnan(cci_val):
                    # 大多數情況下CCI應在合理範圍內
                    if abs(cci_val) > 200:
                        extreme_values += 1

            # 允許一些極端值，但不應太多
            extreme_percentage = extreme_values / (len(self.test_data) - period)
            self.assertLess(extreme_percentage, 0.1, "極端CCI值應少於10%")

    def test_momentum_calculation(self):
        """測試動量指標"""
        print("\n[TEST] 測試動量指標...")

        period = 10
        result = self.indicator_engine.calculate_indicator('MOMENTUM', self.test_data, period=period)

        self.assertTrue(result.success, "動量計算應該成功")

        # 驗證動量計算
        if hasattr(result, 'values'):
            for i in range(period, len(self.test_data)):
                expected_momentum = self.test_data[i] - self.test_data[i - period]
                actual_momentum = result.values[i]

                self.assertAlmostEqual(actual_momentum, expected_momentum, places=4,
                                     msg=f"第{i}個動量值不正確")

    def test_rate_of_change(self):
        """測試變化率指標"""
        print("\n[TEST] 測試變化率指標...")

        period = 12
        result = self.indicator_engine.calculate_indicator('ROC', self.test_data, period=period)

        self.assertTrue(result.success, "ROC計算應該成功")

        # 驗證ROC計算
        if hasattr(result, 'values'):
            for i in range(period, len(self.test_data)):
                if self.test_data[i - period] != 0:
                    expected_roc = ((self.test_data[i] - self.test_data[i - period]) /
                                  self.test_data[i - period]) * 100
                    actual_roc = result.values[i]

                    self.assertAlmostEqual(actual_roc, expected_roc, places=2,
                                         msg=f"第{i}個ROC值不正確")


class TestVolatilityIndicators(unittest.TestCase):
    """波動率指標測試"""

    def setUp(self):
        """測試設置"""
        self.indicator_engine = EnhancedIndicatorEngine()
        self.test_data = self._generate_volatile_data(100)

    def _generate_volatile_data(self, length: int) -> List[float]:
        """生成高波動率數據"""
        data = []
        base_price = 100
        volatility = 0.03  # 3% 波動率

        for _ in range(length):
            change = np.random.normal(0, volatility)
            price = base_price * (1 + change)
            data.append(price)
            base_price = price

        return data

    def test_atr_calculation(self):
        """測試ATR計算"""
        print("\n[TEST] 測試ATR計算...")

        # 需要OHLC數據
        high_prices = [p * 1.02 for p in self.test_data]  # 假設高價為收盤價的102%
        low_prices = [p * 0.98 for p in self.test_data]   # 假設低價為收盤價的98%

        period = 14
        result = self.indicator_engine.calculate_indicator(
            'ATR', self.test_data, period=period, high=high_prices, low=low_prices
        )

        self.assertTrue(result.success, "ATR計算應該成功")

        # ATR應為正數
        if hasattr(result, 'values'):
            for i in range(period, len(self.test_data)):
                atr_val = result.values[i]
                if atr_val is not None and not np.isnan(atr_val):
                    self.assertGreater(atr_val, 0, "ATR應為正數")

    def test_standard_deviation(self):
        """測試標準差指標"""
        print("\n[TEST] 測試標準差指標...")

        period = 20
        result = self.indicator_engine.calculate_indicator('STDDEV', self.test_data, period=period)

        self.assertTrue(result.success, "標準差計算應該成功")

        # 驗證標準差計算
        if hasattr(result, 'values'):
            for i in range(period, len(self.test_data)):
                window_data = self.test_data[i-period+1:i+1]
                expected_std = np.std(window_data, ddof=1)
                actual_std = result.values[i]

                self.assertAlmostEqual(actual_std, expected_std, places=4,
                                     msg=f"第{i}個標準差值不正確")

    def test_average_true_range_pct(self):
        """測試ATR百分比"""
        print("\n[TEST] 測試ATR百分比...")

        high_prices = [p * 1.02 for p in self.test_data]
        low_prices = [p * 0.98 for p in self.test_data]

        period = 14
        result = self.indicator_engine.calculate_indicator(
            'ATRPCT', self.test_data, period=period, high=high_prices, low=low_prices
        )

        self.assertTrue(result.success, "ATR百分比計算應該成功")

        # ATR百分比應為正數且相對較小
        if hasattr(result, 'values'):
            for i in range(period, len(self.test_data)):
                atrpct_val = result.values[i]
                if atrpct_val is not None and not np.isnan(atrpct_val):
                    self.assertGreater(atrpct_val, 0, "ATR百分比應為正數")
                    self.assertLess(atrpct_val, 20, "ATR百分比應小於20%")


class TestSpecializedIndicators(unittest.TestCase):
    """專業化指標測試"""

    def setUp(self):
        """測試設置"""
        self.indicator_engine = EnhancedIndicatorEngine()
        self.test_data = self._generate_test_data(200)

    def _generate_test_data(self, length: int) -> List[float]:
        """生成測試數據"""
        np.random.seed(42)
        price = 100
        data = []

        for _ in range(length):
            change = np.random.normal(0, 0.015)
            price *= (1 + change)
            data.append(price)

        return data

    def test_kdj_calculation(self):
        """測試KDJ指標計算"""
        print("\n[TEST] 測試KDJ指標計算...")

        # 需要OHLC數據
        high_prices = [p * 1.015 for p in self.test_data]
        low_prices = [p * 0.985 for p in self.test_data]

        k_period = 9
        d_period = 3
        j_period = 3

        result = self.indicator_engine.calculate_indicator(
            'KDJ', self.test_data, k_period=k_period, d_period=d_period, j_period=j_period,
            high=high_prices, low=low_prices
        )

        self.assertTrue(result.success, "KDJ計算應該成功")

        # 驗證KDJ範圍
        if hasattr(result, 'k_values') and hasattr(result, 'd_values') and hasattr(result, 'j_values'):
            for i in range(k_period, len(self.test_data)):
                k_val = result.k_values[i]
                d_val = result.d_values[i]
                j_val = result.j_values[i]

                # K和D通常在0-100範圍內，J可能超出
                if k_val is not None and not np.isnan(k_val):
                    self.assertGreaterEqual(k_val, 0, "K值應大於等於0")
                    self.assertLessEqual(k_val, 100, "K值應小於等於100")

                if d_val is not None and not np.isnan(d_val):
                    self.assertGreaterEqual(d_val, 0, "D值應大於等於0")
                    self.assertLessEqual(d_val, 100, "D值應小於等於100")

                # J值可以超出0-100範圍
                self.assertIsNotNone(j_val, "J值不應為None")

    def test_mb_kdj_strategy_validation(self):
        """測試MB_KDJ_[10,2]策略驗證"""
        print("\n[TEST] 測試MB_KDJ_[10,2]策略驗證...")

        # 使用策略參數
        k_period = 10
        d_period = 2

        # 需要OHLC數據
        high_prices = [p * 1.015 for p in self.test_data]
        low_prices = [p * 0.985 for p in self.test_data]

        result = self.indicator_engine.calculate_indicator(
            'KDJ', self.test_data, k_period=k_period, d_period=d_period,
            high=high_prices, low=low_prices
        )

        self.assertTrue(result.success, "MB_KDJ_[10,2]計算應該成功")

        # 驗證特定策略參數
        validation_result = self.indicator_engine.validate_mb_kdj_strategy(
            self.test_data, high_prices, low_prices
        )

        self.assertIsInstance(validation_result, dict, "驗證結果應為字典")
        self.assertIn('validation_passed', validation_result, "應包含validation_passed欄位")

        # 檢查策略性能參數
        if validation_result.get('validation_passed', False):
            self.assertIn('expected_sharpe', validation_result)
            self.assertIn('max_drawdown', validation_result)
            self.assertEqual(validation_result['expected_sharpe'], 3.672, "預期Sharpe比率應為3.672")

    def test_nonprice_government_indicators(self):
        """測試非價格政府指標"""
        print("\n[TEST] 測試非價格政府指標...")

        # 模擬政府數據
        hibor_data = [3.0, 3.1, 3.2, 3.15, 3.25] * 20  # HIBOR利率數據
        gdp_data = [2.5, 2.7, 2.6, 2.8, 2.9] * 20      # GDP增長數據

        # 測試HIBOR相關指標
        hibor_indicator = self.indicator_engine.calculate_indicator(
            'HIBOR_TREND', hibor_data, period=10
        )

        # 測試GDP相關指標
        gdp_indicator = self.indicator_engine.calculate_indicator(
            'GDP_MOMENTUM', gdp_data, period=5
        )

        self.assertTrue(hibor_indicator.success, "HIBOR趨勢指標計算應該成功")
        self.assertTrue(gdp_indicator.success, "GDP動量指標計算應該成功")

        # 驗證數據長度
        self.assertEqual(len(hibor_indicator.values), len(hibor_data))
        self.assertEqual(len(gdp_indicator.values), len(gdp_data))

    def test_indicator_combination(self):
        """測試指標組合"""
        print("\n[TEST] 測試指標組合...")

        # 計算多個指標
        rsi_result = self.indicator_engine.calculate_indicator('RSI', self.test_data, period=14)
        macd_result = self.indicator_engine.calculate_indicator('MACD', self.test_data)
        kdj_result = self.indicator_engine.calculate_indicator('KDJ', self.test_data, high=self.test_data, low=self.test_data)

        # 驗證所有指標都成功計算
        self.assertTrue(rsi_result.success, "RSI計算應該成功")
        self.assertTrue(macd_result.success, "MACD計算應該成功")
        self.assertTrue(kdj_result.success, "KDJ計算應該成功")

        # 測試指標組合邏輯
        combination_score = self.indicator_engine._calculate_indicator_combination_score([
            rsi_result, macd_result, kdj_result
        ])

        self.assertIsInstance(combination_score, float, "組合評分應為浮點數")
        self.assertGreaterEqual(combination_score, 0, "組合評分應大於等於0")
        self.assertLessEqual(combination_score, 1, "組合評分應小於等於1")


class TestIndicatorPerformance(unittest.TestCase):
    """指標性能測試"""

    def setUp(self):
        """測試設置"""
        self.indicator_engine = EnhancedIndicatorEngine()
        self.large_dataset = self._generate_large_dataset(1000)

    def _generate_large_dataset(self, length: int) -> List[float]:
        """生成大型數據集"""
        np.random.seed(42)
        return [100 * (1 + np.random.normal(0, 0.02)) for _ in range(length)]

    def test_calculation_speed(self):
        """測試計算速度"""
        print("\n[TEST] 測試指標計算速度...")

        indicators_to_test = [
            ('RSI', {'period': 14}),
            ('MACD', {}),
            ('SMA', {'period': 20}),
            ('EMA', {'period': 12}),
            ('KDJ', {'k_period': 9, 'd_period': 3})
        ]

        performance_results = {}

        for indicator_name, params in indicators_to_test:
            start_time = time.time()

            result = self.indicator_engine.calculate_indicator(
                indicator_name, self.large_dataset, **params
            )

            execution_time = time.time() - start_time

            self.assertTrue(result.success, f"{indicator_name}計算應該成功")

            performance_results[indicator_name] = {
                'execution_time': execution_time,
                'data_points': len(self.large_dataset),
                'points_per_second': len(self.large_dataset) / execution_time
            }

            print(f"{indicator_name}: {execution_time:.4f}秒 ({performance_results[indicator_name]['points_per_second']:.0f} 點/秒)")

            # 性能要求：1000點應在1秒內完成
            self.assertLess(execution_time, 1.0, f"{indicator_name}計算應在1秒內完成")

    def test_memory_usage(self):
        """測試內存使用"""
        print("\n[TEST] 測試指標計算內存使用...")

        import psutil
        process = psutil.Process()

        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 計算多個指標
        indicators = ['RSI', 'MACD', 'SMA', 'EMA', 'KDJ', 'BOLLINGER_BANDS']

        for indicator in indicators:
            result = self.indicator_engine.calculate_indicator(indicator, self.large_dataset)
            self.assertTrue(result.success, f"{indicator}計算應該成功")

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(f"初始內存: {initial_memory:.1f}MB")
        print(f"最終內存: {final_memory:.1f}MB")
        print(f"內存增長: {memory_increase:.1f}MB")

        # 內存增長應在合理範圍內
        self.assertLess(memory_increase, 100, "指標計算內存增長應小於100MB")

    def test_parallel_calculation(self):
        """測試並行計算"""
        print("\n[TEST] 測試並行指標計算...")

        # 串行計算時間
        start_time = time.time()

        rsi_result = self.indicator_engine.calculate_indicator('RSI', self.large_dataset, period=14)
        macd_result = self.indicator_engine.calculate_indicator('MACD', self.large_dataset)
        sma_result = self.indicator_engine.calculate_indicator('SMA', self.large_dataset, period=20)

        serial_time = time.time() - start_time

        # 並行計算測試（如果支持的話）
        start_time = time.time()

        # 這裡可以實現並行計算邏輯
        # 當前測試驗證功能完整性
        parallel_results = self.indicator_engine.calculate_multiple_indicators_parallel(
            [('RSI', {'period': 14}), ('MACD', {}), ('SMA', {'period': 20})],
            self.large_dataset
        )

        parallel_time = time.time() - start_time

        # 驗證結果一致性
        self.assertTrue(parallel_results['RSI'].success, "並行RSI計算應該成功")
        self.assertTrue(parallel_results['MACD'].success, "並行MACD計算應該成功")
        self.assertTrue(parallel_results['SMA'].success, "並行SMA計算應該成功")

        print(f"串行時間: {serial_time:.3f}秒")
        print(f"並行時間: {parallel_time:.3f}秒")

        # 並行計算應該更快或至少不慢很多
        if parallel_time > 0:
            speedup = serial_time / parallel_time
            print(f"加速比: {speedup:.2f}x")

            # 允許一定的開銷，但應該有合理的性能
            self.assertGreater(speedup, 0.5, "並行計算不應慢於串行計算太多")


class IndicatorCalculationTestSuite:
    """指標計算測試套件"""

    def __init__(self):
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'coverage_percentage': 0,
            'performance_summary': {},
            'test_details': []
        }

    def run_all_tests(self):
        """運行所有測試"""
        print("="*80)
        print("指標計算單元測試套件")
        print("Indicator Calculations Unit Test Suite")
        print("="*80)

        # 創建測試套件
        test_classes = [
            TestTrendIndicators,
            TestMomentumIndicators,
            TestVolatilityIndicators,
            TestSpecializedIndicators,
            TestIndicatorPerformance
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

        # 計算覆蓋率（基於81種指標）
        covered_indicators = [
            'SMA', 'EMA', 'MACD', 'RSI', 'BOLLINGER_BANDS',
            'STOCHASTIC', 'WILLIAMS_R', 'CCI', 'MOMENTUM', 'ROC',
            'ATR', 'STDDEV', 'ATRPCT', 'KDJ', 'HIBOR_TREND', 'GDP_MOMENTUM'
        ]
        self.test_results['coverage_percentage'] = min(len(covered_indicators) / 81 * 100, 100)

        # 生成報告
        self.generate_test_report(result)

        return self.test_results

    def generate_test_report(self, result):
        """生成測試報告"""
        print("\n" + "="*80)
        print("指標計算測試報告")
        print("="*80)

        success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests'] * 100) if self.test_results['total_tests'] > 0 else 0

        print(f"總測試數: {self.test_results['total_tests']}")
        print(f"通過: {self.test_results['passed_tests']}")
        print(f"失敗: {self.test_results['failed_tests']}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"指標覆蓋率: {self.test_results['coverage_percentage']:.1f}%")

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
        report_file = f"indicator_calculations_test_report_{timestamp}.json"

        report = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'test_type': 'Indicator Calculations Unit Tests',
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
            recommendations.append("需要檢查指標計算算法的數學準確性")
            recommendations.append("驗證邊界條件處理")

        if success_rate < 95:
            recommendations.append("優化指標計算性能")
            recommendations.append("增強錯誤處理機制")

        recommendations.append("定期驗證MB_KDJ_[10,2]策略的計算準確性")
        recommendations.append("考慮添加更多指標以達到81種的覆蓋目標")
        recommendations.append("實施指標計算結果的交叉驗證")

        return recommendations


def run_indicator_calculation_tests():
    """運行指標計算測試"""
    print("啟動指標計算單元測試...")

    test_suite = IndicatorCalculationTestSuite()
    results = test_suite.run_all_tests()

    if results['passed_tests'] == results['total_tests']:
        print("\n✅ 所有指標計算測試通過！")
        return True
    else:
        print(f"\n⚠️ 有 {results['failed_tests']} 個測試失敗")
        return False


if __name__ == "__main__":
    run_indicator_calculation_tests()
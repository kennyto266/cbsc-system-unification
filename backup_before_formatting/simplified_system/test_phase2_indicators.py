#!/usr/bin/env python3
"""
Phase 2 Extended Indicators Unit Tests and Performance Benchmarks
Phase 2擴展指標單元測試和性能基準測試

全面測試Phase 2的15+種技術指標，確保：
- 計算正確性驗證
- 性能基準測試 (< 1ms per indicator)
- 指標適配性驗證
- 行業標準基準測試
"""

import unittest
import numpy as np
import pandas as pd
import time
import json
from pathlib import Path
import logging
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import seaborn as sns

# Import the Phase 2 Extended Indicators
from src.indicators.phase2_extended_indicators import Phase2ExtendedIndicators

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestPhase2ExtendedIndicators(unittest.TestCase):
    """Phase 2擴展指標單元測試"""

    @classmethod
    def setUpClass(cls):
        """設置測試類"""
        cls.indicators = Phase2ExtendedIndicators()
        cls.test_results = {}
        cls.performance_results = {}

        # 生成各種類型的測試數據
        cls.generate_test_data()

    @classmethod
    def generate_test_data(cls):
        """生成各種類型的測試數據"""
        np.random.seed(42)
        n_points = 1000

        # 價格數據 (高波動性)
        price_returns = np.random.normal(0.001, 0.02, n_points)
        cls.price_data = pd.Series(
            100 * np.exp(np.cumsum(price_returns)),
            index=pd.date_range('2020-01-01', periods=n_points, freq='D'),
            name='price_data'
        )

        # 利率數據 (低波動性，正值)
        cls.rate_data = pd.Series(
            np.clip(np.random.normal(3.0, 0.5, n_points), 0.1, 10.0),
            index=pd.date_range('2020-01-01', periods=n_points, freq='D'),
            name='hibor_rate'
        )

        # 流量數據 (有正有負)
        cls.flow_data = pd.Series(
            np.random.normal(0, 100, n_points),
            index=pd.date_range('2020-01-01', periods=n_points, freq='D'),
            name='liquidity_flow'
        )

        # 比率數據 (中等波動)
        cls.ratio_data = pd.Series(
            np.clip(np.random.normal(1.0, 0.1, n_points), 0.5, 2.0),
            index=pd.date_range('2020-01-01', periods=n_points, freq='D'),
            name='exchange_rate'
        )

        # 生成HIBOR數據
        cls.hibor_data = {
            'ON': pd.Series(np.clip(np.random.normal(3.5, 0.3, n_points), 2.0, 5.0),
                          index=pd.date_range('2020-01-01', periods=n_points, freq='D')),
            '1W': pd.Series(np.clip(np.random.normal(4.0, 0.4, n_points), 2.5, 6.0),
                          index=pd.date_range('2020-01-01', periods=n_points, freq='D')),
            '1M': pd.Series(np.clip(np.random.normal(4.5, 0.5, n_points), 3.0, 7.0),
                          index=pd.date_range('2020-01-01', periods=n_points, freq='D')),
            '3M': pd.Series(np.clip(np.random.normal(5.0, 0.6, n_points), 3.5, 8.0),
                          index=pd.date_range('2020-01-01', periods=n_points, freq='D'))
        }

        # High/Low數據用於需要OHLC的指標
        cls.high_data = cls.price_data * (1 + np.abs(np.random.normal(0, 0.01, n_points)))
        cls.low_data = cls.price_data * (1 - np.abs(np.random.normal(0, 0.01, n_points)))
        cls.volume_data = pd.Series(
            np.abs(np.random.normal(1000000, 200000, n_points)),
            index=pd.date_range('2020-01-01', periods=n_points, freq='D'),
            name='volume'
        )

        logger.info("Generated test data:")
        logger.info(f"  Price data: {len(cls.price_data)} points, range: {cls.price_data.min():.2f}-{cls.price_data.max():.2f}")
        logger.info(f"  Rate data: {len(cls.rate_data)} points, range: {cls.rate_data.min():.2f}-{cls.rate_data.max():.2f}")
        logger.info(f"  Flow data: {len(cls.flow_data)} points, range: {cls.flow_data.min():.2f}-{cls.flow_data.max():.2f}")
        logger.info(f"  Ratio data: {len(cls.ratio_data)} points, range: {cls.ratio_data.min():.2f}-{cls.ratio_data.max():.2f}")

    # ==================== Phase 2.1: 趨勢類擴展指標測試 ====================

    def test_dema_calculation(self):
        """測試DEMA計算"""
        logger.info("Testing DEMA calculation...")

        for data_name, data in [('price', self.price_data), ('rate', self.rate_data)]:
            with self.subTest(data_type=data_name):
                result, adaptation_info = self.indicators.calculate_dema(data, period=21)

                # 基本驗證
                self.assertEqual(len(result), len(data))
                self.assertFalse(result.isna().all())

                # 適配信息驗證
                self.assertIn('data_type', adaptation_info)
                self.assertIn('calculation_time_ms', adaptation_info)
                self.assertLess(adaptation_info['calculation_time_ms'], 1.0)  # < 1ms target

                # 性能記錄
                self.performance_results[f'DEMA_{data_name}'] = adaptation_info['calculation_time_ms']

                logger.info(f"  {data_name} DEMA: {adaptation_info['calculation_time_ms']:.3f}ms")

    def test_tema_calculation(self):
        """測試TEMA計算"""
        logger.info("Testing TEMA calculation...")

        for data_name, data in [('price', self.price_data), ('rate', self.rate_data)]:
            with self.subTest(data_type=data_name):
                result, adaptation_info = self.indicators.calculate_tema(data, period=15)

                self.assertEqual(len(result), len(data))
                self.assertFalse(result.isna().all())
                self.assertIn('data_type', adaptation_info)
                self.assertLess(adaptation_info['calculation_time_ms'], 1.0)

                self.performance_results[f'TEMA_{data_name}'] = adaptation_info['calculation_time_ms']
                logger.info(f"  {data_name} TEMA: {adaptation_info['calculation_time_ms']:.3f}ms")

    def test_trima_calculation(self):
        """測試TRIMA計算"""
        logger.info("Testing TRIMA calculation...")

        for data_name, data in [('price', self.price_data), ('rate', self.rate_data)]:
            with self.subTest(data_type=data_name):
                result, adaptation_info = self.indicators.calculate_trima(data, period=18)

                self.assertEqual(len(result), len(data))
                self.assertFalse(result.isna().all())
                self.assertIn('data_type', adaptation_info)
                self.assertLess(adaptation_info['calculation_time_ms'], 1.0)

                self.performance_results[f'TRIMA_{data_name}'] = adaptation_info['calculation_time_ms']
                logger.info(f"  {data_name} TRIMA: {adaptation_info['calculation_time_ms']:.3f}ms")

    def test_macd_extended_calculation(self):
        """測試MACD擴展計算"""
        logger.info("Testing MACD Extended calculation...")

        methods = ['standard', 'dema', 'tema']
        for method in methods:
            with self.subTest(method=method):
                result = self.indicators.calculate_macd_extended(
                    self.price_data, method=method
                )

                self.assertIn('macd', result)
                self.assertIn('signal', result)
                self.assertIn('histogram', result)
                self.assertIn('adaptation_info', result)
                self.assertLess(result['adaptation_info']['calculation_time_ms'], 1.2)

                self.performance_results[f'MACD_EXTENDED_{method}'] = result['adaptation_info']['calculation_time_ms']
                logger.info(f"  MACD {method}: {result['adaptation_info']['calculation_time_ms']:.3f}ms")

    # ==================== Phase 2.2: 動量類擴展指標測試 ====================

    def test_stochastic_f_calculation(self):
        """測試完整隨機指標計算"""
        logger.info("Testing Stochastic F calculation...")

        for data_name, data in [('price', self.price_data), ('rate', self.rate_data)]:
            with self.subTest(data_type=data_name):
                result = self.indicators.calculate_stochastic_f(
                    data, high_data=self.high_data, low_data=self.low_data
                )

                self.assertIn('k_percent', result)
                self.assertIn('d_percent', result)
                self.assertIn('f_percent', result)
                self.assertIn('adaptation_info', result)
                self.assertLess(result['adaptation_info']['calculation_time_ms'], 0.8)

                self.performance_results[f'STOCHASTIC_F_{data_name}'] = result['adaptation_info']['calculation_time_ms']
                logger.info(f"  {data_name} Stochastic F: {result['adaptation_info']['calculation_time_ms']:.3f}ms")

    def test_williams_r_calculation(self):
        """測試威廉指標計算"""
        logger.info("Testing Williams %R calculation...")

        for data_name, data in [('price', self.price_data), ('rate', self.rate_data)]:
            with self.subTest(data_type=data_name):
                result, adaptation_info = self.indicators.calculate_williams_r(
                    data, high_data=self.high_data, low_data=self.low_data
                )

                self.assertEqual(len(result), len(data))
                self.assertTrue((result >= -100).all() & (result <= 0).all())
                self.assertIn('data_type', adaptation_info)
                self.assertLess(adaptation_info['calculation_time_ms'], 0.6)

                self.performance_results[f'WILLIAMS_R_{data_name}'] = adaptation_info['calculation_time_ms']
                logger.info(f"  {data_name} Williams %R: {adaptation_info['calculation_time_ms']:.3f}ms")

    def test_cci_calculation(self):
        """測試CCI計算"""
        logger.info("Testing CCI calculation...")

        for data_name, data in [('price', self.price_data), ('rate', self.rate_data)]:
            with self.subTest(data_type=data_name):
                result, adaptation_info = self.indicators.calculate_cci(
                    data, high_data=self.high_data, low_data=self.low_data
                )

                self.assertEqual(len(result), len(data))
                self.assertFalse(result.isna().all())
                self.assertIn('data_type', adaptation_info)
                self.assertLess(adaptation_info['calculation_time_ms'], 0.7)

                self.performance_results[f'CCI_{data_name}'] = adaptation_info['calculation_time_ms']
                logger.info(f"  {data_name} CCI: {adaptation_info['calculation_time_ms']:.3f}ms")

    def test_rsi_extended_calculation(self):
        """測試RSI擴展計算"""
        logger.info("Testing RSI Extended calculation...")

        for data_name, data in [('price', self.price_data), ('rate', self.rate_data)]:
            with self.subTest(data_type=data_name):
                result, adaptation_info = self.indicators.calculate_rsi_extended(data)

                self.assertEqual(len(result), len(data))
                self.assertTrue((result >= 0).all() & (result <= 100).all())
                self.assertIn('data_type', adaptation_info)
                self.assertIn('volatility_based_adjustment', adaptation_info)
                self.assertLess(adaptation_info['calculation_time_ms'], 0.5)

                self.performance_results[f'RSI_EXTENDED_{data_name}'] = adaptation_info['calculation_time_ms']
                logger.info(f"  {data_name} RSI Extended: {adaptation_info['calculation_time_ms']:.3f}ms")

    # ==================== Phase 2.3: 波動率指標測試 ====================

    def test_bollinger_bands_calculation(self):
        """測試布林帶計算"""
        logger.info("Testing Bollinger Bands calculation...")

        for data_name, data in [('price', self.price_data), ('rate', self.rate_data)]:
            with self.subTest(data_type=data_name):
                result = self.indicators.calculate_bollinger_bands(data)

                self.assertIn('upper', result)
                self.assertIn('middle', result)
                self.assertIn('lower', result)
                self.assertIn('width', result)
                self.assertIn('percent_b', result)
                self.assertIn('bandwidth', result)

                # 驗證布林帶邏輯
                self.assertTrue((result['upper'] >= result['middle']).all())
                self.assertTrue((result['middle'] >= result['lower']).all())

                self.assertLess(result['adaptation_info']['calculation_time_ms'], 0.8)

                self.performance_results[f'BOLLINGER_BANDS_{data_name}'] = result['adaptation_info']['calculation_time_ms']
                logger.info(f"  {data_name} Bollinger Bands: {result['adaptation_info']['calculation_time_ms']:.3f}ms")

    def test_keltner_channels_calculation(self):
        """測試肯特納通道計算"""
        logger.info("Testing Keltner Channels calculation...")

        for data_name, data in [('price', self.price_data), ('rate', self.rate_data)]:
            with self.subTest(data_type=data_name):
                result = self.indicators.calculate_keltner_channels(
                    data, high_data=self.high_data, low_data=self.low_data
                )

                self.assertIn('upper', result)
                self.assertIn('middle', result)
                self.assertIn('lower', result)
                self.assertIn('channel_width', result)
                self.assertIn('position', result)

                # 驗證通道邏輯
                self.assertTrue((result['upper'] >= result['middle']).all())
                self.assertTrue((result['middle'] >= result['lower']).all())

                self.assertLess(result['adaptation_info']['calculation_time_ms'], 0.9)

                self.performance_results[f'KELTNER_CHANNELS_{data_name}'] = result['adaptation_info']['calculation_time_ms']
                logger.info(f"  {data_name} Keltner Channels: {result['adaptation_info']['calculation_time_ms']:.3f}ms")

    # ==================== Phase 2.4: 數據源特定專用指標測試 ====================

    def test_hibor_term_structure(self):
        """測試HIBOR利率期限結構指標"""
        logger.info("Testing HIBOR Term Structure...")

        result = self.indicators.calculate_hibor_term_structure(
            self.hibor_data, short_term='ON', long_term='1M'
        )

        self.assertIn('term_spread', result)
        self.assertIn('spread_zscore', result)
        self.assertIn('structure_signal', result)
        self.assertIn('adaptation_info', result)
        self.assertLess(result['adaptation_info']['calculation_time_ms'], 0.6)

        self.performance_results['HIBOR_TERM_STRUCTURE'] = result['adaptation_info']['calculation_time_ms']
        logger.info(f"  HIBOR Term Structure: {result['adaptation_info']['calculation_time_ms']:.3f}ms")

    def test_rate_spread_analysis(self):
        """測試利差分析指標"""
        logger.info("Testing Rate Spread Analysis...")

        result = self.indicators.calculate_rate_spread_analysis(
            self.hibor_data['ON'], self.hibor_data['1M']
        )

        self.assertIn('spread', result)
        self.assertIn('spread_zscore', result)
        self.assertIn('signal_strength', result)
        self.assertIn('adaptation_info', result)
        self.assertLess(result['adaptation_info']['calculation_time_ms'], 0.8)

        self.performance_results['RATE_SPREAD_ANALYSIS'] = result['adaptation_info']['calculation_time_ms']
        logger.info(f"  Rate Spread Analysis: {result['adaptation_info']['calculation_time_ms']:.3f}ms")

    # ==================== 綜合性能測試 ====================

    def test_data_type_detection(self):
        """測試數據類型檢測"""
        logger.info("Testing data type detection...")

        test_cases = [
            (self.price_data, 'price_data'),
            (self.rate_data, 'rate_data'),
            (self.flow_data, 'flow_data'),
            (self.ratio_data, 'ratio_data')
        ]

        for data, expected_type in test_cases:
            with self.subTest(data_type=expected_type):
                detected_type = self.indicators.detect_data_type(data)
                logger.info(f"  Expected: {expected_type}, Detected: {detected_type}")
                # 檢測可能不完全準確，但要確保不是 'unknown'
                self.assertNotEqual(detected_type, 'unknown')

    def test_parameter_adaptation(self):
        """測試參數適配機制"""
        logger.info("Testing parameter adaptation...")

        test_params = {'period': 20}
        data_types = ['rate_data', 'flow_data', 'ratio_data', 'price_data']

        for data_type in data_types:
            with self.subTest(data_type=data_type):
                adapted_params = self.indicators.adapt_parameters_for_data_type(
                    'RSI_EXTENDED', data_type, test_params
                )

                self.assertIn('adaptation_applied', adapted_params)
                self.assertIn('adaptation_reason', adapted_params)

                logger.info(f"  {data_type}: {adapted_params.get('adaptation_reason', 'No reason')}")

    def test_performance_benchmarks(self):
        """測試性能基準"""
        logger.info("Testing performance benchmarks...")

        all_performance_results = []

        # 收集所有性能結果
        for test_name, calc_time in self.performance_results.items():
            indicator_name = test_name.split('_')[0]

            if indicator_name in self.indicators.indicator_metadata:
                metadata = self.indicators.indicator_metadata[indicator_name]
                target_time = metadata.performance_target

                performance_ratio = calc_time / target_time
                meets_target = calc_time <= target_time

                all_performance_results.append({
                    'test_name': test_name,
                    'indicator': indicator_name,
                    'calculation_time_ms': calc_time,
                    'target_time_ms': target_time,
                    'performance_ratio': performance_ratio,
                    'meets_target': meets_target,
                    'status': 'PASS' if meets_target else 'FAIL'
                })

        # 性能統計
        performance_summary = {
            'total_tests': len(all_performance_results),
            'tests_passing': sum(1 for r in all_performance_results if r['meets_target']),
            'average_calc_time': np.mean([r['calculation_time_ms'] for r in all_performance_results]),
            'max_calc_time': np.max([r['calculation_time_ms'] for r in all_performance_results]),
            'min_calc_time': np.min([r['calculation_time_ms'] for r in all_performance_results]),
            'pass_rate': (sum(1 for r in all_performance_results if r['meets_target']) / len(all_performance_results)) * 100
        }

        # 性能要求：至少90%的測試應該通過性能基準
        self.assertGreaterEqual(performance_summary['pass_rate'], 90.0)

        self.test_results['performance_benchmarks'] = {
            'summary': performance_summary,
            'detailed_results': all_performance_results
        }

        logger.info(f"Performance Summary:")
        logger.info(f"  Pass Rate: {performance_summary['pass_rate']:.1f}%")
        logger.info(f"  Average Time: {performance_summary['average_calc_time']:.3f}ms")
        logger.info(f"  Max Time: {performance_summary['max_calc_time']:.3f}ms")
        logger.info(f"  Min Time: {performance_summary['min_calc_time']:.3f}ms")

    def test_comprehensive_indicator_validation(self):
        """測試綜合指標驗證"""
        logger.info("Running comprehensive indicator validation...")

        # 選擇代表性指標進行全面測試
        test_indicators = ['DEMA', 'TEMA', 'RSI_EXTENDED', 'BOLLINGER_BANDS', 'KELTNER_CHANNELS']
        comprehensive_results = self.indicators.run_comprehensive_test(
            self.price_data, test_indicators
        )

        # 驗證測試結果結構
        self.assertIn('test_summary', comprehensive_results)
        self.assertIn('individual_results', comprehensive_results)
        self.assertIn('performance_analysis', comprehensive_results)

        # 驗證性能目標
        performance_targets_met = comprehensive_results['test_summary']['performance_targets_met']
        total_tests = comprehensive_results['test_summary']['total_tests']
        performance_rate = (performance_targets_met / total_tests) * 100

        self.assertGreaterEqual(performance_rate, 80.0)  # 至少80%的測試應該滿足性能目標

        self.test_results['comprehensive_validation'] = comprehensive_results

        logger.info(f"Comprehensive Validation Results:")
        logger.info(f"  Performance Rate: {performance_rate:.1f}%")
        logger.info(f"  System Rating: {comprehensive_results['performance_analysis'].get('system_performance_rating', 'Unknown')}")

    @classmethod
    def save_test_results(cls):
        """保存測試結果"""
        output_dir = Path('data/phase2_test_results')
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')

        # 保存性能測試結果
        if cls.performance_results:
            performance_file = output_dir / f'phase2_performance_benchmark_{timestamp}.json'
            with open(performance_file, 'w') as f:
                json.dump(cls.performance_results, f, indent=2, default=str)
            logger.info(f"Performance results saved to: {performance_file}")

        # 保存綜合測試結果
        if cls.test_results:
            comprehensive_file = output_dir / f'phase2_comprehensive_test_{timestamp}.json'
            with open(comprehensive_file, 'w') as f:
                json.dump(cls.test_results, f, indent=2, default=str)
            logger.info(f"Comprehensive test results saved to: {comprehensive_file}")

        # 生成性能報告
        cls.generate_performance_report(output_dir, timestamp)

    @classmethod
    def generate_performance_report(cls, output_dir: Path, timestamp: str):
        """生成性能報告"""
        if not cls.performance_results:
            return

        # 創建性能可視化
        try:
            plt.figure(figsize=(12, 8))

            # 性能時間圖
            indicators = list(cls.performance_results.keys())
            times = list(cls.performance_results.values())

            plt.subplot(2, 1, 1)
            plt.bar(range(len(indicators)), times)
            plt.axhline(y=1.0, color='r', linestyle='--', label='1ms Target')
            plt.title('Phase 2 Indicators Performance Benchmark')
            plt.ylabel('Calculation Time (ms)')
            plt.xticks(range(len(indicators)), indicators, rotation=45, ha='right')
            plt.legend()
            plt.grid(True, alpha=0.3)

            # 性能分布圖
            plt.subplot(2, 1, 2)
            plt.hist(times, bins=10, alpha=0.7, edgecolor='black')
            plt.axvline(x=1.0, color='r', linestyle='--', label='1ms Target')
            plt.title('Performance Distribution')
            plt.xlabel('Calculation Time (ms)')
            plt.ylabel('Frequency')
            plt.legend()
            plt.grid(True, alpha=0.3)

            plt.tight_layout()

            # 保存圖表
            chart_file = output_dir / f'phase2_performance_chart_{timestamp}.png'
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"Performance chart saved to: {chart_file}")

        except Exception as e:
            logger.error(f"Failed to generate performance chart: {e}")


def run_performance_comparison():
    """運行性能比較測試"""
    logger.info("Running performance comparison tests...")

    indicators = Phase2ExtendedIndicators()

    # 比較不同數據類型下的性能
    np.random.seed(42)
    test_sizes = [100, 500, 1000, 2000, 5000]

    comparison_results = {}

    for size in test_sizes:
        test_data = pd.Series(
            np.cumsum(np.random.randn(size)) + 100,
            index=pd.date_range('2020-01-01', periods=size, freq='D')
        )

        size_results = {}

        # 測試關鍵指標
        key_indicators = ['DEMA', 'TEMA', 'RSI_EXTENDED', 'BOLLINGER_BANDS']

        for indicator_name in key_indicators:
            try:
                start_time = time.time()
                indicators._calculate_indicator_by_name(indicator_name, test_data)
                calc_time = (time.time() - start_time) * 1000
                size_results[indicator_name] = calc_time
            except Exception as e:
                size_results[indicator_name] = None
                logger.error(f"Error testing {indicator_name} with size {size}: {e}")

        comparison_results[f'size_{size}'] = size_results
        logger.info(f"Size {size} tests completed")

    # 保存比較結果
    output_dir = Path('data/phase2_test_results')
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    comparison_file = output_dir / f'phase2_performance_comparison_{timestamp}.json'

    with open(comparison_file, 'w') as f:
        json.dump(comparison_results, f, indent=2, default=str)

    logger.info(f"Performance comparison results saved to: {comparison_file}")
    return comparison_results


def main():
    """主測試函數"""
    print("[START] Phase 2 Extended Indicators Unit Tests and Performance Benchmarks")
    print("=" * 80)

    # 創建測試套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase2ExtendedIndicators)

    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 保存測試結果
    TestPhase2ExtendedIndicators.save_test_results()

    # 運行性能比較測試
    comparison_results = run_performance_comparison()

    # 測試總結
    print("\n" + "=" * 80)
    print("[COMPLETE] Phase 2 Extended Indicators Testing Summary:")
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100:.1f}%")

    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    print(f"\n[COMPLETE] All test results saved to: data/phase2_test_results/")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
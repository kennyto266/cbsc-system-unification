#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VectorBT Performance Regression Testing
向量化性能回歸測試套件
"""

import sys
import os
import time
import pandas as pd
import numpy as np
import json
from datetime import datetime
from typing import Dict, List, Tuple

sys.path.append(os.path.dirname(__file__))

from src.backtest.vectorbt_engine import VectorBTEngine, BacktestConfig
from src.api.stock_api import get_hk_stock_data

class PerformanceRegressionTester:
    """性能回歸測試器"""

    def __init__(self):
        self.engine = VectorBTEngine()
        self.baseline_results = {}
        self.performance_targets = {
            'strategies_per_second': 600,  # 每秒600個策略
            'rsi_calculation_time': 0.001,  # RSI計算時間<1ms
            'macd_calculation_time': 0.001,  # MACD計算時間<1ms
            'backtest_time': 0.1,  # 回測時間<100ms
        }

    def load_baseline(self, filename: str = None) -> bool:
        """加載基準性能數據"""
        if filename is None:
            filename = 'performance_baseline.json'

        try:
            with open(filename, 'r') as f:
                self.baseline_results = json.load(f)
            return True
        except FileNotFoundError:
            print(f"Baseline file {filename} not found. Will create new baseline.")
            return False

    def save_baseline(self, filename: str = None):
        """保存基準性能數據"""
        if filename is None:
            filename = f'performance_baseline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        with open(filename, 'w') as f:
            json.dump(self.baseline_results, f, indent=2)
        print(f"Baseline saved to {filename}")

    def test_strategy_performance(self, data: pd.DataFrame, strategy: str, params: Dict, iterations: int = 10) -> Dict:
        """測試單個策略的性能"""
        times = []

        for _ in range(iterations):
            start_time = time.time()
            result = self.engine.backtest_strategy(data, strategy, params)
            end_time = time.time()
            times.append(end_time - start_time)

        return {
            'strategy': strategy,
            'params': params,
            'avg_time': np.mean(times),
            'min_time': np.min(times),
            'max_time': np.max(times),
            'std_time': np.std(times),
            'iterations': iterations
        }

    def run_comprehensive_performance_test(self) -> Dict:
        """運行全面的性能測試"""
        print("Running comprehensive VectorBT performance test...")

        # 獲取測試數據
        data = get_hk_stock_data('0700.HK', 365)
        if data is None or isinstance(data, dict):
            print("Failed to get test data, using synthetic data")
            data = self.generate_synthetic_data()

        print(f"Using {len(data)} data points for testing")

        # 測試所有策略
        strategies = [
            ('RSI_MEAN_REVERSION', {'period': 14, 'oversold': 30, 'overbought': 70}),
            ('MACD_CROSSOVER', {'fast': 12, 'slow': 26, 'signal': 9}),
            ('BOLLINGER_BANDS', {'period': 20, 'std_dev': 2.0}),
            ('DUAL_MOVING_AVERAGE', {'short_period': 20, 'long_period': 50}),
            ('MOMENTUM_BREAKOUT', {'lookback': 20, 'threshold': 0.02}),
            ('VOLATILITY_BREAKOUT', {'atr_period': 14, 'multiplier': 2.0})
        ]

        results = {}
        total_strategies = 0

        for strategy, params in strategies:
            print(f"Testing {strategy}...")
            result = self.test_strategy_performance(data, strategy, params)
            results[strategy] = result
            total_strategies += result['iterations']

        # 計算總體性能指標
        total_time = sum(r['avg_time'] for r in results.values())
        strategies_per_second = total_strategies / total_time

        results['overall_performance'] = {
            'total_strategies': total_strategies,
            'total_time': total_time,
            'strategies_per_second': strategies_per_second,
            'data_points': len(data)
        }

        return results

    def generate_synthetic_data(self, days: int = 365) -> pd.DataFrame:
        """生成合成測試數據"""
        np.random.seed(42)

        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

        # 生成模擬股價數據
        returns = np.random.normal(0.001, 0.02, days)  # 日常回報
        prices = 100 * np.exp(np.cumsum(returns))  # 價格路徑

        # 生成OHLCV數據
        high = prices * (1 + np.abs(np.random.normal(0, 0.01, days)))
        low = prices * (1 - np.abs(np.random.normal(0, 0.01, days)))
        volume = np.random.randint(1000000, 10000000, days)
        open_prices = np.roll(prices, 1)
        open_prices[0] = prices[0]

        return pd.DataFrame({
            'open': open_prices,
            'high': high,
            'low': low,
            'close': prices,
            'volume': volume
        }, index=dates)

    def validate_performance_targets(self, results: Dict) -> Dict:
        """驗證性能目標"""
        validation_results = {
            'passed': True,
            'failures': [],
            'warnings': []
        }

        overall = results.get('overall_performance', {})

        # 檢查策略處理速度
        if overall.get('strategies_per_second', 0) < self.performance_targets['strategies_per_second']:
            validation_results['passed'] = False
            validation_results['failures'].append(
                f"Strategy processing too slow: {overall.get('strategies_per_second', 0):.1f} < {self.performance_targets['strategies_per_second']}"
            )

        # 檢查各策略性能
        for strategy, result in results.items():
            if strategy == 'overall_performance':
                continue

            if result['avg_time'] > 0.01:  # 10ms
                validation_results['warnings'].append(
                    f"Strategy {strategy} slow: {result['avg_time']*1000:.2f}ms"
                )

        return validation_results

    def compare_with_baseline(self, results: Dict) -> Dict:
        """與基準性能比較"""
        if not self.baseline_results:
            print("No baseline data available for comparison")
            return {'status': 'no_baseline'}

        comparison = {
            'status': 'completed',
            'improvements': [],
            'regressions': [],
            'unchanged': []
        }

        current_overall = results.get('overall_performance', {})
        baseline_overall = self.baseline_results.get('overall_performance', {})

        # 比較總體性能
        current_sps = current_overall.get('strategies_per_second', 0)
        baseline_sps = baseline_overall.get('strategies_per_second', 0)

        if baseline_sps > 0:
            improvement_pct = ((current_sps - baseline_sps) / baseline_sps) * 100

            if improvement_pct > 5:
                comparison['improvements'].append(
                    f"Overall performance improved by {improvement_pct:.1f}%"
                )
            elif improvement_pct < -5:
                comparison['regressions'].append(
                    f"Overall performance regressed by {abs(improvement_pct):.1f}%"
                )
            else:
                comparison['unchanged'].append("Overall performance stable")

        # 比較各策略
        for strategy in results:
            if strategy == 'overall_performance':
                continue

            current_time = results[strategy].get('avg_time', 0)
            baseline_time = self.baseline_results.get(strategy, {}).get('avg_time', 0)

            if baseline_time > 0:
                change_pct = ((current_time - baseline_time) / baseline_time) * 100

                if change_pct < -10:
                    comparison['improvements'].append(
                        f"{strategy} speed improved by {abs(change_pct):.1f}%"
                    )
                elif change_pct > 10:
                    comparison['regressions'].append(
                        f"{strategy} speed regressed by {change_pct:.1f}%"
                    )

        return comparison

def run_performance_regression():
    """運行性能回歸測試"""
    print("=" * 80)
    print("VectorBT Performance Regression Test")
    print("=" * 80)

    tester = PerformanceRegressionTester()

    # 加載基準數據
    has_baseline = tester.load_baseline()

    # 運行性能測試
    results = tester.run_comprehensive_performance_test()

    # 驗證性能目標
    validation = tester.validate_performance_targets(results)

    # 顯示結果
    print("\nPerformance Results:")
    overall = results.get('overall_performance', {})
    print(f"Strategies processed: {overall.get('total_strategies', 0)}")
    print(f"Total time: {overall.get('total_time', 0):.3f}s")
    print(f"Strategies per second: {overall.get('strategies_per_second', 0):.1f}")

    print("\nIndividual Strategy Performance:")
    for strategy, result in results.items():
        if strategy == 'overall_performance':
            continue
        print(f"{strategy}: {result['avg_time']*1000:.2f}ms ± {result['std_time']*1000:.2f}ms")

    # 驗證結果
    print(f"\nValidation: {'PASSED' if validation['passed'] else 'FAILED'}")
    if validation['failures']:
        print("Failures:")
        for failure in validation['failures']:
            print(f"  - {failure}")

    if validation['warnings']:
        print("Warnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")

    # 與基準比較
    if has_baseline:
        comparison = tester.compare_with_baseline(results)
        print(f"\nBaseline Comparison: {comparison['status']}")

        if comparison['improvements']:
            print("Improvements:")
            for improvement in comparison['improvements']:
                print(f"  ✓ {improvement}")

        if comparison['regressions']:
            print("Regressions:")
            for regression in comparison['regressions']:
                print(f"  ✗ {regression}")

        if comparison['unchanged']:
            print("Unchanged:")
            for unchanged in comparison['unchanged']:
                print(f"  ~ {unchanged}")

    # 保存新基準（如果需要）
    if not has_baseline or not validation['passed']:
        tester.save_baseline()

    # 保存測試結果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"performance_test_results_{timestamp}.json"

    test_results = {
        'timestamp': timestamp,
        'results': results,
        'validation': validation,
        'baseline_comparison': tester.compare_with_baseline(results) if has_baseline else None
    }

    with open(filename, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)

    print(f"\nTest results saved to: {filename}")
    print(f"{'SUCCESS' if validation['passed'] else 'FAILURE'}: Performance regression test completed")

    return validation['passed']

if __name__ == "__main__":
    success = run_performance_regression()
    sys.exit(0 if success else 1)
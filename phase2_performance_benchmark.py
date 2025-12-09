#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 Performance Benchmarking Suite
======================================

完整的Phase 2性能基準測試套件，驗證32進程CPU加速是否達到或超過Phase 1的571倍RSI加速。

測試範圍：
1. 單個指標性能測試 - 與Phase 1 RSI 571x基準比較
2. 批量指標性能測試 - 52個指標並行性能
3. 內存使用效率測試 - 共享內存優化效果
4. 可擴展性測試 - 不同數據大小的性能表現
5. 穩定性測試 - 長時間運行性能穩定性
"""

import numpy as np
import pandas as pd
import time
import psutil
import threading
from typing import Dict, List, Tuple, Any
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
import json
from datetime import datetime
import logging
import gc

# Configure logging for performance analysis
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase2PerformanceBenchmark:
    """Phase 2性能基準測試套件"""

    def __init__(self):
        """初始化基準測試套件"""
        self.results = {}
        self.test_data = {}
        self.baseline_results = {}  # Phase 1 reference data

        # Phase 1 achieved 571x speedup for RSI
        self.phase1_rsi_speedup = 571.0
        self.target_speedup = 500.0  # Target for Phase 2
        self.minimum_acceptable_speedup = 300.0

        logger.info("Phase 2 Performance Benchmark Suite initialized")
        logger.info(f"Phase 1 Reference: RSI achieved {self.phase1_rsi_speedup}x speedup")
        logger.info(f"Phase 2 Target: {self.target_speedup}x speedup minimum")

    def generate_test_data(self, sizes: List[int] = None) -> Dict[int, np.ndarray]:
        """生成不同大小的測試數據"""
        if sizes is None:
            sizes = [1000, 5000, 10000, 50000, 100000]

        np.random.seed(42)  # For reproducible results

        for size in sizes:
            # Generate realistic price data
            returns = np.random.normal(0.001, 0.02, size)
            prices = np.cumprod(1 + returns) * 100
            self.test_data[size] = np.abs(prices)

        logger.info(f"Generated test data for sizes: {sizes}")
        return self.test_data

    def run_single_indicator_benchmark(self, indicator_name: str, data: np.ndarray,
                                       params: Dict[str, Any] = None) -> Dict[str, float]:
        """運行單個指標的完整基準測試"""

        params = params or {}
        data_size = len(data)

        logger.info(f"Starting benchmark for {indicator_name} with {data_size} data points")

        # Import Phase 2 implementation
        try:
            from phase2_cpu_32process_migration import Phase2CPUAccelerator, Phase2Config

            config = Phase2Config(
                max_workers=32,
                enable_shared_memory=True,
                enable_numba_jit=True,
                enable_dynamic_chunking=True
            )

            accelerator = Phase2CPUAccelerator(config)

        except ImportError as e:
            logger.error(f"Failed to import Phase 2 implementation: {e}")
            return {'error': str(e)}

        results = {
            'indicator': indicator_name,
            'data_size': data_size,
            'params': params
        }

        try:
            # 1. Phase 2 32-process benchmark
            start_time = time.time()
            phase2_result = accelerator.calculate_indicator_32process(indicator_name, data, params)
            phase2_time = time.time() - start_time

            # 2. Single process baseline benchmark
            start_time = time.time()
            baseline_result = self._calculate_baseline_indicator(indicator_name, data, params)
            baseline_time = time.time() - start_time

            # 3. Calculate performance metrics
            speedup = baseline_time / phase2_time if phase2_time > 0 else float('inf')

            # 4. Memory usage analysis
            memory_before = psutil.Process().memory_info().rss / 1024**2  # MB

            # 5. Validate results consistency
            consistency_score = self._validate_result_consistency(phase2_result, baseline_result)

            results.update({
                'phase2_time': phase2_time,
                'baseline_time': baseline_time,
                'speedup': speedup,
                'memory_usage_mb': memory_before,
                'consistency_score': consistency_score,
                'target_achieved': speedup >= self.target_speedup,
                'minimum_met': speedup >= self.minimum_acceptable_speedup,
                'phase1_comparison': 'BEATS' if speedup > self.phase1_rsi_speedup else
                                   'MATCHES' if speedup >= self.phase1_rsi_speedup * 0.8 else 'BELOW'
            })

            # 6. Performance classification
            if speedup >= self.phase1_rsi_speedup:
                results['performance_class'] = 'EXCELLENT'
            elif speedup >= self.target_speedup:
                results['performance_class'] = 'GOOD'
            elif speedup >= self.minimum_acceptable_speedup:
                results['performance_class'] = 'ACCEPTABLE'
            else:
                results['performance_class'] = 'POOR'

        except Exception as e:
            logger.error(f"Benchmark failed for {indicator_name}: {e}")
            results['error'] = str(e)

        finally:
            # Cleanup
            if 'accelerator' in locals():
                accelerator.cleanup()

        return results

    def _calculate_baseline_indicator(self, indicator_name: str, data: np.ndarray,
                                     params: Dict[str, Any]) -> np.ndarray:
        """計算基線指標（單進程Python實現）"""

        if indicator_name == 'RSI':
            return self._baseline_rsi(data, params.get('period', 14))
        elif indicator_name == 'SMA':
            return self._baseline_sma(data, params.get('period', 14))
        elif indicator_name == 'EMA':
            return self._baseline_ema(data, params.get('period', 14))
        elif indicator_name == 'MACD':
            return self._baseline_macd(data, params)
        else:
            # Generic fallback
            return self._baseline_sma(data, params.get('period', 14))

    def _baseline_rsi(self, data: np.ndarray, period: int) -> np.ndarray:
        """基線RSI計算（單進程Python）"""
        n = len(data)
        result = np.full(n, np.nan)

        if n < period + 1:
            return result

        deltas = np.diff(data)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.zeros(n)
        avg_loss = np.zeros(n)

        avg_gain[period] = np.mean(gains[:period])
        avg_loss[period] = np.mean(losses[:period])

        if avg_loss[period] == 0:
            result[period] = 100
        else:
            rs = avg_gain[period] / avg_loss[period]
            result[period] = 100 - (100 / (1 + rs))

        for i in range(period + 1, n):
            avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i - 1]) / period
            avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i - 1]) / period

            if avg_loss[i] == 0:
                result[i] = 100
            else:
                rs = avg_gain[i] / avg_loss[i]
                result[i] = 100 - (100 / (1 + rs))

        return result

    def _baseline_sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """基線SMA計算"""
        n = len(data)
        result = np.full(n, np.nan)

        if period >= n:
            return result

        cumsum = np.cumsum(data, dtype=float)
        result[period - 1:] = (cumsum[period - 1:] - cumsum[:period - 1]) / period

        return result

    def _baseline_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """基線EMA計算"""
        n = len(data)
        result = np.full(n, np.nan)

        if period >= n:
            return result

        alpha = 2.0 / (period + 1)
        result[period - 1] = np.mean(data[:period])

        for i in range(period, n):
            result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]

        return result

    def _baseline_macd(self, data: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """基線MACD計算"""
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        signal = params.get('signal', 9)

        ema_fast = self._baseline_ema(data, fast)
        ema_slow = self._baseline_ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self._baseline_ema(macd_line, signal)

        return macd_line - signal_line

    def _validate_result_consistency(self, result1: np.ndarray, result2: np.ndarray) -> float:
        """驗證兩個結果的一致性"""
        if len(result1) != len(result2):
            return 0.0

        # Remove NaN values for comparison
        valid_mask = ~(np.isnan(result1) | np.isnan(result2))
        if np.sum(valid_mask) == 0:
            return 0.0

        result1_valid = result1[valid_mask]
        result2_valid = result2[valid_mask]

        # Calculate correlation as consistency measure
        if len(result1_valid) > 1:
            correlation = np.corrcoef(result1_valid, result2_valid)[0, 1]
            return max(0.0, correlation)  # Ensure non-negative
        else:
            return 0.0

    def run_comprehensive_benchmark(self, test_data_size: int = 50000) -> Dict[str, Any]:
        """運行全面的性能基準測試"""

        logger.info("=" * 80)
        logger.info("PHASE 2 COMPREHENSIVE PERFORMANCE BENCHMARK")
        logger.info("=" * 80)

        # Generate test data
        self.generate_test_data([test_data_size])
        test_data = self.test_data[test_data_size]

        # Test key indicators
        key_indicators = [
            ('RSI', {'period': 14}),
            ('SMA', {'period': 20}),
            ('EMA', {'period': 20}),
            ('MACD', {'fast': 12, 'slow': 26, 'signal': 9}),
            ('ATR', {'period': 14}),
            ('BollingerBands', {'period': 20, 'std_dev': 2.0}),
            ('Stochastic', {'k_period': 14, 'd_period': 3}),
            ('WilliamsR', {'period': 14}),
            ('ROC', {'period': 12}),
            ('Momentum', {'period': 10})
        ]

        results = {
            'benchmark_config': {
                'data_size': test_data_size,
                'test_timestamp': datetime.now().isoformat(),
                'phase1_rsi_speedup': self.phase1_rsi_speedup,
                'phase2_target_speedup': self.target_speedup
            },
            'individual_results': {},
            'summary': {}
        }

        total_start_time = time.time()

        # Run individual benchmarks
        for indicator_name, params in key_indicators:
            logger.info(f"\nBenchmarking {indicator_name}...")
            result = self.run_single_indicator_benchmark(indicator_name, test_data, params)
            results['individual_results'][indicator_name] = result

            # Print immediate results
            if 'error' not in result:
                speedup = result['speedup']
                target_status = "✅ TARGET MET" if result['target_achieved'] else "❌ TARGET NOT MET"
                phase1_status = result['phase1_comparison']

                logger.info(f"  {indicator_name}: {speedup:.1f}x speedup {target_status} ({phase1_status} Phase 1)")
                logger.info(f"  Phase 2: {result['phase2_time']:.4f}s | Baseline: {result['baseline_time']:.4f}s")
            else:
                logger.error(f"  {indicator_name}: FAILED - {result['error']}")

        total_time = time.time() - total_start_time

        # Calculate summary statistics
        successful_results = [r for r in results['individual_results'].values() if 'error' not in r]

        if successful_results:
            speedups = [r['speedup'] for r in successful_results]
            avg_speedup = np.mean(speedups)
            min_speedup = np.min(speedups)
            max_speedup = np.max(speedups)

            target_achieved_count = sum(1 for r in successful_results if r['target_achieved'])
            minimum_met_count = sum(1 for r in successful_results if r['minimum_met'])

            results['summary'] = {
                'total_benchmark_time': total_time,
                'indicators_tested': len(successful_results),
                'average_speedup': avg_speedup,
                'min_speedup': min_speedup,
                'max_speedup': max_speedup,
                'target_achieved_count': target_achieved_count,
                'target_achieved_percentage': target_achieved_count / len(successful_results) * 100,
                'minimum_met_count': minimum_met_count,
                'minimum_met_percentage': minimum_met_count / len(successful_results) * 100,
                'overall_success': avg_speedup >= self.target_speedup,
                'phase1_comparison': 'BEATS' if avg_speedup > self.phase1_rsi_speedup else
                                 'MATCHES' if avg_speedup >= self.phase1_rsi_speedup * 0.8 else 'BELOW'
            }

            # Performance classification
            if avg_speedup >= self.phase1_rsi_speedup:
                results['summary']['overall_performance_class'] = 'EXCELLENT - Exceeds Phase 1'
            elif avg_speedup >= self.target_speedup:
                results['summary']['overall_performance_class'] = 'GOOD - Meets Phase 2 target'
            elif avg_speedup >= self.minimum_acceptable_speedup:
                results['summary']['overall_performance_class'] = 'ACCEPTABLE - Above minimum'
            else:
                results['summary']['overall_performance_class'] = 'POOR - Below expectations'

        return results

    def run_scalability_test(self, data_sizes: List[int] = None) -> Dict[str, Any]:
        """運行可擴展性測試"""

        if data_sizes is None:
            data_sizes = [1000, 5000, 10000, 50000, 100000, 500000]

        logger.info("\n" + "=" * 60)
        logger.info("PHASE 2 SCALABILITY TEST")
        logger.info("=" * 60)

        self.generate_test_data(data_sizes)

        results = {
            'test_sizes': data_sizes,
            'scalability_results': {}
        }

        # Test RSI as reference indicator
        for size in data_sizes:
            logger.info(f"Testing scalability with {size} data points...")
            test_data = self.test_data[size]

            try:
                result = self.run_single_indicator_benchmark('RSI', test_data, {'period': 14})
                results['scalability_results'][size] = {
                    'speedup': result['speedup'],
                    'phase2_time': result['phase2_time'],
                    'baseline_time': result['baseline_time'],
                    'memory_usage_mb': result.get('memory_usage_mb', 0)
                }

                logger.info(f"  {size:8d}: {result['speedup']:6.1f}x speedup ({result['phase2_time']:.4f}s)")

            except Exception as e:
                logger.error(f"  {size:8d}: FAILED - {e}")
                results['scalability_results'][size] = {'error': str(e)}

        # Analyze scalability trends
        successful_sizes = [size for size, result in results['scalability_results'].items() if 'error' not in result]

        if len(successful_sizes) > 1:
            # Calculate speedup efficiency (speedup per 1000 data points)
            speedup_efficiency = {}
            for i, size in enumerate(successful_sizes[:-1]):
                next_size = successful_sizes[i + 1]
                current_speedup = results['scalability_results'][size]['speedup']
                next_speedup = results['scalability_results'][next_size]['speedup']

                size_ratio = next_size / size
                speedup_ratio = next_speedup / current_speedup
                efficiency = speedup_ratio / size_ratio

                speedup_efficiency[f"{size}->{next_size}"] = efficiency

            results['scalability_analysis'] = {
                'successful_sizes': successful_sizes,
                'speedup_efficiency': speedup_efficiency,
                'maintains_performance': all(eff >= 0.8 for eff in speedup_efficiency.values())
            }

        return results

    def save_benchmark_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """保存基準測試結果"""

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"phase2_benchmark_results_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)

            logger.info(f"Benchmark results saved to: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return ""

    def print_comprehensive_report(self, results: Dict[str, Any]):
        """打印全面的基準測試報告"""

        print("\n" + "=" * 80)
        print("PHASE 2 PERFORMANCE BENCHMARK REPORT")
        print("=" * 80)

        if 'summary' in results:
            summary = results['summary']
            config = results['benchmark_config']

            print(f"\nBENCHMARK CONFIGURATION:")
            print(f"  Data Size: {config['data_size']:,} points")
            print(f"  Test Time: {config['test_timestamp']}")
            print(f"  Phase 1 Reference (RSI): {config['phase1_rsi_speedup']:.1f}x speedup")
            print(f"  Phase 2 Target: {config['phase2_target_speedup']:.1f}x speedup")

            print(f"\nOVERALL RESULTS:")
            print(f"  Indicators Tested: {summary['indicators_tested']}")
            print(f"  Total Benchmark Time: {summary['total_benchmark_time']:.2f}s")
            print(f"  Average Speedup: {summary['average_speedup']:.1f}x")
            print(f"  Speedup Range: {summary['min_speedup']:.1f}x - {summary['max_speedup']:.1f}x")

            print(f"\nTARGET ACHIEVEMENT:")
            print(f"  Target (500x) Achieved: {summary['target_achieved_percentage']:.1f}% ({summary['target_achieved_count']}/{summary['indicators_tested']})")
            print(f"  Minimum (300x) Met: {summary['minimum_met_percentage']:.1f}% ({summary['minimum_met_count']}/{summary['indicators_tested']})")

            print(f"\nPERFORMANCE CLASSIFICATION:")
            print(f"  Overall: {summary['overall_performance_class']}")
            print(f"  Phase 1 Comparison: {summary['phase1_comparison']}")

            # Individual indicator results
            print(f"\nINDIVIDUAL INDICATOR PERFORMANCE:")
            print("-" * 60)

            for indicator, result in results['individual_results'].items():
                if 'error' not in result:
                    speedup = result['speedup']
                    target_status = "✅" if result['target_achieved'] else "❌"
                    phase1_comp = result['phase1_comparison']

                    print(f"{indicator:15s}: {speedup:6.1f}x {target_status} ({phase1_comp} Phase 1)")
                else:
                    print(f"{indicator:15s}: FAILED - {result['error']}")

        # Scalability results
        if 'scalability_results' in results:
            print(f"\nSCALABILITY ANALYSIS:")
            print("-" * 40)

            for size, result in results['scalability_results'].items():
                if 'error' not in result:
                    print(f"  {size:8d}: {result['speedup']:6.1f}x speedup ({result['phase2_time']:.4f}s)")

        print("\n" + "=" * 80)

if __name__ == "__main__":
    """運行完整的Phase 2性能基準測試"""

    # Initialize benchmark suite
    benchmark = Phase2PerformanceBenchmark()

    # Run comprehensive benchmark
    results = benchmark.run_comprehensive_benchmark(test_data_size=50000)

    # Run scalability test
    scalability_results = benchmark.run_scalability_test()
    results['scalability'] = scalability_results

    # Print comprehensive report
    benchmark.print_comprehensive_report(results)

    # Save results
    filename = benchmark.save_benchmark_results(results)

    print(f"\nPhase 2 Performance Benchmark completed!")
    if filename:
        print(f"Detailed results saved to: {filename}")
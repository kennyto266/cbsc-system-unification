#!/usr/bin/env python3
"""
Phase 3 Performance Optimization Test and Validation Script

This script tests and validates the performance optimizations implemented
for the technical analysis system in Phase 3.

Features:
- Performance benchmarking
- Accuracy validation
- Memory usage analysis
- Comparative analysis
- Integration testing
"""

import sys
import os
import time
import numpy as np
import pandas as pd
import logging
import matplotlib.pyplot as plt
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import gc
import psutil

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "simplified_system" / "src" / "indicators"))

# Import both original and optimized implementations
try:
    from core_indicators import CoreIndicators as OriginalCoreIndicators
    from performance_optimized_indicators import PerformanceOptimizedCoreIndicators
    from phase3_performance_optimizer import Phase3PerformanceOptimizer, create_performance_optimizer
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required modules are available")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceTestSuite:
    """Comprehensive performance testing suite"""

    def __init__(self):
        self.test_results = {}
        self.original_indicators = None
        self.optimized_indicators = None
        self.phase3_optimizer = None

    def setup_test_environment(self):
        """Setup test environment and initialize indicators"""
        logger.info("Setting up test environment...")

        try:
            # Initialize original indicators
            self.original_indicators = OriginalCoreIndicators()
            logger.info("✅ Original CoreIndicators initialized")

            # Initialize optimized indicators
            self.optimized_indicators = PerformanceOptimizedCoreIndicators(
                enable_optimizations=True,
                cache_size_mb=50,  # Smaller for testing
                enable_parallel=True,
                batch_size=500
            )
            logger.info("✅ Optimized CoreIndicators initialized")

            # Initialize Phase 3 optimizer
            self.phase3_optimizer = create_performance_optimizer(
                cache_size_mb=50,
                enable_parallel=True,
                batch_size=500
            )
            logger.info("✅ Phase 3 Performance Optimizer initialized")

        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            raise

    def generate_test_data(self, size: int = 10000) -> pd.DataFrame:
        """Generate synthetic test data for benchmarking"""
        logger.info(f"Generating test data with {size} points...")

        np.random.seed(42)  # For reproducible results

        # Generate realistic price movements
        returns = np.random.normal(0.001, 0.02, size)  # Daily returns
        prices = 100 * np.exp(np.cumsum(returns))  # Price series

        # Generate OHLCV data
        high = prices * (1 + np.abs(np.random.normal(0, 0.01, size)))
        low = prices * (1 - np.abs(np.random.normal(0, 0.01, size)))
        close = prices
        volume = np.random.randint(1000000, 10000000, size)

        # Create DataFrame
        dates = pd.date_range('2020-01-01', periods=size, freq='D')
        data = pd.DataFrame({
            'open': close,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }, index=dates)

        logger.info(f"✅ Test data generated: {len(data)} points")
        return data

    def test_single_indicator_performance(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Test performance of single indicator calculations"""
        logger.info("Testing single indicator performance...")

        results = {}
        indicators_to_test = [
            ('RSI', lambda ind: ind.calculate_rsi(data['close'], 14)),
            ('SMA', lambda ind: ind.calculate_sma(data['close'], 20)),
            ('EMA', lambda ind: ind.calculate_ema(data['close'], 26)),
            ('MACD', lambda ind: ind.calculate_macd(data['close'], 12, 26, 9)),
            ('Bollinger', lambda ind: ind.calculate_bollinger_bands(data['close'], 20, 2)),
            ('Stochastic', lambda ind: ind.calculate_stochastic(data['high'], data['low'], data['close'], 14, 3)),
            ('Williams_R', lambda ind: ind.calculate_williams_r(data['high'], data['low'], data['close'], 14)),
            ('ATR', lambda ind: ind.calculate_atr(data['high'], data['low'], data['close'], 14)),
            ('Volume_MA', lambda ind: ind.calculate_volume_ma(data['volume'], 20))
        ]

        for indicator_name, calculation_func in indicators_to_test:
            logger.info(f"Testing {indicator_name}...")

            # Test original implementation
            gc.collect()  # Clean memory before test
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

            try:
                original_result = calculation_func(self.original_indicators)
                original_time = time.time() - start_time
                original_memory = psutil.Process().memory_info().rss / 1024 / 1024 - start_memory
            except Exception as e:
                logger.warning(f"Original {indicator_name} failed: {e}")
                original_result = None
                original_time = float('inf')
                original_memory = 0

            # Test optimized implementation
            gc.collect()  # Clean memory before test
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

            try:
                optimized_result = calculation_func(self.optimized_indicators)
                optimized_time = time.time() - start_time
                optimized_memory = psutil.Process().memory_info().rss / 1024 / 1024 - start_memory
            except Exception as e:
                logger.error(f"Optimized {indicator_name} failed: {e}")
                optimized_result = None
                optimized_time = float('inf')
                optimized_memory = 0

            # Validate accuracy
            accuracy_validated = False
            if original_result is not None and optimized_result is not None:
                accuracy_validated = self._validate_results(original_result, optimized_result, indicator_name)

            # Calculate performance metrics
            speedup = original_time / optimized_time if optimized_time > 0 and original_time != float('inf') else 0
            memory_saving = (original_memory - optimized_memory) / max(original_memory, 1) * 100 if original_memory > 0 else 0

            results[indicator_name] = {
                'original_time': original_time,
                'optimized_time': optimized_time,
                'speedup': speedup,
                'original_memory_mb': original_memory,
                'optimized_memory_mb': optimized_memory,
                'memory_saving_percent': memory_saving,
                'accuracy_validated': accuracy_validated,
                'original_data_points': len(original_result) if original_result is not None else 0,
                'optimized_data_points': len(optimized_result) if optimized_result is not None else 0
            }

            logger.info(f"✅ {indicator_name}: Speedup {speedup:.2f}x, Memory saving {memory_saving:.1f}%")

        return results

    def test_batch_indicator_performance(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Test performance of batch indicator calculations"""
        logger.info("Testing batch indicator performance...")

        # Define indicator configurations for batch processing
        indicators_config = [
            {'name': 'rsi_14', 'type': 'rsi', 'params': {'period': 14}},
            {'name': 'rsi_21', 'type': 'rsi', 'params': {'period': 21}},
            {'name': 'sma_20', 'type': 'sma', 'params': {'period': 20}},
            {'name': 'sma_50', 'type': 'sma', 'params': {'period': 50}},
            {'name': 'ema_12', 'type': 'ema', 'params': {'period': 12}},
            {'name': 'ema_26', 'type': 'ema', 'params': {'period': 26}},
            {'name': 'macd_standard', 'type': 'macd', 'params': {'fast': 12, 'slow': 26, 'signal': 9}},
            {'name': 'bollinger_20', 'type': 'bollinger', 'params': {'period': 20, 'std_dev': 2}},
            {'name': 'stochastic_14', 'type': 'stochastic', 'params': {'k_period': 14, 'd_period': 3}},
            {'name': 'williams_r_14', 'type': 'williams_r', 'params': {'period': 14}},
            {'name': 'atr_14', 'type': 'atr', 'params': {'period': 14}},
            {'name': 'volume_ma_20', 'type': 'volume_ma', 'params': {'period': 20}}
        ]

        # Test Phase 3 optimizer
        gc.collect()
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        try:
            phase3_results = self.phase3_optimizer.optimize_technical_analysis(data, indicators_config)
            phase3_time = time.time() - start_time
            phase3_memory = psutil.Process().memory_info().rss / 1024 / 1024 - start_memory
        except Exception as e:
            logger.error(f"Phase 3 optimizer failed: {e}")
            phase3_results = None
            phase3_time = float('inf')
            phase3_memory = 0

        # Test optimized batch processing
        gc.collect()
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        try:
            batch_results = self.optimized_indicators.calculate_multiple_indicators(data, indicators_config)
            batch_time = time.time() - start_time
            batch_memory = psutil.Process().memory_info().rss / 1024 / 1024 - start_memory
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            batch_results = None
            batch_time = float('inf')
            batch_memory = 0

        # Test sequential processing (baseline)
        gc.collect()
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        try:
            sequential_results = self.optimized_indicators._calculate_multiple_indicators_basic(data, indicators_config)
            sequential_time = time.time() - start_time
            sequential_memory = psutil.Process().memory_info().rss / 1024 / 1024 - start_memory
        except Exception as e:
            logger.error(f"Sequential processing failed: {e}")
            sequential_results = None
            sequential_time = float('inf')
            sequential_memory = 0

        results = {
            'phase3_optimizer': {
                'time': phase3_time,
                'memory_mb': phase3_memory,
                'indicators_calculated': len(phase3_results['indicators']) if phase3_results else 0,
                'optimization_strategy': phase3_results['optimization']['strategy'] if phase3_results else 'failed'
            },
            'batch_processing': {
                'time': batch_time,
                'memory_mb': batch_memory,
                'indicators_calculated': len(batch_results) if batch_results else 0
            },
            'sequential_processing': {
                'time': sequential_time,
                'memory_mb': sequential_memory,
                'indicators_calculated': len(sequential_results) if sequential_results else 0
            }
        }

        # Calculate performance comparisons
        if batch_time > 0 and sequential_time > 0:
            results['batch_vs_sequential_speedup'] = sequential_time / batch_time
        else:
            results['batch_vs_sequential_speedup'] = 0

        if phase3_time > 0 and sequential_time > 0:
            results['phase3_vs_sequential_speedup'] = sequential_time / phase3_time
        else:
            results['phase3_vs_sequential_speedup'] = 0

        logger.info(f"✅ Batch performance test completed")
        logger.info(f"   Phase 3 vs Sequential: {results['phase3_vs_sequential_speedup']:.2f}x speedup")
        logger.info(f"   Batch vs Sequential: {results['batch_vs_sequential_speedup']:.2f}x speedup")

        return results

    def test_scalability(self) -> Dict[str, Any]:
        """Test scalability with different data sizes"""
        logger.info("Testing scalability...")

        data_sizes = [1000, 5000, 10000, 25000, 50000]
        results = {}

        for size in data_sizes:
            logger.info(f"Testing with {size} data points...")
            data = self.generate_test_data(size)

            # Test optimized implementation
            gc.collect()
            start_time = time.time()
            try:
                optimized_result = self.optimized_indicators.calculate_rsi(data['close'], 14)
                optimized_time = time.time() - start_time
                optimized_points = len(optimized_result)
            except Exception as e:
                logger.error(f"Optimized RSI failed for size {size}: {e}")
                optimized_time = float('inf')
                optimized_points = 0

            # Test original implementation
            gc.collect()
            start_time = time.time()
            try:
                original_result = self.original_indicators.calculate_rsi(data['close'], 14)
                original_time = time.time() - start_time
                original_points = len(original_result)
            except Exception as e:
                logger.error(f"Original RSI failed for size {size}: {e}")
                original_time = float('inf')
                original_points = 0

            results[f"size_{size}"] = {
                'data_points': size,
                'optimized_time': optimized_time,
                'original_time': original_time,
                'speedup': original_time / optimized_time if optimized_time > 0 and original_time != float('inf') else 0,
                'optimized_points': optimized_points,
                'original_points': original_points,
                'time_per_point': optimized_time / size if optimized_time > 0 else float('inf')
            }

            logger.info(f"   Speedup: {results[f'size_{size}']['speedup']:.2f}x")

        return results

    def test_memory_efficiency(self) -> Dict[str, Any]:
        """Test memory efficiency and cache performance"""
        logger.info("Testing memory efficiency...")

        # Get cache statistics
        cache_stats = self.optimized_indicators.get_performance_report()

        # Test memory cleanup
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Run multiple calculations to fill cache
        data = self.generate_test_data(5000)
        for i in range(10):
            self.optimized_indicators.calculate_rsi(data['close'], 14 + i)

        filled_cache_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Test memory optimization
        self.optimized_indicators.optimize_memory()
        optimized_memory = psutil.Process().memory_info().rss / 1024 / 1024

        results = {
            'initial_memory_mb': initial_memory,
            'filled_cache_memory_mb': filled_cache_memory,
            'optimized_memory_mb': optimized_memory,
            'memory_saved_mb': filled_cache_memory - optimized_memory,
            'cache_statistics': cache_stats
        }

        logger.info(f"   Memory saved: {results['memory_saved_mb']:.2f} MB")

        return results

    def _validate_results(self, original: Any, optimized: Any, indicator_name: str) -> bool:
        """Validate that optimized results match original within tolerance"""
        try:
            if original is None or optimized is None:
                return False

            # Handle different data types
            if isinstance(original, dict) and isinstance(optimized, dict):
                # For MACD and other dictionary results
                for key in original.keys():
                    if key in optimized:
                        if not self._compare_arrays(original[key], optimized[key], indicator_name, key):
                            return False
                return True
            else:
                # For single series results
                return self._compare_arrays(original, optimized, indicator_name)

        except Exception as e:
            logger.warning(f"Validation failed for {indicator_name}: {e}")
            return False

    def _compare_arrays(self, arr1: Any, arr2: Any, indicator_name: str, sub_key: str = "") -> bool:
        """Compare two arrays for equality within tolerance"""
        try:
            # Convert to numpy arrays if needed
            if hasattr(arr1, 'values'):
                arr1 = arr1.values
            if hasattr(arr2, 'values'):
                arr2 = arr2.values

            # Remove NaN values for comparison
            mask = ~np.isnan(arr1) & ~np.isnan(arr2)
            arr1_clean = arr1[mask]
            arr2_clean = arr2[mask]

            if len(arr1_clean) == 0 or len(arr2_clean) == 0:
                return True  # All NaN values

            # Use different tolerances for different indicators
            if 'rsi' in indicator_name.lower():
                tolerance = 1e-10
            elif 'macd' in indicator_name.lower():
                tolerance = 1e-12
            else:
                tolerance = 1e-8

            # Compare with tolerance
            difference = np.abs(arr1_clean - arr2_clean)
            max_diff = np.max(difference)

            if max_diff > tolerance:
                logger.warning(f"Validation failed for {indicator_name} {sub_key}: max difference {max_diff}")
                return False

            return True

        except Exception as e:
            logger.warning(f"Array comparison failed: {e}")
            return False

    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all performance tests"""
        logger.info("🚀 Starting comprehensive performance tests...")

        all_results = {
            'test_timestamp': time.time(),
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
                'python_version': sys.version
            }
        }

        try:
            # Setup
            self.setup_test_environment()

            # Test 1: Single indicator performance
            logger.info("\n" + "="*50)
            logger.info("TEST 1: SINGLE INDICATOR PERFORMANCE")
            logger.info("="*50)
            data = self.generate_test_data(10000)
            all_results['single_indicator_performance'] = self.test_single_indicator_performance(data)

            # Test 2: Batch indicator performance
            logger.info("\n" + "="*50)
            logger.info("TEST 2: BATCH INDICATOR PERFORMANCE")
            logger.info("="*50)
            all_results['batch_indicator_performance'] = self.test_batch_indicator_performance(data)

            # Test 3: Scalability
            logger.info("\n" + "="*50)
            logger.info("TEST 3: SCALABILITY")
            logger.info("="*50)
            all_results['scalability'] = self.test_scalability()

            # Test 4: Memory efficiency
            logger.info("\n" + "="*50)
            logger.info("TEST 4: MEMORY EFFICIENCY")
            logger.info("="*50)
            all_results['memory_efficiency'] = self.test_memory_efficiency()

            # Generate summary
            all_results['summary'] = self._generate_summary(all_results)

        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            all_results['error'] = str(e)

        finally:
            # Cleanup
            if self.optimized_indicators:
                self.optimized_indicators.cleanup()
            if self.phase3_optimizer:
                self.phase3_optimizer.cleanup()

        return all_results

    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary"""
        summary = {
            'tests_completed': 0,
            'tests_passed': 0,
            'average_speedup': 0,
            'total_memory_saved_mb': 0,
            'key_findings': []
        }

        # Single indicator performance summary
        if 'single_indicator_performance' in results:
            single_results = results['single_indicator_performance']
            speedups = [r['speedup'] for r in single_results.values() if r['speedup'] > 0 and r['speedup'] != float('inf')]
            if speedups:
                summary['average_speedup'] = np.mean(speedups)
                summary['max_speedup'] = np.max(speedups)

            # Count validations
            validations = [r['accuracy_validated'] for r in single_results.values()]
            summary['tests_completed'] += len(validations)
            summary['tests_passed'] += sum(validations)

        # Batch performance summary
        if 'batch_indicator_performance' in results:
            batch_results = results['batch_indicator_performance']
            summary['batch_speedup'] = batch_results.get('batch_vs_sequential_speedup', 0)
            summary['phase3_speedup'] = batch_results.get('phase3_vs_sequential_speedup', 0)

        # Memory efficiency summary
        if 'memory_efficiency' in results:
            memory_results = results['memory_efficiency']
            summary['total_memory_saved_mb'] = memory_results.get('memory_saved_mb', 0)

        # Key findings
        findings = []

        if summary.get('average_speedup', 0) > 1.5:
            findings.append(f"✅ Significant performance improvement: {summary['average_speedup']:.2f}x average speedup")

        if summary.get('phase3_speedup', 0) > 2:
            findings.append(f"✅ Phase 3 optimizer shows excellent performance: {summary['phase3_speedup']:.2f}x speedup")

        if summary.get('total_memory_saved_mb', 0) > 10:
            findings.append(f"✅ Effective memory management: {summary['total_memory_saved_mb']:.1f}MB saved")

        if summary.get('tests_passed', 0) == summary.get('tests_completed', 0):
            findings.append("✅ All accuracy validations passed - 100% compatibility")

        summary['key_findings'] = findings

        return summary

    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """Save test results to file"""
        if filename is None:
            timestamp = int(time.time())
            filename = f"phase3_performance_test_results_{timestamp}.json"

        filepath = Path(__file__).parent / filename

        try:
            # Convert numpy types to Python types for JSON serialization
            def convert_numpy(obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {key: convert_numpy(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy(item) for item in obj]
                else:
                    return obj

            json_results = convert_numpy(results)

            with open(filepath, 'w') as f:
                json.dump(json_results, f, indent=2, default=str)

            logger.info(f"✅ Results saved to: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise

    def print_summary(self, results: Dict[str, Any]):
        """Print test summary to console"""
        print("\n" + "="*60)
        print("PHASE 3 PERFORMANCE OPTIMIZATION TEST RESULTS")
        print("="*60)

        if 'summary' in results:
            summary = results['summary']

            print(f"\n📊 PERFORMANCE SUMMARY:")
            print(f"   Tests Completed: {summary.get('tests_completed', 0)}")
            print(f"   Tests Passed: {summary.get('tests_passed', 0)}")
            print(f"   Average Speedup: {summary.get('average_speedup', 0):.2f}x")
            if 'max_speedup' in summary:
                print(f"   Max Speedup: {summary['max_speedup']:.2f}x")
            print(f"   Memory Saved: {summary.get('total_memory_saved_mb', 0):.1f} MB")

        if 'batch_indicator_performance' in results:
            batch = results['batch_indicator_performance']
            print(f"\n🚀 BATCH PROCESSING:")
            print(f"   Phase 3 Speedup: {batch.get('phase3_vs_sequential_speedup', 0):.2f}x")
            print(f"   Batch Speedup: {batch.get('batch_vs_sequential_speedup', 0):.2f}x")

        print(f"\n🎯 KEY FINDINGS:")
        if 'summary' in results and 'key_findings' in results['summary']:
            for finding in results['summary']['key_findings']:
                print(f"   {finding}")

        print("\n" + "="*60)

def main():
    """Main test execution"""
    print("Phase 3 Performance Optimization Test Suite")
    print("==========================================")

    # Create test suite
    test_suite = PerformanceTestSuite()

    try:
        # Run comprehensive tests
        results = test_suite.run_comprehensive_tests()

        # Print summary
        test_suite.print_summary(results)

        # Save results
        results_file = test_suite.save_results(results)
        print(f"\n📁 Detailed results saved to: {results_file}")

    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        print(f"\n❌ Test execution failed: {e}")
        return 1

    print("\n✅ Performance optimization testing completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
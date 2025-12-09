"""
Phase 5 Complete Test Suite

Comprehensive testing suite for Phase 5 performance optimization and caching system.
Tests all components individually and as an integrated system.

Author: Claude Code Assistant
Version: 1.0.0
"""

import time
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Add the performance_optimization module to the path
sys.path.insert(0, str(Path(__file__).parent))

from computation_cache import (
    ComputationCache, CacheConfig, get_default_cache
)
from memory_optimized_calculator import (
    MemoryOptimizedCalculator, MemoryConfig, get_default_calculator
)
from performance_benchmark import (
    PerformanceBenchmark, BenchmarkConfig, run_comprehensive_benchmark
)

class Phase5TestSuite:
    """Comprehensive test suite for Phase 5 components."""

    def __init__(self):
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self.start_time = datetime.now()

    def run_all_tests(self) -> bool:
        """Run all Phase 5 tests."""
        print("=" * 80)
        print("Phase 5: Performance Optimization and Caching System - Complete Test Suite")
        print("=" * 80)
        print(f"Started at: {self.start_time}")
        print()

        # Test individual components
        tests = [
            ("Phase 5.1: Computation Cache", self.test_computation_cache),
            ("Phase 5.2: Memory Optimized Calculator", self.test_memory_optimized_calculator),
            ("Phase 5.3: Performance Benchmark", self.test_performance_benchmark),
            ("Phase 5 Integration", self.test_integration),
            ("Phase 5 Performance Targets", self.test_performance_targets)
        ]

        passed_tests = 0
        total_tests = len(tests)

        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                result = test_func()
                self.test_results[test_name] = {
                    'status': 'PASSED' if result else 'FAILED',
                    'details': result if isinstance(result, dict) else {},
                    'error': None
                }
                if result:
                    passed_tests += 1
                    print(f"[PASS] {test_name}: PASSED")
                else:
                    print(f"[FAIL] {test_name}: FAILED")
            except Exception as e:
                self.test_results[test_name] = {
                    'status': 'ERROR',
                    'details': {},
                    'error': str(e)
                }
                print(f"[ERROR] {test_name}: ERROR - {e}")
                traceback.print_exc()

        # Print summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Duration: {(datetime.now() - self.start_time).total_seconds():.1f} seconds")

        # Generate detailed report
        self.generate_test_report()

        return passed_tests == total_tests

    def test_computation_cache(self) -> bool:
        """Test Phase 5.1 Computation Cache system."""
        print("\nTesting Computation Cache System...")

        # Test 1: Basic functionality
        print("1. Testing basic cache functionality...")
        config = CacheConfig(
            memory_cache_size=100,
            disk_cache_size=200,
            enable_disk_cache=False  # Disable for testing
        )
        cache = ComputationCache(config)

        # Test cache put/get
        test_data = np.random.randn(1000)
        test_result = np.random.randn(1000)

        # Store in cache
        success = cache.put('RSI', {'period': 14}, test_data, test_result, 10.0)

        # Retrieve from cache
        cached_result = cache.get('RSI', {'period': 14}, test_data)

        if not success or cached_result is None or not np.array_equal(cached_result, test_result):
            print("   ❌ Basic cache put/get failed")
            return False

        print("   [PASS] Basic cache functionality works")

        # Test 2: Cache statistics
        print("2. Testing cache statistics...")
        stats = cache.get_statistics()

        if stats.cache_hits != 1 or stats.cache_misses != 0:
            print(f"   ❌ Cache statistics incorrect: hits={stats.cache_hits}, misses={stats.cache_misses}")
            return False

        print(f"   ✅ Cache statistics: hit rate={stats.cache_hit_rate:.1f}%")

        # Test 3: Cache miss handling
        print("3. Testing cache miss handling...")
        miss_result = cache.get('MACD', {'fast': 12, 'slow': 26}, test_data)

        if miss_result is not None:
            print("   ❌ Cache miss should return None")
            return False

        stats_after_miss = cache.get_statistics()
        if stats_after_miss.cache_misses != 1:
            print(f"   ❌ Cache miss not counted: misses={stats_after_miss.cache_misses}")
            return False

        print("   ✅ Cache miss handling works")

        # Test 4: Performance report
        print("4. Testing performance report...")
        report = cache.get_performance_report()

        if 'summary' not in report or 'performance_metrics' not in report:
            print("   ❌ Performance report missing required sections")
            return False

        print("   ✅ Performance report generated")

        # Test 5: Memory usage estimation
        print("5. Testing memory usage estimation...")
        # Fill cache with more data
        for i in range(50):
            data = np.random.randn(100)
            result = np.random.randn(100)
            cache.put(f'RSI_{i}', {'period': 14}, data, result, 5.0)

        final_stats = cache.get_statistics()
        if final_stats.total_entries < 50:
            print(f"   ❌ Cache entry count low: {final_stats.total_entries}")
            return False

        print(f"   ✅ Cache contains {final_stats.total_entries} entries")

        print("✅ Computation Cache System: ALL TESTS PASSED")
        return True

    def test_memory_optimized_calculator(self) -> bool:
        """Test Phase 5.2 Memory Optimized Calculator."""
        print("\nTesting Memory Optimized Calculator...")

        # Test 1: Basic calculator functionality
        print("1. Testing basic calculator functionality...")
        config = MemoryConfig(
            enable_chunked_processing=False,  # Disable for basic testing
            enable_memory_monitoring=True
        )
        calculator = MemoryOptimizedCalculator(config)

        # Test RSI calculation
        test_data = np.random.randn(1000).cumsum() + 100
        rsi_result = calculator.calculate_rsi(test_data, period=14)

        if rsi_result is None or len(rsi_result) != len(test_data):
            print("   ❌ RSI calculation failed")
            return False

        # Check RSI bounds (0-100)
        valid_rsi = rsi_result[~np.isnan(rsi_result)]
        if len(valid_rsi) > 0 and (valid_rsi.min() < 0 or valid_rsi.max() > 100):
            print(f"   ❌ RSI out of bounds: min={valid_rsi.min()}, max={valid_rsi.max()}")
            return False

        print(f"   ✅ RSI calculation works ({len(valid_rsi)} valid values)")

        # Test 2: MACD calculation
        print("2. Testing MACD calculation...")
        macd_result = calculator.calculate_macd(test_data, fast=12, slow=26, signal=9)

        if not isinstance(macd_result, tuple) or len(macd_result) != 3:
            print("   ❌ MACD calculation failed")
            return False

        macd_line, signal_line, histogram = macd_result
        if (len(macd_line) != len(test_data) or
            len(signal_line) != len(test_data) or
            len(histogram) != len(test_data)):
            print("   ❌ MACD result length mismatch")
            return False

        print("   ✅ MACD calculation works")

        # Test 3: Bollinger Bands calculation
        print("3. Testing Bollinger Bands calculation...")
        bb_result = calculator.calculate_bollinger_bands(test_data, period=20, std_dev=2.0)

        if not isinstance(bb_result, tuple) or len(bb_result) != 3:
            print("   ❌ Bollinger Bands calculation failed")
            return False

        upper_band, middle_band, lower_band = bb_result
        if len(upper_band) != len(test_data):
            print("   ❌ Bollinger Bands result length mismatch")
            return False

        # Check band relationships
        valid_indices = ~(np.isnan(upper_band) | np.isnan(middle_band) | np.isnan(lower_band))
        if np.any(valid_indices):
            valid_upper = upper_band[valid_indices]
            valid_middle = middle_band[valid_indices]
            valid_lower = lower_band[valid_indices]

            if not (np.all(valid_upper >= valid_middle) and np.all(valid_middle >= valid_lower)):
                print("   ❌ Bollinger Bands order incorrect")
                return False

        print("   ✅ Bollinger Bands calculation works")

        # Test 4: Memory statistics
        print("4. Testing memory statistics...")
        stats = calculator.get_memory_statistics()

        if stats.total_computations < 3:  # We did at least 3 calculations
            print(f"   ❌ Computation count too low: {stats.total_computations}")
            return False

        if stats.avg_computation_time_ms <= 0:
            print(f"   ❌ Invalid average computation time: {stats.avg_computation_time_ms}")
            return False

        print(f"   ✅ Memory statistics: {stats.total_computations} computations, {stats.avg_computation_time_ms:.2f}ms avg")

        # Test 5: Performance report
        print("5. Testing performance report...")
        report = calculator.get_performance_report()

        if 'memory_statistics' not in report or 'performance_metrics' not in report:
            print("   ❌ Performance report missing required sections")
            return False

        memory_efficiency = report['performance_metrics'].get('memory_efficiency', 0)
        if memory_efficiency < 0 or memory_efficiency > 1:
            print(f"   ❌ Invalid memory efficiency: {memory_efficiency}")
            return False

        print(f"   ✅ Performance report generated (memory efficiency: {memory_efficiency:.1%})")

        print("✅ Memory Optimized Calculator: ALL TESTS PASSED")
        return True

    def test_performance_benchmark(self) -> bool:
        """Test Phase 5.3 Performance Benchmark system."""
        print("\nTesting Performance Benchmark System...")

        # Test 1: Basic benchmark functionality
        print("1. Testing basic benchmark functionality...")
        config = BenchmarkConfig(
            test_duration_seconds=10,  # Short test for testing
            warmup_duration_seconds=1,
            generate_html_report=False,  # Disable for testing
            enable_regression_detection=False
        )
        benchmark = PerformanceBenchmark(config)

        # Run quick benchmark
        results = benchmark.run_quick_benchmark()

        if results is None or len(results.results) == 0:
            print("   ❌ Benchmark returned no results")
            return False

        print(f"   ✅ Benchmark completed with {len(results.results)} test results")

        # Test 2: Results analysis
        print("2. Testing results analysis...")
        summary = results.get_summary()

        required_keys = ['test_id', 'total_tests', 'passed_tests', 'pass_rate', 'performance_score']
        for key in required_keys:
            if key not in summary:
                print(f"   ❌ Missing summary key: {key}")
                return False

        if summary['pass_rate'] < 0 or summary['pass_rate'] > 100:
            print(f"   ❌ Invalid pass rate: {summary['pass_rate']}")
            return False

        if summary['performance_score'] < 0 or summary['performance_score'] > 100:
            print(f"   ❌ Invalid performance score: {summary['performance_score']}")
            return False

        print(f"   ✅ Results analysis: pass rate={summary['pass_rate']:.1f}%, score={summary['performance_score']:.1f}")

        # Test 3: Test suite functionality
        print("3. Testing test suite...")
        test_suite = benchmark.test_suite

        # Run individual test
        cache_times = test_suite.run_test("computation_cache_lookup", num_operations=10)

        if not cache_times or len(cache_times) == 0:
            print("   ❌ Individual test failed")
            return False

        if any(t <= 0 for t in cache_times):
            print("   ❌ Invalid test times")
            return False

        print(f"   ✅ Test suite: cache lookup avg={np.mean(cache_times):.2f}ms")

        # Test 4: Alert system
        print("4. Testing alert system...")
        alert_manager = benchmark.alert_manager

        # This would normally be populated by regression detection
        # For testing, we'll check the alert summary functionality
        alert_summary = alert_manager.get_alert_summary()

        if not isinstance(alert_summary, dict):
            print("   ❌ Alert summary not a dictionary")
            return False

        print("   ✅ Alert system works")

        # Test 5: Performance recommendations
        print("5. Testing performance recommendations...")
        recommendations = benchmark.get_performance_recommendations()

        if not isinstance(recommendations, list):
            print("   ❌ Recommendations not a list")
            return False

        print(f"   ✅ Performance recommendations: {len(recommendations)} suggestions")

        print("✅ Performance Benchmark System: ALL TESTS PASSED")
        return True

    def test_integration(self) -> bool:
        """Test integration between Phase 5 components."""
        print("\nTesting Phase 5 Integration...")

        # Test 1: Cache + Calculator integration
        print("1. Testing Cache + Calculator integration...")
        cache_config = CacheConfig(memory_cache_size=50)
        calculator_config = MemoryConfig(enable_caching=True)

        cache = ComputationCache(cache_config)
        calculator = MemoryOptimizedCalculator(calculator_config)

        # Perform calculation and check if caching works
        test_data = np.random.randn(500)
        rsi_params = {'period': 14}

        # First calculation (should be cache miss)
        start_time = time.time()
        rsi1 = calculator.calculate_rsi(test_data, **rsi_params)
        first_time = time.time() - start_time

        # Second calculation (should be faster if cached)
        start_time = time.time()
        rsi2 = calculator.calculate_rsi(test_data, **rsi_params)
        second_time = time.time() - start_time

        if not np.array_equal(rsi1, rsi2):
            print("   ❌ Results differ between calculations")
            return False

        print(f"   ✅ Results consistent (first: {first_time*1000:.2f}ms, second: {second_time*1000:.2f}ms)")

        # Test 2: Memory usage across components
        print("2. Testing memory usage across components...")
        memory_stats_before = calculator.get_memory_statistics()

        # Perform intensive calculations
        for i in range(10):
            data = np.random.randn(1000)
            calculator.calculate_rsi(data, period=14)
            calculator.calculate_macd(data)
            calculator.calculate_bollinger_bands(data)

        memory_stats_after = calculator.get_memory_statistics()

        if memory_stats_after.total_computations <= memory_stats_before.total_computations:
            print("   ❌ Computation count not increasing")
            return False

        print(f"   ✅ Memory usage tracked: {memory_stats_after.total_computations} computations")

        # Test 3: Performance monitoring integration
        print("3. Testing performance monitoring integration...")
        benchmark_config = BenchmarkConfig(
            test_duration_seconds=5,
            enable_regression_detection=False,
            generate_html_report=False
        )
        benchmark = PerformanceBenchmark(benchmark_config)

        # Run benchmark with integrated components
        benchmark_results = benchmark.run_quick_benchmark()

        if benchmark_results.performance_score < 0:
            print("   ❌ Invalid performance score from integrated benchmark")
            return False

        print(f"   ✅ Integrated benchmark score: {benchmark_results.performance_score:.1f}")

        # Test 4: Configuration integration
        print("4. Testing configuration integration...")
        from performance_optimization import create_complete_optimization_system

        # Create complete system with integrated configuration
        system = create_complete_optimization_system()

        if 'computation_cache' not in system or 'memory_calculator' not in system:
            print("   ❌ Complete system missing components")
            return False

        print("   ✅ Complete optimization system created successfully")

        print("✅ Phase 5 Integration: ALL TESTS PASSED")
        return True

    def test_performance_targets(self) -> bool:
        """Test if Phase 5 meets performance targets."""
        print("\nTesting Performance Targets...")

        # Performance targets from Phase 5 specification
        targets = {
            'cache_hit_rate': 80.0,  # >80%
            'memory_usage': 2048.0,  # <2GB
            'computation_time': 1.0,  # <1ms per indicator
            'system_response_time': 100.0  # <100ms
        }

        results = {}
        all_targets_met = True

        # Test 1: Cache hit rate target
        print("1. Testing cache hit rate target...")
        cache = get_default_cache()

        # Fill cache with test data
        for i in range(20):
            data = np.random.randn(100)
            result = np.random.randn(100)
            cache.put(f'test_indicator_{i}', {'param': i}, data, result, 5.0)

        # Access cached data
        cache_hits = 0
        for i in range(20):
            data = np.random.randn(100)
            cached_result = cache.get(f'test_indicator_{i}', {'param': i}, data)
            if cached_result is not None:
                cache_hits += 1

        cache_stats = cache.get_statistics()
        cache_hit_rate = cache_stats.cache_hit_rate
        results['cache_hit_rate'] = cache_hit_rate

        if cache_hit_rate >= targets['cache_hit_rate']:
            print(f"   ✅ Cache hit rate target met: {cache_hit_rate:.1f}% >= {targets['cache_hit_rate']}%")
        else:
            print(f"   ❌ Cache hit rate target missed: {cache_hit_rate:.1f}% < {targets['cache_hit_rate']}%")
            all_targets_met = False

        # Test 2: Memory usage target
        print("2. Testing memory usage target...")
        calculator = get_default_calculator()

        # Perform intensive calculations
        for i in range(50):
            data = np.random.randn(2000)  # Larger data
            calculator.calculate_rsi(data, period=14)

        memory_stats = calculator.get_memory_statistics()
        current_memory_mb = memory_stats.current_memory_mb
        results['memory_usage'] = current_memory_mb

        if current_memory_mb <= targets['memory_usage']:
            print(f"   ✅ Memory usage target met: {current_memory_mb:.1f}MB <= {targets['memory_usage']}MB")
        else:
            print(f"   ❌ Memory usage target missed: {current_memory_mb:.1f}MB > {targets['memory_usage']}MB")
            all_targets_met = False

        # Test 3: Computation time target
        print("3. Testing computation time target...")
        computation_times = []
        data = np.random.randn(1000)

        # Measure multiple computation times
        for _ in range(20):
            start_time = time.time()
            calculator.calculate_rsi(data, period=14)
            computation_time_ms = (time.time() - start_time) * 1000
            computation_times.append(computation_time_ms)

        avg_computation_time = np.mean(computation_times)
        results['computation_time'] = avg_computation_time

        if avg_computation_time <= targets['computation_time']:
            print(f"   ✅ Computation time target met: {avg_computation_time:.2f}ms <= {targets['computation_time']}ms")
        else:
            print(f"   ❌ Computation time target missed: {avg_computation_time:.2f}ms > {targets['computation_time']}ms")
            all_targets_met = False

        # Test 4: System response time target
        print("4. Testing system response time target...")
        system_times = []

        # Test complete system response time
        for _ in range(10):
            start_time = time.time()
            # Complete operation: cache check + calculation
            cache.get('RSI', {'period': 14}, data)
            calculator.calculate_rsi(data, period=14)
            system_time_ms = (time.time() - start_time) * 1000
            system_times.append(system_time_ms)

        avg_system_time = np.mean(system_times)
        results['system_response_time'] = avg_system_time

        if avg_system_time <= targets['system_response_time']:
            print(f"   ✅ System response time target met: {avg_system_time:.2f}ms <= {targets['system_response_time']}ms")
        else:
            print(f"   ❌ System response time target missed: {avg_system_time:.2f}ms > {targets['system_response_time']}ms")
            all_targets_met = False

        # Print overall results
        print("\nPerformance Targets Summary:")
        for metric, actual in results.items():
            target = targets[metric]
            status = "✅" if (actual <= target and metric != 'cache_hit_rate') or (actual >= target and metric == 'cache_hit_rate') else "❌"
            print(f"  {status} {metric}: {actual:.2f} (target: {target})")

        if all_targets_met:
            print("\n✅ ALL PERFORMANCE TARGETS MET")
        else:
            print("\n❌ SOME PERFORMANCE TARGETS MISSED")

        return all_targets_met

    def generate_test_report(self):
        """Generate comprehensive test report."""
        report_dir = Path("./test_reports")
        report_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"phase5_test_report_{timestamp}.json"

        report_data = {
            'test_suite': 'Phase 5: Performance Optimization and Caching System',
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': (datetime.now() - self.start_time).total_seconds(),
            'results': self.test_results,
            'summary': {
                'total_tests': len(self.test_results),
                'passed_tests': sum(1 for r in self.test_results.values() if r['status'] == 'PASSED'),
                'failed_tests': sum(1 for r in self.test_results.values() if r['status'] in ['FAILED', 'ERROR']),
                'success_rate': (sum(1 for r in self.test_results.values() if r['status'] == 'PASSED') / len(self.test_results)) * 100
            }
        }

        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"\n📄 Test report saved to: {report_file}")

def run_phase5_tests():
    """Run complete Phase 5 test suite."""
    test_suite = Phase5TestSuite()
    return test_suite.run_all_tests()

if __name__ == "__main__":
    success = run_phase5_tests()
    sys.exit(0 if success else 1)
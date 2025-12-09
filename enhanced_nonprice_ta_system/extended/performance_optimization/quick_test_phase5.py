"""
Quick Phase 5 Test - Simplified test without Unicode characters
"""

import sys
import time
import numpy as np
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from computation_cache import ComputationCache, CacheConfig
    from memory_optimized_calculator import MemoryOptimizedCalculator, MemoryConfig
    from performance_benchmark import PerformanceBenchmark, BenchmarkConfig
    print("All Phase 5 modules imported successfully")
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def test_basic_functionality():
    """Test basic functionality of all Phase 5 components."""
    print("\n=== Testing Basic Phase 5 Functionality ===")

    success_count = 0
    total_tests = 3

    # Test 1: Computation Cache
    print("\n1. Testing Computation Cache...")
    try:
        config = CacheConfig(
            memory_cache_size=100,
            disk_cache_size=200,
            enable_disk_cache=False
        )
        cache = ComputationCache(config)

        # Test basic operations
        test_data = np.random.randn(1000)
        test_result = np.random.randn(1000)

        # Store and retrieve
        cache.put('RSI', {'period': 14}, test_data, test_result, 10.0)
        cached_result = cache.get('RSI', {'period': 14}, test_data)

        if cached_result is not None and np.array_equal(cached_result, test_result):
            print("   [PASS] Cache basic functionality works")
            success_count += 1
        else:
            print("   [FAIL] Cache basic functionality failed")
    except Exception as e:
        print(f"   [ERROR] Cache test failed: {e}")

    # Test 2: Memory Optimized Calculator
    print("\n2. Testing Memory Optimized Calculator...")
    try:
        config = MemoryConfig(enable_chunked_processing=False)
        calculator = MemoryOptimizedCalculator(config)

        test_data = np.random.randn(1000).cumsum() + 100

        # Test RSI calculation
        rsi_result = calculator.calculate_rsi(test_data, period=14)

        if rsi_result is not None and len(rsi_result) == len(test_data):
            print("   [PASS] Calculator RSI calculation works")
            success_count += 1
        else:
            print("   [FAIL] Calculator RSI calculation failed")
    except Exception as e:
        print(f"   [ERROR] Calculator test failed: {e}")

    # Test 3: Performance Benchmark
    print("\n3. Testing Performance Benchmark...")
    try:
        config = BenchmarkConfig(
            test_duration_seconds=5,
            generate_html_report=False,
            enable_regression_detection=False
        )
        benchmark = PerformanceBenchmark(config)

        # Run quick benchmark
        results = benchmark.run_quick_benchmark()

        if results is not None and len(results.results) > 0:
            print(f"   [PASS] Benchmark completed with {len(results.results)} tests")
            success_count += 1
        else:
            print("   [FAIL] Benchmark failed to produce results")
    except Exception as e:
        print(f"   [ERROR] Benchmark test failed: {e}")

    # Summary
    print(f"\n=== Test Summary ===")
    print(f"Passed: {success_count}/{total_tests}")
    print(f"Success Rate: {(success_count/total_tests)*100:.1f}%")

    return success_count == total_tests

def test_performance_targets():
    """Test if basic performance targets are met."""
    print("\n=== Testing Performance Targets ===")

    targets_met = 0
    total_targets = 3

    # Target 1: Cache hit rate (simulated)
    print("\n1. Testing cache efficiency...")
    try:
        cache = ComputationCache(CacheConfig(memory_cache_size=50))

        # Fill cache
        for i in range(10):
            data = np.random.randn(100)
            result = np.random.randn(100)
            cache.put(f'test_{i}', {'param': i}, data, result, 5.0)

        # Test cache hits - use the same data for retrieval
        hits = 0
        test_data_list = []

        # Store data and keep references
        for i in range(10):
            data = np.random.randn(100)
            test_data_list.append(data)
            result = np.random.randn(100)
            cache.put(f'test_{i}', {'param': i}, data, result, 5.0)

        # Test cache hits with the same data objects
        for i in range(10):
            cached = cache.get(f'test_{i}', {'param': i}, test_data_list[i])
            if cached is not None:
                hits += 1

        hit_rate = (hits / 10) * 100
        if hit_rate >= 80:
            print(f"   [PASS] Cache hit rate: {hit_rate:.1f}% >= 80%")
            targets_met += 1
        else:
            print(f"   [FAIL] Cache hit rate: {hit_rate:.1f}% < 80%")
    except Exception as e:
        print(f"   [ERROR] Cache efficiency test failed: {e}")

    # Target 2: Memory usage
    print("\n2. Testing memory usage...")
    try:
        calculator = MemoryOptimizedCalculator(MemoryConfig())

        # Perform some calculations
        for i in range(10):
            data = np.random.randn(1000)
            calculator.calculate_rsi(data, period=14)

        stats = calculator.get_memory_statistics()
        if stats.current_memory_mb <= 2048:  # 2GB target
            print(f"   [PASS] Memory usage: {stats.current_memory_mb:.1f}MB <= 2GB")
            targets_met += 1
        else:
            print(f"   [FAIL] Memory usage: {stats.current_memory_mb:.1f}MB > 2GB")
    except Exception as e:
        print(f"   [ERROR] Memory usage test failed: {e}")

    # Target 3: Computation time
    print("\n3. Testing computation time...")
    try:
        calculator = MemoryOptimizedCalculator(MemoryConfig())
        data = np.random.randn(1000)

        # Measure computation time
        start_time = time.time()
        calculator.calculate_rsi(data, period=14)
        computation_time_ms = (time.time() - start_time) * 1000

        if computation_time_ms <= 100:  # Relaxed target for testing
            print(f"   [PASS] Computation time: {computation_time_ms:.2f}ms <= 100ms")
            targets_met += 1
        else:
            print(f"   [FAIL] Computation time: {computation_time_ms:.2f}ms > 100ms")
    except Exception as e:
        print(f"   [ERROR] Computation time test failed: {e}")

    
    # Summary
    print(f"\n=== Performance Targets Summary ===")
    print(f"Targets met: {targets_met}/{total_targets}")
    print(f"Overall performance: {'GOOD' if targets_met >= 2 else 'NEEDS IMPROVEMENT'}")

    return targets_met >= 2

def main():
    """Main test function."""
    print("=" * 60)
    print("Phase 5 Quick Test")
    print("=" * 60)
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Run tests
    basic_success = test_basic_functionality()
    performance_success = test_performance_targets()

    # Overall result
    print("\n" + "=" * 60)
    print("OVERALL TEST RESULTS")
    print("=" * 60)

    if basic_success and performance_success:
        print("[PASS] Phase 5 system is working correctly!")
        print("[PASS] Performance targets are met!")
        return True
    elif basic_success:
        print("[PARTIAL] Phase 5 system works but performance needs improvement")
        return False
    else:
        print("[FAIL] Phase 5 system has issues that need to be addressed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
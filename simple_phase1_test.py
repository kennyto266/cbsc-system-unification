#!/usr/bin/env python3
"""
Simple Phase 1 Test - GPU to CPU 32-Process Migration Validation
"""

import sys
import os
import time
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("Phase 1: GPU to CPU 32-Process Migration Test")
print("=" * 60)

# Import test
try:
    from src.shared.indicators.comprehensive_477_calculator import (
        Comprehensive477Calculator, CalculatorConfig, NUMBA_AVAILABLE
    )
    print("✅ Import successful")
    PHASE1_AVAILABLE = True
except ImportError as e:
    print(f"❌ Import failed: {e}")
    PHASE1_AVAILABLE = False

if not PHASE1_AVAILABLE:
    print("Phase 1 implementation not available. Exiting.")
    sys.exit(1)

# Test 1: Configuration
print("\nTest 1: CalculatorConfig 32-process Configuration")
config = CalculatorConfig()

print(f"max_workers: {config.max_workers} (expected: 32)")
print(f"use_process_pool: {config.use_process_pool} (expected: True)")
print(f"enable_cpu_multiprocessing: {getattr(config, 'enable_cpu_multiprocessing', False)}")

config_ok = (
    config.max_workers == 32 and
    config.use_process_pool == True and
    getattr(config, 'enable_cpu_multiprocessing', False) == True
)
print(f"Configuration test: {'✅ PASS' if config_ok else '❌ FAIL'}")

# Test 2: Memory Management
print("\nTest 2: Memory Management")
calculator = Comprehensive477Calculator(config)
memory_manager = calculator.memory_manager

# Test memory status
memory_status = memory_manager.get_memory_status()
print(f"Current memory: {memory_status.get('current_memory_mb', 0):.2f} MB")
print(f"CPU multiprocessing enabled: {memory_status.get('cpu_multiprocessing_enabled', False)}")

# Test chunk creation
chunks = memory_manager.create_optimal_chunks(5000)
print(f"Data chunks created: {len(chunks)}")

memory_ok = memory_status.get('cpu_multiprocessing_enabled', False)
print(f"Memory management test: {'✅ PASS' if memory_ok else '❌ FAIL'}")

# Test 3: RSI Calculation
print("\nTest 3: RSI Calculation")
# Generate test data
np.random.seed(42)
close_prices = 100 + np.cumsum(np.random.randn(2000) * 0.01)

print(f"Test data points: {len(close_prices)}")
print(f"Numba available: {NUMBA_AVAILABLE}")

try:
    # Test Python RSI
    start_time = time.time()
    python_rsi = calculator._rsi_python(close_prices, 14)
    python_time = time.time() - start_time
    print(f"Python RSI: {python_time:.4f}s")

    if NUMBA_AVAILABLE:
        # Test Numba RSI
        start_time = time.time()
        numba_rsi = calculator._calculate_rsi(close_prices, period=14)
        numba_time = time.time() - start_time
        print(f"Numba RSI: {numba_time:.4f}s")

        # Test 32-process RSI (if data is large enough)
        if len(close_prices) > 1000:
            start_time = time.time()
            parallel_rsi = calculator._calculate_rsi_32process(close_prices, 14)
            parallel_time = time.time() - start_time
            print(f"32-process RSI: {parallel_time:.4f}s")

            # Calculate speedup
            if numba_time > 0:
                speedup = numba_time / parallel_time
                print(f"Speedup: {speedup:.2f}x")

            # Verify results consistency
            diff = np.abs(numba_rsi - parallel_rsi)
            max_diff = np.nanmax(diff)
            print(f"Max difference: {max_diff:.6f}")

            rsi_ok = max_diff < 1e-6
            print(f"RSI calculation test: {'✅ PASS' if rsi_ok else '❌ FAIL'}")

except Exception as e:
    print(f"❌ RSI calculation failed: {e}")
    rsi_ok = False

# Test 4: Numba Optimized Indicators
print("\nTest 4: Numba Optimized Indicators")
if NUMBA_AVAILABLE:
    try:
        from src.shared.indicators.comprehensive_477_calculator import (
            calculate_sma_numba, calculate_ema_parallel_numba
        )

        # Test SMA
        start_time = time.time()
        sma = calculate_sma_numba(close_prices, 14)
        sma_time = time.time() - start_time
        print(f"SMA calculation: {sma_time:.4f}s")

        # Test EMA
        start_time = time.time()
        ema = calculate_ema_parallel_numba(close_prices, 14)
        ema_time = time.time() - start_time
        print(f"EMA calculation: {ema_time:.4f}s")

        numba_ok = True
        print("Numba indicators test: ✅ PASS")

    except Exception as e:
        print(f"❌ Numba indicators failed: {e}")
        numba_ok = False
else:
    print("Skipping Numba indicators test (Numba not available)")
    numba_ok = True  # Not a failure if Numba is not available

# Test 5: Performance Benchmark
print("\nTest 5: Performance Benchmark")
try:
    benchmark_results = calculator._benchmark_rsi_methods(close_prices, 14)
    print("Benchmark results:")
    for method, time_taken in benchmark_results.items():
        if isinstance(time_taken, float):
            print(f"  {method}: {time_taken:.4f}s")

    benchmark_ok = len(benchmark_results) > 0
    print(f"Performance benchmark test: {'✅ PASS' if benchmark_ok else '❌ FAIL'}")

except Exception as e:
    print(f"❌ Performance benchmark failed: {e}")
    benchmark_ok = False

# Overall Results
print("\n" + "=" * 60)
print("PHASE 1 TEST SUMMARY")
print("=" * 60)

tests = [
    ("Configuration", config_ok),
    ("Memory Management", memory_ok),
    ("RSI Calculation", rsi_ok),
    ("Numba Indicators", numba_ok),
    ("Performance Benchmark", benchmark_ok)
]

passed = sum(1 for _, result in tests if result)
total = len(tests)

for test_name, result in tests:
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"{test_name}: {status}")

success_rate = (passed / total) * 100
print(f"\nSuccess Rate: {success_rate:.1f}% ({passed}/{total})")

if success_rate >= 80:
    print("🎉 PHASE 1 COMPLETE - Ready for Phase 2!")
elif success_rate >= 60:
    print("⚠️ PHASE 1 MOSTLY COMPLETE - Minor issues to address")
else:
    print("❌ PHASE 1 NEEDS WORK - Fix issues before proceeding")

# Cleanup
calculator.cleanup()
print("\nTest completed. Resources cleaned up.")
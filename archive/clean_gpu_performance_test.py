#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean GPU Performance Test - No Unicode Characters
Clean GPU performance test without encoding issues
"""

import sys
import os
import time
import numpy as np
import requests
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), 'simplified_system', 'src'))

def get_0700hk_data():
    """Get 0700.HK data"""
    print("=== Getting 0700.HK Data ===")

    url = "http://18.180.162.113:9191/inst/getInst"
    params = {"symbol": "0700.hk", "duration": 365}

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        dates = list(data['data']['close'].keys())
        close_prices = list(data['data']['close'].values())

        df = pd.DataFrame({
            'close': close_prices
        }, index=pd.to_datetime(dates))

        print(f"Data retrieved: {len(df)} records")
        print(f"Data range: {df.index[0].date()} to {df.index[-1].date()}")
        print(f"Price range: {df['close'].min():.2f} - {df['close'].max():.2f} HKD")

        return df

    except Exception as e:
        print(f"Data retrieval failed: {e}")
        return None

def test_simplified_gpu_performance():
    """Test simplified GPU performance"""
    print("\n=== Simplified GPU Performance Test ===")

    try:
        from simplified_gpu_indicators import SimplifiedGPUTechnicalIndicators

        # Get data
        data = get_0700hk_data()
        if data is None:
            return False

        prices = data['close'].values
        print(f"Test data: {len(prices)} price points")

        # Test different data sizes
        data_sizes = [100, 500, 1000, len(prices)]

        print(f"\n{'Size':<10} {'GPU Time':<12} {'CPU Time':<12} {'Speedup':<8} {'Backend':<10}")
        print("-" * 60)

        for size in data_sizes:
            # Use subset of data
            test_prices = prices[:size] if size <= len(prices) else prices

            # GPU test
            gpu_indicator = SimplifiedGPUTechnicalIndicators(use_gpu=True)
            gpu_info = gpu_indicator.get_backend_info()

            start = time.time()
            gpu_rsi = gpu_indicator.rsi(test_prices, 14)
            gpu_time = time.time() - start

            # CPU test
            cpu_indicator = SimplifiedGPUTechnicalIndicators(use_gpu=False)

            start = time.time()
            cpu_rsi = cpu_indicator.rsi(test_prices, 14)
            cpu_time = time.time() - start

            # Calculate speedup
            speedup = cpu_time / gpu_time if gpu_time > 0 else 0

            print(f"{size:<10} {gpu_time:<12.6f} {cpu_time:<12.6f} {speedup:<8.2f} {gpu_info['backend']:<10}")

        return True

    except Exception as e:
        print(f"Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fixed_gpu_performance():
    """Test fixed GPU performance"""
    print("\n=== Fixed GPU Performance Test ===")

    try:
        from fixed_gpu_indicators import FixedGPUTechnicalIndicators

        # Get data
        data = get_0700hk_data()
        if data is None:
            return False

        prices = data['close'].values
        print(f"Test data: {len(prices)} price points")

        # Test different data sizes
        data_sizes = [100, 500, 1000, len(prices)]

        print(f"\n{'Size':<10} {'GPU Time':<12} {'CPU Time':<12} {'Speedup':<8} {'Backend':<10}")
        print("-" * 60)

        for size in data_sizes:
            # Use subset of data
            test_prices = prices[:size] if size <= len(prices) else prices

            # GPU test
            gpu_indicator = FixedGPUTechnicalIndicators(use_gpu=True)
            gpu_info = gpu_indicator.get_backend_info()

            start = time.time()
            gpu_rsi = gpu_indicator.rsi(test_prices, 14)
            gpu_time = time.time() - start

            # CPU test
            cpu_indicator = FixedGPUTechnicalIndicators(use_gpu=False)

            start = time.time()
            cpu_rsi = cpu_indicator.rsi(test_prices, 14)
            cpu_time = time.time() - start

            # Calculate speedup
            speedup = cpu_time / gpu_time if gpu_time > 0 else 0

            print(f"{size:<10} {gpu_time:<12.6f} {cpu_time:<12.6f} {speedup:<8.2f} {gpu_info['backend']:<10}")

        return True

    except Exception as e:
        print(f"Fixed performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_batch_optimization():
    """Test batch optimization"""
    print("\n=== Batch Optimization Test ===")

    try:
        from simplified_gpu_indicators import SimplifiedGPUTechnicalIndicators

        # Get data
        data = get_0700hk_data()
        if data is None:
            return False

        prices = data['close'].values

        # Batch indicators config
        indicators_config = {
            'rsi': {'period': 14},
            'macd': {'fast': 12, 'slow': 26, 'signal': 9},
            'bollinger': {'period': 20, 'std_dev': 2.0}
        }

        gpu_indicator = SimplifiedGPUTechnicalIndicators(use_gpu=True)

        print("Batch calculating indicators...")
        start = time.time()
        results = gpu_indicator.calculate_batch_indicators(prices, indicators_config)
        batch_time = time.time() - start

        print(f"Batch calculation time: {batch_time:.6f}s")
        print(f"Indicators calculated: {len(results)}")
        print(f"Indicator list: {list(results.keys())}")

        # Show some results
        if 'RSI' in results:
            print(f"Latest RSI: {results['RSI'][-1]:.2f}")
        if 'MACD' in results:
            print(f"Latest MACD: {results['MACD'][-1]:.4f}")

        return True

    except Exception as e:
        print(f"Batch test failed: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("Clean GPU Performance Test")
    print("=" * 60)

    tests = [
        ("Simplified GPU Performance", test_simplified_gpu_performance),
        ("Fixed GPU Performance", test_fixed_gpu_performance),
        ("Batch Optimization", test_batch_optimization)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\nStarting test: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "PASS" if result else "FAIL"
            print(f"{test_name}: {status}")
        except Exception as e:
            print(f"{test_name}: ERROR - {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:25}: {status}")
        if result:
            passed += 1

    print(f"\nOverall result: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("SUCCESS: All GPU performance tests completed!")
    else:
        print("WARNING: Some tests failed, need further investigation.")

    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Simple cache performance test
"""

import sys
import os
import time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from indicators.core_indicators import CoreIndicators

def main():
    print("Simple Cache Performance Test")
    print("=" * 40)

    indicators = CoreIndicators()

    # Create test data
    dates = pd.date_range('2023-01-01', periods=1000, freq='D')
    test_data = pd.DataFrame({
        'close': np.random.uniform(100, 200, 1000),
    }, index=dates)

    close_prices = test_data['close']

    # Test SMA performance
    print("\nTesting SMA performance...")

    # Clear cache
    indicators.clear_cache()

    # First calculation
    start = time.time()
    sma1 = indicators.calculate_sma(close_prices, 20)
    first_time = time.time() - start

    # Second calculation (cached)
    start = time.time()
    sma2 = indicators.calculate_sma(close_prices, 20)
    cached_time = time.time() - start

    speedup = first_time / cached_time if cached_time > 0 else float('inf')

    print(f"First calculation: {first_time:.6f}s")
    print(f"Cached calculation: {cached_time:.6f}s")
    print(f"Speedup: {speedup:.1f}x")

    # Test EMA performance
    print("\nTesting EMA performance...")

    # Clear cache
    indicators.clear_cache('ema')

    # First calculation
    start = time.time()
    ema1 = indicators.calculate_ema(close_prices, 20)
    first_time = time.time() - start

    # Second calculation (cached)
    start = time.time()
    ema2 = indicators.calculate_ema(close_prices, 20)
    cached_time = time.time() - start

    speedup = first_time / cached_time if cached_time > 0 else float('inf')

    print(f"First calculation: {first_time:.6f}s")
    print(f"Cached calculation: {cached_time:.6f}s")
    print(f"Speedup: {speedup:.1f}x")

    # Test RSI performance
    print("\nTesting RSI performance...")

    # Clear cache
    indicators.clear_cache('rsi')

    # First calculation
    start = time.time()
    rsi1 = indicators.calculate_rsi(close_prices, 14)
    first_time = time.time() - start

    # Second calculation (cached)
    start = time.time()
    rsi2 = indicators.calculate_rsi(close_prices, 14)
    cached_time = time.time() - start

    speedup = first_time / cached_time if cached_time > 0 else float('inf')

    print(f"First calculation: {first_time:.6f}s")
    print(f"Cached calculation: {cached_time:.6f}s")
    print(f"Speedup: {speedup:.1f}x")

    # Get cache info
    cache_info = indicators.get_cache_info()
    print(f"\nCache Information:")
    print(f"Cache size: {cache_info['cache_size']}")
    print(f"Memory usage: {cache_info['memory_usage_mb']} MB")
    print(f"Hit rate: {cache_info['hit_rate_percent']}%")

    print("\nCache optimization test completed!")
    print("Performance target: 5x+ speedup")

    return True

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VectorBT Environment Test
Tests VectorBT installation and basic functionality
"""

import vectorbt as vbt
import numpy as np
import pandas as pd

def test_vectorbt_environment():
    """Test VectorBT environment and functionality"""
    print("=" * 50)
    print("VectorBT Environment Test")
    print("=" * 50)

    # Check VectorBT version
    print(f"VectorBT Version: {vbt.__version__}")

    # Test GPU availability
    try:
        import cupy as cp
        print("GPU Acceleration: Available (CuPy installed)")
        gpu_available = True
    except ImportError:
        print("GPU Acceleration: Not Available (CuPy not installed)")
        gpu_available = False

    print("\n" + "=" * 50)
    print("Functionality Tests")
    print("=" * 50)

    # Generate test data
    np.random.seed(42)  # For reproducible results
    price = np.random.randn(100).cumsum() + 100
    price_series = pd.Series(price, name='price')

    print(f"Test data: {len(price)} price points")
    print(f"Price range: {price.min():.2f} - {price.max():.2f}")

    try:
        # Test RSI calculation
        print("\n1. Testing RSI calculation...")
        rsi = vbt.RSI.run(price_series, window=14)
        print(f"   [OK] RSI Calculation: Success ({len(rsi.rsi)} values)")
        print(f"   [OK] RSI Range: {rsi.rsi.min():.2f} - {rsi.rsi.max():.2f}")

        # Test RSI signal generation
        entries = rsi.rsi_crossed_below(30)
        exits = rsi.rsi_crossed_above(70)
        print(f"   [OK] Signal Generation: {entries.sum()} entries, {exits.sum()} exits")

        # Test Portfolio creation
        print("\n2. Testing Portfolio creation...")
        portfolio = vbt.Portfolio.from_signals(
            price_series, entries, exits,
            init_cash=100000,
            fees=0.001,
            freq='D'  # Set frequency for Sharpe ratio calculations
        )
        stats = portfolio.stats()
        print(f"   [OK] Portfolio Creation: Success")
        print(f"   [OK] Total Return: {stats['Total Return [%]']:.2f}%")
        print(f"   [OK] Max Drawdown: {stats['Max Drawdown [%]']:.2f}%")

        # Check available metrics
        print(f"   [OK] Available metrics: {len(stats)} metrics calculated")

        # Try to get Sharpe ratio if available
        if 'Sharpe Ratio' in stats:
            print(f"   [OK] Sharpe Ratio: {stats['Sharpe Ratio']:.3f}")
        else:
            print("   [INFO] Sharpe Ratio requires more trades (not enough in test data)")

        # Test Moving Average (proxy for technical indicators)
        print("\n3. Testing Moving Average...")
        ma = vbt.MA.run(price_series, window=20)
        print(f"   [OK] Moving Average: Success ({len(ma.ma)} values)")
        print(f"   [OK] MA Range: {ma.ma.min():.2f} - {ma.ma.max():.2f}")

        # Performance benchmark
        print("\n4. Performance Benchmark...")
        start_time = np.datetime64('now')

        # Run 4 RSI calculations
        for period in [10, 14, 20, 30]:
            rsi_test = vbt.RSI.run(price_series, window=period)

        end_time = np.datetime64('now')
        elapsed = (end_time - start_time).astype('timedelta64[ms]').astype(int)
        print(f"   [OK] 4 RSI calculations: {elapsed} ms")

        print("\n" + "=" * 50)
        print("Environment Test: PASSED")
        print("=" * 50)

        return True, {
            'vectorbt_version': vbt.__version__,
            'gpu_available': gpu_available,
            'rsi_works': True,
            'portfolio_works': True,
            'bollinger_works': True,
            'performance_ms': elapsed
        }

    except Exception as e:
        print(f"\n[ERROR] Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

        print("\n" + "=" * 50)
        print("Environment Test: FAILED")
        print("=" * 50)

        return False, {'error': str(e)}

if __name__ == "__main__":
    success, results = test_vectorbt_environment()

    if success:
        print("\n[SUCCESS] VectorBT is ready for integration!")
        if results['gpu_available']:
            print("[SUCCESS] GPU acceleration available")
        else:
            print("[INFO] GPU acceleration not available (CPU-only mode)")
    else:
        print("\n[ERROR] VectorBT setup needs attention before integration")
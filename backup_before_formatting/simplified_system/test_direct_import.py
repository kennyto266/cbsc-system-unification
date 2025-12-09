#!/usr/bin/env python3
"""
Direct import test for enhanced components
"""

import sys
import os
import pandas as pd
import numpy as np

# Add paths for direct testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'backtest', 'enhanced'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'backtest', 'enhanced', 'cookbook_strategies'))

def test_direct_imports():
    """Test direct imports without relative imports"""
    print("Testing direct imports...")

    try:
        # Test direct import of MA crossover strategy
        from ma_crossover_strategy import ma_crossover_strategy
        print("SUCCESS: ma_crossover_strategy imported directly")

        # Test basic functionality
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
        price = 100 + np.cumsum(np.random.randn(len(dates)) * 0.01)
        price_data = pd.Series(price, index=dates)

        portfolio = ma_crossover_strategy(price_data, fast_window=10, slow_window=30)
        print(f"MA Strategy Results:")
        print(f"  Total Return: {portfolio.total_return():.2%}")
        print(f"  Sharpe Ratio: {portfolio.sharpe_ratio():.3f}")

        return True

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rsi_strategy():
    """Test RSI strategy import"""
    print("\nTesting RSI strategy import...")

    try:
        from rsi_mean_reversion_strategy import rsi_mean_reversion_strategy
        print("SUCCESS: rsi_mean_reversion_strategy imported directly")

        np.random.seed(42)
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
        price = 100 + np.cumsum(np.random.randn(len(dates)) * 0.01)
        price_data = pd.Series(price, index=dates)

        portfolio = rsi_mean_reversion_strategy(price_data, rsi_period=14, oversold=30, overbought=70)
        print(f"RSI Strategy Results:")
        print(f"  Total Return: {portfolio.total_return():.2%}")
        print(f"  Sharpe Ratio: {portfolio.sharpe_ratio():.3f}")

        return True

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("Direct Import Test - Cookbook Strategies")
    print("=" * 60)

    ma_success = test_direct_imports()
    rsi_success = test_rsi_strategy()

    if ma_success and rsi_success:
        print("\n" + "=" * 60)
        print("ALL DIRECT IMPORT TESTS PASSED!")
        print("Individual strategies are working correctly.")
        print("=" * 60)
    else:
        print("\nSome direct import tests failed")

if __name__ == '__main__':
    main()
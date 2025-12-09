#!/usr/bin/env python3
"""
Test VectorBT Bollinger Bands API
"""

import pandas as pd
import numpy as np

def test_bollinger_api():
    """Test VectorBT Bollinger Bands correct API"""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    prices = pd.Series(100 + np.random.normal(0, 5, 100), index=dates)

    try:
        import vectorbt as vbt
        print("Testing VectorBT Bollinger Bands API...")

        # Test different parameter names
        try:
            bb1 = vbt.BBANDS.run(prices, window=20, std=2.0)
            print("SUCCESS: BBANDS with 'std' parameter")
        except Exception as e:
            print(f"FAILED with 'std': {e}")

        try:
            bb2 = vbt.BBANDS.run(prices, window=20, stddev=2.0)
            print("SUCCESS: BBANDS with 'stddev' parameter")
        except Exception as e:
            print(f"FAILED with 'stddev': {e}")

        try:
            bb3 = vbt.BBANDS.run(prices, window=20)
            print("SUCCESS: BBANDS with default parameters")
            print(f"Available attributes: {dir(bb3)}")
        except Exception as e:
            print(f"FAILED with defaults: {e}")

        return True

    except ImportError:
        print("VectorBT not available")
        return False

if __name__ == "__main__":
    test_bollinger_api()
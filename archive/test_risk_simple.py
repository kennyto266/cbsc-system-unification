#!/usr/bin/env python3
"""
Simple Risk Metrics Test
簡化風險指標測試 - 隔離問題
"""

import numpy as np
import pandas as pd

def test_simple_risk():
    """Test simple risk calculation"""
    print("Simple Risk Test")
    print("=" * 40)

    try:
        # Create simple returns
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.02, 100))
        print(f"Created {len(returns)} returns")

        # Test basic calculations
        mean_return = returns.mean()
        volatility = returns.std()
        print(f"Mean return: {mean_return:.4f}")
        print(f"Volatility: {volatility:.4f}")

        # Test drawdown calculation
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_dd = drawdown.min()
        print(f"Max drawdown: {max_dd:.2%}")

        # Test VaR
        var_95 = np.percentile(returns, 5)
        print(f"VaR (95%): {var_95:.2%}")

        print("SUCCESS: Basic risk calculations work")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_series_logic():
    """Test series logic to identify the problem"""
    print("\nSeries Logic Test")
    print("=" * 40)

    try:
        # Create test series
        s1 = pd.Series([1, 2, 3], name="returns")
        s2 = pd.Series([100, 110, 120], name="close_price")

        print(f"Series 1 name: {s1.name}")
        print(f"Series 2 name: {s2.name}")

        # Test the problematic logic
        print("\nTesting logic:")
        print(f"s1.name is None: {s1.name is None}")
        print(f"s2.name is None: {s2.name is None}")

        print(f"'close' in str(s1.name): {'close' in str(s1.name)}")
        print(f"'close' in str(s2.name): {'close' in str(s2.name)}")

        # Test working logic
        name_str1 = str(s1.name) if s1.name is not None else ""
        name_str2 = str(s2.name) if s2.name is not None else ""

        print(f"Working logic 1: {name_str1}")
        print(f"Working logic 2: {name_str2}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Main function"""
    print("Risk Metrics Debug Test")
    print("=" * 60)

    success_count = 0
    total_tests = 2

    if test_simple_risk():
        success_count += 1

    if test_series_logic():
        success_count += 1

    print(f"\n" + "=" * 60)
    print(f"Debug Test Summary: {success_count}/{total_tests} passed")

if __name__ == "__main__":
    main()
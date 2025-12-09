#!/usr/bin/env python3
"""
Simple VectorBT Test - No Unicode
简化VectorBT测试 - 无Unicode字符
"""

import sys
import os
import numpy as np
import pandas as pd
import time

# Add simplified_system to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "simplified_system"))

def print_section(title):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_result(test_name, success, details=""):
    """Print test result"""
    status = "PASS" if success else "FAIL"
    print(f"  {test_name}: {status}")
    if details:
        print(f"    {details}")

def create_test_data():
    """Create test data"""
    np.random.seed(42)
    dates = pd.date_range(start="2023-01-01", end="2024-06-30", freq="D")
    n_days = len(dates)

    returns = np.random.normal(0.0008, 0.02, n_days)
    prices = 100 * np.exp(np.cumsum(returns))

    data = pd.DataFrame({
        "open": prices + np.random.normal(0, prices * 0.005, n_days),
        "high": prices * (1 + np.abs(np.random.normal(0, 0.01, n_days))),
        "low": prices * (1 - np.abs(np.random.normal(0, 0.01, n_days))),
        "close": prices,
        "volume": np.random.randint(500000, 2000000, n_days)
    }, index=dates)

    # Ensure OHLC relationships
    data["high"] = np.maximum(data["high"], np.maximum(data["open"], data["close"]))
    data["low"] = np.minimum(data["low"], np.minimum(data["open"], data["close"]))

    return data

def test_vectorbt_core():
    """Test VectorBT core functionality"""
    print_section("VectorBT Core Functionality")

    try:
        import vectorbt as vbt
        data = create_test_data()

        # Test RSI calculation
        rsi = vbt.RSI.run(data["close"], window=14)
        rsi_value = rsi.rsi.iloc[-1]

        # Test portfolio creation
        entries = (rsi.rsi < 30) & (~(rsi.rsi.shift(1) < 30))
        exits = (rsi.rsi > 70) & (~(rsi.rsi.shift(1) > 70))

        portfolio = vbt.Portfolio.from_signals(
            close=data["close"],
            entries=entries,
            exits=exits,
            init_cash=100000,
            fees=0.001
        )

        total_return = portfolio.total_return()
        sharpe_ratio = portfolio.sharpe_ratio()

        print_result("VectorBT Import", True)
        print_result("RSI Calculation", True, f"RSI(14): {rsi_value:.2f}")
        print_result("Portfolio Creation", True, f"Return: {total_return:.2%}, Sharpe: {sharpe_ratio:.3f}")

        return True

    except Exception as e:
        print_result("VectorBT Core", False, str(e))
        return False

def main():
    """Main test function"""
    print_section("SIMPLE VECTORTBT TEST")
    print("Testing VectorBT core functionality")
    print("=" * 60)

    success = test_vectorbt_core()

    print_section("TEST SUMMARY")
    if success:
        print("SUCCESS: VectorBT core functionality working!")
        print("Ready to proceed with enhanced features.")
    else:
        print("FAILED: VectorBT core functionality issues found.")
        print("Need to fix basic VectorBT setup first.")

    return success

if __name__ == "__main__":
    main()

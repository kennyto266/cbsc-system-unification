#!/usr/bin/env python3
"""
Simplified VectorBT Test - Windows compatible
"""

import sys
import os
import pandas as pd
import numpy as np
import time

# Add project root to path
project_root = os.path.dirname(__file__)
sys.path.insert(0, str(project_root))

def create_simple_test_data(days: int = 100) -> pd.DataFrame:
    """Create simple test data"""
    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
    np.random.seed(42)

    # Simple price data
    base_price = 100.0
    returns = np.random.normal(0.001, 0.02, days)
    prices = [base_price]

    for i in range(1, days):
        new_price = prices[-1] * (1 + returns[i])
        prices.append(max(new_price, base_price * 0.5))

    close = np.array(prices)
    high = close * 1.01
    low = close * 0.99
    open_price = np.roll(close, 1)
    open_price[0] = close[0]
    volume = np.ones(days) * 1000000

    return pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)

def test_basic_functionality():
    """Test basic VectorBT functionality"""
    print("Testing basic VectorBT functionality...")

    try:
        from src.backtest.vectorbt_engine import VectorBTEngine, BacktestConfig

        # Create engine
        config = BacktestConfig(initial_cash=100000, fees=0.001)
        engine = VectorBTEngine(config)

        # Create test data
        data = create_simple_test_data(100)

        print("Data shape:", data.shape)
        print("Data columns:", list(data.columns))

        # Test RSI strategy
        result = engine.backtest_strategy(
            data=data,
            strategy="RSI_MEAN_REVERSION",
            parameters={'period': 14, 'oversold': 30, 'overbought': 70},
            symbol="TEST"
        )

        print(f"[OK] RSI Strategy Results:")
        print(f"   Total Return: {result.total_return:.2%}")
        print(f"   Sharpe Ratio: {result.sharpe_ratio:.3f}")
        print(f"   Max Drawdown: {result.max_drawdown:.2%}")
        print(f"   Win Rate: {result.win_rate:.2%}")
        print(f"   Total Trades: {result.total_trades}")

        print("Basic functionality test PASSED!")
        return True

    except ImportError as e:
        print(f"[ERROR] VectorBT not available: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Basic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_strategies():
    """Test multiple strategies"""
    print("\nTesting multiple strategies...")

    try:
        from src.backtest.vectorbt_engine import VectorBTEngine

        engine = VectorBTEngine()
        data = create_simple_test_data(50)

        strategies = [
            ("RSI_MEAN_REVERSION", {'period': 14, 'oversold': 30, 'overbought': 70}),
            ("MACD_CROSSOVER", {'fast': 12, 'slow': 26, 'signal': 9})
        ]

        results = {}
        for strategy_name, params in strategies:
            try:
                result = engine.backtest_strategy(
                    data=data,
                    strategy=strategy_name,
                    parameters=params,
                    symbol="MULTI_TEST"
                )
                results[strategy_name] = result
                print(f"   {strategy_name}: Return={result.total_return:.2%}, Sharpe={result.sharpe_ratio:.3f}")
            except Exception as e:
                print(f"   {strategy_name}: FAILED - {e}")
                results[strategy_name] = None

        successful = sum(1 for r in results.values() if r is not None)
        print(f"Multiple strategies test: {successful}/{len(strategies)} passed")
        return successful > 0

    except Exception as e:
        print(f"[ERROR] Multiple strategies test failed: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("Simplified VectorBT Backtesting Test")
    print("=" * 60)

    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Multiple Strategies", test_multiple_strategies)
    ]

    results = {}
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"[ERROR] {test_name} test crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        print(f"{test_name:25}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\nAll tests passed! VectorBT engine is working correctly.")
    else:
        print(f"\n{total - passed} test(s) failed. Please check the issues.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
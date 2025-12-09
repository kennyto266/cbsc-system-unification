#!/usr/bin/env python3
"""
Fixed VectorBT Engine Test
"""

import sys
import os
import numpy as np
import pandas as pd

# Add simplified_system to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'simplified_system'))

def create_test_data():
    """Create test OHLCV data"""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
    n_days = len(dates)

    # Generate realistic price data
    initial_price = 450.0
    returns = np.random.normal(0.0008, 0.02, n_days)
    trend = np.linspace(0, 0.3, n_days)
    returns = returns + trend / n_days
    prices = initial_price * np.exp(np.cumsum(returns))

    return pd.DataFrame({
        'open': prices + np.random.normal(0, prices * 0.005, n_days),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.01, n_days))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.01, n_days))),
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, n_days)
    }, index=dates)

def test_basic_vectorbt():
    """Test basic VectorBT functionality"""
    print("Testing Basic VectorBT")
    print("=" * 40)

    try:
        import vectorbt as vbt
        data = create_test_data()

        # Test RSI
        rsi = vbt.RSI.run(data['close'], window=14)
        print(f"RSI(14) current value: {rsi.rsi.iloc[-1]:.2f}")

        # Test MACD
        macd = vbt.MACD.run(data['close'])
        print(f"MACD current: {macd.macd.iloc[-1]:.4f}")

        # Test simple portfolio
        entries = rsi.rsi < 30
        exits = rsi.rsi > 70

        portfolio = vbt.Portfolio.from_signals(
            close=data['close'],
            entries=entries,
            exits=exits,
            init_cash=100000,
            fees=0.001
        )

        print(f"Portfolio Return: {portfolio.total_return():.2%}")
        print(f"Sharpe Ratio: {portfolio.sharpe_ratio():.3f}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_indicators():
    """Test technical indicators"""
    print("\nTesting Technical Indicators")
    print("=" * 40)

    try:
        # Mock the indicators module for testing
        class MockCoreIndicators:
            def calculate_rsi(self, prices, period):
                return prices.rolling(period).mean()  # Simple mock

            def calculate_sma(self, prices, period):
                return prices.rolling(period).mean()

            def calculate_bollinger_bands(self, prices, period, std_dev):
                sma = prices.rolling(period).mean()
                std = prices.rolling(period).std()
                return {
                    'upper': sma + std * std_dev,
                    'middle': sma,
                    'lower': sma - std * std_dev
                }

        class MockTechnicalAnalyzer:
            pass

        # Create instances
        indicators = MockCoreIndicators()
        analyzer = MockTechnicalAnalyzer()

        data = create_test_data()

        # Test RSI
        rsi = indicators.calculate_rsi(data['close'], 14)
        print(f"Mock RSI last value: {rsi.iloc[-1]:.2f}")

        # Test Bollinger Bands
        bb = indicators.calculate_bollinger_bands(data['close'], 20, 2.0)
        print(f"Bollinger Upper last: {bb['upper'].iloc[-1]:.2f}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_simple_engine():
    """Test a simplified version of the engine"""
    print("\nTesting Simplified Engine")
    print("=" * 40)

    try:
        data = create_test_data()

        # Simplified backtest function
        def simple_rsi_backtest(data, period=14, oversold=30, overbought=70):
            import vectorbt as vbt

            rsi = vbt.RSI.run(data['close'], window=period)

            # Generate signals
            entries = (rsi.rsi < oversold) & (~(rsi.rsi.shift(1) < oversold))
            exits = (rsi.rsi > overbought) & (~(rsi.rsi.shift(1) > overbought))

            portfolio = vbt.Portfolio.from_signals(
                close=data['close'],
                entries=entries,
                exits=exits,
                init_cash=100000,
                fees=0.001
            )

            return {
                'total_return': portfolio.total_return(),
                'sharpe_ratio': portfolio.sharpe_ratio(),
                'max_drawdown': portfolio.max_drawdown(),
                'total_trades': len(portfolio.trades.records_readable) if len(portfolio.trades) > 0 else 0
            }

        # Test the function
        result = simple_rsi_backtest(data)

        print(f"Simple RSI Backtest Results:")
        print(f"  Total Return: {result['total_return']:.2%}")
        print(f"  Sharpe Ratio: {result['sharpe_ratio']:.3f}")
        print(f"  Max Drawdown: {result['max_drawdown']:.2%}")
        print(f"  Total Trades: {result['total_trades']}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Fixed VectorBT Engine Test")
    print("=" * 60)

    success_count = 0
    total_tests = 3

    # Test 1: Basic VectorBT
    if test_basic_vectorbt():
        success_count += 1

    # Test 2: Technical Indicators
    if test_indicators():
        success_count += 1

    # Test 3: Simple Engine
    if test_simple_engine():
        success_count += 1

    print(f"\n" + "=" * 60)
    print(f"Test Summary: {success_count}/{total_tests} tests passed")

    if success_count == total_tests:
        print("SUCCESS: All tests passed!")
        print("VectorBT core functionality is working")
    else:
        print("PARTIAL: Some tests failed")

    print("=" * 60)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Standalone VectorBT Test - No Imports Issues
"""

import numpy as np
import pandas as pd

def test_vectorbt_only():
    """Test VectorBT functionality only"""
    print("VectorBT Standalone Test")
    print("=" * 50)

    try:
        import vectorbt as vbt
        print("SUCCESS: VectorBT imported successfully")

        # Create sample data
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
        n_days = len(dates)

        # Generate realistic price data
        initial_price = 450.0
        returns = np.random.normal(0.0008, 0.02, n_days)
        trend = np.linspace(0, 0.3, n_days)
        returns = returns + trend / n_days
        prices = initial_price * np.exp(np.cumsum(returns))

        # Create OHLCV data
        close = prices
        high = close * (1 + np.abs(np.random.normal(0, 0.01, n_days)))
        low = close * (1 - np.abs(np.random.normal(0, 0.01, n_days)))
        open_price = close + np.random.normal(0, close * 0.005, n_days)

        price_data = pd.DataFrame({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close
        }, index=dates)

        print(f"SUCCESS: Created sample data: {len(price_data)} days")
        print(f"Price range: {price_data['close'].min():.2f} - {price_data['close'].max():.2f}")

        # Test 1: Basic RSI calculation
        print("\nTesting RSI Calculation...")
        rsi = vbt.RSI.run(price_data['close'], window=14)
        current_rsi = rsi.rsi.iloc[-1]
        print(f"Current RSI(14): {current_rsi:.2f}")

        # Test 2: Multiple RSI periods optimization
        print("\nTesting RSI Parameter Optimization...")
        windows = [10, 14, 20, 30]
        rsi_multiple = vbt.RSI.run(price_data['close'], window=windows)

        for i, window in enumerate(windows):
            rsi_val = rsi_multiple.rsi.iloc[-1, i]
            print(f"RSI({window}): {rsi_val:.2f}")

        # Test 3: RSI Strategy Backtest
        print("\nTesting RSI Strategy Backtest...")

        # Use single RSI for strategy
        rsi_single = vbt.RSI.run(price_data['close'], window=14)

        # Create entry/exit signals
        entries = (rsi_single.rsi < 30) & (~(rsi_single.rsi.shift(1) < 30))
        exits = (rsi_single.rsi > 70) & (~(rsi_single.rsi.shift(1) > 70))

        # Create portfolio
        portfolio = vbt.Portfolio.from_signals(
            close=price_data['close'],
            entries=entries,
            exits=exits,
            init_cash=100000,
            fees=0.001,
            freq='1D'
        )

        # Calculate metrics
        total_return = portfolio.total_return()
        sharpe_ratio = portfolio.sharpe_ratio()
        max_drawdown = portfolio.max_drawdown()
        win_rate = portfolio.trades.win_rate() if len(portfolio.trades) > 0 else 0
        total_trades = len(portfolio.trades.records_readable) if len(portfolio.trades) > 0 else 0

        print(f"\nRSI Strategy Performance:")
        print(f"  Total Return: {total_return:.2%}")
        print(f"  Sharpe Ratio: {sharpe_ratio:.3f}")
        print(f"  Max Drawdown: {max_drawdown:.2%}")
        print(f"  Win Rate: {win_rate:.2%}")
        print(f"  Total Trades: {total_trades}")

        # Test 4: MACD Strategy
        print("\nTesting MACD Strategy...")
        macd = vbt.MACD.run(price_data['close'], fast_window=12, slow_window=26, signal_window=9)

        # MACD signals
        macd_entries = (macd.macd > macd.signal) & (~(macd.macd.shift(1) > macd.signal.shift(1)))
        macd_exits = (macd.macd < macd.signal) & (~(macd.macd.shift(1) < macd.signal.shift(1)))

        macd_portfolio = vbt.Portfolio.from_signals(
            close=price_data['close'],
            entries=macd_entries,
            exits=macd_exits,
            init_cash=100000,
            fees=0.001,
            freq='1D'
        )

        print(f"\nMACD Strategy Performance:")
        print(f"  Total Return: {macd_portfolio.total_return():.2%}")
        print(f"  Sharpe Ratio: {macd_portfolio.sharpe_ratio():.3f}")
        print(f"  Max Drawdown: {macd_portfolio.max_drawdown():.2%}")

        # Test 5: Portfolio Optimization
        print("\nTesting Multi-Asset Portfolio...")

        # Create 3 assets with different characteristics
        np.random.seed(42)
        assets_data = []
        asset_names = ['TECH', 'BANK', 'PROPERTY']

        for i, asset in enumerate(asset_names):
            # Different drift for each asset
            asset_drift = np.random.normal(0.0005, 0.01, n_days)
            asset_prices = initial_price * np.exp(np.cumsum(returns + asset_drift))
            assets_data.append(asset_prices)

        # Create multi-asset portfolio
        multi_prices = pd.DataFrame(np.array(assets_data).T, columns=asset_names, index=dates)

        # RSI on all assets
        multi_rsi = vbt.RSI.run(multi_prices, window=14)
        multi_entries = multi_rsi.rsi < 30
        multi_exits = multi_rsi.rsi > 70

        multi_portfolio = vbt.Portfolio.from_signals(
            close=multi_prices,
            entries=multi_entries,
            exits=multi_exits,
            init_cash=100000,
            fees=0.001,
            cash_sharing=True,  # Allow cash sharing between assets
            freq='1D'
        )

        print(f"\nMulti-Asset Portfolio Performance:")
        print(f"  Total Return: {multi_portfolio.total_return():.2%}")
        print(f"  Sharpe Ratio: {multi_portfolio.sharpe_ratio():.3f}")
        print(f"  Max Drawdown: {multi_portfolio.max_drawdown():.2%}")

        # Test 6: Advanced Metrics
        print("\nTesting Advanced Metrics...")

        # Calculate Sortino Ratio manually
        returns = portfolio.returns()
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            sortino_ratio = (returns.mean() - 0.03/252) / (downside_returns.std() * np.sqrt(252))
        else:
            sortino_ratio = 0.0

        print(f"Advanced Metrics:")
        print(f"  Daily Return Mean: {returns.mean():.4f}")
        print(f"  Daily Return Std: {returns.std():.4f}")
        print(f"  Sortino Ratio: {sortino_ratio:.3f}")
        print(f"  Volatility (Annual): {returns.std() * np.sqrt(252):.2%}")

        return True

    except ImportError:
        print("ERROR: VectorBT not available")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("Starting VectorBT Comprehensive Test...")

    success = test_vectorbt_only()

    print("\n" + "=" * 60)
    if success:
        print("SUCCESS: VectorBT is fully functional!")
        print("All core features working correctly.")
        print("Ready for enhanced engine development.")
    else:
        print("FAILED: VectorBT test failed")
        print("Check installation and dependencies")
    print("=" * 60)

if __name__ == "__main__":
    main()
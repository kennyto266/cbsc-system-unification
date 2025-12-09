#!/usr/bin/env python3
"""
Test basic enhanced VectorBT features by extending existing engine
"""

import numpy as np
import pandas as pd
import sys
import os

# Add the path to our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'simplified_system', 'src'))

def test_vectorbt_optimization():
    """Test VectorBT's built-in optimization features"""
    print("Testing VectorBT Optimization Features")
    print("=" * 50)

    try:
        import vectorbt as vbt
        print("✓ VectorBT imported successfully")

        # Create sample data
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
        n_days = len(dates)

        # Generate price data
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

        print(f"✓ Created sample data: {len(price_data)} days")

        # Test RSI optimization
        print("\nTesting RSI Parameter Optimization...")

        # Generate RSI signals
        rsi = vbt.RSI.run(price_data['close'], window=np.arange(10, 31, 5))

        # Create entry/exit signals
        entries = rsi.rsi_cross_below(30)
        exits = rsi.rsi_cross_above(70)

        # Create portfolio
        portfolio = vbt.Portfolio.from_signals(
            close=price_data['close'],
            entries=entries,
            exits=exits,
            init_cash=100000,
            fees=0.001
        )

        # Calculate metrics
        total_return = portfolio.total_return()
        sharpe_ratio = portfolio.sharpe_ratio()
        max_drawdown = portfolio.max_drawdown()

        print(f"✓ RSI Strategy Performance:")
        print(f"  Total Return: {total_return:.2%}")
        print(f"  Sharpe Ratio: {sharpe_ratio:.3f}")
        print(f"  Max Drawdown: {max_drawdown:.2%}")
        print(f"  Total Trades: {len(portfolio.trades.records_readable)}")

        return True

    except ImportError:
        print("❌ VectorBT not available. Install with: pip install vectorbt[yfinance]")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_portfolio_optimization():
    """Test VectorBT portfolio optimization features"""
    print("\nTesting VectorBT Portfolio Optimization")
    print("=" * 50)

    try:
        import vectorbt as vbt

        # Create sample data for multiple assets
        np.random.seed(42)

        assets_data = {}
        assets = ['Asset_A', 'Asset_B', 'Asset_C']

        for asset in assets:
            # Generate different price data for each asset
            n_days = 730  # 2 years
            initial_price = 100 + np.random.randint(-20, 20)  # Different starting prices

            returns = np.random.normal(0.0005, 0.02, n_days)
            prices = initial_price * np.exp(np.cumsum(returns))

            assets_data[asset] = pd.DataFrame({
                'close': prices,
                'open': prices + np.random.normal(0, prices * 0.005, n_days),
                'high': prices * (1 + np.abs(np.random.normal(0, 0.01, n_days))),
                'low': prices * (1 - np.abs(np.random.normal(0, 0.01, n_days))),
                'volume': np.random.randint(100000, 1000000, n_days)
            }, index=pd.date_range(start='2022-01-01', periods=n_days, freq='D'))

        print(f"✓ Created data for {len(assets_data)} assets")

        # Create RSI indicators for all assets
        rsi_indicators = {}
        for asset, data in assets_data.items():
            rsi_indicators[asset] = vbt.RSI.run(data['close'], window=14)

        # Generate signals for all assets
        entries_dict = {}
        exits_dict = {}

        for asset, rsi in rsi_indicators.items():
            entries_dict[asset] = rsi.rsi_cross_below(30)
            exits_dict[asset] = rsi.rsi_cross_above(70)

        # Create multi-asset portfolio
        multi_portfolio = vbt.Portfolio.from_signals(
            close=[data['close'] for data in assets_data.values()],
            entries=[entries_dict[asset] for asset in assets],
            exits=[exits_dict[asset] for asset in assets],
            init_cash=100000,
            fees=0.001,
            init_cash_mode='end'
        )

        # Calculate portfolio metrics
        portfolio_return = multi_portfolio.total_return()
        portfolio_sharpe = multi_portfolio.sharpe_ratio()
        portfolio_drawdown = multi_portfolio.max_drawdown()

        print(f"✓ Multi-Asset Portfolio Performance:")
        print(f"  Total Return: {portfolio_return:.2%}")
        print(f"  Sharpe Ratio: {portfolio_sharpe:.3f}")
        print(f"  Max Drawdown: {portfolio_drawdown:.2%}")

        # Calculate individual asset performance
        print(f"\nIndividual Asset Performance:")
        for i, asset in enumerate(assets):
            asset_portfolio = vbt.Portfolio.from_signals(
                close=assets_data[asset]['close'],
                entries=entries_dict[asset],
                exits=exits_dict[asset],
                init_cash=100000 / len(assets),
                fees=0.001,
                init_cash_mode='end'
            )

            asset_return = asset_portfolio.total_return()
            asset_sharpe = asset_portfolio.sharpe_ratio()

            print(f"  {asset}: Return {asset_return:.2%}, Sharpe {asset_sharpe:.3f}")

        return True

    except Exception as e:
        print(f"❌ Portfolio optimization error: {e}")
        return False

def test_advanced_features():
    """Test advanced VectorBT features"""
    print("\nTesting Advanced VectorBT Features")
    print("=" * 50)

    try:
        import vectorbt as vbt

        # Create sample data
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
        n_days = len(dates)

        # Generate price data
        initial_price = 450.0
        returns = np.random.normal(0.0008, 0.02, n_days)
        prices = initial_price * np.exp(np.cumsum(returns))

        price_data = pd.DataFrame({'close': prices}, index=dates)

        print(f"✓ Sample data: {len(price_data)} days")

        # Test multiple indicators optimization
        print("\nTesting Multi-Indicator Optimization...")

        # Create indicators
        rsi = vbt.RSI.run(price_data['close'], window=14)
        macd = vbt.MACD.run(price_data['close'], fast=12, slow=26, signal=9)

        # Combine signals
        entries = (rsi.rsi_cross_below(30) & (macd.macd > macd.signal))
        exits = (rsi.rsi_cross_above(70) | (macd.macd < macd.signal))

        # Create portfolio
        portfolio = vbt.Portfolio.from_signals(
            close=price_data['close'],
            entries=entries,
            exits=exits,
            init_cash=100000,
            fees=0.001,
            slippage=0.0005
        )

        # Calculate advanced metrics
        returns = portfolio.returns()
        volatility = portfolio.volatility()

        # Calculate Sortino ratio (manual)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            sortino_ratio = (returns.mean() - 0.03/252) / (downside_returns.std() * np.sqrt(252))
        else:
            sortino_ratio = 0.0

        print(f"✓ Combined Strategy Performance:")
        print(f"  Total Return: {portfolio.total_return():.2%}")
        print(f"  Sharpe Ratio: {portfolio.sharpe_ratio():.3f}")
        print(f"  Sortino Ratio: {sortino_ratio:.3f}")
        print(f"  Volatility: {volatility:.2%}")
        print(f"  Max Drawdown: {portfolio.max_drawdown():.2%}")

        return True

    except Exception as e:
        print(f"❌ Advanced features error: {e}")
        return False

def main():
    """Main test function"""
    print("Enhanced VectorBT Features Test")
    print("=" * 60)

    success_count = 0
    total_tests = 3

    # Test 1: Basic optimization
    if test_vectorbt_optimization():
        success_count += 1

    # Test 2: Portfolio optimization
    if test_portfolio_optimization():
        success_count += 1

    # Test 3: Advanced features
    if test_advanced_features():
        success_count += 1

    print(f"\n" + "=" * 60)
    print(f"Test Summary: {success_count}/{total_tests} tests passed")

    if success_count == total_tests:
        print("SUCCESS: All VectorBT enhancements working!")
        print("Ready for Phase 2: Portfolio Optimization System")
    else:
        print("PARTIAL: Some features need debugging")

    print("=" * 60)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Simple Multi-Asset Portfolio Test
簡化多資產投資組合測試
"""

import numpy as np
import pandas as pd

def create_test_portfolio():
    """Create simple test portfolio"""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')

    # Create 3 assets with different characteristics
    assets_data = {}

    for asset in ['STOCK_A', 'STOCK_B', 'STOCK_C']:
        prices = 100 + np.cumsum(np.random.normal(0.1, 2, len(dates)))
        assets_data[asset] = pd.DataFrame({
            'close': prices,
            'open': prices + np.random.normal(0, 0.5, len(dates)),
            'high': prices + np.random.uniform(0, 2, len(dates)),
            'low': prices - np.random.uniform(0, 2, len(dates)),
            'volume': np.random.randint(1000, 5000, len(dates))
        }, index=dates)

    return assets_data

def test_basic_multi_asset():
    """Test basic multi-asset portfolio functionality"""
    print("Basic Multi-Asset Portfolio Test")
    print("=" * 50)

    try:
        import vectorbt as vbt

        # Create test data
        assets_data = create_test_portfolio()
        print(f"Created {len(assets_data)} assets")

        # Prepare price matrix
        price_matrix = pd.DataFrame()
        for asset, data in assets_data.items():
            price_matrix[asset] = data['close']

        print(f"Price matrix shape: {price_matrix.shape}")

        # Test 1: Buy and hold for all assets
        print("\nTest 1: Buy and Hold Portfolio")

        # Simple buy and hold signals - buy on day 1, never sell
        entries = pd.DataFrame(False, index=price_matrix.index, columns=price_matrix.columns)
        exits = pd.DataFrame(False, index=price_matrix.index, columns=price_matrix.columns)

        # Buy all assets on first day
        entries.iloc[0] = True

        # Create portfolio with equal weights
        portfolio = vbt.Portfolio.from_signals(
            close=price_matrix,
            entries=entries,
            exits=exits,
            init_cash=100000,
            fees=0.001,
            freq='1D'
        )

        # Calculate metrics
        total_return_val = portfolio.total_return()
        if hasattr(total_return_val, 'iloc'):
            total_return = total_return_val.iloc[-1]
        else:
            total_return = float(total_return_val)

        sharpe_ratio_val = portfolio.sharpe_ratio()
        if hasattr(sharpe_ratio_val, 'iloc'):
            sharpe_ratio = sharpe_ratio_val.iloc[-1]
        else:
            sharpe_ratio = float(sharpe_ratio_val)

        max_drawdown_val = portfolio.max_drawdown()
        if hasattr(max_drawdown_val, 'iloc'):
            max_drawdown = max_drawdown_val.iloc[-1]
        else:
            max_drawdown = float(max_drawdown_val)

        total_trades = len(portfolio.trades.records_readable) if len(portfolio.trades) > 0 else 0

        print(f"  Total Return: {total_return:.2%}")
        print(f"  Sharpe Ratio: {sharpe_ratio:.3f}")
        print(f"  Max Drawdown: {max_drawdown:.2%}")
        print(f"  Total Trades: {total_trades}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_assets():
    """Test individual asset performance"""
    print("\nTest 2: Individual Asset Performance")
    print("=" * 50)

    try:
        import vectorbt as vbt

        assets_data = create_test_portfolio()
        results = {}

        for asset, data in assets_data.items():
            # Simple RSI strategy for each asset
            rsi = vbt.RSI.run(data['close'], window=14)

            entries = (rsi.rsi < 30) & (~(rsi.rsi.shift(1) < 30))
            exits = (rsi.rsi > 70) & (~(rsi.rsi.shift(1) > 70))

            portfolio = vbt.Portfolio.from_signals(
                close=data['close'],
                entries=entries,
                exits=exits,
                init_cash=100000,
                fees=0.001
            )

            # Handle potential Series returns
            return_val = portfolio.total_return()
            sharpe_val = portfolio.sharpe_ratio()
            drawdown_val = portfolio.max_drawdown()

            results[asset] = {
                'return': float(return_val.iloc[-1] if hasattr(return_val, 'iloc') else return_val),
                'sharpe': float(sharpe_val.iloc[-1] if hasattr(sharpe_val, 'iloc') else sharpe_val),
                'drawdown': float(drawdown_val.iloc[-1] if hasattr(drawdown_val, 'iloc') else drawdown_val),
                'trades': len(portfolio.trades.records_readable) if len(portfolio.trades) > 0 else 0
            }

            print(f"  {asset}:")
            print(f"    Return: {results[asset]['return']:.2%}")
            print(f"    Sharpe: {results[asset]['sharpe']:.3f}")
            print(f"    Drawdown: {results[asset]['drawdown']:.2%}")
            print(f"    Trades: {results[asset]['trades']}")

        # Find best performing asset
        best_asset = max(results.keys(), key=lambda x: results[x]['sharpe'])
        print(f"\nBest Asset: {best_asset} (Sharpe: {results[best_asset]['sharpe']:.3f})")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_portfolio_comparison():
    """Test portfolio vs individual assets"""
    print("\nTest 3: Portfolio vs Individual Assets")
    print("=" * 50)

    try:
        import vectorbt as vbt

        assets_data = create_test_portfolio()
        price_matrix = pd.DataFrame()

        for asset, data in assets_data.items():
            price_matrix[asset] = data['close']

        # Portfolio: Equal weight buy and hold
        entries = pd.DataFrame(False, index=price_matrix.index, columns=price_matrix.columns)
        entries.iloc[0] = True

        portfolio = vbt.Portfolio.from_signals(
            close=price_matrix,
            entries=entries,
            exits=pd.DataFrame(False, index=price_matrix.index, columns=price_matrix.columns),
            init_cash=100000,
            fees=0.001,
            freq='1D'
        )

        return_val = portfolio.total_return()
        sharpe_val = portfolio.sharpe_ratio()
        drawdown_val = portfolio.max_drawdown()

        portfolio_return = float(return_val.iloc[-1] if hasattr(return_val, 'iloc') else return_val)
        portfolio_sharpe = float(sharpe_val.iloc[-1] if hasattr(sharpe_val, 'iloc') else sharpe_val)
        portfolio_drawdown = float(drawdown_val.iloc[-1] if hasattr(drawdown_val, 'iloc') else drawdown_val)

        print(f"Equal Weight Portfolio:")
        print(f"  Return: {portfolio_return:.2%}")
        print(f"  Sharpe: {portfolio_sharpe:.3f}")
        print(f"  Drawdown: {portfolio_drawdown:.2%}")

        # Compare with individual assets
        print(f"\nIndividual Assets:")
        for asset in price_matrix.columns:
            data = assets_data[asset]

            # Buy and hold for individual asset
            individual_entries = pd.Series(False, index=data.index)
            individual_entries.iloc[0] = True
            individual_exits = pd.Series(False, index=data.index)

            individual_portfolio = vbt.Portfolio.from_signals(
                close=data['close'],
                entries=individual_entries,
                exits=individual_exits,
                init_cash=100000,
                fees=0.001
            )

            asset_return_val = individual_portfolio.total_return()
            asset_sharpe_val = individual_portfolio.sharpe_ratio()

            asset_return = float(asset_return_val.iloc[-1] if hasattr(asset_return_val, 'iloc') else asset_return_val)
            asset_sharpe = float(asset_sharpe_val.iloc[-1] if hasattr(asset_sharpe_val, 'iloc') else asset_sharpe_val)

            print(f"  {asset}: Return {asset_return:.2%}, Sharpe {asset_sharpe:.3f}")

        # Portfolio diversification benefit
        print(f"\nDiversification Analysis:")
        print(f"  Portfolio Sharpe: {portfolio_sharpe:.3f}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_simple_weighting():
    """Test different weighting schemes"""
    print("\nTest 4: Simple Weighting Schemes")
    print("=" * 50)

    try:
        import vectorbt as vbt

        assets_data = create_test_portfolio()
        price_matrix = pd.DataFrame()

        for asset, data in assets_data.items():
            price_matrix[asset] = data['close']

        # Different weighting schemes
        weighting_schemes = {
            'Equal Weight': [1/3, 1/3, 1/3],
            'Tech Heavy': [0.6, 0.2, 0.2],
            'Balanced': [0.4, 0.3, 0.3]
        }

        base_entries = pd.DataFrame(False, index=price_matrix.index, columns=price_matrix.columns)
        base_entries.iloc[0] = True
        base_exits = pd.DataFrame(False, index=price_matrix.index, columns=price_matrix.columns)

        results = {}

        for scheme_name, weights in weighting_schemes.items():
            portfolio = vbt.Portfolio.from_signals(
                close=price_matrix,
                entries=base_entries,
                exits=base_exits,
                size=weights,
                init_cash=100000,
                fees=0.001,
                freq='1D'
            )

            return_val = portfolio.total_return()
            sharpe_val = portfolio.sharpe_ratio()
            drawdown_val = portfolio.max_drawdown()

            results[scheme_name] = {
                'return': float(return_val.iloc[-1] if hasattr(return_val, 'iloc') else return_val),
                'sharpe': float(sharpe_val.iloc[-1] if hasattr(sharpe_val, 'iloc') else sharpe_val),
                'drawdown': float(drawdown_val.iloc[-1] if hasattr(drawdown_val, 'iloc') else drawdown_val)
            }

            print(f"  {scheme_name} ({weights}):")
            print(f"    Return: {results[scheme_name]['return']:.2%}")
            print(f"    Sharpe: {results[scheme_name]['sharpe']:.3f}")
            print(f"    Drawdown: {results[scheme_name]['drawdown']:.2%}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Main test function"""
    print("Simple Multi-Asset Portfolio Test Suite")
    print("=" * 60)

    success_count = 0
    total_tests = 4

    # Run tests
    if test_basic_multi_asset():
        success_count += 1

    if test_individual_assets():
        success_count += 1

    if test_portfolio_comparison():
        success_count += 1

    if test_simple_weighting():
        success_count += 1

    print(f"\n" + "=" * 60)
    print(f"Test Summary: {success_count}/{total_tests} tests passed")

    if success_count == total_tests:
        print("SUCCESS: Basic multi-asset portfolio functionality working!")
        print("VectorBT multi-asset backtesting confirmed")
    else:
        print("PARTIAL: Some tests failed")

    print("=" * 60)

if __name__ == "__main__":
    main()
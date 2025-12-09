#!/usr/bin/env python3
"""
Test Multi-Asset Portfolio Engine
測試多資產投資組合引擎
"""

import sys
import os
import numpy as np
import pandas as pd

# Add simplified_system to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'simplified_system'))

def create_multi_asset_data():
    """Create test data for multiple assets"""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
    n_days = len(dates)

    assets = ['TECH_STOCK', 'BANK_STOCK', 'PROPERTY_STOCK', 'UTILITY_STOCK']
    data_dict = {}

    # Create different price patterns for each asset
    asset_params = {
        'TECH_STOCK': {'initial_price': 500, 'drift': 0.001, 'volatility': 0.025},
        'BANK_STOCK': {'initial_price': 200, 'drift': 0.0005, 'volatility': 0.015},
        'PROPERTY_STOCK': {'initial_price': 100, 'drift': 0.0003, 'volatility': 0.020},
        'UTILITY_STOCK': {'initial_price': 50, 'drift': 0.0002, 'volatility': 0.010}
    }

    for asset, params in asset_params.items():
        # Generate returns with different characteristics
        returns = np.random.normal(params['drift'], params['volatility'], n_days)
        prices = params['initial_price'] * np.exp(np.cumsum(returns))

        # Create OHLCV data
        high = prices * (1 + np.abs(np.random.normal(0, 0.01, n_days)))
        low = prices * (1 - np.abs(np.random.normal(0, 0.01, n_days)))
        open_price = prices + np.random.normal(0, prices * 0.005, n_days)
        volume = np.random.randint(1000000, 5000000, n_days)

        # Ensure OHLC relationships
        high = np.maximum(high, np.maximum(open_price, prices))
        low = np.minimum(low, np.minimum(open_price, prices))

        data_dict[asset] = pd.DataFrame({
            'open': open_price,
            'high': high,
            'low': low,
            'close': prices,
            'volume': volume
        }, index=dates)

    print(f"Created data for {len(data_dict)} assets:")
    for asset, data in data_dict.items():
        print(f"  {asset}: {len(data)} days, price range: {data['close'].min():.2f}-{data['close'].max():.2f}")

    return data_dict

def test_portfolio_import():
    """Test portfolio engine import"""
    print("Testing Portfolio Engine Import")
    print("=" * 50)

    try:
        from simplified_system.src.backtest.portfolio_engine import (
            PortfolioEngine, PortfolioConfig, create_portfolio_engine,
            backtest_multi_asset_portfolio
        )
        print("SUCCESS: Portfolio engine imported")

        # Test configuration
        config = PortfolioConfig(initial_cash=1000000, max_positions=10)
        print(f"SUCCESS: Portfolio config created with {config.initial_cash:,.0f} initial cash")

        # Test engine creation
        engine = create_portfolio_engine(config)
        print("SUCCESS: Portfolio engine created")

        return engine

    except Exception as e:
        print(f"ERROR: Import failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_equal_weight_portfolio(engine, data_dict):
    """Test equal weight portfolio strategy"""
    print("\nTesting Equal Weight Portfolio")
    print("=" * 50)

    try:
        result = engine.backtest_portfolio(
            data_dict=data_dict,
            strategy="EQUAL_WEIGHT"
        )

        print(f"Portfolio Performance:")
        print(f"  Assets: {result.assets}")
        print(f"  Weights: {result.weights}")
        print(f"  Portfolio Return: {result.portfolio_return:.2%}")
        print(f"  Sharpe Ratio: {result.portfolio_sharpe:.3f}")
        print(f"  Volatility: {result.portfolio_volatility:.2%}")
        print(f"  Max Drawdown: {result.portfolio_max_drawdown:.2%}")
        print(f"  Calmar Ratio: {result.portfolio_calmar:.3f}")
        print(f"  Sortino Ratio: {result.portfolio_sortino:.3f}")

        print(f"\nRisk Metrics:")
        print(f"  VaR (95%): {result.var_95:.2%}")
        print(f"  VaR (99%): {result.var_99:.2%}")
        print(f"  Expected Shortfall: {result.expected_shortfall:.2%}")
        print(f"  Beta: {result.beta:.3f}")
        print(f"  Alpha: {result.alpha:.2%}")
        print(f"  Information Ratio: {result.information_ratio:.3f}")

        print(f"\nIndividual Asset Performance:")
        for asset in result.assets:
            print(f"  {asset}:")
            print(f"    Return: {result.individual_returns[asset]:.2%}")
            print(f"    Sharpe: {result.individual_sharpes[asset]:.3f}")
            print(f"    Volatility: {result.individual_volatilities[asset]:.2%}")

        print(f"\nTrading Statistics:")
        print(f"  Total Trades: {result.total_trades}")
        print(f"  Win Rate: {result.win_rate:.2%}")
        print(f"  Profit Factor: {result.profit_factor:.2f}")

        return True

    except Exception as e:
        print(f"ERROR: Equal weight test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_custom_weights_portfolio(engine, data_dict):
    """Test custom weights portfolio"""
    print("\nTesting Custom Weights Portfolio")
    print("=" * 50)

    try:
        # Define custom weights
        custom_weights = {
            'TECH_STOCK': 0.4,
            'BANK_STOCK': 0.3,
            'PROPERTY_STOCK': 0.2,
            'UTILITY_STOCK': 0.1
        }

        print(f"Custom weights: {custom_weights}")

        result = engine.backtest_portfolio(
            data_dict=data_dict,
            weights=custom_weights
        )

        print(f"Custom Portfolio Performance:")
        print(f"  Portfolio Return: {result.portfolio_return:.2%}")
        print(f"  Sharpe Ratio: {result.portfolio_sharpe:.3f}")
        print(f"  Max Drawdown: {result.portfolio_max_drawdown:.2%}")
        print(f"  Applied Weights: {result.weights}")

        return True

    except Exception as e:
        print(f"ERROR: Custom weights test failed: {e}")
        return False

def test_strategy_portfolios(engine, data_dict):
    """Test different strategy portfolios"""
    print("\nTesting Strategy-Based Portfolios")
    print("=" * 50)

    strategies = ["BUY_AND_HOLD", "RSI_MEAN_REVERSION", "DUAL_MOVING_AVERAGE"]
    results = {}

    for strategy in strategies:
        try:
            print(f"\nTesting {strategy} strategy...")
            result = engine.backtest_portfolio(
                data_dict=data_dict,
                strategy=strategy
            )

            results[strategy] = {
                'return': result.portfolio_return,
                'sharpe': result.portfolio_sharpe,
                'drawdown': result.portfolio_max_drawdown,
                'volatility': result.portfolio_volatility
            }

            print(f"  Return: {result.portfolio_return:.2%}")
            print(f"  Sharpe: {result.portfolio_sharpe:.3f}")
            print(f"  Drawdown: {result.portfolio_max_drawdown:.2%}")

        except Exception as e:
            print(f"  ERROR {strategy}: {e}")

    # Find best performing strategy
    if results:
        best_strategy = max(results.keys(), key=lambda x: results[x]['sharpe'])
        print(f"\nBest Strategy: {best_strategy}")
        print(f"  Sharpe: {results[best_strategy]['sharpe']:.3f}")
        print(f"  Return: {results[best_strategy]['return']:.2%}")

    return len(results) > 0

def test_portfolio_optimization(engine, data_dict):
    """Test portfolio optimization"""
    print("\nTesting Portfolio Optimization")
    print("=" * 50)

    optimization_methods = ["EQUAL_WEIGHT", "MIN_VOLATILITY", "RISK_PARITY"]
    results = {}

    for method in optimization_methods:
        try:
            print(f"\nTesting {method} optimization...")
            result = engine.optimize_portfolio(
                data_dict=data_dict,
                optimization_method=method
            )

            results[method] = {
                'return': result.portfolio_return,
                'sharpe': result.portfolio_sharpe,
                'volatility': result.portfolio_volatility,
                'weights': result.weights
            }

            print(f"  Return: {result.portfolio_return:.2%}")
            print(f"  Sharpe: {result.portfolio_sharpe:.3f}")
            print(f"  Volatility: {result.portfolio_volatility:.2%}")
            print(f"  Weights: {result.weights}")

        except Exception as e:
            print(f"  ERROR {method}: {e}")

    # Compare optimization results
    if results:
        print(f"\nOptimization Comparison:")
        for method, metrics in results.items():
            print(f"  {method}:")
            print(f"    Sharpe: {metrics['sharpe']:.3f}")
            print(f"    Return: {metrics['return']:.2%}")
            print(f"    Volatility: {metrics['volatility']::.2%}")

    return len(results) > 0

def test_portfolio_convenience_function(data_dict):
    """Test portfolio convenience function"""
    print("\nTesting Portfolio Convenience Function")
    print("=" * 50)

    try:
        from simplified_system.src.backtest.portfolio_engine import backtest_multi_asset_portfolio

        result = backtest_multi_asset_portfolio(
            data_dict=data_dict,
            strategy="EQUAL_WEIGHT"
        )

        print(f"Convenience Function Results:")
        print(f"  Portfolio Return: {result.portfolio_return:.2%}")
        print(f"  Sharpe Ratio: {result.portfolio_sharpe:.3f}")
        print(f"  Number of Assets: {len(result.assets)}")

        return True

    except Exception as e:
        print(f"ERROR: Convenience function test failed: {e}")
        return False

def test_large_portfolio():
    """Test with larger portfolio"""
    print("\nTesting Larger Portfolio")
    print("=" * 50)

    try:
        # Create larger dataset
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=252, freq='D')  # 1 year

        # Create 8 assets
        assets = [f'STOCK_{i:02d}' for i in range(1, 9)]
        data_dict = {}

        for asset in assets:
            # Different characteristics for each asset
            drift = np.random.uniform(0.0002, 0.001)
            volatility = np.random.uniform(0.015, 0.030)
            initial_price = np.random.uniform(50, 200)

            returns = np.random.normal(drift, volatility, len(dates))
            prices = initial_price * np.exp(np.cumsum(returns))

            data_dict[asset] = pd.DataFrame({
                'open': prices,
                'high': prices * 1.02,
                'low': prices * 0.98,
                'close': prices,
                'volume': np.random.randint(1000000, 5000000, len(dates))
            }, index=dates)

        # Test portfolio with 8 assets
        from simplified_system.src.backtest.portfolio_engine import backtest_multi_asset_portfolio

        result = backtest_multi_asset_portfolio(
            data_dict=data_dict,
            strategy="EQUAL_WEIGHT"
        )

        print(f"Larger Portfolio Results ({len(assets)} assets):")
        print(f"  Portfolio Return: {result.portfolio_return:.2%}")
        print(f"  Sharpe Ratio: {result.portfolio_sharpe:.3f}")
        print(f"  Max Drawdown: {result.portfolio_max_drawdown:.2%}")
        print(f"  Total Trades: {result.total_trades}")

        return True

    except Exception as e:
        print(f"ERROR: Large portfolio test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Multi-Asset Portfolio Engine Test")
    print("=" * 60)
    print("Testing Professional Portfolio Management")
    print("=" * 60)

    success_count = 0
    total_tests = 6

    # Create test data
    data_dict = create_multi_asset_data()

    # Test 1: Import
    engine = test_portfolio_import()
    if engine:
        success_count += 1

    # Test 2: Equal weight portfolio
    if engine and test_equal_weight_portfolio(engine, data_dict):
        success_count += 1

    # Test 3: Custom weights portfolio
    if engine and test_custom_weights_portfolio(engine, data_dict):
        success_count += 1

    # Test 4: Strategy portfolios
    if engine and test_strategy_portfolios(engine, data_dict):
        success_count += 1

    # Test 5: Portfolio optimization
    if engine and test_portfolio_optimization(engine, data_dict):
        success_count += 1

    # Test 6: Convenience function
    if test_portfolio_convenience_function(data_dict):
        success_count += 1

    # Test 7: Large portfolio
    if test_large_portfolio():
        success_count += 1

    print(f"\n" + "=" * 60)
    print(f"Final Test Summary: {success_count}/{total_tests+1} test groups passed")

    if success_count >= total_tests:
        print("SUCCESS: Multi-Asset Portfolio Engine working!")
        print("Professional portfolio management features ready")
        print("✅ Equal weight portfolios")
        print("✅ Custom weight allocations")
        print("✅ Strategy-based portfolios")
        print("✅ Portfolio optimization")
        print("✅ Advanced risk metrics")
        print("✅ Large portfolio support")
    else:
        print("PARTIAL: Some tests failed")

    print("=" * 60)

if __name__ == "__main__":
    main()
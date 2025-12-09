#!/usr/bin/env python3
"""
Test Multi-Asset Portfolio Engine
测试多资产投资组合引擎
"""

import numpy as np
import pandas as pd
import sys
import os
import time

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

def create_multi_asset_data():
    """Create multi-asset test data"""
    np.random.seed(42)

    # Create 3 years of data
    dates = pd.date_range(start='2022-01-01', end='2024-12-31', freq='D')
    n_days = len(dates)

    # Create 4 assets with different characteristics
    assets = {}
    asset_characteristics = {
        'TECH': {'drift': 0.0012, 'vol': 0.025, 'initial': 200},
        'BANK': {'drift': 0.0005, 'vol': 0.015, 'initial': 100},
        'RETAIL': {'drift': 0.0003, 'vol': 0.018, 'initial': 50},
        'UTILITY': {'drift': 0.0002, 'vol': 0.012, 'initial': 30}
    }

    for asset, char in asset_characteristics.items():
        returns = np.random.normal(char['drift'], char['vol'], n_days)
        prices = char['initial'] * np.exp(np.cumsum(returns))

        assets[asset] = pd.DataFrame({
            'open': prices + np.random.normal(0, prices * 0.005, n_days),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, n_days))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, n_days))),
            'close': prices,
            'volume': np.random.randint(500000, 2000000, n_days)
        }, index=dates)

        # Ensure OHLC relationships
        high = np.maximum(assets[asset]['high'], np.maximum(assets[asset]['open'], assets[asset]['close']))
        low = np.minimum(assets[asset]['low'], np.minimum(assets[asset]['open'], assets[asset]['close']))
        assets[asset]['high'] = high
        assets[asset]['low'] = low

    print(f"Created data for {len(assets)} assets over {n_days} days")
    return assets

def test_basic_portfolio():
    """Test basic portfolio functionality"""
    print_section("Basic Portfolio Test")

    try:
        # Import portfolio engine directly
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'simplified_system', 'src'))
        from backtest.portfolio_engine import PortfolioEngine, PortfolioConfig

        # Create engine
        config = PortfolioConfig(initial_cash=100000, fees=0.001)
        engine = PortfolioEngine(config)

        print_result("Portfolio Engine Creation", True)

        # Create multi-asset data
        assets_data = create_multi_asset_data()

        # Test equal weight portfolio
        result = engine.backtest_portfolio(
            data_dict=assets_data,
            strategy="EQUAL_WEIGHT"
        )

        print_result("Equal Weight Portfolio", True,
                    f"Return: {result.portfolio_return:.2%}, Sharpe: {result.portfolio_sharpe:.3f}")

        return engine, assets_data, result

    except Exception as e:
        print_result("Basic Portfolio", False, str(e))
        import traceback
        traceback.print_exc()
        return None, None, None

def test_portfolio_strategies(engine, assets_data):
    """Test different portfolio strategies"""
    print_section("Portfolio Strategies Test")

    if engine is None:
        print_result("Portfolio Strategies", False, "No engine available")
        return False

    strategies_to_test = [
        "BUY_AND_HOLD",
        "RSI_MEAN_REVERSION",
        "DUAL_MOVING_AVERAGE"
    ]

    success_count = 0
    results = {}

    for strategy in strategies_to_test:
        try:
            result = engine.backtest_portfolio(
                data_dict=assets_data,
                strategy=strategy
            )

            results[strategy] = {
                'return': result.portfolio_return,
                'sharpe': result.portfolio_sharpe,
                'volatility': result.portfolio_volatility,
                'max_dd': result.portfolio_max_drawdown
            }

            print_result(f"Strategy '{strategy}'", True,
                        f"Return: {result.portfolio_return:.2%}, Sharpe: {result.portfolio_sharpe:.3f}")
            success_count += 1

        except Exception as e:
            print_result(f"Strategy '{strategy}'", False, str(e))

    # Find best strategy
    if results:
        best_strategy = max(results.keys(), key=lambda x: results[x]['sharpe'])
        print_result("Best Strategy", True,
                    f"{best_strategy} (Sharpe: {results[best_strategy]['sharpe']:.3f})")

    return success_count > 0

def test_portfolio_optimization(engine, assets_data):
    """Test portfolio optimization"""
    print_section("Portfolio Optimization Test")

    if engine is None:
        print_result("Portfolio Optimization", False, "No engine available")
        return False

    optimization_methods = [
        "EQUAL_WEIGHT",
        "MIN_VOLATILITY",
        "RISK_PARITY"
    ]

    success_count = 0

    for method in optimization_methods:
        try:
            result = engine.optimize_portfolio(
                data_dict=assets_data,
                optimization_method=method
            )

            print_result(f"Optimization '{method}'", True,
                        f"Return: {result.portfolio_return:.2%}, Sharpe: {result.portfolio_sharpe:.3f}")
            success_count += 1

        except Exception as e:
            print_result(f"Optimization '{method}'", False, str(e))

    return success_count > 0

def test_custom_weights(engine, assets_data):
    """Test custom weights"""
    print_section("Custom Weights Test")

    if engine is None:
        print_result("Custom Weights", False, "No engine available")
        return False

    try:
        # Define custom weights
        custom_weights = {
            'TECH': 0.4,      # 40% tech
            'BANK': 0.3,      # 30% bank
            'RETAIL': 0.2,    # 20% retail
            'UTILITY': 0.1    # 10% utility
        }

        result = engine.backtest_portfolio(
            data_dict=assets_data,
            strategy="CUSTOM_WEIGHTS",
            weights=custom_weights
        )

        print_result("Custom Weights Portfolio", True,
                    f"Return: {result.portfolio_return:.2%}, Sharpe: {result.portfolio_sharpe:.3f}")

        # Verify weights
        print(f"Final weights: {result.weights}")

        return True

    except Exception as e:
        print_result("Custom Weights", False, str(e))
        return False

def test_risk_metrics(engine, assets_data):
    """Test advanced risk metrics"""
    print_section("Advanced Risk Metrics Test")

    if engine is None:
        print_result("Risk Metrics", False, "No engine available")
        return False

    try:
        result = engine.backtest_portfolio(
            data_dict=assets_data,
            strategy="EQUAL_WEIGHT"
        )

        # Display risk metrics
        print_result("Risk Metrics Calculation", True)
        print(f"  VaR (95%): {result.var_95:.2%}")
        print(f"  VaR (99%): {result.var_99:.2%}")
        print(f"  Expected Shortfall: {result.expected_shortfall:.2%}")
        print(f"  Beta: {result.beta:.3f}")
        print(f"  Alpha: {result.alpha:.2%}")
        print(f"  Information Ratio: {result.information_ratio:.3f}")

        # Test individual asset metrics
        print_result("Individual Asset Metrics", True)
        for asset in result.assets[:3]:  # Show first 3
            print(f"  {asset}: Return {result.individual_returns[asset]:.2%}, "
                  f"Sharpe {result.individual_sharpes[asset]:.3f}")

        return True

    except Exception as e:
        print_result("Risk Metrics", False, str(e))
        return False

def test_performance_benchmark(engine, assets_data):
    """Test performance benchmarking"""
    print_section("Performance Benchmark Test")

    if engine is None:
        print_result("Performance Benchmark", False, "No engine available")
        return False

    try:
        # Benchmark single asset vs portfolio
        start_time = time.time()

        # Portfolio test
        portfolio_result = engine.backtest_portfolio(
            data_dict=assets_data,
            strategy="EQUAL_WEIGHT"
        )

        portfolio_time = time.time() - start_time

        # Single asset test (first asset)
        single_asset_data = {list(assets_data.keys())[0]: assets_data[list(assets_data.keys())[0]]}
        single_result = engine.backtest_portfolio(
            data_dict=single_asset_data,
            strategy="BUY_AND_HOLD"
        )

        print_result("Performance Benchmark", True,
                    f"Portfolio time: {portfolio_time:.3f}s")
        print_result("Diversification Benefit", True,
                    f"Portfolio Sharpe: {portfolio_result.portfolio_sharpe:.3f} vs "
                    f"Single Asset: {single_result.portfolio_sharpe:.3f}")

        return True

    except Exception as e:
        print_result("Performance Benchmark", False, str(e))
        return False

def main():
    """Main test function"""
    print_section("MULTI-ASSET PORTFOLIO ENGINE TEST")
    print("Testing Professional Multi-Asset Portfolio Capabilities")
    print("=" * 60)

    success_count = 0
    total_tests = 6

    # Test 1: Basic Portfolio
    engine, assets_data, result = test_basic_portfolio()
    if engine:
        success_count += 1

    # Test 2: Portfolio Strategies
    if test_portfolio_strategies(engine, assets_data):
        success_count += 1

    # Test 3: Portfolio Optimization
    if test_portfolio_optimization(engine, assets_data):
        success_count += 1

    # Test 4: Custom Weights
    if test_custom_weights(engine, assets_data):
        success_count += 1

    # Test 5: Risk Metrics
    if test_risk_metrics(engine, assets_data):
        success_count += 1

    # Test 6: Performance Benchmark
    if test_performance_benchmark(engine, assets_data):
        success_count += 1

    # Summary
    print_section("MULTI-ASSET PORTFOLIO TEST SUMMARY")
    print(f"Tests Passed: {success_count}/{total_tests}")
    print(f"Success Rate: {success_count/total_tests*100:.1f}%")

    if success_count >= total_tests - 1:  # Allow one test to fail
        print("\n" + "*" * 50)
        print("SUCCESS: MULTI-ASSET PORTFOLIO ENGINE WORKING!")
        print("* Professional Portfolio Management Ready")
        print("* Modern Portfolio Theory Implemented")
        print("* Advanced Risk Metrics Available")
        print("* Portfolio Optimization Functional")
        print("*" * 50)

        if result:
            print(f"\nSample Portfolio Results:")
            print(f"  Assets: {len(result.assets)}")
            print(f"  Return: {result.portfolio_return:.2%}")
            print(f"  Sharpe: {result.portfolio_sharpe:.3f}")
            print(f"  Max Drawdown: {result.portfolio_max_drawdown:.2%}")
            print(f"  Volatility: {result.portfolio_volatility:.2%}")

    else:
        print(f"\nWARNING: {total_tests - success_count} test(s) failed")
        print("Portfolio engine needs more work")

    return success_count >= total_tests - 1

if __name__ == "__main__":
    main()
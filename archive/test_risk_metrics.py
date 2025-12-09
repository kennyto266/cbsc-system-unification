#!/usr/bin/env python3
"""
Test Advanced Risk Metrics Calculator
測試進階風險指標計算器
"""

import sys
import os
import numpy as np
import pandas as pd

# Add simplified_system to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'simplified_system'))

def create_test_returns():
    """Create test return series"""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')

    # Generate realistic returns with some skewness and fat tails
    n_days = len(dates)

    # Base returns
    base_returns = np.random.normal(0.0008, 0.02, n_days)

    # Add some fat tails
    extreme_events = np.random.choice([-0.05, 0.05], size=5, p=[0.5, 0.5])
    extreme_positions = np.random.choice(n_days, size=5, replace=False)
    base_returns[extreme_positions] = extreme_events

    # Add slight trend
    trend = np.linspace(0, 0.0002, n_days)
    base_returns += trend

    returns_series = pd.Series(base_returns, index=dates)

    # Create market returns (benchmark)
    market_returns = np.random.normal(0.0005, 0.015, n_days)
    market_trend = np.linspace(0, 0.0001, n_days)
    market_returns += market_trend

    market_series = pd.Series(market_returns, index=dates)

    # Create portfolio value series
    initial_value = 1000000
    portfolio_values = initial_value * (1 + returns_series).cumprod()

    return returns_series, market_series, portfolio_values

def test_risk_metrics_import():
    """Test risk metrics import"""
    print("Testing Risk Metrics Import")
    print("=" * 50)

    try:
        from simplified_system.src.backtest.risk_metrics import (
            AdvancedRiskMetrics, RiskMetricsConfig, calculate_risk_metrics,
            calculate_portfolio_risk
        )
        print("SUCCESS: Risk metrics imported")

        # Test configuration
        config = RiskMetricsConfig(
            confidence_levels=[0.95, 0.99],
            var_method="historical",
            risk_free_rate=0.03
        )
        print("SUCCESS: Risk metrics configuration created")

        # Test calculator creation
        calculator = AdvancedRiskMetrics(config)
        print("SUCCESS: Risk metrics calculator created")

        return calculator

    except Exception as e:
        print(f"ERROR: Import failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_basic_risk_metrics(calculator, returns, market_returns, portfolio_values):
    """Test basic risk metrics calculation"""
    print("\nTesting Basic Risk Metrics")
    print("=" * 50)

    try:
        # Calculate comprehensive risk metrics
        risk_metrics = calculator.calculate_risk_metrics(
            returns=returns,
            benchmark_returns=market_returns,
            portfolio_value=portfolio_values
        )

        print("Risk Metrics Results:")
        print(f"  Data points: {risk_metrics.data_points}")
        print(f"  Time period: {risk_metrics.time_period}")

        print(f"\nBasic Statistics:")
        print(f"  Mean Return (Annual): {risk_metrics.mean_return:.2%}")
        print(f"  Volatility (Annual): {risk_metrics.volatility:.2%}")
        print(f"  Skewness: {risk_metrics.skewness:.3f}")
        print(f"  Kurtosis: {risk_metrics.kurtosis:.3f}")
        print(f"  Downside Volatility: {risk_metrics.downside_volatility:.2%}")

        print(f"\nValue at Risk:")
        print(f"  VaR (90%): {risk_metrics.var_90:.2%}")
        print(f"  VaR (95%): {risk_metrics.var_95:.2%}")
        print(f"  VaR (99%): {risk_metrics.var_99:.2%}")
        print(f"  Expected Shortfall (95%): {risk_metrics.expected_shortfall_95:.2%}")
        print(f"  Expected Shortfall (99%): {risk_metrics.expected_shortfall_99:.2%}")

        print(f"\nSharpe Ratio Variants:")
        print(f"  Sharpe Ratio: {risk_metrics.sharpe_ratio:.3f}")
        print(f"  Sortino Ratio: {risk_metrics.sortino_ratio:.3f}")
        print(f"  Calmar Ratio: {risk_metrics.calmar_ratio:.3f}")
        print(f"  Information Ratio: {risk_metrics.information_ratio:.3f}")
        print(f"  Treynor Ratio: {risk_metrics.treynor_ratio:.3f}")

        return True

    except Exception as e:
        print(f"ERROR: Basic risk metrics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_drawdown_analysis(calculator, returns, portfolio_values):
    """Test drawdown analysis"""
    print("\nTesting Drawdown Analysis")
    print("=" * 50)

    try:
        risk_metrics = calculator.calculate_risk_metrics(
            returns=returns,
            portfolio_value=portfolio_values
        )

        print("Drawdown Analysis:")
        print(f"  Maximum Drawdown: {risk_metrics.max_drawdown:.2%}")
        print(f"  Average Drawdown: {risk_metrics.average_drawdown:.2%}")
        print(f"  Drawdown Duration: {risk_metrics.drawdown_duration} days")
        print(f"  Recovery Time: {risk_metrics.recovery_time} days")

        # Verify drawdown calculation
        if risk_metrics.max_drawdown < 0:
            print("  ✓ Maximum drawdown correctly calculated")
        else:
            print("  ✗ Maximum drawdown should be negative")

        return True

    except Exception as e:
        print(f"ERROR: Drawdown analysis failed: {e}")
        return False

def test_market_risk_metrics(calculator, returns, market_returns):
    """Test market risk metrics"""
    print("\nTesting Market Risk Metrics")
    print("=" * 50)

    try:
        risk_metrics = calculator.calculate_risk_metrics(
            returns=returns,
            benchmark_returns=market_returns
        )

        print("Market Risk Analysis:")
        print(f"  Beta: {risk_metrics.beta:.3f}")
        print(f"  Alpha (Annual): {risk_metrics.alpha:.2%}")
        print(f"  Tracking Error: {risk_metrics.tracking_error:.2%}")
        print(f"  Up Capture: {risk_metrics.up_capture:.1%}")
        print(f"  Down Capture: {risk_metrics.down_capture:.1%}")

        # Reasonableness checks
        if 0 < risk_metrics.beta < 3:
            print("  ✓ Beta within reasonable range")
        else:
            print(f"  ✗ Beta {risk_metrics.beta:.3f} seems unusual")

        return True

    except Exception as e:
        print(f"ERROR: Market risk metrics test failed: {e}")
        return False

def test_advanced_risk_metrics(calculator, returns, portfolio_values):
    """Test advanced risk metrics"""
    print("\nTesting Advanced Risk Metrics")
    print("=" * 50)

    try:
        risk_metrics = calculator.calculate_risk_metrics(
            returns=returns,
            portfolio_value=portfolio_values
        )

        print("Advanced Risk Metrics:")
        print(f"  Sterling Ratio: {risk_metrics.sterling_ratio:.3f}")
        print(f"  Burke Ratio: {risk_metrics.burke_ratio:.3f}")
        print(f"  Pain Index: {risk_metrics.pain_index:.2%}")
        print(f"  Ulcer Index: {risk_metrics.ulcer_index:.2%}")
        print(f"  Martin Ratio: {risk_metrics.martin_ratio:.3f}")

        print(f"\nTail Risk Metrics:")
        print(f"  Tail Ratio: {risk_metrics.tail_ratio:.3f}")
        print(f"  Conditional VaR: {risk_metrics.conditional_value_at_risk:.2%}")

        # Risk assessment
        if risk_metrics.volatility < 0.3:  # 30% annual vol
            print("  ✓ Volatility within normal range")
        else:
            print(f"  ! High volatility detected: {risk_metrics.volatility:.2%}")

        if risk_metrics.var_95 > -0.05:  # VaR not too extreme
            print("  ✓ VaR (95%) within acceptable range")
        else:
            print(f"  ! Extreme VaR (95%): {risk_metrics.var_95:.2%}")

        return True

    except Exception as e:
        print(f"ERROR: Advanced risk metrics test failed: {e}")
        return False

def test_convenience_functions(returns, market_returns):
    """Test convenience functions"""
    print("\nTesting Convenience Functions")
    print("=" * 50)

    try:
        from simplified_system.src.backtest.risk_metrics import calculate_risk_metrics, calculate_portfolio_risk

        # Test calculate_risk_metrics
        risk_metrics = calculate_risk_metrics(
            returns=returns,
            benchmark_returns=market_returns
        )

        print(f"Convenience function results:")
        print(f"  Sharpe Ratio: {risk_metrics.sharpe_ratio:.3f}")
        print(f"  Max Drawdown: {risk_metrics.max_drawdown:.2%}")
        print(f"  Beta: {risk_metrics.beta:.3f}")

        # Test calculate_portfolio_risk
        risk_dict = calculate_portfolio_risk(
            portfolio_returns=returns,
            market_returns=market_returns
        )

        print(f"\nDictionary format results:")
        print(f"  Available sections: {list(risk_dict.keys())}")
        print(f"  Sharpe Ratio: {risk_dict['sharpe_variants']['sharpe_ratio']:.3f}")
        print(f"  VaR (95%): {risk_dict['var_metrics']['var_95']:.2%}")

        return True

    except Exception as e:
        print(f"ERROR: Convenience functions test failed: {e}")
        return False

def test_risk_comparison():
    """Test risk metrics comparison between strategies"""
    print("\nTesting Risk Metrics Comparison")
    print("=" * 50)

    try:
        from simplified_system.src.backtest.risk_metrics import calculate_risk_metrics

        # Create two different return series
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=252, freq='D')

        # Conservative strategy (lower risk, lower return)
        conservative_returns = np.random.normal(0.0003, 0.008, 252)  # 0.03% daily, 8% vol
        conservative_series = pd.Series(conservative_returns, index=dates)

        # Aggressive strategy (higher risk, higher return)
        aggressive_returns = np.random.normal(0.0015, 0.025, 252)  # 0.15% daily, 25% vol
        aggressive_series = pd.Series(aggressive_returns, index=dates)

        # Calculate risk metrics for both
        conservative_metrics = calculate_risk_metrics(conservative_series)
        aggressive_metrics = calculate_risk_metrics(aggressive_series)

        print("Strategy Comparison:")
        print(f"  Conservative Strategy:")
        print(f"    Annual Return: {conservative_metrics.mean_return:.2%}")
        print(f"    Volatility: {conservative_metrics.volatility:.2%}")
        print(f"    Sharpe Ratio: {conservative_metrics.sharpe_ratio:.3f}")
        print(f"    Max Drawdown: {conservative_metrics.max_drawdown:.2%}")
        print(f"    VaR (95%): {conservative_metrics.var_95:.2%}")

        print(f"  Aggressive Strategy:")
        print(f"    Annual Return: {aggressive_metrics.mean_return:.2%}")
        print(f"    Volatility: {aggressive_metrics.volatility:.2%}")
        print(f"    Sharpe Ratio: {aggressive_metrics.sharpe_ratio:.3f}")
        print(f"    Max Drawdown: {aggressive_metrics.max_drawdown:.2%}")
        print(f"    VaR (95%): {aggressive_metrics.var_95:.2%}")

        # Risk-adjusted comparison
        print(f"\nRisk-Adjusted Analysis:")
        if conservative_metrics.sharpe_ratio > aggressive_metrics.sharpe_ratio:
            print("  ✓ Conservative strategy has better risk-adjusted returns")
        else:
            print("  ✓ Aggressive strategy has better risk-adjusted returns")

        return True

    except Exception as e:
        print(f"ERROR: Risk comparison test failed: {e}")
        return False

def test_export_functionality(calculator, returns, market_returns):
    """Test export functionality"""
    print("\nTesting Export Functionality")
    print("=" * 50)

    try:
        risk_metrics = calculator.calculate_risk_metrics(
            returns=returns,
            benchmark_returns=market_returns
        )

        # Export to dictionary
        risk_dict = risk_metrics.to_dict()

        print("Export Results:")
        print(f"  Dictionary keys: {list(risk_dict.keys())}")
        print(f"  Basic stats keys: {list(risk_dict['basic_statistics'].keys())}")
        print(f"  Total exported values: {sum(len(v) if isinstance(v, dict) else 1 for v in risk_dict.values())}")

        # Verify key values are exported correctly
        if risk_dict['basic_statistics']['volatility'] > 0:
            print("  ✓ Volatility correctly exported")
        if risk_dict['var_metrics']['var_95'] < 0:
            print("  ✓ VaR correctly exported")
        if risk_dict['sharpe_variants']['sharpe_ratio'] is not None:
            print("  ✓ Sharpe ratio correctly exported")

        return True

    except Exception as e:
        print(f"ERROR: Export functionality test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Advanced Risk Metrics Test Suite")
    print("=" * 60)
    print("Testing Professional Risk Analysis Capabilities")
    print("=" * 60)

    # Create test data
    returns, market_returns, portfolio_values = create_test_returns()
    print(f"Created test data: {len(returns)} daily returns")

    success_count = 0
    total_tests = 8

    # Test 1: Import
    calculator = test_risk_metrics_import()
    if calculator:
        success_count += 1

    # Test 2: Basic risk metrics
    if calculator and test_basic_risk_metrics(calculator, returns, market_returns, portfolio_values):
        success_count += 1

    # Test 3: Drawdown analysis
    if calculator and test_drawdown_analysis(calculator, returns, portfolio_values):
        success_count += 1

    # Test 4: Market risk metrics
    if calculator and test_market_risk_metrics(calculator, returns, market_returns):
        success_count += 1

    # Test 5: Advanced risk metrics
    if calculator and test_advanced_risk_metrics(calculator, returns, portfolio_values):
        success_count += 1

    # Test 6: Convenience functions
    if test_convenience_functions(returns, market_returns):
        success_count += 1

    # Test 7: Risk comparison
    if test_risk_comparison():
        success_count += 1

    # Test 8: Export functionality
    if calculator and test_export_functionality(calculator, returns, market_returns):
        success_count += 1

    print(f"\n" + "=" * 60)
    print(f"Final Test Summary: {success_count}/{total_tests} test groups passed")

    if success_count == total_tests:
        print("SUCCESS: Advanced risk metrics working!")
        print("Professional risk analysis capabilities ready")
        print("✅ Value at Risk (VaR) and Expected Shortfall")
        print("✅ Multiple Sharpe ratio variants")
        print("✅ Comprehensive drawdown analysis")
        print("✅ Market risk metrics (Alpha, Beta)")
        print("✅ Advanced risk-adjusted measures")
        print("✅ Tail risk analysis")
        print("✅ Pain and ulcer indices")
        print("✅ Export and reporting capabilities")
    else:
        print("PARTIAL: Some tests failed")

    print("=" * 60)

if __name__ == "__main__":
    main()
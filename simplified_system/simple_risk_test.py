#!/usr / bin / env python3
"""
Simple Risk Analytics Test Script
簡單風險分析測試腳本

Testing the basic functionality of risk analysis system
測試風險分析系統的基本功能
"""

import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def generate_test_data():
    """Generate test data"""
    print("Generating test data...")

    # Generate sample returns data
    np.random.seed(42)
    dates = pd.date_range(end = datetime.now(), periods = 252, freq="D")
    returns = pd.Series(
        np.random.normal(0.0005, 0.02, 252), index = dates, name="portfolio_returns"
    )

    # Generate portfolio positions
    portfolio_positions = pd.DataFrame(
        [
            {
                "asset": "AAPL",
                "market_value": 200000,
                "weight": 0.40,
                "sector": "Technology",
            },
            {
                "asset": "MSFT",
                "market_value": 150000,
                "weight": 0.30,
                "sector": "Technology",
            },
            {
                "asset": "GOOGL",
                "market_value": 100000,
                "weight": 0.20,
                "sector": "Technology",
            },
            {
                "asset": "Gold",
                "market_value": 50000,
                "weight": 0.10,
                "sector": "Commodities",
            },
        ]
    )

    print(f"Generated {len(returns)} days of returns data")
    print(f"Generated portfolio with {len(portfolio_positions)} positions")

    return returns, portfolio_positions


def test_monte_carlo_var(returns, portfolio_positions):
    """Test Monte Carlo VaR Calculator"""
    print("\nTesting Monte Carlo VaR Calculator...")

    try:
        # Import directly to avoid relative import issues
        from risk.monte_carlo_var import (
            DistributionType,
            MonteCarloVaRCalculator,
            VaRConfig,
        )

        # Create calculator with reduced simulations for faster testing
        config = VaRConfig(
            confidence_levels=[0.95],
            time_horizons=[1],
            num_simulations = 1000,  # Reduced for testing
            distribution_type = DistributionType.NORMAL,
            variance_reduction = None,
        )

        calculator = MonteCarloVaRCalculator(config)
        portfolio_value = portfolio_positions["market_value"].sum()

        # Calculate VaR
        results = calculator.calculate_var(returns, portfolio_value)

        print(f"SUCCESS: Monte Carlo VaR calculation completed")
        print(f"  Portfolio Value: ${portfolio_value:,.2f}")
        print(f"  Simulations: {len(results.simulated_returns)}")
        print(f"  Distribution: {results.distribution_params['type']}")

        # Display results
        for confidence, horizon_results in results.var_results.items():
            for horizon, var_result in horizon_results.items():
                print(
                    f"  VaR {int(confidence * 100)}% ({horizon}d): ${var_result.var_value:,.2f} ({var_result.var_percentage:.2%})"
                )
                print(f"  Expected Shortfall: ${var_result.expected_shortfall:,.2f}")

        return True

    except Exception as e:
        print(f"FAILED: Monte Carlo VaR test failed: {e}")
        return False


def test_stress_test_engine(returns, portfolio_positions):
    """Test Stress Test Engine"""
    print("\nTesting Stress Test Engine...")

    try:
        from risk.stress_test_engine import StressTestEngine

        engine = StressTestEngine()

        # Prepare portfolio data
        portfolio_data = {
            "current_value": portfolio_positions["market_value"].sum(),
            "returns": returns,
            "portfolio_id": "test_portfolio",
        }

        # Run stress tests with limited scenarios
        stress_report = engine.run_stress_tests(
            portfolio_data, scenario_ids=["2008_financial_crisis", "2020_covid_crash"]
        )

        print(f"SUCCESS: Stress testing completed")
        print(f"  Portfolio Value: ${portfolio_data['current_value']:,.2f}")
        print(f"  Worst Case Scenario: {stress_report.worst_case_scenario}")
        print(f"  Worst Case Loss: ${stress_report.worst_case_loss:,.2f}")
        print(f"  Worst Case Loss %: {stress_report.worst_case_loss_percentage:.2%}")
        print(
            f"  Portfolio Resilience Score: {stress_report.portfolio_resilience_score:.1f}/100"
        )
        print(f"  Scenarios Tested: {len(stress_report.scenarios_tested)}")

        return True

    except Exception as e:
        print(f"FAILED: Stress Test Engine test failed: {e}")
        return False


def test_liquidity_risk_analyzer(portfolio_positions):
    """Test Liquidity Risk Analyzer"""
    print("\nTesting Liquidity Risk Analyzer...")

    try:
        from risk.liquidity_risk import LiquidityRiskAnalyzer

        analyzer = LiquidityRiskAnalyzer()

        # Create simple market data
        market_data = {}
        for _, position in portfolio_positions.iterrows():
            asset = position["asset"]
            dates = pd.date_range(end = datetime.now(), periods = 100, freq="D")
            prices = pd.Series(
                [100 + np.random.normal(0, 10) for _ in range(100)], index = dates
            )
            volumes = pd.Series(
                [1000000 + np.random.normal(0, 100000) for _ in range(100)], index = dates
            )

            market_data[asset] = pd.DataFrame({"close": prices, "volume": volumes})

        # Analyze liquidity risk
        liquidity_results = analyzer.analyze_liquidity_risk(
            portfolio_positions = portfolio_positions, market_data = market_data
        )

        print(f"SUCCESS: Liquidity risk analysis completed")
        print(
            f"  Overall Liquidity Risk: {liquidity_results.overall_liquidity_risk:.1f}/100"
        )
        print(
            f"  Market Liquidity Risk: {liquidity_results.market_liquidity_risk:.1f}/100"
        )
        print(
            f"  Funding Liquidity Risk: {liquidity_results.funding_liquidity_risk:.1f}/100"
        )
        print(
            f"  Liquidity Coverage Ratio: {liquidity_results.liquidity_coverage_ratio:.2f}"
        )
        print(
            f"  Net Stable Funding Ratio: {liquidity_results.net_stable_funding_ratio:.2f}"
        )
        print(f"  Risk Level: {liquidity_results.risk_level.value}")

        return True

    except Exception as e:
        print(f"FAILED: Liquidity Risk Analyzer test failed: {e}")
        return False


def main():
    """Main test function"""
    print("Starting Advanced Risk Analytics Testing")
    print("=" * 50)

    # Generate test data
    returns, portfolio_positions = generate_test_data()

    # Test individual components
    var_ok = test_monte_carlo_var(returns, portfolio_positions)
    stress_ok = test_stress_test_engine(returns, portfolio_positions)
    liquidity_ok = test_liquidity_risk_analyzer(portfolio_positions)

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    tests = [
        ("Monte Carlo VaR Calculator", var_ok),
        ("Stress Test Engine", stress_ok),
        ("Liquidity Risk Analyzer", liquidity_ok),
    ]

    passed = 0
    total = len(tests)

    for test_name, result in tests:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1

    print(f"\nOverall Result: {passed}/{total} tests passed ({passed / total:.1%})")

    if passed == total:
        print(
            "\nAll tests passed! Advanced Risk Analytics system is working correctly."
        )
    else:
        print(f"\n{total - passed} test(s) failed. Please check the implementation.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

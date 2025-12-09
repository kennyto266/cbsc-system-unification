#!/usr / bin / env python3
"""
Advanced Risk Analytics Demo (Simple Version)
進階風險分析演示（簡化版）

Demonstration of the comprehensive risk analysis system
綜合風險分析系統演示
"""

import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def main():
    """Main demonstration function"""
    print("=" * 70)
    print("ADVANCED RISK ANALYTICS DEMONSTRATION")
    print("進階風險分析系統演示")
    print("=" * 70)

    # Generate realistic test data
    print("\nGenerating realistic portfolio data...")
    np.random.seed(123)  # For reproducible results

    # Create 1 year of daily returns with realistic market characteristics
    dates = pd.date_range(end = datetime.now(), periods = 252, freq="D")

    # Generate returns with market - like characteristics
    market_return = 0.0008  # 0.08% daily (about 20% annual)
    market_volatility = 0.015  # 1.5% daily volatility

    # Add some autocorrelation and fat tails
    returns = []
    for i in range(252):
        # Base market return
        daily_return = market_return + np.random.normal(0, market_volatility)

        # Add occasional extreme events
        if np.random.random() < 0.02:  # 2% chance of extreme event
            daily_return *= np.random.uniform(-4, -1)  # Extreme negative
        elif np.random.random() < 0.02:  # 2% chance of positive extreme
            daily_return *= np.random.uniform(1, 3)

        returns.append(daily_return)

    returns = pd.Series(returns, index = dates, name="portfolio_returns")

    # Create diversified portfolio
    portfolio_positions = pd.DataFrame(
        [
            {
                "asset": "AAPL",
                "asset_type": "equity",
                "market_value": 800000,
                "weight": 0.267,
                "sector": "Technology",
            },
            {
                "asset": "MSFT",
                "asset_type": "equity",
                "market_value": 600000,
                "weight": 0.200,
                "sector": "Technology",
            },
            {
                "asset": "NVDA",
                "asset_type": "equity",
                "market_value": 400000,
                "weight": 0.133,
                "sector": "Technology",
            },
            {
                "asset": "JPM",
                "asset_type": "equity",
                "market_value": 300000,
                "weight": 0.100,
                "sector": "Financial",
            },
            {
                "asset": "BRK.B",
                "asset_type": "equity",
                "market_value": 250000,
                "weight": 0.083,
                "sector": "Financial",
            },
            {
                "asset": "US_Treasury_10Y",
                "asset_type": "government_bond",
                "market_value": 400000,
                "weight": 0.133,
                "sector": "Fixed Income",
            },
            {
                "asset": "Gold",
                "asset_type": "commodity",
                "market_value": 150000,
                "weight": 0.050,
                "sector": "Commodities",
            },
            {
                "asset": "REIT_Index",
                "asset_type": "real_estate",
                "market_value": 100000,
                "weight": 0.033,
                "sector": "Real Estate",
            },
        ]
    )

    portfolio_value = portfolio_positions["market_value"].sum()
    print(f"[SUCCESS] Generated {len(returns)} trading days of data")
    print(f"[SUCCESS] Portfolio Value: ${portfolio_value:,.2f}")
    print(
        f"[SUCCESS] Portfolio Composition: {len(portfolio_positions)} assets across {len(portfolio_positions['sector'].unique())} sectors"
    )

    # DEMONSTRATION 1: Monte Carlo VaR Analysis
    print("\n" + "=" * 70)
    print("DEMO 1: MONTE CARLO VALUE AT RISK ANALYSIS")
    print("演示 1: 蒙特卡羅風險價值分析")
    print("=" * 70)

    try:
        from risk.monte_carlo_var import (
            DistributionType,
            MonteCarloVaRCalculator,
            VaRConfig,
        )

        # Comprehensive VaR analysis with multiple scenarios
        config = VaRConfig(
            confidence_levels=[0.90, 0.95, 0.99],
            time_horizons=[1, 5, 22],  # 1 day, 1 week, 1 month
            num_simulations = 5000,
            distribution_type = DistributionType.STUDENT_T,
            variance_reduction = None,
        )

        calculator = MonteCarloVaRCalculator(config)
        results = calculator.calculate_var(returns, portfolio_value)

        print(f"\nMonte Carlo VaR Results:")
        print(f"   Portfolio Value: ${portfolio_value:,.2f}")
        print(f"   Simulations Run: {len(results.simulated_returns):,}")
        print(f"   Distribution: {results.distribution_params['type']}")
        print(f"   Computational Time: {results.computational_time:.2f} seconds")

        print(f"\nVaR and Expected Shortfall Analysis:")
        for confidence, horizon_results in results.var_results.items():
            for horizon, var_result in horizon_results.items():
                horizon_str = "1 - Day" if horizon == 1 else f"{horizon}-Day"
                print(
                    f"   {int(confidence * 100)}% VaR ({horizon_str}): ${var_result.var_value:,.2f} ({var_result.var_percentage:.2%})"
                )
                print(
                    f"   {int(confidence * 100)}% Expected Shortfall ({horizon_str}): ${var_result.expected_shortfall:,.2f} ({var_result.expected_shortfall_percentage:.2%})"
                )

        # Show distribution fitting results
        print(f"\nDistribution Fitting Results:")
        if results.distribution_params["type"] == "student_t":
            print(
                f"   Student - t Degrees of Freedom: {results.distribution_params['df']:.2f}"
            )
            print(f"   Location Parameter: {results.distribution_params['mu']:.6f}")
            print(f"   Scale Parameter: {results.distribution_params['sigma']:.6f}")

    except Exception as e:
        print(f"[ERROR] Monte Carlo VaR demo failed: {e}")

    # DEMONSTRATION 2: Stress Testing Analysis
    print("\n" + "=" * 70)
    print("DEMO 2: STRESS TESTING ANALYSIS")
    print("演示 2: 壓力測試分析")
    print("=" * 70)

    try:
        from risk.stress_test_engine import StressTestEngine

        engine = StressTestEngine()

        portfolio_data = {
            "current_value": portfolio_value,
            "returns": returns,
            "positions": portfolio_positions,
            "portfolio_id": "demo_portfolio",
        }

        stress_report = engine.run_stress_tests(
            portfolio_data,
            scenario_ids=[
                "2008_financial_crisis",
                "2020_covid_crash",
                "interest_rate_shock",
            ],
        )

        print(f"\nStress Testing Results:")
        print(f"   Portfolio Value Under Normal Conditions: ${portfolio_value:,.2f}")
        print(f"   Worst Case Scenario: {stress_report.worst_case_scenario}")
        print(f"   Worst Case Loss: ${stress_report.worst_case_loss:,.2f}")
        print(
            f"   Worst Case Loss Percentage: {stress_report.worst_case_loss_percentage:.2%}"
        )
        print(
            f"   Portfolio Resilience Score: {stress_report.portfolio_resilience_score:.1f}/100"
        )

        print(f"\nScenario Analysis:")
        for result in stress_report.detailed_results:
            print(f"   {result.scenario_name}:")
            print(
                f"     Portfolio Loss: ${result.portfolio_loss:,.2f} ({result.portfolio_loss_percentage:.2%})"
            )
            print(f"     Maximum Drawdown: {result.max_drawdown:.2%}")
            print(f"     Recovery Time: {result.recovery_time_days} days")

        print(f"\nRisk Insights:")
        print(f"   Average Loss Across Scenarios: ${stress_report.average_loss:,.2f}")
        print(f"   Median Loss: ${stress_report.median_loss:,.2f}")
        print(f"   Stress VaR (95%): {stress_report.stress_var:.2%}")

    except Exception as e:
        print(f"[ERROR] Stress testing demo failed: {e}")

    # DEMONSTRATION 3: Liquidity Risk Analysis
    print("\n" + "=" * 70)
    print("DEMO 3: LIQUIDITY RISK ANALYSIS")
    print("演示 3: 流動性風險分析")
    print("=" * 70)

    try:
        from risk.liquidity_risk import LiquidityRiskAnalyzer

        # Create realistic market data
        market_data = {}
        for _, position in portfolio_positions.iterrows():
            asset = position["asset"]
            asset_type = position["asset_type"].lower()

            # Generate different market characteristics based on asset type
            dates = pd.date_range(end = datetime.now(), periods = 100, freq="D")

            if "equity" in asset_type:
                base_price = np.random.uniform(50, 300)
                base_volume = np.random.uniform(500000, 5000000)
                spread_factor = 0.005
            elif "bond" in asset_type:
                base_price = np.random.uniform(95, 105)
                base_volume = np.random.uniform(1000000, 10000000)
                spread_factor = 0.01
            elif "commodity" in asset_type:
                base_price = np.random.uniform(1800, 2200)
                base_volume = np.random.uniform(100000, 1000000)
                spread_factor = 0.015
            else:
                base_price = np.random.uniform(100, 200)
                base_volume = np.random.uniform(200000, 2000000)
                spread_factor = 0.008

            prices = pd.Series(
                base_price * np.cumprod(1 + np.random.normal(0, 0.02, 100)), index = dates
            )
            volumes = pd.Series(
                np.abs(np.random.normal(base_volume, base_volume * 0.3, 100)),
                index = dates,
            )

            bid_prices = prices * (1 - spread_factor / 2)
            ask_prices = prices * (1 + spread_factor / 2)

            market_data[asset] = pd.DataFrame(
                {
                    "close": prices,
                    "volume": volumes,
                    "bid": bid_prices,
                    "ask": ask_prices,
                }
            )

        analyzer = LiquidityRiskAnalyzer()
        liquidity_results = analyzer.analyze_liquidity_risk(
            portfolio_positions = portfolio_positions, market_data = market_data
        )

        print(f"\nLiquidity Risk Assessment:")
        print(
            f"   Overall Liquidity Risk Score: {liquidity_results.overall_liquidity_risk:.1f}/100"
        )
        print(
            f"   Market Liquidity Risk: {liquidity_results.market_liquidity_risk:.1f}/100"
        )
        print(
            f"   Funding Liquidity Risk: {liquidity_results.funding_liquidity_risk:.1f}/100"
        )
        print(f"   Risk Level: {liquidity_results.risk_level.value}")

        print(f"\nRegulatory Ratios:")
        print(
            f"   Liquidity Coverage Ratio (LCR): {liquidity_results.liquidity_coverage_ratio:.2f}"
        )
        print(
            f"   Net Stable Funding Ratio (NSFR): {liquidity_results.net_stable_funding_ratio:.2f}"
        )
        print(
            f"   Liquidity - Adjusted VaR: ${liquidity_results.liquidity_adjusted_var:,.2f}"
        )

        print(f"\nEarly Warning Indicators:")
        if liquidity_results.early_warning_indicators:
            for indicator in liquidity_results.early_warning_indicators:
                print(f"   - {indicator}")
        else:
            print("   No early warning indicators triggered")

    except Exception as e:
        print(f"[ERROR] Liquidity risk demo failed: {e}")

    # DEMONSTRATION 4: Risk Dashboard Summary
    print("\n" + "=" * 70)
    print("DEMO 4: COMPREHENSIVE RISK SUMMARY")
    print("演示 4: 綜合風險摘要")
    print("=" * 70)

    try:
        # Calculate basic portfolio statistics
        annual_return = returns.mean() * 252
        annual_volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
        max_drawdown = (returns.cumsum() - returns.cumsum().cummax()).min()

        print(f"\nPortfolio Performance Metrics:")
        print(f"   Annual Return: {annual_return:.2%}")
        print(f"   Annual Volatility: {annual_volatility:.2%}")
        print(f"   Sharpe Ratio: {sharpe_ratio:.3f}")
        print(f"   Maximum Drawdown: {max_drawdown:.2%}")
        print(f"   Best Day: {returns.max():.2%}")
        print(f"   Worst Day: {returns.min():.2%}")

        print(f"\nRisk Assessment Summary:")
        print(f"   Portfolio Value: ${portfolio_value:,.2f}")
        print(f"   Number of Positions: {len(portfolio_positions)}")
        print(
            f"   Sector Diversification: {len(portfolio_positions['sector'].unique())} sectors"
        )
        print(
            f"   Largest Position: {portfolio_positions['market_value'].max():,.2f} ({portfolio_positions.loc[portfolio_positions['market_value'].idxmax(), 'asset']})"
        )
        print(
            f"   Portfolio Concentration: {(portfolio_positions['market_value'] / portfolio_value).max():.2%}"
        )

        # Sector allocation
        print(f"\nSector Allocation:")
        sector_allocation = portfolio_positions.groupby("sector")["market_value"].sum()
        for sector, value in sector_allocation.items():
            percentage = value / portfolio_value
            print(f"   {sector}: ${value:,.2f} ({percentage:.1%})")

        print(f"\nKey Risk Management Insights:")
        print(
            f"   1. VaR analysis provides quantitative risk estimates at multiple confidence levels"
        )
        print(
            f"   2. Stress testing evaluates portfolio resilience under extreme market conditions"
        )
        print(
            f"   3. Liquidity analysis ensures ability to meet obligations and market trading needs"
        )
        print(f"   4. Multi - factor approach provides comprehensive risk coverage")
        print(f"   5. Regular monitoring enables proactive risk management")

    except Exception as e:
        print(f"[ERROR] Risk summary demo failed: {e}")

    print("\n" + "=" * 70)
    print("ADVANCED RISK ANALYTICS DEMO COMPLETED")
    print("進階風險分析系統演示完成")
    print("=" * 70)
    print("This institutional - grade risk analytics system provides:")
    print("   - Monte Carlo Value at Risk with multiple distributions")
    print("   - Comprehensive stress testing with historical scenarios")
    print("   - Advanced liquidity risk analysis with regulatory ratios")
    print("   - Real - time risk monitoring and early warning indicators")
    print("   - Risk decomposition and concentration analysis")
    print("   - Regulatory compliance reporting")
    print(
        "\nFor production deployment and customization, please contact the development team."
    )


if __name__ == "__main__":
    main()

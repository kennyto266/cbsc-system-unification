#!/usr/bin/env python3
"""
Advanced Risk Analytics Test Script
進階風險分析測試腳本

Testing the comprehensive risk analysis system
測試綜合風險分析系統
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from risk import (
        AdvancedRiskAnalyzer,
        StressTestEngine,
        MonteCarloVaRCalculator,
        LiquidityRiskAnalyzer,
        comprehensive_risk_analysis,
        quick_stress_test,
        quick_var_calculation,
        quick_liquidity_assessment
    )
    print("✅ Successfully imported all risk analysis modules")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def generate_test_data():
    """生成測試數據"""
    print("\n📊 Generating test data...")

    # Generate sample returns data (2 years of daily data)
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=504, freq='D')  # 2 years
    returns = pd.Series(
        np.random.normal(0.0005, 0.02, 504),  # 0.05% daily return, 2% volatility
        index=dates,
        name='portfolio_returns'
    )

    # Add some fat tails and skewness
    extreme_events = np.random.choice(returns.index, size=5, replace=False)
    returns.loc[extreme_events] *= np.random.uniform(-3, -1, 5)  # Extreme negative events

    # Generate portfolio positions
    portfolio_positions = pd.DataFrame([
        {'asset': 'AAPL', 'asset_type': 'equity', 'market_value': 200000, 'weight': 0.20, 'sector': 'Technology'},
        {'asset': 'MSFT', 'asset_type': 'equity', 'market_value': 150000, 'weight': 0.15, 'sector': 'Technology'},
        {'asset': 'GOOGL', 'asset_type': 'equity', 'market_value': 100000, 'weight': 0.10, 'sector': 'Technology'},
        {'asset': 'JPM', 'asset_type': 'equity', 'market_value': 120000, 'weight': 0.12, 'sector': 'Financial'},
        {'asset': 'BAC', 'asset_type': 'equity', 'market_value': 80000, 'weight': 0.08, 'sector': 'Financial'},
        {'asset': 'US_Treasury', 'asset_type': 'government_bond', 'market_value': 200000, 'weight': 0.20, 'sector': 'Fixed Income'},
        {'asset': 'Corporate_Bond', 'asset_type': 'corporate_bond', 'market_value': 100000, 'weight': 0.10, 'sector': 'Fixed Income'},
        {'asset': 'Gold', 'asset_type': 'commodity', 'market_value': 50000, 'weight': 0.05, 'sector': 'Commodities'}
    ])

    # Generate market data
    market_data = {}
    for asset in portfolio_positions['asset']:
        # Simulate price and volume data
        base_price = np.random.uniform(50, 500)
        prices = pd.Series(
            base_price * np.cumprod(1 + np.random.normal(0, 0.02, 504)),
            index=dates,
            name='close'
        )
        volumes = pd.Series(
            np.random.exponential(1000000, 504),
            index=dates,
            name='volume'
        )

        # Bid-ask spreads based on asset type
        if 'bond' in asset:
            spread_factor = 0.01
        elif asset == 'Gold':
            spread_factor = 0.015
        else:
            spread_factor = 0.005

        bid_prices = prices * (1 - spread_factor / 2)
        ask_prices = prices * (1 + spread_factor / 2)

        market_data[asset] = pd.DataFrame({
            'close': prices,
            'volume': volumes,
            'bid': bid_prices,
            'ask': ask_prices
        })

    # Generate funding data
    funding_data = {
        'funding_sources': [
            {
                'name': 'Bank_Line_A',
                'amount': 300000,
                'cost': 0.025,  # 2.5%
                'maturity_profile': {'1M': 100000, '3M': 100000, '6M': 100000},
                'collateral_ratio': 1.0,
                'renewal_probability': 0.9,
                'concentration': 0.3,
                'rollover_risk': 0.1
            },
            {
                'name': 'Commercial_Paper',
                'amount': 200000,
                'cost': 0.02,  # 2%
                'maturity_profile': {'1D': 50000, '1W': 50000, '1M': 100000},
                'collateral_ratio': 1.0,
                'renewal_probability': 0.8,
                'concentration': 0.2,
                'rollover_risk': 0.2
            },
            {
                'name': 'Long_Term_Debt',
                'amount': 500000,
                'cost': 0.04,  # 4%
                'maturity_profile': {'1Y': 200000, '5Y': 300000},
                'collateral_ratio': 1.0,
                'renewal_probability': 1.0,
                'concentration': 0.5,
                'rollover_risk': 0.05
            }
        ]
    }

    print(f"✅ Generated {len(returns)} days of returns data")
    print(f"✅ Generated portfolio with {len(portfolio_positions)} positions")
    print(f"✅ Generated market data for {len(market_data)} assets")
    print(f"✅ Generated funding data with {len(funding_data['funding_sources'])} sources")

    return returns, portfolio_positions, market_data, funding_data

def test_advanced_risk_analyzer(returns, portfolio_positions, market_data, funding_data):
    """測試高級風險分析器"""
    print("\n🔬 Testing Advanced Risk Analyzer...")

    try:
        analyzer = AdvancedRiskAnalyzer()

        # Run comprehensive risk analysis
        risk_results = analyzer.analyze_comprehensive_risk(
            returns=returns,
            portfolio_positions=portfolio_positions,
            market_data=market_data
        )

        print(f"✅ Overall Risk Level: {risk_results['overall_risk_level']}")
        print(f"✅ Sharpe Ratio: {risk_results['basic_risk_metrics']['sharpe_variants']['sharpe_ratio']:.3f}")
        print(f"✅ Max Drawdown: {risk_results['basic_risk_metrics']['drawdown_metrics']['max_drawdown']:.2%}")
        print(f"✅ VaR 95%: {risk_results['basic_risk_metrics']['var_metrics']['var_95']:.2%}")
        print(f"✅ Number of Risk Alerts: {len(risk_results['risk_alerts'])}")
        print(f"✅ Concentration Score: {risk_results['concentration_risk']['concentration_score']:.2f}")
        print(f"✅ Liquidity Score: {risk_results['liquidity_risk']['liquidity_score']:.2f}")

        # Generate dashboard data
        dashboard_data = analyzer.generate_risk_dashboard_data(risk_results)
        print(f"✅ Generated dashboard data with {len(dashboard_data)} sections")

        return risk_results

    except Exception as e:
        print(f"❌ Advanced Risk Analyzer test failed: {e}")
        return None

def test_stress_test_engine(returns, portfolio_positions, market_data, funding_data):
    """測試壓力測試引擎"""
    print("\n🌪️ Testing Stress Test Engine...")

    try:
        engine = StressTestEngine()

        # Prepare portfolio data for stress testing
        portfolio_data = {
            'current_value': portfolio_positions['market_value'].sum(),
            'returns': returns,
            'positions': portfolio_positions,
            'portfolio_id': 'test_portfolio'
        }

        # Run stress tests
        stress_report = engine.run_stress_tests(portfolio_data)

        print(f"✅ Worst Case Scenario: {stress_report.worst_case_scenario}")
        print(f"✅ Worst Case Loss: {stress_report.worst_case_loss:,.2f}")
        print(f"✅ Worst Case Loss %: {stress_report.worst_case_loss_percentage:.2%}")
        print(f"✅ Portfolio Resilience Score: {stress_report.portfolio_resilience_score:.1f}/100")
        print(f"✅ Number of Scenarios Tested: {len(stress_report.scenarios_tested)}")
        print(f"✅ Number of Recommendations: {len(stress_report.recommendations)}")

        # Test Monte Carlo stress testing
        mc_stress_results = engine.run_monte_carlo_stress_test(portfolio_data)
        print(f"✅ Monte Carlo VaR: {mc_stress_results['monte_carlo_var']:.2%}")
        print(f"✅ Worst Case Loss (MC): {mc_stress_results['worst_case_loss']:.2%}")

        return stress_report

    except Exception as e:
        print(f"❌ Stress Test Engine test failed: {e}")
        return None

def test_monte_carlo_var(returns, portfolio_positions):
    """測試蒙特卡羅VaR計算器"""
    print("\n🎲 Testing Monte Carlo VaR Calculator...")

    try:
        from risk.monte_carlo_var import VaRConfig, DistributionType

        # Configure VaR calculation
        config = VaRConfig(
            confidence_levels=[0.90, 0.95, 0.99],
            time_horizons=[1, 5, 10, 22],
            num_simulations=5000,  # Reduced for testing
            distribution_type=DistributionType.STUDENT_T,
            variance_reduction=None
        )

        calculator = MonteCarloVaRCalculator(config)

        # Calculate VaR
        portfolio_value = portfolio_positions['market_value'].sum()
        mc_results = calculator.calculate_var(returns, portfolio_value)

        print(f"✅ Simulations completed: {mc_results.sample_size}")
        print(f"✅ Computational time: {mc_results.computational_time:.2f} seconds")
        print(f"✅ Distribution type: {mc_results.distribution_params['type']}")

        # Display some key results
        for confidence, horizon_results in mc_results.var_results.items():
            for horizon, var_result in horizon_results.items():
                print(f"✅ VaR {int(confidence*100)}% ({horizon}d): {var_result.var_value:,.2f} ({var_result.var_percentage:.2%})")

        return mc_results

    except Exception as e:
        print(f"❌ Monte Carlo VaR test failed: {e}")
        return None

def test_liquidity_risk_analyzer(portfolio_positions, market_data, funding_data):
    """測試流動性風險分析器"""
    print("\n💧 Testing Liquidity Risk Analyzer...")

    try:
        analyzer = LiquidityRiskAnalyzer()

        # Analyze liquidity risk
        liquidity_results = analyzer.analyze_liquidity_risk(
            portfolio_positions=portfolio_positions,
            market_data=market_data,
            funding_data=funding_data
        )

        print(f"✅ Overall Liquidity Risk: {liquidity_results.overall_liquidity_risk:.1f}/100")
        print(f"✅ Market Liquidity Risk: {liquidity_results.market_liquidity_risk:.1f}/100")
        print(f"✅ Funding Liquidity Risk: {liquidity_results.funding_liquidity_risk:.1f}/100")
        print(f"✅ Liquidity Coverage Ratio: {liquidity_results.liquidity_coverage_ratio:.2f}")
        print(f"✅ Net Stable Funding Ratio: {liquidity_results.net_stable_funding_ratio:.2f}")
        print(f"✅ Liquidity-Adjusted VaR: {liquidity_results.liquidity_adjusted_var:,.2f}")
        print(f"✅ Risk Level: {liquidity_results.risk_level.value}")
        print(f"✅ Early Warning Indicators: {len(liquidity_results.early_warning_indicators)}")

        # Test liquidity stress testing
        stress_results = analyzer.run_liquidity_stress_test(
            portfolio_positions, market_data, funding_data
        )
        print(f"✅ Liquidity Stress Scenarios: {len(stress_results)}")
        for scenario in stress_results:
            print(f"  - {scenario.scenario_name}: Funding Gap {scenario.funding_gap:,.2f}")

        return liquidity_results

    except Exception as e:
        print(f"❌ Liquidity Risk Analyzer test failed: {e}")
        return None

def test_quick_functions(returns, portfolio_positions, market_data):
    """測試便利函數"""
    print("\n⚡ Testing Quick Functions...")

    try:
        # Quick stress test
        portfolio_value = portfolio_positions['market_value'].sum()
        quick_stress = quick_stress_test(portfolio_value, returns)
        print(f"✅ Quick Stress Test: Worst case {quick_stress['worst_case_loss_percentage']:.2%}")

        # Quick VaR calculation
        quick_var = quick_var_calculation(returns, portfolio_value)
        print(f"✅ Quick VaR 95%: {quick_var['var_value']:,.2f} ({quick_var['var_percentage']:.2%})")
        print(f"✅ Quick Expected Shortfall: {quick_var['expected_shortfall']:,.2f}")

        # Quick liquidity assessment
        bid_ask_spreads = {asset: 0.01 for asset in portfolio_positions['asset']}
        daily_volumes = {asset: 1000000 for asset in portfolio_positions['asset']}
        quick_liquidity = quick_liquidity_assessment(portfolio_value, bid_ask_spreads, daily_volumes)
        print(f"✅ Quick Liquidity Risk: {quick_liquidity['overall_liquidity_risk']:.1f}/100")
        print(f"✅ Quick LCR: {quick_liquidity['liquidity_coverage_ratio']:.2f}")

        return True

    except Exception as e:
        print(f"❌ Quick functions test failed: {e}")
        return False

def test_comprehensive_analysis(returns, portfolio_positions, market_data, funding_data):
    """測試綜合風險分析"""
    print("\n📈 Testing Comprehensive Risk Analysis...")

    try:
        # Run comprehensive analysis
        comprehensive_results = comprehensive_risk_analysis(
            returns_data=returns,
            portfolio_positions=portfolio_positions,
            market_data=market_data,
            funding_data=funding_data
        )

        print(f"✅ Analysis completed with {len(comprehensive_results['risk_modules_completed'])} modules")
        print(f"✅ Overall Risk Assessment: {comprehensive_results['summary']['overall_risk_assessment']['risk_level']}")
        print(f"✅ Overall Risk Score: {comprehensive_results['summary']['overall_risk_assessment']['overall_score']:.1f}/100")
        print(f"✅ Confidence: {comprehensive_results['summary']['overall_risk_assessment']['confidence']:.1%}")

        # Display module results summary
        if 'basic_risk_metrics' in comprehensive_results:
            sharpe = comprehensive_results['basic_risk_metrics']['sharpe_variants']['sharpe_ratio']
            print(f"✅ Basic Risk Metrics: Sharpe = {sharpe:.3f}")

        if 'advanced_risk_analysis' in comprehensive_results:
            risk_level = comprehensive_results['advanced_risk_analysis']['overall_risk_level']
            print(f"✅ Advanced Risk Analysis: Risk Level = {risk_level}")

        if 'stress_test_results' in comprehensive_results:
            worst_loss = comprehensive_results['stress_test_results']['worst_case_loss_percentage']
            print(f"✅ Stress Test: Worst Loss = {worst_loss:.2%}")

        return comprehensive_results

    except Exception as e:
        print(f"❌ Comprehensive analysis test failed: {e}")
        return None

def main():
    """主測試函數"""
    print("🚀 Starting Advanced Risk Analytics Testing")
    print("=" * 60)

    # Generate test data
    returns, portfolio_positions, market_data, funding_data = generate_test_data()

    # Test individual components
    risk_results = test_advanced_risk_analyzer(returns, portfolio_positions, market_data, funding_data)
    stress_results = test_stress_test_engine(returns, portfolio_positions, market_data, funding_data)
    var_results = test_monte_carlo_var(returns, portfolio_positions)
    liquidity_results = test_liquidity_risk_analyzer(portfolio_positions, market_data, funding_data)
    quick_functions_ok = test_quick_functions(returns, portfolio_positions, market_data)
    comprehensive_results = test_comprehensive_analysis(returns, portfolio_positions, market_data, funding_data)

    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)

    tests = [
        ("Advanced Risk Analyzer", risk_results is not None),
        ("Stress Test Engine", stress_results is not None),
        ("Monte Carlo VaR Calculator", var_results is not None),
        ("Liquidity Risk Analyzer", liquidity_results is not None),
        ("Quick Functions", quick_functions_ok),
        ("Comprehensive Analysis", comprehensive_results is not None)
    ]

    passed = 0
    total = len(tests)

    for test_name, result in tests:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1

    print(f"\nOverall Result: {passed}/{total} tests passed ({passed/total:.1%})")

    if passed == total:
        print("\n🎉 All tests passed! Advanced Risk Analytics system is working correctly.")
        print("🏆 System is ready for production use.")
    else:
        print(f"\n⚠️ {total-passed} test(s) failed. Please check the implementation.")
        print("🔧 Some components may need debugging or fixes.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
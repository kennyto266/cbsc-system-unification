#!/usr / bin / env python3
"""
Test Phase 3: Risk Management Integration
Comprehensive testing of professional risk metrics, portfolio management,
and risk management framework implementation.
"""

import json
import logging
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

# Add current directory to path
sys.path.append(os.getcwd())

from src.api.stock_api import get_hk_stock_data
from src.backtest.advanced_portfolio_manager import (
    DynamicPositionSizer,
    MultiAssetPortfolioBacktester,
    PortfolioOptimizer,
    create_multi_asset_test_data,
)
from src.backtest.professional_risk_metrics import RiskCalculator, RiskMetrics
from src.backtest.risk_management_framework import (
    AlertType,
    IntegratedRiskManager,
    RiskBudget,
    RiskLevel,
    create_default_risk_budget,
)

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)


def load_test_data() -> pd.DataFrame:
    """Load real market data for testing"""
    logger.info("Loading test data...")

    try:
        # Load real 0700.HK data
        data = get_hk_stock_data("0700.HK", 252)

        # Convert to DataFrame with proper format
        if isinstance(data, list):
            df = pd.DataFrame(data)
            if "timestamp" in df.columns:
                df["date"] = pd.to_datetime(df["timestamp"])
                df.set_index("date", inplace = True)

            # Ensure we have a 'close' column for price
            if "close" not in df.columns:
                df["close"] = df.get("price", 100)

            return df[["close"]]

        return data

    except Exception as e:
        logger.error(f"Failed to load real data: {e}")
        logger.warning("Using synthetic data for testing...")

        # Generate synthetic data
        dates = pd.date_range("2022 - 01 - 01", periods = 252, freq="D")
        np.random.seed(42)
        prices = 500 + np.cumsum(np.random.normal(0.001, 0.02, 252))

        return pd.DataFrame({"close": prices}, index = dates)


def test_professional_risk_metrics():
    """Test Phase 3.1: Professional Risk Metrics Implementation"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING Phase 3.1: Professional Risk Metrics")
    logger.info("=" * 60)

    # Load test data
    price_data = load_test_data()
    prices = price_data["close"]

    # Initialize risk calculator
    risk_calculator = RiskCalculator(risk_free_rate = 0.03)

    try:
        # Calculate comprehensive risk metrics
        risk_metrics = risk_calculator.calculate_comprehensive_metrics(prices)

        # Verify key metrics
        assert isinstance(risk_metrics, RiskMetrics), "Should return RiskMetrics object"
        assert risk_metrics.total_return != 0, "Total return should not be zero"
        assert risk_metrics.volatility >= 0, "Volatility should be non - negative"
        assert not np.isnan(risk_metrics.sharpe_ratio), "Sharpe ratio should not be NaN"

        # Test VaR calculations
        returns = risk_calculator.calculate_returns(prices)
        var_95 = risk_calculator.calculate_var(returns, 0.95)
        cvar_95 = risk_calculator.calculate_cvar(returns, 0.95)

        assert var_95 < 0, "VaR should be negative"
        assert cvar_95 <= var_95, "CVaR should be less than or equal to VaR"

        logger.info(f"✓ Risk metrics calculated successfully:")
        logger.info(f"  Total Return: {risk_metrics.total_return:.2%}")
        logger.info(f"  Annualized Return: {risk_metrics.annualized_return:.2%}")
        logger.info(f"  Volatility: {risk_metrics.volatility:.2%}")
        logger.info(f"  Sharpe Ratio: {risk_metrics.sharpe_ratio:.3f}")
        logger.info(f"  Sortino Ratio: {risk_metrics.sortino_ratio:.3f}")
        logger.info(f"  Max Drawdown: {risk_metrics.max_drawdown:.2%}")
        logger.info(f"  VaR 95%: {risk_metrics.var_95:.3f}")
        logger.info(f"  CVaR 95%: {risk_metrics.cvar_95:.3f}")

        return True, risk_metrics

    except Exception as e:
        logger.error(f"Professional risk metrics test failed: {e}")
        return False, None


def test_portfolio_optimization():
    """Test Phase 3.2: Advanced Portfolio Management"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING Phase 3.2: Advanced Portfolio Management")
    logger.info("=" * 60)

    try:
        # Create multi - asset test data
        price_data = create_multi_asset_test_data()
        returns = price_data.pct_change().dropna()

        # Initialize portfolio optimizer
        optimizer = PortfolioOptimizer(risk_free_rate = 0.03)

        # Test efficient frontier calculation
        ef_returns, ef_volatilities, ef_weights = (
            optimizer.calculate_efficient_frontier(returns, num_portfolios = 20)
        )

        assert len(ef_returns) == 20, "Should generate 20 portfolios"
        assert len(ef_volatilities) == 20, "Should generate 20 volatility points"
        assert len(ef_weights) == 20, "Should generate 20 weight sets"

        # Test maximum Sharpe ratio optimization
        max_sharpe_portfolio = optimizer.maximize_sharpe_ratio(returns)

        assert max_sharpe_portfolio.sharpe_ratio > 0, "Sharpe ratio should be positive"
        assert (
            abs(sum(max_sharpe_portfolio.weights.values()) - 1.0) < 1e - 6
        ), "Weights should sum to 1"

        # Test minimum volatility optimization
        min_vol_portfolio = optimizer.minimize_volatility(returns)

        assert (
            min_vol_portfolio.expected_volatility >= 0
        ), "Volatility should be non - negative"
        assert (
            abs(sum(min_vol_portfolio.weights.values()) - 1.0) < 1e - 6
        ), "Weights should sum to 1"

        # Test dynamic position sizer
        position_sizer = DynamicPositionSizer(
            portfolio_value = 1000000, max_position_size = 0.3
        )

        # Test volatility - adjusted weights
        vol_adj_weights = position_sizer.calculate_volatility_adjusted_weights(returns)

        assert len(vol_adj_weights) == len(
            returns.columns
        ), "Should return weight for each asset"
        assert (
            abs(sum(vol_adj_weights.values()) - 1.0) < 1e - 6
        ), "Weights should sum to 1"

        # Test risk parity weights
        risk_parity_weights = position_sizer.calculate_risk_parity_weights(returns)

        assert len(risk_parity_weights) == len(
            returns.columns
        ), "Should return weight for each asset"
        assert (
            abs(sum(risk_parity_weights.values()) - 1.0) < 1e - 6
        ), "Weights should sum to 1"

        logger.info(f"✓ Portfolio optimization successful:")
        logger.info(f"  Efficient Frontier: {len(ef_returns)} portfolios")
        logger.info(
            f"  Max Sharpe Portfolio: {max_sharpe_portfolio.sharpe_ratio:.3f} Sharpe"
        )
        logger.info(
            f"  Min Vol Portfolio: {min_vol_portfolio.expected_volatility:.2%} volatility"
        )
        logger.info(
            f"  Risk Parity Weights: {list(risk_parity_weights.values())[:3]}..."
        )

        return True, {
            "max_sharpe": max_sharpe_portfolio,
            "min_volatility": min_vol_portfolio,
            "risk_parity_weights": risk_parity_weights,
        }

    except Exception as e:
        logger.error(f"Portfolio optimization test failed: {e}")
        return False, None


def test_risk_management_framework():
    """Test Phase 3.3: Risk Management Framework"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING Phase 3.3: Risk Management Framework")
    logger.info("=" * 60)

    try:
        # Create test portfolio data
        dates = pd.date_range("2023 - 01 - 01", periods = 252, freq="D")
        np.random.seed(42)
        portfolio_returns = pd.Series(np.random.normal(0.0005, 0.015, 252), index = dates)

        # Initialize risk budget
        risk_budget = create_default_risk_budget()

        # Initialize integrated risk manager
        def test_alert_callback(alert):
            logger.info(f"Alert received: {alert.alert_type.value} - {alert.message}")

        risk_manager = IntegratedRiskManager(risk_budget, test_alert_callback)

        # Create test positions and prices
        positions = {"STOCK_A": 1000, "STOCK_B": 500, "BOND_A": 2000}
        current_prices = {"STOCK_A": 150, "STOCK_B": 80, "BOND_A": 100}
        portfolio_value = sum(
            pos * price
            for pos, price in zip(positions.values(), current_prices.values())
        )

        # Generate comprehensive risk report
        risk_report = risk_manager.generate_risk_report(
            portfolio_returns, positions, current_prices, portfolio_value
        )

        # Verify report structure
        assert "risk_metrics" in risk_report, "Report should contain risk metrics"
        assert "current_alerts" in risk_report, "Report should contain current alerts"
        assert (
            "stress_test_summary" in risk_report
        ), "Report should contain stress test summary"
        assert "recommendations" in risk_report, "Report should contain recommendations"

        # Test stress testing
        stress_results = risk_manager.stress_testing.run_stress_tests(portfolio_returns)

        assert len(stress_results) > 0, "Should generate stress test results"

        # Test risk monitoring
        alerts = risk_manager.risk_monitoring.monitor_portfolio_risk(
            portfolio_returns, portfolio_value, positions, current_prices
        )

        # Risk monitoring should complete without errors
        logger.info(f"Risk monitoring completed with {len(alerts)} alerts")

        # Test risk budgeting
        returns_matrix = pd.DataFrame(
            np.random.normal(0.001, 0.02, (252, 3)), columns=["A", "B", "C"]
        )
        risk_budget_weights = risk_manager.risk_budgeting.calculate_risk_budget_weights(
            returns_matrix
        )

        assert (
            abs(sum(risk_budget_weights.values()) - 1.0) < 1e - 6
        ), "Risk budget weights should sum to 1"

        logger.info(f"✓ Risk management framework successful:")
        logger.info(f"  Portfolio Value: ${portfolio_value:,.0f}")
        logger.info(f"  Risk Alerts Generated: {len(risk_report['current_alerts'])}")
        logger.info(f"  Stress Scenarios Tested: {len(stress_results)}")
        logger.info(f"  Risk Budget Weights: {len(risk_budget_weights)} assets")
        logger.info(f"  Recommendations: {len(risk_report['recommendations'])}")

        return True, risk_report

    except Exception as e:
        logger.error(f"Risk management framework test failed: {e}")
        return False, None


def test_multi_asset_backtesting():
    """Test multi - asset portfolio backtesting"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING Multi - Asset Portfolio Backtesting")
    logger.info("=" * 60)

    try:
        # Create test data
        price_data = create_multi_asset_test_data()

        # Initialize backtester
        backtester = MultiAssetPortfolioBacktester(
            initial_capital = 1000000,
            rebalance_frequency="monthly",
            transaction_costs = 0.001,
        )

        # Test different strategies
        strategies = ["max_sharpe", "min_volatility", "risk_parity"]
        results = {}

        for strategy in strategies:
            strategy_results = backtester.backtest_portfolio_strategy(
                price_data,
                strategy = strategy,
                lookback_window = 100,  # Smaller for testing
                rebalance_window = 20,
            )

            results[strategy] = strategy_results

            # Verify results
            assert strategy_results["final_value"] > 0, "Final value should be positive"
            assert (
                strategy_results["num_rebalances"] >= 0
            ), "Rebalance count should be non - negative"

        # Compare strategies
        best_strategy = max(results.keys(), key = lambda k: results[k]["total_return"])

        logger.info(f"✓ Multi - asset backtesting successful:")
        for strategy, result in results.items():
            logger.info(
                f"  {strategy}: {result['total_return']:.2%} return, "
                f"{result['num_rebalances']} rebalances"
            )

        logger.info(f"  Best strategy: {best_strategy}")

        return True, results

    except Exception as e:
        logger.error(f"Multi - asset backtesting test failed: {e}")
        return False, None


def run_comprehensive_phase3_test():
    """Run comprehensive Phase 3 test suite"""
    logger.info("Starting Comprehensive Phase 3 Risk Management Test...")

    test_results = {
        "test_time": datetime.now().isoformat(),
        "tests": {},
        "overall_status": "FAILED",
    }

    success_count = 0
    total_tests = 4

    try:
        # Test 1: Professional Risk Metrics
        success, risk_metrics = test_professional_risk_metrics()
        test_results["tests"]["professional_risk_metrics"] = {
            "status": "PASSED" if success else "FAILED",
            "success": success,
        }
        if success:
            success_count += 1

        # Test 2: Portfolio Optimization
        success, portfolio_results = test_portfolio_optimization()
        test_results["tests"]["portfolio_optimization"] = {
            "status": "PASSED" if success else "FAILED",
            "success": success,
        }
        if success:
            success_count += 1

        # Test 3: Risk Management Framework
        success, risk_management_results = test_risk_management_framework()
        test_results["tests"]["risk_management_framework"] = {
            "status": "PASSED" if success else "FAILED",
            "success": success,
        }
        if success:
            success_count += 1

        # Test 4: Multi - Asset Backtesting
        success, backtesting_results = test_multi_asset_backtesting()
        test_results["tests"]["multi_asset_backtesting"] = {
            "status": "PASSED" if success else "FAILED",
            "success": success,
        }
        if success:
            success_count += 1

        # Generate summary
        test_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": success_count,
            "success_rate": success_count / total_tests,
            "overall_status": "PASSED" if success_count == total_tests else "PARTIAL",
        }

        logger.info("\n" + "=" * 60)
        logger.info("PHASE 3 COMPREHENSIVE TEST SUMMARY")
        logger.info("=" * 60)

        for test_name, result in test_results["tests"].items():
            status = "PASSED" if result["success"] else "FAILED"
            logger.info(f"  {test_name}: {status}")

        logger.info(f"\nOverall: {success_count}/{total_tests} tests passed")
        logger.info(f"Success Rate: {success_count / total_tests:.1%}")

        if success_count == total_tests:
            logger.info("\n🎉 All Phase 3 Risk Management tests PASSED!")
        else:
            logger.info(f"\n⚠️ {total_tests - success_count} test(s) failed")

        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"phase3_risk_management_test_results_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(test_results, f, indent = 2, default = str)

        logger.info(f"Test results saved to: {filename}")

        return test_results

    except Exception as e:
        logger.error(f"Comprehensive Phase 3 test failed: {e}")
        test_results["error"] = str(e)
        return test_results


if __name__ == "__main__":
    # Run comprehensive Phase 3 test
    results = run_comprehensive_phase3_test()

    # Print final status
    if "summary" in results:
        if results["summary"]["overall_status"] == "PASSED":
            print(f"\n✅ Phase 3 Risk Management Integration: COMPLETE")
            print(
                f"📊 {results['summary']['passed_tests']}/{results['summary']['total_tests']} tests passed"
            )
        else:
            print(f"\n⚠️ Phase 3 Risk Management Integration: PARTIAL")
            print(
                f"📊 {results['summary']['passed_tests']}/{results['summary']['total_tests']} tests passed"
            )
    else:
        print("\n❌ Phase 3 Risk Management Integration: FAILED")

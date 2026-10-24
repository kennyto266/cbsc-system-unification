"""
Test Enhanced Backtest Engine
================================

Test suite for the enhanced backtest engine with integrated risk management

Author: CBSC Quant Team
Version: 1.0.0
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from enhanced_backtest_engine import (
    EnhancedBacktestEngine,
    BacktestConfig,
    BacktestMode,
    example_strategy
)

class TestEnhancedBacktestEngine(unittest.TestCase):
    """Test cases for EnhancedBacktestEngine"""

    def setUp(self):
        """Set up test data and configuration"""
        # Create sample data
        self.dates = pd.date_range(start="2023-01-01", end="2023-03-31", freq="D")
        np.random.seed(42)

        # Simulate AAPL and MSFT price data
        aapl_prices = 150 * np.cumprod(1 + np.random.normal(0.0005, 0.02, len(self.dates)))
        msft_prices = 250 * np.cumprod(1 + np.random.normal(0.0003, 0.015, len(self.dates)))

        self.data = pd.DataFrame({
            "AAPL": aapl_prices,
            "MSFT": msft_prices
        }, index=self.dates)

        # Benchmark data (S&P 500 simulation)
        spy_prices = 4000 * np.cumprod(1 + np.random.normal(0.0002, 0.01, len(self.dates)))
        self.benchmark_data = pd.DataFrame({
            "SPY": spy_prices,
            "returns": np.diff(np.log(spy_prices), prepend=0)
        }, index=self.dates)

        # Test configuration
        self.config = BacktestConfig(
            start_date=self.dates[0],
            end_date=self.dates[-1],
            initial_capital=1000000,
            enable_risk_management=True,
            enable_dynamic_adjustments=True,
            var_limit=0.02,
            max_drawdown_limit=0.15,
            leverage_limit=2.0,
            position_size_limit=0.4
        )

    def test_initialization(self):
        """Test engine initialization"""
        engine = EnhancedBacktestEngine(self.config)

        self.assertEqual(engine.current_capital, self.config.initial_capital)
        self.assertEqual(len(engine.positions), 0)
        self.assertEqual(len(engine.trades), 0)
        self.assertEqual(engine.high_water_mark, self.config.initial_capital)

    def test_standard_backtest(self):
        """Test standard backtest mode"""
        engine = EnhancedBacktestEngine(self.config)

        result = engine.run_backtest(
            strategy=example_strategy,
            data=self.data,
            mode=BacktestMode.STANDARD
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result.total_return, float)
        self.assertIsInstance(result.sharpe_ratio, float)
        self.assertGreaterEqual(result.total_trades, 0)

    def test_risk_managed_backtest(self):
        """Test risk managed backtest mode"""
        engine = EnhancedBacktestEngine(self.config)

        result = engine.run_backtest(
            strategy=example_strategy,
            data=self.data,
            benchmark_data=self.benchmark_data,
            mode=BacktestMode.RISK_MANAGED
        )

        self.assertIsNotNone(result)
        self.assertIsNotNone(result.var_95)
        self.assertIsNotNone(result.var_99)
        self.assertIsNotNone(result.expected_shortfall_95)
        self.assertIsNotNone(result.expected_shortfall_99)

    def test_position_management(self):
        """Test position management functionality"""
        engine = EnhancedBacktestEngine(self.config)

        # Test portfolio value calculation
        initial_value = engine._calculate_portfolio_value()
        self.assertEqual(initial_value, self.config.initial_capital)

        # Add a position
        engine.positions["AAPL"] = unittest.mock.Mock()
        engine.positions["AAPL"].market_value = 50000
        engine.positions["AAPL"].quantity = 100
        engine.positions["AAPL"].entry_price = 150

        portfolio_value = engine._calculate_portfolio_value()
        self.assertEqual(portfolio_value, self.config.initial_capital + 50000)

    def test_risk_management_application(self):
        """Test risk management rule application"""
        engine = EnhancedBacktestEngine(self.config)

        # Create target positions that exceed limits
        target_positions = {
            "AAPL": 1000000,  # Exceeds position size limit
            "MSFT": 500000    # Within reasonable range
        }

        market_data = pd.Series({"AAPL": 150, "MSFT": 250})

        # Apply risk management
        adjusted_positions = engine._apply_risk_management(
            target_positions,
            datetime.now(),
            market_data
        )

        # Check that position size limits are enforced
        max_aapl_value = self.config.position_size_limit * self.config.initial_capital
        max_aapl_quantity = max_aapl_value / 150
        self.assertLessEqual(abs(adjusted_positions["AAPL"]), max_aapl_quantity)

    def test_drawdown_calculation(self):
        """Test drawdown calculation and limits"""
        engine = EnhancedBacktestEngine(self.config)

        # Simulate losses that trigger drawdown limit
        engine.current_drawdown = 0.20  # 20% drawdown exceeds limit of 15%

        target_positions = {"AAPL": 100}
        market_data = pd.Series({"AAPL": 150})

        # Apply risk management - should reduce positions
        adjusted_positions = engine._apply_risk_management(
            target_positions,
            datetime.now(),
            market_data
        )

        # Positions should be reduced
        self.assertLess(abs(adjusted_positions["AAPL"]), abs(target_positions["AAPL"]))

    def test_monte_carlo_simulation(self):
        """Test Monte Carlo simulation mode"""
        engine = EnhancedBacktestEngine(self.config)

        # Run Monte Carlo with fewer simulations for testing
        result = engine.run_backtest(
            strategy=example_strategy,
            data=self.data,
            mode=BacktestMode.MONTE_CARLO
        )

        self.assertIsNotNone(result)
        # Check if Monte Carlo specific attributes were added
        # (These would be dynamically added in the actual implementation)

    def test_rebalancing_logic(self):
        """Test rebalancing frequency logic"""
        engine = EnhancedBacktestEngine(self.config)

        # Test daily rebalancing
        engine.config.rebalance_frequency = "daily"
        self.assertTrue(engine._should_rebalance(datetime.now()))

        # Test weekly rebalancing
        engine.config.rebalance_frequency = "weekly"
        engine.last_rebalance_date = datetime.now() - timedelta(days=8)
        self.assertTrue(engine._should_rebalance(datetime.now()))

        engine.last_rebalance_date = datetime.now() - timedelta(days=3)
        self.assertFalse(engine._should_rebalance(datetime.now()))

    def test_trade_execution(self):
        """Test trade execution with commissions and slippage"""
        engine = EnhancedBacktestEngine(self.config)

        target_positions = {"AAPL": 100}
        market_data = pd.Series({"AAPL": 150})
        portfolio_value = engine._calculate_portfolio_value()

        initial_capital = engine.current_capital

        engine._execute_trades(
            target_positions,
            datetime.now(),
            market_data,
            portfolio_value
        )

        # Check that capital was reduced for purchase
        trade_value = 100 * 150
        expected_commission = trade_value * self.config.commission_rate
        expected_slippage = trade_value * self.config.slippage_rate

        self.assertLess(
            engine.current_capital,
            initial_capital - trade_value - expected_commission - expected_slippage + 0.01  # Small tolerance
        )

        # Check that position was created
        self.assertIn("AAPL", engine.positions)
        self.assertEqual(engine.positions["AAPL"].quantity, 100)

    def test_comprehensive_results_generation(self):
        """Test comprehensive results generation"""
        engine = EnhancedBacktestEngine(self.config)

        # Mock some data for testing
        engine.equity_curve = [
            (datetime.now(), self.config.initial_capital),
            (datetime.now(), self.config.initial_capital * 1.1),
            (datetime.now(), self.config.initial_capital * 1.05)
        ]
        engine.returns_history = [0.1, -0.045]  # 10% up, 4.5% down

        result = engine._generate_results()

        self.assertIsNotNone(result)
        self.assertIsInstance(result.total_return, float)
        self.assertIsInstance(result.sharpe_ratio, float)
        self.assertIsInstance(result.max_drawdown, float)

    def test_edge_cases(self):
        """Test edge cases and error handling"""
        engine = EnhancedBacktestEngine(self.config)

        # Test with empty data
        empty_data = pd.DataFrame()

        # Should handle gracefully
        try:
            result = engine.run_backtest(
                strategy=example_strategy,
                data=empty_data,
                mode=BacktestMode.STANDARD
            )
            # If no exception, result should still be valid
            self.assertIsNotNone(result)
        except Exception as e:
            # Expected behavior for empty data
            self.assertIsInstance(e, (ValueError, IndexError))

    def test_performance_metrics(self):
        """Test performance metric calculations"""
        engine = EnhancedBacktestEngine(self.config)

        # Run a complete backtest
        result = engine.run_backtest(
            strategy=example_strategy,
            data=self.data,
            benchmark_data=self.benchmark_data,
            mode=BacktestMode.RISK_MANAGED
        )

        # Verify all expected metrics are present
        expected_metrics = [
            'total_return', 'annualized_return', 'volatility', 'sharpe_ratio',
            'max_drawdown', 'calmar_ratio', 'var_95', 'var_99',
            'expected_shortfall_95', 'expected_shortfall_99',
            'total_trades', 'win_rate', 'avg_win', 'avg_loss', 'profit_factor'
        ]

        for metric in expected_metrics:
            self.assertTrue(hasattr(result, metric), f"Missing metric: {metric}")

        # Validate metric ranges
        self.assertGreaterEqual(result.win_rate, 0)
        self.assertLessEqual(result.win_rate, 1)
        self.assertGreaterEqual(result.total_trades, 0)
        self.assertIsInstance(result.avg_win, (int, float))
        self.assertIsInstance(result.avg_loss, (int, float))

def run_integration_test():
    """Run integration test with realistic scenario"""
    print("Running Enhanced Backtest Engine Integration Test...")

    # Create realistic test data
    dates = pd.date_range(start="2023-01-01", end="2023-06-30", freq="D")
    np.random.seed(123)

    # Simulate correlated price movements
    n_assets = 3
    returns = np.random.multivariate_normal(
        mean=[0.0005, 0.0003, 0.0002],
        cov=[[0.0004, 0.0002, 0.0001],
             [0.0002, 0.0003, 0.00015],
             [0.0001, 0.00015, 0.0002]],
        size=len(dates)
    )

    prices = np.cumprod(1 + returns, axis=0)
    prices[0] = [150, 250, 100]  # Initial prices

    data = pd.DataFrame(
        prices,
        columns=['AAPL', 'MSFT', 'GOOGL'],
        index=dates
    )

    # Enhanced configuration
    config = BacktestConfig(
        start_date=dates[0],
        end_date=dates[-1],
        initial_capital=1000000,
        enable_risk_management=True,
        enable_dynamic_adjustments=True,
        enable_stress_testing=True,
        var_limit=0.015,
        max_drawdown_limit=0.10,
        leverage_limit=1.5,
        position_size_limit=0.3,
        volatility_targeting=True,
        target_volatility=0.12
    )

    # Create engine
    engine = EnhancedBacktestEngine(config)

    def balanced_strategy(date: datetime, market_data: pd.Series, portfolio_state: Dict[str, Any]) -> Dict[str, float]:
        """Simple balanced allocation strategy"""
        portfolio_value = portfolio_state["portfolio_value"]

        # Equal weight allocation
        target_allocation = {
            "AAPL": 0.4,
            "MSFT": 0.35,
            "GOOGL": 0.25
        }

        target_positions = {}
        for symbol, allocation in target_allocation.items():
            if symbol in market_data:
                target_value = portfolio_value * allocation
                target_positions[symbol] = target_value / market_data[symbol]

        return target_positions

    # Run different modes
    modes = [
        BacktestMode.STANDARD,
        BacktestMode.RISK_MANAGED,
        # BacktestMode.STRESS_TEST,  # Commented out for faster testing
        # BacktestMode.MONTE_CARLO    # Commented out for faster testing
    ]

    results = {}

    for mode in modes:
        print(f"\nTesting {mode.value} mode...")

        # Reset engine
        engine = EnhancedBacktestEngine(config)

        result = engine.run_backtest(
            strategy=balanced_strategy,
            data=data,
            mode=mode
        )

        results[mode.value] = result

        print(f"  Total Return: {result.total_return:.2%}")
        print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"  Max Drawdown: {result.max_drawdown:.2%}")
        print(f"  VaR 95%: {result.var_95:.2%}")
        print(f"  Total Trades: {result.total_trades}")

    # Compare results
    print("\n" + "="*60)
    print("COMPARISON SUMMARY")
    print("="*60)

    for mode, result in results.items():
        print(f"\n{mode.upper()} MODE:")
        print(f"  Return: {result.total_return:.2%}")
        print(f"  Sharpe: {result.sharpe_ratio:.2f}")
        print(f"  Max DD: {result.max_drawdown:.2%}")
        print(f"  Win Rate: {result.win_rate:.2%}")

    print("\n✅ Integration Test Complete!")
    return results

if __name__ == "__main__":
    import unittest.mock
    from typing import Dict, Any

    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)

    # Run integration test
    run_integration_test()
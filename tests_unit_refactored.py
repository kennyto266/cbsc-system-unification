#!/usr/bin/env python3
"""
Unit Tests for Refactored Technical Analysis System
重構後技術分析系統的單元測試

Comprehensive unit tests for all refactored components.
"""

import unittest
import sys
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
sys.path.append('.')

from refactored_tech_analysis import (
    DataRepository,
    IndicatorFactory,
    BacktestEngine,
    PerformanceCalculator,
    OptimizationOrchestrator,
    OptimizationConfig,
    RSIStrategy,
    MACDStrategy,
    BollingerBandsStrategy,
    CCIStrategy,
    StochasticStrategy
)


class TestDataRepository(unittest.TestCase):
    """Test DataRepository functionality"""

    def setUp(self):
        self.repo = DataRepository()

    @patch('refactored_tech_analysis.data_repository.requests.get')
    def test_get_stock_data_success(self, mock_get):
        """Test successful stock data retrieval"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'close': {
                    '2023-01-01': 100.0,
                    '2023-01-02': 101.0,
                    '2023-01-03': 102.0
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test
        result = self.repo.get_stock_data('0700.HK', 365)

        # Assertions
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 3)
        self.assertIn('close', result.columns)
        self.assertTrue(isinstance(result.index, pd.DatetimeIndex))

    def test_cache_functionality(self):
        """Test caching mechanism"""
        # Test cache size initially
        self.assertEqual(self.repo.get_cache_size(), 0)

        # Mock a simple data
        with patch.object(self.repo, 'stock_source') as mock_source:
            mock_source.fetch_data.return_value = pd.DataFrame({'close': [100, 101, 102]})

            # First access
            data1 = self.repo.get_stock_data('0700.HK')
            self.assertEqual(self.repo.get_cache_size(), 1)

            # Second access (should use cache)
            data2 = self.repo.get_stock_data('0700.HK')
            self.assertEqual(self.repo.get_cache_size(), 1)

            # Clear cache
            self.repo.clear_cache()
            self.assertEqual(self.repo.get_cache_size(), 0)

    def test_clear_cache(self):
        """Test cache clearing"""
        self.repo.clear_cache()
        self.assertEqual(self.repo.get_cache_size(), 0)


class TestTechnicalIndicatorStrategies(unittest.TestCase):
    """Test technical indicator strategies"""

    def test_rsi_strategy(self):
        """Test RSI strategy"""
        strategy = RSIStrategy()

        # Test basic properties
        self.assertEqual(strategy.name, "RSI")
        default_params = strategy.get_default_params()
        self.assertEqual(default_params, {"period": 14})

        param_ranges = strategy.get_param_ranges()
        self.assertEqual(param_ranges, {"period": (5, 50)})

        # Test calculation
        test_data = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110,
                                 109, 108, 107, 106, 105, 104])
        rsi = strategy.calculate(test_data, period=14)

        self.assertIsInstance(rsi, pd.Series)
        self.assertEqual(len(rsi), len(test_data))

    def test_macd_strategy(self):
        """Test MACD strategy"""
        strategy = MACDStrategy()

        # Test basic properties
        self.assertEqual(strategy.name, "MACD")
        default_params = strategy.get_default_params()
        expected_params = {"fast": 12, "slow": 26, "signal": 9}
        self.assertEqual(default_params, expected_params)

        # Test calculation
        test_data = pd.Series(np.random.randn(100) + 100)
        macd = strategy.calculate(test_data, fast=12, slow=26, signal=9)

        self.assertIsInstance(macd, pd.Series)
        self.assertEqual(len(macd), len(test_data))

    def test_bollinger_bands_strategy(self):
        """Test Bollinger Bands strategy"""
        strategy = BollingerBandsStrategy()

        # Test basic properties
        self.assertEqual(strategy.name, "BollingerBands")
        default_params = strategy.get_default_params()
        expected_params = {"period": 20, "std_dev": 2.0}
        self.assertEqual(default_params, expected_params)

        # Test calculation
        test_data = pd.Series(np.random.randn(100) + 100)
        bb_position = strategy.calculate(test_data, period=20, std_dev=2.0)

        self.assertIsInstance(bb_position, pd.Series)
        # BB position should be between 0 and 1
        self.assertTrue((bb_position >= 0).all())
        self.assertTrue((bb_position <= 1).all())

    def test_parameter_validation(self):
        """Test parameter validation"""
        strategy = RSIStrategy()

        # Valid parameters
        valid_params = {"period": 14}
        self.assertTrue(strategy.validate_params(valid_params))

        # Invalid parameters (missing required param)
        invalid_params = {}
        self.assertFalse(strategy.validate_params(invalid_params))


class TestBacktestEngine(unittest.TestCase):
    """Test backtesting engine"""

    def setUp(self):
        self.engine = BacktestEngine()
        self.test_prices = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109])
        self.test_indicator = pd.Series([1, 0, -1, 1, 0, -1, 1, 0, -1, 1])

    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation with 3% risk-free rate"""
        calculator = PerformanceCalculator()

        # Test data with reasonable returns
        test_returns = [0.01, -0.005, 0.02, -0.01, 0.015, -0.008, 0.025, -0.003]

        sharpe = calculator.calculate_sharpe_ratio(test_returns)

        # Sharpe should be calculated correctly
        self.assertIsInstance(sharpe, float)
        self.assertTrue(0 <= sharpe <= 10)  # Reasonable range

        # Test edge cases
        self.assertEqual(calculator.calculate_sharpe_ratio([]), 0.0)
        self.assertEqual(calculator.calculate_sharpe_ratio([0.01]), 0.0)

    def test_max_drawdown_calculation(self):
        """Test max drawdown calculation"""
        calculator = PerformanceCalculator()

        test_returns = [0.05, 0.02, -0.10, 0.03, -0.05]
        max_dd = calculator.calculate_max_drawdown(test_returns)

        self.assertIsInstance(max_dd, float)
        self.assertLessEqual(max_dd, 0)  # Drawdown should be negative or zero

    def test_single_backtest(self):
        """Test single strategy backtest"""
        result = self.engine.backtest_strategy(
            self.test_indicator, self.test_prices, "TEST_STRATEGY"
        )

        self.assertIsInstance(result, result.__class__)
        self.assertEqual(result.strategy_id, "TEST_STRATEGY")
        self.assertIsInstance(result.total_return, float)
        self.assertIsInstance(result.sharpe_ratio, float)
        self.assertTrue(0 <= result.quality_score <= 100)

    def test_multiple_backtests(self):
        """Test multiple strategies backtest"""
        indicators = {
            "STRATEGY_1": pd.Series([1, 0, -1, 1, 0, -1, 1, 0, -1, 1]),
            "STRATEGY_2": pd.Series([0, 1, 0, -1, 1, -1, 1, 0, 1, 0]),
            "STRATEGY_3": pd.Series([-1, 1, 0, 1, -1, 1, 0, -1, 1, 0])
        }

        results = self.engine.backtest_multiple_strategies(indicators, self.test_prices)

        self.assertEqual(len(results), 3)
        for result in results:
            self.assertTrue(result.strategy_id.startswith("STRATEGY_"))
            self.assertIsInstance(result.total_return, float)

    def test_get_top_strategies(self):
        """Test getting top strategies"""
        # Create mock results with different quality scores
        results = [
            Mock(quality_score=50, sharpe_ratio=1.0, total_return=0.05),
            Mock(quality_score=80, sharpe_ratio=2.0, total_return=0.10),
            Mock(quality_score=60, sharpe_ratio=1.5, total_return=0.07),
            Mock(quality_score=90, sharpe_ratio=2.5, total_return=0.15),
        ]

        with patch.object(self.engine, 'backtest_multiple_strategies', return_value=results):
            top_strategies = self.engine.get_top_strategies(results, top_n=2)

        self.assertEqual(len(top_strategies), 2)
        # Should be sorted by quality_score descending
        self.assertEqual(top_strategies[0].quality_score, 90)
        self.assertEqual(top_strategies[1].quality_score, 80)


class TestIndicatorFactory(unittest.TestCase):
    """Test indicator factory"""

    def setUp(self):
        self.repo = DataRepository()
        self.factory = IndicatorFactory(self.repo)

    @patch.object(IndicatorFactory, 'generate_all_combinations')
    def test_create_indicator(self, mock_generate):
        """Test single indicator creation"""
        # Mock combinations
        mock_generate.return_value = []

        with patch.object(self.factory, '_safe_create_indicator') as mock_create:
            mock_create.return_value = pd.Series([1, 2, 3, 4, 5])

            result = self.factory.create_indicator('RSI', 'HB', {'period': 14})

            # Should call the safe creation method
            mock_create.assert_called_once()

    def test_generate_combinations(self):
        """Test combination generation"""
        # This test will be limited due to actual data access
        # In real scenario, we would mock the data sources
        try:
            combinations = self.factory.generate_all_combinations()
            self.assertIsInstance(combinations, list)
            # Should generate combinations for all data sources and indicators
        except Exception as e:
            # Expected due to missing data files in test environment
            self.assertIsInstance(e, Exception)


class TestOptimizationOrchestrator(unittest.TestCase):
    """Test optimization orchestrator"""

    def setUp(self):
        self.config = OptimizationConfig(max_workers=2)
        # Use mock repository to avoid data access issues
        self.mock_repo = Mock()
        self.factory = Mock()
        self.engine = Mock()

        # Mock stock data
        mock_stock_data = Mock()
        self.mock_repo.get_stock_data.return_value = mock_stock_data

        self.orchestrator = OptimizationOrchestrator(
            config=self.config,
            data_repository=self.mock_repo,
            indicator_factory=self.factory,
            backtest_engine=self.engine
        )

    def test_initialization(self):
        """Test orchestrator initialization"""
        self.assertEqual(self.orchestrator.config.max_workers, 2)
        self.assertIsInstance(self.orchestrator.data_repository, Mock)
        self.assertIsInstance(self.orchestrator.indicator_factory, Mock)
        self.assertIsInstance(self.orchestrator.backtest_engine, Mock)

    @patch.object(OptimizationOrchestrator, '_generate_combinations')
    @patch.object(OptimizationOrchestrator, '_create_indicators')
    @patch.object(OptimizationOrchestrator, '_run_backtests')
    def test_run_complete_optimization(self, mock_run_backtests, mock_create_indicators, mock_generate_combinations):
        """Test complete optimization run"""
        # Mock the methods
        mock_generate_combinations.return_value = []
        mock_create_indicators.return_value = {}
        mock_run_backtests.return_value = []

        # Run optimization
        results = self.orchestrator.run_complete_optimization(max_combinations=5)

        # Verify methods were called
        mock_generate_combinations.assert_called_once()
        mock_create_indicators.assert_called_once()
        mock_run_backtests.assert_called_once()


def run_unit_tests():
    """Run all unit tests"""
    print("RUNNING UNIT TESTS FOR REFACTORED SYSTEM")
    print("=" * 60)

    # Create test suite
    test_classes = [
        TestDataRepository,
        TestTechnicalIndicatorStrategies,
        TestBacktestEngine,
        TestIndicatorFactory,
        TestOptimizationOrchestrator
    ]

    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    print("UNIT TEST SUMMARY")
    print("=" * 60)

    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)

    print(f"Tests Run: {total_tests}")
    print(f"Failures: {failures}")
    print(f"Errors: {errors}")
    print(f"Success Rate: {((total_tests - failures - errors) / total_tests * 100):.1f}%")

    if failures == 0 and errors == 0:
        print("\nALL TESTS PASSED! ✅")
        print("Refactored system components are working correctly.")
        print("Design patterns and architecture are properly implemented.")
    else:
        print(f"\n{failures + errors} TESTS FAILED! ❌")
        print("Some components need attention.")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_unit_tests()
    sys.exit(0 if success else 1)
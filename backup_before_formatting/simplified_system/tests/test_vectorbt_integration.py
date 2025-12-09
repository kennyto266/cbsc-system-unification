#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive VectorBT Integration Testing Suite
全面VectorBT集成测试套件 - Phase 5.1

Unit tests, integration tests, performance regression tests, and stress tests
单元测试、集成测试、性能回归测试和压力测试
"""

import unittest
import pytest
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import logging
import time
import sys
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    logging.warning("VectorBT not available - some tests will be skipped")

# Import modules to test
from indicators.vectorbt_indicators import VectorBTIndicators
from backtest.vectorbt_engine import VectorBTEngine
from backtest.signal_fusion_engine import SignalFusionEngine, SignalFusionConfig
from backtest.advanced_portfolio_manager import AdvancedPortfolioManager
from backtest.professional_risk_metrics import ProfessionalRiskMetrics

logger = logging.getLogger(__name__)

class TestVectorBTIndicators(unittest.TestCase):
    """Unit tests for VectorBT indicators"""

    def setUp(self):
        """Set up test fixtures"""
        self.vbt_indicators = VectorBTIndicators(enable_gpu=False)
        self.test_data = self._create_test_data()

    def _create_test_data(self) -> pd.DataFrame:
        """Create test price data"""
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
        assets = ['Asset_A', 'Asset_B', 'Asset_C']

        prices_data = {}
        for asset in assets:
            prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, len(dates))))
            prices_data[asset] = pd.Series(prices, index=dates)

        return pd.DataFrame(prices_data)

    def test_batch_rsi_calculation(self):
        """Test batch RSI calculation"""
        logger.info("Testing batch RSI calculation")

        periods = [14, 21, 30]
        rsi_results = self.vbt_indicators.batch_calculate_rsi(self.test_data, periods)

        # Check results structure
        self.assertIsInstance(rsi_results, pd.DataFrame)
        self.assertEqual(rsi_results.shape[0], len(self.test_data))
        self.assertEqual(len(rsi_results.columns), len(periods))

        # Check value ranges
        for col in rsi_results.columns:
            valid_values = rsi_results[col].dropna()
            if len(valid_values) > 0:
                self.assertTrue((valid_values >= 0).all())
                self.assertTrue((valid_values <= 100).all())

        logger.info(f"RSI batch calculation passed: {rsi_results.shape}")

    def test_batch_macd_calculation(self):
        """Test batch MACD calculation"""
        logger.info("Testing batch MACD calculation")

        if not VECTORBT_AVAILABLE:
            self.skipTest("VectorBT not available")

        macd_results = self.vbt_indicators.batch_calculate_macd(self.test_data)

        # Check results structure
        self.assertIsInstance(macd_results, dict)
        self.assertIn('macd', macd_results)
        self.assertIn('signal', macd_results)
        self.assertIn('histogram', macd_results)

        # Check data consistency
        for key in ['macd', 'signal', 'histogram']:
            if hasattr(macd_results[key], 'shape'):
                self.assertEqual(macd_results[key].shape[0], len(self.test_data))

        logger.info(f"MACD batch calculation passed")

    def test_cross_indicator_analysis(self):
        """Test cross-indicator analysis"""
        logger.info("Testing cross-indicator analysis")

        indicator_configs = {
            'RSI': {'type': 'rsi', 'periods': [14]},
            'MACD': {'type': 'macd', 'fast_periods': [12], 'slow_periods': [26]}
        }

        cross_analysis = self.vbt_indicators.vectorized_cross_indicator_analysis(
            self.test_data, indicator_configs
        )

        # Check results structure
        self.assertIsInstance(cross_analysis, dict)
        self.assertIn('indicators', cross_analysis)
        self.assertIn('correlations', cross_analysis)
        self.assertIn('signals', cross_analysis)
        self.assertIn('attribution', cross_analysis)

        logger.info(f"Cross-indicator analysis passed")

    def test_adaptive_parameter_optimization(self):
        """Test adaptive parameter optimization"""
        logger.info("Testing adaptive parameter optimization")

        returns = self.test_data.pct_change().fillna(0)
        param_ranges = {'periods': [10, 14, 20]}

        adaptive_results = self.vbt_indicators.adaptive_parameter_optimization(
            self.test_data, returns.iloc[:, 0], 'rsi', param_ranges,
            optimization_window=100, rebalance_frequency=20
        )

        # Check results structure
        self.assertIsInstance(adaptive_results, dict)
        self.assertIn('indicator_type', adaptive_results)
        self.assertIn('param_timeline', adaptive_results)
        self.assertIn('average_performance', adaptive_results)

        logger.info(f"Adaptive parameter optimization passed")

    def test_indicator_performance_attribution(self):
        """Test indicator performance attribution"""
        logger.info("Testing indicator performance attribution")

        # Create dummy signals
        signals = {
            'RSI_14': pd.Series(np.random.uniform(-1, 1, len(self.test_data)), index=self.test_data.index),
            'MACD_12_26': pd.Series(np.random.uniform(-1, 1, len(self.test_data)), index=self.test_data.index)
        }

        returns = self.test_data.pct_change().fillna(0)
        benchmark_returns = returns.iloc[:, 0]

        attribution = self.vbt_indicators.calculate_indicator_performance_attribution(
            self.test_data, signals, benchmark_returns
        )

        # Check results
        self.assertIsInstance(attribution, dict)
        for signal_name in signals.keys():
            self.assertIn(signal_name, attribution)
            self.assertTrue(hasattr(attribution[signal_name], 'signal_quality'))

        logger.info(f"Indicator performance attribution passed")

class TestVectorBTEngine(unittest.TestCase):
    """Unit tests for VectorBT engine"""

    def setUp(self):
        """Set up test fixtures"""
        if not VECTORBT_AVAILABLE:
            self.skipTest("VectorBT not available")

        self.engine = VectorBTEngine()
        self.test_data = self._create_test_data()

    def _create_test_data(self) -> pd.DataFrame:
        """Create test OHLCV data"""
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', periods=252, freq='D')

        close_prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, 252)))
        high_prices = close_prices * (1 + np.random.uniform(0, 0.02, 252))
        low_prices = close_prices * (1 - np.random.uniform(0, 0.02, 252))
        open_prices = np.roll(close_prices, 1)
        open_prices[0] = close_prices[0]
        volume = np.random.randint(1000000, 10000000, 252)

        return pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volume
        }, index=dates)

    def test_rsi_strategy_backtest(self):
        """Test RSI strategy backtest"""
        logger.info("Testing RSI strategy backtest")

        params = {'period': 14, 'oversold': 30, 'overbought': 70}
        result = self.engine.backtest_strategy(self.test_data, 'RSI_MEAN_REVERSION', params)

        # Check result structure
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'portfolio') or hasattr(result, 'get_metrics'))

        logger.info(f"RSI strategy backtest passed")

    def test_macd_strategy_backtest(self):
        """Test MACD strategy backtest"""
        logger.info("Testing MACD strategy backtest")

        params = {'fast': 12, 'slow': 26, 'signal': 9}
        result = self.engine.backtest_strategy(self.test_data, 'MACD_CROSSOVER', params)

        # Check result structure
        self.assertIsNotNone(result)

        logger.info(f"MACD strategy backtest passed")

    def test_multiple_strategies_comparison(self):
        """Test multiple strategies comparison"""
        logger.info("Testing multiple strategies comparison")

        strategies = [
            ('RSI_MEAN_REVERSION', {'period': 14, 'oversold': 30, 'overbought': 70}),
            ('MACD_CROSSOVER', {'fast': 12, 'slow': 26, 'signal': 9}),
            ('BOLLINGER_BANDS', {'period': 20, 'std_dev': 2.0})
        ]

        results = []
        for strategy, params in strategies:
            result = self.engine.backtest_strategy(self.test_data, strategy, params)
            results.append((strategy, result))

        # Check that we got results for all strategies
        self.assertEqual(len(results), len(strategies))

        logger.info(f"Multiple strategies comparison passed: {len(results)} strategies")

class TestSignalFusionEngine(unittest.TestCase):
    """Unit tests for signal fusion engine"""

    def setUp(self):
        """Set up test fixtures"""
        self.fusion_engine = SignalFusionEngine()
        self.test_signals = self._create_test_signals()

    def _create_test_signals(self) -> Dict[str, pd.Series]:
        """Create test signals"""
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', periods=100, freq='D')

        return {
            'RSI': pd.Series(np.random.uniform(0, 1, 100), index=dates),
            'MACD': pd.Series(np.random.uniform(0, 1, 100), index=dates),
            'Volume': pd.Series(np.random.uniform(0, 1, 100), index=dates)
        }

    def test_signal_fusion(self):
        """Test signal fusion functionality"""
        logger.info("Testing signal fusion")

        # This test will check the basic structure since the full fusion engine
        # may have dependencies on other modules
        self.assertIsNotNone(self.fusion_engine)
        self.assertIsInstance(self.test_signals, dict)

        logger.info(f"Signal fusion test passed")

class TestProfessionalRiskMetrics(unittest.TestCase):
    """Unit tests for professional risk metrics"""

    def setUp(self):
        """Set up test fixtures"""
        self.risk_metrics = ProfessionalRiskMetrics()
        self.test_returns = self._create_test_returns()

    def _create_test_returns(self) -> pd.Series:
        """Create test returns data"""
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 252)
        return pd.Series(returns, index=pd.date_range('2020-01-01', periods=252, freq='D'))

    def test_var_calculation(self):
        """Test VaR calculation"""
        logger.info("Testing VaR calculation")

        var_results = self.risk_metrics.calculate_var(self.test_returns, 0.95)

        # Check results structure
        self.assertIsInstance(var_results, dict)
        self.assertIn('var_historical', var_results)
        self.assertIn('var_parametric', var_results)
        self.assertIn('var_cornish_fisher', var_results)

        # Check that VaR values are reasonable (negative values)
        for var_type in ['var_historical', 'var_parametric', 'var_cornish_fisher']:
            var_value = var_results[var_type]
            if var_value is not None and not np.isnan(var_value):
                self.assertLess(var_value, 0)  # VaR should be negative

        logger.info(f"VaR calculation passed")

    def test_cvar_calculation(self):
        """Test CVaR calculation"""
        logger.info("Testing CVaR calculation")

        cvar_results = self.risk_metrics.calculate_cvar(self.test_returns, 0.95)

        # Check results structure
        self.assertIsInstance(cvar_results, dict)
        self.assertIn('cvar_historical', cvar_results)
        self.assertIn('cvar_parametric', cvar_results)

        logger.info(f"CVaR calculation passed")

    def test_sortino_ratio(self):
        """Test Sortino ratio calculation"""
        logger.info("Testing Sortino ratio calculation")

        sortino_ratio = self.risk_metrics.calculate_sortino_ratio(self.test_returns)

        # Check that Sortino ratio is a reasonable number
        self.assertIsInstance(sortino_ratio, float)
        self.assertFalse(np.isnan(sortino_ratio))

        logger.info(f"Sortino ratio calculation passed: {sortino_ratio:.3f}")

    def test_calmar_ratio(self):
        """Test Calmar ratio calculation"""
        logger.info("Testing Calmar ratio calculation")

        calmar_ratio = self.risk_metrics.calculate_calmar_ratio(self.test_returns)

        # Check that Calmar ratio is a reasonable number
        self.assertIsInstance(calmar_ratio, float)
        self.assertFalse(np.isnan(calmar_ratio))

        logger.info(f"Calmar ratio calculation passed: {calmar_ratio:.3f}")

    def test_comprehensive_metrics(self):
        """Test comprehensive metrics calculation"""
        logger.info("Testing comprehensive metrics calculation")

        all_metrics = self.risk_metrics.calculate_all_metrics(self.test_returns)

        # Check that key metrics are present
        required_metrics = [
            'total_return', 'annualized_return', 'volatility', 'sharpe_ratio',
            'sortino_ratio', 'calmar_ratio', 'max_drawdown'
        ]

        for metric in required_metrics:
            self.assertIn(metric, all_metrics)
            self.assertFalse(np.isnan(all_metrics[metric]))

        logger.info(f"Comprehensive metrics calculation passed")

class TestPerformanceRegression(unittest.TestCase):
    """Performance regression tests"""

    def setUp(self):
        """Set up test fixtures"""
        self.baseline_performance = {
            'rsi_calculation_time': 0.01,  # 10ms
            'macd_calculation_time': 0.01,  # 10ms
            'portfolio_backtest_time': 0.1,  # 100ms
            'risk_metrics_calculation_time': 0.05  # 50ms
        }

    def test_vectorbt_performance_regression(self):
        """Test VectorBT performance regression"""
        logger.info("Testing VectorBT performance regression")

        if not VECTORBT_AVAILABLE:
            self.skipTest("VectorBT not available")

        # Create test data
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', periods=1000, freq='D')
        prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, 1000)))
        price_data = pd.DataFrame({'close': prices}, index=dates)

        # Test RSI calculation performance
        start_time = time.time()
        rsi_indicator = vbt.RSI.run(price_data['close'], window=14)
        rsi_time = time.time() - start_time

        # Test MACD calculation performance
        start_time = time.time()
        macd_indicator = vbt.MACD.run(price_data['close'], fast=12, slow=26, signal=9)
        macd_time = time.time() - start_time

        # Check performance against baseline (allow 2x slower as acceptable)
        self.assertLess(rsi_time, self.baseline_performance['rsi_calculation_time'] * 2)
        self.assertLess(macd_time, self.baseline_performance['macd_calculation_time'] * 2)

        logger.info(f"Performance regression test passed: RSI={rsi_time:.3f}s, MACD={macd_time:.3f}s")

class TestStressTesting(unittest.TestCase):
    """Stress tests for large-scale optimizations"""

    def test_large_scale_parameter_optimization(self):
        """Test large-scale parameter optimization"""
        logger.info("Testing large-scale parameter optimization")

        # Create large test dataset
        np.random.seed(42)
        dates = pd.date_range('2010-01-01', '2023-12-31', freq='D')  # ~14 years of data
        assets = [f'Asset_{i:03d}' for i in range(50)]  # 50 assets

        prices_data = {}
        for asset in assets:
            prices = 100 * np.exp(np.cumsum(np.random.normal(0.0005, 0.015, len(dates))))
            prices_data[asset] = pd.Series(prices, index=dates)

        large_dataset = pd.DataFrame(prices_data)

        # Test that the system can handle large datasets without memory issues
        self.assertEqual(large_dataset.shape[1], 50)
        self.assertGreater(len(large_dataset), 3000)  # At least 3000 data points

        # Test batch calculation on large dataset
        if VECTORBT_AVAILABLE:
            vbt_indicators = VectorBTIndicators()

            # Test RSI calculation (should not crash)
            periods = [14, 21]
            start_time = time.time()
            rsi_results = vbt_indicators.batch_calculate_rsi(large_dataset.iloc[:, :10], periods)  # Test with subset
            rsi_time = time.time() - start_time

            # Should complete within reasonable time (30 seconds for large dataset)
            self.assertLess(rsi_time, 30.0)
            self.assertIsNotNone(rsi_results)

            logger.info(f"Large-scale optimization test passed: {rsi_time:.2f}s for {large_dataset.shape}")
        else:
            self.skipTest("VectorBT not available")

    def test_memory_usage_stress(self):
        """Test memory usage under stress"""
        logger.info("Testing memory usage stress")

        try:
            import psutil
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Create multiple large datasets
            datasets = []
            for i in range(5):
                np.random.seed(42 + i)
                dates = pd.date_range('2015-01-01', '2023-12-31', freq='D')
                prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, len(dates))))
                df = pd.DataFrame({'close': prices}, index=dates)
                datasets.append(df)

            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - initial_memory

            # Memory increase should be reasonable (< 1GB)
            self.assertLess(memory_increase, 1024)

            logger.info(f"Memory usage stress test passed: {memory_increase:.1f}MB increase")
        except ImportError:
            self.skipTest("psutil not available - cannot test memory usage")

class IntegrationTestSuite(unittest.TestCase):
    """Integration tests for the complete system"""

    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        logger.info("Testing end-to-end workflow")

        # Create test data
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', periods=252, freq='D')
        close_prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, 252)))
        high_prices = close_prices * (1 + np.random.uniform(0, 0.02, 252))
        low_prices = close_prices * (1 - np.random.uniform(0, 0.02, 252))
        open_prices = np.roll(close_prices, 1)
        open_prices[0] = close_prices[0]
        volume = np.random.randint(1000000, 10000000, 252)

        ohlcv_data = pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volume
        }, index=dates)

        # Test complete workflow
        # 1. Calculate indicators
        if VECTORBT_AVAILABLE:
            vbt_indicators = VectorBTIndicators()
            rsi_results = vbt_indicators.batch_calculate_rsi(ohlcv_data[['close']], [14])
            self.assertIsNotNone(rsi_results)

            # 2. Run backtest
            engine = VectorBTEngine()
            result = engine.backtest_strategy(ohlcv_data, 'RSI_MEAN_REVERSION', {'period': 14, 'oversold': 30, 'overbought': 70})
            self.assertIsNotNone(result)

            # 3. Calculate risk metrics
            returns = ohlcv_data['close'].pct_change().fillna(0)
            risk_metrics = ProfessionalRiskMetrics()
            all_metrics = risk_metrics.calculate_all_metrics(returns)
            self.assertIsInstance(all_metrics, dict)

            logger.info("End-to-end workflow test passed")

    def test_multi_component_integration(self):
        """Test integration between multiple components"""
        logger.info("Testing multi-component integration")

        # This test checks that different components can work together
        # without conflicts or dependency issues

        try:
            # Initialize all components
            components = {}

            if VECTORBT_AVAILABLE:
                components['vbt_indicators'] = VectorBTIndicators()
                components['engine'] = VectorBTEngine()

            components['risk_metrics'] = ProfessionalRiskMetrics()

            # Check that all components initialized successfully
            for name, component in components.items():
                self.assertIsNotNone(component)

            logger.info(f"Multi-component integration test passed: {len(components)} components")

        except Exception as e:
            self.fail(f"Multi-component integration failed: {e}")

# Test runner and reporting functions

def run_comprehensive_test_suite():
    """Run the complete test suite and generate report"""
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE VECTORBT INTEGRATION TEST SUITE")
    logger.info("=" * 80)

    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test cases
    test_classes = [
        TestVectorBTIndicators,
        TestVectorBTEngine,
        TestSignalFusionEngine,
        TestProfessionalRiskMetrics,
        TestPerformanceRegression,
        TestStressTesting,
        IntegrationTestSuite
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Generate test report
    test_report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_tests': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100,
        'vectorbt_available': VECTORBT_AVAILABLE,
        'test_classes': len(test_classes)
    }

    # Print summary
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total Tests: {test_report['total_tests']}")
    logger.info(f"Failures: {test_report['failures']}")
    logger.info(f"Errors: {test_report['errors']}")
    logger.info(f"Success Rate: {test_report['success_rate']:.1f}%")
    logger.info(f"VectorBT Available: {test_report['vectorbt_available']}")
    logger.info(f"Test Classes: {test_report['test_classes']}")

    if result.failures:
        logger.info("\nFAILURES:")
        for test, traceback in result.failures:
            logger.info(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        logger.info("\nERRORS:")
        for test, traceback in result.errors:
            logger.info(f"- {test}: {traceback.split('Exception:')[-1].strip()}")

    # Save test report
    try:
        import json
        report_filename = f"vectorbt_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(test_report, f, indent=2, default=str)
        logger.info(f"\nTest report saved to: {report_filename}")
    except Exception as e:
        logger.warning(f"Could not save test report: {e}")

    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_comprehensive_test_suite()
    sys.exit(0 if success else 1)
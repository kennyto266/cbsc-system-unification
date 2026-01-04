"""
Tests for risk calculators
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from ..risk_calculators import (
    VaRCalculator,
    ExpectedShortfallCalculator,
    MaxDrawdownCalculator,
    VolatilityCalculator,
    CorrelationAnalyzer
)


class TestVaRCalculator(unittest.TestCase):
    """Test VaR calculator"""

    def setUp(self):
        self.calculator = VaRCalculator()
        # Generate sample returns
        np.random.seed(42)
        self.returns = pd.Series(np.random.normal(0.001, 0.02, 1000))

    def test_historical_var(self):
        """Test historical VaR calculation"""
        var_95 = self.calculator.calculate_historical_var(self.returns, 0.95)
        var_99 = self.calculator.calculate_historical_var(self.returns, 0.99)

        # VaR should be positive
        self.assertGreater(var_95, 0)
        self.assertGreater(var_99, 0)

        # 99% VaR should be greater than 95% VaR
        self.assertGreater(var_99, var_95)

    def test_parametric_var(self):
        """Test parametric VaR calculation"""
        var_normal = self.calculator.calculate_parametric_var(self.returns, 0.95, "normal")
        var_t = self.calculator.calculate_parametric_var(self.returns, 0.95, "t")

        # VaR should be positive
        self.assertGreater(var_normal, 0)
        self.assertGreater(var_t, 0)

    def test_monte_carlo_var(self):
        """Test Monte Carlo VaR calculation"""
        var_mc = self.calculator.calculate_monte_carlo_var(self.returns, 0.95, n_simulations=1000)

        # VaR should be positive
        self.assertGreater(var_mc, 0)


class TestExpectedShortfallCalculator(unittest.TestCase):
    """Test Expected Shortfall calculator"""

    def setUp(self):
        self.calculator = ExpectedShortfallCalculator()
        np.random.seed(42)
        self.returns = pd.Series(np.random.normal(0.001, 0.02, 1000))

    def test_historical_es(self):
        """Test historical ES calculation"""
        es_95 = self.calculator.calculate_historical_es(self.returns, 0.95)
        es_99 = self.calculator.calculate_historical_es(self.returns, 0.99)

        # ES should be positive
        self.assertGreater(es_95, 0)
        self.assertGreater(es_99, 0)

        # 99% ES should be greater than 95% ES
        self.assertGreater(es_99, es_95)

    def test_parametric_es(self):
        """Test parametric ES calculation"""
        es_normal = self.calculator.calculate_parametric_es(self.returns, 0.95, "normal")
        es_t = self.calculator.calculate_parametric_es(self.returns, 0.95, "t")

        # ES should be positive
        self.assertGreater(es_normal, 0)
        self.assertGreater(es_t, 0)


class TestMaxDrawdownCalculator(unittest.TestCase):
    """Test Max Drawdown calculator"""

    def setUp(self):
        self.calculator = MaxDrawdownCalculator()
        # Generate sample prices
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 1000)
        self.prices = pd.Series(100 * np.exp(np.cumsum(returns)))

    def test_max_drawdown(self):
        """Test max drawdown calculation"""
        metrics = self.calculator.calculate_max_drawdown(self.prices)

        # Check all required metrics are present
        self.assertIn("max_drawdown", metrics)
        self.assertIn("max_drawdown_duration", metrics)
        self.assertIn("recovery_time", metrics)
        self.assertIn("current_drawdown", metrics)

        # Max drawdown should be positive
        self.assertGreater(metrics["max_drawdown"], 0)

        # Duration should be non-negative
        self.assertGreaterEqual(metrics["max_drawdown_duration"], 0)

    def test_rolling_max_drawdown(self):
        """Test rolling max drawdown calculation"""
        rolling_dd = self.calculator.calculate_rolling_max_drawdown(self.prices, window=100)

        # Should return a series
        self.assertIsInstance(rolling_dd, pd.Series)

        # Length should match input (minus window)
        self.assertEqual(len(rolling_dd), len(self.prices))


class TestVolatilityCalculator(unittest.TestCase):
    """Test Volatility calculator"""

    def setUp(self):
        self.calculator = VolatilityCalculator()
        np.random.seed(42)
        self.returns = pd.Series(np.random.normal(0.001, 0.02, 1000))

    def test_returns_volatility(self):
        """Test returns volatility calculation"""
        vol_20 = self.calculator.calculate_returns_volatility(self.returns, window=20)
        vol_60 = self.calculator.calculate_returns_volatility(self.returns, window=60)

        # Volatility should be positive
        self.assertGreater(vol_20, 0)
        self.assertGreater(vol_60, 0)

    def test_parkinson_volatility(self):
        """Test Parkinson volatility calculation"""
        # Generate OHLC data
        close = 100 + np.cumsum(np.random.normal(0, 1, 1000))
        high = close + np.random.uniform(0, 2, 1000)
        low = close - np.random.uniform(0, 2, 1000)

        parkinson_vol = self.calculator.calculate_parkinson_volatility(
            pd.Series(high),
            pd.Series(low),
            window=20
        )

        # Should return a series
        self.assertIsInstance(parkinson_vol, pd.Series)

        # Volatility should be positive
        self.assertTrue((parkinson_vol > 0).all())

    def test_ewma_volatility(self):
        """Test EWMA volatility calculation"""
        ewma_vol = self.calculator.calculate_ewma_volatility(self.returns)

        # Should return a series
        self.assertIsInstance(ewma_vol, pd.Series)

        # Length should match input
        self.assertEqual(len(ewma_vol), len(self.returns))


class TestCorrelationAnalyzer(unittest.TestCase):
    """Test Correlation analyzer"""

    def setUp(self):
        self.analyzer = CorrelationAnalyzer()
        np.random.seed(42)
        # Generate correlated returns
        n = 1000
        returns1 = np.random.normal(0, 0.02, n)
        returns2 = 0.5 * returns1 + np.random.normal(0, 0.015, n)
        self.returns_df = pd.DataFrame({
            "asset1": returns1,
            "asset2": returns2
        })

    def test_correlation_matrix(self):
        """Test correlation matrix calculation"""
        corr_matrix = self.analyzer.calculate_correlation_matrix(self.returns_df)

        # Should be a DataFrame
        self.assertIsInstance(corr_matrix, pd.DataFrame)

        # Should be square
        self.assertEqual(corr_matrix.shape[0], corr_matrix.shape[1])

        # Diagonal should be 1
        np.testing.assert_array_almost_equal(np.diag(corr_matrix), 1.0)

    def test_rolling_correlation(self):
        """Test rolling correlation calculation"""
        rolling_corr = self.analyzer.calculate_rolling_correlation(
            self.returns_df,
            window=60
        )

        # Should return a dictionary
        self.assertIsInstance(rolling_corr, dict)

        # Should have correlation for asset pair
        self.assertIn(("asset1", "asset2"), rolling_corr)

    def test_concentration_ratio(self):
        """Test concentration ratio calculation"""
        weights = pd.Series([0.4, 0.3, 0.2, 0.1], index=["A", "B", "C", "D"])
        concentration = self.analyzer.calculate_concentration_ratio(weights, top_n=2)

        # Should contain expected metrics
        self.assertIn("top_2_concentration", concentration)
        self.assertIn("hhi", concentration)
        self.assertIn("effective_positions", concentration)
        self.assertIn("gini_coefficient", concentration)

        # Top 2 concentration should be 0.7 (40% + 30%)
        self.assertAlmostEqual(concentration["top_2_concentration"], 0.7, places=2)


if __name__ == "__main__":
    unittest.main()
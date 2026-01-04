"""
Tests for risk engine
"""

import unittest
import asyncio
import pandas as pd
from datetime import datetime, timedelta

from ..risk_engine import RiskEngine
from ..config import RiskConfig


class TestRiskEngine(unittest.TestCase):
    """Test Risk Engine"""

    def setUp(self):
        self.config = RiskConfig()
        # Disable InfluxDB and WebSocket for testing
        self.config.influxdb_host = ""
        self.config.websocket_port = 0
        self.engine = RiskEngine(self.config)

    def test_initialization(self):
        """Test engine initialization"""
        self.assertIsNotNone(self.engine.var_calculator)
        self.assertIsNotNone(self.engine.es_calculator)
        self.assertIsNotNone(self.engine.drawdown_calculator)
        self.assertIsNotNone(self.engine.volatility_calculator)
        self.assertIsNotNone(self.engine.alert_system)

    def test_add_remove_portfolio(self):
        """Test adding and removing portfolios"""
        portfolio_id = "test_portfolio"
        portfolio_info = {
            "name": "Test Portfolio",
            "positions": {"AAPL": 0.5, "MSFT": 0.5}
        }

        # Add portfolio
        self.engine.add_portfolio(portfolio_id, portfolio_info)
        self.assertIn(portfolio_id, self.engine.engine.portfolios)

        # Remove portfolio
        self.engine.remove_portfolio(portfolio_id)
        self.assertNotIn(portfolio_id, self.engine.engine.portfolios)

    def test_risk_metrics_calculation(self):
        """Test risk metrics calculation"""
        # Create sample portfolio data
        dates = pd.date_range(end=datetime.now(), periods=100, freq="D")
        returns = pd.Series(
            [0.001] * 100,
            index=dates
        )
        portfolio_data = pd.DataFrame({"returns": returns})

        # Calculate metrics
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        metrics = loop.run_until_complete(
            self.engine._calculate_risk_metrics("test", portfolio_data)
        )
        loop.close()

        # Check metrics are calculated
        self.assertIsNotNone(metrics)
        self.assertIn("var_95_historical", metrics)
        self.assertIn("volatility_20d", metrics)


class TestRiskCalculations(unittest.TestCase):
    """Test integrated risk calculations"""

    def setUp(self):
        self.config = RiskConfig()
        self.engine = RiskEngine(self.config)

    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation"""
        # Create returns series
        returns = pd.Series([0.01] * 100)  # 1% daily returns

        sharpe = self.engine._calculate_sharpe_ratio(returns)
        self.assertGreater(sharpe, 0)

    def test_beta_calculation(self):
        """Test beta calculation"""
        # Create asset and market returns
        asset_returns = pd.Series([0.01] * 100)
        market_returns = pd.Series([0.008] * 100)

        beta = self.engine._calculate_beta(asset_returns, market_returns)
        self.assertIsInstance(beta, float)

    def test_risk_summary(self):
        """Test risk summary generation"""
        summary = self.engine.get_risk_summary()

        # Check summary contains expected fields
        self.assertIn("monitored_portfolios", summary)
        self.assertIn("active_alerts", summary)
        self.assertIn("calculation_interval", summary)


if __name__ == "__main__":
    unittest.main()
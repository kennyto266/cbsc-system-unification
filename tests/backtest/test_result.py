"""
Unit tests for BacktestResult.

Tests result parsing, DataFrame conversion, and visualization methods.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from cbsc_strategy_sdk.backtest.result import BacktestResult
from cbsc_strategy_sdk.backtest.models import (
    BacktestJob,
    BacktestMetrics,
    BacktestResultData,
    BacktestStatus,
    BacktestTrade,
)


class TestBacktestResult:
    """Test suite for BacktestResult class."""

    @pytest.fixture
    def sample_result_data(self):
        """Create sample result data for testing."""
        return BacktestResultData(
            job=BacktestJob(
                job_id="test-job-123",
                status=BacktestStatus.COMPLETED,
                created_at=datetime(2024, 1, 1, 12, 0, 0),
                started_at=datetime(2024, 1, 1, 12, 0, 1),
                completed_at=datetime(2024, 1, 1, 12, 0, 10),
                progress=100.0,
            ),
            metrics=BacktestMetrics(
                total_return=15.5,
                annual_return=18.2,
                sharpe_ratio=1.5,
                sortino_ratio=2.0,
                max_drawdown=8.5,
                calmar_ratio=2.1,
                win_rate=65.0,
                profit_factor=1.8,
                total_trades=100,
                profit_trades=65,
                avg_profit=2.5,
                avg_loss=-1.8,
            ),
            trades=[
                BacktestTrade(
                    trade_id="trade-001",
                    symbol="AAPL",
                    entry_time=datetime(2024, 1, 2, 10, 0, 0),
                    exit_time=datetime(2024, 1, 5, 15, 0, 0),
                    direction="long",
                    entry_price=150.0,
                    exit_price=155.0,
                    quantity=100,
                    pnl=500.0,
                    pnl_percent=3.33,
                ),
                BacktestTrade(
                    trade_id="trade-002",
                    symbol="AAPL",
                    entry_time=datetime(2024, 1, 10, 10, 0, 0),
                    exit_time=datetime(2024, 1, 15, 15, 0, 0),
                    direction="short",
                    entry_price=152.0,
                    exit_price=150.0,
                    quantity=100,
                    pnl=200.0,
                    pnl_percent=1.32,
                ),
            ],
            equity_curve=[
                {"timestamp": "2024-01-01T00:00:00", "equity": 1000000, "drawdown": 0.0},
                {"timestamp": "2024-01-02T00:00:00", "equity": 1000500, "drawdown": 0.0},
                {"timestamp": "2024-01-05T00:00:00", "equity": 1001000, "drawdown": 0.0},
                {"timestamp": "2024-01-10T00:00:00", "equity": 1000800, "drawdown": 0.02},
                {"timestamp": "2024-01-15T00:00:00", "equity": 1001000, "drawdown": 0.0},
            ],
            parameters={"rsi_period": 14, "oversold": 30},
        )

    @pytest.fixture
    def result(self, sample_result_data):
        """Create BacktestResult instance."""
        return BacktestResult(raw_data=sample_result_data)

    def test_initialization(self, result):
        """Test result initializes correctly."""
        assert result.job.job_id == "test-job-123"
        assert result.metrics.total_return == 15.5
        assert len(result.trades) == 2
        assert len(result.equity_curve) == 5

    def test_to_dataframe(self, result):
        """Test DataFrame conversion."""
        df = result.to_dataframe()

        assert df is not None
        assert len(df) == 2
        assert "trade_id" in df.columns
        assert "symbol" in df.columns
        assert "pnl" in df.columns
        assert "is_winner" in df.columns
        assert "holding_period_days" in df.columns

        # Check trade data
        assert df.iloc[0]["trade_id"] == "trade-001"
        assert df.iloc[0]["pnl"] == 500.0
        assert df.iloc[0]["is_winner"] == True  # Use == instead of is

    def test_to_dataframe_empty_trades(self):
        """Test DataFrame conversion with no trades."""
        data = BacktestResultData(
            job=BacktestJob(
                job_id="test-job",
                status=BacktestStatus.COMPLETED,
                created_at=datetime.now(),
                progress=100.0,
            ),
            metrics=BacktestMetrics(
                total_return=0.0,
                annual_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                total_trades=0,
                profit_trades=0,
                avg_profit=0.0,
                avg_loss=0.0,
            ),
            trades=[],
            equity_curve=[],
            parameters={},
        )

        result = BacktestResult(raw_data=data)
        df = result.to_dataframe()

        assert df.empty

    def test_get_equity_dataframe(self, result):
        """Test equity curve DataFrame."""
        df = result.get_equity_dataframe()

        assert df is not None
        assert len(df) == 5
        assert "timestamp" in df.columns
        assert "equity" in df.columns
        assert "drawdown" in df.columns

        # Check values
        assert df.iloc[0]["equity"] == 1000000
        assert df.iloc[-1]["equity"] == 1001000

    def test_summary(self, result):
        """Test text summary generation."""
        summary = result.summary()

        assert "Backtest Summary: test-job-123" in summary
        assert "15.50%" in summary  # Total return
        assert "1.50" in summary  # Sharpe ratio
        assert "100" in summary  # Total trades
        assert "65" in summary  # Profit trades

    def test_get_metrics_dict(self, result):
        """Test metrics dictionary."""
        metrics = result.get_metrics_dict()

        assert isinstance(metrics, dict)
        assert metrics["total_return"] == 15.5
        assert metrics["sharpe_ratio"] == 1.5
        assert metrics["win_rate"] == 65.0

    def test_plot_equity_curve(self, result):
        """Test equity curve plotting."""
        fig = result.plot_equity_curve()

        if fig is not None:  # Plotly available
            assert hasattr(fig, "show")
        else:
            # Plotly not available, should return None
            assert fig is None

    def test_plot_drawdown(self, result):
        """Test drawdown plotting."""
        fig = result.plot_drawdown()

        if fig is not None:
            assert hasattr(fig, "show")

    def test_plot_monthly_returns(self, result):
        """Test monthly returns plotting."""
        fig = result.plot_monthly_returns()

        if fig is not None:
            assert hasattr(fig, "show")

    def test_repr(self, result):
        """Test string representation."""
        repr_str = repr(result)

        assert "BacktestResult" in repr_str
        assert "test-job-123" in repr_str
        assert "15.50%" in repr_str
        assert "1.50" in repr_str

    def test_calculate_rolling_metrics(self, result):
        """Test rolling metrics calculation."""
        rolling = result.calculate_rolling_metrics(window=2)

        assert rolling is not None
        assert "returns" in rolling.columns
        assert "volatility" in rolling.columns
        assert "sharpe" in rolling.columns
        assert "drawdown" in rolling.columns


class TestBacktestResultEdgeCases:
    """Test edge cases for BacktestResult."""

    def test_empty_equity_curve(self):
        """Test handling of empty equity curve."""
        data = BacktestResultData(
            job=BacktestJob(
                job_id="test-job",
                status=BacktestStatus.COMPLETED,
                created_at=datetime.now(),
                progress=100.0,
            ),
            metrics=BacktestMetrics(
                total_return=0.0,
                annual_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                total_trades=0,
                profit_trades=0,
                avg_profit=0.0,
                avg_loss=0.0,
            ),
            trades=[],
            equity_curve=[],
            parameters={},
        )

        result = BacktestResult(raw_data=data)

        # Empty equity curve
        df = result.get_equity_dataframe()
        assert df.empty

        # Plotting with empty data
        fig = result.plot_equity_curve()
        assert fig is None

        fig = result.plot_drawdown()
        assert fig is None

    def test_equity_curve_missing_drawdown(self):
        """Test equity curve without drawdown data."""
        data = BacktestResultData(
            job=BacktestJob(
                job_id="test-job",
                status=BacktestStatus.COMPLETED,
                created_at=datetime.now(),
                progress=100.0,
            ),
            metrics=BacktestMetrics(
                total_return=0.0,
                annual_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                total_trades=0,
                profit_trades=0,
                avg_profit=0.0,
                avg_loss=0.0,
            ),
            trades=[],
            equity_curve=[
                {"timestamp": "2024-01-01T00:00:00", "equity": 1000000},
            ],
            parameters={},
        )

        result = BacktestResult(raw_data=data)
        df = result.get_equity_dataframe()

        # Should have equity but no drawdown
        assert "equity" in df.columns
        # Drawdown column should exist but be NaN
        assert "drawdown" in df.columns

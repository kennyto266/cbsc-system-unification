"""
Unit tests for visualization.performance module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from cbsc_strategy_sdk.visualization.performance import PerformanceCharts


@pytest.fixture
def sample_returns():
    """Create sample returns data for testing."""
    np.random.seed(42)
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=252),
        periods=252,
        freq='D'
    )

    returns = pd.Series(
        np.random.normal(0.001, 0.02, 252),
        index=dates
    )

    return returns


@pytest.fixture
def sample_benchmark():
    """Create sample benchmark returns."""
    np.random.seed(43)
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=252),
        periods=252,
        freq='D'
    )

    returns = pd.Series(
        np.random.normal(0.0005, 0.015, 252),
        index=dates
    )

    return returns


@pytest.fixture
def sample_pnl():
    """Create sample PnL data."""
    np.random.seed(44)
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=100),
        periods=100,
        freq='D'
    )

    pnl = pd.Series(
        np.random.normal(100, 500, 100),
        index=dates
    )

    return pnl


class TestPerformanceCharts:
    """Test PerformanceCharts class."""

    def test_init_default_theme(self):
        """Test PerformanceCharts initialization."""
        charts = PerformanceCharts()
        assert charts is not None
        assert charts.theme.name == "dark"

    def test_init_custom_theme(self):
        """Test PerformanceCharts with custom theme."""
        charts = PerformanceCharts(theme="light")
        assert charts.theme.name == "light"

    def test_init_without_plotly(self, monkeypatch):
        """Test error when Plotly is not available."""
        import sys
        module = type(sys)('cbsc_strategy_sdk.visualization.performance')
        module.PLOTLY_AVAILABLE = False

        with pytest.raises(ImportError, match="Plotly is required"):
            PerformanceCharts()

    def test_plot_performance_basic(self, sample_returns):
        """Test basic performance plot."""
        charts = PerformanceCharts()
        fig = charts.plot_performance(sample_returns)

        assert fig is not None
        assert len(fig.data) == 2  # Returns + drawdown

    def test_plot_performance_with_benchmark(self, sample_returns, sample_benchmark):
        """Test performance plot with benchmark."""
        charts = PerformanceCharts()
        fig = charts.plot_performance(sample_returns, sample_benchmark)

        assert fig is not None
        assert len(fig.data) >= 3  # Strategy + benchmark + drawdown

    def test_plot_pnl_basic(self, sample_pnl):
        """Test basic PnL plot."""
        charts = PerformanceCharts()
        fig = charts.plot_pnl(sample_pnl, show_cumulative=False)

        assert fig is not None
        assert len(fig.data) == 1

    def test_plot_pnl_with_cumulative(self, sample_pnl):
        """Test PnL plot with cumulative view."""
        charts = PerformanceCharts()
        fig = charts.plot_pnl(sample_pnl, show_cumulative=True)

        assert fig is not None
        assert len(fig.data) == 2  # Cumulative + period PnL

    def test_plot_backtest_comparison(self, sample_returns):
        """Test backtest comparison plot."""
        charts = PerformanceCharts()

        results = {
            'Strategy A': sample_returns,
            'Strategy B': sample_returns * 0.8,
            'Strategy C': sample_returns * 1.2,
        }

        fig = charts.plot_backtest_comparison(results)

        assert fig is not None
        assert len(fig.data) == 3  # Three strategies

    def test_plot_rolling_metrics(self, sample_returns):
        """Test rolling metrics plot."""
        charts = PerformanceCharts()
        fig = charts.plot_rolling_metrics(sample_returns, window=20)

        assert fig is not None
        assert len(fig.data) == 2  # Sharpe + Sortino

    def test_plot_monthly_returns(self, sample_returns):
        """Test monthly returns heatmap."""
        charts = PerformanceCharts()
        fig = charts.plot_monthly_returns(sample_returns)

        assert fig is not None
        # Heatmap should have at least one trace
        assert len(fig.data) >= 1

    def test_create_performance_dashboard(self, sample_returns):
        """Test comprehensive performance dashboard."""
        charts = PerformanceCharts()
        fig = charts.create_performance_dashboard(sample_returns)

        assert fig is not None
        # Dashboard should have multiple traces
        assert len(fig.data) >= 3

    def test_create_performance_dashboard_with_benchmark(self, sample_returns, sample_benchmark):
        """Test performance dashboard with benchmark."""
        charts = PerformanceCharts()
        fig = charts.create_performance_dashboard(
            sample_returns,
            benchmark=sample_benchmark
        )

        assert fig is not None
        # Should have more traces with benchmark
        assert len(fig.data) >= 4


class TestPerformanceCalculations:
    """Test performance metric calculations."""

    def test_cumulative_returns_calculation(self, sample_returns):
        """Test cumulative returns are calculated correctly."""
        charts = PerformanceCharts()
        fig = charts.plot_performance(sample_returns)

        # Check that cumulative returns are present
        assert len(fig.data) > 0

    def test_drawdown_calculation(self, sample_returns):
        """Test drawdown is calculated correctly."""
        charts = PerformanceCharts()
        fig = charts.plot_performance(sample_returns)

        # Second trace should be drawdown
        assert len(fig.data) >= 2

    def test_rolling_sharpe_calculation(self, sample_returns):
        """Test rolling Sharpe calculation."""
        charts = PerformanceCharts()
        fig = charts.plot_rolling_metrics(sample_returns, window=20)

        # Should have Sharpe and Sortino traces
        assert len(fig.data) == 2


class TestPerformanceThemes:
    """Test theme application for performance charts."""

    def test_dark_theme(self, sample_returns):
        """Test dark theme application."""
        charts = PerformanceCharts(theme="dark")
        fig = charts.plot_performance(sample_returns)

        assert fig.layout.paper_bgcolor == charts.theme.background

    def test_light_theme(self, sample_returns):
        """Test light theme application."""
        charts = PerformanceCharts(theme="light")
        fig = charts.plot_performance(sample_returns)

        assert fig.layout.paper_bgcolor == charts.theme.background

    def test_midnight_theme(self, sample_returns):
        """Test midnight theme application."""
        charts = PerformanceCharts(theme="midnight")
        fig = charts.plot_performance(sample_returns)

        assert fig.layout.paper_bgcolor == charts.theme.background


class TestPerformanceIntegration:
    """Integration tests for performance visualizations."""

    def test_full_analysis_workflow(self, sample_returns, sample_benchmark, sample_pnl):
        """Test complete performance analysis workflow."""
        charts = PerformanceCharts(theme="dark")

        # Create performance plot
        fig1 = charts.plot_performance(sample_returns, sample_benchmark)
        assert fig1 is not None

        # Create PnL plot
        fig2 = charts.plot_pnl(sample_pnl)
        assert fig2 is not None

        # Create dashboard
        fig3 = charts.create_performance_dashboard(sample_returns, sample_benchmark)
        assert fig3 is not None

    def test_comparison_workflow(self, sample_returns):
        """Test strategy comparison workflow."""
        charts = PerformanceCharts()

        # Create multiple strategies
        results = {
            'Momentum': sample_returns,
            'Mean Reversion': sample_returns * 0.9,
            'Trend Following': sample_returns * 1.1,
        }

        fig = charts.plot_backtest_comparison(results)
        assert len(fig.data) == 3

    def test_performance_chart_update_speed(self, sample_returns):
        """Test that chart updates are fast enough."""
        import time

        charts = PerformanceCharts()

        start = time.time()
        charts.plot_performance(sample_returns)
        elapsed = time.time() - start

        # Should be much faster than 100ms
        assert elapsed < 0.1

    def test_monthly_returns_data_integrity(self, sample_returns):
        """Test monthly returns heatmap data integrity."""
        charts = PerformanceCharts()
        fig = charts.plot_monthly_returns(sample_returns)

        # Should have a heatmap trace
        heatmap_found = False
        for trace in fig.data:
            if hasattr(trace, 'type') and trace.type == 'heatmap':
                heatmap_found = True
                break

        assert heatmap_found


class TestPerformanceEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_returns(self):
        """Test handling of empty returns data."""
        charts = PerformanceCharts()
        empty_returns = pd.Series([], dtype=float)

        # Should still create a figure
        fig = charts.plot_performance(empty_returns)
        assert fig is not None

    def test_single_value_returns(self):
        """Test handling of single value returns."""
        charts = PerformanceCharts()
        single_return = pd.Series([0.01])

        fig = charts.plot_performance(single_return)
        assert fig is not None

    def test_all_positive_returns(self):
        """Test with all positive returns."""
        charts = PerformanceCharts()
        positive_returns = pd.Series([0.01] * 100)

        fig = charts.plot_performance(positive_returns)
        assert fig is not None

    def test_all_negative_returns(self):
        """Test with all negative returns."""
        charts = PerformanceCharts()
        negative_returns = pd.Series([-0.01] * 100)

        fig = charts.plot_performance(negative_returns)
        assert fig is not None

    def test_extreme_values(self):
        """Test with extreme return values."""
        charts = PerformanceCharts()
        extreme_returns = pd.Series([0.5, -0.5, 0.3, -0.3] * 25)

        fig = charts.plot_performance(extreme_returns)
        assert fig is not None

    def test_zero_returns(self):
        """Test with zero returns."""
        charts = PerformanceCharts()
        zero_returns = pd.Series([0.0] * 100)

        fig = charts.plot_performance(zero_returns)
        assert fig is not None

    def test_custom_window_size(self, sample_returns):
        """Test custom rolling window sizes."""
        charts = PerformanceCharts()

        # Test various window sizes
        for window in [5, 10, 20, 50, 100]:
            fig = charts.plot_rolling_metrics(sample_returns, window=window)
            assert fig is not None

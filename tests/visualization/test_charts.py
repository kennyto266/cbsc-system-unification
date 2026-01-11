"""
Unit tests for visualization.charts module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from cbsc_strategy_sdk.visualization.charts import (
    ChartBuilder,
    create_sample_data,
)


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data for testing."""
    np.random.seed(42)
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=100),
        periods=100,
        freq='D'
    )

    returns = np.random.normal(0.001, 0.02, 100)
    price = 100 * np.cumprod(1 + returns)
    noise = np.random.normal(0, 0.01, 100)

    data = pd.DataFrame({
        'open': price * (1 + noise * 0.5),
        'high': price * (1 + np.abs(noise)),
        'low': price * (1 - np.abs(noise)),
        'close': price,
        'volume': np.random.randint(1000000, 10000000, 100),
    }, index=dates)

    data['high'] = data[['open', 'close', 'high']].max(axis=1)
    data['low'] = data[['open', 'close', 'low']].min(axis=1)

    return data


@pytest.fixture
def sample_signals():
    """Create sample trading signals."""
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=100),
        periods=100,
        freq='D'
    )

    signals = pd.Series(0, index=dates)
    signals.iloc[10] = 1   # Buy
    signals.iloc[30] = -1  # Sell
    signals.iloc[50] = 1   # Buy
    signals.iloc[70] = -1  # Sell

    return pd.DataFrame({'signal': signals})


class TestChartBuilder:
    """Test ChartBuilder class."""

    def test_init_default_theme(self):
        """Test ChartBuilder initialization with default theme."""
        builder = ChartBuilder()
        assert builder is not None
        assert builder._figure is None

    def test_init_custom_theme(self):
        """Test ChartBuilder initialization with custom theme."""
        builder = ChartBuilder(theme="light")
        assert builder is not None
        assert builder.theme.name == "light"

    def test_init_without_plotly(self, monkeypatch):
        """Test error when Plotly is not available."""
        # Mock Plotly as unavailable
        import sys
        module = type(sys)('cbsc_strategy_sdk.visualization.charts')
        module.PLOTLY_AVAILABLE = False

        with pytest.raises(ImportError, match="Plotly is required"):
            ChartBuilder()

    def test_create_candlestick_basic(self, sample_ohlcv_data):
        """Test basic candlestick chart creation."""
        builder = ChartBuilder()
        fig = builder.create_candlestick(sample_ohlcv_data)

        assert fig is not None
        assert builder._figure is not None
        assert len(fig.data) > 0

    def test_create_candlestick_without_volume(self, sample_ohlcv_data):
        """Test candlestick chart without volume."""
        builder = ChartBuilder()
        fig = builder.create_candlestick(
            sample_ohlcv_data,
            show_volume=False
        )

        assert fig is not None
        assert len(fig.data) == 1  # Only candlestick

    def test_create_candlestick_missing_columns(self):
        """Test error with missing required columns."""
        builder = ChartBuilder()
        incomplete_data = pd.DataFrame({
            'open': [1, 2, 3],
            'high': [4, 5, 6],
        })

        with pytest.raises(ValueError, match="Missing required columns"):
            builder.create_candlestick(incomplete_data)

    def test_plot_signals(self, sample_ohlcv_data, sample_signals):
        """Test signal plotting on chart."""
        builder = ChartBuilder()
        builder.create_candlestick(sample_ohlcv_data)
        fig = builder.plot_signals(sample_ohlcv_data, sample_signals)

        assert fig is not None
        # Should have original traces plus signal markers
        assert len(fig.data) > 2

    def test_plot_signals_without_existing_chart(self, sample_ohlcv_data, sample_signals):
        """Test signal plotting creates chart if none exists."""
        builder = ChartBuilder()
        fig = builder.plot_signals(sample_ohlcv_data, sample_signals)

        assert fig is not None
        assert builder._figure is not None

    def test_add_moving_average(self, sample_ohlcv_data):
        """Test adding moving average to chart."""
        builder = ChartBuilder()
        builder.create_candlestick(sample_ohlcv_data)
        fig = builder.add_moving_average(sample_ohlcv_data, periods=[5, 10, 20])

        assert fig is not None
        # Should have original traces plus MA lines
        assert len(fig.data) >= 4  # Candlestick + volume + 3 MAs

    def test_add_bollinger_bands(self, sample_ohlcv_data):
        """Test adding Bollinger Bands to chart."""
        builder = ChartBuilder()
        builder.create_candlestick(sample_ohlcv_data)
        fig = builder.add_bollinger_bands(sample_ohlcv_data)

        assert fig is not None
        # Should have BB upper, lower, middle
        assert len(fig.data) >= 4

    def test_create_line_chart(self, sample_ohlcv_data):
        """Test line chart creation."""
        builder = ChartBuilder()
        fig = builder.create_line_chart(
            sample_ohlcv_data,
            columns=['close'],
            title="Test Line Chart"
        )

        assert fig is not None
        assert len(fig.data) == 1

    def test_create_line_chart_multiple_columns(self, sample_ohlcv_data):
        """Test line chart with multiple columns."""
        builder = ChartBuilder()
        fig = builder.create_line_chart(
            sample_ohlcv_data,
            columns=['open', 'close', 'high']
        )

        assert fig is not None
        assert len(fig.data) == 3

    def test_export_html(self, sample_ohlcv_data, tmp_path):
        """Test exporting chart to HTML."""
        builder = ChartBuilder()
        builder.create_candlestick(sample_ohlcv_data)

        filepath = tmp_path / "test_chart.html"
        builder.export_html(str(filepath))

        assert filepath.exists()
        # Check file has content
        content = filepath.read_text()
        assert "<!DOCTYPE html>" in content

    def test_export_html_without_figure(self, tmp_path):
        """Test error when exporting without creating figure."""
        builder = ChartBuilder()
        filepath = tmp_path / "test.html"

        with pytest.raises(ValueError, match="No figure to export"):
            builder.export_html(str(filepath))

    def test_get_figure(self, sample_ohlcv_data):
        """Test getting the current figure."""
        builder = ChartBuilder()
        assert builder.get_figure() is None

        builder.create_candlestick(sample_ohlcv_data)
        assert builder.get_figure() is not None


class TestCreateSampleData:
    """Test create_sample_data function."""

    def test_default_parameters(self):
        """Test sample data with default parameters."""
        data = create_sample_data()

        assert isinstance(data, pd.DataFrame)
        assert len(data) == 100
        assert all(col in data.columns for col in ['open', 'high', 'low', 'close', 'volume'])

    def test_custom_days(self):
        """Test sample data with custom day count."""
        data = create_sample_data(days=50)

        assert len(data) == 50

    def test_data_integrity(self):
        """Test that generated data is valid."""
        data = create_sample_data(days=100)

        # Check high >= max(open, close)
        assert all(data['high'] >= data[['open', 'close']].max(axis=1))

        # Check low <= min(open, close)
        assert all(data['low'] <= data[['open', 'close']].min(axis=1))

        # Check volume is positive
        assert all(data['volume'] > 0)

    def test_datetime_index(self):
        """Test that data has datetime index."""
        data = create_sample_data()

        assert isinstance(data.index, pd.DatetimeIndex)


class TestChartIntegration:
    """Integration tests for chart building workflows."""

    def test_full_chart_workflow(self, sample_ohlcv_data, sample_signals):
        """Test complete chart building workflow."""
        builder = ChartBuilder(theme="midnight")

        # Create candlestick
        fig = builder.create_candlestick(sample_ohlcv_data)

        # Add indicators
        fig = builder.add_moving_average(sample_ohlcv_data, periods=[10, 20])
        fig = builder.add_bollinger_bands(sample_ohlcv_data)

        # Add signals
        fig = builder.plot_signals(sample_ohlcv_data, sample_signals)

        # Verify figure has all traces
        assert len(fig.data) > 10  # Candlestick + volume + MAs + BBs + signals

    def test_performance_chart_update(self, sample_ohlcv_data):
        """Test that chart updates are fast enough (<100ms)."""
        import time

        builder = ChartBuilder()

        start = time.time()
        builder.create_candlestick(sample_ohlcv_data)
        builder.add_moving_average(sample_ohlcv_data)
        builder.add_bollinger_bands(sample_ohlcv_data)
        elapsed = time.time() - start

        # Should be much faster than 100ms
        assert elapsed < 0.1

    def test_theme_application(self, sample_ohlcv_data):
        """Test that themes are applied correctly."""
        builder_dark = ChartBuilder(theme="dark")
        fig_dark = builder_dark.create_candlestick(sample_ohlcv_data)

        builder_light = ChartBuilder(theme="light")
        fig_light = builder_light.create_candlestick(sample_ohlcv_data)

        # Background colors should differ
        assert (
            fig_dark.layout.paper_bgcolor !=
            fig_light.layout.paper_bgcolor
        )

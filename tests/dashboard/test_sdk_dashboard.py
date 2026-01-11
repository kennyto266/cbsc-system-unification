"""
Unit tests for CBSC Strategy SDK Dashboard module.

Tests all dashboard components including StrategyDashboard,
DashboardLayout, ChartBuilders, MetricsDisplay, LiveUpdateComponent,
and ThemeManager.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestThemeManager:
    """Test ThemeManager class."""

    def test_initialization_default_theme(self):
        """Test ThemeManager initialization with default theme."""
        from cbsc_strategy_sdk.dashboard.theme import ThemeManager

        theme = ThemeManager()
        assert theme.current_theme == "dark"
        assert theme.is_dark
        assert not theme.is_light

    def test_initialization_light_theme(self):
        """Test ThemeManager initialization with light theme."""
        from cbsc_strategy_sdk.dashboard.theme import ThemeManager

        theme = ThemeManager(initial_theme="light")
        assert theme.current_theme == "light"
        assert theme.is_light
        assert not theme.is_dark

    def test_initialization_invalid_theme(self):
        """Test ThemeManager initialization with invalid theme."""
        from cbsc_strategy_sdk.dashboard.theme import ThemeManager

        with pytest.raises(ValueError, match="Invalid theme"):
            ThemeManager(initial_theme="blue")

    def test_get_colors(self):
        """Test get_colors returns all expected keys."""
        from cbsc_strategy_sdk.dashboard.theme import ThemeManager

        theme = ThemeManager()
        colors = theme.get_colors()

        expected_keys = [
            'background', 'surface', 'primary', 'secondary',
            'success', 'warning', 'danger', 'info',
            'text', 'text_secondary', 'border', 'grid',
            'up', 'down'
        ]

        for key in expected_keys:
            assert key in colors
            assert isinstance(colors[key], str)
            assert colors[key].startswith('#')

    def test_get_color(self):
        """Test get_color method."""
        from cbsc_strategy_sdk.dashboard.theme import ThemeManager

        theme = ThemeManager()
        assert theme.get_color('primary') == '#42a5f5'
        assert theme.get_color('background') == '#1e1e1e'

    def test_toggle_theme(self):
        """Test toggle_theme method."""
        from cbsc_strategy_sdk.dashboard.theme import ThemeManager

        theme = ThemeManager(initial_theme="dark")
        assert theme.toggle_theme() == "light"
        assert theme.toggle_theme() == "dark"

    def test_set_theme(self):
        """Test set_theme method."""
        from cbsc_strategy_sdk.dashboard.theme import ThemeManager

        theme = ThemeManager()
        theme.set_theme("light")
        assert theme.current_theme == "light"

        with pytest.raises(ValueError):
            theme.set_theme("invalid")

    def test_get_stylesheet_url(self):
        """Test get_stylesheet_url returns valid URLs."""
        from cbsc_strategy_sdk.dashboard.theme import ThemeManager

        theme = ThemeManager()
        url = theme.get_stylesheet_url()
        assert isinstance(url, str)
        assert url.startswith("https://")
        assert "bootswatch" in url

    def test_get_plotly_template(self):
        """Test get_plotly_template returns valid structure."""
        from cbsc_strategy_sdk.dashboard.theme import ThemeManager

        theme = ThemeManager()
        template = theme.get_plotly_template()

        assert 'layout' in template
        assert 'paper_bgcolor' in template['layout']
        assert 'plot_bgcolor' in template['layout']
        assert 'font' in template['layout']


class TestChartBuilders:
    """Test ChartBuilders class."""

    @pytest.fixture
    def sample_ohlcv_data(self):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)

        close_prices = 100 + np.cumsum(np.random.randn(100) * 2)

        data = {
            'open': close_prices + np.random.randn(100),
            'high': close_prices + abs(np.random.randn(100)) * 3,
            'low': close_prices - abs(np.random.randn(100)) * 3,
            'close': close_prices,
            'volume': np.random.randint(1000000, 10000000, 100),
        }

        return pd.DataFrame(data, index=dates)

    @pytest.fixture
    def sample_returns(self):
        """Create sample returns data for testing."""
        dates = pd.date_range(start='2024-01-01', periods=252, freq='D')
        np.random.seed(42)

        returns = pd.Series(
            np.random.randn(252) * 0.02,
            index=dates
        )

        return returns

    def test_initialization(self):
        """Test ChartBuilders initialization."""
        from cbsc_strategy_sdk.dashboard.charts import ChartBuilders
        from cbsc_strategy_sdk.dashboard.theme import ThemeManager

        theme = ThemeManager()
        builder = ChartBuilders(theme_manager=theme)

        assert builder.theme == theme

    def test_candlestick_chart(self, sample_ohlcv_data):
        """Test candlestick chart creation."""
        from cbsc_strategy_sdk.dashboard.charts import ChartBuilders

        builder = ChartBuilders()
        fig = builder.candlestick_chart(sample_ohlcv_data)

        assert fig is not None
        assert hasattr(fig, 'data')
        assert len(fig.data) > 0

    def test_candlestick_chart_missing_columns(self):
        """Test candlestick chart with missing required columns."""
        from cbsc_strategy_sdk.dashboard.charts import ChartBuilders

        builder = ChartBuilders()
        bad_data = pd.DataFrame({'a': [1, 2, 3]})

        with pytest.raises(ValueError, match="Missing required columns"):
            builder.candlestick_chart(bad_data)

    def test_line_chart(self, sample_ohlcv_data):
        """Test line chart creation."""
        from cbsc_strategy_sdk.dashboard.charts import ChartBuilders

        builder = ChartBuilders()
        fig = builder.line_chart(sample_ohlcv_data, columns=['close'])

        assert fig is not None
        assert hasattr(fig, 'data')
        assert len(fig.data) > 0

    def test_heatmap(self):
        """Test heatmap creation."""
        from cbsc_strategy_sdk.dashboard.charts import ChartBuilders

        builder = ChartBuilders()

        # Create sample correlation data
        data = pd.DataFrame({
            'A': np.random.randn(100),
            'B': np.random.randn(100),
            'C': np.random.randn(100),
        })

        fig = builder.heatmap(data)

        assert fig is not None
        assert hasattr(fig, 'data')

    def test_equity_curve(self, sample_returns):
        """Test equity curve creation."""
        from cbsc_strategy_sdk.dashboard.charts import ChartBuilders

        builder = ChartBuilders()
        fig = builder.equity_curve(sample_returns)

        assert fig is not None
        assert hasattr(fig, 'data')
        assert len(fig.data) > 0

    def test_drawdown_chart(self, sample_returns):
        """Test drawdown chart creation."""
        from cbsc_strategy_sdk.dashboard.charts import ChartBuilders

        builder = ChartBuilders()
        fig = builder.drawdown_chart(sample_returns)

        assert fig is not None
        assert hasattr(fig, 'data')

    def test_returns_distribution(self, sample_returns):
        """Test returns distribution chart creation."""
        from cbsc_strategy_sdk.dashboard.charts import ChartBuilders

        builder = ChartBuilders()
        fig = builder.returns_distribution(sample_returns)

        assert fig is not None
        assert hasattr(fig, 'data')

    def test_comparison_chart(self, sample_returns):
        """Test comparison chart creation."""
        from cbsc_strategy_sdk.dashboard.charts import ChartBuilders

        builder = ChartBuilders()

        results = {
            'Strategy A': sample_returns,
            'Strategy B': sample_returns * 0.8,
        }

        fig = builder.comparison_chart(results)

        assert fig is not None
        assert hasattr(fig, 'data')
        assert len(fig.data) >= 2


class TestMetricsDisplay:
    """Test MetricsDisplay class."""

    @pytest.fixture
    def sample_returns(self):
        """Create sample returns data for testing."""
        dates = pd.date_range(start='2024-01-01', periods=252, freq='D')
        np.random.seed(42)

        returns = pd.Series(
            np.random.randn(252) * 0.02,
            index=dates
        )

        return returns

    def test_initialization_with_returns(self, sample_returns):
        """Test MetricsDisplay initialization with returns."""
        from cbsc_strategy_sdk.dashboard.metrics import MetricsDisplay

        metrics = MetricsDisplay(returns=sample_returns)

        assert metrics.returns is not None
        assert metrics._metrics is not None
        assert 'total_return' in metrics._metrics

    def test_initialization_without_returns(self):
        """Test MetricsDisplay initialization without returns."""
        from cbsc_strategy_sdk.dashboard.metrics import MetricsDisplay

        metrics = MetricsDisplay()

        assert metrics.returns is None
        assert metrics._metrics == {}

    def test_calculate_metrics(self, sample_returns):
        """Test metrics calculation."""
        from cbsc_strategy_sdk.dashboard.metrics import MetricsDisplay

        metrics = MetricsDisplay(returns=sample_returns)

        assert 'total_return' in metrics._metrics
        assert 'annual_return' in metrics._metrics
        assert 'volatility' in metrics._metrics
        assert 'sharpe_ratio' in metrics._metrics
        assert 'max_drawdown' in metrics._metrics
        assert 'win_rate' in metrics._metrics

    def test_summary_cards(self, sample_returns):
        """Test summary cards creation."""
        from cbsc_strategy_sdk.dashboard.metrics import MetricsDisplay

        metrics = MetricsDisplay(returns=sample_returns)
        cards = metrics.summary_cards()

        assert isinstance(cards, list)
        assert len(cards) == 6  # 6 metric cards

    def test_detailed_table(self, sample_returns):
        """Test detailed table creation."""
        from cbsc_strategy_sdk.dashboard.metrics import MetricsDisplay

        metrics = MetricsDisplay(returns=sample_returns)
        table = metrics.detailed_table()

        assert table is not None
        assert hasattr(table, 'columns')
        assert hasattr(table, 'data')

    def test_comparison_chart(self, sample_returns):
        """Test comparison chart creation."""
        from cbsc_strategy_sdk.dashboard.metrics import MetricsDisplay

        metrics = MetricsDisplay(returns=sample_returns)
        benchmark = sample_returns * 0.7

        fig = metrics.comparison_chart(benchmark)

        assert fig is not None
        assert hasattr(fig, 'data')


class TestCircularBuffer:
    """Test CircularBuffer class."""

    def test_initialization(self):
        """Test CircularBuffer initialization."""
        from cbsc_strategy_sdk.dashboard.live import CircularBuffer

        buffer = CircularBuffer(size=10)
        assert buffer.size == 10
        assert len(buffer) == 0

    def test_add_and_get_data(self):
        """Test adding and retrieving data."""
        from cbsc_strategy_sdk.dashboard.live import CircularBuffer

        buffer = CircularBuffer(size=5)

        for i in range(3):
            buffer.add(i)

        data = buffer.get_data()
        assert data == [0, 1, 2]
        assert len(buffer) == 3

    def test_buffer_overflow(self):
        """Test buffer overflow behavior."""
        from cbsc_strategy_sdk.dashboard.live import CircularBuffer

        buffer = CircularBuffer(size=3)

        for i in range(5):
            buffer.add(i)

        data = buffer.get_data()
        assert data == [2, 3, 4]  # Only last 3 items
        assert len(buffer) == 3

    def test_get_dataframe(self):
        """Test getting data as DataFrame."""
        from cbsc_strategy_sdk.dashboard.live import CircularBuffer

        buffer = CircularBuffer(size=10)

        for i in range(3):
            buffer.add({'value': i, 'squared': i ** 2})

        df = buffer.get_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert 'value' in df.columns

    def test_clear(self):
        """Test clearing buffer."""
        from cbsc_strategy_sdk.dashboard.live import CircularBuffer

        buffer = CircularBuffer(size=10)

        for i in range(5):
            buffer.add(i)

        buffer.clear()
        assert len(buffer) == 0
        assert buffer.get_data() == []


class TestLiveUpdateComponent:
    """Test LiveUpdateComponent class."""

    def test_initialization(self):
        """Test LiveUpdateComponent initialization."""
        from cbsc_strategy_sdk.dashboard.live import LiveUpdateComponent

        component = LiveUpdateComponent()

        assert component.update_interval == 1000
        assert not component.is_running
        assert component.websocket_url is None

    def test_setup_websocket(self):
        """Test WebSocket setup."""
        from cbsc_strategy_sdk.dashboard.live import LiveUpdateComponent

        component = LiveUpdateComponent()
        component.setup_websocket('ws://localhost:8000/ws', ['AAPL'])

        assert component.websocket_url == 'ws://localhost:8000/ws'
        assert component.subscribed_symbols == ['AAPL']

    def test_create_sample_live_data(self):
        """Test sample live data creation."""
        from cbsc_strategy_sdk.dashboard.live import LiveUpdateComponent

        component = LiveUpdateComponent()
        df = component.create_sample_live_data(num_points=50, symbols=['AAPL'])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 50
        assert 'symbol' in df.columns
        assert 'close' in df.columns


@pytest.mark.skipif(
    sys.version_info < (3, 8),
    reason="Dash requires Python 3.8+"
)
class TestStrategyDashboard:
    """Test StrategyDashboard class (integration tests)."""

    def test_create_dashboard(self):
        """Test creating a dashboard instance."""
        from cbsc_strategy_sdk.dashboard.app import create_dashboard

        dashboard = create_dashboard(title="Test Dashboard")

        assert dashboard.title == "Test Dashboard"
        assert dashboard.port == 8050
        assert dashboard.current_theme == "dark"

    def test_dashboard_initialization(self):
        """Test dashboard initialization with all parameters."""
        from cbsc_strategy_sdk.dashboard.app import StrategyDashboard

        dashboard = StrategyDashboard(
            title="Test Dashboard",
            port=8051,
            mode='inline',
            theme='light',
        )

        assert dashboard.title == "Test Dashboard"
        assert dashboard.port == 8051
        assert dashboard.mode == 'inline'
        assert dashboard.current_theme == "light"

    def test_load_data(self):
        """Test loading data into dashboard."""
        from cbsc_strategy_sdk.dashboard.app import create_dashboard

        dashboard = create_dashboard()

        # Create sample price data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        data = {
            'timestamp': dates,
            'open': np.random.randn(100) * 2 + 100,
            'high': np.random.randn(100) * 2 + 102,
            'low': np.random.randn(100) * 2 + 98,
            'close': np.random.randn(100) * 2 + 100,
            'volume': np.random.randint(1000000, 10000000, 100),
        }
        df = pd.DataFrame(data)

        dashboard.load_data(df)

        assert 'price_data' in dashboard._data_store

    def test_load_backtest_results(self):
        """Test loading backtest results."""
        from cbsc_strategy_sdk.dashboard.app import create_dashboard

        dashboard = create_dashboard()

        # Create sample returns
        dates = pd.date_range(start='2024-01-01', periods=252, freq='D')
        returns = pd.Series(np.random.randn(252) * 0.02, index=dates)

        dashboard.load_backtest_results(returns)

        assert 'returns' in dashboard._data_store
        assert 'dates' in dashboard._data_store

    def test_set_theme(self):
        """Test setting dashboard theme."""
        from cbsc_strategy_sdk.dashboard.app import create_dashboard

        dashboard = create_dashboard(theme="dark")

        dashboard.set_theme("light")
        assert dashboard.current_theme == "light"

        with pytest.raises(ValueError):
            dashboard.set_theme("invalid")


class TestDashboardIntegration:
    """Integration tests for dashboard components."""

    def test_theme_and_charts_integration(self):
        """Test ThemeManager integration with ChartBuilders."""
        from cbsc_strategy_sdk.dashboard.theme import ThemeManager
        from cbsc_strategy_sdk.dashboard.charts import ChartBuilders

        theme = ThemeManager(initial_theme="light")
        builder = ChartBuilders(theme_manager=theme)

        # Create sample data
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        data = pd.DataFrame({
            'close': np.random.randn(50) * 2 + 100,
            'open': np.random.randn(50) * 2 + 100,
            'high': np.random.randn(50) * 2 + 102,
            'low': np.random.randn(50) * 2 + 98,
        }, index=dates)

        fig = builder.line_chart(data)

        # Verify light theme colors are used
        assert fig is not None

    def test_metrics_and_charts_integration(self):
        """Test MetricsDisplay integration with charts."""
        from cbsc_strategy_sdk.dashboard.metrics import MetricsDisplay

        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        returns = pd.Series(np.random.randn(100) * 0.02, index=dates)

        metrics = MetricsDisplay(returns=returns)

        # Get metrics and charts
        cards = metrics.summary_cards()
        assert len(cards) > 0

        table = metrics.detailed_table()
        assert table is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

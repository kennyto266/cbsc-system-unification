"""
Tests for fundamental strategies using economic indicators
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from ..fundamental_strategies import (
    HIBORStrategy,
    GDPGrowthStrategy,
    VisitorArrivalStrategy,
    PMIStrategy,
    UnemploymentStrategy,
    CompositeEconomicStrategy
)


class TestHIBORStrategy:
    """Test cases for HIBOR Strategy"""

    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data with HIBOR rates"""
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        np.random.seed(42)

        # Create price data
        prices = 100 + np.cumsum(np.random.randn(100) * 0.5)

        # Create HIBOR rate data
        hibor_rates = 4.0 + np.sin(np.linspace(0, 4*np.pi, 100)) * 1.5
        hibor_rates += np.random.normal(0, 0.2, 100)
        hibor_rates = np.clip(hibor_rates, 1.0, 8.0)

        data = pd.DataFrame({
            'open': prices * (1 + np.random.randn(100) * 0.001),
            'high': prices * (1 + np.abs(np.random.randn(100) * 0.01)),
            'low': prices * (1 - np.abs(np.random.randn(100) * 0.01)),
            'close': prices,
            'volume': np.random.randint(10000, 100000, 100),
            'hibor_rate': hibor_rates
        }, index=dates)

        return data

    def test_initialization(self):
        """Test strategy initialization"""
        strategy = HIBORStrategy(
            lookback_period=20,
            rate_threshold_high=5.0,
            rate_threshold_low=2.5
        )

        assert strategy.lookback_period == 20
        assert strategy.rate_threshold_high == 5.0
        assert strategy.rate_threshold_low == 2.5
        assert strategy.data_column == 'hibor_rate'

    def test_calculate_rate_momentum(self, sample_data):
        """Test HIBOR rate momentum calculation"""
        strategy = HIBORStrategy(lookback_period=10)
        momentum = strategy.calculate_rate_momentum(sample_data)

        assert isinstance(momentum, pd.Series)
        assert len(momentum) == len(sample_data)
        assert momentum.notna().sum() > 0

    def test_generate_signals(self, sample_data):
        """Test signal generation"""
        strategy = HIBORStrategy()
        signals = strategy.generate_signals(sample_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)

        # Check signal values
        unique_signals = signals.unique()
        assert all(s in [-1, 0, 1] for s in unique_signals if pd.notna(s))

    def test_get_required_columns(self):
        """Test required columns"""
        strategy = HIBORStrategy()
        columns = strategy.get_required_columns()

        assert 'hibor_rate' in columns


class TestGDPGrowthStrategy:
    """Test cases for GDP Growth Strategy"""

    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data with GDP data"""
        dates = pd.date_range(start="2020-01-01", periods=200, freq="D")
        np.random.seed(42)

        # Create price data with economic cycle
        gdp_cycle = np.sin(np.linspace(0, 2*np.pi, 200)) * 20
        trend = np.linspace(100, 150, 200)
        prices = trend + gdp_cycle + np.random.randn(200) * 2

        # Create GDP growth data (quarterly, resampled to daily)
        gdp_growth = 2.5 + np.sin(np.linspace(0, 2*np.pi, 200/60)) * 3.0
        gdp_growth = np.repeat(gdp_growth, 60)[:200] + np.random.normal(0, 0.5, 200)

        data = pd.DataFrame({
            'open': prices * (1 + np.random.randn(200) * 0.001),
            'high': prices * (1 + np.abs(np.random.randn(200) * 0.01)),
            'low': prices * (1 - np.abs(np.random.randn(200) * 0.01)),
            'close': prices,
            'volume': np.random.randint(10000, 100000, 200),
            'gdp_growth': gdp_growth
        }, index=dates)

        return data

    def test_initialization(self):
        """Test strategy initialization"""
        strategy = GDPGrowthStrategy(
            gdp_threshold_high=4.0,
            gdp_threshold_low=1.0
        )

        assert strategy.gdp_threshold_high == 4.0
        assert strategy.gdp_threshold_low == 1.0

    def test_identify_economic_cycle(self, sample_data):
        """Test economic cycle identification"""
        strategy = GDPGrowthStrategy()
        cycles = strategy.identify_economic_cycle(sample_data)

        assert isinstance(cycles, pd.Series)
        assert len(cycles) == len(sample_data)

        # Check cycle values
        unique_cycles = cycles.unique()
        valid_cycles = {'expansion', 'recession', 'neutral', np.nan}
        assert all(c in valid_cycles for c in unique_cycles)

    def test_generate_signals(self, sample_data):
        """Test signal generation"""
        strategy = GDPGrowthStrategy()
        signals = strategy.generate_signals(sample_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)


class TestVisitorArrivalStrategy:
    """Test cases for Visitor Arrival Strategy"""

    @pytest.fixture
    def sample_data(self):
        """Create sample data with visitor arrival numbers"""
        dates = pd.date_range(start="2023-01-01", periods=365, freq="D")
        np.random.seed(42)

        # Create price data for tourism stocks
        seasonal_pattern = 1.0 + 0.3 * np.sin(np.linspace(0, 2*np.pi, 365))
        trend = np.linspace(100, 120, 365)
        prices = trend * seasonal_pattern + np.random.randn(365) * 2

        # Create visitor arrival data
        base_visitors = 4.5  # million
        visitors = base_visitors * seasonal_pattern + np.random.normal(0, 0.5, 365)

        data = pd.DataFrame({
            'open': prices * (1 + np.random.randn(365) * 0.001),
            'high': prices * (1 + np.abs(np.random.randn(365) * 0.01)),
            'low': prices * (1 - np.abs(np.random.randn(365) * 0.01)),
            'close': prices,
            'volume': np.random.randint(10000, 100000, 365),
            'visitor_arrivals': visitors * 1e6  # Convert to actual numbers
        }, index=dates)

        return data

    def test_initialization(self):
        """Test strategy initialization"""
        strategy = VisitorArrivalStrategy(
            trend_period=90,
            change_threshold=0.05
        )

        assert strategy.trend_period == 90
        assert strategy.change_threshold == 0.05

    def test_calculate_visitor_trend(self, sample_data):
        """Test visitor trend calculation"""
        strategy = VisitorArrivalStrategy(trend_period=30)
        trend = strategy.calculate_visitor_trend(sample_data)

        assert isinstance(trend, pd.Series)
        assert len(trend) == len(sample_data)

    def test_generate_signals(self, sample_data):
        """Test signal generation"""
        strategy = VisitorArrivalStrategy()
        signals = strategy.generate_signals(sample_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)


class TestPMIStrategy:
    """Test cases for PMI Strategy"""

    @pytest.fixture
    def sample_data(self):
        """Create sample data with PMI values"""
        dates = pd.date_range(start="2023-01-01", periods=180, freq="D")
        np.random.seed(42)

        # Create price data
        prices = 100 + np.cumsum(np.random.randn(180) * 0.5)

        # Create PMI data (monthly, resampled to daily)
        pmi_values = 50 + 10 * np.sin(np.linspace(0, 3*np.pi, 180/30))
        pmi_values = np.repeat(pmi_values, 30)[:180] + np.random.normal(0, 2, 180)

        data = pd.DataFrame({
            'open': prices * (1 + np.random.randn(180) * 0.001),
            'high': prices * (1 + np.abs(np.random.randn(180) * 0.01)),
            'low': prices * (1 - np.abs(np.random.randn(180) * 0.01)),
            'close': prices,
            'volume': np.random.randint(10000, 100000, 180),
            'pmi_manufacturing': pmi_values
        }, index=dates)

        return data

    def test_initialization(self):
        """Test strategy initialization"""
        strategy = PMIStrategy(
            expansion_threshold=50.0,
            contraction_threshold=45.0
        )

        assert strategy.expansion_threshold == 50.0
        assert strategy.contraction_threshold == 45.0

    def test_interpret_pmi_level(self, sample_data):
        """Test PMI level interpretation"""
        strategy = PMIStrategy()
        interpretation = strategy.interpret_pmi_level(sample_data)

        assert isinstance(interpretation, pd.Series)
        assert len(interpretation) == len(sample_data)

    def test_generate_signals(self, sample_data):
        """Test signal generation"""
        strategy = PMIStrategy()
        signals = strategy.generate_signals(sample_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)


class TestUnemploymentStrategy:
    """Test cases for Unemployment Strategy"""

    @pytest.fixture
    def sample_data(self):
        """Create sample data with unemployment data"""
        dates = pd.date_range(start="2023-01-01", periods=120, freq="D")
        np.random.seed(42)

        # Create price data
        prices = 100 + np.cumsum(np.random.randn(120) * 0.5)

        # Create unemployment data (monthly, resampled to daily)
        unemployment = 4.5 + 2.0 * np.sin(np.linspace(0, 2*np.pi, 120/30))
        unemployment = np.repeat(unemployment, 30)[:120] + np.random.normal(0, 0.2, 120)

        data = pd.DataFrame({
            'open': prices * (1 + np.random.randn(120) * 0.001),
            'high': prices * (1 + np.abs(np.random.randn(120) * 0.01)),
            'low': prices * (1 - np.abs(np.random.randn(120) * 0.01)),
            'close': prices,
            'volume': np.random.randint(10000, 100000, 120),
            'unemployment_rate': unemployment
        }, index=dates)

        return data

    def test_initialization(self):
        """Test strategy initialization"""
        strategy = UnemploymentStrategy(
            lookback_period=60,
            change_threshold=0.25
        )

        assert strategy.lookback_period == 60
        assert strategy.change_threshold == 0.25

    def test_calculate_unemployment_trend(self, sample_data):
        """Test unemployment trend calculation"""
        strategy = UnemploymentStrategy(lookback_period=30)
        trend = strategy.calculate_unemployment_trend(sample_data)

        assert isinstance(trend, pd.Series)
        assert len(trend) == len(sample_data)

    def test_generate_signals(self, sample_data):
        """Test signal generation"""
        strategy = UnemploymentStrategy()
        signals = strategy.generate_signals(sample_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)


class TestCompositeEconomicStrategy:
    """Test cases for Composite Economic Strategy"""

    @pytest.fixture
    def sample_data(self):
        """Create sample data with all economic indicators"""
        dates = pd.date_range(start="2023-01-01", periods=150, freq="D")
        np.random.seed(42)

        # Create price data
        prices = 100 + np.cumsum(np.random.randn(150) * 0.5)

        # Create all economic indicators
        hibor_rates = 4.0 + np.sin(np.linspace(0, 4*np.pi, 150)) * 1.5
        gdp_growth = 2.5 + np.sin(np.linspace(0, 2*np.pi, 150/60)) * 3.0
        pmi_values = 50 + 10 * np.sin(np.linspace(0, 3*np.pi, 150/30))
        unemployment = 4.5 + 2.0 * np.sin(np.linspace(0, 2*np.pi, 150/30))

        # Resample to daily frequency
        gdp_growth = np.repeat(gdp_growth, 60)[:150]
        pmi_values = np.repeat(pmi_values, 30)[:150]
        unemployment = np.repeat(unemployment, 30)[:150]

        data = pd.DataFrame({
            'open': prices * (1 + np.random.randn(150) * 0.001),
            'high': prices * (1 + np.abs(np.random.randn(150) * 0.01)),
            'low': prices * (1 - np.abs(np.random.randn(150) * 0.01)),
            'close': prices,
            'volume': np.random.randint(10000, 100000, 150),
            'hibor_rate': hibor_rates,
            'gdp_growth': gdp_growth,
            'pmi_manufacturing': pmi_values,
            'unemployment_rate': unemployment
        }, index=dates)

        return data

    def test_initialization(self):
        """Test strategy initialization"""
        strategy = CompositeEconomicStrategy(
            hibor_weight=0.25,
            gdp_weight=0.25,
            pmi_weight=0.25,
            unemployment_weight=0.25
        )

        assert strategy.hibor_weight == 0.25
        assert strategy.gdp_weight == 0.25
        assert strategy.pmi_weight == 0.25
        assert strategy.unemployment_weight == 0.25
        assert abs(sum([strategy.hibor_weight, strategy.gdp_weight,
                       strategy.pmi_weight, strategy.unemployment_weight]) - 1.0) < 1e-6

    def test_calculate_composite_signal(self, sample_data):
        """Test composite signal calculation"""
        strategy = CompositeEconomicStrategy()
        composite = strategy.calculate_composite_signal(sample_data)

        assert isinstance(composite, pd.Series)
        assert len(composite) == len(sample_data)

        # Check composite values are bounded
        assert composite.min() >= -1.0
        assert composite.max() <= 1.0

    def test_generate_signals(self, sample_data):
        """Test signal generation"""
        strategy = CompositeEconomicStrategy()
        signals = strategy.generate_signals(sample_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)

    def test_get_required_columns(self):
        """Test required columns"""
        strategy = CompositeEconomicStrategy()
        columns = strategy.get_required_columns()

        required = ['hibor_rate', 'gdp_growth', 'pmi_manufacturing', 'unemployment_rate']
        for col in required:
            assert col in columns

    @patch('src.strategies.fundamental_strategies.get_economic_data_adapter')
    def test_with_economic_data_adapter(self, mock_get_adapter):
        """Test with mocked economic data adapter"""
        # Mock the adapter and its data
        mock_adapter = Mock()
        mock_data = pd.DataFrame({
            'hibor_rate': [4.0, 4.1, 4.2],
            'gdp_growth': [2.5, 2.6, 2.7],
            'pmi_manufacturing': [50, 51, 52],
            'unemployment_rate': [4.5, 4.4, 4.3]
        })
        mock_adapter.get_all_economic_data.return_value = mock_data
        mock_get_adapter.return_value = mock_adapter

        # Create basic price data
        dates = pd.date_range(start="2023-01-01", periods=3, freq="D")
        price_data = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'close': [100, 101, 102],
            'volume': [50000, 55000, 60000]
        }, index=dates)

        strategy = CompositeEconomicStrategy()
        signals = strategy.generate_signals(price_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(price_data)
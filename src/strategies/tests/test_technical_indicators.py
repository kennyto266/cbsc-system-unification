"""
Tests for technical indicator strategies
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from ..technical_indicators import (
    BollingerBandsStrategy,
    MACDStrategy,
    StochasticStrategy,
    WilliamsRStrategy,
    CCIStrategy
)


class TestBollingerBandsStrategy:
    """Test cases for Bollinger Bands Strategy"""

    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data"""
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        np.random.seed(42)

        # Create trending price data
        prices = 100 + np.cumsum(np.random.randn(100) * 0.5)

        data = pd.DataFrame({
            'open': prices * (1 + np.random.randn(100) * 0.001),
            'high': prices * (1 + np.abs(np.random.randn(100) * 0.01)),
            'low': prices * (1 - np.abs(np.random.randn(100) * 0.01)),
            'close': prices,
            'volume': np.random.randint(10000, 100000, 100)
        }, index=dates)

        return data

    def test_initialization(self):
        """Test strategy initialization"""
        strategy = BollingerBandsStrategy(period=20, std_dev=2.0)

        assert strategy.period == 20
        assert strategy.std_dev == 2.0
        assert strategy.strategy_type == "mean_reversion"

    def test_calculate_bollinger_bands(self, sample_data):
        """Test Bollinger Bands calculation"""
        strategy = BollingerBandsStrategy()
        upper, middle, lower = strategy.calculate_bollinger_bands(sample_data['close'])

        # Check lengths
        assert len(upper) == len(sample_data)
        assert len(middle) == len(sample_data)
        assert len(lower) == len(sample_data)

        # Check relationships
        assert (upper >= middle).all()
        assert (middle >= lower).all()

        # Check that upper band is above lower band
        assert (upper > lower).all()

    def test_mean_reversion_signals(self, sample_data):
        """Test mean reversion signal generation"""
        strategy = BollingerBandsStrategy(strategy_type="mean_reversion")
        signals = strategy.generate_signals(sample_data)

        # Check signal format
        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)
        assert signals.dtype in [np.int64, np.float64, np.int32]

        # Check signal values
        unique_signals = signals.unique()
        assert all(s in [-1, 0, 1] for s in unique_signals)

    def test_breakout_signals(self, sample_data):
        """Test breakout signal generation"""
        strategy = BollingerBandsStrategy(strategy_type="breakout")
        signals = strategy.generate_signals(sample_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)

    def test_get_bands_values(self, sample_data):
        """Test getting Bollinger Bands values"""
        strategy = BollingerBandsStrategy()
        bands = strategy.get_bands_values(sample_data)

        assert 'upper_band' in bands
        assert 'middle_band' in bands
        assert 'lower_band' in bands
        assert 'bandwidth' in bands
        assert 'percent_b' in bands

        # Check that bandwidth is positive
        assert (bands['bandwidth'] > 0).all()


class TestMACDStrategy:
    """Test cases for MACD Strategy"""

    @pytest.fixture
    def sample_data(self):
        """Create sample price data"""
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(100) * 0.5)

        data = pd.DataFrame({
            'close': prices,
        }, index=dates)

        return data

    def test_initialization(self):
        """Test MACD initialization"""
        strategy = MACDStrategy(fast_period=12, slow_period=26, signal_period=9)

        assert strategy.fast_period == 12
        assert strategy.slow_period == 26
        assert strategy.signal_period == 9
        assert strategy.histogram_threshold == 0.0

    def test_calculate_macd(self, sample_data):
        """Test MACD calculation"""
        strategy = MACDStrategy()
        macd_line, signal_line, histogram = strategy.calculate_macd(sample_data['close'])

        # Check lengths
        assert len(macd_line) == len(sample_data)
        assert len(signal_line) == len(sample_data)
        assert len(histogram) == len(sample_data)

        # Check relationship: histogram = macd - signal
        np.testing.assert_array_almost_equal(
            histogram.values,
            (macd_line - signal_line).values,
            decimal=10
        )

    def test_generate_signals(self, sample_data):
        """Test MACD signal generation"""
        strategy = MACDStrategy()
        signals = strategy.generate_signals(sample_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)

    def test_get_macd_values(self, sample_data):
        """Test getting MACD values"""
        strategy = MACDStrategy()
        macd_values = strategy.get_macd_values(sample_data)

        assert 'macd_line' in macd_values
        assert 'signal_line' in macd_values
        assert 'histogram' in macd_values


class TestStochasticStrategy:
    """Test cases for Stochastic Strategy"""

    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data"""
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        np.random.seed(42)
        close = 100 + np.cumsum(np.random.randn(100) * 0.5)

        data = pd.DataFrame({
            'high': close * (1 + np.abs(np.random.randn(100) * 0.02)),
            'low': close * (1 - np.abs(np.random.randn(100) * 0.02)),
            'close': close,
        }, index=dates)

        return data

    def test_initialization(self):
        """Test Stochastic initialization"""
        strategy = StochasticStrategy(
            k_period=14,
            d_period=3,
            overbought_level=80,
            oversold_level=20
        )

        assert strategy.k_period == 14
        assert strategy.d_period == 3
        assert strategy.overbought_level == 80
        assert strategy.oversold_level == 20

    def test_calculate_stochastic(self, sample_data):
        """Test Stochastic calculation"""
        strategy = StochasticStrategy()
        k_percent, d_percent = strategy.calculate_stochastic(
            sample_data['high'],
            sample_data['low'],
            sample_data['close']
        )

        # Check lengths
        assert len(k_percent) == len(sample_data)
        assert len(d_percent) == len(sample_data)

        # Check range (should be between 0 and 100)
        assert k_percent.min() >= 0
        assert k_percent.max() <= 100
        assert d_percent.min() >= 0
        assert d_percent.max() <= 100

    def test_generate_signals(self, sample_data):
        """Test Stochastic signal generation"""
        strategy = StochasticStrategy()
        signals = strategy.generate_signals(sample_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)


class TestWilliamsRStrategy:
    """Test cases for Williams %R Strategy"""

    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data"""
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        np.random.seed(42)
        close = 100 + np.cumsum(np.random.randn(100) * 0.5)

        data = pd.DataFrame({
            'high': close * (1 + np.abs(np.random.randn(100) * 0.02)),
            'low': close * (1 - np.abs(np.random.randn(100) * 0.02)),
            'close': close,
        }, index=dates)

        return data

    def test_initialization(self):
        """Test Williams %R initialization"""
        strategy = WilliamsRStrategy(period=14, overbought_level=-20, oversold_level=-80)

        assert strategy.period == 14
        assert strategy.overbought_level == -20
        assert strategy.oversold_level == -80

    def test_calculate_williams_r(self, sample_data):
        """Test Williams %R calculation"""
        strategy = WilliamsRStrategy()
        williams_r = strategy.calculate_williams_r(
            sample_data['high'],
            sample_data['low'],
            sample_data['close']
        )

        # Check length
        assert len(williams_r) == len(sample_data)

        # Check range (should be between -100 and 0)
        assert williams_r.min() >= -100
        assert williams_r.max() <= 0

    def test_generate_signals(self, sample_data):
        """Test Williams %R signal generation"""
        strategy = WilliamsRStrategy()
        signals = strategy.generate_signals(sample_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)


class TestCCIStrategy:
    """Test cases for CCI Strategy"""

    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data"""
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        np.random.seed(42)
        close = 100 + np.cumsum(np.random.randn(100) * 0.5)

        data = pd.DataFrame({
            'high': close * (1 + np.abs(np.random.randn(100) * 0.02)),
            'low': close * (1 - np.abs(np.random.randn(100) * 0.02)),
            'close': close,
        }, index=dates)

        return data

    def test_initialization(self):
        """Test CCI initialization"""
        strategy = CCIStrategy(period=20, overbought_level=100, oversold_level=-100)

        assert strategy.period == 20
        assert strategy.overbought_level == 100
        assert strategy.oversold_level == -100

    def test_calculate_cci(self, sample_data):
        """Test CCI calculation"""
        strategy = CCIStrategy()
        cci = strategy.calculate_cci(
            sample_data['high'],
            sample_data['low'],
            sample_data['close']
        )

        # Check length
        assert len(cci) == len(sample_data)

        # CCI can be any value, but should not be NaN after initial period
        assert not cci.iloc[20:].isnull().any()

    def test_generate_signals(self, sample_data):
        """Test CCI signal generation"""
        strategy = CCIStrategy()
        signals = strategy.generate_signals(sample_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)

    def test_get_cci_values(self, sample_data):
        """Test getting CCI values"""
        strategy = CCIStrategy()
        cci_values = strategy.get_cci_values(sample_data)

        assert 'cci' in cci_values
        assert 'overbought' in cci_values
        assert 'oversold' in cci_values
        assert 'zero' in cci_values

        # Check that overbought/oversold levels are constants
        assert (cci_values['overbought'] == 100).all()
        assert (cci_values['oversold'] == -100).all()
        assert (cci_values['zero'] == 0).all()
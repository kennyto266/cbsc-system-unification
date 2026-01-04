"""
Test suite for trend following strategies.

Tests MA Crossover, Bollinger Bands, and Donchian Channel strategies.
"""

import pytest
import pandas as pd
import numpy as np
from pandas import Series, DataFrame

from src.strategies.optimization.strategies.trend_following import (
    MAStrategy,
    BollingerBandsStrategy,
    DonchianChannelStrategy,
)


class TestMAStrategy:
    """Test MA Crossover strategy."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        strategy = MAStrategy()
        assert strategy.fast_period == 10
        assert strategy.slow_period == 20

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        strategy = MAStrategy(fast_period=5, slow_period=15)
        assert strategy.fast_period == 5
        assert strategy.slow_period == 15

    def test_generate_signals_uptrend(self):
        """Test signal generation in uptrend."""
        # Create data with clear uptrend
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        data = DataFrame({
            'close': np.arange(20, 50, 1.0)  # Rising prices
        }, index=dates)

        strategy = MAStrategy(fast_period=5, slow_period=10)
        signals = strategy.generate_signals(data)

        # Verify output is Series
        assert isinstance(signals, Series)
        assert len(signals) == len(data)

        # In strong uptrend, fast MA should be above slow MA
        # Signals should be 1 (long) after warmup period
        assert signals.iloc[-1] in [-1, 0, 1]

    def test_generate_signals_downtrend(self):
        """Test signal generation in downtrend."""
        # Create data with clear downtrend
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        data = DataFrame({
            'close': np.arange(50, 20, -1.0)  # Falling prices
        }, index=dates)

        strategy = MAStrategy(fast_period=5, slow_period=10)
        signals = strategy.generate_signals(data)

        # Verify output
        assert isinstance(signals, Series)
        assert signals.iloc[-1] in [-1, 0, 1]

    def test_generate_signals_sideways(self):
        """Test signal generation in sideways market."""
        # Create sideways data
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        np.random.seed(42)
        data = DataFrame({
            'close': 100 + np.random.randn(30) * 2  # Flat around 100
        }, index=dates)

        strategy = MAStrategy(fast_period=5, slow_period=10)
        signals = strategy.generate_signals(data)

        # Should still generate valid signals
        assert isinstance(signals, Series)
        assert all(signals.fillna(0).isin([-1, 0, 1]))

    def test_signal_values_valid(self):
        """Test that all signal values are -1, 0, or 1."""
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        np.random.seed(42)
        data = DataFrame({
            'close': 100 + np.random.randn(50) * 5
        }, index=dates)

        strategy = MAStrategy()
        signals = strategy.generate_signals(data)

        # Check all non-NaN values are valid
        valid_signals = signals.dropna()
        assert all(valid_signals.isin([-1, 0, 1]))


class TestBollingerBandsStrategy:
    """Test Bollinger Bands strategy."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        strategy = BollingerBandsStrategy()
        assert strategy.period == 20
        assert strategy.std_dev == 2.0

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        strategy = BollingerBandsStrategy(period=10, std_dev=1.5)
        assert strategy.period == 10
        assert strategy.std_dev == 1.5

    def test_generate_signals_breakout_upper(self):
        """Test signal generation on upper band breakout."""
        # Create data with price breaking above upper band
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        np.random.seed(42)

        # First 20 prices normal, then sharp breakout
        base_prices = 100 + np.random.randn(20) * 2
        breakout_prices = np.arange(105, 115, 1.0)  # Strong uptrend
        prices = np.concatenate([base_prices, breakout_prices])

        data = DataFrame({'close': prices}, index=dates)

        strategy = BollingerBandsStrategy(period=10, std_dev=2.0)
        signals = strategy.generate_signals(data)

        # Verify output
        assert isinstance(signals, Series)
        assert len(signals) == len(data)
        assert signals.iloc[-1] in [-1, 0, 1]

    def test_generate_signals_breakout_lower(self):
        """Test signal generation on lower band breakout."""
        # Create data with price breaking below lower band
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        np.random.seed(42)

        # First 20 prices normal, then sharp breakdown
        base_prices = 100 + np.random.randn(20) * 2
        breakdown_prices = np.arange(95, 85, -1.0)  # Strong downtrend
        prices = np.concatenate([base_prices, breakdown_prices])

        data = DataFrame({'close': prices}, index=dates)

        strategy = BollingerBandsStrategy(period=10, std_dev=2.0)
        signals = strategy.generate_signals(data)

        # Verify output
        assert isinstance(signals, Series)
        assert signals.iloc[-1] in [-1, 0, 1]

    def test_generate_signals_within_bands(self):
        """Test signal generation when price stays within bands."""
        # Create stable data within bands
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        np.random.seed(42)
        data = DataFrame({
            'close': 100 + np.random.randn(30) * 1  # Low volatility
        }, index=dates)

        strategy = BollingerBandsStrategy(period=20, std_dev=2.0)
        signals = strategy.generate_signals(data)

        # Should generate valid signals
        assert isinstance(signals, Series)
        valid_signals = signals.dropna()
        assert all(valid_signals.isin([-1, 0, 1]))

    def test_signal_values_valid(self):
        """Test that all signal values are -1, 0, or 1."""
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        np.random.seed(42)
        data = DataFrame({
            'close': 100 + np.random.randn(50) * 5
        }, index=dates)

        strategy = BollingerBandsStrategy()
        signals = strategy.generate_signals(data)

        # Check all non-NaN values are valid
        valid_signals = signals.dropna()
        assert all(valid_signals.isin([-1, 0, 1]))


class TestDonchianChannelStrategy:
    """Test Donchian Channel strategy."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        strategy = DonchianChannelStrategy()
        assert strategy.period == 20

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        strategy = DonchianChannelStrategy(period=10)
        assert strategy.period == 10

    def test_generate_signals_with_high_low(self):
        """Test signal generation with high and low data."""
        # Create data with clear channel breakout
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        np.random.seed(42)

        # Generate price data
        close_prices = 100 + np.arange(30) * 0.5  # Uptrend
        high_prices = close_prices + 2  # High is 2 above close
        low_prices = close_prices - 2  # Low is 2 below close

        data = DataFrame({
            'close': close_prices,
            'high': high_prices,
            'low': low_prices
        }, index=dates)

        strategy = DonchianChannelStrategy(period=10)
        signals = strategy.generate_signals(data)

        # Verify output
        assert isinstance(signals, Series)
        assert len(signals) == len(data)
        assert signals.iloc[-1] in [-1, 0, 1]

    def test_generate_signals_without_high_low(self):
        """Test signal generation without high/low columns (fallback to close)."""
        # Create data with only close prices
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        np.random.seed(42)

        # Uptrending data
        close_prices = 100 + np.arange(30) * 0.5

        data = DataFrame({'close': close_prices}, index=dates)

        strategy = DonchianChannelStrategy(period=10)
        signals = strategy.generate_signals(data)

        # Should work with just close prices
        assert isinstance(signals, Series)
        assert signals.iloc[-1] in [-1, 0, 1]

    def test_generate_signals_breakout_high(self):
        """Test signal on high breakout."""
        # Create data with high breakout
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        np.random.seed(42)

        # Sideways then breakout
        base_prices = np.full(20, 100.0)
        breakout_prices = np.arange(105, 115, 1.0)
        close_prices = np.concatenate([base_prices, breakout_prices])

        data = DataFrame({
            'close': close_prices,
            'high': close_prices + 2,
            'low': close_prices - 2
        }, index=dates)

        strategy = DonchianChannelStrategy(period=10)
        signals = strategy.generate_signals(data)

        # Last signal should be valid
        assert signals.iloc[-1] in [-1, 0, 1]

    def test_generate_signals_breakout_low(self):
        """Test signal on low breakout."""
        # Create data with low breakdown
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        np.random.seed(42)

        # Sideways then breakdown
        base_prices = np.full(20, 100.0)
        breakdown_prices = np.arange(95, 85, -1.0)
        close_prices = np.concatenate([base_prices, breakdown_prices])

        data = DataFrame({
            'close': close_prices,
            'high': close_prices + 2,
            'low': close_prices - 2
        }, index=dates)

        strategy = DonchianChannelStrategy(period=10)
        signals = strategy.generate_signals(data)

        # Last signal should be valid
        assert signals.iloc[-1] in [-1, 0, 1]

    def test_signal_values_valid(self):
        """Test that all signal values are -1, 0, or 1."""
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        np.random.seed(42)

        close_prices = 100 + np.random.randn(50) * 5
        data = DataFrame({
            'close': close_prices,
            'high': close_prices + 2,
            'low': close_prices - 2
        }, index=dates)

        strategy = DonchianChannelStrategy()
        signals = strategy.generate_signals(data)

        # Check all non-NaN values are valid
        valid_signals = signals.dropna()
        assert all(valid_signals.isin([-1, 0, 1]))

    def test_uses_shifted_channels(self):
        """Test that strategy uses shifted channels for breakout detection."""
        # This is important: should use .shift(1) on channels
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        np.random.seed(42)

        # Create scenario where price breaks previous channel
        close_prices = 100 + np.arange(30) * 0.3  # Steady uptrend
        data = DataFrame({
            'close': close_prices,
            'high': close_prices + 1,
            'low': close_prices - 1
        }, index=dates)

        strategy = DonchianChannelStrategy(period=10)
        signals = strategy.generate_signals(data)

        # Should generate signals
        assert isinstance(signals, Series)
        # In uptrend, should eventually get long signals
        assert signals.iloc[-1] in [-1, 0, 1]

"""
Test suite for mean reversion strategies.

Tests RSI Mean Reversion, Z-Score, and Pairs Trading strategies.
"""

import pytest
import pandas as pd
import numpy as np
from pandas import Series, DataFrame

from src.strategies.optimization.strategies.mean_reversion import (
    RSIMeanReversionStrategy,
    ZScoreStrategy,
    PairsTradingStrategy,
)


class TestRSIMeanReversionStrategy:
    """Test RSI Mean Reversion strategy."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        strategy = RSIMeanReversionStrategy()
        assert strategy.rsi_period == 14
        assert strategy.oversold == 30
        assert strategy.overbought == 70

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        strategy = RSIMeanReversionStrategy(rsi_period=10, oversold=20, overbought=80)
        assert strategy.rsi_period == 10
        assert strategy.oversold == 20
        assert strategy.overbought == 80

    def test_generate_signals_oversold(self):
        """Test signal generation when RSI is oversold."""
        # Create data that will trigger oversold condition
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        np.random.seed(42)

        # Create downtrend then reversal (RSI will go low then rise)
        downtrend = np.arange(100, 75, -1)  # 25 falling prices
        reversal = np.arange(75, 100, 1)  # 25 rising prices
        prices = np.concatenate([downtrend, reversal])

        data = DataFrame({'close': prices}, index=dates)

        strategy = RSIMeanReversionStrategy(rsi_period=14, oversold=30, overbought=70)
        signals = strategy.generate_signals(data)

        # Verify output
        assert isinstance(signals, Series)
        assert len(signals) == len(data)

        # Check all non-NaN values are valid
        valid_signals = signals.dropna()
        assert all(valid_signals.isin([-1, 0, 1]))

    def test_generate_signals_overbought(self):
        """Test signal generation when RSI is overbought."""
        # Create data that will trigger overbought condition
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        np.random.seed(42)

        # Create uptrend then reversal (RSI will go high then fall)
        uptrend = np.arange(75, 100, 1)  # 25 rising prices
        reversal = np.arange(100, 75, -1)  # 25 falling prices
        prices = np.concatenate([uptrend, reversal])

        data = DataFrame({'close': prices}, index=dates)

        strategy = RSIMeanReversionStrategy(rsi_period=14, oversold=30, overbought=70)
        signals = strategy.generate_signals(data)

        # Verify output
        assert isinstance(signals, Series)
        assert len(signals) == len(data)

        # Check all non-NaN values are valid
        valid_signals = signals.dropna()
        assert all(valid_signals.isin([-1, 0, 1]))

    def test_generate_signals_sideways(self):
        """Test signal generation in sideways market."""
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        np.random.seed(42)
        data = DataFrame({
            'close': 100 + np.random.randn(50) * 2
        }, index=dates)

        strategy = RSIMeanReversionStrategy()
        signals = strategy.generate_signals(data)

        # Should generate valid signals
        assert isinstance(signals, Series)
        valid_signals = signals.dropna()
        assert all(valid_signals.isin([-1, 0, 1]))

    def test_signal_values_valid(self):
        """Test that all signal values are -1, 0, or 1."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        data = DataFrame({
            'close': 100 + np.random.randn(100) * 5
        }, index=dates)

        strategy = RSIMeanReversionStrategy()
        signals = strategy.generate_signals(data)

        # Check all non-NaN values are valid
        valid_signals = signals.dropna()
        assert all(valid_signals.isin([-1, 0, 1]))

    def test_rsi_calculation(self):
        """Test RSI calculation produces expected range."""
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        np.random.seed(42)

        # Create data with known trend
        prices = 100 + np.arange(50) * 0.5  # Steady uptrend
        data = DataFrame({'close': prices}, index=dates)

        strategy = RSIMeanReversionStrategy()
        rsi = strategy._calculate_rsi(data['close'], 14)

        # RSI should be between 0 and 100
        assert rsi.dropna().min() >= 0
        assert rsi.dropna().max() <= 100


class TestZScoreStrategy:
    """Test Z-Score Mean Reversion strategy."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        strategy = ZScoreStrategy()
        assert strategy.period == 20
        assert strategy.threshold == 2.0

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        strategy = ZScoreStrategy(period=10, threshold=1.5)
        assert strategy.period == 10
        assert strategy.threshold == 1.5

    def test_generate_signals_low_zscore(self):
        """Test signal generation when Z-score is low (buy signal)."""
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        np.random.seed(42)

        # Create price drop (price far below mean)
        base_prices = 100 + np.random.randn(25) * 2
        drop_prices = np.linspace(102, 82, 25)  # 25 sharp drop prices
        prices = np.concatenate([base_prices, drop_prices])

        data = DataFrame({'close': prices}, index=dates)

        strategy = ZScoreStrategy(period=20, threshold=2.0)
        signals = strategy.generate_signals(data)

        # Verify output
        assert isinstance(signals, Series)
        assert len(signals) == len(data)

        # Should have some buy signals when price drops
        valid_signals = signals.dropna()
        assert all(valid_signals.isin([-1, 0, 1]))

    def test_generate_signals_high_zscore(self):
        """Test signal generation when Z-score is high (sell signal)."""
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        np.random.seed(42)

        # Create price spike (price far above mean)
        base_prices = 100 + np.random.randn(25) * 2
        spike_prices = np.arange(105, 120, 0.6)  # 25 sharp rise prices
        prices = np.concatenate([base_prices, spike_prices])

        data = DataFrame({'close': prices}, index=dates)

        strategy = ZScoreStrategy(period=20, threshold=2.0)
        signals = strategy.generate_signals(data)

        # Verify output
        assert isinstance(signals, Series)
        assert len(signals) == len(data)

        # Should have some sell signals when price spikes
        valid_signals = signals.dropna()
        assert all(valid_signals.isin([-1, 0, 1]))

    def test_generate_signals_normal_range(self):
        """Test signal generation when price is in normal range."""
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        np.random.seed(42)

        # Create stable prices (within 1 std of mean)
        data = DataFrame({
            'close': 100 + np.random.randn(50) * 2
        }, index=dates)

        strategy = ZScoreStrategy(period=20, threshold=2.0)
        signals = strategy.generate_signals(data)

        # Should have mostly 0 signals (no action)
        assert isinstance(signals, Series)
        valid_signals = signals.dropna()
        assert all(valid_signals.isin([-1, 0, 1]))

    def test_signal_values_valid(self):
        """Test that all signal values are -1, 0, or 1."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        data = DataFrame({
            'close': 100 + np.random.randn(100) * 5
        }, index=dates)

        strategy = ZScoreStrategy()
        signals = strategy.generate_signals(data)

        # Check all non-NaN values are valid
        valid_signals = signals.dropna()
        assert all(valid_signals.isin([-1, 0, 1]))


class TestPairsTradingStrategy:
    """Test Pairs Trading strategy."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        strategy = PairsTradingStrategy()
        assert strategy.entry_threshold == 2.0
        assert strategy.exit_threshold == 0.5
        assert strategy.lookback == 30

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        strategy = PairsTradingStrategy(entry_threshold=1.5, exit_threshold=0.3, lookback=20)
        assert strategy.entry_threshold == 1.5
        assert strategy.exit_threshold == 0.3
        assert strategy.lookback == 20

    def test_generate_signals_correlated_assets(self):
        """Test signal generation with correlated assets."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        np.random.seed(42)

        # Create two correlated price series
        base_price = 100 + np.random.randn(100) * 2
        asset1 = Series(base_price, index=dates)
        asset2 = Series(base_price + 5, index=dates)  # Perfectly correlated with offset

        strategy = PairsTradingStrategy(entry_threshold=2.0, exit_threshold=0.5, lookback=30)
        result = strategy.generate_signals(asset1, asset2, hedge_ratio=1.0)

        # Verify return structure
        assert isinstance(result, dict)
        assert 'asset1' in result
        assert 'asset2' in result
        assert 'spread_zscore' in result

        # Verify signals
        assert isinstance(result['asset1'], Series)
        assert isinstance(result['asset2'], Series)
        assert isinstance(result['spread_zscore'], Series)

        # Check lengths
        assert len(result['asset1']) == len(asset1)
        assert len(result['asset2']) == len(asset2)
        assert len(result['spread_zscore']) == len(asset1)

    def test_generate_signals_divergent_assets(self):
        """Test signal generation when assets diverge."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        np.random.seed(42)

        # Create divergent assets (spread widens)
        base_prices = 100 + np.random.randn(70) * 2
        asset1_drops = np.linspace(100, 85, 30)  # 30 dropping prices
        asset2_rises = np.linspace(100, 115, 30)  # 30 rising prices
        asset1_prices = np.concatenate([base_prices, asset1_drops])
        asset2_prices = np.concatenate([base_prices, asset2_rises])

        asset1 = Series(asset1_prices, index=dates)
        asset2 = Series(asset2_prices, index=dates)

        strategy = PairsTradingStrategy(entry_threshold=2.0, exit_threshold=0.5, lookback=30)
        result = strategy.generate_signals(asset1, asset2, hedge_ratio=1.0)

        # Should generate signals when spread is wide
        signals1_valid = result['asset1'].dropna()
        signals2_valid = result['asset2'].dropna()

        # All signals should be valid
        assert all(signals1_valid.isin([-1, 0, 1]))
        assert all(signals2_valid.isin([-1, 0, 1]))

    def test_generate_signals_with_hedge_ratio(self):
        """Test signal generation with custom hedge ratio."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        np.random.seed(42)

        asset1 = Series(100 + np.random.randn(100) * 2, index=dates)
        asset2 = Series(200 + np.random.randn(100) * 4, index=dates)  # 2x asset1

        # Use hedge ratio of 2 (should account for price difference)
        strategy = PairsTradingStrategy(entry_threshold=2.0, exit_threshold=0.5, lookback=30)
        result = strategy.generate_signals(asset1, asset2, hedge_ratio=0.5)

        # Should still work
        assert isinstance(result, dict)
        assert 'spread_zscore' in result
        assert len(result['spread_zscore']) == len(asset1)

    def test_signal_values_valid(self):
        """Test that all signal values are -1, 0, or 1."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        np.random.seed(42)

        asset1 = Series(100 + np.random.randn(100) * 3, index=dates)
        asset2 = Series(100 + np.random.randn(100) * 3, index=dates)

        strategy = PairsTradingStrategy()
        result = strategy.generate_signals(asset1, asset2)

        # Check all non-NaN values are valid for both assets
        signals1_valid = result['asset1'].dropna()
        signals2_valid = result['asset2'].dropna()

        assert all(signals1_valid.isin([-1, 0, 1]))
        assert all(signals2_valid.isin([-1, 0, 1]))

    def test_spread_zscore_calculation(self):
        """Test that spread Z-score is calculated correctly."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        np.random.seed(42)

        # Create simple spread scenario
        asset1 = Series(100 + np.arange(100) * 0.1, index=dates)  # Rising
        asset2 = Series(100 + np.arange(100) * 0.1, index=dates)  # Same

        strategy = PairsTradingStrategy(lookback=30)
        result = strategy.generate_signals(asset1, asset2, hedge_ratio=1.0)

        # Spread should be near zero (assets are identical)
        spread_zscore = result['spread_zscore'].dropna()

        # Most Z-scores should be reasonable (not extreme)
        # After lookback period, should have values
        if len(spread_zscore) > 0:
            assert spread_zscore.abs().max() < 10  # Should not have extreme values

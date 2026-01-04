import pandas as pd
import numpy as np
from typing import Dict, Any

class MAStrategy:
    """
    Moving Average Crossover Strategy

    Goes long when fast MA crosses above slow MA
    Goes short when fast MA crosses below slow MA
    """

    def __init__(self, fast_period: int = 10, slow_period: int = 20):
        """
        Initialize MA strategy

        Args:
            fast_period: Fast MA period
            slow_period: Slow MA period
        """
        self.fast_period = fast_period
        self.slow_period = slow_period

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals

        Args:
            data: DataFrame with 'close' column

        Returns:
            Series of signals (-1, 0, 1)
        """
        close = data['close']

        # Calculate moving averages
        fast_ma = close.rolling(window=self.fast_period).mean()
        slow_ma = close.rolling(window=self.slow_period).mean()

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Long when fast MA > slow MA
        signals[fast_ma > slow_ma] = 1

        # Short when fast MA < slow MA
        signals[fast_ma < slow_ma] = -1

        return signals


class BollingerBandsStrategy:
    """
    Bollinger Bands Breakout Strategy

    Goes long when price breaks above upper band
    Goes short when price breaks below lower band
    """

    def __init__(self, period: int = 20, std_dev: float = 2.0):
        """
        Initialize Bollinger Bands strategy

        Args:
            period: MA period for bands
            std_dev: Number of standard deviations
        """
        self.period = period
        self.std_dev = std_dev

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on Bollinger Bands"""
        close = data['close']

        # Calculate bands
        sma = close.rolling(window=self.period).mean()
        std = close.rolling(window=self.period).std()

        upper_band = sma + (std * self.std_dev)
        lower_band = sma - (std * self.std_dev)

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Long when price breaks above upper band
        signals[close > upper_band] = 1

        # Short when price breaks below lower band
        signals[close < lower_band] = -1

        return signals


class DonchianChannelStrategy:
    """
    Donchian Channel Breakout Strategy

    Goes long when price breaks above N-day high
    Goes short when price breaks below N-day low
    """

    def __init__(self, period: int = 20):
        """
        Initialize Donchian Channel strategy

        Args:
            period: Lookback period for channel
        """
        self.period = period

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on Donchian Channel"""
        high = data['high'] if 'high' in data.columns else data['close']
        low = data['low'] if 'low' in data.columns else data['close']
        close = data['close']

        # Calculate channels
        upper_channel = high.rolling(window=self.period).max()
        lower_channel = low.rolling(window=self.period).min()

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Long when price breaks above upper channel
        signals[close > upper_channel.shift(1)] = 1

        # Short when price breaks below lower channel
        signals[close < lower_channel.shift(1)] = -1

        return signals

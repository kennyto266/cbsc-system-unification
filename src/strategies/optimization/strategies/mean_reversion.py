"""
Mean reversion strategies for quantitative trading.

Implements RSI, Z-Score, and Pairs Trading strategies.
"""

import pandas as pd
import numpy as np
from typing import Dict


class RSIMeanReversionStrategy:
    """
    RSI Mean Reversion Strategy

    Buys when RSI is oversold (e.g., < 30)
    Sells when RSI is overbought (e.g., > 70)
    """

    def __init__(self, rsi_period: int = 14,
                 oversold: float = 30,
                 overbought: float = 70):
        """
        Initialize RSI mean reversion strategy

        Args:
            rsi_period: RSI calculation period
            oversold: RSI level considered oversold
            overbought: RSI level considered overbought
        """
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on RSI"""
        # Input validation
        if 'close' not in data.columns:
            raise ValueError("DataFrame must contain 'close' column")
        if data.empty:
            return pd.Series(dtype=int, index=data.index)

        close = data['close']

        # Calculate RSI
        rsi = self._calculate_rsi(close, self.rsi_period)

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Buy when RSI crosses above oversold
        buy_signals = (rsi > self.oversold) & (rsi.shift(1) <= self.oversold)
        signals[buy_signals] = 1

        # Sell when RSI crosses below overbought
        sell_signals = (rsi < self.overbought) & (rsi.shift(1) >= self.overbought)
        signals[sell_signals] = -1

        return signals

    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi


class ZScoreStrategy:
    """
    Z-Score Mean Reversion Strategy

    Buys when price is more than N standard deviations below mean
    Sells when price is more than N standard deviations above mean
    """

    def __init__(self, period: int = 20, threshold: float = 2.0):
        """
        Initialize Z-Score strategy

        Args:
            period: Lookback period for mean/std
            threshold: Number of standard deviations for entry
        """
        self.period = period
        self.threshold = threshold

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on Z-score"""
        # Input validation
        if 'close' not in data.columns:
            raise ValueError("DataFrame must contain 'close' column")
        if data.empty:
            return pd.Series(dtype=int, index=data.index)

        close = data['close']

        # Calculate rolling statistics
        rolling_mean = close.rolling(window=self.period).mean()
        rolling_std = close.rolling(window=self.period).std()

        # Calculate Z-score
        zscore = (close - rolling_mean) / rolling_std

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Buy when Z-score < -threshold
        signals[zscore < -self.threshold] = 1

        # Sell when Z-score > threshold
        signals[zscore > self.threshold] = -1

        return signals


class PairsTradingStrategy:
    """
    Pairs Trading Strategy (Statistical Arbitrage)

    Trades two correlated assets based on mean reversion of spread
    """

    def __init__(self, entry_threshold: float = 2.0,
                 exit_threshold: float = 0.5,
                 lookback: int = 30):
        """
        Initialize pairs trading strategy

        Args:
            entry_threshold: Z-score for entry
            exit_threshold: Z-score for exit
            lookback: Period for calculating spread statistics
        """
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.lookback = lookback

    def generate_signals(self, asset1: pd.Series, asset2: pd.Series,
                        hedge_ratio: float = 1.0) -> Dict[str, pd.Series]:
        """
        Generate pairs trading signals

        Args:
            asset1: Prices of first asset
            asset2: Prices of second asset
            hedge_ratio: Ratio for position sizing

        Returns:
            Dictionary with signals for both assets
        """
        # Input validation
        if asset1.empty or asset2.empty:
            return {'asset1': pd.Series(dtype=int, index=asset1.index),
                    'asset2': pd.Series(dtype=int, index=asset2.index),
                    'spread_zscore': pd.Series(dtype=float)}

        # Calculate spread
        spread = asset1 - hedge_ratio * asset2

        # Calculate Z-score of spread
        spread_mean = spread.rolling(window=self.lookback).mean()
        spread_std = spread.rolling(window=self.lookback).std()
        spread_zscore = (spread - spread_mean) / spread_std

        # Generate signals
        signals_asset1 = pd.Series(0, index=asset1.index)
        signals_asset2 = pd.Series(0, index=asset2.index)

        # Entry: Long spread (long asset1, short asset2)
        long_spread = spread_zscore < -self.entry_threshold
        signals_asset1[long_spread] = 1
        signals_asset2[long_spread] = -1

        # Entry: Short spread (short asset1, long asset2)
        short_spread = spread_zscore > self.entry_threshold
        signals_asset1[short_spread] = -1
        signals_asset2[short_spread] = 1

        # Exit when spread reverts
        exit_signal = spread_zscore.abs() < self.exit_threshold
        signals_asset1[exit_signal] = 0
        signals_asset2[exit_signal] = 0

        return {
            'asset1': signals_asset1,
            'asset2': signals_asset2,
            'spread_zscore': spread_zscore
        }

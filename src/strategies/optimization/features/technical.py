# src/strategies/optimization/features/technical.py
import pandas as pd
import numpy as np
from typing import Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Try to import TA-Lib
try:
    import talib
    HAS_TALIB = True
    logger.info("TA-Lib is available and will be used for technical indicators")
except ImportError:
    HAS_TALIB = False
    logger.warning("TA-Lib not installed, using pure Python implementations")


class TechnicalIndicators:
    """Calculate technical indicators using TA-Lib or pure Python"""

    def __init__(self):
        """Initialize technical indicators calculator"""
        self.use_talib = HAS_TALIB

    def sma(self, series: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate Simple Moving Average

        Args:
            series: Price series
            period: Moving average period

        Returns:
            Series with SMA values
        """
        if self.use_talib:
            result = talib.SMA(series.values, timeperiod=period)
            return pd.Series(result, index=series.index)
        else:
            return series.rolling(window=period).mean()

    def ema(self, series: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate Exponential Moving Average

        Args:
            series: Price series
            period: Moving average period

        Returns:
            Series with EMA values
        """
        if self.use_talib:
            result = talib.EMA(series.values, timeperiod=period)
            return pd.Series(result, index=series.index)
        else:
            return series.ewm(span=period, adjust=False).mean()

    def rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index

        Args:
            series: Price series
            period: RSI period

        Returns:
            Series with RSI values (0-100)
        """
        if self.use_talib:
            result = talib.RSI(series.values, timeperiod=period)
            return pd.Series(result, index=series.index)
        else:
            # Pure Python implementation
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return rsi

    def bollinger_bands(self, series: pd.Series, period: int = 20,
                       std_dev: float = 2.0) -> pd.DataFrame:
        """
        Calculate Bollinger Bands

        Args:
            series: Price series
            period: Moving average period
            std_dev: Number of standard deviations

        Returns:
            DataFrame with 'upper', 'middle', 'lower' columns
        """
        sma = self.sma(series, period)
        std = series.rolling(window=period).std()

        return pd.DataFrame({
            'upper': sma + (std * std_dev),
            'middle': sma,
            'lower': sma - (std * std_dev)
        }, index=series.index)

    def macd(self, series: pd.Series, fast: int = 12, slow: int = 26,
             signal: int = 9) -> pd.DataFrame:
        """
        Calculate MACD (Moving Average Convergence Divergence)

        Args:
            series: Price series
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line EMA period

        Returns:
            DataFrame with 'macd', 'signal', 'histogram' columns
        """
        ema_fast = self.ema(series, fast)
        ema_slow = self.ema(series, slow)

        macd_line = ema_fast - ema_slow
        signal_line = self.ema(macd_line, signal)
        histogram = macd_line - signal_line

        return pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }, index=series.index)

    def atr(self, high: pd.Series, low: pd.Series, close: pd.Series,
            period: int = 14) -> pd.Series:
        """
        Calculate Average True Range

        Args:
            high: High price series
            low: Low price series
            close: Close price series
            period: ATR period

        Returns:
            Series with ATR values
        """
        if self.use_talib:
            result = talib.ATR(high.values, low.values, close.values, timeperiod=period)
            return pd.Series(result, index=close.index)
        else:
            high_low = high - low
            high_close = np.abs(high - close.shift())
            low_close = np.abs(low - close.shift())

            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            return tr.rolling(window=period).mean()

    def stoch(self, high: pd.Series, low: pd.Series, close: pd.Series,
              k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """
        Calculate Stochastic Oscillator

        Args:
            high: High price series
            low: Low price series
            close: Close price series
            k_period: Stochastic %K period
            d_period: Stochastic %D period

        Returns:
            DataFrame with 'k', 'd' columns
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        # Handle division by zero (when high == low)
        high_low_range = highest_high - lowest_low
        high_low_range = high_low_range.replace(0, np.nan)  # Avoid division by zero

        k = 100 * (close - lowest_low) / high_low_range
        # Replace any remaining inf/nan with 50 (neutral)
        k = k.fillna(50).replace([np.inf, -np.inf], 50)

        # Clip values to valid range [0, 100]
        k = k.clip(0, 100)

        d = k.rolling(window=d_period).mean()

        return pd.DataFrame({'k': k, 'd': d}, index=close.index)

"""
RSI (Relative Strength Index) Strategy

Strategy:
- Buy when RSI < oversold threshold (typically 30)
- Sell when RSI > overbought threshold (typically 70)
- Can be combined with trend filter for better results
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .ma_crossover import BaseStrategy, Signal


class RSIStrategy(BaseStrategy):
    """
    Relative Strength Index (RSI) Strategy

    Generates buy/sell signals based on RSI overbought/oversold levels.

    Parameters:
        rsi_period: RSI calculation period (default: 14)
        oversold_threshold: RSI level to consider oversold (default: 30)
        overbought_threshold: RSI level to consider overbought (default: 70)
        use_trend_filter: Use moving average trend filter (default: True)
        trend_ma_period: Trend filter MA period (default: 200)
    """

    def __init__(
        self,
        rsi_period: int = 14,
        oversold_threshold: float = 30,
        overbought_threshold: float = 70,
        use_trend_filter: bool = True,
        trend_ma_period: int = 200
    ):
        super().__init__(
            name=f"RSI_{rsi_period}_{oversold_threshold}_{overbought_threshold}",
            params={
                'rsi_period': rsi_period,
                'oversold_threshold': oversold_threshold,
                'overbought_threshold': overbought_threshold,
                'use_trend_filter': use_trend_filter,
                'trend_ma_period': trend_ma_period
            }
        )

        self.rsi_period = rsi_period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold
        self.use_trend_filter = use_trend_filter
        self.trend_ma_period = trend_ma_period

        # Validate parameters
        if rsi_period < 2:
            raise ValueError("RSI period must be at least 2")
        if oversold_threshold >= overbought_threshold:
            raise ValueError("Oversold threshold must be less than overbought threshold")
        if not (0 <= oversold_threshold <= 50):
            raise ValueError("Oversold threshold must be between 0 and 50")
        if not (50 <= overbought_threshold <= 100):
            raise ValueError("Overbought threshold must be between 50 and 100")

    def calculate_rsi(self, data: pd.Series, period: int) -> pd.Series:
        """
        Calculate Relative Strength Index

        Args:
            data: Price series
            period: RSI period

        Returns:
            pd.Series: RSI values
        """
        # Calculate price changes
        delta = data.diff()

        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)

        # Calculate average gains and losses using Wilder's smoothing
        avg_gains = gains.rolling(window=period, min_periods=1).mean()
        avg_losses = losses.rolling(window=period, min_periods=1).mean()

        # Alternative: Use exponential smoothing for better results
        # avg_gains = gains.ewm(com=period-1, adjust=False).mean()
        # avg_losses = losses.ewm(com=period-1, adjust=False).mean()

        # Calculate Relative Strength
        rs = avg_gains / avg_losses

        # Calculate RSI
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on RSI

        Args:
            data: DataFrame with OHLCV data

        Returns:
            pd.Series: Trading signals (1 for buy, -1 for sell, 0 for hold)
        """
        # Calculate RSI
        rsi = self.calculate_rsi(data['close'], self.rsi_period)

        # Initialize signals series
        signals = pd.Series(0, index=data.index)

        # Apply trend filter if enabled
        if self.use_trend_filter:
            trend_ma = data['close'].rolling(window=self.trend_ma_period).mean()
            is_uptrend = data['close'] > trend_ma
        else:
            is_uptrend = pd.Series(True, index=data.index)

        # Generate signals
        for i in range(self.rsi_period, len(data)):
            current_rsi = rsi.iloc[i]
            prev_rsi = rsi.iloc[i-1]
            in_uptrend = is_uptrend.iloc[i]

            # Buy signal: RSI crosses above oversold threshold
            if (prev_rsi <= self.oversold_threshold and
                current_rsi > self.oversold_threshold and
                in_uptrend):
                signals.iloc[i] = Signal.BUY.value

            # Sell signal: RSI crosses below overbought threshold
            elif (prev_rsi >= self.overbought_threshold and
                  current_rsi < self.overbought_threshold):
                signals.iloc[i] = Signal.SELL.value

        return signals

    def get_rsi_values(self, data: pd.DataFrame) -> pd.Series:
        """
        Get RSI values for plotting/analysis

        Args:
            data: DataFrame with OHLCV data

        Returns:
            pd.Series: RSI values
        """
        return self.calculate_rsi(data['close'], self.rsi_period)

    def calculate_performance_metrics(self, data: pd.DataFrame) -> Dict:
        """
        Calculate basic performance metrics for the strategy

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Dict: Performance metrics
        """
        signals = self.generate_signals(data)
        returns = self.calculate_returns(data, signals)

        # Basic metrics
        total_return = (1 + returns).prod() - 1
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1
        volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0

        # Signal metrics
        total_signals = (signals != 0).sum()
        buy_signals = (signals == 1).sum()
        sell_signals = (signals == -1).sum()

        # RSI distribution metrics
        rsi = self.get_rsi_values(data)
        rsi_mean = rsi.mean()
        rsi_std = rsi.std()

        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'total_signals': total_signals,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'signal_frequency': total_signals / len(data),
            'rsi_mean': rsi_mean,
            'rsi_std': rsi_std
        }


class EnhancedRSIStrategy(RSIStrategy):
    """
    Enhanced RSI Strategy with additional features

    Features:
    - RSI divergence detection
    - Multiple timeframes
    - Dynamic thresholds
    - Volume confirmation
    - Stop loss and take profit
    """

    def __init__(
        self,
        rsi_period: int = 14,
        oversold_threshold: float = 30,
        overbought_threshold: float = 70,
        use_trend_filter: bool = True,
        trend_ma_period: int = 200,
        use_divergence: bool = True,
        dynamic_thresholds: bool = True,
        volume_confirmation: bool = True,
        stop_loss: float = 0.05,
        take_profit: float = 0.15
    ):
        super().__init__(
            rsi_period=rsi_period,
            oversold_threshold=oversold_threshold,
            overbought_threshold=overbought_threshold,
            use_trend_filter=use_trend_filter,
            trend_ma_period=trend_ma_period
        )

        self.name = f"Enhanced_{self.name}"
        self.params.update({
            'use_divergence': use_divergence,
            'dynamic_thresholds': dynamic_thresholds,
            'volume_confirmation': volume_confirmation,
            'stop_loss': stop_loss,
            'take_profit': take_profit
        })

        self.use_divergence = use_divergence
        self.dynamic_thresholds = dynamic_thresholds
        self.volume_confirmation = volume_confirmation
        self.stop_loss = stop_loss
        self.take_profit = take_profit

        # State tracking
        self.entry_price = None
        self.current_position = 0

    def detect_divergence(self, prices: pd.Series, rsi: pd.Series, window: int = 20) -> pd.Series:
        """
        Detect RSI divergences

        Args:
            prices: Price series
            rsi: RSI series
            window: Lookback window for divergence detection

        Returns:
            pd.Series: Divergence signals
        """
        divergence_signals = pd.Series(0, index=prices.index)

        for i in range(window, len(prices)):
            price_window = prices.iloc[i-window:i+1]
            rsi_window = rsi.iloc[i-window:i+1]

            # Find local extrema
            price_peaks = self._find_peaks(price_window)
            rsi_peaks = self._find_peaks(rsi_window)

            # Check for bullish divergence (price lower low, RSI higher low)
            if (len(price_peaks) >= 2 and len(rsi_peaks) >= 2):
                price_ll = price_window.iloc[price_peaks[-1]] < price_window.iloc[price_peaks[-2]]
                rsi_hl = rsi_window.iloc[rsi_peaks[-1]] > rsi_window.iloc[rsi_peaks[-2]]

                if price_ll and rsi_hl:
                    divergence_signals.iloc[i] = 1  # Bullish divergence

            # Check for bearish divergence (price higher high, RSI lower high)
            if (len(price_peaks) >= 2 and len(rsi_peaks) >= 2):
                price_hh = price_window.iloc[price_peaks[-1]] > price_window.iloc[price_peaks[-2]]
                rsi_lh = rsi_window.iloc[rsi_peaks[-1]] < rsi_window.iloc[rsi_peaks[-2]]

                if price_hh and rsi_lh:
                    divergence_signals.iloc[i] = -1  # Bearish divergence

        return divergence_signals

    def _find_peaks(self, series: pd.Series) -> List[int]:
        """Find peak indices in a series"""
        peaks = []
        for i in range(1, len(series) - 1):
            if series.iloc[i] > series.iloc[i-1] and series.iloc[i] > series.iloc[i+1]:
                peaks.append(i)
        return peaks

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate enhanced RSI signals with all features

        Args:
            data: DataFrame with OHLCV data

        Returns:
            pd.Series: Enhanced trading signals
        """
        # Calculate basic RSI
        rsi = self.calculate_rsi(data['close'], self.rsi_period)

        # Initialize signals series
        signals = pd.Series(0, index=data.index)

        # Calculate dynamic thresholds if enabled
        if self.dynamic_thresholds:
            oversold = rsi.rolling(window=50).quantile(0.2)
            overbought = rsi.rolling(window=50).quantile(0.8)
        else:
            oversold = pd.Series(self.oversold_threshold, index=data.index)
            overbought = pd.Series(self.overbought_threshold, index=data.index)

        # Trend filter
        if self.use_trend_filter:
            trend_ma = data['close'].rolling(window=self.trend_ma_period).mean()
            is_uptrend = data['close'] > trend_ma
        else:
            is_uptrend = pd.Series(True, index=data.index)

        # Volume confirmation
        if self.volume_confirmation:
            volume_ma = data['volume'].rolling(window=20).mean()
            volume_confirmed = data['volume'] > volume_ma * 1.2
        else:
            volume_confirmed = pd.Series(True, index=data.index)

        # Divergence detection
        if self.use_divergence:
            divergence = self.detect_divergence(data['close'], rsi)
        else:
            divergence = pd.Series(0, index=data.index)

        # Generate signals with all conditions
        for i in range(max(self.rsi_period, self.trend_ma_period), len(data)):
            current_rsi = rsi.iloc[i]
            prev_rsi = rsi.iloc[i-1]
            current_oversold = oversold.iloc[i]
            current_overbought = overbought.iloc[i]
            in_uptrend = is_uptrend.iloc[i]
            vol_confirmed = volume_confirmed.iloc[i]
            divergence_sig = divergence.iloc[i]

            # Risk management checks
            if self.current_position > 0:  # Long position
                pnl = (data['close'].iloc[i] - self.entry_price) / self.entry_price
                if pnl <= -self.stop_loss or pnl >= self.take_profit:
                    self.current_position = 0
                    self.entry_price = None
                    signals.iloc[i] = Signal.SELL.value
                    continue

            elif self.current_position < 0:  # Short position
                pnl = (self.entry_price - data['close'].iloc[i]) / self.entry_price
                if pnl <= -self.stop_loss or pnl >= self.take_profit:
                    self.current_position = 0
                    self.entry_price = None
                    signals.iloc[i] = Signal.BUY.value
                    continue

            # Entry conditions
            buy_condition = (
                prev_rsi <= current_oversold and
                current_rsi > current_oversold and
                in_uptrend and
                vol_confirmed
            )

            # Add divergence confirmation
            if self.use_divergence and divergence_sig == 1:
                buy_condition = True

            sell_condition = (
                prev_rsi >= current_overbought and
                current_rsi < current_overbought
            )

            # Add divergence confirmation
            if self.use_divergence and divergence_sig == -1:
                sell_condition = True

            # Generate signals
            if buy_condition and self.current_position <= 0:
                self.entry_price = data['close'].iloc[i]
                self.current_position = 1
                signals.iloc[i] = Signal.BUY.value

            elif sell_condition and self.current_position >= 0:
                self.entry_price = data['close'].iloc[i]
                self.current_position = -1
                signals.iloc[i] = Signal.SELL.value

        return signals

    def reset(self):
        """Reset strategy state"""
        self.entry_price = None
        self.current_position = 0
        self.signals = []


# Utility functions for RSI optimization
def optimize_rsi_parameters(
    data: pd.DataFrame,
    rsi_range: range = range(10, 21, 2),
    oversold_range: range = range(20, 36, 5),
    overbought_range: range = (65, 81, 5)
) -> Dict:
    """
    Optimize RSI strategy parameters

    Args:
        data: OHLCV data
        rsi_range: Range of RSI periods to test
        oversold_range: Range of oversold thresholds to test
        overbought_range: Range of overbought thresholds to test

    Returns:
        Dict: Best parameters and performance
    """
    best_params = None
    best_sharpe = -np.inf

    results = []

    for rsi_period in rsi_range:
        for oversold in oversold_range:
            for overbought in overbought_range:
                if oversold >= overbought:
                    continue

                strategy = RSIStrategy(
                    rsi_period=rsi_period,
                    oversold_threshold=oversold,
                    overbought_threshold=overbought,
                    use_trend_filter=True
                )

                metrics = strategy.calculate_performance_metrics(data)
                sharpe = metrics['sharpe_ratio']

                results.append({
                    'rsi_period': rsi_period,
                    'oversold_threshold': oversold,
                    'overbought_threshold': overbought,
                    'sharpe_ratio': sharpe,
                    'total_return': metrics['total_return'],
                    'volatility': metrics['volatility'],
                    'signal_frequency': metrics['signal_frequency']
                })

                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_params = {
                        'rsi_period': rsi_period,
                        'oversold_threshold': oversold,
                        'overbought_threshold': overbought,
                        'sharpe_ratio': sharpe,
                        'total_return': metrics['total_return']
                    }

    return {
        'best_params': best_params,
        'all_results': sorted(results, key=lambda x: x['sharpe_ratio'], reverse=True)
    }
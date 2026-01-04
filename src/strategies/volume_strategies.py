"""
Volume-Based Trading Strategies

This module contains strategies that incorporate volume analysis.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .ma_crossover import BaseStrategy, Signal


class VolumePriceTrendStrategy(BaseStrategy):
    """
    Volume Price Trend (VPT) Strategy

    Strategy:
    - VPT accumulates volume based on price direction
    - Buy when VPT is rising (confirming uptrend)
    - Sell when VPT is falling (confirming downtrend)
    """

    def __init__(
        self,
        ma_period: int = 20,
        volume_ma_period: int = 10,
        threshold: float = 0.0
    ):
        super().__init__(
            name=f"VPT_{ma_period}_{volume_ma_period}",
            params={
                'ma_period': ma_period,
                'volume_ma_period': volume_ma_period,
                'threshold': threshold
            }
        )
        self.ma_period = ma_period
        self.volume_ma_period = volume_ma_period
        self.threshold = threshold

    def calculate_vpt(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate Volume Price Trend"""
        # Calculate price change rate
        price_change = close.pct_change()

        # Calculate VPT
        vpt = (price_change * volume).cumsum()

        return vpt

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on VPT"""
        vpt = self.calculate_vpt(data['close'], data['volume'])

        # Initialize signals
        signals = pd.Series(0, index=data.index)

        # Calculate VPT moving average
        vpt_ma = vpt.rolling(window=self.ma_period).mean()
        vpt_ma_slope = vpt_ma.diff()

        # Buy when VPT MA slope is positive
        buy_signal = vpt_ma_slope > self.threshold
        signals[buy_signal] = Signal.BUY.value

        # Sell when VPT MA slope is negative
        sell_signal = vpt_ma_slope < -self.threshold
        signals[sell_signal] = Signal.SELL.value

        return signals


class OnBalanceVolumeStrategy(BaseStrategy):
    """
    On-Balance Volume (OBV) Strategy

    Strategy:
    - OBV adds volume on up days, subtracts on down days
    - Buy when OBV is rising
    - Sell when OBV is falling
    - Can confirm price trends or predict reversals
    """

    def __init__(
        self,
        ma_period: int = 20,
        divergence_period: int = 10
    ):
        super().__init__(
            name=f"OBV_{ma_period}_{divergence_period}",
            params={
                'ma_period': ma_period,
                'divergence_period': divergence_period
            }
        )
        self.ma_period = ma_period
        self.divergence_period = divergence_period

    def calculate_obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate On-Balance Volume"""
        # Determine up or down days
        price_change = close.diff()

        # Calculate OBV
        obv = pd.Series(0, index=close.index)
        for i in range(1, len(close)):
            if price_change.iloc[i] > 0:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif price_change.iloc[i] < 0:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]

        return obv

    def detect_divergence(self, price: pd.Series, obv: pd.Series) -> pd.Series:
        """Detect price-OBV divergence"""
        divergence = pd.Series(0, index=price.index)

        # Simple divergence detection
        for i in range(self.divergence_period, len(price)):
            price_window = price.iloc[i-self.divergence_period:i+1]
            obv_window = obv.iloc[i-self.divergence_period:i+1]

            # Bullish divergence: price lower low, OBV higher low
            if (price_window.iloc[-1] < price_window.min() and
                obv_window.iloc[-1] > obv_window.min()):
                divergence.iloc[i] = 1

            # Bearish divergence: price higher high, OBV lower high
            elif (price_window.iloc[-1] > price_window.max() and
                  obv_window.iloc[-1] < obv_window.max()):
                divergence.iloc[i] = -1

        return divergence

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on OBV"""
        obv = self.calculate_obv(data['close'], data['volume'])

        # Initialize signals
        signals = pd.Series(0, index=data.index)

        # Calculate OBV moving average
        obv_ma = obv.rolling(window=self.ma_period).mean()
        obv_ma_slope = obv_ma.diff()

        # Detect divergence
        divergence = self.detect_divergence(data['close'], obv)

        # Buy signals
        buy_condition = (
            (obv_ma_slope > 0) |  # OBV rising
            (divergence == 1)      # Bullish divergence
        )
        signals[buy_condition] = Signal.BUY.value

        # Sell signals
        sell_condition = (
            (obv_ma_slope < 0) |  # OBV falling
            (divergence == -1)     # Bearish divergence
        )
        signals[sell_condition] = Signal.SELL.value

        return signals

    def get_obv_values(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Get OBV values for plotting"""
        obv = self.calculate_obv(data['close'], data['volume'])
        obv_ma = obv.rolling(window=self.ma_period).mean()

        return {
            'obv': obv,
            'obv_ma': obv_ma,
            'divergence': self.detect_divergence(data['close'], obv)
        }


class VWAPStrategy(BaseStrategy):
    """
    Volume Weighted Average Price (VWAP) Strategy

    Strategy:
    - VWAP is the average price weighted by volume
    - Buy when price crosses above VWAP
    - Sell when price crosses below VWAP
    - Works well for intraday trading
    """

    def __init__(
        self,
        reset_period: Optional[int] = None,  # None for cumulative, int for reset
        std_dev_bands: float = 2.0
    ):
        super().__init__(
            name=f"VWAP_{reset_period}_{std_dev_bands}",
            params={
                'reset_period': reset_period,
                'std_dev_bands': std_dev_bands
            }
        )
        self.reset_period = reset_period
        self.std_dev_bands = std_dev_bands

    def calculate_vwap(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate VWAP and standard deviation bands"""
        if self.reset_period is None:
            # Cumulative VWAP
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            cumulative_volume = data['volume'].cumsum()
            cumulative_price_volume = (typical_price * data['volume']).cumsum()

            vwap = cumulative_price_volume / cumulative_volume

            # Calculate standard deviation bands
            variance = ((typical_price - vwap) ** 2 * data['volume']).cumsum() / cumulative_volume
            std_dev = np.sqrt(variance)

        else:
            # Reset VWAP for each period
            typical_price = (data['high'] + data['low'] + data['close']) / 3

            # Create reset groups
            if hasattr(data.index, 'dayofyear'):
                reset_groups = data.index.dayofyear // self.reset_period
            else:
                reset_groups = np.arange(len(data)) // self.reset_period

            vwap = typical_price.groupby(reset_groups).transform(
                lambda x: (x * data.loc[x.index, 'volume']).sum() / data.loc[x.index, 'volume'].sum()
            )

            # Calculate standard deviation within groups
            def calc_std(group):
                vwap_val = (group * data.loc[group.index, 'volume']).sum() / data.loc[group.index, 'volume'].sum()
                variance = ((group - vwap_val) ** 2 * data.loc[group.index, 'volume']).sum() / data.loc[group.index, 'volume'].sum()
                return np.sqrt(variance)

            std_dev = typical_price.groupby(reset_groups).transform(calc_std)

        # Bands
        upper_band = vwap + (std_dev * self.std_dev_bands)
        lower_band = vwap - (std_dev * self.std_dev_bands)

        return vwap, upper_band, lower_band

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on VWAP"""
        vwap, upper_band, lower_band = self.calculate_vwap(data)

        # Initialize signals
        signals = pd.Series(0, index=data.index)

        # Buy when price crosses above VWAP
        buy_signal = (
            (data['close'] > vwap) &
            (data['close'].shift(1) <= vwap.shift(1))
        )
        signals[buy_signal] = Signal.BUY.value

        # Sell when price crosses below VWAP
        sell_signal = (
            (data['close'] < vwap) &
            (data['close'].shift(1) >= vwap.shift(1))
        )
        signals[sell_signal] = Signal.SELL.value

        return signals

    def get_vwap_values(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Get VWAP values for plotting"""
        vwap, upper_band, lower_band = self.calculate_vwap(data)

        return {
            'vwap': vwap,
            'upper_band': upper_band,
            'lower_band': lower_band
        }


class MoneyFlowIndexStrategy(BaseStrategy):
    """
    Money Flow Index (MFI) Strategy

    Strategy:
    - MFI combines price and volume
    - Similar to RSI but incorporates volume
    - Overbought > 80, Oversold < 20
    """

    def __init__(
        self,
        period: int = 14,
        overbought_level: float = 80,
        oversold_level: float = 20
    ):
        super().__init__(
            name=f"MFI_{period}",
            params={
                'period': period,
                'overbought_level': overbought_level,
                'oversold_level': oversold_level
            }
        )
        self.period = period
        self.overbought_level = overbought_level
        self.oversold_level = oversold_level

    def calculate_mfi(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Money Flow Index"""
        # Typical Price
        tp = (data['high'] + data['low'] + data['close']) / 3
        raw_money_flow = tp * data['volume']

        # Positive and Negative Money Flow
        positive_mf = pd.Series(0, index=data.index)
        negative_mf = pd.Series(0, index=data.index)

        for i in range(1, len(data)):
            if tp.iloc[i] > tp.iloc[i-1]:
                positive_mf.iloc[i] = raw_money_flow.iloc[i]
            elif tp.iloc[i] < tp.iloc[i-1]:
                negative_mf.iloc[i] = raw_money_flow.iloc[i]

        # Money Flow Ratio
        positive_mf_sum = positive_mf.rolling(window=self.period).sum()
        negative_mf_sum = negative_mf.rolling(window=self.period).sum()

        money_flow_ratio = positive_mf_sum / negative_mf_sum

        # Money Flow Index
        mfi = 100 - (100 / (1 + money_flow_ratio))

        return mfi

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on MFI"""
        mfi = self.calculate_mfi(data)

        # Initialize signals
        signals = pd.Series(0, index=data.index)

        # Buy when MFI crosses above oversold level
        buy_signal = (
            (mfi > self.oversold_level) &
            (mfi.shift(1) <= self.oversold_level.shift(1))
        )
        signals[buy_signal] = Signal.BUY.value

        # Sell when MFI crosses below overbought level
        sell_signal = (
            (mfi < self.overbought_level) &
            (mfi.shift(1) >= self.overbought_level.shift(1))
        )
        signals[sell_signal] = Signal.SELL.value

        return signals

    def get_mfi_values(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Get MFI values for plotting"""
        mfi = self.calculate_mfi(data)

        return {
            'mfi': mfi,
            'overbought': pd.Series(self.overbought_level, index=data.index),
            'oversold': pd.Series(self.oversold_level, index=data.index)
        }


# Volume strategy registry
VOLUME_STRATEGIES = {
    'vpt': VolumePriceTrendStrategy,
    'obv': OnBalanceVolumeStrategy,
    'vwap': VWAPStrategy,
    'mfi': MoneyFlowIndexStrategy,
}

__all__ = [
    'VolumePriceTrendStrategy',
    'OnBalanceVolumeStrategy',
    'VWAPStrategy',
    'MoneyFlowIndexStrategy',
    'VOLUME_STRATEGIES'
]
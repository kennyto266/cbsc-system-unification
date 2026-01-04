"""
Momentum-Based Trading Strategies

This module contains strategies based on momentum indicators.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .ma_crossover import BaseStrategy, Signal


class MomentumStrategy(BaseStrategy):
    """
    Momentum Trading Strategy

    Strategy:
    - Buy when momentum is positive and increasing
    - Sell when momentum is negative or decreasing
    - Uses rate of change (ROC) as momentum indicator
    """

    def __init__(
        self,
        period: int = 10,
        threshold: float = 0.0,
        use_ema: bool = True
    ):
        super().__init__(
            name=f"Momentum_{period}_{threshold}",
            params={
                'period': period,
                'threshold': threshold,
                'use_ema': use_ema
            }
        )
        self.period = period
        self.threshold = threshold
        self.use_ema = use_ema

    def calculate_momentum(self, data: pd.Series) -> pd.Series:
        """Calculate momentum (Rate of Change)"""
        if self.use_ema:
            # Use EMA for smoother momentum
            roc = data.pct_change(periods=self.period) * 100
            momentum = roc.ewm(span=self.period).mean()
        else:
            # Simple momentum
            momentum = data.pct_change(periods=self.period) * 100

        return momentum

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on momentum"""
        momentum = self.calculate_momentum(data['close'])

        # Initialize signals
        signals = pd.Series(0, index=data.index)

        # Buy when momentum crosses above threshold
        buy_signal = (
            (momentum > self.threshold) &
            (momentum.shift(1) <= self.threshold.shift(1))
        )
        signals[buy_signal] = Signal.BUY.value

        # Sell when momentum crosses below -threshold
        sell_signal = (
            (momentum < -self.threshold) &
            (momentum.shift(1) >= -self.threshold.shift(1))
        )
        signals[sell_signal] = Signal.SELL.value

        return signals


class ADXStrategy(BaseStrategy):
    """
    Average Directional Index (ADX) Strategy

    Strategy:
    - ADX measures trend strength (not direction)
    - Use with +DI and -DI for direction
    - Buy when +DI crosses above -DI and ADX > 25
    - Sell when -DI crosses above +DI and ADX > 25
    """

    def __init__(
        self,
        period: int = 14,
        adx_threshold: float = 25
    ):
        super().__init__(
            name=f"ADX_{period}_{adx_threshold}",
            params={
                'period': period,
                'adx_threshold': adx_threshold
            }
        )
        self.period = period
        self.adx_threshold = adx_threshold

    def calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """Calculate ADX, +DI, and -DI"""
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate directional movements
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

        # Convert to Series
        plus_dm = pd.Series(plus_dm, index=close.index)
        minus_dm = pd.Series(minus_dm, index=close.index)
        tr = pd.Series(tr, index=close.index)

        # Calculate smoothed values
        atr = tr.rolling(window=self.period).mean()
        smoothed_plus_dm = plus_dm.rolling(window=self.period).mean()
        smoothed_minus_dm = minus_dm.rolling(window=self.period).mean()

        # Calculate DI
        plus_di = 100 * smoothed_plus_dm / atr
        minus_di = 100 * smoothed_minus_dm / atr

        # Calculate DX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)

        # Calculate ADX
        adx = dx.rolling(window=self.period).mean()

        return adx, plus_di, minus_di, dx

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on ADX"""
        adx, plus_di, minus_di, dx = self.calculate_adx(
            data['high'], data['low'], data['close']
        )

        # Initialize signals
        signals = pd.Series(0, index=data.index)

        # Strong trend condition
        strong_trend = adx > self.adx_threshold

        # Buy when +DI crosses above -DI in strong uptrend
        buy_signal = (
            strong_trend &
            (plus_di > minus_di) &
            (plus_di.shift(1) <= minus_di.shift(1))
        )
        signals[buy_signal] = Signal.BUY.value

        # Sell when -DI crosses above +DI in strong downtrend
        sell_signal = (
            strong_trend &
            (minus_di > plus_di) &
            (minus_di.shift(1) <= plus_di.shift(1))
        )
        signals[sell_signal] = Signal.SELL.value

        return signals

    def get_adx_values(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Get ADX values for plotting"""
        adx, plus_di, minus_di, dx = self.calculate_adx(
            data['high'], data['low'], data['close']
        )

        return {
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di,
            'dx': dx,
            'threshold': pd.Series(self.adx_threshold, index=data.index)
        }


class ParabolicSARStrategy(BaseStrategy):
    """
    Parabolic Stop and Reverse (SAR) Strategy

    Strategy:
    - SAR provides trailing stop-loss levels
    - Buy when price crosses above SAR
    - Sell when price crosses below SAR
    - Good for trending markets
    """

    def __init__(
        self,
        acceleration_factor: float = 0.02,
        maximum_acceleration: float = 0.2
    ):
        super().__init__(
            name=f"ParabolicSAR_{acceleration_factor}_{maximum_acceleration}",
            params={
                'acceleration_factor': acceleration_factor,
                'maximum_acceleration': maximum_acceleration
            }
        )
        self.af = acceleration_factor
        self.max_af = maximum_acceleration

    def calculate_parabolic_sar(self, high: pd.Series, low: pd.Series) -> pd.Series:
        """Calculate Parabolic SAR"""
        # Initialize SAR values
        sar = pd.Series(index=high.index, dtype=float)
        ep = pd.Series(index=high.index, dtype=float)  # Extreme Point
        af = pd.Series(index=high.index, dtype=float)  # Acceleration Factor
        is_uptrend = pd.Series(index=high.index, dtype=bool)

        # Initial values
        sar.iloc[0] = low.iloc[0]
        ep.iloc[0] = high.iloc[0]
        af.iloc[0] = self.af
        is_uptrend.iloc[0] = True

        # Calculate SAR
        for i in range(1, len(high)):
            if is_uptrend.iloc[i-1]:
                # Uptrend
                sar.iloc[i] = sar.iloc[i-1] + af.iloc[i-1] * (ep.iloc[i-1] - sar.iloc[i-1])

                # Check for new high
                if high.iloc[i] > ep.iloc[i-1]:
                    ep.iloc[i] = high.iloc[i]
                    af.iloc[i] = min(af.iloc[i-1] + self.af, self.max_af)
                else:
                    ep.iloc[i] = ep.iloc[i-1]
                    af.iloc[i] = af.iloc[i-1]

                # Check for trend reversal
                if low.iloc[i] < sar.iloc[i]:
                    is_uptrend.iloc[i] = False
                    sar.iloc[i] = max(ep.iloc[i-1], high.iloc[i])
                    ep.iloc[i] = low.iloc[i]
                    af.iloc[i] = self.af
                else:
                    is_uptrend.iloc[i] = True
            else:
                # Downtrend
                sar.iloc[i] = sar.iloc[i-1] + af.iloc[i-1] * (ep.iloc[i-1] - sar.iloc[i-1])

                # Check for new low
                if low.iloc[i] < ep.iloc[i-1]:
                    ep.iloc[i] = low.iloc[i]
                    af.iloc[i] = min(af.iloc[i-1] + self.af, self.max_af)
                else:
                    ep.iloc[i] = ep.iloc[i-1]
                    af.iloc[i] = af.iloc[i-1]

                # Check for trend reversal
                if high.iloc[i] > sar.iloc[i]:
                    is_uptrend.iloc[i] = True
                    sar.iloc[i] = min(ep.iloc[i-1], low.iloc[i])
                    ep.iloc[i] = high.iloc[i]
                    af.iloc[i] = self.af
                else:
                    is_uptrend.iloc[i] = False

        return sar

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on Parabolic SAR"""
        sar = self.calculate_parabolic_sar(data['high'], data['low'])

        # Initialize signals
        signals = pd.Series(0, index=data.index)

        # Buy when price crosses above SAR
        buy_signal = (
            (data['close'] > sar) &
            (data['close'].shift(1) <= sar.shift(1))
        )
        signals[buy_signal] = Signal.BUY.value

        # Sell when price crosses below SAR
        sell_signal = (
            (data['close'] < sar) &
            (data['close'].shift(1) >= sar.shift(1))
        )
        signals[sell_signal] = Signal.SELL.value

        return signals

    def get_sar_values(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Get Parabolic SAR values for plotting"""
        sar = self.calculate_parabolic_sar(data['high'], data['low'])

        return {
            'sar': sar
        }


class AroonStrategy(BaseStrategy):
    """
    Aroon Indicator Strategy

    Strategy:
    - Aroon Up: Measures strength of uptrend
    - Aroon Down: Measures strength of downtrend
    - Buy when Aroon Up crosses above Aroon Down
    - Sell when Aroon Down crosses above Aroon Up
    """

    def __init__(self, period: int = 25):
        super().__init__(
            name=f"Aroon_{period}",
            params={
                'period': period
            }
        )
        self.period = period

    def calculate_aroon(self, high: pd.Series, low: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Aroon indicator"""
        # Aroon Up: Since highest high
        aroon_up = high.rolling(window=self.period, min_periods=1).apply(
            lambda x: (x.argmax() / (len(x) - 1)) * 100
        )

        # Aroon Down: Since lowest low
        aroon_down = low.rolling(window=self.period, min_periods=1).apply(
            lambda x: (x.argmin() / (len(x) - 1)) * 100
        )

        # Aroon Oscillator
        aroon_oscillator = aroon_up - aroon_down

        return aroon_up, aroon_down, aroon_oscillator

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on Aroon"""
        aroon_up, aroon_down, aroon_oscillator = self.calculate_aroon(
            data['high'], data['low']
        )

        # Initialize signals
        signals = pd.Series(0, index=data.index)

        # Buy when Aroon Up crosses above Aroon Down
        buy_signal = (
            (aroon_up > aroon_down) &
            (aroon_up.shift(1) <= aroon_down.shift(1))
        )
        signals[buy_signal] = Signal.BUY.value

        # Sell when Aroon Down crosses above Aroon Up
        sell_signal = (
            (aroon_down > aroon_up) &
            (aroon_down.shift(1) <= aroon_up.shift(1))
        )
        signals[sell_signal] = Signal.SELL.value

        return signals

    def get_aroon_values(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Get Aroon values for plotting"""
        aroon_up, aroon_down, aroon_oscillator = self.calculate_aroon(
            data['high'], data['low']
        )

        return {
            'aroon_up': aroon_up,
            'aroon_down': aroon_down,
            'aroon_oscillator': aroon_oscillator,
            'zero': pd.Series(0, index=data.index)
        }


# Momentum strategy registry
MOMENTUM_STRATEGIES = {
    'momentum': MomentumStrategy,
    'adx': ADXStrategy,
    'parabolic_sar': ParabolicSARStrategy,
    'aroon': AroonStrategy,
}

__all__ = [
    'MomentumStrategy',
    'ADXStrategy',
    'ParabolicSARStrategy',
    'AroonStrategy',
    'MOMENTUM_STRATEGIES'
]
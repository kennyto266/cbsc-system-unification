"""
Momentum Strategies
動量策略實現
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
import logging

from src.strategies.base import BaseStrategy, BaseSignal

logger = logging.getLogger(__name__)

class ADXStrategy(BaseStrategy):
    """Average Directional Index Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.period = self.parameters.get("period", 14)
        self.trend_threshold = self.parameters.get("trend_threshold", 25)

    def initialize(self, data: pd.DataFrame) -> None:
        """Initialize ADX strategy"""
        if not self.validate_data(data):
            raise ValueError("Invalid data for ADX strategy")

        high, low, close = data['high'], data['low'], data['close']

        # Calculate True Range
        data['tr1'] = high - low
        data['tr2'] = abs(high - close.shift(1))
        data['tr3'] = abs(low - close.shift(1))
        data['tr'] = data[['tr1', 'tr2', 'tr3']].max(axis=1)

        # Calculate directional movement
        data['up_move'] = high - high.shift(1)
        data['down_move'] = low.shift(1) - low

        data['plus_dm'] = np.where((data['up_move'] > data['down_move']) & (data['up_move'] > 0), data['up_move'], 0)
        data['minus_dm'] = np.where((data['down_move'] > data['up_move']) & (data['down_move'] > 0), data['down_move'], 0)

        # Calculate smoothed values
        data['tr_smooth'] = data['tr'].rolling(window=self.period).mean()
        data['plus_di_smooth'] = (data['plus_dm'].rolling(window=self.period).sum() /
                                 data['tr_smooth'].rolling(window=self.period).sum()) * 100
        data['minus_di_smooth'] = (data['minus_dm'].rolling(window=self.period).sum() /
                                  data['tr_smooth'].rolling(window=self.period).sum()) * 100

        # Calculate ADX
        data['dx'] = abs(data['plus_di_smooth'] - data['minus_di_smooth']) / (data['plus_di_smooth'] + data['minus_di_smooth']) * 100
        data['adx'] = data['dx'].rolling(window=self.period).mean()

        # Generate momentum signals
        data['adx_signal'] = np.where(
            (data['adx'] > self.trend_threshold) & (data['plus_di_smooth'] > data['minus_di_smooth']), 1,
            np.where(
                (data['adx'] > self.trend_threshold) & (data['minus_di_smooth'] > data['plus_di_smooth']), -1, 0
            )
        )

        self.is_initialized = True
        logger.info(f"ADX strategy initialized: period={self.period}, threshold={self.trend_threshold}")

    def generate_signals(self, data: pd.DataFrame) -> List[BaseSignal]:
        """Generate ADX trading signals"""
        if not self.is_initialized:
            self.initialize(data)

        signals = []

        for i in range(1, len(data)):
            current_signal = data.iloc[i]["adx_signal"]
            prev_signal = data.iloc[i-1]["adx_signal"]

            # Generate signal when trend changes
            if current_signal != prev_signal and current_signal != 0:
                action = "buy" if current_signal == 1 else "sell"

                # Confidence based on ADX strength
                adx_value = data.iloc[i]["adx"]
                confidence = min(adx_value / 50, 1.0)  # Normalize assuming 50 as strong trend

                signal = BaseSignal(
                    timestamp=data.index[i],
                    action=action,
                    symbol=self.parameters.get("symbol", "DEFAULT"),
                    price=data.iloc[i]["close"],
                    quantity=self.parameters.get("quantity", 1.0),
                    confidence=confidence,
                    metadata={
                        "strategy": "adx",
                        "adx_value": adx_value,
                        "plus_di": data.iloc[i]["plus_di_smooth"],
                        "minus_di": data.iloc[i]["minus_di_smooth"],
                        "trend_strength": "strong" if adx_value > 40 else "moderate" if adx_value > 25 else "weak"
                    }
                )
                signals.append(signal)

        return signals

    def get_required_data_columns(self) -> List[str]:
        """Get required data columns for ADX strategy"""
        return ["high", "low", "close", "volume"]

class SARStrategy(BaseStrategy):
    """Parabolic SAR Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.acceleration_factor = self.parameters.get("acceleration_factor", 0.02)
        self.maximum_acceleration = self.parameters.get("maximum_acceleration", 0.2)

    def initialize(self, data: pd.DataFrame) -> None:
        """Initialize SAR strategy"""
        if not self.validate_data(data):
            raise ValueError("Invalid data for SAR strategy")

        high, low = data['high'], data['low']

        # Initialize SAR values
        data['ep'] = np.nan
        data['af'] = self.acceleration_factor
        data['sar'] = low[0]
        data['position'] = 1  # 1 for long, -1 for short

        ep = high[0]  # Extreme point
        af = self.acceleration_factor
        sar = low[0]
        position = 1  # Start with long position

        for i in range(1, len(data)):
            # Update SAR
            if position == 1:  # Long position
                new_sar = sar + af * (ep - sar)
                # SAR cannot be above previous low or current SAR
                new_sar = min(new_sar, low.iloc[i-1], low.iloc[i])

                # Check if SAR penetrated current low (reverse position)
                if new_sar > low.iloc[i]:
                    position = -1
                    sar = max(high.iloc[i], ep)
                    ep = low.iloc[i]
                    af = self.acceleration_factor
                else:
                    sar = new_sar
                    # Update extreme point if new high
                    if high.iloc[i] > ep:
                        ep = high.iloc[i]
                        af = min(af + self.acceleration_factor, self.maximum_acceleration)
            else:  # Short position
                new_sar = sar + af * (ep - sar)
                # SAR cannot be below previous high or current SAR
                new_sar = max(new_sar, high.iloc[i-1], high.iloc[i])

                # Check if SAR penetrated current high (reverse position)
                if new_sar < high.iloc[i]:
                    position = 1
                    sar = min(low.iloc[i], ep)
                    ep = high.iloc[i]
                    af = self.acceleration_factor
                else:
                    sar = new_sar
                    # Update extreme point if new low
                    if low.iloc[i] < ep:
                        ep = low.iloc[i]
                        af = min(af + self.acceleration_factor, self.maximum_acceleration)

            data.at[data.index[i], 'sar'] = sar
            data.at[data.index[i], 'position'] = position

        # Generate signals based on position changes
        data['sar_signal'] = np.where(data['position'] != data['position'].shift(1),
                                     np.where(data['position'] == 1, 1, -1), 0)

        self.is_initialized = True
        logger.info(f"SAR strategy initialized: af={self.acceleration_factor}, max_af={self.maximum_acceleration}")

    def generate_signals(self, data: pd.DataFrame) -> List[BaseSignal]:
        """Generate SAR trading signals"""
        if not self.is_initialized:
            self.initialize(data)

        signals = []

        for i in range(1, len(data)):
            current_signal = data.iloc[i]["sar_signal"]

            # Generate signal when position changes
            if current_signal != 0:
                action = "buy" if current_signal == 1 else "sell"

                signal = BaseSignal(
                    timestamp=data.index[i],
                    action=action,
                    symbol=self.parameters.get("symbol", "DEFAULT"),
                    price=data.iloc[i]["close"],
                    quantity=self.parameters.get("quantity", 1.0),
                    confidence=0.7,  # SAR typically provides reliable signals
                    metadata={
                        "strategy": "sar",
                        "sar_value": data.iloc[i]["sar"],
                        "position": "long" if data.iloc[i]["position"] == 1 else "short"
                    }
                )
                signals.append(signal)

        return signals

    def get_required_data_columns(self) -> List[str]:
        """Get required data columns for SAR strategy"""
        return ["high", "low", "close", "volume"]

class AroonStrategy(BaseStrategy):
    """Aroon Indicator Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.period = self.parameters.get("period", 14)
        self.signal_threshold = self.parameters.get("signal_threshold", 50)

    def initialize(self, data: pd.DataFrame) -> None:
        """Initialize Aroon strategy"""
        if not self.validate_data(data):
            raise ValueError("Invalid data for Aroon strategy")

        high, low = data['high'], data['low']

        # Calculate Aroon Up and Down
        data['aroon_up'] = high.rolling(window=self.period).apply(
            lambda x: (x.argmax() / (len(x) - 1)) * 100
        )
        data['aroon_down'] = low.rolling(window=self.period).apply(
            lambda x: (x.argmin() / (len(x) - 1)) * 100
        )

        # Generate Aroon signals
        data['aroon_signal'] = np.where(
            (data['aroon_up'] > self.signal_threshold) & (data['aroon_up'] > data['aroon_down']), 1,
            np.where(
                (data['aroon_down'] > self.signal_threshold) & (data['aroon_down'] > data['aroon_up']), -1, 0
            )
        )

        self.is_initialized = True
        logger.info(f"Aroon strategy initialized: period={self.period}, threshold={self.signal_threshold}")

    def generate_signals(self, data: pd.DataFrame) -> List[BaseSignal]:
        """Generate Aroon trading signals"""
        if not self.is_initialized:
            self.initialize(data)

        signals = []

        for i in range(1, len(data)):
            current_signal = data.iloc[i]["aroon_signal"]
            prev_signal = data.iloc[i-1]["aroon_signal"]

            # Generate signal when Aroon crossover occurs
            if current_signal != prev_signal and current_signal != 0:
                action = "buy" if current_signal == 1 else "sell"

                # Confidence based on Aroon strength
                aroon_up = data.iloc[i]["aroon_up"]
                aroon_down = data.iloc[i]["aroon_down"]
                confidence = max(abs(aroon_up - aroon_down)) / 100

                signal = BaseSignal(
                    timestamp=data.index[i],
                    action=action,
                    symbol=self.parameters.get("symbol", "DEFAULT"),
                    price=data.iloc[i]["close"],
                    quantity=self.parameters.get("quantity", 1.0),
                    confidence=confidence,
                    metadata={
                        "strategy": "aroon",
                        "aroon_up": aroon_up,
                        "aroon_down": aroon_down,
                        "trend_direction": "uptrend" if aroon_up > aroon_down else "downtrend"
                    }
                )
                signals.append(signal)

        return signals

    def get_required_data_columns(self) -> List[str]:
        """Get required data columns for Aroon strategy"""
        return ["high", "low", "close", "volume"]

class WilliamsRStrategy(BaseStrategy):
    """Williams %R Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.period = self.parameters.get("period", 14)
        self.overbought_threshold = self.parameters.get("overbought_threshold", -20)
        self.oversold_threshold = self.parameters.get("oversold_threshold", -80)

    def initialize(self, data: pd.DataFrame) -> None:
        """Initialize Williams %R strategy"""
        if not self.validate_data(data):
            raise ValueError("Invalid data for Williams %R strategy")

        high, low, close = data['high'], data['low'], data['close']

        # Calculate Williams %R
        highest_high = high.rolling(window=self.period).max()
        lowest_low = low.rolling(window=self.period).min()
        data['williams_r'] = -100 * (highest_high - close) / (highest_high - lowest_low)

        # Generate signals
        data['williams_r_signal'] = np.where(
            data['williams_r'] > self.oversold_threshold, 1,
            np.where(data['williams_r'] < self.overbought_threshold, -1, 0)
        )

        self.is_initialized = True
        logger.info(f"Williams %R strategy initialized: period={self.period}")

    def generate_signals(self, data: pd.DataFrame) -> List[BaseSignal]:
        """Generate Williams %R trading signals"""
        if not self.is_initialized:
            self.initialize(data)

        signals = []

        for i in range(1, len(data)):
            current_signal = data.iloc[i]["williams_r_signal"]
            prev_signal = data.iloc[i-1]["williams_r_signal"]

            # Generate signal when Williams %R crosses thresholds
            if current_signal != prev_signal and current_signal != 0:
                action = "buy" if current_signal == 1 else "sell"

                # Confidence based on how far from middle (-50)
                williams_value = data.iloc[i]["williams_r"]
                confidence = abs(williams_value + 50) / 50

                signal = BaseSignal(
                    timestamp=data.index[i],
                    action=action,
                    symbol=self.parameters.get("symbol", "DEFAULT"),
                    price=data.iloc[i]["close"],
                    quantity=self.parameters.get("quantity", 1.0),
                    confidence=confidence,
                    metadata={
                        "strategy": "williams_r",
                        "williams_r_value": williams_value,
                        "overbought": self.overbought_threshold,
                        "oversold": self.oversold_threshold
                    }
                )
                signals.append(signal)

        return signals

    def get_required_data_columns(self) -> List[str]:
        """Get required data columns for Williams %R strategy"""
        return ["high", "low", "close", "volume"]
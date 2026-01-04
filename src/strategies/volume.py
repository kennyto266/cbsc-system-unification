"""
Volume Strategies
成交量策略實現
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
import logging

from src.strategies.base import BaseStrategy, BaseSignal

logger = logging.getLogger(__name__)

class OBVStrategy(BaseStrategy):
    """On-Balance Volume Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.ma_period = self.parameters.get("ma_period", 10)
        self.signal_threshold = self.parameters.get("signal_threshold", 0.02)

    def initialize(self, data: pd.DataFrame) -> None:
        """Initialize OBV strategy"""
        if not self.validate_data(data):
            raise ValueError("Invalid data for OBV strategy")

        close, volume = data['close'], data['volume']

        # Calculate OBV
        price_change = close.diff()
        data['obv'] = np.where(price_change > 0, volume,
                              np.where(price_change < 0, -volume, 0)).cumsum()

        # Calculate OBV moving average
        data['obv_ma'] = data['obv'].rolling(window=self.ma_period).mean()

        # Calculate OBV rate of change
        data['obv_roc'] = data['obv'].pct_change()

        # Generate signals
        data['obv_signal'] = np.where(
            (data['obv'] > data['obv_ma']) & (data['obv_roc'] > self.signal_threshold), 1,
            np.where(
                (data['obv'] < data['obv_ma']) & (data['obv_roc'] < -self.signal_threshold), -1, 0
            )
        )

        self.is_initialized = True
        logger.info(f"OBV strategy initialized: ma_period={self.ma_period}, threshold={self.signal_threshold}")

    def generate_signals(self, data: pd.DataFrame) -> List[BaseSignal]:
        """Generate OBV trading signals"""
        if not self.is_initialized:
            self.initialize(data)

        signals = []

        for i in range(1, len(data)):
            current_signal = data.iloc[i]["obv_signal"]
            prev_signal = data.iloc[i-1]["obv_signal"]

            # Generate signal when OBV changes
            if current_signal != prev_signal and current_signal != 0:
                action = "buy" if current_signal == 1 else "sell"

                # Confidence based on OBV ROC magnitude
                obv_roc = abs(data.iloc[i]["obv_roc"])
                confidence = min(obv_roc / 0.1, 1.0)  # Normalize assuming 10% as strong

                signal = BaseSignal(
                    timestamp=data.index[i],
                    action=action,
                    symbol=self.parameters.get("symbol", "DEFAULT"),
                    price=data.iloc[i]["close"],
                    quantity=self.parameters.get("quantity", 1.0),
                    confidence=confidence,
                    metadata={
                        "strategy": "obv",
                        "obv_value": data.iloc[i]["obv"],
                        "obv_ma": data.iloc[i]["obv_ma"],
                        "obv_roc": data.iloc[i]["obv_roc"]
                    }
                )
                signals.append(signal)

        return signals

    def get_required_data_columns(self) -> List[str]:
        """Get required data columns for OBV strategy"""
        return ["close", "volume"]

class VWAPStrategy(BaseStrategy):
    """Volume Weighted Average Price Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.session_reset = self.parameters.get("session_reset", True)
        self.deviation_threshold = self.parameters.get("deviation_threshold", 0.02)

    def initialize(self, data: pd.DataFrame) -> None:
        """Initialize VWAP strategy"""
        if not self.validate_data(data):
            raise ValueError("Invalid data for VWAP strategy")

        high, low, close, volume = data['high'], data['low'], data['close'], data['volume']

        # Calculate typical price
        data['typical_price'] = (high + low + close) / 3

        # Calculate cumulative values
        data['cumulative_volume'] = volume.cumsum()
        data['cumulative_price_volume'] = (data['typical_price'] * volume).cumsum()

        # Calculate VWAP
        data['vwap'] = data['cumulative_price_volume'] / data['cumulative_volume']

        # Reset VWAP at session boundaries if configured
        if self.session_reset:
            # Simple reset based on volume drop (placeholder for proper session detection)
            volume_drop = volume < volume.shift(1) * 0.1
            session_groups = volume_drop.cumsum()

            data['vwap'] = data.groupby(session_groups)[['typical_price', 'volume']].apply(
                lambda x: ((x['typical_price'] * x['volume']).cumsum() / x['volume'].cumsum())
            ).reset_index(level=0, drop=True)

        # Calculate deviation from VWAP
        data['vwap_deviation'] = (close - data['vwap']) / data['vwap']

        # Generate signals
        data['vwap_signal'] = np.where(
            data['vwap_deviation'] > self.deviation_threshold, -1,  # Price above VWAP = sell
            np.where(
                data['vwap_deviation'] < -self.deviation_threshold, 1,  # Price below VWAP = buy
                0
            )
        )

        self.is_initialized = True
        logger.info(f"VWAP strategy initialized: threshold={self.deviation_threshold}")

    def generate_signals(self, data: pd.DataFrame) -> List[BaseSignal]:
        """Generate VWAP trading signals"""
        if not self.is_initialized:
            self.initialize(data)

        signals = []

        for i in range(1, len(data)):
            current_signal = data.iloc[i]["vwap_signal"]
            prev_signal = data.iloc[i-1]["vwap_signal"]

            # Generate signal when price crosses VWAP threshold
            if current_signal != prev_signal and current_signal != 0:
                action = "buy" if current_signal == 1 else "sell"

                # Confidence based on deviation magnitude
                deviation = abs(data.iloc[i]["vwap_deviation"])
                confidence = min(deviation / (self.deviation_threshold * 2), 1.0)

                signal = BaseSignal(
                    timestamp=data.index[i],
                    action=action,
                    symbol=self.parameters.get("symbol", "DEFAULT"),
                    price=data.iloc[i]["close"],
                    quantity=self.parameters.get("quantity", 1.0),
                    confidence=confidence,
                    metadata={
                        "strategy": "vwap",
                        "vwap_value": data.iloc[i]["vwap"],
                        "vwap_deviation": data.iloc[i]["vwap_deviation"],
                        "price_position": "below" if data.iloc[i]["close"] < data.iloc[i]["vwap"] else "above"
                    }
                )
                signals.append(signal)

        return signals

    def get_required_data_columns(self) -> List[str]:
        """Get required data columns for VWAP strategy"""
        return ["high", "low", "close", "volume"]

class MFIStrategy(BaseStrategy):
    """Money Flow Index Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.period = self.parameters.get("period", 14)
        self.overbought_threshold = self.parameters.get("overbought_threshold", 80)
        self.oversold_threshold = self.parameters.get("oversold_threshold", 20)

    def initialize(self, data: pd.DataFrame) -> None:
        """Initialize MFI strategy"""
        if not self.validate_data(data):
            raise ValueError("Invalid data for MFI strategy")

        high, low, close, volume = data['high'], data['low'], data['close'], data['volume']

        # Calculate typical price
        data['typical_price'] = (high + low + close) / 3

        # Calculate raw money flow
        data['raw_money_flow'] = data['typical_price'] * volume

        # Determine positive and negative money flow
        price_change = data['typical_price'].diff()
        data['positive_mf'] = np.where(price_change > 0, data['raw_money_flow'], 0)
        data['negative_mf'] = np.where(price_change < 0, data['raw_money_flow'], 0)

        # Calculate money flow ratios
        data['positive_mf_sum'] = data['positive_mf'].rolling(window=self.period).sum()
        data['negative_mf_sum'] = data['negative_mf'].rolling(window=self.period).sum()

        # Calculate MFI
        data['mfi'] = 100 - (100 / (1 + data['positive_mf_sum'] / data['negative_mf_sum']))

        # Generate signals
        data['mfi_signal'] = np.where(
            data['mfi'] < self.oversold_threshold, 1,
            np.where(data['mfi'] > self.overbought_threshold, -1, 0)
        )

        self.is_initialized = True
        logger.info(f"MFI strategy initialized: period={self.period}")

    def generate_signals(self, data: pd.DataFrame) -> List[BaseSignal]:
        """Generate MFI trading signals"""
        if not self.is_initialized:
            self.initialize(data)

        signals = []

        for i in range(1, len(data)):
            current_signal = data.iloc[i]["mfi_signal"]
            prev_signal = data.iloc[i-1]["mfi_signal"]

            # Generate signal when MFI crosses thresholds
            if current_signal != prev_signal and current_signal != 0:
                action = "buy" if current_signal == 1 else "sell"

                # Confidence based on how far MFI is from neutral (50)
                mfi_value = data.iloc[i]["mfi"]
                confidence = abs(mfi_value - 50) / 50

                signal = BaseSignal(
                    timestamp=data.index[i],
                    action=action,
                    symbol=self.parameters.get("symbol", "DEFAULT"),
                    price=data.iloc[i]["close"],
                    quantity=self.parameters.get("quantity", 1.0),
                    confidence=confidence,
                    metadata={
                        "strategy": "mfi",
                        "mfi_value": mfi_value,
                        "overbought": self.overbought_threshold,
                        "oversold": self.oversold_threshold
                    }
                )
                signals.append(signal)

        return signals

    def get_required_data_columns(self) -> List[str]:
        """Get required data columns for MFI strategy"""
        return ["high", "low", "close", "volume"]

class VolumeProfileStrategy(BaseStrategy):
    """Volume Profile Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.lookback_period = self.parameters.get("lookback_period", 100)
        self.price_levels = self.parameters.get("price_levels", 20)
        self.high_volume_threshold = self.parameters.get("high_volume_threshold", 1.5)

    def initialize(self, data: pd.DataFrame) -> None:
        """Initialize Volume Profile strategy"""
        if not self.validate_data(data):
            raise ValueError("Invalid data for Volume Profile strategy")

        high, low, close, volume = data['high'], data['low'], data['close'], data['volume']

        # Calculate price levels for volume profile
        min_price = low.rolling(window=self.lookback_period).min()
        max_price = high.rolling(window=self.lookback_period).max()

        # Create price bins
        data['price_bin'] = ((close - min_price) / (max_price - min_price) * self.price_levels).astype(int)
        data['price_bin'] = data['price_bin'].clip(0, self.price_levels - 1)

        # Calculate volume at each price level
        def calculate_volume_profile(group):
            price_range = max_price.iloc[group.name] - min_price.iloc[group.name]
            if price_range == 0:
                return pd.Series([0] * self.price_levels)

            bin_size = price_range / self.price_levels
            volume_profile = np.zeros(self.price_levels)

            for i in range(len(group)):
                price = close.iloc[group.index[i]]
                vol = volume.iloc[group.index[i]]
                bin_idx = int((price - min_price.iloc[group.name]) / bin_size)
                bin_idx = max(0, min(bin_idx, self.price_levels - 1))
                volume_profile[bin_idx] += vol

            return pd.Series(volume_profile)

        # Apply volume profile calculation
        volume_profiles = data.groupby(data.index // self.lookback_period).apply(calculate_volume_profile)

        # Find high volume nodes
        avg_volume = volume_profiles.mean(axis=1)
        high_volume_nodes = volume_profiles > avg_volume * self.high_volume_threshold

        # Generate signals based on price vs volume profile
        data['volume_profile_signal'] = 0  # Placeholder for actual implementation
        data['volume_profile_signal'] = np.where(
            close < close.rolling(window=20).mean(), 1, -1  # Simple trend signal as placeholder
        )

        self.is_initialized = True
        logger.info(f"Volume Profile strategy initialized: period={self.lookback_period}")

    def generate_signals(self, data: pd.DataFrame) -> List[BaseSignal]:
        """Generate Volume Profile trading signals"""
        if not self.is_initialized:
            self.initialize(data)

        signals = []

        for i in range(1, len(data)):
            current_signal = data.iloc[i]["volume_profile_signal"]
            prev_signal = data.iloc[i-1]["volume_profile_signal"]

            # Generate signal when trend changes
            if current_signal != prev_signal and current_signal != 0:
                action = "buy" if current_signal == 1 else "sell"

                signal = BaseSignal(
                    timestamp=data.index[i],
                    action=action,
                    symbol=self.parameters.get("symbol", "DEFAULT"),
                    price=data.iloc[i]["close"],
                    quantity=self.parameters.get("quantity", 1.0),
                    confidence=0.6,  # Medium confidence for volume profile
                    metadata={
                        "strategy": "volume_profile",
                        "price_bin": data.iloc[i].get("price_bin", 0),
                        "volume_level": self.lookback_period
                    }
                )
                signals.append(signal)

        return signals

    def get_required_data_columns(self) -> List[str]:
        """Get required data columns for Volume Profile strategy"""
        return ["high", "low", "close", "volume"]
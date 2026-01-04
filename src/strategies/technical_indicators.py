"""
Technical Indicator Strategies
技術指標策略實現
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
import logging

from src.strategies.base import BaseStrategy, BaseSignal

logger = logging.getLogger(__name__)

class MACrossoverStrategy(BaseStrategy):
    """Moving Average Crossover Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.fast_period = self.parameters.get("fast_period", 10)
        self.slow_period = self.parameters.get("slow_period", 30)
        self.signal_threshold = self.parameters.get("signal_threshold", 0.001)

    def initialize(self, data: pd.DataFrame) -> None:
        """Initialize strategy with historical data"""
        if not self.validate_data(data):
            raise ValueError("Invalid data for MA crossover strategy")

        # Calculate moving averages
        data[f"ma_{self.fast_period}"] = data["close"].rolling(window=self.fast_period).mean()
        data[f"ma_{self.slow_period}"] = data["close"].rolling(window=self.slow_period).mean()

        # Calculate crossover signals
        data["ma_diff"] = data[f"ma_{self.fast_period}"] - data[f"ma_{self.slow_period}"]
        data["ma_signal"] = np.where(data["ma_diff"] > self.signal_threshold, 1,
                                   np.where(data["ma_diff"] < -self.signal_threshold, -1, 0))

        self.is_initialized = True
        logger.info(f"MA Crossover strategy initialized: fast={self.fast_period}, slow={self.slow_period}")

    def generate_signals(self, data: pd.DataFrame) -> List[BaseSignal]:
        """Generate trading signals based on MA crossover"""
        if not self.is_initialized:
            self.initialize(data)

        signals = []

        for i in range(1, len(data)):
            current_signal = data.iloc[i]["ma_signal"]
            prev_signal = data.iloc[i-1]["ma_signal"]

            # Generate signal on crossover
            if current_signal != prev_signal and current_signal != 0:
                action = "buy" if current_signal == 1 else "sell"

                signal = BaseSignal(
                    timestamp=data.index[i],
                    action=action,
                    symbol=self.parameters.get("symbol", "DEFAULT"),
                    price=data.iloc[i]["close"],
                    quantity=self.parameters.get("quantity", 1.0),
                    confidence=min(abs(data.iloc[i]["ma_diff"]) / self.signal_threshold, 1.0),
                    metadata={
                        "strategy": "ma_crossover",
                        "fast_ma": data.iloc[i][f"ma_{self.fast_period}"],
                        "slow_ma": data.iloc[i][f"ma_{self.slow_period}"],
                        "ma_diff": data.iloc[i]["ma_diff"]
                    }
                )
                signals.append(signal)

        return signals

    def get_required_data_columns(self) -> List[str]:
        """Get required data columns for this strategy"""
        return ["close", "volume"]

class RSIStrategy(BaseStrategy):
    """Relative Strength Index Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.period = self.parameters.get("period", 14)
        self.overbought_threshold = self.parameters.get("overbought_threshold", 70)
        self.oversold_threshold = self.parameters.get("oversold_threshold", 30)

    def initialize(self, data: pd.DataFrame) -> None:
        """Initialize RSI strategy"""
        if not self.validate_data(data):
            raise ValueError("Invalid data for RSI strategy")

        # Calculate RSI
        delta = data["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()

        rs = gain / loss
        data["rsi"] = 100 - (100 / (1 + rs))

        # Generate RSI signals
        data["rsi_signal"] = np.where(data["rsi"] < self.oversold_threshold, 1,
                                    np.where(data["rsi"] > self.overbought_threshold, -1, 0))

        self.is_initialized = True
        logger.info(f"RSI strategy initialized: period={self.period}")

    def generate_signals(self, data: pd.DataFrame) -> List[BaseSignal]:
        """Generate RSI trading signals"""
        if not self.is_initialized:
            self.initialize(data)

        signals = []

        for i in range(1, len(data)):
            current_signal = data.iloc[i]["rsi_signal"]
            prev_signal = data.iloc[i-1]["rsi_signal"]

            # Generate signal when RSI crosses thresholds
            if current_signal != prev_signal and current_signal != 0:
                action = "buy" if current_signal == 1 else "sell"

                # Calculate confidence based on how far RSI is from neutral (50)
                rsi_value = data.iloc[i]["rsi"]
                confidence = abs(rsi_value - 50) / 50  # Normalize to 0-1

                signal = BaseSignal(
                    timestamp=data.index[i],
                    action=action,
                    symbol=self.parameters.get("symbol", "DEFAULT"),
                    price=data.iloc[i]["close"],
                    quantity=self.parameters.get("quantity", 1.0),
                    confidence=confidence,
                    metadata={
                        "strategy": "rsi",
                        "rsi_value": rsi_value,
                        "overbought": self.overbought_threshold,
                        "oversold": self.oversold_threshold
                    }
                )
                signals.append(signal)

        return signals

    def get_required_data_columns(self) -> List[str]:
        """Get required data columns for RSI strategy"""
        return ["close", "volume"]

class BollingerBandsStrategy(BaseStrategy):
    """Bollinger Bands Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.period = self.parameters.get("period", 20)
        self.std_dev = self.parameters.get("std_dev", 2)

    def initialize(self, data: pd.DataFrame) -> None:
        """Initialize Bollinger Bands strategy"""
        if not self.validate_data(data):
            raise ValueError("Invalid data for Bollinger Bands strategy")

        # Calculate Bollinger Bands
        data["bb_middle"] = data["close"].rolling(window=self.period).mean()
        data["bb_std"] = data["close"].rolling(window=self.period).std()
        data["bb_upper"] = data["bb_middle"] + (data["bb_std"] * self.std_dev)
        data["bb_lower"] = data["bb_middle"] - (data["bb_std"] * self.std_dev)

        # Generate signals based on band penetration
        data["bb_position"] = (data["close"] - data["bb_lower"]) / (data["bb_upper"] - data["bb_lower"])
        data["bb_signal"] = np.where(data["bb_position"] < 0, 1,
                                   np.where(data["bb_position"] > 1, -1, 0))

        self.is_initialized = True
        logger.info(f"Bollinger Bands strategy initialized: period={self.period}, std={self.std_dev}")

    def generate_signals(self, data: pd.DataFrame) -> List[BaseSignal]:
        """Generate Bollinger Bands trading signals"""
        if not self.is_initialized:
            self.initialize(data)

        signals = []

        for i in range(1, len(data)):
            current_signal = data.iloc[i]["bb_signal"]
            prev_signal = data.iloc[i-1]["bb_signal"]

            # Generate signal when price penetrates bands
            if current_signal != prev_signal and current_signal != 0:
                action = "buy" if current_signal == 1 else "sell"

                # Confidence based on how far price penetrates the band
                bb_position = data.iloc[i]["bb_position"]
                confidence = min(abs(bb_position) * 2, 1.0) if bb_position < 0 or bb_position > 1 else 0.5

                signal = BaseSignal(
                    timestamp=data.index[i],
                    action=action,
                    symbol=self.parameters.get("symbol", "DEFAULT"),
                    price=data.iloc[i]["close"],
                    quantity=self.parameters.get("quantity", 1.0),
                    confidence=confidence,
                    metadata={
                        "strategy": "bollinger_bands",
                        "bb_upper": data.iloc[i]["bb_upper"],
                        "bb_middle": data.iloc[i]["bb_middle"],
                        "bb_lower": data.iloc[i]["bb_lower"],
                        "bb_position": bb_position
                    }
                )
                signals.append(signal)

        return signals

    def get_required_data_columns(self) -> List[str]:
        """Get required data columns for Bollinger Bands strategy"""
        return ["close", "volume"]

class MACDStrategy(BaseStrategy):
    """MACD (Moving Average Convergence Divergence) Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.fast_period = self.parameters.get("fast_period", 12)
        self.slow_period = self.parameters.get("slow_period", 26)
        self.signal_period = self.parameters.get("signal_period", 9)

    def initialize(self, data: pd.DataFrame) -> None:
        """Initialize MACD strategy"""
        if not self.validate_data(data):
            raise ValueError("Invalid data for MACD strategy")

        # Calculate MACD
        exp1 = data["close"].ewm(span=self.fast_period).mean()
        exp2 = data["close"].ewm(span=self.slow_period).mean()
        data["macd"] = exp1 - exp2
        data["macd_signal"] = data["macd"].ewm(span=self.signal_period).mean()
        data["macd_histogram"] = data["macd"] - data["macd_signal"]

        # Generate signals based on MACD crossover
        data["macd_crossover"] = np.where(data["macd"] > data["macd_signal"], 1, -1)

        self.is_initialized = True
        logger.info(f"MACD strategy initialized: fast={self.fast_period}, slow={self.slow_period}, signal={self.signal_period}")

    def generate_signals(self, data: pd.DataFrame) -> List[BaseSignal]:
        """Generate MACD trading signals"""
        if not self.is_initialized:
            self.initialize(data)

        signals = []

        for i in range(1, len(data)):
            current_crossover = data.iloc[i]["macd_crossover"]
            prev_crossover = data.iloc[i-1]["macd_crossover"]

            # Generate signal on MACD crossover
            if current_crossover != prev_crossover:
                action = "buy" if current_crossover == 1 else "sell"

                # Confidence based on histogram strength
                histogram = data.iloc[i]["macd_histogram"]
                confidence = min(abs(histogram) / 0.01, 1.0)  # Normalize assuming 0.01 as strong signal

                signal = BaseSignal(
                    timestamp=data.index[i],
                    action=action,
                    symbol=self.parameters.get("symbol", "DEFAULT"),
                    price=data.iloc[i]["close"],
                    quantity=self.parameters.get("quantity", 1.0),
                    confidence=confidence,
                    metadata={
                        "strategy": "macd",
                        "macd": data.iloc[i]["macd"],
                        "macd_signal": data.iloc[i]["macd_signal"],
                        "macd_histogram": histogram
                    }
                )
                signals.append(signal)

        return signals

    def get_required_data_columns(self) -> List[str]:
        """Get required data columns for MACD strategy"""
        return ["close", "volume"]
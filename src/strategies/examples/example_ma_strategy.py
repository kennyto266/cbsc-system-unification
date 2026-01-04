"""
Example Moving Average Crossover Strategy

This example demonstrates how to create a strategy that can be dynamically
loaded by the enhanced strategy factory.
"""

from uuid import uuid4
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from ..base import BaseStrategy
from ..enhanced_factory import StrategyType, StrategyMetadata
from ..technical_indicators import calculate_sma


class ExampleMAStrategy(BaseStrategy):
    """
    Example Moving Average Crossover Strategy

    Generates buy/sell signals when fast and slow moving averages cross.
    Demonstrates proper strategy structure for factory loading.
    """

    # Strategy metadata for factory registration
    STRATEGY_NAME = "example_ma_crossover"
    STRATEGY_TYPE = StrategyType.MOMENTUM
    DESCRIPTION = "Example moving average crossover strategy for demonstration"
    VERSION = "1.0.0"
    AUTHOR = "CBSC Team"
    TAGS = ["example", "moving_average", "crossover", "momentum"]

    # Strategy parameters schema
    PARAMETERS = {
        "fast_period": {
            "type": int,
            "default": 10,
            "min": 1,
            "max": 50,
            "required": True,
            "description": "Fast moving average period"
        },
        "slow_period": {
            "type": int,
            "default": 20,
            "min": 10,
            "max": 200,
            "required": True,
            "description": "Slow moving average period"
        },
        "symbols": {
            "type": list,
            "default": ["AAPL", "MSFT", "SPY"],
            "required": True,
            "description": "List of symbols to trade"
        },
        "position_size": {
            "type": float,
            "default": 0.1,
            "min": 0.01,
            "max": 1.0,
            "required": False,
            "description": "Position size as fraction of capital"
        },
        "stop_loss": {
            "type": float,
            "default": 0.05,
            "min": 0.01,
            "max": 0.20,
            "required": False,
            "description": "Stop loss percentage"
        },
        "take_profit": {
            "type": float,
            "default": 0.10,
            "min": 0.02,
            "max": 0.50,
            "required": False,
            "description": "Take profit percentage"
        }
    }

    # Required data for this strategy
    REQUIRED_DATA = ["price", "volume"]

    # Strategy performance expectations
    RISK_LEVEL = "medium"
    EXPECTED_RETURN = 0.15  # 15% annual return expectation
    MAX_DRAWDOWN = 0.10     # 10% maximum drawdown expectation

    # Dependencies
    DEPENDENCIES = ["pandas", "numpy", "talib"]

    def __init__(self, instance_id: uuid4, config: Dict[str, Any], metadata: StrategyMetadata):
        """
        Initialize the MA Crossover strategy

        Args:
            instance_id: Unique identifier for this strategy instance
            config: Strategy configuration parameters
            metadata: Strategy metadata from factory
        """
        super().__init__(instance_id, config, metadata)

        # Extract configuration parameters
        self.fast_period = config.get("fast_period", 10)
        self.slow_period = config.get("slow_period", 20)
        self.symbols = config.get("symbols", ["AAPL", "MSFT", "SPY"])
        self.position_size = config.get("position_size", 0.1)
        self.stop_loss = config.get("stop_loss", 0.05)
        self.take_profit = config.get("take_profit", 0.10)

        # Validate parameters
        self._validate_parameters()

        # Initialize strategy state
        self.positions = {}
        self.signals = {}
        self.performance_metrics = {
            "total_trades": 0,
            "winning_trades": 0,
            "total_pnl": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0
        }

        # Initialize indicators for each symbol
        self.indicators = {}
        for symbol in self.symbols:
            self.indicators[symbol] = {
                "fast_ma": [],
                "slow_ma": [],
                "last_signal": None,
                "last_cross": None
            }

    def _validate_parameters(self) -> None:
        """Validate strategy parameters"""
        if self.fast_period >= self.slow_period:
            raise ValueError("Fast period must be less than slow period")

        if not self.symbols:
            raise ValueError("At least one symbol must be specified")

        if not 0 < self.position_size <= 1:
            raise ValueError("Position size must be between 0 and 1")

    def initialize(self, data: Dict[str, pd.DataFrame]) -> None:
        """
        Initialize strategy with historical data

        Args:
            data: Dictionary of symbol -> DataFrame with OHLCV data
        """
        for symbol in self.symbols:
            if symbol not in data:
                raise ValueError(f"No data provided for symbol {symbol}")

            df = data[symbol]

            # Validate data columns
            required_columns = ["open", "high", "low", "close", "volume"]
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"Missing required columns for symbol {symbol}")

            # Calculate initial indicators
            self.indicators[symbol]["fast_ma"] = calculate_sma(
                df["close"], self.fast_period
            ).fillna(method='bfill')

            self.indicators[symbol]["slow_ma"] = calculate_sma(
                df["close"], self.slow_period
            ).fillna(method='bfill')

            # Determine initial signal
            self._update_signal(symbol, df)

    def update(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Update strategy with new market data

        Args:
            data: Dictionary of symbol -> DataFrame with latest OHLCV data

        Returns:
            Dictionary containing signals and metrics
        """
        signals = {}

        for symbol in self.symbols:
            if symbol not in data:
                continue

            df = data[symbol]

            # Update indicators
            self._update_indicators(symbol, df)

            # Generate trading signals
            signal = self._update_signal(symbol, df)

            if signal:
                signals[symbol] = signal

        # Calculate performance metrics
        self._update_performance_metrics()

        return {
            "signals": signals,
            "performance": self.performance_metrics,
            "positions": self.positions,
            "timestamp": pd.Timestamp.now()
        }

    def _update_indicators(self, symbol: str, df: pd.DataFrame) -> None:
        """Update moving averages for a symbol"""
        if len(df) < self.slow_period:
            return

        # Get latest close price
        close_price = df["close"].iloc[-1]

        # Update fast MA
        fast_ma_values = self.indicators[symbol]["fast_ma"]
        fast_ma_values.append(close_price)
        if len(fast_ma_values) > self.fast_period:
            fast_ma_values.pop(0)

        # Update slow MA
        slow_ma_values = self.indicators[symbol]["slow_ma"]
        slow_ma_values.append(close_price)
        if len(slow_ma_values) > self.slow_period:
            slow_ma_values.pop(0)

        # Calculate current MAs
        if len(fast_ma_values) >= self.fast_period:
            self.indicators[symbol]["current_fast_ma"] = np.mean(fast_ma_values)

        if len(slow_ma_values) >= self.slow_period:
            self.indicators[symbol]["current_slow_ma"] = np.mean(slow_ma_values)

    def _update_signal(self, symbol: str, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Update trading signal for a symbol"""
        indicator_data = self.indicators[symbol]

        # Check if we have enough data
        if "current_fast_ma" not in indicator_data or "current_slow_ma" not in indicator_data:
            return None

        fast_ma = indicator_data["current_fast_ma"]
        slow_ma = indicator_data["current_slow_ma"]
        current_price = df["close"].iloc[-1]
        last_signal = indicator_data.get("last_signal")

        # Generate signals
        signal = None

        # Bullish crossover (fast MA crosses above slow MA)
        if fast_ma > slow_ma and last_signal != "buy":
            signal = {
                "symbol": symbol,
                "action": "buy",
                "price": current_price,
                "quantity": self.position_size,
                "reason": "Bullish MA crossover",
                "fast_ma": fast_ma,
                "slow_ma": slow_ma,
                "stop_loss": current_price * (1 - self.stop_loss),
                "take_profit": current_price * (1 + self.take_profit)
            }
            indicator_data["last_signal"] = "buy"
            indicator_data["last_cross"] = pd.Timestamp.now()

        # Bearish crossover (fast MA crosses below slow MA)
        elif fast_ma < slow_ma and last_signal != "sell":
            # Check if we have a position to close
            if symbol in self.positions:
                signal = {
                    "symbol": symbol,
                    "action": "sell",
                    "price": current_price,
                    "quantity": self.positions[symbol]["quantity"],
                    "reason": "Bearish MA crossover",
                    "fast_ma": fast_ma,
                    "slow_ma": slow_ma,
                    "pnl": self._calculate_pnl(symbol, current_price)
                }
                del self.positions[symbol]

            indicator_data["last_signal"] = "sell"
            indicator_data["last_cross"] = pd.Timestamp.now()

        return signal

    def _calculate_pnl(self, symbol: str, current_price: float) -> float:
        """Calculate profit/loss for a position"""
        if symbol not in self.positions:
            return 0.0

        position = self.positions[symbol]
        entry_price = position["entry_price"]
        quantity = position["quantity"]

        return (current_price - entry_price) * quantity

    def _update_performance_metrics(self) -> None:
        """Update strategy performance metrics"""
        # This would typically calculate various performance metrics
        # For now, we'll just update basic metrics
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get current strategy status"""
        return {
            "strategy_name": self.STRATEGY_NAME,
            "instance_id": str(self.instance_id),
            "is_active": self.is_active,
            "parameters": {
                "fast_period": self.fast_period,
                "slow_period": self.slow_period,
                "symbols": self.symbols,
                "position_size": self.position_size
            },
            "positions": self.positions,
            "performance": self.performance_metrics,
            "last_update": pd.Timestamp.now()
        }

    def cleanup(self) -> None:
        """Cleanup resources when strategy is stopped"""
        # Close any open positions
        for symbol in list(self.positions.keys()):
            # In a real implementation, this would generate sell signals
            del self.positions[symbol]

        # Clear indicators
        self.indicators.clear()

        # Mark as inactive
        self.is_active = False
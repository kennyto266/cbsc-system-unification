"""
Base strategy class
基礎策略類
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    import pandas as pd
    import numpy as np
except ImportError:
    pd = None
    np = None

class BaseSignal:
    """Trading signal representation"""

    def __init__(self, timestamp: datetime, action: str, symbol: str,
                 price: float, quantity: float, confidence: float = 1.0,
                 metadata: Optional[Dict[str, Any]] = None):
        self.timestamp = timestamp
        self.action = action  # 'buy', 'sell', 'hold'
        self.symbol = symbol
        self.price = price
        self.quantity = quantity
        self.confidence = confidence
        self.metadata = metadata or {}

    def __repr__(self):
        return f"Signal({self.timestamp}, {self.action}, {self.symbol}, {self.price}, {self.quantity})"

class BaseStrategy(ABC):
    """Base strategy class"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", self.__class__.__name__)
        self.strategy_type = config.get("strategy_type", "unknown")
        self.parameters = config.get("parameters", {})
        self.is_initialized = False
        self.last_update = None

    @abstractmethod
    def initialize(self, data: pd.DataFrame) -> None:
        """Initialize strategy with historical data"""
        pass

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[BaseSignal]:
        """Generate trading signals"""
        pass

    @abstractmethod
    def get_required_data_columns(self) -> List[str]:
        """Get required data columns for this strategy"""
        pass

    def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """Update strategy parameters"""
        self.parameters.update(parameters)
        self.last_update = datetime.utcnow()

    def get_parameters(self) -> Dict[str, Any]:
        """Get current strategy parameters"""
        return self.parameters.copy()

    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate data contains required columns"""
        required_cols = self.get_required_data_columns()
        missing_cols = [col for col in required_cols if col not in data.columns]

        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            return False

        return True

    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "strategy_type": self.strategy_type,
            "parameters": self.parameters,
            "is_initialized": self.is_initialized,
            "last_update": self.last_update
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get strategy performance metrics"""
        return {
            "total_signals": 0,
            "buy_signals": 0,
            "sell_signals": 0,
            "hold_signals": 0,
            "avg_confidence": 0.0,
            "last_signal_time": None
        }
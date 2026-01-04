"""
Strategy Factory Pattern Implementation
策略工廠模式實現
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
from enum import Enum
import logging

from src.strategies.base import BaseStrategy
from src.strategies.technical_indicators import *
from src.strategies.momentum import *
from src.strategies.volume import *

logger = logging.getLogger(__name__)

class StrategyType(Enum):
    """Strategy type enumeration"""
    TECHNICAL_INDICATORS = "technical_indicators"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    VOLUME = "volume"
    VOLATILITY = "volatility"
    FUNDAMENTAL = "fundamental"
    PORTFOLIO = "portfolio"
    ARBITRAGE = "arbitrage"
    MACRO = "macro"

class StrategyFactory:
    """Strategy factory for creating strategy instances"""

    _strategies: Dict[str, Type[BaseStrategy]] = {}
    _initialized = False

    @classmethod
    def register_strategy(cls, strategy_class: Type[BaseStrategy]) -> None:
        """Register a strategy class"""
        if not issubclass(strategy_class, BaseStrategy):
            raise ValueError("Strategy must inherit from BaseStrategy")

        strategy_name = strategy_class.__name__
        cls._strategies[strategy_name] = strategy_class
        logger.info(f"Registered strategy: {strategy_name}")

    @classmethod
    def register_by_code(cls, code: str, strategy_class: Type[BaseStrategy]) -> None:
        """Register a strategy by code"""
        if not issubclass(strategy_class, BaseStrategy):
            raise ValueError("Strategy must inherit from BaseStrategy")

        cls._strategies[code] = strategy_class
        logger.info(f"Registered strategy by code: {code}")

    @classmethod
    def create_strategy(cls, strategy_config: Dict[str, Any]) -> BaseStrategy:
        """Create strategy instance from configuration"""
        strategy_type = strategy_config.get("strategy_type")
        if not strategy_type:
            raise ValueError("Strategy type is required in configuration")

        # Get strategy class
        strategy_class = cls._strategies.get(strategy_type)
        if not strategy_class:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        # Create instance
        try:
            strategy = strategy_class(strategy_config)
            logger.info(f"Created strategy: {strategy.__class__.__name__} ({strategy_type})")
            return strategy
        except Exception as e:
            logger.error(f"Failed to create strategy {strategy_type}: {e}")
            raise

    @classmethod
    def get_available_strategies(cls) -> Dict[str, str]:
        """Get all available strategies"""
        return {
            code: cls._strategies[code].__name__
            for code in cls._strategies
        }

    @classmethod
    def get_strategy_class(cls, strategy_type: str) -> Optional[Type[BaseStrategy]]:
        """Get strategy class by type"""
        return cls._strategies.get(strategy_type)

    @classmethod
    def initialize_default_strategies(cls) -> None:
        """Initialize default strategy classes"""
        if cls._initialized:
            return

        # Register technical indicator strategies
        cls.register_strategy(MACrossoverStrategy)
        cls.register_by_code("ma_crossover", MACrossoverStrategy)
        cls.register_strategy(RSIStrategy)
        cls.register_by_code("rsi", RSIStrategy)
        cls.register_strategy(BollingerBandsStrategy)
        cls.register_by_code("bollinger_bands", BollingerBandsStrategy)
        cls.register_strategy(MACDStrategy)
        cls.register_by_code("macd", MACDStrategy)

        # Register momentum strategies
        cls.register_strategy(ADXStrategy)
        cls.register_by_code("adx", ADXStrategy)
        cls.register_strategy(SARStrategy)
        cls.register_by_code("sar", SARStrategy)
        cls.register_strategy(AroonStrategy)
        cls.register_by_code("aroon", AroonStrategy)
        cls.register_strategy(WilliamsRStrategy)
        cls.register_by_code("williams_r", WilliamsRStrategy)

        # Register volume strategies
        cls.register_strategy(OBVStrategy)
        cls.register_by_code("obv", OBVStrategy)
        cls.register_strategy(VWAPStrategy)
        cls.register_by_code("vwap", VWAPStrategy)
        cls.register_strategy(MFIStrategy)
        cls.register_by_code("mfi", MFIStrategy)

        cls._initialized = True
        logger.info(f"Initialized {len(cls._strategies)} default strategies")

    @classmethod
    def create_technical_indicator_strategy(
        cls,
        indicator: str,
        parameters: Dict[str, Any]
    ) -> BaseStrategy:
        """Create technical indicator strategy"""

        # Map indicator names to strategy classes
        strategy_mapping = {
            "ma_crossover": MACrossoverStrategy,
            "rsi": RSIStrategy,
            "bollinger_bands": BollingerBandsStrategy,
            "macd": MACDStrategy
        }

        strategy_class = strategy_mapping.get(indicator.lower())
        if not strategy_class:
            raise ValueError(f"Unknown technical indicator: {indicator}")

        strategy_config = {
            "strategy_type": "technical_indicators",
            "parameters": parameters
        }

        return cls.create_strategy(strategy_config)

    @classmethod
    def create_momentum_strategy(
        cls,
        indicator: str,
        parameters: Dict[str, Any]
    ) -> BaseStrategy:
        """Create momentum strategy"""

        strategy_mapping = {
            "adx": ADXStrategy,
            "sar": SARStrategy,
            "aroon": AroonStrategy,
            "williams_r": WilliamsRStrategy
        }

        strategy_class = strategy_mapping.get(indicator.lower())
        if not strategy_class:
            raise ValueError(f"Unknown momentum indicator: {indicator}")

        strategy_config = {
            "strategy_type": "momentum",
            "parameters": parameters
        }

        return cls.create_strategy(strategy_config)

    @classmethod
    def create_volume_strategy(
        cls,
        indicator: str,
        parameters: Dict[str, Any]
    ) -> BaseStrategy:
        """Create volume strategy"""

        strategy_mapping = {
            "obv": OBVStrategy,
            "vwap": VWAPStrategy,
            "mfi": MFIStrategy
        }

        strategy_class = strategy_mapping.get(indicator.lower())
        if not strategy_class:
            raise ValueError(f"Unknown volume indicator: {indicator}")

        strategy_config = {
            "strategy_type": "volume",
            "parameters": parameters
        }

        return cls.create_strategy(strategy_config)

# Initialize default strategies on import
StrategyFactory.initialize_default_strategies()
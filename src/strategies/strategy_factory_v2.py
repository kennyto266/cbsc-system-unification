"""
Strategy Factory v2.0
Factory for creating and managing strategy instances
Phase 3.1 - 實現策略數據模型
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Type, List, Optional
from uuid import UUID
import logging
from datetime import datetime

from ..models.strategy_models_v2 import Strategy, StrategyType
from ..models.strategy_validators import StrategyValidationError

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """Base abstract strategy class"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize strategy with configuration"""
        self.config = config
        self.parameters = {}
        self.indicators = {}
        self.signals = []

    @abstractmethod
    def calculate_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate technical indicators"""
        pass

    @abstractmethod
    def generate_signals(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate trading signals"""
        pass

    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate strategy parameters"""
        pass

    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """Set strategy parameters"""
        if self.validate_parameters(parameters):
            self.parameters = parameters
        else:
            raise StrategyValidationError("Invalid strategy parameters")

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get parameter validation schema"""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    def get_default_parameters(self) -> Dict[str, Any]:
        """Get default parameters"""
        return {}

    def get_required_timeframes(self) -> List[str]:
        """Get required timeframes for this strategy"""
        return ["1d"]

    def get_required_indicators(self) -> List[str]:
        """Get list of required indicators"""
        return []


class TechnicalStrategy(BaseStrategy):
    """Technical indicator strategy base class"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.indicators_config = config.get('indicators', [])

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate technical strategy parameters"""
        # Validate each indicator's parameters
        for indicator_config in self.indicators_config:
            indicator_type = indicator_config.get('type')
            indicator_params = indicator_config.get('parameters', {})

            # Check if required parameters are provided
            if indicator_type == 'ma':
                if 'period' not in indicator_params:
                    return False
                period = indicator_params['period']
                if not isinstance(period, int) or not 5 <= period <= 500:
                    return False

            elif indicator_type == 'rsi':
                if 'period' not in indicator_params:
                    return False
                period = indicator_params['period']
                if not isinstance(period, int) or not 2 <= period <= 100:
                    return False

            elif indicator_type == 'macd':
                if 'fast' not in indicator_params or 'slow' not in indicator_params:
                    return False
                if indicator_params['fast'] >= indicator_params['slow']:
                    return False

        return True

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get technical strategy parameter schema"""
        properties = {}
        required = []

        for indicator_config in self.indicators_config:
            indicator_type = indicator_config['type']
            indicator_params = indicator_config.get('parameters', {})

            if indicator_type == 'ma':
                properties[f'{indicator_type}_period'] = {
                    'type': 'number',
                    'minimum': 5,
                    'maximum': 500,
                    'default': indicator_params.get('period', 20)
                }
                properties[f'{indicator_type}_type'] = {
                    'type': 'string',
                    'enum': ['sma', 'ema', 'wma'],
                    'default': indicator_params.get('ma_type', 'sma')
                }

            elif indicator_type == 'rsi':
                properties[f'{indicator_type}_period'] = {
                    'type': 'number',
                    'minimum': 2,
                    'maximum': 100,
                    'default': indicator_params.get('period', 14)
                }
                properties[f'{indicator_type}_overbought'] = {
                    'type': 'number',
                    'minimum': 50,
                    'maximum': 100,
                    'default': indicator_params.get('overbought', 70)
                }
                properties[f'{indicator_type}_oversold'] = {
                    'type': 'number',
                    'minimum': 0,
                    'maximum': 50,
                    'default': indicator_params.get('oversold', 30)
                }

            elif indicator_type == 'macd':
                properties[f'{indicator_type}_fast'] = {
                    'type': 'number',
                    'minimum': 1,
                    'maximum': 50,
                    'default': indicator_params.get('fast', 12)
                }
                properties[f'{indicator_type}_slow'] = {
                    'type': 'number',
                    'minimum': 10,
                    'maximum': 200,
                    'default': indicator_params.get('slow', 26)
                }
                properties[f'{indicator_type}_signal'] = {
                    'type': 'number',
                    'minimum': 1,
                    'maximum': 50,
                    'default': indicator_params.get('signal', 9)
                }

        return {
            "type": "object",
            "properties": properties,
            "required": required
        }


class MomentumStrategy(BaseStrategy):
    """Momentum strategy base class"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.lookback_period = config.get('lookback_period', 20)
        self.momentum_threshold = config.get('momentum_threshold', 0.02)

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate momentum strategy parameters"""
        if 'lookback_period' in parameters:
            period = parameters['lookback_period']
            if not isinstance(period, int) or not 1 <= period <= 500:
                return False

        if 'momentum_threshold' in parameters:
            threshold = parameters['momentum_threshold']
            if not isinstance(threshold, (int, float)) or not -1 <= threshold <= 1:
                return False

        return True

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get momentum strategy parameter schema"""
        return {
            "type": "object",
            "properties": {
                "lookback_period": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 500,
                    "default": self.lookback_period,
                    "description": "Lookback period for momentum calculation"
                },
                "momentum_threshold": {
                    "type": "number",
                    "minimum": -1,
                    "maximum": 1,
                    "default": self.momentum_threshold,
                    "description": "Momentum threshold for signal generation"
                }
            },
            "required": []
        }


class VolumeStrategy(BaseStrategy):
    """Volume-based strategy base class"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.volume_ma_period = config.get('volume_ma_period', 20)
        self.volume_multiplier = config.get('volume_multiplier', 1.5)

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate volume strategy parameters"""
        if 'volume_ma_period' in parameters:
            period = parameters['volume_ma_period']
            if not isinstance(period, int) or not 5 <= period <= 200:
                return False

        if 'volume_multiplier' in parameters:
            multiplier = parameters['volume_multiplier']
            if not isinstance(multiplier, (int, float)) or not 0.5 <= multiplier <= 5:
                return False

        return True

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get volume strategy parameter schema"""
        return {
            "type": "object",
            "properties": {
                "volume_ma_period": {
                    "type": "number",
                    "minimum": 5,
                    "maximum": 200,
                    "default": self.volume_ma_period,
                    "description": "Volume moving average period"
                },
                "volume_multiplier": {
                    "type": "number",
                    "minimum": 0.5,
                    "maximum": 5,
                    "default": self.volume_multiplier,
                    "description": "Volume threshold multiplier"
                }
            },
            "required": []
        }


class PortfolioStrategy(BaseStrategy):
    """Portfolio strategy base class"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.assets = config.get('assets', [])
        self.rebalance_frequency = config.get('rebalance_frequency', 'monthly')
        self.optimization_method = config.get('optimization_method', 'equal_weight')

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate portfolio strategy parameters"""
        if 'assets' in parameters:
            assets = parameters['assets']
            if not isinstance(assets, list) or len(assets) == 0:
                return False

            # Check asset weights sum to 1
            total_weight = sum(asset.get('weight', 0) for asset in assets)
            if abs(total_weight - 1.0) > 0.01:
                return False

        if 'rebalance_frequency' in parameters:
            freq = parameters['rebalance_frequency']
            valid_freq = ['daily', 'weekly', 'monthly', 'quarterly']
            if freq not in valid_freq:
                return False

        return True

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get portfolio strategy parameter schema"""
        return {
            "type": "object",
            "properties": {
                "rebalance_frequency": {
                    "type": "string",
                    "enum": ["daily", "weekly", "monthly", "quarterly"],
                    "default": self.rebalance_frequency,
                    "description": "Portfolio rebalancing frequency"
                },
                "optimization_method": {
                    "type": "string",
                    "enum": ["equal_weight", "min_variance", "max_sharpe", "risk_parity"],
                    "default": self.optimization_method,
                    "description": "Portfolio optimization method"
                }
            },
            "required": []
        }


class FundamentalStrategy(BaseStrategy):
    """Fundamental strategy base class"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.economic_indicators = config.get('economic_indicators', [])
        self.data_frequency = config.get('data_frequency', 'monthly')

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate fundamental strategy parameters"""
        if 'economic_indicators' in parameters:
            indicators = parameters['economic_indicators']
            if not isinstance(indicators, list) or len(indicators) == 0:
                return False

        if 'data_frequency' in parameters:
            freq = parameters['data_frequency']
            valid_freq = ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']
            if freq not in valid_freq:
                return False

        return True

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get fundamental strategy parameter schema"""
        return {
            "type": "object",
            "properties": {
                "data_frequency": {
                    "type": "string",
                    "enum": ["daily", "weekly", "monthly", "quarterly", "yearly"],
                    "default": self.data_frequency,
                    "description": "Economic data frequency"
                }
            },
            "required": []
        }


class StrategyFactory:
    """Factory for creating strategy instances"""

    _strategy_registry: Dict[str, Type[BaseStrategy]] = {
        StrategyType.TECHNICAL: TechnicalStrategy,
        StrategyType.MOMENTUM: MomentumStrategy,
        StrategyType.VOLUME: VolumeStrategy,
        StrategyType.PORTFOLIO: PortfolioStrategy,
        StrategyType.FUNDAMENTAL: FundamentalStrategy,
    }

    @classmethod
    def register_strategy(cls, strategy_type: str, strategy_class: Type[BaseStrategy]) -> None:
        """Register a new strategy type"""
        cls._strategy_registry[strategy_type] = strategy_class
        logger.info(f"Registered strategy type: {strategy_type}")

    @classmethod
    def create_strategy(cls, strategy_model: Strategy) -> BaseStrategy:
        """Create strategy instance from model"""
        strategy_type = strategy_model.strategy_type

        if strategy_type not in cls._strategy_registry:
            raise StrategyValidationError(f"Unknown strategy type: {strategy_type}")

        strategy_class = cls._strategy_registry[strategy_type]

        # Create strategy instance
        config = strategy_model.config or {}
        strategy = strategy_class(config)

        # Set default parameters
        if strategy_model.default_parameters:
            strategy.set_parameters(strategy_model.default_parameters)

        logger.info(f"Created strategy instance: {strategy_model.name} ({strategy_type})")
        return strategy

    @classmethod
    def create_strategy_from_config(
        cls,
        strategy_type: str,
        config: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None
    ) -> BaseStrategy:
        """Create strategy instance from type and config"""
        if strategy_type not in cls._strategy_registry:
            raise StrategyValidationError(f"Unknown strategy type: {strategy_type}")

        strategy_class = cls._strategy_registry[strategy_type]
        strategy = strategy_class(config)

        if parameters:
            strategy.set_parameters(parameters)

        logger.info(f"Created strategy from config: {strategy_type}")
        return strategy

    @classmethod
    def get_strategy_types(cls) -> List[str]:
        """Get list of available strategy types"""
        return list(cls._strategy_registry.keys())

    @classmethod
    def get_strategy_class(cls, strategy_type: str) -> Optional[Type[BaseStrategy]]:
        """Get strategy class by type"""
        return cls._strategy_registry.get(strategy_type)

    @classmethod
    def validate_strategy_config(cls, strategy_type: str, config: Dict[str, Any]) -> bool:
        """Validate strategy configuration"""
        try:
            if strategy_type not in cls._strategy_registry:
                return False

            strategy_class = cls._strategy_registry[strategy_type]
            # Create temporary instance to validate config
            strategy = strategy_class(config)
            return True

        except Exception as e:
            logger.error(f"Strategy config validation failed: {e}")
            return False

    @classmethod
    def get_default_config(cls, strategy_type: str) -> Dict[str, Any]:
        """Get default configuration for strategy type"""
        defaults = {
            StrategyType.TECHNICAL: {
                'indicators': [
                    {'type': 'ma', 'parameters': {'period': 20, 'ma_type': 'sma'}},
                    {'type': 'rsi', 'parameters': {'period': 14, 'overbought': 70, 'oversold': 30}}
                ]
            },
            StrategyType.MOMENTUM: {
                'lookback_period': 20,
                'momentum_threshold': 0.02
            },
            StrategyType.VOLUME: {
                'volume_ma_period': 20,
                'volume_multiplier': 1.5
            },
            StrategyType.PORTFOLIO: {
                'assets': [],
                'rebalance_frequency': 'monthly',
                'optimization_method': 'equal_weight'
            },
            StrategyType.FUNDAMENTAL: {
                'economic_indicators': ['GDP', 'CPI', 'UNEMPLOYMENT'],
                'data_frequency': 'monthly'
            }
        }

        return defaults.get(strategy_type, {})


# Pre-built strategy configurations
class StrategyTemplates:
    """Pre-built strategy templates"""

    @staticmethod
    def ma_crossover_strategy() -> Dict[str, Any]:
        """MA Crossover strategy template"""
        return {
            'name': 'MA Crossover',
            'description': 'Simple moving average crossover strategy',
            'strategy_type': StrategyType.TECHNICAL,
            'config': {
                'indicators': [
                    {
                        'type': 'ma',
                        'parameters': {
                            'period': 10,
                            'ma_type': 'sma'
                        }
                    },
                    {
                        'type': 'ma',
                        'parameters': {
                            'period': 30,
                            'ma_type': 'sma'
                        }
                    }
                ]
            },
            'default_parameters': {
                'ma_period_1': 10,
                'ma_type_1': 'sma',
                'ma_period_2': 30,
                'ma_type_2': 'sma'
            },
            'parameter_schema': {
                'type': 'object',
                'properties': {
                    'ma_period_1': {'type': 'number', 'minimum': 5, 'maximum': 100, 'default': 10},
                    'ma_type_1': {'type': 'string', 'enum': ['sma', 'ema'], 'default': 'sma'},
                    'ma_period_2': {'type': 'number', 'minimum': 10, 'maximum': 200, 'default': 30},
                    'ma_type_2': {'type': 'string', 'enum': ['sma', 'ema'], 'default': 'sma'}
                }
            }
        }

    @staticmethod
    def rsi_mean_reversion_strategy() -> Dict[str, Any]:
        """RSI Mean Reversion strategy template"""
        return {
            'name': 'RSI Mean Reversion',
            'description': 'RSI-based mean reversion strategy',
            'strategy_type': StrategyType.TECHNICAL,
            'config': {
                'indicators': [
                    {
                        'type': 'rsi',
                        'parameters': {
                            'period': 14,
                            'overbought': 70,
                            'oversold': 30
                        }
                    }
                ]
            },
            'default_parameters': {
                'rsi_period': 14,
                'rsi_overbought': 70,
                'rsi_oversold': 30
            }
        }

    @staticmethod
    def momentum_breakout_strategy() -> Dict[str, Any]:
        """Momentum Breakout strategy template"""
        return {
            'name': 'Momentum Breakout',
            'description': 'Price momentum breakout strategy',
            'strategy_type': StrategyType.MOMENTUM,
            'config': {
                'lookback_period': 20,
                'momentum_threshold': 0.02
            },
            'default_parameters': {
                'lookback_period': 20,
                'momentum_threshold': 0.02
            }
        }
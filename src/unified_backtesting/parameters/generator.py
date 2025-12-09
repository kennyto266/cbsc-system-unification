"""
Comprehensive Parameter Space Generator for Unified Backtesting

Generates and manages parameter combinations for various trading strategies
with support for the 0-300 range and step 5 configuration as specified in
the unified backtesting requirements.

Key Features:
- 0-300 parameter range with step 5 (60 values per parameter)
- Support for multiple strategy types (RSI, MACD, Bollinger, CBSC sentiment)
- Efficient parameter combination generation with memory optimization
- Parameter validation and constraint management
- Configurable parameter distributions (uniform, logarithmic, custom)
"""

import itertools
import math
from typing import Dict, List, Tuple, Iterator, Optional, Any, Union
from dataclasses import dataclass
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParameterDefinition:
    """Definition of a single parameter with validation constraints"""
    name: str
    values: List[Union[int, float]]
    param_type: str = "numeric"  # numeric, categorical, boolean
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    description: str = ""

    def validate(self, value: Union[int, float]) -> bool:
        """Validate a parameter value against constraints"""
        if self.param_type == "numeric":
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
        return value in self.values


class ComprehensiveParameterSpace:
    """
    Comprehensive parameter space generator for trading strategies

    Generates parameter combinations for 0-300 range with step 5 as specified,
    supporting various CBSC trading strategies with efficient memory management.
    """

    def __init__(self, config=None):
        """Initialize parameter space generator"""
        if config is None:
            from ..core.config import DEFAULT_CONFIG
            config = DEFAULT_CONFIG

        self.config = config
        self.param_range = config.parameter_range
        self._parameter_definitions = self._initialize_parameter_definitions()
        self._total_combinations = None

        logger.info(f"Initialized parameter space with range {list(self.param_range)}")
        logger.info(f"Total parameter values: {len(self.param_range)}")

    def _initialize_parameter_definitions(self) -> Dict[str, ParameterDefinition]:
        """Initialize parameter definitions for all supported strategies"""
        param_values = list(self.param_range)

        return {
            # RSI Strategy Parameters
            'rsi_period': ParameterDefinition(
                name='rsi_period',
                values=param_values,
                param_type='numeric',
                min_value=5,
                max_value=300,
                description='RSI calculation period'
            ),
            'rsi_overbought': ParameterDefinition(
                name='rsi_overbought',
                values=list(range(70, 91, 5)),  # 70-90 step 5
                param_type='numeric',
                min_value=70,
                max_value=90,
                description='RSI overbought threshold'
            ),
            'rsi_oversold': ParameterDefinition(
                name='rsi_oversold',
                values=list(range(10, 31, 5)),  # 10-30 step 5
                param_type='numeric',
                min_value=10,
                max_value=30,
                description='RSI oversold threshold'
            ),

            # MACD Strategy Parameters
            'macd_fast': ParameterDefinition(
                name='macd_fast',
                values=[5, 10, 12, 15, 20, 25, 30, 35, 40, 45, 50],
                param_type='numeric',
                min_value=5,
                max_value=50,
                description='MACD fast EMA period'
            ),
            'macd_slow': ParameterDefinition(
                name='macd_slow',
                values=[20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100],
                param_type='numeric',
                min_value=20,
                max_value=100,
                description='MACD slow EMA period'
            ),
            'macd_signal': ParameterDefinition(
                name='macd_signal',
                values=[5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
                param_type='numeric',
                min_value=5,
                max_value=50,
                description='MACD signal line period'
            ),

            # Bollinger Bands Strategy Parameters
            'bb_period': ParameterDefinition(
                name='bb_period',
                values=param_values,
                param_type='numeric',
                min_value=5,
                max_value=300,
                description='Bollinger Bands period'
            ),
            'bb_std_dev': ParameterDefinition(
                name='bb_std_dev',
                values=[1.5, 2.0, 2.5, 3.0],
                param_type='numeric',
                min_value=1.5,
                max_value=3.0,
                description='Bollinger Bands standard deviation'
            ),

            # CBSC Sentiment Strategy Parameters
            'sentiment_rsi_period': ParameterDefinition(
                name='sentiment_rsi_period',
                values=param_values,
                param_type='numeric',
                min_value=5,
                max_value=300,
                description='Sentiment RSI calculation period'
            ),
            'sentiment_threshold': ParameterDefinition(
                name='sentiment_threshold',
                values=list(range(30, 71, 5)),  # 30-70 step 5
                param_type='numeric',
                min_value=30,
                max_value=70,
                description='Sentiment threshold for signals'
            ),
            'sentiment_lookback': ParameterDefinition(
                name='sentiment_lookback',
                values=[1, 2, 3, 5, 7, 10, 14, 20, 30],
                param_type='numeric',
                min_value=1,
                max_value=30,
                description='Sentiment lookback period'
            ),

            # Common Trading Parameters
            'stop_loss': ParameterDefinition(
                name='stop_loss',
                values=[0.01, 0.02, 0.03, 0.05, 0.07, 0.10],
                param_type='numeric',
                min_value=0.01,
                max_value=0.10,
                description='Stop loss percentage'
            ),
            'take_profit': ParameterDefinition(
                name='take_profit',
                values=[0.02, 0.03, 0.05, 0.07, 0.10, 0.15, 0.20],
                param_type='numeric',
                min_value=0.02,
                max_value=0.20,
                description='Take profit percentage'
            ),
            'position_size': ParameterDefinition(
                name='position_size',
                values=[0.1, 0.2, 0.3, 0.5, 0.7, 1.0],
                param_type='numeric',
                min_value=0.1,
                max_value=1.0,
                description='Position size as fraction of capital'
            )
        }

    def get_strategy_parameters(self, strategy_name: str) -> List[str]:
        """Get parameter names for a specific strategy"""
        strategy_params = {
            'rsi_strategy': ['rsi_period', 'rsi_overbought', 'rsi_oversold', 'stop_loss', 'take_profit'],
            'macd_strategy': ['macd_fast', 'macd_slow', 'macd_signal', 'stop_loss', 'take_profit'],
            'bollinger_strategy': ['bb_period', 'bb_std_dev', 'stop_loss', 'take_profit'],
            'sentiment_strategy': ['sentiment_rsi_period', 'sentiment_threshold', 'sentiment_lookback', 'stop_loss', 'take_profit'],
            'combined_strategy': ['rsi_period', 'rsi_overbought', 'rsi_oversold',
                                 'macd_fast', 'macd_slow', 'macd_signal',
                                 'stop_loss', 'take_profit']
        }
        return strategy_params.get(strategy_name, [])

    def generate_parameter_combinations(self, strategy_name: str,
                                      limit: Optional[int] = None) -> Iterator[Tuple[Dict, int]]:
        """
        Generate parameter combinations for a specific strategy

        Args:
            strategy_name: Name of the strategy
            limit: Optional limit on number of combinations to generate

        Yields:
            Tuple of (parameter_dict, combination_index)
        """
        param_names = self.get_strategy_parameters(strategy_name)
        if not param_names:
            raise ValueError(f"Unknown strategy: {strategy_name}")

        # Generate parameter value lists
        param_value_lists = []
        for param_name in param_names:
            if param_name in self._parameter_definitions:
                param_def = self._parameter_definitions[param_name]
                param_value_lists.append(param_def.values)
            else:
                logger.warning(f"Parameter {param_name} not found in definitions")
                param_value_lists.append([None])  # Default value

        # Calculate total combinations
        total_combinations = 1
        for value_list in param_value_lists:
            total_combinations *= len(value_list)

        if limit:
            total_combinations = min(total_combinations, limit)

        logger.info(f"Generating {total_combinations} parameter combinations for {strategy_name}")

        # Generate combinations using itertools.product for efficiency
        combination_count = 0
        for combination in itertools.product(*param_value_lists):
            if limit and combination_count >= limit:
                break

            param_dict = dict(zip(param_names, combination))
            yield param_dict, combination_count
            combination_count += 1

    def generate_chunked_combinations(self, strategy_name: str,
                                    chunk_size: int = 1000) -> Iterator[List[Tuple[Dict, int]]]:
        """
        Generate parameter combinations in chunks to manage memory

        Args:
            strategy_name: Name of the strategy
            chunk_size: Size of each chunk

        Yields:
            List of parameter combination tuples
        """
        chunk = []
        for param_dict, index in self.generate_parameter_combinations(strategy_name):
            chunk.append((param_dict, index))

            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []

        # Yield remaining combinations
        if chunk:
            yield chunk

    def validate_parameters(self, strategy_name: str, parameters: Dict) -> bool:
        """
        Validate a parameter set against strategy constraints

        Args:
            strategy_name: Name of the strategy
            parameters: Parameter dictionary to validate

        Returns:
            True if parameters are valid, False otherwise
        """
        param_names = self.get_strategy_parameters(strategy_name)

        for param_name, value in parameters.items():
            if param_name not in param_names:
                logger.warning(f"Unexpected parameter {param_name} for strategy {strategy_name}")
                continue

            if param_name in self._parameter_definitions:
                param_def = self._parameter_definitions[param_name]
                if not param_def.validate(value):
                    logger.error(f"Invalid value {value} for parameter {param_name}")
                    return False

        # Strategy-specific validation
        if strategy_name == 'rsi_strategy':
            if parameters.get('rsi_overbought', 0) <= parameters.get('rsi_oversold', 0):
                logger.error("RSI overbought must be greater than oversold")
                return False
        elif strategy_name == 'macd_strategy':
            if parameters.get('macd_fast', 0) >= parameters.get('macd_slow', 0):
                logger.error("MACD fast must be less than slow")
                return False

        return True

    def get_parameter_combinations_count(self, strategy_name: str) -> int:
        """Calculate total number of parameter combinations for a strategy"""
        param_names = self.get_strategy_parameters(strategy_name)
        total = 1

        for param_name in param_names:
            if param_name in self._parameter_definitions:
                param_def = self._parameter_definitions[param_name]
                total *= len(param_def.values)
            else:
                total *= 1  # Default value

        return total

    def get_parameter_info(self) -> Dict[str, Dict]:
        """Get information about all available parameters"""
        return {
            name: {
                'values': param_def.values,
                'type': param_def.param_type,
                'min_value': param_def.min_value,
                'max_value': param_def.max_value,
                'description': param_def.description,
                'count': len(param_def.values)
            }
            for name, param_def in self._parameter_definitions.items()
        }

    def create_custom_parameter_range(self, param_name: str,
                                    custom_values: List[Union[int, float]]) -> None:
        """
        Create a custom parameter range for a specific parameter

        Args:
            param_name: Name of the parameter
            custom_values: Custom values for the parameter
        """
        if param_name in self._parameter_definitions:
            self._parameter_definitions[param_name].values = custom_values
            logger.info(f"Updated {param_name} with {len(custom_values)} custom values")
        else:
            raise ValueError(f"Unknown parameter: {param_name}")

    def export_parameter_space(self, filepath: str, strategy_name: str) -> None:
        """Export parameter space configuration to file"""
        import json

        param_info = self.get_parameter_info()
        strategy_params = self.get_strategy_parameters(strategy_name)

        export_data = {
            'strategy': strategy_name,
            'parameters': strategy_params,
            'parameter_info': {name: param_info[name] for name in strategy_params},
            'total_combinations': self.get_parameter_combinations_count(strategy_name),
            'config': self.config.to_dict()
        }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported parameter space to {filepath}")


# Utility functions for parameter optimization
def create_uniform_distribution(start: int, end: int, step: int = 5) -> List[int]:
    """Create uniform parameter distribution"""
    return list(range(start, end + 1, step))


def create_logarithmic_distribution(start: int, end: int, count: int = 20) -> List[int]:
    """Create logarithmic parameter distribution"""
    return [int(start * (end/start) ** (i/(count-1))) for i in range(count)]


def create_fibonacci_distribution(start: int, end: int) -> List[int]:
    """Create Fibonacci-based parameter distribution"""
    fibs = [1, 1]
    while fibs[-1] + fibs[-2] <= end:
        fibs.append(fibs[-1] + fibs[-2])

    return [f for f in fibs if start <= f <= end]
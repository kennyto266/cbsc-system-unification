"""
Strategy Templates for Code Generation

Provides template-based code generation for various trading strategy types.
Templates ensure generated code follows CBSC patterns and best practices.
"""

from .base import StrategyTemplate
from .momentum import MomentumTemplate
from .mean_reversion import MeanReversionTemplate
from .arbitrage import ArbitrageTemplate
from .pair_trading import PairTradingTemplate
from .ml_strategy import MLStrategyTemplate

__all__ = [
    "StrategyTemplate",
    "MomentumTemplate",
    "MeanReversionTemplate",
    "ArbitrageTemplate",
    "PairTradingTemplate",
    "MLStrategyTemplate",
]

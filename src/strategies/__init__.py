"""
Trading Strategies Module

This module contains various trading strategies for the CBSC backtesting system.
"""

from .ma_crossover import MACrossoverStrategy, EnhancedMACrossoverStrategy
from .rsi_strategy import RSIStrategy, EnhancedRSIStrategy

# Strategy registry for easy access
STRATEGIES = {
    'ma_crossover': MACrossoverStrategy,
    'enhanced_ma_crossover': EnhancedMACrossoverStrategy,
    'rsi': RSIStrategy,
    'enhanced_rsi': EnhancedRSIStrategy,
}

__all__ = [
    'MACrossoverStrategy',
    'EnhancedMACrossoverStrategy',
    'RSIStrategy',
    'EnhancedRSIStrategy',
    'STRATEGIES'
]
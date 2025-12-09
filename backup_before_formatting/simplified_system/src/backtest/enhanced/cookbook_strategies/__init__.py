#!/usr/bin/env python3
"""
Cookbook Strategies Module
Strategies extracted and adapted from Python Algorithmic Trading Cookbook
"""

# Strategy exports
try:
    from .ma_crossover_strategy import ma_crossover_strategy, optimize_ma_crossover
    from .rsi_mean_reversion_strategy import rsi_mean_reversion_strategy, rsi_with_stop_loss_strategy, optimize_rsi_strategy

    __all__ = [
        'ma_crossover_strategy',
        'optimize_ma_crossover',
        'rsi_mean_reversion_strategy',
        'rsi_with_stop_loss_strategy',
        'optimize_rsi_strategy'
    ]

except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import some strategies: {e}")

    __all__ = []
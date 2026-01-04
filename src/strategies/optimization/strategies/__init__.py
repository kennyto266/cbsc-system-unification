"""
Trend following strategies for optimization system.

Includes MA Crossover, Bollinger Bands, and Donchian Channel strategies.
"""

from .trend_following import (
    MAStrategy,
    BollingerBandsStrategy,
    DonchianChannelStrategy,
)

__all__ = [
    'MAStrategy',
    'BollingerBandsStrategy',
    'DonchianChannelStrategy',
]

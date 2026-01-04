"""
Trading strategies for optimization system.

Includes trend following and mean reversion strategies.
"""

from .trend_following import (
    MAStrategy,
    BollingerBandsStrategy,
    DonchianChannelStrategy,
)
from .mean_reversion import (
    RSIMeanReversionStrategy,
    ZScoreStrategy,
    PairsTradingStrategy,
)

__all__ = [
    'MAStrategy',
    'BollingerBandsStrategy',
    'DonchianChannelStrategy',
    'RSIMeanReversionStrategy',
    'ZScoreStrategy',
    'PairsTradingStrategy',
]

"""
Technical Indicators Strategies V2
重構後的技術指標策略模塊

提供統一的技術指標策略基類和實現
"""

from .base import BaseTechnicalIndicatorStrategy
from .ma_crossover import MACrossoverStrategy
from .rsi_strategy import RSIStrategy
from .macd_strategy import MACDStrategy
from .bollinger_bands import BollingerBandsStrategy

# 策略註冊字典
TECHNICAL_STRATEGIES = {
    "ma_crossover": MACrossoverStrategy,
    "rsi": RSIStrategy,
    "macd": MACDStrategy,
    "bollinger_bands": BollingerBandsStrategy
}

__all__ = [
    "BaseTechnicalIndicatorStrategy",
    "MACrossoverStrategy",
    "RSIStrategy",
    "MACDStrategy",
    "BollingerBandsStrategy",
    "TECHNICAL_STRATEGIES"
]
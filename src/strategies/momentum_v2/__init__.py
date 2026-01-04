"""
Momentum Strategies V2
重構後的動量策略模塊

提供統一的動量策略基類和實現
"""

from .base import BaseMomentumStrategy
from .adx_strategy import ADXStrategy
from .sar_strategy import SARStrategy

# 策略註冊字典
MOMENTUM_STRATEGIES = {
    "adx": ADXStrategy,
    "sar": SARStrategy
}

__all__ = [
    "BaseMomentumStrategy",
    "ADXStrategy",
    "SARStrategy",
    "MOMENTUM_STRATEGIES"
]
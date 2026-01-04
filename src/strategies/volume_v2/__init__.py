"""
Volume Strategies V2
重構後的成交量策略模塊

提供統一的成交量策略基類和實現
"""

from .base import BaseVolumeStrategy
from .obv_strategy import OBVStrategy
from .vwap_strategy import VWAPStrategy
from .mfi_strategy import MFIStrategy

# 策略註冊字典
VOLUME_STRATEGIES = {
    "obv": OBVStrategy,
    "vwap": VWAPStrategy,
    "mfi": MFIStrategy
}

__all__ = [
    "BaseVolumeStrategy",
    "OBVStrategy",
    "VWAPStrategy",
    "MFIStrategy",
    "VOLUME_STRATEGIES"
]
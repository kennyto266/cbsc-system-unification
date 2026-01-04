"""
Fundamental Strategies V2
重構後的基本面策略模塊

提供統一的基本面分析策略基類和實現
"""

from .base import BaseFundamentalStrategy
from .hibor_strategy import HIBORStrategy
from .gdp_strategy import GDPGrowthStrategy
from .pmi_strategy import PMIStrategy

# 策略註冊字典
FUNDAMENTAL_STRATEGIES = {
    "hibor": HIBORStrategy,
    "gdp_growth": GDPGrowthStrategy,
    "pmi": PMIStrategy
}

__all__ = [
    "BaseFundamentalStrategy",
    "HIBORStrategy",
    "GDPGrowthStrategy",
    "PMIStrategy",
    "FUNDAMENTAL_STRATEGIES"
]
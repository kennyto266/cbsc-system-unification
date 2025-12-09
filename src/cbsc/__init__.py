"""
CBSC (Callable Bull/Bear Contract) Module
牛熊證量化交易模組

This module provides comprehensive CBSC trading functionality including:
- Advanced sentiment analysis strategies
- Parameter optimization
- Backtesting engine
- Risk management
- Data processing and validation

Author: CBSC Trading System Team
Date: 2025-12-05
Version: 1.0.0
"""

from .core import CBSCProcessor, CBSCConfig
from .strategies import (
    DirectRSIStrategy,
    SentimentMomentumStrategy,
    CompositeIndexStrategy,
    VolatilityAdjustedStrategy
)
from .backtesting.engine import CBSCBacktester
from .optimization.optimizer import CBSCParameterOptimizer
from .data.processor import CBSCDataProcessor
from .risk.management import CBSCRiskManager

__version__ = "1.0.0"
__all__ = [
    # Core
    "CBSCProcessor",
    "CBSCConfig",

    # Strategies
    "DirectRSIStrategy",
    "SentimentMomentumStrategy",
    "CompositeIndexStrategy",
    "VolatilityAdjustedStrategy",

    # Analysis & Testing
    "CBSCBacktester",
    "CBSCParameterOptimizer",

    # Data & Risk
    "CBSCDataProcessor",
    "CBSCRiskManager"
]
"""
智能交易信號模塊
港股量化交易系統的多因子交易信號生成
"""

from .intelligent_signals import IntelligentSignalGenerator
from .signal_combiner import SignalCombiner
from .signal_models import (
    MultiFactorSignal,
    SentimentSignal,
    SignalStrength,
    SignalType,
    TechnicalSignal,
    TradingSignal,
)

__all__ = [
    "IntelligentSignalGenerator",
    "TradingSignal",
    "SignalType",
    "SignalStrength",
    "MultiFactorSignal",
    "SentimentSignal",
    "TechnicalSignal",
    "SignalCombiner",
]

__version__ = "3.0.0"

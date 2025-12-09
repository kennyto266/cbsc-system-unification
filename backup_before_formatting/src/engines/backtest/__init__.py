"""
Backtest Engine Package
回測引擎包

Provides comprehensive backtesting capabilities for trading strategies
with performance metrics and risk analysis.
為交易策略提供全面的回測功能，包括性能指標和風險分析。
"""

from .backtest_engine import BacktestEngine
from .strategy import Strategy, StrategyResult
from .performance import PerformanceAnalyzer

__all__ = [
    "BacktestEngine",
    "Strategy",
    "StrategyResult",
    "PerformanceAnalyzer"
]
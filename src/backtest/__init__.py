"""
回测引擎模块

提供策略回测、绩效计算和验证功能。
"""

from .config import StockBacktestConfig  # pragma: no cover
from .engine_interface import BaseBacktestEngine, BacktestEngineConfig
from .stockbacktest_integration import StockBacktestIntegration
from .strategy_performance import BacktestMetrics, StrategyPerformance

__all__ = [
    "StockBacktestConfig",
    'BaseBacktestEngine',
    'BacktestEngineConfig', 
    'StockBacktestIntegration',
    'StrategyPerformance',
    'BacktestMetrics',
]

"""
回测层 - 简化版
Backtest Layer - Simplified Edition
"""

from .vectorbt_engine import VectorBTEngine, BacktestConfig, BacktestResult, get_backtest_engine, quick_backtest

__all__ = [
    'VectorBTEngine',
    'BacktestConfig',
    'BacktestResult',
    'get_backtest_engine',
    'quick_backtest'
]
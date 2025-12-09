"""
簡化系統 - 回測模塊
Simplified System - Backtesting Module

核心回測功能，支持VectorBT高性能回測
Core backtesting functionality with VectorBT high-performance backtesting
"""

from .vectorbt_engine import VectorBTEngine
from .strategy_builder import StrategyBuilder
from .market_regime import MarketRegimeDetector, RegimeConfig, RegimePrediction
from .dynamic_allocator import DynamicAssetAllocator, AssetConfig, AllocationConfig
from .tactical_overlay import TacticalOverlaySystem, OverlayConfig
from .dynamic_allocation_backtest import DynamicAllocationBacktester, BacktestScenario

__all__ = [
    'VectorBTEngine',
    'StrategyBuilder',
    'MarketRegimeDetector',
    'RegimeConfig',
    'RegimePrediction',
    'DynamicAssetAllocator',
    'AssetConfig',
    'AllocationConfig',
    'TacticalOverlaySystem',
    'OverlayConfig',
    'DynamicAllocationBacktester',
    'BacktestScenario'
]

# 版本信息
__version__ = "1.0.0"
__author__ = "Simplified System"

# 核心策略類型
CORE_STRATEGIES = [
    'RSI_MEAN_REVERSION',    # RSI均值回歸策略
    'MACD_CROSSOVER',        # MACD交叉策略
    'BOLLINGER_BANDS',       # 布林帶策略
    'DUAL_MOVING_AVERAGE',   # 雙移動平均策略
    'MOMENTUM_BREAKOUT',     # 動量突破策略
    'VOLATILITY_BREAKOUT'    # 波動率突破策略
]

# 支持的性能指標
SUPPORTED_METRICS = [
    'total_return',      # 總回報
    'sharpe_ratio',      # 夏普比率
    'max_drawdown',      # 最大回撤
    'win_rate',          # 勝率
    'profit_factor',     # 盈利因子
    'calmar_ratio',      # 卡爾瑪比率
    'sortino_ratio',     # 索提諾比率
    'annual_return'      # 年化回報
]
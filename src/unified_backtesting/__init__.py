"""
Unified Backtesting Framework for CBSC Trading System

This module provides a comprehensive, high-performance backtesting framework that addresses:
1. Memory management for large parameter spaces (120,832+ combinations)
2. Multi-process VectorBT integration for 0-300 parameter ranges
3. Standardized performance metrics (Sharpe Ratio, Max Drawdown)
4. Adaptive resource allocation and fault tolerance

Core Features:
- Unified parameter space generation (0-300 range, step 5)
- Multi-process VectorBT engine with 32 workers
- Standardized metrics calculation across all strategies
- Adaptive memory management for large-scale backtesting
- Real-time progress tracking and result aggregation
"""

__version__ = "1.0.0"
__author__ = "CBSC Quantitative Trading Team"

from .core.framework import UnifiedBacktestingFramework
from .core.config import BacktestingConfig
from .parameters.generator import ComprehensiveParameterSpace
from .vectorbt_engine.engine import EnhancedVectorBTEngine
from .metrics.calculator import StandardizedMetricsCalculator
from .memory.manager import AdaptiveMemoryManager
from .results.aggregator import ResultAggregator

__all__ = [
    'UnifiedBacktestingFramework',
    'BacktestingConfig',
    'ComprehensiveParameterSpace',
    'EnhancedVectorBTEngine',
    'StandardizedMetricsCalculator',
    'AdaptiveMemoryManager',
    'ResultAggregator'
]
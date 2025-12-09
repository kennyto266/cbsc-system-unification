#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtest Engine Module
統一回測引擎模組，整合所有回測相關功能

This module provides unified backtesting capabilities, consolidating functionality
from multiple separate backtest implementations into a cohesive and efficient system.

Core Components:
- UnifiedBacktestEngine: 統一回測引擎
- GPUAcceleratedBacktest: GPU加速回測
- PerformanceAnalyzer: 性能分析器

Author: Architecture Consolidation Team
Date: 2025-11-30
"""

from .unified_engine import UnifiedBacktestEngine
from .gpu_accelerated import GPUAcceleratedBacktest
from .performance_analyzer import PerformanceAnalyzer

__all__ = [
    'UnifiedBacktestEngine',
    'GPUAcceleratedBacktest',
    'PerformanceAnalyzer'
]
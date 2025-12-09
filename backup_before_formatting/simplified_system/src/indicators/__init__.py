"""
簡化系統 - 技術指標模塊
Simplified System - Technical Indicators Module

核心技術指標計算引擎，專注於量化交易所需的最重要指標
Core technical indicator calculation engine focused on essential indicators for quantitative trading
"""

from .core_indicators import CoreIndicators
from .technical_analyzer import TechnicalAnalyzer

__all__ = [
    'CoreIndicators',
    'TechnicalAnalyzer'
]

# 版本信息
__version__ = "1.0.0"
__author__ = "Simplified System"

# 核心指標列表
CORE_INDICATORS = [
    'RSI',        # 相對強弱指數
    'MACD',       # 移動平均收斂背離
    'SMA',        # 簡單移動平均
    'EMA',        # 指數移動平均
    'BOLLINGER',  # 布林帶
    'ATR',        # 平均真實範圍
    'VOLUME_MA',  # 成交量移動平均
    'STOCH',      # 隨機指標
    'WILLIAMS_R'  # 威廉指標
]

# 指標分類
INDICATOR_CATEGORIES = {
    'trend': ['SMA', 'EMA', 'MACD'],
    'momentum': ['RSI', 'STOCH', 'WILLIAMS_R'],
    'volatility': ['BOLLINGER', 'ATR'],
    'volume': ['VOLUME_MA']
}
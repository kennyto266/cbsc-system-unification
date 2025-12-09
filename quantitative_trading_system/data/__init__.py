"""
数据层 - 简化版
Data Layer - Simplified Edition
"""

from .data_manager import DataManager, get_data_manager, get_stock_data, get_multiple_stocks, get_latest_hibor

__all__ = [
    'DataManager',
    'get_data_manager',
    'get_stock_data',
    'get_multiple_stocks',
    'get_latest_hibor'
]
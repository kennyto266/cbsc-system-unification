"""
数据适配器模块

提供统一的数据适配器接口，支持多种数据源的集成和转换。
主要功能：
- 数据源抽象和标准化
- 数据格式转换和验证
- 数据质量检查和错误处理
- 多数据源管理和切换
"""

from .base_adapter import BaseDataAdapter, DataAdapterConfig
from .raw_data_adapter import RawDataAdapter

__all__ = [
    'BaseDataAdapter',
    'DataAdapterConfig', 
    'RawDataAdapter'
]

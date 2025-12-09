#!/usr/bin/env python3
"""
Simplified System - Configuration Management
简化系统 - 配置管理

统一的配置管理系统，支持环境分离、类型验证和动态配置更新。
"""

from .config_manager import (
    get_config_manager,
    get_config,
    get_data_source_config,
    get_performance_config,
    get_api_config,
    reload_config
)

__all__ = [
    'get_config_manager',
    'get_config',
    'get_data_source_config',
    'get_performance_config',
    'get_api_config',
    'reload_config'
]
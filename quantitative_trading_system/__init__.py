#!/usr/bin/env python3
"""
量化交易系统 - 简化版
Quantitative Trading System - Simplified Edition

基于YAGNI和KISS原则的专业级量化交易平台
专注于核心功能：数据获取、技术指标、回测、优化

Author: Claude Code Assistant
Created: 2025-11-29
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Claude Code Assistant"
__description__ = "基于真实数据的专业量化交易系统 - 简化版"

# 导入核心模块
from .data.data_manager import DataManager, get_data_manager
from .indicators.core_indicators import CoreIndicators, get_core_indicators
from .backtest.vectorbt_engine import VectorBTEngine, BacktestResult, get_backtest_engine
from .optimization.optimizer import ParameterOptimizer, get_optimizer
from .utils.config import ConfigManager, get_config_manager
from .web.simple_dashboard import SimpleDashboard, create_dashboard

# 公开API
__all__ = [
    # 版本信息
    '__version__',
    '__author__',
    '__description__',

    # 核心类
    'DataManager',
    'CoreIndicators',
    'VectorBTEngine',
    'ParameterOptimizer',
    'ConfigManager',
    'SimpleDashboard',

    # 结果类
    'BacktestResult',

    # 便捷函数
    'get_data_manager',
    'get_core_indicators',
    'get_backtest_engine',
    'get_optimizer',
    'get_config_manager',
    'create_dashboard'
]

# 系统信息
SYSTEM_INFO = {
    'name': '量化交易系统 - 简化版',
    'version': __version__,
    'core_files': 12,
    'architecture': 'MVP (Minimum Viable Product)',
    'design_principles': ['YAGNI', 'KISS', 'Practical First'],
    'data_sources': {
        'stock': '中央API (真实港股数据)',
        'government': '香港政府API (官方经济数据)'
    },
    'core_capabilities': [
        '实时股票数据获取',
        '20个核心技术指标',
        'VectorBT专业回测',
        '智能参数优化',
        '简洁Web界面'
    ],
    'performance_targets': {
        'startup_time': '<10秒',
        'backtest_speed': '>2000策略/秒',
        'memory_usage': '减少80%',
        'file_count': '10-15个核心文件'
    }
}

def get_system_info():
    """获取系统信息"""
    return SYSTEM_INFO.copy()

def print_system_info():
    """打印系统信息"""
    info = get_system_info()
    print(f"\n🚀 {info['name']} v{info['version']}")
    print("=" * 60)
    print(f"📁 核心文件数: {info['core_files']}")
    print(f"🏗️ 架构: {info['architecture']}")
    print(f"📋 设计原则: {', '.join(info['design_principles'])}")
    print(f"\n📊 核心能力:")
    for capability in info['core_capabilities']:
        print(f"  ✅ {capability}")
    print(f"\n🎯 性能目标:")
    for metric, target in info['performance_targets'].items():
        print(f"  📈 {metric}: {target}")
    print("=" * 60)
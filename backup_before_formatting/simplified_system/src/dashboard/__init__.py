"""
量化交易仪表板模块
Quantitative Trading Dashboard Module

提供专业的实时量化交易仪表板功能：
- 交互式图表和可视化
- 实时数据更新
- 投资组合监控
- 性能分析
- 风险指标展示
"""

from .dashboard_app import QuantDashboard, create_dashboard, run_dashboard
from .performance_charts import PerformanceCharts
from .real_time_updater import RealTimeUpdater, create_real_time_updater, get_global_updater

__all__ = [
    # 主仪表板
    'QuantDashboard',
    'create_dashboard',
    'run_dashboard',

    # 图表组件
    'PerformanceCharts',

    # 实时更新
    'RealTimeUpdater',
    'create_real_time_updater',
    'get_global_updater'
]

__version__ = '1.0.0'
__author__ = 'Quantitative Trading System'
__description__ = 'Professional quantitative trading dashboard with real-time updates'
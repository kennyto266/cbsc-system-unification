"""
港股量化交易 AI Agent 系统 - 高级分析模块

Phase 5: Advanced Analytics and Visualization System
=====================================================

This module provides comprehensive analytics, visualization, and benchmark comparison
capabilities for the 0700.HK quantitative trading platform.

Core Components:
- PerformanceVisualizer: Interactive visualization with 3D plots and heatmaps
- BenchmarkAnalyzer: HSI and sector index comparison analysis
- InteractiveDashboard: Real-time multi-strategy analysis dashboard
- AdvancedStatistics: Monte Carlo and bootstrap statistical analysis
- ReportGenerator: Automated comprehensive report generation
- MLAnalytics: Machine learning pattern recognition and prediction

Features:
- Interactive parameter heatmaps and 3D surface plots
- Multi-dimensional parameter space exploration
- Real-time performance dashboards
- Risk-return scatter plots and efficient frontier analysis
- HSI and sector-specific benchmark comparisons
- Monte Carlo simulation for strategy validation
- Bootstrap confidence intervals
- Pattern recognition in parameter performance
- Automated report generation in multiple formats

Integration:
- Seamless integration with existing Phase 1-4 systems
- Compatible with current API and monitoring infrastructure
- Real-time data streaming and WebSocket support
- GPU-accelerated computation for large-scale analysis

Author: Claude Code Assistant
Date: 2025-11-29
Version: 5.0.0
"""

from .performance_visualizer import PerformanceVisualizer, VisualizerConfig
from .benchmark_analyzer import BenchmarkAnalyzer, BenchmarkConfig
from .interactive_dashboard import InteractiveDashboard, DashboardConfig
from .advanced_statistics import AdvancedStatistics, StatisticsConfig
from .report_generator import ReportGenerator, ReportConfig
from .ml_analytics import MLAnalytics, MLConfig

__version__ = "5.0.0"
__author__ = "Claude Code Assistant"

__all__ = [
    # Core visualization
    "PerformanceVisualizer",
    "VisualizerConfig",

    # Benchmark analysis
    "BenchmarkAnalyzer",
    "BenchmarkConfig",

    # Interactive dashboard
    "InteractiveDashboard",
    "DashboardConfig",

    # Advanced statistics
    "AdvancedStatistics",
    "StatisticsConfig",

    # Report generation
    "ReportGenerator",
    "ReportConfig",

    # Machine learning analytics
    "MLAnalytics",
    "MLConfig",

    # Module info
    "__version__",
    "__author__",
]

# Analytics module configuration
ANALYTICS_CONFIG = {
    "version": "5.0.0",
    "phase": "Phase 5",
    "description": "Advanced Analytics and Visualization System",
    "features": [
        "Interactive parameter visualization",
        "3D surface plots and heatmaps",
        "Real-time performance dashboards",
        "Benchmark comparison analysis",
        "Monte Carlo simulation",
        "Bootstrap confidence intervals",
        "ML pattern recognition",
        "Automated report generation"
    ],
    "integrations": [
        "Phase 1-4 systems",
        "GPU acceleration",
        "WebSocket streaming",
        "REST API",
        "Monitoring systems"
    ],
    "supported_assets": ["0700.HK", "HSI constituents", "Sector ETFs"],
    "performance_metrics": [
        "Sharpe ratio", "Sortino ratio", "Calmar ratio",
        "Maximum drawdown", "Volatility", "Beta/Alpha",
        "Information ratio", "Tracking error"
    ]
}

def get_analytics_info():
    """Get analytics module information"""
    return ANALYTICS_CONFIG

def get_version():
    """Get analytics module version"""
    return __version__
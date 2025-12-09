"""
港股量化交易 AI Agent 系统 - 研究分析师模块

包含学术文献研究、策略假设测试和回测验证功能。
"""

from .backtest_validation import (
    BacktestConfig,
    BacktestResult,
    BacktestValidator,
    BiasDetector,
    BiasType,
    ValidationMetrics,
)

__all__ = [
    "BacktestValidator",
    "BacktestConfig",
    "BacktestResult",
    "ValidationMetrics",
    "BiasDetector",
    "BiasType",
]

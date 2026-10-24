"""
CBSC Strategy SDK - Backtest Module.

This module provides a notebook-friendly interface for running backtests
against the CBSC backtesting API, with support for:

- Simple run() interface for backtesting
- Real-time progress tracking
- Result parsing and visualization
- Parameter optimization (grid search and Bayesian)
- Async support for non-blocking execution

Example:
    >>> from cbsc_strategy_sdk import BacktestAdapter
    >>> from datetime import date
    >>>
    >>> async with BacktestAdapter() as adapter:
    ...     result = await adapter.run_backtest(
    ...         strategy_code="my_strategy",
    ...         symbols=["AAPL"],
    ...         start_date=date(2024, 1, 1),
    ...         end_date=date(2024, 12, 31),
    ...         parameters={"rsi_period": 14}
    ...     )
    ...     result.plot_equity_curve()
"""

__version__ = "0.1.0"

from .adapter import BacktestAdapter
from .result import BacktestResult
from .progress import BacktestProgress
from .optimizer import ParameterOptimizer, OptimizationResult
from .models import (
    BacktestRequest,
    BacktestStatus,
    BacktestJob,
    BacktestMetrics,
    BacktestTrade,
)

__all__ = [
    # Version
    "__version__",
    # Core classes
    "BacktestAdapter",
    "BacktestResult",
    "BacktestProgress",
    "ParameterOptimizer",
    "OptimizationResult",
    # Models
    "BacktestRequest",
    "BacktestStatus",
    "BacktestJob",
    "BacktestMetrics",
    "BacktestTrade",
]

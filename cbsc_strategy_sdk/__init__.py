"""
CBSC Strategy SDK - Python SDK for Strategy Development.

This SDK provides a unified interface for developing, testing, and analyzing
trading strategies using the CBSC (Computer-Based Strategy Configuration) platform.

Main Features:
    - Historical market data retrieval
    - Real-time data streaming
    - Strategy backtesting
    - Performance analysis
    - Jupyter notebook integration

Example:
    >>> from cbsc_strategy_sdk import StrategyWorkspace, BacktestAdapter
    >>> from datetime import date
    >>>
    >>> # Create workspace with default configuration
    >>> workspace = StrategyWorkspace()
    >>>
    >>> # Fetch historical data
    >>> async with workspace as ws:
    ...     data = ws.get_historical_data("AAPL", date(2024, 1, 1), date(2024, 12, 31))
    ...     print(data.head())
    >>>
    >>> # Run backtest
    >>> async with BacktestAdapter() as adapter:
    ...     result = await adapter.run_backtest(
    ...         strategy_code="my_strategy",
    ...         symbols=["AAPL"],
    ...         start_date=date(2024, 1, 1),
    ...         end_date=date(2024, 12, 31),
    ...         parameters={"rsi_period": 14}
    ...     )
    ...     result.plot_equity_curve()

Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "CBSC Development Team"
__all__ = [
    # Version
    "__version__",
    # Exceptions
    "StrategyWorkspaceError",
    "DataFetchError",
    "APIConnectionError",
    "ConfigurationError",
    # Configuration
    "WorkspaceConfig",
    "create_config",
    # Main Workspace
    "StrategyWorkspace",
    # Backtest Module
    "BacktestAdapter",
    "BacktestResult",
    "BacktestProgress",
    "ParameterOptimizer",
    "OptimizationResult",
    # Controls Module
    "StrategyControlPanel",
    "ControlWidgets",
    "SymbolSelector",
    "DateRangePicker",
    "ParameterValidator",
    "ValidationResult",
    "AutoRefreshManager",
    "PresetManager",
    "TabbedControls",
    # Dashboard Module
    "StrategyDashboard",
    "create_dashboard",
    "DashboardLayout",
    "ChartBuilders",
    "MetricsDisplay",
    "LiveUpdateComponent",
    "ThemeManager",
]

# Import exceptions for public API
from .exceptions import (
    APIConnectionError,
    ConfigurationError,
    DataFetchError,
    StrategyWorkspaceError,
)

# Import configuration classes
from .config import WorkspaceConfig, create_config

# Import main workspace class
from .workspace import StrategyWorkspace

# Import backtest module classes
from .backtest import (
    BacktestAdapter,
    BacktestProgress,
    BacktestResult,
    OptimizationResult,
    ParameterOptimizer,
)

# Import controls module classes (with error handling for missing dependencies)
try:
    from .controls import (
        StrategyControlPanel,
        ControlWidgets,
        SymbolSelector,
        DateRangePicker,
        ParameterValidator,
        ValidationResult,
        AutoRefreshManager,
        PresetManager,
        TabbedControls,
    )
    _controls_available = True
except ImportError:
    _controls_available = False
    # Create dummy classes for type hints
    StrategyControlPanel = None  # type: ignore
    ControlWidgets = None  # type: ignore
    SymbolSelector = None  # type: ignore
    DateRangePicker = None  # type: ignore
    ParameterValidator = None  # type: ignore
    ValidationResult = None  # type: ignore
    AutoRefreshManager = None  # type: ignore
    PresetManager = None  # type: ignore
    TabbedControls = None  # type: ignore

# Import dashboard module classes
try:
    from .dashboard import (
        StrategyDashboard,
        create_dashboard,
        DashboardLayout,
        ChartBuilders,
        MetricsDisplay,
        LiveUpdateComponent,
        ThemeManager,
    )
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False

__all__.extend([
    "StrategyWorkspace",
    "BacktestAdapter",
    "BacktestResult",
    "BacktestProgress",
    "ParameterOptimizer",
    "OptimizationResult",
])

if _controls_available:
    __all__.extend([
        "StrategyControlPanel",
        "ControlWidgets",
        "SymbolSelector",
        "DateRangePicker",
        "ParameterValidator",
        "ValidationResult",
        "AutoRefreshManager",
        "PresetManager",
        "TabbedControls",
    ])

if DASHBOARD_AVAILABLE:
    __all__.extend([
        "StrategyDashboard",
        "create_dashboard",
        "DashboardLayout",
        "ChartBuilders",
        "MetricsDisplay",
        "LiveUpdateComponent",
        "ThemeManager",
    ])


def get_version() -> str:
    """Get the current SDK version.

    Returns:
        Version string (e.g., "0.1.0")
    """
    return __version__


def check_version(required_version: str) -> bool:
    """Check if the current SDK version meets requirements.

    Args:
        required_version: Minimum required version (e.g., "0.1.0")

    Returns:
        True if current version >= required_version

    Example:
        >>> if not check_version("0.2.0"):
        ...     print("Please upgrade SDK to version 0.2.0 or higher")
    """
    from packaging import version as pkg_version

    current = pkg_version.parse(__version__)
    required = pkg_version.parse(required_version)
    return current >= required

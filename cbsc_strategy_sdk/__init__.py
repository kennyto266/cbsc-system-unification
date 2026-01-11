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
    >>> from cbsc_strategy_sdk import StrategyWorkspace, WorkspaceConfig
    >>>
    >>> # Create workspace with default configuration
    >>> workspace = StrategyWorkspace()
    >>>
    >>> # Or with custom configuration
    >>> config = WorkspaceConfig(api_base="https://api.example.com")
    >>> workspace = StrategyWorkspace(config=config)
    >>>
    >>> # Use as context manager for automatic cleanup
    >>> with StrategyWorkspace() as ws:
    ...     data = ws.get_historical_data("AAPL", start_date, end_date)
    ...     print(data.head())

Version: 0.1.0
"""

__version__ = "0.1.0"
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

# Note: StrategyWorkspace will be imported in Stream B
# This avoids circular imports and keeps streams independent
# from .workspace import StrategyWorkspace  # Added in Stream B

__all__.extend([
    # "StrategyWorkspace",  # Will be added in Stream B
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

"""
Dash Dashboard module for CBSC Strategy SDK.

Provides interactive dashboard components for real-time strategy monitoring,
performance analysis, and live market data visualization in Jupyter notebooks.

Main classes:
    - StrategyDashboard: Main dashboard application
    - DashboardLayout: Layout component builder
    - ChartBuilders: Plotly chart builder for Dash
    - MetricsDisplay: Performance metrics visualization
    - LiveUpdateComponent: Real-time data streaming
    - ThemeManager: Dark/light theme management

Example:
    >>> from cbsc_strategy_sdk.dashboard import StrategyDashboard, create_dashboard
    >>>
    >>> # Create dashboard
    >>> dashboard = create_dashboard(title="My Strategy Dashboard")
    >>>
    >>> # Load data
    >>> dashboard.load_backtest_results(returns)
    >>>
    >>> # Run in Jupyter
    >>> dashboard.run(mode='inline')
"""

from .app import StrategyDashboard, create_dashboard
from .layout import DashboardLayout
from .charts import ChartBuilders
from .metrics import MetricsDisplay
from .live import LiveUpdateComponent, CircularBuffer
from .theme import ThemeManager

__all__ = [
    # Main Dashboard
    'StrategyDashboard',
    'create_dashboard',

    # Layout
    'DashboardLayout',

    # Charts
    'ChartBuilders',

    # Metrics
    'MetricsDisplay',

    # Live Updates
    'LiveUpdateComponent',
    'CircularBuffer',

    # Theme
    'ThemeManager',
]

# Version info
__version__ = '1.0.0'
__author__ = 'CBSC Strategy Team'


def get_version() -> str:
    """Get the dashboard module version.

    Returns:
        Version string (e.g., "1.0.0")
    """
    return __version__


def check_dependencies() -> dict:
    """Check if required dependencies are installed.

    Returns:
        Dictionary with dependency status
    """
    dependencies = {
        'dash': False,
        'dash_bootstrap_components': False,
        'plotly': False,
        'websockets': False,
        'pandas': False,
    }

    try:
        import dash  # noqa: F401
        dependencies['dash'] = True
    except ImportError:
        pass

    try:
        import dash_bootstrap_components  # noqa: F401
        dependencies['dash_bootstrap_components'] = True
    except ImportError:
        pass

    try:
        import plotly  # noqa: F401
        dependencies['plotly'] = True
    except ImportError:
        pass

    try:
        import websockets  # noqa: F401
        dependencies['websockets'] = True
    except ImportError:
        pass

    try:
        import pandas  # noqa: F401
        dependencies['pandas'] = True
    except ImportError:
        pass

    return dependencies


def print_dependency_status() -> None:
    """Print status of required dependencies."""
    status = check_dependencies()

    print("CBSC Strategy SDK - Dashboard Module Dependencies:")
    print("=" * 50)

    all_installed = True
    for name, installed in status.items():
        symbol = "✓" if installed else "✗"
        print(f"  {symbol} {name}: {'Installed' if installed else 'Missing'}")
        if not installed:
            all_installed = False

    print("=" * 50)

    if all_installed:
        print("All dependencies are installed!")
    else:
        print("\nMissing dependencies. Install with:")
        print("  pip install dash dash-bootstrap-components plotly websockets pandas")

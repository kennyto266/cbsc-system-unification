"""
Visualization module for CBSC Strategy SDK.

Provides interactive charting, performance analysis, and
widget controls for Jupyter notebooks.

Main classes:
    - ChartBuilder: Create interactive Plotly charts
    - PerformanceCharts: Strategy performance visualizations
    - ControlPanel: Interactive controls with ipywidgets
    - LayoutManager: Multi-panel layout organization

Example:
    >>> from cbsc_strategy_sdk.visualization import ChartBuilder
    >>> builder = ChartBuilder(theme="dark")
    >>> fig = builder.create_candlestick(data)
    >>> fig.show()
"""

from .charts import ChartBuilder, create_sample_data
from .performance import PerformanceCharts
from .widgets import ControlPanel, create_strategy_controls
from .layouts import LayoutManager, create_chart_layout
from .themes import Theme, get_theme, list_themes

__all__ = [
    # Charts
    'ChartBuilder',
    'create_sample_data',

    # Performance
    'PerformanceCharts',

    # Widgets
    'ControlPanel',
    'create_strategy_controls',

    # Layouts
    'LayoutManager',
    'create_chart_layout',

    # Themes
    'Theme',
    'get_theme',
    'list_themes',
]

# Version info
__version__ = '1.0.0'
__author__ = 'CBSC Strategy Team'

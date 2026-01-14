"""
Interactive Controls Module for CBSC Strategy SDK

This module provides comprehensive ipywidgets-based controls for interactive
strategy parameter management in Jupyter notebooks.

Components:
- StrategyControlPanel: Main control panel for managing parameters
- ControlWidgets: Collection of specialized widget types
- SymbolSelector: Symbol selection with search functionality
- DateRangePicker: Date range selection with presets
- ParameterValidator: Parameter validation system
- AutoRefreshManager: Auto-refresh on parameter changes
- PresetManager: Save/load parameter presets
- TabbedControls: Tabbed interface organization
"""

from .panel import StrategyControlPanel
from .widgets import ControlWidgets
from .symbol_selector import SymbolSelector
from .date_picker import DateRangePicker
from .validator import ParameterValidator, ValidationResult
from .refresh import AutoRefreshManager
from .presets import PresetManager
from .tabs import TabbedControls

__all__ = [
    "StrategyControlPanel",
    "ControlWidgets",
    "SymbolSelector",
    "DateRangePicker",
    "ParameterValidator",
    "ValidationResult",
    "AutoRefreshManager",
    "PresetManager",
    "TabbedControls",
]

__version__ = "1.0.0"

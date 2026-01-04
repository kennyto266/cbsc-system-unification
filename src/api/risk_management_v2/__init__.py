"""
Risk Management API v2
======================

Advanced risk analysis and management for quantitative trading strategies.

Author: CBSC Risk Management Team
Version: 2.0.0
"""

__version__ = "2.0.0"
__title__ = "CBSC Risk Management API"
__description__ = "Advanced risk analysis and management for quantitative trading strategies"

# Export main components
from .main import app
from .models import *
from .routes import router
from .config import settings

__all__ = [
    "app",
    "router",
    "settings",
    "__version__",
    "__title__",
    "__description__"
]
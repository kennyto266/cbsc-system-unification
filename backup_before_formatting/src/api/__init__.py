"""
API Package for Hong Kong Quantitative Trading System
香港量化交易系統 API 包
"""

from .app import create_app
from .models import *

__version__ = "2.1.0"
__all__ = ["create_app"]

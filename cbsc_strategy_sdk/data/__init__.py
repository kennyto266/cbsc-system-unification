"""Data layer for CBSC Strategy SDK.

Provides data connector, cache, models, and real-time streaming for market data access.
"""

from .cache import DataCache
from .connector import CBSCDataConnector
from .models import OHLCVBar, SymbolInfo, TickData
from .events import EventEmitter
from .buffer import CircularBuffer, TickCircularBuffer

try:
    from .realtime_stream import RealTimeDataStream, ConnectionManager
    _realtime_available = True
except ImportError:
    _realtime_available = False

__all__ = [
    "DataCache",
    "CBSCDataConnector",
    "OHLCVBar",
    "SymbolInfo",
    "TickData",
    "EventEmitter",
    "CircularBuffer",
    "TickCircularBuffer",
]

# Add real-time streaming classes if available
if _realtime_available:
    __all__.extend([
        "RealTimeDataStream",
        "ConnectionManager",
    ])

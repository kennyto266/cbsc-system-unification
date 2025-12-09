"""
交易模組 - 真實交易API集成

支持多個券商和交易所的真實交易功能
"""

from .base_trading_api import BaseTradingAPI, OrderSide, OrderStatus, OrderType
from .broker_apis import ETRADEAPI, FidelityAPI, InteractiveBrokersAPI, TDAmeritradeAPI
from .crypto_apis import BinanceAPI, CoinbaseAPI, KrakenAPI
from .order_manager import OrderManager
from .position_manager import PositionManager
from .trading_manager import TradingManager

__all__ = [
    "BaseTradingAPI",
    "OrderType",
    "OrderStatus",
    "OrderSide",
    "InteractiveBrokersAPI",
    "TDAmeritradeAPI",
    "ETRADEAPI",
    "FidelityAPI",
    "BinanceAPI",
    "CoinbaseAPI",
    "KrakenAPI",
    "TradingManager",
    "OrderManager",
    "PositionManager",
]

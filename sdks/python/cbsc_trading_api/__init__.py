"""
CBSC Trading API Python SDK

A comprehensive Python SDK for interacting with the CBSC Trading Platform API.
"""

from .client import CBSCClient, AsyncCBSCClient
from .exceptions import (
    CBSCAPIError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    ServerError,
)
from .models import (
    TokenResponse,
    User,
    UserCreate,
    Strategy,
    StrategyCreate,
    Portfolio,
    Position,
    Order,
    Symbol,
    Backtest,
    Webhook,
    APIResponse,
)
from .version import __version__

__all__ = [
    # Clients
    "CBSCClient",
    "AsyncCBSCClient",
    # Exceptions
    "CBSCAPIError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
    # Models
    "TokenResponse",
    "User",
    "UserCreate",
    "Strategy",
    "StrategyCreate",
    "Portfolio",
    "Position",
    "Order",
    "Symbol",
    "Backtest",
    "Webhook",
    "APIResponse",
    # Version
    "__version__",
]

# 设置默认配置
import logging

# 创建 SDK logger
logger = logging.getLogger("cbsc_trading_api")
logger.addHandler(logging.NullHandler())
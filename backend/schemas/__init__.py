"""
Request and response schemas for API endpoints.
"""

from .common import (
    PaginationParams,
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse
)
from .auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    UserCreate,
    UserUpdate
)
from .strategy import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategyListResponse
)
from .backtest import (
    BacktestCreate,
    BacktestResponse,
    BacktestListResponse
)

__all__ = [
    # Common
    "PaginationParams",
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
    # Auth
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "UserResponse",
    "UserCreate",
    "UserUpdate",
    # Strategy
    "StrategyCreate",
    "StrategyUpdate",
    "StrategyResponse",
    "StrategyListResponse",
    # Backtest
    "BacktestCreate",
    "BacktestResponse",
    "BacktestListResponse",
]

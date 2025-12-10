"""
工具模块
Utilities Module
"""

from .permissions import (
    PermissionManager,
    get_current_user,
    require_strategy_permission,
    authenticate_websocket,
    create_access_token
)
from .cache import (
    CacheManager,
    cache_manager,
    CacheKeys,
    cache_result,
    invalidate_cache
)
from .validators import (
    BaseValidator,
    StrategyValidator,
    ExecutionValidator,
    PersonalDataValidator,
    ValidationError,
    ValidatorFactory
)
from .errors import (
    ErrorCode,
    BusinessError,
    StrategyError,
    ExecutionError,
    ValidationError as UtilValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ErrorHandler,
    ExceptionHandlerMiddleware,
    ErrorLogger,
    ErrorReporter,
    error_reporter
)

__all__ = [
    # Permissions
    "PermissionManager",
    "get_current_user",
    "require_strategy_permission",
    "authenticate_websocket",
    "create_access_token",

    # Cache
    "CacheManager",
    "cache_manager",
    "CacheKeys",
    "cache_result",
    "invalidate_cache",

    # Validators
    "BaseValidator",
    "StrategyValidator",
    "ExecutionValidator",
    "PersonalDataValidator",
    "ValidationError",
    "ValidatorFactory",

    # Errors
    "ErrorCode",
    "BusinessError",
    "StrategyError",
    "ExecutionError",
    "ValidationError as UtilValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ErrorHandler",
    "ExceptionHandlerMiddleware",
    "ErrorLogger",
    "ErrorReporter",
    "error_reporter"
]
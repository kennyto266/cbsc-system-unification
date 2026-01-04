"""
Unified Exception Classes

Custom exception hierarchy for CBSC system.
"""

from typing import Any, Optional, Dict
from .responses import ErrorCode


class CBSCError(Exception):
    """Base exception for all CBSC system errors"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(CBSCError):
    """Validation error"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            details=error_details
        )


class NotFoundError(CBSCError):
    """Resource not found error"""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(
            message=message,
            code=ErrorCode.NOT_FOUND,
            details=details
        )


class UnauthorizedError(CBSCError):
    """Unauthorized access error"""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            code=ErrorCode.UNAUTHORIZED
        )


class ForbiddenError(CBSCError):
    """Forbidden access error"""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            code=ErrorCode.FORBIDDEN
        )


class ConflictError(CBSCError):
    """Resource conflict error"""

    def __init__(
        self,
        message: str,
        conflicting_field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if conflicting_field:
            error_details["conflicting_field"] = conflicting_field
        super().__init__(
            message=message,
            code=ErrorCode.CONFLICT,
            details=error_details
        )


class ServiceUnavailableError(CBSCError):
    """Service unavailable error"""

    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(
            message=message,
            code=ErrorCode.SERVICE_UNAVAILABLE
        )


class RateLimitError(CBSCError):
    """Rate limit exceeded error"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        limit: Optional[int] = None
    ):
        details = {}
        if retry_after is not None:
            details["retry_after"] = retry_after
        if limit is not None:
            details["limit"] = limit
        super().__init__(
            message=message,
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            details=details
        )


class StrategyError(CBSCError):
    """Strategy-related errors"""

    def __init__(self, message: str, strategy_id: Optional[str] = None):
        details = {"strategy_id": strategy_id} if strategy_id else {}
        super().__init__(
            message=message,
            code="STRATEGY_ERROR",
            details=details
        )


class BacktestError(CBSCError):
    """Backtest-related errors"""

    def __init__(self, message: str, backtest_id: Optional[str] = None):
        details = {"backtest_id": backtest_id} if backtest_id else {}
        super().__init__(
            message=message,
            code="BACKTEST_ERROR",
            details=details
        )


class CacheError(CBSCError):
    """Cache-related errors"""

    def __init__(self, message: str, cache_key: Optional[str] = None):
        details = {"cache_key": cache_key} if cache_key else {}
        super().__init__(
            message=message,
            code="CACHE_ERROR",
            details=details
        )


class DatabaseError(CBSCError):
    """Database-related errors"""

    def __init__(self, message: str, query: Optional[str] = None):
        details = {"query": query} if query else {}
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            details=details
        )

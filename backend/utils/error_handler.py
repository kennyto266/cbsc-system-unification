"""
Centralized error handling utilities for the CBSC Trading System.

Provides error classification, user-friendly messages, and recovery options.
"""

import logging
import traceback
import uuid
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime


# Configure logger
logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of errors for proper handling and messaging."""
    NETWORK = "network"
    API_RATE_LIMIT = "api_rate_limit"
    DATABASE = "database"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    EXTERNAL_SERVICE = "external_service"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"          # User can retry, no data loss
    MEDIUM = "medium"    # Action required, potential partial data loss
    HIGH = "high"        # System impact, requires intervention
    CRITICAL = "critical"  # System failure, immediate attention needed


class CBAError(Exception):
    """Base exception class for CBSC Trading System errors."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: Optional[str] = None,
        recovery_actions: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.category = category
        self.severity = severity
        self.user_message = user_message or self._default_user_message()
        self.recovery_actions = recovery_actions or self._default_recovery_actions()
        self.context = context or {}
        self.error_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)

    def _default_user_message(self) -> str:
        """Generate default user-friendly message based on category."""
        messages = {
            ErrorCategory.NETWORK: "網絡連接出現問題，請檢查您的網絡連接",
            ErrorCategory.API_RATE_LIMIT: "API 請求頻率過高，請稍後再試",
            ErrorCategory.DATABASE: "數據庫連接問題，正在嘗試重新連接",
            ErrorCategory.VALIDATION: "輸入數據格式不正確，請檢查後重試",
            ErrorCategory.AUTHENTICATION: "身份驗證失敗，請重新登錄",
            ErrorCategory.AUTHORIZATION: "沒有執行此操作的權限",
            ErrorCategory.EXTERNAL_SERVICE: "外部服務暫時不可用",
            ErrorCategory.INTERNAL: "系統內部錯誤，我們正在處理",
        }
        return messages.get(self.category, "發生未知錯誤")

    def _default_recovery_actions(self) -> List[str]:
        """Generate default recovery actions based on category."""
        actions = {
            ErrorCategory.NETWORK: ["檢查網絡連接", "稍後重試"],
            ErrorCategory.API_RATE_LIMIT: ["等待 30 秒後重試", "減少請求頻率"],
            ErrorCategory.DATABASE: ["系統將自動重試", "如問題持續，請聯繫支持"],
            ErrorCategory.VALIDATION: ["檢查輸入格式", "參考文檔說明"],
            ErrorCategory.AUTHENTICATION: ["重新登錄", "檢查帳號狀態"],
            ErrorCategory.AUTHORIZATION: ["聯繫管理員獲取權限"],
            ErrorCategory.EXTERNAL_SERVICE: ["稍後重試", "使用其他數據源"],
            ErrorCategory.INTERNAL: ["請聯繫技術支持", "保存當前工作"],
        }
        return actions.get(self.category, ["稍後重試", "如問題持續，請聯繫支持"])

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses."""
        return {
            "error_id": self.error_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.user_message,
            "technical_message": self.message,
            "recovery_actions": self.recovery_actions,
            "context": {k: str(v) for k, v in self.context.items()},
            "timestamp": self.timestamp.isoformat()
        }


class NetworkError(CBAError):
    """Network-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class APIRateLimitError(CBAError):
    """API rate limiting errors."""

    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        recovery_actions = [f"等待 {retry_after or 30} 秒後重試", "減少請求頻率"]
        super().__init__(
            message=message,
            category=ErrorCategory.API_RATE_LIMIT,
            severity=ErrorSeverity.LOW,
            recovery_actions=recovery_actions,
            **kwargs
        )


class DatabaseError(CBAError):
    """Database-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class ValidationError(CBAError):
    """Data validation errors."""

    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if field:
            context['field'] = field
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            context=context,
            **kwargs
        )


class AuthenticationError(CBAError):
    """Authentication errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class AuthorizationError(CBAError):
    """Authorization errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class ExternalServiceError(CBAError):
    """External service errors."""

    def __init__(self, message: str, service: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if service:
            context['service'] = service
        user_message = f"{service} 服務暫時不可用" if service else "外部服務暫時不可用"
        super().__init__(
            message=message,
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.MEDIUM,
            user_message=user_message,
            context=context,
            **kwargs
        )


class ErrorHandler:
    """
    Centralized error handling utility.

    Provides consistent error logging, classification, and user messaging.
    """

    @staticmethod
    def classify_error(error: Exception) -> CBAError:
        """
        Classify a generic exception into appropriate CBAError type.

        Args:
            error: The exception to classify

        Returns:
            Appropriate CBAError subclass instance
        """
        error_message = str(error)
        error_type = type(error).__name__

        # Network-related errors
        if any(term in error_type.lower() or term in error_message.lower()
               for term in ['connection', 'timeout', 'network', 'dns', 'refused']):
            return NetworkError(
                message=f"網絡錯誤: {error_message}",
                context={"original_error": error_type, "original_message": error_message}
            )

        # Rate limit errors
        if any(term in error_message.lower()
               for term in ['rate limit', '429', 'too many requests', 'quota exceeded']):
            return APIRateLimitError(
                message=f"API 限流: {error_message}",
                context={"original_error": error_type, "original_message": error_message}
            )

        # Database errors
        if any(term in error_type.lower() or term in error_message.lower()
               for term in ['database', 'sql', 'query', 'connection', 'pool']):
            return DatabaseError(
                message=f"數據庫錯誤: {error_message}",
                context={"original_error": error_type, "original_message": error_message}
            )

        # Validation errors
        if any(term in error_type.lower()
               for term in ['validation', 'valueerror', 'typeerror', 'pydantic']):
            return ValidationError(
                message=f"數據驗證錯誤: {error_message}",
                context={"original_error": error_type, "original_message": error_message}
            )

        # Authentication errors
        if any(term in error_message.lower()
               for term in ['authentication', 'unauthorized', 'invalid token', '401']):
            return AuthenticationError(
                message=f"身份驗證錯誤: {error_message}",
                context={"original_error": error_type, "original_message": error_message}
            )

        # Authorization errors
        if any(term in error_message.lower()
               for term in ['authorization', 'forbidden', 'permission', '403']):
            return AuthorizationError(
                message=f"權限錯誤: {error_message}",
                context={"original_error": error_type, "original_message": error_message}
            )

        # Default to internal error
        return CBAError(
            message=f"系統錯誤: {error_message}",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.MEDIUM,
            context={"original_error": error_type, "original_message": error_message}
        )

    @staticmethod
    def log_error(error: CBAError, extra_context: Optional[Dict[str, Any]] = None):
        """
        Log error with structured context.

        Args:
            error: The CBAError to log
            extra_context: Additional context to include in logs
        """
        log_context = {
            "error_id": error.error_id,
            "category": error.category.value,
            "severity": error.severity.value,
            **error.context,
            **(extra_context or {})
        }

        log_message = f"[{error.error_id}] {error.category.value.upper()}: {error.message}"

        if error.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]:
            logger.warning(log_message, extra=log_context)
        else:
            logger.error(log_message, extra=log_context, exc_info=True)

    @staticmethod
    def handle_error(
        error: Exception,
        reraise: bool = False,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> CBAError:
        """
        Handle an exception with proper classification and logging.

        Args:
            error: The exception to handle
            reraise: Whether to reraise after handling
            extra_context: Additional context for logging

        Returns:
            Classified CBAError instance

        Raises:
            CBAError: If reraise is True
        """
        # Classify the error
        if isinstance(error, CBAError):
            cba_error = error
        else:
            cba_error = ErrorHandler.classify_error(error)

        # Add traceback for non-CBA errors
        if not isinstance(error, CBAError):
            cba_error.context['traceback'] = traceback.format_exc()

        # Log the error
        ErrorHandler.log_error(cba_error, extra_context)

        # Reraise if requested
        if reraise:
            raise cba_error

        return cba_error

    @staticmethod
    def create_error_response(
        error: CBAError,
        include_technical: bool = False
    ) -> Dict[str, Any]:
        """
        Create user-facing error response for API.

        Args:
            error: The CBAError to format
            include_technical: Whether to include technical details

        Returns:
            Dictionary suitable for JSON API response
        """
        response = {
            "success": False,
            "error": {
                "id": error.error_id,
                "category": error.category.value,
                "severity": error.severity.value,
                "message": error.user_message,
                "recovery_actions": error.recovery_actions,
                "timestamp": error.timestamp.isoformat()
            }
        }

        if include_technical:
            response["error"]["technical"] = {
                "message": error.message,
                "context": error.context
            }

        return response


def handle_exception(
    error: Exception,
    reraise: bool = False,
    extra_context: Optional[Dict[str, Any]] = None
) -> CBAError:
    """
    Convenience function for error handling.

    Args:
        error: The exception to handle
        reraise: Whether to reraise after handling
        extra_context: Additional context for logging

    Returns:
        Classified CBAError instance
    """
    return ErrorHandler.handle_error(error, reraise, extra_context)

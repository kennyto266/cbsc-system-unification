"""
错误处理工具
Error Handling Utilities

职责：
- 统一错误定义
- 错误码管理
- 异常处理
"""

from typing import Any, Dict, List, Optional, Type, Union
from enum import Enum
import logging
import traceback
from datetime import datetime
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """错误码枚举"""

    # 通用错误 (1000-1999)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    TIMEOUT = "TIMEOUT"

    # 策略相关错误 (2000-2999)
    STRATEGY_NOT_FOUND = "STRATEGY_NOT_FOUND"
    STRATEGY_ALREADY_EXISTS = "STRATEGY_ALREADY_EXISTS"
    STRATEGY_INVALID_PARAMETERS = "STRATEGY_INVALID_PARAMETERS"
    STRATEGY_INVALID_STATUS = "STRATEGY_INVALID_STATUS"
    STRATEGY_CANNOT_DELETE = "STRATEGY_CANNOT_DELETE"
    STRATEGY_TEMPLATE_NOT_FOUND = "STRATEGY_TEMPLATE_NOT_FOUND"
    STRATEGY_TYPE_MISMATCH = "STRATEGY_TYPE_MISMATCH"
    STRATEGY_EXECUTION_FAILED = "STRATEGY_EXECUTION_FAILED"
    STRATEGY_ALREADY_RUNNING = "STRATEGY_ALREADY_RUNNING"
    STRATEGY_OPTIMIZATION_FAILED = "STRATEGY_OPTIMIZATION_FAILED"

    # 执行相关错误 (3000-3999)
    EXECUTION_NOT_FOUND = "EXECUTION_NOT_FOUND"
    EXECUTION_ALREADY_COMPLETED = "EXECUTION_ALREADY_COMPLETED"
    EXECUTION_CANNOT_STOP = "EXECUTION_CANNOT_STOP"
    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT"
    EXECUTION_RESOURCE_EXHAUSTED = "EXECUTION_RESOURCE_EXHAUSTED"
    EXECUTION_DATA_NOT_AVAILABLE = "EXECUTION_DATA_NOT_AVAILABLE"
    EXECUTION_FAILED = "EXECUTION_FAILED"

    # 用户相关错误 (4000-4999)
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    USER_INVALID_CREDENTIALS = "USER_INVALID_CREDENTIALS"
    USER_ACCOUNT_LOCKED = "USER_ACCOUNT_LOCKED"
    USER_PREFERENCES_INVALID = "USER_PREFERENCES_INVALID"
    USER_INSUFFICIENT_PERMISSIONS = "USER_INSUFFICIENT_PERMISSIONS"

    # 数据相关错误 (5000-5999)
    DATA_NOT_FOUND = "DATA_NOT_FOUND"
    DATA_CORRUPTION = "DATA_CORRUPTION"
    DATA_CONNECTION_FAILED = "DATA_CONNECTION_FAILED"
    DATA_CONSTRAINT_VIOLATION = "DATA_CONSTRAINT_VIOLATION"

    # 外部服务错误 (6000-6999)
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_TIMEOUT = "EXTERNAL_SERVICE_TIMEOUT"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    MARKET_DATA_UNAVAILABLE = "MARKET_DATA_UNAVAILABLE"

    # 缓存相关错误 (7000-7999)
    CACHE_CONNECTION_FAILED = "CACHE_CONNECTION_FAILED"
    CACHE_OPERATION_FAILED = "CACHE_OPERATION_FAILED"

    # WebSocket相关错误 (8000-8999)
    WEBSOCKET_CONNECTION_FAILED = "WEBSOCKET_CONNECTION_FAILED"
    WEBSOCKET_AUTHENTICATION_FAILED = "WEBSOCKET_AUTHENTICATION_FAILED"
    WEBSOCKET_MESSAGE_INVALID = "WEBSOCKET_MESSAGE_INVALID"


class BusinessError(Exception):
    """业务错误基类"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "timestamp": datetime.now().isoformat()
        }


class StrategyError(BusinessError):
    """策略相关错误"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.STRATEGY_EXECUTION_FAILED,
        strategy_id: Optional[str] = None,
        **kwargs
    ):
        if strategy_id:
            kwargs.setdefault("details", {})["strategy_id"] = strategy_id
        super().__init__(message, error_code, **kwargs)


class ExecutionError(BusinessError):
    """执行相关错误"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.EXECUTION_FAILED,
        execution_id: Optional[str] = None,
        **kwargs
    ):
        if execution_id:
            kwargs.setdefault("details", {})["execution_id"] = execution_id
        super().__init__(message, error_code, **kwargs)


class ValidationError(BusinessError):
    """验证错误"""

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if field_name:
            details["field_name"] = field_name
        if field_value is not None:
            details["field_value"] = field_value
        kwargs["details"] = details
        super().__init__(message, ErrorCode.VALIDATION_ERROR, **kwargs)


class AuthenticationError(BusinessError):
    """认证错误"""

    def __init__(self, message: str = "认证失败", **kwargs):
        super().__init__(message, ErrorCode.UNAUTHORIZED, **kwargs)


class AuthorizationError(BusinessError):
    """授权错误"""

    def __init__(self, message: str = "权限不足", **kwargs):
        super().__init__(message, ErrorCode.FORBIDDEN, **kwargs)


class NotFoundError(BusinessError):
    """资源未找到错误"""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        kwargs["details"] = details
        super().__init__(message, ErrorCode.NOT_FOUND, **kwargs)


class ConflictError(BusinessError):
    """冲突错误"""

    def __init__(
        self,
        message: str,
        conflicting_resource: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if conflicting_resource:
            details["conflicting_resource"] = conflicting_resource
        kwargs["details"] = details
        super().__init__(message, ErrorCode.CONFLICT, **kwargs)


class RateLimitError(BusinessError):
    """速率限制错误"""

    def __init__(
        self,
        message: str = "请求过于频繁",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if retry_after:
            details["retry_after"] = retry_after
        kwargs["details"] = details
        super().__init__(message, ErrorCode.RATE_LIMITED, **kwargs)


class ErrorHandler:
    """错误处理器"""

    @staticmethod
    def handle_business_error(error: BusinessError) -> HTTPException:
        """
        处理业务错误
        """
        # 根据错误码确定HTTP状态码
        status_code_map = {
            ErrorCode.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
            ErrorCode.UNAUTHORIZED: status.HTTP_401_UNAUTHORIZED,
            ErrorCode.FORBIDDEN: status.HTTP_403_FORBIDDEN,
            ErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
            ErrorCode.CONFLICT: status.HTTP_409_CONFLICT,
            ErrorCode.RATE_LIMITED: status.HTTP_429_TOO_MANY_REQUESTS,
        }

        http_status = status_code_map.get(
            error.error_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        return HTTPException(
            status_code=http_status,
            detail=error.to_dict()
        )

    @staticmethod
    def handle_validation_error(error: RequestValidationError) -> HTTPException:
        """
        处理请求验证错误
        """
        details = []
        for err in error.errors():
            details.append({
                "field": ".".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
                "type": err["type"]
            })

        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": ErrorCode.VALIDATION_ERROR.value,
                "message": "请求参数验证失败",
                "details": {
                    "validation_errors": details
                },
                "timestamp": datetime.now().isoformat()
            }
        )

    @staticmethod
    def handle_generic_error(error: Exception) -> HTTPException:
        """
        处理通用错误
        """
        logger.error(f"未处理的异常: {error}", exc_info=True)

        # 在生产环境中，不应该暴露详细的错误信息
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": ErrorCode.INTERNAL_SERVER_ERROR.value,
                "message": "服务器内部错误",
                "details": {
                    "error_id": id(error),  # 用于日志追踪
                },
                "timestamp": datetime.now().isoformat()
            }
        )

    @staticmethod
    def create_error_response(
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ) -> JSONResponse:
        """
        创建错误响应
        """
        error_data = {
            "error_code": error_code.value,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }

        return JSONResponse(
            status_code=status_code,
            content=error_data
        )


class ExceptionHandlerMiddleware:
    """异常处理中间件"""

    async def __call__(self, request: Request, call_next):
        """
        处理请求中的异常
        """
        try:
            response = await call_next(request)
            return response

        except BusinessError as e:
            logger.error(f"业务错误: {e.message}", exc_info=True)
            error_handler = ErrorHandler()
            http_exception = error_handler.handle_business_error(e)
            return JSONResponse(
                status_code=http_exception.status_code,
                content=http_exception.detail
            )

        except RequestValidationError as e:
            logger.warning(f"请求验证错误: {e}")
            error_handler = ErrorHandler()
            http_exception = error_handler.handle_validation_error(e)
            return JSONResponse(
                status_code=http_exception.status_code,
                content=http_exception.detail
            )

        except StarletteHTTPException as e:
            # FastAPI/Starlette的HTTP异常
            logger.warning(f"HTTP异常: {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error_code": ErrorCode.HTTP_STATUS_ERROR.value,
                    "message": e.detail,
                    "details": {},
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"未处理的异常: {e}", exc_info=True)
            error_handler = ErrorHandler()
            http_exception = error_handler.handle_generic_error(e)
            return JSONResponse(
                status_code=http_exception.status_code,
                content=http_exception.detail
            )


class ErrorLogger:
    """错误日志记录器"""

    @staticmethod
    def log_error(
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        request_id: Optional[str] = None
    ):
        """
        记录错误日志
        """
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_code": getattr(error, "error_code", None),
            "stack_trace": traceback.format_exc(),
            "context": context or {},
            "user_id": user_id,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }

        logger.error(f"错误记录: {error_data}")

    @staticmethod
    def log_business_error(
        error: BusinessError,
        user_id: Optional[int] = None,
        request_id: Optional[str] = None
    ):
        """
        记录业务错误
        """
        error_data = {
            "error_code": error.error_code.value,
            "error_message": error.message,
            "error_details": error.details,
            "cause": str(error.cause) if error.cause else None,
            "user_id": user_id,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }

        logger.error(f"业务错误: {error_data}")


class ErrorReporter:
    """错误报告器"""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    async def report_error(
        self,
        error: Exception,
        severity: str = "error",
        tags: Optional[List[str]] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """
        报告错误到外部监控系统（如Sentry）
        """
        if not self.enabled:
            return

        try:
            # 这里可以集成外部错误监控服务
            # 例如：Sentry、Bugsnag、Rollbar等
            error_data = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "stack_trace": traceback.format_exc(),
                "severity": severity,
                "tags": tags or [],
                "extra_data": extra_data or {},
                "timestamp": datetime.now().isoformat()
            }

            # 模拟发送到外部服务
            logger.info(f"错误报告: {error_data}")

        except Exception as e:
            logger.error(f"发送错误报告失败: {e}")


# 全局错误报告器实例
error_reporter = ErrorReporter()


# 错误处理装饰器
def handle_errors(
    error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
    error_message: str = "操作失败",
    reraise: bool = False
):
    """
    错误处理装饰器
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except BusinessError:
                if reraise:
                    raise
                error_handler = ErrorHandler()
                return error_handler.create_error_response(
                    error_code,
                    error_message
                )
            except Exception as e:
                logger.error(f"函数 {func.__name__} 执行失败: {e}", exc_info=True)
                if reraise:
                    raise
                error_handler = ErrorHandler()
                return error_handler.create_error_response(
                    error_code,
                    error_message,
                    {"error_type": type(e).__name__}
                )

        return wrapper
    return decorator


def safe_execute(
    func,
    default_return=None,
    error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
    log_error: bool = True
):
    """
    安全执行函数
    """
    async def wrapper(*args, **kwargs):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            if log_error:
                logger.error(f"安全执行失败: {e}", exc_info=True)
            if isinstance(e, BusinessError):
                ErrorLogger.log_business_error(e)
            return default_return

    return wrapper


# 导入必要的模块
import asyncio
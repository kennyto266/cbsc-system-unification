"""
API响应工具类
API Response Utilities

提供统一的API响应格式和错误处理
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum
import json
import traceback
from fastapi import HTTPException
from pydantic import BaseModel


class ResponseCode(str, Enum):
    """响应状态码枚举"""
    SUCCESS = "success"
    ERROR = "error"
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    PERMISSION_DENIED = "permission_denied"
    INTERNAL_ERROR = "internal_error"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"


class APIResponse(BaseModel):
    """统一API响应格式"""
    success: bool
    code: ResponseCode
    message: str
    data: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
    errors: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime
    request_id: Optional[str] = None

    @classmethod
    def success_response(
        cls,
        data: Any = None,
        message: str = "操作成功",
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> "APIResponse":
        """创建成功响应"""
        return cls(
            success=True,
            code=ResponseCode.SUCCESS,
            message=message,
            data=data,
            metadata=metadata,
            timestamp=datetime.utcnow(),
            request_id=request_id
        )

    @classmethod
    def error_response(
        cls,
        code: ResponseCode,
        message: str,
        errors: Optional[List[Dict[str, Any]]] = None,
        request_id: Optional[str] = None
    ) -> "APIResponse":
        """创建错误响应"""
        return cls(
            success=False,
            code=code,
            message=message,
            errors=errors,
            timestamp=datetime.utcnow(),
            request_id=request_id
        )


class PaginatedResponse(BaseModel):
    """分页响应格式"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def create(
        cls,
        items: List[Any],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse":
        """创建分页响应"""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


class APIError(Exception):
    """API错误基类"""
    def __init__(
        self,
        code: ResponseCode,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ValidationError(APIError):
    """验证错误"""
    def __init__(self, message: str, field: str = None, value: Any = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(ResponseCode.VALIDATION_ERROR, message, details)


class NotFoundError(APIError):
    """资源未找到错误"""
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource}不存在"
        if identifier:
            message += f": {identifier}"
        super().__init__(ResponseCode.NOT_FOUND, message, {"resource": resource, "id": identifier})


class PermissionError(APIError):
    """权限错误"""
    def __init__(self, message: str = "权限不足", action: str = None):
        details = {}
        if action:
            details["action"] = action
        super().__init__(ResponseCode.PERMISSION_DENIED, message, details)


class InternalError(APIError):
    """内部服务器错误"""
    def __init__(self, message: str = "内部服务器错误", original_error: Exception = None):
        details = {}
        if original_error:
            details["original_error"] = str(original_error)
            details["traceback"] = traceback.format_exc()
        super().__init__(ResponseCode.INTERNAL_ERROR, message, details)


class ResponseBuilder:
    """响应构建器"""

    @staticmethod
    def build_success(
        data: Any = None,
        message: str = "操作成功",
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> APIResponse:
        """构建成功响应"""
        return APIResponse.success_response(
            data=data,
            message=message,
            metadata=metadata,
            request_id=request_id
        )

    @staticmethod
    def build_paginated(
        items: List[Any],
        total: int,
        page: int,
        page_size: int,
        message: str = "获取成功"
    ) -> APIResponse:
        """构建分页响应"""
        paginated_data = PaginatedResponse.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )
        return APIResponse.success_response(
            data=paginated_data.dict(),
            message=message
        )

    @staticmethod
    def build_error(
        error: Union[APIError, Exception],
        request_id: Optional[str] = None
    ) -> APIResponse:
        """构建错误响应"""
        if isinstance(error, APIError):
            code = error.code
            message = error.message
            errors = [error.details] if error.details else None
        else:
            # 处理未捕获的异常
            code = ResponseCode.INTERNAL_ERROR
            message = "内部服务器错误"
            errors = [{"original_error": str(error), "traceback": traceback.format_exc()}]

        return APIResponse.error_response(
            code=code,
            message=message,
            errors=errors,
            request_id=request_id
        )


def handle_api_errors(func):
    """API错误处理装饰器"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except APIError as e:
            raise HTTPException(
                status_code=400,
                detail=ResponseBuilder.build_error(e).dict()
            )
        except Exception as e:
            error = InternalError(original_error=e)
            raise HTTPException(
                status_code=500,
                detail=ResponseBuilder.build_error(error).dict()
            )
    return wrapper


# 导出的类型和函数
__all__ = [
    "ResponseCode",
    "APIResponse",
    "PaginatedResponse",
    "APIError",
    "ValidationError",
    "NotFoundError",
    "PermissionError",
    "InternalError",
    "ResponseBuilder",
    "handle_api_errors"
]
"""
Unified API Response Format

Standardized response wrapper for all API endpoints.
"""

from datetime import datetime, timezone
from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')


class APIError(BaseModel):
    """API error details"""
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(None, description="Additional error details")


class APIResponse(BaseModel, Generic[T]):
    """
    Unified API response format.

    All endpoints should use this format for consistency.
    """
    success: bool = Field(..., description="Indicates if the request was successful")
    data: Optional[T] = Field(None, description="Response data (present on success)")
    error: Optional[APIError] = Field(None, description="Error details (present on failure)")
    message: str = Field(default="", description="Optional message providing additional context")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracing")

    class Config:
        """Pydantic config"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "success": True,
                "data": {"id": "123", "name": "Example"},
                "message": "Operation completed successfully",
                "timestamp": "2025-12-25T15:00:00Z",
                "request_id": "req_abc123"
            }
        }

    @classmethod
    def success_response(
        cls,
        data: T,
        message: str = "Operation successful",
        request_id: Optional[str] = None
    ) -> "APIResponse[T]":
        """Create a success response"""
        return cls(
            success=True,
            data=data,
            message=message,
            request_id=request_id
        )

    @classmethod
    def error_response(
        cls,
        code: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> "APIResponse[None]":
        """Create an error response"""
        return cls(
            success=False,
            error=APIError(code=code, message=message, details=details),
            message=message,
            request_id=request_id
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated response format.
    """
    items: list[T] = Field(..., description="List of items in the current page")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number (1-indexed)")
    per_page: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")
    success: bool = Field(default=True)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int = 1,
        per_page: int = 20
    ) -> "PaginatedResponse[T]":
        """Create a paginated response"""
        pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )


# Error codes constants
class ErrorCode:
    """Standard error codes"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

"""
Exception classes for CBSC Trading API SDK
"""

from typing import Optional, Any, Dict


class CBSCAPIError(Exception):
    """Base exception class for CBSC API errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(self.message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, status_code={self.status_code})"


class AuthenticationError(CBSCAPIError):
    """Raised when authentication fails"""

    def __init__(self, message: str = "Authentication failed", response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, response_data=response_data)


class RateLimitError(CBSCAPIError):
    """Raised when rate limit is exceeded"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        self.retry_after = retry_after
        super().__init__(message, status_code=429, response_data=response_data)


class NotFoundError(CBSCAPIError):
    """Raised when a resource is not found"""

    def __init__(self, message: str = "Resource not found", response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, response_data=response_data)


class ValidationError(CBSCAPIError):
    """Raised when request validation fails"""

    def __init__(self, message: str = "Validation failed", response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, response_data=response_data)


class ServerError(CBSCAPIError):
    """Raised when server error occurs"""

    def __init__(self, message: str = "Server error", response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, response_data=response_data)


class ConnectionError(CBSCAPIError):
    """Raised when connection to API fails"""

    def __init__(self, message: str = "Connection failed"):
        super().__init__(message, status_code=None)


class TimeoutError(CBSCAPIError):
    """Raised when request times out"""

    def __init__(self, message: str = "Request timeout"):
        super().__init__(message, status_code=None)
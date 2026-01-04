"""
Risk Management API v2 - Middleware
====================================

Custom middleware for authentication, authorization, rate limiting, and logging.

Author: CBSC Risk Management Team
Version: 2.0.0
"""

import time
import logging
import json
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from functools import wraps
import redis
import hashlib
import hmac
from datetime import datetime, timedelta

from .config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-based rate limiter"""

    def __init__(self, redis_url: str, default_limits: Dict[str, str]):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.default_limits = default_limits
        self.prefix = "rate_limit:"

    def is_allowed(
        self,
        key: str,
        limit: str,
        window: int
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed based on rate limit

        Args:
            key: Unique identifier for rate limiting (e.g., IP, user ID)
            limit: Rate limit string (e.g., "100/hour")
            window: Time window in seconds

        Returns:
            Tuple of (is_allowed, info_dict)
        """
        try:
            # Parse limit string
            limit_parts = limit.split("/")
            if len(limit_parts) != 2:
                return True, {"error": "Invalid limit format"}

            max_requests = int(limit_parts[0])
            window = self._parse_time_unit(limit_parts[1]) if window == 0 else window

            # Use sliding window algorithm
            now = int(time.time())
            pipeline = self.redis_client.pipeline()

            # Remove old entries
            pipeline.zremrangebyscore(
                f"{self.prefix}{key}",
                0,
                now - window
            )

            # Count current requests
            pipeline.zcard(f"{self.prefix}{key}")

            # Add current request
            pipeline.zadd(f"{self.prefix}{key}", {str(now): now})

            # Set expiration
            pipeline.expire(f"{self.prefix}{key}", window)

            results = pipeline.execute()
            current_requests = results[1]

            return current_requests < max_requests, {
                "current": current_requests,
                "limit": max_requests,
                "window": window,
                "remaining": max(0, max_requests - current_requests - 1),
                "reset_time": now + window
            }

        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Allow request if rate limiter fails
            return True, {"error": "Rate limiter unavailable"}

    def _parse_time_unit(self, unit: str) -> int:
        """Parse time unit to seconds"""
        unit = unit.lower()
        if unit == "second" or unit == "s":
            return 1
        elif unit == "minute" or unit == "m":
            return 60
        elif unit == "hour" or unit == "h":
            return 3600
        elif unit == "day" or unit == "d":
            return 86400
        else:
            return 3600  # Default to hour


# Global rate limiter instance
rate_limiter = RateLimiter(
    redis_url=settings.redis_url,
    default_limits=settings.rate_limits
)


def rate_limit(limit: str):
    """
    Decorator for rate limiting endpoints
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None

            # Find request in args/kwargs
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                request = kwargs.get('request')

            if not request:
                return await func(*args, **kwargs)

            # Get client identifier
            client_ip = request.client.host if request.client else "unknown"
            user_id = getattr(request.state, 'user_id', None)
            key = user_id if user_id else client_ip

            # Check rate limit
            allowed, info = rate_limiter.is_allowed(key, limit, 0)

            if not allowed:
                logger.warning(f"Rate limit exceeded for {key}: {info}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "limit": limit,
                        "reset_time": info.get("reset_time")
                    },
                    headers={
                        "X-RateLimit-Limit": str(info.get("limit", 0)),
                        "X-RateLimit-Remaining": str(info.get("remaining", 0)),
                        "X-RateLimit-Reset": str(info.get("reset_time", 0))
                    }
                )

            # Add rate limit headers
            response = await func(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers["X-RateLimit-Limit"] = str(info.get("limit", 0))
                response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
                response.headers["X-RateLimit-Reset"] = str(info.get("reset_time", 0))

            return response

        return wrapper
    return decorator


async def rate_limit_middleware(request: Request, call_next: Callable):
    """Rate limiting middleware"""
    # Get rate limit for endpoint
    path = request.url.path

    # Determine rate limit based on endpoint
    limit = settings.rate_limits.get("default", "100/hour")

    if "/alerts" in path:
        limit = settings.rate_limits.get("alerts", "50/hour")
    elif "/reports" in path:
        limit = settings.rate_limits.get("reports", "20/hour")
    elif "/adjustments" in path:
        limit = settings.rate_limits.get("adjustments", "20/hour")

    # Get client identifier
    client_ip = request.client.host if request.client else "unknown"
    user_id = getattr(request.state, 'user_id', None)
    key = user_id if user_id else client_ip

    # Check rate limit
    allowed, info = rate_limiter.is_allowed(key, limit, 0)

    if not allowed:
        logger.warning(f"Rate limit exceeded for {key}: {info}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "success": False,
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests",
                    "details": {
                        "limit": limit,
                        "reset_time": info.get("reset_time")
                    }
                }
            },
            headers={
                "X-RateLimit-Limit": str(info.get("limit", 0)),
                "X-RateLimit-Remaining": str(info.get("remaining", 0)),
                "X-RateLimit-Reset": str(info.get("reset_time", 0))
            }
        )

    # Process request
    response = await call_next(request)

    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(info.get("limit", 0))
    response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
    response.headers["X-RateLimit-Reset"] = str(info.get("reset_time", 0))

    return response


async def auth_middleware(request: Request, call_next: Callable):
    """Authentication middleware"""
    # Skip authentication for health and docs endpoints
    if request.url.path in ["/health", "/health/ready", "/health/live", "/docs", "/redoc", "/metrics"]:
        return await call_next(request)

    # Get authorization header
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        # No auth provided, set anonymous user
        request.state.user = {
            "id": "anonymous",
            "username": "anonymous",
            "permissions": [],
            "is_active": True
        }
        request.state.user_id = "anonymous"
        return await call_next(request)

    try:
        # Validate Bearer token
        if not auth_header.startswith("Bearer "):
            raise ValueError("Invalid authorization header format")

        token = auth_header[7:]  # Remove "Bearer " prefix

        # Mock token validation - replace with actual JWT validation
        if token.startswith("mock_"):
            user_id = token.split("_")[1]
            request.state.user = {
                "id": user_id,
                "username": f"user_{user_id}",
                "email": f"user_{user_id}@example.com",
                "permissions": ["risk:read", "risk:write"],
                "is_active": True
            }
            request.state.user_id = user_id
        else:
            # Actual JWT validation would go here
            # For now, set anonymous user
            request.state.user = {
                "id": "anonymous",
                "username": "anonymous",
                "permissions": [],
                "is_active": True
            }
            request.state.user_id = "anonymous"

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        # Set anonymous user on error
        request.state.user = {
            "id": "anonymous",
            "username": "anonymous",
            "permissions": [],
            "is_active": True
        }
        request.state.user_id = "anonymous"

    return await call_next(request)


async def audit_middleware(request: Request, call_next: Callable):
    """Audit logging middleware"""
    start_time = time.time()

    # Get request details
    method = request.method
    path = request.url.path
    query_params = dict(request.query_params)
    headers = dict(request.headers)

    # Remove sensitive headers
    sensitive_headers = ["authorization", "cookie", "x-api-key"]
    for header in sensitive_headers:
        headers.pop(header, None)

    # Get user info
    user = getattr(request.state, 'user', None)
    user_id = user.get("id", "anonymous") if user else "anonymous"

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log audit entry
    audit_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "method": method,
        "path": path,
        "query_params": query_params,
        "headers": headers,
        "status_code": response.status_code,
        "duration_ms": round(duration * 1000, 2),
        "request_id": getattr(request.state, 'request_id', None),
        "client_ip": request.client.host if request.client else None
    }

    # Log to file or external audit system
    logger.info(f"AUDIT: {json.dumps(audit_data)}")

    # Store in audit log database if needed
    # This would typically be async to avoid slowing down responses

    return response


async def error_handler_middleware(request: Request, call_next: Callable):
    """Global error handling middleware"""
    try:
        return await call_next(request)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected error
        logger.error(
            f"Unexpected error processing {request.method} {request.url.path}: {e}",
            exc_info=True
        )

        # Return generic error response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "type": "server_error"
                },
                "timestamp": time.time(),
                "request_id": getattr(request.state, 'request_id', None)
            }
        )


def require_permissions(permissions: list):
    """
    Decorator to require specific permissions
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None

            # Find request in args/kwargs
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                request = kwargs.get('request')

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )

            # Get user permissions
            user = getattr(request.state, 'user', {})
            user_permissions = user.get("permissions", [])

            # Check required permissions
            missing = [p for p in permissions if p not in user_permissions]
            if missing:
                logger.warning(
                    f"Permission denied for user {user.get('id')}: "
                    f"missing {', '.join(missing)}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Permission denied",
                        "required_permissions": permissions,
                        "missing_permissions": missing
                    }
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def sanitize_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize sensitive data from logs
    """
    sensitive_fields = [
        "password", "token", "secret", "key", "auth",
        "authorization", "cookie", "session"
    ]

    sanitized = data.copy()

    for key, value in sanitized.items():
        if isinstance(key, str) and any(field in key.lower() for field in sensitive_fields):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_sensitive_data(value)

    return sanitized


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Limit request size"""

    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "success": False,
                    "error": {
                        "code": "REQUEST_TOO_LARGE",
                        "message": f"Request size exceeds limit of {self.max_size} bytes"
                    }
                }
            )

        return await call_next(request)
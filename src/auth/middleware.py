"""
Authentication Middleware
FastAPI middleware for authentication, authorization, and security
"""

import time
import json
import os
import uuid
from typing import Optional, List, Dict, Any, Callable
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from functools import wraps
import redis
import logging

from .service import AuthService
from .utils import verify_jwt_token, mask_sensitive_data, get_client_ip
from .exceptions import (
    AuthenticationError, AuthorizationError, TokenExpiredError,
    TokenInvalidError, RateLimitExceededError
)

logger = logging.getLogger(__name__)

# Redis client for rate limiting
redis_client = None
try:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        decode_responses=True
    )
    redis_client.ping()
except Exception as e:
    logger.warning(f"Redis not available for rate limiting: {e}")


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for FastAPI"""

    def __init__(self, app, auth_service: AuthService, exclude_paths: List[str] = None):
        super().__init__(app)
        self.auth_service = auth_service
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics",
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/verify-email",
            "/api/auth/password-reset"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through authentication middleware"""
        # Check if path is excluded
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Get authorization header
        authorization = request.headers.get("authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract token
        token = authorization.split(" ")[1]

        try:
            # Verify token
            payload = verify_jwt_token(token, self.auth_service.jwt_public_key)

            # Get user
            user = self.auth_service.get_user_by_id(payload["user_id"])
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )

            # Add user to request state
            request.state.user = user
            request.state.user_id = user.id
            request.state.permissions = payload.get("permissions", [])
            request.state.roles = payload.get("roles", [])

            # Process request
            response = await call_next(request)

            return response

        except TokenExpiredError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except TokenInvalidError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10,
        exclude_paths: List[str] = None
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through rate limiting middleware"""
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Get client identifier
        client_ip = get_client_ip(request)
        user_id = getattr(request.state, "user_id", None)
        identifier = str(user_id) if user_id else client_ip

        # Check rate limits
        if redis_client:
            # Minute limit
            minute_key = f"rate_limit:{identifier}:minute"
            minute_count = redis_client.incr(minute_key)
            if minute_count == 1:
                redis_client.expire(minute_key, 60)

            # Hour limit
            hour_key = f"rate_limit:{identifier}:hour"
            hour_count = redis_client.incr(hour_key)
            if hour_count == 1:
                redis_client.expire(hour_key, 3600)

            # Check limits
            if minute_count > self.requests_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded (per minute)",
                    headers={"Retry-After": "60"}
                )

            if hour_count > self.requests_per_hour:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded (per hour)",
                    headers={"Retry-After": "3600"}
                )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        if redis_client:
            response.headers["X-RateLimit-Remaining-Minute"] = str(max(0, self.requests_per_minute - minute_count))
            response.headers["X-RateLimit-Remaining-Hour"] = str(max(0, self.requests_per_hour - hour_count))

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


class AuditMiddleware(BaseHTTPMiddleware):
    """Audit logging middleware"""

    def __init__(self, app, auth_service: AuthService, exclude_paths: List[str] = None):
        super().__init__(app)
        self.auth_service = auth_service
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log audit events"""
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Record start time
        start_time = time.time()

        # Get request details
        method = request.method
        path = request.url.path
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log audit event
            self._log_request(
                request=request,
                response=response,
                duration=duration,
                request_id=request_id
            )

            return response

        except Exception as e:
            # Log error
            duration = time.time() - start_time
            self._log_error(
                request=request,
                error=e,
                duration=duration,
                request_id=request_id
            )
            raise

    def _log_request(self, request: Request, response: Response, duration: float, request_id: str):
        """Log successful request"""
        try:
            user_id = getattr(request.state, "user_id", None)

            # Determine action from path
            action = self._get_action_from_path(request.method, request.url.path)

            # Check if this is a sensitive operation
            sensitive_actions = ["create", "update", "delete", "login", "logout", "password"]
            is_sensitive = any(s in action.lower() for s in sensitive_actions)

            # Log only sensitive operations or those with errors
            if is_sensitive or response.status_code >= 400:
                db = self.auth_service.get_db()
                try:
                    self.auth_service._log_audit(
                        db=db,
                        user_id=user_id,
                        action=action,
                        resource_type=self._get_resource_type(request.url.path),
                        status="success" if response.status_code < 400 else "error",
                        status_code=response.status_code,
                        ip_address=get_client_ip(request),
                        user_agent=request.headers.get("user-agent"),
                        endpoint=f"{request.method} {request.url.path}",
                        request_id=request_id,
                        metadata={
                            "duration": duration,
                            "response_size": response.headers.get("content-length")
                        }
                    )
                finally:
                    db.close()

        except Exception as e:
            logger.error(f"Failed to log audit: {e}")

    def _log_error(self, request: Request, error: Exception, duration: float, request_id: str):
        """Log request error"""
        try:
            user_id = getattr(request.state, "user_id", None)
            action = self._get_action_from_path(request.method, request.url.path)

            db = self.auth_service.get_db()
            try:
                self.auth_service._log_audit(
                    db=db,
                    user_id=user_id,
                    action=action,
                    resource_type=self._get_resource_type(request.url.path),
                    status="error",
                    status_code=500,
                    error_message=str(error),
                    ip_address=get_client_ip(request),
                    user_agent=request.headers.get("user-agent"),
                    endpoint=f"{request.method} {request.url.path}",
                    request_id=request_id,
                    metadata={
                        "duration": duration,
                        "error_type": type(error).__name__
                    }
                )
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to log error audit: {e}")

    def _get_action_from_path(self, method: str, path: str) -> str:
        """Extract action from request path"""
        # Map HTTP methods to actions
        method_map = {
            "GET": "read",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete"
        }

        action = method_map.get(method, "unknown")

        # Extract resource from path
        parts = path.strip("/").split("/")
        if parts:
            # Handle special cases
            if "auth" in parts:
                if "login" in parts:
                    return "auth.login"
                elif "logout" in parts:
                    return "auth.logout"
                elif "register" in parts:
                    return "auth.register"
                elif "password" in parts:
                    return "auth.password_change"
            elif "users" in parts and len(parts) > 2:
                return f"user.{action}"
            elif "roles" in parts:
                return f"role.{action}"
            elif "permissions" in parts:
                return f"permission.{action}"

        return f"{action}"


# Dependency functions for FastAPI
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    request: Request = None
) -> Optional[Any]:
    """Get current user if authenticated (optional)"""
    if not credentials:
        return None

    try:
        payload = verify_jwt_token(credentials.credentials, request.app.state.auth_service.jwt_public_key)
        user = request.app.state.auth_service.get_user_by_id(payload["user_id"])
        return user
    except:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> Any:
    """Get current user (required)"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = verify_jwt_token(credentials.credentials, request.app.state.auth_service.jwt_public_key)
        user = request.app.state.auth_service.get_user_by_id(payload["user_id"])

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        return user
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_permissions(*permissions: str):
    """Decorator to require specific permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Check permissions
            user_permissions = set(current_user.permissions)
            required_permissions = set(permissions)

            if not required_permissions.issubset(user_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {', '.join(required_permissions)}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_roles(*roles: str):
    """Decorator to require specific roles"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Check roles
            user_roles = set(current_user.role_names)
            required_roles = set(roles)

            if not required_roles.intersection(user_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient roles. Required one of: {', '.join(required_roles)}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_admin():
    """Decorator to require admin role"""
    return require_roles("admin", "super_admin")


def require_super_admin():
    """Decorator to require super admin role"""
    return require_roles("super_admin")


def require_self_or_admin():
    """Decorator to require user to be accessing own data or be admin"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            target_user_id = kwargs.get('user_id')

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Check if user is accessing own data or is admin
            user_roles = set(current_user.role_names)
            is_admin = user_roles.intersection({"admin", "super_admin"})

            if not is_admin and str(current_user.id) != str(target_user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


# RBAC check function
def check_permission(user: Any, permission: str, resource_id: str = None) -> bool:
    """
    Check if user has permission for resource

    Args:
        user: User object
        permission: Permission code
        resource_id: Optional resource ID for ownership checks

    Returns:
        True if user has permission
    """
    # Super admin has all permissions
    if "super_admin" in user.role_names:
        return True

    # Check permission in user's permissions
    if permission in user.permissions:
        # Additional check for ownership if resource_id provided
        if resource_id and str(resource_id) == str(user.id):
            return True
        return True

    return False


# Rate limiting decorator
def rate_limit(requests: int, window: int = 60, per_user: bool = True):
    """Decorator for rate limiting specific endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            if not request:
                return await func(*args, **kwargs)

            # Get identifier
            if per_user and hasattr(request.state, 'user_id'):
                identifier = f"user:{request.state.user_id}"
            else:
                identifier = f"ip:{get_client_ip(request)}"

            # Check rate limit
            if redis_client:
                key = f"rate_limit:{identifier}:{func.__name__}"
                count = redis_client.incr(key)
                if count == 1:
                    redis_client.expire(key, window)

                if count > requests:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded for {func.__name__}",
                        headers={"Retry-After": str(window)}
                    )

            return await func(*args, **kwargs)
        return wrapper
    return decorator
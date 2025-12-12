"""
非價格策略安全中間件
Non-Price Strategy Security Middleware

Extended middleware components for non-price strategy security,
including RBAC enforcement, security headers, and monitoring.
"""

import time
import logging
from typing import Callable, Optional
from datetime import datetime
from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import JSONResponse

from ..security.rbac import rbac_manager, Permission, StrategyType
from ..security.audit_logger import (
    audit_logger, AuditEventType, EventSeverity
)
from ..security.monitoring import (
    security_monitor, AlertType, ThreatLevel,
    monitor_security_event
)
from ..security.rate_limiter import rate_limiter, RateLimitMiddleware
from ..security.encryption import data_masking

logger = logging.getLogger(__name__)


class NonPriceSecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware for non-price strategies"""

    def __init__(self, app, security_config: Optional[dict] = None):
        super().__init__(app)
        self.security_config = security_config or {}
        self.rate_limit_middleware = RateLimitMiddleware(rate_limiter)

        # Paths that don't require authentication
        self.public_paths = {
            "/api/auth/login",
            "/api/auth/register",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
            "/health",
            "/metrics"
        }

        # Non-price strategy paths requiring special handling
        self.non_price_paths = {
            "/api/non-price/strategies",
            "/api/non-price/macro",
            "/api/non-price/sentiment",
            "/api/non-price/hkma",
            "/api/non-price/calendar"
        }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()

        # Get request information
        path = request.url.path
        method = request.method
        client_ip = request.client.host if request.client else "unknown"

        # Check rate limiting first
        try:
            await self._check_rate_limit(request)
        except HTTPException as e:
            await self._log_security_event(
                request=request,
                event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
                details={"path": path, "method": method}
            )
            raise

        # Skip authentication for public paths
        if path in self.public_paths or path.startswith("/static"):
            return await call_next(request)

        # Extract user information
        user_id = await self._extract_user_id(request)
        user_role = None

        if user_id:
            user_role = rbac_manager.user_roles.get(user_id)

        # Apply path-specific security measures
        if any(path.startswith(np_path) for np_path in self.non_price_paths):
            await self._handle_non_price_security(request, user_id, user_role)

        # Continue with request
        response = await call_next(request)

        # Apply security headers
        response = await self._apply_security_headers(response, user_role)

        # Apply data masking to response if needed
        if response.headers.get("content-type", "").startswith("application/json"):
            response = await self._mask_response_data(response, user_role)

        # Log successful request
        process_time = time.time() - start_time
        await self._log_request(request, response, user_id, process_time, True)

        return response

    async def _check_rate_limit(self, request: Request):
        """Check rate limits using rate limiting middleware"""
        # Create a mock call_next for the rate limit middleware
        async def mock_call_next(req):
            return Response()

        # Use the rate limit middleware to check limits
        await self.rate_limit_middleware(request, mock_call_next)

    async def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request"""
        # Try to get from JWT token
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # This would integrate with your JWT decoding
                # For now, try to get from request state
                if hasattr(request.state, 'user') and request.state.user:
                    return str(request.state.user.id)
            except Exception:
                pass

        # Try to get from session cookie
        session_id = request.cookies.get("session_id")
        if session_id:
            # This would validate session and get user
            pass

        return None

    async def _handle_non_price_security(
        self,
        request: Request,
        user_id: Optional[str],
        user_role: Optional[str]
    ):
        """Handle security for non-price strategy endpoints"""

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for non-price strategies"
            )

        # Check if user has access to non-price strategies
        if user_role and user_role in ["basic"]:
            # Basic users need explicit permission
            has_access = rbac_manager.check_permission(
                user_id=user_id,
                permission=Permission.READ_MACRO_INDICATORS
            )

            if not has_access:
                await security_monitor.create_alert(
                    alert_type=AlertType.UNAUTHORIZED_ACCESS,
                    threat_level=ThreatLevel.MEDIUM,
                    description="Basic user attempted to access non-price strategies",
                    user_id=user_id,
                    ip_address=request.client.host,
                    resource=request.url.path
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Upgrade to premium for non-price strategies"
                )

    async def _apply_security_headers(self, response: Response, user_role: Optional[str]) -> Response:
        """Apply security headers to response"""
        # Standard security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' wss: ws:; "
            "font-src 'self'; "
            "object-src 'none'; "
            "media-src 'self'; "
            "frame-src 'none';"
        )
        response.headers["Content-Security-Policy"] = csp

        # HSTS (only in production)
        if self.security_config.get("environment") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Custom headers for non-price strategies
        if user_role in ["admin", "institutional", "non_price_admin"]:
            response.headers["X-Data-Access-Level"] = "full"
        elif user_role in ["premium", "quant_analyst", "non_price_analyst"]:
            response.headers["X-Data-Access-Level"] = "restricted"
        else:
            response.headers["X-Data-Access-Level"] = "masked"

        return response

    async def _mask_response_data(self, response: Response, user_role: Optional[str]) -> Response:
        """Apply data masking to sensitive response data"""
        # Skip masking for admin/privileged users
        if user_role in ["admin", "institutional", "non_price_admin"]:
            return response

        # Get response body
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        try:
            # Parse JSON
            import json
            data = json.loads(response_body.decode())

            # Apply masking based on user role
            masked_data = data_masking.mask_sensitive_fields(
                data, user_role or "basic"
            )

            # Create new response with masked data
            return JSONResponse(
                content=masked_data,
                status_code=response.status_code,
                headers=dict(response.headers)
            )

        except Exception as e:
            # If masking fails, return original response
            logger.warning(f"Failed to mask response data: {e}")
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers)
            )

    async def _log_request(
        self,
        request: Request,
        response: Response,
        user_id: Optional[str],
        process_time: float,
        success: bool
    ):
        """Log request for audit"""
        # Log to audit logger for sensitive endpoints
        if any(path.startswith(request.url.path) for path in self.non_price_paths):
            await audit_logger.log_event(
                event_type=AuditEventType.API_ACCESS,
                user_id=user_id,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                resource=request.url.path,
                action=request.method,
                details={
                    "status_code": response.status_code,
                    "process_time": process_time
                },
                success=200 <= response.status_code < 400
            )

        # Log slow requests
        if process_time > 2.0:
            await audit_logger.log_event(
                event_type=AuditEventType.ERROR_OCCURRED,
                user_id=user_id,
                ip_address=request.client.host,
                resource=request.url.path,
                details={
                    "error_type": "slow_request",
                    "process_time": process_time
                },
                success=False
            )


class NonPriceRBACMiddleware(BaseHTTPMiddleware):
    """Role-Based Access Control middleware for non-price strategies"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Only apply to non-price strategy endpoints
        if not request.url.path.startswith("/api/non-price/"):
            return await call_next(request)

        # Extract user information
        user_id = await self._extract_user_id(request)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        # Determine required permission based on endpoint
        required_permission = self._get_required_permission(
            request.url.path,
            request.method
        )

        # Check permission
        if required_permission and not rbac_manager.check_permission(
            user_id=user_id,
            permission=required_permission
        ):
            await audit_logger.log_event(
                event_type=AuditEventType.PERMISSION_DENIED,
                user_id=user_id,
                ip_address=request.client.host,
                resource=request.url.path,
                action=request.method,
                details={"required_permission": required_permission.value},
                success=False
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {required_permission.value}"
            )

        return await call_next(request)

    async def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request"""
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # This would decode JWT and extract user_id
            # For now, try to get from request state
            if hasattr(request.state, 'user') and request.state.user:
                return str(request.state.user.id)
        return None

    def _get_required_permission(self, path: str, method: str) -> Optional[Permission]:
        """Get required permission for endpoint"""
        if method == "GET":
            if "/macro" in path:
                return Permission.READ_MACRO_INDICATORS
            elif "/sentiment" in path:
                return Permission.READ_SENTIMENT_DATA
            elif "/strategies" in path:
                return Permission.READ_PRICE_STRATEGIES
        elif method in ["POST", "PUT", "PATCH"]:
            if "/execute" in path:
                return Permission.EXECUTE_NON_PRICE_STRATEGIES
            else:
                return Permission.MODIFY_STRATEGY_PARAMS
        elif method == "DELETE":
            return Permission.MANAGE_DATA_SOURCES

        return None


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced logging middleware for security events"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Log request start
        logger.info(
            f"Security Request: {request.method} {request.url.path} - "
            f"IP: {request.client.host} - "
            f"User-Agent: {request.headers.get('user-agent', 'unknown')[:100]}"
        )

        try:
            response = await call_next(request)

            # Log suspicious status codes
            if response.status_code in [401, 403, 404, 429, 500]:
                await self._log_suspicious_response(request, response)

            return response

        except Exception as e:
            # Log errors
            await audit_logger.log_event(
                event_type=AuditEventType.ERROR_OCCURRED,
                user_id=None,  # Unknown at this point
                ip_address=request.client.host,
                resource=request.url.path,
                details={"error": str(e)},
                success=False
            )
            raise

    async def _log_suspicious_response(self, request: Request, response: Response):
        """Log suspicious response status codes"""
        event_details = {
            "status_code": response.status_code,
            "path": request.url.path,
            "method": request.method
        }

        if response.status_code == 401:
            event_type = AuditEventType.LOGIN_FAILED
            event_details["reason"] = "authentication_failed"
        elif response.status_code == 403:
            event_type = AuditEventType.PERMISSION_DENIED
            event_details["reason"] = "access_denied"
        elif response.status_code == 429:
            event_type = AuditEventType.RATE_LIMIT_EXCEEDED
            event_details["reason"] = "rate_limit_exceeded"
        else:
            event_type = AuditEventType.ERROR_OCCURRED
            event_details["reason"] = "http_error"

        await audit_logger.log_event(
            event_type=event_type,
            user_id=None,
            ip_address=request.client.host,
            resource=request.url.path,
            details=event_details,
            success=False
        )


def setup_non_price_security_middleware(app, security_config: Optional[dict] = None):
    """Setup all security middleware for non-price strategies"""

    # Order is important - outermost middleware runs first

    # 1. Rate limiting
    app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

    # 2. Comprehensive security middleware
    app.add_middleware(NonPriceSecurityMiddleware, security_config=security_config)

    # 3. RBAC middleware
    app.add_middleware(NonPriceRBACMiddleware)

    # 4. Security logging
    app.add_middleware(SecurityLoggingMiddleware)

    logger.info("Non-price strategy security middleware configured")
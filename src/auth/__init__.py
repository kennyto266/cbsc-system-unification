"""
Enhanced Authentication and User Management Service
Enterprise-grade security implementation for CBSC system
"""

from .service import AuthService
from .models import (
    User, Role, Permission, UserRole, RolePermission,
    UserSession, UserDevice, LoginHistory, PasswordHistory,
    AuditLog
)
from .schemas import (
    UserCreate, UserLogin, UserResponse, Token, TokenRefresh,
    PasswordChange, PasswordReset, PasswordResetConfirm,
    EmailVerification, UserUpdate, RoleCreate, PermissionCreate,
    UserDeviceResponse, LoginHistoryResponse, AuditLogResponse
)
from .middleware import (
    AuthMiddleware, RBACMiddleware, RateLimitMiddleware,
    AuditMiddleware
)
from .exceptions import (
    AuthenticationError, AuthorizationError, TokenExpiredError,
    UserLockedError, InvalidCredentialsError, PermissionDeniedError
)
from .utils import (
    generate_jwt_tokens, verify_jwt_token, hash_password,
    verify_password, generate_password_reset_token, verify_email_token
)

__version__ = "1.0.0"
__author__ = "CBSC Development Team"

# Export main components
__all__ = [
    "AuthService",
    "User", "Role", "Permission", "UserRole", "RolePermission",
    "UserSession", "UserDevice", "LoginHistory", "PasswordHistory",
    "AuditLog",
    "UserCreate", "UserLogin", "UserResponse", "Token", "TokenRefresh",
    "PasswordChange", "PasswordReset", "PasswordResetConfirm",
    "EmailVerification", "UserUpdate", "RoleCreate", "PermissionCreate",
    "UserDeviceResponse", "LoginHistoryResponse", "AuditLogResponse",
    "AuthMiddleware", "RBACMiddleware", "RateLimitMiddleware",
    "AuditMiddleware",
    "AuthenticationError", "AuthorizationError", "TokenExpiredError",
    "UserLockedError", "InvalidCredentialsError", "PermissionDeniedError",
    "generate_jwt_tokens", "verify_jwt_token", "hash_password",
    "verify_password", "generate_password_reset_token", "verify_email_token"
]
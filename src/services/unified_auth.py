"""
Unified Authentication Service
==============================

Complete authentication and authorization solution combining all auth implementations:
- JWT token management (RS256/HS256)
- Multi-factor authentication (TOTP)
- Password hashing with argon2
- Role-based access control (RBAC)
- Session management
- Social login support
- Login history and audit
"""

# Export all auth components from the main auth service
from src.api.services.auth import (
    # Models
    User,
    Role,
    Permission,
    LoginHistory,
    UserSession,
    SocialAccount,
    Base,
    user_roles,
    role_permissions,

    # Managers
    JWTManager,
    MFAManager,
    PasswordManager,

    # Main Service
    AuthService,

    # Dependencies
    get_auth_service,
    get_current_user,
    require_permission,
)

__all__ = [
    # Models
    "User",
    "Role",
    "Permission",
    "LoginHistory",
    "UserSession",
    "SocialAccount",
    "Base",
    "user_roles",
    "role_permissions",

    # Managers
    "JWTManager",
    "MFAManager",
    "PasswordManager",

    # Main Service
    "AuthService",

    # Dependencies
    "get_auth_service",
    "get_current_user",
    "require_permission",
]

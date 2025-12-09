"""
安全模組 - 合規性和安全性措施

包含身份驗證、授權、加密、審計和合規性檢查
"""

# 訪問控制和權限管理
from .access_control import (
    ABACManager,
    APIAccessManager,
    APIKey,
    Attribute,
    BackupCode,
    Context,
    EndpointPermission,
    MFAManager,
    MFAMethod,
    Permission,
    Policy,
    RateLimit,
    RBACManager,
    Role,
    RoleHierarchy,
    RolePermission,
    Session,
    SessionManager,
    TokenManager,
    TOTPProvider,
    UserRole,
)

__all__ = [
    # RBAC
    "RBACManager",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "RoleHierarchy",
    # ABAC
    "ABACManager",
    "Policy",
    "Attribute",
    "Context",
    # MFA
    "MFAManager",
    "MFAMethod",
    "TOTPProvider",
    "BackupCode",
    # Session
    "SessionManager",
    "Session",
    "TokenManager",
    # API
    "APIAccessManager",
    "APIKey",
    "RateLimit",
    "EndpointPermission",
]

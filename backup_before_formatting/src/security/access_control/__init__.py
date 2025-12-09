"""
港股量化交易系統 - 訪問控制與權限管理模塊
提供完整的RBAC、ABAC、MFA、會話管理和API訪問控制功能

模塊結構:
- rbac: 基於角色的訪問控制
- abac: 基於屬性的訪問控制
- mfa: 多因素認證
- session: 會話管理
- api_access: API訪問控制
- middleware: 中間件
"""

from .abac import ABACManager, Attribute, Context, Policy
from .api_access import APIAccessManager, APIKey, EndpointPermission, RateLimit
from .mfa import BackupCode, MFAManager, MFAMethod, TOTPProvider
from .rbac import Permission, RBACManager, Role, RoleHierarchy, RolePermission, UserRole
from .session import Session, SessionManager, TokenManager

__all__ = [
    "RBACManager",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "RoleHierarchy",
    "ABACManager",
    "Policy",
    "Attribute",
    "Context",
    "MFAManager",
    "MFAMethod",
    "TOTPProvider",
    "BackupCode",
    "SessionManager",
    "Session",
    "TokenManager",
    "APIAccessManager",
    "APIKey",
    "RateLimit",
    "EndpointPermission",
]

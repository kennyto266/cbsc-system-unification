"""
Middleware package
中間件包
"""

from .auth_middleware import (
    require_permissions,
    require_role,
    require_super_admin,
    require_strategy_admin,
    require_premium,
    PermissionChecker,
    create_permission_middleware,
    get_current_user_with_permissions,
    get_permission_checker,
    RESOURCE_PERMISSIONS,
    get_resource_permission
)

__all__ = [
    "require_permissions",
    "require_role",
    "require_super_admin",
    "require_strategy_admin",
    "require_premium",
    "PermissionChecker",
    "create_permission_middleware",
    "get_current_user_with_permissions",
    "get_permission_checker",
    "RESOURCE_PERMISSIONS",
    "get_resource_permission"
]
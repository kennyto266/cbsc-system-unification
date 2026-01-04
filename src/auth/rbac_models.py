"""
RBAC Models - Role-Based Access Control Models
基於角色的訪問控制模型

Defines the core RBAC data structures for the CBSC trading system.
"""

from enum import Enum
from typing import List, Dict, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import json


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    TRADER = "trader"
    ANALYST = "analyst"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Permission enumeration"""
    # Strategy permissions
    READ_STRATEGIES = "read_strategies"
    WRITE_STRATEGIES = "write_strategies"
    DELETE_STRATEGIES = "delete_strategies"
    EXECUTE_STRATEGIES = "execute_strategies"

    # Trading permissions
    EXECUTE_TRADES = "execute_trades"
    VIEW_POSITIONS = "view_positions"
    MANAGE_ORDERS = "manage_orders"

    # Performance permissions
    VIEW_PERFORMANCE = "view_performance"
    EXPORT_REPORTS = "export_reports"

    # User management permissions
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    VIEW_AUDIT_LOGS = "view_audit_logs"

    # System permissions
    SYSTEM_CONFIG = "system_config"
    VIEW_SYSTEM_STATUS = "view_system_status"


@dataclass
class RolePermissions:
    """Role permission mapping"""
    role: UserRole
    permissions: List[Permission]
    description: str


# RBAC permission configuration
RBAC_CONFIG: Dict[UserRole, List[Permission]] = {
    UserRole.ADMIN: [
        # All permissions
        Permission.READ_STRATEGIES,
        Permission.WRITE_STRATEGIES,
        Permission.DELETE_STRATEGIES,
        Permission.EXECUTE_STRATEGIES,
        Permission.EXECUTE_TRADES,
        Permission.VIEW_POSITIONS,
        Permission.MANAGE_ORDERS,
        Permission.VIEW_PERFORMANCE,
        Permission.EXPORT_REPORTS,
        Permission.MANAGE_USERS,
        Permission.MANAGE_ROLES,
        Permission.VIEW_AUDIT_LOGS,
        Permission.SYSTEM_CONFIG,
        Permission.VIEW_SYSTEM_STATUS,
    ],
    UserRole.TRADER: [
        Permission.READ_STRATEGIES,
        Permission.WRITE_STRATEGIES,
        Permission.EXECUTE_STRATEGIES,
        Permission.EXECUTE_TRADES,
        Permission.VIEW_POSITIONS,
        Permission.MANAGE_ORDERS,
        Permission.VIEW_PERFORMANCE,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_SYSTEM_STATUS,
    ],
    UserRole.ANALYST: [
        Permission.READ_STRATEGIES,
        Permission.WRITE_STRATEGIES,
        Permission.VIEW_PERFORMANCE,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_SYSTEM_STATUS,
    ],
    UserRole.VIEWER: [
        Permission.READ_STRATEGIES,
        Permission.VIEW_PERFORMANCE,
        Permission.VIEW_SYSTEM_STATUS,
    ]
}


@dataclass
class UserPermissionContext:
    """User permission context for runtime checks"""
    user_id: int
    username: str
    role: UserRole
    permissions: Set[Permission]
    device_id: str = None
    session_id: str = None
    expires_at: datetime = None

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions

    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        return any(p in self.permissions for p in permissions)

    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all of the specified permissions"""
        return all(p in self.permissions for p in permissions)


@dataclass
class AuditLogEntry:
    """Audit log entry for security events"""
    user_id: int
    username: str
    action: str
    resource: str
    permission: Permission
    success: bool
    ip_address: str
    user_agent: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    device_info: Dict[str, Any] = field(default_factory=dict)
    failure_reason: str = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'action': self.action,
            'resource': self.resource,
            'permission': self.permission.value,
            'success': self.success,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat(),
            'device_info': self.device_info,
            'failure_reason': self.failure_reason
        }


def get_role_permissions(role: UserRole) -> List[Permission]:
    """Get permissions for a given role"""
    return RBAC_CONFIG.get(role, [])


def get_role_description(role: UserRole) -> str:
    """Get description for a given role"""
    descriptions = {
        UserRole.ADMIN: "系统管理员 - 完全访问权限",
        UserRole.TRADER: "交易员 - 执行交易和管理策略",
        UserRole.ANALYST: "分析师 - 分析策略和性能",
        UserRole.VIEWER: "查看者 - 只读访问"
    }
    return descriptions.get(role, "未知角色")


def create_user_context(user_id: int, username: str, role: UserRole,
                       device_id: str = None, session_id: str = None,
                       expires_at: datetime = None) -> UserPermissionContext:
    """Create a user permission context"""
    permissions = set(get_role_permissions(role))
    return UserPermissionContext(
        user_id=user_id,
        username=username,
        role=role,
        permissions=permissions,
        device_id=device_id,
        session_id=session_id,
        expires_at=expires_at
    )


def validate_permission_requirement(required_permissions: List[Permission],
                                    user_context: UserPermissionContext,
                                    require_all: bool = True) -> bool:
    """
    Validate if user context meets permission requirements

    Args:
        required_permissions: List of required permissions
        user_context: User permission context
        require_all: If True, user must have ALL permissions.
                     If False, user must have AT LEAST ONE permission.

    Returns:
        True if permission requirement is met
    """
    if require_all:
        return user_context.has_all_permissions(required_permissions)
    else:
        return user_context.has_any_permission(required_permissions)

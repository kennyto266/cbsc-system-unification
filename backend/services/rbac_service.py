"""
Enhanced RBAC Service - Role-Based Access Control
Provides comprehensive permission management with hierarchical roles and resource-based access.
"""

from typing import List, Dict, Any, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
import logging
from functools import lru_cache
from datetime import datetime

try:
    from models.rbac_models import Permission, Resource, Action
    from models.unified_models import User, Role, UserRole
except ImportError:
    # Fallback types
    from enum import Enum
    class Permission(str, Enum):
        READ = "read"
        WRITE = "write"
        DELETE = "delete"
        ADMIN = "admin"
        CREATE = "create"
        UPDATE = "update"

    class Resource(str, Enum):
        STRATEGIES = "strategies"
        USERS = "users"
        PORTFOLIOS = "portfolios"
        TRADES = "trades"
        MARKET_DATA = "market_data"
        BACKTESTS = "backtests"
        API_KEYS = "api_keys"
        WEBHOOKS = "webhooks"

    class Action(str, Enum):
        CREATE = "create"
        READ = "read"
        UPDATE = "update"
        DELETE = "delete"
        EXECUTE = "execute"
        MANAGE = "manage"

logger = logging.getLogger(__name__)


@dataclass
class RoleDefinition:
    """Role definition with permissions"""
    name: str
    description: str
    permissions: Dict[str, Set[str]] = field(default_factory=dict)  # resource -> actions
    inherits_from: List[str] = field(default_factory=list)
    is_system_role: bool = False


# Predefined role definitions
ROLE_DEFINITIONS: Dict[str, RoleDefinition] = {
    "super_admin": RoleDefinition(
        name="super_admin",
        description="Full system access including user management",
        permissions={
            "*": {"*"}  # Wildcard for all resources and actions
        },
        is_system_role=True
    ),

    "admin": RoleDefinition(
        name="admin",
        description="Administrative access for managing users and strategies",
        permissions={
            "users": {"create", "read", "update", "delete", "manage"},
            "strategies": {"create", "read", "update", "delete", "execute", "manage"},
            "portfolios": {"create", "read", "update", "delete", "manage"},
            "trades": {"read", "update", "delete"},
            "backtests": {"create", "read", "update", "delete", "execute"},
            "market_data": {"read"},
            "api_keys": {"create", "read", "update", "delete", "manage"},
            "webhooks": {"create", "read", "update", "delete", "manage"},
        },
        is_system_role=True
    ),

    "trader": RoleDefinition(
        name="trader",
        description="Trading access for executing strategies",
        permissions={
            "strategies": {"create", "read", "update", "delete", "execute"},
            "portfolios": {"read"},
            "trades": {"create", "read"},
            "backtests": {"create", "read", "execute"},
            "market_data": {"read"},
        }
    ),

    "analyst": RoleDefinition(
        name="analyst",
        description="Read-only access for analysis and monitoring",
        permissions={
            "strategies": {"read"},
            "portfolios": {"read"},
            "trades": {"read"},
            "backtests": {"read"},
            "market_data": {"read"},
        }
    ),

    "developer": RoleDefinition(
        name="developer",
        description="API access for integration and development",
        permissions={
            "strategies": {"read", "create", "update"},
            "portfolios": {"read"},
            "trades": {"read"},
            "backtests": {"read", "execute"},
            "market_data": {"read"},
            "api_keys": {"create", "read", "update", "delete"},
            "webhooks": {"create", "read", "update", "delete"},
        }
    ),

    "viewer": RoleDefinition(
        name="viewer",
        description="Limited read-only access",
        permissions={
            "strategies": {"read"},
            "portfolios": {"read"},
            "market_data": {"read"},
        }
    ),
}


class RBACService:
    """
    Role-Based Access Control Service
    Manages permissions and authorization checks
    """

    def __init__(self):
        self._role_cache: Dict[str, RoleDefinition] = {}
        self._permission_cache: Dict[str, Set[str]] = {}
        self._init_role_cache()

    def _init_role_cache(self) -> None:
        """Initialize role definitions cache"""
        self._role_cache = ROLE_DEFINITIONS.copy()
        logger.info(f"Initialized RBAC with {len(self._role_cache)} roles")

    def get_role(self, role_name: str) -> Optional[RoleDefinition]:
        """Get role definition by name"""
        return self._role_cache.get(role_name)

    def get_all_roles(self) -> List[RoleDefinition]:
        """Get all available roles"""
        return list(self._role_cache.values())

    @lru_cache(maxsize=1024)
    def get_effective_permissions(
        self,
        role_names: List[str]
    ) -> Dict[str, Set[str]]:
        """
        Get effective permissions for a user with multiple roles.
        Handles role inheritance and permission aggregation.

        Args:
            role_names: List of role names assigned to the user

        Returns:
            Dictionary mapping resources to allowed actions
        """
        effective_permissions: Dict[str, Set[str]] = {}

        for role_name in role_names:
            role_def = self.get_role(role_name)
            if not role_def:
                logger.warning(f"Unknown role: {role_name}")
                continue

            # Process inherited roles first
            for inherited_role in role_def.inherits_from:
                inherited_perms = self.get_effective_permissions([inherited_role])
                for resource, actions in inherited_perms.items():
                    if resource not in effective_permissions:
                        effective_permissions[resource] = set()
                    effective_permissions[resource].update(actions)

            # Add direct permissions
            for resource, actions in role_def.permissions.items():
                if resource == "*":
                    # Wildcard permission - grant all
                    if "*" not in effective_permissions:
                        effective_permissions["*"] = set()
                    effective_permissions["*"].update(actions)
                else:
                    if resource not in effective_permissions:
                        effective_permissions[resource] = set()
                    effective_permissions[resource].update(actions)

        return effective_permissions

    def has_permission(
        self,
        user_roles: List[str],
        resource: str,
        action: str
    ) -> bool:
        """
        Check if user has permission to perform action on resource.

        Args:
            user_roles: List of role names assigned to user
            resource: Resource being accessed
            action: Action being performed

        Returns:
            True if user has permission, False otherwise
        """
        effective_permissions = self.get_effective_permissions(tuple(user_roles))

        # Check wildcard permission first
        if "*" in effective_permissions:
            wildcard_actions = effective_permissions["*"]
            if "*" in wildcard_actions or action in wildcard_actions:
                return True

        # Check specific resource permission
        if resource in effective_permissions:
            allowed_actions = effective_permissions[resource]
            if "*" in allowed_actions or action in allowed_actions:
                return True

        return False

    def has_any_permission(
        self,
        user_roles: List[str],
        resource: str,
        actions: List[str]
    ) -> bool:
        """
        Check if user has any of the specified permissions on resource.

        Args:
            user_roles: List of role names
            resource: Resource being accessed
            actions: List of actions to check

        Returns:
            True if user has any of the permissions
        """
        return any(
            self.has_permission(user_roles, resource, action)
            for action in actions
        )

    def has_all_permissions(
        self,
        user_roles: List[str],
        resource: str,
        actions: List[str]
    ) -> bool:
        """
        Check if user has all of the specified permissions on resource.

        Args:
            user_roles: List of role names
            resource: Resource being accessed
            actions: List of actions to check

        Returns:
            True if user has all permissions
        """
        return all(
            self.has_permission(user_roles, resource, action)
            for action in actions
        )

    def filter_resources_by_permission(
        self,
        user_roles: List[str],
        resource_type: str,
        action: str,
        resource_ids: List[Any]
    ) -> List[Any]:
        """
        Filter resource IDs based on user permissions.
        For future use with row-level security.

        Args:
            user_roles: List of role names
            resource_type: Type of resource
            action: Action to check
            resource_ids: List of resource IDs to filter

        Returns:
            Filtered list of resource IDs user can access
        """
        if self.has_permission(user_roles, resource_type, action):
            return resource_ids

        # Future: Implement resource-specific filtering
        # For now, return empty list if no permission
        return []

    def get_required_permission_error(
        self,
        resource: str,
        action: str
    ) -> Dict[str, Any]:
        """
        Get standardized error response for permission denied.

        Args:
            resource: Resource that was accessed
            action: Action that was attempted

        Returns:
            Error response dictionary
        """
        return {
            "success": False,
            "error": {
                "code": "PERMISSION_DENIED",
                "message": f"Permission denied: '{action}' action on '{resource}' requires elevated privileges",
                "required_permission": f"{resource}:{action}",
                "documentation": "/docs/authorization"
            },
            "timestamp": datetime.utcnow().isoformat()
        }


# Global RBAC service instance
rbac_service = RBACService()


def require_permission(resource: str, action: str):
    """
    Decorator for requiring permission on FastAPI endpoints.
    Use with dependency injection.

    Args:
        resource: Resource being accessed
        action: Action being performed

    Example:
        @router.get("/strategies/{id}")
        @require_permission("strategies", "read")
        async def get_strategy(id: int, current_user: User = Depends(get_current_user)):
            ...
    """
    from functools import wraps

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs (injected by FastAPI Depends)
            current_user = kwargs.get('current_user')
            if not current_user:
                from fastapi import HTTPException
                raise HTTPException(status_code=401, detail="Authentication required")

            # Check permission
            user_roles = [role.name for role in current_user.roles] if hasattr(current_user, 'roles') else ['viewer']

            if not rbac_service.has_permission(user_roles, resource, action):
                from fastapi import HTTPException
                error_response = rbac_service.get_required_permission_error(resource, action)
                raise HTTPException(status_code=403, detail=error_response)

            return await func(*args, **kwargs)
        return wrapper

    return decorator


def check_permission(resource: str, action: str, user_roles: List[str]) -> bool:
    """
    Helper function to check permissions.

    Args:
        resource: Resource being accessed
        action: Action being performed
        user_roles: List of user role names

    Returns:
        True if user has permission
    """
    return rbac_service.has_permission(user_roles, resource, action)


# Permission constants for use in code
class Permissions:
    """Permission constants"""

    # Strategy permissions
    STRATEGY_READ = "strategies:read"
    STRATEGY_CREATE = "strategies:create"
    STRATEGY_UPDATE = "strategies:update"
    STRATEGY_DELETE = "strategies:delete"
    STRATEGY_EXECUTE = "strategies:execute"
    STRATEGY_MANAGE = "strategies:manage"

    # User permissions
    USER_READ = "users:read"
    USER_CREATE = "users:create"
    USER_UPDATE = "users:update"
    USER_DELETE = "users:delete"
    USER_MANAGE = "users:manage"

    # Portfolio permissions
    PORTFOLIO_READ = "portfolios:read"
    PORTFOLIO_CREATE = "portfolios:create"
    PORTFOLIO_UPDATE = "portfolios:update"
    PORTFOLIO_DELETE = "portfolios:delete"
    PORTFOLIO_MANAGE = "portfolios:manage"

    # Trade permissions
    TRADE_READ = "trades:read"
    TRADE_CREATE = "trades:create"
    TRADE_UPDATE = "trades:update"
    TRADE_DELETE = "trades:delete"

    # Backtest permissions
    BACKTEST_READ = "backtests:read"
    BACKTEST_CREATE = "backtests:create"
    BACKTEST_EXECUTE = "backtests:execute"
    BACKTEST_DELETE = "backtests:delete"

    # API Key permissions
    API_KEY_READ = "api_keys:read"
    API_KEY_CREATE = "api_keys:create"
    API_KEY_UPDATE = "api_keys:update"
    API_KEY_DELETE = "api_keys:delete"
    API_KEY_MANAGE = "api_keys:manage"

    # Webhook permissions
    WEBHOOK_READ = "webhooks:read"
    WEBHOOK_CREATE = "webhooks:create"
    WEBHOOK_UPDATE = "webhooks:update"
    WEBHOOK_DELETE = "webhooks:delete"


__all__ = [
    'RBACService',
    'rbac_service',
    'require_permission',
    'check_permission',
    'Permissions',
    'RoleDefinition',
    'ROLE_DEFINITIONS',
]

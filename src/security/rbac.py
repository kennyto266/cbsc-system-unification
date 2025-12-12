"""
Role-Based Access Control (RBAC) System for Non-Price Strategies

This module implements comprehensive role-based permissions for accessing
non-price strategy data and functionality, ensuring proper access control
according to user roles and organizational policies.
"""

from enum import Enum
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging
from functools import wraps
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User roles with different access levels"""
    BASIC_USER = "basic"
    PREMIUM_USER = "premium"
    INSTITUTIONAL_USER = "institutional"
    ADMIN = "admin"
    QUANT_ANALYST = "quant_analyst"
    NON_PRICE_VIEWER = "non_price_viewer"
    NON_PRICE_ANALYST = "non_price_analyst"
    NON_PRICE_ADMIN = "non_price_admin"


class Permission(Enum):
    """ granular permissions for different actions"""

    # Read permissions for price strategies
    READ_PRICE_STRATEGIES = "read_price_strategies"
    READ_PRICE_PERFORMANCE = "read_price_performance"

    # Read permissions for non-price strategies
    READ_MACRO_INDICATORS = "read_macro_indicators"
    READ_SENTIMENT_DATA = "read_sentiment_data"
    READ_REAL_TIME_SIGNALS = "read_real_time_signals"
    READ_ECONOMIC_CALENDAR = "read_economic_calendar"
    READ_NEWS_FEED = "read_news_feed"

    # Write permissions
    EXECUTE_STRATEGIES = "execute_strategies"
    MODIFY_STRATEGY_PARAMS = "modify_strategy_params"
    CREATE_CUSTOM_STRATEGIES = "create_custom_strategies"

    # Non-price specific permissions
    ACCESS_HKMA_DATA = "access_hkma_data"
    ACCESS_SENTIMENT_API = "access_sentiment_api"
    EXECUTE_NON_PRICE_STRATEGIES = "execute_non_price_strategies"
    MODIFY_MACRO_CONFIG = "modify_macro_config"

    # Admin permissions
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_DATA_SOURCES = "manage_data_sources"
    ACCESS_SENSITIVE_DATA = "access_sensitive_data"
    EXPORT_DATA = "export_data"
    MANAGE_API_KEYS = "manage_api_keys"


class StrategyType(Enum):
    """Types of strategies with different access requirements"""
    PRICE_BASED = "price_based"
    MACRO_INDICATORS = "macro_indicators"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    ALTERNATIVE_DATA = "alternative_data"
    COMBINED_STRATEGIES = "combined_strategies"
    ECONOMIC_CALENDAR = "economic_calendar"
    NEWS_SENTIMENT = "news_sentiment"


class DataAccessLevel(Enum):
    """Data access sensitivity levels"""
    PUBLIC = "public"
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"
    TOP_SECRET = "top_secret"


@dataclass
class RolePermission:
    """Permission configuration for a role"""
    role: UserRole
    permissions: Set[Permission]
    strategy_access: Set[StrategyType]
    data_access_level: DataAccessLevel
    rate_limits: Dict[str, int]
    data_retention_days: int


class RBACManager:
    """Role-Based Access Control Manager for CBSC System"""

    def __init__(self):
        self.role_permissions = self._initialize_role_permissions()
        self.user_roles: Dict[str, UserRole] = {}  # user_id -> role
        self.logger = logging.getLogger(__name__)

    def _initialize_role_permissions(self) -> Dict[UserRole, RolePermission]:
        """Initialize role-based permissions with non-price strategy support"""

        return {
            UserRole.BASIC_USER: RolePermission(
                role=UserRole.BASIC_USER,
                permissions={
                    Permission.READ_PRICE_STRATEGIES,
                    Permission.READ_PRICE_PERFORMANCE,
                    # Limited macro access
                    Permission.READ_MACRO_INDICATORS,
                },
                strategy_access={
                    StrategyType.PRICE_BASED,
                    StrategyType.MACRO_INDICATORS,
                },
                data_access_level=DataAccessLevel.PUBLIC,
                rate_limits={
                    'api_calls_per_minute': 60,
                    'real_time_connections': 1,
                    'data_exports_per_hour': 2,
                    'strategy_executions_per_hour': 10
                },
                data_retention_days=30
            ),

            UserRole.PREMIUM_USER: RolePermission(
                role=UserRole.PREMIUM_USER,
                permissions={
                    # Price strategy permissions
                    Permission.READ_PRICE_STRATEGIES,
                    Permission.READ_PRICE_PERFORMANCE,
                    # Non-price read permissions
                    Permission.READ_MACRO_INDICATORS,
                    Permission.READ_SENTIMENT_DATA,
                    Permission.READ_ECONOMIC_CALENDAR,
                    Permission.READ_NEWS_FEED,
                    # Execution permissions
                    Permission.EXECUTE_STRATEGIES,
                    Permission.MODIFY_STRATEGY_PARAMS,
                },
                strategy_access={
                    StrategyType.PRICE_BASED,
                    StrategyType.MACRO_INDICATORS,
                    StrategyType.SENTIMENT_ANALYSIS,
                    StrategyType.ECONOMIC_CALENDAR,
                },
                data_access_level=DataAccessLevel.RESTRICTED,
                rate_limits={
                    'api_calls_per_minute': 300,
                    'real_time_connections': 5,
                    'data_exports_per_hour': 20,
                    'strategy_executions_per_hour': 100
                },
                data_retention_days=90
            ),

            UserRole.NON_PRICE_VIEWER: RolePermission(
                role=UserRole.NON_PRICE_VIEWER,
                permissions={
                    # Read-only access to non-price strategies
                    Permission.READ_MACRO_INDICATORS,
                    Permission.READ_SENTIMENT_DATA,
                    Permission.READ_ECONOMIC_CALENDAR,
                    Permission.READ_NEWS_FEED,
                    Permission.READ_PRICE_PERFORMANCE,
                },
                strategy_access={
                    StrategyType.MACRO_INDICATORS,
                    StrategyType.SENTIMENT_ANALYSIS,
                    StrategyType.ECONOMIC_CALENDAR,
                    StrategyType.NEWS_SENTIMENT,
                },
                data_access_level=DataAccessLevel.RESTRICTED,
                rate_limits={
                    'api_calls_per_minute': 150,
                    'real_time_connections': 2,
                    'data_exports_per_hour': 10,
                    'strategy_executions_per_hour': 0  # No execution rights
                },
                data_retention_days=60
            ),

            UserRole.NON_PRICE_ANALYST: RolePermission(
                role=UserRole.NON_PRICE_ANALYST,
                permissions={
                    # Full read access to non-price data
                    Permission.READ_MACRO_INDICATORS,
                    Permission.READ_SENTIMENT_DATA,
                    Permission.READ_REAL_TIME_SIGNALS,
                    Permission.READ_ECONOMIC_CALENDAR,
                    Permission.READ_NEWS_FEED,
                    Permission.READ_PRICE_PERFORMANCE,
                    # Limited execution rights
                    Permission.EXECUTE_NON_PRICE_STRATEGIES,
                    Permission.MODIFY_STRATEGY_PARAMS,
                    Permission.CREATE_CUSTOM_STRATEGIES,
                    # Special data access
                    Permission.ACCESS_HKMA_DATA,
                    Permission.ACCESS_SENTIMENT_API,
                },
                strategy_access={
                    StrategyType.MACRO_INDICATORS,
                    StrategyType.SENTIMENT_ANALYSIS,
                    StrategyType.ALTERNATIVE_DATA,
                    StrategyType.COMBINED_STRATEGIES,
                    StrategyType.ECONOMIC_CALENDAR,
                    StrategyType.NEWS_SENTIMENT,
                },
                data_access_level=DataAccessLevel.RESTRICTED,
                rate_limits={
                    'api_calls_per_minute': 500,
                    'real_time_connections': 10,
                    'data_exports_per_hour': 50,
                    'strategy_executions_per_hour': 200
                },
                data_retention_days=180
            ),

            UserRole.INSTITUTIONAL_USER: RolePermission(
                role=UserRole.INSTITUTIONAL_USER,
                permissions={
                    # All read permissions
                    Permission.READ_PRICE_STRATEGIES,
                    Permission.READ_PRICE_PERFORMANCE,
                    Permission.READ_MACRO_INDICATORS,
                    Permission.READ_SENTIMENT_DATA,
                    Permission.READ_REAL_TIME_SIGNALS,
                    Permission.READ_ECONOMIC_CALENDAR,
                    Permission.READ_NEWS_FEED,
                    # All write permissions
                    Permission.EXECUTE_STRATEGIES,
                    Permission.EXECUTE_NON_PRICE_STRATEGIES,
                    Permission.MODIFY_STRATEGY_PARAMS,
                    Permission.CREATE_CUSTOM_STRATEGIES,
                    # Special permissions
                    Permission.ACCESS_HKMA_DATA,
                    Permission.ACCESS_SENTIMENT_API,
                    Permission.EXPORT_DATA,
                },
                strategy_access={
                    StrategyType.PRICE_BASED,
                    StrategyType.MACRO_INDICATORS,
                    StrategyType.SENTIMENT_ANALYSIS,
                    StrategyType.ALTERNATIVE_DATA,
                    StrategyType.COMBINED_STRATEGIES,
                    StrategyType.ECONOMIC_CALENDAR,
                    StrategyType.NEWS_SENTIMENT,
                },
                data_access_level=DataAccessLevel.CONFIDENTIAL,
                rate_limits={
                    'api_calls_per_minute': 1000,
                    'real_time_connections': 20,
                    'data_exports_per_hour': 100,
                    'strategy_executions_per_hour': 500
                },
                data_retention_days=365
            ),

            UserRole.QUANT_ANALYST: RolePermission(
                role=UserRole.QUANT_ANALYST,
                permissions={
                    # Comprehensive read access
                    Permission.READ_PRICE_STRATEGIES,
                    Permission.READ_PRICE_PERFORMANCE,
                    Permission.READ_MACRO_INDICATORS,
                    Permission.READ_SENTIMENT_DATA,
                    Permission.READ_REAL_TIME_SIGNALS,
                    Permission.READ_ECONOMIC_CALENDAR,
                    Permission.READ_NEWS_FEED,
                    # Advanced permissions
                    Permission.CREATE_CUSTOM_STRATEGIES,
                    Permission.MODIFY_STRATEGY_PARAMS,
                    Permission.MODIFY_MACRO_CONFIG,
                    Permission.ACCESS_HKMA_DATA,
                    Permission.ACCESS_SENTIMENT_API,
                    # Limited execution
                    Permission.EXECUTE_STRATEGIES,
                    Permission.EXECUTE_NON_PRICE_STRATEGIES,
                },
                strategy_access={
                    StrategyType.PRICE_BASED,
                    StrategyType.MACRO_INDICATORS,
                    StrategyType.SENTIMENT_ANALYSIS,
                    StrategyType.ALTERNATIVE_DATA,
                    StrategyType.COMBINED_STRATEGIES,
                    StrategyType.ECONOMIC_CALENDAR,
                    StrategyType.NEWS_SENTIMENT,
                },
                data_access_level=DataAccessLevel.CONFIDENTIAL,
                rate_limits={
                    'api_calls_per_minute': 800,
                    'real_time_connections': 15,
                    'data_exports_per_hour': 80,
                    'strategy_executions_per_hour': 400
                },
                data_retention_days=365
            ),

            UserRole.NON_PRICE_ADMIN: RolePermission(
                role=UserRole.NON_PRICE_ADMIN,
                permissions={
                    # All permissions except system-level admin
                    Permission.READ_PRICE_STRATEGIES,
                    Permission.READ_PRICE_PERFORMANCE,
                    Permission.READ_MACRO_INDICATORS,
                    Permission.READ_SENTIMENT_DATA,
                    Permission.READ_REAL_TIME_SIGNALS,
                    Permission.READ_ECONOMIC_CALENDAR,
                    Permission.READ_NEWS_FEED,
                    # Full non-price permissions
                    Permission.EXECUTE_STRATEGIES,
                    Permission.EXECUTE_NON_PRICE_STRATEGIES,
                    Permission.MODIFY_STRATEGY_PARAMS,
                    Permission.CREATE_CUSTOM_STRATEGIES,
                    Permission.MODIFY_MACRO_CONFIG,
                    Permission.ACCESS_HKMA_DATA,
                    Permission.ACCESS_SENTIMENT_API,
                    Permission.ACCESS_SENSITIVE_DATA,
                    # Management permissions
                    Permission.MANAGE_DATA_SOURCES,
                    Permission.EXPORT_DATA,
                    Permission.MANAGE_API_KEYS,
                },
                strategy_access=set(StrategyType),  # All strategy types
                data_access_level=DataAccessLevel.CONFIDENTIAL,
                rate_limits={
                    'api_calls_per_minute': 2000,
                    'real_time_connections': 50,
                    'data_exports_per_hour': 200,
                    'strategy_executions_per_hour': 1000
                },
                data_retention_days=730  # 2 years
            ),

            UserRole.ADMIN: RolePermission(
                role=UserRole.ADMIN,
                permissions=set(Permission),  # All permissions
                strategy_access=set(StrategyType),  # All strategies
                data_access_level=DataAccessLevel.TOP_SECRET,
                rate_limits={
                    'api_calls_per_minute': 10000,
                    'real_time_connections': 100,
                    'data_exports_per_hour': 500,
                    'strategy_executions_per_hour': 2000
                },
                data_retention_days=2555  # 7 years
            )
        }

    def check_permission(
        self,
        user_id: str,
        permission: Permission,
        strategy_type: Optional[StrategyType] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if user has permission for specific action"""

        try:
            user_role = self.user_roles.get(user_id)
            if not user_role:
                self.logger.warning(f"User {user_id} has no assigned role")
                return False

            role_permission = self.role_permissions.get(user_role)
            if not role_permission:
                self.logger.error(f"No permissions defined for role {user_role}")
                return False

            # Check basic permission
            if permission not in role_permission.permissions:
                self._log_permission_denied(user_id, user_role, permission, strategy_type)
                return False

            # Check strategy type access if specified
            if strategy_type and strategy_type not in role_permission.strategy_access:
                self._log_strategy_access_denied(user_id, user_role, strategy_type)
                return False

            # Additional context checks
            if context:
                return self._check_context_permissions(user_role, role_permission, context)

            return True

        except Exception as e:
            self.logger.error(f"Error checking permission: {e}")
            return False

    def _check_context_permissions(
        self,
        role: UserRole,
        role_permission: RolePermission,
        context: Dict[str, Any]
    ) -> bool:
        """Check additional context-based permissions"""

        # Check data sensitivity level
        if 'data_sensitivity' in context:
            required_level = context['data_sensitivity']
            if not self._check_data_access_level(role_permission.data_access_level, required_level):
                return False

        # Check rate limits
        if 'check_rate_limit' in context:
            return True  # Will be handled by rate limiter

        # Check time-based restrictions
        if 'time_restricted' in context and context['time_restricted']:
            if role in [UserRole.BASIC_USER, UserRole.NON_PRICE_VIEWER]:
                # Basic users only access during market hours
                current_hour = datetime.now().hour
                if not (9 <= current_hour <= 16):  # Market hours
                    return False

        return True

    def _check_data_access_level(
        self,
        user_level: DataAccessLevel,
        required_level: DataAccessLevel
    ) -> bool:
        """Check if user can access data of required sensitivity"""
        level_hierarchy = {
            DataAccessLevel.PUBLIC: 0,
            DataAccessLevel.RESTRICTED: 1,
            DataAccessLevel.CONFIDENTIAL: 2,
            DataAccessLevel.TOP_SECRET: 3
        }

        return level_hierarchy[user_level] >= level_hierarchy[required_level]

    def assign_role(self, user_id: str, role: UserRole, assigned_by: str) -> bool:
        """Assign role to user with audit logging"""

        try:
            old_role = self.user_roles.get(user_id)

            # Log role assignment
            self._log_security_event(
                event_type="role_assignment",
                user_id=user_id,
                details={
                    "old_role": old_role.value if old_role else None,
                    "new_role": role.value,
                    "assigned_by": assigned_by,
                    "timestamp": datetime.now().isoformat()
                }
            )

            self.user_roles[user_id] = role

            self.logger.info(f"Role {role.value} assigned to user {user_id} by {assigned_by}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to assign role {role} to user {user_id}: {e}")
            return False

    def get_user_permissions(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get all permissions and settings for a user"""

        user_role = self.user_roles.get(user_id)
        if not user_role:
            return None

        role_permission = self.role_permissions.get(user_role)
        if not role_permission:
            return None

        return {
            "role": user_role.value,
            "permissions": list(role_permission.permissions),
            "strategy_access": list(role_permission.strategy_access),
            "data_access_level": role_permission.data_access_level.value,
            "rate_limits": role_permission.rate_limits,
            "data_retention_days": role_permission.data_retention_days
        }

    def get_accessible_strategies(self, user_id: str) -> List[StrategyType]:
        """Get list of strategies accessible to user"""

        user_role = self.user_roles.get(user_id)
        if not user_role:
            return [StrategyType.PRICE_BASED]

        return list(self.role_permissions[user_role].strategy_access)

    def get_user_rate_limits(self, user_id: str) -> Dict[str, int]:
        """Get rate limits for user"""

        user_role = self.user_roles.get(user_id)
        if not user_role:
            return self.role_permissions[UserRole.BASIC_USER].rate_limits

        return self.role_permissions[user_role].rate_limits

    def _log_permission_denied(
        self,
        user_id: str,
        role: UserRole,
        permission: Permission,
        strategy_type: Optional[StrategyType] = None
    ) -> None:
        """Log permission denial for security monitoring"""
        self.logger.warning(
            f"Permission denied: User {user_id} (role: {role.value}) "
            f"attempted to access {permission.value}"
            f"{' for ' + strategy_type.value if strategy_type else ''}"
        )

    def _log_strategy_access_denied(
        self,
        user_id: str,
        role: UserRole,
        strategy_type: StrategyType
    ) -> None:
        """Log strategy access denial"""
        self.logger.warning(
            f"Strategy access denied: User {user_id} (role: {role.value}) "
            f"attempted to access {strategy_type.value}"
        )

    def _log_security_event(self, event_type: str, user_id: str, details: Dict[str, Any]) -> None:
        """Log security-related events"""
        try:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "user_id": user_id,
                "details": details
            }

            # This would integrate with the audit logging system
            logger.info(f"Security Event: {event_type} - User: {user_id} - Details: {details}")

        except Exception as e:
            self.logger.error(f"Failed to log security event: {e}")


# Decorator for permission checking
def require_permission(permission: Permission, strategy_type: Optional[StrategyType] = None):
    """Decorator to check permissions before executing function"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from request or function arguments
            user_id = None
            for arg in args:
                if hasattr(arg, 'user') and hasattr(arg.user, 'id'):
                    user_id = arg.user.id
                    break
                elif hasattr(arg, 'id'):
                    user_id = arg.id

            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Check permissions using global RBAC manager
            rbac = RBACManager()
            if not rbac.check_permission(user_id, permission, strategy_type):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Global RBAC manager instance
rbac_manager = RBACManager()


# Initialize with some test users (remove in production)
def _initialize_test_users():
    """Initialize test users for development"""
    test_users = {
        "user_001": UserRole.BASIC_USER,
        "user_002": UserRole.PREMIUM_USER,
        "user_003": UserRole.NON_PRICE_VIEWER,
        "user_004": UserRole.NON_PRICE_ANALYST,
        "user_005": UserRole.QUANT_ANALYST,
        "admin_001": UserRole.ADMIN,
        "np_admin_001": UserRole.NON_PRICE_ADMIN,
        "inst_001": UserRole.INSTITUTIONAL_USER,
    }

    for user_id, role in test_users.items():
        rbac_manager.assign_role(user_id, role, "system_init")


# Initialize test users
_initialize_test_users()
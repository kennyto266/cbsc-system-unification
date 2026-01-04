"""
FastAPI dependencies
FastAPI依賴項
"""

from typing import Generator, Optional, Dict, Any, Union, TYPE_CHECKING
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import os
import jwt
from datetime import datetime, timezone, timedelta
from typing import List

# Import async database configuration
from .core.database import AsyncSessionLocal, get_db as get_async_db
from .core.config import settings

# Security
security = HTTPBearer()

# JWT Configuration
JWT_SECRET_KEY = settings.jwt_secret
JWT_ALGORITHM = settings.jwt_algorithm
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Import models and services only for type checking (avoid circular imports)
if TYPE_CHECKING:
    from .models.user import User, Role
    from .services.rbac_service import RBACService
    from .middleware.auth_middleware import PermissionChecker

# Database dependency - use async from core.database
async def get_db() -> AsyncSession:
    """Get database session (async)"""
    async for session in get_async_db():
        yield session

# JWT Token utilities
def create_access_token(data: dict, expires_delta: Optional[int] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# Current user dependency with RBAC support
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user with RBAC support
    獲取當前認證用戶（支持RBAC）
    """
    from .models.user import User

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate JWT token
    try:
        payload = verify_token(credentials.credentials)
        user_id: str = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed"
        )

    # Fetch user from database with roles (async query)
    from sqlalchemy import select
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is locked"
        )

    return user

# Get RBAC service dependency
def get_rbac_service_dependency(
    db: AsyncSession = Depends(get_db)
):
    """Get RBAC service instance"""
    from .services.rbac_service import get_rbac_service
    return get_rbac_service(db)

# Alias for get_rbac_service for external imports
get_rbac_service = get_rbac_service_dependency

# Get permission checker dependency
def get_permission_checker_dependency(
    rbac_service: "RBACService" = Depends(get_rbac_service_dependency)
) -> "PermissionChecker":
    """Get permission checker instance"""
    from .middleware.auth_middleware import get_permission_checker
    return get_permission_checker(rbac_service)

# Role-based permission checker
async def check_permission(
    resource_type: str,
    action: str,
    resource_id: Optional[str] = None
):
    """
    Create permission checker dependency
    創建權限檢查依賴
    """
    from .middleware.auth_middleware import get_resource_permission, ResourceType, ResourceAction

    resource_type_enum, action_enum = get_resource_permission(resource_type, action)

    async def permission_checker(
        current_user: "User" = Depends(get_current_user),
        rbac_service: "RBACService" = Depends(get_rbac_service_dependency),
        request: Request = None
    ):
        """Check if user has required permission"""
        context = {
            'ip_address': request.client.host if request else None,
            'user_agent': request.headers.get('user-agent') if request else None,
            'endpoint': str(request.url) if request else None
        }

        permission_result = await rbac_service.check_permission(
            user=current_user,
            resource_type=resource_type_enum,
            action=action_enum,
            resource_id=resource_id,
            context=context
        )

        if not permission_result.granted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission_result.reason or 'Insufficient permissions'}"
            )

        return permission_result

    return permission_checker

# Require specific role(s)
def require_roles(required_roles: List[str], require_all: bool = False):
    """
    Require user to have specific role(s)
    要求用戶擁有特定角色

    Args:
        required_roles: List of required role names
        require_all: If True, user must have all roles; if False, any role is sufficient
    """
    async def role_checker(
        current_user: "User" = Depends(get_current_user)
    ) -> "User":
        user_roles = [role.name for role in current_user.roles]

        if require_all:
            # User must have all required roles
            if not all(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required all roles: {', '.join(required_roles)}"
                )
        else:
            # User must have at least one required role
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required any role: {', '.join(required_roles)}"
                )

        return current_user

    return role_checker

# Predefined role checkers
require_admin = require_roles(['admin', 'super_admin'])
require_strategy_admin = require_roles(['admin', 'super_admin', 'strategy_admin'])
require_analyst = require_roles(['admin', 'super_admin', 'strategy_admin', 'analyst'])
require_premium_user = lambda: get_current_user  # Will be checked via user.is_premium

# Optional: Check if user is premium
async def require_premium(
    current_user: "User" = Depends(get_current_user)
) -> "User":
    """Require user to have premium subscription"""
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required"
        )
    return current_user

# Optional: Check if user is verified
async def require_verified(
    current_user: "User" = Depends(get_current_user)
) -> "User":
    """Require user to be verified"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return current_user

# Get user with all permissions
async def get_user_with_permissions(
    current_user: "User" = Depends(get_current_user),
    rbac_service: "RBACService" = Depends(get_rbac_service_dependency)
) -> dict:
    """Get user with all their permissions"""
    permissions = await rbac_service.get_user_permissions(current_user.id, include_roles=True)
    return {
        "user": current_user,
        "permissions": permissions
    }

# Health check dependency
async def health_check() -> bool:
    """Health check dependency"""
    return True

# Permission check decorators for routes
def permission_required(resource_type: str, action: str):
    """Permission decorator for routes"""
    return Depends(check_permission(resource_type, action))

def role_required(roles: Union[str, List[str]], require_all: bool = False):
    """Role decorator for routes"""
    if isinstance(roles, str):
        roles = [roles]
    return Depends(require_roles(roles, require_all))
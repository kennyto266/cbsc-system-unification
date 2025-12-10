"""
权限管理工具
Permission Management Utilities

职责：
- 用户身份验证
- 策略权限检查
- 操作权限验证
"""

from fastapi import Depends, HTTPException, status, WebSocket
from typing import Optional, Callable, Any
from functools import wraps
import logging
import jwt
from datetime import datetime, timedelta

from ..repositories.user_repository import UserRepository
from ..models import User

logger = logging.getLogger(__name__)

# JWT配置
JWT_SECRET_KEY = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


class PermissionManager:
    """权限管理器"""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_current_user(self, token: str) -> User:
        """
        从JWT token获取当前用户
        """
        try:
            # 解码JWT token
            payload = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM]
            )

            user_id = payload.get("sub")
            if user_id is None:
                raise ValueError("Invalid token payload")

            # 获取用户信息
            user = await self.user_repo.get_by_id(int(user_id))
            if not user:
                raise ValueError("User not found")

            if not user.is_active:
                raise ValueError("User is inactive")

            return user

        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.JWTError:
            raise ValueError("Invalid token")

    async def require_authentication(self, token: str) -> User:
        """
        要求用户认证
        """
        user = await self.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未授权访问",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    async def check_strategy_permission(
        self,
        strategy_id: str,
        user: User,
        action: str
    ) -> bool:
        """
        检查策略权限
        """
        # 管理员有所有权限
        if user.is_admin:
            return True

        # 获取策略信息
        from ..repositories.strategy_repository import StrategyRepository
        strategy_repo = StrategyRepository()
        strategy = await strategy_repo.get_by_id(strategy_id)

        if not strategy:
            return False

        # 检查是否为策略所有者
        if strategy.user_id != user.id:
            return False

        # 检查操作权限
        if action == "delete" and strategy.is_active:
            return False

        if action == "execute" and not strategy.is_active:
            return False

        return True


# 全局权限管理器实例
_permission_manager: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    """
    获取权限管理器实例
    """
    global _permission_manager
    if _permission_manager is None:
        user_repo = UserRepository()
        _permission_manager = PermissionManager(user_repo)
    return _permission_manager


def create_access_token(user_id: int) -> str:
    """
    创建访问令牌
    """
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


async def get_current_user_from_token(token: str = None) -> User:
    """
    从token获取当前用户（依赖注入）
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    permission_manager = get_permission_manager()
    return await permission_manager.require_authentication(token)


async def get_current_user(authorization: str = None) -> User:
    """
    获取当前用户（从Authorization头）
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authentication scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证格式",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await get_current_user_from_token(token)


async def require_strategy_permission(
    strategy_id: str,
    action: str
) -> Callable[[Any], Any]:
    """
    策略权限检查装饰器
    """
    async def checker(user: User = Depends(get_current_user)):
        permission_manager = get_permission_manager()

        # 对于不需要特定策略ID的操作，直接返回
        if action in ["view", "batch", "create"]:
            return user

        has_permission = await permission_manager.check_strategy_permission(
            strategy_id, user, action
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权限执行操作: {action}"
            )
        return user

    return checker


def require_admin(user: User = Depends(get_current_user)) -> User:
    """
    要求管理员权限
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return user


async def authenticate_websocket(websocket: WebSocket, **kwargs) -> Optional[User]:
    """
    WebSocket认证
    """
    try:
        # 从查询参数获取token
        token = websocket.query_params.get("token")
        if not token:
            # 尝试从headers获取
            auth_header = websocket.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]

        if not token:
            await websocket.close(code=4001, reason="缺少认证令牌")
            return None

        # 验证token
        permission_manager = get_permission_manager()
        user = await permission_manager.get_current_user(token)

        if not user:
            await websocket.close(code=4002, reason="无效的认证令牌")
            return None

        return user

    except Exception as e:
        logger.error(f"WebSocket认证失败: {e}")
        await websocket.close(code=4003, reason="认证失败")
        return None


def require_websocket_auth(websocket: WebSocket, **kwargs) -> Optional[User]:
    """
    WebSocket认证装饰器
    """
    async def wrapper():
        return await authenticate_websocket(websocket, **kwargs)

    return wrapper


# 权限级别枚举
class PermissionLevel:
    """权限级别"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


async def check_permission_level(
    user: User,
    required_level: str
) -> bool:
    """
    检查用户权限级别
    """
    if required_level == PermissionLevel.READ:
        return user.is_active
    elif required_level == PermissionLevel.WRITE:
        return user.is_active
    elif required_level == PermissionLevel.DELETE:
        return user.is_active
    elif required_level == PermissionLevel.ADMIN:
        return user.is_admin
    else:
        return False


def require_permission(level: str):
    """
    权限级别要求装饰器
    """
    async def permission_checker(user: User = Depends(get_current_user)):
        if not await check_permission_level(user, level):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要{level}权限"
            )
        return user

    return permission_checker


# 角色权限映射
ROLE_PERMISSIONS = {
    "user": [
        "strategy:create",
        "strategy:read:own",
        "strategy:update:own",
        "strategy:execute:own",
        "profile:read:own",
        "profile:update:own"
    ],
    "admin": [
        "strategy:*",
        "user:*",
        "system:*"
    ]
}


async def check_role_permission(
    user: User,
    permission: str
) -> bool:
    """
    检查角色权限
    """
    role = "admin" if user.is_admin else "user"
    permissions = ROLE_PERMISSIONS.get(role, [])

    # 支持通配符权限
    for perm in permissions:
        if perm == "*":
            return True
        if perm.endswith(":*"):
            prefix = perm[:-2]
            if permission.startswith(prefix):
                return True
        if perm == permission:
            return True

    return False


def require_role_permission(permission: str):
    """
    角色权限要求装饰器
    """
    async def role_checker(user: User = Depends(get_current_user)):
        if not await check_role_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要权限: {permission}"
            )
        return user

    return role_checker


# 速率限制
class RateLimiter:
    """简单的内存速率限制器"""

    def __init__(self):
        self.requests = {}

    def is_allowed(
        self,
        key: str,
        limit: int,
        window: int
    ) -> bool:
        """
        检查是否允许请求
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=window)

        # 清理过期记录
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]
        else:
            self.requests[key] = []

        # 检查限制
        if len(self.requests[key]) >= limit:
            return False

        # 记录当前请求
        self.requests[key].append(now)
        return True


# 全局速率限制器
rate_limiter = RateLimiter()


def require_rate_limit(limit: int = 100, window: int = 3600):
    """
    速率限制装饰器
    """
    async def rate_limiter_checker(user: User = Depends(get_current_user)):
        key = f"user:{user.id}"
        if not rate_limiter.is_allowed(key, limit, window):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"请求过于频繁，限制: {limit}/{window}秒"
            )
        return user

    return rate_limiter_checker
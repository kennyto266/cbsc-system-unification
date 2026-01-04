"""
Authorization Middleware
授權中間件

提供基於RBAC的權限檢查中間件和裝飾器。
"""

from typing import List, Optional, Dict, Any, Callable
from functools import wraps
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from src.models.rbac_models import ResourceType, ResourceAction, PermissionResultSchema
from src.models.user import User
from src.services.rbac_service import RBACService
from src.core.logging import logger

# Security
security = HTTPBearer()


def require_permissions(
    resource_type: ResourceType,
    action: ResourceAction,
    resource_id_param: Optional[str] = None,
    check_ownership: bool = False
):
    """
    權限檢查裝飾器

    Args:
        resource_type: 資源類型
        action: 操作類型
        resource_id_param: 資源ID參數名稱（從路徑或查詢參數獲取）
        check_ownership: 是否檢查資源所有權
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 從kwargs中獲取必要的依賴
            current_user: User = kwargs.get('current_user')
            rbac_service: RBACService = kwargs.get('rbac_service')
            request: Request = kwargs.get('request')

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # 獲取資源ID
            resource_id = None
            if resource_id_param:
                # 從路徑參數獲取
                if hasattr(request, 'path_params') and resource_id_param in request.path_params:
                    resource_id = request.path_params[resource_id_param]
                # 從查詢參數獲取
                elif hasattr(request, 'query_params') and resource_id_param in request.query_params:
                    resource_id = request.query_params[resource_id_param]
                # 從請求體獲取（需要提前解析）
                elif 'resource_id' in kwargs:
                    resource_id = kwargs['resource_id']

            # 構建上下文
            context = {
                'ip_address': request.client.host if request else None,
                'user_agent': request.headers.get('user-agent') if request else None,
                'endpoint': str(request.url) if request else None
            }

            # 檢查權限
            permission_result = await rbac_service.check_permission(
                user=current_user,
                resource_type=resource_type,
                action=action,
                resource_id=resource_id,
                context=context
            )

            if not permission_result.granted:
                logger.warning(
                    f"Permission denied for user {current_user.id} on {resource_type.value}:{action.value}",
                    extra={
                        "user_id": current_user.id,
                        "resource_type": resource_type.value,
                        "action": action.value,
                        "resource_id": resource_id,
                        "reason": permission_result.reason
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission_result.reason or 'Insufficient permissions'}"
                )

            # 將權限結果添加到kwargs，供後續使用
            kwargs['permission_result'] = permission_result

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(roles: List[str]):
    """
    角色檢查裝飾器

    Args:
        roles: 要求的角色列表
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user: User = kwargs.get('current_user')

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            user_roles = [role.name for role in current_user.roles]
            if not any(role in user_roles for role in roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(roles)}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_super_admin():
    """要求超級管理員權限"""
    return require_role(['super_admin', 'admin'])


def require_strategy_admin():
    """要求策略管理員權限"""
    return require_role(['super_admin', 'admin', 'strategy_admin'])


def require_premium():
    """要求高級用戶權限"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user: User = kwargs.get('current_user')

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            if not current_user.is_premium:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Premium subscription required"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


class PermissionChecker:
    """權限檢查器類"""

    def __init__(self, rbac_service: RBACService):
        self.rbac_service = rbac_service

    async def check_and_filter(
        self,
        user: User,
        resource_type: ResourceType,
        action: ResourceAction,
        resources: List[Any],
        resource_id_getter: Callable[[Any], str] = lambda x: x.id
    ) -> List[Any]:
        """
        檢查並過濾資源列表

        Args:
            user: 當前用戶
            resource_type: 資源類型
            action: 操作類型
            resources: 資源列表
            resource_id_getter: 獲取資源ID的函數

        Returns:
            過濾後的資源列表
        """
        if not resources:
            return []

        # 檢查用戶是否有全局權限
        global_permission = await self.rbac_service.check_permission(
            user=user,
            resource_type=resource_type,
            action=ResourceAction.READ
        )

        if global_permission.granted and global_permission.source in ['super_admin', 'system']:
            return resources

        # 過濾資源
        filtered_resources = []
        for resource in resources:
            resource_id = resource_id_getter(resource)
            permission = await self.rbac_service.check_permission(
                user=user,
                resource_type=resource_type,
                action=action,
                resource_id=resource_id
            )
            if permission.granted:
                filtered_resources.append(resource)

        return filtered_resources

    async def can_access(
        self,
        user: User,
        resource_type: ResourceType,
        action: ResourceAction,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """檢查用戶是否可以訪問資源"""
        result = await self.rbac_service.check_permission(
            user=user,
            resource_type=resource_type,
            action=action,
            resource_id=resource_id,
            context=context
        )
        return result.granted


# FastAPI依賴注入函數
def get_current_user_with_permissions(
    credentials: dict = Depends(security),
    db: Session = Depends(lambda: None)  # 需要實際的數據庫依賴
):
    """獲取當前用戶並驗證"""
    # 這裡需要實現JWT驗證邏輯
    # 暫時返回一個示例用戶
    from ..models.user import User
    user = User(
        id="user-001",
        username="user",
        email="user@example.com",
        is_active=True
    )
    return user


def get_permission_checker(
    rbac_service: RBACService = Depends(lambda: None)  # 需要實際的RBAC服務依賴
) -> PermissionChecker:
    """獲取權限檢查器"""
    return PermissionChecker(rbac_service)


# 中間件工廠函數
def create_permission_middleware(
    public_paths: List[str] = None,
    auth_header_name: str = "Authorization"
):
    """
    創建權限檢查中間件

    Args:
        public_paths: 公開路徑列表（不需要權限檢查）
        auth_header_name: 認證頭部名稱
    """
    public_paths = public_paths or [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register"
    ]

    async def middleware(request: Request, call_next):
        # 檢查是否為公開路徑
        path = str(request.url.path)
        if any(path.startswith(public_path) for public_path in public_paths):
            return await call_next(request)

        # 獲取認證頭
        auth_header = request.headers.get(auth_header_name)
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication header"
            )

        # 驗證JWT令牌（這裡需要實現實際的JWT驗證邏輯）
        try:
            # 解析JWT令牌獲取用戶信息
            # user_info = decode_jwt_token(auth_header)
            # 將用戶信息添加到request.state
            # request.state.current_user = user_info
            pass
        except Exception as e:
            logger.error(f"JWT validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

        # 繼續處理請求
        response = await call_next(request)
        return response

    return middleware


# 資源權限映射配置
RESOURCE_PERMISSIONS = {
    # 策略管理
    "strategy": {
        "create": (ResourceType.STRATEGY, ResourceAction.CREATE),
        "read": (ResourceType.STRATEGY, ResourceAction.READ),
        "update": (ResourceType.STRATEGY, ResourceAction.UPDATE),
        "delete": (ResourceType.STRATEGY, ResourceAction.DELETE),
        "execute": (ResourceType.STRATEGY, ResourceAction.EXECUTE),
    },
    # 回測管理
    "backtest": {
        "create": (ResourceType.BACKTEST, ResourceAction.CREATE),
        "read": (ResourceType.BACKTEST, ResourceAction.READ),
        "update": (ResourceType.BACKTEST, ResourceAction.UPDATE),
        "delete": (ResourceType.BACKTEST, ResourceAction.DELETE),
        "execute": (ResourceType.BACKTEST, ResourceAction.EXECUTE),
    },
    # 交易管理
    "trading": {
        "create": (ResourceType.TRADING, ResourceAction.CREATE),
        "read": (ResourceType.TRADING, ResourceAction.READ),
        "update": (ResourceType.TRADING, ResourceAction.UPDATE),
        "delete": (ResourceType.TRADING, ResourceAction.DELETE),
        "execute": (ResourceType.TRADING, ResourceAction.EXECUTE),
        "approve": (ResourceType.TRADING, ResourceAction.APPROVE),
    },
    # 用戶管理
    "user": {
        "create": (ResourceType.USER, ResourceAction.CREATE),
        "read": (ResourceType.USER, ResourceAction.READ),
        "update": (ResourceType.USER, ResourceAction.UPDATE),
        "delete": (ResourceType.USER, ResourceAction.DELETE),
    },
    # 角色管理
    "role": {
        "create": (ResourceType.ROLE, ResourceAction.CREATE),
        "read": (ResourceType.ROLE, ResourceAction.READ),
        "update": (ResourceType.ROLE, ResourceAction.UPDATE),
        "delete": (ResourceType.ROLE, ResourceAction.DELETE),
    },
    # 報告管理
    "report": {
        "create": (ResourceType.REPORT, ResourceAction.CREATE),
        "read": (ResourceType.REPORT, ResourceAction.READ),
        "update": (ResourceType.REPORT, ResourceAction.UPDATE),
        "delete": (ResourceType.REPORT, ResourceAction.DELETE),
        "export": (ResourceType.REPORT, ResourceAction.EXPORT),
    },
    # 系統管理
    "system": {
        "read": (ResourceType.SYSTEM, ResourceAction.READ),
        "update": (ResourceType.SYSTEM, ResourceAction.UPDATE),
        "admin": (ResourceType.SYSTEM, ResourceAction.ADMIN),
    },
    # 投資組合管理
    "portfolio": {
        "create": (ResourceType.PORTFOLIO, ResourceAction.CREATE),
        "read": (ResourceType.PORTFOLIO, ResourceAction.READ),
        "update": (ResourceType.PORTFOLIO, ResourceAction.UPDATE),
        "delete": (ResourceType.PORTFOLIO, ResourceAction.DELETE),
    },
    # 市場數據
    "market_data": {
        "read": (ResourceType.MARKET_DATA, ResourceAction.READ),
        "export": (ResourceType.MARKET_DATA, ResourceAction.EXPORT),
    }
}


def get_resource_permission(resource: str, action: str) -> tuple:
    """獲取資源權限映射"""
    if resource not in RESOURCE_PERMISSIONS:
        raise ValueError(f"Unknown resource type: {resource}")

    if action not in RESOURCE_PERMISSIONS[resource]:
        raise ValueError(f"Unknown action '{action}' for resource '{resource}'")

    return RESOURCE_PERMISSIONS[resource][action]
"""
權限管理服務
Permission Management Service

基於BaseBusinessService實現的權限管理服務，
提供統一的RBAC（基於角色的訪問控制）功能。

職責：
- 角色管理
- 權限定義和分配
- 資源訪問控制
- 權限繼承和組合
"""

from typing import List, Optional, Dict, Any, Set
from datetime import datetime
import logging
from enum import Enum

from .base_business_service import BaseBusinessService
from ..models.permission import (
    Role, Permission, Resource,
    RoleAssignment, PermissionGrant,
    ResourceType, Action
)
from ..schemas.permission import (
    RoleCreate, RoleUpdate, RoleResponse,
    PermissionCreate, PermissionResponse,
    ResourceResponse
)
from ..utils.validators import PermissionValidator
from ..utils.permissions import PermissionChecker
from ..utils.events import EventBus
from ..utils.cache import CacheManager
from ..repositories.permission_repository import PermissionRepository

logger = logging.getLogger(__name__)


class PermissionService(BaseBusinessService[Role, RoleCreate, RoleUpdate, RoleResponse]):
    """
    權限管理服務

    提供完整的權限管理功能，包括：
    - 角色定義和管理
    - 權限定義和分配
    - 資源訪問控制
    - 動態權限檢查
    """

    def __init__(
        self,
        permission_repo: PermissionRepository,
        cache_manager: CacheManager,
        validator: PermissionValidator,
        permission_checker: PermissionChecker,
        event_bus: EventBus
    ):
        super().__init__(
            repository=permission_repo,
            cache_manager=cache_manager,
            validator=validator,
            permission_checker=permission_checker,
            event_bus=event_bus,
            cache_prefix="permission",
            default_ttl=1800  # 30分鐘緩存
        )
        self.permission_repo = permission_repo

    def get_model_class(self):
        """獲取角色模型類"""
        return Role

    def get_response_schema(self):
        """獲取角色響應模式類"""
        return RoleResponse

    async def create_permission(
        self,
        request: PermissionCreate,
        creator_id: int
    ) -> PermissionResponse:
        """
        創建新權限

        Args:
            request: 權限創建請求
            creator_id: 創建者ID

        Returns:
            創建的權限響應
        """
        # 驗證權限唯一性
        if await self.permission_repo.permission_exists(
            request.resource_type,
            request.action,
            request.resource_pattern
        ):
            raise ValueError(f"權限已存在: {request.resource_type}:{request.action}")

        # 創建權限
        permission_id = f"perm_{request.resource_type.value}_{request.action.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        permission = Permission(
            id=permission_id,
            name=request.name,
            description=request.description,
            resource_type=request.resource_type,
            action=request.action,
            resource_pattern=request.resource_pattern,
            conditions=request.conditions,
            created_by=creator_id
        )

        # 保存到數據庫
        permission = await self.permission_repo.create_permission(permission)

        # 清除權限緩存
        await self._clear_permission_cache()

        # 觸發事件
        await self.events.emit("permission_created", {
            "permission_id": permission.id,
            "resource_type": permission.resource_type.value,
            "action": permission.action.value,
            "creator_id": creator_id
        })

        return PermissionResponse.model_validate(permission)

    async def grant_role_permission(
        self,
        role_id: str,
        permission_id: str,
        granter_id: int,
        conditions: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        授予角色權限

        Args:
            role_id: 角色ID
            permission_id: 權限ID
            granter_id: 授予者ID
            conditions: 附加條件
        """
        # 權限檢查
        await self.permission.check_permission_management(granter_id)

        # 檢查權限是否已存在
        if await self.permission_repo.role_has_permission(role_id, permission_id):
            raise ValueError(f"角色已具有該權限: {role_id} - {permission_id}")

        # 創建權限授予
        grant = PermissionGrant(
            role_id=role_id,
            permission_id=permission_id,
            granted_by=granter_id,
            granted_at=datetime.now(),
            conditions=conditions
        )

        # 保存授予
        await self.permission_repo.create_permission_grant(grant)

        # 清除緩存
        await self._clear_role_cache(role_id)
        await self._clear_permission_cache()

        # 觸發事件
        await self.events.emit("role_permission_granted", {
            "role_id": role_id,
            "permission_id": permission_id,
            "granter_id": granter_id
        })

    async def assign_user_role(
        self,
        user_id: str,
        role_id: str,
        assigner_id: int,
        expires_at: Optional[datetime] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        分配用戶角色

        Args:
            user_id: 用戶ID
            role_id: 角色ID
            assigner_id: 分配者ID
            expires_at: 過期時間
            context: 分配上下文
        """
        # 權限檢查
        await self.permission.check_role_assignment(assigner_id, role_id)

        # 檢查角色是否已分配
        if await self.permission_repo.user_has_role(user_id, role_id):
            raise ValueError(f"用戶已具有該角色: {user_id} - {role_id}")

        # 創建角色分配
        assignment = RoleAssignment(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigner_id,
            assigned_at=datetime.now(),
            expires_at=expires_at,
            context=context
        )

        # 保存分配
        await self.permission_repo.create_role_assignment(assignment)

        # 清除用戶權限緩存
        await self._clear_user_permission_cache(user_id)

        # 觸發事件
        await self.events.emit("user_role_assigned", {
            "user_id": user_id,
            "role_id": role_id,
            "assigner_id": assigner_id,
            "expires_at": expires_at
        })

    async def check_user_permission(
        self,
        user_id: str,
        resource_type: ResourceType,
        action: Action,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        檢查用戶權限

        Args:
            user_id: 用戶ID
            resource_type: 資源類型
            action: 操作
            resource_id: 資源ID（可選）
            context: 上下文信息

        Returns:
            是否有權限
        """
        # 構建緩存鍵
        cache_key = f"user_perm:{user_id}:{resource_type.value}:{action.value}:{resource_id}:{hash(str(context))}"

        # 嘗試從緩存獲取
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # 檢查權限
        has_permission = await self.permission_repo.check_user_permission(
            user_id, resource_type, action, resource_id, context
        )

        # 緩存結果（權限檢查結果緩存時間較短）
        await self.cache.set(cache_key, has_permission, ttl=60)  # 1分鐘緩存

        return has_permission

    async def get_user_permissions(
        self,
        user_id: str,
        resource_type: Optional[ResourceType] = None
    ) -> List[PermissionResponse]:
        """
        獲取用戶所有權限

        Args:
            user_id: 用戶ID
            resource_type: 資源類型過濾

        Returns:
            權限列表
        """
        # 檢查緩存
        cache_key = f"user_perms:{user_id}:{resource_type.value if resource_type else 'all'}"
        cached_permissions = await self.cache.get(cache_key)
        if cached_permissions:
            return cached_permissions

        # 獲取權限
        permissions = await self.permission_repo.get_user_permissions(user_id, resource_type)

        # 轉換為響應格式
        response = [PermissionResponse.model_validate(p) for p in permissions]

        # 緩存結果
        await self.cache.set(cache_key, response, ttl=300)  # 5分鐘緩存

        return response

    async def get_role_permissions(self, role_id: str) -> List[PermissionResponse]:
        """
        獲取角色所有權限

        Args:
            role_id: 角色ID

        Returns:
            權限列表
        """
        # 檢查緩存
        cache_key = f"role_perms:{role_id}"
        cached_permissions = await self.cache.get(cache_key)
        if cached_permissions:
            return cached_permissions

        # 獲取權限
        permissions = await self.permission_repo.get_role_permissions(role_id)

        # 轉換為響應格式
        response = [PermissionResponse.model_validate(p) for p in permissions]

        # 緩存結果
        await self.cache.set(cache_key, response, ttl=600)  # 10分鐘緩存

        return response

    async def create_role_hierarchy(
        self,
        parent_role_id: str,
        child_role_id: str,
        creator_id: int
    ) -> None:
        """
        創建角色層級關係

        Args:
            parent_role_id: 父角色ID
            child_role_id: 子角色ID
            creator_id: 創建者ID
        """
        # 檢查循環依賴
        if await self._would_create_cycle(parent_role_id, child_role_id):
            raise ValueError("創建角色層級會導致循環依賴")

        # 創建層級關係
        await self.permission_repo.create_role_hierarchy(parent_role_id, child_role_id, creator_id)

        # 清除角色權限緩存
        await self._clear_role_cache(child_role_id)

        # 觸發事件
        await self.events.emit("role_hierarchy_created", {
            "parent_role_id": parent_role_id,
            "child_role_id": child_role_id,
            "creator_id": creator_id
        })

    async def revoke_user_role(
        self,
        user_id: str,
        role_id: str,
        revoker_id: int,
        reason: Optional[str] = None
    ) -> None:
        """
        撤銷用戶角色

        Args:
            user_id: 用戶ID
            role_id: 角色ID
            revoker_id: 撤銷者ID
            reason: 撤銷原因
        """
        # 權限檢查
        await self.permission.check_role_assignment(revoker_id, role_id)

        # 撤銷角色
        await self.permission_repo.revoke_user_role(user_id, role_id)

        # 清除用戶權限緩存
        await self._clear_user_permission_cache(user_id)

        # 觸發事件
        await self.events.emit("user_role_revoked", {
            "user_id": user_id,
            "role_id": role_id,
            "revoker_id": revoker_id,
            "reason": reason
        })

    async def get_accessible_resources(
        self,
        user_id: str,
        resource_type: ResourceType,
        action: Action
    ) -> List[ResourceResponse]:
        """
        獲取用戶可訪問的資源列表

        Args:
            user_id: 用戶ID
            resource_type: 資源類型
            action: 操作類型

        Returns:
            可訪問的資源列表
        """
        # 檢查緩存
        cache_key = f"user_resources:{user_id}:{resource_type.value}:{action.value}"
        cached_resources = await self.cache.get(cache_key)
        if cached_resources:
            return cached_resources

        # 獲取可訪問資源
        resources = await self.permission_repo.get_accessible_resources(
            user_id, resource_type, action
        )

        # 轉換為響應格式
        response = [ResourceResponse.model_validate(r) for r in resources]

        # 緩存結果
        await self.cache.set(cache_key, response, ttl=180)  # 3分鐘緩存

        return response

    # 重寫基類方法
    async def _check_unique_constraints(self, request: RoleCreate, user_id: int) -> None:
        """檢查角色唯一性約束"""
        if await self.permission_repo.role_exists(request.name):
            raise ValueError(f"角色名稱已存在: {request.name}")

    async def _check_unique_constraints_on_update(
        self,
        request: RoleUpdate,
        item: Role
    ) -> None:
        """檢查更新時的唯一性約束"""
        if request.name and request.name != item.name:
            if await self.permission_repo.role_exists(request.name):
                raise ValueError(f"角色名稱已存在: {request.name}")

    async def _get_related_data(self, item: Role, user_id: Optional[int]) -> Dict[str, Any]:
        """獲取角色相關數據"""
        # 獲取角色權限
        permissions = await self.get_role_permissions(item.id)

        # 獲取角色層級
        hierarchy = await self.permission_repo.get_role_hierarchy(item.id)

        # 獲取角色用戶數
        user_count = await self.permission_repo.get_role_user_count(item.id)

        return {
            "permissions": permissions,
            "hierarchy": hierarchy,
            "user_count": user_count
        }

    # 輔助方法
    async def _would_create_cycle(self, parent_id: str, child_id: str) -> bool:
        """檢查是否會創建循環依賴"""
        # 簡化的循環檢查，實際實現可能需要更復雜的算法
        ancestors = await self.permission_repo.get_role_ancestors(parent_id)
        return child_id in ancestors

    async def _clear_permission_cache(self) -> None:
        """清除權限相關緩存"""
        patterns = [
            "permission:*",
            "user_perm:*",
            "role_perms:*"
        ]
        for pattern in patterns:
            await self.cache.clear_pattern(pattern)

    async def _clear_role_cache(self, role_id: str) -> None:
        """清除角色相關緩存"""
        patterns = [
            f"permission:detail:{role_id}:*",
            f"role_perms:{role_id}"
        ]
        for pattern in patterns:
            await self.cache.clear_pattern(pattern)

    async def _clear_user_permission_cache(self, user_id: str) -> None:
        """清除用戶權限緩存"""
        patterns = [
            f"user_perm:{user_id}:*",
            f"user_perms:{user_id}:*",
            f"user_resources:{user_id}:*"
        ]
        for pattern in patterns:
            await self.cache.clear_pattern(pattern)
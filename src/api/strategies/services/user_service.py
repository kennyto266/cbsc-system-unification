"""
用戶管理服務
User Management Service

基於BaseBusinessService實現的用戶管理服務，
提供完整的用戶生命周期管理功能。

職責：
- 用戶CRUD操作
- 用戶狀態管理
- 用戶偏好設置
- 用戶活動記錄
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from .base_business_service import BaseBusinessService
from ..models.user import User, UserStatus, UserRole
from ..schemas.user import (
    UserCreate, UserUpdate, UserResponse,
    UserPreferenceCreate, UserPreferenceUpdate,
    UserProfileResponse
)
from ..utils.validators import UserValidator
from ..utils.permissions import UserPermissionChecker
from ..utils.events import EventBus
from ..utils.cache import CacheManager
from ..repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserService(BaseBusinessService[User, UserCreate, UserUpdate, UserResponse]):
    """
    用戶管理服務

    提供完整的用戶管理功能，包括：
    - 用戶賬戶管理
    - 用戶狀態控制
    - 用戶偏好設置
    - 用戶活動追蹤
    """

    def __init__(
        self,
        user_repo: UserRepository,
        cache_manager: CacheManager,
        validator: UserValidator,
        permission_checker: UserPermissionChecker,
        event_bus: EventBus
    ):
        super().__init__(
            repository=user_repo,
            cache_manager=cache_manager,
            validator=validator,
            permission_checker=permission_checker,
            event_bus=event_bus,
            cache_prefix="user",
            default_ttl=600  # 10分鐘緩存
        )
        self.user_repo = user_repo

    def get_model_class(self):
        """獲取用戶模型類"""
        return User

    def get_response_schema(self):
        """獲取用戶響應模式類"""
        return UserResponse

    async def create_user_with_profile(
        self,
        request: UserCreate,
        creator_id: int
    ) -> UserResponse:
        """
        創建用戶並初始化個人資料

        Args:
            request: 用戶創建請求
            creator_id: 創建者ID

        Returns:
            創建的用戶響應
        """
        # 驗證郵箱唯一性
        if await self.user_repo.email_exists(request.email):
            raise ValueError(f"郵箱已存在: {request.email}")

        # 驗證用戶名唯一性
        if await self.user_repo.username_exists(request.username):
            raise ValueError(f"用戶名已存在: {request.username}")

        # 創建用戶
        user = await self.create_item(request, creator_id)

        # 初始化用戶偏好設置
        default_preferences = {
            "theme": "light",
            "language": "zh-CN",
            "timezone": "Asia/Shanghai",
            "email_notifications": True,
            "push_notifications": True
        }
        await self.update_user_preferences(user.id, default_preferences, user.id)

        # 觸發歡迎事件
        await self.events.emit("user_welcomed", {
            "user_id": user.id,
            "email": user.email
        })

        return user

    async def get_user_profile(
        self,
        user_id: str,
        viewer_id: Optional[int] = None
    ) -> UserProfileResponse:
        """
        獲取用戶完整個人資料

        Args:
            user_id: 用戶ID
            viewer_id: 查看者ID（用於權限檢查）

        Returns:
            用戶個人資料響應
        """
        # 檢查緩存
        cache_key = f"user:profile:{user_id}:{viewer_id}"
        cached_profile = await self.cache.get(cache_key)
        if cached_profile:
            return cached_profile

        # 獲取用戶基本信息
        item_data = await self.get_item(user_id, viewer_id)
        user = item_data["item"]

        # 獲取用戶偏好設置
        preferences = await self.user_repo.get_user_preferences(user_id)

        # 獲取用戶統計信息
        stats = await self._get_user_stats(user_id)

        # 獲取最近活動
        recent_activities = await self.user_repo.get_recent_activities(
            user_id, limit=10
        )

        # 構建響應
        profile = UserProfileResponse(
            **user.model_dump(),
            preferences=preferences or {},
            stats=stats,
            recent_activities=recent_activities
        )

        # 緩存結果
        await self.cache.set(cache_key, profile, ttl=300)  # 5分鐘緩存

        return profile

    async def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any],
        updater_id: int
    ) -> Dict[str, Any]:
        """
        更新用戶偏好設置

        Args:
            user_id: 用戶ID
            preferences: 偏好設置
            updater_id: 更新者ID

        Returns:
            更新後的偏好設置
        """
        # 權限檢查 - 用戶只能更新自己的偏好，管理員可以更新任何人
        user = await self.user_repo.get_by_id(user_id)
        if updater_id != int(user_id):
            updater = await self.user_repo.get_by_id(str(updater_id))
            if not updater or not updater.is_admin:
                raise PermissionError("無權限更新用戶偏好設置")

        # 更新偏好設置
        updated_preferences = await self.user_repo.update_user_preferences(
            user_id, preferences
        )

        # 清除緩存
        await self._clear_user_profile_cache(user_id)

        # 觸發事件
        await self.events.emit("user_preferences_updated", {
            "user_id": user_id,
            "preferences": preferences
        })

        return updated_preferences

    async def change_user_status(
        self,
        user_id: str,
        new_status: UserStatus,
        operator_id: int,
        reason: Optional[str] = None
    ) -> None:
        """
        變更用戶狀態

        Args:
            user_id: 用戶ID
            new_status: 新狀態
            operator_id: 操作者ID
            reason: 變更原因
        """
        # 獲取用戶
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"用戶不存在: {user_id}")

        # 權限檢查
        await self.permission.check_status_change_permission(operator_id, user, new_status)

        # 記錄狀態變更
        old_status = user.status
        user.status = new_status
        user.status_changed_at = datetime.now()
        user.status_reason = reason

        # 保存更新
        await self.user_repo.update(user)

        # 清除緩存
        await self._clear_item_cache(user_id)
        await self._clear_user_profile_cache(user_id)

        # 觸發事件
        await self.events.emit("user_status_changed", {
            "user_id": user_id,
            "old_status": old_status.value,
            "new_status": new_status.value,
            "operator_id": operator_id,
            "reason": reason
        })

        logger.info(f"用戶狀態變更: {user_id} {old_status.value} -> {new_status.value}")

    async def assign_user_role(
        self,
        user_id: str,
        role: UserRole,
        assigner_id: int,
        expires_at: Optional[datetime] = None
    ) -> None:
        """
        分配用戶角色

        Args:
            user_id: 用戶ID
            role: 角色
            assigner_id: 分配者ID
            expires_at: 過期時間（可選）
        """
        # 權限檢查
        await self.permission.check_role_assignment_permission(assigner_id, role)

        # 分配角色
        await self.user_repo.assign_role(user_id, role, expires_at)

        # 清除緩存
        await self._clear_item_cache(user_id)
        await self._clear_user_profile_cache(user_id)

        # 觸發事件
        await self.events.emit("user_role_assigned", {
            "user_id": user_id,
            "role": role.value,
            "assigner_id": assigner_id,
            "expires_at": expires_at
        })

    async def search_users(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        搜索用戶

        Args:
            query: 搜索關鍵詞
            page: 頁碼
            page_size: 每頁大小
            filters: 額外過濾條件

        Returns:
            搜索結果
        """
        # 構建緩存鍵
        cache_key = f"user:search:{query}:{page}:{page_size}:{hash(str(filters))}"

        # 嘗試從緩存獲取
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result

        # 執行搜索
        users, total_count = await self.user_repo.search_users(
            query=query,
            page=page,
            page_size=page_size,
            filters=filters or {}
        )

        # 轉換為響應格式
        result = {
            "users": [UserResponse.model_validate(user) for user in users],
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "query": query
        }

        # 緩存結果（搜索結果緩存時間較短）
        await self.cache.set(cache_key, result, ttl=60)  # 1分鐘緩存

        return result

    async def get_user_activity_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        獲取用戶活動摘要

        Args:
            user_id: 用戶ID
            days: 統計天數

        Returns:
            活動摘要
        """
        # 檢查緩存
        cache_key = f"user:activity:{user_id}:{days}"
        cached_summary = await self.cache.get(cache_key)
        if cached_summary:
            return cached_summary

        # 獲取活動數據
        summary = await self.user_repo.get_activity_summary(user_id, days)

        # 緩存結果
        await self.cache.set(cache_key, summary, ttl=300)  # 5分鐘緩存

        return summary

    # 重寫基類方法
    async def _check_unique_constraints(self, request: UserCreate, user_id: int) -> None:
        """檢查用戶唯一性約束"""
        if await self.user_repo.email_exists(request.email):
            raise ValueError(f"郵箱已存在: {request.email}")
        if await self.user_repo.username_exists(request.username):
            raise ValueError(f"用戶名已存在: {request.username}")

    async def _check_unique_constraints_on_update(
        self,
        request: UserUpdate,
        item: User
    ) -> None:
        """檢查更新時的唯一性約束"""
        if request.email and request.email != item.email:
            if await self.user_repo.email_exists(request.email):
                raise ValueError(f"郵箱已存在: {request.email}")
        if request.username and request.username != item.username:
            if await self.user_repo.username_exists(request.username):
                raise ValueError(f"用戶名已存在: {request.username}")

    async def _get_related_data(self, item: User, user_id: Optional[int]) -> Dict[str, Any]:
        """獲取用戶相關數據"""
        # 獲取用戶偏好設置
        preferences = await self.user_repo.get_user_preferences(item.id)

        # 獲取用戶角色
        roles = await self.user_repo.get_user_roles(item.id)

        return {
            "preferences": preferences or {},
            "roles": roles
        }

    async def _check_delete_preconditions(self, item: User) -> None:
        """檢查刪除前置條件"""
        # 檢查用戶是否有未完成的策略
        active_strategies = await self.user_repo.get_active_strategy_count(item.id)
        if active_strategies > 0:
            raise ValueError(f"用戶有 {active_strategies} 個活躍策略，無法刪除")

    # 輔助方法
    async def _get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """獲取用戶統計信息"""
        return await self.user_repo.get_user_stats(user_id)

    async def _clear_user_profile_cache(self, user_id: str) -> None:
        """清除用戶資料緩存"""
        patterns = [
            f"user:profile:{user_id}:*",
            f"user:activity:{user_id}:*"
        ]
        for pattern in patterns:
            await self.cache.clear_pattern(pattern)
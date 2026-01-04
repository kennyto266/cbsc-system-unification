"""
RBAC (Role-Based Access Control) Service
RBAC服務層

提供權限檢查、動態權限管理、臨時授權等功能。
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, not_, func
from fastapi import HTTPException, status
import logging

from ..models.rbac_models import (
    DynamicPermission, TemporaryAuthorization, PermissionAuditLog,
    PermissionLevel, ResourceAction, ResourceType,
    DynamicPermissionCreateSchema, TemporaryAuthorizationCreateSchema,
    PermissionCheckSchema, PermissionResultSchema
)
from ..models.user import User, Role, Permission
from ..core.logging import logger

# 配置日誌
logging.basicConfig(level=logging.INFO)
rbac_logger = logging.getLogger(__name__)


class RBACService:
    """RBAC服務類"""

    def __init__(self, db: Session):
        self.db = db
        self._permission_cache = {}  # 簡單的內存緩存，生產環境建議使用Redis

    async def check_permission(
        self,
        user: User,
        resource_type: ResourceType,
        action: ResourceAction,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> PermissionResultSchema:
        """
        檢查用戶權限

        Args:
            user: 用戶對象
            resource_type: 資源類型
            action: 操作類型
            resource_id: 資源ID（可選）
            context: 上下文信息（可選）

        Returns:
            PermissionResultSchema: 權限檢查結果
        """
        # 1. 檢查用戶狀態
        if not user.is_active:
            return PermissionResultSchema(
                granted=False,
                reason="用戶已被禁用",
                source="user_status"
            )

        # 2. 檢查賬戶鎖定
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            return PermissionResultSchema(
                granted=False,
                reason="用戶賬戶已被鎖定",
                source="account_locked"
            )

        # 3. 檢查臨時授權
        temp_auth_result = await self._check_temporary_authorization(
            user, resource_type, action, resource_id, context
        )
        if temp_auth_result.granted:
            return temp_auth_result

        # 4. 檢查動態權限
        dynamic_result = await self._check_dynamic_permissions(
            user, resource_type, action, resource_id, context
        )
        if dynamic_result.granted:
            return dynamic_result

        # 5. 檢查基礎角色權限
        role_result = await self._check_role_permissions(
            user, resource_type, action, resource_id, context
        )
        if role_result.granted:
            return role_result

        # 6. 所有權限檢查都失敗
        return PermissionResultSchema(
            granted=False,
            reason="沒有足夠的權限執行此操作",
            source="none"
        )

    async def _check_temporary_authorization(
        self,
        user: User,
        resource_type: ResourceType,
        action: ResourceAction,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> PermissionResultSchema:
        """檢查臨時授權"""
        now = datetime.now(timezone.utc)

        # 查詢有效的臨時授權
        temp_auths = self.db.query(TemporaryAuthorization).filter(
            and_(
                TemporaryAuthorization.user_id == user.id,
                TemporaryAuthorization.is_active == True,
                TemporaryAuthorization.is_revoked == False,
                TemporaryAuthorization.starts_at <= now,
                TemporaryAuthorization.expires_at > now
            )
        ).all()

        for temp_auth in temp_auths:
            # 檢查權限是否在授權範圍內
            permission_code = f"{resource_type.value}:{action.value}"
            if permission_code in temp_auth.permissions:
                # 檢查資源限制
                if temp_auth.resource_ids and resource_id:
                    if resource_id not in temp_auth.resource_ids:
                        continue

                # 更新使用統計
                temp_auth.usage_count += 1
                temp_auth.last_used_at = now
                self.db.commit()

                # 記錄審計日誌
                await self._log_permission_use(
                    user=user,
                    action="temp_auth_used",
                    resource_type=resource_type.value,
                    resource_id=resource_id,
                    details={
                        "temp_auth_id": temp_auth.id,
                        "permission": permission_code
                    }
                )

                return PermissionResultSchema(
                    granted=True,
                    source="temporary_authorization",
                    expires_at=temp_auth.expires_at
                )

        return PermissionResultSchema(
            granted=False,
            source="temporary_authorization"
        )

    async def _check_dynamic_permissions(
        self,
        user: User,
        resource_type: ResourceType,
        action: ResourceAction,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> PermissionResultSchema:
        """檢查動態權限"""
        now = datetime.now(timezone.utc)

        # 查詢用戶的直接動態權限
        user_permissions = self.db.query(DynamicPermission).filter(
            and_(
                DynamicPermission.user_id == user.id,
                DynamicPermission.resource_type == resource_type,
                DynamicPermission.action == action,
                DynamicPermission.is_active == True,
                or_(
                    DynamicPermission.valid_from.is_(None),
                    DynamicPermission.valid_from <= now
                ),
                or_(
                    DynamicPermission.valid_until.is_(None),
                    DynamicPermission.valid_until > now
                )
            )
        ).all()

        # 查詢通過角色授予的動態權限
        role_ids = [role.id for role in user.roles]
        role_permissions = self.db.query(DynamicPermission).filter(
            and_(
                DynamicPermission.role_id.in_(role_ids),
                DynamicPermission.resource_type == resource_type,
                DynamicPermission.action == action,
                DynamicPermission.is_active == True,
                or_(
                    DynamicPermission.valid_from.is_(None),
                    DynamicPermission.valid_from <= now
                ),
                or_(
                    DynamicPermission.valid_until.is_(None),
                    DynamicPermission.valid_until > now
                )
            )
        ).all()

        # 合並並檢查權限
        all_permissions = user_permissions + role_permissions
        for permission in all_permissions:
            # 檢查使用次數限制
            if permission.usage_limit and permission.usage_count >= permission.usage_limit:
                continue

            # 檢查條件
            if permission.conditions and not await self._evaluate_conditions(
                permission.conditions, user, resource_id, context
            ):
                continue

            # 檢查限制
            if permission.restrictions and await self._check_restrictions(
                permission.restrictions, user, resource_id, context
            ):
                continue

            # 更新使用次數
            permission.usage_count += 1
            self.db.commit()

            # 記錄審計日誌
            await self._log_permission_use(
                user=user,
                action="dynamic_permission_used",
                resource_type=resource_type.value,
                resource_id=resource_id,
                details={
                    "permission_id": permission.id,
                    "permission_name": permission.name
                }
            )

            return PermissionResultSchema(
                granted=True,
                source="dynamic_permission",
                conditions=permission.conditions,
                expires_at=permission.valid_until
            )

        return PermissionResultSchema(
            granted=False,
            source="dynamic_permission"
        )

    async def _check_role_permissions(
        self,
        user: User,
        resource_type: ResourceType,
        action: ResourceAction,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> PermissionResultSchema:
        """檢查基礎角色權限"""
        # 超級管理員擁有所有權限
        if user.has_permission("system:admin"):
            return PermissionResultSchema(
                granted=True,
                source="super_admin"
            )

        # 檢查特定權限
        permission_code = f"{resource_type.value}:{action.value}"

        # 資源所有者權限
        if resource_id and await self._check_resource_ownership(user, resource_type, resource_id):
            return PermissionResultSchema(
                granted=True,
                source="resource_owner"
            )

        # 檢查角色權限
        for role in user.roles:
            if role.has_permission(permission_code):
                return PermissionResultSchema(
                    granted=True,
                    source=f"role:{role.name}"
                )

        return PermissionResultSchema(
            granted=False,
            source="role_permission"
        )

    async def _check_resource_ownership(
        self,
        user: User,
        resource_type: ResourceType,
        resource_id: str
    ) -> bool:
        """檢查資源所有權"""
        # 根據資源類型查詢所有者
        if resource_type == ResourceType.STRATEGY:
            from ..models.strategy_models_v2 import Strategy
            strategy = self.db.query(Strategy).filter(
                Strategy.id == resource_id,
                Strategy.created_by == user.id
            ).first()
            return strategy is not None

        elif resource_type == ResourceType.BACKTEST:
            from ..models.backtest_models_v2 import Backtest
            backtest = self.db.query(Backtest).filter(
                Backtest.id == resource_id,
                Backtest.user_id == user.id
            ).first()
            return backtest is not None

        elif resource_type == ResourceType.PORTFOLIO:
            from ..models.trading_models_v2 import Portfolio
            portfolio = self.db.query(Portfolio).filter(
                Portfolio.id == resource_id,
                Portfolio.user_id == user.id
            ).first()
            return portfolio is not None

        return False

    async def _evaluate_conditions(
        self,
        conditions: Dict[str, Any],
        user: User,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """評估權限條件"""
        try:
            # 時間條件
            if "time_range" in conditions:
                time_range = conditions["time_range"]
                now = datetime.now(timezone.utc).hour
                if "start" in time_range and "end" in time_range:
                    if not (time_range["start"] <= now <= time_range["end"]):
                        return False

            # IP條件
            if "allowed_ips" in conditions and context:
                client_ip = context.get("ip_address")
                if client_ip and client_ip not in conditions["allowed_ips"]:
                    return False

            # 用戶屬性條件
            if "user_attributes" in conditions:
                attrs = conditions["user_attributes"]
                if "premium_only" in attrs and attrs["premium_only"] and not user.is_premium:
                    return False
                if "verified_only" in attrs and attrs["verified_only"] and not user.is_verified:
                    return False

            # 資源條件
            if "resource_conditions" in conditions and resource_id:
                resource_conditions = conditions["resource_conditions"]
                # 可以根據資源類型添加特定條件檢查
                pass

            return True
        except Exception as e:
            rbac_logger.error(f"Error evaluating conditions: {str(e)}")
            return False

    async def _check_restrictions(
        self,
        restrictions: Dict[str, Any],
        user: User,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """檢查權限限制"""
        # 返回True表示有限制（即權限被阻止）
        if "blocked_ips" in restrictions and context:
            client_ip = context.get("ip_address")
            if client_ip and client_ip in restrictions["blocked_ips"]:
                return True

        if "max_daily_usage" in restrictions:
            # 實現每日使用次數限制
            pass

        return False

    async def create_dynamic_permission(
        self,
        permission_data: DynamicPermissionCreateSchema,
        created_by: str
    ) -> DynamicPermission:
        """創建動態權限"""
        permission = DynamicPermission(
            **permission_data.dict(),
            created_by=created_by
        )
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)

        # 記錄審計日誌
        await self._log_permission_use(
            user=None,  # 系統操作
            action="dynamic_permission_created",
            resource_type=permission_data.resource_type.value,
            details={
                "permission_id": permission.id,
                "permission_name": permission.name
            }
        )

        return permission

    async def grant_temporary_authorization(
        self,
        auth_data: TemporaryAuthorizationCreateSchema,
        delegated_by: str
    ) -> TemporaryAuthorization:
        """授予臨時授權"""
        temp_auth = TemporaryAuthorization(
            **auth_data.dict(),
            delegated_by=delegated_by
        )
        self.db.add(temp_auth)
        self.db.commit()
        self.db.refresh(temp_auth)

        # 記錄審計日誌
        await self._log_permission_use(
            user=None,
            action="temporary_authorization_granted",
            resource_type="authorization",
            details={
                "temp_auth_id": temp_auth.id,
                "target_user": auth_data.user_id,
                "permissions": auth_data.permissions
            }
        )

        return temp_auth

    async def revoke_temporary_authorization(
        self,
        temp_auth_id: str,
        revoked_by: str
    ) -> bool:
        """撤銷臨時授權"""
        temp_auth = self.db.query(TemporaryAuthorization).filter(
            TemporaryAuthorization.id == temp_auth_id
        ).first()

        if not temp_auth:
            return False

        temp_auth.is_revoked = True
        temp_auth.revoked_at = datetime.now(timezone.utc)
        temp_auth.revoked_by = revoked_by
        self.db.commit()

        # 記錄審計日誌
        await self._log_permission_use(
            user=None,
            action="temporary_authorization_revoked",
            resource_type="authorization",
            details={
                "temp_auth_id": temp_auth_id,
                "revoked_by": revoked_by
            }
        )

        return True

    async def get_user_permissions(
        self,
        user_id: str,
        include_roles: bool = True
    ) -> Dict[str, Any]:
        """獲取用戶所有權限"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}

        permissions = {
            "static": [],
            "dynamic": [],
            "temporary": [],
            "roles": []
        }

        # 獲取角色權限
        if include_roles:
            for role in user.roles:
                if role.is_active:
                    permissions["roles"].append(role.name)
                    for perm in role.permissions:
                        if perm.is_active:
                            permissions["static"].append({
                                "code": perm.code,
                                "name": perm.name,
                                "resource": perm.resource,
                                "action": perm.action
                            })

        # 獲取動態權限
        dynamic_perms = self.db.query(DynamicPermission).filter(
            DynamicPermission.user_id == user_id,
            DynamicPermission.is_active == True
        ).all()
        for perm in dynamic_perms:
            permissions["dynamic"].append({
                "id": perm.id,
                "name": perm.name,
                "resource_type": perm.resource_type.value,
                "action": perm.action.value,
                "level": perm.level.value,
                "valid_until": perm.valid_until,
                "usage_limit": perm.usage_limit,
                "usage_count": perm.usage_count
            })

        # 獲取臨時授權
        temp_auths = self.db.query(TemporaryAuthorization).filter(
            and_(
                TemporaryAuthorization.user_id == user_id,
                TemporaryAuthorization.is_active == True,
                TemporaryAuthorization.is_revoked == False,
                TemporaryAuthorization.expires_at > datetime.now(timezone.utc)
            )
        ).all()
        for auth in temp_auths:
            permissions["temporary"].append({
                "id": auth.id,
                "reason": auth.reason,
                "permissions": auth.permissions,
                "expires_at": auth.expires_at,
                "usage_count": auth.usage_count
            })

        return permissions

    async def _log_permission_use(
        self,
        user: Optional[User],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """記錄權限使用審計日誌"""
        audit_log = PermissionAuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user.id if user else None,
            details=details,
            success=True
        )
        self.db.add(audit_log)
        self.db.commit()

    async def get_permission_audit_logs(
        self,
        query_params: Dict[str, Any]
    ) -> Tuple[List[PermissionAuditLog], int]:
        """獲取權限審計日誌"""
        query = self.db.query(PermissionAuditLog)

        # 應用過濾條件
        if query_params.get("user_id"):
            query = query.filter(PermissionAuditLog.user_id == query_params["user_id"])

        if query_params.get("action"):
            query = query.filter(PermissionAuditLog.action == query_params["action"])

        if query_params.get("resource_type"):
            query = query.filter(PermissionAuditLog.resource_type == query_params["resource_type"])

        if query_params.get("from_date"):
            query = query.filter(PermissionAuditLog.created_at >= query_params["from_date"])

        if query_params.get("to_date"):
            query = query.filter(PermissionAuditLog.created_at <= query_params["to_date"])

        # 獲取總數
        total = query.count()

        # 應用分頁
        page = query_params.get("page", 1)
        limit = query_params.get("limit", 50)
        offset = (page - 1) * limit

        logs = query.order_by(PermissionAuditLog.created_at.desc()).offset(offset).limit(limit).all()

        return logs, total

    def clear_permission_cache(self, user_id: Optional[str] = None):
        """清除權限緩存"""
        if user_id:
            self._permission_cache.pop(user_id, None)
        else:
            self._permission_cache.clear()


# FastAPI依賴注入函數
def get_rbac_service(db: Session) -> RBACService:
    """獲取RBAC服務實例"""
    return RBACService(db)
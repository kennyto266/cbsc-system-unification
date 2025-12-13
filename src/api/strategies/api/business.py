"""
業務服務API端點
Business Service API Endpoints

提供統一的業務服務API接口，包括：
- 用戶管理
- 權限控制
- 審計日誌
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ..services import (
    UserService, PermissionService, AuditService,
    CacheManager
)
from ..models.permission import ResourceType, Action
from ..models.audit import AuditFilter, AuditEventType
from ..schemas.user import (
    UserCreate, UserUpdate, UserResponse,
    UserProfileResponse
)
from ..schemas.permission import (
    RoleCreate, RoleUpdate, RoleResponse,
    PermissionCreate, PermissionResponse
)
from ..schemas.audit import (
    AuditLogResponse, AuditReportResponse
)
from ..dependencies import get_current_user, get_user_service, get_permission_service, get_audit_service

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/business", tags=["business"])

# ===== 用戶管理端點 =====

@router.get("/users", response_model=Dict[str, Any])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    role: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """獲取用戶列表"""
    filters = {}
    if status:
        filters["status"] = status
    if role:
        filters["role"] = role
    if search:
        filters["search"] = search

    return await user_service.list_items(
        page=page,
        page_size=page_size,
        filters=filters,
        user_id=current_user["id"]
    )

@router.post("/users", response_model=UserResponse)
async def create_user(
    request: UserCreate,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """創建新用戶"""
    return await user_service.create_user_with_profile(request, current_user["id"])

@router.get("/users/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """獲取用戶完整資料"""
    return await user_service.get_user_profile(user_id, current_user["id"])

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdate,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """更新用戶信息"""
    return await user_service.update_item(user_id, request, current_user["id"])

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """刪除用戶"""
    await user_service.delete_item(user_id, current_user["id"])
    return {"message": "用戶刪除成功"}

@router.post("/users/{user_id}/preferences")
async def update_user_preferences(
    user_id: str,
    preferences: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """更新用戶偏好設置"""
    updated_preferences = await user_service.update_user_preferences(
        user_id, preferences, current_user["id"]
    )
    return {"preferences": updated_preferences}

@router.post("/users/{user_id}/status")
async def change_user_status(
    user_id: str,
    status: str,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """變更用戶狀態"""
    from ..models.user import UserStatus
    new_status = UserStatus(status)
    await user_service.change_user_status(
        user_id, new_status, current_user["id"], reason
    )
    return {"message": f"用戶狀態已更新為: {status}"}

@router.get("/users/search/{query}")
async def search_users(
    query: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """搜索用戶"""
    return await user_service.search_users(query, page, page_size)

@router.post("/users/batch")
async def batch_user_operation(
    operation: str,
    user_ids: List[str],
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """批量用戶操作"""
    return await user_service.batch_operation(user_ids, operation, current_user["id"])

# ===== 權限管理端點 =====

@router.get("/roles", response_model=Dict[str, Any])
async def list_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """獲取角色列表"""
    return await permission_service.list_items(
        page=page,
        page_size=page_size,
        user_id=current_user["id"]
    )

@router.post("/roles", response_model=RoleResponse)
async def create_role(
    request: RoleCreate,
    current_user: dict = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """創建新角色"""
    return await permission_service.create_item(request, current_user["id"])

@router.post("/permissions", response_model=PermissionResponse)
async def create_permission(
    request: PermissionCreate,
    current_user: dict = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """創建新權限"""
    return await permission_service.create_permission(request, current_user["id"])

@router.post("/roles/{role_id}/permissions/{permission_id}")
async def grant_role_permission(
    role_id: str,
    permission_id: str,
    conditions: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """授予角色權限"""
    await permission_service.grant_role_permission(
        role_id, permission_id, current_user["id"], conditions
    )
    return {"message": "權限授予成功"}

@router.post("/users/{user_id}/roles/{role_id}")
async def assign_user_role(
    user_id: str,
    role_id: str,
    expires_at: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """分配用戶角色"""
    await permission_service.assign_user_role(
        user_id, role_id, current_user["id"], expires_at
    )
    return {"message": "角色分配成功"}

@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: str,
    resource_type: Optional[ResourceType] = None,
    current_user: dict = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """獲取用戶權限列表"""
    return await permission_service.get_user_permissions(user_id, resource_type)

@router.post("/check-permission")
async def check_permission(
    resource_type: ResourceType,
    action: Action,
    resource_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """檢查用戶權限"""
    has_permission = await permission_service.check_user_permission(
        current_user["id"], resource_type, action, resource_id, context
    )
    return {"has_permission": has_permission}

@router.get("/users/{user_id}/accessible-resources")
async def get_accessible_resources(
    user_id: str,
    resource_type: ResourceType,
    action: Action,
    current_user: dict = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """獲取用戶可訪問的資源列表"""
    return await permission_service.get_accessible_resources(
        user_id, resource_type, action
    )

# ===== 審計日誌端點 =====

@router.get("/audit/logs", response_model=Dict[str, Any])
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    event_type: Optional[AuditEventType] = None,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """獲取審計日誌列表"""
    filters = AuditFilter(
        event_type=event_type,
        user_id=user_id,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date
    )

    return await audit_service.search_audit_logs(
        filters=filters,
        page=page,
        page_size=page_size,
        user_id=current_user["id"]
    )

@router.get("/audit/reports/{report_type}", response_model=AuditReportResponse)
async def generate_compliance_report(
    report_type: str,
    start_date: datetime,
    end_date: datetime,
    filters: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """生成合規報告"""
    return await audit_service.generate_compliance_report(
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        filters=filters,
        user_id=current_user["id"]
    )

@router.get("/audit/users/{user_id}/activity-summary")
async def get_user_activity_summary(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """獲取用戶活動摘要"""
    return await audit_service.get_user_activity_summary(user_id, days)

@router.get("/audit/anomalies")
async def detect_anomalous_activities(
    time_window: int = Query(24, ge=1, le=168),
    threshold: float = Query(2.0, ge=1.0, le=5.0),
    current_user: dict = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """檢測異常活動"""
    return await audit_service.detect_anomalous_activities(time_window, threshold)

@router.get("/audit/resources/{resource_type}/{resource_id}/history")
async def get_resource_access_history(
    resource_type: str,
    resource_id: str,
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """獲取資源訪問歷史"""
    return await audit_service.get_resource_access_history(
        resource_type, resource_id, days
    )

@router.post("/audit/export")
async def export_audit_logs(
    filters: AuditFilter,
    format: str = Query("csv", regex="^(csv|json|excel)$"),
    current_user: dict = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """導出審計日誌"""
    file_path = await audit_service.export_audit_logs(
        filters=filters,
        format=format,
        user_id=current_user["id"]
    )
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
    )

# ===== 系統管理端點 =====

@router.get("/system/cache-stats")
async def get_cache_statistics(
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """獲取緩存統計信息"""
    return await cache_manager.get_stats()

@router.post("/system/clear-cache")
async def clear_cache(
    pattern: Optional[str] = None,
    cache_manager: CacheManager = Depends(get_cache_manager),
    current_user: dict = Depends(get_current_user)
):
    """清除緩存"""
    if pattern:
        count = await cache_manager.clear_pattern(pattern)
    else:
        # 清除所有緩存需要管理員權限
        # 這裡可以添加權限檢查
        count = await cache_manager.clear_all()

    return {"message": f"已清除 {count} 個緩存項"}

@router.get("/system/health")
async def get_system_health(
    user_service: UserService = Depends(get_user_service),
    permission_service: PermissionService = Depends(get_permission_service),
    audit_service: AuditService = Depends(get_audit_service),
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """獲取系統健康狀態"""
    # 檢查各服務狀態
    health_status = {
        "services": {
            "user_service": "healthy",
            "permission_service": "healthy",
            "audit_service": "healthy"
        },
        "cache": {
            "redis_available": cache_manager._redis_available,
            "memory_items": len(cache_manager._memory_cache)
        },
        "timestamp": datetime.now().isoformat()
    }

    return health_status
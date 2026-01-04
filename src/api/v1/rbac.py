"""
RBAC (Role-Based Access Control) API Routes
RBAC API路由

提供角色、權限、動態權限和臨時授權的管理接口。
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from datetime import datetime

from src.models.user import User, Role, Permission
from src.models.rbac_models import (
    DynamicPermission, TemporaryAuthorization, PermissionAuditLog,
    DynamicPermissionCreateSchema, DynamicPermissionUpdateSchema,
    TemporaryAuthorizationCreateSchema,
    PermissionCheckSchema, PermissionResultSchema,
    AuditLogQuerySchema, AuditLogResponseSchema
)
from src.dependencies import (
    get_db, get_current_user, get_rbac_service,
    require_admin, permission_required, role_required
)
from src.services.rbac_service import RBACService
from src.core.logging import logger

router = APIRouter()

# =============== Role Management ===============

@router.get("/roles", response_model=List[dict])
async def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    獲取角色列表
    """
    query = select(Role)

    if not include_inactive:
        query = query.where(Role.is_active == True)

    result = await db.execute(query.offset(skip).limit(limit))
    roles = result.scalars().all()

    # Format response with additional info
    role_list = []
    for role in roles:
        role_data = {
            "id": role.id,
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description,
            "level": role.level,
            "is_active": role.is_active,
            "is_system_role": role.is_system_role,
            "user_count": len(role.users) if role.users else 0,
            "permission_count": len(role.permissions) if role.permissions else 0,
            "created_at": role.created_at,
            "updated_at": role.updated_at
        }
        role_list.append(role_data)

    return role_list


@router.post("/roles", response_model=dict)
async def create_role(
    role_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    創建新角色
    """
    # Check if role name already exists
    result = await db.execute(select(Role).filter(Role.name == role_data["name"]))
    existing_role = result.scalar_one_or_none()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role name already exists"
        )

    # Create new role
    role = Role(
        name=role_data["name"],
        display_name=role_data["display_name"],
        description=role_data.get("description"),
        level=role_data.get("level", 0),
        is_active=role_data.get("is_active", True)
    )

    db.add(role)
    await db.commit()
    await db.refresh(role)

    logger.info(f"Role created: {role.name} by user {current_user.id}")

    return {
        "id": role.id,
        "name": role.name,
        "display_name": role.display_name,
        "message": "Role created successfully"
    }


@router.get("/roles/{role_id}", response_model=dict)
async def get_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    獲取角色詳情
    """
    result = await db.execute(select(Role).filter(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Get role permissions
    permissions = []
    for perm in role.permissions:
        permissions.append({
            "id": perm.id,
            "code": perm.code,
            "name": perm.name,
            "category": perm.category,
            "resource": perm.resource,
            "action": perm.action
        })

    # Get users with this role
    users = []
    for user in role.users:
        users.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "is_active": user.is_active
        })

    return {
        "id": role.id,
        "name": role.name,
        "display_name": role.display_name,
        "description": role.description,
        "level": role.level,
        "is_active": role.is_active,
        "is_system_role": role.is_system_role,
        "permissions": permissions,
        "users": users,
        "created_at": role.created_at,
        "updated_at": role.updated_at
    }


@router.put("/roles/{role_id}", response_model=dict)
async def update_role(
    role_id: str,
    role_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    更新角色
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Cannot modify system roles
    if role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify system roles"
        )

    # Update role fields
    if "display_name" in role_data:
        role.display_name = role_data["display_name"]
    if "description" in role_data:
        role.description = role_data["description"]
    if "level" in role_data:
        role.level = role_data["level"]
    if "is_active" in role_data:
        role.is_active = role_data["is_active"]

    db.commit()
    db.refresh(role)

    logger.info(f"Role updated: {role.name} by user {current_user.id}")

    return {
        "id": role.id,
        "name": role.name,
        "message": "Role updated successfully"
    }


@router.delete("/roles/{role_id}", response_model=dict)
async def delete_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    刪除角色
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Cannot delete system roles
    if role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system roles"
        )

    # Check if role has users
    if role.users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete role with assigned users"
        )

    db.delete(role)
    db.commit()

    logger.info(f"Role deleted: {role.name} by user {current_user.id}")

    return {"message": "Role deleted successfully"}


@router.post("/roles/{role_id}/permissions", response_model=dict)
async def assign_permission_to_role(
    role_id: str,
    permission_ids: List[str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    為角色分配權限
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Get permissions
    permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
    if len(permissions) != len(permission_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more permissions not found"
        )

    # Assign permissions to role
    for permission in permissions:
        if permission not in role.permissions:
            role.permissions.append(permission)

    db.commit()

    logger.info(f"Permissions assigned to role {role.name} by user {current_user.id}")

    return {
        "role_id": role.id,
        "role_name": role.name,
        "assigned_permissions": len(permissions),
        "message": "Permissions assigned successfully"
    }


@router.delete("/roles/{role_id}/permissions/{permission_id}", response_model=dict)
async def remove_permission_from_role(
    role_id: str,
    permission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    從角色移除權限
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )

    if permission in role.permissions:
        role.permissions.remove(permission)
        db.commit()

        logger.info(f"Permission removed from role {role.name} by user {current_user.id}")

    return {
        "role_id": role.id,
        "permission_id": permission_id,
        "message": "Permission removed from role successfully"
    }


# =============== Dynamic Permissions ===============

@router.get("/dynamic-permissions", response_model=List[dict])
async def list_dynamic_permissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    role_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    獲取動態權限列表
    """
    query = db.query(DynamicPermission)

    if user_id:
        query = query.filter(DynamicPermission.user_id == user_id)
    if role_id:
        query = query.filter(DynamicPermission.role_id == role_id)
    if resource_type:
        query = query.filter(DynamicPermission.resource_type == resource_type)

    permissions = query.offset(skip).limit(limit).all()

    # Format response
    permission_list = []
    for perm in permissions:
        permission_data = {
            "id": perm.id,
            "name": perm.name,
            "description": perm.description,
            "resource_type": perm.resource_type.value,
            "action": perm.action.value,
            "level": perm.level.value,
            "user_id": perm.user_id,
            "role_id": perm.role_id,
            "is_active": perm.is_active,
            "usage_limit": perm.usage_limit,
            "usage_count": perm.usage_count,
            "valid_from": perm.valid_from,
            "valid_until": perm.valid_until,
            "created_at": perm.created_at
        }
        permission_list.append(permission_data)

    return permission_list


@router.post("/dynamic-permissions", response_model=dict)
async def create_dynamic_permission(
    permission_data: DynamicPermissionCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """
    創建動態權限
    """
    # Validate user or role exists
    if permission_data.user_id:
        user = db.query(User).filter(User.id == permission_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    elif permission_data.role_id:
        role = db.query(Role).filter(Role.id == permission_data.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify either user_id or role_id"
        )

    # Create permission
    permission = await rbac_service.create_dynamic_permission(
        permission_data=permission_data,
        created_by=current_user.id
    )

    logger.info(f"Dynamic permission created: {permission.name} by user {current_user.id}")

    return {
        "id": permission.id,
        "name": permission.name,
        "message": "Dynamic permission created successfully"
    }


@router.put("/dynamic-permissions/{permission_id}", response_model=dict)
async def update_dynamic_permission(
    permission_id: str,
    permission_data: DynamicPermissionUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    更新動態權限
    """
    permission = db.query(DynamicPermission).filter(
        DynamicPermission.id == permission_id
    ).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dynamic permission not found"
        )

    # Update fields
    update_data = permission_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(permission, field, value)

    db.commit()
    db.refresh(permission)

    logger.info(f"Dynamic permission updated: {permission.name} by user {current_user.id}")

    return {
        "id": permission.id,
        "message": "Dynamic permission updated successfully"
    }


@router.delete("/dynamic-permissions/{permission_id}", response_model=dict)
async def delete_dynamic_permission(
    permission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    刪除動態權限
    """
    permission = db.query(DynamicPermission).filter(
        DynamicPermission.id == permission_id
    ).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dynamic permission not found"
        )

    db.delete(permission)
    db.commit()

    logger.info(f"Dynamic permission deleted: {permission.name} by user {current_user.id}")

    return {"message": "Dynamic permission deleted successfully"}


# =============== Temporary Authorizations ===============

@router.get("/temporary-authorizations", response_model=List[dict])
async def list_temporary_authorizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    delegated_by: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    獲取臨時授權列表
    """
    query = db.query(TemporaryAuthorization)

    if user_id:
        query = query.filter(TemporaryAuthorization.user_id == user_id)
    if delegated_by:
        query = query.filter(TemporaryAuthorization.delegated_by == delegated_by)
    if active_only:
        now = datetime.utcnow()
        query = query.filter(
            and_(
                TemporaryAuthorization.is_active == True,
                TemporaryAuthorization.is_revoked == False,
                TemporaryAuthorization.expires_at > now
            )
        )

    authorizations = query.offset(skip).limit(limit).all()

    # Format response
    auth_list = []
    for auth in authorizations:
        # Get user info
        user = db.query(User).filter(User.id == auth.user_id).first()
        delegator = db.query(User).filter(User.id == auth.delegated_by).first()

        auth_data = {
            "id": auth.id,
            "user_id": auth.user_id,
            "user_name": user.username if user else "Unknown",
            "delegated_by": auth.delegated_by,
            "delegator_name": delegator.username if delegator else "Unknown",
            "reason": auth.reason,
            "permissions": auth.permissions,
            "starts_at": auth.starts_at,
            "expires_at": auth.expires_at,
            "is_active": auth.is_active,
            "is_revoked": auth.is_revoked,
            "usage_count": auth.usage_count,
            "last_used_at": auth.last_used_at,
            "created_at": auth.created_at
        }
        auth_list.append(auth_data)

    return auth_list


@router.post("/temporary-authorizations", response_model=dict)
async def grant_temporary_authorization(
    auth_data: TemporaryAuthorizationCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """
    授予臨時授權
    """
    # Validate target user exists
    target_user = db.query(User).filter(User.id == auth_data.user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found"
        )

    # Cannot grant to yourself
    if auth_data.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot grant temporary authorization to yourself"
        )

    # Grant authorization
    temp_auth = await rbac_service.grant_temporary_authorization(
        auth_data=auth_data,
        delegated_by=current_user.id
    )

    logger.info(
        f"Temporary authorization granted to user {auth_data.user_id} "
        f"by {current_user.id}"
    )

    return {
        "id": temp_auth.id,
        "user_id": temp_auth.user_id,
        "expires_at": temp_auth.expires_at,
        "message": "Temporary authorization granted successfully"
    }


@router.post("/temporary-authorizations/{auth_id}/revoke", response_model=dict)
async def revoke_temporary_authorization(
    auth_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """
    撤銷臨時授權
    """
    success = await rbac_service.revoke_temporary_authorization(
        temp_auth_id=auth_id,
        revoked_by=current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Temporary authorization not found"
        )

    logger.info(f"Temporary authorization {auth_id} revoked by {current_user.id}")

    return {"message": "Temporary authorization revoked successfully"}


# =============== User Permissions ===============

@router.get("/users/{user_id}/permissions", response_model=dict)
async def get_user_permissions(
    user_id: str,
    include_roles: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """
    獲取用戶權限（用戶只能查看自己的權限，管理員可以查看所有用戶）
    """
    # Check permission - users can only view their own permissions unless they're admin
    if user_id != current_user.id and not any(role.name in ['admin', 'super_admin'] for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own permissions"
        )

    # Validate user exists
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get permissions
    permissions = await rbac_service.get_user_permissions(
        user_id=user_id,
        include_roles=include_roles
    )

    return {
        "user_id": user_id,
        "user_name": target_user.username,
        "permissions": permissions
    }


@router.post("/check-permission", response_model=PermissionResultSchema)
async def check_user_permission(
    permission_check: PermissionCheckSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service),
    request: Request = None
):
    """
    檢查當前用戶權限
    """
    context = {
        'ip_address': request.client.host if request else None,
        'user_agent': request.headers.get('user-agent') if request else None,
        'endpoint': str(request.url) if request else None
    }

    if permission_check.context:
        context.update(permission_check.context)

    result = await rbac_service.check_permission(
        user=current_user,
        resource_type=permission_check.resource_type,
        action=permission_check.action,
        resource_id=permission_check.resource_id,
        context=context
    )

    return result


# =============== Audit Logs ===============

@router.get("/audit-logs", response_model=dict)
async def get_permission_audit_logs(
    query_params: AuditLogQuerySchema = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """
    獲取權限審計日誌
    """
    logs, total = await rbac_service.get_permission_audit_logs(
        query_params.dict(exclude_unset=True)
    )

    # Format response
    log_list = []
    for log in logs:
        log_data = {
            "id": log.id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "user_id": log.user_id,
            "target_user_id": log.target_user_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "success": log.success,
            "reason": log.reason,
            "created_at": log.created_at
        }
        log_list.append(log_data)

    return {
        "logs": log_list,
        "total": total,
        "page": query_params.page,
        "limit": query_params.limit
    }


# =============== Role Assignment ===============

@router.post("/users/{user_id}/roles/{role_id}", response_model=dict)
async def assign_role_to_user(
    user_id: str,
    role_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    為用戶分配角色
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Assign role if not already assigned
    if role not in user.roles:
        user.roles.append(role)
        db.commit()

        logger.info(f"Role {role.name} assigned to user {user.username} by {current_user.id}")

    return {
        "user_id": user_id,
        "role_id": role_id,
        "message": "Role assigned to user successfully"
    }


@router.delete("/users/{user_id}/roles/{role_id}", response_model=dict)
async def remove_role_from_user(
    user_id: str,
    role_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    從用戶移除角色
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Remove role if assigned
    if role in user.roles:
        user.roles.remove(role)
        db.commit()

        logger.info(f"Role {role.name} removed from user {user.username} by {current_user.id}")

    return {
        "user_id": user_id,
        "role_id": role_id,
        "message": "Role removed from user successfully"
    }


@router.get("/users/{user_id}/roles", response_model=List[dict])
async def get_user_roles(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取用戶角色
    """
    # Users can only view their own roles unless they're admin
    if user_id != current_user.id and not any(role.name in ['admin', 'super_admin'] for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own roles"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    roles = []
    for role in user.roles:
        roles.append({
            "id": role.id,
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description,
            "level": role.level,
            "is_system_role": role.is_system_role
        })

    return roles
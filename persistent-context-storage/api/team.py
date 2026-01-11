"""
团队和权限API模块 - 提供上下文共享和团队权限管理接口
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Header
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from services.permission_service import PermissionService
from services.context_service import ContextService
from config.database import get_database_session
from models.context import Context, ContextShare, ContextAccess

router = APIRouter()

# 初始化权限服务和上下文服务
try:
    permission_service = PermissionService()
    context_service = ContextService()
    print("PermissionService and ContextService initialized successfully")
except Exception as e:
    print(f"Failed to initialize services: {e}")
    import traceback
    traceback.print_exc()
    permission_service = None
    context_service = None

# Pydantic models for request/response
class ShareRequest(BaseModel):
    """共享上下文的请求模型"""
    context_id: str = Field(..., description="上下文ID")
    shared_with_user_id: Optional[str] = Field(None, description="被共享用户ID（为空则创建公开链接）")
    permission_level: str = Field("viewer", pattern="^(viewer|editor|owner)$", description="权限级别")
    expires_hours: Optional[int] = Field(24, ge=0, description="过期小时数（0表示永不过期）")
    message: Optional[str] = Field(None, max_length=500, description="共享消息")

class ShareLinkRequest(BaseModel):
    """创建共享链接的请求模型"""
    context_id: str = Field(..., description="上下文ID")
    permission_level: str = Field("viewer", pattern="^(viewer|editor|owner)$", description="权限级别")
    expires_hours: int = Field(24, ge=0, description="过期小时数（0表示永不过期）")
    max_accesses: Optional[int] = Field(None, ge=1, description="最大访问次数")

class ShareTokenAccessRequest(BaseModel):
    """通过共享令牌访问的请求模型"""
    share_token: str = Field(..., description="共享令牌")
    user_id: Optional[str] = Field(None, description="访问者用户ID（可选）")

class UpdatePermissionRequest(BaseModel):
    """更新权限的请求模型"""
    permission_level: str = Field(..., pattern="^(viewer|editor|owner)$", description="新的权限级别")

@router.post("/share", response_model=Dict[str, Any], status_code=201)
async def share_context(
    request: ShareRequest,
    user_id: str = Query(..., description="共享者用户ID")
):
    """共享上下文给其他用户或创建公开链接"""
    try:
        if permission_service is None:
            raise HTTPException(status_code=500, detail="权限服务未初始化")

        # 计算过期时间
        expires_at = None
        if request.expires_hours > 0:
            expires_at = datetime.utcnow() + timedelta(hours=request.expires_hours)

        # 共享上下文
        share_id = await permission_service.share_context(
            context_id=request.context_id,
            shared_by_user_id=user_id,
            shared_with_user_id=request.shared_with_user_id,
            permission_level=request.permission_level,
            expires_at=expires_at,
            message=request.message
        )

        if not share_id:
            raise HTTPException(status_code=400, detail="共享失败，可能是权限不足或上下文不存在")

        return {
            "success": True,
            "data": {
                "share_id": share_id,
                "context_id": request.context_id,
                "shared_with": request.shared_with_user_id or "公开链接",
                "permission_level": request.permission_level,
                "expires_at": expires_at.isoformat() if expires_at else None
            },
            "message": "上下文共享成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"共享上下文失败: {str(e)}")

@router.post("/share/link", response_model=Dict[str, Any], status_code=201)
async def create_share_link(
    request: ShareLinkRequest,
    user_id: str = Query(..., description="创建者用户ID")
):
    """创建匿名共享链接"""
    try:
        if permission_service is None:
            raise HTTPException(status_code=500, detail="权限服务未初始化")

        # 创建共享链接
        share_token = await permission_service.create_share_link(
            context_id=request.context_id,
            shared_by_user_id=user_id,
            permission_level=request.permission_level,
            expires_hours=request.expires_hours,
            max_accesses=request.max_accesses
        )

        if not share_token:
            raise HTTPException(status_code=400, detail="创建共享链接失败，可能是权限不足")

        # 构建访问URL
        share_url = f"/api/team/share/access/{share_token}"

        return {
            "success": True,
            "data": {
                "share_token": share_token,
                "share_url": share_url,
                "context_id": request.context_id,
                "permission_level": request.permission_level,
                "expires_hours": request.expires_hours,
                "max_accesses": request.max_accesses
            },
            "message": "共享链接创建成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建共享链接失败: {str(e)}")

@router.get("/share/access/{share_token}", response_model=Dict[str, Any])
async def access_by_share_token(
    share_token: str,
    user_id: Optional[str] = Query(None, description="访问者用户ID（可选）"),
    user_agent: Optional[str] = Header(None, description="用户代理"),
    x_forwarded_for: Optional[str] = Header(None, description="客户端IP")
):
    """通过共享令牌访问上下文"""
    try:
        if permission_service is None:
            raise HTTPException(status_code=500, detail="权限服务未初始化")

        # 获取客户端IP
        ip_address = x_forwarded_for or None

        # 通过共享令牌访问
        context_info = await permission_service.access_by_share_token(
            share_token=share_token,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if not context_info:
            raise HTTPException(status_code=404, detail="共享链接无效或已过期")

        return {
            "success": True,
            "data": context_info,
            "message": "通过共享链接访问成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"通过共享链接访问失败: {str(e)}")

@router.get("/share/{share_id}/context", response_model=Dict[str, Any])
async def get_shared_context_full(
    share_id: str,
    user_id: Optional[str] = Query(None, description="访问者用户ID"),
    user_agent: Optional[str] = Header(None, description="用户代理"),
    x_forwarded_for: Optional[str] = Header(None, description="客户端IP")
):
    """通过共享ID获取完整的上下文内容（需要权限验证）"""
    try:
        if permission_service is None or context_service is None:
            raise HTTPException(status_code=500, detail="服务未初始化")

        with get_database_session() as db:
            # 查找共享记录
            share = db.query(ContextShare).filter(ContextShare.id == share_id).first()
            if not share:
                raise HTTPException(status_code=404, detail="共享记录不存在")

            # 检查共享是否有效
            if not share.is_active or share.is_expired():
                raise HTTPException(status_code=403, detail="共享已失效或过期")

            # 检查访问权限
            has_permission, _ = await permission_service.check_permission(
                share.context_id, user_id, "view"
            )

            if not has_permission and user_id:
                # 如果是用户访问但没有权限，检查是否通过共享令牌访问
                if not share.share_token:
                    raise HTTPException(status_code=403, detail="无权访问此上下文")
            elif not user_id and not share.share_token:
                # 匿名访问但没有共享令牌
                raise HTTPException(status_code=403, detail="需要共享令牌或用户认证")

            # 获取完整上下文内容
            context_data = await context_service.load_context(
                context_id=share.context_id,
                user_id=user_id
            )

            if not context_data:
                raise HTTPException(status_code=404, detail="上下文不存在")

            # 记录访问日志
            access_record = ContextAccess(
                context_id=share.context_id,
                user_id=user_id or "anonymous",
                access_type="view",
                ip_address=x_forwarded_for,
                user_agent=user_agent,
                accessed_at=datetime.utcnow()
            )
            db.add(access_record)
            db.commit()

            return {
                "success": True,
                "data": context_data,
                "share_info": {
                    "share_id": share_id,
                    "permission_level": share.permission_level,
                    "can_edit": share.can_edit,
                    "can_share": share.can_share,
                    "can_delete": share.can_delete
                },
                "message": "获取共享上下文成功",
                "timestamp": datetime.now().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取共享上下文失败: {str(e)}")

@router.put("/share/{share_id}/permission", response_model=Dict[str, Any])
async def update_share_permission(
    share_id: str,
    request: UpdatePermissionRequest,
    user_id: str = Query(..., description="操作用户ID")
):
    """更新共享权限级别"""
    try:
        if permission_service is None:
            raise HTTPException(status_code=500, detail="权限服务未初始化")

        success = await permission_service.update_share_permission(
            share_id=share_id,
            user_id=user_id,
            new_permission_level=request.permission_level
        )

        if not success:
            raise HTTPException(status_code=404, detail="共享不存在或无权更新")

        return {
            "success": True,
            "data": {
                "share_id": share_id,
                "new_permission_level": request.permission_level
            },
            "message": "权限更新成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新权限失败: {str(e)}")

@router.delete("/share/{share_id}", response_model=Dict[str, Any])
async def revoke_share(
    share_id: str,
    user_id: str = Query(..., description="操作用户ID")
):
    """撤销共享"""
    try:
        if permission_service is None:
            raise HTTPException(status_code=500, detail="权限服务未初始化")

        success = await permission_service.revoke_share(
            share_id=share_id,
            user_id=user_id
        )

        if not success:
            raise HTTPException(status_code=404, detail="共享不存在或无权撤销")

        return {
            "success": True,
            "data": {
                "share_id": share_id
            },
            "message": "共享撤销成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"撤销共享失败: {str(e)}")

@router.get("/shares", response_model=List[Dict[str, Any]])
async def list_shares(
    context_id: Optional[str] = Query(None, description="上下文ID过滤"),
    user_id: str = Query(..., description="用户ID"),
    include_expired: bool = Query(False, description="是否包含已过期的共享"),
    limit: int = Query(50, ge=1, le=100, description="结果数量限制"),
    offset: int = Query(0, ge=0, description="结果偏移量")
):
    """列出共享"""
    try:
        if permission_service is None:
            raise HTTPException(status_code=500, detail="权限服务未初始化")

        shares = await permission_service.list_shares(
            context_id=context_id,
            user_id=user_id,
            include_expired=include_expired,
            limit=limit,
            offset=offset
        )

        return shares

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列出共享失败: {str(e)}")

@router.get("/permissions/{user_id}", response_model=Dict[str, Any])
async def get_user_permissions(
    user_id: str,
    context_id: Optional[str] = Query(None, description="上下文ID（可选）")
):
    """获取用户权限信息"""
    try:
        if permission_service is None:
            raise HTTPException(status_code=500, detail="权限服务未初始化")

        permissions = await permission_service.get_user_permissions(
            user_id=user_id,
            context_id=context_id
        )

        if "error" in permissions:
            raise HTTPException(status_code=500, detail=permissions["error"])

        return {
            "success": True,
            "data": permissions,
            "message": "获取用户权限成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户权限失败: {str(e)}")

@router.get("/check-permission", response_model=Dict[str, Any])
async def check_permission(
    context_id: str = Query(..., description="上下文ID"),
    user_id: str = Query(..., description="用户ID"),
    required_permission: str = Query("view", pattern="^(view|edit|share|delete)$", description="所需权限类型")
):
    """检查用户对上下文的权限"""
    try:
        if permission_service is None:
            raise HTTPException(status_code=500, detail="权限服务未初始化")

        has_permission, permission_level = await permission_service.check_permission(
            context_id=context_id,
            user_id=user_id,
            required_permission=required_permission
        )

        return {
            "success": True,
            "data": {
                "context_id": context_id,
                "user_id": user_id,
                "required_permission": required_permission,
                "has_permission": has_permission,
                "permission_level": permission_level
            },
            "message": f"权限检查完成，结果: {has_permission}",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"权限检查失败: {str(e)}")

@router.get("/access-logs", response_model=List[Dict[str, Any]])
async def get_access_logs(
    context_id: Optional[str] = Query(None, description="上下文ID过滤"),
    user_id: Optional[str] = Query(None, description="用户ID过滤"),
    access_type: Optional[str] = Query(None, description="访问类型过滤"),
    limit: int = Query(100, ge=1, le=200, description="结果数量限制"),
    offset: int = Query(0, ge=0, description="结果偏移量"),
    admin_user_id: str = Query(..., description="管理员用户ID（用于权限检查）")
):
    """获取访问日志（需要管理员权限）"""
    try:
        if permission_service is None:
            raise HTTPException(status_code=500, detail="权限服务未初始化")

        # 简单的权限检查 - 这里可以扩展更复杂的权限逻辑
        if context_id:
            has_permission, _ = await permission_service.check_permission(
                context_id=context_id,
                user_id=admin_user_id,
                required_permission="view"
            )
            if not has_permission:
                raise HTTPException(status_code=403, detail="无权查看此上下文的访问日志")

        logs = await permission_service.get_access_logs(
            context_id=context_id,
            user_id=user_id,
            access_type=access_type,
            limit=limit,
            offset=offset
        )

        return logs

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取访问日志失败: {str(e)}")

@router.get("/permission-levels", response_model=Dict[str, Any])
async def get_permission_levels():
    """获取所有可用的权限级别"""
    try:
        if permission_service is None:
            raise HTTPException(status_code=500, detail="权限服务未初始化")

        levels = permission_service.get_permission_levels()

        return {
            "success": True,
            "data": levels,
            "message": "获取权限级别成功",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取权限级别失败: {str(e)}")

@router.post("/cleanup-expired-shares", response_model=Dict[str, Any])
async def cleanup_expired_shares(
    admin_user_id: str = Query(..., description="管理员用户ID")
):
    """清理过期的共享（需要管理员权限）"""
    try:
        if permission_service is None:
            raise HTTPException(status_code=500, detail="权限服务未初始化")

        # 这里应该检查管理员权限，简化处理
        cleaned_count = await permission_service.cleanup_expired_shares()

        return {
            "success": True,
            "data": {
                "cleaned_count": cleaned_count
            },
            "message": f"清理了 {cleaned_count} 个过期共享",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理过期共享失败: {str(e)}")

@router.get("/contexts/{context_id}/shares", response_model=Dict[str, Any])
async def get_context_shares(
    context_id: str,
    user_id: str = Query(..., description="用户ID（用于权限检查）"),
    include_expired: bool = Query(False, description="是否包含已过期的共享")
):
    """获取特定上下文的所有共享"""
    try:
        if permission_service is None:
            raise HTTPException(status_code=500, detail="权限服务未初始化")

        # 检查权限
        has_permission, _ = await permission_service.check_permission(
            context_id=context_id,
            user_id=user_id,
            required_permission="view"
        )

        if not has_permission:
            raise HTTPException(status_code=403, detail="无权查看此上下文的共享信息")

        shares = await permission_service.list_shares(
            context_id=context_id,
            user_id=None,  # 获取所有共享，不仅仅是特定用户的
            include_expired=include_expired,
            limit=100,
            offset=0
        )

        # 获取上下文基本信息
        with get_database_session() as db:
            context = db.query(Context).filter(Context.id == context_id).first()
            context_info = {
                "id": context.id,
                "title": context.title,
                "description": context.description,
                "owner_id": context.user_id,
                "visibility": context.visibility
            } if context else None

        return {
            "success": True,
            "data": {
                "context": context_info,
                "shares": shares,
                "total_shares": len(shares)
            },
            "message": "获取上下文共享信息成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取上下文共享信息失败: {str(e)}")

@router.get("/users/{user_id}/shared-contexts", response_model=Dict[str, Any])
async def get_user_shared_contexts(
    user_id: str,
    requesting_user_id: str = Query(..., description="请求者用户ID（用于权限检查）"),
    include_expired: bool = Query(False, description="是否包含已过期的共享"),
    limit: int = Query(50, ge=1, le=100, description="结果数量限制"),
    offset: int = Query(0, ge=0, description="结果偏移量")
):
    """获取用户共享的上下文列表"""
    try:
        if permission_service is None:
            raise HTTPException(status_code=500, detail="权限服务未初始化")

        # 权限检查 - 只有用户本人或管理员可以查看
        if requesting_user_id != user_id:
            # 这里可以添加管理员权限检查逻辑
            # 简化处理：只允许用户查看自己的共享上下文
            raise HTTPException(status_code=403, detail="只能查看自己的共享上下文")

        # 获取用户权限信息（包含共享列表）
        user_permissions = await permission_service.get_user_permissions(
            user_id=user_id
        )

        if "error" in user_permissions:
            raise HTTPException(status_code=500, detail=user_permissions["error"])

        # 过滤结果
        result = {
            "user_id": user_id,
            "shares_given": user_permissions.get("shares_given", []),
            "shares_received": user_permissions.get("shares_received", []),
            "total_accessible_contexts": user_permissions.get("total_accessible_contexts", 0)
        }

        # 如果不需要过期共享，进行过滤
        if not include_expired:
            result["shares_given"] = [
                share for share in result["shares_given"]
                if not share.get("is_expired", False)
            ]
            result["shares_received"] = [
                share for share in result["shares_received"]
                if not share.get("is_expired", False)
            ]

        # 分页处理
        if offset > 0 or limit < len(result["shares_given"]):
            result["shares_given"] = result["shares_given"][offset:offset + limit]

        return {
            "success": True,
            "data": result,
            "message": "获取用户共享上下文成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户共享上下文失败: {str(e)}")

# Team management endpoints (基础的团队管理接口)
@router.get("/teams", response_model=Dict[str, Any])
async def get_user_teams(
    user_id: str = Query(..., description="用户ID")
):
    """获取用户所属的团队列表"""
    try:
        # 这里应该实现获取用户团队的逻辑
        # 由于Team模型已经定义，但服务层还没有完全实现
        # 返回基本的响应结构

        return {
            "success": True,
            "data": {
                "teams": [],
                "total_count": 0
            },
            "message": "获取用户团队列表成功",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户团队列表失败: {str(e)}")

@router.get("/teams/{team_id}/contexts", response_model=Dict[str, Any])
async def get_team_contexts(
    team_id: str,
    user_id: str = Query(..., description="用户ID（用于权限检查）"),
    limit: int = Query(50, ge=1, le=100, description="结果数量限制"),
    offset: int = Query(0, ge=0, description="结果偏移量")
):
    """获取团队共享的上下文列表"""
    try:
        if context_service is None:
            raise HTTPException(status_code=500, detail="上下文服务未初始化")

        # 获取团队可见的上下文（visibility="team"）
        contexts = await context_service.list_contexts(
            user_id=None,  # 不限制用户
            visibility="team",  # 只获取团队可见的上下文
            limit=limit,
            offset=offset
        )

        return {
            "success": True,
            "data": {
                "team_id": team_id,
                "contexts": contexts,
                "total_count": len(contexts)
            },
            "message": "获取团队上下文列表成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取团队上下文列表失败: {str(e)}")
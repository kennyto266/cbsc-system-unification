"""
用户管理API端点
User Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Optional, Dict, Any
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from datetime import datetime
import logging
import os
from pathlib import Path

from auth_simple import User
from user_profile import user_profile_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/user", tags=["用户管理"])

# 依赖注入
def get_current_user():
    """获取当前用户"""
    from auth_simple import auth_service
    return auth_service.get_current_user

def get_db():
    """获取数据库会话"""
    return user_profile_service.get_db()

# Pydantic模型
class ProfileUpdate(BaseModel):
    """资料更新模型"""
    bio: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    theme: Optional[str] = None

class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    login_count: int

    class Config:
        from_attributes = True

class ProfileResponse(BaseModel):
    """资料响应模型"""
    user: UserResponse
    avatar_url: Optional[str]
    bio: Optional[str]
    phone: Optional[str]
    timezone: str
    language: str
    theme: str

class NotificationSettings(BaseModel):
    """通知设置模型"""
    email_notifications: Dict[str, bool]
    browser_notifications: Dict[str, bool]

class AppearanceSettings(BaseModel):
    """外观设置模型"""
    theme: str
    language: str
    timezone: str

@router.get("/profile", response_model=ProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取用户资料"""
    try:
        db = next(get_db())

        # 获取用户资料
        profile = user_profile_service.get_or_create_profile(current_user.id, db)

        return ProfileResponse(
            user=UserResponse.from_orm(current_user),
            avatar_url=profile.avatar_url,
            bio=profile.bio,
            phone=profile.phone,
            timezone=profile.timezone,
            language=profile.language,
            theme=profile.theme
        )

    except Exception as e:
        logger.error(f"获取用户资料失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户资料失败"
        )
    finally:
        if 'db' in locals():
            db.close()

@router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新用户资料"""
    try:
        # 过滤空值
        update_data = {k: v for k, v in profile_data.dict().items() if v is not None}

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有提供有效的更新数据"
            )

        success = user_profile_service.update_profile(current_user.id, update_data)

        if success:
            return {"message": "资料更新成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="资料更新失败"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户资料失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="资料更新失败"
        )

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传头像"""
    try:
        # 验证文件类型
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请上传图片文件"
            )

        # 验证文件大小 (5MB)
        if file.size and file.size > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="图片大小不能超过5MB"
            )

        # 读取文件数据
        file_data = await file.read()

        # 获取文件扩展名
        file_extension = file.filename.split('.')[-1] if file.filename else 'jpg'
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']

        if file_extension.lower() not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件格式。支持: {', '.join(allowed_extensions)}"
            )

        # 上传文件
        avatar_url = user_profile_service.upload_avatar(
            current_user.id,
            file_data,
            file_extension
        )

        return {
            "message": "头像上传成功",
            "avatar_url": avatar_url
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传头像失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="头像上传失败"
        )

@router.get("/statistics")
async def get_user_statistics(
    period: int = 30,
    current_user: User = Depends(get_current_user)
):
    """获取用户统计"""
    try:
        if period not in [7, 30, 90]:
            period = 30  # 默认30天

        stats = user_profile_service.get_user_statistics(current_user.id, period)

        # 添加一些计算指标
        if stats:
            stats['avg_daily_logins'] = round(stats['login_count'] / max(stats['active_days'], 1), 1)
            stats['login_frequency'] = 'daily' if stats['avg_daily_logins'] > 1 else 'occasional'
            stats['performance_grade'] = (
                'excellent' if stats['performance_score'] >= 90 else
                'good' if stats['performance_score'] >= 70 else
                'average' if stats['performance_score'] >= 50 else
                'needs_improvement'
            )

        return stats

    except Exception as e:
        logger.error(f"获取用户统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户统计失败"
        )

@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """获取最近活动"""
    try:
        if limit > 50:
            limit = 50  # 限制最大数量

        stats = user_profile_service.get_user_statistics(current_user.id, 30)
        activities = stats.get('recent_activities', [])

        return {
            "activities": activities[:limit],
            "total_count": len(activities)
        }

    except Exception as e:
        logger.error(f"获取最近活动失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取最近活动失败"
        )

@router.get("/settings")
async def get_user_settings(current_user: User = Depends(get_current_user)):
    """获取用户设置"""
    try:
        settings = user_profile_service.get_user_settings(current_user.id)

        return settings

    except Exception as e:
        logger.error(f"获取用户设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户设置失败"
        )

@router.put("/settings/notifications")
async def update_notification_settings(
    settings: NotificationSettings,
    current_user: User = Depends(get_current_user)
):
    """更新通知设置"""
    try:
        success = user_profile_service.update_user_settings(
            current_user.id,
            settings.dict()
        )

        if success:
            return {"message": "通知设置更新成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="通知设置更新失败"
            )

    except Exception as e:
        logger.error(f"更新通知设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="通知设置更新失败"
        )

@router.put("/settings/appearance")
async def update_appearance_settings(
    settings: AppearanceSettings,
    current_user: User = Depends(get_current_user)
):
    """更新外观设置"""
    try:
        # 将外观设置转换为用户资料更新
        profile_update = {
            'theme': settings.theme,
            'language': settings.language,
            'timezone': settings.timezone
        }

        success = user_profile_service.update_profile(current_user.id, profile_update)

        if success:
            return {"message": "外观设置更新成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="外观设置更新失败"
            )

    except Exception as e:
        logger.error(f"更新外观设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="外观设置更新失败"
        )

@router.post("/export-data")
async def export_user_data(current_user: User = Depends(get_current_user)):
    """导出用户数据"""
    try:
        # 收集用户数据
        db = next(get_db())

        profile = user_profile_service.get_or_create_profile(current_user.id, db)
        statistics = user_profile_service.get_user_statistics(current_user.id, 365)
        settings = user_profile_service.get_user_settings(current_user.id)

        export_data = {
            "user_info": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "created_at": current_user.created_at.isoformat(),
                "last_login": current_user.last_login.isoformat() if current_user.last_login else None
            },
            "profile": {
                "bio": profile.bio,
                "phone": profile.phone,
                "timezone": profile.timezone,
                "language": profile.language,
                "theme": profile.theme,
                "avatar_url": profile.avatar_url
            },
            "statistics": statistics,
            "settings": settings,
            "export_date": datetime.utcnow().isoformat()
        }

        # 在实际应用中，这里应该生成文件并提供下载链接
        # 目前只返回数据
        return {
            "message": "用户数据导出成功",
            "data": export_data,
            "note": "在实际部署中，这将生成一个可下载的文件"
        }

    except Exception as e:
        logger.error(f"导出用户数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="导出用户数据失败"
        )
    finally:
        if 'db' in locals():
            db.close()

@router.post("/clear-cache")
async def clear_user_cache(current_user: User = Depends(get_current_user)):
    """清理用户缓存"""
    try:
        # 在实际应用中，这里应该清理Redis或其他缓存
        # 目前只是返回成功消息

        # 记录活动
        user_profile_service.record_activity(
            current_user.id,
            'settings',
            '清理了用户缓存',
            {}
        )

        return {"message": "用户缓存清理完成"}

    except Exception as e:
        logger.error(f"清理用户缓存失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="清理用户缓存失败"
        )

@router.get("/quick-actions")
async def get_quick_actions(current_user: User = Depends(get_current_user)):
    """获取快捷操作"""
    try:
        # 基于用户状态提供快捷操作
        stats = user_profile_service.get_user_statistics(current_user.id, 7)

        actions = [
            {
                "id": "profile_edit",
                "title": "编辑资料",
                "description": "更新个人信息和头像",
                "icon": "User",
                "url": "/profile/edit",
                "color": "blue"
            },
            {
                "id": "security_settings",
                "title": "安全设置",
                "description": "密码和登录安全",
                "icon": "Shield",
                "url": "/settings/security",
                "color": "green"
            },
            {
                "id": "notification_settings",
                "title": "通知设置",
                "description": "邮件和浏览器通知",
                "icon": "Bell",
                "url": "/settings/notifications",
                "color": "purple"
            },
            {
                "id": "data_export",
                "title": "数据导出",
                "description": "下载个人数据备份",
                "icon": "Download",
                "url": "/export-data",
                "color": "gray"
            }
        ]

        return {"actions": actions}

    except Exception as e:
        logger.error(f"获取快捷操作失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取快捷操作失败"
        )
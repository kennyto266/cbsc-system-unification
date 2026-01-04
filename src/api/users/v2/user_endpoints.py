"""
User Management API v2 Endpoints
用戶管理 API v2 端點

提供用戶資料、密碼、MFA、偏好設置等管理功能
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.services.user_service_v2 import UserServiceV2
from src.schemas.user_schemas import (
    UserProfileSchema,
    UserProfileUpdateSchema,
    PasswordChangeRequestSchema,
    PasswordResetRequestSchema,
    PasswordResetConfirmSchema,
    MFASettingsSchema,
    TOTPSetupRequestSchema,
    TOTPSetupResponseSchema,
    TOTPVerifyRequestSchema,
    SMSVerificationRequestSchema,
    SMSVerificationConfirmSchema,
    UserPreferencesSchema,
    APIKeyCreateRequestSchema,
    APIKeyCreateResponseSchema,
    APIKeyResponseSchema,
    ActivityLogSchema,
    ActivityLogListSchema,
    APIResponseSchema,
    PaginatedResponseSchema
)
from src.core.database import get_db
from src.models.user import User

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Create router
router = APIRouter(prefix="/api/v2/users", tags=["user-management-v2"])

# Dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    獲取當前用戶

    Args:
        credentials: JWT 憑證
        db: 數據庫會話

    Returns:
        當前用戶對象

    Raises:
        HTTPException: 認證失敗
    """
    # TODO: Implement JWT verification
    # For now, return a mock user
    user = db.query(User).filter(User.id == "test-user-id").first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未授權訪問"
        )
    return user

async def get_user_service(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserServiceV2:
    """
    獲取用戶服務實例

    Args:
        current_user: 當前用戶
        db: 數據庫會話

    Returns:
        用戶服務實例
    """
    return UserServiceV2(db)


# ============================================================================
# Profile Management Endpoints
# ============================================================================

@router.get("/profile", response_model=APIResponseSchema)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserServiceV2 = Depends(get_user_service)
):
    """
    獲取用戶個人資料

    獲取當前用戶的詳細個人資料信息
    """
    try:
        profile = await user_service.get_user_profile(current_user.id)

        return APIResponseSchema(
            data=profile.dict(),
            message="成功獲取用戶資料"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取用戶資料失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取用戶資料失敗"
        )


@router.put("/profile", response_model=APIResponseSchema)
async def update_user_profile(
    profile_data: UserProfileUpdateSchema,
    current_user: User = Depends(get_current_user),
    user_service: UserServiceV2 = Depends(get_user_service)
):
    """
    更新用戶個人資料

    更新當前用戶的個人資料信息
    """
    try:
        profile = await user_service.update_user_profile(
            current_user.id,
            profile_data
        )

        return APIResponseSchema(
            data=profile.dict(),
            message="用戶資料更新成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用戶資料失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用戶資料失敗"
        )


@router.post("/avatar", response_model=APIResponseSchema)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    user_service: UserServiceV2 = Depends(get_user_service)
):
    """
    上傳用戶頭像

    上傳並設置用戶頭像
    """
    try:
        avatar_url = await user_service.upload_avatar(current_user.id, file)

        return APIResponseSchema(
            data={"avatar_url": avatar_url},
            message="頭像上傳成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上傳頭像失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="上傳頭像失敗"
        )


# ============================================================================
# Password Management Endpoints
# ============================================================================

@router.post("/change-password", response_model=APIResponseSchema)
async def change_password(
    password_data: PasswordChangeRequestSchema,
    current_user: User = Depends(get_current_user),
    user_service: UserServiceV2 = Depends(get_user_service)
):
    """
    更改密碼

    更改當前用戶的登錄密碼
    """
    try:
        success = await user_service.change_password(
            current_user.id,
            password_data
        )

        if success:
            return APIResponseSchema(
                message="密碼更改成功"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密碼更改失敗"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更改密碼失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更改密碼失敗"
        )


@router.post("/request-password-reset", response_model=APIResponseSchema)
async def request_password_reset(
    request_data: PasswordResetRequestSchema,
    db: Session = Depends(get_db)
):
    """
    請求密碼重置

    發送密碼重置郵件到用戶註冊的郵箱
    """
    try:
        user_service = UserServiceV2(db)
        success = await user_service.request_password_reset(request_data.email)

        if success:
            return APIResponseSchema(
                message="如果郵箱存在，重置鏈接已發送"
            )
        else:
            return APIResponseSchema(
                message="如果郵箱存在，重置鏈接已發送"
            )
    except Exception as e:
        logger.error(f"請求密碼重置失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="請求密碼重置失敗"
        )


@router.post("/confirm-password-reset", response_model=APIResponseSchema)
async def confirm_password_reset(
    reset_data: PasswordResetConfirmSchema,
    db: Session = Depends(get_db)
):
    """
    確認密碼重置

    使用重置令牌設置新密碼
    """
    try:
        user_service = UserServiceV2(db)
        success = await user_service.confirm_password_reset(
            reset_data.token,
            reset_data.new_password
        )

        if success:
            return APIResponseSchema(
                message="密碼重置成功"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密碼重置失敗"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"確認密碼重置失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="確認密碼重置失敗"
        )


# ============================================================================
# MFA Settings Endpoints
# ============================================================================

@router.get("/mfa-settings", response_model=APIResponseSchema)
async def get_mfa_settings(
    current_user: User = Depends(get_current_user),
    user_service: UserServiceV2 = Depends(get_user_service)
):
    """
    獲取 MFA 設置

    獲取當前用戶的多因子認證設置
    """
    try:
        settings = await user_service.get_mfa_settings(current_user.id)

        return APIResponseSchema(
            data=settings.dict(),
            message="成功獲取 MFA 設置"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取 MFA 設置失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取 MFA 設置失敗"
        )


@router.post("/mfa/setup-totp", response_model=APIResponseSchema)
async def setup_totp(
    request_data: TOTPSetupRequestSchema,
    current_user: User = Depends(get_current_user),
    user_service: UserServiceV2 = Depends(get_user_service)
):
    """
    設置 TOTP

    初始化 TOTP 多因子認證，返回密鑰和 QR Code
    """
    try:
        totp_setup = await user_service.setup_totp(
            current_user.id,
            request_data.password
        )

        return APIResponseSchema(
            data=totp_setup.dict(),
            message="TOTP 設置初始化成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"設置 TOTP 失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="設置 TOTP 失敗"
        )


@router.post("/mfa/verify-totp", response_model=APIResponseSchema)
async def verify_and_enable_totp(
    verify_data: TOTPVerifyRequestSchema,
    current_user: User = Depends(get_current_user),
    user_service: UserServiceV2 = Depends(get_user_service)
):
    """
    驗證並啟用 TOTP

    驗證 TOTP 代碼並啟用多因子認證
    """
    try:
        success = await user_service.verify_and_enable_totp(
            current_user.id,
            verify_data.code
        )

        if success:
            return APIResponseSchema(
                message="TOTP 驗證成功，多因子認證已啟用"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TOTP 驗證失敗"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"驗證 TOTP 失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="驗證 TOTP 失敗"
        )


@router.post("/mfa/disable-totp", response_model=APIResponseSchema)
async def disable_totp(
    password: str,  # Will be sent in request body
    current_user: User = Depends(get_current_user),
    user_service: UserServiceV2 = Depends(get_user_service)
):
    """
    禁用 TOTP

    禁用 TOTP 多因子認證
    """
    try:
        success = await user_service.disable_totp(current_user.id, password)

        if success:
            return APIResponseSchema(
                message="TOTP 已禁用"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="禁用 TOTP 失敗"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"禁用 TOTP 失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="禁用 TOTP 失敗"
        )


# ============================================================================
# User Preferences Endpoints
# ============================================================================

@router.get("/preferences", response_model=APIResponseSchema)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    user_service: UserServiceV2 = Depends(get_user_service)
):
    """
    獲取用戶偏好設置

    獲取當前用戶的所有偏好設置
    """
    try:
        preferences = await user_service.get_user_preferences(current_user.id)

        return APIResponseSchema(
            data=preferences.dict(),
            message="成功獲取用戶偏好設置"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取用戶偏好設置失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取用戶偏好設置失敗"
        )


@router.put("/preferences", response_model=APIResponseSchema)
async def update_user_preferences(
    preferences: UserPreferencesSchema,
    current_user: User = Depends(get_current_user),
    user_service: UserServiceV2 = Depends(get_user_service)
):
    """
    更新用戶偏好設置

    更新當前用戶的偏好設置
    """
    try:
        updated_preferences = await user_service.update_user_preferences(
            current_user.id,
            preferences
        )

        return APIResponseSchema(
            data=updated_preferences.dict(),
            message="用戶偏好設置更新成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用戶偏好設置失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用戶偏好設置失敗"
        )


# ============================================================================
# API Key Management Endpoints
# ============================================================================

@router.post("/api-keys", response_model=APIResponseSchema)
async def create_api_key(
    key_data: APIKeyCreateRequestSchema,
    current_user: User = Depends(get_current_user),
    user_service: UserServiceV2 = Depends(get_user_service)
):
    """
    創建 API 密鑰

    為當前用戶創建新的 API 密鑰
    """
    try:
        api_key = await user_service.create_api_key(current_user.id, key_data)

        return APIResponseSchema(
            data=api_key.dict(),
            message="API 密鑰創建成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建 API 密鑰失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="創建 API 密鑰失敗"
        )


@router.get("/api-keys", response_model=APIResponseSchema)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    user_service: UserServiceV2 = Depends(get_user_service)
):
    """
    列出 API 密鑰

    獲取當前用戶的所有 API 密鑰
    """
    try:
        api_keys = await user_service.list_api_keys(current_user.id)

        return APIResponseSchema(
            data=api_keys,
            message="成功獲取 API 密鑰列表"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取 API 密鑰列表失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取 API 密鑰列表失敗"
        )


@router.delete("/api-keys/{key_id}", response_model=APIResponseSchema)
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    user_service: UserServiceV2 = Depends(get_user_service)
):
    """
    撤銷 API 密鑰

    撤銷指定的 API 密鑰
    """
    try:
        success = await user_service.revoke_api_key(current_user.id, key_id)

        if success:
            return APIResponseSchema(
                message="API 密鑰已撤銷"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API 密鑰不存在"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"撤銷 API 密鑰失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="撤銷 API 密鑰失敗"
        )


# ============================================================================
# Activity Log Endpoints
# ============================================================================

@router.get("/activity-logs", response_model=PaginatedResponseSchema)
async def get_activity_logs(
    page: int = 1,
    page_size: int = 20,
    action_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    user_service: UserServiceV2 = Depends(get_user_service)
):
    """
    獲取活動日誌

    獲取當前用戶的活動日誌記錄
    """
    try:
        logs, total = await user_service.get_activity_logs(
            current_user.id,
            page,
            page_size,
            action_filter
        )

        pagination = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size
        }

        return PaginatedResponseSchema(
            data=logs,
            pagination=pagination,
            message="成功獲取活動日誌"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取活動日誌失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取活動日誌失敗"
        )
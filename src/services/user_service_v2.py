"""
User Service v2
用戶服務層 v2

提供用戶管理、認證、偏好設置等功能
"""

import logging
import secrets
import hashlib
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from fastapi import HTTPException, status, UploadFile

from ..models.user import User, Role, Permission
from ..schemas.user_schemas import (
    UserProfileSchema,
    UserProfileUpdateSchema,
    PasswordChangeRequestSchema,
    MFASettingsSchema,
    NotificationPreferencesSchema,
    DashboardPreferencesSchema,
    APISettingsSchema,
    UserPreferencesSchema,
    APIKeyCreateRequestSchema,
    APIKeyResponseSchema,
    APIKeyCreateResponseSchema,
    ActivityLogSchema,
    TOTPSetupResponseSchema,
    MFAMethod,
    LanguageType,
    ThemeType
)

logger = logging.getLogger(__name__)


class UserServiceV2:
    """用戶服務 v2"""

    def __init__(self, db: Session):
        """初始化服務"""
        self.db = db
        self.default_notifications = {
            "email": {
                "strategy_alerts": True,
                "performance_reports": True,
                "system_updates": True,
                "security_alerts": True,
                "marketing_emails": False
            },
            "browser": {
                "strategy_alerts": True,
                "system_updates": True,
                "security_alerts": True
            },
            "push": {
                "strategy_alerts": True,
                "security_alerts": True
            }
        }

    # Profile Management
    async def get_user_profile(self, user_id: str) -> UserProfileSchema:
        """
        獲取用戶資料

        Args:
            user_id: 用戶 ID

        Returns:
            用戶資料對象

        Raises:
            HTTPException: 用戶不存在
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )

        # Get role names
        role_names = [role.name for role in user.roles] if user.roles else []

        return UserProfileSchema(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            phone=user.phone,
            timezone=user.timezone,
            language=LanguageType(user.language),
            theme=ThemeType(user.theme),
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_premium=user.is_premium,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at
        )

    async def update_user_profile(
        self,
        user_id: str,
        profile_data: UserProfileUpdateSchema
    ) -> UserProfileSchema:
        """
        更新用戶資料

        Args:
            user_id: 用戶 ID
            profile_data: 更新資料

        Returns:
            更新後的用戶資料

        Raises:
            HTTPException: 用戶不存在或更新失敗
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )

        # Update fields
        update_dict = profile_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if value is not None:
                setattr(user, field, value)

        # Update display_name if not provided
        if not update_dict.get('display_name') and (profile_data.first_name or profile_data.last_name):
            user.display_name = f"{profile_data.first_name or ''} {profile_data.last_name or ''}".strip()

        # Update timestamp
        user.updated_at = datetime.now(timezone.utc)

        try:
            self.db.commit()
            self.db.refresh(user)

            # Log activity
            await self.log_activity(
                user_id,
                "profile_updated",
                details={"updated_fields": list(update_dict.keys())}
            )

            return await self.get_user_profile(user_id)
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新用戶資料失敗: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新用戶資料失敗"
            )

    async def upload_avatar(
        self,
        user_id: str,
        file: UploadFile
    ) -> str:
        """
        上傳用戶頭像

        Args:
            user_id: 用戶 ID
            file: 上傳的文件

        Returns:
            頭像 URL

        Raises:
            HTTPException: 文件驗證失敗或上傳失敗
        """
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必須上傳圖片文件"
            )

        # Validate file size (5MB)
        file_size = 0
        content = await file.read()
        file_size = len(content)

        if file_size > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="圖片大小不能超過 5MB"
            )

        # Reset file pointer
        await file.seek(0)

        # Generate filename
        file_extension = file.filename.split('.')[-1] if file.filename else 'jpg'
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']

        if file_extension.lower() not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件格式。支持: {', '.join(allowed_extensions)}"
            )

        # Save file (in production, use cloud storage)
        filename = f"avatars/{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"

        # For now, return a mock URL
        # In production, save to S3, Azure Blob, or local storage
        avatar_url = f"/static/{filename}"

        # Update user avatar_url
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.avatar_url = avatar_url
            user.updated_at = datetime.now(timezone.utc)
            self.db.commit()

            await self.log_activity(
                user_id,
                "avatar_uploaded",
                details={"filename": filename}
            )

        return avatar_url

    # Password Management
    async def change_password(
        self,
        user_id: str,
        password_data: PasswordChangeRequestSchema
    ) -> bool:
        """
        更改用戶密碼

        Args:
            user_id: 用戶 ID
            password_data: 密碼更改請求

        Returns:
            是否成功

        Raises:
            HTTPException: 驗證失敗或密碼錯誤
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )

        # Verify current password
        if not user.verify_password(password_data.current_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="當前密碼不正確"
            )

        # Check if new password is same as current
        if user.verify_password(password_data.new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="新密碼不能與當前密碼相同"
            )

        # Update password
        user.set_password(password_data.new_password)
        user.updated_at = datetime.now(timezone.utc)

        # Reset failed login attempts and lock if any
        user.failed_login_attempts = 0
        user.locked_until = None

        try:
            self.db.commit()

            await self.log_activity(
                user_id,
                "password_changed",
                details={"method": "user_initiated"}
            )

            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"更改密碼失敗: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更改密碼失敗"
            )

    async def request_password_reset(self, email: str) -> bool:
        """
        請求密碼重置

        Args:
            email: 用戶郵箱

        Returns:
            是否成功發送重置郵件
        """
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            # Don't reveal if user exists
            return True

        # Generate reset token (expires in 1 hour)
        reset_token = secrets.token_urlsafe(32)
        user.reset_token = reset_token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)

        try:
            self.db.commit()

            # TODO: Send email with reset link
            # await email_service.send_password_reset_email(user.email, reset_token)

            await self.log_activity(
                user.id,
                "password_reset_requested",
                details={"email": email}
            )

            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"請求密碼重置失敗: {e}")
            return False

    async def confirm_password_reset(
        self,
        token: str,
        new_password: str
    ) -> bool:
        """
        確認密碼重置

        Args:
            token: 重置令牌
            new_password: 新密碼

        Returns:
            是否成功

        Raises:
            HTTPException: 令牌無效或過期
        """
        user = self.db.query(User).filter(
            and_(
                User.reset_token == token,
                User.reset_token_expires > datetime.now(timezone.utc)
            )
        ).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="重置令牌無效或已過期"
            )

        # Update password
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        user.updated_at = datetime.now(timezone.utc)

        try:
            self.db.commit()

            await self.log_activity(
                user.id,
                "password_reset_completed",
                details={"method": "email_reset"}
            )

            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"確認密碼重置失敗: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密碼重置失敗"
            )

    # MFA Management
    async def get_mfa_settings(self, user_id: str) -> MFASettingsSchema:
        """
        獲取 MFA 設置

        Args:
            user_id: 用戶 ID

        Returns:
            MFA 設置對象
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )

        mfa_methods = []
        if user.mfa_secret:
            mfa_methods.append(MFAMethod.TOTP)
        if user.phone and user.mfa_enabled:
            mfa_methods.append(MFAMethod.SMS)

        return MFASettingsSchema(
            mfa_enabled=user.mfa_enabled,
            mfa_methods=mfa_methods,
            totp_enabled=MFAMethod.TOTP in mfa_methods,
            sms_enabled=MFAMethod.SMS in mfa_methods,
            email_enabled=False,  # Not implemented yet
            phone_number=user.phone,
            backup_codes_count=0,  # TODO: Implement backup codes
            last_mfa_used=user.last_login_at if user.mfa_enabled else None
        )

    async def setup_totp(
        self,
        user_id: str,
        password: str
    ) -> TOTPSetupResponseSchema:
        """
        設置 TOTP

        Args:
            user_id: 用戶 ID
            password: 用戶密碼（用於驗證）

        Returns:
            TOTP 設置響應

        Raises:
            HTTPException: 驗證失敗
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )

        # Verify password
        if not user.verify_password(password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密碼不正確"
            )

        # Generate TOTP secret
        totp_secret = pyotp.random_base32()
        totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
            name=user.email,
            issuer_name="CBSC Strategy Management"
        )

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()

        # Generate backup codes
        backup_codes = [secrets.token_urlsafe(8) for _ in range(10)]

        # Store temporary (not enabled yet)
        user.temp_mfa_secret = totp_secret
        user.temp_backup_codes = backup_codes
        self.db.commit()

        return TOTPSetupResponseSchema(
            secret=totp_secret,
            qr_code_url=f"data:image/png;base64,{qr_code_data}",
            backup_codes=backup_codes
        )

    async def verify_and_enable_totp(
        self,
        user_id: str,
        code: str
    ) -> bool:
        """
        驗證並啟用 TOTP

        Args:
            user_id: 用戶 ID
            code: TOTP 驗證碼

        Returns:
            是否成功

        Raises:
            HTTPException: 驗證失敗
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.temp_mfa_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TOTP 未正確初始化"
            )

        # Verify code
        totp = pyotp.TOTP(user.temp_mfa_secret)
        if not totp.verify(code, valid_window=1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="驗證碼不正確"
            )

        # Enable TOTP
        user.mfa_secret = user.temp_mfa_secret
        user.mfa_enabled = True
        user.temp_mfa_secret = None
        user.temp_backup_codes = None
        user.updated_at = datetime.now(timezone.utc)

        try:
            self.db.commit()

            await self.log_activity(
                user_id,
                "mfa_totp_enabled",
                details={"method": "totp"}
            )

            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"啟用 TOTP 失敗: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="啟用 TOTP 失敗"
            )

    async def disable_totp(self, user_id: str, password: str) -> bool:
        """
        禁用 TOTP

        Args:
            user_id: 用戶 ID
            password: 用戶密碼

        Returns:
            是否成功

        Raises:
            HTTPException: 驗證失敗
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )

        # Verify password
        if not user.verify_password(password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密碼不正確"
            )

        # Check if user has other MFA methods
        has_other_mfa = False
        if user.phone and user.mfa_enabled:
            has_other_mfa = True

        # Disable TOTP
        user.mfa_secret = None
        if not has_other_mfa:
            user.mfa_enabled = False
        user.updated_at = datetime.now(timezone.utc)

        try:
            self.db.commit()

            await self.log_activity(
                user_id,
                "mfa_totp_disabled",
                details={"method": "totp"}
            )

            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"禁用 TOTP 失敗: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="禁用 TOTP 失敗"
            )

    # User Preferences
    async def get_user_preferences(self, user_id: str) -> UserPreferencesSchema:
        """
        獲取用戶偏好設置

        Args:
            user_id: 用戶 ID

        Returns:
            用戶偏好設置對象
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )

        # Parse notifications from JSONB
        notifications = user.notifications or self.default_notifications

        notification_prefs = NotificationPreferencesSchema(
            email_enabled=notifications.get("email", {}).get("enabled", True),
            sms_enabled=notifications.get("sms", {}).get("enabled", False),
            push_enabled=notifications.get("push", {}).get("enabled", True),
            browser_enabled=notifications.get("browser", {}).get("enabled", True),
            strategy_alerts=notifications.get("email", {}).get("strategy_alerts", True),
            performance_reports=notifications.get("email", {}).get("performance_reports", True),
            system_updates=notifications.get("email", {}).get("system_updates", True),
            security_alerts=notifications.get("email", {}).get("security_alerts", True),
            marketing_emails=notifications.get("email", {}).get("marketing_emails", False)
        )

        # TODO: Implement dashboard and API preferences storage
        dashboard_prefs = DashboardPreferencesSchema()
        api_prefs = APISettingsSchema()

        return UserPreferencesSchema(
            notifications=notification_prefs,
            dashboard=dashboard_prefs,
            api=api_prefs
        )

    async def update_user_preferences(
        self,
        user_id: str,
        preferences: UserPreferencesSchema
    ) -> UserPreferencesSchema:
        """
        更新用戶偏好設置

        Args:
            user_id: 用戶 ID
            preferences: 偏好設置

        Returns:
            更新後的偏好設置
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )

        # Convert notifications to JSONB format
        notifications_dict = {
            "email": {
                "enabled": preferences.notifications.email_enabled,
                "strategy_alerts": preferences.notifications.strategy_alerts,
                "performance_reports": preferences.notifications.performance_reports,
                "system_updates": preferences.notifications.system_updates,
                "security_alerts": preferences.notifications.security_alerts,
                "marketing_emails": preferences.notifications.marketing_emails
            },
            "sms": {
                "enabled": preferences.notifications.sms_enabled
            },
            "push": {
                "enabled": preferences.notifications.push_enabled
            },
            "browser": {
                "enabled": preferences.notifications.browser_enabled
            }
        }

        user.notifications = notifications_dict
        user.updated_at = datetime.now(timezone.utc)

        try:
            self.db.commit()

            await self.log_activity(
                user_id,
                "preferences_updated",
                details={"type": "user_preferences"}
            )

            return await self.get_user_preferences(user_id)
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新用戶偏好設置失敗: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新偏好設置失敗"
            )

    # Activity Logging
    async def log_activity(
        self,
        user_id: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        記錄用戶活動日誌

        Args:
            user_id: 用戶 ID
            action: 操作類型
            resource_type: 資源類型
            resource_id: 資源 ID
            details: 詳細信息
            ip_address: IP 地址
            user_agent: 用戶代理
        """
        # TODO: Implement activity logging with database table
        # For now, just log to file
        logger.info(
            f"User Activity: {user_id} - {action} - "
            f"Resource: {resource_type}:{resource_id} - "
            f"Details: {details} - IP: {ip_address}"
        )

    async def get_activity_logs(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        action_filter: Optional[str] = None
    ) -> Tuple[List[ActivityLogSchema], int]:
        """
        獲取用戶活動日誌

        Args:
            user_id: 用戶 ID
            page: 頁碼
            page_size: 每頁大小
            action_filter: 操作類型過濾

        Returns:
            日誌列表和總數
        """
        # TODO: Implement with actual database queries
        # For now, return empty list
        return [], 0

    # API Key Management
    async def create_api_key(
        self,
        user_id: str,
        key_data: APIKeyCreateRequestSchema
    ) -> APIKeyCreateResponseSchema:
        """
        創建 API 密鑰

        Args:
            user_id: 用戶 ID
            key_data: API 密鑰創建請求

        Returns:
            創建的 API 密鑰信息

        Raises:
            HTTPException: 創建失敗
        """
        # TODO: Implement API key management
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="API 密鑰管理功能尚未實現"
        )

    async def list_api_keys(self, user_id: str) -> List[APIKeyResponseSchema]:
        """
        列出用戶的 API 密鑰

        Args:
            user_id: 用戶 ID

        Returns:
            API 密鑰列表
        """
        # TODO: Implement with actual database queries
        return []

    async def revoke_api_key(self, user_id: str, key_id: str) -> bool:
        """
        撤銷 API 密鑰

        Args:
            user_id: 用戶 ID
            key_id: 密鑰 ID

        Returns:
            是否成功
        """
        # TODO: Implement with actual database operations
        return False
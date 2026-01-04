"""
User Management Schemas for API v2
用戶管理 API v2 的數據結構定義
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator, SecretStr
from enum import Enum


class NotificationType(str, Enum):
    """通知類型枚舉"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    BROWSER = "browser"


class ThemeType(str, Enum):
    """主題類型枚舉"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class LanguageType(str, Enum):
    """語言類型枚舉"""
    ZH_TW = "zh-TW"
    ZH_CN = "zh-CN"
    EN = "en"
    JA = "ja"
    KO = "ko"


class MFAMethod(str, Enum):
    """MFA 方法枚舉"""
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    BACKUP_CODE = "backup_code"


# Base Schemas
class BaseUserSchema(BaseModel):
    """用戶基礎結構"""
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Profile Management Schemas
class UserProfileSchema(BaseUserSchema):
    """用戶資料結構"""
    id: str = Field(..., description="用戶 ID")
    username: str = Field(..., min_length=3, max_length=50, description="用戶名")
    email: EmailStr = Field(..., description="電子郵件")
    first_name: Optional[str] = Field(None, max_length=100, description="名")
    last_name: Optional[str] = Field(None, max_length=100, description="姓")
    display_name: Optional[str] = Field(None, max_length=200, description="顯示名稱")
    avatar_url: Optional[str] = Field(None, max_length=500, description="頭像 URL")
    phone: Optional[str] = Field(None, max_length=20, description="電話號碼")
    timezone: str = Field("UTC", description="時區")
    language: LanguageType = Field(LanguageType.EN, description="語言")
    theme: ThemeType = Field(ThemeType.LIGHT, description="主題")
    is_active: bool = Field(True, description="帳號是否啟用")
    is_verified: bool = Field(False, description="是否已驗證")
    is_premium: bool = Field(False, description="是否為高級用戶")
    created_at: datetime = Field(..., description="創建時間")
    updated_at: datetime = Field(..., description="更新時間")
    last_login_at: Optional[datetime] = Field(None, description="最後登入時間")


class UserProfileUpdateSchema(BaseModel):
    """用戶資料更新結構"""
    first_name: Optional[str] = Field(None, max_length=100, description="名")
    last_name: Optional[str] = Field(None, max_length=100, description="姓")
    display_name: Optional[str] = Field(None, max_length=200, description="顯示名稱")
    phone: Optional[str] = Field(None, max_length=20, description="電話號碼")
    timezone: Optional[str] = Field(None, description="時區")
    language: Optional[LanguageType] = Field(None, description="語言")
    theme: Optional[ThemeType] = Field(None, description="主題")


# Password Management Schemas
class PasswordChangeRequestSchema(BaseModel):
    """密碼更改請求結構"""
    current_password: str = Field(..., min_length=1, description="當前密碼")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密碼")
    confirm_password: str = Field(..., description="確認新密碼")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('密碼不匹配')
        return v

    @validator('new_password')
    def validate_password_strength(cls, v):
        """驗證密碼強度"""
        if len(v) < 8:
            raise ValueError('密碼長度至少為 8 個字符')

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v)

        if not (has_upper and has_lower and has_digit):
            raise ValueError('密碼必須包含大小寫字母和數字')

        return v


class PasswordResetRequestSchema(BaseModel):
    """密碼重置請求結構"""
    email: EmailStr = Field(..., description="註冊的電子郵件")


class PasswordResetConfirmSchema(BaseModel):
    """密碼重置確認結構"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密碼")
    confirm_password: str = Field(..., description="確認新密碼")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('密碼不匹配')
        return v


# MFA Settings Schemas
class MFASettingsSchema(BaseUserSchema):
    """MFA 設置結構"""
    mfa_enabled: bool = Field(False, description="是否啟用 MFA")
    mfa_methods: List[MFAMethod] = Field(default_factory=list, description="已配置的 MFA 方法")
    totp_enabled: bool = Field(False, description="是否啟用 TOTP")
    sms_enabled: bool = Field(False, description="是否啟用 SMS 驗證")
    email_enabled: bool = Field(False, description="是否啟用郵件驗證")
    phone_number: Optional[str] = Field(None, description="SMS 驗證電話號碼")
    backup_codes_count: int = Field(0, description="剩餘備份代碼數量")
    last_mfa_used: Optional[datetime] = Field(None, description="最後使用 MFA 的時間")


class TOTPSetupRequestSchema(BaseModel):
    """TOTP 設置請求結構"""
    password: str = Field(..., description="帳號密碼，用於驗證身份")


class TOTPSetupResponseSchema(BaseModel):
    """TOTP 設置響應結構"""
    secret: str = Field(..., description="TOTP 密鑰")
    qr_code_url: str = Field(..., description="QR Code URL")
    backup_codes: List[str] = Field(..., description="備份代碼列表")


class TOTPVerifyRequestSchema(BaseModel):
    """TOTP 驗證請求結構"""
    code: str = Field(..., pattern=r'^\d{6}$', description="6 位數驗證碼")


class SMSVerificationRequestSchema(BaseModel):
    """SMS 驗證設置請求結構"""
    phone_number: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$', description="電話號碼")
    password: str = Field(..., description="帳號密碼，用於驗證身份")


class SMSVerificationConfirmSchema(BaseModel):
    """SMS 驗證確認結構"""
    code: str = Field(..., pattern=r'^\d{6}$', description="6 位數驗證碼")


# User Preferences Schemas
class NotificationPreferencesSchema(BaseModel):
    """通知偏好設置結構"""
    email_enabled: bool = Field(True, description="是否啟用郵件通知")
    sms_enabled: bool = Field(False, description="是否啟用短信通知")
    push_enabled: bool = Field(True, description="是否啟用推送通知")
    browser_enabled: bool = Field(True, description="是否啟用瀏覽器通知")

    # Specific notification types
    strategy_alerts: bool = Field(True, description="策略警報通知")
    performance_reports: bool = Field(True, description="性能報告通知")
    system_updates: bool = Field(True, description="系統更新通知")
    security_alerts: bool = Field(True, description="安全警報通知")
    marketing_emails: bool = Field(False, description="行銷郵件通知")


class DashboardPreferencesSchema(BaseModel):
    """儀表板偏好設置結構"""
    default_layout: str = Field("grid", description="默認布局類型")
    show_welcome: bool = Field(True, description="是否顯示歡迎信息")
    default_timeframe: str = Field("1D", description="默認時間框架")
    auto_refresh: bool = Field(True, description="是否自動刷新")
    refresh_interval: int = Field(30, ge=5, le=300, description="刷新間隔（秒）")
    visible_widgets: List[str] = Field(default_factory=list, description="可見的小部件列表")
    widget_configurations: Dict[str, Any] = Field(default_factory=dict, description="小部件配置")


class APISettingsSchema(BaseModel):
    """API 設置結構"""
    api_key_enabled: bool = Field(False, description="是否啟用 API 密鑰")
    api_keys: List[Dict[str, Any]] = Field(default_factory=list, description="API 密鑰列表")
    rate_limit_per_hour: int = Field(100, ge=1, le=10000, description="每小時請求限制")
    ip_whitelist: List[str] = Field(default_factory=list, description="IP 白名單")
    webhook_url: Optional[str] = Field(None, description="Webhook URL")


class UserPreferencesSchema(BaseModel):
    """用戶偏好設置完整結構"""
    notifications: NotificationPreferencesSchema = Field(default_factory=NotificationPreferencesSchema)
    dashboard: DashboardPreferencesSchema = Field(default_factory=DashboardPreferencesSchema)
    api: APISettingsSchema = Field(default_factory=APISettingsSchema)


# API Key Management Schemas
class APIKeyCreateRequestSchema(BaseModel):
    """API 密鑰創建請求結構"""
    name: str = Field(..., min_length=1, max_length=100, description="API 密鑰名稱")
    description: Optional[str] = Field(None, max_length=500, description="API 密鑰描述")
    permissions: List[str] = Field(default_factory=list, description="權限列表")
    expires_at: Optional[datetime] = Field(None, description="過期時間")


class APIKeyResponseSchema(BaseModel):
    """API 密鑰響應結構"""
    id: str = Field(..., description="API 密鑰 ID")
    name: str = Field(..., description="API 密鑰名稱")
    key_prefix: str = Field(..., description="API 密鑰前綴")
    permissions: List[str] = Field(..., description="權限列表")
    created_at: datetime = Field(..., description="創建時間")
    expires_at: Optional[datetime] = Field(None, description="過期時間")
    last_used_at: Optional[datetime] = Field(None, description="最後使用時間")
    is_active: bool = Field(True, description="是否啟用")


class APIKeyCreateResponseSchema(APIKeyResponseSchema):
    """API 密鑰創建響應結構（包含完整密鑰）"""
    api_key: str = Field(..., description="完整的 API 密鑰（只在創建時顯示）")


# Activity Log Schemas
class ActivityLogSchema(BaseModel):
    """活動日誌結構"""
    id: str = Field(..., description="日誌 ID")
    action: str = Field(..., description="操作類型")
    resource_type: Optional[str] = Field(None, description="資源類型")
    resource_id: Optional[str] = Field(None, description="資源 ID")
    details: Dict[str, Any] = Field(default_factory=dict, description="詳細信息")
    ip_address: Optional[str] = Field(None, description="IP 地址")
    user_agent: Optional[str] = Field(None, description="用戶代理")
    created_at: datetime = Field(..., description="創建時間")


class ActivityLogListSchema(BaseModel):
    """活動日誌列表結構"""
    items: List[ActivityLogSchema] = Field(..., description="日誌項列表")
    total: int = Field(..., description="總數")
    page: int = Field(..., description="當前頁碼")
    page_size: int = Field(..., description="每頁大小")
    total_pages: int = Field(..., description="總頁數")


# Response Wrappers
class APIResponseSchema(BaseModel):
    """API 響應包裝結構"""
    success: bool = Field(True, description="請求是否成功")
    data: Optional[Any] = Field(None, description="響應數據")
    message: Optional[str] = Field(None, description="響應消息")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="響應時間戳")


class PaginatedResponseSchema(BaseModel):
    """分頁響應包裝結構"""
    success: bool = Field(True, description="請求是否成功")
    data: List[Any] = Field(..., description="數據列表")
    pagination: Dict[str, Any] = Field(..., description="分頁信息")
    message: Optional[str] = Field(None, description="響應消息")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="響應時間戳")


# Error Response Schema
class ErrorResponseSchema(BaseModel):
    """錯誤響應結構"""
    success: bool = Field(False, description="請求是否成功")
    error: Dict[str, Any] = Field(..., description="錯誤詳情")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="響應時間戳")
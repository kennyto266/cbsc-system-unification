"""
Authentication Schemas
認證請求/響應模型定義
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum
import re

class MFAType(str, Enum):
    """MFA types supported"""
    TOTP = "totp"
    EMAIL = "email"
    SMS = "sms"

class TokenInfo(BaseModel):
    """Token information"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int

class UserLogin(BaseModel):
    """User login request"""
    username: str = Field(..., min_length=3, max_length=50, description="Username or email")
    password: str = Field(..., min_length=1, description="User password")
    device_fingerprint: Optional[str] = Field(None, description="Unique device fingerprint")
    device_name: Optional[str] = Field(None, description="Human-readable device name")

    @validator('device_name')
    def validate_device_name(cls, v, values):
        if 'device_fingerprint' in values and values['device_fingerprint'] and not v:
            return f"Device-{values['device_fingerprint'][:8]}"
        return v

class UserRegistration(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$',
                         description="Username (alphanumeric and underscore only)")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    confirm_password: str = Field(..., description="Confirm password")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    accept_terms: bool = Field(True, description="Accept terms and conditions")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

    @validator('password')
    def validate_password_complexity(cls, v):
        """Validate password complexity"""
        errors = []

        if len(v) < 8:
            errors.append("Password must be at least 8 characters long")

        if not re.search(r'[a-z]', v):
            errors.append("Password must contain at least one lowercase letter")

        if not re.search(r'[A-Z]', v):
            errors.append("Password must contain at least one uppercase letter")

        if not re.search(r'\d', v):
            errors.append("Password must contain at least one digit")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            errors.append("Password must contain at least one special character")

        # Check for common patterns
        common_patterns = ['123456', 'password', 'qwerty', 'admin']
        if any(pattern in v.lower() for pattern in common_patterns):
            errors.append("Password cannot contain common patterns")

        if errors:
            raise ValueError('. '.join(errors))

        return v

class PasswordReset(BaseModel):
    """Password reset request"""
    email: EmailStr = Field(..., description="Email address for password reset")

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Confirm new password")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class PasswordChange(BaseModel):
    """Password change request"""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Confirm new password")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class TokenRefresh(BaseModel):
    """Token refresh request"""
    refresh_token: str = Field(..., description="Refresh token")
    device_fingerprint: str = Field(..., description="Device fingerprint")

class MFASetupRequest(BaseModel):
    """MFA setup request"""
    mfa_type: MFAType = Field(..., description="Type of MFA to set up")
    email: Optional[EmailStr] = Field(None, description="Email for email MFA")
    phone: Optional[str] = Field(None, pattern=r'^\+?1?\d{9,15}$',
                                 description="Phone number for SMS MFA (with country code)")

    @validator('email')
    def validate_email_for_email_mfa(cls, v, values):
        if 'mfa_type' in values and values['mfa_type'] == MFAType.EMAIL and not v:
            raise ValueError('Email is required for email MFA')
        return v

    @validator('phone')
    def validate_phone_for_sms_mfa(cls, v, values):
        if 'mfa_type' in values and values['mfa_type'] == MFAType.SMS and not v:
            raise ValueError('Phone number is required for SMS MFA')
        return v

class MFAVerifyRequest(BaseModel):
    """MFA verification request"""
    mfa_challenge_token: str = Field(..., description="MFA challenge token")
    code: Optional[str] = Field(None, min_length=6, max_length=6, description="MFA verification code")
    backup_code: Optional[str] = Field(None, min_length=8, max_length=8, description="Backup code")

    @validator('backup_code')
    def validate_backup_code_format(cls, v):
        if v and not re.match(r'^[A-F0-9]+$', v):
            raise ValueError('Backup code must be alphanumeric')
        return v

    @validator('code')
    def validate_code_or_backup(cls, v, values):
        if not v and not values.get('backup_code'):
            raise ValueError('Either verification code or backup code must be provided')
        return v

class MFADisableRequest(BaseModel):
    """MFA disable request"""
    mfa_type: MFAType = Field(..., description="Type of MFA to disable")
    password: str = Field(..., description="Current password for verification")

class AuthResponse(BaseModel):
    """Base authentication response"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LoginResponse(AuthResponse):
    """Login response"""
    requires_mfa: bool = Field(False, description="Whether MFA is required")
    mfa_types: Optional[List[MFAType]] = Field(None, description="MFA types required")
    mfa_challenge_token: Optional[str] = Field(None, description="MFA challenge token")
    token_info: Optional[TokenInfo] = Field(None, description="Token information")

class RegisterResponse(AuthResponse):
    """Registration response"""
    user_id: Optional[int] = Field(None, description="New user ID")
    email_verification_required: bool = Field(False, description="Whether email verification is required")

class TokenRefreshResponse(AuthResponse):
    """Token refresh response"""
    token_info: TokenInfo = Field(..., description="New token information")

class LogoutResponse(AuthResponse):
    """Logout response"""
    revoked_tokens_count: Optional[int] = Field(None, description="Number of tokens revoked")

class MFASetupResponse(AuthResponse):
    """MFA setup response"""
    mfa_type: MFAType
    secret: Optional[str] = None  # TOTP secret
    qr_code: Optional[str] = None  # Base64 encoded QR code
    backup_codes: Optional[List[str]] = None
    setup_instructions: Optional[Dict[str, Any]] = None

class MFASummary(BaseModel):
    """MFA settings summary"""
    mfa_enabled: bool
    mfa_types: List[MFAType]
    last_used: Optional[datetime]

class UserProfile(BaseModel):
    """User profile information"""
    id: int
    username: str
    email: Optional[str]
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    mfa_summary: MFASummary

    class Config:
        from_attributes = True

class LoginAttempt(BaseModel):
    """Login attempt record"""
    id: int
    ip_address: str
    success: bool
    failure_reason: Optional[str]
    timestamp: datetime
    user_agent: str
    device_info: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

class UserDevice(BaseModel):
    """User device information"""
    id: int
    device_name: str
    device_type: str
    device_fingerprint: str
    last_seen: datetime
    is_trusted: bool
    location: Optional[str]

    class Config:
        from_attributes = True

class PasswordStrength(BaseModel):
    """Password strength assessment"""
    score: int = Field(..., ge=0, le=6, description="Password strength score (0-6)")
    level: str = Field(..., pattern=r'^(weak|medium|strong)$', description="Strength level")
    requirements: Dict[str, bool] = Field(..., description="Password requirements check")
    suggestions: Optional[List[str]] = Field(None, description="Improvement suggestions")

class EmailVerification(BaseModel):
    """Email verification request"""
    token: str = Field(..., description="Email verification token")

class ResendVerification(BaseModel):
    """Resend email verification request"""
    email: EmailStr = Field(..., description="Email address to verify")

class SessionInfo(BaseModel):
    """Active session information"""
    session_id: str
    device_name: str
    ip_address: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_current: bool

class SecuritySettings(BaseModel):
    """User security settings"""
    mfa_enabled: bool
    email_notifications: bool
    session_timeout: int
    trusted_devices: List[str]
    login_alerts: bool

class AuditLogEntry(BaseModel):
    """Security audit log entry"""
    id: int
    action: str
    resource: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    success: bool
    details: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

class APIKeyCreate(BaseModel):
    """API key creation request"""
    name: str = Field(..., min_length=1, max_length=100, description="Key name/label")
    permissions: List[str] = Field(default_factory=list, description="Permissions list")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")

class APIKeyResponse(BaseModel):
    """API key creation response"""
    api_key: str = Field(..., description="Generated API key")
    key_id: str = Field(..., description="Key identifier")
    name: str = Field(..., description="Key name")
    permissions: List[str] = Field(..., description="Key permissions")
    expires_at: Optional[datetime] = Field(None, description="Key expiration")
    created_at: datetime = Field(..., description="Creation timestamp")
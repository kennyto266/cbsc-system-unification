"""
MFA (Multi-Factor Authentication) models

This module contains database models for multi-factor authentication features including:
- MFA sessions
- Trusted devices
- MFA audit logs
- User security settings
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from pydantic import BaseModel, Field
import secrets

from .unified_base import UnifiedBaseModel, UnifiedSchema


class MFASession(UnifiedBaseModel):
    """MFA verification session model"""

    __tablename__ = 'mfa_sessions'

    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    user = relationship("User", backref="mfa_sessions")

    # Session details
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    mfa_type = Column(String(20), nullable=False)  # 'totp', 'sms', 'email'
    status = Column(String(20), nullable=False, default='pending')  # 'pending', 'verified', 'expired', 'failed'

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Request metadata
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)

    # Security
    attempt_count = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    json_metadata = Column(JSONB, nullable=True)

    def increment_attempt(self):
        """Increment failed attempt count"""
        self.attempt_count += 1
        if self.attempt_count >= self.max_attempts:
            self.status = 'failed'

    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now(timezone.utc) > self.expires_at

    def is_failed(self) -> bool:
        """Check if session has failed"""
        return self.status == 'failed' or self.attempt_count >= self.max_attempts


class MFATrustedDevice(UnifiedBaseModel):
    """MFA trusted device model"""

    __tablename__ = 'mfa_trusted_devices'

    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    user = relationship("User", backref="trusted_devices")

    # Device identification
    device_fingerprint = Column(String(255), nullable=False, index=True)
    device_name = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=True)  # 'mobile', 'desktop', 'tablet'

    # Status and timestamps
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Request metadata
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    json_metadata = Column(JSONB, nullable=True)

    def is_expired(self) -> bool:
        """Check if device trust has expired"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def update_last_used(self, ip_address: str = None, user_agent: str = None):
        """Update last used timestamp and metadata"""
        self.last_used_at = datetime.now(timezone.utc)
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent


class MFAAuditLog(UnifiedBaseModel):
    """MFA activity audit log model"""

    __tablename__ = 'mfa_audit_log'

    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    user = relationship("User", backref="mfa_audit_logs")

    # Activity details
    action = Column(String(50), nullable=False, index=True)  # 'enable', 'disable', 'verify', 'failed_attempt'
    mfa_type = Column(String(20), nullable=True)
    status = Column(String(20), nullable=False, index=True)  # 'success', 'failed', 'bypass'

    # Request metadata
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    json_metadata = Column(JSONB, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)


class UserSecuritySettings(UnifiedBaseModel):
    """User security preferences model"""

    __tablename__ = 'user_security_settings'

    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), unique=True, nullable=False, index=True)
    user = relationship("User", backref="security_settings")

    # MFA requirements
    require_mfa_for_login = Column(Boolean, default=False, nullable=False)
    require_mfa_for_sensitive_operations = Column(Boolean, default=True, nullable=False)

    # MFA methods preferences
    preferred_mfa_method = Column(String(20), nullable=True)  # 'totp', 'sms', 'email'
    allow_backup_codes = Column(Boolean, default=True, nullable=False)

    # Trusted device settings
    enable_trusted_devices = Column(Boolean, default=True, nullable=False)
    trusted_device_duration_days = Column(Integer, default=30, nullable=False)

    # Session security
    session_timeout_minutes = Column(Integer, default=480, nullable=False)  # 8 hours
    max_concurrent_sessions = Column(Integer, default=5, nullable=False)

    # Notification settings
    notify_on_new_device = Column(Boolean, default=True, nullable=False)
    notify_on_failed_login = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


# Pydantic Schemas

class MFASessionBaseSchema(UnifiedSchema):
    """MFA session base schema"""
    mfa_type: str = Field(..., description="MFA type")
    status: str = Field("pending", description="Session status")
    expires_at: datetime = Field(..., description="Expiration time")


class MFASessionCreateSchema(MFASessionBaseSchema):
    """Create MFA session schema"""
    user_id: str = Field(..., description="User ID")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class MFASessionResponseSchema(MFASessionBaseSchema):
    """MFA session response schema"""
    id: str
    session_token: str
    created_at: datetime
    verified_at: Optional[datetime] = None
    attempt_count: int
    max_attempts: int
    is_expired: bool = False
    is_failed: bool = False

    class Config:
        from_attributes = True


class MFATrustedDeviceBaseSchema(UnifiedSchema):
    """Trusted device base schema"""
    device_name: Optional[str] = Field(None, description="Device name")
    device_type: Optional[str] = Field(None, description="Device type")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")


class MFATrustedDeviceCreateSchema(MFATrustedDeviceBaseSchema):
    """Create trusted device schema"""
    device_fingerprint: str = Field(..., description="Device fingerprint")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")


class MFATrustedDeviceResponseSchema(MFATrustedDeviceBaseSchema):
    """Trusted device response schema"""
    id: str
    device_fingerprint: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_expired: bool = False

    class Config:
        from_attributes = True


class UserSecuritySettingsBaseSchema(UnifiedSchema):
    """User security settings base schema"""
    require_mfa_for_login: bool = Field(False, description="Require MFA for login")
    require_mfa_for_sensitive_operations: bool = Field(True, description="Require MFA for sensitive operations")
    preferred_mfa_method: Optional[str] = Field(None, description="Preferred MFA method")
    allow_backup_codes: bool = Field(True, description="Allow backup codes")
    enable_trusted_devices: bool = Field(True, description="Enable trusted devices")
    trusted_device_duration_days: int = Field(30, description="Trusted device duration in days")
    session_timeout_minutes: int = Field(480, description="Session timeout in minutes")
    max_concurrent_sessions: int = Field(5, description="Maximum concurrent sessions")
    notify_on_new_device: bool = Field(True, description="Notify on new device")
    notify_on_failed_login: bool = Field(True, description="Notify on failed login")


class UserSecuritySettingsUpdateSchema(UserSecuritySettingsBaseSchema):
    """Update user security settings schema"""
    pass


class UserSecuritySettingsResponseSchema(UserSecuritySettingsBaseSchema):
    """User security settings response schema"""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MFAEnrollmentRequestSchema(UnifiedSchema):
    """MFA enrollment request schema"""
    mfa_type: str = Field(..., description="MFA type to enable")
    phone_number: Optional[str] = Field(None, description="Phone number for SMS MFA")
    verification_code: Optional[str] = Field(None, description="Verification code")


class MFAVerificationRequestSchema(UnifiedSchema):
    """MFA verification request schema"""
    session_token: Optional[str] = Field(None, description="MFA session token")
    verification_code: str = Field(..., description="Verification code")
    backup_code: Optional[str] = Field(None, description="Backup code")
    remember_device: Optional[bool] = Field(False, description="Remember this device")


class MFADisableRequestSchema(UnifiedSchema):
    """MFA disable request schema"""
    verification_code: Optional[str] = Field(None, description="Verification code")
    backup_code: Optional[str] = Field(None, description="Backup code")
    confirmation: bool = Field(..., description="Confirm disabling MFA")


class MFAStatusResponseSchema(UnifiedSchema):
    """MFA status response schema"""
    mfa_enabled: bool = Field(..., description="MFA enabled status")
    mfa_type: Optional[str] = Field(None, description="Enabled MFA type")
    phone_verified: bool = Field(False, description="Phone verification status")
    phone_display: Optional[str] = Field(None, description="Phone display format")
    backup_codes_available: int = Field(0, description="Number of available backup codes")
    trusted_devices_count: int = Field(0, description="Number of trusted devices")
    recent_login_attempts: int = Field(0, description="Recent login attempts")
    last_mfa_used: Optional[datetime] = Field(None, description="Last MFA usage time")
    security_settings: Optional[Dict[str, Any]] = Field(None, description="Security settings")

    class Config:
        from_attributes = True
"""
Pydantic Schemas for Authentication and User Management
Request/response models with comprehensive validation
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator, root_validator
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    TRADER = "trader"
    ANALYST = "analyst"
    VIEWER = "viewer"


class LoginMethod(str, Enum):
    """Login method enumeration"""
    PASSWORD = "password"
    OAUTH = "oauth"
    SSO = "sso"
    MFA = "mfa"


class DeviceType(str, Enum):
    """Device type enumeration"""
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"


class PasswordStrength(str, Enum):
    """Password strength levels"""
    WEAK = "weak"
    FAIR = "fair"
    GOOD = "good"
    STRONG = "strong"


# User Schemas
class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50, regex=r'^[a-zA-Z0-9_-]+$')
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    timezone: str = Field("UTC", max_length=50)
    language: str = Field("en", max_length=10)
    theme: str = Field("light", regex=r'^(light|dark)$')

    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        forbidden_names = ['admin', 'root', 'system', 'api', 'www']
        if v.lower() in forbidden_names:
            raise ValueError('Username is not allowed')
        return v

    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Invalid phone number format')
        return v


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str
    is_premium: Optional[bool] = False

    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        errors = []
        if len(v) < 8:
            errors.append('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            errors.append('Password must contain uppercase letters')
        if not any(c.islower() for c in v):
            errors.append('Password must contain lowercase letters')
        if not any(c.isdigit() for c in v):
            errors.append('Password must contain digits')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            errors.append('Password must contain special characters')

        if errors:
            raise ValueError('; '.join(errors))
        return v

    @root_validator
    def validate_password_match(cls, values):
        """Validate password confirmation"""
        password = values.get('password')
        confirm_password = values.get('confirm_password')
        if password != confirm_password:
            raise ValueError('Passwords do not match')
        return values


class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    theme: Optional[str] = Field(None, regex=r'^(light|dark)$')
    notifications: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class UserResponse(UserBase):
    """User response schema"""
    id: str
    is_active: bool
    is_verified: bool
    is_premium: bool
    mfa_enabled: bool
    failed_login_attempts: int
    locked_until: Optional[datetime]
    last_login_at: Optional[datetime]
    last_login_ip: Optional[str]
    created_at: datetime
    updated_at: datetime
    roles: List[str] = []
    permissions: List[str] = []

    class Config:
        from_attributes = True


class UserPublic(BaseModel):
    """Public user information (safe to share)"""
    id: str
    username: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    is_premium: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Authentication Schemas
class UserLogin(BaseModel):
    """User login schema"""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    remember_me: Optional[bool] = False
    device_fingerprint: Optional[str] = None


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
    permissions: List[str]
    session_id: str


class TokenRefresh(BaseModel):
    """Token refresh schema"""
    refresh_token: str


class PasswordChange(BaseModel):
    """Password change schema"""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        errors = []
        if len(v) < 8:
            errors.append('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            errors.append('Password must contain uppercase letters')
        if not any(c.islower() for c in v):
            errors.append('Password must contain lowercase letters')
        if not any(c.isdigit() for c in v):
            errors.append('Password must contain digits')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            errors.append('Password must contain special characters')

        if errors:
            raise ValueError('; '.join(errors))
        return v

    @root_validator
    def validate_passwords(cls, values):
        """Validate password confirmation"""
        new_password = values.get('new_password')
        confirm_password = values.get('confirm_password')
        if new_password != confirm_password:
            raise ValueError('Passwords do not match')
        return values


class PasswordReset(BaseModel):
    """Password reset request schema"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

    @root_validator
    def validate_passwords(cls, values):
        """Validate password confirmation"""
        new_password = values.get('new_password')
        confirm_password = values.get('confirm_password')
        if new_password != confirm_password:
            raise ValueError('Passwords do not match')
        return values


class EmailVerification(BaseModel):
    """Email verification schema"""
    token: str


# MFA Schemas
class MFASetup(BaseModel):
    """MFA setup response"""
    secret: str
    qr_code: str
    backup_codes: List[str]


class MFAVerify(BaseModel):
    """MFA verification schema"""
    code: str = Field(..., min_length=6, max_length=6, regex=r'^[0-9]{6}$')


class MFADisable(BaseModel):
    """MFA disable schema"""
    password: str
    code: str = Field(..., min_length=6, max_length=6, regex=r'^[0-9]{6}$')


# Role and Permission Schemas
class RoleBase(BaseModel):
    """Base role schema"""
    name: str = Field(..., min_length=2, max_length=50, regex=r'^[a-zA-Z0-9_-]+$')
    display_name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    level: int = Field(0, ge=0)
    is_active: bool = True


class RoleCreate(RoleBase):
    """Role creation schema"""
    permission_ids: Optional[List[str]] = []


class RoleUpdate(BaseModel):
    """Role update schema"""
    display_name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permission_ids: Optional[List[str]] = None


class RoleResponse(RoleBase):
    """Role response schema"""
    id: str
    is_system_role: bool
    created_at: datetime
    updated_at: datetime
    permissions: List[str] = []
    user_count: int = 0

    class Config:
        from_attributes = True


class PermissionBase(BaseModel):
    """Base permission schema"""
    code: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    category: str = Field(..., min_length=2, max_length=50)
    resource: str = Field(..., min_length=2, max_length=50)
    action: str = Field(..., min_length=2, max_length=50)
    level: int = Field(0, ge=0)
    is_active: bool = True


class PermissionCreate(PermissionBase):
    """Permission creation schema"""
    pass


class PermissionResponse(PermissionBase):
    """Permission response schema"""
    id: str
    is_system_permission: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserRoleAssign(BaseModel):
    """User role assignment schema"""
    user_id: str
    role_id: str
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class UserRoleUpdate(BaseModel):
    """User role update schema"""
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


# Session and Device Schemas
class UserDeviceResponse(BaseModel):
    """User device response schema"""
    id: str
    device_name: str
    device_type: DeviceType
    platform: Optional[str]
    browser: Optional[str]
    last_ip: Optional[str]
    last_location: Optional[str]
    first_seen_at: datetime
    last_seen_at: datetime
    usage_count: int
    is_trusted: bool
    is_blocked: bool

    class Config:
        from_attributes = True


class UserSessionResponse(BaseModel):
    """User session response schema"""
    id: str
    device: Optional[UserDeviceResponse]
    ip_address: Optional[str]
    location: Optional[str]
    created_at: datetime
    last_accessed_at: datetime
    expires_at: datetime
    is_active: bool
    is_trusted: bool
    mfa_verified: bool

    class Config:
        from_attributes = True


# Login History and Audit Schemas
class LoginHistoryResponse(BaseModel):
    """Login history response schema"""
    id: str
    ip_address: Optional[str]
    device_info: Optional[Dict[str, Any]]
    location: Optional[str]
    success: bool
    failure_reason: Optional[str]
    login_method: LoginMethod
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Audit log response schema"""
    id: str
    user_id: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    endpoint: Optional[str]
    method: Optional[str]
    ip_address: Optional[str]
    status: str
    status_code: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# Password Strength Schema
class PasswordStrengthResult(BaseModel):
    """Password strength validation result"""
    is_valid: bool
    score: int = Field(..., ge=0, le=5)
    strength: PasswordStrength
    feedback: List[str]
    requirements: Dict[str, bool]

    class Config:
        schema_extra = {
            "example": {
                "is_valid": True,
                "score": 4,
                "strength": "strong",
                "feedback": ["Password meets all requirements"],
                "requirements": {
                    "length": True,
                    "uppercase": True,
                    "lowercase": True,
                    "numbers": True,
                    "special": True
                }
            }
        }


# List and Filter Schemas
class UserListParams(BaseModel):
    """User list query parameters"""
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    search: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_premium: Optional[bool] = None
    role: Optional[str] = None
    sort_by: Optional[str] = Field("created_at", regex=r'^(username|email|created_at|last_login)')
    sort_order: Optional[str] = Field("desc", regex=r'^(asc|desc)')


class RoleListParams(BaseModel):
    """Role list query parameters"""
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    search: Optional[str] = None
    is_active: Optional[bool] = None
    is_system_role: Optional[bool] = None
    sort_by: Optional[str] = Field("name", regex=r'^(name|level|created_at)')
    sort_order: Optional[str] = Field("asc", regex=r'^(asc|desc)')


class AuditLogListParams(BaseModel):
    """Audit log list query parameters"""
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    user_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: Optional[str] = Field("created_at", regex=r'^(created_at|action|status)')
    sort_order: Optional[str] = Field("desc", regex=r'^(asc|desc)')


# Batch Operations
class BatchUserOperation(BaseModel):
    """Batch user operation schema"""
    user_ids: List[str]
    operation: str = Field(..., regex=r'^(activate|deactivate|delete|assign_role|remove_role)$')
    value: Optional[Any] = None


class PasswordPolicy(BaseModel):
    """Password policy configuration"""
    min_length: int = Field(8, ge=6, le=128)
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special: bool = True
    prevent_common: bool = True
    prevent_username: bool = True
    max_age_days: Optional[int] = Field(None, ge=1)
    history_count: int = Field(5, ge=1, le=20)
    lockout_attempts: int = Field(5, ge=1, le=10)
    lockout_minutes: int = Field(30, ge=1, le=1440)


# API Response Wrappers
class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    success: bool
    message: str
    data: List[Any]
    pagination: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
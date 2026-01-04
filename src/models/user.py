"""
用戶和權限管理模型

定義用戶、角色、權限等相關的數據模型。
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, Text, Table, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pydantic import BaseModel, Field, EmailStr, validator
import secrets
import hashlib

from .unified_base import UnifiedBaseModel, UnifiedSchema, StatusEnum

# 多對多關聯表
user_roles = Table(
    'user_roles',
    UnifiedBaseModel.metadata,
    Column('user_id', String(36), ForeignKey('user.id'), primary_key=True),
    Column('role_id', String(36), ForeignKey('role.id'), primary_key=True),
    Column('assigned_at', DateTime, default=lambda: datetime.now(timezone.utc)),
    Column('assigned_by', String(36), nullable=True),
    Column('expires_at', DateTime, nullable=True)
)

role_permissions = Table(
    'role_permissions',
    UnifiedBaseModel.metadata,
    Column('role_id', String(36), ForeignKey('role.id'), primary_key=True),
    Column('permission_id', String(36), ForeignKey('permission.id'), primary_key=True),
    Column('granted_at', DateTime, default=lambda: datetime.now(timezone.utc)),
    Column('granted_by', String(36), nullable=True)
)

class User(UnifiedBaseModel):
    """用戶模型"""

    __tablename__ = 'users'

    # 基本信息
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # 個人信息
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    display_name = Column(String(200), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)

    # 狀態和驗證
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)

    # 安全設置
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(32), nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)

    # 偏好設置
    timezone = Column(String(50), default='UTC', nullable=False)
    language = Column(String(10), default='en', nullable=False)
    theme = Column(String(20), default='light', nullable=False)
    notifications = Column(JSONB, nullable=True)

    # 關聯
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    portfolios = relationship("Portfolio", back_populates="user")
    strategy_configs = relationship("StrategyConfig", back_populates="user")

    def set_password(self, password: str):
        """設置密碼"""
        salt = secrets.token_hex(16)
        self.password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() + ':' + salt

    def verify_password(self, password: str) -> bool:
        """驗證密碼"""
        if not self.password_hash or ':' not in self.password_hash:
            return False

        hash_part, salt = self.password_hash.split(':')
        test_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
        return hash_part == test_hash

    def has_permission(self, permission_code: str) -> bool:
        """檢查用戶是否有特定權限"""
        for role in self.roles:
            if role.has_permission(permission_code):
                return True
        return False

    def lock_account(self, hours: int = 24):
        """鎖定賬戶"""
        from datetime import timedelta
        self.locked_until = datetime.now(timezone.utc) + timedelta(hours=hours)
        self.failed_login_attempts = 0

    def unlock_account(self):
        """解鎖賬戶"""
        self.locked_until = None
        self.failed_login_attempts = 0

class Role(UnifiedBaseModel):
    """角色模型"""

    __tablename__ = 'roles'

    # 基本信息
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # 狀態
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_role = Column(Boolean, default=False, nullable=False)

    # 權限等級
    level = Column(Integer, default=0, nullable=False)

    # 關聯
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

    def has_permission(self, permission_code: str) -> bool:
        """檢查角色是否有特定權限"""
        return any(p.code == permission_code for p in self.permissions)

class Permission(UnifiedBaseModel):
    """權限模型"""

    __tablename__ = 'permissions'

    # 基本信息
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # 權限分類
    category = Column(String(50), nullable=False, index=True)
    resource = Column(String(50), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)

    # 權限等級
    level = Column(Integer, default=0, nullable=False)

    # 狀態
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_permission = Column(Boolean, default=False, nullable=False)

    # 關聯
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class UserRole(UnifiedBaseModel):
    """用戶角色關聯模型"""

    __tablename__ = 'user_role_assignments'

    # 關聯字段
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    role_id = Column(String(36), ForeignKey('roles.id'), nullable=False)

    # 分配信息
    assigned_by = Column(String(36), nullable=True)
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=True)

    # 狀態
    is_active = Column(Boolean, default=True, nullable=False)

    # 備註
    notes = Column(Text, nullable=True)

# Pydantic Schemas
class UserBaseSchema(UnifiedSchema):
    """用戶基礎Schema"""
    username: str = Field(..., min_length=3, max_length=50, description="用戶名")
    email: EmailStr = Field(..., description="電子郵件")
    first_name: Optional[str] = Field(None, max_length=100, description="名")
    last_name: Optional[str] = Field(None, max_length=100, description="姓")
    display_name: Optional[str] = Field(None, max_length=200, description="顯示名稱")
    avatar_url: Optional[str] = Field(None, max_length=500, description="頭像URL")
    phone: Optional[str] = Field(None, max_length=20, description="電話號碼")
    timezone: str = Field("UTC", description="時區")
    language: str = Field("en", description="語言")
    theme: str = Field("light", description="主題")

class UserCreateSchema(UserBaseSchema):
    """創建用戶Schema"""
    password: str = Field(..., min_length=8, max_length=128, description="密碼")
    confirm_password: str = Field(..., description="確認密碼")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('密碼不匹配')
        return v

class UserUpdateSchema(UnifiedSchema):
    """更新用戶Schema"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    avatar_url: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    timezone: Optional[str] = None
    language: Optional[str] = None
    theme: Optional[str] = None
    notifications: Optional[Dict[str, Any]] = None

class UserResponseSchema(UserBaseSchema):
    """用戶響應Schema"""
    is_active: bool
    is_verified: bool
    is_premium: bool
    mfa_enabled: bool
    last_login_at: Optional[datetime] = None
    roles: List[str] = []

    class Config:
        from_attributes = True

class RoleBaseSchema(UnifiedSchema):
    """角色基礎Schema"""
    name: str = Field(..., min_length=3, max_length=50, description="角色名稱")
    display_name: str = Field(..., min_length=3, max_length=100, description="顯示名稱")
    description: Optional[str] = Field(None, description="角色描述")
    level: int = Field(0, ge=0, description="權限等級")

class RoleCreateSchema(RoleBaseSchema):
    """創建角色Schema"""
    permission_ids: List[str] = Field(default_factory=list, description="權限ID列表")

class RoleResponseSchema(RoleBaseSchema):
    """角色響應Schema"""
    is_active: bool
    is_system_role: bool
    user_count: int = 0
    permissions: List[str] = []

    class Config:
        from_attributes = True

class PermissionBaseSchema(UnifiedSchema):
    """權限基礎Schema"""
    code: str = Field(..., min_length=3, max_length=100, description="權限代碼")
    name: str = Field(..., min_length=3, max_length=100, description="權限名稱")
    description: Optional[str] = Field(None, description="權限描述")
    category: str = Field(..., description="權限分類")
    resource: str = Field(..., description="資源")
    action: str = Field(..., description="操作")
    level: int = Field(0, ge=0, description="權限等級")

class PermissionResponseSchema(PermissionBaseSchema):
    """權限響應Schema"""
    is_active: bool
    is_system_permission: bool
    role_count: int = 0

    class Config:
        from_attributes = True
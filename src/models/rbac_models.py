"""
RBAC (Role-Based Access Control) Models
基於角色的訪問控制模型

增強現有的用戶模型，添加動態權限、臨時授權和審計功能。
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Set
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum as PydanticEnum

# Handle pydantic v2/v1 compatibility
try:
    from pydantic import BaseModel, Field, field_validator
    PYDANTIC_V2 = True
except ImportError:
    from pydantic import BaseModel, Field, validator
    PYDANTIC_V2 = False

from .unified_base import UnifiedBaseModel, UnifiedSchema, StatusEnum
from .user import User, Role, Permission, user_roles, role_permissions


class PermissionLevel(str, PydanticEnum):
    """權限等級枚舉"""
    READ = "read"           # 只讀權限
    WRITE = "write"         # 讀寫權限
    ADMIN = "admin"         # 管理權限
    OWNER = "owner"         # 所有者權限


class ResourceAction(str, PydanticEnum):
    """資源操作枚舉"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    APPROVE = "approve"
    EXPORT = "export"
    IMPORT = "import"
    ADMIN = "admin"


class ResourceType(str, PydanticEnum):
    """資源類型枚舉"""
    STRATEGY = "strategy"
    BACKTEST = "backtest"
    TRADING = "trading"
    USER = "user"
    ROLE = "role"
    REPORT = "report"
    SYSTEM = "system"
    MARKET_DATA = "market_data"
    PORTFOLIO = "portfolio"


class DynamicPermission(UnifiedBaseModel):
    """動態權限模型"""

    __tablename__ = 'dynamic_permissions'

    # 基本信息
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # 權限定義
    resource_type = Column(Enum(ResourceType), nullable=False, index=True)
    action = Column(Enum(ResourceAction), nullable=False, index=True)
    level = Column(Enum(PermissionLevel), nullable=False)

    # 條件限制
    conditions = Column(JSON, nullable=True)  # 權限條件（JSON格式）
    restrictions = Column(JSON, nullable=True)  # 權限限制

    # 時間限制
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)

    # 使用限制
    usage_limit = Column(Integer, nullable=True)  # 使用次數限制
    usage_count = Column(Integer, default=0, nullable=False)  # 已使用次數

    # 狀態
    is_active = Column(Boolean, default=True, nullable=False)

    # 關聯
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True)
    role_id = Column(String(36), ForeignKey('roles.id'), nullable=True)

    # 審計
    created_by = Column(String(36), nullable=True)
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # 關聯關係
    user = relationship("User", back_populates="dynamic_permissions")
    role = relationship("Role", back_populates="dynamic_permissions")
    audit_logs = relationship("PermissionAuditLog", back_populates="permission")


class TemporaryAuthorization(UnifiedBaseModel):
    """臨時授權模型"""

    __tablename__ = 'temporary_authorizations'

    # 基本信息
    reason = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

    # 授權詳情
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    delegated_by = Column(String(36), ForeignKey('users.id'), nullable=False)
    role_id = Column(String(36), ForeignKey('roles.id'), nullable=True)

    # 權限範圍
    permissions = Column(JSON, nullable=False)  # 授權的權限列表
    resource_ids = Column(JSON, nullable=True)  # 特定資源ID限制

    # 時間限制
    starts_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # 狀態
    is_active = Column(Boolean, default=True, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(String(36), nullable=True)

    # 使用統計
    usage_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # 關聯
    user = relationship("User", foreign_keys=[user_id], back_populates="temp_auths_received")
    delegator = relationship("User", foreign_keys=[delegated_by], back_populates="temp_auths_given")
    role = relationship("Role", back_populates="temp_auths")

    # 審計
    audit_logs = relationship("PermissionAuditLog", back_populates="temp_auth")


class PermissionAuditLog(UnifiedBaseModel):
    """權限審計日誌"""

    __tablename__ = 'permission_audit_logs'

    # 操作信息
    action = Column(String(50), nullable=False, index=True)  # grant, revoke, use, etc.
    resource_type = Column(String(50), nullable=True, index=True)
    resource_id = Column(String(36), nullable=True)

    # 用戶信息
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    target_user_id = Column(String(36), ForeignKey('users.id'), nullable=True)  # 權限目標用戶

    # 權限信息
    permission_id = Column(String(36), ForeignKey('dynamic_permissions.id'), nullable=True)
    role_id = Column(String(36), ForeignKey('roles.id'), nullable=True)
    temp_auth_id = Column(String(36), ForeignKey('temporary_authorizations.id'), nullable=True)

    # 詳情
    details = Column(JSON, nullable=True)  # 操作詳情
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # 結果
    success = Column(Boolean, nullable=False)
    reason = Column(Text, nullable=True)

    # 關聯
    user = relationship("User", foreign_keys=[user_id], back_populates="audit_logs")
    target_user = relationship("User", foreign_keys=[target_user_id], back_populates="target_audit_logs")
    permission = relationship("DynamicPermission", back_populates="audit_logs")
    temp_auth = relationship("TemporaryAuthorization", back_populates="audit_logs")


class RolePermissionCache(UnifiedBaseModel):
    """角色權限緩存"""

    __tablename__ = 'role_permission_cache'

    # 緩存鍵
    role_id = Column(String(36), ForeignKey('roles.id'), nullable=False, index=True)
    permission_code = Column(String(100), nullable=False, index=True)

    # 緩存數據
    permissions = Column(JSON, nullable=False)  # 緩存的權限列表
    computed_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # 統計
    hit_count = Column(Integer, default=0, nullable=False)
    last_hit_at = Column(DateTime(timezone=True), nullable=True)

    # 關聯
    role = relationship("Role", back_populates="permission_cache")


# 擴展User模型關聯
User.dynamic_permissions = relationship("DynamicPermission", back_populates="user")
User.temp_auths_received = relationship("TemporaryAuthorization", foreign_keys="[TemporaryAuthorization.user_id]", back_populates="user")
User.temp_auths_given = relationship("TemporaryAuthorization", foreign_keys="[TemporaryAuthorization.delegated_by]", back_populates="delegator")
User.audit_logs = relationship("PermissionAuditLog", foreign_keys="[PermissionAuditLog.user_id]", back_populates="user")
User.target_audit_logs = relationship("PermissionAuditLog", foreign_keys="[PermissionAuditLog.target_user_id]", back_populates="target_user")

# 擴展Role模型關聯
Role.dynamic_permissions = relationship("DynamicPermission", back_populates="role")
Role.temp_auths = relationship("TemporaryAuthorization", back_populates="role")
Role.permission_cache = relationship("RolePermissionCache", back_populates="role")


# Pydantic Schemas
class DynamicPermissionBaseSchema(UnifiedSchema):
    """動態權限基礎Schema"""
    name: str = Field(..., min_length=3, max_length=100, description="權限名稱")
    description: Optional[str] = Field(None, description="權限描述")
    resource_type: ResourceType = Field(..., description="資源類型")
    action: ResourceAction = Field(..., description="操作類型")
    level: PermissionLevel = Field(..., description="權限等級")
    conditions: Optional[Dict[str, Any]] = Field(None, description="權限條件")
    restrictions: Optional[Dict[str, Any]] = Field(None, description="權限限制")
    valid_from: Optional[datetime] = Field(None, description="生效時間")
    valid_until: Optional[datetime] = Field(None, description="失效時間")
    usage_limit: Optional[int] = Field(None, ge=0, description="使用次數限制")


class DynamicPermissionCreateSchema(DynamicPermissionBaseSchema):
    """創建動態權限Schema"""
    user_id: Optional[str] = Field(None, description="用戶ID")
    role_id: Optional[str] = Field(None, description="角色ID")

    if PYDANTIC_V2:
        @field_validator('user_id', 'role_id')
        @classmethod
        def validate_target(cls, v, info):
            # Check if at least one of user_id or role_id is provided
            values = info.data if hasattr(info, 'data') else {}
            other_field = 'role_id' if info.field_name == 'user_id' else 'user_id'
            if not v and not values.get(other_field):
                raise ValueError('必須指定用戶ID或角色ID其中一個')
            return v
    else:
        @validator('user_id', 'role_id')
        def validate_target(cls, v, values, field):
            if not v and not values.get('role_id' if field.name == 'user_id' else 'user_id'):
                raise ValueError('必須指定用戶ID或角色ID其中一個')
            return v


class DynamicPermissionUpdateSchema(UnifiedSchema):
    """更新動態權限Schema"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    restrictions: Optional[Dict[str, Any]] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    usage_limit: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class DynamicPermissionResponseSchema(DynamicPermissionBaseSchema):
    """動態權限響應Schema"""
    usage_count: int
    is_active: bool
    user_id: Optional[str] = None
    role_id: Optional[str] = None
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TemporaryAuthorizationBaseSchema(UnifiedSchema):
    """臨時授權基礎Schema"""
    reason: str = Field(..., min_length=10, max_length=500, description="授權原因")
    description: Optional[str] = Field(None, description="詳細描述")
    permissions: List[str] = Field(..., min_items=1, description="授權權限列表")
    resource_ids: Optional[List[str]] = Field(None, description="資源ID限制")
    starts_at: datetime = Field(..., description="開始時間")
    expires_at: datetime = Field(..., description="結束時間")


class TemporaryAuthorizationCreateSchema(TemporaryAuthorizationBaseSchema):
    """創建臨時授權Schema"""
    user_id: str = Field(..., description="授權用戶ID")
    role_id: Optional[str] = Field(None, description="角色ID")

    if PYDANTIC_V2:
        @field_validator('expires_at')
        @classmethod
        def validate_duration(cls, v, info):
            values = info.data if hasattr(info, 'data') else {}
            if 'starts_at' in values and v <= values['starts_at']:
                raise ValueError('結束時間必須晚於開始時間')
            # 限制最長授權時間為30天
            if 'starts_at' in values:
                duration = v - values['starts_at']
                if duration.days > 30:
                    raise ValueError('臨時授權最長不能超過30天')
            return v
    else:
        @validator('expires_at')
        def validate_duration(cls, v, values):
            if 'starts_at' in values and v <= values['starts_at']:
                raise ValueError('結束時間必須晚於開始時間')
            # 限制最長授權時間為30天
            if 'starts_at' in values:
                duration = v - values['starts_at']
                if duration.days > 30:
                    raise ValueError('臨時授權最長不能超過30天')
            return v


class TemporaryAuthorizationResponseSchema(TemporaryAuthorizationBaseSchema):
    """臨時授權響應Schema"""
    id: str
    user_id: str
    delegated_by: str
    role_id: Optional[str] = None
    is_active: bool
    is_revoked: bool
    usage_count: int
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PermissionCheckSchema(BaseModel):
    """權限檢查Schema"""
    resource_type: ResourceType = Field(..., description="資源類型")
    action: ResourceAction = Field(..., description="操作類型")
    resource_id: Optional[str] = Field(None, description="資源ID")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


class PermissionResultSchema(BaseModel):
    """權限檢查結果Schema"""
    granted: bool = Field(..., description="是否授權")
    reason: Optional[str] = Field(None, description="拒絕原因")
    source: str = Field(..., description="權限來源")
    conditions: Optional[Dict[str, Any]] = Field(None, description="附加條件")
    expires_at: Optional[datetime] = Field(None, description="權限過期時間")


class AuditLogQuerySchema(BaseModel):
    """審計日誌查詢Schema"""
    user_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    page: int = Field(1, ge=1)
    limit: int = Field(50, ge=1, le=100)


class AuditLogResponseSchema(BaseModel):
    """審計日誌響應Schema"""
    id: str
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    user_id: str
    target_user_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    success: bool
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
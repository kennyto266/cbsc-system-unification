"""
认证模型
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    DEVELOPER = "developer"
    USER = "user"
    READONLY = "readonly"

class GrantType(str, Enum):
    """授权类型枚举"""
    CLIENT_CREDENTIALS = "client_credentials"
    AUTHORIZATION_CODE = "authorization_code"
    REFRESH_TOKEN = "refresh_token"

class User(BaseModel):
    """用户"""
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, description="全名")
    role: UserRole = Field(default=UserRole.USER, description="用户角色")
    is_active: bool = Field(default=True, description="是否激活")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")

class UserCreate(BaseModel):
    """创建用户请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=8, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    role: UserRole = Field(default=UserRole.USER, description="用户角色")

    @validator('username')
    def username_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('用户名不能为空')
        return v.strip()

    @validator('password')
    def password_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        # 可以添加更多密码强度检查
        return v

class UserUpdate(BaseModel):
    """更新用户请求"""
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    role: Optional[UserRole] = Field(None, description="用户角色")
    is_active: Optional[bool] = Field(None, description="是否激活")

class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")

class TokenRequest(BaseModel):
    """Token请求"""
    grant_type: GrantType = Field(..., description="授权类型")
    client_id: str = Field(..., description="客户端ID")
    client_secret: str = Field(..., description="客户端密钥")
    scope: Optional[str] = Field(None, description="权限范围")
    refresh_token: Optional[str] = Field(None, description="刷新令牌")

class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    refresh_token: Optional[str] = Field(None, description="刷新令牌")
    scope: Optional[str] = Field(None, description="权限范围")

class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="刷新令牌")

class TokenData(BaseModel):
    """Token数据"""
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    role: UserRole = Field(..., description="用户角色")
    scopes: List[str] = Field(default=[], description="权限范围")
    exp: Optional[int] = Field(None, description="过期时间")

class Permission(BaseModel):
    """权限"""
    id: str = Field(..., description="权限ID")
    name: str = Field(..., description="权限名称")
    resource: str = Field(..., description="资源")
    action: str = Field(..., description="操作")
    description: Optional[str] = Field(None, description="权限描述")

class Scope(BaseModel):
    """权限范围"""
    name: str = Field(..., description="范围名称")
    description: str = Field(..., description="范围描述")
    permissions: List[Permission] = Field(default=[], description="包含的权限")

class APIUserInfo(BaseModel):
    """API用户信息"""
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    role: UserRole = Field(..., description="用户角色")
    permissions: List[str] = Field(default=[], description="权限列表")
    api_key_id: Optional[str] = Field(None, description="API密钥ID")

class UserStats(BaseModel):
    """用户统计信息"""
    total_users: int = Field(..., description="用户总数")
    active_users: int = Field(..., description="活跃用户数")
    new_users_today: int = Field(..., description="今日新增用户")
    users_by_role: Dict[str, int] = Field(default={}, description="按角色分组的用户数")
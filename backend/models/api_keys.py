"""
API密钥模型
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class APIKeyStatus(str, Enum):
    """API密钥状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    REVOKED = "revoked"

class APIKeyPermission(str, Enum):
    """API密钥权限枚举"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    FULL_ACCESS = "full_access"

class APIKey(BaseModel):
    """API密钥"""
    id: str = Field(..., description="API密钥ID")
    name: str = Field(..., description="密钥名称")
    key_hash: str = Field(..., description="密钥哈希值")
    key_prefix: str = Field(..., description="密钥前缀（用于显示）")
    user_id: str = Field(..., description="所属用户ID")
    permissions: List[APIKeyPermission] = Field(default=[], description="权限列表")
    allowed_ips: Optional[List[str]] = Field(None, description="允许的IP地址列表")
    rate_limit: Optional[int] = Field(None, description="速率限制（请求/分钟）")
    status: APIKeyStatus = Field(default=APIKeyStatus.ACTIVE, description="状态")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

class APIKeyCreate(BaseModel):
    """创建API密钥请求"""
    name: str = Field(..., min_length=1, max_length=100, description="密钥名称")
    permissions: List[APIKeyPermission] = Field(default=[APIKeyPermission.READ], description="权限列表")
    allowed_ips: Optional[List[str]] = Field(None, description="允许的IP地址列表")
    rate_limit: Optional[int] = Field(None, ge=1, le=10000, description="速率限制（请求/分钟）")
    expires_at: Optional[datetime] = Field(None, description="过期时间")

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('密钥名称不能为空')
        return v.strip()

    @validator('allowed_ips')
    def validate_ips(cls, v):
        if v is not None:
            # 简单的IP格式验证，实际应用中可能需要更严格的验证
            for ip in v:
                if not ip.strip():
                    raise ValueError('IP地址不能为空')
        return v

class APIKeyUpdate(BaseModel):
    """更新API密钥请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="密钥名称")
    permissions: Optional[List[APIKeyPermission]] = Field(None, description="权限列表")
    allowed_ips: Optional[List[str]] = Field(None, description="允许的IP地址列表")
    rate_limit: Optional[int] = Field(None, ge=1, le=10000, description="速率限制（请求/分钟）")
    status: Optional[APIKeyStatus] = Field(None, description="状态")
    expires_at: Optional[datetime] = Field(None, description="过期时间")

class APIKeyResponse(BaseModel):
    """API密钥响应"""
    id: str = Field(..., description="API密钥ID")
    name: str = Field(..., description="密钥名称")
    key: str = Field(..., description="完整API密钥（仅在创建时返回）")
    key_prefix: str = Field(..., description="密钥前缀")
    permissions: List[APIKeyPermission] = Field(default=[], description="权限列表")
    allowed_ips: Optional[List[str]] = Field(None, description="允许的IP地址列表")
    rate_limit: Optional[int] = Field(None, description="速率限制（请求/分钟）")
    status: APIKeyStatus = Field(default=APIKeyStatus.ACTIVE, description="状态")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    created_at: datetime = Field(..., description="创建时间")

class APIKeyInfo(BaseModel):
    """API密钥信息（不包含完整密钥）"""
    id: str = Field(..., description="API密钥ID")
    name: str = Field(..., description="密钥名称")
    key_prefix: str = Field(..., description="密钥前缀")
    permissions: List[APIKeyPermission] = Field(default=[], description="权限列表")
    allowed_ips: Optional[List[str]] = Field(None, description="允许的IP地址列表")
    rate_limit: Optional[int] = Field(None, description="速率限制（请求/分钟）")
    status: APIKeyStatus = Field(default=APIKeyStatus.ACTIVE, description="状态")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

class APIKeyUsage(BaseModel):
    """API密钥使用情况"""
    api_key_id: str = Field(..., description="API密钥ID")
    date: datetime = Field(..., description="日期")
    request_count: int = Field(..., description="请求数量")
    success_count: int = Field(..., description="成功请求数量")
    error_count: int = Field(..., description="错误请求数量")
    avg_response_time: Optional[float] = Field(None, description="平均响应时间（毫秒）")

class APIKeyStats(BaseModel):
    """API密钥统计信息"""
    total_keys: int = Field(..., description="总密钥数")
    active_keys: int = Field(..., description="活跃密钥数")
    expired_keys: int = Field(..., description="过期密钥数")
    suspended_keys: int = Field(..., description="暂停密钥数")
    total_requests_today: int = Field(..., description="今日总请求数")
    keys_by_user: Dict[str, int] = Field(default={}, description="按用户分组的密钥数")

class APIKeyActivity(BaseModel):
    """API密钥活动记录"""
    id: str = Field(..., description="活动记录ID")
    api_key_id: str = Field(..., description="API密钥ID")
    action: str = Field(..., description="操作类型")
    ip_address: str = Field(..., description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    endpoint: str = Field(..., description="请求端点")
    method: str = Field(..., description="HTTP方法")
    status_code: int = Field(..., description="响应状态码")
    response_time: Optional[int] = Field(None, description="响应时间（毫秒）")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
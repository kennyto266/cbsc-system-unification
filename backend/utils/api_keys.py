"""
API密钥工具模块 - API密钥生成、验证和管理工具函数
"""

import secrets
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import logging
import ipaddress
import re

try:
    from config.api_config import settings
    from models.api_keys import (
        APIKey, APIKeyCreate, APIKeyPermission, APIKeyStatus
    )
    from utils.auth import AuthenticationError
except ImportError:
    # Fallback for different import paths
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config.api_config import settings
    from models.api_keys import (
        APIKey, APIKeyCreate, APIKeyPermission, APIKeyStatus
    )
    from utils.auth import AuthenticationError

logger = logging.getLogger(__name__)


class APIKeyError(Exception):
    """API密钥错误异常"""
    pass


class RateLimitError(Exception):
    """速率限制错误异常"""
    pass


def generate_api_key() -> Tuple[str, str]:
    """
    生成新的API密钥

    Returns:
        (api_key, key_hash) 元组，包含完整密钥和用于存储的哈希值

    Raises:
        APIKeyError: 当生成密钥失败时抛出
    """
    try:
        # 生成随机字节串
        random_bytes = secrets.token_bytes(settings.API_KEY_LENGTH)

        # 转换为base64字符串并去除填充字符
        api_key = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')

        # 添加前缀
        full_api_key = f"{settings.API_KEY_PREFIX}{api_key}"

        # 创建哈希值用于存储
        key_hash = hashlib.sha256(full_api_key.encode('utf-8')).hexdigest()

        logger.info(f"生成API密钥成功，前缀: {full_api_key[:8]}...")
        return full_api_key, key_hash

    except Exception as e:
        logger.error(f"生成API密钥失败: {e}")
        raise APIKeyError(f"生成API密钥失败: {e}")


def get_api_key_prefix(api_key: str) -> str:
    """
    获取API密钥的前缀用于显示

    Args:
        api_key: 完整API密钥

    Returns:
        API密钥前缀（显示前8位和后4位）
    """
    if len(api_key) < 12:
        return api_key[:4]

    return f"{api_key[:8]}...{api_key[-4:]}"


def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """
    验证API密钥

    Args:
        api_key: 提供的API密钥
        stored_hash: 存储的密钥哈希值

    Returns:
        验证是否成功
    """
    try:
        if not api_key or not stored_hash:
            return False

        # 计算提供密钥的哈希值
        computed_hash = hashlib.sha256(api_key.encode('utf-8')).hexdigest()

        # 使用恒定时间比较防止时序攻击
        return hmac.compare_digest(computed_hash, stored_hash)

    except Exception as e:
        logger.error(f"验证API密钥失败: {e}")
        return False


def validate_api_key_permissions(
    api_key_permissions: List[APIKeyPermission],
    required_permission: str
) -> bool:
    """
    验证API密钥是否有指定权限

    Args:
        api_key_permissions: API密钥的权限列表
        required_permission: 需要的权限

    Returns:
        是否有权限
    """
    # 转换为字符串进行比较
    permission_strs = [perm.value for perm in api_key_permissions]

    # 完全访问权限
    if APIKeyPermission.FULL_ACCESS.value in permission_strs:
        return True

    # 管理员权限
    if APIKeyPermission.ADMIN.value in permission_strs:
        return True

    # 检查具体权限
    return required_permission in permission_strs


def check_ip_whitelist(
    client_ip: str,
    allowed_ips: Optional[List[str]]
) -> bool:
    """
    检查客户端IP是否在白名单中

    Args:
        client_ip: 客户端IP地址
        allowed_ips: 允许的IP地址列表

    Returns:
        IP是否被允许
    """
    if not allowed_ips:
        return True  # 没有IP限制

    try:
        client_ip_obj = ipaddress.ip_address(client_ip)

        for allowed_ip in allowed_ips:
            try:
                # 支持单个IP和CIDR网段
                if '/' in allowed_ip:
                    allowed_ip_obj = ipaddress.ip_network(allowed_ip, strict=False)
                else:
                    allowed_ip_obj = ipaddress.ip_address(allowed_ip)

                if client_ip_obj == allowed_ip_obj or (
                    isinstance(allowed_ip_obj, ipaddress.IPv4Network) and
                    client_ip_obj in allowed_ip_obj
                ):
                    return True
            except ValueError:
                logger.warning(f"无效的IP地址格式: {allowed_ip}")
                continue

        return False

    except ValueError:
        logger.warning(f"无效的客户端IP地址: {client_ip}")
        return False


def validate_api_key_status(
    status: APIKeyStatus,
    expires_at: Optional[datetime] = None
) -> bool:
    """
    验证API密钥状态是否有效

    Args:
        status: API密钥状态
        expires_at: 过期时间

    Returns:
        密钥是否有效
    """
    if status != APIKeyStatus.ACTIVE:
        return False

    # 检查是否过期
    if expires_at and datetime.utcnow() > expires_at:
        return False

    return True


def calculate_rate_limit_key(
    api_key_id: str,
    endpoint: str,
    window_minutes: int = 1
) -> str:
    """
    计算速率限制的缓存键

    Args:
        api_key_id: API密钥ID
        endpoint: API端点
        window_minutes: 时间窗口（分钟）

    Returns:
        速率限制键
    """
    current_time = datetime.utcnow()
    window_start = current_time.replace(
        minute=(current_time.minute // window_minutes) * window_minutes,
        second=0,
        microsecond=0
    )

    key_data = f"rate_limit:{api_key_id}:{endpoint}:{window_start.timestamp()}"
    return hashlib.md5(key_data.encode()).hexdigest()


def check_rate_limit(
    api_key_id: str,
    endpoint: str,
    limit: int,
    current_count: int
) -> bool:
    """
    检查是否超过速率限制

    Args:
        api_key_id: API密钥ID
        endpoint: API端点
        limit: 限制数量
        current_count: 当前计数

    Returns:
        是否允许请求
    """
    if limit <= 0:
        return True  # 无限制

    if current_count >= limit:
        logger.warning(
            f"速率限制触发 - API密钥ID: {api_key_id}, "
            f"端点: {endpoint}, 当前计数: {current_count}, 限制: {limit}"
        )
        return False

    return True


def get_rate_limit_headers(
    limit: int,
    remaining: int,
    reset_time: datetime
) -> Dict[str, str]:
    """
    获取速率限制相关的HTTP头

    Args:
        limit: 限制数量
        remaining: 剩余请求数
        reset_time: 重置时间

    Returns:
        HTTP头字典
    """
    reset_timestamp = int(reset_time.timestamp())

    return {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(reset_timestamp)
    }


def extract_api_key_from_header(authorization: str) -> Optional[str]:
    """
    从HTTP头中提取API密钥

    Args:
        authorization: Authorization头值

    Returns:
        API密钥字符串，如果格式不正确则返回None
    """
    if not authorization:
        return None

    # 支持Bearer格式和直接API密钥格式
    if authorization.startswith("Bearer "):
        return authorization[7:]
    elif authorization.startswith("ApiKey "):
        return authorization[7:]
    elif authorization.startswith(settings.API_KEY_PREFIX):
        return authorization
    else:
        return None


def sanitize_api_key_for_logging(api_key: str) -> str:
    """
    为日志记录清理API密钥

    Args:
        api_key: 原始API密钥

    Returns:
        清理后的密钥（只显示前缀）
    """
    if len(api_key) < 12:
        return "****"

    return f"{api_key[:8]}...****"


def validate_api_key_request(request_data: APIKeyCreate) -> Tuple[bool, str]:
    """
    验证API密钥创建请求

    Args:
        request_data: 创建请求数据

    Returns:
        (是否有效, 错误消息) 元组
    """
    # 验证名称
    if not request_data.name or not request_data.name.strip():
        return False, "API密钥名称不能为空"

    if len(request_data.name) > 100:
        return False, "API密钥名称不能超过100个字符"

    # 验证权限
    if not request_data.permissions:
        return False, "至少需要指定一个权限"

    # 验证速率限制
    if request_data.rate_limit is not None and (
        request_data.rate_limit < 1 or request_data.rate_limit > 10000
    ):
        return False, "速率限制必须在1-10000之间"

    # 验证IP地址列表
    if request_data.allowed_ips:
        for ip in request_data.allowed_ips:
            try:
                # 验证单个IP或CIDR网段
                if '/' in ip:
                    ipaddress.ip_network(ip, strict=False)
                else:
                    ipaddress.ip_address(ip)
            except ValueError:
                return False, f"无效的IP地址格式: {ip}"

    return True, ""


def create_api_key_response(
    api_key_obj: APIKey,
    full_api_key: str
) -> Dict[str, Any]:
    """
    创建API密钥响应数据

    Args:
        api_key_obj: API密钥对象
        full_api_key: 完整API密钥

    Returns:
        响应数据字典
    """
    return {
        "id": api_key_obj.id,
        "name": api_key_obj.name,
        "key": full_api_key,
        "key_prefix": api_key_obj.key_prefix,
        "permissions": [perm.value for perm in api_key_obj.permissions],
        "allowed_ips": api_key_obj.allowed_ips,
        "rate_limit": api_key_obj.rate_limit,
        "status": api_key_obj.status.value,
        "expires_at": api_key_obj.expires_at.isoformat() if api_key_obj.expires_at else None,
        "created_at": api_key_obj.created_at.isoformat()
    }


def update_last_used_time(api_key_id: str) -> None:
    """
    更新API密钥最后使用时间

    Args:
        api_key_id: API密钥ID
    """
    try:
        # 这里应该更新数据库中的最后使用时间
        # 由于这是工具函数，实际的数据库更新应该在服务层处理
        logger.debug(f"更新API密钥最后使用时间: {api_key_id}")
    except Exception as e:
        logger.error(f"更新API密钥最后使用时间失败: {e}")


def get_permission_hierarchy() -> Dict[APIKeyPermission, List[APIKeyPermission]]:
    """
    获取权限层次结构

    Returns:
        权限层次字典，高权限包含低权限
    """
    return {
        APIKeyPermission.FULL_ACCESS: [
            APIKeyPermission.ADMIN,
            APIKeyPermission.WRITE,
            APIKeyPermission.READ
        ],
        APIKeyPermission.ADMIN: [
            APIKeyPermission.WRITE,
            APIKeyPermission.READ
        ],
        APIKeyPermission.WRITE: [
            APIKeyPermission.READ
        ],
        APIKeyPermission.READ: []
    }


def has_higher_permission(
    current_permission: APIKeyPermission,
    target_permission: APIKeyPermission
) -> bool:
    """
    检查当前权限是否高于或等于目标权限

    Args:
        current_permission: 当前权限
        target_permission: 目标权限

    Returns:
        是否有足够权限
    """
    if current_permission == target_permission:
        return True

    hierarchy = get_permission_hierarchy()
    return target_permission in hierarchy.get(current_permission, [])


def get_permission_description(permission: APIKeyPermission) -> str:
    """
    获取权限描述

    Args:
        permission: 权限枚举

    Returns:
        权限描述字符串
    """
    descriptions = {
        APIKeyPermission.READ: "只读权限，可以查看数据",
        APIKeyPermission.WRITE: "读写权限，可以创建和修改数据",
        APIKeyPermission.ADMIN: "管理员权限，可以执行管理操作",
        APIKeyPermission.FULL_ACCESS: "完全访问权限，拥有所有功能"
    }

    return descriptions.get(permission, "未知权限")


# 常用的错误消息
API_KEY_ERRORS = {
    "INVALID_API_KEY": "API密钥无效",
    "API_KEY_EXPIRED": "API密钥已过期",
    "API_KEY_INACTIVE": "API密钥已被禁用",
    "INSUFFICIENT_PERMISSIONS": "API密钥权限不足",
    "IP_NOT_ALLOWED": "客户端IP不在允许列表中",
    "RATE_LIMIT_EXCEEDED": "API调用频率超出限制",
    "DUPLICATE_KEY_NAME": "API密钥名称已存在",
    "INVALID_KEY_FORMAT": "API密钥格式无效"
}


def get_api_key_error_message(error_key: str) -> str:
    """
    获取API密钥错误消息

    Args:
        error_key: 错误键

    Returns:
        错误消息字符串
    """
    return API_KEY_ERRORS.get(error_key, "未知错误")
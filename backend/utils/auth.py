"""
认证工具模块 - JWT令牌处理和认证相关工具函数
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
import secrets
import hashlib
import logging
from passlib.context import CryptContext

try:
    from config.api_config import settings
    from models.auth import TokenData, User, UserRole
except ImportError:
    # Fallback for different import paths
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config.api_config import settings
    from models.auth import TokenData, User, UserRole

logger = logging.getLogger(__name__)

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationError(Exception):
    """认证错误异常"""
    pass


class AuthorizationError(Exception):
    """授权错误异常"""
    pass


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建访问令牌

    Args:
        data: 要编码到令牌中的数据
        expires_delta: 过期时间增量，默认使用配置中的过期时间

    Returns:
        JWT访问令牌字符串

    Raises:
        AuthenticationError: 当JWT密钥未配置时抛出
    """
    try:
        if not settings.JWT_SECRET_KEY:
            raise AuthenticationError("JWT密钥未配置")

        to_encode = data.copy()

        # 设置过期时间
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire})

        # 创建JWT令牌
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        logger.info(f"创建访问令牌成功，用户ID: {data.get('sub', 'unknown')}")
        return encoded_jwt

    except Exception as e:
        logger.error(f"创建访问令牌失败: {e}")
        raise AuthenticationError(f"创建访问令牌失败: {e}")


def create_refresh_token(
    data: Dict[str, Any]
) -> str:
    """
    创建刷新令牌

    Args:
        data: 要编码到令牌中的数据

    Returns:
        JWT刷新令牌字符串

    Raises:
        AuthenticationError: 当JWT密钥未配置时抛出
    """
    try:
        if not settings.JWT_SECRET_KEY:
            raise AuthenticationError("JWT密钥未配置")

        to_encode = data.copy()

        # 刷新令牌过期时间更长
        expire = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

        to_encode.update({
            "exp": expire,
            "type": "refresh"
        })

        # 创建刷新令牌
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        logger.info(f"创建刷新令牌成功，用户ID: {data.get('sub', 'unknown')}")
        return encoded_jwt

    except Exception as e:
        logger.error(f"创建刷新令牌失败: {e}")
        raise AuthenticationError(f"创建刷新令牌失败: {e}")


def verify_token(token: str) -> TokenData:
    """
    验证并解析JWT令牌

    Args:
        token: JWT令牌字符串

    Returns:
        TokenData对象，包含令牌中的用户信息

    Raises:
        AuthenticationError: 令牌无效、过期或验证失败时抛出
    """
    try:
        if not settings.JWT_SECRET_KEY:
            raise AuthenticationError("JWT密钥未配置")

        # 解码JWT令牌
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # 提取用户信息
        user_id: str = payload.get("sub")
        if not user_id:
            raise AuthenticationError("令牌中缺少用户ID")

        username: str = payload.get("username")
        if not username:
            raise AuthenticationError("令牌中缺少用户名")

        role: str = payload.get("role", UserRole.USER)
        scopes: list = payload.get("scopes", [])
        exp: Optional[int] = payload.get("exp")

        # 创建TokenData对象
        token_data = TokenData(
            user_id=user_id,
            username=username,
            role=UserRole(role),
            scopes=scopes,
            exp=exp
        )

        logger.debug(f"令牌验证成功，用户ID: {user_id}, 角色: {role}")
        return token_data

    except jwt.ExpiredSignatureError:
        logger.warning("令牌已过期")
        raise AuthenticationError("令牌已过期")

    except jwt.JWTError as e:
        logger.warning(f"令牌验证失败: {e}")
        raise AuthenticationError(f"令牌验证失败: {e}")

    except Exception as e:
        logger.error(f"验证令牌时发生错误: {e}")
        raise AuthenticationError(f"验证令牌失败: {e}")


def hash_password(password: str) -> str:
    """
    哈希密码

    Args:
        password: 明文密码

    Returns:
        哈希后的密码字符串
    """
    try:
        hashed_password = pwd_context.hash(password)
        logger.debug("密码哈希成功")
        return hashed_password
    except Exception as e:
        logger.error(f"密码哈希失败: {e}")
        raise AuthenticationError(f"密码哈希失败: {e}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        密码是否匹配
    """
    try:
        is_valid = pwd_context.verify(plain_password, hashed_password)
        logger.debug(f"密码验证结果: {is_valid}")
        return is_valid
    except Exception as e:
        logger.error(f"密码验证失败: {e}")
        return False


def create_user_token_data(user: User) -> Dict[str, Any]:
    """
    为用户创建令牌数据

    Args:
        user: 用户对象

    Returns:
        用于创建令牌的数据字典
    """
    return {
        "sub": user.id,
        "username": user.username,
        "role": user.role.value,
        "scopes": get_role_scopes(user.role)
    }


def get_role_scopes(role: UserRole) -> list:
    """
    根据用户角色获取权限范围

    Args:
        role: 用户角色

    Returns:
        权限范围列表
    """
    scope_mapping = {
        UserRole.ADMIN: ["admin", "read", "write", "delete"],
        UserRole.DEVELOPER: ["read", "write", "api_access"],
        UserRole.USER: ["read", "profile"],
        UserRole.READONLY: ["read"]
    }

    return scope_mapping.get(role, ["read"])


def check_permission(user_role: UserRole, required_permission: str) -> bool:
    """
    检查用户是否有指定权限

    Args:
        user_role: 用户角色
        required_permission: 需要的权限

    Returns:
        是否有权限
    """
    user_scopes = get_role_scopes(user_role)

    # 管理员有所有权限
    if user_role == UserRole.ADMIN:
        return True

    return required_permission in user_scopes


def validate_token_scopes(token_data: TokenData, required_scopes: list) -> bool:
    """
    验证令牌是否具有所需的作用域

    Args:
        token_data: 令牌数据
        required_scopes: 需要的作用域列表

    Returns:
        是否有足够的权限
    """
    user_scopes = set(token_data.scopes)
    required_scopes_set = set(required_scopes)

    # 管理员有所有权限
    if token_data.role == UserRole.ADMIN:
        return True

    # 检查是否包含所需的作用域
    return required_scopes_set.issubset(user_scopes)


def extract_token_from_header(authorization: str) -> Optional[str]:
    """
    从Authorization头中提取Bearer令牌

    Args:
        authorization: Authorization头值

    Returns:
        JWT令牌字符串，如果格式不正确则返回None
    """
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


def is_token_expired(token_data: TokenData) -> bool:
    """
    检查令牌是否已过期

    Args:
        token_data: 令牌数据

    Returns:
        是否已过期
    """
    if not token_data.exp:
        return True

    current_time = datetime.utcnow().timestamp()
    return current_time > token_data.exp


def generate_client_credentials() -> tuple:
    """
    生成客户端凭据

    Returns:
        (client_id, client_secret) 元组
    """
    client_id = f"client_{secrets.token_urlsafe(16)}"
    client_secret = secrets.token_urlsafe(32)

    logger.info(f"生成客户端凭据成功，客户端ID: {client_id}")
    return client_id, client_secret


def verify_client_credentials(
    client_id: str,
    client_secret: str,
    stored_client_hash: str
) -> bool:
    """
    验证客户端凭据

    Args:
        client_id: 客户端ID
        client_secret: 客户端密钥
        stored_client_hash: 存储的客户端凭据哈希

    Returns:
        验证是否成功
    """
    try:
        # 创建验证字符串
        verify_string = f"{client_id}:{client_secret}"
        verify_hash = hashlib.sha256(verify_string.encode()).hexdigest()

        return verify_hash == stored_client_hash
    except Exception as e:
        logger.error(f"验证客户端凭据失败: {e}")
        return False


def hash_client_credentials(client_id: str, client_secret: str) -> str:
    """
    哈希客户端凭据用于存储

    Args:
        client_id: 客户端ID
        client_secret: 客户端密钥

    Returns:
        哈希后的凭据字符串
    """
    credentials_string = f"{client_id}:{client_secret}"
    return hashlib.sha256(credentials_string.encode()).hexdigest()


# 常用的错误消息
AUTH_ERRORS = {
    "INVALID_CREDENTIALS": "用户名或密码错误",
    "TOKEN_EXPIRED": "令牌已过期，请重新登录",
    "TOKEN_INVALID": "令牌无效",
    "INSUFFICIENT_PERMISSIONS": "权限不足",
    "CLIENT_NOT_FOUND": "客户端不存在",
    "CLIENT_INACTIVE": "客户端已被禁用",
    "JWT_KEY_MISSING": "JWT密钥未配置",
    "PASSWORD_HASH_ERROR": "密码哈希失败"
}


def get_auth_error_message(error_key: str) -> str:
    """
    获取认证错误消息

    Args:
        error_key: 错误键

    Returns:
        错误消息字符串
    """
    return AUTH_ERRORS.get(error_key, "未知错误")
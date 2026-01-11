"""
认证API模块 - 提供OAuth2/JWT认证相关接口
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import logging
import hashlib

try:
    from models.auth import (
        TokenRequest, TokenResponse, RefreshTokenRequest,
        UserCreate, UserLogin, User, UserRole, GrantType
    )
    from models.api_keys import APIKey, APIKeyCreate, APIKeyStatus, APIKeyPermission
    from utils.auth import (
        create_access_token, create_refresh_token, verify_token,
        hash_password, verify_password, create_user_token_data,
        verify_client_credentials, hash_client_credentials,
        generate_client_credentials, AuthenticationError,
        get_auth_error_message
    )
    from utils.api_keys import (
        generate_api_key, verify_api_key, validate_api_key_status,
        get_api_key_prefix, create_api_key_response,
        validate_api_key_request, APIKeyError
    )
    from config.api_config import settings
except ImportError:
    # Fallback for different import paths
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models.auth import (
        TokenRequest, TokenResponse, RefreshTokenRequest,
        UserCreate, UserLogin, User, UserRole, GrantType
    )
    from models.api_keys import APIKey, APIKeyCreate, APIKeyStatus, APIKeyPermission
    from utils.auth import (
        create_access_token, create_refresh_token, verify_token,
        hash_password, verify_password, create_user_token_data,
        verify_client_credentials, hash_client_credentials,
        generate_client_credentials, AuthenticationError,
        get_auth_error_message
    )
    from utils.api_keys import (
        generate_api_key, verify_api_key, validate_api_key_status,
        get_api_key_prefix, create_api_key_response,
        validate_api_key_request, APIKeyError
    )
    from config.api_config import settings

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

# 模拟用户数据 (使用预哈希的密码)
MOCK_USERS = [
    {
        "id": "user_1",
        "username": "admin",
        "email": "admin@cbsc.com",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj1bp.CmU.1K",  # admin123
        "full_name": "系统管理员",
        "role": UserRole.ADMIN,
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "last_login": None
    },
    {
        "id": "user_2",
        "username": "developer",
        "email": "dev@cbsc.com",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj1bp.CmU.1K",  # admin123
        "full_name": "API开发者",
        "role": UserRole.DEVELOPER,
        "is_active": True,
        "created_at": "2024-01-02T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
        "last_login": None
    }
]

# 模拟客户端应用数据 (使用预哈希的凭据)
MOCK_CLIENTS = [
    {
        "id": "test",
        "name": "测试客户端",
        "secret_hash": hashlib.sha256(b"test:test").hexdigest(),
        "scopes": ["read", "write", "api_access"],
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z"
    }
]

# 模拟API密钥数据
MOCK_API_KEYS = []

@router.post("/auth/token")
async def get_token(request: TokenRequest):
    """获取访问令牌 - OAuth2客户端凭据模式"""
    try:
        # 验证授权类型
        if request.grant_type != GrantType.CLIENT_CREDENTIALS:
            raise HTTPException(
                status_code=400,
                detail="不支持的授权类型"
            )

        # 查找客户端
        client = next((c for c in MOCK_CLIENTS if c["id"] == request.client_id), None)
        if not client:
            raise HTTPException(
                status_code=401,
                detail="客户端认证失败"
            )

        # 验证客户端凭据
        if not verify_client_credentials(
            request.client_id,
            request.client_secret,
            client["secret_hash"]
        ):
            raise HTTPException(
                status_code=401,
                detail="客户端认证失败"
            )

        # 检查客户端状态
        if not client["is_active"]:
            raise HTTPException(
                status_code=403,
                detail="客户端已被禁用"
            )

        # 创建访问令牌
        token_data = {
            "sub": f"client:{request.client_id}",
            "username": request.client_id,
            "role": UserRole.DEVELOPER,
            "scopes": request.scope.split() if request.scope else client["scopes"]
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # 记录日志
        logger.info(f"客户端 {request.client_id} 获取访问令牌成功")

        return {
            "success": True,
            "data": {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "refresh_token": refresh_token,
                "scope": request.scope or " ".join(client["scopes"])
            },
            "message": "访问令牌获取成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取访问令牌失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取访问令牌失败"
        )

@router.post("/auth/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """刷新访问令牌"""
    try:
        # 验证刷新令牌
        token_data = verify_token(request.refresh_token)

        # 检查令牌类型
        # 注意：这里简化处理，实际应该在JWT payload中包含type字段

        # 创建新的访问令牌
        new_token_data = {
            "sub": token_data.user_id,
            "username": token_data.username,
            "role": token_data.role,
            "scopes": token_data.scopes
        }

        access_token = create_access_token(new_token_data)

        logger.info(f"用户 {token_data.username} 刷新访问令牌成功")

        return {
            "success": True,
            "data": {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "scope": " ".join(token_data.scopes)
            },
            "message": "访问令牌刷新成功",
            "timestamp": datetime.now().isoformat()
        }

    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"刷新访问令牌失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="刷新访问令牌失败"
        )

@router.post("/auth/login")
async def login(request: UserLogin):
    """用户登录"""
    try:
        # 查找用户
        user = next(
            (u for u in MOCK_USERS if u["username"] == request.username or u["email"] == request.username),
            None
        )

        if not user:
            raise HTTPException(
                status_code=401,
                detail="用户名或密码错误"
            )

        # 验证密码
        if not verify_password(request.password, user["password_hash"]):
            raise HTTPException(
                status_code=401,
                detail="用户名或密码错误"
            )

        # 检查用户状态
        if not user["is_active"]:
            raise HTTPException(
                status_code=403,
                detail="用户账户已被禁用"
            )

        # 创建令牌
        user_obj = User(**user)
        token_data = create_user_token_data(user_obj)

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # 更新最后登录时间
        user["last_login"] = datetime.now().isoformat()

        logger.info(f"用户 {user['username']} 登录成功")

        return {
            "success": True,
            "data": {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "refresh_token": refresh_token,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "full_name": user["full_name"],
                    "role": user["role"].value
                }
            },
            "message": "登录成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户登录失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="登录失败"
        )

@router.post("/auth/register")
async def register(request: UserCreate):
    """用户注册"""
    try:
        # 检查用户名是否已存在
        existing_user = next(
            (u for u in MOCK_USERS if u["username"] == request.username or u["email"] == request.email),
            None
        )

        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="用户名或邮箱已存在"
            )

        # 创建新用户
        new_user = {
            "id": f"user_{uuid.uuid4().hex[:8]}",
            "username": request.username,
            "email": request.email,
            "password_hash": hash_password(request.password),
            "full_name": request.full_name,
            "role": request.role,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_login": None
        }

        MOCK_USERS.append(new_user)

        logger.info(f"用户 {new_user['username']} 注册成功")

        return {
            "success": True,
            "data": {
                "id": new_user["id"],
                "username": new_user["username"],
                "email": new_user["email"],
                "full_name": new_user["full_name"],
                "role": new_user["role"].value,
                "created_at": new_user["created_at"]
            },
            "message": "用户注册成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户注册失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="用户注册失败"
        )

@router.get("/auth/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户信息"""
    try:
        # 验证访问令牌
        token_data = verify_token(credentials.credentials)

        # 如果是客户端令牌
        if token_data.user_id.startswith("client:"):
            client_id = token_data.user_id.split(":", 1)[1]
            client = next((c for c in MOCK_CLIENTS if c["id"] == client_id), None)

            if not client:
                raise HTTPException(status_code=404, detail="客户端不存在")

            return {
                "success": True,
                "data": {
                    "type": "client",
                    "id": client["id"],
                    "name": client["name"],
                    "scopes": token_data.scopes,
                    "role": token_data.role.value
                },
                "message": "获取客户端信息成功",
                "timestamp": datetime.now().isoformat()
            }

        # 如果是用户令牌
        user = next((u for u in MOCK_USERS if u["id"] == token_data.user_id), None)

        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        return {
            "success": True,
            "data": {
                "type": "user",
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"].value,
                "scopes": token_data.scopes,
                "last_login": user["last_login"]
            },
            "message": "获取用户信息成功",
            "timestamp": datetime.now().isoformat()
        }

    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取当前用户信息失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取用户信息失败"
        )

@router.post("/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """用户登出"""
    try:
        # 验证访问令牌
        token_data = verify_token(credentials.credentials)

        # 这里可以添加令牌黑名单逻辑
        # 由于这是简化实现，我们只记录日志

        logger.info(f"用户 {token_data.username} 登出成功")

        return {
            "success": True,
            "message": "登出成功",
            "timestamp": datetime.now().isoformat()
        }

    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"用户登出失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="登出失败"
        )

@router.post("/auth/api-keys")
async def create_api_key(
    request: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """创建API密钥"""
    try:
        # 验证访问令牌
        token_data = verify_token(credentials.credentials)

        # 检查权限
        if "api_access" not in token_data.scopes and token_data.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=403,
                detail="权限不足，无法创建API密钥"
            )

        # 验证请求数据
        api_key_request = APIKeyCreate(**request)
        is_valid, error_message = validate_api_key_request(api_key_request)

        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=error_message
            )

        # 生成API密钥
        full_api_key, key_hash = generate_api_key()
        key_prefix = get_api_key_prefix(full_api_key)

        # 创建API密钥记录
        new_api_key = {
            "id": f"key_{uuid.uuid4().hex[:8]}",
            "name": api_key_request.name,
            "key_hash": key_hash,
            "key_prefix": key_prefix,
            "user_id": token_data.user_id,
            "permissions": api_key_request.permissions,
            "allowed_ips": api_key_request.allowed_ips,
            "rate_limit": api_key_request.rate_limit,
            "status": APIKeyStatus.ACTIVE,
            "expires_at": api_key_request.expires_at.isoformat() if api_key_request.expires_at else None,
            "last_used_at": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        MOCK_API_KEYS.append(new_api_key)

        logger.info(f"用户 {token_data.username} 创建API密钥成功: {key_prefix}")

        return {
            "success": True,
            "data": {
                "id": new_api_key["id"],
                "name": new_api_key["name"],
                "key": full_api_key,  # 只在创建时返回完整密钥
                "key_prefix": new_api_key["key_prefix"],
                "permissions": [perm.value for perm in new_api_key["permissions"]],
                "allowed_ips": new_api_key["allowed_ips"],
                "rate_limit": new_api_key["rate_limit"],
                "status": new_api_key["status"].value,
                "expires_at": new_api_key["expires_at"],
                "created_at": new_api_key["created_at"]
            },
            "message": "API密钥创建成功",
            "timestamp": datetime.now().isoformat()
        }

    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建API密钥失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="创建API密钥失败"
        )

@router.get("/auth/api-keys")
async def list_api_keys(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取API密钥列表"""
    try:
        # 验证访问令牌
        token_data = verify_token(credentials.credentials)

        # 获取用户的API密钥
        user_api_keys = [
            {
                "id": key["id"],
                "name": key["name"],
                "key_prefix": key["key_prefix"],
                "permissions": [perm.value for perm in key["permissions"]],
                "status": key["status"].value,
                "last_used_at": key["last_used_at"],
                "created_at": key["created_at"]
            }
            for key in MOCK_API_KEYS
            if key["user_id"] == token_data.user_id
        ]

        return {
            "success": True,
            "data": user_api_keys,
            "message": "API密钥列表获取成功",
            "timestamp": datetime.now().isoformat()
        }

    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"获取API密钥列表失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取API密钥列表失败"
        )
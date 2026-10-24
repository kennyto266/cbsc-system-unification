"""
CBSC系統統一認證服務
JWT + OAuth2 統一認證機制實現
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import redis
import logging

logger = logging.getLogger(__name__)

class JWTAuthenticationService:
    """JWT認證服務"""

    def __init__(self):
        # JWT配置
        self.SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30分鐘
        self.REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7天

        # 密碼加密上下文
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # Redis連接（用於token黑名單）
        try:
            self.redis_client = redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379"),
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✅ 認證服務Redis連接成功")
        except Exception as e:
            logger.warning(f"⚠️ 認證服務Redis連接失敗: {e}")
            self.redis_client = None

        # 用戶數據庫（生產環境應使用真實數據庫）
        self.users_db = {
            "admin": {
                "username": "admin",
                "email": "admin@cbsc.com",
                "hashed_password": self.get_password_hash("admin123"),
                "disabled": False,
                "roles": ["admin", "user"],
                "permissions": ["read", "write", "delete"],
                "created_at": datetime.now().isoformat()
            },
            "user": {
                "username": "user",
                "email": "user@cbsc.com",
                "hashed_password": self.get_password_hash("user123"),
                "disabled": False,
                "roles": ["user"],
                "permissions": ["read"],
                "created_at": datetime.now().isoformat()
            }
        }

        # Token黑名單（Redis備用）
        self.token_blacklist = set()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """驗證密碼"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """生成密碼哈希"""
        return self.pwd_context.hash(password)

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """驗證用戶"""
        user = self.users_db.get(username)
        if not user:
            return None

        if not self.verify_password(password, user["hashed_password"]):
            return None

        if user.get("disabled"):
            return None

        return user

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """創建訪問令牌"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
            "jti": secrets.token_urlsafe(16)  # JWT ID
        })

        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """創建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": secrets.token_urlsafe(16)
        })

        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """驗證令牌"""
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])

            # 檢查令牌類型
            if payload.get("type") != token_type:
                return None

            # 檢查是否在黑名單中
            jti = payload.get("jti")
            if self.is_token_blacklisted(jti):
                return None

            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None

    def revoke_token(self, jti: str, exp: datetime):
        """撤銷令牌（添加到黑名單）"""
        if self.redis_client:
            # 使用Redis存儲黑名單，設置過期時間
            ttl = int((exp - datetime.utcnow()).total_seconds())
            if ttl > 0:
                self.redis_client.setex(f"blacklist:{jti}", ttl, "revoked")
                logger.info(f"Token {jti} 已添加到黑名單")
        else:
            # 使用內存黑名單
            self.token_blacklist.add(jti)
            logger.info(f"Token {jti} 已添加到內存黑名單")

    def is_token_blacklisted(self, jti: str) -> bool:
        """檢查令牌是否在黑名單中"""
        if self.redis_client:
            return self.redis_client.exists(f"blacklist:{jti}")
        else:
            return jti in self.token_blacklist

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """刷新訪問令牌"""
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None

        # 撤銷舊的刷新令牌
        old_jti = payload.get("jti")
        old_exp = datetime.fromtimestamp(payload.get("exp"))
        self.revoke_token(old_jti, old_exp)

        # 創建新的訪問令牌
        user_data = {
            "sub": payload.get("sub"),
            "username": payload.get("username"),
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", [])
        }

        return self.create_access_token(user_data)

    def get_user_permissions(self, username: str) -> List[str]:
        """獲取用戶權限"""
        user = self.users_db.get(username)
        if not user:
            return []
        return user.get("permissions", [])

    def check_permission(self, username: str, required_permission: str) -> bool:
        """檢查用戶權限"""
        user_permissions = self.get_user_permissions(username)
        return required_permission in user_permissions

class OAuth2Service:
    """OAuth2認證服務"""

    def __init__(self, jwt_service: JWTAuthenticationService):
        self.jwt_service = jwt_service

        # OAuth2客戶端配置
        self.clients = {
            "web_client": {
                "client_id": "cbsc_web_client",
                "client_secret": "web_client_secret",
                "redirect_uris": ["http://localhost:3000/auth/callback"],
                "scopes": ["read", "write"],
                "grant_types": ["authorization_code", "refresh_token"]
            },
            "mobile_client": {
                "client_id": "cbsc_mobile_client",
                "client_secret": "mobile_client_secret",
                "redirect_uris": ["cbscapp://auth/callback"],
                "scopes": ["read"],
                "grant_types": ["authorization_code", "refresh_token"]
            }
        }

        # 授權碼存儲（生產環境應使用數據庫）
        self.authorization_codes = {}

    def generate_authorization_code(self, client_id: str, username: str, scope: List[str]) -> str:
        """生成授權碼"""
        code = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=10)  # 10分鐘過期

        self.authorization_codes[code] = {
            "client_id": client_id,
            "username": username,
            "scope": scope,
            "expires_at": expires_at,
            "used": False
        }

        return code

    def validate_authorization_code(self, code: str, client_id: str) -> Optional[Dict[str, Any]]:
        """驗證授權碼"""
        auth_data = self.authorization_codes.get(code)
        if not auth_data:
            return None

        # 檢查客戶端ID
        if auth_data["client_id"] != client_id:
            return None

        # 檢查過期時間
        if datetime.utcnow() > auth_data["expires_at"]:
            return None

        # 檢查是否已使用
        if auth_data["used"]:
            return None

        # 標記為已使用
        auth_data["used"] = True

        return {
            "username": auth_data["username"],
            "scope": auth_data["scope"]
        }

    def exchange_code_for_tokens(self, code: str, client_id: str, client_secret: str) -> Optional[Dict[str, str]]:
        """授權碼交換令牌"""
        # 驗證客戶端
        client = self.clients.get(client_id)
        if not client or client["client_secret"] != client_secret:
            return None

        # 驗證授權碼
        auth_data = self.validate_authorization_code(code, client_id)
        if not auth_data:
            return None

        username = auth_data["username"]
        scope = auth_data["scope"]

        # 獲取用戶信息
        user = self.jwt_service.users_db.get(username)
        if not user:
            return None

        # 創建令牌
        token_data = {
            "sub": username,
            "username": username,
            "roles": user.get("roles", []),
            "permissions": user.get("permissions", []),
            "scope": scope,
            "client_id": client_id
        }

        access_token = self.jwt_service.create_access_token(token_data)
        refresh_token = self.jwt_service.create_refresh_token({"sub": username})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": self.jwt_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "scope": " ".join(scope)
        }

    def validate_client(self, client_id: str, client_secret: str) -> bool:
        """驗證OAuth2客戶端"""
        client = self.clients.get(client_id)
        return client and client["client_secret"] == client_secret

# 全局認證服務實例
jwt_auth_service = JWTAuthenticationService()
oauth2_service = OAuth2Service(jwt_auth_service)

# 便捷函數
def get_current_user_token(token: str) -> Optional[Dict[str, Any]]:
    """獲取當前用戶令牌信息"""
    return jwt_auth_service.verify_token(token, "access")

def check_user_permission(username: str, permission: str) -> bool:
    """檢查用戶權限"""
    return jwt_auth_service.check_permission(username, permission)
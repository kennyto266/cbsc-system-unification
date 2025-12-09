#!/usr/bin/env python3
"""
WebSocket Authentication Module
WebSocket身份驗證模組
提供JWT token驗證和用戶管理功能
"""

import jwt
import time
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from fastapi import WebSocket, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncio
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """身份驗證錯誤"""
    pass

class AuthorizationError(Exception):
    """授權錯誤"""
    pass

class RateLimitError(Exception):
    """速率限制錯誤"""
    pass

@dataclass
class User:
    """用戶信息"""
    user_id: str
    username: str
    permissions: List[str]
    api_key_hash: Optional[str] = None
    created_at: datetime = None
    last_login: Optional[datetime] = None
    is_active: bool = True

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class ConnectionContext:
    """連接上下文"""
    user: User
    permissions: List[str]
    connected_at: datetime
    client_ip: str
    user_agent: str
    subscription_filters: Dict[str, Any] = None
    last_activity: datetime = None

    def __post_init__(self):
        if self.last_activity is None:
            self.last_activity = datetime.now()
        if self.subscription_filters is None:
            self.subscription_filters = {}

class WebSocketAuthenticator:
    """WebSocket身份驗證器"""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expiry = timedelta(hours=24)
        self.users = {}  # user_id -> User
        self.api_keys = {}  # api_key_hash -> User

        # 速率限制
        self.rate_limiters = defaultdict(lambda: deque(maxlen=100))  # IP -> timestamps
        self.max_connections_per_minute = 30
        self.max_connections_per_hour = 100

        # 初始化測試用戶
        self._initialize_test_users()

    def _initialize_test_users(self):
        """初始化測試用戶"""
        # 創建測試用戶
        test_users = [
            User(
                user_id="user_001",
                username="trader_demo",
                permissions=["realtime_data", "historical_data", "trading"],
                is_active=True
            ),
            User(
                user_id="user_002",
                username="viewer_demo",
                permissions=["realtime_data"],
                is_active=True
            ),
            User(
                user_id="user_003",
                username="admin_demo",
                permissions=["realtime_data", "historical_data", "trading", "admin"],
                is_active=True
            )
        ]

        for user in test_users:
            self.users[user.user_id] = user

    def generate_api_key(self, user_id: str) -> str:
        """為用戶生成API密鑰"""
        if user_id not in self.users:
            raise AuthenticationError(f"User {user_id} not found")

        # 生成隨機API密鑰
        import secrets
        api_key = f"ws_{secrets.token_urlsafe(32)}"
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # 存儲API密鑰
        user = self.users[user_id]
        user.api_key_hash = api_key_hash
        self.api_keys[api_key_hash] = user

        return api_key

    def generate_jwt_token(self, user_id: str, permissions: List[str] = None) -> str:
        """生成JWT token"""
        if user_id not in self.users:
            raise AuthenticationError(f"User {user_id} not found")

        user = self.users[user_id]
        if not user.is_active:
            raise AuthenticationError(f"User {user_id} is inactive")

        # 使用用戶權限或指定的權限
        token_permissions = permissions or user.permissions

        payload = {
            'user_id': user_id,
            'username': user.username,
            'permissions': token_permissions,
            'exp': datetime.utcnow() + self.token_expiry,
            'iat': datetime.utcnow(),
            'type': 'websocket_auth'
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """驗證JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # 驗證token類型
            if payload.get('type') != 'websocket_auth':
                raise AuthenticationError("Invalid token type")

            # 驗證用戶存在且活躍
            user_id = payload.get('user_id')
            if user_id not in self.users or not self.users[user_id].is_active:
                raise AuthenticationError("User not found or inactive")

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")

    def validate_api_key(self, api_key: str) -> User:
        """驗證API密鑰"""
        if not api_key:
            raise AuthenticationError("API key required")

        # 哈希API密鑰
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # 查找用戶
        if api_key_hash not in self.api_keys:
            raise AuthenticationError("Invalid API key")

        user = self.api_keys[api_key_hash]
        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        return user

    def check_rate_limit(self, client_ip: str) -> bool:
        """檢查速率限制"""
        now = time.time()
        timestamps = self.rate_limiters[client_ip]

        # 清理過期的時間戳（1小時前）
        cutoff = now - 3600
        self.rate_limiters[client_ip] = deque([
            ts for ts in timestamps if ts > cutoff
        ], maxlen=1000)

        # 檢查1分鐘限制
        minute_ago = now - 60
        minute_connections = sum(1 for ts in self.rate_limiters[client_ip] if ts > minute_ago)
        if minute_connections >= self.max_connections_per_minute:
            raise RateLimitError(f"Too many connections per minute: {minute_connections}")

        # 檢查1小時限制
        hour_connections = len(self.rate_limiters[client_ip])
        if hour_connections >= self.max_connections_per_hour:
            raise RateLimitError(f"Too many connections per hour: {hour_connections}")

        # 記錄當前連接
        self.rate_limiters[client_ip].append(now)
        return True

    def authenticate_websocket(self, websocket: WebSocket) -> ConnectionContext:
        """驗證WebSocket連接"""
        client_ip = websocket.client.host if websocket.client else "unknown"
        user_agent = websocket.headers.get("user-agent", "unknown")

        # 檢查速率限制
        self.check_rate_limit(client_ip)

        # 獲取token（查詢參數優先，然後是header）
        token = websocket.query_params.get("token")
        if not token:
            # 嘗試從Authorization header獲取
            auth_header = websocket.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]

        # 如果沒有token，嘗試API密鑰
        api_key = websocket.query_params.get("api_key")

        if not token and not api_key:
            raise AuthenticationError("Authentication required: token or api_key")

        # 驗證身份
        user = None
        permissions = []

        try:
            if token:
                # JWT token驗證
                payload = self.validate_jwt_token(token)
                user_id = payload['user_id']
                user = self.users[user_id]
                permissions = payload['permissions']

                # 更新最後登錄時間
                user.last_login = datetime.now()

            elif api_key:
                # API密鑰驗證
                user = self.validate_api_key(api_key)
                permissions = user.permissions
                user.last_login = datetime.now()

        except (AuthenticationError, jwt.InvalidTokenError) as e:
            logger.warning(f"Authentication failed from {client_ip}: {e}")
            raise AuthenticationError(f"Authentication failed: {e}")

        # 檢查必要權限
        if "realtime_data" not in permissions:
            raise AuthorizationError("Insufficient permissions: realtime_data required")

        # 創建連接上下文
        context = ConnectionContext(
            user=user,
            permissions=permissions,
            connected_at=datetime.now(),
            client_ip=client_ip,
            user_agent=user_agent
        )

        logger.info(f"WebSocket authenticated: user_id={user.user_id}, ip={client_ip}")
        return context

    def authorize_subscription(self, context: ConnectionContext, symbols: List[str]) -> List[str]:
        """授權訂閱請求"""
        # 檢查用戶權限
        if "realtime_data" not in context.permissions:
            raise AuthorizationError("No realtime_data permission")

        # 基本符號驗證（可以擴展）
        allowed_symbols = []
        for symbol in symbols:
            if isinstance(symbol, str) and len(symbol) > 0:
                # 這裡可以添加更複雜的符號訪問控制
                allowed_symbols.append(symbol)

        logger.info(f"Subscription authorized: user={context.user.user_id}, symbols={allowed_symbols}")
        return allowed_symbols

    def update_activity(self, context: ConnectionContext):
        """更新用戶活動時間"""
        context.last_activity = datetime.now()

    def logout(self, context: ConnectionContext):
        """用戶登出"""
        # 這裡可以添加清理邏輯
        logger.info(f"WebSocket logout: user_id={context.user.user_id}")

    def get_user_stats(self) -> Dict[str, Any]:
        """獲取用戶統計信息"""
        total_users = len(self.users)
        active_users = sum(1 for user in self.users.values() if user.is_active)
        total_api_keys = len(self.api_keys)

        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_api_keys": total_api_keys,
            "rate_limit_config": {
                "max_per_minute": self.max_connections_per_minute,
                "max_per_hour": self.max_connections_per_hour
            }
        }

class WebSocketMiddleware:
    """WebSocket中間件"""

    def __init__(self, authenticator: WebSocketAuthenticator):
        self.authenticator = authenticator

    async def authenticate_connection(self, websocket: WebSocket) -> ConnectionContext:
        """身份驗證中間件"""
        try:
            return self.authenticator.authenticate_websocket(websocket)
        except AuthenticationError as e:
            # 拒絕連接並返回錯誤
            await websocket.close(code=4001, reason=str(e))
            raise
        except RateLimitError as e:
            # 速率限制錯誤
            await websocket.close(code=4003, reason=str(e))
            raise
        except Exception as e:
            # 未知錯誤
            logger.error(f"Authentication middleware error: {e}")
            await websocket.close(code=4000, reason="Authentication failed")
            raise

# 全局實例
def create_authenticator(secret_key: str = "your-secret-key-change-in-production") -> WebSocketAuthenticator:
    """創建身份驗證器實例"""
    return WebSocketAuthenticator(secret_key=secret_key)

def create_middleware(authenticator: WebSocketAuthenticator) -> WebSocketMiddleware:
    """創建中間件實例"""
    return WebSocketMiddleware(authenticator)

# 測試函數
async def test_authentication():
    """測試身份驗證功能"""
    authenticator = create_authenticator("test-secret-key")

    print("=== WebSocket Authentication Test ===")

    # 1. 創建測試用戶
    test_user = authenticator.users["user_001"]
    print(f"Test user: {test_user.username} (permissions: {test_user.permissions})")

    # 2. 生成JWT token
    jwt_token = authenticator.generate_jwt_token("user_001")
    print(f"Generated JWT token: {jwt_token[:50]}...")

    # 3. 驗證JWT token
    try:
        payload = authenticator.validate_jwt_token(jwt_token)
        print(f"JWT validation successful: user={payload['user_id']}")
    except Exception as e:
        print(f"JWT validation failed: {e}")

    # 4. 生成API密鑰
    api_key = authenticator.generate_api_key("user_001")
    print(f"Generated API key: {api_key}")

    # 5. 驗證API密鑰
    try:
        user = authenticator.validate_api_key(api_key)
        print(f"API key validation successful: user={user.username}")
    except Exception as e:
        print(f"API key validation failed: {e}")

    # 6. 測試速率限制
    print("Testing rate limiting...")
    for i in range(3):
        try:
            authenticator.check_rate_limit("127.0.0.1")
            print(f"  Connection {i+1}: Allowed")
        except RateLimitError as e:
            print(f"  Connection {i+1}: Rate limited - {e}")

    # 7. 獲取統計信息
    stats = authenticator.get_user_stats()
    print(f"User stats: {stats}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_authentication())
"""
CBSC系统统一认证服务
Unified Authentication Service for CBSC System
"""

import jwt
import hashlib
import secrets
import redis
import time
import json
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class User:
    """用户数据类"""
    username: str
    email: str
    password_hash: str
    roles: List[str]
    permissions: List[str]
    is_active: bool = True
    created_at: datetime = None
    last_login: Optional[datetime] = None
    login_attempts: int = 0
    locked_until: Optional[datetime] = None

@dataclass
class Client:
    """OAuth2客户端数据类"""
    client_id: str
    client_secret: str
    client_name: str
    redirect_uris: List[str]
    scopes: List[str]
    is_active: bool = True

@dataclass
class TokenData:
    """Token数据类"""
    jti: str  # JWT ID
    sub: str  # Subject (user ID)
    iat: int  # Issued At
    exp: int  # Expiration Time
    type: str  # access, refresh, or verification
    scope: Optional[str] = None
    client_id: Optional[str] = None

class JWTAuthService:
    """JWT认证服务"""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 60,
        refresh_token_expire_days: int = 7,
        redis_client: Optional[redis.Redis] = None
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.redis_client = redis_client

        # 内存存储（Redis不可用时的备用）
        self.token_blacklist: Dict[str, float] = {}
        self.revoked_tokens: Dict[str, float] = {}

        # 用户数据库（模拟）
        self.users_db: Dict[str, User] = {}
        self.init_default_users()

        # 密码策略
        self.password_min_length = 8
        self.max_login_attempts = 5
        self.lockout_duration_minutes = 30

    def init_default_users(self):
        """初始化默认用户"""
        # 管理员用户
        admin_password_hash = self.hash_password("admin123")
        self.users_db["admin"] = User(
            username="admin",
            email="admin@cbsc.local",
            password_hash=admin_password_hash,
            roles=["admin"],
            permissions=["*"],
            created_at=datetime.now()
        )

        # 分析师用户
        analyst_password_hash = self.hash_password("analyst123")
        self.users_db["analyst"] = User(
            username="analyst",
            email="analyst@cbsc.local",
            password_hash=analyst_password_hash,
            roles=["analyst"],
            permissions=[
                "strategies:read", "strategies:write",
                "backtest:execute", "data:read", "reports:read"
            ],
            created_at=datetime.now()
        )

        # 普通用户
        user_password_hash = self.hash_password("user123")
        self.users_db["user"] = User(
            username="user",
            email="user@cbsc.local",
            password_hash=user_password_hash,
            roles=["user"],
            permissions=[
                "profile:read", "profile:write",
                "strategies:read_own", "dashboard:access"
            ],
            created_at=datetime.now()
        )

    def hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def is_password_strong(self, password: str) -> Tuple[bool, List[str]]:
        """检查密码强度"""
        errors = []

        if len(password) < self.password_min_length:
            errors.append(f"密码长度至少{self.password_min_length}位")

        if not any(c.isupper() for c in password):
            errors.append("密码必须包含大写字母")

        if not any(c.islower() for c in password):
            errors.append("密码必须包含小写字母")

        if not any(c.isdigit() for c in password):
            errors.append("密码必须包含数字")

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            errors.append("密码必须包含特殊字符")

        return len(errors) == 0, errors

    def is_account_locked(self, user: User) -> bool:
        """检查账户是否被锁定"""
        if user.locked_until and datetime.now() < user.locked_until:
            return True
        return False

    def lock_account(self, user: User) -> None:
        """锁定账户"""
        user.locked_until = datetime.now() + timedelta(minutes=self.lockout_duration_minutes)
        user.login_attempts = 0
        logger.warning(f"账户 {user.username} 已被锁定至 {user.locked_until}")

    def unlock_account(self, user: User) -> None:
        """解锁账户"""
        user.locked_until = None
        user.login_attempts = 0
        logger.info(f"账户 {user.username} 已解锁")

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """用户认证"""
        user = self.users_db.get(username)
        if not user:
            logger.warning(f"登录失败: 用户不存在 - {username}")
            return None

        # 检查账户状态
        if not user.is_active:
            logger.warning(f"登录失败: 账户已禁用 - {username}")
            return None

        # 检查账户锁定
        if self.is_account_locked(user):
            logger.warning(f"登录失败: 账户已锁定 - {username}")
            return None

        # 验证密码
        if not self.verify_password(password, user.password_hash):
            user.login_attempts += 1
            logger.warning(f"登录失败: 密码错误 - {username} (尝试次数: {user.login_attempts})")

            # 检查是否需要锁定账户
            if user.login_attempts >= self.max_login_attempts:
                self.lock_account(user)

            return None

        # 重置登录尝试次数
        user.login_attempts = 0
        user.last_login = datetime.now()

        logger.info(f"用户登录成功 - {username}")

        return {
            "username": user.username,
            "email": user.email,
            "roles": user.roles,
            "permissions": user.permissions,
            "last_login": user.last_login.isoformat(),
            "created_at": user.created_at.isoformat()
        }

    def create_token(self, payload: Dict[str, Any], token_type: str = "access", expires_delta: Optional[timedelta] = None) -> str:
        """创建JWT令牌"""
        now = datetime.utcnow()

        if token_type == "access":
            expire = now + timedelta(minutes=self.access_token_expire_minutes)
        elif token_type == "refresh":
            expire = now + timedelta(days=self.refresh_token_expire_days)
        else:
            expire = now + (expires_delta or timedelta(hours=1))

        # 添加标准声明
        token_data = {
            "jti": secrets.token_urlsafe(32),  # JWT ID
            "sub": payload.get("sub", "anonymous"),
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "type": token_type,
            "iss": "cbsc-gateway",
            "aud": "cbsc-services"
        }

        # 添加自定义声明
        for key, value in payload.items():
            if key not in token_data:
                token_data[key] = value

        # 创建令牌
        token = jwt.encode(token_data, self.secret_key, algorithm=self.algorithm)

        # 如果有Redis，缓存令牌信息
        if self.redis_client:
            self.redis_client.setex(
                f"token:{token_data['jti']}",
                int((expire - now).total_seconds()),
                json.dumps(token_data)
            )

        return token

    def create_access_token(self, payload: Dict[str, Any]) -> str:
        """创建访问令牌"""
        return self.create_token(payload, "access")

    def create_refresh_token(self, payload: Dict[str, Any]) -> str:
        """创建刷新令牌"""
        return self.create_token(payload, "refresh")

    def verify_token(self, token: str, token_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            # 解码令牌
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # 检查令牌类型
            if token_type and payload.get("type") != token_type:
                logger.warning(f"令牌类型不匹配: 期望 {token_type}, 实际 {payload.get('type')}")
                return None

            # 检查是否在黑名单中
            if self.is_token_blacklisted(payload.get("jti")):
                logger.warning(f"令牌已被撤销: {payload.get('jti')}")
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("令牌已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"无效令牌: {e}")
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """刷新访问令牌"""
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None

        # 创建新的访问令牌
        new_payload = {
            "sub": payload.get("sub"),
            "username": payload.get("username"),
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", [])
        }

        return self.create_access_token(new_payload)

    def revoke_token(self, jti: str, exp: int) -> None:
        """撤销令牌"""
        now = datetime.utcnow()
        exp_time = datetime.fromtimestamp(exp)
        ttl = int((exp_time - now).total_seconds())

        if ttl > 0 and self.redis_client:
            # 将令牌加入黑名单
            self.redis_client.setex(f"blacklist:{jti}", ttl, "revoked")
        else:
            # 内存黑名单
            self.token_blacklist[jti] = exp_time.timestamp()

    def is_token_blacklisted(self, jti: str) -> bool:
        """检查令牌是否在黑名单中"""
        if self.redis_client:
            return self.redis_client.exists(f"blacklist:{jti}")
        else:
            # 检查内存黑名单
            if jti in self.token_blacklist:
                return datetime.now().timestamp() < self.token_blacklist[jti]
            return False

    def get_user_by_token(self, token: str) -> Optional[User]:
        """通过令牌获取用户"""
        payload = self.verify_token(token, "access")
        if not payload:
            return None

        username = payload.get("sub")
        return self.users_db.get(username)

    def check_user_permission(self, username: str, permission: str) -> bool:
        """检查用户权限"""
        user = self.users_db.get(username)
        if not user or not user.is_active:
            return False

        # 管理员拥有所有权限
        if "admin" in user.roles:
            return True

        # 检查特定权限
        return "*" in user.permissions or permission in user.permissions

class OAuth2Service:
    """OAuth2服务"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client

        # 授权码存储
        self.authorization_codes: Dict[str, Dict[str, Any]] = {}

        # 客户端数据库
        self.clients: Dict[str, Client] = {}
        self.init_default_clients()

    def init_default_clients(self):
        """初始化默认OAuth2客户端"""
        # Web应用客户端
        self.clients["cbsc-web"] = Client(
            client_id="cbsc-web",
            client_secret="web_secret_2024",
            client_name="CBSC Web Application",
            redirect_uris=[
                "http://localhost:3000/callback",
                "http://localhost:3001/callback"
            ],
            scopes=["openid", "profile", "email", "strategies:read", "dashboard:access"]
        )

        # 移动应用客户端
        self.clients["cbsc-mobile"] = Client(
            client_id="cbsc-mobile",
            client_secret="mobile_secret_2024",
            client_name="CBSC Mobile Application",
            redirect_uris=[
                "cbsc://auth/callback",
                "http://localhost:8080/callback"
            ],
            scopes=["openid", "profile", "email", "strategies:read"]
        )

        # 第三方集成客户端
        self.clients["cbsc-integration"] = Client(
            client_id="cbsc-integration",
            client_secret="integration_secret_2024",
            client_name="CBSC Integration Client",
            redirect_uris=[
                "https://api.partner.com/callback"
            ],
            scopes=["strategies:read", "data:read"]
        )

    def validate_client(self, client_id: str, client_secret: str) -> bool:
        """验证OAuth2客户端"""
        client = self.clients.get(client_id)
        if not client or not client.is_active:
            return False

        # 在实际应用中，这里应该使用更安全的比较方法
        return secrets.compare_digest(client.client_secret, client_secret)

    def generate_authorization_code(self, client_id: str, user_id: str, scopes: List[str]) -> str:
        """生成授权码"""
        code = secrets.token_urlsafe(32)

        auth_data = {
            "client_id": client_id,
            "user_id": user_id,
            "scopes": scopes,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(minutes=10)
        }

        # 存储授权码
        if self.redis_client:
            self.redis_client.setex(
                f"auth_code:{code}",
                600,  # 10分钟过期
                json.dumps(auth_data, default=str)
            )
        else:
            self.authorization_codes[code] = auth_data

        logger.info(f"生成授权码: {code} for client {client_id}")
        return code

    def validate_authorization_code(self, code: str, client_id: str) -> Optional[Dict[str, Any]]:
        """验证授权码"""
        auth_data = None

        if self.redis_client:
            data = self.redis_client.get(f"auth_code:{code}")
            if data:
                auth_data = json.loads(data)
                # 删除已使用的授权码
                self.redis_client.delete(f"auth_code:{code}")
        else:
            auth_data = self.authorization_codes.pop(code, None)

        if not auth_data:
            return None

        # 验证客户端ID
        if auth_data.get("client_id") != client_id:
            return None

        # 检查过期时间
        expires_at = datetime.fromisoformat(auth_data.get("expires_at"))
        if datetime.now() > expires_at:
            return None

        return auth_data

    def exchange_code_for_tokens(self, code: str, client_id: str, client_secret: str) -> Optional[Dict[str, Any]]:
        """授权码交换令牌"""
        # 验证客户端
        if not self.validate_client(client_id, client_secret):
            logger.warning(f"OAuth2客户端验证失败: {client_id}")
            return None

        # 验证授权码
        auth_data = self.validate_authorization_code(code, client_id)
        if not auth_data:
            logger.warning(f"OAuth2授权码验证失败: {code}")
            return None

        # 获取用户信息
        user_id = auth_data.get("user_id")
        scopes = auth_data.get("scopes")

        # 生成令牌（这里需要与JWTAuthService集成）
        # 在实际实现中，这应该是一个单独的方法调用
        token_data = {
            "sub": user_id,
            "client_id": client_id,
            "scope": " ".join(scopes),
            "grant_type": "authorization_code"
        }

        # 这里应该调用JWTAuthService来创建令牌
        # 为了示例，我们返回模拟数据
        return {
            "access_token": f"access_token_{secrets.token_urlsafe(32)}",
            "refresh_token": f"refresh_token_{secrets.token_urlsafe(32)}",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": " ".join(scopes)
        }

# 全局服务实例
def create_auth_services(redis_client: Optional[redis.Redis] = None, secret_key: str = "default-secret") -> Tuple[JWTAuthService, OAuth2Service]:
    """创建认证服务实例"""
    jwt_service = JWTAuthService(
        secret_key=secret_key,
        redis_client=redis_client
    )

    oauth2_service = OAuth2Service(redis_client=redis_client)

    return jwt_service, oauth2_service

# 辅助函数
def get_current_user_token(credentials: str, jwt_service: JWTAuthService) -> Optional[Dict[str, Any]]:
    """从认证头获取当前用户信息"""
    if not credentials.startswith("Bearer "):
        return None

    token = credentials[7:]  # 移除 "Bearer " 前缀
    return jwt_service.verify_token(token, "access")

def check_user_permission(username: str, permission: str, jwt_service: JWTAuthService) -> bool:
    """检查用户权限"""
    return jwt_service.check_user_permission(username, permission)

def get_user_permissions(username: str, jwt_service: JWTAuthService) -> List[str]:
    """获取用户权限列表"""
    user = jwt_service.users_db.get(username)
    if not user or not user.is_active:
        return []

    # 管理员拥有所有权限
    if "admin" in user.roles:
        return ["*"]

    return user.permissions
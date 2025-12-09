"""
API訪問控制系統
提供API密鑰管理、速率限制、端點權限和OAuth 2.0支持
"""

import hashlib
import hmac
import json
import logging
import re
import secrets
import sqlite3
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import redis

logger = logging.getLogger(__name__)


class APIKeyStatus(Enum):
    """API密鑰狀態"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    REVOKED = "revoked"


class RateLimitScope(Enum):
    """速率限制範圍"""

    GLOBAL = "global"
    USER = "user"
    API_KEY = "api_key"
    IP = "ip"
    ENDPOINT = "endpoint"


@dataclass
class APIKey:
    """API密鑰"""

    id: Optional[int]
    key_id: str  # human - readable ID
    user_id: str
    name: str
    key_hash: str  # 存儲哈希值
    key_prefix: str  # 前缀，用於識別
    scopes: Set[str]  # 權限範圍
    rate_limit: int  # 每分鐘請求數
    status: APIKeyStatus
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["scopes"] = list(self.scopes)
        if self.status:
            data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIKey":
        if "scopes" in data and isinstance(data["scopes"], list):
            data["scopes"] = set(data["scopes"])
        if "status" in data and isinstance(data["status"], str):
            data["status"] = APIKeyStatus(data["status"])
        return cls(**data)


@dataclass
class RateLimit:
    """速率限制"""

    id: Optional[int]
    scope: RateLimitScope
    scope_value: str  # user_id, api_key_id, ip, endpoint
    limit: int
    window: int  # 秒
    requests: deque
    created_at: datetime
    metadata: Dict[str, Any]

    def __post_init__(self):
        if not isinstance(self.requests, deque):
            self.requests = deque(maxlen=self.limit)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EndpointPermission:
    """端點權限"""

    method: str  # GET, POST, PUT, DELETE等
    path_pattern: str  # 路徑模式，支持正則表達式
    required_scopes: Set[str]
    required_roles: Set[str]
    rate_limit: Optional[int]
    is_public: bool
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method,
            "path_pattern": self.path_pattern,
            "required_scopes": list(self.required_scopes),
            "required_roles": list(self.required_roles),
            "rate_limit": self.rate_limit,
            "is_public": self.is_public,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EndpointPermission":
        return cls(
            method=data["method"],
            path_pattern=data["path_pattern"],
            required_scopes=set(data.get("required_scopes", [])),
            required_roles=set(data.get("required_roles", [])),
            rate_limit=data.get("rate_limit"),
            is_public=data.get("is_public", False),
            metadata=data.get("metadata", {}),
        )


class RateLimiter:
    """速率限制器"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.local_limiters: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

    def is_rate_limited(
        self, key: str, limit: int, window: int, client_ip: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """檢查是否超限"""
        now = time.time()
        window_start = now - window

        if self.redis_client:
            # 使用Redis實現
            pipe = self.redis_client.pipeline()
            pipe.lrem(key, 0, 0)  # 移除舊記錄
            pipe.lpush(key, now)
            pipe.ltrim(key, 0, limit - 1)
            pipe.expire(key, window)
            pipe.llen(key)
            results = pipe.execute()
            current_requests = results[-1] if results else 0
        else:
            # 使用本地緩存
            if key not in self.local_limiters:
                self.local_limiters[key] = deque(maxlen=limit)

            # 清理過期請求
            requests = self.local_limiters[key]
            while requests and requests[0] < window_start:
                requests.popleft()

            # 添加當前請求
            requests.append(now)
            current_requests = len(requests)

        remaining = max(0, limit - current_requests)
        reset_time = int(now + window)

        is_limited = current_requests > limit

        return is_limited, {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "current": current_requests,
        }


class RequestSigner:
    """請求簽名器"""

    @staticmethod
    def sign_request(
        method: str, path: str, body: str, timestamp: str, secret_key: str
    ) -> str:
        """簽名請求"""
        message = f"{method}\n{path}\n{body}\n{timestamp}"
        signature = hmac.new(
            secret_key.encode(), message.encode(), hashlib.sha256
        ).hexdigest()
        return signature

    @staticmethod
    def verify_signature(
        method: str,
        path: str,
        body: str,
        timestamp: str,
        signature: str,
        secret_key: str,
    ) -> bool:
        """驗證簽名"""
        expected_signature = RequestSigner.sign_request(
            method, path, body, timestamp, secret_key
        )
        return hmac.compare_digest(signature, expected_signature)


class APIAccessManager:
    """API訪問管理器"""

    def __init__(self, db_path: str = "api_access.db", redis_url: str = None):
        self.db_path = db_path
        self.redis_client = None
        self.rate_limiter = RateLimiter()
        self.endpoint_permissions: List[EndpointPermission] = []
        self.request_signer = RequestSigner()

        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.rate_limiter = RateLimiter(self.redis_client)
            except Exception as e:
                logger.error(f"Redis連接失敗: {e}")

        self._init_database()
        self._create_default_endpoints()
        self._load_endpoint_permissions()

    def _init_database(self):
        """初始化數據庫"""
        with self._get_connection() as conn:
            # API密鑰表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_id TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    key_hash TEXT NOT NULL,
                    key_prefix TEXT NOT NULL,
                    scopes TEXT NOT NULL,
                    rate_limit INTEGER DEFAULT 60,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    last_used_at TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    metadata TEXT
                )
            """
            )

            # 端點權限表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS endpoint_permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    method TEXT NOT NULL,
                    path_pattern TEXT NOT NULL,
                    required_scopes TEXT,
                    required_roles TEXT,
                    rate_limit INTEGER,
                    is_public BOOLEAN DEFAULT FALSE,
                    metadata TEXT
                )
            """
            )

            # API使用統計表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_key_id TEXT,
                    user_id TEXT,
                    endpoint TEXT,
                    method TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    response_code INTEGER,
                    response_time REAL,
                    ip_address TEXT,
                    user_agent TEXT
                )
            """
            )

            # 創建索引
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_api_usage_api_key ON api_usage(api_key_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint)"
            )

            conn.commit()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _create_default_endpoints(self):
        """創建默認端點權限"""
        default_endpoints = [
            EndpointPermission(
                method="GET",
                path_pattern="/api / v1 / health",
                required_scopes=set(),
                required_roles=set(),
                rate_limit=100,
                is_public=True,
                metadata={},
            ),
            EndpointPermission(
                method="GET",
                path_pattern="/api / v1 / data/.*",
                required_scopes={"data:read"},
                required_roles=set(),
                rate_limit=60,
                is_public=False,
                metadata={},
            ),
            EndpointPermission(
                method="POST",
                path_pattern="/api / v1 / trade / execute",
                required_scopes={"trade:execute"},
                required_roles={"trader", "admin"},
                rate_limit=10,
                is_public=False,
                metadata={},
            ),
            EndpointPermission(
                method="GET",
                path_pattern="/api / v1 / portfolio/.*",
                required_scopes={"portfolio:view"},
                required_roles={"trader", "analyst", "admin"},
                rate_limit=30,
                is_public=False,
                metadata={},
            ),
            EndpointPermission(
                method="GET",
                path_pattern="/api / v1 / analysis/.*",
                required_scopes={"analysis:view"},
                required_roles={"analyst", "admin"},
                rate_limit=20,
                is_public=False,
                metadata={},
            ),
            EndpointPermission(
                method="POST",
                path_pattern="/api / v1 / strategy/.*",
                required_scopes={"strategy:execute"},
                required_roles={"trader", "analyst", "admin"},
                rate_limit=5,
                is_public=False,
                metadata={},
            ),
            EndpointPermission(
                method="POST",
                path_pattern="/api / v1 / user/.*",
                required_scopes={"user:manage"},
                required_roles={"admin"},
                rate_limit=20,
                is_public=False,
                metadata={},
            ),
        ]

        for endpoint in default_endpoints:
            self.add_endpoint_permission(endpoint)

    def _load_endpoint_permissions(self):
        """加載端點權限"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM endpoint_permissions")
            for row in cursor.fetchall():
                endpoint = EndpointPermission(
                    method=row["method"],
                    path_pattern=row["path_pattern"],
                    required_scopes=set(
                        json.loads(row["required_scopes"])
                        if row["required_scopes"]
                        else "[]"
                    ),
                    required_roles=set(
                        json.loads(row["required_roles"])
                        if row["required_roles"]
                        else "[]"
                    ),
                    rate_limit=row["rate_limit"],
                    is_public=bool(row["is_public"]),
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
                self.endpoint_permissions.append(endpoint)

    def generate_api_key(
        self,
        user_id: str,
        name: str,
        scopes: List[str],
        rate_limit: int = 60,
        expires_at: Optional[datetime] = None,
    ) -> Tuple[str, APIKey]:
        """生成API密鑰"""
        # 生成密鑰
        key_id = secrets.token_hex(8)
        key_prefix = secrets.token_hex(4)
        secret_key = secrets.token_hex(32)
        key_hash = hashlib.sha256(secret_key.encode()).hexdigest()
        full_key = f"{key_prefix}_{secret_key}"

        # 創建API密鑰對象
        api_key = APIKey(
            id=None,
            key_id=key_id,
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            scopes=set(scopes),
            rate_limit=rate_limit,
            status=APIKeyStatus.ACTIVE,
            created_at=datetime.now(),
            expires_at=expires_at,
            last_used_at=None,
            usage_count=0,
            metadata={},
        )

        # 保存到數據庫
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO api_keys (
                    key_id, user_id, name, key_hash, key_prefix,
                    scopes, rate_limit, status, created_at,
                    expires_at, usage_count, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    api_key.key_id,
                    user_id,
                    name,
                    key_hash,
                    key_prefix,
                    json.dumps(list(scopes)),
                    rate_limit,
                    api_key.status.value,
                    api_key.created_at.isoformat(),
                    expires_at.isoformat() if expires_at else None,
                    0,
                    json.dumps({}),
                ),
            )
            conn.commit()

        logger.info(f"生成API密鑰: {key_id} (用戶: {user_id})")
        return full_key, api_key

    def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """驗證API密鑰"""
        if "_" not in api_key:
            return None

        prefix, secret = api_key.split("_", 1)
        key_hash = hashlib.sha256(secret.encode()).hexdigest()

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM api_keys
                WHERE key_prefix = ? AND key_hash = ? AND status = ?
                """,
                (prefix, key_hash, APIKeyStatus.ACTIVE.value),
            )
            row = cursor.fetchone()

            if row:
                # 檢查過期
                if row["expires_at"]:
                    expires_at = datetime.fromisoformat(row["expires_at"])
                    if datetime.now() > expires_at:
                        # 標記為過期
                        conn.execute(
                            "UPDATE api_keys SET status = ? WHERE id = ?",
                            (APIKeyStatus.EXPIRED.value, row["id"]),
                        )
                        conn.commit()
                        return None

                # 更新使用統計
                conn.execute(
                    """
                    UPDATE api_keys
                    SET last_used_at = ?, usage_count = usage_count + 1
                    WHERE id = ?
                    """,
                    (datetime.now().isoformat(), row["id"]),
                )
                conn.commit()

                scopes = set(json.loads(row["scopes"]) if row["scopes"] else "[]")
                return APIKey(
                    id=row["id"],
                    key_id=row["key_id"],
                    user_id=row["user_id"],
                    name=row["name"],
                    key_hash=row["key_hash"],
                    key_prefix=row["key_prefix"],
                    scopes=scopes,
                    rate_limit=row["rate_limit"],
                    status=APIKeyStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    expires_at=(
                        datetime.fromisoformat(row["expires_at"])
                        if row["expires_at"]
                        else None
                    ),
                    last_used_at=(
                        datetime.fromisoformat(row["last_used_at"])
                        if row["last_used_at"]
                        else None
                    ),
                    usage_count=row["usage_count"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )

        return None

    def check_endpoint_permission(
        self, method: str, path: str, user_id: str = None, api_key: APIKey = None
    ) -> Tuple[bool, Optional[str]]:
        """檢查端點權限"""
        # 查找匹配的端點權限
        for endpoint in self.endpoint_permissions:
            if re.match(endpoint.path_pattern, path):
                # 檢查公共端點
                if endpoint.is_public:
                    return True, None

                # 檢查權限範圍
                if endpoint.required_scopes:
                    user_scopes = set()
                    if api_key:
                        user_scopes = api_key.scopes
                    # 合併用戶角色權限
                    # user_scopes |= self.get_user_scopes(user_id)

                    if not endpoint.required_scopes.issubset(user_scopes):
                        return False, "insufficient_scope"

                return True, None

        # 未找到匹配的端點，默認拒絕
        return False, "endpoint_not_found"

    def check_rate_limit(
        self, api_key: APIKey, endpoint: str, method: str, client_ip: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """檢查速率限制"""
        # 構建速率限制鍵
        if client_ip:
            rate_key = f"rate:{client_ip}:{method}:{endpoint}"
            rate_limit = 100  # IP級限制
        else:
            rate_key = f"rate:{api_key.key_id}:{method}:{endpoint}"
            rate_limit = api_key.rate_limit

        # 檢查限制
        is_limited, rate_info = self.rate_limiter.is_rate_limited(
            rate_key, rate_limit, 60  # 1分鐘窗口
        )

        return is_limited, rate_info

    def verify_request_signature(
        self,
        method: str,
        path: str,
        body: str,
        headers: Dict[str, str],
        api_key: APIKey,
    ) -> bool:
        """驗證請求簽名"""
        # 檢查簽名頭
        signature = headers.get("X - Signature")
        timestamp = headers.get("X - Timestamp")
        nonce = headers.get("X - Nonce")

        if not all([signature, timestamp, nonce]):
            return False

        # 檢查時間戳（5分鐘窗口）
        try:
            req_time = int(timestamp)
            now = int(time.time())
            if abs(now - req_time) > 300:
                logger.warning("請求時間戳過期")
                return False
        except ValueError:
            return False

        # 檢查Nonce（防重放攻擊）
        nonce_key = f"nonce:{api_key.key_id}:{nonce}"
        if self.redis_client:
            if self.redis_client.exists(nonce_key):
                return False  # 重放攻擊
            self.redis_client.setex(nonce_key, 300, 1)

        # 驗證簽名
        return self.request_signer.verify_signature(
            method, path, body, timestamp, signature, api_key.key_hash
        )

    def log_api_usage(
        self,
        api_key: APIKey,
        user_id: str,
        endpoint: str,
        method: str,
        response_code: int,
        response_time: float,
        client_ip: str,
        user_agent: str,
    ):
        """記錄API使用情況"""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO api_usage (
                    api_key_id, user_id, endpoint, method,
                    response_code, response_time, ip_address, user_agent
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    api_key.key_id,
                    user_id,
                    endpoint,
                    method,
                    response_code,
                    response_time,
                    client_ip,
                    user_agent,
                ),
            )
            conn.commit()

    def revoke_api_key(self, key_id: str) -> bool:
        """撤銷API密鑰"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE api_keys SET status = ? WHERE key_id = ?",
                (APIKeyStatus.REVOKED.value, key_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_user_api_keys(self, user_id: str) -> List[APIKey]:
        """獲取用戶的API密鑰"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM api_keys WHERE user_id = ?", (user_id,)
            )
            keys = []
            for row in cursor.fetchall():
                scopes = set(json.loads(row["scopes"]) if row["scopes"] else "[]")
                key = APIKey(
                    id=row["id"],
                    key_id=row["key_id"],
                    user_id=row["user_id"],
                    name=row["name"],
                    key_hash=row["key_hash"],
                    key_prefix=row["key_prefix"],
                    scopes=scopes,
                    rate_limit=row["rate_limit"],
                    status=APIKeyStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    expires_at=(
                        datetime.fromisoformat(row["expires_at"])
                        if row["expires_at"]
                        else None
                    ),
                    last_used_at=(
                        datetime.fromisoformat(row["last_used_at"])
                        if row["last_used_at"]
                        else None
                    ),
                    usage_count=row["usage_count"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
                keys.append(key)
            return keys

    def add_endpoint_permission(self, endpoint: EndpointPermission):
        """添加端點權限"""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO endpoint_permissions (
                    method, path_pattern, required_scopes,
                    required_roles, rate_limit, is_public, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    endpoint.method,
                    endpoint.path_pattern,
                    json.dumps(list(endpoint.required_scopes)),
                    json.dumps(list(endpoint.required_roles)),
                    endpoint.rate_limit,
                    endpoint.is_public,
                    json.dumps(endpoint.metadata),
                ),
            )
            conn.commit()

        self.endpoint_permissions.append(endpoint)

    def get_api_usage_stats(self, user_id: str = None) -> Dict[str, Any]:
        """獲取API使用統計"""
        with self._get_connection() as conn:
            if user_id:
                # 特定用戶統計
                cursor = conn.execute(
                    """
                    SELECT
                        COUNT(*) as total_requests,
                        AVG(response_time) as avg_response_time,
                        COUNT(CASE WHEN response_code >= 400 THEN 1 END) as error_count
                    FROM api_usage
                    WHERE user_id = ?
                    """,
                    (user_id,),
                )
                row = cursor.fetchone()
            else:
                # 全局統計
                cursor = conn.execute(
                    """
                    SELECT
                        COUNT(*) as total_requests,
                        AVG(response_time) as avg_response_time,
                        COUNT(CASE WHEN response_code >= 400 THEN 1 END) as error_count
                    FROM api_usage
                    """
                )
                row = cursor.fetchone()

            return {
                "total_requests": row["total_requests"] or 0,
                "avg_response_time": row["avg_response_time"] or 0,
                "error_count": row["error_count"] or 0,
            }


from contextlib import contextmanager

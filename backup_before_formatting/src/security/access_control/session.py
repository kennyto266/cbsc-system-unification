"""
會話管理系統
提供安全的會話處理、JWT令牌管理和單點登錄功能
"""

import hashlib
import hmac
import ipaddress
import json
import logging
import secrets
import sqlite3
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import jwt
import redis
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """會話狀態"""

    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"


class TokenType(Enum):
    """令牌類型"""

    ACCESS = "access"
    REFRESH = "refresh"
    ID = "id"


@dataclass
class Session:
    """會話對象"""

    id: Optional[int]
    session_id: str
    user_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    status: SessionStatus
    device_id: str
    device_name: str
    location: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        if "status" in data and isinstance(data["status"], str):
            data["status"] = SessionStatus(data["status"])
        return cls(**data)


@dataclass
class Token:
    """令牌對象"""

    token_id: str
    user_id: str
    token_type: TokenType
    token_hash: str
    created_at: datetime
    expires_at: datetime
    is_revoked: bool
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Token":
        if "token_type" in data and isinstance(data["token_type"], str):
            data["token_type"] = TokenType(data["token_type"])
        return cls(**data)


class TokenManager:
    """令牌管理器"""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)

    def generate_access_token(self, user_id: str, session_id: str, **claims) -> str:
        """生成訪問令牌"""
        now = int(time.time())
        payload = {
            "type": "access",
            "user_id": user_id,
            "session_id": session_id,
            "iat": now,
            "exp": now + 3600,  # 1小時
            **claims,
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def generate_refresh_token(self, user_id: str, session_id: str) -> str:
        """生成刷新令牌"""
        now = int(time.time())
        payload = {
            "type": "refresh",
            "user_id": user_id,
            "session_id": session_id,
            "iat": now,
            "exp": now + 604800,  # 7天
            "jti": secrets.token_hex(16),  # JWT ID
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def generate_id_token(self, user_id: str, user_info: Dict[str, Any]) -> str:
        """生成ID令牌"""
        now = int(time.time())
        payload = {
            "type": "id",
            "user_id": user_id,
            "user_info": user_info,
            "iat": now,
            "exp": now + 3600,
            "aud": "hk - quant - system",
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """驗證令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("令牌已過期")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"無效令牌: {e}")
            return None

    def encrypt_sensitive_data(self, data: str) -> str:
        """加密敏感數據"""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """解密敏感數據"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()


class SessionManager:
    """會話管理器"""

    def __init__(
        self,
        db_path: str = "sessions.db",
        redis_url: str = None,
        token_manager: TokenManager = None,
        idle_timeout: int = 1800,  # 30分鐘
        absolute_timeout: int = 86400,  # 24小時
        max_concurrent_sessions: int = 5,
    ):
        self.db_path = db_path
        self.redis_url = redis_url
        self.token_manager = token_manager or TokenManager(secrets.token_hex(32))
        self.idle_timeout = timedelta(seconds=idle_timeout)
        self.absolute_timeout = timedelta(seconds=absolute_timeout)
        self.max_concurrent_sessions = max_concurrent_sessions
        self.redis_client = None

        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
            except Exception as e:
                logger.error(f"Redis連接失敗: {e}")

        self._init_database()

    def _init_database(self):
        """初始化數據庫"""
        with self._get_connection() as conn:
            # 會話表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    status TEXT DEFAULT 'active',
                    device_id TEXT,
                    device_name TEXT,
                    location TEXT,
                    metadata TEXT
                )
            """
            )

            # 令牌表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tokens (
                    token_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token_type TEXT NOT NULL,
                    token_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_revoked BOOLEAN DEFAULT FALSE,
                    metadata TEXT
                )
            """
            )

            # 登錄嘗試表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    ip_address TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    failure_reason TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 創建索引
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tokens_user_id ON tokens(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_login_attempts_user ON login_attempts(user_id)"
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

    def create_session(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        device_id: str,
        device_name: str,
        location: str = "Unknown",
        metadata: Dict[str, Any] = None,
    ) -> Tuple[Session, str, str, str]:
        """創建新會話"""
        now = datetime.now()

        # 檢查並終止過多的會話
        self._terminate_excess_sessions(user_id)

        # 生成會話ID
        session_id = secrets.token_urlsafe(32)

        # 創建會話
        session = Session(
            id=None,
            session_id=session_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=now,
            last_activity=now,
            expires_at=now + self.absolute_timeout,
            status=SessionStatus.ACTIVE,
            device_id=device_id,
            device_name=device_name,
            location=location,
            metadata=metadata or {},
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO sessions (
                    session_id, user_id, ip_address, user_agent,
                    created_at, last_activity, expires_at, status,
                    device_id, device_name, location, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session.session_id,
                    user_id,
                    ip_address,
                    user_agent,
                    now.isoformat(),
                    now.isoformat(),
                    session.expires_at.isoformat(),
                    session.status.value,
                    device_id,
                    device_name,
                    location,
                    json.dumps(session.metadata),
                ),
            )
            conn.commit()

        # 生成令牌
        access_token = self.token_manager.generate_access_token(
            user_id, session_id, device_id=device_id, device_name=device_name
        )
        refresh_token = self.token_manager.generate_refresh_token(user_id, session_id)
        id_token = self.token_manager.generate_id_token(
            user_id, {"device_id": device_id, "device_name": device_name}
        )

        # 緩存到Redis
        if self.redis_client:
            self.redis_client.hset(
                f"session:{session_id}",
                mapping={
                    "user_id": user_id,
                    "status": "active",
                    "expires_at": session.expires_at.isoformat(),
                },
            )
            self.redis_client.expireat(
                f"session:{session_id}", int(session.expires_at.timestamp())
            )

        logger.info(f"創建會話: {session_id} (用戶: {user_id})")
        return session, access_token, refresh_token, id_token

    def get_session(self, session_id: str) -> Optional[Session]:
        """獲取會話"""
        # 優先從Redis獲取
        if self.redis_client:
            redis_data = self.redis_client.hgetall(f"session:{session_id}")
            if redis_data:
                with self._get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
                    )
                    row = cursor.fetchone()
                    if row:
                        return self._row_to_session(row)

        # 從數據庫獲取
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_session(row)

        return None

    def update_activity(self, session_id: str) -> bool:
        """更新會話活動時間"""
        now = datetime.now()

        session = self.get_session(session_id)
        if not session:
            return False

        # 檢查空閒超時
        if now - session.last_activity > self.idle_timeout:
            self.terminate_session(session_id, "idle_timeout")
            return False

        # 檢查絕對超時
        if now > session.expires_at:
            self.terminate_session(session_id, "absolute_timeout")
            return False

        # 更新活動時間
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE sessions
                SET last_activity = ?
                WHERE session_id = ?
                """,
                (now.isoformat(), session_id),
            )
            conn.commit()

        # 更新Redis
        if self.redis_client:
            self.redis_client.hset(
                f"session:{session_id}", "last_activity", now.isoformat()
            )

        return True

    def terminate_session(
        self, session_id: str, reason: str = "user_terminate"
    ) -> bool:
        """終止會話"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE sessions
                SET status = ?
                WHERE session_id = ?
                """,
                (SessionStatus.TERMINATED.value, session_id),
            )
            conn.commit()
            if cursor.rowcount > 0:
                # 從Redis刪除
                if self.redis_client:
                    self.redis_client.delete(f"session:{session_id}")
                logger.info(f"終止會話: {session_id} (原因: {reason})")
                return True
        return False

    def terminate_user_sessions(self, user_id: str, reason: str = "user_logout") -> int:
        """終止用戶的所有會話"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE sessions
                SET status = ?
                WHERE user_id = ? AND status = ?
                """,
                (SessionStatus.TERMINATED.value, user_id, SessionStatus.ACTIVE.value),
            )
            conn.commit()
            count = cursor.rowcount

            if count > 0:
                # 從Redis刪除用戶的所有會話
                if self.redis_client:
                    # 這裡需要遍歷所有會話，建議使用Scan操作
                    pass

                logger.info(f"終止用戶 {user_id} 的 {count} 個會話")
        return count

    def get_user_sessions(self, user_id: str) -> List[Session]:
        """獲取用戶的所有會話"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM sessions
                WHERE user_id = ? AND status = ?
                ORDER BY last_activity DESC
                """,
                (user_id, SessionStatus.ACTIVE.value),
            )
            return [self._row_to_session(row) for row in cursor.fetchall()]

    def check_ip_whitelist(self, user_id: str, ip_address: str) -> bool:
        """檢查IP白名單"""
        with self._get_connection() as conn:
            # 這裡應該從用戶配置中獲取IP白名單
            # 簡化實現
            return True

    def log_login_attempt(
        self,
        user_id: Optional[str],
        ip_address: str,
        success: bool,
        failure_reason: str = None,
    ):
        """記錄登錄嘗試"""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO login_attempts (
                    user_id, ip_address, success, failure_reason
                )
                VALUES (?, ?, ?, ?)
                """,
                (user_id, ip_address, success, failure_reason),
            )
            conn.commit()

    def check_brute_force(self, ip_address: str, threshold: int = 5) -> bool:
        """檢查暴力破解"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM login_attempts
                WHERE ip_address = ? AND success = FALSE
                AND timestamp > ?
                """,
                (ip_address, (datetime.now() - timedelta(hours=1)).isoformat()),
            )
            count = cursor.fetchone()[0]
            return count >= threshold

    def cleanup_expired_sessions(self) -> int:
        """清理過期會話"""
        now = datetime.now()
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE sessions
                SET status = ?
                WHERE expires_at < ? AND status = ?
                """,
                (
                    SessionStatus.EXPIRED.value,
                    now.isoformat(),
                    SessionStatus.ACTIVE.value,
                ),
            )
            conn.commit()
            count = cursor.rowcount

            if count > 0:
                logger.info(f"清理了 {count} 個過期會話")
        return count

    def _terminate_excess_sessions(self, user_id: str):
        """終止過多的會話"""
        sessions = self.get_user_sessions(user_id)
        if len(sessions) >= self.max_concurrent_sessions:
            # 終止最舊的會話
            oldest_session = min(sessions, key=lambda s: s.last_activity)
            self.terminate_session(oldest_session.session_id, "excess_sessions")

    def _row_to_session(self, row: sqlite3.Row) -> Session:
        """數據庫行轉Session對象"""
        metadata = {}
        if row["metadata"]:
            metadata = json.loads(row["metadata"])

        return Session(
            id=row["id"],
            session_id=row["session_id"],
            user_id=row["user_id"],
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            created_at=datetime.fromisoformat(row["created_at"]),
            last_activity=datetime.fromisoformat(row["last_activity"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
            status=SessionStatus(row["status"]),
            device_id=row["device_id"],
            device_name=row["device_name"],
            location=row["location"],
            metadata=metadata,
        )

    def get_session_stats(self) -> Dict[str, Any]:
        """獲取會話統計"""
        with self._get_connection() as conn:
            # 活躍會話數
            cursor = conn.execute(
                "SELECT COUNT(*) FROM sessions WHERE status = ?",
                (SessionStatus.ACTIVE.value,),
            )
            active_sessions = cursor.fetchone()[0]

            # 今日創建的會話
            today = datetime.now().date()
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM sessions
                WHERE DATE(created_at) = ?
                """,
                (today.isoformat(),),
            )
            today_sessions = cursor.fetchone()[0]

            # 活躍用戶數
            cursor = conn.execute(
                "SELECT COUNT(DISTINCT user_id) FROM sessions WHERE status = ?",
                (SessionStatus.ACTIVE.value,),
            )
            active_users = cursor.fetchone()[0]

            return {
                "active_sessions": active_sessions,
                "today_sessions": today_sessions,
                "active_users": active_users,
                "max_concurrent_sessions": self.max_concurrent_sessions,
            }


from contextlib import contextmanager

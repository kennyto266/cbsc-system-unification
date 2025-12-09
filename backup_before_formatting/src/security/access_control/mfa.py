"""
多因素認證 (MFA) 系統
支持TOTP、SMS、Email、硬件令牌和生物識別等多種認證方式
"""

import base64
import hashlib
import hmac
import json
import logging
import secrets
import smtplib
import sqlite3
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from email.mime.multipart import MimeMultipart
from email.mime.text import MimeText
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pyotp
import qrcode

logger = logging.getLogger(__name__)


class MFAMethodType(Enum):
    """MFA方法類型"""

    TOTP = "totp"  # Time - based One - Time Password
    SMS = "sms"
    EMAIL = "email"
    HARDWARE_TOKEN = "hardware"
    BIOMETRIC = "biometric"
    BACKUP_CODE = "backup_code"


class DeviceTrustLevel(Enum):
    """設備信任等級"""

    UNTRUSTED = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    TRUSTED = 4


@dataclass
class MFAMethod:
    """MFA方法"""

    id: Optional[int]
    user_id: str
    method_type: MFAMethodType
    name: str  # 例如"主要手機"或"工作郵箱"
    secret_key: str  # 加密存儲
    phone_number: Optional[str]
    email: Optional[str]
    is_primary: bool
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MFAMethod":
        if "method_type" in data and isinstance(data["method_type"], str):
            data["method_type"] = MFAMethodType(data["method_type"])
        return cls(**data)


@dataclass
class BackupCode:
    """備份代碼"""

    id: Optional[int]
    user_id: str
    code_hash: str
    is_used: bool
    used_at: Optional[datetime]
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackupCode":
        return cls(**data)


@dataclass
class DeviceInfo:
    """設備信息"""

    device_id: str
    user_id: str
    device_name: str
    device_type: str  # mobile, desktop, tablet
    browser: str
    os: str
    ip_address: str
    location: str
    trust_level: DeviceTrustLevel
    is_trusted: bool
    first_seen: datetime
    last_seen: datetime
    fingerprint: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceInfo":
        if "trust_level" in data and isinstance(data["trust_level"], int):
            data["trust_level"] = DeviceTrustLevel(data["trust_level"])
        return cls(**data)


class TOTPProvider:
    """TOTP提供器"""

    @staticmethod
    def generate_secret() -> str:
        """生成TOTP密鑰"""
        return pyotp.random_base32()

    @staticmethod
    def generate_qr_code(secret: str, account_name: str, issuer_name: str) -> bytes:
        """生成QR碼"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=account_name, issuer_name=issuer_name
        )
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(totp_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def verify_token(secret: str, token: str, window: int = 1) -> bool:
        """驗證TOTP令牌"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=window)


class SMSProvider:
    """SMS提供器"""

    def __init__(self, api_key: str, api_secret: str, sender: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.sender = sender

    async def send_sms(self, phone_number: str, code: str) -> bool:
        """發送SMS驗證碼"""
        try:
            # 這裡應該集成實際的SMS服務商API
            # 例如: Twilio, AWS SNS, 阿里雲短信等
            logger.info(f"發送SMS驗證碼到 {phone_number}: {code}")
            # 實際實現中需要調用SMS API
            # await self._call_sms_api(phone_number, code)
            return True
        except Exception as e:
            logger.error(f"SMS發送失敗: {e}")
            return False


class EmailProvider:
    """Email提供器"""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        use_tls: bool = True,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    async def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """發送驗證郵件"""
        try:
            msg = MimeMultipart()
            msg["From"] = self.username
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MimeText(body, "html"))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()

            logger.info(f"郵件已發送到 {to_email}")
            return True
        except Exception as e:
            logger.error(f"郵件發送失敗: {e}")
            return False


class MFAManager:
    """MFA管理器"""

    def __init__(self, db_path: str = "mfa.db"):
        self.db_path = db_path
        self.totp_provider = TOTPProvider()
        self._init_database()

    def _init_database(self):
        """初始化數據庫"""
        with self._get_connection() as conn:
            # MFA方法表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mfa_methods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    method_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    secret_key TEXT,
                    phone_number TEXT,
                    email TEXT,
                    is_primary BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP,
                    metadata TEXT
                )
            """
            )

            # 備份代碼表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS backup_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    code_hash TEXT NOT NULL,
                    is_used BOOLEAN DEFAULT FALSE,
                    used_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 設備信息表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    device_name TEXT NOT NULL,
                    device_type TEXT,
                    browser TEXT,
                    os TEXT,
                    ip_address TEXT,
                    location TEXT,
                    trust_level INTEGER DEFAULT 0,
                    is_trusted BOOLEAN DEFAULT FALSE,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fingerprint TEXT
                )
            """
            )

            # MFA驗證日誌表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mfa_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    method_type TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    failure_reason TEXT
                )
            """
            )

            # 創建索引
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_mfa_methods_user_id ON mfa_methods(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_backup_codes_user_id ON backup_codes(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_devices_user_id ON devices(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_mfa_logs_user_id ON mfa_logs(user_id)"
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

    async def setup_totp(self, user_id: str, account_name: str) -> Tuple[str, bytes]:
        """設置TOTP認證"""
        secret = self.totp_provider.generate_secret()
        qr_code = self.totp_provider.generate_qr_code(
            secret, account_name, "HK Quant System"
        )

        # 保存MFA方法
        mfa_method = MFAMethod(
            id=None,
            user_id=user_id,
            method_type=MFAMethodType.TOTP,
            name="TOTP Authenticator",
            secret_key=secret,
            phone_number=None,
            email=None,
            is_primary=True,
            is_active=True,
            created_at=datetime.now(),
            last_used_at=None,
            metadata={"account_name": account_name},
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO mfa_methods (
                    user_id, method_type, name, secret_key, is_primary, is_active,
                    created_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    MFAMethodType.TOTP.value,
                    mfa_method.name,
                    mfa_method.secret_key,
                    mfa_method.is_primary,
                    mfa_method.is_active,
                    mfa_method.created_at.isoformat(),
                    json.dumps(mfa_method.metadata),
                ),
            )
            conn.commit()

        return secret, qr_code

    async def verify_totp(self, user_id: str, token: str) -> bool:
        """驗證TOTP令牌"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM mfa_methods
                WHERE user_id = ? AND method_type = ? AND is_active = TRUE
                """,
                (user_id, MFAMethodType.TOTP.value),
            )
            row = cursor.fetchone()

            if not row:
                logger.warning(f"用戶 {user_id} 沒有設置TOTP")
                return False

            secret = row["secret_key"]
            is_valid = self.totp_provider.verify_token(secret, token)

            # 記錄驗證結果
            conn.execute(
                """
                INSERT INTO mfa_logs (user_id, method_type, success, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (
                    user_id,
                    MFAMethodType.TOTP.value,
                    is_valid,
                    datetime.now().isoformat(),
                ),
            )

            if is_valid:
                conn.execute(
                    """
                    UPDATE mfa_methods
                    SET last_used_at = ?
                    WHERE id = ?
                    """,
                    (datetime.now().isoformat(), row["id"]),
                )

            conn.commit()
            return is_valid

    async def setup_sms(self, user_id: str, phone_number: str) -> bool:
        """設置SMS認證"""
        # 驗證手機號碼
        if not self._validate_phone_number(phone_number):
            raise ValueError("無效的手機號碼")

        # 發送驗證碼
        code = self._generate_verification_code()
        # 在實際實現中，需要集成SMS服務
        # await sms_provider.send_sms(phone_number, code)

        # 保存MFA方法
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO mfa_methods (
                    user_id, method_type, name, phone_number, is_active,
                    created_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    MFAMethodType.SMS.value,
                    f"Phone ({phone_number[-4:]})",
                    phone_number,
                    True,
                    datetime.now().isoformat(),
                    json.dumps({"verification_code": code}),  # 實際中不應明文存儲
                ),
            )
            conn.commit()

        logger.info(f"為用戶 {user_id} 設置SMS認證")
        return True

    async def verify_sms(self, user_id: str, code: str) -> bool:
        """驗證SMS驗證碼"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM mfa_methods
                WHERE user_id = ? AND method_type = ? AND is_active = TRUE
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id, MFAMethodType.SMS.value),
            )
            row = cursor.fetchone()

            if not row:
                return False

            metadata = json.loads(row["metadata"])
            stored_code = metadata.get("verification_code")

            is_valid = stored_code == code

            conn.execute(
                """
                INSERT INTO mfa_logs (user_id, method_type, success, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (
                    user_id,
                    MFAMethodType.SMS.value,
                    is_valid,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()

            if is_valid:
                conn.execute(
                    """
                    UPDATE mfa_methods
                    SET last_used_at = ?
                    WHERE id = ?
                    """,
                    (datetime.now().isoformat(), row["id"]),
                )
                conn.commit()

            return is_valid

    async def setup_email(self, user_id: str, email: str) -> bool:
        """設置Email認證"""
        # 驗證郵箱
        if not self._validate_email(email):
            raise ValueError("無效的郵箱地址")

        # 發送驗證郵件
        code = self._generate_verification_code()
        # email_provider = EmailProvider(...)
        # await email_provider.send_email(
        #     email,
        #     "HK Quant System - 驗證您的郵箱",
        #     f"您的驗證碼是: {code}"
        # )

        # 保存MFA方法
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO mfa_methods (
                    user_id, method_type, name, email, is_active,
                    created_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    MFAMethodType.EMAIL.value,
                    email,
                    email,
                    True,
                    datetime.now().isoformat(),
                    json.dumps({"verification_code": code}),
                ),
            )
            conn.commit()

        return True

    async def verify_email(self, user_id: str, code: str) -> bool:
        """驗證Email驗證碼"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM mfa_methods
                WHERE user_id = ? AND method_type = ? AND is_active = TRUE
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id, MFAMethodType.EMAIL.value),
            )
            row = cursor.fetchone()

            if not row:
                return False

            metadata = json.loads(row["metadata"])
            stored_code = metadata.get("verification_code")

            is_valid = stored_code == code

            conn.execute(
                """
                INSERT INTO mfa_logs (user_id, method_type, success, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (
                    user_id,
                    MFAMethodType.EMAIL.value,
                    is_valid,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()

            return is_valid

    def generate_backup_codes(self, user_id: str, count: int = 10) -> List[str]:
        """生成備份代碼"""
        codes = [self._generate_backup_code() for _ in range(count)]

        with self._get_connection() as conn:
            for code in codes:
                code_hash = hashlib.sha256(code.encode()).hexdigest()
                conn.execute(
                    """
                    INSERT INTO backup_codes (user_id, code_hash, is_used, created_at)
                    VALUES (?, ?, FALSE, ?)
                    """,
                    (user_id, code_hash, datetime.now().isoformat()),
                )
            conn.commit()

        logger.info(f"為用戶 {user_id} 生成了 {count} 個備份代碼")
        return codes

    def verify_backup_code(self, user_id: str, code: str) -> bool:
        """驗證備份代碼"""
        code_hash = hashlib.sha256(code.encode()).hexdigest()

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM backup_codes
                WHERE user_id = ? AND code_hash = ? AND is_used = FALSE
                """,
                (user_id, code_hash),
            )
            row = cursor.fetchone()

            if not row:
                return False

            # 標記為已使用
            conn.execute(
                """
                UPDATE backup_codes
                SET is_used = TRUE, used_at = ?
                WHERE id = ?
                """,
                (datetime.now().isoformat(), row["id"]),
            )
            conn.commit()

            return True

    def register_device(self, user_id: str, device_info: Dict[str, Any]) -> DeviceInfo:
        """註冊設備"""
        device = DeviceInfo(
            device_id=device_info.get("device_id", secrets.token_hex(16)),
            user_id=user_id,
            device_name=device_info.get("device_name", "Unknown Device"),
            device_type=device_info.get("device_type", "unknown"),
            browser=device_info.get("browser", "unknown"),
            os=device_info.get("os", "unknown"),
            ip_address=device_info.get("ip_address", ""),
            location=device_info.get("location", "Unknown"),
            trust_level=DeviceTrustLevel.UNTRUSTED,
            is_trusted=False,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            fingerprint=device_info.get("fingerprint", ""),
        )

        with self._get_connection() as conn:
            # 檢查設備是否已存在
            cursor = conn.execute(
                "SELECT * FROM devices WHERE device_id = ?", (device.device_id,)
            )
            row = cursor.fetchone()

            if row:
                # 更新最後使用時間
                conn.execute(
                    """
                    UPDATE devices
                    SET last_seen = ?
                    WHERE device_id = ?
                    """,
                    (datetime.now().isoformat(), device.device_id),
                )
            else:
                # 插入新設備
                conn.execute(
                    """
                    INSERT INTO devices (
                        device_id, user_id, device_name, device_type,
                        browser, os, ip_address, location, trust_level,
                        is_trusted, first_seen, last_seen, fingerprint
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        device.device_id,
                        user_id,
                        device.device_name,
                        device.device_type,
                        device.browser,
                        device.os,
                        device.ip_address,
                        device.location,
                        device.trust_level.value,
                        device.is_trusted,
                        device.first_seen.isoformat(),
                        device.last_seen.isoformat(),
                        device.fingerprint,
                    ),
                )
            conn.commit()

        return device

    def trust_device(self, user_id: str, device_id: str) -> bool:
        """信任設備"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE devices
                SET trust_level = ?, is_trusted = TRUE, last_seen = ?
                WHERE user_id = ? AND device_id = ?
                """,
                (
                    DeviceTrustLevel.HIGH.value,
                    datetime.now().isoformat(),
                    user_id,
                    device_id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_user_mfa_methods(self, user_id: str) -> List[MFAMethod]:
        """獲取用戶的MFA方法"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM mfa_methods
                WHERE user_id = ? AND is_active = TRUE
                ORDER BY is_primary DESC, created_at
                """,
                (user_id,),
            )
            methods = []
            for row in cursor.fetchall():
                method = MFAMethod(
                    id=row["id"],
                    user_id=row["user_id"],
                    method_type=MFAMethodType(row["method_type"]),
                    name=row["name"],
                    secret_key=row["secret_key"],
                    phone_number=row["phone_number"],
                    email=row["email"],
                    is_primary=bool(row["is_primary"]),
                    is_active=bool(row["is_active"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    last_used_at=(
                        datetime.fromisoformat(row["last_used_at"])
                        if row["last_used_at"]
                        else None
                    ),
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
                methods.append(method)
            return methods

    def get_user_devices(self, user_id: str) -> List[DeviceInfo]:
        """獲取用戶的設備列表"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM devices
                WHERE user_id = ?
                ORDER BY last_seen DESC
                """,
                (user_id,),
            )
            devices = []
            for row in cursor.fetchall():
                device = DeviceInfo(
                    device_id=row["device_id"],
                    user_id=row["user_id"],
                    device_name=row["device_name"],
                    device_type=row["device_type"],
                    browser=row["browser"],
                    os=row["os"],
                    ip_address=row["ip_address"],
                    location=row["location"],
                    trust_level=DeviceTrustLevel(row["trust_level"]),
                    is_trusted=bool(row["is_trusted"]),
                    first_seen=datetime.fromisoformat(row["first_seen"]),
                    last_seen=datetime.fromisoformat(row["last_seen"]),
                    fingerprint=row["fingerprint"],
                )
                devices.append(device)
            return devices

    def _generate_verification_code(self) -> str:
        """生成6位數字驗證碼"""
        return f"{secrets.randbelow(1000000):06d}"

    def _generate_backup_code(self) -> str:
        """生成備份代碼 (8位字符)"""
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return "".join(secrets.choice(alphabet) for _ in range(8))

    def _validate_phone_number(self, phone: str) -> bool:
        """驗證手機號碼"""
        return bool(re.match(r"^\+?1?\d{9,15}$", phone))

    def _validate_email(self, email: str) -> bool:
        """驗證郵箱地址"""
        return bool(
            re.match(r"^[a - zA - Z0 - 9._%+-]+@[a - zA - Z0 - 9.-]+\.[a - zA - Z]{2,}$", email)
        )


import re
from contextlib import contextmanager

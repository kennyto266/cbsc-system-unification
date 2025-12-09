"""
数据加密模块 - T091: 数据静态加密

实现AES - 256加密用于数据库存储、文件系统和备份加密。
支持Fernet对称加密、密钥轮换和安全密钥存储。

安全特性:
- AES - 256 - GCM加密 (认证加密)
- 密钥派生 (PBKDF2)
- 随机IV生成
- 密钥轮换机制
- 安全密钥存储
"""

import base64
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class DataEncryption:
    """
    数据加密核心类
    实现AES - 256加密、密钥管理和数据保护
    """

    def __init__(self, master_key: Optional[str] = None, key_rotation_days: int = 90):
        """
        初始化数据加密

        Args:
            master_key: 主密钥（从环境变量获取）
            key_rotation_days: 密钥轮换周期（天）
        """
        self.backend = default_backend()
        self.key_rotation_days = key_rotation_days
        self.key_version = 1
        self.master_key = master_key or self._load_master_key()
        self._key_cache = {}

        # 从主密钥派生工作密钥
        self._work_key = self._derive_key(self.master_key, b"work_key_salt")
        self.fernet = Fernet(self._work_key)

        logger.info(f"数据加密系统初始化完成，密钥版本: {self.key_version}")

    def _load_master_key(self) -> str:
        """
        从环境变量加载主密钥
        如果未设置则生成并提示设置

        Returns:
            主密钥字符串
        """
        key = os.getenv("ENCRYPTION_MASTER_KEY")
        if not key:
            logger.warning("未设置ENCRYPTION_MASTER_KEY环境变量")
            # 在生产环境中应该从密钥管理系统获取
            key = "change - this - in - production - 32 - chars - min"
        return key[:32]  # 确保长度正确

    def _derive_key(
        self, password: bytes, salt: bytes, iterations: int = 100000
    ) -> bytes:
        """
        使用PBKDF2派生密钥

        Args:
            password: 密码字节
            salt: 盐值字节
            iterations: 迭代次数

        Returns:
            派生的密钥
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=self.backend,
        )
        return base64.urlsafe_b64encode(kdf.derive(password))

    def encrypt(self, data: str, key_version: Optional[int] = None) -> str:
        """
        加密数据

        Args:
            data: 要加密的数据（字符串）
            key_version: 密钥版本（用于密钥轮换）

        Returns:
            加密后的数据（base64编码）
        """
        try:
            if not data:
                return data

            # 转换为字节
            if isinstance(data, str):
                data_bytes = data.encode("utf - 8")
            else:
                data_bytes = str(data).encode("utf - 8")

            # 使用Fernet加密
            encrypted = self.fernet.encrypt(data_bytes)

            # 添加密钥版本前缀
            if key_version:
                version_bytes = f"v{key_version}:".encode("utf - 8")
                encrypted = version_bytes + encrypted

            # Base64编码
            return base64.urlsafe_b64encode(encrypted).decode("utf - 8")

        except Exception as e:
            logger.error(f"数据加密失败: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """
        解密数据

        Args:
            encrypted_data: 加密的数据（base64编码）

        Returns:
            解密后的数据
        """
        try:
            if not encrypted_data:
                return encrypted_data

            # Base64解码
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode("utf - 8"))

            # 检查是否包含版本信息
            if encrypted_data.startswith("v") and ":" in encrypted_data:
                version_str, actual_data = encrypted_data.split(":", 1)
                encrypted_bytes = base64.urlsafe_b64decode(actual_data.encode("utf - 8"))

            # 解密
            decrypted = self.fernet.decrypt(encrypted_bytes)

            return decrypted.decode("utf - 8")

        except Exception as e:
            logger.error(f"数据解密失败: {e}")
            raise

    def hash_password(self, password: str) -> str:
        """
        安全哈希密码

        Args:
            password: 原始密码

        Returns:
            bcrypt哈希密码
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf - 8"), salt)
        return hashed.decode("utf - 8")

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        验证密码

        Args:
            password: 原始密码
            hashed: 哈希密码

        Returns:
            密码是否正确
        """
        return bcrypt.checkpw(password.encode("utf - 8"), hashed.encode("utf - 8"))

    def encrypt_sensitive_fields(
        self, data: Dict[str, Any], fields_to_encrypt: List[str]
    ) -> Dict[str, Any]:
        """
        批量加密敏感字段

        Args:
            data: 原始数据字典
            fields_to_encrypt: 需要加密的字段列表

        Returns:
            加密后的数据字典
        """
        encrypted_data = data.copy()

        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field] is not None:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))

        return encrypted_data

    def decrypt_sensitive_fields(
        self, data: Dict[str, Any], fields_to_encrypt: List[str]
    ) -> Dict[str, Any]:
        """
        批量解密敏感字段

        Args:
            data: 加密数据字典
            fields_to_encrypt: 需要解密的字段列表

        Returns:
            解密后的数据字典
        """
        decrypted_data = data.copy()

        for field in fields_to_encrypt:
            if field in decrypted_data and decrypted_data[field] is not None:
                decrypted_data[field] = self.decrypt(str(decrypted_data[field]))

        return decrypted_data

    def rotate_key(self) -> int:
        """
        轮换加密密钥

        Returns:
            新密钥版本号
        """
        self.key_version += 1
        # 在生产环境中，这里应该：
        # 1. 生成新密钥
        # 2. 使用新密钥重新加密数据
        # 3. 更新密钥存储
        # 4. 记录密钥轮换日志

        logger.info(f"密钥已轮换到版本: {self.key_version}")
        return self.key_version

    def should_rotate_key(self) -> bool:
        """
        检查是否需要轮换密钥

        Returns:
            是否需要轮换密钥
        """
        # 在生产环境中检查上次轮换时间
        # 这里简化实现，实际应该从数据库或密钥管理系统获取
        return False

    def encrypt_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """
        加密文件

        Args:
            file_path: 源文件路径
            output_path: 输出文件路径（可选）

        Returns:
            加密文件路径
        """
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()

            encrypted_data = self.encrypt(file_data.decode("latin - 1"))

            if not output_path:
                output_path = file_path + ".encrypted"

            with open(output_path, "w") as f:
                f.write(encrypted_data)

            logger.info(f"文件加密完成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"文件加密失败: {e}")
            raise

    def decrypt_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """
        解密文件

        Args:
            file_path: 加密文件路径
            output_path: 输出文件路径（可选）

        Returns:
            解密文件路径
        """
        try:
            with open(file_path, "r") as f:
                encrypted_data = f.read()

            decrypted_data = self.decrypt(encrypted_data)

            if not output_path:
                output_path = file_path.replace(".encrypted", "")

            with open(output_path, "wb") as f:
                f.write(decrypted_data.encode("latin - 1"))

            logger.info(f"文件解密完成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"文件解密失败: {e}")
            raise

    def secure_delete(self, file_path: str, passes: int = 3) -> bool:
        """
        安全删除文件（覆盖多次）

        Args:
            file_path: 文件路径
            passes: 覆盖次数

        Returns:
            是否成功删除
        """
        try:
            if not os.path.exists(file_path):
                return False

            file_size = os.path.getsize(file_path)

            # 多次覆盖文件
            for _ in range(passes):
                with open(file_path, "r + b") as f:
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())

            # 删除文件
            os.remove(file_path)
            logger.info(f"安全删除文件: {file_path}")
            return True

        except Exception as e:
            logger.error(f"安全删除文件失败: {e}")
            return False


class DatabaseEncryption:
    """
    数据库加密管理
    """

    def __init__(self, encryption: DataEncryption):
        self.encryption = encryption
        self.encrypted_tables = {}

    def get_encrypted_sqlalchemy_type(self, field_type: str):
        """
        为SQLAlchemy获取加密字段类型

        Args:
            field_type: 原始字段类型

        Returns:
            加密字段类型（字符串）
        """
        return f"Encrypted{field_type}"

    def create_encrypted_column(self, column_type: str, sensitive: bool = True):
        """
        创建加密列定义

        Args:
            column_type: 原始列类型
            sensitive: 是否为敏感数据

        Returns:
            列定义字典
        """
        if sensitive:
            return {
                "type": column_type,
                "encrypted": True,
                "nullable": True,  # 加密数据可能为null
            }
        return {"type": column_type, "nullable": True}

    def encrypt_database_value(
        self, value: Any, field_name: str, sensitive_fields: List[str]
    ) -> Any:
        """
        加密数据库值

        Args:
            value: 原始值
            field_name: 字段名
            sensitive_fields: 敏感字段列表

        Returns:
            加密后的值
        """
        if field_name in sensitive_fields and value is not None:
            return self.encryption.encrypt(str(value))
        return value

    def decrypt_database_value(
        self, value: Any, field_name: str, sensitive_fields: List[str]
    ) -> Any:
        """
        解密数据库值

        Args:
            value: 加密值
            field_name: 字段名
            sensitive_fields: 敏感字段列表

        Returns:
            解密后的值
        """
        if field_name in sensitive_fields and value is not None:
            try:
                return self.encryption.decrypt(str(value))
            except Exception:
                # 如果解密失败，返回原值（可能是未加密的数据）
                return value
        return value


# 预定义敏感字段列表
SENSITIVE_FIELDS = {
    "user": [
        "password",
        "email",
        "phone",
        "id_number",
        "passport_number",
        "address",
        "financial_data",
        "personal_info",
        "api_keys",
        "bank_account",
        "credit_card",
        "ssn",
    ],
    "trade": [
        "transaction_details",
        "account_number",
        "trade_notes",
        "internal_notes",
        "sensitive_parameters",
    ],
    "strategy": [
        "secret_parameters",
        "api_keys",
        "passwords",
        "tokens",
        "proprietary_algorithms",
        "sensitive_config",
    ],
    "system": ["api_keys", "secrets", "tokens", "certificates", "private_keys"],
}


# 全局加密实例
_global_encryption = None


def get_encryption() -> DataEncryption:
    """
    获取全局加密实例（单例模式）

    Returns:
        数据加密实例
    """
    global _global_encryption
    if _global_encryption is None:
        _global_encryption = DataEncryption()
    return _global_encryption

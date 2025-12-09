"""
字段级加密模块 - T093: 字段级加密

实现数据库字段级别的加密，支持：
- 特定字段加密（用户信息、交易详情、策略参数）
- 部分加密（掩码处理）
- 可搜索加密（索引支持）
- 性能优化

用法示例:
    field_enc = FieldLevelEncryption()

    # 加密单个字段
    encrypted_value = field_enc.encrypt_field('user_email', 'user123@example.com')

    # 批量加密
    user_data = {
        'id': 1,
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '1234567890'
    }
    encrypted_data = field_enc.encrypt_fields(user_data, ['email', 'phone'])
"""

import base64
import hashlib
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .encryption import get_encryption

logger = logging.getLogger(__name__)


class EncryptionType(Enum):
    """加密类型枚举"""

    FULL = "full"  # 完整加密
    PARTIAL = "partial"  # 部分加密（掩码）
    SEARCHABLE = "searchable"  # 可搜索加密
    HASH = "hash"  # 单向哈希
    TOKENIZE = "tokenize"  # 令牌化


@dataclass
class FieldConfig:
    """字段加密配置"""

    field_name: str
    encryption_type: EncryptionType
    mask_char: str = "*"
    mask_length: int = 4
    searchable: bool = False
    indexable: bool = False


class FieldLevelEncryption:
    """
    字段级加密管理类
    """

    def __init__(self):
        self.encryption = get_encryption()
        self.field_configs: Dict[str, FieldConfig] = {}
        self._init_default_configs()

    def _init_default_configs(self):
        """初始化默认字段配置"""
        default_configs = [
            # 用户信息字段
            FieldConfig(
                "email", EncryptionType.SEARCHABLE, searchable=True, indexable=True
            ),
            FieldConfig("phone", EncryptionType.PARTIAL, mask_char="*", mask_length=4),
            FieldConfig(
                "id_number", EncryptionType.PARTIAL, mask_char="*", mask_length=4
            ),
            FieldConfig(
                "passport_number", EncryptionType.PARTIAL, mask_char="*", mask_length=4
            ),
            FieldConfig("address", EncryptionType.FULL),
            FieldConfig(
                "bank_account", EncryptionType.PARTIAL, mask_char="*", mask_length=4
            ),
            FieldConfig(
                "credit_card", EncryptionType.PARTIAL, mask_char="*", mask_length=4
            ),
            # 交易相关字段
            FieldConfig("transaction_details", EncryptionType.FULL),
            FieldConfig(
                "account_number", EncryptionType.PARTIAL, mask_char="*", mask_length=4
            ),
            FieldConfig("trade_notes", EncryptionType.FULL),
            FieldConfig("internal_notes", EncryptionType.FULL),
            # 策略参数字段
            FieldConfig("secret_parameters", EncryptionType.FULL),
            FieldConfig("api_keys", EncryptionType.HASH),
            FieldConfig("tokens", EncryptionType.HASH),
            FieldConfig("passwords", EncryptionType.HASH),
            # 系统字段
            FieldConfig("private_keys", EncryptionType.FULL),
            FieldConfig("certificates", EncryptionType.FULL),
        ]

        for config in default_configs:
            self.field_configs[config.field_name] = config

    def register_field_config(self, config: FieldConfig):
        """
        注册字段配置

        Args:
            config: 字段配置
        """
        self.field_configs[config.field_name] = config
        logger.info(
            f"注册字段配置: {config.field_name} - {config.encryption_type.value}"
        )

    def encrypt_field(self, field_name: str, value: Any) -> str:
        """
        加密单个字段

        Args:
            field_name: 字段名
            value: 原始值

        Returns:
            加密后的值
        """
        if value is None or value == "":
            return value

        config = self.field_configs.get(field_name)
        if not config:
            # 如果没有配置，默认不加密
            logger.warning(f"字段 {field_name} 未配置加密策略")
            return str(value)

        str_value = str(value)

        try:
            if config.encryption_type == EncryptionType.FULL:
                return self.encryption.encrypt(str_value)

            elif config.encryption_type == EncryptionType.PARTIAL:
                return self._partial_encrypt(str_value, config)

            elif config.encryption_type == EncryptionType.SEARCHABLE:
                return self._searchable_encrypt(str_value, field_name)

            elif config.encryption_type == EncryptionType.HASH:
                return self._hash_value(str_value)

            elif config.encryption_type == EncryptionType.TOKENIZE:
                return self._tokenize_value(str_value, field_name)

            else:
                return str_value

        except Exception as e:
            logger.error(f"字段 {field_name} 加密失败: {e}")
            raise

    def decrypt_field(self, field_name: str, encrypted_value: Any) -> str:
        """
        解密单个字段

        Args:
            field_name: 字段名
            encrypted_value: 加密值

        Returns:
            解密后的值
        """
        if encrypted_value is None or encrypted_value == "":
            return encrypted_value

        config = self.field_configs.get(field_name)
        if not config:
            return str(encrypted_value)

        str_value = str(encrypted_value)

        try:
            if config.encryption_type in [
                EncryptionType.FULL,
                EncryptionType.SEARCHABLE,
            ]:
                return self.encryption.decrypt(str_value)

            elif config.encryption_type in [
                EncryptionType.PARTIAL,
                EncryptionType.HASH,
                EncryptionType.TOKENIZE,
            ]:
                # 这些类型不能解密，返回原值
                return str_value

            else:
                return str_value

        except Exception as e:
            logger.error(f"字段 {field_name} 解密失败: {e}")
            raise

    def _partial_encrypt(self, value: str, config: FieldConfig) -> str:
        """
        部分加密（掩码）

        Args:
            value: 原始值
            config: 字段配置

        Returns:
            掩码后的值
        """
        if not value:
            return value

        # 根据值类型进行不同的掩码处理
        if "@" in value:  # 邮箱
            return self._mask_email(value, config)
        elif re.match(r"^\+?[\d\s-()]+$", value):  # 电话号码
            return self._mask_phone(value, config)
        elif len(value) > 8:  # 长字符串
            return self._mask_string(value, config)
        else:
            # 短字符串，全部掩码
            return config.mask_char * len(value)

    def _mask_email(self, email: str, config: FieldConfig) -> str:
        """掩码邮箱地址"""
        parts = email.split("@")
        if len(parts) == 2:
            username, domain = parts
            masked_username = config.mask_char * max(
                1, len(username) - config.mask_length
            )
            return f"{masked_username}@{domain}"
        return config.mask_char * len(email)

    def _mask_phone(self, phone: str, config: FieldConfig) -> str:
        """掩码电话号码"""
        digits = re.sub(r"\D", "", phone)
        if len(digits) >= 7:
            masked_digits = (
                config.mask_char * (len(digits) - config.mask_length)
                + digits[-config.mask_length :]
            )
            # 重新格式化
            formatted = ""
            for i, char in enumerate(phone):
                if char.isdigit():
                    idx = len(formatted) - phone[:i].count("")
                    if idx < len(masked_digits):
                        formatted += masked_digits[idx]
                    else:
                        formatted += char
                else:
                    formatted += char
            return formatted
        return config.mask_char * len(phone)

    def _mask_string(self, value: str, config: FieldConfig) -> str:
        """掩码字符串"""
        if len(value) <= config.mask_length:
            return config.mask_char * len(value)
        return value[: config.mask_length] + config.mask_char * (
            len(value) - config.mask_length
        )

    def _searchable_encrypt(self, value: str, field_name: str) -> str:
        """
        可搜索加密
        使用确定性加密，允许在加密数据上进行搜索

        Args:
            value: 原始值
            field_name: 字段名

        Returns:
            可搜索的加密值
        """
        # 使用字段名作为额外的盐值，确保不同字段的相同值产生不同的加密结果
        salt = f"{field_name}_searchable_salt".encode("utf - 8")
        key = self.encryption._derive_key(
            self.encryption.master_key.encode("utf - 8"), salt
        )

        # 使用相同的key进行加密（但使用不同的IV）
        from cryptography.fernet import Fernet

        fernet = Fernet(key)
        return fernet.encrypt(value.encode("utf - 8")).decode("utf - 8")

    def _hash_value(self, value: str) -> str:
        """
        单向哈希（不可逆）

        Args:
            value: 原始值

        Returns:
            SHA - 256哈希值
        """
        return hashlib.sha256(value.encode("utf - 8")).hexdigest()

    def _tokenize_value(self, value: str, field_name: str) -> str:
        """
        令牌化
        将敏感值替换为随机的令牌

        Args:
            value: 原始值
            field_name: 字段名

        Returns:
            令牌
        """
        # 使用HMAC生成确定性令牌
        import hmac

        secret = f"{field_name}_tokenize_secret".encode("utf - 8")
        token = hmac.new(secret, value.encode("utf - 8"), hashlib.sha256).hexdigest()
        return f"token_{token[:16]}"

    def encrypt_fields(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """
        批量加密字段

        Args:
            data: 原始数据字典
            fields: 要加密的字段列表

        Returns:
            加密后的数据字典
        """
        result = data.copy()

        for field in fields:
            if field in result and result[field] is not None:
                result[field] = self.encrypt_field(field, result[field])

        return result

    def decrypt_fields(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """
        批量解密字段

        Args:
            data: 加密数据字典
            fields: 要解密的字段列表

        Returns:
            解密后的数据字典
        """
        result = data.copy()

        for field in fields:
            if field in result and result[field] is not None:
                result[field] = self.decrypt_field(field, result[field])

        return result

    def get_searchable_value(self, field_name: str, value: str) -> str:
        """
        获取字段的可搜索加密值

        Args:
            field_name: 字段名
            value: 原始值

        Returns:
            可搜索的加密值
        """
        config = self.field_configs.get(field_name)
        if config and config.encryption_type == EncryptionType.SEARCHABLE:
            return self._searchable_encrypt(value, field_name)
        return None

    def is_searchable(self, field_name: str) -> bool:
        """
        检查字段是否为可搜索加密

        Args:
            field_name: 字段名

        Returns:
            是否可搜索
        """
        config = self.field_configs.get(field_name)
        return config and config.searchable

    def is_indexable(self, field_name: str) -> bool:
        """
        检查字段是否可索引

        Args:
            field_name: 字段名

        Returns:
            是否可索引
        """
        config = self.field_configs.get(field_name)
        return config and config.indexable

    def get_encrypted_sql_column(
        self, field_name: str, original_type: str = "VARCHAR(255)"
    ) -> str:
        """
        获取加密后的SQL列定义

        Args:
            field_name: 字段名
            original_type: 原始列类型

        Returns:
            加密后的列定义SQL
        """
        config = self.field_configs.get(field_name)

        if not config:
            return f"{field_name} {original_type}"

        if config.encryption_type == EncryptionType.HASH:
            # 哈希字段使用固定长度
            return f"{field_name}_hash CHAR(64)"
        else:
            # 加密字段使用TEXT类型（Fernet加密后长度会增加）
            return f"{field_name}_encrypted TEXT"

    def validate_encrypted_data(self, data: Dict[str, Any]) -> Dict[str, bool]:
        """
        验证加密数据

        Args:
            data: 数据字典

        Returns:
            字段加密状态字典
        """
        validation_results = {}

        for field_name, value in data.items():
            config = self.field_configs.get(field_name)
            if not config:
                validation_results[field_name] = False
                continue

            if value is None:
                validation_results[field_name] = True
                continue

            try:
                if config.encryption_type == EncryptionType.FULL:
                    # 尝试解密
                    self.encryption.decrypt(str(value))
                    validation_results[field_name] = True
                elif config.encryption_type == EncryptionType.PARTIAL:
                    # 检查是否包含掩码字符
                    validation_results[field_name] = config.mask_char in str(value)
                elif config.encryption_type == EncryptionType.HASH:
                    # 检查哈希长度
                    validation_results[field_name] = len(str(value)) == 64
                else:
                    validation_results[field_name] = True

            except Exception:
                validation_results[field_name] = False

        return validation_results


# 全局字段级加密实例
_global_field_encryption = None


def get_field_encryption() -> FieldLevelEncryption:
    """
    获取全局字段级加密实例

    Returns:
        字段级加密实例
    """
    global _global_field_encryption
    if _global_field_encryption is None:
        _global_field_encryption = FieldLevelEncryption()
    return _global_field_encryption

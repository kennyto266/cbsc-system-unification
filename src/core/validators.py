"""
Common Validators

Shared validation utilities for the CBSC system.
"""

import re
import hashlib
import secrets
import string
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from decimal import Decimal

from .exceptions import ValidationError


class Validator:
    """
    Common validation utilities.
    通用驗證工具類。
    """

    # Email validation regex
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    # Username validation regex (alphanumeric, underscore, hyphen)
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,50}$')

    # Phone validation regex (Chinese mobile)
    PHONE_PATTERN = re.compile(r'^1[3-9]\d{9}$')

    # URL validation regex
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format.
        驗證郵箱格式。
        """
        if not email:
            return False
        return bool(Validator.EMAIL_PATTERN.match(email))

    @staticmethod
    def validate_username(username: str) -> bool:
        """
        Validate username format (3-50 chars, alphanumeric + underscore/hyphen).
        驗證用戶名格式。
        """
        if not username:
            return False
        return bool(Validator.USERNAME_PATTERN.match(username))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """
        Validate phone number format (Chinese mobile).
        驗證手機號格式。
        """
        if not phone:
            return False
        return bool(Validator.PHONE_PATTERN.match(phone))

    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate URL format.
        驗證URL格式。
        """
        if not url:
            return False
        return bool(Validator.URL_PATTERN.match(url))

    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """
        Validate password strength.
        驗證密碼強度。

        Returns:
            Dict with keys:
            - valid: bool - Whether password meets requirements
            - score: int - Strength score (0-5)
            - issues: List[str] - List of issues found
        """
        result = {
            'valid': False,
            'score': 0,
            'issues': []
        }

        if not password:
            result['issues'].append('密碼不能為空')
            return result

        # Length check (min 8 characters)
        if len(password) < 8:
            result['issues'].append('密碼長度至少8位')
        else:
            result['score'] += 1

        # Uppercase check
        if not re.search(r'[A-Z]', password):
            result['issues'].append('密碼需包含大寫字母')
        else:
            result['score'] += 1

        # Lowercase check
        if not re.search(r'[a-z]', password):
            result['issues'].append('密碼需包含小寫字母')
        else:
            result['score'] += 1

        # Digit check
        if not re.search(r'\d', password):
            result['issues'].append('密碼需包含數字')
        else:
            result['score'] += 1

        # Special character check
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result['issues'].append('密碼需包含特殊字符')
        else:
            result['score'] += 1

        result['valid'] = len(result['issues']) == 0
        return result

    @staticmethod
    def validate_numeric_range(
        value: Any,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        field_name: str = "value"
    ) -> List[str]:
        """
        Validate numeric value is within range.
        驗證數值是否在範圍內。
        """
        errors = []

        try:
            num_value = float(value)
        except (TypeError, ValueError):
            errors.append(f"{field_name}必須是數字")
            return errors

        if min_value is not None and num_value < min_value:
            errors.append(f"{field_name}必須大於等於{min_value}")

        if max_value is not None and num_value > max_value:
            errors.append(f"{field_name}必須小於等於{max_value}")

        return errors

    @staticmethod
    def validate_string_length(
        value: Any,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        field_name: str = "value"
    ) -> List[str]:
        """
        Validate string length.
        驗證字符串長度。
        """
        errors = []

        if value is None:
            errors.append(f"{field_name}不能為空")
            return errors

        str_value = str(value)
        length = len(str_value)

        if min_length is not None and length < min_length:
            errors.append(f"{field_name}長度至少{min_length}個字符")

        if max_length is not None and length > max_length:
            errors.append(f"{field_name}長度不能超過{max_length}個字符")

        return errors

    @staticmethod
    def validate_date_range(
        value: Any,
        min_date: Optional[datetime] = None,
        max_date: Optional[datetime] = None,
        field_name: str = "date"
    ) -> List[str]:
        """
        Validate date is within range.
        驗證日期是否在範圍內。
        """
        errors = []

        if value is None:
            errors.append(f"{field_name}不能為空")
            return errors

        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                errors.append(f"{field_name}格式無效")
                return errors

        if min_date and value < min_date:
            errors.append(f"{field_name}不能早於{min_date.isoformat()}")

        if max_date and value > max_date:
            errors.append(f"{field_name}不能晚於{max_date.isoformat()}")

        return errors

    @staticmethod
    def validate_enum(value: Any, allowed_values: List[Any], field_name: str = "value") -> List[str]:
        """
        Validate value is in allowed list.
        驗證值是否在允許列表中。
        """
        if value not in allowed_values:
            return [f"{field_name}必須是以下值之一: {', '.join(map(str, allowed_values))}"]
        return []

    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """
        Validate required fields are present.
        驗證必填字段是否存在。
        """
        errors = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                errors.append(f"缺少必填字段: {field}")
        return errors


class CryptoUtils:
    """
    Cryptographic utility functions.
    加密工具類。
    """

    @staticmethod
    def generate_uuid() -> str:
        """Generate UUID string"""
        import uuid
        return str(uuid.uuid4())

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        Generate cryptographically secure random token.
        生成隨機令牌。
        """
        return secrets.token_urlsafe(length)

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Hash password with PBKDF2.
        使用 PBKDF2 哈希密碼。

        Returns:
            Tuple of (password_hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)

        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # Iterations
        )
        return password_hash.hex(), salt

    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """
        Verify password against hash.
        驗證密碼。
        """
        calculated_hash, _ = CryptoUtils.hash_password(password, salt)
        return secrets.compare_digest(calculated_hash, password_hash)

    @staticmethod
    def generate_api_key() -> str:
        """
        Generate API key with prefix.
        生成 API 密鑰。
        """
        random_part = secrets.token_urlsafe(32)
        return f"cbsc_{random_part}"


class PaginationUtils:
    """
    Pagination utilities.
    分頁工具類。
    """

    @staticmethod
    def paginate(items: List[Any], page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Paginate a list of items.
        分頁處理列表。

        Returns:
            Dict with keys:
            - items: List of items in current page
            - total: Total number of items
            - page: Current page number
            - per_page: Items per page
            - pages: Total number of pages
        """
        total = len(items)
        if per_page <= 0:
            per_page = 20
        if page < 1:
            page = 1

        start = (page - 1) * per_page
        end = start + per_page

        return {
            'items': items[start:end],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page if per_page > 0 else 0
        }

    @staticmethod
    def calculate_offset(page: int, per_page: int) -> int:
        """Calculate offset for database query"""
        return (page - 1) * per_page if page > 0 else 0


class SerializationUtils:
    """
    Serialization utilities.
    序列化工具類。
    """

    @staticmethod
    def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO format string"""
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=None)  # Assume UTC if naive
        return dt.isoformat()

    @staticmethod
    def deserialize_datetime(dt_str: Optional[str]) -> Optional[datetime]:
        """Deserialize ISO format string to datetime"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except ValueError:
            return None

    @staticmethod
    def serialize_decimal(decimal_value: Optional[Decimal]) -> Optional[float]:
        """Serialize Decimal to float"""
        return float(decimal_value) if decimal_value is not None else None

    @staticmethod
    def safe_serialize(data: Any) -> Any:
        """
        Safely serialize data to JSON-compatible format.
        安全序列化為 JSON 兼容格式。
        """
        if data is None:
            return None
        elif isinstance(data, datetime):
            return SerializationUtils.serialize_datetime(data)
        elif isinstance(data, Decimal):
            return SerializationUtils.serialize_decimal(data)
        elif isinstance(data, (list, tuple)):
            return [SerializationUtils.safe_serialize(item) for item in data]
        elif isinstance(data, dict):
            return {k: SerializationUtils.safe_serialize(v) for k, v in data.items()}
        elif hasattr(data, 'to_dict'):
            return SerializationUtils.safe_serialize(data.to_dict())
        else:
            return data

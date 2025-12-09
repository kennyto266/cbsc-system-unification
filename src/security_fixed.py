import os
import hashlib
import hmac
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from pathlib import Path

logger = logging.getLogger('quant_system')

class EncryptionManager:
    """加密管理器"""

    def __init__(self):
        self.key_file = Path('keys/encryption.key')
        self.key_file.parent.mkdir(exist_ok=True)
        self._load_or_generate_key()

    def _load_or_generate_key(self):
        """加载或生成加密密钥"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(self.key)

    def encrypt(self, data: str) -> str:
        """加密数据"""
        f = Fernet(self.key)
        encrypted_data = f.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        f = Fernet(self.key)
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        decrypted_data = f.decrypt(encrypted_bytes)
        return decrypted_data.decode()

class SessionManager:
    """会话管理器"""

    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.encryption_manager = EncryptionManager()
        self.session_timeout = 3600  # 1 hour

    def create_session(self, user_id: str, client_ip: str) -> str:
        """创建新会话"""
        session_id = secrets.token_urlsafe(32)

        self.sessions[session_id] = {
            'user_id': user_id,
            'client_ip': client_ip,
            'created_at': datetime.now(),
            'last_accessed': datetime.now(),
            'is_active': True
        }

        logger.info(f"Session created: {session_id} for user {user_id}")
        return session_id

    def validate_session(self, session_id: str, client_ip: str) -> bool:
        """验证会话"""
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]

        # 检查会话是否过期
        if (datetime.now() - session['last_accessed']).seconds > self.session_timeout:
            self.revoke_session(session_id)
            return False

        # 检查IP地址是否匹配
        if session['client_ip'] != client_ip:
            logger.warning(f"IP mismatch for session {session_id}: {session['client_ip']} vs {client_ip}")
            return False

        # 更新最后访问时间
        session['last_accessed'] = datetime.now()
        return True

    def revoke_session(self, session_id: str):
        """撤销会话"""
        if session_id in self.sessions:
            user_id = self.sessions[session_id]['user_id']
            del self.sessions[session_id]
            logger.info(f"Session revoked: {session_id} for user {user_id}")

class SecureParameterValidator:
    """安全参数验证器"""

    def __init__(self):
        self.allowed_parameters = {
            'rsi_period', 'macd_fast', 'macd_slow', 'bollinger_period',
            'sentiment_threshold', 'risk_tolerance', 'allocation_percentage'
        }
        self.parameter_ranges = {
            'rsi_period': (2, 50),
            'macd_fast': (5, 20),
            'macd_slow': (20, 50),
            'bollinger_period': (10, 50),
            'sentiment_threshold': (0.0, 1.0),
            'risk_tolerance': (0.0, 100.0),
            'allocation_percentage': (10.0, 100.0)
        }

    def validate_parameter(self, param_name: str, param_value: Any) -> tuple[bool, str]:
        """验证参数"""
        # 检查参数名是否在允许列表中
        if param_name not in self.allowed_parameters:
            return False, f"Parameter '{param_name}' is not allowed"

        # 检查参数值范围
        if param_name in self.parameter_ranges:
            min_val, max_val = self.parameter_ranges[param_name]
            try:
                value = float(param_value)
                if not (min_val <= value <= max_val):
                    return False, f"Value {value} out of range [{min_val}, {max_val}]"
            except (ValueError, TypeError):
                return False, f"Invalid numeric value: {param_value}"

        return True, "Valid"

    def sanitize_input(self, input_data: str) -> str:
        """清理输入数据"""
        if not isinstance(input_data, str):
            return str(input_data)

        # 移除潜在的恶意字符
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`']
        sanitized = input_data

        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')

        return sanitized.strip()

class RateLimiter:
    """速率限制器"""

    def __init__(self):
        self.requests: Dict[str, List[datetime]] = {}
        self.max_requests_per_minute = 60
        self.blocked_ips: Dict[str, datetime] = {}
        self.block_duration = timedelta(minutes=5)

    def is_allowed(self, client_ip: str) -> tuple[bool, str]:
        """检查请求是否允许"""
        current_time = datetime.now()

        # 检查IP是否被封禁
        if client_ip in self.blocked_ips:
            if current_time - self.blocked_ips[client_ip] < self.block_duration:
                return False, "IP address is temporarily blocked"
            else:
                del self.blocked_ips[client_ip]

        # 清理过期请求记录
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if (current_time - req_time).seconds < 60
            ]
        else:
            self.requests[client_ip] = []

        # 检查请求频率
        if len(self.requests[client_ip]) >= self.max_requests_per_minute:
            # 封禁IP
            self.blocked_ips[client_ip] = current_time
            logger.warning(f"IP {client_ip} blocked due to rate limit violation")
            return False, "Rate limit exceeded - IP blocked"

        # 记录请求
        self.requests[client_ip].append(current_time)
        return True, "Allowed"

# 全局实例
encryption_manager = EncryptionManager()
session_manager = SessionManager()
parameter_validator = SecureParameterValidator()
rate_limiter = RateLimiter()
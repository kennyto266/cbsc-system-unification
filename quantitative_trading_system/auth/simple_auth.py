#!/usr/bin/env python3
"""
简单认证模块 - 简化版
Simple Authentication Module - Simplified Edition

基于JWT的基础用户认证功能

Author: Claude Code Assistant
Created: 2025-11-29
Version: 1.0.0
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    logging.warning("PyJWT不可用，使用简化认证")

logger = logging.getLogger(__name__)

class SimpleAuth:
    """
    简化认证系统
    提供基础的用户认证和权限管理
    """

    def __init__(self, secret_key: str = "quantitative_trading_system_secret"):
        """
        初始化认证系统

        Args:
            secret_key: 密钥
        """
        self.secret_key = secret_key
        self.users = self._load_default_users()
        self.sessions = {}

        logger.info("简单认证系统初始化完成")

    def _load_default_users(self) -> Dict[str, Dict]:
        """加载默认用户"""
        return {
            "admin": {
                "password_hash": self._hash_password("admin123"),
                "role": "admin",
                "created_at": datetime.now().isoformat(),
                "permissions": ["read", "write", "admin"]
            },
            "user": {
                "password_hash": self._hash_password("user123"),
                "role": "user",
                "created_at": datetime.now().isoformat(),
                "permissions": ["read"]
            }
        }

    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        return self._hash_password(password) == password_hash

    def login(self, username: str, password: str) -> Optional[str]:
        """
        用户登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            成功返回token，失败返回None
        """
        try:
            if username not in self.users:
                logger.warning(f"登录失败: 用户不存在 {username}")
                return None

            user = self.users[username]
            if not self.verify_password(password, user['password_hash']):
                logger.warning(f"登录失败: 密码错误 {username}")
                return None

            # 生成token
            if JWT_AVAILABLE:
                token = self._generate_jwt_token(username, user['role'], user['permissions'])
            else:
                token = self._generate_simple_token(username, user['role'], user['permissions'])

            # 记录会话
            self.sessions[token] = {
                'username': username,
                'role': user['role'],
                'login_time': datetime.now(),
                'last_activity': datetime.now()
            }

            logger.info(f"用户登录成功: {username}")
            return token

        except Exception as e:
            logger.error(f"登录过程出错: {e}")
            return None

    def _generate_jwt_token(self, username: str, role: str, permissions: list) -> str:
        """生成JWT token"""
        payload = {
            'username': username,
            'role': role,
            'permissions': permissions,
            'exp': datetime.now() + timedelta(hours=24),
            'iat': datetime.now()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def _generate_simple_token(self, username: str, role: str, permissions: list) -> str:
        """生成简化token"""
        token_data = {
            'username': username,
            'role': role,
            'permissions': permissions,
            'timestamp': int(time.time()),
            'expiry': int(time.time()) + 86400  # 24小时
        }
        token_string = json.dumps(token_data, sort_keys=True)
        token_hash = hashlib.sha256((token_string + self.secret_key).encode()).hexdigest()
        return f"{token_hash}.{token_string}"

    def verify_token(self, token: str) -> Optional[Dict]:
        """
        验证token

        Args:
            token: 认证token

        Returns:
            成功返回用户信息，失败返回None
        """
        try:
            # 检查会话是否存在
            if token not in self.sessions:
                return None

            session = self.sessions[token]

            # 检查会话是否过期
            if datetime.now() - session['login_time'] > timedelta(hours=24):
                del self.sessions[token]
                return None

            # 更新最后活动时间
            session['last_activity'] = datetime.now()

            if JWT_AVAILABLE:
                # 验证JWT
                try:
                    payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
                    return payload
                except jwt.ExpiredSignatureError:
                    del self.sessions[token]
                    return None
                except jwt.InvalidTokenError:
                    return None
            else:
                # 验证简化token
                if '.' not in token:
                    return None

                token_hash, token_string = token.split('.', 1)
                expected_hash = hashlib.sha256((token_string + self.secret_key).encode()).hexdigest()

                if token_hash != expected_hash:
                    return None

                token_data = json.loads(token_string)
                if int(time.time()) > token_data['expiry']:
                    del self.sessions[token]
                    return None

                return token_data

        except Exception as e:
            logger.error(f"token验证失败: {e}")
            return None

    def has_permission(self, token: str, permission: str) -> bool:
        """
        检查权限

        Args:
            token: 认证token
            permission: 权限名称

        Returns:
            有权限返回True，否则返回False
        """
        user_info = self.verify_token(token)
        if not user_info:
            return False

        permissions = user_info.get('permissions', [])
        return permission in permissions

    def logout(self, token: str) -> bool:
        """
        用户登出

        Args:
            token: 认证token

        Returns:
            成功返回True，失败返回False
        """
        try:
            if token in self.sessions:
                username = self.sessions[token]['username']
                del self.sessions[token]
                logger.info(f"用户登出: {username}")
                return True
            return False
        except Exception as e:
            logger.error(f"登出失败: {e}")
            return False

    def add_user(self, username: str, password: str, role: str = "user", permissions: list = None) -> bool:
        """
        添加用户

        Args:
            username: 用户名
            password: 密码
            role: 角色
            permissions: 权限列表

        Returns:
            成功返回True，失败返回False
        """
        try:
            if username in self.users:
                logger.warning(f"用户已存在: {username}")
                return False

            if permissions is None:
                permissions = ["read"] if role == "user" else ["read", "write", "admin"]

            self.users[username] = {
                "password_hash": self._hash_password(password),
                "role": role,
                "created_at": datetime.now().isoformat(),
                "permissions": permissions
            }

            logger.info(f"用户添加成功: {username}")
            return True

        except Exception as e:
            logger.error(f"添加用户失败: {e}")
            return False

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        修改密码

        Args:
            username: 用户名
            old_password: 旧密码
            new_password: 新密码

        Returns:
            成功返回True，失败返回False
        """
        try:
            if username not in self.users:
                return False

            user = self.users[username]
            if not self.verify_password(old_password, user['password_hash']):
                return False

            user['password_hash'] = self._hash_password(new_password)
            logger.info(f"密码修改成功: {username}")
            return True

        except Exception as e:
            logger.error(f"修改密码失败: {e}")
            return False

    def get_active_sessions(self) -> Dict:
        """获取活跃会话"""
        active_sessions = {}
        current_time = datetime.now()

        for token, session in self.sessions.items():
            if current_time - session['login_time'] < timedelta(hours=24):
                active_sessions[token] = {
                    'username': session['username'],
                    'role': session['role'],
                    'login_time': session['login_time'].isoformat(),
                    'last_activity': session['last_activity'].isoformat(),
                    'session_duration': str(current_time - session['login_time'])
                }

        return active_sessions

    def cleanup_expired_sessions(self):
        """清理过期会话"""
        current_time = datetime.now()
        expired_tokens = []

        for token, session in self.sessions.items():
            if current_time - session['login_time'] > timedelta(hours=24):
                expired_tokens.append(token)

        for token in expired_tokens:
            del self.sessions[token]

        if expired_tokens:
            logger.info(f"清理了 {len(expired_tokens)} 个过期会话")


# 便捷函数
def get_auth_system(secret_key: str = "quantitative_trading_system_secret") -> SimpleAuth:
    """获取认证系统实例"""
    return SimpleAuth(secret_key)

def create_default_admin(username: str = "admin", password: str = "admin123") -> bool:
    """创建默认管理员账户"""
    auth = SimpleAuth()
    return auth.add_user(username, password, "admin", ["read", "write", "admin"])
"""
用户数据访问层
User Data Access Layer

职责：
- 用户数据的CRUD操作
- 用户认证相关数据
- 用户偏好设置管理
"""

from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import hashlib
import secrets

from ..models import User

logger = logging.getLogger(__name__)


class UserRepository:
    """用户数据访问层"""

    def __init__(self):
        """
        初始化用户仓库
        简化实现使用内存存储
        """
        self._users: Dict[int, User] = {}
        self._users_by_username: Dict[str, User] = {}
        self._users_by_email: Dict[str, User] = {}
        self._next_id = 1

        # 初始化示例用户
        self._init_sample_users()

    def _init_sample_users(self):
        """初始化示例用户"""
        sample_users = [
            User(
                id=1,
                username="admin",
                email="admin@cbsc.com",
                is_active=True,
                is_admin=True,
                created_at=datetime.now() - timedelta(days=365),
                preferences={
                    "default_strategy_type": "direct_rsi",
                    "risk_tolerance": "medium",
                    "notification_settings": {
                        "email": True,
                        "sms": False,
                        "push": True
                    },
                    "dashboard_layout": {
                        "chart_position": "left",
                        "theme": "dark"
                    },
                    "auto_refresh_interval": 30
                }
            ),
            User(
                id=2,
                username="trader1",
                email="trader1@example.com",
                is_active=True,
                is_admin=False,
                created_at=datetime.now() - timedelta(days=30),
                preferences={
                    "default_strategy_type": "dual_rsi",
                    "risk_tolerance": "low",
                    "notification_settings": {
                        "email": True,
                        "sms": True,
                        "push": True
                    },
                    "dashboard_layout": {
                        "chart_position": "right",
                        "theme": "light"
                    },
                    "auto_refresh_interval": 60
                }
            ),
            User(
                id=3,
                username="analyst1",
                email="analyst1@example.com",
                is_active=True,
                is_admin=False,
                created_at=datetime.now() - timedelta(days=15),
                preferences={
                    "default_strategy_type": "composite",
                    "risk_tolerance": "high",
                    "notification_settings": {
                        "email": True,
                        "sms": False,
                        "push": False
                    },
                    "dashboard_layout": {
                        "chart_position": "top",
                        "theme": "auto"
                    },
                    "auto_refresh_interval": 15
                }
            )
        ]

        for user in sample_users:
            self._users[user.id] = user
            self._users_by_username[user.username] = user
            self._users_by_email[user.email] = user
            self._next_id = max(self._next_id, user.id + 1)

    # ============================================================================
    # 用户CRUD操作
    # ============================================================================

    async def create(
        self,
        username: str,
        email: str,
        password_hash: str,
        is_admin: bool = False
    ) -> User:
        """
        创建用户
        """
        # 检查用户名是否已存在
        if username in self._users_by_username:
            raise ValueError(f"用户名已存在: {username}")

        # 检查邮箱是否已存在
        if email in self._users_by_email:
            raise ValueError(f"邮箱已存在: {email}")

        # 创建用户
        user = User(
            id=self._next_id,
            username=username,
            email=email,
            is_active=True,
            is_admin=is_admin,
            created_at=datetime.now()
        )

        # 保存用户
        self._users[user.id] = user
        self._users_by_username[user.username] = user
        self._users_by_email[user.email] = user
        self._next_id += 1

        logger.info(f"创建用户: {username}")
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        根据ID获取用户
        """
        return self._users.get(user_id)

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        """
        return self._users_by_username.get(username)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        根据邮箱获取用户
        """
        return self._users_by_email.get(email)

    async def update(self, user: User) -> User:
        """
        更新用户信息
        """
        if user.id not in self._users:
            raise ValueError(f"用户不存在: {user.id}")

        # 更新映射
        old_user = self._users[user.id]
        if old_user.username != user.username:
            if user.username in self._users_by_username:
                raise ValueError(f"用户名已存在: {user.username}")
            del self._users_by_username[old_user.username]
            self._users_by_username[user.username] = user

        if old_user.email != user.email:
            if user.email in self._users_by_email:
                raise ValueError(f"邮箱已存在: {user.email}")
            del self._users_by_email[old_user.email]
            self._users_by_email[user.email] = user

        # 保存更新
        self._users[user.id] = user

        logger.info(f"更新用户: {user.username}")
        return user

    async def delete(self, user_id: int) -> bool:
        """
        删除用户
        """
        user = self._users.get(user_id)
        if not user:
            return False

        # 从所有映射中删除
        del self._users[user_id]
        del self._users_by_username[user.username]
        del self._users_by_email[user.email]

        logger.info(f"删除用户: {user.username}")
        return True

    # ============================================================================
    # 用户认证相关
    # ============================================================================

    async def authenticate(
        self,
        username: str,
        password: str
    ) -> Optional[User]:
        """
        用户认证
        """
        user = await self.get_by_username(username)
        if not user:
            return None

        # 这里应该验证密码哈希
        # 简化实现，实际应该使用安全的密码验证
        if not user.is_active:
            return None

        # 更新最后登录时间
        user.last_login = datetime.now()
        await self.update(user)

        logger.info(f"用户认证成功: {username}")
        return user

    async def update_password(
        self,
        user_id: int,
        new_password_hash: str
    ) -> bool:
        """
        更新用户密码
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False

        # 这里应该保存密码哈希
        # 简化实现
        logger.info(f"更新用户密码: {user.username}")
        return True

    async def reset_password(
        self,
        email: str,
        reset_token: str,
        new_password_hash: str
    ) -> bool:
        """
        重置密码
        """
        user = await self.get_by_email(email)
        if not user:
            return False

        # 这里应该验证重置令牌
        # 简化实现
        logger.info(f"重置用户密码: {user.username}")
        return True

    def hash_password(self, password: str) -> str:
        """
        密码哈希
        """
        # 实际实现应该使用bcrypt或argon2
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000
        ).hex()
        return f"{salt}:{password_hash}"

    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        验证密码
        """
        try:
            salt, hash_value = password_hash.split(':')
            computed_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode(),
                salt.encode(),
                100000
            ).hex()
            return computed_hash == hash_value
        except:
            return False

    # ============================================================================
    # 用户偏好设置
    # ============================================================================

    async def get_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取用户偏好设置
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None
        return user.preferences

    async def update_preferences(
        self,
        user_id: int,
        preferences: Dict[str, Any]
    ) -> bool:
        """
        更新用户偏好设置
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.preferences = preferences
        await self.update(user)

        logger.info(f"更新用户偏好设置: {user.username}")
        return True

    # ============================================================================
    # 用户统计和查询
    # ============================================================================

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None,
        is_admin: Optional[bool] = None
    ) -> tuple[List[User], int]:
        """
        获取用户列表
        """
        users = list(self._users.values())

        # 过滤
        if is_active is not None:
            users = [u for u in users if u.is_active == is_active]
        if is_admin is not None:
            users = [u for u in users if u.is_admin == is_admin]

        # 排序（按创建时间倒序）
        users.sort(key=lambda x: x.created_at, reverse=True)

        # 分页
        total_count = len(users)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_users = users[start_index:end_index]

        return paginated_users, total_count

    async def search_users(
        self,
        query: str,
        limit: int = 10
    ) -> List[User]:
        """
        搜索用户
        """
        query_lower = query.lower()
        results = []

        for user in self._users.values():
            if (query_lower in user.username.lower() or
                query_lower in user.email.lower()):
                results.append(user)

        return results[:limit]

    async def get_user_statistics(self) -> Dict[str, Any]:
        """
        获取用户统计信息
        """
        users = list(self._users.values())
        total_users = len(users)
        active_users = len([u for u in users if u.is_active])
        admin_users = len([u for u in users if u.is_admin])

        # 最近注册用户
        recent_users = [
            u for u in users
            if u.created_at >= datetime.now() - timedelta(days=30)
        ]

        # 活跃用户（最近登录）
        active_recently = [
            u for u in users
            if u.last_login and u.last_login >= datetime.now() - timedelta(days=7)
        ]

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "admin_users": admin_users,
            "regular_users": total_users - admin_users,
            "recent_registrations": len(recent_users),
            "active_recently": len(active_recently)
        }

    # ============================================================================
    # 会话和令牌管理
    # ============================================================================

    async def create_session(
        self,
        user_id: int,
        session_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建用户会话
        """
        # 简化实现，实际应该使用Redis等存储会话
        session_token = secrets.token_urlsafe(32)
        logger.info(f"创建用户会话: {user_id}")
        return session_token

    async def get_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        获取会话信息
        """
        # 简化实现
        return None

    async def revoke_session(self, session_token: str) -> bool:
        """
        撤销会话
        """
        # 简化实现
        logger.info(f"撤销会话: {session_token}")
        return True

    async def revoke_all_sessions(self, user_id: int) -> bool:
        """
        撤销用户所有会话
        """
        # 简化实现
        logger.info(f"撤销用户所有会话: {user_id}")
        return True

    # ============================================================================
    # 用户活动日志
    # ============================================================================

    async def log_user_activity(
        self,
        user_id: int,
        activity: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录用户活动
        """
        activity_log = {
            "user_id": user_id,
            "activity": activity,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"用户活动: {activity_log}")

    async def get_user_activities(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取用户活动记录
        """
        # 简化实现，实际应该从数据库或日志中获取
        return []
"""
认证服务模块
Authentication Service Module

提供完整的用户认证和授权功能
"""

import jwt
import bcrypt
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import json
import secrets
import hashlib
import re
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import logging
import os

logger = logging.getLogger(__name__)

# 数据库模型
Base = declarative_base()

# 用户角色关联表
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime, default=datetime.utcnow),
    Column('assigned_by', Integer, ForeignKey('users.id'))
)

# 角色权限关联表
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True),
    Column('granted_at', DateTime, default=datetime.utcnow)
)

class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    # 状态字段
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)

    # MFA相关
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255))
    backup_codes = Column(Text)  # JSON格式存储备用码

    # 安全字段
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    login_history = relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    social_accounts = relationship("SocialAccount", back_populates="user", cascade="all, delete-orphan")

class Role(Base):
    """角色模型"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_system_role = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

class Permission(Base):
    """权限模型"""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    resource = Column(String(50), nullable=False)  # 资源类型：strategy, user, system等
    action = Column(String(50), nullable=False)    # 操作类型：create, read, update, delete等
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class LoginHistory(Base):
    """登录历史记录"""
    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    device_info = Column(Text)
    location = Column(String(100))
    success = Column(Boolean, default=True)
    failure_reason = Column(String(100))
    login_type = Column(String(20), default="password")  # password, mfa, social
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    user = relationship("User", back_populates="login_history")

class UserSession(Base):
    """用户会话管理"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_token = Column(String(255), unique=True, index=True)
    refresh_token = Column(String(255), unique=True, index=True)
    device_name = Column(String(100))
    device_type = Column(String(50))
    ip_address = Column(String(45))
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    user = relationship("User", back_populates="sessions")

class SocialAccount(Base):
    """社交账号关联"""
    __tablename__ = "social_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    provider = Column(String(50), nullable=False)  # wechat, github, google
    provider_id = Column(String(255), nullable=False)
    access_token = Column(Text)
    refresh_token = Column(Text)
    email = Column(String(255))
    name = Column(String(100))
    avatar_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    user = relationship("User", back_populates="social_accounts")

class JWTManager:
    """JWT令牌管理器"""

    def __init__(self, private_key_path: str = None, public_key_path: str = None):
        self.private_key_path = private_key_path or os.getenv("JWT_PRIVATE_KEY_PATH", "jwt_private.pem")
        self.public_key_path = public_key_path or os.getenv("JWT_PUBLIC_KEY_PATH", "jwt_public.pem")
        self.algorithm = "RS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7

        # 加载或生成密钥对
        self._load_or_generate_keys()

    def _load_or_generate_keys(self):
        """加载或生成RSA密钥对"""
        try:
            # 尝试加载现有密钥
            with open(self.private_key_path, "rb") as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )

            with open(self.public_key_path, "rb") as f:
                self.public_key = serialization.load_pem_public_key(
                    f.read(),
                    backend=default_backend()
                )
            logger.info("JWT密钥对加载成功")
        except FileNotFoundError:
            # 生成新的密钥对
            logger.info("生成新的JWT密钥对")
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            self.public_key = self.private_key.public_key()

            # 保存密钥对
            self._save_keys()

    def _save_keys(self):
        """保存密钥对到文件"""
        # 保存私钥
        pem_private = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        with open(self.private_key_path, "wb") as f:
            f.write(pem_private)

        # 保存公钥
        pem_public = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        with open(self.public_key_path, "wb") as f:
            f.write(pem_public)

        # 设置文件权限（仅所有者可读写）
        os.chmod(self.private_key_path, 0o600)
        os.chmod(self.public_key_path, 0o644)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow()
        })

        encoded_jwt = jwt.encode(
            to_encode,
            self.private_key,
            algorithm=self.algorithm
        )

        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        to_encode.update({
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow()
        })

        encoded_jwt = jwt.encode(
            to_encode,
            self.private_key,
            algorithm=self.algorithm
        )

        return encoded_jwt

    def verify_token(self, token: str, token_type: str = "access") -> dict:
        """验证令牌"""
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.algorithm]
            )

            # 检查令牌类型
            if payload.get("type") != token_type:
                raise jwt.InvalidTokenError(f"Invalid token type: expected {token_type}")

            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

class MFAManager:
    """多因子认证管理器"""

    @staticmethod
    def generate_secret() -> str:
        """生成MFA密钥"""
        return pyotp.random_base32()

    @staticmethod
    def generate_qr_code(username: str, secret: str, issuer_name: str = "CBSC量化交易系统") -> str:
        """生成二维码"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=username,
            issuer_name=issuer_name
        )

        # 创建二维码
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)

        # 转换为base64图片
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    @staticmethod
    def verify_token(secret: str, token: str) -> bool:
        """验证MFA令牌"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)  # 允许1个时间步的偏差

    @staticmethod
    def generate_backup_codes(count: int = 10) -> List[str]:
        """生成备用恢复码"""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()
            codes.append(code)
        return codes

class PasswordManager:
    """密码管理器"""

    @staticmethod
    def hash_password(password: str) -> str:
        """使用Argon2id哈希密码"""
        # 由于bcrypt更常用，这里暂时使用bcrypt
        # 生产环境建议使用argon2
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False

    @staticmethod
    def validate_strength(password: str) -> Dict[str, Any]:
        """验证密码强度"""
        requirements = {
            'length': len(password) >= 12,
            'uppercase': bool(re.search(r'[A-Z]', password)),
            'lowercase': bool(re.search(r'[a-z]', password)),
            'numbers': bool(re.search(r'\d', password)),
            'special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
            'no_common_patterns': not re.search(r'(.)\1{2,}', password),  # 避免连续重复字符
        }

        score = sum(requirements.values())

        if score <= 2:
            level = 'weak'
            text = '弱'
            color = 'red'
        elif score <= 4:
            level = 'medium'
            text = '中等'
            color = 'yellow'
        else:
            level = 'strong'
            text = '强'
            color = 'green'

        return {
            'score': score,
            'level': level,
            'text': text,
            'color': color,
            'requirements': requirements
        }

class AuthService:
    """认证服务主类"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.jwt_manager = JWTManager()
        self.mfa_manager = MFAManager()
        self.password_manager = PasswordManager()
        self.max_login_attempts = 5
        self.lockout_duration_minutes = 30

    def authenticate(self, username: str, password: str, mfa_token: str = None) -> Dict[str, Any]:
        """用户认证"""
        # 查找用户
        user = self.db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user:
            self._record_login_attempt(None, username, False, None, "用户不存在")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        # 检查账户状态
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="账户已被禁用"
            )

        # 检查是否被锁定
        if user.locked_until and datetime.utcnow() < user.locked_until:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"账户已被锁定，请在 {user.locked_until} 后重试"
            )

        # 验证密码
        if not self.password_manager.verify_password(password, user.password_hash):
            self._handle_failed_login(user, "密码错误")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        # 检查MFA
        if user.mfa_enabled:
            if not mfa_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要MFA验证码",
                    headers={"X-Require-MFA": "true"}
                )

            if not self.mfa_manager.verify_token(user.mfa_secret, mfa_token):
                self._handle_failed_login(user, "MFA验证失败")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="MFA验证码错误"
                )

        # 认证成功
        self._handle_successful_login(user)

        # 创建令牌
        access_token = self.jwt_manager.create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )
        refresh_token = self.jwt_manager.create_refresh_token(
            data={"sub": user.username, "user_id": user.id}
        )

        # 创建会话
        session = self._create_session(user, refresh_token)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.jwt_manager.access_token_expire_minutes * 60,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "roles": [role.name for role in user.roles],
                "permissions": self._get_user_permissions(user)
            }
        }

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """刷新访问令牌"""
        try:
            payload = self.jwt_manager.verify_token(refresh_token, "refresh")
            user_id = payload.get("user_id")

            # 验证会话
            session = self.db.query(UserSession).filter(
                UserSession.refresh_token == refresh_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            ).first()

            if not session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的刷新令牌"
                )

            # 获取用户
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户不存在或已被禁用"
                )

            # 创建新的访问令牌
            access_token = self.jwt_manager.create_access_token(
                data={"sub": user.username, "user_id": user.id}
            )

            # 更新会话最后访问时间
            session.last_accessed = datetime.utcnow()
            self.db.commit()

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": self.jwt_manager.access_token_expire_minutes * 60
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"刷新令牌失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌刷新失败"
            )

    def enable_mfa(self, user_id: int) -> Dict[str, Any]:
        """启用MFA"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 生成MFA密钥
        secret = self.mfa_manager.generate_secret()
        qr_code = self.mfa_manager.generate_qr_code(user.username, secret)
        backup_codes = self.mfa_manager.generate_backup_codes()

        # 临时保存密钥（不直接启用，需要验证）
        user.mfa_secret = secret
        # 不设置mfa_enabled为True，等待验证

        self.db.commit()

        return {
            "secret": secret,
            "qr_code": qr_code,
            "backup_codes": backup_codes
        }

    def verify_and_enable_mfa(self, user_id: int, token: str) -> bool:
        """验证并启用MFA"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.mfa_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA未设置"
            )

        if self.mfa_manager.verify_token(user.mfa_secret, token):
            user.mfa_enabled = True
            self.db.commit()
            return True

        return False

    def disable_mfa(self, user_id: int, password: str) -> bool:
        """禁用MFA"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 验证密码
        if not self.password_manager.verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码错误"
            )

        user.mfa_enabled = False
        user.mfa_secret = None
        user.backup_codes = None

        self.db.commit()
        return True

    def get_current_user(self, token: str) -> User:
        """获取当前用户"""
        payload = self.jwt_manager.verify_token(token)
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌"
            )

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用"
            )

        return user

    def check_permission(self, user: User, resource: str, action: str) -> bool:
        """检查用户权限"""
        # 超级用户拥有所有权限
        if user.is_superuser:
            return True

        # 获取用户所有角色
        user_roles = user.roles

        # 检查每个角色的权限
        for role in user_roles:
            for permission in role.permissions:
                if permission.resource == resource and permission.action == action:
                    return True

        return False

    def logout(self, token: str) -> bool:
        """用户登出"""
        try:
            payload = self.jwt_manager.verify_token(token)
            user_id = payload.get("user_id")

            # 将会话标记为无效
            self.db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            ).update({"is_active": False})

            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"登出失败: {e}")
            return False

    def logout_all_sessions(self, user_id: int) -> bool:
        """登出所有会话"""
        try:
            self.db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            ).update({"is_active": False})

            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"登出所有会话失败: {e}")
            return False

    def get_user_sessions(self, user_id: int) -> List[Dict]:
        """获取用户活跃会话"""
        sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).all()

        return [
            {
                "id": session.id,
                "device_name": session.device_name,
                "device_type": session.device_type,
                "ip_address": session.ip_address,
                "created_at": session.created_at.isoformat(),
                "last_accessed": session.last_accessed.isoformat(),
                "expires_at": session.expires_at.isoformat()
            }
            for session in sessions
        ]

    def revoke_session(self, user_id: int, session_id: int) -> bool:
        """撤销指定会话"""
        try:
            session = self.db.query(UserSession).filter(
                UserSession.id == session_id,
                UserSession.user_id == user_id
            ).first()

            if session:
                session.is_active = False
                self.db.commit()
                return True

            return False

        except Exception as e:
            logger.error(f"撤销会话失败: {e}")
            return False

    def _handle_failed_login(self, user: User, reason: str):
        """处理登录失败"""
        user.failed_login_attempts += 1

        if user.failed_login_attempts >= self.max_login_attempts:
            user.locked_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration_minutes)
            logger.warning(f"用户 {user.username} 因多次失败登录被锁定")

        self.db.commit()

    def _handle_successful_login(self, user: User):
        """处理登录成功"""
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()

        self.db.commit()

    def _record_login_attempt(self, user: User, username: str, success: bool,
                            ip_address: str, failure_reason: str = None,
                            user_agent: str = None, login_type: str = "password"):
        """记录登录尝试"""
        login_record = LoginHistory(
            user_id=user.id if user else None,
            username=username if not user else None,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason,
            login_type=login_type
        )

        self.db.add(login_record)
        self.db.commit()

    def _create_session(self, user: User, refresh_token: str) -> UserSession:
        """创建用户会话"""
        session = UserSession(
            user_id=user.id,
            session_token=secrets.token_urlsafe(32),
            refresh_token=refresh_token,
            device_name="Unknown Device",  # 可以从user_agent解析
            device_type="desktop",
            ip_address="127.0.0.1",  # 从请求获取
            expires_at=datetime.utcnow() + timedelta(days=self.jwt_manager.refresh_token_expire_days)
        )

        self.db.add(session)
        self.db.commit()

        return session

    def _get_user_permissions(self, user: User) -> List[str]:
        """获取用户所有权限"""
        permissions = set()

        for role in user.roles:
            for permission in role.permissions:
                permissions.add(f"{permission.resource}:{permission.action}")

        return list(permissions)

# 依赖注入函数
def get_auth_service(db: Session) -> AuthService:
    """获取认证服务实例"""
    return AuthService(db)

def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="api/auth/login")),
                    db: Session = Depends(get_db)) -> User:
    """获取当前用户依赖"""
    auth_service = get_auth_service(db)
    return auth_service.get_current_user(token)

def require_permission(resource: str, action: str):
    """权限检查装饰器工厂"""
    def permission_checker(current_user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)) -> User:
        auth_service = get_auth_service(db)
        if not auth_service.check_permission(current_user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足: 需要 {resource}:{action} 权限"
            )
        return current_user

    return permission_checker
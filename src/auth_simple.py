"""
简化的用户认证系统
Simple User Authentication System
为个人使用场景优化的认证功能
"""

import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
import re
import logging
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import os
import json
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./user_management.db")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 数据库模型
Base = declarative_base()

class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)

    # 关联关系
    login_history = relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")
    devices = relationship("UserDevice", back_populates="user", cascade="all, delete-orphan")

class LoginHistory(Base):
    """登录历史记录"""
    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ip_address = Column(String(45))  # 支持IPv6
    user_agent = Column(Text)
    device_info = Column(Text)  # JSON格式存储设备信息
    location = Column(String(100))
    success = Column(Boolean, default=True)
    failure_reason = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    user = relationship("User", back_populates="login_history")

class UserDevice(Base):
    """用户设备管理"""
    __tablename__ = "user_devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    device_name = Column(String(100))
    device_type = Column(String(50))  # desktop, mobile, tablet
    user_agent = Column(Text)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_trusted = Column(Boolean, default=False)

    # 关联关系
    user = relationship("User", back_populates="devices")

# Pydantic模型
class UserCreate(BaseModel):
    """创建用户模型"""
    username: str
    email: Optional[EmailStr] = None
    password: str

class UserLogin(BaseModel):
    """用户登录模型"""
    username: str
    password: str

class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    login_count: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class PasswordChange(BaseModel):
    """密码修改模型"""
    old_password: str
    new_password: str

class PasswordStrengthResult(BaseModel):
    """密码强度结果"""
    score: int
    level: str  # weak, medium, strong
    text: str
    color: str
    requirements: Dict[str, bool]

class LoginHistoryResponse(BaseModel):
    """登录历史响应模型"""
    id: int
    ip_address: Optional[str]
    device_info: Optional[str]
    location: Optional[str]
    success: bool
    failure_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# 认证服务类
class AuthService:
    """认证服务类"""

    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

    def create_tables(self):
        """创建数据库表"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("数据库表创建完成")

    def get_db(self):
        """获取数据库会话"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def hash_password(self, password: str) -> str:
        """安全地哈希密码"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"密码验证错误: {e}")
            return False

    def validate_password_strength(self, password: str) -> PasswordStrengthResult:
        """验证密码强度"""
        requirements = {
            'length': len(password) >= 8,
            'uppercase': bool(re.search(r'[A-Z]', password)),
            'lowercase': bool(re.search(r'[a-z]', password)),
            'numbers': bool(re.search(r'\d', password)),
            'special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
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

        return PasswordStrengthResult(
            score=score,
            level=level,
            text=text,
            color=color,
            requirements=requirements
        )

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def authenticate_user(self, username: str, password: str, db) -> Optional[User]:
        """验证用户凭据"""
        # 查找用户
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None

        # 检查账户是否被锁定
        if user.locked_until and datetime.utcnow() < user.locked_until:
            logger.warning(f"用户 {username} 账户被锁定")
            return None

        # 验证密码
        if not self.verify_password(password, user.password_hash):
            # 增加失败次数
            user.failed_login_attempts += 1

            # 如果失败次数过多，锁定账户
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                logger.warning(f"用户 {username} 因多次失败登录被锁定")

            db.commit()
            return None

        # 登录成功，重置失败次数
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        user.login_count += 1

        db.commit()
        return user

    async def get_current_user(self, token: str = Depends(OAuth2PasswordBearer(tokenUrl="api/auth/login")), db=Depends(get_db)) -> User:
        """获取当前用户"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except jwt.PyJWTError:
            raise credentials_exception

        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise credentials_exception

        return user

    def record_login_history(self, user: User, success: bool, ip_address: str, user_agent: str, failure_reason: str = None, db=None):
        """记录登录历史"""
        if db is None:
            db = self.SessionLocal()

        try:
            # 提取设备信息
            device_info = self.extract_device_info(user_agent)

            # 获取位置信息（简化版）
            location = self.get_location_from_ip(ip_address)

            login_record = LoginHistory(
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                device_info=json.dumps(device_info),
                location=location,
                success=success,
                failure_reason=failure_reason
            )

            db.add(login_record)

            # 如果是成功的登录，更新或添加设备记录
            if success:
                existing_device = db.query(UserDevice).filter(
                    UserDevice.user_id == user.id,
                    UserDevice.device_name == device_info.get('name', 'Unknown Device')
                ).first()

                if existing_device:
                    existing_device.last_seen = datetime.utcnow()
                else:
                    new_device = UserDevice(
                        user_id=user.id,
                        device_name=device_info.get('name', 'Unknown Device'),
                        device_type=device_info.get('type', 'desktop'),
                        user_agent=user_agent,
                        last_seen=datetime.utcnow()
                    )
                    db.add(new_device)

            db.commit()

        except Exception as e:
            logger.error(f"记录登录历史失败: {e}")
            db.rollback()
        finally:
            db.close()

    def extract_device_info(self, user_agent: str) -> Dict[str, Any]:
        """提取设备信息"""
        # 简化的设备信息提取
        device_info = {
            'name': 'Unknown Device',
            'type': 'desktop',
            'browser': 'Unknown',
            'os': 'Unknown'
        }

        if not user_agent:
            return device_info

        # 检测浏览器
        browsers = ['Chrome', 'Firefox', 'Safari', 'Edge', 'Opera']
        for browser in browsers:
            if browser.lower() in user_agent.lower():
                device_info['browser'] = browser
                device_info['name'] = f"{browser} Browser"
                break

        # 检测操作系统
        os_list = ['Windows', 'Mac OS', 'Linux', 'Android', 'iOS']
        for os_name in os_list:
            if os_name.lower() in user_agent.lower():
                device_info['os'] = os_name
                break

        # 检测设备类型
        if 'mobile' in user_agent.lower() or 'android' in user_agent.lower() or 'ios' in user_agent.lower():
            device_info['type'] = 'mobile'
        elif 'tablet' in user_agent.lower() or 'ipad' in user_agent.lower():
            device_info['type'] = 'tablet'

        return device_info

    def get_location_from_ip(self, ip_address: str) -> str:
        """从IP地址获取位置信息"""
        # 简化实现，实际应用中可以使用IP地理位置服务
        if ip_address.startswith('127.') or ip_address.startswith('192.168.') or ip_address == '::1':
            return '本地网络'
        elif ip_address.startswith('192.168.'):
            return '内网'
        else:
            return '未知位置'

    def get_user_login_history(self, user_id: int, limit: int = 10, db=None):
        """获取用户登录历史"""
        if db is None:
            db = self.SessionLocal()

        try:
            history = db.query(LoginHistory).filter(
                LoginHistory.user_id == user_id
            ).order_by(LoginHistory.created_at.desc()).limit(limit).all()

            return [LoginHistoryResponse.from_orm(record) for record in history]

        except Exception as e:
            logger.error(f"获取登录历史失败: {e}")
            return []
        finally:
            db.close()

    def get_user_devices(self, user_id: int, db=None):
        """获取用户设备列表"""
        if db is None:
            db = self.SessionLocal()

        try:
            devices = db.query(UserDevice).filter(
                UserDevice.user_id == user_id
            ).order_by(UserDevice.last_seen.desc()).all()

            return devices

        except Exception as e:
            logger.error(f"获取设备列表失败: {e}")
            return []
        finally:
            db.close()

    def change_password(self, user: User, old_password: str, new_password: str, db=None) -> bool:
        """修改密码"""
        if db is None:
            db = self.SessionLocal()

        try:
            # 验证旧密码
            if not self.verify_password(old_password, user.password_hash):
                return False

            # 验证新密码强度
            strength = self.validate_password_strength(new_password)
            if strength.score < 3:
                raise ValueError("密码强度不够")

            # 更新密码
            user.password_hash = self.hash_password(new_password)
            user.updated_at = datetime.utcnow()

            db.commit()
            return True

        except Exception as e:
            logger.error(f"修改密码失败: {e}")
            db.rollback()
            return False
        finally:
            db.close()

# 全局认证服务实例
auth_service = AuthService()

# 初始化函数
def init_auth_service():
    """初始化认证服务"""
    auth_service.create_tables()
    logger.info("认证服务初始化完成")

# Export functions for backward compatibility
def get_db():
    """获取数据库会话 - Export wrapper for backward compatibility"""
    return auth_service.get_db()

async def get_current_user(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="api/auth/login")),
    db=Depends(get_db)
) -> User:
    """获取当前用户 - Export wrapper for backward compatibility"""
    return await auth_service.get_current_user(token, db)

if __name__ == "__main__":
    init_auth_service()
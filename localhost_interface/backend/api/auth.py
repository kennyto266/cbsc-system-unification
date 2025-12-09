"""
JWT認證系統 - 基於角色的訪問控制
支持交易員、分析師、管理員等不同角色
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import secrets
import hashlib
import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt as jose_jwt
import logging

from shared.models.schemas import User, UserRole
from backend.core.config import get_settings

logger = logging.getLogger(__name__)

# 配置
settings = get_settings()
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# OAuth2 密碼方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# 用戶數據庫模擬 (生產環境應使用真實數據庫)

def hash_password_func(password: str) -> str:
    """安全的密碼哈希"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${pwd_hash.hex()}"

USERS_DB: Dict[str, Dict[str, Any]] = {
    "admin": {
        "username": "admin",
        "full_name": "系統管理員",
        "email": "admin@trading-system.com",
        "hashed_password": hash_password_func("admin123!@#"),
        "role": UserRole.ADMIN,
        "permissions": ["read", "write", "delete", "admin", "trading", "backtest", "risk_management"],
        "is_active": True,
        "created_at": datetime.now(),
        "last_login": None
    },
    "trader": {
        "username": "trader",
        "full_name": "量化交易員",
        "email": "trader@trading-system.com",
        "hashed_password": hash_password_func("trader123!@#"),
        "role": UserRole.TRADER,
        "permissions": ["read", "write", "trading", "backtest"],
        "is_active": True,
        "created_at": datetime.now(),
        "last_login": None
    },
    "analyst": {
        "username": "analyst",
        "full_name": "數據分析師",
        "email": "analyst@trading-system.com",
        "hashed_password": hash_password_func("analyst123!@#"),
        "role": UserRole.ANALYST,
        "permissions": ["read", "backtest"],
        "is_active": True,
        "created_at": datetime.now(),
        "last_login": None
    },
    "guest": {
        "username": "guest",
        "full_name": "訪客用戶",
        "email": "guest@trading-system.com",
        "hashed_password": hash_password_func("guest123"),
        "role": UserRole.GUEST,
        "permissions": ["read"],
        "is_active": True,
        "created_at": datetime.now(),
        "last_login": None
    }
}

def hash_password(password: str) -> str:
    """安全的密碼哈希"""
    return hash_password_func(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證密碼"""
    try:
        salt, pwd_hash = hashed_password.split('$')
        test_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), salt.encode(), 100000)
        return test_hash.hex() == pwd_hash
    except:
        return False

def authenticate_user(username: str, password: str) -> Optional[User]:
    """驗證用戶憑證"""
    user_data = USERS_DB.get(username)
    if not user_data:
        logger.warning(f"用戶 {username} 不存在")
        return None

    if not verify_password(password, user_data["hashed_password"]):
        logger.warning(f"用戶 {username} 密碼錯誤")
        return None

    if not user_data["is_active"]:
        logger.warning(f"用戶 {username} 賬戶已禁用")
        return None

    # 更新最後登入時間
    user_data["last_login"] = datetime.now()

    logger.info(f"用戶 {username} 認證成功")
    return User(
        username=user_data["username"],
        full_name=user_data["full_name"],
        email=user_data["email"],
        role=user_data["role"],
        permissions=user_data["permissions"],
        is_active=user_data["is_active"],
        created_at=user_data["created_at"],
        last_login=user_data["last_login"]
    )

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """創建JWT訪問令牌"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    try:
        encoded_jwt = jose_jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.debug(f"創建訪問令牌，用戶: {data.get('sub')}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"創建訪問令牌失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌創建失敗"
        )

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """驗證JWT令牌"""
    try:
        payload = jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            logger.warning("令牌中缺少用戶名")
            return None

        return payload
    except JWTError as e:
        logger.warning(f"JWT驗證失敗: {e}")
        return None
    except Exception as e:
        logger.error(f"令牌驗證錯誤: {e}")
        return None

async def get_current_trader(token: str = Depends(oauth2_scheme)) -> User:
    """獲取當前認證用戶"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="無效的認證憑證",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 驗證令牌
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    # 獲取用戶信息
    user_data = USERS_DB.get(username)
    if user_data is None:
        raise credentials_exception

    # 檢查用戶是否啟用
    if not user_data["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用戶賬戶已禁用"
        )

    user = User(
        username=user_data["username"],
        full_name=user_data["full_name"],
        email=user_data["email"],
        role=user_data["role"],
        permissions=user_data["permissions"],
        is_active=user_data["is_active"],
        created_at=user_data["created_at"],
        last_login=user_data["last_login"]
    )

    return user

async def get_current_active_trader(current_user: User = Depends(get_current_trader)) -> User:
    """獲取當前活躍用戶"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用戶賬戶已禁用")
    return current_user

def check_permissions(required_permission: str):
    """檢查用戶權限的裝飾器"""
    async def permission_checker(current_user: User = Depends(get_current_active_trader)):
        if required_permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"權限不足，需要權限: {required_permission}"
            )
        return current_user

    return permission_checker

# 角色權限檢查函數
def require_admin(current_user: User = Depends(get_current_active_trader)) -> User:
    """需要管理員權限"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理員權限"
        )
    return current_user

def require_trader_or_admin(current_user: User = Depends(get_current_active_trader)) -> User:
    """需要交易員或管理員權限"""
    if current_user.role not in [UserRole.TRADER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要交易員或管理員權限"
        )
    return current_user

# 刷新令牌功能
def create_refresh_token(username: str) -> str:
    """創建刷新令牌 (有效期7天)"""
    data = {
        "sub": username,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jose_jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

async def refresh_access_token(refresh_token: str) -> Optional[str]:
    """使用刷新令牌獲取新的訪問令牌"""
    try:
        payload = jose_jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        # 驗證是否為刷新令牌
        if payload.get("type") != "refresh":
            return None

        username = payload.get("sub")
        if not username:
            return None

        # 檢查用戶是否存在且啟用
        user_data = USERS_DB.get(username)
        if not user_data or not user_data["is_active"]:
            return None

        # 創建新的訪問令牌
        return create_access_token(data={"sub": username})

    except JWTError:
        return None

# 令牌黑名單 (用於登出功能)
TOKEN_BLACKLIST: set[str] = set()

def revoke_token(token: str) -> bool:
    """撤銷令牌 (添加到黑名單)"""
    try:
        payload = jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        if jti:
            TOKEN_BLACKLIST.add(jti)
            return True
    except JWTError:
        pass
    return False

def is_token_revoked(token: str) -> bool:
    """檢查令牌是否已撤銷"""
    try:
        payload = jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        return jti in TOKEN_BLACKLIST if jti else False
    except JWTError:
        return True
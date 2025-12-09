"""
认证API端点
Authentication API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from typing import List
from datetime import datetime
import logging

from auth_simple import (
    auth_service, User, UserLogin, Token, UserResponse,
    PasswordChange, PasswordStrengthResult, LoginHistoryResponse,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/auth", tags=["认证"])

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# 依赖注入
def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前用户"""
    return auth_service.get_current_user(token)

def get_db():
    """获取数据库会话"""
    return auth_service.get_db()

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, request: Request):
    """用户登录"""
    try:
        db = next(get_db())

        # 获取客户端信息
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")

        # 验证用户凭据
        user = auth_service.authenticate_user(
            user_credentials.username,
            user_credentials.password,
            db
        )

        if not user:
            # 记录失败的登录尝试
            existing_user = db.query(User).filter(User.username == user_credentials.username).first()
            if existing_user:
                auth_service.record_login_history(
                    existing_user,
                    False,
                    client_ip,
                    user_agent,
                    "用户名或密码错误"
                )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 检查用户是否激活
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="账户已被禁用"
            )

        # 创建访问令牌
        access_token_expires = auth_service.create_access_token(
            data={"sub": user.username},
            expires_delta=None  # 使用默认过期时间
        )

        # 记录成功的登录
        auth_service.record_login_history(user, True, client_ip, user_agent)

        # 构建响应
        token_response = Token(
            access_token=access_token_expires,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )

        logger.info(f"用户 {user.username} 登录成功")
        return token_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录过程中发生错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )
    finally:
        if 'db' in locals():
            db.close()

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """用户登出"""
    try:
        logger.info(f"用户 {current_user.username} 登出")
        return {"message": "登出成功"}

    except Exception as e:
        logger.error(f"登出过程中发生错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出失败"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse.from_orm(current_user)

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user)
):
    """修改密码"""
    try:
        db = next(get_db())

        # 验证新密码强度
        strength = auth_service.validate_password_strength(password_data.new_password)
        if strength.score < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"密码强度不够，当前强度: {strength.text}"
            )

        # 修改密码
        success = auth_service.change_password(
            current_user,
            password_data.old_password,
            password_data.new_password,
            db
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码错误"
            )

        logger.info(f"用户 {current_user.username} 修改密码成功")
        return {"message": "密码修改成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改密码过程中发生错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码修改失败"
        )
    finally:
        if 'db' in locals():
            db.close()

@router.get("/login-history", response_model=List[LoginHistoryResponse])
async def get_login_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """获取登录历史"""
    try:
        history = auth_service.get_user_login_history(current_user.id, limit)
        return history

    except Exception as e:
        logger.error(f"获取登录历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取登录历史失败"
        )

@router.post("/validate-password")
async def validate_password_strength(password: str):
    """验证密码强度"""
    try:
        strength = auth_service.validate_password_strength(password)
        return strength

    except Exception as e:
        logger.error(f"密码强度验证失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码强度验证失败"
        )

@router.get("/devices")
async def get_user_devices(current_user: User = Depends(get_current_user)):
    """获取用户设备列表"""
    try:
        devices = auth_service.get_user_devices(current_user.id)

        device_list = []
        for device in devices:
            device_info = {
                "id": device.id,
                "device_name": device.device_name,
                "device_type": device.device_type,
                "last_seen": device.last_seen.isoformat(),
                "is_trusted": device.is_trusted
            }
            device_list.append(device_info)

        return {"devices": device_list}

    except Exception as e:
        logger.error(f"获取设备列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取设备列表失败"
        )

@router.post("/devices/{device_id}/trust")
async def trust_device(
    device_id: int,
    current_user: User = Depends(get_current_user)
):
    """信任设备"""
    try:
        db = next(get_db())

        device = db.query(auth_service.UserDevice).filter(
            auth_service.UserDevice.id == device_id,
            auth_service.UserDevice.user_id == current_user.id
        ).first()

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="设备不存在"
            )

        device.is_trusted = True
        db.commit()

        logger.info(f"用户 {current_user.username} 信任设备: {device.device_name}")
        return {"message": "设备已标记为信任"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"信任设备失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="信任设备失败"
        )
    finally:
        if 'db' in locals():
            db.close()

@router.get("/check-token")
async def check_token_validity(current_user: User = Depends(get_current_user)):
    """检查Token有效性"""
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "expires_at": None  # 可以根据需要添加过期时间
    }
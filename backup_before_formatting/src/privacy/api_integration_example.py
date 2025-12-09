"""
API集成示例

展示如何在FastAPI应用中集成所有安全功能。

使用示例:
    from src.privacy.api_integration_example import create_secure_app

    app = create_secure_app()
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

from .anonymization import DataAnonymizer, get_anonymizer
from .data_classification import DataType, get_classification_manager
from .database_integration import (
    DatabaseEncryptionManager,
    EncryptedInteger,
    EncryptedString,
    EncryptedText,
    Strategy,
    Trade,
    User,
)
from .encryption import get_encryption
from .field_encryption import get_field_encryption
from .security_middleware import (
    DataValidationMiddleware,
    SecurityMiddleware,
    verify_api_key,
)
from .tls_manager import TLSManager

logger = logging.getLogger(__name__)

# FastAPI应用实例
app = FastAPI(
    title="HK Quant Trading System - Secure API",
    description="带有数据加密和匿名化的安全API",
    version="1.0.0",
)

# 添加安全中间件
app.add_middleware(SecurityMiddleware)
app.add_middleware(DataValidationMiddleware)


# Pydantic模型
class UserCreate(BaseModel):
    """用户创建模型"""

    email: EmailStr
    phone: Optional[str] = None
    name: str


class UserResponse(BaseModel):
    """用户响应模型"""

    id: int
    email: str
    phone: Optional[str] = None
    name: Optional[str] = None


class TradeCreate(BaseModel):
    """交易创建模型"""

    user_id: int
    symbol: str
    quantity: int
    price: float
    transaction_details: Optional[str] = None


class AnalyticsRequest(BaseModel):
    """分析请求模型"""

    data_type: str
    purpose: str = "analytics"
    anonymize: bool = True


# 初始化安全组件
encryption = get_encryption()
field_encryption = get_field_encryption()
anonymizer = get_anonymizer()
classification_manager = get_classification_manager()
tls_manager = TLSManager()


@app.get("/api / health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "security": "enabled", "encryption": "active"}


@app.get("/api / security / status")
async def security_status(current_user: str = Depends(verify_api_key)):
    """获取安全状态"""
    return {
        "encryption": "enabled",
        "tls": "enabled",
        "anonymization": "enabled",
        "classification": "enabled",
        "user": current_user,
    }


@app.post("/api / secure / users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate, current_user: str = Depends(verify_api_key)
):
    """
    创建用户（自动加密敏感数据）
    """
    # 注册数据到分类系统
    data_dict = user_data.dict()
    classification_manager.register_data(
        data_id=f"user_{user_data.email}", data=data_dict, data_type=DataType.USER_DATA
    )

    # 记录访问
    classification_manager.log_data_access(
        user_id=current_user,
        data_id=f"user_{user_data.email}",
        action="create",
        ip_address="127.0.0.1",
        user_agent="API",
        result="success",
    )

    # 实际应用中应该保存到数据库
    # 这里返回模拟数据
    return UserResponse(
        id=1, email=user_data.email, phone=user_data.phone, name=user_data.name
    )


@app.get("/api / secure / users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    anonymize: bool = Query(False, description="是否匿名化响应"),
    current_user: str = Depends(verify_api_key),
):
    """
    获取用户信息（可选匿名化）
    """
    # 模拟从数据库获取数据
    user_data = {
        "id": user_id,
        "email": "user@example.com",
        "phone": "1234567890",
        "name": "John Doe",
    }

    # 记录访问
    classification_manager.log_data_access(
        user_id=current_user,
        data_id=f"user_{user_id}",
        action="read",
        ip_address="127.0.0.1",
        user_agent="API",
        result="success",
    )

    # 如果需要匿名化
    if anonymize:
        user_data = anonymizer.anonymize_for_analytics(user_data, "analytics")

    return UserResponse(**user_data)


@app.post("/api / secure / trades")
async def create_trade(
    trade_data: TradeCreate, current_user: str = Depends(verify_api_key)
):
    """
    创建交易（自动加密交易详情）
    """
    # 注册数据
    data_dict = trade_data.dict()
    classification_manager.register_data(
        data_id=f"trade_{trade_data.user_id}_{trade_data.symbol}",
        data=data_dict,
        data_type=DataType.TRADE_DATA,
    )

    # 加密敏感字段
    sensitive_fields = ["price", "transaction_details", "account_number"]
    encrypted_data = field_encryption.encrypt_fields(data_dict, sensitive_fields)

    # 记录访问
    classification_manager.log_data_access(
        user_id=current_user,
        data_id=f"trade_{trade_data.user_id}_{trade_data.symbol}",
        action="create",
        ip_address="127.0.0.1",
        user_agent="API",
        result="success",
    )

    return {
        "status": "created",
        "trade_id": 1,
        "encrypted": True,
        "encrypted_fields": sensitive_fields,
    }


def create_secure_app() -> FastAPI:
    """创建并配置安全的FastAPI应用"""
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app

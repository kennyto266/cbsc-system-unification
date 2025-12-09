"""
港股量化交易系統 - 訪問控制完整使用示例
展示如何集成RBAC、ABAC、MFA、會話管理和API訪問控制
"""

import asyncio
import logging
import os
import sys
from typing import Any, Dict, Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 添加項目根目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .abac import ABACManager, Context
from .api_access import APIAccessManager
from .mfa import MFAManager, MFAMethodType
from .middleware import (
    AccessControlManager,
    APIAccessMiddleware,
    AuthenticationMiddleware,
    AuthorizationMiddleware,
    SecurityHeadersMiddleware,
)
from .rbac import RBACManager, Role, RoleType
from .session import SessionManager, TokenManager

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("access_control.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# 創建FastAPI應用
app = FastAPI(
    title="港股量化交易系統 - 訪問控制API",
    description="完整的訪問控制和權限管理系統",
    version="1.0.0",
)

# 添加CORS中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化訪問控制管理器
access_control = AccessControlManager(
    rbac_db_path="data / example_rbac.db",
    mfa_db_path="data / example_mfa.db",
    session_db_path="data / example_sessions.db",
    api_db_path="data / example_api.db",
    abac_policy_path="data / example_abac_policies.json",
)

# 添加安全頭中間件
app.add_middleware(SecurityHeadersMiddleware)

# 添加認證中間件
app.add_middleware(
    AuthenticationMiddleware,
    rbac_manager=access_control.rbac_manager,
    mfa_manager=access_control.mfa_manager,
    session_manager=access_control.session_manager,
    require_mfa=True,
)

# 添加授權中間件
app.add_middleware(
    AuthorizationMiddleware,
    rbac_manager=access_control.rbac_manager,
    abac_manager=access_control.abac_manager,
)

# 添加API訪問控制中間件
app.add_middleware(
    APIAccessMiddleware, api_access_manager=access_control.api_access_manager
)


# ========================
# 認證相關端點
# ========================


@app.post("/auth / login")
async def login(request: Request):
    """用戶登錄"""
    data = await request.json()
    username = data.get("username")
    password = data.get("password")

    # 簡化的認證邏輯（實際中應使用加密密碼）
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用戶名和密碼不能為空"
        )

    # 檢查憑據（這裡應該查詢用戶數據庫）
    # 模擬檢查
    if username == "admin" and password == "admin123":
        user_id = "admin"
        roles = ["admin"]
    elif username == "trader" and password == "trader123":
        user_id = "trader"
        roles = ["trader"]
    else:
        # 記錄失敗的登錄嘗試
        access_control.session_manager.log_login_attempt(
            user_id=username,
            ip_address=request.client.host,
            success=False,
            failure_reason="invalid_credentials",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用戶名或密碼錯誤"
        )

    # 創建會話
    session, access_token, refresh_token, id_token = (
        access_control.session_manager.create_session(
            user_id=user_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user - agent", ""),
            device_id=data.get("device_id", "web"),
            device_name="Web Browser",
        )
    )

    # 記錄成功的登錄
    access_control.session_manager.log_login_attempt(
        user_id=user_id, ip_address=request.client.host, success=True
    )

    return {
        "success": True,
        "message": "登錄成功",
        "data": {
            "user_id": user_id,
            "session_id": session.session_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "id_token": id_token,
            "expires_in": 3600,
        },
    }


@app.post("/auth / logout")
async def logout(request: Request):
    """用戶登出"""
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要認證")

    user = request.state.user
    session = request.state.session

    # 終止會話
    if session:
        access_control.session_manager.terminate_session(
            session.session_id, "user_logout"
        )

    return {"success": True, "message": "已成功登出"}


@app.get("/auth / me")
async def get_current_user(request: Request):
    """獲取當前用戶信息"""
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要認證")

    user = request.state.user
    roles = access_control.rbac_manager.get_user_roles(user["user_id"])

    return {
        "success": True,
        "data": {
            "user_id": user["user_id"],
            "session_id": user["session_id"],
            "roles": [r.to_dict() for r in roles],
        },
    }


# ========================
# MFA相關端點
# ========================


@app.post("/mfa / setup / totp")
async def setup_totp(request: Request):
    """設置TOTP認證"""
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要認證")

    user_id = request.state.user["user_id"]
    data = await request.json()
    account_name = data.get("account_name", f"{user_id}@quant - system.com")

    secret, qr_code = await access_control.mfa_manager.setup_totp(user_id, account_name)

    # 將QR碼轉換為base64
    import base64

    qr_code_b64 = base64.b64encode(qr_code).decode()

    return {
        "success": True,
        "message": "TOTP設置成功",
        "data": {"secret": secret, "qr_code": f"data:image / png;base64,{qr_code_b64}"},
    }


@app.post("/mfa / verify / totp")
async def verify_totp(request: Request):
    """驗證TOTP"""
    data = await request.json()
    token = data.get("token")

    # 獲取用戶ID（從認證token或session）
    # 簡化實現
    user_id = "admin"  # 實際中應從request.state.user獲取

    is_valid = await access_control.mfa_manager.verify_totp(user_id, token)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="TOTP驗證失敗"
        )

    return {"success": True, "message": "TOTP驗證成功"}


@app.get("/mfa / methods")
async def get_mfa_methods(request: Request):
    """獲取用戶的MFA方法"""
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要認證")

    user_id = request.state.user["user_id"]
    methods = access_control.mfa_manager.get_user_mfa_methods(user_id)

    return {"success": True, "data": {"methods": [m.to_dict() for m in methods]}}


# ========================
# 角色和權限管理端點
# ========================


@app.get("/rbac / roles")
async def list_roles():
    """獲取所有角色"""
    roles = access_control.rbac_manager.get_all_roles()
    return {"success": True, "data": {"roles": [r.to_dict() for r in roles]}}


@app.post("/rbac / assign - role")
async def assign_role(request: Request):
    """分配角色給用戶（需要admin權限）"""
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要認證")

    # 檢查admin權限
    user_roles = access_control.rbac_manager.get_user_roles(
        request.state.user["user_id"]
    )
    if not any(r.name == "admin" for r in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要admin權限"
        )

    data = await request.json()
    target_user_id = data.get("user_id")
    role_name = data.get("role_name")

    role = access_control.rbac_manager.get_role_by_name(role_name)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"角色 {role_name} 不存在"
        )

    access_control.rbac_manager.assign_role_to_user(
        user_id=target_user_id,
        role_id=role.id,
        assigned_by=request.state.user["user_id"],
    )

    return {
        "success": True,
        "message": f"已將角色 {role_name} 分配給用戶 {target_user_id}",
    }


# ========================
# API密鑰管理端點
# ========================


@app.post("/api / keys")
async def create_api_key(request: Request):
    """創建API密鑰"""
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要認證")

    user_id = request.state.user["user_id"]
    data = await request.json()
    name = data.get("name", "My API Key")
    scopes = data.get("scopes", ["data:read"])
    rate_limit = data.get("rate_limit", 60)

    api_key, api_key_obj = access_control.api_access_manager.generate_api_key(
        user_id=user_id, name=name, scopes=scopes, rate_limit=rate_limit
    )

    return {
        "success": True,
        "message": "API密鑰創建成功",
        "data": {
            "api_key": api_key,
            "key_id": api_key_obj.key_id,
            "scopes": list(api_key_obj.scopes),
            "rate_limit": api_key_obj.rate_limit,
        },
    }


@app.get("/api / keys")
async def list_api_keys(request: Request):
    """獲取用戶的API密鑰"""
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要認證")

    user_id = request.state.user["user_id"]
    keys = access_control.api_access_manager.get_user_api_keys(user_id)

    return {"success": True, "data": {"keys": [k.to_dict() for k in keys]}}


# ========================
# 業務API端點示例
# ========================


@app.get("/api / v1 / data/{symbol}")
async def get_stock_data(request: Request, symbol: str):
    """獲取股票數據（需要data:read權限）"""
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要認證")

    # 這裡可以添加實際的數據獲取邏輯
    return {
        "success": True,
        "data": {
            "symbol": symbol,
            "price": 350.0,
            "change": 5.0,
            "change_percent": 1.45,
            "timestamp": "2025 - 11 - 09T20:11:00Z",
        },
    }


@app.post("/api / v1 / trade / execute")
async def execute_trade(request: Request):
    """執行交易（需要trade:execute權限）"""
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要認證")

    # 檢查交易員或管理員角色
    user_roles = access_control.rbac_manager.get_user_roles(
        request.state.user["user_id"]
    )
    has_permission = any(r.name in ["trader", "admin"] for r in user_roles)

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要trader或admin權限"
        )

    data = await request.json()
    # 這裡可以添加實際的交易邏輯

    return {
        "success": True,
        "message": "交易已提交",
        "data": {
            "order_id": "ORD - 2025 - 001",
            "symbol": data.get("symbol"),
            "quantity": data.get("quantity"),
            "price": data.get("price"),
            "status": "pending",
        },
    }


@app.get("/api / v1 / portfolio")
async def get_portfolio(request: Request):
    """獲取投資組合（需要portfolio:view權限）"""
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要認證")

    return {
        "success": True,
        "data": {
            "total_value": 1000000.0,
            "cash": 200000.0,
            "positions": [
                {
                    "symbol": "0700.HK",
                    "quantity": 1000,
                    "value": 350000.0,
                    "unrealized_pnl": 15000.0,
                }
            ],
        },
    }


# ========================
# 系統管理和監控端點
# ========================


@app.get("/admin / stats")
async def get_system_stats(request: Request):
    """獲取系統統計信息（僅admin）"""
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要認證")

    user_roles = access_control.rbac_manager.get_user_roles(
        request.state.user["user_id"]
    )
    if not any(r.name == "admin" for r in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要admin權限"
        )

    return {
        "success": True,
        "data": {
            "rbac": {"total_roles": len(access_control.rbac_manager.get_all_roles())},
            "session": access_control.session_manager.get_session_stats(),
            "api": access_control.api_access_manager.get_api_usage_stats(),
            "abac": access_control.abac_manager.get_policy_summary(),
        },
    }


@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "timestamp": "2025 - 11 - 09T20:11:00Z",
        "version": "1.0.0",
    }


# ========================
# 初始化腳本
# ========================


async def init_example_data():
    """初始化示例數據"""
    logger.info("初始化示例數據...")

    # 為admin用戶分配admin角色
    admin_role = access_control.rbac_manager.get_role_by_name("admin")
    if admin_role:
        access_control.rbac_manager.assign_role_to_user(
            user_id="admin", role_id=admin_role.id, assigned_by="system"
        )

    # 為trader用戶分配trader角色
    trader_role = access_control.rbac_manager.get_role_by_name("trader")
    if trader_role:
        access_control.rbac_manager.assign_role_to_user(
            user_id="trader", role_id=trader_role.id, assigned_by="system"
        )

    # 為admin用戶設置TOTP
    try:
        await access_control.mfa_manager.setup_totp("admin", "admin@quant - system.com")
        logger.info("已為admin用戶設置TOTP")
    except Exception as e:
        logger.warning(f"TOTP設置失敗: {e}")

    logger.info("示例數據初始化完成")


# ========================
# 啟動應用
# ========================


@app.on_event("startup")
async def startup_event():
    """啟動時初始化"""
    # 創建數據目錄
    os.makedirs("data", exist_ok=True)

    # 初始化示例數據
    await init_example_data()

    logger.info("港股量化交易系統 - 訪問控制API啟動完成")


if __name__ == "__main__":
    uvicorn.run(
        "example_usage:app", host="0.0.0.0", port=8001, reload=True, log_level="info"
    )

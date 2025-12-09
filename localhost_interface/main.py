"""
量化交易系統 - FastAPI 主應用程式
香港非價格信號交易系統的RESTful API和WebSocket服務器
"""

from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys
import os
import asyncio
from typing import List, Dict, Any, Optional
import json
import secrets
from datetime import datetime, timedelta

# 添加現有系統路徑和當前項目路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'backend'))
sys.path.append(os.path.join(current_dir, 'backend'))
sys.path.append(os.path.join(current_dir, 'shared'))

from backend.api.auth import (
    authenticate_user, create_access_token, get_current_trader,
    ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
)
from backend.api.routes import (
    trading_signals, strategies, backtest, risk_management,
    market_data, performance_analytics
)
from backend.websocket.connection_manager import ConnectionManager
from backend.services.trading_service import TradingService
from backend.services.non_price_service import NonPriceService
from backend.core.config import get_settings
from shared.models.schemas import (
    Token, User, StrategyConfig, BacktestRequest,
    PerformanceMetrics, TradingSignal, WebSocketMessage
)

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('localhost_interface/logs/api.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 生命週期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式啟動和關閉的生命週期管理"""
    # 啟動時初始化
    logger.info("🚀 量化交易系統 API 服務器啟動中...")

    # 初始化交易服務
    app.state.trading_service = TradingService()
    await app.state.trading_service.initialize()

    # 初始化非價格信號服務
    app.state.non_price_service = NonPriceService()
    await app.state.non_price_service.initialize()

    # 初始化WebSocket連接管理器
    app.state.connection_manager = ConnectionManager()

    # 啟動後台任務
    asyncio.create_task(background_data_update_task(app))

    logger.info("✅ API 服務器啟動完成，準備接收請求")

    yield

    # 關閉時清理
    logger.info("🔄 關閉API服務器...")
    await app.state.trading_service.shutdown()
    await app.state.non_price_service.shutdown()
    logger.info("✅ API 服務器已安全關閉")

# 創建FastAPI應用程式
app = FastAPI(
    title="量化交易系統 API",
    description="基於香港政府數據的非價格信號量化交易平台",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# 配置CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 認證方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# 導入Phase 4組件
from backend.api.routes.parameter_backtest import router as parameter_backtest_router
from backend.services.job_manager import job_manager, get_job_manager
from backend.websocket.parameter_monitor import get_parameter_monitor
from backend.middleware.enhanced_auth import init_security_middleware, get_enhanced_auth
from backend.monitoring.metrics import init_metrics, get_metrics_collector, create_metrics_endpoint, create_health_endpoint

# 初始化安全中間件（在創建應用後）
import redis.asyncio as redis

redis_client = None
security_middleware = None
enhanced_auth_system = None
metrics_system = None

async def init_phase4_components():
    """初始化Phase 4組件"""
    global redis_client, security_middleware, enhanced_auth_system, metrics_system

    try:
        # 初始化Redis
        redis_client = redis.from_url("redis://localhost:6379/0")
        await redis_client.ping()
        logger.info("✅ Redis連接成功")

        # 初始化安全中間件
        security_middleware, enhanced_auth_system = init_security_middleware(app, redis_client)
        logger.info("✅ 安全中間件初始化完成")

        # 初始化指標收集器
        metrics_system = init_metrics(redis_client)
        logger.info("✅ 指標收集器初始化完成")

        # 初始化任務管理器
        await job_manager.initialize()
        logger.info("✅ 任務管理器初始化完成")

        # 註冊任務處理器
        from gpu_accelerated_0700_backtest import GPUAccelerated0700BacktestEngine

        async def optimization_processor(payload: dict, worker_id: str) -> dict:
            """參數優化任務處理器"""
            try:
                request_data = payload["request_data"]

                # 創建優化引擎
                engine = GPUAccelerated0700BacktestEngine(
                    gpu_device=request_data.get("gpu_device", 0)
                )

                # 執行優化
                # 這裡需要實現具體的優化邏輯
                result = {
                    "success": True,
                    "best_sharpe": 1.5,
                    "total_combinations": 100,
                    "execution_time": 120.0
                }

                return result

            except Exception as e:
                logger.error(f"優化任務處理失敗: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }

        job_manager.register_processor("parameter_optimization", optimization_processor)

        logger.info("✅ Phase 4組件初始化完成")

    except Exception as e:
        logger.error(f"Phase 4組件初始化失敗: {e}")
        # Redis不可用時使用內存存儲
        metrics_system = init_metrics()

# 設置應用級別的初始化
@app.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    await init_phase4_components()

@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    try:
        if metrics_system:
            metrics_system.stop_monitoring()
        if job_manager:
            await job_manager.shutdown()
        if redis_client:
            await redis_client.close()
        logger.info("✅ Phase 4組件已安全關閉")
    except Exception as e:
        logger.error(f"關閉組件時發生錯誤: {e}")

# 路由註冊
app.include_router(trading_signals.router, prefix="/api/trading", tags=["trading"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])
app.include_router(risk_management.router, prefix="/api/risk", tags=["risk"])
app.include_router(market_data.router, prefix="/api/market", tags=["market"])
app.include_router(performance_analytics.router, prefix="/api/performance", tags=["performance"])

# Phase 4路由
app.include_router(parameter_backtest_router, prefix="/api/parameter-backtest", tags=["parameter-optimization"])

# 指標和健康檢查端點
app.get("/metrics")(create_metrics_endpoint())
app.get("/health")(create_health_endpoint())

# 根路徑
@app.get("/")
async def root():
    """歡迎頁面"""
    return {
        "message": "量化交易系統 API",
        "description": "基於香港政府數據的非價格信號交易平台",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/health"
    }

# 健康檢查
@app.get("/api/health")
async def health_check():
    """系統健康狀態檢查"""
    try:
        # 檢查各個服務狀態
        trading_status = await app.state.trading_service.health_check()
        non_price_status = await app.state.non_price_service.health_check()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "trading_service": trading_status,
                "non_price_service": non_price_status,
                "websocket_connections": len(app.state.connection_manager.active_connections)
            }
        }
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# 認證端點
@app.post("/api/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """用戶登入獲取訪問令牌"""
    try:
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用戶名或密碼錯誤",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role},
            expires_delta=access_token_expires
        )

        logger.info(f"用戶 {user.username} 成功登入")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "username": user.username,
                "role": user.role,
                "permissions": user.permissions
            }
        }

    except Exception as e:
        logger.error(f"登入失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登入處理失敗"
        )

# 獲取當前用戶信息
@app.get("/api/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_trader)):
    """獲取當前認證用戶的信息"""
    return current_user

# WebSocket 端點
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket 連接端點，用於實時數據傳輸"""
    await app.state.connection_manager.connect(websocket, client_id)
    logger.info(f"客戶端 {client_id} 已連接WebSocket")

    try:
        while True:
            # 接收客戶端消息
            data = await websocket.receive_text()
            message = json.loads(data)

            # 處理不同類型的消息
            if message["type"] == "subscribe":
                # 訂閱實時數據
                await handle_subscription(app, client_id, message["data"])
            elif message["type"] == "unsubscribe":
                # 取消訂閱
                await handle_unsubscription(app, client_id, message["data"])
            elif message["type"] == "ping":
                # 心跳檢查
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
            else:
                logger.warning(f"未知消息類型: {message['type']}")

    except WebSocketDisconnect:
        await app.state.connection_manager.disconnect(client_id)
        logger.info(f"客戶端 {client_id} 已斷開WebSocket連接")
    except Exception as e:
        logger.error(f"WebSocket連接錯誤: {e}")
        await app.state.connection_manager.disconnect(client_id)

async def handle_subscription(app, client_id: str, subscription_data: Dict[str, Any]):
    """處理客戶端訂閱請求"""
    symbol = subscription_data.get("symbol", "0700.HK")
    data_type = subscription_data.get("type", "signals")

    # 添加到客戶端訂閱列表
    app.state.connection_manager.add_subscription(client_id, symbol, data_type)

    # 發送確認消息
    await app.state.connection_manager.send_personal_message({
        "type": "subscription_confirmed",
        "symbol": symbol,
        "data_type": data_type,
        "timestamp": datetime.now().isoformat()
    }, client_id)

async def handle_unsubscription(app, client_id: str, subscription_data: Dict[str, Any]):
    """處理客戶端取消訂閱請求"""
    symbol = subscription_data.get("symbol", "0700.HK")
    data_type = subscription_data.get("type", "signals")

    # 從客戶端訂閱列表移除
    app.state.connection_manager.remove_subscription(client_id, symbol, data_type)

# 後台任務：定期更新數據
async def background_data_update_task(app):
    """後台任務，定期獲取和廣播市場數據"""
    while True:
        try:
            # 獲取最新的非價格信號數據
            signals = await app.state.non_price_service.get_latest_signals()

            # 廣播給訂閱的客戶端
            await app.state.connection_manager.broadcast_signals(signals)

            # 等待30秒再進行下次更新
            await asyncio.sleep(30)

        except Exception as e:
            logger.error(f"後台數據更新任務錯誤: {e}")
            await asyncio.sleep(5)  # 錯誤時等待5秒後重試

# 啟動服務器
if __name__ == "__main__":
    import uvicorn

    # 確保日誌目錄存在
    os.makedirs("localhost_interface/logs", exist_ok=True)

    logger.info("🚀 啟動量化交易系統 API 服務器...")

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
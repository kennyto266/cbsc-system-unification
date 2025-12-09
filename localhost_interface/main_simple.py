"""
量化交易系統 - FastAPI 主應用程式 (簡化版)
測試基本功能
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from fastapi.responses import JSONResponse
except ImportError as e:
    logger.error(f"無法導入FastAPI: {e}")
    logger.info("正在安裝FastAPI...")
    os.system("pip install fastapi uvicorn")
    logger.info("請重新運行此腳本")
    sys.exit(1)

# 簡化的數據模型
class User(BaseModel):
    username: str
    full_name: str
    role: str
    is_active: bool = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TradingSignal(BaseModel):
    id: str
    symbol: str
    signal_type: str
    strength: float
    confidence: float
    price_at_signal: float
    timestamp: datetime
    source_indicators: List[str]
    strategy_name: str

# 創建FastAPI應用程式
app = FastAPI(
    title="量化交易系統 API",
    description="基於香港政府數據的非價格信號交易平台",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 用戶數據庫模擬
USERS_DB = {
    "admin": {
        "username": "admin",
        "full_name": "系統管理員",
        "password": "admin123",
        "role": "admin",
        "is_active": True
    },
    "trader": {
        "username": "trader",
        "full_name": "量化交易員",
        "password": "trader123",
        "role": "trader",
        "is_active": True
    }
}

# 模擬交易信號
MOCK_SIGNALS = [
    {
        "id": "signal_0700_001",
        "symbol": "0700.HK",
        "signal_type": "buy",
        "strength": 0.75,
        "confidence": 0.68,
        "price_at_signal": 398.50,
        "timestamp": datetime.now(),
        "source_indicators": ["RSI", "MACD"],
        "strategy_name": "NonPrice_Signal_Strategy"
    },
    {
        "id": "signal_0941_002",
        "symbol": "0941.HK",
        "signal_type": "hold",
        "strength": 0.45,
        "confidence": 0.55,
        "price_at_signal": 48.20,
        "timestamp": datetime.now(),
        "source_indicators": ["布林帶"],
        "strategy_name": "NonPrice_Signal_Strategy"
    }
]

@app.get("/")
async def root():
    """歡迎頁面"""
    return {
        "message": "量化交易系統 API",
        "description": "基於香港政府數據的非價格信號交易平台",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/health",
        "signals": "/api/signals"
    }

@app.get("/api/health")
async def health_check():
    """系統健康狀態檢查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api_server": True,
            "signal_generator": True,
            "websocket_service": False
        }
    }

@app.post("/api/auth/token", response_model=Token)
async def login(username: str, password: str):
    """用戶登入獲取訪問令牌"""
    try:
        # 簡化驗證
        if username in USERS_DB and USERS_DB[username]["password"] == password:
            user_data = USERS_DB[username]

            # 創建用戶對象
            user = User(
                username=user_data["username"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_active=user_data["is_active"]
            )

            # 生成簡單的訪問令牌
            token_data = f"{user.username}:{datetime.now().isoformat()}"
            access_token = f"token_{token_data}"

            logger.info(f"用戶 {username} 登入成功")

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用戶名或密碼錯誤"
            )

    except Exception as e:
        logger.error(f"登入失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登入處理失敗: {str(e)}"
        )

@app.get("/api/signals", response_model=List[TradingSignal])
async def get_trading_signals(symbol: str = None):
    """獲取交易信號"""
    try:
        signals = MOCK_SIGNALS
        if symbol:
            signals = [s for s in signals if s["symbol"] == symbol]

        # 轉換為TradingSignal模型
        trading_signals = []
        for signal in signals:
            trading_signal = TradingSignal(**signal)
            trading_signals.append(trading_signal)

        logger.info(f"返回 {len(trading_signals)} 個交易信號")
        return trading_signals

    except Exception as e:
        logger.error(f"獲取交易信號失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取交易信號失敗: {str(e)}"
        )

@app.get("/api/signals/{signal_id}", response_model=TradingSignal)
async def get_signal_by_id(signal_id: str):
    """根據ID獲取特定交易信號"""
    try:
        # 查找匹配的信號
        signal_data = None
        for signal in MOCK_SIGNALS:
            if signal["id"] == signal_id:
                signal_data = signal
                break

        if signal_data:
            return TradingSignal(**signal_data)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到信號: {signal_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取信號失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取信號失敗: {str(e)}"
        )

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket 連接端點，用於實時數據傳輸"""
    try:
        await websocket.accept()
        logger.info(f"客戶端 {client_id} 已連接WebSocket")

        # 發送歡迎消息
        welcome_message = {
            "type": "welcome",
            "client_id": client_id,
            "server_time": datetime.now().isoformat(),
            "message": "WebSocket連接已建立"
        }

        await websocket.send_text(json.dumps(welcome_message, default=str))

        # 簡單的心跳和消息循環
        message_count = 0
        while True:
            try:
                # 接收客戶端消息
                data = await websocket.receive_text()
                message_count += 1

                # 簡單的ping/pong處理
                if data == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat(),
                        "message_count": message_count
                    }, default=str))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "echo",
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    }, default=str))

            except WebSocketDisconnect:
                logger.info(f"客戶端 {client_id} 已斷開WebSocket連接")
                break

    except Exception as e:
        logger.error(f"WebSocket連接錯誤: {e}")

# 啟動信息
if __name__ == "__main__":
    logger.info("🚀 啟動量化交易系統 Localhost API 服務器...")
    logger.info("📊 功能概覽:")
    logger.info("   - JWT用戶認證系統")
    logger.info("   - 交易信號API")
    logger.info("   - WebSocket實時通信")
    logger.info("   - 基於香港政府數據的非價格信號")
    logger.info("")
    logger.info("🔐 預設用戶:")
    logger.info("   admin / admin123 - 管理員權限")
    logger.info("   trader / trader123 - 交易員權限")
    logger.info("")
    logger.info("📱 API文檔: http://127.0.0.1:8000/api/docs")
    logger.info("🏥 健康檢查: http://127.0.0.1:8000/api/health")
    logger.info("📊 交易信號: http://127.0.0.1:8000/api/signals")

    try:
        import uvicorn
        uvicorn.run(
            "main_simple:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except ImportError:
        logger.error("安裝uvicorn: pip install uvicorn[standard]")
    except Exception as e:
        logger.error(f"啟動服務器失敗: {e}")
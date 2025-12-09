#!/usr/bin/env python3
"""
實時WebSocket服務器啟動腳本
"""

import asyncio
import logging
import sys
import os
import json
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
from datetime import datetime

# 導入WebSocket管理器
from src.api.websocket_server import get_websocket_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('websocket_server.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 創建FastAPI應用
app = FastAPI(
    title="CBSC策略實時數據服務器",
    description="提供WebSocket實時數據推送和REST API服務",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 獲取WebSocket管理器
websocket_manager = get_websocket_manager()

@app.get("/")
async def root():
    """根路徑 - 服務器狀態"""
    return {
        "service": "CBSC策略實時數據服務器",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "websocket_endpoint": "ws://localhost:3004/ws",
        "active_connections": len(websocket_manager.active_connections)
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "active_connections": len(websocket_manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket連接端點"""
    client_id = f"client_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(websocket)}"

    logger.info(f"New WebSocket connection attempt: {client_id}")

    # 嘗試建立連接
    connected = await websocket_manager.connect(websocket, client_id)

    if not connected:
        logger.error(f"Failed to establish WebSocket connection for {client_id}")
        return

    try:
        while True:
            # 接收客戶端消息
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await websocket_manager.handle_message(client_id, message)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received from {client_id}: {e}")
                # 發送錯誤響應
                await websocket_manager.send_personal_message(client_id, {
                    'type': 'error',
                    'message': 'Invalid JSON format',
                    'timestamp': datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket connection for {client_id}: {e}")
    finally:
        await websocket_manager.disconnect(client_id)

@app.get("/api/strategies")
async def get_strategies():
    """獲取策略列表API"""
    try:
        return {
            "success": True,
            "data": websocket_manager.mock_strategies,
            "total": len(websocket_manager.mock_strategies),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/stats")
async def get_stats():
    """獲取統計信息API"""
    try:
        return {
            "success": True,
            "data": {
                "active_connections": len(websocket_manager.active_connections),
                "total_strategies": len(websocket_manager.mock_strategies),
                "channel_subscriptions": {
                    channel: len(subscribers)
                    for channel, subscribers in websocket_manager.channel_subscriptions.items()
                },
                "server_uptime": "N/A",  # 實際應用中計算真實運行時間
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/notify/{channel}")
async def send_notification(channel: str, message: dict):
    """發送通知到指定頻道"""
    try:
        await websocket_manager.broadcast_to_channel(channel, {
            'type': 'notification',
            'channel': channel,
            'data': message,
            'timestamp': datetime.now().isoformat()
        })

        return {
            "success": True,
            "message": f"Notification sent to {channel}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# 啟動時事件
@app.on_event("startup")
async def startup_event():
    """應用啟動時執行"""
    logger.info("Starting CBSC Real-time WebSocket Server...")
    logger.info(f"WebSocket endpoint: ws://localhost:3004/ws")
    logger.info(f"API documentation: http://localhost:3004/docs")

    # 啟動數據模擬
    asyncio.create_task(websocket_manager.start_data_simulation())
    logger.info("Data simulation started")

@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉時執行"""
    logger.info("Shutting down CBSC Real-time WebSocket Server...")
    websocket_manager.stop_data_simulation()
    logger.info("Data simulation stopped")

# 簡單的測試頁面
@app.get("/test", response_class=HTMLResponse)
async def test_websocket():
    """WebSocket測試頁面"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .connected { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .disconnected { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .messages { border: 1px solid #ddd; padding: 10px; height: 300px; overflow-y: scroll; }
            .message { margin: 5px 0; padding: 5px; background: #f9f9f9; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>WebSocket測試</h1>
        <div id="status" class="status disconnected">未連接</div>
        <button onclick="connect()">連接</button>
        <button onclick="disconnect()">斷開</button>
        <button onclick="subscribe()">訂閱性能更新</button>
        <div id="messages" class="messages"></div>

        <script>
            let ws = null;

            function connect() {
                ws = new WebSocket('ws://localhost:3004/ws');

                ws.onopen = function() {
                    updateStatus('connected', '已連接');
                    addMessage('已連接到服務器');
                };

                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    addMessage('收到消息: ' + JSON.stringify(data, null, 2));
                };

                ws.onclose = function() {
                    updateStatus('disconnected', '未連接');
                    addMessage('連接已斷開');
                };

                ws.onerror = function(error) {
                    addMessage('錯誤: ' + error);
                };
            }

            function disconnect() {
                if (ws) {
                    ws.close();
                    ws = null;
                }
            }

            function subscribe() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'subscribe',
                        data: {
                            channel: 'performance_updates'
                        }
                    }));
                    addMessage('已訂閱性能更新');
                }
            }

            function updateStatus(status, text) {
                const statusEl = document.getElementById('status');
                statusEl.className = 'status ' + status;
                statusEl.textContent = text;
            }

            function addMessage(message) {
                const messagesEl = document.getElementById('messages');
                const messageEl = document.createElement('div');
                messageEl.className = 'message';
                messageEl.innerHTML = '<strong>' + new Date().toLocaleTimeString() + '</strong>: ' + message;
                messagesEl.appendChild(messageEl);
                messagesEl.scrollTop = messagesEl.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    # 設置啟動參數
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=3004,
        log_level="info",
        access_log=True,
        reload=False
    )

    # 啟動服務器
    server = uvicorn.Server(config)

    try:
        logger.info("Starting CBSC Real-time WebSocket Server on port 3004...")
        server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
"""
生產級參數控制系統演示
基於專家審查建議的完整實施展示

Features:
- FastAPI + WebSocket 生產級架構
- 企業級安全框架
- 實時參數控制和計算
- 性能監控和統計
- 完整的錯誤處理

Usage:
    python production_parameter_system_demo.py

Author: CBSC Quantitative Trading System
Version: 1.0.0
"""

import asyncio
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path

# 添加項目根目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

# 導入生產級組件
from src.security.enterprise_security import rate_limiter, RateLimitMiddleware
from src.api.production_parameter_controls import (
    SecureParameterUpdate, session_manager, ParameterResponse
)
from src.websocket.production_websocket_manager import websocket_manager

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('production_parameter_system.log')
    ]
)

logger = logging.getLogger(__name__)

# 創建FastAPI應用
app = FastAPI(
    title="CBSC 生產級參數控制系統",
    description="基於專家審查建議的企業級量化交易參數控制平台",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應該限制為特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加速率限制中間件
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)


@app.get("/", response_class=HTMLResponse)
async def get_root():
    """
    提供演示頁面
    """
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CBSC 生產級參數控制系統</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .stat-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }
            .stat-value {
                font-size: 2em;
                font-weight: bold;
                margin-bottom: 5px;
            }
            .stat-label {
                font-size: 0.9em;
                opacity: 0.9;
            }
            .parameter-controls {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .parameter-group {
                margin-bottom: 15px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
                color: #495057;
            }
            input[type="range"] {
                width: 100%;
                margin-bottom: 5px;
            }
            .value-display {
                text-align: center;
                color: #007bff;
                font-weight: bold;
            }
            button {
                background: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin: 5px;
            }
            button:hover {
                background: #0056b3;
            }
            .results {
                background: #e9ecef;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
                white-space: pre-wrap;
                font-family: monospace;
                max-height: 400px;
                overflow-y: auto;
            }
            .connection-status {
                text-align: center;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
                font-weight: bold;
            }
            .connected {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .disconnected {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .error {
                background: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 CBSC 生產級參數控制系統</h1>
            <p><strong>基於專家審查建議的企業級量化交易參數控制平台</strong></p>

            <div id="connectionStatus" class="connection-status disconnected">
                連接狀態: 未連接
            </div>

            <div class="stats" id="stats">
                <div class="stat-card">
                    <div class="stat-value" id="activeConnections">0</div>
                    <div class="stat-label">活躍連接</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="totalMessages">0</div>
                    <div class="stat-label">消息總數</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="errorCount">0</div>
                    <div class="stat-label">錯誤次數</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="avgProcessingTime">0ms</div>
                    <div class="stat-label">平均處理時間</div>
                </div>
            </div>

            <div class="parameter-controls">
                <h3>📊 參數控制</h3>

                <div class="parameter-group">
                    <label for="rsiPeriod">RSI 週期 (5-50)</label>
                    <input type="range" id="rsiPeriod" min="5" max="50" value="14">
                    <div class="value-display" id="rsiPeriodValue">14</div>
                </div>

                <div class="parameter-group">
                    <label for="sentimentThreshold">情緒閾值 (0.1-1.0)</label>
                    <input type="range" id="sentimentThreshold" min="0.1" max="1.0" step="0.05" value="0.7">
                    <div class="value-display" id="sentimentThresholdValue">0.70</div>
                </div>

                <div class="parameter-group">
                    <label for="maShort">短期均線 (5-30)</label>
                    <input type="range" id="maShort" min="5" max="30" value="10">
                    <div class="value-display" id="maShortValue">10</div>
                </div>

                <div class="parameter-group">
                    <label for="maLong">長期均線 (20-100)</label>
                    <input type="range" id="maLong" min="20" max="100" value="30">
                    <div class="value-display" id="maLongValue">30</div>
                </div>

                <div style="text-align: center; margin-top: 20px;">
                    <button onclick="connectWebSocket()">連接 WebSocket</button>
                    <button onclick="disconnectWebSocket()">斷開連接</button>
                    <button onclick="sendPing()">發送心跳</button>
                    <button onclick="requestStatus()">查詢狀態</button>
                </div>
            </div>

            <div class="results" id="results">
                等待連接...
            </div>
        </div>

        <script>
            let ws = null;
            let sessionId = 'demo_session_' + Date.now();
            let messageCount = 0;
            let errorCount = 0;

            // 更新滑塊值顯示
            document.getElementById('rsiPeriod').addEventListener('input', function(e) {
                document.getElementById('rsiPeriodValue').textContent = e.target.value;
                sendParameterUpdate('rsi_period', parseInt(e.target.value));
            });

            document.getElementById('sentimentThreshold').addEventListener('input', function(e) {
                document.getElementById('sentimentThresholdValue').textContent = parseFloat(e.target.value).toFixed(2);
                sendParameterUpdate('sentiment_threshold', parseFloat(e.target.value));
            });

            document.getElementById('maShort').addEventListener('input', function(e) {
                document.getElementById('maShortValue').textContent = e.target.value;
                sendParameterUpdate('ma_short', parseInt(e.target.value));
            });

            document.getElementById('maLong').addEventListener('input', function(e) {
                document.getElementById('maLongValue').textContent = e.target.value;
                sendParameterUpdate('ma_long', parseInt(e.target.value));
            });

            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/parameters/${sessionId}`;

                try {
                    ws = new WebSocket(wsUrl);

                    ws.onopen = function(event) {
                        updateConnectionStatus('connected', '已連接到服務器');
                        addMessage('WebSocket連接建立成功');
                        updateStats();
                    };

                    ws.onmessage = function(event) {
                        try {
                            const data = JSON.parse(event.data);
                            messageCount++;
                            addMessage('收到消息: ' + JSON.stringify(data, null, 2));
                            updateStats();
                        } catch (e) {
                            addMessage('收到非JSON消息: ' + event.data);
                        }
                    };

                    ws.onclose = function(event) {
                        updateConnectionStatus('disconnected', '連接已斷開');
                        addMessage('WebSocket連接關閉: ' + event.code + ' - ' + event.reason);
                        updateStats();
                    };

                    ws.onerror = function(error) {
                        errorCount++;
                        updateConnectionStatus('error', '連接錯誤');
                        addMessage('WebSocket錯誤: ' + error);
                        updateStats();
                    };

                } catch (error) {
                    errorCount++;
                    addMessage('連接失敗: ' + error.message);
                    updateStats();
                }
            }

            function disconnectWebSocket() {
                if (ws) {
                    ws.close();
                    ws = null;
                }
            }

            function sendParameterUpdate(paramName, value) {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    const message = {
                        type: 'parameter_update',
                        data: {
                            parameter_name: paramName,
                            value: value,
                            timestamp: new Date().toISOString()
                        }
                    };
                    ws.send(JSON.stringify(message));
                    addMessage('發送參數更新: ' + paramName + ' = ' + value);
                } else {
                    addMessage('WebSocket未連接，無法發送參數更新');
                }
            }

            function sendPing() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    const message = {
                        type: 'ping',
                        timestamp: new Date().toISOString()
                    };
                    ws.send(JSON.stringify(message));
                    addMessage('發送心跳消息');
                } else {
                    addMessage('WebSocket未連接，無法發送心跳');
                }
            }

            function requestStatus() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    const message = {
                        type: 'status_query',
                        timestamp: new Date().toISOString()
                    };
                    ws.send(JSON.stringify(message));
                    addMessage('請求狀態信息');
                } else {
                    addMessage('WebSocket未連接，無法請求狀態');
                }
            }

            function updateConnectionStatus(status, message) {
                const statusElement = document.getElementById('connectionStatus');
                statusElement.className = 'connection-status ' + status;
                statusElement.textContent = '連接狀態: ' + message;
            }

            function addMessage(message) {
                const results = document.getElementById('results');
                const timestamp = new Date().toLocaleTimeString();
                results.textContent = '[' + timestamp + '] ' + message + '\\n' + results.textContent;

                // 保持最新的20條消息
                const lines = results.textContent.split('\\n');
                if (lines.length > 20) {
                    results.textContent = lines.slice(0, 20).join('\\n');
                }
            }

            function updateStats() {
                document.getElementById('activeConnections').textContent = ws && ws.readyState === WebSocket.OPEN ? '1' : '0';
                document.getElementById('totalMessages').textContent = messageCount;
                document.getElementById('errorCount').textContent = errorCount;
                document.getElementById('avgProcessingTime').textContent = '0ms'; // 這個需要從服務器獲取
            }

            // 頁面加載完成後自動連接
            window.addEventListener('load', function() {
                addMessage('頁面加載完成，準備連接WebSocket');
                setTimeout(connectWebSocket, 1000);
            });
        </script>
    </body>
    </html>
    """


@app.websocket("/ws/parameters/{session_id}")
async def websocket_parameter_endpoint(
    websocket: WebSocket,
    session_id: str
):
    """
    生產級WebSocket參數控制端點

    基於專家審查建議實現的企業級WebSocket端點
    """
    connection_id = None

    try:
        # 建立連接
        connection_id = await websocket_manager.connect(
            websocket=websocket,
            session_id=session_id,
            user_id=None
        )

        logger.info(f"WebSocket連接建立: {connection_id} (session: {session_id})")

        # 主消息循環
        while True:
            try:
                # 接收消息
                data = await websocket.receive_json()
                logger.debug(f"收到WebSocket消息: {session_id} - {data}")

                # 處理消息
                success = await websocket_manager.handle_message(connection_id, data)

                if not success:
                    logger.warning(f"消息處理失敗: {connection_id}")

            except WebSocketDisconnect:
                logger.info(f"WebSocket客戶端斷開: {connection_id}")
                break

            except Exception as e:
                logger.error(f"WebSocket消息處理錯誤: {connection_id} - {str(e)}")
                # 繼續循環，不要因單個消息錯誤而斷開連接

    except WebSocketDisconnect:
        logger.info(f"WebSocket連接正常斷開: {session_id}")

    except Exception as e:
        logger.error(f"WebSocket連接錯誤: {session_id} - {str(e)}")

    finally:
        # 清理連接
        if connection_id:
            await websocket_manager.disconnect(connection_id)


@app.get("/api/stats")
async def get_system_stats():
    """
    獲取系統統計信息

    Returns:
        系統統計數據
    """
    try:
        websocket_stats = websocket_manager.get_server_stats()
        session_stats = session_manager.get_session_stats()
        rate_limit_stats = rate_limiter.get_stats()

        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "websocket": websocket_stats,
            "sessions": session_stats,
            "rate_limiter": rate_limit_stats,
            "system": {
                "uptime": "運行中",
                "version": "1.0.0"
            }
        }

    except Exception as e:
        logger.error(f"獲取系統統計失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取系統統計失敗: {str(e)}"
        )


@app.get("/api/sessions/{session_id}/parameters")
async def get_session_parameters(session_id: str):
    """
    獲取會話參數

    Args:
        session_id: 會話ID

    Returns:
        會話參數
    """
    try:
        parameters = await session_manager.get_session_parameters(session_id)
        return {
            "status": "success",
            "session_id": session_id,
            "parameters": parameters,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"獲取會話參數失敗: {session_id} - {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取會話參數失敗: {str(e)}"
        )


@app.post("/api/sessions/{session_id}/parameters")
async def update_session_parameter(
    session_id: str,
    parameter_update: SecureParameterUpdate
):
    """
    更新會話參數 (HTTP API)

    Args:
        session_id: 會話ID
        parameter_update: 參數更新數據

    Returns:
        更新結果
    """
    try:
        # 確保session_id匹配
        parameter_update.session_id = session_id
        parameter_update.request_source = "http"

        # 處理參數更新
        response = await process_parameter_update(session_id, parameter_update.dict())

        # 如果是WebSocket客戶端，廣播更新
        if response.success:
            broadcast_message = {
                "type": "parameter_broadcast",
                "session_id": session_id,
                "parameter_update": response.data.get("parameter_update"),
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket_manager.broadcast_to_session(session_id, broadcast_message)

        return response

    except Exception as e:
        logger.error(f"HTTP參數更新失敗: {session_id} - {str(e)}")
        return ParameterResponse(
            success=False,
            error=f"參數更新失敗: {str(e)}",
            error_code="HTTP_UPDATE_ERROR",
            session_id=session_id
        )


@app.get("/api/health")
async def health_check():
    """
    健康檢查端點

    Returns:
        服務健康狀態
    """
    try:
        # 檢查核心組件
        websocket_stats = websocket_manager.get_server_stats()
        session_stats = session_manager.get_session_stats()

        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "websocket_manager": websocket_stats["tasks"]["message_processor_running"],
                "session_manager": session_stats["active_sessions"] >= 0,
                "rate_limiter": True
            },
            "version": "1.0.0"
        }

        # 檢查所有組件是否正常
        if not all(health_status["components"].values()):
            health_status["status"] = "degraded"

        return health_status

    except Exception as e:
        logger.error(f"健康檢查失敗: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "version": "1.0.0"
        }


async def create_demo_session():
    """
    創建演示會話
    """
    demo_session_id = "demo_session_production"
    await session_manager.create_session(demo_session_id, "demo_user")
    logger.info(f"演示會話創建成功: {demo_session_id}")


@app.on_event("startup")
async def startup_event():
    """
    應用啟動事件
    """
    logger.info("🚀 CBSC 生產級參數控制系統啟動")
    logger.info("✅ 安全框架已加載")
    logger.info("✅ 速率限制已啟用")
    logger.info("✅ WebSocket管理器已初始化")
    logger.info("✅ 會話管理器已初始化")

    # 創建演示會話
    await create_demo_session()

    # 輸出系統信息
    stats = websocket_manager.get_server_stats()
    logger.info(f"📊 系統統計: {stats}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    應用關閉事件
    """
    logger.info("🔄 開始關閉CBSC 生產級參數控制系統")

    try:
        # 關閉WebSocket管理器
        await websocket_manager.shutdown()
        logger.info("✅ WebSocket管理器已關閉")

    except Exception as e:
        logger.error(f"❌ 關閉過程中發生錯誤: {str(e)}")

    logger.info("🛑 系統已完全關閉")


def main():
    """
    主函數 - 啟動生產級參數控制系統
    """
    print("🚀 啟動 CBSC 生產級參數控制系統")
    print("=" * 50)
    print("📋 功能特性:")
    print("  ✅ 企業級安全驗證")
    print("  ✅ 速率限制和DDoS防護")
    print("  ✅ 實時參數控制")
    print("  ✅ 性能監控和統計")
    print("  ✅ 完整的錯誤處理")
    print("  ✅ WebSocket連接管理")
    print("=" * 50)
    print("🌐 服務地址: http://localhost:8000")
    print("📚 API文檔: http://localhost:8000/docs")
    print("📊 統計信息: http://localhost:8000/api/stats")
    print("🏥 健康檢查: http://localhost:8000/api/health")
    print("=" * 50)
    print("按 Ctrl+C 停止服務")
    print()

    try:
        uvicorn.run(
            "production_parameter_system_demo:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 服務已停止")
    except Exception as e:
        print(f"❌ 服務啟動失敗: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
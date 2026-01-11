"""
WebSocket连接池路由集成
WebSocket Pool Route Integration

将WebSocket连接池集成到主API系统中
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Header
from fastapi.responses import HTMLResponse
import logging
import json
from datetime import datetime

from .strategies.websocket_pool_integration import websocket_endpoint_handler
from .strategies.websocket_pool_api import router as websocket_pool_api_router
from ..services.websocket_pool import get_connection_pool, cleanup_connection_pool

logger = logging.getLogger(__name__)

# 创建WebSocket路由器
websocket_router = APIRouter(tags=["websocket"])

# 包含WebSocket Pool API路由
websocket_router.include_router(
    websocket_pool_api_router,
    prefix="/ws-pool"
)


@websocket_router.websocket("/connect")
async def websocket_connect_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="Authentication token"),
    channel: str = Query("default", description="Channel name"),
    strategy_ids: str = Query(None, description="Comma-separated strategy IDs"),
    authorization: str = Header(None, description="Authorization header")
):
    """
    WebSocket连接端点

    这是主要的WebSocket连接入口，支持：
    - JWT token认证
    - 频道选择
    - 策略订阅
    - 实时消息推送
    """
    await websocket_endpoint_handler(
        websocket=websocket,
        token=token,
        channel=channel,
        strategy_ids=strategy_ids,
        authorization=authorization
    )


@websocket_router.get("/test-page", response_class=HTMLResponse)
async def websocket_test_page():
    """
    WebSocket测试页面

    提供一个简单的HTML页面用于测试WebSocket连接
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WebSocket连接池测试</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            .controls {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
                margin-bottom: 20px;
            }
            .status {
                padding: 10px;
                border-radius: 4px;
                margin-bottom: 10px;
            }
            .status.connected {
                background-color: #d4edda;
                color: #155724;
            }
            .status.disconnected {
                background-color: #f8d7da;
                color: #721c24;
            }
            .messages {
                height: 400px;
                overflow-y: auto;
                border: 1px solid #ddd;
                padding: 10px;
                background-color: #fafafa;
            }
            .message {
                margin-bottom: 5px;
                padding: 5px;
                border-radius: 3px;
                font-size: 14px;
            }
            .message.connection {
                background-color: #cce5ff;
            }
            .message.broadcast {
                background-color: #fff3cd;
            }
            .message.heartbeat {
                background-color: #e2e3e5;
            }
            .message.error {
                background-color: #f8d7da;
                color: #721c24;
            }
            input, select, button {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            button {
                background-color: #007bff;
                color: white;
                cursor: pointer;
                border: none;
            }
            button:hover {
                background-color: #0056b3;
            }
            button:disabled {
                background-color: #6c757d;
                cursor: not-allowed;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 10px;
            }
            .stat-card {
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 4px;
                text-align: center;
            }
            .stat-value {
                font-size: 24px;
                font-weight: bold;
                color: #007bff;
            }
            .stat-label {
                font-size: 12px;
                color: #6c757d;
            }
        </style>
    </head>
    <body>
        <h1>WebSocket连接池测试</h1>

        <div class="container">
            <h2>连接控制</h2>
            <div id="status" class="status disconnected">
                状态: 未连接
            </div>

            <div class="controls">
                <input type="text" id="token" placeholder="JWT Token" value="test-token-123">
                <select id="channel">
                    <option value="default">默认频道</option>
                    <option value="strategies">策略频道</option>
                    <option value="market_data">市场数据</option>
                    <option value="notifications">通知</option>
                </select>
                <input type="text" id="strategyIds" placeholder="策略ID (逗号分隔)">
                <button id="connectBtn" onclick="connect()">连接</button>
                <button id="disconnectBtn" onclick="disconnect()" disabled>断开</button>
            </div>

            <div class="controls">
                <input type="text" id="subscribeChannel" placeholder="订阅频道">
                <button onclick="subscribe()">订阅</button>
                <input type="text" id="unsubscribeChannel" placeholder="取消订阅频道">
                <button onclick="unsubscribe()">取消订阅</button>
                <button onclick="sendPing()">发送心跳</button>
            </div>
        </div>

        <div class="container">
            <h2>统计信息</h2>
            <div class="stats">
                <div class="stat-card">
                    <div id="messageCount" class="stat-value">0</div>
                    <div class="stat-label">消息数量</div>
                </div>
                <div class="stat-card">
                    <div id="errorCount" class="stat-value">0</div>
                    <div class="stat-label">错误数量</div>
                </div>
                <div class="stat-card">
                    <div id="latency" class="stat-value">0</div>
                    <div class="stat-label">延迟 (ms)</div>
                </div>
                <div class="stat-card">
                    <div id="uptime" class="stat-value">0</div>
                    <div class="stat-label">运行时间 (s)</div>
                </div>
            </div>
        </div>

        <div class="container">
            <h2>消息日志</h2>
            <button onclick="clearMessages()">清空日志</button>
            <div id="messages" class="messages"></div>
        </div>

        <script>
            let ws = null;
            let messageCount = 0;
            let errorCount = 0;
            let connectTime = null;
            let lastPingTime = null;

            function updateStatus(connected) {
                const status = document.getElementById('status');
                const connectBtn = document.getElementById('connectBtn');
                const disconnectBtn = document.getElementById('disconnectBtn');

                if (connected) {
                    status.className = 'status connected';
                    status.textContent = '状态: 已连接';
                    connectBtn.disabled = true;
                    disconnectBtn.disabled = false;
                    connectTime = Date.now();
                } else {
                    status.className = 'status disconnected';
                    status.textContent = '状态: 未连接';
                    connectBtn.disabled = false;
                    disconnectBtn.disabled = true;
                    connectTime = null;
                }
                updateStats();
            }

            function addMessage(message, type = 'info') {
                const messages = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;

                const time = new Date().toLocaleTimeString();
                const content = typeof message === 'object'
                    ? JSON.stringify(message, null, 2)
                    : message;

                messageDiv.innerHTML = `<strong>[${time}]</strong> ${content}`;
                messages.appendChild(messageDiv);
                messages.scrollTop = messages.scrollHeight;

                if (type === 'error') {
                    errorCount++;
                } else {
                    messageCount++;
                }
                updateStats();
            }

            function updateStats() {
                document.getElementById('messageCount').textContent = messageCount;
                document.getElementById('errorCount').textContent = errorCount;

                if (connectTime) {
                    const uptime = Math.floor((Date.now() - connectTime) / 1000);
                    document.getElementById('uptime').textContent = uptime;
                } else {
                    document.getElementById('uptime').textContent = 0;
                }

                if (lastPingTime) {
                    document.getElementById('latency').textContent = lastPingTime;
                }
            }

            function connect() {
                const token = document.getElementById('token').value;
                const channel = document.getElementById('channel').value;
                const strategyIds = document.getElementById('strategyIds').value;

                if (!token) {
                    alert('请输入JWT Token');
                    return;
                }

                let wsUrl = `ws://localhost:8000/ws/connect?token=${encodeURIComponent(token)}&channel=${channel}`;
                if (strategyIds) {
                    wsUrl += `&strategy_ids=${encodeURIComponent(strategyIds)}`;
                }

                try {
                    ws = new WebSocket(wsUrl);

                    ws.onopen = function(event) {
                        updateStatus(true);
                        addMessage('WebSocket连接已建立', 'connection');
                    };

                    ws.onmessage = function(event) {
                        try {
                            const message = JSON.parse(event.data);

                            // 处理不同类型的消息
                            switch(message.type) {
                                case 'connection_established':
                                    addMessage(`连接已建立，ID: ${message.data.connection_id}`, 'connection');
                                    break;
                                case 'pong':
                                    if (message.data.timestamp) {
                                        const pingTime = Date.now() - new Date(message.data.timestamp).getTime();
                                        lastPingTime = pingTime;
                                        addMessage(`收到心跳响应，延迟: ${pingTime}ms`, 'heartbeat');
                                    } else {
                                        addMessage('收到心跳响应', 'heartbeat');
                                    }
                                    break;
                                case 'subscription_confirmed':
                                    addMessage(`已订阅: ${message.data.target}`, 'info');
                                    break;
                                case 'unsubscription_confirmed':
                                    addMessage(`已取消订阅: ${message.data.target}`, 'info');
                                    break;
                                case 'broadcast':
                                    addMessage(`广播消息: ${JSON.stringify(message.data)}`, 'broadcast');
                                    break;
                                case 'error':
                                    addMessage(`错误: ${message.data.error}`, 'error');
                                    break;
                                default:
                                    addMessage(message, 'info');
                            }
                        } catch (e) {
                            addMessage(`解析消息失败: ${event.data}`, 'error');
                        }
                    };

                    ws.onclose = function(event) {
                        updateStatus(false);
                        addMessage(`WebSocket连接已关闭: ${event.code} ${event.reason}`, 'connection');
                    };

                    ws.onerror = function(error) {
                        addMessage(`WebSocket错误: ${error}`, 'error');
                    };

                } catch (error) {
                    addMessage(`连接失败: ${error.message}`, 'error');
                }
            }

            function disconnect() {
                if (ws) {
                    ws.close();
                    ws = null;
                }
            }

            function subscribe() {
                const channel = document.getElementById('subscribeChannel').value;
                if (!channel) {
                    alert('请输入要订阅的频道');
                    return;
                }

                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'subscribe',
                        target: channel
                    }));
                    addMessage(`发送订阅请求: ${channel}`, 'info');
                } else {
                    addMessage('WebSocket未连接', 'error');
                }
            }

            function unsubscribe() {
                const channel = document.getElementById('unsubscribeChannel').value;
                if (!channel) {
                    alert('请输入要取消订阅的频道');
                    return;
                }

                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'unsubscribe',
                        target: channel
                    }));
                    addMessage(`发送取消订阅请求: ${channel}`, 'info');
                } else {
                    addMessage('WebSocket未连接', 'error');
                }
            }

            function sendPing() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    const pingTime = Date.now();
                    ws.send(JSON.stringify({
                        type: 'ping',
                        data: {
                            timestamp: new Date(pingTime).toISOString()
                        }
                    }));
                    addMessage('发送心跳', 'heartbeat');
                } else {
                    addMessage('WebSocket未连接', 'error');
                }
            }

            function clearMessages() {
                document.getElementById('messages').innerHTML = '';
                messageCount = 0;
                errorCount = 0;
                updateStats();
            }

            // 定期更新统计信息
            setInterval(updateStats, 1000);

            // 页面加载完成后的初始化
            window.onload = function() {
                updateStatus(false);
                addMessage('WebSocket测试页面已加载', 'info');
            };

            // 页面卸载时清理连接
            window.onbeforeunload = function() {
                if (ws) {
                    ws.close();
                }
            };
        </script>
    </body>
    </html>
    """
    return html_content


@websocket_router.on_event("startup")
async def startup_event():
    """
    应用启动时的初始化
    """
    logger.info("WebSocket连接池服务启动")

    # 初始化连接池
    pool = get_connection_pool()
    logger.info(f"WebSocket连接池已初始化，配置: {pool.config.dict()}")


@websocket_router.on_event("shutdown")
async def shutdown_event():
    """
    应用关闭时的清理
    """
    logger.info("WebSocket连接池服务关闭")

    # 清理连接池
    await cleanup_connection_pool()
    logger.info("WebSocket连接池已清理")


# 导出路由器
__all__ = ['websocket_router']
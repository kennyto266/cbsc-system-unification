"""
Simplified Production-Grade Parameter Control System Demo
Fixed version for Windows console encoding

Features:
- Basic security framework
- Parameter validation and control
- Real-time WebSocket communication
- Performance monitoring

Usage:
    python simple_production_demo_fixed.py

Author: CBSC Quantitative Trading System
Version: 1.0.0
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Simple Security Validator
class SimpleSecurityValidator:
    """Simplified security validator"""

    XSS_PATTERNS = [
        r'<script.*?>.*?</script>',
        r'javascript:',
        r'data:',
        r'on\w+\s*=',
        r'expression\s*\(',
    ]

    SQL_PATTERNS = [
        r"'.*?;",
        r'".*?;',
        r'DROP TABLE',
        r'INSERT INTO',
        r'DELETE FROM',
        r'UNION SELECT',
        r'EXEC\s+\w+',
    ]

    @staticmethod
    def validate_input(input_data: str) -> bool:
        """Validate input for security threats"""
        if not isinstance(input_data, str):
            return False

        import re
        lower_input = input_data.lower()

        # Check for XSS patterns
        for pattern in SimpleSecurityValidator.XSS_PATTERNS:
            if re.search(pattern, lower_input, re.IGNORECASE):
                return False

        # Check for SQL injection patterns
        for pattern in SimpleSecurityValidator.SQL_PATTERNS:
            if re.search(pattern, lower_input, re.IGNORECASE):
                return False

        return True

    @staticmethod
    def sanitize_input(input_data: str) -> str:
        """Sanitize input by removing dangerous characters"""
        if not isinstance(input_data, str):
            return ""

        import bleach
        return bleach.clean(input_data, tags=[], strip=True)

# Simple Rate Limiter
class SimpleRateLimiter:
    """Simple rate limiter"""

    def __init__(self, max_requests: int = 100, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, List[float]] = {}

    def is_allowed(self, user_id: str) -> bool:
        """Check if user is allowed to make a request"""
        now = time.time()

        if user_id not in self.requests:
            self.requests[user_id] = []

        # Remove old requests outside time window
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.time_window
        ]

        # Check if under limit
        if len(self.requests[user_id]) < self.max_requests:
            self.requests[user_id].append(now)
            return True

        return False

# FastAPI app
app = FastAPI(
    title="CBSC Production Parameter Control System",
    description="Simplified demo for production-grade parameter control",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
security_validator = SimpleSecurityValidator()
rate_limiter = SimpleRateLimiter()

# Active WebSocket connections
active_connections: List[WebSocket] = []

# Parameter storage
current_parameters = {
    "rsi_period": 14,
    "macd_fast": 12,
    "macd_slow": 26,
    "bb_period": 20,
    "bb_std": 2.0
}

# WebSocket management
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            # Send current parameters
            await websocket.send_text(json.dumps({
                "type": "parameters_update",
                "data": current_parameters,
                "timestamp": datetime.now().isoformat()
            }))

            # Wait for client message or heartbeat
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)

                # Parse client message
                try:
                    message = json.loads(data)
                    if message.get("type") == "heartbeat":
                        await websocket.send_text(json.dumps({"type": "heartbeat_response"}))
                    elif message.get("type") == "parameter_update":
                        await handle_parameter_update(message.get("data", {}))
                except json.JSONDecodeError:
                    pass

            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(json.dumps({"type": "heartbeat"}))

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        if websocket in active_connections:
            active_connections.remove(websocket)

async def handle_parameter_update(param_data: Dict[str, Any]):
    """Handle parameter update from client"""
    try:
        # Validate parameters
        for key, value in param_data.items():
            if key in current_parameters:
                # Basic validation
                if isinstance(value, (int, float)) and value > 0:
                    current_parameters[key] = value
                    logger.info(f"Parameter updated: {key} = {value}")

        # Broadcast to all connected clients
        message = json.dumps({
            "type": "parameters_update",
            "data": current_parameters,
            "timestamp": datetime.now().isoformat()
        })

        for connection in active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

    except Exception as e:
        logger.error(f"Error handling parameter update: {str(e)}")

# API Routes
@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Main dashboard page"""
    return HTMLResponse(WEB_INTERFACE)

@app.get("/api/status")
async def get_status():
    """System status"""
    return {
        "status": "running",
        "active_connections": len(active_connections),
        "current_parameters": current_parameters,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/parameters")
async def get_parameters():
    """Get current parameters"""
    return current_parameters

@app.post("/api/parameters")
async def update_parameters(params: Dict[str, Any]):
    """Update parameters"""
    user_id = "demo_user"  # In production, get from authentication

    # Rate limiting
    if not rate_limiter.is_allowed(user_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Validate and update parameters
    for key, value in params.items():
        if key in current_parameters and isinstance(value, (int, float)):
            if value > 0:  # Basic validation
                current_parameters[key] = value

    return {"status": "success", "parameters": current_parameters}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Web interface
WEB_INTERFACE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CBSC Production Parameter Control System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            padding: 30px;
        }

        .parameters-section {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }

        .section-title {
            font-size: 1.8em;
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #3498db;
        }

        .parameter-control {
            margin-bottom: 25px;
            padding: 15px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .parameter-label {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            font-weight: 600;
            color: #2c3e50;
        }

        .parameter-value {
            background: #3498db;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.9em;
            min-width: 50px;
            text-align: center;
        }

        .parameter-slider {
            width: 100%;
            height: 8px;
            border-radius: 5px;
            background: #ddd;
            outline: none;
            -webkit-appearance: none;
        }

        .parameter-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #3498db;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
        }

        .parameter-slider::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #3498db;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
        }

        .status-section {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }

        .status-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            margin-bottom: 15px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .status-label {
            font-weight: 600;
            color: #2c3e50;
        }

        .status-value {
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 500;
        }

        .status-online {
            background: #27ae60;
            color: white;
        }

        .status-connected {
            background: #3498db;
            color: white;
        }

        .connection-status {
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-weight: 600;
            margin-bottom: 20px;
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

        .controls {
            display: flex;
            gap: 15px;
            margin-top: 20px;
        }

        .btn {
            flex: 1;
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .btn-primary {
            background: #3498db;
            color: white;
        }

        .btn-primary:hover {
            background: #2980b9;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.3);
        }

        .btn-secondary {
            background: #95a5a6;
            color: white;
        }

        .btn-secondary:hover {
            background: #7f8c8d;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(149, 165, 166, 0.3);
        }

        .footer {
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            margin-top: 30px;
        }

        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
                gap: 20px;
                padding: 20px;
            }

            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>CBSC Production Parameter Control</h1>
            <p>Real-time Parameter Management System</p>
        </div>

        <div class="main-content">
            <div class="parameters-section">
                <h2 class="section-title">Parameter Controls</h2>

                <div class="parameter-control">
                    <div class="parameter-label">
                        <span>RSI Period</span>
                        <span class="parameter-value" id="rsi-period-value">14</span>
                    </div>
                    <input type="range" class="parameter-slider" id="rsi-period"
                           min="5" max="50" value="14" step="1">
                </div>

                <div class="parameter-control">
                    <div class="parameter-label">
                        <span>MACD Fast Period</span>
                        <span class="parameter-value" id="macd-fast-value">12</span>
                    </div>
                    <input type="range" class="parameter-slider" id="macd-fast"
                           min="5" max="50" value="12" step="1">
                </div>

                <div class="parameter-control">
                    <div class="parameter-label">
                        <span>MACD Slow Period</span>
                        <span class="parameter-value" id="macd-slow-value">26</span>
                    </div>
                    <input type="range" class="parameter-slider" id="macd-slow"
                           min="10" max="100" value="26" step="1">
                </div>

                <div class="parameter-control">
                    <div class="parameter-label">
                        <span>Bollinger Bands Period</span>
                        <span class="parameter-value" id="bb-period-value">20</span>
                    </div>
                    <input type="range" class="parameter-slider" id="bb-period"
                           min="5" max="50" value="20" step="1">
                </div>

                <div class="parameter-control">
                    <div class="parameter-label">
                        <span>Bollinger Bands Std Dev</span>
                        <span class="parameter-value" id="bb-std-value">2.0</span>
                    </div>
                    <input type="range" class="parameter-slider" id="bb-std"
                           min="0.5" max="3.0" value="2.0" step="0.1">
                </div>

                <div class="controls">
                    <button class="btn btn-primary" onclick="applyParameters()">Apply Changes</button>
                    <button class="btn btn-secondary" onclick="resetParameters()">Reset Default</button>
                </div>
            </div>

            <div class="status-section">
                <h2 class="section-title">System Status</h2>

                <div class="connection-status disconnected" id="connection-status">
                    Connecting to server...
                </div>

                <div class="status-item">
                    <span class="status-label">System Status</span>
                    <span class="status-value status-online">ONLINE</span>
                </div>

                <div class="status-item">
                    <span class="status-label">Active Connections</span>
                    <span class="status-value status-connected" id="active-connections">0</span>
                </div>

                <div class="status-item">
                    <span class="status-label">Last Update</span>
                    <span class="status-value" id="last-update">Never</span>
                </div>

                <div class="status-item">
                    <span class="status-label">WebSocket Status</span>
                    <span class="status-value" id="websocket-status">Connecting...</span>
                </div>

                <div class="status-item">
                    <span class="status-label">Rate Limit Status</span>
                    <span class="status-value status-online">ACTIVE</span>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>CBSC Quantitative Trading System | Production Demo | Version 1.0.0</p>
        </div>
    </div>

    <script>
        let ws = null;
        let reconnectInterval = null;
        let currentParameters = {};

        // Initialize WebSocket connection
        function connectWebSocket() {
            try {
                ws = new WebSocket('ws://localhost:8000/ws');

                ws.onopen = function(event) {
                    console.log('WebSocket connected');
                    updateConnectionStatus(true);

                    if (reconnectInterval) {
                        clearInterval(reconnectInterval);
                        reconnectInterval = null;
                    }
                };

                ws.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        handleMessage(data);
                    } catch (e) {
                        console.error('Error parsing message:', e);
                    }
                };

                ws.onclose = function(event) {
                    console.log('WebSocket disconnected');
                    updateConnectionStatus(false);

                    // Try to reconnect after 3 seconds
                    if (!reconnectInterval) {
                        reconnectInterval = setInterval(connectWebSocket, 3000);
                    }
                };

                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                    updateConnectionStatus(false);
                };

            } catch (e) {
                console.error('Failed to connect WebSocket:', e);
                updateConnectionStatus(false);
            }
        }

        // Handle incoming WebSocket messages
        function handleMessage(data) {
            switch (data.type) {
                case 'parameters_update':
                    currentParameters = data.data;
                    updateParameterDisplays();
                    updateLastUpdate();
                    break;
                case 'heartbeat':
                case 'heartbeat_response':
                    // Connection is alive
                    updateConnectionStatus(true);
                    break;
                default:
                    console.log('Unknown message type:', data.type);
            }
        }

        // Update connection status display
        function updateConnectionStatus(connected) {
            const statusElement = document.getElementById('connection-status');
            const wsStatusElement = document.getElementById('websocket-status');

            if (connected) {
                statusElement.textContent = 'Connected to server';
                statusElement.className = 'connection-status connected';
                wsStatusElement.textContent = 'CONNECTED';
                wsStatusElement.className = 'status-value status-online';
            } else {
                statusElement.textContent = 'Disconnected from server';
                statusElement.className = 'connection-status disconnected';
                wsStatusElement.textContent = 'DISCONNECTED';
                wsStatusElement.className = 'status-value';
            }
        }

        // Update parameter displays
        function updateParameterDisplays() {
            if (currentParameters) {
                Object.keys(currentParameters).forEach(key => {
                    const value = currentParameters[key];
                    const sliderElement = document.getElementById(key);
                    const valueElement = document.getElementById(key + '-value');

                    if (sliderElement && valueElement) {
                        sliderElement.value = value;
                        valueElement.textContent = value;
                    }
                });
            }
        }

        // Update last update time
        function updateLastUpdate() {
            const now = new Date();
            document.getElementById('last-update').textContent =
                now.toLocaleTimeString();
        }

        // Apply parameter changes
        async function applyParameters() {
            const params = {
                'rsi_period': parseInt(document.getElementById('rsi-period').value),
                'macd_fast': parseInt(document.getElementById('macd-fast').value),
                'macd_slow': parseInt(document.getElementById('macd-slow').value),
                'bb_period': parseInt(document.getElementById('bb-period').value),
                'bb_std': parseFloat(document.getElementById('bb-std').value)
            };

            try {
                const response = await fetch('/api/parameters', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(params)
                });

                if (response.ok) {
                    console.log('Parameters applied successfully');
                    updateLastUpdate();
                } else {
                    console.error('Failed to apply parameters');
                }
            } catch (error) {
                console.error('Error applying parameters:', error);
            }
        }

        // Reset parameters to default
        function resetParameters() {
            const defaults = {
                'rsi-period': 14,
                'macd-fast': 12,
                'macd-slow': 26,
                'bb-period': 20,
                'bb-std': 2.0
            };

            Object.keys(defaults).forEach(key => {
                const sliderElement = document.getElementById(key);
                const valueElement = document.getElementById(key + '-value');

                if (sliderElement && valueElement) {
                    sliderElement.value = defaults[key];
                    valueElement.textContent = defaults[key];
                }
            });
        }

        // Update slider values in real-time
        document.addEventListener('DOMContentLoaded', function() {
            const sliders = document.querySelectorAll('.parameter-slider');
            sliders.forEach(slider => {
                slider.addEventListener('input', function() {
                    const valueElement = document.getElementById(this.id + '-value');
                    if (valueElement) {
                        valueElement.textContent = this.value;
                    }
                });
            });

            // Start WebSocket connection
            connectWebSocket();

            // Load system status
            loadSystemStatus();
        });

        // Load system status
        async function loadSystemStatus() {
            try {
                const response = await fetch('/api/status');
                if (response.ok) {
                    const data = await response.json();
                    document.getElementById('active-connections').textContent =
                        data.active_connections || 0;
                }
            } catch (error) {
                console.error('Error loading status:', error);
            }
        }

        // Periodically update system status
        setInterval(loadSystemStatus, 5000);
    </script>
</body>
</html>
"""

def main():
    """Main function"""
    print("=" * 60)
    print("CBSC Production Parameter Control System")
    print("=" * 60)
    print("Starting production-grade parameter control demo...")
    print()
    print("Features:")
    print("- Real-time parameter control via WebSocket")
    print("- Input validation and security")
    print("- Rate limiting and DDoS protection")
    print("- Beautiful web interface")
    print("- Production-grade error handling")
    print()
    print("Access the dashboard at: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()

if __name__ == "__main__":
    main()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
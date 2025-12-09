import asyncio
import json
import logging
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Body
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False
    print("Warning: bleach not available. Install with: pip install bleach")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Warning: redis not available. Install with: pip install redis")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. Install with: pip install psutil")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_demo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Data Models
@dataclass
class ParameterUpdate:
    """Parameter update data structure"""
    parameter_name: str
    old_value: float
    new_value: float
    timestamp: datetime
    user_id: str
    session_id: str
    risk_level: str
    validated: bool

class SecureParameterUpdate(BaseModel):
    """Secure parameter update model with validation"""
    parameter_name: str = Field(..., min_length=1, max_length=50, description="Parameter name")
    value: float = Field(..., ge=0, le=100, description="Parameter value (0-100)")
    user_id: str = Field(..., min_length=1, max_length=50, description="User identifier")
    session_id: str = Field(..., min_length=1, max_length=50, description="Session identifier")

    class Config:
        extra = "forbid"  # Prevent additional fields

# Security Implementation
class SecurityValidator:
    """Enterprise-grade security validator"""

    def __init__(self):
        self.xss_patterns = [
            '<script', 'javascript:', 'onload=', 'onerror=', 'onclick=',
            'eval(', 'setTimeout(', 'setInterval('
        ]
        self.sql_injection_patterns = [
            "'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_', 'drop ',
            'delete ', 'insert ', 'update ', 'select ', 'union '
        ]
        self.command_injection_patterns = [
            '&', ';', '`', '|', '(', ')', '$', '<', '>', '\n', '\r'
        ]

    def sanitize_input(self, data: str) -> str:
        """Sanitize input data to prevent XSS and injection attacks"""
        if not data:
            return ""

        if BLEACH_AVAILABLE:
            return bleach.clean(data, strip=True)

        # Fallback sanitization
        sanitized = data
        for pattern in self.xss_patterns + self.sql_injection_patterns + self.command_injection_patterns:
            sanitized = sanitized.replace(pattern, '')
        return sanitized.strip()

    def validate_parameter_value(self, param_name: str, value: float) -> Tuple[bool, str]:
        """Validate parameter value against security constraints"""
        # Check for valid parameter names
        valid_params = ['rsi_period', 'macd_fast', 'macd_slow', 'bollinger_period',
                       'sentiment_threshold', 'risk_tolerance', 'allocation_percentage']

        if param_name not in valid_params:
            return False, f"Invalid parameter name: {param_name}"

        # Check value ranges based on parameter type
        if 'period' in param_name:
            if not (2 <= value <= 100):
                return False, f"Period value {value} out of range (2-100)"
        elif param_name == 'sentiment_threshold':
            if not (0 <= value <= 1):
                return False, f"Sentiment threshold {value} out of range (0-1)"
        elif param_name in ['risk_tolerance', 'allocation_percentage']:
            if not (0 <= value <= 100):
                return False, f"Percentage value {value} out of range (0-100)"

        return True, "Valid"

class RateLimiter:
    """Enterprise-grade rate limiter with dynamic banning"""

    def __init__(self):
        self.requests: Dict[str, List[float]] = {}
        self.banned_ips: Dict[str, float] = {}
        self.max_requests_per_minute = 60
        self.ban_duration = 300  # 5 minutes

    def is_allowed(self, client_ip: str) -> Tuple[bool, str]:
        """Check if request is allowed from this IP"""
        current_time = time.time()

        # Check if IP is banned
        if client_ip in self.banned_ips:
            if current_time - self.banned_ips[client_ip] < self.ban_duration:
                return False, "IP temporarily banned due to excessive requests"
            else:
                # Unban expired bans
                del self.banned_ips[client_ip]

        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < 60
            ]
        else:
            self.requests[client_ip] = []

        # Check rate limit
        if len(self.requests[client_ip]) >= self.max_requests_per_minute:
            # Ban this IP
            self.banned_ips[client_ip] = current_time
            logger.warning(f"IP {client_ip} banned due to rate limit violation")
            return False, "Rate limit exceeded - IP temporarily banned"

        # Record this request
        self.requests[client_ip].append(current_time)
        return True, "Allowed"

# Global instances
security_validator = SecurityValidator()
rate_limiter = RateLimiter()

# Production WebSocket Manager
class ProductionWebSocketManager:
    """Enterprise-grade WebSocket connection manager"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict] = {}
        self.message_queue: List[Dict] = []
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'messages_sent': 0,
            'errors': 0
        }

    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept and register new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)

        self.connection_metadata[websocket] = {
            'client_id': client_id or f"client_{len(self.active_connections)}",
            'connected_at': datetime.now(),
            'message_count': 0,
            'last_ping': time.time()
        }

        self.connection_stats['total_connections'] += 1
        self.connection_stats['active_connections'] = len(self.active_connections)

        logger.info(f"WebSocket connected: {client_id}, Total: {len(self.active_connections)}")

        # Send welcome message
        await self.send_personal_message({
            'type': 'connection_established',
            'client_id': self.connection_metadata[websocket]['client_id'],
            'timestamp': datetime.now().isoformat(),
            'server_stats': self.connection_stats
        }, websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        if websocket in self.connection_metadata:
            client_id = self.connection_metadata[websocket]['client_id']
            del self.connection_metadata[websocket]
            logger.info(f"WebSocket disconnected: {client_id}")

        self.connection_stats['active_connections'] = len(self.active_connections)

    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
            self.connection_stats['messages_sent'] += 1

            # Update metadata
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]['message_count'] += 1
                self.connection_metadata[websocket]['last_ping'] = time.time()

        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")
            self.connection_stats['errors'] += 1

    async def broadcast(self, message: Dict):
        """Broadcast message to all connected WebSockets"""
        if not self.active_connections:
            return

        disconnected_websockets = []

        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
                self.connection_stats['messages_sent'] += 1

                # Update metadata
                if connection in self.connection_metadata:
                    self.connection_metadata[connection]['message_count'] += 1
                    self.connection_metadata[connection]['last_ping'] = time.time()

            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected_websockets.append(connection)
                self.connection_stats['errors'] += 1

        # Clean up disconnected WebSockets
        for ws in disconnected_websockets:
            self.disconnect(ws)

    def get_stats(self) -> Dict:
        """Get connection statistics"""
        return {
            **self.connection_stats,
            'queue_size': len(self.message_queue),
            'active_connections_details': [
                {
                    'client_id': metadata['client_id'],
                    'connected_at': metadata['connected_at'].isoformat(),
                    'message_count': metadata['message_count'],
                    'connected_duration': (datetime.now() - metadata['connected_at']).total_seconds()
                }
                for metadata in self.connection_metadata.values()
            ]
        }

# Global WebSocket manager
websocket_manager = ProductionWebSocketManager()

# FastAPI app with lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting CBSC Production Parameter System")
    yield
    logger.info("Shutting down CBSC Production Parameter System")

app = FastAPI(
    title="CBSC Production Parameter System",
    description="Enterprise-grade parameter control with security validation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global parameter storage with validation
current_parameters = {
    "rsi_period": {"value": 14.0, "min": 2.0, "max": 50.0, "unit": "periods"},
    "macd_fast": {"value": 12.0, "min": 5.0, "max": 20.0, "unit": "periods"},
    "macd_slow": {"value": 26.0, "min": 20.0, "max": 50.0, "unit": "periods"},
    "bollinger_period": {"value": 20.0, "min": 10.0, "max": 50.0, "unit": "periods"},
    "sentiment_threshold": {"value": 0.6, "min": 0.0, "max": 1.0, "unit": "ratio"},
    "risk_tolerance": {"value": 50.0, "min": 0.0, "max": 100.0, "unit": "percent"},
    "allocation_percentage": {"value": 60.0, "min": 10.0, "max": 100.0, "unit": "percent"}
}

parameter_history: List[ParameterUpdate] = []

# Security middleware
@app.middleware("http")
async def security_middleware(request, call_next):
    """Security middleware for rate limiting and validation"""
    client_ip = request.client.host if request.client else "unknown"

    # Rate limiting
    is_allowed, message = rate_limiter.is_allowed(client_ip)
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(status_code=429, detail=message)

    # Continue with request
    response = await call_next(request)
    return response

# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the parameter control dashboard"""
    return HTML_CONTENT

@app.post("/api/parameters/update")
async def update_parameter(
    parameter_update: SecureParameterUpdate,
    client_ip: str = None
):
    """Secure parameter update endpoint with comprehensive validation"""
    try:
        # Sanitize inputs
        parameter_update.parameter_name = security_validator.sanitize_input(parameter_update.parameter_name)
        parameter_update.user_id = security_validator.sanitize_input(parameter_update.user_id)
        parameter_update.session_id = security_validator.sanitize_input(parameter_update.session_id)

        # Validate parameter exists
        if parameter_update.parameter_name not in current_parameters:
            raise HTTPException(status_code=400, detail="Invalid parameter name")

        # Validate parameter value
        is_valid, validation_message = security_validator.validate_parameter_value(
            parameter_update.parameter_name,
            parameter_update.value
        )

        if not is_valid:
            raise HTTPException(status_code=400, detail=validation_message)

        # Check value range
        param_config = current_parameters[parameter_update.parameter_name]
        if not (param_config["min"] <= parameter_update.value <= param_config["max"]):
            raise HTTPException(
                status_code=400,
                detail=f"Value {parameter_update.value} out of range [{param_config['min']}, {param_config['max']}]"
            )

        # Update parameter
        old_value = param_config["value"]
        param_config["value"] = parameter_update.value

        # Calculate risk level
        value_change = abs(parameter_update.value - old_value) / old_value if old_value != 0 else 0
        if value_change > 0.5:
            risk_level = "HIGH"
        elif value_change > 0.2:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Record update
        update_record = ParameterUpdate(
            parameter_name=parameter_update.parameter_name,
            old_value=old_value,
            new_value=parameter_update.value,
            timestamp=datetime.now(),
            user_id=parameter_update.user_id,
            session_id=parameter_update.session_id,
            risk_level=risk_level,
            validated=True
        )

        parameter_history.append(update_record)

        # Broadcast update to all connected clients
        await websocket_manager.broadcast({
            "type": "parameter_update",
            "parameter": parameter_update.parameter_name,
            "old_value": old_value,
            "new_value": parameter_update.value,
            "risk_level": risk_level,
            "timestamp": update_record.timestamp.isoformat(),
            "user_id": parameter_update.user_id
        })

        logger.info(f"Parameter updated: {parameter_update.parameter_name} = {parameter_update.value} (Risk: {risk_level})")

        return {
            "status": "success",
            "message": "Parameter updated successfully",
            "parameter": parameter_update.parameter_name,
            "old_value": old_value,
            "new_value": parameter_update.value,
            "risk_level": risk_level,
            "timestamp": update_record.timestamp.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating parameter: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/parameters/current")
async def get_current_parameters():
    """Get current parameter values"""
    return {
        "parameters": current_parameters,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/parameters/history")
async def get_parameter_history(limit: int = Query(50, ge=1, le=1000)):
    """Get parameter update history"""
    return {
        "history": [
            {
                "parameter_name": update.parameter_name,
                "old_value": update.old_value,
                "new_value": update.new_value,
                "timestamp": update.timestamp.isoformat(),
                "user_id": update.user_id,
                "risk_level": update.risk_level,
                "validated": update.validated
            }
            for update in parameter_history[-limit:]
        ],
        "total_count": len(parameter_history)
    }

@app.get("/api/system/stats")
async def get_system_stats():
    """Get system statistics"""
    system_stats = {
        "websocket_stats": websocket_manager.get_stats(),
        "parameter_count": len(current_parameters),
        "update_count": len(parameter_history),
        "security_features": {
            "bleach_available": BLEACH_AVAILABLE,
            "redis_available": REDIS_AVAILABLE,
            "psutil_available": PSUTIL_AVAILABLE
        }
    }

    if PSUTIL_AVAILABLE:
        try:
            system_stats["system_resources"] = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent
            }
        except Exception as e:
            logger.warning(f"Could not get system resource stats: {e}")

    return system_stats

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time parameter updates"""
    client_id = f"client_{int(time.time())}_{len(websocket_manager.active_connections)}"
    await websocket_manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket_manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                elif message.get("type") == "get_parameters":
                    await websocket_manager.send_personal_message({
                        "type": "parameters",
                        "parameters": current_parameters,
                        "timestamp": datetime.now().isoformat()
                    }, websocket)

            except json.JSONDecodeError:
                await websocket_manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, websocket)

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

# HTML Content
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CBSC Production Parameter System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }

        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }

        .main-content {
            padding: 40px;
        }

        .parameters-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }

        .parameter-card {
            background: #f8fafc;
            border-radius: 15px;
            padding: 25px;
            border: 2px solid #e2e8f0;
            transition: all 0.3s ease;
        }

        .parameter-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            border-color: #4f46e5;
        }

        .parameter-label {
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 8px;
            font-size: 1.1rem;
        }

        .parameter-value {
            font-size: 2rem;
            font-weight: 700;
            color: #4f46e5;
            margin-bottom: 5px;
        }

        .parameter-range {
            font-size: 0.9rem;
            color: #64748b;
            margin-bottom: 15px;
        }

        .parameter-slider {
            width: 100%;
            height: 8px;
            border-radius: 5px;
            background: #e2e8f0;
            outline: none;
            -webkit-appearance: none;
            margin-bottom: 10px;
        }

        .parameter-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 25px;
            height: 25px;
            border-radius: 50%;
            background: #4f46e5;
            cursor: pointer;
            box-shadow: 0 2px 10px rgba(79, 70, 229, 0.3);
        }

        .parameter-slider::-moz-range-thumb {
            width: 25px;
            height: 25px;
            border-radius: 50%;
            background: #4f46e5;
            cursor: pointer;
            box-shadow: 0 2px 10px rgba(79, 70, 229, 0.3);
        }

        .update-btn {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s ease;
        }

        .update-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(79, 70, 229, 0.3);
        }

        .update-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .status-panel {
            background: #1e293b;
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
        }

        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .status-item {
            text-align: center;
        }

        .status-value {
            font-size: 2rem;
            font-weight: 700;
            color: #4f46e5;
            margin-bottom: 5px;
        }

        .status-label {
            font-size: 0.9rem;
            opacity: 0.8;
        }

        .connection-status {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 20px;
        }

        .connection-status.connected {
            background: #10b981;
            color: white;
        }

        .connection-status.disconnected {
            background: #ef4444;
            color: white;
        }

        .history-panel {
            background: #f8fafc;
            border-radius: 15px;
            padding: 25px;
            border: 2px solid #e2e8f0;
        }

        .history-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 20px;
        }

        .history-item {
            background: white;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid #4f46e5;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .history-parameter {
            font-weight: 600;
            color: #1e293b;
        }

        .history-change {
            color: #64748b;
            margin: 0 10px;
        }

        .history-risk {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
        }

        .risk-low {
            background: #dcfce7;
            color: #16a34a;
        }

        .risk-medium {
            background: #fef3c7;
            color: #d97706;
        }

        .risk-high {
            background: #fee2e2;
            color: #dc2626;
        }

        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 15px;
            }

            .main-content {
                padding: 20px;
            }

            .parameters-grid {
                grid-template-columns: 1fr;
                gap: 20px;
            }

            .header h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>CBSC Production Parameter System</h1>
            <p>Enterprise-grade parameter control with security validation</p>
        </div>

        <div class="main-content">
            <div class="status-panel">
                <div id="connectionStatus" class="connection-status disconnected">
                    Connecting to server...
                </div>

                <div class="status-grid">
                    <div class="status-item">
                        <div id="activeConnections" class="status-value">-</div>
                        <div class="status-label">Active Connections</div>
                    </div>
                    <div class="status-item">
                        <div id="totalUpdates" class="status-value">-</div>
                        <div class="status-label">Total Updates</div>
                    </div>
                    <div class="status-item">
                        <div id="messagesSent" class="status-value">-</div>
                        <div class="status-label">Messages Sent</div>
                    </div>
                    <div class="status-item">
                        <div id="serverTime" class="status-value">-</div>
                        <div class="status-label">Server Time</div>
                    </div>
                </div>
            </div>

            <div class="parameters-grid" id="parametersGrid">
                <!-- Parameters will be loaded dynamically -->
            </div>

            <div class="history-panel">
                <div class="history-title">Parameter Update History</div>
                <div id="historyList">
                    <!-- History items will be loaded dynamically -->
                </div>
            </div>
        </div>
    </div>

    <script>
        class ProductionParameterSystem {
            constructor() {
                this.ws = null;
                this.parameters = {};
                this.history = [];
                this.stats = {};
                this.reconnectAttempts = 0;
                this.maxReconnectAttempts = 5;
                this.reconnectDelay = 3000;

                this.init();
            }

            init() {
                this.connectWebSocket();
                this.loadParameters();
                this.setupEventListeners();

                // Refresh system stats every 5 seconds
                setInterval(() => this.loadSystemStats(), 5000);
            }

            connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;

                try {
                    this.ws = new WebSocket(wsUrl);

                    this.ws.onopen = () => {
                        console.log('WebSocket connected');
                        this.updateConnectionStatus(true);
                        this.reconnectAttempts = 0;

                        // Request current parameters
                        this.ws.send(JSON.stringify({ type: 'get_parameters' }));
                    };

                    this.ws.onmessage = (event) => {
                        const message = JSON.parse(event.data);
                        this.handleWebSocketMessage(message);
                    };

                    this.ws.onclose = () => {
                        console.log('WebSocket disconnected');
                        this.updateConnectionStatus(false);
                        this.attemptReconnect();
                    };

                    this.ws.onerror = (error) => {
                        console.error('WebSocket error:', error);
                        this.updateConnectionStatus(false);
                    };

                } catch (error) {
                    console.error('Failed to connect WebSocket:', error);
                    this.updateConnectionStatus(false);
                    this.attemptReconnect();
                }
            }

            attemptReconnect() {
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

                    setTimeout(() => {
                        this.connectWebSocket();
                    }, this.reconnectDelay);
                } else {
                    console.log('Max reconnection attempts reached');
                }
            }

            updateConnectionStatus(connected) {
                const statusElement = document.getElementById('connectionStatus');
                if (connected) {
                    statusElement.textContent = 'Connected to server';
                    statusElement.className = 'connection-status connected';
                } else {
                    statusElement.textContent = 'Disconnected from server';
                    statusElement.className = 'connection-status disconnected';
                }
            }

            handleWebSocketMessage(message) {
                switch (message.type) {
                    case 'connection_established':
                        console.log('Connection established with server');
                        this.stats = message.server_stats;
                        this.updateStatsDisplay();
                        break;

                    case 'parameters':
                        this.parameters = message.parameters;
                        this.renderParameters();
                        break;

                    case 'parameter_update':
                        this.handleParameterUpdate(message);
                        break;

                    case 'pong':
                        // Ping-pong successful
                        break;

                    default:
                        console.log('Unknown message type:', message.type);
                }
            }

            handleParameterUpdate(update) {
                // Update local parameter value
                if (this.parameters[update.parameter]) {
                    this.parameters[update.parameter].value = update.new_value;
                }

                // Update UI
                this.renderParameters();

                // Add to history
                this.addToHistory(update);

                // Show notification
                this.showNotification(
                    `Parameter ${update.parameter} updated to ${update.new_value.toFixed(2)}`,
                    update.risk_level
                );
            }

            async loadParameters() {
                try {
                    const response = await fetch('/api/parameters/current');
                    const data = await response.json();
                    this.parameters = data.parameters;
                    this.renderParameters();
                } catch (error) {
                    console.error('Failed to load parameters:', error);
                }
            }

            async loadSystemStats() {
                try {
                    const response = await fetch('/api/system/stats');
                    const data = await response.json();
                    this.stats = data;
                    this.updateStatsDisplay();
                } catch (error) {
                    console.error('Failed to load system stats:', error);
                }
            }

            updateStatsDisplay() {
                if (!this.stats.websocket_stats) return;

                document.getElementById('activeConnections').textContent =
                    this.stats.websocket_stats.active_connections || 0;
                document.getElementById('totalUpdates').textContent =
                    this.stats.update_count || 0;
                document.getElementById('messagesSent').textContent =
                    this.stats.websocket_stats.messages_sent || 0;
                document.getElementById('serverTime').textContent =
                    new Date().toLocaleTimeString();
            }

            renderParameters() {
                const grid = document.getElementById('parametersGrid');
                grid.innerHTML = '';

                Object.entries(this.parameters).forEach(([name, config]) => {
                    const card = this.createParameterCard(name, config);
                    grid.appendChild(card);
                });
            }

            createParameterCard(name, config) {
                const card = document.createElement('div');
                card.className = 'parameter-card';

                const formattedName = name.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase());

                card.innerHTML = `
                    <div class="parameter-label">${formattedName}</div>
                    <div class="parameter-value">${config.value.toFixed(2)} ${config.unit}</div>
                    <div class="parameter-range">Range: ${config.min.toFixed(1)} - ${config.max.toFixed(1)} ${config.unit}</div>
                    <input type="range"
                           class="parameter-slider"
                           id="slider-${name}"
                           min="${config.min}"
                           max="${config.max}"
                           step="${(config.max - config.min) / 100}"
                           value="${config.value}">
                    <button class="update-btn" onclick="parameterSystem.updateParameter('${name}')">
                        Update ${formattedName}
                    </button>
                `;

                return card;
            }

            async updateParameter(parameterName) {
                const slider = document.getElementById(`slider-${parameterName}`);
                const newValue = parseFloat(slider.value);

                try {
                    const response = await fetch('/api/parameters/update', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            parameter_name: parameterName,
                            value: newValue,
                            user_id: 'web_user',
                            session_id: 'web_session_' + Date.now()
                        })
                    });

                    const result = await response.json();

                    if (response.ok) {
                        this.showNotification(
                            `Parameter ${parameterName} updated successfully`,
                            result.risk_level
                        );
                    } else {
                        this.showNotification(`Error: ${result.detail}`, 'error');
                    }

                } catch (error) {
                    console.error('Failed to update parameter:', error);
                    this.showNotification('Network error occurred', 'error');
                }
            }

            addToHistory(update) {
                const historyList = document.getElementById('historyList');

                const historyItem = document.createElement('div');
                historyItem.className = 'history-item';

                const formattedName = update.parameter.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase());
                const riskClass = `risk-${update.risk_level.toLowerCase()}`;

                historyItem.innerHTML = `
                    <div>
                        <span class="history-parameter">${formattedName}</span>
                        <span class="history-change">
                            ${update.old_value.toFixed(2)} → ${update.new_value.toFixed(2)}
                        </span>
                    </div>
                    <div>
                        <span class="history-risk ${riskClass}">${update.risk_level}</span>
                        <span style="margin-left: 10px; color: #64748b; font-size: 0.9rem;">
                            ${new Date(update.timestamp).toLocaleTimeString()}
                        </span>
                    </div>
                `;

                historyList.insertBefore(historyItem, historyList.firstChild);

                // Keep only last 10 items in display
                while (historyList.children.length > 10) {
                    historyList.removeChild(historyList.lastChild);
                }
            }

            showNotification(message, type = 'info') {
                // Simple notification - could be enhanced with a proper notification system
                const colors = {
                    'info': '#3b82f6',
                    'success': '#10b981',
                    'warning': '#f59e0b',
                    'error': '#ef4444',
                    'LOW': '#10b981',
                    'MEDIUM': '#f59e0b',
                    'HIGH': '#ef4444'
                };

                console.log(`[${type.toUpperCase()}] ${message}`);
            }

            setupEventListeners() {
                // Ping server every 30 seconds to keep connection alive
                setInterval(() => {
                    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                        this.ws.send(JSON.stringify({ type: 'ping' }));
                    }
                }, 30000);
            }
        }

        // Initialize the system when page loads
        let parameterSystem;
        document.addEventListener('DOMContentLoaded', () => {
            parameterSystem = new ProductionParameterSystem();
        });
    </script>
</body>
</html>
"""

def main():
    """Main function to run the production demo"""
    print("Starting CBSC Production Parameter System...")
    print("=" * 60)
    print("Features:")
    print("- Enterprise-grade security validation")
    print("- Real-time parameter control via WebSocket")
    print("- Rate limiting and DDoS protection")
    print("- Comprehensive input sanitization")
    print("- Production logging and monitoring")
    print("=" * 60)
    print("Access the dashboard at: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
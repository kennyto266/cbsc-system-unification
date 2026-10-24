#!/usr/bin/env python3
"""
Monitoring Dashboard - Web-based Real-time Monitoring Interface

Provides a web-based dashboard for monitoring parallel backtesting operations.
Features real-time updates, performance visualizations, and comprehensive metrics.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import aiohttp
from aiohttp import web, WSMsgType

logger = logging.getLogger(__name__)


@dataclass
class DashboardConfig:
    """Dashboard configuration."""
    host: str = "localhost"
    port: int = 8080
    websocket_url: str = "ws://localhost:8765"
    refresh_interval: int = 1  # seconds
    max_history_points: int = 1000


class MonitoringDashboard:
    """
    Web-based monitoring dashboard.

    Features:
    - Real-time WebSocket integration
    - Interactive charts and visualizations
    - Performance metrics display
    - Task progress tracking
    - System monitoring
    - Alert system
    """

    def __init__(self, config: Optional[DashboardConfig] = None):
        self.config = config or DashboardConfig()
        self.app = web.Application()
        self.setup_routes()

        # WebSocket connection
        self.websocket = None
        self.session = None

        # Data storage
        self.current_status = {}
        self.performance_history = []
        self.task_history = []
        self.alerts = []
        self.connected_clients = set()

        # Background tasks
        self.background_tasks = set()

        logger.info(f"Monitoring dashboard initialized on {self.config.host}:{self.config.port}")

    def setup_routes(self) -> None:
        """Setup HTTP routes for the dashboard."""
        self.app.router.add_get('/', self.serve_dashboard)
        self.app.router.add_get('/api/status', self.get_status)
        self.app.router.add_get('/api/performance', self.get_performance_data)
        self.app.router.add_get('/api/tasks', self.get_task_data)
        self.app.router.add_get('/api/alerts', self.get_alerts)
        self.app.router.add_get('/ws', self.websocket_handler)

        # Static files for CSS/JS
        self.app.router.add_static('/', path='static', name='static')

    async def serve_dashboard(self, request: web.Request) -> web.Response:
        """Serve the main dashboard HTML page."""
        html_content = self._generate_dashboard_html()
        return web.Response(text=html_content, content_type='text/html')

    async def get_status(self, request: web.Request) -> web.Response:
        """Get current monitoring status."""
        return web.json_response(self.current_status)

    async def get_performance_data(self, request: web.Request) -> web.Response:
        """Get performance history data."""
        limit = int(request.query.get('limit', self.config.max_history_points))
        data = self.performance_history[-limit:] if self.performance_history else []
        return web.json_response(data)

    async def get_task_data(self, request: web.Request) -> web.Response:
        """Get task tracking data."""
        return web.json_response(self.task_history)

    async def get_alerts(self, request: web.Request) -> web.Response:
        """Get alert history."""
        limit = int(request.query.get('limit', 100))
        alerts = self.alerts[-limit:] if self.alerts else []
        return web.json_response(alerts)

    async def websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections for real-time updates."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.connected_clients.add(ws)
        client_id = f"{request.remote}_{len(self.connected_clients)}"
        logger.info(f"Dashboard client connected: {client_id}")

        try:
            # Send initial data
            await ws.send_str(json.dumps({
                "type": "initial_data",
                "status": self.current_status,
                "performance": self.performance_history[-50:],
                "alerts": self.alerts[-10:]
            }))

            # Handle client messages
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self.handle_dashboard_message(ws, data)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON from dashboard client: {msg.data}")
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')

        except Exception as e:
            logger.error(f"Error in dashboard WebSocket handler: {e}")
        finally:
            self.connected_clients.discard(ws)
            logger.info(f"Dashboard client disconnected: {client_id}")

        return ws

    async def handle_dashboard_message(
        self,
        ws: web.WebSocketResponse,
        data: Dict[str, Any]
    ) -> None:
        """Handle messages from dashboard clients."""
        message_type = data.get("type")

        if message_type == "subscribe":
            # Handle subscription requests
            events = data.get("events", [])
            logger.info(f"Dashboard client subscribed to: {events}")

        elif message_type == "get_status":
            # Send current status
            await ws.send_str(json.dumps({
                "type": "status_update",
                "data": self.current_status
            }))

    def _generate_dashboard_html(self) -> str:
        """Generate the dashboard HTML page."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parallel Backtesting Monitor</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .status-bar {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .status-item {
            display: inline-block;
            margin: 0 20px;
            font-weight: 600;
        }

        .status-item span {
            color: #667eea;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.2em;
        }

        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }

        .task-item {
            border-left: 4px solid #667eea;
            padding: 10px;
            margin: 10px 0;
            background: #f8f9fa;
            border-radius: 5px;
        }

        .task-item.running {
            border-left-color: #28a745;
        }

        .task-item.failed {
            border-left-color: #dc3545;
        }

        .task-item.completed {
            border-left-color: #6c757d;
        }

        .alert {
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            font-weight: 500;
        }

        .alert.warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
        }

        .alert.error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }

        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }

        .metric {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }

        .metric-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
        }

        .metric-label {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }

        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 8px 15px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
        }

        .connected {
            background: #d4edda;
            color: #155724;
        }

        .disconnected {
            background: #f8d7da;
            color: #721c24;
        }

        canvas {
            max-height: 300px;
        }
    </style>
</head>
<body>
    <div class="connection-status" id="connectionStatus">
        <span id="connectionText">Connecting...</span>
    </div>

    <div class="container">
        <div class="header">
            <h1>🚀 Parallel Backtesting Monitor</h1>
            <p>Real-time monitoring and performance analytics</p>
        </div>

        <div class="status-bar">
            <div class="status-item">
                Server Status: <span id="serverStatus">Loading...</span>
            </div>
            <div class="status-item">
                Active Tasks: <span id="activeTasks">0</span>
            </div>
            <div class="status-item">
                Completed Tasks: <span id="completedTasks">0</span>
            </div>
            <div class="status-item">
                Success Rate: <span id="successRate">0%</span>
            </div>
            <div class="status-item">
                ETA Accuracy: <span id="etaAccuracy">N/A</span>
            </div>
            <div class="status-item">
                Last Update: <span id="lastUpdate">Never</span>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>📊 Performance Metrics</h3>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value" id="avgExecutionTime">0s</div>
                        <div class="metric-label">Avg Execution Time</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="throughput">0</div>
                        <div class="metric-label">Tasks/Hour</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="efficiency">0%</div>
                        <div class="metric-label">Efficiency</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="failureRate">0%</div>
                        <div class="metric-label">Failure Rate</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3>⚡ System Resources</h3>
                <canvas id="resourceChart"></canvas>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>📈 Task Progress Timeline</h3>
                <canvas id="progressChart"></canvas>
            </div>

            <div class="card">
                <h3>⏱️ ETA Accuracy Analysis</h3>
                <canvas id="etaChart"></canvas>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>📋 Active Tasks</h3>
                <div id="activeTasksList">
                    <p>No active tasks</p>
                </div>
            </div>

            <div class="card">
                <h3>🚨 Recent Alerts</h3>
                <div id="alertsList">
                    <p>No recent alerts</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        // WebSocket connection
        let ws;
        let reconnectInterval;

        const charts = {};

        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            ws = new WebSocket(wsUrl);

            ws.onopen = function() {
                console.log('WebSocket connected');
                updateConnectionStatus(true);
                clearInterval(reconnectInterval);
            };

            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };

            ws.onclose = function() {
                console.log('WebSocket disconnected');
                updateConnectionStatus(false);
                // Attempt to reconnect
                reconnectInterval = setInterval(connectWebSocket, 5000);
            };

            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }

        function updateConnectionStatus(connected) {
            const status = document.getElementById('connectionStatus');
            const text = document.getElementById('connectionText');

            if (connected) {
                status.className = 'connection-status connected';
                text.textContent = 'Connected';
            } else {
                status.className = 'connection-status disconnected';
                text.textContent = 'Disconnected';
            }
        }

        function handleWebSocketMessage(data) {
            switch(data.type) {
                case 'initial_data':
                    updateDashboard(data.status);
                    if (data.performance) updatePerformanceChart(data.performance);
                    if (data.alerts) updateAlerts(data.alerts);
                    break;
                case 'status_update':
                    updateDashboard(data.data);
                    break;
                case 'task_progress':
                    updateTaskProgress(data.data);
                    break;
                case 'alert':
                    addAlert(data.data);
                    break;
            }
        }

        function updateDashboard(status) {
            // Update status bar
            document.getElementById('serverStatus').textContent =
                status.monitor?.is_running ? 'Running' : 'Stopped';
            document.getElementById('activeTasks').textContent =
                status.monitor?.active_tasks || 0;
            document.getElementById('completedTasks').textContent =
                status.monitor?.completed_tasks || 0;

            const successRate = status.progress?.overall?.completion_rate || 0;
            document.getElementById('successRate').textContent =
                `${(successRate * 100).toFixed(1)}%`;

            const etaAccuracy = status.progress?.eta_accuracy?.average_error || 0;
            document.getElementById('etaAccuracy').textContent =
                etaAccuracy < 60 ? `±${etaAccuracy.toFixed(1)}s` : 'N/A';

            document.getElementById('lastUpdate').textContent =
                new Date().toLocaleTimeString();

            // Update metrics
            const performance = status.performance || {};
            document.getElementById('avgExecutionTime').textContent =
                `${(performance.average_execution_time || 0).toFixed(1)}s`;
            document.getElementById('throughput').textContent =
                Math.round(performance.throughput_per_hour || 0);
            document.getElementById('efficiency').textContent =
                `${((performance.efficiency_score || 0) * 100).toFixed(1)}%`;
            document.getElementById('failureRate').textContent =
                `${((performance.failure_rate || 0) * 100).toFixed(1)}%`;

            // Update system resources
            updateResourceChart(status.system);

            // Update active tasks
            updateActiveTasksList(status.progress?.tasks || {});

            // Store current status
            window.currentStatus = status;
        }

        function updateResourceChart(system) {
            const ctx = document.getElementById('resourceChart').getContext('2d');

            if (!charts.resource) {
                charts.resource = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [
                            {
                                label: 'CPU %',
                                data: [],
                                borderColor: '#667eea',
                                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                                tension: 0.4
                            },
                            {
                                label: 'Memory %',
                                data: [],
                                borderColor: '#764ba2',
                                backgroundColor: 'rgba(118, 75, 162, 0.1)',
                                tension: 0.4
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100
                            }
                        }
                    }
                });
            }

            // Update with new data
            const chart = charts.resource;
            const now = new Date().toLocaleTimeString();

            chart.data.labels.push(now);
            chart.data.datasets[0].data.push(system?.cpu_percent || 0);
            chart.data.datasets[1].data.push(system?.memory_percent || 0);

            // Keep only last 20 points
            if (chart.data.labels.length > 20) {
                chart.data.labels.shift();
                chart.data.datasets.forEach(dataset => dataset.data.shift());
            }

            chart.update('none');
        }

        function updateActiveTasksList(tasks) {
            const container = document.getElementById('activeTasksList');

            if (Object.keys(tasks).length === 0) {
                container.innerHTML = '<p>No active tasks</p>';
                return;
            }

            let html = '';
            for (const [taskId, taskInfo] of Object.entries(tasks)) {
                const statusClass = taskInfo.status === 'running' ? 'running' :
                                   taskInfo.status === 'failed' ? 'failed' : 'completed';

                html += `
                    <div class="task-item ${statusClass}">
                        <div><strong>${taskId.substring(0, 8)}</strong> - ${taskInfo.status}</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${taskInfo.progress}%"></div>
                        </div>
                        <div>
                            Progress: ${(taskInfo.progress || 0).toFixed(1)}% |
                            Phase: ${taskInfo.current_phase || 'Unknown'} |
                            ETA: ${taskInfo.eta ? `${(taskInfo.eta/60).toFixed(1)}m` : 'N/A'}
                        </div>
                        ${taskInfo.message ? `<div><em>${taskInfo.message}</em></div>` : ''}
                    </div>
                `;
            }

            container.innerHTML = html;
        }

        function addAlert(alert) {
            const alertsContainer = document.getElementById('alertsList');
            const alertClass = alert.alert_type.includes('error') ? 'error' : 'warning';
            const timestamp = new Date().toLocaleTimeString();

            const alertHtml = `
                <div class="alert ${alertClass}">
                    <strong>${timestamp}</strong> - ${alert.message}
                </div>
            `;

            alertsContainer.insertAdjacentHTML('afterbegin', alertHtml);

            // Keep only last 10 alerts
            const alerts = alertsContainer.querySelectorAll('.alert');
            if (alerts.length > 10) {
                alerts[alerts.length - 1].remove();
            }
        }

        function updateAlerts(alerts) {
            const container = document.getElementById('alertsList');

            if (alerts.length === 0) {
                container.innerHTML = '<p>No recent alerts</p>';
                return;
            }

            let html = '';
            alerts.slice(-10).reverse().forEach(alert => {
                const timestamp = new Date(alert.timestamp || Date.now()).toLocaleTimeString();
                const alertClass = alert.alert_type.includes('error') ? 'error' : 'warning';

                html += `
                    <div class="alert ${alertClass}">
                        <strong>${timestamp}</strong> - ${alert.message}
                    </div>
                `;
            });

            container.innerHTML = html;
        }

        // Initialize WebSocket connection
        connectWebSocket();

        // Set up periodic status updates
        setInterval(async () => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({type: 'get_status'}));
            }
        }, 5000);
    </script>
</body>
</html>
        """

    async def start(self) -> None:
        """Start the dashboard server."""
        runner = web.AppRunner(self.app)
        await runner.setup()

        site = web.TCPSite(runner, self.config.host, self.config.port)
        await site.start()

        logger.info(f"Dashboard started at http://{self.config.host}:{self.config.port}")

    async def stop(self) -> None:
        """Stop the dashboard server."""
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        # Close WebSocket connections
        for ws in self.connected_clients:
            await ws.close()

        logger.info("Dashboard stopped")

    async def update_status(self, status_data: Dict[str, Any]) -> None:
        """Update dashboard status data."""
        self.current_status = status_data

        # Broadcast to connected clients
        if self.connected_clients:
            message = json.dumps({
                "type": "status_update",
                "data": status_data
            })

            for ws in self.connected_clients.copy():
                try:
                    await ws.send_str(message)
                except Exception as e:
                    logger.error(f"Failed to send update to dashboard client: {e}")
                    self.connected_clients.discard(ws)

    async def add_alert(self, alert_type: str, message: str, data: Dict[str, Any] = None) -> None:
        """Add alert to dashboard."""
        alert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "alert_type": alert_type,
            "message": message,
            "data": data or {}
        }

        self.alerts.append(alert)

        # Keep only recent alerts
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]

        # Broadcast to clients
        if self.connected_clients:
            message = json.dumps({
                "type": "alert",
                "data": alert
            })

            for ws in self.connected_clients.copy():
                try:
                    await ws.send_str(message)
                except Exception as e:
                    logger.error(f"Failed to send alert to dashboard client: {e}")
                    self.connected_clients.discard(ws)


# Convenience function for creating and running dashboard
async def run_dashboard(
    host: str = "localhost",
    port: int = 8080,
    websocket_url: str = "ws://localhost:8765"
) -> MonitoringDashboard:
    """
    Create and run a monitoring dashboard.

    Args:
        host: Dashboard host
        port: Dashboard port
        websocket_url: WebSocket server URL for real-time updates

    Returns:
        Running MonitoringDashboard instance
    """
    config = DashboardConfig(
        host=host,
        port=port,
        websocket_url=websocket_url
    )

    dashboard = MonitoringDashboard(config)
    await dashboard.start()

    return dashboard
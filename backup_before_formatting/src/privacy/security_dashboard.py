"""
T108: 安全仪表板

实现安全仪表板功能，包括：
- Web界面展示
- 实时安全指标
- 可视化图表
- 告警中心
- 安全状态总览
"""

import asyncio
import json
import logging
import sqlite3
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import uvicorn
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


class AlertSeverity(Enum):
    """告警严重级别"""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """告警状态"""

    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class SecurityAlert:
    """安全告警"""

    alert_id: str
    timestamp: datetime
    severity: AlertSeverity
    title: str
    description: str
    source: str
    status: AlertStatus = AlertStatus.NEW
    details: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "status": self.status.value,
            "details": self.details or {},
            "metadata": self.metadata or {},
        }


@dataclass
class SecurityMetric:
    """安全指标"""

    name: str
    value: float
    unit: str
    timestamp: datetime
    threshold: Optional[float] = None
    status: str = "normal"  # normal, warning, critical

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "threshold": self.threshold,
            "status": self.status,
        }


class AlertManager:
    """告警管理器"""

    def __init__(self, db_path: str = "logs / security_alerts.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.alerts: deque = deque(maxlen=10000)  # 最多保留10000条告警
        self.active_alerts: Dict[str, SecurityAlert] = {}
        self.subscribers: Set[WebSocket] = set()
        self.logger = logging.getLogger("hk_quant_system.security.alerts")
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS security_alerts (
                    alert_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    metadata TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_alerts_timestamp
                ON security_alerts(timestamp)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_alerts_severity
                ON security_alerts(severity)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_alerts_status
                ON security_alerts(status)
            """
            )

            conn.commit()

    async def create_alert(self, alert: SecurityAlert) -> str:
        """创建告警"""
        self.alerts.append(alert)
        self.active_alerts[alert.alert_id] = alert
        self._save_to_database(alert)

        # 通知订阅者
        await self._broadcast(alert.to_dict())

        self.logger.warning(f"Security alert: {alert.severity.value} - {alert.title}")

        return alert.alert_id

    def _save_to_database(self, alert: SecurityAlert):
        """保存到数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO security_alerts
                (alert_id, timestamp, severity, title, description, source,
                 status, details, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    alert.alert_id,
                    alert.timestamp.isoformat(),
                    alert.severity.value,
                    alert.title,
                    alert.description,
                    alert.source,
                    alert.status.value,
                    json.dumps(alert.details or {}),
                    json.dumps(alert.metadata or {}),
                ),
            )
            conn.commit()

    def get_alerts(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        获取告警列表

        Args:
            start_time: 开始时间
            end_time: 结束时间
            severity: 严重级别
            status: 状态
            limit: 限制数量

        Returns:
            告警列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            query = "SELECT * FROM security_alerts WHERE 1=1"
            params = []

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())

            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())

            if severity:
                query += " AND severity = ?"
                params.append(severity)

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].status = AlertStatus.ACKNOWLEDGED
            self._save_to_database(self.active_alerts[alert_id])
            await self._broadcast({"type": "alert_acknowledged", "alert_id": alert_id})
            return True
        return False

    async def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].status = AlertStatus.RESOLVED
            self._save_to_database(self.active_alerts[alert_id])
            del self.active_alerts[alert_id]
            await self._broadcast({"type": "alert_resolved", "alert_id": alert_id})
            return True
        return False

    def get_alert_statistics(self) -> Dict[str, Any]:
        """获取告警统计"""
        recent_alerts = [
            a
            for a in self.alerts
            if a.timestamp >= datetime.utcnow() - timedelta(days=30)
        ]

        if not recent_alerts:
            return {}

        stats = {
            "total": len(recent_alerts),
            "by_severity": defaultdict(int),
            "by_status": defaultdict(int),
            "new_today": 0,
            "unresolved": 0,
        }

        today = datetime.utcnow().date()
        for alert in recent_alerts:
            stats["by_severity"][alert.severity.value] += 1
            stats["by_status"][alert.status.value] += 1

            if alert.timestamp.date() == today:
                stats["new_today"] += 1

            if alert.status in [AlertStatus.NEW, AlertStatus.ACKNOWLEDGED]:
                stats["unresolved"] += 1

        stats["by_severity"] = dict(stats["by_severity"])
        stats["by_status"] = dict(stats["by_status"])

        return stats

    async def subscribe(self, websocket: WebSocket):
        """订阅告警"""
        await websocket.accept()
        self.subscribers.add(websocket)

    async def unsubscribe(self, websocket: WebSocket):
        """取消订阅"""
        self.subscribers.discard(websocket)

    async def _broadcast(self, message: Dict[str, Any]):
        """广播消息"""
        if not self.subscribers:
            return

        disconnected = set()
        for websocket in self.subscribers:
            try:
                await websocket.send_json(message)
            except WebSocketDisconnect:
                disconnected.add(websocket)
            except Exception as e:
                self.logger.error(f"Failed to send message: {e}")
                disconnected.add(websocket)

        # 清理断开的连接
        for websocket in disconnected:
            self.subscribers.discard(websocket)


class SecurityMetricsCollector:
    """安全指标收集器"""

    def __init__(self, audit_logger, access_tracker):
        self.audit_logger = audit_logger
        self.access_tracker = access_tracker
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.logger = logging.getLogger("hk_quant_system.security.metrics")

    def collect_metrics(self) -> List[SecurityMetric]:
        """收集安全指标"""
        metrics = []

        # 1. 审计事件数量
        stats = self.audit_logger.get_statistics()
        metrics.append(
            SecurityMetric(
                name="audit_events_total",
                value=stats.get("total_events", 0),
                unit="count",
                timestamp=datetime.utcnow(),
                status="normal",
            )
        )

        # 2. 失败率
        failure_rate = 100 - stats.get("success_rate", 100)
        metrics.append(
            SecurityMetric(
                name="audit_failure_rate",
                value=failure_rate,
                unit="%",
                timestamp=datetime.utcnow(),
                threshold=10.0,
                status="critical" if failure_rate > 10 else "normal",
            )
        )

        # 3. 访问事件数量
        access_stats = self.access_tracker.get_system_statistics()
        metrics.append(
            SecurityMetric(
                name="access_events_total",
                value=access_stats.get("total_accesses", 0),
                unit="count",
                timestamp=datetime.utcnow(),
                status="normal",
            )
        )

        # 4. 未授权访问率
        unauthorized_rate = 0
        if access_stats.get("total_accesses", 0) > 0:
            denied = access_stats.get("by_status", {}).get("denied", 0)
            unauthorized_rate = (denied / access_stats["total_accesses"]) * 100

        metrics.append(
            SecurityMetric(
                name="unauthorized_access_rate",
                value=unauthorized_rate,
                unit="%",
                timestamp=datetime.utcnow(),
                threshold=5.0,
                status="high" if unauthorized_rate > 5 else "normal",
            )
        )

        # 5. 活跃用户数
        metrics.append(
            SecurityMetric(
                name="active_users",
                value=stats.get("active_users", 0),
                unit="count",
                timestamp=datetime.utcnow(),
                status="normal",
            )
        )

        # 6. 敏感数据访问率
        sensitive_rate = access_stats.get("sensitive_rate", 0)
        metrics.append(
            SecurityMetric(
                name="sensitive_access_rate",
                value=sensitive_rate,
                unit="%",
                timestamp=datetime.utcnow(),
                threshold=20.0,
                status="warning" if sensitive_rate > 20 else "normal",
            )
        )

        # 保存历史数据
        for metric in metrics:
            self.metrics_history[metric.name].append(metric)

        return metrics

    def get_metric_history(
        self, metric_name: str, hours: int = 24
    ) -> List[Dict[str, Any]]:
        """获取指标历史"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        history = [
            m.to_dict()
            for m in self.metrics_history[metric_name]
            if m.timestamp >= cutoff
        ]
        return history

    def get_all_metrics(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有指标历史"""
        return {
            name: [m.to_dict() for m in history]
            for name, history in self.metrics_history.items()
        }


class SecurityDashboard:
    """安全仪表板"""

    def __init__(
        self,
        audit_logger,
        access_tracker,
        host: str = "0.0.0.0",
        port: int = 8005,
        static_dir: str = "static / security_dashboard",
        templates_dir: str = "templates / security_dashboard",
    ):
        self.audit_logger = audit_logger
        self.access_tracker = access_tracker
        self.host = host
        self.port = port

        # 创建目录
        self.static_dir = Path(static_dir)
        self.templates_dir = Path(templates_dir)
        self.static_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # 初始化组件
        self.alert_manager = AlertManager()
        self.metrics_collector = SecurityMetricsCollector(audit_logger, access_tracker)

        # 创建FastAPI应用
        self.app = FastAPI(title="Security Dashboard", version="1.0.0")
        self._setup_routes()

        # 创建HTML页面
        self._create_dashboard_html()

        self.logger = logging.getLogger("hk_quant_system.security.dashboard")

    def _setup_routes(self):
        """设置路由"""
        # 静态文件
        self.app.mount(
            "/static", StaticFiles(directory=str(self.static_dir)), name="static"
        )

        # 主页
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            return self._get_dashboard_html()

        # 获取当前指标
        @self.app.get("/api / metrics")
        async def get_metrics():
            metrics = self.metrics_collector.collect_metrics()
            return {"metrics": [m.to_dict() for m in metrics]}

        # 获取指标历史
        @self.app.get("/api / metrics/{metric_name}")
        async def get_metric_history(metric_name: str, hours: int = 24):
            history = self.metrics_collector.get_metric_history(metric_name, hours)
            return {"metric": metric_name, "history": history}

        # 获取告警列表
        @self.app.get("/api / alerts")
        async def get_alerts(
            start_time: Optional[datetime] = Query(None),
            end_time: Optional[datetime] = Query(None),
            severity: Optional[str] = Query(None),
            status: Optional[str] = Query(None),
            limit: int = Query(100),
        ):
            alerts = self.alert_manager.get_alerts(
                start_time=start_time,
                end_time=end_time,
                severity=severity,
                status=status,
                limit=limit,
            )
            return {"alerts": alerts}

        # 确认告警
        @self.app.post("/api / alerts/{alert_id}/acknowledge")
        async def acknowledge_alert(alert_id: str):
            success = await self.alert_manager.acknowledge_alert(alert_id)
            if not success:
                raise HTTPException(status_code=404, detail="Alert not found")
            return {"status": "success"}

        # 解决告警
        @self.app.post("/api / alerts/{alert_id}/resolve")
        async def resolve_alert(alert_id: str):
            success = await self.alert_manager.resolve_alert(alert_id)
            if not success:
                raise HTTPException(status_code=404, detail="Alert not found")
            return {"status": "success"}

        # 获取告警统计
        @self.app.get("/api / alerts / statistics")
        async def get_alert_statistics():
            stats = self.alert_manager.get_alert_statistics()
            return stats

        # WebSocket连接
        @self.app.websocket("/ws / alerts")
        async def websocket_alerts(websocket: WebSocket):
            await self.alert_manager.subscribe(websocket)
            try:
                while True:
                    # 保持连接
                    await websocket.receive_text()
            except WebSocketDisconnect:
                await self.alert_manager.unsubscribe(websocket)

    def _create_dashboard_html(self):
        """创建仪表板HTML文件"""
        html_content = self._get_dashboard_html()
        with open(self.static_dir / "index.html", "w", encoding="utf - 8") as f:
            f.write(html_content)

    def _get_dashboard_html(self) -> str:
        """获取仪表板HTML"""
        return """
<!DOCTYPE html>
<html lang="zh - CN">
<head>
    <meta charset="UTF - 8">
    <meta name="viewport" content="width=device - width, initial - scale=1.0">
    <title>安全仪表板 - Security Dashboard</title>
    <script src="https://cdn.jsdelivr.net / npm / chart.js@3.9.1 / dist / chart.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box - sizing: border - box; }
        body {
            font - family: 'Segoe UI', Tahoma, Geneva, Verdana, sans - serif;
            background: #f5f7fa;
            color: #333;
        }
        header {
            background: linear - gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            box - shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        header h1 {
            font - size: 28px;
            margin - bottom: 10px;
        }
        header p {
            opacity: 0.9;
            font - size: 14px;
        }
        .container {
            max - width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        .metrics - grid {
            display: grid;
            grid - template - columns: repeat(auto - fit, minmax(250px, 1fr));
            gap: 20px;
            margin - bottom: 30px;
        }
        .metric - card {
            background: white;
            border - radius: 8px;
            padding: 20px;
            box - shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .metric - card:hover {
            transform: translateY(-2px);
            box - shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .metric - title {
            font - size: 14px;
            color: #666;
            margin - bottom: 8px;
        }
        .metric - value {
            font - size: 32px;
            font - weight: bold;
            color: #333;
        }
        .metric - unit {
            font - size: 14px;
            color: #999;
            margin - left: 4px;
        }
        .metric - status {
            display: inline - block;
            padding: 4px 8px;
            border - radius: 4px;
            font - size: 12px;
            margin - top: 8px;
        }
        .status - normal { background: #e8f5e9; color: #4caf50; }
        .status - warning { background: #fff3e0; color: #ff9800; }
        .status - critical { background: #ffebee; color: #f44336; }
        .status - high { background: #fce4ec; color: #e91e63; }

        .section {
            background: white;
            border - radius: 8px;
            padding: 20px;
            margin - bottom: 20px;
            box - shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .section - title {
            font - size: 18px;
            font - weight: 600;
            margin - bottom: 16px;
            color: #333;
        }

        .alerts - list {
            max - height: 500px;
            overflow - y: auto;
        }
        .alert - item {
            border - left: 4px solid;
            padding: 12px;
            margin - bottom: 8px;
            background: #f9f9f9;
            border - radius: 4px;
        }
        .alert - item.critical { border - color: #f44336; }
        .alert - item.high { border - color: #e91e63; }
        .alert - item.medium { border - color: #ff9800; }
        .alert - item.low { border - color: #ffc107; }
        .alert - item.info { border - color: #2196f3; }
        .alert - header {
            display: flex;
            justify - content: space - between;
            align - items: center;
            margin - bottom: 4px;
        }
        .alert - title {
            font - weight: 600;
            font - size: 14px;
        }
        .alert - time {
            font - size: 12px;
            color: #666;
        }
        .alert - description {
            font - size: 13px;
            color: #666;
            margin - bottom: 4px;
        }
        .alert - actions button {
            padding: 4px 12px;
            border: none;
            border - radius: 4px;
            cursor: pointer;
            font - size: 12px;
            margin - right: 4px;
        }
        .btn - ack { background: #2196f3; color: white; }
        .btn - resolve { background: #4caf50; color: white; }

        .chart - container {
            position: relative;
            height: 300px;
        }

        .refresh - indicator {
            display: inline - block;
            width: 8px;
            height: 8px;
            background: #4caf50;
            border - radius: 50%;
            margin - left: 8px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>🔒 安全仪表板 <span class="refresh - indicator" id="liveIndicator"></span></h1>
            <p>实时监控安全状态、审计日志和访问控制</p>
        </div>
    </header>

    <div class="container">
        <!-- 关键指标 -->
        <div class="metrics - grid" id="metricsGrid">
            <!-- 动态加载指标 -->
        </div>

        <!-- 图表区域 -->
        <div class="section">
            <h2 class="section - title">安全指标趋势</h2>
            <div class="chart - container">
                <canvas id="metricsChart"></canvas>
            </div>
        </div>

        <!-- 告警中心 -->
        <div class="section">
            <h2 class="section - title">实时告警 <span id="alertCount" style="font - size: 14px; color: #f44336;"></span></h2>
            <div class="alerts - list" id="alertsList">
                <!-- 动态加载告警 -->
            </div>
        </div>
    </div>

    <script>
        let metricsChart;
        let wsConnection;

        // 初始化页面
        document.addEventListener('DOMContentLoaded', function() {
            loadMetrics();
            loadAlerts();
            initWebSocket();
            initChart();

            // 每30秒刷新一次
            setInterval(loadMetrics, 30000);
            setInterval(loadAlerts, 30000);
        });

        // 加载指标
        async function loadMetrics() {
            try {
                const response = await fetch('/api / metrics');
                const data = await response.json();
                displayMetrics(data.metrics);
            } catch (error) {
                console.error('Failed to load metrics:', error);
            }
        }

        // 显示指标
        function displayMetrics(metrics) {
            const grid = document.getElementById('metricsGrid');
            grid.innerHTML = '';

            metrics.forEach(metric => {
                const card = document.createElement('div');
                card.className = 'metric - card';
                card.innerHTML = `
                    <div class="metric - title">${metric.name}</div>
                    <div>
                        <span class="metric - value">${metric.value.toFixed(2)}</span>
                        <span class="metric - unit">${metric.unit}</span>
                    </div>
                    <span class="metric - status status-${metric.status}">${metric.status}</span>
                `;
                grid.appendChild(card);
            });
        }

        // 加载告警
        async function loadAlerts() {
            try {
                const response = await fetch('/api / alerts?limit=50');
                const data = await response.json();
                displayAlerts(data.alerts);
            } catch (error) {
                console.error('Failed to load alerts:', error);
            }
        }

        // 显示告警
        function displayAlerts(alerts) {
            const list = document.getElementById('alertsList');
            list.innerHTML = '';

            document.getElementById('alertCount').textContent =
                alerts.filter(a => a.status === 'new').length + ' 新的告警';

            alerts.forEach(alert => {
                const item = document.createElement('div');
                item.className = `alert - item ${alert.severity}`;
                const time = new Date(alert.timestamp).toLocaleString('zh - CN');
                item.innerHTML = `
                    <div class="alert - header">
                        <div class="alert - title">${alert.title}</div>
                        <div class="alert - time">${time}</div>
                    </div>
                    <div class="alert - description">${alert.description}</div>
                    <div class="alert - actions">
                        ${alert.status === 'new' ?
                            '<button class="btn - ack" onclick="acknowledgeAlert(\\'' + alert.alert_id + '\\')">确认</button>' : ''}
                        ${alert.status !== 'resolved' ?
                            '<button class="btn - resolve" onclick="resolveAlert(\\'' + alert.alert_id + '\\')">解决</button>' : ''}
                    </div>
                `;
                list.appendChild(item);
            });
        }

        // 确认告警
        async function acknowledgeAlert(alertId) {
            try {
                const response = await fetch(`/api / alerts/${alertId}/acknowledge`, {
                    method: 'POST'
                });
                if (response.ok) {
                    loadAlerts();
                }
            } catch (error) {
                console.error('Failed to acknowledge alert:', error);
            }
        }

        // 解决告警
        async function resolveAlert(alertId) {
            try {
                const response = await fetch(`/api / alerts/${alertId}/resolve`, {
                    method: 'POST'
                });
                if (response.ok) {
                    loadAlerts();
                }
            } catch (error) {
                console.error('Failed to resolve alert:', error);
            }
        }

        // 初始化图表
        function initChart() {
            const ctx = document.getElementById('metricsChart').getContext('2d');
            metricsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: []
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: '安全指标时间序列'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // 初始化WebSocket
        function initWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            wsConnection = new WebSocket(`${protocol}//${window.location.host}/ws / alerts`);

            wsConnection.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.alert_id) {
                    loadAlerts();
                }
            };
        }
    </script>
</body>
</html>
        """

    def run(self):
        """运行仪表板"""
        self.logger.info(f"Starting Security Dashboard on {self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")


# 便捷函数
def create_security_dashboard(**kwargs) -> SecurityDashboard:
    """创建安全仪表板"""
    return SecurityDashboard(**kwargs)

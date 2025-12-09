"""
港股量化交易 AI Agent 系统 - 性能监控仪表板

实现实时性能监控界面、告警通知功能和系统状态可视化。
提供全面的系统监控和运维管理能力。
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ...core import SystemConfig
from ...core.message_queue import MessageQueue
from ...dashboard.agent_data_service import AgentDataService
from ...dashboard.performance_service import PerformanceService
from ...dashboard.strategy_data_service import StrategyDataService
from ...models.agent_dashboard import (
    AgentDashboardData,
    DashboardAlert,
    DashboardSummary,
    PerformanceMetrics,
    StrategyInfo,
)
from ...models.base import AgentInfo, SystemMetrics


class AlertLevel(str, Enum):
    """告警级别"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """告警状态"""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class DashboardConfig:
    """仪表板配置"""

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # 监控配置
    update_interval: int = 5  # 数据更新间隔（秒）
    max_history_points: int = 1000  # 最大历史数据点数

    # 告警配置
    alert_retention_days: int = 30  # 告警保留天数
    alert_thresholds: Dict[str, Dict[str, float]] = field(
        default_factory=lambda: {
            "cpu_usage": {"warning": 70.0, "critical": 85.0},
            "memory_usage": {"warning": 75.0, "critical": 90.0},
            "queue_length": {"warning": 50, "critical": 100},
            "error_rate": {"warning": 0.05, "critical": 0.10},
            "latency": {"warning": 1000, "critical": 5000},
        }
    )

    # 通知配置
    enable_email_alerts: bool = False
    enable_slack_alerts: bool = False
    email_recipients: List[str] = field(default_factory=list)
    slack_webhook_url: str = ""


@dataclass
class Alert(BaseModel):
    """告警数据模型"""

    alert_id: str
    title: str
    message: str
    level: AlertLevel
    status: AlertStatus
    source: str
    timestamp: datetime
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardData(BaseModel):
    """仪表板数据模型"""

    timestamp: datetime
    system_metrics: SystemMetrics
    agent_statuses: List[AgentInfo]
    active_alerts: List[Alert]
    performance_history: List[Dict[str, Any]]
    alert_history: List[Alert]


class AlertManager:
    """告警管理器"""

    def __init__(self, config: DashboardConfig):
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.dashboard.alert_manager")
        self.alerts: Dict[str, Alert] = {}
        self.alert_callbacks: List[Callable[[Alert], None]] = []

    def create_alert(
        self,
        title: str,
        message: str,
        level: AlertLevel,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Alert:
        """创建告警"""

        alert = Alert(
            id=str(uuid.uuid4()),
            alert_id=str(uuid.uuid4()),
            title=title,
            message=message,
            level=level,
            status=AlertStatus.ACTIVE,
            source=source,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )

        self.alerts[alert.alert_id] = alert

        # 触发告警回调
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as exc:
                self.logger.error(f"告警回调执行失败: {exc}")

        self.logger.warning(f"创建告警: {title} - {message}")
        return alert

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """确认告警"""

        alert = self.alerts.get(alert_id)
        if not alert:
            return False

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now()

        self.logger.info(f"告警已确认: {alert_id} by {acknowledged_by}")
        return True

    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""

        alert = self.alerts.get(alert_id)
        if not alert:
            return False

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now()

        self.logger.info(f"告警已解决: {alert_id}")
        return True

    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return [
            alert
            for alert in self.alerts.values()
            if alert.status == AlertStatus.ACTIVE
        ]

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """获取告警历史"""
        sorted_alerts = sorted(
            self.alerts.values(), key=lambda x: x.timestamp, reverse=True
        )
        return sorted_alerts[:limit]

    def register_alert_callback(self, callback: Callable[[Alert], None]):
        """注册告警回调"""
        self.alert_callbacks.append(callback)

    def check_thresholds(self, metrics: SystemMetrics) -> List[Alert]:
        """检查阈值并生成告警"""

        new_alerts = []

        # 检查CPU使用率
        if (
            metrics.system_cpu_usage
            >= self.config.alert_thresholds["cpu_usage"]["critical"]
        ):
            alert = self.create_alert(
                title="CPU使用率过高",
                message=f"系统CPU使用率已达到 {metrics.system_cpu_usage:.2f}%",
                level=AlertLevel.CRITICAL,
                source="system_monitor",
                metadata={"metric": "cpu_usage", "value": metrics.system_cpu_usage},
            )
            new_alerts.append(alert)
        elif (
            metrics.system_cpu_usage
            >= self.config.alert_thresholds["cpu_usage"]["warning"]
        ):
            alert = self.create_alert(
                title="CPU使用率警告",
                message=f"系统CPU使用率已达到 {metrics.system_cpu_usage:.2f}%",
                level=AlertLevel.WARNING,
                source="system_monitor",
                metadata={"metric": "cpu_usage", "value": metrics.system_cpu_usage},
            )
            new_alerts.append(alert)

        # 检查内存使用率
        if (
            metrics.system_memory_usage
            >= self.config.alert_thresholds["memory_usage"]["critical"]
        ):
            alert = self.create_alert(
                title="内存使用率过高",
                message=f"系统内存使用率已达到 {metrics.system_memory_usage:.2f}%",
                level=AlertLevel.CRITICAL,
                source="system_monitor",
                metadata={
                    "metric": "memory_usage",
                    "value": metrics.system_memory_usage,
                },
            )
            new_alerts.append(alert)
        elif (
            metrics.system_memory_usage
            >= self.config.alert_thresholds["memory_usage"]["warning"]
        ):
            alert = self.create_alert(
                title="内存使用率警告",
                message=f"系统内存使用率已达到 {metrics.system_memory_usage:.2f}%",
                level=AlertLevel.WARNING,
                source="system_monitor",
                metadata={
                    "metric": "memory_usage",
                    "value": metrics.system_memory_usage,
                },
            )
            new_alerts.append(alert)

        # 检查错误率
        if metrics.error_rate >= self.config.alert_thresholds["error_rate"]["critical"]:
            alert = self.create_alert(
                title="错误率过高",
                message=f"系统错误率已达到 {metrics.error_rate:.2%}",
                level=AlertLevel.CRITICAL,
                source="system_monitor",
                metadata={"metric": "error_rate", "value": metrics.error_rate},
            )
            new_alerts.append(alert)
        elif (
            metrics.error_rate >= self.config.alert_thresholds["error_rate"]["warning"]
        ):
            alert = self.create_alert(
                title="错误率警告",
                message=f"系统错误率已达到 {metrics.error_rate:.2%}",
                level=AlertLevel.WARNING,
                source="system_monitor",
                metadata={"metric": "error_rate", "value": metrics.error_rate},
            )
            new_alerts.append(alert)

        return new_alerts


class PerformanceHistory:
    """性能历史数据管理器"""

    def __init__(self, config: DashboardConfig):
        self.config = config
        self.history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger("hk_quant_system.dashboard.performance_history")

    def add_metrics(self, metrics: SystemMetrics, agent_statuses: List[AgentInfo]):
        """添加性能指标"""

        history_point = {
            "timestamp": datetime.now(),
            "cpu_usage": metrics.system_cpu_usage,
            "memory_usage": metrics.system_memory_usage,
            "redis_memory_usage": metrics.redis_memory_usage,
            "active_agents": metrics.active_agents,
            "total_messages": metrics.total_messages_processed,
            "error_rate": metrics.error_rate,
            "throughput": metrics.throughput,
            "latency_p95": metrics.latency_p95,
            "latency_p99": metrics.latency_p99,
            "agent_details": [
                {
                    "agent_id": agent.agent_id,
                    "status": agent.status.value,
                    "cpu_usage": agent.cpu_usage,
                    "memory_usage": agent.memory_usage,
                    "messages_processed": agent.messages_processed,
                    "error_count": agent.error_count,
                }
                for agent in agent_statuses
            ],
        }

        self.history.append(history_point)

        # 限制历史数据大小
        if len(self.history) > self.config.max_history_points:
            self.history = self.history[-self.config.max_history_points :]

    def get_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取历史数据"""

        cutoff_time = datetime.now() - timedelta(hours=hours)

        return [point for point in self.history if point["timestamp"] >= cutoff_time]

    def get_summary_stats(self) -> Dict[str, Any]:
        """获取汇总统计"""

        if not self.history:
            return {}

        recent_data = self.history[-100:]  # 最近100个数据点

        return {
            "avg_cpu_usage": sum(point["cpu_usage"] for point in recent_data)
            / len(recent_data),
            "avg_memory_usage": sum(point["memory_usage"] for point in recent_data)
            / len(recent_data),
            "max_cpu_usage": max(point["cpu_usage"] for point in recent_data),
            "max_memory_usage": max(point["memory_usage"] for point in recent_data),
            "avg_error_rate": sum(point["error_rate"] for point in recent_data)
            / len(recent_data),
            "avg_throughput": sum(point["throughput"] for point in recent_data)
            / len(recent_data),
            "data_points": len(recent_data),
        }


class MonitoringDashboard:
    """性能监控仪表板主类"""

    def __init__(
        self, config: DashboardConfig, message_queue: MessageQueue, coordinator=None
    ):
        self.config = config
        self.message_queue = message_queue
        self.coordinator = coordinator
        self.logger = logging.getLogger("hk_quant_system.dashboard")

        # 初始化组件
        self.alert_manager = AlertManager(config)
        self.performance_history = PerformanceHistory(config)

        # 初始化Agent仪表板服务
        if coordinator:
            self.agent_data_service = AgentDataService(coordinator, message_queue)
            self.strategy_data_service = StrategyDataService(coordinator, message_queue)
            self.performance_service = PerformanceService(coordinator, message_queue)
            self._agent_services_initialized = False
        else:
            self.agent_data_service = None
            self.strategy_data_service = None
            self.performance_service = None
            self._agent_services_initialized = True

        # WebSocket连接管理
        self.active_connections: List[WebSocket] = []

        # 创建FastAPI应用
        self.app = FastAPI(title="港股量化交易系统监控仪表板", version="1.0.0")
        self._setup_routes()

        # 启动后台任务
        self.running = False
        self.update_task: Optional[asyncio.Task] = None

    def _setup_routes(self):
        """设置路由"""

        @self.app.get("/")
        async def dashboard():
            """仪表板主页"""
            return HTMLResponse(content=self._get_dashboard_html())

        @self.app.get("/api / metrics")
        async def get_metrics():
            """获取当前指标"""
            return await self._get_current_metrics()

        @self.app.get("/api / alerts")
        async def get_alerts():
            """获取告警列表"""
            return {
                "active_alerts": self.alert_manager.get_active_alerts(),
                "alert_history": self.alert_manager.get_alert_history(),
            }

        @self.app.post("/api / alerts/{alert_id}/acknowledge")
        async def acknowledge_alert(alert_id: str, data: Dict[str, str]):
            """确认告警"""
            acknowledged_by = data.get("acknowledged_by", "unknown")
            success = self.alert_manager.acknowledge_alert(alert_id, acknowledged_by)
            if success:
                return {"status": "success", "message": "告警已确认"}
            else:
                raise HTTPException(status_code=404, detail="告警不存在")

        @self.app.post("/api / alerts/{alert_id}/resolve")
        async def resolve_alert(alert_id: str):
            """解决告警"""
            success = self.alert_manager.resolve_alert(alert_id)
            if success:
                return {"status": "success", "message": "告警已解决"}
            else:
                raise HTTPException(status_code=404, detail="告警不存在")

        @self.app.get("/api / history")
        async def get_history(hours: int = 24):
            """获取历史数据"""
            return self.performance_history.get_history(hours)

        @self.app.get("/api / stats")
        async def get_stats():
            """获取汇总统计"""
            return self.performance_history.get_summary_stats()

        # Agent仪表板相关路由
        @self.app.get("/api / agents")
        async def get_agents():
            """获取所有Agent数据"""
            if not self._agent_services_initialized:
                return {"error": "Agent services not initialized"}

            try:
                agents_data = await self.agent_data_service.get_all_agents_data()
                return {"agents": agents_data}
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to get agents data: {str(e)}"
                )

        @self.app.get("/api / agents/{agent_id}")
        async def get_agent(agent_id: str):
            """获取指定Agent数据"""
            if not self._agent_services_initialized:
                return {"error": "Agent services not initialized"}

            try:
                agent_data = await self.agent_data_service.get_agent_data(agent_id)
                if not agent_data:
                    raise HTTPException(
                        status_code=404, detail=f"Agent {agent_id} not found"
                    )
                return {"agent": agent_data}
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to get agent data: {str(e)}"
                )

        @self.app.get("/api / agents/{agent_id}/strategy")
        async def get_agent_strategy(agent_id: str):
            """获取Agent策略信息"""
            if not self._agent_services_initialized:
                return {"error": "Agent services not initialized"}

            try:
                strategy_info = await self.strategy_data_service.get_agent_strategy(
                    agent_id
                )
                if not strategy_info:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Strategy for agent {agent_id} not found",
                    )
                return {"strategy": strategy_info}
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to get strategy data: {str(e)}"
                )

        @self.app.get("/api / agents/{agent_id}/performance")
        async def get_agent_performance(agent_id: str):
            """获取Agent绩效指标"""
            if not self._agent_services_initialized:
                return {"error": "Agent services not initialized"}

            try:
                performance = await self.performance_service.get_agent_performance(
                    agent_id
                )
                if not performance:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Performance data for agent {agent_id} not found",
                    )
                return {"performance": performance}
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to get performance data: {str(e)}"
                )

        @self.app.get("/api / dashboard / summary")
        async def get_dashboard_summary():
            """获取仪表板总览"""
            if not self._agent_services_initialized:
                return {"error": "Agent services not initialized"}

            try:
                summary = await self.agent_data_service.get_dashboard_summary()
                return {"summary": summary}
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to get dashboard summary: {str(e)}"
                )

        @self.app.get("/api / strategies")
        async def get_all_strategies():
            """获取所有策略信息"""
            if not self._agent_services_initialized:
                return {"error": "Agent services not initialized"}

            try:
                strategies = await self.strategy_data_service.get_all_strategies()
                return {"strategies": strategies}
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to get strategies data: {str(e)}"
                )

        @self.app.get("/api / performance")
        async def get_all_performance():
            """获取所有绩效指标"""
            if not self._agent_services_initialized:
                return {"error": "Agent services not initialized"}

            try:
                performance_data = await self.performance_service.get_all_performance()
                return {"performance": performance_data}
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to get performance data: {str(e)}"
                )

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket连接"""
            await websocket.accept()
            self.active_connections.append(websocket)

            try:
                while True:
                    # 保持连接活跃
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)

    def _get_dashboard_html(self) -> str:
        """获取仪表板HTML"""

        return """
<!DOCTYPE html>
<html>
<head>
    <title>港股量化交易系统监控仪表板</title>
    <meta charset="utf - 8">
    <meta name="viewport" content="width=device - width, initial - scale=1">
    <style>
        body { font - family: Arial, sans - serif; margin: 0; padding: 20px; background - color: #f5f5f5; }
        .container { max - width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border - radius: 5px; margin - bottom: 20px; }
        .metrics - grid { display: grid; grid - template - columns: repeat(auto - fit, minmax(250px, 1fr)); gap: 20px; margin - bottom: 20px; }
        .metric - card { background: white; padding: 20px; border - radius: 5px; box - shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric - value { font - size: 2em; font - weight: bold; margin: 10px 0; }
        .metric - label { color: #666; font - size: 0.9em; }
        .alert - panel { background: white; padding: 20px; border - radius: 5px; box - shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .alert - item { padding: 10px; margin: 10px 0; border - left: 4px solid #ddd; border - radius: 3px; }
        .alert - critical { border - left - color: #e74c3c; background: #fdf2f2; }
        .alert - warning { border - left - color: #f39c12; background: #fef9e7; }
        .alert - info { border - left - color: #3498db; background: #f0f8ff; }
        .chart - container { background: white; padding: 20px; border - radius: 5px; box - shadow: 0 2px 4px rgba(0,0,0,0.1); margin - bottom: 20px; }
        .status - indicator { display: inline - block; width: 12px; height: 12px; border - radius: 50%; margin - right: 8px; }
        .status - healthy { background: #27ae60; }
        .status - warning { background: #f39c12; }
        .status - error { background: #e74c3c; }
        button { padding: 8px 16px; margin: 5px; border: none; border - radius: 3px; cursor: pointer; }
        .btn - primary { background: #3498db; color: white; }
        .btn - success { background: #27ae60; color: white; }
        .btn - danger { background: #e74c3c; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>港股量化交易系统监控仪表板</h1>
            <p>实时系统状态和性能监控</p>
        </div>

        <div class="metrics - grid" id="metricsGrid">
            <!-- 指标卡片将通过JavaScript动态生成 -->
        </div>

        <div class="chart - container">
            <h3>系统性能趋势</h3>
            <canvas id="performanceChart" width="800" height="400"></canvas>
        </div>

        <div class="alert - panel">
            <h3>活跃告警</h3>
            <div id="alertsContainer">
                <!-- 告警将通过JavaScript动态生成 -->
            </div>
        </div>
    </div>

    <script>
        // WebSocket连接
        const ws = new WebSocket(`ws://${window.location.host}/ws`);

        // 定期更新数据
        setInterval(updateDashboard, 5000);

        async function updateDashboard() {
            try {
                const response = await fetch('/api / metrics');
                const data = await response.json();
                updateMetricsDisplay(data);
            } catch (error) {
                console.error('更新数据失败:', error);
            }
        }

        async function updateAlerts() {
            try {
                const response = await fetch('/api / alerts');
                const data = await response.json();
                updateAlertsDisplay(data.active_alerts);
            } catch (error) {
                console.error('更新告警失败:', error);
            }
        }

        function updateMetricsDisplay(data) {
            const grid = document.getElementById('metricsGrid');
            grid.innerHTML = `
                <div class="metric - card">
                    <div class="metric - label">CPU使用率</div>
                    <div class="metric - value">${data.system_metrics.system_cpu_usage.toFixed(1)}%</div>
                </div>
                <div class="metric - card">
                    <div class="metric - label">内存使用率</div>
                    <div class="metric - value">${data.system_metrics.system_memory_usage.toFixed(1)}%</div>
                </div>
                <div class="metric - card">
                    <div class="metric - label">活跃Agent</div>
                    <div class="metric - value">${data.system_metrics.active_agents}</div>
                </div>
                <div class="metric - card">
                    <div class="metric - label">错误率</div>
                    <div class="metric - value">${(data.system_metrics.error_rate * 100).toFixed(2)}%</div>
                </div>
                <div class="metric - card">
                    <div class="metric - label">吞吐量</div>
                    <div class="metric - value">${data.system_metrics.throughput.toFixed(0)} msg / s</div>
                </div>
                <div class="metric - card">
                    <div class="metric - label">延迟(P95)</div>
                    <div class="metric - value">${data.system_metrics.latency_p95.toFixed(0)} ms</div>
                </div>
            `;
        }

        function updateAlertsDisplay(alerts) {
            const container = document.getElementById('alertsContainer');
            if (alerts.length === 0) {
                container.innerHTML = '<p>暂无活跃告警</p>';
                return;
            }

            container.innerHTML = alerts.map(alert => `
                <div class="alert - item alert-${alert.level}">
                    <div style="display: flex; justify - content: space - between; align - items: center;">
                        <div>
                            <strong>${alert.title}</strong>
                            <p>${alert.message}</p>
                            <small>来源: ${alert.source} | 时间: ${new Date(alert.timestamp).toLocaleString()}</small>
                        </div>
                        <div>
                            <button class="btn - primary" onclick="acknowledgeAlert('${alert.alert_id}')">确认</button>
                            <button class="btn - success" onclick="resolveAlert('${alert.alert_id}')">解决</button>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        async function acknowledgeAlert(alertId) {
            try {
                await fetch(`/api / alerts/${alertId}/acknowledge`, {
                    method: 'POST',
                    headers: {'Content - Type': 'application / json'},
                    body: JSON.stringify({acknowledged_by: 'dashboard_user'})
                });
                updateAlerts();
            } catch (error) {
                console.error('确认告警失败:', error);
            }
        }

        async function resolveAlert(alertId) {
            try {
                await fetch(`/api / alerts/${alertId}/resolve`, {method: 'POST'});
                updateAlerts();
            } catch (error) {
                console.error('解决告警失败:', error);
            }
        }

        // 初始化
        updateDashboard();
        updateAlerts();
        setInterval(updateAlerts, 10000);
    </script>
</body>
</html>
        """

    async def _get_current_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""

        try:
            # 获取系统指标
            system_metrics = await self._collect_system_metrics()

            # 获取Agent状态
            agent_statuses = await self._collect_agent_statuses()

            # 检查阈值并生成告警
            self.alert_manager.check_thresholds(system_metrics)

            # 添加到历史数据
            self.performance_history.add_metrics(system_metrics, agent_statuses)

            return {
                "system_metrics": system_metrics.dict(),
                "agent_statuses": [agent.dict() for agent in agent_statuses],
                "timestamp": datetime.now(),
            }

        except Exception as exc:
            self.logger.error(f"获取当前指标失败: {exc}")
            return {
                "system_metrics": {},
                "agent_statuses": [],
                "timestamp": datetime.now(),
            }

    async def _collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""

        # 这里应该从实际系统收集指标
        # 暂时返回模拟数据
        return SystemMetrics(
            id=f"metrics_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            active_agents=7,
            total_messages_processed=10000,
            system_cpu_usage=45.2,
            system_memory_usage=67.8,
            redis_memory_usage=23.4,
            queue_lengths={"main": 5},
            error_rate=0.02,
            throughput=150.5,
            latency_p95=120.3,
            latency_p99=250.7,
        )

    async def _collect_agent_statuses(self) -> List[AgentInfo]:
        """收集Agent状态"""

        # 这里应该从实际系统收集Agent状态
        # 暂时返回模拟数据
        return [
            AgentInfo(
                id=f"agent_{i}",
                agent_id=f"agent_{i}",
                agent_type="quantitative_analyst",
                status="running",
                last_heartbeat=datetime.now(),
                cpu_usage=20.0 + i * 5,
                memory_usage=30.0 + i * 3,
                messages_processed=1000 + i * 100,
                error_count=i,
                uptime=3600 + i * 100,
                version="1.0.0",
                configuration={},
            )
            for i in range(7)
        ]

    async def broadcast_update(self, data: Dict[str, Any]):
        """广播更新到所有WebSocket连接"""

        if not self.active_connections:
            return

        message = json.dumps(data, default=str)

        # 发送到所有活跃连接
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)

        # 移除断开的连接
        for connection in disconnected:
            self.active_connections.remove(connection)

    async def initialize_agent_services(self):
        """初始化Agent服务"""
        try:
            if self.agent_data_service and not self._agent_services_initialized:
                self.logger.info("正在初始化Agent仪表板服务...")

                await self.agent_data_service.initialize()
                await self.strategy_data_service.initialize()
                await self.performance_service.initialize()

                self._agent_services_initialized = True
                self.logger.info("Agent仪表板服务初始化完成")

        except Exception as e:
            self.logger.error(f"初始化Agent服务失败: {e}")
            raise

    async def start(self):
        """启动仪表板"""

        if self.running:
            return

        # 初始化Agent服务
        await self.initialize_agent_services()

        self.running = True

        # 启动后台更新任务
        self.update_task = asyncio.create_task(self._update_loop())

        # 启动Web服务器
        config = uvicorn.Config(
            app=self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="info" if not self.config.debug else "debug",
        )
        server = uvicorn.Server(config)

        self.logger.info(
            f"监控仪表板启动: http://{self.config.host}:{self.config.port}"
        )
        await server.serve()

    async def stop(self):
        """停止仪表板"""

        self.running = False

        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass

        # 关闭所有WebSocket连接
        for connection in self.active_connections:
            try:
                await connection.close()
            except Exception:
                pass

        # 清理Agent服务
        await self.cleanup_agent_services()

        self.logger.info("监控仪表板已停止")

    async def cleanup_agent_services(self):
        """清理Agent服务"""
        try:
            if self.agent_data_service:
                await self.agent_data_service.cleanup()
            if self.strategy_data_service:
                await self.strategy_data_service.cleanup()
            if self.performance_service:
                await self.performance_service.cleanup()

            self.logger.info("Agent服务清理完成")

        except Exception as e:
            self.logger.error(f"清理Agent服务失败: {e}")

    async def _update_loop(self):
        """更新循环"""

        while self.running:
            try:
                # 获取最新数据
                data = await self._get_current_metrics()

                # 广播更新
                await self.broadcast_update(data)

                # 等待下次更新
                await asyncio.sleep(self.config.update_interval)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.logger.error(f"更新循环错误: {exc}")
                await asyncio.sleep(5)


__all__ = [
    "MonitoringDashboard",
    "DashboardConfig",
    "AlertManager",
    "PerformanceHistory",
    "Alert",
    "DashboardData",
    "AlertLevel",
    "AlertStatus",
]

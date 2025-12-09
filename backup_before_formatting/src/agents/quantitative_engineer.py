"""
港股量化交易 AI Agent 系统 - 量化工程师Agent

负责系统监控、性能优化、自动部署和故障恢复。
确保整个Agent集群的稳定性和高可用性。
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import psutil

from ..core import SystemConfig
from ..core.message_queue import Message, MessageQueue
from ..models.base import BaseModel, MessageType, SystemMetrics
from .base_agent import AgentConfig, BaseAgent
from .protocol import AgentProtocol, MessagePriority


class SystemHealthStatus(str, Enum):
    """系统健康状态"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"


@dataclass
class MonitoringConfig:
    """监控配置"""

    metrics_interval: int = 10
    health_check_interval: int = 30
    deployment_path: str = "deployments"
    auto_scaling_enabled: bool = True
    max_cpu_usage: float = 85.0
    max_memory_usage: float = 80.0
    max_queue_length: int = 100


@dataclass
class DeploymentRecord(BaseModel):
    """部署记录"""

    deployment_id: str
    version: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    logs: List[str] = field(default_factory=list)


@dataclass
class IncidentRecord(BaseModel):
    """故障记录"""

    incident_id: str
    incident_type: str
    severity: str
    description: str
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_actions: List[str] = field(default_factory=list)


class QuantitativeEngineerProtocol(AgentProtocol):
    """量化工程师协议"""

    def __init__(
        self,
        agent_id: str,
        message_queue: MessageQueue,
        engineer_agent: "QuantitativeEngineerAgent",
    ):
        super().__init__(agent_id, message_queue)
        self.engineer_agent = engineer_agent

    async def _process_control_command(
        self, command: str, parameters: Dict[str, Any], sender_id: str
    ):
        if command == "collect_metrics":
            await self.engineer_agent.collect_system_metrics()
        elif command == "run_health_check":
            await self.engineer_agent.perform_health_check()
        elif command == "trigger_deployment":
            version = parameters.get("version", "latest")
            await self.engineer_agent.trigger_deployment(sender_id, version)
        elif command == "restart_agent":
            target_agent = parameters.get("target_agent")
            await self.engineer_agent.restart_agent(target_agent)
        else:
            self.logger.warning("未知控制命令: %s", command)


class DeploymentManager:
    """部署管理器"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.quant_engineer.deployment")
        os.makedirs(self.config.deployment_path, exist_ok=True)
        self.deployments: Dict[str, DeploymentRecord] = {}

    async def deploy_version(self, version: str) -> DeploymentRecord:
        deployment_id = f"deploy_{version}_{int(time.time())}"
        record = DeploymentRecord(
            id=deployment_id,
            deployment_id=deployment_id,
            version=version,
            status="in_progress",
            start_time=datetime.now(),
            logs=[f"开始部署版本 {version}"],
        )
        self.deployments[deployment_id] = record

        try:
            await asyncio.sleep(2)
            record.logs.append("执行部署脚本...")
            await asyncio.sleep(2)
            record.logs.append("验证服务状态...")
            await asyncio.sleep(1)
            record.status = "success"
            record.logs.append("部署成功")
        except Exception as exc:
            record.status = "failed"
            record.logs.append(f"部署失败: {exc}")
            raise
        finally:
            record.end_time = datetime.now()
            self.logger.info("部署完成: %s 状态: %s", deployment_id, record.status)

        return record

    def get_deployment_history(self, limit: int = 10) -> List[DeploymentRecord]:
        return list(self.deployments.values())[-limit:]


class IncidentManager:
    """故障管理器"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.quant_engineer.incident")
        self.incidents: Dict[str, IncidentRecord] = {}

    def log_incident(
        self, incident_type: str, severity: str, description: str
    ) -> IncidentRecord:
        incident_id = f"incident_{int(time.time())}"
        record = IncidentRecord(
            id=incident_id,
            incident_id=incident_id,
            incident_type=incident_type,
            severity=severity,
            description=description,
            detected_at=datetime.now(),
        )
        self.incidents[incident_id] = record
        self.logger.warning("记录故障: %s - %s", incident_type, description)
        return record

    def resolve_incident(
        self, incident_id: str, actions: List[str]
    ) -> Optional[IncidentRecord]:
        record = self.incidents.get(incident_id)
        if not record:
            return None
        record.resolved_at = datetime.now()
        record.resolution_actions.extend(actions)
        self.logger.info("故障已解决: %s", incident_id)
        return record

    def get_active_incidents(self) -> List[IncidentRecord]:
        return [
            incident
            for incident in self.incidents.values()
            if incident.resolved_at is None
        ]


class SystemMonitor:
    """系统监控器"""

    def __init__(self, config: MonitoringConfig, message_queue: MessageQueue):
        self.config = config
        self.message_queue = message_queue
        self.logger = logging.getLogger("hk_quant_system.quant_engineer.monitor")

    async def collect_metrics(self) -> SystemMetrics:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent
        redis_stats = await self.message_queue.get_system_stats()

        metrics = SystemMetrics(
            id=f"metrics_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            active_agents=redis_stats.get("active_subscribers", 0),
            total_messages_processed=redis_stats.get("registered_handlers", 0),
            system_cpu_usage=cpu_usage,
            system_memory_usage=memory_usage,
            redis_memory_usage=redis_stats.get("redis_info", {}).get("used_memory", 0)
            / max(redis_stats.get("redis_info", {}).get("maxmemory", 1), 1)
            * 100,
            queue_lengths={"main": redis_stats.get("active_subscribers", 0)},
            error_rate=0.0,
            throughput=0.0,
            latency_p95=0.0,
            latency_p99=0.0,
        )
        return metrics

    async def check_system_health(self, metrics: SystemMetrics) -> SystemHealthStatus:
        if (
            metrics.system_cpu_usage > self.config.max_cpu_usage
            or metrics.system_memory_usage > self.config.max_memory_usage
        ):
            self.logger.warning(
                "系统资源使用率过高: CPU %.2f%%, Memory %.2f%%",
                metrics.system_cpu_usage,
                metrics.system_memory_usage,
            )
            return SystemHealthStatus.CRITICAL
        if metrics.redis_memory_usage > self.config.max_memory_usage:
            self.logger.warning(
                "Redis内存使用率过高: %.2f%%",
                metrics.redis_memory_usage,
            )
            return SystemHealthStatus.DEGRADED
        return SystemHealthStatus.HEALTHY


class QuantitativeEngineerAgent(BaseAgent):
    """量化工程师Agent"""

    def __init__(
        self,
        config: AgentConfig,
        message_queue: MessageQueue,
        system_config: SystemConfig = None,
    ):
        super().__init__(config, message_queue, system_config)
        self.monitoring_config = MonitoringConfig()
        self.monitor = SystemMonitor(self.monitoring_config, message_queue)
        self.deployment_manager = DeploymentManager(self.monitoring_config)
        self.incident_manager = IncidentManager()
        self.protocol = QuantitativeEngineerProtocol(
            config.agent_id, message_queue, self
        )
        self.metrics_history: List[SystemMetrics] = []
        self.health_status = SystemHealthStatus.HEALTHY
        self.running_tasks: List[asyncio.Task] = []

    async def initialize(self) -> bool:
        await self.protocol.initialize()
        await self._start_background_tasks()
        self.logger.info("量化工程师Agent初始化完成: %s", self.config.agent_id)
        return True

    async def process_message(self, message: Message) -> bool:
        try:
            await self.protocol.handle_incoming_message(message)
            return True
        except Exception as exc:
            self.logger.error("处理消息失败: %s", exc)
            return False

    async def cleanup(self):
        for task in self.running_tasks:
            if not task.done():
                task.cancel()
        self.logger.info("量化工程师Agent清理完成")

    async def _start_background_tasks(self):
        metrics_task = asyncio.create_task(self._metrics_loop())
        health_task = asyncio.create_task(self._health_check_loop())
        self.running_tasks.extend([metrics_task, health_task])

    async def _metrics_loop(self):
        while self.running:
            try:
                await self.collect_system_metrics()
                await asyncio.sleep(self.monitoring_config.metrics_interval)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.logger.error("收集系统指标失败: %s", exc)
                await asyncio.sleep(5)

    async def _health_check_loop(self):
        while self.running:
            try:
                await self.perform_health_check()
                await asyncio.sleep(self.monitoring_config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.logger.error("执行健康检查失败: %s", exc)
                await asyncio.sleep(5)

    async def collect_system_metrics(self):
        metrics = await self.monitor.collect_metrics()
        self.metrics_history.append(metrics)
        await self.protocol.broadcast_message(
            message_type=MessageType.DATA,
            payload={"data_type": "system_metrics", "metrics": metrics.dict()},
            priority=MessagePriority.NORMAL,
        )
        self.logger.info(
            "系统指标已广播: CPU %.2f%%, Memory %.2f%%",
            metrics.system_cpu_usage,
            metrics.system_memory_usage,
        )

    async def perform_health_check(self):
        if not self.metrics_history:
            return
        latest_metrics = self.metrics_history[-1]
        self.health_status = await self.monitor.check_system_health(latest_metrics)
        if self.health_status != SystemHealthStatus.HEALTHY:
            incident = self.incident_manager.log_incident(
                incident_type="system_health",
                severity=self.health_status.value,
                description=f"系统健康状态为 {self.health_status.value}",
            )
            await self.protocol.broadcast_message(
                message_type=MessageType.CONTROL,
                payload={
                    "command": "system_health_alert",
                    "parameters": {
                        "status": self.health_status.value,
                        "incident_id": incident.incident_id,
                    },
                },
                priority=MessagePriority.URGENT,
            )

    async def trigger_deployment(self, requester_id: str, version: str):
        record = await self.deployment_manager.deploy_version(version)
        await self.protocol.send_message(
            message_type=MessageType.DATA,
            payload={"data_type": "deployment_record", "record": record.dict()},
            receiver_id=requester_id,
        )

    async def restart_agent(self, target_agent: Optional[str]):
        if not target_agent:
            self.logger.warning("未指定重启的Agent")
            return
        await self.protocol.send_control(
            command="restart",
            parameters={},
            target_agent=target_agent,
        )
        self.logger.info("已发送重启命令给Agent: %s", target_agent)

    def get_agent_summary(self) -> Dict[str, Any]:
        return {
            "agent_id": self.config.agent_id,
            "health_status": self.health_status.value,
            "metrics_history_size": len(self.metrics_history),
            "active_incidents": len(self.incident_manager.get_active_incidents()),
            "protocol_stats": self.protocol.get_protocol_stats(),
        }


__all__ = [
    "QuantitativeEngineerAgent",
    "QuantitativeEngineerProtocol",
    "MonitoringConfig",
    "DeploymentManager",
    "IncidentManager",
    "SystemMonitor",
    "DeploymentRecord",
    "IncidentRecord",
]

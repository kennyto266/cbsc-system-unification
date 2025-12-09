"""
Enhanced Base Agent Implementation
增強版基礎智能體實現

這是一個與新架構兼容的基礎智能體系統，包含完整的消息處理、
性能監控和錯誤處理機制。
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from ..core.logging import get_logger, log_performance
from ..core.exceptions import AgentError, AgentConfigurationError


@dataclass
class AgentStatus(Enum):
    """Agent status enumeration."""
    IDLE = "idle"
    BUSY = "busy"
    RUNNING = "running"
    ERROR = "error"
    DISABLED = "disabled"
    INITIALIZING = "initializing"
    STOPPED = "stopped"


@dataclass
class AgentCapability:
    """Agent capability description."""
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    parameters: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class AgentMessage:
    """Agent message data structure."""
    message_id: str
    sender: str
    receiver: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    priority: int = 1  # 1=low, 5=high
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConfig:
    """Agent configuration."""

    agent_id: str
    agent_type: str
    config: Dict[str, Any] = field(default_factory=dict)
    heartbeat_interval: int = 30
    max_errors: int = 10
    restart_delay: int = 5
    max_concurrent_tasks: int = 10
    timeout_seconds: int = 30
    retry_attempts: int = 3
    enable_caching: bool = True
    cache_ttl: int = 300


class BaseAgent(ABC):
    """基础Agent类"""

    def __init__(
        self,
        config: AgentConfig,
        message_queue: MessageQueue,
        system_config: SystemConfig = None,
    ):
        self.config = config
        self.message_queue = message_queue
        self.system_config = system_config or SystemConfig()
        self.logger = logging.getLogger(f"hk_quant_system.agent.{config.agent_id}")

        # Agent状态
        self.status = AgentStatus.IDLE
        self.start_time: Optional[datetime] = None
        self.error_count = 0
        self.messages_processed = 0

        # 任务管理
        self.tasks: List[asyncio.Task] = []
        self.running = False

        # 统计信息
        self.cpu_usage = 0.0
        self.memory_usage = 0.0

    @abstractmethod
    async def initialize(self) -> bool:
        """初始化Agent"""
        pass

    @abstractmethod
    async def process_message(self, message: Message) -> bool:
        """处理消息"""
        pass

    @abstractmethod
    async def cleanup(self):
        """清理资源"""
        pass

    async def start(self) -> bool:
        """启动Agent"""
        try:
            self.logger.info(f"启动Agent: {self.config.agent_id}")

            # 初始化Agent
            if not await self.initialize():
                self.logger.error(f"Agent初始化失败: {self.config.agent_id}")
                return False

            self.status = AgentStatus.RUNNING
            self.start_time = datetime.now()
            self.running = True

            # 启动心跳任务
            heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self.tasks.append(heartbeat_task)

            # 启动消息处理任务
            message_task = asyncio.create_task(self._message_processing_loop())
            self.tasks.append(message_task)

            self.logger.info(f"Agent启动成功: {self.config.agent_id}")
            return True

        except Exception as e:
            self.logger.error(f"Agent启动失败: {self.config.agent_id}, 错误: {e}")
            self.status = AgentStatus.ERROR
            return False

    async def stop(self):
        """停止Agent"""
        self.logger.info(f"停止Agent: {self.config.agent_id}")
        self.running = False
        self.status = AgentStatus.STOPPED

        # 取消所有任务
        for task in self.tasks:
            if not task.done():
                task.cancel()

        # 等待任务完成
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)

        # 清理资源
        await self.cleanup()

        self.logger.info(f"Agent已停止: {self.config.agent_id}")

    async def restart(self):
        """重启Agent"""
        self.logger.info(f"重启Agent: {self.config.agent_id}")
        await self.stop()
        await asyncio.sleep(self.config.restart_delay)
        await self.start()

    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            try:
                await self.message_queue.send_heartbeat(
                    agent_id=self.config.agent_id, status=self.status.value
                )
                await asyncio.sleep(self.config.heartbeat_interval)
            except Exception as e:
                self.logger.error(f"发送心跳失败: {e}")
                await asyncio.sleep(5)

    async def _message_processing_loop(self):
        """消息处理循环"""
        while self.running:
            try:
                # 接收消息
                message = await self.message_queue.receive_message(
                    agent_id=self.config.agent_id, timeout=1.0
                )

                if message:
                    success = await self.process_message(message)
                    self.messages_processed += 1

                    if not success:
                        self.error_count += 1
                        self.logger.warning(f"消息处理失败: {message.id}")

                        # 错误次数过多时重启
                        if self.error_count >= self.config.max_errors:
                            self.logger.error(
                                f"错误次数过多，重启Agent: {self.config.agent_id}"
                            )
                            await self.restart()
                            return

            except asyncio.TimeoutError:
                # 超时是正常的，继续循环
                continue
            except Exception as e:
                self.logger.error(f"消息处理循环异常: {e}")
                self.error_count += 1
                await asyncio.sleep(1)

    def get_agent_info(self) -> AgentInfo:
        """获取Agent信息"""
        uptime = 0.0
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()

        return AgentInfo(
            agent_id=self.config.agent_id,
            agent_type=self.config.agent_type,
            status=self.status,
            last_heartbeat=datetime.now(),
            cpu_usage=self.cpu_usage,
            memory_usage=self.memory_usage,
            messages_processed=self.messages_processed,
            error_count=self.error_count,
            uptime=uptime,
            version="1.0.0",
            configuration=self.config.config,
        )

    async def send_control_message(
        self, target_agent: str, command: str, parameters: Dict[str, Any] = None
    ):
        """发送控制消息"""
        await self.message_queue.send_control_message(
            command=command,
            target_agent=target_agent,
            parameters=parameters or {},
            sender=self.config.agent_id,
        )

    async def broadcast_message(self, message_type: str, content: Dict[str, Any]):
        """广播消息"""
        await self.message_queue.publish_message(
            message_type=message_type, content=content, sender=self.config.agent_id
        )

    def update_status(self, status: AgentStatus):
        """更新Agent状态"""
        old_status = self.status
        self.status = status
        self.logger.info(f"Agent状态变更: {old_status.value} -> {status.value}")

    def reset_error_count(self):
        """重置错误计数"""
        self.error_count = 0
        self.logger.info("错误计数已重置")

    def is_healthy(self) -> bool:
        """检查Agent健康状态"""
        return (
            self.status == AgentStatus.RUNNING
            and self.error_count < self.config.max_errors
            and self.running
        )

"""
港股量化交易 AI Agent 系统协调器

负责管理所有Agent的生命周期、注册发现、健康监控和协调通信。
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Type

from ..core import SystemConfig, SystemConstants
from ..core.message_queue import Message, MessageQueue
from ..models.base import AgentInfo, AgentStatus, SystemMetrics
from .base_agent import AgentConfig, BaseAgent


@dataclass
class AgentRegistry:
    """Agent注册信息"""

    agent: BaseAgent
    config: AgentConfig
    registered_at: datetime
    last_heartbeat: datetime
    health_check_count: int = 0


class AgentCoordinator:
    """Agent协调器"""

    def __init__(self, config: SystemConfig = None):
        self.config = config or SystemConfig()
        self.logger = logging.getLogger("hk_quant_system.coordinator")

        # Agent注册表
        self.agent_registry: Dict[str, AgentRegistry] = {}
        self.agent_types: Dict[str, Type[BaseAgent]] = {}

        # 消息队列
        self.message_queue = MessageQueue(self.config)

        # 协调器状态
        self.running = False
        self.tasks: List[asyncio.Task] = []

        # 统计信息
        self.total_messages_processed = 0
        self.system_start_time = datetime.now()

    async def initialize(self):
        """初始化协调器"""
        try:
            # 初始化消息队列
            await self.message_queue.initialize()

            # 订阅控制消息
            await self.message_queue.subscribe_to_channel(
                channel_name=SystemConstants.MESSAGE_TYPES["CONTROL"],
                agent_id="coordinator",
                handler=self._handle_control_message,
            )

            self.logger.info("Agent协调器初始化成功")
            return True

        except Exception as e:
            self.logger.error(f"Agent协调器初始化失败: {e}")
            return False

    async def start(self):
        """启动协调器"""
        if not await self.initialize():
            raise RuntimeError("协调器初始化失败")

        self.running = True
        self.logger.info("启动Agent协调器")

        # 启动健康监控任务
        health_task = asyncio.create_task(self._health_monitoring_loop())
        self.tasks.append(health_task)

        # 启动统计收集任务
        stats_task = asyncio.create_task(self._stats_collection_loop())
        self.tasks.append(stats_task)

        # 启动系统监控任务
        monitor_task = asyncio.create_task(self._system_monitoring_loop())
        self.tasks.append(monitor_task)

        self.logger.info("Agent协调器启动成功")

    async def stop(self):
        """停止协调器"""
        self.logger.info("停止Agent协调器")
        self.running = False

        # 停止所有Agent
        for registry in self.agent_registry.values():
            await registry.agent.stop()

        # 取消所有任务
        for task in self.tasks:
            if not task.done():
                task.cancel()

        # 等待任务完成
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)

        # 关闭消息队列
        await self.message_queue.close()

        self.logger.info("Agent协调器已停止")

    def register_agent_type(self, agent_type: str, agent_class: Type[BaseAgent]):
        """注册Agent类型"""
        self.agent_types[agent_type] = agent_class
        self.logger.info(f"注册Agent类型: {agent_type}")

    async def start_agent(
        self, agent_type: str, agent_id: str, config: Dict[str, Any] = None
    ) -> bool:
        """启动指定类型的Agent"""
        if agent_type not in self.agent_types:
            self.logger.error(f"未知的Agent类型: {agent_type}")
            return False

        if agent_id in self.agent_registry:
            self.logger.warning(f"Agent已存在: {agent_id}")
            return False

        try:
            # 创建Agent配置
            agent_config = AgentConfig(
                agent_id=agent_id,
                agent_type=agent_type,
                config=config or {},
                heartbeat_interval=self.config.agent_heartbeat_interval,
            )

            # 创建Agent实例
            agent_class = self.agent_types[agent_type]
            agent = agent_class(agent_config, self.message_queue, self.config)

            # 启动Agent
            success = await agent.start()
            if success:
                # 注册Agent
                registry = AgentRegistry(
                    agent=agent,
                    config=agent_config,
                    registered_at=datetime.now(),
                    last_heartbeat=datetime.now(),
                )
                self.agent_registry[agent_id] = registry

                self.logger.info(f"Agent启动成功: {agent_id} ({agent_type})")
                return True
            else:
                self.logger.error(f"Agent启动失败: {agent_id}")
                return False

        except Exception as e:
            self.logger.error(f"启动Agent异常: {agent_id}, 错误: {e}")
            return False

    async def stop_agent(self, agent_id: str) -> bool:
        """停止指定Agent"""
        if agent_id not in self.agent_registry:
            self.logger.warning(f"Agent不存在: {agent_id}")
            return False

        try:
            registry = self.agent_registry[agent_id]
            await registry.agent.stop()
            del self.agent_registry[agent_id]

            self.logger.info(f"Agent已停止: {agent_id}")
            return True

        except Exception as e:
            self.logger.error(f"停止Agent异常: {agent_id}, 错误: {e}")
            return False

    async def restart_agent(self, agent_id: str) -> bool:
        """重启指定Agent"""
        if agent_id not in self.agent_registry:
            self.logger.warning(f"Agent不存在: {agent_id}")
            return False

        try:
            registry = self.agent_registry[agent_id]
            await registry.agent.restart()
            registry.last_heartbeat = datetime.now()

            self.logger.info(f"Agent已重启: {agent_id}")
            return True

        except Exception as e:
            self.logger.error(f"重启Agent异常: {agent_id}, 错误: {e}")
            return False

    async def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """获取Agent信息"""
        if agent_id not in self.agent_registry:
            return None

        registry = self.agent_registry[agent_id]
        return registry.agent.get_agent_info()

    async def list_agents(self) -> List[AgentInfo]:
        """列出所有Agent信息"""
        agents = []
        for registry in self.agent_registry.values():
            agents.append(registry.agent.get_agent_info())
        return agents

    async def broadcast_to_agents(
        self, message_type: str, content: Dict[str, Any], agent_types: List[str] = None
    ):
        """向指定类型的Agent广播消息"""
        await self.message_queue.publish_message(
            message_type=message_type, content=content, sender="coordinator"
        )
        self.logger.info(f"向Agent广播消息: {message_type}")

    async def send_to_agent(
        self, agent_id: str, message_type: str, content: Dict[str, Any]
    ) -> bool:
        """向指定Agent发送消息"""
        if agent_id not in self.agent_registry:
            self.logger.warning(f"Agent不存在: {agent_id}")
            return False

        await self.message_queue.publish_message(
            message_type=message_type,
            content=content,
            sender="coordinator",
            receiver=agent_id,
        )
        return True

    async def _handle_control_message(self, message: Message):
        """处理控制消息"""
        try:
            command = message.content.get("command")
            parameters = message.content.get("parameters", {})

            if command == "start_agent":
                agent_type = parameters.get("agent_type")
                agent_id = parameters.get("agent_id")
                config = parameters.get("config", {})
                await self.start_agent(agent_type, agent_id, config)

            elif command == "stop_agent":
                agent_id = parameters.get("agent_id")
                await self.stop_agent(agent_id)

            elif command == "restart_agent":
                agent_id = parameters.get("agent_id")
                await self.restart_agent(agent_id)

            elif command == "broadcast":
                message_type = parameters.get("message_type")
                content = parameters.get("content", {})
                agent_types = parameters.get("agent_types")
                await self.broadcast_to_agents(message_type, content, agent_types)

            self.total_messages_processed += 1

        except Exception as e:
            self.logger.error(f"处理控制消息失败: {e}")

    async def _health_monitoring_loop(self):
        """健康监控循环"""
        while self.running:
            try:
                current_time = datetime.now()

                for agent_id, registry in list(self.agent_registry.items()):
                    # 检查心跳超时
                    heartbeat_timeout = timedelta(
                        seconds=self.config.agent_heartbeat_interval * 3
                    )

                    if current_time - registry.last_heartbeat > heartbeat_timeout:
                        self.logger.warning(f"Agent心跳超时: {agent_id}")

                        # 尝试重启Agent
                        await self.restart_agent(agent_id)

                    # 检查Agent健康状态
                    if not registry.agent.is_healthy():
                        self.logger.warning(f"Agent不健康: {agent_id}")
                        registry.health_check_count += 1

                        # 健康检查失败次数过多时重启
                        if registry.health_check_count >= 3:
                            self.logger.error(
                                f"Agent健康检查失败次数过多，重启: {agent_id}"
                            )
                            await self.restart_agent(agent_id)
                            registry.health_check_count = 0
                    else:
                        registry.health_check_count = 0

                await asyncio.sleep(30)  # 每30秒检查一次

            except Exception as e:
                self.logger.error(f"健康监控异常: {e}")
                await asyncio.sleep(10)

    async def _stats_collection_loop(self):
        """统计收集循环"""
        while self.running:
            try:
                # 收集系统统计信息
                stats = await self.message_queue.get_system_stats()

                # 计算系统指标
                active_agents = len(
                    [
                        registry
                        for registry in self.agent_registry.values()
                        if registry.agent.status == AgentStatus.RUNNING
                    ]
                )

                system_metrics = SystemMetrics(
                    timestamp=datetime.now(),
                    active_agents=active_agents,
                    total_messages_processed=self.total_messages_processed,
                    system_cpu_usage=0.0,  # 可以从系统监控获取
                    system_memory_usage=0.0,  # 可以从系统监控获取
                    redis_memory_usage=stats.get("redis_info", {}).get(
                        "used_memory_percentage", 0.0
                    ),
                    queue_lengths={},
                    error_rate=0.0,  # 可以计算
                    throughput=0.0,  # 可以计算
                    latency_p95=0.0,  # 可以计算
                    latency_p99=0.0,  # 可以计算
                )

                # 可以发送到监控系统
                self.logger.debug(f"系统指标: {system_metrics}")

                await asyncio.sleep(60)  # 每分钟收集一次

            except Exception as e:
                self.logger.error(f"统计收集异常: {e}")
                await asyncio.sleep(10)

    async def _system_monitoring_loop(self):
        """系统监控循环"""
        while self.running:
            try:
                # 检查Agent数量限制
                if len(self.agent_registry) >= self.config.max_concurrent_agents:
                    self.logger.warning(
                        f"Agent数量达到限制: {len(self.agent_registry)}"
                    )

                # 可以添加更多系统监控逻辑
                # 如：内存使用、CPU使用、磁盘空间等

                await asyncio.sleep(300)  # 每5分钟检查一次

            except Exception as e:
                self.logger.error(f"系统监控异常: {e}")
                await asyncio.sleep(30)

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "running": self.running,
            "total_agents": len(self.agent_registry),
            "active_agents": len(
                [
                    registry
                    for registry in self.agent_registry.values()
                    if registry.agent.status == AgentStatus.RUNNING
                ]
            ),
            "total_messages_processed": self.total_messages_processed,
            "uptime": (datetime.now() - self.system_start_time).total_seconds(),
            "registered_agent_types": list(self.agent_types.keys()),
        }

"""
港股量化交易 AI Agent 系统 - Agent数据服务

负责收集和聚合Agent状态数据，为仪表板提供统一的数据访问层。
集成现有的AgentCoordinator和MessageQueue，实现实时数据更新。
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from ..agents.coordinator import AgentCoordinator
from ..core import SystemConfig
from ..core.message_queue import Message, MessageQueue
from ..models.agent_dashboard import (
    AgentDashboardData,
    DashboardSummary,
    ExtendedAgentInfo,
    PerformanceMetrics,
    ResourceUsage,
)
from ..models.base import AgentInfo, AgentStatus, SystemMetrics


@dataclass
class AgentDataConfig:
    """Agent数据服务配置"""

    update_interval: int = 5  # 数据更新间隔（秒）
    max_history_size: int = 1000  # 最大历史数据条数
    cache_ttl: int = 30  # 缓存TTL（秒）
    enable_real_time: bool = True  # 是否启用实时更新


class AgentDataService:
    """Agent数据服务"""

    def __init__(
        self,
        coordinator: AgentCoordinator,
        message_queue: MessageQueue,
        config: AgentDataConfig = None,
    ):
        self.coordinator = coordinator
        self.message_queue = message_queue
        self.config = config or AgentDataConfig()
        self.logger = logging.getLogger("hk_quant_system.agent_data_service")

        # 数据缓存
        self._agent_data_cache: Dict[str, AgentDashboardData] = {}
        self._last_update: Dict[str, datetime] = {}
        self._update_callbacks: List[Callable[[str, AgentDashboardData], None]] = []

        # 后台任务
        self._update_task: Optional[asyncio.Task] = None
        self._running = False

    async def initialize(self) -> bool:
        """初始化服务"""
        try:
            self.logger.info("正在初始化Agent数据服务...")

            # 订阅Agent状态变化消息
            await self._subscribe_to_agent_updates()

            # 启动后台更新任务
            if self.config.enable_real_time:
                self._running = True
                self._update_task = asyncio.create_task(self._background_update_loop())

            self.logger.info("Agent数据服务初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"Agent数据服务初始化失败: {e}")
            return False

    async def _subscribe_to_agent_updates(self):
        """订阅Agent状态更新消息"""
        try:
            # 订阅Agent状态变化消息
            await self.message_queue.subscribe(
                "agent_status_updates", self._handle_agent_status_update
            )

            # 订阅Agent心跳消息
            await self.message_queue.subscribe(
                "agent_heartbeat", self._handle_agent_heartbeat
            )

            # 订阅Agent错误消息
            await self.message_queue.subscribe("agent_errors", self._handle_agent_error)

            self.logger.info("已订阅Agent状态更新消息")

        except Exception as e:
            self.logger.error(f"订阅Agent更新消息失败: {e}")

    async def _handle_agent_status_update(self, message: Message):
        """处理Agent状态更新消息"""
        try:
            payload = message.payload
            agent_id = payload.get("agent_id")

            if agent_id:
                # 触发数据更新
                await self._update_agent_data(agent_id)

        except Exception as e:
            self.logger.error(f"处理Agent状态更新消息失败: {e}")

    async def _handle_agent_heartbeat(self, message: Message):
        """处理Agent心跳消息"""
        try:
            payload = message.payload
            agent_id = payload.get("agent_id")

            if agent_id and agent_id in self._agent_data_cache:
                # 更新心跳时间
                self._agent_data_cache[agent_id].last_heartbeat = datetime.utcnow()
                self._last_update[agent_id] = datetime.utcnow()

        except Exception as e:
            self.logger.error(f"处理Agent心跳消息失败: {e}")

    async def _handle_agent_error(self, message: Message):
        """处理Agent错误消息"""
        try:
            payload = message.payload
            agent_id = payload.get("agent_id")
            error_message = payload.get("error_message")

            if agent_id and agent_id in self._agent_data_cache:
                # 更新错误信息
                self._agent_data_cache[agent_id].error_count += 1
                self._agent_data_cache[agent_id].last_error = error_message
                self._last_update[agent_id] = datetime.utcnow()

        except Exception as e:
            self.logger.error(f"处理Agent错误消息失败: {e}")

    async def _background_update_loop(self):
        """后台数据更新循环"""
        while self._running:
            try:
                # 获取所有Agent ID
                agent_statuses = await self.coordinator.get_all_agent_statuses()

                # 更新每个Agent的数据
                for agent_id in agent_statuses.keys():
                    await self._update_agent_data(agent_id)

                # 等待下次更新
                await asyncio.sleep(self.config.update_interval)

            except Exception as e:
                self.logger.error(f"后台更新循环错误: {e}")
                await asyncio.sleep(self.config.update_interval)

    async def _update_agent_data(self, agent_id: str):
        """更新指定Agent的数据"""
        try:
            # 检查缓存是否过期
            if agent_id in self._last_update:
                cache_age = datetime.utcnow() - self._last_update[agent_id]
                if cache_age.total_seconds() < self.config.cache_ttl:
                    return  # 缓存未过期，跳过更新

            # 获取Agent基础信息
            agent_status = await self.coordinator.get_agent_status(agent_id)
            if not agent_status:
                return

            # 创建或更新Agent数据
            agent_data = await self._build_agent_dashboard_data(agent_id, agent_status)

            # 更新缓存
            self._agent_data_cache[agent_id] = agent_data
            self._last_update[agent_id] = datetime.utcnow()

            # 通知回调函数
            for callback in self._update_callbacks:
                try:
                    callback(agent_id, agent_data)
                except Exception as e:
                    self.logger.error(f"执行更新回调失败: {e}")

        except Exception as e:
            self.logger.error(f"更新Agent数据失败 {agent_id}: {e}")

    async def _build_agent_dashboard_data(
        self, agent_id: str, agent_status: Dict[str, Any]
    ) -> AgentDashboardData:
        """构建Agent仪表板数据"""

        # 计算运行时间
        start_time = agent_status.get("start_time")
        uptime_seconds = 0.0
        if start_time:
            uptime_seconds = (datetime.utcnow() - start_time).total_seconds()

        # 获取资源使用情况
        resource_usage = await self._get_agent_resource_usage(agent_id)

        # 获取绩效指标（如果有的话）
        performance_metrics = await self._get_agent_performance_metrics(agent_id)

        # 构建Agent仪表板数据
        agent_data = AgentDashboardData(
            agent_id=agent_id,
            agent_type=agent_status.get("agent_type", "Unknown"),
            status=AgentStatus(agent_status.get("status", "unknown")),
            last_heartbeat=agent_status.get("last_heartbeat", datetime.utcnow()),
            uptime_seconds=uptime_seconds,
            current_strategy=None,  # 将在策略服务中填充
            available_strategies=[],  # 将在策略服务中填充
            performance_metrics=performance_metrics,
            performance_history=[],  # 将在绩效服务中填充
            resource_usage=resource_usage,
            recent_actions=[],  # 将在控制服务中填充
            pending_actions=[],  # 将在控制服务中填充
            messages_processed=agent_status.get("messages_processed", 0),
            error_count=agent_status.get("error_count", 0),
            last_error=agent_status.get("last_error"),
            configuration=agent_status.get("configuration", {}),
            version=agent_status.get("version", "1.0.0"),
            last_updated=datetime.utcnow(),
        )

        return agent_data

    async def _get_agent_resource_usage(self, agent_id: str) -> Optional[ResourceUsage]:
        """获取Agent资源使用情况"""
        try:
            # 这里应该从系统监控或Agent自身获取实际的资源使用数据
            # 目前返回模拟数据
            return ResourceUsage(
                agent_id=agent_id,
                cpu_usage=0.0,  # 实际实现中应该从系统获取
                memory_usage=0.0,
                memory_used_mb=0.0,
                memory_total_mb=0.0,
                network_in_mbps=0.0,
                network_out_mbps=0.0,
                disk_io_mbps=0.0,
                messages_per_second=0.0,
                queue_length=0,
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            self.logger.error(f"获取Agent资源使用情况失败 {agent_id}: {e}")
            return None

    async def _get_agent_performance_metrics(
        self, agent_id: str
    ) -> Optional[PerformanceMetrics]:
        """获取Agent绩效指标"""
        try:
            # 这里应该从绩效服务获取实际的绩效数据
            # 目前返回None，将在绩效服务中实现
            return None
        except Exception as e:
            self.logger.error(f"获取Agent绩效指标失败 {agent_id}: {e}")
            return None

    async def get_agent_data(self, agent_id: str) -> Optional[AgentDashboardData]:
        """获取指定Agent的数据"""
        try:
            # 检查缓存
            if agent_id in self._agent_data_cache:
                return self._agent_data_cache[agent_id]

            # 如果缓存中没有，立即更新
            await self._update_agent_data(agent_id)
            return self._agent_data_cache.get(agent_id)

        except Exception as e:
            self.logger.error(f"获取Agent数据失败 {agent_id}: {e}")
            return None

    async def get_all_agents_data(self) -> Dict[str, AgentDashboardData]:
        """获取所有Agent的数据"""
        try:
            # 获取所有Agent ID
            agent_statuses = await self.coordinator.get_all_agent_statuses()

            # 确保所有Agent数据都已更新
            for agent_id in agent_statuses.keys():
                if agent_id not in self._agent_data_cache:
                    await self._update_agent_data(agent_id)

            return self._agent_data_cache.copy()

        except Exception as e:
            self.logger.error(f"获取所有Agent数据失败: {e}")
            return {}

    async def get_dashboard_summary(self) -> DashboardSummary:
        """获取仪表板总览数据"""
        try:
            all_agents = await self.get_all_agents_data()

            total_agents = len(all_agents)
            active_agents = sum(
                1
                for agent in all_agents.values()
                if agent.status == AgentStatus.RUNNING
            )
            error_agents = sum(
                1 for agent in all_agents.values() if agent.status == AgentStatus.ERROR
            )

            # 计算系统整体绩效指标
            system_sharpe_ratio = 0.0
            system_total_return = 0.0
            system_max_drawdown = 0.0

            total_cpu_usage = 0.0
            total_memory_usage = 0.0
            total_messages_processed = 0

            active_strategies = 0
            strategy_types = {}

            for agent in all_agents.values():
                # 累计绩效指标
                if agent.performance_metrics:
                    system_sharpe_ratio += agent.performance_metrics.sharpe_ratio
                    system_total_return += agent.performance_metrics.total_return
                    system_max_drawdown = max(
                        system_max_drawdown, agent.performance_metrics.max_drawdown
                    )

                # 累计资源使用
                if agent.resource_usage:
                    total_cpu_usage += agent.resource_usage.cpu_usage
                    total_memory_usage += agent.resource_usage.memory_usage

                total_messages_processed += agent.messages_processed

                # 统计策略信息
                if agent.current_strategy:
                    active_strategies += 1
                    strategy_type = agent.current_strategy.strategy_type
                    strategy_types[strategy_type] = (
                        strategy_types.get(strategy_type, 0) + 1
                    )

            # 计算平均值
            if total_agents > 0:
                system_sharpe_ratio /= total_agents
                system_total_return /= total_agents
                total_cpu_usage /= total_agents
                total_memory_usage /= total_agents

            return DashboardSummary(
                total_agents=total_agents,
                active_agents=active_agents,
                error_agents=error_agents,
                system_sharpe_ratio=system_sharpe_ratio,
                system_total_return=system_total_return,
                system_max_drawdown=system_max_drawdown,
                total_cpu_usage=total_cpu_usage,
                total_memory_usage=total_memory_usage,
                total_messages_processed=total_messages_processed,
                active_strategies=active_strategies,
                strategy_types=strategy_types,
                last_updated=datetime.utcnow(),
            )

        except Exception as e:
            self.logger.error(f"获取仪表板总览失败: {e}")
            return DashboardSummary(
                total_agents=0,
                active_agents=0,
                error_agents=0,
                system_sharpe_ratio=0.0,
                system_total_return=0.0,
                system_max_drawdown=0.0,
                total_cpu_usage=0.0,
                total_memory_usage=0.0,
                total_messages_processed=0,
                active_strategies=0,
                strategy_types={},
                last_updated=datetime.utcnow(),
            )

    def add_update_callback(self, callback: Callable[[str, AgentDashboardData], None]):
        """添加数据更新回调函数"""
        self._update_callbacks.append(callback)

    def remove_update_callback(
        self, callback: Callable[[str, AgentDashboardData], None]
    ):
        """移除数据更新回调函数"""
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)

    async def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在清理Agent数据服务...")

            self._running = False

            if self._update_task:
                self._update_task.cancel()
                try:
                    await self._update_task
                except asyncio.CancelledError:
                    pass

            # 清理缓存
            self._agent_data_cache.clear()
            self._last_update.clear()
            self._update_callbacks.clear()

            self.logger.info("Agent数据服务清理完成")

        except Exception as e:
            self.logger.error(f"清理Agent数据服务失败: {e}")


__all__ = [
    "AgentDataConfig",
    "AgentDataService",
]

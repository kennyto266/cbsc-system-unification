"""
港股量化交易 AI Agent 系统 - Agent控制组件

实现AgentControlService类，提供Agent启动 / 停止 / 重启功能。
集成AgentCoordinator的控制接口，提供Agent操作的统一控制接口。
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from ..agents.coordinator import AgentCoordinator
from ..core import SystemConfig
from ..core.message_queue import Message, MessageQueue
from ..models.agent_dashboard import (
    ActionResult,
    ActionStatus,
    AgentControlAction,
    ControlActionType,
)


@dataclass
class AgentControlConfig:
    """Agent控制服务配置"""

    action_timeout: int = 30  # 操作超时时间（秒）
    max_retry_attempts: int = 3  # 最大重试次数
    retry_delay: int = 5  # 重试延迟（秒）
    enable_confirmations: bool = True  # 是否启用确认机制
    log_all_actions: bool = True  # 是否记录所有操作


class AgentControlService:
    """Agent控制服务"""

    def __init__(
        self,
        coordinator: AgentCoordinator,
        message_queue: MessageQueue,
        config: AgentControlConfig = None,
    ):
        self.coordinator = coordinator
        self.message_queue = message_queue
        self.config = config or AgentControlConfig()
        self.logger = logging.getLogger("hk_quant_system.agent_control_service")

        # 操作管理
        self._pending_actions: Dict[str, AgentControlAction] = {}
        self._action_history: List[AgentControlAction] = []
        self._action_callbacks: List[Callable[[str, AgentControlAction], None]] = []

        # 操作状态跟踪
        self._action_timeouts: Dict[str, asyncio.Task] = {}

        # 后台任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def initialize(self) -> bool:
        """初始化服务"""
        try:
            self.logger.info("正在初始化Agent控制服务...")

            # 订阅控制相关消息
            await self._subscribe_to_control_updates()

            # 启动后台清理任务
            self._running = True
            self._cleanup_task = asyncio.create_task(self._background_cleanup_loop())

            self.logger.info("Agent控制服务初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"Agent控制服务初始化失败: {e}")
            return False

    async def _subscribe_to_control_updates(self):
        """订阅控制更新消息"""
        try:
            # 订阅Agent状态变化消息
            await self.message_queue.subscribe(
                "agent_status_changes", self._handle_agent_status_change
            )

            # 订阅控制操作结果消息
            await self.message_queue.subscribe(
                "control_action_results", self._handle_control_action_result
            )

            self.logger.info("已订阅Agent控制更新消息")

        except Exception as e:
            self.logger.error(f"订阅控制更新消息失败: {e}")

    async def _handle_agent_status_change(self, message: Message):
        """处理Agent状态变化消息"""
        try:
            payload = message.payload
            agent_id = payload.get("agent_id")
            new_status = payload.get("status")
            old_status = payload.get("old_status")

            if agent_id and new_status and old_status:
                # 查找相关的待处理操作
                for action_id, action in self._pending_actions.items():
                    if action.agent_id == agent_id:
                        # 检查操作是否完成
                        await self._check_action_completion(
                            action_id, action, new_status
                        )

        except Exception as e:
            self.logger.error(f"处理Agent状态变化消息失败: {e}")

    async def _handle_control_action_result(self, message: Message):
        """处理控制操作结果消息"""
        try:
            payload = message.payload
            action_id = payload.get("action_id")
            success = payload.get("success", False)
            message_text = payload.get("message", "")
            error_code = payload.get("error_code")

            if action_id and action_id in self._pending_actions:
                action = self._pending_actions[action_id]

                # 更新操作结果
                action.result = ActionResult(
                    success=success, message=message_text, error_code=error_code
                )

                # 完成操作
                await self._complete_action(action_id, success)

        except Exception as e:
            self.logger.error(f"处理控制操作结果消息失败: {e}")

    async def _check_action_completion(
        self, action_id: str, action: AgentControlAction, new_status: str
    ):
        """检查操作是否完成"""
        try:
            expected_status = None

            # 根据操作类型确定期望的状态
            if action.action_type == ControlActionType.START:
                expected_status = "running"
            elif action.action_type == ControlActionType.STOP:
                expected_status = "stopped"
            elif action.action_type == ControlActionType.RESTART:
                # 重启操作需要特殊处理
                return

            # 检查是否达到期望状态
            if expected_status and new_status == expected_status:
                await self._complete_action(action_id, True)

        except Exception as e:
            self.logger.error(f"检查操作完成状态失败 {action_id}: {e}")

    async def _complete_action(self, action_id: str, success: bool):
        """完成操作"""
        try:
            if action_id not in self._pending_actions:
                return

            action = self._pending_actions[action_id]
            action.status = ActionStatus.COMPLETED if success else ActionStatus.FAILED
            action.completed_at = datetime.utcnow()

            # 取消超时任务
            if action_id in self._action_timeouts:
                self._action_timeouts[action_id].cancel()
                del self._action_timeouts[action_id]

            # 移动到历史记录
            self._action_history.append(action)
            del self._pending_actions[action_id]

            # 通知回调函数
            for callback in self._action_callbacks:
                try:
                    callback(action_id, action)
                except Exception as e:
                    self.logger.error(f"执行操作完成回调失败: {e}")

            # 记录操作日志
            if self.config.log_all_actions:
                self.logger.info(
                    f"操作完成 {action_id}: {action.action_type} -> {'成功' if success else '失败'}"
                )

        except Exception as e:
            self.logger.error(f"完成操作失败 {action_id}: {e}")

    async def _background_cleanup_loop(self):
        """后台清理循环"""
        while self._running:
            try:
                # 清理过期的操作
                await self._cleanup_expired_actions()

                # 等待下次清理
                await asyncio.sleep(60)  # 每分钟清理一次

            except Exception as e:
                self.logger.error(f"后台清理循环错误: {e}")
                await asyncio.sleep(60)

    async def _cleanup_expired_actions(self):
        """清理过期的操作"""
        try:
            current_time = datetime.utcnow()
            expired_actions = []

            for action_id, action in self._pending_actions.items():
                # 检查操作是否超时
                if action.started_at:
                    elapsed_time = (current_time - action.started_at).total_seconds()
                    if elapsed_time > self.config.action_timeout:
                        expired_actions.append(action_id)

            # 处理过期操作
            for action_id in expired_actions:
                await self._timeout_action(action_id)

        except Exception as e:
            self.logger.error(f"清理过期操作失败: {e}")

    async def _timeout_action(self, action_id: str):
        """处理超时操作"""
        try:
            if action_id not in self._pending_actions:
                return

            action = self._pending_actions[action_id]
            action.status = ActionStatus.FAILED
            action.completed_at = datetime.utcnow()
            action.error_message = "操作超时"

            # 取消超时任务
            if action_id in self._action_timeouts:
                self._action_timeouts[action_id].cancel()
                del self._action_timeouts[action_id]

            # 移动到历史记录
            self._action_history.append(action)
            del self._pending_actions[action_id]

            self.logger.warning(f"操作超时 {action_id}: {action.action_type}")

        except Exception as e:
            self.logger.error(f"处理超时操作失败 {action_id}: {e}")

    async def start_agent(self, agent_id: str, initiated_by: str = "system") -> str:
        """启动Agent"""
        try:
            # 检查Agent是否已经在运行
            agent_status = await self.coordinator.get_agent_status(agent_id)
            if agent_status and agent_status.get("status") == "running":
                raise ValueError(f"Agent {agent_id} 已经在运行中")

            # 创建控制操作
            action = AgentControlAction(
                action_id=str(uuid.uuid4()),
                agent_id=agent_id,
                action_type=ControlActionType.START,
                initiated_by=initiated_by,
                requires_confirmation=self.config.enable_confirmations,
            )

            # 执行操作
            return await self._execute_action(action)

        except Exception as e:
            self.logger.error(f"启动Agent失败 {agent_id}: {e}")
            raise

    async def stop_agent(self, agent_id: str, initiated_by: str = "system") -> str:
        """停止Agent"""
        try:
            # 检查Agent是否已经停止
            agent_status = await self.coordinator.get_agent_status(agent_id)
            if agent_status and agent_status.get("status") == "stopped":
                raise ValueError(f"Agent {agent_id} 已经停止")

            # 创建控制操作
            action = AgentControlAction(
                action_id=str(uuid.uuid4()),
                agent_id=agent_id,
                action_type=ControlActionType.STOP,
                initiated_by=initiated_by,
                requires_confirmation=self.config.enable_confirmations,
            )

            # 执行操作
            return await self._execute_action(action)

        except Exception as e:
            self.logger.error(f"停止Agent失败 {agent_id}: {e}")
            raise

    async def restart_agent(self, agent_id: str, initiated_by: str = "system") -> str:
        """重启Agent"""
        try:
            # 创建控制操作
            action = AgentControlAction(
                action_id=str(uuid.uuid4()),
                agent_id=agent_id,
                action_type=ControlActionType.RESTART,
                initiated_by=initiated_by,
                requires_confirmation=self.config.enable_confirmations,
            )

            # 执行操作
            return await self._execute_action(action)

        except Exception as e:
            self.logger.error(f"重启Agent失败 {agent_id}: {e}")
            raise

    async def pause_agent(self, agent_id: str, initiated_by: str = "system") -> str:
        """暂停Agent"""
        try:
            # 创建控制操作
            action = AgentControlAction(
                action_id=str(uuid.uuid4()),
                agent_id=agent_id,
                action_type=ControlActionType.PAUSE,
                initiated_by=initiated_by,
                requires_confirmation=self.config.enable_confirmations,
            )

            # 执行操作
            return await self._execute_action(action)

        except Exception as e:
            self.logger.error(f"暂停Agent失败 {agent_id}: {e}")
            raise

    async def resume_agent(self, agent_id: str, initiated_by: str = "system") -> str:
        """恢复Agent"""
        try:
            # 创建控制操作
            action = AgentControlAction(
                action_id=str(uuid.uuid4()),
                agent_id=agent_id,
                action_type=ControlActionType.RESUME,
                initiated_by=initiated_by,
                requires_confirmation=self.config.enable_confirmations,
            )

            # 执行操作
            return await self._execute_action(action)

        except Exception as e:
            self.logger.error(f"恢复Agent失败 {agent_id}: {e}")
            raise

    async def update_agent_parameters(
        self, agent_id: str, parameters: Dict[str, Any], initiated_by: str = "system"
    ) -> str:
        """更新Agent参数"""
        try:
            # 创建控制操作
            action = AgentControlAction(
                action_id=str(uuid.uuid4()),
                agent_id=agent_id,
                action_type=ControlActionType.UPDATE_PARAMETERS,
                parameters=parameters,
                initiated_by=initiated_by,
                requires_confirmation=self.config.enable_confirmations,
            )

            # 执行操作
            return await self._execute_action(action)

        except Exception as e:
            self.logger.error(f"更新Agent参数失败 {agent_id}: {e}")
            raise

    async def switch_agent_strategy(
        self, agent_id: str, strategy_id: str, initiated_by: str = "system"
    ) -> str:
        """切换Agent策略"""
        try:
            # 创建控制操作
            action = AgentControlAction(
                action_id=str(uuid.uuid4()),
                agent_id=agent_id,
                action_type=ControlActionType.SWITCH_STRATEGY,
                parameters={"strategy_id": strategy_id},
                initiated_by=initiated_by,
                requires_confirmation=self.config.enable_confirmations,
            )

            # 执行操作
            return await self._execute_action(action)

        except Exception as e:
            self.logger.error(f"切换Agent策略失败 {agent_id}: {e}")
            raise

    async def _execute_action(self, action: AgentControlAction) -> str:
        """执行控制操作"""
        try:
            # 添加到待处理操作列表
            self._pending_actions[action.action_id] = action

            # 设置操作状态
            action.status = ActionStatus.IN_PROGRESS
            action.started_at = datetime.utcnow()

            # 根据操作类型执行相应操作
            if action.action_type == ControlActionType.START:
                await self.coordinator.start_agent(action.agent_id)
            elif action.action_type == ControlActionType.STOP:
                await self.coordinator.stop_agent(action.agent_id)
            elif action.action_type == ControlActionType.RESTART:
                await self.coordinator.stop_agent(action.agent_id)
                await asyncio.sleep(2)  # 等待停止完成
                await self.coordinator.start_agent(action.agent_id)
            elif action.action_type == ControlActionType.PAUSE:
                # 发送暂停消息
                await self.message_queue.publish_message(
                    "agent_control", {"action": "pause", "agent_id": action.agent_id}
                )
            elif action.action_type == ControlActionType.RESUME:
                # 发送恢复消息
                await self.message_queue.publish_message(
                    "agent_control", {"action": "resume", "agent_id": action.agent_id}
                )
            elif action.action_type == ControlActionType.UPDATE_PARAMETERS:
                # 发送参数更新消息
                await self.message_queue.publish_message(
                    "agent_control",
                    {
                        "action": "update_parameters",
                        "agent_id": action.agent_id,
                        "parameters": action.parameters,
                    },
                )
            elif action.action_type == ControlActionType.SWITCH_STRATEGY:
                # 发送策略切换消息
                await self.message_queue.publish_message(
                    "agent_control",
                    {
                        "action": "switch_strategy",
                        "agent_id": action.agent_id,
                        "strategy_id": action.parameters.get("strategy_id"),
                    },
                )

            # 设置超时任务
            self._action_timeouts[action.action_id] = asyncio.create_task(
                self._action_timeout_handler(action.action_id)
            )

            # 记录操作日志
            if self.config.log_all_actions:
                self.logger.info(
                    f"执行操作 {action.action_id}: {action.action_type} -> {action.agent_id}"
                )

            return action.action_id

        except Exception as e:
            # 操作失败
            action.status = ActionStatus.FAILED
            action.completed_at = datetime.utcnow()
            action.error_message = str(e)

            # 移动到历史记录
            self._action_history.append(action)
            if action.action_id in self._pending_actions:
                del self._pending_actions[action.action_id]

            self.logger.error(f"执行操作失败 {action.action_id}: {e}")
            raise

    async def _action_timeout_handler(self, action_id: str):
        """操作超时处理器"""
        try:
            await asyncio.sleep(self.config.action_timeout)

            # 检查操作是否仍在待处理列表中
            if action_id in self._pending_actions:
                await self._timeout_action(action_id)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"操作超时处理器错误 {action_id}: {e}")

    async def get_action_status(self, action_id: str) -> Optional[AgentControlAction]:
        """获取操作状态"""
        try:
            # 检查待处理操作
            if action_id in self._pending_actions:
                return self._pending_actions[action_id]

            # 检查历史操作
            for action in self._action_history:
                if action.action_id == action_id:
                    return action

            return None

        except Exception as e:
            self.logger.error(f"获取操作状态失败 {action_id}: {e}")
            return None

    async def get_pending_actions(self) -> List[AgentControlAction]:
        """获取所有待处理操作"""
        try:
            return list(self._pending_actions.values())
        except Exception as e:
            self.logger.error(f"获取待处理操作失败: {e}")
            return []

    async def get_action_history(
        self, agent_id: Optional[str] = None
    ) -> List[AgentControlAction]:
        """获取操作历史记录"""
        try:
            if agent_id:
                return [
                    action
                    for action in self._action_history
                    if action.agent_id == agent_id
                ]
            else:
                return self._action_history.copy()

        except Exception as e:
            self.logger.error(f"获取操作历史记录失败: {e}")
            return []

    async def cancel_action(self, action_id: str, reason: str = "用户取消") -> bool:
        """取消操作"""
        try:
            if action_id not in self._pending_actions:
                return False

            action = self._pending_actions[action_id]
            action.status = ActionStatus.CANCELLED
            action.completed_at = datetime.utcnow()
            action.error_message = reason

            # 取消超时任务
            if action_id in self._action_timeouts:
                self._action_timeouts[action_id].cancel()
                del self._action_timeouts[action_id]

            # 移动到历史记录
            self._action_history.append(action)
            del self._pending_actions[action_id]

            self.logger.info(f"操作已取消 {action_id}: {reason}")
            return True

        except Exception as e:
            self.logger.error(f"取消操作失败 {action_id}: {e}")
            return False

    def add_action_callback(self, callback: Callable[[str, AgentControlAction], None]):
        """添加操作回调函数"""
        self._action_callbacks.append(callback)

    def remove_action_callback(
        self, callback: Callable[[str, AgentControlAction], None]
    ):
        """移除操作回调函数"""
        if callback in self._action_callbacks:
            self._action_callbacks.remove(callback)

    async def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在清理Agent控制服务...")

            self._running = False

            # 取消所有超时任务
            for task in self._action_timeouts.values():
                task.cancel()

            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass

            # 清理数据
            self._pending_actions.clear()
            self._action_history.clear()
            self._action_callbacks.clear()
            self._action_timeouts.clear()

            self.logger.info("Agent控制服务清理完成")

        except Exception as e:
            self.logger.error(f"清理Agent控制服务失败: {e}")


__all__ = [
    "AgentControlConfig",
    "AgentControlService",
]

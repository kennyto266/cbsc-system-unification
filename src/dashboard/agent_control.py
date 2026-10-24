"""
港股量化交易 AI Agent 系统 - Agent控制组件

实现AgentControlService类，提供Agent启动/停止/重启功能。
集成AgentCoordinator的控制接口，提供Agent操作的统一控制接口。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import uuid

from ..core import SystemConfig
from ..core.message_queue import MessageQueue, Message
from ..agents.coordinator import AgentCoordinator
from ..models.agent_dashboard import (
AgentControlAction,
ControlActionType,
ActionStatus,
ActionResult
)

@dataclass
class AgentControlConfig:
"""Agent控制服务配置"""
action_timeout: int = 30 # 操作超时时间（秒）
max_retry_attempts: int = 3 # 最大重试次数
retry_delay: int = 5 # 重试延迟（秒）
enable_confirmations: bool = True # 是否启用确认机制
log_all_actions: bool = True # 是否记录所有操作

class AgentControlService:
"""Agent控制服务"""

def __init__(
self, 
coordinator: AgentCoordinator,
message_queue: MessageQueue,
config: AgentControlConfig = None
):    self.coordinator = coordinator
self.message_queue = message_queue
self.config = config or AgentControlConfig()
self.logger = logging.getLogger"hk_quant_system.agent_control_service"

self._pending_actions: Dict[str, AgentControlAction] = {}
self._action_history: List[AgentControlAction] = []
self._action_callbacks: List[Callable[[str, AgentControlAction], None]] = []

self._action_timeouts: Dict[str, asyncio.Task] = {}

self._cleanup_task: Optional[asyncio.Task] = None
self._running = False

async def initializeself -> bool:
"""初始化服务"""
try:
self.logger.info"正在初始化Agent控制服务..."

# 订阅控制相关消息
await self._subscribe_to_control_updates()

# 启动后台清理任务
self._running = True
self._cleanup_task = asyncio.create_task(self._background_cleanup_loop())

self.logger.info"Agent控制服务初始化完成"
return True

except Exception as e:
self.logger.errorf"Agent控制服务初始化失败: {e}"
return False

async def _subscribe_to_control_updatesself:
"""订阅控制更新消息"""
try:
# 订阅Agent状态变化消息
await self.message_queue.subscribe(
"agent_status_changes",
self._handle_agent_status_change
)

# 订阅控制操作结果消息
await self.message_queue.subscribe(
"control_action_results",
self._handle_control_action_result
)

self.logger.info"已订阅Agent控制更新消息"

except Exception as e:
self.logger.errorf"订阅控制更新消息失败: {e}"

async def _handle_agent_status_changeself, message: Message:
"""处理Agent状态变化消息"""
try:    payload = message.payload
agent_id = payload.get"agent_id"
new_status = payload.get"status"
old_status = payload.get"old_status"

if agent_id and new_status and old_status:
# 查找相关的待处理操作
for action_id, action in self._pending_actions.items():    if action.agent_id == agent_id:
# 检查操作是否完成
await self._check_action_completionaction_id, action, new_status

except Exception as e:
self.logger.errorf"处理Agent状态变化消息失败: {e}"

async def _handle_control_action_resultself, message: Message:
"""处理控制操作结果消息"""
try:    payload = message.payload
action_id = payload.get"action_id"
success = payload.get"success", False
message_text = payload.get"message", ""
error_code = payload.get"error_code"

if action_id and action_id in self._pending_actions:    action = self._pending_actions[action_id]

action.result = ActionResult(
success=success,
message=message_text,
error_code=error_code
)

await self._complete_actionaction_id, success

except Exception as e:
self.logger.errorf"处理控制操作结果消息失败: {e}"

async def _check_action_completionself, action_id: str, action: AgentControlAction, new_status: str:
"""检查操作是否完成"""
try:    expected_status = None

# 根据操作类型确定期望的状态
if action.action_type == ControlActionType.START:    expected_status = "running"
elif action.action_type == ControlActionType.STOP:    expected_status = "stopped"
elif action.action_type == ControlActionType.RESTART:
# 重启操作需要特殊处理
return

# 检查是否达到期望状态
if expected_status and new_status == expected_status:
await self._complete_actionaction_id, True

except Exception as e:
self.logger.errorf"检查操作完成状态失败 {action_id}: {e}"

async def _complete_actionself, action_id: str, success: bool:
"""完成操作"""
try:
if action_id not in self._pending_actions:
return

action = self._pending_actions[action_id]
action.status = ActionStatus.COMPLETED if success else ActionStatus.FAILED
action.completed_at = datetime.utcnow()

if action_id in self._action_timeouts:
self._action_timeouts[action_id].cancel()
del self._action_timeouts[action_id]

self._action_history.appendaction
del self._pending_actions[action_id]

for callback in self._action_callbacks:
try:
callbackaction_id, action
except Exception as e:
self.logger.errorf"执行操作完成回调失败: {e}"

if self.config.log_all_actions:
self.logger.infof"操作完成 {action_id}: {action.action_type} -> {'成功' if success else '失败'}"

except Exception as e:
self.logger.errorf"完成操作失败 {action_id}: {e}"

async def _background_cleanup_loopself:
"""后台清理循环"""
while self._running:
try:

await self._cleanup_expired_actions()

await asyncio.sleep60 # 每分钟清理一次

except Exception as e:
self.logger.errorf"后台清理循环错误: {e}"
await asyncio.sleep60

async def _cleanup_expired_actionsself:
"""清理过期的操作"""
try:    current_time = datetime.utcnow()
expired_actions = []

for action_id, action in self._pending_actions.items():
# 检查操作是否超时
if action.started_at:    elapsed_time = (current_time - action.started_at).total_seconds()
if elapsed_time > self.config.action_timeout:
expired_actions.appendaction_id

for action_id in expired_actions:
await self._timeout_actionaction_id

except Exception as e:
self.logger.errorf"清理过期操作失败: {e}"

async def _timeout_actionself, action_id: str:
"""处理超时操作"""
try:
if action_id not in self._pending_actions:
return

action = self._pending_actions[action_id]
action.status = ActionStatus.FAILED
action.completed_at = datetime.utcnow()
action.error_message = "操作超时"

if action_id in self._action_timeouts:
self._action_timeouts[action_id].cancel()
del self._action_timeouts[action_id]

self._action_history.appendaction
del self._pending_actions[action_id]

self.logger.warningf"操作超时 {action_id}: {action.action_type}"

except Exception as e:
self.logger.errorf"处理超时操作失败 {action_id}: {e}"

async def start_agentself, agent_id: str, initiated_by: str = "system" -> str:
"""启动Agent"""
try:
# 检查Agent是否已经在运行
agent_status = await self.coordinator.get_agent_statusagent_id
if agent_status and agent_status.get"status" == "running":
raise ValueErrorf"Agent {agent_id} 已经在运行中"

action = AgentControlAction(
action_id=str(uuid.uuid4()),
agent_id=agent_id,
action_type=ControlActionType.START,
initiated_by=initiated_by,
requires_confirmation=self.config.enable_confirmations
)

return await self._execute_actionaction

except Exception as e:
self.logger.errorf"启动Agent失败 {agent_id}: {e}"
raise

async def stop_agentself, agent_id: str, initiated_by: str = "system" -> str:
"""停止Agent"""
try:
# 检查Agent是否已经停止
agent_status = await self.coordinator.get_agent_statusagent_id
if agent_status and agent_status.get"status" == "stopped":
raise ValueErrorf"Agent {agent_id} 已经停止"

action = AgentControlAction(
action_id=str(uuid.uuid4()),
agent_id=agent_id,
action_type=ControlActionType.STOP,
initiated_by=initiated_by,
requires_confirmation=self.config.enable_confirmations
)

return await self._execute_actionaction

except Exception as e:
self.logger.errorf"停止Agent失败 {agent_id}: {e}"
raise

async def restart_agentself, agent_id: str, initiated_by: str = "system" -> str:
"""重启Agent"""
try:

action = AgentControlAction(
action_id=str(uuid.uuid4()),
agent_id=agent_id,
action_type=ControlActionType.RESTART,
initiated_by=initiated_by,
requires_confirmation=self.config.enable_confirmations
)

return await self._execute_actionaction

except Exception as e:
self.logger.errorf"重启Agent失败 {agent_id}: {e}"
raise

async def pause_agentself, agent_id: str, initiated_by: str = "system" -> str:
"""暂停Agent"""
try:

action = AgentControlAction(
action_id=str(uuid.uuid4()),
agent_id=agent_id,
action_type=ControlActionType.PAUSE,
initiated_by=initiated_by,
requires_confirmation=self.config.enable_confirmations
)

return await self._execute_actionaction

except Exception as e:
self.logger.errorf"暂停Agent失败 {agent_id}: {e}"
raise

async def resume_agentself, agent_id: str, initiated_by: str = "system" -> str:
"""恢复Agent"""
try:

action = AgentControlAction(
action_id=str(uuid.uuid4()),
agent_id=agent_id,
action_type=ControlActionType.RESUME,
initiated_by=initiated_by,
requires_confirmation=self.config.enable_confirmations
)

return await self._execute_actionaction

except Exception as e:
self.logger.errorf"恢复Agent失败 {agent_id}: {e}"
raise

async def update_agent_parameters(
self, 
agent_id: str, 
parameters: Dict[str, Any],
initiated_by: str = "system"
) -> str:
"""更新Agent参数"""
try:

action = AgentControlAction(
action_id=str(uuid.uuid4()),
agent_id=agent_id,
action_type=ControlActionType.UPDATE_PARAMETERS,
parameters=parameters,
initiated_by=initiated_by,
requires_confirmation=self.config.enable_confirmations
)

return await self._execute_actionaction

except Exception as e:
self.logger.errorf"更新Agent参数失败 {agent_id}: {e}"
raise

async def switch_agent_strategy(
self, 
agent_id: str, 
strategy_id: str,
initiated_by: str = "system"
) -> str:
"""切换Agent策略"""
try:

action = AgentControlAction(
action_id=str(uuid.uuid4()),
agent_id=agent_id,
action_type=ControlActionType.SWITCH_STRATEGY,
parameters={"strategy_id": strategy_id},
initiated_by=initiated_by,
requires_confirmation=self.config.enable_confirmations
)

return await self._execute_actionaction

except Exception as e:
self.logger.errorf"切换Agent策略失败 {agent_id}: {e}"
raise

async def _execute_actionself, action: AgentControlAction -> str:
"""执行控制操作"""
try:
# 添加到待处理操作列表
self._pending_actions[action.action_id] = action

action.status = ActionStatus.IN_PROGRESS
action.started_at = datetime.utcnow()

# 根据操作类型执行相应操作
if action.action_type == ControlActionType.START:
await self.coordinator.start_agentaction.agent_id
elif action.action_type == ControlActionType.STOP:
await self.coordinator.stop_agentaction.agent_id
elif action.action_type == ControlActionType.RESTART:
await self.coordinator.stop_agentaction.agent_id
await asyncio.sleep2 # 等待停止完成
await self.coordinator.start_agentaction.agent_id
elif action.action_type == ControlActionType.PAUSE:

await self.message_queue.publish_message(
"agent_control",
{
"action": "pause",
"agent_id": action.agent_id
}
)
elif action.action_type == ControlActionType.RESUME:

await self.message_queue.publish_message(
"agent_control",
{
"action": "resume",
"agent_id": action.agent_id
}
)
elif action.action_type == ControlActionType.UPDATE_PARAMETERS:
# 发送参数更新消息
await self.message_queue.publish_message(
"agent_control",
{
"action": "update_parameters",
"agent_id": action.agent_id,
"parameters": action.parameters
}
)
elif action.action_type == ControlActionType.SWITCH_STRATEGY:
# 发送策略切换消息
await self.message_queue.publish_message(
"agent_control",
{
"action": "switch_strategy",
"agent_id": action.agent_id,
"strategy_id": action.parameters.get"strategy_id"
}
)

self._action_timeouts[action.action_id] = asyncio.create_task(
self._action_timeout_handleraction.action_id
)

if self.config.log_all_actions:
self.logger.infof"执行操作 {action.action_id}: {action.action_type} -> {action.agent_id}"

return action.action_id

except Exception as e:

action.status = ActionStatus.FAILED
action.completed_at = datetime.utcnow()
action.error_message = stre

self._action_history.appendaction
if action.action_id in self._pending_actions:
del self._pending_actions[action.action_id]

self.logger.errorf"执行操作失败 {action.action_id}: {e}"
raise

async def _action_timeout_handlerself, action_id: str:
"""操作超时处理器"""
try:
await asyncio.sleepself.config.action_timeout

# 检查操作是否仍在待处理列表中
if action_id in self._pending_actions:
await self._timeout_actionaction_id

except asyncio.CancelledError:
pass
except Exception as e:
self.logger.errorf"操作超时处理器错误 {action_id}: {e}"

async def get_action_statusself, action_id: str -> Optional[AgentControlAction]:
"""获取操作状态"""
try:

if action_id in self._pending_actions:
return self._pending_actions[action_id]

for action in self._action_history:    if action.action_id == action_id:
return action

return None

except Exception as e:
self.logger.errorf"获取操作状态失败 {action_id}: {e}"
return None

async def get_pending_actionsself -> List[AgentControlAction]:
"""获取所有待处理操作"""
try:
return list(self._pending_actions.values())
except Exception as e:
self.logger.errorf"获取待处理操作失败: {e}"
return []

async def get_action_historyself, agent_id: Optional[str] = None -> List[AgentControlAction]:
"""获取操作历史记录"""
try:
if agent_id:    return [action for action in self._action_history if action.agent_id == agent_id]
else:
return self._action_history.copy()

except Exception as e:
self.logger.errorf"获取操作历史记录失败: {e}"
return []

async def cancel_actionself, action_id: str, reason: str = "用户取消" -> bool:
"""取消操作"""
try:
if action_id not in self._pending_actions:
return False

action = self._pending_actions[action_id]
action.status = ActionStatus.CANCELLED
action.completed_at = datetime.utcnow()
action.error_message = reason

if action_id in self._action_timeouts:
self._action_timeouts[action_id].cancel()
del self._action_timeouts[action_id]

self._action_history.appendaction
del self._pending_actions[action_id]

self.logger.infof"操作已取消 {action_id}: {reason}"
return True

except Exception as e:
self.logger.errorf"取消操作失败 {action_id}: {e}"
return False

def add_action_callbackself, callback: Callable[[str, AgentControlAction], None]:
"""添加操作回调函数"""
self._action_callbacks.appendcallback

def remove_action_callbackself, callback: Callable[[str, AgentControlAction], None]:
"""移除操作回调函数"""
if callback in self._action_callbacks:
self._action_callbacks.removecallback

async def cleanupself:
"""清理资源"""
try:
self.logger.info"正在清理Agent控制服务..."

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

self._pending_actions.clear()
self._action_history.clear()
self._action_callbacks.clear()
self._action_timeouts.clear()

self.logger.info"Agent控制服务清理完成"

except Exception as e:
self.logger.errorf"清理Agent控制服务失败: {e}"

__all__ = [
"AgentControlConfig",
"AgentControlService",
]

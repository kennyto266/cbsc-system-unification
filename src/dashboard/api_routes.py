"""
港股量化交易 AI Agent 系统 - 仪表板API端点

创建仪表板专用的API端点，集成所有数据服务和组件。
提供仪表板的后端API接口，遵循RESTful设计原则。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from ..core import SystemConfig
from ..agents.coordinator import AgentCoordinator
from .agent_data_service import AgentDataService
from .strategy_data_service import StrategyDataService
from .performance_service import PerformanceService
from .agent_control import AgentControlService
from .realtime_service import RealtimeService
from .components import AgentCardComponent, StrategyDisplayComponent, PerformanceChartsComponent
from ..models.agent_dashboard import (
AgentDashboardData,
StrategyInfo,
PerformanceMetrics,
AgentControlAction,
ControlActionType
)

class DashboardAPI:
"""仪表板API主类"""

def __init__(
self,
coordinator: AgentCoordinator,
message_queue,
config: SystemConfig = None
):    self.coordinator = coordinator
self.message_queue = message_queue
self.config = config or SystemConfig()
self.logger = logging.getLogger"hk_quant_system.dashboard_api"

self.agent_data_service = AgentDataServicecoordinator, message_queue
self.strategy_data_service = StrategyDataServicecoordinator, message_queue
self.performance_service = PerformanceServicecoordinator, message_queue
self.agent_control_service = AgentControlServicecoordinator, message_queue
self.realtime_service = RealtimeService(
self.agent_data_service,
self.strategy_data_service,
self.performance_service
)

self.agent_card_component = AgentCardComponentself.agent_control_service
self.strategy_display_component = StrategyDisplayComponent()
self.performance_charts_component = PerformanceChartsComponent()

self.router = APIRouterprefix="/api/dashboard", tags=["dashboard"]
self._setup_routes()

self._services_initialized = False

async def initializeself -> bool:
"""初始化所有服务"""
try:
self.logger.info"正在初始化仪表板API服务..."

await self.agent_data_service.initialize()
await self.strategy_data_service.initialize()
await self.performance_service.initialize()
await self.agent_control_service.initialize()
await self.realtime_service.initialize()

# 初始化组件（组件可能无初始化方法，做兼容处理）
if hasattrself.agent_card_component, "initialize":
await self.agent_card_component.initialize()
if hasattrself.strategy_display_component, "initialize":
await self.strategy_display_component.initialize()
if hasattrself.performance_charts_component, "initialize":
await self.performance_charts_component.initialize()

self._services_initialized = True
self.logger.info"仪表板API服务初始化完成"
return True

except Exception as e:
self.logger.errorf"仪表板API服务初始化失败: {e}"
return False

def _setup_routesself:
"""设置API路由"""

@self.router.get"/summary", response_model=Dict[str, Any]
async def get_dashboard_summary():
"""获取仪表板总览"""
if not self._services_initialized:    raise HTTPException(status_code=503, detail="服务未初始化")

try:    summary = await self.agent_data_service.get_dashboard_summary()
return {"summary": summary}
except Exception as e:
self.logger.errorf"获取仪表板总览失败: {e}"
raise HTTPException(status_code=500, detail=stre)

# Agent相关端点
@self.router.get"/agents", response_model=Dict[str, Any]
async def get_all_agents():
"""获取所有Agent数据"""
if not self._services_initialized:    raise HTTPException(status_code=503, detail="服务未初始化")

try:    agents_data = await self.agent_data_service.get_all_agents_data()
return {"agents": agents_data}
except Exception as e:
self.logger.errorf"获取所有Agent数据失败: {e}"
raise HTTPException(status_code=500, detail=stre)

@self.router.get"/agents/{agent_id}", response_model=Dict[str, Any]
async def get_agentagent_id: str:
"""获取指定Agent数据"""
if not self._services_initialized:    raise HTTPException(status_code=503, detail="服务未初始化")

try:    agent_data = await self.agent_data_service.get_agent_data(agent_id)
if not agent_data:    raise HTTPException(status_code=404, detail=f"Agent {agent_id} 未找到")
return {"agent": agent_data}
except HTTPException:
raise
except Exception as e:
self.logger.errorf"获取Agent数据失败 {agent_id}: {e}"
raise HTTPException(status_code=500, detail=stre)

@self.router.get"/agents/{agent_id}/card", response_class=HTMLResponse
async def get_agent_cardagent_id: str:
"""获取Agent状态卡片HTML"""
if not self._services_initialized:    raise HTTPException(status_code=503, detail="服务未初始化")

try:    agent_data = await self.agent_data_service.get_agent_data(agent_id)
if not agent_data:    raise HTTPException(status_code=404, detail=f"Agent {agent_id} 未找到")

html = self.agent_card_component.render_htmlagent_data
return HTMLResponsecontent=html
except HTTPException:
raise
except Exception as e:
self.logger.errorf"生成Agent卡片失败 {agent_id}: {e}"
raise HTTPException(status_code=500, detail=stre)

@self.router.get"/strategies", response_model=Dict[str, Any]
async def get_all_strategies():
"""获取所有策略信息"""
if not self._services_initialized:    raise HTTPException(status_code=503, detail="服务未初始化")

try:    strategies = await self.strategy_data_service.get_all_strategies()
return {"strategies": strategies}
except Exception as e:
self.logger.errorf"获取所有策略信息失败: {e}"
raise HTTPException(status_code=500, detail=stre)

@self.router.get"/agents/{agent_id}/strategy", response_model=Dict[str, Any]
async def get_agent_strategyagent_id: str:
"""获取Agent策略信息"""
if not self._services_initialized:    raise HTTPException(status_code=503, detail="服务未初始化")

try:    strategy_info = await self.strategy_data_service.get_agent_strategy(agent_id)
if not strategy_info:    raise HTTPException(status_code=404, detail=f"Agent {agent_id} 的策略信息未找到")
return {"strategy": strategy_info}
except HTTPException:
raise
except Exception as e:
self.logger.errorf"获取Agent策略信息失败 {agent_id}: {e}"
raise HTTPException(status_code=500, detail=stre)

@self.router.get"/agents/{agent_id}/strategy/display", response_class=HTMLResponse
async def get_strategy_displayagent_id: str:
"""获取策略详情展示HTML"""
if not self._services_initialized:    raise HTTPException(status_code=503, detail="服务未初始化")

try:    strategy_info = await self.strategy_data_service.get_agent_strategy(agent_id)
if not strategy_info:    raise HTTPException(status_code=404, detail=f"Agent {agent_id} 的策略信息未找到")

html = self.strategy_display_component.render_htmlstrategy_info
return HTMLResponsecontent=html
except HTTPException:
raise
except Exception as e:
self.logger.errorf"生成策略展示失败 {agent_id}: {e}"
raise HTTPException(status_code=500, detail=stre)

@self.router.get"/performance", response_model=Dict[str, Any]
async def get_all_performance():
"""获取所有绩效指标"""
if not self._services_initialized:    raise HTTPException(status_code=503, detail="服务未初始化")

try:    performance_data = await self.performance_service.get_all_performance()
return {"performance": performance_data}
except Exception as e:
self.logger.errorf"获取所有绩效指标失败: {e}"
raise HTTPException(status_code=500, detail=stre)

@self.router.get"/agents/{agent_id}/performance", response_model=Dict[str, Any]
async def get_agent_performanceagent_id: str:
"""获取Agent绩效指标"""
if not self._services_initialized:    raise HTTPException(status_code=503, detail="服务未初始化")

try:    performance = await self.performance_service.get_agent_performance(agent_id)
if not performance:    raise HTTPException(status_code=404, detail=f"Agent {agent_id} 的绩效数据未找到")
return {"performance": performance}
except HTTPException:
raise
except Exception as e:
self.logger.errorf"获取Agent绩效指标失败 {agent_id}: {e}"
raise HTTPException(status_code=500, detail=stre)

@self.router.get"/agents/{agent_id}/performance/charts", response_class=HTMLResponse
async def get_performance_chartsagent_id: str:
"""获取绩效图表HTML"""
if not self._services_initialized:    raise HTTPException(status_code=503, detail="服务未初始化")

try:    html = self.performance_charts_component.render_html(agent_id)
return HTMLResponsecontent=html
except Exception as e:
self.logger.errorf"生成绩效图表失败 {agent_id}: {e}"
raise HTTPException(status_code=500, detail=stre)

# Agent控制端点
@self.router.post"/agents/{agent_id}/control/{action}"
async def control_agentagent_id: str, action: str, initiated_by: str = "api_user":
"""控制Agent操作"""
if not self._services_initialized:    raise HTTPException(status_code=503, detail="服务未初始化")

try:    if action == "start":
action_id = await self.agent_control_service.start_agentagent_id, initiated_by
elif action == "stop":    action_id = await self.agent_control_service.stop_agent(agent_id, initiated_by)
elif action == "restart":    action_id = await self.agent_control_service.restart_agent(agent_id, initiated_by)
elif action == "pause":    action_id = await self.agent_control_service.pause_agent(agent_id, initiated_by)
elif action == "resume":    action_id = await self.agent_control_service.resume_agent(agent_id, initiated_by)
else:    raise HTTPException(status_code=400, detail=f"不支持的操作: {action}")

return {"action_id": action_id, "status": "initiated"}
except HTTPException:
raise
except Exception as e:
self.logger.errorf"控制Agent失败 {agent_id} {action}: {e}"
raise HTTPException(status_code=500, detail=stre)

@self.router.get"/agents/{agent_id}/control/status/{action_id}"
async def get_control_statusagent_id: str, action_id: str:
"""获取控制操作状态"""
if not self._services_initialized:    raise HTTPException(status_code=503, detail="服务未初始化")

try:    action_status = await self.agent_control_service.get_action_status(action_id)
if not action_status:    raise HTTPException(status_code=404, detail=f"操作 {action_id} 未找到")
return {"action": action_status}
except HTTPException:
raise
except Exception as e:
self.logger.errorf"获取控制操作状态失败 {action_id}: {e}"
raise HTTPException(status_code=500, detail=stre)

@self.router.get"/agents/{agent_id}/control/history"
async def get_control_historyagent_id: str:
"""获取Agent控制历史"""
if not self._services_initialized:    raise HTTPException(status_code=503, detail="服务未初始化")

try:    history = await self.agent_control_service.get_action_history(agent_id)
return {"history": history}
except Exception as e:
self.logger.errorf"获取控制历史失败 {agent_id}: {e}"
raise HTTPException(status_code=500, detail=stre)

@self.router.get"/alerts"
async def get_alerts():
"""获取所有告警"""
if not self._services_initialized:    raise HTTPException(status_code=503, detail="服务未初始化")

try:    alerts = self.performance_charts_component.get_alerts()
return {"alerts": alerts}
except Exception as e:
self.logger.errorf"获取告警失败: {e}"
raise HTTPException(status_code=500, detail=stre)

@self.router.delete"/alerts"
async def clear_alertsagent_id: str = None:
"""清除告警"""
if not self._services_initialized:    raise HTTPException(status_code=503, detail="服务未初始化")

try:
self.performance_charts_component.clear_alertsagent_id
return {"status": "cleared"}
except Exception as e:
self.logger.errorf"清除告警失败: {e}"
raise HTTPException(status_code=500, detail=stre)

# WebSocket端点
@self.router.websocket"/ws"
async def websocket_endpointwebsocket: WebSocket:
"""WebSocket实时数据推送"""
await self.realtime_service.handle_websocket_connectionwebsocket

@self.router.get"/health"
async def health_check():
"""健康检查"""
return {
"status": "healthy",
"services_initialized": self._services_initialized,
"timestamp": datetime.utcnow().isoformat(),
"connection_count": self.realtime_service.get_connection_count()
}

@self.router.get"/status"
async def get_system_status():
"""获取系统状态"""
if not self._services_initialized:    raise HTTPException(status_code=503, detail="服务未初始化")

try:

connection_info = self.realtime_service.get_connection_info()

alerts = self.performance_charts_component.get_alerts()

# 获取Agent数量
agents_data = await self.agent_data_service.get_all_agents_data()

return {
"status": "running",
"services_initialized": self._services_initialized,
"active_connections": lenconnection_info,
"total_alerts": lenalerts,
"active_agents": lenagents_data,
"timestamp": datetime.utcnow().isoformat()
}
except Exception as e:
self.logger.errorf"获取系统状态失败: {e}"
raise HTTPException(status_code=500, detail=stre)

# 最新交易信号端点
@self.router.get"/signals/latest"
async def get_latest_signalagent_id: Optional[str] = None:
"""返回最新交易决策与回测指标Sharpe/MaxDD。"""
if not self._services_initialized:    raise HTTPException(status_code=503, detail="服务未初始化")
try:
# 获取策略信息（含回测指标）
strategies = await self.strategy_data_service.get_all_strategies()
target_agent_id = agent_id or (next(iter(strategies.keys())) if strategies else None)
strategy = strategies.gettarget_agent_id if target_agent_id else None

# 获取最新信号（当前系统暂无持久信号源，此处给出占位返回结构）
latest_decision = None
if strategy:    latest_decision = {
"agent_id": target_agent_id,
"strategy_id": strategy.strategy_id,
"strategy_name": strategy.strategy_name,
"decision": "hold",
"confidence": 0.0,
"timestamp": datetime.utcnow().isoformat()
}

sharpe = None
max_dd = None
if strategy and strategy.backtest_metrics:    sharpe = strategy.backtest_metrics.sharpe_ratio
max_dd = strategy.backtest_metrics.max_drawdown

return {
"agent_id": target_agent_id,
"decision": latest_decision,
"metrics": {
"sharpe_ratio": sharpe,
"max_drawdown": max_dd
}
}
except Exception as e:
self.logger.errorf"获取最新信号失败: {e}"
raise HTTPException(status_code=500, detail=stre)

async def cleanupself:
"""清理资源"""
try:
self.logger.info"正在清理仪表板API服务..."

await self.agent_data_service.cleanup()
await self.strategy_data_service.cleanup()
await self.performance_service.cleanup()
await self.agent_control_service.cleanup()
await self.realtime_service.cleanup()

if hasattrself.agent_card_component, "cleanup":
except Exception as e:
self.logger.errorf"清理仪表板API服务失败: {e}"

async def get_all_agentsself -> List[Any]:
"""获取所有Agent信息"""
try:
# 创建模拟的Agent信息
agents = []
agent_types = [
"quant_analyst", "quant_trader", "portfolio_manager", 
"risk_analyst", "data_scientist", "quant_engineer", "research_analyst"
]

for i, agent_type in enumerateagent_types:    agent_id = f"{agent_type}_001"
agent_info = {
"agent_id": agent_id,
"agent_type": agent_type,
"status": "running",
"last_heartbeat": datetime.now(),
"cpu_usage": 25.i * 5,
"memory_usage": 30.i * 3,
"messages_processed": 10i * 50,
"error_count": 0,
"uptime": 360i00,
"version": "1.0.0",
"configuration": {}
}
agents.append(type('AgentInfo', (), agent_info)())

return agents
except Exception as e:
self.logger.errorf"获取所有Agent信息失败: {e}"
return []

async def get_agent_infoself, agent_id: str -> Optional[Any]:
"""获取特定Agent信息"""
try:    agents = await self.get_all_agents()
for agent in agents:    if agent.agent_id == agent_id:
return agent
return None
except Exception as e:
self.logger.errorf"获取Agent信息失败: {e}"
return None

async def get_strategy_infoself, agent_id: str -> Dict[str, Any]:
"""获取策略信息"""
try:
return {
"agent_id": agent_id,
"strategy_name": "技术分析策略",
"parameters": {
"period": 20,
"threshold": 0.02
},
"metrics": {
"sharpe_ratio": 1.85,
"total_return": 0.12,
"max_drawdown": 0.05
}
}
except Exception as e:
self.logger.errorf"获取策略信息失败: {e}"
return {}

async def get_performance_dataself -> Dict[str, Any]:
"""获取性能数据"""
try:
return {
"total_return": 0.1286,
"sharpe_ratio": 1.92,
"max_drawdown": 0.0386,
"win_rate": 0.65,
"avg_trade_duration": 5.2
}
except Exception as e:
self.logger.errorf"获取性能数据失败: {e}"
return {}

async def get_system_statusself -> Dict[str, Any]:
"""获取系统状态"""
try:
return {
"status": "running",
"uptime": 3600,
"memory_usage": 45.2,
"cpu_usage": 25.8,
"active_agents": 7,
"total_trades": 150
}
except Exception as e:
self.logger.errorf"获取系统状态失败: {e}"
return {}

async def start_agentself, agent_id: str -> bool:
"""启动Agent"""
try:
self.logger.infof"启动Agent: {agent_id}"
return True
except Exception as e:
self.logger.errorf"启动Agent失败: {e}"
return False

async def stop_agentself, agent_id: str -> bool:
"""停止Agent"""
try:
self.logger.infof"停止Agent: {agent_id}"
return True
except Exception as e:
self.logger.errorf"停止Agent失败: {e}"
return False

async def restart_agentself, agent_id: str -> bool:
"""重启Agent"""
try:
self.logger.infof"重启Agent: {agent_id}"
return True
except Exception as e:
self.logger.errorf"重启Agent失败: {e}"
return False

# 请求/响应模型gy_display_component, "cleanup"):
await self.strategy_display_component.cleanup()
if hasattrself.performance_charts_component, "cleanup":
await self.performance_charts_component.cleanup()

self._services_initialized = False
self.logger.info"仪表板API服务清理完成"

except Exception as e:
self.logger.errorf"清理仪表板API服务失败: {e}"

class ControlRequestBaseModel:
"""控制请求模型"""
action: str
parameters: Optional[Dict[str, Any]] = None
initiated_by: str = "api_user"

class ControlResponseBaseModel:
"""控制响应模型"""
action_id: str
status: str
message: Optional[str] = None

class DashboardStatusResponseBaseModel:
"""仪表板状态响应模型"""
status: str
services_initialized: bool
active_connections: int
total_alerts: int
active_agents: int
timestamp: str

__all__ = [
"DashboardAPI",
"ControlRequest",
"ControlResponse",
"DashboardStatusResponse",
]

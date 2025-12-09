"""
路由处理器

负责处理HTTP路由和API端点
"""

import logging
from typing import Any, Dict, Optional

from fastapi import Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse

from .api_routes import DashboardAPI
from .html_generator import HTMLGenerator
from .websocket_manager import WebSocketManager


class RouteHandler:
    """路由处理器"""

    def __init__(
        self, dashboard_api: DashboardAPI, websocket_manager: WebSocketManager
    ):
        self.dashboard_api = dashboard_api
        self.websocket_manager = websocket_manager
        self.html_generator = HTMLGenerator()
        self.logger = logging.getLogger("hk_quant_system.route_handler")

    async def dashboard_home(self, request: Request) -> HTMLResponse:
        """仪表板主页"""
        try:
            # 获取Agent数据
            agent_data = await self._get_agent_data()
            html_content = self.html_generator.get_dashboard_html(agent_data)
            return HTMLResponse(content=html_content)
        except Exception as e:
            self.logger.error(f"生成仪表板主页失败: {e}")
            return HTMLResponse(content="<h1>仪表板加载失败</h1>", status_code=500)

    async def agent_detail(self, request: Request, agent_id: str) -> HTMLResponse:
        """Agent详情页面"""
        try:
            # 获取特定Agent数据
            agent_data = await self._get_agent_data(agent_id)
            html_content = self.html_generator.get_agent_detail_html(
                agent_id, agent_data
            )
            return HTMLResponse(content=html_content)
        except Exception as e:
            self.logger.error(f"生成Agent详情页面失败: {e}")
            return HTMLResponse(content="<h1>Agent详情加载失败</h1>", status_code=500)

    async def strategy_detail(self, request: Request, agent_id: str) -> HTMLResponse:
        """策略详情页面"""
        try:
            # 获取策略数据
            strategy_data = await self._get_strategy_data(agent_id)
            html_content = self.html_generator.get_strategy_detail_html(
                agent_id, strategy_data
            )
            return HTMLResponse(content=html_content)
        except Exception as e:
            self.logger.error(f"生成策略详情页面失败: {e}")
            return HTMLResponse(content="<h1>策略详情加载失败</h1>", status_code=500)

    async def performance_analysis(self, request: Request) -> HTMLResponse:
        """绩效分析页面"""
        try:
            html_content = self.html_generator.get_performance_html()
            return HTMLResponse(content=html_content)
        except Exception as e:
            self.logger.error(f"生成绩效分析页面失败: {e}")
            return HTMLResponse(
                content="<h1>绩效分析页面加载失败</h1>", status_code=500
            )

    async def system_status(self, request: Request) -> HTMLResponse:
        """系统状态页面"""
        try:
            html_content = self.html_generator.get_system_status_html()
            return HTMLResponse(content=html_content)
        except Exception as e:
            self.logger.error(f"生成系统状态页面失败: {e}")
            return HTMLResponse(
                content="<h1>系统状态页面加载失败</h1>", status_code=500
            )

    async def api_proxy(self, path: str, request: Request) -> JSONResponse:
        """API代理"""
        try:
            # 将请求转发到DashboardAPI
            if path.startswith("agents/"):
                return await self._handle_agent_api(path, request)
            elif path.startswith("performance/"):
                return await self._handle_performance_api(path, request)
            elif path.startswith("system/"):
                return await self._handle_system_api(path, request)
            else:
                return JSONResponse(content={"error": "未知的API端点"}, status_code=404)
        except Exception as e:
            self.logger.error(f"API代理处理失败: {e}")
            return JSONResponse(content={"error": "服务器内部错误"}, status_code=500)

    async def websocket_endpoint(self, websocket: WebSocket) -> None:
        """WebSocket端点"""
        await self.websocket_manager.connect(websocket)
        try:
            while True:
                # 接收客户端消息
                data = await websocket.receive_text()
                await self.websocket_manager.handle_client_message(websocket, data)
        except WebSocketDisconnect:
            await self.websocket_manager.disconnect(websocket)
        except Exception as e:
            self.logger.error(f"WebSocket处理异常: {e}")
            await self.websocket_manager.disconnect(websocket)

    async def _get_agent_data(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """获取Agent数据"""
        try:
            if agent_id:
                # 获取特定Agent数据
                agent_info = await self.dashboard_api.get_agent_info(agent_id)
                return {agent_id: agent_info} if agent_info else {}
            else:
                # 获取所有Agent数据
                agents = await self.dashboard_api.get_all_agents()
                return {agent.agent_id: agent.dict() for agent in agents}
        except Exception as e:
            self.logger.error(f"获取Agent数据失败: {e}")
            return {}

    async def _get_strategy_data(self, agent_id: str) -> Dict[str, Any]:
        """获取策略数据"""
        try:
            strategy_info = await self.dashboard_api.get_strategy_info(agent_id)
            return strategy_info if strategy_info else {}
        except Exception as e:
            self.logger.error(f"获取策略数据失败: {e}")
            return {}

    async def _handle_agent_api(self, path: str, request: Request) -> JSONResponse:
        """处理Agent相关API"""
        try:
            if request.method == "GET":
                if path == "agents":
                    agents = await self.dashboard_api.get_all_agents()
                    return JSONResponse(content=[agent.dict() for agent in agents])
                elif path.startswith("agents/"):
                    agent_id = path.split("/")[1]
                    if len(path.split("/")) == 2:
                        # GET /agents/{agent_id}
                        agent_info = await self.dashboard_api.get_agent_info(agent_id)
                        if agent_info:
                            return JSONResponse(content=agent_info.dict())
                        else:
                            return JSONResponse(
                                content={"error": "Agent不存在"}, status_code=404
                            )
                    else:
                        # GET /agents/{agent_id}/...
                        action = path.split("/")[2]
                        if action == "strategy":
                            strategy_info = await self.dashboard_api.get_strategy_info(
                                agent_id
                            )
                            return JSONResponse(content=strategy_info)
                        else:
                            return JSONResponse(
                                content={"error": "未知操作"}, status_code=400
                            )

            elif request.method == "POST":
                if path.startswith("agents/"):
                    parts = path.split("/")
                    if len(parts) >= 3:
                        agent_id = parts[1]
                        action = parts[2]

                        if action == "start":
                            success = await self.dashboard_api.start_agent(agent_id)
                            return JSONResponse(content={"success": success})
                        elif action == "stop":
                            success = await self.dashboard_api.stop_agent(agent_id)
                            return JSONResponse(content={"success": success})
                        elif action == "restart":
                            success = await self.dashboard_api.restart_agent(agent_id)
                            return JSONResponse(content={"success": success})
                        else:
                            return JSONResponse(
                                content={"error": "未知操作"}, status_code=400
                            )

            return JSONResponse(content={"error": "不支持的HTTP方法"}, status_code=405)

        except Exception as e:
            self.logger.error(f"处理Agent API失败: {e}")
            return JSONResponse(content={"error": "服务器内部错误"}, status_code=500)

    async def _handle_performance_api(
        self, path: str, request: Request
    ) -> JSONResponse:
        """处理绩效相关API"""
        try:
            if path == "performance":
                performance_data = await self.dashboard_api.get_performance_data()
                return JSONResponse(content=performance_data)
            else:
                return JSONResponse(
                    content={"error": "未知的绩效API端点"}, status_code=404
                )
        except Exception as e:
            self.logger.error(f"处理绩效API失败: {e}")
            return JSONResponse(content={"error": "服务器内部错误"}, status_code=500)

    async def _handle_system_api(self, path: str, request: Request) -> JSONResponse:
        """处理系统相关API"""
        try:
            if path == "system / status":
                system_status = await self.dashboard_api.get_system_status()
                return JSONResponse(content=system_status)
            elif path == "system / health":
                health_status = await self.dashboard_api.get_health_status()
                return JSONResponse(content=health_status)
            else:
                return JSONResponse(
                    content={"error": "未知的系统API端点"}, status_code=404
                )
        except Exception as e:
            self.logger.error(f"处理系统API失败: {e}")
            return JSONResponse(content={"error": "服务器内部错误"}, status_code=500)

"""
港股量化交易 AI Agent 系统 - 仪表板前端界面

重构后的仪表板UI，使用模块化设计，提高可维护性和可测试性。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, WebSocket

from ..core import SystemConfig
from .api_routes import DashboardAPI
from .html_generator import HTMLGenerator
from .route_handler import RouteHandler
from .websocket_manager import WebSocketManager


class DashboardUI:
    """仪表板前端界面 - 重构版本"""

    def __init__(self, dashboard_api: DashboardAPI, config: SystemConfig = None):
        self.dashboard_api = dashboard_api
        self.config = config or SystemConfig()
        self.logger = logging.getLogger("hk_quant_system.dashboard_ui")

        # 初始化组件
        self.html_generator = HTMLGenerator()
        self.websocket_manager = WebSocketManager()
        self.route_handler = RouteHandler(dashboard_api, self.websocket_manager)

        # 创建FastAPI应用
        self.app = FastAPI(
            title="港股量化交易 AI Agent 仪表板",
            description="实时监控和管理7个AI Agent的量化交易系统",
            version="1.0.0",
        )

        # 设置路由
        self._setup_routes()

        # 数据缓存
        self._cached_data: Dict[str, Any] = {}
        self._last_update: Dict[str, datetime] = {}

        # 后台任务
        self._update_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._running = False

    def _setup_routes(self):
        """设置前端路由"""

        # 主仪表板页面
        @self.app.get("/")
        async def dashboard_home(request: Request):
            """仪表板主页"""
            return await self.route_handler.dashboard_home(request)

        # Agent详情页面
        @self.app.get("/agent/{agent_id}")
        async def agent_detail(request: Request, agent_id: str):
            """Agent详情页面"""
            return await self.route_handler.agent_detail(request, agent_id)

        # 策略详情页面
        @self.app.get("/agent/{agent_id}/strategy")
        async def strategy_detail(request: Request, agent_id: str):
            """策略详情页面"""
            return await self.route_handler.strategy_detail(request, agent_id)

        # 绩效分析页面
        @self.app.get("/performance")
        async def performance_analysis(request: Request):
            """绩效分析页面"""
            return await self.route_handler.performance_analysis(request)

        # 系统状态页面
        @self.app.get("/system")
        async def system_status(request: Request):
            """系统状态页面"""
            return await self.route_handler.system_status(request)

        # API代理端点
        @self.app.api_route(
            "/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"]
        )
        async def api_proxy(path: str, request: Request):
            """API代理"""
            return await self.route_handler.api_proxy(path, request)

        # WebSocket端点
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket实时连接"""
            await self.route_handler.websocket_endpoint(websocket)

    async def start(self):
        """启动仪表板服务"""
        try:
            self.logger.info("启动仪表板服务...")
            self._running = True

            # 启动数据更新任务
            self._update_task = asyncio.create_task(self._data_update_loop())

            # 启动WebSocket心跳任务
            self._heartbeat_task = asyncio.create_task(
                self.websocket_manager.start_heartbeat_task()
            )

            self.logger.info("仪表板服务启动成功")
            return True

        except Exception as e:
            self.logger.error(f"启动仪表板服务失败: {e}")
            return False

    async def stop(self):
        """停止仪表板服务"""
        try:
            self.logger.info("停止仪表板服务...")
            self._running = False

            # 取消后台任务
            if self._update_task:
                self._update_task.cancel()
                try:
                    await self._update_task
                except asyncio.CancelledError:
                    pass

            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass

            self.logger.info("仪表板服务已停止")

        except Exception as e:
            self.logger.error(f"停止仪表板服务失败: {e}")

    async def _data_update_loop(self):
        """数据更新循环"""
        while self._running:
            try:
                # 获取最新数据
                await self._update_cached_data()

                # 通过WebSocket推送更新
                await self._broadcast_updates()

                # 等待下次更新
                await asyncio.sleep(self.config.update_interval or 5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"数据更新循环异常: {e}")
                await asyncio.sleep(5)

    async def _update_cached_data(self):
        """更新缓存数据"""
        try:
            # 获取所有Agent数据
            agents = await self.dashboard_api.get_all_agents()
            agent_data = {agent.agent_id: agent.dict() for agent in agents}

            # 更新缓存
            self._cached_data["agents"] = agent_data
            self._last_update["agents"] = datetime.now()

            # 获取系统状态
            system_status = await self.dashboard_api.get_system_status()
            self._cached_data["system"] = system_status
            self._last_update["system"] = datetime.now()

        except Exception as e:
            self.logger.error(f"更新缓存数据失败: {e}")

    async def _broadcast_updates(self):
        """广播数据更新"""
        try:
            if "agents" in self._cached_data:
                await self.websocket_manager.send_agent_update(
                    "all", self._cached_data["agents"]
                )

            if "system" in self._cached_data:
                await self.websocket_manager.send_performance_data(
                    self._cached_data["system"]
                )

        except Exception as e:
            self.logger.error(f"广播更新失败: {e}")

    def get_cached_data(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        return self._cached_data.get(key)

    def is_data_fresh(self, key: str, max_age_seconds: int = 60) -> bool:
        """检查数据是否新鲜"""
        if key not in self._last_update:
            return False

        age = (datetime.now() - self._last_update[key]).total_seconds()
        return age <= max_age_seconds

    def get_connection_count(self) -> int:
        """获取WebSocket连接数"""
        return self.websocket_manager.get_connection_count()

    def get_connection_info(self) -> List[Dict[str, Any]]:
        """获取连接信息"""
        return self.websocket_manager.get_connection_info()

    async def send_alert(self, alert_type: str, message: str, severity: str = "info"):
        """发送系统告警"""
        await self.websocket_manager.send_system_alert(alert_type, message, severity)

    async def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("开始清理DashboardUI资源...")

            # 停止后台任务
            await self.stop()

            # 清理WebSocket连接
            if hasattr(self.websocket_manager, "active_connections"):
                for connection in self.websocket_manager.active_connections:
                    try:
                        await connection.close()
                    except Exception:
                        pass
                self.websocket_manager.active_connections.clear()

            # 清理缓存
            self._cached_data.clear()
            self._last_update.clear()

            self.logger.info("DashboardUI资源清理完成")

        except Exception as e:
            self.logger.error(f"清理DashboardUI资源失败: {e}")

    def get_app(self) -> FastAPI:
        """获取FastAPI应用实例"""
        return self.app

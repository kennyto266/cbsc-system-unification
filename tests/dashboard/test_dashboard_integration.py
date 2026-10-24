"""
港股量化交易 AI Agent 系统 - 仪表板集成测试

编写仪表板与Agent系统的集成测试，测试端到端的数据流和用户交互。
确保仪表板与现有系统的正确集成。
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.core import SystemConfig
from src.core.message_queue import MessageQueue
from src.agents.coordinator import AgentCoordinator
from src.dashboard.api_routes import DashboardAPI
from src.dashboard.dashboard_ui import DashboardUI
from src.models.agent_dashboard import (
    AgentDashboardData,
    StrategyInfo,
    StrategyType,
    StrategyStatus,
    PerformanceMetrics,
    PerformancePeriod,
    AgentStatus
)


class TestDashboardAgentIntegration:
    """仪表板与Agent系统集成测试"""
    
    @pytest.fixture
    async def mock_coordinator(self):
        """创建模拟的AgentCoordinator"""
        coordinator = Mock(spec=AgentCoordinator)
        coordinator.get_agent_status = AsyncMock()
        coordinator.get_all_agent_statuses = AsyncMock()
        coordinator.start_agent = AsyncMock()
        coordinator.stop_agent = AsyncMock()
        coordinator.register_agent = AsyncMock()
        coordinator.unregister_agent = AsyncMock()
        
        # 模拟Agent状态
        coordinator.get_all_agent_statuses.return_value = {
            "quant_analyst_001": {
                "agent_type": "QuantitativeAnalyst",
                "status": "running",
                "cpu_usage": 45.0,
                "memory_usage": 55.0,
                "messages_processed": 1500,
                "error_count": 2,
                "uptime_seconds": 7200,
                "version": "1.0.0",
                "configuration": {"param1": "value1"},
                "last_heartbeat": datetime.utcnow(),
                "last_updated": datetime.utcnow()
            },
            "quant_trader_001": {
                "agent_type": "QuantitativeTrader",
                "status": "running",
                "cpu_usage": 60.0,
                "memory_usage": 70.0,
                "messages_processed": 3000,
                "error_count": 1,
                "uptime_seconds": 5400,
                "version": "1.0.0",
                "configuration": {"param2": "value2"},
                "last_heartbeat": datetime.utcnow(),
                "last_updated": datetime.utcnow()
            },
            "portfolio_manager_001": {
                "agent_type": "PortfolioManager",
                "status": "running",
                "cpu_usage": 35.0,
                "memory_usage": 45.0,
                "messages_processed": 800,
                "error_count": 0,
                "uptime_seconds": 9000,
                "version": "1.0.0",
                "configuration": {"param3": "value3"},
                "last_heartbeat": datetime.utcnow(),
                "last_updated": datetime.utcnow()
            }
        }
        
        return coordinator
    
    @pytest.fixture
    async def mock_message_queue(self):
        """创建模拟的MessageQueue"""
        message_queue = Mock(spec=MessageQueue)
        message_queue.subscribe = AsyncMock()
        message_queue.unsubscribe = AsyncMock()
        message_queue.publish_message = AsyncMock()
        message_queue.publish = AsyncMock()
        return message_queue
    
    @pytest.fixture
    async def dashboard_api(self, mock_coordinator, mock_message_queue):
        """创建DashboardAPI实例"""
        api = DashboardAPI(mock_coordinator, mock_message_queue)
        await api.initialize()
        return api
    
    @pytest.fixture
    def dashboard_app(self, dashboard_api):
        """创建FastAPI应用"""
        app = FastAPI()
        app.include_router(dashboard_api.router)
        return app
    
    @pytest.fixture
    def client(self, dashboard_app):
        """创建测试客户端"""
        return TestClient(dashboard_app)
    
    @pytest.mark.asyncio
    async def test_dashboard_api_initialization(self, dashboard_api):
        """测试仪表板API初始化"""
        assert dashboard_api._services_initialized is True
        assert dashboard_api.agent_data_service is not None
        assert dashboard_api.strategy_data_service is not None
        assert dashboard_api.performance_service is not None
        assert dashboard_api.agent_control_service is not None
        assert dashboard_api.realtime_service is not None
    
    @pytest.mark.asyncio
    async def test_agent_data_flow(self, dashboard_api, mock_coordinator):
        """测试Agent数据流"""
        # 获取仪表板总览
        summary = await dashboard_api.agent_data_service.get_dashboard_summary()
        
        assert summary is not None
        assert summary.system_metrics.active_agents == 3
        assert summary.system_metrics.system_cpu_usage == 46.67  # 平均值 (45+60+35)/3
        assert summary.system_metrics.system_memory_usage == 56.67  # 平均值 (55+70+45)/3
        
        # 获取所有Agent数据
        agents_data = await dashboard_api.agent_data_service.get_all_agents_data()
        
        assert isinstance(agents_data, dict)
        assert len(agents_data) == 3
        assert "quant_analyst_001" in agents_data
        assert "quant_trader_001" in agents_data
        assert "portfolio_manager_001" in agents_data
    
    @pytest.mark.asyncio
    async def test_strategy_data_flow(self, dashboard_api, mock_coordinator):
        """测试策略数据流"""
        # 获取单个Agent的策略
        strategy = await dashboard_api.strategy_data_service.get_agent_strategy("quant_analyst_001")
        
        assert strategy is not None
        assert strategy.strategy_type == StrategyType.TREND_FOLLOWING
        assert strategy.strategy_name == "技术分析策略"
        assert strategy.status == StrategyStatus.ACTIVE
        
        # 获取所有策略
        strategies = await dashboard_api.strategy_data_service.get_all_strategies()
        
        assert isinstance(strategies, dict)
        assert len(strategies) == 3
    
    @pytest.mark.asyncio
    async def test_performance_data_flow(self, dashboard_api, mock_coordinator):
        """测试绩效数据流"""
        # 获取单个Agent的绩效
        performance = await dashboard_api.performance_service.get_agent_performance("quant_analyst_001")
        
        # 如果没有历史数据，应该返回None
        assert performance is None or isinstance(performance, PerformanceMetrics)
        
        # 获取所有绩效数据
        all_performance = await dashboard_api.performance_service.get_all_performance()
        
        assert isinstance(all_performance, dict)
    
    @pytest.mark.asyncio
    async def test_agent_control_flow(self, dashboard_api, mock_coordinator):
        """测试Agent控制流"""
        # 测试启动Agent
        action_id = await dashboard_api.agent_control_service.start_agent("test_agent", "test_user")
        
        assert action_id is not None
        assert len(action_id) > 0
        
        # 测试获取操作状态
        action_status = await dashboard_api.agent_control_service.get_action_status(action_id)
        
        assert action_status is not None
        assert action_status.action_id == action_id
        assert action_status.agent_id == "test_agent"
        
        # 测试获取控制历史
        history = await dashboard_api.agent_control_service.get_action_history("test_agent")
        
        assert isinstance(history, list)
        assert len(history) >= 1  # 至少有一个操作记录
    
    def test_api_endpoints(self, client):
        """测试API端点"""
        # 测试健康检查端点
        response = client.get("/api/dashboard/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services_initialized"] is True
        
        # 测试系统状态端点
        response = client.get("/api/dashboard/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["active_agents"] == 3
        
        # 测试获取所有Agent
        response = client.get("/api/dashboard/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 3
        
        # 测试获取特定Agent
        response = client.get("/api/dashboard/agents/quant_analyst_001")
        assert response.status_code == 200
        data = response.json()
        assert "agent" in data
        assert data["agent"]["agent_id"] == "quant_analyst_001"
        
        # 测试获取不存在的Agent
        response = client.get("/api/dashboard/agents/nonexistent_agent")
        assert response.status_code == 404
    
    def test_agent_control_endpoints(self, client):
        """测试Agent控制端点"""
        # 测试启动Agent
        response = client.post("/api/dashboard/agents/test_agent/control/start")
        assert response.status_code == 200
        data = response.json()
        assert "action_id" in data
        assert "status" in data
        
        # 测试停止Agent
        response = client.post("/api/dashboard/agents/test_agent/control/stop")
        assert response.status_code == 200
        
        # 测试重启Agent
        response = client.post("/api/dashboard/agents/test_agent/control/restart")
        assert response.status_code == 200
        
        # 测试无效操作
        response = client.post("/api/dashboard/agents/test_agent/control/invalid")
        assert response.status_code == 400
    
    def test_strategy_endpoints(self, client):
        """测试策略端点"""
        # 测试获取所有策略
        response = client.get("/api/dashboard/strategies")
        assert response.status_code == 200
        data = response.json()
        assert "strategies" in data
        
        # 测试获取Agent策略
        response = client.get("/api/dashboard/agents/quant_analyst_001/strategy")
        assert response.status_code == 200
        data = response.json()
        assert "strategy" in data
        
        # 测试获取不存在的Agent策略
        response = client.get("/api/dashboard/agents/nonexistent_agent/strategy")
        assert response.status_code == 404
    
    def test_performance_endpoints(self, client):
        """测试绩效端点"""
        # 测试获取所有绩效数据
        response = client.get("/api/dashboard/performance")
        assert response.status_code == 200
        data = response.json()
        assert "performance" in data
        
        # 测试获取Agent绩效
        response = client.get("/api/dashboard/agents/quant_analyst_001/performance")
        # 如果没有绩效数据，可能返回404
        assert response.status_code in [200, 404]
    
    def test_html_endpoints(self, client):
        """测试HTML端点"""
        # 测试Agent卡片HTML
        response = client.get("/api/dashboard/agents/quant_analyst_001/card")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "agent-card" in response.text
        
        # 测试策略展示HTML
        response = client.get("/api/dashboard/agents/quant_analyst_001/strategy/display")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        # 测试绩效图表HTML
        response = client.get("/api/dashboard/agents/quant_analyst_001/performance/charts")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestDashboardUIIntegration:
    """仪表板UI集成测试"""
    
    @pytest.fixture
    async def mock_coordinator(self):
        """创建模拟的AgentCoordinator"""
        coordinator = Mock(spec=AgentCoordinator)
        coordinator.get_agent_status = AsyncMock()
        coordinator.get_all_agent_statuses = AsyncMock()
        coordinator.start_agent = AsyncMock()
        coordinator.stop_agent = AsyncMock()
        
        coordinator.get_all_agent_statuses.return_value = {
            "quant_analyst_001": {
                "agent_type": "QuantitativeAnalyst",
                "status": "running",
                "cpu_usage": 45.0,
                "memory_usage": 55.0,
                "messages_processed": 1500,
                "error_count": 2,
                "uptime_seconds": 7200,
                "version": "1.0.0",
                "configuration": {},
                "last_heartbeat": datetime.utcnow(),
                "last_updated": datetime.utcnow()
            }
        }
        
        return coordinator
    
    @pytest.fixture
    async def mock_message_queue(self):
        """创建模拟的MessageQueue"""
        message_queue = Mock(spec=MessageQueue)
        message_queue.subscribe = AsyncMock()
        message_queue.unsubscribe = AsyncMock()
        message_queue.publish_message = AsyncMock()
        return message_queue
    
    @pytest.fixture
    async def dashboard_ui(self, mock_coordinator, mock_message_queue):
        """创建DashboardUI实例"""
        dashboard_api = DashboardAPI(mock_coordinator, mock_message_queue)
        await dashboard_api.initialize()
        
        ui = DashboardUI(dashboard_api)
        await ui.start()
        
        return ui
    
    @pytest.fixture
    def ui_client(self, dashboard_ui):
        """创建UI测试客户端"""
        return TestClient(dashboard_ui.app)
    
    def test_dashboard_home_page(self, ui_client):
        """测试仪表板主页"""
        response = ui_client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        html_content = response.text
        assert "港股量化交易 AI Agent 仪表板" in html_content
        assert "dashboard-container" in html_content
        assert "agents-grid" in html_content
        assert "system-stats" in html_content
    
    def test_agent_detail_page(self, ui_client):
        """测试Agent详情页面"""
        response = ui_client.get("/agent/quant_analyst_001")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        html_content = response.text
        assert "quant_analyst_001" in html_content
        assert "Agent 详情页面" in html_content
    
    def test_strategy_detail_page(self, ui_client):
        """测试策略详情页面"""
        response = ui_client.get("/agent/quant_analyst_001/strategy")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        html_content = response.text
        assert "quant_analyst_001" in html_content
        assert "策略详情" in html_content
    
    def test_performance_page(self, ui_client):
        """测试绩效分析页面"""
        response = ui_client.get("/performance")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        html_content = response.text
        assert "绩效分析" in html_content
    
    def test_system_status_page(self, ui_client):
        """测试系统状态页面"""
        response = ui_client.get("/system")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        html_content = response.text
        assert "系统状态" in html_content


class TestDashboardWebSocketIntegration:
    """仪表板WebSocket集成测试"""
    
    @pytest.fixture
    async def mock_coordinator(self):
        """创建模拟的AgentCoordinator"""
        coordinator = Mock(spec=AgentCoordinator)
        coordinator.get_agent_status = AsyncMock()
        coordinator.get_all_agent_statuses = AsyncMock()
        coordinator.start_agent = AsyncMock()
        coordinator.stop_agent = AsyncMock()
        
        coordinator.get_all_agent_statuses.return_value = {
            "quant_analyst_001": {
                "agent_type": "QuantitativeAnalyst",
                "status": "running",
                "cpu_usage": 45.0,
                "memory_usage": 55.0,
                "messages_processed": 1500,
                "error_count": 2,
                "uptime_seconds": 7200,
                "version": "1.0.0",
                "configuration": {},
                "last_heartbeat": datetime.utcnow(),
                "last_updated": datetime.utcnow()
            }
        }
        
        return coordinator
    
    @pytest.fixture
    async def mock_message_queue(self):
        """创建模拟的MessageQueue"""
        message_queue = Mock(spec=MessageQueue)
        message_queue.subscribe = AsyncMock()
        message_queue.unsubscribe = AsyncMock()
        message_queue.publish_message = AsyncMock()
        return message_queue
    
    @pytest.fixture
    def dashboard_app_with_ws(self, mock_coordinator, mock_message_queue):
        """创建带WebSocket的仪表板应用"""
        dashboard_api = DashboardAPI(mock_coordinator, mock_message_queue)
        dashboard_ui = DashboardUI(dashboard_api)
        
        app = FastAPI()
        app.include_router(dashboard_api.router)
        
        @app.websocket("/ws")
        async def websocket_endpoint(websocket):
            await dashboard_ui._handle_websocket(websocket)
        
        return app
    
    def test_websocket_connection(self, dashboard_app_with_ws):
        """测试WebSocket连接"""
        client = TestClient(dashboard_app_with_ws)
        
        with client.websocket_connect("/ws") as websocket:
            # 测试发送订阅消息
            websocket.send_json({
                "type": "subscribe",
                "subscription_type": "agent_updates"
            })
            
            # 测试发送心跳
            websocket.send_json({
                "type": "ping"
            })
            
            # 应该收到pong响应
            data = websocket.receive_json()
            assert data["type"] == "pong"


class TestDashboardPerformanceIntegration:
    """仪表板性能集成测试"""
    
    @pytest.fixture
    async def mock_coordinator(self):
        """创建模拟的AgentCoordinator"""
        coordinator = Mock(spec=AgentCoordinator)
        coordinator.get_agent_status = AsyncMock()
        coordinator.get_all_agent_statuses = AsyncMock()
        coordinator.start_agent = AsyncMock()
        coordinator.stop_agent = AsyncMock()
        
        # 创建大量Agent数据
        agent_statuses = {}
        for i in range(50):
            agent_statuses[f"agent_{i:03d}"] = {
                "agent_type": "QuantitativeAnalyst",
                "status": "running",
                "cpu_usage": 45.0,
                "memory_usage": 55.0,
                "messages_processed": 1500 + i * 100,
                "error_count": i % 3,
                "uptime_seconds": 7200 + i * 100,
                "version": "1.0.0",
                "configuration": {},
                "last_heartbeat": datetime.utcnow(),
                "last_updated": datetime.utcnow()
            }
        
        coordinator.get_all_agent_statuses.return_value = agent_statuses
        
        return coordinator
    
    @pytest.fixture
    async def mock_message_queue(self):
        """创建模拟的MessageQueue"""
        message_queue = Mock(spec=MessageQueue)
        message_queue.subscribe = AsyncMock()
        message_queue.unsubscribe = AsyncMock()
        message_queue.publish_message = AsyncMock()
        return message_queue
    
    @pytest.mark.asyncio
    async def test_large_dataset_performance(self, mock_coordinator, mock_message_queue):
        """测试大数据集性能"""
        dashboard_api = DashboardAPI(mock_coordinator, mock_message_queue)
        await dashboard_api.initialize()
        
        # 测试获取大量Agent数据的性能
        start_time = datetime.utcnow()
        
        summary = await dashboard_api.agent_data_service.get_dashboard_summary()
        agents_data = await dashboard_api.agent_data_service.get_all_agents_data()
        strategies = await dashboard_api.strategy_data_service.get_all_strategies()
        
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        # 验证数据完整性
        assert summary.system_metrics.active_agents == 50
        assert len(agents_data) == 50
        assert len(strategies) == 50
        
        # 验证性能（应该在合理时间内完成）
        assert execution_time < 5.0  # 5秒内完成
        
        await dashboard_api.cleanup()
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, mock_coordinator, mock_message_queue):
        """测试并发请求性能"""
        dashboard_api = DashboardAPI(mock_coordinator, mock_message_queue)
        await dashboard_api.initialize()
        
        # 创建并发任务
        tasks = []
        for i in range(20):
            task = dashboard_api.agent_data_service.get_dashboard_summary()
            tasks.append(task)
        
        # 执行并发请求
        start_time = datetime.utcnow()
        results = await asyncio.gather(*tasks)
        end_time = datetime.utcnow()
        
        execution_time = (end_time - start_time).total_seconds()
        
        # 验证所有请求都成功
        assert len(results) == 20
        for result in results:
            assert result is not None
            assert result.system_metrics.active_agents == 50
        
        # 验证性能（并发请求应该在合理时间内完成）
        assert execution_time < 3.0  # 3秒内完成
        
        await dashboard_api.cleanup()


class TestDashboardErrorHandling:
    """仪表板错误处理测试"""
    
    @pytest.fixture
    async def mock_coordinator_with_errors(self):
        """创建有错误的模拟AgentCoordinator"""
        coordinator = Mock(spec=AgentCoordinator)
        coordinator.get_agent_status = AsyncMock(side_effect=Exception("Database connection error"))
        coordinator.get_all_agent_statuses = AsyncMock(side_effect=Exception("Network timeout"))
        coordinator.start_agent = AsyncMock(side_effect=Exception("Agent start failed"))
        coordinator.stop_agent = AsyncMock(side_effect=Exception("Agent stop failed"))
        
        return coordinator
    
    @pytest.fixture
    async def mock_message_queue(self):
        """创建模拟的MessageQueue"""
        message_queue = Mock(spec=MessageQueue)
        message_queue.subscribe = AsyncMock(side_effect=Exception("Message queue error"))
        message_queue.unsubscribe = AsyncMock()
        message_queue.publish_message = AsyncMock()
        return message_queue
    
    @pytest.mark.asyncio
    async def test_error_handling_in_services(self, mock_coordinator_with_errors, mock_message_queue):
        """测试服务中的错误处理"""
        dashboard_api = DashboardAPI(mock_coordinator_with_errors, mock_message_queue)
        
        # 初始化应该失败
        result = await dashboard_api.initialize()
        assert result is False
        
        # 即使初始化失败，API应该优雅处理错误
        app = FastAPI()
        app.include_router(dashboard_api.router)
        client = TestClient(app)
        
        # 健康检查应该返回服务未初始化状态
        response = client.get("/api/dashboard/health")
        assert response.status_code == 200
        data = response.json()
        assert data["services_initialized"] is False
    
    def test_api_error_responses(self, mock_coordinator_with_errors, mock_message_queue):
        """测试API错误响应"""
        dashboard_api = DashboardAPI(mock_coordinator_with_errors, mock_message_queue)
        
        app = FastAPI()
        app.include_router(dashboard_api.router)
        client = TestClient(app)
        
        # 测试获取Agent数据时的错误处理
        response = client.get("/api/dashboard/agents")
        assert response.status_code == 503  # Service Unavailable
        
        # 测试获取不存在的Agent
        response = client.get("/api/dashboard/agents/nonexistent_agent")
        assert response.status_code == 404  # Not Found
        
        # 测试无效的控制操作
        response = client.post("/api/dashboard/agents/test_agent/control/invalid_action")
        assert response.status_code == 400  # Bad Request


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

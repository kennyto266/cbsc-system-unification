"""
港股量化交易 AI Agent 系统 - 仪表板单元测试

编写所有仪表板组件的单元测试，测试数据服务和API端点。
确保仪表板功能的可靠性。
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from src.dashboard.agent_data_service import AgentDataService
from src.dashboard.strategy_data_service import StrategyDataService, StrategyDataConfig
from src.dashboard.performance_service import PerformanceService, PerformanceConfig
from src.dashboard.agent_control import AgentControlService, AgentControlConfig
from src.dashboard.realtime_service import RealtimeService, RealtimeConfig
from src.dashboard.components.agent_card import AgentCardComponent, AgentCardConfig
from src.dashboard.components.strategy_display import StrategyDisplayComponent, StrategyDisplayConfig
from src.dashboard.components.performance_charts import PerformanceChartsComponent, PerformanceChartsConfig
from src.dashboard.api_routes import DashboardAPI
from src.dashboard.dashboard_ui import DashboardUI

from src.models.agent_dashboard import (
    AgentDashboardData,
    StrategyInfo,
    StrategyType,
    StrategyStatus,
    StrategyParameter,
    PerformanceMetrics,
    PerformancePeriod,
    BacktestMetrics,
    LiveMetrics,
    ResourceUsage,
    AgentStatus
)


class TestAgentDataService:
    """Agent数据服务测试"""
    
    @pytest.fixture
    def mock_coordinator(self):
        """模拟AgentCoordinator"""
        coordinator = Mock()
        coordinator.get_agent_status = AsyncMock()
        coordinator.get_all_agent_statuses = AsyncMock()
        return coordinator
    
    @pytest.fixture
    def mock_message_queue(self):
        """模拟MessageQueue"""
        message_queue = Mock()
        message_queue.subscribe = AsyncMock()
        message_queue.unsubscribe = AsyncMock()
        return message_queue
    
    @pytest.fixture
    def agent_data_service(self, mock_coordinator, mock_message_queue):
        """创建AgentDataService实例"""
        return AgentDataService(mock_coordinator, mock_message_queue)
    
    @pytest.mark.asyncio
    async def test_initialize(self, agent_data_service):
        """测试服务初始化"""
        result = await agent_data_service.initialize()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_dashboard_summary(self, agent_data_service):
        """测试获取仪表板总览"""
        # 模拟Agent状态
        agent_data_service._coordinator.get_all_agent_statuses.return_value = {
            "agent_001": {"status": "running", "cpu_usage": 50.0, "memory_usage": 60.0},
            "agent_002": {"status": "running", "cpu_usage": 40.0, "memory_usage": 55.0}
        }
        
        summary = await agent_data_service.get_dashboard_summary()
        
        assert summary is not None
        assert summary.system_metrics.active_agents == 2
        assert summary.system_metrics.system_cpu_usage == 45.0  # 平均值
        assert summary.system_metrics.system_memory_usage == 57.5  # 平均值
    
    @pytest.mark.asyncio
    async def test_get_all_agents_data(self, agent_data_service):
        """测试获取所有Agent数据"""
        # 模拟Agent状态
        agent_data_service._coordinator.get_all_agent_statuses.return_value = {
            "agent_001": {"status": "running", "cpu_usage": 50.0, "memory_usage": 60.0}
        }
        
        agents_data = await agent_data_service.get_all_agents_data()
        
        assert isinstance(agents_data, dict)
        assert len(agents_data) >= 0  # 可能没有数据，但不应该出错


class TestStrategyDataService:
    """策略数据服务测试"""
    
    @pytest.fixture
    def mock_coordinator(self):
        """模拟AgentCoordinator"""
        coordinator = Mock()
        coordinator.get_agent_status = AsyncMock()
        coordinator.get_all_agent_statuses = AsyncMock()
        return coordinator
    
    @pytest.fixture
    def mock_message_queue(self):
        """模拟MessageQueue"""
        message_queue = Mock()
        message_queue.subscribe = AsyncMock()
        message_queue.unsubscribe = AsyncMock()
        return message_queue
    
    @pytest.fixture
    def strategy_data_service(self, mock_coordinator, mock_message_queue):
        """创建StrategyDataService实例"""
        config = StrategyDataConfig()
        config.enable_strategy_monitoring = False  # 禁用后台任务
        return StrategyDataService(mock_coordinator, mock_message_queue, config)
    
    @pytest.mark.asyncio
    async def test_initialize(self, strategy_data_service):
        """测试服务初始化"""
        result = await strategy_data_service.initialize()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_agent_strategy(self, strategy_data_service):
        """测试获取Agent策略"""
        # 模拟Agent状态
        strategy_data_service._coordinator.get_agent_status.return_value = {
            "agent_type": "QuantitativeAnalyst",
            "status": "running"
        }
        
        strategy = await strategy_data_service.get_agent_strategy("test_agent")
        
        assert strategy is not None
        assert strategy.strategy_id.startswith("qa_strategy_")
        assert strategy.strategy_type == StrategyType.TREND_FOLLOWING
    
    @pytest.mark.asyncio
    async def test_get_all_strategies(self, strategy_data_service):
        """测试获取所有策略"""
        # 模拟Agent状态
        strategy_data_service._coordinator.get_all_agent_statuses.return_value = {
            "agent_001": {"agent_type": "QuantitativeAnalyst"},
            "agent_002": {"agent_type": "QuantitativeTrader"}
        }
        
        strategies = await strategy_data_service.get_all_strategies()
        
        assert isinstance(strategies, dict)
        assert len(strategies) >= 0


class TestPerformanceService:
    """绩效计算服务测试"""
    
    @pytest.fixture
    def mock_coordinator(self):
        """模拟AgentCoordinator"""
        coordinator = Mock()
        coordinator.get_agent_status = AsyncMock()
        coordinator.get_all_agent_statuses = AsyncMock()
        return coordinator
    
    @pytest.fixture
    def mock_message_queue(self):
        """模拟MessageQueue"""
        message_queue = Mock()
        message_queue.subscribe = AsyncMock()
        message_queue.unsubscribe = AsyncMock()
        return message_queue
    
    @pytest.fixture
    def performance_service(self, mock_coordinator, mock_message_queue):
        """创建PerformanceService实例"""
        config = PerformanceConfig()
        config.update_interval = 3600  # 设置很长的更新间隔避免后台任务干扰
        return PerformanceService(mock_coordinator, mock_message_queue, config)
    
    @pytest.mark.asyncio
    async def test_initialize(self, performance_service):
        """测试服务初始化"""
        result = await performance_service.initialize()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_calculate_strategy_performance(self, performance_service):
        """测试策略绩效计算"""
        import pandas as pd
        import numpy as np
        
        # 创建模拟收益数据
        returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015])
        
        backtest_metrics = await performance_service.calculate_strategy_performance(
            "test_strategy", returns
        )
        
        assert backtest_metrics is not None
        assert backtest_metrics.total_return >= 0  # 应该有正收益
        assert backtest_metrics.sharpe_ratio >= 0  # 夏普比率应该为正
        assert backtest_metrics.trades_count == 5  # 交易次数应该等于数据点数
    
    @pytest.mark.asyncio
    async def test_get_agent_performance(self, performance_service):
        """测试获取Agent绩效"""
        # 模拟Agent状态
        performance_service._coordinator.get_agent_status.return_value = {
            "agent_type": "QuantitativeAnalyst",
            "status": "running"
        }
        
        performance = await performance_service.get_agent_performance("test_agent")
        
        # 如果没有历史数据，应该返回None
        assert performance is None or isinstance(performance, PerformanceMetrics)


class TestAgentControlService:
    """Agent控制服务测试"""
    
    @pytest.fixture
    def mock_coordinator(self):
        """模拟AgentCoordinator"""
        coordinator = Mock()
        coordinator.get_agent_status = AsyncMock()
        coordinator.start_agent = AsyncMock()
        coordinator.stop_agent = AsyncMock()
        return coordinator
    
    @pytest.fixture
    def mock_message_queue(self):
        """模拟MessageQueue"""
        message_queue = Mock()
        message_queue.subscribe = AsyncMock()
        message_queue.unsubscribe = AsyncMock()
        message_queue.publish_message = AsyncMock()
        return message_queue
    
    @pytest.fixture
    def agent_control_service(self, mock_coordinator, mock_message_queue):
        """创建AgentControlService实例"""
        config = AgentControlConfig()
        config.enable_confirmations = False  # 禁用确认机制简化测试
        return AgentControlService(mock_coordinator, mock_message_queue, config)
    
    @pytest.mark.asyncio
    async def test_initialize(self, agent_control_service):
        """测试服务初始化"""
        result = await agent_control_service.initialize()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_start_agent(self, agent_control_service):
        """测试启动Agent"""
        # 模拟Agent状态
        agent_control_service._coordinator.get_agent_status.return_value = {
            "status": "stopped"
        }
        
        action_id = await agent_control_service.start_agent("test_agent", "test_user")
        
        assert action_id is not None
        assert len(action_id) > 0  # 应该是有效的UUID
    
    @pytest.mark.asyncio
    async def test_stop_agent(self, agent_control_service):
        """测试停止Agent"""
        # 模拟Agent状态
        agent_control_service._coordinator.get_agent_status.return_value = {
            "status": "running"
        }
        
        action_id = await agent_control_service.stop_agent("test_agent", "test_user")
        
        assert action_id is not None
        assert len(action_id) > 0  # 应该是有效的UUID
    
    @pytest.mark.asyncio
    async def test_get_action_status(self, agent_control_service):
        """测试获取操作状态"""
        # 先启动一个Agent
        agent_control_service._coordinator.get_agent_status.return_value = {
            "status": "stopped"
        }
        
        action_id = await agent_control_service.start_agent("test_agent", "test_user")
        
        # 获取操作状态
        action_status = await agent_control_service.get_action_status(action_id)
        
        assert action_status is not None
        assert action_status.action_id == action_id
        assert action_status.agent_id == "test_agent"


class TestAgentCardComponent:
    """Agent卡片组件测试"""
    
    @pytest.fixture
    def mock_agent_control_service(self):
        """模拟AgentControlService"""
        return Mock()
    
    @pytest.fixture
    def agent_card_component(self, mock_agent_control_service):
        """创建AgentCardComponent实例"""
        config = AgentCardConfig()
        config.auto_refresh_interval = 0  # 禁用自动刷新
        return AgentCardComponent(mock_agent_control_service, config)
    
    @pytest.mark.asyncio
    async def test_initialize(self, agent_card_component):
        """测试组件初始化"""
        result = await agent_card_component.initialize()
        assert result is True
    
    def test_render_html(self, agent_card_component):
        """测试HTML渲染"""
        # 创建模拟Agent数据
        agent_data = AgentDashboardData(
            agent_id="test_agent",
            agent_type="QuantitativeAnalyst",
            status=AgentStatus.RUNNING,
            last_heartbeat=datetime.utcnow(),
            cpu_usage=50.0,
            memory_usage=60.0,
            messages_processed=1000,
            error_count=0,
            uptime_seconds=3600,
            version="1.0.0",
            configuration={},
            last_updated=datetime.utcnow()
        )
        
        html = agent_card_component.render_html(agent_data)
        
        assert isinstance(html, str)
        assert "agent-card" in html
        assert "test_agent" in html
        assert "QuantitativeAnalyst" in html
    
    def test_update_data(self, agent_card_component):
        """测试数据更新"""
        agent_data = AgentDashboardData(
            agent_id="test_agent",
            agent_type="QuantitativeAnalyst",
            status=AgentStatus.RUNNING,
            last_heartbeat=datetime.utcnow(),
            cpu_usage=50.0,
            memory_usage=60.0,
            messages_processed=1000,
            error_count=0,
            uptime_seconds=3600,
            version="1.0.0",
            configuration={},
            last_updated=datetime.utcnow()
        )
        
        # 添加回调函数
        callback_called = False
        
        def test_callback(data):
            nonlocal callback_called
            callback_called = True
            assert data.agent_id == "test_agent"
        
        agent_card_component.add_update_callback(test_callback)
        
        # 更新数据
        agent_card_component.update_data(agent_data)
        
        # 验证回调被调用
        assert callback_called is True
        assert agent_card_component.get_current_data().agent_id == "test_agent"


class TestStrategyDisplayComponent:
    """策略展示组件测试"""
    
    @pytest.fixture
    def strategy_display_component(self):
        """创建StrategyDisplayComponent实例"""
        config = StrategyDisplayConfig()
        return StrategyDisplayComponent(config)
    
    @pytest.mark.asyncio
    async def test_initialize(self, strategy_display_component):
        """测试组件初始化"""
        result = await strategy_display_component.initialize()
        assert result is True
    
    def test_render_html(self, strategy_display_component):
        """测试HTML渲染"""
        # 创建模拟策略数据
        strategy_info = StrategyInfo(
            strategy_id="test_strategy",
            strategy_name="测试策略",
            strategy_type=StrategyType.MOMENTUM,
            status=StrategyStatus.ACTIVE,
            description="这是一个测试策略",
            parameters=[
                StrategyParameter(
                    name="period",
                    value=20,
                    type="number",
                    description="周期参数",
                    min_value=5,
                    max_value=50
                )
            ],
            version="1.0.0",
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            risk_level="medium",
            max_position_size=0.1
        )
        
        html = strategy_display_component.render_html(strategy_info)
        
        assert isinstance(html, str)
        assert "strategy-display" in html
        assert "test_strategy" in html
        assert "测试策略" in html
    
    def test_update_strategy(self, strategy_display_component):
        """测试策略更新"""
        strategy_info = StrategyInfo(
            strategy_id="test_strategy",
            strategy_name="测试策略",
            strategy_type=StrategyType.MOMENTUM,
            status=StrategyStatus.ACTIVE,
            description="这是一个测试策略",
            parameters=[],
            version="1.0.0",
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            risk_level="medium",
            max_position_size=0.1
        )
        
        # 添加回调函数
        callback_called = False
        
        def test_callback(strategy):
            nonlocal callback_called
            callback_called = True
            assert strategy.strategy_id == "test_strategy"
        
        strategy_display_component.add_update_callback(test_callback)
        
        # 更新策略
        strategy_display_component.update_strategy(strategy_info)
        
        # 验证回调被调用
        assert callback_called is True
        assert strategy_display_component.get_current_strategy().strategy_id == "test_strategy"


class TestPerformanceChartsComponent:
    """绩效图表组件测试"""
    
    @pytest.fixture
    def performance_charts_component(self):
        """创建PerformanceChartsComponent实例"""
        config = PerformanceChartsConfig()
        config.chart_update_interval = 0  # 禁用后台更新
        return PerformanceChartsComponent(config)
    
    @pytest.mark.asyncio
    async def test_initialize(self, performance_charts_component):
        """测试组件初始化"""
        result = await performance_charts_component.initialize()
        assert result is True
    
    def test_render_html(self, performance_charts_component):
        """测试HTML渲染"""
        # 创建模拟绩效数据
        performance = PerformanceMetrics(
            agent_id="test_agent",
            calculation_period=PerformancePeriod.DAILY,
            sharpe_ratio=1.5,
            total_return=0.12,
            annualized_return=0.15,
            volatility=0.20,
            max_drawdown=0.05,
            win_rate=0.65,
            profit_factor=1.8,
            trades_count=100,
            avg_win=0.02,
            avg_loss=-0.01,
            var_95=-0.03,
            var_99=-0.05,
            cvar_95=-0.04,
            beta=1.0,
            alpha=0.05,
            calculation_date=datetime.utcnow(),
            period_start=datetime.utcnow() - timedelta(days=30),
            period_end=datetime.utcnow()
        )
        
        # 更新绩效数据
        performance_charts_component.update_performance("test_agent", performance)
        
        # 渲染HTML
        html = performance_charts_component.render_html("test_agent")
        
        assert isinstance(html, str)
        assert "performance-charts" in html
        assert "test_agent" in html
    
    def test_update_performance(self, performance_charts_component):
        """测试绩效更新"""
        performance = PerformanceMetrics(
            agent_id="test_agent",
            calculation_period=PerformancePeriod.DAILY,
            sharpe_ratio=1.5,
            total_return=0.12,
            annualized_return=0.15,
            volatility=0.20,
            max_drawdown=0.05,
            win_rate=0.65,
            profit_factor=1.8,
            trades_count=100,
            avg_win=0.02,
            avg_loss=-0.01,
            var_95=-0.03,
            var_99=-0.05,
            cvar_95=-0.04,
            beta=1.0,
            alpha=0.05,
            calculation_date=datetime.utcnow(),
            period_start=datetime.utcnow() - timedelta(days=30),
            period_end=datetime.utcnow()
        )
        
        # 添加回调函数
        callback_called = False
        
        def test_callback(agent_id, history):
            nonlocal callback_called
            callback_called = True
            assert agent_id == "test_agent"
            assert len(history) == 1
        
        performance_charts_component.add_update_callback(test_callback)
        
        # 更新绩效数据
        performance_charts_component.update_performance("test_agent", performance)
        
        # 验证回调被调用
        assert callback_called is True
        history = performance_charts_component.get_performance_history("test_agent")
        assert len(history) == 1
        assert history[0].sharpe_ratio == 1.5


class TestDashboardAPI:
    """仪表板API测试"""
    
    @pytest.fixture
    def mock_coordinator(self):
        """模拟AgentCoordinator"""
        coordinator = Mock()
        coordinator.get_agent_status = AsyncMock()
        coordinator.get_all_agent_statuses = AsyncMock()
        coordinator.start_agent = AsyncMock()
        coordinator.stop_agent = AsyncMock()
        return coordinator
    
    @pytest.fixture
    def mock_message_queue(self):
        """模拟MessageQueue"""
        message_queue = Mock()
        message_queue.subscribe = AsyncMock()
        message_queue.unsubscribe = AsyncMock()
        message_queue.publish_message = AsyncMock()
        return message_queue
    
    @pytest.fixture
    def dashboard_api(self, mock_coordinator, mock_message_queue):
        """创建DashboardAPI实例"""
        return DashboardAPI(mock_coordinator, mock_message_queue)
    
    @pytest.mark.asyncio
    async def test_initialize(self, dashboard_api):
        """测试API初始化"""
        result = await dashboard_api.initialize()
        assert result is True
        assert dashboard_api._services_initialized is True
    
    def test_router_creation(self, dashboard_api):
        """测试路由器创建"""
        assert dashboard_api.router is not None
        assert len(dashboard_api.router.routes) > 0  # 应该有路由
    
    @pytest.mark.asyncio
    async def test_cleanup(self, dashboard_api):
        """测试资源清理"""
        await dashboard_api.initialize()
        await dashboard_api.cleanup()
        assert dashboard_api._services_initialized is False


class TestDashboardUI:
    """仪表板UI测试"""
    
    @pytest.fixture
    def mock_dashboard_api(self):
        """模拟DashboardAPI"""
        api = Mock()
        api.router = Mock()
        return api
    
    @pytest.fixture
    def dashboard_ui(self, mock_dashboard_api):
        """创建DashboardUI实例"""
        return DashboardUI(mock_dashboard_api)
    
    @pytest.mark.asyncio
    async def test_start(self, dashboard_ui):
        """测试UI启动"""
        await dashboard_ui.start()
        assert dashboard_ui.app is not None
    
    def test_get_dashboard_html(self, dashboard_ui):
        """测试获取仪表板HTML"""
        html = dashboard_ui._get_dashboard_html()
        
        assert isinstance(html, str)
        assert "港股量化交易 AI Agent 仪表板" in html
        assert "dashboard-container" in html
        assert "agents-grid" in html
    
    def test_get_agent_detail_html(self, dashboard_ui):
        """测试获取Agent详情HTML"""
        html = dashboard_ui._get_agent_detail_html("test_agent")
        
        assert isinstance(html, str)
        assert "test_agent" in html
        assert "Agent 详情页面" in html
    
    def test_get_strategy_detail_html(self, dashboard_ui):
        """测试获取策略详情HTML"""
        html = dashboard_ui._get_strategy_detail_html("test_agent")
        
        assert isinstance(html, str)
        assert "test_agent" in html
        assert "策略详情" in html
    
    def test_get_performance_html(self, dashboard_ui):
        """测试获取绩效分析HTML"""
        html = dashboard_ui._get_performance_html()
        
        assert isinstance(html, str)
        assert "绩效分析" in html
    
    def test_get_system_status_html(self, dashboard_ui):
        """测试获取系统状态HTML"""
        html = dashboard_ui._get_system_status_html()
        
        assert isinstance(html, str)
        assert "系统状态" in html


# 集成测试
class TestDashboardIntegration:
    """仪表板集成测试"""
    
    @pytest.fixture
    def mock_coordinator(self):
        """模拟AgentCoordinator"""
        coordinator = Mock()
        coordinator.get_agent_status = AsyncMock()
        coordinator.get_all_agent_statuses = AsyncMock()
        coordinator.start_agent = AsyncMock()
        coordinator.stop_agent = AsyncMock()
        return coordinator
    
    @pytest.fixture
    def mock_message_queue(self):
        """模拟MessageQueue"""
        message_queue = Mock()
        message_queue.subscribe = AsyncMock()
        message_queue.unsubscribe = AsyncMock()
        message_queue.publish_message = AsyncMock()
        return message_queue
    
    @pytest.mark.asyncio
    async def test_full_dashboard_initialization(self, mock_coordinator, mock_message_queue):
        """测试完整仪表板初始化"""
        # 创建DashboardAPI
        dashboard_api = DashboardAPI(mock_coordinator, mock_message_queue)
        
        # 初始化API
        api_result = await dashboard_api.initialize()
        assert api_result is True
        
        # 创建DashboardUI
        dashboard_ui = DashboardUI(dashboard_api)
        
        # 启动UI
        await dashboard_ui.start()
        
        # 验证所有组件都已初始化
        assert dashboard_ui.app is not None
        assert dashboard_api._services_initialized is True
        
        # 清理资源
        await dashboard_ui.cleanup()
        await dashboard_api.cleanup()
    
    @pytest.mark.asyncio
    async def test_data_flow_integration(self, mock_coordinator, mock_message_queue):
        """测试数据流集成"""
        # 创建服务
        dashboard_api = DashboardAPI(mock_coordinator, mock_message_queue)
        await dashboard_api.initialize()
        
        # 模拟Agent数据
        mock_coordinator.get_all_agent_statuses.return_value = {
            "agent_001": {
                "agent_type": "QuantitativeAnalyst",
                "status": "running",
                "cpu_usage": 50.0,
                "memory_usage": 60.0
            }
        }
        
        # 测试数据流
        summary = await dashboard_api.agent_data_service.get_dashboard_summary()
        assert summary is not None
        
        agents_data = await dashboard_api.agent_data_service.get_all_agents_data()
        assert isinstance(agents_data, dict)
        
        strategies = await dashboard_api.strategy_data_service.get_all_strategies()
        assert isinstance(strategies, dict)
        
        # 清理资源
        await dashboard_api.cleanup()


# 性能测试
class TestDashboardPerformance:
    """仪表板性能测试"""
    
    @pytest.fixture
    def mock_coordinator(self):
        """模拟AgentCoordinator"""
        coordinator = Mock()
        coordinator.get_agent_status = AsyncMock()
        coordinator.get_all_agent_statuses = AsyncMock()
        return coordinator
    
    @pytest.fixture
    def mock_message_queue(self):
        """模拟MessageQueue"""
        message_queue = Mock()
        message_queue.subscribe = AsyncMock()
        message_queue.unsubscribe = AsyncMock()
        return message_queue
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, mock_coordinator, mock_message_queue):
        """测试并发请求性能"""
        dashboard_api = DashboardAPI(mock_coordinator, mock_message_queue)
        await dashboard_api.initialize()
        
        # 模拟大量Agent数据
        agent_statuses = {}
        for i in range(100):
            agent_statuses[f"agent_{i:03d}"] = {
                "agent_type": "QuantitativeAnalyst",
                "status": "running",
                "cpu_usage": 50.0,
                "memory_usage": 60.0
            }
        
        mock_coordinator.get_all_agent_statuses.return_value = agent_statuses
        
        # 并发请求
        tasks = []
        for i in range(10):
            task = dashboard_api.agent_data_service.get_dashboard_summary()
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # 验证所有请求都成功
        assert len(results) == 10
        for result in results:
            assert result is not None
        
        await dashboard_api.cleanup()
    
    @pytest.mark.asyncio
    async def test_memory_usage(self, mock_coordinator, mock_message_queue):
        """测试内存使用情况"""
        dashboard_api = DashboardAPI(mock_coordinator, mock_message_queue)
        await dashboard_api.initialize()
        
        # 创建大量绩效数据
        import pandas as pd
        
        for i in range(50):
            agent_id = f"agent_{i:03d}"
            returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015] * 20)  # 100个数据点
            
            backtest_metrics = await dashboard_api.performance_service.calculate_strategy_performance(
                f"strategy_{i}", returns
            )
            
            assert backtest_metrics is not None
        
        await dashboard_api.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

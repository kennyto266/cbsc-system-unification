"""
港股量化交易 AI Agent 系统 - Agent集成测试

测试Agent之间的协作、端到端交易流程和系统集成功能。
"""

import asyncio
import logging
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid

from src.core.message_queue import MessageQueue, Message
from src.models.base import MarketData, TradingSignal, Portfolio, RiskMetrics
from src.agents.coordinator import AgentCoordinator
from src.agents.base_agent import AgentConfig
from src.agents.quantitative_analyst import QuantitativeAnalystAgent
from src.agents.quantitative_trader import QuantitativeTraderAgent
from src.agents.portfolio_manager import PortfolioManagerAgent
from src.agents.risk_analyst import RiskAnalystAgent
from src.agents.data_scientist import DataScientistAgent
from src.agents.quantitative_engineer import QuantitativeEngineerAgent
from src.agents.research_analyst import ResearchAnalystAgent


class TestAgentIntegration:
    """Agent集成测试类"""
    
    @pytest.fixture
    async def message_queue(self):
        """消息队列fixture"""
        queue = MessageQueue()
        await queue.initialize()
        yield queue
        await queue.cleanup()
    
    @pytest.fixture
    async def coordinator(self, message_queue):
        """Agent协调器fixture"""
        coordinator = AgentCoordinator(message_queue)
        await coordinator.initialize()
        yield coordinator
        await coordinator.cleanup()
    
    @pytest.fixture
    def sample_market_data(self):
        """示例市场数据"""
        return MarketData(
            id=str(uuid.uuid4()),
            symbol="2800.HK",
            timestamp=datetime.now(),
            open_price=25.50,
            high_price=25.80,
            low_price=25.40,
            close_price=25.70,
            volume=1000000,
            vwap=25.60
        )
    
    @pytest.fixture
    def sample_trading_signal(self):
        """示例交易信号"""
        return TradingSignal(
            id=str(uuid.uuid4()),
            symbol="2800.HK",
            signal_type="BUY",
            strength=0.8,
            price=25.70,
            timestamp=datetime.now(),
            confidence=0.85,
            reasoning="动量指标显示买入信号"
        )
    
    @pytest_asyncio.fixture
    async def all_agents(self, message_queue):
        """所有Agent的fixture"""
        agents = {}
        
        # 创建所有Agent
        agent_configs = {
            "quantitative_analyst": AgentConfig(
                agent_id="quant_analyst_001",
                agent_type="QuantitativeAnalyst",
                status="active"
            ),
            "quantitative_trader": AgentConfig(
                agent_id="quant_trader_001", 
                agent_type="QuantitativeTrader",
                status="active"
            ),
            "portfolio_manager": AgentConfig(
                agent_id="portfolio_manager_001",
                agent_type="PortfolioManager", 
                status="active"
            ),
            "risk_analyst": AgentConfig(
                agent_id="risk_analyst_001",
                agent_type="RiskAnalyst",
                status="active"
            ),
            "data_scientist": AgentConfig(
                agent_id="data_scientist_001",
                agent_type="DataScientist",
                status="active"
            ),
            "quantitative_engineer": AgentConfig(
                agent_id="quant_engineer_001",
                agent_type="QuantitativeEngineer",
                status="active"
            ),
            "research_analyst": AgentConfig(
                agent_id="research_analyst_001",
                agent_type="ResearchAnalyst",
                status="active"
            )
        }
        
        # 实例化所有Agent
        agents["quantitative_analyst"] = QuantitativeAnalystAgent(
            agent_configs["quantitative_analyst"], message_queue
        )
        agents["quantitative_trader"] = QuantitativeTraderAgent(
            agent_configs["quantitative_trader"], message_queue
        )
        agents["portfolio_manager"] = PortfolioManagerAgent(
            agent_configs["portfolio_manager"], message_queue
        )
        agents["risk_analyst"] = RiskAnalystAgent(
            agent_configs["risk_analyst"], message_queue
        )
        agents["data_scientist"] = DataScientistAgent(
            agent_configs["data_scientist"], message_queue
        )
        agents["quantitative_engineer"] = QuantitativeEngineerAgent(
            agent_configs["quantitative_engineer"], message_queue
        )
        agents["research_analyst"] = ResearchAnalystAgent(
            agent_configs["research_analyst"], message_queue
        )
        
        # 初始化所有Agent
        for agent in agents.values():
            await agent.initialize()
        
        yield agents
        
        # 清理所有Agent
        for agent in agents.values():
            await agent.cleanup()
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, all_agents):
        """测试Agent初始化"""
        
        for agent_name, agent in all_agents.items():
            assert agent is not None
            assert agent.running is True
            assert agent.config.agent_id is not None
            assert agent.protocol is not None
    
    @pytest.mark.asyncio
    async def test_message_flow_between_agents(self, all_agents, sample_market_data):
        """测试Agent间消息流"""
        
        # 发送市场数据给量化分析师
        market_message = Message(
            id=str(uuid.uuid4()),
            sender_id="market_data_source",
            receiver_id="quant_analyst_001",
            message_type="MARKET_DATA",
            payload=sample_market_data.dict(),
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await all_agents["quantitative_analyst"].process_message(market_message)
        
        # 等待消息处理
        await asyncio.sleep(1)
        
        # 验证量化分析师处理了消息
        assert all_agents["quantitative_analyst"].running is True
    
    @pytest.mark.asyncio
    async def test_trading_signal_generation_flow(self, all_agents, sample_market_data):
        """测试交易信号生成流程"""
        
        # 1. 数据科学家处理市场数据
        data_message = Message(
            id=str(uuid.uuid4()),
            sender_id="market_data_source",
            receiver_id="data_scientist_001",
            message_type="MARKET_DATA",
            payload=sample_market_data.dict(),
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await all_agents["data_scientist"].process_message(data_message)
        await asyncio.sleep(0.5)
        
        # 2. 量化分析师生成交易信号
        analyst_message = Message(
            id=str(uuid.uuid4()),
            sender_id="data_scientist_001",
            receiver_id="quant_analyst_001",
            message_type="PROCESSED_DATA",
            payload={"processed_features": {"momentum": 0.8, "volatility": 0.15}},
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await all_agents["quantitative_analyst"].process_message(analyst_message)
        await asyncio.sleep(0.5)
        
        # 3. 量化交易员执行交易
        signal_message = Message(
            id=str(uuid.uuid4()),
            sender_id="quant_analyst_001",
            receiver_id="quant_trader_001",
            message_type="TRADING_SIGNAL",
            payload={
                "symbol": "2800.HK",
                "signal_type": "BUY",
                "strength": 0.8,
                "price": 25.70
            },
            timestamp=datetime.now(),
            priority="HIGH"
        )
        
        await all_agents["quantitative_trader"].process_message(signal_message)
        await asyncio.sleep(0.5)
        
        # 验证所有Agent都处理了消息
        for agent_name, agent in all_agents.items():
            assert agent.running is True
    
    @pytest.mark.asyncio
    async def test_risk_management_flow(self, all_agents, sample_trading_signal):
        """测试风险管理流程"""
        
        # 1. 交易信号发送给风险分析师
        signal_message = Message(
            id=str(uuid.uuid4()),
            sender_id="quant_analyst_001",
            receiver_id="risk_analyst_001",
            message_type="TRADING_SIGNAL",
            payload=sample_trading_signal.dict(),
            timestamp=datetime.now(),
            priority="HIGH"
        )
        
        await all_agents["risk_analyst"].process_message(signal_message)
        await asyncio.sleep(0.5)
        
        # 2. 风险分析师评估风险
        portfolio_message = Message(
            id=str(uuid.uuid4()),
            sender_id="portfolio_manager_001",
            receiver_id="risk_analyst_001",
            message_type="PORTFOLIO_UPDATE",
            payload={
                "current_positions": {"2800.HK": 1000},
                "total_value": 25700.0,
                "cash": 50000.0
            },
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await all_agents["risk_analyst"].process_message(portfolio_message)
        await asyncio.sleep(0.5)
        
        # 验证风险管理流程
        assert all_agents["risk_analyst"].running is True
    
    @pytest.mark.asyncio
    async def test_portfolio_rebalancing_flow(self, all_agents):
        """测试投资组合再平衡流程"""
        
        # 1. 投资组合经理接收再平衡信号
        rebalance_message = Message(
            id=str(uuid.uuid4()),
            sender_id="quant_analyst_001",
            receiver_id="portfolio_manager_001",
            message_type="REBALANCE_SIGNAL",
            payload={
                "target_allocation": {"2800.HK": 0.6, "0700.HK": 0.4},
                "current_allocation": {"2800.HK": 0.7, "0700.HK": 0.3},
                "rebalance_threshold": 0.05
            },
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await all_agents["portfolio_manager"].process_message(rebalance_message)
        await asyncio.sleep(0.5)
        
        # 2. 投资组合经理生成交易指令
        trade_message = Message(
            id=str(uuid.uuid4()),
            sender_id="portfolio_manager_001",
            receiver_id="quant_trader_001",
            message_type="TRADE_INSTRUCTION",
            payload={
                "symbol": "2800.HK",
                "action": "SELL",
                "quantity": 100,
                "price": 25.70,
                "reason": "再平衡"
            },
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await all_agents["quantitative_trader"].process_message(trade_message)
        await asyncio.sleep(0.5)
        
        # 验证再平衡流程
        assert all_agents["portfolio_manager"].running is True
        assert all_agents["quantitative_trader"].running is True
    
    @pytest.mark.asyncio
    async def test_research_workflow(self, all_agents):
        """测试研究工作流程"""
        
        # 1. 研究分析师启动研究项目
        research_message = Message(
            id=str(uuid.uuid4()),
            sender_id="system_coordinator",
            receiver_id="research_analyst_001",
            message_type="CONTROL",
            payload={
                "command": "start_research",
                "parameters": {
                    "research_type": "strategy_hypothesis",
                    "focus_area": "momentum_strategies"
                }
            },
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await all_agents["research_analyst"].process_message(research_message)
        await asyncio.sleep(1)
        
        # 2. 研究分析师请求数据
        data_request_message = Message(
            id=str(uuid.uuid4()),
            sender_id="research_analyst_001",
            receiver_id="data_scientist_001",
            message_type="DATA_REQUEST",
            payload={
                "data_type": "historical_prices",
                "symbols": ["2800.HK", "0700.HK"],
                "period": "1Y",
                "features": ["returns", "volatility", "volume"]
            },
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await all_agents["data_scientist"].process_message(data_request_message)
        await asyncio.sleep(0.5)
        
        # 验证研究流程
        assert all_agents["research_analyst"].running is True
        assert all_agents["data_scientist"].running is True
    
    @pytest.mark.asyncio
    async def test_system_monitoring_flow(self, all_agents):
        """测试系统监控流程"""
        
        # 1. 量化工程师收集系统指标
        metrics_message = Message(
            id=str(uuid.uuid4()),
            sender_id="system_coordinator",
            receiver_id="quant_engineer_001",
            message_type="CONTROL",
            payload={
                "command": "collect_metrics",
                "parameters": {}
            },
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await all_agents["quantitative_engineer"].process_message(metrics_message)
        await asyncio.sleep(1)
        
        # 2. 系统健康检查
        health_check_message = Message(
            id=str(uuid.uuid4()),
            sender_id="system_coordinator",
            receiver_id="quant_engineer_001",
            message_type="CONTROL",
            payload={
                "command": "run_health_check",
                "parameters": {}
            },
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await all_agents["quantitative_engineer"].process_message(health_check_message)
        await asyncio.sleep(0.5)
        
        # 验证监控流程
        assert all_agents["quantitative_engineer"].running is True
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, all_agents):
        """测试错误处理和恢复"""
        
        # 发送错误消息
        error_message = Message(
            id=str(uuid.uuid4()),
            sender_id="error_source",
            receiver_id="quant_analyst_001",
            message_type="ERROR",
            payload={
                "error_type": "data_error",
                "error_message": "测试错误",
                "error_context": {"symbol": "2800.HK", "timestamp": datetime.now().isoformat()}
            },
            timestamp=datetime.now(),
            priority="URGENT"
        )
        
        # Agent应该能够处理错误消息而不崩溃
        await all_agents["quantitative_analyst"].process_message(error_message)
        await asyncio.sleep(0.5)
        
        # 验证Agent仍然运行
        assert all_agents["quantitative_analyst"].running is True
    
    @pytest.mark.asyncio
    async def test_high_frequency_message_processing(self, all_agents, sample_market_data):
        """测试高频消息处理"""
        
        # 发送大量消息
        messages = []
        for i in range(100):
            message = Message(
                id=str(uuid.uuid4()),
                sender_id="market_data_source",
                receiver_id="quant_analyst_001",
                message_type="MARKET_DATA",
                payload={
                    **sample_market_data.dict(),
                    "timestamp": datetime.now().isoformat(),
                    "sequence": i
                },
                timestamp=datetime.now(),
                priority="NORMAL"
            )
            messages.append(message)
        
        # 并发处理消息
        tasks = []
        for message in messages:
            task = asyncio.create_task(
                all_agents["quantitative_analyst"].process_message(message)
            )
            tasks.append(task)
        
        # 等待所有消息处理完成
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # 验证Agent仍然运行
        assert all_agents["quantitative_analyst"].running is True
    
    @pytest.mark.asyncio
    async def test_agent_coordination_through_coordinator(self, coordinator, all_agents):
        """测试通过协调器的Agent协调"""
        
        # 注册所有Agent到协调器
        for agent_name, agent in all_agents.items():
            await coordinator.register_agent(agent.config.agent_id, agent.config.agent_type)
        
        # 获取所有Agent状态
        statuses = await coordinator.get_all_agent_statuses()
        
        # 验证所有Agent都已注册
        assert len(statuses) == len(all_agents)
        
        for agent_name, agent in all_agents.items():
            assert agent.config.agent_id in statuses
            assert statuses[agent.config.agent_id]["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_end_to_end_trading_workflow(self, all_agents, sample_market_data):
        """测试端到端交易工作流程"""
        
        # 完整的交易流程测试
        
        # 1. 市场数据输入
        market_message = Message(
            id=str(uuid.uuid4()),
            sender_id="market_data_source",
            receiver_id="data_scientist_001",
            message_type="MARKET_DATA",
            payload=sample_market_data.dict(),
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await all_agents["data_scientist"].process_message(market_message)
        await asyncio.sleep(0.5)
        
        # 2. 特征工程
        features_message = Message(
            id=str(uuid.uuid4()),
            sender_id="data_scientist_001",
            receiver_id="quant_analyst_001",
            message_type="PROCESSED_DATA",
            payload={
                "features": {
                    "momentum": 0.8,
                    "volatility": 0.15,
                    "volume_ratio": 1.2,
                    "rsi": 65.0
                },
                "symbol": "2800.HK",
                "timestamp": datetime.now().isoformat()
            },
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await all_agents["quantitative_analyst"].process_message(features_message)
        await asyncio.sleep(0.5)
        
        # 3. 交易信号生成
        signal_message = Message(
            id=str(uuid.uuid4()),
            sender_id="quant_analyst_001",
            receiver_id="quant_trader_001",
            message_type="TRADING_SIGNAL",
            payload={
                "symbol": "2800.HK",
                "signal_type": "BUY",
                "strength": 0.8,
                "price": 25.70,
                "confidence": 0.85,
                "reasoning": "动量指标显示买入信号"
            },
            timestamp=datetime.now(),
            priority="HIGH"
        )
        
        await all_agents["quantitative_trader"].process_message(signal_message)
        await asyncio.sleep(0.5)
        
        # 4. 风险管理检查
        risk_message = Message(
            id=str(uuid.uuid4()),
            sender_id="quant_trader_001",
            receiver_id="risk_analyst_001",
            message_type="TRADE_REQUEST",
            payload={
                "symbol": "2800.HK",
                "action": "BUY",
                "quantity": 100,
                "price": 25.70,
                "total_value": 2570.0
            },
            timestamp=datetime.now(),
            priority="HIGH"
        )
        
        await all_agents["risk_analyst"].process_message(risk_message)
        await asyncio.sleep(0.5)
        
        # 5. 投资组合更新
        portfolio_message = Message(
            id=str(uuid.uuid4()),
            sender_id="risk_analyst_001",
            receiver_id="portfolio_manager_001",
            message_type="RISK_APPROVED",
            payload={
                "symbol": "2800.HK",
                "action": "BUY",
                "quantity": 100,
                "price": 25.70,
                "risk_score": 0.3,
                "approved": True
            },
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await all_agents["portfolio_manager"].process_message(portfolio_message)
        await asyncio.sleep(0.5)
        
        # 6. 执行交易
        execute_message = Message(
            id=str(uuid.uuid4()),
            sender_id="portfolio_manager_001",
            receiver_id="quant_trader_001",
            message_type="EXECUTE_TRADE",
            payload={
                "symbol": "2800.HK",
                "action": "BUY",
                "quantity": 100,
                "price": 25.70,
                "order_id": str(uuid.uuid4())
            },
            timestamp=datetime.now(),
            priority="URGENT"
        )
        
        await all_agents["quantitative_trader"].process_message(execute_message)
        await asyncio.sleep(0.5)
        
        # 验证端到端流程
        for agent_name, agent in all_agents.items():
            assert agent.running is True, f"Agent {agent_name} 在端到端测试中失败"
        
        # 验证系统监控
        await all_agents["quantitative_engineer"].process_message(Message(
            id=str(uuid.uuid4()),
            sender_id="system_coordinator",
            receiver_id="quant_engineer_001",
            message_type="CONTROL",
            payload={"command": "collect_metrics"},
            timestamp=datetime.now(),
            priority="NORMAL"
        ))
        
        assert all_agents["quantitative_engineer"].running is True


class TestSystemIntegration:
    """系统集成测试类"""
    
    @pytest.mark.asyncio
    async def test_system_startup_and_shutdown(self):
        """测试系统启动和关闭"""
        
        # 创建消息队列
        message_queue = MessageQueue()
        await message_queue.initialize()
        
        # 创建协调器
        coordinator = AgentCoordinator(message_queue)
        await coordinator.initialize()
        
        # 验证系统启动
        assert coordinator.running is True
        
        # 关闭系统
        await coordinator.cleanup()
        await message_queue.cleanup()
        
        # 验证系统关闭
        assert coordinator.running is False
    
    @pytest.mark.asyncio
    async def test_message_queue_performance(self):
        """测试消息队列性能"""
        
        message_queue = MessageQueue()
        await message_queue.initialize()
        
        # 发送大量消息测试性能
        messages = []
        for i in range(1000):
            message = Message(
                id=str(uuid.uuid4()),
                sender_id="test_sender",
                receiver_id="test_receiver",
                message_type="TEST_MESSAGE",
                payload={"sequence": i},
                timestamp=datetime.now(),
                priority="NORMAL"
            )
            messages.append(message)
        
        # 测试消息发送性能
        start_time = datetime.now()
        
        for message in messages:
            await message_queue.publish_message(message)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 验证性能：1000条消息应该在5秒内发送完成
        assert duration < 5.0, f"消息发送性能不足，耗时 {duration:.2f} 秒"
        
        await message_queue.cleanup()
    
    @pytest.mark.asyncio
    async def test_system_scalability(self):
        """测试系统可扩展性"""
        
        message_queue = MessageQueue()
        await message_queue.initialize()
        
        # 创建多个Agent实例测试可扩展性
        agents = []
        
        for i in range(10):
            config = AgentConfig(
                agent_id=f"test_agent_{i}",
                agent_type="TestAgent",
                status="active"
            )
            
            # 模拟Agent（简化版）
            agent = type('TestAgent', (), {
                'config': config,
                'running': True,
                'initialize': lambda: asyncio.sleep(0.1),
                'cleanup': lambda: asyncio.sleep(0.1),
                'process_message': lambda msg: asyncio.sleep(0.01)
            })()
            
            agents.append(agent)
            await agent.initialize()
        
        # 验证所有Agent都成功启动
        assert len(agents) == 10
        for agent in agents:
            assert agent.running is True
        
        # 清理
        for agent in agents:
            await agent.cleanup()
        
        await message_queue.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

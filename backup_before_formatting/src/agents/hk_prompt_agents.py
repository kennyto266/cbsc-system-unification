"""
基于Prompt模板的港股量化分析AI代理实现

实现7个专业AI代理，使用prompt模板和LLM进行港股量化分析。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from ..core import SystemConfig
from ..core.message_queue import Message, MessageQueue
from ..data_adapters.base_adapter import RealMarketData
from ..data_adapters.data_service import DataService
from .base_agent import AgentConfig, AgentStatus, BaseAgent
from .hk_prompt_engine import (
    HKPromptEngine,
    LLMConfig,
    LLMProvider,
    PromptExecutionResult,
)
from .hk_prompt_templates import AgentType, HKPromptTemplates
from .protocol import AgentProtocol, MessageType


class HKPromptAgent(BaseAgent):
    """港股Prompt代理基类"""

    def __init__(
        self,
        config: AgentConfig,
        message_queue: MessageQueue,
        system_config: SystemConfig = None,
        prompt_engine: HKPromptEngine = None,
    ):
        super().__init__(config, message_queue, system_config)

        self.prompt_engine = prompt_engine
        self.templates = HKPromptTemplates()
        self.data_service = DataService()

        # 代理特定配置
        self.agent_type = self._get_agent_type()
        self.analysis_symbols = config.config.get(
            "analysis_symbols", ["0700.HK", "0005.HK", "0941.HK"]
        )
        self.lookback_days = config.config.get("lookback_days", 30)

        # 缓存和分析历史
        self.analysis_cache: Dict[str, Any] = {}
        self.last_analysis_time: Optional[datetime] = None
        self.analysis_interval = timedelta(minutes=5)  # 5分钟分析一次

        # 协议
        self.protocol = AgentProtocol(config.agent_id, message_queue)

    def _get_agent_type(self) -> AgentType:
        """子类需要重写此方法返回对应的代理类型"""
        raise NotImplementedError("子类必须实现_get_agent_type方法")

    async def initialize(self) -> bool:
        """初始化代理"""
        try:
            # 初始化协议
            await self.protocol.initialize()

            # 注册消息处理器
            self.protocol.register_handler(MessageType.DATA, self._handle_market_data)
            self.protocol.register_handler(MessageType.CONTROL, self._handle_control)

            # 初始化数据服务
            if not await self.data_service.initialize():
                self.logger.error("数据服务初始化失败")
                return False

            self.logger.info(
                f"{self.agent_type.value}代理初始化成功: {self.config.agent_id}"
            )
            return True

        except Exception as e:
            self.logger.error(f"{self.agent_type.value}代理初始化失败: {e}")
            return False

    async def process_message(self, message: Message) -> bool:
        """处理消息"""
        try:
            self.messages_processed += 1

            if message.type == "market_data":
                return await self._handle_market_data(message)
            elif message.type == "analysis_request":
                return await self._handle_analysis_request(message)
            elif message.type == "control":
                return await self._handle_control(message)
            else:
                self.logger.warning(f"未知消息类型: {message.type}")
                return False

        except Exception as e:
            self.logger.error(f"处理消息失败: {e}")
            self.error_count += 1
            return False

    async def _handle_market_data(self, message: Message) -> bool:
        """处理市场数据"""
        try:
            market_data = message.content.get("market_data", [])
            if not market_data:
                self.logger.warning("收到空的市场数据")
                return False

            # 检查是否需要进行分析
            if self._should_analyze():
                await self._perform_analysis(market_data)
                self.last_analysis_time = datetime.now()

            return True

        except Exception as e:
            self.logger.error(f"处理市场数据失败: {e}")
            return False

    async def _handle_analysis_request(self, message: Message) -> bool:
        """处理分析请求"""
        try:
            market_data = message.content.get("market_data", [])
            force_analysis = message.content.get("force", False)

            if force_analysis or self._should_analyze():
                result = await self._perform_analysis(market_data)

                # 发送分析结果
                response_message = Message(
                    id=f"{self.config.agent_id}_{datetime.now().timestamp()}",
                    type="analysis_result",
                    sender=self.config.agent_id,
                    receiver=message.sender,
                    content={
                        "agent_type": self.agent_type.value,
                        "analysis_result": result,
                        "timestamp": datetime.now().isoformat(),
                    },
                    timestamp=datetime.now(),
                )

                await self.message_queue.publish(response_message)
                return True

            return False

        except Exception as e:
            self.logger.error(f"处理分析请求失败: {e}")
            return False

    async def _handle_control(self, message: Message) -> bool:
        """处理控制消息"""
        try:
            command = message.content.get("command")
            parameters = message.content.get("parameters", {})

            if command == "get_status":
                await self._send_status_response(message.sender)
            elif command == "force_analysis":
                await self._handle_analysis_request(message)
            elif command == "update_config":
                await self._update_config(parameters)

            return True

        except Exception as e:
            self.logger.error(f"处理控制消息失败: {e}")
            return False

    def _should_analyze(self) -> bool:
        """判断是否需要进行新的分析"""
        if self.last_analysis_time is None:
            return True

        return datetime.now() - self.last_analysis_time > self.analysis_interval

    async def _perform_analysis(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, Any]:
        """执行分析"""
        try:
            if not self.prompt_engine:
                self.logger.error("Prompt引擎未初始化")
                return {"error": "Prompt引擎未初始化"}

            # 准备输入数据
            input_data = self._prepare_input_data(market_data)

            # 执行prompt
            result = await self.prompt_engine.execute_prompt(
                self.agent_type, input_data
            )

            if result.success:
                # 缓存结果
                self.analysis_cache[self.agent_type.value] = {
                    "result": result.parsed_data,
                    "explanation": result.explanation,
                    "timestamp": datetime.now(),
                    "execution_time": result.execution_time,
                }

                # 发送分析结果到其他代理
                await self._broadcast_analysis_result(result)

                return {
                    "success": True,
                    "agent_type": self.agent_type.value,
                    "data": result.parsed_data,
                    "explanation": result.explanation,
                    "execution_time": result.execution_time,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                self.logger.error(f"分析执行失败: {result.error}")
                return {
                    "success": False,
                    "error": result.error,
                    "agent_type": self.agent_type.value,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            self.logger.error(f"执行分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_type": self.agent_type.value,
                "timestamp": datetime.now().isoformat(),
            }

    def _prepare_input_data(self, market_data: List[RealMarketData]) -> Dict[str, Any]:
        """准备输入数据，子类可以重写此方法"""
        # 基础数据准备
        data = {
            "market_data": [],
            "symbols": [],
            "timestamp": datetime.now().isoformat(),
        }

        for item in market_data:
            data["market_data"].append(
                {
                    "symbol": item.symbol,
                    "timestamp": item.timestamp.isoformat(),
                    "open": float(item.open_price),
                    "high": float(item.high_price),
                    "low": float(item.low_price),
                    "close": float(item.close_price),
                    "volume": item.volume,
                }
            )
            if item.symbol not in data["symbols"]:
                data["symbols"].append(item.symbol)

        return data

    async def _broadcast_analysis_result(self, result: PromptExecutionResult):
        """广播分析结果到其他代理"""
        try:
            broadcast_message = Message(
                id=f"{self.config.agent_id}_broadcast_{datetime.now().timestamp()}",
                type="analysis_broadcast",
                sender=self.config.agent_id,
                receiver="all",
                content={
                    "agent_type": self.agent_type.value,
                    "analysis_result": result.parsed_data,
                    "explanation": result.explanation,
                    "timestamp": datetime.now().isoformat(),
                },
                timestamp=datetime.now(),
            )

            await self.message_queue.publish(broadcast_message)

        except Exception as e:
            self.logger.error(f"广播分析结果失败: {e}")

    async def _send_status_response(self, receiver: str):
        """发送状态响应"""
        try:
            status_message = Message(
                id=f"{self.config.agent_id}_status_{datetime.now().timestamp()}",
                type="status_response",
                sender=self.config.agent_id,
                receiver=receiver,
                content={
                    "agent_type": self.agent_type.value,
                    "status": self.status.value,
                    "last_analysis_time": (
                        self.last_analysis_time.isoformat()
                        if self.last_analysis_time
                        else None
                    ),
                    "analysis_count": len(self.analysis_cache),
                    "messages_processed": self.messages_processed,
                    "error_count": self.error_count,
                    "performance_metrics": await self.get_performance_metrics(),
                },
                timestamp=datetime.now(),
            )

            await self.message_queue.publish(status_message)

        except Exception as e:
            self.logger.error(f"发送状态响应失败: {e}")

    async def _update_config(self, parameters: Dict[str, Any]):
        """更新配置"""
        try:
            if "analysis_symbols" in parameters:
                self.analysis_symbols = parameters["analysis_symbols"]
                self.logger.info(f"更新分析标的: {self.analysis_symbols}")

            if "lookback_days" in parameters:
                self.lookback_days = parameters["lookback_days"]
                self.logger.info(f"更新回看天数: {self.lookback_days}")

            if "analysis_interval" in parameters:
                self.analysis_interval = timedelta(
                    minutes=parameters["analysis_interval"]
                )
                self.logger.info(f"更新分析间隔: {self.analysis_interval}")

        except Exception as e:
            self.logger.error(f"更新配置失败: {e}")

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        base_metrics = await super().get_performance_metrics()

        # 添加代理特定指标
        agent_metrics = {
            "agent_type": self.agent_type.value,
            "analysis_symbols": self.analysis_symbols,
            "lookback_days": self.lookback_days,
            "last_analysis_time": (
                self.last_analysis_time.isoformat() if self.last_analysis_time else None
            ),
            "analysis_cache_size": len(self.analysis_cache),
            "prompt_engine_available": self.prompt_engine is not None,
        }

        return {**base_metrics, **agent_metrics}

    async def cleanup(self):
        """清理资源"""
        try:
            self.logger.info(f"清理{self.agent_type.value}代理资源...")

            # 清理数据服务
            if hasattr(self.data_service, "cleanup"):
                await self.data_service.cleanup()

            # 清理缓存
            self.analysis_cache.clear()

            await super().cleanup()

        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")


class HKFundamentalAnalystAgent(HKPromptAgent):
    """港股基本面分析代理"""

    def _get_agent_type(self) -> AgentType:
        return AgentType.FUNDAMENTAL_ANALYST

    def _prepare_input_data(self, market_data: List[RealMarketData]) -> Dict[str, Any]:
        """准备基本面分析输入数据"""
        base_data = super()._prepare_input_data(market_data)

        # 添加基本面数据
        fundamental_data = {}
        for item in market_data:
            if item.symbol not in fundamental_data:
                fundamental_data[item.symbol] = {
                    "close_prices": [],
                    "eps_estimates": [],
                    "roe": [],
                }

            fundamental_data[item.symbol]["close_prices"].append(
                float(item.close_price)
            )
            # 这里应该从实际数据源获取EPS和ROE数据
            # 目前使用模拟数据
            fundamental_data[item.symbol]["eps_estimates"].append(
                float(item.close_price) * 0.1
            )
            fundamental_data[item.symbol]["roe"].append(0.15)

        base_data["fundamental_data"] = fundamental_data
        return base_data


class HKSentimentAnalystAgent(HKPromptAgent):
    """港股情绪分析代理"""

    def _get_agent_type(self) -> AgentType:
        return AgentType.SENTIMENT_ANALYST

    def _prepare_input_data(self, market_data: List[RealMarketData]) -> Dict[str, Any]:
        """准备情绪分析输入数据"""
        base_data = super()._prepare_input_data(market_data)

        # 添加情绪数据（模拟）
        sentiment_data = {}
        for item in market_data:
            if item.symbol not in sentiment_data:
                sentiment_data[item.symbol] = {"posts": [], "volumes": []}

            # 模拟社交媒体帖子
            sentiment_data[item.symbol]["posts"].append(f"{item.symbol}表现强劲！")
            sentiment_data[item.symbol]["volumes"].append(item.volume)

        base_data["sentiment_data"] = sentiment_data
        return base_data


class HKNewsAnalystAgent(HKPromptAgent):
    """港股新闻分析代理"""

    def _get_agent_type(self) -> AgentType:
        return AgentType.NEWS_ANALYST

    def _prepare_input_data(self, market_data: List[RealMarketData]) -> Dict[str, Any]:
        """准备新闻分析输入数据"""
        base_data = super()._prepare_input_data(market_data)

        # 添加新闻数据（模拟）
        news_data = {
            "news_items": [
                f"恒生指数成分股{market_data[0].symbol}发布财报",
                "港股市场情绪乐观",
                "地缘政治风险影响港股",
            ],
            "stock": market_data[0].symbol if market_data else "0700.HK",
        }

        base_data["news_data"] = news_data
        return base_data


class HKTechnicalAnalystAgent(HKPromptAgent):
    """港股技术分析代理"""

    def _get_agent_type(self) -> AgentType:
        return AgentType.TECHNICAL_ANALYST

    def _prepare_input_data(self, market_data: List[RealMarketData]) -> Dict[str, Any]:
        """准备技术分析输入数据"""
        base_data = super()._prepare_input_data(market_data)

        # 添加技术分析数据
        technical_data = {}
        for item in market_data:
            if item.symbol not in technical_data:
                technical_data[item.symbol] = {"close_prices": [], "volumes": []}

            technical_data[item.symbol]["close_prices"].append(float(item.close_price))
            technical_data[item.symbol]["volumes"].append(item.volume)

        base_data["technical_data"] = technical_data
        return base_data


class HKResearchDebateAgent(HKPromptAgent):
    """港股研究辩论代理"""

    def _get_agent_type(self) -> AgentType:
        return AgentType.RESEARCH_DEBATE

    def _prepare_input_data(self, market_data: List[RealMarketData]) -> Dict[str, Any]:
        """准备研究辩论输入数据"""
        base_data = super()._prepare_input_data(market_data)

        # 模拟其他代理的分析结果
        debate_data = {
            "fundamental": {"pe_avg": 12.5},
            "sentiment": {"avg_score": 0.3},
            "news": {"avg_impact": 0.05},
            "technical": {"rsi_avg": 55.0},
        }

        base_data["debate_data"] = debate_data
        return base_data


class HKTraderAgent(HKPromptAgent):
    """港股交易执行代理"""

    def _get_agent_type(self) -> AgentType:
        return AgentType.TRADER

    def _prepare_input_data(self, market_data: List[RealMarketData]) -> Dict[str, Any]:
        """准备交易执行输入数据"""
        base_data = super()._prepare_input_data(market_data)

        # 模拟交易信号和价格数据
        trading_data = {
            "balanced_score": 0.4,
            "signals": [1, -1, 1],
            "close_prices": [float(item.close_price) for item in market_data],
        }

        base_data["trading_data"] = trading_data
        return base_data


class HKRiskManagerAgent(HKPromptAgent):
    """港股风险管理代理"""

    def _get_agent_type(self) -> AgentType:
        return AgentType.RISK_MANAGER

    def _prepare_input_data(self, market_data: List[RealMarketData]) -> Dict[str, Any]:
        """准备风险管理输入数据"""
        base_data = super()._prepare_input_data(market_data)

        # 计算收益率数据
        returns = []
        for i in range(1, len(market_data)):
            prev_price = float(market_data[i - 1].close_price)
            curr_price = float(market_data[i].close_price)
            returns.append((curr_price - prev_price) / prev_price)

        risk_data = {"returns": returns, "risk_free_rate": 0.03}

        base_data["risk_data"] = risk_data
        return base_data


class HKPromptAgentFactory:
    """港股Prompt代理工厂"""

    @staticmethod
    def create_agent(
        agent_type: AgentType,
        config: AgentConfig,
        message_queue: MessageQueue,
        system_config: SystemConfig = None,
        prompt_engine: HKPromptEngine = None,
    ) -> HKPromptAgent:
        """创建指定类型的代理"""

        agent_classes = {
            AgentType.FUNDAMENTAL_ANALYST: HKFundamentalAnalystAgent,
            AgentType.SENTIMENT_ANALYST: HKSentimentAnalystAgent,
            AgentType.NEWS_ANALYST: HKNewsAnalystAgent,
            AgentType.TECHNICAL_ANALYST: HKTechnicalAnalystAgent,
            AgentType.RESEARCH_DEBATE: HKResearchDebateAgent,
            AgentType.TRADER: HKTraderAgent,
            AgentType.RISK_MANAGER: HKRiskManagerAgent,
        }

        agent_class = agent_classes.get(agent_type)
        if not agent_class:
            raise ValueError(f"不支持的代理类型: {agent_type}")

        return agent_class(config, message_queue, system_config, prompt_engine)

    @staticmethod
    def create_all_agents(
        message_queue: MessageQueue,
        system_config: SystemConfig = None,
        prompt_engine: HKPromptEngine = None,
    ) -> Dict[AgentType, HKPromptAgent]:
        """创建所有类型的代理"""
        agents = {}

        for agent_type in AgentType:
            config = AgentConfig(
                agent_id=f"hk_{agent_type.value}",
                agent_name=f"港股{agent_type.value}代理",
                config={
                    "analysis_symbols": ["0700.HK", "0005.HK", "0941.HK"],
                    "lookback_days": 30,
                },
            )

            agent = HKPromptAgentFactory.create_agent(
                agent_type, config, message_queue, system_config, prompt_engine
            )
            agents[agent_type] = agent

        return agents

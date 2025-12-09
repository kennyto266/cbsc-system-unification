"""
AI代理管理器
管理7个专业AI代理的启动、运行和结果聚合
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from .base_agent import BaseAgent
from .fundamental_agent import FundamentalAgent
from .news_agent import NewsAgent
from .research_agent import ResearchAgent
from .risk_manager_agent import RiskManagerAgent
from .sentiment_agent import SentimentAgent
from .technical_agent import TechnicalAgent
from .trader_agent import TraderAgent

logger = logging.getLogger(__name__)


class AgentManager:
    """AI代理管理器"""

    def __init__(self, cursor_api_key: str):
        self.cursor_api_key = cursor_api_key
        self.base_url = "https://api.cursor.com / v0"
        self.agents: List[BaseAgent] = []
        self.agent_results: Dict[str, Dict[str, Any]] = {}

        # 初始化7个专业代理
        self._initialize_agents()

    def _initialize_agents(self):
        """初始化所有代理"""
        self.agents = [
            FundamentalAgent(self.cursor_api_key, self.base_url),
            TechnicalAgent(self.cursor_api_key, self.base_url),
            SentimentAgent(self.cursor_api_key, self.base_url),
            NewsAgent(self.cursor_api_key, self.base_url),
            ResearchAgent(self.cursor_api_key, self.base_url),
            TraderAgent(self.cursor_api_key, self.base_url),
            RiskManagerAgent(self.cursor_api_key, self.base_url),
        ]

    async def run_all_agents(
        self,
        market_data: List[Dict[str, Any]],
        on_progress: Optional[callable] = None,
        parallel: bool = True,
        max_concurrent: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        运行所有代理 - 优化版本支持并行处理

        Args:
            market_data: 市场数据
            on_progress: 进度回调
            parallel: 是否并行执行
            max_concurrent: 最大并发数

        Returns:
            代理分析结果列表
        """
        logger.info(f"启动 {len(self.agents)} 个AI代理 (并行模式: {parallel})")

        if parallel and max_concurrent > 1:
            # 并行执行模式
            return await self._run_agents_parallel(
                market_data, on_progress, max_concurrent
            )
        else:
            # 串行执行模式（保持向后兼容）
            return await self._run_agents_serial(market_data, on_progress)

    async def _run_agents_parallel(
        self,
        market_data: List[Dict[str, Any]],
        on_progress: Optional[callable] = None,
        max_concurrent: int = 3,
    ) -> List[Dict[str, Any]]:
        """并行运行代理"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_semaphore(agent):
            async with semaphore:
                return await self._run_single_agent(agent, market_data, on_progress)

        # 创建所有任务
        tasks = [run_with_semaphore(agent) for agent in self.agents]

        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"代理 {self.agents[i].name} 运行失败: {result}")
            elif result:
                successful_results.append(result)
                self.agent_results[self.agents[i].agent_id] = result

        logger.info(f"并行执行完成，成功 {len(successful_results)} 个代理分析")
        return successful_results

    async def _run_agents_serial(
        self, market_data: List[Dict[str, Any]], on_progress: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """串行运行代理（原逻辑）"""
        results = []
        for i, agent in enumerate(self.agents):
            logger.info(f"启动代理 {i + 1}/{len(self.agents)}: {agent.name}")
            result = await self._run_single_agent(agent, market_data, on_progress)
            results.append(result)

            # 代理之间稍作延迟
            if i < len(self.agents) - 1:
                print("⏱️ 等待2秒后启动下一个代理...")
                await asyncio.sleep(2)

        # 处理结果
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"代理 {self.agents[i].name} 运行失败: {result}")
            elif result:
                successful_results.append(result)
                self.agent_results[self.agents[i].agent_id] = result

        logger.info(f"串行执行完成，成功 {len(successful_results)} 个代理分析")
        return successful_results

    async def _run_single_agent(
        self,
        agent: BaseAgent,
        market_data: List[Dict[str, Any]],
        on_progress: Optional[callable] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        运行单个代理

        Args:
            agent: 代理实例
            market_data: 市场数据

        Returns:
            代理分析结果
        """
        try:
            logger.info(f"启动代理: {agent.name}")

            # 启动代理
            agent_id = await agent.launch(market_data)
            if not agent_id:
                logger.error(f"代理 {agent.name} 启动失败")
                return None

            # 等待代理完成分析 - 减少等待时间
            max_wait_time = 90  # 1.5分钟
            check_interval = 10  # 每10秒检查一次（减少API调用）
            waited_time = 0
            last_conversation_check = 0

            print(f"⏳ 等待 {agent.name} 完成分析...")

            while waited_time < max_wait_time:
                await asyncio.sleep(check_interval)
                waited_time += check_interval

                # 显示进度
                progress = min(100, (waited_time / max_wait_time) * 100)
                print(
                    f"📊 {agent.name}: {progress:.0f}% ({waited_time}s/{max_wait_time}s)"
                )

                # 检查代理状态
                status = await agent.get_status(agent_id)
                if status:
                    agent_status_raw = status.get("status", "unknown")
                    agent_status = str(agent_status_raw).lower()
                    logger.info(
                        f"代理 {agent.name} 状态: {agent_status_raw} (等待 {waited_time}s)"
                    )

                    # 每20秒才抓取一次对话，避免429错误
                    if (
                        on_progress is not None
                        and (waited_time - last_conversation_check) >= 20
                    ):
                        try:
                            conversation = await agent.get_conversation(agent_id)
                            if conversation:
                                incremental = {
                                    "agent_name": agent.name,
                                    "agent_icon": getattr(agent, "icon", "🤖"),
                                    "agent_id": agent_id,
                                    "status": status,
                                    "conversation": conversation,
                                }
                                await on_progress(incremental)
                                last_conversation_check = waited_time
                        except Exception as e:
                            if "429" in str(e):
                                print("⚠️ API限制，跳过对话更新")
                            else:
                                print(f"⚠️ 对话获取失败: {e}")

                    if agent_status == "completed":
                        print(f"✅ {agent.name} 完成!")
                        break
                    elif agent_status == "failed":
                        logger.error(f"代理 {agent.name} 分析失败")
                        print(f"❌ {agent.name} 失败!")
                        return None
                else:
                    logger.warning(f"无法获取代理 {agent.name} 状态")

            # 获取分析结果
            result = await agent.get_result(agent_id)
            if result:
                logger.info(f"代理 {agent.name} 分析完成")
                return result
            else:
                logger.warning(f"代理 {agent.name} 未返回结果")
                return None

        except Exception as e:
            logger.error(f"代理 {agent.name} 运行出错: {e}")
            return None

    async def update_agent_status(self):
        """更新所有代理状态"""
        for agent in self.agents:
            if agent.agent_id:
                try:
                    status = await agent.get_status(agent.agent_id)
                    if status:
                        self.agent_results[agent.agent_id]["status"] = status
                except Exception as e:
                    logger.warning(f"更新代理 {agent.name} 状态失败: {e}")

    def get_agent_summary(self) -> Dict[str, Any]:
        """获取代理摘要信息"""
        return {
            "total_agents": len(self.agents),
            "successful_agents": len(self.agent_results),
            "agent_results": self.agent_results,
            "last_updated": datetime.now().isoformat(),
        }

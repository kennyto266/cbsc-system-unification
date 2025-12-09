"""
港股量化分析AI代理团队演示示例

展示如何使用基于prompt模板的7个专业AI代理进行港股量化分析。
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hk_prompt_demo")

# 导入必要的模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.hk_prompt_templates import HKPromptTemplates, AgentType
from src.agents.hk_prompt_engine import HKPromptEngine, LLMConfig, LLMProvider
from src.agents.hk_prompt_agents import HKPromptAgentFactory
from src.core.message_queue import MessageQueue
from src.core import SystemConfig
from src.agents.base_agent import AgentConfig


class HKPromptDemo:
    """港股Prompt代理演示类"""
    
    def __init__(self):
        self.logger = logging.getLogger("hk_prompt_demo")
        self.message_queue = None
        self.prompt_engine = None
        self.agents = {}
        
    async def initialize(self):
        """初始化演示环境"""
        try:
            # 初始化消息队列
            self.message_queue = MessageQueue()
            await self.message_queue.initialize()
            
            # 初始化系统配置
            system_config = SystemConfig()
            
            # 配置LLM（这里使用模拟配置，实际使用时需要真实的API密钥）
            llm_config = LLMConfig(
                provider=LLMProvider.OPENAI,
                api_key="your-openai-api-key-here",  # 替换为真实的API密钥
                model="gpt-4",
                max_tokens=2000,
                temperature=0.1
            )
            
            # 初始化Prompt引擎
            self.prompt_engine = HKPromptEngine(llm_config)
            
            # 创建所有代理
            self.agents = HKPromptAgentFactory.create_all_agents(
                self.message_queue, system_config, self.prompt_engine
            )
            
            # 初始化所有代理
            for agent_type, agent in self.agents.items():
                success = await agent.initialize()
                if success:
                    self.logger.info(f"代理 {agent_type.value} 初始化成功")
                else:
                    self.logger.error(f"代理 {agent_type.value} 初始化失败")
            
            self.logger.info("港股Prompt代理演示环境初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            return False
    
    def create_mock_market_data(self) -> List[Dict[str, Any]]:
        """创建模拟港股市场数据"""
        symbols = ["0700.HK", "0005.HK", "0941.HK", "1299.HK", "0388.HK"]
        market_data = []
        
        base_date = datetime.now() - timedelta(days=30)
        
        for i in range(30):  # 30天的数据
            for symbol in symbols:
                # 模拟价格数据
                base_price = 100 + (hash(symbol) % 50)  # 不同股票不同基础价格
                price_change = (hash(f"{symbol}_{i}") % 20 - 10) / 100  # -10%到+10%的随机变化
                current_price = base_price * (1 + price_change)
                
                market_data.append({
                    "symbol": symbol,
                    "timestamp": (base_date + timedelta(days=i)).isoformat(),
                    "open": current_price * 0.99,
                    "high": current_price * 1.02,
                    "low": current_price * 0.98,
                    "close": current_price,
                    "volume": 1000000 + (hash(f"{symbol}_{i}") % 500000)
                })
        
        return market_data
    
    async def test_individual_agents(self):
        """测试单个代理"""
        self.logger.info("开始测试单个代理...")
        
        market_data = self.create_mock_market_data()
        
        for agent_type, agent in self.agents.items():
            try:
                self.logger.info(f"测试代理: {agent_type.value}")
                
                # 创建分析请求消息
                analysis_message = {
                    "id": f"test_{agent_type.value}_{datetime.now().timestamp()}",
                    "type": "analysis_request",
                    "sender": "demo",
                    "receiver": agent.config.agent_id,
                    "content": {
                        "market_data": market_data,
                        "force": True
                    },
                    "timestamp": datetime.now()
                }
                
                # 处理消息
                success = await agent.process_message(analysis_message)
                
                if success:
                    self.logger.info(f"代理 {agent_type.value} 分析完成")
                else:
                    self.logger.error(f"代理 {agent_type.value} 分析失败")
                
                # 等待一下
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"测试代理 {agent_type.value} 时出错: {e}")
    
    async def test_agent_pipeline(self):
        """测试代理管道"""
        self.logger.info("开始测试代理管道...")
        
        market_data = self.create_mock_market_data()
        
        # 定义代理执行顺序
        agent_sequence = [
            AgentType.FUNDAMENTAL_ANALYST,
            AgentType.SENTIMENT_ANALYST,
            AgentType.NEWS_ANALYST,
            AgentType.TECHNICAL_ANALYST,
            AgentType.RESEARCH_DEBATE,
            AgentType.TRADER,
            AgentType.RISK_MANAGER
        ]
        
        try:
            # 使用Prompt引擎执行管道
            results = await self.prompt_engine.execute_agent_pipeline(
                {"market_data": market_data}, agent_sequence
            )
            
            # 显示结果
            for agent_type, result in results.items():
                if result.success:
                    self.logger.info(f"代理 {agent_type.value} 执行成功:")
                    self.logger.info(f"  执行时间: {result.execution_time:.2f}秒")
                    self.logger.info(f"  解释: {result.explanation}")
                    self.logger.info(f"  数据: {json.dumps(result.parsed_data, indent=2, ensure_ascii=False)}")
                else:
                    self.logger.error(f"代理 {agent_type.value} 执行失败: {result.error}")
                
                print("-" * 50)
            
        except Exception as e:
            self.logger.error(f"测试代理管道时出错: {e}")
    
    async def test_parallel_agents(self):
        """测试并行代理执行"""
        self.logger.info("开始测试并行代理执行...")
        
        market_data = self.create_mock_market_data()
        
        # 选择几个代理进行并行测试
        parallel_agents = [
            AgentType.FUNDAMENTAL_ANALYST,
            AgentType.TECHNICAL_ANALYST,
            AgentType.SENTIMENT_ANALYST
        ]
        
        try:
            # 并行执行
            results = await self.prompt_engine.execute_parallel_agents(
                {"market_data": market_data}, parallel_agents
            )
            
            # 显示结果
            for agent_type, result in results.items():
                if result.success:
                    self.logger.info(f"并行代理 {agent_type.value} 执行成功:")
                    self.logger.info(f"  执行时间: {result.execution_time:.2f}秒")
                    self.logger.info(f"  解释: {result.explanation}")
                else:
                    self.logger.error(f"并行代理 {agent_type.value} 执行失败: {result.error}")
                
                print("-" * 50)
            
        except Exception as e:
            self.logger.error(f"测试并行代理时出错: {e}")
    
    async def test_prompt_templates(self):
        """测试Prompt模板"""
        self.logger.info("开始测试Prompt模板...")
        
        templates = HKPromptTemplates()
        
        # 测试所有模板
        for agent_type in AgentType:
            try:
                template = templates.get_template(agent_type)
                if template:
                    self.logger.info(f"模板 {agent_type.value}:")
                    self.logger.info(f"  角色: {template.role}")
                    self.logger.info(f"  任务数量: {len(template.tasks)}")
                    self.logger.info(f"  示例输出: {json.dumps(template.example_output, indent=2, ensure_ascii=False)}")
                    print("-" * 30)
                
            except Exception as e:
                self.logger.error(f"测试模板 {agent_type.value} 时出错: {e}")
    
    async def test_llm_connection(self):
        """测试LLM连接"""
        self.logger.info("开始测试LLM连接...")
        
        try:
            if self.prompt_engine:
                success = await self.prompt_engine.test_connection()
                if success:
                    self.logger.info("LLM连接测试成功")
                else:
                    self.logger.error("LLM连接测试失败")
            else:
                self.logger.error("Prompt引擎未初始化")
                
        except Exception as e:
            self.logger.error(f"LLM连接测试时出错: {e}")
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 清理所有代理
            for agent in self.agents.values():
                await agent.cleanup()
            
            # 清理消息队列
            if self.message_queue:
                await self.message_queue.cleanup()
            
            self.logger.info("资源清理完成")
            
        except Exception as e:
            self.logger.error(f"清理资源时出错: {e}")
    
    async def run_demo(self):
        """运行完整演示"""
        try:
            # 初始化
            if not await self.initialize():
                self.logger.error("初始化失败，退出演示")
                return
            
            print("=" * 60)
            print("港股量化分析AI代理团队演示")
            print("=" * 60)
            
            # 测试LLM连接
            await self.test_llm_connection()
            print()
            
            # 测试Prompt模板
            await self.test_prompt_templates()
            print()
            
            # 测试单个代理
            await self.test_individual_agents()
            print()
            
            # 测试代理管道
            await self.test_agent_pipeline()
            print()
            
            # 测试并行代理
            await self.test_parallel_agents()
            print()
            
            # 显示统计信息
            if self.prompt_engine:
                stats = self.prompt_engine.get_execution_stats()
                self.logger.info("执行统计信息:")
                for key, value in stats.items():
                    self.logger.info(f"  {key}: {value}")
            
            print("=" * 60)
            print("演示完成")
            print("=" * 60)
            
        except Exception as e:
            self.logger.error(f"运行演示时出错: {e}")
        
        finally:
            # 清理资源
            await self.cleanup()


async def main():
    """主函数"""
    demo = HKPromptDemo()
    await demo.run_demo()


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())

"""
港股量化分析AI代理Prompt执行引擎

负责执行prompt模板，调用LLM API，解析响应并验证结果。
支持多种LLM提供商（OpenAI、Claude、本地模型等）。
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

import aiohttp
import openai

from .hk_prompt_templates import AgentType, HKPromptTemplates, PromptTemplate


class LLMProvider(str, Enum):
    """LLM提供商枚举"""

    OPENAI = "openai"
    CLAUDE = "claude"
    GROK = "grok"
    LOCAL = "local"
    CUSTOM = "custom"


@dataclass
class LLMConfig:
    """LLM配置"""

    provider: LLMProvider
    api_key: str
    base_url: Optional[str] = None
    model: str = "gpt - 4"
    max_tokens: int = 2000
    temperature: float = 0.1
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0


@dataclass
class PromptExecutionResult:
    """Prompt执行结果"""

    success: bool
    agent_type: AgentType
    input_data: Dict[str, Any]
    prompt_text: str
    response: str
    parsed_data: Dict[str, Any]
    explanation: str
    execution_time: float
    error: Optional[str] = None
    validation_passed: bool = False


class HKPromptEngine:
    """港股量化分析AI代理Prompt执行引擎"""

    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.templates = HKPromptTemplates()
        self.logger = logging.getLogger("hk_quant_system.prompt_engine")

        # 初始化LLM客户端
        self._init_llm_client()

        # 统计信息
        self.execution_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_execution_time = 0.0

    def _init_llm_client(self):
        """初始化LLM客户端"""
        try:
            if self.llm_config.provider == LLMProvider.OPENAI:
                openai.api_key = self.llm_config.api_key
                if self.llm_config.base_url:
                    openai.api_base = self.llm_config.base_url
                self.client = openai
            elif self.llm_config.provider == LLMProvider.CLAUDE:
                # 这里可以集成Anthropic Claude API
                self.client = None
            elif self.llm_config.provider == LLMProvider.GROK:
                # 这里可以集成Grok API
                self.client = None
            else:
                self.client = None

            self.logger.info(f"LLM客户端初始化完成: {self.llm_config.provider}")

        except Exception as e:
            self.logger.error(f"LLM客户端初始化失败: {e}")
            self.client = None

    async def execute_prompt(
        self,
        agent_type: AgentType,
        input_data: Dict[str, Any],
        custom_prompt: Optional[str] = None,
    ) -> PromptExecutionResult:
        """执行prompt并返回结果"""
        start_time = datetime.now()

        try:
            self.execution_count += 1

            # 生成prompt
            if custom_prompt:
                prompt_text = custom_prompt
            else:
                prompt_text = self.templates.generate_prompt(agent_type, input_data)

            # 调用LLM
            response = await self._call_llm(prompt_text)

            # 解析响应
            parsed_data = self.templates.parse_agent_response(response)

            # 验证响应
            validation_passed = self.templates.validate_response(
                agent_type, parsed_data
            )

            execution_time = (datetime.now() - start_time).total_seconds()
            self.total_execution_time += execution_time

            if validation_passed:
                self.success_count += 1
            else:
                self.error_count += 1

            result = PromptExecutionResult(
                success=validation_passed,
                agent_type=agent_type,
                input_data=input_data,
                prompt_text=prompt_text,
                response=response,
                parsed_data=parsed_data.get("json_data", {}),
                explanation=parsed_data.get("explanation", ""),
                execution_time=execution_time,
                validation_passed=validation_passed,
            )

            self.logger.info(
                f"Prompt执行完成: {agent_type.value}, 耗时: {execution_time:.2f}s, 验证: {validation_passed}"
            )
            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.error_count += 1

            self.logger.error(f"Prompt执行失败: {agent_type.value}, 错误: {e}")

            return PromptExecutionResult(
                success=False,
                agent_type=agent_type,
                input_data=input_data,
                prompt_text=custom_prompt or "",
                response="",
                parsed_data={},
                explanation="",
                execution_time=execution_time,
                error=str(e),
                validation_passed=False,
            )

    async def _call_llm(self, prompt: str) -> str:
        """调用LLM API"""
        if not self.client:
            raise ValueError("LLM客户端未初始化")

        if self.llm_config.provider == LLMProvider.OPENAI:
            return await self._call_openai(prompt)
        elif self.llm_config.provider == LLMProvider.CLAUDE:
            return await self._call_claude(prompt)
        elif self.llm_config.provider == LLMProvider.GROK:
            return await self._call_grok(prompt)
        else:
            raise ValueError(f"不支持的LLM提供商: {self.llm_config.provider}")

    async def _call_openai(self, prompt: str) -> str:
        """调用OpenAI API"""
        try:
            # 检查OpenAI版本并使用相应的API
            try:
                # 尝试使用新版本API (>=1.0.0)
                from openai import AsyncOpenAI

                # 创建客户端
                client_kwargs = {
                    "api_key": self.llm_config.api_key,
                    "timeout": self.llm_config.timeout,
                }

                if self.llm_config.base_url:
                    client_kwargs["base_url"] = self.llm_config.base_url

                client = AsyncOpenAI(**client_kwargs)

                # 调用API
                response = await client.chat.completions.create(
                    model=self.llm_config.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一位专业的港股量化分析AI代理，请严格按照要求输出JSON格式结果。",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=self.llm_config.max_tokens,
                    temperature=self.llm_config.temperature,
                )

                return response.choices[0].message.content.strip()

            except ImportError:
                # 使用旧版本API (<1.0.0)
                if self.llm_config.base_url and "cursor.sh" in self.llm_config.base_url:
                    # 使用Cursor API
                    response = await openai.ChatCompletion.acreate(
                        model=self.llm_config.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "你是一位专业的港股量化分析AI代理，请严格按照要求输出JSON格式结果。",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        max_tokens=self.llm_config.max_tokens,
                        temperature=self.llm_config.temperature,
                        timeout=self.llm_config.timeout,
                        api_base=self.llm_config.base_url,
                    )
                else:
                    # 使用标准OpenAI API
                    response = await openai.ChatCompletion.acreate(
                        model=self.llm_config.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "你是一位专业的港股量化分析AI代理，请严格按照要求输出JSON格式结果。",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        max_tokens=self.llm_config.max_tokens,
                        temperature=self.llm_config.temperature,
                        timeout=self.llm_config.timeout,
                    )

                return response.choices[0].message.content.strip()

        except Exception as e:
            self.logger.error(f"OpenAI API调用失败: {e}")
            raise

    async def _call_claude(self, prompt: str) -> str:
        """调用Claude API（需要实现）"""
        # 这里需要集成Anthropic Claude API
        raise NotImplementedError("Claude API集成待实现")

    async def _call_grok(self, prompt: str) -> str:
        """调用Grok API（需要实现）"""
        # 这里需要集成Grok API
        raise NotImplementedError("Grok API集成待实现")

    async def execute_agent_pipeline(
        self, input_data: Dict[str, Any], agent_sequence: List[AgentType] = None
    ) -> Dict[AgentType, PromptExecutionResult]:
        """执行代理管道，按顺序执行多个代理"""
        if agent_sequence is None:
            agent_sequence = list(AgentType)

        results = {}

        for agent_type in agent_sequence:
            try:
                result = await self.execute_prompt(agent_type, input_data)
                results[agent_type] = result

                # 如果某个代理失败，可以选择继续或停止
                if not result.success:
                    self.logger.warning(
                        f"代理 {agent_type.value} 执行失败，继续执行下一个代理"
                    )

            except Exception as e:
                self.logger.error(f"代理 {agent_type.value} 执行异常: {e}")
                results[agent_type] = PromptExecutionResult(
                    success=False,
                    agent_type=agent_type,
                    input_data=input_data,
                    prompt_text="",
                    response="",
                    parsed_data={},
                    explanation="",
                    execution_time=0.0,
                    error=str(e),
                    validation_passed=False,
                )

        return results

    async def execute_parallel_agents(
        self, input_data: Dict[str, Any], agent_types: List[AgentType]
    ) -> Dict[AgentType, PromptExecutionResult]:
        """并行执行多个代理"""
        tasks = []

        for agent_type in agent_types:
            task = asyncio.create_task(self.execute_prompt(agent_type, input_data))
            tasks.append((agent_type, task))

        results = {}

        for agent_type, task in tasks:
            try:
                result = await task
                results[agent_type] = result
            except Exception as e:
                self.logger.error(f"并行执行代理 {agent_type.value} 失败: {e}")
                results[agent_type] = PromptExecutionResult(
                    success=False,
                    agent_type=agent_type,
                    input_data=input_data,
                    prompt_text="",
                    response="",
                    parsed_data={},
                    explanation="",
                    execution_time=0.0,
                    error=str(e),
                    validation_passed=False,
                )

        return results

    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        avg_execution_time = 0.0
        if self.execution_count > 0:
            avg_execution_time = self.total_execution_time / self.execution_count

        success_rate = 0.0
        if self.execution_count > 0:
            success_rate = self.success_count / self.execution_count

        return {
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": success_rate,
            "total_execution_time": self.total_execution_time,
            "avg_execution_time": avg_execution_time,
            "llm_provider": self.llm_config.provider.value,
            "model": self.llm_config.model,
        }

    def reset_stats(self):
        """重置统计信息"""
        self.execution_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_execution_time = 0.0

    async def test_connection(self) -> bool:
        """测试LLM连接"""
        try:
            test_prompt = "请回复'连接测试成功'"
            response = await self._call_llm(test_prompt)
            self.logger.info(f"LLM连接测试成功: {response}")
            return True
        except Exception as e:
            self.logger.error(f"LLM连接测试失败: {e}")
            return False


class HKPromptEngineManager:
    """港股Prompt引擎管理器"""

    def __init__(self):
        self.engines: Dict[str, HKPromptEngine] = {}
        self.logger = logging.getLogger("hk_quant_system.prompt_engine_manager")

    def add_engine(self, name: str, engine: HKPromptEngine):
        """添加引擎"""
        self.engines[name] = engine
        self.logger.info(f"添加Prompt引擎: {name}")

    def get_engine(self, name: str) -> Optional[HKPromptEngine]:
        """获取引擎"""
        return self.engines.get(name)

    def get_default_engine(self) -> Optional[HKPromptEngine]:
        """获取默认引擎"""
        if self.engines:
            return list(self.engines.values())[0]
        return None

    async def execute_with_engine(
        self, engine_name: str, agent_type: AgentType, input_data: Dict[str, Any]
    ) -> Optional[PromptExecutionResult]:
        """使用指定引擎执行"""
        engine = self.get_engine(engine_name)
        if not engine:
            self.logger.error(f"未找到引擎: {engine_name}")
            return None

        return await engine.execute_prompt(agent_type, input_data)

    def get_all_engines(self) -> Dict[str, HKPromptEngine]:
        """获取所有引擎"""
        return self.engines.copy()

    def remove_engine(self, name: str) -> bool:
        """移除引擎"""
        if name in self.engines:
            del self.engines[name]
            self.logger.info(f"移除Prompt引擎: {name}")
            return True
        return False

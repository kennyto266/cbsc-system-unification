"""
港股量化交易 AI Agent 系统Agent模块

这个模块包含了7个专业的AI Agent实现：
1. 量化分析师Agent
2. 量化交易员Agent
3. 投资组合经理Agent
4. 风险分析师Agent
5. 数据科学家Agent
6. 量化工程师Agent
7. 研究分析师Agent

以及Agent协调器，负责管理所有Agent的生命周期和协调。
"""

from .base_agent import BaseAgent
from .coordinator import AgentCoordinator

__all__ = ["AgentCoordinator", "BaseAgent"]

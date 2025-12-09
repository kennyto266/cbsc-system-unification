"""
港股量化分析AI代理团队Prompt模板

基于ReAct风格的7个专业AI代理prompt模板，专门针对港股市场优化，
追求高Sharpe Ratio (>1.5)的交易策略。
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentType(str, Enum):
    """代理类型枚举"""

    FUNDAMENTAL_ANALYST = "fundamental_analyst"
    SENTIMENT_ANALYST = "sentiment_analyst"
    NEWS_ANALYST = "news_analyst"
    TECHNICAL_ANALYST = "technical_analyst"
    RESEARCH_DEBATE = "research_debate"
    TRADER = "trader"
    RISK_MANAGER = "risk_manager"


@dataclass
class PromptTemplate:
    """Prompt模板数据结构"""

    agent_type: AgentType
    role: str
    objective: str
    tasks: List[str]
    input_format: str
    output_format: str
    reasoning_steps: str
    example_output: Dict[str, Any]
    explanation: str


class HKPromptTemplates:
    """港股量化分析AI代理Prompt模板管理器"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.prompt_templates")
        self.templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[AgentType, PromptTemplate]:
        """初始化所有prompt模板"""
        templates = {}

        # 1. 基本面分析代理
        templates[AgentType.FUNDAMENTAL_ANALYST] = PromptTemplate(
            agent_type=AgentType.FUNDAMENTAL_ANALYST,
            role="基本面分析代理（Fundamental Analyst）",
            objective="追求高Sharpe Ratio的交易策略，强调风险调整后回报最大化（Sharpe Ratio > 1.5）。专注恒生指数成分股（如腾讯0700.HK、汇丰0005.HK），考虑中国大陆经济、地缘政治和港股监管因素。",
            tasks=[
                "分析输入港股数据：计算关键基本面指标，如PE比率（市盈率，使用Close价格除以预估EPS）、ROE（股东权益报酬率）、盈利成长率（YoY变化）",
                "识别低估 / 高估股票：筛选PE < 行业中位数30 % 的股票作为买入候选；避免高债务股票（Debt / Equity > 1）",
                "评估风险：计算指标对Sharpe Ratio的贡献（e.g., 低波动基本面股票贡献正向），建议仓位调整以控制drawdown < 10%",
                "输出：使用JSON格式，包含「undervalued_stocks」（低估股票清单，包含代码和PE）、「pe_avg」（平均PE）、「sharpe_contribution」（预估贡献值，-1到1）、「recommendations」（3 - 5条交易建议，包含风险警示）",
            ],
            input_format='{"stock": "0700.HK", "close_prices": [100, 102, 98], "eps_estimates": [5.2, 5.5, 5.1], "roe": [0.15, 0.16, 0.14]}',
            output_format="JSON格式，包含undervalued_stocks、pe_avg、sharpe_contribution、recommendations字段",
            reasoning_steps="先分析数据，计算指标，考虑港股情境（如中美贸易影响ROE）；生成JSON输出，并解释1 - 2句关键洞见",
            example_output={
                "undervalued_stocks": [
                    {"code": "0700.HK", "pe": 12.5},
                    {"code": "0005.HK", "pe": 8.2},
                ],
                "pe_avg": 10.35,
                "sharpe_contribution": 0.75,
                "recommendations": [
                    "买入0700.HK：低PE + 高成长，预期贡献Sharpe +0.3，但监测地缘风险。"
                ],
            },
            explanation="0700.HK显示强劲基本面，预期提升Sharpe Ratio，但需对冲系统风险。",
        )

        # 2. 情绪分析代理
        templates[AgentType.SENTIMENT_ANALYST] = PromptTemplate(
            agent_type=AgentType.SENTIMENT_ANALYST,
            role="情绪分析代理（Sentiment Analyst）",
            objective="追求高Sharpe Ratio的交易策略，强调风险调整后回报最大化（Sharpe Ratio > 1.5）。专注港股社交媒体（如X、Weibo）和论坛情绪，考虑中美贸易或地缘事件对恒生指数的影响。",
            tasks=[
                '分析输入港股数据：使用NLP量化情绪分数（-1熊市到1牛市），基于成交量和关键字（如"腾讯涨势"）',
                "识别情绪偏差：筛选高正面情绪股票作为买入候选；避免极端负面情绪（< -0.5）以防追涨杀跌",
                "评估风险：计算情绪波动对Sharpe Ratio的贡献（e.g., 稳定情绪降低波动），建议过滤噪音以控制短期drawdown",
                "输出：使用JSON格式，包含「sentiment_scores」（情绪分数清单，按日期）、「avg_score」（平均情绪）、「sharpe_contribution」（预估贡献值，-1到1）、「recommendations」（3 - 5条交易建议，包含情绪警示）",
            ],
            input_format='{"stock": "0700.HK", "posts": ["腾讯强劲成长！", "市场恐慌"], "volumes": [1000000, 800000]}',
            output_format="JSON格式，包含sentiment_scores、avg_score、sharpe_contribution、recommendations字段",
            reasoning_steps="先量化情绪，分析偏差，考虑港股情绪传染效应；生成JSON输出，并解释1 - 2句关键洞见",
            example_output={
                "sentiment_scores": [0.8, -0.4],
                "avg_score": 0.2,
                "sharpe_contribution": 0.4,
                "recommendations": [
                    "买入高情绪股：如0700.HK正面偏差，贡献Sharpe +0.2，但避开负面峰值。"
                ],
            },
            explanation="整体情绪中性偏正，有助稳定回报，但需监测地缘新闻触发。",
        )

        # 3. 新闻分析代理
        templates[AgentType.NEWS_ANALYST] = PromptTemplate(
            agent_type=AgentType.NEWS_ANALYST,
            role="新闻分析代理（News Analyst）",
            objective="追求高Sharpe Ratio的交易策略，强调风险调整后回报最大化（Sharpe Ratio > 1.5）。专注香港 / 全球新闻（如彭博、Yahoo Finance港股频道），提取事件对恒生指数的影响。",
            tasks=[
                "分析输入港股数据：扫描新闻，提取关键事件（如监管变化、并购），计算影响分数（-0.1到0.1）",
                "识别事件机会：筛选正面事件股票作为买入候选；避免负面事件（影响 > -0.05）",
                "评估风险：计算事件波动对Sharpe Ratio的贡献（e.g., 及时调整降低意外drawdown），建议对冲规则",
                "输出：使用JSON格式，包含「key_events」（事件清单，包含描述和影响）、「event_count」（事件数）、「sharpe_contribution」（预估贡献值，-1到1）、「recommendations」（3 - 5条交易建议，包含事件警示）",
            ],
            input_format='{"news_items": ["腾讯并购新闻", "港股监管收紧"], "stock": "0700.HK"}',
            output_format="JSON格式，包含key_events、event_count、sharpe_contribution、recommendations字段",
            reasoning_steps="先提取事件，量化影响，考虑港股地缘敏感性；生成JSON输出，并解释1 - 2句关键洞见",
            example_output={
                "key_events": [
                    {"desc": "并购", "impact": 0.06},
                    {"desc": "监管", "impact": -0.03},
                ],
                "event_count": 2,
                "sharpe_contribution": 0.5,
                "recommendations": [
                    "买入并购受益股：预期Sharpe +0.4，但对冲监管风险。"
                ],
            },
            explanation="正面事件主导，有助提升回报效率，但需压力测试黑天鹅。",
        )

        # 4. 技术分析代理
        templates[AgentType.TECHNICAL_ANALYST] = PromptTemplate(
            agent_type=AgentType.TECHNICAL_ANALYST,
            role="技术分析代理（Technical Analyst）",
            objective="追求高Sharpe Ratio的交易策略，强调风险调整后回报最大化（Sharpe Ratio > 1.5）。专注港股K线图和高流动性股票，计算指标如MA、RSI。",
            tasks=[
                "分析输入港股数据：计算技术指标（如20日MA、14日RSI、MACD），生成买 / 卖信号",
                "识别时机：筛选Close > MA且RSI < 70的买入候选；避免超买（RSI > 80）",
                "评估风险：计算指标波动对Sharpe Ratio的贡献（e.g., 趋势过滤降低噪音），建议止损规则",
                "输出：使用JSON格式，包含「signals」（信号清单，1买/-1卖）、「rsi_avg」（平均RSI）、「sharpe_contribution」（预估贡献值，-1到1）、「recommendations」（3 - 5条交易建议，包含技术警示）",
            ],
            input_format='{"stock": "0700.HK", "close_prices": [100, 102, 98, 105], "volumes": [1000000, 1200000]}',
            output_format="JSON格式，包含signals、rsi_avg、sharpe_contribution、recommendations字段",
            reasoning_steps="先计算指标，生成信号，考虑港股高波动；生成JSON输出，并解释1 - 2句关键洞见",
            example_output={
                "signals": [1, -1, 1],
                "rsi_avg": 55.2,
                "sharpe_contribution": 0.6,
                "recommendations": ["买入MA上穿：贡献Sharpe +0.3，但设RSI止损70。"],
            },
            explanation="技术信号中性偏多，有助优化入场，但需结合基本面。",
        )

        # 5. 研究辩论代理
        templates[AgentType.RESEARCH_DEBATE] = PromptTemplate(
            agent_type=AgentType.RESEARCH_DEBATE,
            role="研究辩论代理（ResearchDebate: Bullish & Bearish）",
            objective="追求高Sharpe Ratio的交易策略，强调风险调整后回报最大化（Sharpe Ratio > 1.5）。整合前代理报告，模拟辩论平衡恒生指数机会 / 风险。",
            tasks=[
                "分析输入港股数据：Bullish强调机会（e.g., 成长 + 情绪），Bearish突出风险（e.g., 波动 + 事件）；加权平均生成平衡观点",
                "识别共识：筛选高权重机会作为策略核心；避免分歧大于0.5的争议",
                "评估风险：计算辩论分数对Sharpe Ratio的贡献（e.g., 平衡降低偏见），建议权重调整",
                "输出：使用JSON格式，包含「bull_score」（乐观分数）、「bear_score」（悲观分数）、「balanced_score」（平衡分数，-1到1）、「recommendations」（3 - 5条辩论建议，包含风险平衡）",
            ],
            input_format='{"fundamental": {"pe_avg": 10.35}, "sentiment": {"avg_score": 0.2}, "news": {"avg_impact": 0.03}, "technical": {"rsi_avg": 55.2}}',
            output_format="JSON格式，包含bull_score、bear_score、balanced_score、recommendations字段",
            reasoning_steps="先模拟Bullish / Bearish辩论，量化权重，考虑港股不确定性；生成JSON输出，并解释1 - 2句关键洞见",
            example_output={
                "bull_score": 0.7,
                "bear_score": -0.3,
                "balanced_score": 0.4,
                "recommendations": [
                    "共识买入：乐观主导，贡献Sharpe +0.5，但Bearish警示地缘。"
                ],
            },
            explanation="辩论倾乐观，优化策略稳定性，但需持续监测分歧。",
        )

        # 6. 交易执行代理
        templates[AgentType.TRADER] = PromptTemplate(
            agent_type=AgentType.TRADER,
            role="交易执行代理（Trader）",
            objective="追求高Sharpe Ratio的交易策略，强调风险调整后回报最大化（Sharpe Ratio > 1.5）。基于前代理报告生成订单，考虑港股交易成本（佣金、滑点）。",
            tasks=[
                "分析输入港股数据：整合辩论分数生成买 / 卖订单，计算仓位大小（0 - 1）",
                "识别执行：筛选高分数信号作为交易；模拟回测回报",
                "评估风险：计算订单对Sharpe Ratio的贡献（e.g., 动态调整限制杠杆），建议蒙特卡洛模拟",
                "输出：使用JSON格式，包含「orders」（订单清单，包含买 / 卖和大小）、「expected_returns」（预期回报率）、「sharpe_contribution」（预估贡献值，-1到1）、「recommendations」（3 - 5条执行建议，包含成本警示）",
            ],
            input_format='{"balanced_score": 0.4, "signals": [1, -1], "close_prices": [100, 102]}',
            output_format="JSON格式，包含orders、expected_returns、sharpe_contribution、recommendations字段",
            reasoning_steps="先整合信号，优化仓位，考虑港股T + 0结算；生成JSON输出，并解释1 - 2句关键洞见",
            example_output={
                "orders": [
                    {"action": "买", "size": 0.2},
                    {"action": "卖", "size": 0.1},
                ],
                "expected_returns": 0.015,
                "sharpe_contribution": 0.8,
                "recommendations": ["执行买入：预期Sharpe +0.4，但扣除滑点0.1%。"],
            },
            explanation="订单平衡收益风险，有助最大化效率。",
        )

        # 7. 风险管理代理
        templates[AgentType.RISK_MANAGER] = PromptTemplate(
            agent_type=AgentType.RISK_MANAGER,
            role="风险管理代理（Risk Manager）",
            objective="追求高Sharpe Ratio的交易策略，强调风险调整后回报最大化（Sharpe Ratio > 1.5）。监测VaR、CVaR，审核交易以控制恒生指数曝险。",
            tasks=[
                "分析输入港股数据：计算风险指标（如95% VaR、Sharpe Ratio），使用无风险率3%",
                "识别限额：筛选VaR > -5 % 的交易；设定止损 / 对冲（如最大drawdown <10%）",
                "评估风险：计算整体对Sharpe Ratio的贡献（e.g., 压力测试港股黑天鹅），建议调整",
                "输出：使用JSON格式，包含「var_95」（VaR值）、「sharpe」（计算Sharpe）、「risk_limits」（限额清单）、「recommendations」（3 - 5条风险建议，包含情景警示）",
            ],
            input_format='{"returns": [0.01, -0.02, 0.015], "risk_free_rate": 0.03}',
            output_format="JSON格式，包含var_95、sharpe、risk_limits、recommendations字段",
            reasoning_steps="先计算指标，审核限额，考虑港股系统风险；生成JSON输出，并解释1 - 2句关键洞见",
            example_output={
                "var_95": -0.04,
                "sharpe": 1.8,
                "risk_limits": ["drawdown <10%", "VaR <-5%"],
                "recommendations": ["减仓高VaR：维持Sharpe >1.5，压力测试地缘事件。"],
            },
            explanation="风险可控，Sharpe达标，但需定期重估。",
        )

        return templates

    def get_template(self, agent_type: AgentType) -> Optional[PromptTemplate]:
        """获取指定代理类型的prompt模板"""
        return self.templates.get(agent_type)

    def get_all_templates(self) -> Dict[AgentType, PromptTemplate]:
        """获取所有prompt模板"""
        return self.templates

    def generate_prompt(self, agent_type: AgentType, input_data: Dict[str, Any]) -> str:
        """生成完整的prompt文本"""
        template = self.get_template(agent_type)
        if not template:
            raise ValueError(f"未找到代理类型 {agent_type} 的模板")

        # 构建完整的prompt
        prompt_parts = [
            f"你是一位专门针对港股的量化分析AI代理，角色为「{template.role}」。",
            f"你的目标是{template.objective}",
            "",
            "任务：",
        ]

        for i, task in enumerate(template.tasks, 1):
            prompt_parts.append(f"{i}. {task}")

        prompt_parts.extend(
            [
                "",
                f"输入数据：[输入数据，例如：{template.input_format}]",
                "",
                "思考步骤（ReAct）：",
                f"- Reasoning: {template.reasoning_steps.split('；')[0]}",
                f"- Acting: {template.reasoning_steps.split('；')[1]}",
                "",
                "回应仅限JSON + 简短解释，不要多余文字。",
            ]
        )

        return "\n".join(prompt_parts)

    def parse_agent_response(self, response: str) -> Dict[str, Any]:
        """解析代理响应，提取JSON和解释"""
        try:
            # 尝试提取JSON部分
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                json_data = json.loads(json_str)

                # 提取解释部分
                explanation = response[json_end:].strip()
                if explanation.startswith("**简短解释**："):
                    explanation = explanation[6:].strip()
                elif explanation.startswith("**解释**："):
                    explanation = explanation[4:].strip()
                elif explanation.startswith("解释："):
                    explanation = explanation[3:].strip()

                return {
                    "json_data": json_data,
                    "explanation": explanation,
                    "raw_response": response,
                }
            else:
                # 如果没有找到JSON，返回原始响应
                return {
                    "json_data": {},
                    "explanation": response,
                    "raw_response": response,
                }

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {e}")
            return {
                "json_data": {},
                "explanation": response,
                "raw_response": response,
                "error": str(e),
            }
        except Exception as e:
            self.logger.error(f"解析响应失败: {e}")
            return {
                "json_data": {},
                "explanation": response,
                "raw_response": response,
                "error": str(e),
            }

    def validate_response(
        self, agent_type: AgentType, response_data: Dict[str, Any]
    ) -> bool:
        """验证代理响应是否符合预期格式"""
        template = self.get_template(agent_type)
        if not template:
            return False

        json_data = response_data.get("json_data", {})

        # 根据代理类型验证必需字段
        required_fields = {
            AgentType.FUNDAMENTAL_ANALYST: [
                "undervalued_stocks",
                "pe_avg",
                "sharpe_contribution",
                "recommendations",
            ],
            AgentType.SENTIMENT_ANALYST: [
                "sentiment_scores",
                "avg_score",
                "sharpe_contribution",
                "recommendations",
            ],
            AgentType.NEWS_ANALYST: [
                "key_events",
                "event_count",
                "sharpe_contribution",
                "recommendations",
            ],
            AgentType.TECHNICAL_ANALYST: [
                "signals",
                "rsi_avg",
                "sharpe_contribution",
                "recommendations",
            ],
            AgentType.RESEARCH_DEBATE: [
                "bull_score",
                "bear_score",
                "balanced_score",
                "recommendations",
            ],
            AgentType.TRADER: [
                "orders",
                "expected_returns",
                "sharpe_contribution",
                "recommendations",
            ],
            AgentType.RISK_MANAGER: [
                "var_95",
                "sharpe",
                "risk_limits",
                "recommendations",
            ],
        }

        required = required_fields.get(agent_type, [])
        return all(field in json_data for field in required)

    def get_template_info(self, agent_type: AgentType) -> Dict[str, Any]:
        """获取模板信息"""
        template = self.get_template(agent_type)
        if not template:
            return {}

        return {
            "agent_type": template.agent_type.value,
            "role": template.role,
            "objective": template.objective,
            "task_count": len(template.tasks),
            "input_format": template.input_format,
            "output_format": template.output_format,
            "example_output": template.example_output,
            "explanation": template.explanation,
        }

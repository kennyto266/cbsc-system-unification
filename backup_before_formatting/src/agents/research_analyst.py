"""
港股量化交易 AI Agent 系统 - 研究分析师Agent

负责学术文献研究、策略假设测试和量化研究开发。
通过科学的研究方法开发新的交易策略和验证现有策略的有效性。
"""

import asyncio
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..core import SystemConfig
from ..core.message_queue import Message, MessageQueue
from ..models.base import BaseModel, MessageType
from .base_agent import AgentConfig, BaseAgent
from .protocol import AgentProtocol, MessagePriority


class ResearchType(str, Enum):
    """研究类型"""

    ACADEMIC_LITERATURE = "academic_literature"
    STRATEGY_HYPOTHESIS = "strategy_hypothesis"
    MARKET_ANALYSIS = "market_analysis"
    RISK_MODELING = "risk_modeling"
    PERFORMANCE_ANALYSIS = "performance_analysis"


class HypothesisStatus(str, Enum):
    """假设状态"""

    PROPOSED = "proposed"
    TESTING = "testing"
    VALIDATED = "validated"
    REJECTED = "rejected"
    REFINED = "refined"


class ResearchPriority(str, Enum):
    """研究优先级"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ResearchConfig:
    """研究配置"""

    # 文献研究配置
    literature_sources: List[str] = field(
        default_factory=lambda: [
            "arXiv",
            "SSRN",
            "Journal of Finance",
            "Review of Financial Studies",
            "Journal of Financial Economics",
            "Quantitative Finance",
        ]
    )
    literature_keywords: List[str] = field(
        default_factory=lambda: [
            "quantitative trading",
            "algorithmic trading",
            "market microstructure",
            "risk management",
            "portfolio optimization",
            "machine learning",
            "high frequency trading",
            "market making",
        ]
    )

    # 策略研究配置
    max_concurrent_hypotheses: int = 5
    hypothesis_testing_period: int = 30  # 天
    validation_confidence_threshold: float = 0.8

    # 研究方法配置
    statistical_significance_level: float = 0.05
    minimum_sample_size: int = 252  # 交易日
    backtest_lookback_period: int = 1000  # 交易日

    # 报告配置
    report_generation_frequency: int = 7  # 天
    include_statistical_tests: bool = True
    include_risk_analysis: bool = True


@dataclass
class LiteraturePaper(BaseModel):
    """学术文献"""

    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    publication_date: datetime
    source: str
    keywords: List[str]
    relevance_score: float
    citation_count: int
    url: str
    summary: str
    key_findings: List[str]
    methodology: str
    data_requirements: List[str]


@dataclass
class ResearchHypothesis(BaseModel):
    """研究假设"""

    hypothesis_id: str
    title: str
    description: str
    research_type: ResearchType
    priority: ResearchPriority
    status: HypothesisStatus
    created_date: datetime
    expected_outcome: str
    methodology: str
    data_requirements: List[str]
    success_criteria: Dict[str, float]
    test_results: Optional[Dict[str, Any]] = None
    validation_date: Optional[datetime] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class ResearchReport(BaseModel):
    """研究报告"""

    report_id: str
    title: str
    research_type: ResearchType
    created_date: datetime
    summary: str
    key_findings: List[str]
    methodology: str
    data_analysis: Dict[str, Any]
    conclusions: List[str]
    recommendations: List[str]
    references: List[LiteraturePaper]
    hypothesis_results: List[ResearchHypothesis]
    statistical_tests: Dict[str, Any]
    risk_assessment: Dict[str, Any]


class LiteratureAnalyzer:
    """文献分析器"""

    def __init__(self, config: ResearchConfig):
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.research_analyst.literature")
        self.paper_database: Dict[str, LiteraturePaper] = {}

    async def search_literature(
        self, query: str, max_results: int = 20
    ) -> List[LiteraturePaper]:
        """搜索学术文献"""

        try:
            # 模拟文献搜索（实际实现中会调用真实的学术数据库API）
            papers = []

            for i in range(min(max_results, 10)):
                paper = LiteraturePaper(
                    id=f"paper_{i}_{datetime.now().timestamp()}",
                    paper_id=f"paper_{i}",
                    title=f"学术论文标题 {i}: {query}",
                    authors=[f"作者{i}_1", f"作者{i}_2"],
                    abstract=f"这是关于 {query} 的学术论文摘要。本研究探讨了量化交易中的关键问题...",
                    publication_date=datetime.now() - timedelta(days=i * 30),
                    source="Journal of Quantitative Finance",
                    keywords=[
                        "quantitative trading",
                        "algorithmic trading",
                        "risk management",
                    ],
                    relevance_score=0.8 - i * 0.05,
                    citation_count=50 - i * 5,
                    url=f"https://example.com / paper_{i}",
                    summary=f"论文 {i} 的核心发现是关于 {query} 的新方法...",
                    key_findings=[
                        f"发现{i}_1: 新的量化方法",
                        f"发现{i}_2: 改进的风险模型",
                        f"发现{i}_3: 更好的性能指标",
                    ],
                    methodology="统计建模和机器学习方法",
                    data_requirements=["历史价格数据", "成交量数据", "基本面数据"],
                    timestamp=datetime.now(),
                )
                papers.append(paper)
                self.paper_database[paper.paper_id] = paper

            self.logger.info(f'文献搜索完成: 查询 "{query}", 找到 {len(papers)} 篇论文')
            return papers

        except Exception as exc:
            self.logger.error(f"文献搜索失败: {exc}")
            return []

    async def analyze_paper_relevance(
        self, paper: LiteraturePaper, research_context: str
    ) -> float:
        """分析论文相关性"""

        try:
            # 基于关键词匹配和内容分析计算相关性分数
            relevance_score = 0.0

            # 关键词匹配
            context_keywords = research_context.lower().split()
            paper_keywords = [kw.lower() for kw in paper.keywords]

            keyword_matches = sum(1 for kw in context_keywords if kw in paper_keywords)
            relevance_score += min(keyword_matches / len(context_keywords), 1.0) * 0.4

            # 摘要分析
            abstract_lower = paper.abstract.lower()
            context_lower = research_context.lower()

            if any(
                keyword in abstract_lower
                for keyword in ["quantitative", "algorithmic", "trading"]
            ):
                relevance_score += 0.3

            if any(
                keyword in abstract_lower
                for keyword in ["risk", "portfolio", "optimization"]
            ):
                relevance_score += 0.2

            # 发表时间权重
            days_since_publication = (datetime.now() - paper.publication_date).days
            if days_since_publication < 365:  # 一年内
                relevance_score += 0.1

            return min(relevance_score, 1.0)

        except Exception as exc:
            self.logger.error(f"论文相关性分析失败: {exc}")
            return 0.0

    async def extract_key_insights(self, papers: List[LiteraturePaper]) -> List[str]:
        """提取关键洞察"""

        insights = []

        try:
            # 基于论文内容提取关键洞察
            for paper in papers:
                if paper.relevance_score > 0.7:
                    insights.extend(paper.key_findings)

            # 去重和排序
            unique_insights = list(set(insights))
            return unique_insights[:10]  # 返回前10个洞察

        except Exception as exc:
            self.logger.error(f"关键洞察提取失败: {exc}")
            return []


class HypothesisTester:
    """假设测试器"""

    def __init__(self, config: ResearchConfig):
        self.config = config
        self.logger = logging.getLogger(
            "hk_quant_system.research_analyst.hypothesis_tester"
        )
        self.active_hypotheses: Dict[str, ResearchHypothesis] = {}
        self.test_results: Dict[str, Dict[str, Any]] = {}

    async def create_hypothesis(
        self,
        title: str,
        description: str,
        research_type: ResearchType,
        priority: ResearchPriority = ResearchPriority.MEDIUM,
    ) -> ResearchHypothesis:
        """创建研究假设"""

        hypothesis = ResearchHypothesis(
            id=str(uuid.uuid4()),
            hypothesis_id=str(uuid.uuid4()),
            title=title,
            description=description,
            research_type=research_type,
            priority=priority,
            status=HypothesisStatus.PROPOSED,
            created_date=datetime.now(),
            expected_outcome="假设将在测试后确定",
            methodology="统计检验和回测分析",
            data_requirements=["历史价格数据", "交易量数据"],
            success_criteria={
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.1,
                "win_rate": 0.6,
                "statistical_significance": 0.05,
            },
            timestamp=datetime.now(),
        )

        self.active_hypotheses[hypothesis.hypothesis_id] = hypothesis

        self.logger.info(f"创建研究假设: {title}")
        return hypothesis

    async def test_hypothesis(
        self, hypothesis: ResearchHypothesis, market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """测试假设"""

        try:
            hypothesis.status = HypothesisStatus.TESTING

            # 模拟假设测试过程
            test_results = {
                "test_date": datetime.now(),
                "sample_size": len(market_data.get("price_data", [])),
                "statistical_tests": {},
                "performance_metrics": {},
                "risk_metrics": {},
                "conclusion": "",
            }

            # 模拟统计检验
            if hypothesis.research_type == ResearchType.STRATEGY_HYPOTHESIS:
                test_results["statistical_tests"] = {
                    "t_test": {"p_value": 0.03, "significant": True},
                    "mann_whitney": {"p_value": 0.02, "significant": True},
                    "chi_square": {"p_value": 0.15, "significant": False},
                }

                # 模拟性能指标
                test_results["performance_metrics"] = {
                    "sharpe_ratio": 1.8,
                    "max_drawdown": -0.08,
                    "win_rate": 0.65,
                    "total_return": 0.25,
                    "volatility": 0.15,
                }

                # 模拟风险指标
                test_results["risk_metrics"] = {
                    "var_95": -0.03,
                    "var_99": -0.05,
                    "expected_shortfall": -0.04,
                    "beta": 0.8,
                }

                # 判断假设是否成立
                if (
                    test_results["performance_metrics"]["sharpe_ratio"]
                    >= hypothesis.success_criteria["sharpe_ratio"]
                ):
                    hypothesis.status = HypothesisStatus.VALIDATED
                    test_results["conclusion"] = "假设成立，策略表现优异"
                else:
                    hypothesis.status = HypothesisStatus.REJECTED
                    test_results["conclusion"] = "假设不成立，策略表现未达预期"

            hypothesis.test_results = test_results
            hypothesis.validation_date = datetime.now()

            self.test_results[hypothesis.hypothesis_id] = test_results

            self.logger.info(
                f"假设测试完成: {hypothesis.title}, 状态: {hypothesis.status.value}"
            )
            return test_results

        except Exception as exc:
            self.logger.error(f"假设测试失败: {exc}")
            hypothesis.status = HypothesisStatus.REJECTED
            return {"error": str(exc)}

    async def refine_hypothesis(
        self, hypothesis: ResearchHypothesis, feedback: str
    ) -> ResearchHypothesis:
        """改进假设"""

        hypothesis.status = HypothesisStatus.REFINED
        hypothesis.notes.append(f"改进反馈: {feedback}")
        hypothesis.description += f"\n\n改进说明: {feedback}"

        self.logger.info(f"假设已改进: {hypothesis.title}")
        return hypothesis


class ResearchReportGenerator:
    """研究报告生成器"""

    def __init__(self, config: ResearchConfig):
        self.config = config
        self.logger = logging.getLogger(
            "hk_quant_system.research_analyst.report_generator"
        )

    async def generate_research_report(
        self,
        research_type: ResearchType,
        papers: List[LiteraturePaper],
        hypotheses: List[ResearchHypothesis],
        analysis_data: Dict[str, Any],
    ) -> ResearchReport:
        """生成研究报告"""

        try:
            report = ResearchReport(
                id=str(uuid.uuid4()),
                report_id=str(uuid.uuid4()),
                title=f"{research_type.value} 研究报告",
                research_type=research_type,
                created_date=datetime.now(),
                summary=self._generate_summary(papers, hypotheses, analysis_data),
                key_findings=self._extract_key_findings(papers, hypotheses),
                methodology=self._describe_methodology(research_type),
                data_analysis=analysis_data,
                conclusions=self._generate_conclusions(hypotheses),
                recommendations=self._generate_recommendations(
                    hypotheses, analysis_data
                ),
                references=papers,
                hypothesis_results=hypotheses,
                statistical_tests=self._compile_statistical_tests(hypotheses),
                risk_assessment=self._assess_risks(hypotheses, analysis_data),
                timestamp=datetime.now(),
            )

            self.logger.info(f"研究报告生成完成: {report.title}")
            return report

        except Exception as exc:
            self.logger.error(f"研究报告生成失败: {exc}")
            raise

    def _generate_summary(
        self,
        papers: List[LiteraturePaper],
        hypotheses: List[ResearchHypothesis],
        analysis_data: Dict[str, Any],
    ) -> str:
        """生成摘要"""

        summary = """
本研究报告基于 {len(papers)} 篇学术文献和 {len(hypotheses)} 个研究假设，
对量化交易策略进行了深入分析。

主要发现包括：
- 文献综述发现了 {len([p for p in papers if p.relevance_score > 0.7])} 篇高相关性论文
- 测试了 {len([h for h in hypotheses if h.status == HypothesisStatus.VALIDATED])} 个有效假设
- 分析了 {len(analysis_data.get('data_points', []))} 个数据点

研究结果表明，量化交易策略在风险控制和收益优化方面具有显著潜力。
        """.strip()

        return summary

    def _extract_key_findings(
        self, papers: List[LiteraturePaper], hypotheses: List[ResearchHypothesis]
    ) -> List[str]:
        """提取关键发现"""

        findings = []

        # 从文献中提取发现
        for paper in papers:
            if paper.relevance_score > 0.7:
                findings.extend(paper.key_findings)

        # 从假设测试中提取发现
        for hypothesis in hypotheses:
            if (
                hypothesis.status == HypothesisStatus.VALIDATED
                and hypothesis.test_results
            ):
                findings.append(f'假设 "{hypothesis.title}" 验证成功')

        return findings[:10]  # 返回前10个发现

    def _describe_methodology(self, research_type: ResearchType) -> str:
        """描述研究方法"""

        methodologies = {
            ResearchType.ACADEMIC_LITERATURE: "文献综述和内容分析方法",
            ResearchType.STRATEGY_HYPOTHESIS: "假设检验和统计分析方法",
            ResearchType.MARKET_ANALYSIS: "技术分析和基本面分析方法",
            ResearchType.RISK_MODELING: "风险建模和压力测试方法",
            ResearchType.PERFORMANCE_ANALYSIS: "绩效分析和回测验证方法",
        }

        return methodologies.get(research_type, "综合研究方法")

    def _generate_conclusions(self, hypotheses: List[ResearchHypothesis]) -> List[str]:
        """生成结论"""

        conclusions = []

        validated_count = len(
            [h for h in hypotheses if h.status == HypothesisStatus.VALIDATED]
        )
        total_count = len(hypotheses)

        conclusions.append(
            f"在 {total_count} 个测试假设中，{validated_count} 个假设得到验证"
        )

        if validated_count > 0:
            conclusions.append("验证的假设显示了量化策略的可行性")
            conclusions.append("建议进一步优化和实盘验证")
        else:
            conclusions.append("当前假设需要进一步改进")
            conclusions.append("建议重新审视策略设计")

        return conclusions

    def _generate_recommendations(
        self, hypotheses: List[ResearchHypothesis], analysis_data: Dict[str, Any]
    ) -> List[str]:
        """生成建议"""

        recommendations = []

        # 基于假设测试结果的建议
        validated_hypotheses = [
            h for h in hypotheses if h.status == HypothesisStatus.VALIDATED
        ]

        if validated_hypotheses:
            recommendations.append("实施已验证的策略假设")
            recommendations.append("建立风险监控机制")
            recommendations.append("定期评估策略性能")
        else:
            recommendations.append("重新设计策略假设")
            recommendations.append("增加数据样本量")
            recommendations.append("改进统计检验方法")

        # 基于分析数据的建议
        if analysis_data.get("correlation_analysis"):
            recommendations.append("关注资产间相关性变化")

        if analysis_data.get("volatility_regime"):
            recommendations.append("适应不同波动率环境")

        return recommendations

    def _compile_statistical_tests(
        self, hypotheses: List[ResearchHypothesis]
    ) -> Dict[str, Any]:
        """编译统计检验结果"""

        statistical_tests = {
            "total_hypotheses": len(hypotheses),
            "validated_hypotheses": len(
                [h for h in hypotheses if h.status == HypothesisStatus.VALIDATED]
            ),
            "test_methods": [],
            "overall_significance": 0.0,
        }

        for hypothesis in hypotheses:
            if (
                hypothesis.test_results
                and "statistical_tests" in hypothesis.test_results
            ):
                tests = hypothesis.test_results["statistical_tests"]
                statistical_tests["test_methods"].extend(tests.keys())

        # 计算整体显著性
        if hypotheses:
            significant_count = len(
                [
                    h
                    for h in hypotheses
                    if h.test_results
                    and h.test_results.get("statistical_tests", {})
                    .get("t_test", {})
                    .get("significant", False)
                ]
            )
            statistical_tests["overall_significance"] = significant_count / len(
                hypotheses
            )

        return statistical_tests

    def _assess_risks(
        self, hypotheses: List[ResearchHypothesis], analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """评估风险"""

        risk_assessment = {
            "overall_risk_level": "medium",
            "key_risks": [],
            "mitigation_strategies": [],
            "risk_metrics": {},
        }

        # 基于假设测试结果评估风险
        validated_hypotheses = [
            h for h in hypotheses if h.status == HypothesisStatus.VALIDATED
        ]

        if len(validated_hypotheses) < len(hypotheses) * 0.5:
            risk_assessment["overall_risk_level"] = "high"
            risk_assessment["key_risks"].append("策略验证率较低")
            risk_assessment["mitigation_strategies"].append("增加样本量和测试期间")

        # 基于性能指标评估风险
        for hypothesis in validated_hypotheses:
            if hypothesis.test_results and "risk_metrics" in hypothesis.test_results:
                risk_metrics = hypothesis.test_results["risk_metrics"]
                if risk_metrics.get("max_drawdown", 0) < -0.15:
                    risk_assessment["key_risks"].append("最大回撤过大")
                    risk_assessment["mitigation_strategies"].append("实施止损机制")

        return risk_assessment


class ResearchAnalystProtocol(AgentProtocol):
    """研究分析师协议"""

    def __init__(
        self,
        agent_id: str,
        message_queue: MessageQueue,
        research_agent: "ResearchAnalystAgent",
    ):
        super().__init__(agent_id, message_queue)
        self.research_agent = research_agent

    async def _process_control_command(
        self, command: str, parameters: Dict[str, Any], sender_id: str
    ):
        if command == "start_research":
            research_type = parameters.get("research_type", "strategy_hypothesis")
            await self.research_agent.start_research_project(research_type)
        elif command == "generate_report":
            research_type = parameters.get("research_type", "strategy_hypothesis")
            await self.research_agent.generate_research_report(research_type)
        elif command == "test_hypothesis":
            hypothesis_id = parameters.get("hypothesis_id")
            market_data = parameters.get("market_data", {})
            await self.research_agent.test_research_hypothesis(
                hypothesis_id, market_data
            )
        else:
            self.logger.warning(f"未知控制命令: {command}")


class ResearchAnalystAgent(BaseAgent):
    """研究分析师Agent"""

    def __init__(
        self,
        config: AgentConfig,
        message_queue: MessageQueue,
        system_config: SystemConfig = None,
    ):
        super().__init__(config, message_queue, system_config)
        self.research_config = ResearchConfig()
        self.literature_analyzer = LiteratureAnalyzer(self.research_config)
        self.hypothesis_tester = HypothesisTester(self.research_config)
        self.report_generator = ResearchReportGenerator(self.research_config)
        self.protocol = ResearchAnalystProtocol(config.agent_id, message_queue, self)

        # 研究状态
        self.active_research_projects: Dict[str, Dict[str, Any]] = {}
        self.research_reports: List[ResearchReport] = []

    async def initialize(self) -> bool:
        await self.protocol.initialize()
        self.logger.info(f"研究分析师Agent初始化完成: {self.config.agent_id}")
        return True

    async def process_message(self, message: Message) -> bool:
        try:
            await self.protocol.handle_incoming_message(message)
            return True
        except Exception as exc:
            self.logger.error("处理消息失败: %s", exc)
            return False

    async def cleanup(self):
        self.logger.info("研究分析师Agent清理完成")

    async def start_research_project(self, research_type: str) -> str:
        """启动研究项目"""

        try:
            research_type_enum = ResearchType(research_type)
            project_id = str(uuid.uuid4())

            # 创建研究项目
            project = {
                "project_id": project_id,
                "research_type": research_type_enum,
                "start_date": datetime.now(),
                "status": "active",
                "papers": [],
                "hypotheses": [],
                "analysis_data": {},
            }

            self.active_research_projects[project_id] = project

            # 启动文献研究
            if research_type_enum == ResearchType.ACADEMIC_LITERATURE:
                await self._conduct_literature_research(project_id)
            elif research_type_enum == ResearchType.STRATEGY_HYPOTHESIS:
                await self._develop_strategy_hypotheses(project_id)

            self.logger.info(f"研究项目启动: {project_id}, 类型: {research_type}")

            # 通知其他Agent
            await self.protocol.broadcast_message(
                message_type=MessageType.DATA,
                payload={
                    "data_type": "research_project_started",
                    "project_id": project_id,
                    "research_type": research_type,
                    "timestamp": datetime.now().isoformat(),
                },
                priority=MessagePriority.NORMAL,
            )

            return project_id

        except Exception as exc:
            self.logger.error(f"启动研究项目失败: {exc}")
            raise

    async def _conduct_literature_research(self, project_id: str):
        """进行文献研究"""

        project = self.active_research_projects.get(project_id)
        if not project:
            return

        try:
            # 搜索相关文献
            papers = await self.literature_analyzer.search_literature(
                "quantitative trading strategies", max_results=20
            )

            # 分析文献相关性
            for paper in papers:
                relevance = await self.literature_analyzer.analyze_paper_relevance(
                    paper, "量化交易策略研究"
                )
                paper.relevance_score = relevance

            # 提取关键洞察
            insights = await self.literature_analyzer.extract_key_insights(papers)

            project["papers"] = papers
            project["analysis_data"]["key_insights"] = insights

            self.logger.info(
                f"文献研究完成: 项目 {project_id}, 找到 {len(papers)} 篇论文"
            )

        except Exception as exc:
            self.logger.error(f"文献研究失败: {exc}")

    async def _develop_strategy_hypotheses(self, project_id: str):
        """开发策略假设"""

        project = self.active_research_projects.get(project_id)
        if not project:
            return

        try:
            # 创建策略假设
            hypotheses = [
                await self.hypothesis_tester.create_hypothesis(
                    title="动量策略假设",
                    description="基于价格动量的交易策略假设",
                    research_type=ResearchType.STRATEGY_HYPOTHESIS,
                    priority=ResearchPriority.HIGH,
                ),
                await self.hypothesis_tester.create_hypothesis(
                    title="均值回归策略假设",
                    description="基于价格均值回归的交易策略假设",
                    research_type=ResearchType.STRATEGY_HYPOTHESIS,
                    priority=ResearchPriority.MEDIUM,
                ),
                await self.hypothesis_tester.create_hypothesis(
                    title="波动率策略假设",
                    description="基于波动率变化的交易策略假设",
                    research_type=ResearchType.STRATEGY_HYPOTHESIS,
                    priority=ResearchPriority.MEDIUM,
                ),
            ]

            project["hypotheses"] = hypotheses

            self.logger.info(
                f"策略假设开发完成: 项目 {project_id}, 创建 {len(hypotheses)} 个假设"
            )

        except Exception as exc:
            self.logger.error(f"策略假设开发失败: {exc}")

    async def test_research_hypothesis(
        self, hypothesis_id: str, market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """测试研究假设"""

        try:
            # 查找假设
            hypothesis = None
            for project in self.active_research_projects.values():
                for h in project.get("hypotheses", []):
                    if h.hypothesis_id == hypothesis_id:
                        hypothesis = h
                        break
                if hypothesis:
                    break

            if not hypothesis:
                raise ValueError(f"假设不存在: {hypothesis_id}")

            # 测试假设
            test_results = await self.hypothesis_tester.test_hypothesis(
                hypothesis, market_data
            )

            self.logger.info(f"假设测试完成: {hypothesis.title}")

            # 通知其他Agent
            await self.protocol.broadcast_message(
                message_type=MessageType.DATA,
                payload={
                    "data_type": "hypothesis_test_completed",
                    "hypothesis_id": hypothesis_id,
                    "hypothesis_title": hypothesis.title,
                    "status": hypothesis.status.value,
                    "test_results": test_results,
                    "timestamp": datetime.now().isoformat(),
                },
                priority=MessagePriority.NORMAL,
            )

            return test_results

        except Exception as exc:
            self.logger.error(f"假设测试失败: {exc}")
            raise

    async def generate_research_report(self, research_type: str) -> ResearchReport:
        """生成研究报告"""

        try:
            research_type_enum = ResearchType(research_type)

            # 收集研究数据
            papers = []
            hypotheses = []
            analysis_data = {}

            for project in self.active_research_projects.values():
                if project["research_type"] == research_type_enum:
                    papers.extend(project.get("papers", []))
                    hypotheses.extend(project.get("hypotheses", []))
                    analysis_data.update(project.get("analysis_data", {}))

            # 生成报告
            report = await self.report_generator.generate_research_report(
                research_type_enum, papers, hypotheses, analysis_data
            )

            self.research_reports.append(report)

            self.logger.info(f"研究报告生成完成: {report.title}")

            # 通知其他Agent
            await self.protocol.broadcast_message(
                message_type=MessageType.DATA,
                payload={
                    "data_type": "research_report_generated",
                    "report_id": report.report_id,
                    "report_title": report.title,
                    "research_type": research_type,
                    "key_findings": report.key_findings,
                    "timestamp": datetime.now().isoformat(),
                },
                priority=MessagePriority.NORMAL,
            )

            return report

        except Exception as exc:
            self.logger.error(f"研究报告生成失败: {exc}")
            raise

    def get_research_summary(self) -> Dict[str, Any]:
        """获取研究摘要"""

        return {
            "active_projects": len(self.active_research_projects),
            "total_reports": len(self.research_reports),
            "total_hypotheses": sum(
                len(project.get("hypotheses", []))
                for project in self.active_research_projects.values()
            ),
            "validated_hypotheses": sum(
                len(
                    [
                        h
                        for h in project.get("hypotheses", [])
                        if h.status == HypothesisStatus.VALIDATED
                    ]
                )
                for project in self.active_research_projects.values()
            ),
            "protocol_stats": self.protocol.get_protocol_stats(),
        }


__all__ = [
    "ResearchAnalystAgent",
    "ResearchAnalystProtocol",
    "ResearchConfig",
    "LiteratureAnalyzer",
    "HypothesisTester",
    "ResearchReportGenerator",
    "LiteraturePaper",
    "ResearchHypothesis",
    "ResearchReport",
    "ResearchType",
    "HypothesisStatus",
    "ResearchPriority",
]

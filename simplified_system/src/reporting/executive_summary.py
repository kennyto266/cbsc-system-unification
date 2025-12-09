#!/usr / bin / env python3
"""
Executive Summary Generator
執行摘要生成器

AI - powered executive summary generation for trading reports
AI驅動的量化交易報告執行摘要生成
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from .report_generator import ReportData, ReportLanguage

logger = logging.getLogger(__name__)

class SummaryTone(Enum):
    """摘要語氣枚舉"""
    FORMAL = "formal"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    TECHNICAL = "technical"

@dataclass
class KeyInsight:
    """關鍵洞察"""
    category: str
    insight: str
    impact: str  # high, medium, low
    recommendation: Optional[str] = None
    supporting_data: Optional[Dict[str, Any]] = None

@dataclass
class ExecutiveSummary:
    """執行摘要結構"""
    title: str
    overview: str
    key_findings: List[KeyInsight]
    performance_highlights: Dict[str, Any]
    risk_assessment: str
    recommendations: List[str]
    conclusion: str
    next_steps: List[str]
    confidence_level: str  # high, medium, low

class ExecutiveSummaryGenerator:
    """執行摘要生成器"""

    def __init__(self):
        """初始化執行摘要生成器"""
        self.logger = logging.getLogger(__name__)

        # Performance thresholds for classification
        self.performance_thresholds = {
            'excellent_sharpe': 2.0,
            'good_sharpe': 1.5,
            'acceptable_sharpe': 1.0,
            'excellent_return': 0.20,  # 20% annual
            'good_return': 0.15,       # 15% annual
            'acceptable_return': 0.10,  # 10% annual
            'high_drawdown': -0.20,    # -20%
            'acceptable_drawdown': -0.15  # -15%
        }

        # Risk assessment criteria
        self.risk_criteria = {
            'high_risk': {'var_95': -0.05, 'max_drawdown': -0.25},
            'medium_risk': {'var_95': -0.03, 'max_drawdown': -0.15},
            'low_risk': {'var_95': -0.02, 'max_drawdown': -0.10}
        }

        # Templates for different scenarios
        self.summary_templates = self._load_templates()

    def generate(
        self,
        data: ReportData,
        language: ReportLanguage = ReportLanguage.BILINGUAL,
        tone: SummaryTone = SummaryTone.PROFESSIONAL
    ) -> str:
        """
        生成執行摘要

        Args:
            data: 報告數據
            language: 語言設置
            tone: 語氣設置

        Returns:
            格式化的執行摘要文本
        """
        try:
            self.logger.info("Generating executive summary")

            # Analyze performance
            performance_analysis = self._analyze_performance(data)

            # Generate key insights
            key_insights = self._generate_key_insights(data, performance_analysis)

            # Assess risk
            risk_assessment = self._assess_risk(data)

            # Generate recommendations
            recommendations = self._generate_recommendations(data, performance_analysis, risk_assessment)

            # Create summary structure
            summary = ExecutiveSummary(
                title = f"{data.strategy_name} 策略執行摘要" if language != ReportLanguage.ENGLISH
                      else f"{data.strategy_name} Strategy Executive Summary",
                overview = self._generate_overview(data, performance_analysis, language),
                key_findings = key_insights,
                performance_highlights = performance_analysis,
                risk_assessment = risk_assessment,
                recommendations = recommendations,
                conclusion = self._generate_conclusion(data, performance_analysis, language),
                next_steps = self._generate_next_steps(data, language),
                confidence_level = self._calculate_confidence_level(data)
            )

            # Format output
            formatted_summary = self._format_summary(summary, language, tone)

            self.logger.info("Executive summary generated successfully")
            return formatted_summary

        except Exception as e:
            self.logger.error(f"Error generating executive summary: {e}")
            return self._generate_fallback_summary(data, language)

    def _analyze_performance(self, data: ReportData) -> Dict[str, Any]:
        """分析策略表現"""
        analysis = {}

        # Categorize Sharpe ratio
        if data.sharpe_ratio >= self.performance_thresholds['excellent_sharpe']:
            sharpe_rating = "excellent"
            sharpe_desc = "優異的風險調整後收益"
        elif data.sharpe_ratio >= self.performance_thresholds['good_sharpe']:
            sharpe_rating = "good"
            sharpe_desc = "良好的風險調整後收益"
        elif data.sharpe_ratio >= self.performance_thresholds['acceptable_sharpe']:
            sharpe_rating = "acceptable"
            sharpe_desc = "可接受的風險調整後收益"
        else:
            sharpe_rating = "poor"
            sharpe_desc = "風險調整後收益不足"

        # Categorize returns
        if data.annual_return >= self.performance_thresholds['excellent_return']:
            return_rating = "excellent"
            return_desc = "卓越的年化收益率"
        elif data.annual_return >= self.performance_thresholds['good_return']:
            return_rating = "good"
            return_desc = "良好的年化收益率"
        elif data.annual_return >= self.performance_thresholds['acceptable_return']:
            return_rating = "acceptable"
            return_desc = "可接受的年化收益率"
        else:
            return_rating = "poor"
            return_desc = "年化收益率偏低"

        # Assess drawdown
        if data.max_drawdown <= self.performance_thresholds['high_drawdown']:
            drawdown_rating = "high"
            drawdown_desc = "回撤風險較高"
        elif data.max_drawdown <= self.performance_thresholds['acceptable_drawdown']:
            drawdown_rating = "acceptable"
            drawdown_desc = "回撤風險可控"
        else:
            drawdown_rating = "low"
            drawdown_desc = "回撤風險較低"

        # Win rate assessment
        if data.win_rate >= 0.60:
            win_rate_rating = "excellent"
            win_rate_desc = "勝率優異"
        elif data.win_rate >= 0.50:
            win_rate_rating = "good"
            win_rate_desc = "勝率良好"
        elif data.win_rate >= 0.40:
            win_rate_rating = "acceptable"
            win_rate_desc = "勝率尚可"
        else:
            win_rate_rating = "poor"
            win_rate_desc = "勝率偏低"

        analysis = {
            'sharpe_ratio': {
                'value': data.sharpe_ratio,
                'rating': sharpe_rating,
                'description': sharpe_desc
            },
            'annual_return': {
                'value': data.annual_return,
                'rating': return_rating,
                'description': return_desc
            },
            'max_drawdown': {
                'value': data.max_drawdown,
                'rating': drawdown_rating,
                'description': drawdown_desc
            },
            'win_rate': {
                'value': data.win_rate,
                'rating': win_rate_rating,
                'description': win_rate_desc
            },
            'overall_rating': self._calculate_overall_rating(sharpe_rating, return_rating, drawdown_rating)
        }

        return analysis

    def _generate_key_insights(
        self,
        data: ReportData,
        performance_analysis: Dict[str, Any]
    ) -> List[KeyInsight]:
        """生成關鍵洞察"""
        insights = []

        # Performance insights
        if performance_analysis['sharpe_ratio']['rating'] == 'excellent':
            insights.append(KeyInsight(
                category="績效表現",
                insight = f"策略表現優異，Sharpe比率達到{data.sharpe_ratio:.3f}",
                impact="high",
                recommendation="考慮適度增加配置",
                supporting_data={'sharpe_ratio': data.sharpe_ratio}
            ))

        if performance_analysis['max_drawdown']['rating'] == 'high':
            insights.append(KeyInsight(
                category="風險控制",
                insight = f"最大回撤{data.max_drawdown:.2%}較高，需要關注風險管理",
                impact="high",
                recommendation="建議加強止損機制",
                supporting_data={'max_drawdown': data.max_drawdown}
            ))

        # Trading insights
        if data.total_trades > 0:
            avg_trade_duration = 252 / data.total_trades if data.total_trades > 0 else 0
            if avg_trade_duration < 5:  # Less than 5 days
                insights.append(KeyInsight(
                    category="交易頻率",
                    insight="策略交易頻率較高，可能產生較高交易成本",
                    impact="medium",
                    recommendation="評估交易成本對淨收益的影響",
                    supporting_data={'avg_trade_duration': avg_trade_duration}
                ))

        # Risk insights
        if data.var_95 < -0.05:  # VaR 95% > 5%
            insights.append(KeyInsight(
                category="風險指標",
                insight = f"VaR(95%)為{data.var_95:.2%}，尾部風險較高",
                impact="medium",
                recommendation="考慮增加對沖或降低倉位",
                supporting_data={'var_95': data.var_95}
            ))

        # Strategy specific insights
        if 'rsi' in data.strategy_name.lower():
            if data.win_rate < 0.50:
                insights.append(KeyInsight(
                    category="策略特徵",
                    insight="RSI策略當前勝率偏低，可能需要調整參數",
                    impact="medium",
                    recommendation="優化RSI週期或閾值設置",
                    supporting_data={'win_rate': data.win_rate}
                ))

        return insights

    def _assess_risk(self, data: ReportData) -> str:
        """評估風險水平"""
        risk_factors = []

        # VaR assessment
        if data.var_95 <= self.risk_criteria['high_risk']['var_95']:
            risk_factors.append("高VaR風險")

        # Drawdown assessment
        if data.max_drawdown <= self.risk_criteria['high_risk']['max_drawdown']:
            risk_factors.append("高回撤風險")

        # Volatility assessment
        if data.volatility > 0.25:  # 25% annual volatility
            risk_factors.append("高波動率")

        # Concentration risk (if multiple trades concentrated in short period)
        if data.total_trades > 0:
            avg_return_per_trade = abs(data.annual_return) / data.total_trades
            if avg_return_per_trade < 0.001:  # Very small average returns
                risk_factors.append("收益集中度風險")

        if not risk_factors:
            return "整體風險水平可控，策略表現穩定"
        elif len(risk_factors) <= 2:
            return f"策略存在中等風險，主要關注：{', '.join(risk_factors)}"
        else:
            return f"策略風險較高，需要密切監控：{', '.join(risk_factors)}"

    def _generate_recommendations(
        self,
        data: ReportData,
        performance_analysis: Dict[str, Any],
        risk_assessment: str
    ) -> List[str]:
        """生成建議"""
        recommendations = []

        # Performance - based recommendations
        if performance_analysis['overall_rating'] in ['excellent', 'good']:
            recommendations.append("策略表現良好，可考慮適度增加資金配置")
        elif performance_analysis['overall_rating'] == 'acceptable':
            recommendations.append("策略表現尚可，建議繼續觀察並尋找優化機會")
        else:
            recommendations.append("策略表現有待改善，建議重新評估參數或策略邏輯")

        # Risk - based recommendations
        if "高" in risk_assessment:
            recommendations.append("實施更嚴格的風險管理措施，如降低倉位或加強止損")
            recommendations.append("考慮增加多元化投資以降低集中度風險")

        # Trading - based recommendations
        if data.total_trades > 100:  # High frequency trading
            recommendations.append("評估交易成本對策略收益的影響，考慮降低交易頻率")

        # Parameter optimization recommendations
        if data.win_rate < 0.45:
            recommendations.append("建議進行參數優化以提高勝率")

        # Market condition recommendations
        recommendations.append("定期監控市場環境變化，及時調整策略參數")

        return recommendations

    def _generate_overview(
        self,
        data: ReportData,
        performance_analysis: Dict[str, Any],
        language: ReportLanguage
    ) -> str:
        """生成概述"""
        if language == ReportLanguage.ENGLISH:
            return self._generate_overview_english(data, performance_analysis)
        else:
            return self._generate_overview_chinese(data, performance_analysis)

    def _generate_overview_chinese(
        self,
        data: ReportData,
        performance_analysis: Dict[str, Any]
    ) -> str:
        """生成中文概述"""
        overall_rating = performance_analysis['overall_rating']

        rating_desc = {
            'excellent': "優異",
            'good': "良好",
            'acceptable': "可接受",
            'poor': "需要改善"
        }

        overview = f"""
        本報告分析了{data.strategy_name}策略在{data.period期間的表現。

        策略總體表現評級為{rating_desc.get(overall_rating, '未知')}，年化收益率為{data.annual_return:.2%}，
        Sharpe比率為{data.sharpe_ratio:.3f}，最大回撤為{data.max_drawdown:.2%}。

        策略共執行{data.total_trades}次交易，勝率為{data.win_rate:.2%}，盈利因子為{data.profit_factor:.2f}。

        從風險指標來看，VaR(95%)為{data.var_95:.2%}，Beta系數為{data.beta:.3f}，
        顯示策略具有{self._describe_risk_profile(data.var_95)}的風險特徵。
        """

        return overview.strip()

    def _generate_overview_english(
        self,
        data: ReportData,
        performance_analysis: Dict[str, Any]
    ) -> str:
        """生成英文概述"""
        overall_rating = performance_analysis['overall_rating']

        rating_desc = {
            'excellent': "excellent",
            'good': "good",
            'acceptable': "acceptable",
            'poor': "needs improvement"
        }

        overview = f"""
        This report analyzes the performance of the {data.strategy_name} strategy during {data.period}.

        The strategy achieved an overall rating of {rating_desc.get(overall_rating, 'unknown')},
        with an annual return of {data.annual_return:.2%}, Sharpe ratio of {data.sharpe_ratio:.3f},
        and maximum drawdown of {data.max_drawdown:.2%}.

        The strategy executed {data.total_trades} trades with a win rate of {data.win_rate:.2%}
        and a profit factor of {data.profit_factor:.2f}.

        From a risk perspective, the VaR(95%) is {data.var_95:.2%} with a Beta of {data.beta:.3f},
        indicating {self._describe_risk_profile(data.var_95)} risk characteristics.
        """

        return overview.strip()

    def _describe_risk_profile(self, var_95: float) -> str:
        """描述風險特徵"""
        if var_95 > -0.02:
            return "較低風險"
        elif var_95 > -0.04:
            return "中等風險"
        else:
            return "較高風險"

    def _calculate_overall_rating(
        self,
        sharpe_rating: str,
        return_rating: str,
        drawdown_rating: str
    ) -> str:
        """計算綜合評級"""
        rating_scores = {
            'excellent': 4,
            'good': 3,
            'acceptable': 2,
            'poor': 1
        }

        # Special handling for drawdown (reverse scoring)
        drawdown_scores = {
            'low': 4,      # Low drawdown is good
            'acceptable': 3,
            'high': 1,
            'poor': 1
        }

        total_score = (
            rating_scores.get(sharpe_rating, 2) * 0.4 +
            rating_scores.get(return_rating, 2) * 0.3 +
            drawdown_scores.get(drawdown_rating, 2) * 0.3
        )

        if total_score >= 3.5:
            return 'excellent'
        elif total_score >= 2.5:
            return 'good'
        elif total_score >= 1.5:
            return 'acceptable'
        else:
            return 'poor'

    def _generate_conclusion(
        self,
        data: ReportData,
        performance_analysis: Dict[str, Any],
        language: ReportLanguage
    ) -> str:
        """生成結論"""
        overall_rating = performance_analysis['overall_rating']

        if language == ReportLanguage.ENGLISH:
            conclusions = {
                'excellent': f"The {data.strategy_name} strategy demonstrates exceptional performance with strong risk - adjusted returns. Consider increasing allocation while maintaining risk monitoring.",
                'good': f"The {data.strategy_name} strategy shows solid performance with good risk management. Continue monitoring and consider optimization opportunities.",
                'acceptable': f"The {data.strategy_name} strategy delivers acceptable returns but has room for improvement. Focus on parameter optimization and risk management.",
                'poor': f"The {data.strategy_name} strategy requires significant improvement. Consider revising the strategy logic or parameters."
            }
        else:
            conclusions = {
                'excellent': f"{data.strategy_name}策略表現卓越，風險調整後收益優異。建議在保持風險監控的前提下適度增加配置。",
                'good': f"{data.strategy_name}策略表現良好，風險管理到位。建議繼續監控並尋找優化機會。",
                'acceptable': f"{data.strategy_name}策略表現尚可，但仍有改善空間。建議專注於參數優化和風險管理。",
                'poor': f"{data.strategy_name}策略表現需要大幅改善。建議重新評估策略邏輯或調整參數。"
            }

        return conclusions.get(overall_rating, conclusions['acceptable'])

    def _generate_next_steps(self, data: ReportData, language: ReportLanguage) -> List[str]:
        """生成下一步行動"""
        if language == ReportLanguage.ENGLISH:
            return [
                "Review strategy performance in different market conditions",
                "Consider parameter optimization based on recent market data",
                "Implement enhanced risk management protocols",
                "Monitor strategy correlation with other portfolio components",
                "Schedule regular performance reviews"
            ]
        else:
            return [
                "在不同市場條件下回測策略表現",
                "根據最新市場數據考慮參數優化",
                "實施增強的風險管理協議",
                "監控策略與投資組合其他部分的相關性",
                "安排定期的績效評估"
            ]

    def _calculate_confidence_level(self, data: ReportData) -> str:
        """計算信心水平"""
        # Factors affecting confidence
        factors = []

        # Sample size (number of trades)
        if data.total_trades > 100:
            factors.append(0.4)
        elif data.total_trades > 50:
            factors.append(0.3)
        else:
            factors.append(0.2)

        # Consistency (Sharpe ratio stability)
        if data.sharpe_ratio > 1.5:
            factors.append(0.3)
        elif data.sharpe_ratio > 1.0:
            factors.append(0.2)
        else:
            factors.append(0.1)

        # Risk control
        if data.max_drawdown > -0.15:
            factors.append(0.3)
        elif data.max_drawdown > -0.25:
            factors.append(0.2)
        else:
            factors.append(0.1)

        confidence_score = sum(factors)

        if confidence_score >= 0.8:
            return "high"
        elif confidence_score >= 0.5:
            return "medium"
        else:
            return "low"

    def _format_summary(
        self,
        summary: ExecutiveSummary,
        language: ReportLanguage,
        tone: SummaryTone
    ) -> str:
        """格式化摘要輸出"""
        if language == ReportLanguage.BILINGUAL:
            return self._format_bilingual_summary(summary, tone)
        elif language == ReportLanguage.ENGLISH:
            return self._format_english_summary(summary, tone)
        else:
            return self._format_chinese_summary(summary, tone)

    def _format_chinese_summary(
        self,
        summary: ExecutiveSummary,
        tone: SummaryTone
    ) -> str:
        """格式化中文摘要"""
        formatted = f"""
# {summary.title}

## 執行摘要

{summary.overview}

## 關鍵洞察
"""
        for insight in summary.key_findings:
            formatted += f"""
### {insight.category}
**洞察 * *: {insight.insight}
**影響程度 * *: {insight.impact}
**建議 * *: {insight.recommendation or '無'}
"""

        formatted += f"""
## 績效亮點
- **年化收益率 * *: {summary.performance_highlights.get('annual_return', {}).get('value', 0):.2%}
- **Sharpe比率 * *: {summary.performance_highlights.get('sharpe_ratio', {}).get('value', 0):.3f}
- **最大回撤 * *: {summary.performance_highlights.get('max_drawdown', {}).get('value', 0):.2%}
- **勝率 * *: {summary.performance_highlights.get('win_rate', {}).get('value', 0):.2%}
- **總體評級 * *: {summary.performance_highlights.get('overall_rating', '未知')}

## 風險評估
{summary.risk_assessment}

## 建議措施
"""
        for i, rec in enumerate(summary.recommendations, 1):
            formatted += f"{i}. {rec}\n"

        formatted += f"""
## 結論
{summary.conclusion}

## 下一步行動
"""
        for i, step in enumerate(summary.next_steps, 1):
            formatted += f"{i}. {step}\n"

        formatted += f"""
## 信心水平
{summary.confidence_level}

---

*報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        return formatted

    def _format_english_summary(
        self,
        summary: ExecutiveSummary,
        tone: SummaryTone
    ) -> str:
        """格式化英文摘要"""
        formatted = f"""
# {summary.title}

## Executive Summary

{summary.overview}

## Key Insights
"""
        for insight in summary.key_findings:
            formatted += f"""
### {insight.category}
**Insight * *: {insight.insight}
**Impact * *: {insight.impact}
**Recommendation * *: {insight.recommendation or 'None'}
"""

        formatted += f"""
## Performance Highlights
- **Annual Return * *: {summary.performance_highlights.get('annual_return', {}).get('value', 0):.2%}
- **Sharpe Ratio * *: {summary.performance_highlights.get('sharpe_ratio', {}).get('value', 0):.3f}
- **Maximum Drawdown * *: {summary.performance_highlights.get('max_drawdown', {}).get('value', 0):.2%}
- **Win Rate * *: {summary.performance_highlights.get('win_rate', {}).get('value', 0):.2%}
- **Overall Rating * *: {summary.performance_highlights.get('overall_rating', 'Unknown')}

## Risk Assessment
{summary.risk_assessment}

## Recommendations
"""
        for i, rec in enumerate(summary.recommendations, 1):
            formatted += f"{i}. {rec}\n"

        formatted += f"""
## Conclusion
{summary.conclusion}

## Next Steps
"""
        for i, step in enumerate(summary.next_steps, 1):
            formatted += f"{i}. {step}\n"

        formatted += f"""
## Confidence Level
{summary.confidence_level}

---

*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        return formatted

    def _format_bilingual_summary(
        self,
        summary: ExecutiveSummary,
        tone: SummaryTone
    ) -> str:
        """格式化雙語摘要"""
        # Generate both Chinese and English versions
        chinese_version = self._format_chinese_summary(summary, tone)
        english_version = self._format_english_summary(summary, tone)

        # Combine with clear separation
        return f"""
{chinese_version}

---

# English Version

{english_version}
"""

    def _generate_fallback_summary(self, data: ReportData, language: ReportLanguage) -> str:
        """生成後備摘要"""
        if language == ReportLanguage.ENGLISH:
            return f"""
            # Strategy Analysis Summary

            The {data.strategy_name} strategy achieved {data.annual_return:.2%} annual return
            with a Sharpe ratio of {data.sharpe_ratio:.3f} and maximum drawdown of {data.max_drawdown:.2%}.

            Total trades: {data.total_trades}
            Win rate: {data.win_rate:.2%}
            Profit factor: {data.profit_factor:.2f}

            Risk metrics:
            - VaR(95%): {data.var_95:.2%}
            - Beta: {data.beta:.3f}
            - Volatility: {data.volatility:.2%}
            """
        else:
            return f"""
            # 策略分析摘要

            {data.strategy_name}策略實現了{data.annual_return:.2%}的年化收益率，
            Sharpe比率為{data.sharpe_ratio:.3f}，最大回撤為{data.max_drawdown:.2%}。

            總交易次數：{data.total_trades}
            勝率：{data.win_rate:.2%}
            盈利因子：{data.profit_factor:.2f}

            風險指標：
            - VaR(95%)：{data.var_95:.2%}
            - Beta系數：{data.beta:.3f}
            - 波動率：{data.volatility:.2%}
            """

    def _load_templates(self) -> Dict[str, Any]:
        """加載摘要模板"""
        # Could load from external files, for now return empty dict
        return {}
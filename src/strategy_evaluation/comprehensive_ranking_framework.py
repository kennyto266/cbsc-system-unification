#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CBSC策略综合排名框架
Comprehensive CBSC Strategy Ranking Framework

机构级策略评估、排名和选择系统，提供多维度的策略比较和投资者画像匹配
Institutional-grade strategy evaluation, ranking, and selection system with multi-dimensional comparison and investor profiling
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path
from abc import ABC, abstractmethod
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class InvestorProfile(Enum):
    """投资者画像枚举"""
    AGGRESSIVE = "aggressive"           # 激进型：高收益容忍度
    BALANCED = "balanced"               # 平衡型：风险收益优化
    CONSERVATIVE = "conservative"       # 保守型：资本保护优先
    INSTITUTIONAL = "institutional"     # 机构型：严格风控要求
    RETAIL = "retail"                   # 散户型：简单易懂优先

@dataclass
class RiskMetrics:
    """风险指标数据类"""
    # 波动性指标
    daily_volatility: float
    annualized_volatility: float
    downside_volatility: float

    # 回撤指标
    max_drawdown: float
    average_drawdown: float
    max_drawdown_duration: int
    recovery_time: int

    # 尾部风险
    var_95: float = 0.0
    var_99: float = 0.0
    cvar_95: float = 0.0
    cvar_99: float = 0.0

    # 流动性风险
    liquidity_score: float = 0.0
    market_impact: float = 0.0

@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    # 基础收益指标
    total_return: float
    annual_return: float
    quarterly_returns: List[float]
    monthly_returns: List[float]

    # 风险调整收益
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    information_ratio: float = 0.0

    # 交易指标
    win_rate: float
    profit_factor: float
    avg_win: float = 0.0
    avg_loss: float = 0.0
    total_trades: int = 0
    trading_costs: float = 0.0

    # 稳定性指标
    rolling_sharpe_std: float = 0.0
    monthly_hit_rate: float = 0.0
    quarter_consistency: float = 0.0
    performance_persistence: float = 0.0

    # 市场相关性
    beta: float = 1.0
    alpha: float = 0.0
    correlation: float = 0.0

@dataclass
class RankingWeights:
    """排名权重配置"""
    # 激进型权重
    aggressive_weights: Dict[str, float] = field(default_factory=lambda: {
        'total_return': 0.35,
        'sharpe_ratio': 0.20,
        'max_drawdown': 0.10,
        'win_rate': 0.15,
        'calmar_ratio': 0.10,
        'consistency': 0.05,
        'cost_efficiency': 0.05
    })

    # 平衡型权重
    balanced_weights: Dict[str, float] = field(default_factory=lambda: {
        'total_return': 0.20,
        'sharpe_ratio': 0.25,
        'max_drawdown': 0.20,
        'win_rate': 0.15,
        'calmar_ratio': 0.10,
        'consistency': 0.07,
        'cost_efficiency': 0.03
    })

    # 保守型权重
    conservative_weights: Dict[str, float] = field(default_factory=lambda: {
        'total_return': 0.10,
        'sharpe_ratio': 0.20,
        'max_drawdown': 0.35,
        'win_rate': 0.10,
        'calmar_ratio': 0.15,
        'consistency': 0.07,
        'cost_efficiency': 0.03
    })

@dataclass
class StrategyRanking:
    """策略排名结果"""
    strategy_name: str
    strategy_type: str
    parameters: Dict[str, Any]

    # 综合排名
    overall_score: float
    overall_rank: int

    # 分项排名
    aggressive_rank: int
    balanced_rank: int
    conservative_rank: int
    institutional_rank: int

    # 分项评分
    aggressive_score: float
    balanced_score: float
    conservative_score: float
    institutional_score: float

    # 风险等级
    risk_level: str
    risk_score: float

    # 适合的投资者类型
    suitable_profiles: List[InvestorProfile]

    # 性能指标
    performance_metrics: PerformanceMetrics
    risk_metrics: RiskMetrics

    # 评级和建议
    rating: str  # AAA, AA, A, BBB, BB, B, CCC
    recommendation: str
    warning_flags: List[str]

class StrategyEvaluator(ABC):
    """策略评估器抽象基类"""

    @abstractmethod
    def evaluate(self, strategy_data: Dict[str, Any]) -> Tuple[PerformanceMetrics, RiskMetrics]:
        """评估策略性能和风险"""
        pass

class CompositeStrategyEvaluator(StrategyEvaluator):
    """复合策略评估器"""

    def __init__(self, evaluators: List[StrategyEvaluator]):
        self.evaluators = evaluators

    def evaluate(self, strategy_data: Dict[str, Any]) -> Tuple[PerformanceMetrics, RiskMetrics]:
        """综合多个评估器结果"""
        all_performance = []
        all_risk = []

        for evaluator in self.evaluators:
            perf, risk = evaluator.evaluate(strategy_data)
            all_performance.append(perf)
            all_risk.append(risk)

        # 加权平均综合结果
        performance = self._aggregate_performance(all_performance)
        risk = self._aggregate_risk(all_risk)

        return performance, risk

    def _aggregate_performance(self, performances: List[PerformanceMetrics]) -> PerformanceMetrics:
        """聚合性能指标"""
        if not performances:
            raise ValueError("No performance metrics to aggregate")

        # 简单平均聚合（可根据需要改为加权）
        return PerformanceMetrics(
            total_return=np.mean([p.total_return for p in performances]),
            annual_return=np.mean([p.annual_return for p in performances]),
            quarterly_returns=[],
            monthly_returns=[],
            sharpe_ratio=np.mean([p.sharpe_ratio for p in performances]),
            sortino_ratio=np.mean([p.sortino_ratio for p in performances]),
            calmar_ratio=np.mean([p.calmar_ratio for p in performances]),
            information_ratio=np.mean([p.information_ratio for p in performances]),
            win_rate=np.mean([p.win_rate for p in performances]),
            profit_factor=np.mean([p.profit_factor for p in performances]),
            total_trades=int(np.mean([p.total_trades for p in performances])),
            trading_costs=np.mean([p.trading_costs for p in performances]),
            rolling_sharpe_std=np.mean([p.rolling_sharpe_std for p in performances]),
            monthly_hit_rate=np.mean([p.monthly_hit_rate for p in performances]),
            quarter_consistency=np.mean([p.quarter_consistency for p in performances]),
            performance_persistence=np.mean([p.performance_persistence for p in performances]),
            beta=np.mean([p.beta for p in performances]),
            alpha=np.mean([p.alpha for p in performances]),
            correlation=np.mean([p.correlation for p in performances])
        )

    def _aggregate_risk(self, risks: List[RiskMetrics]) -> RiskMetrics:
        """聚合风险指标"""
        if not risks:
            raise ValueError("No risk metrics to aggregate")

        return RiskMetrics(
            daily_volatility=np.mean([r.daily_volatility for r in risks]),
            annualized_volatility=np.mean([r.annualized_volatility for r in risks]),
            downside_volatility=np.mean([r.downside_volatility for r in risks]),
            max_drawdown=max([r.max_drawdown for r in risks]),  # 取最大值
            average_drawdown=np.mean([r.average_drawdown for r in risks]),
            max_drawdown_duration=max([r.max_drawdown_duration for r in risks]),
            recovery_time=max([r.recovery_time for r in risks]),
            var_95=np.mean([r.var_95 for r in risks]),
            var_99=np.mean([r.var_99 for r in risks]),
            cvar_95=np.mean([r.cvar_95 for r in risks]),
            cvar_99=np.mean([r.cvar_99 for r in risks]),
            liquidity_score=np.mean([r.liquidity_score for r in risks]),
            market_impact=np.mean([r.market_impact for r in risks])
        )

class ComprehensiveRankingFramework:
    """
    CBSC策略综合排名框架

    提供机构级的策略评估、排名和选择功能：
    - 多维度性能评估
    - 投资者画像匹配
    - 风险等级分类
    - 动态权重调整
    - 实时排名更新
    """

    def __init__(self, evaluator: StrategyEvaluator, weights: Optional[RankingWeights] = None):
        """
        初始化综合排名框架

        Args:
            evaluator: 策略评估器
            weights: 排名权重配置
        """
        self.evaluator = evaluator
        self.weights = weights or RankingWeights()

        # 排名统计
        self.ranking_stats = {
            'total_evaluations': 0,
            'top_10_updated': 0,
            'profile_matches': 0,
            'risk_assessments': 0
        }

        # 缓存机制
        self.strategy_cache = {}
        self.ranking_cache = {}

        logger.info("Comprehensive Ranking Framework initialized")

    def evaluate_strategy_batch(self, strategies_data: List[Dict[str, Any]]) -> List[StrategyRanking]:
        """
        批量评估策略并生成排名

        Args:
            strategies_data: 策略数据列表

        Returns:
            策略排名结果列表
        """
        logger.info(f"Evaluating {len(strategies_data)} strategies for comprehensive ranking...")

        strategy_rankings = []

        for i, strategy_data in enumerate(strategies_data):
            try:
                logger.info(f"Evaluating strategy {i+1}/{len(strategies_data)}: {strategy_data.get('strategy_name', 'Unknown')}")

                # 评估策略性能和风险
                performance_metrics, risk_metrics = self.evaluator.evaluate(strategy_data)

                # 计算各投资者类型的评分
                scores = self._calculate_profile_scores(performance_metrics, risk_metrics)

                # 计算综合评分
                overall_score = self._calculate_overall_score(scores)

                # 风险评估
                risk_assessment = self._assess_risk_level(risk_metrics, performance_metrics)

                # 生成评级和建议
                rating, recommendation, warnings = self._generate_rating_and_recommendation(
                    performance_metrics, risk_metrics, scores
                )

                # 确定适合的投资者类型
                suitable_profiles = self._determine_suitable_profiles(scores, risk_assessment['risk_level'])

                # 创建策略排名对象
                ranking = StrategyRanking(
                    strategy_name=strategy_data.get('strategy_name', f'Strategy_{i}'),
                    strategy_type=strategy_data.get('strategy_type', 'Unknown'),
                    parameters=strategy_data.get('parameters', {}),

                    overall_score=overall_score,
                    overall_rank=0,  # 稍后设置

                    aggressive_rank=0,  # 稍后设置
                    balanced_rank=0,    # 稍后设置
                    conservative_rank=0,  # 稍后设置
                    institutional_rank=0,  # 稍后设置

                    aggressive_score=scores['aggressive'],
                    balanced_score=scores['balanced'],
                    conservative_score=scores['conservative'],
                    institutional_score=scores['institutional'],

                    risk_level=risk_assessment['risk_level'],
                    risk_score=risk_assessment['risk_score'],

                    suitable_profiles=suitable_profiles,

                    performance_metrics=performance_metrics,
                    risk_metrics=risk_metrics,

                    rating=rating,
                    recommendation=recommendation,
                    warning_flags=warnings
                )

                strategy_rankings.append(ranking)

            except Exception as e:
                logger.error(f"Failed to evaluate strategy {i+1}: {str(e)}")
                continue

        # 计算排名
        self._calculate_ranks(strategy_rankings)

        # 更新统计
        self.ranking_stats['total_evaluations'] += len(strategy_rankings)

        return strategy_rankings

    def _calculate_profile_scores(self, performance: PerformanceMetrics, risk: RiskMetrics) -> Dict[str, float]:
        """计算各投资者类型的评分"""

        # 标准化各项指标到0-100范围
        normalized_metrics = self._normalize_metrics(performance, risk)

        # 计算各投资者类型评分
        scores = {}

        # 激进型评分
        scores['aggressive'] = self._calculate_weighted_score(
            normalized_metrics, self.weights.aggressive_weights
        )

        # 平衡型评分
        scores['balanced'] = self._calculate_weighted_score(
            normalized_metrics, self.weights.balanced_weights
        )

        # 保守型评分
        scores['conservative'] = self._calculate_weighted_score(
            normalized_metrics, self.weights.conservative_weights
        )

        # 机构型评分（类似保守型，但更注重稳定性）
        institutional_weights = self.weights.conservative_weights.copy()
        institutional_weights['consistency'] = 0.15  # 提高稳定性权重
        institutional_weights['cost_efficiency'] = 0.05
        scores['institutional'] = self._calculate_weighted_score(
            normalized_metrics, institutional_weights
        )

        return scores

    def _normalize_metrics(self, performance: PerformanceMetrics, risk: RiskMetrics) -> Dict[str, float]:
        """标准化指标到0-100范围"""

        normalized = {}

        # 收益类指标
        normalized['total_return'] = min(max(performance.total_return * 20, 0), 100)  # 500% = 100分
        normalized['sharpe_ratio'] = min(max(performance.sharpe_ratio * 25, 0), 100)  # 4.0 = 100分
        normalized['calmar_ratio'] = min(max(performance.calmar_ratio * 50, 0), 100)  # 2.0 = 100分

        # 风险类指标（负向指标，需要转换）
        normalized['max_drawdown'] = max(0, 100 - abs(risk.max_drawdown) * 400)  # 25%回撤 = 0分
        normalized['volatility'] = max(0, 100 - risk.annualized_volatility * 200)  # 50%波动率 = 0分

        # 交易指标
        normalized['win_rate'] = performance.win_rate * 100
        normalized['cost_efficiency'] = max(0, 100 - (performance.trading_costs / max(abs(performance.total_return), 0.01)) * 100)

        # 稳定性指标
        normalized['consistency'] = (
            performance.monthly_hit_rate * 50 +
            performance.quarter_consistency * 30 +
            max(0, 100 - performance.rolling_sharpe_std * 1000)
        ) / 80 * 100

        return normalized

    def _calculate_weighted_score(self, normalized_metrics: Dict[str, float], weights: Dict[str, float]) -> float:
        """计算加权评分"""
        score = 0.0
        total_weight = 0.0

        for metric, weight in weights.items():
            if metric in normalized_metrics:
                score += normalized_metrics[metric] * weight
                total_weight += weight

        return score / total_weight if total_weight > 0 else 0

    def _calculate_overall_score(self, profile_scores: Dict[str, float]) -> float:
        """计算综合评分"""
        # 简单平均，可以根据需要调整权重
        return np.mean(list(profile_scores.values()))

    def _assess_risk_level(self, risk: RiskMetrics, performance: PerformanceMetrics) -> Dict[str, Any]:
        """评估风险等级"""

        # 综合风险评分
        drawdown_risk = abs(risk.max_drawdown)
        volatility_risk = risk.annualized_volatility
        tail_risk = abs(risk.var_99) + abs(risk.cvar_99)

        overall_risk_score = (
            drawdown_risk * 0.4 +
            volatility_risk * 0.3 +
            tail_risk * 0.2 +
            (1 - performance.win_rate) * 0.1
        )

        # 风险等级分类
        if overall_risk_score < 0.15:
            risk_level = "LOW"
        elif overall_risk_score < 0.25:
            risk_level = "MEDIUM"
        elif overall_risk_score < 0.40:
            risk_level = "HIGH"
        else:
            risk_level = "VERY_HIGH"

        return {
            'risk_level': risk_level,
            'risk_score': overall_risk_score * 100,  # 转换为0-100分
            'drawdown_contribution': drawdown_risk * 40,
            'volatility_contribution': volatility_risk * 30,
            'tail_contribution': tail_risk * 20,
            'performance_contribution': (1 - performance.win_rate) * 10
        }

    def _generate_rating_and_recommendation(
        self,
        performance: PerformanceMetrics,
        risk: RiskMetrics,
        scores: Dict[str, float]
    ) -> Tuple[str, str, List[str]]:
        """生成评级和建议"""

        warnings = []

        # 计算综合评分（用于评级）
        overall_score = np.mean(list(scores.values()))

        # 生成评级
        if overall_score >= 90:
            rating = "AAA"
            recommendation = "强烈推荐：顶级策略，各方面表现优异"
        elif overall_score >= 80:
            rating = "AA"
            recommendation = "推荐：优秀策略，适合大多数投资者"
        elif overall_score >= 70:
            rating = "A"
            recommendation = "审慎推荐：良好策略，适合特定投资者"
        elif overall_score >= 60:
            rating = "BBB"
            recommendation = "中性：一般策略，需要密切监控"
        elif overall_score >= 50:
            rating = "BB"
            recommendation = "谨慎：有潜力策略，风险较高"
        elif overall_score >= 40:
            rating = "B"
            recommendation = "高风险：仅适合专业投资者"
        else:
            rating = "CCC"
            recommendation = "极高风险：不建议投资"

        # 生成警告标志
        if abs(risk.max_drawdown) > 0.30:
            warnings.append("高风险回撤")

        if performance.sharpe_ratio < 0.5:
            warnings.append("低Sharpe比率")

        if performance.win_rate < 0.40:
            warnings.append("低胜率")

        if performance.trading_costs > abs(performance.total_return) * 0.1:
            warnings.append("高交易成本")

        if performance.rolling_sharpe_std > 1.0:
            warnings.append("高波动性")

        return rating, recommendation, warnings

    def _determine_suitable_profiles(self, scores: Dict[str, float], risk_level: str) -> List[InvestorProfile]:
        """确定适合的投资者类型"""
        suitable_profiles = []

        # 基于评分和风险等级确定适合的投资者类型
        max_score = max(scores.values())

        if scores['aggressive'] >= max_score * 0.9 and risk_level in ['HIGH', 'VERY_HIGH']:
            suitable_profiles.append(InvestorProfile.AGGRESSIVE)

        if scores['balanced'] >= max_score * 0.9 and risk_level in ['MEDIUM', 'HIGH']:
            suitable_profiles.append(InvestorProfile.BALANCED)

        if scores['conservative'] >= max_score * 0.9 and risk_level in ['LOW', 'MEDIUM']:
            suitable_profiles.append(InvestorProfile.CONSERVATIVE)

        if scores['institutional'] >= max_score * 0.9 and risk_level in ['LOW', 'MEDIUM']:
            suitable_profiles.append(InvestorProfile.INSTITUTIONAL)

        # 默认包含平衡型
        if not suitable_profiles:
            suitable_profiles.append(InvestorProfile.BALANCED)

        return suitable_profiles

    def _calculate_ranks(self, strategy_rankings: List[StrategyRanking]) -> None:
        """计算各项排名"""

        # 总体排名
        sorted_by_overall = sorted(strategy_rankings, key=lambda x: x.overall_score, reverse=True)
        for i, ranking in enumerate(sorted_by_overall, 1):
            ranking.overall_rank = i

        # 激进型排名
        sorted_by_aggressive = sorted(strategy_rankings, key=lambda x: x.aggressive_score, reverse=True)
        for i, ranking in enumerate(sorted_by_aggressive, 1):
            ranking.aggressive_rank = i

        # 平衡型排名
        sorted_by_balanced = sorted(strategy_rankings, key=lambda x: x.balanced_score, reverse=True)
        for i, ranking in enumerate(sorted_by_balanced, 1):
            ranking.balanced_rank = i

        # 保守型排名
        sorted_by_conservative = sorted(strategy_rankings, key=lambda x: x.conservative_score, reverse=True)
        for i, ranking in enumerate(sorted_by_conservative, 1):
            ranking.conservative_rank = i

        # 机构型排名
        sorted_by_institutional = sorted(strategy_rankings, key=lambda x: x.institutional_score, reverse=True)
        for i, ranking in enumerate(sorted_by_institutional, 1):
            ranking.institutional_rank = i

    def get_top_10_strategies(self, strategy_rankings: List[StrategyRanking],
                            profile: Optional[InvestorProfile] = None) -> List[StrategyRanking]:
        """
        获取Top 10策略

        Args:
            strategy_rankings: 策略排名列表
            profile: 投资者类型，如果指定则返回该类型的前10名

        Returns:
            Top 10策略列表
        """
        if profile is None:
            # 总体排名前10
            top_strategies = sorted(strategy_rankings, key=lambda x: x.overall_score, reverse=True)[:10]
        else:
            # 按投资者类型排名前10
            if profile == InvestorProfile.AGGRESSIVE:
                top_strategies = sorted(strategy_rankings, key=lambda x: x.aggressive_score, reverse=True)[:10]
            elif profile == InvestorProfile.BALANCED:
                top_strategies = sorted(strategy_rankings, key=lambda x: x.balanced_score, reverse=True)[:10]
            elif profile == InvestorProfile.CONSERVATIVE:
                top_strategies = sorted(strategy_rankings, key=lambda x: x.conservative_score, reverse=True)[:10]
            elif profile == InvestorProfile.INSTITUTIONAL:
                top_strategies = sorted(strategy_rankings, key=lambda x: x.institutional_score, reverse=True)[:10]
            else:
                top_strategies = sorted(strategy_rankings, key=lambda x: x.overall_score, reverse=True)[:10]

        # 更新统计
        self.ranking_stats['top_10_updated'] += 1

        return top_strategies

    def generate_comprehensive_report(
        self,
        strategy_rankings: List[StrategyRanking],
        output_file: Optional[str] = None
    ) -> str:
        """
        生成综合排名报告

        Args:
            strategy_rankings: 策略排名列表
            output_file: 输出文件路径

        Returns:
            报告内容
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        report_lines = [
            "# CBSC策略综合排名报告",
            f"生成时间: {timestamp}",
            f"评估策略总数: {len(strategy_rankings)}",
            "",
            "## 排名概览",
            ""
        ]

        # Top 10策略概览
        top_10 = self.get_top_10_strategies(strategy_rankings)
        report_lines.extend([
            "### Top 10 策略概览",
            "| 排名 | 策略名称 | 综合评分 | Sharpe比率 | 最大回撤 | 胜率 | 风险等级 | 评级 |",
            "|------|----------|----------|------------|----------|------|----------|------|"
        ])

        for ranking in top_10:
            report_lines.append(
                f"| {ranking.overall_rank} | {ranking.strategy_name} | {ranking.overall_score:.2f} | "
                f"{ranking.performance_metrics.sharpe_ratio:.3f} | {ranking.risk_metrics.max_drawdown*100:.2f}% | "
                f"{ranking.performance_metrics.win_rate*100:.2f}% | {ranking.risk_level} | {ranking.rating} |"
            )

        report_lines.extend(["", "## 投资者类型排名", ""])

        # 各投资者类型Top 5
        for profile in [InvestorProfile.AGGRESSIVE, InvestorProfile.BALANCED, InvestorProfile.CONSERVATIVE]:
            profile_top_5 = self.get_top_10_strategies(strategy_rankings, profile)[:5]

            profile_name = {
                InvestorProfile.AGGRESSIVE: "激进型",
                InvestorProfile.BALANCED: "平衡型",
                InvestorProfile.CONSERVATIVE: "保守型"
            }[profile]

            report_lines.extend([
                f"### {profile_name}投资者 Top 5",
                "| 排名 | 策略名称 | 评分 | 总收益 | 最大回撤 | 适合度 |",
                "|------|----------|------|--------|----------|--------|"
            ])

            for ranking in profile_top_5:
                score = getattr(ranking, f"{profile.value}_score")
                report_lines.append(
                    f"| {getattr(ranking, f'{profile.value}_rank')} | {ranking.strategy_name} | "
                    f"{score:.2f} | {ranking.performance_metrics.total_return*100:.2f}% | "
                    f"{ranking.risk_metrics.max_drawdown*100:.2f}% | "
                    f"{'✓' if profile in ranking.suitable_profiles else '✗'} |"
                )

            report_lines.append("")

        # 风险分析
        risk_distribution = {}
        for ranking in strategy_rankings:
            level = ranking.risk_level
            risk_distribution[level] = risk_distribution.get(level, 0) + 1

        total_strategies = len(strategy_rankings)
        report_lines.extend([
            "## 风险等级分布",
            f"- 低风险: {risk_distribution.get('LOW', 0)} ({risk_distribution.get('LOW', 0)/total_strategies:.1%})",
            f"- 中风险: {risk_distribution.get('MEDIUM', 0)} ({risk_distribution.get('MEDIUM', 0)/total_strategies:.1%})",
            f"- 高风险: {risk_distribution.get('HIGH', 0)} ({risk_distribution.get('HIGH', 0)/total_strategies:.1%})",
            f"- 极高风险: {risk_distribution.get('VERY_HIGH', 0)} ({risk_distribution.get('VERY_HIGH', 0)/total_strategies:.1%})",
            ""
        ])

        # 评级分布
        rating_distribution = {}
        for ranking in strategy_rankings:
            rating = ranking.rating
            rating_distribution[rating] = rating_distribution.get(rating, 0) + 1

        report_lines.extend([
            "## 评级分布",
            f"- AAA级: {rating_distribution.get('AAA', 0)}",
            f"- AA级: {rating_distribution.get('AA', 0)}",
            f"- A级: {rating_distribution.get('A', 0)}",
            f"- BBB级: {rating_distribution.get('BBB', 0)}",
            f"- BB级: {rating_distribution.get('BB', 0)}",
            f"- B级: {rating_distribution.get('B', 0)}",
            f"- CCC级: {rating_distribution.get('CCC', 0)}",
            ""
        ])

        # 投资建议
        report_lines.extend([
            "## 投资建议",
            "",
            "### 激进型投资者",
            "- 推荐关注Top 3激进型策略",
            "- 可承受较高回撤以换取高收益",
            "- 建议配置仓位不超过总投资的30%",
            "",
            "### 平衡型投资者",
            "- 推荐选择Top 5平衡型策略",
            "- 注重风险调整后收益",
            "- 建议分散投资于2-3个策略",
            "",
            "### 保守型投资者",
            "- 仅推荐A级及以上低风险策略",
            "- 优先考虑资本保护",
            "- 建议配置仓位不超过总投资的20%",
            "",
            "### 风险警示",
            "- 过去表现不代表未来收益",
            "- 建议进行敏感性分析和压力测试",
            "- 定期监控策略表现并及时调整",
            "- 注意市场环境变化对策略的影响",
            ""
        ])

        report_content = '\n'.join(report_lines)

        # 保存报告
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"Comprehensive ranking report saved to: {output_file}")

        return report_content

    def get_framework_summary(self) -> Dict[str, Any]:
        """获取框架总结"""
        return {
            'ranking_statistics': self.ranking_stats,
            'evaluation_weights': {
                'aggressive': self.weights.aggressive_weights,
                'balanced': self.weights.balanced_weights,
                'conservative': self.weights.conservative_weights
            },
            'cache_status': {
                'strategy_cache_size': len(self.strategy_cache),
                'ranking_cache_size': len(self.ranking_cache)
            }
        }

# 便利函数
def quick_strategy_ranking(strategies_data: List[Dict[str, Any]],
                         evaluator: Optional[StrategyEvaluator] = None) -> Dict[str, Any]:
    """
    快速策略排名

    Args:
        strategies_data: 策略数据列表
        evaluator: 策略评估器

    Returns:
        排名结果
    """
    if evaluator is None:
        # 使用默认评估器
        from .strategy_evaluator import DefaultStrategyEvaluator
        evaluator = DefaultStrategyEvaluator()

    framework = ComprehensiveRankingFramework(evaluator)

    # 评估并排名策略
    strategy_rankings = framework.evaluate_strategy_batch(strategies_data)

    # 获取各类型Top 10
    results = {
        'overall_top_10': framework.get_top_10_strategies(strategy_rankings),
        'aggressive_top_10': framework.get_top_10_strategies(strategy_rankings, InvestorProfile.AGGRESSIVE),
        'balanced_top_10': framework.get_top_10_strategies(strategy_rankings, InvestorProfile.BALANCED),
        'conservative_top_10': framework.get_top_10_strategies(strategy_rankings, InvestorProfile.CONSERVATIVE),
        'all_rankings': strategy_rankings,
        'framework_summary': framework.get_framework_summary()
    }

    # 生成报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"strategy_ranking_report_{timestamp}.md"
    framework.generate_comprehensive_report(strategy_rankings, report_file)
    results['report_file'] = report_file

    return results

if __name__ == "__main__":
    print("CBSC策略综合排名框架已就绪")
    print("使用 quick_strategy_ranking() 函数进行快速排名")
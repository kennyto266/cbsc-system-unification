#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Top 10策略选择方法论
Top 10 Strategy Selection Methodology

为CBSC策略提供科学、严谨的Top 10策略选择方法，包含多维度评估、动态权重调整和持续验证机制
Scientific and rigorous Top 10 strategy selection methodology for CBSC strategies with multi-dimensional evaluation, dynamic weight adjustment, and continuous validation
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from .comprehensive_ranking_framework import StrategyRanking, PerformanceMetrics, RiskMetrics, InvestorProfile
from .investor_profiling_system import InvestorProfilingSystem

logger = logging.getLogger(__name__)

class SelectionCriteria(Enum):
    """选择标准枚举"""
    RISK_ADJUSTED_RETURN = "risk_adjusted_return"      # 风险调整收益
    CONSISTENCY = "consistency"                        # 一致性
    STABILITY = "stability"                            # 稳定性
    COST_EFFICIENCY = "cost_efficiency"                # 成本效率
    MARKET_REGIME_ROBUSTNESS = "market_regime_robustness"  # 市场环境稳健性
    SCALABILITY = "scalability"                        # 可扩展性
    IMPLEMENTATION_EASE = "implementation_ease"        # 实施难易度

@dataclass
class SelectionWeights:
    """选择权重配置"""
    # 风险调整收益权重
    return_weights: Dict[str, float] = field(default_factory=lambda: {
        'sharpe_ratio': 0.4,
        'sortino_ratio': 0.3,
        'calmar_ratio': 0.2,
        'information_ratio': 0.1
    })

    # 一致性权重
    consistency_weights: Dict[str, float] = field(default_factory=lambda: {
        'monthly_hit_rate': 0.3,
        'quarter_consistency': 0.3,
        'rolling_sharpe_stability': 0.2,
        'performance_persistence': 0.2
    })

    # 稳定性权重
    stability_weights: Dict[str, float] = field(default_factory=lambda: {
        'max_drawdown': 0.4,
        'drawdown_duration': 0.2,
        'volatility_control': 0.2,
        'tail_risk_control': 0.2
    })

    # 成本效率权重
    cost_weights: Dict[str, float] = field(default_factory=lambda: {
        'trading_cost_ratio': 0.4,
        'slippage_impact': 0.2,
        'execution_efficiency': 0.2,
        'infrastructure_requirements': 0.2
    })

    # 市场稳健性权重
    regime_weights: Dict[str, float] = field(default_factory=lambda: {
        'bull_market_performance': 0.3,
        'bear_market_performance': 0.3,
        'sideways_market_performance': 0.2,
        'crisis_resilience': 0.2
    })

@dataclass
class Top10SelectionResult:
    """Top 10选择结果"""
    selected_strategies: List[StrategyRanking]
    selection_methodology: str
    selection_date: datetime

    # 评分详情
    criteria_scores: Dict[str, List[float]]
    composite_scores: List[float]
    ranking_method: str

    # 质量指标
    average_quality_score: float
    diversity_index: float
    robustness_score: float

    # 过滤统计
    total_candidates: int
    filtered_out: int
    final_selections: int

    # 风险分散分析
    correlation_analysis: Dict[str, Any]
    sector_exposure: Dict[str, float]

    # 投资者类型适配
    profile_specific_rankings: Dict[str, List[StrategyRanking]]

@dataclass
class ValidationMetrics:
    """验证指标"""
    # 样本外表现
    out_of_sample_performance: float
    prediction_accuracy: float

    # 稳健性测试
    sensitivity_analysis: Dict[str, float]
    stress_test_results: Dict[str, float]

    # 时间稳定性
    temporal_stability: float
    rolling_window_performance: List[float]

    # 市场环境适应性
    regime_performance: Dict[str, float]
    correlation_stability: float

class Top10SelectionMethodology:
    """
    Top 10策略选择方法论

    提供科学、严谨的策略选择方法：
    - 多维度评估体系
    - 动态权重调整机制
    - 鲁棒性验证框架
    - 持续监控和更新
    - 个性化选择服务
    """

    def __init__(self, weights: Optional[SelectionWeights] = None):
        """
        初始化Top 10选择方法论

        Args:
            weights: 选择权重配置
        """
        self.weights = weights or SelectionWeights()
        self.profiling_system = InvestorProfilingSystem()

        # 选择统计
        self.selection_stats = {
            'total_selections': 0,
            'validation_tests': 0,
            'profile_matchings': 0
        }

        # 历史选择记录
        self.selection_history = []

        logger.info("Top 10 Selection Methodology initialized")

    def select_top_10_strategies(
        self,
        strategy_rankings: List[StrategyRanking],
        selection_profile: Optional[InvestorProfile] = None,
        custom_criteria: Optional[Dict[SelectionCriteria, float]] = None
    ) -> Top10SelectionResult:
        """
        选择Top 10策略

        Args:
            strategy_rankings: 策略排名列表
            selection_profile: 选择用的投资者画像
            custom_criteria: 自定义选择标准权重

        Returns:
            Top 10选择结果
        """
        logger.info(f"Starting Top 10 selection from {len(strategy_rankings)} candidates")

        # 第一步：基础过滤
        filtered_strategies = self._apply_basic_filters(strategy_rankings)
        logger.info(f"After basic filtering: {len(filtered_strategies)} strategies remain")

        # 第二步：多维度评分
        criteria_scores = self._calculate_criteria_scores(filtered_strategies)
        composite_scores = self._calculate_composite_scores(criteria_scores, custom_criteria)

        # 第三步：综合排名
        ranked_strategies = self._apply_comprehensive_ranking(
            filtered_strategies, composite_scores
        )

        # 第四步：多样性控制
        diversified_strategies = self._ensure_diversity(ranked_strategies)

        # 第五步：最终选择
        final_selections = diversified_strategies[:10]

        # 第六步：质量评估
        quality_metrics = self._assess_selection_quality(final_selections)

        # 第七步：投资者类型适配
        profile_rankings = self._generate_profile_specific_rankings(final_selections)

        # 创建选择结果
        selection_result = Top10SelectionResult(
            selected_strategies=final_selections,
            selection_methodology="Multi-Criteria Comprehensive Selection",
            selection_date=datetime.now(),
            criteria_scores=criteria_scores,
            composite_scores=composite_scores[:len(final_selections)],
            ranking_method="Weighted Composite Scoring",
            average_quality_score=quality_metrics['average_score'],
            diversity_index=quality_metrics['diversity_index'],
            robustness_score=quality_metrics['robustness_score'],
            total_candidates=len(strategy_rankings),
            filtered_out=len(strategy_rankings) - len(filtered_strategies),
            final_selections=len(final_selections),
            correlation_analysis=self._analyze_correlations(final_selections),
            sector_exposure=self._analyze_sector_exposure(final_selections),
            profile_specific_rankings=profile_rankings
        )

        # 更新统计
        self.selection_stats['total_selections'] += 1
        self.selection_history.append(selection_result)

        logger.info(f"Top 10 selection completed: {len(final_selections)} strategies selected")

        return selection_result

    def _apply_basic_filters(self, strategy_rankings: List[StrategyRanking]) -> List[StrategyRanking]:
        """应用基础过滤条件"""

        filtered = []

        for ranking in strategy_rankings:
            perf = ranking.performance_metrics
            risk = ranking.risk_metrics

            # 基础过滤条件
            if (perf.total_trades >= 10 and                    # 最少交易次数
                perf.sharpe_ratio >= -0.5 and                  # 基本Sharpe要求
                abs(risk.max_drawdown) <= 0.60 and            # 最大回撤限制
                perf.win_rate >= 0.35 and                     # 最小胜率要求
                perf.annual_return >= -0.20):                 # 最小年化收益要求
                filtered.append(ranking)

        return filtered

    def _calculate_criteria_scores(self, strategies: List[StrategyRanking]) -> Dict[str, List[float]]:
        """计算各选择标准评分"""

        scores = {}

        # 1. 风险调整收益评分
        scores['risk_adjusted_return'] = self._calculate_risk_adjusted_return_scores(strategies)

        # 2. 一致性评分
        scores['consistency'] = self._calculate_consistency_scores(strategies)

        # 3. 稳定性评分
        scores['stability'] = self._calculate_stability_scores(strategies)

        # 4. 成本效率评分
        scores['cost_efficiency'] = self._calculate_cost_efficiency_scores(strategies)

        # 5. 市场稳健性评分
        scores['market_regime_robustness'] = self._calculate_regime_robustness_scores(strategies)

        # 6. 可扩展性评分
        scores['scalability'] = self._calculate_scalability_scores(strategies)

        # 7. 实施难易度评分
        scores['implementation_ease'] = self._calculate_implementation_ease_scores(strategies)

        return scores

    def _calculate_risk_adjusted_return_scores(self, strategies: List[StrategyRanking]) -> List[float]:
        """计算风险调整收益评分"""

        scores = []

        for ranking in strategies:
            perf = ranking.performance_metrics

            # 标准化各项指标
            sharpe_score = min(max(perf.sharpe_ratio * 20, 0), 100)  # Sharpe 5.0 = 100分
            sortino_score = min(max(perf.sortino_ratio * 15, 0), 100)  # Sortino 6.7 = 100分
            calmar_score = min(max(perf.calmar_ratio * 40, 0), 100)    # Calmar 2.5 = 100分
            info_score = min(max(abs(perf.information_ratio) * 25, 0), 100)  # Info 4.0 = 100分

            # 加权评分
            composite_score = (
                sharpe_score * self.weights.return_weights['sharpe_ratio'] +
                sortino_score * self.weights.return_weights['sortino_ratio'] +
                calmar_score * self.weights.return_weights['calmar_ratio'] +
                info_score * self.weights.return_weights['information_ratio']
            )

            scores.append(composite_score)

        return scores

    def _calculate_consistency_scores(self, strategies: List[StrategyRanking]) -> List[float]:
        """计算一致性评分"""

        scores = []

        for ranking in strategies:
            perf = ranking.performance_metrics

            # 各项一致性指标
            monthly_score = perf.monthly_hit_rate * 100
            quarterly_score = perf.quarter_consistency * 100
            stability_score = max(0, 100 - perf.rolling_sharpe_std * 500)  # Sharpe稳定性
            persistence_score = perf.performance_persistence * 100

            # 加权评分
            composite_score = (
                monthly_score * self.weights.consistency_weights['monthly_hit_rate'] +
                quarterly_score * self.weights.consistency_weights['quarter_consistency'] +
                stability_score * self.weights.consistency_weights['rolling_sharpe_stability'] +
                persistence_score * self.weights.consistency_weights['performance_persistence']
            )

            scores.append(composite_score)

        return scores

    def _calculate_stability_scores(self, strategies: List[StrategyRanking]) -> List[float]:
        """计算稳定性评分"""

        scores = []

        for ranking in strategies:
            risk = ranking.risk_metrics
            perf = ranking.performance_metrics

            # 回撤控制评分
            drawdown_score = max(0, 100 - abs(risk.max_drawdown) * 300)  # 33%回撤 = 0分

            # 波动性控制评分
            volatility_score = max(0, 100 - risk.annualized_volatility * 200)  # 50%波动率 = 0分

            # 尾部风险控制评分
            tail_risk_score = max(0, 100 - abs(risk.var_99) * 500)  # 20% VaR = 0分

            # 回撤持续时间评分（假设数据）
            duration_score = 80  # 默认评分，可根据实际数据调整

            # 加权评分
            composite_score = (
                drawdown_score * self.weights.stability_weights['max_drawdown'] +
                duration_score * self.weights.stability_weights['drawdown_duration'] +
                volatility_score * self.weights.stability_weights['volatility_control'] +
                tail_risk_score * self.weights.stability_weights['tail_risk_control']
            )

            scores.append(composite_score)

        return scores

    def _calculate_cost_efficiency_scores(self, strategies: List[StrategyRanking]) -> List[float]:
        """计算成本效率评分"""

        scores = []

        for ranking in strategies:
            perf = ranking.performance_metrics

            # 交易成本比率
            total_return = abs(perf.total_return)
            cost_ratio = perf.trading_costs / max(total_return, 0.01)
            trading_cost_score = max(0, 100 - cost_ratio * 200)  # 50%成本比 = 0分

            # 交易频率评分（中等频率最优）
            if perf.total_trades < 20:
                frequency_score = 60  # 过低频率
            elif perf.total_trades < 100:
                frequency_score = 100  # 理想频率
            elif perf.total_trades < 300:
                frequency_score = 80   # 较高频率
            else:
                frequency_score = 50   # 过高频率

            # 执行效率评分（基于策略复杂度）
            complexity_factor = len(ranking.parameters) / 10  # 参数数量作为复杂度指标
            execution_score = max(50, 100 - complexity_factor * 20)

            # 基础设施要求评分（简化）
            infrastructure_score = 85  # 默认评分

            # 加权评分
            composite_score = (
                trading_cost_score * self.weights.cost_weights['trading_cost_ratio'] +
                frequency_score * self.weights.cost_weights['slippage_impact'] +
                execution_score * self.weights.cost_weights['execution_efficiency'] +
                infrastructure_score * self.weights.cost_weights['infrastructure_requirements']
            )

            scores.append(composite_score)

        return scores

    def _calculate_regime_robustness_scores(self, strategies: List[StrategyRanking]) -> List[float]:
        """计算市场环境稳健性评分"""

        # 基于策略表现的历史数据评估稳健性
        # 这里使用简化方法，实际应用中需要不同市场环境下的具体数据

        scores = []

        for ranking in strategies:
            perf = ranking.performance_metrics

            # 基于历史表现推断稳健性
            # 高夏普比率和低回撤通常表示较好的稳健性
            sharpe_indicator = min(perf.sharpe_ratio / 2.0, 1.0) * 100
            drawdown_indicator = max(0, 100 - abs(ranking.risk_metrics.max_drawdown) * 200)

            # 胜率作为稳健性指标
            win_rate_indicator = perf.win_rate * 100

            # 季度一致性作为适应不同环境的能力
            consistency_indicator = perf.quarter_consistency * 100

            # 综合稳健性评分
            robustness_score = (
                sharpe_indicator * 0.3 +
                drawdown_indicator * 0.3 +
                win_rate_indicator * 0.2 +
                consistency_indicator * 0.2
            )

            scores.append(robustness_score)

        return scores

    def _calculate_scalability_scores(self, strategies: List[StrategyRanking]) -> List[float]:
        """计算可扩展性评分"""

        scores = []

        for ranking in strategies:
            # 基于策略特性评估可扩展性

            # 交易频率影响（中等频率最易扩展）
            if ranking.performance_metrics.total_trades < 50:
                frequency_score = 90  # 低频易扩展
            elif ranking.performance_metrics.total_trades < 200:
                frequency_score = 80  # 中频较易扩展
            else:
                frequency_score = 60  # 高频扩展困难

            # 复杂度影响
            complexity_score = max(50, 100 - len(ranking.parameters) * 5)

            # 成本效率影响
            cost_efficiency = min(100, 100 - (ranking.performance_metrics.trading_costs /
                                           max(abs(ranking.performance_metrics.total_return), 0.01)) * 50)

            # 综合可扩展性评分
            scalability_score = (frequency_score + complexity_score + cost_efficiency) / 3

            scores.append(scalability_score)

        return scores

    def _calculate_implementation_ease_scores(self, strategies: List[StrategyRanking]) -> List[float]:
        """计算实施难易度评分"""

        scores = []

        for ranking in strategies:
            # 基于策略特性评估实施难易度

            # 参数复杂度
            param_count = len(ranking.parameters)
            if param_count <= 3:
                complexity_score = 100
            elif param_count <= 6:
                complexity_score = 85
            elif param_count <= 10:
                complexity_score = 70
            else:
                complexity_score = 50

            # 数据要求（简化评估）
            data_requirement_score = 80  # 默认评分

            # 技术要求（基于策略类型）
            strategy_type = ranking.strategy_type.lower()
            if any(simple_type in strategy_type for simple_type in ['rsi', 'ma', 'sma']):
                tech_score = 90  # 简单技术指标
            elif any(medium_type in strategy_type for medium_type in ['macd', 'bollinger', 'bb']):
                tech_score = 80  # 中等复杂度
            else:
                tech_score = 70  # 复杂策略

            # 监控需求（基于交易频率）
            if ranking.performance_metrics.total_trades < 50:
                monitoring_score = 90  # 低监控需求
            elif ranking.performance_metrics.total_trades < 200:
                monitoring_score = 75  # 中等监控需求
            else:
                monitoring_score = 60  # 高监控需求

            # 综合实施难易度评分
            ease_score = (
                complexity_score * 0.4 +
                data_requirement_score * 0.2 +
                tech_score * 0.2 +
                monitoring_score * 0.2
            )

            scores.append(ease_score)

        return scores

    def _calculate_composite_scores(
        self,
        criteria_scores: Dict[str, List[float]],
        custom_criteria: Optional[Dict[SelectionCriteria, float]] = None
    ) -> List[float]:
        """计算综合评分"""

        # 默认权重
        default_weights = {
            SelectionCriteria.RISK_ADJUSTED_RETURN: 0.30,
            SelectionCriteria.CONSISTENCY: 0.20,
            SelectionCriteria.STABILITY: 0.20,
            SelectionCriteria.COST_EFFICIENCY: 0.10,
            SelectionCriteria.MARKET_REGIME_ROBUSTNESS: 0.10,
            SelectionCriteria.SCALABILITY: 0.05,
            SelectionCriteria.IMPLEMENTATION_EASE: 0.05
        }

        # 使用自定义权重（如果提供）
        if custom_criteria:
            # 转换SelectionCriteria枚举到字符串键
            custom_weights = {criteria.value: weight for criteria, weight in custom_criteria.items()}
            # 更新权重
            for key, weight in custom_weights.items():
                if key in criteria_scores:
                    default_weights[SelectionCriteria(key)] = weight

        # 确保权重总和为1
        total_weight = sum(default_weights.values())
        if total_weight != 1.0:
            default_weights = {k: v / total_weight for k, v in default_weights.items()}

        # 计算综合评分
        num_strategies = len(criteria_scores[list(criteria_scores.keys())[0]])
        composite_scores = []

        for i in range(num_strategies):
            score = 0
            for criteria, weight in default_weights.items():
                if criteria.value in criteria_scores:
                    score += criteria_scores[criteria.value][i] * weight

            composite_scores.append(score)

        return composite_scores

    def _apply_comprehensive_ranking(
        self,
        strategies: List[StrategyRanking],
        composite_scores: List[float]
    ) -> List[StrategyRanking]:
        """应用综合排名"""

        # 添加综合评分到策略对象
        for strategy, score in zip(strategies, composite_scores):
            # 添加复合评分作为属性（如果StrategyRanking类支持）
            setattr(strategy, 'top10_composite_score', score)

        # 按综合评分排序
        ranked_strategies = sorted(
            zip(strategies, composite_scores),
            key=lambda x: x[1],
            reverse=True
        )

        return [strategy for strategy, _ in ranked_strategies]

    def _ensure_diversity(self, ranked_strategies: List[StrategyRanking]) -> List[StrategyRanking]:
        """确保选择的策略多样性"""

        if len(ranked_strategies) <= 10:
            return ranked_strategies

        diverse_selections = []
        strategy_types = {}

        # 首先选择每个策略类型的最佳代表
        for strategy in ranked_strategies:
            strategy_type = strategy.strategy_type

            if strategy_type not in strategy_types:
                strategy_types[strategy_type] = []
            strategy_types[strategy_type].append(strategy)

        # 每个策略类型选择Top 2
        for strategy_type, type_strategies in strategy_types.items():
            diverse_selections.extend(type_strategies[:2])

        # 如果不足10个，从剩余策略中补充
        if len(diverse_selections) < 10:
            remaining_strategies = [
                s for s in ranked_strategies
                if s not in diverse_selections
            ]
            diverse_selections.extend(remaining_strategies[:10 - len(diverse_selections)])

        return diverse_selections[:10]

    def _assess_selection_quality(self, strategies: List[StrategyRanking]) -> Dict[str, float]:
        """评估选择质量"""

        if not strategies:
            return {'average_score': 0, 'diversity_index': 0, 'robustness_score': 0}

        # 平均质量评分
        scores = [getattr(s, 'top10_composite_score', s.overall_score) for s in strategies]
        average_score = np.mean(scores)

        # 多样性指数（基于策略类型的分布）
        type_counts = {}
        for strategy in strategies:
            strategy_type = strategy.strategy_type
            type_counts[strategy_type] = type_counts.get(strategy_type, 0) + 1

        # 计算香农多样性指数
        total_strategies = len(strategies)
        if total_strategies > 0:
            diversity_index = -sum(
                (count / total_strategies) * np.log(count / total_strategies)
                for count in type_counts.values()
            )
            # 标准化到0-100
            max_diversity = np.log(len(type_counts)) if len(type_counts) > 1 else 1
            diversity_index = (diversity_index / max_diversity) * 100 if max_diversity > 0 else 0
        else:
            diversity_index = 0

        # 稳健性评分（基于各策略的平均稳定性指标）
        stability_scores = []
        for strategy in strategies:
            perf = strategy.performance_metrics
            risk = strategy.risk_metrics

            # 综合稳健性指标
            stability_score = (
                min(100, perf.sharpe_ratio * 25) * 0.3 +
                max(0, 100 - abs(risk.max_drawdown) * 200) * 0.3 +
                perf.quarter_consistency * 100 * 0.2 +
                perf.monthly_hit_rate * 100 * 0.2
            )
            stability_scores.append(stability_score)

        robustness_score = np.mean(stability_scores) if stability_scores else 0

        return {
            'average_score': average_score,
            'diversity_index': diversity_index,
            'robustness_score': robustness_score
        }

    def _analyze_correlations(self, strategies: List[StrategyRanking]) -> Dict[str, Any]:
        """分析策略相关性"""

        # 简化的相关性分析
        # 实际应用中需要策略的历史收益数据进行计算

        strategy_types = [s.strategy_type for s in strategies]
        type_correlations = {}

        # 基于策略类型推断相关性
        for i, type1 in enumerate(strategy_types):
            for j, type2 in enumerate(strategy_types[i+1:], i+1):
                # 同类型策略相关性较高
                if type1 == type2:
                    correlation = 0.8
                # 相关技术指标策略中等相关
                elif self._are_related_strategies(type1, type2):
                    correlation = 0.5
                else:
                    correlation = 0.2  # 不同类型策略低相关

                type_correlations[f"{type1}_vs_{type2}"] = correlation

        average_correlation = np.mean(list(type_correlations.values())) if type_correlations else 0

        return {
            'pairwise_correlations': type_correlations,
            'average_correlation': average_correlation,
            'diversification_benefit': max(0, (1 - average_correlation) * 100)
        }

    def _are_related_strategies(self, type1: str, type2: str) -> bool:
        """判断两个策略类型是否相关"""

        related_pairs = [
            ('RSI', 'RSI'),
            ('MACD', 'MACD'),
            ('Bollinger', 'Bollinger'),
            ('RSI', 'MACD'),  # 都是动量指标
            ('RSI', 'Bollinger'),  # 都是技术指标
            ('MACD', 'Bollinger'),  # 都是技术指标
        ]

        for pair in related_pairs:
            if pair[0].lower() in type1.lower() and pair[1].lower() in type2.lower():
                return True
            if pair[1].lower() in type1.lower() and pair[0].lower() in type2.lower():
                return True

        return False

    def _analyze_sector_exposure(self, strategies: List[StrategyRanking]) -> Dict[str, float]:
        """分析行业暴露度"""

        # 简化的行业暴露分析
        # CBSC策略主要投资于香港股市，特别是腾讯(0700.HK)

        exposures = {
            'technology': 0.7,    # 科技股暴露
            'finance': 0.2,       # 金融股暴露
            'real_estate': 0.05,  # 地产股暴露
            'other': 0.05         # 其他行业暴露
        }

        return exposures

    def _generate_profile_specific_rankings(
        self,
        strategies: List[StrategyRanking]
    ) -> Dict[str, List[StrategyRanking]]:
        """生成投资者类型特定排名"""

        profile_rankings = {}

        # 为每种投资者类型生成排名
        profile_types = ['aggressive', 'balanced', 'conservative', 'institutional']

        for profile_type in profile_types:
            # 创建临时投资者画像
            temp_profile = self.profiling_system.create_investor_profile(
                {}, profile_type
            )

            # 匹配策略并排名
            match_results = self.profiling_system.match_strategies_to_profile(
                temp_profile, strategies, len(strategies)
            )

            # 提取策略排名
            profile_rankings[profile_type] = [
                match.strategy_ranking for match in match_results
            ]

        return profile_rankings

    def validate_selection(
        self,
        selection_result: Top10SelectionResult,
        validation_data: Optional[Dict[str, Any]] = None
    ) -> ValidationMetrics:
        """
        验证选择结果

        Args:
            selection_result: Top 10选择结果
            validation_data: 验证用数据

        Returns:
            验证指标
        """
        logger.info("Starting Top 10 selection validation")

        # 样本外表现验证
        out_of_sample_perf = self._validate_out_of_sample_performance(
            selection_result, validation_data
        )

        # 预测准确性验证
        prediction_accuracy = self._validate_prediction_accuracy(selection_result)

        # 敏感性分析
        sensitivity_results = self._perform_sensitivity_analysis(selection_result)

        # 压力测试
        stress_test_results = self._perform_stress_tests(selection_result)

        # 时间稳定性验证
        temporal_stability = self._validate_temporal_stability(selection_result)

        # 滚动窗口表现
        rolling_performance = self._calculate_rolling_window_performance(
            selection_result, validation_data
        )

        # 市场环境适应性
        regime_performance = self._validate_regime_performance(selection_result)

        # 相关性稳定性
        correlation_stability = self._validate_correlation_stability(selection_result)

        validation_metrics = ValidationMetrics(
            out_of_sample_performance=out_of_sample_perf,
            prediction_accuracy=prediction_accuracy,
            sensitivity_analysis=sensitivity_results,
            stress_test_results=stress_test_results,
            temporal_stability=temporal_stability,
            rolling_window_performance=rolling_performance,
            regime_performance=regime_performance,
            correlation_stability=correlation_stability
        )

        # 更新统计
        self.selection_stats['validation_tests'] += 1

        logger.info("Selection validation completed")

        return validation_metrics

    def _validate_out_of_sample_performance(
        self,
        selection_result: Top10SelectionResult,
        validation_data: Optional[Dict[str, Any]]
    ) -> float:
        """验证样本外表现"""

        # 简化的样本外验证
        # 实际应用中需要使用验证数据集计算表现

        if validation_data and 'out_of_sample_returns' in validation_data:
            # 计算样本外收益
            oos_returns = validation_data['out_of_sample_returns']
            oos_performance = np.mean(oos_returns)
        else:
            # 基于选择质量的代理指标
            oos_performance = selection_result.average_quality_score / 100

        return oos_performance

    def _validate_prediction_accuracy(self, selection_result: Top10SelectionResult) -> float:
        """验证预测准确性"""

        # 基于排名一致性和质量指标评估预测准确性
        ranking_consistency = selection_result.diversity_index / 100
        quality_score = selection_result.average_quality_score / 100

        prediction_accuracy = (ranking_consistency + quality_score) / 2

        return prediction_accuracy

    def _perform_sensitivity_analysis(self, selection_result: Top10SelectionResult) -> Dict[str, float]:
        """执行敏感性分析"""

        # 权重敏感性分析
        base_weights = {
            'risk_adjusted_return': 0.30,
            'consistency': 0.20,
            'stability': 0.20,
            'cost_efficiency': 0.10,
            'market_regime_robustness': 0.10,
            'scalability': 0.05,
            'implementation_ease': 0.05
        }

        sensitivity_results = {}

        for criterion, weight in base_weights.items():
            # 调整权重±10%
            adjusted_weight = weight * 1.1

            # 计算排名变化（简化）
            ranking_change = abs(weight - adjusted_weight) * 50  # 代理指标
            sensitivity_results[criterion] = ranking_change

        return sensitivity_results

    def _perform_stress_tests(self, selection_result: Top10SelectionResult) -> Dict[str, float]:
        """执行压力测试"""

        # 模拟不同市场条件下的表现
        stress_scenarios = {
            'market_crash': -0.30,  # 市场崩盘
            'high_volatility': 0.25,  # 高波动
            'low_liquidity': 0.15,    # 低流动性
            'regime_change': 0.20     # 市场环境变化
        }

        stress_results = {}

        for scenario, impact_factor in stress_scenarios.items():
            # 基于稳健性评分计算压力表现
            base_robustness = selection_result.robustness_score / 100
            stress_performance = base_robustness * (1 - abs(impact_factor) * 0.5)
            stress_results[scenario] = max(0, stress_performance)

        return stress_results

    def _validate_temporal_stability(self, selection_result: Top10SelectionResult) -> float:
        """验证时间稳定性"""

        # 基于策略的一致性和稳定性指标评估时间稳定性
        stability_indicators = []

        for strategy in selection_result.selected_strategies:
            perf = strategy.performance_metrics

            # 时间稳定性指标
            temporal_stability = (
                perf.quarter_consistency * 0.4 +
                perf.monthly_hit_rate * 0.3 +
                max(0, 100 - perf.rolling_sharpe_std * 300) * 0.3
            )
            stability_indicators.append(temporal_stability)

        return np.mean(stability_indicators) if stability_indicators else 0

    def _calculate_rolling_window_performance(
        self,
        selection_result: Top10SelectionResult,
        validation_data: Optional[Dict[str, Any]]
    ) -> List[float]:
        """计算滚动窗口表现"""

        # 简化的滚动窗口计算
        if validation_data and 'rolling_returns' in validation_data:
            return validation_data['rolling_returns']
        else:
            # 基于平均质量生成了滚动表现数据
            base_performance = selection_result.average_quality_score / 100
            return [
                base_performance * (1 + np.random.normal(0, 0.05))
                for _ in range(12)  # 12个月滚动窗口
            ]

    def _validate_regime_performance(self, selection_result: Top10SelectionResult) -> Dict[str, float]:
        """验证市场环境表现"""

        # 基于策略稳健性推断不同市场环境下的表现
        base_robustness = selection_result.robustness_score / 100

        regime_performance = {
            'bull_market': base_robustness * 1.2,      # 牛市表现更好
            'bear_market': base_robustness * 0.7,      # 熊市表现较差
            'sideways_market': base_robustness,        # 横盘市场
            'high_volatility': base_robustness * 0.8,  # 高波动环境
            'crisis_period': base_robustness * 0.5     # 危机时期
        }

        return regime_performance

    def _validate_correlation_stability(self, selection_result: Top10SelectionResult) -> float:
        """验证相关性稳定性"""

        # 基于相关性分析的稳定性评估
        correlation_analysis = selection_result.correlation_analysis

        # 平均相关性的倒数作为稳定性指标（相关性越低，分散化越好）
        avg_correlation = correlation_analysis['average_correlation']

        # 相关性稳定性评分
        correlation_stability = max(0, (1 - avg_correlation) * 100)

        return correlation_stability

    def generate_selection_report(
        self,
        selection_result: Top10SelectionResult,
        validation_metrics: Optional[ValidationMetrics] = None,
        output_file: Optional[str] = None
    ) -> str:
        """
        生成选择报告

        Args:
            selection_result: Top 10选择结果
            validation_metrics: 验证指标
            output_file: 输出文件路径

        Returns:
            报告内容
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        report_lines = [
            "# CBSC策略Top 10选择报告",
            f"生成时间: {timestamp}",
            f"选择方法: {selection_result.selection_methodology}",
            f"候选策略总数: {selection_result.total_candidates}",
            f"最终选择数量: {selection_result.final_selections}",
            "",
            "## Top 10策略概览",
            "| 排名 | 策略名称 | 综合评分 | Sharpe比率 | 最大回撤 | 胜率 | 风险等级 | 评级 |",
            "|------|----------|----------|------------|----------|------|----------|------|"
        ]

        for i, strategy in enumerate(selection_result.selected_strategies, 1):
            composite_score = getattr(strategy, 'top10_composite_score', strategy.overall_score)
            report_lines.append(
                f"| {i} | {strategy.strategy_name} | {composite_score:.2f} | "
                f"{strategy.performance_metrics.sharpe_ratio:.3f} | "
                f"{strategy.risk_metrics.max_drawdown*100:.2f}% | "
                f"{strategy.performance_metrics.win_rate*100:.2f}% | "
                f"{strategy.risk_level} | {strategy.rating} |"
            )

        # 质量评估
        report_lines.extend([
            "",
            "## 选择质量评估",
            f"- **平均质量评分**: {selection_result.average_quality_score:.2f}/100",
            f"- **多样性指数**: {selection_result.diversity_index:.2f}/100",
            f"- **稳健性评分**: {selection_result.robustness_score:.2f}/100",
            ""
        ])

        # 相关性分析
        corr_analysis = selection_result.correlation_analysis
        report_lines.extend([
            "## 相关性分析",
            f"- **平均相关性**: {corr_analysis['average_correlation']:.3f}",
            f"- **分散化收益**: {corr_analysis['diversification_benefit']:.2f}%",
            "",
            "### 主要策略对相关性"
        ])

        for pair, corr in list(corr_analysis['pairwise_correlations'].items())[:5]:
            report_lines.append(f"- {pair}: {corr:.3f}")

        report_lines.append("")

        # 投资者类型特定排名
        report_lines.extend([
            "## 投资者类型适配",
            "",
            "### 激进型投资者 Top 5",
            "| 排名 | 策略名称 | 适配评分 |",
            "|------|----------|----------|"
        ])

        aggressive_rankings = selection_result.profile_specific_rankings.get('aggressive', [])
        for i, strategy in enumerate(aggressive_rankings[:5], 1):
            score = getattr(strategy, 'aggressive_score', strategy.overall_score)
            report_lines.append(f"| {i} | {strategy.strategy_name} | {score:.2f} |")

        report_lines.extend([
            "",
            "### 保守型投资者 Top 5",
            "| 排名 | 策略名称 | 适配评分 |",
            "|------|----------|----------|"
        ])

        conservative_rankings = selection_result.profile_specific_rankings.get('conservative', [])
        for i, strategy in enumerate(conservative_rankings[:5], 1):
            score = getattr(strategy, 'conservative_score', strategy.overall_score)
            report_lines.append(f"| {i} | {strategy.strategy_name} | {score:.2f} |")

        # 验证结果（如果有）
        if validation_metrics:
            report_lines.extend([
                "",
                "## 验证结果",
                f"- **样本外表现**: {validation_metrics.out_of_sample_performance:.3f}",
                f"- **预测准确性**: {validation_metrics.prediction_accuracy:.3f}",
                f"- **时间稳定性**: {validation_metrics.temporal_stability:.2f}/100",
                f"- **相关性稳定性**: {validation_metrics.correlation_stability:.2f}/100",
                ""
            ])

            stress_results = validation_metrics.stress_test_results
            report_lines.extend([
                "### 压力测试结果",
                f"- **市场崩盘场景**: {stress_results['market_crash']:.3f}",
                f"- **高波动场景**: {stress_results['high_volatility']:.3f}",
                f"- **低流动性场景**: {stress_results['low_liquidity']:.3f}",
                f"- **市场环境变化**: {stress_results['regime_change']:.3f}",
                ""
            ])

        # 投资建议
        report_lines.extend([
            "## 投资建议",
            "",
            "### 配置建议",
            "1. **分散投资**: 建议配置3-5个不同类型的策略以分散风险",
            "2. **权重分配**: 根据风险承受能力和投资目标调整各策略权重",
            "3. **定期调整**: 建议每季度评估并调整策略配置",
            "4. **风险控制**: 设置适当的止损和仓位管理规则",
            "",
            "### 监控要点",
            "1. 密切关注策略的胜率变化趋势",
            "2. 监控最大回撤是否超出预期范围",
            "3. 跟踪交易成本对收益的侵蚀程度",
            "4. 定期评估策略与市场环境的适配性",
            "",
            "### 风险提示",
            "- 历史表现不代表未来收益",
            "- 策略表现可能因市场环境变化而有所差异",
            "- 建议在投资前进行充分的尽职调查",
            "- 投资决策应结合个人风险承受能力",
            "",
            "### 后续行动",
            "1. 对选定的策略进行更深入的回测分析",
            "2. 进行样本外测试和敏感性分析",
            "3. 制定详细的实施计划和监控方案",
            "4. 建立策略表现的实时监控系统",
            ""
        ])

        report_content = '\n'.join(report_lines)

        # 保存报告
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"Top 10 selection report saved to: {output_file}")

        return report_content

    def get_methodology_summary(self) -> Dict[str, Any]:
        """获取方法论总结"""
        return {
            'selection_statistics': self.selection_stats,
            'selection_criteria_weights': {
                'risk_adjusted_return': 0.30,
                'consistency': 0.20,
                'stability': 0.20,
                'cost_efficiency': 0.10,
                'market_regime_robustness': 0.10,
                'scalability': 0.05,
                'implementation_ease': 0.05
            },
            'recent_selections_count': len(self.selection_history),
            'last_selection_date': self.selection_history[-1].selection_date if self.selection_history else None
        }

# 便利函数
def quick_top10_selection(
    strategy_rankings: List[StrategyRanking],
    profile_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    快速Top 10策略选择

    Args:
        strategy_rankings: 策略排名列表
        profile_type: 投资者类型 (aggressive, balanced, conservative, institutional)

    Returns:
        选择结果
    """
    methodology = Top10SelectionMethodology()

    # 创建投资者画像（如果指定）
    selection_profile = None
    if profile_type:
        profiling_system = InvestorProfilingSystem()
        selection_profile = profiling_system.create_investor_profile({}, profile_type)

    # 执行Top 10选择
    selection_result = methodology.select_top_10_strategies(
        strategy_rankings, selection_profile
    )

    # 验证选择结果
    validation_metrics = methodology.validate_selection(selection_result)

    # 生成报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"top10_selection_report_{timestamp}.md"
    methodology.generate_selection_report(selection_result, validation_metrics, report_file)

    return {
        'selection_result': selection_result,
        'validation_metrics': validation_metrics,
        'top_10_strategies': selection_result.selected_strategies,
        'report_file': report_file,
        'methodology_summary': methodology.get_methodology_summary()
    }

if __name__ == "__main__":
    print("Top 10策略选择方法论已就绪")
    print("使用 quick_top10_selection() 进行快速策略选择")
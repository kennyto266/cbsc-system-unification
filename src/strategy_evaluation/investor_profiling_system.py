#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资者画像匹配系统
Investor Profiling and Matching System

为CBSC策略提供专业的投资者画像分析、风险承受能力评估和策略匹配推荐
Professional investor profiling, risk assessment, and strategy matching system for CBSC strategies
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
import warnings
warnings.filterwarnings('ignore')

from .comprehensive_ranking_framework import InvestorProfile, StrategyRanking, PerformanceMetrics, RiskMetrics

logger = logging.getLogger(__name__)

class RiskTolerance(Enum):
    """风险承受能力枚举"""
    VERY_LOW = "very_low"       # 极低风险承受能力
    LOW = "low"                 # 低风险承受能力
    MODERATE = "moderate"       # 中等风险承受能力
    HIGH = "high"               # 高风险承受能力
    VERY_HIGH = "very_high"     # 极高风险承受能力

class InvestmentGoal(Enum):
    """投资目标枚举"""
    CAPITAL_PRESERVATION = "capital_preservation"  # 资本保值
    STEADY_GROWTH = "steady_growth"                # 稳健增长
    BALANCED_RETURN = "balanced_return"            # 平衡收益
    AGGRESSIVE_GROWTH = "aggressive_growth"        # 激进增长
    SPECULATIVE = "speculative"                    # 投机交易

class TimeHorizon(Enum):
    """投资期限枚举"""
    SHORT_TERM = "short_term"        # 短期（<1年）
    MEDIUM_TERM = "medium_term"      # 中期（1-3年）
    LONG_TERM = "long_term"          # 长期（3-5年）
    VERY_LONG_TERM = "very_long_term"  # 超长期（>5年）

@dataclass
class InvestorCharacteristics:
    """投资者特征数据类"""
    # 基本信息
    age: int
    income_level: str  # low, medium, high, very_high
    net_worth: str    # low, medium, high, very_high
    investment_experience: str  # beginner, intermediate, advanced, expert

    # 风险特征
    risk_tolerance: RiskTolerance
    loss_aversion: float  # 0-1，损失厌恶程度
    volatility_sensitivity: float  # 0-1，波动性敏感度

    # 投资特征
    investment_goal: InvestmentGoal
    time_horizon: TimeHorizon
    liquidity_needs: float  # 0-1，流动性需求程度
    portfolio_size: float  # 投资组合规模（万元）

    # 行为特征
    emotional_stability: float  # 0-1，情绪稳定性
    decision_confidence: float  # 0-1，决策自信度
    market_knowledge: float  # 0-1，市场知识水平

    # 偏好设置
    max_acceptable_loss: float  # 最大可接受损失（百分比）
    expected_return: float     # 期望收益（年化百分比）
    diversification_preference: float  # 0-1，分散化偏好

@dataclass
class InvestorProfile:
    """投资者画像数据类"""
    profile_id: str
    profile_name: str
    characteristics: InvestorCharacteristics

    # 风险画像
    risk_profile: str  # conservative, moderate, aggressive
    risk_capacity: float  # 风险承担能力评分

    # 策略偏好
    preferred_strategy_types: List[str]
    avoidance_factors: List[str]

    # 投资约束
    max_portfolio_allocation: float  # 单策略最大配置比例
    rebalancing_frequency: str  # daily, weekly, monthly, quarterly
    performance_review_period: str  # monthly, quarterly, semi_annually

    # 适合的策略特征
    suitable_metrics: Dict[str, Tuple[float, float]]  # 指标名称: (最小值, 最大值)

    # 画像标签
    tags: List[str]
    description: str

@dataclass
class StrategyMatchResult:
    """策略匹配结果"""
    strategy_ranking: StrategyRanking
    match_score: float  # 匹配度评分 0-100
    match_reasons: List[str]  # 匹配原因
    risk_warnings: List[str]  # 风险提示
    allocation_suggestion: float  # 建议配置比例
    monitoring_points: List[str]  # 监控要点

class InvestorProfilingSystem:
    """
    投资者画像匹配系统

    提供专业的投资者画像分析功能：
    - 多维度投资者特征分析
    - 风险承受能力评估
    - 个性化策略匹配
    - 动态画像更新
    - 投资建议生成
    """

    def __init__(self):
        """初始化投资者画像系统"""

        # 画像模板
        self.profile_templates = self._initialize_profile_templates()

        # 匹配算法权重
        self.matching_weights = {
            'risk_alignment': 0.30,      # 风险对齐度
            'return_expectation': 0.20,  # 收益期望匹配度
            'time_horizon': 0.15,        # 投资期限匹配度
            'complexity_fit': 0.10,      # 复杂度适配度
            'cost_sensitivity': 0.10,    # 成本敏感度
            'liquidity_match': 0.10,     # 流动性匹配度
            'behavioral_fit': 0.05       # 行为匹配度
        }

        # 统计数据
        self.profiling_stats = {
            'profiles_created': 0,
            'matches_performed': 0,
            'recommendations_generated': 0
        }

        logger.info("Investor Profiling System initialized")

    def _initialize_profile_templates(self) -> Dict[str, InvestorProfile]:
        """初始化投资者画像模板"""

        templates = {}

        # 激进型投资者模板
        templates['aggressive'] = InvestorProfile(
            profile_id='template_aggressive',
            profile_name='激进型投资者',
            characteristics=InvestorCharacteristics(
                age=35,
                income_level='high',
                net_worth='medium',
                investment_experience='advanced',
                risk_tolerance=RiskTolerance.VERY_HIGH,
                loss_aversion=0.3,
                volatility_sensitivity=0.2,
                investment_goal=InvestmentGoal.AGGRESSIVE_GROWTH,
                time_horizon=TimeHorizon.MEDIUM_TERM,
                liquidity_needs=0.2,
                portfolio_size=50.0,
                emotional_stability=0.7,
                decision_confidence=0.8,
                market_knowledge=0.8,
                max_acceptable_loss=0.30,
                expected_return=0.25,
                diversification_preference=0.4
            ),
            risk_profile='aggressive',
            risk_capacity=0.85,
            preferred_strategy_types=['RSI Aggressive', 'MACD Sensitive', 'High Frequency'],
            avoidance_factors=['Low Return', 'High Stability'],
            max_portfolio_allocation=0.40,
            rebalancing_frequency='weekly',
            performance_review_period='monthly',
            suitable_metrics={
                'max_drawdown': (-0.50, -0.10),
                'sharpe_ratio': (0.8, 3.0),
                'annual_return': (0.15, 0.50),
                'win_rate': (0.45, 0.70)
            },
            tags=['高收益', '高风险', '积极', '经验丰富'],
            description='追求高收益，能承受较大回撤，适合激进策略'
        )

        # 平衡型投资者模板
        templates['balanced'] = InvestorProfile(
            profile_id='template_balanced',
            profile_name='平衡型投资者',
            characteristics=InvestorCharacteristics(
                age=40,
                income_level='medium',
                net_worth='medium',
                investment_experience='intermediate',
                risk_tolerance=RiskTolerance.MODERATE,
                loss_aversion=0.5,
                volatility_sensitivity=0.5,
                investment_goal=InvestmentGoal.BALANCED_RETURN,
                time_horizon=TimeHorizon.LONG_TERM,
                liquidity_needs=0.4,
                portfolio_size=30.0,
                emotional_stability=0.6,
                decision_confidence=0.6,
                market_knowledge=0.6,
                max_acceptable_loss=0.20,
                expected_return=0.15,
                diversification_preference=0.7
            ),
            risk_profile='moderate',
            risk_capacity=0.60,
            preferred_strategy_types=['RSI Conservative', 'Bollinger Standard', 'Sentiment Momentum'],
            avoidance_factors=['Extreme Volatility', 'Speculative Trading'],
            max_portfolio_allocation=0.30,
            rebalancing_frequency='monthly',
            performance_review_period='quarterly',
            suitable_metrics={
                'max_drawdown': (-0.30, -0.05),
                'sharpe_ratio': (1.0, 2.5),
                'annual_return': (0.08, 0.20),
                'win_rate': (0.50, 0.65)
            },
            tags=['平衡', '稳健', '理性', '中等经验'],
            description='追求风险与收益的平衡，适合多样化策略组合'
        )

        # 保守型投资者模板
        templates['conservative'] = InvestorProfile(
            profile_id='template_conservative',
            profile_name='保守型投资者',
            characteristics=InvestorCharacteristics(
                age=50,
                income_level='medium',
                net_worth='high',
                investment_experience='beginner',
                risk_tolerance=RiskTolerance.LOW,
                loss_aversion=0.8,
                volatility_sensitivity=0.8,
                investment_goal=InvestmentGoal.CAPITAL_PRESERVATION,
                time_horizon=TimeHorizon.VERY_LONG_TERM,
                liquidity_needs=0.3,
                portfolio_size=100.0,
                emotional_stability=0.5,
                decision_confidence=0.4,
                market_knowledge=0.4,
                max_acceptable_loss=0.10,
                expected_return=0.08,
                diversification_preference=0.9
            ),
            risk_profile='conservative',
            risk_capacity=0.30,
            preferred_strategy_types=['RSI Conservative', 'Bollinger Wide', 'Low Frequency'],
            avoidance_factors=['High Volatility', 'Complex Strategies', 'High Trading Costs'],
            max_portfolio_allocation=0.20,
            rebalancing_frequency='quarterly',
            performance_review_period='semi_annually',
            suitable_metrics={
                'max_drawdown': (-0.15, 0.0),
                'sharpe_ratio': (1.2, 2.0),
                'annual_return': (0.05, 0.12),
                'win_rate': (0.55, 0.70)
            },
            tags=['保守', '稳健', '资本保护', '经验较少'],
            description='优先保护本金，适合低风险、稳定收益策略'
        )

        # 机构型投资者模板
        templates['institutional'] = InvestorProfile(
            profile_id='template_institutional',
            profile_name='机构型投资者',
            characteristics=InvestorCharacteristics(
                age=999,  # 机构不适用年龄
                income_level='very_high',
                net_worth='very_high',
                investment_experience='expert',
                risk_tolerance=RiskTolerance.MODERATE,
                loss_aversion=0.4,
                volatility_sensitivity=0.3,
                investment_goal=InvestmentGoal.STEADY_GROWTH,
                time_horizon=TimeHorizon.VERY_LONG_TERM,
                liquidity_needs=0.2,
                portfolio_size=1000.0,
                emotional_stability=0.9,
                decision_confidence=0.9,
                market_knowledge=0.9,
                max_acceptable_loss=0.15,
                expected_return=0.12,
                diversification_preference=0.8
            ),
            risk_profile='institutional',
            risk_capacity=0.70,
            preferred_strategy_types=['Multi-Factor', 'Statistical Arbitrage', 'Market Neutral'],
            avoidance_factors=['High Drawdown', 'Low Liquidity', 'Opaque Strategies'],
            max_portfolio_allocation=0.25,
            rebalancing_frequency='monthly',
            performance_review_period='monthly',
            suitable_metrics={
                'max_drawdown': (-0.20, -0.05),
                'sharpe_ratio': (1.5, 3.0),
                'annual_return': (0.08, 0.18),
                'win_rate': (0.52, 0.68)
            },
            tags=['机构', '专业', '风控严格', '长期价值'],
            description='注重风险控制和长期稳定收益，适合专业级策略'
        )

        return templates

    def create_investor_profile(
        self,
        profile_data: Dict[str, Any],
        template_name: Optional[str] = None
    ) -> InvestorProfile:
        """
        创建投资者画像

        Args:
            profile_data: 投资者特征数据
            template_name: 使用的模板名称

        Returns:
            投资者画像
        """
        logger.info(f"Creating investor profile using template: {template_name}")

        # 使用模板或创建新画像
        if template_name and template_name in self.profile_templates:
            template = self.profile_templates[template_name]
            # 基于模板创建，但允许覆盖特定特征
            characteristics = self._update_characteristics_from_data(
                template.characteristics, profile_data
            )

            profile = InvestorProfile(
                profile_id=f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                profile_name=profile_data.get('profile_name', f"Custom {template_name.title()}"),
                characteristics=characteristics,
                risk_profile=self._calculate_risk_profile(characteristics),
                risk_capacity=self._calculate_risk_capacity(characteristics),
                preferred_strategy_types=profile_data.get('preferred_strategy_types', template.preferred_strategy_types),
                avoidance_factors=profile_data.get('avoidance_factors', template.avoidance_factors),
                max_portfolio_allocation=profile_data.get('max_portfolio_allocation', template.max_portfolio_allocation),
                rebalancing_frequency=profile_data.get('rebalancing_frequency', template.rebalancing_frequency),
                performance_review_period=profile_data.get('performance_review_period', template.performance_review_period),
                suitable_metrics=self._calculate_suitable_metrics(characteristics),
                tags=profile_data.get('tags', template.tags),
                description=profile_data.get('description', template.description)
            )
        else:
            # 从零创建画像
            characteristics = self._create_characteristics_from_data(profile_data)

            profile = InvestorProfile(
                profile_id=f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                profile_name=profile_data.get('profile_name', 'Custom Profile'),
                characteristics=characteristics,
                risk_profile=self._calculate_risk_profile(characteristics),
                risk_capacity=self._calculate_risk_capacity(characteristics),
                preferred_strategy_types=profile_data.get('preferred_strategy_types', []),
                avoidance_factors=profile_data.get('avoidance_factors', []),
                max_portfolio_allocation=profile_data.get('max_portfolio_allocation', 0.30),
                rebalancing_frequency=profile_data.get('rebalancing_frequency', 'monthly'),
                performance_review_period=profile_data.get('performance_review_period', 'quarterly'),
                suitable_metrics=self._calculate_suitable_metrics(characteristics),
                tags=profile_data.get('tags', []),
                description=profile_data.get('description', 'Custom investor profile')
            )

        # 更新统计
        self.profiling_stats['profiles_created'] += 1

        return profile

    def _update_characteristics_from_data(
        self,
        base_characteristics: InvestorCharacteristics,
        profile_data: Dict[str, Any]
    ) -> InvestorCharacteristics:
        """基于数据更新特征"""

        # 创建新特征对象，允许覆盖特定字段
        return InvestorCharacteristics(
            age=profile_data.get('age', base_characteristics.age),
            income_level=profile_data.get('income_level', base_characteristics.income_level),
            net_worth=profile_data.get('net_worth', base_characteristics.net_worth),
            investment_experience=profile_data.get('investment_experience', base_characteristics.investment_experience),
            risk_tolerance=RiskTolerance(profile_data.get('risk_tolerance', base_characteristics.risk_tolerance.value)),
            loss_aversion=profile_data.get('loss_aversion', base_characteristics.loss_aversion),
            volatility_sensitivity=profile_data.get('volatility_sensitivity', base_characteristics.volatility_sensitivity),
            investment_goal=InvestmentGoal(profile_data.get('investment_goal', base_characteristics.investment_goal.value)),
            time_horizon=TimeHorizon(profile_data.get('time_horizon', base_characteristics.time_horizon.value)),
            liquidity_needs=profile_data.get('liquidity_needs', base_characteristics.liquidity_needs),
            portfolio_size=profile_data.get('portfolio_size', base_characteristics.portfolio_size),
            emotional_stability=profile_data.get('emotional_stability', base_characteristics.emotional_stability),
            decision_confidence=profile_data.get('decision_confidence', base_characteristics.decision_confidence),
            market_knowledge=profile_data.get('market_knowledge', base_characteristics.market_knowledge),
            max_acceptable_loss=profile_data.get('max_acceptable_loss', base_characteristics.max_acceptable_loss),
            expected_return=profile_data.get('expected_return', base_characteristics.expected_return),
            diversification_preference=profile_data.get('diversification_preference', base_characteristics.diversification_preference)
        )

    def _create_characteristics_from_data(self, profile_data: Dict[str, Any]) -> InvestorCharacteristics:
        """从数据创建特征"""

        return InvestorCharacteristics(
            age=profile_data.get('age', 40),
            income_level=profile_data.get('income_level', 'medium'),
            net_worth=profile_data.get('net_worth', 'medium'),
            investment_experience=profile_data.get('investment_experience', 'intermediate'),
            risk_tolerance=RiskTolerance(profile_data.get('risk_tolerance', 'moderate')),
            loss_aversion=profile_data.get('loss_aversion', 0.5),
            volatility_sensitivity=profile_data.get('volatility_sensitivity', 0.5),
            investment_goal=InvestmentGoal(profile_data.get('investment_goal', 'balanced_return')),
            time_horizon=TimeHorizon(profile_data.get('time_horizon', 'long_term')),
            liquidity_needs=profile_data.get('liquidity_needs', 0.5),
            portfolio_size=profile_data.get('portfolio_size', 50.0),
            emotional_stability=profile_data.get('emotional_stability', 0.6),
            decision_confidence=profile_data.get('decision_confidence', 0.6),
            market_knowledge=profile_data.get('market_knowledge', 0.6),
            max_acceptable_loss=profile_data.get('max_acceptable_loss', 0.20),
            expected_return=profile_data.get('expected_return', 0.15),
            diversification_preference=profile_data.get('diversification_preference', 0.7)
        )

    def _calculate_risk_profile(self, characteristics: InvestorCharacteristics) -> str:
        """计算风险画像"""

        risk_score = 0

        # 风险承受能力评分
        risk_tolerance_scores = {
            RiskTolerance.VERY_LOW: 1,
            RiskTolerance.LOW: 2,
            RiskTolerance.MODERATE: 3,
            RiskTolerance.HIGH: 4,
            RiskTolerance.VERY_HIGH: 5
        }
        risk_score += risk_tolerance_scores[characteristics.risk_tolerance] * 0.3

        # 损失厌恶程度评分（负向）
        risk_score += (1 - characteristics.loss_aversion) * 0.2

        # 波动性敏感度评分（负向）
        risk_score += (1 - characteristics.volatility_sensitivity) * 0.2

        # 投资经验评分
        experience_scores = {
            'beginner': 1,
            'intermediate': 2,
            'advanced': 3,
            'expert': 4
        }
        risk_score += experience_scores[characteristics.investment_experience] * 0.15

        # 情绪稳定性评分
        risk_score += characteristics.emotional_stability * 0.15

        # 确定风险画像
        if risk_score >= 4.0:
            return 'aggressive'
        elif risk_score >= 3.0:
            return 'moderate'
        else:
            return 'conservative'

    def _calculate_risk_capacity(self, characteristics: InvestorCharacteristics) -> float:
        """计算风险承担能力"""

        capacity_score = 0

        # 净值评分
        net_worth_scores = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'very_high': 4
        }
        capacity_score += net_worth_scores[characteristics.net_worth] * 0.25

        # 收入评分
        income_scores = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'very_high': 4
        }
        capacity_score += income_scores[characteristics.income_level] * 0.2

        # 投资组合规模评分
        if characteristics.portfolio_size >= 100:
            portfolio_score = 4
        elif characteristics.portfolio_size >= 50:
            portfolio_score = 3
        elif characteristics.portfolio_size >= 20:
            portfolio_score = 2
        else:
            portfolio_score = 1
        capacity_score += portfolio_score * 0.25

        # 投资期限评分
        horizon_scores = {
            TimeHorizon.SHORT_TERM: 1,
            TimeHorizon.MEDIUM_TERM: 2,
            TimeHorizon.LONG_TERM: 3,
            TimeHorizon.VERY_LONG_TERM: 4
        }
        capacity_score += horizon_scores[characteristics.time_horizon] * 0.2

        # 流动性需求评分（负向）
        capacity_score += (1 - characteristics.liquidity_needs) * 0.1

        return capacity_score / 4.0  # 标准化到0-1

    def _calculate_suitable_metrics(self, characteristics: InvestorCharacteristics) -> Dict[str, Tuple[float, float]]:
        """计算适合的策略指标范围"""

        risk_profile = self._calculate_risk_profile(characteristics)
        risk_capacity = self._calculate_risk_capacity(characteristics)

        if risk_profile == 'aggressive':
            return {
                'max_drawdown': (-0.60, -0.10),
                'sharpe_ratio': (0.5, 3.5),
                'annual_return': (0.15, 0.60),
                'win_rate': (0.40, 0.75),
                'calmar_ratio': (0.3, 3.0),
                'max_volatility': (0.15, 0.50)
            }
        elif risk_profile == 'moderate':
            return {
                'max_drawdown': (-0.35, -0.05),
                'sharpe_ratio': (0.8, 2.5),
                'annual_return': (0.08, 0.25),
                'win_rate': (0.48, 0.68),
                'calmar_ratio': (0.4, 2.0),
                'max_volatility': (0.10, 0.30)
            }
        else:  # conservative
            return {
                'max_drawdown': (-0.20, 0.0),
                'sharpe_ratio': (1.0, 2.0),
                'annual_return': (0.05, 0.15),
                'win_rate': (0.52, 0.72),
                'calmar_ratio': (0.5, 1.5),
                'max_volatility': (0.08, 0.20)
            }

    def match_strategies_to_profile(
        self,
        investor_profile: InvestorProfile,
        strategy_rankings: List[StrategyRanking],
        top_n: int = 10
    ) -> List[StrategyMatchResult]:
        """
        将策略匹配到投资者画像

        Args:
            investor_profile: 投资者画像
            strategy_rankings: 策略排名列表
            top_n: 返回前N个匹配结果

        Returns:
            策略匹配结果列表
        """
        logger.info(f"Matching strategies to investor profile: {investor_profile.profile_name}")

        match_results = []

        for strategy_ranking in strategy_rankings:
            # 计算匹配度评分
            match_score, match_details = self._calculate_match_score(
                investor_profile, strategy_ranking
            )

            # 生成匹配结果
            match_result = StrategyMatchResult(
                strategy_ranking=strategy_ranking,
                match_score=match_score,
                match_reasons=match_details['reasons'],
                risk_warnings=match_details['warnings'],
                allocation_suggestion=self._calculate_allocation_suggestion(
                    match_score, investor_profile, strategy_ranking
                ),
                monitoring_points=match_details['monitoring_points']
            )

            match_results.append(match_result)

        # 按匹配度排序
        match_results.sort(key=lambda x: x.match_score, reverse=True)

        # 更新统计
        self.profiling_stats['matches_performed'] += 1

        return match_results[:top_n]

    def _calculate_match_score(
        self,
        investor_profile: InvestorProfile,
        strategy_ranking: StrategyRanking
    ) -> Tuple[float, Dict[str, Any]]:
        """计算匹配度评分"""

        scores = {}
        reasons = []
        warnings = []
        monitoring_points = []

        performance = strategy_ranking.performance_metrics
        risk = strategy_ranking.risk_metrics

        # 1. 风险对齐度 (30%)
        risk_alignment_score = self._calculate_risk_alignment(
            investor_profile, strategy_ranking
        )
        scores['risk_alignment'] = risk_alignment_score
        if risk_alignment_score > 80:
            reasons.append("风险承受能力匹配度高")
        elif risk_alignment_score < 40:
            warnings.append("风险承受能力不匹配")

        # 2. 收益期望匹配度 (20%)
        return_score = self._calculate_return_alignment(
            investor_profile, performance
        )
        scores['return_expectation'] = return_score
        if return_score > 80:
            reasons.append("收益期望符合预期")
        elif return_score < 40:
            warnings.append("收益期望可能不达标")

        # 3. 投资期限匹配度 (15%)
        time_horizon_score = self._calculate_time_horizon_alignment(
            investor_profile, performance
        )
        scores['time_horizon'] = time_horizon_score
        if time_horizon_score > 70:
            reasons.append("投资期限适配良好")
        elif time_horizon_score < 40:
            warnings.append("投资期限可能不匹配")

        # 4. 复杂度适配度 (10%)
        complexity_score = self._calculate_complexity_alignment(
            investor_profile, strategy_ranking
        )
        scores['complexity_fit'] = complexity_score

        # 5. 成本敏感度 (10%)
        cost_score = self._calculate_cost_alignment(
            investor_profile, performance
        )
        scores['cost_sensitivity'] = cost_score
        if cost_score < 50:
            warnings.append("交易成本较高")
            monitoring_points.append("密切监控交易成本")

        # 6. 流动性匹配度 (10%)
        liquidity_score = self._calculate_liquidity_alignment(
            investor_profile, strategy_ranking
        )
        scores['liquidity_match'] = liquidity_score

        # 7. 行为匹配度 (5%)
        behavioral_score = self._calculate_behavioral_alignment(
            investor_profile, strategy_ranking
        )
        scores['behavioral_fit'] = behavioral_score

        # 计算加权总分
        total_score = sum(
            scores[key] * weight
            for key, weight in self.matching_weights.items()
        )

        # 添加监控要点
        if risk.max_drawdown < -0.20:
            monitoring_points.append("密切关注回撤控制")
        if performance.sharpe_ratio < 1.0:
            monitoring_points.append("监控风险调整收益")
        if performance.win_rate < 0.45:
            monitoring_points.append("关注胜率变化趋势")

        match_details = {
            'reasons': reasons,
            'warnings': warnings,
            'monitoring_points': monitoring_points,
            'detailed_scores': scores
        }

        return total_score, match_details

    def _calculate_risk_alignment(
        self,
        investor_profile: InvestorProfile,
        strategy_ranking: StrategyRanking
    ) -> float:
        """计算风险对齐度"""

        suitable_metrics = investor_profile.suitable_metrics

        # 检查各项指标是否在适合范围内
        scores = []

        # 最大回撤
        if 'max_drawdown' in suitable_metrics:
            min_dd, max_dd = suitable_metrics['max_drawdown']
            actual_dd = strategy_ranking.risk_metrics.max_drawdown
            if min_dd <= actual_dd <= max_dd:
                scores.append(100)
            elif actual_dd < min_dd:
                # 回撤小于最小值，表现优于预期
                scores.append(90)
            else:
                # 回撤超过最大容忍值
                penalty = (actual_dd - max_dd) / abs(max_dd) * 100
                scores.append(max(0, 50 - penalty))

        # 夏普比率
        if 'sharpe_ratio' in suitable_metrics:
            min_sr, max_sr = suitable_metrics['sharpe_ratio']
            actual_sr = strategy_ranking.performance_metrics.sharpe_ratio
            if min_sr <= actual_sr <= max_sr:
                scores.append(100)
            elif actual_sr > max_sr:
                scores.append(95)  # 优于预期
            else:
                scores.append((actual_sr / min_sr) * 80)

        # 年化收益
        if 'annual_return' in suitable_metrics:
            min_ret, max_ret = suitable_metrics['annual_return']
            actual_ret = strategy_ranking.performance_metrics.annual_return
            if min_ret <= actual_ret <= max_ret:
                scores.append(100)
            elif actual_ret > max_ret:
                scores.append(95)  # 优于预期
            else:
                scores.append((actual_ret / min_ret) * 70)

        # 胜率
        if 'win_rate' in suitable_metrics:
            min_wr, max_wr = suitable_metrics['win_rate']
            actual_wr = strategy_ranking.performance_metrics.win_rate
            if min_wr <= actual_wr <= max_wr:
                scores.append(100)
            elif actual_wr > max_wr:
                scores.append(95)
            else:
                scores.append((actual_wr / min_wr) * 80)

        return np.mean(scores) if scores else 50

    def _calculate_return_alignment(
        self,
        investor_profile: InvestorProfile,
        performance: PerformanceMetrics
    ) -> float:
        """计算收益期望匹配度"""

        expected_return = investor_profile.characteristics.expected_return
        actual_return = performance.annual_return

        if actual_return >= expected_return:
            return min(100, 50 + (actual_return - expected_return) * 200)
        else:
            gap = expected_return - actual_return
            return max(0, 50 - gap * 300)

    def _calculate_time_horizon_alignment(
        self,
        investor_profile: InvestorProfile,
        performance: PerformanceMetrics
    ) -> float:
        """计算投资期限匹配度"""

        # 基于策略的稳定性和持续性评分
        stability_score = performance.quarter_consistency * 100
        persistence_score = performance.performance_persistence * 100

        # 根据投资期限调整权重
        time_horizon = investor_profile.characteristics.time_horizon

        if time_horizon == TimeHorizon.VERY_LONG_TERM:
            # 长期投资者更重视稳定性和持续性
            return stability_score * 0.5 + persistence_score * 0.5
        elif time_horizon == TimeHorizon.LONG_TERM:
            return stability_score * 0.6 + persistence_score * 0.4
        elif time_horizon == TimeHorizon.MEDIUM_TERM:
            return stability_score * 0.7 + persistence_score * 0.3
        else:  # SHORT_TERM
            # 短期投资者更重视当前表现
            return min(100, performance.annual_return * 400)

    def _calculate_complexity_alignment(
        self,
        investor_profile: InvestorProfile,
        strategy_ranking: StrategyRanking
    ) -> float:
        """计算复杂度适配度"""

        experience = investor_profile.characteristics.investment_experience
        strategy_complexity = self._assess_strategy_complexity(strategy_ranking)

        experience_scores = {
            'beginner': 1,
            'intermediate': 2,
            'advanced': 3,
            'expert': 4
        }

        exp_score = experience_scores[experience]

        # 复杂度匹配评分
        if abs(exp_score - strategy_complexity) <= 1:
            return 100  # 复杂度匹配
        elif exp_score > strategy_complexity:
            return 85   # 经验丰富，策略简单
        else:
            return 60   # 经验不足，策略复杂

    def _assess_strategy_complexity(self, strategy_ranking: StrategyRanking) -> int:
        """评估策略复杂度"""

        complexity_score = 1

        # 基于参数数量
        param_count = len(strategy_ranking.parameters)
        if param_count > 5:
            complexity_score += 1
        if param_count > 10:
            complexity_score += 1

        # 基于策略类型
        strategy_type = strategy_ranking.strategy_type.lower()
        if any(complex_word in strategy_type for complex_word in ['multi', 'advanced', 'optimized']):
            complexity_score += 1

        # 基于交易频率
        if strategy_ranking.performance_metrics.total_trades > 100:
            complexity_score += 1

        return min(4, complexity_score)

    def _calculate_cost_alignment(
        self,
        investor_profile: InvestorProfile,
        performance: PerformanceMetrics
    ) -> float:
        """计算成本敏感度匹配"""

        # 计算成本效率
        total_return = abs(performance.total_return)
        trading_costs = performance.trading_costs

        if total_return == 0:
            return 20  # 无收益的情况下成本效率很低

        cost_ratio = trading_costs / total_return

        # 成本敏感度越低，越能容忍高成本
        cost_tolerance = 1 - investor_profile.characteristics.loss_aversion

        if cost_ratio <= 0.02:  # 成本占比小于2%
            return 100
        elif cost_ratio <= 0.05:  # 成本占比小于5%
            return max(80, 100 - cost_ratio * 1000)
        elif cost_ratio <= 0.1:   # 成本占比小于10%
            return max(60, 100 - cost_ratio * 1500)
        else:
            return max(20, 100 - cost_ratio * 2000) * cost_tolerance

    def _calculate_liquidity_alignment(
        self,
        investor_profile: InvestorProfile,
        strategy_ranking: StrategyRanking
    ) -> float:
        """计算流动性匹配度"""

        liquidity_needs = investor_profile.characteristics.liquidity_needs

        # 基于交易频率评估流动性
        trading_frequency = strategy_ranking.performance_metrics.total_trades

        if trading_frequency < 20:  # 低频交易
            liquidity_score = 80
        elif trading_frequency < 100:  # 中频交易
            liquidity_score = 60
        else:  # 高频交易
            liquidity_score = 40

        # 根据流动性需求调整
        if liquidity_needs < 0.3:  # 流动性需求低
            return liquidity_score
        elif liquidity_needs < 0.6:  # 流动性需求中等
            return liquidity_score * 0.8
        else:  # 流动性需求高
            return liquidity_score * 0.6

    def _calculate_behavioral_alignment(
        self,
        investor_profile: InvestorProfile,
        strategy_ranking: StrategyRanking
    ) -> float:
        """计算行为匹配度"""

        emotional_stability = investor_profile.characteristics.emotional_stability
        decision_confidence = investor_profile.characteristics.decision_confidence
        market_knowledge = investor_profile.characteristics.market_knowledge

        # 基于策略的波动性要求
        volatility_tolerance = emotional_stability * decision_confidence

        # 策略风险等级匹配
        risk_level_scores = {
            'LOW': 100,
            'MEDIUM': 80,
            'HIGH': 60,
            'VERY_HIGH': 40
        }

        strategy_risk_score = risk_level_scores.get(strategy_ranking.risk_level, 50)

        # 根据市场知识调整
        knowledge_factor = 0.7 + market_knowledge * 0.3

        return strategy_risk_score * knowledge_factor * volatility_tolerance

    def _calculate_allocation_suggestion(
        self,
        match_score: float,
        investor_profile: InvestorProfile,
        strategy_ranking: StrategyRanking
    ) -> float:
        """计算建议配置比例"""

        base_allocation = investor_profile.max_portfolio_allocation

        # 根据匹配度调整
        allocation_factor = match_score / 100

        # 根据风险等级调整
        risk_adjustments = {
            'LOW': 1.2,
            'MEDIUM': 1.0,
            'HIGH': 0.8,
            'VERY_HIGH': 0.6
        }

        risk_factor = risk_adjustments.get(strategy_ranking.risk_level, 1.0)

        suggested_allocation = base_allocation * allocation_factor * risk_factor

        return min(suggested_allocation, base_allocation)

    def generate_profile_report(
        self,
        investor_profile: InvestorProfile,
        match_results: List[StrategyMatchResult],
        output_file: Optional[str] = None
    ) -> str:
        """
        生成投资者画像报告

        Args:
            investor_profile: 投资者画像
            match_results: 策略匹配结果
            output_file: 输出文件路径

        Returns:
            报告内容
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        report_lines = [
            "# 投资者画像与策略匹配报告",
            f"生成时间: {timestamp}",
            f"投资者画像: {investor_profile.profile_name}",
            "",
            "## 投资者画像分析",
            ""
        ]

        # 基本特征
        char = investor_profile.characteristics
        report_lines.extend([
            "### 基本特征",
            f"- **年龄**: {char.age}岁",
            f"- **收入水平**: {char.income_level}",
            f"- **净资产**: {char.net_worth}",
            f"- **投资经验**: {char.investment_experience}",
            f"- **投资组合规模**: {char.portfolio_size:.1f}万元",
            ""
        ])

        # 风险特征
        report_lines.extend([
            "### 风险特征",
            f"- **风险承受能力**: {char.risk_tolerance.value}",
            f"- **损失厌恶程度**: {char.loss_aversion:.2f}",
            f"- **波动性敏感度**: {char.volatility_sensitivity:.2f}",
            f"- **最大可接受损失**: {char.max_acceptable_loss*100:.1f}%",
            f"- **风险画像**: {investor_profile.risk_profile}",
            f"- **风险承担能力**: {investor_profile.risk_capacity:.2f}",
            ""
        ])

        # 投资偏好
        report_lines.extend([
            "### 投资偏好",
            f"- **投资目标**: {char.investment_goal.value}",
            f"- **投资期限**: {char.time_horizon.value}",
            f"- **期望年化收益**: {char.expected_return*100:.1f}%",
            f"- **流动性需求**: {char.liquidity_needs:.2f}",
            f"- **分散化偏好**: {char.diversification_preference:.2f}",
            ""
        ])

        # Top 5 匹配策略
        top_matches = match_results[:5]
        report_lines.extend([
            "## Top 5 匹配策略",
            "| 排名 | 策略名称 | 匹配度 | 综合评分 | 风险等级 | 建议配置 | 关键优势 |",
            "|------|----------|--------|----------|----------|----------|----------|"
        ])

        for i, match in enumerate(top_matches, 1):
            advantages = ', '.join(match.match_reasons[:2]) if match.match_reasons else "无明显优势"
            report_lines.append(
                f"| {i} | {match.strategy_ranking.strategy_name} | "
                f"{match.match_score:.1f} | {match.strategy_ranking.overall_score:.1f} | "
                f"{match.strategy_ranking.risk_level} | {match.allocation_suggestion*100:.1f}% | {advantages} |"
            )

        # 详细策略分析
        report_lines.extend([
            "",
            "## 详细策略分析",
            ""
        ])

        for i, match in enumerate(top_matches[:3], 1):
            strategy = match.strategy_ranking
            perf = strategy.performance_metrics
            risk = strategy.risk_metrics

            report_lines.extend([
                f"### {i}. {strategy.strategy_name}",
                f"**匹配度评分**: {match.match_score:.1f}/100",
                f"**综合评级**: {strategy.rating} ({strategy.recommendation})",
                "",
                "#### 性能指标",
                f"- 总收益率: {perf.total_return*100:.2f}%",
                f"- 年化收益率: {perf.annual_return*100:.2f}%",
                f"- Sharpe比率: {perf.sharpe_ratio:.3f}",
                f"- 最大回撤: {risk.max_drawdown*100:.2f}%",
                f"- 胜率: {perf.win_rate*100:.2f}%",
                f"- 总交易次数: {perf.total_trades}",
                f"- 交易成本: {perf.trading_costs:,.0f}",
                "",
                "#### 匹配分析",
                f"**匹配原因**: {', '.join(match.match_reasons)}" if match.match_reasons else "**匹配原因**: 基本符合要求",
                f"**风险提示**: {', '.join(match.risk_warnings)}" if match.risk_warnings else "**风险提示**: 需要常规监控",
                f"**监控要点**: {', '.join(match.monitoring_points)}" if match.monitoring_points else "**监控要点**: 标准监控即可",
                f"**建议配置**: {match.allocation_suggestion*100:.1f}%",
                ""
            ])

        # 投资建议
        report_lines.extend([
            "## 投资建议",
            "",
            "### 资产配置建议",
            f"- **单一策略最大配置**: {investor_profile.max_portfolio_allocation*100:.1f}%",
            f"- **建议策略数量**: {min(3, len(top_matches))}个",
            f"- **再平衡频率**: {investor_profile.rebalancing_frequency}",
            f"- **业绩评估周期**: {investor_profile.performance_review_period}",
            ""
        ])

        # 风险提示
        all_warnings = set()
        for match in top_matches:
            all_warnings.update(match.risk_warnings)

        if all_warnings:
            report_lines.extend([
                "### 风险提示",
                *[f"- {warning}" for warning in sorted(all_warnings)],
                ""
            ])

        # 实施建议
        report_lines.extend([
            "### 实施建议",
            "1. **分散投资**: 建议配置2-3个不同类型的策略",
            "2. **定期评估**: 按建议周期进行业绩评估和调整",
            "3. **风险监控**: 建立完善的监控系统，关注关键指标变化",
            "4. **渐进投入**: 建议分阶段投入，初期可使用较低仓位",
            "5. **持续学习**: 提升投资知识，增强对策略的理解",
            "",
            "### 免责声明",
            "- 本报告基于历史数据生成，过去表现不代表未来收益",
            "- 投资有风险，决策需谨慎",
            "- 建议在投资前咨询专业的财务顾问",
            ""
        ])

        report_content = '\n'.join(report_lines)

        # 保存报告
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"Profile report saved to: {output_file}")

        # 更新统计
        self.profiling_stats['recommendations_generated'] += 1

        return report_content

    def get_profiling_summary(self) -> Dict[str, Any]:
        """获取画像系统总结"""
        return {
            'profiling_statistics': self.profiling_stats,
            'available_templates': list(self.profile_templates.keys()),
            'matching_weights': self.matching_weights
        }

# 便利函数
def create_quick_investor_profile(
    profile_type: str,
    customizations: Optional[Dict[str, Any]] = None
) -> InvestorProfile:
    """
    快速创建投资者画像

    Args:
        profile_type: 画像类型 (aggressive, balanced, conservative, institutional)
        customizations: 自定义设置

    Returns:
        投资者画像
    """
    system = InvestorProfilingSystem()

    profile_data = customizations or {}
    profile_data['profile_name'] = f"{profile_type.title()} Investor"

    return system.create_investor_profile(profile_data, profile_type)

def quick_strategy_matching(
    profile_type: str,
    strategy_rankings: List[StrategyRanking]
) -> Dict[str, Any]:
    """
    快速策略匹配

    Args:
        profile_type: 画像类型
        strategy_rankings: 策略排名列表

    Returns:
        匹配结果
    """
    system = InvestorProfilingSystem()

    # 创建投资者画像
    profile = create_quick_investor_profile(profile_type)

    # 匹配策略
    match_results = system.match_strategies_to_profile(profile, strategy_rankings)

    # 生成报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"investor_profile_report_{profile_type}_{timestamp}.md"
    system.generate_profile_report(profile, match_results, report_file)

    return {
        'investor_profile': profile,
        'match_results': match_results,
        'top_matches': match_results[:5],
        'report_file': report_file
    }

if __name__ == "__main__":
    print("投资者画像匹配系统已就绪")
    print("使用 create_quick_investor_profile() 创建画像")
    print("使用 quick_strategy_matching() 进行策略匹配")
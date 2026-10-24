"""
Composite Signal Generator - Phase 4.4 Implementation
复合信号生成器 - Phase 4.4实施

This module implements comprehensive composite signal generation that integrates
all indicator signals with explainable AI capabilities, quality assessment,
and visualization support.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
from pathlib import Path
import warnings
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix
# Visualization imports (optional)
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None
    px = None
    make_subplots = None

# Import signal components
try:
    from .signal_generator import SignalGenerator, Signal, SignalType, SignalFormat
    from .weight_manager import DynamicWeightManager
    from .conflict_resolver import ConflictResolver, ConflictResolutionStrategy, SignalConflict
except ImportError:
    # Fallback for standalone testing
    from signal_generator import SignalGenerator, Signal, SignalType, SignalFormat
    from weight_manager import DynamicWeightManager
    from conflict_resolver import ConflictResolver, ConflictResolutionStrategy, SignalConflict

logger = logging.getLogger(__name__)

class SignalQuality(Enum):
    """信号质量等级"""
    EXCELLENT = "excellent"    # 优秀 (>0.9)
    GOOD = "good"             # 良好 (0.7-0.9)
    FAIR = "fair"             # 一般 (0.5-0.7)
    POOR = "poor"             # 较差 (0.3-0.5)
    VERY_POOR = "very_poor"   # 很差 (<0.3)

class ExplanationLevel(Enum):
    """解释详细程度"""
    MINIMAL = "minimal"       # 最少信息
    BASIC = "basic"          # 基本解释
    DETAILED = "detailed"    # 详细解释
    COMPREHENSIVE = "comprehensive"  # 全面解释

@dataclass
class SignalExplanation:
    """信号解释数据结构"""
    summary: str                           # 信号摘要
    reasoning: List[str]                   # 推理过程
    key_factors: Dict[str, float]          # 关键因素
    contributing_indicators: List[str]     # 贡献指标
    confidence_breakdown: Dict[str, float] # 置信度分解
    risk_factors: List[str]                # 风险因素
    market_context: Dict[str, Any]         # 市场上下文
    level: ExplanationLevel               # 解释级别

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'summary': self.summary,
            'reasoning': self.reasoning,
            'key_factors': self.key_factors,
            'contributing_indicators': self.contributing_indicators,
            'confidence_breakdown': self.confidence_breakdown,
            'risk_factors': self.risk_factors,
            'market_context': self.market_context,
            'level': self.level.value
        }

@dataclass
class CompositeSignal:
    """复合信号数据结构"""
    timestamp: datetime
    signal_type: SignalType
    signal_value: float
    strength: float                    # 信号强度 1-10
    confidence: float                  # 置信度 0-1
    quality: SignalQuality             # 信号质量
    explanation: SignalExplanation      # 信号解释
    component_signals: List[Signal]    # 组成信号
    weights: Dict[str, float]          # 使用的权重
    resolution_strategy: Optional[ConflictResolutionStrategy] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'signal_type': self.signal_type.value,
            'signal_value': self.signal_value,
            'strength': self.strength,
            'confidence': self.confidence,
            'quality': self.quality.value,
            'explanation': self.explanation.to_dict(),
            'component_signals': [s.to_dict() for s in self.component_signals],
            'weights': self.weights,
            'resolution_strategy': self.resolution_strategy.value if self.resolution_strategy else None,
            'metadata': self.metadata
        }

@dataclass
class CompositeSignalMetrics:
    """复合信号性能指标"""
    total_signals: int = 0
    signal_accuracy: float = 0.0
    quality_distribution: Dict[str, int] = field(default_factory=dict)
    avg_confidence: float = 0.0
    avg_strength: float = 0.0
    explanation_effectiveness: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

class ExplainableAI:
    """可解释AI组件"""

    def __init__(self, explanation_level: ExplanationLevel = ExplanationLevel.DETAILED):
        """
        初始化可解释AI组件

        Args:
            explanation_level: 解释详细程度
        """
        self.explanation_level = explanation_level

        # 信号类型解释模板
        self.explanation_templates = {
            SignalType.STRONG_BUY: {
                'summary': "强烈买入信号",
                'reasoning': [
                    "多个指标同时显示强烈的买入信号",
                    "市场趋势支持向上突破",
                    "技术指标形成多头排列"
                ],
                'key_factors': ["趋势强度", "动量指标", "成交量确认"]
            },
            SignalType.BUY: {
                'summary': "买入信号",
                'reasoning': [
                    "技术指标显示买入机会",
                    "价格处于相对低位",
                    "短期趋势向上"
                ],
                'key_factors': ["超卖反弹", "趋势确认", "支撑位"]
            },
            SignalType.HOLD: {
                'summary': "持有信号",
                'reasoning': [
                    "多空信号平衡",
                    "缺乏明确方向",
                    "建议观望"
                ],
                'key_factors': ["市场观望", "方向不明", "风险控制"]
            },
            SignalType.SELL: {
                'summary': "卖出信号",
                'reasoning': [
                    "技术指标显示卖出信号",
                    "价格处于相对高位",
                    "短期趋势向下"
                ],
                'key_factors': ["超买回调", "阻力位", "获利了结"]
            },
            SignalType.STRONG_SELL: {
                'summary': "强烈卖出信号",
                'reasoning': [
                    "多个指标同时显示强烈的卖出信号",
                    "市场趋势支持向下突破",
                    "技术指标形成空头排列"
                ],
                'key_factors': ["趋势反转", "恐慌情绪", "支撑破位"]
            }
        }

    def generate_explanation(self,
                           composite_signal: CompositeSignal,
                           component_signals: List[Signal],
                           weights: Dict[str, float],
                           market_context: Optional[Dict[str, Any]] = None) -> SignalExplanation:
        """
        生成信号解释

        Args:
            composite_signal: 复合信号
            component_signals: 组成信号
            weights: 权重
            market_context: 市场上下文

        Returns:
            SignalExplanation: 信号解释
        """
        signal_type = composite_signal.signal_type
        template = self.explanation_templates.get(signal_type, self.explanation_templates[SignalType.HOLD])

        # 基础解释
        summary = template['summary']
        reasoning = template['reasoning'].copy()

        # 根据详细程度添加解释
        if self.explanation_level in [ExplanationLevel.DETAILED, ExplanationLevel.COMPREHENSIVE]:
            reasoning.extend(self._generate_detailed_reasoning(component_signals, weights))

        if self.explanation_level == ExplanationLevel.COMPREHENSIVE:
            reasoning.extend(self._generate_comprehensive_reasoning(market_context))

        # 计算关键因素
        key_factors = self._identify_key_factors(component_signals, weights)

        # 识别贡献指标
        contributing_indicators = self._identify_contributing_indicators(component_signals, weights)

        # 置信度分解
        confidence_breakdown = self._calculate_confidence_breakdown(component_signals, weights)

        # 识别风险因素
        risk_factors = self._identify_risk_factors(component_signals, composite_signal)

        return SignalExplanation(
            summary=summary,
            reasoning=reasoning,
            key_factors=key_factors,
            contributing_indicators=contributing_indicators,
            confidence_breakdown=confidence_breakdown,
            risk_factors=risk_factors,
            market_context=market_context or {},
            level=self.explanation_level
        )

    def _generate_detailed_reasoning(self,
                                   component_signals: List[Signal],
                                   weights: Dict[str, float]) -> List[str]:
        """生成详细推理"""
        reasoning = []

        # 按信号类型分组
        signal_groups = defaultdict(list)
        for signal in component_signals:
            signal_groups[signal.signal_type].append(signal)

        # 添加群体分析
        for signal_type, signals in signal_groups.items():
            count = len(signals)
            avg_strength = np.mean([s.strength for s in signals])
            avg_confidence = np.mean([s.confidence for s in signals])

            reasoning.append(
                f"{count}个{signal_type.name}信号，平均强度{avg_strength:.1f}，平均置信度{avg_confidence:.2f}"
            )

        # 添加权重分析
        if weights:
            top_weighted = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:3]
            reasoning.append(f"权重最高的指标: {', '.join([f'{k}({v:.2f})' for k, v in top_weighted])}")

        return reasoning

    def _generate_comprehensive_reasoning(self,
                                        market_context: Optional[Dict[str, Any]]) -> List[str]:
        """生成全面推理"""
        reasoning = []

        if market_context:
            # 市场状态分析
            if 'regime' in market_context:
                reasoning.append(f"当前市场状态: {market_context['regime']}")

            # 波动率分析
            if 'volatility' in market_context:
                volatility = market_context['volatility']
                if volatility > 0.03:
                    reasoning.append(f"市场波动率较高 ({volatility:.2%})，需要谨慎")
                elif volatility < 0.01:
                    reasoning.append(f"市场波动率较低 ({volatility:.2%})，趋势可能持续")

            # 趋势分析
            if 'trend' in market_context:
                reasoning.append(f"整体趋势: {market_context['trend']}")

        return reasoning

    def _identify_key_factors(self,
                            component_signals: List[Signal],
                            weights: Dict[str, float]) -> Dict[str, float]:
        """识别关键因素"""
        key_factors = {}

        # 按指标类型分组
        indicator_types = defaultdict(list)
        for signal in component_signals:
            indicator_type = signal.indicator_name.split('_')[0]  # 提取指标类型前缀
            indicator_types[indicator_type].append(signal)

        # 计算每种类型的加权影响力
        for indicator_type, signals in indicator_types.items():
            total_influence = 0
            for signal in signals:
                weight = weights.get(signal.indicator_name, 1.0)
                influence = signal.strength * signal.confidence * weight
                total_influence += influence

            key_factors[indicator_type] = total_influence

        # 标准化并排序
        if key_factors:
            max_influence = max(key_factors.values())
            key_factors = {k: v/max_influence for k, v in key_factors.items()}

        return dict(sorted(key_factors.items(), key=lambda x: x[1], reverse=True))

    def _identify_contributing_indicators(self,
                                        component_signals: List[Signal],
                                        weights: Dict[str, float]) -> List[str]:
        """识别贡献指标"""
        # 计算每个指标的贡献分数
        contributions = {}
        for signal in component_signals:
            weight = weights.get(signal.indicator_name, 1.0)
            contribution = signal.strength * signal.confidence * weight * abs(signal.signal_value)
            contributions[signal.indicator_name] = contribution

        # 返回贡献最高的指标
        sorted_contributions = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
        return [indicator for indicator, _ in sorted_contributions[:5]]  # 前5个

    def _calculate_confidence_breakdown(self,
                                      component_signals: List[Signal],
                                      weights: Dict[str, float]) -> Dict[str, float]:
        """计算置信度分解"""
        breakdown = {}

        for signal in component_signals:
            weight = weights.get(signal.indicator_name, 1.0)
            weighted_confidence = signal.confidence * weight
            breakdown[signal.indicator_name] = weighted_confidence

        # 标准化
        if breakdown:
            total = sum(breakdown.values())
            if total > 0:
                breakdown = {k: v/total for k, v in breakdown.items()}

        return dict(sorted(breakdown.items(), key=lambda x: x[1], reverse=True))

    def _identify_risk_factors(self,
                             component_signals: List[Signal],
                             composite_signal: CompositeSignal) -> List[str]:
        """识别风险因素"""
        risk_factors = []

        # 低置信度风险
        if composite_signal.confidence < 0.5:
            risk_factors.append("信号置信度较低")

        # 信号冲突风险
        signal_types = [s.signal_type for s in component_signals]
        if len(set(signal_types)) > 2:  # 超过2种不同信号类型
            risk_factors.append("存在较多信号冲突")

        # 低强度风险
        if composite_signal.strength < 3.0:
            risk_factors.append("信号强度较弱")

        # 置信度分散风险
        confidences = [s.confidence for s in component_signals]
        if np.std(confidences) > 0.3:
            risk_factors.append("各指标置信度差异较大")

        return risk_factors

class SignalQualityAssessor:
    """信号质量评估器"""

    def __init__(self):
        """初始化信号质量评估器"""
        self.quality_thresholds = {
            SignalQuality.EXCELLENT: 0.9,
            SignalQuality.GOOD: 0.7,
            SignalQuality.FAIR: 0.5,
            SignalQuality.POOR: 0.3,
            SignalQuality.VERY_POOR: 0.0
        }

    def assess_signal_quality(self,
                            composite_signal: CompositeSignal,
                            component_signals: List[Signal],
                            market_context: Optional[Dict[str, Any]] = None) -> SignalQuality:
        """
        评估信号质量

        Args:
            composite_signal: 复合信号
            component_signals: 组成信号
            market_context: 市场上下文

        Returns:
            SignalQuality: 信号质量等级
        """
        quality_score = 0.0

        # 1. 置信度评分 (30%)
        confidence_score = composite_signal.confidence * 0.3

        # 2. 信号强度评分 (25%)
        strength_score = min(1.0, composite_signal.strength / 10) * 0.25

        # 3. 信号一致性评分 (20%)
        consistency_score = self._calculate_signal_consistency(component_signals) * 0.2

        # 4. 市场适应性评分 (15%)
        market_score = self._calculate_market_adaptability(composite_signal, market_context) * 0.15

        # 5. 历史表现评分 (10%)
        historical_score = self._calculate_historical_performance_score(composite_signal) * 0.1

        quality_score = confidence_score + strength_score + consistency_score + market_score + historical_score

        # 确定质量等级
        for quality, threshold in sorted(self.quality_thresholds.items(), key=lambda x: x[1], reverse=True):
            if quality_score >= threshold:
                return quality

        return SignalQuality.VERY_POOR

    def _calculate_signal_consistency(self, component_signals: List[Signal]) -> float:
        """计算信号一致性"""
        if len(component_signals) < 2:
            return 0.5

        # 计算信号值的标准差（越小越一致）
        signal_values = [s.signal_value for s in component_signals]
        value_std = np.std(signal_values)

        # 计算置信度的标准差（越小越一致）
        confidences = [s.confidence for s in component_signals]
        confidence_std = np.std(confidences)

        # 综合一致性分数
        value_consistency = max(0, 1 - value_std / 2)  # 归一化
        confidence_consistency = max(0, 1 - confidence_std)

        return (value_consistency + confidence_consistency) / 2

    def _calculate_market_adaptability(self,
                                     composite_signal: CompositeSignal,
                                     market_context: Optional[Dict[str, Any]]) -> float:
        """计算市场适应性"""
        if not market_context:
            return 0.5

        score = 0.5  # 基础分数

        # 根据市场状态调整
        market_regime = market_context.get('regime', 'neutral')
        signal_type = composite_signal.signal_type

        if market_regime == 'bull' and signal_type.value > 0:
            score += 0.3  # 牛市中的买入信号更合适
        elif market_regime == 'bear' and signal_type.value < 0:
            score += 0.3  # 熊市中的卖出信号更合适
        elif market_regime == 'sideways' and signal_type == SignalType.HOLD:
            score += 0.3  # 震荡市中的持有信号更合适

        # 根据波动率调整
        volatility = market_context.get('volatility', 0.02)
        if volatility > 0.03 and composite_signal.confidence > 0.7:
            score += 0.2  # 高波动市场中的高置信度信号更可靠

        return min(1.0, score)

    def _calculate_historical_performance_score(self, composite_signal: CompositeSignal) -> float:
        """计算历史表现分数（简化实现）"""
        # 这里应该基于历史信号的实际表现来计算
        # 暂时返回基于置信度的估算分数
        return composite_signal.confidence

class CompositeSignalGenerator:
    """
    复合信号生成器 - Phase 4.4核心实现

    功能：
    1. 集成所有指标信号
    2. 计算综合信号强度
    3. 生成信号解释和推理
    4. 实现信号质量评估
    5. 创建信号可视化
    """

    def __init__(self,
                 signal_generator: SignalGenerator,
                 weight_manager: DynamicWeightManager,
                 conflict_resolver: ConflictResolver,
                 explanation_level: ExplanationLevel = ExplanationLevel.DETAILED,
                 enable_quality_assessment: bool = True,
                 cache_dir: Optional[str] = None):
        """
        初始化复合信号生成器

        Args:
            signal_generator: 信号生成器
            weight_manager: 权重管理器
            conflict_resolver: 冲突解决器
            explanation_level: 解释详细程度
            enable_quality_assessment: 启用质量评估
            cache_dir: 缓存目录
        """
        self.signal_generator = signal_generator
        self.weight_manager = weight_manager
        self.conflict_resolver = conflict_resolver
        self.explanation_level = explanation_level
        self.enable_quality_assessment = enable_quality_assessment

        # 初始化组件
        self.explainable_ai = ExplainableAI(explanation_level)
        self.quality_assessor = SignalQualityAssessor() if enable_quality_assessment else None

        # 信号历史记录
        self.signal_history: List[CompositeSignal] = []

        # 性能指标
        self.metrics = CompositeSignalMetrics()

        # 缓存设置
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./cache/composite_signals")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info("CompositeSignalGenerator initialized")

    def generate_composite_signal(self,
                                indicator_data: Dict[str, pd.Series],
                                parameters: Dict[str, Dict[str, Any]],
                                market_context: Optional[Dict[str, Any]] = None,
                                custom_weights: Optional[Dict[str, float]] = None) -> CompositeSignal:
        """
        生成复合信号

        Args:
            indicator_data: 指标数据 {indicator_name: indicator_values}
            parameters: 指标参数 {indicator_name: parameters}
            market_context: 市场上下文
            custom_weights: 自定义权重

        Returns:
            CompositeSignal: 复合信号
        """
        try:
            # 1. 生成所有指标的单独信号
            component_signals = self._generate_component_signals(indicator_data, parameters)

            if not component_signals:
                return self._create_default_composite_signal()

            # 2. 获取权重
            if custom_weights:
                current_weights = custom_weights
            else:
                # 动态调整权重
                performance_data = self._prepare_performance_data(component_signals)
                current_weights = self.weight_manager.update_weights(
                    performance_data, market_context or {}
                )

            # 3. 解决信号冲突
            resolved_signal, conflicts = self.conflict_resolver.resolve_conflicts(
                component_signals, current_weights, market_context
            )

            # 4. 生成复合信号
            if resolved_signal:
                composite_signal = self._create_composite_signal_from_resolved(
                    resolved_signal, component_signals, current_weights, conflicts, market_context
                )
            else:
                # 如果没有解决信号，使用默认合并方法
                composite_signal = self._create_merged_composite_signal(
                    component_signals, current_weights, market_context
                )

            # 5. 生成解释
            composite_signal.explanation = self.explainable_ai.generate_explanation(
                composite_signal, component_signals, current_weights, market_context
            )

            # 6. 评估质量
            if self.quality_assessor:
                composite_signal.quality = self.quality_assessor.assess_signal_quality(
                    composite_signal, component_signals, market_context
                )

            # 7. 更新历史记录和指标
            self._update_history_and_metrics(composite_signal)

            logger.debug(f"Generated composite signal: {composite_signal.signal_type.name} "
                        f"(quality: {composite_signal.quality.value}, confidence: {composite_signal.confidence:.2f})")

            return composite_signal

        except Exception as e:
            logger.error(f"Error generating composite signal: {str(e)}")
            return self._create_error_composite_signal(str(e))

    def _generate_component_signals(self,
                                  indicator_data: Dict[str, pd.Series],
                                  parameters: Dict[str, Dict[str, Any]]) -> List[Signal]:
        """生成组成信号"""
        component_signals = []

        for indicator_name, data in indicator_data.items():
            try:
                if len(data) == 0:
                    continue

                # 获取指标参数
                indicator_params = parameters.get(indicator_name, {})
                indicator_params['name'] = indicator_name

                # 生成信号
                signal = self.signal_generator.generate_signal(
                    indicator_name, data, indicator_params
                )

                component_signals.append(signal)

            except Exception as e:
                logger.warning(f"Failed to generate signal for {indicator_name}: {str(e)}")
                continue

        return component_signals

    def _prepare_performance_data(self, component_signals: List[Signal]) -> Dict[str, Any]:
        """准备性能数据用于权重调整"""
        performance_data = {
            'indicator_performance': {},
            'correlation_matrix': {}
        }

        # 计算指标性能
        for signal in component_signals:
            performance_data['indicator_performance'][signal.indicator_name] = {
                'strength': signal.strength,
                'confidence': signal.confidence,
                'signal_value': signal.signal_value,
                'performance_score': signal.strength * signal.confidence
            }

        # 计算相关性矩阵（简化实现）
        indicators = list(set(s.indicator_name for s in component_signals))
        for indicator1 in indicators:
            performance_data['correlation_matrix'][indicator1] = {}
            for indicator2 in indicators:
                if indicator1 == indicator2:
                    performance_data['correlation_matrix'][indicator1][indicator2] = 1.0
                else:
                    # 基于信号类型的相关性估算
                    signals1 = [s for s in component_signals if s.indicator_name == indicator1]
                    signals2 = [s for s in component_signals if s.indicator_name == indicator2]
                    if signals1 and signals2:
                        correlation = self._estimate_signal_correlation(signals1[0], signals2[0])
                        performance_data['correlation_matrix'][indicator1][indicator2] = correlation
                    else:
                        performance_data['correlation_matrix'][indicator1][indicator2] = 0.0

        return performance_data

    def _estimate_signal_correlation(self, signal1: Signal, signal2: Signal) -> float:
        """估算信号相关性"""
        # 基于信号类型的相关性估算
        if signal1.signal_type == signal2.signal_type:
            return 0.8  # 同类型信号高度相关
        elif signal1.signal_type.value * signal2.signal_type.value < 0:
            return -0.6  # 相反信号负相关
        else:
            return 0.2  # 中性相关

    def _create_composite_signal_from_resolved(self,
                                            resolved_signal: Signal,
                                            component_signals: List[Signal],
                                            weights: Dict[str, float],
                                            conflicts: List[SignalConflict],
                                            market_context: Optional[Dict[str, Any]]) -> CompositeSignal:
        """基于解决信号创建复合信号"""
        # 计算复合强度和置信度
        composite_strength = self._calculate_composite_strength(resolved_signal, component_signals, weights)
        composite_confidence = self._calculate_composite_confidence(resolved_signal, component_signals, weights)

        return CompositeSignal(
            timestamp=datetime.now(),
            signal_type=resolved_signal.signal_type,
            signal_value=resolved_signal.signal_value,
            strength=composite_strength,
            confidence=composite_confidence,
            quality=SignalQuality.FAIR,  # 将在后续步骤中更新
            explanation=None,  # 将在后续步骤中生成
            component_signals=component_signals,
            weights=weights,
            resolution_strategy=conflicts[0].resolution_strategy if conflicts else None,
            metadata={
                'conflicts_resolved': len(conflicts),
                'market_context': market_context or {},
                'generation_method': 'conflict_resolution'
            }
        )

    def _create_merged_composite_signal(self,
                                      component_signals: List[Signal],
                                      weights: Dict[str, float],
                                      market_context: Optional[Dict[str, Any]]) -> CompositeSignal:
        """创建合并的复合信号"""
        # 计算加权信号值
        weighted_signal_value = 0
        total_weight = 0

        for signal in component_signals:
            weight = weights.get(signal.indicator_name, 1.0)
            weighted_signal_value += signal.signal_value * weight * signal.confidence
            total_weight += weight * signal.confidence

        if total_weight > 0:
            composite_signal_value = weighted_signal_value / total_weight
        else:
            composite_signal_value = 0

        # 确定信号类型
        if abs(composite_signal_value) < 0.1:
            signal_type = SignalType.HOLD
        elif composite_signal_value > 1.5:
            signal_type = SignalType.STRONG_BUY
        elif composite_signal_value > 0.5:
            signal_type = SignalType.BUY
        elif composite_signal_value < -1.5:
            signal_type = SignalType.STRONG_SELL
        elif composite_signal_value < -0.5:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD

        # 计算复合强度和置信度
        composite_strength = np.mean([s.strength for s in component_signals])
        composite_confidence = np.mean([s.confidence for s in component_signals])

        return CompositeSignal(
            timestamp=datetime.now(),
            signal_type=signal_type,
            signal_value=composite_signal_value,
            strength=composite_strength,
            confidence=composite_confidence,
            quality=SignalQuality.FAIR,  # 将在后续步骤中更新
            explanation=None,  # 将在后续步骤中生成
            component_signals=component_signals,
            weights=weights,
            resolution_strategy=ConflictResolutionStrategy.WEIGHTED_VOTING,
            metadata={
                'market_context': market_context or {},
                'generation_method': 'weighted_merge'
            }
        )

    def _calculate_composite_strength(self,
                                    resolved_signal: Signal,
                                    component_signals: List[Signal],
                                    weights: Dict[str, float]) -> float:
        """计算复合信号强度"""
        # 基于解决信号强度和组成信号强度计算
        base_strength = resolved_signal.strength

        # 考虑支持该信号的权重
        supporting_weight = 0
        total_weight = 0

        for signal in component_signals:
            weight = weights.get(signal.indicator_name, 1.0)
            total_weight += weight

            if signal.signal_type == resolved_signal.signal_type:
                supporting_weight += weight

        if total_weight > 0:
            support_factor = supporting_weight / total_weight
            adjusted_strength = base_strength * (0.7 + 0.3 * support_factor)
        else:
            adjusted_strength = base_strength

        return min(10.0, max(1.0, adjusted_strength))

    def _calculate_composite_confidence(self,
                                      resolved_signal: Signal,
                                      component_signals: List[Signal],
                                      weights: Dict[str, float]) -> float:
        """计算复合信号置信度"""
        # 基于解决信号置信度和组成信号一致性计算
        base_confidence = resolved_signal.confidence

        # 计算信号一致性
        signal_types = [s.signal_type for s in component_signals]
        type_counts = Counter(signal_types)

        # 计算主要信号类型的一致性
        if signal_types:
            most_common_type, count = type_counts.most_common(1)[0]
            consistency = count / len(signal_types)
        else:
            consistency = 0.5

        # 综合置信度
        composite_confidence = base_confidence * (0.6 + 0.4 * consistency)

        return min(1.0, max(0.0, composite_confidence))

    def _create_default_composite_signal(self) -> CompositeSignal:
        """创建默认复合信号"""
        return CompositeSignal(
            timestamp=datetime.now(),
            signal_type=SignalType.HOLD,
            signal_value=0.0,
            strength=1.0,
            confidence=0.5,
            quality=SignalQuality.POOR,
            explanation=SignalExplanation(
                summary="无可用信号",
                reasoning=["缺乏足够的指标数据"],
                key_factors={},
                contributing_indicators=[],
                confidence_breakdown={},
                risk_factors=["数据不足"],
                market_context={},
                level=self.explanation_level
            ),
            component_signals=[],
            weights={},
            metadata={'generation_method': 'default'}
        )

    def _create_error_composite_signal(self, error_message: str) -> CompositeSignal:
        """创建错误复合信号"""
        return CompositeSignal(
            timestamp=datetime.now(),
            signal_type=SignalType.HOLD,
            signal_value=0.0,
            strength=1.0,
            confidence=0.0,
            quality=SignalQuality.VERY_POOR,
            explanation=SignalExplanation(
                summary="信号生成错误",
                reasoning=[f"生成过程中发生错误: {error_message}"],
                key_factors={},
                contributing_indicators=[],
                confidence_breakdown={},
                risk_factors=["系统错误", "数据异常"],
                market_context={},
                level=self.explanation_level
            ),
            component_signals=[],
            weights={},
            metadata={'error': error_message, 'generation_method': 'error'}
        )

    def _update_history_and_metrics(self, composite_signal: CompositeSignal):
        """更新历史记录和性能指标"""
        # 添加到历史记录
        self.signal_history.append(composite_signal)

        # 限制历史记录长度
        if len(self.signal_history) > 1000:
            self.signal_history = self.signal_history[-1000:]

        # 更新性能指标
        self.metrics.total_signals += 1
        self.metrics.avg_confidence = (
            (self.metrics.avg_confidence * (self.metrics.total_signals - 1) + composite_signal.confidence) /
            self.metrics.total_signals
        )
        self.metrics.avg_strength = (
            (self.metrics.avg_strength * (self.metrics.total_signals - 1) + composite_signal.strength) /
            self.metrics.total_signals
        )

        # 更新质量分布
        quality_key = composite_signal.quality.value
        self.metrics.quality_distribution[quality_key] = self.metrics.quality_distribution.get(quality_key, 0) + 1

        self.metrics.last_updated = datetime.now()

    def generate_signal_visualization(self,
                                    composite_signal: CompositeSignal,
                                    save_path: Optional[str] = None) -> Optional[str]:
        """
        生成信号可视化

        Args:
            composite_signal: 复合信号
            save_path: 保存路径

        Returns:
            Optional[str]: 保存的文件路径
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available, skipping visualization")
            return None

        try:
            # 创建子图
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=[
                    '信号强度分布',
                    '指标贡献度',
                    '置信度分解',
                    '信号类型分布'
                ],
                specs=[
                    [{"type": "bar"}, {"type": "pie"}],
                    [{"type": "bar"}, {"type": "pie"}]
                ]
            )

            # 1. 信号强度分布
            component_signals = composite_signal.component_signals
            if component_signals:
                indicators = [s.indicator_name for s in component_signals]
                strengths = [s.strength for s in component_signals]

                fig.add_trace(
                    go.Bar(x=indicators, y=strengths, name='信号强度'),
                    row=1, col=1
                )

            # 2. 指标贡献度（权重饼图）
            if composite_signal.weights:
                fig.add_trace(
                    go.Pie(
                        labels=list(composite_signal.weights.keys()),
                        values=list(composite_signal.weights.values()),
                        name='指标权重'
                    ),
                    row=1, col=2
                )

            # 3. 置信度分解
            if composite_signal.explanation and composite_signal.explanation.confidence_breakdown:
                confidence_items = list(composite_signal.explanation.confidence_breakdown.keys())
                confidence_values = list(composite_signal.explanation.confidence_breakdown.values())

                fig.add_trace(
                    go.Bar(x=confidence_items, y=confidence_values, name='置信度'),
                    row=2, col=1
                )

            # 4. 信号类型分布
            if component_signals:
                signal_types = [s.signal_type.name for s in component_signals]
                type_counts = Counter(signal_types)

                fig.add_trace(
                    go.Pie(
                        labels=list(type_counts.keys()),
                        values=list(type_counts.values()),
                        name='信号类型'
                    ),
                    row=2, col=2
                )

            # 更新布局
            fig.update_layout(
                title_text=f"复合信号分析 - {composite_signal.signal_type.name}",
                showlegend=False,
                height=600
            )

            # 保存或显示
            if save_path:
                fig.write_html(save_path)
                logger.info(f"Signal visualization saved to: {save_path}")
                return save_path
            else:
                fig.show()
                return None

        except Exception as e:
            logger.error(f"Error generating signal visualization: {str(e)}")
            return None

    def generate_explanation_report(self, composite_signal: CompositeSignal) -> str:
        """
        生成解释报告

        Args:
            composite_signal: 复合信号

        Returns:
            str: 解释报告
        """
        if not composite_signal.explanation:
            return "无可用解释"

        explanation = composite_signal.explanation

        report = f"""
# 复合信号解释报告

## 信号摘要
{explanation.summary}

## 信号详情
- **信号类型**: {composite_signal.signal_type.name}
- **信号强度**: {composite_signal.strength:.2f}/10
- **置信度**: {composite_signal.confidence:.2%}
- **信号质量**: {composite_signal.quality.value}
- **生成时间**: {composite_signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

## 推理过程
"""
        for i, reason in enumerate(explanation.reasoning, 1):
            report += f"{i}. {reason}\n"

        report += f"""
## 关键因素
"""
        for factor, score in explanation.key_factors.items():
            report += f"- **{factor}**: {score:.2f}\n"

        report += f"""
## 贡献指标
{', '.join(explanation.contributing_indicators)}

## 置信度分解
"""
        for indicator, confidence in explanation.confidence_breakdown.items():
            report += f"- **{indicator}**: {confidence:.2%}\n"

        if explanation.risk_factors:
            report += f"""
## 风险因素
"""
            for risk in explanation.risk_factors:
                report += f"- ⚠️ {risk}\n"

        if explanation.market_context:
            report += f"""
## 市场上下文
"""
            for key, value in explanation.market_context.items():
                report += f"- **{key}**: {value}\n"

        return report

    def export_composite_signals(self,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None,
                               format: str = 'dataframe') -> Union[pd.DataFrame, List[Dict]]:
        """
        导出复合信号数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            format: 导出格式 ('dataframe', 'dict')

        Returns:
            复合信号数据
        """
        # 过滤信号
        filtered_signals = []
        for signal in self.signal_history:
            if start_date and signal.timestamp < start_date:
                continue
            if end_date and signal.timestamp > end_date:
                continue
            filtered_signals.append(signal)

        if format == 'dataframe':
            data = []
            for signal in filtered_signals:
                data.append({
                    'timestamp': signal.timestamp,
                    'signal_type': signal.signal_type.name,
                    'signal_value': signal.signal_value,
                    'strength': signal.strength,
                    'confidence': signal.confidence,
                    'quality': signal.quality.value,
                    'component_count': len(signal.component_signals),
                    'resolution_strategy': signal.resolution_strategy.value if signal.resolution_strategy else None
                })
            return pd.DataFrame(data)
        elif format == 'dict':
            return [signal.to_dict() for signal in filtered_signals]
        else:
            raise ValueError(f"Unknown export format: {format}")

    def get_performance_metrics(self) -> CompositeSignalMetrics:
        """获取性能指标"""
        return self.metrics

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成综合报告"""
        metrics = self.get_performance_metrics()

        # 获取最近的信号统计
        recent_signals = self.signal_history[-100:] if len(self.signal_history) >= 100 else self.signal_history

        recent_stats = {
            'total_signals': len(recent_signals),
            'avg_confidence': np.mean([s.confidence for s in recent_signals]) if recent_signals else 0,
            'avg_strength': np.mean([s.strength for s in recent_signals]) if recent_signals else 0,
            'signal_type_distribution': Counter([s.signal_type.name for s in recent_signals]),
            'quality_distribution': Counter([s.quality.value for s in recent_signals])
        }

        return {
            'performance_metrics': {
                'total_signals': metrics.total_signals,
                'signal_accuracy': metrics.signal_accuracy,
                'avg_confidence': metrics.avg_confidence,
                'avg_strength': metrics.avg_strength,
                'explanation_effectiveness': metrics.explanation_effectiveness
            },
            'recent_statistics': recent_stats,
            'configuration': {
                'explanation_level': self.explanation_level.value,
                'quality_assessment_enabled': self.enable_quality_assessment,
                'cache_directory': str(self.cache_dir)
            },
            'signal_history_length': len(self.signal_history),
            'last_updated': metrics.last_updated.isoformat()
        }

    def clear_history(self):
        """清除历史记录"""
        self.signal_history.clear()
        self.metrics = CompositeSignalMetrics()
        logger.info("Composite signal history cleared")

    def save_state(self):
        """保存状态"""
        try:
            state_file = self.cache_dir / "composite_signal_state.json"

            state = {
                'metrics': self.metrics.__dict__,
                'signal_history': [signal.to_dict() for signal in self.signal_history[-100:]],  # 只保存最近100条
                'configuration': {
                    'explanation_level': self.explanation_level.value,
                    'quality_assessment_enabled': self.enable_quality_assessment
                },
                'last_saved': datetime.now().isoformat()
            }

            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

            logger.debug("Composite signal state saved")

        except Exception as e:
            logger.error(f"Failed to save state: {str(e)}")

    def load_state(self):
        """加载状态"""
        try:
            state_file = self.cache_dir / "composite_signal_state.json"
            if state_file.exists():
                with open(state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)

                # 恢复指标
                if 'metrics' in state:
                    self.metrics = CompositeSignalMetrics(**state['metrics'])

                # 恢复历史记录（简化恢复）
                if 'signal_history' in state:
                    for signal_data in state['signal_history']:
                        # 这里需要完整的信号重构逻辑，暂时跳过
                        pass

                logger.debug("Composite signal state loaded")

        except Exception as e:
            logger.warning(f"Failed to load state: {str(e)}")
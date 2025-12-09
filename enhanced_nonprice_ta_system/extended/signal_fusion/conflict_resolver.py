"""
Conflict Resolver - Phase 4.3 Implementation
信号冲突解决器 - Phase 4.3实施

This module implements sophisticated conflict resolution mechanisms for handling
conflicting signals from multiple indicators, including multiple strategies,
learning mechanisms, and effect assessment.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
from pathlib import Path
import warnings
from collections import Counter, defaultdict
# ML imports (optional)
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    import pickle
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    RandomForestClassifier = None
    StandardScaler = None
    pickle = None

# Import signal components
try:
    from .signal_generator import Signal, SignalType
except ImportError:
    # Fallback for standalone testing
    from signal_generator import Signal, SignalType

logger = logging.getLogger(__name__)

class ConflictResolutionStrategy(Enum):
    """冲突解决策略枚举"""
    MAJORITY_VOTING = "majority_voting"           # 多数投票
    WEIGHTED_VOTING = "weighted_voting"           # 加权投票
    CONSENSUS_BASED = "consensus_based"           # 基于共识
    HIERARCHICAL = "hierarchical"                 # 分层决策
    CONFIDENCE_WEIGHTED = "confidence_weighted"   # 置信度加权
    ML_BASED = "ml_based"                         # 机器学习
    ENSEMBLE = "ensemble"                         # 集成方法
    DYNAMIC_SELECTION = "dynamic_selection"       # 动态选择

class ConflictType(Enum):
    """冲突类型枚举"""
    BUY_SELL_CONFLICT = "buy_sell"               # 买卖冲突
    STRENGTH_CONFLICT = "strength"               # 强度冲突
    TIMING_CONFLICT = "timing"                   # 时间冲突
    DIRECTION_CONFLICT = "direction"             # 方向冲突
    CONFIDENCE_CONFLICT = "confidence"           # 置信度冲突

class ConflictSeverity(Enum):
    """冲突严重程度"""
    LOW = 1      # 低冲突
    MEDIUM = 2   # 中等冲突
    HIGH = 3     # 高冲突
    CRITICAL = 4 # 严重冲突

@dataclass
class SignalConflict:
    """信号冲突描述"""
    conflict_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    timestamp: datetime
    conflicting_signals: List[Signal]
    signal_groups: Dict[SignalType, List[Signal]]
    resolution_strategy: Optional[ConflictResolutionStrategy] = None
    resolution_result: Optional[SignalType] = None
    resolution_confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'conflict_id': self.conflict_id,
            'conflict_type': self.conflict_type.value,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'conflicting_signals': [s.to_dict() for s in self.conflicting_signals],
            'signal_groups': {k.value: [s.to_dict() for s in v] for k, v in self.signal_groups.items()},
            'resolution_strategy': self.resolution_strategy.value if self.resolution_strategy else None,
            'resolution_result': self.resolution_result.value if self.resolution_result else None,
            'resolution_confidence': self.resolution_confidence,
            'metadata': self.metadata
        }

@dataclass
class ResolutionHistory:
    """解决历史记录"""
    timestamp: datetime
    strategy: ConflictResolutionStrategy
    conflict_type: ConflictType
    success_rate: float
    resolution_quality: float
    market_context: Dict[str, Any]

@dataclass
class ConflictResolutionMetrics:
    """冲突解决性能指标"""
    total_conflicts: int = 0
    resolved_conflicts: int = 0
    resolution_success_rate: float = 0.0
    avg_resolution_time: float = 0.0
    strategy_performance: Dict[str, float] = field(default_factory=dict)
    conflict_type_distribution: Dict[str, int] = field(default_factory=dict)
    learning_effectiveness: float = 0.0

class ConflictDetectionEngine:
    """冲突检测引擎"""

    def __init__(self, conflict_threshold: float = 0.5):
        """
        初始化冲突检测引擎

        Args:
            conflict_threshold: 冲突检测阈值
        """
        self.conflict_threshold = conflict_threshold

    def detect_conflicts(self, signals: List[Signal]) -> List[SignalConflict]:
        """
        检测信号冲突

        Args:
            signals: 信号列表

        Returns:
            List[SignalConflict]: 检测到的冲突列表
        """
        conflicts = []

        if len(signals) < 2:
            return conflicts

        # 1. 检测买卖冲突
        buy_sell_conflicts = self._detect_buy_sell_conflicts(signals)
        conflicts.extend(buy_sell_conflicts)

        # 2. 检测强度冲突
        strength_conflicts = self._detect_strength_conflicts(signals)
        conflicts.extend(strength_conflicts)

        # 3. 检测方向冲突
        direction_conflicts = self._detect_direction_conflicts(signals)
        conflicts.extend(direction_conflicts)

        # 4. 检测置信度冲突
        confidence_conflicts = self._detect_confidence_conflicts(signals)
        conflicts.extend(confidence_conflicts)

        return conflicts

    def _detect_buy_sell_conflicts(self, signals: List[Signal]) -> List[SignalConflict]:
        """检测买卖冲突"""
        conflicts = []

        # 按信号类型分组
        signal_groups = defaultdict(list)
        for signal in signals:
            signal_groups[signal.signal_type].append(signal)

        # 检查是否存在相互冲突的信号
        buy_signals = signal_groups.get(SignalType.BUY, []) + signal_groups.get(SignalType.STRONG_BUY, [])
        sell_signals = signal_groups.get(SignalType.SELL, []) + signal_groups.get(SignalType.STRONG_SELL, [])

        if buy_signals and sell_signals:
            # 存在买卖冲突
            severity = self._calculate_conflict_severity(buy_signals, sell_signals)

            conflict = SignalConflict(
                conflict_id=f"buy_sell_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(conflicts)}",
                conflict_type=ConflictType.BUY_SELL_CONFLICT,
                severity=severity,
                timestamp=datetime.now(),
                conflicting_signals=buy_signals + sell_signals,
                signal_groups={k: v for k, v in signal_groups.items() if v},
                metadata={
                    'buy_count': len(buy_signals),
                    'sell_count': len(sell_signals),
                    'buy_avg_strength': np.mean([s.strength for s in buy_signals]),
                    'sell_avg_strength': np.mean([s.strength for s in sell_signals])
                }
            )
            conflicts.append(conflict)

        return conflicts

    def _detect_strength_conflicts(self, signals: List[Signal]) -> List[SignalConflict]:
        """检测强度冲突"""
        conflicts = []

        # 按信号类型分组
        signal_groups = defaultdict(list)
        for signal in signals:
            signal_groups[signal.signal_type].append(signal)

        # 检查同类型信号的强度差异
        for signal_type, type_signals in signal_groups.items():
            if len(type_signals) >= 2:
                strengths = [s.strength for s in type_signals]
                strength_std = np.std(strengths)
                strength_range = max(strengths) - min(strengths)

                # 如果强度差异超过阈值，认为是冲突
                if strength_range > self.conflict_threshold * 10:  # 强度范围阈值
                    severity = ConflictSeverity.MEDIUM if strength_range < 15 else ConflictSeverity.HIGH

                    conflict = SignalConflict(
                        conflict_id=f"strength_{signal_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(conflicts)}",
                        conflict_type=ConflictType.STRENGTH_CONFLICT,
                        severity=severity,
                        timestamp=datetime.now(),
                        conflicting_signals=type_signals,
                        signal_groups={signal_type: type_signals},
                        metadata={
                            'signal_type': signal_type.value,
                            'strength_range': strength_range,
                            'strength_std': strength_std,
                            'avg_strength': np.mean(strengths)
                        }
                    )
                    conflicts.append(conflict)

        return conflicts

    def _detect_direction_conflicts(self, signals: List[Signal]) -> List[SignalConflict]:
        """检测方向冲突"""
        conflicts = []

        # 按指标类型分组
        indicator_groups = defaultdict(list)
        for signal in signals:
            indicator_groups[signal.indicator_name].append(signal)

        # 检查同一指标的不同时间点的信号
        for indicator, indicator_signals in indicator_groups.items():
            if len(indicator_signals) >= 2:
                # 按时间排序
                indicator_signals.sort(key=lambda x: x.timestamp)

                # 检查连续信号的方向变化
                for i in range(len(indicator_signals) - 1):
                    current_signal = indicator_signals[i]
                    next_signal = indicator_signals[i + 1]

                    # 如果信号方向相反且时间间隔很短，认为是冲突
                    if (current_signal.signal_type.value * next_signal.signal_type.value < 0 and
                        (next_signal.timestamp - current_signal.timestamp).total_seconds() < 3600):  # 1小时内

                        severity = ConflictSeverity.MEDIUM
                        conflict = SignalConflict(
                            conflict_id=f"direction_{indicator}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(conflicts)}",
                            conflict_type=ConflictType.DIRECTION_CONFLICT,
                            severity=severity,
                            timestamp=datetime.now(),
                            conflicting_signals=[current_signal, next_signal],
                            signal_groups={
                                current_signal.signal_type: [current_signal],
                                next_signal.signal_type: [next_signal]
                            },
                            metadata={
                                'indicator_name': indicator,
                                'time_gap_seconds': (next_signal.timestamp - current_signal.timestamp).total_seconds(),
                                'signal_change': f"{current_signal.signal_type.value} -> {next_signal.signal_type.value}"
                            }
                        )
                        conflicts.append(conflict)

        return conflicts

    def _detect_confidence_conflicts(self, signals: List[Signal]) -> List[SignalConflict]:
        """检测置信度冲突"""
        conflicts = []

        # 按信号类型分组
        signal_groups = defaultdict(list)
        for signal in signals:
            signal_groups[signal.signal_type].append(signal)

        # 检查高置信度信号与低置信度信号的冲突
        for signal_type, type_signals in signal_groups.items():
            if len(type_signals) >= 2:
                confidences = [s.confidence for s in type_signals]
                confidence_range = max(confidences) - min(confidences)

                # 如果置信度差异很大，可能是冲突
                if confidence_range > self.conflict_threshold:
                    severity = ConflictSeverity.LOW if confidence_range < 0.7 else ConflictSeverity.MEDIUM

                    conflict = SignalConflict(
                        conflict_id=f"confidence_{signal_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(conflicts)}",
                        conflict_type=ConflictType.CONFIDENCE_CONFLICT,
                        severity=severity,
                        timestamp=datetime.now(),
                        conflicting_signals=type_signals,
                        signal_groups={signal_type: type_signals},
                        metadata={
                            'signal_type': signal_type.value,
                            'confidence_range': confidence_range,
                            'avg_confidence': np.mean(confidences),
                            'high_confidence_count': sum(1 for c in confidences if c > 0.7),
                            'low_confidence_count': sum(1 for c in confidences if c < 0.4)
                        }
                    )
                    conflicts.append(conflict)

        return conflicts

    def _calculate_conflict_severity(self, buy_signals: List[Signal], sell_signals: List[Signal]) -> ConflictSeverity:
        """计算冲突严重程度"""
        # 计算买卖信号的平均强度
        buy_avg_strength = np.mean([s.strength for s in buy_signals])
        sell_avg_strength = np.mean([s.strength for s in sell_signals])

        # 计算买卖信号的平均置信度
        buy_avg_confidence = np.mean([s.confidence for s in buy_signals])
        sell_avg_confidence = np.mean([s.confidence for s in sell_signals])

        # 综合评分
        strength_factor = (buy_avg_strength + sell_avg_strength) / 20  # 归一化到0-1
        confidence_factor = (buy_avg_confidence + sell_avg_confidence) / 2
        balance_factor = min(buy_avg_strength, sell_avg_strength) / max(buy_avg_strength, sell_avg_strength)

        overall_score = strength_factor * 0.4 + confidence_factor * 0.4 + balance_factor * 0.2

        if overall_score > 0.8:
            return ConflictSeverity.CRITICAL
        elif overall_score > 0.6:
            return ConflictSeverity.HIGH
        elif overall_score > 0.4:
            return ConflictSeverity.MEDIUM
        else:
            return ConflictSeverity.LOW

class ConflictResolver:
    """
    冲突解决器 - Phase 4.3核心实现

    功能：
    1. 冲突检测机制
    2. 多种冲突解决策略
    3. 冲突解决学习机制
    4. 冲突解决效果评估
    5. 冲突解决报告
    """

    def __init__(self,
                 default_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.WEIGHTED_VOTING,
                 enable_learning: bool = True,
                 cache_dir: Optional[str] = None):
        """
        初始化冲突解决器

        Args:
            default_strategy: 默认解决策略
            enable_learning: 启用学习机制
            cache_dir: 缓存目录
        """
        self.default_strategy = default_strategy
        self.enable_learning = enable_learning

        # 初始化冲突检测引擎
        self.detection_engine = ConflictDetectionEngine()

        # 解决历史记录
        self.resolution_history: List[ResolutionHistory] = []

        # 策略性能统计
        self.strategy_performance: Dict[ConflictResolutionStrategy, List[float]] = defaultdict(list)

        # 机器学习模型
        self.ml_model = None
        self.feature_scaler = None
        self.ml_training_data: List[Dict] = []

        # 缓存设置
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./cache/conflict_resolver")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 冲突解决指标
        self.metrics = ConflictResolutionMetrics()

        # 加载历史数据
        if enable_learning:
            self._load_learning_data()
            self._initialize_ml_model()

        logger.info(f"ConflictResolver initialized with strategy: {default_strategy.value}")

    def resolve_conflicts(self,
                         signals: List[Signal],
                         weights: Optional[Dict[str, float]] = None,
                         market_context: Optional[Dict[str, Any]] = None,
                         strategy: Optional[ConflictResolutionStrategy] = None) -> Tuple[Optional[Signal], List[SignalConflict]]:
        """
        解决信号冲突

        Args:
            signals: 输入信号列表
            weights: 指标权重
            market_context: 市场上下文
            strategy: 指定解决策略

        Returns:
            Tuple[Optional[Signal], List[SignalConflict]]: 解决后的信号和冲突列表
        """
        start_time = datetime.now()

        try:
            # 1. 检测冲突
            conflicts = self.detection_engine.detect_conflicts(signals)

            if not conflicts:
                # 没有冲突，使用加权融合
                resolved_signal = self._merge_signals_without_conflict(signals, weights)
                self.metrics.total_conflicts += 1
                self.metrics.resolved_conflicts += 1
                return resolved_signal, []

            self.metrics.total_conflicts += len(conflicts)

            # 2. 选择解决策略
            resolution_strategy = strategy or self._select_resolution_strategy(conflicts, market_context)

            # 3. 解决冲突
            resolved_signal = self._apply_resolution_strategy(
                signals, conflicts, weights, market_context, resolution_strategy
            )

            # 4. 记录解决历史
            resolution_time = (datetime.now() - start_time).total_seconds()
            self._record_resolution(conflicts, resolution_strategy, resolution_time, market_context)

            # 5. 更新学习数据
            if self.enable_learning and resolved_signal:
                self._update_learning_data(signals, conflicts, resolved_signal, market_context)

            logger.debug(f"Resolved {len(conflicts)} conflicts using {resolution_strategy.value}")
            return resolved_signal, conflicts

        except Exception as e:
            logger.error(f"Error resolving conflicts: {str(e)}")
            # 返回默认信号
            return self._create_default_signal(signals), []

    def _select_resolution_strategy(self,
                                  conflicts: List[SignalConflict],
                                  market_context: Optional[Dict[str, Any]] = None) -> ConflictResolutionStrategy:
        """动态选择解决策略"""
        # 基于历史性能选择策略
        strategy_scores = {}

        for strategy in ConflictResolutionStrategy:
            if strategy in self.strategy_performance and self.strategy_performance[strategy]:
                # 计算平均成功率
                avg_success = np.mean(self.strategy_performance[strategy])
                strategy_scores[strategy] = avg_success
            else:
                strategy_scores[strategy] = 0.5  # 默认分数

        # 根据冲突类型调整策略选择
        conflict_types = [c.conflict_type for c in conflicts]

        if ConflictType.BUY_SELL_CONFLICT in conflict_types:
            # 买卖冲突优先使用加权投票
            strategy_scores[ConflictResolutionStrategy.WEIGHTED_VOTING] += 0.2
            strategy_scores[ConflictResolutionStrategy.CONSENSUS_BASED] += 0.1

        if ConflictType.STRENGTH_CONFLICT in conflict_types:
            # 强度冲突优先使用置信度加权
            strategy_scores[ConflictResolutionStrategy.CONFIDENCE_WEIGHTED] += 0.2

        # 根据市场条件调整
        if market_context:
            market_volatility = market_context.get('volatility', 0.2)
            if market_volatility > 0.03:  # 高波动市场
                strategy_scores[ConflictResolutionStrategy.HIERARCHICAL] += 0.1
                strategy_scores[ConflictResolutionStrategy.ML_BASED] += 0.1

        # 选择得分最高的策略
        best_strategy = max(strategy_scores, key=strategy_scores.get)
        logger.debug(f"Selected resolution strategy: {best_strategy.value}")

        return best_strategy

    def _apply_resolution_strategy(self,
                                 signals: List[Signal],
                                 conflicts: List[SignalConflict],
                                 weights: Optional[Dict[str, float]],
                                 market_context: Optional[Dict[str, Any]],
                                 strategy: ConflictResolutionStrategy) -> Optional[Signal]:
        """应用指定的冲突解决策略"""
        if strategy == ConflictResolutionStrategy.MAJORITY_VOTING:
            return self._majority_voting_resolution(signals, conflicts)
        elif strategy == ConflictResolutionStrategy.WEIGHTED_VOTING:
            return self._weighted_voting_resolution(signals, conflicts, weights)
        elif strategy == ConflictResolutionStrategy.CONSENSUS_BASED:
            return self._consensus_based_resolution(signals, conflicts)
        elif strategy == ConflictResolutionStrategy.HIERARCHICAL:
            return self._hierarchical_resolution(signals, conflicts, market_context)
        elif strategy == ConflictResolutionStrategy.CONFIDENCE_WEIGHTED:
            return self._confidence_weighted_resolution(signals, conflicts)
        elif strategy == ConflictResolutionStrategy.ML_BASED:
            return self._ml_based_resolution(signals, conflicts, market_context)
        elif strategy == ConflictResolutionStrategy.ENSEMBLE:
            return self._ensemble_resolution(signals, conflicts, weights, market_context)
        else:
            # 默认使用加权投票
            return self._weighted_voting_resolution(signals, conflicts, weights)

    def _majority_voting_resolution(self,
                                  signals: List[Signal],
                                  conflicts: List[SignalConflict]) -> Optional[Signal]:
        """多数投票解决策略"""
        signal_votes = Counter([s.signal_type for s in signals])

        if not signal_votes:
            return None

        # 获取得票最多的信号类型
        majority_signal_type, vote_count = signal_votes.most_common(1)[0]

        # 如果票数没有过半，返回中性信号
        total_votes = len(signals)
        if vote_count < total_votes / 2:
            return self._create_hold_signal(signals)

        # 使用该类型信号中置信度最高的作为结果
        majority_signals = [s for s in signals if s.signal_type == majority_signal_type]
        best_signal = max(majority_signals, key=lambda s: s.confidence)

        # 更新冲突解决结果
        for conflict in conflicts:
            conflict.resolution_strategy = ConflictResolutionStrategy.MAJORITY_VOTING
            conflict.resolution_result = majority_signal_type
            conflict.resolution_confidence = vote_count / total_votes

        return best_signal

    def _weighted_voting_resolution(self,
                                  signals: List[Signal],
                                  conflicts: List[SignalConflict],
                                  weights: Optional[Dict[str, float]]) -> Optional[Signal]:
        """加权投票解决策略"""
        if not signals:
            return None

        # 计算每个信号类型的加权得分
        signal_scores = defaultdict(float)
        total_weight = 0

        for signal in signals:
            signal_weight = weights.get(signal.indicator_name, 1.0) if weights else 1.0
            weighted_score = signal_weight * signal.signal_value * signal.confidence

            signal_scores[signal.signal_type] += weighted_score
            total_weight += signal_weight

        if not signal_scores:
            return self._create_hold_signal(signals)

        # 选择得分最高的信号类型
        best_signal_type = max(signal_scores, key=signal_scores.get)

        # 找到该类型中综合评分最高的信号
        best_signals = [s for s in signals if s.signal_type == best_signal_type]
        best_signal = max(best_signals, key=lambda s: s.strength * s.confidence)

        # 更新冲突解决结果
        max_score = signal_scores[best_signal_type]
        total_score = sum(signal_scores.values())
        confidence = max_score / total_score if total_score > 0 else 0

        for conflict in conflicts:
            conflict.resolution_strategy = ConflictResolutionStrategy.WEIGHTED_VOTING
            conflict.resolution_result = best_signal_type
            conflict.resolution_confidence = confidence

        return best_signal

    def _consensus_based_resolution(self,
                                  signals: List[Signal],
                                  conflicts: List[SignalConflict]) -> Optional[Signal]:
        """基于共识的解决策略"""
        if not signals:
            return None

        # 计算信号的一致性
        signal_types = [s.signal_type for s in signals]
        type_counts = Counter(signal_types)

        # 计算一致性分数
        most_common_type, most_common_count = type_counts.most_common(1)[0]
        consensus_level = most_common_count / len(signals)

        # 如果一致性很低，返回中性信号
        if consensus_level < 0.6:
            return self._create_hold_signal(signals)

        # 检查信号的强度一致性
        strength_values = [s.strength for s in signals if s.signal_type == most_common_type]
        if strength_values:
            strength_consensus = 1 - (np.std(strength_values) / np.mean(strength_values)) if np.mean(strength_values) > 0 else 0
        else:
            strength_consensus = 0

        # 综合共识分数
        overall_consensus = consensus_level * 0.7 + strength_consensus * 0.3

        # 选择共识信号
        consensus_signals = [s for s in signals if s.signal_type == most_common_type]
        best_signal = max(consensus_signals, key=lambda s: s.confidence)

        # 更新冲突解决结果
        for conflict in conflicts:
            conflict.resolution_strategy = ConflictResolutionStrategy.CONSENSUS_BASED
            conflict.resolution_result = most_common_type
            conflict.resolution_confidence = overall_consensus
            conflict.metadata['consensus_level'] = consensus_level
            conflict.metadata['strength_consensus'] = strength_consensus

        return best_signal

    def _hierarchical_resolution(self,
                               signals: List[Signal],
                               conflicts: List[SignalConflict],
                               market_context: Optional[Dict[str, Any]]) -> Optional[Signal]:
        """分层决策解决策略"""
        if not signals:
            return None

        # 定义信号优先级层次
        priority_order = [
            SignalType.STRONG_BUY,
            SignalType.STRONG_SELL,
            SignalType.BUY,
            SignalType.SELL,
            SignalType.WEAK_BUY,
            SignalType.WEAK_SELL,
            SignalType.HOLD
        ]

        # 根据市场条件调整优先级
        if market_context:
            market_regime = market_context.get('regime', 'neutral')
            if market_regime == 'bull':
                # 牛市中买入信号优先级提高
                priority_order = [
                    SignalType.STRONG_BUY,
                    SignalType.BUY,
                    SignalType.WEAK_BUY,
                    SignalType.STRONG_SELL,
                    SignalType.SELL,
                    SignalType.WEAK_SELL,
                    SignalType.HOLD
                ]
            elif market_regime == 'bear':
                # 熊市中卖出信号优先级提高
                priority_order = [
                    SignalType.STRONG_SELL,
                    SignalType.SELL,
                    SignalType.WEAK_SELL,
                    SignalType.STRONG_BUY,
                    SignalType.BUY,
                    SignalType.WEAK_BUY,
                    SignalType.HOLD
                ]

        # 按优先级选择信号
        for signal_type in priority_order:
            type_signals = [s for s in signals if s.signal_type == signal_type]
            if type_signals:
                # 选择该类型中置信度最高的信号
                best_signal = max(type_signals, key=lambda s: s.confidence)

                # 检查是否有足够的高置信度信号
                high_confidence_signals = [s for s in type_signals if s.confidence > 0.7]
                if high_confidence_signals:
                    best_signal = max(high_confidence_signals, key=lambda s: s.strength)

                # 更新冲突解决结果
                for conflict in conflicts:
                    conflict.resolution_strategy = ConflictResolutionStrategy.HIERARCHICAL
                    conflict.resolution_result = signal_type
                    conflict.resolution_confidence = best_signal.confidence
                    conflict.metadata['priority_level'] = priority_order.index(signal_type)

                return best_signal

        # 如果没有找到任何信号，返回中性信号
        return self._create_hold_signal(signals)

    def _confidence_weighted_resolution(self,
                                      signals: List[Signal],
                                      conflicts: List[SignalConflict]) -> Optional[Signal]:
        """置信度加权解决策略"""
        if not signals:
            return None

        # 按信号类型分组，计算置信度加权的平均强度
        type_groups = defaultdict(list)
        for signal in signals:
            type_groups[signal.signal_type].append(signal)

        # 计算每种信号类型的加权评分
        type_scores = {}
        for signal_type, type_signals in type_groups.items():
            # 置信度加权平均强度
            weighted_strength = sum(s.strength * s.confidence for s in type_signals)
            total_confidence = sum(s.confidence for s in type_signals)
            avg_strength = weighted_strength / total_confidence if total_confidence > 0 else 0

            # 平均置信度
            avg_confidence = total_confidence / len(type_signals)

            # 综合评分
            type_scores[signal_type] = avg_strength * avg_confidence

        if not type_scores:
            return self._create_hold_signal(signals)

        # 选择评分最高的信号类型
        best_signal_type = max(type_scores, key=type_scores.get)

        # 选择该类型中综合质量最高的信号
        best_signals = [s for s in signals if s.signal_type == best_signal_type]
        best_signal = max(best_signals, key=lambda s: s.strength * s.confidence)

        # 更新冲突解决结果
        max_score = type_scores[best_signal_type]
        total_score = sum(type_scores.values())
        confidence = max_score / total_score if total_score > 0 else 0

        for conflict in conflicts:
            conflict.resolution_strategy = ConflictResolutionStrategy.CONFIDENCE_WEIGHTED
            conflict.resolution_result = best_signal_type
            conflict.resolution_confidence = confidence

        return best_signal

    def _ml_based_resolution(self,
                           signals: List[Signal],
                           conflicts: List[SignalConflict],
                           market_context: Optional[Dict[str, Any]]) -> Optional[Signal]:
        """基于机器学习的解决策略"""
        if not signals or self.ml_model is None:
            return self._weighted_voting_resolution(signals, conflicts, None)

        try:
            # 提取特征
            features = self._extract_ml_features(signals, conflicts, market_context)

            # 预测最佳信号类型
            if features:
                predicted_type = self.ml_model.predict([features])[0]
                predicted_prob = self.ml_model.predict_proba([features])[0]

                # 找到对应类型的信号
                type_mapping = {
                    0: SignalType.BUY,
                    1: SignalType.SELL,
                    2: SignalType.HOLD
                }

                predicted_signal_type = type_mapping.get(int(predicted_type), SignalType.HOLD)
                max_probability = max(predicted_prob) if len(predicted_prob) > 0 else 0.5

                # 选择该类型中质量最高的信号
                candidate_signals = [s for s in signals if s.signal_type == predicted_signal_type]
                if candidate_signals:
                    best_signal = max(candidate_signals, key=lambda s: s.strength * s.confidence)

                    # 更新冲突解决结果
                    for conflict in conflicts:
                        conflict.resolution_strategy = ConflictResolutionStrategy.ML_BASED
                        conflict.resolution_result = predicted_signal_type
                        conflict.resolution_confidence = max_probability

                    return best_signal

        except Exception as e:
            logger.warning(f"ML-based resolution failed: {str(e)}")

        # 回退到加权投票
        return self._weighted_voting_resolution(signals, conflicts, None)

    def _ensemble_resolution(self,
                           signals: List[Signal],
                           conflicts: List[SignalConflict],
                           weights: Optional[Dict[str, float]],
                           market_context: Optional[Dict[str, Any]]) -> Optional[Signal]:
        """集成方法解决策略"""
        # 使用多种策略，然后集成结果
        strategies = [
            ConflictResolutionStrategy.WEIGHTED_VOTING,
            ConflictResolutionStrategy.CONSENSUS_BASED,
            ConflictResolutionStrategy.CONFIDENCE_WEIGHTED
        ]

        strategy_results = {}
        for strategy in strategies:
            result = self._apply_resolution_strategy(signals, conflicts, weights, market_context, strategy)
            strategy_results[strategy] = result

        # 集成策略结果
        if strategy_results:
            # 计算每种结果的出现次数和质量
            signal_votes = Counter()
            signal_qualities = defaultdict(list)

            for strategy, signal in strategy_results.items():
                if signal:
                    signal_votes[signal.signal_type] += 1
                    signal_qualities[signal.signal_type].append(signal.confidence * signal.strength)

            # 选择投票最多且质量最高的信号类型
            if signal_votes:
                best_signal_type = max(signal_votes, key=lambda x: (signal_votes[x], np.mean(signal_qualities[x])))

                # 选择对应类型的最佳信号
                best_signals = [s for s in signals if s.signal_type == best_signal_type]
                if best_signals:
                    best_signal = max(best_signals, key=lambda s: s.confidence * s.strength)

                    # 更新冲突解决结果
                    ensemble_confidence = signal_votes[best_signal_type] / len(strategies)
                    for conflict in conflicts:
                        conflict.resolution_strategy = ConflictResolutionStrategy.ENSEMBLE
                        conflict.resolution_result = best_signal_type
                        conflict.resolution_confidence = ensemble_confidence
                        conflict.metadata['strategy_votes'] = dict(signal_votes)

                    return best_signal

        return self._create_hold_signal(signals)

    def _merge_signals_without_conflict(self,
                                      signals: List[Signal],
                                      weights: Optional[Dict[str, float]]) -> Optional[Signal]:
        """无冲突时合并信号"""
        if not signals:
            return None

        # 加权合并所有信号
        total_weight = 0
        weighted_value = 0
        weighted_confidence = 0
        weighted_strength = 0

        for signal in signals:
            signal_weight = weights.get(signal.indicator_name, 1.0) if weights else 1.0
            total_weight += signal_weight
            weighted_value += signal.signal_value * signal_weight
            weighted_confidence += signal.confidence * signal_weight
            weighted_strength += signal.strength * signal_weight

        if total_weight == 0:
            return None

        # 计算合并后的信号值
        final_value = weighted_value / total_weight
        final_confidence = weighted_confidence / total_weight
        final_strength = weighted_strength / total_weight

        # 确定信号类型
        if abs(final_value) < 0.1:
            final_signal_type = SignalType.HOLD
        elif final_value > 1.5:
            final_signal_type = SignalType.STRONG_BUY
        elif final_value > 0.5:
            final_signal_type = SignalType.BUY
        elif final_value < -1.5:
            final_signal_type = SignalType.STRONG_SELL
        elif final_value < -0.5:
            final_signal_type = SignalType.SELL
        else:
            final_signal_type = SignalType.HOLD

        # 创建合并信号
        merged_signal = Signal(
            timestamp=datetime.now(),
            indicator_name="MERGED",
            signal_type=final_signal_type,
            signal_value=final_value,
            strength=final_strength,
            confidence=final_confidence,
            raw_indicator_value=final_value,
            parameters={'merge_method': 'weighted_average'},
            metadata={
                'source_signals': len(signals),
                'merge_strategy': 'weighted_average'
            }
        )

        return merged_signal

    def _create_hold_signal(self, signals: List[Signal]) -> Optional[Signal]:
        """创建中性信号"""
        if not signals:
            return None

        # 使用输入信号的平均置信度和强度
        avg_confidence = np.mean([s.confidence for s in signals])
        avg_strength = np.mean([s.strength for s in signals])

        hold_signal = Signal(
            timestamp=datetime.now(),
            indicator_name="HOLD",
            signal_type=SignalType.HOLD,
            signal_value=0.0,
            strength=avg_strength,
            confidence=avg_confidence,
            raw_indicator_value=0.0,
            parameters={'reason': 'conflict_resolution'},
            metadata={'source_signals': len(signals)}
        )

        return hold_signal

    def _create_default_signal(self, signals: List[Signal]) -> Optional[Signal]:
        """创建默认信号"""
        if not signals:
            return None

        # 选择置信度最高的信号作为默认
        best_signal = max(signals, key=lambda s: s.confidence)
        return best_signal

    def _extract_ml_features(self,
                           signals: List[Signal],
                           conflicts: List[SignalConflict],
                           market_context: Optional[Dict[str, Any]]) -> Optional[List[float]]:
        """提取机器学习特征"""
        if not signals:
            return None

        features = []

        # 1. 信号统计特征
        buy_count = sum(1 for s in signals if s.signal_type.value > 0)
        sell_count = sum(1 for s in signals if s.signal_type.value < 0)
        hold_count = len(signals) - buy_count - sell_count

        features.extend([
            buy_count / len(signals),  # 买入信号比例
            sell_count / len(signals), # 卖出信号比例
            hold_count / len(signals)  # 中性信号比例
        ])

        # 2. 强度特征
        strengths = [s.strength for s in signals]
        features.extend([
            np.mean(strengths),   # 平均强度
            np.std(strengths),    # 强度标准差
            np.max(strengths),    # 最大强度
            np.min(strengths)     # 最小强度
        ])

        # 3. 置信度特征
        confidences = [s.confidence for s in signals]
        features.extend([
            np.mean(confidences),  # 平均置信度
            np.std(confidences),   # 置信度标准差
            np.max(confidences),   # 最大置信度
        ])

        # 4. 冲突特征
        features.extend([
            len(conflicts),                    # 冲突数量
            sum(c.severity.value for c in conflicts) / max(1, len(conflicts)),  # 平均冲突严重程度
        ])

        # 5. 市场上下文特征
        if market_context:
            features.extend([
                market_context.get('volatility', 0.2),     # 市场波动率
                1 if market_context.get('regime') == 'bull' else 0,  # 牛市标识
                1 if market_context.get('regime') == 'bear' else 0,  # 熊市标识
            ])
        else:
            features.extend([0.2, 0, 0])

        return features

    def _record_resolution(self,
                         conflicts: List[SignalConflict],
                         strategy: ConflictResolutionStrategy,
                         resolution_time: float,
                         market_context: Optional[Dict[str, Any]]):
        """记录解决历史"""
        self.resolution_history.append(ResolutionHistory(
            timestamp=datetime.now(),
            strategy=strategy,
            conflict_type=conflicts[0].conflict_type if conflicts else ConflictType.BUY_SELL_CONFLICT,
            success_rate=1.0,  # 假设成功，后续可以通过实际结果更新
            resolution_quality=1.0 / resolution_time,  # 解决速度作为质量指标
            market_context=market_context or {}
        ))

        # 更新策略性能
        self.strategy_performance[strategy].append(1.0)

        # 更新指标
        self.metrics.resolved_conflicts += len(conflicts)
        self.metrics.avg_resolution_time = (
            (self.metrics.avg_resolution_time * (self.metrics.resolved_conflicts - len(conflicts)) + resolution_time) /
            self.metrics.resolved_conflicts
        )

    def _update_learning_data(self,
                            signals: List[Signal],
                            conflicts: List[SignalConflict],
                            resolved_signal: Signal,
                            market_context: Optional[Dict[str, Any]]):
        """更新学习数据"""
        if not self.enable_learning:
            return

        # 准备训练数据
        features = self._extract_ml_features(signals, conflicts, market_context)
        if features:
            # 标签编码
            label_map = {
                SignalType.BUY: 0,
                SignalType.SELL: 1,
                SignalType.HOLD: 2,
                SignalType.STRONG_BUY: 0,
                SignalType.STRONG_SELL: 1,
                SignalType.WEAK_BUY: 0,
                SignalType.WEAK_SELL: 1
            }

            label = label_map.get(resolved_signal.signal_type, 2)

            self.ml_training_data.append({
                'features': features,
                'label': label,
                'timestamp': datetime.now(),
                'confidence': resolved_signal.confidence
            })

            # 限制训练数据大小
            if len(self.ml_training_data) > 1000:
                self.ml_training_data = self.ml_training_data[-1000:]

            # 定期重新训练模型
            if len(self.ml_training_data) % 50 == 0:
                self._retrain_ml_model()

    def _initialize_ml_model(self):
        """初始化机器学习模型"""
        if not SKLEARN_AVAILABLE:
            logger.warning("Scikit-learn not available, ML-based resolution disabled")
            return

        try:
            self.ml_model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=10
            )
            self.feature_scaler = StandardScaler()

            # 如果有历史数据，训练模型
            if len(self.ml_training_data) >= 10:
                self._retrain_ml_model()

        except Exception as e:
            logger.warning(f"Failed to initialize ML model: {str(e)}")

    def _retrain_ml_model(self):
        """重新训练机器学习模型"""
        if not SKLEARN_AVAILABLE or len(self.ml_training_data) < 10:
            return

        try:
            # 准备训练数据
            X = np.array([item['features'] for item in self.ml_training_data])
            y = np.array([item['label'] for item in self.ml_training_data])

            # 标准化特征
            X_scaled = self.feature_scaler.fit_transform(X)

            # 训练模型
            self.ml_model.fit(X_scaled, y)

            logger.debug(f"ML model retrained with {len(self.ml_training_data)} samples")

        except Exception as e:
            logger.warning(f"Failed to retrain ML model: {str(e)}")

    def _load_learning_data(self):
        """加载学习数据"""
        if not SKLEARN_AVAILABLE:
            logger.debug("Sklearn not available, skipping ML data loading")
            return

        try:
            model_file = self.cache_dir / "ml_model.pkl"
            scaler_file = self.cache_dir / "feature_scaler.pkl"
            data_file = self.cache_dir / "training_data.json"

            if model_file.exists():
                with open(model_file, 'rb') as f:
                    self.ml_model = pickle.load(f)

            if scaler_file.exists():
                with open(scaler_file, 'rb') as f:
                    self.feature_scaler = pickle.load(f)

            if data_file.exists():
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.ml_training_data = data.get('training_data', [])

                # 转换时间戳
                for item in self.ml_training_data:
                    item['timestamp'] = datetime.fromisoformat(item['timestamp'])

            logger.debug(f"Loaded learning data: {len(self.ml_training_data)} samples")

        except Exception as e:
            logger.warning(f"Failed to load learning data: {str(e)}")

    def _save_learning_data(self):
        """保存学习数据"""
        if not SKLEARN_AVAILABLE:
            logger.debug("Sklearn not available, skipping ML data saving")
            return

        try:
            model_file = self.cache_dir / "ml_model.pkl"
            scaler_file = self.cache_dir / "feature_scaler.pkl"
            data_file = self.cache_dir / "training_data.json"

            if self.ml_model:
                with open(model_file, 'wb') as f:
                    pickle.dump(self.ml_model, f)

            if self.feature_scaler:
                with open(scaler_file, 'wb') as f:
                    pickle.dump(self.feature_scaler, f)

            # 保存训练数据
            serializable_data = []
            for item in self.ml_training_data:
                serializable_item = item.copy()
                serializable_item['timestamp'] = item['timestamp'].isoformat()
                serializable_data.append(serializable_item)

            data = {
                'training_data': serializable_data,
                'last_saved': datetime.now().isoformat()
            }

            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug("Learning data saved successfully")

        except Exception as e:
            logger.error(f"Failed to save learning data: {str(e)}")

    def get_resolution_metrics(self) -> ConflictResolutionMetrics:
        """获取冲突解决性能指标"""
        # 更新成功率
        if self.metrics.total_conflicts > 0:
            self.metrics.resolution_success_rate = self.metrics.resolved_conflicts / self.metrics.total_conflicts

        # 更新策略性能
        self.metrics.strategy_performance = {}
        for strategy, performances in self.strategy_performance.items():
            if performances:
                self.metrics.strategy_performance[strategy.value] = np.mean(performances)

        # 更新冲突类型分布
        if self.resolution_history:
            type_counts = Counter([h.conflict_type.value for h in self.resolution_history])
            self.metrics.conflict_type_distribution = dict(type_counts)

        # 计算学习效果
        if self.ml_training_data:
            self.metrics.learning_effectiveness = min(1.0, len(self.ml_training_data) / 100.0)

        return self.metrics

    def generate_conflict_report(self) -> Dict[str, Any]:
        """生成冲突解决报告"""
        metrics = self.get_resolution_metrics()

        report = {
            'summary': {
                'total_conflicts': metrics.total_conflicts,
                'resolved_conflicts': metrics.resolved_conflicts,
                'resolution_success_rate': metrics.resolution_success_rate,
                'avg_resolution_time': metrics.avg_resolution_time,
                'learning_effectiveness': metrics.learning_effectiveness
            },
            'strategy_performance': metrics.strategy_performance,
            'conflict_type_distribution': metrics.conflict_type_distribution,
            'configuration': {
                'default_strategy': self.default_strategy.value,
                'learning_enabled': self.enable_learning,
                'cache_directory': str(self.cache_dir)
            },
            'recent_resolutions': [
                {
                    'timestamp': h.timestamp.isoformat(),
                    'strategy': h.strategy.value,
                    'conflict_type': h.conflict_type.value,
                    'success_rate': h.success_rate,
                    'resolution_quality': h.resolution_quality
                }
                for h in self.resolution_history[-10:]  # 最近10条记录
            ]
        }

        return report

    def export_conflict_data(self, format: str = 'dict') -> Union[Dict, pd.DataFrame]:
        """
        导出冲突数据

        Args:
            format: 导出格式 ('dict', 'dataframe')

        Returns:
            冲突数据
        """
        if format == 'dict':
            return {
                'resolution_history': [
                    {
                        'timestamp': h.timestamp.isoformat(),
                        'strategy': h.strategy.value,
                        'conflict_type': h.conflict_type.value,
                        'success_rate': h.success_rate,
                        'resolution_quality': h.resolution_quality,
                        'market_context': h.market_context
                    }
                    for h in self.resolution_history
                ],
                'strategy_performance': {
                    k.value: v for k, v in self.strategy_performance.items()
                },
                'metrics': self.get_resolution_metrics().__dict__
            }
        elif format == 'dataframe':
            data = []
            for h in self.resolution_history:
                data.append({
                    'timestamp': h.timestamp,
                    'strategy': h.strategy.value,
                    'conflict_type': h.conflict_type.value,
                    'success_rate': h.success_rate,
                    'resolution_quality': h.resolution_quality
                })
            return pd.DataFrame(data)
        else:
            raise ValueError(f"Unknown export format: {format}")

    def reset_learning(self):
        """重置学习数据"""
        self.ml_training_data.clear()
        self.ml_model = None
        self.feature_scaler = None
        self.resolution_history.clear()
        self.strategy_performance.clear()

        # 删除缓存文件
        for file_path in self.cache_dir.glob("*.pkl"):
            file_path.unlink()

        logger.info("Learning data reset")

    def __del__(self):
        """析构函数，保存数据"""
        if self.enable_learning:
            self._save_learning_data()
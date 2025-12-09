"""
Dynamic Weight Manager - Phase 4.2 Implementation
多指标权重管理器 - Phase 4.2实施

This module implements intelligent weight management for multiple indicators,
including static weight configuration, dynamic adjustment algorithms,
weight optimization, and performance assessment.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
from pathlib import Path
import warnings
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class WeightAdjustmentStrategy(Enum):
    """权重调整策略枚举"""
    STATIC = "static"                    # 静态权重
    PERFORMANCE_BASED = "performance"    # 基于性能的动态调整
    MARKET_REGIME = "market_regime"      # 基于市场状态的调整
    VOLATILITY_ADAPTIVE = "volatility"   # 基于波动率的自适应调整
    CORRELATION_AWARE = "correlation"    # 基于相关性的调整
    ML_OPTIMIZED = "ml_optimized"       # 机器学习优化
    HYBRID = "hybrid"                    # 混合策略

class MarketRegime(Enum):
    """市场状态枚举"""
    BULL_MARKET = "bull"        # 牛市
    BEAR_MARKET = "bear"        # 熊市
    SIDEWAYS = "sideways"       # 震荡市
    HIGH_VOLATILITY = "high_vol" # 高波动
    LOW_VOLATILITY = "low_vol"   # 低波动
    CRISIS = "crisis"           # 危机状态

@dataclass
class IndicatorWeight:
    """单个指标权重配置"""
    indicator_name: str
    base_weight: float          # 基础权重 (0-1)
    current_weight: float       # 当前权重 (0-1)
    min_weight: float           # 最小权重 (0-1)
    max_weight: float           # 最大权重 (0-1)
    adjustment_factor: float    # 调整因子
    last_adjusted: datetime     # 最后调整时间
    performance_score: float    # 性能评分
    volatility_score: float     # 波动率评分
    correlation_penalty: float  # 相关性惩罚
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'indicator_name': self.indicator_name,
            'base_weight': self.base_weight,
            'current_weight': self.current_weight,
            'min_weight': self.min_weight,
            'max_weight': self.max_weight,
            'adjustment_factor': self.adjustment_factor,
            'last_adjusted': self.last_adjusted.isoformat(),
            'performance_score': self.performance_score,
            'volatility_score': self.volatility_score,
            'correlation_penalty': self.correlation_penalty,
            'metadata': self.metadata
        }

@dataclass
class WeightConstraints:
    """权重约束条件"""
    total_weight_sum: float = 1.0          # 权重总和
    min_individual_weight: float = 0.05    # 最小单个权重
    max_individual_weight: float = 0.4     # 最大单个权重
    max_weight_change_rate: float = 0.2    # 最大权重变化率
    rebalance_threshold: float = 0.1       # 重新平衡阈值
    sector_constraints: Dict[str, float] = field(default_factory=dict)  # 板块约束

@dataclass
class WeightPerformanceMetrics:
    """权重性能指标"""
    sharpe_ratio: float = 0.0
    total_return: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    stability_score: float = 0.0
    correlation_adjusted_return: float = 0.0
    effective_weight_ratio: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

class WeightAdjustmentAlgorithm(ABC):
    """权重调整算法抽象基类"""

    @abstractmethod
    def calculate_adjustment(self,
                           current_weights: Dict[str, float],
                           performance_data: Dict[str, Any],
                           market_data: Dict[str, Any]) -> Dict[str, float]:
        """
        计算权重调整

        Args:
            current_weights: 当前权重
            performance_data: 性能数据
            market_data: 市场数据

        Returns:
            Dict[str, float]: 调整后的权重
        """
        pass

class PerformanceBasedAdjustment(WeightAdjustmentAlgorithm):
    """基于性能的权重调整算法"""

    def __init__(self,
                 performance_window: int = 30,
                 adjustment_rate: float = 0.1,
                 performance_metric: str = 'sharpe_ratio'):
        """
        初始化性能权重调整器

        Args:
            performance_window: 性能评估窗口
            adjustment_rate: 调整速率
            performance_metric: 使用的性能指标
        """
        self.performance_window = performance_window
        self.adjustment_rate = adjustment_rate
        self.performance_metric = performance_metric

    def calculate_adjustment(self,
                           current_weights: Dict[str, float],
                           performance_data: Dict[str, Any],
                           market_data: Dict[str, Any]) -> Dict[str, float]:
        """
        基于性能计算权重调整
        """
        adjusted_weights = current_weights.copy()
        indicator_performance = performance_data.get('indicator_performance', {})

        if not indicator_performance:
            return adjusted_weights

        # 计算性能排名
        performance_scores = {}
        for indicator, metrics in indicator_performance.items():
            if indicator in current_weights:
                score = self._calculate_performance_score(metrics)
                performance_scores[indicator] = score

        if not performance_scores:
            return adjusted_weights

        # 标准化性能分数
        scores = np.array(list(performance_scores.values()))
        if len(scores) > 1 and scores.std() > 0:
            normalized_scores = (scores - scores.min()) / (scores.max() - scores.min())
        else:
            normalized_scores = np.ones(len(scores)) * 0.5

        # 调整权重
        total_adjustment = 0
        for i, (indicator, current_weight) in enumerate(current_weights.items()):
            if indicator in performance_scores:
                # 计算目标权重
                target_weight = normalized_scores[i] * self.adjustment_rate + \
                               current_weight * (1 - self.adjustment_rate)

                # 应用调整
                adjustment = target_weight - current_weight
                adjusted_weights[indicator] = target_weight
                total_adjustment += abs(adjustment)

        logger.debug(f"Performance-based adjustment: total change = {total_adjustment:.3f}")
        return adjusted_weights

    def _calculate_performance_score(self, metrics: Dict[str, Any]) -> float:
        """计算综合性能分数"""
        score = 0.0
        count = 0

        # Sharpe比率 (权重: 30%)
        if 'sharpe_ratio' in metrics:
            sharpe = metrics['sharpe_ratio']
            score += max(0, min(3, sharpe)) / 3 * 0.3
            count += 0.3

        # 总回报 (权重: 25%)
        if 'total_return' in metrics:
            returns = metrics['total_return']
            score += max(0, min(1, returns)) * 0.25
            count += 0.25

        # 胜率 (权重: 20%)
        if 'win_rate' in metrics:
            win_rate = metrics['win_rate']
            score += win_rate * 0.2
            count += 0.2

        # 稳定性 (权重: 15%)
        if 'stability_score' in metrics:
            stability = metrics['stability_score']
            score += stability * 0.15
            count += 0.15

        # 最大回撤 (权重: 10%)
        if 'max_drawdown' in metrics:
            max_dd = abs(metrics['max_drawdown'])
            score += max(0, 1 - max_dd * 5) * 0.1  # 假设20%回撤为0分
            count += 0.1

        return score / max(count, 0.1)

class MarketRegimeAdjustment(WeightAdjustmentAlgorithm):
    """基于市场状态的权重调整算法"""

    def __init__(self,
                 regime_weights: Dict[MarketRegime, Dict[str, float]],
                 regime_detection_window: int = 20):
        """
        初始化市场状态权重调整器

        Args:
            regime_weights: 不同市场状态下的最优权重配置
            regime_detection_window: 市场状态检测窗口
        """
        self.regime_weights = regime_weights
        self.regime_detection_window = regime_detection_window
        self.current_regime = MarketRegime.SIDEWAYS
        self.regime_history: List[Tuple[datetime, MarketRegime]] = []

    def calculate_adjustment(self,
                           current_weights: Dict[str, float],
                           performance_data: Dict[str, Any],
                           market_data: Dict[str, Any]) -> Dict[str, float]:
        """
        基于市场状态计算权重调整
        """
        # 检测当前市场状态
        new_regime = self._detect_market_regime(market_data)

        # 如果市场状态变化，调整权重
        if new_regime != self.current_regime:
            logger.info(f"Market regime changed from {self.current_regime.value} to {new_regime.value}")
            self.current_regime = new_regime
            self.regime_history.append((datetime.now(), new_regime))

            # 获取目标权重
            target_weights = self.regime_weights.get(new_regime, {})
            if target_weights:
                return self._blend_weights(current_weights, target_weights, blend_factor=0.7)

        return current_weights.copy()

    def _detect_market_regime(self, market_data: Dict[str, Any]) -> MarketRegime:
        """检测当前市场状态"""
        price_data = market_data.get('price_data')
        if price_data is None or len(price_data) < self.regime_detection_window:
            return MarketRegime.SIDEWAYS

        recent_prices = price_data.tail(self.regime_detection_window)
        returns = recent_prices.pct_change().dropna()

        if len(returns) == 0:
            return MarketRegime.SIDEWAYS

        # 计算指标
        avg_return = returns.mean()
        volatility = returns.std()
        trend_strength = abs(avg_return) / volatility if volatility > 0 else 0

        # 检测危机状态
        if volatility > 0.05 and avg_return < -0.02:
            return MarketRegime.CRISIS
        # 检测牛市
        elif trend_strength > 0.5 and avg_return > 0.01:
            return MarketRegime.BULL_MARKET
        # 检测熊市
        elif trend_strength > 0.5 and avg_return < -0.01:
            return MarketRegime.BEAR_MARKET
        # 检测高波动
        elif volatility > 0.03:
            return MarketRegime.HIGH_VOLATILITY
        # 检测低波动
        elif volatility < 0.01:
            return MarketRegime.LOW_VOLATILITY
        else:
            return MarketRegime.SIDEWAYS

    def _blend_weights(self,
                      current_weights: Dict[str, float],
                      target_weights: Dict[str, float],
                      blend_factor: float) -> Dict[str, float]:
        """混合当前权重和目标权重"""
        blended_weights = {}

        for indicator in current_weights:
            current_weight = current_weights[indicator]
            target_weight = target_weights.get(indicator, current_weight)
            blended_weights[indicator] = (1 - blend_factor) * current_weight + blend_factor * target_weight

        return blended_weights

class DynamicWeightManager:
    """
    动态权重管理器 - Phase 4.2核心实现

    功能：
    1. 静态权重配置支持
    2. 动态权重调整算法
    3. 权重优化功能
    4. 权重约束条件管理
    5. 权重性能评估
    """

    def __init__(self,
                 initial_weights: Dict[str, float],
                 constraints: Optional[WeightConstraints] = None,
                 adjustment_strategy: WeightAdjustmentStrategy = WeightAdjustmentStrategy.HYBRID,
                 enable_optimization: bool = True,
                 cache_dir: Optional[str] = None):
        """
        初始化动态权重管理器

        Args:
            initial_weights: 初始权重配置
            constraints: 权重约束条件
            adjustment_strategy: 权重调整策略
            enable_optimization: 启用权重优化
            cache_dir: 缓存目录
        """
        self.initial_weights = initial_weights.copy()
        self.current_weights = initial_weights.copy()
        self.constraints = constraints or WeightConstraints()
        self.adjustment_strategy = adjustment_strategy
        self.enable_optimization = enable_optimization

        # 初始化指标权重对象
        self.indicator_weights: Dict[str, IndicatorWeight] = {}
        for indicator, weight in initial_weights.items():
            self.indicator_weights[indicator] = IndicatorWeight(
                indicator_name=indicator,
                base_weight=weight,
                current_weight=weight,
                min_weight=self.constraints.min_individual_weight,
                max_weight=min(self.constraints.max_individual_weight, weight * 2),
                adjustment_factor=1.0,
                last_adjusted=datetime.now(),
                performance_score=0.5,
                volatility_score=0.5,
                correlation_penalty=0.0
            )

        # 初始化调整算法
        self.adjustment_algorithms: Dict[WeightAdjustmentStrategy, WeightAdjustmentAlgorithm] = {}
        self._initialize_algorithms()

        # 权重历史记录
        self.weight_history: List[Tuple[datetime, Dict[str, float]]] = []

        # 性能指标
        self.performance_metrics: Dict[str, WeightPerformanceMetrics] = {}

        # 缓存设置
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./cache/weight_manager")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 加载历史数据
        self._load_historical_weights()

        logger.info(f"DynamicWeightManager initialized with {len(initial_weights)} indicators")

    def _initialize_algorithms(self):
        """初始化权重调整算法"""
        # 性能权重调整
        self.adjustment_algorithms[WeightAdjustmentStrategy.PERFORMANCE_BASED] = \
            PerformanceBasedAdjustment()

        # 市场状态权重调整 - 需要提供默认配置
        default_regime_weights = {
            MarketRegime.BULL_MARKET: self.current_weights.copy(),
            MarketRegime.BEAR_MARKET: {k: v * 0.8 for k, v in self.current_weights.items()},
            MarketRegime.SIDEWAYS: self.current_weights.copy(),
            MarketRegime.HIGH_VOLATILITY: {k: v * 0.6 for k, v in self.current_weights.items()},
            MarketRegime.LOW_VOLATILITY: self.current_weights.copy(),
            MarketRegime.CRISIS: {k: v * 0.4 for k, v in self.current_weights.items()}
        }
        self.adjustment_algorithms[WeightAdjustmentStrategy.MARKET_REGIME] = \
            MarketRegimeAdjustment(default_regime_weights)

    def update_weights(self,
                      performance_data: Dict[str, Any],
                      market_data: Dict[str, Any],
                      force_rebalance: bool = False) -> Dict[str, float]:
        """
        更新权重

        Args:
            performance_data: 性能数据
            market_data: 市场数据
            force_rebalance: 强制重新平衡

        Returns:
            Dict[str, float]: 更新后的权重
        """
        try:
            old_weights = self.current_weights.copy()

            # 应用权重调整策略
            if self.adjustment_strategy == WeightAdjustmentStrategy.STATIC:
                # 静态权重，不调整
                new_weights = old_weights.copy()
            elif self.adjustment_strategy == WeightAdjustmentStrategy.HYBRID:
                # 混合策略
                new_weights = self._apply_hybrid_strategy(performance_data, market_data)
            else:
                # 单一策略
                algorithm = self.adjustment_algorithms.get(self.adjustment_strategy)
                if algorithm:
                    new_weights = algorithm.calculate_adjustment(
                        old_weights, performance_data, market_data
                    )
                else:
                    new_weights = old_weights.copy()

            # 应用权重约束
            constrained_weights = self._apply_constraints(new_weights)

            # 检查是否需要重新平衡
            weight_change = self._calculate_weight_change(old_weights, constrained_weights)
            if force_rebalance or weight_change > self.constraints.rebalance_threshold:
                constrained_weights = self._rebalance_weights(constrained_weights)
                logger.info(f"Rebalanced weights due to {weight_change:.3f} change")

            # 更新内部状态
            self._update_weight_state(constrained_weights)

            # 记录权重历史
            self.weight_history.append((datetime.now(), constrained_weights.copy()))

            # 限制历史记录长度
            if len(self.weight_history) > 1000:
                self.weight_history = self.weight_history[-1000:]

            # 定期保存
            if len(self.weight_history) % 10 == 0:
                self._save_weights()

            logger.debug(f"Weights updated: avg change = {weight_change:.3f}")
            return constrained_weights

        except Exception as e:
            logger.error(f"Error updating weights: {str(e)}")
            return self.current_weights.copy()

    def _apply_hybrid_strategy(self,
                             performance_data: Dict[str, Any],
                             market_data: Dict[str, Any]) -> Dict[str, float]:
        """应用混合权重调整策略"""
        weights = self.current_weights.copy()

        # 1. 基于性能的调整 (权重: 40%)
        perf_algorithm = self.adjustment_algorithms[WeightAdjustmentStrategy.PERFORMANCE_BASED]
        perf_weights = perf_algorithm.calculate_adjustment(weights, performance_data, market_data)

        # 2. 基于市场状态的调整 (权重: 35%)
        regime_algorithm = self.adjustment_algorithms[WeightAdjustmentStrategy.MARKET_REGIME]
        regime_weights = regime_algorithm.calculate_adjustment(weights, performance_data, market_data)

        # 3. 基于相关性的调整 (权重: 25%)
        corr_weights = self._apply_correlation_adjustment(weights, performance_data)

        # 混合调整结果
        final_weights = {}
        for indicator in weights:
            final_weights[indicator] = (
                0.4 * perf_weights.get(indicator, weights[indicator]) +
                0.35 * regime_weights.get(indicator, weights[indicator]) +
                0.25 * corr_weights.get(indicator, weights[indicator])
            )

        return final_weights

    def _apply_correlation_adjustment(self,
                                    current_weights: Dict[str, float],
                                    performance_data: Dict[str, Any]) -> Dict[str, float]:
        """基于相关性调整权重"""
        correlation_matrix = performance_data.get('correlation_matrix')
        if correlation_matrix is None:
            return current_weights.copy()

        adjusted_weights = current_weights.copy()
        indicators = list(current_weights.keys())

        for i, indicator1 in enumerate(indicators):
            if indicator1 not in correlation_matrix:
                continue

            # 计算与其它指标的平均相关性
            avg_correlation = 0
            count = 0

            for j, indicator2 in enumerate(indicators):
                if i != j and indicator2 in correlation_matrix[indicator1]:
                    avg_correlation += abs(correlation_matrix[indicator1][indicator2])
                    count += 1

            if count > 0:
                avg_correlation /= count
                # 相关性越高，权重调整幅度越大
                correlation_penalty = avg_correlation * 0.3
                adjusted_weights[indicator1] *= (1 - correlation_penalty)

        return adjusted_weights

    def _apply_constraints(self, weights: Dict[str, float]) -> Dict[str, float]:
        """应用权重约束条件"""
        constrained_weights = weights.copy()

        # 1. 应用单个权重约束
        for indicator, weight in constrained_weights.items():
            if indicator in self.indicator_weights:
                indicator_weight = self.indicator_weights[indicator]
                constrained_weights[indicator] = max(
                    indicator_weight.min_weight,
                    min(indicator_weight.max_weight, weight)
                )

        # 2. 确保权重总和为1
        total_weight = sum(constrained_weights.values())
        if total_weight > 0:
            for indicator in constrained_weights:
                constrained_weights[indicator] /= total_weight

        return constrained_weights

    def _rebalance_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """重新平衡权重"""
        rebalanced_weights = weights.copy()
        indicators = list(rebalanced_weights.keys())

        if not indicators:
            return rebalanced_weights

        # 按当前权重排序
        sorted_indicators = sorted(indicators, key=lambda x: rebalanced_weights[x], reverse=True)

        # 重新分配权重以确保总和为1且满足约束
        remaining_weight = self.constraints.total_weight_sum
        assigned_weight = 0

        for indicator in sorted_indicators:
            if indicator in self.indicator_weights:
                ind_weight = self.indicator_weights[indicator]
                max_assignable = min(remaining_weight, ind_weight.max_weight)

                if assigned_weight + max_assignable <= remaining_weight:
                    rebalanced_weights[indicator] = max_assignable
                    assigned_weight += max_assignable
                else:
                    rebalanced_weights[indicator] = remaining_weight - assigned_weight
                    break

        # 标准化权重
        total = sum(rebalanced_weights.values())
        if total > 0:
            for indicator in rebalanced_weights:
                rebalanced_weights[indicator] /= total

        return rebalanced_weights

    def _calculate_weight_change(self, old_weights: Dict[str, float], new_weights: Dict[str, float]) -> float:
        """计算权重变化幅度"""
        total_change = 0
        for indicator in old_weights:
            old_weight = old_weights.get(indicator, 0)
            new_weight = new_weights.get(indicator, 0)
            total_change += abs(new_weight - old_weight)

        return total_change

    def _update_weight_state(self, new_weights: Dict[str, float]):
        """更新权重内部状态"""
        for indicator, new_weight in new_weights.items():
            if indicator in self.indicator_weights:
                indicator_weight = self.indicator_weights[indicator]
                indicator_weight.current_weight = new_weight
                indicator_weight.last_adjusted = datetime.now()

        self.current_weights = new_weights.copy()

    def optimize_weights(self,
                        objective_function: Callable[[Dict[str, float]], float],
                        optimization_method: str = 'grid_search',
                        num_iterations: int = 100) -> Dict[str, float]:
        """
        权重优化

        Args:
            objective_function: 目标函数
            optimization_method: 优化方法 ('grid_search', 'random_search', 'bayesian')
            num_iterations: 迭代次数

        Returns:
            Dict[str, float]: 优化后的权重
        """
        if not self.enable_optimization:
            logger.warning("Weight optimization is disabled")
            return self.current_weights.copy()

        try:
            if optimization_method == 'grid_search':
                best_weights = self._grid_search_optimization(objective_function, num_iterations)
            elif optimization_method == 'random_search':
                best_weights = self._random_search_optimization(objective_function, num_iterations)
            elif optimization_method == 'bayesian':
                best_weights = self._bayesian_optimization(objective_function, num_iterations)
            else:
                logger.warning(f"Unknown optimization method: {optimization_method}")
                return self.current_weights.copy()

            logger.info(f"Weight optimization completed: score = {objective_function(best_weights):.4f}")
            return best_weights

        except Exception as e:
            logger.error(f"Weight optimization failed: {str(e)}")
            return self.current_weights.copy()

    def _grid_search_optimization(self,
                                objective_function: Callable[[Dict[str, float]], float],
                                num_iterations: int) -> Dict[str, float]:
        """网格搜索优化"""
        best_weights = self.current_weights.copy()
        best_score = objective_function(best_weights)

        indicators = list(self.current_weights.keys())
        if len(indicators) > 3:
            # 对于多个指标，使用粗粒度网格搜索
            step_size = 0.1
        else:
            step_size = 0.05

        def generate_grid_combinations():
            """生成网格组合"""
            if len(indicators) == 1:
                for w1 in np.arange(0.1, 1.0, step_size):
                    yield {indicators[0]: w1}
            elif len(indicators) == 2:
                for w1 in np.arange(0.1, 0.9, step_size):
                    w2 = 1.0 - w1
                    if w2 >= 0.1:
                        yield {indicators[0]: w1, indicators[1]: w2}
            else:
                # 对于3个及以上指标，使用简化搜索
                for _ in range(min(num_iterations, 100)):
                    weights = np.random.dirichlet(np.ones(len(indicators)))
                    yield dict(zip(indicators, weights))

        count = 0
        for weights in generate_grid_combinations():
            if count >= num_iterations:
                break

            constrained_weights = self._apply_constraints(weights)
            score = objective_function(constrained_weights)

            if score > best_score:
                best_score = score
                best_weights = constrained_weights.copy()

            count += 1

        return best_weights

    def _random_search_optimization(self,
                                  objective_function: Callable[[Dict[str, float]], float],
                                  num_iterations: int) -> Dict[str, float]:
        """随机搜索优化"""
        best_weights = self.current_weights.copy()
        best_score = objective_function(best_weights)

        indicators = list(self.current_weights.keys())
        count = 0

        while count < num_iterations:
            # 生成随机权重
            weights = np.random.dirichlet(np.ones(len(indicators)))
            random_weights = dict(zip(indicators, weights))

            constrained_weights = self._apply_constraints(random_weights)
            score = objective_function(constrained_weights)

            if score > best_score:
                best_score = score
                best_weights = constrained_weights.copy()

            count += 1

        return best_weights

    def _bayesian_optimization(self,
                             objective_function: Callable[[Dict[str, float]], float],
                             num_iterations: int) -> Dict[str, float]:
        """贝叶斯优化（简化实现）"""
        # 这里使用简化的贝叶斯优化，实际应用中可使用更专业的库
        best_weights = self.current_weights.copy()
        best_score = objective_function(best_weights)

        indicators = list(self.current_weights.keys())

        # 初始采样
        for _ in range(min(10, num_iterations)):
            weights = np.random.dirichlet(np.ones(len(indicators)))
            random_weights = dict(zip(indicators, weights))
            constrained_weights = self._apply_constraints(random_weights)
            score = objective_function(constrained_weights)

            if score > best_score:
                best_score = score
                best_weights = constrained_weights.copy()

        return best_weights

    def update_performance_metrics(self,
                                 indicator_name: str,
                                 metrics: WeightPerformanceMetrics):
        """
        更新指标性能指标

        Args:
            indicator_name: 指标名称
            metrics: 性能指标
        """
        self.performance_metrics[indicator_name] = metrics

        # 更新指标权重对象的性能分数
        if indicator_name in self.indicator_weights:
            # 计算综合性能分数
            performance_score = (
                metrics.sharpe_ratio * 0.3 +
                metrics.total_return * 0.25 +
                metrics.win_rate * 0.2 +
                metrics.stability_score * 0.15 +
                (1 - abs(metrics.max_drawdown)) * 0.1
            )
            performance_score = max(0, min(1, performance_score))

            self.indicator_weights[indicator_name].performance_score = performance_score
            self.indicator_weights[indicator_name].last_adjusted = datetime.now()

    def get_weight_statistics(self) -> Dict[str, Any]:
        """获取权重统计信息"""
        stats = {
            'current_weights': self.current_weights.copy(),
            'base_weights': {k: v.base_weight for k, v in self.indicator_weights.items()},
            'weight_changes': {},
            'performance_scores': {k: v.performance_score for k, v in self.indicator_weights.items()},
            'total_indicators': len(self.indicator_weights),
            'last_update': max([v.last_adjusted for v in self.indicator_weights.values()]).isoformat()
        }

        # 计算权重变化
        for indicator in self.indicator_weights:
            base_weight = self.indicator_weights[indicator].base_weight
            current_weight = self.indicator_weights[indicator].current_weight
            stats['weight_changes'][indicator] = current_weight - base_weight

        return stats

    def get_weight_history(self,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[Tuple[datetime, Dict[str, float]]]:
        """获取权重历史记录"""
        if not start_date and not end_date:
            return self.weight_history.copy()

        filtered_history = []
        for timestamp, weights in self.weight_history:
            if start_date and timestamp < start_date:
                continue
            if end_date and timestamp > end_date:
                continue
            filtered_history.append((timestamp, weights.copy()))

        return filtered_history

    def export_weights(self, format: str = 'dict') -> Union[Dict, pd.DataFrame]:
        """
        导出权重数据

        Args:
            format: 导出格式 ('dict', 'dataframe')

        Returns:
            权重数据
        """
        if format == 'dict':
            return {
                'current_weights': self.current_weights.copy(),
                'indicator_weights': {k: v.to_dict() for k, v in self.indicator_weights.items()},
                'constraints': self.constraints.__dict__,
                'performance_metrics': {k: v.__dict__ for k, v in self.performance_metrics.items()}
            }
        elif format == 'dataframe':
            data = []
            for indicator, weight_obj in self.indicator_weights.items():
                data.append({
                    'indicator_name': indicator,
                    'base_weight': weight_obj.base_weight,
                    'current_weight': weight_obj.current_weight,
                    'weight_change': weight_obj.current_weight - weight_obj.base_weight,
                    'performance_score': weight_obj.performance_score,
                    'last_adjusted': weight_obj.last_adjusted
                })
            return pd.DataFrame(data)
        else:
            raise ValueError(f"Unknown export format: {format}")

    def _load_historical_weights(self):
        """加载历史权重数据"""
        try:
            weights_file = self.cache_dir / "weight_history.json"
            if weights_file.exists():
                with open(weights_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 恢复权重历史
                for item in data.get('weight_history', []):
                    timestamp = datetime.fromisoformat(item['timestamp'])
                    weights = item['weights']
                    self.weight_history.append((timestamp, weights))

                logger.debug(f"Loaded {len(self.weight_history)} historical weight records")

        except Exception as e:
            logger.warning(f"Failed to load historical weights: {str(e)}")

    def _save_weights(self):
        """保存权重数据"""
        try:
            weights_file = self.cache_dir / "weight_history.json"

            data = {
                'current_weights': self.current_weights,
                'indicator_weights': {k: v.to_dict() for k, v in self.indicator_weights.items()},
                'weight_history': [
                    {'timestamp': timestamp.isoformat(), 'weights': weights}
                    for timestamp, weights in self.weight_history[-100:]  # 只保存最近100条记录
                ],
                'last_saved': datetime.now().isoformat()
            }

            with open(weights_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug("Weight data saved successfully")

        except Exception as e:
            logger.error(f"Failed to save weight data: {str(e)}")

    def reset_weights(self):
        """重置权重到初始状态"""
        self.current_weights = self.initial_weights.copy()

        for indicator, weight in self.initial_weights.items():
            if indicator in self.indicator_weights:
                self.indicator_weights[indicator].current_weight = weight
                self.indicator_weights[indicator].adjustment_factor = 1.0
                self.indicator_weights[indicator].last_adjusted = datetime.now()

        logger.info("Weights reset to initial state")

    def get_configuration_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            'total_indicators': len(self.indicator_weights),
            'adjustment_strategy': self.adjustment_strategy.value,
            'optimization_enabled': self.enable_optimization,
            'constraints': {
                'total_weight_sum': self.constraints.total_weight_sum,
                'min_individual_weight': self.constraints.min_individual_weight,
                'max_individual_weight': self.constraints.max_individual_weight,
                'rebalance_threshold': self.constraints.rebalance_threshold
            },
            'algorithms': list(self.adjustment_algorithms.keys()),
            'cache_directory': str(self.cache_dir),
            'weight_history_length': len(self.weight_history)
        }
#!/usr/bin/env python3
"""
Strategy Combination Optimization System
策略组合优化系统

Professional strategy combination optimization with advanced features:
- Strategy correlation and cointegration analysis
- Multi-strategy weight optimization
- Transaction cost and slippage analysis
- Strategy attribution analysis
- Dynamic strategy allocation
- Strategy stability testing
- VectorBT multi-strategy backtesting integration

专为Task 2.4设计的专业策略组合优化系统
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
import logging
from datetime import datetime
import time
import warnings
warnings.filterwarnings('ignore')

try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    logging.warning("VectorBT not available. Install with: pip install vectorbt")

try:
    from scipy.optimize import minimize, differential_evolution
    from scipy.stats import pearsonr, spearmanr, kendalltau
    from scipy.spatial.distance import pdist, squareform
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("SciPy not available. Some features may not work")

from .expanded_strategies import ExpandedStrategies
from .mpt_optimizer import MPTOptimizer, OptimizationResult
from .strategy_correlation import StrategyCorrelationAnalyzer, CorrelationConfig
from .strategy_attribution import StrategyAttributionAnalyzer, AttributionConfig

logger = logging.getLogger(__name__)

@dataclass
class StrategyCombinationConfig:
    """策略组合优化配置"""
    # 基本参数
    risk_free_rate: float = 0.03  # 无风险利率
    trading_days_per_year: int = 252  # 交易日数

    # 策略选择参数
    max_strategies_per_combination: int = 8  # 最大策略数
    min_strategy_weight: float = 0.05  # 最小策略权重
    max_strategy_weight: float = 0.5  # 最大策略权重
    correlation_threshold: float = 0.7  # 相关性阈值

    # 优化参数
    optimization_method: str = "sharpe_ratio"  # sharpe_ratio, risk_adjusted_return, utility
    rebalance_frequency: str = "monthly"  # daily, weekly, monthly, quarterly
    window_size: int = 252  # 滚动窗口大小

    # 交易成本
    transaction_cost: float = 0.001  # 交易成本率
    slippage_model: str = "linear"  # linear, quadratic, percentage
    slippage_rate: float = 0.0005  # 滑点率
    market_impact_factor: float = 0.0001  # 市场冲击因子

    # 稳定性测试
    stability_periods: int = 12  # 稳定性测试周期数
    var_confidence_level: float = 0.95  # VaR置信水平
    cvar_confidence_level: float = 0.95  # CVaR置信水平

    # 动态调整
    dynamic_allocation: bool = True  # 启用动态分配
    momentum_adjustment: bool = True  # 动量调整
    volatility_targeting: bool = True  # 波动率目标
    max_volatility: float = 0.15  # 最大波动率

    # 风险管理
    max_drawdown_limit: float = 0.20  # 最大回撤限制
    leverage_limit: float = 2.0  # 杠杆限制
    position_concentration_limit: float = 0.3  # 仓位集中度限制

    # 输出和监控
    detailed_attribution: bool = True  # 详细归因分析
    performance_monitoring: bool = True  # 性能监控
    save_intermediate_results: bool = True  # 保存中间结果

@dataclass
class StrategyInfo:
    """策略信息"""
    name: str  # 策略名称
    parameters: Dict[str, Any]  # 策略参数
    category: str  # 策略类别
    expected_return: float  # 期望回报
    expected_volatility: float  # 期望波动率
    sharpe_ratio: float  # 夏普比率
    max_drawdown: float  # 最大回撤
    win_rate: float  # 胜率
    profit_factor: float  # 盈利因子

@dataclass
class StrategyCombination:
    """策略组合"""
    strategies: List[StrategyInfo]  # 策略列表
    weights: np.ndarray  # 策略权重
    combination_method: str  # 组合方法

    # 性能指标
    expected_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    var_95: float  # 95% VaR
    cvar_95: float  # 95% CVaR

    # 相关性指标
    avg_correlation: float
    effective_number_bets: float  # 有效策略数
    diversification_ratio: float  # 多样化比率

    # 成本分析
    expected_turnover: float  # 期望换手率
    transaction_costs: float  # 交易成本
    slippage_costs: float  # 滑点成本
    total_costs: float  # 总成本

    # 归因分析
    strategy_attribution: Dict[str, float]  # 策略归因
    risk_attribution: Dict[str, float]  # 风险归因

    # 稳定性指标
    stability_score: float  # 稳定性评分
    performance_consistency: float  # 表现一致性
    ranking_stability: float  # 排名稳定性

    # 元数据
    creation_time: str
    optimization_time: float

@dataclass
class CombinationOptimizationResult:
    """组合优化结果"""
    best_combination: StrategyCombination  # 最佳组合
    all_combinations: List[StrategyCombination]  # 所有组合
    optimization_objective: str  # 优化目标
    optimization_time: float  # 优化时间
    total_combinations_tested: int  # 测试的组合数

    # 性能统计
    performance_summary: Dict[str, Any]  # 性能总结
    stability_analysis: Dict[str, Any]  # 稳定性分析
    cost_analysis: Dict[str, Any]  # 成本分析
    attribution_summary: Dict[str, Any]  # 归因总结

class StrategyCombinationOptimizer:
    """
    策略组合优化引擎

    专业级多策略组合优化系统，支持：
    - 策略相关性分析和协整测试
    - 多目标权重优化
    - 交易成本和滑点建模
    - 策略归因和风险分解
    - 动态策略分配
    - 稳健性测试
    """

    def __init__(self, config: Optional[StrategyCombinationConfig] = None):
        """初始化策略组合优化引擎"""
        self.config = config or StrategyCombinationConfig()

        # 初始化组件
        self.expanded_strategies = ExpandedStrategies()
        self.mpt_optimizer = MPTOptimizer()
        self.correlation_analyzer = StrategyCorrelationAnalyzer()
        self.attribution_analyzer = StrategyAttributionAnalyzer()

        # 策略缓存
        self.strategy_cache: Dict[str, StrategyInfo] = {}
        self.combination_cache: Dict[str, StrategyCombination] = {}

        logger.info("Strategy Combination Optimizer initialized")

    def optimize_strategy_combinations(
        self,
        price_data: pd.DataFrame,
        available_strategies: List[Tuple[str, Dict[str, Any]]],
        optimization_objective: str = "sharpe_ratio",
        constraints: Optional[Dict[str, Any]] = None
    ) -> CombinationOptimizationResult:
        """
        优化策略组合

        Args:
            price_data: 价格数据
            available_strategies: 可用策略列表 [(strategy_name, parameters)]
            optimization_objective: 优化目标
            constraints: 约束条件

        Returns:
            CombinationOptimizationResult: 优化结果
        """
        start_time = time.time()
        logger.info(f"Starting strategy combination optimization with {len(available_strategies)} strategies")

        try:
            # 预处理策略
            strategy_performances = self._preprocess_strategies(price_data, available_strategies)

            # 策略相关性分析
            correlation_matrix = self._analyze_strategy_correlations(strategy_performances)

            # 生成候选策略组合
            candidate_combinations = self._generate_candidate_combinations(
                strategy_performances, correlation_matrix
            )

            # 优化每个组合
            optimized_combinations = []
            for i, combination in enumerate(candidate_combinations):
                logger.info(f"Optimizing combination {i+1}/{len(candidate_combinations)}")

                optimized = self._optimize_single_combination(
                    price_data, combination, optimization_objective, constraints
                )

                if optimized:
                    optimized_combinations.append(optimized)

            # 选择最佳组合
            best_combination = self._select_best_combination(
                optimized_combinations, optimization_objective
            )

            # 稳定性测试
            stable_combinations = self._stability_test(
                price_data, optimized_combinations[:10]  # 测试前10个
            )

            # 创建结果
            result = CombinationOptimizationResult(
                best_combination=best_combination,
                all_combinations=stable_combinations,
                optimization_objective=optimization_objective,
                optimization_time=time.time() - start_time,
                total_combinations_tested=len(candidate_combinations),
                performance_summary=self._generate_performance_summary(stable_combinations),
                stability_analysis=self._generate_stability_analysis(stable_combinations),
                cost_analysis=self._generate_cost_analysis(stable_combinations),
                attribution_summary=self._generate_attribution_summary(stable_combinations)
            )

            logger.info(f"Strategy combination optimization completed in {result.optimization_time:.3f}s")
            return result

        except Exception as e:
            logger.error(f"Strategy combination optimization failed: {e}")
            raise

    def _preprocess_strategies(
        self,
        price_data: pd.DataFrame,
        available_strategies: List[Tuple[str, Dict[str, Any]]]
    ) -> List[StrategyInfo]:
        """预处理策略，计算性能指标"""
        strategy_performances = []

        for strategy_name, parameters in available_strategies:
            try:
                # 检查缓存
                cache_key = f"{strategy_name}_{hash(str(sorted(parameters.items())))}"
                if cache_key in self.strategy_cache:
                    strategy_performances.append(self.strategy_cache[cache_key])
                    continue

                # 生成策略信号
                signals = self.expanded_strategies.generate_signals(price_data, strategy_name, parameters)

                # 回测策略
                if VECTORBT_AVAILABLE:
                    portfolio = vbt.Portfolio.from_signals(
                        close=price_data['close'],
                        entries=signals['entries'],
                        exits=signals['exits'],
                        init_cash=100000,
                        fees=self.config.transaction_cost
                    )

                    # 计算性能指标
                    stats = portfolio.stats()

                    strategy_info = StrategyInfo(
                        name=strategy_name,
                        parameters=parameters,
                        category=self._get_strategy_category(strategy_name),
                        expected_return=stats['Total Return [%]'] / 100,
                        expected_volatility=stats['Volatility (Ann.) [%]'] / 100,
                        sharpe_ratio=stats['Sharpe Ratio'],
                        max_drawdown=abs(stats['Max Drawdown [%]'] / 100),
                        win_rate=stats['Win Rate [%]'] / 100,
                        profit_factor=stats.get('Profit Factor', 1.0)
                    )
                else:
                    # 简化的性能计算
                    strategy_info = StrategyInfo(
                        name=strategy_name,
                        parameters=parameters,
                        category=self._get_strategy_category(strategy_name),
                        expected_return=0.0,
                        expected_volatility=0.0,
                        sharpe_ratio=0.0,
                        max_drawdown=0.0,
                        win_rate=0.0,
                        profit_factor=1.0
                    )

                self.strategy_cache[cache_key] = strategy_info
                strategy_performances.append(strategy_info)

            except Exception as e:
                logger.warning(f"Failed to process strategy {strategy_name}: {e}")
                continue

        # 过滤低质量策略
        min_sharpe = 0.5
        max_drawdown_limit = 0.3

        filtered_strategies = [
            s for s in strategy_performances
            if s.sharpe_ratio >= min_sharpe and s.max_drawdown <= max_drawdown_limit
        ]

        logger.info(f"Filtered {len(filtered_strategies)}/{len(strategy_performances)} strategies")
        return filtered_strategies

    def _analyze_strategy_correlations(
        self,
        strategy_performances: List[StrategyInfo]
    ) -> pd.DataFrame:
        """分析策略相关性"""
        logger.info("Analyzing strategy correlations")

        # 生成策略收益序列（简化版本）
        # 实际实现中应该基于历史回测数据
        n_strategies = len(strategy_performances)
        correlation_matrix = pd.DataFrame(
            np.eye(n_strategies),
            index=[s.name for s in strategy_performances],
            columns=[s.name for s in strategy_performances]
        )

        # 基于策略类别和参数估算相关性
        for i in range(n_strategies):
            for j in range(i+1, n_strategies):
                s1, s2 = strategy_performances[i], strategy_performances[j]

                # 基于类别的基础相关性
                if s1.category == s2.category:
                    base_corr = 0.6  # 同类别策略相关性较高
                else:
                    base_corr = 0.3  # 不同类别策略相关性较低

                # 基于参数调整
                param_similarity = self._calculate_parameter_similarity(s1.parameters, s2.parameters)
                correlation = base_corr + 0.2 * param_similarity
                correlation = min(0.9, max(-0.3, correlation))  # 限制范围

                correlation_matrix.iloc[i, j] = correlation
                correlation_matrix.iloc[j, i] = correlation

        return correlation_matrix

    def _generate_candidate_combinations(
        self,
        strategy_performances: List[StrategyInfo],
        correlation_matrix: pd.DataFrame
    ) -> List[List[StrategyInfo]]:
        """生成候选策略组合"""
        logger.info("Generating candidate strategy combinations")

        candidate_combinations = []
        n_strategies = len(strategy_performances)

        # 按Sharpe比率排序
        sorted_strategies = sorted(strategy_performances, key=lambda x: x.sharpe_ratio, reverse=True)

        # 生成不同大小的组合
        for size in range(2, min(self.config.max_strategies_per_combination + 1, n_strategies + 1)):
            # 基于性能和相关性生成组合
            for i in range(min(50, n_strategies)):  # 限制组合数量
                if i + size > n_strategies:
                    break

                # 选择策略
                combination = [sorted_strategies[i]]

                # 添加相关性较低的策略
                for j in range(n_strategies):
                    if j != i and len(combination) < size:
                        candidate = sorted_strategies[j]

                        # 检查相关性
                        max_corr = 0.0
                        for existing in combination:
                            corr = correlation_matrix.loc[candidate.name, existing.name]
                            max_corr = max(max_corr, corr)

                        if max_corr < self.config.correlation_threshold:
                            combination.append(candidate)

                if len(combination) == size:
                    candidate_combinations.append(combination)

        # 添加基于聚类的组合
        if len(strategy_performances) > 5:
            cluster_combinations = self._generate_cluster_based_combinations(
                strategy_performances, correlation_matrix
            )
            candidate_combinations.extend(cluster_combinations)

        logger.info(f"Generated {len(candidate_combinations)} candidate combinations")
        return candidate_combinations

    def _optimize_single_combination(
        self,
        price_data: pd.DataFrame,
        strategies: List[StrategyInfo],
        optimization_objective: str,
        constraints: Optional[Dict[str, Any]]
    ) -> Optional[StrategyCombination]:
        """优化单个策略组合"""
        try:
            n_strategies = len(strategies)

            # 生成策略收益矩阵
            returns_matrix = self._generate_strategy_returns_matrix(price_data, strategies)

            if returns_matrix is None or len(returns_matrix) == 0:
                return None

            # 权重优化
            if optimization_objective == "sharpe_ratio":
                optimal_weights = self._optimize_for_sharpe_ratio(returns_matrix, strategies)
            elif optimization_objective == "risk_adjusted_return":
                optimal_weights = self._optimize_for_risk_adjusted_return(returns_matrix, strategies)
            elif optimization_objective == "utility":
                optimal_weights = self._optimize_for_utility(returns_matrix, strategies)
            else:
                optimal_weights = np.ones(n_strategies) / n_strategies  # 等权重

            # 计算组合性能
            portfolio_returns = np.dot(returns_matrix, optimal_weights)

            performance_metrics = self._calculate_portfolio_performance(portfolio_returns)
            correlation_metrics = self._calculate_correlation_metrics(optimal_weights, returns_matrix)
            cost_metrics = self._calculate_cost_metrics(optimal_weights, returns_matrix)
            attribution_metrics = self._calculate_attribution_metrics(optimal_weights, strategies)
            stability_metrics = self._calculate_stability_metrics(optimal_weights, returns_matrix)

            # 创建策略组合
            combination = StrategyCombination(
                strategies=strategies,
                weights=optimal_weights,
                combination_method=optimization_objective,
                expected_return=performance_metrics['expected_return'],
                volatility=performance_metrics['volatility'],
                sharpe_ratio=performance_metrics['sharpe_ratio'],
                max_drawdown=performance_metrics['max_drawdown'],
                var_95=performance_metrics['var_95'],
                cvar_95=performance_metrics['cvar_95'],
                avg_correlation=correlation_metrics['avg_correlation'],
                effective_number_bets=correlation_metrics['effective_number_bets'],
                diversification_ratio=correlation_metrics['diversification_ratio'],
                expected_turnover=cost_metrics['expected_turnover'],
                transaction_costs=cost_metrics['transaction_costs'],
                slippage_costs=cost_metrics['slippage_costs'],
                total_costs=cost_metrics['total_costs'],
                strategy_attribution=attribution_metrics['strategy_attribution'],
                risk_attribution=attribution_metrics['risk_attribution'],
                stability_score=stability_metrics['stability_score'],
                performance_consistency=stability_metrics['performance_consistency'],
                ranking_stability=stability_metrics['ranking_stability'],
                creation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                optimization_time=0.0
            )

            return combination

        except Exception as e:
            logger.warning(f"Failed to optimize combination: {e}")
            return None

    def _optimize_for_sharpe_ratio(
        self,
        returns_matrix: np.ndarray,
        strategies: List[StrategyInfo]
    ) -> np.ndarray:
        """为最大化Sharpe比率优化权重"""
        if not SCIPY_AVAILABLE:
            return np.ones(len(strategies)) / len(strategies)

        n_strategies = len(strategies)

        # 目标函数：负Sharpe比率
        def negative_sharpe(weights):
            portfolio_return = np.mean(np.dot(returns_matrix, weights))
            portfolio_vol = np.std(np.dot(returns_matrix, weights))

            if portfolio_vol < 1e-8:
                return -np.inf

            sharpe = (portfolio_return - self.config.risk_free_rate) / portfolio_vol
            return -sharpe

        # 约束条件
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}  # 权重和为1
        ]

        bounds = [
            (self.config.min_strategy_weight, self.config.max_strategy_weight)
            for _ in range(n_strategies)
        ]

        # 初始权重（等权重）
        initial_weights = np.ones(n_strategies) / n_strategies

        # 优化
        result = minimize(
            negative_sharpe,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )

        if result.success:
            weights = result.x
            # 归一化
            weights = np.maximum(weights, 0)
            weights = weights / np.sum(weights)
            return weights
        else:
            return initial_weights

    def _optimize_for_risk_adjusted_return(
        self,
        returns_matrix: np.ndarray,
        strategies: List[StrategyInfo]
    ) -> np.ndarray:
        """为风险调整后回报优化权重"""
        n_strategies = len(strategies)

        # 计算风险调整后期望回报
        risk_adjusted_returns = []
        for i, strategy in enumerate(strategies):
            strategy_returns = returns_matrix[:, i]
            mean_return = np.mean(strategy_returns)
            volatility = np.std(strategy_returns)
            risk_adjusted = mean_return / (volatility + 1e-8)  # 避免除零
            risk_adjusted_returns.append(risk_adjusted)

        # 基于风险调整后回报分配权重
        risk_adjusted_returns = np.array(risk_adjusted_returns)
        risk_adjusted_returns = np.maximum(risk_adjusted_returns, 0)  # 确保非负

        weights = risk_adjusted_returns / np.sum(risk_adjusted_returns)

        # 应用约束
        weights = np.maximum(weights, self.config.min_strategy_weight)
        weights = np.minimum(weights, self.config.max_strategy_weight)
        weights = weights / np.sum(weights)

        return weights

    def _optimize_for_utility(
        self,
        returns_matrix: np.ndarray,
        strategies: List[StrategyInfo]
    ) -> np.ndarray:
        """为效用函数优化权重"""
        n_strategies = len(strategies)

        # 均值-方差效用函数: U = E[R] - 0.5 * λ * Var[R]
        risk_aversion = 3.0  # 风险厌恶参数

        def utility(weights):
            portfolio_returns = np.dot(returns_matrix, weights)
            expected_return = np.mean(portfolio_returns)
            portfolio_variance = np.var(portfolio_returns)

            utility = expected_return - 0.5 * risk_aversion * portfolio_variance
            return -utility  # 负效用因为是最小化

        # 约束条件
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        ]

        bounds = [
            (self.config.min_strategy_weight, self.config.max_strategy_weight)
            for _ in range(n_strategies)
        ]

        initial_weights = np.ones(n_strategies) / n_strategies

        if SCIPY_AVAILABLE:
            result = minimize(
                utility,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000}
            )

            if result.success:
                weights = result.x
                weights = np.maximum(weights, 0)
                weights = weights / np.sum(weights)
                return weights

        return initial_weights

    def _generate_strategy_returns_matrix(
        self,
        price_data: pd.DataFrame,
        strategies: List[StrategyInfo]
    ) -> Optional[np.ndarray]:
        """生成策略收益矩阵"""
        try:
            returns_matrix = []

            for strategy in strategies:
                # 生成策略信号
                signals = self.expanded_strategies.generate_signals(
                    price_data, strategy.name, strategy.parameters
                )

                if VECTORBT_AVAILABLE:
                    # 计算策略收益
                    portfolio = vbt.Portfolio.from_signals(
                        close=price_data['close'],
                        entries=signals['entries'],
                        exits=signals['exits'],
                        init_cash=100000,
                        fees=self.config.transaction_cost
                    )

                    returns = portfolio.returns()
                    returns_matrix.append(returns.values)
                else:
                    # 简化计算
                    returns = price_data['close'].pct_change().fillna(0)
                    returns_matrix.append(returns.values)

            if returns_matrix:
                return np.array(returns_matrix).T  # 转置: (time_periods, strategies)
            else:
                return None

        except Exception as e:
            logger.warning(f"Failed to generate strategy returns matrix: {e}")
            return None

    def _calculate_portfolio_performance(self, portfolio_returns: np.ndarray) -> Dict[str, float]:
        """计算组合性能指标"""
        if len(portfolio_returns) == 0:
            return {
                'expected_return': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'var_95': 0.0,
                'cvar_95': 0.0
            }

        # 基本统计
        expected_return = np.mean(portfolio_returns) * self.config.trading_days_per_year
        volatility = np.std(portfolio_returns) * np.sqrt(self.config.trading_days_per_year)

        # Sharpe比率
        if volatility > 1e-8:
            sharpe_ratio = (expected_return - self.config.risk_free_rate) / volatility
        else:
            sharpe_ratio = 0.0

        # 最大回撤
        cumulative_returns = np.cumprod(1 + portfolio_returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = abs(np.min(drawdown))

        # VaR和CVaR
        var_95 = np.percentile(portfolio_returns, 5)
        cvar_95 = np.mean(portfolio_returns[portfolio_returns <= var_95])

        return {
            'expected_return': expected_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'var_95': var_95,
            'cvar_95': cvar_95
        }

    def _calculate_correlation_metrics(
        self,
        weights: np.ndarray,
        returns_matrix: np.ndarray
    ) -> Dict[str, float]:
        """计算相关性指标"""
        n_strategies = len(weights)

        # 计算相关性矩阵
        if returns_matrix.shape[1] > 1:
            corr_matrix = np.corrcoef(returns_matrix.T)
            avg_correlation = (np.sum(corr_matrix) - n_strategies) / (n_strategies * (n_strategies - 1))
        else:
            avg_correlation = 0.0

        # 有效策略数
        effective_number_bets = 1.0 / np.sum(weights ** 2)

        # 多样化比率
        weighted_vol = np.sqrt(np.dot(weights.T, np.dot(np.cov(returns_matrix.T), weights)))
        weighted_avg_vol = np.sum(weights * np.sqrt(np.diag(np.cov(returns_matrix.T))))

        if weighted_avg_vol > 1e-8:
            diversification_ratio = weighted_avg_vol / weighted_vol
        else:
            diversification_ratio = 1.0

        return {
            'avg_correlation': avg_correlation,
            'effective_number_bets': effective_number_bets,
            'diversification_ratio': diversification_ratio
        }

    def _calculate_cost_metrics(
        self,
        weights: np.ndarray,
        returns_matrix: np.ndarray
    ) -> Dict[str, float]:
        """计算成本指标"""
        # 期望换手率（简化计算）
        if len(returns_matrix) > 1:
            # 基于波动率估算换手率
            strategy_volatilities = np.std(returns_matrix, axis=0)
            expected_turnover = np.mean(strategy_volatilities) * np.sqrt(252) * 0.5  # 经验系数
        else:
            expected_turnover = 0.0

        # 交易成本
        transaction_costs = expected_turnover * self.config.transaction_cost

        # 滑点成本
        if self.config.slippage_model == "linear":
            slippage_costs = expected_turnover * self.config.slippage_rate
        elif self.config.slippage_model == "quadratic":
            slippage_costs = expected_turnover ** 2 * self.config.slippage_rate
        else:  # percentage
            slippage_costs = expected_turnover * self.config.slippage_rate

        # 市场冲击成本
        market_impact_costs = expected_turnover ** 1.5 * self.config.market_impact_factor

        total_costs = transaction_costs + slippage_costs + market_impact_costs

        return {
            'expected_turnover': expected_turnover,
            'transaction_costs': transaction_costs,
            'slippage_costs': slippage_costs,
            'total_costs': total_costs
        }

    def _calculate_attribution_metrics(
        self,
        weights: np.ndarray,
        strategies: List[StrategyInfo]
    ) -> Dict[str, float]:
        """计算归因指标"""
        strategy_names = [s.name for s in strategies]

        # 策略归因（基于权重）
        strategy_attribution = {
            name: float(weight) for name, weight in zip(strategy_names, weights)
        }

        # 风险归因（基于波动率）
        strategy_volatilities = np.array([s.expected_volatility for s in strategies])
        weighted_volatilities = weights * strategy_volatilities
        total_weighted_vol = np.sum(weighted_volatilities)

        if total_weighted_vol > 1e-8:
            risk_attribution = {
                name: float(wv / total_weighted_vol)
                for name, wv in zip(strategy_names, weighted_volatilities)
            }
        else:
            risk_attribution = strategy_attribution.copy()

        return {
            'strategy_attribution': strategy_attribution,
            'risk_attribution': risk_attribution
        }

    def _calculate_stability_metrics(
        self,
        weights: np.ndarray,
        returns_matrix: np.ndarray
    ) -> Dict[str, float]:
        """计算稳定性指标"""
        if len(returns_matrix) < 50:  # 数据不足
            return {
                'stability_score': 0.5,
                'performance_consistency': 0.5,
                'ranking_stability': 0.5
            }

        # 性能一致性（基于滚动窗口）
        window_size = min(60, len(returns_matrix) // 4)
        rolling_returns = []

        for i in range(window_size, len(returns_matrix)):
            window_data = returns_matrix[i-window_size:i]
            portfolio_returns = np.dot(window_data, weights)
            rolling_returns.append(np.mean(portfolio_returns))

        if rolling_returns:
            performance_consistency = 1.0 - (np.std(rolling_returns) / (np.mean(rolling_returns) + 1e-8))
            performance_consistency = max(0.0, min(1.0, performance_consistency))
        else:
            performance_consistency = 0.5

        # 排名稳定性（简化版本）
        # 在实际实现中，应该基于不同时间段的表现排名
        ranking_stability = 0.7  # 经验值

        # 综合稳定性评分
        stability_score = (performance_consistency + ranking_stability) / 2

        return {
            'stability_score': stability_score,
            'performance_consistency': performance_consistency,
            'ranking_stability': ranking_stability
        }

    def _select_best_combination(
        self,
        combinations: List[StrategyCombination],
        optimization_objective: str
    ) -> StrategyCombination:
        """选择最佳策略组合"""
        if not combinations:
            raise ValueError("No valid combinations available")

        if optimization_objective == "sharpe_ratio":
            # 考虑成本调整后的Sharpe比率
            best = max(combinations, key=lambda c: c.sharpe_ratio - c.total_costs)
        elif optimization_objective == "risk_adjusted_return":
            best = max(combinations, key=lambda c: c.expected_return / (c.volatility + 1e-8))
        elif optimization_objective == "utility":
            # 均值-方差效用
            risk_aversion = 3.0
            best = max(
                combinations,
                key=lambda c: c.expected_return - 0.5 * risk_aversion * c.volatility ** 2
            )
        else:
            # 综合评分
            best = max(
                combinations,
                key=lambda c: (
                    0.4 * c.sharpe_ratio +
                    0.3 * c.stability_score +
                    0.2 * c.diversification_ratio -
                    0.1 * c.total_costs
                )
            )

        return best

    def _stability_test(
        self,
        price_data: pd.DataFrame,
        combinations: List[StrategyCombination]
    ) -> List[StrategyCombination]:
        """稳定性测试"""
        logger.info("Performing stability testing")

        stable_combinations = []

        for combination in combinations:
            # 分割数据为多个时期
            n_periods = self.config.stability_periods
            period_length = len(price_data) // n_periods

            period_performances = []

            for i in range(n_periods):
                start_idx = i * period_length
                end_idx = (i + 1) * period_length if i < n_periods - 1 else len(price_data)

                period_data = price_data.iloc[start_idx:end_idx]

                # 重新生成策略收益
                returns_matrix = self._generate_strategy_returns_matrix(
                    period_data, combination.strategies
                )

                if returns_matrix is not None:
                    portfolio_returns = np.dot(returns_matrix, combination.weights)
                    performance = self._calculate_portfolio_performance(portfolio_returns)
                    period_performances.append(performance['sharpe_ratio'])

            # 计算稳定性指标
            if len(period_performances) >= 2:
                sharpe_std = np.std(period_performances)
                sharpe_mean = np.mean(period_performances)

                if sharpe_mean > 0:
                    stability_coefficient = sharpe_std / sharpe_mean
                    # 稳定性评分 (越低越好，转换为0-1评分)
                    stability_score = max(0.0, 1.0 - stability_coefficient)
                else:
                    stability_score = 0.0

                # 更新组合的稳定性评分
                combination.stability_score = stability_score

                # 只保留稳定的组合
                if stability_score >= 0.6:  # 稳定性阈值
                    stable_combinations.append(combination)
            else:
                # 数据不足，给中等评分
                combination.stability_score = 0.5
                stable_combinations.append(combination)

        logger.info(f"Stability testing completed: {len(stable_combinations)}/{len(combinations)} stable combinations")
        return stable_combinations

    def _generate_performance_summary(self, combinations: List[StrategyCombination]) -> Dict[str, Any]:
        """生成性能总结"""
        if not combinations:
            return {}

        sharpe_ratios = [c.sharpe_ratio for c in combinations]
        returns = [c.expected_return for c in combinations]
        volatilities = [c.volatility for c in combinations]
        drawdowns = [c.max_drawdown for c in combinations]

        return {
            'sharpe_ratio_stats': {
                'mean': np.mean(sharpe_ratios),
                'std': np.std(sharpe_ratios),
                'min': np.min(sharpe_ratios),
                'max': np.max(sharpe_ratios),
                'median': np.median(sharpe_ratios)
            },
            'return_stats': {
                'mean': np.mean(returns),
                'std': np.std(returns),
                'min': np.min(returns),
                'max': np.max(returns)
            },
            'volatility_stats': {
                'mean': np.mean(volatilities),
                'std': np.std(volatilities),
                'min': np.min(volatilities),
                'max': np.max(volatilities)
            },
            'drawdown_stats': {
                'mean': np.mean(drawdowns),
                'std': np.std(drawdowns),
                'min': np.min(drawdowns),
                'max': np.max(drawdowns)
            }
        }

    def _generate_stability_analysis(self, combinations: List[StrategyCombination]) -> Dict[str, Any]:
        """生成稳定性分析"""
        if not combinations:
            return {}

        stability_scores = [c.stability_score for c in combinations]
        consistency_scores = [c.performance_consistency for c in combinations]

        return {
            'stability_distribution': {
                'mean': np.mean(stability_scores),
                'std': np.std(stability_scores),
                'min': np.min(stability_scores),
                'max': np.max(stability_scores),
                'high_stability_count': sum(1 for s in stability_scores if s >= 0.7)
            },
            'consistency_distribution': {
                'mean': np.mean(consistency_scores),
                'std': np.std(consistency_scores),
                'min': np.min(consistency_scores),
                'max': np.max(consistency_scores)
            }
        }

    def _generate_cost_analysis(self, combinations: List[StrategyCombination]) -> Dict[str, Any]:
        """生成成本分析"""
        if not combinations:
            return {}

        total_costs = [c.total_costs for c in combinations]
        transaction_costs = [c.transaction_costs for c in combinations]
        turnovers = [c.expected_turnover for c in combinations]

        return {
            'cost_distribution': {
                'mean_total_cost': np.mean(total_costs),
                'mean_transaction_cost': np.mean(transaction_costs),
                'mean_turnover': np.mean(turnovers),
                'total_cost_range': [np.min(total_costs), np.max(total_costs)]
            },
            'cost_efficiency': {
                'cost_adjusted_sharpe': [
                    c.sharpe_ratio - c.total_costs for c in combinations
                ]
            }
        }

    def _generate_attribution_summary(self, combinations: List[StrategyCombination]) -> Dict[str, Any]:
        """生成归因总结"""
        if not combinations:
            return {}

        # 统计策略出现频率
        strategy_frequency = {}
        strategy_contribution = {}

        for combination in combinations:
            for i, strategy in enumerate(combination.strategies):
                strategy_name = strategy.name
                weight = combination.weights[i]

                # 频率统计
                strategy_frequency[strategy_name] = strategy_frequency.get(strategy_name, 0) + 1

                # 贡献统计
                contribution = weight * combination.sharpe_ratio
                strategy_contribution[strategy_name] = strategy_contribution.get(strategy_name, 0) + contribution

        # 计算平均贡献
        for strategy_name in strategy_contribution:
            strategy_contribution[strategy_name] /= strategy_frequency[strategy_name]

        return {
            'strategy_frequency': strategy_frequency,
            'average_contribution': strategy_contribution,
            'top_strategies': sorted(
                strategy_contribution.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

    def _get_strategy_category(self, strategy_name: str) -> str:
        """获取策略类别"""
        category_map = {
            "RSI_MEAN_REVERSION": "Mean Reversion",
            "MACD_CROSSOVER": "Trend",
            "DUAL_MOVING_AVERAGE": "Trend",
            "BOLLINGER_BANDS": "Mean Reversion",
            "VOLATILITY_BREAKOUT": "Volatility",
            "MOMENTUM_BREAKOUT": "Price Action"
        }

        return category_map.get(strategy_name, "Other")

    def _calculate_parameter_similarity(
        self,
        params1: Dict[str, Any],
        params2: Dict[str, Any]
    ) -> float:
        """计算参数相似性"""
        common_keys = set(params1.keys()) & set(params2.keys())

        if not common_keys:
            return 0.0

        similarities = []
        for key in common_keys:
            val1 = params1[key]
            val2 = params2[key]

            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # 数值参数的相似性
                if abs(val1) > 1e-8:
                    similarity = 1.0 - abs(val1 - val2) / abs(val1)
                    similarity = max(0.0, min(1.0, similarity))
                    similarities.append(similarity)
                else:
                    similarities.append(1.0 if abs(val2) < 1e-8 else 0.0)
            else:
                # 分类参数的相似性
                similarities.append(1.0 if val1 == val2 else 0.0)

        return np.mean(similarities)

    def _generate_cluster_based_combinations(
        self,
        strategy_performances: List[StrategyInfo],
        correlation_matrix: pd.DataFrame
    ) -> List[List[StrategyInfo]]:
        """基于聚类生成组合"""
        if len(strategy_performances) < 5:
            return []

        combinations = []

        try:
            # 使用相关性进行聚类
            if SKLEARN_AVAILABLE:
                correlation_distances = 1 - correlation_matrix.values
                distance_matrix = squareform(correlation_distances)

                # K-means聚类
                n_clusters = min(4, len(strategy_performances) // 2)
                kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                cluster_labels = kmeans.fit_predict(correlation_matrix.values)

                # 为每个聚类生成代表性策略
                for cluster_id in range(n_clusters):
                    cluster_strategies = [
                        strategy_performances[i]
                        for i, label in enumerate(cluster_labels)
                        if label == cluster_id
                    ]

                    if cluster_strategies:
                        # 选择每个聚类中Sharpe最高的策略
                        best_in_cluster = max(cluster_strategies, key=lambda s: s.sharpe_ratio)
                        combinations.append([best_in_cluster])

            # 生成跨聚类的组合
            for i in range(0, len(strategy_performances), 3):
                for j in range(i+1, min(i+4, len(strategy_performances))):
                    for k in range(j+1, min(i+5, len(strategy_performances))):
                        if i < len(strategy_performances) and j < len(strategy_performances) and k < len(strategy_performances):
                            combination = [
                                strategy_performances[i],
                                strategy_performances[j],
                                strategy_performances[k]
                            ]
                            combinations.append(combination)

        except Exception as e:
            logger.warning(f"Cluster-based combination generation failed: {e}")

        return combinations

# 便利函数
def create_strategy_combination_optimizer(
    config: Optional[StrategyCombinationConfig] = None
) -> StrategyCombinationOptimizer:
    """创建策略组合优化引擎"""
    return StrategyCombinationOptimizer(config)

def optimize_strategy_combinations(
    price_data: pd.DataFrame,
    available_strategies: List[Tuple[str, Dict[str, Any]]],
    optimization_objective: str = "sharpe_ratio"
) -> CombinationOptimizationResult:
    """便利函数：优化策略组合"""
    optimizer = StrategyCombinationOptimizer()
    return optimizer.optimize_strategy_combinations(
        price_data, available_strategies, optimization_objective
    )
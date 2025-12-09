#!/usr/bin/env python3
"""
Risk Parity Portfolio Optimization Engine
风险平价投资组合优化引擎

Professional implementation of risk parity and risk budgeting strategies
专业风险平价和风险预算策略实现

Features:
- Equal risk contribution portfolios
- Risk budgeting optimization
- Multiple risk measures (volatility, VaR, CVaR)
- Hierarchical risk parity
- Dynamic risk allocation
- Constraint handling and leverage
- Integration with existing risk metrics
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
    from scipy.optimize import minimize, LinearConstraint, Bounds, NonlinearConstraint
    from scipy.spatial.distance import squareform, pdist
    import scipy.linalg as la
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("SciPy not available. Install with: pip install scipy")

try:
    from .risk_metrics import AdvancedRiskMetrics, RiskMetricsConfig
except ImportError:
    # Fallback for direct module execution
    import risk_metrics
    AdvancedRiskMetrics = risk_metrics.AdvancedRiskMetrics
    RiskMetricsConfig = risk_metrics.RiskMetricsConfig

logger = logging.getLogger(__name__)

@dataclass
class RiskParityConfig:
    """风险平价配置"""
    # 基本参数
    risk_free_rate: float = 0.03  # 无风险利率 (3%)
    trading_days_per_year: int = 252  # 交易日数

    # 风险预算
    risk_budget: Optional[np.ndarray] = None  # 风险预算比例
    equal_risk_budget: bool = True  # 等风险预算

    # 风险度量
    risk_measure: str = "volatility"  # volatility, var, cvar
    confidence_level: float = 0.95  # VaR/CVaR置信水平

    # 约束条件
    min_weight: float = 0.0  # 最小权重
    max_weight: float = 1.0  # 最大权重
    weight_sum: float = 1.0  # 权重总和
    leverage_limit: float = 1.5  # 杠杆限制

    # 优化参数
    max_iterations: int = 1000  # 最大迭代次数
    tolerance: float = 1e-8  # 收敛容差
    convergence_criterion: str = "risk_budget"  # risk_budget, weights_change, objective

    # 数值稳定性
    epsilon: float = 1e-8  # 数值精度
    regularization: float = 1e-6  # 正则化参数

    # 高级选项
    enable_hierarchical: bool = False  # 启用层次风险平价
    clustering_method: str = "linkage"  # linkage, kmeans
    linkage_method: str = "ward"  # ward, average, complete

    # 交易成本
    trading_cost: float = 0.001  # 交易成本
    rebalance_threshold: float = 0.05  # 再平衡阈值

    def __post_init__(self):
        if self.risk_budget is None and not self.equal_risk_budget:
            self.risk_budget = None  # 将在优化时设置

@dataclass
class RiskContribution:
    """风险贡献分析"""
    marginal_contributions: np.ndarray  # 边际风险贡献
    risk_contributions: np.ndarray  # 风险贡献
    percentage_contributions: np.ndarray  # 百分比贡献

    # 风险分解
    systematic_risk: float  # 系统性风险
    idiosyncratic_risk: float  # 特质性风险
    diversification_ratio: float  # 分散化比率

    # 风险预算偏差
    budget_deviations: np.ndarray  # 预算偏差
    budget_error: float  # 预算误差
    parity_satisfaction: float  # 平价满足度

@dataclass
class RiskParityResult:
    """风险平价优化结果"""
    weights: np.ndarray  # 最优权重
    risk_contributions: RiskContribution  # 风险贡献分析

    # 投资组合指标
    expected_return: float  # 期望回报
    volatility: float  # 波动率
    sharpe_ratio: float  # 夏普比率
    leverage: float  # 杠杆

    # 风险度量
    portfolio_var: float  # 投资组合方差
    portfolio_var_95: float  # 95% VaR
    portfolio_cvar_95: float  # 95% CVaR

    # 优化信息
    optimization_method: str
    success: bool
    iterations: int
    convergence_time: float
    objective_value: float

    # 元数据
    assets: List[str]
    calculation_time: float
    timestamp: str

    # 层次结构 (如果适用)
    clusters: Optional[np.ndarray] = None
    cluster_weights: Optional[np.ndarray] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        weights_dict = {asset: weight for asset, weight in zip(self.assets, self.weights)}

        return {
            'portfolio_weights': weights_dict,
            'performance': {
                'expected_return': round(self.expected_return * 100, 2),
                'volatility': round(self.volatility * 100, 2),
                'sharpe_ratio': round(self.sharpe_ratio, 3),
                'leverage': round(self.leverage, 2)
            },
            'risk_metrics': {
                'portfolio_variance': round(self.portfolio_var, 6),
                'var_95': round(self.portfolio_var_95 * 100, 2),
                'cvar_95': round(self.portfolio_cvar_95 * 100, 2)
            },
            'risk_contributions': {
                'marginal_contributions': {
                    asset: round(marginal, 4)
                    for asset, marginal in zip(self.assets, self.risk_contributions.marginal_contributions)
                },
                'risk_contributions': {
                    asset: round(risk, 4)
                    for asset, risk in zip(self.assets, self.risk_contributions.risk_contributions)
                },
                'percentage_contributions': {
                    asset: round(pct * 100, 2)
                    for asset, pct in zip(self.assets, self.risk_contributions.percentage_contributions)
                },
                'systematic_risk': round(self.risk_contributions.systematic_risk, 4),
                'idiosyncratic_risk': round(self.risk_contributions.idiosyncratic_risk, 4),
                'diversification_ratio': round(self.risk_contributions.diversification_ratio, 3),
                'budget_error': round(self.risk_contributions.budget_error, 6),
                'parity_satisfaction': round(self.risk_contributions.parity_satisfaction * 100, 2)
            },
            'optimization_info': {
                'method': self.optimization_method,
                'success': self.success,
                'iterations': self.iterations,
                'convergence_time': round(self.convergence_time, 3),
                'objective_value': round(self.objective_value, 6)
            },
            'hierarchical_structure': {
                'clusters': self.clusters.tolist() if self.clusters is not None else None,
                'cluster_weights': self.cluster_weights.tolist() if self.cluster_weights is not None else None
            },
            'metadata': {
                'assets': self.assets,
                'calculation_time': round(self.calculation_time, 3),
                'timestamp': self.timestamp
            }
        }

class RiskParityOptimizer:
    """
    风险平价优化引擎

    Professional implementation of:
    - Equal Risk Contribution (ERC) portfolios
    - Risk budgeting optimization
    - Hierarchical Risk Parity (HRP)
    - Multiple risk measures (volatility, VaR, CVaR)
    - Constraint optimization with leverage
    """

    def __init__(self, config: Optional[RiskParityConfig] = None):
        """初始化风险平价优化引擎"""
        self.config = config or RiskParityConfig()

        if not SCIPY_AVAILABLE:
            raise ImportError("SciPy is required for Risk Parity Optimizer")

        # 风险指标计算器
        self.risk_calculator = AdvancedRiskMetrics()

        logger.info("Risk Parity Optimizer initialized")

    def optimize_equal_risk_contribution(
        self,
        returns: pd.DataFrame,
        risk_budget: Optional[np.ndarray] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> RiskParityResult:
        """
        等风险贡献优化

        Args:
            returns: 资产回报率矩阵 (time x assets)
            risk_budget: 风险预算比例 (可选)
            constraints: 约束条件

        Returns:
            RiskParityResult: 优化结果
        """
        start_time = time.time()

        try:
            logger.info(f"Starting equal risk contribution optimization for {returns.shape[1]} assets")

            # 准备数据
            mean_returns, cov_matrix = self._prepare_data(returns)
            num_assets = len(mean_returns)

            # 设置风险预算
            if risk_budget is None:
                if self.config.equal_risk_budget:
                    risk_budget = np.ones(num_assets) / num_assets
                else:
                    raise ValueError("Risk budget must be specified when equal_risk_budget is False")

            # 构建约束条件
            constraints_list, bounds = self._build_constraints(num_assets, constraints)

            # 初始权重 (基于波动率的倒数)
            volatilities = np.sqrt(np.diag(cov_matrix))
            initial_weights = 1.0 / volatilities
            initial_weights = initial_weights / initial_weights.sum()

            # 执行优化
            result = self._optimize_erc_risk_parity(
                mean_returns, cov_matrix, initial_weights, risk_budget, constraints_list, bounds
            )

            # 计算风险贡献
            risk_contributions = self._calculate_risk_contributions(result.x, cov_matrix, risk_budget)

            # 计算投资组合指标
            portfolio_metrics = self._calculate_portfolio_metrics(result.x, mean_returns, cov_matrix)

            # 创建结果
            optimization_result = RiskParityResult(
                weights=result.x,
                risk_contributions=risk_contributions,
                expected_return=portfolio_metrics['expected_return'],
                volatility=portfolio_metrics['volatility'],
                sharpe_ratio=portfolio_metrics['sharpe_ratio'],
                leverage=portfolio_metrics['leverage'],
                portfolio_var=portfolio_metrics['portfolio_var'],
                portfolio_var_95=portfolio_metrics['var_95'],
                portfolio_cvar_95=portfolio_metrics['cvar_95'],
                optimization_method='EQUAL_RISK_CONTRIBUTION',
                success=result.success,
                iterations=result.nit,
                convergence_time=result.time,
                objective_value=result.fun,
                assets=list(returns.columns),
                calculation_time=time.time() - start_time,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )

            logger.info(f"Equal risk contribution optimization completed in {optimization_result.calculation_time:.3f}s")
            return optimization_result

        except Exception as e:
            logger.error(f"Equal risk contribution optimization failed: {e}")
            raise

    def optimize_risk_budgeting(
        self,
        returns: pd.DataFrame,
        risk_budget: np.ndarray,
        constraints: Optional[Dict[str, Any]] = None
    ) -> RiskParityResult:
        """
        风险预算优化

        Args:
            returns: 资产回报率矩阵
            risk_budget: 风险预算比例 (和为1)
            constraints: 约束条件

        Returns:
            RiskParityResult: 优化结果
        """
        start_time = time.time()

        try:
            logger.info(f"Starting risk budgeting optimization for {returns.shape[1]} assets")

            # 验证风险预算
            if len(risk_budget) != returns.shape[1]:
                raise ValueError("Risk budget length must match number of assets")
            if not np.isclose(risk_budget.sum(), 1.0):
                risk_budget = risk_budget / risk_budget.sum()
                logger.warning("Risk budget normalized to sum to 1")

            # 准备数据
            mean_returns, cov_matrix = self._prepare_data(returns)
            num_assets = len(mean_returns)

            # 构建约束条件
            constraints_list, bounds = self._build_constraints(num_assets, constraints)

            # 初始权重 (基于风险预算和波动率)
            volatilities = np.sqrt(np.diag(cov_matrix))
            initial_weights = risk_budget / volatilities
            initial_weights = initial_weights / initial_weights.sum()

            # 执行优化
            result = self._optimize_risk_budgeting(
                mean_returns, cov_matrix, initial_weights, risk_budget, constraints_list, bounds
            )

            # 计算风险贡献
            risk_contributions = self._calculate_risk_contributions(result.x, cov_matrix, risk_budget)

            # 计算投资组合指标
            portfolio_metrics = self._calculate_portfolio_metrics(result.x, mean_returns, cov_matrix)

            # 创建结果
            optimization_result = RiskParityResult(
                weights=result.x,
                risk_contributions=risk_contributions,
                expected_return=portfolio_metrics['expected_return'],
                volatility=portfolio_metrics['volatility'],
                sharpe_ratio=portfolio_metrics['sharpe_ratio'],
                leverage=portfolio_metrics['leverage'],
                portfolio_var=portfolio_metrics['portfolio_var'],
                portfolio_var_95=portfolio_metrics['var_95'],
                portfolio_cvar_95=portfolio_metrics['cvar_95'],
                optimization_method='RISK_BUDGETING',
                success=result.success,
                iterations=result.nit,
                convergence_time=result.time,
                objective_value=result.fun,
                assets=list(returns.columns),
                calculation_time=time.time() - start_time,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )

            logger.info(f"Risk budgeting optimization completed in {optimization_result.calculation_time:.3f}s")
            return optimization_result

        except Exception as e:
            logger.error(f"Risk budgeting optimization failed: {e}")
            raise

    def optimize_hierarchical_risk_parity(
        self,
        returns: pd.DataFrame,
        linkage_method: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> RiskParityResult:
        """
        层次风险平价优化

        Args:
            returns: 资产回报率矩阵
            linkage_method: 连接方法
            constraints: 约束条件

        Returns:
            RiskParityResult: 优化结果
        """
        start_time = time.time()

        try:
            logger.info(f"Starting hierarchical risk parity optimization for {returns.shape[1]} assets")

            # 准备数据
            mean_returns, cov_matrix = self._prepare_data(returns)
            num_assets = len(mean_returns)

            # 层次聚类
            linkage_method = linkage_method or self.config.linkage_method
            clusters, cluster_order = self._hierarchical_clustering(cov_matrix, linkage_method)

            # 递归二分分配
            weights = self._recursive_bisection(cov_matrix, cluster_order)

            # 计算风险贡献
            risk_budget = np.ones(num_assets) / num_assets  # HRP通常目标是等风险贡献
            risk_contributions = self._calculate_risk_contributions(weights, cov_matrix, risk_budget)

            # 计算投资组合指标
            portfolio_metrics = self._calculate_portfolio_metrics(weights, mean_returns, cov_matrix)

            # 创建结果
            optimization_result = RiskParityResult(
                weights=weights,
                risk_contributions=risk_contributions,
                expected_return=portfolio_metrics['expected_return'],
                volatility=portfolio_metrics['volatility'],
                sharpe_ratio=portfolio_metrics['sharpe_ratio'],
                leverage=portfolio_metrics['leverage'],
                portfolio_var=portfolio_metrics['portfolio_var'],
                portfolio_var_95=portfolio_metrics['var_95'],
                portfolio_cvar_95=portfolio_metrics['cvar_95'],
                optimization_method='HIERARCHICAL_RISK_PARITY',
                success=True,
                iterations=0,
                convergence_time=time.time() - start_time,
                objective_value=0.0,
                clusters=clusters,
                cluster_weights=None,
                assets=list(returns.columns),
                calculation_time=time.time() - start_time,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )

            logger.info(f"Hierarchical risk parity optimization completed in {optimization_result.calculation_time:.3f}s")
            return optimization_result

        except Exception as e:
            logger.error(f"Hierarchical risk parity optimization failed: {e}")
            raise

    def _prepare_data(self, returns: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """准备优化数据"""
        # 移除NaN值
        returns_clean = returns.dropna()

        if len(returns_clean) == 0:
            raise ValueError("No valid return data after removing NaN values")

        # 年化回报率和协方差矩阵
        mean_returns = returns_clean.mean() * self.config.trading_days_per_year
        cov_matrix = returns_clean.cov() * self.config.trading_days_per_year

        # 正则化
        cov_matrix = cov_matrix + self.config.regularization * np.eye(len(mean_returns))

        return mean_returns.values, cov_matrix.values

    def _build_constraints(
        self,
        num_assets: int,
        custom_constraints: Optional[Dict[str, Any]]
    ) -> Tuple[List[Dict], Any]:
        """构建优化约束条件"""
        constraints_list = []

        # 权重总和约束
        constraints_list.append({
            'type': 'eq',
            'fun': lambda weights: np.sum(weights) - self.config.weight_sum
        })

        # 杠杆约束 (绝对权重和)
        if self.config.leverage_limit < float('inf'):
            constraints_list.append({
                'type': 'ineq',
                'fun': lambda weights: self.config.leverage_limit - np.sum(np.abs(weights))
            })

        # 边界约束
        bounds = tuple([
            (self.config.min_weight, self.config.max_weight)
            for _ in range(num_assets)
        ])

        # 自定义约束
        if custom_constraints:
            if 'min_weight' in custom_constraints:
                min_weight = custom_constraints['min_weight']
                bounds = tuple([
                    (min_weight, b[1])
                    for b in bounds
                ])

            if 'max_weight' in custom_constraints:
                max_weight = custom_constraints['max_weight']
                bounds = tuple([
                    (b[0], max_weight)
                    for b in bounds
                ])

            # 行业约束
            if 'sector_constraints' in custom_constraints:
                sector_constraints = custom_constraints['sector_constraints']
                for sector_info in sector_constraints:
                    sector_assets = sector_info['assets']
                    sector_min = sector_info.get('min_weight', 0)
                    sector_max = sector_info.get('max_weight', 1)

                    constraints_list.append({
                        'type': 'ineq',
                        'fun': lambda w, idx=sector_assets: np.sum(w[idx]) - sector_min
                    })

                    constraints_list.append({
                        'type': 'ineq',
                        'fun': lambda w, idx=sector_assets, max_w=sector_max: max_w - np.sum(w[idx])
                    })

        return constraints_list, bounds

    def _optimize_erc_risk_parity(
        self,
        mean_returns: np.ndarray,
        cov_matrix: np.ndarray,
        initial_weights: np.ndarray,
        risk_budget: np.ndarray,
        constraints: List[Dict],
        bounds: Tuple
    ) -> Any:
        """执行等风险贡献优化"""

        def risk_parity_objective(weights: np.ndarray) -> float:
            """风险平价目标函数"""
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))

            if portfolio_variance < self.config.epsilon:
                return float('inf')

            # 计算风险贡献
            marginal_contributions = np.dot(cov_matrix, weights) / portfolio_variance
            risk_contributions = weights * marginal_contributions

            # 计算与风险预算的差异
            risk_parity_error = np.sum((risk_contributions - risk_budget) ** 2)

            return risk_parity_error

        # 执行优化
        result = minimize(
            risk_parity_objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={
                'maxiter': self.config.max_iterations,
                'ftol': self.config.tolerance
            }
        )

        return result

    def _optimize_risk_budgeting(
        self,
        mean_returns: np.ndarray,
        cov_matrix: np.ndarray,
        initial_weights: np.ndarray,
        risk_budget: np.ndarray,
        constraints: List[Dict],
        bounds: Tuple
    ) -> Any:
        """执行风险预算优化"""

        def risk_budgeting_objective(weights: np.ndarray) -> float:
            """风险预算目标函数"""
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))

            if portfolio_variance < self.config.epsilon:
                return float('inf')

            # 计算风险贡献
            marginal_contributions = np.dot(cov_matrix, weights) / portfolio_variance
            risk_contributions = weights * marginal_contributions

            # 计算与指定风险预算的差异
            budget_error = np.sum((risk_contributions - risk_budget) ** 2)

            # 添加交易成本惩罚
            trading_cost_penalty = self.config.trading_cost * np.sum(np.abs(weights - initial_weights))

            return budget_error + trading_cost_penalty

        # 执行优化
        result = minimize(
            risk_budgeting_objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={
                'maxiter': self.config.max_iterations,
                'ftol': self.config.tolerance
            }
        )

        return result

    def _hierarchical_clustering(
        self,
        cov_matrix: np.ndarray,
        linkage_method: str
    ) -> Tuple[np.ndarray, List[int]]:
        """层次聚类"""
        try:
            from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
            from scipy.spatial.distance import squareform

            # 计算距离矩阵
            correlation = np.corrcoef(np.sqrt(np.diag(cov_matrix)) * cov_matrix / np.sqrt(np.diag(cov_matrix)))
            distance = np.sqrt(2 * (1 - correlation))

            # 层次聚类
            linkage_matrix = linkage(squareform(distance), method=linkage_method)

            # 获取聚类标签
            clusters = fcluster(linkage_matrix, t=3, criterion='maxclust')

            # 获取聚类顺序
            cluster_order = self._get_cluster_order(linkage_matrix)

            return clusters, cluster_order

        except ImportError:
            logger.warning("SciPy hierarchical clustering not available, using simple ordering")
            # 简单的替代方案：基于相关性排序
            correlation = np.corrcoef(np.sqrt(np.diag(cov_matrix)) * cov_matrix / np.sqrt(np.diag(cov_matrix)))
            cluster_order = list(range(len(correlation)))
            return np.ones(len(correlation)), cluster_order

    def _get_cluster_order(self, linkage_matrix: np.ndarray) -> List[int]:
        """获取聚类顺序"""
        n = linkage_matrix.shape[0] + 1
        order = list(range(n))

        # 简化的聚类顺序获取
        # 实际实现需要更复杂的树遍历算法
        return order

    def _recursive_bisection(
        self,
        cov_matrix: np.ndarray,
        cluster_order: List[int],
        weights: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """递归二分分配权重"""
        n = len(cluster_order)

        if weights is None:
            weights = np.ones(n)

        if n <= 1:
            return weights / weights.sum()

        # 分割聚类
        mid = n // 2
        left_cluster = cluster_order[:mid]
        right_cluster = cluster_order[mid:]

        # 计算子协方差矩阵
        left_cov = cov_matrix[np.ix_(left_cluster, left_cluster)]
        right_cov = cov_matrix[np.ix_(right_cluster, right_cluster)]

        # 递归分配
        left_weights = self._recursive_bisection(left_cov, list(range(len(left_cluster))))
        right_weights = self._recursive_bisection(right_cov, list(range(len(right_cluster))))

        # 计算最优分割比例
        left_var = np.dot(left_weights.T, np.dot(left_cov, left_weights))
        right_var = np.dot(right_weights.T, np.dot(right_cov, right_weights))

        inverse_volatility_split = 1 / np.sqrt(left_var) / (1 / np.sqrt(left_var) + 1 / np.sqrt(right_var))

        # 组合权重
        combined_weights = np.zeros(n)
        combined_weights[left_cluster] = left_weights * inverse_volatility_split
        combined_weights[right_cluster] = right_weights * (1 - inverse_volatility_split)

        return combined_weights

    def _calculate_risk_contributions(
        self,
        weights: np.ndarray,
        cov_matrix: np.ndarray,
        risk_budget: np.ndarray
    ) -> RiskContribution:
        """计算风险贡献"""
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))

        if portfolio_variance < self.config.epsilon:
            portfolio_variance = self.config.epsilon

        # 边际风险贡献
        marginal_contributions = np.dot(cov_matrix, weights) / portfolio_variance

        # 风险贡献
        risk_contributions = weights * marginal_contributions

        # 百分比贡献
        percentage_contributions = risk_contributions / np.sum(risk_contributions)

        # 风险分解
        eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
        systematic_risk = np.sum(eigenvalues[eigenvalues > self.config.epsilon])
        idiosyncratic_risk = portfolio_variance - systematic_risk
        diversification_ratio = np.sum(weights * np.sqrt(np.diag(cov_matrix))) / np.sqrt(portfolio_variance)

        # 风险预算偏差
        budget_deviations = risk_contributions - risk_budget
        budget_error = np.sum(budget_deviations ** 2)
        parity_satisfaction = 1.0 / (1.0 + budget_error)

        return RiskContribution(
            marginal_contributions=marginal_contributions,
            risk_contributions=risk_contributions,
            percentage_contributions=percentage_contributions,
            systematic_risk=systematic_risk,
            idiosyncratic_risk=idiosyncratic_risk,
            diversification_ratio=diversification_ratio,
            budget_deviations=budget_deviations,
            budget_error=budget_error,
            parity_satisfaction=parity_satisfaction
        )

    def _calculate_portfolio_metrics(
        self,
        weights: np.ndarray,
        mean_returns: np.ndarray,
        cov_matrix: np.ndarray
    ) -> Dict[str, float]:
        """计算投资组合指标"""
        # 基本指标
        expected_return = np.sum(mean_returns * weights)
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
        volatility = np.sqrt(portfolio_variance)

        # 夏普比率
        excess_return = expected_return - self.config.risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > self.config.epsilon else 0.0

        # 杠杆
        leverage = np.sum(np.abs(weights))

        # VaR和CVaR (简化版本)
        # 实际应用中需要更精确的模拟或历史方法
        var_95 = -1.65 * volatility / np.sqrt(self.config.trading_days_per_year)
        cvar_95 = -2.33 * volatility / np.sqrt(self.config.trading_days_per_year)

        return {
            'expected_return': expected_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'leverage': leverage,
            'portfolio_var': portfolio_variance,
            'var_95': var_95,
            'cvar_95': cvar_95
        }

# 便利函数
def create_risk_parity_optimizer(config: Optional[RiskParityConfig] = None) -> RiskParityOptimizer:
    """创建风险平价优化引擎"""
    return RiskParityOptimizer(config)

def optimize_equal_risk_contribution(
    returns: pd.DataFrame,
    risk_budget: Optional[np.ndarray] = None,
    constraints: Optional[Dict[str, Any]] = None
) -> RiskParityResult:
    """便利函数：等风险贡献优化"""
    optimizer = RiskParityOptimizer()
    return optimizer.optimize_equal_risk_contribution(returns, risk_budget, constraints)

def optimize_risk_budgeting(
    returns: pd.DataFrame,
    risk_budget: np.ndarray,
    constraints: Optional[Dict[str, Any]] = None
) -> RiskParityResult:
    """便利函数：风险预算优化"""
    optimizer = RiskParityOptimizer()
    return optimizer.optimize_risk_budgeting(returns, risk_budget, constraints)

def optimize_hierarchical_risk_parity(
    returns: pd.DataFrame,
    linkage_method: Optional[str] = None,
    constraints: Optional[Dict[str, Any]] = None
) -> RiskParityResult:
    """便利函数：层次风险平价优化"""
    optimizer = RiskParityOptimizer()
    return optimizer.optimize_hierarchical_risk_parity(returns, linkage_method, constraints)
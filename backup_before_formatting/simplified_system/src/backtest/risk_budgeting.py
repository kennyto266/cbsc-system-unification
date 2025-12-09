#!/usr/bin/env python3
"""
Risk Budgeting Framework
风险预算框架

Advanced risk budgeting and allocation strategies
高级风险预算和分配策略

Features:
- Multiple risk budgeting approaches
- Risk factor modeling
- Dynamic risk allocation
- Risk-adjusted performance attribution
- Risk budget monitoring and rebalancing
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    from scipy.optimize import minimize
    from scipy.stats import norm
    import scipy.linalg as la
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("SciPy not available. Install with: pip install scipy")

try:
    from .risk_parity_optimizer import RiskParityOptimizer, RiskParityConfig
    from .risk_metrics import AdvancedRiskMetrics
except ImportError:
    # Fallback for direct module execution
    import risk_parity_optimizer
    import risk_metrics
    RiskParityOptimizer = risk_parity_optimizer.RiskParityOptimizer
    RiskParityConfig = risk_parity_optimizer.RiskParityConfig
    AdvancedRiskMetrics = risk_metrics.AdvancedRiskMetrics

logger = logging.getLogger(__name__)

@dataclass
class RiskBudgetConfig:
    """风险预算配置"""
    # 基本参数
    risk_free_rate: float = 0.03  # 无风险利率
    trading_days_per_year: int = 252  # 交易日数

    # 风险预算类型
    budget_type: str = "equal"  # equal, custom, factor_based, target_vol

    # 风险因子
    risk_factors: List[str] = field(default_factory=lambda: ["market", "size", "value", "momentum", "quality"])
    factor_lookback: int = 252  # 因子计算回看期

    # 目标风险
    target_volatility: Optional[float] = None  # 目标波动率
    target_var_95: Optional[float] = None  # 目标VaR (95%)
    target_cvar_95: Optional[float] = None  # 目标CVaR (95%)

    # 再平衡参数
    rebalance_frequency: str = "monthly"  # daily, weekly, monthly, quarterly
    rebalance_threshold: float = 0.05  # 再平衡阈值
    drift_tolerance: float = 0.02  # 偏差容忍度

    # 监控参数
    monitoring_window: int = 20  # 监控窗口
    stress_testing: bool = True  # 压力测试

    # 约束条件
    min_weight: float = 0.0
    max_weight: float = 1.0
    max_leverage: float = 1.5

    # 性能基准
    benchmark_weights: Optional[np.ndarray] = None  # 基准权重
    tracking_error_limit: Optional[float] = None  # 跟踪误差限制

@dataclass
class RiskBudget:
    """风险预算定义"""
    name: str
    budget_allocation: np.ndarray  # 风险预算分配
    asset_names: List[str]

    # 风险目标
    target_volatility: Optional[float] = None
    target_var: Optional[float] = None
    target_cvar: Optional[float] = None

    # 约束条件
    min_weights: Optional[np.ndarray] = None
    max_weights: Optional[np.ndarray] = None

    # 元数据
    created_date: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    description: str = ""

@dataclass
class RiskBudgetAllocation:
    """风险预算分配结果"""
    weights: np.ndarray  # 资产权重
    risk_contributions: np.ndarray  # 风险贡献
    risk_budgets: np.ndarray  # 风险预算

    # 性能指标
    expected_return: float
    volatility: float
    sharpe_ratio: float

    # 风险指标
    portfolio_var: float
    var_95: float
    cvar_95: float

    # 预算偏差分析
    budget_deviations: np.ndarray
    budget_satisfaction: float

    # 元数据
    calculation_date: str
    allocation_method: str

    # 因子暴露 (如果适用)
    factor_exposures: Optional[np.ndarray] = None

class RiskBudgetingFramework:
    """
    风险预算框架

    提供多种风险预算方法和动态分配策略:
    - 等风险预算
    - 自定义风险预算
    - 基于因子的风险预算
    - 目标风险预算
    - 动态风险预算调整
    """

    def __init__(self, config: Optional[RiskBudgetConfig] = None):
        """初始化风险预算框架"""
        self.config = config or RiskBudgetConfig()

        if not SCIPY_AVAILABLE:
            raise ImportError("SciPy is required for Risk Budgeting Framework")

        # 风险平价优化器
        rp_config = RiskParityConfig(
            risk_free_rate=self.config.risk_free_rate,
            trading_days_per_year=self.config.trading_days_per_year,
            min_weight=self.config.min_weight,
            max_weight=self.config.max_weight,
            leverage_limit=self.config.max_leverage
        )
        self.rp_optimizer = RiskParityOptimizer(rp_config)

        # 风险指标计算器
        self.risk_calculator = AdvancedRiskMetrics()

        # 风险预算存储
        self.risk_budgets: Dict[str, RiskBudget] = {}

        logger.info("Risk Budgeting Framework initialized")

    def create_equal_risk_budget(
        self,
        assets: List[str],
        name: str = "equal_risk_budget"
    ) -> RiskBudget:
        """
        创建等风险预算

        Args:
            assets: 资产列表
            name: 预算名称

        Returns:
            RiskBudget: 等风险预算
        """
        num_assets = len(assets)
        equal_allocation = np.ones(num_assets) / num_assets

        budget = RiskBudget(
            name=name,
            budget_allocation=equal_allocation,
            asset_names=assets,
            description="Equal risk budget - each asset contributes equally to portfolio risk"
        )

        self.risk_budgets[name] = budget
        logger.info(f"Created equal risk budget '{name}' for {num_assets} assets")

        return budget

    def create_custom_risk_budget(
        self,
        assets: List[str],
        risk_allocations: Dict[str, float],
        name: str = "custom_risk_budget"
    ) -> RiskBudget:
        """
        创建自定义风险预算

        Args:
            assets: 资产列表
            risk_allocations: 风险分配字典 {asset: risk_percentage}
            name: 预算名称

        Returns:
            RiskBudget: 自定义风险预算
        """
        num_assets = len(assets)
        allocations = np.array([risk_allocations.get(asset, 0.0) for asset in assets])

        # 标准化到和为1
        if allocations.sum() > 0:
            allocations = allocations / allocations.sum()
        else:
            raise ValueError("Risk allocations must sum to positive value")

        budget = RiskBudget(
            name=name,
            budget_allocation=allocations,
            asset_names=assets,
            description=f"Custom risk budget with allocations: {dict(zip(assets, allocations.round(4)))}"
        )

        self.risk_budgets[name] = budget
        logger.info(f"Created custom risk budget '{name}'")

        return budget

    def create_factor_based_risk_budget(
        self,
        returns: pd.DataFrame,
        factor_returns: pd.DataFrame,
        name: str = "factor_risk_budget"
    ) -> RiskBudget:
        """
        创建基于因子的风险预算

        Args:
            returns: 资产回报率
            factor_returns: 因子回报率
            name: 预算名称

        Returns:
            RiskBudget: 基于因子的风险预算
        """
        # 计算因子暴露
        factor_exposures = self._calculate_factor_exposures(returns, factor_returns)

        # 基于因子暴露分配风险预算
        factor_risk_contributions = np.sum(np.abs(factor_exposures), axis=1)
        risk_allocations = factor_risk_contributions / factor_risk_contributions.sum()

        budget = RiskBudget(
            name=name,
            budget_allocation=risk_allocations,
            asset_names=list(returns.columns),
            description="Factor-based risk budget using PCA or regression analysis",
            factor_exposures=factor_exposures
        )

        self.risk_budgets[name] = budget
        logger.info(f"Created factor-based risk budget '{name}'")

        return budget

    def allocate_portfolio(
        self,
        returns: pd.DataFrame,
        budget_name: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> RiskBudgetAllocation:
        """
        根据风险预算分配投资组合

        Args:
            returns: 资产回报率
            budget_name: 风险预算名称
            constraints: 约束条件

        Returns:
            RiskBudgetAllocation: 分配结果
        """
        if budget_name not in self.risk_budgets:
            raise ValueError(f"Risk budget '{budget_name}' not found")

        budget = self.risk_budgets[budget_name]

        # 对齐资产顺序
        if set(budget.asset_names) != set(returns.columns):
            raise ValueError("Asset names in budget and returns must match")

        aligned_returns = returns[budget.asset_names]

        # 使用风险平价优化器执行分配
        result = self.rp_optimizer.optimize_risk_budgeting(
            aligned_returns,
            budget.budget_allocation,
            constraints
        )

        # 计算性能指标
        expected_return = result.expected_return
        volatility = result.volatility
        sharpe_ratio = result.sharpe_ratio

        # 风险指标
        portfolio_var = result.portfolio_var
        var_95 = result.portfolio_var_95
        cvar_95 = result.portfolio_cvar_95

        # 预算偏差分析
        risk_contributions = result.risk_contributions.risk_contributions
        budget_deviations = risk_contributions - budget.budget_allocation
        budget_satisfaction = result.risk_contributions.parity_satisfaction

        # 创建分配结果
        allocation = RiskBudgetAllocation(
            weights=result.weights,
            risk_contributions=risk_contributions,
            risk_budgets=budget.budget_allocation,
            expected_return=expected_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            portfolio_var=portfolio_var,
            var_95=var_95,
            cvar_95=cvar_95,
            budget_deviations=budget_deviations,
            budget_satisfaction=budget_satisfaction,
            factor_exposures=getattr(budget, 'factor_exposures', None),
            calculation_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            allocation_method=budget.name
        )

        logger.info(f"Portfolio allocation completed for budget '{budget_name}'")
        return allocation

    def create_target_volatility_budget(
        self,
        assets: List[str],
        target_vol: float,
        returns: Optional[pd.DataFrame] = None,
        name: str = "target_vol_budget"
    ) -> RiskBudget:
        """
        创建目标波动率风险预算

        Args:
            assets: 资产列表
            target_vol: 目标波动率
            returns: 历史回报率 (用于估算)
            name: 预算名称

        Returns:
            RiskBudget: 目标波动率风险预算
        """
        num_assets = len(assets)

        if returns is not None:
            # 基于历史数据估算波动率
            volatilities = returns.std()
            risk_budget = 1.0 / volatilities
            risk_budget = risk_budget / risk_budget.sum()
        else:
            # 等权重风险预算
            risk_budget = np.ones(num_assets) / num_assets

        budget = RiskBudget(
            name=name,
            budget_allocation=risk_budget,
            asset_names=assets,
            target_volatility=target_vol,
            description=f"Target volatility budget: {target_vol:.2%}"
        )

        self.risk_budgets[name] = budget
        logger.info(f"Created target volatility budget '{name}' with vol={target_vol:.2%}")

        return budget

    def monitor_budget_drift(
        self,
        current_allocation: np.ndarray,
        budget_name: str,
        returns: pd.DataFrame,
        lookback_days: int = 20
    ) -> Dict[str, Any]:
        """
        监控风险预算漂移

        Args:
            current_allocation: 当前资产权重
            budget_name: 风险预算名称
            returns: 最近回报率
            lookback_days: 回看天数

        Returns:
            Dict: 漂移分析结果
        """
        if budget_name not in self.risk_budgets:
            raise ValueError(f"Risk budget '{budget_name}' not found")

        budget = self.risk_budgets[budget_name]

        # 使用最近的回报率数据
        recent_returns = returns.tail(lookback_days)

        # 计算当前风险贡献
        cov_matrix = recent_returns.cov().values * self.config.trading_days_per_year
        current_risk_contributions = self._calculate_risk_contributions(current_allocation, cov_matrix)

        # 计算漂移
        drift = current_risk_contributions - budget.budget_allocation
        drift_magnitude = np.sqrt(np.sum(drift ** 2))

        # 判断是否需要再平衡
        needs_rebalance = (
            drift_magnitude > self.config.rebalance_threshold or
            np.max(np.abs(drift)) > self.config.drift_tolerance
        )

        # 计算跟踪误差 (如果有基准)
        tracking_error = 0.0
        if self.config.benchmark_weights is not None:
            active_returns = recent_returns @ (current_allocation - self.config.benchmark_weights)
            tracking_error = active_returns.std() * np.sqrt(self.config.trading_days_per_year)

        monitoring_result = {
            'budget_name': budget_name,
            'current_risk_contributions': current_risk_contributions,
            'target_risk_budgets': budget.budget_allocation,
            'risk_drift': drift,
            'drift_magnitude': drift_magnitude,
            'needs_rebalance': needs_rebalance,
            'tracking_error': tracking_error,
            'monitoring_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'lookback_days': lookback_days
        }

        logger.info(f"Budget drift monitoring completed for '{budget_name}': drift={drift_magnitude:.4f}")

        return monitoring_result

    def rebalance_portfolio(
        self,
        current_weights: np.ndarray,
        budget_name: str,
        returns: pd.DataFrame,
        transaction_costs: float = 0.001
    ) -> Dict[str, Any]:
        """
        再平衡投资组合

        Args:
            current_weights: 当前权重
            budget_name: 风险预算名称
            returns: 回报率数据
            transaction_costs: 交易成本

        Returns:
            Dict: 再平衡结果
        """
        # 重新计算最优权重
        optimal_allocation = self.allocate_portfolio(returns, budget_name)
        optimal_weights = optimal_allocation.weights

        # 计算交易
        trades = optimal_weights - current_weights
        trade_costs = np.sum(np.abs(trades)) * transaction_costs

        # 净效果
        expected_improvement = (
            optimal_allocation.sharpe_ratio -
            self._calculate_current_sharpe(current_weights, returns)
        )

        # 决策：是否执行再平衡
        should_rebalance = expected_improvement > 0 and trade_costs < expected_improvement * 0.1

        rebalance_result = {
            'current_weights': current_weights,
            'optimal_weights': optimal_weights,
            'trades': trades,
            'trade_costs': trade_costs,
            'expected_improvement': expected_improvement,
            'should_rebalance': should_rebalance,
            'rebalance_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        if should_rebalance:
            logger.info(f"Rebalancing recommended for budget '{budget_name}'")
        else:
            logger.info(f"Rebalancing not recommended for budget '{budget_name}'")

        return rebalance_result

    def stress_test_budget(
        self,
        budget_name: str,
        stress_scenarios: Dict[str, pd.DataFrame],
        returns: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        风险预算压力测试

        Args:
            budget_name: 风险预算名称
            stress_scenarios: 压力情景 {scenario_name: stressed_returns}
            returns: 基础回报率

        Returns:
            Dict: 压力测试结果
        """
        if budget_name not in self.risk_budgets:
            raise ValueError(f"Risk budget '{budget_name}' not found")

        # 获取基准分配
        baseline_allocation = self.allocate_portfolio(returns, budget_name)

        stress_results = {}

        for scenario_name, stressed_returns in stress_scenarios.items():
            try:
                # 在压力情景下重新分配
                stressed_allocation = self.allocate_portfolio(stressed_returns, budget_name)

                # 计算压力指标
                stress_impact = {
                    'baseline_sharpe': baseline_allocation.sharpe_ratio,
                    'stressed_sharpe': stressed_allocation.sharpe_ratio,
                    'sharpe_decline': baseline_allocation.sharpe_ratio - stressed_allocation.sharpe_ratio,
                    'baseline_volatility': baseline_allocation.volatility,
                    'stressed_volatility': stressed_allocation.volatility,
                    'volatility_increase': stressed_allocation.volatility - baseline_allocation.volatility,
                    'weight_changes': np.abs(stressed_allocation.weights - baseline_allocation.weights).sum(),
                    'budget_satisfaction': stressed_allocation.budget_satisfaction
                }

                stress_results[scenario_name] = stress_impact

            except Exception as e:
                logger.warning(f"Stress test failed for scenario '{scenario_name}': {e}")
                stress_results[scenario_name] = {'error': str(e)}

        # 汇总结果
        stress_summary = {
            'budget_name': budget_name,
            'baseline_allocation': baseline_allocation,
            'stress_results': stress_results,
            'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        logger.info(f"Stress testing completed for budget '{budget_name}' with {len(stress_scenarios)} scenarios")

        return stress_summary

    def compare_budgets(
        self,
        returns: pd.DataFrame,
        budget_names: List[str]
    ) -> pd.DataFrame:
        """
        比较多个风险预算

        Args:
            returns: 资产回报率
            budget_names: 预算名称列表

        Returns:
            pd.DataFrame: 比较结果
        """
        comparison_results = []

        for budget_name in budget_names:
            try:
                allocation = self.allocate_portfolio(returns, budget_name)

                result = {
                    'budget_name': budget_name,
                    'expected_return': allocation.expected_return,
                    'volatility': allocation.volatility,
                    'sharpe_ratio': allocation.sharpe_ratio,
                    'budget_satisfaction': allocation.budget_satisfaction,
                    'budget_error': np.sum(allocation.budget_deviations ** 2),
                    'diversification_ratio': 0.0  # 占位符
                }

                comparison_results.append(result)

            except Exception as e:
                logger.warning(f"Failed to analyze budget '{budget_name}': {e}")
                comparison_results.append({
                    'budget_name': budget_name,
                    'error': str(e)
                })

        return pd.DataFrame(comparison_results)

    def _calculate_factor_exposures(
        self,
        returns: pd.DataFrame,
        factor_returns: pd.DataFrame
    ) -> np.ndarray:
        """计算因子暴露"""
        try:
            # 使用线性回归计算因子暴露
            exposures = []

            for asset in returns.columns:
                asset_returns = returns[asset]

                # 确保数据对齐
                aligned_data = pd.concat([asset_returns, factor_returns], axis=1, join='inner')
                y = aligned_data.iloc[:, 0].values
                X = aligned_data.iloc[:, 1:].values

                # 添加常数项
                X = np.column_stack([np.ones(len(X)), X])

                # 线性回归
                try:
                    coefficients = np.linalg.lstsq(X, y, rcond=None)[0]
                    asset_exposure = coefficients[1:]  # 去掉常数项
                except:
                    asset_exposure = np.zeros(len(factor_returns.columns))

                exposures.append(asset_exposure)

            return np.array(exposures)

        except Exception as e:
            logger.warning(f"Factor exposure calculation failed: {e}")
            # 使用PCA作为备选方案
            from sklearn.decomposition import PCA

            pca = PCA(n_components=min(5, returns.shape[1]))
            try:
                return pca.fit_transform(returns.T).T
            except:
                return np.random.randn(5, len(returns.columns))

    def _calculate_risk_contributions(
        self,
        weights: np.ndarray,
        cov_matrix: np.ndarray
    ) -> np.ndarray:
        """计算风险贡献"""
        portfolio_var = np.dot(weights.T, np.dot(cov_matrix, weights))

        if portfolio_var < 1e-8:
            return np.ones(len(weights)) / len(weights)

        marginal_contributions = np.dot(cov_matrix, weights) / portfolio_var
        risk_contributions = weights * marginal_contributions

        return risk_contributions

    def _calculate_current_sharpe(self, weights: np.ndarray, returns: pd.DataFrame) -> float:
        """计算当前投资组合的夏普比率"""
        mean_returns = returns.mean() * self.config.trading_days_per_year
        cov_matrix = returns.cov() * self.config.trading_days_per_year

        expected_return = np.sum(mean_returns * weights)
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

        excess_return = expected_return - self.config.risk_free_rate

        return excess_return / portfolio_vol if portfolio_vol > 0 else 0.0

    def get_budget_summary(self) -> pd.DataFrame:
        """获取风险预算汇总"""
        summary_data = []

        for name, budget in self.risk_budgets.items():
            summary_data.append({
                'budget_name': name,
                'num_assets': len(budget.asset_names),
                'target_volatility': budget.target_volatility,
                'target_var': budget.target_var,
                'target_cvar': budget.target_cvar,
                'created_date': budget.created_date,
                'description': budget.description[:50] + "..." if len(budget.description) > 50 else budget.description
            })

        return pd.DataFrame(summary_data)

# 便利函数
def create_risk_budgeting_framework(config: Optional[RiskBudgetConfig] = None) -> RiskBudgetingFramework:
    """创建风险预算框架"""
    return RiskBudgetingFramework(config)
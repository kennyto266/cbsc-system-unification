#!/usr / bin / env python3
"""
Mean - Variance Portfolio Optimization Engine
均值 - 方差投資組合優化引擎

Professional implementation of Modern Portfolio Theory (MPT)
專業現代投資組合理論(MPT)實現

Features:
- Markowitz mean - variance optimization
- Maximum Sharpe ratio optimization
- Minimum variance optimization
- Risk - adjusted return optimization
- Integration with VectorBT portfolio optimization
"""

import logging
import time
import warnings
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

try:
    import vectorbt as vbt

    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    logging.warning("VectorBT not available. Install with: pip install vectorbt")

try:
    from scipy.optimize import Bounds, LinearConstraint, minimize
    from scipy.spatial.distance import pdist, squareform

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("SciPy not available. Install with: pip install scipy")

logger = logging.getLogger(__name__)


@dataclass
class MPTConfig:
    """MPT優化配置"""

    # 基本參數
    risk_free_rate: float = 0.03  # 無風險利率 (3%)
    trading_days_per_year: int = 252  # 交易日數

    # 約束條件
    min_weight: float = 0.0  # 最小權重
    max_weight: float = 1.0  # 最大權重
    weight_sum: float = 1.0  # 權重總和

    # 優化參數
    max_iterations: int = 1000  # 最大迭代次數
    tolerance: float = 1e - 8  # 收斂容差

    # 數值穩定性
    epsilon: float = 1e - 8  # 數值精度
    regularization: float = 1e - 6  # 正則化參數

    # 計算選項
    efficient_frontier_points: int = 100  # 有效邊界點數
    enable_regularization: bool = True  # 啟用正則化


@dataclass
class OptimizationResult:
    """優化結果"""

    weights: np.ndarray  # 最優權重
    expected_return: float  # 期望回報
    volatility: float  # 波動率
    sharpe_ratio: float  # 夏普比率

    # 優化信息
    optimization_method: str
    success: bool
    iterations: int
    objective_value: float

    # 風險貢獻
    marginal_contributions: np.ndarray
    risk_contributions: np.ndarray

    # 元數據
    assets: List[str]
    calculation_time: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        weights_dict = {
            asset: weight for asset, weight in zip(self.assets, self.weights)
        }

        return {
            "portfolio_weights": weights_dict,
            "performance": {
                "expected_return": round(self.expected_return * 100, 2),
                "volatility": round(self.volatility * 100, 2),
                "sharpe_ratio": round(self.sharpe_ratio, 3),
            },
            "optimization_info": {
                "method": self.optimization_method,
                "success": self.success,
                "iterations": self.iterations,
                "objective_value": round(self.objective_value, 6),
            },
            "risk_analysis": {
                "marginal_contributions": {
                    asset: round(marginal, 4)
                    for asset, marginal in zip(self.assets, self.marginal_contributions)
                },
                "risk_contributions": {
                    asset: round(risk, 4)
                    for asset, risk in zip(self.assets, self.risk_contributions)
                },
            },
            "metadata": {
                "assets": self.assets,
                "calculation_time": round(self.calculation_time, 3),
                "timestamp": self.timestamp,
            },
        }


class MPTOptimizer:
    """
    現代投資組合理論優化引擎

    Implements Markowitz mean - variance optimization with professional features:
    - Maximum Sharpe ratio optimization
    - Minimum variance optimization
    - Risk parity and target volatility
    - Constraint optimization
    - Efficient frontier calculation
    """

    def __init__(self, config: Optional[MPTConfig] = None):
        """初始化MPT優化引擎"""
        self.config = config or MPTConfig()

        if not VECTORBT_AVAILABLE:
            raise ImportError("VectorBT is required for MPT Optimizer")

        if not SCIPY_AVAILABLE:
            raise ImportError("SciPy is required for MPT Optimizer")

        logger.info("MPT Optimizer initialized")

    def maximize_sharpe_ratio(
        self, returns: pd.DataFrame, constraints: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """
        最大化夏普比率

        Args:
            returns: 資產回報率矩陣 (time x assets)
            constraints: 約束條件

        Returns:
            OptimizationResult: 優化結果
        """
        start_time = time.time()

        try:
            logger.info(
                f"Starting Sharpe ratio maximization for {returns.shape[1]} assets"
            )

            # 準備數據
            mean_returns, cov_matrix = self._prepare_data(returns)
            num_assets = len(mean_returns)

            # 構建約束條件
            constraints_list, bounds = self._build_constraints(num_assets, constraints)

            # 目標函數 (負夏普比率，因為是最小化)
            def negative_sharpe_ratio(weights: np.ndarray) -> float:
                portfolio_return = np.sum(mean_returns * weights)
                portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
                portfolio_volatility = np.sqrt(portfolio_variance)

                if portfolio_volatility < self.config.epsilon:
                    return -np.inf

                excess_return = portfolio_return - self.config.risk_free_rate
                sharpe_ratio = excess_return / portfolio_volatility

                return -sharpe_ratio

            # 初始權重 (等權重)
            initial_weights = np.array([1.0 / num_assets] * num_assets)

            # 執行優化
            result = minimize(
                negative_sharpe_ratio,
                initial_weights,
                method="SLSQP",
                bounds = bounds,
                constraints = constraints_list,
                options={
                    "maxiter": self.config.max_iterations,
                    "ftol": self.config.tolerance,
                },
            )

            # 計算結果指標
            if result.success:
                weights = result.x
                portfolio_return = np.sum(mean_returns * weights)
                portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
                portfolio_volatility = np.sqrt(portfolio_variance)
                sharpe_ratio = (
                    portfolio_return - self.config.risk_free_rate
                ) / portfolio_volatility

                # 計算風險貢獻
                marginal_contributions = self._calculate_marginal_contributions(
                    weights, cov_matrix
                )
                risk_contributions = self._calculate_risk_contributions(
                    weights, cov_matrix
                )
            else:
                # 如果優化失敗，返回等權重
                weights = initial_weights
                portfolio_return = np.sum(mean_returns * weights)
                portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
                portfolio_volatility = np.sqrt(portfolio_variance)
                sharpe_ratio = (
                    portfolio_return - self.config.risk_free_rate
                ) / portfolio_volatility
                marginal_contributions = np.zeros(num_assets)
                risk_contributions = np.zeros(num_assets)

            # 創建結果
            optimization_result = OptimizationResult(
                weights = weights,
                expected_return = portfolio_return,
                volatility = portfolio_volatility,
                sharpe_ratio = sharpe_ratio,
                optimization_method="MAX_SHARPE",
                success = result.success,
                iterations = result.nit,
                objective_value = -result.fun,
                marginal_contributions = marginal_contributions,
                risk_contributions = risk_contributions,
                assets = list(returns.columns),
                calculation_time = time.time() - start_time,
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

            logger.info(
                f"Sharpe ratio optimization completed in {optimization_result.calculation_time:.3f}s"
            )
            return optimization_result

        except Exception as e:
            logger.error(f"Sharpe ratio optimization failed: {e}")
            raise

    def minimize_volatility(
        self, returns: pd.DataFrame, constraints: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """
        最小化波動率

        Args:
            returns: 資產回報率矩陣
            constraints: 約束條件

        Returns:
            OptimizationResult: 優化結果
        """
        start_time = time.time()

        try:
            logger.info(
                f"Starting volatility minimization for {returns.shape[1]} assets"
            )

            # 準備數據
            mean_returns, cov_matrix = self._prepare_data(returns)
            num_assets = len(mean_returns)

            # 構建約束條件
            constraints_list, bounds = self._build_constraints(num_assets, constraints)

            # 目標函數 (投資組合方差)
            def portfolio_variance(weights: np.ndarray) -> float:
                return np.dot(weights.T, np.dot(cov_matrix, weights))

            # 初始權重
            initial_weights = np.array([1.0 / num_assets] * num_assets)

            # 執行優化
            result = minimize(
                portfolio_variance,
                initial_weights,
                method="SLSQP",
                bounds = bounds,
                constraints = constraints_list,
                options={
                    "maxiter": self.config.max_iterations,
                    "ftol": self.config.tolerance,
                },
            )

            # 計算結果指標
            if result.success:
                weights = result.x
                portfolio_return = np.sum(mean_returns * weights)
                portfolio_variance = result.fun
                portfolio_volatility = np.sqrt(portfolio_variance)
                sharpe_ratio = (
                    portfolio_return - self.config.risk_free_rate
                ) / portfolio_volatility

                # 計算風險貢獻
                marginal_contributions = self._calculate_marginal_contributions(
                    weights, cov_matrix
                )
                risk_contributions = self._calculate_risk_contributions(
                    weights, cov_matrix
                )
            else:
                # 如果優化失敗，返回等權重
                weights = initial_weights
                portfolio_return = np.sum(mean_returns * weights)
                portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
                portfolio_volatility = np.sqrt(portfolio_variance)
                sharpe_ratio = (
                    portfolio_return - self.config.risk_free_rate
                ) / portfolio_volatility
                marginal_contributions = np.zeros(num_assets)
                risk_contributions = np.zeros(num_assets)

            # 創建結果
            optimization_result = OptimizationResult(
                weights = weights,
                expected_return = portfolio_return,
                volatility = portfolio_volatility,
                sharpe_ratio = sharpe_ratio,
                optimization_method="MIN_VOLATILITY",
                success = result.success,
                iterations = result.nit,
                objective_value = portfolio_variance,
                marginal_contributions = marginal_contributions,
                risk_contributions = risk_contributions,
                assets = list(returns.columns),
                calculation_time = time.time() - start_time,
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

            logger.info(
                f"Volatility minimization completed in {optimization_result.calculation_time:.3f}s"
            )
            return optimization_result

        except Exception as e:
            logger.error(f"Volatility minimization failed: {e}")
            raise

    def target_return_optimization(
        self,
        returns: pd.DataFrame,
        target_return: float,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> OptimizationResult:
        """
        目標回報率優化

        Args:
            returns: 資產回報率矩陣
            target_return: 目標回報率
            constraints: 約束條件

        Returns:
            OptimizationResult: 優化結果
        """
        start_time = time.time()

        try:
            logger.info(
                f"Starting target return optimization for {returns.shape[1]} assets"
            )

            # 準備數據
            mean_returns, cov_matrix = self._prepare_data(returns)
            num_assets = len(mean_returns)

            # 構建約束條件
            constraints_list, bounds = self._build_constraints(num_assets, constraints)

            # 添加目標回報率約束
            target_constraint = {
                "type": "eq",
                "fun": lambda weights: np.sum(mean_returns * weights) - target_return,
            }
            constraints_list.append(target_constraint)

            # 目標函數 (最小化方差)
            def portfolio_variance(weights: np.ndarray) -> float:
                return np.dot(weights.T, np.dot(cov_matrix, weights))

            # 初始權重
            initial_weights = np.array([1.0 / num_assets] * num_assets)

            # 執行優化
            result = minimize(
                portfolio_variance,
                initial_weights,
                method="SLSQP",
                bounds = bounds,
                constraints = constraints_list,
                options={
                    "maxiter": self.config.max_iterations,
                    "ftol": self.config.tolerance,
                },
            )

            # 計算結果指標
            if result.success:
                weights = result.x
                portfolio_return = np.sum(mean_returns * weights)
                portfolio_variance = result.fun
                portfolio_volatility = np.sqrt(portfolio_variance)
                sharpe_ratio = (
                    portfolio_return - self.config.risk_free_rate
                ) / portfolio_volatility

                # 計算風險貢獻
                marginal_contributions = self._calculate_marginal_contributions(
                    weights, cov_matrix
                )
                risk_contributions = self._calculate_risk_contributions(
                    weights, cov_matrix
                )
            else:
                # 如果優化失敗，返回等權重
                weights = initial_weights
                portfolio_return = np.sum(mean_returns * weights)
                portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
                portfolio_volatility = np.sqrt(portfolio_variance)
                sharpe_ratio = (
                    portfolio_return - self.config.risk_free_rate
                ) / portfolio_volatility
                marginal_contributions = np.zeros(num_assets)
                risk_contributions = np.zeros(num_assets)

            # 創建結果
            optimization_result = OptimizationResult(
                weights = weights,
                expected_return = portfolio_return,
                volatility = portfolio_volatility,
                sharpe_ratio = sharpe_ratio,
                optimization_method="TARGET_RETURN",
                success = result.success,
                iterations = result.nit,
                objective_value = portfolio_variance,
                marginal_contributions = marginal_contributions,
                risk_contributions = risk_contributions,
                assets = list(returns.columns),
                calculation_time = time.time() - start_time,
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

            logger.info(
                f"Target return optimization completed in {optimization_result.calculation_time:.3f}s"
            )
            return optimization_result

        except Exception as e:
            logger.error(f"Target return optimization failed: {e}")
            raise

    def risk_parity_optimization(
        self, returns: pd.DataFrame, constraints: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """
        風險平價優化

        Args:
            returns: 資產回報率矩陣
            constraints: 約束條件

        Returns:
            OptimizationResult: 優化結果
        """
        start_time = time.time()

        try:
            logger.info(
                f"Starting risk parity optimization for {returns.shape[1]} assets"
            )

            # 準備數據
            mean_returns, cov_matrix = self._prepare_data(returns)
            num_assets = len(mean_returns)

            # 構建約束條件
            constraints_list, bounds = self._build_constraints(num_assets, constraints)

            # 目標函數 (最小化風險貢獻的差異)
            def risk_parity_objective(weights: np.ndarray) -> float:
                # 計算邊際風險貢獻
                portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
                marginal_contributions = (
                    np.dot(cov_matrix, weights) / portfolio_variance
                )
                risk_contributions = weights * marginal_contributions

                # 計算風險貢獻的差異 (使用L2範數)
                target_risk = 1.0 / num_assets
                risk_parity_error = np.sum((risk_contributions - target_risk) ** 2)

                return risk_parity_error

            # 初始權重 (基於波動率的倒數)
            volatilities = np.sqrt(np.diag(cov_matrix))
            initial_weights = 1.0 / volatilities
            initial_weights = initial_weights / initial_weights.sum()

            # 執行優化
            result = minimize(
                risk_parity_objective,
                initial_weights,
                method="SLSQP",
                bounds = bounds,
                constraints = constraints_list,
                options={
                    "maxiter": self.config.max_iterations,
                    "ftol": self.config.tolerance,
                },
            )

            # 計算結果指標
            if result.success:
                weights = result.x
                portfolio_return = np.sum(mean_returns * weights)
                portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
                portfolio_volatility = np.sqrt(portfolio_variance)
                sharpe_ratio = (
                    portfolio_return - self.config.risk_free_rate
                ) / portfolio_volatility

                # 計算風險貢獻
                marginal_contributions = self._calculate_marginal_contributions(
                    weights, cov_matrix
                )
                risk_contributions = self._calculate_risk_contributions(
                    weights, cov_matrix
                )
            else:
                # 如果優化失敗，使用基於波動率的倒數
                weights = initial_weights
                portfolio_return = np.sum(mean_returns * weights)
                portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
                portfolio_volatility = np.sqrt(portfolio_variance)
                sharpe_ratio = (
                    portfolio_return - self.config.risk_free_rate
                ) / portfolio_volatility
                marginal_contributions = self._calculate_marginal_contributions(
                    weights, cov_matrix
                )
                risk_contributions = self._calculate_risk_contributions(
                    weights, cov_matrix
                )

            # 創建結果
            optimization_result = OptimizationResult(
                weights = weights,
                expected_return = portfolio_return,
                volatility = portfolio_volatility,
                sharpe_ratio = sharpe_ratio,
                optimization_method="RISK_PARITY",
                success = result.success,
                iterations = result.nit,
                objective_value = result.fun,
                marginal_contributions = marginal_contributions,
                risk_contributions = risk_contributions,
                assets = list(returns.columns),
                calculation_time = time.time() - start_time,
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

            logger.info(
                f"Risk parity optimization completed in {optimization_result.calculation_time:.3f}s"
            )
            return optimization_result

        except Exception as e:
            logger.error(f"Risk parity optimization failed: {e}")
            raise

    def _prepare_data(self, returns: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """準備優化數據"""
        # 移除NaN值
        returns_clean = returns.dropna()

        if len(returns_clean) == 0:
            raise ValueError("No valid return data after removing NaN values")

        # 年化回報率和協方差矩陣
        mean_returns = returns_clean.mean() * self.config.trading_days_per_year
        cov_matrix = returns_clean.cov() * self.config.trading_days_per_year

        # 正則化 (如果啟用)
        if self.config.enable_regularization:
            cov_matrix = cov_matrix + self.config.regularization * np.eye(
                len(mean_returns)
            )

        return mean_returns.values, cov_matrix.values

    def _build_constraints(
        self, num_assets: int, custom_constraints: Optional[Dict[str, Any]]
    ) -> Tuple[List[Dict], Any]:
        """構建優化約束條件"""
        constraints_list = []

        # 權重總和約束
        constraints_list.append(
            {
                "type": "eq",
                "fun": lambda weights: np.sum(weights) - self.config.weight_sum,
            }
        )

        # 邊界約束
        bounds = tuple(
            [
                (self.config.min_weight, self.config.max_weight)
                for _ in range(num_assets)
            ]
        )

        # 自定義約束
        if custom_constraints:
            # 最小 / 最大權重約束
            if "min_weight" in custom_constraints:
                min_weight = custom_constraints["min_weight"]
                bounds = tuple([(min_weight, b[1]) for b in bounds])

            if "max_weight" in custom_constraints:
                max_weight = custom_constraints["max_weight"]
                bounds = tuple([(b[0], max_weight) for b in bounds])

            # 行業約束 (如果提供)
            if "sector_constraints" in custom_constraints:
                sector_constraints = custom_constraints["sector_constraints"]
                for sector_info in sector_constraints:
                    sector_assets = sector_info["assets"]
                    sector_min = sector_info.get("min_weight", 0)
                    sector_max = sector_info.get("max_weight", 1)

                    # 創建行業權重約束
                    def sector_constraint(weights, assets_idx = sector_assets):
                        return np.sum(weights[assets_idx])

                    constraints_list.append(
                        {
                            "type": "ineq",
                            "fun": lambda w, idx = sector_assets: np.sum(w[idx])
                            - sector_min,
                        }
                    )

                    constraints_list.append(
                        {
                            "type": "ineq",
                            "fun": lambda w, idx = sector_assets, max_w = sector_max: max_w
                            - np.sum(w[idx]),
                        }
                    )

        return constraints_list, bounds

    def _calculate_marginal_contributions(
        self, weights: np.ndarray, cov_matrix: np.ndarray
    ) -> np.ndarray:
        """計算邊際風險貢獻"""
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
        if portfolio_variance < self.config.epsilon:
            return np.zeros_like(weights)

        marginal_contributions = np.dot(cov_matrix, weights) / portfolio_variance
        return marginal_contributions

    def _calculate_risk_contributions(
        self, weights: np.ndarray, cov_matrix: np.ndarray
    ) -> np.ndarray:
        """計算風險貢獻"""
        marginal_contributions = self._calculate_marginal_contributions(
            weights, cov_matrix
        )
        risk_contributions = weights * marginal_contributions

        # 正規化到1
        total_risk = np.sum(risk_contributions)
        if total_risk > self.config.epsilon:
            risk_contributions = risk_contributions / total_risk

        return risk_contributions


# 便利函數
def create_mpt_optimizer(config: Optional[MPTConfig] = None) -> MPTOptimizer:
    """創建MPT優化引擎"""
    return MPTOptimizer(config)


def optimize_maximum_sharpe(
    returns: pd.DataFrame, constraints: Optional[Dict[str, Any]] = None
) -> OptimizationResult:
    """便利函數：最大化夏普比率"""
    optimizer = MPTOptimizer()
    return optimizer.maximize_sharpe_ratio(returns, constraints)


def optimize_minimum_volatility(
    returns: pd.DataFrame, constraints: Optional[Dict[str, Any]] = None
) -> OptimizationResult:
    """便利函數：最小化波動率"""
    optimizer = MPTOptimizer()
    return optimizer.minimize_volatility(returns, constraints)

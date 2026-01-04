"""
Multi-Asset Portfolio Optimizer
多資產投資組合優化器

實現現代投資組合理論的多資產優化算法：
- Markowitz 均值-方差優化
- Black-Litterman 模型
- 風險平價 (Risk Parity)
- 最小方差組合
- 動態權重調整
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, date
from dataclasses import dataclass, field
from enum import Enum
import cvxpy as cp
from scipy import stats
from scipy.optimize import minimize

logger = logging.getLogger(__name__)


class OptimizationMethod(str, Enum):
    """優化方法枚舉"""
    MARKOWITZ = "markowitz"           # Markowitz 均值-方差優化
    BLACK_LITTERMAN = "black_litterman"  # Black-Litterman 模型
    RISK_PARITY = "risk_parity"        # 風險平價
    MIN_VARIANCE = "min_variance"      # 最小方差
    EQUAL_WEIGHT = "equal_weight"      # 等權重
    MAX_DIVERSIFICATION = "max_diversification"  # 最大分散化
    TARGET_RETURN = "target_return"    # 目標收益率
    TARGET_VOLATILITY = "target_volatility"  # 目標波動率


class RebalanceFrequency(str, Enum):
    """再平衡頻率"""
    DAILY = "D"
    WEEKLY = "W"
    MONTHLY = "M"
    QUARTERLY = "Q"
    YEARLY = "Y"


@dataclass
class OptimizationConstraints:
    """優化約束條件"""
    # 權重約束
    weight_bounds: Tuple[float, float] = (0.0, 1.0)  # 權重範圍
    max_weight_per_asset: Optional[float] = None     # 單個資產最大權重
    min_weight_per_asset: Optional[float] = None     # 單個資產最小權重

    # 行業約束
    sector_limits: Optional[Dict[str, float]] = None  # 行業權重限制
    sector_mappings: Optional[Dict[str, str]] = None  # 資產到行業的映射

    # 交易成本約束
    max_turnover: Optional[float] = None      # 最大周轉率
    transaction_cost: float = 0.001           # 交易成本

    # 其他約束
    leverage_limit: float = 1.0               # 槓桿限制
    cash_balance: float = 0.0                 # 現金持有比例


@dataclass
class BlackLittermanConfig:
    """Black-Litterman 模型配置"""
    # 預期收益率
    tau: float = 0.025  # 不確定性參數

    # 投資者觀點
    views: List[Dict[str, Any]] = field(default_factory=list)
    # 觀點格式: [{"assets": ["AAPL", "MSFT"], "weights": [0.6, 0.4], "confidence": 0.5}]

    # 優先股模型
    use_prior_returns: bool = True
    prior_weights: Optional[Dict[str, float]] = None  # 優先權重（如市值權重）


class MultiAssetOptimizer:
    """
    多資產投資組合優化器

    支持多種優化方法和約束條件
    """

    def __init__(
        self,
        method: OptimizationMethod = OptimizationMethod.MARKOWITZ,
        constraints: Optional[OptimizationConstraints] = None,
        risk_free_rate: float = 0.02,
        lookback_window: int = 252,
        rebalance_frequency: RebalanceFrequency = RebalanceFrequency.MONTHLY
    ):
        """
        初始化優化器

        Args:
            method: 優化方法
            constraints: 約束條件
            risk_free_rate: 無風險利率
            lookback_window: 回溯窗口（天數）
            rebalance_frequency: 再平衡頻率
        """
        self.method = method
        self.constraints = constraints or OptimizationConstraints()
        self.risk_free_rate = risk_free_rate
        self.lookback_window = lookback_window
        self.rebalance_frequency = rebalance_frequency

        # 內部狀態
        self.asset_returns: Optional[pd.DataFrame] = None
        self.expected_returns: Optional[pd.Series] = None
        self.covariance_matrix: Optional[pd.DataFrame] = None
        self.optimization_history: List[Dict[str, Any]] = []

        logger.info(f"Multi-Asset Optimizer initialized: method={method.value}")

    def prepare_data(
        self,
        price_data: Dict[str, pd.DataFrame],
        returns_column: str = 'close'
    ) -> None:
        """
        準備優化所需的數據

        Args:
            price_data: 資產價格數據字典
            returns_column: 用於計算收益率的列名
        """
        try:
            # 提取價格數據並計算收益率
            returns_data = {}
            dates = None

            for asset, df in price_data.items():
                if returns_column not in df.columns:
                    logger.error(f"Column '{returns_column}' not found for {asset}")
                    continue

                # 計算日收益率
                asset_returns = df[returns_column].pct_change().dropna()

                # 確保有足夠的數據
                if len(asset_returns) < self.lookback_window:
                    logger.warning(f"Insufficient data for {asset}: {len(asset_returns)} < {self.lookback_window}")
                    continue

                returns_data[asset] = asset_returns

                # 記錄日期範圍
                if dates is None:
                    dates = asset_returns.index
                else:
                    dates = dates.union(asset_returns.index)

            if not returns_data:
                raise ValueError("No valid returns data found")

            # 對齊所有資產的收益率
            self.asset_returns = pd.DataFrame(returns_data).reindex(dates).fillna(0)

            # 計算統計量
            self._calculate_statistics()

            logger.info(f"Data prepared for {len(returns_data)} assets")

        except Exception as e:
            logger.error(f"Data preparation failed: {e}")
            raise

    def _calculate_statistics(self) -> None:
        """計算預期收益率和協方差矩陣"""
        if self.asset_returns is None:
            raise ValueError("Asset returns not prepared")

        # 計算年化預期收益率（使用歷史平均）
        self.expected_returns = self.asset_returns.mean() * 252

        # 計算年化協方差矩陣
        self.covariance_matrix = self.asset_returns.cov() * 252

        # 處理數值問題
        np.fill_diagonal(self.covariance_matrix.values,
                        np.maximum(np.diag(self.covariance_matrix.values), 1e-6))

    def optimize_weights(
        self,
        target_return: Optional[float] = None,
        target_volatility: Optional[float] = None,
        current_weights: Optional[Dict[str, float]] = None,
        bl_config: Optional[BlackLittermanConfig] = None
    ) -> Dict[str, float]:
        """
        執行權重優化

        Args:
            target_return: 目標收益率（僅用於目標收益率優化）
            target_volatility: 目標波動率（僅用於目標波動率優化）
            current_weights: 當前權重（用於計算交易成本）
            bl_config: Black-Litterman 配置

        Returns:
            優化後的權重字典
        """
        try:
            if self.expected_returns is None or self.covariance_matrix is None:
                raise ValueError("Statistics not calculated. Call prepare_data first.")

            # 根據方法執行優化
            if self.method == OptimizationMethod.MARKOWITZ:
                weights = self._markowitz_optimization(target_return, target_volatility)
            elif self.method == OptimizationMethod.BLACK_LITTERMAN:
                weights = self._black_litterman_optimization(bl_config)
            elif self.method == OptimizationMethod.RISK_PARITY:
                weights = self._risk_parity_optimization()
            elif self.method == OptimizationMethod.MIN_VARIANCE:
                weights = self._min_variance_optimization()
            elif self.method == OptimizationMethod.EQUAL_WEIGHT:
                weights = self._equal_weight_optimization()
            elif self.method == OptimizationMethod.MAX_DIVERSIFICATION:
                weights = self._max_diversification_optimization()
            elif self.method == OptimizationMethod.TARGET_RETURN:
                if target_return is None:
                    raise ValueError("Target return required for target return optimization")
                weights = self._markowitz_optimization(target_return=target_return)
            elif self.method == OptimizationMethod.TARGET_VOLATILITY:
                if target_volatility is None:
                    raise ValueError("Target volatility required for target volatility optimization")
                weights = self._markowitz_optimization(target_volatility=target_volatility)
            else:
                raise ValueError(f"Unknown optimization method: {self.method}")

            # 應用約束條件
            weights = self._apply_constraints(weights)

            # 計算交易成本
            if current_weights:
                turnover = self._calculate_turnover(current_weights, weights)
                weights = self._adjust_for_transaction_costs(weights, turnover)

            # 記錄優化歷史
            self.optimization_history.append({
                'timestamp': datetime.now(),
                'method': self.method.value,
                'weights': weights.copy(),
                'expected_return': self._calculate_portfolio_return(weights),
                'volatility': self._calculate_portfolio_volatility(weights),
                'sharpe_ratio': self._calculate_sharpe_ratio(weights)
            })

            logger.info(f"Optimization completed: {len(weights)} assets")
            return weights

        except Exception as e:
            logger.error(f"Weight optimization failed: {e}")
            raise

    def _markowitz_optimization(
        self,
        target_return: Optional[float] = None,
        target_volatility: Optional[float] = None
    ) -> Dict[str, float]:
        """Markowitz 均值-方差優化"""
        n_assets = len(self.expected_returns)
        assets = list(self.expected_returns.index)

        # 優化變量
        weights = cp.Variable(n_assets)

        # 目標函數
        portfolio_return = weights.T @ self.expected_returns.values
        portfolio_variance = cp.quad_form(weights, self.covariance_matrix.values)
        portfolio_volatility = cp.sqrt(portfolio_variance)

        if target_return is not None:
            # 目標收益率約束下的最小方差
            objective = cp.Minimize(portfolio_variance)
            constraints = [
                weights >= self.constraints.weight_bounds[0],
                weights <= self.constraints.weight_bounds[1],
                cp.sum(weights) == 1 - self.constraints.cash_balance,
                portfolio_return >= target_return
            ]
        elif target_volatility is not None:
            # 目標波動率約束下的最大收益率
            objective = cp.Maximize(portfolio_return)
            constraints = [
                weights >= self.constraints.weight_bounds[0],
                weights <= self.constraints.weight_bounds[1],
                cp.sum(weights) == 1 - self.constraints.cash_balance,
                portfolio_volatility <= target_volatility
            ]
        else:
            # 最大夏普比率
            objective = cp.Maximize((portfolio_return - self.risk_free_rate) / portfolio_volatility)
            constraints = [
                weights >= self.constraints.weight_bounds[0],
                weights <= self.constraints.weight_bounds[1],
                cp.sum(weights) == 1 - self.constraints.cash_balance
            ]

        # 添加其他約束
        if self.constraints.max_weight_per_asset:
            constraints.append(weights <= self.constraints.max_weight_per_asset)

        if self.constraints.min_weight_per_asset:
            constraints.append(weights >= self.constraints.min_weight_per_asset)

        # 求解優化問題
        problem = cp.Problem(objective, constraints)
        problem.solve(solver=cp.ECOS)

        if problem.status != cp.OPTIMAL:
            logger.warning("Optimization did not converge to optimal solution")
            # 返回等權重作為後備
            return self._equal_weight_optimization()

        # 提取權重
        optimal_weights = weights.value
        return dict(zip(assets, optimal_weights))

    def _black_litterman_optimization(
        self,
        config: Optional[BlackLittermanConfig] = None
    ) -> Dict[str, float]:
        """Black-Litterman 模型優化"""
        if config is None:
            config = BlackLittermanConfig()

        n_assets = len(self.expected_returns)
        assets = list(self.expected_returns.index)

        # 優先收益（使用 CAPM 或歷史收益）
        if config.use_prior_returns:
            pi = self.expected_returns.values
        elif config.prior_weights:
            # 使用市值權重計算隱含收益率
            w_prior = np.array([config.prior_weights.get(asset, 0) for asset in assets])
            pi = self.risk_free_rate + 0.5 * self.covariance_matrix.values @ w_prior
        else:
            pi = self.expected_returns.values

        # 構建觀點矩陣
        if not config.views:
            # 如果沒有觀點，使用優先收益
            bl_returns = pd.Series(pi, index=assets)
        else:
            P = []  # 觀點矩陣
            q = []  # 預期收益率
            Omega = []  # 觀點不確定性矩陣

            for view in config.views:
                # 創建觀點向量
                p_vec = np.zeros(n_assets)
                view_assets = view['assets']
                view_weights = view['weights']

                for asset, weight in zip(view_assets, view_weights):
                    if asset in assets:
                        p_vec[assets.index(asset)] = weight

                P.append(p_vec)
                q.append(view.get('expected_return', 0))

                # 計算觀點不確定性
                confidence = view.get('confidence', 0.5)
                omega = (1 / confidence - 1) * p_vec @ self.covariance_matrix.values @ p_vec.T
                Omega.append(omega)

            P = np.array(P)
            q = np.array(q)
            Omega = np.diag(Omega)

            # Black-Litterman 公式
            tau = config.tau
            tau_sigma = tau * self.covariance_matrix.values

            # 計算 Black-Litterman 收益率
            M_inv = np.linalg.inv(tau_sigma) + P.T @ np.linalg.inv(Omega) @ P
            bl_returns_array = M_inv @ (
                np.linalg.inv(tau_sigma) @ pi + P.T @ np.linalg.inv(Omega) @ q
            )
            bl_returns = pd.Series(bl_returns_array, index=assets)

        # 使用 Black-Litterman 收益率進行 Markowitz 優化
        self.expected_returns = bl_returns
        return self._markowitz_optimization()

    def _risk_parity_optimization(self) -> Dict[str, float]:
        """風險平價優化"""
        n_assets = len(self.expected_returns)
        assets = list(self.expected_returns.index)

        def risk_parity_objective(weights):
            """風險平價目標函數"""
            weights = np.maximum(weights, 1e-8)  # 避免負權重

            # 計算邊際風險貢獻
            portfolio_vol = np.sqrt(weights @ self.covariance_matrix.values @ weights)
            marginal_contrib = self.covariance_matrix.values @ weights / portfolio_vol
            risk_contrib = weights * marginal_contrib
            risk_contrib_pct = risk_contrib / risk_contrib.sum()

            # 目標：使所有資產的風險貢獻相等
            target_risk = 1.0 / n_assets
            return np.sum((risk_contrib_pct - target_risk) ** 2) * 10000

        # 優化約束
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}  # 權重和為1
        ]

        bounds = self.constraints.weight_bounds
        bounds = [bounds] * n_assets

        # 初始權重（等權重）
        x0 = np.array([1.0 / n_assets] * n_assets)

        # 執行優化
        result = minimize(
            risk_parity_objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        if not result.success:
            logger.warning(f"Risk parity optimization failed: {result.message}")
            return self._equal_weight_optimization()

        return dict(zip(assets, result.x))

    def _min_variance_optimization(self) -> Dict[str, float]:
        """最小方差優化"""
        n_assets = len(self.expected_returns)
        assets = list(self.expected_returns.index)

        # 優化變量
        weights = cp.Variable(n_assets)

        # 目標函數：最小化方差
        portfolio_variance = cp.quad_form(weights, self.covariance_matrix.values)
        objective = cp.Minimize(portfolio_variance)

        # 約束條件
        constraints = [
            weights >= self.constraints.weight_bounds[0],
            weights <= self.constraints.weight_bounds[1],
            cp.sum(weights) == 1 - self.constraints.cash_balance
        ]

        # 求解優化問題
        problem = cp.Problem(objective, constraints)
        problem.solve(solver=cp.ECOS)

        if problem.status != cp.OPTIMAL:
            logger.warning("Min variance optimization did not converge")
            return self._equal_weight_optimization()

        optimal_weights = weights.value
        return dict(zip(assets, optimal_weights))

    def _equal_weight_optimization(self) -> Dict[str, float]:
        """等權重優化"""
        n_assets = len(self.expected_returns)
        assets = list(self.expected_returns.index)
        weight = (1 - self.constraints.cash_balance) / n_assets

        return {asset: weight for asset in assets}

    def _max_diversification_optimization(self) -> Dict[str, float]:
        """最大分散化優化"""
        n_assets = len(self.expected_returns)
        assets = list(self.expected_returns.index)

        # 計算資產波動率
        volatilities = np.sqrt(np.diag(self.covariance_matrix.values))

        # 優化變量
        weights = cp.Variable(n_assets)

        # 計算投資組合波動率和加權平均資產波動率
        portfolio_volatility = cp.sqrt(cp.quad_form(weights, self.covariance_matrix.values))
        weighted_avg_vol = weights.T @ volatilities

        # 目標函數：最大化分散化比率
        objective = cp.Maximize(weighted_avg_vol / portfolio_volatility)

        # 約束條件
        constraints = [
            weights >= self.constraints.weight_bounds[0],
            weights <= self.constraints.weight_bounds[1],
            cp.sum(weights) == 1 - self.constraints.cash_balance
        ]

        # 求解優化問題
        problem = cp.Problem(objective, constraints)
        problem.solve(solver=cp.ECOS)

        if problem.status != cp.OPTIMAL:
            logger.warning("Max diversification optimization did not converge")
            return self._equal_weight_optimization()

        optimal_weights = weights.value
        return dict(zip(assets, optimal_weights))

    def _apply_constraints(self, weights: Dict[str, float]) -> Dict[str, float]:
        """應用約束條件"""
        # 權重邊界
        for asset in weights:
            weights[asset] = np.clip(
                weights[asset],
                self.constraints.weight_bounds[0],
                self.constraints.weight_bounds[1]
            )

        # 單個資產權重限制
        if self.constraints.max_weight_per_asset:
            for asset in weights:
                weights[asset] = min(weights[asset], self.constraints.max_weight_per_asset)

        if self.constraints.min_weight_per_asset:
            for asset in weights:
                weights[asset] = max(weights[asset], self.constraints.min_weight_per_asset)

        # 行業限制
        if self.constraints.sector_limits and self.constraints.sector_mappings:
            weights = self._apply_sector_constraints(weights)

        # 正規化權重
        total_weight = sum(weights.values())
        if total_weight > 0:
            for asset in weights:
                weights[asset] /= total_weight
        else:
            # 如果所有權重為0，返回等權重
            return self._equal_weight_optimization()

        return weights

    def _apply_sector_constraints(self, weights: Dict[str, float]) -> Dict[str, float]:
        """應用行業約束"""
        # 計算每個行業的總權重
        sector_weights = {}
        for asset, weight in weights.items():
            sector = self.constraints.sector_mappings.get(asset, 'Other')
            sector_weights[sector] = sector_weights.get(sector, 0) + weight

        # 檢查並調整超限的行業
        for sector, current_weight in sector_weights.items():
            limit = self.constraints.sector_limits.get(sector)
            if limit and current_weight > limit:
                # 按比例減少該行業所有資產的權重
                scale_factor = limit / current_weight
                for asset in weights:
                    if self.constraints.sector_mappings.get(asset, 'Other') == sector:
                        weights[asset] *= scale_factor

        return weights

    def _calculate_turnover(
        self,
        current_weights: Dict[str, float],
        new_weights: Dict[str, float]
    ) -> float:
        """計算組合周轉率"""
        turnover = 0.0
        all_assets = set(current_weights.keys()) | set(new_weights.keys())

        for asset in all_assets:
            current = current_weights.get(asset, 0)
            new = new_weights.get(asset, 0)
            turnover += abs(new - current)

        return turnover / 2  # 除以2因為買賣是對稱的

    def _adjust_for_transaction_costs(
        self,
        weights: Dict[str, float],
        turnover: float
    ) -> Dict[str, float]:
        """調整權重以考慮交易成本"""
        if self.constraints.max_turnover and turnover > self.constraints.max_turnover:
            # 按比例減少權重變化
            scale_factor = self.constraints.max_turnover / turnover
            # 這裡簡化處理，實際實現需要更複雜的邏輯
            logger.warning(f"Turnover {turnover:.2%} exceeds limit {self.constraints.max_turnover:.2%}")

        return weights

    def _calculate_portfolio_return(self, weights: Dict[str, float]) -> float:
        """計算投資組合預期收益率"""
        if not weights or self.expected_returns is None:
            return 0.0

        portfolio_return = 0.0
        for asset, weight in weights.items():
            if asset in self.expected_returns:
                portfolio_return += weight * self.expected_returns[asset]

        return portfolio_return

    def _calculate_portfolio_volatility(self, weights: Dict[str, float]) -> float:
        """計算投資組合波動率"""
        if not weights or self.covariance_matrix is None:
            return 0.0

        assets = list(weights.keys())
        weights_array = np.array([weights[asset] for asset in assets])

        # 提取相關的協方差矩陣
        cov_subset = self.covariance_matrix.loc[assets, assets]

        # 計算投資組合方差
        portfolio_variance = weights_array @ cov_subset.values @ weights_array

        return np.sqrt(portfolio_variance)

    def _calculate_sharpe_ratio(self, weights: Dict[str, float]) -> float:
        """計算夏普比率"""
        portfolio_return = self._calculate_portfolio_return(weights)
        portfolio_volatility = self._calculate_portfolio_volatility(weights)

        if portfolio_volatility == 0:
            return 0.0

        return (portfolio_return - self.risk_free_rate) / portfolio_volatility

    def calculate_correlation_matrix(self) -> pd.DataFrame:
        """計算資產相關性矩陣"""
        if self.asset_returns is None:
            raise ValueError("Asset returns not prepared")

        return self.asset_returns.corr()

    def get_efficient_frontier(
        self,
        num_portfolios: int = 100,
        target_returns: Optional[List[float]] = None
    ) -> pd.DataFrame:
        """
        計算有效前沿

        Args:
            num_portfolios: 投資組合數量
            target_returns: 目標收益率列表（可選）

        Returns:
            包含有效前沿點的DataFrame
        """
        if target_returns is None:
            # 生成目標收益率範圍
            min_return = self.expected_returns.min()
            max_return = self.expected_returns.max()
            target_returns = np.linspace(min_return, max_return, num_portfolios)

        efficient_points = []

        for target_return in target_returns:
            try:
                weights = self._markowitz_optimization(target_return=target_return)
                portfolio_return = self._calculate_portfolio_return(weights)
                portfolio_volatility = self._calculate_portfolio_volatility(weights)
                sharpe_ratio = self._calculate_sharpe_ratio(weights)

                efficient_points.append({
                    'target_return': target_return,
                    'actual_return': portfolio_return,
                    'volatility': portfolio_volatility,
                    'sharpe_ratio': sharpe_ratio,
                    'weights': weights.copy()
                })
            except Exception as e:
                logger.warning(f"Failed to calculate efficient point for return {target_return}: {e}")
                continue

        return pd.DataFrame(efficient_points)

    def get_optimization_summary(self) -> Dict[str, Any]:
        """獲取優化結果摘要"""
        if not self.optimization_history:
            return {}

        latest = self.optimization_history[-1]

        return {
            'method': latest['method'],
            'weights': latest['weights'],
            'expected_return': latest['expected_return'],
            'volatility': latest['volatility'],
            'sharpe_ratio': latest['sharpe_ratio'],
            'num_assets': len(latest['weights']),
            'optimization_time': latest['timestamp'].isoformat(),
            'constraints': {
                'weight_bounds': self.constraints.weight_bounds,
                'max_weight_per_asset': self.constraints.max_weight_per_asset,
                'sector_limits': self.constraints.sector_limits,
                'max_turnover': self.constraints.max_turnover
            }
        }

    def analyze_risk_contributions(
        self,
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        """分析各資產的風險貢獻"""
        if self.covariance_matrix is None:
            raise ValueError("Covariance matrix not calculated")

        assets = list(weights.keys())
        weights_array = np.array([weights[asset] for asset in assets])
        cov_subset = self.covariance_matrix.loc[assets, assets]

        # 計算邊際風險貢獻
        portfolio_volatility = np.sqrt(weights_array @ cov_subset.values @ weights_array)
        marginal_contrib = cov_subset.values @ weights_array / portfolio_volatility

        # 計算絕對風險貢獻
        risk_contrib = weights_array * marginal_contrib

        # 轉換為百分比
        risk_contrib_pct = risk_contrib / risk_contrib.sum()

        return dict(zip(assets, risk_contrib_pct))

    def backtest_dynamic_allocation(
        self,
        price_data: Dict[str, pd.DataFrame],
        rebalance_dates: Optional[List[datetime]] = None
    ) -> pd.DataFrame:
        """
        回測動態權重調整策略

        Args:
            price_data: 價格數據
            rebalance_dates: 再平衡日期列表（可選）

        Returns:
            回測結果DataFrame
        """
        # 準備數據
        self.prepare_data(price_data)

        # 確定再平衡日期
        if rebalance_dates is None:
            # 根據頻率生成再平衡日期
            all_dates = self.asset_returns.index
            if self.rebalance_frequency == RebalanceFrequency.MONTHLY:
                rebalance_dates = all_dates[all_dates.day == 1]
            elif self.rebalance_frequency == RebalanceFrequency.QUARTERLY:
                rebalance_dates = all_dates[(all_dates.month % 3 == 1) & (all_dates.day == 1)]
            else:
                rebalance_dates = all_dates[::30]  # 每30天

        # 執行回測
        weights_history = []
        performance_history = []

        current_weights = None
        portfolio_value = 1.0

        for date in rebalance_dates:
            # 獲取歷史數據
            end_date = date
            start_date = end_date - pd.Timedelta(days=self.lookback_window)

            historical_data = {}
            for asset, df in price_data.items():
                historical_data[asset] = df.loc[start_date:end_date]

            # 準備數據
            self.prepare_data(historical_data)

            # 優化權重
            new_weights = self.optimize_weights(current_weights=current_weights)

            # 記錄權重
            weights_history.append({
                'date': date,
                'weights': new_weights.copy()
            })

            # 計算投資組合收益（簡化版本）
            portfolio_return = 0.0
            for asset, weight in new_weights.items():
                if asset in price_data and date in price_data[asset].index:
                    asset_return = price_data[asset].loc[date, 'close'] / price_data[asset].loc[date, 'close'] - 1
                    portfolio_return += weight * asset_return

            portfolio_value *= (1 + portfolio_return)

            performance_history.append({
                'date': date,
                'portfolio_value': portfolio_value,
                'portfolio_return': portfolio_return
            })

            current_weights = new_weights

        # 合併結果
        weights_df = pd.DataFrame(weights_history).set_index('date')
        performance_df = pd.DataFrame(performance_history).set_index('date')

        return pd.concat([weights_df, performance_df], axis=1)
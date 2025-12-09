"""
港股量化交易 AI Agent 系统 - 风险预算系统

实现风险预算计算、动态资产配置和风险分配管理。
确保投资组合在风险预算约束下实现最优配置。
"""

import asyncio
import logging
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from ...models.base import BaseModel


class RiskBudgetMethod(str, Enum):
    """风险预算方法"""

    EQUAL_RISK_CONTRIBUTION = "equal_risk_contribution"
    MAXIMUM_SHARPE = "maximum_sharpe"
    MINIMUM_VARIANCE = "minimum_variance"
    RISK_PARITY = "risk_parity"


@dataclass
class RiskBudgetConfig:
    """风险预算配置"""

    # 风险预算方法
    method: RiskBudgetMethod = RiskBudgetMethod.EQUAL_RISK_CONTRIBUTION

    # 风险预算参数
    target_volatility: float = 0.12  # 目标年化波动率
    risk_budget_tolerance: float = 0.02  # 风险预算容忍度

    # 资产约束
    max_weight: float = 0.4  # 单一资产最大权重
    min_weight: float = 0.01  # 单一资产最小权重

    # 再平衡参数
    rebalance_threshold: float = 0.05  # 再平衡触发阈值
    rebalance_frequency: int = 30  # 再平衡频率（天）

    # 风险控制
    max_var: float = 0.05  # 最大VaR限制
    max_drawdown: float = 0.15  # 最大回撤限制

    # 计算参数
    lookback_period: int = 252  # 回望期（交易日）
    correlation_window: int = 60  # 相关性计算窗口


@dataclass
class AssetRiskMetrics(BaseModel):
    """资产风险指标"""

    symbol: str
    weight: float
    expected_return: float
    volatility: float
    risk_contribution: float
    marginal_risk_contribution: float
    sharpe_ratio: float
    var_95: float
    var_99: float


@dataclass
class RiskBudgetResult(BaseModel):
    """风险预算结果"""

    portfolio_id: str
    timestamp: datetime
    target_weights: Dict[str, float]
    risk_budget: Dict[str, float]
    portfolio_volatility: float
    portfolio_return: float
    portfolio_sharpe: float
    risk_contributions: Dict[str, float]
    asset_metrics: List[AssetRiskMetrics]
    optimization_status: str
    optimization_message: str


class RiskBudgetOptimizer:
    """风险预算优化器"""

    def __init__(self, config: RiskBudgetConfig):
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.risk_budget.optimizer")

    def optimize_risk_budget(
        self, returns: pd.DataFrame, risk_budgets: Dict[str, float]
    ) -> Tuple[Dict[str, float], str, str]:
        """优化风险预算配置"""

        try:
            # 计算协方差矩阵
            cov_matrix = returns.cov() * 252  # 年化协方差

            # 获取资产列表
            assets = returns.columns.tolist()
            n_assets = len(assets)

            # 设置优化目标函数
            if self.config.method == RiskBudgetMethod.EQUAL_RISK_CONTRIBUTION:
                result = self._optimize_equal_risk_contribution(
                    cov_matrix, assets, risk_budgets
                )
            elif self.config.method == RiskBudgetMethod.MAXIMUM_SHARPE:
                result = self._optimize_maximum_sharpe(cov_matrix, assets, returns)
            elif self.config.method == RiskBudgetMethod.MINIMUM_VARIANCE:
                result = self._optimize_minimum_variance(cov_matrix, assets)
            elif self.config.method == RiskBudgetMethod.RISK_PARITY:
                result = self._optimize_risk_parity(cov_matrix, assets)
            else:
                raise ValueError(f"未知的风险预算方法: {self.config.method}")

            return result

        except Exception as exc:
            self.logger.error(f"风险预算优化失败: {exc}")
            return {}, "failed", str(exc)

    def _optimize_equal_risk_contribution(
        self,
        cov_matrix: pd.DataFrame,
        assets: List[str],
        risk_budgets: Dict[str, float],
    ) -> Tuple[Dict[str, float], str, str]:
        """等风险贡献优化"""

        n_assets = len(assets)

        def objective(weights):
            """目标函数：最小化风险贡献的差异"""
            portfolio_var = np.dot(weights, np.dot(cov_matrix.values, weights))
            marginal_contrib = np.dot(cov_matrix.values, weights)
            risk_contrib = weights * marginal_contrib / portfolio_var

            # 计算与目标风险预算的差异
            target_contrib = np.array(
                [risk_budgets.get(asset, 1.0 / n_assets) for asset in assets]
            )
            diff = risk_contrib - target_contrib
            return np.sum(diff ** 2)

        # 约束条件
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]  # 权重和为1

        # 边界条件
        bounds = [
            (self.config.min_weight, self.config.max_weight) for _ in range(n_assets)
        ]

        # 初始权重（等权重）
        x0 = np.array([1.0 / n_assets] * n_assets)

        # 优化
        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000},
        )

        if result.success:
            weights = {asset: weight for asset, weight in zip(assets, result.x)}
            return weights, "success", "等风险贡献优化成功"
        else:
            return {}, "failed", result.message

    def _optimize_maximum_sharpe(
        self, cov_matrix: pd.DataFrame, assets: List[str], returns: pd.DataFrame
    ) -> Tuple[Dict[str, float], str, str]:
        """最大夏普比率优化"""

        n_assets = len(assets)
        expected_returns = returns.mean() * 252  # 年化收益

        def negative_sharpe(weights):
            """负夏普比率（用于最小化）"""
            portfolio_return = np.dot(weights, expected_returns.values)
            portfolio_var = np.dot(weights, np.dot(cov_matrix.values, weights))
            if portfolio_var <= 0:
                return -np.inf
            sharpe = portfolio_return / np.sqrt(portfolio_var)
            return -sharpe

        # 约束条件
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

        # 边界条件
        bounds = [
            (self.config.min_weight, self.config.max_weight) for _ in range(n_assets)
        ]

        # 初始权重
        x0 = np.array([1.0 / n_assets] * n_assets)

        # 优化
        result = minimize(
            negative_sharpe,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000},
        )

        if result.success:
            weights = {asset: weight for asset, weight in zip(assets, result.x)}
            return weights, "success", "最大夏普比率优化成功"
        else:
            return {}, "failed", result.message

    def _optimize_minimum_variance(
        self, cov_matrix: pd.DataFrame, assets: List[str]
    ) -> Tuple[Dict[str, float], str, str]:
        """最小方差优化"""

        n_assets = len(assets)

        def portfolio_variance(weights):
            """投资组合方差"""
            return np.dot(weights, np.dot(cov_matrix.values, weights))

        # 约束条件
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

        # 边界条件
        bounds = [
            (self.config.min_weight, self.config.max_weight) for _ in range(n_assets)
        ]

        # 初始权重
        x0 = np.array([1.0 / n_assets] * n_assets)

        # 优化
        result = minimize(
            portfolio_variance,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000},
        )

        if result.success:
            weights = {asset: weight for asset, weight in zip(assets, result.x)}
            return weights, "success", "最小方差优化成功"
        else:
            return {}, "failed", result.message

    def _optimize_risk_parity(
        self, cov_matrix: pd.DataFrame, assets: List[str]
    ) -> Tuple[Dict[str, float], str, str]:
        """风险平价优化"""

        n_assets = len(assets)

        def risk_parity_objective(weights):
            """风险平价目标函数"""
            portfolio_var = np.dot(weights, np.dot(cov_matrix.values, weights))
            marginal_contrib = np.dot(cov_matrix.values, weights)
            risk_contrib = weights * marginal_contrib / portfolio_var

            # 最小化风险贡献的方差
            return np.var(risk_contrib)

        # 约束条件
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

        # 边界条件
        bounds = [
            (self.config.min_weight, self.config.max_weight) for _ in range(n_assets)
        ]

        # 初始权重
        x0 = np.array([1.0 / n_assets] * n_assets)

        # 优化
        result = minimize(
            risk_parity_objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000},
        )

        if result.success:
            weights = {asset: weight for asset, weight in zip(assets, result.x)}
            return weights, "success", "风险平价优化成功"
        else:
            return {}, "failed", result.message


class DynamicRebalancer:
    """动态再平衡器"""

    def __init__(self, config: RiskBudgetConfig):
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.risk_budget.rebalancer")
        self.last_rebalance_date = None
        self.current_weights = {}
        self.target_weights = {}

    def should_rebalance(self, current_weights: Dict[str, float]) -> bool:
        """判断是否需要再平衡"""

        if not self.target_weights:
            return True

        # 检查时间间隔
        if self.last_rebalance_date:
            days_since_rebalance = (datetime.now() - self.last_rebalance_date).days
            if days_since_rebalance < self.config.rebalance_frequency:
                return False

        # 检查权重偏离
        total_deviation = 0.0
        for asset, current_weight in current_weights.items():
            target_weight = self.target_weights.get(asset, 0.0)
            deviation = abs(current_weight - target_weight)
            total_deviation += deviation

        return total_deviation > self.config.rebalance_threshold

    def calculate_rebalance_trades(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        portfolio_value: float,
    ) -> Dict[str, float]:
        """计算再平衡交易"""

        trades = {}

        # 获取所有资产
        all_assets = set(current_weights.keys()) | set(target_weights.keys())

        for asset in all_assets:
            current_weight = current_weights.get(asset, 0.0)
            target_weight = target_weights.get(asset, 0.0)

            weight_change = target_weight - current_weight
            trade_amount = weight_change * portfolio_value

            if abs(trade_amount) > 0.01:  # 忽略微小交易
                trades[asset] = trade_amount

        return trades

    def update_rebalance_status(self, target_weights: Dict[str, float]):
        """更新再平衡状态"""
        self.target_weights = target_weights.copy()
        self.last_rebalance_date = datetime.now()


class RiskBudgetSystem:
    """风险预算系统主类"""

    def __init__(self, config: RiskBudgetConfig):
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.risk_budget")
        self.optimizer = RiskBudgetOptimizer(config)
        self.rebalancer = DynamicRebalancer(config)
        self.risk_data_cache = {}

    async def calculate_risk_budget(
        self,
        portfolio_id: str,
        market_data: pd.DataFrame,
        current_weights: Optional[Dict[str, float]] = None,
    ) -> RiskBudgetResult:
        """计算风险预算"""

        try:
            # 准备数据
            returns = self._prepare_returns_data(market_data)

            # 计算风险预算
            risk_budgets = self._calculate_risk_budgets(returns)

            # 优化资产配置
            optimal_weights, status, message = self.optimizer.optimize_risk_budget(
                returns, risk_budgets
            )

            # 计算资产风险指标
            asset_metrics = self._calculate_asset_metrics(returns, optimal_weights)

            # 计算投资组合指标
            portfolio_metrics = self._calculate_portfolio_metrics(
                returns, optimal_weights
            )

            # 计算风险贡献
            risk_contributions = self._calculate_risk_contributions(
                returns, optimal_weights
            )

            result = RiskBudgetResult(
                id=f"risk_budget_{portfolio_id}_{datetime.now().timestamp()}",
                portfolio_id=portfolio_id,
                timestamp=datetime.now(),
                target_weights=optimal_weights,
                risk_budget=risk_budgets,
                portfolio_volatility=portfolio_metrics["volatility"],
                portfolio_return=portfolio_metrics["expected_return"],
                portfolio_sharpe=portfolio_metrics["sharpe_ratio"],
                risk_contributions=risk_contributions,
                asset_metrics=asset_metrics,
                optimization_status=status,
                optimization_message=message,
            )

            # 更新再平衡器状态
            self.rebalancer.update_rebalance_status(optimal_weights)

            self.logger.info(
                f"风险预算计算完成: {portfolio_id}, 状态: {status}, "
                f"组合波动率: {portfolio_metrics['volatility']:.4f}, "
                f"夏普比率: {portfolio_metrics['sharpe_ratio']:.4f}"
            )

            return result

        except Exception as exc:
            self.logger.error(f"风险预算计算失败: {exc}")
            # 返回空结果
            return RiskBudgetResult(
                id=f"risk_budget_error_{datetime.now().timestamp()}",
                portfolio_id=portfolio_id,
                timestamp=datetime.now(),
                target_weights={},
                risk_budget={},
                portfolio_volatility=0.0,
                portfolio_return=0.0,
                portfolio_sharpe=0.0,
                risk_contributions={},
                asset_metrics=[],
                optimization_status="error",
                optimization_message=str(exc),
            )

    def _prepare_returns_data(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """准备收益率数据"""

        # 计算收益率
        returns = market_data.pct_change().dropna()

        # 限制回望期
        if len(returns) > self.config.lookback_period:
            returns = returns.tail(self.config.lookback_period)

        # 处理异常值
        returns = returns.clip(lower=-0.2, upper=0.2)  # 限制单日涨跌幅

        return returns

    def _calculate_risk_budgets(self, returns: pd.DataFrame) -> Dict[str, float]:
        """计算风险预算"""

        assets = returns.columns.tolist()
        n_assets = len(assets)

        if self.config.method == RiskBudgetMethod.EQUAL_RISK_CONTRIBUTION:
            # 等风险贡献
            return {asset: 1.0 / n_assets for asset in assets}
        elif self.config.method == RiskBudgetMethod.RISK_PARITY:
            # 风险平价
            return {asset: 1.0 / n_assets for asset in assets}
        else:
            # 其他方法使用等权重风险预算
            return {asset: 1.0 / n_assets for asset in assets}

    def _calculate_asset_metrics(
        self, returns: pd.DataFrame, weights: Dict[str, float]
    ) -> List[AssetRiskMetrics]:
        """计算资产风险指标"""

        asset_metrics = []
        cov_matrix = returns.cov() * 252  # 年化协方差
        expected_returns = returns.mean() * 252  # 年化收益

        for symbol in returns.columns:
            weight = weights.get(symbol, 0.0)
            expected_return = expected_returns[symbol]
            volatility = np.sqrt(cov_matrix.loc[symbol, symbol])

            # 计算风险贡献
            portfolio_var = np.dot(
                list(weights.values()),
                np.dot(cov_matrix.values, list(weights.values())),
            )
            marginal_contrib = np.dot(
                cov_matrix.loc[symbol, :].values, list(weights.values())
            )
            risk_contrib = (
                weight * marginal_contrib / portfolio_var if portfolio_var > 0 else 0
            )

            # 计算夏普比率（假设无风险利率为2%）
            sharpe_ratio = (
                (expected_return - 0.02) / volatility if volatility > 0 else 0
            )

            # 计算VaR
            var_95 = np.percentile(returns[symbol], 5) * np.sqrt(252)
            var_99 = np.percentile(returns[symbol], 1) * np.sqrt(252)

            asset_metrics.append(
                AssetRiskMetrics(
                    id=f"asset_metrics_{symbol}_{datetime.now().timestamp()}",
                    symbol=symbol,
                    weight=weight,
                    expected_return=expected_return,
                    volatility=volatility,
                    risk_contribution=risk_contrib,
                    marginal_risk_contribution=marginal_contrib,
                    sharpe_ratio=sharpe_ratio,
                    var_95=var_95,
                    var_99=var_99,
                    timestamp=datetime.now(),
                )
            )

        return asset_metrics

    def _calculate_portfolio_metrics(
        self, returns: pd.DataFrame, weights: Dict[str, float]
    ) -> Dict[str, float]:
        """计算投资组合指标"""

        # 计算投资组合收益率
        portfolio_returns = (returns * pd.Series(weights)).sum(axis=1)

        # 计算年化收益和波动率
        expected_return = portfolio_returns.mean() * 252
        volatility = portfolio_returns.std() * np.sqrt(252)

        # 计算夏普比率
        sharpe_ratio = (expected_return - 0.02) / volatility if volatility > 0 else 0

        return {
            "expected_return": expected_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
        }

    def _calculate_risk_contributions(
        self, returns: pd.DataFrame, weights: Dict[str, float]
    ) -> Dict[str, float]:
        """计算风险贡献"""

        cov_matrix = returns.cov() * 252
        portfolio_var = np.dot(
            list(weights.values()), np.dot(cov_matrix.values, list(weights.values()))
        )

        risk_contributions = {}
        for symbol, weight in weights.items():
            marginal_contrib = np.dot(
                cov_matrix.loc[symbol, :].values, list(weights.values())
            )
            risk_contrib = (
                weight * marginal_contrib / portfolio_var if portfolio_var > 0 else 0
            )
            risk_contributions[symbol] = risk_contrib

        return risk_contributions

    def get_rebalance_recommendation(
        self, current_weights: Dict[str, float], portfolio_value: float
    ) -> Optional[Dict[str, float]]:
        """获取再平衡建议"""

        if self.rebalancer.should_rebalance(current_weights):
            target_weights = self.rebalancer.target_weights
            if target_weights:
                return self.rebalancer.calculate_rebalance_trades(
                    current_weights, target_weights, portfolio_value
                )

        return None


__all__ = [
    "RiskBudgetSystem",
    "RiskBudgetConfig",
    "RiskBudgetOptimizer",
    "DynamicRebalancer",
    "AssetRiskMetrics",
    "RiskBudgetResult",
    "RiskBudgetMethod",
]

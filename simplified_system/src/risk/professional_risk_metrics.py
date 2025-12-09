#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
Professional Risk Metrics Implementation
專業級風險指標實現 - VaR、CVaR、Sortino、Calmar等
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class RiskMetricsConfig:
    """風險指標配置"""

    confidence_levels: List[float] = None
    time_horizons: List[int] = None  # 天數
    benchmark_return: float = 0.03  # 無風險利率3%
    trading_days_per_year: int = 252


class ProfessionalRiskMetrics:
    """專業級風險指標計算器"""

    def __init__(self, config: Optional[RiskMetricsConfig] = None):
        self.config = config or RiskMetricsConfig()

        # 默認配置
        if self.config.confidence_levels is None:
            self.config.confidence_levels = [0.90, 0.95, 0.99]
        if self.config.time_horizons is None:
            self.config.time_horizons = [1, 5, 10, 21]  # 1天, 1周, 2周, 1月

    def calculate_var(
        self, returns: pd.Series, confidence_level: float = 0.95
    ) -> Dict[str, float]:
        """
        計算Value at Risk (VaR)

        Args:
            returns: 回報序列
            confidence_level: 置信水平 (0.95表示95% VaR)

        Returns:
            VaR結果
        """
        if len(returns) == 0:
            return {"var": 0.0, "method": "empty_data"}

        # Historical Simulation VaR
        var_historical = self._historical_var(returns, confidence_level)

        # Parametric VaR (假設常態分佈)
        var_parametric = self._parametric_var(returns, confidence_level)

        # Cornish - Fisher Expansion VaR (調整非正態性)
        var_cornish_fisher = self._cornish_fisher_var(returns, confidence_level)

        return {
            "var_historical": var_historical,
            "var_parametric": var_parametric,
            "var_cornish_fisher": var_cornish_fisher,
            "confidence_level": confidence_level,
            "method": "multi_method",
        }

    def _historical_var(self, returns: pd.Series, confidence_level: float) -> float:
        """Historical Simulation VaR"""
        # 負分位數
        var_value = returns.quantile(1 - confidence_level)
        return var_value

    def _parametric_var(self, returns: pd.Series, confidence_level: float) -> float:
        """Parametric VaR (假設常態分佈)"""
        mean = returns.mean()
        std = returns.std()

        # 使用標準正態分佈的百分位數
        z_score = stats.norm.ppf(1 - confidence_level)
        var = mean + z_score * std

        return var

    def _cornish_fisher_var(self, returns: pd.Series, confidence_level: float) -> float:
        """Cornish - Fisher Expansion VaR"""
        mean = returns.mean()
        std = returns.std()

        # 計算偏度和峰度
        skewness = stats.skew(returns)
        kurtosis = stats.kurtosis(returns)

        # Cornish - Fisher調整
        z_score = stats.norm.ppf(1 - confidence_level)

        # 三階和四階調整項
        cf_adjustment = (z_score * *2 - 1) * skewness / 6 + (
            z_score * *3 - 3 * z_score
        ) * (kurtosis - 3) / 24

        adjusted_z = z_score + cf_adjustment
        var = mean + adjusted_z * std

        return var

    def calculate_cvar(
        self, returns: pd.Series, confidence_level: float = 0.95
    ) -> Dict[str, float]:
        """
        計算Conditional Value at Risk (CVaR)

        Args:
            returns: 回報序列
            confidence_level: 置信水平

        Returns:
            CVaR結果
        """
        if len(returns) == 0:
            return {"cvar": 0.0, "expected_shortfall": 0.0, "method": "empty_data"}

        # Historical CVaR
        cvar_historical = self._historical_cvar(returns, confidence_level)

        # Parametric CVaR
        cvar_parametric = self._parametric_cvar(returns, confidence_level)

        return {
            "cvar_historical": cvar_historical,
            "cvar_parametric": cvar_parametric,
            "confidence_level": confidence_level,
            "method": "multi_method",
        }

    def _historical_cvar(self, returns: pd.Series, confidence_level: float) -> float:
        """Historical CVaR"""
        var_threshold = self._historical_var(returns, confidence_level)

        # 取小於VaR的回報的平均值
        shortfall_returns = returns[returns <= var_threshold]

        if len(shortfall_returns) == 0:
            return var_threshold

        cvar = shortfall_returns.mean()
        return cvar

    def _parametric_cvar(self, returns: pd.Series, confidence_level: float) -> float:
        """Parametric CVaR (假設常態分佈)"""
        mean = returns.mean()
        std = returns.std()

        z_score = stats.norm.ppf(1 - confidence_level)

        # 對於分佈的CVaR公式
        # E[X | X < VaR] = mean - φ(z) / Φ(z) * σ
        # 其中φ是標準常態PDF，Φ是標準常態CDF
        pdf = stats.norm.pdf(z_score)
        stats.norm.cdf(z_score)

        cvar = mean - (pdf / (1 - confidence_level)) * std
        return cvar

    def calculate_sortino_ratio(
        self, returns: pd.Series, downside_threshold: Optional[float] = None
    ) -> float:
        """
        計算Sortino比率

        Args:
            returns: 回報序列
            downside_threshold: 下行風險閾值，默認為無風險利率

        Returns:
            Sortino比率
        """
        if len(returns) == 0:
            return 0.0

        if downside_threshold is None:
            downside_threshold = (
                self.config.benchmark_return / self.config.trading_days_per_year
            )

        # 計算下行回報
        downside_returns = returns[returns < downside_threshold]

        if len(downside_returns) == 0:
            return float("inf") if returns.mean() > 0 else 0.0

        # Sortino比率公式
        excess_return = returns.mean() - downside_threshold
        downside_deviation = downside_returns.std()

        if downside_deviation == 0:
            return float("inf") if excess_return > 0 else 0.0

        sortino_ratio = excess_return / downside_deviation
        return sortino_ratio

    def calculate_calmar_ratio(self, returns: pd.Series) -> float:
        """
        計算Calmar比率 (年化回報 / 最大回撤)

        Args:
            returns: 回報序列

        Returns:
            Calmar比率
        """
        if len(returns) == 0:
            return 0.0

        # 年化回報
        total_return = np.prod(1 + returns) - 1
        annualized_return = (1 + total_return) ** (
            self.config.trading_days_per_year / len(returns)
        ) - 1

        # 最大回撤
        max_drawdown = self.calculate_max_drawdown(returns)

        if max_drawdown == 0:
            return float("inf") if annualized_return > 0 else 0.0

        calmar_ratio = annualized_return / abs(max_drawdown)
        return calmar_ratio

    def calculate_max_drawdown(self, returns: pd.Series) -> float:
        """
        計算最大回撤

        Args:
            returns: 回報序列

        Returns:
            最大回撤 (負值)
        """
        if len(returns) == 0:
            return 0.0

        # 累積回報
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)

        # 回撤
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdown)

        return max_drawdown

    def calculate_information_ratio(
        self, returns: pd.Series, benchmark_returns: pd.Series
    ) -> float:
        """
        計算Information比率 (相對基準的超額回報 / 跟踪誤差)

        Args:
            returns: 策略回報
            benchmark_returns: 基準回報

        Returns:
            Information比率
        """
        if len(returns) == 0 or len(benchmark_returns) == 0:
            return 0.0

        # 確保長度一致
        min_length = min(len(returns), len(benchmark_returns))
        returns = returns[:min_length]
        benchmark_returns = benchmark_returns[:min_length]

        # 超額回報
        excess_returns = returns - benchmark_returns

        # 跟踪誤差
        tracking_error = np.std(excess_returns)

        if tracking_error == 0:
            return float("inf") if excess_returns.mean() > 0 else 0.0

        # Information比率
        information_ratio = excess_returns.mean() / tracking_error
        return information_ratio

    def calculate_beta(self, returns: pd.Series, market_returns: pd.Series) -> float:
        """
        計算Beta (系統性風險)

        Args:
            returns: 資產回報
            market_returns: 市場回報

        Returns:
            Beta值
        """
        if len(returns) == 0 or len(market_returns) == 0:
            return 1.0  # 默認值

        # 確保長度一致
        min_length = min(len(returns), len(market_returns))
        returns = returns[:min_length]
        market_returns = market_returns[:min_length]

        # 計算協方差和方差
        covariance = np.cov(returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)

        if market_variance == 0:
            return 1.0

        beta = covariance / market_variance
        return beta

    def calculate_alpha(self, returns: pd.Series, market_returns: pd.Series) -> float:
        """
        計算Alpha (超額回報)

        Args:
            returns: 資產回報
            market_returns: 市場回報

        Returns:
            Alpha值
        """
        if len(returns) == 0 or len(market_returns) == 0:
            return 0.0

        min_length = min(len(returns), len(market_returns))
        returns = returns[:min_length]
        market_returns = market_returns[:min_length]

        # 年化回報
        asset_return = (np.prod(1 + returns) - 1) * (
            self.config.trading_days_per_year / min_length
        )
        market_return = (np.prod(1 + market_returns) - 1) * (
            self.config.trading_days_per_year / min_length
        )

        beta = self.calculate_beta(returns, market_returns)

        # Alpha = Return - Risk_free_rate - Beta * (Market Return - Risk - free_rate)
        risk_free_rate = self.config.benchmark_return
        alpha = asset_return - risk_free_rate - beta * (market_return - risk_free_rate)

        return alpha

    def calculate_omega_ratio(
        self, returns: pd.Series, target_return: float = 0.15
    ) -> float:
        """
        計算Omega比率 (收益 / 虧損比)

        Args:
            returns: 回報序列
            target_return: 目標回報

        Returns:
            Omega比率
        """
        if len(returns) == 0:
            return 0.0

        # 計算收益和虧損
        gains = returns[returns > target_return]
        losses = returns[returns <= target_return]

        if len(losses) == 0:
            return float("inf")

        omega_ratio = gains.sum() / abs(losses.sum())
        return omega_ratio

    def calculate_all_metrics(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
        market_returns: Optional[pd.Series] = None,
    ) -> Dict[str, Any]:
        """
        計算所有風險指標

        Args:
            returns: 策略回報序列
            benchmark_returns: 基準回報序列 (可選)
            market_returns: 市場回報序列 (可選)

        Returns:
            所有風險指標字典
        """
        metrics = {}

        # 基本指標
        metrics["total_return"] = np.prod(1 + returns) - 1
        metrics["annualized_return"] = (1 + metrics["total_return"]) ** (
            252 / len(returns)
        ) - 1
        metrics["volatility"] = returns.std() * np.sqrt(252)
        metrics["sharpe_ratio"] = self.calculate_sharpe_ratio(returns)

        # 高級指標
        metrics["sortino_ratio"] = self.calculate_sortino_ratio(returns)
        metrics["calmar_ratio"] = self.calculate_calmar_ratio(returns)
        metrics["max_drawdown"] = self.calculate_max_drawdown(returns)
        metrics["omega_ratio"] = self.calculate_omega_ratio(returns)

        # VaR和CVaR
        for confidence_level in self.config.confidence_levels:
            var_results = self.calculate_var(returns, confidence_level)
            cvar_results = self.calculate_cvar(returns, confidence_level)

            metrics[f"var_{int(confidence_level * 100)}"] = var_results["var_historical"]
            metrics[f"cvar_{int(confidence_level * 100)}"] = cvar_results[
                "cvar_historical"
            ]

        # 基準和市場相關指標
        if benchmark_returns is not None:
            metrics["information_ratio"] = self.calculate_information_ratio(
                returns, benchmark_returns
            )
            metrics["tracking_error"] = np.std(returns - benchmark_returns)

        if market_returns is not None:
            metrics["beta"] = self.calculate_beta(returns, market_returns)
            metrics["alpha"] = self.calculate_alpha(returns, market_returns)

        # 壓力比指標
        metrics["win_rate"] = self.calculate_win_rate(returns)
        metrics["profit_factor"] = self.calculate_profit_factor(returns)
        metrics["average_win_loss_ratio"] = self.calculate_average_win_loss_ratio(
            returns
        )

        return metrics

    def calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """計算Sharpe比率"""
        if len(returns) == 0:
            return 0.0

        excess_returns = returns - self.config.benchmark_return / 252

        if np.std(excess_returns) == 0:
            return 0.0

        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        return sharpe

    def calculate_win_rate(self, returns: pd.Series) -> float:
        """計算勝率"""
        if len(returns) == 0:
            return 0.0

        wins = returns[returns > 0]
        return len(wins) / len(returns)

    def calculate_profit_factor(self, returns: pd.Series) -> float:
        """計算盈利因子"""
        if len(returns) == 0:
            return 1.0

        gains = returns[returns > 0].sum()
        losses = abs(returns[returns <= 0].sum())

        if losses == 0:
            return float("inf")

        return gains / losses

    def calculate_average_win_loss_ratio(self, returns: pd.Series) -> float:
        """計算平均盈虧比"""
        if len(returns) == 0:
            return 1.0

        wins = returns[returns > 0]
        losses = returns[returns <= 0]

        if len(losses) == 0:
            return float("inf") if len(wins) > 0 else 1.0

        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 1.0

        return avg_win / avg_loss

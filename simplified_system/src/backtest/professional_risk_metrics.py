#!/usr / bin / env python3
"""
Advanced Risk Management Metrics
Phase 3.1: Professional Risk Metrics Implementation

Implements Value at Risk (VaR), Conditional Value at Risk (CVaR),
Sortino ratio, Calmar ratio, Information ratio, and other risk - adjusted
performance metrics for comprehensive risk analysis.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Container for risk metrics"""

    # Basic return metrics
    total_return: float
    annualized_return: float
    volatility: float

    # Risk - adjusted ratios
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    information_ratio: float

    # Value at Risk metrics
    var_95: float  # 95% VaR
    var_99: float  # 99% VaR
    cvar_95: float  # 95% Conditional VaR
    cvar_99: float  # 99% Conditional VaR

    # Drawdown metrics
    max_drawdown: float
    avg_drawdown: float
    drawdown_duration: int

    # Additional metrics
    beta: float
    alpha: float
    tracking_error: float
    win_rate: float
    profit_factor: float

    # Distribution metrics
    skewness: float
    kurtosis: float
    tail_ratio: float


class RiskCalculator:
    """Professional risk metrics calculator"""

    def __init__(self, risk_free_rate: float = 0.03):
        """
        Initialize risk calculator

        Args:
            risk_free_rate: Annual risk - free rate (default: 3%)
        """
        self.risk_free_rate = risk_free_rate

    def calculate_returns(self, prices: pd.Series) -> pd.Series:
        """Calculate daily returns from price series"""
        return prices.pct_change().dropna()

    def calculate_basic_metrics(
        self, returns: pd.Series, benchmark_returns: Optional[pd.Series] = None
    ) -> Dict[str, float]:
        """Calculate basic performance metrics"""

        # Total return
        total_return = (1 + returns).prod() - 1

        # Annualized metrics (assuming daily returns)
        trading_days_per_year = 252
        annualized_return = (1 + total_return) ** (
            trading_days_per_year / len(returns)
        ) - 1
        volatility = returns.std() * np.sqrt(trading_days_per_year)

        metrics = {
            "total_return": total_return,
            "annualized_return": annualized_return,
            "volatility": volatility,
        }

        if benchmark_returns is not None:
            # Align returns
            common_index = returns.index.intersection(benchmark_returns.index)
            aligned_returns = returns.loc[common_index]
            aligned_benchmark = benchmark_returns.loc[common_index]

            # Calculate excess returns
            excess_returns = aligned_returns - aligned_benchmark

            # Alpha and Beta
            covariance = np.cov(aligned_returns, aligned_benchmark)[0, 1]
            benchmark_variance = np.var(aligned_benchmark)
            beta = covariance / benchmark_variance if benchmark_variance != 0 else 0

            # Alpha (annualized)
            benchmark_ann_return = (1 + aligned_benchmark).prod() ** (
                trading_days_per_year / len(aligned_benchmark)
            ) - 1
            alpha = annualized_return - (
                self.risk_free_rate
                + beta * (benchmark_ann_return - self.risk_free_rate)
            )

            # Information ratio
            tracking_error = excess_returns.std() * np.sqrt(trading_days_per_year)
            information_ratio = (
                (excess_returns.mean() * trading_days_per_year) / tracking_error
                if tracking_error != 0
                else 0
            )

            metrics.update(
                {
                    "beta": beta,
                    "alpha": alpha,
                    "tracking_error": tracking_error,
                    "information_ratio": information_ratio,
                }
            )

        return metrics

    def calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calculate Sharpe ratio with 3% risk - free rate"""
        excess_returns = returns - self.risk_free_rate / 252
        if excess_returns.std() == 0:
            return 0
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252)

    def calculate_sortino_ratio(self, returns: pd.Series) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        excess_returns = returns - self.risk_free_rate / 252
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0

        return excess_returns.mean() / downside_returns.std() * np.sqrt(252)

    def calculate_calmar_ratio(self, returns: pd.Series, prices: pd.Series) -> float:
        """Calculate Calmar ratio (annual return / max drawdown)"""
        # Calculate annualized return
        total_return = (1 + returns).prod() - 1
        annualized_return = (1 + total_return) ** (252 / len(returns)) - 1

        # Calculate maximum drawdown
        running_max = prices.expanding().max()
        drawdown = (prices - running_max) / running_max
        max_drawdown = drawdown.min()

        if abs(max_drawdown) < 1e - 10:
            return 0

        return annualized_return / abs(max_drawdown)

    def calculate_var(
        self, returns: pd.Series, confidence_level: float = 0.95
    ) -> float:
        """Calculate Value at Risk using historical method"""
        return np.percentile(returns, (1 - confidence_level) * 100)

    def calculate_cvar(
        self, returns: pd.Series, confidence_level: float = 0.95
    ) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        var_threshold = self.calculate_var(returns, confidence_level)
        tail_losses = returns[returns <= var_threshold]

        if len(tail_losses) == 0:
            return var_threshold

        return tail_losses.mean()

    def calculate_drawdown_metrics(self, prices: pd.Series) -> Dict[str, float]:
        """Calculate comprehensive drawdown metrics"""
        # Calculate running maximum and drawdown
        running_max = prices.expanding().max()
        drawdown = (prices - running_max) / running_max

        # Maximum drawdown
        max_drawdown = drawdown.min()

        # Average drawdown (only negative drawdowns)
        negative_drawdowns = drawdown[drawdown < 0]
        avg_drawdown = negative_drawdowns.mean() if len(negative_drawdowns) > 0 else 0

        # Drawdown duration
        drawdown_periods = []
        in_drawdown = False
        current_duration = 0

        for dd in drawdown:
            if dd < 0:
                if not in_drawdown:
                    in_drawdown = True
                    current_duration = 1
                else:
                    current_duration += 1
            else:
                if in_drawdown:
                    drawdown_periods.append(current_duration)
                    in_drawdown = False
                    current_duration = 0

        # Add final period if we're still in drawdown
        if in_drawdown:
            drawdown_periods.append(current_duration)

        drawdown_duration = max(drawdown_periods) if drawdown_periods else 0

        return {
            "max_drawdown": max_drawdown,
            "avg_drawdown": avg_drawdown,
            "drawdown_duration": drawdown_duration,
        }

    def calculate_distribution_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate distribution characteristics"""

        # Skewness and kurtosis
        skewness = stats.skew(returns)
        kurtosis = stats.kurtosis(returns)  # Excess kurtosis (normal = 0)

        # Tail ratio (95th percentile / 5th percentile absolute value)
        p95 = np.percentile(returns, 95)
        p5 = np.percentile(returns, 5)
        tail_ratio = p95 / abs(p5) if p5 != 0 else float("inf")

        return {"skewness": skewness, "kurtosis": kurtosis, "tail_ratio": tail_ratio}

    def calculate_trading_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate trading - specific metrics"""

        # Win rate (percentage of positive returns)
        win_rate = (returns > 0).mean()

        # Profit factor (gross profit / gross loss)
        positive_returns = returns[returns > 0]
        negative_returns = returns[returns < 0]

        gross_profit = positive_returns.sum() if len(positive_returns) > 0 else 0
        gross_loss = abs(negative_returns.sum()) if len(negative_returns) > 0 else 0

        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        return {"win_rate": win_rate, "profit_factor": profit_factor}

    def calculate_comprehensive_metrics(
        self, prices: pd.Series, benchmark_returns: Optional[pd.Series] = None
    ) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics

        Args:
            prices: Price series
            benchmark_returns: Optional benchmark returns for alpha / beta calculation

        Returns:
            RiskMetrics object with all calculated metrics
        """

        # Calculate returns
        returns = self.calculate_returns(prices)

        if len(returns) == 0:
            raise ValueError("No returns data available")

        # Basic metrics
        basic_metrics = self.calculate_basic_metrics(returns, benchmark_returns)

        # Risk - adjusted ratios
        sharpe_ratio = self.calculate_sharpe_ratio(returns)
        sortino_ratio = self.calculate_sortino_ratio(returns)
        calmar_ratio = self.calculate_calmar_ratio(returns, prices)

        # Value at Risk metrics
        var_95 = self.calculate_var(returns, 0.95)
        var_99 = self.calculate_var(returns, 0.99)
        cvar_95 = self.calculate_cvar(returns, 0.95)
        cvar_99 = self.calculate_cvar(returns, 0.99)

        # Drawdown metrics
        drawdown_metrics = self.calculate_drawdown_metrics(prices)

        # Distribution metrics
        distribution_metrics = self.calculate_distribution_metrics(returns)

        # Trading metrics
        trading_metrics = self.calculate_trading_metrics(returns)

        # Combine all metrics
        risk_metrics = RiskMetrics(
            # Basic return metrics
            total_return = basic_metrics["total_return"],
            annualized_return = basic_metrics["annualized_return"],
            volatility = basic_metrics["volatility"],
            # Risk - adjusted ratios
            sharpe_ratio = sharpe_ratio,
            sortino_ratio = sortino_ratio,
            calmar_ratio = calmar_ratio,
            information_ratio = basic_metrics.get("information_ratio", 0),
            # Value at Risk metrics
            var_95 = var_95,
            var_99 = var_99,
            cvar_95 = cvar_95,
            cvar_99 = cvar_99,
            # Drawdown metrics
            max_drawdown = drawdown_metrics["max_drawdown"],
            avg_drawdown = drawdown_metrics["avg_drawdown"],
            drawdown_duration = drawdown_metrics["drawdown_duration"],
            # Additional metrics
            beta = basic_metrics.get("beta", 0),
            alpha = basic_metrics.get("alpha", 0),
            tracking_error = basic_metrics.get("tracking_error", 0),
            win_rate = trading_metrics["win_rate"],
            profit_factor = trading_metrics["profit_factor"],
            # Distribution metrics
            skewness = distribution_metrics["skewness"],
            kurtosis = distribution_metrics["kurtosis"],
            tail_ratio = distribution_metrics["tail_ratio"],
        )

        return risk_metrics

    def calculate_risk_adjusted_performance_score(
        self, risk_metrics: RiskMetrics, weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate composite risk - adjusted performance score

        Args:
            risk_metrics: RiskMetrics object
            weights: Optional weights for different metrics (default: equal weights)

        Returns:
            Composite score (higher is better)
        """

        if weights is None:
            weights = {
                "sharpe_ratio": 0.3,
                "sortino_ratio": 0.2,
                "calmar_ratio": 0.2,
                "max_drawdown": 0.15,  # Negative weight (less drawdown is better)
                "var_95": 0.1,  # Negative weight (less VaR is better)
                "win_rate": 0.05,
            }

        # Normalize metrics to comparable scale
        # (This is a simple normalization - in practice, you might use more sophisticated methods)

        sharpe_score = (
            max(0, risk_metrics.sharpe_ratio) / 3
        )  # Normalize to 0 - 1 (assuming max Sharpe of 3)
        sortino_score = max(0, risk_metrics.sortino_ratio) / 4  # Normalize to 0 - 1
        calmar_score = max(0, risk_metrics.calmar_ratio) / 2  # Normalize to 0 - 1
        drawdown_score = max(
            0, 1 + risk_metrics.max_drawdown
        )  # Normalize (drawdown is negative)
        var_score = max(
            0, 1 + risk_metrics.var_95 * 10
        )  # Normalize VaR (VaR is negative)
        win_rate_score = risk_metrics.win_rate  # Already 0 - 1

        # Calculate weighted score
        composite_score = (
            weights["sharpe_ratio"] * sharpe_score
            + weights["sortino_ratio"] * sortino_score
            + weights["calmar_ratio"] * calmar_score
            + weights["max_drawdown"] * drawdown_score
            + weights["var_95"] * var_score
            + weights["win_rate"] * win_rate_score
        )

        return composite_score


# Utility functions for portfolio risk analysis


def calculate_portfolio_risk(
    returns_matrix: pd.DataFrame, weights: np.ndarray
) -> Dict[str, float]:
    """
    Calculate portfolio risk metrics

    Args:
        returns_matrix: DataFrame of asset returns (columns = assets)
        weights: Portfolio weights

    Returns:
        Dictionary of portfolio risk metrics
    """

    # Calculate portfolio returns
    portfolio_returns = (returns_matrix * weights).sum(axis = 1)

    # Portfolio volatility
    portfolio_variance = np.dot(weights.T, np.dot(returns_matrix.cov() * 252, weights))
    portfolio_volatility = np.sqrt(portfolio_variance)

    # Individual asset volatilities
    asset_volatilities = returns_matrix.std() * np.sqrt(252)

    # Contribution to risk (simplified)
    marginal_contributions = (
        np.dot(returns_matrix.cov() * 252, weights) / portfolio_volatility
    )
    component_contributions = weights * marginal_contributions

    return {
        "portfolio_volatility": portfolio_volatility,
        "portfolio_variance": portfolio_variance,
        "asset_volatilities": asset_volatilities.tolist(),
        "marginal_contributions": marginal_contributions.tolist(),
        "component_contributions": component_contributions.tolist(),
        "risk_contribution_percentages": (
            component_contributions / portfolio_volatility
        ).tolist(),
    }


def stress_test_returns(
    returns: pd.Series, stress_scenarios: Dict[str, Dict[str, float]]
) -> Dict[str, Dict[str, float]]:
    """
    Perform stress testing on returns under different scenarios

    Args:
        returns: Return series to stress test
        stress_scenarios: Dictionary of stress scenarios with parameters

    Returns:
        Dictionary with stress test results
    """

    results = {}

    for scenario_name, params in stress_scenarios.items():
        stressed_returns = returns.copy()

        # Apply stress scenario
        if "shock" in params:
            # Add shock to all returns
            stressed_returns = stressed_returns + params["shock"]

        if "volatility_multiplier" in params:
            # Increase volatility
            stressed_returns = stressed_returns * params["volatility_multiplier"]

        if "correlation_increase" in params:
            # Increase correlation (simplified approach)
            stressed_returns = stressed_returns * params["correlation_increase"]

        # Calculate metrics under stress
        stressed_volatility = stressed_returns.std() * np.sqrt(252)
        stressed_var_95 = np.percentile(stressed_returns, 5)
        stressed_cvar_95 = stressed_returns[stressed_returns <= stressed_var_95].mean()

        results[scenario_name] = {
            "volatility": stressed_volatility,
            "var_95": stressed_var_95,
            "cvar_95": stressed_cvar_95,
            "volatility_increase": stressed_volatility / (returns.std() * np.sqrt(252))
            - 1,
            "var_deterioration": stressed_var_95 / np.percentile(returns, 5) - 1,
        }

    return results


def create_default_stress_scenarios() -> Dict[str, Dict[str, float]]:
    """Create default stress test scenarios"""
    return {
        "market_crash": {
            "shock": -0.05,  # 5% daily drop
            "volatility_multiplier": 2.0,
            "correlation_increase": 1.5,
        },
        "volatility_spike": {"volatility_multiplier": 3.0},
        "correlation_breakdown": {"correlation_increase": 2.0},
        "moderate_downturn": {
            "shock": -0.02,  # 2% daily drop
            "volatility_multiplier": 1.5,
        },
    }

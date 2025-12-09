#!/usr / bin / env python3
"""
Advanced Portfolio Management System
Phase 3.2: Advanced Portfolio Management

Implements multi - asset portfolio backtesting, dynamic position sizing,
risk - parity methods, and portfolio optimization algorithms.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .professional_risk_metrics import (
    RiskCalculator,
    RiskMetrics,
    calculate_portfolio_risk,
)

logger = logging.getLogger(__name__)


@dataclass
class PortfolioAllocation:
    """Portfolio allocation information"""

    weights: Dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    var_95: float


@dataclass
class PositionSize:
    """Position sizing information"""

    symbol: str
    weight: float
    size: float  # Number of shares / units
    value: float  # Position value in currency
    risk_contribution: float


class DynamicPositionSizer:
    """Dynamic position sizing based on volatility and risk metrics"""

    def __init__(
        self,
        portfolio_value: float = 1000000,
        max_position_size: float = 0.2,
        volatility_lookback: int = 60,
        rebalance_frequency: int = 20,
    ):
        """
        Initialize dynamic position sizer

        Args:
            portfolio_value: Total portfolio value
            max_position_size: Maximum allocation to single position (20% default)
            volatility_lookback: Days to look back for volatility calculation
            rebalance_frequency: Days between rebalancing
        """
        self.portfolio_value = portfolio_value
        self.max_position_size = max_position_size
        self.volatility_lookback = volatility_lookback
        self.rebalance_frequency = rebalance_frequency

    def calculate_volatility_adjusted_weights(
        self, returns: pd.DataFrame, target_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Calculate volatility - adjusted portfolio weights

        Args:
            returns: DataFrame of asset returns
            target_weights: Optional target weights

        Returns:
            Dictionary of volatility - adjusted weights
        """

        # Calculate rolling volatilities
        volatilities = returns.rolling(self.volatility_lookback).std().iloc[-1]

        # Inverse volatility weighting
        inverse_vol = 1 / volatilities
        weights = inverse_vol / inverse_vol.sum()

        # Apply target weights if provided
        if target_weights:
            for asset, target_weight in target_weights.items():
                if asset in weights:
                    weights[asset] = 0.7 * weights[asset] + 0.3 * target_weight

        # Apply maximum position size constraint
        weights = weights.clip(upper = self.max_position_size)
        weights = weights / weights.sum()  # Re - normalize

        return weights.to_dict()

    def calculate_risk_parity_weights(
        self, returns: pd.DataFrame, target_volatility: float = 0.15
    ) -> Dict[str, float]:
        """
        Calculate risk parity weights (equal risk contribution)

        Args:
            returns: DataFrame of asset returns
            target_volatility: Target portfolio volatility

        Returns:
            Dictionary of risk parity weights
        """

        n_assets = returns.shape[1]
        assets = returns.columns.tolist()

        # Covariance matrix
        cov_matrix = returns.cov() * 252  # Annualized

        def risk_parity_objective(weights):
            """Objective function for risk parity optimization"""
            portfolio_var = np.dot(weights.T, np.dot(cov_matrix, weights))
            marginal_contrib = np.dot(cov_matrix, weights)
            risk_contrib = weights * marginal_contrib / portfolio_var

            # Minimize squared deviation from equal risk contribution
            target_risk_contrib = 1 / n_assets
            return np.sum((risk_contrib - target_risk_contrib) ** 2)

        # Constraints
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1}  # Weights sum to 1
        ]

        # Bounds
        bounds = [(0, self.max_position_size) for _ in range(n_assets)]

        # Initial guess (equal weights)
        initial_weights = np.array([1 / n_assets] * n_assets)

        # Optimization
        result = minimize(
            risk_parity_objective,
            initial_weights,
            method="SLSQP",
            bounds = bounds,
            constraints = constraints,
            options={"ftol": 1e - 9, "disp": False},
        )

        if not result.success:
            logger.warning(f"Risk parity optimization failed: {result.message}")
            return {asset: 1 / n_assets for asset in assets}

        # Scale to target volatility
        weights = result.x
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        scaling_factor = target_volatility / portfolio_vol

        # Don't scale up beyond 100% allocation
        scaling_factor = min(scaling_factor, 1.0)
        weights = weights * scaling_factor
        weights = weights / weights.sum()  # Re - normalize

        return dict(zip(assets, weights))

    def calculate_kelly_criterion_weights(
        self, returns: pd.DataFrame, lookahead_returns: Optional[pd.DataFrame] = None
    ) -> Dict[str, float]:
        """
        Calculate Kelly criterion weights for optimal growth

        Args:
            returns: Historical returns
            lookahead_returns: Expected future returns (optional)

        Returns:
            Dictionary of Kelly criterion weights
        """

        assets = returns.columns.tolist()
        weights = {}

        for asset in assets:
            asset_returns = returns[asset]

            # Expected return and volatility
            if lookahead_returns is not None and asset in lookahead_returns.columns:
                expected_return = lookahead_returns[asset].mean()
            else:
                expected_return = asset_returns.mean()

            volatility = asset_returns.std()

            # Kelly fraction (simplified)
            if volatility > 0:
                kelly_fraction = expected_return / (volatility * *2)
                # Conservative Kelly (fraction of full Kelly)
                kelly_fraction = kelly_fraction * 0.25
                # Apply bounds
                kelly_fraction = max(0, min(kelly_fraction, self.max_position_size))
            else:
                kelly_fraction = 0

            weights[asset] = kelly_fraction

        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        else:
            weights = {asset: 1 / len(assets) for asset in assets}

        return weights


class PortfolioOptimizer:
    """Advanced portfolio optimization algorithms"""

    def __init__(self, risk_free_rate: float = 0.03):
        """
        Initialize portfolio optimizer

        Args:
            risk_free_rate: Risk - free rate for calculations
        """
        self.risk_free_rate = risk_free_rate
        self.risk_calculator = RiskCalculator(risk_free_rate)

    def calculate_efficient_frontier(
        self, returns: pd.DataFrame, num_portfolios: int = 100
    ) -> Tuple[np.ndarray, np.ndarray, List[Dict[str, float]]]:
        """
        Calculate efficient frontier

        Args:
            returns: DataFrame of asset returns
            num_portfolios: Number of portfolios to generate

        Returns:
            Tuple of (returns, volatilities, weights_list)
        """

        n_assets = returns.shape[1]
        assets = returns.columns.tolist()

        # Calculate expected returns and covariance matrix
        expected_returns = returns.mean() * 252  # Annualized
        cov_matrix = returns.cov() * 252

        # Generate random portfolios
        np.random.seed(42)
        weights_list = []
        returns_list = []
        volatilities_list = []

        for _ in range(num_portfolios):
            # Generate random weights
            weights = np.random.random(n_assets)
            weights = weights / np.sum(weights)

            # Calculate portfolio metrics
            portfolio_return = np.dot(weights, expected_returns)
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)

            weights_list.append(dict(zip(assets, weights)))
            returns_list.append(portfolio_return)
            volatilities_list.append(portfolio_volatility)

        return np.array(returns_list), np.array(volatilities_list), weights_list

    def maximize_sharpe_ratio(
        self,
        returns: pd.DataFrame,
        weight_bounds: Optional[List[Tuple[float, float]]] = None,
    ) -> PortfolioAllocation:
        """
        Find portfolio with maximum Sharpe ratio

        Args:
            returns: DataFrame of asset returns
            weight_bounds: Optional bounds for weights

        Returns:
            PortfolioAllocation object
        """

        n_assets = returns.shape[1]
        assets = returns.columns.tolist()

        # Expected returns and covariance matrix
        expected_returns = returns.mean() * 252
        cov_matrix = returns.cov() * 252

        def negative_sharpe_ratio(weights):
            """Negative Sharpe ratio for minimization"""
            portfolio_return = np.dot(weights, expected_returns)
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)

            if portfolio_volatility == 0:
                return -np.inf

            sharpe_ratio = (
                portfolio_return - self.risk_free_rate
            ) / portfolio_volatility
            return -sharpe_ratio

        # Constraints
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1}  # Weights sum to 1
        ]

        # Bounds
        if weight_bounds is None:
            bounds = [(0, 1) for _ in range(n_assets)]
        else:
            bounds = weight_bounds

        # Initial guess
        initial_weights = np.array([1 / n_assets] * n_assets)

        # Optimization
        result = minimize(
            negative_sharpe_ratio,
            initial_weights,
            method="SLSQP",
            bounds = bounds,
            constraints = constraints,
            options={"ftol": 1e - 9, "disp": False},
        )

        if not result.success:
            logger.warning(f"Sharpe ratio optimization failed: {result.message}")
            result.x = initial_weights

        # Calculate portfolio metrics
        weights = result.x
        portfolio_return = np.dot(weights, expected_returns)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility

        # Estimate risk metrics using historical returns
        portfolio_returns = (returns * weights).sum(axis = 1)
        risk_metrics = self.risk_calculator.calculate_comprehensive_metrics(
            (1 + portfolio_returns).cumprod()
        )

        return PortfolioAllocation(
            weights = dict(zip(assets, weights)),
            expected_return = portfolio_return,
            expected_volatility = portfolio_volatility,
            sharpe_ratio = sharpe_ratio,
            max_drawdown = risk_metrics.max_drawdown,
            var_95 = risk_metrics.var_95,
        )

    def minimize_volatility(
        self,
        returns: pd.DataFrame,
        target_return: Optional[float] = None,
        weight_bounds: Optional[List[Tuple[float, float]]] = None,
    ) -> PortfolioAllocation:
        """
        Find portfolio with minimum volatility (or minimum volatility for target return)

        Args:
            returns: DataFrame of asset returns
            target_return: Optional target return constraint
            weight_bounds: Optional bounds for weights

        Returns:
            PortfolioAllocation object
        """

        n_assets = returns.shape[1]
        assets = returns.columns.tolist()

        # Expected returns and covariance matrix
        expected_returns = returns.mean() * 252
        cov_matrix = returns.cov() * 252

        def portfolio_volatility(weights):
            """Portfolio volatility for minimization"""
            return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

        # Constraints
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]

        if target_return is not None:
            constraints.append(
                {
                    "type": "eq",
                    "fun": lambda w: np.dot(w, expected_returns) - target_return,
                }
            )

        # Bounds
        if weight_bounds is None:
            bounds = [(0, 1) for _ in range(n_assets)]
        else:
            bounds = weight_bounds

        # Initial guess
        initial_weights = np.array([1 / n_assets] * n_assets)

        # Optimization
        result = minimize(
            portfolio_volatility,
            initial_weights,
            method="SLSQP",
            bounds = bounds,
            constraints = constraints,
            options={"ftol": 1e - 9, "displ": False},
        )

        if not result.success:
            logger.warning(f"Volatility minimization failed: {result.message}")
            result.x = initial_weights

        # Calculate portfolio metrics
        weights = result.x
        portfolio_return = np.dot(weights, expected_returns)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility

        # Estimate risk metrics using historical returns
        portfolio_returns = (returns * weights).sum(axis = 1)
        risk_metrics = self.risk_calculator.calculate_comprehensive_metrics(
            (1 + portfolio_returns).cumprod()
        )

        return PortfolioAllocation(
            weights = dict(zip(assets, weights)),
            expected_return = portfolio_return,
            expected_volatility = portfolio_volatility,
            sharpe_ratio = sharpe_ratio,
            max_drawdown = risk_metrics.max_drawdown,
            var_95 = risk_metrics.var_95,
        )


class MultiAssetPortfolioBacktester:
    """Multi - asset portfolio backtesting system"""

    def __init__(
        self,
        initial_capital: float = 1000000,
        rebalance_frequency: str = "monthly",
        transaction_costs: float = 0.001,
    ):
        """
        Initialize multi - asset portfolio backtester

        Args:
            initial_capital: Starting portfolio value
            rebalance_frequency: Rebalancing frequency ('daily', 'weekly', 'monthly')
            transaction_costs: Transaction cost rate (0.1% default)
        """
        self.initial_capital = initial_capital
        self.rebalance_frequency = rebalance_frequency
        self.transaction_costs = transaction_costs

        self.portfolio_optimizer = PortfolioOptimizer()
        self.position_sizer = DynamicPositionSizer(initial_capital)

    def backtest_portfolio_strategy(
        self,
        price_data: pd.DataFrame,
        strategy: str = "max_sharpe",
        lookback_window: int = 252,
        rebalance_window: int = 20,
    ) -> Dict[str, Any]:
        """
        Backtest portfolio strategy

        Args:
            price_data: DataFrame of asset prices
            strategy: Portfolio strategy ('max_sharpe', 'min_volatility', 'risk_parity')
            lookback_window: Lookback window for optimization
            rebalance_window: Rebalancing frequency in days

        Returns:
            Dictionary with backtest results
        """

        assets = price_data.columns.tolist()
        dates = price_data.index

        # Calculate returns
        returns = price_data.pct_change().dropna()

        # Initialize portfolio tracking
        portfolio_values = []
        weights_history = []
        rebalance_dates = []

        # Initial allocation
        current_weights = {asset: 1 / len(assets) for asset in assets}
        current_value = self.initial_capital

        # Calculate positions
        current_positions = {}
        for asset, weight in current_weights.items():
            position_value = current_value * weight
            current_positions[asset] = position_value / price_data[asset].iloc[0]

        portfolio_values.append(current_value)
        weights_history.append(current_weights.copy())

        # Rolling window backtest
        for i in range(lookback_window, len(dates)):
            current_date = dates[i]

            # Check if we should rebalance
            if i % rebalance_window == 0:
                rebalance_dates.append(current_date)

                # Get historical data for optimization
                hist_returns = returns.iloc[i - lookback_window : i]

                # Optimize portfolio based on strategy
                if strategy == "max_sharpe":
                    allocation = self.portfolio_optimizer.maximize_sharpe_ratio(
                        hist_returns
                    )
                elif strategy == "min_volatility":
                    allocation = self.portfolio_optimizer.minimize_volatility(
                        hist_returns
                    )
                elif strategy == "risk_parity":
                    risk_parity_weights = (
                        self.position_sizer.calculate_risk_parity_weights(hist_returns)
                    )
                    allocation = PortfolioAllocation(
                        weights = risk_parity_weights,
                        expected_return = 0,  # Not calculated for risk parity
                        expected_volatility = 0,
                        sharpe_ratio = 0,
                        max_drawdown = 0,
                        var_95 = 0,
                    )
                else:
                    raise ValueError(f"Unknown strategy: {strategy}")

                target_weights = allocation.weights

                # Calculate current portfolio value
                current_portfolio_value = sum(
                    current_positions[asset] * price_data[asset].iloc[i]
                    for asset in assets
                )

                # Calculate target positions
                target_positions = {}
                for asset in assets:
                    target_value = current_portfolio_value * target_weights[asset]
                    target_positions[asset] = target_value / price_data[asset].iloc[i]

                # Apply transaction costs
                trades = []
                for asset in assets:
                    trade_size = target_positions[asset] - current_positions[asset]
                    if abs(trade_size) > 0:
                        trade_value = abs(trade_size * price_data[asset].iloc[i])
                        cost = trade_value * self.transaction_costs
                        current_portfolio_value -= cost
                        trades.append((asset, trade_size, cost))

                    current_positions[asset] = target_positions[asset]

                current_weights = target_weights
                current_value = current_portfolio_value

            # Update portfolio value
            current_value = sum(
                current_positions[asset] * price_data[asset].iloc[i] for asset in assets
            )

            portfolio_values.append(current_value)
            weights_history.append(current_weights.copy())

        # Calculate performance metrics
        portfolio_series = pd.Series(
            portfolio_values, index = dates[: len(portfolio_values)]
        )
        portfolio_series.pct_change().dropna()

        risk_calculator = RiskCalculator()
        risk_metrics = risk_calculator.calculate_comprehensive_metrics(portfolio_series)

        return {
            "strategy": strategy,
            "portfolio_values": portfolio_series,
            "weights_history": weights_history,
            "rebalance_dates": rebalance_dates,
            "final_value": portfolio_values[-1],
            "total_return": (portfolio_values[-1] / self.initial_capital) - 1,
            "risk_metrics": risk_metrics,
            "num_rebalances": len(rebalance_dates),
        }


def create_multi_asset_test_data() -> pd.DataFrame:
    """Create test data for multi - asset portfolio analysis"""
    np.random.seed(42)

    dates = pd.date_range("2020 - 01 - 01", "2023 - 12 - 31", freq="D")
    n_assets = 4
    assets = ["STOCK_A", "STOCK_B", "BOND_A", "BOND_B"]

    # Generate correlated returns
    correlation_matrix = np.array(
        [
            [1.0, 0.7, 0.3, 0.2],
            [0.7, 1.0, 0.2, 0.1],
            [0.3, 0.2, 1.0, 0.6],
            [0.2, 0.1, 0.6, 1.0],
        ]
    )

    volatilities = [0.2, 0.25, 0.08, 0.06]  # Annual volatilities
    expected_returns = [0.08, 0.10, 0.04, 0.03]  # Annual expected returns

    # Generate correlated random returns
    n_days = len(dates)
    daily_vol = [v / np.sqrt(252) for v in volatilities]
    daily_ret = [r / 252 for r in expected_returns]

    # Cholesky decomposition for correlation
    chol_matrix = np.linalg.cholesky(correlation_matrix)

    # Generate correlated returns
    random_returns = np.random.normal(0, 1, (n_days, n_assets))
    correlated_returns = random_returns @ chol_matrix.T

    # Scale by volatilities and add expected returns
    for i in range(n_assets):
        correlated_returns[:, i] = (
            correlated_returns[:, i] * daily_vol[i] + daily_ret[i]
        )

    # Convert to prices
    prices = pd.DataFrame(index = dates, columns = assets)
    prices.iloc[0] = 100

    for i in range(1, n_days):
        prices.iloc[i] = prices.iloc[i - 1] * (1 + correlated_returns[i])

    return prices


# Example usage and testing functions


def test_portfolio_optimization():
    """Test portfolio optimization functionality"""
    logger.info("Testing portfolio optimization...")

    # Create test data
    price_data = create_multi_asset_test_data()
    returns = price_data.pct_change().dropna()

    # Initialize optimizer
    optimizer = PortfolioOptimizer()

    # Test efficient frontier
    ef_returns, ef_volatilities, ef_weights = optimizer.calculate_efficient_frontier(
        returns, 50
    )

    # Test maximum Sharpe ratio portfolio
    max_sharpe_portfolio = optimizer.maximize_sharpe_ratio(returns)

    # Test minimum volatility portfolio
    min_vol_portfolio = optimizer.minimize_volatility(returns)

    logger.info(f"Efficient frontier: {len(ef_returns)} portfolios")
    logger.info(
        f"Max Sharpe portfolio: Return={max_sharpe_portfolio.expected_return:.3f}, "
        f"Vol={max_sharpe_portfolio.expected_volatility:.3f}, "
        f"Sharpe={max_sharpe_portfolio.sharpe_ratio:.3f}"
    )
    logger.info(
        f"Min Vol portfolio: Return={min_vol_portfolio.expected_return:.3f}, "
        f"Vol={min_vol_portfolio.expected_volatility:.3f}, "
        f"Sharpe={min_vol_portfolio.sharpe_ratio:.3f}"
    )

    return {
        "efficient_frontier": (ef_returns, ef_volatilities, ef_weights),
        "max_sharpe": max_sharpe_portfolio,
        "min_volatility": min_vol_portfolio,
    }


if __name__ == "__main__":
    # Test portfolio optimization
    test_portfolio_optimization()

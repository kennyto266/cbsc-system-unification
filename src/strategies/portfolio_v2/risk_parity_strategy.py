"""
Risk Parity Strategy Implementation
風險平價策略實現

This module implements the risk parity portfolio strategy that allocates
capital based on risk contributions rather than market capitalization.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from uuid import UUID
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .base import BasePortfolioStrategy
from ..enhanced_factory import StrategyMetadata, StrategyType

logger = logging.getLogger(__name__)


class RiskParityStrategy(BasePortfolioStrategy):
    """
    Risk Parity Portfolio Strategy

    Allocates capital based on equal risk contribution from each asset.
    Assets with higher volatility get lower weights, and vice versa.
    """

    # Strategy metadata
    STRATEGY_NAME = "risk_parity"
    DESCRIPTION = "Risk parity portfolio strategy with equal risk contributions"

    # Default parameters
    DEFAULT_PARAMETERS = {
        'assets': [],  # List of (symbol, strategy_config) tuples
        'rebalance_frequency': 'M',
        'risk_target': 0.15,  # Target annual volatility
        'lookback_period': 60,
        'volatility_floor': 0.02,  # Minimum volatility estimate
        'volatility_cap': 1.0,  # Maximum volatility estimate
        'correlation_adjustment': True,
        'max_weight': 0.4,  # Maximum weight for any single asset
        'min_weight': 0.05,  # Minimum weight for included assets
        'risk_parity_method': 'iterative'  # 'iterative', 'ccd', 'optimization'
    }

    # Required parameters
    REQUIRED_PARAMETERS = ['assets']

    # Optional parameters
    OPTIONAL_PARAMETERS = {
        'rebalance_frequency': {
            'type': str,
            'choices': ['D', 'W', 'M', 'Q'],
            'default': 'M'
        },
        'risk_target': {
            'type': float,
            'min': 0.01,
            'max': 0.5,
            'default': 0.15
        },
        'lookback_period': {
            'type': int,
            'min': 10,
            'max': 252,
            'default': 60
        },
        'volatility_floor': {
            'type': float,
            'min': 0.001,
            'max': 0.1,
            'default': 0.02
        },
        'volatility_cap': {
            'type': float,
            'min': 0.1,
            'max': 2.0,
            'default': 1.0
        },
        'correlation_adjustment': {
            'type': bool,
            'default': True
        },
        'max_weight': {
            'type': float,
            'min': 0.1,
            'max': 1.0,
            'default': 0.4
        },
        'min_weight': {
            'type': float,
            'min': 0.001,
            'max': 0.5,
            'default': 0.05
        },
        'risk_parity_method': {
            'type': str,
            'choices': ['iterative', 'ccd', 'optimization'],
            'default': 'iterative'
        }
    }

    def __init__(
        self,
        instance_id: UUID,
        config: Dict[str, Any],
        metadata: StrategyMetadata
    ):
        """
        Initialize risk parity strategy

        Args:
            instance_id: Unique instance identifier
            config: Strategy configuration
            metadata: Strategy metadata
        """
        super().__init__(instance_id, config, metadata)

        self.volatility_floor = config.get('volatility_floor', 0.02)
        self.volatility_cap = config.get('volatility_cap', 1.0)
        self.correlation_adjustment = config.get('correlation_adjustment', True)
        self.max_weight = config.get('max_weight', 0.4)
        self.min_weight = config.get('min_weight', 0.05)
        self.risk_parity_method = config.get('risk_parity_method', 'iterative')

        # Initialize asset list
        self.asset_list = config.get('assets', [])
        self.asset_symbols = [asset[0] for asset in self.asset_list]

        # Cache for risk calculations
        self._risk_cache = {}

    def calculate_returns(
        self,
        data: Dict[str, pd.DataFrame],
        symbols: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Calculate returns for specified assets

        Args:
            data: Dictionary of asset data
            symbols: List of symbols to include

        Returns:
            DataFrame of returns
        """
        if symbols is None:
            symbols = self.asset_symbols

        returns_list = {}
        for symbol in symbols:
            if symbol in data and 'close' in data[symbol].columns:
                prices = data[symbol]['close']
                asset_returns = prices.pct_change().dropna()

                if len(asset_returns) >= self.lookback_period:
                    returns_list[symbol] = asset_returns.tail(self.lookback_period)

        if not returns_list:
            return pd.DataFrame()

        # Align returns
        returns_df = pd.DataFrame(returns_list)
        return returns_df.fillna(0)

    def calculate_volatility_estimates(
        self,
        returns: pd.DataFrame
    ) -> pd.Series:
        """
        Calculate volatility estimates with floor and cap

        Args:
            returns: DataFrame of asset returns

        Returns:
            Series of volatility estimates
        """
        volatilities = returns.std() * np.sqrt(252)  # Annualized

        # Apply floor and cap
        volatilities = volatilities.clip(lower=self.volatility_floor, upper=self.volatility_cap)

        return volatilities

    def calculate_inverse_volatility_weights(
        self,
        volatilities: pd.Series
    ) -> pd.Series:
        """
        Calculate inverse volatility weights

        Args:
            volatilities: Series of volatilities

        Returns:
            Series of inverse volatility weights
        """
        inv_vols = 1 / volatilities
        weights = inv_vols / inv_vols.sum()

        return weights

    def calculate_risk_parity_weights_iterative(
        self,
        cov_matrix: pd.DataFrame,
        max_iterations: int = 1000,
        tolerance: float = 1e-8
    ) -> np.ndarray:
        """
        Calculate risk parity weights using iterative method

        Args:
            cov_matrix: Covariance matrix
            max_iterations: Maximum iterations
            tolerance: Convergence tolerance

        Returns:
            Array of risk parity weights
        """
        n_assets = len(cov_matrix)
        weights = np.ones(n_assets) / n_assets

        for iteration in range(max_iterations):
            # Calculate risk contributions
            portfolio_vol = np.sqrt(weights.dot(cov_matrix).dot(weights))
            marginal_contrib = cov_matrix.dot(weights)
            risk_contrib = weights * marginal_contrib / portfolio_vol

            # Normalize risk contributions
            risk_contrib_pct = risk_contrib / risk_contrib.sum()

            # Update weights (multiply by inverse of risk contribution)
            new_weights = weights / risk_contrib_pct
            new_weights = new_weights / new_weights.sum()

            # Check convergence
            weight_change = np.abs(new_weights - weights).sum()
            if weight_change < tolerance:
                break

            weights = new_weights

        return weights

    def calculate_risk_parity_weights_optimization(
        self,
        cov_matrix: pd.DataFrame
    ) -> np.ndarray:
        """
        Calculate risk parity weights using optimization

        Args:
            cov_matrix: Covariance matrix

        Returns:
            Array of risk parity weights
        """
        n_assets = len(cov_matrix)

        # Objective function: minimize squared deviation of risk contributions
        def risk_parity_objective(weights):
            portfolio_vol = np.sqrt(weights.dot(cov_matrix).dot(weights))
            marginal_contrib = cov_matrix.dot(weights)
            risk_contrib = weights * marginal_contrib / portfolio_vol

            # Want risk contributions to be equal (1/n_assets each)
            target_contrib = 1.0 / n_assets
            error = risk_contrib - target_contrib

            return np.sum(error ** 2)

        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},  # Weights sum to 1
        ]

        # Bounds
        bounds = [(0.001, 1.0) for _ in range(n_assets)]

        # Initial guess (equal weight)
        x0 = np.ones(n_assets) / n_assets

        # Optimize
        result = minimize(
            risk_parity_objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'ftol': 1e-9, 'disp': False}
        )

        if result.success:
            return result.x
        else:
            logger.warning("Optimization failed, using equal weights")
            return x0

    def calculate_risk_parity_weights(
        self,
        data: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """
        Calculate risk parity weights for assets

        Args:
            data: Dictionary of asset data

        Returns:
            Dictionary of risk parity weights
        """
        # Calculate returns
        returns = self.calculate_returns(data)

        if len(returns) < 2:
            logger.warning("Insufficient data for risk parity calculation")
            return {}

        # Calculate covariance matrix
        cov_matrix = returns.cov() * 252  # Annualized

        # Handle zero diagonal (zero variance assets)
        np.fill_diagonal(cov_matrix.values, np.maximum(
            cov_matrix.values.diagonal(), 0.0001
        ))

        # Apply correlation adjustment if enabled
        if not self.correlation_adjustment:
            # Use only diagonal (variances)
            cov_matrix = pd.DataFrame(
                np.diag(np.diag(cov_matrix)),
                index=cov_matrix.index,
                columns=cov_matrix.columns
            )

        # Calculate weights based on method
        if self.risk_parity_method == 'iterative':
            weights = self.calculate_risk_parity_weights_iterative(cov_matrix)
        elif self.risk_parity_method == 'optimization':
            weights = self.calculate_risk_parity_weights_optimization(cov_matrix)
        else:  # 'ccd' or fallback
            # Simplified cyclical coordinate descent
            weights = self._ccd_risk_parity(cov_matrix)

        # Apply position limits
        weights = self._apply_position_limits(weights, returns.columns.tolist())

        # Create weight dictionary
        weight_dict = {symbol: weight for symbol, weight in zip(returns.columns, weights)}

        return weight_dict

    def _ccd_risk_parity(
        self,
        cov_matrix: pd.DataFrame,
        max_iterations: int = 100
    ) -> np.ndarray:
        """
        Cyclical Coordinate Descent for risk parity

        Args:
            cov_matrix: Covariance matrix
            max_iterations: Maximum iterations

        Returns:
            Array of weights
        """
        n_assets = len(cov_matrix)
        weights = np.ones(n_assets) / n_assets

        for _ in range(max_iterations):
            for i in range(n_assets):
                # Calculate weight for asset i given others
                sigma_i = np.sqrt(cov_matrix.iloc[i, i])
                sigma_p_i = 0

                for j in range(n_assets):
                    if j != i:
                        sigma_p_i += weights[j] * cov_matrix.iloc[i, j]

                # New weight to equalize risk contribution
                numerator = sigma_i ** 2
                denominator = sigma_i * np.sqrt(numerator) + sigma_p_i

                if denominator > 0:
                    new_weight_i = numerator / denominator
                    weights[i] = max(0.001, new_weight_i)  # Ensure positive

            # Normalize
            weights = weights / weights.sum()

        return weights

    def _apply_position_limits(
        self,
        weights: np.ndarray,
        symbols: List[str]
    ) -> np.ndarray:
        """
        Apply position limits to weights

        Args:
            weights: Array of weights
            symbols: List of symbols

        Returns:
            Adjusted weights array
        """
        # Apply max weight limit
        weights = np.minimum(weights, self.max_weight)

        # Remove assets below min weight
        weights[weights < self.min_weight] = 0

        # Renormalize
        total_weight = weights.sum()
        if total_weight > 0:
            weights = weights / total_weight

        return weights

    def calculate_allocation_weights(
        self,
        data: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """
        Calculate optimal allocation weights

        Args:
            data: Dictionary of asset data

        Returns:
            Dictionary of asset weights
        """
        weights = self.calculate_risk_parity_weights(data)

        # Adjust for risk target if needed
        if weights:
            # Calculate portfolio volatility with these weights
            returns = self.calculate_returns(data)
            if len(returns) > 1:
                cov_matrix = returns.cov() * 252
                weights_array = np.array([weights.get(s, 0) for s in returns.columns])

                if len(weights_array) > 0 and weights_array.sum() > 0:
                    portfolio_vol = np.sqrt(
                        weights_array.dot(cov_matrix).dot(weights_array)
                    )

                    # Adjust leverage to meet risk target
                    if portfolio_vol > 0:
                        leverage = min(self.risk_target / portfolio_vol, 2.0)  # Cap leverage at 2x
                        weights = {k: v * leverage for k, v in weights.items()}

                        # Renormalize after leverage adjustment
                        total_weight = sum(weights.values())
                        if total_weight > 0:
                            weights = {k: v/total_weight for k, v in weights.items()}

        return weights

    def should_rebalance(
        self,
        data: Dict[str, pd.DataFrame],
        current_date: Optional[datetime] = None
    ) -> bool:
        """
        Determine if portfolio should be rebalanced

        Args:
            data: Dictionary of asset data
            current_date: Current date

        Returns:
            True if rebalancing is needed
        """
        if not self.last_rebalance_date:
            return True

        # Risk parity strategies typically rebalance based on:
        # 1. Time schedule
        # 2. Risk budget deviation
        # 3. Volatility regime change

        # Check time-based rebalancing first
        if current_date is None:
            all_dates = []
            for df in data.values():
                all_dates.extend(df.index.tolist())
            if not all_dates:
                return False
            current_date = max(all_dates)

        time_diff = current_date - self.last_rebalance_date

        # Basic time-based check
        if self.rebalance_frequency == 'D' and time_diff.days >= 1:
            return True
        elif self.rebalance_frequency == 'W' and time_diff.days >= 7:
            return True
        elif self.rebalance_frequency == 'M' and time_diff.days >= 30:
            return True
        elif self.rebalance_frequency == 'Q' and time_diff.days >= 90:
            return True

        # Check risk budget deviation (simplified)
        if self.current_weights and len(self.current_weights) > 0:
            # Calculate current risk contributions
            risk_contribs = self.calculate_risk_contributions(
                data, self.current_weights
            )

            # Check if risk contributions deviate significantly from equal
            if risk_contribs:
                contrib_values = list(risk_contribs.values())
                equal_contrib = 1.0 / len(contrib_values)
                max_deviation = max(abs(c - equal_contrib) for c in contrib_values)

                # Rebalance if deviation exceeds 20% of equal contribution
                if max_deviation > 0.2 * equal_contrib:
                    return True

        return False

    def get_risk_metrics(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Get detailed risk metrics for the portfolio

        Args:
            data: Dictionary of asset data

        Returns:
            Dictionary of risk metrics
        """
        metrics = {}

        if not self.current_weights:
            return metrics

        # Calculate returns
        returns = self.calculate_returns(data)
        if len(returns) < 2:
            return metrics

        # Portfolio metrics
        weights_array = np.array([
            self.current_weights.get(s, 0) for s in returns.columns
        ])

        if weights_array.sum() > 0:
            # Volatility
            cov_matrix = returns.cov() * 252
            portfolio_vol = np.sqrt(weights_array.dot(cov_matrix).dot(weights_array))
            metrics['portfolio_volatility'] = float(portfolio_vol)

            # Risk contributions
            risk_contribs = self.calculate_risk_contributions(data, self.current_weights)
            metrics['risk_contributions'] = risk_contribs

            # Diversification ratio
            weighted_vol = sum(
                self.current_weights.get(s, 0) * returns[s].std() * np.sqrt(252)
                for s in returns.columns if s in self.current_weights
            )
            diversification_ratio = weighted_vol / portfolio_vol if portfolio_vol > 0 else 1
            metrics['diversification_ratio'] = float(diversification_ratio)

            # Effective number of bets
            if risk_contribs:
                contrib_values = np.array(list(risk_contribs.values()))
                effective_bets = 1 / np.sum(contrib_values ** 2)
                metrics['effective_number_of_bets'] = float(effective_bets)

        return metrics
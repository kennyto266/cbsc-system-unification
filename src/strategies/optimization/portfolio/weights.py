"""
Portfolio weight allocation algorithms.

Provides equal weight, risk parity, and Kelly criterion allocators
for dynamic portfolio weight distribution.
"""

import logging
from typing import Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class EqualWeightAllocator:
    """
    Equal weight portfolio allocator.

    Assigns equal weight to all strategies (1/n).
    """

    def allocate(self, strategies: List[str]) -> Dict[str, float]:
        """
        Allocate equal weights to strategies.

        Args:
            strategies: List of strategy names

        Returns:
            Dictionary mapping strategy names to equal weights

        Example:
            allocator = EqualWeightAllocator()
            weights = allocator.allocate(['MA', 'RSI', 'ZScore'])
            # Returns: {'MA': 0.333, 'RSI': 0.333, 'ZScore': 0.333}
        """
        if not strategies:
            return {}

        weight = 1.0 / len(strategies)
        return {s: weight for s in strategies}


class RiskParityAllocator:
    """
    Risk parity allocator based on inverse volatility.

    Allocates weights inversely proportional to volatility
    so each strategy contributes equal risk to portfolio.
    """

    def __init__(self, target_volatility: float = 0.0):
        """
        Initialize risk parity allocator.

        Args:
            target_volatility: Target portfolio volatility (default 0.0 = no scaling)
                             If > 0, weights will be scaled to achieve this volatility
        """
        self.target_volatility = target_volatility

    def allocate(
        self,
        strategies: List[str],
        returns: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Allocate weights based on risk parity.

        Args:
            strategies: List of strategy names (column names in returns)
            returns: DataFrame with strategy returns as columns

        Returns:
            Dictionary mapping strategy names to weights

        Algorithm:
            1. Calculate covariance matrix of returns
            2. Calculate volatility (std dev) for each strategy
            3. Calculate inverse volatility weights (1/vol)
            4. Normalize weights so sum = 1.0
            5. Scale to target volatility if needed
        """
        if returns.empty:
            logger.warning("Empty returns DataFrame provided")
            return {}

        # Filter returns to only include requested strategies
        valid_strategies = [s for s in strategies if s in returns.columns]
        if not valid_strategies:
            logger.warning("No valid strategies found in returns")
            return {s: 0.0 for s in strategies}

        filtered_returns = returns[valid_strategies]

        # Calculate covariance matrix
        cov_matrix = filtered_returns.cov()

        # Calculate volatilities (diagonal of covariance matrix)
        volatilities = np.sqrt(np.diag(cov_matrix))

        # Handle zero volatility
        volatilities = pd.Series(volatilities, index=valid_strategies)
        volatilities = volatilities.replace(0, np.nan)

        # Calculate inverse volatility weights
        inv_vol = 1.0 / volatilities

        # Skip NaN values (zero volatility strategies)
        inv_vol = inv_vol.dropna()

        if inv_vol.sum() == 0 or len(inv_vol) == 0:
            logger.warning("Sum of inverse volatilities is zero")
            return {s: 0.0 for s in strategies}

        weights = inv_vol / inv_vol.sum()

        # Scale to target volatility if needed
        if not cov_matrix.empty and self.target_volatility > 0:
            # Filter covariance matrix to match weights (same strategies, same order)
            cov_subset = cov_matrix.loc[weights.index, weights.index]

            # Calculate portfolio volatility with current weights
            weights_array = weights.values
            portfolio_vol = np.sqrt(weights_array @ cov_subset.values @ weights_array.T)

            # Scale to target volatility
            if portfolio_vol > 1e-10:
                scale_factor = self.target_volatility / portfolio_vol
                weights = weights * scale_factor  # Scale Series directly
                # Safety cap to prevent extreme leverage (max 500% per position)
                weights = weights.clip(upper=5.0)

        # Ensure all strategies have weights
        result = {}
        for strategy in strategies:
            result[strategy] = weights.get(strategy, 0.0)

        return result


class KellyAllocator:
    """
    Kelly criterion allocator for maximizing long-term growth.

    Calculates optimal fraction to allocate based on expected
    return and variance.
    """

    def __init__(self, kelly_fraction: float = 0.25):
        """
        Initialize Kelly allocator.

        Args:
            kelly_fraction: Fraction of full Kelly to use (default 0.25 for half-Kelly)
        """
        self.kelly_fraction = kelly_fraction

    def allocate(
        self,
        strategies: List[str],
        returns: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Allocate weights using Kelly criterion.

        Args:
            strategies: List of strategy names (column names in returns)
            returns: DataFrame with strategy returns as columns

        Returns:
            Dictionary mapping strategy names to weights

        Algorithm:
            1. Calculate mean return (mu) and variance (sigma^2) for each strategy
            2. Calculate Kelly weight: w = kelly_fraction * mu / sigma^2
            3. Cap individual weights at 1.0 (max 100% allocation)
            4. If sum > 1.0, normalize to sum = 1.0
            5. Return weights dictionary
        """
        if returns.empty:
            logger.warning("Empty returns DataFrame provided")
            return {}

        weights = {}

        for strategy in strategies:
            if strategy not in returns.columns:
                logger.warning(f"Strategy {strategy} not found in returns")
                weights[strategy] = 0.0
                continue

            series = returns[strategy]
            mu = series.mean()
            sigma2 = series.var()

            # Handle zero variance
            if sigma2 < 1e-10:
                logger.warning(f"Strategy {strategy} has zero variance")
                weights[strategy] = 0.0
                continue

            # Kelly weight: f = kelly_fraction * mu / sigma^2
            kelly_weight = self.kelly_fraction * mu / sigma2

            # Ensure non-negative (negative expected return -> zero weight)
            if kelly_weight < 0:
                kelly_weight = 0.0

            # Cap at 1.0
            weights[strategy] = min(kelly_weight, 1.0)

        # Normalize if total > 1.0
        total = sum(weights.values())

        if total > 1.0:
            logger.info(f"Normalizing weights: total {total:.3f} > 1.0")
            weights = {k: v / total for k, v in weights.items()}
        elif total == 0:
            logger.warning("All weights are zero, using equal weights")
            # Fallback to equal weights if all are zero
            weight = 1.0 / len(strategies) if strategies else 0.0
            weights = {s: weight for s in strategies}

        return weights

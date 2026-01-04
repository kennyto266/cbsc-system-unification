"""
Multi-Factor Strategy Implementation
多因子策略實現

This module implements the multi-factor portfolio strategy that combines
multiple trading factors into a unified portfolio allocation.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import numpy as np
import pandas as pd

from .base import BasePortfolioStrategy
from ..enhanced_factory import StrategyMetadata, StrategyType
from ..enhanced_factory_v2 import StrategyFactoryV2

logger = logging.getLogger(__name__)


class MultiFactorStrategy(BasePortfolioStrategy):
    """
    Multi-Factor Portfolio Strategy

    Combines multiple strategies/factors into a unified portfolio.
    Each factor contributes to the final allocation based on its weight.
    """

    # Strategy metadata
    STRATEGY_NAME = "multi_factor"
    DESCRIPTION = "Multi-factor portfolio strategy combining multiple trading signals"

    # Default parameters
    DEFAULT_PARAMETERS = {
        'factors': [],  # List of (strategy_name, weight, config) tuples
        'rebalance_frequency': 'M',
        'min_positions': 1,
        'max_positions': 10,
        'factor_combination_method': 'weighted_average',  # 'weighted_average', 'rank_based'
        'signal_threshold': 0.5,
        'risk_parity_adjustment': False
    }

    # Required parameters
    REQUIRED_PARAMETERS = ['factors']

    # Optional parameters
    OPTIONAL_PARAMETERS = {
        'rebalance_frequency': {
            'type': str,
            'choices': ['D', 'W', 'M', 'Q'],
            'default': 'M'
        },
        'min_positions': {
            'type': int,
            'min': 1,
            'max': 50,
            'default': 1
        },
        'max_positions': {
            'type': int,
            'min': 1,
            'max': 100,
            'default': 10
        },
        'factor_combination_method': {
            'type': str,
            'choices': ['weighted_average', 'rank_based'],
            'default': 'weighted_average'
        },
        'signal_threshold': {
            'type': float,
            'min': 0.0,
            'max': 2.0,
            'default': 0.5
        },
        'risk_parity_adjustment': {
            'type': bool,
            'default': False
        }
    }

    def __init__(
        self,
        instance_id: UUID,
        config: Dict[str, Any],
        metadata: StrategyMetadata
    ):
        """
        Initialize multi-factor strategy

        Args:
            instance_id: Unique instance identifier
            config: Strategy configuration
            metadata: Strategy metadata
        """
        super().__init__(instance_id, config, metadata)

        self.factors = config.get('factors', [])
        self.factor_combination_method = config.get('factor_combination_method', 'weighted_average')
        self.signal_threshold = config.get('signal_threshold', 0.5)
        self.risk_parity_adjustment = config.get('risk_parity_adjustment', False)

        # Initialize strategy factory
        self.factory = StrategyFactoryV2()

        # Create factor strategies
        self.factor_strategies = {}
        self._initialize_factors()

        # Track factor contributions
        self.factor_contributions = {}

    def _initialize_factors(self):
        """Initialize factor strategies"""
        total_weight = 0

        for factor_config in self.factors:
            if isinstance(factor_config, dict):
                strategy_name = factor_config.get('name')
                weight = factor_config.get('weight', 1.0)
                strategy_config = factor_config.get('config', {})
            else:
                # Legacy tuple format (name, weight, config)
                strategy_name, weight, strategy_config = factor_config

            if strategy_name and weight > 0:
                try:
                    # Create strategy instance
                    strategy = self.factory.create_strategy(
                        strategy_name,
                        strategy_config
                    )

                    self.factor_strategies[strategy_name] = {
                        'strategy': strategy,
                        'weight': weight,
                        'config': strategy_config
                    }

                    total_weight += weight
                    logger.info(f"Initialized factor: {strategy_name} with weight {weight}")

                except Exception as e:
                    logger.error(f"Failed to initialize factor {strategy_name}: {e}")

        # Normalize weights
        if total_weight > 0:
            for factor_name in self.factor_strategies:
                self.factor_strategies[factor_name]['weight'] /= total_weight

        if not self.factor_strategies:
            raise ValueError("No valid factors could be initialized")

    def generate_factor_signals(
        self,
        data: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        """
        Generate signals from all factors

        Args:
            data: Dictionary of asset data

        Returns:
            Dictionary of factor signals
        """
        factor_signals = {}

        for factor_name, factor_info in self.factor_strategies.items():
            try:
                strategy = factor_info['strategy']

                # Execute strategy
                result = strategy.execute(data)

                # Extract signals for each asset
                asset_signals = {}
                for symbol, symbol_result in result.get('results', {}).items():
                    if 'signals' in symbol_result and len(symbol_result['signals']) > 0:
                        signals_df = symbol_result['signals']
                        # Get the latest signal value
                        if 'signal' in signals_df.columns:
                            asset_signals[symbol] = signals_df['signal'].iloc[-1]
                        elif f"{symbol}_signal" in signals_df.columns:
                            asset_signals[symbol] = signals_df[f"{symbol}_signal"].iloc[-1]
                        elif 'signal_type' in signals_df.columns:
                            # Convert BUY/HOLD/SELL to numeric
                            signal_map = {'BUY': 1, 'HOLD': 0, 'SELL': -1}
                            asset_signals[symbol] = signal_map.get(
                                signals_df['signal_type'].iloc[-1], 0
                            )

                factor_signals[factor_name] = pd.Series(asset_signals)

            except Exception as e:
                logger.error(f"Failed to generate signals for factor {factor_name}: {e}")
                factor_signals[factor_name] = pd.Series()

        return factor_signals

    def combine_factors(
        self,
        factor_signals: Dict[str, pd.Series]
    ) -> pd.Series:
        """
        Combine factor signals into unified signal

        Args:
            factor_signals: Dictionary of factor signals

        Returns:
            Combined signal series
        """
        if not factor_signals:
            return pd.Series()

        # Align all signals
        all_symbols = set()
        for signals in factor_signals.values():
            if isinstance(signals, pd.Series):
                all_symbols.update(signals.index)

        if not all_symbols:
            return pd.Series()

        # Create combined signal DataFrame
        combined_df = pd.DataFrame(index=list(all_symbols))

        for factor_name, signals in factor_signals.items():
            if isinstance(signals, pd.Series):
                weight = self.factor_strategies[factor_name]['weight']
                combined_df[factor_name] = signals * weight
            else:
                combined_df[factor_name] = 0

        # Combine based on method
        if self.factor_combination_method == 'weighted_average':
            # Simple weighted average
            combined_signal = combined_df.fillna(0).sum(axis=1)
        else:  # rank_based
            # Rank-based combination
            rank_signals = combined_df.fillna(0).rank(axis=0)
            for factor_name, factor_info in self.factor_strategies.items():
                if factor_name in rank_signals.columns:
                    rank_signals[factor_name] *= factor_info['weight']
            combined_signal = rank_signals.sum(axis=1)

        # Apply signal threshold
        final_signal = pd.Series(0, index=combined_signal.index)
        final_signal[combined_signal > self.signal_threshold] = 1
        final_signal[combined_signal < -self.signal_threshold] = -1

        return final_signal

    def calculate_allocation_weights(
        self,
        data: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """
        Calculate optimal allocation weights based on multi-factor signals

        Args:
            data: Dictionary of asset data

        Returns:
            Dictionary of asset weights
        """
        # Generate factor signals
        factor_signals = self.generate_factor_signals(data)

        # Combine factors
        combined_signal = self.combine_factors(factor_signals)

        if combined_signal.empty:
            return {}

        # Calculate initial weights based on signal strength
        weights = {}
        positive_signals = combined_signal[combined_signal > 0]

        if len(positive_signals) > 0:
            # Equal weight among positive signals
            equal_weight = 1.0 / len(positive_signals)

            for symbol in positive_signals.index:
                weights[symbol] = equal_weight
        else:
            # No positive signals, use current weights or equal weight
            if self.current_weights:
                return self.current_weights
            else:
                # Equal weight across all assets
                symbols = list(data.keys())
                equal_weight = 1.0 / len(symbols) if symbols else 1.0
                weights = {symbol: equal_weight for symbol in symbols}

        # Apply risk parity adjustment if enabled
        if self.risk_parity_adjustment:
            weights = self._apply_risk_parity_adjustment(data, weights)

        # Apply position limits
        weights = self._apply_position_limits(weights)

        return weights

    def _apply_risk_parity_adjustment(
        self,
        data: Dict[str, pd.DataFrame],
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        """Apply risk parity adjustment to weights"""
        # Calculate recent returns
        returns = {}
        for symbol in weights:
            if symbol in data:
                asset_returns = data[symbol]['close'].pct_change().dropna()
                if len(asset_returns) >= self.lookback_period:
                    returns[symbol] = asset_returns.tail(self.lookback_period)

        if len(returns) < 2:
            return weights

        # Create returns DataFrame
        returns_df = pd.DataFrame(returns).fillna(0)
        returns_df = returns_df * 252  # Annualize

        # Calculate volatilities
        volatilities = returns_df.std()
        inv_vols = 1 / volatilities

        # Combine with equal weight and signal weights
        risk_parity_weights = inv_vols / inv_vols.sum()

        # Blend with original weights
        adjusted_weights = {}
        for symbol in weights:
            signal_weight = weights.get(symbol, 0)
            rp_weight = risk_parity_weights.get(symbol, 0)
            # 50% signal, 50% risk parity
            adjusted_weights[symbol] = 0.5 * signal_weight + 0.5 * rp_weight

        # Normalize
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            adjusted_weights = {k: v/total_weight for k, v in adjusted_weights.items()}

        return adjusted_weights

    def _apply_position_limits(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Apply position limits to weights"""
        # Filter by minimum weight threshold
        filtered_weights = {
            symbol: weight for symbol, weight in weights.items()
            if weight > 0.01  # 1% minimum weight
        }

        # Check position count
        active_positions = len(filtered_weights)

        if active_positions > self.max_positions:
            # Keep top N positions by weight
            sorted_weights = sorted(
                filtered_weights.items(),
                key=lambda x: x[1],
                reverse=True
            )
            filtered_weights = dict(sorted_weights[:self.max_positions])

        elif active_positions < self.min_positions:
            # Add more positions if below minimum
            # Use remaining assets with equal weight
            current_symbols = set(filtered_weights.keys())
            additional_needed = self.min_positions - active_positions

            # (In practice, would have a universe of assets to draw from)
            for i in range(additional_needed):
                symbol = f"additional_asset_{i}"
                if symbol not in current_symbols:
                    filtered_weights[symbol] = 0.01

        # Normalize weights
        total_weight = sum(filtered_weights.values())
        if total_weight > 0:
            filtered_weights = {k: v/total_weight for k, v in filtered_weights.items()}

        return filtered_weights

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

        # Check rebalancing frequency
        if current_date is None:
            # Get latest date from data
            all_dates = []
            for df in data.values():
                all_dates.extend(df.index.tolist())
            if not all_dates:
                return False
            current_date = max(all_dates)

        # Calculate time since last rebalance
        time_diff = current_date - self.last_rebalance_date

        # Check based on frequency
        if self.rebalance_frequency == 'D':
            return time_diff.days >= 1
        elif self.rebalance_frequency == 'W':
            return time_diff.days >= 7
        elif self.rebalance_frequency == 'M':
            return time_diff.days >= 30
        elif self.rebalance_frequency == 'Q':
            return time_diff.days >= 90

        return False

    def get_factor_contributions(self) -> Dict[str, Dict[str, float]]:
        """
        Get recent factor contributions to portfolio

        Returns:
            Dictionary of factor contributions
        """
        return self.factor_contributions.copy()

    def update_factor_contributions(
        self,
        factor_signals: Dict[str, pd.Series]
    ):
        """
        Update factor contributions for tracking

        Args:
            factor_signals: Dictionary of factor signals
        """
        contributions = {}

        for factor_name, signals in factor_signals.items():
            if isinstance(signals, pd.Series) and len(signals) > 0:
                weight = self.factor_strategies[factor_name]['weight']
                contributions[factor_name] = {
                    'weight': weight,
                    'average_signal': float(signals.mean()),
                    'signal_strength': float(signals.abs().mean()),
                    'active_positions': int((signals != 0).sum())
                }

        self.factor_contributions = contributions

    def get_factor_analysis(self) -> Dict[str, Any]:
        """
        Get detailed factor analysis

        Returns:
            Dictionary with factor analysis
        """
        analysis = {
            'factor_count': len(self.factor_strategies),
            'factors': [],
            'combination_method': self.factor_combination_method,
            'signal_threshold': self.signal_threshold,
            'risk_parity_adjustment': self.risk_parity_adjustment
        }

        for factor_name, factor_info in self.factor_strategies.items():
            factor_data = {
                'name': factor_name,
                'weight': factor_info['weight'],
                'strategy_type': factor_info['strategy'].__class__.__name__
            }

            if factor_name in self.factor_contributions:
                factor_data.update(self.factor_contributions[factor_name])

            analysis['factors'].append(factor_data)

        return analysis
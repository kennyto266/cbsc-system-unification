"""
Base Portfolio Strategy
組合策略基類

This module provides the base class for all portfolio management strategies.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from uuid import UUID

import pandas as pd
import numpy as np

from ..base import BaseStrategy
from ..enhanced_factory import StrategyMetadata, StrategyType

logger = logging.getLogger(__name__)


class BasePortfolioStrategy(BaseStrategy):
    """
    Base class for portfolio management strategies

    Portfolio strategies manage multiple assets or strategies,
    handling allocation, rebalancing, and risk management.
    """

    # Strategy metadata
    STRATEGY_TYPE = StrategyType.PORTFOLIO

    # Default parameters
    DEFAULT_PARAMETERS = {
        'rebalance_frequency': 'M',  # 'D', 'W', 'M', 'Q'
        'min_positions': 1,
        'max_positions': 10,
        'risk_target': 0.15,
        'lookback_period': 60
    }

    # Required parameters
    REQUIRED_PARAMETERS = ['assets']

    # Optional parameters with validation
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
        'risk_target': {
            'type': float,
            'min': 0.01,
            'max': 1.0,
            'default': 0.15
        },
        'lookback_period': {
            'type': int,
            'min': 10,
            'max': 252,
            'default': 60
        }
    }

    def __init__(
        self,
        instance_id: UUID,
        config: Dict[str, Any],
        metadata: StrategyMetadata
    ):
        """
        Initialize portfolio strategy

        Args:
            instance_id: Unique instance identifier
            config: Strategy configuration
            metadata: Strategy metadata
        """
        super().__init__(instance_id, config, metadata)

        self.assets = config.get('assets', [])
        self.rebalance_frequency = config.get('rebalance_frequency', 'M')
        self.min_positions = config.get('min_positions', 1)
        self.max_positions = config.get('max_positions', 10)
        self.risk_target = config.get('risk_target', 0.15)
        self.lookback_period = config.get('lookback_period', 60)

        # Portfolio state
        self.current_weights = {}
        self.last_rebalance_date = None
        self.portfolio_value_history = []

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    def validate_portfolio_constraints(
        self,
        weights: Dict[str, float]
    ) -> bool:
        """
        Validate portfolio constraints

        Args:
            weights: Dictionary of asset weights

        Returns:
            True if constraints are satisfied
        """
        # Check weight sum
        total_weight = sum(weights.values())
        if not np.isclose(total_weight, 1.0, atol=1e-6):
            logger.warning(f"Weights sum to {total_weight}, normalizing")
            # Normalize weights
            if total_weight > 0:
                for key in weights:
                    weights[key] /= total_weight

        # Check position count
        active_positions = sum(1 for w in weights.values() if w > 1e-6)
        if active_positions < self.min_positions:
            logger.warning(f"Active positions ({active_positions}) below minimum ({self.min_positions})")
            return False

        if active_positions > self.max_positions:
            logger.warning(f"Active positions ({active_positions}) above maximum ({self.max_positions})")
            return False

        # Check individual weights
        for asset, weight in weights.items():
            if weight < 0 or weight > 1:
                logger.error(f"Invalid weight {weight} for {asset}")
                return False

        return True

    def calculate_portfolio_metrics(
        self,
        data: Dict[str, pd.DataFrame],
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate portfolio performance metrics

        Args:
            data: Dictionary of asset data
            weights: Dictionary of asset weights

        Returns:
            Dictionary of portfolio metrics
        """
        returns = {}

        # Calculate individual asset returns
        for symbol, df in data.items():
            if symbol in weights and weights[symbol] > 0:
                asset_returns = df['close'].pct_change().dropna()
                if len(asset_returns) > 0:
                    returns[symbol] = asset_returns * weights[symbol]

        if not returns:
            return {
                'portfolio_return': 0,
                'portfolio_volatility': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0
            }

        # Combine returns
        portfolio_returns = pd.DataFrame(returns).sum(axis=1)

        # Calculate metrics
        metrics = {}

        # Return
        if len(portfolio_returns) > 0:
            metrics['portfolio_return'] = portfolio_returns.mean() * 252
            metrics['portfolio_volatility'] = portfolio_returns.std() * np.sqrt(252)

            # Sharpe ratio (assuming risk-free rate = 0)
            if metrics['portfolio_volatility'] > 0:
                metrics['sharpe_ratio'] = metrics['portfolio_return'] / metrics['portfolio_volatility']
            else:
                metrics['sharpe_ratio'] = 0

            # Max drawdown
            cumulative = (1 + portfolio_returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            metrics['max_drawdown'] = drawdown.min()
        else:
            metrics = {
                'portfolio_return': 0,
                'portfolio_volatility': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0
            }

        return metrics

    def calculate_risk_contributions(
        self,
        data: Dict[str, pd.DataFrame],
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate risk contributions for each asset

        Args:
            data: Dictionary of asset data
            weights: Dictionary of asset weights

        Returns:
            Dictionary of risk contributions
        """
        # Get returns matrix
        returns_list = []
        assets = []

        for symbol, df in data.items():
            if symbol in weights and weights[symbol] > 0:
                returns = df['close'].pct_change().dropna()
                if len(returns) >= self.lookback_period:
                    returns_list.append(returns.tail(self.lookback_period))
                    assets.append(symbol)

        if len(returns_list) < 2:
            return {symbol: 1.0/len(weights) for symbol in weights}

        # Create returns DataFrame
        returns_df = pd.concat(returns_list, axis=1)
        returns_df.columns = assets

        # Calculate covariance matrix
        cov_matrix = returns_df.cov() * 252  # Annualized

        # Get weights array
        weights_array = np.array([weights.get(asset, 0) for asset in assets])

        # Calculate marginal contributions
        portfolio_volatility = np.sqrt(weights_array.dot(cov_matrix).dot(weights_array))

        if portfolio_volatility > 0:
            marginal_contrib = cov_matrix.dot(weights_array)
            contrib = weights_array * marginal_contrib
            risk_contrib = contrib / portfolio_volatility

            # Normalize to percentages
            risk_contrib_pct = risk_contrib / risk_contrib.sum()

            return {asset: float(risk_contrib_pct[i])
                   for i, asset in enumerate(assets)}
        else:
            return {asset: 1.0/len(assets) for asset in assets}

    def generate_signals(
        self,
        data: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Generate portfolio rebalancing signals

        Args:
            data: Dictionary of asset data

        Returns:
            DataFrame with rebalancing signals
        """
        # Check if rebalancing is needed
        if not self.should_rebalance(data):
            # Return empty signals if no rebalancing needed
            all_dates = set()
            for df in data.values():
                all_dates.update(df.index)

            if all_dates:
                signals_df = pd.DataFrame(0, index=sorted(all_dates), columns=['portfolio_signal'])
                return signals_df
            else:
                return pd.DataFrame()

        # Calculate new weights
        new_weights = self.calculate_allocation_weights(data)

        # Validate constraints
        if not self.validate_portfolio_constraints(new_weights):
            logger.error("Portfolio constraints violated, using current weights")
            new_weights = self.current_weights or {}

        # Generate rebalancing signals
        # Find most recent date across all assets
        all_dates = []
        for df in data.values():
            all_dates.extend(df.index.tolist())

        if not all_dates:
            return pd.DataFrame()

        latest_date = max(all_dates)

        # Compare with current weights
        signals = {}
        for asset in set(list(new_weights.keys()) + list(self.current_weights.keys())):
            current_weight = self.current_weights.get(asset, 0)
            new_weight = new_weights.get(asset, 0)

            # Generate signal if weight changed significantly
            weight_change = abs(new_weight - current_weight)
            if weight_change > 0.05:  # 5% change threshold
                if new_weight > current_weight:
                    signals[asset] = 1  # Buy signal
                elif new_weight < current_weight:
                    signals[asset] = -1  # Sell signal
            else:
                signals[asset] = 0  # Hold

        # Create signals DataFrame
        signals_df = pd.DataFrame([signals], index=[latest_date])
        signals_df.columns = [f"{col}_signal" for col in signals_df.columns]

        # Add portfolio signal
        signals_df['portfolio_signal'] = 1 if len(signals) > 0 else 0

        # Update current weights
        self.current_weights = new_weights
        self.last_rebalance_date = latest_date

        return signals_df

    def get_portfolio_status(self) -> Dict[str, Any]:
        """
        Get current portfolio status

        Returns:
            Dictionary with portfolio status
        """
        return {
            'strategy_id': self.instance_id,
            'strategy_name': self.STRATEGY_NAME,
            'current_weights': self.current_weights,
            'last_rebalance_date': self.last_rebalance_date,
            'rebalance_frequency': self.rebalance_frequency,
            'risk_target': self.risk_target,
            'active_positions': sum(1 for w in self.current_weights.values() if w > 1e-6)
        }

    def execute(
        self,
        data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Execute portfolio strategy

        Args:
            data: Dictionary of asset data

        Returns:
            Dictionary with execution results
        """
        start_time = datetime.now()

        try:
            # Generate rebalancing signals
            signals = self.generate_signals(data)

            # Calculate portfolio metrics
            metrics = {}
            if self.current_weights:
                metrics = self.calculate_portfolio_metrics(data, self.current_weights)
                risk_contrib = self.calculate_risk_contributions(data, self.current_weights)
                metrics['risk_contributions'] = risk_contrib

            # Prepare results for each asset
            results = {}
            for symbol, df in data.items():
                if symbol in signals.columns or any(col.startswith(symbol) for col in signals.columns):
                    asset_signals = signals.filter(like=symbol)
                    results[symbol] = {
                        'signals': asset_signals,
                        'current_weight': self.current_weights.get(symbol, 0),
                        'price_history': df
                    }

            # Add portfolio level results
            results['_portfolio'] = {
                'signals': signals,
                'metrics': metrics,
                'status': self.get_portfolio_status()
            }

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                'strategy_id': str(self.instance_id),
                'strategy_name': self.STRATEGY_NAME,
                'execution_time': execution_time,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Portfolio strategy execution failed: {e}")
            raise

    def backtest(
        self,
        data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Backtest portfolio strategy

        Args:
            data: Dictionary of asset data

        Returns:
            Dictionary with backtest results
        """
        # For portfolio strategies, backtest involves simulating
        # periodic rebalancing based on historical data

        results = {
            'strategy': {
                'name': self.STRATEGY_NAME,
                'type': self.STRATEGY_TYPE.value,
                'parameters': self.config
            },
            'backtest_period': {
                'start': min(df.index.min() for df in data.values() if len(df) > 0),
                'end': max(df.index.max() for df in data.values() if len(df) > 0)
            },
            'backtest_results': {}
        }

        # Run execution
        execution_result = self.execute(data)
        results['execution_result'] = execution_result

        # Add portfolio-specific metrics
        if '_portfolio' in execution_result['results']:
            portfolio_data = execution_result['results']['_portfolio']
            results['backtest_results']['_portfolio'] = {
                'portfolio_metrics': portfolio_data.get('metrics', {}),
                'final_weights': self.current_weights,
                'rebalance_count': self._count_rebalances(data)
            }

        return results

    def _count_rebalances(self, data: Dict[str, pd.DataFrame]) -> int:
        """Count number of rebalancing events"""
        # This is a simplified implementation
        # In practice, would track historical rebalancing dates
        return 0
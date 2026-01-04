"""
Dynamic Asset Allocation Strategy Implementation
動態資產配置策略實現

This module implements a dynamic asset allocation strategy that adjusts
portfolio weights based on market conditions, volatility regimes, and momentum.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import numpy as np
import pandas as pd

from .base import BasePortfolioStrategy
from ..enhanced_factory import StrategyMetadata, StrategyType

logger = logging.getLogger(__name__)


class DynamicAllocationStrategy(BasePortfolioStrategy):
    """
    Dynamic Asset Allocation Strategy

    Adjusts portfolio allocation based on market conditions,
    volatility regimes, and momentum signals.
    """

    # Strategy metadata
    STRATEGY_NAME = "dynamic_allocation"
    DESCRIPTION = "Dynamic asset allocation strategy with regime-based adjustments"

    # Default parameters
    DEFAULT_PARAMETERS = {
        'assets': [],  # List of (symbol, strategy_config) tuples
        'rebalance_frequency': 'W',
        'volatility_window': 20,
        'momentum_window': 60,
        'aggressive_vol_threshold': 0.25,  # High volatility threshold
        'defensive_vol_threshold': 0.15,  # Low volatility threshold
        'momentum_threshold': 0.02,  # Momentum significance threshold
        'max_concentration': 0.6,  # Maximum concentration in top assets
        'min_diversification': 0.7,  # Minimum number of assets to hold
        'trend_following_weight': 0.6,  # Weight for trend following
        'mean_reversion_weight': 0.4,  # Weight for mean reversion
        'regime_detection_method': 'volatility'  # 'volatility', 'trend', 'combined'
    }

    # Required parameters
    REQUIRED_PARAMETERS = ['assets']

    # Optional parameters
    OPTIONAL_PARAMETERS = {
        'rebalance_frequency': {
            'type': str,
            'choices': ['D', 'W', 'M', 'Q'],
            'default': 'W'
        },
        'volatility_window': {
            'type': int,
            'min': 5,
            'max': 100,
            'default': 20
        },
        'momentum_window': {
            'type': int,
            'min': 10,
            'max': 252,
            'default': 60
        },
        'aggressive_vol_threshold': {
            'type': float,
            'min': 0.1,
            'max': 0.5,
            'default': 0.25
        },
        'defensive_vol_threshold': {
            'type': float,
            'min': 0.05,
            'max': 0.3,
            'default': 0.15
        },
        'momentum_threshold': {
            'type': float,
            'min': 0.001,
            'max': 0.1,
            'default': 0.02
        },
        'max_concentration': {
            'type': float,
            'min': 0.3,
            'max': 1.0,
            'default': 0.6
        },
        'min_diversification': {
            'type': int,
            'min': 1,
            'max': 20,
            'default': 7
        },
        'trend_following_weight': {
            'type': float,
            'min': 0.0,
            'max': 1.0,
            'default': 0.6
        },
        'mean_reversion_weight': {
            'type': float,
            'min': 0.0,
            'max': 1.0,
            'default': 0.4
        },
        'regime_detection_method': {
            'type': str,
            'choices': ['volatility', 'trend', 'combined'],
            'default': 'volatility'
        }
    }

    def __init__(
        self,
        instance_id: UUID,
        config: Dict[str, Any],
        metadata: StrategyMetadata
    ):
        """
        Initialize dynamic allocation strategy

        Args:
            instance_id: Unique instance identifier
            config: Strategy configuration
            metadata: Strategy metadata
        """
        super().__init__(instance_id, config, metadata)

        self.vol_window = config.get('volatility_window', 20)
        self.mom_window = config.get('momentum_window', 60)
        self.agg_vol_thresh = config.get('aggressive_vol_threshold', 0.25)
        self.def_vol_thresh = config.get('defensive_vol_threshold', 0.15)
        self.mom_thresh = config.get('momentum_threshold', 0.02)
        self.max_conc = config.get('max_concentration', 0.6)
        self.min_div = config.get('min_diversification', 7)
        self.trend_weight = config.get('trend_following_weight', 0.6)
        self.rev_weight = config.get('mean_reversion_weight', 0.4)
        self.regime_method = config.get('regime_detection_method', 'volatility')

        # Normalize weights
        total_weight = self.trend_weight + self.rev_weight
        if total_weight > 0:
            self.trend_weight /= total_weight
            self.rev_weight /= total_weight

        # Initialize regime history
        self.regime_history = []
        self.last_regime_change = None

    def calculate_returns(
        self,
        data: Dict[str, pd.DataFrame],
        symbol: str
    ) -> pd.Series:
        """
        Calculate returns for a specific asset

        Args:
            data: Dictionary of asset data
            symbol: Asset symbol

        Returns:
            Series of returns
        """
        if symbol not in data:
            return pd.Series()

        prices = data[symbol]['close']
        returns = prices.pct_change().dropna()

        return returns

    def calculate_volatility_regime(
        self,
        returns: pd.Series
    ) -> str:
        """
        Determine volatility regime based on returns

        Args:
            returns: Series of returns

        Returns:
            Regime type: 'aggressive', 'moderate', or 'defensive'
        """
        if len(returns) < self.vol_window:
            return 'moderate'

        # Calculate rolling volatility
        vol = returns.rolling(window=self.vol_window).std().iloc[-1] * np.sqrt(252)

        if vol > self.agg_vol_thresh:
            return 'aggressive'
        elif vol < self.def_vol_thresh:
            return 'defensive'
        else:
            return 'moderate'

    def calculate_trend_regime(
        self,
        returns: pd.Series,
        prices: pd.Series
    ) -> str:
        """
        Determine trend regime based on price and returns

        Args:
            returns: Series of returns
            prices: Series of prices

        Returns:
            Regime type: 'bull', 'bear', or 'neutral'
        """
        if len(returns) < self.mom_window:
            return 'neutral'

        # Calculate momentum metrics
        momentum = returns.rolling(window=self.mom_window).mean().iloc[-1]
        price_trend = (prices.iloc[-1] - prices.iloc[-min(self.mom_window, len(prices))]) / prices.iloc[-min(self.mom_window, len(prices))]

        # Determine regime
        if momentum > self.mom_thresh and price_trend > self.mom_thresh:
            return 'bull'
        elif momentum < -self.mom_thresh and price_trend < -self.mom_thresh:
            return 'bear'
        else:
            return 'neutral'

    def detect_market_regime(
        self,
        data: Dict[str, pd.DataFrame]
    ) -> Dict[str, str]:
        """
        Detect overall market regime

        Args:
            data: Dictionary of asset data

        Returns:
            Dictionary with regime information
        """
        regime_info = {
            'volatility_regime': 'moderate',
            'trend_regime': 'neutral',
            'combined_regime': 'moderate',
            'regime_strength': 0.5
        }

        # Get market proxy (use first asset or create market index)
        market_returns = None
        market_prices = None

        if data:
            # Use first asset as market proxy (in practice, would use market index)
            first_symbol = list(data.keys())[0]
            market_returns = self.calculate_returns(data, first_symbol)
            market_prices = data[first_symbol]['close']

        if market_returns is not None and len(market_returns) > 0:
            # Volatility regime
            vol_regime = self.calculate_volatility_regime(market_returns)
            regime_info['volatility_regime'] = vol_regime

            # Trend regime
            trend_regime = self.calculate_trend_regime(market_returns, market_prices)
            regime_info['trend_regime'] = trend_regime

            # Combined regime
            if self.regime_method == 'volatility':
                regime_info['combined_regime'] = vol_regime
            elif self.regime_method == 'trend':
                regime_info['combined_regime'] = trend_regime
            else:  # combined
                if vol_regime == 'aggressive' and trend_regime == 'bear':
                    regime_info['combined_regime'] = 'defensive'
                elif vol_regime == 'defensive' and trend_regime == 'bull':
                    regime_info['combined_regime'] = 'moderate'
                elif vol_regime == 'aggressive' and trend_regime == 'bull':
                    regime_info['combined_regime'] = 'aggressive'
                else:
                    regime_info['combined_regime'] = 'moderate'

        return regime_info

    def calculate_momentum_scores(
        self,
        data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate momentum scores for all assets

        Args:
            data: Dictionary of asset data

        Returns:
            Dictionary with momentum information for each asset
        """
        momentum_scores = {}

        for symbol, df in data.items():
            if len(df) < self.mom_window:
                continue

            prices = df['close']
            returns = prices.pct_change().dropna()

            if len(returns) < self.mom_window:
                continue

            # Calculate various momentum measures
            momentum_info = {}

            # Price momentum
            price_mom = (prices.iloc[-1] - prices.iloc[-self.mom_window]) / prices.iloc[-self.mom_window]
            momentum_info['price_momentum'] = float(price_mom)

            # Return momentum
            return_mom = returns.rolling(window=self.mom_window).mean().iloc[-1]
            momentum_info['return_momentum'] = float(return_mom)

            # Trend strength (based on R² of linear trend)
            x = np.arange(len(prices.tail(self.mom_window)))
            y = prices.tail(self.mom_window).values
            if len(x) > 1:
                slope, _, r_value, _, _ = np.polyfit(x, y, 1, full=True)
                momentum_info['trend_strength'] = float(r_value ** 2)
                momentum_info['trend_slope'] = float(slope)
            else:
                momentum_info['trend_strength'] = 0.0
                momentum_info['trend_slope'] = 0.0

            # Volatility
            vol = returns.rolling(window=self.vol_window).std().iloc[-1] * np.sqrt(252)
            momentum_info['volatility'] = float(vol)

            # Sharpe ratio (annualized)
            if vol > 0:
                sharpe = (return_mom * 252) / vol
                momentum_info['sharpe_ratio'] = float(sharpe)
            else:
                momentum_info['sharpe_ratio'] = 0.0

            momentum_scores[symbol] = momentum_info

        return momentum_scores

    def get_regime_based_weights(
        self,
        regime: str,
        momentum_scores: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """
        Get allocation weights based on regime and momentum scores

        Args:
            regime: Market regime
            momentum_scores: Momentum scores for assets

        Returns:
            Dictionary of asset weights
        """
        weights = {}

        if not momentum_scores:
            return weights

        # Sort assets by momentum score
        scored_assets = []
        for symbol, scores in momentum_scores.items():
            # Composite score (weighted average of different metrics)
            composite_score = (
                0.4 * scores['price_momentum'] +
                0.3 * scores['return_momentum'] +
                0.2 * scores['sharpe_ratio'] * 0.01 +  # Scale Sharpe ratio
                0.1 * scores['trend_strength']
            )
            scored_assets.append((symbol, composite_score))

        scored_assets.sort(key=lambda x: x[1], reverse=True)

        if regime == 'aggressive':
            # Concentrate in top performers
            top_n = max(3, self.min_div // 2)
            for i, (symbol, score) in enumerate(scored_assets[:top_n]):
                if score > 0:
                    weights[symbol] = (1 - 0.1 * i) / top_n  # Decreasing weights

        elif regime == 'defensive':
            # More diversified allocation
            # Equal weight to assets with positive scores
            positive_assets = [(s, sc) for s, sc in scored_assets if sc > 0]
            if positive_assets:
                n_assets = max(self.min_div, len(positive_assets))
                for symbol, _ in positive_assets[:n_assets]:
                    weights[symbol] = 1.0 / n_assets

        else:  # moderate
            # Balanced approach with momentum tilt
            n_assets = max(self.min_div, len(scored_assets))
            base_weight = 1.0 / n_assets

            for i, (symbol, score) in enumerate(scored_assets[:n_assets]):
                # Adjust base weight by momentum score
                adjusted_weight = base_weight * (1 + score)
                weights[symbol] = adjusted_weight

        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v/total_weight for k, v in weights.items()}

        return weights

    def apply_risk_adjustments(
        self,
        weights: Dict[str, float],
        momentum_scores: Dict[str, Dict[str, float]],
        data: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """
        Apply risk adjustments to weights

        Args:
            weights: Initial weights
            momentum_scores: Momentum scores
            data: Asset data

        Returns:
            Adjusted weights
        """
        adjusted_weights = weights.copy()

        # Apply concentration limits
        if adjusted_weights:
            max_weight = max(adjusted_weights.values())
            if max_weight > self.max_conc:
                # Scale down all weights proportionally
                scale_factor = self.max_conc / max_weight
                adjusted_weights = {k: v * scale_factor for k, v in adjusted_weights.items()}

        # Apply volatility adjustments
        for symbol, info in momentum_scores.items():
            if symbol in adjusted_weights and info['volatility'] > self.agg_vol_thresh:
                # Reduce weight for high volatility assets
                adjusted_weights[symbol] *= 0.8

        # Ensure minimum diversification
        if len(adjusted_weights) < self.min_div:
            # Add more assets if below minimum
            available_assets = set(momentum_scores.keys()) - set(adjusted_weights.keys())
            additional_needed = self.min_div - len(adjusted_weights)

            for i, symbol in enumerate(list(available_assets)[:additional_needed]):
                adjusted_weights[symbol] = 0.01  # Small weight

        # Renormalize
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            adjusted_weights = {k: v/total_weight for k, v in adjusted_weights.items()}

        return adjusted_weights

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
        # Detect market regime
        regime_info = self.detect_market_regime(data)
        regime = regime_info['combined_regime']

        # Calculate momentum scores
        momentum_scores = self.calculate_momentum_scores(data)

        # Get regime-based weights
        weights = self.get_regime_based_weights(regime, momentum_scores)

        # Apply risk adjustments
        weights = self.apply_risk_adjustments(weights, momentum_scores, data)

        # Store regime information
        self.current_regime = regime
        self.regime_history.append({
            'date': datetime.now(),
            'regime': regime,
            'regime_info': regime_info
        })

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
        # Always rebalance if no previous rebalance
        if not self.last_rebalance_date:
            return True

        # Check regime change
        if hasattr(self, 'current_regime'):
            regime_info = self.detect_market_regime(data)
            if regime_info['combined_regime'] != self.current_regime:
                return True

        # Time-based rebalancing
        if current_date is None:
            all_dates = []
            for df in data.values():
                all_dates.extend(df.index.tolist())
            if not all_dates:
                return False
            current_date = max(all_dates)

        time_diff = current_date - self.last_rebalance_date

        if self.rebalance_frequency == 'D' and time_diff.days >= 1:
            return True
        elif self.rebalance_frequency == 'W' and time_diff.days >= 7:
            return True
        elif self.rebalance_frequency == 'M' and time_diff.days >= 30:
            return True
        elif self.rebalance_frequency == 'Q' and time_diff.days >= 90:
            return True

        return False

    def get_regime_analysis(self) -> Dict[str, Any]:
        """
        Get detailed regime analysis

        Returns:
            Dictionary with regime analysis
        """
        analysis = {
            'current_regime': getattr(self, 'current_regime', 'unknown'),
            'regime_history': self.regime_history[-10:],  # Last 10 regimes
            'regime_changes': len(self.regime_history)
        }

        # Calculate regime statistics
        if self.regime_history:
            regime_counts = {}
            for entry in self.regime_history:
                regime = entry['regime']
                regime_counts[regime] = regime_counts.get(regime, 0) + 1

            total = len(self.regime_history)
            analysis['regime_distribution'] = {
                regime: count / total for regime, count in regime_counts.items()
            }

        return analysis
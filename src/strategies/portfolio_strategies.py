"""
Portfolio and Multi-Factor Strategies

This module contains advanced portfolio management strategies.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass
import warnings

from .ma_crossover import BaseStrategy, Signal


@dataclass
class Asset:
    """Asset definition for portfolio strategies"""
    symbol: str
    weight: float
    strategy: BaseStrategy
    data: pd.DataFrame


class MultiFactorStrategy(BaseStrategy):
    """
    Multi-Factor Model Strategy

    Combines multiple strategies/factors into a unified signal
    Each factor can have different weights
    """

    def __init__(
        self,
        factors: List[Tuple[BaseStrategy, float, str]],  # (strategy, weight, name)
        rebalance_frequency: str = "M",  # 'D', 'W', 'M'
        min_positions: int = 1,
        max_positions: int = 10
    ):
        """
        Initialize Multi-Factor Strategy

        Args:
            factors: List of (strategy, weight, name) tuples
            rebalance_frequency: Rebalancing frequency
            min_positions: Minimum number of positions
            max_positions: Maximum number of positions
        """
        super().__init__(
            name=f"MultiFactor_{len(factors)}factors",
            params={
                'factors': [(s.name, w, n) for s, w, n in factors],
                'rebalance_frequency': rebalance_frequency,
                'min_positions': min_positions,
                'max_positions': max_positions
            }
        )

        self.factors = factors
        self.rebalance_frequency = rebalance_frequency
        self.min_positions = min_positions
        self.max_positions = max_positions

        # Normalize weights
        total_weight = sum(w for _, w, _ in factors)
        if total_weight > 0:
            self.factors = [(s, w/total_weight, n) for s, w, n in factors]

    def generate_factor_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate signals from all factors"""
        factor_signals = {}

        for strategy, weight, name in self.factors:
            signals = strategy.generate_signals(data)
            factor_signals[name] = signals * weight

        return pd.DataFrame(factor_signals)

    def combine_signals(self, factor_signals: pd.DataFrame) -> pd.Series:
        """Combine factor signals into final signal"""
        # Sum all weighted signals
        combined_signal = factor_signals.sum(axis=1)

        # Normalize to -1, 0, 1
        final_signal = pd.Series(0, index=combined_signal.index)
        final_signal[combined_signal > 0.5] = Signal.BUY.value
        final_signal[combined_signal < -0.5] = Signal.SELL.value

        return final_signal

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate multi-factor signals"""
        factor_signals = self.generate_factor_signals(data)
        combined_signal = self.combine_signals(factor_signals)

        return combined_signal

    def get_factor_contributions(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Get individual factor contributions"""
        factor_signals = self.generate_factor_signals(data)
        contributions = {}

        for _, _, name in self.factors:
            if name in factor_signals.columns:
                contributions[name] = factor_signals[name]

        return contributions


class RiskParityStrategy(BaseStrategy):
    """
    Risk Parity Portfolio Strategy

    Allocates capital based on risk contribution
    Assets with higher volatility get lower weights
    """

    def __init__(
        self,
        assets: List[Asset],
        lookback_period: int = 60,
        rebalance_frequency: str = "M",
        risk_target: float = 0.15  # Target annual volatility
    ):
        """
        Initialize Risk Parity Strategy

        Args:
            assets: List of assets with their strategies
            lookback_period: Period for risk calculation
            rebalance_frequency: Rebalancing frequency
            risk_target: Target portfolio volatility
        """
        super().__init__(
            name=f"RiskParity_{len(assets)}assets",
            params={
                'assets': [(a.symbol, a.weight) for a in assets],
                'lookback_period': lookback_period,
                'rebalance_frequency': rebalance_frequency,
                'risk_target': risk_target
            }
        )

        self.assets = assets
        self.lookback_period = lookback_period
        self.rebalance_frequency = rebalance_frequency
        self.risk_target = risk_target

    def calculate_returns(self, data: pd.Series) -> pd.Series:
        """Calculate returns"""
        return data.pct_change().dropna()

    def calculate_risk_contributions(self, returns: pd.DataFrame) -> pd.DataFrame:
        """Calculate risk contributions for each asset"""
        # Calculate covariance matrix
        cov_matrix = returns.cov() * 252  # Annualized

        # Initialize equal weights
        weights = np.array([1 / len(self.assets)] * len(self.assets))

        # Risk budgeting optimization (simplified)
        # In practice, this would use more sophisticated optimization
        marginal_contrib = cov_matrix.dot(weights)
        risk_contrib = weights * marginal_contrib
        total_risk = np.sqrt(weights.dot(cov_matrix).dot(weights))

        if total_risk > 0:
            risk_contrib_percent = risk_contrib / total_risk
        else:
            risk_contrib_percent = np.ones(len(self.assets)) / len(self.assets)

        return pd.DataFrame(
            risk_contrib_percent.reshape(1, -1),
            columns=[a.symbol for a in self.assets],
            index=returns.index[-1:]
        )

    def calculate_risk_parity_weights(self, returns: pd.DataFrame) -> np.ndarray:
        """Calculate risk parity weights"""
        # Simplified risk parity calculation
        # Use inverse volatility weighting
        volatilities = returns.std() * np.sqrt(252)
        inv_vols = 1 / volatilities
        weights = inv_vols / inv_vols.sum()

        return weights.values

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate risk parity rebalancing signals"""
        # This is a simplified implementation
        # In practice, you'd need individual asset data and more complex logic

        # Generate portfolio signal based on combined strategies
        portfolio_return = pd.Series(0, index=data.index)
        portfolio_value = pd.Series(100000, index=data.index)  # Initial capital

        signals = pd.Series(0, index=data.index)

        # Calculate risk parity weights
        returns = self.calculate_returns(data['close'])
        if len(returns) >= self.lookback_period:
            recent_returns = returns.tail(self.lookback_period)
            weights = self.calculate_risk_parity_weights(
                pd.DataFrame({data.iloc[-1].get('symbol', 'MAIN'): recent_returns})
            )

            # Generate signal based on weighted strategy signals
            combined_score = 0
            for asset in self.assets:
                asset_score = np.random.randn()  # Simplified - would use actual strategy
                combined_score += asset_score * asset.weight

            if combined_score > 0.5:
                signals.iloc[-1] = Signal.BUY.value
            elif combined_score < -0.5:
                signals.iloc[-1] = Signal.SELL.value

        return signals


class DynamicAllocationStrategy(BaseStrategy):
    """
    Dynamic Asset Allocation Strategy

    Adjusts allocation based on market conditions
    Uses volatility regimes and momentum signals
    """

    def __init__(
        self,
        assets: List[Asset],
        volatility_window: int = 20,
        momentum_window: int = 60,
        rebalance_frequency: str = "W",
        aggressive_vol_threshold: float = 0.25,
        defensive_vol_threshold: float = 0.15
    ):
        """
        Initialize Dynamic Allocation Strategy

        Args:
            assets: List of assets with their strategies
            volatility_window: Window for volatility calculation
            momentum_window: Window for momentum calculation
            rebalance_frequency: Rebalancing frequency
            aggressive_vol_threshold: Volatility threshold for aggressive allocation
            defensive_vol_threshold: Volatility threshold for defensive allocation
        """
        super().__init__(
            name=f"DynamicAlloc_{len(assets)}assets",
            params={
                'assets': [(a.symbol, a.weight) for a in assets],
                'volatility_window': volatility_window,
                'momentum_window': momentum_window,
                'rebalance_frequency': rebalance_frequency
            }
        )

        self.assets = assets
        self.vol_window = volatility_window
        self.mom_window = momentum_window
        self.rebalance_frequency = rebalance_frequency
        self.agg_vol_thresh = aggressive_vol_threshold
        self.def_vol_thresh = defensive_vol_threshold

    def calculate_volatility_regime(self, returns: pd.Series) -> str:
        """Determine market volatility regime"""
        vol = returns.rolling(window=self.vol_window).std().iloc[-1] * np.sqrt(252)

        if vol > self.agg_vol_thresh:
            return "aggressive"
        elif vol < self.def_vol_thresh:
            return "defensive"
        else:
            return "moderate"

    def calculate_momentum_scores(self, data: pd.Series) -> float:
        """Calculate momentum score"""
        returns = data.pct_change()
        momentum = returns.rolling(window=self.mom_window).mean().iloc[-1]
        return momentum

    def get_allocation_weights(self, regime: str, momentum_scores: Dict[str, float]) -> Dict[str, float]:
        """Get allocation weights based on regime and momentum"""
        weights = {}

        if regime == "aggressive":
            # Concentrate in high momentum assets
            sorted_assets = sorted(
                momentum_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )
            # Top 3 assets get 80% allocation
            for i, (symbol, _) in enumerate(sorted_assets[:3]):
                weights[symbol] = 0.8 / 3
            # Rest get 20%
            for symbol, _ in sorted_assets[3:]:
                weights[symbol] = 0.2 / max(len(sorted_assets) - 3, 1)

        elif regime == "defensive":
            # Equal weight allocation
            equal_weight = 1.0 / len(self.assets)
            for asset in self.assets:
                weights[asset.symbol] = equal_weight

        else:  # moderate
            # Balanced allocation with momentum tilt
            base_weight = 1.0 / len(self.assets)
            for asset in self.assets:
                symbol = asset.symbol
                mom_score = momentum_scores.get(symbol, 0)
                # Adjust base weight by momentum
                weights[symbol] = base_weight * (1 + mom_score)

        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v/total_weight for k, v in weights.items()}

        return weights

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate dynamic allocation signals"""
        # Calculate market regime
        returns = self.calculate_returns(data['close'])
        regime = self.calculate_volatility_regime(returns)

        # Calculate momentum scores for each asset
        momentum_scores = {}
        for asset in self.assets:
            momentum_scores[asset.symbol] = self.calculate_momentum_scores(asset.data['close'])

        # Get allocation weights
        weights = self.get_allocation_weights(regime, momentum_scores)

        # Generate rebalancing signal if weights changed significantly
        signals = pd.Series(0, index=data.index)

        # Simplified: generate signal based on overall portfolio momentum
        portfolio_momentum = np.mean(list(momentum_scores.values()))
        if portfolio_momentum > 0.02:
            signals.iloc[-1] = Signal.BUY.value
        elif portfolio_momentum < -0.02:
            signals.iloc[-1] = Signal.SELL.value

        return signals


class PairsTradingStrategy(BaseStrategy):
    """
    Pairs Trading Strategy

    Trades based on mean reversion between two correlated assets
    Long the undervalued, short the overvalued
    """

    def __init__(
        self,
        asset1_data: pd.DataFrame,
        asset2_data: pd.DataFrame,
        lookback_period: int = 60,
        entry_threshold: float = 2.0,
        exit_threshold: float = 0.5
    ):
        """
        Initialize Pairs Trading Strategy

        Args:
            asset1_data: Price data for first asset
            asset2_data: Price data for second asset
            lookback_period: Period for relationship calculation
            entry_threshold: Z-score threshold for entry
            exit_threshold: Z-score threshold for exit
        """
        super().__init__(
            name="PairsTrading",
            params={
                'lookback_period': lookback_period,
                'entry_threshold': entry_threshold,
                'exit_threshold': exit_threshold
            }
        )

        self.asset1 = asset1_data
        self.asset2 = asset2_data
        self.lookback_period = lookback_period
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold

    def calculate_spread(self) -> pd.Series:
        """Calculate price spread between assets"""
        # Align the data
        aligned_data = pd.concat(
            [self.asset1['close'], self.asset2['close']],
            axis=1,
            join='inner'
        )
        aligned_data.columns = ['Asset1', 'Asset2']

        # Calculate spread (simple price ratio)
        spread = aligned_data['Asset1'] / aligned_data['Asset2']

        return spread

    def calculate_zscore(self, spread: pd.Series) -> pd.Series:
        """Calculate Z-score of the spread"""
        spread_mean = spread.rolling(window=self.lookback_period).mean()
        spread_std = spread.rolling(window=self.lookback_period).std()

        zscore = (spread - spread_mean) / spread_std

        return zscore

    def generate_signals(self, data: pd.DataFrame = None) -> pd.Series:
        """Generate pairs trading signals"""
        spread = self.calculate_spread()
        zscore = self.calculate_zscore(spread)

        # Initialize signals
        signals = pd.Series(0, index=zscore.index)

        # Entry signals
        # Long spread (buy Asset1, sell Asset2) when Z-score is low
        long_entry = zscore < -self.entry_threshold
        signals[long_entry] = 1

        # Short spread (sell Asset1, buy Asset2) when Z-score is high
        short_entry = zscore > self.entry_threshold
        signals[short_entry] = -1

        # Exit signals
        exit_signal = abs(zscore) < self.exit_threshold
        signals[exit_signal] = 0

        return signals

    def get_spread_values(self) -> Dict[str, pd.Series]:
        """Get spread values for analysis"""
        spread = self.calculate_spread()
        zscore = self.calculate_zscore(spread)

        return {
            'spread': spread,
            'zscore': zscore,
            'mean': spread.rolling(window=self.lookback_period).mean(),
            'upper_band': spread.rolling(window=self.lookback_period).mean() +
                         spread.rolling(window=self.lookback_period).std() * 2,
            'lower_band': spread.rolling(window=self.lookback_period).mean() -
                         spread.rolling(window=self.lookback_period).std() * 2
        }


# Portfolio strategy registry
PORTFOLIO_STRATEGIES = {
    'multi_factor': MultiFactorStrategy,
    'risk_parity': RiskParityStrategy,
    'dynamic_allocation': DynamicAllocationStrategy,
    'pairs_trading': PairsTradingStrategy,
}

__all__ = [
    'Asset',
    'MultiFactorStrategy',
    'RiskParityStrategy',
    'DynamicAllocationStrategy',
    'PairsTradingStrategy',
    'PORTFOLIO_STRATEGIES'
]
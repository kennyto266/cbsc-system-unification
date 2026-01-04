"""
HIBOR Strategy Implementation
HIBOR利率策略實現

This module implements a trading strategy based on Hong Kong Interbank Offered Rate (HIBOR),
which reflects monetary policy conditions and market liquidity.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import pandas as pd
import numpy as np

from .base import BaseFundamentalStrategy
from ..enhanced_factory import StrategyMetadata, StrategyType

logger = logging.getLogger(__name__)


class HIBORStrategy(BaseFundamentalStrategy):
    """
    HIBOR (Hong Kong Interbank Offered Rate) Strategy

    Strategy:
    - HIBOR reflects monetary policy stance and banking system liquidity
    - Lower HIBOR = Loose monetary policy = Bullish for equities
    - Higher HIBOR = Tight monetary policy = Bearish for equities
    - Rate changes and momentum provide trading signals
    - Consider rate levels relative to historical ranges
    """

    # Strategy metadata
    STRATEGY_NAME = "hibor"
    DESCRIPTION = "HIBOR-based monetary policy and liquidity strategy"

    # Default parameters
    DEFAULT_PARAMETERS = {
        'lookback_period': 30,  # Days for HIBOR analysis
        'rate_threshold_high': 5.0,  # High rate threshold (percent)
        'rate_threshold_low': 2.0,  # Low rate threshold (percent)
        'use_momentum': True,  # Use rate momentum
        'use_rate_level': True,  # Use absolute rate level
        'momentum_periods': [5, 10, 20],  # Multiple momentum periods
        'ma_periods': [10, 20, 50],  # Moving average periods
        'rate_history_window': 252,  # Days for rate percentile calculation
        'signal_sensitivity': 1.0,  # Signal multiplier
        'min_rate_change': 0.25,  # Minimum rate change for signal (bps)
        'target_symbols': ['HSI', 'HSCEI', 'MCHI']  # HK market proxies
    }

    # Required parameters
    REQUIRED_PARAMETERS = []

    # Optional parameters
    OPTIONAL_PARAMETERS = {
        'lookback_period': {
            'type': int,
            'min': 5,
            'max': 100,
            'default': 30
        },
        'rate_threshold_high': {
            'type': float,
            'min': 0.1,
            'max': 20.0,
            'default': 5.0
        },
        'rate_threshold_low': {
            'type': float,
            'min': 0.01,
            'max': 10.0,
            'default': 2.0
        },
        'signal_sensitivity': {
            'type': float,
            'min': 0.1,
            'max': 5.0,
            'default': 1.0
        },
        'min_rate_change': {
            'type': float,
            'min': 0.05,
            'max': 2.0,
            'default': 0.25
        }
    }

    def __init__(
        self,
        instance_id: UUID,
        config: Dict[str, Any],
        metadata: StrategyMetadata
    ):
        """
        Initialize HIBOR strategy

        Args:
            instance_id: Unique instance identifier
            config: Strategy configuration
            metadata: Strategy metadata
        """
        super().__init__(instance_id, config, metadata)

        self.rate_threshold_high = config.get('rate_threshold_high', 5.0)
        self.rate_threshold_low = config.get('rate_threshold_low', 2.0)
        self.use_momentum = config.get('use_momentum', True)
        self.use_rate_level = config.get('use_rate_level', True)
        self.momentum_periods = config.get('momentum_periods', [5, 10, 20])
        self.ma_periods = config.get('ma_periods', [10, 20, 50])
        self.rate_history_window = config.get('rate_history_window', 252)
        self.signal_sensitivity = config.get('signal_sensitivity', 1.0)
        self.min_rate_change = config.get('min_rate_change', 0.25)
        self.target_symbols = config.get('target_symbols', ['HSI', 'HSCEI', 'MCHI'])

        # Rate history cache
        self._rate_history = None
        self._rate_percentiles = {}

    def fetch_fundamental_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Fetch HIBOR data

        In a real implementation, this would fetch from:
        - HKMA API
        - Bloomberg
        - Financial data providers

        Args:
            symbols: List of symbols (not used for HIBOR)

        Returns:
            Dictionary with HIBOR data
        """
        # For demonstration, generate synthetic HIBOR data
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=self.rate_history_window + 30),
            end=datetime.now(),
            freq='D'
        )

        # Generate realistic HIBOR rates
        np.random.seed(42)
        base_rate = 3.0  # Base HIBOR rate

        hibor_rates = []
        current_rate = base_rate

        for i, date in enumerate(dates):
            # Simulate rate changes based on market conditions
            if i % 30 == 0:  # Monthly changes
                policy_change = np.random.normal(0, 0.5)
                current_rate = max(0.1, current_rate + policy_change)

            # Daily fluctuations
            daily_change = np.random.normal(0, 0.02)
            current_rate = max(0.1, current_rate + daily_change)

            hibor_rates.append(current_rate)

        # Create DataFrame
        hibor_df = pd.DataFrame({
            'hibor_rate': hibor_rates,
            'date': dates
        })
        hibor_df.set_index('date', inplace=True)

        # Add derived metrics
        hibor_df['rate_change'] = hibor_df['hibor_rate'].diff()
        hibor_df['rate_change_pct'] = hibor_df['hibor_rate'].pct_change()

        # Calculate moving averages
        for period in self.ma_periods:
            hibor_df[f'hibor_ma_{period}'] = hibor_df['hibor_rate'].rolling(window=period).mean()

        # Calculate momentum
        for period in self.momentum_periods:
            hibor_df[f'rate_momentum_{period}'] = hibor_df['hibor_rate'].diff(period)

        return {'HIBOR': hibor_df}

    def calculate_rate_regime(self, hibor_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate current HIBOR regime

        Args:
            hibor_data: HIBOR rate data

        Returns:
            Dictionary with regime information
        """
        if hibor_data.empty or len(hibor_data) < self.lookback_period:
            return {'regime': 'unknown', 'strength': 0}

        current_rate = hibor_data['hibor_rate'].iloc[-1]
        recent_rates = hibor_data['hibor_rate'].tail(self.lookback_period)

        # Calculate rate percentiles
        if self._rate_history is not None and len(self._rate_history) > 0:
            rate_percentile = np.percentile(self._rate_history, [25, 50, 75])
        else:
            rate_percentile = np.percentile(recent_rates, [25, 50, 75])

        # Determine regime
        if current_rate < rate_percentile[0]:
            regime = 'low'  # Very accommodative
        elif current_rate < rate_percentile[1]:
            regime = 'moderate_low'  # Accommodative
        elif current_rate < rate_percentile[2]:
            regime = 'moderate_high'  # Restrictive
        else:
            regime = 'high'  # Very restrictive

        # Calculate regime strength based on distance from median
        median_rate = rate_percentile[1]
        strength = abs(current_rate - median_rate) / median_rate

        return {
            'regime': regime,
            'strength': min(strength, 1.0),
            'current_rate': current_rate,
            'percentiles': rate_percentile.tolist()
        }

    def calculate_momentum_signals(self, hibor_data: pd.DataFrame) -> pd.Series:
        """
        Calculate momentum-based signals

        Args:
            hibor_data: HIBOR rate data

        Returns:
            Series of momentum signals
        """
        signals = pd.Series(0, index=hibor_data.index)

        if len(hibor_data) < max(self.momentum_periods):
            return signals

        for i in range(max(self.momentum_periods), len(hibor_data)):
            momentum_signals = []
            weights = []

            for period in self.momentum_periods:
                momentum = hibor_data[f'rate_momentum_{period}'].iloc[i]
                momentum_signals.append(-momentum)  # Negative because falling rates are bullish
                weights.append(1.0 / period)  # Shorter periods get higher weight

            # Weighted average momentum
            weighted_momentum = sum(m * w for m, w in zip(momentum_signals, weights)) / sum(weights)

            # Apply signal sensitivity
            signal = weighted_momentum * self.signal_sensitivity

            # Normalize signal
            signals.iloc[i] = self.calculate_signal_strength(signal, self.min_rate_change / 100)

        return signals

    def calculate_level_signals(self, hibor_data: pd.DataFrame) -> pd.Series:
        """
        Calculate signals based on rate levels

        Args:
            hibor_data: HIBOR rate data

        Returns:
            Series of level-based signals
        """
        signals = pd.Series(0, index=hibor_data.index)

        if len(hibor_data) < max(self.ma_periods):
            return signals

        for i in range(max(self.ma_periods), len(hibor_data)):
            current_rate = hibor_data['hibor_rate'].iloc[i]

            # Compare with multiple moving averages
            ma_signals = []
            for period in self.ma_periods:
                ma = hibor_data[f'hibor_ma_{period}'].iloc[i]
                if current_rate < ma:
                    # Rate below MA (falling trend) = bullish
                    ma_signals.append(0.5)
                elif current_rate > ma:
                    # Rate above MA (rising trend) = bearish
                    ma_signals.append(-0.5)
                else:
                    ma_signals.append(0)

            # Average MA signals
            avg_ma_signal = sum(ma_signals) / len(ma_signals)

            # Apply threshold-based signals
            if current_rate < self.rate_threshold_low:
                # Very low rates = strong bullish
                level_signal = 1.0
            elif current_rate > self.rate_threshold_high:
                # Very high rates = strong bearish
                level_signal = -1.0
            else:
                level_signal = 0

            # Combine signals
            combined_signal = 0.6 * level_signal + 0.4 * avg_ma_signal
            signals.iloc[i] = combined_signal

        return signals

    def calculate_fundamental_signals(
        self,
        fundamental_data: Dict[str, pd.DataFrame],
        market_data: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Dict[str, pd.Series]:
        """
        Calculate signals based on HIBOR data

        Args:
            fundamental_data: Dictionary with HIBOR data
            market_data: Optional market data

        Returns:
            Dictionary of signals
        """
        signals = {}

        if 'HIBOR' not in fundamental_data:
            logger.warning("No HIBOR data available")
            return signals

        hibor_data = fundamental_data['HIBOR']

        # Update rate history
        if self._rate_history is None:
            self._rate_history = hibor_data['hibor_rate'].values
        else:
            # Maintain rolling window of historical rates
            new_rates = hibor_data['hibor_rate'].values
            self._rate_history = np.concatenate([self._rate_history[-(self.rate_history_window - len(new_rates)):], new_rates])

        # Calculate regime
        regime_info = self.calculate_rate_regime(hibor_data)

        # Generate signals
        momentum_signals = pd.Series(0, index=hibor_data.index)
        level_signals = pd.Series(0, index=hibor_data.index)

        if self.use_momentum:
            momentum_signals = self.calculate_momentum_signals(hibor_data)

        if self.use_rate_level:
            level_signals = self.calculate_level_signals(hibor_data)

        # Combine signals
        combined_signals = pd.Series(0, index=hibor_data.index)

        if self.use_momentum and self.use_rate_level:
            # Weight by regime
            if regime_info['regime'] in ['low', 'moderate_low']:
                # In accommodative regime, focus on momentum
                combined_signals = 0.7 * momentum_signals + 0.3 * level_signals
            elif regime_info['regime'] in ['high', 'moderate_high']:
                # In restrictive regime, focus on level
                combined_signals = 0.3 * momentum_signals + 0.7 * level_signals
            else:
                # Balanced approach
                combined_signals = 0.5 * momentum_signals + 0.5 * level_signals
        elif self.use_momentum:
            combined_signals = momentum_signals
        elif self.use_rate_level:
            combined_signals = level_signals

        # Apply regime-based scaling
        if regime_info['strength'] > 0.5:
            # Strong regime, amplify signals
            combined_signals *= (1 + regime_info['strength'])

        # Generate signals for target symbols
        for symbol in self.target_symbols:
            signals[symbol] = combined_signals.copy()

        return signals

    def get_hibor_analysis(self) -> Dict[str, Any]:
        """
        Get detailed HIBOR analysis

        Returns:
            Dictionary with HIBOR analysis
        """
        analysis = {
            'strategy': self.STRATEGY_NAME,
            'parameters': {
                'lookback_period': self.lookback_period,
                'rate_thresholds': {
                    'high': self.rate_threshold_high,
                    'low': self.rate_threshold_low
                },
                'use_momentum': self.use_momentum,
                'use_rate_level': self.use_rate_level
            },
            'data_status': self.get_data_status()
        }

        if self._rate_history is not None and len(self._rate_history) > 0:
            analysis['rate_statistics'] = {
                'current': self._rate_history[-1] if len(self._rate_history) > 0 else None,
                'min': float(np.min(self._rate_history)),
                'max': float(np.max(self._rate_history)),
                'mean': float(np.mean(self._rate_history)),
                'std': float(np.std(self._rate_history)),
                'percentiles': {
                    '25': float(np.percentile(self._rate_history, 25)),
                    '50': float(np.percentile(self._rate_history, 50)),
                    '75': float(np.percentile(self._rate_history, 75))
                }
            }

        return analysis
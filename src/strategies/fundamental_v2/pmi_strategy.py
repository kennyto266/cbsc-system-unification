"""
PMI Strategy Implementation
PMI採購經理人指數策略實現

This module implements a trading strategy based on Purchasing Managers Index (PMI),
which is a leading indicator of economic activity.
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


class PMIStrategy(BaseFundamentalStrategy):
    """
    Purchasing Managers Index (PMI) Strategy

    Strategy:
    - PMI > 50 = Economic expansion (bullish)
    - PMI < 50 = Economic contraction (bearish)
    - PMI trends more important than absolute levels
    - Combine manufacturing and services PMI
    - Regional PMI provides geographic insights
    """

    # Strategy metadata
    STRATEGY_NAME = "pmi"
    DESCRIPTION = "PMI-based economic activity and business cycle strategy"

    # Default parameters
    DEFAULT_PARAMETERS = {
        'expansion_threshold': 55,  # Strong expansion threshold
        'contraction_threshold': 45,  # Strong contraction threshold
        'neutral_range': 5,  # Range around 50 considered neutral
        'lookback_months': 12,  # Months for PMI analysis
        'use_trend': True,  # Use PMI trend analysis
        'trend_periods': [3, 6, 12],  # Trend calculation periods
        'weight_manufacturing': 0.5,  # Weight for manufacturing PMI
        'weight_services': 0.5,  # Weight for services PMI
        'regional_weight': 0.3,  # Weight for regional PMI
        'composite_weight': 0.7,  # Weight for composite PMI
        'min_change_threshold': 1.0,  # Minimum PMI change for signal
        'smoothing_periods': [3, 6],  # Smoothing periods
        'target_regions': ['US', 'EU', 'CN', 'JP', 'IND'],  # Major economies
        'sector_weights': {  # Sector exposure weights
            'industrial': 0.25,
            'materials': 0.15,
            'consumer': 0.20,
            'technology': 0.15,
            'financials': 0.10,
            'energy': 0.10,
            'healthcare': 0.05
        }
    }

    # Required parameters
    REQUIRED_PARAMETERS = []

    # Optional parameters
    OPTIONAL_PARAMETERS = {
        'expansion_threshold': {
            'type': int,
            'min': 50,
            'max': 70,
            'default': 55
        },
        'contraction_threshold': {
            'type': int,
            'min': 30,
            'max': 50,
            'default': 45
        },
        'lookback_months': {
            'type': int,
            'min': 3,
            'max': 36,
            'default': 12
        },
        'weight_manufacturing': {
            'type': float,
            'min': 0.0,
            'max': 1.0,
            'default': 0.5
        },
        'weight_services': {
            'type': float,
            'min': 0.0,
            'max': 1.0,
            'default': 0.5
        }
    }

    def __init__(
        self,
        instance_id: UUID,
        config: Dict[str, Any],
        metadata: StrategyMetadata
    ):
        """
        Initialize PMI strategy

        Args:
            instance_id: Unique instance identifier
            config: Strategy configuration
            metadata: Strategy metadata
        """
        super().__init__(instance_id, config, metadata)

        self.expansion_threshold = config.get('expansion_threshold', 55)
        self.contraction_threshold = config.get('contraction_threshold', 45)
        self.neutral_range = config.get('neutral_range', 5)
        self.lookback_months = config.get('lookback_months', 12)
        self.use_trend = config.get('use_trend', True)
        self.trend_periods = config.get('trend_periods', [3, 6, 12])
        self.weight_manufacturing = config.get('weight_manufacturing', 0.5)
        self.weight_services = config.get('weight_services', 0.5)
        self.regional_weight = config.get('regional_weight', 0.3)
        self.composite_weight = config.get('composite_weight', 0.7)
        self.min_change_threshold = config.get('min_change_threshold', 1.0)
        self.smoothing_periods = config.get('smoothing_periods', [3, 6])
        self.target_regions = config.get('target_regions', ['US', 'EU', 'CN', 'JP', 'IND'])
        self.sector_weights = config.get('sector_weights', {})

        # Ensure weights sum to 1
        total_mfg_svc = self.weight_manufacturing + self.weight_services
        if total_mfg_svc > 0:
            self.weight_manufacturing /= total_mfg_svc
            self.weight_services /= total_mfg_svc

        total_reg_comp = self.regional_weight + self.composite_weight
        if total_reg_comp > 0:
            self.regional_weight /= total_reg_comp
            self.composite_weight /= total_reg_comp

        # PMI history cache
        self._pmi_history = {}

    def fetch_fundamental_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Fetch PMI data

        In a real implementation, this would fetch from:
        - ISM (Institute for Supply Management) for US PMI
        - Markit for Global PMI
        - National statistics offices
        - Bloomberg/Reuters

        Args:
            symbols: List of target symbols

        Returns:
            Dictionary with PMI data
        """
        # Generate synthetic PMI data for demonstration
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=self.lookback_months * 30 + 365),
            end=datetime.now(),
            freq='M'  # Monthly frequency
        )

        pmi_data = {}

        # Global PMI
        global_pmi = []
        base_pmi = 50.0

        np.random.seed(42)
        for i, date in enumerate(dates):
            # Generate realistic PMI with business cycle
            cycle = 3.0 * np.sin(2 * np.pi * i / 12)  # Annual cycle
            trend = 0.02 * i / len(dates)  # Slight uptrend
            noise = np.random.normal(0, 2)

            current_pmi = base_pmi + cycle + trend + noise
            current_pmi = max(30, min(70, current_pmi))  # Clamp to reasonable range

            global_pmi.append(current_pmi)

        # Create global PMI DataFrame
        global_df = pd.DataFrame({
            'pmi_global': global_pmi,
            'date': dates
        })
        global_df.set_index('date', inplace=True)

        # Calculate derived metrics
        global_df['pmi_global_ma_3'] = global_df['pmi_global'].rolling(window=3).mean()
        global_df['pmi_global_ma_6'] = global_df['pmi_global'].rolling(window=6).mean()
        global_df['pmi_global_change'] = global_df['pmi_global'].diff()
        global_df['pmi_global_trend_3'] = global_df['pmi_global'].diff(3)
        global_df['pmi_global_trend_6'] = global_df['pmi_global'].diff(6)

        pmi_data['PMI_GLOBAL'] = global_df

        # Regional PMIs
        for region in self.target_regions:
            np.random.seed(hash(region) % 2**32)
            regional_pmi = []

            for i, date in enumerate(dates):
                # Regional variation around global PMI
                regional_adjustment = np.random.normal(0, 3)
                current_pmi = global_pmi[i] + regional_adjustment
                current_pmi = max(30, min(70, current_pmi))

                regional_pmi.append(current_pmi)

            regional_df = pd.DataFrame({
                f'pmi_{region.lower()}': regional_pmi,
                'date': dates
            })
            regional_df.set_index('date', inplace=True)

            pmi_data[f'PMI_{region}'] = regional_df

        # Manufacturing and Services PMI
        manufacturing_pmi = []
        services_pmi = []

        for i, date in enumerate(dates):
            # Manufacturing tends to be more volatile
            man_volatility = np.random.normal(0, 2.5)
            svc_volatility = np.random.normal(0, 1.5)

            man_pmi = global_pmi[i] + man_volatility
            svc_pmi = global_pmi[i] + svc_volatility

            manufacturing_pmi.append(max(30, min(70, man_pmi)))
            services_pmi.append(max(30, min(70, svc_pmi)))

        component_df = pd.DataFrame({
            'pmi_manufacturing': manufacturing_pmi,
            'pmi_services': services_pmi,
            'date': dates
        })
        component_df.set_index('date', inplace=True)

        pmi_data['PMI_COMPONENTS'] = component_df

        return pmi_data

    def calculate_pmi_regime(
        self,
        pmi_data: pd.DataFrame,
        pmi_type: str = 'global'
    ) -> Dict[str, Any]:
        """
        Calculate current PMI regime

        Args:
            pmi_data: PMI data DataFrame
            pmi_type: Type of PMI ('global', 'manufacturing', 'services', or region)

        Returns:
            Dictionary with regime information
        """
        if pmi_data.empty:
            return {'regime': 'unknown', 'strength': 0}

        # Get PMI column
        pmi_col = f'pmi_{pmi_type}'
        if pmi_col not in pmi_data.columns:
            # Try alternative column names
            for col in pmi_data.columns:
                if pmi_type.lower() in col.lower():
                    pmi_col = col
                    break

        if pmi_col not in pmi_data.columns:
            return {'regime': 'unknown', 'strength': 0}

        current_pmi = pmi_data[pmi_col].iloc[-1]

        # Determine regime
        if current_pmi > self.expansion_threshold:
            regime = 'strong_expansion'
        elif current_pmi > 50 + self.neutral_range/2:
            regime = 'moderate_expansion'
        elif current_pmi > 50 - self.neutral_range/2:
            regime = 'neutral'
        elif current_pmi > self.contraction_threshold:
            regime = 'moderate_contraction'
        else:
            regime = 'strong_contraction'

        # Calculate distance from 50 (breakeven point)
        distance_from_50 = abs(current_pmi - 50)
        strength = min(distance_from_50 / 20, 1.0)  # Normalize to 0-1

        return {
            'regime': regime,
            'strength': strength,
            'current_pmi': current_pmi,
            'distance_from_50': distance_from_50
        }

    def calculate_trend_signals(
        self,
        pmi_data: pd.DataFrame,
        pmi_col: str
    ) -> pd.Series:
        """
        Calculate trend-based signals

        Args:
            pmi_data: PMI data DataFrame
            pmi_col: PMI column name

        Returns:
            Series of trend signals
        """
        signals = pd.Series(0, index=pmi_data.index)

        if len(pmi_data) < max(self.trend_periods):
            return signals

        for i in range(max(self.trend_periods), len(pmi_data)):
            trend_signals = []
            weights = []

            for period in self.trend_periods:
                if f'{pmi_col}_trend_{period}' in pmi_data.columns:
                    trend = pmi_data[f'{pmi_col}_trend_{period}'].iloc[i]
                    trend_signals.append(trend)
                    weights.append(1.0 / period)  # Shorter periods get higher weight

            if trend_signals:
                # Weighted average trend
                weighted_trend = sum(t * w for t, w in zip(trend_signals, weights)) / sum(weights)

                # Convert to signal
                if weighted_trend > self.min_change_threshold:
                    signal = min(weighted_trend / 10, 1.0)  # Normalize to -1 to 1
                elif weighted_trend < -self.min_change_threshold:
                    signal = max(weighted_trend / 10, -1.0)
                else:
                    signal = 0

                signals.iloc[i] = signal

        return signals

    def calculate_level_signals(
        self,
        pmi_data: pd.DataFrame,
        pmi_col: str
    ) -> pd.Series:
        """
        Calculate level-based signals

        Args:
            pmi_data: PMI data DataFrame
            pmi_col: PMI column name

        Returns:
            Series of level-based signals
        """
        signals = pd.Series(0, index=pmi_data.index)

        for i in range(len(pmi_data)):
            current_pmi = pmi_data[pmi_col].iloc[i]

            # Calculate signal based on PMI level
            if current_pmi > self.expansion_threshold:
                signal = min((current_pmi - 50) / 20, 1.0)
            elif current_pmi < self.contraction_threshold:
                signal = max((current_pmi - 50) / 20, -1.0)
            else:
                signal = 0

            # Apply smoothing if available
            for period in self.smoothing_periods:
                if f'{pmi_col}_ma_{period}' in pmi_data.columns:
                    ma = pmi_data[f'{pmi_col}_ma_{period}'].iloc[i]
                    if current_pmi > ma:
                        signal = signal * 0.7 + 0.3 * min((current_pmi - ma) / 10, 1.0)
                    else:
                        signal = signal * 0.7 - 0.3 * min((ma - current_pmi) / 10, 1.0)

            signals.iloc[i] = signal

        return signals

    def calculate_fundamental_signals(
        self,
        fundamental_data: Dict[str, pd.DataFrame],
        market_data: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Dict[str, pd.Series]:
        """
        Calculate signals based on PMI data

        Args:
            fundamental_data: Dictionary with PMI data
            market_data: Optional market data

        Returns:
            Dictionary of signals
        """
        signals = {}

        if not fundamental_data:
            logger.warning("No PMI data available")
            return signals

        # Get component PMI data
        component_data = fundamental_data.get('PMI_COMPONENTS')
        if component_data is None:
            logger.warning("No PMI component data found")
            return signals

        # Calculate composite PMI signals
        if 'pmi_manufacturing' in component_data.columns and 'pmi_services' in component_data.columns:
            # Manufacturing signals
            if self.use_trend:
                man_trend = self.calculate_trend_signals(component_data, 'pmi_manufacturing')
                man_level = self.calculate_level_signals(component_data, 'pmi_manufacturing')
                man_signals = 0.6 * man_trend + 0.4 * man_level
            else:
                man_signals = self.calculate_level_signals(component_data, 'pmi_manufacturing')

            # Services signals
            if self.use_trend:
                svc_trend = self.calculate_trend_signals(component_data, 'pmi_services')
                svc_level = self.calculate_level_signals(component_data, 'pmi_services')
                svc_signals = 0.6 * svc_trend + 0.4 * svc_level
            else:
                svc_signals = self.calculate_level_signals(component_data, 'pmi_services')

            # Combine manufacturing and services
            composite_signals = (
                self.weight_manufacturing * man_signals +
                self.weight_services * svc_signals
            )

            signals['GLOBAL_EQUITY'] = composite_signals

            # Generate sector-specific signals based on PMI
            for sector, weight in self.sector_weights.items():
                if weight > 0:
                    # Sector-specific adjustments
                    if sector == 'industrial':
                        # Industrial sensitive to manufacturing PMI
                        sector_signals = man_signals * 1.2
                    elif sector in ['consumer', 'financials']:
                        # Consumer and services sensitive to services PMI
                        sector_signals = svc_signals * 1.1
                    else:
                        # Other sectors use composite
                        sector_signals = composite_signals

                    signals[f'{sector.upper()}_ETF'] = sector_signals * min(weight * 4, 1.0)  # Scale weights

        # Get regional PMI signals
        for region in self.target_regions:
            region_key = f'PMI_{region}'
            if region_key in fundamental_data:
                region_data = fundamental_data[region_key]
                region_pmi_col = f'pmi_{region.lower()}'

                if self.use_trend and f'{region_pmi_col}_trend_3' in region_data.columns:
                    region_trend = self.calculate_trend_signals(region_data, region_pmi_col)
                    region_level = self.calculate_level_signals(region_data, region_pmi_col)
                    region_signals = 0.7 * region_trend + 0.3 * region_level
                else:
                    region_signals = self.calculate_level_signals(region_data, region_pmi_col)

                signals[f'{region}_EQUITY'] = region_signals * self.regional_weight

        return signals

    def get_pmi_analysis(self) -> Dict[str, Any]:
        """
        Get detailed PMI analysis

        Returns:
            Dictionary with PMI analysis
        """
        analysis = {
            'strategy': self.STRATEGY_NAME,
            'parameters': {
                'expansion_threshold': self.expansion_threshold,
                'contraction_threshold': self.contraction_threshold,
                'neutral_range': self.neutral_range,
                'weights': {
                    'manufacturing': self.weight_manufacturing,
                    'services': self.weight_services,
                    'regional': self.regional_weight,
                    'composite': self.composite_weight
                }
            },
            'data_status': self.get_data_status()
        }

        return analysis

    def get_economic_indicators_summary(self, pmi_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Get summary of economic indicators from PMI

        Args:
            pmi_data: Dictionary of PMI data

        Returns:
            Dictionary with indicator summary
        """
        summary = {}

        # Global PMI
        if 'PMI_GLOBAL' in pmi_data:
            global_data = pmi_data['PMI_GLOBAL']
            if not global_data.empty:
                global_regime = self.calculate_pmi_regime(global_data, 'global')
                summary['global_pmi'] = {
                    'current': global_regime.get('current_pmi'),
                    'regime': global_regime.get('regime'),
                    'strength': global_regime.get('strength')
                }

        # Component PMIs
        if 'PMI_COMPONENTS' in pmi_data:
            component_data = pmi_data['PMI_COMPONENTS']
            if not component_data.empty:
                summary['components'] = {}

                for pmi_type in ['manufacturing', 'services']:
                    col = f'pmi_{pmi_type}'
                    if col in component_data.columns:
                        current = component_data[col].iloc[-1]
                        summary['components'][pmi_type] = {
                            'current': current,
                            'trend': component_data[col].iloc[-1] - component_data[col].iloc[-2] if len(component_data) > 1 else 0,
                            'ma_3': component_data[f'{col}_ma_3'].iloc[-1] if f'{col}_ma_3' in component_data.columns else current,
                            'ma_6': component_data[f'{col}_ma_6'].iloc[-1] if f'{col}_ma_6' in component_data.columns else current
                        }

        return summary
"""
GDP Growth Strategy Implementation
GDP增長策略實現

This module implements a trading strategy based on Gross Domestic Product (GDP) growth data,
which reflects overall economic activity and growth trends.
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


class GDPGrowthStrategy(BaseFundamentalStrategy):
    """
    GDP Growth Strategy

    Strategy:
    - GDP growth reflects overall economic health
    - Strong GDP growth = Economic expansion = Bullish for equities
    - Weak/negative GDP growth = Economic contraction = Bearish
    - GDP acceleration/deceleration provides momentum signals
    - Combine quarterly and annual GDP data with leading indicators
    """

    # Strategy metadata
    STRATEGY_NAME = "gdp_growth"
    DESCRIPTION = "GDP growth-based economic cycle strategy"

    # Default parameters
    DEFAULT_PARAMETERS = {
        'growth_threshold_high': 0.05,  # 5% annual growth threshold for bullish
        'growth_threshold_low': 0.01,  # 1% annual growth threshold for bearish
        'lookback_quarters': 8,  # Number of quarters for analysis
        'use_acceleration': True,  # Consider GDP acceleration
        'use_year_over_year': True,  # Use YoY comparisons
        'seasonal_adjust': True,  # Use seasonally adjusted data
        'weight_quarterly': 0.6,  # Weight for quarterly GDP
        'weight_annual': 0.4,  # Weight for annual GDP
        'min_change_threshold': 0.001,  # Minimum change for signal
        'trend_periods': [4, 8, 12],  # Trend calculation periods
        'target_regions': ['US', 'EU', 'CN', 'JP'],  # Target economies
        'sector_mapping': {  # Map sectors to GDP components
            'technology': ['business_investment', 'innovation'],
            'financials': ['financial_services', 'credit_growth'],
            'industrial': ['manufacturing', 'industrial_production'],
            'consumer': ['consumer_spending', 'retail_sales'],
            'energy': ['energy_consumption', 'commodity_prices'],
            'healthcare': ['healthcare_spending', 'demographics'],
            'materials': ['construction', 'raw_materials']
        }
    }

    # Required parameters
    REQUIRED_PARAMETERS = []

    # Optional parameters
    OPTIONAL_PARAMETERS = {
        'growth_threshold_high': {
            'type': float,
            'min': 0.0,
            'max': 0.2,
            'default': 0.05
        },
        'growth_threshold_low': {
            'type': float,
            'min': -0.1,
            'max': 0.1,
            'default': 0.01
        },
        'lookback_quarters': {
            'type': int,
            'min': 1,
            'max': 20,
            'default': 8
        },
        'weight_quarterly': {
            'type': float,
            'min': 0.0,
            'max': 1.0,
            'default': 0.6
        },
        'weight_annual': {
            'type': float,
            'min': 0.0,
            'max': 1.0,
            'default': 0.4
        }
    }

    def __init__(
        self,
        instance_id: UUID,
        config: Dict[str, Any],
        metadata: StrategyMetadata
    ):
        """
        Initialize GDP growth strategy

        Args:
            instance_id: Unique instance identifier
            config: Strategy configuration
            metadata: Strategy metadata
        """
        super().__init__(instance_id, config, metadata)

        self.growth_threshold_high = config.get('growth_threshold_high', 0.05)
        self.growth_threshold_low = config.get('growth_threshold_low', 0.01)
        self.lookback_quarters = config.get('lookback_quarters', 8)
        self.use_acceleration = config.get('use_acceleration', True)
        self.use_year_over_year = config.get('use_year_over_year', True)
        self.seasonal_adjust = config.get('seasonal_adjust', True)
        self.weight_quarterly = config.get('weight_quarterly', 0.6)
        self.weight_annual = config.get('weight_annual', 0.4)
        self.min_change_threshold = config.get('min_change_threshold', 0.001)
        self.trend_periods = config.get('trend_periods', [4, 8, 12])
        self.target_regions = config.get('target_regions', ['US', 'EU', 'CN', 'JP'])
        self.sector_mapping = config.get('sector_mapping', {})

        # Ensure weights sum to 1
        total_weight = self.weight_quarterly + self.weight_annual
        if total_weight > 0:
            self.weight_quarterly /= total_weight
            self.weight_annual /= total_weight

        # GDP components cache
        self._gdp_components = {}

    def fetch_fundamental_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Fetch GDP growth data

        In a real implementation, this would fetch from:
        - World Bank API
        - IMF data
        - National statistics offices
        - Bloomberg/Reuters

        Args:
            symbols: List of target symbols

        Returns:
            Dictionary with GDP data
        """
        # Generate synthetic GDP data for demonstration
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=self.lookback_quarters * 90 + 365),
            end=datetime.now(),
            freq='Q'  # Quarterly frequency
        )

        gdp_data = {}

        for region in self.target_regions:
            # Generate realistic GDP growth rates
            np.random.seed(hash(region) % 2**32)
            base_growth = 0.025 if region == 'US' else 0.02

            # Generate GDP growth data
            gdp_growth_rates = []
            current_growth = base_growth

            for i, date in enumerate(dates):
                # Add cyclical component
                cyclical = 0.01 * np.sin(2 * np.pi * i / 8)  # 2-year cycle
                # Add trend component
                trend = 0.0001 * i
                # Add random shock
                shock = np.random.normal(0, 0.01)

                current_growth = base_growth + cyclical + trend + shock
                current_growth = max(-0.1, min(0.1, current_growth))  # Clamp to reasonable range

                gdp_growth_rates.append(current_growth)

            # Create DataFrame
            gdp_df = pd.DataFrame({
                f'gdp_growth_{region}': gdp_growth_rates,
                'date': dates
            })
            gdp_df.set_index('date', inplace=True)

            # Calculate derived metrics
            gdp_df[f'gdp_trend_{region}'] = gdp_df[f'gdp_growth_{region}'].rolling(window=4).mean()
            gdp_df[f'gdp_acceleration_{region}'] = gdp_df[f'gdp_growth_{region}'].diff()
            gdp_df[f'gdp_momentum_{region}'] = gdp_df[f'gdp_growth_{region}'].rolling(window=2).mean()

            # Calculate YoY for quarterly data
            gdp_df[f'gdp_yoy_{region}'] = gdp_df[f'gdp_growth_{region}'].rolling(window=4).sum()

            gdp_data[f'GDP_{region}'] = gdp_df

        # Create composite GDP indicator
        composite_df = pd.DataFrame(index=dates)
        composite_df['composite_growth'] = 0
        composite_df['composite_trend'] = 0
        composite_df['composite_acceleration'] = 0

        for region in self.target_regions:
            if f'GDP_{region}' in gdp_data:
                region_data = gdp_data[f'GDP_{region}']
                weight = 1.0 / len(self.target_regions)  # Equal weights

                composite_df['composite_growth'] += region_data[f'gdp_growth_{region}'] * weight
                composite_df['composite_trend'] += region_data[f'gdp_trend_{region}'] * weight
                composite_df['composite_acceleration'] += region_data[f'gdp_acceleration_{region}'] * weight

        gdp_data['GDP_GLOBAL'] = composite_df

        return gdp_data

    def calculate_growth_phase(
        self,
        gdp_data: pd.DataFrame,
        region: str = 'GLOBAL'
    ) -> Dict[str, Any]:
        """
        Calculate current GDP growth phase

        Args:
            gdp_data: GDP data DataFrame
            region: Region to analyze

        Returns:
            Dictionary with phase information
        """
        if gdp_data.empty or len(gdp_data) < self.lookback_quarters:
            return {'phase': 'unknown', 'strength': 0}

        # Get growth column
        if region == 'GLOBAL':
            growth_col = 'composite_growth'
        else:
            growth_col = f'gdp_growth_{region}'

        if growth_col not in gdp_data.columns:
            return {'phase': 'unknown', 'strength': 0}

        current_growth = gdp_data[growth_col].iloc[-1]
        recent_growth = gdp_data[growth_col].tail(self.lookback_quarters)
        trend = gdp_data.get(f'gdp_trend_{region}' if region != 'GLOBAL' else 'composite_trend',
                               pd.Series(0, index=gdp_data.index)).iloc[-1]
        acceleration = gdp_data.get(f'gdp_acceleration_{region}' if region != 'GLOBAL' else 'composite_acceleration',
                                    pd.Series(0, index=gdp_data.index)).iloc[-1]

        # Determine phase
        if current_growth > self.growth_threshold_high:
            if acceleration > 0:
                phase = 'expansion_accelerating'
            else:
                phase = 'expansion_decelerating'
        elif current_growth > self.growth_threshold_low:
            if acceleration > 0:
                phase = 'recovery_accelerating'
            else:
                phase = 'recovery_decelerating'
        elif current_growth > 0:
            phase = 'slowdown_positive'
        else:
            phase = 'contraction'

        # Calculate phase strength
        strength = min(abs(current_growth) / self.growth_threshold_high, 1.0)

        return {
            'phase': phase,
            'strength': strength,
            'current_growth': current_growth,
            'trend': trend,
            'acceleration': acceleration,
            'recent_average': float(recent_growth.mean())
        }

    def calculate_sector_signals(
        self,
        gdp_data: pd.DataFrame,
        sector: str
    ) -> pd.Series:
        """
        Calculate sector-specific signals based on GDP components

        Args:
            gdp_data: GDP data
            sector: Sector name

        Returns:
            Series of sector signals
        """
        signals = pd.Series(0, index=gdp_data.index)

        if sector not in self.sector_mapping:
            return signals

        components = self.sector_mapping[sector]
        component_signals = []

        for component in components:
            # In a real implementation, would map GDP components to actual data
            # For demonstration, use GDP growth as proxy
            if 'composite_growth' in gdp_data.columns:
                # Apply sector-specific weighting
                sector_weight = self._get_sector_weight(sector)
                component_signal = gdp_data['composite_growth'] * sector_weight
                component_signals.append(component_signal)

        if component_signals:
            # Average all component signals
            signals = pd.Series(
                np.mean(component_signals, axis=0),
                index=gdp_data.index
            )

        return signals

    def _get_sector_weight(self, sector: str) -> float:
        """
        Get sector weight in GDP

        Args:
            sector: Sector name

        Returns:
            Sector weight
        """
        # Simplified sector weights
        sector_weights = {
            'technology': 0.25,
            'financials': 0.20,
            'industrial': 0.15,
            'consumer': 0.20,
            'energy': 0.08,
            'healthcare': 0.07,
            'materials': 0.05
        }
        return sector_weights.get(sector, 0.1)

    def calculate_fundamental_signals(
        self,
        fundamental_data: Dict[str, pd.DataFrame],
        market_data: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Dict[str, pd.Series]:
        """
        Calculate signals based on GDP growth data

        Args:
            fundamental_data: Dictionary with GDP data
            market_data: Optional market data

        Returns:
            Dictionary of signals
        """
        signals = {}

        if not fundamental_data:
            logger.warning("No GDP data available")
            return signals

        # Get global GDP data
        global_gdp = fundamental_data.get('GDP_GLOBAL')
        if global_gdp is None:
            logger.warning("No global GDP data found")
            return signals

        # Calculate growth phase
        phase_info = self.calculate_growth_phase(global_gdp)

        # Generate base signals from GDP growth
        base_signals = pd.Series(0, index=global_gdp.index)

        if len(global_gdp) >= self.lookback_quarters:
            current_growth = global_gdp['composite_growth'].iloc[-1]
            trend = global_gdp['composite_trend'].iloc[-1]

            # Generate signals based on growth levels
            if current_growth > self.growth_threshold_high:
                if self.use_acceleration:
                    accel = global_gdp['composite_acceleration'].iloc[-1]
                    strength = 1.5 if accel > 0 else 1.0
                else:
                    strength = 1.0
                base_signals.iloc[-1] = strength

            elif current_growth > self.growth_threshold_low:
                strength = 0.5
                base_signals.iloc[-1] = strength

            elif current_growth < -0.01:
                if self.use_acceleration:
                    accel = global_gdp['composite_acceleration'].iloc[-1]
                    strength = -1.5 if accel < 0 else -1.0
                else:
                    strength = -1.0
                base_signals.iloc[-1] = strength

        # Apply trend smoothing
        if len(base_signals) > 4:
            smoothed_signals = base_signals.rolling(window=4).mean()
            base_signals = smoothed_signals.fillna(0)

        # Generate signals for different regions
        for region in self.target_regions:
            region_key = f'GDP_{region}'
            if region_key in fundamental_data:
                region_data = fundamental_data[region_key]
                region_signals = base_signals.copy()

                # Adjust for region-specific factors
                if f'gdp_growth_{region}' in region_data.columns:
                    region_growth = region_data[f'gdp_growth_{region}'].iloc[-1]
                    adjustment = region_growth / global_gdp['composite_growth'].iloc[-1] if global_gdp['composite_growth'].iloc[-1] != 0 else 1
                    region_signals *= adjustment

                signals[f'{region}_EQUITY'] = region_signals

        # Generate sector-specific signals
        for sector in self.sector_mapping.keys():
            sector_signals = self.calculate_sector_signals(global_gdp, sector)
            signals[f'{sector.upper()}_ETF'] = sector_signals

        # Generate global equity signal
        signals['GLOBAL_EQUITY'] = base_signals

        return signals

    def get_gdp_analysis(self) -> Dict[str, Any]:
        """
        Get detailed GDP analysis

        Returns:
            Dictionary with GDP analysis
        """
        analysis = {
            'strategy': self.STRATEGY_NAME,
            'parameters': {
                'growth_thresholds': {
                    'high': self.growth_threshold_high,
                    'low': self.growth_threshold_low
                },
                'lookback_quarters': self.lookback_quarters,
                'use_acceleration': self.use_acceleration,
                'target_regions': self.target_regions
            },
            'data_status': self.get_data_status(),
            'sector_mapping': self.sector_mapping
        }

        return analysis

    def get_economic_cycle_indicators(self, gdp_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Get economic cycle indicators based on GDP

        Args:
            gdp_data: GDP data

        Returns:
            Dictionary with cycle indicators
        """
        indicators = {}

        if gdp_data.empty:
            return indicators

        # Leading indicator: GDP acceleration
        if 'composite_acceleration' in gdp_data.columns:
            acceleration = gdp_data['composite_acceleration'].iloc[-1]
            indicators['gdp_acceleration'] = float(acceleration)

            # Determine cycle phase
            if acceleration > 0.01:
                indicators['cycle_phase'] = 'expansion'
            elif acceleration < -0.01:
                indicators['cycle_phase'] = 'contraction'
            else:
                indicators['cycle_phase'] = 'stable'

        # Current growth rate
        if 'composite_growth' in gdp_data.columns:
            current_growth = gdp_data['composite_growth'].iloc[-1]
            indicators['current_growth'] = float(current_growth)

            # Growth momentum
            if len(gdp_data) > 1:
                recent_growth = gdp_data['composite_growth'].tail(4)
                momentum = recent_growth.iloc[-1] - recent_growth.iloc[0]
                indicators['growth_momentum'] = float(momentum)

        # Trend strength
        if 'composite_trend' in gdp_data.columns:
            trend = gdp_data['composite_trend'].iloc[-1]
            indicators['trend_strength'] = float(trend)

        return indicators
"""
Fundamental/Non-Price Data Trading Strategies

This module contains strategies based on economic indicators and fundamental data.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum

from src.strategies.base import BaseStrategy, BaseSignal


class HIBORStrategy(BaseStrategy):
    """
    HIBOR (Hong Kong Interbank Offered Rate) Strategy

    Strategy:
    - Use HIBOR rates as market sentiment indicator
    - Lower HIBOR = Looser monetary policy = Bullish for equities
    - Higher HIBOR = Tighter monetary policy = Bearish for equities
    - Generate signals based on HIBOR changes and levels
    """

    def __init__(
        self,
        lookback_period: int = 30,
        rate_threshold_high: float = 5.0,
        rate_threshold_low: float = 2.0,
        use_momentum: bool = True
    ):
        """
        Initialize HIBOR Strategy

        Args:
            lookback_period: Period for HIBOR analysis
            rate_threshold_high: High rate threshold for bearish signals
            rate_threshold_low: Low rate threshold for bullish signals
            use_momentum: Use HIBOR momentum in signals
        """
        super().__init__(
            name=f"HIBOR_{lookback_period}",
            params={
                'lookback_period': lookback_period,
                'rate_threshold_high': rate_threshold_high,
                'rate_threshold_low': rate_threshold_low,
                'use_momentum': use_momentum
            }
        )
        self.lookback_period = lookback_period
        self.rate_threshold_high = rate_threshold_high
        self.rate_threshold_low = rate_threshold_low
        self.use_momentum = use_momentum

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate signals based on HIBOR data
        Expected data columns: ['hibor_rate', 'market_close'] (optional)
        """
        signals = pd.Series(0, index=data.index)

        if 'hibor_rate' not in data.columns:
            return signals

        hibor = data['hibor_rate']

        # Calculate HIBOR moving average
        hibor_ma = hibor.rolling(window=self.lookback_period).mean()

        # Calculate HIBOR momentum
        hibor_momentum = hibor.diff(self.lookback_period)

        for i in range(self.lookback_period, len(data)):
            current_rate = hibor.iloc[i]
            avg_rate = hibor_ma.iloc[i]

            # Bullish signals
            if current_rate < self.rate_threshold_low:
                # Very low HIBOR - strong bullish
                signals.iloc[i] = Signal.BUY.value
            elif current_rate < avg_rate and self.use_momentum:
                # Falling HIBOR - bullish
                signals.iloc[i] = Signal.BUY.value

            # Bearish signals
            elif current_rate > self.rate_threshold_high:
                # Very high HIBOR - strong bearish
                signals.iloc[i] = Signal.SELL.value
            elif current_rate > avg_rate and self.use_momentum:
                # Rising HIBOR - bearish
                signals.iloc[i] = Signal.SELL.value

        return signals


class GDPGrowthStrategy(BaseStrategy):
    """
    GDP Growth Strategy

    Strategy:
    - Use GDP growth data to identify economic cycles
    - Strong GDP growth = Bullish for equities
    - Weak/negative GDP growth = Bearish for equities
    - Combine with quarterly and annual GDP data
    """

    def __init__(
        self,
        growth_threshold_high: float = 0.05,
        growth_threshold_low: float = 0.01,
        lookback_quarters: int = 4,
        use_acceleration: bool = True
    ):
        """
        Initialize GDP Growth Strategy

        Args:
            growth_threshold_high: High growth threshold for bullish signals
            growth_threshold_low: Low growth threshold for bearish signals
            lookback_quarters: Number of quarters to analyze
            use_acceleration: Consider GDP acceleration/deceleration
        """
        super().__init__(
            name=f"GDP_{lookback_quarters}Q",
            params={
                'growth_threshold_high': growth_threshold_high,
                'growth_threshold_low': growth_threshold_low,
                'lookback_quarters': lookback_quarters,
                'use_acceleration': use_acceleration
            }
        )
        self.growth_threshold_high = growth_threshold_high
        self.growth_threshold_low = growth_threshold_low
        self.lookback_quarters = lookback_quarters
        self.use_acceleration = use_acceleration

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate signals based on GDP data
        Expected data columns: ['gdp_growth', 'quarter'] (optional)
        """
        signals = pd.Series(0, index=data.index)

        if 'gdp_growth' not in data.columns:
            return signals

        gdp_growth = data['gdp_growth']

        # Calculate GDP growth moving average
        gdp_ma = gdp_growth.rolling(window=self.lookback_quarters).mean()

        # Calculate GDP acceleration
        if self.use_acceleration:
            gdp_accel = gdp_growth.diff()
        else:
            gdp_accel = pd.Series(0, index=data.index)

        for i in range(self.lookback_quarters, len(data)):
            current_growth = gdp_growth.iloc[i]
            avg_growth = gdp_ma.iloc[i]
            current_accel = gdp_accel.iloc[i]

            # Strong bullish signals
            if current_growth > self.growth_threshold_high:
                if self.use_acceleration and current_accel > 0:
                    signals.iloc[i] = Signal.BUY.value * 2  # Stronger signal
                else:
                    signals.iloc[i] = Signal.BUY.value

            # Moderate bullish
            elif current_growth > self.growth_threshold_low:
                signals.iloc[i] = Signal.BUY.value

            # Strong bearish signals
            elif current_growth < -0.01:
                if self.use_acceleration and current_accel < 0:
                    signals.iloc[i] = Signal.SELL.value * 2  # Stronger signal
                else:
                    signals.iloc[i] = Signal.SELL.value

        return signals


class VisitorArrivalStrategy(BaseStrategy):
    """
    Hong Kong Visitor Arrival Strategy

    Strategy:
    - Visitor arrivals correlate with retail and hospitality sectors
    - Increasing arrivals = Economic optimism = Bullish
    - Decreasing arrivals = Economic slowdown = Bearish
    - Use monthly visitor data for tourism-related stocks
    """

    def __init__(
        self,
        lookback_months: int = 12,
        growth_threshold: float = 0.05,
        seasonal_adjust: bool = True
    ):
        """
        Initialize Visitor Arrival Strategy

        Args:
            lookback_months: Number of months for analysis
            growth_threshold: Growth rate threshold for signals
            seasonal_adjust: Apply seasonal adjustments
        """
        super().__init__(
            name=f"VisitorArrival_{lookback_months}M",
            params={
                'lookback_months': lookback_months,
                'growth_threshold': growth_threshold,
                'seasonal_adjust': seasonal_adjust
            }
        )
        self.lookback_months = lookback_months
        self.growth_threshold = growth_threshold
        self.seasonal_adjust = seasonal_adjust

    def seasonal_adjust_visitors(self, visitors: pd.Series) -> pd.Series:
        """Apply seasonal adjustment to visitor data"""
        if not self.seasonal_adjust:
            return visitors

        # Calculate seasonal patterns
        monthly_pattern = visitors.groupby(visitors.index.month).mean()
        overall_mean = visitors.mean()

        # Calculate seasonal factors
        seasonal_factors = monthly_pattern / overall_mean

        # Apply adjustment
        adjusted_visitors = visitors.copy()
        for month in range(1, 13):
            mask = adjusted_visitors.index.month == month
            adjusted_visitors[mask] = adjusted_visitors[mask] / seasonal_factors[month]

        return adjusted_visitors

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate signals based on visitor arrival data
        Expected data columns: ['visitor_arrivals', 'market_close'] (optional)
        """
        signals = pd.Series(0, index=data.index)

        if 'visitor_arrivals' not in data.columns:
            return signals

        visitors = data['visitor_arrivals']

        # Apply seasonal adjustment
        if self.seasonal_adjust:
            visitors = self.seasonal_adjust_visitors(visitors)

        # Calculate visitor growth
        visitor_growth = visitors.pct_change(period=self.lookback_months)
        visitor_ma = visitors.rolling(window=self.lookback_months).mean()

        # Generate signals
        for i in range(self.lookback_months, len(data)):
            current_growth = visitor_growth.iloc[i]
            current_visitors = visitors.iloc[i]
            avg_visitors = visitor_ma.iloc[i]

            # Strong bullish signals
            if current_growth > self.growth_threshold * 2:
                signals.iloc[i] = Signal.BUY.value * 2
            elif current_growth > self.growth_threshold:
                signals.iloc[i] = Signal.BUY.value

            # Bearish signals
            elif current_growth < -self.growth_threshold * 2:
                signals.iloc[i] = Signal.SELL.value * 2
            elif current_growth < -self.growth_threshold:
                signals.iloc[i] = Signal.SELL.value

        return signals


class PMIStrategy(BaseStrategy):
    """
    Purchasing Managers Index (PMI) Strategy

    Strategy:
    - PMI > 50 = Expansion (bullish)
    - PMI < 50 = Contraction (bearish)
    - PMI trends more important than absolute levels
    - Combine manufacturing and services PMI if available
    """

    def __init__(
        self,
        expansion_threshold: float = 55,
        contraction_threshold: float = 45,
        trend_periods: int = 3,
        combine_manufacturing_services: bool = True
    ):
        """
        Initialize PMI Strategy

        Args:
            expansion_threshold: PMI level indicating strong expansion
            contraction_threshold: PMI level indicating contraction
            trend_periods: Number of periods to consider for trend
            combine_manufacturing_services: Combine mfg and services PMI
        """
        super().__init__(
            name=f"PMI_{trend_periods}periods",
            params={
                'expansion_threshold': expansion_threshold,
                'contraction_threshold': contraction_threshold,
                'trend_periods': trend_periods,
                'combine_manufacturing_services': combine_manufacturing_services
            }
        )
        self.expansion_threshold = expansion_threshold
        self.contraction_threshold = contraction_threshold
        self.trend_periods = trend_periods
        self.combine_mfg_services = combine_manufacturing_services

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate signals based on PMI data
        Expected data columns: ['pmi_manufacturing', 'pmi_services'] (optional)
        """
        signals = pd.Series(0, index=data.index)

        # Get PMI data
        if self.combine_mfg_services and all(col in data.columns for col in ['pmi_manufacturing', 'pmi_services']):
            # Combined PMI (weighted average)
            pmi = (data['pmi_manufacturing'] + data['pmi_services']) / 2
        elif 'pmi_manufacturing' in data.columns:
            pmi = data['pmi_manufacturing']
        elif 'pmi_services' in data.columns:
            pmi = data['pmi_services']
        else:
            return signals

        # Calculate PMI trend
        pmi_trend = pmi.diff(self.trend_periods)

        for i in range(self.trend_periods, len(data)):
            current_pmi = pmi.iloc[i]
            current_trend = pmi_trend.iloc[i]

            # Strong expansion signals
            if current_pmi > self.expansion_threshold:
                if current_trend > 0:  # Accelerating expansion
                    signals.iloc[i] = Signal.BUY.value * 2
                else:
                    signals.iloc[i] = Signal.BUY.value

            # Contraction signals
            elif current_pmi < self.contraction_threshold:
                if current_trend < 0:  # Accelerating contraction
                    signals.iloc[i] = Signal.SELL.value * 2
                else:
                    signals.iloc[i] = Signal.SELL.value

            # Trend-based signals
            elif current_trend > 5:  # Strong uptrend
                signals.iloc[i] = Signal.BUY.value
            elif current_trend < -5:  # Strong downtrend
                signals.iloc[i] = Signal.SELL.value

        return signals


class UnemploymentStrategy(BaseStrategy):
    """
    Unemployment Rate Strategy

    Strategy:
    - Rising unemployment = Economic weakness = Bearish
    - Falling unemployment = Economic strength = Bullish
    - Focus on unemployment rate changes and trends
    - Consider lagged effects
    """

    def __init__(
        self,
        rate_change_threshold: float = 0.1,
        trend_periods: int = 6,
        lag_periods: int = 1
    ):
        """
        Initialize Unemployment Strategy

        Args:
            rate_change_threshold: Threshold for unemployment rate changes
            trend_periods: Periods for trend analysis
            lag_periods: Lag periods to account for delayed effects
        """
        super().__init__(
            name=f"Unemployment_{trend_periods}periods",
            params={
                'rate_change_threshold': rate_change_threshold,
                'trend_periods': trend_periods,
                'lag_periods': lag_periods
            }
        )
        self.rate_change_threshold = rate_change_threshold
        self.trend_periods = trend_periods
        self.lag_periods = lag_periods

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate signals based on unemployment data
        Expected data columns: ['unemployment_rate']
        """
        signals = pd.Series(0, index=data.index)

        if 'unemployment_rate' not in data.columns:
            return signals

        unemployment = data['unemployment_rate']

        # Calculate unemployment rate change
        unemp_change = unemployment.diff()
        unemp_trend = unemployment.diff(self.trend_periods)

        # Apply lag to account for delayed effects
        unemp_trend_lagged = unemp_trend.shift(self.lag_periods)

        for i in range(self.trend_periods + self.lag_periods, len(data)):
            current_change = unemp_change.iloc[i]
            current_trend = unemp_trend_lagged.iloc[i]

            # Bearish signals - rising unemployment
            if current_change > self.rate_change_threshold:
                if current_trend > 0:  # Accelerating rise
                    signals.iloc[i] = Signal.SELL.value * 2
                else:
                    signals.iloc[i] = Signal.SELL.value

            # Bullish signals - falling unemployment
            elif current_change < -self.rate_change_threshold:
                if current_trend < 0:  # Accelerating fall
                    signals.iloc[i] = Signal.BUY.value * 2
                else:
                    signals.iloc[i] = Signal.BUY.value

            # Trend signals
            elif current_trend > 1.0:  # Rising trend
                signals.iloc[i] = Signal.SELL.value
            elif current_trend < -1.0:  # Falling trend
                signals.iloc[i] = Signal.BUY.value

        return signals


class CompositeEconomicStrategy(BaseStrategy):
    """
    Composite Economic Indicator Strategy

    Combines multiple economic indicators for more robust signals
    """

    def __init__(
        self,
        indicators: Dict[str, float],  # indicator_name: weight
        consensus_threshold: float = 0.6,
        min_signals: int = 2
    ):
        """
        Initialize Composite Economic Strategy

        Args:
            indicators: Dictionary of indicator names and their weights
            consensus_threshold: Threshold for consensus
            min_signals: Minimum number of agreeing signals
        """
        super().__init__(
            name=f"CompositeEconomic_{len(indicators)}factors",
            params={
                'indicators': indicators,
                'consensus_threshold': consensus_threshold,
                'min_signals': min_signals
            }
        )
        self.indicators = indicators
        self.consensus_threshold = consensus_threshold
        self.min_signals = min_signals

        # Normalize weights
        total_weight = sum(self.indicators.values())
        if total_weight > 0:
            self.indicators = {k: v/total_weight for k, v in self.indicators.items()}

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate combined signals from multiple economic indicators
        """
        signals = pd.Series(0, index=data.index)

        # Initialize indicator strategies
        indicator_strategies = {
            'hibor': HIBORStrategy(),
            'gdp': GDPGrowthStrategy(),
            'visitor_arrival': VisitorArrivalStrategy(),
            'pmi': PMIStrategy(),
            'unemployment': UnemploymentStrategy()
        }

        # Collect signals from each indicator
        indicator_signals = {}
        for ind_name in self.indicators:
            if ind_name in indicator_strategies and ind_name in [self._get_data_indicator(col) for col in data.columns]:
                # Try to identify which column corresponds to this indicator
                col_name = self._find_indicator_column(data, ind_name)
                if col_name:
                    # Create a new dataframe with the expected column name
                    indicator_data = data[[col_name]].copy()
                    indicator_data.columns = [self._get_expected_column(ind_name)]
                    indicator_signals[ind_name] = indicator_strategies[ind_name].generate_signals(indicator_data)

        # Combine signals with weights
        if indicator_signals:
            combined_score = pd.Series(0, index=data.index)

            for ind_name, weight in self.indicators.items():
                if ind_name in indicator_signals:
                    combined_score += indicator_signals[ind_name] * weight

            # Generate final signals based on consensus
            # Normalize combined score to [-1, 1] range
            max_possible = sum(self.indicators.values())
            if max_possible > 0:
                normalized_score = combined_score / max_possible
            else:
                normalized_score = combined_score

            # Apply threshold
            signals[normalized_score > self.consensus_threshold] = Signal.BUY.value
            signals[normalized_score < -self.consensus_threshold] = Signal.SELL.value

        return signals

    def _get_data_indicator(self, column_name: str) -> str:
        """Map column name to indicator type"""
        mapping = {
            'hibor_rate': 'hibor',
            'hk_hibor': 'hibor',
            'gdp_growth': 'gdp',
            'gdp_qoq': 'gdp',
            'visitor_arrivals': 'visitor_arrival',
            'hk_visitors': 'visitor_arrival',
            'tourist_arrivals': 'visitor_arrival',
            'pmi_manufacturing': 'pmi',
            'pmi_services': 'pmi',
            'pmi_combined': 'pmi',
            'unemployment_rate': 'unemployment',
            'jobless_rate': 'unemployment'
        }
        return mapping.get(column_name.lower(), column_name)

    def _find_indicator_column(self, data: pd.DataFrame, indicator_name: str) -> Optional[str]:
        """Find the column corresponding to an indicator"""
        for col in data.columns:
            if self._get_data_indicator(col) == indicator_name:
                return col
        return None

    def _get_expected_column(self, indicator_name: str) -> str:
        """Get expected column name for indicator"""
        mapping = {
            'hibor': 'hibor_rate',
            'gdp': 'gdp_growth',
            'visitor_arrival': 'visitor_arrivals',
            'pmi': 'pmi_manufacturing',
            'unemployment': 'unemployment_rate'
        }
        return mapping.get(indicator_name, indicator_name)


# Fundamental strategy registry
FUNDAMENTAL_STRATEGIES = {
    'hibor': HIBORStrategy,
    'gdp_growth': GDPGrowthStrategy,
    'visitor_arrival': VisitorArrivalStrategy,
    'pmi': PMIStrategy,
    'unemployment': UnemploymentStrategy,
    'composite': CompositeEconomicStrategy,
}

__all__ = [
    'HIBORStrategy',
    'GDPGrowthStrategy',
    'VisitorArrivalStrategy',
    'PMIStrategy',
    'UnemploymentStrategy',
    'CompositeEconomicStrategy',
    'FUNDAMENTAL_STRATEGIES'
]
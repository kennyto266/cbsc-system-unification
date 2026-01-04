"""
Base Fundamental Strategy
基本面策略基類

This module provides the base class for all fundamental analysis-based strategies.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import pandas as pd
import numpy as np

from ..base import BaseStrategy
from ..enhanced_factory import StrategyMetadata, StrategyType

logger = logging.getLogger(__name__)


class BaseFundamentalStrategy(BaseStrategy):
    """
    Base class for fundamental analysis strategies

    Fundamental strategies use economic indicators, financial metrics,
    and other non-price data to generate trading signals.
    """

    # Strategy metadata
    STRATEGY_TYPE = StrategyType.FUNDAMENTAL

    # Default parameters
    DEFAULT_PARAMETERS = {
        'data_frequency': 'D',  # 'D', 'W', 'M', 'Q'
        'lookback_periods': 12,  # Number of periods for analysis
        'signal_threshold': 0.02,  # Minimum signal strength
        'min_data_points': 5,  # Minimum data points required
        'data_source': 'auto'  # 'auto', 'manual', 'api'
    }

    # Optional parameters
    OPTIONAL_PARAMETERS = {
        'data_frequency': {
            'type': str,
            'choices': ['D', 'W', 'M', 'Q'],
            'default': 'D'
        },
        'lookback_periods': {
            'type': int,
            'min': 1,
            'max': 252,
            'default': 12
        },
        'signal_threshold': {
            'type': float,
            'min': 0.001,
            'max': 0.1,
            'default': 0.02
        },
        'min_data_points': {
            'type': int,
            'min': 1,
            'max': 100,
            'default': 5
        },
        'data_source': {
            'type': str,
            'choices': ['auto', 'manual', 'api'],
            'default': 'auto'
        }
    }

    def __init__(
        self,
        instance_id: UUID,
        config: Dict[str, Any],
        metadata: StrategyMetadata
    ):
        """
        Initialize fundamental strategy

        Args:
            instance_id: Unique instance identifier
            config: Strategy configuration
            metadata: Strategy metadata
        """
        super().__init__(instance_id, config, metadata)

        self.data_frequency = config.get('data_frequency', 'D')
        self.lookback_periods = config.get('lookback_periods', 12)
        self.signal_threshold = config.get('signal_threshold', 0.02)
        self.min_data_points = config.get('min_data_points', 5)
        self.data_source = config.get('data_source', 'auto')

        # Data cache
        self._fundamental_data = {}
        self._last_update = None

    @abstractmethod
    def fetch_fundamental_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Fetch fundamental data for specified symbols

        Args:
            symbols: List of symbols to fetch data for

        Returns:
            Dictionary of fundamental data by symbol
        """
        pass

    @abstractmethod
    def calculate_fundamental_signals(
        self,
        fundamental_data: Dict[str, pd.DataFrame],
        market_data: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Dict[str, pd.Series]:
        """
        Calculate signals based on fundamental data

        Args:
            fundamental_data: Dictionary of fundamental data
            market_data: Optional market price data

        Returns:
            Dictionary of signals by symbol
        """
        pass

    def validate_data_quality(
        self,
        data: pd.DataFrame,
        data_type: str = "fundamental"
    ) -> bool:
        """
        Validate data quality

        Args:
            data: DataFrame to validate
            data_type: Type of data ('fundamental' or 'market')

        Returns:
            True if data is valid
        """
        if data is None or data.empty:
            logger.warning(f"No {data_type} data available")
            return False

        if len(data) < self.min_data_points:
            logger.warning(f"Insufficient {data_type} data: {len(data)} < {self.min_data_points}")
            return False

        # Check for missing values
        missing_pct = data.isnull().sum().sum() / (len(data) * len(data.columns))
        if missing_pct > 0.5:  # More than 50% missing
            logger.warning(f"High missing data ratio in {data_type}: {missing_pct:.2%}")
            return False

        return True

    def align_data_series(
        self,
        fundamental_data: pd.DataFrame,
        market_data: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Align fundamental and market data series

        Args:
            fundamental_data: Fundamental data DataFrame
            market_data: Market data DataFrame

        Returns:
            Aligned fundamental and market data
        """
        # Find common date range
        start_date = max(fundamental_data.index.min(), market_data.index.min())
        end_date = min(fundamental_data.index.max(), market_data.index.max())

        # Slice data to common range
        fund_aligned = fundamental_data.loc[start_date:end_date]
        market_aligned = market_data.loc[start_date:end_date]

        return fund_aligned, market_aligned

    def calculate_signal_strength(
        self,
        signal_value: float,
        threshold: Optional[float] = None
    ) -> float:
        """
        Calculate signal strength

        Args:
            signal_value: Raw signal value
            threshold: Optional threshold

        Returns:
            Signal strength (-1 to 1)
        """
        if threshold is None:
            threshold = self.signal_threshold

        # Normalize signal
        if abs(signal_value) < threshold:
            return 0.0

        # Calculate strength (clamped between -1 and 1)
        strength = np.sign(signal_value) * min(abs(signal_value) / threshold, 1.0)

        return float(strength)

    def generate_signals(
        self,
        data: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Generate signals based on fundamental data

        Args:
            data: Dictionary of data (includes both fundamental and market data)

        Returns:
            DataFrame with signals
        """
        # Separate fundamental and market data
        fundamental_data = {}
        market_data = {}

        for symbol, df in data.items():
            # Check if this is fundamental data (specific columns)
            fundamental_cols = self._get_fundamental_columns()
            if any(col in df.columns for col in fundamental_cols):
                fundamental_data[symbol] = df

            # Check if this is market data (OHLCV)
            if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
                market_data[symbol] = df

        if not fundamental_data:
            logger.warning("No fundamental data found")
            # Return empty signals with correct index
            all_dates = set()
            for df in data.values():
                all_dates.update(df.index)
            if all_dates:
                return pd.DataFrame(0, index=sorted(all_dates), columns=['signal'])
            else:
                return pd.DataFrame()

        # Validate fundamental data
        for symbol, df in fundamental_data.items():
            if not self.validate_data_quality(df, "fundamental"):
                logger.error(f"Invalid fundamental data for {symbol}")
                continue

        # Calculate fundamental signals
        signals = self.calculate_fundamental_signals(
            fundamental_data,
            market_data if market_data else None
        )

        # Convert to DataFrame format
        if signals:
            # Get all dates from all signal series
            all_dates = set()
            for signal_series in signals.values():
                all_dates.update(signal_series.index)

            if all_dates:
                # Create combined signals DataFrame
                combined_signals = pd.DataFrame(index=sorted(all_dates))

                # Add individual asset signals
                for symbol, signal_series in signals.items():
                    combined_signals[f"{symbol}_signal"] = signal_series

                # Add portfolio signal (average of all signals)
                signal_cols = [col for col in combined_signals.columns if col.endswith('_signal')]
                if signal_cols:
                    combined_signals['signal'] = combined_signals[signal_cols].mean(axis=1)

                return combined_signals

        # Return empty DataFrame if no signals
        return pd.DataFrame()

    def _get_fundamental_columns(self) -> List[str]:
        """
        Get list of fundamental data column names

        Returns:
            List of column names
        """
        # Common fundamental data columns
        return [
            'hibor_rate', 'gdp_growth', 'pmi', 'cpi', 'unemployment_rate',
            'visitor_arrivals', 'retail_sales', 'industrial_production',
            'consumer_confidence', 'inflation_rate', 'interest_rate',
            'earnings_per_share', 'price_to_earnings', 'dividend_yield',
            'book_value', 'roe', 'debt_to_equity'
        ]

    def update_data_cache(
        self,
        fundamental_data: Dict[str, pd.DataFrame]
    ):
        """
        Update fundamental data cache

        Args:
            fundamental_data: New fundamental data
        """
        self._fundamental_data = fundamental_data
        self._last_update = datetime.now()

    def get_data_status(self) -> Dict[str, Any]:
        """
        Get status of fundamental data

        Returns:
            Dictionary with data status
        """
        status = {
            "data_source": self.data_source,
            "last_update": self._last_update,
            "cached_symbols": list(self._fundamental_data.keys()),
            "data_quality": "unknown"
        }

        # Check data quality if cached data exists
        if self._fundamental_data:
            valid_count = 0
            total_count = len(self._fundamental_data)

            for symbol, df in self._fundamental_data.items():
                if self.validate_data_quality(df, "fundamental"):
                    valid_count += 1

            if total_count > 0:
                quality_ratio = valid_count / total_count
                if quality_ratio > 0.9:
                    status["data_quality"] = "excellent"
                elif quality_ratio > 0.7:
                    status["data_quality"] = "good"
                elif quality_ratio > 0.5:
                    status["data_quality"] = "fair"
                else:
                    status["data_quality"] = "poor"

        return status

    def execute(
        self,
        data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Execute fundamental strategy

        Args:
            data: Dictionary of data

        Returns:
            Dictionary with execution results
        """
        start_time = datetime.now()

        try:
            # Generate signals
            signals = self.generate_signals(data)

            # Prepare results
            results = {}
            for symbol, df in data.items():
                # Find corresponding signals for this symbol
                signal_col = f"{symbol}_signal"
                if signal_col in signals.columns:
                    asset_signals = signals[[signal_col]].copy()
                    asset_signals.columns = ['signal']
                    results[symbol] = {
                        'signals': asset_signals,
                        'fundamental_data': self._fundamental_data.get(symbol, pd.DataFrame()),
                        'data_quality': self.validate_data_quality(
                            self._fundamental_data.get(symbol, pd.DataFrame()),
                            "fundamental"
                        )
                    }

            # Add strategy level results
            if 'signal' in signals.columns:
                results['_strategy'] = {
                    'signals': signals[['signal']],
                    'data_status': self.get_data_status(),
                    'strategy_type': 'fundamental'
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
            logger.error(f"Fundamental strategy execution failed: {e}")
            raise
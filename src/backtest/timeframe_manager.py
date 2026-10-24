"""
Timeframe Manager for CBSC Backtest System
Handles multiple timeframe resampling and alignment
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from datetime import datetime, timezone, timedelta
import pytz
from enum import Enum


class Timeframe(Enum):
    """Standard timeframes"""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    HOUR_8 = "8h"
    DAY_1 = "1d"
    DAY_3 = "3d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"


class MarketSession(Enum):
    """Market session types"""
    HK = "HK"  # Hong Kong
    US = "US"  # US
    EUR = "EUR"  # European


class TimeframeManager:
    """
    Manages timeframe operations for backtesting
    """

    # Timeframe configurations in seconds
    TIMEFRAME_SECONDS = {
        Timeframe.MINUTE_1.value: 60,
        Timeframe.MINUTE_5.value: 300,
        Timeframe.MINUTE_15.value: 900,
        Timeframe.MINUTE_30.value: 1800,
        Timeframe.HOUR_1.value: 3600,
        Timeframe.HOUR_4.value: 14400,
        Timeframe.HOUR_8.value: 28800,
        Timeframe.DAY_1.value: 86400,
        Timeframe.DAY_3.value: 259200,
        Timeframe.WEEK_1.value: 604800,
        Timeframe.MONTH_1.value: 2592000,  # Approximate
    }

    # Market session hours (UTC)
    MARKET_SESSIONS = {
        MarketSession.HK: {
            "open": "01:00",  # 9:00 HK time
            "close": "08:00",  # 16:00 HK time
            "timezone": "Asia/Hong_Kong"
        },
        MarketSession.US: {
            "open": "14:30",  # 9:30 US Eastern
            "close": "21:00",  # 16:00 US Eastern
            "timezone": "America/New_York"
        },
    }

    def __init__(self, base_timeframe: str = "1m", market_session: MarketSession = MarketSession.HK):
        """
        Initialize TimeframeManager

        Args:
            base_timeframe: Base timeframe for data
            market_session: Market session for trading hours
        """
        self.base_timeframe = base_timeframe
        self.market_session = market_session
        self.market_tz = pytz.timezone(self.MARKET_SESSIONS[market_session]["timezone"])

    def get_timeframe_seconds(self, timeframe: str) -> int:
        """
        Get timeframe in seconds

        Args:
            timeframe: Timeframe string (e.g., '1m', '1h', '1d')

        Returns:
            int: Timeframe in seconds
        """
        return self.TIMEFRAME_SECONDS.get(timeframe, 0)

    def validate_timeframe(self, timeframe: str) -> bool:
        """
        Validate if timeframe is supported

        Args:
            timeframe: Timeframe string

        Returns:
            bool: True if valid
        """
        return timeframe in self.TIMEFRAME_SECONDS

    def resample_ohlcv(
        self,
        data: pd.DataFrame,
        target_timeframe: str,
        method: str = "ohlc"
    ) -> pd.DataFrame:
        """
        Resample OHLCV data to target timeframe

        Args:
            data: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
            target_timeframe: Target timeframe (e.g., '5m', '1h', '1d')
            method: Resampling method ('ohlc', 'vwap', 'close')

        Returns:
            pd.DataFrame: Resampled data
        """
        if not self.validate_timeframe(target_timeframe):
            raise ValueError(f"Unsupported timeframe: {target_timeframe}")

        # Ensure data has datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)

        # Get resample rule
        rule = self._get_pandas_resample_rule(target_timeframe)

        # Resample based on method
        if method == "ohlc":
            resampled = self._resample_ohlc(data, rule)
        elif method == "vwap":
            resampled = self._resample_vwap(data, rule)
        elif method == "close":
            resampled = self._resample_close(data, rule)
        else:
            raise ValueError(f"Unsupported resampling method: {method}")

        return resampled

    def _get_pandas_resample_rule(self, timeframe: str) -> str:
        """Convert timeframe to pandas resample rule"""
        timeframe_map = {
            Timeframe.MINUTE_1.value: "1T",
            Timeframe.MINUTE_5.value: "5T",
            Timeframe.MINUTE_15.value: "15T",
            Timeframe.MINUTE_30.value: "30T",
            Timeframe.HOUR_1.value: "1H",
            Timeframe.HOUR_4.value: "4H",
            Timeframe.HOUR_8.value: "8H",
            Timeframe.DAY_1.value: "1D",
            Timeframe.DAY_3.value: "3D",
            Timeframe.WEEK_1.value: "1W",
            Timeframe.MONTH_1.value: "1M",
        }
        return timeframe_map.get(timeframe, "1T")

    def _resample_ohlc(self, data: pd.DataFrame, rule: str) -> pd.DataFrame:
        """Resample using OHLC method"""
        resampled = pd.DataFrame()

        # OHLC prices
        resampled['open'] = data['open'].resample(rule).first()
        resampled['high'] = data['high'].resample(rule).max()
        resampled['low'] = data['low'].resample(rule).min()
        resampled['close'] = data['close'].resample(rule).last()

        # Volume
        resampled['volume'] = data['volume'].resample(rule).sum()

        # Remove rows with NaN values
        resampled = resampled.dropna()

        return resampled

    def _resample_vwap(self, data: pd.DataFrame, rule: str) -> pd.DataFrame:
        """Resample using Volume-Weighted Average Price"""
        resampled = pd.DataFrame()

        # Calculate VWAP for each period
        vwap = (data['close'] * data['volume']).resample(rule).sum() / data['volume'].resample(rule).sum()

        resampled['open'] = data['open'].resample(rule).first()
        resampled['high'] = data['high'].resample(rule).max()
        resampled['low'] = data['low'].resample(rule).min()
        resampled['close'] = vwap
        resampled['volume'] = data['volume'].resample(rule).sum()

        resampled = resampled.dropna()
        return resampled

    def _resample_close(self, data: pd.DataFrame, rule: str) -> pd.DataFrame:
        """Resample using close prices only"""
        resampled = pd.DataFrame()

        resampled['open'] = data['close'].resample(rule).first()
        resampled['high'] = data['close'].resample(rule).max()
        resampled['low'] = data['close'].resample(rule).min()
        resampled['close'] = data['close'].resample(rule).last()
        resampled['volume'] = data['volume'].resample(rule).sum()

        resampled = resampled.dropna()
        return resampled

    def align_to_market_hours(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Align data to market trading hours

        Args:
            data: DataFrame with datetime index

        Returns:
            pd.DataFrame: Filtered data for market hours only
        """
        # Convert to market timezone
        if data.index.tz is None:
            data.index = data.index.tz_localize('UTC')
        data.index = data.index.tz_convert(self.market_tz)

        # Get market hours
        session = self.MARKET_SESSIONS[self.market_session]
        open_time = pd.to_datetime(session["open"]).time()
        close_time = pd.to_datetime(session["close"]).time()

        # Filter to market hours
        mask = (
            (data.index.time >= open_time) &
            (data.index.time <= close_time) &
            (data.index.dayofweek < 5)  # Monday to Friday
        )

        return data[mask]

    def handle_timezones(self, data: pd.DataFrame, source_tz: str = "UTC") -> pd.DataFrame:
        """
        Handle timezone conversion for data

        Args:
            data: DataFrame with datetime index
            source_tz: Source timezone

        Returns:
            pd.DataFrame: Data with timezone-aware index
        """
        # Ensure timezone awareness
        if data.index.tz is None:
            data.index = data.index.tz_localize(source_tz)

        # Convert to market timezone
        data.index = data.index.tz_convert(self.market_tz)

        return data

    def interpolate_missing_data(
        self,
        data: pd.DataFrame,
        method: str = "time",
        limit: int = None
    ) -> pd.DataFrame:
        """
        Interpolate missing data points

        Args:
            data: DataFrame with potential missing values
            method: Interpolation method ('time', 'linear', 'forward')
            limit: Maximum number of consecutive NaNs to fill

        Returns:
            pd.DataFrame: Data with interpolated values
        """
        if method == "time":
            # Time-based interpolation
            data = data.interpolate(method='time', limit=limit)
        elif method == "linear":
            # Linear interpolation
            data = data.interpolate(method='linear', limit=limit)
        elif method == "forward":
            # Forward fill
            data = data.fillna(method='ffill', limit=limit)
        else:
            raise ValueError(f"Unsupported interpolation method: {method}")

        return data

    def get_timeframe_list(self) -> List[str]:
        """
        Get list of supported timeframes

        Returns:
            List[str]: List of timeframe strings
        """
        return list(self.TIMEFRAME_SECONDS.keys())

    def align_multiple_timeframes(
        self,
        data_dict: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Align multiple timeframes into a single DataFrame

        Args:
            data_dict: Dictionary of DataFrames with different timeframes

        Returns:
            pd.DataFrame: Aligned data with columns for each timeframe
        """
        if not data_dict:
            return pd.DataFrame()

        # Get the base (lowest) timeframe
        base_timeframe = min(data_dict.keys(), key=lambda x: self.get_timeframe_seconds(x))
        base_data = data_dict[base_timeframe].copy()

        # Add other timeframes as columns
        for timeframe, data in data_dict.items():
            if timeframe == base_timeframe:
                continue

            # Resample to base timeframe
            resampled = self.resample_ohlcv(data, base_timeframe, method="close")

            # Merge with base data
            suffix = f"_{timeframe}"
            base_data = base_data.join(
                resampled[['open', 'high', 'low', 'close']].add_suffix(suffix),
                how='left'
            )

        # Forward fill to handle non-matching timestamps
        base_data = base_data.fillna(method='ffill')

        return base_data

    def calculate_returns(
        self,
        data: pd.DataFrame,
        method: str = "simple"
    ) -> pd.Series:
        """
        Calculate returns from price data

        Args:
            data: DataFrame with price data
            method: Return calculation method ('simple', 'log')

        Returns:
            pd.Series: Returns
        """
        if method == "simple":
            returns = data['close'].pct_change()
        elif method == "log":
            returns = np.log(data['close'] / data['close'].shift(1))
        else:
            raise ValueError(f"Unsupported return calculation method: {method}")

        return returns.fillna(0)

    def get_trading_sessions(self, start_date: datetime, end_date: datetime) -> pd.DatetimeIndex:
        """
        Get valid trading sessions between dates

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            pd.DatetimeIndex: Valid trading timestamps
        """
        # Create date range
        date_range = pd.date_range(
            start=start_date,
            end=end_date,
            freq=self._get_pandas_resample_rule(self.base_timeframe),
            tz=self.market_tz
        )

        # Filter to market hours and weekdays
        session = self.MARKET_SESSIONS[self.market_session]
        open_time = pd.to_datetime(session["open"]).time()
        close_time = pd.to_datetime(session["close"]).time()

        mask = (
            (date_range.time >= open_time) &
            (date_range.time <= close_time) &
            (date_range.dayofweek < 5)
        )

        return date_range[mask]
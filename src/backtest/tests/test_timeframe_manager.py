"""
Tests for TimeframeManager
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

from ..timeframe_manager import TimeframeManager, Timeframe, MarketSession


class TestTimeframeManager:
    """Test cases for TimeframeManager"""

    @pytest.fixture
    def manager(self):
        """Create a TimeframeManager instance"""
        return TimeframeManager(base_timeframe="1m", market_session=MarketSession.HK)

    @pytest.fixture
    def sample_ohlcv_data(self):
        """Create sample OHLCV data"""
        # Create 1 day of minute data
        index = pd.date_range(
            start="2024-01-01 00:00:00",
            end="2024-01-01 23:59:00",
            freq="1T",
            tz="UTC"
        )

        # Generate synthetic price data
        np.random.seed(42)
        close_prices = 100 + np.cumsum(np.random.randn(len(index)) * 0.1)

        data = pd.DataFrame({
            'open': close_prices,
            'high': close_prices * 1.001,
            'low': close_prices * 0.999,
            'close': close_prices,
            'volume': np.random.randint(1000, 10000, len(index))
        }, index=index)

        return data

    def test_get_timeframe_seconds(self, manager):
        """Test getting timeframe in seconds"""
        assert manager.get_timeframe_seconds("1m") == 60
        assert manager.get_timeframe_seconds("5m") == 300
        assert manager.get_timeframe_seconds("1h") == 3600
        assert manager.get_timeframe_seconds("1d") == 86400
        assert manager.get_timeframe_seconds("invalid") == 0

    def test_validate_timeframe(self, manager):
        """Test timeframe validation"""
        assert manager.validate_timeframe("1m") is True
        assert manager.validate_timeframe("1h") is True
        assert manager.validate_timeframe("1d") is True
        assert manager.validate_timeframe("invalid") is False

    def test_resample_ohlcv_to_5m(self, manager, sample_ohlcv_data):
        """Test resampling from 1m to 5m"""
        resampled = manager.resample_ohlcv(sample_ohlcv_data, "5m", method="ohlc")

        # Check if we have approximately 1/5 of the data points
        expected_length = len(sample_ohlcv_data) // 5
        assert len(resampled) <= expected_length + 1

        # Check if OHLC relationships hold
        assert (resampled['high'] >= resampled['open']).all()
        assert (resampled['high'] >= resampled['close']).all()
        assert (resampled['low'] <= resampled['open']).all()
        assert (resampled['low'] <= resampled['close']).all()

        # Check if volume is summed correctly
        # This is an approximate check due to potential rounding
        total_volume_original = sample_ohlcv_data['volume'].sum()
        total_volume_resampled = resampled['volume'].sum()
        assert abs(total_volume_original - total_volume_resampled) < 0.01 * total_volume_original

    def test_resample_ohlcv_to_1h(self, manager, sample_ohlcv_data):
        """Test resampling from 1m to 1h"""
        resampled = manager.resample_ohlcv(sample_ohlcv_data, "1h", method="ohlc")

        # Check if we have approximately 1/60 of the data points
        expected_length = len(sample_ohlcv_data) // 60
        assert len(resampled) <= expected_length + 1

        # Verify data integrity
        assert not resampled.isnull().any().any()

    def test_resample_vwap(self, manager, sample_ohlcv_data):
        """Test VWAP resampling"""
        resampled_vwap = manager.resample_ohlcv(sample_ohlcv_data, "5m", method="vwap")
        resampled_ohlc = manager.resample_ohlcv(sample_ohlcv_data, "5m", method="ohlc")

        # VWAP close should be different from OHLC close
        assert not (resampled_vwap['close'] == resampled_ohlc['close']).all()

    def test_resample_close(self, manager, sample_ohlcv_data):
        """Test close-only resampling"""
        resampled = manager.resample_ohlcv(sample_ohlcv_data, "5m", method="close")

        # In close method, all OHLC should equal the last close price
        assert (resampled['open'] == resampled['close']).all()
        assert (resampled['high'] == resampled['close']).all()
        assert (resampled['low'] == resampled['close']).all()

    def test_invalid_resample_method(self, manager, sample_ohlcv_data):
        """Test invalid resampling method"""
        with pytest.raises(ValueError):
            manager.resample_ohlcv(sample_ohlcv_data, "5m", method="invalid")

    def test_invalid_target_timeframe(self, manager, sample_ohlcv_data):
        """Test invalid target timeframe"""
        with pytest.raises(ValueError):
            manager.resample_ohlcv(sample_ohlcv_data, "invalid", method="ohlc")

    def test_align_to_market_hours(self, manager):
        """Test aligning data to market hours"""
        # Create data covering 24 hours
        index = pd.date_range(
            start="2024-01-01 00:00:00",
            end="2024-01-01 23:59:00",
            freq="1T",
            tz="UTC"
        )

        data = pd.DataFrame({
            'close': 100,
            'volume': 1000
        }, index=index)

        # Align to HK market hours (9:00-16:00 HK time, which is 1:00-8:00 UTC)
        aligned = manager.align_to_market_hours(data)

        # Should only have data during market hours (7 hours = 420 minutes)
        assert len(aligned) == 420

        # Check if first timestamp is during market hours
        assert aligned.index[0].hour == 1  # 9:00 HK time in UTC

    def test_handle_timezones(self, manager):
        """Test timezone handling"""
        # Create naive datetime index
        index = pd.date_range(
            start="2024-01-01 09:00:00",
            periods=10,
            freq="1T"
        )

        data = pd.DataFrame({
            'close': 100,
            'volume': 1000
        }, index=index)

        # Convert timezone-aware
        converted = manager.handle_timezones(data, source_tz="Asia/Hong_Kong")

        # Check if index is now timezone-aware
        assert converted.index.tz is not None
        assert converted.index.tz.zone == "Asia/Hong_Kong"

    def test_interpolate_missing_data(self, manager):
        """Test missing data interpolation"""
        # Create data with missing values
        index = pd.date_range(start="2024-01-01", periods=10, freq="1T")
        data = pd.DataFrame({
            'close': [100, 101, np.nan, 103, np.nan, np.nan, 106, 107, 108, 109],
            'volume': [1000, 1100, np.nan, 1300, np.nan, np.nan, 1600, 1700, 1800, 1900]
        }, index=index)

        # Interpolate using time method
        interpolated = manager.interpolate_missing_data(data, method="time")

        # Check if NaN values are filled
        assert not interpolated.isnull().any().any()

        # Check if interpolated values are reasonable
        assert interpolated.loc[data.index[2], 'close'] > 101
        assert interpolated.loc[data.index[2], 'close'] < 103

    def test_get_timeframe_list(self, manager):
        """Test getting list of supported timeframes"""
        timeframes = manager.get_timeframe_list()

        assert "1m" in timeframes
        assert "5m" in timeframes
        assert "1h" in timeframes
        assert "1d" in timeframes
        assert len(timeframes) == len(manager.TIMEFRAME_SECONDS)

    def test_align_multiple_timeframes(self, manager):
        """Test aligning multiple timeframes"""
        # Create sample data for different timeframes
        base_data = pd.DataFrame({
            'close': [100, 101, 102, 103, 104],
            'open': [99, 100, 101, 102, 103],
            'high': [101, 102, 103, 104, 105],
            'low': [98, 99, 100, 101, 102],
            'volume': [1000, 1100, 1200, 1300, 1400]
        }, index=pd.date_range(start="2024-01-01", periods=5, freq="1T"))

        hourly_data = pd.DataFrame({
            'close': [100, 102, 104],
            'open': [99, 101, 103],
            'high': [101, 103, 105],
            'low': [98, 100, 102],
            'volume': [3300, 3600, 3900]
        }, index=pd.date_range(start="2024-01-01", periods=3, freq="3T"))

        data_dict = {
            "1m": base_data,
            "3m": hourly_data
        }

        aligned = manager.align_multiple_timeframes(data_dict)

        # Check if aligned DataFrame has all columns
        expected_columns = [
            'open', 'high', 'low', 'close', 'volume',  # 1m columns
            'open_3m', 'high_3m', 'low_3m', 'close_3m'  # 3m columns
        ]

        for col in expected_columns:
            assert col in aligned.columns

        # Check if base timeframe data is preserved
        assert len(aligned) == len(base_data)

    def test_calculate_returns_simple(self, manager):
        """Test simple returns calculation"""
        data = pd.DataFrame({
            'close': [100, 101, 102, 101, 103]
        })

        returns = manager.calculate_returns(data, method="simple")

        # First return should be 0 (no previous price)
        assert returns.iloc[0] == 0

        # Calculate expected returns
        expected = np.array([0, 0.01, 0.009901, -0.009804, 0.019802])
        np.testing.assert_array_almost_equal(returns.values, expected, decimal=6)

    def test_calculate_returns_log(self, manager):
        """Test log returns calculation"""
        data = pd.DataFrame({
            'close': [100, 101, 102]
        })

        returns = manager.calculate_returns(data, method="log")

        # Calculate expected log returns
        expected = np.array([0, np.log(101/100), np.log(102/101)])
        np.testing.assert_array_almost_equal(returns.values, expected, decimal=6)

    def test_invalid_return_method(self, manager):
        """Test invalid return calculation method"""
        data = pd.DataFrame({'close': [100, 101, 102]})

        with pytest.raises(ValueError):
            manager.calculate_returns(data, method="invalid")

    def test_get_trading_sessions(self, manager):
        """Test getting valid trading sessions"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)

        sessions = manager.get_trading_sessions(start_date, end_date)

        # Should only include weekdays and market hours
        # January 1, 2024 is a Monday
        assert len(sessions) > 0

        # Check if all sessions are within market hours
        session = manager.MARKET_SESSIONS[manager.market_session]
        open_time = pd.to_datetime(session["open"]).time()
        close_time = pd.to_datetime(session["close"]).time()

        for timestamp in sessions:
            assert open_time <= timestamp.time() <= close_time
            assert timestamp.dayofweek < 5  # Weekday

    def test_market_session_us(self, sample_ohlcv_data):
        """Test with US market session"""
        manager = TimeframeManager(base_timeframe="1m", market_session=MarketSession.US)

        # Test timezone conversion
        converted = manager.handle_timezones(sample_ohlcv_data, source_tz="UTC")

        # Should be in US/Eastern timezone
        assert converted.index.tz.zone == "America/New_York"

        # Test market hours alignment
        aligned = manager.align_to_market_hours(converted)

        # US market hours should be different from HK
        assert len(aligned) > 0
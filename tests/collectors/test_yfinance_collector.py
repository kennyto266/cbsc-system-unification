#!/usr/bin/env python3
"""
Test cases for YFinance Collector
YFinance 收集器測試用例
Task 8.1 - 數據獲取模塊
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import pandas as pd
import numpy as np

from src.collectors.yfinance_collector import (
    YFinanceCollector, YFinanceConfig, Market, DataPoint
)

class TestYFinanceCollector:
    """Test cases for YFinanceCollector"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return YFinanceConfig(
            symbols=["AAPL", "MSFT", "0700.HK"],
            markets=[Market.US, Market.HK],
            intervals=["1d"],
            batch_size=10
        )

    @pytest.fixture
    def mock_influxdb(self):
        """Create mock InfluxDB manager"""
        mock = Mock()
        mock.write_market_data = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def mock_cache(self):
        """Create mock cache service"""
        mock = Mock()
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        mock.ping = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def collector(self, config, mock_influxdb, mock_cache):
        """Create YFinance collector instance"""
        return YFinanceCollector(
            config=config,
            influxdb_manager=mock_influxdb,
            cache_service=mock_cache
        )

    @pytest.mark.asyncio
    async def test_initialization(self, collector):
        """Test collector initialization"""
        assert collector.config.symbols == ["AAPL", "MSFT", "0700.HK"]
        assert collector.config.markets == [Market.US, Market.HK]
        assert collector.stats["total_requests"] == 0
        assert collector.stats["successful_requests"] == 0

    @pytest.mark.asyncio
    async def test_start_stop(self, collector):
        """Test collector start and stop"""
        # Mock aiohttp.ClientSession
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value = Mock()

            await collector.start()
            assert collector.session is not None

            await collector.stop()
            assert collector.session is None

    @pytest.mark.asyncio
    async def test_validate_symbol(self, collector):
        """Test symbol validation"""
        # Test valid symbols
        valid_symbols = ["AAPL", "0700.HK", "MSFT"]
        for symbol in valid_symbols:
            result = await collector._validate_symbol(symbol)
            assert result is not None

        # Test invalid symbols
        invalid_symbols = ["", None, "INVALID"]
        for symbol in invalid_symbols:
            result = await collector._validate_symbol(symbol)
            assert result is None

    @pytest.mark.asyncio
    async def test_collect_historical_data(self, collector):
        """Test historical data collection"""
        # Mock yfinance Ticker
        with patch('yfinance.Ticker') as mock_ticker_class:
            # Setup mock ticker
            mock_ticker = Mock()
            mock_ticker_class.return_value = mock_ticker

            # Create mock historical data
            dates = pd.date_range('2020-01-01', periods=5, freq='D')
            mock_hist = pd.DataFrame({
                'Open': [100, 101, 102, 103, 104],
                'High': [105, 106, 107, 108, 109],
                'Low': [95, 96, 97, 98, 99],
                'Close': [104, 105, 106, 107, 108],
                'Volume': [1000000, 1100000, 1200000, 1300000, 1400000]
            }, index=dates)

            mock_ticker.history.return_value = mock_hist

            # Collect data
            data_points = await collector.collect_historical_data(
                symbol="AAPL",
                period="5d",
                interval="1d"
            )

            # Assertions
            assert len(data_points) == 5
            assert all(isinstance(dp, DataPoint) for dp in data_points)
            assert all(dp.symbol == "AAPL" for dp in data_points)
            assert all(dp.data_type == "price" for dp in data_points)

    @pytest.mark.asyncio
    async def test_collect_real_time_data(self, collector):
        """Test real-time data collection"""
        # Mock yfinance Tickers
        with patch('yfinance.Tickers') as mock_tickers_class:
            # Setup mock tickers
            mock_tickers = Mock()
            mock_tickers_class.return_value = mock_tickers

            # Create mock ticker data
            mock_ticker = Mock()
            mock_tickers.tickers = {"AAPL": mock_ticker}

            # Mock info and history
            mock_ticker.info = {
                "bid": 150.0,
                "ask": 150.5,
                "previousClose": 149.0,
                "currency": "USD"
            }

            dates = pd.date_range('2020-01-01', periods=1, freq='1min')
            mock_hist = pd.DataFrame({
                'Open': [150.0],
                'High': [151.0],
                'Low': [149.0],
                'Close': [150.5],
                'Volume': [10000]
            }, index=dates)

            mock_ticker.history.return_value = mock_hist

            # Collect data
            results = await collector.collect_real_time_data(["AAPL"])

            # Assertions
            assert "AAPL" in results
            assert isinstance(results["AAPL"], DataPoint)
            assert results["AAPL"].symbol == "AAPL"

    @pytest.mark.asyncio
    async def test_collect_dividends_and_splits(self, collector):
        """Test dividend and split collection"""
        with patch('yfinance.Ticker') as mock_ticker_class:
            # Setup mock ticker
            mock_ticker = Mock()
            mock_ticker_class.return_value = mock_ticker

            # Create mock dividend data
            dividend_dates = pd.date_range('2020-01-01', periods=2, freq='Q')
            mock_dividends = pd.Series([0.5, 0.55], index=dividend_dates)
            mock_ticker.dividends = mock_dividends

            # Create mock split data
            split_dates = pd.date_range('2020-06-01', periods=1, freq='D')
            mock_splits = pd.Series([2.0], index=split_dates)
            mock_ticker.splits = mock_splits

            # Collect data
            results = await collector.collect_dividends_and_splits("AAPL")

            # Assertions
            assert "dividends" in results
            assert "splits" in results
            assert len(results["dividends"]) == 2
            assert len(results["splits"]) == 1

    @pytest.mark.asyncio
    async def test_process_historical_data(self, collector):
        """Test historical data processing"""
        # Create test DataFrame
        dates = pd.date_range('2020-01-01', periods=3, freq='D')
        hist = pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [105, 106, 107],
            'Low': [95, 96, 97],
            'Close': [104, 105, 106],
            'Volume': [1000000, 1100000, 1200000],
            'Adj Close': [103, 104, 105]
        }, index=dates)

        # Process data
        data_points = await collector._process_historical_data(hist, "AAPL", "1d")

        # Assertions
        assert len(data_points) == 3
        for dp in data_points:
            assert dp.symbol == "AAPL"
            assert dp.data_type == "price"
            assert dp.interval == "1d"
            assert "open" in dp.fields
            assert "high" in dp.fields
            assert "low" in dp.fields
            assert "close" in dp.fields
            assert "volume" in dp.fields

    def test_validate_ohlc(self, collector):
        """Test OHLC validation"""
        # Valid OHLC
        valid_data = pd.Series({
            "Open": 100,
            "High": 105,
            "Low": 95,
            "Close": 104
        })
        assert collector._validate_ohlc(valid_data) is True

        # Invalid OHLC - high less than close
        invalid_data = pd.Series({
            "Open": 100,
            "High": 103,
            "Low": 95,
            "Close": 104
        })
        assert collector._validate_ohlc(invalid_data) is False

        # Invalid OHLC - negative values
        invalid_data2 = pd.Series({
            "Open": -100,
            "High": 105,
            "Low": 95,
            "Close": 104
        })
        assert collector._validate_ohlc(invalid_data2) is False

    @pytest.mark.asyncio
    async def test_calculate_data_quality_score(self, collector):
        """Test data quality score calculation"""
        # Perfect data
        perfect_data = pd.Series({
            "Open": 100,
            "High": 105,
            "Low": 95,
            "Close": 104
        })
        score = await collector._calculate_data_quality_score(perfect_data)
        assert score > 0.8

        # Data with missing values
        missing_data = pd.Series({
            "Open": np.nan,
            "High": 105,
            "Low": 95,
            "Close": 104
        })
        score = await collector._calculate_data_quality_score(missing_data)
        assert score < 1.0

    def test_get_symbol_market(self, collector):
        """Test market detection from symbol"""
        assert collector._get_symbol_market("AAPL") == Market.US
        assert collector._get_symbol_market("0700.HK") == Market.HK
        assert collector._get_symbol_market("7203.T") == Market.JP

    def test_get_symbol_market_str(self, collector):
        """Test market string detection"""
        assert collector._get_symbol_market_str("AAPL") == "US"
        assert collector._get_symbol_market_str("0700.HK") == "HK"
        assert collector._get_symbol_market_str("7203.T") == "JP"

    @pytest.mark.asyncio
    async def test_get_statistics(self, collector):
        """Test statistics collection"""
        stats = await collector.get_statistics()

        assert "total_requests" in stats
        assert "successful_requests" in stats
        assert "failed_requests" in stats
        assert "data_points_collected" in stats
        assert "cache_hits" in stats
        assert "success_rate" in stats
        assert "cache_hit_rate" in stats

    @pytest.mark.asyncio
    async def test_health_check(self, collector):
        """Test health check"""
        # Mock session
        collector.session = Mock()
        collector.session.close = AsyncMock()

        # Mock yfinance
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker.return_value.info = {"regularMarketPrice": 100}

            health = await collector.health_check()

            assert health["status"] in ["healthy", "degraded", "unhealthy"]
            assert "checks" in health
            assert "timestamp" in health

class TestYFinanceConfig:
    """Test cases for YFinanceConfig"""

    def test_default_values(self):
        """Test default configuration values"""
        config = YFinanceConfig()

        assert config.symbols == []
        assert config.markets == [Market.US, Market.HK]
        assert config.intervals == ["1m", "5m", "15m", "1h", "1d"]
        assert config.rate_limit == 2000
        assert config.timeout == 30
        assert config.retry_attempts == 3
        assert config.batch_size == 100
        assert config.threads == 8

    def test_custom_values(self):
        """Test custom configuration values"""
        config = YFinanceConfig(
            symbols=["AAPL"],
            markets=[Market.US],
            batch_size=50,
            timeout=60
        )

        assert config.symbols == ["AAPL"]
        assert config.markets == [Market.US]
        assert config.batch_size == 50
        assert config.timeout == 60

class TestDataPoint:
    """Test cases for DataPoint"""

    def test_data_point_creation(self):
        """Test DataPoint creation"""
        timestamp = datetime.now()
        fields = {"open": 100, "high": 105, "low": 95, "close": 104}
        tags = {"currency": "USD"}

        dp = DataPoint(
            timestamp=timestamp,
            symbol="AAPL",
            exchange="NASDAQ",
            data_type="price",
            interval="1d",
            fields=fields,
            tags=tags
        )

        assert dp.timestamp == timestamp
        assert dp.symbol == "AAPL"
        assert dp.exchange == "NASDAQ"
        assert dp.data_type == "price"
        assert dp.interval == "1d"
        assert dp.fields == fields
        assert dp.tags == tags
        assert dp.quality_score == 1.0

# Integration tests
@pytest.mark.integration
class TestYFinanceCollectorIntegration:
    """Integration tests for YFinanceCollector"""

    @pytest.mark.asyncio
    async def test_end_to_end_collection(self):
        """Test end-to-end data collection with real API"""
        # This test requires internet connection and should be marked appropriately
        pytest.skip("Integration test - requires internet connection")

    @pytest.mark.asyncio
    async def test_multiple_symbols_parallel(self):
        """Test collecting data for multiple symbols in parallel"""
        # This test would verify parallel collection performance
        pytest.skip("Integration test - requires internet connection")

# Performance tests
@pytest.mark.performance
class TestYFinanceCollectorPerformance:
    """Performance tests for YFinanceCollector"""

    @pytest.mark.asyncio
    async def test_batch_performance(self):
        """Test batch collection performance"""
        # This test would measure performance with large symbol lists
        pytest.skip("Performance test - requires specific setup")

# Error handling tests
@pytest.mark.error_handling
class TestYFinanceCollectorErrors:
    """Error handling tests for YFinanceCollector"""

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test handling of API errors"""
        config = YFinanceConfig(symbols=["INVALID_SYMBOL"])
        mock_influxdb = Mock()
        mock_cache = Mock()
        mock_cache.get = AsyncMock(return_value=None)

        collector = YFinanceCollector(
            config=config,
            influxdb_manager=mock_influxdb,
            cache_service=mock_cache
        )

        # Mock aiohttp to simulate API error
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            mock_session.get = AsyncMock(side_effect=Exception("API Error"))

            await collector.start()

            data_points = await collector.collect_historical_data(
                symbol="INVALID",
                period="1d",
                interval="1d"
            )

            # Should return empty list on error
            assert data_points == []

            await collector.stop()

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test handling of timeouts"""
        config = YFinanceConfig(timeout=1)  # Very short timeout
        mock_influxdb = Mock()
        mock_cache = Mock()
        mock_cache.get = AsyncMock(return_value=None)

        collector = YFinanceCollector(
            config=config,
            influxdb_manager=mock_influxdb,
            cache_service=mock_cache
        )

        # Mock slow response
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate timeout
            async def mock_get(*args, **kwargs):
                await asyncio.sleep(2)  # Longer than timeout
                raise asyncio.TimeoutError()

            mock_session.get = mock_get

            await collector.start()

            data_points = await collector.collect_historical_data(
                symbol="AAPL",
                period="1d",
                interval="1d"
            )

            # Should handle timeout gracefully
            assert data_points == []

            await collector.stop()

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
"""
Test Data Adapters
測試數據適配器

Unit tests for market and economic data adapters
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import pandas as pd
from unittest.mock import Mock, AsyncMock, patch

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_factory import (
    DataAdapterFactory,
    DataSourceType,
    DataProvider,
    get_market_data_adapter,
    get_economic_data_adapter
)
from market_data_adapter import MarketDataAdapter, MarketDataConfig
from economic_data_adapter import EconomicDataAdapter


class TestMarketDataAdapter:
    """Test market data adapter"""

    @pytest.mark.asyncio
    async def test_get_price_data_yahoo(self):
        """Test getting price data from Yahoo Finance"""
        config = MarketDataConfig(
            primary_source="yahoo",
            cache_enabled=False  # Disable cache for testing
        )

        adapter = MarketDataAdapter(config)

        # Test with a common stock
        symbol = "AAPL"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        data = await adapter.get_price_data(symbol, start_date, end_date, "1d")

        assert data is not None, "Should get data for AAPL"
        assert not data.empty, "Data should not be empty"
        assert 'close' in data.columns, "Data should have close column"
        assert 'volume' in data.columns, "Data should have volume column"

        # Check for calculated indicators
        assert 'returns' in data.columns, "Data should have returns column"
        assert 'sma_20' in data.columns, "Data should have SMA_20 column"
        assert 'volatility_20' in data.columns, "Data should have volatility column"

    @pytest.mark.asyncio
    async def test_get_latest_price(self):
        """Test getting latest price"""
        config = MarketDataConfig(
            primary_source="yahoo",
            cache_enabled=False
        )

        adapter = MarketDataAdapter(config)

        # Test with a common stock
        symbol = "MSFT"

        price_data = await adapter.get_latest_price(symbol)

        assert price_data is not None, "Should get latest price for MSFT"
        assert 'price' in price_data, "Should have price field"
        assert 'change' in price_data, "Should have change field"
        assert 'timestamp' in price_data, "Should have timestamp field"

    @pytest.mark.asyncio
    async def test_get_multiple_symbols(self):
        """Test getting multiple symbols"""
        config = MarketDataConfig(
            primary_source="yahoo",
            cache_enabled=False
        )

        adapter = MarketDataAdapter(config)

        symbols = ["AAPL", "MSFT", "GOOGL"]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        results = await adapter.get_multiple_symbols(symbols, start_date, end_date, "1d")

        assert len(results) > 0, "Should get data for some symbols"
        for symbol, data in results.items():
            assert symbol in symbols, f"Symbol {symbol} should be in requested list"
            assert data is not None, f"Data for {symbol} should not be None"
            assert not data.empty, f"Data for {symbol} should not be empty"

    @pytest.mark.asyncio
    async def test_get_technical_indicators(self):
        """Test getting technical indicators"""
        config = MarketDataConfig(
            primary_source="yahoo",
            cache_enabled=False
        )

        adapter = MarketDataAdapter(config)

        symbol = "AAPL"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)  # Need more data for indicators

        indicators = ["SMA_20", "SMA_50", "RSI", "MACD", "BOLLINGER"]

        indicators_df = await adapter.get_technical_indicators(
            symbol, indicators, start_date, end_date
        )

        assert indicators_df is not None, "Should get indicators DataFrame"
        assert not indicators_df.empty, "Indicators DataFrame should not be empty"
        assert 'SMA_20' in indicators_df.columns, "Should have SMA_20 column"
        assert 'RSI' in indicators_df.columns, "Should have RSI column"

    @pytest.mark.asyncio
    async def test_cache_functionality(self):
        """Test cache functionality"""
        config = MarketDataConfig(
            primary_source="yahoo",
            cache_enabled=True,
            cache_ttl=60  # 1 minute
        )

        adapter = MarketDataAdapter(config)

        symbol = "TSLA"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)

        # First call should fetch from source
        data1 = await adapter.get_price_data(symbol, start_date, end_date, "1d")

        # Second call should use cache
        data2 = await adapter.get_price_data(symbol, start_date, end_date, "1d")

        assert data1 is not None, "First call should return data"
        assert data2 is not None, "Second call should return data"

        # Data should be identical (from cache)
        pd.testing.assert_frame_equal(data1, data2)

        # Check cache stats
        cache_stats = adapter.get_cache_stats()
        assert cache_stats['cache_enabled'] is True, "Cache should be enabled"
        assert cache_stats['cache_size'] > 0, "Cache should have entries"


class TestEconomicDataAdapter:
    """Test economic data adapter"""

    @pytest.mark.asyncio
    async def test_get_hibor_data(self):
        """Test getting HIBOR data"""
        adapter = EconomicDataAdapter()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        data = adapter.get_hibor_data(start_date, end_date)

        assert data is not None, "Should get HIBOR data"
        assert not data.empty, "HIBOR data should not be empty"
        assert 'hibor_rate' in data.columns, "Should have hibor_rate column"

    @pytest.mark.asyncio
    async def test_get_gdp_data(self):
        """Test getting GDP data"""
        adapter = EconomicDataAdapter()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        data = adapter.get_gdp_data(start_date, end_date, "quarterly")

        assert data is not None, "Should get GDP data"
        assert not data.empty, "GDP data should not be empty"
        assert 'gdp_growth' in data.columns, "Should have gdp_growth column"

    @pytest.mark.asyncio
    async def test_get_all_economic_data(self):
        """Test getting all economic data"""
        adapter = EconomicDataAdapter()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)

        data = adapter.get_all_economic_data(start_date, end_date)

        assert data is not None, "Should get economic data"
        assert not data.empty, "Economic data should not be empty"

        # Check for multiple indicators
        indicator_columns = [col for col in data.columns if col in [
            'hibor_rate', 'gdp_growth', 'visitor_arrivals',
            'pmi_manufacturing', 'pmi_services', 'unemployment_rate'
        ]]
        assert len(indicator_columns) > 0, "Should have at least one indicator"

    def test_cache_clearing(self):
        """Test cache clearing"""
        adapter = EconomicDataAdapter()

        # Add some data to cache
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        adapter.get_hibor_data(start_date, end_date)
        assert len(adapter.cache) > 0, "Cache should have entries"

        adapter.clear_cache()
        assert len(adapter.cache) == 0, "Cache should be empty after clearing"

    def test_data_summary(self):
        """Test data summary"""
        adapter = EconomicDataAdapter()

        # Add some data to cache
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        adapter.get_hibor_data(start_date, end_date)

        summary = adapter.get_data_summary()
        assert 'cache_size' in summary, "Summary should have cache_size"
        assert 'cached_indicators' in summary, "Summary should have cached_indicators"
        assert summary['cache_size'] > 0, "Cache should have entries"


class TestDataAdapterFactory:
    """Test data adapter factory"""

    @pytest.mark.asyncio
    async def test_create_market_adapter(self):
        """Test creating market adapter through factory"""
        adapter = await DataAdapterFactory.create_adapter(
            DataSourceType.MARKET_DATA,
            DataProvider.YAHOO_FINANCE,
            {'cache_enabled': False}
        )

        assert adapter is not None, "Should create adapter"
        assert hasattr(adapter, 'get_data'), "Adapter should have get_data method"

    @pytest.mark.asyncio
    async def test_create_economic_adapter(self):
        """Test creating economic adapter through factory"""
        adapter = await DataAdapterFactory.create_adapter(
            DataSourceType.ECONOMIC_DATA,
            DataProvider.CSV_FILES
        )

        assert adapter is not None, "Should create adapter"
        assert hasattr(adapter, 'get_data'), "Adapter should have get_data method"

    @pytest.mark.asyncio
    async def test_get_existing_adapter(self):
        """Test getting existing adapter"""
        # Create adapter
        adapter1 = await DataAdapterFactory.create_adapter(
            DataSourceType.MARKET_DATA,
            DataProvider.YAHOO_FINANCE
        )

        # Get same adapter
        adapter2 = DataAdapterFactory.get_adapter(
            DataSourceType.MARKET_DATA,
            DataProvider.YAHOO_FINANCE
        )

        assert adapter1 is adapter2, "Should return same adapter instance"

    @pytest.mark.asyncio
    async def test_list_adapters(self):
        """Test listing adapters"""
        # Create some adapters
        await DataAdapterFactory.create_adapter(
            DataSourceType.MARKET_DATA,
            DataProvider.YAHOO_FINANCE
        )
        await DataAdapterFactory.create_adapter(
            DataSourceType.ECONOMIC_DATA,
            DataProvider.CSV_FILES
        )

        adapters = DataAdapterFactory.list_adapters()
        assert DataSourceType.MARKET_DATA in adapters, "Should have market data adapter"
        assert DataSourceType.ECONOMIC_DATA in adapters, "Should have economic data adapter"

    @pytest.mark.asyncio
    async def test_convenience_functions(self):
        """Test convenience functions"""
        market_adapter = await get_market_data_adapter(
            DataProvider.YAHOO_FINANCE,
            {'cache_enabled': False}
        )
        assert market_adapter is not None, "Should get market adapter"

        economic_adapter = await get_economic_data_adapter()
        assert economic_adapter is not None, "Should get economic adapter"


@pytest.mark.asyncio
async def test_integration_market_and_economic_data():
    """Integration test for market and economic data"""
    # Create adapters
    market_config = MarketDataConfig(
        primary_source="yahoo",
        cache_enabled=False
    )
    market_adapter = MarketDataAdapter(market_config)

    economic_adapter = EconomicDataAdapter()

    # Get market data
    symbol = "HSBC"  # Hong Kong bank, relates to HIBOR
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)

    market_data = await market_adapter.get_price_data(symbol, start_date, end_date, "1d")

    # Get economic data
    hibor_data = economic_adapter.get_hibor_data(start_date, end_date)

    assert market_data is not None, "Should get market data"
    assert hibor_data is not None, "Should get HIBOR data"

    # Both should have data for the time period
    assert not market_data.empty, "Market data should not be empty"
    assert not hibor_data.empty, "HIBOR data should not be empty"

    print(f"✅ Got {len(market_data)} days of market data for {symbol}")
    print(f"✅ Got {len(hibor_data)} days of HIBOR data")


if __name__ == "__main__":
    # Run integration test
    asyncio.run(test_integration_market_and_economic_data())
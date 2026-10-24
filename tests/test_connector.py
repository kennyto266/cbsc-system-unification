"""
Unit tests for CBSCDataConnector.

Tests HTTP client operations with mocked responses using respx.
"""

from datetime import date, datetime

import httpx
import pytest
import respx

from cbsc_strategy_sdk.config import WorkspaceConfig
from cbsc_strategy_sdk.data import CBSCDataConnector, DataCache, OHLCVBar, SymbolInfo
from cbsc_strategy_sdk.exceptions import APIConnectionError, DataFetchError


@pytest.fixture
def config():
    """Provide test configuration."""
    return WorkspaceConfig(
        api_base="http://localhost:3003",
        cache_ttl=300,
        timeout=30
    )


@pytest.fixture
def cache():
    """Provide test cache instance."""
    return DataCache(default_ttl=300)


@pytest.fixture
def mock_ohlcv_response():
    """Provide mock OHLCV API response."""
    return {
        "data": [
            {
                "timestamp": "2024-01-01T00:00:00Z",
                "open": 150.0,
                "high": 155.0,
                "low": 149.0,
                "close": 154.0,
                "volume": 1000000
            },
            {
                "timestamp": "2024-01-02T00:00:00Z",
                "open": 154.0,
                "high": 158.0,
                "low": 153.0,
                "close": 157.0,
                "volume": 1200000
            }
        ]
    }


@pytest.fixture
def mock_symbols_response():
    """Provide mock symbols API response."""
    return {
        "symbols": [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "exchange": "NASDAQ",
                "type": "stock"
            },
            {
                "symbol": "TSLA",
                "name": "Tesla Inc.",
                "exchange": "NASDAQ",
                "type": "stock"
            },
            {
                "symbol": "0700.HK",
                "name": "Tencent Holdings",
                "exchange": "HKEX",
                "type": "stock"
            }
        ]
    }


class TestCBSCDataConnectorInitialization:
    """Test connector initialization."""

    def test_initialization(self, config, cache):
        """Test connector initializes correctly."""
        connector = CBSCDataConnector(
            config=config,
            cache=cache,
            timeout=30
        )
        assert connector._config == config
        assert connector._cache == cache
        assert connector._timeout == 30
        assert connector._client is None

    def test_initialization_with_custom_timeout(self, config, cache):
        """Test connector with custom timeout."""
        connector = CBSCDataConnector(
            config=config,
            cache=cache,
            timeout=60
        )
        assert connector._timeout == 60


class TestCBSCDataConnectorContextManager:
    """Test async context manager behavior."""

    @pytest.mark.asyncio
    async def test_aenter_creates_client(self, config, cache):
        """Test __aenter__ creates httpx client."""
        connector = CBSCDataConnector(config=config, cache=cache)
        async with connector as conn:
            assert conn._client is not None
            assert isinstance(conn._client, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_aexit_closes_client(self, config, cache):
        """Test __aexit__ closes httpx client."""
        connector = CBSCDataConnector(config=config, cache=cache)
        async with connector as conn:
            client = conn._client
        assert connector._client is None

    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self, config, cache):
        """Test context manager properly cleans up."""
        connector = CBSCDataConnector(config=config, cache=cache)
        async with connector:
            pass
        # Client should be closed
        assert connector._client is None


class TestCBSCDataConnectorFetchOHLCV:
    """Test fetch_ohlcv method."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_ohlcv_success(
        self, config, cache, mock_ohlcv_response
    ):
        """Test successful OHLCV data fetch."""
        # Mock API response
        api_url = config.get_api_url("/api/data/stocks")
        route = respx.get(
            f"{api_url}?symbol=AAPL&start=2024-01-01&end=2024-01-31&interval=1d"
        ).mock(return_value=httpx.Response(200, json=mock_ohlcv_response))

        # Create connector and fetch
        connector = CBSCDataConnector(config=config, cache=cache)
        async with connector as conn:
            bars = await conn.fetch_ohlcv(
                symbol="AAPL",
                start=date(2024, 1, 1),
                end=date(2024, 1, 31),
                interval="1d"
            )

        # Verify results
        assert len(bars) == 2
        assert bars[0].symbol == "AAPL"
        assert bars[0].open == 150.0
        assert bars[0].close == 154.0
        assert bars[1].open == 154.0
        assert bars[1].close == 157.0

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_ohlcv_caches_result(
        self, config, cache, mock_ohlcv_response
    ):
        """Test fetch_ohlcv caches results."""
        api_url = config.get_api_url("/api/data/stocks")
        route = respx.get(
            f"{api_url}?symbol=AAPL&start=2024-01-01&end=2024-01-31&interval=1d"
        ).mock(return_value=httpx.Response(200, json=mock_ohlcv_response))

        connector = CBSCDataConnector(config=config, cache=cache)
        async with connector as conn:
            # First call - should hit API
            bars1 = await conn.fetch_ohlcv(
                symbol="AAPL",
                start=date(2024, 1, 1),
                end=date(2024, 1, 31),
                interval="1d"
            )

            # Second call - should use cache
            bars2 = await conn.fetch_ohlcv(
                symbol="AAPL",
                start=date(2024, 1, 1),
                end=date(2024, 1, 31),
                interval="1d"
            )

        # Should only call API once
        assert route.call_count == 1
        assert len(bars1) == len(bars2)

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_ohlcv_api_error(self, config, cache):
        """Test fetch_ohlcv handles API errors."""
        api_url = config.get_api_url("/api/data/stocks")
        respx.get(
            f"{api_url}?symbol=INVALID&start=2024-01-01&end=2024-01-31&interval=1d"
        ).mock(return_value=httpx.Response(404, json={"error": "Symbol not found"}))

        connector = CBSCDataConnector(config=config, cache=cache)
        async with connector as conn:
            with pytest.raises(APIConnectionError):
                await conn.fetch_ohlcv(
                    symbol="INVALID",
                    start=date(2024, 1, 1),
                    end=date(2024, 1, 31),
                    interval="1d"
                )

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_ohlcv_network_error(self, config, cache):
        """Test fetch_ohlcv handles network errors."""
        api_url = config.get_api_url("/api/data/stocks")
        respx.get(
            f"{api_url}?symbol=AAPL&start=2024-01-01&end=2024-01-31&interval=1d"
        ).mock(side_effect=httpx.ConnectError("Connection refused"))

        connector = CBSCDataConnector(config=config, cache=cache)
        async with connector as conn:
            with pytest.raises(APIConnectionError):
                await conn.fetch_ohlcv(
                    symbol="AAPL",
                    start=date(2024, 1, 1),
                    end=date(2024, 1, 31),
                    interval="1d"
                )

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_ohlcv_invalid_response_format(
        self, config, cache
    ):
        """Test fetch_ohlcv handles invalid response format."""
        api_url = config.get_api_url("/api/data/stocks")
        respx.get(
            f"{api_url}?symbol=AAPL&start=2024-01-01&end=2024-01-31&interval=1d"
        ).mock(return_value=httpx.Response(200, json={"invalid": "response"}))

        connector = CBSCDataConnector(config=config, cache=cache)
        async with connector as conn:
            with pytest.raises(DataFetchError):
                await conn.fetch_ohlcv(
                    symbol="AAPL",
                    start=date(2024, 1, 1),
                    end=date(2024, 1, 31),
                    interval="1d"
                )

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_ohlcv_malformed_data(
        self, config, cache
    ):
        """Test fetch_ohlcv handles malformed data."""
        api_url = config.get_api_url("/api/data/stocks")
        respx.get(
            f"{api_url}?symbol=AAPL&start=2024-01-01&end=2024-01-31&interval=1d"
        ).mock(return_value=httpx.Response(200, json={
            "data": [
                {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "open": "invalid",  # Should be number
                    "high": 155.0,
                    "low": 149.0,
                    "close": 154.0,
                    "volume": 1000000
                }
            ]
        }))

        connector = CBSCDataConnector(config=config, cache=cache)
        async with connector as conn:
            with pytest.raises(DataFetchError):
                await conn.fetch_ohlcv(
                    symbol="AAPL",
                    start=date(2024, 1, 1),
                    end=date(2024, 1, 31),
                    interval="1d"
                )

    @pytest.mark.asyncio
    async def test_fetch_ohlcv_without_initialization(self, config, cache):
        """Test fetch_ohlcv fails without initialization."""
        connector = CBSCDataConnector(config=config, cache=cache)
        # Don't use context manager, so client is None
        with pytest.raises(APIConnectionError):
            await connector.fetch_ohlcv(
                symbol="AAPL",
                start=date(2024, 1, 1),
                end=date(2024, 1, 31)
            )


class TestCBSCDataConnectorFetchSymbols:
    """Test fetch_symbols method."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_symbols_success(
        self, config, cache, mock_symbols_response
    ):
        """Test successful symbols fetch."""
        api_url = config.get_api_url("/api/data/symbols")
        route = respx.get(api_url).mock(
            return_value=httpx.Response(200, json=mock_symbols_response)
        )

        connector = CBSCDataConnector(config=config, cache=cache)
        async with connector as conn:
            symbols = await conn.fetch_symbols()

        # Verify results
        assert len(symbols) == 3
        assert symbols[0].symbol == "AAPL"
        assert symbols[0].name == "Apple Inc."
        assert symbols[0].exchange == "NASDAQ"
        assert symbols[1].symbol == "TSLA"
        assert symbols[2].symbol == "0700.HK"

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_symbols_caches_result(
        self, config, cache, mock_symbols_response
    ):
        """Test fetch_symbols caches results."""
        api_url = config.get_api_url("/api/data/symbols")
        route = respx.get(api_url).mock(
            return_value=httpx.Response(200, json=mock_symbols_response)
        )

        connector = CBSCDataConnector(config=config, cache=cache)
        async with connector as conn:
            # First call
            symbols1 = await conn.fetch_symbols()
            # Second call - should use cache
            symbols2 = await conn.fetch_symbols()

        # Should only call API once
        assert route.call_count == 1
        assert len(symbols1) == len(symbols2)

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_symbols_api_error(self, config, cache):
        """Test fetch_symbols handles API errors."""
        api_url = config.get_api_url("/api/data/symbols")
        respx.get(api_url).mock(
            return_value=httpx.Response(500, json={"error": "Internal server error"})
        )

        connector = CBSCDataConnector(config=config, cache=cache)
        async with connector as conn:
            with pytest.raises(APIConnectionError):
                await conn.fetch_symbols()

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_symbols_invalid_response_format(
        self, config, cache
    ):
        """Test fetch_symbols handles invalid response format."""
        api_url = config.get_api_url("/api/data/symbols")
        respx.get(api_url).mock(
            return_value=httpx.Response(200, json={"invalid": "response"})
        )

        connector = CBSCDataConnector(config=config, cache=cache)
        async with connector as conn:
            with pytest.raises(DataFetchError):
                await conn.fetch_symbols()

    @pytest.mark.asyncio
    async def test_fetch_symbols_without_initialization(self, config, cache):
        """Test fetch_symbols fails without initialization."""
        connector = CBSCDataConnector(config=config, cache=cache)
        with pytest.raises(APIConnectionError):
            await connector.fetch_symbols()


class TestCBSCDataConnectorCacheInvalidation:
    """Test cache invalidation methods."""

    def test_invalidate_symbol_cache(self, config, cache):
        """Test invalidating cache for specific symbol."""
        connector = CBSCDataConnector(config=config, cache=cache)

        # Add cached data
        cache.set("ohlcv:AAPL:2024-01-01:2024-01-31:1d", "data1")
        cache.set("ohlcv:TSLA:2024-01-01:2024-01-31:1d", "data2")

        # Invalidate AAPL cache
        connector.invalidate_symbol_cache("AAPL")

        assert cache.get("ohlcv:AAPL:2024-01-01:2024-01-31:1d") is None
        assert cache.get("ohlcv:TSLA:2024-01-01:2024-01-31:1d") == "data2"

    def test_invalidate_symbols_cache(self, config, cache):
        """Test invalidating symbols list cache."""
        connector = CBSCDataConnector(config=config, cache=cache)

        # Add cached symbols
        cache.set("symbols:all", ["AAPL", "TSLA"])

        # Invalidate symbols cache
        connector.invalidate_symbols_cache()

        assert cache.get("symbols:all") is None


class TestCBSCDataConnectorEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_ohlcv_empty_response(self, config, cache):
        """Test fetch_ohlcv with empty data array."""
        api_url = config.get_api_url("/api/data/stocks")
        respx.get(
            f"{api_url}?symbol=AAPL&start=2024-01-01&end=2024-01-31&interval=1d"
        ).mock(return_value=httpx.Response(200, json={"data": []}))

        connector = CBSCDataConnector(config=config, cache=cache)
        async with connector as conn:
            bars = await conn.fetch_ohlcv(
                symbol="AAPL",
                start=date(2024, 1, 1),
                end=date(2024, 1, 31),
                interval="1d"
            )

        assert len(bars) == 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_symbols_empty_response(self, config, cache):
        """Test fetch_symbols with empty symbols array."""
        api_url = config.get_api_url("/api/data/symbols")
        respx.get(api_url).mock(
            return_value=httpx.Response(200, json={"symbols": []})
        )

        connector = CBSCDataConnector(config=config, cache=cache)
        async with connector as conn:
            symbols = await conn.fetch_symbols()

        assert len(symbols) == 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_ohlcv_missing_volume_field(
        self, config, cache
    ):
        """Test fetch_ohlcv handles missing volume field."""
        api_url = config.get_api_url("/api/data/stocks")
        respx.get(
            f"{api_url}?symbol=AAPL&start=2024-01-01&end=2024-01-31&interval=1d"
        ).mock(return_value=httpx.Response(200, json={
            "data": [
                {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "open": 150.0,
                    "high": 155.0,
                    "low": 149.0,
                    "close": 154.0
                    # volume field missing
                }
            ]
        }))

        connector = CBSCDataConnector(config=config, cache=cache)
        async with connector as conn:
            bars = await conn.fetch_ohlcv(
                symbol="AAPL",
                start=date(2024, 1, 1),
                end=date(2024, 1, 31),
                interval="1d"
            )

        # Should default to 0
        assert len(bars) == 1
        assert bars[0].volume == 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_symbols_missing_optional_fields(
        self, config, cache
    ):
        """Test fetch_symbols handles missing optional fields."""
        api_url = config.get_api_url("/api/data/symbols")
        respx.get(api_url).mock(return_value=httpx.Response(200, json={
            "symbols": [
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc."
                    # exchange and type missing
                }
            ]
        }))

        connector = CBSCDataConnector(config=config, cache=cache)
        async with connector as conn:
            symbols = await conn.fetch_symbols()

        assert len(symbols) == 1
        assert symbols[0].symbol == "AAPL"
        assert symbols[0].exchange == "UNKNOWN"  # Default value
        assert symbols[0].type == "stock"  # Default value

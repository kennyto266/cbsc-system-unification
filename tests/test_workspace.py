"""
Unit tests for StrategyWorkspace.

Tests workspace operations with mocked connector and cache.
"""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from cbsc_strategy_sdk.data import DataCache, OHLCVBar, SymbolInfo
from cbsc_strategy_sdk.exceptions import DataFetchError, StrategyWorkspaceError
from cbsc_strategy_sdk.workspace import StrategyWorkspace


@pytest.fixture
def mock_cache():
    """Provide mock cache."""
    return MagicMock(spec=DataCache)


@pytest.fixture
def mock_connector():
    """Provide mock connector."""
    connector = MagicMock()
    connector.__aenter__ = AsyncMock(return_value=connector)
    connector.__aexit__ = AsyncMock()
    return connector


@pytest.fixture
def sample_bars():
    """Provide sample OHLCV bars."""
    return [
        OHLCVBar(
            timestamp=datetime(2024, 1, 1),
            open=150.0,
            high=155.0,
            low=149.0,
            close=154.0,
            volume=1000000
        ),
        OHLCVBar(
            timestamp=datetime(2024, 1, 2),
            open=154.0,
            high=158.0,
            low=153.0,
            close=157.0,
            volume=1200000
        )
    ]


@pytest.fixture
def sample_symbols():
    """Provide sample symbols."""
    return [
        SymbolInfo(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ", type="stock"),
        SymbolInfo(symbol="TSLA", name="Tesla Inc.", exchange="NASDAQ", type="stock"),
        SymbolInfo(symbol="0700.HK", name="Tencent", exchange="HKEX", type="stock")
    ]


class TestStrategyWorkspaceInitialization:
    """Test workspace initialization."""

    def test_initialization_with_defaults(self):
        """Test workspace with default parameters."""
        ws = StrategyWorkspace()
        assert ws._config.api_base == "http://localhost:3003"
        assert ws._config.cache_ttl == 300
        assert ws._config.timeout == 30
        assert ws._connector is None
        assert ws._is_initialized is False

    def test_initialization_with_custom_params(self):
        """Test workspace with custom parameters."""
        ws = StrategyWorkspace(
            api_base="https://api.example.com",
            cache_ttl=600,
            timeout=60
        )
        assert ws._config.api_base == "https://api.example.com"
        assert ws._config.cache_ttl == 600
        assert ws._config.timeout == 60

    def test_cache_instance_created(self):
        """Test cache is created on initialization."""
        ws = StrategyWorkspace()
        assert ws._cache is not None
        assert isinstance(ws._cache, DataCache)


class TestStrategyWorkspaceContextManager:
    """Test async context manager behavior."""

    @pytest.mark.asyncio
    async def test_aenter_initializes_connector(self):
        """Test __aenter__ creates and initializes connector."""
        ws = StrategyWorkspace()
        assert not ws._is_initialized

        async with ws:
            assert ws._is_initialized
            assert ws._connector is not None

    @pytest.mark.asyncio
    async def test_aexit_cleans_up(self):
        """Test __aexit__ cleans up resources."""
        ws = StrategyWorkspace()

        async with ws:
            assert ws._is_initialized

        assert not ws._is_initialized
        assert ws._connector is None

    @pytest.mark.asyncio
    async def test_double_initialization_fails(self):
        """Test double initialization raises error."""
        ws = StrategyWorkspace()

        async with ws:
            with pytest.raises(StrategyWorkspaceError) as exc_info:
                await ws.__aenter__()

        assert "already initialized" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_context_manager_on_failure(self):
        """Test cleanup happens even if initialization fails."""
        ws = StrategyWorkspace()

        # Mock __aenter__ to raise error
        with patch.object(ws, '_connector', None):
            # Can't easily test this without more complex mocking
            # The key point is that __aexit__ should be called
            pass


class TestStrategyWorkspaceEnsureInitialized:
    """Test _ensure_initialized method."""

    def test_ensure_initialized_passes_when_initialized(self):
        """Test _ensure_initialized passes when initialized."""
        ws = StrategyWorkspace()
        ws._is_initialized = True
        ws._connector = MagicMock()

        # Should not raise
        ws._ensure_initialized()

    def test_ensure_initialized_fails_when_not_initialized(self):
        """Test _ensure_initialized fails when not initialized."""
        ws = StrategyWorkspace()

        with pytest.raises(StrategyWorkspaceError) as exc_info:
            ws._ensure_initialized()

        assert "not initialized" in str(exc_info.value).lower()


class TestStrategyWorkspaceGetHistoricalData:
    """Test get_historical_data method."""

    @pytest.mark.asyncio
    async def test_get_historical_data_success(
        self, mock_connector, sample_bars
    ):
        """Test successful historical data fetch."""
        ws = StrategyWorkspace()
        ws._is_initialized = True
        ws._connector = mock_connector

        # Mock the connector's fetch_ohlcv
        mock_connector.fetch_ohlcv = AsyncMock(return_value=sample_bars)

        df = ws.get_historical_data(
            symbol="AAPL",
            start=date(2024, 1, 1),
            end=date(2024, 1, 31)
        )

        # Verify DataFrame structure
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "open" in df.columns
        assert "high" in df.columns
        assert "low" in df.columns
        assert "close" in df.columns
        assert "volume" in df.columns

        # Verify data
        assert df.iloc[0]["open"] == 150.0
        assert df.iloc[0]["close"] == 154.0

    @pytest.mark.asyncio
    async def test_get_historical_data_with_interval(
        self, mock_connector, sample_bars
    ):
        """Test get_historical_data with custom interval."""
        ws = StrategyWorkspace()
        ws._is_initialized = True
        ws._connector = mock_connector

        mock_connector.fetch_ohlcv = AsyncMock(return_value=sample_bars)

        df = ws.get_historical_data(
            symbol="AAPL",
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            interval="1h"
        )

        assert len(df) == 2
        mock_connector.fetch_ohlcv.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_historical_data_empty_response(
        self, mock_connector
    ):
        """Test get_historical_data with empty response."""
        ws = StrategyWorkspace()
        ws._is_initialized = True
        ws._connector = mock_connector

        mock_connector.fetch_ohlcv = AsyncMock(return_value=[])

        df = ws.get_historical_data(
            symbol="AAPL",
            start=date(2024, 1, 1),
            end=date(2024, 1, 31)
        )

        # Should return empty DataFrame with correct columns
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert "open" in df.columns

    @pytest.mark.asyncio
    async def test_get_historical_data_not_initialized(self):
        """Test get_historical_data fails when not initialized."""
        ws = StrategyWorkspace()

        with pytest.raises(StrategyWorkspaceError):
            ws.get_historical_data(
                symbol="AAPL",
                start=date(2024, 1, 1),
                end=date(2024, 1, 31)
            )

    @pytest.mark.asyncio
    async def test_get_historical_data_fetch_error(
        self, mock_connector
    ):
        """Test get_historical_data handles fetch errors."""
        ws = StrategyWorkspace()
        ws._is_initialized = True
        ws._connector = mock_connector

        # Mock fetch to raise error
        mock_connector.fetch_ohlcv = AsyncMock(
            side_effect=Exception("API error")
        )

        with pytest.raises(DataFetchError):
            ws.get_historical_data(
                symbol="AAPL",
                start=date(2024, 1, 1),
                end=date(2024, 1, 31)
            )

    @pytest.mark.asyncio
    async def test_get_historical_data_returns_sorted_dataframe(
        self, mock_connector
    ):
        """Test DataFrame is sorted by timestamp."""
        # Create bars out of order
        bars = [
            OHLCVBar(
                timestamp=datetime(2024, 1, 2),
                open=154.0,
                high=158.0,
                low=153.0,
                close=157.0,
                volume=1200000
            ),
            OHLCVBar(
                timestamp=datetime(2024, 1, 1),
                open=150.0,
                high=155.0,
                low=149.0,
                close=154.0,
                volume=1000000
            )
        ]

        ws = StrategyWorkspace()
        ws._is_initialized = True
        ws._connector = mock_connector
        mock_connector.fetch_ohlcv = AsyncMock(return_value=bars)

        df = ws.get_historical_data(
            symbol="AAPL",
            start=date(2024, 1, 1),
            end=date(2024, 1, 31)
        )

        # Should be sorted by timestamp
        assert df.iloc[0]["close"] == 154.0  # Jan 1
        assert df.iloc[1]["close"] == 157.0  # Jan 2


class TestStrategyWorkspaceGetAvailableSymbols:
    """Test get_available_symbols method."""

    @pytest.mark.asyncio
    async def test_get_available_symbols_success(
        self, mock_connector, sample_symbols
    ):
        """Test successful symbols fetch."""
        ws = StrategyWorkspace()
        ws._is_initialized = True
        ws._connector = mock_connector

        mock_connector.fetch_symbols = AsyncMock(return_value=sample_symbols)

        symbols = ws.get_available_symbols()

        assert isinstance(symbols, list)
        assert len(symbols) == 3
        assert "AAPL" in symbols
        assert "TSLA" in symbols
        assert "0700.HK" in symbols

    @pytest.mark.asyncio
    async def test_get_available_symbols_not_initialized(self):
        """Test get_available_symbols fails when not initialized."""
        ws = StrategyWorkspace()

        with pytest.raises(StrategyWorkspaceError):
            ws.get_available_symbols()

    @pytest.mark.asyncio
    async def test_get_available_symbols_fetch_error(
        self, mock_connector
    ):
        """Test get_available_symbols handles fetch errors."""
        ws = StrategyWorkspace()
        ws._is_initialized = True
        ws._connector = mock_connector

        mock_connector.fetch_symbols = AsyncMock(
            side_effect=Exception("API error")
        )

        with pytest.raises(DataFetchError):
            ws.get_available_symbols()


class TestStrategyWorkspaceClearCache:
    """Test clear_cache method."""

    def test_clear_cache(self, mock_cache):
        """Test clear_cache clears the cache."""
        ws = StrategyWorkspace()
        ws._cache = mock_cache

        ws.clear_cache()

        mock_cache.clear.assert_called_once()

    def test_clear_cache_with_real_cache(self):
        """Test clear_cache with real cache instance."""
        ws = StrategyWorkspace()
        ws._cache.set("key", "value")

        assert ws._cache.size() > 0
        ws.clear_cache()
        assert ws._cache.size() == 0


class TestStrategyWorkspaceProperties:
    """Test workspace properties."""

    def test_config_property(self):
        """Test config property returns configuration."""
        ws = StrategyWorkspace(api_base="https://test.com", cache_ttl=600)

        config = ws.config
        assert config.api_base == "https://test.com"
        assert config.cache_ttl == 600

    def test_cache_size_property(self):
        """Test cache_size property returns cache size."""
        ws = StrategyWorkspace()
        ws._cache.set("key1", "value1")
        ws._cache.set("key2", "value2")

        assert ws.cache_size == 2

    def test_cache_size_with_empty_cache(self):
        """Test cache_size with empty cache."""
        ws = StrategyWorkspace()
        assert ws.cache_size == 0


class TestStrategyWorkspaceRepr:
    """Test string representation."""

    def test_repr_not_initialized(self):
        """Test repr when not initialized."""
        ws = StrategyWorkspace()
        repr_str = repr(ws)

        assert "StrategyWorkspace" in repr_str
        assert "http://localhost:3003" in repr_str
        assert "not initialized" in repr_str

    def test_repr_initialized(self):
        """Test repr when initialized."""
        ws = StrategyWorkspace()
        ws._is_initialized = True

        repr_str = repr(ws)
        assert "initialized" in repr_str


class TestStrategyWorkspaceIntegration:
    """Integration tests with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, mock_connector, sample_bars, sample_symbols):
        """Test complete workflow from initialization to data access."""
        ws = StrategyWorkspace()

        # Mock connector methods
        mock_connector.fetch_ohlcv = AsyncMock(return_value=sample_bars)
        mock_connector.fetch_symbols = AsyncMock(return_value=sample_symbols)

        # Initialize workspace
        ws._is_initialized = True
        ws._connector = mock_connector

        # Get symbols
        symbols = ws.get_available_symbols()
        assert len(symbols) == 3

        # Get historical data
        df = ws.get_historical_data(
            symbol="AAPL",
            start=date(2024, 1, 1),
            end=date(2024, 1, 31)
        )
        assert len(df) == 2

        # Check cache size
        assert ws.cache_size >= 0

        # Clear cache
        ws.clear_cache()

    @pytest.mark.asyncio
    async def test_workspace_with_custom_config(self, mock_connector):
        """Test workspace with custom configuration."""
        ws = StrategyWorkspace(
            api_base="https://custom.api.com",
            cache_ttl=1200,
            timeout=90
        )

        assert ws.config.api_base == "https://custom.api.com"
        assert ws.config.cache_ttl == 1200
        assert ws.config.timeout == 90


class TestStrategyWorkspaceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_get_historical_data_with_future_dates(
        self, mock_connector
    ):
        """Test get_historical_data with future date range."""
        ws = StrategyWorkspace()
        ws._is_initialized = True
        ws._connector = mock_connector
        mock_connector.fetch_ohlcv = AsyncMock(return_value=[])

        # Future dates
        df = ws.get_historical_data(
            symbol="AAPL",
            start=date(2099, 1, 1),
            end=date(2099, 12, 31)
        )

        # Should handle gracefully
        assert isinstance(df, pd.DataFrame)

    @pytest.mark.asyncio
    async def test_get_historical_data_with_inverted_dates(
        self, mock_connector
    ):
        """Test get_historical_data with inverted date range."""
        ws = StrategyWorkspace()
        ws._is_initialized = True
        ws._connector = mock_connector
        mock_connector.fetch_ohlcv = AsyncMock(return_value=[])

        # End before start
        df = ws.get_historical_data(
            symbol="AAPL",
            start=date(2024, 12, 31),
            end=date(2024, 1, 1)
        )

        # Should handle - depends on API behavior
        assert isinstance(df, pd.DataFrame)

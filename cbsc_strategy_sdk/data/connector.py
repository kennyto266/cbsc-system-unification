"""HTTP client for CBSC backend API.

Provides async methods for fetching market data and symbols.
"""

from datetime import date
from typing import Any

import httpx

# Import from parent modules (will be created by Stream A)
from ..config import WorkspaceConfig
from ..exceptions import APIConnectionError, DataFetchError
from .cache import DataCache
from .models import OHLCVBar, SymbolInfo


class CBSCDataConnector:
    """HTTP client for CBSC backend API.

    Provides async methods for fetching market data with caching support.

    Attributes:
        _config: Workspace configuration
        _client: httpx async client
        _cache: In-memory data cache
    """

    def __init__(
        self,
        config: WorkspaceConfig,
        cache: DataCache,
        timeout: int = 30,
    ) -> None:
        """Initialize data connector.

        Args:
            config: Workspace configuration
            cache: Data cache instance
            timeout: Request timeout in seconds
        """
        self._config = config
        self._cache = cache
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "CBSCDataConnector":
        """Enter async context, create HTTP client.

        Returns:
            Self for context manager usage
        """
        self._client = httpx.AsyncClient(
            base_url=self._config.api_base,
            timeout=self._timeout,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context, close HTTP client."""
        if self._client:
            await self._client.aclose()

    async def fetch_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str = "1d",
    ) -> list[OHLCVBar]:
        """Fetch OHLCV data for a symbol.

        Args:
            symbol: Trading symbol
            start: Start date
            end: End date
            interval: Data interval (1d, 1h, 5m, etc.)

        Returns:
            List of OHLCV bars

        Raises:
            APIConnectionError: If API request fails
            DataFetchError: If data parsing fails
        """
        if not self._client:
            raise APIConnectionError("Client not initialized. Use async context manager.")

        # Check cache first
        cache_key = f"ohlcv:{symbol}:{start}:{end}:{interval}"
        cached_data = self._cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        # Fetch from API
        try:
            response = await self._client.get(
                "/api/data/stocks",
                params={
                    "symbol": symbol,
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "interval": interval,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise APIConnectionError(f"Failed to fetch OHLCV data: {e}") from e

        # Parse response
        try:
            data = response.json()
            if not isinstance(data, dict) or "data" not in data:
                raise DataFetchError("Invalid response format from API")

            bars = []
            for bar_data in data["data"]:
                bars.append(
                    OHLCVBar(
                        timestamp=bar_data["timestamp"],
                        open=bar_data["open"],
                        high=bar_data["high"],
                        low=bar_data["low"],
                        close=bar_data["close"],
                        volume=bar_data.get("volume", 0),
                    )
                )

            # Cache the result (default TTL: 5 minutes)
            self._cache.set(cache_key, bars, ttl=300)

            return bars

        except (KeyError, ValueError, TypeError) as e:
            raise DataFetchError(f"Failed to parse OHLCV data: {e}") from e

    async def fetch_symbols(self) -> list[SymbolInfo]:
        """Fetch list of available trading symbols.

        Returns:
            List of symbol information

        Raises:
            APIConnectionError: If API request fails
            DataFetchError: If data parsing fails
        """
        if not self._client:
            raise APIConnectionError("Client not initialized. Use async context manager.")

        # Check cache first
        cache_key = "symbols:all"
        cached_data = self._cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        # Fetch from API
        try:
            response = await self._client.get("/api/data/symbols")
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise APIConnectionError(f"Failed to fetch symbols: {e}") from e

        # Parse response
        try:
            data = response.json()
            if not isinstance(data, dict) or "symbols" not in data:
                raise DataFetchError("Invalid response format from API")

            symbols = []
            for symbol_data in data["symbols"]:
                symbols.append(
                    SymbolInfo(
                        symbol=symbol_data["symbol"],
                        name=symbol_data["name"],
                        exchange=symbol_data.get("exchange", "UNKNOWN"),
                        type=symbol_data.get("type", "stock"),
                    )
                )

            # Cache the result (default TTL: 1 hour)
            self._cache.set(cache_key, symbols, ttl=3600)

            return symbols

        except (KeyError, ValueError, TypeError) as e:
            raise DataFetchError(f"Failed to parse symbols data: {e}") from e

    def invalidate_symbol_cache(self, symbol: str) -> None:
        """Invalidate cached data for a specific symbol.

        Args:
            symbol: Symbol to invalidate
        """
        self._cache.invalidate(f"ohlcv:{symbol}:.*")

    def invalidate_symbols_cache(self) -> None:
        """Invalidate cached symbols list."""
        self._cache.invalidate("symbols:.*")

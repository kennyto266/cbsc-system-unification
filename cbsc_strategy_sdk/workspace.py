"""StrategyWorkspace main class for CBSC Strategy SDK.

This module provides the main workspace interface for strategy development,
integrating data access, caching, and session management for Jupyter notebooks.
"""

from datetime import date
from typing import Optional

import pandas as pd

from .config import WorkspaceConfig, create_config
from .data import CBSCDataConnector, DataCache, OHLCVBar, SymbolInfo
from .exceptions import StrategyWorkspaceError


class StrategyWorkspace:
    """Main workspace for strategy development in Jupyter notebooks.

    This class provides a unified interface for accessing market data,
    managing workspace state, and integrating with the CBSC backend API.

    The workspace should be used as an async context manager to ensure
    proper resource initialization and cleanup.

    Attributes:
        _config: Workspace configuration
        _connector: Data connector for API access
        _cache: In-memory data cache

    Example:
        >>> from cbsc_strategy_sdk import StrategyWorkspace
        >>> from datetime import date
        >>>
        >>> async with StrategyWorkspace() as ws:
        ...     # Fetch historical data
        ...     data = ws.get_historical_data(
        ...         symbol="AAPL",
        ...         start=date(2024, 1, 1),
        ...         end=date(2024, 12, 31)
        ...     )
        ...     print(data.head())
        >>>
        >>> # Workspace automatically closed after context exit
    """

    def __init__(
        self,
        api_base: str = "http://localhost:3003",
        cache_ttl: int = 300,
        timeout: int = 30,
    ) -> None:
        """Initialize StrategyWorkspace.

        Args:
            api_base: Base URL for CBSC backend API
            cache_ttl: Cache time-to-live in seconds
            timeout: HTTP request timeout in seconds
        """
        self._config: WorkspaceConfig = create_config(
            api_base=api_base,
            cache_ttl=cache_ttl,
            timeout=timeout,
        )
        self._cache: DataCache = DataCache(default_ttl=cache_ttl)
        self._connector: Optional[CBSCDataConnector] = None
        self._is_initialized: bool = False

    async def __aenter__(self) -> "StrategyWorkspace":
        """Enter async context, initialize connector.

        Creates and initializes the data connector with HTTP client.

        Returns:
            Self for context manager usage

        Raises:
            StrategyWorkspaceError: If initialization fails
        """
        if self._is_initialized:
            raise StrategyWorkspaceError("Workspace is already initialized")

        try:
            # Create connector instance
            self._connector = CBSCDataConnector(
                config=self._config,
                cache=self._cache,
                timeout=self._config.timeout,
            )

            # Initialize connector (creates HTTP client)
            await self._connector.__aenter__()

            self._is_initialized = True
            return self

        except Exception as e:
            # Clean up on failure
            if self._connector:
                await self._connector.__aexit__(None, None, None)
                self._connector = None
            self._is_initialized = False

            raise StrategyWorkspaceError(
                f"Failed to initialize workspace: {e}",
                details={"api_base": self._config.api_base},
            ) from e

    async def __aexit__(self, *args) -> None:
        """Exit async context, cleanup resources.

        Closes the HTTP client and releases resources.
        """
        if self._connector:
            await self._connector.__aexit__(*args)
            self._connector = None
        self._is_initialized = False

    def _ensure_initialized(self) -> None:
        """Check if workspace is initialized.

        Raises:
            StrategyWorkspaceError: If workspace not initialized
        """
        if not self._is_initialized or self._connector is None:
            raise StrategyWorkspaceError(
                "Workspace not initialized. Use 'async with StrategyWorkspace() as ws:'"
            )

    def get_historical_data(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Retrieve OHLCV historical data for a symbol.

        This method fetches market data from the CBSC backend API,
        utilizing the built-in cache for improved performance on
        repeated requests.

        Args:
            symbol: Trading symbol (e.g., 'AAPL', '0700.HK')
            start: Start date (inclusive)
            end: End date (inclusive)
            interval: Data interval ('1d', '1h', '5m', etc.)

        Returns:
            pandas DataFrame with columns:
            - timestamp: Datetime index
            - open: Opening price
            - high: Highest price
            - low: Lowest price
            - close: Closing price
            - volume: Trading volume

        Raises:
            StrategyWorkspaceError: If workspace not initialized
            DataFetchError: If data fetch fails

        Example:
            >>> from datetime import date
            >>> data = ws.get_historical_data(
            ...     symbol="AAPL",
            ...     start=date(2024, 1, 1),
            ...     end=date(2024, 1, 31)
            ... )
            >>> print(data.head())
        """
        self._ensure_initialized()

        # Note: This is a sync wrapper around async connector method
        # In production with asyncio running, you'd typically use the async API directly
        # For notebook convenience, we'll need to handle async execution
        import asyncio

        try:
            # Try to get running loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context (like Jupyter with tornado)
                    # Need to use nest_asyncio or run in separate thread
                    import nest_asyncio
                    nest_asyncio.apply()
                    bars = asyncio.run(
                        self._connector.fetch_ohlcv(symbol, start, end, interval)
                    )
                else:
                    # No loop running, can use run
                    bars = asyncio.run(
                        self._connector.fetch_ohlcv(symbol, start, end, interval)
                    )
            except RuntimeError:
                # No event loop, create new one
                bars = asyncio.run(
                    self._connector.fetch_ohlcv(symbol, start, end, interval)
                )

        except Exception as e:
            from .exceptions import DataFetchError
            raise DataFetchError(
                f"Failed to fetch historical data for {symbol}: {e}",
                symbol=symbol,
            ) from e

        # Convert to pandas DataFrame
        if not bars:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        data = {
            "timestamp": [bar.timestamp for bar in bars],
            "open": [bar.open for bar in bars],
            "high": [bar.high for bar in bars],
            "low": [bar.low for bar in bars],
            "close": [bar.close for bar in bars],
            "volume": [bar.volume for bar in bars],
        }

        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)

        return df

    def get_available_symbols(self) -> list[str]:
        """List all available trading symbols.

        Retrieves the complete list of tradable symbols from the CBSC backend,
        utilizing the cache to avoid repeated API calls.

        Returns:
            List of symbol strings (e.g., ['AAPL', '0700.HK', 'TSLA'])

        Raises:
            StrategyWorkspaceError: If workspace not initialized
            DataFetchError: If symbols fetch fails

        Example:
            >>> symbols = ws.get_available_symbols()
            >>> print(f"Available symbols: {len(symbols)}")
            >>> print(symbols[:5])
        """
        self._ensure_initialized()

        import asyncio

        try:
            # Try to get running loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
                    symbols = asyncio.run(self._connector.fetch_symbols())
                else:
                    symbols = asyncio.run(self._connector.fetch_symbols())
            except RuntimeError:
                symbols = asyncio.run(self._connector.fetch_symbols())

        except Exception as e:
            from .exceptions import DataFetchError
            raise DataFetchError(f"Failed to fetch available symbols: {e}") from e

        return [s.symbol for s in symbols]

    def clear_cache(self) -> None:
        """Clear all cached data.

        Removes all entries from the in-memory cache, forcing subsequent
        data requests to fetch fresh data from the API.

        Example:
            >>> ws.clear_cache()
            >>> # Next data fetch will hit the API
            >>> data = ws.get_historical_data("AAPL", start, end)
        """
        self._cache.clear()

    @property
    def config(self) -> WorkspaceConfig:
        """Get the workspace configuration.

        Returns:
            Current workspace configuration

        Example:
            >>> print(ws.config.api_base)
            >>> print(ws.config.cache_ttl)
        """
        return self._config

    @property
    def cache_size(self) -> int:
        """Get the current cache size.

        Returns:
            Number of entries currently cached

        Example:
            >>> print(f"Cache contains {ws.cache_size} entries")
        """
        return self._cache.size()

    def __repr__(self) -> str:
        """Return string representation of workspace."""
        status = "initialized" if self._is_initialized else "not initialized"
        return f"StrategyWorkspace(api_base='{self._config.api_base}', {status})"

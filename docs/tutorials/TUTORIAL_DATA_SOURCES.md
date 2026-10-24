# Tutorial: Integrating Custom Data Sources

Learn how to integrate custom data sources with the CBSC Strategy SDK. This tutorial covers connecting to external APIs, databases, and file-based data sources.

## Overview

The CBSC SDK provides a flexible data connector architecture that allows you to integrate custom data sources beyond the default CBSC backend API.

## Prerequisites

- Completed [Quick Start Guide](../QUICKSTART.md)
- Understanding of async/await patterns in Python
- Basic knowledge of APIs and databases

## Data Connector Architecture

### Base Data Connector

All data sources implement the following interface:

```python
from abc import ABC, abstractmethod
from typing import List
from datetime import date
import pandas as pd

class CustomDataSource(ABC):
    """Abstract base class for custom data sources."""

    @abstractmethod
    async def fetch_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for a symbol.

        Args:
            symbol: Trading symbol
            start: Start date
            end: End date
            interval: Data interval

        Returns:
            DataFrame with columns: [open, high, low, close, volume]
        """
        pass

    @abstractmethod
    async def get_available_symbols(self) -> List[str]:
        """Get list of available symbols."""
        pass
```

## Example 1: CSV File Data Source

Load market data from CSV files:

```python
import pandas as pd
from pathlib import Path
from typing import List
from datetime import date

class CSVDataSource(CustomDataSource):
    """Data source that reads from CSV files."""

    def __init__(self, data_directory: str):
        """
        Initialize CSV data source.

        Args:
            data_directory: Path to directory containing CSV files
        """
        self.data_dir = Path(data_directory)
        if not self.data_dir.exists():
            raise ValueError(f"Directory not found: {data_directory}")

    async def fetch_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Fetch data from CSV file."""
        # Construct file path
        csv_file = self.data_dir / f"{symbol}.csv"

        if not csv_file.exists():
            raise FileNotFoundError(f"Data file not found: {csv_file}")

        # Read CSV
        df = pd.read_csv(csv_file, index_col="date", parse_dates=True)

        # Filter by date range
        df = df.loc[start:end]

        # Ensure required columns
        required_cols = ["open", "high", "low", "close", "volume"]
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")

        return df[required_cols]

    async def get_available_symbols(self) -> List[str]:
        """Get list of symbols from CSV files."""
        csv_files = list(self.data_dir.glob("*.csv"))
        symbols = [f.stem for f in csv_files]
        return symbols

# Usage
csv_source = CSVDataSource("path/to/data/directory")

async with csv_source:
    data = await csv_source.fetch_ohlcv(
        symbol="AAPL",
        start=date(2024, 1, 1),
        end=date(2024, 12, 31)
    )
    print(data.head())
```

## Example 2: REST API Data Source

Connect to a REST API (e.g., Alpha Vantage, Yahoo Finance):

```python
import httpx
from typing import List
from datetime import date
import pandas as pd

class APIDataSource(CustomDataSource):
    """Data source that connects to a REST API."""

    def __init__(
        self,
        base_url: str,
        api_key: str = None,
        timeout: int = 30
    ):
        """
        Initialize API data source.

        Args:
            base_url: Base URL for the API
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.client: httpx.AsyncClient = None

    async def __aenter__(self):
        """Create HTTP client."""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout
        )
        return self

    async def __aexit__(self, *args):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()

    async def fetch_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Fetch data from API."""
        if not self.client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        # Make API request
        params = {
            "symbol": symbol,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "interval": interval
        }

        response = await self.client.get("/api/ohlcv", params=params)
        response.raise_for_status()

        # Parse response
        data = response.json()

        # Convert to DataFrame
        df = pd.DataFrame(data["results"])
        df["date"] = pd.to_datetime(df["timestamp"])
        df.set_index("date", inplace=True)

        # Select required columns
        df = df[["open", "high", "low", "close", "volume"]]

        return df

    async def get_available_symbols(self) -> List[str]:
        """Get list of available symbols from API."""
        if not self.client:
            raise RuntimeError("Client not initialized")

        response = await self.client.get("/api/symbols")
        response.raise_for_status()

        data = response.json()
        return data["symbols"]

# Usage
api_source = APIDataSource(
    base_url="https://api.example.com",
    api_key="your_api_key"
)

async with api_source:
    data = await api_source.fetch_ohlcv(
        symbol="AAPL",
        start=date(2024, 1, 1),
        end=date(2024, 12, 31)
    )
    print(data.head())
```

## Example 3: Database Data Source

Connect to a SQL database:

```python
import aiosqlite
from typing import List
from datetime import date
import pandas as pd

class DatabaseDataSource(CustomDataSource):
    """Data source that connects to a SQLite database."""

    def __init__(self, db_path: str):
        """
        Initialize database data source.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection: aiosqlite.Connection = None

    async def __aenter__(self):
        """Create database connection."""
        self.connection = await aiosqlite.connect(self.db_path)
        return self

    async def __aexit__(self, *args):
        """Close database connection."""
        if self.connection:
            await self.connection.close()

    async def fetch_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Fetch data from database."""
        if not self.connection:
            raise RuntimeError("Connection not initialized")

        # Query database
        query = """
        SELECT date, open, high, low, close, volume
        FROM ohlcv_data
        WHERE symbol = ?
          AND date >= ?
          AND date <= ?
          AND interval = ?
        ORDER BY date ASC
        """

        cursor = await self.connection.execute(
            query,
            (symbol, start.isoformat(), end.isoformat(), interval)
        )

        rows = await cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=columns)
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        return df

    async def get_available_symbols(self) -> List[str]:
        """Get list of available symbols from database."""
        if not self.connection:
            raise RuntimeError("Connection not initialized")

        query = "SELECT DISTINCT symbol FROM ohlcv_data"
        cursor = await self.connection.execute(query)
        rows = await cursor.fetchall()

        return [row[0] for row in rows]

# Usage
db_source = DatabaseDataSource("path/to/market_data.db")

async with db_source:
    data = await db_source.fetch_ohlcv(
        symbol="AAPL",
        start=date(2024, 1, 1),
        end=date(2024, 12, 31)
    )
    print(data.head())
```

## Example 4: PostgreSQL Database

Connect to PostgreSQL database:

```python
import asyncpg
from typing import List
from datetime import date
import pandas as pd

class PostgreSQLDataSource(CustomDataSource):
    """Data source that connects to a PostgreSQL database."""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str
    ):
        """
        Initialize PostgreSQL data source.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
        """
        self.connection_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }
        self.connection: asyncpg.Connection = None

    async def __aenter__(self):
        """Create database connection."""
        self.connection = await asyncpg.connect(**self.connection_params)
        return self

    async def __aexit__(self, *args):
        """Close database connection."""
        if self.connection:
            await self.connection.close()

    async def fetch_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Fetch data from PostgreSQL database."""
        if not self.connection:
            raise RuntimeError("Connection not initialized")

        # Query database
        query = """
        SELECT timestamp, open, high, low, close, volume
        FROM market_data
        WHERE symbol = $1
          AND timestamp >= $2
          AND timestamp <= $3
          AND interval = $4
        ORDER BY timestamp ASC
        """

        rows = await self.connection.fetch(
            query,
            symbol,
            start,
            end,
            interval
        )

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                "date": row["timestamp"],
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"]
            }
            for row in rows
        ])
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        return df

    async def get_available_symbols(self) -> List[str]:
        """Get list of available symbols from database."""
        if not self.connection:
            raise RuntimeError("Connection not initialized")

        query = "SELECT DISTINCT symbol FROM market_data"
        rows = await self.connection.fetch(query)

        return [row["symbol"] for row in rows]

# Usage
pg_source = PostgreSQLDataSource(
    host="localhost",
    port=5432,
    database="market_data",
    user="postgres",
    password="password"
)

async with pg_source:
    data = await pg_source.fetch_ohlcv(
        symbol="AAPL",
        start=date(2024, 1, 1),
        end=date(2024, 12, 31)
    )
    print(data.head())
```

## Integrating with StrategyWorkspace

Use custom data sources with StrategyWorkspace:

```python
from cbsc_strategy_sdk import StrategyWorkspace, BacktestAdapter

class CustomWorkspace(StrategyWorkspace):
    """Workspace with custom data source."""

    def __init__(self, custom_source: CustomDataSource):
        super().__init__()
        self.custom_source = custom_source

    async def get_custom_data(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Fetch data from custom source."""
        return await self.custom_source.fetch_ohlcv(
            symbol, start, end, interval
        )

# Usage
csv_source = CSVDataSource("path/to/data")
workspace = CustomWorkspace(csv_source)

async with workspace:
    data = await workspace.get_custom_data(
        symbol="AAPL",
        start=date(2024, 1, 1),
        end=date(2024, 12, 31)
    )
    print(data.head())
```

## Caching Custom Data

Implement caching for custom data sources:

```python
from functools import lru_cache
from typing import Tuple
import hashlib

class CachedDataSource(CustomDataSource):
    """Data source with caching."""

    def __init__(self, source: CustomDataSource, cache_size: int = 100):
        """
        Initialize cached data source.

        Args:
            source: Underlying data source
            cache_size: Number of cached queries
        """
        self.source = source

    def _cache_key(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str
    ) -> str:
        """Generate cache key."""
        key_str = f"{symbol}:{start}:{end}:{interval}"
        return hashlib.md5(key_str.encode()).hexdigest()

    async def fetch_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Fetch with caching."""
        # Check cache
        cache_key = self._cache_key(symbol, start, end, interval)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        # Fetch from source
        data = await self.source.fetch_ohlcv(symbol, start, end, interval)

        # Store in cache
        self._store_in_cache(cache_key, data)

        return data

    def _get_from_cache(self, key: str) -> pd.DataFrame:
        """Get from cache (implement your caching logic)."""
        pass

    def _store_in_cache(self, key: str, data: pd.DataFrame):
        """Store in cache (implement your caching logic)."""
        pass

    async def get_available_symbols(self) -> List[str]:
        """Get available symbols from underlying source."""
        return await self.source.get_available_symbols()
```

## Error Handling

Implement robust error handling:

```python
class RobustDataSource(CustomDataSource):
    """Data source with error handling."""

    async def fetch_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str = "1d",
        max_retries: int = 3
    ) -> pd.DataFrame:
        """Fetch with retry logic."""
        for attempt in range(max_retries):
            try:
                return await self._fetch_impl(symbol, start, end, interval)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    async def _fetch_impl(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str
    ) -> pd.DataFrame:
        """Actual fetch implementation."""
        # Your fetch logic here
        pass
```

## Best Practices

1. **Always use async context managers** for connections
2. **Implement proper error handling** with retries
3. **Cache results** to avoid redundant API calls
4. **Validate data** before returning
5. **Use connection pooling** for database sources
6. **Log errors** for debugging

## Next Steps

- Learn about [custom indicators](TUTORIAL_CUSTOM_INDICATORS.md)
- Explore [advanced backtesting](TUTORIAL_ADVANCED_BACKTEST.md)
- Check out [example notebooks](../examples/)

---

**Version:** 0.1.0
**Last Updated:** 2026-01-11

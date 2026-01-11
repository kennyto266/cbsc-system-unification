"""Circular buffer for time-series data aggregation.

Provides fixed-size circular buffer for efficient data storage.
"""

from collections import deque
from typing import Any, Optional
import pandas as pd


class CircularBuffer:
    """Fixed-size circular buffer for time-series data.

    Provides efficient O(1) append and O(n) conversion to pandas DataFrame.
    Automatically discards old data when buffer is full.

    Example:
        >>> buffer = CircularBuffer(size=100)
        >>> buffer.append({'price': 100.0, 'volume': 1000})
        >>> buffer.append({'price': 101.0, 'volume': 2000})
        >>> df = buffer.to_dataframe()
    """

    def __init__(self, size: int, columns: Optional[list[str]] = None) -> None:
        """Initialize circular buffer.

        Args:
            size: Maximum number of items to store
            columns: Optional column names for DataFrame conversion

        Raises:
            ValueError: If size is not positive
        """
        if size <= 0:
            raise ValueError(f"Buffer size must be positive, got {size}")
        self.size = size
        self.columns = columns
        self._buffer: deque = deque(maxlen=size)
        self._count = 0

    def append(self, item: Any) -> None:
        """Add item to buffer.

        If buffer is full, oldest item is automatically removed.

        Args:
            item: Item to add (dict, object, or any type)
        """
        self._buffer.append(item)
        self._count += 1

    def extend(self, items: list[Any]) -> None:
        """Add multiple items to buffer.

        Args:
            items: List of items to add
        """
        for item in items:
            self.append(item)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert buffer to pandas DataFrame.

        Returns:
            DataFrame with buffered data. If columns were specified
            during initialization, uses those column names.

        Example:
            >>> df = buffer.to_dataframe()
            >>> print(df.head())
        """
        if not self._buffer:
            # Return empty DataFrame with columns if specified
            if self.columns:
                return pd.DataFrame(columns=self.columns)
            return pd.DataFrame()

        # Convert items to dict if they are Pydantic models
        data = []
        for item in self._buffer:
            if hasattr(item, 'model_dump'):
                # Pydantic v2
                data.append(item.model_dump())
            elif hasattr(item, 'dict'):
                # Pydantic v1
                data.append(item.dict())
            elif isinstance(item, dict):
                data.append(item)
            else:
                # Fallback for other objects
                data.append(item)

        df = pd.DataFrame(data)

        # Use specified columns if provided
        if self.columns and not df.empty:
            # Reorder/filter columns
            available_columns = [c for c in self.columns if c in df.columns]
            if available_columns:
                df = df[available_columns]

        return df

    def latest(self, n: int) -> list[Any]:
        """Get n most recent items.

        Args:
            n: Number of items to retrieve

        Returns:
            List of most recent items (empty if n > current size)

        Example:
            >>> # Get last 10 items
            >>> recent = buffer.latest(10)
        """
        if n <= 0:
            return []
        if n >= len(self._buffer):
            return list(self._buffer)
        # Get last n items
        return list(self._buffer)[-n:]

    def clear(self) -> None:
        """Clear all items from buffer.

        Example:
            >>> buffer.clear()
        """
        self._buffer.clear()
        self._count = 0

    @property
    def is_empty(self) -> bool:
        """Check if buffer is empty.

        Returns:
            True if buffer has no items
        """
        return len(self._buffer) == 0

    @property
    def is_full(self) -> bool:
        """Check if buffer is full.

        Returns:
            True if buffer has reached max size
        """
        return len(self._buffer) == self.size

    @property
    def current_size(self) -> int:
        """Get current number of items in buffer.

        Returns:
            Current buffer size
        """
        return len(self._buffer)

    @property
    def total_appended(self) -> int:
        """Get total count of items ever appended.

        Returns:
            Total number of append operations (including overwritten items)
        """
        return self._count

    def __len__(self) -> int:
        """Get current buffer size."""
        return len(self._buffer)

    def __repr__(self) -> str:
        """String representation of buffer."""
        return f"CircularBuffer(size={self.size}, current={len(self._buffer)})"


class TickCircularBuffer(CircularBuffer):
    """Specialized circular buffer for TickData.

    Provides convenience methods for working with market tick data.
    """

    def __init__(self, size: int, symbol: Optional[str] = None) -> None:
        """Initialize tick buffer.

        Args:
            size: Maximum number of ticks to store
            symbol: Optional symbol name for this buffer
        """
        super().__init__(size)
        self.symbol = symbol

    def get_latest_price(self) -> Optional[float]:
        """Get latest price from buffer.

        Returns:
            Latest price or None if buffer is empty
        """
        if self.is_empty:
            return None
        latest_tick = self._buffer[-1]
        return getattr(latest_tick, 'price', None)

    def get_prices(self) -> list[float]:
        """Extract all prices from buffer.

        Returns:
            List of prices in chronological order
        """
        prices = []
        for tick in self._buffer:
            price = getattr(tick, 'price', None)
            if price is not None:
                prices.append(price)
        return prices

    def get_volumes(self) -> list[int]:
        """Extract all volumes from buffer.

        Returns:
            List of volumes in chronological order
        """
        volumes = []
        for tick in self._buffer:
            volume = getattr(tick, 'volume', None)
            if volume is not None:
                volumes.append(volume)
        return volumes

    def to_ohlcv(self, interval: str = '1s') -> pd.DataFrame:
        """Convert ticks to OHLCV bars.

        Aggregates ticks into OHLCV bars for the specified interval.

        Args:
            interval: Pandas resample interval string (e.g., '1s', '5s', '1min')

        Returns:
            DataFrame with OHLCV data

        Example:
            >>> bars = tick_buffer.to_ohlcv('5s')
            >>> print(bars.head())
        """
        if self.is_empty:
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

        # Convert to DataFrame
        df = self.to_dataframe()

        # Ensure we have required columns
        required_cols = ['timestamp', 'price', 'volume']
        if not all(col in df.columns for col in required_cols):
            # Try to extract from TickData objects
            data = {
                'timestamp': [t.timestamp for t in self._buffer if hasattr(t, 'timestamp')],
                'price': [t.price for t in self._buffer if hasattr(t, 'price')],
                'volume': [t.volume for t in self._buffer if hasattr(t, 'volume')],
            }
            df = pd.DataFrame(data)

        # Set timestamp as index
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)

        # Resample to OHLCV
        ohlcv = df.resample(interval).agg({
            'price': ['first', 'max', 'min', 'last'],
            'volume': 'sum'
        })

        # Flatten column names
        ohlcv.columns = ['open', 'high', 'low', 'close', 'volume']

        # Remove rows with NaN
        ohlcv.dropna(inplace=True)

        return ohlcv

    def __repr__(self) -> str:
        """String representation of tick buffer."""
        symbol_str = f"symbol='{self.symbol}'" if self.symbol else ""
        return f"TickCircularBuffer({symbol_str}size={self.size}, current={len(self._buffer)})"

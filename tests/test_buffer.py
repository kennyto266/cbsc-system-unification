"""Tests for CircularBuffer and TickCircularBuffer.

Unit tests for data buffering and aggregation.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta

from cbsc_strategy_sdk.data.buffer import CircularBuffer, TickCircularBuffer
from cbsc_strategy_sdk.data.models import TickData


class TestCircularBuffer:
    """Test CircularBuffer functionality."""

    def test_init(self) -> None:
        """Test buffer initialization."""
        buffer = CircularBuffer(size=100)
        assert buffer.size == 100
        assert buffer.is_empty
        assert not buffer.is_full
        assert buffer.current_size == 0

    def test_init_invalid_size(self) -> None:
        """Test initialization with invalid size."""
        with pytest.raises(ValueError):
            CircularBuffer(size=0)
        with pytest.raises(ValueError):
            CircularBuffer(size=-1)

    def test_append_single_item(self) -> None:
        """Test appending single item."""
        buffer = CircularBuffer(size=10)
        buffer.append({'value': 1})

        assert buffer.current_size == 1
        assert not buffer.is_empty

    def test_append_multiple_items(self) -> None:
        """Test appending multiple items."""
        buffer = CircularBuffer(size=10)
        for i in range(5):
            buffer.append({'value': i})

        assert buffer.current_size == 5

    def test_extend(self) -> None:
        """Test extending buffer with multiple items."""
        buffer = CircularBuffer(size=10)
        items = [{'value': i} for i in range(5)]
        buffer.extend(items)

        assert buffer.current_size == 5

    def test_buffer_overwrite(self) -> None:
        """Test that old items are overwritten when buffer is full."""
        buffer = CircularBuffer(size=5)

        # Fill buffer
        for i in range(5):
            buffer.append({'value': i})

        # Add more items
        buffer.append({'value': 5})
        buffer.append({'value': 6})

        # Buffer should still have size 5
        assert buffer.current_size == 5
        assert buffer.is_full

        # Oldest items should be gone
        df = buffer.to_dataframe()
        assert len(df) == 5
        assert df['value'].tolist() == [2, 3, 4, 5, 6]

    def test_to_dataframe_empty(self) -> None:
        """Test converting empty buffer to DataFrame."""
        buffer = CircularBuffer(size=10)
        df = buffer.to_dataframe()

        assert df.empty
        assert isinstance(df, pd.DataFrame)

    def test_to_dataframe_with_data(self) -> None:
        """Test converting buffer with data to DataFrame."""
        buffer = CircularBuffer(size=10)
        buffer.append({'name': 'Alice', 'age': 30})
        buffer.append({'name': 'Bob', 'age': 25})

        df = buffer.to_dataframe()

        assert len(df) == 2
        assert 'name' in df.columns
        assert 'age' in df.columns
        assert df['name'].tolist() == ['Alice', 'Bob']
        assert df['age'].tolist() == [30, 25]

    def test_to_dataframe_with_columns(self) -> None:
        """Test DataFrame conversion with specified columns."""
        buffer = CircularBuffer(size=10, columns=['name', 'age'])
        buffer.append({'name': 'Alice', 'age': 30, 'extra': 'data'})
        buffer.append({'name': 'Bob', 'age': 25, 'extra': 'more'})

        df = buffer.to_dataframe()

        assert list(df.columns) == ['name', 'age']

    def test_latest_empty_buffer(self) -> None:
        """Test getting latest items from empty buffer."""
        buffer = CircularBuffer(size=10)
        latest = buffer.latest(5)

        assert latest == []

    def test_latest_partial_buffer(self) -> None:
        """Test getting more items than buffer has."""
        buffer = CircularBuffer(size=10)
        for i in range(3):
            buffer.append({'value': i})

        latest = buffer.latest(5)
        assert len(latest) == 3
        assert [item['value'] for item in latest] == [0, 1, 2]

    def test_exact_items(self) -> None:
        """Test getting exact number of items."""
        buffer = CircularBuffer(size=10)
        for i in range(10):
            buffer.append({'value': i})

        latest = buffer.latest(5)
        assert len(latest) == 5
        assert [item['value'] for item in latest] == [5, 6, 7, 8, 9]

    def test_clear(self) -> None:
        """Test clearing buffer."""
        buffer = CircularBuffer(size=10)
        for i in range(5):
            buffer.append({'value': i})

        buffer.clear()

        assert buffer.is_empty
        assert buffer.current_size == 0

    def test_total_appended_counter(self) -> None:
        """Test total appended counter includes overwritten items."""
        buffer = CircularBuffer(size=5)

        # Add more items than buffer size
        for i in range(10):
            buffer.append({'value': i})

        # Current size should be 5
        assert buffer.current_size == 5
        # But total appended should be 10
        assert buffer.total_appended == 10

    def test_len(self) -> None:
        """Test len() function on buffer."""
        buffer = CircularBuffer(size=10)
        assert len(buffer) == 0

        buffer.append({'value': 1})
        assert len(buffer) == 2

    def test_repr(self) -> None:
        """Test string representation."""
        buffer = CircularBuffer(size=100)
        for i in range(5):
            buffer.append({'value': i})

        repr_str = repr(buffer)
        assert 'CircularBuffer' in repr_str
        assert 'size=100' in repr_str
        assert 'current=5' in repr_str


class TestTickCircularBuffer:
    """Test TickCircularBuffer functionality."""

    def create_tick(self, symbol: str, price: float, volume: int) -> TickData:
        """Helper to create test tick."""
        return TickData(
            symbol=symbol,
            timestamp=datetime.now(),
            price=price,
            volume=volume,
        )

    def test_init(self) -> None:
        """Test tick buffer initialization."""
        buffer = TickCircularBuffer(size=100, symbol='AAPL')
        assert buffer.size == 100
        assert buffer.symbol == 'AAPL'

    def test_init_without_symbol(self) -> None:
        """Test tick buffer without symbol."""
        buffer = TickCircularBuffer(size=100)
        assert buffer.symbol is None

    def test_get_latest_price_empty(self) -> None:
        """Test getting latest price from empty buffer."""
        buffer = TickCircularBuffer(size=100)
        assert buffer.get_latest_price() is None

    def test_get_latest_price(self) -> None:
        """Test getting latest price."""
        buffer = TickCircularBuffer(size=100, symbol='AAPL')

        buffer.append(self.create_tick('AAPL', 100.0, 1000))
        buffer.append(self.create_tick('AAPL', 101.0, 2000))
        buffer.append(self.create_tick('AAPL', 102.0, 3000))

        assert buffer.get_latest_price() == 102.0

    def test_get_prices(self) -> None:
        """Test extracting all prices."""
        buffer = TickCircularBuffer(size=100)

        for price in [100.0, 101.0, 102.0, 103.0]:
            buffer.append(self.create_tick('AAPL', price, 1000))

        prices = buffer.get_prices()
        assert prices == [100.0, 101.0, 102.0, 103.0]

    def test_get_volumes(self) -> None:
        """Test extracting all volumes."""
        buffer = TickCircularBuffer(size=100)

        for volume in [1000, 2000, 3000, 4000]:
            buffer.append(self.create_tick('AAPL', 100.0, volume))

        volumes = buffer.get_volumes()
        assert volumes == [1000, 2000, 3000, 4000]

    def test_to_dataframe(self) -> None:
        """Test converting tick buffer to DataFrame."""
        buffer = TickCircularBuffer(size=100)

        buffer.append(self.create_tick('AAPL', 100.0, 1000))
        buffer.append(self.create_tick('AAPL', 101.0, 2000))

        df = buffer.to_dataframe()

        assert len(df) == 2
        assert 'price' in df.columns
        assert 'volume' in df.columns
        assert df['price'].tolist() == [100.0, 101.0]

    def test_to_ohlcv_empty(self) -> None:
        """Test OHLCV conversion with empty buffer."""
        buffer = TickCircularBuffer(size=100)
        ohlcv = buffer.to_ohlcv()

        assert ohlcv.empty
        assert 'open' in ohlcv.columns
        assert 'high' in ohlcv.columns
        assert 'low' in ohlcv.columns
        assert 'close' in ohlcv.columns
        assert 'volume' in ohlcv.columns

    def test_to_ohlcv_aggregation(self) -> None:
        """Test OHLCV aggregation."""
        buffer = TickCircularBuffer(size=100)
        base_time = datetime.now()

        # Add ticks over time
        for i in range(10):
            tick = TickData(
                symbol='AAPL',
                timestamp=base_time + timedelta(seconds=i),
                price=100.0 + i,
                volume=1000 * (i + 1),
            )
            buffer.append(tick)

        # Convert to OHLCV with 5-second intervals
        ohlcv = buffer.to_ohlcv(interval='5s')

        # Should have 2 bars
        assert len(ohlcv) == 2

        # Check first bar
        first_bar = ohlcv.iloc[0]
        assert first_bar['open'] == 100.0
        assert first_bar['high'] == 104.0
        assert first_bar['low'] == 100.0
        assert first_bar['close'] == 104.0
        assert first_bar['volume'] == 30000  # 1000 + 2000 + 3000 + 4000 + 5000

    def test_repr(self) -> None:
        """Test string representation."""
        buffer = TickCircularBuffer(size=100, symbol='AAPL')
        for i in range(5):
            buffer.append(self.create_tick('AAPL', 100.0 + i, 1000))

        repr_str = repr(buffer)
        assert 'TickCircularBuffer' in repr_str
        assert 'symbol=' in repr_str
        assert 'AAPL' in repr_str


class TestCircularBufferEdgeCases:
    """Test edge cases and error handling."""

    def test_large_buffer(self) -> None:
        """Test buffer with large size."""
        buffer = CircularBuffer(size=10000)

        for i in range(10000):
            buffer.append({'value': i})

        assert buffer.is_full
        assert buffer.current_size == 10000

    def test_single_item_buffer(self) -> None:
        """Test buffer with size of 1."""
        buffer = CircularBuffer(size=1)

        buffer.append({'value': 1})
        assert buffer.current_size == 1
        assert buffer.get_latest_price() is None  # Not a TickCircularBuffer

    def test_mixed_data_types(self) -> None:
        """Test buffer with various data types."""
        buffer = CircularBuffer(size=10)

        buffer.append({'int': 42, 'float': 3.14, 'str': 'hello', 'bool': True})
        df = buffer.to_dataframe()

        assert df['int'].iloc[0] == 42
        assert df['float'].iloc[0] == 3.14
        assert df['str'].iloc[0] == 'hello'
        assert df['bool'].iloc[0] is True

    def test_unicode_strings(self) -> None:
        """Test buffer with Unicode strings."""
        buffer = CircularBuffer(size=10)

        buffer.append({'text': 'Hello 世界 🌍'})
        df = buffer.to_dataframe()

        assert df['text'].iloc[0] == 'Hello 世界 🌍'

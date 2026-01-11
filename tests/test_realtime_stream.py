"""Tests for RealTimeDataStream WebSocket client.

Unit tests with mock WebSocket server.
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from cbsc_strategy_sdk.data.realtime_stream import (
    RealTimeDataStream,
    ConnectionManager,
    RealTimeDataStreamError,
)
from cbsc_strategy_sdk.data.models import TickData
from cbsc_strategy_sdk.data.buffer import TickCircularBuffer


# Mock WebSocket for testing
class MockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self):
        self.messages_sent = []
        self.closed = False
        self._queue = asyncio.Queue()

    async def send(self, message):
        """Mock send."""
        self.messages_sent.append(message)

    async def close(self):
        """Mock close."""
        self.closed = True

    async def put_message(self, message):
        """Add message to queue for receiving."""
        await self._queue.put(message)

    def __aiter__(self):
        """Async iterator."""
        return self

    async def __anext__(self):
        """Get next message."""
        return await self._queue.get()


class TestConnectionManager:
    """Test ConnectionManager functionality."""

    def test_init(self) -> None:
        """Test ConnectionManager initialization."""
        manager = ConnectionManager(max_retries=3, retry_delay=0.5)
        assert manager.max_retries == 3
        assert manager.retry_delay == 0.5
        assert manager.backoff_factor == 2.0
        assert manager.retry_count == 0
        assert not manager.is_connected

    def test_reset(self) -> None:
        """Test resetting retry counter."""
        manager = ConnectionManager()
        manager.retry_count = 5
        manager.reset()
        assert manager.retry_count == 0


class TestRealTimeDataStream:
    """Test RealTimeDataStream functionality."""

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket."""
        return MockWebSocket()

    @pytest.fixture
    def stream_config(self):
        """Get stream configuration."""
        return {
            'ws_url': 'ws://localhost:3007/ws/realtime',
            'auth_token': 'test-token',
            'symbols': ['AAPL', '0700.HK'],
            'buffer_size': 100,
        }

    def test_init(self, stream_config) -> None:
        """Test RealTimeDataStream initialization."""
        stream = RealTimeDataStream(**stream_config)

        assert stream.ws_url == stream_config['ws_url']
        assert stream.auth_token == stream_config['auth_token']
        assert stream.symbols == stream_config['symbols']
        assert stream.buffer_size == stream_config['buffer_size']
        assert not stream.is_connected
        assert not stream.is_streaming

    def test_init_creates_buffers(self, stream_config) -> None:
        """Test that initialization creates buffers for each symbol."""
        stream = RealTimeDataStream(**stream_config)

        assert 'AAPL' in stream._buffers
        assert '0700.HK' in stream._buffers
        assert isinstance(stream._buffers['AAPL'], TickCircularBuffer)
        assert isinstance(stream._buffers['0700.HK'], TickCircularBuffer)

    def test_symbols_subscribed(self, stream_config) -> None:
        """Test getting subscribed symbols."""
        stream = RealTimeDataStream(**stream_config)

        symbols = stream.symbols_subscribed
        assert symbols == ['AAPL', '0700.HK']

    def test_get_buffer(self, stream_config) -> None:
        """Test getting buffer for symbol."""
        stream = RealTimeDataStream(**stream_config)

        buffer = stream.get_buffer('AAPL')
        assert buffer is not None
        assert buffer.symbol == 'AAPL'

    def test_get_buffer_nonexistent(self, stream_config) -> None:
        """Test getting buffer for non-existent symbol."""
        stream = RealTimeDataStream(**stream_config)

        buffer = stream.get_buffer('INVALID')
        assert buffer is None

    def test_parse_tick_valid(self, stream_config) -> None:
        """Test parsing valid tick data."""
        stream = RealTimeDataStream(**stream_config)

        data = {
            'symbol': 'AAPL',
            'timestamp': '2024-01-01T10:00:00Z',
            'price': '150.25',
            'volume': '1000',
            'bid': '150.20',
            'ask': '150.30',
            'bid_size': '500',
            'ask_size': '500',
        }

        tick = stream._parse_tick(data)

        assert tick is not None
        assert tick.symbol == 'AAPL'
        assert tick.price == 150.25
        assert tick.volume == 1000
        assert tick.bid == 150.20
        assert tick.ask == 150.30
        assert tick.bid_size == 500
        assert tick.ask_size == 500

    def test_parse_tick_minimal(self, stream_config) -> None:
        """Test parsing tick with minimal data."""
        stream = RealTimeDataStream(**stream_config)

        data = {
            'symbol': 'AAPL',
            'timestamp': '2024-01-01T10:00:00Z',
            'price': '150.25',
            'volume': '1000',
        }

        tick = stream._parse_tick(data)

        assert tick is not None
        assert tick.symbol == 'AAPL'
        assert tick.price == 150.25
        assert tick.bid is None
        assert tick.ask is None

    def test_parse_tick_invalid(self, stream_config) -> None:
        """Test parsing invalid tick data."""
        stream = RealTimeDataStream(**stream_config)

        # Invalid price
        data = {
            'symbol': 'AAPL',
            'timestamp': '2024-01-01T10:00:00Z',
            'price': 'invalid',
            'volume': '1000',
        }

        tick = stream._parse_tick(data)
        assert tick is None

    def test_subscribe_new_symbol(self, stream_config) -> None:
        """Test subscribing to new symbol."""
        stream = RealTimeDataStream(**stream_config)

        assert 'TSLA' not in stream._buffers
        stream.subscribe('TSLA')
        assert 'TSLA' in stream._buffers
        assert 'TSLA' in stream.symbols

    def test_unsubscribe_symbol(self, stream_config) -> None:
        """Test unsubscribing from symbol."""
        stream = RealTimeDataStream(**stream_config)

        assert 'AAPL' in stream._buffers
        stream.unsubscribe('AAPL')
        assert 'AAPL' not in stream._buffers
        assert 'AAPL' not in stream.symbols

    def test_get_latest_ticks(self, stream_config) -> None:
        """Test getting latest ticks."""
        stream = RealTimeDataStream(**stream_config)

        # Add ticks to buffer
        tick1 = TickData(
            symbol='AAPL',
            timestamp=datetime.now(),
            price=150.0,
            volume=1000,
        )
        tick2 = TickData(
            symbol='AAPL',
            timestamp=datetime.now(),
            price=151.0,
            volume=2000,
        )

        stream._buffers['AAPL'].append(tick1)
        stream._buffers['AAPL'].append(tick2)

        latest = stream.get_latest_ticks('AAPL', 2)
        assert len(latest) == 2
        assert latest[0].price == 150.0
        assert latest[1].price == 151.0

    def test_repr(self, stream_config) -> None:
        """Test string representation."""
        stream = RealTimeDataStream(**stream_config)

        repr_str = repr(stream)
        assert 'RealTimeDataStream' in repr_str
        assert 'symbols=2' in repr_str
        assert 'disconnected' in repr_str


class TestRealTimeDataStreamAsync:
    """Async tests for RealTimeDataStream."""

    @pytest.fixture
    def stream_config(self):
        """Get stream configuration."""
        return {
            'ws_url': 'ws://localhost:3007/ws/realtime',
            'auth_token': 'test-token',
            'symbols': ['AAPL'],
            'buffer_size': 10,
        }

    @pytest.mark.asyncio
    async def test_connect_mock(self, stream_config) -> None:
        """Test connection with mock WebSocket."""
        stream = RealTimeDataStream(**stream_config)

        mock_ws = MockWebSocket()

        with patch('cbsc_strategy_sdk.data.realtime_stream.websockets') as mock_websockets:
            mock_websockets.connect = AsyncMock(return_value=mock_ws)
            mock_websockets.exceptions = MagicMock()
            mock_websockets.exceptions.ConnectionClosed = Exception

            await stream.connect()

            assert stream.is_connected
            assert len(mock_ws.messages_sent) == 1  # Subscribe message

            # Check subscription message
            subscribe_msg = json.loads(mock_ws.messages_sent[0])
            assert subscribe_msg['action'] == 'subscribe'
            assert subscribe_msg['symbol'] == 'AAPL'

    @pytest.mark.asyncio
    async def test_disconnect(self, stream_config) -> None:
        """Test disconnection."""
        stream = RealTimeDataStream(**stream_config)

        mock_ws = MockWebSocket()

        with patch('cbsc_strategy_sdk.data.realtime_stream.websockets') as mock_websockets:
            mock_websockets.connect = AsyncMock(return_value=mock_ws)
            mock_websockets.exceptions = MagicMock()
            mock_websockets.exceptions.ConnectionClosed = Exception

            await stream.connect()
            assert stream.is_connected

            await stream.disconnect()
            assert not stream.is_connected
            assert mock_ws.closed

    @pytest.mark.asyncio
    async def test_stream_iteration(self, stream_config) -> None:
        """Test async iteration over stream."""
        stream = RealTimeDataStream(**stream_config)

        # Add tick to queue
        tick = TickData(
            symbol='AAPL',
            timestamp=datetime.now(),
            price=150.0,
            volume=1000,
        )
        await stream._queue.put(tick)

        # Stream should yield tick
        ticks_received = []
        async for received_tick in stream.stream():
            ticks_received.append(received_tick)
            if len(ticks_received) >= 1:
                break

        assert len(ticks_received) == 1
        assert ticks_received[0].price == 150.0

    @pytest.mark.asyncio
    async def test_event_emission(self, stream_config) -> None:
        """Test event emission on tick."""
        stream = RealTimeDataStream(**stream_config)

        ticks_received = []

        def on_tick(tick):
            ticks_received.append(tick)

        stream.on('tick', on_tick)

        # Emit tick event
        tick = TickData(
            symbol='AAPL',
            timestamp=datetime.now(),
            price=150.0,
            volume=1000,
        )
        await stream.emit('tick', tick)

        assert len(ticks_received) == 1
        assert ticks_received[0].price == 150.0

    @pytest.mark.asyncio
    async def test_subscribe_existing_symbol(self, stream_config) -> None:
        """Test subscribing to existing symbol doesn't duplicate."""
        stream = RealTimeDataStream(**stream_config)

        initial_count = len(stream.symbols)
        stream.subscribe('AAPL')  # Already subscribed
        assert len(stream.symbols) == initial_count


class TestRealTimeDataStreamErrorHandling:
    """Test error handling in RealTimeDataStream."""

    def test_connection_error_raised_without_websockets(self) -> None:
        """Test that missing websockets library raises ImportError."""
        with patch('cbsc_strategy_sdk.data.realtime_stream.WEBSOCKETS_AVAILABLE', False):
            with pytest.raises(ImportError):
                ConnectionManager()

    @pytest.mark.asyncio
    async def test_connection_failure_after_retries(self) -> None:
        """Test connection failure after max retries."""
        manager = ConnectionManager(max_retries=2, retry_delay=0.01)

        with patch('cbsc_strategy_sdk.data.realtime_stream.websockets') as mock_websockets:
            mock_websockets.connect = AsyncMock(side_effect=ConnectionError("Failed"))
            mock_websockets.exceptions = MagicMock()
            mock_websockets.exceptions.ConnectionClosed = Exception

            with pytest.raises(RealTimeDataStreamError):
                await manager.connect_with_retry('ws://localhost:9999')

            assert manager.retry_count == 2


class TestRealTimeDataStreamIntegration:
    """Integration tests for RealTimeDataStream."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self) -> None:
        """Test full lifecycle: connect -> receive -> disconnect."""
        config = {
            'ws_url': 'ws://localhost:3007/ws/realtime',
            'auth_token': 'test-token',
            'symbols': ['AAPL'],
            'buffer_size': 10,
        }

        stream = RealTimeDataStream(**config)
        mock_ws = MockWebSocket()

        # Mock websockets module
        with patch('cbsc_strategy_sdk.data.realtime_stream.websockets') as mock_websockets:
            mock_websockets.connect = AsyncMock(return_value=mock_ws)
            mock_websockets.exceptions = MagicMock()
            mock_websockets.exceptions.ConnectionClosed = Exception

            # Connect
            await stream.connect()
            assert stream.is_connected

            # Simulate receiving tick
            tick_data = {
                'symbol': 'AAPL',
                'timestamp': datetime.now().isoformat(),
                'price': '150.25',
                'volume': '1000',
            }
            await mock_ws.put_message(json.dumps(tick_data))

            # Wait a bit for message processing
            await asyncio.sleep(0.1)

            # Disconnect
            await stream.disconnect()
            assert not stream.is_connected

    @pytest.mark.asyncio
    async def test_multiple_symbols_buffering(self) -> None:
        """Test buffering for multiple symbols."""
        config = {
            'ws_url': 'ws://localhost:3007/ws/realtime',
            'auth_token': 'test-token',
            'symbols': ['AAPL', '0700.HK', 'TSLA'],
            'buffer_size': 10,
        }

        stream = RealTimeDataStream(**config)

        # Add ticks to each buffer
        for symbol in config['symbols']:
            tick = TickData(
                symbol=symbol,
                timestamp=datetime.now(),
                price=150.0,
                volume=1000,
            )
            stream._buffers[symbol].append(tick)

        # Check each buffer
        for symbol in config['symbols']:
            latest = stream.get_latest_ticks(symbol, 1)
            assert len(latest) == 1
            assert latest[0].symbol == symbol

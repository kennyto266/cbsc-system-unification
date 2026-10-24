"""WebSocket client for CBSC real-time market data streaming.

Provides async WebSocket client with auto-reconnection, event system,
and data buffering for live market data consumption.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncIterator, Optional, Union

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketClientProtocol = None

from .buffer import CircularBuffer, TickCircularBuffer
from .events import EventEmitter
from .models import TickData
from ..exceptions import StrategyWorkspaceError

logger = logging.getLogger(__name__)


class RealTimeDataStreamError(StrategyWorkspaceError):
    """Exception raised for real-time stream errors."""

    pass


class ConnectionManager:
    """Manage WebSocket connection with auto-reconnect.

    Handles connection lifecycle with exponential backoff retry logic.
    """

    def __init__(
        self,
        max_retries: int = 5,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
    ) -> None:
        """Initialize connection manager.

        Args:
            max_retries: Maximum number of reconnection attempts
            retry_delay: Initial delay between retries in seconds
            backoff_factor: Multiplier for delay after each retry
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets library is required. Install: pip install websockets")

        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self.retry_count = 0
        self._is_connected = False
        self._websocket: Optional[WebSocketClientProtocol] = None

    async def connect_with_retry(
        self,
        url: str,
        auth_token: Optional[str] = None,
    ) -> WebSocketClientProtocol:
        """Connect to WebSocket with exponential backoff.

        Args:
            url: WebSocket URL
            auth_token: Optional JWT token for authentication

        Returns:
            Connected WebSocket client protocol

        Raises:
            RealTimeDataStreamError: If all retry attempts fail
        """
        delay = self.retry_delay

        for attempt in range(self.max_retries):
            try:
                # Prepare headers with auth token
                headers = {}
                if auth_token:
                    headers["Authorization"] = f"Bearer {auth_token}"

                # Connect to WebSocket
                logger.info(f"Connecting to {url} (attempt {attempt + 1}/{self.max_retries})")
                self._websocket = await websockets.connect(url, extra_headers=headers)
                self._is_connected = True
                self.retry_count = 0

                logger.info(f"Connected to {url}")
                return self._websocket

            except Exception as e:
                self.retry_count += 1
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")

                if attempt < self.max_retries - 1:
                    # Wait before next retry with exponential backoff
                    await asyncio.sleep(delay)
                    delay *= self.backoff_factor

        # All retries failed
        raise RealTimeDataStreamError(
            f"Failed to connect after {self.max_retries} attempts",
            details={"url": url, "retry_count": self.retry_count},
        )

    async def disconnect(self) -> None:
        """Close WebSocket connection gracefully."""
        if self._websocket:
            try:
                await self._websocket.close()
                logger.info("WebSocket connection closed")
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
            finally:
                self._websocket = None
                self._is_connected = False

    def reset(self) -> None:
        """Reset retry counter."""
        self.retry_count = 0

    @property
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._is_connected and self._websocket is not None

    @property
    def websocket(self) -> Optional[WebSocketClientProtocol]:
        """Get underlying WebSocket connection."""
        return self._websocket


class RealTimeDataStream(EventEmitter):
    """WebSocket client for CBSC real-time market data.

    Provides async interface for consuming live market data with
    automatic reconnection, data buffering, and event callbacks.

    Example:
        >>> stream = RealTimeDataStream(
        ...     ws_url="ws://localhost:3007/ws/realtime",
        ...     auth_token="your-jwt-token",
        ...     symbols=["AAPL", "0700.HK"],
        ...     buffer_size=1000
        ... )
        >>>
        >>> # Add event callback
        >>> stream.on('tick', lambda tick: print(f"Received: {tick}"))
        >>>
        >>> # Connect and stream
        >>> await stream.connect()
        >>> async for tick in stream.stream():
        ...     # Process tick
        ...     pass
        >>>
        >>> await stream.disconnect()
    """

    def __init__(
        self,
        ws_url: str,
        auth_token: str,
        symbols: list[str],
        buffer_size: int = 1000,
        max_retries: int = 5,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize real-time data stream.

        Args:
            ws_url: WebSocket server URL
            auth_token: JWT authentication token
            symbols: List of symbols to subscribe
            buffer_size: Size of circular buffer per symbol
            max_retries: Maximum reconnection attempts
            retry_delay: Initial delay between retries
        """
        super().__init__()

        self.ws_url = ws_url
        self.auth_token = auth_token
        self.symbols = symbols
        self.buffer_size = buffer_size

        # Initialize connection manager
        self._connection = ConnectionManager(
            max_retries=max_retries,
            retry_delay=retry_delay,
        )

        # Data buffers per symbol
        self._buffers: dict[str, TickCircularBuffer] = {}
        for symbol in symbols:
            self._buffers[symbol] = TickCircularBuffer(size=buffer_size, symbol=symbol)

        # Async queue for streaming
        self._queue: asyncio.Queue = asyncio.Queue()
        self._consume_task: Optional[asyncio.Task] = None
        self._is_streaming = False

    async def connect(self) -> None:
        """Establish WebSocket connection.

        Raises:
            RealTimeDataStreamError: If connection fails
        """
        try:
            # Connect with retry logic
            ws = await self._connection.connect_with_retry(
                url=self.ws_url,
                auth_token=self.auth_token,
            )

            # Subscribe to symbols
            for symbol in self.symbols:
                await self._subscribe_symbol(ws, symbol)

            # Start consume task
            self._consume_task = asyncio.create_task(self._consume_messages(ws))

            # Emit connected event
            await self.emit('connected')

        except Exception as e:
            await self.emit('error', e)
            raise RealTimeDataStreamError(
                f"Failed to connect to real-time stream: {e}",
                details={"ws_url": self.ws_url},
            ) from e

    async def disconnect(self) -> None:
        """Gracefully close connection and cleanup resources."""
        self._is_streaming = False

        # Cancel consume task
        if self._consume_task:
            self._consume_task.cancel()
            try:
                await self._consume_task
            except asyncio.CancelledError:
                pass
            self._consume_task = None

        # Close connection
        await self._connection.disconnect()

        # Emit disconnected event
        await self.emit('disconnected')

    async def _subscribe_symbol(self, ws: WebSocketClientProtocol, symbol: str) -> None:
        """Send subscription message for a symbol.

        Args:
            ws: WebSocket connection
            symbol: Symbol to subscribe
        """
        subscribe_msg = {
            "action": "subscribe",
            "symbol": symbol,
        }
        try:
            await ws.send(json.dumps(subscribe_msg))
            logger.info(f"Subscribed to {symbol}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {symbol}: {e}")
            raise

    async def _unsubscribe_symbol(self, ws: WebSocketClientProtocol, symbol: str) -> None:
        """Send unsubscribe message for a symbol.

        Args:
            ws: WebSocket connection
            symbol: Symbol to unsubscribe
        """
        unsubscribe_msg = {
            "action": "unsubscribe",
            "symbol": symbol,
        }
        try:
            await ws.send(json.dumps(unsubscribe_msg))
            logger.info(f"Unsubscribed from {symbol}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe from {symbol}: {e}")

    def subscribe(self, symbol: str, fields: Optional[list[str]] = None) -> None:
        """Subscribe to a symbol (for future symbol addition).

        Note: This is a placeholder for future dynamic subscription.
        Current implementation requires symbols to be set at initialization.

        Args:
            symbol: Symbol to subscribe
            fields: Optional list of fields to receive
        """
        if symbol not in self.symbols:
            # Add new buffer for this symbol
            self._buffers[symbol] = TickCircularBuffer(size=self.buffer_size, symbol=symbol)
            self.symbols.append(symbol)

            # Send subscription if connected
            if self._connection.is_connected and self._connection.websocket:
                asyncio.create_task(self._subscribe_symbol(self._connection.websocket, symbol))

    def unsubscribe(self, symbol: str) -> None:
        """Unsubscribe from a symbol.

        Args:
            symbol: Symbol to unsubscribe
        """
        if symbol in self.symbols:
            # Send unsubscribe if connected
            if self._connection.is_connected and self._connection.websocket:
                asyncio.create_task(self._unsubscribe_symbol(self._connection.websocket, symbol))

            # Remove buffer
            if symbol in self._buffers:
                del self._buffers[symbol]

            # Remove from symbols list
            self.symbols.remove(symbol)

    async def _consume_messages(self, ws: WebSocketClientProtocol) -> None:
        """Consume messages from WebSocket and emit events.

        Args:
            ws: WebSocket connection
        """
        try:
            async for message in ws:
                try:
                    data = json.loads(message)
                    tick = self._parse_tick(data)

                    if tick:
                        # Add to buffer
                        if tick.symbol in self._buffers:
                            self._buffers[tick.symbol].append(tick)

                        # Add to queue for async iteration
                        await self._queue.put(tick)

                        # Emit tick event
                        await self.emit('tick', tick)

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
                    await self.emit('error', e)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await self.emit('error', e)

        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            await self.emit('disconnected')
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
            await self.emit('error', e)

    def _parse_tick(self, data: dict) -> Optional[TickData]:
        """Parse tick data from WebSocket message.

        Args:
            data: Raw message data

        Returns:
            TickData object or None if parsing fails
        """
        try:
            # Parse timestamp
            timestamp = data.get('timestamp')
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif isinstance(timestamp, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp)
            else:
                timestamp = datetime.now()

            # Create TickData
            tick = TickData(
                symbol=data.get('symbol', ''),
                timestamp=timestamp,
                price=float(data.get('price', 0)),
                volume=int(data.get('volume', 0)),
                bid=float(data.get('bid')) if data.get('bid') else None,
                ask=float(data.get('ask')) if data.get('ask') else None,
                bid_size=int(data.get('bid_size')) if data.get('bid_size') else None,
                ask_size=int(data.get('ask_size')) if data.get('ask_size') else None,
            )

            return tick

        except Exception as e:
            logger.error(f"Failed to parse tick data: {e}")
            return None

    async def stream(self) -> AsyncIterator[TickData]:
        """Async iterator for consuming ticks.

        Yields:
            TickData objects as they arrive

        Example:
            >>> async for tick in stream.stream():
            ...     print(f"Received: {tick}")
        """
        self._is_streaming = True

        while self._is_streaming:
            try:
                # Wait for tick with timeout
                tick = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                yield tick
            except asyncio.TimeoutError:
                # Continue looping
                continue
            except Exception as e:
                logger.error(f"Error in stream iteration: {e}")
                break

    def get_buffer(self, symbol: str) -> Optional[TickCircularBuffer]:
        """Get data buffer for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            TickCircularBuffer or None if symbol not found

        Example:
            >>> buffer = stream.get_buffer('AAPL')
            >>> df = buffer.to_dataframe()
        """
        return self._buffers.get(symbol)

    def get_latest_ticks(self, symbol: str, n: int = 10) -> list[TickData]:
        """Get latest n ticks for a symbol.

        Args:
            symbol: Trading symbol
            n: Number of ticks to retrieve

        Returns:
            List of recent ticks

        Example:
            >>> recent = stream.get_latest_ticks('AAPL', 10)
        """
        buffer = self.get_buffer(symbol)
        if buffer:
            return buffer.latest(n)
        return []

    @property
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._connection.is_connected

    @property
    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        return self._is_streaming

    @property
    def symbols_subscribed(self) -> list[str]:
        """Get list of subscribed symbols."""
        return self.symbols.copy()

    def __repr__(self) -> str:
        """String representation of stream."""
        status = "connected" if self.is_connected else "disconnected"
        return f"RealTimeDataStream(symbols={len(self.symbols)}, {status})"

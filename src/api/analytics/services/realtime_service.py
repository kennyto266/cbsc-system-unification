"""
Real-time data service for WebSocket connections
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional, Any
from dataclasses import dataclass, asdict
import websockets
from websockets.server import WebSocketServerProtocol

from ..models.analytics import RealTimeUpdate

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection"""
    websocket: WebSocketServerProtocol
    user_id: Optional[int] = None
    subscribed_strategies: Optional[Set[str]] = None
    subscribed_channels: Optional[Set[str]] = None
    last_ping: Optional[datetime] = None

    def __post_init__(self):
        if self.subscribed_strategies is None:
            self.subscribed_strategies = set()
        if self.subscribed_channels is None:
            self.subscribed_channels = set()


class RealTimeDataService:
    """Service for managing real-time data streaming"""

    def __init__(self):
        # Active connections
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[int, Set[str]] = {}  # user_id -> connection_ids
        self.strategy_subscribers: Dict[str, Set[str]] = {}  # strategy_id -> connection_ids

        # Background tasks
        self.background_tasks = set()

        # Event handlers
        self.event_handlers = {}

    async def register_connection(self, websocket: WebSocketServerProtocol) -> str:
        """
        Register a new WebSocket connection

        Args:
            websocket: WebSocket connection

        Returns:
            Connection ID
        """
        connection_id = f"conn_{len(self.connections)}_{datetime.now().timestamp()}"

        self.connections[connection_id] = ConnectionInfo(
            websocket=websocket,
            last_ping=datetime.utcnow()
        )

        logger.info(f"New WebSocket connection registered: {connection_id}")
        return connection_id

    async def unregister_connection(self, connection_id: str):
        """Unregister a WebSocket connection"""
        if connection_id in self.connections:
            conn_info = self.connections[connection_id]

            # Remove from user mappings
            if conn_info.user_id:
                if conn_info.user_id in self.user_connections:
                    self.user_connections[conn_info.user_id].discard(connection_id)
                    if not self.user_connections[conn_info.user_id]:
                        del self.user_connections[conn_info.user_id]

            # Remove from strategy subscriptions
            for strategy_id in conn_info.subscribed_strategies:
                if strategy_id in self.strategy_subscribers:
                    self.strategy_subscribers[strategy_id].discard(connection_id)
                    if not self.strategy_subscribers[strategy_id]:
                        del self.strategy_subscribers[strategy_id]

            del self.connections[connection_id]
            logger.info(f"WebSocket connection unregistered: {connection_id}")

    async def authenticate_connection(
        self,
        connection_id: str,
        user_id: int
    ):
        """
        Authenticate a connection with user ID

        Args:
            connection_id: Connection identifier
            user_id: User identifier
        """
        if connection_id in self.connections:
            self.connections[connection_id].user_id = user_id

            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)

            logger.info(f"Connection {connection_id} authenticated for user {user_id}")

    async def subscribe_to_strategy(
        self,
        connection_id: str,
        strategy_id: str
    ):
        """
        Subscribe connection to strategy updates

        Args:
            connection_id: Connection identifier
            strategy_id: Strategy identifier
        """
        if connection_id in self.connections:
            self.connections[connection_id].subscribed_strategies.add(strategy_id)

            if strategy_id not in self.strategy_subscribers:
                self.strategy_subscribers[strategy_id] = set()
            self.strategy_subscribers[strategy_id].add(connection_id)

            logger.info(f"Connection {connection_id} subscribed to strategy {strategy_id}")

    async def subscribe_to_channel(
        self,
        connection_id: str,
        channel: str
    ):
        """
        Subscribe connection to a channel

        Args:
            connection_id: Connection identifier
            channel: Channel name
        """
        if connection_id in self.connections:
            self.connections[connection_id].subscribed_channels.add(channel)
            logger.info(f"Connection {connection_id} subscribed to channel {channel}")

    async def broadcast_to_strategy(
        self,
        strategy_id: str,
        message: Dict[str, Any]
    ):
        """
        Broadcast message to all subscribers of a strategy

        Args:
            strategy_id: Strategy identifier
            message: Message to broadcast
        """
        if strategy_id not in self.strategy_subscribers:
            return

        update = RealTimeUpdate(
            type="strategy_update",
            strategy_id=strategy_id,
            data=message
        )

        await self._broadcast_to_connections(
            self.strategy_subscribers[strategy_id],
            update
        )

    async def broadcast_to_user(
        self,
        user_id: int,
        message: Dict[str, Any]
    ):
        """
        Broadcast message to all connections for a user

        Args:
            user_id: User identifier
            message: Message to broadcast
        """
        if user_id not in self.user_connections:
            return

        update = RealTimeUpdate(
            type="user_update",
            user_id=user_id,
            data=message
        )

        await self._broadcast_to_connections(
            self.user_connections[user_id],
            update
        )

    async def broadcast_to_channel(
        self,
        channel: str,
        message: Dict[str, Any]
    ):
        """
        Broadcast message to all subscribers of a channel

        Args:
            channel: Channel name
            message: Message to broadcast
        """
        # Find all connections subscribed to this channel
        subscribed_connections = set()
        for conn_id, conn_info in self.connections.items():
            if channel in conn_info.subscribed_channels:
                subscribed_connections.add(conn_id)

        if subscribed_connections:
            update = RealTimeUpdate(
                type="channel_update",
                data=message
            )

            await self._broadcast_to_connections(
                subscribed_connections,
                update
            )

    async def _broadcast_to_connections(
        self,
        connection_ids: Set[str],
        update: RealTimeUpdate
    ):
        """
        Broadcast update to specific connections

        Args:
            connection_ids: Set of connection IDs
            update: Update to broadcast
        """
        message = json.dumps(asdict(update), default=str)

        # Create tasks for parallel sending
        tasks = []
        for conn_id in connection_ids:
            if conn_id in self.connections:
                task = asyncio.create_task(
                    self._send_to_connection(self.connections[conn_id].websocket, message)
                )
                tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_to_connection(
        self,
        websocket: WebSocketServerProtocol,
        message: str
    ):
        """
        Send message to a specific WebSocket connection

        Args:
            websocket: WebSocket connection
            message: Message to send
        """
        try:
            await websocket.send(message)
        except websockets.exceptions.ConnectionClosed:
            pass  # Connection already closed
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")

    async def start_ping_interval(self, interval: int = 30):
        """
        Start periodic ping to keep connections alive

        Args:
            interval: Ping interval in seconds
        """
        async def ping_loop():
            while True:
                await asyncio.sleep(interval)
                await self._ping_all_connections()

        task = asyncio.create_task(ping_loop())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    async def _ping_all_connections(self):
        """Send ping to all active connections"""
        dead_connections = []

        for conn_id, conn_info in self.connections.items():
            try:
                # Check if connection is still alive
                if conn_info.last_ping and \
                   (datetime.utcnow() - conn_info.last_ping).seconds > 90:
                    dead_connections.append(conn_id)
                    continue

                await conn_info.websocket.ping()
                conn_info.last_ping = datetime.utcnow()

            except Exception:
                dead_connections.append(conn_id)

        # Clean up dead connections
        for conn_id in dead_connections:
            await self.unregister_connection(conn_id)

    async def get_connection_stats(self) -> Dict:
        """Get statistics about active connections"""
        total_connections = len(self.connections)
        authenticated_connections = sum(
            1 for conn in self.connections.values()
            if conn.user_id is not None
        )

        strategy_subscriptions = sum(
            len(conn.subscribed_strategies)
            for conn in self.connections.values()
        )

        channel_subscriptions = sum(
            len(conn.subscribed_channels)
            for conn in self.connections.values()
        )

        return {
            "total_connections": total_connections,
            "authenticated_connections": authenticated_connections,
            "unique_users": len(self.user_connections),
            "strategy_subscriptions": strategy_subscriptions,
            "channel_subscriptions": channel_subscriptions,
            "active_strategies": len(self.strategy_subscribers)
        }

    def register_event_handler(self, event_type: str, handler):
        """
        Register a handler for specific event types

        Args:
            event_type: Event type to handle
            handler: Handler function
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    async def handle_event(self, event_type: str, data: Dict):
        """
        Handle an event by calling registered handlers

        Args:
            event_type: Type of event
            data: Event data
        """
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")


# Global instance for the application
realtime_service = RealTimeDataService()
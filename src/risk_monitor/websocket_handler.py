"""
WebSocket Handler for Real-time Risk Data

This module implements WebSocket server for real-time risk monitoring:
- Risk metrics streaming
- Alert notifications
- Portfolio updates
- Client connection management
"""

import asyncio
import json
import logging
from typing import Dict, List, Set, Optional, Callable, Any
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed
import jwt
import threading
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types"""
    RISK_UPDATE = "risk_update"
    ALERT = "alert"
    PORTFOLIO_UPDATE = "portfolio_update"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    ACK = "acknowledgment"


@dataclass
class WSMessage:
    """WebSocket message structure"""
    type: MessageType
    data: Dict[str, Any]
    timestamp: datetime
    message_id: Optional[str] = None
    client_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
            "client_id": self.client_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WSMessage":
        """Create message from dictionary"""
        return cls(
            type=MessageType(data["type"]),
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            message_id=data.get("message_id"),
            client_id=data.get("client_id")
        )


class ClientSubscription:
    """Client subscription manager"""

    def __init__(self, client_id: str):
        """
        Initialize subscription manager

        Args:
            client_id: Unique client identifier
        """
        self.client_id = client_id
        self.subscriptions: Set[str] = set()
        self.last_heartbeat = datetime.now()
        self.active = True

    def subscribe(self, topic: str):
        """Subscribe to a topic"""
        self.subscriptions.add(topic)
        logger.debug(f"Client {self.client_id} subscribed to {topic}")

    def unsubscribe(self, topic: str):
        """Unsubscribe from a topic"""
        self.subscriptions.discard(topic)
        logger.debug(f"Client {self.client_id} unsubscribed from {topic}")

    def is_subscribed(self, topic: str) -> bool:
        """Check if subscribed to topic"""
        return topic in self.subscriptions

    def update_heartbeat(self):
        """Update last heartbeat time"""
        self.last_heartbeat = datetime.now()


class RiskWebSocketHandler:
    """WebSocket handler for risk monitoring"""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        max_connections: int = 100,
        auth_required: bool = True,
        jwt_secret: str = "your-secret-key",
        heartbeat_interval: int = 30
    ):
        """
        Initialize WebSocket handler

        Args:
            host: Server host
            port: Server port
            max_connections: Maximum concurrent connections
            auth_required: Whether authentication is required
            jwt_secret: JWT secret key for authentication
            heartbeat_interval: Heartbeat interval in seconds
        """
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.auth_required = auth_required
        self.jwt_secret = jwt_secret
        self.heartbeat_interval = heartbeat_interval

        # Client management
        self.clients: Dict[str, WebSocketServerProtocol] = {}
        self.subscriptions: Dict[str, ClientSubscription] = {}
        self.client_counter = 0

        # Message handlers
        self.message_handlers: Dict[MessageType, List[Callable]] = {
            msg_type: [] for msg_type in MessageType
        }

        # Background tasks
        self.server = None
        self.heartbeat_task = None
        self.running = False

    async def start_server(self):
        """Start the WebSocket server"""
        self.running = True

        # Start heartbeat task
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        # Start WebSocket server
        self.server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port,
            max_size=10 * 1024 * 1024,  # 10MB max message size
            ping_interval=20,
            ping_timeout=10
        )

        logger.info(f"WebSocket server started on {self.host}:{self.port}")

    async def stop_server(self):
        """Stop the WebSocket server"""
        self.running = False

        # Cancel heartbeat task
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        for client in self.clients.values():
            await client.close()

        # Stop server
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        logger.info("WebSocket server stopped")

    async def _handle_client(
        self,
        websocket: WebSocketServerProtocol,
        path: str
    ):
        """Handle new client connection"""
        # Check connection limit
        if len(self.clients) >= self.max_connections:
            await websocket.close(1013, "Server overload")
            return

        # Authenticate if required
        client_id = None
        if self.auth_required:
            client_id = await self._authenticate_client(websocket)
            if not client_id:
                await websocket.close(4001, "Authentication failed")
                return
        else:
            # Generate client ID
            self.client_counter += 1
            client_id = f"client_{self.client_counter}"

        # Register client
        self.clients[client_id] = websocket
        self.subscriptions[client_id] = ClientSubscription(client_id)

        logger.info(f"Client {client_id} connected from {websocket.remote_address}")

        try:
            # Send welcome message
            await self._send_message(
                websocket,
                WSMessage(
                    type=MessageType.ACK,
                    data={"client_id": client_id, "status": "connected"},
                    timestamp=datetime.now()
                )
            )

            # Handle messages
            async for message in websocket:
                await self._handle_message(client_id, message)

        except ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            # Cleanup
            self.clients.pop(client_id, None)
            self.subscriptions.pop(client_id, None)

    async def _authenticate_client(
        self,
        websocket: WebSocketServerProtocol
    ) -> Optional[str]:
        """Authenticate client connection"""
        try:
            # Get token from query parameters or initial message
            token = await websocket.recv()

            # Verify JWT token
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"]
            )

            return payload.get("client_id")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None

    async def _handle_message(
        self,
        client_id: str,
        raw_message: str
    ):
        """Handle incoming message from client"""
        try:
            # Parse message
            message_data = json.loads(raw_message)
            message = WSMessage.from_dict(message_data)
            message.client_id = client_id

            # Update heartbeat
            self.subscriptions[client_id].update_heartbeat()

            # Handle message type
            if message.type == MessageType.SUBSCRIBE:
                await self._handle_subscribe(client_id, message.data)
            elif message.type == MessageType.UNSUBSCRIBE:
                await self._handle_unsubscribe(client_id, message.data)
            elif message.type == MessageType.HEARTBEAT:
                await self._handle_heartbeat(client_id)
            else:
                # Call registered handlers
                for handler in self.message_handlers[message.type]:
                    try:
                        await handler(message)
                    except Exception as e:
                        logger.error(f"Error in message handler: {e}")

        except json.JSONDecodeError:
            await self._send_error(client_id, "Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self._send_error(client_id, str(e))

    async def _handle_subscribe(self, client_id: str, data: Dict[str, Any]):
        """Handle subscription request"""
        topic = data.get("topic")
        if topic:
            self.subscriptions[client_id].subscribe(topic)
            await self._send_message(
                self.clients[client_id],
                WSMessage(
                    type=MessageType.ACK,
                    data={"action": "subscribed", "topic": topic},
                    timestamp=datetime.now(),
                    client_id=client_id
                )
            )

    async def _handle_unsubscribe(self, client_id: str, data: Dict[str, Any]):
        """Handle unsubscription request"""
        topic = data.get("topic")
        if topic:
            self.subscriptions[client_id].unsubscribe(topic)
            await self._send_message(
                self.clients[client_id],
                WSMessage(
                    type=MessageType.ACK,
                    data={"action": "unsubscribed", "topic": topic},
                    timestamp=datetime.now(),
                    client_id=client_id
                )
            )

    async def _handle_heartbeat(self, client_id: str):
        """Handle heartbeat message"""
        # Heartbeat already updated in message handler
        pass

    async def _heartbeat_loop(self):
        """Send periodic heartbeats and check client connectivity"""
        while self.running:
            try:
                # Check client heartbeats
                current_time = datetime.now()
                timeout_threshold = timedelta(seconds=self.heartbeat_interval * 3)

                clients_to_remove = []
                for client_id, subscription in self.subscriptions.items():
                    if current_time - subscription.last_heartbeat > timeout_threshold:
                        clients_to_remove.append(client_id)

                # Remove inactive clients
                for client_id in clients_to_remove:
                    if client_id in self.clients:
                        await self.clients[client_id].close()
                        self.clients.pop(client_id, None)
                        self.subscriptions.pop(client_id, None)
                        logger.warning(f"Client {client_id} timeout, removed")

                # Send heartbeat to active clients
                heartbeat_msg = WSMessage(
                    type=MessageType.HEARTBEAT,
                    data={"timestamp": datetime.now().isoformat()},
                    timestamp=datetime.now()
                )

                for client_id, websocket in self.clients.items():
                    try:
                        await self._send_message(websocket, heartbeat_msg)
                    except ConnectionClosed:
                        # Client disconnected, will be cleaned up next loop
                        pass

                # Sleep until next heartbeat
                await asyncio.sleep(self.heartbeat_interval)

            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(5)

    async def _send_message(
        self,
        websocket: WebSocketServerProtocol,
        message: WSMessage
    ):
        """Send message to client"""
        try:
            await websocket.send(json.dumps(message.to_dict()))
        except ConnectionClosed:
            raise
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

    async def _send_error(self, client_id: str, error_message: str):
        """Send error message to client"""
        if client_id in self.clients:
            error_msg = WSMessage(
                type=MessageType.ERROR,
                data={"error": error_message},
                timestamp=datetime.now(),
                client_id=client_id
            )
            try:
                await self._send_message(self.clients[client_id], error_msg)
            except Exception:
                pass  # Client might be disconnected

    async def broadcast_risk_update(
        self,
        portfolio_id: str,
        risk_data: Dict[str, Any]
    ):
        """Broadcast risk metrics update"""
        message = WSMessage(
            type=MessageType.RISK_UPDATE,
            data={
                "portfolio_id": portfolio_id,
                "risk_metrics": risk_data
            },
            timestamp=datetime.now()
        )

        # Send to subscribed clients
        topic = f"risk:{portfolio_id}"
        await self._broadcast_to_subscribers(topic, message)

    async def broadcast_alert(
        self,
        alert_data: Dict[str, Any]
    ):
        """Broadcast alert notification"""
        message = WSMessage(
            type=MessageType.ALERT,
            data=alert_data,
            timestamp=datetime.now()
        )

        # Send to all clients subscribed to alerts
        await self._broadcast_to_subscribers("alerts", message)

        # Also send to portfolio-specific subscribers
        if "portfolio_id" in alert_data:
            portfolio_topic = f"alerts:{alert_data['portfolio_id']}"
            await self._broadcast_to_subscribers(portfolio_topic, message)

    async def broadcast_portfolio_update(
        self,
        portfolio_id: str,
        portfolio_data: Dict[str, Any]
    ):
        """Broadcast portfolio update"""
        message = WSMessage(
            type=MessageType.PORTFOLIO_UPDATE,
            data={
                "portfolio_id": portfolio_id,
                "portfolio_data": portfolio_data
            },
            timestamp=datetime.now()
        )

        # Send to subscribed clients
        topic = f"portfolio:{portfolio_id}"
        await self._broadcast_to_subscribers(topic, message)

    async def _broadcast_to_subscribers(
        self,
        topic: str,
        message: WSMessage
    ):
        """Broadcast message to subscribers of a topic"""
        disconnected_clients = []

        for client_id, subscription in self.subscriptions.items():
            if subscription.is_subscribed(topic) and client_id in self.clients:
                try:
                    await self._send_message(self.clients[client_id], message)
                except ConnectionClosed:
                    disconnected_clients.append(client_id)
                except Exception as e:
                    logger.error(f"Error broadcasting to client {client_id}: {e}")

        # Remove disconnected clients
        for client_id in disconnected_clients:
            self.clients.pop(client_id, None)
            self.subscriptions.pop(client_id, None)

    def add_message_handler(
        self,
        message_type: MessageType,
        handler: Callable[[WSMessage], Any]
    ):
        """Add custom message handler"""
        self.message_handlers[message_type].append(handler)
        logger.info(f"Added handler for {message_type.value}")

    def get_client_stats(self) -> Dict[str, Any]:
        """Get client connection statistics"""
        topic_counts = {}
        for subscription in self.subscriptions.values():
            for topic in subscription.subscriptions:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        return {
            "connected_clients": len(self.clients),
            "subscriptions": topic_counts,
            "max_connections": self.max_connections
        }

    async def send_message_to_client(
        self,
        client_id: str,
        message_type: MessageType,
        data: Dict[str, Any]
    ):
        """Send message to specific client"""
        if client_id in self.clients:
            message = WSMessage(
                type=message_type,
                data=data,
                timestamp=datetime.now(),
                client_id=client_id
            )
            await self._send_message(self.clients[client_id], message)

    def generate_client_token(
        self,
        client_id: str,
        expires_in: int = 3600
    ) -> str:
        """
        Generate JWT token for client authentication

        Args:
            client_id: Client identifier
            expires_in: Token expiration time in seconds

        Returns:
            JWT token string
        """
        payload = {
            "client_id": client_id,
            "exp": datetime.utcnow().timestamp() + expires_in,
            "iat": datetime.utcnow().timestamp()
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        return token

    async def send_personalized_alert(
        self,
        client_id: str,
        alert_data: Dict[str, Any]
    ):
        """Send personalized alert to specific client"""
        await self.send_message_to_client(
            client_id,
            MessageType.ALERT,
            alert_data
        )
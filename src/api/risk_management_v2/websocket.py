"""
Risk Management API v2 - WebSocket Handlers
===========================================

WebSocket handlers for real-time risk data streaming.

Author: CBSC Risk Management Team
Version: 2.0.0
"""

import asyncio
import json
import logging
from typing import Dict, List, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from .models import (
    WebSocketMessage, RiskUpdateMessage, AlertMessage, AdjustmentMessage
)
from .services import RiskMetricsService, AlertService, AdjustmentService

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        # Store active connections
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # Store subscriptions per connection
        self.subscriptions: Dict[str, Dict[str, Set[str]]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str):
        """Accept and track a new WebSocket connection"""
        await websocket.accept()

        # Store connection
        self.active_connections[user_id] = self.active_connections.get(user_id, {})
        self.active_connections[user_id][connection_id] = websocket

        # Initialize subscriptions for this connection
        if connection_id not in self.subscriptions:
            self.subscriptions[connection_id] = {
                "portfolios": set(),
                "strategies": set(),
                "alerts": True,
                "adjustments": True
            }

        # Store connection metadata
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.now(),
            "last_ping": datetime.now()
        }

        logger.info(f"WebSocket connected: {connection_id} for user {user_id}")

    def disconnect(self, connection_id: str, user_id: str):
        """Remove a WebSocket connection"""
        # Remove from active connections
        if user_id in self.active_connections:
            self.active_connections[user_id].pop(connection_id, None)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        # Remove subscriptions
        self.subscriptions.pop(connection_id, None)

        # Remove metadata
        self.connection_metadata.pop(connection_id, None)

        logger.info(f"WebSocket disconnected: {connection_id}")

    async def send_personal_message(self, message: dict, connection_id: str):
        """Send a message to a specific connection"""
        # Get connection from metadata
        metadata = self.connection_metadata.get(connection_id)
        if not metadata:
            return

        user_id = metadata["user_id"]
        websocket = self.active_connections.get(user_id, {}).get(connection_id)

        if websocket:
            try:
                await websocket.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                # Remove broken connection
                self.disconnect(connection_id, user_id)

    async def broadcast_to_subscribers(self, message: dict, message_type: str, target_id: str):
        """Broadcast message to all subscribers of a specific target"""
        disconnected = []

        for connection_id, subscriptions in self.subscriptions.items():
            metadata = self.connection_metadata.get(connection_id)
            if not metadata:
                continue

            user_id = metadata["user_id"]

            # Check if connection is subscribed to this target
            should_send = False

            if message_type == "risk_update":
                should_send = target_id in subscriptions["portfolios"]
            elif message_type == "alert":
                should_send = subscriptions.get("alerts", False)
            elif message_type == "adjustment":
                should_send = target_id in subscriptions["portfolios"] or subscriptions.get("adjustments", False)

            if should_send:
                websocket = self.active_connections.get(user_id, {}).get(connection_id)
                if websocket:
                    try:
                        await websocket.send_text(json.dumps(message, default=str))
                    except Exception as e:
                        logger.error(f"Error broadcasting to {connection_id}: {e}")
                        disconnected.append((connection_id, user_id))

        # Clean up disconnected connections
        for connection_id, user_id in disconnected:
            self.disconnect(connection_id, user_id)

    async def subscribe(self, connection_id: str, subscription_type: str, target_id: str = None):
        """Subscribe a connection to specific updates"""
        if connection_id not in self.subscriptions:
            return

        if subscription_type == "portfolio":
            self.subscriptions[connection_id]["portfolios"].add(target_id)
        elif subscription_type == "strategy":
            self.subscriptions[connection_id]["strategies"].add(target_id)
        elif subscription_type == "alerts":
            self.subscriptions[connection_id]["alerts"] = True
        elif subscription_type == "adjustments":
            self.subscriptions[connection_id]["adjustments"] = True

        logger.info(f"Connection {connection_id} subscribed to {subscription_type}: {target_id}")

    async def unsubscribe(self, connection_id: str, subscription_type: str, target_id: str = None):
        """Unsubscribe a connection from specific updates"""
        if connection_id not in self.subscriptions:
            return

        if subscription_type == "portfolio" and target_id:
            self.subscriptions[connection_id]["portfolios"].discard(target_id)
        elif subscription_type == "strategy" and target_id:
            self.subscriptions[connection_id]["strategies"].discard(target_id)
        elif subscription_type == "alerts":
            self.subscriptions[connection_id]["alerts"] = False
        elif subscription_type == "adjustments":
            self.subscriptions[connection_id]["adjustments"] = False

        logger.info(f"Connection {connection_id} unsubscribed from {subscription_type}: {target_id}")

    def get_connection_stats(self) -> dict:
        """Get statistics about active connections"""
        total_connections = sum(len(connections) for connections in self.active_connections.values())

        return {
            "total_connections": total_connections,
            "active_users": len(self.active_connections),
            "subscriptions": {
                "portfolio_subscribers": len([
                    s for s in self.subscriptions.values()
                    if s["portfolios"]
                ]),
                "alert_subscribers": len([
                    s for s in self.subscriptions.values()
                    if s["alerts"]
                ]),
                "adjustment_subscribers": len([
                    s for s in self.subscriptions.values()
                    if s["adjustments"]
                ])
            }
        }


# Global connection manager
manager = ConnectionManager()


async def websocket_risk_monitoring(websocket: WebSocket, connection_id: str, user_id: str):
    """
    WebSocket endpoint for real-time risk monitoring
    """
    await manager.connect(websocket, connection_id, user_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            message_type = message.get("type")

            if message_type == "subscribe":
                subscription_type = message.get("subscription_type")
                target_id = message.get("target_id")
                await manager.subscribe(connection_id, subscription_type, target_id)

                # Send confirmation
                await manager.send_personal_message(
                    {
                        "type": "subscription_confirmed",
                        "subscription_type": subscription_type,
                        "target_id": target_id
                    },
                    connection_id
                )

            elif message_type == "unsubscribe":
                subscription_type = message.get("subscription_type")
                target_id = message.get("target_id")
                await manager.unsubscribe(connection_id, subscription_type, target_id)

                # Send confirmation
                await manager.send_personal_message(
                    {
                        "type": "unsubscription_confirmed",
                        "subscription_type": subscription_type,
                        "target_id": target_id
                    },
                    connection_id
                )

            elif message_type == "ping":
                # Update last ping time
                if connection_id in manager.connection_metadata:
                    manager.connection_metadata[connection_id]["last_ping"] = datetime.now()

                # Send pong
                await manager.send_personal_message(
                    {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    },
                    connection_id
                )

    except WebSocketDisconnect:
        manager.disconnect(connection_id, user_id)
    except Exception as e:
        logger.error(f"Error in WebSocket connection {connection_id}: {e}")
        manager.disconnect(connection_id, user_id)


async def websocket_alert_stream(websocket: WebSocket, connection_id: str, user_id: str):
    """
    WebSocket endpoint for real-time alert streaming
    """
    await manager.connect(websocket, connection_id, user_id)

    # Auto-subscribe to alerts
    await manager.subscribe(connection_id, "alerts")

    try:
        while True:
            # Keep connection alive with ping/pong
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(connection_id, user_id)
    except Exception as e:
        logger.error(f"Error in alert WebSocket {connection_id}: {e}")
        manager.disconnect(connection_id, user_id)


# Broadcast functions for services

async def broadcast_risk_update(portfolio_id: str, risk_metrics: dict):
    """
    Broadcast risk metrics update to all subscribers
    """
    message = RiskUpdateMessage(
        type="risk_update",
        timestamp=datetime.now(),
        portfolio_id=portfolio_id,
        risk_metrics=risk_metrics
    )

    await manager.broadcast_to_subscribers(
        message.dict(),
        "risk_update",
        portfolio_id
    )


async def broadcast_alert(alert: dict):
    """
    Broadcast alert to all subscribers
    """
    message = AlertMessage(
        type="alert",
        timestamp=datetime.now(),
        alert=alert
    )

    await manager.broadcast_to_subscribers(
        message.dict(),
        "alert",
        "global"
    )


async def broadcast_adjustment(portfolio_id: str, adjustment: dict):
    """
    Broadcast adjustment to all subscribers
    """
    message = AdjustmentMessage(
        type="adjustment",
        timestamp=datetime.now(),
        portfolio_id=portfolio_id,
        adjustment=adjustment
    )

    await manager.broadcast_to_subscribers(
        message.dict(),
        "adjustment",
        portfolio_id
    )


# Background task for connection health monitoring

async def monitor_connection_health():
    """
    Monitor WebSocket connection health and clean up stale connections
    """
    while True:
        try:
            current_time = datetime.now()
            stale_connections = []

            # Check for stale connections (no ping for 5 minutes)
            for connection_id, metadata in manager.connection_metadata.items():
                last_ping = metadata["last_ping"]
                if (current_time - last_ping).seconds > 300:  # 5 minutes
                    stale_connections.append((connection_id, metadata["user_id"]))

            # Clean up stale connections
            for connection_id, user_id in stale_connections:
                logger.warning(f"Removing stale connection: {connection_id}")
                manager.disconnect(connection_id, user_id)

            # Sleep for 1 minute before next check
            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"Error in connection health monitor: {e}")
            await asyncio.sleep(60)


# Heartbeat task for active connections

async def send_heartbeat_to_connections():
    """
    Send periodic heartbeat messages to all active connections
    """
    while True:
        try:
            current_time = datetime.now()
            heartbeat_message = {
                "type": "heartbeat",
                "timestamp": current_time.isoformat(),
                "server_time": current_time.isoformat(),
                "connection_stats": manager.get_connection_stats()
            }

            # Send to all connections
            for user_id, connections in manager.active_connections.items():
                for connection_id, websocket in connections.items():
                    try:
                        await websocket.send_text(json.dumps(heartbeat_message, default=str))
                    except Exception as e:
                        logger.error(f"Error sending heartbeat to {connection_id}: {e}")

            # Sleep for 30 seconds before next heartbeat
            await asyncio.sleep(30)

        except Exception as e:
            logger.error(f"Error in heartbeat task: {e}")
            await asyncio.sleep(30)
"""
WebSocket server for real-time backtest monitoring updates.

Provides live streaming of:
- Progress updates
- Resource utilization metrics
- System alerts
- Task status changes
- Performance statistics
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
import websockets
from websockets.server import WebSocketServerProtocol
from dataclasses import asdict
import threading
import time

from .monitor import get_monitor, Alert, TaskProgress, ResourceMetrics


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self._server = None
        self._running = False
        self._broadcast_task = None

    async def start_server(self):
        """Start the WebSocket server."""
        if self._running:
            return

        self._running = True
        self._server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        )

        # Start broadcast task
        self._broadcast_task = asyncio.create_task(self._broadcast_loop())

        logging.info(f"WebSocket server started on ws://{self.host}:{self.port}")

    async def stop_server(self):
        """Stop the WebSocket server."""
        if not self._running:
            return

        self._running = False

        # Close all client connections
        for client in list(self.clients):
            try:
                await client.close()
            except Exception:
                pass

        self.clients.clear()

        # Cancel broadcast task
        if self._broadcast_task:
            self._broadcast_task.cancel()

        # Stop server
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        logging.info("WebSocket server stopped")

    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket client connection."""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}:{id(websocket)}"
        logging.info(f"Client connected: {client_id}")

        self.clients.add(websocket)

        try:
            # Send initial status
            await self._send_initial_status(websocket)

            # Handle incoming messages
            async for message in websocket:
                await self._handle_message(websocket, message)

        except websockets.exceptions.ConnectionClosed:
            logging.info(f"Client disconnected: {client_id}")
        except Exception as e:
            logging.error(f"Client handler error: {e}")
        finally:
            self.clients.discard(websocket)

    async def _send_initial_status(self, websocket: WebSocketServerProtocol):
        """Send initial status to newly connected client."""
        try:
            monitor = get_monitor()
            status = monitor.get_status_report()

            initial_message = {
                "type": "initial_status",
                "timestamp": datetime.now().isoformat(),
                "data": status
            }

            await websocket.send(json.dumps(initial_message, default=str))
        except Exception as e:
            logging.error(f"Error sending initial status: {e}")

    async def _handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle incoming message from client."""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "get_status":
                await self._send_status_update(websocket)
            elif message_type == "get_history":
                await self._send_history_data(websocket, data.get("duration", 300))
            elif message_type == "acknowledge_alert":
                await self._acknowledge_alert(data.get("alert_id"))
            else:
                logging.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            logging.error("Invalid JSON message received")
        except Exception as e:
            logging.error(f"Error handling message: {e}")

    async def _send_status_update(self, websocket: WebSocketServerProtocol):
        """Send current status update to specific client."""
        try:
            monitor = get_monitor()
            status = monitor.get_status_report()

            message = {
                "type": "status_update",
                "timestamp": datetime.now().isoformat(),
                "data": status
            }

            await websocket.send(json.dumps(message, default=str))
        except Exception as e:
            logging.error(f"Error sending status update: {e}")

    async def _send_history_data(self, websocket: WebSocketServerProtocol, duration_seconds: int):
        """Send historical resource data."""
        try:
            monitor = get_monitor()
            resource_history = list(monitor.resource_monitor.metrics_history)

            # Filter by duration
            cutoff_time = datetime.now().timestamp() - duration_seconds
            filtered_history = [
                asdict(m) for m in resource_history
                if m.timestamp.timestamp() >= cutoff_time
            ]

            message = {
                "type": "resource_history",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "duration": duration_seconds,
                    "metrics": filtered_history
                }
            }

            await websocket.send(json.dumps(message, default=str))
        except Exception as e:
            logging.error(f"Error sending history data: {e}")

    async def _acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert."""
        try:
            monitor = get_monitor()
            monitor.alert_manager.acknowledge_alert(alert_id)

            # Broadcast alert acknowledgment
            await self._broadcast_alert_acknowledgment(alert_id)
        except Exception as e:
            logging.error(f"Error acknowledging alert: {e}")

    async def _broadcast_loop(self):
        """Main broadcast loop for sending periodic updates."""
        while self._running:
            try:
                if self.clients:
                    await self._broadcast_status_update()

                await asyncio.sleep(2.0)  # Update every 2 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Broadcast loop error: {e}")

    async def _broadcast_status_update(self):
        """Broadcast status update to all connected clients."""
        if not self.clients:
            return

        try:
            monitor = get_monitor()
            status = monitor.get_status_report()

            message = {
                "type": "status_update",
                "timestamp": datetime.now().isoformat(),
                "data": status
            }

            await self._broadcast_message(message)
        except Exception as e:
            logging.error(f"Error broadcasting status update: {e}")

    async def _broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        if not self.clients:
            return

        message_str = json.dumps(message, default=str)
        disconnected_clients = set()

        for client in self.clients:
            try:
                await client.send(message_str)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logging.error(f"Error broadcasting to client: {e}")
                disconnected_clients.add(client)

        # Remove disconnected clients
        self.clients -= disconnected_clients

    async def broadcast_task_update(self, task: TaskProgress):
        """Broadcast task progress update."""
        message = {
            "type": "task_update",
            "timestamp": datetime.now().isoformat(),
            "data": asdict(task)
        }

        await self._broadcast_message(message)

    async def broadcast_alert(self, alert: Alert):
        """Broadcast new alert."""
        message = {
            "type": "new_alert",
            "timestamp": datetime.now().isoformat(),
            "data": asdict(alert)
        }

        await self._broadcast_message(message)

    async def _broadcast_alert_acknowledgment(self, alert_id: str):
        """Broadcast alert acknowledgment."""
        message = {
            "type": "alert_acknowledged",
            "timestamp": datetime.now().isoformat(),
            "data": {"alert_id": alert_id}
        }

        await self._broadcast_message(message)

    async def broadcast_resource_alert(self, alert_type: str, value: float, threshold: float):
        """Broadcast resource utilization alert."""
        message = {
            "type": "resource_alert",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "alert_type": alert_type,
                "current_value": value,
                "threshold": threshold,
                "severity": "warning" if value < threshold * 0.95 else "critical"
            }
        }

        await self._broadcast_message(message)

    def get_client_count(self) -> int:
        """Get number of connected clients."""
        return len(self.clients)


# Global WebSocket manager
_ws_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketManager()
    return _ws_manager


async def start_websocket_server(host: str = "localhost", port: int = 8765):
    """Start the WebSocket server."""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketManager(host, port)
    await _ws_manager.start_server()


async def stop_websocket_server():
    """Stop the WebSocket server."""
    global _ws_manager
    if _ws_manager:
        await _ws_manager.stop_server()
        _ws_manager = None


class MonitoringEventHandler:
    """Event handler that forwards monitor events to WebSocket clients."""

    def __init__(self, ws_manager: WebSocketManager):
        self.ws_manager = ws_manager

    async def handle_task_update(self, task: TaskProgress):
        """Handle task progress update."""
        await self.ws_manager.broadcast_task_update(task)

    async def handle_new_alert(self, alert: Alert):
        """Handle new alert."""
        await self.ws_manager.broadcast_alert(alert)

    async def handle_resource_alert(self, alert_type: str, value: float, threshold: float):
        """Handle resource utilization alert."""
        await self.ws_manager.broadcast_resource_alert(alert_type, value, threshold)


def run_websocket_server_in_thread(host: str = "localhost", port: int = 8765):
    """Run WebSocket server in a separate thread."""
    def run_server():
        asyncio.run(start_websocket_server(host, port))

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    return thread


def stop_websocket_server_in_thread():
    """Stop WebSocket server running in thread."""
    asyncio.run(stop_websocket_server())
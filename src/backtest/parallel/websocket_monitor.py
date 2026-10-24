#!/usr/bin/env python3
"""
Real-time WebSocket Monitoring Server

Provides WebSocket endpoints for live monitoring of parallel backtesting operations.
Integrates with enhanced ProgressTracker for accurate ETA calculations.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
import websockets
from websockets.server import WebSocketServerProtocol

from .monitor import BacktestMonitor, ProgressTracker, TaskStatus
from ..models import Task, TaskResult

logger = logging.getLogger(__name__)


@dataclass
class WebSocketMessage:
    """WebSocket message format."""
    type: str
    timestamp: str
    data: Dict[str, Any]


class MonitoringWebSocketServer:
    """
    Real-time monitoring server using WebSockets.

    Features:
    - Live progress updates
    - ETA predictions with accuracy tracking
    - Performance metrics streaming
    - Client connection management
    - Event filtering and subscriptions
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        monitor: Optional[BacktestMonitor] = None
    ):
        self.host = host
        self.port = port
        self.monitor = monitor or BacktestMonitor()
        self.progress_tracker = self.monitor.progress_tracker

        # Connection management
        self.clients: Set[WebSocketServerProtocol] = set()
        self.client_subscriptions: Dict[WebSocketServerProtocol, Set[str]] = {}

        # Server state
        self.server = None
        self.is_running = False
        self.broadcast_queue = asyncio.Queue()

        # Monitoring data cache
        self._last_broadcast_time = 0
        self._broadcast_interval = 1.0  # seconds
        self._performance_history = []
        self._max_history_size = 1000

        logger.info(f"WebSocket monitoring server initialized on {host}:{port}")

    async def start_server(self) -> None:
        """Start the WebSocket server."""
        try:
            self.server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )

            self.is_running = True

            # Start background tasks
            asyncio.create_task(self.broadcast_worker())
            asyncio.create_task(self.performance_monitor())

            logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")

        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            raise

    async def stop_server(self) -> None:
        """Stop the WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.is_running = False
            logger.info("WebSocket server stopped")

    async def handle_client(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """
        Handle new WebSocket client connection.

        Args:
            websocket: WebSocket connection
            path: Connection path (for routing)
        """
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}_{int(time.time())}"
        logger.info(f"New client connected: {client_id}")

        # Register client
        self.clients.add(websocket)
        self.client_subscriptions[websocket] = set()

        try:
            # Send initial status
            await self.send_initial_status(websocket)

            # Handle client messages
            async for message in websocket:
                try:
                    await self.handle_client_message(websocket, message)
                except Exception as e:
                    logger.error(f"Error handling message from {client_id}: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error in client handler for {client_id}: {e}")
        finally:
            # Cleanup client
            self.clients.discard(websocket)
            self.client_subscriptions.pop(websocket, None)

    async def send_initial_status(self, websocket: WebSocketServerProtocol) -> None:
        """Send initial monitoring status to new client."""
        try:
            # Get current status
            status = await self.get_comprehensive_status()

            message = WebSocketMessage(
                type="initial_status",
                timestamp=datetime.now(timezone.utc).isoformat(),
                data=status
            )

            await websocket.send(json.dumps(asdict(message), default=str))

        except Exception as e:
            logger.error(f"Failed to send initial status: {e}")

    async def handle_client_message(
        self,
        websocket: WebSocketServerProtocol,
        message: str
    ) -> None:
        """
        Handle incoming message from client.

        Args:
            websocket: Client connection
            message: JSON message
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "subscribe":
                # Handle subscription to specific events
                events = data.get("events", [])
                self.client_subscriptions[websocket].update(events)

                # Acknowledge subscription
                response = WebSocketMessage(
                    type="subscription_ack",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    data={"subscribed_events": list(self.client_subscriptions[websocket])}
                )
                await websocket.send(json.dumps(asdict(response), default=str))

            elif message_type == "get_status":
                # Send current status on demand
                status = await self.get_comprehensive_status()
                response = WebSocketMessage(
                    type="status_update",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    data=status
                )
                await websocket.send(json.dumps(asdict(response), default=str))

            elif message_type == "unsubscribe":
                # Handle unsubscription
                events = data.get("events", [])
                for event in events:
                    self.client_subscriptions[websocket].discard(event)

                response = WebSocketMessage(
                    type="unsubscription_ack",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    data={"unsubscribed_events": events}
                )
                await websocket.send(json.dumps(asdict(response), default=str))

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message from client: {message}")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")

    async def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status."""
        try:
            # Basic monitor status
            monitor_status = self.monitor.get_status()

            # Enhanced progress tracking
            progress_status = self.progress_tracker.get_overall_progress()

            # Performance metrics
            performance_metrics = self.progress_tracker.get_performance_metrics()

            # ETA accuracy
            eta_accuracy = self.progress_tracker.get_eta_accuracy()

            # Task details
            task_details = {}
            for task_id in self.progress_tracker.tasks:
                task_progress = self.progress_tracker.get_task_progress(task_id)
                if task_progress:
                    task_details[task_id] = {
                        "progress": task_progress.progress_percentage,
                        "eta": task_progress.eta.total_seconds() if task_progress.eta else None,
                        "status": task_progress.status.value,
                        "current_phase": task_progress.current_phase,
                        "message": task_progress.message
                    }

            # System resources
            system_load = self.monitor.system_monitor.get_current_load()

            return {
                "monitor": monitor_status,
                "progress": {
                    "overall": asdict(progress_status),
                    "tasks": task_details,
                    "eta_accuracy": eta_accuracy
                },
                "performance": performance_metrics,
                "system": system_load,
                "server_info": {
                    "uptime": time.time() - self._start_time if hasattr(self, '_start_time') else 0,
                    "connected_clients": len(self.clients),
                    "broadcast_interval": self._broadcast_interval
                }
            }

        except Exception as e:
            logger.error(f"Error getting comprehensive status: {e}")
            return {"error": str(e)}

    async def broadcast_worker(self) -> None:
        """Background worker for broadcasting updates."""
        self._start_time = time.time()

        while self.is_running:
            try:
                # Check if it's time to broadcast
                current_time = time.time()
                if current_time - self._last_broadcast_time >= self._broadcast_interval:

                    # Get current status
                    status = await self.get_comprehensive_status()

                    # Create broadcast message
                    message = WebSocketMessage(
                        type="status_update",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        data=status
                    )

                    # Queue for broadcasting
                    await self.broadcast_queue.put(message)
                    self._last_broadcast_time = current_time

                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in broadcast worker: {e}")
                await asyncio.sleep(1)

    async def performance_monitor(self) -> None:
        """Background performance monitoring and metrics collection."""
        while self.is_running:
            try:
                # Collect performance metrics
                performance_metrics = self.progress_tracker.get_performance_metrics()

                # Add timestamp
                performance_metrics["timestamp"] = time.time()

                # Store in history
                self._performance_history.append(performance_metrics)

                # Limit history size
                if len(self._performance_history) > self._max_history_size:
                    self._performance_history.pop(0)

                # Check for performance anomalies
                await self._detect_performance_anomalies(performance_metrics)

                # Sleep for monitoring interval
                await asyncio.sleep(5)  # Monitor every 5 seconds

            except Exception as e:
                logger.error(f"Error in performance monitor: {e}")
                await asyncio.sleep(10)

    async def _detect_performance_anomalies(self, metrics: Dict[str, Any]) -> None:
        """Detect and report performance anomalies."""
        try:
            # Check for high failure rate
            failure_rate = metrics.get("failure_rate", 0)
            if failure_rate > 0.1:  # 10% failure rate
                await self._broadcast_alert(
                    "high_failure_rate",
                    f"High failure rate detected: {failure_rate:.1%}",
                    {"failure_rate": failure_rate}
                )

            # Check for ETA accuracy degradation
            eta_accuracy = metrics.get("eta_accuracy", {})
            avg_error = eta_accuracy.get("average_error", 0)
            if avg_error > 300:  # 5 minutes average error
                await self._broadcast_alert(
                    "eta_accuracy_degraded",
                    f"ETA accuracy degraded: {avg_error:.1f}s average error",
                    {"average_error": avg_error}
                )

        except Exception as e:
            logger.error(f"Error detecting performance anomalies: {e}")

    async def _broadcast_alert(
        self,
        alert_type: str,
        message: str,
        data: Dict[str, Any]
    ) -> None:
        """Broadcast alert to all subscribed clients."""
        try:
            alert_message = WebSocketMessage(
                type="alert",
                timestamp=datetime.now(timezone.utc).isoformat(),
                data={
                    "alert_type": alert_type,
                    "message": message,
                    "data": data
                }
            )

            # Send to all clients
            if self.clients:
                await asyncio.gather(
                    *[client.send(json.dumps(asdict(alert_message), default=str))
                      for client in self.clients],
                    return_exceptions=True
                )

        except Exception as e:
            logger.error(f"Error broadcasting alert: {e}")

    async def broadcast_update(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Broadcast update to subscribed clients.

        Args:
            event_type: Type of event
            data: Event data
        """
        if not self.clients:
            return

        try:
            message = WebSocketMessage(
                type=event_type,
                timestamp=datetime.now(timezone.utc).isoformat(),
                data=data
            )

            # Send to subscribed clients
            tasks = []
            for client in self.clients:
                subscriptions = self.client_subscriptions.get(client, set())
                if not subscriptions or event_type in subscriptions:
                    tasks.append(
                        client.send(json.dumps(asdict(message), default=str))
                    )

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Error broadcasting update: {e}")

    # Integration methods with ParallelEngine

    async def notify_task_submitted(self, task: Task) -> None:
        """Notify clients of new task submission."""
        await self.broadcast_update("task_submitted", {
            "task_id": task.id,
            "type": task.type.value,
            "complexity": task.complexity.value,
            "priority": task.priority,
            "estimated_duration": task.estimated_duration.total_seconds() if task.estimated_duration else None
        })

    async def notify_task_started(self, task_id: str, process_id: int) -> None:
        """Notify clients of task start."""
        await self.broadcast_update("task_started", {
            "task_id": task_id,
            "process_id": process_id,
            "started_at": datetime.now(timezone.utc).isoformat()
        })

    async def notify_task_progress(
        self,
        task_id: str,
        progress: float,
        current_phase: str,
        message: Optional[str] = None
    ) -> None:
        """Notify clients of task progress update."""
        # Get ETA from progress tracker
        task_progress = self.progress_tracker.get_task_progress(task_id)
        eta_seconds = task_progress.eta.total_seconds() if task_progress and task_progress.eta else None

        await self.broadcast_update("task_progress", {
            "task_id": task_id,
            "progress": progress,
            "current_phase": current_phase,
            "message": message,
            "eta_seconds": eta_seconds
        })

    async def notify_task_completed(self, task_id: str, result: TaskResult) -> None:
        """Notify clients of task completion."""
        await self.broadcast_update("task_completed", {
            "task_id": task_id,
            "success": result.success,
            "execution_time": result.execution_time,
            "performance_metrics": result.performance_metrics
        })

    async def notify_task_failed(self, task_id: str, error: Exception) -> None:
        """Notify clients of task failure."""
        await self.broadcast_update("task_failed", {
            "task_id": task_id,
            "error_type": type(error).__name__,
            "error_message": str(error)
        })

    def get_performance_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent performance history."""
        return self._performance_history[-limit:]

    def get_server_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        return {
            "is_running": self.is_running,
            "connected_clients": len(self.clients),
            "host": self.host,
            "port": self.port,
            "uptime": time.time() - self._start_time if hasattr(self, '_start_time') else 0,
            "broadcast_queue_size": self.broadcast_queue.qsize(),
            "performance_history_size": len(self._performance_history)
        }


# Convenience function for creating and managing server
async def create_monitoring_server(
    host: str = "localhost",
    port: int = 8765,
    monitor: Optional[BacktestMonitor] = None
) -> MonitoringWebSocketServer:
    """
    Create and start a monitoring server.

    Args:
        host: Server host
        port: Server port
        monitor: BacktestMonitor instance

    Returns:
        Running MonitoringWebSocketServer instance
    """
    server = MonitoringWebSocketServer(host, port, monitor)
    await server.start_server()
    return server
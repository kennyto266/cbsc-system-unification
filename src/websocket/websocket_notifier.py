"""
WebSocket Notifier for VectorBT Multiprocess Engine
==================================================

Provides real-time notifications for backtest progress,
completion, and system events.
"""

import asyncio
import json
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Notification types"""
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    SYSTEM_ALERT = "system_alert"
    RESOURCE_WARNING = "resource_warning"
    PERFORMANCE_UPDATE = "performance_update"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class NotificationMessage:
    """WebSocket notification message"""
    id: str
    type: NotificationType
    timestamp: datetime
    task_id: Optional[str] = None
    message: str
    data: Optional[Dict] = None
    severity: str = "info"  # info, warning, error, critical


class WebSocketNotifier:
    """Manages WebSocket connections and broadcasts notifications"""

    def __init__(self):
        self.connections: Dict[str, Set] = {}  # connection_id -> set of websockets
        self.subscriptions: Dict[str, Set[str]] = {}  # task_id -> set of connection_ids
        self.message_history: List[NotificationMessage] = []
        self.max_history = 1000
        self._connection_counter = 0

        # Notification queues for different types
        self.notification_queues = {
            NotificationType.TASK_STARTED: asyncio.Queue(),
            NotificationType.TASK_PROGRESS: asyncio.Queue(),
            NotificationType.TASK_COMPLETED: asyncio.Queue(),
            NotificationType.TASK_FAILED: asyncio.Queue(),
            NotificationType.SYSTEM_ALERT: asyncio.Queue(),
            NotificationType.RESOURCE_WARNING: asyncio.Queue()
        }

        # Broadcast workers
        self._broadcast_tasks: List[asyncio.Task] = []
        self._running = False

    async def start(self):
        """Start the WebSocket notifier"""
        if self._running:
            return

        self._running = True
        logger.info("WebSocket notifier started")

        # Start broadcast workers for high-volume notifications
        for notification_type in [
            NotificationType.TASK_PROGRESS,
            NotificationType.RESOURCE_WARNING
        ]:
            task = asyncio.create_task(
                self._broadcast_worker(notification_type)
            )
            self._broadcast_tasks.append(task)

    async def stop(self):
        """Stop the WebSocket notifier"""
        self._running = False

        # Cancel broadcast workers
        for task in self._broadcast_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Close all connections
        for connection_set in self.connections.values():
            for websocket in connection_set:
                try:
                    await websocket.close()
                except:
                    pass

        self.connections.clear()
        logger.info("WebSocket notifier stopped")

    def register_connection(self, websocket, connection_id: Optional[str] = None) -> str:
        """Register a new WebSocket connection"""
        if connection_id is None:
            self._connection_counter += 1
            connection_id = f"conn_{self._connection_counter}_{uuid.uuid4().hex[:8]}"

        if connection_id not in self.connections:
            self.connections[connection_id] = set()

        self.connections[connection_id].add(websocket)
        logger.info(f"Registered WebSocket connection: {connection_id}")

        # Send welcome message
        asyncio.create_task(
            self._send_to_connection(connection_id, {
                "type": "connection_established",
                "connection_id": connection_id,
                "timestamp": datetime.now().isoformat(),
                "message": "WebSocket connection established"
            })
        )

        return connection_id

    def unregister_connection(self, connection_id: str):
        """Unregister a WebSocket connection"""
        if connection_id in self.connections:
            # Remove from all subscriptions
            for task_id, subscribers in self.subscriptions.items():
                if connection_id in subscribers:
                    subscribers.remove(connection_id)

            # Close websockets
            for websocket in self.connections[connection_id]:
                try:
                    asyncio.create_task(websocket.close())
                except:
                    pass

            del self.connections[connection_id]
            logger.info(f"Unregistered WebSocket connection: {connection_id}")

    def subscribe_to_task(self, connection_id: str, task_id: str):
        """Subscribe a connection to task notifications"""
        if task_id not in self.subscriptions:
            self.subscriptions[task_id] = set()

        self.subscriptions[task_id].add(connection_id)
        logger.debug(f"Connection {connection_id} subscribed to task {task_id}")

    def unsubscribe_from_task(self, connection_id: str, task_id: str):
        """Unsubscribe a connection from task notifications"""
        if task_id in self.subscriptions and connection_id in self.subscriptions[task_id]:
            self.subscriptions[task_id].remove(connection_id)
            logger.debug(f"Connection {connection_id} unsubscribed from task {task_id}")

    async def notify_task_started(self, task_id: str, details: Dict = None):
        """Notify that a task has started"""
        message = NotificationMessage(
            id=str(uuid.uuid4()),
            type=NotificationType.TASK_STARTED,
            timestamp=datetime.now(),
            task_id=task_id,
            message=f"Backtest task {task_id} started",
            data=details or {}
        )
        await self._broadcast_notification(message)

    async def notify_progress(self, task_id: str, progress: float, details: Dict = None):
        """Notify task progress (0.0 to 1.0)"""
        message = NotificationMessage(
            id=str(uuid.uuid4()),
            type=NotificationType.TASK_PROGRESS,
            timestamp=datetime.now(),
            task_id=task_id,
            message=f"Task {task_id} progress: {progress:.1%}",
            data={
                "progress": progress,
                "percentage": int(progress * 100)
            }
        )

        if details:
            message.data.update(details)

        # Use queue for high-volume progress notifications
        await self.notification_queues[NotificationType.TASK_PROGRESS].put(message)

    async def notify_task_completed(self, task_id: str, results: Dict = None):
        """Notify that a task has completed"""
        message = NotificationMessage(
            id=str(uuid.uuid4()),
            type=NotificationType.TASK_COMPLETED,
            timestamp=datetime.now(),
            task_id=task_id,
            message=f"Backtest task {task_id} completed successfully",
            data=results or {}
        )
        await self._broadcast_notification(message)

    async def notify_task_failed(self, task_id: str, error: str, details: Dict = None):
        """Notify that a task has failed"""
        message = NotificationMessage(
            id=str(uuid.uuid4()),
            type=NotificationType.TASK_FAILED,
            timestamp=datetime.now(),
            task_id=task_id,
            message=f"Backtest task {task_id} failed: {error}",
            data={
                "error": error,
                "details": details or {}
            },
            severity="error"
        )
        await self._broadcast_notification(message)

    async def notify_task_cancelled(self, task_id: str):
        """Notify that a task has been cancelled"""
        message = NotificationMessage(
            id=str(uuid.uuid4()),
            type=NotificationType.TASK_CANCELLED,
            timestamp=datetime.now(),
            task_id=task_id,
            message=f"Backtest task {task_id} was cancelled",
            severity="warning"
        )
        await self._broadcast_notification(message)

    async def notify_system_alert(self, message: str, severity: str = "warning", data: Dict = None):
        """Send a system alert"""
        notification = NotificationMessage(
            id=str(uuid.uuid4()),
            type=NotificationType.SYSTEM_ALERT,
            timestamp=datetime.now(),
            message=message,
            data=data or {},
            severity=severity
        )
        await self._broadcast_notification(notification)

    async def notify_resource_warning(self, resource_type: str, usage: float, details: Dict = None):
        """Send a resource usage warning"""
        message = NotificationMessage(
            id=str(uuid.uuid4()),
            type=NotificationType.RESOURCE_WARNING,
            timestamp=datetime.now(),
            message=f"High {resource_type} usage: {usage:.1%}",
            data={
                "resource_type": resource_type,
                "usage": usage,
                "details": details or {}
            },
            severity="warning"
        )

        # Use queue for resource warnings
        await self.notification_queues[NotificationType.RESOURCE_WARNING].put(message)

    async def notify_performance_update(self, metrics: Dict):
        """Send performance metrics update"""
        message = NotificationMessage(
            id=str(uuid.uuid4()),
            type=NotificationType.PERFORMANCE_UPDATE,
            timestamp=datetime.now(),
            message="Performance metrics update",
            data=metrics,
            severity="info"
        )
        await self._broadcast_notification(message)

    async def notify_error_occurred(self, error: str, context: Dict = None):
        """Send error notification"""
        message = NotificationMessage(
            id=str(uuid.uuid4()),
            type=NotificationType.ERROR_OCCURRED,
            timestamp=datetime.now(),
            message=f"Error occurred: {error}",
            data={
                "error": error,
                "context": context or {}
            },
            severity="error"
        )
        await self._broadcast_notification(message)

    async def _broadcast_notification(self, message: NotificationMessage):
        """Broadcast notification to relevant connections"""
        # Add to history
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]

        # Determine target connections
        target_connections = []

        if message.task_id:
            # Send to connections subscribed to this task
            subscribers = self.subscriptions.get(message.task_id, set())
            for conn_id in subscribers:
                if conn_id in self.connections:
                    target_connections.extend(self.connections[conn_id])
        else:
            # Send to all connections
            for connection_set in self.connections.values():
                target_connections.extend(connection_set)

        # Broadcast to all target connections
        if target_connections:
            await self._broadcast_to_connections(target_connections, message)

    async def _broadcast_to_connections(self, connections, message: NotificationMessage):
        """Broadcast message to specific connections"""
        message_dict = asdict(message)
        message_dict['timestamp'] = message.timestamp.isoformat()

        # Create broadcast tasks
        broadcast_tasks = []
        for websocket in connections:
            try:
                broadcast_tasks.append(
                    websocket.send_text(json.dumps(message_dict))
                )
            except Exception as e:
                logger.error(f"Error preparing broadcast: {e}")

        # Execute broadcasts concurrently
        if broadcast_tasks:
            results = await asyncio.gather(*broadcast_tasks, return_exceptions=True)

            # Handle any errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Broadcast error: {result}")

    async def _send_to_connection(self, connection_id: str, message: Dict):
        """Send message to specific connection"""
        if connection_id not in self.connections:
            return

        message_str = json.dumps({
            **message,
            "timestamp": datetime.now().isoformat() if "timestamp" not in message else message["timestamp"]
        })

        send_tasks = []
        for websocket in self.connections[connection_id]:
            try:
                send_tasks.append(websocket.send_text(message_str))
            except Exception as e:
                logger.error(f"Error preparing message: {e}")

        if send_tasks:
            await asyncio.gather(*send_tasks, return_exceptions=True)

    async def _broadcast_worker(self, notification_type: NotificationType):
        """Worker for broadcasting high-volume notifications"""
        queue = self.notification_queues[notification_type]

        while self._running:
            try:
                # Get message from queue
                message = await asyncio.wait_for(queue.get(), timeout=1.0)

                # Batch similar messages to reduce broadcast overhead
                batch = [message]
                try:
                    while True:
                        # Try to get more messages quickly
                        additional = await asyncio.wait_for(queue.get(), timeout=0.1)
                        if additional.type == notification_type:
                            batch.append(additional)
                except asyncio.TimeoutError:
                    pass

                # Send batch
                for msg in batch:
                    await self._broadcast_notification(msg)

            except asyncio.TimeoutError:
                # No messages, continue
                continue
            except Exception as e:
                logger.error(f"Error in broadcast worker for {notification_type}: {e}")

    def get_connection_stats(self) -> Dict:
        """Get connection statistics"""
        return {
            "total_connections": sum(len(conns) for conns in self.connections.values()),
            "active_connections": len(self.connections),
            "subscriptions": {
                task_id: len(subscribers)
                for task_id, subscribers in self.subscriptions.items()
            },
            "message_history_size": len(self.message_history)
        }

    def get_recent_messages(
        self,
        task_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get recent notification messages"""
        messages = self.message_history

        if task_id:
            messages = [m for m in messages if m.task_id == task_id]

        # Convert to dict and limit
        recent = messages[-limit:] if len(messages) > limit else messages
        return [
            {
                "id": m.id,
                "type": m.type.value,
                "timestamp": m.timestamp.isoformat(),
                "task_id": m.task_id,
                "message": m.message,
                "data": m.data,
                "severity": m.severity
            }
            for m in recent
        ]

    async def cleanup_disconnected(self):
        """Clean up disconnected websockets"""
        for connection_id, websockets in list(self.connections.items()):
            active_websockets = set()
            for ws in websockets:
                try:
                    # Test connection
                    if not ws.closed:
                        active_websockets.add(ws)
                except:
                    # Connection is broken
                    pass

            if active_websockets != websockets:
                self.connections[connection_id] = active_websockets
                if not active_websockets:
                    del self.connections[connection_id]

                logger.info(f"Cleaned up {len(websockets) - len(active_websockets)} "
                           f"disconnected websockets for {connection_id}")


# Global instance
notifier = WebSocketNotifier()
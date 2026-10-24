#!/usr/bin/env python3
"""
Enhanced Inter-Process Communication System
Integrates with Phase 2 IPC Synchronization components for 32-core processing
"""

import os
import sys
import time
import json
import mmap
import struct
import socket
import logging
import threading
import tempfile
import multiprocessing as mp
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
import psutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import Phase 2 synchronization components
try:
    from src.ipc import (
        DeadlockDetector, ResourceType, DeadlockResolution, Priority,
        SmartMessageQueue, MessagePriority, QueuePolicy
    )
    PHASE2_SYNC_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Phase 2 synchronization components not available: {e}")
    PHASE2_SYNC_AVAILABLE = False

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Enhanced message types for inter-process communication"""
    TASK_ASSIGNMENT = "task_assignment"
    TASK_RESULT = "task_result"
    TASK_ERROR = "task_error"
    HEARTBEAT = "heartbeat"
    SHUTDOWN = "shutdown"
    DATA_REQUEST = "data_request"
    DATA_RESPONSE = "data_response"
    PROGRESS_UPDATE = "progress_update"
    RESOURCE_UPDATE = "resource_update"
    DEADLOCK_NOTIFICATION = "deadlock_notification"
    SYNC_COORDINATION = "sync_coordination"
    MEMORY_PRESSURE = "memory_pressure"
    SYSTEM_STATUS = "system_status"


@dataclass
class IPCMessage:
    """Enhanced inter-process communication message"""
    message_id: str
    message_type: MessageType
    sender_id: int
    receiver_id: Optional[int]
    timestamp: datetime
    payload: Dict[str, Any]
    priority: int = 1
    requires_ack: bool = False
    correlation_id: Optional[str] = None
    deadline: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class SharedMemoryBlock:
    """Shared memory block information"""
    block_id: str
    size_bytes: int
    creator_id: int
    access_count: int = 0
    created_at: datetime = None
    last_accessed: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_accessed is None:
            self.last_accessed = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class EnhancedInterProcessCommunication:
    """
    Enhanced IPC system with Phase 2 synchronization

    New features:
    - Integrated deadlock detection and resolution
    - Smart message queuing with backpressure
    - Resource tracking for deadlock prevention
    - Advanced retry logic and failure recovery
    - Real-time performance monitoring
    - Circuit breaker for fault tolerance
    """

    def __init__(
        self,
        process_id: int,
        max_shared_memory_mb: int = 1024,
        message_queue_size: int = 10000,
        enable_compression: bool = True,
        heartbeat_interval: float = 1.0,
        enable_deadlock_detection: Optional[bool] = None,
        enable_smart_queuing: Optional[bool] = None,
        deadlock_detection_interval: float = 1.0,
        smart_queue_max_size: int = 10000
    ):
        self.process_id = process_id
        self.max_shared_memory_bytes = max_shared_memory_mb * 1024 * 1024
        self.message_queue_size = message_queue_size
        self.enable_compression = enable_compression
        self.heartbeat_interval = heartbeat_interval

        # Phase 2 features (auto-detect if not specified)
        self.enable_deadlock_detection = (
            enable_deadlock_detection if enable_deadlock_detection is not None
            else PHASE2_SYNC_AVAILABLE
        )
        self.enable_smart_queuing = (
            enable_smart_queuing if enable_smart_queuing is not None
            else PHASE2_SYNC_AVAILABLE
        )

        # Shared memory management
        self.shared_memory_blocks: Dict[str, mp.shared_memory.SharedMemory] = {}
        self.shared_memory_info: Dict[str, SharedMemoryBlock] = {}
        self.shared_memory_usage = 0
        self.resource_lock = threading.RLock()

        # Traditional message queues (fallback)
        self.message_queues: Dict[int, mp.Queue] = {}
        self.broadcast_queue = mp.Queue(message_queue_size)

        # Smart message queue (Phase 2)
        self.smart_queue: Optional[SmartMessageQueue] = None
        if self.enable_smart_queuing:
            self.smart_queue = SmartMessageQueue(
                max_size=smart_queue_max_size,
                overflow_policy=QueuePolicy.THROTTLE_PRODUCERS,
                enable_backpressure=True,
                enable_metrics=True
            )

        # Deadlock detector (Phase 2)
        self.deadlock_detector: Optional[DeadlockDetector] = None
        if self.enable_deadlock_detection:
            self.deadlock_detector = DeadlockDetector(
                detection_interval_seconds=deadlock_detection_interval,
                enable_auto_resolution=True,
                resolution_strategy=DeadlockResolution.VICTIM_SELECTION
            )

        # Communication channels
        self.server_socket: Optional[socket.socket] = None
        self.client_sockets: Dict[int, socket.socket] = {}

        # Performance tracking
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'bytes_transferred': 0,
            'shared_memory_blocks_created': 0,
            'shared_memory_current_usage_mb': 0.0,
            'compression_ratio': 1.0,
            'average_message_latency_ms': 0.0,
            'peak_memory_usage_mb': 0.0,
            'deadlock_detections': 0,
            'circuit_breaker_trips': 0,
            'queue_overflows': 0
        }

        # Monitoring threads
        self.is_running = False
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.cleanup_thread: Optional[threading.Thread] = None
        self.message_processor_thread: Optional[threading.Thread] = None

        # Message handlers
        self.message_handlers: Dict[MessageType, Callable] = {}
        self._register_default_handlers()

        # Circuit breaker state
        self.circuit_breaker_open = False
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure: Optional[datetime] = None

        logger.info(f"Enhanced IPC initialized for process {process_id} with "
                   f"deadlock_detection={self.enable_deadlock_detection}, "
                   f"smart_queuing={self.enable_smart_queuing}")

    def start(self):
        """Start enhanced IPC system"""
        if self.is_running:
            logger.warning("IPC system is already running")
            return

        self.is_running = True

        # Start Phase 2 components
        if self.smart_queue:
            self.smart_queue.start()
            logger.info("Smart message queue started")

        if self.deadlock_detector:
            self.deadlock_detector.start()
            self.deadlock_detector.register_process(
                self.process_id,
                Priority.HIGH  # IPC system has high priority
            )
            logger.info("Deadlock detector started")

        # Start monitoring threads
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()

        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

        self.message_processor_thread = threading.Thread(target=self._message_processor_loop, daemon=True)
        self.message_processor_thread.start()

        logger.info(f"Enhanced IPC system started for process {self.process_id}")

    def stop(self):
        """Stop enhanced IPC system"""
        logger.info(f"Stopping enhanced IPC system for process {self.process_id}...")

        self.is_running = False

        # Send shutdown message
        self.broadcast_message(MessageType.SHUTDOWN, {})

        # Stop Phase 2 components
        if self.deadlock_detector:
            self.deadlock_detector.unregister_process(self.process_id)
            self.deadlock_detector.stop()

        if self.smart_queue:
            self.smart_queue.stop()

        # Close sockets
        for sock in self.client_sockets.values():
            sock.close()
        if self.server_socket:
            self.server_socket.close()

        # Cleanup shared memory
        self.cleanup_all_shared_memory()

        logger.info(f"Enhanced IPC system stopped for process {self.process_id}")

    def create_message_queue(self, process_id: int) -> mp.Queue:
        """Create a message queue for a specific process"""
        if process_id not in self.message_queues:
            self.message_queues[process_id] = mp.Queue(self.message_queue_size)
            logger.debug(f"Created message queue for process {process_id}")
        return self.message_queues[process_id]

    def send_message(
        self,
        receiver_id: int,
        message_type: MessageType,
        payload: Dict[str, Any],
        priority: int = 1,
        requires_ack: bool = False,
        deadline: Optional[datetime] = None,
        correlation_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Send enhanced message with deadlock prevention

        Args:
            receiver_id: Target process ID
            message_type: Type of message
            payload: Message payload
            priority: Message priority
            requires_ack: Whether acknowledgment is required
            deadline: Message deadline
            correlation_id: Correlation ID for request/response tracking

        Returns:
            Message ID or None if failed
        """
        # Check circuit breaker
        if self.circuit_breaker_open:
            logger.warning("Circuit breaker open - message rejected")
            self.stats['circuit_breaker_trips'] += 1
            return None

        message_id = f"msg_{int(time.time() * 1000000)}_{self.process_id}"

        message = IPCMessage(
            message_id=message_id,
            message_type=message_type,
            sender_id=self.process_id,
            receiver_id=receiver_id,
            timestamp=datetime.now(),
            payload=payload,
            priority=priority,
            requires_ack=requires_ack,
            deadline=deadline,
            correlation_id=correlation_id
        )

        try:
            # Use smart queue if available
            if self.smart_queue:
                return self._send_via_smart_queue(receiver_id, message)
            else:
                return self._send_via_traditional_queue(receiver_id, message)

        except Exception as e:
            logger.error(f"Failed to send message to process {receiver_id}: {e}")
            self._update_circuit_breaker(False)
            return None

    def _send_via_smart_queue(self, receiver_id: int, message: IPCMessage) -> Optional[str]:
        """Send message via smart queue with deadlock prevention"""
        try:
            # Register resource request with deadlock detector
            if self.deadlock_detector:
                queue_resource_id = f"queue_{receiver_id}"
                request_id = self.deadlock_detector.request_resource(
                    process_id=self.process_id,
                    resource_id=queue_resource_id,
                    resource_type=ResourceType.MESSAGE_QUEUE,
                    exclusive=False,
                    timeout_seconds=message.timeout_seconds if hasattr(message, 'timeout_seconds') else 30.0
                )

            # Convert message priority
            msg_priority = self._convert_priority(message.priority)

            # Send via smart queue
            message_payload = {
                'message': asdict(message),
                'target_process': receiver_id
            }

            queue_message_id = self.smart_queue.enqueue(
                payload=message_payload,
                priority=msg_priority,
                timeout_seconds=30.0,
                correlation_id=message.correlation_id
            )

            # Mark resource as acquired
            if self.deadlock_detector:
                self.deadlock_detector.acquire_resource(request_id)

            self.stats['messages_sent'] += 1
            logger.debug(f"Sent message {message.message_id} to process {receiver_id} via smart queue")
            return message_id

        except Exception as e:
            logger.error(f"Smart queue send failed: {e}")
            raise

    def _send_via_traditional_queue(self, receiver_id: int, message: IPCMessage) -> Optional[str]:
        """Send message via traditional queue"""
        # Serialize message
        serialized_msg = self._serialize_message(message)

        # Send to specific queue
        if receiver_id in self.message_queues:
            try:
                self.message_queues[receiver_id].put((message.priority, time.time(), serialized_msg), timeout=1.0)
                self.stats['messages_sent'] += 1
                self.stats['bytes_transferred'] += len(serialized_msg)
                logger.debug(f"Sent message {message.message_id} to process {receiver_id}")
                return message_id
            except Exception as e:
                logger.error(f"Failed to send message to process {receiver_id}: {e}")
                return None
        else:
            logger.warning(f"No message queue for process {receiver_id}")
            return None

    def _convert_priority(self, priority: int) -> MessagePriority:
        """Convert integer priority to MessagePriority enum"""
        if priority >= 5:
            return MessagePriority.URGENT
        elif priority >= 4:
            return MessagePriority.CRITICAL
        elif priority >= 3:
            return MessagePriority.HIGH
        elif priority >= 2:
            return MessagePriority.NORMAL
        else:
            return MessagePriority.LOW

    def broadcast_message(
        self,
        message_type: MessageType,
        payload: Dict[str, Any],
        priority: int = 1
    ) -> Optional[str]:
        """Broadcast message to all processes"""
        message_id = f"broadcast_{int(time.time() * 1000000)}_{self.process_id}"

        message = IPCMessage(
            message_id=message_id,
            message_type=message_type,
            sender_id=self.process_id,
            receiver_id=None,  # Broadcast
            timestamp=datetime.now(),
            payload=payload,
            priority=priority
        )

        try:
            if self.smart_queue:
                # Send via smart queue to all processes
                msg_priority = self._convert_priority(priority)
                queue_message_id = self.smart_queue.enqueue(
                    payload={
                        'message': asdict(message),
                        'broadcast': True
                    },
                    priority=msg_priority
                )
                self.stats['messages_sent'] += 1
                logger.debug(f"Broadcast message {message_id} via smart queue")
                return message_id
            else:
                # Traditional broadcast
                serialized_msg = self._serialize_message(message)
                self.broadcast_queue.put((priority, time.time(), serialized_msg), timeout=1.0)
                self.stats['messages_sent'] += 1
                self.stats['bytes_transferred'] += len(serialized_msg)
                logger.debug(f"Broadcast message {message_id}")
                return message_id

        except Exception as e:
            logger.error(f"Failed to broadcast message: {e}")
            self._update_circuit_breaker(False)
            return None

    def create_shared_memory(
        self,
        data: Any,
        block_id: Optional[str] = None,
        metadata: Dict[str, Any] = None,
        exclusive: bool = True
    ) -> Optional[str]:
        """
        Create shared memory block with deadlock prevention

        Args:
            data: Data to share
            block_id: Optional block ID
            metadata: Optional metadata
            exclusive: Whether exclusive access is required

        Returns:
            Shared memory block ID or None if failed
        """
        with self.resource_lock:
            if block_id is None:
                block_id = f"shm_{self.process_id}_{int(time.time() * 1000000)}"

            # Register resource request with deadlock detector
            if self.deadlock_detector:
                request_id = self.deadlock_detector.request_resource(
                    process_id=self.process_id,
                    resource_id=block_id,
                    resource_type=ResourceType.SHARED_MEMORY,
                    exclusive=exclusive,
                    timeout_seconds=10.0
                )

            try:
                # Serialize data
                serialized_data = self._serialize_data(data)

                # Check memory limits
                required_size = len(serialized_data)
                if self.shared_memory_usage + required_size > self.max_shared_memory_bytes:
                    # Try to free up memory
                    self._cleanup_unused_memory()
                    if self.shared_memory_usage + required_size > self.max_shared_memory_bytes:
                        raise MemoryError("Insufficient shared memory available")

                # Create shared memory block
                shm = mp.shared_memory.SharedMemory(create=True, size=required_size)
                shm.buf[:required_size] = serialized_data

                # Store references
                self.shared_memory_blocks[block_id] = shm
                self.shared_memory_info[block_id] = SharedMemoryBlock(
                    block_id=block_id,
                    size_bytes=required_size,
                    creator_id=self.process_id,
                    metadata=metadata or {}
                )

                self.shared_memory_usage += required_size

                # Mark resource as acquired
                if self.deadlock_detector:
                    self.deadlock_detector.acquire_resource(request_id)

                # Update statistics
                self.stats['shared_memory_blocks_created'] += 1
                self.stats['shared_memory_current_usage_mb'] = self.shared_memory_usage / (1024 * 1024)
                self.stats['peak_memory_usage_mb'] = max(
                    self.stats['peak_memory_usage_mb'],
                    self.shared_memory_usage / (1024 * 1024)
                )

                logger.debug(f"Created shared memory block {block_id} ({required_size} bytes)")
                return block_id

            except Exception as e:
                logger.error(f"Failed to create shared memory block: {e}")
                # Release resource request on failure
                if self.deadlock_detector:
                    self.deadlock_detector.release_resource_request(request_id)
                return None

    def access_shared_memory(self, block_id: str) -> Optional[Any]:
        """Access data from shared memory block"""
        with self.resource_lock:
            if block_id not in self.shared_memory_blocks:
                logger.warning(f"Shared memory block {block_id} not found")
                return None

            try:
                shm = self.shared_memory_blocks[block_id]
                shm_info = self.shared_memory_info[block_id]

                # Deserialize data
                data = self._deserialize_data(shm.buf[:shm_info.size_bytes])

                # Update access info
                shm_info.access_count += 1
                shm_info.last_accessed = datetime.now()

                return data

            except Exception as e:
                logger.error(f"Failed to access shared memory block {block_id}: {e}")
                return None

    def release_shared_memory(self, block_id: str) -> bool:
        """Release a shared memory block"""
        with self.resource_lock:
            if block_id not in self.shared_memory_blocks:
                logger.warning(f"Shared memory block {block_id} not found for release")
                return False

            try:
                shm = self.shared_memory_blocks[block_id]
                shm_info = self.shared_memory_info[block_id]

                # Release resource from deadlock detector
                if self.deadlock_detector:
                    self.deadlock_detector.release_resource_holder(block_id)

                # Close and unlink shared memory
                shm.close()
                shm.unlink()

                # Update usage tracking
                self.shared_memory_usage -= shm_info.size_bytes

                # Remove from tracking
                del self.shared_memory_blocks[block_id]
                del self.shared_memory_info[block_id]

                # Update statistics
                self.stats['shared_memory_current_usage_mb'] = self.shared_memory_usage / (1024 * 1024)

                logger.debug(f"Released shared memory block {block_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to release shared memory block {block_id}: {e}")
                return False

    def _update_circuit_breaker(self, success: bool):
        """Update circuit breaker state"""
        if success:
            self.circuit_breaker_failures = 0
            if self.circuit_breaker_open:
                logger.info("Circuit breaker closed")
                self.circuit_breaker_open = False
        else:
            self.circuit_breaker_failures += 1
            self.circuit_breaker_last_failure = datetime.now()

            # Open circuit breaker after 10 consecutive failures
            if self.circuit_breaker_failures >= 10:
                logger.warning("Circuit breaker opened due to consecutive failures")
                self.circuit_breaker_open = True

    def _heartbeat_loop(self):
        """Send periodic heartbeat messages"""
        while self.is_running:
            try:
                heartbeat_data = {
                    'timestamp': datetime.now().isoformat(),
                    'pid': os.getpid(),
                    'memory_usage_mb': psutil.Process().memory_info().rss / (1024 * 1024),
                    'cpu_percent': psutil.cpu_percent(interval=0.1),
                    'ipc_stats': self.stats.copy()
                }

                # Include deadlock detector stats if available
                if self.deadlock_detector:
                    deadlock_stats = self.deadlock_detector.get_statistics()
                    heartbeat_data['deadlock_stats'] = deadlock_stats

                self.broadcast_message(MessageType.HEARTBEAT, heartbeat_data)
                time.sleep(self.heartbeat_interval)

            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                time.sleep(self.heartbeat_interval)

    def _cleanup_loop(self):
        """Periodic cleanup of unused resources"""
        while self.is_running:
            try:
                # Cleanup old shared memory blocks
                self._cleanup_unused_memory()

                # Cleanup old messages from queues
                self._cleanup_old_messages()

                time.sleep(60)  # Cleanup every minute

            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                time.sleep(60)

    def _message_processor_loop(self):
        """Process incoming messages"""
        while self.is_running:
            try:
                # Process smart queue messages
                if self.smart_queue:
                    self._process_smart_queue_messages()

                # Process traditional queue messages
                self._process_traditional_messages()

                time.sleep(0.01)  # Small delay to prevent busy waiting

            except Exception as e:
                logger.error(f"Error in message processor loop: {e}")
                time.sleep(0.01)

    def _process_smart_queue_messages(self):
        """Process messages from smart queue"""
        if not self.smart_queue:
            return

        try:
            # Process messages in batches
            batch_size = 10
            processed = 0

            while processed < batch_size:
                message = self.smart_queue.dequeue(timeout_seconds=0.1)
                if message is None:
                    break

                try:
                    # Extract message data
                    if isinstance(message.payload, dict) and 'message' in message.payload:
                        message_data = message.payload['message']
                        is_broadcast = message.payload.get('broadcast', False)
                        target_process = message.payload.get('target_process')

                        # Deserialize IPC message
                        ipc_message = IPCMessage(
                            message_id=message_data['message_id'],
                            message_type=MessageType(message_data['message_type']),
                            sender_id=message_data['sender_id'],
                            receiver_id=message_data['receiver_id'],
                            timestamp=datetime.fromisoformat(message_data['timestamp']),
                            payload=message_data['payload'],
                            priority=message_data['priority'],
                            requires_ack=message_data['requires_ack'],
                            correlation_id=message_data.get('correlation_id')
                        )

                        # Check if message is for this process or broadcast
                        if (is_broadcast or
                            (target_process == self.process_id) or
                            (ipc_message.receiver_id == self.process_id or ipc_message.receiver_id is None)):
                            self._process_message(ipc_message)

                    processed += 1

                except Exception as e:
                    logger.error(f"Error processing smart queue message: {e}")

        except Exception as e:
            logger.error(f"Error in smart queue processing: {e}")

    def _process_traditional_messages(self):
        """Process messages from traditional queues"""
        try:
            # Check process-specific queues
            for process_id, queue in self.message_queues.items():
                try:
                    priority, timestamp, serialized_msg = queue.get_nowait()
                    message = self._deserialize_message(serialized_msg)
                    if message.receiver_id == self.process_id or message.receiver_id is None:
                        self._process_message(message)
                except:
                    pass  # No messages available

            # Check broadcast queue
            try:
                priority, timestamp, serialized_msg = self.broadcast_queue.get_nowait()
                message = self._deserialize_message(serialized_msg)
                if message.receiver_id is None or message.receiver_id == self.process_id:
                    self._process_message(message)
            except:
                pass  # No messages available

        except Exception as e:
            logger.error(f"Error in traditional message processing: {e}")

    def _process_message(self, message: IPCMessage):
        """Process a received message"""
        self.stats['messages_received'] += 1

        # Calculate message latency
        latency = (datetime.now() - message.timestamp).total_seconds() * 1000
        self.stats['average_message_latency_ms'] = (
            (self.stats['average_message_latency_ms'] + latency) / 2
        )

        # Handle deadlock notifications
        if (self.deadlock_detector and
            message.message_type == MessageType.DEADLOCK_NOTIFICATION):
            self._handle_deadlock_notification(message)
            return

        # Get handler for message type
        handler = self.message_handlers.get(message.message_type)
        if handler:
            try:
                handler(message)
                self._update_circuit_breaker(True)
            except Exception as e:
                logger.error(f"Error handling message {message.message_type}: {e}")
                self._update_circuit_breaker(False)
        else:
            logger.debug(f"No handler for message type {message.message_type}")

    def _handle_deadlock_notification(self, message: IPCMessage):
        """Handle deadlock notification"""
        self.stats['deadlock_detections'] += 1
        logger.warning(f"Deadlock notification received: {message.payload}")

        # Take appropriate action based on deadlock info
        deadlock_info = message.payload.get('deadlock_info', {})
        if 'victim_process' in deadlock_info and deadlock_info['victim_process'] == self.process_id:
            logger.critical("This process selected as deadlock victim - initiating graceful shutdown")
            # Implement graceful shutdown logic here

    def _register_default_handlers(self):
        """Register default message handlers"""
        self.message_handlers[MessageType.HEARTBEAT] = self._handle_heartbeat
        self.message_handlers[MessageType.SHUTDOWN] = self._handle_shutdown
        self.message_handlers[MessageType.DATA_REQUEST] = self._handle_data_request
        self.message_handlers[MessageType.PROGRESS_UPDATE] = self._handle_progress_update
        self.message_handlers[MessageType.RESOURCE_UPDATE] = self._handle_resource_update
        self.message_handlers[MessageType.DEADLOCK_NOTIFICATION] = self._handle_deadlock_notification

    def _handle_heartbeat(self, message: IPCMessage):
        """Handle heartbeat message"""
        logger.debug(f"Received heartbeat from process {message.sender_id}")

    def _handle_shutdown(self, message: IPCMessage):
        """Handle shutdown message"""
        logger.info(f"Received shutdown message from process {message.sender_id}")

    def _handle_data_request(self, message: IPCMessage):
        """Handle data request message"""
        logger.debug(f"Received data request from process {message.sender_id}")

    def _handle_progress_update(self, message: IPCMessage):
        """Handle progress update message"""
        logger.debug(f"Received progress update from process {message.sender_id}")

    def _handle_resource_update(self, message: IPCMessage):
        """Handle resource update message"""
        logger.debug(f"Received resource update from process {message.sender_id}")

    def _cleanup_unused_memory(self):
        """Cleanup unused shared memory blocks"""
        current_time = datetime.now()
        blocks_to_remove = []

        for block_id, block_info in self.shared_memory_info.items():
            # Remove blocks not accessed in the last 5 minutes
            if (current_time - block_info.last_accessed).total_seconds() > 300:
                # Only remove if we're not the creator or it was created more than 30 minutes ago
                if (block_info.creator_id != self.process_id or
                    (current_time - block_info.created_at).total_seconds() > 1800):
                    blocks_to_remove.append(block_id)

        for block_id in blocks_to_remove:
            self.release_shared_memory(block_id)
            logger.debug(f"Cleaned up unused shared memory block {block_id}")

    def _cleanup_old_messages(self):
        """Cleanup old messages from queues"""
        # Smart queue handles this automatically
        pass

    def cleanup_all_shared_memory(self):
        """Cleanup all shared memory blocks"""
        blocks_to_release = list(self.shared_memory_blocks.keys())
        for block_id in blocks_to_release:
            self.release_shared_memory(block_id)

        logger.info("Cleaned up all shared memory blocks")

    def _serialize_message(self, message: IPCMessage) -> bytes:
        """Serialize message to bytes"""
        message_dict = asdict(message)
        message_dict['timestamp'] = message.timestamp.isoformat()
        message_dict['message_type'] = message.message_type.value
        if message.deadline:
            message_dict['deadline'] = message.deadline.isoformat()

        serialized = json.dumps(message_dict).encode('utf-8')

        if self.enable_compression:
            import zlib
            compressed = zlib.compress(serialized, level=6)
            if len(compressed) < len(serialized):
                # Update compression ratio
                self.stats['compression_ratio'] = len(serialized) / len(compressed)
                return compressed

        return serialized

    def _deserialize_message(self, serialized_data: bytes) -> IPCMessage:
        """Deserialize message from bytes"""
        # Try to decompress if compression is enabled
        if self.enable_compression:
            try:
                import zlib
                decompressed = zlib.decompress(serialized_data)
                serialized_data = decompressed
            except:
                pass  # Data wasn't compressed

        message_dict = json.loads(serialized_data.decode('utf-8'))
        message_dict['timestamp'] = datetime.fromisoformat(message_dict['timestamp'])
        message_dict['message_type'] = MessageType(message_dict['message_type'])
        if message_dict.get('deadline'):
            message_dict['deadline'] = datetime.fromisoformat(message_dict['deadline'])

        return IPCMessage(**message_dict)

    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data for shared memory"""
        if isinstance(data, pd.DataFrame):
            # Use pickle for DataFrames
            import pickle
            return pickle.dumps(data)
        elif isinstance(data, np.ndarray):
            # Use numpy's native format
            return data.tobytes()
        elif isinstance(data, (list, dict, str, int, float, bool)):
            # Use pickle for Python objects
            import pickle
            return pickle.dumps(data)
        else:
            raise ValueError(f"Unsupported data type for serialization: {type(data)}")

    def _deserialize_data(self, serialized_data: bytes) -> Any:
        """Deserialize data from shared memory"""
        # Try different deserialization methods
        try:
            import pickle
            return pickle.loads(serialized_data)
        except:
            # If pickle fails, try to interpret as numpy array
            try:
                return np.frombuffer(serialized_data, dtype=np.float64)
            except:
                # Return raw bytes if all else fails
                return serialized_data

    def get_statistics(self) -> Dict[str, Any]:
        """Get enhanced IPC statistics"""
        stats = {
            'ipc_stats': self.stats.copy(),
            'shared_memory_blocks': len(self.shared_memory_blocks),
            'message_queues': len(self.message_queues),
            'is_running': self.is_running,
            'features_enabled': {
                'deadlock_detection': self.enable_deadlock_detection,
                'smart_queuing': self.enable_smart_queuing
            },
            'circuit_breaker_open': self.circuit_breaker_open
        }

        # Add Phase 2 component stats
        if self.deadlock_detector:
            stats['deadlock_detector_stats'] = self.deadlock_detector.get_statistics()

        if self.smart_queue:
            stats['smart_queue_metrics'] = self.smart_queue.get_metrics().to_dict()
            stats['smart_queue_status'] = self.smart_queue.get_status()

        return stats

    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Register a custom message handler"""
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for message type {message_type}")


# Utility functions for enhanced IPC setup
def create_enhanced_ipc_systems(
    process_count: int,
    memory_per_process_mb: int = 256,
    **kwargs
) -> List[EnhancedInterProcessCommunication]:
    """Create enhanced IPC systems for multiple processes"""
    ipc_systems = []

    for i in range(process_count):
        ipc = EnhancedInterProcessCommunication(
            process_id=i,
            max_shared_memory_mb=memory_per_process_mb,
            **kwargs
        )
        ipc_systems.append(ipc)

    return ipc_systems


def setup_enhanced_ipc_connections(ipc_systems: List[EnhancedInterProcessCommunication]):
    """Setup enhanced connections between IPC systems"""
    # Create message queues for each process
    for ipc in ipc_systems:
        for other_ipc in ipc_systems:
            if ipc.process_id != other_ipc.process_id:
                ipc.create_message_queue(other_ipc.process_id)

    logger.info(f"Setup enhanced IPC connections for {len(ipc_systems)} processes")


# Backward compatibility aliases
InterProcessCommunication = EnhancedInterProcessCommunication
create_ipc_systems = create_enhanced_ipc_systems
setup_ipc_connections = setup_enhanced_ipc_connections
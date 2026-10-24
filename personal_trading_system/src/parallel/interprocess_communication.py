#!/usr/bin/env python3
"""
Inter-Process Communication System
High-performance shared memory and message passing for 32-core parallel processing
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
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Message types for inter-process communication"""
    TASK_ASSIGNMENT = "task_assignment"
    TASK_RESULT = "task_result"
    TASK_ERROR = "task_error"
    HEARTBEAT = "heartbeat"
    SHUTDOWN = "shutdown"
    DATA_REQUEST = "data_request"
    DATA_RESPONSE = "data_response"
    PROGRESS_UPDATE = "progress_update"
    RESOURCE_UPDATE = "resource_update"


@dataclass
class IPCMessage:
    """Inter-process communication message"""
    message_id: str
    message_type: MessageType
    sender_id: int
    receiver_id: Optional[int]
    timestamp: datetime
    payload: Dict[str, Any]
    priority: int = 1
    requires_ack: bool = False


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


class InterProcessCommunication:
    """
    High-performance inter-process communication system

    Features:
    - Shared memory blocks for large data transfer
    - Message queuing for command and control
    - Zero-copy data sharing where possible
    - Automatic memory management and cleanup
    - Performance monitoring and optimization
    - Fault tolerance and recovery
    """

    def __init__(
        self,
        process_id: int,
        max_shared_memory_mb: int = 1024,
        message_queue_size: int = 10000,
        enable_compression: bool = True,
        heartbeat_interval: float = 1.0
    ):
        self.process_id = process_id
        self.max_shared_memory_bytes = max_shared_memory_mb * 1024 * 1024
        self.message_queue_size = message_queue_size
        self.enable_compression = enable_compression
        self.heartbeat_interval = heartbeat_interval

        # Shared memory management
        self.shared_memory_blocks: Dict[str, mp.shared_memory.SharedMemory] = {}
        self.shared_memory_info: Dict[str, SharedMemoryBlock] = {}
        self.shared_memory_usage = 0

        # Message queues
        self.message_queues: Dict[int, mp.Queue] = {}
        self.broadcast_queue = mp.Queue(message_queue_size)

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
            'peak_memory_usage_mb': 0.0
        }

        # Monitoring threads
        self.is_running = False
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.cleanup_thread: Optional[threading.Thread] = None
        self.message_processor_thread: Optional[threading.Thread] = None

        # Message handlers
        self.message_handlers: Dict[MessageType, Callable] = {}
        self._register_default_handlers()

        logger.info(f"IPC initialized for process {process_id} with {max_shared_memory_mb}MB shared memory")

    def start(self):
        """Start IPC system"""
        if self.is_running:
            logger.warning("IPC system is already running")
            return

        self.is_running = True

        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()

        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

        # Start message processor thread
        self.message_processor_thread = threading.Thread(target=self._message_processor_loop, daemon=True)
        self.message_processor_thread.start()

        logger.info(f"IPC system started for process {self.process_id}")

    def stop(self):
        """Stop IPC system"""
        logger.info(f"Stopping IPC system for process {self.process_id}...")

        self.is_running = False

        # Send shutdown message
        self.broadcast_message(MessageType.SHUTDOWN, {})

        # Close sockets
        for sock in self.client_sockets.values():
            sock.close()
        if self.server_socket:
            self.server_socket.close()

        # Cleanup shared memory
        self.cleanup_all_shared_memory()

        logger.info(f"IPC system stopped for process {self.process_id}")

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
        requires_ack: bool = False
    ) -> str:
        """
        Send a message to a specific process

        Args:
            receiver_id: Target process ID
            message_type: Type of message
            payload: Message payload
            priority: Message priority (higher = more important)
            requires_ack: Whether acknowledgment is required

        Returns:
            Message ID
        """
        message_id = f"msg_{int(time.time() * 1000000)}_{self.process_id}"

        message = IPCMessage(
            message_id=message_id,
            message_type=message_type,
            sender_id=self.process_id,
            receiver_id=receiver_id,
            timestamp=datetime.now(),
            payload=payload,
            priority=priority,
            requires_ack=requires_ack
        )

        # Serialize message
        serialized_msg = self._serialize_message(message)

        # Send to specific queue
        if receiver_id in self.message_queues:
            try:
                self.message_queues[receiver_id].put((priority, time.time(), serialized_msg), timeout=1.0)
                self.stats['messages_sent'] += 1
                self.stats['bytes_transferred'] += len(serialized_msg)
                logger.debug(f"Sent message {message_id} to process {receiver_id}")
                return message_id
            except Exception as e:
                logger.error(f"Failed to send message to process {receiver_id}: {e}")
                return None
        else:
            logger.warning(f"No message queue for process {receiver_id}")
            return None

    def broadcast_message(
        self,
        message_type: MessageType,
        payload: Dict[str, Any],
        priority: int = 1
    ) -> str:
        """
        Broadcast a message to all processes

        Args:
            message_type: Type of message
            payload: Message payload
            priority: Message priority

        Returns:
            Message ID
        """
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

        # Serialize and send to broadcast queue
        serialized_msg = self._serialize_message(message)
        try:
            self.broadcast_queue.put((priority, time.time(), serialized_msg), timeout=1.0)
            self.stats['messages_sent'] += 1
            self.stats['bytes_transferred'] += len(serialized_msg)
            logger.debug(f"Broadcast message {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"Failed to broadcast message: {e}")
            return None

    def create_shared_memory(
        self,
        data: Any,
        block_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Create shared memory block for large data

        Args:
            data: Data to share (DataFrame, array, etc.)
            block_id: Optional block ID
            metadata: Optional metadata

        Returns:
            Shared memory block ID
        """
        if block_id is None:
            block_id = f"shm_{self.process_id}_{int(time.time() * 1000000)}"

        # Serialize data
        serialized_data = self._serialize_data(data)

        # Check memory limits
        required_size = len(serialized_data)
        if self.shared_memory_usage + required_size > self.max_shared_memory_bytes:
            # Try to free up memory
            self._cleanup_unused_memory()
            if self.shared_memory_usage + required_size > self.max_shared_memory_bytes:
                raise MemoryError("Insufficient shared memory available")

        try:
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
            raise

    def access_shared_memory(self, block_id: str) -> Optional[Any]:
        """
        Access data from shared memory block

        Args:
            block_id: Shared memory block ID

        Returns:
            Deserialized data or None if not found
        """
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
        """
        Release a shared memory block

        Args:
            block_id: Shared memory block ID

        Returns:
            True if released successfully
        """
        if block_id not in self.shared_memory_blocks:
            logger.warning(f"Shared memory block {block_id} not found for release")
            return False

        try:
            shm = self.shared_memory_blocks[block_id]
            shm_info = self.shared_memory_info[block_id]

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

    def transfer_large_data(
        self,
        receiver_id: int,
        data: Any,
        data_description: str = ""
    ) -> str:
        """
        Transfer large data using shared memory

        Args:
            receiver_id: Target process ID
            data: Data to transfer
            data_description: Description of the data

        Returns:
            Transfer ID
        """
        transfer_id = f"transfer_{int(time.time() * 1000000)}"

        try:
            # Create shared memory block
            block_id = self.create_shared_memory(
                data=data,
                metadata={
                    'transfer_id': transfer_id,
                    'sender_id': self.process_id,
                    'receiver_id': receiver_id,
                    'description': data_description,
                    'created_at': datetime.now().isoformat()
                }
            )

            # Send notification message
            self.send_message(
                receiver_id=receiver_id,
                message_type=MessageType.DATA_RESPONSE,
                payload={
                    'transfer_id': transfer_id,
                    'block_id': block_id,
                    'data_description': data_description
                }
            )

            logger.debug(f"Initiated data transfer {transfer_id} to process {receiver_id}")
            return transfer_id

        except Exception as e:
            logger.error(f"Failed to transfer data to process {receiver_id}: {e}")
            return None

    def _serialize_message(self, message: IPCMessage) -> bytes:
        """Serialize message to bytes"""
        message_dict = asdict(message)
        message_dict['timestamp'] = message.timestamp.isoformat()
        message_dict['message_type'] = message.message_type.value

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

    def _register_default_handlers(self):
        """Register default message handlers"""
        self.message_handlers[MessageType.HEARTBEAT] = self._handle_heartbeat
        self.message_handlers[MessageType.SHUTDOWN] = self._handle_shutdown
        self.message_handlers[MessageType.DATA_REQUEST] = self._handle_data_request
        self.message_handlers[MessageType.PROGRESS_UPDATE] = self._handle_progress_update
        self.message_handlers[MessageType.RESOURCE_UPDATE] = self._handle_resource_update

    def _heartbeat_loop(self):
        """Send periodic heartbeat messages"""
        while self.is_running:
            try:
                self.broadcast_message(
                    MessageType.HEARTBEAT,
                    {
                        'timestamp': datetime.now().isoformat(),
                        'pid': os.getpid(),
                        'memory_usage_mb': psutil.Process().memory_info().rss / (1024 * 1024),
                        'cpu_percent': psutil.cpu_percent(interval=0.1)
                    }
                )
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
                # Check process-specific queues
                for process_id, queue in self.message_queues.items():
                    try:
                        priority, timestamp, serialized_msg = queue.get_nowait()
                        message = self._deserialize_message(serialized_msg)
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

                time.sleep(0.01)  # Small delay to prevent busy waiting

            except Exception as e:
                logger.error(f"Error in message processor loop: {e}")
                time.sleep(0.01)

    def _process_message(self, message: IPCMessage):
        """Process a received message"""
        self.stats['messages_received'] += 1

        # Calculate message latency
        latency = (datetime.now() - message.timestamp).total_seconds() * 1000
        self.stats['average_message_latency_ms'] = (
            (self.stats['average_message_latency_ms'] + latency) / 2
        )

        # Get handler for message type
        handler = self.message_handlers.get(message.message_type)
        if handler:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error handling message {message.message_type}: {e}")
        else:
            logger.debug(f"No handler for message type {message.message_type}")

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
        # This is a placeholder for message cleanup logic
        # In practice, Python's Queue has size limits that handle this
        pass

    def _handle_heartbeat(self, message: IPCMessage):
        """Handle heartbeat message"""
        logger.debug(f"Received heartbeat from process {message.sender_id}")

    def _handle_shutdown(self, message: IPCMessage):
        """Handle shutdown message"""
        logger.info(f"Received shutdown message from process {message.sender_id}")
        # Note: Actual shutdown is handled by the main stop() method

    def _handle_data_request(self, message: IPCMessage):
        """Handle data request message"""
        # This should be implemented by the specific application
        logger.debug(f"Received data request from process {message.sender_id}")

    def _handle_progress_update(self, message: IPCMessage):
        """Handle progress update message"""
        logger.debug(f"Received progress update from process {message.sender_id}")

    def _handle_resource_update(self, message: IPCMessage):
        """Handle resource update message"""
        logger.debug(f"Received resource update from process {message.sender_id}")

    def cleanup_all_shared_memory(self):
        """Cleanup all shared memory blocks"""
        blocks_to_release = list(self.shared_memory_blocks.keys())
        for block_id in blocks_to_release:
            self.release_shared_memory(block_id)

        logger.info("Cleaned up all shared memory blocks")

    def get_statistics(self) -> Dict[str, Any]:
        """Get IPC statistics"""
        return {
            'ipc_stats': self.stats.copy(),
            'shared_memory_blocks': len(self.shared_memory_blocks),
            'message_queues': len(self.message_queues),
            'is_running': self.is_running
        }

    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Register a custom message handler"""
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for message type {message_type}")


# Utility functions for IPC setup
def create_ipc_systems(process_count: int, memory_per_process_mb: int = 256) -> List[InterProcessCommunication]:
    """
    Create IPC systems for multiple processes

    Args:
        process_count: Number of processes
        memory_per_process_mb: Memory allocation per process

    Returns:
        List of IPC systems
    """
    ipc_systems = []

    for i in range(process_count):
        ipc = InterProcessCommunication(
            process_id=i,
            max_shared_memory_mb=memory_per_process_mb
        )
        ipc_systems.append(ipc)

    return ipc_systems


def setup_ipc_connections(ipc_systems: List[InterProcessCommunication]):
    """Setup connections between IPC systems"""
    # Create message queues for each process
    for ipc in ipc_systems:
        for other_ipc in ipc_systems:
            if ipc.process_id != other_ipc.process_id:
                ipc.create_message_queue(other_ipc.process_id)

    logger.info(f"Setup IPC connections for {len(ipc_systems)} processes")


# Performance monitoring utilities
class IPCPerformanceMonitor:
    """Monitor IPC performance metrics"""

    def __init__(self, ipc_systems: List[InterProcessCommunication]):
        self.ipc_systems = ipc_systems
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.performance_history: List[Dict[str, Any]] = []

    def start_monitoring(self, interval: float = 1.0):
        """Start performance monitoring"""
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False

    def _monitoring_loop(self, interval: float):
        """Performance monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect statistics from all IPC systems
                snapshot = {
                    'timestamp': datetime.now().isoformat(),
                    'total_messages_sent': sum(ipc.stats['messages_sent'] for ipc in self.ipc_systems),
                    'total_messages_received': sum(ipc.stats['messages_received'] for ipc in self.ipc_systems),
                    'total_memory_usage_mb': sum(ipc.stats['shared_memory_current_usage_mb'] for ipc in self.ipc_systems),
                    'average_latency_ms': sum(ipc.stats['average_message_latency_ms'] for ipc in self.ipc_systems) / len(self.ipc_systems),
                    'active_shared_memory_blocks': sum(len(ipc.shared_memory_blocks) for ipc in self.ipc_systems)
                }

                self.performance_history.append(snapshot)

                # Keep only last 1000 snapshots
                if len(self.performance_history) > 1000:
                    self.performance_history = self.performance_history[-1000:]

                time.sleep(interval)

            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                time.sleep(interval)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.performance_history:
            return {}

        recent = self.performance_history[-100:]  # Last 100 snapshots

        return {
            'monitoring_duration_minutes': len(self.performance_history) * 1,  # Assuming 1-second intervals
            'total_messages_sent': recent[-1]['total_messages_sent'],
            'total_messages_received': recent[-1]['total_messages_received'],
            'peak_memory_usage_mb': max(snapshot['total_memory_usage_mb'] for snapshot in recent),
            'average_memory_usage_mb': sum(snapshot['total_memory_usage_mb'] for snapshot in recent) / len(recent),
            'average_latency_ms': sum(snapshot['average_latency_ms'] for snapshot in recent) / len(recent),
            'peak_shared_memory_blocks': max(snapshot['active_shared_memory_blocks'] for snapshot in recent),
            'current_shared_memory_blocks': recent[-1]['active_shared_memory_blocks']
        }
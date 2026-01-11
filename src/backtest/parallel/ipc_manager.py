"""
Inter-Process Communication Manager for CBSC multiprocessing backtesting.

Provides efficient, low-latency communication between processes using shared memory,
message passing, and optimized serialization.
"""

import os
import time
import pickle
import mmap
import struct
import threading
import socket
import json
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp
import numpy as np
from queue import Queue, Empty
import psutil

from .models import Task, TaskResult


class MessageType(str, Enum):
    """Message types for IPC."""
    TASK_ASSIGNMENT = "task_assignment"
    TASK_RESULT = "task_result"
    HEARTBEAT = "heartbeat"
    SHUTDOWN = "shutdown"
    STATUS_UPDATE = "status_update"
    DATA_TRANSFER = "data_transfer"
    ERROR_REPORT = "error_report"


class SerializationFormat(str, Enum):
    """Serialization formats."""
    PICKLE = "pickle"
    JSON = "json"
    NUMPY = "numpy"
    CUSTOM = "custom"


@dataclass
class IPCMessage:
    """IPC message structure."""
    message_type: MessageType
    sender_id: int
    receiver_id: Optional[int]  # None for broadcast
    timestamp: float = field(default_factory=time.time)
    data: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher = higher priority
    requires_ack: bool = False


@dataclass
class SharedMemoryBlock:
    """Shared memory block information."""
    name: str
    size: int
    fd: int
    mmap_obj: Optional[mmap.mmap] = None
    ref_count: int = 0
    created_at: float = field(default_factory=time.time)


class MessageQueue:
    """High-performance message queue with priority support."""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.queue = []
        self.lock = threading.RLock()
        self.not_empty = threading.Condition(self.lock)
        self.not_full = threading.Condition(self.lock)

    def put(self, message: IPCMessage, block: bool = True, timeout: Optional[float] = None) -> bool:
        """Put a message in the queue."""
        with self.not_full:
            if not block and len(self.queue) >= self.max_size:
                return False

            while len(self.queue) >= self.max_size:
                if not self.not_full.wait(timeout):
                    return False

            # Insert in priority order
            insert_pos = 0
            for i, existing_msg in enumerate(self.queue):
                if message.priority > existing_msg.priority:
                    insert_pos = i
                    break
                insert_pos = i + 1

            self.queue.insert(insert_pos, message)
            self.not_empty.notify()
            return True

    def get(self, block: bool = True, timeout: Optional[float] = None) -> Optional[IPCMessage]:
        """Get a message from the queue."""
        with self.not_empty:
            if not block and not self.queue:
                return None

            while not self.queue:
                if not self.not_empty.wait(timeout):
                    return None

            message = self.queue.pop(0)
            self.not_full.notify()
            return message

    def peek(self) -> Optional[IPCMessage]:
        """Peek at the next message without removing it."""
        with self.lock:
            return self.queue[0] if self.queue else None

    def size(self) -> int:
        """Get queue size."""
        with self.lock:
            return len(self.queue)


class SerializationManager:
    """Manages serialization and deserialization of different data types."""

    def __init__(self):
        self.serializers = {
            SerializationFormat.PICKLE: self._serialize_pickle,
            SerializationFormat.JSON: self._serialize_json,
            SerializationFormat.NUMPY: self._serialize_numpy
        }

        self.deserializers = {
            SerializationFormat.PICKLE: self._deserialize_pickle,
            SerializationFormat.JSON: self._deserialize_json,
            SerializationFormat.NUMPY: self._deserialize_numpy
        }

    def serialize(self, data: Any, format_type: SerializationFormat = SerializationFormat.PICKLE) -> bytes:
        """Serialize data using specified format."""
        if format_type not in self.serializers:
            raise ValueError(f"Unsupported serialization format: {format_type}")

        return self.serializers[format_type](data)

    def deserialize(self, data: bytes, format_type: SerializationFormat = SerializationFormat.PICKLE) -> Any:
        """Deserialize data using specified format."""
        if format_type not in self.deserializers:
            raise ValueError(f"Unsupported deserialization format: {format_type}")

        return self.deserializers[format_type](data)

    def get_optimal_format(self, data: Any) -> SerializationFormat:
        """Determine the optimal serialization format for data."""
        # Use NumPy format for NumPy arrays
        if isinstance(data, np.ndarray):
            return SerializationFormat.NUMPY

        # Use JSON for simple data structures
        if isinstance(data, (dict, list, str, int, float, bool, type(None))):
            try:
                # Test if JSON serializable
                json.dumps(data)
                return SerializationFormat.JSON
            except (TypeError, ValueError):
                pass

        # Default to pickle
        return SerializationFormat.PICKLE

    def _serialize_pickle(self, data: Any) -> bytes:
        """Serialize using pickle."""
        return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)

    def _deserialize_pickle(self, data: bytes) -> Any:
        """Deserialize using pickle."""
        return pickle.loads(data)

    def _serialize_json(self, data: Any) -> bytes:
        """Serialize using JSON."""
        return json.dumps(data, default=str).encode('utf-8')

    def _deserialize_json(self, data: bytes) -> Any:
        """Deserialize using JSON."""
        return json.loads(data.decode('utf-8'))

    def _serialize_numpy(self, data: Any) -> bytes:
        """Serialize NumPy array."""
        if not isinstance(data, np.ndarray):
            raise ValueError("Data must be NumPy array for numpy format")

        return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)

    def _deserialize_numpy(self, data: bytes) -> Any:
        """Deserialize NumPy array."""
        return pickle.loads(data)


class SharedMemoryManager:
    """Manages shared memory blocks for large data transfer."""

    def __init__(self, max_blocks: int = 100):
        self.max_blocks = max_blocks
        self.blocks: Dict[str, SharedMemoryBlock] = {}
        self.lock = threading.RLock()
        self.total_memory = 0
        self.max_memory = 1024 * 1024 * 1024  # 1GB

    def create_block(self, size: int, name: Optional[str] = None) -> str:
        """Create a new shared memory block."""
        with self.lock:
            # Check memory limit
            if self.total_memory + size > self.max_memory:
                raise MemoryError("Shared memory limit exceeded")

            # Generate unique name
            if name is None:
                name = f"cbsc_shm_{int(time.time() * 1000000)}_{os.getpid()}"

            if name in self.blocks:
                raise ValueError(f"Shared memory block {name} already exists")

            try:
                # Create shared memory file
                fd = os.open(f"/dev/shm/{name}", os.O_CREAT | os.O_RDWR | os.O_TRUNC, 0o666)
                os.ftruncate(fd, size)

                # Memory map the file
                mmap_obj = mmap.mmap(fd, size)

                block = SharedMemoryBlock(
                    name=name,
                    size=size,
                    fd=fd,
                    mmap_obj=mmap_obj
                )

                self.blocks[name] = block
                self.total_memory += size

                return name

            except Exception as e:
                # Cleanup on failure
                if 'fd' in locals():
                    os.close(fd)
                raise RuntimeError(f"Failed to create shared memory block: {e}")

    def get_block(self, name: str) -> Optional[SharedMemoryBlock]:
        """Get a shared memory block by name."""
        with self.lock:
            if name not in self.blocks:
                return None

            block = self.blocks[name]
            block.ref_count += 1
            return block

    def write_data(self, name: str, data: bytes, offset: int = 0) -> int:
        """Write data to shared memory block."""
        block = self.get_block(name)
        if block is None:
            raise ValueError(f"Shared memory block {name} not found")

        if offset + len(data) > block.size:
            raise ValueError("Data exceeds block size")

        if block.mmap_obj:
            block.mmap_obj.seek(offset)
            block.mmap_obj.write(data)
            return len(data)

        return 0

    def read_data(self, name: str, size: int, offset: int = 0) -> bytes:
        """Read data from shared memory block."""
        block = self.get_block(name)
        if block is None:
            raise ValueError(f"Shared memory block {name} not found")

        if offset + size > block.size:
            raise ValueError("Read exceeds block size")

        if block.mmap_obj:
            block.mmap_obj.seek(offset)
            return block.mmap_obj.read(size)

        return b""

    def release_block(self, name: str):
        """Release reference to a shared memory block."""
        with self.lock:
            if name not in self.blocks:
                return

            block = self.blocks[name]
            block.ref_count -= 1

            if block.ref_count <= 0:
                self._cleanup_block(block)
                del self.blocks[name]

    def _cleanup_block(self, block: SharedMemoryBlock):
        """Clean up a shared memory block."""
        try:
            if block.mmap_obj:
                block.mmap_obj.close()

            os.close(block.fd)
            os.unlink(f"/dev/shm/{block.name}")

            self.total_memory -= block.size

        except Exception as e:
            # Log error but don't raise
            print(f"Error cleaning up shared memory block {block.name}: {e}")

    def cleanup_expired_blocks(self, max_age_seconds: int = 3600):
        """Clean up expired shared memory blocks."""
        with self.lock:
            current_time = time.time()
            expired_blocks = []

            for name, block in list(self.blocks.items()):
                if current_time - block.created_at > max_age_seconds and block.ref_count == 0:
                    expired_blocks.append(name)

            for name in expired_blocks:
                self.release_block(name)


class NetworkTransport:
    """Network-based transport for inter-process communication."""

    def __init__(self, port_base: int = 20000):
        self.port_base = port_base
        self.sockets: Dict[int, socket.socket] = {}
        self.listening_sockets: Dict[int, socket.socket] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.message_handlers: Dict[MessageType, List[Callable]] = defaultdict(list)

    def start_server(self, process_id: int, message_handler: Callable[[IPCMessage], None]):
        """Start server for a specific process."""
        # Find available port
        port = self.port_base + process_id
        max_attempts = 10

        for attempt in range(max_attempts):
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind(('localhost', port + attempt))
                server_socket.listen(5)

                self.listening_sockets[process_id] = server_socket

                # Start accepting connections
                self.executor.submit(self._accept_connections, process_id, server_socket, message_handler)

                return port + attempt

            except OSError:
                if attempt == max_attempts - 1:
                    raise
                continue

    def _accept_connections(self, process_id: int, server_socket: socket.socket,
                           message_handler: Callable[[IPCMessage], None]):
        """Accept incoming connections."""
        while True:
            try:
                client_socket, address = server_socket.accept()
                self.executor.submit(self._handle_connection, client_socket, message_handler)

            except Exception as e:
                print(f"Error accepting connection for process {process_id}: {e}")
                break

    def _handle_connection(self, client_socket: socket.socket, message_handler: Callable[[IPCMessage], None]):
        """Handle incoming connection."""
        try:
            while True:
                # Receive message length
                length_data = client_socket.recv(4)
                if not length_data:
                    break

                message_length = struct.unpack('!I', length_data)[0]

                # Receive message data
                message_data = b""
                while len(message_data) < message_length:
                    chunk = client_socket.recv(message_length - len(message_data))
                    if not chunk:
                        break
                    message_data += chunk

                # Deserialize message
                message = pickle.loads(message_data)
                message_handler(message)

        except Exception as e:
            print(f"Error handling connection: {e}")
        finally:
            client_socket.close()

    def send_message(self, target_process_id: int, message: IPCMessage) -> bool:
        """Send a message to another process."""
        try:
            # Find port for target process
            port = self.port_base + target_process_id

            # Connect to target process
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('localhost', port))

            # Serialize message
            message_data = pickle.dumps(message)

            # Send length
            length_data = struct.pack('!I', len(message_data))
            client_socket.send(length_data)

            # Send message
            client_socket.send(message_data)
            client_socket.close()

            return True

        except Exception as e:
            print(f"Error sending message to process {target_process_id}: {e}")
            return False

    def stop_server(self, process_id: int):
        """Stop server for a specific process."""
        if process_id in self.listening_sockets:
            self.listening_sockets[process_id].close()
            del self.listening_sockets[process_id]


class IPCManager:
    """
    High-performance inter-process communication manager.

    Features:
    - Shared memory for large data transfer
    - Message queues with priority support
    - Network-based transport for remote processes
    - Automatic serialization format selection
    - Low-latency message passing
    """

    def __init__(self,
                 process_id: int,
                 enable_shared_memory: bool = True,
                 enable_network_transport: bool = True,
                 queue_size: int = 10000):

        self.process_id = process_id
        self.enable_shared_memory = enable_shared_memory
        self.enable_network_transport = enable_network_transport

        self.logger = logging.getLogger(f"{__name__}.IPCManager.{process_id}")

        # Core components
        self.serialization_manager = SerializationManager()
        self.message_queues: Dict[int, MessageQueue] = defaultdict(lambda: MessageQueue(queue_size))
        self.shared_memory_manager = SharedMemoryManager() if enable_shared_memory else None
        self.network_transport = NetworkTransport() if enable_network_transport else None

        # Message handling
        self.message_handlers: Dict[MessageType, List[Callable]] = defaultdict(list)
        self.running = False

        # Statistics
        self.messages_sent = 0
        self.messages_received = 0
        self.bytes_transferred = 0

    def start(self):
        """Start the IPC manager."""
        if self.running:
            return

        self.running = True

        # Start network transport
        if self.network_transport:
            self.network_transport.start_server(self.process_id, self._handle_message)

        self.logger.info(f"IPC manager started for process {self.process_id}")

    def stop(self):
        """Stop the IPC manager."""
        if not self.running:
            return

        self.running = False

        # Stop network transport
        if self.network_transport:
            self.network_transport.stop_server(self.process_id)

        # Cleanup shared memory
        if self.shared_memory_manager:
            self.shared_memory_manager.cleanup_expired_blocks(0)  # Clean up all blocks

        self.logger.info(f"IPC manager stopped for process {self.process_id}")

    def send_message(self, message: IPCMessage, target_process_id: Optional[int] = None,
                    use_shared_memory: bool = False, large_data_threshold: int = 1024 * 1024) -> bool:
        """
        Send a message to another process.

        Args:
            message: Message to send
            target_process_id: Target process ID (None for broadcast)
            use_shared_memory: Force use shared memory for large data
            large_data_threshold: Threshold for using shared memory

        Returns:
            True if message sent successfully
        """
        try:
            # Serialize message data
            data_format = self.serialization_manager.get_optimal_format(message.data)
            serialized_data = self.serialization_manager.serialize(message.data, data_format)

            # Check if we should use shared memory
            use_shm = (use_shared_memory or
                      len(serialized_data) > large_data_threshold) and self.shared_memory_manager

            if use_shm:
                # Transfer large data via shared memory
                shm_name = self._transfer_via_shared_memory(serialized_data)
                message.metadata['shared_memory_name'] = shm_name
                message.metadata['serialization_format'] = data_format
                message.data = "__SHARED_MEMORY__"

            # Use appropriate transport
            if target_process_id is not None and self.network_transport:
                # Network transport for specific target
                success = self.network_transport.send_message(target_process_id, message)
            else:
                # Local queue transport
                if target_process_id is None:
                    # Broadcast to all queues
                    success = True
                    for pid, queue in self.message_queues.items():
                        if pid != self.process_id:  # Don't send to self
                            queue.put(message)
                else:
                    # Send to specific queue
                    queue = self.message_queues[target_process_id]
                    success = queue.put(message, block=False)

            if success:
                self.messages_sent += 1
                self.bytes_transferred += len(serialized_data)

            return success

        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False

    def receive_message(self, timeout: Optional[float] = None) -> Optional[IPCMessage]:
        """Receive a message from any source."""
        try:
            # Check local queues
            for source_pid, queue in self.message_queues.items():
                if source_pid == self.process_id:
                    continue

                message = queue.get(block=False)
                if message:
                    # Handle shared memory data
                    if isinstance(message.data, str) and message.data == "__SHARED_MEMORY__":
                        message.data = self._receive_from_shared_memory(message.metadata)

                    self.messages_received += 1
                    return message

            return None

        except Empty:
            return None
        except Exception as e:
            self.logger.error(f"Error receiving message: {e}")
            return None

    def register_handler(self, message_type: MessageType, handler: Callable[[IPCMessage], None]):
        """Register a handler for a specific message type."""
        self.message_handlers[message_type].append(handler)

    def _handle_message(self, message: IPCMessage):
        """Handle received message."""
        # Handle shared memory data
        if isinstance(message.data, str) and message.data == "__SHARED_MEMORY__":
            message.data = self._receive_from_shared_memory(message.metadata)

        # Call registered handlers
        for handler in self.message_handlers.get(message.message_type, []):
            try:
                handler(message)
            except Exception as e:
                self.logger.error(f"Error in message handler: {e}")

        # Send acknowledgment if required
        if message.requires_ack and message.sender_id != self.process_id:
            ack_message = IPCMessage(
                message_type=MessageType.HEARTBEAT,
                sender_id=self.process_id,
                receiver_id=message.sender_id,
                data={"ack": True, "original_message_id": message.metadata.get("message_id")}
            )
            self.send_message(ack_message, message.sender_id)

    def _transfer_via_shared_memory(self, data: bytes) -> str:
        """Transfer data via shared memory."""
        if not self.shared_memory_manager:
            raise RuntimeError("Shared memory not enabled")

        shm_name = self.shared_memory_manager.create_block(len(data))
        self.shared_memory_manager.write_data(shm_name, data)
        return shm_name

    def _receive_from_shared_memory(self, metadata: Dict[str, Any]) -> Any:
        """Receive data from shared memory."""
        if not self.shared_memory_manager:
            raise RuntimeError("Shared memory not enabled")

        shm_name = metadata.get("shared_memory_name")
        if not shm_name:
            raise ValueError("Missing shared memory name in metadata")

        # Get block info
        block = self.shared_memory_manager.get_block(shm_name)
        if not block:
            raise ValueError(f"Shared memory block {shm_name} not found")

        # Read data
        data = self.shared_memory_manager.read_data(shm_name, block.size)

        # Deserialize data
        format_type = SerializationFormat(metadata.get("serialization_format", "pickle"))
        deserialized_data = self.serialization_manager.deserialize(data, format_type)

        # Release block
        self.shared_memory_manager.release_block(shm_name)

        return deserialized_data

    def get_statistics(self) -> Dict[str, Any]:
        """Get IPC statistics."""
        return {
            "process_id": self.process_id,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "bytes_transferred": self.bytes_transferred,
            "queue_sizes": {pid: q.size() for pid, q in self.message_queues.items()},
            "shared_memory_blocks": len(self.shared_memory_manager.blocks) if self.shared_memory_manager else 0,
            "shared_memory_usage_mb": self.shared_memory_manager.total_memory / (1024*1024) if self.shared_memory_manager else 0
        }
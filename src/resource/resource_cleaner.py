#!/usr/bin/env python3
"""
Resource Cleaner
Comprehensive resource cleanup with extensible handler registration
"""

import os
import sys
import time
import socket
import signal
import threading
import tempfile
import resource
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
import psutil
import gc
import weakref

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of resources that can be cleaned up"""
    FILE_HANDLE = "file_handle"
    DIRECTORY = "directory"
    TEMPORARY_FILE = "temporary_file"
    SHARED_MEMORY = "shared_memory"
    NETWORK_CONNECTION = "network_connection"
    SOCKET = "socket"
    PIPE = "pipe"
    LOCK = "lock"
    SEMAPHORE = "semaphore"
    THREAD = "thread"
    PROCESS = "process"
    MEMORY_POOL = "memory_pool"
    DATABASE_CONNECTION = "database_connection"
    CACHE = "cache"
    QUEUE = "queue"
    EVENT = "event"
    CONDITION = "condition"
    CUSTOM = "custom"


class CleanupStatus(Enum):
    """Status of cleanup operations"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ResourceInfo:
    """Information about a managed resource"""
    resource_id: str
    resource_type: ResourceType
    resource_object: Any
    created_at: datetime
    cleanup_function: Optional[Callable] = None
    cleanup_args: tuple = ()
    cleanup_kwargs: dict = field(default_factory=dict)
    is_critical: bool = False
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    cleanup_status: CleanupStatus = CleanupStatus.PENDING
    cleanup_attempts: int = 0
    last_cleanup_attempt: Optional[datetime] = None
    cleanup_duration: Optional[float] = None
    cleanup_error: Optional[str] = None


@dataclass
class CleanupResult:
    """Result of a cleanup operation"""
    resource_id: str
    resource_type: ResourceType
    status: CleanupStatus
    duration: float
    success: bool
    error_message: Optional[str] = None
    cleanup_method: Optional[str] = None


@dataclass
class CleanupMetrics:
    """Metrics for resource cleanup operations"""
    total_resources_managed: int = 0
    total_cleanup_attempts: int = 0
    total_successful_cleanups: int = 0
    total_failed_cleanups: int = 0
    total_cleanup_time: float = 0.0
    average_cleanup_time: float = 0.0
    cleanup_success_rate: float = 0.0
    peak_resource_count: int = 0
    current_resource_count: int = 0
    memory_freed_mb: float = 0.0
    file_handles_freed: int = 0
    network_connections_closed: int = 0
    last_cleanup_time: Optional[datetime] = None


@dataclass
class CleanerConfig:
    """Configuration for resource cleaner"""
    # Cleanup timing
    cleanup_timeout: float = 30.0
    cleanup_retry_attempts: int = 3
    cleanup_retry_delay: float = 1.0
    force_cleanup_timeout: float = 5.0

    # Resource limits
    max_managed_resources: int = 1000
    memory_cleanup_threshold_mb: float = 100.0
    file_handle_threshold: int = 50

    # Validation
    enable_cleanup_validation: bool = True
    validation_delay: float = 1.0
    strict_validation: bool = False

    # Monitoring
    enable_monitoring: bool = True
    monitoring_interval: float = 10.0
    enable_memory_tracking: bool = True
    enable_handle_tracking: bool = True

    # Advanced settings
    enable_garbage_collection: bool = True
    enable_weakref_tracking: bool = True
    enable_system_resource_cleanup: bool = True
    cleanup_on_exit: bool = True


class ResourceCleaner:
    """
    Comprehensive resource cleanup system with extensible handlers

    Features:
    - Automatic cleanup of file handles, shared memory, network connections
    - Extensible cleanup handler registration
    - Cleanup validation and verification
    - Performance metrics and timing
    - Thread-safe operation
    - Memory leak detection and cleanup
    - System resource monitoring
    """

    def __init__(self, config: Optional[CleanerConfig] = None):
        self.config = config or CleanerConfig()

        # Resource management
        self.managed_resources: Dict[str, ResourceInfo] = {}
        self.resource_handlers: Dict[ResourceType, Callable] = {}
        self.cleanup_results: List[CleanupResult] = []

        # Monitoring state
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None

        # Statistics
        self.metrics = CleanupMetrics()
        self.cleanup_history: List[Tuple[datetime, CleanupResult]] = []

        # System state
        self.initial_memory_usage = self._get_memory_usage()
        self.initial_file_handles = self._get_file_handle_count()

        # Setup default handlers
        self._setup_default_handlers()

        # Register exit handler
        if self.config.cleanup_on_exit:
            import atexit
            atexit.register(self.cleanup_all_resources)

        logger.info("ResourceCleaner initialized")
        logger.info(f"Cleanup timeout: {self.config.cleanup_timeout}s, "
                   f"Validation enabled: {self.config.enable_cleanup_validation}")

    def register_resource(
        self,
        resource_id: str,
        resource_type: ResourceType,
        resource_object: Any,
        cleanup_function: Optional[Callable] = None,
        cleanup_args: tuple = (),
        cleanup_kwargs: dict = None,
        is_critical: bool = False,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register a resource for cleanup management

        Args:
            resource_id: Unique identifier for the resource
            resource_type: Type of resource
            resource_object: The actual resource object
            cleanup_function: Custom cleanup function (optional)
            cleanup_args: Arguments for cleanup function
            cleanup_kwargs: Keyword arguments for cleanup function
            is_critical: Whether this resource is critical
            description: Resource description
            metadata: Additional metadata

        Returns:
            True if registration successful
        """
        try:
            # Check resource limit
            if len(self.managed_resources) >= self.config.max_managed_resources:
                logger.warning(f"Maximum resource limit ({self.config.max_managed_resources}) reached")
                return False

            # Check for duplicate resource ID
            if resource_id in self.managed_resources:
                logger.warning(f"Resource {resource_id} already registered")
                return False

            resource_info = ResourceInfo(
                resource_id=resource_id,
                resource_type=resource_type,
                resource_object=resource_object,
                created_at=datetime.now(),
                cleanup_function=cleanup_function,
                cleanup_args=cleanup_args,
                cleanup_kwargs=cleanup_kwargs or {},
                is_critical=is_critical,
                description=description,
                metadata=metadata or {}
            )

            self.managed_resources[resource_id] = resource_info
            self.metrics.total_resources_managed += 1
            self.metrics.current_resource_count = len(self.managed_resources)
            self.metrics.peak_resource_count = max(self.metrics.peak_resource_count, self.metrics.current_resource_count)

            logger.debug(f"Registered {resource_type.value} resource: {resource_id} "
                        f"(critical: {is_critical})")

            return True

        except Exception as e:
            logger.error(f"Failed to register resource {resource_id}: {e}")
            return False

    def unregister_resource(self, resource_id: str) -> bool:
        """
        Unregister a resource from management

        Args:
            resource_id: Resource ID to unregister

        Returns:
            True if unregistration successful
        """
        try:
            if resource_id not in self.managed_resources:
                logger.warning(f"Resource {resource_id} not registered")
                return False

            resource_info = self.managed_resources[resource_id]

            # Perform cleanup before unregistration
            cleanup_result = self.cleanup_resource(resource_id)

            # Remove from managed resources
            del self.managed_resources[resource_id]
            self.metrics.current_resource_count = len(self.managed_resources)

            logger.debug(f"Unregistered resource: {resource_id}")
            return cleanup_result.success

        except Exception as e:
            logger.error(f"Failed to unregister resource {resource_id}: {e}")
            return False

    def cleanup_resource(self, resource_id: str, force: bool = False) -> CleanupResult:
        """
        Clean up a specific resource

        Args:
            resource_id: Resource ID to clean up
            force: Force cleanup even if critical

        Returns:
            Cleanup result
        """
        if resource_id not in self.managed_resources:
            return CleanupResult(
                resource_id=resource_id,
                resource_type=ResourceType.CUSTOM,
                status=CleanupStatus.FAILED,
                duration=0.0,
                success=False,
                error_message="Resource not found"
            )

        resource_info = self.managed_resources[resource_id]
        cleanup_start_time = time.time()

        # Check if resource is critical and not forcing cleanup
        if resource_info.is_critical and not force:
            logger.warning(f"Skipping cleanup of critical resource: {resource_id}")
            resource_info.cleanup_status = CleanupStatus.SKIPPED
            return CleanupResult(
                resource_id=resource_id,
                resource_type=resource_info.resource_type,
                status=CleanupStatus.SKIPPED,
                duration=0.0,
                success=False,
                error_message="Critical resource - use force=True"
            )

        logger.debug(f"Starting cleanup of resource: {resource_id}")

        try:
            # Update resource info
            resource_info.cleanup_status = CleanupStatus.IN_PROGRESS
            resource_info.cleanup_attempts += 1
            resource_info.last_cleanup_attempt = datetime.now()

            cleanup_success = False
            cleanup_method = None
            error_message = None

            # Try custom cleanup function first
            if resource_info.cleanup_function:
                try:
                    logger.debug(f"Using custom cleanup function for {resource_id}")
                    resource_info.cleanup_function(
                        resource_info.resource_object,
                        *resource_info.cleanup_args,
                        **resource_info.cleanup_kwargs
                    )
                    cleanup_success = True
                    cleanup_method = "custom_function"
                except Exception as e:
                    logger.debug(f"Custom cleanup failed for {resource_id}: {e}")
                    error_message = str(e)

            # Fall back to type-specific handler
            if not cleanup_success and resource_info.resource_type in self.resource_handlers:
                try:
                    logger.debug(f"Using type-specific handler for {resource_id}")
                    self.resource_handlers[resource_info.resource_type](resource_info)
                    cleanup_success = True
                    cleanup_method = "type_handler"
                except Exception as e:
                    logger.debug(f"Type-specific handler failed for {resource_id}: {e}")
                    if not error_message:
                        error_message = str(e)

            # Update resource info
            cleanup_duration = time.time() - cleanup_start_time
            resource_info.cleanup_duration = cleanup_duration
            resource_info.cleanup_status = (
                CleanupStatus.COMPLETED if cleanup_success else CleanupStatus.FAILED
            )
            resource_info.cleanup_error = error_message

            # Create cleanup result
            result = CleanupResult(
                resource_id=resource_id,
                resource_type=resource_info.resource_type,
                status=resource_info.cleanup_status,
                duration=cleanup_duration,
                success=cleanup_success,
                error_message=error_message,
                cleanup_method=cleanup_method
            )

            # Add to results and history
            self.cleanup_results.append(result)
            self.cleanup_history.append((datetime.now(), result))

            # Update metrics
            self.metrics.total_cleanup_attempts += 1
            self.metrics.total_cleanup_time += cleanup_duration
            if cleanup_success:
                self.metrics.total_successful_cleanups += 1
            else:
                self.metrics.total_failed_cleanups += 1

            # Calculate success rate and average time
            if self.metrics.total_cleanup_attempts > 0:
                self.metrics.cleanup_success_rate = (
                    self.metrics.total_successful_cleanups / self.metrics.total_cleanup_attempts
                )
                self.metrics.average_cleanup_time = (
                    self.metrics.total_cleanup_time / self.metrics.total_cleanup_attempts
                )

            self.metrics.last_cleanup_time = datetime.now()

            # Validation if enabled
            if self.config.enable_cleanup_validation and cleanup_success:
                self._validate_cleanup(resource_id, resource_info)

            logger.debug(f"Cleanup {resource_id}: {'SUCCESS' if cleanup_success else 'FAILED'} "
                        f"({cleanup_duration:.3f}s)")

            return result

        except Exception as e:
            logger.error(f"Unexpected error during cleanup of {resource_id}: {e}")
            cleanup_duration = time.time() - cleanup_start_time

            resource_info.cleanup_status = CleanupStatus.FAILED
            resource_info.cleanup_duration = cleanup_duration
            resource_info.cleanup_error = str(e)

            return CleanupResult(
                resource_id=resource_id,
                resource_type=resource_info.resource_type,
                status=CleanupStatus.FAILED,
                duration=cleanup_duration,
                success=False,
                error_message=str(e)
            )

    def cleanup_all_resources(self, force: bool = False) -> List[CleanupResult]:
        """
        Clean up all managed resources

        Args:
            force: Force cleanup of critical resources

        Returns:
            List of cleanup results
        """
        logger.info(f"Starting cleanup of {len(self.managed_resources)} resources "
                   f"(force: {force})")

        cleanup_start_time = time.time()
        results = []

        # Get all resource IDs
        resource_ids = list(self.managed_resources.keys())

        # Clean up in priority order: critical resources last
        critical_resources = []
        non_critical_resources = []

        for resource_id in resource_ids:
            if resource_id in self.managed_resources:
                resource_info = self.managed_resources[resource_id]
                if resource_info.is_critical:
                    critical_resources.append(resource_id)
                else:
                    non_critical_resources.append(resource_id)

        # Clean up non-critical resources first
        for resource_id in non_critical_resources:
            result = self.cleanup_resource(resource_id, force=False)
            results.append(result)

        # Clean up critical resources (with force if specified)
        if force:
            for resource_id in critical_resources:
                result = self.cleanup_resource(resource_id, force=True)
                results.append(result)
        else:
            logger.info(f"Skipping {len(critical_resources)} critical resources "
                       f"(use force=True to clean them)")

        # Perform system-level cleanup
        if self.config.enable_system_resource_cleanup:
            self._perform_system_cleanup()

        # Perform garbage collection
        if self.config.enable_garbage_collection:
            self._perform_garbage_collection()

        total_duration = time.time() - cleanup_start_time
        successful_cleanups = sum(1 for r in results if r.success)

        logger.info(f"Cleanup completed: {successful_cleanups}/{len(results)} successful "
                   f"in {total_duration:.2f}s")

        return results

    def start_monitoring(self):
        """Start resource monitoring"""
        if self.monitoring_active:
            logger.warning("Resource monitoring already active")
            return

        logger.info("Starting resource monitoring...")
        self.monitoring_active = True

        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name="ResourceMonitor",
            daemon=True
        )
        self.monitor_thread.start()

        logger.info("Resource monitoring started")

    def stop_monitoring(self):
        """Stop resource monitoring"""
        if not self.monitoring_active:
            return

        logger.info("Stopping resource monitoring...")
        self.monitoring_active = False

        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)

        logger.info("Resource monitoring stopped")

    def _setup_default_handlers(self):
        """Setup default resource cleanup handlers"""
        self.resource_handlers.update({
            ResourceType.FILE_HANDLE: self._cleanup_file_handle,
            ResourceType.DIRECTORY: self._cleanup_directory,
            ResourceType.TEMPORARY_FILE: self._cleanup_temporary_file,
            ResourceType.SHARED_MEMORY: self._cleanup_shared_memory,
            ResourceType.NETWORK_CONNECTION: self._cleanup_network_connection,
            ResourceType.SOCKET: self._cleanup_socket,
            ResourceType.PIPE: self._cleanup_pipe,
            ResourceType.THREAD: self._cleanup_thread,
            ResourceType.PROCESS: self._cleanup_process,
            ResourceType.DATABASE_CONNECTION: self._cleanup_database_connection,
            ResourceType.QUEUE: self._cleanup_queue,
            ResourceType.MEMORY_POOL: self._cleanup_memory_pool,
        })

    def _cleanup_file_handle(self, resource_info: ResourceInfo):
        """Clean up file handle"""
        file_obj = resource_info.resource_object
        if hasattr(file_obj, 'close'):
            file_obj.close()
            self.metrics.file_handles_freed += 1
        elif hasattr(file_obj, 'fileno'):
            fd = file_obj.fileno()
            try:
                os.close(fd)
                self.metrics.file_handles_freed += 1
            except OSError:
                pass  # Already closed

    def _cleanup_directory(self, resource_info: ResourceInfo):
        """Clean up directory"""
        dir_path = Path(resource_info.resource_object)
        if dir_path.exists():
            import shutil
            shutil.rmtree(dir_path, ignore_errors=True)

    def _cleanup_temporary_file(self, resource_info: ResourceInfo):
        """Clean up temporary file"""
        temp_path = Path(resource_info.resource_object)
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)

    def _cleanup_shared_memory(self, resource_info: ResourceInfo):
        """Clean up shared memory"""
        try:
            import multiprocessing as mp
            if hasattr(resource_info.resource_object, 'close'):
                resource_info.resource_object.close()
            if hasattr(resource_info.resource_object, 'unlink'):
                resource_info.resource_object.unlink()
        except Exception:
            pass  # Shared memory might already be cleaned up

    def _cleanup_network_connection(self, resource_info: ResourceInfo):
        """Clean up network connection"""
        conn = resource_info.resource_object
        if hasattr(conn, 'close'):
            conn.close()
            self.metrics.network_connections_closed += 1

    def _cleanup_socket(self, resource_info: ResourceInfo):
        """Clean up socket"""
        sock = resource_info.resource_object
        try:
            sock.close()
            self.metrics.network_connections_closed += 1
        except Exception:
            pass

    def _cleanup_pipe(self, resource_info: ResourceInfo):
        """Clean up pipe"""
        pipe = resource_info.resource_object
        if hasattr(pipe, 'close'):
            pipe.close()
        elif isinstance(pipe, tuple) and len(pipe) == 2:  # (read_end, write_end)
            for end in pipe:
                if hasattr(end, 'close'):
                    end.close()

    def _cleanup_thread(self, resource_info: ResourceInfo):
        """Clean up thread"""
        thread = resource_info.resource_object
        if isinstance(thread, threading.Thread):
            if thread.is_alive():
                thread.join(timeout=self.config.cleanup_timeout)

    def _cleanup_process(self, resource_info: ResourceInfo):
        """Clean up process"""
        process = resource_info.resource_object
        if hasattr(process, 'terminate'):
            process.terminate()
            process.join(timeout=self.config.cleanup_timeout)
            if process.is_alive():
                process.kill()
                process.join(timeout=self.config.force_kill_timeout)

    def _cleanup_database_connection(self, resource_info: ResourceInfo):
        """Clean up database connection"""
        conn = resource_info.resource_object
        if hasattr(conn, 'close'):
            conn.close()

    def _cleanup_queue(self, resource_info: ResourceInfo):
        """Clean up queue"""
        queue_obj = resource_info.resource_object
        if hasattr(queue_obj, 'close'):
            queue_obj.close()
        if hasattr(queue_obj, 'join_thread'):
            queue_obj.join_thread()

    def _cleanup_memory_pool(self, resource_info: ResourceInfo):
        """Clean up memory pool"""
        pool = resource_info.resource_object
        if hasattr(pool, 'cleanup'):
            pool.cleanup()
        elif hasattr(pool, 'close'):
            pool.close()

    def _validate_cleanup(self, resource_id: str, resource_info: ResourceInfo):
        """Validate that cleanup was successful"""
        try:
            time.sleep(self.config.validation_delay)

            # Check if resource still exists
            if resource_info.resource_type == ResourceType.FILE_HANDLE:
                if hasattr(resource_info.resource_object, 'closed'):
                    if self.config.strict_validation and not resource_info.resource_object.closed:
                        logger.warning(f"File handle {resource_id} may not be properly closed")

            elif resource_info.resource_type == ResourceType.TEMPORARY_FILE:
                temp_path = Path(resource_info.resource_object)
                if self.config.strict_validation and temp_path.exists():
                    logger.warning(f"Temporary file {resource_id} may not be properly removed")

            elif resource_info.resource_type == ResourceType.PROCESS:
                process = resource_info.resource_object
                if hasattr(process, 'is_alive') and process.is_alive():
                    logger.warning(f"Process {resource_id} may still be running after cleanup")

        except Exception as e:
            logger.debug(f"Cleanup validation failed for {resource_id}: {e}")

    def _perform_system_cleanup(self):
        """Perform system-level resource cleanup"""
        try:
            # Close any open file descriptors that might have been missed
            try:
                # Get list of open file descriptors
                proc = psutil.Process()
                open_files = proc.open_files()

                for file_info in open_files:
                    if any(keyword in str(file_info.path).lower()
                          for keyword in ['tmp', 'temp', '/dev/null']):
                        try:
                            os.close(file_info.fd)
                            self.metrics.file_handles_freed += 1
                        except OSError:
                            pass
            except (psutil.AccessDenied, AttributeError):
                pass

            # Clean up temporary files in system temp directories
            temp_dir = Path(tempfile.gettempdir())
            current_pid = os.getpid()

            try:
                for temp_file in temp_dir.glob(f"*{current_pid}*"):
                    if temp_file.is_file():
                        temp_file.unlink(missing_ok=True)
                    elif temp_file.is_dir():
                        import shutil
                        shutil.rmtree(temp_file, ignore_errors=True)
            except PermissionError:
                pass

        except Exception as e:
            logger.debug(f"System cleanup failed: {e}")

    def _perform_garbage_collection(self):
        """Perform garbage collection"""
        try:
            # Force garbage collection
            collected = gc.collect()

            # Collect weak references
            if self.config.enable_weakref_tracking:
                weakref.collect()

            logger.debug(f"Garbage collection completed: {collected} objects collected")

        except Exception as e:
            logger.debug(f"Garbage collection failed: {e}")

    def _monitoring_loop(self):
        """Resource monitoring loop"""
        logger.info("Resource monitoring loop started")

        while self.monitoring_active:
            try:
                # Check memory usage
                if self.config.enable_memory_tracking:
                    current_memory = self._get_memory_usage()
                    memory_diff = current_memory - self.initial_memory_usage

                    if memory_diff > self.config.memory_cleanup_threshold_mb:
                        logger.info(f"Memory usage increased by {memory_diff:.1f}MB, "
                                  f"triggering cleanup")
                        self._perform_garbage_collection()

                # Check file handle usage
                if self.config.enable_handle_tracking:
                    current_handles = self._get_file_handle_count()
                    handle_diff = current_handles - self.initial_file_handles

                    if handle_diff > self.config.file_handle_threshold:
                        logger.warning(f"File handle count increased by {handle_diff}, "
                                     f"consider resource cleanup")

                time.sleep(self.config.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in resource monitoring loop: {e}")
                time.sleep(self.config.monitoring_interval)

        logger.info("Resource monitoring loop ended")

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0

    def _get_file_handle_count(self) -> int:
        """Get current file handle count"""
        try:
            proc = psutil.Process()
            return len(proc.open_files())
        except Exception:
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cleaner statistics"""
        return {
            'cleaner_stats': {
                'monitoring_active': self.monitoring_active,
                'current_resources': len(self.managed_resources),
                'max_resources': self.config.max_managed_resources
            },
            'cleanup_metrics': {
                'total_managed': self.metrics.total_resources_managed,
                'total_attempts': self.metrics.total_cleanup_attempts,
                'successful_cleanups': self.metrics.total_successful_cleanups,
                'failed_cleanups': self.metrics.total_failed_cleanups,
                'success_rate': self.metrics.cleanup_success_rate,
                'average_cleanup_time': self.metrics.average_cleanup_time,
                'peak_resource_count': self.metrics.peak_resource_count,
                'memory_freed_mb': self.metrics.memory_freed_mb,
                'file_handles_freed': self.metrics.file_handles_freed,
                'network_connections_closed': self.metrics.network_connections_closed,
                'last_cleanup': self.metrics.last_cleanup_time.isoformat() if self.metrics.last_cleanup_time else None
            },
            'system_resources': {
                'current_memory_mb': self._get_memory_usage(),
                'initial_memory_mb': self.initial_memory_usage,
                'memory_diff_mb': self._get_memory_usage() - self.initial_memory_usage,
                'current_file_handles': self._get_file_handle_count(),
                'initial_file_handles': self.initial_file_handles,
                'file_handle_diff': self._get_file_handle_count() - self.initial_file_handles
            },
            'resource_summary': {
                resource_type.value: len([
                    r for r in self.managed_resources.values()
                    if r.resource_type == resource_type
                ])
                for resource_type in ResourceType
            },
            'recent_cleanups': [
                {
                    'resource_id': result.resource_id,
                    'resource_type': result.resource_type.value,
                    'status': result.status.value,
                    'duration': result.duration,
                    'success': result.success,
                    'method': result.cleanup_method
                }
                for _, result in self.cleanup_history[-10:]
            ]
        }


# Context manager for automatic resource cleanup
@contextmanager
def managed_resource(
    cleaner: ResourceCleaner,
    resource_id: str,
    resource_type: ResourceType,
    resource_object: Any,
    **kwargs
):
    """Context manager for automatic resource cleanup"""
    try:
        cleaner.register_resource(resource_id, resource_type, resource_object, **kwargs)
        yield resource_object
    finally:
        cleaner.unregister_resource(resource_id)


# Decorator for automatic resource cleanup
def auto_cleanup(
    resource_id: str,
    resource_type: ResourceType,
    cleaner: Optional[ResourceCleaner] = None
):
    """Decorator for automatic resource cleanup"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Create cleaner if not provided
            nonlocal cleaner
            if cleaner is None:
                cleaner = ResourceCleaner()

            # Register the return value as a resource
            result = func(*args, **kwargs)
            if result is not None:
                cleaner.register_resource(
                    resource_id=f"{resource_id}_{func.__name__}",
                    resource_type=resource_type,
                    resource_object=result
                )
            return result
        return wrapper
    return decorator
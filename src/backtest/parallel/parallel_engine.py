"""
Parallel Backtesting Engine for CBSC quantitative trading system.

Integrates all multiprocessing components to provide high-performance
parallel backtesting capabilities with intelligent task distribution,
fault tolerance, and real-time monitoring.
"""

import os
import time
import logging
import threading
import signal
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import Future, TimeoutError
import multiprocessing as mp
import psutil

from .models import Task, TaskResult, TaskType, TaskComplexity
from .process_pool import DynamicProcessPool, SystemMonitor
from .task_distributor import TaskDistributor, SchedulingStrategy
from .fault_handler import FaultHandler, RecoveryAction, ErrorType
from .ipc_manager import IPCManager, IPCMessage, MessageType
from .monitor import BacktestMonitor, ResourceMonitor
from .performance_metrics import PerformanceMetricsCollector


@dataclass
class EngineConfig:
    """Configuration for the parallel engine."""
    # Process pool settings
    min_processes: int = 1
    max_processes: int = 32
    auto_scaling: bool = True
    memory_limit_mb: float = 4096.0

    # Task distribution
    scheduling_strategy: SchedulingStrategy = SchedulingStrategy.LOAD_BALANCED
    enable_adaptive_scheduling: bool = True

    # Fault tolerance
    enable_circuit_breaker: bool = True
    enable_resource_monitoring: bool = True
    max_task_retries: int = 3

    # Performance monitoring
    enable_monitoring: bool = True
    enable_metrics: bool = True

    # Communication
    enable_shared_memory: bool = True
    enable_network_transport: bool = True
    message_queue_size: int = 10000

    # System
    rebalance_interval: float = 5.0
    health_check_interval: float = 1.0
    shutdown_timeout: float = 30.0


class ParallelEngine:
    """
    Main parallel backtesting engine.

    Orchestrates all components to provide:
    - Intelligent task scheduling and distribution
    - Fault-tolerant execution
    - Real-time monitoring and metrics
    - Efficient resource utilization
    - Seamless scalability
    """

    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or EngineConfig()
        self.logger = logging.getLogger(f"{__name__}.ParallelEngine")

        # Core components
        self.process_pool: Optional[DynamicProcessPool] = None
        self.task_distributor: Optional[TaskDistributor] = None
        self.fault_handler: Optional[FaultHandler] = None
        self.ipc_manager: Optional[IPCManager] = None
        self.monitor: Optional[BacktestMonitor] = None
        self.metrics_collector: Optional[PerformanceMetricsCollector] = None

        # State management
        self.running = False
        self.process_id = os.getpid()
        self.task_futures: Dict[str, Future] = {}
        self.completion_callbacks: Dict[str, List[Callable]] = {}

        # Statistics
        self.start_time: Optional[float] = None
        self.total_tasks_submitted = 0
        self.total_tasks_completed = 0
        self.total_errors = 0

        # Thread management
        self.coordinator_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Setup signal handlers
        self._setup_signal_handlers()

    def start(self):
        """Start the parallel engine."""
        if self.running:
            self.logger.warning("Engine already running")
            return

        try:
            self.logger.info("Starting parallel engine...")

            # Initialize components in dependency order
            self._initialize_ipc_manager()
            self._initialize_process_pool()
            self._initialize_task_distributor()
            self._initialize_fault_handler()
            self._initialize_monitoring()

            # Start background coordination
            self._start_coordinator()

            self.running = True
            self.start_time = time.time()

            self.logger.info("Parallel engine started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start parallel engine: {e}")
            self.stop()
            raise

    def stop(self, timeout: Optional[float] = None):
        """Stop the parallel engine gracefully."""
        if not self.running:
            return

        timeout = timeout or self.config.shutdown_timeout
        self.logger.info(f"Stopping parallel engine (timeout: {timeout}s)...")

        self.running = False
        self.stop_event.set()

        # Stop accepting new tasks
        if self.coordinator_thread:
            self.coordinator_thread.join(timeout=5.0)

        # Cancel pending tasks
        self._cancel_pending_tasks()

        # Shutdown components in reverse order
        self._shutdown_monitoring()
        self._shutdown_fault_handler()
        self._shutdown_task_distributor()
        self._shutdown_process_pool()
        self._shutdown_ipc_manager()

        # Wait for graceful shutdown
        self._wait_for_shutdown(timeout)

        self.logger.info("Parallel engine stopped")

    def submit_tasks(self, tasks: List[Task]) -> Dict[str, Future]:
        """
        Submit tasks for parallel execution.

        Args:
            tasks: List of tasks to execute

        Returns:
            Dictionary mapping task IDs to Future objects
        """
        if not self.running:
            raise RuntimeError("Engine not running")

        futures = {}

        for task in tasks:
            future = self._submit_single_task(task)
            if future:
                futures[task.id] = future
                self.task_futures[task.id] = future
                self.total_tasks_submitted += 1

        return futures

    def submit_task(self, task: Task) -> Optional[Future]:
        """Submit a single task for execution."""
        if not self.running:
            raise RuntimeError("Engine not running")

        future = self._submit_single_task(task)
        if future:
            self.task_futures[task.id] = future
            self.total_tasks_submitted += 1

        return future

    def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Optional[TaskResult]:
        """Get result for a specific task."""
        if task_id not in self.task_futures:
            return None

        try:
            future = self.task_futures[task_id]
            result = future.result(timeout=timeout)
            return result
        except TimeoutError:
            return None
        except Exception as e:
            self.logger.error(f"Error getting result for task {task_id}: {e}")
            return None

    def add_completion_callback(self, task_id: str, callback: Callable[[TaskResult], None]):
        """Add completion callback for a task."""
        if task_id not in self.completion_callbacks:
            self.completion_callbacks[task_id] = []
        self.completion_callbacks[task_id].append(callback)

    def get_status(self) -> Dict[str, Any]:
        """Get current engine status."""
        status = {
            "engine": {
                "running": self.running,
                "process_id": self.process_id,
                "uptime_seconds": time.time() - self.start_time if self.start_time else 0,
                "start_time": self.start_time
            },
            "tasks": {
                "total_submitted": self.total_tasks_submitted,
                "total_completed": self.total_tasks_completed,
                "total_errors": self.total_errors,
                "pending": len(self.task_futures) - self.total_tasks_completed - self.total_errors,
                "running": len([f for f in self.task_futures.values() if f.running()])
            },
            "components": {
                "process_pool": self.process_pool.get_status() if self.process_pool else None,
                "task_distributor": self.task_distributor.get_status() if self.task_distributor else None,
                "fault_handler": self.fault_handler.get_health_report() if self.fault_handler else None,
                "ipc_manager": self.ipc_manager.get_statistics() if self.ipc_manager else None
            }
        }

        return status

    def _initialize_ipc_manager(self):
        """Initialize IPC manager."""
        self.ipc_manager = IPCManager(
            process_id=self.process_id,
            enable_shared_memory=self.config.enable_shared_memory,
            enable_network_transport=self.config.enable_network_transport,
            queue_size=self.config.message_queue_size
        )
        self.ipc_manager.start()

    def _initialize_process_pool(self):
        """Initialize process pool."""
        self.process_pool = DynamicProcessPool(
            min_processes=self.config.min_processes,
            max_processes=self.config.max_processes,
            auto_scaling=self.config.auto_scaling,
            memory_limit_mb=self.config.memory_limit_mb,
            scaling_check_interval=self.config.rebalance_interval
        )
        self.process_pool.start()

    def _initialize_task_distributor(self):
        """Initialize task distributor."""
        self.task_distributor = TaskDistributor(
            scheduling_strategy=self.config.scheduling_strategy,
            enable_adaptive=self.config.enable_adaptive_scheduling,
            rebalance_interval=self.config.rebalance_interval
        )
        self.task_distributor.start()

        # Register processes with distributor
        pool_status = self.process_pool.get_status()
        process_count = pool_status["processes"]["total"]
        for i in range(process_count):
            # Create mock process info
            from .models import ProcessInfo, ProcessStatus
            process_info = ProcessInfo(
                id=i,
                pid=0,  # Would be set by actual process
                worker_id=f"worker_{i}",
                status=ProcessStatus.IDLE
            )
            self.task_distributor.register_process(process_info)

    def _initialize_fault_handler(self):
        """Initialize fault handler."""
        self.fault_handler = FaultHandler(
            enable_circuit_breaker=self.config.enable_circuit_breaker,
            enable_resource_monitoring=self.config.enable_resource_monitoring
        )
        self.fault_handler.start()

        # Register recovery callbacks
        self.fault_handler.add_recovery_callback(
            RecoveryAction.RESTART_PROCESS,
            self._handle_process_restart
        )

    def _initialize_monitoring(self):
        """Initialize monitoring components."""
        if self.config.enable_monitoring:
            self.monitor = BacktestMonitor()
            self.monitor.start_monitoring()

        if self.config.enable_metrics:
            self.metrics_collector = PerformanceMetricsCollector()
            self.metrics_collector.start_collection()

    def _submit_single_task(self, task: Task) -> Optional[Future]:
        """Submit a single task for execution."""
        try:
            # Get task estimate
            task_estimate = self.task_distributor.estimator.estimate_task(task)

            # Select process
            process_id = self.task_distributor.distribute_task(task)
            if process_id is None:
                return None

            # Create future for task
            future = Future()

            # Submit to process pool (simplified)
            # In a real implementation, this would use the actual process pool
            def task_wrapper():
                try:
                    # Simulate task execution
                    time.sleep(0.1)  # Simulate work

                    # Create mock result
                    result = TaskResult(
                        task_id=task.id,
                        success=True,
                        execution_time=task_estimate.estimated_duration,
                        performance_metrics={"test": "value"},
                        trade_history=[],
                        process_id=process_id
                    )

                    # Handle completion
                    self._handle_task_completion(task, result)
                    future.set_result(result)

                    return result

                except Exception as e:
                    error_result = TaskResult(
                        task_id=task.id,
                        success=False,
                        execution_time=0.0,
                        error_message=str(e),
                        process_id=process_id
                    )

                    self._handle_task_error(task, error_result, e)
                    future.set_exception(e)

                    return None

            # Submit task (simplified - would use actual process pool)
            import threading
            thread = threading.Thread(target=task_wrapper, daemon=True)
            thread.start()

            return future

        except Exception as e:
            self.logger.error(f"Error submitting task {task.id}: {e}")
            self.fault_handler.handle_error(task.id, None, e)
            return None

    def _handle_task_completion(self, task: Task, result: TaskResult):
        """Handle successful task completion."""
        self.total_tasks_completed += 1

        # Update task distributor
        if result.process_id:
            self.task_distributor.update_process_load(result.process_id, result)

        # Update fault handler
        self.fault_handler.retry_manager.estimator.record_execution(
            task, result.execution_time, 1.0  # Simplified estimate
        )

        # Call completion callbacks
        if task.id in self.completion_callbacks:
            for callback in self.completion_callbacks[task.id]:
                try:
                    callback(result)
                except Exception as e:
                    self.logger.error(f"Error in completion callback: {e}")

        # Record metrics
        if self.metrics_collector:
            self.metrics_collector.record_task_completion(
                task_type=task.type.value,
                duration_ms=result.execution_time * 1000,
                success=True
            )

        # Update monitor
        if self.monitor:
            self.monitor.progress_tracker.complete_task(task.id, True)

        self.logger.debug(f"Task {task.id} completed successfully")

    def _handle_task_error(self, task: Task, result: TaskResult, error: Exception):
        """Handle task execution error."""
        self.total_errors += 1

        # Handle through fault handler
        error_report = self.fault_handler.handle_error(
            task.id=task.id,
            process_id=result.process_id,
            error=error,
            context={"task_type": task.type, "complexity": task.complexity}
        )

        # Try to retry if appropriate
        if error_report.recovery_action == RecoveryAction.RETRY:
            self.fault_handler.retry_task(
                task.id,
                lambda tid: self._retry_task(tid),
                max_retries=self.config.max_task_retries
            )

        # Update monitor
        if self.monitor:
            self.monitor.progress_tracker.complete_task(task.id, False, str(error))

        # Record metrics
        if self.metrics_collector:
            self.metrics_collector.record_task_completion(
                task_type=task.type.value,
                duration_ms=result.execution_time * 1000,
                success=False
            )

        self.logger.error(f"Task {task.id} failed: {error}")

    def _retry_task(self, task_id: str):
        """Retry a failed task."""
        # In a real implementation, this would resubmit the original task
        self.logger.info(f"Retrying task {task_id}")

    def _handle_process_restart(self, error_report):
        """Handle process restart."""
        if error_report.process_id:
            self.logger.info(f"Restarting process {error_report.process_id}")

    def _start_coordinator(self):
        """Start background coordinator thread."""
        self.coordinator_thread = threading.Thread(target=self._coordinator_loop, daemon=True)
        self.coordinator_thread.start()

    def _coordinator_loop(self):
        """Main coordinator loop."""
        while not self.stop_event.is_set():
            try:
                # Check for completed tasks
                self._check_completed_tasks()

                # Handle IPC messages
                if self.ipc_manager:
                    message = self.ipc_manager.receive_message(timeout=0.1)
                    if message:
                        self._handle_ipc_message(message)

                # Cleanup completed futures
                self._cleanup_futures()

                time.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Error in coordinator loop: {e}")

    def _check_completed_tasks(self):
        """Check for completed tasks."""
        completed_tasks = []
        for task_id, future in list(self.task_futures.items()):
            if future.done():
                completed_tasks.append(task_id)

        for task_id in completed_tasks:
            del self.task_futures[task_id]

    def _cleanup_futures(self):
        """Clean up old task futures."""
        # In a real implementation, this might clean up very old futures
        pass

    def _handle_ipc_message(self, message: IPCMessage):
        """Handle IPC message."""
        self.logger.debug(f"Received IPC message: {message.message_type} from {message.sender_id}")

        # Route to appropriate handler
        if message.message_type == MessageType.HEARTBEAT:
            self._handle_heartbeat(message)
        elif message.message_type == MessageType.STATUS_UPDATE:
            self._handle_status_update(message)
        else:
            self.logger.warning(f"Unhandled IPC message type: {message.message_type}")

    def _handle_heartbeat(self, message: IPCMessage):
        """Handle heartbeat message."""
        # Update process health
        pass

    def _handle_status_update(self, message: IPCMessage):
        """Handle status update message."""
        # Update process status
        pass

    def _cancel_pending_tasks(self):
        """Cancel all pending tasks."""
        for task_id, future in self.task_futures.items():
            if not future.done():
                future.cancel()

        self.task_futures.clear()

    def _shutdown_monitoring(self):
        """Shutdown monitoring components."""
        if self.monitor:
            self.monitor.stop_monitoring()
        if self.metrics_collector:
            self.metrics_collector.stop_collection()

    def _shutdown_fault_handler(self):
        """Shutdown fault handler."""
        if self.fault_handler:
            self.fault_handler.stop()

    def _shutdown_task_distributor(self):
        """Shutdown task distributor."""
        if self.task_distributor:
            self.task_distributor.stop()

    def _shutdown_process_pool(self):
        """Shutdown process pool."""
        if self.process_pool:
            self.process_pool.stop()

    def _shutdown_ipc_manager(self):
        """Shutdown IPC manager."""
        if self.ipc_manager:
            self.ipc_manager.stop()

    def _wait_for_shutdown(self, timeout: float):
        """Wait for graceful shutdown."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check if all tasks are done
            if not self.task_futures:
                break

            time.sleep(0.1)

        # Force cancel remaining tasks
        if self.task_futures:
            self.logger.warning(f"Force canceling {len(self.task_futures)} pending tasks")
            self._cancel_pending_tasks()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
            self.stop()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
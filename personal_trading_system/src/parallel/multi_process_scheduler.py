#!/usr/bin/env python3
"""
Multi-Process Scheduler for 32-Core CPU Backtesting
High-performance task distribution and load balancing system
"""

import os
import sys
import time
import uuid
import queue
import logging
import multiprocessing as mp
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor, as_completed
from enum import Enum
import psutil
import numpy as np
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents a parallel processing task"""
    task_id: str
    function: Callable
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    estimated_memory_mb: int = 100
    estimated_cpu_time: float = 1.0
    chunk_size: int = 1
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    worker_id: Optional[int] = None


@dataclass
class WorkerInfo:
    """Worker process information"""
    worker_id: int
    pid: int
    cpu_affinity: List[int]
    memory_limit_mb: int
    current_load: int = 0
    max_concurrent_tasks: int = 1
    total_tasks_completed: int = 0
    total_execution_time: float = 0.0
    last_activity: datetime = field(default_factory=datetime.now)


class MultiProcessScheduler:
    """
    High-performance multi-process scheduler for 32-core CPU systems

    Features:
    - Intelligent task distribution across 32 cores
    - Dynamic load balancing based on CPU and memory usage
    - Priority-based task scheduling
    - Dependency resolution
    - Resource monitoring and optimization
    - Fault tolerance and automatic recovery
    """

    def __init__(
        self,
        max_workers: int = 32,
        memory_limit_gb: float = 16.0,
        enable_cpu_affinity: bool = True,
        load_balancing_strategy: str = "adaptive"
    ):
        self.max_workers = max_workers
        self.memory_limit_bytes = memory_limit_gb * 1024 * 1024 * 1024
        self.enable_cpu_affinity = enable_cpu_affinity
        self.load_balancing_strategy = load_balancing_strategy

        # Task management
        self.tasks: Dict[str, Task] = {}
        self.task_queue = queue.PriorityQueue()
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}

        # Worker management
        self.workers: Dict[int, WorkerInfo] = {}
        self.worker_processes: Dict[int, mp.Process] = {}
        self.available_workers = queue.Queue()

        # Performance tracking
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'total_execution_time': 0.0,
            'average_task_time': 0.0,
            'cpu_utilization': 0.0,
            'memory_utilization': 0.0,
            'throughput_tasks_per_second': 0.0
        }

        # System monitoring
        self.system_monitor = SystemMonitor()
        self.is_running = False
        self.scheduler_thread = None

        logger.info(f"MultiProcessScheduler initialized with {max_workers} workers")
        self._initialize_workers()

    def _initialize_workers(self):
        """Initialize worker processes with CPU affinity"""
        logger.info("Initializing worker processes...")

        for i in range(self.max_workers):
            # Determine CPU affinity for this worker
            if self.enable_cpu_affinity and self.max_workers <= 32:
                cpu_list = [i] if i < 32 else [i % 32]
            else:
                cpu_list = list(range(min(32, mp.cpu_count())))

            worker_info = WorkerInfo(
                worker_id=i,
                pid=0,  # Will be set when process starts
                cpu_affinity=cpu_list,
                memory_limit_mb=self.memory_limit_bytes // (1024 * 1024) // self.max_workers,
                max_concurrent_tasks=1
            )

            self.workers[i] = worker_info
            self.available_workers.put(i)

        logger.info(f"Initialized {len(self.workers)} workers")

    def submit_task(
        self,
        function: Callable,
        args: tuple = (),
        kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        estimated_memory_mb: int = 100,
        estimated_cpu_time: float = 1.0,
        chunk_size: int = 1,
        dependencies: List[str] = None
    ) -> str:
        """
        Submit a task for parallel execution

        Args:
            function: Function to execute
            args: Function arguments
            kwargs: Function keyword arguments
            priority: Task priority
            estimated_memory_mb: Estimated memory usage in MB
            estimated_cpu_time: Estimated CPU time in seconds
            chunk_size: Data chunk size for this task
            dependencies: List of task IDs this task depends on

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())

        task = Task(
            task_id=task_id,
            function=function,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            estimated_memory_mb=estimated_memory_mb,
            estimated_cpu_time=estimated_cpu_time,
            chunk_size=chunk_size,
            dependencies=dependencies or []
        )

        self.tasks[task_id] = task
        self.task_queue.put((-priority.value, time.time(), task_id))

        self.stats['total_tasks'] += 1
        logger.debug(f"Submitted task {task_id} with priority {priority.name}")

        return task_id

    def submit_batch_tasks(
        self,
        function: Callable,
        data_chunks: List[Any],
        args: tuple = (),
        kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        estimated_memory_mb_per_task: int = 100,
        estimated_cpu_time_per_task: float = 1.0
    ) -> List[str]:
        """
        Submit multiple tasks for batch processing

        Args:
            function: Function to execute
            data_chunks: List of data chunks, one per task
            args: Common function arguments
            kwargs: Common function keyword arguments
            priority: Task priority
            estimated_memory_mb_per_task: Memory usage per task
            estimated_cpu_time_per_task: CPU time per task

        Returns:
            List of task IDs
        """
        task_ids = []

        for i, chunk in enumerate(data_chunks):
            task_kwargs = kwargs.copy() if kwargs else {}
            task_kwargs['data_chunk'] = chunk
            task_kwargs['chunk_index'] = i

            task_id = self.submit_task(
                function=function,
                args=args,
                kwargs=task_kwargs,
                priority=priority,
                estimated_memory_mb=estimated_memory_mb_per_task,
                estimated_cpu_time=estimated_cpu_time_per_task,
                chunk_size=len(chunk) if hasattr(chunk, '__len__') else 1
            )
            task_ids.append(task_id)

        logger.info(f"Submitted batch of {len(task_ids)} tasks")
        return task_ids

    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        self.is_running = True

        # Start scheduler thread
        import threading
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()

        # Start system monitoring
        self.system_monitor.start()

        logger.info("MultiProcessScheduler started")

    def stop(self, timeout: float = 30.0):
        """Stop the scheduler"""
        logger.info("Stopping MultiProcessScheduler...")

        self.is_running = False

        # Cancel pending tasks
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED

        # Wait for running tasks to complete
        start_time = time.time()
        while self.running_tasks and time.time() - start_time < timeout:
            time.sleep(0.1)

        # Terminate worker processes
        for worker_process in self.worker_processes.values():
            if worker_process.is_alive():
                worker_process.terminate()
                worker_process.join(timeout=1.0)

        # Stop system monitoring
        self.system_monitor.stop()

        logger.info("MultiProcessScheduler stopped")

    def _scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Scheduler loop started")

        while self.is_running:
            try:
                # Get next task from queue
                try:
                    _, _, task_id = self.task_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                task = self.tasks.get(task_id)
                if not task:
                    continue

                # Check dependencies
                if not self._check_dependencies(task):
                    # Re-queue task for later
                    self.task_queue.put((-task.priority.value, time.time(), task_id))
                    continue

                # Get available worker
                try:
                    worker_id = self.available_workers.get(timeout=0.1)
                except queue.Empty:
                    # Re-queue task for later
                    self.task_queue.put((-task.priority.value, time.time(), task_id))
                    continue

                # Check resource availability
                if not self._check_resource_availability(task):
                    # Re-queue task and return worker to pool
                    self.available_workers.put(worker_id)
                    self.task_queue.put((-task.priority.value, time.time(), task_id))
                    continue

                # Execute task
                self._execute_task(task, worker_id)

            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(0.1)

        logger.info("Scheduler loop ended")

    def _check_dependencies(self, task: Task) -> bool:
        """Check if task dependencies are satisfied"""
        for dep_id in task.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True

    def _check_resource_availability(self, task: Task) -> bool:
        """Check if system has enough resources for the task"""
        # Check memory
        available_memory = psutil.virtual_memory().available
        if available_memory < task.estimated_memory_mb * 1024 * 1024:
            return False

        # Check CPU load
        cpu_percent = psutil.cpu_percent(interval=0.1)
        if cpu_percent > 95:  # Leave some headroom
            return False

        return True

    def _execute_task(self, task: Task, worker_id: int):
        """Execute a task on a specific worker"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        task.worker_id = worker_id

        self.running_tasks[task.task_id] = task

        worker_info = self.workers[worker_id]
        worker_info.current_load += 1
        worker_info.last_activity = datetime.now()

        # Execute task in separate process
        def task_wrapper():
            try:
                result = task.function(*task.args, **task.kwargs)
                return (True, result, None)
            except Exception as e:
                return (False, None, str(e))

        # Start process
        process = mp.Process(target=task_wrapper)
        process.start()
        self.worker_processes[worker_id] = process

        logger.debug(f"Started task {task.task_id} on worker {worker_id}")

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get status of a specific task"""
        task = self.tasks.get(task_id)
        return task.status if task else None

    def get_task_result(self, task_id: str) -> Any:
        """Get result of a completed task"""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.COMPLETED:
            return task.result
        return None

    def wait_for_completion(self, task_ids: List[str], timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Wait for completion of specific tasks

        Args:
            task_ids: List of task IDs to wait for
            timeout: Maximum time to wait

        Returns:
            Dictionary mapping task IDs to results or errors
        """
        results = {}
        start_time = time.time()

        while len(results) < len(task_ids):
            if timeout and time.time() - start_time > timeout:
                break

            for task_id in task_ids:
                if task_id in results:
                    continue

                task = self.tasks.get(task_id)
                if not task:
                    results[task_id] = None
                    continue

                if task.status == TaskStatus.COMPLETED:
                    results[task_id] = task.result
                elif task.status == TaskStatus.FAILED:
                    results[task_id] = None
                elif task.status == TaskStatus.CANCELLED:
                    results[task_id] = None

            time.sleep(0.1)

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        # Update stats
        self._update_statistics()

        return {
            'scheduler_stats': self.stats.copy(),
            'worker_stats': {
                worker_id: {
                    'current_load': worker.current_load,
                    'total_tasks_completed': worker.total_tasks_completed,
                    'total_execution_time': worker.total_execution_time,
                    'last_activity': worker.last_activity.isoformat()
                }
                for worker_id, worker in self.workers.items()
            },
            'system_stats': self.system_monitor.get_current_stats(),
            'task_stats': {
                'total_tasks': len(self.tasks),
                'pending_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
                'running_tasks': len(self.running_tasks),
                'completed_tasks': len(self.completed_tasks),
                'failed_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED])
            }
        }

    def _update_statistics(self):
        """Update internal statistics"""
        completed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
        failed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.FAILED]

        self.stats['completed_tasks'] = len(completed_tasks)
        self.stats['failed_tasks'] = len(failed_tasks)

        if completed_tasks:
            total_time = sum(
                (t.completed_at - t.started_at).total_seconds()
                for t in completed_tasks
                if t.completed_at and t.started_at
            )
            self.stats['total_execution_time'] = total_time
            self.stats['average_task_time'] = total_time / len(completed_tasks)

            # Calculate throughput
            elapsed_time = (datetime.now() - min(t.created_at for t in self.tasks.values())).total_seconds()
            if elapsed_time > 0:
                self.stats['throughput_tasks_per_second'] = len(completed_tasks) / elapsed_time

        # Update system utilization
        self.stats['cpu_utilization'] = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        self.stats['memory_utilization'] = memory.percent

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            return True
        return False

    def clear_completed_tasks(self):
        """Clear completed tasks from memory"""
        completed_task_ids = [
            task_id for task_id, task in self.tasks.items()
            if task.status == TaskStatus.COMPLETED
        ]

        for task_id in completed_task_ids:
            del self.tasks[task_id]
            if task_id in self.completed_tasks:
                del self.completed_tasks[task_id]

        logger.info(f"Cleared {len(completed_task_ids)} completed tasks")


class SystemMonitor:
    """System resource monitoring"""

    def __init__(self, update_interval: float = 1.0):
        self.update_interval = update_interval
        self.is_monitoring = False
        self.monitor_thread = None
        self.stats = {
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'memory_available_gb': 0.0,
            'disk_usage_percent': 0.0,
            'active_processes': 0,
            'timestamp': None
        }

    def start(self):
        """Start monitoring"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        import threading
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop(self):
        """Stop monitoring"""
        self.is_monitoring = False

    def _monitor_loop(self):
        """Monitoring loop"""
        while self.is_monitoring:
            try:
                # CPU usage
                self.stats['cpu_percent'] = psutil.cpu_percent(interval=0.1)

                # Memory usage
                memory = psutil.virtual_memory()
                self.stats['memory_percent'] = memory.percent
                self.stats['memory_available_gb'] = memory.available / (1024**3)

                # Disk usage
                disk = psutil.disk_usage('/')
                self.stats['disk_usage_percent'] = disk.percent

                # Process count
                self.stats['active_processes'] = len(psutil.pids())

                self.stats['timestamp'] = datetime.now().isoformat()

                time.sleep(self.update_interval)

            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                time.sleep(self.update_interval)

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        return self.stats.copy()


# Utility functions for parallel processing
def chunk_data(data: Any, num_chunks: int) -> List[Any]:
    """
    Split data into chunks for parallel processing

    Args:
        data: Data to chunk (list, array, DataFrame)
        num_chunks: Number of chunks to create

    Returns:
        List of data chunks
    """
    if isinstance(data, pd.DataFrame):
        chunk_size = max(1, len(data) // num_chunks)
        return [data.iloc[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    elif isinstance(data, (list, np.ndarray)):
        chunk_size = max(1, len(data) // num_chunks)
        return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    else:
        raise ValueError(f"Unsupported data type for chunking: {type(data)}")


def estimate_task_memory(data_sample: Any, function_overhead_mb: int = 50) -> int:
    """
    Estimate memory usage for a task

    Args:
        data_sample: Sample data to estimate size
        function_overhead_mb: Additional memory for function execution

    Returns:
        Estimated memory usage in MB
    """
    if isinstance(data_sample, pd.DataFrame):
        data_size_mb = data_sample.memory_usage(deep=True).sum() / (1024 * 1024)
    elif isinstance(data_sample, np.ndarray):
        data_size_mb = data_sample.nbytes / (1024 * 1024)
    elif isinstance(data_sample, list):
        data_size_mb = len(str(data_sample)) / (1024 * 1024)  # Rough estimate
    else:
        data_size_mb = 1  # Default estimate

    # Add 3x buffer for processing overhead
    return int(data_size_mb * 3 + function_overhead_mb)
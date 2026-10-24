"""
Parallel Backtest Processor
===========================

High-performance parallel processing system for backtest tasks.
Supports both multi-threading and multi-processing for optimal performance.
"""

import asyncio
import multiprocessing as mp
import threading
import time
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import queue
# Try to import psutil, use mock if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    # Use mock psutil for testing
    try:
        import sys
        import os
        # Add project root to path
        project_root = os.path.abspath('../../..')
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        import mock_psutil as psutil
        PSUTIL_AVAILABLE = False
    except ImportError:
        # Create minimal mock inline
        class MockPsutil:
            def cpu_percent(self, interval=None):
                return 25.0
            def virtual_memory(self):
                class MockMemory:
                    total = 16 * 1024 * 1024 * 1024
                    available = 8 * 1024 * 1024 * 1024
                    percent = 50.0
                return MockMemory()
        psutil = MockPsutil()
        PSUTIL_AVAILABLE = False
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ExecutionMode(str, Enum):
    """Execution mode for parallel processing"""
    THREAD = "thread"
    PROCESS = "process"
    DISTRIBUTED = "distributed"


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ParallelTask:
    """Parallel task definition"""
    task_id: str
    func: Callable
    args: Tuple
    kwargs: Dict[str, Any]
    priority: int = 0
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    estimated_duration: Optional[float] = None
    memory_requirement: Optional[float] = None  # MB

    def __post_init__(self):
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None


@dataclass
class TaskResult:
    """Task execution result"""
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[Exception] = None
    execution_time: Optional[float] = None
    worker_id: Optional[str] = None


class ResourceMonitor:
    """Monitor system resources for optimal task scheduling"""

    def __init__(self):
        self.cpu_count = mp.cpu_count()
        self.total_memory = psutil.virtual_memory().total / (1024 * 1024)  # MB

    def get_available_resources(self) -> Dict[str, float]:
        """Get current available resources"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        available_memory = memory.available / (1024 * 1024)  # MB

        return {
            'cpu_usage': cpu_percent,
            'cpu_available': max(0, 100 - cpu_percent),
            'memory_usage': memory.percent,
            'memory_available': available_memory,
            'memory_available_pct': (available_memory / self.total_memory) * 100
        }

    def can_run_task(self, task: ParallelTask, margin: float = 0.1) -> bool:
        """Check if system can run this task"""
        resources = self.get_available_resources()

        # Check memory
        if task.memory_requirement:
            available_memory = resources['memory_available'] * (1 - margin)
            if task.memory_requirement > available_memory:
                return False

        # Check CPU (simple check)
        if resources['cpu_available'] < 10:  # Less than 10% CPU available
            return False

        return True


class TaskScheduler:
    """Intelligent task scheduler based on resources and priority"""

    def __init__(self, resource_monitor: ResourceMonitor):
        self.resource_monitor = resource_monitor
        self.task_queue = asyncio.PriorityQueue()
        self.active_tasks: Dict[str, ParallelTask] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}

    async def submit_task(self, task: ParallelTask):
        """Submit a task for scheduling"""
        # Use negative priority for max-heap behavior
        await self.task_queue.put((-task.priority, time.time(), task))

    async def get_next_task(self) -> Optional[ParallelTask]:
        """Get the next task to execute"""
        try:
            # Get task with highest priority
            _, _, task = await asyncio.wait_for(
                self.task_queue.get(),
                timeout=0.1
            )

            # Check if we can run it
            if self.resource_monitor.can_run_task(task):
                self.active_tasks[task.task_id] = task
                return task
            else:
                # Put back in queue
                await self.task_queue.put((-task.priority, time.time(), task))
                return None

        except asyncio.TimeoutError:
            return None

    def complete_task(self, task_id: str, result: TaskResult):
        """Mark a task as completed"""
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        self.completed_tasks[task_id] = result

    def get_queue_size(self) -> int:
        """Get number of pending tasks"""
        return self.task_queue.qsize()

    def get_active_count(self) -> int:
        """Get number of active tasks"""
        return len(self.active_tasks)


class ParallelProcessor:
    """Main parallel processing engine"""

    def __init__(
        self,
        max_workers: Optional[int] = None,
        execution_mode: ExecutionMode = ExecutionMode.THREAD,
        enable_resource_monitoring: bool = True,
        max_memory_per_worker: Optional[float] = None
    ):
        """
        Initialize parallel processor

        Args:
            max_workers: Maximum number of worker threads/processes
            execution_mode: Execution mode (thread/process)
            enable_resource_monitoring: Enable system resource monitoring
            max_memory_per_worker: Maximum memory per worker in MB
        """
        self.max_workers = max_workers or min(32, (mp.cpu_count() or 1) + 4)
        self.execution_mode = execution_mode
        self.enable_resource_monitoring = enable_resource_monitoring
        self.max_memory_per_worker = max_memory_per_worker

        # Initialize components
        self.resource_monitor = ResourceMonitor() if enable_resource_monitoring else None
        self.scheduler = TaskScheduler(self.resource_monitor) if enable_resource_monitoring else None

        # Execution pools
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.process_pool: Optional[ProcessPoolExecutor] = None

        # Worker management
        self.worker_semaphore = asyncio.Semaphore(self.max_workers)
        self.active_futures: Dict[str, asyncio.Future] = {}

        # Statistics
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cancelled_tasks': 0,
            'total_execution_time': 0.0,
            'average_execution_time': 0.0,
            'throughput_per_second': 0.0
        }

        logger.info(f"Parallel processor initialized: mode={execution_mode}, workers={self.max_workers}")

    async def initialize(self):
        """Initialize execution pools"""
        if self.execution_mode in [ExecutionMode.THREAD, ExecutionMode.DISTRIBUTED]:
            self.thread_pool = ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix="BacktestWorker"
            )

        if self.execution_mode == ExecutionMode.PROCESS:
            self.process_pool = ProcessPoolExecutor(
                max_workers=self.max_workers
            )

        logger.info(f"Execution pools initialized in {self.execution_mode} mode")

    async def submit_task(
        self,
        task_id: str,
        func: Callable,
        args: Tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        priority: int = 0,
        timeout: Optional[float] = None,
        max_retries: int = 3,
        estimated_duration: Optional[float] = None
    ) -> str:
        """
        Submit a task for parallel execution

        Args:
            task_id: Unique task identifier
            func: Function to execute
            args: Function arguments
            kwargs: Function keyword arguments
            priority: Task priority (higher = more important)
            timeout: Task timeout in seconds
            max_retries: Maximum retry attempts
            estimated_duration: Estimated execution time

        Returns:
            Task ID
        """
        kwargs = kwargs or {}

        task = ParallelTask(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries,
            estimated_duration=estimated_duration
        )

        if self.scheduler:
            await self.scheduler.submit_task(task)
        else:
            # Direct submission
            await self._execute_task(task)

        self.stats['total_tasks'] += 1
        logger.debug(f"Submitted task {task_id} with priority {priority}")

        return task_id

    async def _execute_task(self, task: ParallelTask):
        """Execute a single task"""
        async with self.worker_semaphore:
            task.started_at = time.time()

            try:
                if self.execution_mode == ExecutionMode.PROCESS and self.process_pool:
                    # Run in process pool
                    loop = asyncio.get_event_loop()
                    future = loop.run_in_executor(
                        self.process_pool,
                        self._run_task_sync,
                        task
                    )
                else:
                    # Run in thread pool
                    loop = asyncio.get_event_loop()
                    future = loop.run_in_executor(
                        self.thread_pool,
                        self._run_task_sync,
                        task
                    )

                # Store future for cancellation
                self.active_futures[task.task_id] = future

                # Wait for completion with timeout
                try:
                    if task.timeout:
                        result = await asyncio.wait_for(future, timeout=task.timeout)
                    else:
                        result = await future

                    # Create success result
                    task_result = TaskResult(
                        task_id=task.task_id,
                        status=TaskStatus.COMPLETED,
                        result=result,
                        execution_time=time.time() - task.started_at,
                        worker_id=threading.current_thread().name
                    )

                    self.stats['completed_tasks'] += 1

                except asyncio.TimeoutError:
                    # Handle timeout
                    if not future.done():
                        future.cancel()

                    task_result = TaskResult(
                        task_id=task.task_id,
                        status=TaskStatus.FAILED,
                        error=TimeoutError(f"Task timed out after {task.timeout} seconds"),
                        execution_time=time.time() - task.started_at
                    )

                    self.stats['failed_tasks'] += 1

                except Exception as e:
                    # Handle other errors
                    task_result = TaskResult(
                        task_id=task.task_id,
                        status=TaskStatus.FAILED,
                        error=e,
                        execution_time=time.time() - task.started_at
                    )

                    self.stats['failed_tasks'] += 1

                    # Retry if configured
                    if task.retry_count < task.max_retries:
                        logger.warning(f"Task {task.task_id} failed, retrying ({task.retry_count + 1}/{task.max_retries})")
                        task.retry_count += 1
                        await self.submit_task(
                            task.task_id + f"_retry_{task.retry_count}",
                            task.func,
                            task.args,
                            task.kwargs,
                            task.priority,
                            task.timeout,
                            task.max_retries - task.retry_count
                        )

            except Exception as e:
                # Handle critical errors
                task_result = TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.FAILED,
                    error=e,
                    execution_time=time.time() - task.started_at if task.started_at else None
                )

                self.stats['failed_tasks'] += 1

            finally:
                # Cleanup
                task.completed_at = time.time()
                if task.task_id in self.active_futures:
                    del self.active_futures[task.task_id]

                # Update scheduler if used
                if self.scheduler:
                    self.scheduler.complete_task(task.task_id, task_result)

                # Update statistics
                self._update_stats(task_result)

            return task_result

    @staticmethod
    def _run_task_sync(task: ParallelTask) -> Any:
        """Run task synchronously (executed in worker)"""
        try:
            # Check memory usage if specified
            if task.memory_requirement:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / (1024 * 1024)
                if memory_mb > task.memory_requirement * 1.5:  # 50% buffer
                    raise MemoryError(f"Task exceeded memory limit: {memory_mb:.1f}MB > {task.memory_requirement}MB")

            # Execute function
            return task.func(*task.args, **task.kwargs)

        except Exception as e:
            logger.error(f"Task {task.task_id} execution failed: {e}")
            raise

    async def run_worker_loop(self):
        """Main worker loop for scheduled execution"""
        if not self.scheduler:
            logger.warning("No scheduler configured, worker loop disabled")
            return

        while True:
            try:
                # Get next task from scheduler
                task = await self.scheduler.get_next_task()

                if task:
                    # Execute task
                    asyncio.create_task(self._execute_task(task))
                else:
                    # No tasks available, wait a bit
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(1)

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task

        Args:
            task_id: Task ID to cancel

        Returns:
            True if cancelled successfully
        """
        # Check active futures
        if task_id in self.active_futures:
            future = self.active_futures[task_id]
            if not future.done():
                future.cancel()
                self.stats['cancelled_tasks'] += 1
                return True

        # Check scheduler queue
        if self.scheduler and task_id in self.scheduler.active_tasks:
            task = self.scheduler.active_tasks[task_id]
            del self.scheduler.active_tasks[task_id]
            self.stats['cancelled_tasks'] += 1
            return True

        return False

    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get result of a completed task"""
        if self.scheduler and task_id in self.scheduler.completed_tasks:
            return self.scheduler.completed_tasks[task_id]
        return None

    async def wait_for_completion(self, task_ids: List[str], timeout: Optional[float] = None) -> Dict[str, TaskResult]:
        """
        Wait for multiple tasks to complete

        Args:
            task_ids: List of task IDs to wait for
            timeout: Maximum wait time

        Returns:
            Dictionary of task results
        """
        results = {}
        start_time = time.time()

        while len(results) < len(task_ids):
            # Check each task
            for task_id in task_ids:
                if task_id not in results:
                    result = await self.get_task_result(task_id)
                    if result:
                        results[task_id] = result

            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                break

            # Small delay to prevent busy waiting
            await asyncio.sleep(0.1)

        return results

    async def process_batch(
        self,
        tasks: List[Tuple[str, Callable, Tuple, Dict[str, Any]]],
        max_concurrent: Optional[int] = None
    ) -> Dict[str, TaskResult]:
        """
        Process a batch of tasks

        Args:
            tasks: List of (task_id, func, args, kwargs) tuples
            max_concurrent: Maximum concurrent tasks

        Returns:
            Dictionary of task results
        """
        if max_concurrent:
            semaphore = asyncio.Semaphore(max_concurrent)
        else:
            semaphore = self.worker_semaphore

        async def process_single(task_data):
            task_id, func, args, kwargs = task_data
            async with semaphore:
                await self.submit_task(task_id, func, args, kwargs)
                result = await self.wait_for_completion([task_id])
                return task_id, result[task_id]

        # Process all tasks concurrently
        coroutines = [process_single(task) for task in tasks]
        results = await asyncio.gather(*coroutines)

        return {task_id: result for task_id, result in results}

    def _update_stats(self, result: TaskResult):
        """Update execution statistics"""
        if result.execution_time:
            self.stats['total_execution_time'] += result.execution_time
            completed = self.stats['completed_tasks']
            if completed > 0:
                self.stats['average_execution_time'] = (
                    self.stats['total_execution_time'] / completed
                )

        # Calculate throughput (tasks per second over last minute)
        if self.stats['total_execution_time'] > 0:
            self.stats['throughput_per_second'] = (
                self.stats['completed_tasks'] / self.stats['total_execution_time']
            )

    async def get_statistics(self) -> Dict[str, Any]:
        """Get processor statistics"""
        stats = self.stats.copy()

        if self.resource_monitor:
            stats['system_resources'] = self.resource_monitor.get_available_resources()

        if self.scheduler:
            stats['queue_size'] = self.scheduler.get_queue_size()
            stats['active_tasks'] = self.scheduler.get_active_count()

        stats['active_futures'] = len(self.active_futures)
        stats['max_workers'] = self.max_workers
        stats['execution_mode'] = self.execution_mode

        return stats

    async def shutdown(self):
        """Shutdown the processor and clean up resources"""
        logger.info("Shutting down parallel processor")

        # Cancel all active tasks
        for task_id in list(self.active_futures.keys()):
            await self.cancel_task(task_id)

        # Wait for all futures to complete
        if self.active_futures:
            await asyncio.gather(
                *self.active_futures.values(),
                return_exceptions=True
            )

        # Shutdown pools
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)

        if self.process_pool:
            self.process_pool.shutdown(wait=True)

        logger.info("Parallel processor shutdown complete")


# Utility functions for common patterns
async def parallel_map(
    processor: ParallelProcessor,
    func: Callable,
    items: List[Any],
    chunk_size: Optional[int] = None
) -> List[Any]:
    """
    Apply function to items in parallel

    Args:
        processor: Parallel processor instance
        func: Function to apply
        items: List of items to process
        chunk_size: Size of chunks for processing

    Returns:
        List of results
    """
    if not chunk_size:
        chunk_size = max(1, len(items) // processor.max_workers)

    # Create chunks
    chunks = [
        items[i:i + chunk_size]
        for i in range(0, len(items), chunk_size)
    ]

    # Process each chunk
    tasks = []
    for i, chunk in enumerate(chunks):
        task_id = f"map_task_{i}"
        tasks.append((task_id, func, (chunk,), {}))

    # Execute batch
    results = await processor.process_batch(tasks)

    # Flatten results
    final_results = []
    for i in range(len(chunks)):
        task_id = f"map_task_{i}"
        if task_id in results and results[task_id].result:
            final_results.extend(results[task_id].result)

    return final_results


async def parallel_reduce(
    processor: ParallelProcessor,
    func: Callable,
    items: List[Any],
    initial: Any
) -> Any:
    """
    Reduce items in parallel

    Args:
        processor: Parallel processor instance
        func: Reduction function
        items: List of items to reduce
        initial: Initial value

    Returns:
        Reduced value
    """
    if not items:
        return initial

    # Base case
    if len(items) == 1:
        return func(initial, items[0])

    # Recursive parallel reduction
    mid = len(items) // 2
    left, right = items[:mid], items[mid:]

    # Process halves in parallel
    task_id_left = f"reduce_left_{time.time()}"
    task_id_right = f"reduce_right_{time.time()}"

    await processor.submit_task(task_id_left, parallel_reduce, (processor, func, left, initial))
    await processor.submit_task(task_id_right, parallel_reduce, (processor, func, right, initial))

    # Wait for completion
    results = await processor.wait_for_completion([task_id_left, task_id_right])

    left_result = results[task_id_left].result
    right_result = results[task_id_right].result

    # Combine results
    return func(left_result, right_result) if right_result else left_result
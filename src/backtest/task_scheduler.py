"""
Task Scheduler for VectorBT Multiprocess Engine
============================================

Provides comprehensive task scheduling with priority queues,
load balancing, and intelligent resource management.
"""

import asyncio
import heapq
import logging
import uuid
from typing import Dict, List, Set, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, Future
import time
import json
from collections import defaultdict, deque
import threading
import weakref

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(int, Enum):
    """Task priority levels (lower value = higher priority)"""
    CRITICAL = 1  # System critical tasks
    HIGH = 2      # User interactive tasks
    NORMAL = 3    # Standard backtest tasks
    LOW = 4       # Background processing
    BATCH = 5     # Batch processing


class SchedulingAlgorithm(str, Enum):
    """Scheduling algorithms"""
    FIFO = "fifo"                    # First In First Out
    PRIORITY = "priority"            # Priority-based
    SHORTEST_JOB = "shortest_job"     # Shortest execution time first
    FAIR_SHARE = "fair_share"        # Fair share scheduling
    LOAD_BALANCED = "load_balanced"  # Load-aware scheduling
    ADAPTIVE = "adaptive"            # Adaptive scheduling


@dataclass
class Task:
    """Task representation"""
    id: str
    name: str
    priority: TaskPriority = TaskPriority.NORMAL
    function: Callable = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)
    estimated_duration: float = 0.0
    max_retries: int = 3
    retry_count: int = 0
    timeout: Optional[float] = None
    metadata: dict = field(default_factory=dict)

    # Runtime state
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    worker_id: Optional[str] = None
    result: Any = None
    error: Optional[Exception] = None
    progress: float = 0.0

    def __lt__(self, other):
        """For priority queue ordering"""
        return (self.priority.value, self.created_at) < (other.priority.value, other.created_at)


@dataclass
class WorkerInfo:
    """Worker information"""
    id: str
    type: str  # 'process', 'thread', 'external'
    status: str  # 'idle', 'busy', 'offline'
    current_task: Optional[Task] = None
    tasks_completed: int = 0
    total_processing_time: float = 0.0
    avg_task_duration: float = 0.0
    last_activity: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


class TaskQueue:
    """Advanced task queue with multiple priority levels"""

    def __init__(self):
        self._queues: Dict[TaskPriority, deque] = {
            priority: deque() for priority in TaskPriority
        }
        self._task_index: Dict[str, Task] = {}
        self._dependencies: Dict[str, Set[str]] = {}
        self._dependents: Dict[str, Set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition()

    async def put(self, task: Task):
        """Add task to queue"""
        async with self._lock:
            self._task_index[task.id] = task
            self._dependencies[task.id] = task.dependencies.copy()

            # Register dependencies
            for dep_id in task.dependencies:
                self._dependents[dep_id].add(task.id)

            # Add to appropriate priority queue
            self._queues[task.priority].append(task)

            async with self._condition:
                self._condition.notify()

    async def get(self, algorithm: SchedulingAlgorithm = SchedulingAlgorithm.PRIORITY) -> Optional[Task]:
        """Get next task to execute"""
        async with self._condition:
            while True:
                task = await self._get_next_task(algorithm)
                if task:
                    return task

                # Wait for new tasks
                await self._condition.wait()

    async def _get_next_task(self, algorithm: SchedulingAlgorithm) -> Optional[Task]:
        """Get next task based on algorithm"""
        async with self._lock:
            if algorithm == SchedulingAlgorithm.PRIORITY:
                return self._get_priority_task()
            elif algorithm == SchedulingAlgorithm.SHORTEST_JOB:
                return self._get_shortest_job_task()
            elif algorithm == SchedulingAlgorithm.FAIR_SHARE:
                return self._get_fair_share_task()
            elif algorithm == SchedulingAlgorithm.ADAPTIVE:
                return self._get_adaptive_task()
            else:
                return self._get_priority_task()

    async def _get_priority_task(self) -> Optional[Task]:
        """Get highest priority ready task"""
        for priority in sorted(TaskPriority):
            queue = self._queues[priority]
            for task in list(queue):
                if await self._is_task_ready(task):
                    queue.remove(task)
                    return task
        return None

    async def _get_shortest_job_task(self) -> Optional[Task]:
        """Get task with shortest estimated duration"""
        ready_tasks = []
        for priority in TaskPriority:
            queue = self._queues[priority]
            for task in list(queue):
                if await self._is_task_ready(task):
                    ready_tasks.append(task)

        if ready_tasks:
            return min(ready_tasks, key=lambda t: t.estimated_duration)
        return None

    async def _get_fair_share_task(self) -> Optional[Task]:
        """Get task for fair share scheduling"""
        # Simplified fair share - prioritize tasks from users with fewer running tasks
        ready_tasks = []
        for priority in TaskPriority:
            queue = self._queues[priority]
            for task in list(queue):
                if await self._is_task_ready(task):
                    ready_tasks.append(task)

        if ready_tasks:
            # Sort by priority first, then by user fairness
            return sorted(ready_tasks, key=lambda t: (t.priority.value, t.metadata.get('user_id', '')))[0]
        return None

    async def _get_adaptive_task(self) -> Optional[Task]:
        """Adaptive task selection based on system state"""
        ready_tasks = []
        for priority in TaskPriority:
            queue = self._queues[priority]
            for task in list(queue):
                if await self._is_task_ready(task):
                    ready_tasks.append(task)

        if ready_tasks:
            # Consider system load and task characteristics
            return max(ready_tasks, key=lambda t: self._calculate_task_score(t))
        return None

    async def _is_task_ready(self, task: Task) -> bool:
        """Check if task dependencies are satisfied"""
        remaining_deps = self._dependencies.get(task.id, set())

        # Check if all dependencies are completed
        for dep_id in remaining_deps:
            dep_task = self._task_index.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False

        return True

    def _calculate_task_score(self, task: Task) -> float:
        """Calculate adaptive score for task selection"""
        # Factors: priority, wait time, estimated duration, system load
        wait_time = (datetime.now() - task.created_at).total_seconds()

        # Higher score = more likely to be selected
        score = (10 - task.priority.value) * 10  # Priority (inverted)
        score += min(wait_time / 60, 10)  # Wait time (max 10 points)

        if task.estimated_duration > 0:
            score += max(10 - task.estimated_duration / 300, 0)  # Duration (prefer shorter)

        return score

    async def remove_task(self, task_id: str) -> bool:
        """Remove task from queue"""
        async with self._lock:
            task = self._task_index.get(task_id)
            if not task:
                return False

            # Remove from priority queue
            self._queues[task.priority].remove(task)

            # Update dependencies
            for dep_id in task.dependencies:
                self._dependencies[dep_id].discard(task_id)

            del self._task_index[task_id]
            return True

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self._task_index.get(task_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = {
            'pending_tasks': 0,
            'tasks_by_priority': {priority.value: len(queue) for priority, queue in self._queues.items()},
            'total_tasks': len(self._task_index),
            'dependency_chains': 0
        }

        # Count pending tasks
        for task in self._task_index.values():
            if task.status == TaskStatus.PENDING:
                stats['pending_tasks'] += 1

        return stats


class LoadBalancer:
    """Load balancer for worker distribution"""

    def __init__(self):
        self._workers: Dict[str, WorkerInfo] = {}
        self._worker_loads: Dict[str, float] = {}
        self._lock = threading.Lock()

    def register_worker(self, worker: WorkerInfo):
        """Register a new worker"""
        with self._lock:
            self._workers[worker.id] = worker
            self._worker_loads[worker.id] = 0.0

    def update_worker_load(self, worker_id: str, load: float):
        """Update worker load"""
        with self._lock:
            self._worker_loads[worker_id] = load

    def get_best_worker(self, task: Task) -> Optional[WorkerInfo]:
        """Get best worker for task"""
        with self._lock:
            available_workers = [
                worker for worker in self._workers.values()
                if worker.status == 'idle'
            ]

            if not available_workers:
                return None

            # Select worker with lowest load
            return min(
                available_workers,
                key=lambda w: self._worker_loads.get(w.id, 0)
            )

    def get_load_stats(self) -> Dict[str, Any]:
        """Get load statistics"""
        with self._lock:
            total_load = sum(self._worker_loads.values())
            avg_load = total_load / len(self._workers) if self._workers else 0

            return {
                'total_workers': len(self._workers),
                'active_workers': sum(1 for w in self._workers.values() if w.status == 'busy'),
                'idle_workers': sum(1 for w in self._workers.values() if w.status == 'idle'),
                'average_load': avg_load,
                'load_distribution': self._worker_loads.copy()
            }


class TaskScheduler:
    """Main task scheduler with advanced scheduling capabilities"""

    def __init__(
        self,
        max_workers: int = None,
        scheduling_algorithm: SchedulingAlgorithm = SchedulingAlgorithm.PRIORITY,
        enable_load_balancing: bool = True,
        enable_fair_share: bool = True
    ):
        self.max_workers = max_workers or min(mp.cpu_count(), 8)
        self.scheduling_algorithm = scheduling_algorithm
        self.enable_load_balancing = enable_load_balancing
        self.enable_fair_share = enable_fair_share

        # Core components
        self.task_queue = TaskQueue()
        self.load_balancer = LoadBalancer()
        self.executor: Optional[ProcessPoolExecutor] = None
        self.thread_executor: Optional[ThreadPoolExecutor] = None

        # State
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._workers: Dict[str, WorkerInfo] = {}
        self._running_tasks: Dict[str, Tuple[Task, Future]] = {}
        self._completed_tasks: Dict[str, Task] = {}

        # Statistics
        self.stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'tasks_cancelled': 0,
            'total_execution_time': 0.0,
            'average_task_time': 0.0,
            'peak_concurrent_tasks': 0
        }

        # Callbacks
        self._task_callbacks: Dict[str, List[Callable]] = {
            'on_task_start': [],
            'on_task_complete': [],
            'on_task_fail': [],
            'on_task_cancel': []
        }

        # Load monitoring
        self._load_monitor_task: Optional[asyncio.Task] = None
        self._system_load = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'active_tasks': 0
        }

    async def start(self):
        """Start the scheduler"""
        if self._running:
            return

        self._running = True

        # Initialize executors
        self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
        self.thread_executor = ThreadPoolExecutor(max_workers=min(self.max_workers, 4))

        # Start scheduler task
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())

        # Start load monitoring
        self._load_monitor_task = asyncio.create_task(self._load_monitor_loop())

        logger.info(f"Task scheduler started with {self.max_workers} workers")

    async def stop(self):
        """Stop the scheduler"""
        self._running = False

        # Cancel tasks
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        if self._load_monitor_task:
            self._load_monitor_task.cancel()
            try:
                await self._load_monitor_task
            except asyncio.CancelledError:
                pass

        # Cancel running tasks
        for task_id, (task, future) in self._running_tasks.items():
            future.cancel()
            task.status = TaskStatus.CANCELLED

        # Shutdown executors
        if self.executor:
            self.executor.shutdown(wait=True)
        if self.thread_executor:
            self.thread_executor.shutdown(wait=True)

        logger.info("Task scheduler stopped")

    async def submit_task(
        self,
        name: str,
        function: Callable,
        args: tuple = (),
        kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: Set[str] = None,
        timeout: Optional[float] = None,
        estimated_duration: float = 0.0,
        **metadata
    ) -> str:
        """Submit a new task"""
        task_id = str(uuid.uuid4())

        task = Task(
            id=task_id,
            name=name,
            priority=priority,
            function=function,
            args=args,
            kwargs=kwargs or {},
            dependencies=dependencies or set(),
            timeout=timeout,
            estimated_duration=estimated_duration,
            metadata=metadata
        )

        await self.task_queue.put(task)
        self.stats['tasks_submitted'] += 1

        logger.debug(f"Task submitted: {name} (ID: {task_id})")
        return task_id

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        # Check if task is in queue
        task = self.task_queue.get_task(task_id)
        if task and task.status == TaskStatus.PENDING:
            if await self.task_queue.remove_task(task_id):
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                self.stats['tasks_cancelled'] += 1

                await self._trigger_callbacks('on_task_cancel', task)
                return True

        # Check if task is running
        if task_id in self._running_tasks:
            task, future = self._running_tasks[task_id]
            future.cancel()
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            del self._running_tasks[task_id]
            self.stats['tasks_cancelled'] += 1

            await self._trigger_callbacks('on_task_cancel', task)
            return True

        return False

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status"""
        task = self.task_queue.get_task(task_id)
        if not task:
            # Check completed tasks
            task = self._completed_tasks.get(task_id)

        if not task:
            return None

        return {
            'id': task.id,
            'name': task.name,
            'status': task.status.value,
            'priority': task.priority.value,
            'progress': task.progress,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'worker_id': task.worker_id,
            'error': str(task.error) if task.error else None,
            'retry_count': task.retry_count
        }

    def add_callback(self, event: str, callback: Callable):
        """Add event callback"""
        if event in self._task_callbacks:
            self._task_callbacks[event].append(callback)

    def remove_callback(self, event: str, callback: Callable):
        """Remove event callback"""
        if event in self._task_callbacks:
            try:
                self._task_callbacks[event].remove(callback)
            except ValueError:
                pass

    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self._running:
            try:
                # Get next task
                task = await self.task_queue.get(self.scheduling_algorithm)

                if task and self._can_execute_task(task):
                    await self._execute_task(task)

                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(1)

    async def _execute_task(self, task: Task):
        """Execute a task"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        task.queued_at = datetime.now()

        # Update worker load
        if task.worker_id:
            self.load_balancer.update_worker_load(task.worker_id, 1.0)

        self._system_load['active_tasks'] = len(self._running_tasks)
        self.stats['peak_concurrent_tasks'] = max(
            self.stats['peak_concurrent_tasks'],
            len(self._running_tasks)
        )

        # Trigger callbacks
        await self._trigger_callbacks('on_task_start', task)

        try:
            # Choose executor
            if asyncio.iscoroutinefunction(task.function):
                # Async function - execute in thread pool
                future = self.thread_executor.submit(
                    asyncio.run, task.function(*task.args, **task.kwargs)
                )
            else:
                # Regular function - execute in process pool
                future = self.executor.submit(task.function, *task.args, **task.kwargs)

            self._running_tasks[task.id] = (task, future)

            # Wait for completion with timeout
            try:
                result = await asyncio.wrap_future(future)
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()

                # Update statistics
                execution_time = (task.completed_at - task.started_at).total_seconds()
                self.stats['tasks_completed'] += 1
                self.stats['total_execution_time'] += execution_time
                self.stats['average_task_time'] = (
                    self.stats['total_execution_time'] / self.stats['tasks_completed']
                )

                await self._trigger_callbacks('on_task_complete', task)

            except asyncio.TimeoutError:
                task.status = TaskStatus.TIMEOUT
                task.error = TimeoutError(f"Task timed out after {task.timeout} seconds")
                future.cancel()

            except Exception as e:
                task.error = e
                task.status = TaskStatus.FAILED
                task.retry_count += 1

                # Retry logic
                if task.retry_count < task.max_retries:
                    logger.info(f"Retrying task {task.id} (attempt {task.retry_count + 1})")
                    await self.task_queue.put(task)
                else:
                    self.stats['tasks_failed'] += 1
                    await self._trigger_callbacks('on_task_fail', task)

            finally:
                # Cleanup
                if task.id in self._running_tasks:
                    del self._running_tasks[task.id]

                if task.worker_id:
                    self.load_balancer.update_worker_load(task.worker_id, 0.0)

                self._system_load['active_tasks'] = len(self._running_tasks)
                self._completed_tasks[task.id] = task

        except Exception as e:
            logger.error(f"Task execution error: {e}")
            task.status = TaskStatus.FAILED
            task.error = e
            self.stats['tasks_failed'] += 1
            await self._trigger_callbacks('on_task_fail', task)

    def _can_execute_task(self, task: Task) -> bool:
        """Check if task can be executed"""
        # Check resource constraints
        if self._system_load['cpu_usage'] > 0.9:
            return False

        # Check concurrent task limit
        if len(self._running_tasks) >= self.max_workers:
            return False

        return True

    async def _trigger_callbacks(self, event: str, task: Task):
        """Trigger event callbacks"""
        for callback in self._task_callbacks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(task)
                else:
                    callback(task)
            except Exception as e:
                logger.error(f"Callback error for {event}: {e}")

    async def _load_monitor_loop(self):
        """Monitor system load"""
        while self._running:
            try:
                # Simple load monitoring
                self._system_load['cpu_usage'] = min(len(self._running_tasks) / self.max_workers, 1.0)
                self._system_load['memory_usage'] = 0.5  # Placeholder
                self._system_load['active_tasks'] = len(self._running_tasks)

                await asyncio.sleep(5)  # Update every 5 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Load monitor error: {e}")
                await asyncio.sleep(5)

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        queue_stats = self.task_queue.get_stats()
        load_stats = self.load_balancer.get_load_stats()

        return {
            'scheduler_stats': self.stats,
            'queue_stats': queue_stats,
            'load_stats': load_stats,
            'system_load': self._system_load.copy(),
            'running_tasks': len(self._running_tasks),
            'completed_tasks': len(self._completed_tasks)
        }


# Global scheduler instance
scheduler = TaskScheduler()
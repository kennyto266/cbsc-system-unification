"""
Async Task Queue System for Backtest Processing
===============================================

Redis-based task queue with priority handling, retry mechanism,
and distributed execution support.

Author: CBSC Quant Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import pickle
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Union
import redis
import redis.asyncio as redis_async
from dataclasses import dataclass, asdict
import aioredis
from concurrent.futures import ThreadPoolExecutor
import traceback
from functools import wraps

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

    @property
    def score(self) -> int:
        """Get priority score for Redis sorted set"""
        scores = {
            TaskPriority.LOW: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.HIGH: 3,
            TaskPriority.URGENT: 4
        }
        return scores[self]


@dataclass
class Task:
    """Task representation"""
    id: str
    name: str
    func_name: str
    args: tuple
    kwargs: dict
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    timeout: Optional[int] = None  # seconds
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.QUEUED
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


class TaskQueue:
    """Async task queue with Redis backend"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        queue_name: str = "backtest_queue",
        result_ttl: int = 86400,  # 24 hours
        max_workers: int = 10,
        health_check_interval: int = 30
    ):
        """
        Initialize task queue

        Args:
            redis_url: Redis connection URL
            queue_name: Queue name prefix
            result_ttl: Result TTL in seconds
            max_workers: Maximum worker processes
            health_check_interval: Health check interval in seconds
        """
        self.redis_url = redis_url
        self.queue_name = queue_name
        self.result_ttl = result_ttl
        self.max_workers = max_workers
        self.health_check_interval = health_check_interval

        # Redis connections
        self.redis_sync = redis.Redis.from_url(redis_url, decode_responses=False)
        self.redis: Optional[redis_async.Redis] = None

        # Task registry
        self.task_functions: Dict[str, Callable] = {}

        # Worker management
        self.workers: List[asyncio.Task] = []
        self.is_running = False

        # Executor for CPU-bound tasks
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Statistics
        self.stats = {
            "tasks_processed": 0,
            "tasks_failed": 0,
            "tasks_retried": 0,
            "workers_active": 0,
            "queue_length": 0
        }

    async def start(self):
        """Start the task queue and workers"""
        if self.is_running:
            logger.warning("Task queue is already running")
            return

        # Initialize async Redis connection
        self.redis = await aioredis.from_url(self.redis_url, decode_responses=False)

        # Test Redis connection
        try:
            await self.redis.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

        # Start workers
        self.is_running = True
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)

        # Start health monitor
        health_task = asyncio.create_task(self._health_monitor())
        self.workers.append(health_task)

        logger.info(f"Task queue started with {self.max_workers} workers")

    async def stop(self):
        """Stop the task queue and workers"""
        if not self.is_running:
            return

        self.is_running = False

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)

        # Close connections
        if self.redis:
            await self.redis.close()
        self.redis_sync.close()
        self.executor.shutdown(wait=True)

        logger.info("Task queue stopped")

    def register_task(self, name: str, func: Callable):
        """
        Register a task function

        Args:
            name: Task function name
            func: Callable function
        """
        self.task_functions[name] = func
        logger.info(f"Registered task function: {name}")

    async def enqueue(
        self,
        func_name: str,
        args: tuple = (),
        kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        name: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: int = 60,
        timeout: Optional[int] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Enqueue a task

        Args:
            func_name: Registered function name
            args: Function arguments
            kwargs: Function keyword arguments
            priority: Task priority
            name: Optional task name
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries (seconds)
            timeout: Task timeout (seconds)
            metadata: Additional metadata

        Returns:
            Task ID
        """
        if func_name not in self.task_functions:
            raise ValueError(f"Unknown task function: {func_name}")

        # Create task
        task = Task(
            id=str(uuid.uuid4()),
            name=name or f"{func_name}_{uuid.uuid4().hex[:8]}",
            func_name=func_name,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            metadata=metadata or {}
        )

        # Serialize and store task
        task_data = pickle.dumps(task)
        task_key = f"{self.queue_name}:task:{task.id}"

        # Store task details
        async with self.redis.pipeline() as pipe:
            await pipe.setex(task_key, self.result_ttl, task_data)
            await pipe.zadd(
                f"{self.queue_name}:pending",
                {task.id: self._get_priority_score(task.priority, task.created_at)}
            )
            await pipe.execute()

        logger.info(f"Enqueued task: {task.id} ({func_name})")
        return task.id

    async def get_task_status(self, task_id: str) -> Optional[Task]:
        """
        Get task status and details

        Args:
            task_id: Task ID

        Returns:
            Task object or None if not found
        """
        # Check pending queue
        if await self.redis.zscore(f"{self.queue_name}:pending", task_id) is not None:
            # Task is pending
            task_data = await self.redis.get(f"{self.queue_name}:task:{task_id}")
            if task_data:
                task = pickle.loads(task_data)
                task.status = TaskStatus.QUEUED
                return task

        # Check running queue
        if await self.redis.zscore(f"{self.queue_name}:running", task_id) is not None:
            # Task is running
            task_data = await self.redis.get(f"{self.queue_name}:task:{task_id}")
            if task_data:
                task = pickle.loads(task_data)
                task.status = TaskStatus.RUNNING
                return task

        # Check results
        result_key = f"{self.queue_name}:result:{task_id}"
        result_data = await self.redis.get(result_key)
        if result_data:
            result = json.loads(result_data)
            task_data = await self.redis.get(f"{self.queue_name}:task:{task_id}")
            if task_data:
                task = pickle.loads(task_data)
                task.status = TaskStatus[result["status"]]
                task.result = result.get("result")
                task.error = result.get("error")
                task.completed_at = datetime.fromisoformat(result["completed_at"]) if result.get("completed_at") else None
                return task

        return None

    async def get_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Get task result, wait if not completed

        Args:
            task_id: Task ID
            timeout: Maximum time to wait (seconds)

        Returns:
            Task result or raises exception
        """
        start_time = datetime.utcnow()

        while True:
            task = await self.get_task_status(task_id)
            if not task:
                raise ValueError(f"Task not found: {task_id}")

            if task.status == TaskStatus.COMPLETED:
                return task.result
            elif task.status == TaskStatus.FAILED:
                raise Exception(f"Task failed: {task.error}")
            elif task.status == TaskStatus.CANCELLED:
                raise Exception("Task was cancelled")

            # Check timeout
            if timeout and (datetime.utcnow() - start_time).total_seconds() > timeout:
                raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")

            # Wait before retrying
            await asyncio.sleep(0.5)

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending or running task

        Args:
            task_id: Task ID

        Returns:
            True if cancelled, False if not found or already completed
        """
        task = await self.get_task_status(task_id)
        if not task:
            return False

        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False

        # Remove from queues and mark as cancelled
        async with self.redis.pipeline() as pipe:
            await pipe.zrem(f"{self.queue_name}:pending", task_id)
            await pipe.zrem(f"{self.queue_name}:running", task_id)
            await pipe.execute()

        # Update task status
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()
        task_data = pickle.dumps(task)
        await self.redis.setex(f"{self.queue_name}:task:{task_id}", self.result_ttl, task_data)

        # Store cancelled result
        result_data = {
            "status": TaskStatus.CANCELLED.value,
            "completed_at": task.completed_at.isoformat()
        }
        await self.redis.setex(
            f"{self.queue_name}:result:{task_id}",
            self.result_ttl,
            json.dumps(result_data)
        )

        logger.info(f"Cancelled task: {task_id}")
        return True

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        pending_count = await self.redis.zcard(f"{self.queue_name}:pending")
        running_count = await self.redis.zcard(f"{self.queue_name}:running")

        self.stats.update({
            "queue_length": pending_count,
            "workers_active": running_count
        })

        return self.stats.copy()

    async def _worker(self, worker_name: str):
        """Worker coroutine to process tasks"""
        logger.info(f"Worker {worker_name} started")

        while self.is_running:
            try:
                # Get next task
                task_id = await self._get_next_task()
                if not task_id:
                    await asyncio.sleep(1)
                    continue

                # Process task
                await self._process_task(worker_name, task_id)

            except asyncio.CancelledError:
                logger.info(f"Worker {worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(5)

        logger.info(f"Worker {worker_name} stopped")

    async def _get_next_task(self) -> Optional[str]:
        """Get next task from queue"""
        # Get from pending queue with highest priority
        now = datetime.utcnow()
        max_score = self._get_priority_score(TaskPriority.URGENT, now)

        # Use Redis BLPOP with timeout for better performance
        result = await self.redis.bzpopmin(f"{self.queue_name}:pending", timeout=1)
        if result:
            task_id, score = result
            # Move to running queue
            await self.redis.zadd(f"{self.queue_name}:running", {task_id: score})
            return task_id.decode() if isinstance(task_id, bytes) else task_id

        return None

    async def _process_task(self, worker_name: str, task_id: str):
        """Process a single task"""
        try:
            # Get task data
            task_data = await self.redis.get(f"{self.queue_name}:task:{task_id}")
            if not task_data:
                logger.error(f"Task data not found: {task_id}")
                return

            task = pickle.loads(task_data)
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()

            # Update task status
            task_data = pickle.dumps(task)
            await self.redis.setex(f"{self.queue_name}:task:{task_id}", self.result_ttl, task_data)

            # Get function
            if task.func_name not in self.task_functions:
                raise ValueError(f"Unknown task function: {task.func_name}")

            func = self.task_functions[task.func_name]

            # Execute task with timeout
            try:
                if task.timeout:
                    result = await asyncio.wait_for(
                        self._execute_task(func, task.args, task.kwargs),
                        timeout=task.timeout
                    )
                else:
                    result = await self._execute_task(func, task.args, task.kwargs)

                # Success
                task.status = TaskStatus.COMPLETED
                task.result = result
                self.stats["tasks_processed"] += 1

            except asyncio.TimeoutError:
                # Timeout
                task.status = TaskStatus.FAILED
                task.error = f"Task timed out after {task.timeout} seconds"

            except Exception as e:
                # Execution error
                if task.retry_count < task.max_retries:
                    # Retry
                    task.status = TaskStatus.RETRYING
                    task.error = str(e)
                    task.retry_count += 1
                    self.stats["tasks_retried"] += 1

                    # Schedule retry
                    await asyncio.sleep(task.retry_delay)
                    await self.redis.zadd(
                        f"{self.queue_name}:pending",
                        {task_id: self._get_priority_score(task.priority, datetime.utcnow())}
                    )
                    await self.redis.zrem(f"{self.queue_name}:running", task_id)

                    logger.info(f"Retrying task {task_id} (attempt {task.retry_count}/{task.max_retries})")
                    return
                else:
                    # Failed
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    self.stats["tasks_failed"] += 1

        except Exception as e:
            # Unexpected error
            task.status = TaskStatus.FAILED
            task.error = f"Internal error: {str(e)}"
            logger.error(f"Unexpected error processing task {task_id}: {e}")
            self.stats["tasks_failed"] += 1

        finally:
            # Clean up
            await self.redis.zrem(f"{self.queue_name}:running", task_id)
            task.completed_at = datetime.utcnow()

            # Store result
            result_data = {
                "status": task.status.value,
                "result": self._serialize_result(task.result) if task.result is not None else None,
                "error": task.error,
                "completed_at": task.completed_at.isoformat(),
                "execution_time": (task.completed_at - task.started_at).total_seconds() if task.started_at else None
            }

            await self.redis.setex(
                f"{self.queue_name}:result:{task_id}",
                self.result_ttl,
                json.dumps(result_data)
            )

            # Update task data
            task_data = pickle.dumps(task)
            await self.redis.setex(f"{self.queue_name}:task:{task_id}", self.result_ttl, task_data)

            logger.info(f"Task {task_id} completed with status: {task.status}")

    async def _execute_task(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """Execute task function"""
        if asyncio.iscoroutinefunction(func):
            # Async function
            return await func(*args, **kwargs)
        else:
            # Sync function - run in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.executor, func, *args, **kwargs)

    async def _health_monitor(self):
        """Monitor queue health and statistics"""
        while self.is_running:
            try:
                # Update statistics
                stats = await self.get_queue_stats()
                logger.debug(f"Queue stats: {stats}")

                # Check for stuck tasks (running for too long)
                running_tasks = await self.redis.zrange(f"{self.queue_name}:running", 0, -1, withscores=True)
                now = datetime.utcnow()

                for task_id_bytes, score in running_tasks:
                    task_id = task_id_bytes.decode() if isinstance(task_id_bytes, bytes) else task_id_bytes
                    task_data = await self.redis.get(f"{self.queue_name}:task:{task_id}")
                    if task_data:
                        task = pickle.loads(task_data)
                        if task.started_at:
                            running_time = (now - task.started_at).total_seconds()
                            if task.timeout and running_time > task.timeout * 2:
                                logger.warning(f"Task {task_id} appears to be stuck (running for {running_time}s)")

                await asyncio.sleep(self.health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(10)

    def _get_priority_score(self, priority: TaskPriority, timestamp: datetime) -> float:
        """Get priority score for sorted set (higher = higher priority)"""
        # Combine priority and timestamp for FIFO within priority
        priority_value = priority.score * 1000000  # Scale priority
        timestamp_value = timestamp.timestamp()  # Add timestamp for FIFO
        return priority_value - timestamp_value

    def _serialize_result(self, result: Any) -> Any:
        """Serialize result for JSON storage"""
        try:
            # Try JSON serialization
            json.dumps(result)
            return result
        except:
            # Fallback to string representation
            return str(result)


# Decorator for registering task functions
def task(name: Optional[str] = None, queue: Optional[TaskQueue] = None):
    """Decorator to register a function as a task"""
    def decorator(func: Callable):
        task_name = name or func.__name__

        # Auto-register if queue is provided
        if queue:
            queue.register_task(task_name, func)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        wrapper.task_name = task_name
        return wrapper

    return decorator


# Example usage
if __name__ == "__main__":
    async def example_usage():
        # Create task queue
        queue = TaskQueue(redis_url="redis://localhost:6379", max_workers=5)

        # Register task functions
        @task("example_task", queue)
        def example_task(x: int, y: int) -> int:
            """Example task function"""
            import time
            time.sleep(2)  # Simulate work
            return x + y

        @task("failing_task", queue)
        def failing_task():
            """Example task that fails"""
            raise ValueError("This task always fails")

        # Start queue
        await queue.start()

        try:
            # Enqueue tasks
            task_id1 = await queue.enqueue("example_task", args=(5, 10), priority=TaskPriority.HIGH)
            task_id2 = await queue.enqueue("example_task", args=(10, 20))
            task_id3 = await queue.enqueue("failing_task", max_retries=2)

            print(f"Enqueued tasks: {task_id1}, {task_id2}, {task_id3}")

            # Wait for results
            result1 = await queue.get_result(task_id1, timeout=10)
            print(f"Task 1 result: {result1}")

            result2 = await queue.get_result(task_id2, timeout=10)
            print(f"Task 2 result: {result2}")

            # Check failed task
            task3 = await queue.get_task_status(task_id3)
            print(f"Task 3 status: {task3.status}, error: {task3.error}")

            # Get statistics
            stats = await queue.get_queue_stats()
            print(f"Queue stats: {stats}")

        finally:
            # Stop queue
            await queue.stop()

    # Run example
    asyncio.run(example_usage())
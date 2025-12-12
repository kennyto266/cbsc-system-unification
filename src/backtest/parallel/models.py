"""
Data models for CBSC multiprocessing backtesting system.

Defines core data structures for tasks, results, processes, and execution statistics.
"""

import time
import uuid
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone


class TaskType(str, Enum):
    """Task type enumeration."""
    BACKTEST = "backtest"
    OPTIMIZATION = "optimization"
    ANALYSIS = "analysis"
    DATA_PROCESSING = "data_processing"
    VALIDATION = "validation"


class TaskComplexity(str, Enum):
    """Task complexity enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class ProcessStatus(str, Enum):
    """Process status enumeration."""
    IDLE = "idle"
    BUSY = "busy"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    RECYCLING = "recycling"


@dataclass
class Task:
    """Represents a backtest task."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: TaskType = TaskType.BACKTEST
    complexity: TaskComplexity = TaskComplexity.MEDIUM
    priority: int = 0  # Higher number = higher priority

    # Task data
    strategy_code: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    data_config: Dict[str, Any] = field(default_factory=dict)
    backtest_config: Dict[str, Any] = field(default_factory=dict)

    # Timing
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    timeout_seconds: Optional[float] = None

    # Resource requirements
    estimated_memory_mb: Optional[float] = None
    estimated_cpu_cores: float = 1.0
    requires_gpu: bool = False

    # Dependencies
    dependencies: List[str] = field(default_factory=list)

    # Status
    status: str = "pending"
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        """Validate task after initialization."""
        if not self.id:
            self.id = str(uuid.uuid4())

    @property
    def execution_time(self) -> Optional[float]:
        """Get task execution time if completed."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    @property
    def is_pending(self) -> bool:
        """Check if task is pending."""
        return self.status == "pending"

    @property
    def is_running(self) -> bool:
        """Check if task is running."""
        return self.status == "running"

    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == "completed"

    @property
    def is_failed(self) -> bool:
        """Check if task is failed."""
        return self.status == "failed"

    def mark_started(self):
        """Mark task as started."""
        self.started_at = time.time()
        self.status = "running"

    def mark_completed(self, success: bool = True):
        """Mark task as completed."""
        self.completed_at = time.time()
        self.status = "completed" if success else "failed"

    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries and self.is_failed

    def increment_retry(self):
        """Increment retry count."""
        self.retry_count += 1
        self.status = "pending"


@dataclass
class TaskResult:
    """Represents the result of a task execution."""
    task_id: str
    success: bool

    # Result data
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    trade_history: List[Dict[str, Any]] = field(default_factory=list)
    portfolio_data: Dict[str, Any] = field(default_factory=dict)
    analysis_data: Dict[str, Any] = field(default_factory=dict)

    # Execution details
    execution_time: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

    # Error information
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    error_type: Optional[str] = None

    # Metadata
    process_id: Optional[int] = None
    worker_id: Optional[str] = None
    completed_at: float = field(default_factory=time.time)

    # Performance statistics
    cache_hits: int = 0
    cache_misses: int = 0
    data_processed_mb: float = 0.0

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

    @property
    def throughput_mb_per_sec(self) -> float:
        """Calculate data processing throughput."""
        if self.execution_time == 0:
            return 0.0
        return self.data_processed_mb / self.execution_time


@dataclass
class ProcessInfo:
    """Information about a worker process."""
    id: int
    pid: int
    worker_id: str
    status: ProcessStatus = ProcessStatus.IDLE

    # Resource allocation
    assigned_memory_mb: float = 0.0
    max_memory_mb: float = 1024.0
    cpu_cores_allocated: float = 1.0

    # Current task
    current_task_id: Optional[str] = None
    current_task_start_time: Optional[float] = None

    # Statistics
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    memory_peak_mb: float = 0.0

    # Health monitoring
    last_heartbeat: float = field(default_factory=time.time)
    error_count: int = 0
    restart_count: int = 0

    # Process lifecycle
    created_at: float = field(default_factory=time.time)
    last_recycled: Optional[float] = None

    @property
    def is_busy(self) -> bool:
        """Check if process is busy."""
        return self.status == ProcessStatus.BUSY

    @property
    def is_healthy(self) -> bool:
        """Check if process is healthy."""
        heartbeat_age = time.time() - self.last_heartbeat
        return heartbeat_age < 30.0 and self.error_count < 5  # 30 second timeout

    @property
    def success_rate(self) -> float:
        """Calculate task success rate."""
        total_tasks = self.tasks_completed + self.tasks_failed
        if total_tasks == 0:
            return 1.0
        return self.tasks_completed / total_tasks

    @property
    def average_task_time(self) -> float:
        """Calculate average task execution time."""
        if self.tasks_completed == 0:
            return 0.0
        return self.total_execution_time / self.tasks_completed

    def mark_task_started(self, task_id: str):
        """Mark task as started in this process."""
        self.current_task_id = task_id
        self.current_task_start_time = time.time()
        self.status = ProcessStatus.BUSY

    def mark_task_completed(self, success: bool = True):
        """Mark task as completed in this process."""
        if success:
            self.tasks_completed += 1
        else:
            self.tasks_failed += 1

        if self.current_task_start_time:
            execution_time = time.time() - self.current_task_start_time
            self.total_execution_time += execution_time

        self.current_task_id = None
        self.current_task_start_time = None
        self.status = ProcessStatus.IDLE
        self.last_heartbeat = time.time()

    def update_heartbeat(self):
        """Update process heartbeat."""
        self.last_heartbeat = time.time()


@dataclass
class ExecutionStats:
    """Overall execution statistics for the multiprocessing system."""

    # Task statistics
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    running_tasks: int = 0
    pending_tasks: int = 0

    # Performance metrics
    total_execution_time: float = 0.0
    average_task_time: float = 0.0
    tasks_per_second: float = 0.0

    # Resource usage
    total_memory_usage_mb: float = 0.0
    peak_memory_usage_mb: float = 0.0
    average_cpu_usage_percent: float = 0.0

    # Process statistics
    active_processes: int = 0
    max_processes: int = 0
    process_recycles: int = 0

    # Cache statistics
    cache_hits: int = 0
    cache_misses: int = 0

    # Error statistics
    total_errors: int = 0
    timeout_errors: int = 0
    memory_errors: int = 0

    # Timing
    start_time: float = field(default_factory=time.time)
    last_update_time: float = field(default_factory=time.time)

    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        total_completed = self.completed_tasks + self.failed_tasks
        if total_completed == 0:
            return 1.0
        return self.completed_tasks / total_completed

    @property
    def completion_rate(self) -> float:
        """Calculate task completion rate."""
        if self.total_tasks == 0:
            return 0.0
        return self.completed_tasks / self.total_tasks

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_cache_ops = self.cache_hits + self.cache_misses
        if total_cache_ops == 0:
            return 0.0
        return self.cache_hits / total_cache_ops

    @property
    def runtime(self) -> float:
        """Calculate total runtime."""
        return self.last_update_time - self.start_time

    def update_task_counts(self, completed: int, failed: int, running: int, pending: int):
        """Update task count statistics."""
        self.completed_tasks = completed
        self.failed_tasks = failed
        self.running_tasks = running
        self.pending_tasks = pending
        self.total_tasks = completed + failed + running + pending
        self.last_update_time = time.time()

    def update_performance_metrics(self, total_time: float, memory_mb: float, cpu_percent: float):
        """Update performance metrics."""
        self.total_execution_time = total_time
        self.total_memory_usage_mb = memory_mb
        self.average_cpu_usage_percent = cpu_percent

        if self.completed_tasks > 0:
            self.average_task_time = total_time / self.completed_tasks

        runtime = self.runtime
        if runtime > 0:
            self.tasks_per_second = self.completed_tasks / runtime

        self.last_update_time = time.time()


# Factory functions for creating instances
def create_backtest_task(strategy_code: str,
                        parameters: Dict[str, Any],
                        priority: int = 0,
                        complexity: TaskComplexity = TaskComplexity.MEDIUM) -> Task:
    """Create a backtest task."""
    return Task(
        type=TaskType.BACKTEST,
        strategy_code=strategy_code,
        parameters=parameters,
        priority=priority,
        complexity=complexity
    )


def create_optimization_task(strategy_code: str,
                            parameter_grid: Dict[str, List[Any]],
                            priority: int = 0) -> Task:
    """Create an optimization task."""
    return Task(
        type=TaskType.OPTIMIZATION,
        strategy_code=strategy_code,
        parameters=parameter_grid,
        priority=priority,
        complexity=TaskComplexity.HIGH
    )


def create_task_result(task_id: str,
                      success: bool,
                      metrics: Dict[str, Any] = None) -> TaskResult:
    """Create a task result."""
    return TaskResult(
        task_id=task_id,
        success=success,
        performance_metrics=metrics or {}
    )


def create_process_info(pid: int, worker_id: str, max_memory_mb: float = 1024.0) -> ProcessInfo:
    """Create process information."""
    return ProcessInfo(
        id=pid,
        pid=pid,
        worker_id=worker_id,
        max_memory_mb=max_memory_mb
    )
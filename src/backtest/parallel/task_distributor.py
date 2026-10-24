"""
Intelligent Task Distribution Algorithm for CBSC multiprocessing backtesting.

Implements advanced task scheduling, load balancing, and optimization algorithms
to maximize throughput and minimize execution time for backtesting workloads.
"""

import time
import heapq
import logging
import threading
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import numpy as np
from abc import ABC, abstractmethod

from .models import Task, TaskResult, ProcessInfo, TaskType, TaskComplexity


class SchedulingStrategy(str, Enum):
    """Task scheduling strategies."""
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"
    PRIORITY_FIRST = "priority_first"
    COMPLEXITY_AWARE = "complexity_aware"
    AFFINITY_BASED = "affinity_based"
    ADAPTIVE = "adaptive"


class LoadMetric(str, Enum):
    """Load balancing metrics."""
    TASK_COUNT = "task_count"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    EXECUTION_TIME = "execution_time"
    QUEUE_DEPTH = "queue_depth"
    COMBINED = "combined"


@dataclass
class TaskEstimate:
    """Estimated task resource requirements."""
    task_id: str
    estimated_duration: float  # seconds
    memory_requirement: float   # MB
    cpu_requirement: float      # cores (0.0-1.0)
    io_intensity: float         # 0.0-1.0
    data_dependencies: Set[str] = field(default_factory=set)
    affinity_processes: Set[int] = field(default_factory=set)
    priority_score: float = 0.0


@dataclass
class ProcessLoad:
    """Current load information for a process."""
    process_id: int
    current_tasks: int = 0
    estimated_completion_time: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_utilization: float = 0.0
    queue_depth: int = 0
    recent_completion_times: deque = field(default_factory=lambda: deque(maxlen=10))
    task_history: List[str] = field(default_factory=list)
    specializations: Set[TaskType] = field(default_factory=set)

    @property
    def load_score(self) -> float:
        """Calculate overall load score (higher = more loaded)."""
        # Weighted combination of different load factors
        task_weight = self.current_tasks * 0.3
        cpu_weight = self.cpu_utilization * 0.25
        memory_weight = (self.memory_usage_mb / 1024.0) * 0.2  # Normalize to GB
        queue_weight = self.queue_depth * 0.25

        return task_weight + cpu_weight + memory_weight + queue_weight

    @property
    def average_completion_time(self) -> float:
        """Calculate average task completion time."""
        if not self.recent_completion_times:
            return 1.0  # Default estimate
        return sum(self.recent_completion_times) / len(self.recent_completion_times)

    def update_completion_time(self, duration: float):
        """Update recent completion times."""
        self.recent_completion_times.append(duration)


class TaskEstimator:
    """Estimates task resource requirements based on historical data and heuristics."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.TaskEstimator")
        self.historical_data: Dict[str, List[float]] = defaultdict(list)
        self.base_estimates = {
            TaskType.BACKTEST: {"duration": 5.0, "memory": 512.0, "cpu": 0.8},
            TaskType.OPTIMIZATION: {"duration": 30.0, "memory": 1024.0, "cpu": 1.0},
            TaskType.ANALYSIS: {"duration": 2.0, "memory": 256.0, "cpu": 0.4},
            TaskType.DATA_PROCESSING: {"duration": 10.0, "memory": 2048.0, "cpu": 0.6},
            TaskType.VALIDATION: {"duration": 1.0, "memory": 128.0, "cpu": 0.2}
        }

    def estimate_task(self, task: Task) -> TaskEstimate:
        """Estimate resource requirements for a task."""
        base = self.base_estimates.get(task.type, {"duration": 5.0, "memory": 512.0, "cpu": 0.8})

        # Adjust based on complexity
        complexity_multiplier = {
            TaskComplexity.LOW: 0.5,
            TaskComplexity.MEDIUM: 1.0,
            TaskComplexity.HIGH: 2.0,
            TaskComplexity.EXTREME: 4.0
        }.get(task.complexity, 1.0)

        # Adjust based on parameters
        param_factor = self._calculate_parameter_factor(task.parameters)

        # Get historical data if available
        historical_multiplier = self._get_historical_multiplier(task)

        # Calculate final estimates
        estimated_duration = base["duration"] * complexity_multiplier * param_factor * historical_multiplier
        memory_requirement = base["memory"] * complexity_multiplier * param_factor
        cpu_requirement = min(base["cpu"] * complexity_multiplier, 1.0)

        # Estimate I/O intensity based on task type
        io_intensity = self._estimate_io_intensity(task)

        # Calculate priority score
        priority_score = self._calculate_priority_score(task)

        return TaskEstimate(
            task_id=task.id,
            estimated_duration=estimated_duration,
            memory_requirement=memory_requirement,
            cpu_requirement=cpu_requirement,
            io_intensity=io_intensity,
            data_dependencies=set(task.dependencies),
            priority_score=priority_score
        )

    def _calculate_parameter_factor(self, parameters: Dict[str, Any]) -> float:
        """Calculate scaling factor based on task parameters."""
        if not parameters:
            return 1.0

        factor = 1.0

        # Common parameter patterns that affect execution time
        for key, value in parameters.items():
            if isinstance(value, (list, tuple)):
                factor *= max(1.0, len(value) / 10.0)  # Scale with list size
            elif isinstance(value, dict):
                factor *= max(1.0, len(value) / 5.0)   # Scale with dict size
            elif isinstance(value, (int, float)):
                if "range" in key.lower() or "grid" in key.lower():
                    factor *= max(1.0, value / 100.0)  # Scale with range size
                elif "iterations" in key.lower() or "trials" in key.lower():
                    factor *= max(1.0, value / 1000.0)  # Scale with iterations

        return min(factor, 10.0)  # Cap at 10x

    def _estimate_io_intensity(self, task: Task) -> float:
        """Estimate I/O intensity based on task characteristics."""
        if task.type == TaskType.DATA_PROCESSING:
            return 0.8
        elif task.type == TaskType.BACKTEST:
            # High if data_config suggests large datasets
            data_size = task.data_config.get("data_size_mb", 100)
            return min(0.9, data_size / 1000.0)
        elif task.type == TaskType.ANALYSIS:
            return 0.4
        else:
            return 0.2

    def _calculate_priority_score(self, task: Task) -> float:
        """Calculate priority score for task scheduling."""
        # Base priority from task field
        priority = task.priority

        # Boost for high complexity tasks (to prevent starvation)
        complexity_boost = {
            TaskComplexity.LOW: 0.0,
            TaskComplexity.MEDIUM: 0.1,
            TaskComplexity.HIGH: 0.2,
            TaskComplexity.EXTREME: 0.3
        }.get(task.complexity, 0.0)

        # Age-based boost (older tasks get higher priority)
        age = time.time() - task.created_at
        age_boost = min(age / 3600.0, 0.5)  # Max 0.5 boost after 1 hour

        return priority + complexity_boost + age_boost

    def _get_historical_multiplier(self, task: Task) -> float:
        """Get multiplier based on historical execution data."""
        # For simplicity, use task type as key
        key = f"{task.type}_{task.complexity}"

        if key not in self.historical_data or len(self.historical_data[key]) < 3:
            return 1.0

        # Calculate ratio of actual to estimated durations
        ratios = self.historical_data[key]
        avg_ratio = sum(ratios) / len(ratios)

        # Return inverse to adjust future estimates
        return 1.0 / avg_ratio

    def record_execution(self, task: Task, actual_duration: float, estimated_duration: float):
        """Record actual execution time for future estimates."""
        key = f"{task.type}_{task.complexity}"
        ratio = actual_duration / estimated_duration if estimated_duration > 0 else 1.0

        self.historical_data[key].append(ratio)

        # Keep only recent data (last 100 executions)
        if len(self.historical_data[key]) > 100:
            self.historical_data[key] = self.historical_data[key][-100:]


class SchedulingAlgorithm(ABC):
    """Abstract base class for task scheduling algorithms."""

    @abstractmethod
    def select_process(self, task_estimate: TaskEstimate, processes: List[ProcessLoad]) -> Optional[int]:
        """Select the best process for a given task."""
        pass


class RoundRobinScheduler(SchedulingAlgorithm):
    """Simple round-robin scheduler."""

    def __init__(self):
        self.last_process = -1

    def select_process(self, task_estimate: TaskEstimate, processes: List[ProcessLoad]) -> Optional[int]:
        if not processes:
            return None

        # Simple round-robin
        self.last_process = (self.last_process + 1) % len(processes)
        return processes[self.last_process].process_id


class LoadBalancedScheduler(SchedulingAlgorithm):
    """Load-balanced scheduler based on process load."""

    def select_process(self, task_estimate: TaskEstimate, processes: List[ProcessLoad]) -> Optional[int]:
        if not processes:
            return None

        # Find process with minimum load score
        best_process = min(processes, key=lambda p: p.load_score)
        return best_process.process_id


class PriorityFirstScheduler(SchedulingAlgorithm):
    """Priority-based scheduler that assigns high-priority tasks to least loaded processes."""

    def select_process(self, task_estimate: TaskEstimate, processes: List[ProcessLoad]) -> Optional[int]:
        if not processes:
            return None

        # Sort processes by load (ascending)
        sorted_processes = sorted(processes, key=lambda p: p.load_score)

        # For high priority tasks, use the least loaded process
        if task_estimate.priority_score > 5:
            return sorted_processes[0].process_id

        # For normal priority, use a balanced approach
        return sorted_processes[len(sorted_processes) // 2].process_id


class ComplexityAwareScheduler(SchedulingAlgorithm):
    """Complexity-aware scheduler that considers task complexity and process capabilities."""

    def select_process(self, task_estimate: TaskEstimate, processes: List[ProcessLoad]) -> Optional[int]:
        if not processes:
            return None

        suitable_processes = []

        for process in processes:
            # Check if process can handle the task requirements
            suitable = True

            # Memory constraint
            if process.memory_usage_mb + task_estimate.memory_requirement > 2048:  # 2GB limit
                suitable = False

            # CPU constraint
            if process.cpu_utilization + task_estimate.cpu_requirement > 0.95:
                suitable = False

            # Queue depth constraint
            if process.queue_depth > 10:
                suitable = False

            if suitable:
                suitable_processes.append(process)

        if not suitable_processes:
            # Fallback to least loaded process
            return min(processes, key=lambda p: p.load_score).process_id

        # Among suitable processes, choose the one with best specialization match
        # (This would require process specialization information)
        return min(suitable_processes, key=lambda p: p.load_score).process_id


class AdaptiveScheduler(SchedulingAlgorithm):
    """Adaptive scheduler that learns and adjusts its strategy."""

    def __init__(self):
        self.performance_history: Dict[str, List[float]] = defaultdict(list)
        self.strategy_weights = {
            "round_robin": 0.2,
            "load_balanced": 0.3,
            "priority_first": 0.3,
            "complexity_aware": 0.2
        }
        self.schedulers = {
            "round_robin": RoundRobinScheduler(),
            "load_balanced": LoadBalancedScheduler(),
            "priority_first": PriorityFirstScheduler(),
            "complexity_aware": ComplexityAwareScheduler()
        }

    def select_process(self, task_estimate: TaskEstimate, processes: List[ProcessLoad]) -> Optional[int]:
        if not processes:
            return None

        # For now, use weighted combination of strategies
        # In a full implementation, this would learn from performance
        return self.schedulers["load_balanced"].select_process(task_estimate, processes)

    def record_performance(self, strategy: str, task_duration: float, efficiency: float):
        """Record performance of a scheduling decision."""
        self.performance_history[strategy].append(efficiency)

        # Update weights based on performance (simplified)
        if len(self.performance_history[strategy]) > 10:
            avg_efficiency = sum(self.performance_history[strategy][-10:]) / 10
            # Increase weight for better performing strategies
            self.strategy_weights[strategy] *= (1.0 + avg_efficiency * 0.1)


class TaskDistributor:
    """
    Intelligent task distribution system for optimal workload allocation.

    Features:
    - Multiple scheduling algorithms
    - Load balancing across processes
    - Task dependency resolution
    - Adaptive learning from execution history
    - Real-time load monitoring
    """

    def __init__(self,
                 scheduling_strategy: SchedulingStrategy = SchedulingStrategy.LOAD_BALANCED,
                 load_metric: LoadMetric = LoadMetric.COMBINED,
                 enable_adaptive: bool = True,
                 rebalance_interval: float = 5.0):

        self.scheduling_strategy = scheduling_strategy
        self.load_metric = load_metric
        self.enable_adaptive = enable_adaptive
        self.rebalance_interval = rebalance_interval

        self.logger = logging.getLogger(f"{__name__}.TaskDistributor")

        # Core components
        self.estimator = TaskEstimator()
        self.scheduler = self._create_scheduler(scheduling_strategy)

        # Process tracking
        self.processes: Dict[int, ProcessLoad] = {}
        self.pending_tasks: List[Task] = []
        self.running_tasks: Dict[str, Tuple[int, float]] = {}  # task_id -> (process_id, start_time)
        self.completed_tasks: List[TaskResult] = []

        # Performance tracking
        self.total_tasks_distributed = 0
        self.total_execution_time = 0.0
        self.rebalance_count = 0

        # Thread safety
        self.lock = threading.RLock()

        # Background rebalancing
        self.rebalance_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

    def _create_scheduler(self, strategy: SchedulingStrategy) -> SchedulingAlgorithm:
        """Create scheduler instance based on strategy."""
        if strategy == SchedulingStrategy.ROUND_ROBIN:
            return RoundRobinScheduler()
        elif strategy == SchedulingStrategy.LOAD_BALANCED:
            return LoadBalancedScheduler()
        elif strategy == SchedulingStrategy.PRIORITY_FIRST:
            return PriorityFirstScheduler()
        elif strategy == SchedulingStrategy.COMPLEXITY_AWARE:
            return ComplexityAwareScheduler()
        elif strategy == SchedulingStrategy.ADAPTIVE:
            return AdaptiveScheduler()
        else:
            return LoadBalancedScheduler()  # Default

    def start(self):
        """Start the task distributor."""
        with self.lock:
            if self.rebalance_thread is not None:
                self.logger.warning("Task distributor already started")
                return

            self.stop_event.clear()
            self.rebalance_thread = threading.Thread(target=self._rebalance_loop, daemon=True)
            self.rebalance_thread.start()

            self.logger.info("Task distributor started")

    def stop(self):
        """Stop the task distributor."""
        with self.lock:
            self.stop_event.set()

            if self.rebalance_thread and self.rebalance_thread.is_alive():
                self.rebalance_thread.join(timeout=5.0)
                self.rebalance_thread = None

            self.logger.info("Task distributor stopped")

    def register_process(self, process_info: ProcessInfo):
        """Register a new process for task distribution."""
        with self.lock:
            process_load = ProcessLoad(
                process_id=process_info.id,
                specializations=set()  # Could be configured based on process capabilities
            )

            self.processes[process_info.id] = process_load
            self.logger.debug(f"Registered process {process_info.id}")

    def unregister_process(self, process_id: int):
        """Unregister a process."""
        with self.lock:
            if process_id in self.processes:
                del self.processes[process_id]
                self.logger.debug(f"Unregistered process {process_id}")

    def update_process_load(self, process_id: int, task_result: Optional[TaskResult] = None):
        """Update process load information."""
        with self.lock:
            if process_id not in self.processes:
                return

            process = self.processes[process_id]

            if task_result:
                # Update based on completed task
                process.current_tasks = max(0, process.current_tasks - 1)
                process.update_completion_time(task_result.execution_time)
                process.task_history.append(task_result.task_id)

                # Update memory usage (estimated)
                process.memory_usage_mb = max(0, process.memory_usage_mb - task_result.memory_usage_mb)

                # Record for estimator learning
                # Note: This would need the original task, which we don't have here
                # In a full implementation, we'd track this differently

                self.total_execution_time += task_result.execution_time
                self.completed_tasks.append(task_result)

            # Update other load metrics (in a real implementation, these would come from system monitoring)
            process.cpu_utilization = min(0.95, process.current_tasks * 0.1)
            process.queue_depth = len(self.pending_tasks)

    def distribute_task(self, task: Task) -> Optional[int]:
        """
        Distribute a task to the most suitable process.

        Returns:
            Process ID if distribution successful, None otherwise
        """
        with self.lock:
            if not self.processes:
                self.logger.warning("No processes available for task distribution")
                return None

            # Estimate task requirements
            task_estimate = self.estimator.estimate_task(task)

            # Check dependencies
            if not self._check_dependencies(task):
                self.logger.debug(f"Task {task.id} dependencies not met, keeping in pending queue")
                self.pending_tasks.append(task)
                return None

            # Select process using scheduler
            process_loads = list(self.processes.values())
            selected_process_id = self.scheduler.select_process(task_estimate, process_loads)

            if selected_process_id is None:
                self.logger.warning(f"No suitable process found for task {task.id}")
                self.pending_tasks.append(task)
                return None

            # Assign task to process
            self._assign_task_to_process(task, task_estimate, selected_process_id)

            self.total_tasks_distributed += 1
            return selected_process_id

    def _assign_task_to_process(self, task: Task, task_estimate: TaskEstimate, process_id: int):
        """Assign a task to a specific process."""
        process = self.processes[process_id]

        # Update process load
        process.current_tasks += 1
        process.memory_usage_mb += task_estimate.memory_requirement
        process.estimated_completion_time += task_estimate.estimated_duration
        process.queue_depth = max(0, process.queue_depth - 1)

        # Track running task
        self.running_tasks[task.id] = (process_id, time.time())

        # Mark task as started
        task.mark_started()

        self.logger.debug(f"Assigned task {task.id} to process {process_id} "
                         f"(est. duration: {task_estimate.estimated_duration:.2f}s)")

    def _check_dependencies(self, task: Task) -> bool:
        """Check if task dependencies are satisfied."""
        for dependency in task.dependencies:
            if dependency not in [rt.task_id for rt in self.completed_tasks]:
                return False
        return True

    def _rebalance_loop(self):
        """Background loop for periodic rebalancing."""
        while not self.stop_event.is_set():
            try:
                with self.lock:
                    self._rebalance_pending_tasks()
                    self._check_for_stragglers()

                time.sleep(self.rebalance_interval)

            except Exception as e:
                self.logger.error(f"Error in rebalance loop: {e}")

    def _rebalance_pending_tasks(self):
        """Rebalance pending tasks that might now be assignable."""
        if not self.pending_tasks:
            return

        newly_assignable = []
        still_pending = []

        for task in self.pending_tasks:
            if self._check_dependencies(task):
                newly_assignable.append(task)
            else:
                still_pending.append(task)

        self.pending_tasks = still_pending

        # Try to assign newly assignable tasks
        for task in newly_assignable:
            self.distribute_task(task)

        if newly_assignable:
            self.logger.info(f"Rebalanced {len(newly_assignable)} pending tasks")

    def _check_for_stragglers(self):
        """Check for long-running tasks (stragglers)."""
        current_time = time.time()
        straggler_threshold = 300.0  # 5 minutes

        for task_id, (process_id, start_time) in list(self.running_tasks.items()):
            runtime = current_time - start_time

            if runtime > straggler_threshold:
                self.logger.warning(f"Detected straggler task {task_id} on process {process_id} "
                                  f"(runtime: {runtime:.2f}s)")

                # In a full implementation, we might:
                # 1. Kill the task and restart it elsewhere
                # 2. Increase its priority
                # 3. Alert the monitoring system

                self.rebalance_count += 1

    def get_status(self) -> Dict[str, Any]:
        """Get current distributor status."""
        with self.lock:
            return {
                "processes": {
                    "total": len(self.processes),
                    "active": sum(1 for p in self.processes.values() if p.current_tasks > 0),
                    "average_load": np.mean([p.load_score for p in self.processes.values()]) if self.processes else 0.0
                },
                "tasks": {
                    "pending": len(self.pending_tasks),
                    "running": len(self.running_tasks),
                    "completed": len(self.completed_tasks),
                    "total_distributed": self.total_tasks_distributed
                },
                "performance": {
                    "total_execution_time": self.total_execution_time,
                    "average_task_time": self.total_execution_time / max(1, len(self.completed_tasks)),
                    "rebalance_count": self.rebalance_count
                },
                "scheduling": {
                    "strategy": self.scheduling_strategy,
                    "adaptive_enabled": self.enable_adaptive
                }
            }

    def get_load_distribution(self) -> List[Dict[str, Any]]:
        """Get detailed load distribution across processes."""
        with self.lock:
            return [
                {
                    "process_id": pid,
                    "load_score": proc.load_score,
                    "current_tasks": proc.current_tasks,
                    "memory_usage_mb": proc.memory_usage_mb,
                    "cpu_utilization": proc.cpu_utilization,
                    "queue_depth": proc.queue_depth,
                    "avg_completion_time": proc.average_completion_time,
                    "specializations": list(proc.specializations)
                }
                for pid, proc in self.processes.items()
            ]

    def update_strategy(self, new_strategy: SchedulingStrategy):
        """Update scheduling strategy."""
        with self.lock:
            old_strategy = self.scheduling_strategy
            self.scheduling_strategy = new_strategy
            self.scheduler = self._create_scheduler(new_strategy)

            self.logger.info(f"Updated scheduling strategy: {old_strategy} -> {new_strategy}")
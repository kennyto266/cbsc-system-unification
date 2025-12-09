#!/usr/bin/env python3
"""
Distributed Computing System for VectorBT Parameter Optimization
Phase 2.3: Distributed Computing Support

Implements multi-core parallel optimization, resource management,
load balancing, progress monitoring, and memory optimization for
large-scale parameter optimizations.
"""

import os
import time
import psutil
import logging
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Callable, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from queue import Queue
import threading
import pickle
import gc
from datetime import datetime
import json

# Import our advanced optimizer
try:
    from .advanced_optimizer import AdvancedOptimizer
    from .vectorbt_engine import VectorBTEngine
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.backtest.advanced_optimizer import AdvancedOptimizer
    from src.backtest.vectorbt_engine import VectorBTEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class OptimizationTask:
    """Represents a single optimization task"""
    task_id: str
    data: pd.DataFrame
    strategy: str
    param_ranges: Dict[str, Any]
    optimization_method: str
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    worker_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class ResourceUsage:
    """System resource usage information"""
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    active_tasks: int
    available_workers: int

class ResourceMonitor:
    """Monitor system resources and optimize resource allocation"""

    def __init__(self, max_memory_usage: float = 0.8):
        self.max_memory_usage = max_memory_usage
        self.monitoring = False
        self.monitor_thread = None
        self.resource_history = []

    def start_monitoring(self, interval: float = 1.0):
        """Start resource monitoring"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_resources,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()

    def _monitor_resources(self, interval: float):
        """Monitor system resources"""
        while self.monitoring:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory_info = psutil.virtual_memory()

                resource_info = {
                    'timestamp': datetime.now(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_info.percent,
                    'memory_mb': memory_info.used / 1024 / 1024,
                    'available_mb': memory_info.available / 1024 / 1024
                }

                self.resource_history.append(resource_info)

                # Keep only last 1000 records
                if len(self.resource_history) > 1000:
                    self.resource_history.pop(0)

                time.sleep(interval)

            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")

    def get_current_usage(self) -> ResourceUsage:
        """Get current resource usage"""
        cpu_percent = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()

        return ResourceUsage(
            cpu_percent=cpu_percent,
            memory_percent=memory_info.percent,
            memory_mb=memory_info.used / 1024 / 1024,
            active_tasks=0,  # To be updated by task manager
            available_workers=mp.cpu_count()
        )

    def should_throttle(self) -> bool:
        """Check if we should throttle task execution"""
        current_usage = self.get_current_usage()
        return (
            current_usage.memory_percent > (self.max_memory_usage * 100) or
            current_usage.cpu_percent > 95
        )

class TaskQueue:
    """Priority task queue with load balancing"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queue = Queue(maxsize=max_size)
        self._task_dict = {}  # task_id -> task
        self._lock = threading.Lock()

    def put(self, task: OptimizationTask):
        """Add task to queue"""
        with self._lock:
            if task.task_id in self._task_dict:
                logger.warning(f"Task {task.task_id} already exists")
                return False

            try:
                self._queue.put(task, block=False)
                self._task_dict[task.task_id] = task
                return True
            except Exception as e:
                logger.error(f"Failed to add task to queue: {e}")
                return False

    def get(self, timeout: float = None) -> Optional[OptimizationTask]:
        """Get next task from queue"""
        try:
            task = self._queue.get(timeout=timeout)
            with self._lock:
                if task.task_id in self._task_dict:
                    del self._task_dict[task.task_id]
            return task
        except Exception:
            return None

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get status of a specific task"""
        with self._lock:
            task = self._task_dict.get(task_id)
            return task.status if task else None

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        with self._lock:
            task = self._task_dict.get(task_id)
            if task and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                return True
            return False

    def get_pending_count(self) -> int:
        """Get number of pending tasks"""
        return self._queue.qsize()

    def clear_completed(self):
        """Clear completed tasks from dictionary"""
        with self._lock:
            completed_tasks = [
                task_id for task_id, task in self._task_dict.items()
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            ]
            for task_id in completed_tasks:
                del self._task_dict[task_id]

class DistributedOptimizer:
    """Main distributed optimization system"""

    def __init__(
        self,
        max_workers: Optional[int] = None,
        max_memory_usage: float = 0.8,
        enable_gpu: bool = False
    ):
        self.max_workers = max_workers or min(mp.cpu_count(), 32)
        self.max_memory_usage = max_memory_usage
        self.enable_gpu = enable_gpu

        # Initialize components
        self.resource_monitor = ResourceMonitor(max_memory_usage)
        self.task_queue = TaskQueue()
        self.active_tasks = {}  # task_id -> worker_id
        self.worker_stats = {}  # worker_id -> stats

        # Load balancing
        self.load_balancer = LoadBalancer(self.max_workers)

        # Progress tracking
        self.progress_callbacks = []

        # Optimization engines (one per worker to avoid conflicts)
        self.engine_pool = []

        logger.info(f"DistributedOptimizer initialized with {self.max_workers} workers")

    def start(self):
        """Start the distributed optimization system"""
        logger.info("Starting distributed optimization system...")

        # Start resource monitoring
        self.resource_monitor.start_monitoring()

        # Initialize worker processes
        self._initialize_workers()

        logger.info("Distributed optimization system started")

    def stop(self):
        """Stop the distributed optimization system"""
        logger.info("Stopping distributed optimization system...")

        # Stop resource monitoring
        self.resource_monitor.stop_monitoring()

        # Cancel all pending tasks
        self.cancel_all_tasks()

        logger.info("Distributed optimization system stopped")

    def _initialize_workers(self):
        """Initialize worker processes"""
        logger.info(f"Initializing {self.max_workers} workers...")

        for i in range(self.max_workers):
            self.worker_stats[i] = {
                'tasks_completed': 0,
                'tasks_failed': 0,
                'total_execution_time': 0.0,
                'memory_peak': 0.0
            }

    def submit_optimization_task(
        self,
        task_id: str,
        data: pd.DataFrame,
        strategy: str,
        param_ranges: Dict[str, Any],
        optimization_method: str = "bayesian",
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> bool:
        """Submit an optimization task"""

        task = OptimizationTask(
            task_id=task_id,
            data=data,
            strategy=strategy,
            param_ranges=param_ranges,
            optimization_method=optimization_method,
            priority=priority
        )

        return self.task_queue.put(task)

    def execute_task(
        self,
        task: OptimizationTask,
        worker_id: int
    ) -> Dict[str, Any]:
        """Execute a single optimization task"""

        start_time = time.time()

        try:
            # Update task status
            task.status = TaskStatus.RUNNING
            task.worker_id = worker_id
            task.start_time = datetime.now()

            # Create optimization engine for this worker
            optimizer = AdvancedOptimizer()

            logger.info(f"Worker {worker_id} executing task {task.task_id}")

            # Execute optimization based on method
            if task.optimization_method == "bayesian":
                result = optimizer.optimize_bayesian(
                    data=task.data,
                    strategy=task.strategy,
                    param_bounds=task.param_ranges,
                    n_calls=50
                )
            elif task.optimization_method == "genetic":
                result = optimizer.optimize_genetic(
                    data=task.data,
                    strategy=task.strategy,
                    param_ranges=task.param_ranges,
                    population_size=50,
                    generations=20
                )
            elif task.optimization_method == "vectorbt":
                # Use VectorBT native optimization
                vectorbt_engine = VectorBTEngine()
                result = vectorbt_engine.optimize_parameters(
                    data=task.data,
                    strategy=task.strategy,
                    param_ranges=task.param_ranges
                )
            else:
                # Default to advanced optimizer
                result = optimizer.optimize(
                    data=task.data,
                    strategy=task.strategy,
                    param_ranges=task.param_ranges
                )

            # Update task status
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.now()
            task.result = result

            execution_time = time.time() - start_time

            # Update worker statistics
            self.worker_stats[worker_id]['tasks_completed'] += 1
            self.worker_stats[worker_id]['total_execution_time'] += execution_time

            # Clean up memory
            gc.collect()

            logger.info(f"Task {task.task_id} completed by worker {worker_id} in {execution_time:.2f}s")

            return result

        except Exception as e:
            # Update task status with error
            task.status = TaskStatus.FAILED
            task.end_time = datetime.now()
            task.error = str(e)

            execution_time = time.time() - start_time

            # Update worker statistics
            self.worker_stats[worker_id]['tasks_failed'] += 1
            self.worker_stats[worker_id]['total_execution_time'] += execution_time

            logger.error(f"Task {task.task_id} failed on worker {worker_id}: {e}")

            return {
                'error': str(e),
                'task_id': task.task_id,
                'worker_id': worker_id,
                'execution_time': execution_time
            }

    def run_optimization(
        self,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Run the distributed optimization process"""

        logger.info("Starting distributed optimization...")
        start_time = time.time()

        results = []
        completed_tasks = 0
        failed_tasks = 0

        try:
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit initial batch of tasks
                futures = {}

                while True:
                    # Check resource constraints
                    if self.resource_monitor.should_throttle():
                        logger.warning("Resource usage high, throttling...")
                        time.sleep(1)
                        continue

                    # Submit new tasks if workers are available
                    while len(futures) < self.max_workers:
                        task = self.task_queue.get(timeout=0.1)
                        if not task:
                            break

                        future = executor.submit(self.execute_task, task, len(futures))
                        futures[future] = task

                    # Check for completed tasks
                    completed_futures = []
                    for future, task in futures.items():
                        if future.done():
                            try:
                                result = future.result(timeout=1.0)
                                results.append(result)

                                if 'error' in result:
                                    failed_tasks += 1
                                else:
                                    completed_tasks += 1

                            except Exception as e:
                                logger.error(f"Task execution error: {e}")
                                failed_tasks += 1

                            completed_futures.append(future)

                            # Notify progress callbacks
                            self._notify_progress(completed_tasks, failed_tasks)

                    # Remove completed futures
                    for future in completed_futures:
                        del futures[future]

                    # Check if we're done
                    if (self.task_queue.get_pending_count() == 0 and
                        len(futures) == 0):
                        break

                    # Check timeout
                    if timeout and (time.time() - start_time) > timeout:
                        logger.warning("Optimization timeout reached")
                        break

        except Exception as e:
            logger.error(f"Distributed optimization error: {e}")

        total_time = time.time() - start_time

        # Calculate statistics
        total_tasks = completed_tasks + failed_tasks
        success_rate = completed_tasks / total_tasks if total_tasks > 0 else 0

        summary = {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'success_rate': success_rate,
            'total_execution_time': total_time,
            'average_time_per_task': total_time / total_tasks if total_tasks > 0 else 0,
            'workers_used': self.max_workers,
            'results': results
        }

        logger.info(f"Distributed optimization completed: {completed_tasks}/{total_tasks} tasks successful")

        return summary

    def _notify_progress(self, completed: int, failed: int):
        """Notify progress callbacks"""
        total = completed + failed
        for callback in self.progress_callbacks:
            try:
                callback(completed, failed, total)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

    def cancel_all_tasks(self):
        """Cancel all pending tasks"""
        # Clear the task queue
        while self.task_queue.get_pending_count() > 0:
            self.task_queue.get(timeout=0.1)

        logger.info("All pending tasks cancelled")

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        resource_usage = self.resource_monitor.get_current_usage()

        status = {
            'resource_usage': {
                'cpu_percent': resource_usage.cpu_percent,
                'memory_percent': resource_usage.memory_percent,
                'memory_mb': resource_usage.memory_mb,
                'available_workers': resource_usage.available_workers
            },
            'task_queue': {
                'pending_tasks': self.task_queue.get_pending_count(),
                'active_tasks': len(self.active_tasks)
            },
            'worker_stats': self.worker_stats.copy(),
            'system_health': 'HEALTHY' if not self.resource_monitor.should_throttle() else 'THROTTLED'
        }

        return status

    def optimize_memory_usage(self):
        """Optimize memory usage"""
        # Force garbage collection
        gc.collect()

        # Clear completed tasks from queue
        self.task_queue.clear_completed()

        logger.info("Memory usage optimized")

class LoadBalancer:
    """Load balancer for distributing tasks across workers"""

    def __init__(self, max_workers: int):
        self.max_workers = max_workers
        self.worker_loads = [0] * max_workers
        self.worker_speeds = [1.0] * max_workers  # Relative speed factors

    def get_best_worker(self) -> int:
        """Get the best available worker based on load and speed"""
        # Calculate load scores (lower is better)
        scores = []
        for i in range(self.max_workers):
            load_score = self.worker_loads[i] / self.worker_speeds[i]
            scores.append((load_score, i))

        # Return worker with lowest score
        scores.sort()
        return scores[0][1]

    def assign_task(self, worker_id: int):
        """Assign a task to a worker"""
        self.worker_loads[worker_id] += 1

    def complete_task(self, worker_id: int, execution_time: float):
        """Mark a task as completed and update worker speed"""
        self.worker_loads[worker_id] -= 1

        # Update speed factor based on execution time
        # (faster execution = higher speed factor)
        avg_time = 10.0  # Expected average time
        speed_factor = avg_time / execution_time if execution_time > 0 else 1.0

        # Exponential moving average for speed factor
        alpha = 0.1
        self.worker_speeds[worker_id] = (
            alpha * speed_factor +
            (1 - alpha) * self.worker_speeds[worker_id]
        )

    def get_load_distribution(self) -> List[int]:
        """Get current load distribution across workers"""
        return self.worker_loads.copy()

# Utility functions for common optimization patterns

def parallel_parameter_sweep(
    data: pd.DataFrame,
    strategy: str,
    param_ranges: Dict[str, List],
    max_workers: Optional[int] = None,
    chunk_size: int = 100
) -> Dict[str, Any]:
    """
    Perform parallel parameter sweep across multiple parameter combinations

    Args:
        data: Market data
        strategy: Strategy name
        param_ranges: Dictionary of parameter ranges
        max_workers: Maximum number of workers
        chunk_size: Size of parameter chunks per worker

    Returns:
        Optimization results summary
    """

    # Generate all parameter combinations
    import itertools

    param_names = list(param_ranges.keys())
    param_values = list(param_ranges.values())

    all_combinations = []
    for combination in itertools.product(*param_values):
        param_dict = dict(zip(param_names, combination))
        all_combinations.append(param_dict)

    logger.info(f"Generated {len(all_combinations)} parameter combinations")

    # Split into chunks for parallel processing
    chunks = [
        all_combinations[i:i + chunk_size]
        for i in range(0, len(all_combinations), chunk_size)
    ]

    # Initialize distributed optimizer
    optimizer = DistributedOptimizer(max_workers=max_workers)
    optimizer.start()

    try:
        # Submit chunk tasks
        for i, chunk in enumerate(chunks):
            task_id = f"chunk_{i:04d}"
            optimizer.submit_optimization_task(
                task_id=task_id,
                data=data,
                strategy=strategy,
                param_ranges={'combinations': chunk},
                optimization_method="vectorbt",
                priority=TaskPriority.NORMAL
            )

        # Run optimization
        results = optimizer.run_optimization()

        # Find best parameters across all chunks
        best_result = None
        best_score = float('-inf')

        for result in results['results']:
            if 'best_params' in result and 'best_score' in result:
                if result['best_score'] > best_score:
                    best_score = result['best_score']
                    best_result = result

        return {
            'total_combinations': len(all_combinations),
            'chunks_processed': len(chunks),
            'best_parameters': best_result['best_params'] if best_result else None,
            'best_score': best_score,
            'optimization_summary': results,
            'worker_stats': optimizer.get_system_status()['worker_stats']
        }

    finally:
        optimizer.stop()

# Performance monitoring and profiling

def profile_optimization_performance(
    data: pd.DataFrame,
    strategy: str,
    param_ranges: Dict[str, Any],
    optimization_methods: List[str] = ["bayesian", "genetic", "vectorbt"]
) -> Dict[str, Any]:
    """
    Profile performance of different optimization methods

    Args:
        data: Market data
        strategy: Strategy name
        param_ranges: Parameter ranges
        optimization_methods: List of methods to test

    Returns:
        Performance comparison results
    """

    results = {}

    for method in optimization_methods:
        logger.info(f"Profiling {method} optimization...")

        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        try:
            # Run optimization
            if method == "vectorbt":
                engine = VectorBTEngine()
                result = engine.optimize_parameters(data, strategy, param_ranges)
            else:
                optimizer = AdvancedOptimizer()

                if method == "bayesian":
                    result = optimizer.optimize_bayesian(data, strategy, param_ranges)
                elif method == "genetic":
                    result = optimizer.optimize_genetic(data, strategy, param_ranges)
                else:
                    result = optimizer.optimize(data, strategy, param_ranges)

            execution_time = time.time() - start_time
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_usage = end_memory - start_memory

            results[method] = {
                'success': True,
                'execution_time': execution_time,
                'memory_usage_mb': memory_usage,
                'best_score': result.get('best_score', 0),
                'convergence_iterations': result.get('iterations', 0),
                'result': result
            }

        except Exception as e:
            execution_time = time.time() - start_time
            results[method] = {
                'success': False,
                'execution_time': execution_time,
                'error': str(e)
            }

    # Create performance comparison
    comparison = {
        'methods_tested': optimization_methods,
        'method_performance': results,
        'fastest_method': min(
            [m for m in results.keys() if results[m]['success']],
            key=lambda m: results[m]['execution_time']
        ) if any(results[m]['success'] for m in results) else None,
        'best_score_method': max(
            [m for m in results.keys() if results[m]['success']],
            key=lambda m: results[m]['best_score']
        ) if any(results[m]['success'] for m in results) else None
    }

    return comparison

# Example usage and testing functions

def test_distributed_optimization():
    """Test the distributed optimization system"""

    logger.info("Testing distributed optimization system...")

    # Generate test data
    dates = pd.date_range('2022-01-01', periods=252, freq='D')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.normal(0.001, 0.02, 252))

    data = pd.DataFrame({
        'open': prices * (1 + np.random.normal(0, 0.005, 252)),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.01, 252))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.01, 252))),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 252)
    }, index=dates)

    # Test parallel parameter sweep
    param_ranges = {
        'rsi_period': [10, 14, 20],
        'oversold': [20, 30, 40],
        'overbought': [60, 70, 80]
    }

    result = parallel_parameter_sweep(
        data=data,
        strategy='RSI_MEAN_REVERSION',
        param_ranges=param_ranges,
        max_workers=4,
        chunk_size=3
    )

    logger.info(f"Parallel sweep completed: {result['total_combinations']} combinations tested")
    logger.info(f"Best parameters: {result['best_parameters']}")
    logger.info(f"Best score: {result['best_score']}")

    return result

if __name__ == "__main__":
    # Test the distributed optimization system
    test_distributed_optimization()
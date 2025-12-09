#!/usr/bin/env python3
"""
Threaded Optimization System for VectorBT Parameter Optimization
Phase 2.3: Distributed Computing Support (Threaded Version)

Implements multi-threaded parallel optimization, resource management,
load balancing, and memory optimization for large-scale optimizations.
Uses threading instead of multiprocessing to avoid pickle serialization issues.
"""

import time
import psutil
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from queue import Queue
import gc
from datetime import datetime
import json
import os

# Import our optimization engines
try:
    from .advanced_optimizer import AdvancedOptimizer
    from .vectorbt_engine import VectorBTEngine
except ImportError:
    import sys
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

class ThreadedOptimizer:
    """Threaded optimization system with resource management"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.task_queue = Queue()
        self.active_tasks = {}
        self.completed_tasks = {}
        self.worker_stats = {}
        self.progress_callbacks = []

        # Thread synchronization
        self._lock = threading.Lock()
        self._shutdown_event = threading.Event()

        # Initialize worker stats
        for i in range(max_workers):
            self.worker_stats[i] = {
                'tasks_completed': 0,
                'tasks_failed': 0,
                'total_execution_time': 0.0,
                'memory_peak': 0.0
            }

        logger.info(f"ThreadedOptimizer initialized with {max_workers} workers")

    def add_progress_callback(self, callback):
        """Add progress callback function"""
        self.progress_callbacks.append(callback)

    def submit_task(self, task: OptimizationTask) -> bool:
        """Submit an optimization task"""
        try:
            self.task_queue.put(task, block=False)
            logger.info(f"Task {task.task_id} submitted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to submit task {task.task_id}: {e}")
            return False

    def create_optimization_task(
        self,
        task_id: str,
        data: pd.DataFrame,
        strategy: str,
        param_ranges: Dict[str, Any],
        optimization_method: str = "vectorbt",
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> OptimizationTask:
        """Create an optimization task"""
        return OptimizationTask(
            task_id=task_id,
            data=data,
            strategy=strategy,
            param_ranges=param_ranges,
            optimization_method=optimization_method,
            priority=priority
        )

    def execute_task(self, task: OptimizationTask, worker_id: int) -> Dict[str, Any]:
        """Execute a single optimization task"""
        start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        try:
            # Update task status
            with self._lock:
                task.status = TaskStatus.RUNNING
                task.worker_id = worker_id
                task.start_time = datetime.now()
                self.active_tasks[task.task_id] = task

            logger.info(f"Worker {worker_id} executing task {task.task_id}")

            # Execute optimization based on method
            if task.optimization_method == "vectorbt":
                result = self._execute_vectorbt_optimization(task)
            elif task.optimization_method == "bayesian":
                result = self._execute_bayesian_optimization(task)
            elif task.optimization_method == "genetic":
                result = self._execute_genetic_optimization(task)
            else:
                result = self._execute_default_optimization(task)

            # Update task status
            execution_time = time.time() - start_time
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024

            with self._lock:
                task.status = TaskStatus.COMPLETED
                task.end_time = datetime.now()
                task.result = result
                self.completed_tasks[task.task_id] = task
                if task.task_id in self.active_tasks:
                    del self.active_tasks[task.task_id]

            # Update worker statistics
            self.worker_stats[worker_id]['tasks_completed'] += 1
            self.worker_stats[worker_id]['total_execution_time'] += execution_time
            self.worker_stats[worker_id]['memory_peak'] = max(
                self.worker_stats[worker_id]['memory_peak'],
                final_memory - initial_memory
            )

            # Clean up memory
            gc.collect()

            logger.info(f"Task {task.task_id} completed by worker {worker_id} in {execution_time:.2f}s")

            # Notify progress callbacks
            self._notify_progress()

            return result

        except Exception as e:
            execution_time = time.time() - start_time

            with self._lock:
                task.status = TaskStatus.FAILED
                task.end_time = datetime.now()
                task.error = str(e)
                self.completed_tasks[task.task_id] = task
                if task.task_id in self.active_tasks:
                    del self.active_tasks[task.task_id]

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

    def _execute_vectorbt_optimization(self, task: OptimizationTask) -> Dict[str, Any]:
        """Execute VectorBT optimization"""
        engine = VectorBTEngine()
        return engine.optimize_parameters(
            data=task.data,
            strategy=task.strategy,
            param_ranges=task.param_ranges
        )

    def _execute_bayesian_optimization(self, task: OptimizationTask) -> Dict[str, Any]:
        """Execute Bayesian optimization"""
        optimizer = AdvancedOptimizer()

        # Convert param_ranges to param_bounds if needed
        param_bounds = {}
        for param, values in task.param_ranges.items():
            if isinstance(values, (list, tuple)) and len(values) == 2:
                param_bounds[param] = tuple(values)
            elif isinstance(values, list):
                param_bounds[param] = (min(values), max(values))
            else:
                param_bounds[param] = (values, values)

        return optimizer.optimize_bayesian(
            data=task.data,
            strategy=task.strategy,
            param_bounds=param_bounds,
            n_calls=30
        )

    def _execute_genetic_optimization(self, task: OptimizationTask) -> Dict[str, Any]:
        """Execute Genetic optimization"""
        optimizer = AdvancedOptimizer()
        return optimizer.optimize_genetic(
            data=task.data,
            strategy=task.strategy,
            param_ranges=task.param_ranges,
            population_size=30,
            generations=15
        )

    def _execute_default_optimization(self, task: OptimizationTask) -> Dict[str, Any]:
        """Execute default optimization"""
        optimizer = AdvancedOptimizer()
        return optimizer.optimize(
            data=task.data,
            strategy=task.strategy,
            param_ranges=task.param_ranges
        )

    def _notify_progress(self):
        """Notify progress callbacks"""
        completed = len(self.completed_tasks)
        failed = sum(1 for task in self.completed_tasks.values() if task.status == TaskStatus.FAILED)
        total = completed + len(self.active_tasks)

        for callback in self.progress_callbacks:
            try:
                callback(completed, failed, total)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

    def run_optimization(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Run the threaded optimization process"""
        logger.info("Starting threaded optimization...")
        start_time = time.time()

        results = []
        completed_tasks = 0
        failed_tasks = 0

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []

                while True:
                    # Submit new tasks if workers are available
                    while len(futures) < self.max_workers and not self.task_queue.empty():
                        try:
                            task = self.task_queue.get(timeout=0.1)
                            future = executor.submit(self.execute_task, task, len(futures))
                            futures.append((future, task))
                        except Exception:
                            break

                    # Check for completed tasks
                    completed_futures = []
                    for future, task in futures:
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

                            completed_futures.append((future, task))

                    # Remove completed futures
                    for future, task in completed_futures:
                        futures.remove((future, task))

                    # Check if we're done
                    if self.task_queue.empty() and len(futures) == 0:
                        break

                    # Check timeout
                    if timeout and (time.time() - start_time) > timeout:
                        logger.warning("Optimization timeout reached")
                        break

                    # Small delay to prevent busy waiting
                    time.sleep(0.1)

        except Exception as e:
            logger.error(f"Threaded optimization error: {e}")

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
            'worker_stats': self.worker_stats.copy(),
            'results': results
        }

        logger.info(f"Threaded optimization completed: {completed_tasks}/{total_tasks} tasks successful")

        return summary

    def get_task_results(self) -> Dict[str, OptimizationTask]:
        """Get all completed task results"""
        return self.completed_tasks.copy()

    def get_best_result(self, metric: str = 'sharpe_ratio') -> Optional[Dict[str, Any]]:
        """Get best result based on specified metric"""
        best_result = None
        best_score = float('-inf')

        for task in self.completed_tasks.values():
            if (task.status == TaskStatus.COMPLETED and
                task.result and 'best_score' in task.result):

                if task.result['best_score'] > best_score:
                    best_score = task.result['best_score']
                    best_result = task.result

        return best_result

    def cancel_all_tasks(self):
        """Cancel all pending tasks"""
        # Clear the task queue
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except Exception:
                break

        logger.info("All pending tasks cancelled")

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        resource_usage = psutil.virtual_memory()

        status = {
            'resource_usage': {
                'memory_percent': resource_usage.percent,
                'memory_mb': resource_usage.used / 1024 / 1024,
                'available_mb': resource_usage.available / 1024 / 1024
            },
            'task_status': {
                'pending_tasks': self.task_queue.qsize(),
                'active_tasks': len(self.active_tasks),
                'completed_tasks': len(self.completed_tasks)
            },
            'worker_stats': self.worker_stats.copy(),
            'system_health': 'HEALTHY'
        }

        return status

# Utility functions for common optimization patterns

def parallel_parameter_sweep_threaded(
    data: pd.DataFrame,
    strategy: str,
    param_ranges: Dict[str, List],
    max_workers: int = 4
) -> Dict[str, Any]:
    """
    Perform parallel parameter sweep using threading

    Args:
        data: Market data
        strategy: Strategy name
        param_ranges: Dictionary of parameter ranges
        max_workers: Maximum number of worker threads

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

    # Initialize threaded optimizer
    optimizer = ThreadedOptimizer(max_workers=max_workers)

    # Submit all combinations as individual tasks
    for i, combination in enumerate(all_combinations):
        task_id = f"param_combo_{i:04d}"

        # Create param_ranges with single values for this combination
        single_param_ranges = {k: [v] for k, v in combination.items()}

        task = optimizer.create_optimization_task(
            task_id=task_id,
            data=data,
            strategy=strategy,
            param_ranges=single_param_ranges,
            optimization_method="vectorbt",
            priority=TaskPriority.NORMAL
        )

        optimizer.submit_task(task)

    # Run optimization
    results = optimizer.run_optimization()

    # Find best parameters across all combinations
    best_result = optimizer.get_best_result()

    return {
        'total_combinations': len(all_combinations),
        'best_parameters': best_result['best_params'] if best_result else None,
        'best_score': best_result['best_score'] if best_result else None,
        'optimization_summary': results,
        'all_task_results': optimizer.get_task_results()
    }

def test_threaded_optimization():
    """Test the threaded optimization system"""
    logger.info("Testing threaded optimization system...")

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

    result = parallel_parameter_sweep_threaded(
        data=data,
        strategy='RSI_MEAN_REVERSION',
        param_ranges=param_ranges,
        max_workers=4
    )

    logger.info(f"Parallel sweep completed: {result['total_combinations']} combinations tested")
    logger.info(f"Success rate: {result['optimization_summary']['success_rate']:.2%}")

    if result['best_parameters']:
        logger.info(f"Best parameters: {result['best_parameters']}")
        logger.info(f"Best score: {result['best_score']:.4f}")

    return result

if __name__ == "__main__":
    # Test the threaded optimization system
    test_threaded_optimization()
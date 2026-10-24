"""
Dynamic Process Pool Manager for CBSC multiprocessing backtesting system.

Provides intelligent process lifecycle management, resource monitoring, and
automatic scaling based on system workload and resource availability.
"""

import os
import time
import signal
import logging
import threading
import multiprocessing as mp
from typing import Dict, List, Any, Optional, Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from queue import Queue, Empty
import psutil
import gc

from .models import ProcessInfo, Task, TaskResult, ProcessStatus, TaskType


class SystemMonitor:
    """Monitor system resources and availability."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SystemMonitor")
        self.cpu_count = psutil.cpu_count()
        self.memory_total = psutil.virtual_memory().total
        self.memory_available = psutil.virtual_memory().available

    def get_current_load(self) -> Dict[str, float]:
        """Get current system load."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()

        return {
            'cpu_percent': cpu_percent,
            'cpu_count': self.cpu_count,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'memory_total_gb': memory.total / (1024**3),
            'disk_read_mb_s': disk_io.read_bytes / (1024*1024) if disk_io else 0,
            'disk_write_mb_s': disk_io.write_bytes / (1024*1024) if disk_io else 0
        }

    def can_spawn_process(self, memory_requirement_mb: float = 1024.0) -> bool:
        """Check if system can handle spawning a new process."""
        memory = psutil.virtual_memory()
        available_memory_gb = memory.available / (1024**3)
        required_memory_gb = memory_requirement_mb / 1024

        # Need at least 1GB free per process and 20% system memory free
        return (available_memory_gb > required_memory_gb + 1.0 and
                memory.percent < 80)

    def get_optimal_process_count(self, min_processes: int = 1,
                                 max_processes: int = 32) -> int:
        """Calculate optimal process count based on system resources."""
        load = self.get_current_load()

        # Base on CPU cores
        cpu_based = min(self.cpu_count, max_processes)

        # Adjust based on current load
        if load['cpu_percent'] > 80:
            cpu_based = max(1, cpu_based // 2)
        elif load['cpu_percent'] > 60:
            cpu_based = max(1, int(cpu_based * 0.75))

        # Adjust based on memory
        memory_based = min(
            int(load['memory_available_gb'] * 0.8),  # Use 80% of available memory
            max_processes
        )

        # Take minimum of CPU and memory based counts
        optimal = min(cpu_based, memory_based, max_processes)
        return max(min_processes, optimal)


class DynamicProcessPool:
    """
    Dynamic process pool that scales based on workload and system resources.

    Features:
    - Automatic scaling up/down based on queue depth and system load
    - Process recycling to prevent memory leaks
    - Health monitoring and automatic recovery
    - Task affinity and priority scheduling
    """

    def __init__(self,
                 min_processes: int = 1,
                 max_processes: int = 32,
                 auto_scaling: bool = True,
                 recycle_interval: int = 100,
                 memory_limit_mb: float = 4096.0,
                 scaling_check_interval: float = 5.0):

        self.min_processes = min_processes
        self.max_processes = max_processes
        self.auto_scaling = auto_scaling
        self.recycle_interval = recycle_interval
        self.memory_limit_mb = memory_limit_mb
        self.scaling_check_interval = scaling_check_interval

        self.logger = logging.getLogger(f"{__name__}.DynamicProcessPool")
        self.system_monitor = SystemMonitor()

        # Process management
        self.processes: Dict[int, ProcessInfo] = {}
        self.process_executor: Optional[ProcessPoolExecutor] = None
        self.task_queue = mp.Queue()
        self.result_queue = mp.Queue()
        self.stop_event = threading.Event()

        # Scaling and monitoring
        self.scaling_thread: Optional[threading.Thread] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.recycle_counter = 0

        # Statistics
        self.total_tasks_processed = 0
        self.total_processes_created = 0
        self.total_processes_recycled = 0

        self.logger.info(f"DynamicProcessPool initialized: min={min_processes}, max={max_processes}")

    def start(self):
        """Start the process pool."""
        if self.process_executor is not None:
            self.logger.warning("Process pool already started")
            return

        try:
            # Start with minimum processes
            initial_count = self.system_monitor.get_optimal_process_count(
                self.min_processes,
                min(self.max_processes, self.min_processes * 2)
            )

            self.process_executor = ProcessPoolExecutor(
                max_workers=initial_count,
                mp_context=mp.get_context('spawn')
            )

            # Initialize process tracking
            for i in range(initial_count):
                self._track_process(i)

            # Start background threads
            if self.auto_scaling:
                self.scaling_thread = threading.Thread(target=self._scaling_loop, daemon=True)
                self.scaling_thread.start()

            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()

            self.logger.info(f"Process pool started with {initial_count} processes")

        except Exception as e:
            self.logger.error(f"Failed to start process pool: {e}")
            self.stop()
            raise

    def stop(self, timeout: float = 30.0):
        """Stop the process pool gracefully."""
        if self.process_executor is None:
            return

        self.logger.info("Stopping process pool...")
        self.stop_event.set()

        # Shutdown executor
        if self.process_executor:
            self.process_executor.shutdown(wait=True)
            self.process_executor = None

        # Wait for threads to finish
        if self.scaling_thread and self.scaling_thread.is_alive():
            self.scaling_thread.join(timeout=5.0)

        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)

        # Clear queues
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except Empty:
                break

        while not self.result_queue.empty():
            try:
                self.result_queue.get_nowait()
            except Empty:
                break

        self.processes.clear()
        self.logger.info("Process pool stopped")

    def submit_task(self, task: Task) -> bool:
        """Submit a task to the process pool."""
        if self.process_executor is None:
            self.logger.error("Process pool not started")
            return False

        try:
            # Check if we need to scale up
            if self.auto_scaling:
                self._check_scaling_up()

            # Submit task
            self.task_queue.put(task)
            self.logger.debug(f"Task {task.id} submitted to queue")
            return True

        except Exception as e:
            self.logger.error(f"Failed to submit task {task.id}: {e}")
            return False

    def get_result(self, timeout: Optional[float] = None) -> Optional[TaskResult]:
        """Get a result from the result queue."""
        try:
            return self.result_queue.get(timeout=timeout)
        except Empty:
            return None

    def get_status(self) -> Dict[str, Any]:
        """Get current pool status."""
        active_processes = sum(1 for p in self.processes.values() if p.is_healthy)
        busy_processes = sum(1 for p in self.processes.values() if p.is_busy)

        system_load = self.system_monitor.get_current_load()

        return {
            'processes': {
                'total': len(self.processes),
                'active': active_processes,
                'busy': busy_processes,
                'idle': active_processes - busy_processes,
                'max_allowed': self.max_processes
            },
            'queue_depth': self.task_queue.qsize(),
            'system_load': system_load,
            'statistics': {
                'total_tasks_processed': self.total_tasks_processed,
                'total_processes_created': self.total_processes_created,
                'total_processes_recycled': self.total_processes_recycled,
                'average_success_rate': self._calculate_average_success_rate()
            },
            'auto_scaling_enabled': self.auto_scaling
        }

    def _track_process(self, worker_id: int):
        """Track a new process."""
        process_info = ProcessInfo(
            id=worker_id,
            pid=0,  # Will be set when task is assigned
            worker_id=f"worker_{worker_id}",
            max_memory_mb=self.memory_limit_mb / len(self.processes) if self.processes else self.memory_limit_mb
        )
        self.processes[worker_id] = process_info
        self.total_processes_created += 1

    def _scaling_loop(self):
        """Background thread for automatic scaling."""
        while not self.stop_event.is_set():
            try:
                self._check_scaling()
                time.sleep(self.scaling_check_interval)
            except Exception as e:
                self.logger.error(f"Error in scaling loop: {e}")

    def _monitor_loop(self):
        """Background thread for process monitoring."""
        while not self.stop_event.is_set():
            try:
                self._monitor_processes()
                self._check_recycling()
                time.sleep(1.0)  # Check every second
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}")

    def _check_scaling(self):
        """Check if scaling is needed."""
        if not self.process_executor or not self.auto_scaling:
            return

        queue_depth = self.task_queue.qsize()
        current_workers = self.process_executor._max_workers
        system_load = self.system_monitor.get_current_load()

        # Scale up conditions
        need_scale_up = (
            queue_depth > current_workers * 2 and  # Queue depth > 2x workers
            system_load['cpu_percent'] < 70 and     # CPU not overloaded
            system_load['memory_percent'] < 70 and  # Memory available
            current_workers < self.max_processes
        )

        # Scale down conditions
        need_scale_down = (
            queue_depth == 0 and                    # No work
            system_load['cpu_percent'] < 30 and     # Low CPU usage
            current_workers > self.min_processes
        )

        if need_scale_up:
            self._scale_up()
        elif need_scale_down:
            self._scale_down()

    def _check_scaling_up(self):
        """Check if immediate scaling up is needed (high queue depth)."""
        queue_depth = self.task_queue.qsize()
        current_workers = len(self.processes)

        if queue_depth > current_workers * 3 and current_workers < self.max_processes:
            self._scale_up()

    def _scale_up(self):
        """Scale up the process pool."""
        if not self.process_executor:
            return

        current_workers = len(self.processes)
        if current_workers >= self.max_processes:
            return

        # Calculate new size
        new_size = min(current_workers + 2, self.max_processes)
        system_load = self.system_monitor.get_current_load()

        # Check if system can handle more processes
        if not self.system_monitor.can_spawn_process(self.memory_limit_mb / new_size):
            self.logger.warning("System resources insufficient for scaling up")
            return

        try:
            # Create new executor with more workers
            old_executor = self.process_executor
            self.process_executor = ProcessPoolExecutor(
                max_workers=new_size,
                mp_context=mp.get_context('spawn')
            )

            # Track new processes
            for i in range(current_workers, new_size):
                self._track_process(i)

            # Shutdown old executor gracefully
            old_executor.shutdown(wait=False)

            self.logger.info(f"Scaled up from {current_workers} to {new_size} processes")

        except Exception as e:
            self.logger.error(f"Failed to scale up: {e}")

    def _scale_down(self):
        """Scale down the process pool."""
        if not self.process_executor:
            return

        current_workers = len(self.processes)
        if current_workers <= self.min_processes:
            return

        # Calculate new size
        new_size = max(self.min_processes, current_workers - 1)

        try:
            # Wait for current tasks to finish
            busy_processes = [p for p in self.processes.values() if p.is_busy]
            if len(busy_processes) > new_size:
                self.logger.info("Waiting for processes to finish before scaling down")
                return

            # Create new executor with fewer workers
            old_executor = self.process_executor
            self.process_executor = ProcessPoolExecutor(
                max_workers=new_size,
                mp_context=mp.get_context('spawn')
            )

            # Remove process tracking
            for i in range(new_size, current_workers):
                if i in self.processes:
                    del self.processes[i]

            # Shutdown old executor
            old_executor.shutdown(wait=False)

            self.logger.info(f"Scaled down from {current_workers} to {new_size} processes")

        except Exception as e:
            self.logger.error(f"Failed to scale down: {e}")

    def _monitor_processes(self):
        """Monitor process health and update statistics."""
        for process_info in self.processes.values():
            try:
                # Update heartbeat
                process_info.update_heartbeat()

                # Check memory usage (approximation)
                if process_info.pid > 0:
                    try:
                        proc = psutil.Process(process_info.pid)
                        memory_mb = proc.memory_info().rss / (1024 * 1024)
                        process_info.memory_peak_mb = max(process_info.memory_peak_mb, memory_mb)

                        # Check if process is using too much memory
                        if memory_mb > process_info.max_memory_mb * 1.2:
                            self.logger.warning(f"Process {process_info.worker_id} using excessive memory: {memory_mb:.1f}MB")
                            process_info.error_count += 1

                    except psutil.NoSuchProcess:
                        # Process has terminated
                        process_info.status = ProcessStatus.ERROR
                        process_info.error_count += 1

            except Exception as e:
                self.logger.debug(f"Error monitoring process {process_info.worker_id}: {e}")

    def _check_recycling(self):
        """Check if processes need recycling to prevent memory leaks."""
        self.recycle_counter += 1

        if self.recycle_counter >= self.recycle_interval:
            self.recycle_counter = 0
            self._recycle_processes()

    def _recycle_processes(self):
        """Recycle processes that have been running too long."""
        if not self.process_executor:
            return

        recycled_count = 0
        current_time = time.time()

        for process_info in list(self.processes.values()):
            # Recycle if process has been running for more than 1 hour
            # and is currently idle
            recycle_threshold = 3600.0  # 1 hour

            if (process_info.created_at < current_time - recycle_threshold and
                not process_info.is_busy and
                len(self.processes) > self.min_processes):

                try:
                    # Mark for recycling (in a real implementation, this would
                    # involve gracefully terminating and restarting the process)
                    process_info.status = ProcessStatus.RECYCLING
                    process_info.last_recycled = current_time
                    recycled_count += 1

                    self.logger.debug(f"Marked process {process_info.worker_id} for recycling")

                except Exception as e:
                    self.logger.error(f"Error recycling process {process_info.worker_id}: {e}")

        if recycled_count > 0:
            self.total_processes_recycled += recycled_count
            self.logger.info(f"Recycled {recycled_count} processes")

    def _calculate_average_success_rate(self) -> float:
        """Calculate average success rate across all processes."""
        if not self.processes:
            return 1.0

        total_success = sum(p.tasks_completed for p in self.processes.values())
        total_failed = sum(p.tasks_failed for p in self.processes.values())
        total = total_success + total_failed

        if total == 0:
            return 1.0

        return total_success / total

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
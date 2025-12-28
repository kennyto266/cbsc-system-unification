"""
Parallel Processing Optimizer for Backtesting
============================================

High-performance parallel processing engine for backtesting with:
- Multi-process execution
- Task queue management
- Resource optimization
- Distributed computing support
- Memory-efficient chunking
- Progress tracking and monitoring

Author: CBSC Quant Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Callable, Union, Iterator
from dataclasses import dataclass, field
from enum import Enum
import logging
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import time
import psutil
import threading
import queue
from functools import partial
import pickle
import hashlib
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class ProcessingMode(str, Enum):
    """Parallel processing modes"""
    MULTI_PROCESS = "multi_process"
    MULTI_THREAD = "multi_thread"
    DISTRIBUTED = "distributed"


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ChunkingStrategy(str, Enum):
    """Data chunking strategies"""
    EQUAL_SIZE = "equal_size"
    TIME_BASED = "time_based"
    MEMORY_BASED = "memory_based"
    ADAPTIVE = "adaptive"


@dataclass
class ParallelConfig:
    """Parallel processing configuration"""
    mode: ProcessingMode = ProcessingMode.MULTI_PROCESS
    n_workers: int = -1  # -1 for auto-detect
    max_memory_gb: float = 4.0  # Maximum memory per worker
    chunk_size: Optional[int] = None
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.MEMORY_BASED

    # Resource limits
    max_tasks_per_worker: int = 100
    timeout_seconds: int = 3600
    memory_limit: Optional[str] = None

    # Optimization
    enable_caching: bool = True
    cache_dir: str = "/tmp/backtest_cache"
    prefetch_tasks: int = 2

    # Monitoring
    enable_progress_bar: bool = True
    log_interval: int = 10  # seconds


@dataclass
class ProcessingTask:
    """Processing task definition"""
    task_id: str
    function: Callable
    args: Tuple = ()
    kwargs: Dict = {}
    priority: TaskPriority = TaskPriority.NORMAL
    chunk_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Processing task result"""
    task_id: str
    result: Any
    execution_time: float
    memory_usage: float
    worker_id: int
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


class ChunkManager:
    """Manages data chunking for parallel processing"""

    def __init__(self, strategy: ChunkingStrategy, chunk_size: Optional[int] = None):
        self.strategy = strategy
        self.chunk_size = chunk_size

    def create_chunks(
        self,
        data: Union[pd.DataFrame, np.ndarray, List],
        n_workers: int
    ) -> List[Tuple[int, int]]:
        """
        Create chunk indices for data

        Args:
            data: Data to chunk
            n_workers: Number of workers

        Returns:
            List of (start_idx, end_idx) tuples
        """
        n_items = len(data)

        if self.strategy == ChunkingStrategy.EQUAL_SIZE:
            return self._create_equal_chunks(n_items, n_workers)
        elif self.strategy == ChunkingStrategy.TIME_BASED:
            return self._create_time_based_chunks(data, n_workers)
        elif self.strategy == ChunkingStrategy.MEMORY_BASED:
            return self._create_memory_based_chunks(data, n_workers)
        elif self.strategy == ChunkingStrategy.ADAPTIVE:
            return self._create_adaptive_chunks(data, n_workers)
        else:
            raise ValueError(f"Unknown chunking strategy: {self.strategy}")

    def _create_equal_chunks(self, n_items: int, n_workers: int) -> List[Tuple[int, int]]:
        """Create equal-sized chunks"""
        if self.chunk_size:
            n_chunks = n_items // self.chunk_size + (1 if n_items % self.chunk_size else 0)
            chunk_size = self.chunk_size
        else:
            chunk_size = n_items // n_workers + (1 if n_items % n_workers else 0)
            n_chunks = n_workers

        chunks = []
        for i in range(n_chunks):
            start = i * chunk_size
            end = min((i + 1) * chunk_size, n_items)
            chunks.append((start, end))

        return chunks

    def _create_time_based_chunks(
        self,
        data: Union[pd.DataFrame, pd.Series],
        n_workers: int
    ) -> List[Tuple[int, int]]:
        """Create chunks based on time periods"""
        if isinstance(data, pd.DataFrame):
            n_items = len(data)
            period_size = n_items // n_workers
            chunks = []
            for i in range(n_workers):
                start = i * period_size
                end = (i + 1) * period_size if i < n_workers - 1 else n_items
                chunks.append((start, end))
            return chunks
        else:
            return self._create_equal_chunks(len(data), n_workers)

    def _create_memory_based_chunks(
        self,
        data: Union[pd.DataFrame, np.ndarray],
        n_workers: int
    ) -> List[Tuple[int, int]]:
        """Create chunks based on memory usage"""
        # Estimate memory usage
        if isinstance(data, pd.DataFrame):
            memory_per_row = data.memory_usage(deep=True).sum()
        else:
            memory_per_row = data[0].nbytes if len(data) > 0 else 1000

        # Target memory per chunk (500MB default)
        target_memory = 500 * 1024 * 1024
        chunk_size = max(1, target_memory // memory_per_row)

        return self._create_equal_chunks(len(data), min(n_workers, len(data) // chunk_size))

    def _create_adaptive_chunks(
        self,
        data: Union[pd.DataFrame, np.ndarray],
        n_workers: int
    ) -> List[Tuple[int, int]]:
        """Create adaptive chunks based on data characteristics"""
        # Analyze data complexity
        if isinstance(data, pd.DataFrame):
            # Simple heuristic: chunk based on number of columns
            complexity = len(data.columns)
        else:
            complexity = 1

        # Adjust chunk size based on complexity
        base_chunk_size = len(data) // n_workers
        adjusted_size = max(1, int(base_chunk_size / np.sqrt(complexity)))

        self.chunk_size = adjusted_size
        return self._create_equal_chunks(len(data), n_workers)


class ResourceManager:
    """Manages system resources for parallel processing"""

    def __init__(self, config: ParallelConfig):
        self.config = config
        self.n_cpus = mp.cpu_count()
        self.memory_total = psutil.virtual_memory().total / (1024**3)  # GB

        # Auto-detect optimal number of workers
        if config.n_workers == -1:
            self.n_workers = min(self.n_cpus, int(self.memory_total / config.max_memory_gb))
        else:
            self.n_workers = config.n_workers

        logger.info(f"Resource manager initialized: {self.n_workers} workers, "
                   f"{self.memory_total:.1f}GB total memory")

    def get_optimal_workers(self, task_complexity: str = "medium") -> int:
        """Get optimal number of workers for task complexity"""

        if task_complexity == "low":
            return self.n_workers
        elif task_complexity == "medium":
            return max(1, self.n_workers // 2)
        elif task_complexity == "high":
            return max(1, self.n_workers // 4)
        else:
            return 1

    def monitor_resources(self) -> Dict[str, float]:
        """Monitor current resource usage"""
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent

        return {
            "cpu_usage": cpu_percent,
            "memory_usage": memory_percent,
            "available_memory_gb": psutil.virtual_memory().available / (1024**3)
        }


class ParallelProcessor:
    """Main parallel processing engine"""

    def __init__(self, config: ParallelConfig):
        """
        Initialize parallel processor

        Args:
            config: Parallel processing configuration
        """
        self.config = config
        self.resource_manager = ResourceManager(config)
        self.chunk_manager = ChunkManager(
            config.chunking_strategy,
            config.chunk_size
        )

        # Results storage
        self.results: Dict[str, ProcessingResult] = {}
        self.cached_results: Dict[str, Any] = {}

        logger.info(f"Parallel processor initialized with {self.config.mode} mode")

    def process_parallel(
        self,
        func: Callable,
        data_chunks: List[Any],
        args: Tuple = (),
        kwargs: Dict = None,
        progress_callback: Optional[Callable] = None
    ) -> List[ProcessingResult]:
        """
        Process data chunks in parallel

        Args:
            func: Function to execute
            data_chunks: List of data chunks
            args: Additional arguments
            kwargs: Additional keyword arguments
            progress_callback: Progress callback function

        Returns:
            List of processing results
        """
        if kwargs is None:
            kwargs = {}

        start_time = time.time()

        if self.config.mode == ProcessingMode.MULTI_PROCESS:
            results = self._process_multiprocess(func, data_chunks, args, kwargs)
        elif self.config.mode == ProcessingMode.MULTI_THREAD:
            results = self._process_multithread(func, data_chunks, args, kwargs)
        elif self.config.mode == ProcessingMode.DISTRIBUTED:
            results = self._process_distributed(func, data_chunks, args, kwargs)
        else:
            raise ValueError(f"Unsupported processing mode: {self.config.mode}")

        # Call progress callback
        if progress_callback:
            progress_callback(len(results), len(data_chunks))

        total_time = time.time() - start_time
        logger.info(f"Processed {len(data_chunks)} chunks in {total_time:.2f}s")

        return results

    def _process_multiprocess(
        self,
        func: Callable,
        data_chunks: List[Any],
        args: Tuple,
        kwargs: Dict
    ) -> List[ProcessingResult]:
        """Process using multiprocessing"""

        n_workers = self.resource_manager.n_workers
        results = []

        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            # Submit all tasks
            futures = []
            for i, chunk in enumerate(data_chunks):
                future = executor.submit(self._execute_task, func, chunk, *args, **kwargs)
                futures.append((future, i))

            # Collect results
            for future, chunk_id in futures:
                try:
                    result = future.result(timeout=self.config.timeout_seconds)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Task {chunk_id} failed: {e}")
                    results.append(ProcessingResult(
                        task_id=str(chunk_id),
                        result=None,
                        execution_time=0,
                        memory_usage=0,
                        worker_id=-1,
                        error=str(e)
                    ))

        return results

    def _process_multithread(
        self,
        func: Callable,
        data_chunks: List[Any],
        args: Tuple,
        kwargs: Dict
    ) -> List[ProcessingResult]:
        """Process using multithreading"""

        n_workers = self.resource_manager.n_workers
        results = []

        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            futures = []
            for i, chunk in enumerate(data_chunks):
                future = executor.submit(self._execute_task, func, chunk, *args, **kwargs)
                futures.append((future, i))

            for future, chunk_id in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Task {chunk_id} failed: {e}")
                    results.append(ProcessingResult(
                        task_id=str(chunk_id),
                        result=None,
                        execution_time=0,
                        memory_usage=0,
                        worker_id=-1,
                        error=str(e)
                    ))

        return results

    def _process_distributed(
        self,
        func: Callable,
        data_chunks: List[Any],
        args: Tuple,
        kwargs: Dict
    ) -> List[ProcessingResult]:
        """Process using distributed computing (placeholder)"""
        # This would integrate with Dask, Ray, or other distributed frameworks
        # For now, fall back to multiprocessing
        return self._process_multiprocess(func, data_chunks, args, kwargs)

    @staticmethod
    def _execute_task(
        func: Callable,
        data_chunk: Any,
        *args,
        **kwargs
    ) -> ProcessingResult:
        """Execute a single task"""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / (1024**2)  # MB

        try:
            # Execute function
            result = func(data_chunk, *args, **kwargs)

            execution_time = time.time() - start_time
            memory_usage = psutil.Process().memory_info().rss / (1024**2) - start_memory

            return ProcessingResult(
                task_id=str(hash(str(data_chunk)))[0:8],
                result=result,
                execution_time=execution_time,
                memory_usage=memory_usage,
                worker_id=os.getpid()
            )

        except Exception as e:
            return ProcessingResult(
                task_id=str(hash(str(data_chunk)))[0:8],
                result=None,
                execution_time=time.time() - start_time,
                memory_usage=0,
                worker_id=os.getpid(),
                error=str(e)
            )

    def _create_data_chunks(
        self,
        data: Union[pd.DataFrame, np.ndarray, List]
    ) -> List[Any]:
        """Create data chunks for parallel processing"""
        chunk_indices = self.chunk_manager.create_chunks(
            data,
            self.resource_manager.n_workers
        )

        chunks = []
        for start, end in chunk_indices:
            if isinstance(data, (pd.DataFrame, pd.Series)):
                chunks.append(data.iloc[start:end])
            else:
                chunks.append(data[start:end])

        return chunks

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.results:
            return {}

        execution_times = [r.execution_time for r in self.results.values()]
        memory_usage = [r.memory_usage for r in self.results.values()]

        return {
            'total_tasks': len(self.results),
            'avg_execution_time': np.mean(execution_times),
            'max_execution_time': np.max(execution_times),
            'min_execution_time': np.min(execution_times),
            'total_execution_time': np.sum(execution_times),
            'avg_memory_usage_mb': np.mean(memory_usage),
            'max_memory_usage_mb': np.max(memory_usage),
            'successful_tasks': sum(1 for r in self.results.values() if r.error is None),
            'failed_tasks': sum(1 for r in self.results.values() if r.error is not None)
        }


# Utility functions
def create_parallel_config(
    mode: ProcessingMode = ProcessingMode.MULTI_PROCESS,
    n_workers: int = -1,
    **kwargs
) -> ParallelConfig:
    """Create parallel processing configuration"""
    config = {
        'mode': mode,
        'n_workers': n_workers,
        'max_memory_gb': 4.0,
        'enable_caching': True,
        'chunking_strategy': ChunkingStrategy.MEMORY_BASED
    }

    config.update(kwargs)
    return ParallelConfig(**config)


def parallel_backtest_wrapper(
    backtest_func: Callable,
    data_chunk: pd.DataFrame,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """
    Wrapper for parallel backtesting

    Args:
        backtest_func: Backtest function
        data_chunk: Chunk of data
        *args, **kwargs: Additional arguments

    Returns:
        Backtest results for the chunk
    """
    # Run backtest on chunk
    result = backtest_func(data_chunk, *args, **kwargs)

    # Return serializable result
    if hasattr(result, '__dict__'):
        return result.__dict__
    else:
        return result


__all__ = [
    'ParallelProcessor',
    'ParallelConfig',
    'ProcessingTask',
    'ProcessingResult',
    'ChunkManager',
    'ResourceManager',
    'ProcessingMode',
    'TaskPriority',
    'ChunkingStrategy',
    'create_parallel_config',
    'parallel_backtest_wrapper'
]
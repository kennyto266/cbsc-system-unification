#!/usr/bin/env python3
"""
Result Aggregator for Multi-Process Parallel Processing
Efficient collection, merging, and analysis of distributed computation results
"""

import os
import sys
import time
import json
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import numpy as np
import pandas as pd
from concurrent.futures import Future
import pickle
import hashlib

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .interprocess_communication import InterProcessCommunication, MessageType
from .parallel_backtesting_engine import BacktestResult

logger = logging.getLogger(__name__)


class ResultStatus(Enum):
    """Status of result aggregation"""
    PENDING = "pending"
    COLLECTING = "collecting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class PartialResult:
    """Represents a partial result from a single process"""
    result_id: str
    worker_id: int
    task_id: str
    chunk_id: Optional[str]
    data: Any
    metadata: Dict[str, Any]
    timestamp: datetime
    processing_time: float
    memory_usage_mb: float
    status: str = "success"
    error_message: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)


@dataclass
class AggregationJob:
    """Represents an aggregation job"""
    job_id: str
    expected_results: int
    received_results: int = 0
    partial_results: List[PartialResult] = field(default_factory=list)
    aggregation_function: Optional[str] = None
    aggregation_params: Dict[str, Any] = field(default_factory=dict)
    status: ResultStatus = ResultStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_seconds: float = 300.0
    merged_result: Optional[Any] = None
    error_message: Optional[str] = None

    @property
    def completion_rate(self) -> float:
        """Calculate completion rate"""
        if self.expected_results == 0:
            return 0.0
        return self.received_results / self.expected_results

    @property
    def is_timeout(self) -> bool:
        """Check if job has timed out"""
        if self.started_at is None:
            return False
        return (datetime.now() - self.started_at).total_seconds() > self.timeout_seconds


@dataclass
class AggregationConfig:
    """Configuration for result aggregation"""
    max_concurrent_jobs: int = 100
    default_timeout_seconds: float = 300.0
    enable_compression: bool = True
    enable_deduplication: bool = True
    enable_validation: bool = True
    enable_caching: bool = True
    cache_size_mb: float = 512.0
    max_partial_results_per_job: int = 10000
    enable_streaming: bool = True
    streaming_batch_size: int = 100


class ResultAggregator:
    """
    Advanced result aggregation system for multi-process parallel processing

    Features:
    - Efficient collection and merging of distributed results
    - Multiple aggregation strategies and algorithms
    - Real-time progress tracking and monitoring
    - Fault tolerance and error recovery
    - Memory-efficient streaming for large datasets
    - Result validation and deduplication
    - Configurable aggregation functions
    - Performance optimization and caching
    - Timeout management and recovery
    """

    def __init__(
        self,
        config: AggregationConfig = None,
        ipc_system: Optional[InterProcessCommunication] = None
    ):
        self.config = config or AggregationConfig()
        self.ipc_system = ipc_system

        # Aggregation state
        self.active_jobs: Dict[str, AggregationJob] = {}
        self.completed_jobs: Dict[str, AggregationJob] = {}
        self.result_cache: Dict[str, Any] = {}

        # Aggregation functions
        self.aggregation_functions = {
            'sum': self._aggregate_sum,
            'mean': self._aggregate_mean,
            'concatenate': self._aggregate_concatenate,
            'merge_dataframe': self._aggregate_dataframe,
            'merge_backtest_results': self._aggregate_backtest_results,
            'weighted_average': self._aggregate_weighted_average,
            'custom': self._aggregate_custom
        }

        # Processing state
        self.is_running = False
        self.processing_thread: Optional[threading.Thread] = None
        self.cleanup_thread: Optional[threading.Thread] = None

        # Statistics
        self.stats = {
            'total_jobs_created': 0,
            'total_jobs_completed': 0,
            'total_jobs_failed': 0,
            'total_results_processed': 0,
            'total_data_processed_gb': 0.0,
            'average_aggregation_time': 0.0,
            'peak_memory_usage_mb': 0.0,
            'cache_hit_rate': 0.0,
            'compression_ratio': 1.0,
            'deduplication_rate': 0.0
        }

        logger.info("ResultAggregator initialized")

    def start(self):
        """Start the result aggregator"""
        if self.is_running:
            logger.warning("ResultAggregator is already running")
            return

        self.is_running = True

        # Start processing thread
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()

        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

        logger.info("ResultAggregator started")

    def stop(self):
        """Stop the result aggregator"""
        if not self.is_running:
            return

        logger.info("Stopping ResultAggregator...")
        self.is_running = False

        # Wait for threads to finish
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5.0)

        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5.0)

        # Finalize all active jobs
        for job_id, job in list(self.active_jobs.items()):
            self._finalize_job(job_id, force=True)

        logger.info("ResultAggregator stopped")

    def create_aggregation_job(
        self,
        job_id: str,
        expected_results: int,
        aggregation_function: str = 'concatenate',
        aggregation_params: Dict[str, Any] = None,
        timeout_seconds: Optional[float] = None
    ) -> bool:
        """
        Create a new aggregation job

        Args:
            job_id: Unique job identifier
            expected_results: Number of expected results
            aggregation_function: Function to use for aggregation
            aggregation_params: Parameters for aggregation function
            timeout_seconds: Job timeout in seconds

        Returns:
            True if job created successfully
        """
        if job_id in self.active_jobs or job_id in self.completed_jobs:
            logger.warning(f"Aggregation job {job_id} already exists")
            return False

        if aggregation_function not in self.aggregation_functions:
            logger.error(f"Unknown aggregation function: {aggregation_function}")
            return False

        job = AggregationJob(
            job_id=job_id,
            expected_results=expected_results,
            aggregation_function=aggregation_function,
            aggregation_params=aggregation_params or {},
            timeout_seconds=timeout_seconds or self.config.default_timeout_seconds
        )

        self.active_jobs[job_id] = job
        self.stats['total_jobs_created'] += 1

        logger.debug(f"Created aggregation job {job_id} expecting {expected_results} results")
        return True

    def submit_partial_result(
        self,
        job_id: str,
        worker_id: int,
        task_id: str,
        data: Any,
        chunk_id: Optional[str] = None,
        metadata: Dict[str, Any] = None,
        processing_time: float = 0.0,
        memory_usage_mb: float = 0.0
    ) -> bool:
        """
        Submit a partial result to an aggregation job

        Args:
            job_id: Target aggregation job ID
            worker_id: Worker process ID
            task_id: Original task ID
            data: Result data
            chunk_id: Optional chunk identifier
            metadata: Additional metadata
            processing_time: Time taken to generate result
            memory_usage_mb: Memory usage during processing

        Returns:
            True if result submitted successfully
        """
        job = self.active_jobs.get(job_id)
        if not job:
            logger.warning(f"Aggregation job {job_id} not found")
            return False

        if job.status != ResultStatus.PENDING and job.status != ResultStatus.COLLECTING:
            logger.warning(f"Job {job_id} is not accepting results (status: {job.status.value})")
            return False

        # Validate result
        if self.config.enable_validation:
            if not self._validate_partial_result(data, metadata):
                logger.error(f"Validation failed for result in job {job_id}")
                return False

        # Apply deduplication
        if self.config.enable_deduplication:
            data_hash = self._calculate_data_hash(data)
            if self._is_duplicate_result(job_id, data_hash):
                logger.debug(f"Duplicate result detected for job {job_id}")
                return True  # Not an error, just skip

        # Compress data if enabled
        compressed_data = data
        if self.config.enable_compression and self._should_compress(data):
            compressed_data = self._compress_data(data)

        # Create partial result
        partial_result = PartialResult(
            result_id=f"{job_id}_{worker_id}_{task_id}_{int(time.time())}",
            worker_id=worker_id,
            task_id=task_id,
            chunk_id=chunk_id,
            data=compressed_data,
            metadata=metadata or {},
            timestamp=datetime.now(),
            processing_time=processing_time,
            memory_usage_mb=memory_usage_mb
        )

        job.partial_results.append(partial_result)
        job.received_results += 1

        # Update job status
        if job.status == ResultStatus.PENDING:
            job.status = ResultStatus.COLLECTING
            job.started_at = datetime.now()

        # Check if job is complete
        if job.received_results >= job.expected_results:
            job.status = ResultStatus.PROCESSING
            logger.info(f"Aggregation job {job_id} ready for processing")

        # Update statistics
        self.stats['total_results_processed'] += 1
        if isinstance(data, (pd.DataFrame, np.ndarray)):
            data_size = len(data) if hasattr(data, '__len__') else 1
            self.stats['total_data_processed_gb'] += data_size * 8 / (1024**3)  # Rough estimate

        return True

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an aggregation job"""
        job = self.active_jobs.get(job_id) or self.completed_jobs.get(job_id)
        if not job:
            return None

        return {
            'job_id': job.job_id,
            'status': job.status.value,
            'expected_results': job.expected_results,
            'received_results': job.received_results,
            'completion_rate': job.completion_rate,
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'is_timeout': job.is_timeout,
            'aggregation_function': job.aggregation_function,
            'error_message': job.error_message
        }

    def get_job_result(self, job_id: str, timeout: Optional[float] = None) -> Any:
        """
        Get the final aggregated result for a job

        Args:
            job_id: Job identifier
            timeout: Maximum time to wait

        Returns:
            Aggregated result or None if not ready
        """
        start_time = time.time()

        while True:
            job = self.completed_jobs.get(job_id)
            if job and job.status == ResultStatus.COMPLETED:
                return job.merged_result

            job = self.active_jobs.get(job_id)
            if not job:
                return None

            if job.status == ResultStatus.FAILED:
                logger.error(f"Job {job_id} failed: {job.error_message}")
                return None

            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                logger.warning(f"Timeout waiting for job {job_id} result")
                return None

            time.sleep(0.1)

    def wait_for_completion(self, job_ids: List[str], timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Wait for completion of multiple jobs

        Args:
            job_ids: List of job IDs to wait for
            timeout: Maximum time to wait

        Returns:
            Dictionary mapping job IDs to results
        """
        start_time = time.time()
        results = {}

        while len(results) < len(job_ids):
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                break

            for job_id in job_ids:
                if job_id in results:
                    continue

                result = self.get_job_result(job_id, timeout=0.1)
                if result is not None:
                    results[job_id] = result

            time.sleep(0.1)

        return results

    def _processing_loop(self):
        """Main processing loop for aggregation jobs"""
        while self.is_running:
            try:
                # Find jobs ready for processing
                ready_jobs = [
                    job for job in self.active_jobs.values()
                    if job.status == ResultStatus.PROCESSING or job.is_timeout
                ]

                # Process ready jobs
                for job in ready_jobs:
                    threading.Thread(
                        target=self._process_aggregation_job,
                        args=(job.job_id,),
                        daemon=True
                    ).start()

                time.sleep(0.1)  # Small delay to prevent busy waiting

            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(1.0)

    def _cleanup_loop(self):
        """Periodic cleanup of old jobs and cache"""
        while self.is_running:
            try:
                self._cleanup_old_jobs()
                self._cleanup_cache()
                time.sleep(60)  # Cleanup every minute
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                time.sleep(60)

    def _process_aggregation_job(self, job_id: str):
        """Process a single aggregation job"""
        job = self.active_jobs.get(job_id)
        if not job:
            return

        start_time = time.time()
        logger.info(f"Processing aggregation job {job_id}")

        try:
            # Check for timeout
            if job.is_timeout:
                job.status = ResultStatus.TIMEOUT
                job.error_message = f"Job timed out after {job.timeout_seconds} seconds"
                self._finalize_job(job_id)
                return

            # Decompress data if needed
            decompressed_results = []
            for partial_result in job.partial_results:
                if self.config.enable_compression and self._is_compressed(partial_result.data):
                    partial_result.data = self._decompress_data(partial_result.data)

                # Decompress nested data in metadata
                if 'compressed_data' in partial_result.metadata:
                    partial_result.metadata['data'] = self._decompress_data(partial_result.metadata['compressed_data'])

                decompressed_results.append(partial_result)

            # Get aggregation function
            agg_function = self.aggregation_functions.get(job.aggregation_function)
            if not agg_function:
                raise ValueError(f"Unknown aggregation function: {job.aggregation_function}")

            # Perform aggregation
            merged_result = agg_function(decompressed_results, job.aggregation_params)

            # Validate final result
            if self.config.enable_validation:
                if not self._validate_aggregated_result(merged_result, job):
                    raise ValueError("Aggregated result validation failed")

            # Update job with result
            job.merged_result = merged_result
            job.status = ResultStatus.COMPLETED
            job.completed_at = datetime.now()

            # Update statistics
            processing_time = time.time() - start_time
            self.stats['total_jobs_completed'] += 1
            self._update_aggregation_stats(processing_time, len(decompressed_results))

            # Move job to completed
            self._finalize_job(job_id)

            logger.info(f"Successfully completed aggregation job {job_id} in {processing_time:.2f}s")

        except Exception as e:
            job.status = ResultStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()

            self.stats['total_jobs_failed'] += 1
            self._finalize_job(job_id)

            logger.error(f"Failed to process aggregation job {job_id}: {e}")

    def _finalize_job(self, job_id: str, force: bool = False):
        """Finalize an aggregation job"""
        job = self.active_jobs.get(job_id)
        if not job:
            return

        # Cache result if caching is enabled and job completed successfully
        if (self.config.enable_caching and job.status == ResultStatus.COMPLETED
            and job.merged_result is not None):

            # Check cache size limit
            cache_size = sum(self._get_result_size(r) for r in self.result_cache.values()) / (1024 * 1024)
            if cache_size < self.config.cache_size_mb:
                self.result_cache[job_id] = job.merged_result
            else:
                # Remove oldest entry
                oldest_key = next(iter(self.result_cache))
                del self.result_cache[oldest_key]
                self.result_cache[job_id] = job.merged_result

        # Move job from active to completed
        self.completed_jobs[job_id] = job
        del self.active_jobs[job_id]

        # Limit completed jobs size
        if len(self.completed_jobs) > self.config.max_concurrent_jobs:
            oldest_key = min(self.completed_jobs.keys(),
                           key=lambda k: self.completed_jobs[k].completed_at or datetime.min)
            del self.completed_jobs[oldest_key]

    def _aggregate_sum(self, results: List[PartialResult], params: Dict[str, Any]) -> Union[int, float]:
        """Aggregate results by summing"""
        total = 0
        for result in results:
            if isinstance(result.data, (int, float)):
                total += result.data
            elif hasattr(result.data, '__iter__'):
                total += sum(result.data)
        return total

    def _aggregate_mean(self, results: List[PartialResult], params: Dict[str, Any]) -> float:
        """Aggregate results by calculating mean"""
        if not results:
            return 0.0

        total = self._aggregate_sum(results, params)
        count = len(results)
        return total / count if count > 0 else 0.0

    def _aggregate_concatenate(self, results: List[PartialResult], params: Dict[str, Any]) -> List[Any]:
        """Aggregate results by concatenating"""
        concatenated = []
        for result in results:
            if isinstance(result.data, (list, tuple)):
                concatenated.extend(result.data)
            else:
                concatenated.append(result.data)
        return concatenated

    def _aggregate_dataframe(self, results: List[PartialResult], params: Dict[str, Any]) -> pd.DataFrame:
        """Aggregate DataFrame results"""
        dataframes = []
        for result in results:
            if isinstance(result.data, pd.DataFrame):
                # Decompress if needed
                if self._is_compressed(result.data):
                    df = self._decompress_data(result.data)
                else:
                    df = result.data
                dataframes.append(df)

        if not dataframes:
            return pd.DataFrame()

        # Determine concatenation method
        axis = params.get('axis', 0)
        ignore_index = params.get('ignore_index', True)
        sort = params.get('sort', False)

        return pd.concat(dataframes, axis=axis, ignore_index=ignore_index, sort=sort)

    def _aggregate_backtest_results(self, results: List[PartialResult], params: Dict[str, Any]) -> BacktestResult:
        """Aggregate backtest results"""
        if not results:
            return None

        # Extract backtest results
        backtest_results = []
        for result in results:
            if isinstance(result.data, BacktestResult):
                backtest_results.append(result.data)
            elif isinstance(result.data, dict) and 'total_return' in result.data:
                # Convert dict to BacktestResult if needed
                backtest_results.append(BacktestResult(**result.data))

        if not backtest_results:
            return None

        if len(backtest_results) == 1:
            return backtest_results[0]

        # Combine results
        combined_equity = pd.concat([r.equity_curve for r in backtest_results], ignore_index=False)
        combined_drawdown = pd.concat([r.drawdown_curve for r in backtest_results], ignore_index=False)
        all_trades = pd.concat([r.trades for r in backtest_results], ignore_index=True)

        # Calculate combined metrics
        total_return = (combined_equity.iloc[-1] / combined_equity.iloc[0]) - 1
        returns = combined_equity.pct_change().dropna()
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if len(returns) > 1 else 0
        max_drawdown = combined_drawdown.min()

        # Calculate other metrics
        total_trades_count = len(all_trades)
        winning_trades = len(all_trades[all_trades.get('pnl', pd.Series()) > 0]) if 'pnl' in all_trades.columns else total_trades_count // 2
        win_rate = winning_trades / max(1, total_trades_count)

        return BacktestResult(
            chunk_id="aggregated",
            symbols=list(set(sum([r.symbols for r in backtest_results], []))),
            start_date=min(r.start_date for r in backtest_results),
            end_date=max(r.end_date for r in backtest_results),
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=1.0,  # Would need proper calculation
            total_trades=total_trades_count,
            final_portfolio_value=combined_equity.iloc[-1],
            equity_curve=combined_equity,
            drawdown_curve=combined_drawdown,
            trades=all_trades,
            positions=pd.DataFrame(),  # Would need proper aggregation
            execution_time=sum(r.execution_time for r in backtest_results),
            memory_usage_mb=sum(r.memory_usage_mb for r in backtest_results),
            warnings=list(set(sum([r.warnings for r in backtest_results], [])))
        )

    def _aggregate_weighted_average(self, results: List[PartialResult], params: Dict[str, Any]) -> float:
        """Aggregate results using weighted average"""
        weights = params.get('weights', None)
        if weights is None:
            # Use equal weights
            weights = [1.0] * len(results)

        if len(weights) != len(results):
            raise ValueError("Number of weights must match number of results")

        weighted_sum = 0.0
        total_weight = 0.0

        for result, weight in zip(results, weights):
            if isinstance(result.data, (int, float)):
                weighted_sum += result.data * weight
                total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _aggregate_custom(self, results: List[PartialResult], params: Dict[str, Any]) -> Any:
        """Custom aggregation using user-provided function"""
        custom_function = params.get('function')
        if not custom_function:
            raise ValueError("Custom aggregation requires 'function' parameter")

        return custom_function(results, params)

    def _validate_partial_result(self, data: Any, metadata: Dict[str, Any]) -> bool:
        """Validate a partial result"""
        # Basic validation - can be extended
        return data is not None

    def _validate_aggregated_result(self, result: Any, job: AggregationJob) -> bool:
        """Validate an aggregated result"""
        # Basic validation - can be extended
        return result is not None

    def _calculate_data_hash(self, data: Any) -> str:
        """Calculate hash of data for deduplication"""
        try:
            data_bytes = pickle.dumps(data)
            return hashlib.md5(data_bytes).hexdigest()
        except Exception:
            return str(hash(data))

    def _is_duplicate_result(self, job_id: str, data_hash: str) -> bool:
        """Check if result is a duplicate"""
        # This is a simplified implementation
        # In practice, you would maintain a hash set per job
        return False

    def _should_compress(self, data: Any) -> bool:
        """Determine if data should be compressed"""
        try:
            data_size = len(pickle.dumps(data))
            return data_size > 1024 * 1024  # Compress if > 1MB
        except Exception:
            return False

    def _compress_data(self, data: Any) -> Any:
        """Compress data"""
        try:
            import zlib
            serialized = pickle.dumps(data)
            compressed = zlib.compress(serialized)
            return {'compressed_data': compressed, 'original_size': len(serialized)}
        except Exception:
            return data

    def _decompress_data(self, compressed_data: Any) -> Any:
        """Decompress data"""
        try:
            if isinstance(compressed_data, dict) and 'compressed_data' in compressed_data:
                import zlib
                decompressed = zlib.decompress(compressed_data['compressed_data'])
                return pickle.loads(decompressed)
            return compressed_data
        except Exception:
            return compressed_data

    def _is_compressed(self, data: Any) -> bool:
        """Check if data is compressed"""
        return isinstance(data, dict) and 'compressed_data' in data

    def _get_result_size(self, result: Any) -> int:
        """Get size of result in bytes"""
        try:
            return len(pickle.dumps(result))
        except Exception:
            return 0

    def _cleanup_old_jobs(self):
        """Clean up old completed jobs"""
        cutoff_time = datetime.now() - timedelta(hours=1)  # Keep jobs for 1 hour

        jobs_to_remove = [
            job_id for job_id, job in self.completed_jobs.items()
            if job.completed_at and job.completed_at < cutoff_time
        ]

        for job_id in jobs_to_remove:
            del self.completed_jobs[job_id]
            logger.debug(f"Cleaned up old job {job_id}")

    def _cleanup_cache(self):
        """Clean up result cache"""
        if len(self.result_cache) > self.config.max_concurrent_jobs:
            # Remove oldest entries
            items = list(self.result_cache.items())
            items.sort(key=lambda x: 0)  # Keep insertion order
            keep_count = self.config.max_concurrent_jobs // 2

            self.result_cache = dict(items[-keep_count:])

    def _update_aggregation_stats(self, processing_time: float, result_count: int):
        """Update aggregation statistics"""
        # Update average processing time
        total_jobs = self.stats['total_jobs_completed'] + self.stats['total_jobs_failed']
        if total_jobs > 0:
            current_avg = self.stats['average_aggregation_time']
            new_avg = ((current_avg * (total_jobs - 1)) + processing_time) / total_jobs
            self.stats['average_aggregation_time'] = new_avg

    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregator statistics"""
        return {
            'aggregator_stats': self.stats.copy(),
            'active_jobs': len(self.active_jobs),
            'completed_jobs': len(self.completed_jobs),
            'cache_size': len(self.result_cache),
            'is_running': self.is_running,
            'supported_functions': list(self.aggregation_functions.keys())
        }

    def register_aggregation_function(self, name: str, function: Callable):
        """Register a custom aggregation function"""
        self.aggregation_functions[name] = function
        logger.info(f"Registered custom aggregation function: {name}")
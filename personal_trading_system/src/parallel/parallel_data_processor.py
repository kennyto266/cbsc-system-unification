#!/usr/bin/env python3
"""
Parallel Data Processor for Large Dataset Handling
Efficient data chunking, distribution, and processing across 32 cores
"""

import os
import sys
import time
import logging
import pickle
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Iterator
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
import psutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .multi_process_scheduler import MultiProcessScheduler, TaskPriority, chunk_data, estimate_task_memory

logger = logging.getLogger(__name__)


@dataclass
class DataChunk:
    """Represents a chunk of data for parallel processing"""
    chunk_id: str
    data: Any
    chunk_index: int
    total_chunks: int
    start_index: int
    end_index: int
    size_bytes: int
    checksum: str
    metadata: Dict[str, Any]


@dataclass
class ProcessingJob:
    """Represents a data processing job"""
    job_id: str
    data: Any
    processing_function: str
    chunk_size: int
    overlap_size: int = 0
    priority: TaskPriority = TaskPriority.NORMAL
    metadata: Dict[str, Any] = None


class ParallelDataProcessor:
    """
    High-performance parallel data processor for large datasets

    Features:
    - Intelligent data chunking with overlap support
    - Memory-efficient streaming for large datasets
    - Automatic data validation and integrity checking
    - Parallel processing across 32 cores
    - Progress tracking and result aggregation
    - Fault tolerance and recovery
    """

    def __init__(
        self,
        scheduler: MultiProcessScheduler,
        max_chunk_size_mb: int = 100,
        temp_dir: Optional[str] = None,
        enable_compression: bool = True
    ):
        self.scheduler = scheduler
        self.max_chunk_size_mb = max_chunk_size_mb
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "parallel_processor"
        self.enable_compression = enable_compression

        # Create temp directory
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Processing state
        self.active_jobs: Dict[str, ProcessingJob] = {}
        self.data_chunks: Dict[str, List[DataChunk]] = {}
        self.processing_results: Dict[str, List[Any]] = {}

        # Statistics
        self.stats = {
            'total_jobs_processed': 0,
            'total_chunks_processed': 0,
            'total_data_processed_gb': 0.0,
            'average_chunk_processing_time': 0.0,
            'data_integrity_errors': 0,
            'processing_throughput_gb_per_hour': 0.0
        }

        logger.info(f"ParallelDataProcessor initialized with max chunk size {max_chunk_size_mb}MB")

    def create_processing_job(
        self,
        data: Any,
        processing_function: str,
        chunk_size: Optional[int] = None,
        overlap_size: int = 0,
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Create a data processing job

        Args:
            data: Data to process (DataFrame, array, list)
            processing_function: Name of processing function to execute
            chunk_size: Size of each chunk (auto-calculated if None)
            overlap_size: Overlap between chunks for windowed operations
            priority: Task priority
            metadata: Additional job metadata

        Returns:
            Job ID
        """
        job_id = f"job_{int(time.time())}_{hash(str(data)) % 10000:04d}"

        # Calculate optimal chunk size if not provided
        if chunk_size is None:
            chunk_size = self._calculate_optimal_chunk_size(data)

        # Create processing job
        job = ProcessingJob(
            job_id=job_id,
            data=data,
            processing_function=processing_function,
            chunk_size=chunk_size,
            overlap_size=overlap_size,
            priority=priority,
            metadata=metadata or {}
        )

        self.active_jobs[job_id] = job
        logger.info(f"Created processing job {job_id} with chunk size {chunk_size}")

        return job_id

    def process_data_parallel(
        self,
        data: Any,
        processing_function: str,
        processing_args: tuple = (),
        processing_kwargs: dict = None,
        chunk_size: Optional[int] = None,
        overlap_size: int = 0,
        priority: TaskPriority = TaskPriority.NORMAL,
        merge_results: bool = True
    ) -> Union[List[Any], Any]:
        """
        Process data in parallel across multiple cores

        Args:
            data: Data to process
            processing_function: Name of processing function
            processing_args: Arguments for processing function
            processing_kwargs: Keyword arguments for processing function
            chunk_size: Size of each chunk
            overlap_size: Overlap between chunks
            priority: Task priority
            merge_results: Whether to merge results into single object

        Returns:
            Processing results (list or merged object)
        """
        start_time = time.time()

        # Create processing job
        job_id = self.create_processing_job(
            data=data,
            processing_function=processing_function,
            chunk_size=chunk_size,
            overlap_size=overlap_size,
            priority=priority
        )

        # Split data into chunks
        chunks = self._create_data_chunks(job_id)
        if not chunks:
            logger.error(f"Failed to create chunks for job {job_id}")
            return []

        logger.info(f"Processing {len(chunks)} chunks for job {job_id}")

        # Submit processing tasks
        task_ids = []
        for chunk in chunks:
            task_kwargs = {
                'data_chunk': chunk.data,
                'chunk_metadata': {
                    'chunk_id': chunk.chunk_id,
                    'chunk_index': chunk.chunk_index,
                    'total_chunks': chunk.total_chunks
                }
            }
            task_kwargs.update(processing_kwargs or {})

            task_id = self.scheduler.submit_task(
                function=self._get_processing_function(processing_function),
                args=processing_args,
                kwargs=task_kwargs,
                priority=priority,
                estimated_memory_mb=estimate_task_memory(chunk.data),
                estimated_cpu_time=self._estimate_chunk_processing_time(chunk.data, processing_function)
            )
            task_ids.append(task_id)

        # Wait for completion
        results = self.scheduler.wait_for_completion(task_ids, timeout=3600)  # 1 hour timeout

        # Collect results in order
        ordered_results = []
        for chunk in chunks:
            task_result = results.get(task_ids[chunk.chunk_index])
            if task_result is not None:
                ordered_results.append(task_result)

        # Update statistics
        processing_time = time.time() - start_time
        self._update_job_statistics(job_id, processing_time, len(chunks))

        # Merge results if requested
        if merge_results and ordered_results:
            merged_result = self._merge_results(ordered_results, processing_function)
            return merged_result

        return ordered_results

    def process_large_dataframe(
        self,
        df: pd.DataFrame,
        processing_function: str,
        date_column: str = None,
        chunk_by_time: bool = True,
        time_window_days: int = 30,
        **kwargs
    ) -> Any:
        """
        Process large DataFrame with time-based chunking

        Args:
            df: DataFrame to process
            processing_function: Processing function name
            date_column: Name of date column for time-based chunking
            chunk_by_time: Whether to chunk by time periods
            time_window_days: Size of time windows in days
            **kwargs: Additional arguments for process_data_parallel

        Returns:
            Processing results
        """
        if chunk_by_time and date_column and date_column in df.columns:
            # Time-based chunking
            chunks = self._create_time_based_chunks(df, date_column, time_window_days)
            logger.info(f"Created {len(chunks)} time-based chunks from {len(df)} rows")
        else:
            # Row-based chunking
            kwargs['chunk_size'] = kwargs.get('chunk_size', self._calculate_optimal_chunk_size(df))
            chunks = self._create_data_chunks_from_dataframe(df, kwargs['chunk_size'])

        # Process chunks
        return self.process_data_parallel(
            data=chunks,
            processing_function=processing_function,
            **kwargs
        )

    def _calculate_optimal_chunk_size(self, data: Any) -> int:
        """Calculate optimal chunk size based on data characteristics and system resources"""
        # Get data size
        if isinstance(data, pd.DataFrame):
            data_size_mb = data.memory_usage(deep=True).sum() / (1024 * 1024)
            num_rows = len(data)
        elif isinstance(data, np.ndarray):
            data_size_mb = data.nbytes / (1024 * 1024)
            num_rows = len(data)
        elif isinstance(data, list):
            data_size_mb = len(str(data)) / (1024 * 1024)  # Rough estimate
            num_rows = len(data)
        else:
            data_size_mb = 1
            num_rows = 100

        # Calculate optimal number of chunks based on available cores and memory
        available_memory_gb = psutil.virtual_memory().available / (1024**3)
        optimal_chunks = min(
            self.scheduler.max_workers,
            max(1, int(available_memory_gb * 0.8 / self.max_chunk_size_mb * 1024)),
            num_rows // 1000  # Minimum 1000 rows per chunk
        )

        # Calculate chunk size
        if isinstance(data, pd.DataFrame):
            chunk_size = max(1, num_rows // optimal_chunks)
        else:
            chunk_size = max(1, len(data) // optimal_chunks)

        logger.debug(f"Calculated optimal chunk size: {chunk_size} (data size: {data_size_mb:.1f}MB, optimal chunks: {optimal_chunks})")
        return chunk_size

    def _create_data_chunks(self, job_id: str) -> List[DataChunk]:
        """Create data chunks for a job"""
        job = self.active_jobs[job_id]
        data = job.data
        chunk_size = job.chunk_size
        overlap_size = job.overlap_size

        chunks = []

        if isinstance(data, pd.DataFrame):
            chunks = self._create_dataframe_chunks(job_id, data, chunk_size, overlap_size)
        elif isinstance(data, (list, np.ndarray)):
            chunks = self._create_sequence_chunks(job_id, data, chunk_size, overlap_size)
        elif isinstance(data, dict):
            chunks = self._create_dict_chunks(job_id, data, chunk_size)
        else:
            raise ValueError(f"Unsupported data type for chunking: {type(data)}")

        self.data_chunks[job_id] = chunks
        return chunks

    def _create_dataframe_chunks(
        self,
        job_id: str,
        df: pd.DataFrame,
        chunk_size: int,
        overlap_size: int
    ) -> List[DataChunk]:
        """Create chunks from DataFrame"""
        chunks = []
        total_rows = len(df)
        effective_chunk_size = chunk_size - overlap_size

        for i in range(0, total_rows, effective_chunk_size):
            start_idx = max(0, i - overlap_size)
            end_idx = min(total_rows, i + chunk_size)

            chunk_data = df.iloc[start_idx:end_idx].copy()

            # Calculate checksum
            data_bytes = pickle.dumps(chunk_data)
            checksum = hashlib.md5(data_bytes).hexdigest()

            chunk = DataChunk(
                chunk_id=f"{job_id}_chunk_{i//effective_chunk_size:04d}",
                data=chunk_data,
                chunk_index=len(chunks),
                total_chunks=(total_rows + effective_chunk_size - 1) // effective_chunk_size,
                start_index=start_idx,
                end_index=end_idx,
                size_bytes=len(data_bytes),
                checksum=checksum,
                metadata={
                    'overlap_size': overlap_size,
                    'effective_chunk_size': effective_chunk_size
                }
            )
            chunks.append(chunk)

        return chunks

    def _create_sequence_chunks(
        self,
        job_id: str,
        sequence: Union[list, np.ndarray],
        chunk_size: int,
        overlap_size: int
    ) -> List[DataChunk]:
        """Create chunks from sequence (list or array)"""
        chunks = []
        total_length = len(sequence)
        effective_chunk_size = chunk_size - overlap_size

        for i in range(0, total_length, effective_chunk_size):
            start_idx = max(0, i - overlap_size)
            end_idx = min(total_length, i + chunk_size)

            chunk_data = sequence[start_idx:end_idx]

            # Calculate checksum
            data_bytes = pickle.dumps(chunk_data)
            checksum = hashlib.md5(data_bytes).hexdigest()

            chunk = DataChunk(
                chunk_id=f"{job_id}_chunk_{i//effective_chunk_size:04d}",
                data=chunk_data,
                chunk_index=len(chunks),
                total_chunks=(total_length + effective_chunk_size - 1) // effective_chunk_size,
                start_index=start_idx,
                end_index=end_idx,
                size_bytes=len(data_bytes),
                checksum=checksum,
                metadata={
                    'overlap_size': overlap_size,
                    'effective_chunk_size': effective_chunk_size
                }
            )
            chunks.append(chunk)

        return chunks

    def _create_dict_chunks(
        self,
        job_id: str,
        data_dict: dict,
        chunk_size: int
    ) -> List[DataChunk]:
        """Create chunks from dictionary (group key-value pairs)"""
        chunks = []
        items = list(data_dict.items())
        total_items = len(items)

        for i in range(0, total_items, chunk_size):
            chunk_items = items[i:i + chunk_size]
            chunk_data = dict(chunk_items)

            # Calculate checksum
            data_bytes = pickle.dumps(chunk_data)
            checksum = hashlib.md5(data_bytes).hexdigest()

            chunk = DataChunk(
                chunk_id=f"{job_id}_chunk_{i//chunk_size:04d}",
                data=chunk_data,
                chunk_index=len(chunks),
                total_chunks=(total_items + chunk_size - 1) // chunk_size,
                start_index=i,
                end_index=min(i + chunk_size, total_items),
                size_bytes=len(data_bytes),
                checksum=checksum,
                metadata={}
            )
            chunks.append(chunk)

        return chunks

    def _create_time_based_chunks(
        self,
        df: pd.DataFrame,
        date_column: str,
        time_window_days: int
    ) -> List[pd.DataFrame]:
        """Create time-based chunks from DataFrame"""
        # Ensure date column is datetime
        if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
            df[date_column] = pd.to_datetime(df[date_column])

        # Sort by date
        df_sorted = df.sort_values(date_column)

        # Create time windows
        min_date = df_sorted[date_column].min()
        max_date = df_sorted[date_column].max()

        chunks = []
        current_date = min_date

        while current_date <= max_date:
            end_date = current_date + pd.Timedelta(days=time_window_days)
            mask = (df_sorted[date_column] >= current_date) & (df_sorted[date_column] < end_date)
            chunk = df_sorted[mask].copy()

            if not chunk.empty:
                chunks.append(chunk)

            current_date = end_date

        return chunks

    def _get_processing_function(self, function_name: str) -> callable:
        """Get processing function by name"""
        # Import processing functions module
        try:
            from . import processing_functions
            return getattr(processing_functions, function_name)
        except (ImportError, AttributeError):
            # Try to get from global namespace
            try:
                return globals()[function_name]
            except KeyError:
                raise ValueError(f"Processing function '{function_name}' not found")

    def _estimate_chunk_processing_time(self, chunk_data: Any, function_name: str) -> float:
        """Estimate processing time for a chunk"""
        # Base estimates for different data types and operations
        base_time = 0.1  # Base time in seconds

        if isinstance(chunk_data, pd.DataFrame):
            rows = len(chunk_data)
            cols = len(chunk_data.columns)
            base_time += (rows * cols) / 100000  # 100k cells per second
        elif isinstance(chunk_data, (list, np.ndarray)):
            length = len(chunk_data)
            base_time += length / 1000000  # 1M items per second

        # Adjust based on function complexity
        if 'indicator' in function_name.lower():
            base_time *= 2  # Technical indicators are more expensive
        elif 'backtest' in function_name.lower():
            base_time *= 5  # Backtesting is most expensive

        return max(0.1, base_time)  # Minimum 0.1 seconds

    def _merge_results(self, results: List[Any], processing_function: str) -> Any:
        """Merge processing results into single object"""
        if not results:
            return None

        # Handle different result types
        if all(isinstance(r, pd.DataFrame) for r in results):
            # Concatenate DataFrames
            merged = pd.concat(results, ignore_index=False)
            return merged.sort_index()
        elif all(isinstance(r, np.ndarray) for r in results):
            # Concatenate arrays
            return np.concatenate(results)
        elif all(isinstance(r, (list, tuple)) for r in results):
            # Extend sequences
            if isinstance(results[0], tuple):
                return tuple(sum(list(r), []) for r in zip(*results))
            else:
                merged = []
                for r in results:
                    merged.extend(r)
                return merged
        elif all(isinstance(r, dict) for r in results):
            # Merge dictionaries
            merged = {}
            for r in results:
                merged.update(r)
            return merged
        else:
            # Return as list
            return results

    def _update_job_statistics(self, job_id: str, processing_time: float, num_chunks: int):
        """Update job processing statistics"""
        job = self.active_jobs.get(job_id)
        if not job:
            return

        # Update job stats
        self.stats['total_jobs_processed'] += 1
        self.stats['total_chunks_processed'] += num_chunks

        # Calculate data size
        data_size_gb = 0
        if isinstance(job.data, pd.DataFrame):
            data_size_gb = job.data.memory_usage(deep=True).sum() / (1024**3)
        elif isinstance(job.data, np.ndarray):
            data_size_gb = job.data.nbytes / (1024**3)

        self.stats['total_data_processed_gb'] += data_size_gb

        # Update average processing time
        total_jobs = self.stats['total_jobs_processed']
        current_avg = self.stats['average_chunk_processing_time']
        new_avg = ((current_avg * (total_jobs - 1)) + processing_time) / total_jobs
        self.stats['average_chunk_processing_time'] = new_avg

        # Calculate throughput
        if processing_time > 0:
            throughput_gb_per_hour = data_size_gb / (processing_time / 3600)
            self.stats['processing_throughput_gb_per_hour'] = throughput_gb_per_hour

        logger.info(f"Job {job_id} completed: {processing_time:.2f}s, {num_chunks} chunks, {data_size_gb:.2f}GB")

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a processing job"""
        job = self.active_jobs.get(job_id)
        if not job:
            return {'status': 'not_found'}

        chunks = self.data_chunks.get(job_id, [])
        results = self.processing_results.get(job_id, [])

        return {
            'status': 'active' if job else 'completed',
            'job_id': job_id,
            'total_chunks': len(chunks),
            'completed_chunks': len(results),
            'processing_function': job.processing_function if job else 'unknown',
            'chunk_size': job.chunk_size if job else 0,
            'progress': len(results) / len(chunks) if chunks else 0
        }

    def cleanup_job(self, job_id: str):
        """Clean up job data and temporary files"""
        # Remove from active jobs
        if job_id in self.active_jobs:
            del self.active_jobs[job_id]

        # Remove chunks
        if job_id in self.data_chunks:
            del self.data_chunks[job_id]

        # Remove results
        if job_id in self.processing_results:
            del self.processing_results[job_id]

        logger.info(f"Cleaned up job {job_id}")

    def cleanup_all_jobs(self):
        """Clean up all job data"""
        self.active_jobs.clear()
        self.data_chunks.clear()
        self.processing_results.clear()

        # Clean up temp directory
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Cleaned up all jobs")

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'processor_stats': self.stats.copy(),
            'active_jobs': len(self.active_jobs),
            'total_chunks_stored': sum(len(chunks) for chunks in self.data_chunks.values()),
            'temp_directory': str(self.temp_dir),
            'temp_directory_size_mb': sum(
                f.stat().st_size for f in self.temp_dir.rglob('*') if f.is_file()
            ) / (1024 * 1024)
        }


# Processing function registry and utilities
class ProcessingFunctions:
    """Registry of commonly used data processing functions"""

    @staticmethod
    def calculate_technical_indicators(data_chunk: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """Calculate technical indicators for a data chunk"""
        chunk_metadata = kwargs.get('chunk_metadata', {})
        logger.debug(f"Calculating indicators for chunk {chunk_metadata.get('chunk_index', 'unknown')}")

        # Import indicator calculation
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from src.analysis.long_term_indicators import LongTermIndicators

            indicators = LongTermIndicators()
            result = indicators.calculate_comprehensive_indicators(data_chunk)
            return result

        except ImportError:
            # Fallback simple calculations
            result = data_chunk.copy()
            if 'close' in result.columns:
                result['sma_20'] = result['close'].rolling(window=20, min_periods=1).mean()
                result['rsi_14'] = 100 - (100 / (1 + result['close'].diff().rolling(14).apply(
                    lambda x: x[x > 0].mean() / abs(x[x < 0].mean()) if len(x[x < 0]) > 0 else 1
                )))
            return result

    @staticmethod
    def backtest_strategy(data_chunk: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Backtest trading strategy on data chunk"""
        chunk_metadata = kwargs.get('chunk_metadata', {})
        logger.debug(f"Backtesting chunk {chunk_metadata.get('chunk_index', 'unknown')}")

        # Simple backtest logic
        if 'close' not in data_chunk.columns:
            return {'total_return': 0, 'sharpe_ratio': 0, 'max_drawdown': 0}

        returns = data_chunk['close'].pct_change().dropna()
        total_return = (1 + returns).prod() - 1
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        max_drawdown = (data_chunk['close'] / data_chunk['close'].cummax() - 1).min()

        return {
            'chunk_id': chunk_metadata.get('chunk_id'),
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'num_trades': len(returns),
            'chunk_size': len(data_chunk)
        }

    @staticmethod
    def process_hkma_data(data_chunk: Any, **kwargs) -> pd.DataFrame:
        """Process HKMA government data chunk"""
        chunk_metadata = kwargs.get('chunk_metadata', {})
        logger.debug(f"Processing HKMA chunk {chunk_metadata.get('chunk_index', 'unknown')}")

        # Convert to DataFrame if needed
        if not isinstance(data_chunk, pd.DataFrame):
            return pd.DataFrame()

        # Basic processing
        result = data_chunk.copy()

        # Add derived columns if applicable
        if 'rate' in result.columns:
            result['rate_change'] = result['rate'].diff()
            result['rate_ma_5'] = result['rate'].rolling(5, min_periods=1).mean()

        return result

    @staticmethod
    def validate_data_quality(data_chunk: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Validate data quality for a chunk"""
        chunk_metadata = kwargs.get('chunk_metadata', {})

        quality_report = {
            'chunk_id': chunk_metadata.get('chunk_id'),
            'total_rows': len(data_chunk),
            'null_counts': data_chunk.isnull().sum().to_dict(),
            'duplicate_rows': data_chunk.duplicated().sum(),
            'data_types': data_chunk.dtypes.astype(str).to_dict(),
            'quality_score': 0.0
        }

        # Calculate quality score
        total_cells = len(data_chunk) * len(data_chunk.columns)
        null_cells = data_chunk.isnull().sum().sum()
        quality_score = 1.0 - (null_cells / total_cells) if total_cells > 0 else 0.0
        quality_report['quality_score'] = quality_score

        return quality_report


# Register processing functions
processing_functions = ProcessingFunctions()
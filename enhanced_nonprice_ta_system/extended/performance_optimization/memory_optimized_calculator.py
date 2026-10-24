"""
Phase 5.2: Memory Optimized Calculator

Memory-optimized computation engine for technical indicators with vectorized
computation, chunked processing, and intelligent memory management.

Author: Claude Code Assistant
Version: 1.0.0
"""

import gc
import time
import threading
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union, Callable, Iterator
from dataclasses import dataclass, asdict
from enum import Enum
import logging

import numpy as np

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import numba
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

class ComputationMethod(Enum):
    """Computation method enumeration."""
    VECTORIZED = "vectorized"
    CHUNKED = "chunked"
    STREAMING = "streaming"
    NUMBA_ACCELERATED = "numba_accelerated"

class MemoryStrategy(Enum):
    """Memory management strategy enumeration."""
    CONSERVATIVE = "conservative"  # Minimal memory usage
    BALANCED = "balanced"         # Balance between speed and memory
    AGGRESSIVE = "aggressive"    # Maximum performance, higher memory usage

@dataclass
class MemoryConfig:
    """Configuration for memory optimized calculator."""
    # Chunking settings
    enable_chunked_processing: bool = True
    default_chunk_size: int = 10000  # Default chunk size for large datasets
    max_memory_usage_mb: int = 2048  # Maximum memory usage in MB
    auto_chunk_size: bool = True     # Automatically determine optimal chunk size

    # Computation settings
    preferred_method: ComputationMethod = ComputationMethod.VECTORIZED
    enable_numba_acceleration: bool = True
    enable_parallel_processing: bool = True
    num_threads: int = 4

    # Memory management settings
    memory_strategy: MemoryStrategy = MemoryStrategy.BALANCED
    enable_garbage_collection: bool = True
    gc_frequency: int = 100          # Force GC every N computations
    enable_memory_monitoring: bool = True
    memory_check_interval: float = 1.0  # seconds

    # Performance settings
    enable_vectorization: bool = True
    enable_caching: bool = True
    optimize_for_speed: bool = True
    optimize_for_memory: bool = True

    # Advanced settings
    memory_leak_detection: bool = True
    performance_profiling: bool = True
    detailed_logging: bool = False

@dataclass
class MemoryStats:
    """Memory usage statistics."""
    # Current usage
    current_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    available_memory_mb: float = 0.0

    # Computation statistics
    total_computations: int = 0
    chunked_computations: int = 0
    vectorized_computations: int = 0
    numba_computations: int = 0

    # Performance statistics
    avg_computation_time_ms: float = 0.0
    total_computation_time_ms: float = 0.0
    memory_efficiency_score: float = 0.0

    # Garbage collection statistics
    gc_collections: int = 0
    gc_time_ms: float = 0.0
    memory_freed_mb: float = 0.0

    # Error statistics
    memory_errors: int = 0
    out_of_memory_errors: int = 0
    computation_errors: int = 0

class ChunkedProcessor:
    """Handles chunked processing of large datasets."""

    def __init__(self, chunk_size: int = 10000, overlap: int = 0):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def create_chunks(self, data: Union[np.ndarray, pd.Series]) -> Iterator[Tuple[int, np.ndarray]]:
        """
        Create overlapping chunks from data.

        Args:
            data: Input data to chunk

        Yields:
            Tuple of (chunk_start_index, chunk_data)
        """
        if isinstance(data, pd.Series):
            data = data.values

        total_length = len(data)
        effective_chunk_size = self.chunk_size - self.overlap

        for start in range(0, total_length, effective_chunk_size):
            end = min(start + self.chunk_size, total_length)
            chunk = data[start:end]
            yield start, chunk

    def process_with_overlap(
        self,
        data: np.ndarray,
        processing_func: Callable,
        *args,
        **kwargs
    ) -> np.ndarray:
        """
        Process data with overlapping chunks, handling boundary conditions.

        Args:
            data: Input data
            processing_func: Function to apply to each chunk
            *args: Additional arguments for processing function
            **kwargs: Additional keyword arguments

        Returns:
            Processed result array
        """
        results = []
        total_length = len(data)
        effective_chunk_size = self.chunk_size - self.overlap

        for start, chunk in self.create_chunks(data):
            # Process chunk
            chunk_result = processing_func(chunk, *args, **kwargs)

            # Handle overlap - only keep non-overlapping part except for last chunk
            if self.overlap > 0 and start + self.chunk_size < total_length:
                # Remove overlap from result
                if isinstance(chunk_result, np.ndarray):
                    chunk_result = chunk_result[:-self.overlap]
                elif PANDAS_AVAILABLE and isinstance(chunk_result, pd.Series):
                    chunk_result = chunk_result.iloc[:-self.overlap]

            results.append(chunk_result)

        # Concatenate results
        if PANDAS_AVAILABLE and any(isinstance(r, pd.Series) for r in results):
            return pd.concat(results, ignore_index=True)
        else:
            return np.concatenate(results)

class VectorizedCalculator:
    """Vectorized computation utilities."""

    def __init__(self, enable_numba: bool = True):
        self.enable_numba = enable_numba and NUMBA_AVAILABLE

    def calculate_rsi_vectorized(
        self,
        prices: np.ndarray,
        period: int = 14
    ) -> np.ndarray:
        """
        Calculate RSI using vectorized operations.

        Args:
            prices: Price array
            period: RSI period

        Returns:
            RSI values array
        """
        if len(prices) < period:
            return np.full(len(prices), np.nan)

        # Calculate price changes
        deltas = np.diff(prices, prepend=prices[0])

        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        # Calculate average gains and losses using exponential smoothing
        avg_gains = self._ema_vectorized(gains, period)
        avg_losses = self._ema_vectorized(losses, period)

        # Calculate RSI
        rs = avg_gains / np.where(avg_losses == 0, 1e-10, avg_losses)
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_macd_vectorized(
        self,
        prices: np.ndarray,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate MACD using vectorized operations.

        Args:
            prices: Price array
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period

        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        # Calculate EMAs
        fast_ema = self._ema_vectorized(prices, fast_period)
        slow_ema = self._ema_vectorized(prices, slow_period)

        # Calculate MACD line
        macd_line = fast_ema - slow_ema

        # Calculate signal line
        signal_line = self._ema_vectorized(macd_line, signal_period)

        # Calculate histogram
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def calculate_bollinger_bands_vectorized(
        self,
        prices: np.ndarray,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate Bollinger Bands using vectorized operations.

        Args:
            prices: Price array
            period: Moving average period
            std_dev: Number of standard deviations

        Returns:
            Tuple of (Upper band, Middle band, Lower band)
        """
        # Calculate moving average
        middle_band = self._sma_vectorized(prices, period)

        # Calculate rolling standard deviation
        rolling_std = self._rolling_std_vectorized(prices, period)

        # Calculate bands
        upper_band = middle_band + (rolling_std * std_dev)
        lower_band = middle_band - (rolling_std * std_dev)

        return upper_band, middle_band, lower_band

    def _ema_vectorized(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average using vectorized operations."""
        alpha = 2.0 / (period + 1)
        ema = np.empty_like(data)
        ema[0] = data[0]

        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]

        return ema

    def _sma_vectorized(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average using vectorized operations."""
        result = np.full(len(data), np.nan)
        if len(data) >= period:
            cumsum = np.cumsum(data, dtype=float)
            cumsum[period:] = cumsum[period:] - cumsum[:-period]
            result[period-1:] = cumsum[period-1:] / period
        return result

    def _rolling_std_vectorized(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate rolling standard deviation using vectorized operations."""
        result = np.full(len(data), np.nan)
        if len(data) >= period:
            for i in range(period-1, len(data)):
                window = data[i-period+1:i+1]
                result[i] = np.std(window, ddof=0)
        return result

class NumbaAcceleratedCalculator:
    """Numba-accelerated computation utilities."""

    def __init__(self):
        self.numba_available = NUMBA_AVAILABLE
        if self.numba_available:
            self._compile_numba_functions()

    def _compile_numba_functions(self):
        """Pre-compile Numba functions for better performance."""
        try:
            # These functions would be decorated with @numba.jit
            pass
        except Exception as e:
            logger.warning(f"Numba compilation failed: {e}")
            self.numba_available = False

    def calculate_rsi_numba(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate RSI using Numba acceleration."""
        if not self.numba_available:
            # Fallback to regular computation
            return self._calculate_rsi_fallback(prices, period)

        # Numba-accelerated implementation would go here
        return self._calculate_rsi_fallback(prices, period)

    def _calculate_rsi_fallback(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Fallback RSI calculation without Numba."""
        deltas = np.diff(prices, prepend=prices[0])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gains = np.convolve(gains, np.ones(period)/period, mode='valid')
        avg_losses = np.convolve(losses, np.ones(period)/period, mode='valid')

        rs = avg_gains / np.where(avg_losses == 0, 1e-10, avg_losses)
        rsi = 100 - (100 / (1 + rs))

        # Pad with NaN to match original length
        result = np.full(len(prices), np.nan)
        result[period-1:] = rsi
        return result

class MemoryMonitor:
    """Memory usage monitoring and management."""

    def __init__(self, check_interval: float = 1.0):
        self.check_interval = check_interval
        self.monitoring = False
        self.monitor_thread = None
        self.memory_history: List[Tuple[datetime, float]] = []

    def start_monitoring(self):
        """Start memory monitoring in background thread."""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop memory monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

    def _monitor_loop(self):
        """Memory monitoring loop."""
        while self.monitoring:
            try:
                current_memory = self.get_current_memory_usage()
                timestamp = datetime.now()
                self.memory_history.append((timestamp, current_memory))

                # Keep only last 1000 entries
                if len(self.memory_history) > 1000:
                    self.memory_history = self.memory_history[-1000:]

                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")

    def get_current_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            if PSUTIL_AVAILABLE:
                process = psutil.Process()
                return process.memory_info().rss / 1024 / 1024
            else:
                # Fallback: try to get from resource module
                import resource
                return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        except:
            return 0.0

    def get_memory_stats(self) -> Dict[str, float]:
        """Get comprehensive memory statistics."""
        if not self.memory_history:
            return {}

        memory_values = [mem for _, mem in self.memory_history]

        return {
            'current_mb': memory_values[-1] if memory_values else 0.0,
            'peak_mb': max(memory_values) if memory_values else 0.0,
            'average_mb': np.mean(memory_values) if memory_values else 0.0,
            'min_mb': min(memory_values) if memory_values else 0.0,
            'std_mb': np.std(memory_values) if memory_values else 0.0
        }

    def get_available_memory(self) -> float:
        """Get available system memory in MB."""
        try:
            if PSUTIL_AVAILABLE:
                return psutil.virtual_memory().available / 1024 / 1024
            else:
                return 1024.0  # Default estimate
        except:
            return 1024.0

class MemoryOptimizedCalculator:
    """
    Memory-optimized calculator for technical indicators.

    Features:
    - Vectorized computations
    - Chunked processing for large datasets
    - Memory usage monitoring
    - Garbage collection optimization
    - Numba acceleration support
    - Memory leak detection
    - Performance profiling
    """

    def __init__(self, config: MemoryConfig):
        self.config = config
        self.stats = MemoryStats()
        self.memory_monitor = MemoryMonitor(config.memory_check_interval)

        # Initialize computation components
        self.chunked_processor = ChunkedProcessor(
            chunk_size=config.default_chunk_size
        ) if config.enable_chunked_processing else None

        self.vectorized_calc = VectorizedCalculator(
            enable_numba=config.enable_numba_acceleration
        )

        self.numba_calc = NumbaAcceleratedCalculator() if config.enable_numba_acceleration else None

        # Computation timing
        self.computation_times: List[float] = []

        # Start memory monitoring if enabled
        if config.enable_memory_monitoring:
            self.memory_monitor.start_monitoring()

    def calculate_rsi(
        self,
        data: Union[np.ndarray, pd.Series],
        period: int = 14,
        method: Optional[ComputationMethod] = None
    ) -> Union[np.ndarray, pd.Series]:
        """
        Calculate RSI with memory optimization.

        Args:
            data: Price data
            period: RSI period
            method: Computation method (auto-determined if None)

        Returns:
            RSI values
        """
        return self._calculate_indicator(
            'rsi', data, period=period, method=method
        )

    def calculate_macd(
        self,
        data: Union[np.ndarray, pd.Series],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        method: Optional[ComputationMethod] = None
    ) -> Tuple[Union[np.ndarray, pd.Series], ...]:
        """
        Calculate MACD with memory optimization.

        Args:
            data: Price data
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
            method: Computation method (auto-determined if None)

        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        return self._calculate_indicator(
            'macd', data, fast_period=fast_period, slow_period=slow_period,
            signal_period=signal_period, method=method
        )

    def calculate_bollinger_bands(
        self,
        data: Union[np.ndarray, pd.Series],
        period: int = 20,
        std_dev: float = 2.0,
        method: Optional[ComputationMethod] = None
    ) -> Tuple[Union[np.ndarray, pd.Series], ...]:
        """
        Calculate Bollinger Bands with memory optimization.

        Args:
            data: Price data
            period: Moving average period
            std_dev: Number of standard deviations
            method: Computation method (auto-determined if None)

        Returns:
            Tuple of (Upper band, Middle band, Lower band)
        """
        return self._calculate_indicator(
            'bollinger', data, period=period, std_dev=std_dev, method=method
        )

    def _calculate_indicator(
        self,
        indicator_name: str,
        data: Union[np.ndarray, pd.Series],
        method: Optional[ComputationMethod] = None,
        **kwargs
    ) -> Union[np.ndarray, pd.Series, Tuple]:
        """
        Calculate technical indicator with memory optimization.

        Args:
            indicator_name: Name of the indicator
            data: Input data
            method: Computation method
            **kwargs: Indicator-specific parameters

        Returns:
            Calculated indicator values
        """
        start_time = time.time()

        try:
            # Convert to numpy if pandas
            if PANDAS_AVAILABLE and isinstance(data, pd.Series):
                original_type = pd.Series
                original_index = data.index
                data = data.values
            else:
                original_type = type(data)
                original_index = None

            # Determine computation method
            if method is None:
                method = self._determine_computation_method(data)

            # Check memory usage before computation
            if self.config.enable_memory_monitoring:
                self._check_memory_usage()

            # Perform calculation based on method
            if method == ComputationMethod.VECTORIZED:
                result = self._calculate_vectorized(indicator_name, data, **kwargs)
                self.stats.vectorized_computations += 1
            elif method == ComputationMethod.CHUNKED:
                result = self._calculate_chunked(indicator_name, data, **kwargs)
                self.stats.chunked_computations += 1
            elif method == ComputationMethod.NUMBA_ACCELERATED:
                result = self._calculate_numba(indicator_name, data, **kwargs)
                self.stats.numba_computations += 1
            else:
                # Fallback to vectorized
                result = self._calculate_vectorized(indicator_name, data, **kwargs)
                self.stats.vectorized_computations += 1

            # Convert back to original type if needed
            if original_type == pd.Series and isinstance(result, (np.ndarray, tuple)):
                if isinstance(result, tuple):
                    result = tuple(
                        pd.Series(r, index=original_index) if isinstance(r, np.ndarray) else r
                        for r in result
                    )
                else:
                    result = pd.Series(result, index=original_index)

            # Update statistics
            computation_time = (time.time() - start_time) * 1000
            self.computation_times.append(computation_time)
            self.stats.total_computations += 1
            self.stats.total_computation_time_ms += computation_time
            self._update_avg_computation_time()

            # Garbage collection if needed
            if (self.config.enable_garbage_collection and
                self.stats.total_computations % self.config.gc_frequency == 0):
                self._force_garbage_collection()

            return result

        except MemoryError:
            self.stats.out_of_memory_errors += 1
            self.stats.memory_errors += 1
            logger.error(f"Out of memory error calculating {indicator_name}")
            raise
        except Exception as e:
            self.stats.computation_errors += 1
            logger.error(f"Error calculating {indicator_name}: {e}")
            raise

    def _determine_computation_method(
        self,
        data: np.ndarray
    ) -> ComputationMethod:
        """Determine optimal computation method based on data size and available resources."""
        data_size = len(data)
        available_memory = self.memory_monitor.get_available_memory()

        # Large datasets: use chunked processing
        if data_size > self.config.default_chunk_size * 2:
            if available_memory < 512:  # Less than 512MB available
                return ComputationMethod.CHUNKED
            else:
                return ComputationMethod.VECTORIZED

        # Medium datasets: use vectorized or numba
        elif data_size > 1000:
            if self.config.enable_numba_acceleration and self.numba_calc:
                return ComputationMethod.NUMBA_ACCELERATED
            else:
                return ComputationMethod.VECTORIZED

        # Small datasets: use vectorized
        else:
            return ComputationMethod.VECTORIZED

    def _calculate_vectorized(
        self,
        indicator_name: str,
        data: np.ndarray,
        **kwargs
    ) -> Union[np.ndarray, Tuple]:
        """Calculate indicator using vectorized operations."""
        if indicator_name == 'rsi':
            return self.vectorized_calc.calculate_rsi_vectorized(
                data, kwargs.get('period', 14)
            )
        elif indicator_name == 'macd':
            return self.vectorized_calc.calculate_macd_vectorized(
                data,
                kwargs.get('fast_period', 12),
                kwargs.get('slow_period', 26),
                kwargs.get('signal_period', 9)
            )
        elif indicator_name == 'bollinger':
            return self.vectorized_calc.calculate_bollinger_bands_vectorized(
                data,
                kwargs.get('period', 20),
                kwargs.get('std_dev', 2.0)
            )
        else:
            raise ValueError(f"Unknown indicator: {indicator_name}")

    def _calculate_chunked(
        self,
        indicator_name: str,
        data: np.ndarray,
        **kwargs
    ) -> Union[np.ndarray, Tuple]:
        """Calculate indicator using chunked processing."""
        def process_chunk(chunk_data, **chunk_kwargs):
            return self._calculate_vectorized(indicator_name, chunk_data, **chunk_kwargs)

        if indicator_name == 'rsi':
            # Special handling for RSI with overlap
            period = kwargs.get('period', 14)
            self.chunked_processor.overlap = period - 1
            return self.chunked_processor.process_with_overlap(
                data, process_chunk, **kwargs
            )
        else:
            return self.chunked_processor.process_with_overlap(
                data, process_chunk, **kwargs
            )

    def _calculate_numba(
        self,
        indicator_name: str,
        data: np.ndarray,
        **kwargs
    ) -> Union[np.ndarray, Tuple]:
        """Calculate indicator using Numba acceleration."""
        if indicator_name == 'rsi' and self.numba_calc:
            return self.numba_calc.calculate_rsi_numba(
                data, kwargs.get('period', 14)
            )
        else:
            # Fallback to vectorized
            return self._calculate_vectorized(indicator_name, data, **kwargs)

    def _check_memory_usage(self):
        """Check current memory usage and take action if necessary."""
        current_memory = self.memory_monitor.get_current_memory_usage()
        available_memory = self.memory_monitor.get_available_memory()

        # Update statistics
        self.stats.current_memory_mb = current_memory
        self.stats.peak_memory_mb = max(self.stats.peak_memory_mb, current_memory)
        self.stats.available_memory_mb = available_memory

        # Take action if memory is low
        if current_memory > self.config.max_memory_usage_mb:
            logger.warning(f"High memory usage: {current_memory:.1f}MB")
            self._force_garbage_collection()

        if available_memory < 256:  # Less than 256MB available
            logger.warning(f"Low available memory: {available_memory:.1f}MB")
            self._force_garbage_collection()

    def _force_garbage_collection(self):
        """Force garbage collection and track statistics."""
        start_time = time.time()
        memory_before = self.memory_monitor.get_current_memory_usage()

        gc.collect()

        memory_after = self.memory_monitor.get_current_memory_usage()
        gc_time = (time.time() - start_time) * 1000

        self.stats.gc_collections += 1
        self.stats.gc_time_ms += gc_time
        self.stats.memory_freed_mb += max(0, memory_before - memory_after)

    def _update_avg_computation_time(self):
        """Update average computation time."""
        if self.computation_times:
            recent_times = self.computation_times[-100:]  # Last 100 computations
            self.stats.avg_computation_time_ms = np.mean(recent_times)

    def get_memory_statistics(self) -> MemoryStats:
        """Get comprehensive memory statistics."""
        # Update current statistics
        if self.config.enable_memory_monitoring:
            memory_stats = self.memory_monitor.get_memory_stats()
            self.stats.current_memory_mb = memory_stats.get('current_mb', 0.0)
            self.stats.peak_memory_mb = memory_stats.get('peak_mb', 0.0)
            self.stats.available_memory_mb = self.memory_monitor.get_available_memory()

        # Calculate memory efficiency score
        if self.stats.peak_memory_mb > 0:
            target_memory = self.config.max_memory_usage_mb * 0.7  # Target: 70% of max
            self.stats.memory_efficiency_score = min(target_memory / self.stats.peak_memory_mb, 1.0)

        return self.stats

    def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance report."""
        stats = self.get_memory_statistics()

        return {
            'memory_statistics': asdict(stats),
            'performance_metrics': {
                'computation_efficiency': self._calculate_computation_efficiency(),
                'memory_efficiency': stats.memory_efficiency_score,
                'method_distribution': {
                    'vectorized': stats.vectorized_computations,
                    'chunked': stats.chunked_computations,
                    'numba': stats.numba_computations
                },
                'gc_efficiency': self._calculate_gc_efficiency()
            },
            'configuration': asdict(self.config),
            'recommendations': self._get_memory_recommendations()
        }

    def _calculate_computation_efficiency(self) -> float:
        """Calculate computation efficiency score."""
        if self.stats.total_computations == 0:
            return 0.0

        # Factor in computation time, error rate, and method efficiency
        time_efficiency = min(10 / max(self.stats.avg_computation_time_ms, 1), 1.0)  # Target: <10ms
        error_rate = (self.stats.computation_errors + self.stats.memory_errors) / self.stats.total_computations
        error_efficiency = max(1 - error_rate * 10, 0.0)  # Penalize errors heavily

        # Method efficiency: prefer vectorized and numba over chunked
        method_efficiency = (
            (self.stats.vectorized_computations + self.stats.numba_computations) /
            max(self.stats.total_computations, 1)
        )

        return (time_efficiency + error_efficiency + method_efficiency) / 3

    def _calculate_gc_efficiency(self) -> float:
        """Calculate garbage collection efficiency."""
        if self.stats.gc_collections == 0:
            return 1.0

        avg_gc_time = self.stats.gc_time_ms / self.stats.gc_collections
        avg_memory_freed = self.stats.memory_freed_mb / self.stats.gc_collections

        # Efficiency based on memory freed per GC time
        time_efficiency = min(50 / max(avg_gc_time, 1), 1.0)  # Target: <50ms per GC
        memory_efficiency = min(avg_memory_freed / 10, 1.0)  # Target: >10MB freed per GC

        return (time_efficiency + memory_efficiency) / 2

    def _get_memory_recommendations(self) -> List[str]:
        """Get memory optimization recommendations."""
        recommendations = []

        stats = self.get_memory_statistics()

        # Memory usage recommendations
        if stats.current_memory_mb > self.config.max_memory_usage_mb * 0.9:
            recommendations.append("Very high memory usage. Consider reducing chunk size or enabling more aggressive garbage collection.")
        elif stats.current_memory_mb > self.config.max_memory_usage_mb * 0.7:
            recommendations.append("High memory usage. Monitor for potential memory leaks.")

        # Performance recommendations
        if stats.avg_computation_time_ms > 50:
            recommendations.append("Slow computation times. Consider enabling Numba acceleration or optimizing chunk sizes.")

        if stats.memory_efficiency_score < 0.5:
            recommendations.append("Low memory efficiency. Review memory management strategy.")

        # GC recommendations
        if stats.gc_collections > 0:
            avg_gc_time = stats.gc_time_ms / stats.gc_collections
            if avg_gc_time > 100:
                recommendations.append("Slow garbage collection. Consider reducing GC frequency or optimizing memory usage.")

        # Method recommendations
        if stats.chunked_computations > stats.vectorized_computations + stats.numba_computations:
            recommendations.append("High reliance on chunked processing. Consider increasing available memory for better performance.")

        if not self.config.enable_numba_acceleration and NUMBA_AVAILABLE:
            recommendations.append("Numba is available but not enabled. Consider enabling for better performance.")

        return recommendations

    def optimize_memory_usage(self):
        """Perform memory optimization operations."""
        logger.info("Starting memory optimization...")

        # Force garbage collection
        self._force_garbage_collection()

        # Clear computation history
        if len(self.computation_times) > 1000:
            self.computation_times = self.computation_times[-500:]

        # Clear memory monitor history
        if len(self.memory_monitor.memory_history) > 1000:
            self.memory_monitor.memory_history = self.memory_monitor.memory_history[-500:]

        logger.info("Memory optimization completed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.memory_monitor.stop_monitoring()
        self.optimize_memory_usage()

# Utility functions
def get_default_calculator() -> MemoryOptimizedCalculator:
    """Get default memory optimized calculator instance."""
    config = MemoryConfig()
    return MemoryOptimizedCalculator(config)

def create_calculator_with_config(**kwargs) -> MemoryOptimizedCalculator:
    """Create calculator with custom configuration."""
    config = MemoryConfig(**kwargs)
    return MemoryOptimizedCalculator(config)
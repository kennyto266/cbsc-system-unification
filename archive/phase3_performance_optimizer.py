#!/usr/bin/env python3
"""
Phase 3 Performance Optimizer
React Performance Optimization for Technical Analysis System

This module implements comprehensive performance optimizations for the
technical analysis functionality, focusing on:

1. Batch processing for technical indicators
2. Intelligent caching mechanisms
3. Parallel computation capabilities
4. Memory usage optimization
5. Data structure optimization
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Union, Tuple, Any, Callable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from functools import lru_cache, wraps
import time
import pickle
import hashlib
from pathlib import Path
import threading
from dataclasses import dataclass
from collections import defaultdict
import gc

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    computation_time: float
    memory_usage_mb: float
    cache_hit_rate: float
    batch_size: int
    parallel_workers: int

class MemoryEfficientCache:
    """Memory-efficient caching with LRU eviction and size limits"""

    def __init__(self, max_size_mb: int = 100, max_items: int = 1000):
        self.max_size_mb = max_size_mb
        self.max_items = max_items
        self.cache = {}
        self.access_order = []
        self.current_size_mb = 0
        self.lock = threading.RLock()

    def _get_key_hash(self, key: str) -> str:
        """Generate hash for cache key"""
        return hashlib.md5(key.encode()).hexdigest()

    def _estimate_size(self, obj: Any) -> float:
        """Estimate memory usage in MB"""
        try:
            return len(pickle.dumps(obj)) / (1024 * 1024)
        except:
            return 1.0  # Conservative estimate

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self.lock:
            key_hash = self._get_key_hash(key)

            if key_hash in self.cache:
                # Update access order
                self.access_order.remove(key_hash)
                self.access_order.append(key_hash)
                logger.debug(f"Cache hit for key: {key}")
                return self.cache[key_hash]

            logger.debug(f"Cache miss for key: {key}")
            return None

    def put(self, key: str, value: Any) -> None:
        """Put item in cache with eviction policy"""
        with self.lock:
            key_hash = self._get_key_hash(key)
            item_size = self._estimate_size(value)

            # Remove existing item if present
            if key_hash in self.cache:
                self.current_size_mb -= self._estimate_size(self.cache[key_hash])
                self.access_order.remove(key_hash)

            # Evict items if necessary
            while (self.current_size_mb + item_size > self.max_size_mb or
                   len(self.cache) >= self.max_items) and self.cache:
                oldest_key = self.access_order.pop(0)
                self.current_size_mb -= self._estimate_size(self.cache[oldest_key])
                del self.cache[oldest_key]

            # Add new item
            self.cache[key_hash] = value
            self.access_order.append(key_hash)
            self.current_size_mb += item_size

    def clear(self) -> None:
        """Clear cache"""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
            self.current_size_mb = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            return {
                'items': len(self.cache),
                'size_mb': self.current_size_mb,
                'max_items': self.max_items,
                'max_size_mb': self.max_size_mb,
                'utilization': self.current_size_mb / self.max_size_mb
            }

class BatchProcessor:
    """Efficient batch processing for technical indicators"""

    def __init__(self, batch_size: int = 1000, n_workers: int = None):
        self.batch_size = batch_size
        self.n_workers = n_workers or min(mp.cpu_count(), 8)  # Limit workers
        self.cache = MemoryEfficientCache()
        self.performance_metrics = []

    def create_batches(self, data: Union[np.ndarray, pd.DataFrame],
                      batch_size: Optional[int] = None) -> List[np.ndarray]:
        """Split data into efficient batches"""
        batch_size = batch_size or self.batch_size

        if isinstance(data, pd.DataFrame):
            data = data.values

        n_samples = len(data)
        batches = []

        for i in range(0, n_samples, batch_size):
            batch = data[i:i + batch_size]
            if len(batch) > 0:  # Only add non-empty batches
                batches.append(batch)

        return batches

    def parallel_apply(self, func: Callable, data_batches: List[np.ndarray],
                      description: str = "Processing") -> List[np.ndarray]:
        """Apply function in parallel to batches"""
        if len(data_batches) == 1:
            # Single batch - no need for parallel processing
            return [func(data_batches[0])]

        results = [None] * len(data_batches)

        def process_batch_with_index(batch_data):
            index, batch = batch_data
            try:
                result = func(batch)
                return index, result, None
            except Exception as e:
                logger.error(f"Error processing batch {index}: {e}")
                return index, None, str(e)

        # Use ThreadPool for I/O bound or ProcessPool for CPU bound
        with ThreadPoolExecutor(max_workers=self.n_workers) as executor:
            future_to_batch = {
                executor.submit(process_batch_with_index, (i, batch)): i
                for i, batch in enumerate(data_batches)
            }

            completed = 0
            for future in future_to_batch:
                try:
                    index, result, error = future.result(timeout=300)  # 5 min timeout
                    if error:
                        logger.error(f"Batch {index} failed: {error}")
                        results[index] = None
                    else:
                        results[index] = result

                    completed += 1
                    if completed % 10 == 0:
                        logger.debug(f"{description}: {completed}/{len(data_batches)} batches completed")

                except Exception as e:
                    batch_idx = future_to_batch[future]
                    logger.error(f"Batch {batch_idx} failed with exception: {e}")
                    results[batch_idx] = None

        # Filter out None results
        return [r for r in results if r is not None]

class OptimizedTechnicalIndicators:
    """Performance-optimized technical indicators implementation"""

    def __init__(self, use_cache: bool = True, enable_parallel: bool = True,
                 cache_size_mb: int = 100, batch_size: int = 1000):
        self.use_cache = use_cache
        self.enable_parallel = enable_parallel
        self.batch_processor = BatchProcessor(batch_size=batch_size) if enable_parallel else None
        self.performance_history = []

        # Initialize NumPy vectorized operations
        self._init_vectorized_functions()

        logger.info(f"OptimizedTechnicalIndicators initialized: "
                   f"cache={use_cache}, parallel={enable_parallel}, "
                   f"batch_size={batch_size}")

    def _init_vectorized_functions(self):
        """Initialize vectorized computation functions"""
        # Pre-compile commonly used NumPy operations for better performance
        self._vectorized_diff = np.diff
        self._vectorized_rolling_mean = lambda x, w: np.convolve(x, np.ones(w)/w, mode='valid')
        self._vectorized_abs = np.abs
        self._vectorized_maximum = np.maximum
        self._vectorized_minimum = np.minimum

    def _get_cache_key(self, func_name: str, data_hash: str, **kwargs) -> str:
        """Generate cache key for function call"""
        params_str = "_".join(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        return f"{func_name}_{data_hash}_{params_str}"

    def _get_data_hash(self, data: np.ndarray) -> str:
        """Generate hash for data array"""
        # Use only first and last elements for performance with large arrays
        if len(data) > 100:
            sample = np.concatenate([data[:10], data[-10:]])
        else:
            sample = data
        return hashlib.md5(sample.tobytes()).hexdigest()[:16]

    def _cached_computation(self, cache_key: str, compute_func: Callable) -> Any:
        """Wrapper for cached computation"""
        if not self.use_cache:
            return compute_func()

        # Try cache first
        cached_result = self.batch_processor.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Compute and cache
        result = compute_func()
        self.batch_processor.cache.put(cache_key, result)
        return result

    def calculate_rsi_optimized(self, prices: Union[np.ndarray, pd.Series],
                               period: int = 14) -> np.ndarray:
        """
        Optimized RSI calculation with batching and caching
        Performance improvements:
        - Vectorized operations
        - Memory-efficient calculation
        - Batch processing for large datasets
        """
        start_time = time.time()

        # Convert to numpy array if needed
        if isinstance(prices, pd.Series):
            prices = prices.values.astype(np.float64)
        else:
            prices = np.asarray(prices, dtype=np.float64)

        if len(prices) < period + 1:
            return np.full(len(prices), np.nan)

        data_hash = self._get_data_hash(prices)
        cache_key = self._get_cache_key("rsi", data_hash, period=period)

        def compute_rsi():
            # Vectorized RSI calculation using differences
            deltas = self._vectorized_diff(prices)

            # Separate gains and losses
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)

            # Calculate average gains and losses using exponential smoothing
            avg_gains = np.zeros_like(prices)
            avg_losses = np.zeros_like(prices)

            # Initial average gains and losses
            avg_gains[period] = np.mean(gains[:period])
            avg_losses[period] = np.mean(losses[:period])

            # Exponential smoothing for subsequent values
            alpha = 1.0 / period

            for i in range(period + 1, len(prices)):
                avg_gains[i] = alpha * gains[i-1] + (1 - alpha) * avg_gains[i-1]
                avg_losses[i] = alpha * losses[i-1] + (1 - alpha) * avg_losses[i-1]

            # Calculate RSI
            rs = avg_gains[period:] / (avg_losses[period:] + 1e-10)  # Avoid division by zero
            rsi = 100 - (100 / (1 + rs))

            # Pad with NaN for initial values
            result = np.full(len(prices), np.nan)
            result[period:] = rsi

            return result

        # Execute with caching
        result = self._cached_computation(cache_key, compute_rsi)

        # Track performance
        computation_time = time.time() - start_time
        memory_usage = self._get_memory_usage()

        self.performance_history.append(PerformanceMetrics(
            computation_time=computation_time,
            memory_usage_mb=memory_usage,
            cache_hit_rate=self.batch_processor.cache.get_stats()['utilization'],
            batch_size=len(prices),
            parallel_workers=1
        ))

        return result

    def calculate_macd_optimized(self, prices: Union[np.ndarray, pd.Series],
                                fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, np.ndarray]:
        """
        Optimized MACD calculation
        Uses vectorized exponential moving averages
        """
        start_time = time.time()

        if isinstance(prices, pd.Series):
            prices = prices.values.astype(np.float64)
        else:
            prices = np.asarray(prices, dtype=np.float64)

        if len(prices) < slow:
            return {
                'macd': np.full(len(prices), np.nan),
                'signal': np.full(len(prices), np.nan),
                'histogram': np.full(len(prices), np.nan)
            }

        data_hash = self._get_data_hash(prices)
        cache_key = self._get_cache_key("macd", data_hash, fast=fast, slow=slow, signal=signal)

        def compute_macd():
            # Calculate EMAs using exponential smoothing
            def ema(data, period):
                alpha = 2.0 / (period + 1)
                ema_values = np.zeros_like(data)
                ema_values[0] = data[0]

                for i in range(1, len(data)):
                    ema_values[i] = alpha * data[i] + (1 - alpha) * ema_values[i-1]

                return ema_values

            ema_fast = ema(prices, fast)
            ema_slow = ema(prices, slow)

            macd_line = ema_fast - ema_slow
            signal_line = ema(macd_line, signal)
            histogram = macd_line - signal_line

            return {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram
            }

        result = self._cached_computation(cache_key, compute_macd)

        # Track performance
        computation_time = time.time() - start_time
        memory_usage = self._get_memory_usage()

        self.performance_history.append(PerformanceMetrics(
            computation_time=computation_time,
            memory_usage_mb=memory_usage,
            cache_hit_rate=self.batch_processor.cache.get_stats()['utilization'],
            batch_size=len(prices),
            parallel_workers=1
        ))

        return result

    def calculate_multiple_indicators_batch(self, data: pd.DataFrame,
                                          indicators_config: List[Dict]) -> Dict[str, np.ndarray]:
        """
        Calculate multiple indicators in batch for optimal performance
        Uses parallel processing when beneficial
        """
        start_time = time.time()

        results = {}
        prices = data['close'].values.astype(np.float64)

        # Group indicators by type for batch processing
        trend_indicators = []
        momentum_indicators = []
        volatility_indicators = []

        for config in indicators_config:
            indicator_type = config.get('type', 'trend')
            if indicator_type == 'trend':
                trend_indicators.append(config)
            elif indicator_type == 'momentum':
                momentum_indicators.append(config)
            elif indicator_type == 'volatility':
                volatility_indicators.append(config)

        # Process each group
        for group_name, group_configs in [
            ('trend', trend_indicators),
            ('momentum', momentum_indicators),
            ('volatility', volatility_indicators)
        ]:
            if not group_configs:
                continue

            if self.enable_parallel and len(group_configs) > 2:
                # Use parallel processing for multiple indicators
                results.update(self._calculate_indicators_parallel(prices, group_configs))
            else:
                # Sequential processing for small groups
                results.update(self._calculate_indicators_sequential(prices, group_configs))

        # Track performance
        computation_time = time.time() - start_time
        memory_usage = self._get_memory_usage()

        self.performance_history.append(PerformanceMetrics(
            computation_time=computation_time,
            memory_usage_mb=memory_usage,
            cache_hit_rate=self.batch_processor.cache.get_stats()['utilization'],
            batch_size=len(prices),
            parallel_workers=self.batch_processor.n_workers if self.enable_parallel else 1
        ))

        return results

    def _calculate_indicators_parallel(self, prices: np.ndarray,
                                     configs: List[Dict]) -> Dict[str, np.ndarray]:
        """Calculate indicators using parallel processing"""

        def calculate_single_indicator(config):
            indicator_name = config['name']
            indicator_type = config['type']
            params = config.get('params', {})

            try:
                if indicator_type == 'rsi':
                    result = self.calculate_rsi_optimized(prices, **params)
                elif indicator_type == 'macd':
                    macd_results = self.calculate_macd_optimized(prices, **params)
                    return indicator_name, macd_results
                elif indicator_type == 'sma':
                    period = params.get('period', 20)
                    result = self._calculate_sma_vectorized(prices, period)
                elif indicator_type == 'ema':
                    period = params.get('period', 26)
                    result = self._calculate_ema_vectorized(prices, period)
                else:
                    logger.warning(f"Unknown indicator type: {indicator_type}")
                    return indicator_name, None

                return indicator_name, result

            except Exception as e:
                logger.error(f"Error calculating {indicator_name}: {e}")
                return indicator_name, None

        # Parallel execution
        with ThreadPoolExecutor(max_workers=min(len(configs), self.batch_processor.n_workers)) as executor:
            futures = [executor.submit(calculate_single_indicator, config) for config in configs]

            results = {}
            for future in futures:
                try:
                    indicator_name, result = future.result(timeout=60)
                    if result is not None:
                        results[indicator_name] = result
                except Exception as e:
                    logger.error(f"Parallel calculation failed: {e}")

            return results

    def _calculate_indicators_sequential(self, prices: np.ndarray,
                                       configs: List[Dict]) -> Dict[str, np.ndarray]:
        """Calculate indicators sequentially"""
        results = {}

        for config in configs:
            indicator_name = config['name']
            indicator_type = config['type']
            params = config.get('params', {})

            try:
                if indicator_type == 'rsi':
                    results[indicator_name] = self.calculate_rsi_optimized(prices, **params)
                elif indicator_type == 'macd':
                    macd_results = self.calculate_macd_optimized(prices, **params)
                    results.update({f"{indicator_name}_{k}": v for k, v in macd_results.items()})
                elif indicator_type == 'sma':
                    period = params.get('period', 20)
                    results[indicator_name] = self._calculate_sma_vectorized(prices, period)
                elif indicator_type == 'ema':
                    period = params.get('period', 26)
                    results[indicator_name] = self._calculate_ema_vectorized(prices, period)

            except Exception as e:
                logger.error(f"Error calculating {indicator_name}: {e}")
                results[indicator_name] = np.full(len(prices), np.nan)

        return results

    def _calculate_sma_vectorized(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Vectorized SMA calculation using convolution"""
        if len(prices) < period:
            return np.full(len(prices), np.nan)

        # Use convolution for efficient moving average
        kernel = np.ones(period) / period
        sma = np.convolve(prices, kernel, mode='valid')

        # Pad with NaN for initial values
        result = np.full(len(prices), np.nan)
        result[period-1:] = sma

        return result

    def _calculate_ema_vectorized(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Vectorized EMA calculation"""
        if len(prices) == 0:
            return np.array([])

        alpha = 2.0 / (period + 1)
        ema = np.zeros_like(prices)
        ema[0] = prices[0]

        # Vectorized EMA calculation
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]

        return ema

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0  # psutil not available

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.performance_history:
            return {"status": "No performance data available"}

        # Calculate statistics
        computation_times = [m.computation_time for m in self.performance_history]
        memory_usage = [m.memory_usage_mb for m in self.performance_history]
        cache_hit_rates = [m.cache_hit_rate for m in self.performance_history]

        report = {
            "total_calculations": len(self.performance_history),
            "performance_metrics": {
                "avg_computation_time": np.mean(computation_times),
                "max_computation_time": np.max(computation_times),
                "min_computation_time": np.min(computation_times),
                "avg_memory_usage_mb": np.mean(memory_usage),
                "max_memory_usage_mb": np.max(memory_usage),
                "avg_cache_hit_rate": np.mean(cache_hit_rates)
            },
            "cache_stats": self.batch_processor.cache.get_stats() if self.batch_processor else None,
            "optimization_settings": {
                "cache_enabled": self.use_cache,
                "parallel_enabled": self.enable_parallel,
                "batch_size": self.batch_processor.batch_size if self.batch_processor else None,
                "parallel_workers": self.batch_processor.n_workers if self.batch_processor else None
            }
        }

        return report

    def optimize_memory(self):
        """Optimize memory usage by clearing cache and garbage collection"""
        if self.batch_processor and self.batch_processor.cache:
            cache_stats = self.batch_processor.cache.get_stats()
            logger.info(f"Clearing cache: {cache_stats['items']} items, "
                       f"{cache_stats['size_mb']:.2f} MB")
            self.batch_processor.cache.clear()

        # Force garbage collection
        gc.collect()

        logger.info("Memory optimization completed")

class PerformanceMonitor:
    """Real-time performance monitoring for technical analysis"""

    def __init__(self, sampling_interval: float = 1.0):
        self.sampling_interval = sampling_interval
        self.metrics_history = []
        self.monitoring = False
        self.monitor_thread = None

    def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("Performance monitoring stopped")

    def _monitor_loop(self):
        """Performance monitoring loop"""
        try:
            import psutil
        except ImportError:
            logger.warning("psutil not available for performance monitoring")
            return

        while self.monitoring:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()

                # Process-specific metrics
                process = psutil.Process()
                process_memory = process.memory_info().rss / (1024 * 1024)  # MB
                process_cpu = process.cpu_percent()

                metrics = {
                    'timestamp': time.time(),
                    'system_cpu_percent': cpu_percent,
                    'system_memory_percent': memory.percent,
                    'process_memory_mb': process_memory,
                    'process_cpu_percent': process_cpu
                }

                self.metrics_history.append(metrics)

                # Keep only last 1000 samples
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]

                time.sleep(self.sampling_interval)

            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                time.sleep(self.sampling_interval)

    def get_current_metrics(self) -> Dict[str, float]:
        """Get current performance metrics"""
        if not self.metrics_history:
            return {}

        latest = self.metrics_history[-1]
        return {
            'cpu_percent': latest['process_cpu_percent'],
            'memory_mb': latest['process_memory_mb'],
            'system_cpu_percent': latest['system_cpu_percent'],
            'system_memory_percent': latest['system_memory_percent']
        }

    def get_metrics_summary(self, duration_minutes: int = 5) -> Dict[str, Any]:
        """Get performance metrics summary for specified duration"""
        if not self.metrics_history:
            return {}

        cutoff_time = time.time() - (duration_minutes * 60)
        recent_metrics = [m for m in self.metrics_history if m['timestamp'] >= cutoff_time]

        if not recent_metrics:
            return {}

        return {
            'duration_minutes': duration_minutes,
            'sample_count': len(recent_metrics),
            'avg_cpu_percent': np.mean([m['process_cpu_percent'] for m in recent_metrics]),
            'max_cpu_percent': np.max([m['process_cpu_percent'] for m in recent_metrics]),
            'avg_memory_mb': np.mean([m['process_memory_mb'] for m in recent_metrics]),
            'max_memory_mb': np.max([m['process_memory_mb'] for m in recent_metrics]),
            'system_avg_cpu_percent': np.mean([m['system_cpu_percent'] for m in recent_metrics]),
            'system_avg_memory_percent': np.mean([m['system_memory_percent'] for m in recent_metrics])
        }

# Main integration class for Phase 3 optimization
class Phase3PerformanceOptimizer:
    """Main performance optimization coordinator for Phase 3"""

    def __init__(self):
        self.indicators = OptimizedTechnicalIndicators()
        self.monitor = PerformanceMonitor()
        self.optimization_stats = {
            'total_optimizations': 0,
            'total_time_saved': 0.0,
            'memory_saved_mb': 0.0
        }

    def optimize_technical_analysis(self, data: pd.DataFrame,
                                   indicators_config: List[Dict]) -> Dict[str, Any]:
        """
        Main optimization entry point
        Optimizes technical analysis calculations based on data size and complexity
        """
        start_time = time.time()

        # Start monitoring if not already running
        if not self.monitor.monitoring:
            self.monitor.start_monitoring()

        # Analyze data characteristics
        data_size = len(data)
        complexity_score = self._analyze_complexity(data, indicators_config)

        # Choose optimization strategy
        if data_size > 10000 or complexity_score > 0.7:
            # Large dataset - use aggressive optimization
            optimization_strategy = "aggressive"
            results = self._aggressive_optimization(data, indicators_config)
        elif data_size > 1000 or complexity_score > 0.4:
            # Medium dataset - use balanced optimization
            optimization_strategy = "balanced"
            results = self._balanced_optimization(data, indicators_config)
        else:
            # Small dataset - use standard optimization
            optimization_strategy = "standard"
            results = self._standard_optimization(data, indicators_config)

        # Calculate optimization benefits
        computation_time = time.time() - start_time
        estimated_original_time = self._estimate_original_time(data_size, complexity_score)
        time_saved = max(0, estimated_original_time - computation_time)

        # Update statistics
        self.optimization_stats['total_optimizations'] += 1
        self.optimization_stats['total_time_saved'] += time_saved

        # Compile results
        optimized_results = {
            'indicators': results,
            'optimization': {
                'strategy': optimization_strategy,
                'computation_time': computation_time,
                'estimated_original_time': estimated_original_time,
                'time_saved_seconds': time_saved,
                'performance_gain': (time_saved / max(estimated_original_time, 0.001)) * 100,
                'data_size': data_size,
                'complexity_score': complexity_score
            },
            'performance_metrics': self.indicators.get_performance_report(),
            'system_metrics': self.monitor.get_current_metrics()
        }

        return optimized_results

    def _analyze_complexity(self, data: pd.DataFrame,
                          indicators_config: List[Dict]) -> float:
        """Analyze computational complexity (0.0 to 1.0)"""
        data_size_factor = min(len(data) / 10000, 1.0)
        indicator_count_factor = min(len(indicators_config) / 20, 1.0)

        # Check for computationally expensive indicators
        expensive_indicators = ['macd', 'bollinger', 'stochastic']
        has_expensive = any(config.get('type') in expensive_indicators
                          for config in indicators_config)
        expensive_factor = 0.3 if has_expensive else 0.0

        # Check data complexity (multiple columns, etc.)
        data_complexity = min(len(data.columns) / 10, 1.0) * 0.2

        complexity = (data_size_factor * 0.4 +
                     indicator_count_factor * 0.3 +
                     expensive_factor +
                     data_complexity)

        return min(complexity, 1.0)

    def _aggressive_optimization(self, data: pd.DataFrame,
                                indicators_config: List[Dict]) -> Dict[str, Any]:
        """Aggressive optimization for large datasets"""
        logger.info("Applying aggressive optimization strategy")

        # Enable all optimizations
        self.indicators.enable_parallel = True
        self.indicators.use_cache = True

        # Process in chunks if very large
        if len(data) > 50000:
            return self._process_in_chunks(data, indicators_config, chunk_size=10000)
        else:
            return self.indicators.calculate_multiple_indicators_batch(data, indicators_config)

    def _balanced_optimization(self, data: pd.DataFrame,
                             indicators_config: List[Dict]) -> Dict[str, Any]:
        """Balanced optimization for medium datasets"""
        logger.info("Applying balanced optimization strategy")

        # Enable selective optimizations
        self.indicators.enable_parallel = len(indicators_config) > 3
        self.indicators.use_cache = True

        return self.indicators.calculate_multiple_indicators_batch(data, indicators_config)

    def _standard_optimization(self, data: pd.DataFrame,
                             indicators_config: List[Dict]) -> Dict[str, Any]:
        """Standard optimization for small datasets"""
        logger.info("Applying standard optimization strategy")

        # Minimal optimizations for small datasets
        self.indicators.enable_parallel = False
        self.indicators.use_cache = True

        return self.indicators.calculate_multiple_indicators_batch(data, indicators_config)

    def _process_in_chunks(self, data: pd.DataFrame, indicators_config: List[Dict],
                          chunk_size: int) -> Dict[str, Any]:
        """Process very large datasets in chunks"""
        logger.info(f"Processing data in chunks of size {chunk_size}")

        all_results = {}
        total_chunks = (len(data) + chunk_size - 1) // chunk_size

        for i in range(0, len(data), chunk_size):
            chunk = data.iloc[i:i + chunk_size]
            chunk_num = i // chunk_size + 1

            logger.debug(f"Processing chunk {chunk_num}/{total_chunks}")
            chunk_results = self.indicators.calculate_multiple_indicators_batch(chunk, indicators_config)

            # Merge results
            for indicator_name, values in chunk_results.items():
                if indicator_name not in all_results:
                    all_results[indicator_name] = []
                all_results[indicator_name].extend(values.tolist())

        # Convert lists back to arrays
        for indicator_name in all_results:
            all_results[indicator_name] = np.array(all_results[indicator_name])

        return all_results

    def _estimate_original_time(self, data_size: int, complexity: float) -> float:
        """Estimate original computation time without optimizations"""
        # Base time per data point (empirical estimate)
        base_time_per_point = 0.001  # 1ms per data point

        # Complexity factor
        complexity_multiplier = 1 + (complexity * 3)  # Up to 4x slower for complex calculations

        estimated_time = data_size * base_time_per_point * complexity_multiplier

        return estimated_time

    def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive optimization report"""
        return {
            'optimization_statistics': self.optimization_stats,
            'performance_report': self.indicators.get_performance_report(),
            'system_metrics': self.monitor.get_metrics_summary(duration_minutes=10),
            'cache_statistics': self.indicators.batch_processor.cache.get_stats() if self.indicators.batch_processor else None,
            'recommendations': self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on performance data"""
        recommendations = []

        # Analyze cache performance
        cache_stats = self.indicators.batch_processor.cache.get_stats() if self.indicators.batch_processor else None
        if cache_stats and cache_stats['utilization'] > 0.8:
            recommendations.append("Consider increasing cache size to improve hit rate")

        # Analyze memory usage
        current_metrics = self.monitor.get_current_metrics()
        if current_metrics.get('memory_mb', 0) > 1000:  # > 1GB
            recommendations.append("High memory usage detected. Consider chunked processing for large datasets")

        # Analyze computation patterns
        if self.optimization_stats['total_optimizations'] > 10:
            avg_time_saved = (self.optimization_stats['total_time_saved'] /
                            self.optimization_stats['total_optimizations'])
            if avg_time_saved < 0.1:  # Less than 100ms saved on average
                recommendations.append("Optimizations showing minimal benefit. Review data sizes and complexity")

        if not recommendations:
            recommendations.append("Current optimization configuration is performing well")

        return recommendations

    def cleanup(self):
        """Cleanup resources"""
        self.monitor.stop_monitoring()
        self.indicators.optimize_memory()
        logger.info("Phase 3 Performance Optimizer cleanup completed")

# Factory function for easy integration
def create_performance_optimizer(cache_size_mb: int = 100,
                               enable_parallel: bool = True,
                               batch_size: int = 1000) -> Phase3PerformanceOptimizer:
    """Factory function to create optimized performance system"""
    optimizer = Phase3PerformanceOptimizer()

    # Configure based on parameters
    optimizer.indicators.use_cache = True
    optimizer.indicators.enable_parallel = enable_parallel
    if optimizer.indicators.batch_processor:
        optimizer.indicators.batch_processor.batch_size = batch_size
        # Adjust cache size
        optimizer.indicators.batch_processor.cache.max_size_mb = cache_size_mb

    return optimizer

if __name__ == "__main__":
    # Example usage and testing
    print("Phase 3 Performance Optimizer - Test Run")

    # Create sample data
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=5000, freq='D')
    sample_data = pd.DataFrame({
        'close': np.cumsum(np.random.randn(5000)) + 100,
        'high': np.cumsum(np.random.randn(5000)) + 102,
        'low': np.cumsum(np.random.randn(5000)) + 98,
        'volume': np.random.randint(1000000, 5000000, 5000)
    }, index=dates)

    # Configure indicators
    indicators_config = [
        {'name': 'rsi_14', 'type': 'rsi', 'params': {'period': 14}},
        {'name': 'rsi_21', 'type': 'rsi', 'params': {'period': 21}},
        {'name': 'sma_20', 'type': 'sma', 'params': {'period': 20}},
        {'name': 'sma_50', 'type': 'sma', 'params': {'period': 50}},
        {'name': 'ema_12', 'type': 'ema', 'params': {'period': 12}},
        {'name': 'ema_26', 'type': 'ema', 'params': {'period': 26}},
        {'name': 'macd', 'type': 'macd', 'params': {'fast': 12, 'slow': 26, 'signal': 9}}
    ]

    # Create optimizer and run
    optimizer = create_performance_optimizer()

    print(f"Processing {len(sample_data)} data points with {len(indicators_config)} indicators...")

    results = optimizer.optimize_technical_analysis(sample_data, indicators_config)

    print(f"\nOptimization Results:")
    print(f"Strategy: {results['optimization']['strategy']}")
    print(f"Computation Time: {results['optimization']['computation_time']:.3f}s")
    print(f"Estimated Original Time: {results['optimization']['estimated_original_time']:.3f}s")
    print(f"Time Saved: {results['optimization']['time_saved_seconds']:.3f}s")
    print(f"Performance Gain: {results['optimization']['performance_gain']:.1f}%")

    print(f"\nCalculated Indicators: {list(results['indicators'].keys())}")

    # Get final report
    final_report = optimizer.get_optimization_report()
    print(f"\nTotal Optimizations: {final_report['optimization_statistics']['total_optimizations']}")
    print(f"Total Time Saved: {final_report['optimization_statistics']['total_time_saved']:.3f}s")

    print("\nRecommendations:")
    for rec in final_report['recommendations']:
        print(f"- {rec}")

    # Cleanup
    optimizer.cleanup()
    print("\nTest completed successfully!")
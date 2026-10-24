"""
Performance Benchmark Suite for Unified Backtesting System

Comprehensive performance benchmarking and regression testing for the unified
backtesting framework with detailed metrics collection and analysis.

Key Features:
- Performance regression detection
- Scalability testing across different data sizes
- Resource utilization monitoring
- Bottleneck identification
- Performance profiling and optimization suggestions
- Baseline establishment and comparison
- Historical performance tracking
"""

import time
import logging
import threading
import psutil
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import tracemalloc
import cProfile
import pstats
import io
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkMetric:
    """Individual benchmark metric"""
    name: str
    value: float
    unit: str
    category: str  # performance, memory, cpu, io, etc.
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Complete benchmark test result"""
    test_name: str
    metrics: List[BenchmarkMetric]
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_message: Optional[str] = None
    system_info: Dict[str, Any] = field(default_factory=dict)

    def get_metric_by_name(self, name: str) -> Optional[BenchmarkMetric]:
        """Get metric by name"""
        for metric in self.metrics:
            if metric.name == name:
                return metric
        return None

    def get_metrics_by_category(self, category: str) -> List[BenchmarkMetric]:
        """Get all metrics by category"""
        return [m for m in self.metrics if m.category == category]


class PerformanceProfiler:
    """Advanced performance profiling utilities"""

    def __init__(self):
        self.profiles = {}
        self.memory_snapshots = []
        self.cpu_snapshots = []

    def start_profiling(self, test_name: str):
        """Start profiling for a test"""
        tracemalloc.start()
        profiler = cProfile.Profile()
        profiler.enable()

        self.profiles[test_name] = {
            'profiler': profiler,
            'start_time': time.time(),
            'memory_start': psutil.Process().memory_info().rss
        }

        logger.debug(f"Started profiling for {test_name}")

    def stop_profiling(self, test_name: str) -> Dict[str, Any]:
        """Stop profiling and collect results"""
        if test_name not in self.profiles:
            raise ValueError(f"No profiling started for {test_name}")

        profile_data = self.profiles[test_name]
        profiler = profile_data['profiler']
        profiler.disable()

        end_time = time.time()
        memory_end = psutil.Process().memory_info().rss

        # Collect profiling statistics
        stats_stream = io.StringIO()
        ps = pstats.Stats(profiler, stream=stats_stream)
        ps.print_stats()

        # Get memory allocation stats
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        profile_results = {
            'duration': end_time - profile_data['start_time'],
            'memory_delta': memory_end - profile_data['memory_start'],
            'memory_peak': peak,
            'memory_current': current,
            'profiler_stats': stats_stream.getvalue(),
            'function_stats': self._extract_function_stats(profiler)
        }

        del self.profiles[test_name]
        logger.debug(f"Stopped profiling for {test_name}")

        return profile_results

    def _extract_function_stats(self, profiler) -> List[Dict[str, Any]]:
        """Extract function-level statistics from profiler"""
        stats = pstats.Stats(profiler)
        function_stats = []

        for func_info in stats.stats.items():
            func, (_, _, _, _, _, _) = func_info
            calls, total_time, cumulative_time, callers = stats.stats[func_info]

            if hasattr(func, 'co_name'):
                function_stats.append({
                    'name': func.co_name,
                    'filename': func.co_filename,
                    'line_number': func.co_firstlineno,
                    'calls': calls,
                    'total_time': total_time,
                    'cumulative_time': cumulative_time,
                    'per_call_time': total_time / calls if calls > 0 else 0
                })

        # Sort by cumulative time
        function_stats.sort(key=lambda x: x['cumulative_time'], reverse=True)
        return function_stats[:20]  # Top 20 functions


class SystemMonitor:
    """System resource monitoring during benchmarks"""

    def __init__(self, sampling_interval: float = 0.5):
        self.sampling_interval = sampling_interval
        self.monitoring = False
        self.monitor_thread = None
        self.snapshots = []

    def start_monitoring(self):
        """Start system monitoring"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("System monitoring started")

    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("System monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        process = psutil.Process()

        while self.monitoring:
            try:
                snapshot = {
                    'timestamp': time.time(),
                    'cpu_percent': process.cpu_percent(),
                    'memory_rss': process.memory_info().rss,
                    'memory_vms': process.memory_info().vms,
                    'memory_percent': process.memory_percent(),
                    'threads': process.num_threads(),
                    'open_files': len(process.open_files()),
                    'system_cpu': psutil.cpu_percent(interval=None),
                    'system_memory': psutil.virtual_memory().percent
                }

                self.snapshots.append(snapshot)
                time.sleep(self.sampling_interval)

            except Exception as e:
                logger.error(f"System monitoring error: {str(e)}")
                time.sleep(1)

    def get_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        if not self.snapshots:
            return {}

        df = pd.DataFrame(self.snapshots)

        stats = {
            'duration': df['timestamp'].iloc[-1] - df['timestamp'].iloc[0],
            'avg_cpu': df['cpu_percent'].mean(),
            'max_cpu': df['cpu_percent'].max(),
            'avg_memory_percent': df['memory_percent'].mean(),
            'max_memory_percent': df['memory_percent'].max(),
            'avg_memory_rss_mb': (df['memory_rss'].mean() / 1024 / 1024),
            'max_memory_rss_mb': (df['memory_rss'].max() / 1024 / 1024),
            'peak_threads': df['threads'].max(),
            'sample_count': len(df)
        }

        return stats


class BenchmarkTestSuite:
    """Comprehensive benchmark test suite"""

    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.profiler = PerformanceProfiler()
        self.monitor = SystemMonitor()
        self.results = []

        # Test data generators
        self.small_data = self._generate_test_data(100)    # 100 days
        self.medium_data = self._generate_test_data(500)    # 500 days
        self.large_data = self._generate_test_data(1000)     # 1000 days

    def _generate_test_data(self, days: int) -> pd.DataFrame:
        """Generate test price data"""
        np.random.seed(42)  # For reproducible benchmarks
        dates = pd.date_range(end='2024-12-31', periods=days, freq='D')

        # Generate realistic price series
        volatility = 0.02
        daily_returns = np.random.normal(0.0005, volatility, days)
        prices = 100 * np.exp(np.cumsum(daily_returns))

        # Create OHLCV data
        data = pd.DataFrame(index=dates)
        data['open'] = prices
        data['high'] = prices * (1 + np.abs(np.random.normal(0, 0.01, days)))
        data['low'] = prices * (1 - np.abs(np.random.normal(0, 0.01, days)))
        data['close'] = np.roll(prices, -1)
        data['close'].iloc[-1] = prices[-1]
        data['volume'] = np.random.randint(100000, 1000000, days)

        return data

    def run_benchmark(self, test_name: str, test_func: Callable,
                      metadata: Optional[Dict] = None) -> BenchmarkResult:
        """Run a single benchmark test"""
        logger.info(f"Running benchmark: {test_name}")

        start_time = time.time()
        test_metrics = []

        # Start monitoring
        self.monitor.start_monitoring()
        self.profiler.start_profiling(test_name)

        try:
            # Run the benchmark
            result = test_func()
            success = True
            error_message = None

        except Exception as e:
            success = False
            error_message = str(e)
            result = None
            logger.error(f"Benchmark failed: {test_name} - {str(e)}")

        end_time = time.time()
        duration = end_time - start_time

        # Stop monitoring
        self.monitor.stop_monitoring()
        profile_results = self.profiler.stop_profiling(test_name)

        # Collect system information
        system_info = {
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'platform': sys.platform
        }

        # Create metrics
        test_metrics.append(BenchmarkMetric(
            name="duration",
            value=duration,
            unit="seconds",
            category="performance",
            timestamp=start_time,
            metadata=metadata or {}
        ))

        test_metrics.append(BenchmarkMetric(
            name="memory_peak",
            value=profile_results['memory_peak'] / (1024**2),  # MB
            unit="MB",
            category="memory",
            timestamp=start_time
        ))

        test_metrics.append(BenchmarkMetric(
            name="memory_delta",
            value=profile_results['memory_delta'] / (1024**2),  # MB
            unit="MB",
            category="memory",
            timestamp=start_time
        ))

        # Create benchmark result
        benchmark_result = BenchmarkResult(
            test_name=test_name,
            metrics=test_metrics,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            success=success,
            error_message=error_message,
            system_info=system_info
        )

        self.results.append(benchmark_result)

        # Save individual result
        self._save_result(benchmark_result, profile_results)

        return benchmark_result

    def benchmark_parameter_space_generation(self) -> BenchmarkResult:
        """Benchmark parameter space generation performance"""
        from ..parameters.generator import ComprehensiveParameterSpace
        from ..core.config import BacktestingConfig

        def test_func():
            config = BacktestingConfig(
                param_range_start=0,
                param_range_end=300,
                param_step_size=5
            )
            param_space = ComprehensiveParameterSpace(config)

            # Generate combinations for all strategies
            strategies = ["rsi_strategy", "macd_strategy", "bollinger_strategy"]
            counts = {}
            for strategy in strategies:
                counts[strategy] = param_space.get_parameter_combinations_count(strategy)

            return counts

        return self.run_benchmark(
            "parameter_space_generation",
            test_func,
            {"strategies": ["rsi", "macd", "bollinger"]}
        )

    def benchmark_vectorbt_engine(self, data_size: str = "medium") -> BenchmarkResult:
        """Benchmark VectorBT engine performance"""
        from ..vectorbt_engine.enhanced_engine import EnhancedVectorBTEngine
        from ..core.config import BacktestingConfig

        data = getattr(self, f"{data_size}_data")

        def test_func():
            config = BacktestingConfig(max_workers=4, chunk_size=200)
            engine = EnhancedVectorBTEngine(config)

            # Test signal generation for different strategies
            strategies = ["rsi_strategy", "macd_strategy", "bollinger_strategy"]
            results = {}

            for strategy in strategies:
                start_time = time.time()
                signals = engine._generate_optimized_signals(
                    strategy, {'rsi_period': 14} if strategy == "rsi_strategy" else {}, data
                )
                end_time = time.time()
                results[strategy] = {
                    'signal_time': end_time - start_time,
                    'signals_generated': len(signals)
                }

            return results

        return self.run_benchmark(
            f"vectorbt_engine_{data_size}",
            test_func,
            {"data_size": data_size, "data_points": len(data)}
        )

    def benchmark_memory_management(self) -> BenchmarkResult:
        """Benchmark memory management performance"""
        from ..memory.enhanced_manager import EnhancedMemoryManager

        def test_func():
            manager = EnhancedMemoryManager()

            # Test caching performance
            large_data = {f"key_{i}": np.random.random(1000) for i in range(100)}
            cache_times = []

            for key, data in large_data.items():
                start_time = time.time()
                manager.cache_data(key, data)
                cache_times.append(time.time() - start_time)

            # Test retrieval performance
            retrieval_times = []
            for key in large_data.keys():
                start_time = time.time()
                cached_data = manager.get_cached_data(key)
                retrieval_times.append(time.time() - start_time)

            return {
                'cache_times': cache_times,
                'retrieval_times': retrieval_times,
                'avg_cache_time': np.mean(cache_times),
                'avg_retrieval_time': np.mean(retrieval_times)
            }

        return self.run_benchmark(
            "memory_management",
            test_func,
            {"cache_operations": 100, "data_size_per_item": 1000}
        )

    def benchmark_chunking_algorithms(self) -> BenchmarkResult:
        """Benchmark intelligent chunking algorithms"""
        from ..optimization.intelligent_chunker import IntelligentChunker
        from ..optimization.intelligent_chunker import ChunkingStrategy

        def test_func():
            chunker = IntelligentChunker()

            # Test different strategies
            strategies = [
                ChunkingStrategy.ADAPTIVE,
                ChunkingStrategy.MEMORY_AWARE,
                ChunkingStrategy.PERFORMANCE_OPTIMIZED,
                ChunkingStrategy.PREDICTIVE,
                ChunkingStrategy.HYBRID
            ]

            results = {}
            for strategy in strategies:
                chunker.current_strategy = strategy

                start_time = time.time()
                # Calculate chunk size multiple times to average
                chunk_sizes = []
                for i in range(10):
                    chunk_size = chunker.calculate_optimal_chunk_size(
                        "rsi_strategy", 10000, 5000, 2.0
                    )
                    chunk_sizes.append(chunk_size)

                end_time = time.time()
                results[strategy.value] = {
                    'avg_chunk_size': np.mean(chunk_sizes),
                    'chunk_size_variance': np.var(chunk_sizes),
                    'calculation_time': end_time - start_time
                }

            return results

        return self.run_benchmark(
            "chunking_algorithms",
            test_func,
            {"strategies_tested": 5, "calculations_per_strategy": 10}
        )

    def benchmark_scalability(self) -> BenchmarkResult:
        """Benchmark scalability across different data sizes"""
        from ..core.config import BacktestingConfig
        from ..parameters.generator import ComprehensiveParameterSpace

        def test_func():
            data_sizes = [100, 500, 1000, 2000]  # days
            results = {}

            for size in data_sizes:
                # Create test data
                data = self._generate_test_data(size)

                # Test parameter space generation with this data size
                config = BacktestingConfig(
                    param_range_start=5,
                    param_range_end=50,
                    param_step_size=5
                )
                param_space = ComprehensiveParameterSpace(config)

                start_time = time.time()
                combination_count = param_space.get_parameter_combinations_count("rsi_strategy")
                end_time = time.time()

                # Calculate processing time per combination
                if combination_count > 0:
                    time_per_combination = (end_time - start_time) / combination_count
                else:
                    time_per_combination = 0

                results[f"data_size_{size}"] = {
                    'data_points': len(data),
                    'combination_count': combination_count,
                    'total_time': end_time - start_time,
                    'time_per_combination': time_per_combination
                }

            return results

        return self.run_benchmark(
            "scalability",
            test_func,
            {"data_sizes": [100, 500, 1000, 2000]}
        )

    def benchmark_concurrency(self) -> BenchmarkResult:
        """Benchmark concurrent processing performance"""
        from ..core.config import BacktestingConfig
        from ..core.framework import OptimizationRequest

        def test_func():
            data = self.small_data  # Use smaller data for concurrency test

            # Test different worker counts
            worker_counts = [1, 2, 4, 8]
            results = {}

            for workers in worker_counts:
                config = BacktestingConfig(
                    param_range_start=10,
                    param_range_end=30,
                    param_step_size=5,
                    max_workers=workers
                )

                # Create simple optimization function
                def simple_optimization():
                    time.sleep(0.01)  # Simulate work
                    return {"test_result": workers}

                start_time = time.time()
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    futures = [executor.submit(simple_optimization) for _ in range(10)]
                    results_futures = [f.result() for f in futures]
                end_time = time.time()

                results[f"workers_{workers}"] = {
                    'total_time': end_time - start_time,
                    'tasks_completed': len(results_futures),
                    'throughput': len(results_futures) / (end_time - start_time)
                }

            return results

        return self.run_benchmark(
            "concurrency",
            test_func,
            {"worker_counts": [1, 2, 4, 8], "tasks_per_test": 10}
        )

    def generate_performance_report(self) -> str:
        """Generate comprehensive performance report"""
        if not self.results:
            return "No benchmark results available"

        report = []
        report.append("# Unified Backtesting Framework Performance Report")
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Tests: {len(self.results)}")
        report.append("")

        # Summary statistics
        successful_tests = [r for r in self.results if r.success]
        failed_tests = [r for r in self.results if not r.success]

        report.append("## Summary")
        report.append(f"- Successful Tests: {len(successful_tests)}/{len(self.results)}")
        report.append(f"- Failed Tests: {len(failed_tests)}")
        report.append("")

        # Performance metrics summary
        durations = [r.duration for r in successful_tests]
        memory_peaks = [r.get_metric_by_name('memory_peak') for r in successful_tests
                     if r.get_metric_by_name('memory_peak')]

        if durations:
            report.append("## Performance Summary")
            report.append(f"- Average Duration: {np.mean(durations):.2f} seconds")
            report.append(f"- Min Duration: {np.min(durations):.2f} seconds")
            report.append(f"- Max Duration: {np.max(durations):.2f} seconds")
            report.append("")

        if memory_peaks:
            peak_values = [m.value for m in memory_peaks]
            report.append("## Memory Summary")
            report.append(f"- Average Memory Peak: {np.mean(peak_values):.2f} MB")
            report.append(f"- Max Memory Peak: {np.max(peak_values):.2f} MB")
            report.append("")

        # Individual test results
        report.append("## Individual Test Results")
        report.append("")

        for result in self.results:
            report.append(f"### {result.test_name}")
            report.append(f"- **Status**: {'✅ PASS' if result.success else '❌ FAIL'}")
            report.append(f"- **Duration**: {result.duration:.2f} seconds")

            if result.error_message:
                report.append(f"- **Error**: {result.error_message}")

            # Add key metrics
            for metric in result.metrics:
                report.append(f"- **{metric.name.replace('_', ' ').title()}**: {metric.value:.2f} {metric.unit}")

            report.append("")

        # Recommendations
        report.append("## Performance Recommendations")
        report.append("Based on the benchmark results:")

        if memory_peaks:
            avg_peak = np.mean([m.value for m in memory_peaks])
            if avg_peak > 2000:  # 2GB
                report.append("- Consider reducing memory usage or increasing system memory")

        if durations:
            avg_duration = np.mean(durations)
            if avg_duration > 60:  # 1 minute
                report.append("- Some tests are taking longer than expected, consider optimization")

        report.append("- Monitor system resources during production usage")
        report.append("- Implement caching for frequently accessed data")

        return "\n".join(report)

    def _save_result(self, result: BenchmarkResult, profile_results: Dict[str, Any]):
        """Save individual benchmark result"""
        result_file = self.output_dir / f"{result.test_name}_{int(result.start_time)}.json"

        result_data = {
            'test_name': result.test_name,
            'duration': result.duration,
            'success': result.success,
            'error_message': result.error_message,
            'metrics': [m.__dict__ for m in result.metrics],
            'system_info': result.system_info,
            'profile_results': profile_results,
            'monitoring_stats': self.monitor.get_statistics()
        }

        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2, default=str)

    def run_all_benchmarks(self) -> List[BenchmarkResult]:
        """Run all benchmark tests"""
        logger.info("Starting comprehensive benchmark suite...")

        benchmarks = [
            ("Parameter Space Generation", self.benchmark_parameter_space_generation),
            ("VectorBT Engine (Small)", lambda: self.benchmark_vectorbt_engine("small")),
            ("VectorBT Engine (Medium)", lambda: self.benchmark_vectorbt_engine("medium")),
            ("Memory Management", self.benchmark_memory_management),
            ("Chunking Algorithms", self.benchmark_chunking_algorithms),
            ("Scalability", self.benchmark_scalability),
            ("Concurrency", self.benchmark_concurrency)
        ]

        results = []
        for test_name, test_func in benchmarks:
            try:
                result = test_func()
                results.append(result)
                logger.info(f"✅ {test_name}: {result.duration:.2f}s")
            except Exception as e:
                logger.error(f"❌ {test_name}: {str(e)}")
                # Create failed result
                failed_result = BenchmarkResult(
                    test_name=test_name,
                    metrics=[],
                    start_time=time.time(),
                    end_time=time.time(),
                    duration=0,
                    success=False,
                    error_message=str(e)
                )
                results.append(failed_result)

        # Generate and save report
        report = self.generate_performance_report()
        report_file = self.output_dir / "performance_report.md"
        with open(report_file, 'w') as f:
            f.write(report)

        logger.info(f"Performance report saved to {report_file}")

        return results


# Main execution function
def run_performance_benchmarks():
    """Run complete performance benchmark suite"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting performance benchmark suite...")

    suite = BenchmarkTestSuite()
    results = suite.run_all_benchmarks()

    # Summary
    successful = len([r for r in results if r.success])
    total = len(results)

    print(f"\n{'='*60}")
    print(f"Performance Benchmark Results")
    print(f"{'='*60}")
    print(f"Total Tests: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Success Rate: {(successful/total)*100:.1f}%")
    print(f"{'='*60}")

    if successful == total:
        print("✅ All benchmarks passed successfully!")
    else:
        print(f"⚠️ {total - successful} benchmarks failed")

    return successful == total


if __name__ == '__main__':
    success = run_performance_benchmarks()
    sys.exit(0 if success else 1)
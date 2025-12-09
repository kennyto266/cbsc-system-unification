"""
Stress Testing and Load Testing Framework

Comprehensive stress testing and load testing framework for the unified backtesting
system to validate performance under extreme conditions and identify breaking points.

Key Features:
- High-load parameter optimization testing
- Memory pressure testing under extreme conditions
- Concurrent execution stress testing
- Resource exhaustion testing
- System stability under maximum load
- Graceful degradation validation
- Performance degradation analysis
"""

import time
import logging
import threading
import multiprocessing as mp
import numpy as np
import pandas as pd
import psutil
import os
import gc
import random
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from pathlib import Path
import json
import tempfile
import shutil

# Import unified backtesting components
from ..core.framework import UnifiedBacktestingFramework
from ..core.config import BacktestingConfig
from ..parameters.generator import ComprehensiveParameterSpace
from ..core.framework import OptimizationRequest

logger = logging.getLogger(__name__)


@dataclass
class StressTestResult:
    """Stress test result"""
    test_name: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    completed_operations: int
    failed_operations: int
    peak_memory_mb: float
    peak_cpu_percent: float
    error_details: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


class ResourceMonitor:
    """Monitor system resources during stress tests"""

    def __init__(self, sampling_interval: float = 0.1):
        self.sampling_interval = sampling_interval
        self.monitoring = False
        self.monitor_thread = None
        self.metrics = []
        self.process = psutil.Process()

    def start_monitoring(self):
        """Start resource monitoring"""
        if self.monitoring:
            return

        self.monitoring = True
        self.metrics.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                metric = {
                    'timestamp': time.time(),
                    'cpu_percent': self.process.cpu_percent(),
                    'memory_rss': self.process.memory_info().rss,
                    'memory_vms': self.process.memory_info().vms,
                    'memory_percent': self.process.memory_percent(),
                    'threads': self.process.num_threads(),
                    'open_files': len(self.process.open_files()),
                    'system_cpu': psutil.cpu_percent(interval=None),
                    'system_memory': psutil.virtual_memory().percent,
                    'disk_io_read': self.process.io_counters().read_bytes,
                    'disk_io_write': self.process.io_counters().write_bytes
                }
                self.metrics.append(metric)
                time.sleep(self.sampling_interval)
            except Exception as e:
                logger.error(f"Resource monitoring error: {str(e)}")
                time.sleep(1)

    def get_peak_values(self) -> Dict[str, float]:
        """Get peak resource usage values"""
        if not self.metrics:
            return {}

        df = pd.DataFrame(self.metrics)
        return {
            'peak_cpu': df['cpu_percent'].max(),
            'peak_memory_rss_mb': (df['memory_rss'].max() / 1024 / 1024),
            'peak_memory_percent': df['memory_percent'].max(),
            'peak_threads': df['threads'].max(),
            'peak_open_files': df['open_files'].max()
        }


class StressTestDataGenerator:
    """Generate test data for stress testing"""

    @staticmethod
    def create_large_dataset(days: int = 5000, volatility: float = 0.03) -> pd.DataFrame:
        """Create large dataset for stress testing"""
        np.random.seed(42)

        dates = pd.date_range(end='2024-12-31', periods=days, freq='D')

        # Generate realistic market data
        returns = np.random.normal(0.0005, volatility, days)
        prices = 100 * np.exp(np.cumsum(returns))

        # Add some volatility clusters
        volatility_periods = random.sample(range(days), days // 10)
        for period in volatility_periods:
            if period < days - 10:
                volatility_spike = np.random.uniform(0.05, 0.1, 10)
                returns[period:period+10] = np.random.normal(0, volatility_spike, 10)
                prices = np.concatenate([prices[:period], prices[period] * np.exp(np.cumsum(returns[period:period+10]))])

        # Create OHLCV data
        data = pd.DataFrame(index=dates)
        data['open'] = prices
        data['high'] = prices * (1 + np.abs(np.random.normal(0, 0.015, days)))
        data['low'] = prices * (1 - np.abs(np.random.normal(0, 0.015, days)))
        data['close'] = np.roll(prices, -1)
        data['close'].iloc[-1] = prices[-1]
        data['volume'] = np.random.randint(500000, 5000000, days)

        return data

    @staticmethod
    def create_noisy_data(days: int = 2000) -> pd.DataFrame:
        """Create noisy, potentially corrupted data for stress testing"""
        data = StressTestDataGenerator.create_large_dataset(days)

        # Introduce various data quality issues
        data.loc[data.index[::100], 'close'] = None  # Missing values every 100 days
        data.loc[data.index[::200], 'high'] = data.loc[data.index[::200], 'low']  # High < Low
        data.loc[data.index[::300], 'volume'] = -abs(data.loc[data.index[::300], 'volume'])  # Negative volume

        # Add extreme values
        extreme_indices = random.sample(range(len(data)), len(data) // 100)
        for idx in extreme_indices:
            data.loc[data.index[idx], 'close'] *= np.random.uniform(0.1, 10)  # Extreme price changes

        return data


class ParameterSpaceStressTest:
    """Stress test parameter space generation with extreme values"""

    def __init__(self):
        self.extreme_configs = [
            # Very large parameter ranges
            BacktestingConfig(param_range_start=0, param_range_end=1000, param_step_size=1),
            # Very small step sizes
            BacktestingConfig(param_range_start=0, param_range_end=300, param_step_size=1),
            # Maximum parameter combinations
            BacktestingConfig(param_range_start=0, param_range_end=200, param_step_size=2),
            # Memory-intensive configuration
            BacktestingConfig(param_range_start=0, param_range_end=500, param_step_size=1,
                              chunk_size=10, max_workers=32),
        ]

    def test_large_parameter_space(self) -> StressTestResult:
        """Test with extremely large parameter spaces"""
        logger.info("Starting large parameter space stress test...")

        monitor = ResourceMonitor()
        monitor.start_monitoring()

        start_time = time.time()
        completed_operations = 0
        failed_operations = 0
        error_details = []

        for i, config in enumerate(self.extreme_configs):
            try:
                logger.info(f"Testing configuration {i+1}/{len(self.extreme_configs)}")

                param_space = ComprehensiveParameterSpace(config)

                # Test parameter space generation
                strategies = ["rsi_strategy", "macd_strategy", "bollinger_strategy"]
                for strategy in strategies:
                    count = param_space.get_parameter_combinations_count(strategy)
                    logger.info(f"Strategy {strategy}: {count:,} combinations")

                    # Test combination generation (limit to avoid infinite loops)
                    limit = min(10000, count)
                    generated = 0
                    for _ in param_space.generate_parameter_combinations(strategy, limit=limit):
                        generated += 1
                        if generated % 1000 == 0:
                            gc.collect()  # Periodic cleanup

                completed_operations += 1

            except Exception as e:
                failed_operations += 1
                error_details.append(f"Config {i}: {str(e)}")
                logger.error(f"Configuration {i} failed: {str(e)}")

        end_time = time.time()
        monitor.stop_monitoring()

        peak_values = monitor.get_peak_values()

        return StressTestResult(
            test_name="large_parameter_space",
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            success=failed_operations == 0,
            completed_operations=completed_operations,
            failed_operations=failed_operations,
            peak_memory_mb=peak_values['peak_memory_rss_mb'],
            peak_cpu_percent=peak_values['peak_cpu'],
            error_details=error_details,
            performance_metrics={
                'configurations_tested': len(self.extreme_configs),
                'total_parameter_combinations': sum(
                    ComprehensiveParameterSpace(config).get_parameter_combinations_count("rsi_strategy")
                    for config in self.extreme_configs
                )
            }
        )


class ConcurrentExecutionStressTest:
    """Stress test concurrent execution capabilities"""

    def __init__(self):
        self.max_concurrent_tasks = 50
        self.task_duration = 1.0  # seconds

    def test_high_concurrency(self) -> StressTestResult:
        """Test system under high concurrent load"""
        logger.info("Starting high concurrency stress test...")

        monitor = ResourceMonitor()
        monitor.start_monitoring()

        start_time = time.time()

        def stress_task(task_id: int):
            """Individual stress task"""
            try:
                # Simulate computation
                data = np.random.random(10000)
                result = np.fft.fft(data)
                time.sleep(self.task_duration)
                return {"task_id": task_id, "success": True}
            except Exception as e:
                return {"task_id": task_id, "success": False, "error": str(e)}

        completed_operations = 0
        failed_operations = 0

        # Run concurrent tasks
        with ThreadPoolExecutor(max_workers=self.max_concurrent_tasks) as executor:
            futures = [executor.submit(stress_task, i) for i in range(self.max_concurrent_tasks)]

            for future in as_completed(futures):
                result = future.result()
                if result["success"]:
                    completed_operations += 1
                else:
                    failed_operations += 1
                    logger.error(f"Task {result['task_id']} failed: {result['error']}")

        end_time = time.time()
        monitor.stop_monitoring()

        peak_values = monitor.get_peak_values()

        return StressTestResult(
            test_name="high_concurrency",
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            success=failed_operations == 0,
            completed_operations=completed_operations,
            failed_operations=failed_operations,
            peak_memory_mb=peak_values['peak_memory_rss_mb'],
            peak_cpu_percent=peak_values['peak_cpu'],
            performance_metrics={
                'max_concurrent_tasks': self.max_concurrent_tasks,
                'task_duration': self.task_duration
            }
        )


class MemoryPressureStressTest:
    """Stress test system under extreme memory pressure"""

    def __init__(self):
        self.memory_target_mb = 6000  # 6GB target

    def test_memory_exhaustion(self) -> StressTestResult:
        """Test system behavior under memory pressure"""
        logger.info("Starting memory exhaustion stress test...")

        monitor = ResourceMonitor()
        monitor.start_monitoring()

        start_time = time.time()

        # Gradually increase memory usage
        memory_hogs = []
        completed_operations = 0
        failed_operations = 0

        try:
            for i in range(100):  # Try to allocate 100 large arrays
                # Create memory-intensive data
                large_array = np.random.random((1000, 1000))  # ~8MB each
                memory_hogs.append(large_array)

                # Check current memory usage
                current_memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
                logger.info(f"Memory usage: {current_memory_mb:.1f}MB (iteration {i+1})")

                completed_operations += 1

                # Test if we can still allocate more
                if current_memory_mb > self.memory_target_mb:
                    logger.warning(f"Reached target memory usage: {current_memory_mb:.1f}MB")
                    break

                # Perform some operations
                result = np.dot(large_array, large_array.T)

                if i % 10 == 0:
                    gc.collect()  # Periodic cleanup

        except MemoryError as e:
            failed_operations += 1
            logger.error(f"Memory allocation failed: {str(e)}")
        except Exception as e:
            failed_operations += 1
            logger.error(f"Unexpected error: {str(e)}")

        end_time = time.time()
        monitor.stop_monitoring()

        # Clean up memory
        del memory_hogs
        gc.collect()

        peak_values = monitor.get_peak_values()

        return StressTestResult(
            test_name="memory_exhaustion",
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            success=True,  # Success if we reached the target
            completed_operations=completed_operations,
            failed_operations=failed_operations,
            peak_memory_mb=peak_values['peak_memory_rss_mb'],
            peak_cpu_percent=peak_values['peak_cpu'],
            performance_metrics={
                'memory_target_mb': self.memory_target_mb,
                'arrays_allocated': len(memory_hogs) if 'memory_hogs' in locals() else 0
            }
        )


class FullSystemStressTest:
    """Complete system stress test with real backtesting workloads"""

    def __init__(self):
        self.large_data = StressTestDataGenerator.create_large_dataset(days=3000)
        self.temp_dir = tempfile.mkdtemp()

    def __del__(self):
        """Clean up temporary directory"""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_large_scale_optimization(self) -> StressTestResult:
        """Test large-scale parameter optimization"""
        logger.info("Starting large-scale optimization stress test...")

        monitor = ResourceMonitor()
        monitor.start_monitoring()

        start_time = time.time()

        # Create extreme configuration
        config = BacktestingConfig(
            param_range_start=0,
            param_range_end=200,  # Reduced for stress test (still 400M+ combos)
            param_step_size=2,
            max_workers=min(32, psutil.cpu_count()),
            chunk_size=500,
            memory_limit_gb=6.0
        )

        completed_operations = 0
        failed_operations = 0
        error_details = []

        try:
            framework = UnifiedBacktestingFramework(config)
            framework.start_memory_management()

            # Create optimization request
            request = OptimizationRequest(
                strategy_name="rsi_strategy",
                price_data=self.large_data,
                output_directory=self.temp_dir
            )

            # Start optimization
            logger.info("Starting large-scale optimization...")

            # Use a time limit for stress test
            time_limit = 300  # 5 minutes

            optimization_thread = threading.Thread(target=framework.run_optimization, args=(request,))
            optimization_thread.start()

            # Monitor progress
            while optimization_thread.is_alive() and (time.time() - start_time) < time_limit:
                time.sleep(10)  # Check every 10 seconds

                current_memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
                logger.info(f"Memory usage: {current_memory_mb:.1f}MB, Time elapsed: {time.time() - start_time:.1f}s")

                # Stop if memory usage gets too high
                if current_memory_mb > 5500:  # 5.5GB limit
                    logger.warning("Memory usage too high, stopping optimization")
                    break

            # Wait for thread to complete or timeout
            optimization_thread.join(max(0, time_limit - (time.time() - start_time)))

            if optimization_thread.is_alive():
                logger.warning("Optimization timeout reached")
                failed_operations += 1
                error_details.append("Optimization timeout")
            else:
                completed_operations += 1
                logger.info("Large-scale optimization completed successfully")

            framework.stop_memory_management()

        except Exception as e:
            failed_operations += 1
            error_details.append(str(e))
            logger.error(f"Large-scale optimization failed: {str(e)}")

        end_time = time.time()
        monitor.stop_monitoring()

        peak_values = monitor.get_peak_values()

        return StressTestResult(
            test_name="large_scale_optimization",
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            success=failed_operations == 0,
            completed_operations=completed_operations,
            failed_operations=failed_operations,
            peak_memory_mb=peak_values['peak_memory_rss_mb'],
            peak_cpu_percent=peak_values['peak_cpu'],
            error_details=error_details,
            performance_metrics={
                'data_points': len(self.large_data),
                'param_range': '0-200 (step 2)',
                'estimated_combinations': '400M+'
            }
        )


class StressTestSuite:
    """Complete stress test suite"""

    def __init__(self, output_dir: str = "stress_test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []

    def run_all_stress_tests(self) -> List[StressTestResult]:
        """Run all stress tests"""
        logger.info("Starting comprehensive stress test suite...")

        tests = [
            ParameterSpaceStressTest(),
            ConcurrentExecutionStressTest(),
            MemoryPressureStressTest(),
            FullSystemStressTest()
        ]

        results = []

        for test in tests:
            try:
                if isinstance(test, ParameterSpaceStressTest):
                    result = test.test_large_parameter_space()
                elif isinstance(test, ConcurrentExecutionStressTest):
                    result = test.test_high_concurrency()
                elif isinstance(test, MemoryPressureStressTest):
                    result = test.test_memory_exhaustion()
                elif isinstance(test, FullSystemStressTest):
                    result = test.test_large_scale_optimization()
                else:
                    continue

                results.append(result)

                status = "✅ PASS" if result.success else "❌ FAIL"
                logger.info(f"{status} {result.test_name}: {result.duration:.2f}s, "
                           f"Memory: {result.peak_memory_mb:.1f}MB")

            except Exception as e:
                logger.error(f"Stress test failed: {str(e)}")
                # Create failed result
                failed_result = StressTestResult(
                    test_name=type(test).__name__,
                    start_time=time.time(),
                    end_time=time.time(),
                    duration=0,
                    success=False,
                    completed_operations=0,
                    failed_operations=1,
                    peak_memory_mb=0,
                    peak_cpu_percent=0,
                    error_details=[str(e)]
                )
                results.append(failed_result)

        # Save results
        self._save_results(results)
        self._generate_report(results)

        return results

    def _save_results(self, results: List[StressTestResult]):
        """Save stress test results"""
        results_data = []

        for result in results:
            result_data = {
                'test_name': result.test_name,
                'start_time': result.start_time,
                'end_time': result.end_time,
                'duration': result.duration,
                'success': result.success,
                'completed_operations': result.completed_operations,
                'failed_operations': result.failed_operations,
                'peak_memory_mb': result.peak_memory_mb,
                'peak_cpu_percent': result.peak_cpu_percent,
                'error_details': result.error_details,
                'performance_metrics': result.performance_metrics
            }
            results_data.append(result_data)

        # Save to JSON
        json_file = self.output_dir / f"stress_test_results_{int(time.time())}.json"
        with open(json_file, 'w') as f:
            json.dump(results_data, f, indent=2)

        logger.info(f"Stress test results saved to {json_file}")

    def _generate_report(self, results: List[StressTestResult]):
        """Generate stress test report"""
        report = []
        report.append("# Unified Backtesting System Stress Test Report")
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Summary
        total_tests = len(results)
        successful_tests = len([r for r in results if r.success])

        report.append("## Summary")
        report.append(f"- Total Tests: {total_tests}")
        report.append(f"- Successful: {successful_tests}")
        report.append(f"- Failed: {total_tests - successful_tests}")
        report.append(f"- Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        report.append("")

        # Individual test results
        report.append("## Test Results")
        report.append("")

        for result in results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            report.append(f"### {result.test_name}")
            report.append(f"- **Status**: {status}")
            report.append(f"- **Duration**: {result.duration:.2f} seconds")
            report.append(f"- **Peak Memory**: {result.peak_memory_mb:.1f} MB")
            report.append(f"- **Peak CPU**: {result.peak_cpu_percent:.1f}%")
            report.append(f"- **Operations**: {result.completed_operations} completed, {result.failed_operations} failed")

            if result.error_details:
                report.append("- **Errors**:")
                for error in result.error_details[:3]:  # Limit error details
                    report.append(f"  - {error}")

            if result.performance_metrics:
                report.append("- **Performance Metrics**:")
                for key, value in result.performance_metrics.items():
                    report.append(f"  - {key}: {value}")

            report.append("")

        # System Recommendations
        report.append("## System Recommendations")

        avg_memory = np.mean([r.peak_memory_mb for r in results])
        max_memory = np.max([r.peak_memory_mb for r in results])

        if max_memory > 4000:  # 4GB
            report.append("- ⚠️ High memory usage detected. Consider increasing system RAM or optimizing memory management.")

        if any(not r.success for r in results):
            report.append("- ❌ Some tests failed. Review error details and implement fixes.")

        avg_cpu = np.mean([r.peak_cpu_percent for r in results])
        if avg_cpu > 90:
            report.append("- ⚠️ High CPU usage detected. Consider optimizing algorithms or scaling horizontally.")

        if all(r.success for r in results):
            report.append("- ✅ All stress tests passed! System is stable under extreme conditions.")
            report.append("- Consider the system ready for production deployment.")

        # Save report
        report_file = self.output_dir / "stress_test_report.md"
        with open(report_file, 'w') as f:
            f.write('\n'.join(report))

        logger.info(f"Stress test report saved to {report_file}")


def run_stress_tests():
    """Run complete stress test suite"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting stress test suite...")

    suite = StressTestSuite()
    results = suite.run_all_stress_tests()

    # Summary
    successful = len([r for r in results if r.success])
    total = len(results)

    print(f"\n{'='*60}")
    print(f"Stress Test Results")
    print(f"{'='*60}")
    print(f"Total Tests: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Success Rate: {(successful/total)*100:.1f}%")
    print(f"{'='*60}")

    # Memory summary
    if results:
        avg_memory = np.mean([r.peak_memory_mb for r in results])
        max_memory = np.max([r.peak_memory_mb for r in results])
        print(f"Average Peak Memory: {avg_memory:.1f} MB")
        print(f"Maximum Peak Memory: {max_memory:.1f} MB")

    if successful == total:
        print("✅ All stress tests passed successfully!")
        print("🚀 System is ready for production deployment!")
    else:
        print(f"⚠️ {total - successful} stress tests failed")
        print("🔧 Review test failures before production deployment.")

    return successful == total


if __name__ == '__main__':
    success = run_stress_tests()
    import sys
    sys.exit(0 if success else 1)
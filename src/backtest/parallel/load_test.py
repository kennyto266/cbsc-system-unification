"""
Load testing framework for CBSC multiprocessing system.

Provides comprehensive stress testing capabilities to validate system stability,
performance under load, and error handling over extended periods.
"""

import time
import logging
import threading
import random
import json
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import statistics

# Import integration and monitoring components
try:
    from .integration import CBSCMultiprocessingIntegration, BacktestRequest
    from .monitor import get_monitor
    from .performance_metrics import get_metrics_collector
    from .benchmark import BenchmarkDataGenerator
    LOAD_TEST_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Load testing components not available: {e}")
    LOAD_TEST_AVAILABLE = False


@dataclass
class LoadTestConfig:
    """Configuration for load test execution."""
    test_name: str
    duration_hours: int
    concurrent_backtests: int
    max_parameter_count: int
    min_parameter_count: int
    error_rate_threshold: float  # Maximum acceptable error rate (0.1 = 10%)
    stability_rate_threshold: float  # Minimum stability rate (0.999 = 99.9%)
    memory_threshold_mb: float
    health_check_interval_sec: int
    output_directory: str
    enable_monitoring: bool
    enable_error_injection: bool


@dataclass
class LoadTestResult:
    """Individual load test execution result."""
    test_id: str
    start_time: datetime
    end_time: datetime
    execution_time_sec: float
    success: bool
    error_message: Optional[str]
    parameter_count: int
    memory_usage_mb: float
    cpu_utilization: float


@dataclass
class LoadTestStatistics:
    """Aggregated load test statistics."""
    total_backtests: int
    successful_backtests: int
    failed_backtests: int
    error_rate: float
    stability_rate: float
    avg_execution_time_sec: float
    min_execution_time_sec: float
    max_execution_time_sec: float
    avg_throughput_tps: float
    peak_memory_mb: float
    avg_memory_mb: float
    peak_cpu_utilization: float
    avg_cpu_utilization: float
    total_data_processed_gb: float


@dataclass
class SystemHealthMetrics:
    """Current system health status."""
    timestamp: datetime
    memory_usage_mb: float
    memory_percent: float
    cpu_utilization: float
    active_threads: int
    queued_tasks: int
    error_count: int
    warning_count: int


class ErrorInjector:
    """Injects synthetic errors for testing error handling."""

    def __init__(self, enable_error_injection: bool = False):
        self.enabled = enable_error_injection
        self.error_types = [
            'timeout_error',
            'memory_error',
            'network_error',
            'data_corruption',
            'resource_exhaustion'
        ]
        self.error_probability = 0.01  # 1% chance of error

    def should_inject_error(self) -> bool:
        """Determine if an error should be injected."""
        if not self.enabled:
            return False
        return random.random() < self.error_probability

    def inject_error(self) -> Exception:
        """Generate a synthetic error."""
        error_type = random.choice(self.error_types)

        if error_type == 'timeout_error':
            return TimeoutError("Simulated timeout during backtest execution")
        elif error_type == 'memory_error':
            return MemoryError("Simulated memory allocation failure")
        elif error_type == 'network_error':
            return ConnectionError("Simulated network connectivity issue")
        elif error_type == 'data_corruption':
            return ValueError("Simulated data corruption detected")
        else:  # resource_exhaustion
            return RuntimeError("Simulated resource exhaustion")


class LoadTestWorker:
    """Individual worker for load testing."""

    def __init__(self,
                 worker_id: int,
                 integration: CBSCMultiprocessingIntegration,
                 data_generator: BenchmarkDataGenerator,
                 config: LoadTestConfig):
        self.worker_id = worker_id
        self.integration = integration
        self.data_generator = data_generator
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.worker_{worker_id}")

        # Statistics
        self.executed_tests = 0
        self.successful_tests = 0
        self.failed_tests = 0
        self.total_data_processed_mb = 0.0

        # Error injector
        self.error_injector = ErrorInjector(config.enable_error_injection)

    def execute_load_test_batch(self, duration_sec: int) -> List[LoadTestResult]:
        """Execute a batch of load tests for specified duration."""
        results = []
        end_time = time.time() + duration_sec

        self.logger.info(f"Worker {self.worker_id} starting load test batch for {duration_sec}s")

        while time.time() < end_time:
            try:
                result = self._execute_single_test()
                results.append(result)

                # Brief pause to prevent overwhelming the system
                time.sleep(random.uniform(0.1, 0.5))

            except Exception as e:
                self.logger.error(f"Worker {self.worker_id} batch execution failed: {e}")
                break

        self.logger.info(f"Worker {self.worker_id} completed {len(results)} tests")
        return results

    def _execute_single_test(self) -> LoadTestResult:
        """Execute a single load test."""
        test_id = f"load_test_{self.worker_id}_{int(time.time())}"
        start_time = datetime.now()

        # Generate test parameters
        parameter_count = random.randint(self.config.min_parameter_count, self.config.max_parameter_count)
        strategy_code = self.data_generator.generate_strategy_code(random.choice(['medium', 'high']))
        parameters = self.data_generator.generate_parameters(parameter_count, 'high')
        data_config = self.data_generator.generate_data_config(random.uniform(10, 100))

        # Inject error if configured
        if self.error_injector.should_inject_error():
            synthetic_error = self.error_injector.inject_error()
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            self.failed_tests += 1
            return LoadTestResult(
                test_id=test_id,
                start_time=start_time,
                end_time=end_time,
                execution_time_sec=execution_time,
                success=False,
                error_message=str(synthetic_error),
                parameter_count=parameter_count,
                memory_usage_mb=0.0,
                cpu_utilization=0.0
            )

        # Get system metrics before execution
        start_metrics = self._get_system_metrics()

        try:
            # Execute backtest
            result = self.integration.execute_backtest(
                strategy_code=strategy_code,
                parameters={'parameter_grid': parameters},
                data_config=data_config,
                use_multiprocessing=True
            )

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # Get system metrics after execution
            end_metrics = self._get_system_metrics()

            # Update statistics
            self.executed_tests += 1
            if result.success:
                self.successful_tests += 1
            else:
                self.failed_tests += 1

            self.total_data_processed_mb += data_config.get('estimated_size_mb', 0)

            return LoadTestResult(
                test_id=test_id,
                start_time=start_time,
                end_time=end_time,
                execution_time_sec=execution_time,
                success=result.success,
                error_message=result.error_message,
                parameter_count=parameter_count,
                memory_usage_mb=end_metrics['memory_mb'],
                cpu_utilization=end_metrics['cpu_percent']
            )

        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            self.executed_tests += 1
            self.failed_tests += 1

            return LoadTestResult(
                test_id=test_id,
                start_time=start_time,
                end_time=end_time,
                execution_time_sec=execution_time,
                success=False,
                error_message=str(e),
                parameter_count=parameter_count,
                memory_usage_mb=0.0,
                cpu_utilization=0.0
            )

    def _get_system_metrics(self) -> Dict[str, float]:
        """Get current system resource metrics."""
        try:
            import psutil
            return {
                'memory_mb': psutil.virtual_memory().used / 1024 / 1024,
                'cpu_percent': psutil.cpu_percent(interval=0.1)
            }
        except ImportError:
            return {'memory_mb': 0, 'cpu_percent': 0}


class LoadTestFramework:
    """Main load testing framework."""

    def __init__(self, config: LoadTestConfig):
        if not LOAD_TEST_AVAILABLE:
            raise RuntimeError("Load testing components not available")

        self.config = config
        self.logger = logging.getLogger(__name__)

        # Setup output directory
        self.output_dir = Path(config.output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.integration = CBSCMultiprocessingIntegration(
            enable_monitoring=config.enable_monitoring,
            enable_metrics=True
        )
        self.data_generator = BenchmarkDataGenerator()

        # Test state
        self.results = []
        self.health_metrics = []
        self.start_time = None
        self.end_time = None
        self.stop_event = threading.Event()

        # Workers
        self.workers = []
        self.worker_results_queue = queue.Queue()

    def run_load_test(self) -> LoadTestStatistics:
        """Run the complete load test."""
        self.logger.info(f"Starting load test: {self.config.test_name}")
        self.logger.info(f"Duration: {self.config.duration_hours} hours")
        self.logger.info(f"Concurrent backtests: {self.config.concurrent_backtests}")

        self.start_time = datetime.now()

        try:
            # Start health monitoring
            health_thread = threading.Thread(target=self._health_monitoring_loop, daemon=True)
            health_thread.start()

            # Start load test workers
            results = self._execute_load_test()

            # Calculate statistics
            statistics = self._calculate_statistics(results)

            # Save results
            self._save_results(statistics)

            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()

            self.logger.info(f"Load test completed in {duration:.2f} seconds")
            self.logger.info(f"Total tests: {statistics.total_backtests}")
            self.logger.info(f"Success rate: {statistics.stability_rate:.4f}")
            self.logger.info(f"Error rate: {statistics.error_rate:.4f}")

            return statistics

        except Exception as e:
            self.logger.error(f"Load test failed: {e}")
            raise

        finally:
            self.stop_event.set()
            self.integration.shutdown()

    def _execute_load_test(self) -> List[LoadTestResult]:
        """Execute load test with concurrent workers."""
        duration_sec = self.config.duration_hours * 3600
        results = []

        # Create workers
        self.workers = [
            LoadTestWorker(i, self.integration, self.data_generator, self.config)
            for i in range(self.config.concurrent_backtests)
        ]

        # Execute load test batches
        self.logger.info(f"Starting {len(self.workers)} workers for {duration_sec}s")

        with ThreadPoolExecutor(max_workers=self.config.concurrent_backtests) as executor:
            # Submit worker tasks
            futures = [
                executor.submit(worker.execute_load_test_batch, duration_sec)
                for worker in self.workers
            ]

            # Collect results as they complete
            for future in as_completed(futures, timeout=duration_sec + 300):
                try:
                    worker_results = future.result()
                    results.extend(worker_results)
                    self.logger.info(f"Collected {len(worker_results)} results from worker")

                except Exception as e:
                    self.logger.error(f"Worker execution failed: {e}")

        self.results = results
        return results

    def _health_monitoring_loop(self):
        """Background health monitoring loop."""
        while not self.stop_event.is_set():
            try:
                # Collect health metrics
                health_metrics = self._collect_health_metrics()
                self.health_metrics.append(health_metrics)

                # Check for critical conditions
                self._check_critical_conditions(health_metrics)

                # Sleep until next check
                self.stop_event.wait(timeout=self.config.health_check_interval_sec)

            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")

    def _collect_health_metrics(self) -> SystemHealthMetrics:
        """Collect current system health metrics."""
        try:
            import psutil

            # Get monitor status if available
            monitor_status = {}
            if self.config.enable_monitoring:
                monitor = get_monitor()
                if monitor:
                    status_report = monitor.get_status_report()
                    monitor_status = {
                        'active_alerts': len(status_report.get('alerts', {}).get('active_alerts', 0)),
                        'critical_alerts': len(status_report.get('alerts', {}).get('critical', 0))
                    }

            return SystemHealthMetrics(
                timestamp=datetime.now(),
                memory_usage_mb=psutil.virtual_memory().used / 1024 / 1024,
                memory_percent=psutil.virtual_memory().percent,
                cpu_utilization=psutil.cpu_percent(interval=0.1),
                active_threads=threading.active_count(),
                queued_tasks=self.worker_results_queue.qsize(),
                error_count=monitor_status.get('critical_alerts', 0),
                warning_count=monitor_status.get('active_alerts', 0)
            )

        except Exception as e:
            self.logger.error(f"Error collecting health metrics: {e}")
            return SystemHealthMetrics(
                timestamp=datetime.now(),
                memory_usage_mb=0.0,
                memory_percent=0.0,
                cpu_utilization=0.0,
                active_threads=0,
                queued_tasks=0,
                error_count=0,
                warning_count=0
            )

    def _check_critical_conditions(self, metrics: SystemHealthMetrics):
        """Check for critical system conditions."""
        critical_conditions = []

        # Memory threshold
        if metrics.memory_usage_mb > self.config.memory_threshold_mb:
            critical_conditions.append(f"Memory usage exceeded threshold: {metrics.memory_usage_mb:.1f}MB")

        # High error count
        if metrics.error_count > 10:
            critical_conditions.append(f"High error count: {metrics.error_count}")

        # Very low memory (potential crash)
        if metrics.memory_percent > 95:
            critical_conditions.append(f"Critical memory usage: {metrics.memory_percent:.1f}%")

        if critical_conditions:
            self.logger.critical("CRITICAL CONDITIONS DETECTED:")
            for condition in critical_conditions:
                self.logger.critical(f"  - {condition}")

            # In production, this might trigger emergency shutdown or alerting
            # For testing, we just log the conditions

    def _calculate_statistics(self, results: List[LoadTestResult]) -> LoadTestStatistics:
        """Calculate comprehensive load test statistics."""
        if not results:
            return LoadTestStatistics(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        # Basic counts
        total_tests = len(results)
        successful_tests = len([r for r in results if r.success])
        failed_tests = total_tests - successful_tests

        # Rates
        error_rate = failed_tests / total_tests if total_tests > 0 else 0
        stability_rate = successful_tests / total_tests if total_tests > 0 else 0

        # Execution times
        execution_times = [r.execution_time_sec for r in results]
        avg_execution_time = statistics.mean(execution_times) if execution_times else 0
        min_execution_time = min(execution_times) if execution_times else 0
        max_execution_time = max(execution_times) if execution_times else 0

        # Throughput
        total_duration = (self.end_time or datetime.now() - self.start_time).total_seconds()
        avg_throughput = total_tests / total_duration if total_duration > 0 else 0

        # Resource usage
        memory_usages = [r.memory_usage_mb for r in results if r.memory_usage_mb > 0]
        cpu_usages = [r.cpu_utilization for r in results if r.cpu_utilization > 0]

        peak_memory = max(memory_usages) if memory_usages else 0
        avg_memory = statistics.mean(memory_usages) if memory_usages else 0
        peak_cpu = max(cpu_usages) if cpu_usages else 0
        avg_cpu = statistics.mean(cpu_usages) if cpu_usages else 0

        # Data processed
        total_data_gb = sum(r.parameter_count * 0.001 for r in results)  # Rough estimate

        return LoadTestStatistics(
            total_backtests=total_tests,
            successful_backtests=successful_tests,
            failed_backtests=failed_tests,
            error_rate=error_rate,
            stability_rate=stability_rate,
            avg_execution_time_sec=avg_execution_time,
            min_execution_time_sec=min_execution_time,
            max_execution_time_sec=max_execution_time,
            avg_throughput_tps=avg_throughput,
            peak_memory_mb=peak_memory,
            avg_memory_mb=avg_memory,
            peak_cpu_utilization=peak_cpu,
            avg_cpu_utilization=avg_cpu,
            total_data_processed_gb=total_data_gb
        )

    def _save_results(self, statistics: LoadTestStatistics):
        """Save load test results to files."""
        try:
            # Save detailed results
            results_file = self.output_dir / f"{self.config.test_name}_detailed_results.json"
            with open(results_file, 'w') as f:
                json.dump([asdict(r) for r in self.results], f, indent=2, default=str)

            # Save statistics summary
            stats_file = self.output_dir / f"{self.config.test_name}_statistics.json"
            with open(stats_file, 'w') as f:
                json.dump(asdict(statistics), f, indent=2, default=str)

            # Save health metrics
            health_file = self.output_dir / f"{self.config.test_name}_health_metrics.json"
            with open(health_file, 'w') as f:
                json.dump([asdict(h) for h in self.health_metrics], f, indent=2, default=str)

            # Generate and save validation report
            validation = self._validate_stability_targets(statistics)
            validation_file = self.output_dir / f"{self.config.test_name}_validation.json"
            with open(validation_file, 'w') as f:
                json.dump(validation, f, indent=2, default=str)

            self.logger.info(f"Load test results saved to {self.output_dir}")

        except Exception as e:
            self.logger.error(f"Error saving results: {e}")

    def _validate_stability_targets(self, statistics: LoadTestStatistics) -> Dict[str, Any]:
        """Validate if stability targets are met."""
        validation = {
            'test_name': self.config.test_name,
            'targets_met': {},
            'targets_failed': {},
            'overall_success': False,
            'recommendations': []
        }

        # Check error rate target
        error_rate_ok = statistics.error_rate <= self.config.error_rate_threshold
        validation['targets_met']['error_rate'] = error_rate_ok
        if not error_rate_ok:
            validation['targets_failed']['error_rate'] = {
                'target': self.config.error_rate_threshold,
                'actual': statistics.error_rate
            }
            validation['recommendations'].append("Error rate exceeds threshold. Review error handling and resource limits.")

        # Check stability rate target
        stability_rate_ok = statistics.stability_rate >= self.config.stability_rate_threshold
        validation['targets_met']['stability_rate'] = stability_rate_ok
        if not stability_rate_ok:
            validation['targets_failed']['stability_rate'] = {
                'target': self.config.stability_rate_threshold,
                'actual': statistics.stability_rate
            }
            validation['recommendations'].append("Stability rate below target. Increase system reliability and error recovery.")

        # Check memory usage target
        memory_ok = statistics.peak_memory_mb < self.config.memory_threshold_mb
        validation['targets_met']['memory_usage'] = memory_ok
        if not memory_ok:
            validation['targets_failed']['memory_usage'] = {
                'target': f"< {self.config.memory_threshold_mb} MB",
                'actual': f"{statistics.peak_memory_mb:.1f} MB"
            }
            validation['recommendations'].append("Memory usage exceeds limit. Optimize memory management and data processing.")

        # Check reasonable execution time
        reasonable_execution_time = statistics.avg_execution_time_sec < 300  # 5 minutes
        validation['targets_met']['execution_time'] = reasonable_execution_time
        if not reasonable_execution_time:
            validation['targets_failed']['execution_time'] = {
                'target': "< 300 seconds",
                'actual': f"{statistics.avg_execution_time_sec:.1f} seconds"
            }
            validation['recommendations'].append("Average execution time too high. Optimize algorithm efficiency.")

        validation['overall_success'] = all(validation['targets_met'].values())

        return validation


def run_stress_test(duration_hours: int = 1,
                   concurrent_backtests: int = 5,
                   output_directory: str = "./load_test_results") -> LoadTestStatistics:
    """Run standard stress test."""
    config = LoadTestConfig(
        test_name="standard_stress_test",
        duration_hours=duration_hours,
        concurrent_backtests=concurrent_backtests,
        max_parameter_count=50000,
        min_parameter_count=1000,
        error_rate_threshold=0.001,  # 0.1%
        stability_rate_threshold=0.999,  # 99.9%
        memory_threshold_mb=4096,
        health_check_interval_sec=30,
        output_directory=output_directory,
        enable_monitoring=True,
        enable_error_injection=False
    )

    framework = LoadTestFramework(config)
    return framework.run_load_test()


def run_quick_stress_test(output_directory: str = "./load_test_results") -> LoadTestStatistics:
    """Run quick stress test for validation."""
    config = LoadTestConfig(
        test_name="quick_stress_validation",
        duration_hours=0.25,  # 15 minutes
        concurrent_backtests=3,
        max_parameter_count=10000,
        min_parameter_count=1000,
        error_rate_threshold=0.01,  # 1%
        stability_rate_threshold=0.99,  # 99%
        memory_threshold_mb=2048,
        health_check_interval_sec=60,
        output_directory=output_directory,
        enable_monitoring=True,
        enable_error_injection=True
    )

    framework = LoadTestFramework(config)
    return framework.run_load_test()
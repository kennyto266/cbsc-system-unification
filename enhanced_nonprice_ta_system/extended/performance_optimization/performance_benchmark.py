"""
Phase 5.3: Performance Benchmark System

Comprehensive performance testing and monitoring system with automated
benchmarking, regression detection, and performance alerting.

Author: Claude Code Assistant
Version: 1.0.0
"""

import time
import json
import threading
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from pathlib import Path
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

# Configure logging
logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity enumeration."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class BenchmarkType(Enum):
    """Benchmark test type enumeration."""
    PERFORMANCE = "performance"
    MEMORY = "memory"
    SCALABILITY = "scalability"
    REGRESSION = "regression"
    STRESS = "stress"

class PerformanceMetric(Enum):
    """Performance metric enumeration."""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    CACHE_HIT_RATE = "cache_hit_rate"
    ERROR_RATE = "error_rate"

@dataclass
class BenchmarkConfig:
    """Configuration for performance benchmarking."""
    # Test settings
    test_duration_seconds: int = 300  # 5 minutes
    warmup_duration_seconds: int = 30  # 30 seconds
    concurrent_users: int = 10
    requests_per_second: int = 100

    # Performance targets
    target_response_time_ms: float = 100.0  # Target response time
    target_memory_usage_mb: float = 2048.0   # Target memory usage
    target_cache_hit_rate: float = 80.0      # Target cache hit rate (%)
    target_throughput: float = 1000.0        # Target throughput (req/sec)

    # Regression detection
    enable_regression_detection: bool = True
    regression_threshold_percent: float = 10.0  # Alert if performance drops by 10%
    baseline_comparison_file: str = "./benchmark_baseline.json"

    # Alert settings
    enable_alerts: bool = True
    alert_cooldown_seconds: int = 300  # 5 minutes between same alert
    min_samples_for_alert: int = 5

    # Reporting
    generate_html_report: bool = True
    generate_json_report: bool = True
    generate_csv_report: bool = True
    report_directory: str = "./benchmark_reports"

    # Advanced settings
    enable_profiling: bool = False
    detailed_logging: bool = False
    statistical_significance: float = 0.95  # 95% confidence level

@dataclass
class BenchmarkResult:
    """Single benchmark test result."""
    test_name: str
    timestamp: datetime
    metric_type: PerformanceMetric
    value: float
    unit: str
    passed: bool
    target_value: Optional[float] = None
    percentile_50: Optional[float] = None
    percentile_95: Optional[float] = None
    percentile_99: Optional[float] = None
    sample_count: int = 1
    std_deviation: Optional[float] = None

@dataclass
class PerformanceAlert:
    """Performance alert information."""
    alert_id: str
    severity: AlertSeverity
    metric_type: PerformanceMetric
    message: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    test_name: str

@dataclass
class BenchmarkResults:
    """Complete benchmark test results."""
    test_id: str
    timestamp: datetime
    duration_seconds: float
    results: List[BenchmarkResult]
    alerts: List[PerformanceAlert]
    pass_rate: float
    performance_score: float

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        passed_tests = sum(1 for r in self.results if r.passed)
        total_tests = len(self.results)

        return {
            'test_id': self.test_id,
            'timestamp': self.timestamp.isoformat(),
            'duration_seconds': self.duration_seconds,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'pass_rate': self.pass_rate,
            'performance_score': self.performance_score,
            'alert_count': len(self.alerts)
        }

class RegressionDetector:
    """Detects performance regressions compared to baseline."""

    def __init__(self, baseline_file: str, threshold_percent: float = 10.0):
        self.baseline_file = Path(baseline_file)
        self.threshold_percent = threshold_percent
        self.baseline_data: Dict[str, Dict[str, float]] = {}
        self.load_baseline()

    def load_baseline(self):
        """Load baseline performance data."""
        try:
            if self.baseline_file.exists():
                with open(self.baseline_file, 'r') as f:
                    self.baseline_data = json.load(f)
                logger.info(f"Loaded baseline data from {self.baseline_file}")
            else:
                logger.info(f"No baseline file found at {self.baseline_file}")
        except Exception as e:
            logger.error(f"Error loading baseline: {e}")
            self.baseline_data = {}

    def save_baseline(self, results: List[BenchmarkResult]):
        """Save current results as new baseline."""
        baseline = {}
        for result in results:
            test_key = f"{result.test_name}_{result.metric_type.value}"
            baseline[test_key] = {
                'value': result.value,
                'timestamp': result.timestamp.isoformat(),
                'target': result.target_value
            }

        try:
            self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.baseline_file, 'w') as f:
                json.dump(baseline, f, indent=2)
            logger.info(f"Saved baseline data to {self.baseline_file}")
        except Exception as e:
            logger.error(f"Error saving baseline: {e}")

    def detect_regressions(self, results: List[BenchmarkResult]) -> List[PerformanceAlert]:
        """Detect performance regressions in test results."""
        alerts = []

        for result in results:
            test_key = f"{result.test_name}_{result.metric_type.value}"

            if test_key in self.baseline_data:
                baseline_value = self.baseline_data[test_key]['value']
                current_value = result.value

                # Calculate percentage change
                if baseline_value != 0:
                    change_percent = ((current_value - baseline_value) / baseline_value) * 100

                    # Determine if this is a regression (depends on metric type)
                    is_regression = self._is_regression(result.metric_type, change_percent)

                    if is_regression and abs(change_percent) >= self.threshold_percent:
                        alert = PerformanceAlert(
                            alert_id=f"regression_{test_key}_{int(time.time())}",
                            severity=AlertSeverity.WARNING if abs(change_percent) < self.threshold_percent * 2 else AlertSeverity.ERROR,
                            metric_type=result.metric_type,
                            message=f"Performance regression detected: {change_percent:+.1f}% change from baseline",
                            current_value=current_value,
                            threshold_value=baseline_value,
                            timestamp=datetime.now(),
                            test_name=result.test_name
                        )
                        alerts.append(alert)

        return alerts

    def _is_regression(self, metric_type: PerformanceMetric, change_percent: float) -> bool:
        """Determine if change percentage represents a regression."""
        # For metrics where lower is better (response time, memory usage, etc.)
        regression_metrics = {
            PerformanceMetric.RESPONSE_TIME,
            PerformanceMetric.MEMORY_USAGE,
            PerformanceMetric.CPU_USAGE,
            PerformanceMetric.ERROR_RATE
        }

        if metric_type in regression_metrics:
            return change_percent > 0  # Increase is bad
        else:
            return change_percent < 0  # Decrease is bad

class AlertManager:
    """Manages performance alerts with cooldown and filtering."""

    def __init__(self, cooldown_seconds: int = 300, min_samples: int = 5):
        self.cooldown_seconds = cooldown_seconds
        self.min_samples = min_samples
        self.alert_history: List[PerformanceAlert] = []
        self.last_alert_times: Dict[str, datetime] = {}

    def add_alert(self, alert: PerformanceAlert) -> bool:
        """
        Add alert if it passes cooldown and minimum samples criteria.

        Args:
            alert: Alert to add

        Returns:
            True if alert was added, False if filtered out
        """
        alert_key = f"{alert.test_name}_{alert.metric_type.value}"

        # Check cooldown
        if alert_key in self.last_alert_times:
            time_since_last = (datetime.now() - self.last_alert_times[alert_key]).total_seconds()
            if time_since_last < self.cooldown_seconds:
                return False  # Still in cooldown period

        # Check if we have enough recent samples
        recent_alerts = [
            a for a in self.alert_history
            if a.test_name == alert.test_name and a.metric_type == alert.metric_type
        ]

        if len(recent_alerts) < self.min_samples:
            self.last_alert_times[alert_key] = datetime.now()
            self.alert_history.append(alert)
            return True

        # Add alert and update cooldown
        self.last_alert_times[alert_key] = datetime.now()
        self.alert_history.append(alert)
        return True

    def get_recent_alerts(self, hours: int = 24) -> List[PerformanceAlert]:
        """Get alerts from the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [a for a in self.alert_history if a.timestamp > cutoff_time]

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics."""
        if not self.alert_history:
            return {}

        recent_alerts = self.get_recent_alerts(24)

        severity_counts = {}
        metric_counts = {}

        for alert in recent_alerts:
            severity_counts[alert.severity.value] = severity_counts.get(alert.severity.value, 0) + 1
            metric_counts[alert.metric_type.value] = metric_counts.get(alert.metric_type.value, 0) + 1

        return {
            'total_alerts_24h': len(recent_alerts),
            'severity_breakdown': severity_counts,
            'metric_breakdown': metric_counts,
            'most_active_metric': max(metric_counts.items(), key=lambda x: x[1])[0] if metric_counts else None
        }

class PerformanceTestSuite:
    """Suite of performance tests for various system components."""

    def __init__(self):
        self.tests: Dict[str, Callable] = {}
        self.register_default_tests()

    def register_test(self, name: str, test_func: Callable):
        """Register a performance test."""
        self.tests[name] = test_func

    def register_default_tests(self):
        """Register default performance tests."""
        self.register_test("computation_cache_lookup", self._test_cache_lookup)
        self.register_test("computation_cache_storage", self._test_cache_storage)
        self.register_test("indicator_calculation_rsi", self._test_rsi_calculation)
        self.register_test("indicator_calculation_macd", self._test_macd_calculation)
        self.register_test("memory_usage_indicator", self._test_memory_usage)
        self.register_test("throughput_calculations", self._test_throughput)

    def run_test(self, test_name: str, **kwargs) -> List[float]:
        """Run a specific performance test."""
        if test_name not in self.tests:
            raise ValueError(f"Unknown test: {test_name}")

        return self.tests[test_name](**kwargs)

    def run_all_tests(self) -> Dict[str, List[float]]:
        """Run all registered tests."""
        results = {}
        for test_name in self.tests:
            try:
                results[test_name] = self.run_test(test_name)
            except Exception as e:
                logger.error(f"Error running test {test_name}: {e}")
                results[test_name] = []

        return results

    def _test_cache_lookup(self, num_operations: int = 1000) -> List[float]:
        """Test cache lookup performance."""
        # Mock test - would integrate with actual cache
        times = []
        for _ in range(num_operations):
            start_time = time.time()
            time.sleep(0.001)  # Simulate 1ms lookup time
            times.append((time.time() - start_time) * 1000)
        return times

    def _test_cache_storage(self, num_operations: int = 100) -> List[float]:
        """Test cache storage performance."""
        # Mock test - would integrate with actual cache
        times = []
        for _ in range(num_operations):
            start_time = time.time()
            time.sleep(0.005)  # Simulate 5ms storage time
            times.append((time.time() - start_time) * 1000)
        return times

    def _test_rsi_calculation(self, data_size: int = 10000, period: int = 14) -> List[float]:
        """Test RSI calculation performance."""
        # Mock test - would integrate with actual calculator
        times = []
        data = np.random.randn(data_size).cumsum() + 100

        for _ in range(10):  # Multiple runs
            start_time = time.time()
            # Simulate RSI calculation
            time.sleep(0.01)  # Simulate 10ms calculation time
            times.append((time.time() - start_time) * 1000)

        return times

    def _test_macd_calculation(self, data_size: int = 10000) -> List[float]:
        """Test MACD calculation performance."""
        # Mock test - would integrate with actual calculator
        times = []
        data = np.random.randn(data_size).cumsum() + 100

        for _ in range(10):  # Multiple runs
            start_time = time.time()
            # Simulate MACD calculation
            time.sleep(0.015)  # Simulate 15ms calculation time
            times.append((time.time() - start_time) * 1000)

        return times

    def _test_memory_usage(self, duration_seconds: int = 30) -> List[float]:
        """Test memory usage over time."""
        # Mock test - would integrate with actual memory monitoring
        times = []
        start_time = time.time()

        while time.time() - start_time < duration_seconds:
            if PSUTIL_AVAILABLE:
                memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            else:
                memory_mb = 100 + np.random.randn() * 10  # Mock data
            times.append(memory_mb)
            time.sleep(1)

        return times

    def _test_throughput(self, duration_seconds: int = 30) -> List[float]:
        """Test system throughput."""
        # Mock test
        operations_completed = 0
        start_time = time.time()

        while time.time() - start_time < duration_seconds:
            # Simulate operations
            time.sleep(0.01)  # 10ms per operation
            operations_completed += 1

        # Calculate throughput as operations per second
        throughput = operations_completed / duration_seconds
        return [throughput]

class PerformanceBenchmark:
    """
    Comprehensive performance benchmarking system.

    Features:
    - Automated performance testing
    - Regression detection
    - Performance alerts
    - Detailed reporting
    - Statistical analysis
    - Baseline comparison
    """

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.test_suite = PerformanceTestSuite()
        self.regression_detector = RegressionDetector(
            config.baseline_comparison_file,
            config.regression_threshold_percent
        )
        self.alert_manager = AlertManager(
            config.alert_cooldown_seconds,
            config.min_samples_for_alert
        )
        self.results_history: List[BenchmarkResults] = []

        # Ensure report directory exists
        Path(self.config.report_directory).mkdir(parents=True, exist_ok=True)

    def run_comprehensive_benchmark(
        self,
        save_baseline: bool = False
    ) -> BenchmarkResults:
        """
        Run comprehensive performance benchmark.

        Args:
            save_baseline: Whether to save results as new baseline

        Returns:
            Complete benchmark results
        """
        test_id = f"benchmark_{int(time.time())}"
        start_time = datetime.now()

        logger.info(f"Starting comprehensive benchmark: {test_id}")

        # Warmup phase
        if self.config.warmup_duration_seconds > 0:
            logger.info("Running warmup phase...")
            self._run_warmup()

        # Run all tests
        logger.info("Running performance tests...")
        test_results = self.test_suite.run_all_tests()

        # Process results into BenchmarkResult objects
        benchmark_results = []
        for test_name, times in test_results.items():
            if not times:
                continue

            # Determine metric type based on test name
            metric_type = self._infer_metric_type(test_name)
            target_value = self._get_target_value(metric_type)

            # Calculate statistics
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0
            percentile_95 = np.percentile(times, 95) if times else 0
            percentile_99 = np.percentile(times, 99) if times else 0

            # Determine if test passed
            passed = self._evaluate_test_result(metric_type, avg_time, target_value)

            # Determine unit
            unit = self._get_unit(metric_type)

            result = BenchmarkResult(
                test_name=test_name,
                timestamp=datetime.now(),
                metric_type=metric_type,
                value=avg_time,
                unit=unit,
                passed=passed,
                target_value=target_value,
                percentile_50=median_time,
                percentile_95=percentile_95,
                percentile_99=percentile_99,
                sample_count=len(times),
                std_deviation=std_dev
            )
            benchmark_results.append(result)

        # Detect regressions
        alerts = []
        if self.config.enable_regression_detection:
            regression_alerts = self.regression_detector.detect_regressions(benchmark_results)
            for alert in regression_alerts:
                if self.alert_manager.add_alert(alert):
                    alerts.append(alert)

        # Calculate overall metrics
        duration = (datetime.now() - start_time).total_seconds()
        passed_tests = sum(1 for r in benchmark_results if r.passed)
        pass_rate = (passed_tests / len(benchmark_results)) * 100 if benchmark_results else 0
        performance_score = self._calculate_performance_score(benchmark_results)

        # Create results object
        results = BenchmarkResults(
            test_id=test_id,
            timestamp=start_time,
            duration_seconds=duration,
            results=benchmark_results,
            alerts=alerts,
            pass_rate=pass_rate,
            performance_score=performance_score
        )

        # Save results
        self.results_history.append(results)
        self._save_results(results)

        # Save as baseline if requested
        if save_baseline:
            self.regression_detector.save_baseline(benchmark_results)

        logger.info(f"Benchmark completed: {test_id}")
        logger.info(f"Pass rate: {pass_rate:.1f}%, Performance score: {performance_score:.1f}")

        return results

    def run_quick_benchmark(self) -> BenchmarkResults:
        """Run a quick benchmark with essential tests only."""
        # Create a reduced config for quick benchmark
        quick_config = BenchmarkConfig(
            test_duration_seconds=60,  # 1 minute
            warmup_duration_seconds=5,  # 5 seconds
            concurrent_users=1,
            enable_regression_detection=True,
            generate_html_report=False,
            detailed_logging=False
        )

        # Temporarily use quick config
        original_config = self.config
        self.config = quick_config

        try:
            results = self.run_comprehensive_benchmark()
            return results
        finally:
            self.config = original_config

    def _run_warmup(self):
        """Run warmup phase to stabilize system performance."""
        # Simple warmup - run a few quick calculations
        for _ in range(5):
            self.test_suite.run_test("computation_cache_lookup", num_operations=10)

    def _infer_metric_type(self, test_name: str) -> PerformanceMetric:
        """Infer metric type from test name."""
        if "cache" in test_name and "lookup" in test_name:
            return PerformanceMetric.RESPONSE_TIME
        elif "cache" in test_name and "storage" in test_name:
            return PerformanceMetric.RESPONSE_TIME
        elif "memory" in test_name:
            return PerformanceMetric.MEMORY_USAGE
        elif "throughput" in test_name:
            return PerformanceMetric.THROUGHPUT
        else:
            return PerformanceMetric.RESPONSE_TIME

    def _get_target_value(self, metric_type: PerformanceMetric) -> Optional[float]:
        """Get target value for metric type."""
        targets = {
            PerformanceMetric.RESPONSE_TIME: self.config.target_response_time_ms,
            PerformanceMetric.MEMORY_USAGE: self.config.target_memory_usage_mb,
            PerformanceMetric.THROUGHPUT: self.config.target_throughput,
            PerformanceMetric.CACHE_HIT_RATE: self.config.target_cache_hit_rate,
        }
        return targets.get(metric_type)

    def _get_unit(self, metric_type: PerformanceMetric) -> str:
        """Get unit for metric type."""
        units = {
            PerformanceMetric.RESPONSE_TIME: "ms",
            PerformanceMetric.MEMORY_USAGE: "MB",
            PerformanceMetric.THROUGHPUT: "req/sec",
            PerformanceMetric.CACHE_HIT_RATE: "%",
            PerformanceMetric.CPU_USAGE: "%",
            PerformanceMetric.ERROR_RATE: "%"
        }
        return units.get(metric_type, "")

    def _evaluate_test_result(
        self,
        metric_type: PerformanceMetric,
        value: float,
        target: Optional[float]
    ) -> bool:
        """Evaluate if test result passes performance target."""
        if target is None:
            return True  # No target means always pass

        # For metrics where lower is better
        lower_is_better = {
            PerformanceMetric.RESPONSE_TIME,
            PerformanceMetric.MEMORY_USAGE,
            PerformanceMetric.CPU_USAGE,
            PerformanceMetric.ERROR_RATE
        }

        if metric_type in lower_is_better:
            return value <= target
        else:
            return value >= target

    def _calculate_performance_score(self, results: List[BenchmarkResult]) -> float:
        """Calculate overall performance score (0-100)."""
        if not results:
            return 0.0

        total_score = 0.0
        for result in results:
            if result.target_value is None:
                continue

            # Calculate individual score based on how close to target
            if self._evaluate_test_result(result.metric_type, result.value, result.target_value):
                # Passed test - score based on how well it passed
                ratio = result.value / result.target_value
                if result.metric_type in {
                    PerformanceMetric.RESPONSE_TIME,
                    PerformanceMetric.MEMORY_USAGE,
                    PerformanceMetric.CPU_USAGE,
                    PerformanceMetric.ERROR_RATE
                }:
                    # Lower is better - score better if significantly lower than target
                    score = min(100, 100 * (result.target_value / result.value))
                else:
                    # Higher is better - score based on how much higher than target
                    score = min(100, 100 * (result.value / result.target_value))
            else:
                # Failed test - score based on how badly it failed
                ratio = result.value / result.target_value
                if result.metric_type in {
                    PerformanceMetric.RESPONSE_TIME,
                    PerformanceMetric.MEMORY_USAGE,
                    PerformanceMetric.CPU_USAGE,
                    PerformanceMetric.ERROR_RATE
                }:
                    # Lower is better - failed if higher than target
                    score = max(0, 100 - (ratio - 1) * 50)
                else:
                    # Higher is better - failed if lower than target
                    score = max(0, 100 * ratio)

            total_score += score

        return total_score / len(results)

    def _save_results(self, results: BenchmarkResults):
        """Save benchmark results to files."""
        timestamp_str = results.timestamp.strftime("%Y%m%d_%H%M%S")

        # Save JSON report
        if self.config.generate_json_report:
            json_file = Path(self.config.report_directory) / f"benchmark_results_{timestamp_str}.json"
            with open(json_file, 'w') as f:
                json.dump({
                    'summary': results.get_summary(),
                    'results': [asdict(r) for r in results.results],
                    'alerts': [asdict(a) for a in results.alerts]
                }, f, indent=2, default=str)

        # Save CSV report
        if self.config.generate_csv_report and PANDAS_AVAILABLE:
            csv_file = Path(self.config.report_directory) / f"benchmark_results_{timestamp_str}.csv"
            results_data = []
            for result in results.results:
                results_data.append({
                    'test_name': result.test_name,
                    'metric_type': result.metric_type.value,
                    'value': result.value,
                    'unit': result.unit,
                    'passed': result.passed,
                    'target_value': result.target_value,
                    'percentile_95': result.percentile_95,
                    'sample_count': result.sample_count
                })

            df = pd.DataFrame(results_data)
            df.to_csv(csv_file, index=False)

        # Save HTML report (simplified version)
        if self.config.generate_html_report:
            html_file = Path(self.config.report_directory) / f"benchmark_results_{timestamp_str}.html"
            self._generate_html_report(results, html_file)

    def _generate_html_report(self, results: BenchmarkResults, file_path: Path):
        """Generate HTML performance report."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Performance Benchmark Report - {results.test_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; }}
                .results-table {{ width: 100%; border-collapse: collapse; }}
                .results-table th, .results-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .results-table th {{ background-color: #f2f2f2; }}
                .pass {{ color: green; }}
                .fail {{ color: red; }}
                .alert {{ background-color: #ffebee; padding: 10px; margin: 10px 0; border-left: 4px solid #f44336; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Performance Benchmark Report</h1>
                <p><strong>Test ID:</strong> {results.test_id}</p>
                <p><strong>Timestamp:</strong> {results.timestamp}</p>
                <p><strong>Duration:</strong> {results.duration_seconds:.1f} seconds</p>
            </div>

            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Pass Rate:</strong> {results.pass_rate:.1f}%</p>
                <p><strong>Performance Score:</strong> {results.performance_score:.1f}/100</p>
                <p><strong>Total Tests:</strong> {len(results.results)}</p>
                <p><strong>Alerts:</strong> {len(results.alerts)}</p>
            </div>

            <h2>Test Results</h2>
            <table class="results-table">
                <tr>
                    <th>Test Name</th>
                    <th>Metric</th>
                    <th>Value</th>
                    <th>Target</th>
                    <th>Status</th>
                    <th>95th Percentile</th>
                    <th>Samples</th>
                </tr>
        """

        for result in results.results:
            status_class = "pass" if result.passed else "fail"
            status_text = "PASS" if result.passed else "FAIL"

            html_content += f"""
                <tr>
                    <td>{result.test_name}</td>
                    <td>{result.metric_type.value}</td>
                    <td>{result.value:.2f} {result.unit}</td>
                    <td>{result.target_value or 'N/A'} {result.unit if result.target_value else ''}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{result.percentile_95:.2f} {result.unit}</td>
                    <td>{result.sample_count}</td>
                </tr>
            """

        html_content += "</table>"

        if results.alerts:
            html_content += "<h2>Alerts</h2>"
            for alert in results.alerts:
                html_content += f"""
                <div class="alert">
                    <strong>[{alert.severity.value.upper()}]</strong> {alert.message}<br>
                    <small>Test: {alert.test_name} | Current: {alert.current_value:.2f} | Threshold: {alert.threshold_value:.2f}</small>
                </div>
                """

        html_content += """
        </body>
        </html>
        """

        with open(file_path, 'w') as f:
            f.write(html_content)

    def get_performance_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get performance trends over time."""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_results = [
            r for r in self.results_history
            if r.timestamp > cutoff_date
        ]

        if not recent_results:
            return {}

        # Calculate trends for each test
        trends = {}
        for result in recent_results:
            for test_result in result.results:
                test_name = test_result.test_name
                if test_name not in trends:
                    trends[test_name] = []

                trends[test_name].append({
                    'timestamp': result.timestamp,
                    'value': test_result.value,
                    'passed': test_result.passed
                })

        # Calculate trend statistics
        trend_analysis = {}
        for test_name, values in trends.items():
            if len(values) < 2:
                continue

            # Simple linear regression for trend
            x = np.arange(len(values))
            y = np.array([v['value'] for v in values])
            slope = np.polyfit(x, y, 1)[0]

            # Performance trend
            performance_trend = "stable"
            if abs(slope) > 0.1:
                performance_trend = "improving" if slope < 0 else "degrading"

            trend_analysis[test_name] = {
                'trend': performance_trend,
                'slope': slope,
                'data_points': len(values),
                'latest_value': values[-1]['value'],
                'earliest_value': values[0]['value']
            }

        return trend_analysis

    def get_performance_recommendations(self) -> List[str]:
        """Get performance optimization recommendations."""
        recommendations = []

        if not self.results_history:
            return ["No benchmark data available. Run benchmarks to get recommendations."]

        latest_results = self.results_history[-1]

        # Check failed tests
        failed_tests = [r for r in latest_results.results if not r.passed]
        if failed_tests:
            recommendations.append(f"Address {len(failed_tests)} failing performance tests.")

        # Check alerts
        if latest_results.alerts:
            recommendations.append(f"Review {len(latest_results.alerts)} performance alerts.")

        # Check overall performance score
        if latest_results.performance_score < 70:
            recommendations.append("Overall performance score is low. Consider system optimization.")
        elif latest_results.performance_score < 85:
            recommendations.append("Performance could be improved with targeted optimizations.")

        # Check trends
        trends = self.get_performance_trends()
        degrading_tests = [name for name, trend in trends.items() if trend['trend'] == 'degrading']
        if degrading_tests:
            recommendations.append(f"Performance degrading in {len(degrading_tests)} tests. Investigate cause.")

        # Check consistency
        if len(self.results_history) >= 3:
            recent_scores = [r.performance_score for r in self.results_history[-3:]]
            if max(recent_scores) - min(recent_scores) > 20:
                recommendations.append("Performance is inconsistent. Check for external factors affecting performance.")

        return recommendations

# Utility functions
def run_comprehensive_benchmark(config: Optional[BenchmarkConfig] = None) -> BenchmarkResults:
    """Run comprehensive performance benchmark with default or custom config."""
    if config is None:
        config = BenchmarkConfig()

    benchmark = PerformanceBenchmark(config)
    return benchmark.run_comprehensive_benchmark()

def create_benchmark_with_config(**kwargs) -> PerformanceBenchmark:
    """Create benchmark with custom configuration."""
    config = BenchmarkConfig(**kwargs)
    return PerformanceBenchmark(config)
# -*- coding: utf-8 -*-
"""
Testing utilities for comprehensive test execution.
"""

import asyncio
import json
import logging
import os
import statistics
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from unittest.mock import MagicMock

import aiofiles
import aiohttp
import psutil
import pytest

from .core import TestResult


class TestLogger:
    """Enhanced test logger with structured logging."""

    def __init__(self, log_level: str = "INFO"):
        self.logger = logging.getLogger("test_framework")
        self.logger.setLevel(getattr(logging, log_level.upper()))

        # Create formatters
        detailed_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
        )
        simple_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)

        # File handler
        log_file = (
            Path("test_results")
            / f"test_log_{datetime.now().strftime('%Y % m % d_ % H % M % S')}.log"
        )
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)

    def info(self, message: str, extra: Dict[str, Any] = None):
        """Log info message with optional structured data."""
        if extra:
            self.logger.info(f"{message} | Extra: {json.dumps(extra)}")
        else:
            self.logger.info(message)

    def warning(self, message: str, extra: Dict[str, Any] = None):
        """Log warning message with optional structured data."""
        if extra:
            self.logger.warning(f"{message} | Extra: {json.dumps(extra)}")
        else:
            self.logger.warning(message)

    def error(self, message: str, extra: Dict[str, Any] = None):
        """Log error message with optional structured data."""
        if extra:
            self.logger.error(f"{message} | Extra: {json.dumps(extra)}")
        else:
            self.logger.error(message)

    def debug(self, message: str, extra: Dict[str, Any] = None):
        """Log debug message with optional structured data."""
        if extra:
            self.logger.debug(f"{message} | Extra: {json.dumps(extra)}")
        else:
            self.logger.debug(message)


class MetricsCollector:
    """Collects performance and system metrics during testing."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics = {}
        self.thresholds = {}
        self.enabled = True
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.start_time = None

    def configure(self, enabled: bool = True, thresholds: Dict[str, float] = None):
        """Configure metrics collection."""
        self.enabled = enabled
        self.thresholds = thresholds or {}

    def start_monitoring(self, test_id: str):
        """Start monitoring for a test."""
        if not self.enabled:
            return

        self.start_time = time.time()
        self.metrics[test_id] = {
            "start_time": self.start_time,
            "cpu_samples": [],
            "memory_samples": [],
            "network_samples": [],
        }

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_system_resources, args=(test_id,), daemon=True
        )
        self.monitor_thread.start()

    def stop_monitoring(self, test_id: str) -> Dict[str, Any]:
        """Stop monitoring and return metrics."""
        if not self.enabled:
            return {}

        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)

        end_time = time.time()
        test_metrics = self.metrics.get(test_id, {})

        if test_metrics:
            test_metrics.update(
                {
                    "end_time": end_time,
                    "duration": end_time - test_metrics["start_time"],
                }
            )

            # Calculate averages
            if test_metrics["cpu_samples"]:
                test_metrics["avg_cpu"] = statistics.mean(test_metrics["cpu_samples"])
                test_metrics["max_cpu"] = max(test_metrics["cpu_samples"])

            if test_metrics["memory_samples"]:
                test_metrics["avg_memory"] = statistics.mean(
                    test_metrics["memory_samples"]
                )
                test_metrics["max_memory"] = max(test_metrics["memory_samples"])

        return test_metrics

    def _monitor_system_resources(self, test_id: str):
        """Monitor system resources in background thread."""
        process = psutil.Process()

        while self.monitoring:
            try:
                # CPU usage
                cpu_percent = process.cpu_percent()
                self.metrics[test_id]["cpu_samples"].append(cpu_percent)

                # Memory usage
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                self.metrics[test_id]["memory_samples"].append(memory_mb)

                # Network I / O
                network_io = psutil.net_io_counters()
                self.metrics[test_id]["network_samples"].append(
                    {
                        "bytes_sent": network_io.bytes_sent,
                        "bytes_recv": network_io.bytes_recv,
                    }
                )

                time.sleep(0.1)  # Sample every 100ms

            except Exception as e:
                self.logger.warning(f"Error monitoring system resources: {e}")
                break

    def get_test_metrics(self, test_id: str) -> Dict[str, Any]:
        """Get metrics for a specific test."""
        return self.metrics.get(test_id, {})

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total": psutil.virtual_memory().total / 1024 / 1024 / 1024,  # GB
            "memory_available": psutil.virtual_memory().available
            / 1024
            / 1024
            / 1024,  # GB
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent,
            "boot_time": psutil.boot_time(),
        }

    def check_thresholds(self, test_id: str) -> List[str]:
        """Check if metrics exceed thresholds."""
        violations = []
        test_metrics = self.get_test_metrics(test_id)

        for metric, threshold in self.thresholds.items():
            if metric in test_metrics:
                value = test_metrics[metric]
                if value > threshold:
                    violations.append(f"{metric}: {value:.2f} > {threshold}")

        return violations


class TestAssertions:
    """Enhanced test assertions for quantitative trading system."""

    @staticmethod
    def assert_valid_market_data(data: Union[Dict, List], symbol: str = None):
        """Assert that market data is valid."""
        if isinstance(data, list):
            # List of OHLCV records
            assert len(data) > 0, "Market data list is empty"

            for record in data:
                TestAssertions._assert_valid_ohlcv_record(record, symbol)
        elif isinstance(data, dict):
            # Single OHLCV record
            TestAssertions._assert_valid_ohlcv_record(data, symbol)
        else:
            raise AssertionError(f"Invalid market data type: {type(data)}")

    @staticmethod
    def _assert_valid_ohlcv_record(record: Dict, symbol: str = None):
        """Assert that a single OHLCV record is valid."""
        required_fields = ["timestamp", "open", "high", "low", "close", "volume"]
        for field in required_fields:
            assert field in record, f"Missing required field: {field}"

        # Validate OHLC relationships
        assert record["high"] >= record["low"], "High price must be >= low price"
        assert record["high"] >= max(
            record["open"], record["close"]
        ), "High price must be >= open and close"
        assert record["low"] <= min(
            record["open"], record["close"]
        ), "Low price must be <= open and close"

        # Validate values are positive
        assert record["open"] > 0, "Open price must be positive"
        assert record["high"] > 0, "High price must be positive"
        assert record["low"] > 0, "Low price must be positive"
        assert record["close"] > 0, "Close price must be positive"
        assert record["volume"] >= 0, "Volume must be non - negative"

        # Validate timestamp
        if isinstance(record["timestamp"], str):
            try:
                datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
            except ValueError:
                raise AssertionError(f"Invalid timestamp format: {record['timestamp']}")

        # Validate symbol if provided
        if symbol:
            assert (
                record.get("symbol") == symbol
            ), f"Symbol mismatch: expected {symbol}, got {record.get('symbol')}"

    @staticmethod
    def assert_valid_trading_signal(signal: Dict):
        """Assert that a trading signal is valid."""
        required_fields = ["symbol", "signal", "confidence", "timestamp"]
        for field in required_fields:
            assert field in signal, f"Missing required field: {field}"

        # Validate signal type
        valid_signals = ["BUY", "SELL", "HOLD"]
        assert signal["signal"] in valid_signals, f"Invalid signal: {signal['signal']}"

        # Validate confidence
        assert (
            0 <= signal["confidence"] <= 1
        ), f"Confidence must be between 0 and 1: {signal['confidence']}"

        # Validate timestamp
        try:
            datetime.fromisoformat(signal["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            raise AssertionError(f"Invalid timestamp format: {signal['timestamp']}")

    @staticmethod
    def assert_valid_portfolio(portfolio: Dict):
        """Assert that portfolio data is valid."""
        required_fields = ["portfolio_id", "total_value", "positions"]
        for field in required_fields:
            assert field in portfolio, f"Missing required field: {field}"

        assert portfolio["total_value"] > 0, "Total portfolio value must be positive"
        assert isinstance(portfolio["positions"], list), "Positions must be a list"

        total_position_value = 0
        for position in portfolio["positions"]:
            TestAssertions._assert_valid_position(position)
            total_position_value += position.get("market_value", 0)

        # Allow for small rounding differences
        assert (
            abs(total_position_value - portfolio["total_value"])
            < portfolio["total_value"] * 0.01
        ), f"Position values sum to {total_position_value}, but portfolio value is {portfolio['total_value']}"

    @staticmethod
    def _assert_valid_position(position: Dict):
        """Assert that a position is valid."""
        required_fields = [
            "symbol",
            "shares",
            "avg_price",
            "current_price",
            "market_value",
        ]
        for field in required_fields:
            assert field in position, f"Missing required position field: {field}"

        assert position["shares"] > 0, "Shares must be positive"
        assert position["avg_price"] > 0, "Average price must be positive"
        assert position["current_price"] > 0, "Current price must be positive"
        assert position["market_value"] > 0, "Market value must be positive"

        # Check market value calculation
        expected_market_value = position["shares"] * position["current_price"]
        assert (
            abs(position["market_value"] - expected_market_value)
            < expected_market_value * 0.01
        ), f"Market value calculation error: expected {expected_market_value}, got {position['market_value']}"

    @staticmethod
    def assert_valid_risk_metrics(risk_metrics: Dict):
        """Assert that risk metrics are valid."""
        required_fields = ["portfolio_value", "var_95", "var_99", "max_drawdown"]
        for field in required_fields:
            assert field in risk_metrics, f"Missing required risk field: {field}"

        assert risk_metrics["portfolio_value"] > 0, "Portfolio value must be positive"

        # Validate VaR metrics
        assert isinstance(risk_metrics["var_95"], dict), "VaR 95% must be a dictionary"
        assert isinstance(risk_metrics["var_99"], dict), "VaR 99% must be a dictionary"

        assert (
            risk_metrics["var_99"]["value"] > risk_metrics["var_95"]["value"]
        ), "VaR 99% should be higher than VaR 95%"

        # Validate max drawdown
        assert (
            risk_metrics["max_drawdown"]["value"] > 0
        ), "Max drawdown value must be positive"
        assert (
            0 <= risk_metrics["max_drawdown"]["percentage"] <= 1
        ), "Max drawdown percentage must be between 0 and 1"

    @staticmethod
    def assert_performance_within_threshold(
        actual_performance: Dict[str, float],
        expected_performance: Dict[str, float],
        tolerance: float = 0.1,
    ):
        """Assert that performance metrics are within tolerance."""
        for metric, expected_value in expected_performance.items():
            assert metric in actual_performance, f"Missing performance metric: {metric}"
            actual_value = actual_performance[metric]

            if expected_value == 0:
                assert (
                    abs(actual_value) < tolerance
                ), f"Performance metric {metric} should be close to 0, got {actual_value}"
            else:
                relative_error = abs(actual_value - expected_value) / abs(
                    expected_value
                )
                assert (
                    relative_error <= tolerance
                ), f"Performance metric {metric} deviates by {relative_error:.2%}, expected {expected_value}, got {actual_value}"

    @staticmethod
    def assert_api_response(response: Dict, status_code: int = 200):
        """Assert that API response is valid."""
        assert "status_code" in response, "Missing status_code in response"
        assert (
            response["status_code"] == status_code
        ), f"Expected status {status_code}, got {response['status_code']}"

        if status_code == 200:
            assert (
                "data" in response or "result" in response
            ), "Success response should contain data"

    @staticmethod
    def assert_time_elapsed(start_time: datetime, max_seconds: float):
        """Assert that time elapsed is within limits."""
        elapsed = (datetime.now() - start_time).total_seconds()
        assert (
            elapsed <= max_seconds
        ), f"Operation took {elapsed:.2f}s, max allowed: {max_seconds}s"


class TestHelpers:
    """Helper utilities for testing."""

    @staticmethod
    async def wait_for_condition(
        condition: Callable[[], bool],
        timeout: float = 30.0,
        interval: float = 0.5,
        message: str = "Condition not met",
    ):
        """Wait for a condition to be true."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition():
                return True
            await asyncio.sleep(interval)
        raise TimeoutError(f"{message} after {timeout}s")

    @staticmethod
    async def retry_operation(
        operation: Callable,
        max_attempts: int = 3,
        delay: float = 1.0,
        exceptions: tuple = (Exception,),
    ):
        """Retry an operation with exponential backoff."""
        for attempt in range(max_attempts):
            try:
                return await operation()
            except exceptions as e:
                if attempt == max_attempts - 1:
                    raise
                await asyncio.sleep(delay * (2 ** attempt))

    @staticmethod
    def generate_test_id() -> str:
        """Generate unique test ID."""
        return f"test_{datetime.now().strftime('%Y % m % d_ % H % M % S')}_{uuid.uuid4().hex[:8]}"

    @staticmethod
    async def measure_execution_time(operation: Callable) -> tuple:
        """Measure execution time of an operation."""
        start_time = time.time()
        try:
            result = await operation()
            duration = time.time() - start_time
            return result, duration
        except Exception as e:
            duration = time.time() - start_time
            raise e

    @staticmethod
    def compare_dataframes(
        df1: pd.DataFrame, df2: pd.DataFrame, tolerance: float = 1e-6
    ):
        """Compare two DataFrames for equality within tolerance."""
        assert (
            df1.shape == df2.shape
        ), f"DataFrame shapes differ: {df1.shape} vs {df2.shape}"
        assert list(df1.columns) == list(df2.columns), "DataFrame columns differ"

        for col in df1.columns:
            if df1[col].dtype in ["float64", "float32"]:
                assert np.allclose(
                    df1[col], df2[col], atol=tolerance
                ), f"Column {col} values differ"
            else:
                assert df1[col].equals(df2[col]), f"Column {col} values differ"

    @staticmethod
    def create_test_file(content: str, suffix: str = ".tmp") -> Path:
        """Create temporary test file."""
        temp_file = Path(
            f"test_file_{datetime.now().strftime('%Y % m % d_ % H % M % S')}_{uuid.uuid4().hex[:8]}{suffix}"
        )
        temp_file.write_text(content)
        return temp_file

    @staticmethod
    def cleanup_test_files(pattern: str = "test_file_*"):
        """Cleanup test files matching pattern."""
        import glob

        files = glob.glob(pattern)
        for file in files:
            try:
                os.remove(file)
            except Exception as e:
                logging.warning(f"Failed to remove test file {file}: {e}")


class PerformanceMonitor:
    """Monitor performance during test execution."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.measurements: List[Dict[str, Any]] = []

    def start_measurement(self, test_name: str):
        """Start performance measurement."""
        return {
            "test_name": test_name,
            "start_time": time.time(),
            "start_memory": psutil.Process().memory_info().rss,
            "start_cpu": psutil.Process().cpu_percent(),
        }

    def end_measurement(self, measurement: Dict[str, Any]) -> Dict[str, Any]:
        """End performance measurement and return results."""
        end_time = time.time()
        process = psutil.Process()

        measurement.update(
            {
                "end_time": end_time,
                "duration": end_time - measurement["start_time"],
                "end_memory": process.memory_info().rss,
                "end_cpu": process.cpu_percent(),
                "memory_delta": process.memory_info().rss - measurement["start_memory"],
            }
        )

        self.measurements.append(measurement)
        return measurement

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.measurements:
            return {}

        durations = [m["duration"] for m in self.measurements]
        memory_deltas = [m["memory_delta"] for m in self.measurements]

        return {
            "total_tests": len(self.measurements),
            "total_duration": sum(durations),
            "avg_duration": statistics.mean(durations),
            "max_duration": max(durations),
            "min_duration": min(durations),
            "total_memory_delta": sum(memory_deltas),
            "avg_memory_delta": statistics.mean(memory_deltas),
            "max_memory_delta": max(memory_deltas),
            "measurements": self.measurements,
        }


class SecurityTester:
    """Security testing utilities."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def test_sql_injection(self, url: str, params: Dict[str, Any]) -> List[str]:
        """Test for SQL injection vulnerabilities."""
        vulnerabilities = []

        # SQL injection payloads
        payloads = [
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' OR '1'='1' /*",
            "admin'--",
            "admin'/*",
            "' OR 'x'='x",
            "1' OR '1'='1' --",
            "'; EXEC xp_cmdshell('dir'); --",
        ]

        for param_name, param_value in params.items():
            if isinstance(param_value, str):
                for payload in payloads:
                    test_params = params.copy()
                    test_params[param_name] = payload

                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url, params=test_params) as response:
                                if response.status == 200:
                                    text = await response.text()
                                    # Check for SQL error messages
                                    sql_errors = [
                                        "SQL syntax",
                                        "mysql_fetch",
                                        "ORA-",
                                        "Microsoft OLE DB Provider",
                                        "ODBC Microsoft Access Driver",
                                        "ODBC SQL Server Driver",
                                        "Java.sql.SQLException",
                                    ]

                                    if any(error in text for error in sql_errors):
                                        vulnerabilities.append(
                                            f"SQL injection detected in parameter {param_name} with payload: {payload}"
                                        )
                    except Exception as e:
                        self.logger.warning(f"Error testing SQL injection: {e}")

        return vulnerabilities

    async def test_xss(self, url: str, params: Dict[str, Any]) -> List[str]:
        """Test for XSS vulnerabilities."""
        vulnerabilities = []

        # XSS payloads
        payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//",
            "<svg onload=alert('XSS')>",
            "\"><script>alert('XSS')</script>",
            "'><script>alert('XSS')</script>",
        ]

        for param_name, param_value in params.items():
            if isinstance(param_value, str):
                for payload in payloads:
                    test_params = params.copy()
                    test_params[param_name] = payload

                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url, params=test_params) as response:
                                if response.status == 200:
                                    text = await response.text()
                                    if payload in text:
                                        vulnerabilities.append(
                                            f"XSS vulnerability detected in parameter {param_name} with payload: {payload}"
                                        )
                    except Exception as e:
                        self.logger.warning(f"Error testing XSS: {e}")

        return vulnerabilities

    def test_authentication_bypass(self, auth_config: Dict[str, Any]) -> List[str]:
        """Test for authentication bypass vulnerabilities."""
        vulnerabilities = []

        # Test for weak passwords
        weak_passwords = ["password", "123456", "admin", "test", "guest"]
        if "users" in auth_config:
            for user in auth_config["users"]:
                if user.get("password") in weak_passwords:
                    vulnerabilities.append(
                        f"Weak password for user {user.get('username')}"
                    )

        # Test for missing authentication
        if not auth_config.get("authentication_required", True):
            vulnerabilities.append("Authentication is not required")

        # Test for hardcoded credentials
        if "api_key" in auth_config and len(auth_config["api_key"]) < 32:
            vulnerabilities.append("API key appears to be weak or hardcoded")

        return vulnerabilities

    async def test_rate_limiting(
        self, url: str, max_requests: int = 100
    ) -> Dict[str, Any]:
        """Test rate limiting functionality."""
        results = {
            "requests_sent": 0,
            "responses_200": 0,
            "responses_429": 0,
            "responses_other": 0,
            "rate_limit_detected": False,
        }

        try:
            async with aiohttp.ClientSession() as session:
                for i in range(max_requests):
                    results["requests_sent"] += 1
                    async with session.get(url) as response:
                        if response.status == 200:
                            results["responses_200"] += 1
                        elif response.status == 429:
                            results["responses_429"] += 1
                            results["rate_limit_detected"] = True
                            break
                        else:
                            results["responses_other"] += 1

        except Exception as e:
            self.logger.warning(f"Error testing rate limiting: {e}")

        return results


class CoverageAnalyzer:
    """Analyze test coverage."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def analyze_coverage(
        self, source_paths: List[str], test_paths: List[str]
    ) -> Dict[str, Any]:
        """Analyze code coverage."""
        # This would integrate with coverage.py or similar tool
        # For now, return placeholder data
        return {
            "total_lines": 10000,
            "covered_lines": 8500,
            "coverage_percentage": 85.0,
            "missing_lines": 1500,
            "source_files": [],
            "test_files": [],
        }

    def generate_coverage_report(
        self, coverage_data: Dict[str, Any], output_path: Path
    ):
        """Generate HTML coverage report."""
        # This would generate a detailed HTML coverage report
        report_file = output_path / "coverage_report.html"

        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Coverage Report</title>
            <style>
                body {{ font - family: Arial, sans - serif; margin: 20px; }}
                .summary {{ background: #f5f5f5; padding: 20px; border - radius: 5px; }}
                .coverage - high {{ color: green; }}
                .coverage - medium {{ color: orange; }}
                .coverage - low {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>Test Coverage Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p>Total Lines: {coverage_data['total_lines']}</p>
                <p>Covered Lines: {coverage_data['covered_lines']}</p>
                <p class="coverage-{self._get_coverage_level(coverage_data['coverage_percentage'])}">
                    Coverage: {coverage_data['coverage_percentage']:.1f}%
                </p>
            </div>
        </body>
        </html>
        """

        with open(report_file, "w") as f:
            f.write(html_content)

    def _get_coverage_level(self, percentage: float) -> str:
        """Get coverage level classification."""
        if percentage >= 80:
            return "high"
        elif percentage >= 60:
            return "medium"
        else:
            return "low"

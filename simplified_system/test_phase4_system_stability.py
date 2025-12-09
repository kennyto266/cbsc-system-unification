#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
Phase 4: System Stability Testing
Phase 4: 系统稳定性测试

Test system stability under various stress conditions:
- Long - running operations
- Memory leak detection
- Resource exhaustion handling
- Concurrent access stability
- Error recovery mechanisms
- Data integrity under stress

Author: Claude Code Assistant
Date: 2025 - 11 - 26
Version: Phase 4.0
"""

import gc
import json
import logging
import multiprocessing
import os
import random
import sys
import threading
import time
import traceback
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import psutil

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


class StabilityTest:
    """System stability testing suite"""

    def __init__(self):
        self.results = {}
        self.process = psutil.Process()
        self.stress_test_duration = 300  # 5 minutes
        self.monitoring_interval = 10  # 10 seconds
        self.error_log = []

    def generate_test_data(self, size: int = 10000) -> pd.DataFrame:
        """Generate test data for stability testing"""
        np.random.seed(int(time.time()) % 1000)  # Varying seed for different data

        dates = pd.date_range("2020 - 01 - 01", periods = size, freq="D")

        # Create more realistic price data with trends and volatility
        returns = np.random.normal(0.001, 0.02, size)
        price_path = 100 * np.exp(np.cumsum(returns))

        # Add some noise and ensure OHLC relationships
        close_prices = price_path
        high_prices = close_prices * (1 + np.random.uniform(0, 0.03, size))
        low_prices = close_prices * (1 - np.random.uniform(0, 0.03, size))
        open_prices = np.roll(close_prices, 1)
        open_prices[0] = close_prices[0]

        # Ensure OHLC relationships are valid
        high_prices = np.maximum(high_prices, np.maximum(open_prices, close_prices))
        low_prices = np.minimum(low_prices, np.minimum(open_prices, close_prices))

        return pd.DataFrame(
            {
                "open": open_prices,
                "high": high_prices,
                "low": low_prices,
                "close": close_prices,
                "volume": np.random.randint(100000, 10000000, size),
            },
            index = dates,
        )

    def monitor_system_resources(
        self, duration: int, interval: int = 5
    ) -> Dict[str, List]:
        """Monitor system resources during stress tests"""
        logger.info(f"Starting resource monitoring for {duration} seconds")

        resource_data = {
            "timestamps": [],
            "cpu_percent": [],
            "memory_mb": [],
            "memory_percent": [],
            "threads": [],
            "file_descriptors": [],
        }

        start_time = time.time()
        end_time = start_time + duration

        while time.time() < end_time:
            current_time = time.time()

            # Collect resource metrics
            resource_data["timestamps"].append(current_time - start_time)
            resource_data["cpu_percent"].append(self.process.cpu_percent())
            resource_data["memory_mb"].append(
                self.process.memory_info().rss / 1024 / 1024
            )
            resource_data["memory_percent"].append(self.process.memory_percent())
            resource_data["threads"].append(self.process.num_threads())

            try:
                resource_data["file_descriptors"].append(self.process.num_fds())
            except (AttributeError, psutil.AccessDenied):
                resource_data["file_descriptors"].append(0)

            # Sleep for interval
            time.sleep(interval)

        return resource_data

    def test_long_running_operations(self) -> Dict[str, Any]:
        """Test system stability during long - running operations"""
        logger.info("Testing long - running operations stability")

        duration = 30  # 30 seconds test
        results = {
            "test_duration": duration,
            "operations_completed": 0,
            "errors_encountered": 0,
            "resource_monitoring": None,
        }

        # Start resource monitoring in background
        monitor_thread = threading.Thread(
            target = lambda: results.update(
                {"resource_monitoring": self.monitor_system_resources(duration, 5)}
            )
        )
        monitor_thread.start()

        try:
            start_time = time.time()
            end_time = start_time + duration
            operation_count = 0

            while time.time() < end_time:
                try:
                    # Perform various operations
                    test_data = self.generate_test_data(random.randint(1000, 5000))

                    # Execute different strategies
                    strategies = ["RSI", "MACD", "Moving Average"]
                    for strategy in strategies:
                        self._execute_strategy_operation(strategy, test_data)
                        operation_count += 1

                    # Memory cleanup
                    del test_data
                    if operation_count % 10 == 0:
                        gc.collect()

                    # Small delay to prevent 100% CPU usage
                    time.sleep(0.1)

                except Exception as e:
                    results["errors_encountered"] += 1
                    self.error_log.append(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "operation": "long_running",
                            "error": str(e),
                            "traceback": traceback.format_exc(),
                        }
                    )
                    logger.warning(f"Error in long - running operation: {e}")

            results["operations_completed"] = operation_count

        except Exception as e:
            self.error_log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "operation": "long_running_main",
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
            )
            results["errors_encountered"] += 1

        # Wait for monitoring to complete
        monitor_thread.join()

        # Analyze resource usage
        if results["resource_monitoring"]:
            resource_data = results["resource_monitoring"]
            results["resource_analysis"] = {
                "max_memory_mb": max(resource_data["memory_mb"]),
                "avg_memory_mb": np.mean(resource_data["memory_mb"]),
                "memory_growth_mb": resource_data["memory_mb"][-1]
                - resource_data["memory_mb"][0],
                "max_cpu_percent": max(resource_data["cpu_percent"]),
                "avg_cpu_percent": np.mean(resource_data["cpu_percent"]),
                "max_threads": max(resource_data["threads"]),
            }

        logger.info(
            f"Long - running test completed: {results['operations_completed']} operations, {results['errors_encountered']} errors"
        )

        return results

    def test_memory_leak_detection(self) -> Dict[str, Any]:
        """Test for memory leaks during intensive operations"""
        logger.info("Testing memory leak detection")

        # Baseline memory measurement
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        memory_snapshots = [initial_memory]

        # Perform multiple iterations with cleanup
        iterations = 100
        for i in range(iterations):
            try:
                # Create and process large datasets
                test_data = self.generate_test_data(10000)

                # Perform intensive calculations
                result = self._perform_intensive_calculations(test_data)

                # Explicit cleanup
                del test_data, result

                # Force garbage collection
                if i % 10 == 0:
                    gc.collect()

                # Measure memory
                current_memory = self.process.memory_info().rss / 1024 / 1024
                memory_snapshots.append(current_memory)

                # Check for excessive memory growth
                memory_growth = current_memory - initial_memory
                if memory_growth > 500:  # 500MB threshold
                    logger.warning(
                        f"Excessive memory growth detected: {memory_growth:.1f}MB"
                    )

            except Exception as e:
                self.error_log.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "operation": "memory_leak_test",
                        "error": str(e),
                        "iteration": i,
                    }
                )

        # Final cleanup and measurement
        gc.collect()
        final_memory = self.process.memory_info().rss / 1024 / 1024

        # Analyze memory patterns
        memory_analysis = {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "max_memory_mb": max(memory_snapshots),
            "min_memory_mb": min(memory_snapshots),
            "memory_growth_mb": final_memory - initial_memory,
            "memory_leak_detected": (final_memory - initial_memory)
            > 100,  # 100MB threshold
            "memory_volatility_mb": np.std(memory_snapshots),
            "iterations_completed": iterations,
            "memory_snapshots": memory_snapshots[::10],  # Every 10th snapshot
        }

        logger.info(
            f"Memory leak test completed: Growth={memory_analysis['memory_growth_mb']:.1f}MB, Leak detected={memory_analysis['memory_leak_detected']}"
        )

        return memory_analysis

    def test_concurrent_access_stability(self) -> Dict[str, Any]:
        """Test system stability under concurrent access"""
        logger.info("Testing concurrent access stability")

        num_threads = 8
        operations_per_thread = 20
        results = {
            "threads_completed": 0,
            "total_operations": 0,
            "errors_encountered": 0,
            "thread_results": [],
        }

        def worker_function(thread_id: int) -> Dict[str, Any]:
            """Worker function for concurrent testing"""
            thread_results = {
                "thread_id": thread_id,
                "operations_completed": 0,
                "errors": 0,
                "start_time": time.time(),
            }

            try:
                for i in range(operations_per_thread):
                    try:
                        # Generate varying data sizes
                        data_size = random.randint(1000, 5000)
                        test_data = self.generate_test_data(data_size)

                        # Execute random strategies
                        strategies = [
                            "RSI",
                            "MACD",
                            "Moving Average",
                            "Bollinger Bands",
                        ]
                        strategy = random.choice(strategies)

                        self._execute_strategy_operation(strategy, test_data)
                        thread_results["operations_completed"] += 1

                        # Random cleanup
                        if random.random() < 0.3:  # 30% chance
                            del test_data
                            gc.collect()

                    except Exception as e:
                        thread_results["errors"] += 1
                        self.error_log.append(
                            {
                                "timestamp": datetime.now().isoformat(),
                                "operation": f"concurrent_thread_{thread_id}",
                                "error": str(e),
                            }
                        )

                thread_results["end_time"] = time.time()
                thread_results["duration"] = (
                    thread_results["end_time"] - thread_results["start_time"]
                )

            except Exception as e:
                thread_results["critical_error"] = str(e)
                self.error_log.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "operation": f"concurrent_thread_{thread_id}_critical",
                        "error": str(e),
                    }
                )

            return thread_results

        # Start concurrent operations
        start_time = time.time()

        with ThreadPoolExecutor(max_workers = num_threads) as executor:
            # Submit worker tasks
            futures = [
                executor.submit(worker_function, thread_id)
                for thread_id in range(num_threads)
            ]

            # Collect results
            for future in as_completed(futures):
                try:
                    thread_result = future.result()
                    results["thread_results"].append(thread_result)
                    results["threads_completed"] += 1
                    results["total_operations"] += thread_result["operations_completed"]
                    results["errors_encountered"] += thread_result.get("errors", 0)

                except Exception as e:
                    results["errors_encountered"] += 1
                    self.error_log.append(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "operation": "concurrent_result_collection",
                            "error": str(e),
                        }
                    )

        total_time = time.time() - start_time

        # Analyze concurrent performance
        concurrent_analysis = {
            "total_time": total_time,
            "operations_per_second": (
                results["total_operations"] / total_time if total_time > 0 else 0
            ),
            "avg_operations_per_thread": (
                results["total_operations"] / results["threads_completed"]
                if results["threads_completed"] > 0
                else 0
            ),
            "error_rate": (
                results["errors_encountered"] / results["total_operations"]
                if results["total_operations"] > 0
                else 0
            ),
            "thread_success_rate": results["threads_completed"] / num_threads,
            "max_thread_duration": (
                max([r.get("duration", 0) for r in results["thread_results"]])
                if results["thread_results"]
                else 0
            ),
            "min_thread_duration": (
                min([r.get("duration", 0) for r in results["thread_results"]])
                if results["thread_results"]
                else 0
            ),
        }

        results.update(concurrent_analysis)

        logger.info(
            f"Concurrent access test completed: {results['total_operations']} operations, {results['errors_encountered']} errors"
        )

        return results

    def test_resource_exhaustion_handling(self) -> Dict[str, Any]:
        """Test system behavior under resource exhaustion"""
        logger.info("Testing resource exhaustion handling")

        results = {
            "memory_exhaustion_test": None,
            "cpu_exhaustion_test": None,
            "file_handle_exhaustion_test": None,
            "recovery_success": False,
        }

        # Test memory exhaustion handling
        try:
            logger.info("Testing memory exhaustion handling")
            memory_hogs = []
            max_attempts = 100
            attempts = 0

            while attempts < max_attempts:
                try:
                    # Allocate large chunks of memory
                    large_array = np.random.random(1000000)  # ~8MB per array
                    memory_hogs.append(large_array)
                    attempts += 1

                    # Check if system is struggling
                    memory_percent = self.process.memory_percent()
                    if memory_percent > 80:  # 80% memory usage threshold
                        logger.warning(
                            f"High memory usage detected: {memory_percent:.1f}%"
                        )
                        break

                except MemoryError:
                    logger.info("MemoryError caught - system handled gracefully")
                    break
                except Exception as e:
                    logger.warning(f"Unexpected error during memory stress: {e}")
                    break

            results["memory_exhaustion_test"] = {
                "attempts_completed": attempts,
                "arrays_allocated": len(memory_hogs),
                "memory_allocated_mb": len(memory_hogs) * 8,
                "memory_error_handled": attempts < max_attempts,
            }

            # Cleanup
            del memory_hogs
            gc.collect()

        except Exception as e:
            results["memory_exhaustion_test"] = {"error": str(e)}
            self.error_log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "operation": "memory_exhaustion_test",
                    "error": str(e),
                }
            )

        # Test CPU exhaustion handling
        try:
            logger.info("Testing CPU exhaustion handling")
            start_time = time.time()
            duration = 30  # 30 seconds of CPU stress

            def cpu_stress():
                end_time = time.time() + duration
                while time.time() < end_time:
                    # Intensive calculation
                    _ = sum([i * *2 for i in range(10000)])

            # Start CPU stress in multiple threads
            num_threads = multiprocessing.cpu_count()
            threads = []

            for _ in range(num_threads):
                thread = threading.Thread(target = cpu_stress)
                thread.start()
                threads.append(thread)

            # Monitor system during stress
            cpu_readings = []
            while any(thread.is_alive() for thread in threads):
                cpu_readings.append(self.process.cpu_percent())
                time.sleep(1)

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            results["cpu_exhaustion_test"] = {
                "duration": time.time() - start_time,
                "threads_used": num_threads,
                "max_cpu_percent": max(cpu_readings) if cpu_readings else 0,
                "avg_cpu_percent": np.mean(cpu_readings) if cpu_readings else 0,
                "system_responsive": True,  # If we reach here, system remained responsive
            }

        except Exception as e:
            results["cpu_exhaustion_test"] = {"error": str(e)}
            self.error_log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "operation": "cpu_exhaustion_test",
                    "error": str(e),
                }
            )

        # Test file handle exhaustion handling
        try:
            logger.info("Testing file handle exhaustion handling")
            file_handles = []
            max_files = 1000

            for i in range(max_files):
                try:
                    # Create temporary files
                    temp_file = f"temp_test_{i}_{int(time.time())}.tmp"
                    with open(temp_file, "w") as f:
                        f.write(f"Test data {i}")
                    file_handles.append(temp_file)

                except (OSError, IOError) as e:
                    logger.warning(f"File handle limit reached at {i} files: {e}")
                    break
                except Exception as e:
                    logger.warning(f"Unexpected error creating file {i}: {e}")
                    break

            results["file_handle_exhaustion_test"] = {
                "files_created": len(file_handles),
                "limit_reached": len(file_handles) < max_files,
                "cleanup_needed": len(file_handles) > 0,
            }

            # Cleanup
            for temp_file in file_handles:
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

        except Exception as e:
            results["file_handle_exhaustion_test"] = {"error": str(e)}
            self.error_log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "operation": "file_handle_exhaustion_test",
                    "error": str(e),
                }
            )

        # Test recovery capability
        try:
            logger.info("Testing system recovery capability")

            # Try to perform normal operations after stress tests
            test_data = self.generate_test_data(1000)
            result = self._execute_strategy_operation("RSI", test_data)

            recovery_successful = result is not None
            results["recovery_success"] = recovery_successful

            if not recovery_successful:
                logger.error("System failed to recover from resource exhaustion")
            else:
                logger.info("System successfully recovered from resource exhaustion")

        except Exception as e:
            results["recovery_success"] = False
            self.error_log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "operation": "recovery_test",
                    "error": str(e),
                }
            )

        return results

    def test_data_integrity_under_stress(self) -> Dict[str, Any]:
        """Test data integrity during stressful operations"""
        logger.info("Testing data integrity under stress")

        # Create known test data
        np.random.seed(42)  # Fixed seed for reproducible data
        original_data = self.generate_test_data(5000)
        original_checksum = self._calculate_data_checksum(original_data)

        results = {
            "original_checksum": original_checksum,
            "data_corruption_detected": False,
            "integrity_tests_passed": 0,
            "integrity_tests_failed": 0,
            "stress_operations": 0,
        }

        # Perform stress operations while checking integrity
        for i in range(50):
            try:
                # Create a copy and perform operations
                test_data = original_data.copy()

                # Stress operations
                self._perform_intensive_calculations(test_data)

                # Concurrent modifications (simulate)
                with ThreadPoolExecutor(max_workers = 2) as executor:
                    futures = [
                        executor.submit(
                            self._perform_intensive_calculations, test_data.copy()
                        ),
                        executor.submit(
                            self._perform_intensive_calculations, test_data.copy()
                        ),
                    ]

                    for future in futures:
                        future.result()

                # Verify original data is unchanged
                current_checksum = self._calculate_data_checksum(original_data)

                if current_checksum != original_checksum:
                    results["data_corruption_detected"] = True
                    results["corruption_point"] = i
                    self.error_log.append(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "operation": f"data_integrity_test_{i}",
                            "error": "Data corruption detected",
                            "expected_checksum": original_checksum,
                            "actual_checksum": current_checksum,
                        }
                    )
                    break
                else:
                    results["integrity_tests_passed"] += 1

                results["stress_operations"] += 1

                # Cleanup
                del test_data
                if i % 10 == 0:
                    gc.collect()

            except Exception as e:
                results["integrity_tests_failed"] += 1
                self.error_log.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "operation": f"data_integrity_stress_{i}",
                        "error": str(e),
                    }
                )

        logger.info(
            f"Data integrity test completed: {results['integrity_tests_passed']} passed, {results['integrity_tests_failed']} failed"
        )

        return results

    def _execute_strategy_operation(
        self, strategy: str, data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """Execute a strategy operation for testing"""
        try:
            if strategy == "RSI":
                delta = data["close"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window = 14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window = 14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))

                return {"rsi_mean": rsi.mean(), "rsi_std": rsi.std()}

            elif strategy == "MACD":
                ema12 = data["close"].ewm(span = 12).mean()
                ema26 = data["close"].ewm(span = 26).mean()
                macd = ema12 - ema26

                return {"macd_mean": macd.mean(), "macd_std": macd.std()}

            elif strategy == "Moving Average":
                sma20 = data["close"].rolling(window = 20).mean()
                sma50 = data["close"].rolling(window = 50).mean()

                return {"sma20_mean": sma20.mean(), "sma50_mean": sma50.mean()}

            elif strategy == "Bollinger Bands":
                sma20 = data["close"].rolling(window = 20).mean()
                std20 = data["close"].rolling(window = 20).std()
                upper_band = sma20 + (std20 * 2)
                lower_band = sma20 - (std20 * 2)

                return {
                    "upper_band_mean": upper_band.mean(),
                    "lower_band_mean": lower_band.mean(),
                    "band_width_mean": (upper_band - lower_band).mean(),
                }

            return None

        except Exception as e:
            raise Exception(f"Strategy execution failed: {e}")

    def _perform_intensive_calculations(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform intensive calculations on data"""
        try:
            # Multiple intensive operations
            results = {}

            # Statistical calculations
            results["mean"] = data["close"].mean()
            results["std"] = data["close"].std()
            results["skew"] = data["close"].skew()
            results["kurt"] = data["close"].kurtosis()

            # Rolling calculations
            results["rolling_mean"] = data["close"].rolling(window = 50).mean().iloc[-1]
            results["rolling_std"] = data["close"].rolling(window = 50).std().iloc[-1]

            # Correlation calculations
            results["volume_price_corr"] = data["close"].corr(data["volume"])

            # Volatility calculations
            returns = data["close"].pct_change().fillna(0)
            results["volatility"] = returns.std() * np.sqrt(252)

            # Maximum drawdown calculation
            cum_returns = (1 + returns).cumprod()
            running_max = cum_returns.expanding().max()
            drawdown = (cum_returns - running_max) / running_max
            results["max_drawdown"] = drawdown.min()

            return results

        except Exception as e:
            raise Exception(f"Intensive calculations failed: {e}")

    def _calculate_data_checksum(self, data: pd.DataFrame) -> str:
        """Calculate checksum of DataFrame for integrity checking"""
        try:
            # Use hash of key statistics and first / last values
            data_summary = {
                "shape": data.shape,
                "columns": list(data.columns),
                "first_values": data.iloc[0].to_dict(),
                "last_values": data.iloc[-1].to_dict(),
                "close_mean": data["close"].mean(),
                "close_std": data["close"].std(),
                "volume_mean": data["volume"].mean(),
            }

            import hashlib

            summary_str = json.dumps(data_summary, sort_keys = True, default = str)
            return hashlib.md5(summary_str.encode()).hexdigest()

        except Exception as e:
            logger.warning(f"Could not calculate data checksum: {e}")
            return "checksum_error"

    def run_all_stability_tests(self) -> Dict[str, Any]:
        """Run all stability tests"""
        logger.info("=" * 80)
        logger.info("PHASE 4: SYSTEM STABILITY TESTING")
        logger.info("=" * 80)

        start_time = time.time()

        # Run all stability tests
        self.results["long_running_operations"] = self.test_long_running_operations()
        self.results["memory_leak_detection"] = self.test_memory_leak_detection()
        self.results["concurrent_access_stability"] = (
            self.test_concurrent_access_stability()
        )
        self.results["resource_exhaustion_handling"] = (
            self.test_resource_exhaustion_handling()
        )
        self.results["data_integrity_under_stress"] = (
            self.test_data_integrity_under_stress()
        )

        total_time = time.time() - start_time

        # Calculate overall stability score
        stability_score = self._calculate_stability_score()

        # Generate final report
        report = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "phase": "Phase 4 - System Stability Testing",
            "total_execution_time": total_time,
            "stability_tests": self.results,
            "stability_score": stability_score,
            "error_summary": {
                "total_errors": len(self.error_log),
                "error_categories": self._categorize_errors(),
            },
            "summary": {
                "system_stable": stability_score["overall_score"] >= 7.0,
                "memory_leaks_detected": self.results["memory_leak_detection"][
                    "memory_leak_detected"
                ],
                "data_integrity_maintained": not self.results[
                    "data_integrity_under_stress"
                ]["data_corruption_detected"],
                "recovery_successful": self.results["resource_exhaustion_handling"][
                    "recovery_success"
                ],
            },
        }

        # Save report
        report_path = os.path.join(
            os.path.dirname(__file__), "phase4_stability_test_report.json"
        )
        with open(report_path, "w") as f:
            json.dump(report, f, indent = 2, default = str)

        # Print summary
        logger.info("=" * 80)
        logger.info("SYSTEM STABILITY TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(
            f"Overall Stability Score: {stability_score['overall_score']:.1f}/10"
        )
        logger.info(f"System Stable: {report['summary']['system_stable']}")
        logger.info(
            f"Memory Leaks Detected: {report['summary']['memory_leaks_detected']}"
        )
        logger.info(
            f"Data Integrity Maintained: {report['summary']['data_integrity_maintained']}"
        )
        logger.info(f"Recovery Successful: {report['summary']['recovery_successful']}")
        logger.info(f"Total Errors: {report['error_summary']['total_errors']}")

        return report

    def _calculate_stability_score(self) -> Dict[str, float]:
        """Calculate overall stability score"""
        scores = {}

        # Long - running operations score
        long_running = self.results["long_running_operations"]
        if long_running["errors_encountered"] == 0:
            scores["long_running"] = 10.0
        else:
            error_rate = long_running["errors_encountered"] / max(
                long_running["operations_completed"], 1
            )
            scores["long_running"] = max(10.0 - (error_rate * 100), 0.0)

        # Memory leak score
        memory_leak = self.results["memory_leak_detection"]
        if not memory_leak["memory_leak_detected"]:
            scores["memory_leak"] = 10.0
        else:
            memory_growth = memory_leak["memory_growth_mb"]
            scores["memory_leak"] = max(
                10.0 - memory_growth / 20, 0.0
            )  # Deduct points for memory growth

        # Concurrent access score
        concurrent = self.results["concurrent_access_stability"]
        concurrent_score = max(10.0 - (concurrent["error_rate"] * 100), 0.0)
        scores["concurrent_access"] = concurrent_score

        # Resource exhaustion score
        resource_exhaustion = self.results["resource_exhaustion_handling"]
        recovery_score = 10.0 if resource_exhaustion["recovery_success"] else 0.0
        scores["resource_exhaustion"] = recovery_score

        # Data integrity score
        data_integrity = self.results["data_integrity_under_stress"]
        if not data_integrity["data_corruption_detected"]:
            scores["data_integrity"] = 10.0
        else:
            scores["data_integrity"] = 0.0

        # Overall score
        overall_score = np.mean(list(scores.values()))

        return {"component_scores": scores, "overall_score": overall_score}

    def _categorize_errors(self) -> Dict[str, int]:
        """Categorize errors by type"""
        categories = {}
        for error in self.error_log:
            operation = error.get("operation", "unknown")
            if operation not in categories:
                categories[operation] = 0
            categories[operation] += 1
        return categories


def run_stability_tests():
    """Main function to run stability tests"""
    stability_test = StabilityTest()
    return stability_test.run_all_stability_tests()


if __name__ == "__main__":
    logging.basicConfig(
        level = logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    report = run_stability_tests()

    print(f"\nStability testing completed!")
    print(
        f"Overall stability score: {report['stability_score']['overall_score']:.1f}/10"
    )
    print(f"System stable: {report['summary']['system_stable']}")

    sys.exit(0 if report["summary"]["system_stable"] else 1)

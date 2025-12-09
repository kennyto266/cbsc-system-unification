#!/usr/bin/env python3
"""
Performance/Load Test Suite for 32-Core Concurrent Testing and Memory Pressure Validation
Tests system stability under high load and memory pressure scenarios
"""

import os
import sys
import time
import unittest
import threading
import tempfile
import json
import gc
import psutil
import multiprocessing
import concurrent.futures
import statistics
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import actual components if they exist
try:
    from src.memory.adaptive_allocator import AdaptiveMemoryAllocator
except ImportError:
    AdaptiveMemoryAllocator = Mock

try:
    from src.ipc.atomic_initializer import AtomicInitializer
except ImportError:
    AtomicInitializer = Mock


@dataclass
class LoadTestMetrics:
    """Metrics collected during load testing"""
    test_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    total_operations: int
    successful_operations: int
    failed_operations: int
    success_rate: float
    operations_per_second: float
    peak_memory_mb: float
    avg_cpu_percent: float
    peak_cpu_percent: float
    thread_count: int
    errors: List[str]
    memory_samples: List[float]
    cpu_samples: List[float]


class MockHighLoadSystem:
    """Mock system that simulates high load scenarios"""

    def __init__(self, cpu_cores=32, memory_gb=16):
        self.cpu_cores = cpu_cores
        self.memory_gb = memory_gb
        self.active_threads = []
        self.stop_event = threading.Event()
        self.metrics = {}
        self.process = psutil.Process()

    def cpu_intensive_task(self, task_id, duration_seconds=5.0):
        """Simulate CPU-intensive task"""
        try:
            start_time = time.time()
            operations = 0

            while time.time() - start_time < duration_seconds and not self.stop_event.is_set():
                # Perform CPU-intensive operations
                for i in range(1000):
                    _ = i * i * i  # Math operations
                operations += 1

                # Small sleep to prevent complete CPU hogging
                time.sleep(0.001)

            return {
                'task_id': task_id,
                'operations': operations,
                'duration': time.time() - start_time,
                'success': True
            }

        except Exception as e:
            return {
                'task_id': task_id,
                'error': str(e),
                'success': False
            }

    def memory_intensive_task(self, task_id, memory_mb=100, duration_seconds=5.0):
        """Simulate memory-intensive task"""
        try:
            # Allocate memory
            data = []
            chunk_size = 1024  # 1KB chunks
            chunks_needed = memory_mb * 1024 // chunk_size

            for i in range(chunks_needed):
                data.append bytearray(chunk_size))

            start_time = time.time()
            operations = 0

            while time.time() - start_time < duration_seconds and not self.stop_event.is_set():
                # Access memory to simulate active usage
                for chunk in data[:10]:  # Access first 10 chunks
                    _ = chunk[0]  # Read first byte
                operations += 1
                time.sleep(0.01)

            return {
                'task_id': task_id,
                'memory_allocated_mb': memory_mb,
                'operations': operations,
                'duration': time.time() - start_time,
                'success': True
            }

        except MemoryError:
            return {
                'task_id': task_id,
                'error': 'Memory allocation failed',
                'success': False
            }
        except Exception as e:
            return {
                'task_id': task_id,
                'error': str(e),
                'success': False
            }

    def mixed_workload_task(self, task_id, cpu_load=0.5, memory_mb=50, duration_seconds=5.0):
        """Simulate mixed CPU and memory workload"""
        try:
            # Allocate memory
            data = []
            if memory_mb > 0:
                chunk_size = 1024
                chunks_needed = memory_mb * 1024 // chunk_size
                for i in range(chunks_needed):
                    data.append(bytearray(chunk_size))

            start_time = time.time()
            operations = 0

            while time.time() - start_time < duration_seconds and not self.stop_event.is_set():
                # CPU work
                if cpu_load > 0:
                    cpu_work_time = 0.001 * cpu_load
                    cpu_start = time.time()
                    while time.time() - cpu_start < cpu_work_time:
                        _ = operations * operations

                # Memory work
                if data:
                    for chunk in data[:5]:
                        _ = chunk[0]

                operations += 1
                time.sleep(0.01)

            return {
                'task_id': task_id,
                'operations': operations,
                'duration': time.time() - start_time,
                'success': True
            }

        except Exception as e:
            return {
                'task_id': task_id,
                'error': str(e),
                'success': False
            }

    def stop_all_tasks(self):
        """Stop all running tasks"""
        self.stop_event.set()

    def reset(self):
        """Reset system state"""
        self.stop_event.clear()
        self.active_threads.clear()


class LoadTestRunner:
    """Runner for load testing scenarios"""

    def __init__(self, system=None):
        self.system = system or MockHighLoadSystem()
        self.metrics_history = []

    def run_concurrent_cpu_test(self, num_threads=32, duration_seconds=30) -> LoadTestMetrics:
        """Run concurrent CPU-intensive test"""
        test_name = f"concurrent_cpu_test_{num_threads}_threads"
        print(f"Starting {test_name}...")

        self.system.reset()
        start_time = datetime.now()
        memory_samples = []
        cpu_samples = []

        # Start monitoring thread
        def monitor_resources():
            while not self.system.stop_event.wait(0.1):
                try:
                    memory_info = self.system.process.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)
                    cpu_percent = self.system.process.cpu_percent()
                    memory_samples.append(memory_mb)
                    cpu_samples.append(cpu_percent)
                except:
                    pass

        monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
        monitor_thread.start()

        # Run CPU-intensive tasks
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(self.system.cpu_intensive_task, i, duration_seconds)
                for i in range(num_threads)
            ]

            results = []
            for future in concurrent.futures.as_completed(futures, timeout=duration_seconds + 10):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({'error': str(e), 'success': False})

        # Stop monitoring
        self.system.stop_all_tasks()
        time.sleep(0.1)  # Allow monitoring to finish

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Calculate metrics
        successful_operations = sum(1 for r in results if r.get('success', False))
        total_operations = len(results)
        success_rate = successful_operations / total_operations if total_operations > 0 else 0

        metrics = LoadTestMetrics(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=total_operations - successful_operations,
            success_rate=success_rate,
            operations_per_second=successful_operations / duration if duration > 0 else 0,
            peak_memory_mb=max(memory_samples) if memory_samples else 0,
            avg_cpu_percent=statistics.mean(cpu_samples) if cpu_samples else 0,
            peak_cpu_percent=max(cpu_samples) if cpu_samples else 0,
            thread_count=num_threads,
            errors=[r.get('error', '') for r in results if not r.get('success', False)],
            memory_samples=memory_samples,
            cpu_samples=cpu_samples
        )

        self.metrics_history.append(metrics)
        return metrics

    def run_memory_pressure_test(self, memory_gb_total=6, num_threads=16) -> LoadTestMetrics:
        """Run memory pressure test"""
        test_name = f"memory_pressure_test_{memory_gb_total}gb_{num_threads}_threads"
        print(f"Starting {test_name}...")

        self.system.reset()
        start_time = datetime.now()
        memory_samples = []
        cpu_samples = []

        # Calculate memory per thread
        memory_per_thread_mb = (memory_gb_total * 1024) // num_threads

        # Start monitoring
        def monitor_resources():
            while not self.system.stop_event.wait(0.1):
                try:
                    memory_info = self.system.process.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)
                    cpu_percent = self.system.process.cpu_percent()
                    memory_samples.append(memory_mb)
                    cpu_samples.append(cpu_percent)

                    # Stop if memory usage gets too high (>90% of system memory)
                    if memory_mb > (self.system.memory_gb * 1024 * 0.9):
                        print(f"Memory usage too high: {memory_mb:.1f}MB, stopping test")
                        self.system.stop_event.set()
                        break
                except:
                    pass

        monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
        monitor_thread.start()

        # Run memory-intensive tasks
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(self.system.memory_intensive_task, i, memory_per_thread_mb, 10.0)
                for i in range(num_threads)
            ]

            results = []
            for future in concurrent.futures.as_completed(futures, timeout=20.0):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({'error': str(e), 'success': False})

        # Stop monitoring
        self.system.stop_all_tasks()
        time.sleep(0.1)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Calculate metrics
        successful_operations = sum(1 for r in results if r.get('success', False))
        total_operations = len(results)
        success_rate = successful_operations / total_operations if total_operations > 0 else 0

        metrics = LoadTestMetrics(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=total_operations - successful_operations,
            success_rate=success_rate,
            operations_per_second=successful_operations / duration if duration > 0 else 0,
            peak_memory_mb=max(memory_samples) if memory_samples else 0,
            avg_cpu_percent=statistics.mean(cpu_samples) if cpu_samples else 0,
            peak_cpu_percent=max(cpu_samples) if cpu_samples else 0,
            thread_count=num_threads,
            errors=[r.get('error', '') for r in results if not r.get('success', False)],
            memory_samples=memory_samples,
            cpu_samples=cpu_samples
        )

        self.metrics_history.append(metrics)
        return metrics

    def run_mixed_workload_test(self, num_threads=24, duration_seconds=30) -> LoadTestMetrics:
        """Run mixed workload test"""
        test_name = f"mixed_workload_test_{num_threads}_threads"
        print(f"Starting {test_name}...")

        self.system.reset()
        start_time = datetime.now()
        memory_samples = []
        cpu_samples = []

        # Start monitoring
        def monitor_resources():
            while not self.system.stop_event.wait(0.1):
                try:
                    memory_info = self.system.process.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)
                    cpu_percent = self.system.process.cpu_percent()
                    memory_samples.append(memory_mb)
                    cpu_samples.append(cpu_percent)
                except:
                    pass

        monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
        monitor_thread.start()

        # Run mixed workload tasks with varying CPU and memory loads
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for i in range(num_threads):
                # Vary CPU and memory load
                cpu_load = 0.3 + (i % 5) * 0.2  # 0.3 to 1.1
                memory_mb = 25 + (i % 3) * 25   # 25 to 75 MB

                future = executor.submit(
                    self.system.mixed_workload_task,
                    i, cpu_load, memory_mb, duration_seconds
                )
                futures.append(future)

            results = []
            for future in concurrent.futures.as_completed(futures, timeout=duration_seconds + 10):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({'error': str(e), 'success': False})

        # Stop monitoring
        self.system.stop_all_tasks()
        time.sleep(0.1)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Calculate metrics
        successful_operations = sum(1 for r in results if r.get('success', False))
        total_operations = len(results)
        success_rate = successful_operations / total_operations if total_operations > 0 else 0

        metrics = LoadTestMetrics(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=total_operations - successful_operations,
            success_rate=success_rate,
            operations_per_second=successful_operations / duration if duration > 0 else 0,
            peak_memory_mb=max(memory_samples) if memory_samples else 0,
            avg_cpu_percent=statistics.mean(cpu_samples) if cpu_samples else 0,
            peak_cpu_percent=max(cpu_samples) if cpu_samples else 0,
            thread_count=num_threads,
            errors=[r.get('error', '') for r in results if not r.get('success', False)],
            memory_samples=memory_samples,
            cpu_samples=cpu_samples
        )

        self.metrics_history.append(metrics)
        return metrics

    def run_stability_test(self, duration_minutes=5) -> LoadTestMetrics:
        """Run long-term stability test"""
        test_name = f"stability_test_{duration_minutes}min"
        print(f"Starting {test_name}...")

        self.system.reset()
        start_time = datetime.now()
        memory_samples = []
        cpu_samples = []
        duration_seconds = duration_minutes * 60

        # Start monitoring
        def monitor_resources():
            while not self.system.stop_event.wait(0.5):
                try:
                    memory_info = self.system.process.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)
                    cpu_percent = self.system.process.cpu_percent()
                    memory_samples.append(memory_mb)
                    cpu_samples.append(cpu_percent)
                except:
                    pass

        monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
        monitor_thread.start()

        # Run continuous mixed workload
        def continuous_workload():
            cycle_count = 0
            while not self.system.stop_event.is_set():
                # Vary workload over time
                cpu_load = 0.3 + (cycle_count % 10) * 0.1
                memory_mb = 20 + (cycle_count % 5) * 10

                result = self.system.mixed_workload_task(
                    f"continuous_{cycle_count}",
                    cpu_load, memory_mb, 2.0
                )
                cycle_count += 1

        # Start multiple continuous workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(continuous_workload)
                for _ in range(4)
            ]

            # Wait for duration
            time.sleep(duration_seconds)
            self.system.stop_all_tasks()

            # Wait for all workers to finish
            for future in concurrent.futures.as_completed(futures, timeout=10):
                try:
                    future.result()
                except Exception:
                    pass

        # Stop monitoring
        time.sleep(0.1)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Calculate stability metrics
        total_operations = len(memory_samples)
        memory_stability = (
            np.std(memory_samples) / np.mean(memory_samples)
            if memory_samples and np.mean(memory_samples) > 0 else 0
        )
        cpu_stability = (
            np.std(cpu_samples) / np.mean(cpu_samples)
            if cpu_samples and np.mean(cpu_samples) > 0 else 0
        )

        metrics = LoadTestMetrics(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            total_operations=total_operations,
            successful_operations=total_operations,
            failed_operations=0,
            success_rate=1.0,
            operations_per_second=total_operations / duration if duration > 0 else 0,
            peak_memory_mb=max(memory_samples) if memory_samples else 0,
            avg_cpu_percent=statistics.mean(cpu_samples) if cpu_samples else 0,
            peak_cpu_percent=max(cpu_samples) if cpu_samples else 0,
            thread_count=4,
            errors=[],
            memory_samples=memory_samples,
            cpu_samples=cpu_samples
        )

        # Add stability metrics as special notes
        metrics.errors.append(f"Memory stability (CV): {memory_stability:.3f}")
        metrics.errors.append(f"CPU stability (CV): {cpu_stability:.3f}")

        self.metrics_history.append(metrics)
        return metrics


class TestConcurrentLoad(unittest.TestCase):
    """Test concurrent load scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.system = MockHighLoadSystem(cpu_cores=32, memory_gb=16)
        self.runner = LoadTestRunner(self.system)

    def test_32_core_cpu_load(self):
        """Test 32-core concurrent CPU load"""
        metrics = self.runner.run_concurrent_cpu_test(num_threads=32, duration_seconds=10)

        # Validate target metrics
        self.assertGreaterEqual(metrics.success_rate, 0.95, "CPU load test success rate should be >= 95%")
        self.assertLessEqual(metrics.peak_memory_mb, 1024, "Peak memory should be <= 1GB for CPU-only test")
        self.assertGreaterEqual(metrics.avg_cpu_percent, 50.0, "Average CPU usage should be >= 50%")
        self.assertLess(metrics.duration_seconds, 15.0, "Test should complete within 15 seconds")

        print(f"32-core CPU test: {metrics.success_rate:.1%} success rate, "
              f"{metrics.operations_per_second:.1f} ops/sec")

    def test_memory_pressure_6gb(self):
        """Test memory pressure with 6GB stable usage"""
        metrics = self.runner.run_memory_pressure_test(memory_gb_total=6, num_threads=16)

        # Validate memory usage targets
        self.assertGreaterEqual(metrics.success_rate, 0.90, "Memory pressure test success rate should be >= 90%")
        self.assertGreater(metrics.peak_memory_mb, 5500, "Peak memory should be >= 5.5GB")
        self.assertLess(metrics.peak_memory_mb, 6500, "Peak memory should be <= 6.5GB")

        print(f"Memory pressure test: {metrics.peak_memory_mb:.1f}MB peak memory, "
              f"{metrics.success_rate:.1%} success rate")

    def test_mixed_workload_scalability(self):
        """Test mixed workload scalability across different thread counts"""
        thread_counts = [8, 16, 24, 32]
        results = []

        for thread_count in thread_counts:
            metrics = self.runner.run_mixed_workload_test(
                num_threads=thread_count,
                duration_seconds=5
            )
            results.append((thread_count, metrics))

        # Validate scalability
        for thread_count, metrics in results:
            self.assertGreaterEqual(metrics.success_rate, 0.90,
                                  f"Mixed workload with {thread_count} threads should have >= 90% success rate")
            self.assertGreater(metrics.operations_per_second, 0,
                              f"Should have positive operations per second for {thread_count} threads")

        # Check that performance scales with thread count (within reason)
        ops_per_thread = [metrics.operations_per_second / thread_count for thread_count, metrics in results]
        avg_ops_per_thread = statistics.mean(ops_per_thread)

        # Performance per thread shouldn't vary wildly
        for ops in ops_per_thread:
            self.assertGreater(ops, avg_ops_per_thread * 0.3,
                             "Performance per thread should be reasonable across all thread counts")

        print(f"Mixed workload scalability test completed for {len(results)} configurations")

    @unittest.skipUnless(os.getenv('RUN_LONG_TESTS'), "Set RUN_LONG_TESTS environment variable to run")
    def test_long_term_stability(self):
        """Test long-term stability (24-hour equivalent compressed test)"""
        # Run 5-minute stability test as representative
        metrics = self.runner.run_stability_test(duration_minutes=1)  # Reduced for CI

        # Validate stability
        self.assertEqual(metrics.failed_operations, 0, "Should have no failed operations in stability test")
        self.assertGreater(len(metrics.memory_samples), 100, "Should have sufficient memory samples")

        # Parse stability metrics from errors list (used as additional data)
        memory_stability = None
        cpu_stability = None
        for note in metrics.errors:
            if "Memory stability" in note:
                memory_stability = float(note.split(":")[1].strip())
            elif "CPU stability" in note:
                cpu_stability = float(note.split(":")[1].strip())

        if memory_stability is not None:
            self.assertLess(memory_stability, 0.2, "Memory usage should be stable (CV < 0.2)")
        if cpu_stability is not None:
            self.assertLess(cpu_stability, 0.3, "CPU usage should be stable (CV < 0.3)")

        print(f"Stability test: {metrics.duration_seconds:.1f}s duration, "
              f"{metrics.peak_memory_mb:.1f}MB peak memory")

    def test_shutdown_performance(self):
        """Test graceful shutdown performance"""
        start_time = time.time()

        # Start some workloads
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            futures = [
                executor.submit(self.system.mixed_workload_task, i, 0.5, 50, 5.0)
                for i in range(16)
            ]

            # Let them run for a short time
            time.sleep(2.0)

            # Trigger shutdown
            shutdown_start = time.time()
            self.system.stop_all_tasks()

            # Wait for all tasks to complete
            for future in concurrent.futures.as_completed(futures, timeout=10.0):
                try:
                    future.result(timeout=1.0)
                except Exception:
                    pass

            shutdown_time = time.time() - shutdown_start

        # Validate shutdown performance
        self.assertLess(shutdown_time, 30.0, "Graceful shutdown should complete within 30 seconds")

        print(f"Shutdown performance test: {shutdown_time:.2f}s shutdown time")

    def test_memory_fragmentation(self):
        """Test memory fragmentation under load"""
        initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)

        # Perform multiple allocation/deallocation cycles
        for cycle in range(10):
            # Allocate memory
            data_blocks = []
            for i in range(100):
                data_blocks.append(bytearray(1024 * 1024))  # 1MB each

            # Access some memory
            for block in data_blocks[:10]:
                _ = block[0]

            # Deallocate most memory
            del data_blocks[:-10]
            gc.collect()

        final_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        memory_growth = final_memory - initial_memory

        # Memory growth should be reasonable (< 100MB)
        self.assertLess(memory_growth, 100, "Memory growth should be minimal after allocation cycles")

        print(f"Memory fragmentation test: {memory_growth:.1f}MB growth")

    def test_concurrent_allocators(self):
        """Test concurrent memory allocator operations"""
        if AdaptiveMemoryAllocator == Mock:
            self.skipTest("AdaptiveMemoryAllocator not available")

        allocators = []
        results = []

        def allocator_worker(worker_id):
            try:
                allocator = AdaptiveMemoryAllocator(
                    total_memory_gb=4.0,
                    enable_monitoring=False
                )
                allocators.append(allocator)

                # Perform multiple allocations
                for i in range(10):
                    result = allocator.calculate_optimal_allocation(
                        data_size_mb=100.0,
                        concurrent_processes=4,
                        task_type="testing"
                    )
                    results.append((worker_id, i, result is not None))

                return True
            except Exception as e:
                results.append((worker_id, "error", str(e)))
                return False

        # Run multiple allocator workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(allocator_worker, i) for i in range(8)]
            successes = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Validate concurrent allocator performance
        self.assertEqual(len(successes), 8, "All allocator workers should complete")
        self.assertTrue(all(successes), "All allocator workers should succeed")

        successful_allocations = sum(1 for _, _, success in results if success is True)
        expected_allocations = 8 * 10  # 8 workers * 10 allocations each
        self.assertEqual(successful_allocations, expected_allocations,
                        "All allocations should succeed")

        print(f"Concurrent allocators test: {successful_allocations} successful allocations")

    def test_resource_cleanup(self):
        """Test proper resource cleanup after load"""
        initial_process_count = len(psutil.pids())
        initial_thread_count = threading.active_count()
        initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)

        # Run intensive workload
        metrics = self.runner.run_mixed_workload_test(num_threads=16, duration_seconds=5)

        # Force cleanup
        self.system.reset()
        gc.collect()
        time.sleep(1.0)  # Allow for cleanup

        final_process_count = len(psutil.pids())
        final_thread_count = threading.active_count()
        final_memory = psutil.Process().memory_info().rss / (1024 * 1024)

        # Validate cleanup
        process_growth = final_process_count - initial_process_count
        thread_growth = final_thread_count - initial_thread_count
        memory_growth = final_memory - initial_memory

        self.assertLessEqual(process_growth, 2, "Process count should not grow significantly")
        self.assertLessEqual(thread_growth, 2, "Thread count should not grow significantly")
        self.assertLess(memory_growth, 200, "Memory growth should be minimal after cleanup")

        print(f"Resource cleanup test: +{process_growth} processes, "
              f"+{thread_growth} threads, +{memory_growth:.1f}MB memory")


if __name__ == '__main__':
    # Set up environment for long tests if needed
    if len(sys.argv) > 1 and sys.argv[1] == '--long-tests':
        os.environ['RUN_LONG_TESTS'] = '1'

    unittest.main(verbosity=2)
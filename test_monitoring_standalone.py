#!/usr/bin/env python3
"""
Standalone test for monitoring system components.
Tests core monitoring functionality without dependencies on other parallel modules.
"""

import asyncio
import json
import time
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock
import threading
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock dependencies that aren't available
class MockModels:
    pass

sys.modules['src.backtest.parallel.models'] = MockModels()
sys.modules['src.backtest.parallel.process_pool'] = Mock()
sys.modules['src.backtest.parallel.task_distributor'] = Mock()
sys.modules['src.backtest.parallel.ipc_manager'] = Mock()
sys.modules['src.backtest.parallel.fault_handler'] = Mock()
sys.modules['src.backtest.parallel.parallel_engine'] = Mock()
sys.modules['src.backtest.parallel.streaming_loader'] = Mock()
sys.modules['src.backtest.parallel.chunker'] = Mock()
sys.modules['src.backtest.parallel.memory_mapper'] = Mock()
sys.modules['src.backtest.parallel.shared_memory'] = Mock()

# Now import monitoring components
try:
    from backtest.parallel.monitor import (
        ResourceMonitor, ProgressTracker, AlertManager, BacktestMonitor,
        AlertLevel, TaskProgress, ResourceMetrics, Alert
    )
    from backtest.parallel.performance_metrics import (
        PerformanceMetricsCollector, TaskTimer, ThroughputMetrics
    )
    MONITORING_AVAILABLE = True
except ImportError as e:
    print(f"Monitoring modules not available: {e}")
    MONITORING_AVAILABLE = False


class TestResourceMonitor(unittest.TestCase):
    """Test resource monitoring functionality."""

    def setUp(self):
        if not MONITORING_AVAILABLE:
            self.skipTest("Monitoring modules not available")
        self.monitor = ResourceMonitor(sampling_interval=0.1, history_size=100)

    def tearDown(self):
        if hasattr(self, 'monitor'):
            self.monitor.stop()

    def test_start_stop(self):
        """Test monitor start/stop functionality."""
        self.assertFalse(self.monitor._running)

        self.monitor.start()
        self.assertTrue(self.monitor._running)

        # Let it collect some data
        time.sleep(0.3)

        self.monitor.stop()
        self.assertFalse(self.monitor._running)

    def test_metrics_collection(self):
        """Test metrics collection."""
        self.monitor.start()
        time.sleep(0.3)  # Collect some samples

        metrics = self.monitor.get_current_metrics()
        self.assertIsNotNone(metrics)
        self.assertIsInstance(metrics.cpu_percent, float)
        self.assertIsInstance(metrics.memory_percent, float)
        self.assertIsInstance(metrics.memory_mb, int)

        # Verify metrics are reasonable
        self.assertGreaterEqual(metrics.cpu_percent, 0)
        self.assertLessEqual(metrics.cpu_percent, 100)
        self.assertGreaterEqual(metrics.memory_percent, 0)
        self.assertLessEqual(metrics.memory_percent, 100)


class TestProgressTracker(unittest.TestCase):
    """Test progress tracking functionality."""

    def setUp(self):
        if not MONITORING_AVAILABLE:
            self.skipTest("Monitoring modules not available")
        self.tracker = ProgressTracker()

    def test_task_registration(self):
        """Test task registration."""
        self.tracker.register_task("task1", "backtest", 60.0)

        task = self.tracker.get_task_status("task1")
        self.assertIsNotNone(task)
        self.assertEqual(task.task_id, "task1")
        self.assertEqual(task.task_type, "backtest")
        self.assertEqual(task.status, "pending")

    def test_task_lifecycle(self):
        """Test complete task lifecycle."""
        # Register task
        self.tracker.register_task("task1", "optimization")
        self.assertEqual(self.tracker.get_task_status("task1").status, "pending")

        # Start task
        self.tracker.start_task("task1")
        self.assertEqual(self.tracker.get_task_status("task1").status, "running")
        self.assertIsNotNone(self.tracker.get_task_status("task1").started_at)

        # Update progress
        self.tracker.update_progress("task1", 50.0)
        self.assertEqual(self.tracker.get_task_status("task1").progress_percent, 50.0)

        # Complete task
        self.tracker.complete_task("task1", True)
        self.assertIsNone(self.tracker.get_task_status("task1"))  # Moved to history

        # Check overall progress
        progress = self.tracker.get_overall_progress()
        self.assertEqual(progress["total_tasks"], 1)
        self.assertEqual(progress["completed_tasks"], 1)
        self.assertEqual(progress["overall_progress_percent"], 100.0)

    def test_eta_calculation(self):
        """Test ETA calculation for running tasks."""
        self.tracker.register_task("task1", "backtest")
        self.tracker.start_task("task1")

        # Simulate some progress
        time.sleep(0.1)
        self.tracker.update_progress("task1", 25.0)

        task = self.tracker.get_task_status("task1")
        self.assertIsNotNone(task.estimated_completion)
        self.assertGreater(task.estimated_completion, datetime.now())

    def test_multiple_tasks(self):
        """Test handling multiple tasks."""
        # Register multiple tasks
        for i in range(5):
            self.tracker.register_task(f"task{i}", "backtest")
            self.tracker.start_task(f"task{i}")

        # Complete some tasks
        for i in range(3):
            self.tracker.complete_task(f"task{i}", True)

        progress = self.tracker.get_overall_progress()
        self.assertEqual(progress["total_tasks"], 5)
        self.assertEqual(progress["completed_tasks"], 3)
        self.assertEqual(progress["running_tasks"], 2)
        self.assertEqual(progress["overall_progress_percent"], 60.0)


class TestAlertManager(unittest.TestCase):
    """Test alert management functionality."""

    def setUp(self):
        if not MONITORING_AVAILABLE:
            self.skipTest("Monitoring modules not available")
        self.alert_manager = AlertManager()
        self.alerts_received = []

        # Add callback to track alerts
        def alert_callback(alert):
            self.alerts_received.append(alert)

        self.alert_manager.alert_callbacks.append(alert_callback)

    def test_alert_creation(self):
        """Test alert creation and storage."""
        alert_id = self.alert_manager.create_alert(
            AlertLevel.WARNING,
            "Test warning message",
            "test_source"
        )

        self.assertIn(alert_id, self.alert_manager.alerts)
        self.assertEqual(len(self.alerts_received), 1)

        alert = self.alert_manager.alerts[alert_id]
        self.assertEqual(alert.level, AlertLevel.WARNING)
        self.assertEqual(alert.message, "Test warning message")
        self.assertEqual(alert.source, "test_source")
        self.assertFalse(alert.acknowledged)
        self.assertFalse(alert.resolved)

    def test_alert_acknowledgment(self):
        """Test alert acknowledgment."""
        alert_id = self.alert_manager.create_alert(
            AlertLevel.ERROR,
            "Test error message"
        )

        self.alert_manager.acknowledge_alert(alert_id)
        self.assertTrue(self.alert_manager.alerts[alert_id].acknowledged)

    def test_alert_resolution(self):
        """Test alert resolution."""
        alert_id = self.alert_manager.create_alert(
            AlertLevel.INFO,
            "Test info message"
        )

        self.alert_manager.resolve_alert(alert_id)
        self.assertTrue(self.alert_manager.alerts[alert_id].resolved)

    def test_active_alerts_filtering(self):
        """Test filtering active alerts by level."""
        # Create alerts of different levels
        self.alert_manager.create_alert(AlertLevel.INFO, "Info message")
        self.alert_manager.create_alert(AlertLevel.WARNING, "Warning message")
        self.alert_manager.create_alert(AlertLevel.ERROR, "Error message")
        self.alert_manager.create_alert(AlertLevel.WARNING, "Another warning")

        # Get all active alerts
        all_active = self.alert_manager.get_active_alerts()
        self.assertEqual(len(all_active), 4)

        # Get only warnings
        warnings = self.alert_manager.get_active_alerts(AlertLevel.WARNING)
        self.assertEqual(len(warnings), 2)
        self.assertTrue(all(w.level == AlertLevel.WARNING for w in warnings))


class TestPerformanceMetricsCollector(unittest.TestCase):
    """Test performance metrics collection."""

    def setUp(self):
        if not MONITORING_AVAILABLE:
            self.skipTest("Monitoring modules not available")
        self.collector = PerformanceMetricsCollector(history_size=100)

    def tearDown(self):
        if hasattr(self, 'collector'):
            self.collector.stop_collection()

    def test_task_completion_recording(self):
        """Test recording task completions."""
        self.collector.record_task_completion(
            task_type="backtest",
            duration_ms=150.0,
            success=True,
            data_size_mb=10.5
        )

        self.assertEqual(len(self.collector.task_completion_times), 1)
        self.assertEqual(len(self.collector.latency_samples), 1)
        self.assertEqual(self.collector.completed_tasks_count, 1)
        self.assertEqual(self.collector.data_processed_mb, 10.5)

    def test_throughput_calculation(self):
        """Test throughput metrics calculation."""
        # Record some tasks with different timestamps
        base_time = time.time()
        for i in range(5):
            self.collector.record_task_completion(
                "test_task", 100.0, True
            )
            time.sleep(0.01)  # Small delay

        throughput = self.collector.calculate_throughput_metrics()
        self.assertIsInstance(throughput, ThroughputMetrics)
        self.assertGreater(throughput.tasks_per_second, 0)

    def test_latency_metrics(self):
        """Test latency metrics calculation."""
        # Record tasks with varying latencies
        latencies = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for latency in latencies:
            self.collector.record_task_completion("test_task", latency, True)

        latency_metrics = self.collector.calculate_latency_metrics()
        self.assertAlmostEqual(latency_metrics.average_latency_ms, 55.0, places=1)
        self.assertEqual(latency_metrics.min_latency_ms, 10.0)
        self.assertEqual(latency_metrics.max_latency_ms, 100.0)

    def test_task_timer_context_manager(self):
        """Test TaskTimer context manager."""
        with TaskTimer(self.collector, "test_task"):
            time.sleep(0.01)  # Simulate work

        self.assertEqual(len(self.collector.latency_samples), 1)
        self.assertEqual(self.collector.completed_tasks_count, 1)


def run_monitoring_tests():
    """Run all monitoring system tests."""
    print("=== MONITORING SYSTEM TEST SUITE ===\n")

    if not MONITORING_AVAILABLE:
        print("❌ Monitoring modules are not available. Skipping tests.")
        return False

    test_classes = [
        TestResourceMonitor,
        TestProgressTracker,
        TestAlertManager,
        TestPerformanceMetricsCollector
    ]

    total_tests = 0
    total_failures = 0
    total_errors = 0

    for test_class in test_classes:
        print(f"Running {test_class.__name__}...")

        # Create test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(test_class)

        # Run tests
        runner = unittest.TextTestRunner(verbosity=1)
        result = runner.run(suite)

        total_tests += result.testsRun
        total_failures += len(result.failures)
        total_errors += len(result.errors)

        if result.failures:
            print(f"  ❌ {len(result.failures)} failures")
            for test, failure in result.failures[:3]:  # Show first 3 failures
                failure_lines = failure.split('\n')
                for line in failure_lines:
                    if 'AssertionError' in line:
                        print(f"    - {test}: {line.strip()}")
                        break

        if result.errors:
            print(f"  ❌ {len(result.errors)} errors")
            for test, error in result.errors[:3]:  # Show first 3 errors
                error_lines = error.split('\n')
                for line in error_lines:
                    if 'Exception:' in line or 'Error:' in line:
                        print(f"    - {test}: {line.strip()}")
                        break

        if not result.failures and not result.errors:
            print(f"  ✅ All {result.testsRun} tests passed")

        print()

    # Summary
    print(f"=== TEST SUMMARY ===")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {total_tests - total_failures - total_errors}")
    print(f"Failures: {total_failures}")
    print(f"Errors: {total_errors}")

    if total_failures == 0 and total_errors == 0:
        print("\n🎉 ALL TESTS PASSED! Monitoring system is working correctly.")
        return True
    else:
        print(f"\n⚠️ {total_failures + total_errors} tests failed. Review the output above.")
        return False


def demo_monitoring_functionality():
    """Demonstrate monitoring functionality."""
    print("\n=== MONITORING FUNCTIONALITY DEMO ===\n")

    if not MONITORING_AVAILABLE:
        print("❌ Monitoring modules not available for demo.")
        return

    # Create components
    progress_tracker = ProgressTracker()
    alert_manager = AlertManager()
    metrics_collector = PerformanceMetricsCollector()

    print("1. Task Progress Tracking:")
    print("   Registering 3 tasks...")

    # Register tasks
    tasks = [
        ("backtest_001", "backtest"),
        ("optimize_001", "optimization"),
        ("analysis_001", "analysis")
    ]

    for task_id, task_type in tasks:
        progress_tracker.register_task(task_id, task_type, estimated_duration=30.0)

    print(f"   {len(tasks)} tasks registered")

    print("\n2. Simulating Task Execution:")
    for task_id, task_type in tasks:
        print(f"   Starting {task_id} ({task_type})...")
        progress_tracker.start_task(task_id)

        # Simulate work with progress updates
        with TaskTimer(metrics_collector, task_type):
            for progress in [25, 50, 75, 100]:
                progress_tracker.update_progress(task_id, progress)
                print(f"     Progress: {progress}%")
                time.sleep(0.1)  # Simulate work

        progress_tracker.complete_task(task_id, True)
        print(f"   ✅ {task_id} completed")

    print("\n3. Progress Summary:")
    overall_progress = progress_tracker.get_overall_progress()
    for key, value in overall_progress.items():
        if key == "estimated_completion" and value:
            print(f"   {key}: {value}")
        else:
            print(f"   {key}: {value}")

    print("\n4. Performance Metrics:")
    snapshot = metrics_collector.get_performance_snapshot()
    print(f"   Completed tasks: {snapshot.completed_tasks}")
    print(f"   Failed tasks: {snapshot.failed_tasks}")
    print(f"   Average throughput: {snapshot.throughput.average_throughput:.2f} tasks/sec")
    print(f"   P95 latency: {snapshot.latency.p95_latency_ms:.2f} ms")

    print("\n5. Alert System:")
    # Create some test alerts
    alerts = [
        (AlertLevel.INFO, "System started successfully"),
        (AlertLevel.WARNING, "CPU usage approaching threshold"),
        (AlertLevel.ERROR, "Task failed: invalid parameters")
    ]

    for level, message in alerts:
        alert_id = alert_manager.create_alert(level, message, "demo")
        print(f"   Created {level.value} alert: {message}")

    active_alerts = alert_manager.get_active_alerts()
    print(f"   Total active alerts: {len(active_alerts)}")
    print(f"   Critical alerts: {len(alert_manager.get_active_alerts(AlertLevel.CRITICAL))}")
    print(f"   Warnings: {len(alert_manager.get_active_alerts(AlertLevel.WARNING))}")

    print("\n✅ Demo completed successfully!")


if __name__ == "__main__":
    # Run tests
    success = run_monitoring_tests()

    # Run demo
    demo_monitoring_functionality()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
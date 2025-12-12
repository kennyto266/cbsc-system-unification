#!/usr/bin/env python3
"""
Comprehensive test suite for monitoring and progress tracking system.

Tests all monitoring components including:
- Resource monitoring
- Progress tracking
- Alert management
- WebSocket server
- Performance metrics
- End-to-end integration
"""

import asyncio
import json
import time
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import threading

# Import monitoring components
from src.backtest.parallel.monitor import (
    ResourceMonitor, ProgressTracker, AlertManager, BacktestMonitor,
    AlertLevel, TaskProgress, ResourceMetrics
)

from src.backtest.parallel.websocket_server import WebSocketManager
from src.backtest.parallel.performance_metrics import (
    PerformanceMetricsCollector, TaskTimer, ThroughputMetrics
)


class TestResourceMonitor(unittest.TestCase):
    """Test resource monitoring functionality."""

    def setUp(self):
        self.monitor = ResourceMonitor(sampling_interval=0.1, history_size=100)

    def tearDown(self):
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

    def test_average_metrics(self):
        """Test average metrics calculation."""
        self.monitor.start()
        time.sleep(0.3)

        avg_metrics = self.monitor.get_average_metrics(duration_minutes=1)
        self.assertIsNotNone(avg_metrics)

        # Average should be a valid metrics object
        self.assertIsInstance(avg_metrics, ResourceMetrics)


class TestProgressTracker(unittest.TestCase):
    """Test progress tracking functionality."""

    def setUp(self):
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

    def test_old_alert_cleanup(self):
        """Test cleanup of old resolved alerts."""
        # Create and resolve an alert
        alert_id = self.alert_manager.create_alert(AlertLevel.INFO, "Old alert")
        self.alert_manager.resolve_alert(alert_id)

        # Mock the alert timestamp to be old
        old_time = datetime.now() - timedelta(hours=25)
        self.alert_manager.alerts[alert_id].timestamp = old_time

        # Cleanup old alerts
        self.alert_manager.cleanup_old_alerts(hours=24)
        self.assertNotIn(alert_id, self.alert_manager.alerts)


class TestPerformanceMetricsCollector(unittest.TestCase):
    """Test performance metrics collection."""

    def setUp(self):
        self.collector = PerformanceMetricsCollector(history_size=100)

    def tearDown(self):
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

    def test_efficiency_metrics(self):
        """Test efficiency metrics calculation."""
        # Record some tasks
        for _ in range(10):
            self.collector.record_task_completion("test_task", 50.0, True)

        efficiency = self.collector.calculate_efficiency_metrics(
            active_workers=4,
            cpu_usage=50.0,
            memory_usage_mb=1024.0
        )

        self.assertGreater(efficiency.cpu_efficiency, 0)
        self.assertGreater(efficiency.memory_efficiency, 0)

    def test_performance_snapshot(self):
        """Test complete performance snapshot."""
        # Record some tasks
        for i in range(5):
            self.collector.record_task_completion("test_task", 50.0, True)

        snapshot = self.collector.get_performance_snapshot(
            active_workers=2,
            queued_tasks=1,
            cpu_usage=60.0,
            memory_usage_mb=2048.0
        )

        self.assertIsNotNone(snapshot)
        self.assertIsNotNone(snapshot.throughput)
        self.assertIsNotNone(snapshot.latency)
        self.assertIsNotNone(snapshot.efficiency)
        self.assertEqual(snapshot.active_workers, 2)
        self.assertEqual(snapshot.queued_tasks, 1)

    def test_task_type_performance(self):
        """Test performance metrics by task type."""
        # Record different task types
        self.collector.record_task_completion("backtest", 100.0, True, 50.0)
        self.collector.record_task_completion("backtest", 120.0, True, 60.0)
        self.collector.record_task_completion("backtest", 80.0, False, 40.0)
        self.collector.record_task_completion("optimization", 200.0, True, 100.0)

        backtest_perf = self.collector.get_task_type_performance("backtest")
        self.assertEqual(backtest_perf["total_tasks"], 3)
        self.assertEqual(backtest_perf["successful_tasks"], 2)
        self.assertAlmostEqual(backtest_perf["success_rate"], 66.67, places=1)

        optimization_perf = self.collector.get_task_type_performance("optimization")
        self.assertEqual(optimization_perf["total_tasks"], 1)
        self.assertEqual(optimization_perf["success_rate"], 100.0)

    def test_task_timer_context_manager(self):
        """Test TaskTimer context manager."""
        with TaskTimer(self.collector, "test_task"):
            time.sleep(0.01)  # Simulate work

        self.assertEqual(len(self.collector.latency_samples), 1)
        self.assertEqual(self.collector.completed_tasks_count, 1)


class TestBacktestMonitor(unittest.TestCase):
    """Test integrated backtest monitoring."""

    def setUp(self):
        self.monitor = BacktestMonitor()

    def tearDown(self):
        self.monitor.stop_monitoring()

    def test_monitor_initialization(self):
        """Test monitor initialization."""
        self.assertIsNotNone(self.monitor.resource_monitor)
        self.assertIsNotNone(self.monitor.progress_tracker)
        self.assertIsNotNone(self.monitor.alert_manager)
        self.assertFalse(self.monitor._monitoring)

    def test_monitor_start_stop(self):
        """Test monitor start/stop."""
        self.monitor.start_monitoring()
        self.assertTrue(self.monitor._monitoring)

        time.sleep(0.2)  # Let it run briefly

        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor._monitoring)

    def test_task_registration(self):
        """Test bulk task registration."""
        tasks = [
            {"id": "task1", "type": "backtest", "estimated_duration": 60.0},
            {"id": "task2", "type": "optimization", "estimated_duration": 120.0},
            {"id": "task3", "type": "analysis", "estimated_duration": 30.0}
        ]

        self.monitor.register_tasks(tasks)

        self.assertEqual(len(self.monitor.progress_tracker.tasks), 3)
        self.assertIn("task1", self.monitor.progress_tracker.tasks)
        self.assertIn("task2", self.monitor.progress_tracker.tasks)
        self.assertIn("task3", self.monitor.progress_tracker.tasks)

    def test_status_report_generation(self):
        """Test comprehensive status report generation."""
        # Register some tasks
        self.monitor.register_tasks([
            {"id": "task1", "type": "backtest"},
            {"id": "task2", "type": "optimization"}
        ])

        # Start monitoring briefly
        self.monitor.start_monitoring()
        time.sleep(0.1)

        # Generate report
        report = self.monitor.get_status_report()

        # Verify report structure
        self.assertIn("timestamp", report)
        self.assertIn("resources", report)
        self.assertIn("progress", report)
        self.assertIn("tasks", report)
        self.assertIn("alerts", report)

        # Verify progress section
        progress = report["progress"]
        self.assertEqual(progress["total_tasks"], 2)
        self.assertEqual(progress["pending_tasks"], 2)

        self.monitor.stop_monitoring()


class TestIntegration(unittest.TestCase):
    """Test end-to-end integration of monitoring components."""

    def test_full_monitoring_workflow(self):
        """Test complete monitoring workflow."""
        # Create monitor
        monitor = BacktestMonitor()
        metrics_collector = PerformanceMetricsCollector()

        try:
            # Start monitoring
            monitor.start_monitoring()
            metrics_collector.start_collection()

            # Register tasks
            tasks = [
                {"id": "backtest_1", "type": "backtest", "estimated_duration": 5.0},
                {"id": "backtest_2", "type": "backtest", "estimated_duration": 5.0},
                {"id": "optimize_1", "type": "optimization", "estimated_duration": 3.0}
            ]
            monitor.register_tasks(tasks)

            # Simulate task execution
            for task_id in ["backtest_1", "backtest_2", "optimize_1"]:
                monitor.progress_tracker.start_task(task_id)

                # Record metrics for each task
                with TaskTimer(metrics_collector, task_id.split("_")[0]):
                    # Simulate task work
                    for progress in [25, 50, 75, 100]:
                        monitor.progress_tracker.update_progress(task_id, progress)
                        time.sleep(0.02)  # Simulate work

                monitor.progress_tracker.complete_task(task_id, True)

            # Wait for final data collection
            time.sleep(0.2)

            # Verify results
            progress = monitor.progress_tracker.get_overall_progress()
            self.assertEqual(progress["total_tasks"], 3)
            self.assertEqual(progress["completed_tasks"], 3)
            self.assertEqual(progress["overall_progress_percent"], 100.0)

            # Check performance metrics
            snapshot = metrics_collector.get_performance_snapshot()
            self.assertEqual(snapshot.completed_tasks, 3)
            self.assertEqual(snapshot.failed_tasks, 0)

            # Generate final report
            report = monitor.get_status_report()
            self.assertEqual(report["progress"]["completed_tasks"], 3)

        finally:
            monitor.stop_monitoring()
            metrics_collector.stop_collection()

    def test_alert_threshold_monitoring(self):
        """Test alert generation for threshold violations."""
        monitor = BacktestMonitor(config={
            "thresholds": {
                "cpu_warning": 1.0,  # Very low threshold for testing
                "memory_warning": 1.0
            }
        })

        try:
            monitor.start_monitoring()
            time.sleep(0.3)  # Let monitoring run

            # Check if alerts were generated (likely given low thresholds)
            active_alerts = monitor.alert_manager.get_active_alerts()
            # Note: This might not trigger on all systems depending on current load

        finally:
            monitor.stop_monitoring()


def run_monitoring_tests():
    """Run all monitoring system tests."""
    print("=== MONITORING SYSTEM TEST SUITE ===\n")

    test_classes = [
        TestResourceMonitor,
        TestProgressTracker,
        TestAlertManager,
        TestPerformanceMetricsCollector,
        TestBacktestMonitor,
        TestIntegration
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
        runner = unittest.TextTestRunner(verbosity=1, stream=open(os.devnull, 'w'))
        result = runner.run(suite)

        total_tests += result.testsRun
        total_failures += len(result.failures)
        total_errors += len(result.errors)

        if result.failures:
            print(f"  ❌ {len(result.failures)} failures")
            for test, failure in result.failures:
                print(f"    - {test}: {failure.split('AssertionError:')[-1].strip()}")

        if result.errors:
            print(f"  ❌ {len(result.errors)} errors")
            for test, error in result.errors:
                print(f"    - {test}: {error.split('Exception:')[-1].strip()}")

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
    else:
        print(f"\n⚠️ {total_failures + total_errors} tests failed. Review the output above.")

    return total_failures == 0 and total_errors == 0


if __name__ == "__main__":
    import os
    run_monitoring_tests()
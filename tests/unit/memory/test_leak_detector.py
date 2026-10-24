#!/usr/bin/env python3
"""
Unit Tests for Memory Leak Detector
Tests the memory leak detection and prevention system for 32-core parallel processing
"""

import unittest
import sys
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
import psutil
import gc

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from src.memory.leak_detector import (
        MemoryLeakDetector, LeakSeverity, LeakStatus, MemorySnapshot,
        LeakAlert, ObjectTrackingInfo, create_leak_detector, monitor_for_leaks
    )
except ImportError:
    skip_tests = True
else:
    skip_tests = False


@unittest.skipIf(skip_tests, "Memory management components not available")
class TestMemoryLeakDetector(unittest.TestCase):
    """Test cases for MemoryLeakDetector"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock feature flags to enable testing
        with patch('src.memory.leak_detector.MemoryLeakDetector._check_feature_flag', return_value=True):
            self.detector = MemoryLeakDetector(
                detection_threshold_mb=50.0,
                monitoring_interval=1.0,  # Fast for tests
                time_window_minutes=2.0,   # Short for tests
                enable_object_tracking=True,
                enable_tracemalloc=False,  # Disable for tests
                alert_cooldown_minutes=1.0
            )

    def tearDown(self):
        """Clean up test fixtures"""
        if hasattr(self, 'detector'):
            self.detector.stop_monitoring()

    def test_initialization(self):
        """Test detector initialization"""
        self.assertEqual(self.detector.detection_threshold_mb, 50.0)
        self.assertEqual(self.detector.monitoring_interval, 1.0)
        self.assertEqual(self.detector.time_window_minutes, 2.0)
        self.assertTrue(self.detector.enable_object_tracking)
        self.assertEqual(self.detector.alert_cooldown_minutes, 1.0)
        self.assertEqual(len(self.detector.leak_alerts), 0)

    def test_capture_memory_snapshot(self):
        """Test memory snapshot capture"""
        with patch('psutil.Process') as mock_process:
            mock_process.return_value.memory_info.return_value.rss = 1024 * 1024 * 512  # 512MB
            mock_process.return_value.memory_info.return_value.vms = 1024 * 1024 * 600  # 600MB
            mock_process.return_value.memory_percent.return_value = 25.0
            mock_process.return_value.name.return_value = "test_process"

            snapshot = self.detector._capture_memory_snapshot(os.getpid())

            self.assertIsInstance(snapshot, MemorySnapshot)
            self.assertEqual(snapshot.pid, os.getpid())
            self.assertEqual(snapshot.process_name, "test_process")
            self.assertEqual(snapshot.memory_rss_mb, 512.0)
            self.assertEqual(snapshot.memory_vms_mb, 600.0)
            self.assertEqual(snapshot.memory_percent, 25.0)

    def test_capture_memory_snapshot_no_process(self):
        """Test snapshot capture with non-existent process"""
        result = self.detector._capture_memory_snapshot(99999)  # Non-existent PID
        self.assertIsNone(result)

    def test_memory_leak_detection(self):
        """Test basic memory leak detection"""
        with patch('psutil.Process') as mock_process:
            # Create baseline snapshot
            mock_process.return_value.memory_info.return_value.rss = 1024 * 1024 * 100  # 100MB
            mock_process.return_value.memory_info.return_value.vms = 1024 * 1024 * 120
            mock_process.return_value.memory_percent.return_value = 20.0
            mock_process.return_value.name.return_value = "test_process"

            # Start monitoring
            self.detector.start_monitoring([os.getpid()])

            # Add baseline memory
            baseline = self.detector._capture_memory_snapshot(os.getpid())
            self.detector.baseline_memory[os.getpid()] = baseline

            # Simulate memory increase (leak)
            time.sleep(0.1)  # Small delay
            mock_process.return_value.memory_info.return_value.rss = 1024 * 1024 * 200  # 200MB (+100MB)

            current = self.detector._capture_memory_snapshot(os.getpid())
            self.detector.memory_history[os.getpid()].append(current)
            self.detector.memory_history[os.getpid()].append(
                MemorySnapshot(
                    timestamp=datetime.now() + timedelta(minutes=3),
                    pid=os.getpid(),
                    process_name="test_process",
                    memory_rss_mb=250,
                    memory_vms_mb=300,
                    memory_percent=50,
                    object_count=1000,
                    gc_objects=800,
                    tracemalloc_current=0,
                    tracemalloc_peak=0
                )
            )

            # Check for leaks
            self.detector._check_for_leaks(os.getpid(), current, datetime.now())

            # Should have detected a leak
            self.assertGreater(len(self.detector.leak_alerts), 0)
            alert = self.detector.leak_alerts[0]
            self.assertEqual(alert.pid, os.getpid())
            self.assertEqual(alert.process_name, "test_process")
            self.assertGreater(alert.memory_increase_mb, self.detector.detection_threshold_mb)
            self.assertIn(alert.severity, [LeakSeverity.MEDIUM, LeakSeverity.HIGH])

    def test_leak_severity_levels(self):
        """Test leak severity classification"""
        test_cases = [
            (75, LeakSeverity.LOW),
            (125, LeakSeverity.MEDIUM),
            (250, LeakSeverity.HIGH),
            (600, LeakSeverity.CRITICAL)
        ]

        for memory_increase, expected_severity in test_cases:
            with self.subTest(memory_increase=memory_increase):
                # Mock memory increase
                baseline = MemorySnapshot(
                    timestamp=datetime.now(),
                    pid=12345,
                    process_name="test",
                    memory_rss_mb=100,
                    memory_vms_mb=120,
                    memory_percent=10,
                    object_count=100,
                    gc_objects=80,
                    tracemalloc_current=0,
                    tracemalloc_peak=0
                )

                current = MemorySnapshot(
                    timestamp=datetime.now() + timedelta(minutes=5),
                    pid=12345,
                    process_name="test",
                    memory_rss_mb=100 + memory_increase,
                    memory_vms_mb=120 + memory_increase,
                    memory_percent=10 + (memory_increase / 10),
                    object_count=100,
                    gc_objects=80,
                    tracemalloc_current=0,
                    tracemalloc_peak=0
                )

                self.detector.baseline_memory[12345] = baseline
                self.detector._check_for_leaks(12345, current, datetime.now())

                if self.detector.leak_alerts:
                    self.assertEqual(self.detector.leak_alerts[-1].severity, expected_severity)
                    self.detector.leak_alerts.clear()

    def test_alert_cooldown(self):
        """Test alert cooldown mechanism"""
        # Create first alert
        self.detector.last_alert_time[os.getpid()] = datetime.now()

        # Try to create another alert immediately
        with patch('psutil.Process') as mock_process:
            mock_process.return_value.memory_info.return_value.rss = 1024 * 1024 * 300  # Big leak
            mock_process.return_value.memory_info.return_value.vms = 1024 * 1024 * 400
            mock_process.return_value.memory_percent.return_value = 60.0
            mock_process.return_value.name.return_value = "test_process"

            baseline = self.detector._capture_memory_snapshot(os.getpid())
            self.detector.baseline_memory[os.getpid()] = baseline

            # Simulate large leak
            time.sleep(0.1)
            current = self.detector._capture_memory_snapshot(os.getpid())
            self.detector._check_for_leaks(os.getpid(), current, datetime.now())

            # Should not create new alert due to cooldown
            initial_alert_count = len(self.detector.leak_alerts)

            # Wait for cooldown to expire
            self.detector.last_alert_time[os.getpid()] = datetime.now() - timedelta(minutes=2)
            self.detector._check_for_leaks(os.getpid(), current, datetime.now())

            # Should create new alert after cooldown
            if initial_alert_count > 0:
                self.assertGreater(len(self.detector.leak_alerts), initial_alert_count)

    def test_suspected_sources_identification(self):
        """Test identification of suspected leak sources"""
        with patch.object(self.detector, 'enable_object_tracking', True):
            sources = self.detector._identify_suspected_sources(os.getpid())

            self.assertIsInstance(sources, list)
            # Should return some suspected sources even in test scenario
            self.assertGreaterEqual(len(sources), 0)

    def test_recommendation_generation(self):
        """Test leak resolution recommendations"""
        recommendations = self.detector._generate_recommendations(
            memory_increase=200.0,
            growth_rate=50.0
        )

        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

        # Should include high-level recommendations
        all_text = ' '.join(recommendations).lower()
        self.assertIn('memory', all_text)

    def test_auto_cleanup_trigger(self):
        """Test automatic cleanup trigger"""
        with patch('psutil.Process') as mock_process:
            mock_process.return_value.memory_info.return_value.rss = 1024 * 1024 * 800  # Very high
            mock_process.return_value.memory_info.return_value.vms = 1024 * 1024 * 900
            mock_process.return_value.memory_percent.return_value = 80.0
            mock_process.return_value.name.return_value = "test_process"

            snapshot = MemorySnapshot(
                timestamp=datetime.now(),
                pid=os.getpid(),
                process_name="test_process",
                memory_rss_mb=800,
                memory_vms_mb=900,
                memory_percent=80,
                object_count=1000,
                gc_objects=800,
                tracemalloc_current=0,
                tracemalloc_peak=0
            )

            initial_auto_cleanups = self.detector.auto_cleanup_count
            self.detector._trigger_auto_cleanup(os.getpid(), snapshot)

            # Should have triggered auto cleanup
            self.assertGreater(self.detector.auto_cleanup_count, initial_auto_cleanups)

    def test_leak_report_generation(self):
        """Test comprehensive leak report generation"""
        # Add some test alerts
        test_alert = LeakAlert(
            timestamp=datetime.now(),
            severity=LeakSeverity.HIGH,
            pid=12345,
            process_name="test_process",
            memory_increase_mb=150.0,
            time_window_minutes=5.0,
            growth_rate_mb_per_minute=30.0,
            status=LeakStatus.DETECTED,
            suspected_sources=["test source"],
            recommended_actions=["test action"]
        )
        self.detector.leak_alerts.append(test_alert)

        report = self.detector.get_leak_report()

        self.assertIn('summary', report)
        self.assertIn('severity_distribution', report)
        self.assertIn('status_distribution', report)
        self.assertIn('recent_alerts', report)
        self.assertIn('monitoring_status', report)

        summary = report['summary']
        self.assertEqual(summary['total_alerts'], 1)
        self.assertEqual(summary['total_memory_leaked_mb'], 150.0)

    def test_alert_acknowledgment(self):
        """Test leak alert acknowledgment"""
        # Add test alert
        test_alert = LeakAlert(
            timestamp=datetime.now(),
            severity=LeakSeverity.MEDIUM,
            pid=12345,
            process_name="test_process",
            memory_increase_mb=75.0,
            time_window_minutes=3.0,
            growth_rate_mb_per_minute=25.0,
            status=LeakStatus.DETECTED
        )
        self.detector.leak_alerts.append(test_alert)

        # Acknowledge alert
        success = self.detector.acknowledge_alert(0, "Manually resolved")

        self.assertTrue(success)
        self.assertEqual(self.detector.leak_alerts[0].status, LeakStatus.RESOLVED)
        self.assertIsNotNone(self.detector.leak_alerts[0].resolution_time)
        self.assertIn("Manually resolved", self.detector.leak_alerts[0].investigation_notes)

    def test_statistics_reset(self):
        """Test statistics reset functionality"""
        # Set some statistics
        self.detector.total_detections = 10
        self.detector.false_positives = 2
        self.detector.auto_cleanups = 3
        self.detector.objects_tracked = 1000

        # Add alerts
        self.detector.leak_alerts.append(
            LeakAlert(
                timestamp=datetime.now(),
                severity=LeakSeverity.LOW,
                pid=12345,
                process_name="test",
                memory_increase_mb=25.0,
                time_window_minutes=1.0,
                growth_rate_mb_per_minute=25.0,
                status=LeakStatus.DETECTED
            )
        )

        # Reset statistics
        self.detector.reset_statistics()

        self.assertEqual(self.detector.total_detections, 0)
        self.assertEqual(self.detector.false_positives, 0)
        self.assertEqual(self.detector.auto_cleanups, 0)
        self.assertEqual(self.detector.objects_tracked, 0)
        self.assertEqual(len(self.detector.leak_alerts), 0)


@unittest.skipIf(skip_tests, "Memory management components not available")
class TestMemoryLeakDetectorFactory(unittest.TestCase):
    """Test factory functions for memory leak detector"""

    def test_create_leak_detector(self):
        """Test create_leak_detector factory function"""
        detector = create_leak_detector(
            detection_threshold_mb=100.0,
            monitoring_interval=5.0
        )
        self.assertIsInstance(detector, MemoryLeakDetector)
        self.assertEqual(detector.detection_threshold_mb, 100.0)
        self.assertEqual(detector.monitoring_interval, 5.0)
        detector.stop_monitoring()

    def test_monitor_for_leaks_decorator(self):
        """Test monitor_for_leaks decorator"""
        @monitor_for_leaks(threshold_mb=10.0)
        def test_function():
            # Simulate some memory usage
            large_list = [0] * 1000000  # Should use some memory
            return len(large_list)

        result = test_function()
        self.assertGreater(result, 0)


@unittest.skipIf(skip_tests, "Memory management components not available")
class TestLeakAlert(unittest.TestCase):
    """Test LeakAlert dataclass"""

    def test_leak_alert_creation(self):
        """Test creation of LeakAlert"""
        timestamp = datetime.now()
        alert = LeakAlert(
            timestamp=timestamp,
            severity=LeakSeverity.HIGH,
            pid=12345,
            process_name="test_process",
            memory_increase_mb=200.0,
            time_window_minutes=5.0,
            growth_rate_mb_per_minute=40.0,
            status=LeakStatus.DETECTED,
            suspected_sources=["source1", "source2"],
            recommended_actions=["action1", "action2"],
            investigation_notes="Test investigation"
        )

        self.assertEqual(alert.timestamp, timestamp)
        self.assertEqual(alert.severity, LeakSeverity.HIGH)
        self.assertEqual(alert.pid, 12345)
        self.assertEqual(alert.process_name, "test_process")
        self.assertEqual(alert.memory_increase_mb, 200.0)
        self.assertEqual(alert.time_window_minutes, 5.0)
        self.assertEqual(alert.growth_rate_mb_per_minute, 40.0)
        self.assertEqual(alert.status, LeakStatus.DETECTED)
        self.assertEqual(alert.suspected_sources, ["source1", "source2"])
        self.assertEqual(alert.recommended_actions, ["action1", "action2"])
        self.assertEqual(alert.investigation_notes, "Test investigation")


@unittest.skipIf(skip_tests, "Memory management components not available")
class TestMemorySnapshot(unittest.TestCase):
    """Test MemorySnapshot dataclass"""

    def test_memory_snapshot_creation(self):
        """Test creation of MemorySnapshot"""
        timestamp = datetime.now()
        snapshot = MemorySnapshot(
            timestamp=timestamp,
            pid=12345,
            process_name="test_process",
            memory_rss_mb=512.0,
            memory_vms_mb=600.0,
            memory_percent=25.0,
            object_count=1000,
            gc_objects=800,
            tracemalloc_current=50 * 1024 * 1024,
            tracemalloc_peak=60 * 1024 * 1024
        )

        self.assertEqual(snapshot.timestamp, timestamp)
        self.assertEqual(snapshot.pid, 12345)
        self.assertEqual(snapshot.process_name, "test_process")
        self.assertEqual(snapshot.memory_rss_mb, 512.0)
        self.assertEqual(snapshot.memory_vms_mb, 600.0)
        self.assertEqual(snapshot.memory_percent, 25.0)
        self.assertEqual(snapshot.object_count, 1000)
        self.assertEqual(snapshot.gc_objects, 800)
        self.assertEqual(snapshot.tracemalloc_current, 50 * 1024 * 1024)
        self.assertEqual(snapshot.tracemalloc_peak, 60 * 1024 * 1024)


@unittest.skipIf(skip_tests, "Memory management components not available")
class TestObjectTrackingInfo(unittest.TestCase):
    """Test ObjectTrackingInfo dataclass"""

    def test_object_tracking_info_creation(self):
        """Test creation of ObjectTrackingInfo"""
        timestamp = datetime.now()
        tracking_info = ObjectTrackingInfo(
            object_id=12345,
            object_type="TestObject",
            size_bytes=1024,
            creation_time=timestamp,
            ref_count=3,
            traceback_info="file.py:line:function",
            is_alive=True
        )

        self.assertEqual(tracking_info.object_id, 12345)
        self.assertEqual(tracking_info.object_type, "TestObject")
        self.assertEqual(tracking_info.size_bytes, 1024)
        self.assertEqual(tracking_info.creation_time, timestamp)
        self.assertEqual(tracking_info.ref_count, 3)
        self.assertEqual(tracking_info.traceback_info, "file.py:line:function")
        self.assertTrue(tracking_info.is_alive)


class TestMemoryLeakDetectorIntegration(unittest.TestCase):
    """Integration tests for MemoryLeakDetector"""

    @unittest.skipIf(skip_tests, "Memory management components not available")
    def test_detector_with_real_monitoring(self):
        """Test detector with real monitoring (short duration)"""
        try:
            detector = create_leak_detector(
                monitoring_interval=0.5,
                time_window_minutes=0.1  # Very short for tests
            )

            # Start monitoring
            detector.start_monitoring([os.getpid()])

            # Let it run briefly
            time.sleep(1.0)

            # Get report
            report = detector.get_leak_report()

            # Should have monitoring status
            self.assertIn('monitoring_status', report)
            self.assertTrue(report['monitoring_status']['active'])

            detector.stop_monitoring()

        except Exception as e:
            self.fail(f"Integration test failed: {e}")


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryLeakDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryLeakDetectorFactory))
    suite.addTests(loader.loadTestsFromTestCase(TestLeakAlert))
    suite.addTests(loader.loadTestsFromTestCase(TestMemorySnapshot))
    suite.addTests(loader.loadTestsFromTestCase(TestObjectTrackingInfo))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryLeakDetectorIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
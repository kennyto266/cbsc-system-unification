#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Memory Leak Detector
Tests memory leak detection and prevention mechanisms
"""

import os
import sys
import time
import unittest
import threading
import tempfile
import gc
import weakref
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
import psutil
import tracemalloc

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Mock memory leak detector implementation (assuming it exists)
# This is a placeholder test file that should be adapted to the actual implementation


class MockMemoryLeakDetector:
    """Mock implementation of Memory Leak Detector for testing purposes"""

    def __init__(self, enable_tracking=True, sampling_interval=5.0):
        self.enable_tracking = enable_tracking
        self.sampling_interval = sampling_interval
        self.is_monitoring = False
        self.monitor_thread = None
        self.leak_threshold_mb = 100.0
        self.memory_snapshots = []
        self.leak_detected = False
        self.stats = {
            'total_samples': 0,
            'leaks_detected': 0,
            'max_memory_mb': 0,
            'avg_memory_mb': 0
        }

    def start_monitoring(self):
        """Start memory leak monitoring"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        if not tracemalloc.is_tracing():
            tracemalloc.start()

        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name="MemoryLeakDetector",
            daemon=True
        )
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop memory leak monitoring"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                self._take_memory_snapshot()
                self._detect_leaks()
                time.sleep(self.sampling_interval)
            except Exception as e:
                print(f"Memory monitoring error: {e}")

    def _take_memory_snapshot(self):
        """Take memory snapshot"""
        try:
            current, peak = tracemalloc.get_traced_memory()
            process = psutil.Process()
            memory_info = process.memory_info()

            snapshot = {
                'timestamp': datetime.now(),
                'traced_current_mb': current / (1024 * 1024),
                'traced_peak_mb': peak / (1024 * 1024),
                'rss_mb': memory_info.rss / (1024 * 1024),
                'vms_mb': memory_info.vms / (1024 * 1024),
                'percent': process.memory_percent()
            }

            self.memory_snapshots.append(snapshot)
            self.stats['total_samples'] += 1
            self.stats['max_memory_mb'] = max(
                self.stats['max_memory_mb'],
                snapshot['rss_mb']
            )

        except Exception as e:
            print(f"Failed to take memory snapshot: {e}")

    def _detect_leaks(self):
        """Detect memory leaks based on growth patterns"""
        if len(self.memory_snapshots) < 3:
            return

        recent_snapshots = self.memory_snapshots[-3:]
        memory_values = [s['rss_mb'] for s in recent_snapshots]

        # Check for consistent growth
        if all(memory_values[i] < memory_values[i+1] for i in range(len(memory_values)-1)):
            growth = memory_values[-1] - memory_values[0]
            if growth > self.leak_threshold_mb:
                self.leak_detected = True
                self.stats['leaks_detected'] += 1

    def get_memory_statistics(self):
        """Get current memory statistics"""
        if not self.memory_snapshots:
            return self.stats

        recent_avg = sum(s['rss_mb'] for s in self.memory_snapshots[-10:]) / min(10, len(self.memory_snapshots))
        self.stats['avg_memory_mb'] = recent_avg

        return {
            **self.stats,
            'leak_detected': self.leak_detected,
            'snapshots_count': len(self.memory_snapshots),
            'latest_memory_mb': self.memory_snapshots[-1]['rss_mb'] if self.memory_snapshots else 0
        }

    def cleanup(self):
        """Cleanup resources"""
        self.stop_monitoring()
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        self.memory_snapshots.clear()


class TestMemoryLeakDetector(unittest.TestCase):
    """Comprehensive test suite for Memory Leak Detector"""

    def setUp(self):
        """Set up test fixtures"""
        self.detector = MockMemoryLeakDetector(
            enable_tracking=True,
            sampling_interval=0.1  # Fast sampling for tests
        )

    def tearDown(self):
        """Clean up test fixtures"""
        self.detector.cleanup()

    def test_detector_initialization(self):
        """Test memory leak detector initialization"""
        self.assertTrue(self.detector.enable_tracking)
        self.assertEqual(self.detector.sampling_interval, 0.1)
        self.assertFalse(self.detector.is_monitoring)
        self.assertFalse(self.detector.leak_detected)
        self.assertEqual(self.detector.stats['total_samples'], 0)

    @patch('tracemalloc.is_tracing')
    @patch('tracemalloc.start')
    def test_start_monitoring(self, mock_tracemalloc_start, mock_is_tracing):
        """Test starting memory monitoring"""
        mock_is_tracing.return_value = False

        self.detector.start_monitoring()

        self.assertTrue(self.detector.is_monitoring)
        self.assertIsNotNone(self.detector.monitor_thread)
        mock_tracemalloc_start.assert_called_once()

    @patch('tracemalloc.is_tracing')
    @patch('tracemalloc.start')
    def test_start_monitoring_already_tracing(self, mock_tracemalloc_start, mock_is_tracing):
        """Test starting monitoring when already tracing"""
        mock_is_tracing.return_value = True

        self.detector.start_monitoring()

        self.assertTrue(self.detector.is_monitoring)
        mock_tracemalloc_start.assert_not_called()

    def test_stop_monitoring(self):
        """Test stopping memory monitoring"""
        # Start monitoring first
        self.detector.start_monitoring()
        self.assertTrue(self.detector.is_monitoring)

        # Stop monitoring
        self.detector.stop_monitoring()
        self.assertFalse(self.detector.is_monitoring)

    @patch('psutil.Process')
    @patch('tracemalloc.get_traced_memory')
    def test_take_memory_snapshot(self, mock_traced_memory, mock_process):
        """Test taking memory snapshots"""
        # Mock tracemalloc data
        mock_traced_memory.return_value = (100 * 1024 * 1024, 150 * 1024 * 1024)  # 100MB current, 150MB peak

        # Mock psutil Process
        mock_process_instance = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 200 * 1024 * 1024  # 200MB RSS
        mock_memory_info.vms = 300 * 1024 * 1024  # 300MB VMS
        mock_process_instance.memory_info.return_value = mock_memory_info
        mock_process_instance.memory_percent.return_value = 12.5
        mock_process.return_value = mock_process_instance

        # Take snapshot
        self.detector._take_memory_snapshot()

        # Verify snapshot was taken
        self.assertEqual(len(self.detector.memory_snapshots), 1)
        self.assertEqual(self.detector.stats['total_samples'], 1)

        snapshot = self.detector.memory_snapshots[0]
        self.assertEqual(snapshot['traced_current_mb'], 100.0)
        self.assertEqual(snapshot['traced_peak_mb'], 150.0)
        self.assertEqual(snapshot['rss_mb'], 200.0)
        self.assertEqual(snapshot['vms_mb'], 300.0)
        self.assertEqual(snapshot['percent'], 12.5)

    def test_leak_detection_no_leak(self):
        """Test leak detection with no actual leak"""
        # Create snapshots with decreasing memory (no leak)
        self.detector.memory_snapshots = [
            {'rss_mb': 100.0, 'timestamp': datetime.now()},
            {'rss_mb': 95.0, 'timestamp': datetime.now()},
            {'rss_mb': 90.0, 'timestamp': datetime.now()}
        ]

        self.detector._detect_leaks()

        self.assertFalse(self.detector.leak_detected)
        self.assertEqual(self.detector.stats['leaks_detected'], 0)

    def test_leak_detection_with_leak(self):
        """Test leak detection with actual memory leak"""
        # Create snapshots with increasing memory (leak detected)
        self.detector.memory_snapshots = [
            {'rss_mb': 100.0, 'timestamp': datetime.now()},
            {'rss_mb': 200.0, 'timestamp': datetime.now()},
            {'rss_mb': 300.0, 'timestamp': datetime.now()}
        ]

        # Set low threshold for testing
        self.detector.leak_threshold_mb = 50.0

        self.detector._detect_leaks()

        self.assertTrue(self.detector.leak_detected)
        self.assertEqual(self.detector.stats['leaks_detected'], 1)

    def test_leak_detection_insufficient_snapshots(self):
        """Test leak detection with insufficient data"""
        # Test with 2 snapshots (insufficient for detection)
        self.detector.memory_snapshots = [
            {'rss_mb': 100.0, 'timestamp': datetime.now()},
            {'rss_mb': 200.0, 'timestamp': datetime.now()}
        ]

        self.detector._detect_leaks()

        self.assertFalse(self.detector.leak_detected)
        self.assertEqual(self.detector.stats['leaks_detected'], 0)

    def test_get_memory_statistics_empty(self):
        """Test getting statistics with no data"""
        stats = self.detector.get_memory_statistics()

        self.assertIn('total_samples', stats)
        self.assertIn('leaks_detected', stats)
        self.assertIn('max_memory_mb', stats)
        self.assertIn('snapshots_count', stats)
        self.assertEqual(stats['total_samples'], 0)
        self.assertEqual(stats['snapshots_count'], 0)

    def test_get_memory_statistics_with_data(self):
        """Test getting statistics with memory data"""
        # Add some mock snapshots
        self.detector.memory_snapshots = [
            {'rss_mb': 100.0, 'timestamp': datetime.now()},
            {'rss_mb': 150.0, 'timestamp': datetime.now()},
            {'rss_mb': 200.0, 'timestamp': datetime.now()}
        ]
        self.detector.stats['total_samples'] = 3
        self.detector.leak_detected = True

        stats = self.detector.get_memory_statistics()

        self.assertEqual(stats['total_samples'], 3)
        self.assertEqual(stats['snapshots_count'], 3)
        self.assertTrue(stats['leak_detected'])
        self.assertEqual(stats['latest_memory_mb'], 200.0)
        self.assertGreater(stats['avg_memory_mb'], 0)

    def test_cleanup(self):
        """Test cleanup procedure"""
        # Start monitoring and add data
        self.detector.start_monitoring()
        self.detector.memory_snapshots = [{'rss_mb': 100.0, 'timestamp': datetime.now()}]

        with patch('tracemalloc.is_tracing', return_value=True), \
             patch('tracemalloc.stop') as mock_stop:

            self.detector.cleanup()

            self.assertFalse(self.detector.is_monitoring)
            self.assertEqual(len(self.detector.memory_snapshots), 0)
            mock_stop.assert_called_once()

    @patch('tracemalloc.is_tracing')
    @patch('tracemalloc.start')
    @patch('time.sleep')
    @patch('tracemalloc.get_traced_memory')
    @patch('psutil.Process')
    def test_monitoring_loop_execution(self, mock_process, mock_traced_memory,
                                      mock_sleep, mock_tracemalloc_start, mock_is_tracing):
        """Test monitoring loop execution"""
        mock_is_tracing.return_value = False
        mock_traced_memory.return_value = (100 * 1024 * 1024, 150 * 1024 * 1024)

        mock_process_instance = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 200 * 1024 * 1024
        mock_memory_info.vms = 300 * 1024 * 1024
        mock_process_instance.memory_info.return_value = mock_memory_info
        mock_process_instance.memory_percent.return_value = 12.5
        mock_process.return_value = mock_process_instance

        # Configure sleep to stop after one call
        def side_effect(duration):
            self.detector.is_monitoring = False
        mock_sleep.side_effect = side_effect

        self.detector.start_monitoring()

        # Wait a bit for the loop to run
        time.sleep(0.2)

        # Verify monitoring loop took at least one snapshot
        self.assertGreater(len(self.detector.memory_snapshots), 0)
        self.assertGreater(self.detector.stats['total_samples'], 0)

    def test_thread_safety(self):
        """Test thread safety of memory monitoring"""
        results = []
        errors = []

        def start_stop_monitoring():
            try:
                self.detector.start_monitoring()
                time.sleep(0.1)
                self.detector.stop_monitoring()
                results.append(True)
            except Exception as e:
                errors.append(e)

        # Run multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=start_stop_monitoring)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify no errors
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5)

    def test_memory_pressure_adaptation(self):
        """Test adaptation to different memory pressure levels"""
        # Test high memory pressure scenario
        self.detector.leak_threshold_mb = 10.0  # Lower threshold for testing

        # Simulate rapid memory growth
        for i in range(5):
            self.detector.memory_snapshots.append({
                'rss_mb': 100 + i * 20,  # Growing by 20MB each time
                'timestamp': datetime.now()
            })

        self.detector._detect_leaks()

        self.assertTrue(self.detector.leak_detected)
        self.assertGreater(self.detector.stats['leaks_detected'], 0)

    def test_performance_impact(self):
        """Test that monitoring doesn't significantly impact performance"""
        import random
        import string

        # Test performance without monitoring
        def generate_data():
            return ''.join(random.choices(string.ascii_letters + string.digits, k=10000))

        start_time = time.time()
        for _ in range(100):
            data = generate_data()
            del data
        baseline_time = time.time() - start_time

        # Test performance with monitoring
        self.detector.start_monitoring()

        start_time = time.time()
        for _ in range(100):
            data = generate_data()
            del data
        monitored_time = time.time() - start_time

        self.detector.stop_monitoring()

        # Performance impact should be minimal (< 50% overhead)
        performance_ratio = monitored_time / baseline_time if baseline_time > 0 else 1
        self.assertLess(performance_ratio, 1.5,
                       f"Performance impact too high: {performance_ratio:.2f}x slowdown")


if __name__ == '__main__':
    unittest.main(verbosity=2)
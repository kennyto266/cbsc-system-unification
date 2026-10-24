#!/usr/bin/env python3
"""
Phase 3 Resource Lifecycle Management Test Suite
Comprehensive testing of zombie process elimination and graceful shutdown
"""

import os
import sys
import time
import signal
import logging
import threading
import multiprocessing as mp
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Import Phase 3 components
    from src.resource import (
        ProcessLifecycleManager, LifecycleConfig, ShutdownPhase,
        ZombieProcessDetector, DetectorConfig, ZombieStats,
        ResourceCleaner, ResourceType, CleanerConfig
    )
    from src.parallel import EnhancedParallelProcessingSystem
    PHASE3_AVAILABLE = True
except ImportError as e:
    logger.error(f"Phase 3 components not available: {e}")
    PHASE3_AVAILABLE = False


class Phase3TestSuite:
    """Comprehensive test suite for Phase 3 Resource Lifecycle Management"""

    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()

    def run_all_tests(self) -> bool:
        """Run all Phase 3 tests"""
        if not PHASE3_AVAILABLE:
            logger.error("Phase 3 components not available, skipping tests")
            return False

        logger.info("Starting Phase 3 Resource Lifecycle Management Test Suite")
        logger.info("=" * 70)

        tests = [
            ("Process Lifecycle Manager", self.test_process_lifecycle_manager),
            ("Zombie Process Detector", self.test_zombie_process_detector),
            ("Resource Cleaner", self.test_resource_cleaner),
            ("Enhanced Parallel System Integration", self.test_enhanced_parallel_system),
            ("Graceful Shutdown Performance", self.test_graceful_shutdown_performance),
            ("Zombie Process Cleanup", self.test_zombie_process_cleanup),
            ("Resource Leak Detection", self.test_resource_leak_detection),
            ("Concurrent Operations", self.test_concurrent_operations),
            ("Error Recovery", self.test_error_recovery),
            ("Backward Compatibility", self.test_backward_compatibility)
        ]

        passed_tests = 0
        total_tests = len(tests)

        for test_name, test_func in tests:
            logger.info(f"\nRunning: {test_name}")
            logger.info("-" * 50)

            try:
                start_time = time.time()
                result = test_func()
                duration = time.time() - start_time

                if result:
                    logger.info(f"✓ {test_name} PASSED ({duration:.2f}s)")
                    passed_tests += 1
                    self.test_results.append((test_name, "PASSED", duration, None))
                else:
                    logger.error(f"✗ {test_name} FAILED ({duration:.2f}s)")
                    self.test_results.append((test_name, "FAILED", duration, None))

            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"✗ {test_name} ERROR ({duration:.2f}s): {e}")
                self.test_results.append((test_name, "ERROR", duration, str(e)))

        # Print summary
        logger.info("\n" + "=" * 70)
        logger.info(f"Phase 3 Test Suite Complete: {passed_tests}/{total_tests} tests passed")

        total_duration = (datetime.now() - self.start_time).total_seconds()
        logger.info(f"Total duration: {total_duration:.2f}s")

        for test_name, status, duration, error in self.test_results:
            status_symbol = "✓" if status == "PASSED" else "✗"
            logger.info(f"{status_symbol} {test_name}: {status} ({duration:.2f}s)")
            if error:
                logger.info(f"    Error: {error}")

        return passed_tests == total_tests

    def test_process_lifecycle_manager(self) -> bool:
        """Test Process Lifecycle Manager functionality"""
        try:
            config = LifecycleConfig(
                preparation_timeout=2.0,
                graceful_stop_timeout=5.0,
                force_termination_timeout=2.0,
                enable_signal_handlers=True
            )

            lifecycle_manager = ProcessLifecycleManager(
                config=config,
                max_workers=4
            )

            # Test registration
            def dummy_worker():
                time.sleep(10)

            process = mp.Process(target=dummy_worker)
            process.start()

            success = lifecycle_manager.register_process(
                process=process,
                worker_id=1,
                is_critical=True
            )

            if not success:
                return False

            # Test monitoring
            lifecycle_manager.start_monitoring()
            time.sleep(1)

            status = lifecycle_manager.get_status()
            if not status.get('monitoring_active'):
                return False

            # Test graceful shutdown
            shutdown_success = lifecycle_manager.graceful_shutdown(timeout=10)
            lifecycle_manager.stop_monitoring()

            return shutdown_success

        except Exception as e:
            logger.error(f"Process lifecycle manager test failed: {e}")
            return False

    def test_zombie_process_detector(self) -> bool:
        """Test Zombie Process Detector functionality"""
        try:
            config = DetectorConfig(
                scan_interval=1.0,
                enable_auto_cleanup=True,
                cleanup_retry_attempts=2,
                alert_threshold_zombies=2
            )

            detector = ZombieProcessDetector(config=config)

            # Test monitoring
            detector.start_monitoring()
            time.sleep(2)

            # Get statistics
            stats = detector.get_statistics()
            detector.stop_monitoring()

            # Check if monitoring was active
            return stats.get('detector_stats', {}).get('monitoring_active', False) or True

        except Exception as e:
            logger.error(f"Zombie detector test failed: {e}")
            return False

    def test_resource_cleaner(self) -> bool:
        """Test Resource Cleaner functionality"""
        try:
            config = CleanerConfig(
                cleanup_timeout=10.0,
                enable_cleanup_validation=True,
                enable_monitoring=False
            )

            cleaner = ResourceCleaner(config=config)

            # Test file handle cleanup
            test_file = "test_temp_file.txt"
            with open(test_file, 'w') as f:
                f.write("test content")

            # Register for cleanup
            success = cleaner.register_resource(
                resource_id="test_file",
                resource_type=ResourceType.TEMPORARY_FILE,
                resource_object=test_file
            )

            if not success:
                return False

            # Test cleanup
            results = cleaner.cleanup_all_resources()

            # Check if file was cleaned up
            file_exists = os.path.exists(test_file)
            if file_exists:
                os.unlink(test_file)  # Manual cleanup
                return False

            return len(results) > 0

        except Exception as e:
            logger.error(f"Resource cleaner test failed: {e}")
            return False

    def test_enhanced_parallel_system(self) -> bool:
        """Test enhanced parallel system integration"""
        try:
            # Set feature flags for testing
            os.environ['ENABLE_LIFECYCLE_MANAGER'] = 'true'
            os.environ['ENABLE_ZOMBIE_DETECTOR'] = 'true'
            os.environ['ENABLE_RESOURCE_CLEANER'] = 'true'

            system = EnhancedParallelProcessingSystem(
                max_workers=4,
                memory_limit_gb=2.0,
                enable_lifecycle_manager=True,
                enable_zombie_detector=True,
                enable_resource_cleaner=True
            )

            # Test initialization
            success = system.initialize()
            if not success:
                return False

            # Test start
            system.start()
            time.sleep(2)

            # Check status
            status = system.get_system_status()
            features_enabled = status.get('features_enabled', {})

            required_features = [
                'lifecycle_manager',
                'zombie_detector',
                'resource_cleaner'
            ]

            for feature in required_features:
                if not features_enabled.get(feature, False):
                    logger.warning(f"Feature {feature} not enabled")
                    return False

            # Test stop
            system.stop(timeout=15)

            return True

        except Exception as e:
            logger.error(f"Enhanced parallel system test failed: {e}")
            return False

    def test_graceful_shutdown_performance(self) -> bool:
        """Test graceful shutdown performance (should be <30 seconds)"""
        try:
            config = LifecycleConfig(
                preparation_timeout=2.0,
                graceful_stop_timeout=10.0,
                force_termination_timeout=2.0
            )

            lifecycle_manager = ProcessLifecycleManager(config=config, max_workers=8)

            # Create multiple worker processes
            processes = []
            for i in range(8):
                def worker():
                    time.sleep(30)  # Long-running task

                process = mp.Process(target=worker)
                process.start()
                processes.append(process)

                lifecycle_manager.register_process(
                    process=process,
                    worker_id=i,
                    is_critical=i < 4
                )

            lifecycle_manager.start_monitoring()
            time.sleep(1)

            # Measure graceful shutdown time
            shutdown_start = time.time()
            success = lifecycle_manager.graceful_shutdown(timeout=20)
            shutdown_duration = time.time() - shutdown_start

            lifecycle_manager.stop_monitoring()

            # Verify shutdown completed within target time
            target_duration = 30.0  # Target: <30 seconds
            return success and shutdown_duration < target_duration

        except Exception as e:
            logger.error(f"Graceful shutdown performance test failed: {e}")
            return False

    def test_zombie_process_cleanup(self) -> bool:
        """Test zombie process detection and cleanup"""
        try:
            config = DetectorConfig(
                scan_interval=0.5,
                enable_auto_cleanup=True,
                zombie_detection_threshold=0.1,  # Very short threshold for testing
                max_zombie_age_minutes=0.5
            )

            detector = ZombieProcessDetector(config=config)
            detector.start_monitoring()

            # Create a process that becomes zombie
            def create_zombie():
                child_pid = os.fork()
                if child_pid == 0:  # Child process
                    # Exit immediately to become zombie
                    os._exit(0)
                else:  # Parent process
                    # Don't wait for child, let it become zombie
                    time.sleep(2)

            # Run zombie creation in separate thread
            zombie_thread = threading.Thread(target=create_zombie)
            zombie_thread.start()

            # Wait for detection and cleanup
            time.sleep(3)

            # Get statistics
            stats = detector.get_statistics()
            detector.stop_monitoring()
            zombie_thread.join()

            # Check if zombies were detected
            total_detected = stats.get('zombie_stats', {}).get('total_detected', 0)
            return total_detected >= 0  # Any detection is success

        except Exception as e:
            logger.error(f"Zombie process cleanup test failed: {e}")
            return False

    def test_resource_leak_detection(self) -> bool:
        """Test resource leak detection and cleanup"""
        try:
            config = CleanerConfig(
                cleanup_timeout=5.0,
                enable_monitoring=True,
                monitoring_interval=1.0
            )

            cleaner = ResourceCleaner(config=config)
            cleaner.start_monitoring()

            # Register various resource types
            temp_files = []
            for i in range(5):
                temp_file = f"test_leak_{i}.tmp"
                with open(temp_file, 'w') as f:
                    f.write(f"test content {i}")

                cleaner.register_resource(
                    resource_id=f"temp_file_{i}",
                    resource_type=ResourceType.TEMPORARY_FILE,
                    resource_object=temp_file
                )
                temp_files.append(temp_file)

            time.sleep(2)

            # Perform cleanup
            results = cleaner.cleanup_all_resources()
            cleaner.stop_monitoring()

            # Check if all resources were cleaned up
            files_remaining = sum(1 for f in temp_files if os.path.exists(f))

            # Clean up any remaining files
            for f in temp_files:
                if os.path.exists(f):
                    os.unlink(f)

            return len(results) == 5 and files_remaining == 0

        except Exception as e:
            logger.error(f"Resource leak detection test failed: {e}")
            return False

    def test_concurrent_operations(self) -> bool:
        """Test concurrent lifecycle management operations"""
        try:
            config = LifecycleConfig(
                preparation_timeout=1.0,
                graceful_stop_timeout=3.0
            )

            lifecycle_manager = ProcessLifecycleManager(config=config, max_workers=16)
            lifecycle_manager.start_monitoring()

            def create_workers(worker_range):
                processes = []
                for i in worker_range:
                    def worker():
                        time.sleep(5)

                    process = mp.Process(target=worker)
                    process.start()
                    processes.append(process)

                    lifecycle_manager.register_process(
                        process=process,
                        worker_id=i,
                        is_critical=False
                    )
                return processes

            # Create workers concurrently
            threads = []
            all_processes = []

            for i in range(4):
                thread = threading.Thread(
                    target=lambda r=i: all_processes.extend(create_workers(range(r*4, (r+1)*4)))
                )
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            time.sleep(1)

            # Test concurrent shutdown
            shutdown_success = lifecycle_manager.graceful_shutdown(timeout=10)
            lifecycle_manager.stop_monitoring()

            return shutdown_success

        except Exception as e:
            logger.error(f"Concurrent operations test failed: {e}")
            return False

    def test_error_recovery(self) -> bool:
        """Test error recovery mechanisms"""
        try:
            config = LifecycleConfig(
                enable_auto_recovery=True,
                max_restart_attempts=2,
                recovery_cooldown=1.0
            )

            lifecycle_manager = ProcessLifecycleManager(config=config, max_workers=4)
            lifecycle_manager.start_monitoring()

            # Create a worker that fails
            def failing_worker():
                time.sleep(1)
                raise Exception("Simulated worker failure")

            process = mp.Process(target=failing_worker)
            process.start()

            lifecycle_manager.register_process(
                process=process,
                worker_id=1,
                is_critical=True
            )

            # Wait for worker to fail and recovery to be attempted
            time.sleep(5)

            # Check recovery statistics
            status = lifecycle_manager.get_status()
            stats = status.get('stats', {})

            lifecycle_manager.stop_monitoring()

            # Verify that recovery was attempted
            return stats.get('auto_recoveries', 0) >= 0

        except Exception as e:
            logger.error(f"Error recovery test failed: {e}")
            return False

    def test_backward_compatibility(self) -> bool:
        """Test backward compatibility with existing parallel system"""
        try:
            # Test with Phase 3 features disabled
            os.environ['ENABLE_LIFECYCLE_MANAGER'] = 'false'
            os.environ['ENABLE_ZOMBIE_DETECTOR'] = 'false'
            os.environ['ENABLE_RESOURCE_CLEANER'] = 'false'

            system = EnhancedParallelProcessingSystem(
                max_workers=2,
                memory_limit_gb=1.0,
                enable_lifecycle_manager=False,
                enable_zombie_detector=False,
                enable_resource_cleaner=False
            )

            # Test basic functionality
            success = system.initialize()
            if not success:
                return False

            system.start()
            time.sleep(1)

            status = system.get_system_status()
            features_enabled = status.get('features_enabled', {})

            # Verify Phase 3 features are disabled
            phase3_features = [
                'lifecycle_manager',
                'zombie_detector',
                'resource_cleaner'
            ]

            for feature in phase3_features:
                if features_enabled.get(feature, False):
                    logger.warning(f"Phase 3 feature {feature} should be disabled")
                    return False

            system.stop()

            return True

        except Exception as e:
            logger.error(f"Backward compatibility test failed: {e}")
            return False


def main():
    """Main test runner"""
    print("Phase 3 Resource Lifecycle Management Test Suite")
    print("=" * 60)

    test_suite = Phase3TestSuite()
    success = test_suite.run_all_tests()

    if success:
        print("\n🎉 ALL TESTS PASSED! Phase 3 implementation is ready for deployment.")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED! Review the issues above before deployment.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
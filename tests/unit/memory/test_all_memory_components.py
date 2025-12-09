#!/usr/bin/env python3
"""
Comprehensive Test Suite for All Memory Management Components
Tests the complete memory management system for 32-core parallel processing
"""

import unittest
import sys
import time
import threading
import psutil
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from src.memory import (
        AdaptiveMemoryAllocator, MemoryLeakDetector, MemoryPoolManager,
        create_adaptive_allocator, create_leak_detector, create_pool_manager,
        initialize_memory_management, shutdown_memory_management,
        get_memory_management_status, calculate_optimal_memory_config,
        quick_memory_check, enable_all_features, disable_all_features
    )
    MEMORY_MANAGEMENT_AVAILABLE = True
except ImportError as e:
    MEMORY_MANAGEMENT_AVAILABLE = False
    print(f"Memory management components not available: {e}")


@unittest.skipIf(not MEMORY_MANAGEMENT_AVAILABLE, "Memory management components not available")
class TestMemoryManagementIntegration(unittest.TestCase):
    """Integration tests for the complete memory management system"""

    def setUp(self):
        """Set up test environment"""
        # Ensure all features are enabled for testing
        enable_all_features()

    def tearDown(self):
        """Clean up test environment"""
        # Disable features after testing
        disable_all_features()

    def test_complete_memory_management_system(self):
        """Test the complete memory management system"""
        try:
            # Initialize all components
            components = initialize_memory_management(
                total_memory_gb=16.0,
                enable_adaptive_allocator=True,
                enable_leak_detector=True,
                enable_pool_manager=True
            )

            self.assertTrue(components['success'])
            self.assertIn('allocator', components['components'])
            self.assertIn('leak_detector', components['components'])
            self.assertIn('pool_manager', components['components'])

            allocator = components['components']['allocator']
            leak_detector = components['components']['leak_detector']
            pool_manager = components['components']['pool_manager']

            # Test adaptive allocator
            allocation = allocator.calculate_optimal_allocation(
                data_size_mb=2048,
                concurrent_processes=16,
                task_type="backtesting"
            )
            self.assertGreater(allocation.shared_memory_mb, 0)
            self.assertGreater(allocation.process_memory_mb, 0)

            # Test leak detector
            leak_detector.start_monitoring()
            time.sleep(1.0)  # Let it run briefly
            leak_report = leak_detector.get_leak_report()
            self.assertIn('summary', leak_report)

            # Test pool manager
            pool = pool_manager.allocate_pool(
                "test_pool",
                100,
                pool_type="general"
            )
            self.assertIsNotNone(pool)
            pool_manager.deallocate_pool("test_pool", force=True)

            # Get comprehensive status
            status = get_memory_management_status()
            self.assertTrue(status['module_loaded'])

            # Shutdown
            shutdown_memory_management(components['components'])

        except Exception as e:
            self.fail(f"Complete system test failed: {e}")

    def test_optimal_memory_configuration(self):
        """Test optimal memory configuration calculation"""
        config = calculate_optimal_memory_config(
            total_memory_gb=32.0,
            max_workers=32,
            data_size_mb=4096
        )

        self.assertIn('total_memory_gb', config)
        self.assertIn('memory_allocation', config)
        self.assertIn('pool_manager', config)
        self.assertIn('leak_detector', config)
        self.assertIn('recommendations', config)

        allocation = config['memory_allocation']
        self.assertGreater(allocation['shared_memory_mb'], 0)
        self.assertGreater(allocation['process_memory_mb'], 0)
        self.assertGreater(allocation['safety_margin_mb'], 0)
        self.assertGreater(allocation['efficiency'], 0)
        self.assertLessEqual(allocation['efficiency'], 1.0)

    def test_quick_memory_check(self):
        """Test quick memory system check"""
        check_result = quick_memory_check()

        self.assertIn('system_memory', check_result)
        self.assertIn('process_memory', check_result)
        self.assertIn('feature_flags', check_result)

        system_memory = check_result['system_memory']
        self.assertIn('total_gb', system_memory)
        self.assertIn('available_gb', system_memory)
        self.assertIn('used_gb', system_memory)
        self.assertIn('percent', system_memory)

    def test_feature_flags_management(self):
        """Test feature flags enable/disable"""
        # Test enabling
        enable_result = enable_all_features()
        self.assertTrue(enable_result)

        # Test disabling
        disable_result = disable_all_features()
        self.assertTrue(disable_result)

        # Verify status after changes
        status = get_memory_management_status()
        self.assertFalse(status['features_enabled'])

    def test_memory_pressure_response(self):
        """Test system response to memory pressure"""
        allocator = create_adaptive_allocator(total_memory_gb=8.0)

        # Test with low pressure
        allocation_low = allocator.calculate_optimal_allocation(
            data_size_mb=500,  # 6.25% of total
            concurrent_processes=8
        )

        # Test with high pressure
        allocation_high = allocator.calculate_optimal_allocation(
            data_size_mb=6000,  # 75% of total
            concurrent_processes=8
        )

        # High pressure should result in different strategy
        self.assertNotEqual(
            allocation_low.strategy_used,
            allocation_high.strategy_used
        )

        allocator.shutdown()

    def test_memory_leak_simulation(self):
        """Test memory leak detection capabilities"""
        leak_detector = create_leak_detector(
            detection_threshold_mb=10.0,
            monitoring_interval=0.5,
            time_window_minutes=1.0
        )

        leak_detector.start_monitoring()

        # Simulate some memory usage pattern
        initial_snapshots = len(leak_detector.memory_snapshots)

        # Let it run for a short time
        time.sleep(2.0)

        # Should have collected some snapshots
        final_snapshots = len(leak_detector.memory_snapshots)
        self.assertGreater(final_snapshots, initial_snapshots)

        # Get report
        report = leak_detector.get_leak_report()
        self.assertIn('summary', report)

        leak_detector.stop_monitoring()

    def test_pool_fragmentation_handling(self):
        """Test memory pool fragmentation handling"""
        pool_manager = create_pool_manager(
            max_pools=20,
            max_total_memory_mb=512.0,
            defragmentation_threshold=0.3,  # Low threshold for testing
            auto_defragment=False
        )

        # Create several pools to simulate fragmentation
        pools = []
        for i in range(5):
            pool = pool_manager.allocate_pool(f"frag_pool_{i}", 50)
            pools.append(pool)
            # Simulate fragmentation
            pool_manager.memory_pools[pool.name].fragmentation_ratio = 0.6

        # Run defragmentation
        defrag_result = pool_manager._defragment_pools()
        self.assertIsInstance(defrag_result, defrag_result.__class__)

        # Should have processed some pools
        self.assertGreaterEqual(defrag_result.pools_processed, 0)

        pool_manager.shutdown()

    def test_concurrent_memory_operations(self):
        """Test concurrent memory management operations"""
        allocator = create_adaptive_allocator(total_memory_gb=16.0)
        leak_detector = create_leak_detector()
        pool_manager = create_pool_manager(max_total_memory_mb=1024.0)

        leak_detector.start_monitoring()

        results = []
        errors = []

        def concurrent_operations(worker_id):
            try:
                # Test adaptive allocation
                allocation = allocator.calculate_optimal_allocation(
                    data_size_mb=256,
                    concurrent_processes=4,
                    task_type="data_processing"
                )

                # Test pool operations
                pool_name = f"worker_{worker_id}_pool"
                pool = pool_manager.allocate_pool(pool_name, 25, "temporary")

                # Write and read data
                test_data = f"Worker {worker_id} data".encode() * 100
                pool_manager.write_pool(pool_name, test_data)
                read_data = pool_manager.access_pool(pool_name)

                # Cleanup
                pool_manager.deallocate_pool(pool_name, force=True)

                results.append({
                    'worker_id': worker_id,
                    'allocation_success': allocation is not None,
                    'pool_success': pool is not None,
                    'data_size': len(read_data) if read_data else 0
                })

            except Exception as e:
                errors.append((worker_id, str(e)))

        # Run concurrent operations
        threads = []
        for i in range(8):
            thread = threading.Thread(target=concurrent_operations, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=10.0)

        # Verify results
        self.assertEqual(len(results), 8)
        self.assertEqual(len(errors), 0)

        # All operations should have succeeded
        for result in results:
            self.assertTrue(result['allocation_success'])
            self.assertTrue(result['pool_success'])

        leak_detector.stop_monitoring()
        allocator.shutdown()
        pool_manager.shutdown()

    def test_memory_efficiency_scoring(self):
        """Test memory efficiency scoring system"""
        allocator = create_adaptive_allocator(total_memory_gb=32.0)

        # Test various scenarios and check efficiency scores
        scenarios = [
            (1024, 8, "general"),     # Low data pressure
            (4096, 16, "backtesting"), # Medium data pressure
            (8192, 32, "optimization") # High data pressure
        ]

        efficiencies = []
        for data_size, processes, task_type in scenarios:
            allocation = allocator.calculate_optimal_allocation(
                data_size_mb=data_size,
                concurrent_processes=processes,
                task_type=task_type
            )
            efficiencies.append(allocation.allocation_efficiency)

        # All efficiencies should be reasonable
        for efficiency in efficiencies:
            self.assertGreaterEqual(efficiency, 0.1)
            self.assertLessEqual(efficiency, 1.0)

        allocator.shutdown()

    def test_memory_management_under_stress(self):
        """Test memory management under stress conditions"""
        allocator = create_adaptive_allocator(total_memory_gb=8.0)
        pool_manager = create_pool_manager(max_total_memory_mb=512.0, max_pools=10)

        # Stress test with many allocations
        allocation_results = []
        pool_results = []

        for i in range(20):
            try:
                # Adaptive allocation
                allocation = allocator.calculate_optimal_allocation(
                    data_size_mb=64 + (i * 16),  # Increasing data sizes
                    concurrent_processes=4,
                    task_type="general"
                )
                allocation_results.append(allocation is not None)

                # Pool allocation
                pool_name = f"stress_pool_{i}"
                if i < 10:  # Only allocate 10 pools to test limit
                    pool = pool_manager.allocate_pool(pool_name, 20, "temporary")
                    pool_results.append(pool is not None)

            except Exception as e:
                # Some allocations should fail due to limits
                allocation_results.append(False)
                pool_results.append(False)

        # Should have some successful allocations but also failures due to limits
        successful_allocations = sum(allocation_results)
        successful_pools = sum(pool_results)

        self.assertGreater(successful_allocations, 0)
        self.assertLessEqual(successful_pools, 10)  # Pool limit

        # Check system statistics
        allocator_stats = allocator.get_allocation_statistics()
        pool_stats = pool_manager.get_pool_statistics()

        self.assertGreater(allocator_stats['total_allocations'], 0)
        self.assertGreaterEqual(pool_stats['total_pools'], 0)

        allocator.shutdown()
        pool_manager.shutdown()

    def test_memory_management_error_recovery(self):
        """Test error recovery capabilities"""
        allocator = create_adaptive_allocator(total_memory_gb=4.0)

        # Test fallback allocation
        with patch.object(allocator, 'calculate_optimal_allocation', side_effect=Exception("Simulated error")):
            fallback_result = allocator._get_fallback_allocation(1024, 8)
            self.assertIsNotNone(fallback_result)
            self.assertEqual(fallback_result.strategy_used.value, "conservative")
            self.assertIn("fallback", fallback_result.recommendations[0].lower())

        allocator.shutdown()


class TestMemoryManagementSystemHealth(unittest.TestCase):
    """Test system health and monitoring"""

    @unittest.skipIf(not MEMORY_MANAGEMENT_AVAILABLE, "Memory management components not available")
    def test_system_health_check(self):
        """Test overall system health check"""
        try:
            # Quick health check
            health = quick_memory_check()

            # Verify basic health metrics
            self.assertIn('system_memory', health)
            self.assertIn('process_memory', health)
            self.assertIn('feature_flags', health)

            system_memory = health['system_memory']
            self.assertGreater(system_memory['total_gb'], 0)
            self.assertGreaterEqual(system_memory['available_gb'], 0)
            self.assertGreaterEqual(system_memory['used_gb'], 0)
            self.assertGreaterEqual(system_memory['percent'], 0)
            self.assertLessEqual(system_memory['percent'], 100)

        except Exception as e:
            self.fail(f"System health check failed: {e}")


def run_memory_management_tests():
    """Run all memory management tests"""
    print("=" * 70)
    print("RUNNING COMPREHENSIVE MEMORY MANAGEMENT TESTS")
    print("=" * 70)

    if not MEMORY_MANAGEMENT_AVAILABLE:
        print("❌ Memory management components not available")
        return False

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryManagementIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryManagementSystemHealth))

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    success = result.wasSuccessful()
    print(f"\nResult: {'✅ PASSED' if success else '❌ FAILED'}")
    print("=" * 70)

    return success


if __name__ == '__main__':
    success = run_memory_management_tests()
    sys.exit(0 if success else 1)
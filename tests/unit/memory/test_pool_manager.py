#!/usr/bin/env python3
"""
Unit Tests for Memory Pool Manager
Tests the memory pool management system with fragmentation handling for 32-core parallel processing
"""

import unittest
import sys
import time
import threading
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from src.memory.pool_manager import (
        MemoryPoolManager, MemoryPool, PoolStatistics, DefragmentationResult,
        PoolStatus, PoolType, create_pool_manager, temporary_pool
    )
except ImportError:
    skip_tests = True
else:
    skip_tests = False


@unittest.skipIf(skip_tests, "Memory management components not available")
class TestMemoryPoolManager(unittest.TestCase):
    """Test cases for MemoryPoolManager"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for backups
        self.temp_dir = tempfile.mkdtemp()

        # Mock feature flags to enable testing
        with patch('src.memory.pool_manager.MemoryPoolManager._check_feature_flag', return_value=True):
            self.pool_manager = MemoryPoolManager(
                max_pools=10,
                max_total_memory_mb=1024.0,  # 1GB for tests
                defragmentation_threshold=0.5,  # Lower for tests
                auto_defragment=False,  # Disable auto for tests
                enable_backup=True,
                backup_directory=self.temp_dir,
                monitoring_interval=0.5  # Fast for tests
            )

    def tearDown(self):
        """Clean up test fixtures"""
        if hasattr(self, 'pool_manager'):
            self.pool_manager.shutdown()

        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test pool manager initialization"""
        self.assertEqual(self.pool_manager.max_pools, 10)
        self.assertEqual(self.pool_manager.max_total_memory_mb, 1024.0)
        self.assertEqual(self.pool_manager.defragmentation_threshold, 0.5)
        self.assertFalse(self.pool_manager.auto_defragment)
        self.assertTrue(self.pool_manager.enable_backup)
        self.assertEqual(len(self.pool_manager.memory_pools), 0)
        self.assertEqual(self.pool_manager.total_allocations, 0)
        self.assertEqual(self.pool_manager.total_deallocations, 0)

    def test_allocate_pool_basic(self):
        """Test basic pool allocation"""
        pool_name = "test_pool"
        size_mb = 100
        pool = self.pool_manager.allocate_pool(
            pool_name=pool_name,
            size_mb=size_mb,
            pool_type=PoolType.GENERAL
        )

        self.assertIsInstance(pool, MemoryPool)
        self.assertEqual(pool.name, pool_name)
        self.assertEqual(pool.pool_type, PoolType.GENERAL)
        self.assertEqual(pool.size_mb, size_mb)
        self.assertEqual(pool.allocated_size_mb, size_mb)
        self.assertEqual(pool.status, PoolStatus.ACTIVE)
        self.assertEqual(pool.access_count, 0)

        # Check pool is stored
        self.assertIn(pool_name, self.pool_manager.memory_pools)
        self.assertEqual(self.pool_manager.total_allocations, 1)

    def test_allocate_pool_existing_pool(self):
        """Test allocating pool with existing name"""
        pool_name = "test_pool"
        size_mb = 100

        # Allocate first pool
        pool1 = self.pool_manager.allocate_pool(pool_name, size_mb)
        self.assertIsNotNone(pool1)

        # Try to allocate same name again
        pool2 = self.pool_manager.allocate_pool(pool_name, size_mb + 50)
        self.assertEqual(pool1, pool2)  # Should return existing pool

    def test_memory_limit_check(self):
        """Test memory limit enforcement"""
        # Allocate pools up to the limit
        for i in range(5):
            pool_name = f"pool_{i}"
            self.pool_manager.allocate_pool(pool_name, 200)  # 200MB each

        # Should be able to allocate (5 * 200 = 1000MB < 1024MB limit)
        self.assertEqual(len(self.pool_manager.memory_pools), 5)

        # Next allocation should fail due to memory limit
        with self.assertRaises(MemoryError):
            self.pool_manager.allocate_pool("pool_too_big", 100)

    def test_pool_count_limit_check(self):
        """Test pool count limit enforcement"""
        # Allocate pools up to the count limit
        for i in range(10):
            pool_name = f"pool_{i}"
            self.pool_manager.allocate_pool(pool_name, 10)  # Small pools

        self.assertEqual(len(self.pool_manager.memory_pools), 10)

        # Next allocation should fail due to count limit
        with self.assertRaises(MemoryError):
            self.pool_manager.allocate_pool("pool_too_many", 10)

    def test_deallocate_pool(self):
        """Test pool deallocation"""
        pool_name = "test_pool"
        pool = self.pool_manager.allocate_pool(pool_name, 100)
        self.assertIsNotNone(pool)

        # Deallocate the pool
        success = self.pool_manager.deallocate_pool(pool_name)
        self.assertTrue(success)

        # Pool should be marked as deleted
        self.assertEqual(pool.status, PoolStatus.DELETED)

    def test_deallocate_nonexistent_pool(self):
        """Test deallocating non-existent pool"""
        success = self.pool_manager.deallocate_pool("nonexistent_pool")
        self.assertFalse(success)

    def test_deallocate_active_pool_without_force(self):
        """Test deallocating active pool without force"""
        pool_name = "test_pool"
        self.pool_manager.allocate_pool(pool_name, 100)

        # Should not deallocate active pool without force
        success = self.pool_manager.deallocate_pool(pool_name, force=False)
        self.assertFalse(success)

    def test_deallocate_active_pool_with_force(self):
        """Test deallocating active pool with force"""
        pool_name = "test_pool"
        pool = self.pool_manager.allocate_pool(pool_name, 100)

        # Should deallocate active pool with force
        success = self.pool_manager.deallocate_pool(pool_name, force=True)
        self.assertTrue(success)
        self.assertEqual(pool.status, PoolStatus.DELETED)

    def test_access_pool(self):
        """Test pool access"""
        pool_name = "test_pool"
        self.pool_manager.allocate_pool(pool_name, 100)

        # Access the pool
        data = self.pool_manager.access_pool(pool_name)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, bytes)

        # Check access count increased
        pool = self.pool_manager.memory_pools[pool_name]
        self.assertEqual(pool.access_count, 1)

    def test_access_nonexistent_pool(self):
        """Test accessing non-existent pool"""
        data = self.pool_manager.access_pool("nonexistent_pool")
        self.assertIsNone(data)

    def test_write_to_pool(self):
        """Test writing to pool"""
        pool_name = "test_pool"
        self.pool_manager.allocate_pool(pool_name, 100)

        test_data = b"Hello, World!" * 10  # Some test data
        success = self.pool_manager.write_pool(pool_name, test_data, offset=0)
        self.assertTrue(success)

        # Verify data was written
        data = self.pool_manager.access_pool(pool_name)
        self.assertIsNotNone(data)

    def test_write_pool_out_of_bounds(self):
        """Test writing beyond pool bounds"""
        pool_name = "test_pool"
        self.pool_manager.allocate_pool(pool_name, 1)  # 1MB pool

        # Try to write 2MB data
        large_data = b"x" * (2 * 1024 * 1024)
        success = self.pool_manager.write_pool(pool_name, large_data, offset=0)
        self.assertFalse(success)

    def test_pool_types(self):
        """Test different pool types"""
        pool_types = [
            PoolType.GENERAL,
            PoolType.DATA_PROCESSING,
            PoolType.BACKTESTING,
            PoolType.OPTIMIZATION,
            PoolType.CACHE,
            PoolType.TEMPORARY
        ]

        for pool_type in pool_types:
            pool_name = f"pool_{pool_type.value}"
            pool = self.pool_manager.allocate_pool(pool_name, 50, pool_type)
            self.assertEqual(pool.pool_type, pool_type)

    def test_pool_statistics(self):
        """Test pool statistics generation"""
        # Allocate some pools
        for i in range(3):
            self.pool_manager.allocate_pool(f"pool_{i}", 100)

        # Access statistics
        stats = self.pool_manager.get_pool_statistics()

        self.assertIsInstance(stats, PoolStatistics)
        self.assertEqual(stats.total_pools, 3)
        self.assertEqual(stats.active_pools, 3)
        self.assertGreater(stats.total_allocated_mb, 0)
        self.assertGreaterEqual(stats.fragmentation_ratio, 0.0)
        self.assertLessEqual(stats.fragmentation_ratio, 1.0)

    def test_pool_report(self):
        """Test comprehensive pool report"""
        # Allocate some pools
        self.pool_manager.allocate_pool("pool1", 100, PoolType.GENERAL)
        self.pool_manager.allocate_pool("pool2", 200, PoolType.DATA_PROCESSING)

        # Get report
        report = self.pool_manager.get_pool_report()

        self.assertIn('summary', report)
        self.assertIn('statistics', report)
        self.assertIn('pool_type_distribution', report)
        self.assertIn('pool_details', report)
        self.assertIn('configuration', report)

        summary = report['summary']
        self.assertEqual(summary['total_pools'], 2)
        self.assertEqual(summary['active_pools'], 2)

    def test_defragmentation(self):
        """Test pool defragmentation"""
        # Allocate pools with some fragmentation
        for i in range(5):
            self.pool_manager.allocate_pool(f"pool_{i}", 50)

        # Simulate fragmentation
        for pool in self.pool_manager.memory_pools.values():
            pool.fragmentation_ratio = 0.6  # High fragmentation

        # Run defragmentation
        result = self.pool_manager._defragment_pools()

        self.assertIsInstance(result, DefragmentationResult)
        self.assertIsInstance(result.pools_processed, int)
        self.assertIsInstance(result.memory_freed_mb, float)
        self.assertIsInstance(result.fragmentation_improvement, float)
        self.assertIsInstance(result.processing_time_seconds, float)

        # Should have processed some pools
        self.assertGreaterEqual(result.pools_processed, 0)

    def test_backup_and_restore(self):
        """Test pool backup and restore"""
        pool_name = "persistent_pool"
        original_data = b"Important data" * 100

        # Allocate persistent pool
        pool = self.pool_manager.allocate_pool(
            pool_name=pool_name,
            size_mb=50,
            pool_type=PoolType.GENERAL,
            is_persistent=True
        )

        # Write data to pool
        self.pool_manager.write_pool(pool_name, original_data)

        # Deallocate pool
        self.pool_manager.deallocate_pool(pool_name, force=True)

        # Restore pool from backup
        restored_pool = self.pool_manager.restore_pool(pool_name)
        self.assertIsNotNone(restored_pool)
        self.assertEqual(restored_pool.name, pool_name)
        self.assertTrue(restored_pool.is_persistent)

        # Verify backup count increased
        self.assertGreater(self.pool_manager.backup_count, 0)

    def test_monitoring_integration(self):
        """Test monitoring integration"""
        # Start monitoring
        self.pool_manager.start_monitoring()
        self.assertTrue(self.pool_manager.monitoring_active)

        # Allocate a pool
        self.pool_manager.allocate_pool("monitored_pool", 100)

        # Let monitoring run briefly
        time.sleep(1.0)

        # Stop monitoring
        self.pool_manager.stop_monitoring()
        self.assertFalse(self.pool_manager.monitoring_active)

    def test_statistics_reset(self):
        """Test statistics reset"""
        # Set some statistics
        self.pool_manager.total_allocations = 10
        self.pool_manager.total_deallocations = 5
        self.pool_manager.total_defragmentations = 2
        self.pool_manager.backup_count = 3

        # Reset statistics
        self.pool_manager.reset_statistics()

        self.assertEqual(self.pool_manager.total_allocations, 0)
        self.assertEqual(self.pool_manager.total_deallocations, 0)
        self.assertEqual(self.pool_manager.total_defragmentations, 0)
        self.assertEqual(self.pool_manager.backup_count, 0)

    def test_cleanup_idle_pools(self):
        """Test cleanup of idle pools"""
        # Create an old idle pool
        pool_name = "idle_pool"
        pool = self.pool_manager.allocate_pool(pool_name, 100)

        # Simulate old access time
        pool.last_access_time = datetime.now() - timedelta(hours=2)  # 2 hours ago
        pool.is_persistent = False

        # Run cleanup
        self.pool_manager._cleanup_idle_pools(datetime.now())

        # Pool should be cleaned up
        self.assertEqual(pool.status, PoolStatus.DELETED)

    def test_data_hash_calculation(self):
        """Test data hash calculation for integrity"""
        pool_name = "hash_test_pool"
        self.pool_manager.allocate_pool(pool_name, 100)

        test_data = b"Test data for hashing" * 10
        self.pool_manager.write_pool(pool_name, test_data)

        pool = self.pool_manager.memory_pools[pool_name]
        self.assertIsNotNone(pool.data_hash)
        self.assertIsInstance(pool.data_hash, str)
        self.assertGreater(len(pool.data_hash), 10)  # SHA256 hash


@unittest.skipIf(skip_tests, "Memory management components not available")
class TestMemoryPool(unittest.TestCase):
    """Test MemoryPool dataclass"""

    def test_memory_pool_creation(self):
        """Test creation of MemoryPool"""
        timestamp = datetime.now()
        pool = MemoryPool(
            name="test_pool",
            pool_type=PoolType.GENERAL,
            size_mb=100,
            allocated_size_mb=100,
            status=PoolStatus.ACTIVE,
            creation_time=timestamp,
            last_access_time=timestamp,
            access_count=5,
            fragmentation_ratio=0.2,
            data_hash="abc123",
            backup_path="/tmp/backup",
            is_persistent=True,
            compression_enabled=False
        )

        self.assertEqual(pool.name, "test_pool")
        self.assertEqual(pool.pool_type, PoolType.GENERAL)
        self.assertEqual(pool.size_mb, 100)
        self.assertEqual(pool.allocated_size_mb, 100)
        self.assertEqual(pool.status, PoolStatus.ACTIVE)
        self.assertEqual(pool.creation_time, timestamp)
        self.assertEqual(pool.last_access_time, timestamp)
        self.assertEqual(pool.access_count, 5)
        self.assertEqual(pool.fragmentation_ratio, 0.2)
        self.assertEqual(pool.data_hash, "abc123")
        self.assertEqual(pool.backup_path, "/tmp/backup")
        self.assertTrue(pool.is_persistent)
        self.assertFalse(pool.compression_enabled)


@unittest.skipIf(skip_tests, "Memory management components not available")
class TestDefragmentationResult(unittest.TestCase):
    """Test DefragmentationResult dataclass"""

    def test_defragmentation_result_creation(self):
        """Test creation of DefragmentationResult"""
        timestamp = datetime.now()
        result = DefragmentationResult(
            timestamp=timestamp,
            pools_processed=5,
            memory_freed_mb=100.5,
            fragmentation_improvement=0.3,
            processing_time_seconds=2.5,
            success=True,
            errors=["Test error"]
        )

        self.assertEqual(result.timestamp, timestamp)
        self.assertEqual(result.pools_processed, 5)
        self.assertEqual(result.memory_freed_mb, 100.5)
        self.assertEqual(result.fragmentation_improvement, 0.3)
        self.assertEqual(result.processing_time_seconds, 2.5)
        self.assertTrue(result.success)
        self.assertEqual(result.errors, ["Test error"])


@unittest.skipIf(skip_tests, "Memory management components not available")
class TestPoolManagerFactory(unittest.TestCase):
    """Test factory functions for memory pool manager"""

    def test_create_pool_manager(self):
        """Test create_pool_manager factory function"""
        manager = create_pool_manager(
            max_pools=20,
            max_total_memory_mb=2048.0
        )
        self.assertIsInstance(manager, MemoryPoolManager)
        self.assertEqual(manager.max_pools, 20)
        self.assertEqual(manager.max_total_memory_mb, 2048.0)
        manager.shutdown()

    def test_temporary_pool_context_manager(self):
        """Test temporary pool context manager"""
        with temporary_pool("temp_pool", 50, PoolType.TEMPORARY) as (manager, pool):
            self.assertIsInstance(manager, MemoryPoolManager)
            self.assertIsInstance(pool, MemoryPool)
            self.assertEqual(pool.name, "temp_pool")
            self.assertEqual(pool.pool_type, PoolType.TEMPORARY)
            self.assertEqual(pool.size_mb, 50)
            self.assertEqual(pool.status, PoolStatus.ACTIVE)

        # Pool should be automatically cleaned up
        self.assertEqual(pool.status, PoolStatus.DELETED)


@unittest.skipIf(skip_tests, "Memory management components not available")
class TestPoolManagerIntegration(unittest.TestCase):
    """Integration tests for MemoryPoolManager"""

    def test_full_lifecycle(self):
        """Test complete pool lifecycle"""
        try:
            manager = create_pool_manager(
                max_pools=5,
                max_total_memory_mb=512.0,
                enable_backup=True
            )

            # Allocate pools
            pools = []
            for i in range(3):
                pool = manager.allocate_pool(
                    f"lifecycle_pool_{i}",
                    100 + (i * 50),
                    PoolType.DATA_PROCESSING
                )
                pools.append(pool)

            # Access and write to pools
            for i, pool in enumerate(pools):
                data = f"Data for pool {i}".encode() * 100
                success = manager.write_pool(pool.name, data)
                self.assertTrue(success)

                read_data = manager.access_pool(pool.name)
                self.assertIsNotNone(read_data)

            # Get statistics
            stats = manager.get_pool_statistics()
            self.assertEqual(stats.total_pools, 3)
            self.assertEqual(stats.active_pools, 3)

            # Run defragmentation
            defrag_result = manager._defragment_pools()
            self.assertIsInstance(defrag_result, DefragmentationResult)

            # Deallocate pools
            for pool in pools:
                success = manager.deallocate_pool(pool.name, force=True)
                self.assertTrue(success)

            manager.shutdown()

        except Exception as e:
            self.fail(f"Integration test failed: {e}")

    def test_concurrent_operations(self):
        """Test concurrent pool operations"""
        try:
            manager = create_pool_manager(max_pools=20)
            manager.start_monitoring()

            results = []
            errors = []

            def allocate_and_use_pool(pool_id):
                try:
                    pool_name = f"concurrent_pool_{pool_id}"
                    pool = manager.allocate_pool(pool_name, 50, PoolType.TEMPORARY)

                    # Write some data
                    data = f"Concurrent data {pool_id}".encode() * 50
                    success = manager.write_pool(pool_name, data)

                    # Read data back
                    read_data = manager.access_pool(pool_name)

                    # Clean up
                    manager.deallocate_pool(pool_name, force=True)

                    results.append((pool_id, success, len(read_data) if read_data else 0))

                except Exception as e:
                    errors.append((pool_id, str(e)))

            # Run concurrent operations
            threads = []
            for i in range(10):
                thread = threading.Thread(target=allocate_and_use_pool, args=(i,))
                threads.append(thread)
                thread.start()

            # Wait for all threads
            for thread in threads:
                thread.join(timeout=10.0)

            # Check results
            self.assertEqual(len(results), 10)
            self.assertEqual(len(errors), 0)  # No errors expected

            manager.shutdown()

        except Exception as e:
            self.fail(f"Concurrent operations test failed: {e}")


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryPoolManager))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryPool))
    suite.addTests(loader.loadTestsFromTestCase(TestDefragmentationResult))
    suite.addTests(loader.loadTestsFromTestCase(TestPoolManagerFactory))
    suite.addTests(loader.loadTestsFromTestCase(TestPoolManagerIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
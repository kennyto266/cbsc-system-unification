#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Memory Pool Manager
Tests memory pool allocation, deallocation, and management
"""

import os
import sys
import time
import unittest
import threading
import tempfile
import weakref
import gc
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import psutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class MockMemoryPool:
    """Mock implementation of Memory Pool for testing purposes"""

    def __init__(self, initial_size_mb=100, max_size_mb=1000, block_size_mb=10):
        self.initial_size_mb = initial_size_mb
        self.max_size_mb = max_size_mb
        self.block_size_mb = block_size_mb
        self.total_allocated_mb = 0
        self.free_blocks = []
        self.allocated_blocks = {}
        self.block_counter = 0
        self.allocation_lock = threading.Lock()
        self.stats = {
            'allocations': 0,
            'deallocations': 0,
            'expansions': 0,
            'fragmentations': 0,
            'peak_usage_mb': 0
        }

        # Initialize pool
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize the memory pool"""
        num_blocks = self.initial_size_mb // self.block_size_mb
        for i in range(num_blocks):
            block_id = f"block_{i}"
            self.free_blocks.append({
                'id': block_id,
                'size_mb': self.block_size_mb,
                'allocated_at': None,
                'freed_at': None
            })

        self.total_allocated_mb = self.initial_size_mb

    def allocate(self, size_mb, request_id=None):
        """Allocate memory block"""
        with self.allocation_lock:
            if request_id is None:
                request_id = f"req_{self.block_counter}"
                self.block_counter += 1

            # Check if we need to expand pool
            if not self.free_blocks and self.total_allocated_mb < self.max_size_mb:
                self._expand_pool()

            if not self.free_blocks:
                raise MemoryError("No available memory blocks")

            # Allocate block
            block = self.free_blocks.pop(0)
            block['allocated_at'] = datetime.now()
            block['request_id'] = request_id

            self.allocated_blocks[request_id] = block
            self.stats['allocations'] += 1

            # Update peak usage
            current_usage = len(self.allocated_blocks) * self.block_size_mb
            self.stats['peak_usage_mb'] = max(
                self.stats['peak_usage_mb'],
                current_usage
            )

            return {
                'block_id': block['id'],
                'size_mb': block['size_mb'],
                'request_id': request_id
            }

    def deallocate(self, request_id):
        """Deallocate memory block"""
        with self.allocation_lock:
            if request_id not in self.allocated_blocks:
                raise ValueError(f"Block {request_id} not allocated")

            block = self.allocated_blocks.pop(request_id)
            block['freed_at'] = datetime.now()
            block.pop('request_id', None)

            self.free_blocks.append(block)
            self.stats['deallocations'] += 1

            # Consider pool compaction if fragmentation is high
            if len(self.free_blocks) > len(self.allocated_blocks) * 2:
                self._compact_pool()

            return True

    def _expand_pool(self):
        """Expand the memory pool"""
        expansion_blocks = min(
            self.block_size_mb,  # Number of blocks to add
            (self.max_size_mb - self.total_allocated_mb) // self.block_size_mb
        )

        for i in range(expansion_blocks):
            block_id = f"exp_block_{self.block_counter}_{i}"
            self.free_blocks.append({
                'id': block_id,
                'size_mb': self.block_size_mb,
                'allocated_at': None,
                'freed_at': None
            })

        self.total_allocated_mb += expansion_blocks * self.block_size_mb
        self.stats['expansions'] += 1

    def _compact_pool(self):
        """Compact the memory pool to reduce fragmentation"""
        # Simple compaction: just track the event
        self.stats['fragmentations'] += 1

    def get_pool_statistics(self):
        """Get pool statistics"""
        with self.allocation_lock:
            return {
                'total_allocated_mb': self.total_allocated_mb,
                'max_size_mb': self.max_size_mb,
                'block_size_mb': self.block_size_mb,
                'free_blocks': len(self.free_blocks),
                'allocated_blocks': len(self.allocated_blocks),
                'utilization_percent': (len(self.allocated_blocks) * self.block_size_mb /
                                      self.total_allocated_mb * 100) if self.total_allocated_mb > 0 else 0,
                'stats': self.stats.copy()
            }

    def cleanup(self):
        """Cleanup all allocated blocks"""
        with self.allocation_lock:
            self.allocated_blocks.clear()
            self.free_blocks.clear()
            self.total_allocated_mb = 0
            self.stats = {
                'allocations': 0,
                'deallocations': 0,
                'expansions': 0,
                'fragmentations': 0,
                'peak_usage_mb': 0
            }


class MockMemoryPoolManager:
    """Mock implementation of Memory Pool Manager"""

    def __init__(self, default_pool_size_mb=100, max_pools=10):
        self.default_pool_size_mb = default_pool_size_mb
        self.max_pools = max_pools
        self.pools = {}
        self.pool_lock = threading.Lock()
        self.global_stats = {
            'total_pools_created': 0,
            'total_allocations': 0,
            'total_deallocations': 0,
            'memory_usage_mb': 0
        }

    def create_pool(self, pool_name, initial_size_mb=None, max_size_mb=1000, block_size_mb=10):
        """Create a new memory pool"""
        with self.pool_lock:
            if pool_name in self.pools:
                raise ValueError(f"Pool {pool_name} already exists")

            if len(self.pools) >= self.max_pools:
                raise RuntimeError("Maximum number of pools reached")

            if initial_size_mb is None:
                initial_size_mb = self.default_pool_size_mb

            pool = MockMemoryPool(initial_size_mb, max_size_mb, block_size_mb)
            self.pools[pool_name] = pool
            self.global_stats['total_pools_created'] += 1

            return pool

    def get_pool(self, pool_name):
        """Get existing memory pool"""
        with self.pool_lock:
            return self.pools.get(pool_name)

    def delete_pool(self, pool_name):
        """Delete a memory pool"""
        with self.pool_lock:
            if pool_name not in self.pools:
                raise ValueError(f"Pool {pool_name} does not exist")

            pool = self.pools.pop(pool_name)
            pool.cleanup()

    def allocate_from_pool(self, pool_name, size_mb, request_id=None):
        """Allocate memory from specific pool"""
        pool = self.get_pool(pool_name)
        if not pool:
            raise ValueError(f"Pool {pool_name} does not exist")

        result = pool.allocate(size_mb, request_id)
        self.global_stats['total_allocations'] += 1
        return result

    def deallocate_from_pool(self, pool_name, request_id):
        """Deallocate memory from specific pool"""
        pool = self.get_pool(pool_name)
        if not pool:
            raise ValueError(f"Pool {pool_name} does not exist")

        result = pool.deallocate(request_id)
        self.global_stats['total_deallocations'] += 1
        return result

    def get_global_statistics(self):
        """Get global statistics for all pools"""
        with self.pool_lock:
            total_memory_mb = sum(pool.total_allocated_mb for pool in self.pools.values())
            self.global_stats['memory_usage_mb'] = total_memory_mb

            pool_stats = {}
            for name, pool in self.pools.items():
                pool_stats[name] = pool.get_pool_statistics()

            return {
                'global_stats': self.global_stats.copy(),
                'pool_count': len(self.pools),
                'pool_stats': pool_stats
            }

    def cleanup_all_pools(self):
        """Cleanup all memory pools"""
        with self.pool_lock:
            for pool in self.pools.values():
                pool.cleanup()
            self.pools.clear()
            self.global_stats = {
                'total_pools_created': 0,
                'total_allocations': 0,
                'total_deallocations': 0,
                'memory_usage_mb': 0
            }


class TestMemoryPool(unittest.TestCase):
    """Test Memory Pool implementation"""

    def setUp(self):
        """Set up test fixtures"""
        self.pool = MockMemoryPool(
            initial_size_mb=100,
            max_size_mb=500,
            block_size_mb=10
        )

    def tearDown(self):
        """Clean up test fixtures"""
        self.pool.cleanup()

    def test_pool_initialization(self):
        """Test memory pool initialization"""
        self.assertEqual(self.pool.initial_size_mb, 100)
        self.assertEqual(self.pool.max_size_mb, 500)
        self.assertEqual(self.pool.block_size_mb, 10)
        self.assertEqual(len(self.pool.free_blocks), 10)  # 100MB / 10MB per block
        self.assertEqual(len(self.pool.allocated_blocks), 0)
        self.assertEqual(self.pool.total_allocated_mb, 100)

    def test_basic_allocation(self):
        """Test basic memory allocation"""
        allocation = self.pool.allocate(10)

        self.assertIn('block_id', allocation)
        self.assertIn('size_mb', allocation)
        self.assertIn('request_id', allocation)
        self.assertEqual(allocation['size_mb'], 10)
        self.assertEqual(len(self.pool.allocated_blocks), 1)
        self.assertEqual(len(self.pool.free_blocks), 9)

    def test_allocation_with_custom_request_id(self):
        """Test allocation with custom request ID"""
        custom_id = "custom_request_123"
        allocation = self.pool.allocate(10, custom_id)

        self.assertEqual(allocation['request_id'], custom_id)
        self.assertIn(custom_id, self.pool.allocated_blocks)

    def test_multiple_allocations(self):
        """Test multiple allocations"""
        allocations = []
        for i in range(5):
            allocation = self.pool.allocate(10)
            allocations.append(allocation)

        self.assertEqual(len(allocations), 5)
        self.assertEqual(len(self.pool.allocated_blocks), 5)
        self.assertEqual(len(self.pool.free_blocks), 5)

    def test_allocation_exceeds_pool(self):
        """Test allocation when pool is full"""
        # Allocate all blocks
        allocations = []
        for i in range(10):
            allocations.append(self.pool.allocate(10))

        # Try to allocate one more
        with self.assertRaises(MemoryError):
            self.pool.allocate(10)

    def test_basic_deallocation(self):
        """Test basic memory deallocation"""
        allocation = self.pool.allocate(10)
        request_id = allocation['request_id']

        result = self.pool.deallocate(request_id)

        self.assertTrue(result)
        self.assertEqual(len(self.pool.allocated_blocks), 0)
        self.assertEqual(len(self.pool.free_blocks), 10)

    def test_deallocate_nonexistent_block(self):
        """Test deallocation of non-existent block"""
        with self.assertRaises(ValueError):
            self.pool.deallocate("nonexistent_request")

    def test_pool_expansion(self):
        """Test automatic pool expansion"""
        # Fill initial pool
        allocations = []
        for i in range(10):
            allocations.append(self.pool.allocate(10))

        # Allocate one more to trigger expansion
        allocation = self.pool.allocate(10)

        self.assertEqual(len(self.pool.allocated_blocks), 11)
        self.assertGreater(self.pool.total_allocated_mb, 100)
        self.assertGreater(self.pool.stats['expansions'], 0)

    def test_pool_statistics(self):
        """Test pool statistics"""
        # Perform some allocations
        allocations = []
        for i in range(3):
            allocations.append(self.pool.allocate(10))

        # Deallocate one
        self.pool.deallocate(allocations[0]['request_id'])

        stats = self.pool.get_pool_statistics()

        self.assertIn('total_allocated_mb', stats)
        self.assertIn('free_blocks', stats)
        self.assertIn('allocated_blocks', stats)
        self.assertIn('utilization_percent', stats)
        self.assertIn('stats', stats)

        self.assertEqual(stats['allocated_blocks'], 2)
        self.assertEqual(stats['free_blocks'], 8)
        self.assertGreater(stats['utilization_percent'], 0)

    def test_peak_usage_tracking(self):
        """Test peak usage tracking"""
        # Allocate multiple blocks
        allocations = []
        for i in range(5):
            allocations.append(self.pool.allocate(10))

        stats = self.pool.get_pool_statistics()
        expected_peak = 5 * self.pool.block_size_mb  # 5 blocks * 10MB
        self.assertEqual(stats['stats']['peak_usage_mb'], expected_peak)

    def test_thread_safety(self):
        """Test thread safety of pool operations"""
        results = []
        errors = []

        def allocate_deallocate():
            try:
                allocation = self.pool.allocate(10)
                time.sleep(0.01)  # Small delay
                self.pool.deallocate(allocation['request_id'])
                results.append(True)
            except Exception as e:
                errors.append(e)

        # Run multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=allocate_deallocate)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify no errors and all operations completed
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 10)


class TestMemoryPoolManager(unittest.TestCase):
    """Test Memory Pool Manager"""

    def setUp(self):
        """Set up test fixtures"""
        self.manager = MockMemoryPoolManager(
            default_pool_size_mb=50,
            max_pools=5
        )

    def tearDown(self):
        """Clean up test fixtures"""
        self.manager.cleanup_all_pools()

    def test_manager_initialization(self):
        """Test memory pool manager initialization"""
        self.assertEqual(self.manager.default_pool_size_mb, 50)
        self.assertEqual(self.manager.max_pools, 5)
        self.assertEqual(len(self.manager.pools), 0)

    def test_create_pool(self):
        """Test creating a memory pool"""
        pool = self.manager.create_pool(
            "test_pool",
            initial_size_mb=100,
            max_size_mb=200,
            block_size_mb=20
        )

        self.assertIsNotNone(pool)
        self.assertEqual(pool.initial_size_mb, 100)
        self.assertEqual(pool.max_size_mb, 200)
        self.assertEqual(pool.block_size_mb, 20)
        self.assertIn("test_pool", self.manager.pools)
        self.assertEqual(self.manager.global_stats['total_pools_created'], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
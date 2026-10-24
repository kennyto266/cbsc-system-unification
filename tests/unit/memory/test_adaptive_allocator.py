#!/usr/bin/env python3
"""
Unit Tests for Adaptive Memory Allocator
Tests the adaptive memory allocation system for 32-core parallel processing
"""

import unittest
import sys
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime
import psutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from src.memory.adaptive_allocator import (
        AdaptiveMemoryAllocator, MemoryPressureLevel, AllocationStrategy,
        MemoryAllocationResult, SystemMemoryState, create_adaptive_allocator,
        calculate_memory_allocation
    )
except ImportError:
    # Skip tests if module not available
    skip_tests = True
else:
    skip_tests = False


@unittest.skipIf(skip_tests, "Memory management components not available")
class TestAdaptiveMemoryAllocator(unittest.TestCase):
    """Test cases for AdaptiveMemoryAllocator"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_memory_gb = 64.0
        self.test_processes = 32

        # Mock feature flags to enable testing
        with patch('src.memory.adaptive_allocator.AdaptiveMemoryAllocator._check_feature_flag', return_value=True):
            self.allocator = AdaptiveMemoryAllocator(
                total_memory_gb=self.test_memory_gb,
                enable_monitoring=False,  # Disable monitoring for tests
                safety_margin_percent=10.0
            )

    def tearDown(self):
        """Clean up test fixtures"""
        if hasattr(self, 'allocator'):
            self.allocator.shutdown()

    def test_initialization(self):
        """Test allocator initialization"""
        self.assertEqual(self.allocator.total_memory_gb, self.test_memory_gb)
        self.assertEqual(self.allocator.shared_memory_ratio, 0.3)  # Initial ratio
        self.assertEqual(self.allocator.pressure_threshold, 0.8)
        self.assertEqual(self.allocator.current_strategy, AllocationStrategy.ADAPTIVE)

    def test_calculate_optimal_allocation_basic(self):
        """Test basic optimal allocation calculation"""
        data_size_mb = 1024.0  # 1GB
        result = self.allocator.calculate_optimal_allocation(
            data_size_mb=data_size_mb,
            concurrent_processes=self.test_processes
        )

        self.assertIsInstance(result, MemoryAllocationResult)
        self.assertGreater(result.shared_memory_mb, 0)
        self.assertGreater(result.process_memory_mb, 0)
        self.assertGreater(result.safety_margin_mb, 0)
        self.assertLessEqual(result.allocation_efficiency, 1.0)

    def test_calculate_optimal_allocation_high_data_pressure(self):
        """Test allocation with high data pressure"""
        data_size_mb = self.test_memory_gb * 1024 * 0.7  # 70% of total memory
        result = self.allocator.calculate_optimal_allocation(
            data_size_mb=data_size_mb,
            concurrent_processes=self.test_processes
        )

        # With high data pressure, shared memory ratio should increase
        self.assertGreater(self.allocator.shared_memory_ratio, 0.3)
        self.assertIn(result.strategy_used, [AllocationStrategy.ADAPTIVE, AllocationStrategy.BALANCED])

    def test_calculate_optimal_allocation_low_data_pressure(self):
        """Test allocation with low data pressure"""
        data_size_mb = self.test_memory_gb * 1024 * 0.05  # 5% of total memory
        result = self.allocator.calculate_optimal_allocation(
            data_size_mb=data_size_mb,
            concurrent_processes=self.test_processes
        )

        # With low data pressure, shared memory ratio might decrease
        self.assertLessEqual(self.allocator.shared_memory_ratio, 0.3)
        self.assertGreater(result.allocation_efficiency, 0.5)

    def test_safety_checks(self):
        """Test memory allocation safety checks"""
        # Mock low available memory
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value.available = 100 * 1024 * 1024  # 100MB available
            mock_memory.return_value.total = self.test_memory_gb * 1024 * 1024 * 1024

            result = self.allocator.calculate_optimal_allocation(
                data_size_mb=2048,  # Request 2GB
                concurrent_processes=self.test_processes
            )

            # Should scale down allocation due to low available memory
            self.assertLess(result.shared_memory_mb + (result.process_memory_mb * self.test_processes),
                          mock_memory.return_value.available * 0.9)

    def test_minimum_allocations(self):
        """Test minimum memory allocation constraints"""
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value.available = 10 * 1024 * 1024  # Very low memory
            mock_memory.return_value.total = self.test_memory_gb * 1024 * 1024 * 1024

            result = self.allocator.calculate_optimal_allocation(
                data_size_mb=100,
                concurrent_processes=self.test_processes
            )

            # Should maintain minimum allocations
            self.assertGreaterEqual(result.shared_memory_mb, 512)
            self.assertGreaterEqual(result.process_memory_mb, 256)
            self.assertGreaterEqual(result.safety_margin_mb, 512)

    def test_task_type_adjustments(self):
        """Test allocation adjustments based on task type"""
        data_size_mb = 1024.0

        # Test backtesting task
        result_backtesting = self.allocator.calculate_optimal_allocation(
            data_size_mb=data_size_mb,
            concurrent_processes=self.test_processes,
            task_type="backtesting"
        )

        # Test optimization task
        result_optimization = self.allocator.calculate_optimal_allocation(
            data_size_mb=data_size_mb,
            concurrent_processes=self.test_processes,
            task_type="optimization"
        )

        # Backtesting should generally allocate more shared memory
        self.assertGreaterEqual(result_backtesting.shared_memory_mb,
                              result_optimization.shared_memory_mb)

    def test_allocation_statistics(self):
        """Test allocation statistics tracking"""
        # Perform several allocations
        for i in range(5):
            self.allocator.calculate_optimal_allocation(
                data_size_mb=100 * (i + 1),
                concurrent_processes=self.test_processes
            )

        stats = self.allocator.get_allocation_statistics()

        self.assertIn('total_allocations', stats)
        self.assertIn('current_strategy', stats)
        self.assertIn('current_pressure', stats)
        self.assertIn('shared_memory_ratio', stats)
        self.assertGreater(stats['total_allocations'], 0)

    def test_memory_pressure_levels(self):
        """Test memory pressure level detection"""
        # Test LOW pressure
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value.percent = 30.0
            state = self.allocator._capture_system_state()
            self.assertEqual(state.pressure_level, MemoryPressureLevel.LOW)

        # Test MEDIUM pressure
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value.percent = 60.0
            state = self.allocator._capture_system_state()
            self.assertEqual(state.pressure_level, MemoryPressureLevel.MEDIUM)

        # Test HIGH pressure
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value.percent = 80.0
            state = self.allocator._capture_system_state()
            self.assertEqual(state.pressure_level, MemoryPressureLevel.HIGH)

        # Test CRITICAL pressure
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value.percent = 95.0
            state = self.allocator._capture_system_state()
            self.assertEqual(state.pressure_level, MemoryPressureLevel.CRITICAL)

    def test_strategy_adjustment(self):
        """Test allocation strategy adjustment based on pressure"""
        # Simulate HIGH pressure
        self.allocator.current_pressure = MemoryPressureLevel.HIGH
        self.allocator._adjust_strategy_if_needed(
            SystemMemoryState(
                timestamp=datetime.now(),
                total_memory_gb=self.test_memory_gb,
                available_memory_gb=self.test_memory_gb * 0.2,
                used_memory_gb=self.test_memory_gb * 0.8,
                usage_percent=80.0,
                pressure_level=MemoryPressureLevel.HIGH,
                active_processes=self.test_processes,
                gc_collections=0,
                fragmentation_estimate=0.1
            )
        )

        # Strategy should become CONSERVATIVE or BALANCED
        self.assertIn(self.allocator.current_strategy,
                     [AllocationStrategy.CONSERVATIVE, AllocationStrategy.BALANCED])

    def test_fallback_allocation(self):
        """Test fallback allocation when calculation fails"""
        with patch.object(self.allocator, 'calculate_optimal_allocation',
                        side_effect=Exception("Test exception")):
            result = self.allocator._get_fallback_allocation(
                data_size_mb=1000.0,
                concurrent_processes=self.test_processes
            )

            self.assertIsInstance(result, MemoryAllocationResult)
            self.assertEqual(result.strategy_used, AllocationStrategy.CONSERVATIVE)
            self.assertIn("fallback", result.recommendations[0].lower())

    def test_context_manager(self):
        """Test allocator context manager functionality"""
        with self.allocator.temporary_allocation(
            data_size_mb=500.0,
            concurrent_processes=16
        ) as allocation:
            self.assertIsInstance(allocation, MemoryAllocationResult)
            self.assertGreater(allocation.shared_memory_mb, 0)


@unittest.skipIf(skip_tests, "Memory management components not available")
class TestAdaptiveAllocatorFactory(unittest.TestCase):
    """Test factory functions for adaptive allocator"""

    def test_create_adaptive_allocator(self):
        """Test create_adaptive_allocator factory function"""
        allocator = create_adaptive_allocator(total_memory_gb=32.0)
        self.assertIsInstance(allocator, AdaptiveMemoryAllocator)
        self.assertEqual(allocator.total_memory_gb, 32.0)
        allocator.shutdown()

    @patch('psutil.virtual_memory')
    def test_create_adaptive_allocator_auto_detect(self, mock_memory):
        """Test auto-detection of system memory"""
        mock_memory.return_value.total = 32 * 1024 * 1024 * 1024  # 32GB

        allocator = create_adaptive_allocator()  # No memory specified
        self.assertEqual(allocator.total_memory_gb, 32.0)
        allocator.shutdown()

    def test_calculate_memory_allocation(self):
        """Test calculate_memory_allocation utility function"""
        result = calculate_memory_allocation(
            data_size_mb=1024,
            concurrent_processes=16,
            total_memory_gb=32.0
        )

        self.assertIsInstance(result, dict)
        self.assertIn('shared_memory_mb', result)
        self.assertIn('process_memory_mb', result)
        self.assertIn('safety_margin_mb', result)
        self.assertIn('efficiency', result)

        self.assertGreater(result['shared_memory_mb'], 0)
        self.assertGreater(result['process_memory_mb'], 0)
        self.assertGreater(result['safety_margin_mb'], 0)


@unittest.skipIf(skip_tests, "Memory management components not available")
class TestMemoryAllocationResult(unittest.TestCase):
    """Test MemoryAllocationResult dataclass"""

    def test_memory_allocation_result_creation(self):
        """Test creation of MemoryAllocationResult"""
        timestamp = datetime.now()
        result = MemoryAllocationResult(
            timestamp=timestamp,
            total_memory_gb=64.0,
            shared_memory_mb=2048,
            process_memory_mb=128,
            safety_margin_mb=512,
            strategy_used=AllocationStrategy.BALANCED,
            pressure_level=MemoryPressureLevel.MEDIUM,
            data_pressure_ratio=0.25,
            concurrent_processes=32,
            allocation_efficiency=0.85,
            recommendations=["Test recommendation"]
        )

        self.assertEqual(result.timestamp, timestamp)
        self.assertEqual(result.total_memory_gb, 64.0)
        self.assertEqual(result.shared_memory_mb, 2048)
        self.assertEqual(result.process_memory_mb, 128)
        self.assertEqual(result.safety_margin_mb, 512)
        self.assertEqual(result.strategy_used, AllocationStrategy.BALANCED)
        self.assertEqual(result.pressure_level, MemoryPressureLevel.MEDIUM)
        self.assertEqual(result.data_pressure_ratio, 0.25)
        self.assertEqual(result.concurrent_processes, 32)
        self.assertEqual(result.allocation_efficiency, 0.85)
        self.assertEqual(result.recommendations, ["Test recommendation"])


@unittest.skipIf(skip_tests, "Memory management components not available")
class TestSystemMemoryState(unittest.TestCase):
    """Test SystemMemoryState dataclass"""

    def test_system_memory_state_creation(self):
        """Test creation of SystemMemoryState"""
        timestamp = datetime.now()
        state = SystemMemoryState(
            timestamp=timestamp,
            total_memory_gb=64.0,
            available_memory_gb=32.0,
            used_memory_gb=32.0,
            usage_percent=50.0,
            pressure_level=MemoryPressureLevel.MEDIUM,
            active_processes=32,
            gc_collections=5,
            fragmentation_estimate=0.15
        )

        self.assertEqual(state.timestamp, timestamp)
        self.assertEqual(state.total_memory_gb, 64.0)
        self.assertEqual(state.available_memory_gb, 32.0)
        self.assertEqual(state.used_memory_gb, 32.0)
        self.assertEqual(state.usage_percent, 50.0)
        self.assertEqual(state.pressure_level, MemoryPressureLevel.MEDIUM)
        self.assertEqual(state.active_processes, 32)
        self.assertEqual(state.gc_collections, 5)
        self.assertEqual(state.fragmentation_estimate, 0.15)


class TestAdaptiveAllocatorIntegration(unittest.TestCase):
    """Integration tests for AdaptiveMemoryAllocator"""

    @unittest.skipIf(skip_tests, "Memory management components not available")
    def test_allocator_with_real_memory_info(self):
        """Test allocator with actual system memory information"""
        try:
            allocator = create_adaptive_allocator()

            # Test allocation with realistic parameters
            result = allocator.calculate_optimal_allocation(
                data_size_mb=2048,  # 2GB data
                concurrent_processes=32,
                task_type="backtesting"
            )

            # Validate results are reasonable
            self.assertGreater(result.shared_memory_mb, 0)
            self.assertGreater(result.process_memory_mb, 0)
            self.assertLess(result.allocation_efficiency, 1.0)
            self.assertGreaterEqual(result.allocation_efficiency, 0.0)

            allocator.shutdown()

        except Exception as e:
            self.fail(f"Integration test failed: {e}")


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestAdaptiveMemoryAllocator))
    suite.addTests(loader.loadTestsFromTestCase(TestAdaptiveAllocatorFactory))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryAllocationResult))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemMemoryState))
    suite.addTests(loader.loadTestsFromTestCase(TestAdaptiveAllocatorIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
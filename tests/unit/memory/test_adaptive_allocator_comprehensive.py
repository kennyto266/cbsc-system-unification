#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Adaptive Memory Allocator
Tests memory management components with 95%+ coverage target
"""

import os
import sys
import time
import unittest
import threading
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
import psutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.memory.adaptive_allocator import (
    AdaptiveMemoryAllocator,
    MemoryPressureLevel,
    AllocationStrategy,
    MemoryAllocationResult,
    SystemMemoryState,
    create_adaptive_allocator,
    calculate_memory_allocation
)


class TestAdaptiveMemoryAllocator(unittest.TestCase):
    """Comprehensive test suite for AdaptiveMemoryAllocator"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_memory_gb = 16.0
        self.temp_dir = tempfile.mkdtemp()

        # Mock feature flag file
        self.feature_flag_file = Path(self.temp_dir) / "feature_flags.yaml"
        self.feature_flag_data = {
            'feature_flags': {
                'enable_adaptive_memory': True
            }
        }

        with open(self.feature_flag_file, 'w') as f:
            import yaml
            yaml.dump(self.feature_flag_data, f)

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.memory.adaptive_allocator.psutil.virtual_memory')
    @patch('src.memory.adaptive_allocator.Path')
    def test_allocator_initialization(self, mock_path, mock_virtual_memory):
        """Test allocator initialization with various configurations"""
        # Mock system memory
        mock_memory = Mock()
        mock_memory.total = 16 * 1024**3  # 16GB
        mock_memory.available = 8 * 1024**3  # 8GB
        mock_memory.percent = 50.0
        mock_virtual_memory.return_value = mock_memory

        # Mock feature flag file path
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.__truediv__ = Mock(return_value=self.feature_flag_file)
        mock_path.return_value = mock_path_instance

        # Test basic initialization
        allocator = AdaptiveMemoryAllocator(
            total_memory_gb=16.0,
            enable_monitoring=False,
            safety_margin_percent=15.0
        )

        self.assertEqual(allocator.total_memory_gb, 16.0)
        self.assertEqual(allocator.safety_margin_percent, 15.0)
        self.assertEqual(allocator.shared_memory_ratio, 0.3)
        self.assertEqual(allocator.current_strategy, AllocationStrategy.ADAPTIVE)
        self.assertFalse(allocator.enable_monitoring)

    def test_memory_pressure_level_determination(self):
        """Test memory pressure level calculation"""
        allocator = AdaptiveMemoryAllocator(
            total_memory_gb=16.0,
            enable_monitoring=False
        )

        # Test LOW pressure
        memory_state = SystemMemoryState(
            timestamp=datetime.now(),
            total_memory_gb=16.0,
            available_memory_gb=8.0,
            used_memory_gb=8.0,
            usage_percent=45.0,
            pressure_level=MemoryPressureLevel.LOW,
            active_processes=10,
            gc_collections=0,
            fragmentation_estimate=0.1
        )

        allocator._update_pressure_level(memory_state)
        self.assertEqual(allocator.current_pressure, MemoryPressureLevel.LOW)

        # Test MEDIUM pressure
        memory_state.usage_percent = 60.0
        allocator._update_pressure_level(memory_state)
        self.assertEqual(allocator.current_pressure, MemoryPressureLevel.MEDIUM)

        # Test HIGH pressure
        memory_state.usage_percent = 80.0
        allocator._update_pressure_level(memory_state)
        self.assertEqual(allocator.current_pressure, MemoryPressureLevel.HIGH)

        # Test CRITICAL pressure
        memory_state.usage_percent = 90.0
        allocator._update_pressure_level(memory_state)
        self.assertEqual(allocator.current_pressure, MemoryPressureLevel.CRITICAL)

    def test_allocation_strategy_adjustment(self):
        """Test allocation strategy adjustment based on memory pressure"""
        allocator = AdaptiveMemoryAllocator(
            total_memory_gb=16.0,
            enable_monitoring=False
        )

        memory_state = SystemMemoryState(
            timestamp=datetime.now(),
            total_memory_gb=16.0,
            available_memory_gb=8.0,
            used_memory_gb=8.0,
            usage_percent=45.0,
            pressure_level=MemoryPressureLevel.LOW,
            active_processes=10,
            gc_collections=0,
            fragmentation_estimate=0.1
        )

        # Test adjustment to CONSERVATIVE strategy
        memory_state.usage_percent = 90.0
        allocator._adjust_strategy_if_needed(memory_state)
        self.assertEqual(allocator.current_strategy, AllocationStrategy.CONSERVATIVE)
        self.assertLessEqual(allocator.shared_memory_ratio, 0.2)

        # Test adjustment to AGGRESSIVE strategy
        memory_state.usage_percent = 30.0
        allocator._adjust_strategy_if_needed(memory_state)
        self.assertEqual(allocator.current_strategy, AllocationStrategy.AGGRESSIVE)

    @patch('src.memory.adaptive_allocator.psutil.virtual_memory')
    @patch('src.memory.adaptive_allocator.Path')
    def test_optimal_allocation_calculation(self, mock_path, mock_virtual_memory):
        """Test optimal memory allocation calculation"""
        # Mock system memory
        mock_memory = Mock()
        mock_memory.total = 16 * 1024**3
        mock_memory.available = 8 * 1024**3
        mock_memory.percent = 50.0
        mock_virtual_memory.return_value = mock_memory

        # Mock feature flag
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.__truediv__ = Mock(return_value=self.feature_flag_file)
        mock_path.return_value = mock_path_instance

        allocator = AdaptiveMemoryAllocator(
            total_memory_gb=16.0,
            enable_monitoring=False
        )

        # Test basic allocation
        result = allocator.calculate_optimal_allocation(
            data_size_mb=1000.0,
            concurrent_processes=8,
            task_type="backtesting"
        )

        self.assertIsInstance(result, MemoryAllocationResult)
        self.assertGreater(result.shared_memory_mb, 0)
        self.assertGreater(result.process_memory_mb, 0)
        self.assertGreater(result.safety_margin_mb, 0)
        self.assertEqual(result.concurrent_processes, 8)
        self.assertEqual(result.task_type if hasattr(result, 'task_type') else None, None)  # Not stored in result
        self.assertIsInstance(result.allocation_efficiency, float)
        self.assertGreaterEqual(result.allocation_efficiency, 0.0)
        self.assertLessEqual(result.allocation_efficiency, 1.0)

    def test_shared_memory_ratio_adjustment(self):
        """Test shared memory ratio adjustment based on various factors"""
        allocator = AdaptiveMemoryAllocator(
            total_memory_gb=16.0,
            enable_monitoring=False
        )

        # Test high data pressure
        allocator._adjust_shared_memory_ratio(
            data_pressure=0.7,  # 70% data pressure
            concurrent_processes=16,
            task_type="backtesting"
        )
        self.assertGreater(allocator.shared_memory_ratio, 0.3)

        # Test low data pressure
        allocator.shared_memory_ratio = 0.3  # Reset
        allocator._adjust_shared_memory_ratio(
            data_pressure=0.05,  # 5% data pressure
            concurrent_processes=4,
            task_type="data_processing"
        )
        self.assertLess(allocator.shared_memory_ratio, 0.3)

        # Test high process count
        allocator.shared_memory_ratio = 0.3  # Reset
        allocator._adjust_shared_memory_ratio(
            data_pressure=0.2,
            concurrent_processes=28,  # High concurrency
            task_type="optimization"
        )
        self.assertGreater(allocator.shared_memory_ratio, 0.3)

    def test_safety_checks_application(self):
        """Test safety checks to prevent OOM"""
        allocator = AdaptiveMemoryAllocator(
            total_memory_gb=16.0,
            enable_monitoring=False
        )

        memory_state = SystemMemoryState(
            timestamp=datetime.now(),
            total_memory_gb=16.0,
            available_memory_gb=2.0,  # Low available memory
            used_memory_gb=14.0,
            usage_percent=87.5,
            pressure_level=MemoryPressureLevel.CRITICAL,
            active_processes=10,
            gc_collections=0,
            fragmentation_estimate=0.1
        )

        # Test with high allocation request
        shared_memory_mb = 4096  # 4GB
        process_memory_mb = 2048  # 2GB per process
        safety_margin_mb = 1024  # 1GB

        allocation = allocator._apply_safety_checks(
            shared_memory_mb, process_memory_mb, safety_margin_mb, memory_state
        )

        # Should be scaled down due to memory constraints
        self.assertLess(allocation['shared_memory_mb'], shared_memory_mb)
        self.assertLess(allocation['process_memory_mb'], process_memory_mb)
        self.assertGreaterEqual(allocation['safety_margin_mb'], 512)  # Minimum 512MB

    def test_fallback_allocation(self):
        """Test fallback allocation when calculation fails"""
        allocator = AdaptiveMemoryAllocator(
            total_memory_gb=16.0,
            enable_monitoring=False
        )

        result = allocator._get_fallback_allocation(
            data_size_mb=1000.0,
            concurrent_processes=8
        )

        self.assertIsInstance(result, MemoryAllocationResult)
        self.assertEqual(result.strategy_used, AllocationStrategy.CONSERVATIVE)
        self.assertEqual(result.pressure_level, MemoryPressureLevel.MEDIUM)
        self.assertEqual(result.allocation_efficiency, 0.7)
        self.assertIn("Fallback allocation used", result.recommendations)

    def test_allocation_statistics(self):
        """Test allocation statistics tracking"""
        allocator = AdaptiveMemoryAllocator(
            total_memory_gb=16.0,
            enable_monitoring=False
        )

        # Add some mock allocation history
        for i in range(10):
            result = MemoryAllocationResult(
                timestamp=datetime.now(),
                total_memory_gb=16.0,
                shared_memory_mb=1000 + i * 100,
                process_memory_mb=500 + i * 50,
                safety_margin_mb=500,
                strategy_used=AllocationStrategy.ADAPTIVE,
                pressure_level=MemoryPressureLevel.LOW,
                data_pressure_ratio=0.1,
                concurrent_processes=8,
                allocation_efficiency=0.8 + i * 0.01
            )
            allocator.allocation_history.append(result)
            allocator.total_allocations += 1

        stats = allocator.get_allocation_statistics()

        self.assertIn('total_allocations', stats)
        self.assertIn('current_strategy', stats)
        self.assertIn('recent_stats', stats)
        self.assertIn('fragmentation', stats)
        self.assertEqual(stats['total_allocations'], 10)

    def test_recommendation_generation(self):
        """Test recommendation generation based on allocation analysis"""
        allocator = AdaptiveMemoryAllocator(
            total_memory_gb=16.0,
            enable_monitoring=False
        )

        memory_state = SystemMemoryState(
            timestamp=datetime.now(),
            total_memory_gb=16.0,
            available_memory_gb=1.6,  # High memory pressure
            used_memory_gb=14.4,
            usage_percent=90.0,
            pressure_level=MemoryPressureLevel.CRITICAL,
            active_processes=10,
            gc_collections=0,
            fragmentation_estimate=0.4  # High fragmentation
        )

        allocation = {
            'shared_memory_mb': 2048,
            'process_memory_mb': 1024,
            'safety_margin_mb': 512
        }

        recommendations = allocator._generate_recommendations(
            data_pressure=0.8,  # High data pressure
            memory_state=memory_state,
            allocation=allocation
        )

        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

        # Check for expected recommendations
        rec_text = ' '.join(recommendations)
        self.assertIn('chunks', rec_text)  # Should suggest smaller chunks
        self.assertIn('critical', rec_text.lower())  # Should mention critical pressure

    def test_memory_defragmentation_trigger(self):
        """Test memory defragmentation triggering"""
        allocator = AdaptiveMemoryAllocator(
            total_memory_gb=16.0,
            enable_monitoring=False,
            enable_fragmentation_tracking=True
        )

        memory_state = SystemMemoryState(
            timestamp=datetime.now(),
            total_memory_gb=16.0,
            available_memory_gb=8.0,
            used_memory_gb=8.0,
            usage_percent=50.0,
            pressure_level=MemoryPressureLevel.LOW,
            active_processes=10,
            gc_collections=0,
            fragmentation_estimate=0.35  # Above 30% threshold
        )

        # Track fragmentation to trigger defragmentation
        allocator._track_fragmentation(memory_state)

        # Check that defragmentation was triggered
        self.assertIsNotNone(allocator.last_defragmentation)

    @patch('src.memory.adaptive_allocator.psutil.virtual_memory')
    @patch('src.memory.adaptive_allocator.Path')
    def test_factory_function(self, mock_path, mock_virtual_memory):
        """Test factory function for creating allocator"""
        # Mock system memory
        mock_memory = Mock()
        mock_memory.total = 32 * 1024**3  # 32GB
        mock_virtual_memory.return_value = mock_memory

        # Mock feature flag
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = False  # No feature flag file
        mock_path_instance.__truediv__ = Mock(return_value=self.feature_flag_file)
        mock_path.return_value = mock_path_instance

        # Test auto-detection
        allocator = create_adaptive_allocator()
        self.assertEqual(allocator.total_memory_gb, 32.0)

        # Test with specified memory
        allocator = create_adaptive_allocator(total_memory_gb=24.0)
        self.assertEqual(allocator.total_memory_gb, 24.0)

    @patch('src.memory.adaptive_allocator.psutil.virtual_memory')
    @patch('src.memory.adaptive_allocator.Path')
    def test_utility_function(self, mock_path, mock_virtual_memory):
        """Test utility function for quick allocation calculation"""
        # Mock system memory
        mock_memory = Mock()
        mock_memory.total = 16 * 1024**3
        mock_memory.available = 8 * 1024**3
        mock_memory.percent = 50.0
        mock_virtual_memory.return_value = mock_memory

        # Mock feature flag
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = False
        mock_path_instance.__truediv__ = Mock(return_value=self.feature_flag_file)
        mock_path.return_value = mock_path_instance

        result = calculate_memory_allocation(
            data_size_mb=2000.0,
            concurrent_processes=16,
            total_memory_gb=16.0
        )

        self.assertIn('shared_memory_mb', result)
        self.assertIn('process_memory_mb', result)
        self.assertIn('safety_margin_mb', result)
        self.assertIn('efficiency', result)
        self.assertIsInstance(result['efficiency'], float)

    def test_context_manager_usage(self):
        """Test allocator usage as context manager"""
        allocator = AdaptiveMemoryAllocator(
            total_memory_gb=16.0,
            enable_monitoring=False
        )

        with patch.object(allocator, 'calculate_optimal_allocation') as mock_calc:
            mock_result = Mock()
            mock_result.shared_memory_mb = 2048
            mock_result.process_memory_mb = 1024
            mock_calc.return_value = mock_result

            with allocator.temporary_allocation(data_size_mb=1000.0, concurrent_processes=4) as allocation:
                self.assertEqual(allocation, mock_result)
                mock_calc.assert_called_once_with(1000.0, 4)

    def test_thread_safety(self):
        """Test thread safety of allocation calculations"""
        allocator = AdaptiveMemoryAllocator(
            total_memory_gb=16.0,
            enable_monitoring=False
        )

        results = []
        errors = []

        def allocate_memory():
            try:
                result = allocator.calculate_optimal_allocation(
                    data_size_mb=500.0,
                    concurrent_processes=4
                )
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Run multiple threads simultaneously
        threads = []
        for i in range(10):
            thread = threading.Thread(target=allocate_memory)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 10, "Not all allocations completed")

    def test_shutdown_procedure(self):
        """Test proper shutdown procedure"""
        allocator = AdaptiveMemoryAllocator(
            total_memory_gb=16.0,
            enable_monitoring=False
        )

        # Start a mock monitoring thread
        allocator.monitoring_active = True
        allocator.monitor_thread = Mock()
        allocator.monitor_thread.is_alive.return_value = True
        allocator.monitor_thread.join = Mock()

        # Test shutdown
        allocator.shutdown()

        self.assertFalse(allocator.monitoring_active)
        allocator.monitor_thread.join.assert_called_once_with(timeout=5.0)


class TestMemoryAllocationResult(unittest.TestCase):
    """Test MemoryAllocationResult dataclass"""

    def test_result_creation(self):
        """Test MemoryAllocationResult creation and attributes"""
        timestamp = datetime.now()
        result = MemoryAllocationResult(
            timestamp=timestamp,
            total_memory_gb=16.0,
            shared_memory_mb=2048,
            process_memory_mb=1024,
            safety_margin_mb=512,
            strategy_used=AllocationStrategy.ADAPTIVE,
            pressure_level=MemoryPressureLevel.MEDIUM,
            data_pressure_ratio=0.2,
            concurrent_processes=8,
            allocation_efficiency=0.85,
            recommendations=["Test recommendation"]
        )

        self.assertEqual(result.timestamp, timestamp)
        self.assertEqual(result.total_memory_gb, 16.0)
        self.assertEqual(result.shared_memory_mb, 2048)
        self.assertEqual(result.process_memory_mb, 1024)
        self.assertEqual(result.safety_margin_mb, 512)
        self.assertEqual(result.strategy_used, AllocationStrategy.ADAPTIVE)
        self.assertEqual(result.pressure_level, MemoryPressureLevel.MEDIUM)
        self.assertEqual(result.data_pressure_ratio, 0.2)
        self.assertEqual(result.concurrent_processes, 8)
        self.assertEqual(result.allocation_efficiency, 0.85)
        self.assertEqual(len(result.recommendations), 1)


class TestSystemMemoryState(unittest.TestCase):
    """Test SystemMemoryState dataclass"""

    def test_state_creation(self):
        """Test SystemMemoryState creation and attributes"""
        timestamp = datetime.now()
        state = SystemMemoryState(
            timestamp=timestamp,
            total_memory_gb=16.0,
            available_memory_gb=8.0,
            used_memory_gb=8.0,
            usage_percent=50.0,
            pressure_level=MemoryPressureLevel.LOW,
            active_processes=10,
            gc_collections=5,
            fragmentation_estimate=0.1
        )

        self.assertEqual(state.timestamp, timestamp)
        self.assertEqual(state.total_memory_gb, 16.0)
        self.assertEqual(state.available_memory_gb, 8.0)
        self.assertEqual(state.used_memory_gb, 8.0)
        self.assertEqual(state.usage_percent, 50.0)
        self.assertEqual(state.pressure_level, MemoryPressureLevel.LOW)
        self.assertEqual(state.active_processes, 10)
        self.assertEqual(state.gc_collections, 5)
        self.assertEqual(state.fragmentation_estimate, 0.1)

    def test_state_serialization(self):
        """Test SystemMemoryState serialization"""
        timestamp = datetime.now()
        state = SystemMemoryState(
            timestamp=timestamp,
            total_memory_gb=16.0,
            available_memory_gb=8.0,
            used_memory_gb=8.0,
            usage_percent=50.0,
            pressure_level=MemoryPressureLevel.LOW,
            active_processes=10,
            gc_collections=5,
            fragmentation_estimate=0.1
        )

        # This would be used in the actual atomic initializer
        # Test that the state can be converted to dict
        state_dict = state.__dict__
        self.assertIn('timestamp', state_dict)
        self.assertIn('total_memory_gb', state_dict)


if __name__ == '__main__':
    unittest.main(verbosity=2)
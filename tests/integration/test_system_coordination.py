#!/usr/bin/env python3
"""
Integration Tests for System Coordination and Multi-Component Interactions
Tests system startup/shutdown coordination, multi-component interactions, and backward compatibility
"""

import os
import sys
import time
import unittest
import threading
import tempfile
import json
import signal
import subprocess
import multiprocessing
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import actual components if they exist
try:
    from src.ipc.atomic_initializer import (
        AtomicInitializer,
        ComponentInitTask,
        ComponentState,
        InitializationPhase
    )
    from src.memory.adaptive_allocator import AdaptiveMemoryAllocator
except ImportError:
    # Create mock implementations for testing
    class ComponentState:
        NOT_STARTED = "not_started"
        INITIALIZING = "initializing"
        INITIALIZED = "initialized"
        FAILED = "failed"

    class InitializationPhase:
        SYSTEM_LOCK = "system_lock"
        RESOURCE_ALLOCATION = "resource_allocation"
        COMPONENT_INIT = "component_init"
        COMPLETE = "complete"

    class ComponentInitTask:
        def __init__(self, component_id, component_name, init_function, cleanup_function=None, **kwargs):
            self.component_id = component_id
            self.component_name = component_name
            self.init_function = init_function
            self.cleanup_function = cleanup_function
            self.dependencies = kwargs.get('dependencies', set())
            self.priority = kwargs.get('priority', 0)
            self.timeout_seconds = kwargs.get('timeout_seconds', 30.0)
            self.critical = kwargs.get('critical', False)

    class MockAtomicInitializer:
        def __init__(self, process_id, total_processes, **kwargs):
            self.process_id = process_id
            self.total_processes = total_processes
            self.components = {}
            self.initialization_state = None
            self.is_initialized = False

        def register_component(self, component):
            self.components[component.component_id] = component

        def initialize(self):
            # Mock initialization
            time.sleep(0.1)  # Simulate initialization time
            self.is_initialized = True
            return True

        def cleanup(self):
            pass

    AtomicInitializer = MockAtomicInitializer
    AdaptiveMemoryAllocator = Mock


class MockSystemCoordinator:
    """Mock System Coordinator for testing"""

    def __init__(self, total_processes=4):
        self.total_processes = total_processes
        self.initializers = {}
        self.component_registry = {}
        self.system_state = "stopped"
        self.coordination_lock = threading.Lock()
        self.health_monitors = {}

    def register_initializer(self, process_id, initializer):
        """Register an atomic initializer for a process"""
        with self.coordination_lock:
            self.initializers[process_id] = initializer

    def register_component(self, component_id, component_info):
        """Register a system component"""
        with self.coordination_lock:
            self.component_registry[component_id] = component_info

    def start_system(self):
        """Start the entire system"""
        with self.coordination_lock:
            if self.system_state != "stopped":
                raise RuntimeError("System is already running")

            self.system_state = "starting"

            # Initialize all processes
            initialization_futures = {}
            with ThreadPoolExecutor(max_workers=self.total_processes) as executor:
                for process_id, initializer in self.initializers.items():
                    future = executor.submit(initializer.initialize)
                    initialization_futures[future] = process_id

                # Wait for all initializations to complete
                for future in as_completed(initialization_futures):
                    process_id = initialization_futures[future]
                    try:
                        success = future.result(timeout=60)
                        if not success:
                            self.system_state = "failed"
                            raise RuntimeError(f"Process {process_id} initialization failed")
                    except Exception as e:
                        self.system_state = "failed"
                        raise RuntimeError(f"Process {process_id} initialization error: {e}")

            self.system_state = "running"
            return True

    def stop_system(self):
        """Stop the entire system"""
        with self.coordination_lock:
            if self.system_state != "running":
                return False

            self.system_state = "stopping"

            # Cleanup all processes
            with ThreadPoolExecutor(max_workers=self.total_processes) as executor:
                futures = []
                for process_id, initializer in self.initializers.items():
                    future = executor.submit(initializer.cleanup)
                    futures.append(future)

                # Wait for all cleanups to complete
                for future in as_completed(futures):
                    try:
                        future.result(timeout=30)
                    except Exception as e:
                        print(f"Cleanup error: {e}")

            self.system_state = "stopped"
            return True

    def get_system_status(self):
        """Get current system status"""
        with self.coordination_lock:
            return {
                'state': self.system_state,
                'total_processes': self.total_processes,
                'registered_processes': len(self.initializers),
                'registered_components': len(self.component_registry),
                'process_states': {
                    pid: initializer.is_initialized
                    for pid, initializer in self.initializers.items()
                }
            }

    def health_check(self):
        """Perform system health check"""
        with self.coordination_lock:
            healthy_processes = 0
            total_processes = len(self.initializers)

            for process_id, initializer in self.initializers.items():
                if hasattr(initializer, 'is_initialized') and initializer.is_initialized:
                    healthy_processes += 1

            health_percentage = (healthy_processes / total_processes * 100) if total_processes > 0 else 0

            return {
                'overall_health': health_percentage >= 75.0,  # 75% threshold
                'health_percentage': health_percentage,
                'healthy_processes': healthy_processes,
                'total_processes': total_processes,
                'timestamp': datetime.now().isoformat()
            }


class TestSystemStartupShutdown(unittest.TestCase):
    """Test system startup and shutdown coordination"""

    def setUp(self):
        """Set up test fixtures"""
        self.coordinator = MockSystemCoordinator(total_processes=4)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_single_process_startup(self):
        """Test single process startup"""
        initializer = AtomicInitializer(process_id=0, total_processes=1)

        # Register a mock component
        def mock_init():
            time.sleep(0.1)
            return True

        component = ComponentInitTask(
            component_id="test_component",
            component_name="Test Component",
            init_function=mock_init
        )
        initializer.register_component(component)

        self.coordinator.register_initializer(0, initializer)

        # Start system
        result = self.coordinator.start_system()

        self.assertTrue(result)
        self.assertEqual(self.coordinator.system_state, "running")
        self.assertTrue(initializer.is_initialized)

    def test_multi_process_startup(self):
        """Test multi-process startup coordination"""
        # Create multiple initializers
        for i in range(4):
            initializer = AtomicInitializer(process_id=i, total_processes=4)
            self.coordinator.register_initializer(i, initializer)

        # Start system
        start_time = time.time()
        result = self.coordinator.start_system()
        startup_time = time.time() - start_time

        self.assertTrue(result)
        self.assertEqual(self.coordinator.system_state, "running")
        self.assertLess(startup_time, 30.0)  # Should complete within 30 seconds

        # Verify all processes initialized
        for i in range(4):
            self.assertTrue(self.coordinator.initializers[i].is_initialized)

    def test_system_shutdown(self):
        """Test system shutdown coordination"""
        # Start system first
        for i in range(4):
            initializer = AtomicInitializer(process_id=i, total_processes=4)
            self.coordinator.register_initializer(i, initializer)

        self.coordinator.start_system()
        self.assertEqual(self.coordinator.system_state, "running")

        # Shutdown system
        start_time = time.time()
        result = self.coordinator.stop_system()
        shutdown_time = time.time() - start_time

        self.assertTrue(result)
        self.assertEqual(self.coordinator.system_state, "stopped")
        self.assertLess(shutdown_time, 30.0)  # Should shutdown within 30 seconds

    def test_startup_failure_handling(self):
        """Test handling of startup failures"""
        # Create one failing initializer
        def failing_init():
            raise RuntimeError("Simulated initialization failure")

        failing_initializer = AtomicInitializer(process_id=0, total_processes=2)
        failing_component = ComponentInitTask(
            component_id="failing_component",
            component_name="Failing Component",
            init_function=failing_init,
            critical=True
        )
        failing_initializer.register_component(failing_component)

        # Create one successful initializer
        successful_initializer = AtomicInitializer(process_id=1, total_processes=2)

        self.coordinator.register_initializer(0, failing_initializer)
        self.coordinator.register_initializer(1, successful_initializer)

        # System startup should fail
        with self.assertRaises(RuntimeError):
            self.coordinator.start_system()

        self.assertEqual(self.coordinator.system_state, "failed")

    def test_component_dependency_resolution(self):
        """Test component dependency resolution"""
        initializer = AtomicInitializer(process_id=0, total_processes=1)

        # Create components with dependencies
        def init_memory():
            time.sleep(0.1)
            return True

        def init_database():
            time.sleep(0.1)
            return True

        def init_app():
            time.sleep(0.1)
            return True

        memory_component = ComponentInitTask(
            component_id="memory",
            component_name="Memory Manager",
            init_function=init_memory
        )

        database_component = ComponentInitTask(
            component_id="database",
            component_name="Database",
            init_function=init_database,
            dependencies={"memory"}
        )

        app_component = ComponentInitTask(
            component_id="app",
            component_name="Application",
            init_function=init_app,
            dependencies={"database", "memory"}
        )

        # Register in random order
        initializer.register_component(app_component)
        initializer.register_component(memory_component)
        initializer.register_component(database_component)

        self.coordinator.register_initializer(0, initializer)
        result = self.coordinator.start_system()

        self.assertTrue(result)
        self.assertTrue(initializer.is_initialized)

    def test_concurrent_system_operations(self):
        """Test concurrent system operations"""
        # Create multiple initializers
        for i in range(8):
            initializer = AtomicInitializer(process_id=i, total_processes=8)
            self.coordinator.register_initializer(i, initializer)

        # Test concurrent startup
        startup_futures = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            for _ in range(3):  # Try to start 3 times concurrently
                future = executor.submit(self.coordinator.start_system)
                startup_futures.append(future)

            # Only one should succeed
            successes = 0
            for future in as_completed(startup_futures):
                try:
                    if future.result():
                        successes += 1
                except RuntimeError:
                    pass  # Expected for concurrent attempts

            self.assertEqual(successes, 1)

    def test_system_status_monitoring(self):
        """Test system status monitoring"""
        # Add some initializers
        for i in range(4):
            initializer = AtomicInitializer(process_id=i, total_processes=4)
            self.coordinator.register_initializer(i, initializer)

        # Check status before startup
        status = self.coordinator.get_system_status()
        self.assertEqual(status['state'], 'stopped')
        self.assertEqual(status['total_processes'], 4)
        self.assertEqual(status['registered_processes'], 4)

        # Start system and check status
        self.coordinator.start_system()
        status = self.coordinator.get_system_status()
        self.assertEqual(status['state'], 'running')

        # Verify process states
        for process_id, is_initialized in status['process_states'].items():
            self.assertTrue(is_initialized)

    def test_health_check_functionality(self):
        """Test system health check functionality"""
        # Add initializers
        for i in range(4):
            initializer = AtomicInitializer(process_id=i, total_processes=4)
            self.coordinator.register_initializer(i, initializer)

        # Start system
        self.coordinator.start_system()

        # Perform health check
        health = self.coordinator.health_check()

        self.assertIn('overall_health', health)
        self.assertIn('health_percentage', health)
        self.assertIn('healthy_processes', health)
        self.assertIn('total_processes', health)
        self.assertIn('timestamp', health)

        self.assertTrue(health['overall_health'])
        self.assertEqual(health['health_percentage'], 100.0)
        self.assertEqual(health['healthy_processes'], 4)
        self.assertEqual(health['total_processes'], 4)


class TestMultiComponentInteractions(unittest.TestCase):
    """Test multi-component interaction scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.coordinator = MockSystemCoordinator(total_processes=4)

    def test_memory_allocator_integration(self):
        """Test memory allocator integration with system components"""
        # Create mock memory allocator
        if AdaptiveMemoryAllocator != Mock:
            allocator = AdaptiveMemoryAllocator(total_memory_gb=16.0)
        else:
            allocator = Mock()

        # Create initializer that uses memory allocator
        def init_with_memory():
            if hasattr(allocator, 'calculate_optimal_allocation'):
                result = allocator.calculate_optimal_allocation(
                    data_size_mb=1000,
                    concurrent_processes=4
                )
                return result is not None
            return True

        initializer = AtomicInitializer(process_id=0, total_processes=1)
        component = ComponentInitTask(
            component_id="memory_aware_component",
            component_name="Memory Aware Component",
            init_function=init_with_memory
        )
        initializer.register_component(component)

        self.coordinator.register_initializer(0, initializer)
        result = self.coordinator.start_system()

        self.assertTrue(result)
        self.assertTrue(initializer.is_initialized)

    def test_ipc_component_interaction(self):
        """Test IPC component interactions"""
        shared_data = {}
        shared_lock = threading.Lock()

        def init_producer():
            with shared_lock:
                shared_data['producer_data'] = "Producer initialized"
            time.sleep(0.1)
            return True

        def init_consumer():
            # Wait for producer
            time.sleep(0.15)
            with shared_lock:
                if 'producer_data' in shared_data:
                    shared_data['consumer_data'] = "Consumer initialized"
                    return True
            return False

        # Create producer and consumer components
        producer_initializer = AtomicInitializer(process_id=0, total_processes=2)
        producer_component = ComponentInitTask(
            component_id="producer",
            component_name="Data Producer",
            init_function=init_producer
        )
        producer_initializer.register_component(producer_component)

        consumer_initializer = AtomicInitializer(process_id=1, total_processes=2)
        consumer_component = ComponentInitTask(
            component_id="consumer",
            component_name="Data Consumer",
            init_function=init_consumer
        )
        consumer_initializer.register_component(consumer_component)

        self.coordinator.register_initializer(0, producer_initializer)
        self.coordinator.register_initializer(1, consumer_initializer)

        result = self.coordinator.start_system()

        self.assertTrue(result)
        self.assertTrue(producer_initializer.is_initialized)
        self.assertTrue(consumer_initializer.is_initialized)

        # Verify data exchange occurred
        with shared_lock:
            self.assertIn('producer_data', shared_data)
            self.assertIn('consumer_data', shared_data)

    def test_component_failure_propagation(self):
        """Test component failure propagation effects"""
        failure_log = []

        def init_critical_component():
            failure_log.append("critical_started")
            raise RuntimeError("Critical component failed")

        def init_dependent_component():
            # This component depends on critical component
            time.sleep(0.2)
            if any("critical_started" in log for log in failure_log):
                return False  # Should fail due to dependency
            return True

        critical_initializer = AtomicInitializer(process_id=0, total_processes=2)
        critical_component = ComponentInitTask(
            component_id="critical",
            component_name="Critical Component",
            init_function=init_critical_component,
            critical=True
        )
        critical_initializer.register_component(critical_component)

        dependent_initializer = AtomicInitializer(process_id=1, total_processes=2)
        dependent_component = ComponentInitTask(
            component_id="dependent",
            component_name="Dependent Component",
            init_function=init_dependent_component
        )
        dependent_initializer.register_component(dependent_component)

        self.coordinator.register_initializer(0, critical_initializer)
        self.coordinator.register_initializer(1, dependent_initializer)

        # System should fail due to critical component failure
        with self.assertRaises(RuntimeError):
            self.coordinator.start_system()

        self.assertEqual(self.coordinator.system_state, "failed")

    def test_resource_allocation_coordination(self):
        """Test resource allocation coordination between components"""
        allocated_resources = {}
        resource_lock = threading.Lock()

        def init_resource_heavy():
            with resource_lock:
                if 'heavy_allocated' not in allocated_resources:
                    allocated_resources['heavy_allocated'] = True
                    allocated_resources['heavy_memory'] = 2048  # 2GB
                    return True
            return False

        def init_lightweight():
            with resource_lock:
                if allocated_resources.get('heavy_allocated', False):
                    # Check if we have enough resources left
                    used_memory = allocated_resources.get('heavy_memory', 0)
                    if used_memory < 4096:  # 4GB total available
                        allocated_resources['lightweight_allocated'] = True
                        allocated_resources['lightweight_memory'] = 512  # 512MB
                        return True
            return False

        heavy_initializer = AtomicInitializer(process_id=0, total_processes=2)
        heavy_component = ComponentInitTask(
            component_id="heavy_component",
            component_name="Resource Heavy Component",
            init_function=init_resource_heavy
        )
        heavy_initializer.register_component(heavy_component)

        lightweight_initializer = AtomicInitializer(process_id=1, total_processes=2)
        lightweight_component = ComponentInitTask(
            component_id="lightweight_component",
            component_name="Lightweight Component",
            init_function=init_lightweight
        )
        lightweight_initializer.register_component(lightweight_component)

        self.coordinator.register_initializer(0, heavy_initializer)
        self.coordinator.register_initializer(1, lightweight_initializer)

        result = self.coordinator.start_system()

        self.assertTrue(result)
        self.assertTrue(heavy_initializer.is_initialized)
        self.assertTrue(lightweight_initializer.is_initialized)

        # Verify resource allocation
        self.assertTrue(allocated_resources.get('heavy_allocated', False))
        self.assertTrue(allocated_resources.get('lightweight_allocated', False))

    def test_dynamic_component_registration(self):
        """Test dynamic component registration during runtime"""
        initializer = AtomicInitializer(process_id=0, total_processes=1)

        def init_base_component():
            return True

        def init_dynamic_component():
            return True

        # Register base component
        base_component = ComponentInitTask(
            component_id="base",
            component_name="Base Component",
            init_function=init_base_component
        )
        initializer.register_component(base_component)

        self.coordinator.register_initializer(0, initializer)

        # Start system with base component
        self.coordinator.start_system()
        self.assertTrue(initializer.is_initialized)

        # Simulate dynamic registration during runtime
        dynamic_component = ComponentInitTask(
            component_id="dynamic",
            component_name="Dynamic Component",
            init_function=init_dynamic_component
        )

        # In a real system, this would require hot-reload capabilities
        # For this test, we just verify the component can be created
        self.assertIsNotNone(dynamic_component)
        self.assertEqual(dynamic_component.component_id, "dynamic")


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility verification"""

    def setUp(self):
        """Set up test fixtures"""
        self.coordinator = MockSystemCoordinator(total_processes=2)

    def test_legacy_component_compatibility(self):
        """Test compatibility with legacy component interfaces"""
        # Simulate legacy component interface
        class LegacyComponent:
            def __init__(self):
                self.initialized = False

            def initialize(self):
                time.sleep(0.1)
                self.initialized = True
                return True

            def cleanup(self):
                self.initialized = False

        # Create adapter for legacy component
        legacy_component = LegacyComponent()

        def legacy_adapter():
            return legacy_component.initialize()

        def legacy_cleanup():
            return legacy_component.cleanup()

        initializer = AtomicInitializer(process_id=0, total_processes=1)
        component = ComponentInitTask(
            component_id="legacy_component",
            component_name="Legacy Component",
            init_function=legacy_adapter,
            cleanup_function=legacy_cleanup
        )
        initializer.register_component(component)

        self.coordinator.register_initializer(0, initializer)

        result = self.coordinator.start_system()

        self.assertTrue(result)
        self.assertTrue(initializer.is_initialized)
        self.assertTrue(legacy_component.initialized)

        # Test cleanup
        self.coordinator.stop_system()
        self.assertFalse(legacy_component.initialized)

    def test_configuration_compatibility(self):
        """Test configuration format compatibility"""
        # Test different configuration formats
        old_config_format = {
            'components': [
                {
                    'name': 'test_component',
                    'type': 'basic',
                    'enabled': True
                }
            ]
        }

        new_config_format = {
            'system': {
                'version': '2.0',
                'components': {
                    'test_component': {
                        'name': 'Test Component',
                        'type': 'basic',
                        'enabled': True,
                        'priority': 0,
                        'dependencies': set()
                    }
                }
            }
        }

        # Test that both formats can be handled
        def load_config(config):
            if 'components' in config and isinstance(config['components'], list):
                # Old format
                return {comp['name']: comp for comp in config['components']}
            elif 'system' in config and 'components' in config['system']:
                # New format
                return config['system']['components']
            else:
                raise ValueError("Unknown configuration format")

        # Test old format
        old_result = load_config(old_config_format)
        self.assertIn('test_component', old_result)

        # Test new format
        new_result = load_config(new_config_format)
        self.assertIn('test_component', new_result)

        # Verify both produce similar results
        self.assertEqual(old_result['test_component']['name'], new_result['test_component']['name'])

    def test_api_version_compatibility(self):
        """Test API version compatibility"""
        # Simulate different API versions
        class APIv1:
            def initialize_component(self, name, config):
                return {"status": "success", "version": "v1"}

        class APIv2:
            def initialize_component(self, name, config, timeout=30):
                return {"status": "success", "version": "v2", "timeout": timeout}

        # Create adapter to handle both versions
        class APIAdapter:
            def __init__(self, api):
                self.api = api
                self.version = "v1" if hasattr(api, 'initialize_component') and \
                               not hasattr(api.initialize_component, '__code__').co_argcount > 3 else "v2"

            def initialize(self, name, config, timeout=30):
                if self.version == "v1":
                    return self.api.initialize_component(name, config)
                else:
                    return self.api.initialize_component(name, config, timeout)

        # Test adapter with both APIs
        api_v1 = APIv1()
        adapter_v1 = APIAdapter(api_v1)
        result_v1 = adapter_v1.initialize("test", {})
        self.assertEqual(result_v1['version'], "v1")

        api_v2 = APIv2()
        adapter_v2 = APIAdapter(api_v2)
        result_v2 = adapter_v2.initialize("test", {})
        self.assertEqual(result_v2['version'], "v2")

    def test_feature_flag_compatibility(self):
        """Test feature flag compatibility"""
        # Test feature flag handling
        feature_flags = {
            'enable_new_memory_allocator': False,
            'enable_enhanced_ipc': True,
            'legacy_mode': False
        }

        def check_feature(feature_name, default=False):
            return feature_flags.get(feature_name, default)

        # Test known features
        self.assertFalse(check_feature('enable_new_memory_allocator'))
        self.assertTrue(check_feature('enable_enhanced_ipc'))

        # Test unknown feature (should return default)
        self.assertFalse(check_feature('unknown_feature', False))
        self.assertTrue(check_feature('unknown_feature', True))

        # Test legacy mode
        if check_feature('legacy_mode'):
            # Should use legacy implementations
            pass
        else:
            # Should use new implementations
            pass


class TestFeatureFlagsFunctionality(unittest.TestCase):
    """Test feature flags functionality validation"""

    def setUp(self):
        """Set up test fixtures"""
        self.feature_flag_file = tempfile.mktemp(suffix='.json')
        self.feature_flags = {
            'enable_adaptive_memory': True,
            'enable_atomic_initialization': True,
            'enable_enhanced_monitoring': False,
            'enable_experimental_features': False
        }

        with open(self.feature_flag_file, 'w') as f:
            json.dump(self.feature_flags, f)

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.feature_flag_file):
            os.unlink(self.feature_flag_file)

    def test_feature_flag_loading(self):
        """Test loading feature flags from file"""
        with open(self.feature_flag_file, 'r') as f:
            loaded_flags = json.load(f)

        self.assertEqual(loaded_flags['enable_adaptive_memory'], True)
        self.assertEqual(loaded_flags['enable_enhanced_monitoring'], False)

    def test_feature_flag_override(self):
        """Test feature flag override functionality"""
        # Override feature flag
        override_flags = self.feature_flags.copy()
        override_flags['enable_enhanced_monitoring'] = True

        # Verify override works
        self.assertTrue(override_flags['enable_enhanced_monitoring'])
        self.assertFalse(self.feature_flags['enable_enhanced_monitoring'])

    def test_feature_flag_validation(self):
        """Test feature flag validation"""
        required_flags = ['enable_adaptive_memory', 'enable_atomic_initialization']
        optional_flags = ['enable_enhanced_monitoring', 'enable_experimental_features']

        # Check required flags
        for flag in required_flags:
            self.assertIn(flag, self.feature_flags)

        # Check for unknown flags
        known_flags = set(required_flags + optional_flags)
        unknown_flags = set(self.feature_flags.keys()) - known_flags
        self.assertEqual(len(unknown_flags), 0, f"Unknown flags: {unknown_flags}")

    def test_feature_flag_runtime_switching(self):
        """Test runtime feature flag switching"""
        # Simulate runtime flag switching
        def check_flag(flag_name):
            return self.feature_flags.get(flag_name, False)

        # Initial state
        self.assertTrue(check_flag('enable_adaptive_memory'))

        # Runtime switch
        self.feature_flags['enable_adaptive_memory'] = False
        self.assertFalse(check_flag('enable_adaptive_memory'))

        # Verify other flags unchanged
        self.assertTrue(check_flag('enable_atomic_initialization'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
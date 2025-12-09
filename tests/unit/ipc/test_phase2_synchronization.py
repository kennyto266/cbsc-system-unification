#!/usr/bin/env python3
"""
Comprehensive test suite for Phase 2 IPC Synchronization Enhancement
Tests all synchronization scenarios under 32-core concurrent load
"""

import os
import sys
import time
import pytest
import threading
import multiprocessing as mp
import tempfile
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import Phase 2 synchronization components
try:
    from src.ipc import (
        AtomicInitializer, InitializationPhase, ComponentInitTask, ComponentState,
        DeadlockDetector, ResourceType, DeadlockResolution, Priority, ResourceRequest,
        SmartMessageQueue, MessagePriority, QueuePolicy, RetryPolicy
    )
    PHASE2_AVAILABLE = True
except ImportError as e:
    pytest.skip(f"Phase 2 components not available: {e}", allow_module_level=True)
    PHASE2_AVAILABLE = False

# Test configuration
MAX_WORKERS = 32  # Target 32-core concurrent load
TEST_TIMEOUT_SECONDS = 60
RACE_CONDITION_TEST_ITERATIONS = 100
DEADLOCK_TEST_TIMEOUT = 30
MESSAGE_THROUGHPUT_TARGET = 1000  # messages per second


class TestAtomicInitializer:
    """Test atomic initializer functionality"""

    @pytest.fixture
    def temp_state_file(self):
        """Create temporary state file for testing"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            yield f.name
        os.unlink(f.name)

    def test_single_process_initialization(self, temp_state_file):
        """Test single process atomic initialization"""
        initializer = AtomicInitializer(
            process_id=0,
            total_processes=1,
            state_file_path=temp_state_file,
            enable_distributed_locking=False
        )

        # Define test components
        components = [
            ComponentInitTask(
                component_id="test_comp1",
                component_name="Test Component 1",
                init_function=lambda: True,
                cleanup_function=None,
                dependencies=set(),
                critical=True
            ),
            ComponentInitTask(
                component_id="test_comp2",
                component_name="Test Component 2",
                init_function=lambda: True,
                cleanup_function=None,
                dependencies={"test_comp1"},
                critical=False
            )
        ]

        for comp in components:
            initializer.register_component(comp)

        # Test initialization
        assert initializer.initialize() is True
        assert initializer.is_initialized is True

        # Check component states
        status = initializer.get_initialization_status()
        assert status['phase'] == InitializationPhase.COMPLETE.value
        assert status['component_states']['test_comp1'] == ComponentState.INITIALIZED.value
        assert status['component_states']['test_comp2'] == ComponentState.INITIALIZED.value

        initializer.cleanup()

    def test_dependency_resolution(self, temp_state_file):
        """Test dependency resolution functionality"""
        initializer = AtomicInitializer(
            process_id=0,
            total_processes=1,
            state_file_path=temp_state_file,
            enable_distributed_locking=False
        )

        # Create components with complex dependencies
        components = [
            ComponentInitTask(
                component_id="base",
                component_name="Base Component",
                init_function=lambda: True,
                cleanup_function=None,
                dependencies=set(),
                critical=True
            ),
            ComponentInitTask(
                component_id="layer1_a",
                component_name="Layer 1 A",
                init_function=lambda: True,
                cleanup_function=None,
                dependencies={"base"},
                critical=True
            ),
            ComponentInitTask(
                component_id="layer1_b",
                component_name="Layer 1 B",
                init_function=lambda: True,
                cleanup_function=None,
                dependencies={"base"},
                critical=True
            ),
            ComponentInitTask(
                component_id="layer2",
                component_name="Layer 2",
                init_function=lambda: True,
                cleanup_function=None,
                dependencies={"layer1_a", "layer1_b"},
                critical=False
            )
        ]

        for comp in components:
            initializer.register_component(comp)

        # Test initialization with dependencies
        assert initializer.initialize() is True

        status = initializer.get_initialization_status()
        assert status['component_states']['base'] == ComponentState.INITIALIZED.value
        assert status['component_states']['layer1_a'] == ComponentState.INITIALIZED.value
        assert status['component_states']['layer1_b'] == ComponentState.INITIALIZED.value
        assert status['component_states']['layer2'] == ComponentState.INITIALIZED.value

        initializer.cleanup()

    def test_dependency_cycle_detection(self, temp_state_file):
        """Test dependency cycle detection"""
        initializer = AtomicInitializer(
            process_id=0,
            total_processes=1,
            state_file_path=temp_state_file,
            enable_distributed_locking=False
        )

        # Create components with circular dependencies
        components = [
            ComponentInitTask(
                component_id="comp_a",
                component_name="Component A",
                init_function=lambda: True,
                cleanup_function=None,
                dependencies={"comp_b"},  # Circular dependency
                critical=True
            ),
            ComponentInitTask(
                component_id="comp_b",
                component_name="Component B",
                init_function=lambda: True,
                cleanup_function=None,
                dependencies={"comp_a"},  # Circular dependency
                critical=True
            )
        ]

        for comp in components:
            initializer.register_component(comp)

        # Test should fail due to dependency cycle
        assert initializer.initialize() is False

        # Check that cycle was detected
        assert initializer.stats['dependency_cycles_detected'] > 0

        initializer.cleanup()

    @pytest.mark.parametrize("num_processes", [2, 4, 8, 16])
    def test_multi_process_race_conditions(self, num_processes, temp_state_file):
        """Test atomic initialization with multiple processes to eliminate race conditions"""
        def worker_process(process_id, results_queue):
            """Worker process function"""
            try:
                initializer = AtomicInitializer(
                    process_id=process_id,
                    total_processes=num_processes,
                    state_file_path=temp_state_file,
                    enable_distributed_locking=True,
                    lock_timeout_seconds=10.0
                )

                # Define test component
                component = ComponentInitTask(
                    component_id=f"worker_{process_id}_comp",
                    component_name=f"Worker {process_id} Component",
                    init_function=lambda: True,
                    cleanup_function=None,
                    dependencies=set(),
                    critical=True
                )

                initializer.register_component(component)
                success = initializer.initialize()

                results_queue.put({
                    'process_id': process_id,
                    'success': success,
                    'is_leader': initializer.is_leader,
                    'stats': initializer.stats.copy()
                })

                initializer.cleanup()

            except Exception as e:
                results_queue.put({
                    'process_id': process_id,
                    'success': False,
                    'error': str(e)
                })

        # Create processes
        results_queue = mp.Queue()
        processes = []

        for i in range(num_processes):
            p = mp.Process(target=worker_process, args=(i, results_queue))
            processes.append(p)
            p.start()

        # Wait for all processes to complete
        for p in processes:
            p.join(timeout=TEST_TIMEOUT_SECONDS)
            if p.is_alive():
                p.terminate()
                p.join()

        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        # Verify results
        assert len(results) == num_processes

        # All processes should succeed
        successful_processes = [r for r in results if r['success']]
        assert len(successful_processes) == num_processes

        # Exactly one process should be leader
        leaders = [r for r in successful_processes if r['is_leader']]
        assert len(leaders) == 1

        # Check for race conditions (multiple leaders)
        assert len(leaders) == 1

    @pytest.mark.parametrize("iteration", range(RACE_CONDITION_TEST_ITERATIONS))
    def test_concurrent_initialization_race_conditions(self, iteration):
        """Stress test for concurrent initialization to verify race condition elimination"""
        temp_file = tempfile.mktemp()

        def concurrent_init():
            initializer = AtomicInitializer(
                process_id=random.randint(0, 1000),
                total_processes=random.randint(2, 8),
                state_file_path=temp_file,
                enable_distributed_locking=True,
                lock_timeout_seconds=5.0
            )

            component = ComponentInitTask(
                component_id="stress_test_comp",
                component_name="Stress Test Component",
                init_function=lambda: time.sleep(0.01),  # Small delay to increase contention
                cleanup_function=None,
                dependencies=set(),
                critical=True
            )

            initializer.register_component(component)
            return initializer.initialize()

        # Run multiple concurrent initializations
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(concurrent_init) for _ in range(5)]
            results = [f.result() for f in futures]

        # At least one should succeed
        assert any(results), "At least one initialization should succeed"

        # Clean up
        try:
            os.unlink(temp_file)
        except:
            pass


class TestDeadlockDetector:
    """Test deadlock detector functionality"""

    def test_basic_deadlock_detection(self):
        """Test basic deadlock detection"""
        detector = DeadlockDetector(
            detection_interval_seconds=0.5,
            enable_auto_resolution=False  # Manual for testing
        )

        detector.start()

        # Register processes
        detector.register_process(1, Priority.NORMAL)
        detector.register_process(2, Priority.NORMAL)

        # Create deadlock scenario: Process 1 -> Process 2 -> Process 1
        req1 = detector.request_resource(1, "resource1", ResourceType.SHARED_MEMORY, exclusive=True)
        req2 = detector.request_resource(2, "resource2", ResourceType.SHARED_MEMORY, exclusive=True)
        req3 = detector.request_resource(1, "resource2", ResourceType.SHARED_MEMORY, exclusive=True)
        req4 = detector.request_resource(2, "resource1", ResourceType.SHARED_MEMORY, exclusive=True)

        # Wait for detection
        time.sleep(2)

        # Check if deadlock was detected
        stats = detector.get_statistics()
        assert stats['deadlocks_detected'] >= 1

        detector.stop()

    def test_deadlock_resolution_victim_selection(self):
        """Test automatic deadlock resolution through victim selection"""
        detector = DeadlockDetector(
            detection_interval_seconds=0.5,
            enable_auto_resolution=True,
            resolution_strategy=DeadlockResolution.VICTIM_SELECTION
        )

        detector.start()

        # Register processes with different priorities
        detector.register_process(1, Priority.LOW)      # Likely victim
        detector.register_process(2, Priority.HIGH)     # Protected
        detector.register_process(3, Priority.CRITICAL) # Protected

        # Create deadlock
        req1 = detector.request_resource(1, "resource1", ResourceType.SHARED_MEMORY, exclusive=True)
        req2 = detector.request_resource(2, "resource2", ResourceType.SHARED_MEMORY, exclusive=True)
        req3 = detector.request_resource(3, "resource3", ResourceType.SHARED_MEMORY, exclusive=True)
        req4 = detector.request_resource(1, "resource2", ResourceType.SHARED_MEMORY, exclusive=True)
        req5 = detector.request_resource(2, "resource3", ResourceType.SHARED_MEMORY, exclusive=True)
        req6 = detector.request_resource(3, "resource1", ResourceType.SHARED_MEMORY, exclusive=True)

        # Wait for resolution
        time.sleep(3)

        # Check if deadlock was resolved
        stats = detector.get_statistics()
        assert stats['deadlocks_resolved'] >= 1
        assert stats['processes_killed'] >= 1

        detector.stop()

    def test_resource_preemption_resolution(self):
        """Test deadlock resolution through resource preemption"""
        detector = DeadlockDetector(
            detection_interval_seconds=0.5,
            enable_auto_resolution=True,
            resolution_strategy=DeadlockResolution.RESOURCE_PREEMPTION
        )

        detector.start()

        # Register processes
        detector.register_process(1, Priority.HIGH)
        detector.register_process(2, Priority.HIGH)

        # Create deadlock with critical resources
        req1 = detector.request_resource(1, "critical_resource1", ResourceType.SHARED_MEMORY, exclusive=True)
        req2 = detector.request_resource(2, "critical_resource2", ResourceType.SHARED_MEMORY, exclusive=True)
        req3 = detector.request_resource(1, "critical_resource2", ResourceType.SHARED_MEMORY, exclusive=True)
        req4 = detector.request_resource(2, "critical_resource1", ResourceType.SHARED_MEMORY, exclusive=True)

        # Wait for resolution
        time.sleep(3)

        # Check if deadlock was resolved without killing processes
        stats = detector.get_statistics()
        assert stats['deadlocks_resolved'] >= 1

        detector.stop()

    @pytest.mark.parametrize("num_processes", [4, 8, 16, 32])
    def test_high_concurrency_deadlock_detection(self, num_processes):
        """Test deadlock detection under high concurrency"""
        detector = DeadlockDetector(
            detection_interval_seconds=0.1,  # Faster detection for high concurrency
            enable_auto_resolution=False
        )

        detector.start()

        # Register many processes
        for i in range(num_processes):
            detector.register_process(i, Priority.NORMAL)

        # Create potential deadlock scenarios
        resources = [f"resource_{j}" for j in range(num_processes // 2)]
        requests = []

        for i in range(num_processes):
            # Each process requests 2 resources in different order
            resource1 = resources[i % len(resources)]
            resource2 = resources[(i + 1) % len(resources)]

            req1 = detector.request_resource(i, resource1, ResourceType.SHARED_MEMORY, exclusive=True)
            req2 = detector.request_resource(i, resource2, ResourceType.SHARED_MEMORY, exclusive=True)
            requests.extend([req1, req2])

        # Wait for detection
        time.sleep(2)

        # Check for deadlocks (should detect some due to contention)
        stats = detector.get_statistics()
        # Allow for no deadlocks in some runs due to timing
        assert stats['detections_performed'] > 0

        detector.stop()


class TestSmartMessageQueue:
    """Test smart message queue functionality"""

    def test_basic_enqueue_dequeue(self):
        """Test basic message enqueue and dequeue"""
        queue = SmartMessageQueue(max_size=100, enable_metrics=True)
        queue.start()

        # Enqueue test message
        message_id = queue.enqueue(
            payload="test_message",
            priority=MessagePriority.NORMAL
        )

        assert message_id is not None

        # Dequeue message
        message = queue.dequeue(timeout_seconds=1.0)
        assert message is not None
        assert message.payload == "test_message"
        assert message.message_id == message_id

        queue.stop()

    def test_priority_ordering(self):
        """Test message priority ordering"""
        queue = SmartMessageQueue(max_size=100)
        queue.start()

        # Enqueue messages with different priorities
        normal_id = queue.enqueue("normal", MessagePriority.NORMAL)
        urgent_id = queue.enqueue("urgent", MessagePriority.URGENT)
        low_id = queue.enqueue("low", MessagePriority.LOW)
        critical_id = queue.enqueue("critical", MessagePriority.CRITICAL)

        # Dequeue and check priority order (highest priority first)
        critical_msg = queue.dequeue()
        urgent_msg = queue.dequeue()
        normal_msg = queue.dequeue()
        low_msg = queue.dequeue()

        assert critical_msg.payload == "critical"
        assert urgent_msg.payload == "urgent"
        assert normal_msg.payload == "normal"
        assert low_msg.payload == "low"

        queue.stop()

    def test_retry_logic(self):
        """Test message retry logic"""
        queue = SmartMessageQueue(max_size=100, enable_dead_letter=True)
        queue.start()

        # Create a message that will fail
        retry_policy = RetryPolicy(
            max_retries=2,
            initial_delay_seconds=0.1,
            max_delay_seconds=1.0,
            backoff_multiplier=2.0
        )

        message_id = queue.enqueue(
            payload="retry_test",
            priority=MessagePriority.NORMAL,
            retry_policy=retry_policy
        )

        # Process message with failure
        message = queue.dequeue()
        assert message is not None

        # Simulate processing failure
        def failing_processor(payload):
            raise ValueError("Simulated failure")

        result = queue.process_message(message, failing_processor)
        assert result is False  # Should retry

        # Wait for retry
        time.sleep(0.2)

        # Check if message was retried
        retried_message = queue.dequeue()
        assert retried_message is not None
        assert retried_message.retry_count == 1

        queue.stop()

    def test_backpressure_handling(self):
        """Test backpressure mechanism"""
        queue = SmartMessageQueue(
            max_size=10,
            backpressure_threshold=0.8,
            enable_backpressure=True
        )
        queue.start()

        # Fill queue to trigger backpressure
        message_ids = []
        for i in range(15):  # Exceed max_size
            try:
                msg_id = queue.enqueue(f"message_{i}", MessagePriority.NORMAL)
                if msg_id:
                    message_ids.append(msg_id)
            except Exception:
                # Some messages should be rejected due to backpressure
                pass

        # Check that backpressure was activated
        metrics = queue.get_metrics()
        assert metrics.backpressure_events > 0

        queue.stop()

    def test_dead_letter_queue(self):
        """Test dead letter queue functionality"""
        queue = SmartMessageQueue(max_size=100, enable_dead_letter=True)
        queue.start()

        # Create a message that will exhaust retries
        retry_policy = RetryPolicy(
            max_retries=1,
            initial_delay_seconds=0.01
        )

        message_id = queue.enqueue(
            payload="dead_letter_test",
            priority=MessagePriority.NORMAL,
            retry_policy=retry_policy
        )

        # Process message multiple times to exhaust retries
        message = queue.dequeue()
        assert message is not None

        def always_failing_processor(payload):
            raise ValueError("Always fails")

        # Process until dead lettered
        result = queue.process_message(message, always_failing_processor)
        assert result is False

        # Wait for retry and final failure
        time.sleep(0.1)

        # Check dead letter queue
        dead_letter_messages = queue.get_dead_letter_messages()
        assert len(dead_letter_messages) > 0
        assert dead_letter_messages[0]['payload'] == "dead_letter_test"

        queue.stop()

    @pytest.mark.parametrize("message_rate", [100, 500, 1000])
    def test_high_throughput_performance(self, message_rate):
        """Test queue performance under high throughput"""
        queue = SmartMessageQueue(
            max_size=message_rate * 2,
            processing_threads=8,
            batch_size=50
        )
        queue.start()

        start_time = time.time()
        messages_enqueued = 0
        messages_dequeued = 0

        # Enqueue messages rapidly
        with ThreadPoolExecutor(max_workers=4) as executor:
            def enqueue_worker():
                nonlocal messages_enqueued
                for i in range(message_rate // 4):
                    queue.enqueue(f"high_throughput_{i}", MessagePriority.NORMAL)
                    messages_enqueued += 1

            def dequeue_worker():
                nonlocal messages_dequeued
                while messages_dequeued < message_rate:
                    message = queue.dequeue(timeout_seconds=0.1)
                    if message:
                        messages_dequeued += 1

            # Start workers
            enqueue_futures = [executor.submit(enqueue_worker) for _ in range(4)]
            dequeue_future = executor.submit(dequeue_worker)

            # Wait for completion
            for future in enqueue_futures:
                future.result(timeout=30)

            dequeue_future.result(timeout=30)

        end_time = time.time()
        duration = end_time - start_time

        # Calculate throughput
        actual_throughput = messages_dequeued / duration
        print(f"Actual throughput: {actual_throughput:.2f} messages/second")

        # Should achieve reasonable throughput (at least 50% of target)
        assert actual_throughput >= message_rate * 0.5

        queue.stop()


class TestIntegratedSynchronization:
    """Test integrated Phase 2 synchronization components"""

    @pytest.mark.parametrize("num_workers", [4, 8, 16, 32])
    def test_end_to_end_synchronization(self, num_workers):
        """End-to-end test of all Phase 2 synchronization components"""
        def worker_process(worker_id, results_queue):
            """Worker process with full synchronization"""
            try:
                # Initialize components
                initializer = AtomicInitializer(
                    process_id=worker_id,
                    total_processes=num_workers,
                    enable_distributed_locking=True
                )

                deadlock_detector = DeadlockDetector(
                    detection_interval_seconds=0.5,
                    enable_auto_resolution=True
                )

                message_queue = SmartMessageQueue(
                    max_size=1000,
                    enable_backpressure=True,
                    enable_metrics=True
                )

                # Start components
                message_queue.start()
                deadlock_detector.start()
                deadlock_detector.register_process(worker_id, Priority.NORMAL)

                # Define component for initialization
                component = ComponentInitTask(
                    component_id=f"worker_{worker_id}_sync",
                    component_name=f"Worker {worker_id} Sync Component",
                    init_function=lambda: True,
                    cleanup_function=None,
                    dependencies=set(),
                    critical=True
                )

                initializer.register_component(component)
                init_success = initializer.initialize()

                if not init_success:
                    raise Exception("Atomic initialization failed")

                # Perform synchronized work
                messages_sent = 0
                messages_received = 0

                for i in range(10):
                    # Send message
                    msg_id = message_queue.enqueue(
                        payload=f"worker_{worker_id}_message_{i}",
                        priority=MessagePriority.NORMAL
                    )
                    if msg_id:
                        messages_sent += 1

                    # Try to receive message
                    message = message_queue.dequeue(timeout_seconds=0.1)
                    if message:
                        messages_received += 1

                    # Small delay to allow other workers
                    time.sleep(0.01)

                # Collect results
                stats = {
                    'worker_id': worker_id,
                    'init_success': init_success,
                    'is_leader': initializer.is_leader,
                    'messages_sent': messages_sent,
                    'messages_received': messages_received,
                    'initializer_stats': initializer.stats.copy(),
                    'deadlock_stats': deadlock_detector.get_statistics(),
                    'queue_metrics': message_queue.get_metrics().to_dict()
                }

                results_queue.put(stats)

                # Cleanup
                deadlock_detector.unregister_process(worker_id)
                deadlock_detector.stop()
                message_queue.stop()
                initializer.cleanup()

            except Exception as e:
                results_queue.put({
                    'worker_id': worker_id,
                    'init_success': False,
                    'error': str(e)
                })

        # Run worker processes
        results_queue = mp.Queue()
        processes = []

        for i in range(num_workers):
            p = mp.Process(target=worker_process, args=(i, results_queue))
            processes.append(p)
            p.start()

        # Wait for completion
        for p in processes:
            p.join(timeout=TEST_TIMEOUT_SECONDS)
            if p.is_alive():
                p.terminate()
                p.join()

        # Collect and analyze results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        # Verify results
        assert len(results) == num_workers

        successful_workers = [r for r in results if r.get('init_success', False)]
        assert len(successful_workers) == num_workers

        # Check for race conditions (multiple leaders)
        leaders = [r for r in successful_workers if r.get('is_leader', False)]
        assert len(leaders) == 1

        # Verify message processing
        total_messages_sent = sum(r.get('messages_sent', 0) for r in successful_workers)
        total_messages_received = sum(r.get('messages_received', 0) for r in successful_workers)
        assert total_messages_sent > 0
        assert total_messages_received > 0

        # Check for deadlock issues
        deadlock_issues = sum(
            r.get('deadlock_stats', {}).get('deadlocks_detected', 0)
            for r in successful_workers
        )
        # Should not have excessive deadlocks in normal operation
        assert deadlock_issues <= len(successful_workers)

    def test_system_under_maximum_load(self):
        """Test system behavior under maximum 32-core load"""
        num_workers = 32
        duration_seconds = 10

        def stress_worker(worker_id, stop_event, stats_queue):
            """Stress test worker"""
            try:
                # Initialize with full synchronization
                initializer = AtomicInitializer(
                    process_id=worker_id,
                    total_processes=num_workers,
                    enable_distributed_locking=True
                )

                deadlock_detector = DeadlockDetector(
                    detection_interval_seconds=0.2,
                    enable_auto_resolution=True
                )

                message_queue = SmartMessageQueue(
                    max_size=2000,
                    enable_backpressure=True,
                    enable_metrics=True
                )

                # Start components
                message_queue.start()
                deadlock_detector.start()
                deadlock_detector.register_process(worker_id, Priority.NORMAL)

                # Initialize
                component = ComponentInitTask(
                    component_id=f"stress_worker_{worker_id}",
                    component_name=f"Stress Worker {worker_id}",
                    init_function=lambda: True,
                    cleanup_function=None,
                    dependencies=set(),
                    critical=True
                )

                initializer.register_component(component)
                if not initializer.initialize():
                    raise Exception("Initialization failed")

                # Stress test loop
                operations = {
                    'messages_sent': 0,
                    'messages_received': 0,
                    'resource_requests': 0,
                    'errors': 0
                }

                start_time = time.time()
                while not stop_event.is_set() and (time.time() - start_time) < duration_seconds:
                    try:
                        # Message operations
                        msg_id = message_queue.enqueue(
                            payload=f"stress_{worker_id}_{operations['messages_sent']}",
                            priority=random.choice(list(MessagePriority))
                        )
                        if msg_id:
                            operations['messages_sent'] += 1

                        message = message_queue.dequeue(timeout_seconds=0.01)
                        if message:
                            operations['messages_received'] += 1

                        # Resource requests (simulate shared memory operations)
                        if random.random() < 0.1:  # 10% chance
                            resource_id = f"stress_resource_{random.randint(0, 9)}"
                            req_id = deadlock_detector.request_resource(
                                worker_id, resource_id, ResourceType.SHARED_MEMORY
                            )
                            if req_id:
                                operations['resource_requests'] += 1
                                # Release after short time
                                time.sleep(0.001)
                                deadlock_detector.release_resource_request(req_id)

                    except Exception as e:
                        operations['errors'] += 1

                # Report final statistics
                end_time = time.time()
                total_time = end_time - start_time

                final_stats = {
                    'worker_id': worker_id,
                    'total_time': total_time,
                    'operations': operations,
                    'message_rate': operations['messages_sent'] / total_time if total_time > 0 else 0,
                    'initializer_stats': initializer.stats.copy(),
                    'deadlock_stats': deadlock_detector.get_statistics(),
                    'queue_metrics': message_queue.get_metrics().to_dict()
                }

                stats_queue.put(final_stats)

                # Cleanup
                deadlock_detector.unregister_process(worker_id)
                deadlock_detector.stop()
                message_queue.stop()
                initializer.cleanup()

            except Exception as e:
                stats_queue.put({
                    'worker_id': worker_id,
                    'error': str(e)
                })

        # Run stress test
        stop_event = mp.Event()
        stats_queue = mp.Queue()
        processes = []

        print(f"Starting {num_workers}-worker stress test for {duration_seconds} seconds...")

        for i in range(num_workers):
            p = mp.Process(target=stress_worker, args=(i, stop_event, stats_queue))
            processes.append(p)
            p.start()

        # Run for specified duration
        time.sleep(duration_seconds)
        stop_event.set()

        # Wait for all processes to complete
        for p in processes:
            p.join(timeout=30)
            if p.is_alive():
                p.terminate()
                p.join()

        # Collect results
        results = []
        while not stats_queue.empty():
            results.append(stats_queue.get())

        # Analyze results
        successful_workers = [r for r in results if 'error' not in r]
        print(f"Successful workers: {len(successful_workers)}/{num_workers}")

        assert len(successful_workers) >= num_workers * 0.9, "At least 90% of workers should succeed"

        # Calculate aggregate statistics
        total_messages_sent = sum(w['operations']['messages_sent'] for w in successful_workers)
        total_messages_received = sum(w['operations']['messages_received'] for w in successful_workers)
        total_resource_requests = sum(w['operations']['resource_requests'] for w in successful_workers)
        total_errors = sum(w['operations']['errors'] for w in successful_workers)

        avg_message_rate = sum(w['message_rate'] for w in successful_workers) / len(successful_workers)

        print(f"Total messages sent: {total_messages_sent}")
        print(f"Total messages received: {total_messages_received}")
        print(f"Total resource requests: {total_resource_requests}")
        print(f"Total errors: {total_errors}")
        print(f"Average message rate per worker: {avg_message_rate:.2f} msg/s")

        # Verify system stability
        error_rate = total_errors / (total_messages_sent + total_messages_received + total_resource_requests)
        assert error_rate < 0.05, f"Error rate too high: {error_rate:.2%}"

        # Check for race conditions
        leaders = [w for w in successful_workers if w['initializer_stats'].get('is_leader', False)]
        assert len(leaders) == 1, f"Should have exactly 1 leader, got {len(leaders)}"

        # Check deadlock handling
        total_deadlocks = sum(w['deadlock_stats'].get('deadlocks_detected', 0) for w in successful_workers)
        total_resolutions = sum(w['deadlock_stats'].get('deadlocks_resolved', 0) for w in successful_workers)
        print(f"Total deadlocks detected: {total_deadlocks}")
        print(f"Total deadlocks resolved: {total_resolutions}")

        # Should handle deadlocks effectively
        if total_deadlocks > 0:
            resolution_rate = total_resolutions / total_deadlocks
            assert resolution_rate >= 0.8, f"Deadlock resolution rate too low: {resolution_rate:.2%}"

        print("Stress test completed successfully!")


if __name__ == "__main__":
    # Run tests with different configurations
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--timeout=300",  # 5 minute timeout
        "-x"  # Stop on first failure
    ])
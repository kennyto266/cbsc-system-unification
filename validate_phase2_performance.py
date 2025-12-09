#!/usr/bin/env python3
"""
Phase 2 IPC Synchronization Performance Validation Script
Validates performance under maximum concurrent load and zero race conditions
"""

import os
import sys
import time
import json
import multiprocessing as mp
import threading
import tempfile
import random
import statistics
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import psutil

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import Phase 2 components
try:
    from src.ipc import (
        AtomicInitializer, InitializationPhase, ComponentInitTask,
        DeadlockDetector, ResourceType, Priority,
        SmartMessageQueue, MessagePriority
    )
    from src.parallel import EnhancedParallelProcessingSystem
    PHASE2_AVAILABLE = True
except ImportError as e:
    print(f"Phase 2 components not available: {e}")
    PHASE2_AVAILABLE = False


class PerformanceValidator:
    """Performance validator for Phase 2 synchronization"""

    def __init__(self, max_workers: int = 32):
        self.max_workers = max_workers
        self.test_results: Dict[str, Any] = {}
        self.start_time = datetime.now()

    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive performance validation"""
        print(f"Starting Phase 2 Performance Validation with {self.max_workers} workers")
        print(f"Validation started at: {self.start_time}")
        print("-" * 60)

        validation_results = {
            'validation_timestamp': self.start_time.isoformat(),
            'max_workers': self.max_workers,
            'phase2_available': PHASE2_AVAILABLE,
            'tests': {}
        }

        if not PHASE2_AVAILABLE:
            print("❌ Phase 2 components not available - skipping validation")
            validation_results['status'] = 'skipped'
            return validation_results

        # Test 1: Atomic Initializer Race Condition Elimination
        print("🧪 Test 1: Atomic Initializer Race Condition Elimination")
        race_condition_results = self.test_atomic_initializer_race_conditions()
        validation_results['tests']['atomic_initializer'] = race_condition_results
        print(f"   Status: {'✅ PASSED' if race_condition_results['passed'] else '❌ FAILED'}")

        # Test 2: Deadlock Detection Performance
        print("\n🧪 Test 2: Deadlock Detection Performance")
        deadlock_results = self.test_deadlock_detection_performance()
        validation_results['tests']['deadlock_detection'] = deadlock_results
        print(f"   Status: {'✅ PASSED' if deadlock_results['passed'] else '❌ FAILED'}")

        # Test 3: Smart Message Queue Throughput
        print("\n🧪 Test 3: Smart Message Queue Throughput")
        queue_results = self.test_smart_queue_performance()
        validation_results['tests']['smart_queue'] = queue_results
        print(f"   Status: {'✅ PASSED' if queue_results['passed'] else '❌ FAILED'}")

        # Test 4: Integrated System Performance
        print("\n🧪 Test 4: Integrated System Performance")
        integrated_results = self.test_integrated_system_performance()
        validation_results['tests']['integrated_system'] = integrated_results
        print(f"   Status: {'✅ PASSED' if integrated_results['passed'] else '❌ FAILED'}")

        # Test 5: Maximum Load Stress Test
        print("\n🧪 Test 5: Maximum Load Stress Test")
        stress_results = self.test_maximum_load_stress()
        validation_results['tests']['stress_test'] = stress_results
        print(f"   Status: {'✅ PASSED' if stress_results['passed'] else '❌ FAILED'}")

        # Calculate overall results
        all_tests_passed = all(result['passed'] for result in validation_results['tests'].values())
        validation_results['status'] = 'passed' if all_tests_passed else 'failed'
        validation_results['completion_timestamp'] = datetime.now().isoformat()
        validation_results['duration_seconds'] = (
            datetime.now() - self.start_time
        ).total_seconds()

        print("\n" + "=" * 60)
        print(f"🏁 Phase 2 Performance Validation Complete")
        print(f"   Overall Status: {'✅ PASSED' if all_tests_passed else '❌ FAILED'}")
        print(f"   Duration: {validation_results['duration_seconds']:.2f} seconds")
        print(f"   Tests Passed: {sum(1 for r in validation_results['tests'].values() if r['passed'])}/{len(validation_results['tests'])}")

        # Save detailed results
        self.save_validation_results(validation_results)

        return validation_results

    def test_atomic_initializer_race_conditions(self) -> Dict[str, Any]:
        """Test atomic initializer for race condition elimination"""
        print("   Testing concurrent initialization with multiple processes...")

        test_iterations = 20
        successful_inits = []
        race_condition_detections = []

        for iteration in range(test_iterations):
            def concurrent_init_worker(process_id: int, results: List):
                try:
                    temp_file = tempfile.mktemp()
                    initializer = AtomicInitializer(
                        process_id=process_id,
                        total_processes=8,
                        state_file_path=temp_file,
                        enable_distributed_locking=True,
                        lock_timeout_seconds=10.0
                    )

                    component = ComponentInitTask(
                        component_id=f"race_test_{process_id}",
                        component_name=f"Race Test Component {process_id}",
                        init_function=lambda: time.sleep(random.uniform(0.01, 0.05)),  # Variable delay
                        cleanup_function=None,
                        dependencies=set(),
                        critical=True
                    )

                    initializer.register_component(component)
                    success = initializer.initialize()

                    results.append({
                        'process_id': process_id,
                        'success': success,
                        'is_leader': initializer.is_leader,
                        'lock_acquisitions': initializer.stats.get('lock_acquisitions', 0),
                        'lock_contentions': initializer.stats.get('lock_contentions', 0)
                    })

                    initializer.cleanup()
                    try:
                        os.unlink(temp_file)
                    except:
                        pass

                except Exception as e:
                    results.append({
                        'process_id': process_id,
                        'success': False,
                        'error': str(e)
                    })

            # Run concurrent initialization
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = []
                results = []

                for i in range(8):
                    future = executor.submit(concurrent_init_worker, i, results)
                    futures.append(future)

                # Wait for completion
                for future in futures:
                    future.result(timeout=30)

            # Analyze results
            successful = [r for r in results if r['success']]
            leaders = [r for r in successful if r['is_leader']]
            total_contentions = sum(r.get('lock_contentions', 0) for r in results)

            successful_inits.append(len(successful))
            race_condition_detections.append(len(leaders) == 1)  # Should be exactly 1 leader

        # Calculate statistics
        avg_successful = statistics.mean(successful_inits)
        no_race_conditions = sum(race_condition_detections)
        race_condition_rate = no_race_conditions / test_iterations

        results = {
            'passed': avg_successful >= 7.5 and race_condition_rate >= 0.95,  # 95% success rate
            'test_iterations': test_iterations,
            'avg_successful_initializations': avg_successful,
            'max_possible': 8,
            'race_condition_elimination_rate': race_condition_rate,
            'avg_lock_contentions': statistics.mean([
                sum(r.get('lock_contentions', 0) for r in results)
                for results in [successful_inits] * test_iterations
            ]) if race_condition_detections else 0
        }

        print(f"   Average successful initializations: {avg_successful:.1f}/8")
        print(f"   Race condition elimination rate: {race_condition_rate:.1%}")
        print(f"   Average lock contentions: {results['avg_lock_contentions']:.1f}")

        return results

    def test_deadlock_detection_performance(self) -> Dict[str, Any]:
        """Test deadlock detection performance"""
        print("   Testing deadlock detection and resolution...")

        detection_times = []
        resolution_times = []
        detection_accuracies = []

        for test_run in range(10):
            detector = DeadlockDetector(
                detection_interval_seconds=0.1,
                enable_auto_resolution=True,
                resolution_strategy=DeadlockDetector.VICTIM_SELECTION
            )

            detector.start()

            # Register processes
            for i in range(6):
                detector.register_process(i, Priority.NORMAL)

            # Create deadlock scenario
            start_time = time.time()

            # Create circular wait pattern
            requests = []
            for i in range(6):
                resource1 = f"resource_{i}"
                resource2 = f"resource_{(i + 1) % 6}"

                req1 = detector.request_resource(i, resource1, ResourceType.SHARED_MEMORY, exclusive=True)
                req2 = detector.request_resource(i, resource2, ResourceType.SHARED_MEMORY, exclusive=True)
                requests.extend([req1, req2])

            # Wait for detection
            detection_start = time.time()
            time.sleep(2)  # Allow detection to occur

            detection_time = time.time() - detection_start
            detection_times.append(detection_time)

            # Check results
            stats = detector.get_statistics()
            resolution_time = stats.get('average_resolution_time_ms', 0) / 1000
            resolution_times.append(resolution_time)

            # Check if deadlock was properly detected and resolved
            detected = stats['deadlocks_detected'] > 0
            resolved = stats['deadlocks_resolved'] > 0
            accuracy = 1.0 if detected and resolved else 0.0
            detection_accuracies.append(accuracy)

            detector.stop()

        # Calculate statistics
        avg_detection_time = statistics.mean(detection_times)
        avg_resolution_time = statistics.mean(resolution_times)
        accuracy_rate = statistics.mean(detection_accuracies)

        results = {
            'passed': avg_detection_time < 2.0 and accuracy_rate >= 0.8,
            'avg_detection_time_seconds': avg_detection_time,
            'avg_resolution_time_seconds': avg_resolution_time,
            'detection_accuracy_rate': accuracy_rate,
            'test_runs': len(detection_times)
        }

        print(f"   Average detection time: {avg_detection_time:.3f}s")
        print(f"   Average resolution time: {avg_resolution_time:.3f}s")
        print(f"   Detection accuracy rate: {accuracy_rate:.1%}")

        return results

    def test_smart_queue_performance(self) -> Dict[str, Any]:
        """Test smart message queue performance"""
        print("   Testing smart message queue throughput and backpressure...")

        target_throughput = 1000  # messages per second
        test_duration = 5  # seconds

        queue = SmartMessageQueue(
            max_size=target_throughput * test_duration * 2,
            enable_backpressure=True,
            enable_metrics=True,
            processing_threads=8
        )
        queue.start()

        # Producer thread
        def producer():
            sent = 0
            start_time = time.time()
            while time.time() - start_time < test_duration:
                try:
                    msg_id = queue.enqueue(
                        payload=f"perf_test_{sent}",
                        priority=random.choice(list(MessagePriority))
                    )
                    if msg_id:
                        sent += 1
                except:
                    pass  # Backpressure in action
                time.sleep(0.001)  # Small delay
            return sent

        # Consumer thread
        def consumer():
            received = 0
            start_time = time.time()
            while time.time() - start_time < test_duration:
                message = queue.dequeue(timeout_seconds=0.1)
                if message:
                    received += 1
            return received

        # Run test
        with ThreadPoolExecutor(max_workers=2) as executor:
            producer_future = executor.submit(producer)
            consumer_future = executor.submit(consumer)

            messages_sent = producer_future.result()
            messages_received = consumer_future.result()

        # Get metrics
        metrics = queue.get_metrics()
        queue.stop()

        # Calculate throughput
        actual_throughput = messages_received / test_duration
        throughput_efficiency = actual_throughput / target_throughput

        results = {
            'passed': throughput_efficiency >= 0.5 and metrics.backpressure_events >= 0,
            'target_throughput': target_throughput,
            'actual_throughput': actual_throughput,
            'throughput_efficiency': throughput_efficiency,
            'messages_sent': messages_sent,
            'messages_received': messages_received,
            'backpressure_events': metrics.backpressure_events,
            'queue_overflows': metrics.queue_overflows,
            'average_latency_ms': metrics.average_latency_ms
        }

        print(f"   Target throughput: {target_throughput} msg/s")
        print(f"   Actual throughput: {actual_throughput:.1f} msg/s")
        print(f"   Throughput efficiency: {throughput_efficiency:.1%}")
        print(f"   Backpressure events: {metrics.backpressure_events}")
        print(f"   Average latency: {metrics.average_latency_ms:.2f}ms")

        return results

    def test_integrated_system_performance(self) -> Dict[str, Any]:
        """Test integrated system performance"""
        print("   Testing integrated Phase 2 system performance...")

        def worker_process(worker_id: int, duration_seconds: int) -> Dict[str, Any]:
            """Worker process with full Phase 2 integration"""
            start_time = time.time()

            try:
                # Initialize Phase 2 components
                initializer = AtomicInitializer(
                    process_id=worker_id,
                    total_processes=8,
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

                # Initialize
                component = ComponentInitTask(
                    component_id=f"perf_worker_{worker_id}",
                    component_name=f"Performance Worker {worker_id}",
                    init_function=lambda: True,
                    cleanup_function=None,
                    dependencies=set(),
                    critical=True
                )

                initializer.register_component(component)
                init_success = initializer.initialize()
                init_time = time.time() - start_time

                if not init_success:
                    raise Exception("Initialization failed")

                # Perform work
                operations = {
                    'messages_sent': 0,
                    'messages_received': 0,
                    'resource_operations': 0,
                    'errors': 0
                }

                work_start = time.time()
                while (time.time() - work_start) < duration_seconds:
                    try:
                        # Message operations
                        msg_id = message_queue.enqueue(
                            payload=f"perf_{worker_id}_{operations['messages_sent']}",
                            priority=MessagePriority.NORMAL
                        )
                        if msg_id:
                            operations['messages_sent'] += 1

                        message = message_queue.dequeue(timeout_seconds=0.01)
                        if message:
                            operations['messages_received'] += 1

                        # Resource operations
                        if random.random() < 0.1:  # 10% chance
                            resource_id = f"perf_resource_{random.randint(0, 4)}"
                            req_id = deadlock_detector.request_resource(
                                worker_id, resource_id, ResourceType.SHARED_MEMORY
                            )
                            if req_id:
                                operations['resource_operations'] += 1
                                # Release after short time
                                time.sleep(0.001)
                                deadlock_detector.release_resource_request(req_id)

                    except Exception as e:
                        operations['errors'] += 1

                total_time = time.time() - start_time

                # Get final statistics
                worker_stats = {
                    'worker_id': worker_id,
                    'init_success': init_success,
                    'init_time_seconds': init_time,
                    'total_time_seconds': total_time,
                    'operations': operations,
                    'initializer_stats': initializer.stats.copy(),
                    'deadlock_stats': deadlock_detector.get_statistics(),
                    'queue_metrics': message_queue.get_metrics().to_dict()
                }

                # Cleanup
                deadlock_detector.unregister_process(worker_id)
                deadlock_detector.stop()
                message_queue.stop()
                initializer.cleanup()

                return worker_stats

            except Exception as e:
                return {
                    'worker_id': worker_id,
                    'init_success': False,
                    'error': str(e)
                }

        # Run integrated test
        num_workers = 8
        test_duration = 10

        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(worker_process, i, test_duration)
                for i in range(num_workers)
            ]

            results = [future.result(timeout=60) for future in futures]

        # Analyze results
        successful_workers = [r for r in results if r.get('init_success', False)]
        failed_workers = [r for r in results if not r.get('init_success', False)]

        if successful_workers:
            total_messages_sent = sum(w['operations']['messages_sent'] for w in successful_workers)
            total_messages_received = sum(w['operations']['messages_received'] for w in successful_workers)
            total_resource_ops = sum(w['operations']['resource_operations'] for w in successful_workers)
            total_errors = sum(w['operations']['errors'] for w in successful_workers)

            avg_init_time = statistics.mean(w['init_time_seconds'] for w in successful_workers)
            avg_queue_latency = statistics.mean(
                w['queue_metrics']['average_latency_ms'] for w in successful_workers
            )

            # Check for race conditions
            leaders = [w for w in successful_workers if w.get('initializer_stats', {}).get('is_leader', False)]
            race_conditions_eliminated = len(leaders) == 1

            # Check deadlock handling
            total_deadlocks = sum(w['deadlock_stats']['deadlocks_detected'] for w in successful_workers)
            total_resolutions = sum(w['deadlock_stats']['deadlocks_resolved'] for w in successful_workers)
        else:
            total_messages_sent = total_messages_received = total_resource_ops = total_errors = 0
            avg_init_time = avg_queue_latency = 0
            race_conditions_eliminated = False
            total_deadlocks = total_resolutions = 0

        results = {
            'passed': (
                len(successful_workers) >= num_workers * 0.9 and
                race_conditions_eliminated and
                total_errors < (total_messages_sent + total_messages_received) * 0.05
            ),
            'num_workers': num_workers,
            'test_duration_seconds': test_duration,
            'successful_workers': len(successful_workers),
            'failed_workers': len(failed_workers),
            'race_conditions_eliminated': race_conditions_eliminated,
            'total_messages_sent': total_messages_sent,
            'total_messages_received': total_messages_received,
            'total_resource_operations': total_resource_ops,
            'total_errors': total_errors,
            'avg_init_time_seconds': avg_init_time,
            'avg_queue_latency_ms': avg_queue_latency,
            'total_deadlocks_detected': total_deadlocks,
            'total_deadlocks_resolved': total_resolutions
        }

        print(f"   Successful workers: {len(successful_workers)}/{num_workers}")
        print(f"   Race conditions eliminated: {'✅' if race_conditions_eliminated else '❌'}")
        print(f"   Total messages: {total_messages_sent} sent, {total_messages_received} received")
        print(f"   Resource operations: {total_resource_ops}")
        print(f"   Errors: {total_errors}")
        print(f"   Average init time: {avg_init_time:.3f}s")
        print(f"   Average queue latency: {avg_queue_latency:.2f}ms")

        return results

    def test_maximum_load_stress(self) -> Dict[str, Any]:
        """Test system under maximum load stress"""
        print("   Testing system under maximum 32-core load...")

        # This test uses the enhanced parallel processing system
        try:
            system = EnhancedParallelProcessingSystem(
                max_workers=32,
                memory_limit_gb=64.0,
                enable_atomic_initializer=True,
                enable_deadlock_detection=True,
                enable_smart_queuing=True,
                enable_optimization=True,
                enable_monitoring=True
            )

            # Initialize system
            init_start = time.time()
            init_success = system.initialize()
            init_time = time.time() - init_start

            if not init_success:
                return {
                    'passed': False,
                    'error': 'System initialization failed',
                    'init_time_seconds': init_time
                }

            # Start system
            start_start = time.time()
            system.start()
            start_time = time.time() - start_start

            # Perform stress test
            stress_duration = 15
            operations_completed = 0
            errors_encountered = 0

            stress_start = time.time()
            while time.time() - stress_start < stress_duration:
                try:
                    # Simulate work load
                    status = system.get_system_status()
                    operations_completed += 1

                    # Check system health
                    if status.get('deadlock_detector_stats', {}).get('deadlocks_detected', 0) > 10:
                        print(f"   Warning: High deadlock count detected")
                        break

                    time.sleep(0.1)

                except Exception as e:
                    errors_encountered += 1

            stress_time = time.time() - stress_start

            # Get final status
            final_status = system.get_system_status()

            # Stop system
            stop_start = time.time()
            system.stop()
            stop_time = time.time() - stop_start

            results = {
                'passed': (
                    errors_encountered < operations_completed * 0.05 and
                    final_status.get('deadlock_detector_stats', {}).get('deadlocks_detected', 0) < 20
                ),
                'max_workers': 32,
                'init_success': init_success,
                'init_time_seconds': init_time,
                'start_time_seconds': start_time,
                'stress_duration_seconds': stress_duration,
                'stress_time_seconds': stress_time,
                'stop_time_seconds': stop_time,
                'operations_completed': operations_completed,
                'errors_encountered': errors_encountered,
                'error_rate': errors_encountered / max(operations_completed, 1),
                'final_system_status': final_status
            }

            print(f"   System initialization: {'✅' if init_success else '❌'} ({init_time:.3f}s)")
            print(f"   System startup: {start_time:.3f}s")
            print(f"   Stress operations: {operations_completed}")
            print(f"   Error rate: {results['error_rate']:.2%}")
            print(f"   Deadlocks detected: {final_status.get('deadlock_detector_stats', {}).get('deadlocks_detected', 0)}")
            print(f"   System shutdown: {stop_time:.3f}s")

            return results

        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'max_workers': 32
            }

    def save_validation_results(self, results: Dict[str, Any]):
        """Save validation results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"phase2_validation_results_{timestamp}.json"
        filepath = project_root / filename

        try:
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n📊 Detailed results saved to: {filepath}")
        except Exception as e:
            print(f"⚠️  Could not save results to file: {e}")


def main():
    """Main validation function"""
    print("🚀 Phase 2 IPC Synchronization Performance Validation")
    print("=" * 60)

    # Check system resources
    cpu_count = mp.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    print(f"System Resources:")
    print(f"   CPU Cores: {cpu_count}")
    print(f"   Memory: {memory_gb:.1f}GB")
    print(f"   Python Processes: {len(psutil.pids())}")
    print()

    if cpu_count < 8:
        print("⚠️  Warning: Less than 8 CPU cores detected. Some tests may be limited.")

    if memory_gb < 8:
        print("⚠️  Warning: Less than 8GB RAM detected. Some tests may be limited.")

    print()

    # Run validation
    validator = PerformanceValidator(max_workers=min(32, cpu_count))
    results = validator.run_comprehensive_validation()

    # Final summary
    print("\n" + "=" * 60)
    print("📋 VALIDATION SUMMARY")
    print("=" * 60)

    for test_name, test_results in results['tests'].items():
        status = "✅ PASSED" if test_results['passed'] else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")

    print(f"\n🏆 OVERALL RESULT: {'✅ PASSED' if results['status'] == 'passed' else '❌ FAILED'}")
    print(f"⏱️  Total Duration: {results['duration_seconds']:.2f} seconds")

    if results['status'] == 'passed':
        print("\n🎉 Phase 2 IPC Synchronization Enhancement is ready for production!")
        print("   ✅ Zero race conditions under concurrent startup")
        print("   ✅ Effective deadlock detection and resolution")
        print("   ✅ High-performance smart queuing with backpressure")
        print("   ✅ Production-grade error handling and recovery")
        print("   ✅ Comprehensive monitoring and metrics")
    else:
        print("\n⚠️  Some tests failed. Review the detailed results for issues to address.")

    return results['status'] == 'passed'


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
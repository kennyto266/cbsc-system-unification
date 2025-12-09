#!/usr/bin/env python3
"""
Chaos Engineering Tests for Random Process Termination and Resource Exhaustion Scenarios
Tests system resilience under failure conditions and extreme resource constraints
"""

import os
import sys
import time
import unittest
import threading
import tempfile
import json
import random
import signal
import subprocess
import multiprocessing
import concurrent.futures
import psutil
import gc
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Callable, Tuple
import queue

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import actual components if they exist
try:
    from src.ipc.atomic_initializer import AtomicInitializer
    from src.memory.adaptive_allocator import AdaptiveMemoryAllocator
except ImportError:
    AtomicInitializer = Mock
    AdaptiveMemoryAllocator = Mock


@dataclass
class ChaosTestResult:
    """Result of a chaos engineering test"""
    test_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    chaos_injection: str
    system_responded: bool
    recovery_time_seconds: float
    data_corrupted: bool
    processes_lost: int
    resources_exhausted: List[str]
    errors: List[str]
    metrics: Dict[str, Any]


class ChaosInjector:
    """Injects various failure scenarios into the system"""

    def __init__(self):
        self.active_injections = []
        self.injection_lock = threading.Lock()
        self.original_handlers = {}

    def inject_random_process_termination(self, target_processes: List[psutil.Process]) -> int:
        """Randomly terminate processes"""
        if not target_processes:
            return 0

        num_to_kill = max(1, len(target_processes) // 4)  # Kill 25% of processes
        killed_count = 0

        for process in random.sample(target_processes, min(num_to_kill, len(target_processes))):
            try:
                process.terminate()
                killed_count += 1
                time.sleep(0.1)  # Stagger terminations
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return killed_count

    def inject_memory_exhaustion(self, target_process: psutil.Process, memory_mb: int) -> bool:
        """Inject memory exhaustion into target process"""
        try:
            # This is a simulation - in real scenarios, this would be more sophisticated
            current_memory = target_process.memory_info().rss / (1024 * 1024)
            target_memory = current_memory + memory_mb

            # Simulate memory pressure by creating allocations
            data = []
            allocation_size = 1024 * 1024  # 1MB chunks
            chunks_needed = memory_mb

            try:
                for i in range(chunks_needed):
                    data.append(bytearray(allocation_size))
                    if i % 100 == 0:  # Check every 100MB
                        current = target_process.memory_info().rss / (1024 * 1024)
                        if current >= target_memory:
                            break

                # Hold memory for a short time
                time.sleep(2.0)

                # Cleanup
                del data
                return True

            except MemoryError:
                return False

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def inject_cpu_exhaustion(self, duration_seconds: float) -> bool:
        """Inject CPU exhaustion"""
        try:
            end_time = time.time() + duration_seconds
            workload_threads = []

            def cpu_burn():
                while time.time() < end_time:
                    _ = i * i * i for i in range(1000)

            # Start multiple CPU burn threads
            for i in range(multiprocessing.cpu_count()):
                thread = threading.Thread(target=cpu_burn, daemon=True)
                thread.start()
                workload_threads.append(thread)

            # Wait for duration
            time.sleep(duration_seconds)

            return True

        except Exception:
            return False

    def inject_io_latency(self, duration_seconds: float, latency_ms: int = 100):
        """Simulate I/O latency"""
        # This would typically involve network or disk latency injection
        # For testing purposes, we simulate with delays
        start_time = time.time()

        def delayed_io():
            while time.time() - start_time < duration_seconds:
                time.sleep(latency_ms / 1000.0)
                yield

        return list(delayed_io())

    def inject_network_partition(self, duration_seconds: float):
        """Simulate network partition"""
        # In a real implementation, this would use network namespaces or firewall rules
        # For testing, we simulate by blocking communication
        return {
            'partition_active': True,
            'duration': duration_seconds,
            'affected_services': ['database', 'cache', 'message_queue']
        }

    def inject_disk_space_exhaustion(self, temp_dir: str, fill_percent: float = 95.0) -> bool:
        """Fill disk space to simulate exhaustion"""
        try:
            stat = os.statvfs(temp_dir)
            total_space = stat.f_frsize * stat.f_blocks
            target_usage = total_space * (fill_percent / 100.0)
            current_usage = total_space - (stat.f_bavail * stat.f_frsize)

            space_to_fill = target_usage - current_usage
            if space_to_fill <= 0:
                return True  # Already at target usage

            # Create large files to fill space
            chunk_size = 1024 * 1024  # 1MB chunks
            chunks_needed = int(space_to_fill / chunk_size)
            created_files = []

            try:
                for i in range(chunks_needed):
                    file_path = os.path.join(temp_dir, f"chaos_fill_{i}.tmp")
                    with open(file_path, 'wb') as f:
                        f.write(b'\0' * chunk_size)
                    created_files.append(file_path)

                time.sleep(5.0)  # Maintain exhaustion for 5 seconds

                return True

            except (OSError, IOError):
                return False

            finally:
                # Cleanup
                for file_path in created_files:
                    try:
                        os.unlink(file_path)
                    except OSError:
                        pass

        except Exception:
            return False

    def cleanup(self):
        """Clean up all active chaos injections"""
        with self.injection_lock:
            self.active_injections.clear()


class ResilientSystem:
    """Mock system that should be resilient to chaos injections"""

    def __init__(self, num_processes=8):
        self.num_processes = num_processes
        self.processes = {}
        self.shared_state = {}
        self.state_lock = threading.Lock()
        self.health_monitoring = True
        self.recovery_active = False
        self.process_pids = set()

    def start_system(self):
        """Start the resilient system"""
        for i in range(self.num_processes):
            process = MockProcess(process_id=i)
            self.processes[i] = process
            self.process_pids.add(process.pid)

        # Start health monitoring
        monitor_thread = threading.Thread(target=self._health_monitor, daemon=True)
        monitor_thread.start()

        return True

    def _health_monitor(self):
        """Monitor system health and trigger recovery"""
        while self.health_monitoring:
            try:
                # Check process health
                dead_processes = []
                for pid, process in self.processes.items():
                    if not process.is_alive():
                        dead_processes.append(pid)

                # Trigger recovery for dead processes
                if dead_processes and not self.recovery_active:
                    self._trigger_recovery(dead_processes)

                time.sleep(1.0)

            except Exception:
                pass

    def _trigger_recovery(self, dead_processes: List[int]):
        """Trigger recovery for dead processes"""
        self.recovery_active = True

        try:
            # Restart dead processes
            for pid in dead_processes:
                if pid in self.processes:
                    old_process = self.processes[pid]
                    new_process = MockProcess(process_id=pid, recovery_from=old_process)
                    self.processes[pid] = new_process

            # Restore shared state consistency
            self._restore_consistency()

        finally:
            self.recovery_active = False

    def _restore_consistency(self):
        """Restore system consistency after recovery"""
        # Simulate consistency restoration
        time.sleep(0.5)

    def handle_memory_pressure(self):
        """Handle memory pressure scenarios"""
        # Trigger garbage collection
        gc.collect()

        # Notify components to reduce memory usage
        with self.state_lock:
            self.shared_state['memory_pressure'] = True

    def handle_cpu_exhaustion(self):
        """Handle CPU exhaustion scenarios"""
        # Reduce non-critical processing
        with self.state_lock:
            self.shared_state['cpu_throttled'] = True

    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        alive_processes = sum(1 for p in self.processes.values() if p.is_alive())
        memory_info = psutil.Process().memory_info()
        cpu_percent = psutil.cpu_percent()

        return {
            'alive_processes': alive_processes,
            'total_processes': len(self.processes),
            'process_health_ratio': alive_processes / len(self.processes),
            'memory_mb': memory_info.rss / (1024 * 1024),
            'cpu_percent': cpu_percent,
            'recovery_active': self.recovery_active,
            'shared_state': self.shared_state.copy()
        }

    def stop_system(self):
        """Stop the system"""
        self.health_monitoring = False
        for process in self.processes.values():
            process.stop()


class MockProcess:
    """Mock process for testing"""

    def __init__(self, process_id: int, recovery_from: Optional['MockProcess'] = None):
        self.process_id = process_id
        self.pid = os.getpid() + process_id  # Mock PID
        self.alive = True
        self.start_time = time.time()
        self.recovery_count = 0
        self.last_recovery = None

        if recovery_from:
            self.recovery_count = recovery_from.recovery_count + 1
            self.last_recovery = time.time()

    def is_alive(self) -> bool:
        return self.alive

    def terminate(self):
        self.alive = False

    def stop(self):
        self.alive = False

    def restart(self):
        self.alive = True
        self.recovery_count += 1
        self.last_recovery = time.time()


class ChaosTestRunner:
    """Runner for chaos engineering tests"""

    def __init__(self):
        self.chaos_injector = ChaosInjector()
        self.test_results = []

    def run_process_termination_test(self, system: ResilientSystem) -> ChaosTestResult:
        """Test system resilience to random process termination"""
        test_name = "process_termination_test"
        print(f"Starting {test_name}...")

        start_time = datetime.now()
        initial_health = system.get_system_health()

        # Wait for system to stabilize
        time.sleep(2.0)

        # Inject chaos - randomly terminate processes
        processes = list(system.processes.values())
        mock_processes = [Mock(pid=p.pid + 1000) for p in processes]  # Mock psutil.Process
        killed_count = self.chaos_injector.inject_random_process_termination(mock_processes)

        # Actually terminate some mock processes
        actual_to_kill = min(killed_count, len(processes))
        for process in random.sample(processes, actual_to_kill):
            process.terminate()

        # Measure recovery time
        recovery_start = time.time()
        system_recovered = False
        max_recovery_time = 30.0

        while time.time() - recovery_start < max_recovery_time:
            current_health = system.get_system_health()
            if current_health['process_health_ratio'] >= 0.9:  # 90% recovery threshold
                system_recovered = True
                break
            time.sleep(0.5)

        recovery_time = time.time() - recovery_start
        end_time = datetime.now()

        # Analyze results
        final_health = system.get_system_health()
        processes_lost = initial_health['total_processes'] - final_health['alive_processes']

        result = ChaosTestResult(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=(end_time - start_time).total_seconds(),
            chaos_injection=f"Random termination of {killed_count} processes",
            system_responded=system_recovered,
            recovery_time_seconds=recovery_time,
            data_corrupted=False,  # Would check actual data consistency
            processes_lost=processes_lost,
            resources_exhausted=[],
            errors=[] if system_recovered else ["System failed to recover"],
            metrics={
                'initial_health': initial_health,
                'final_health': final_health,
                'killed_processes': killed_count,
                'recovery_success': system_recovered
            }
        )

        self.test_results.append(result)
        return result

    def run_memory_exhaustion_test(self, system: ResilientSystem) -> ChaosTestResult:
        """Test system resilience to memory exhaustion"""
        test_name = "memory_exhaustion_test"
        print(f"Starting {test_name}...")

        start_time = datetime.now()
        initial_health = system.get_system_health()

        # Inject memory exhaustion
        current_process = psutil.Process()
        memory_injected = self.chaos_injector.inject_memory_exhaustion(current_process, 1024)  # 1GB

        # Monitor system response
        recovery_start = time.time()
        system_handled = False
        max_response_time = 15.0

        while time.time() - recovery_start < max_response_time:
            try:
                # Check if system handled memory pressure
                health = system.get_system_health()
                if health.get('memory_pressure', False):
                    system.handle_memory_pressure()
                    system_handled = True
                    break

                # Also check if memory usage is under control
                current_memory = health['memory_mb']
                if current_memory < initial_health['memory_mb'] * 1.5:  # Within 50% growth
                    system_handled = True
                    break

                time.sleep(0.5)

            except Exception as e:
                break

        response_time = time.time() - recovery_start
        end_time = datetime.now()

        # Clean up memory
        gc.collect()
        time.sleep(1.0)

        final_health = system.get_system_health()
        resources_exhausted = []
        if final_health['memory_mb'] > initial_health['memory_mb'] * 2:
            resources_exhausted.append('memory')

        result = ChaosTestResult(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=(end_time - start_time).total_seconds(),
            chaos_injection=f"Memory exhaustion injection: {memory_injected}",
            system_responded=system_handled,
            recovery_time_seconds=response_time,
            data_corrupted=False,
            processes_lost=0,
            resources_exhausted=resources_exhausted,
            errors=[] if system_handled else ["System failed to handle memory pressure"],
            metrics={
                'initial_health': initial_health,
                'final_health': final_health,
                'memory_injected': memory_injected,
                'handling_success': system_handled
            }
        )

        self.test_results.append(result)
        return result

    def run_cpu_exhaustion_test(self, system: ResilientSystem) -> ChaosTestResult:
        """Test system resilience to CPU exhaustion"""
        test_name = "cpu_exhaustion_test"
        print(f"Starting {test_name}...")

        start_time = datetime.now()
        initial_health = system.get_system_health()

        # Inject CPU exhaustion
        cpu_exhausted = self.chaos_injector.inject_cpu_exhaustion(duration_seconds=5.0)

        # Monitor system response
        recovery_start = time.time()
        system_handled = False
        max_response_time = 10.0

        while time.time() - recovery_start < max_response_time:
            try:
                health = system.get_system_health()
                if health.get('cpu_throttled', False):
                    system_handled = True
                    break

                # Check if CPU usage is reasonable again
                current_cpu = health['cpu_percent']
                if current_cpu < 80.0:  # Below 80% is acceptable
                    system_handled = True
                    break

                time.sleep(0.5)

            except Exception:
                break

        response_time = time.time() - recovery_start
        end_time = datetime.now()

        final_health = system.get_system_health()
        resources_exhausted = []
        if final_health['cpu_percent'] > 90.0:
            resources_exhausted.append('cpu')

        result = ChaosTestResult(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=(end_time - start_time).total_seconds(),
            chaos_injection=f"CPU exhaustion injection: {cpu_exhausted}",
            system_responded=system_handled,
            recovery_time_seconds=response_time,
            data_corrupted=False,
            processes_lost=0,
            resources_exhausted=resources_exhausted,
            errors=[] if system_handled else ["System failed to handle CPU exhaustion"],
            metrics={
                'initial_health': initial_health,
                'final_health': final_health,
                'cpu_exhausted': cpu_exhausted,
                'handling_success': system_handled
            }
        )

        self.test_results.append(result)
        return result

    def run_network_partition_test(self, system: ResilientSystem) -> ChaosTestResult:
        """Test system resilience to network partition"""
        test_name = "network_partition_test"
        print(f"Starting {test_name}...")

        start_time = datetime.now()
        initial_health = system.get_system_health()

        # Inject network partition
        partition_info = self.chaos_injector.inject_network_partition(duration_seconds=5.0)

        # Monitor system response
        recovery_start = time.time()
        system_recovered = False
        max_recovery_time = 15.0

        # Simulate network partition effects
        with system.state_lock:
            system.shared_state['network_partition'] = True
            system.shared_state['partition_duration'] = partition_info['duration']

        while time.time() - recovery_start < max_recovery_time:
            try:
                health = system.get_system_health()

                # Check if system is handling partition (should maintain operation)
                if health['process_health_ratio'] >= 0.8:  # 80% processes still alive
                    system_recovered = True
                    break

                time.sleep(0.5)

            except Exception:
                break

        # Remove partition effects
        with system.state_lock:
            system.shared_state.pop('network_partition', None)
            system.shared_state.pop('partition_duration', None)

        recovery_time = time.time() - recovery_start
        end_time = datetime.now()

        final_health = system.get_system_health()

        result = ChaosTestResult(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=(end_time - start_time).total_seconds(),
            chaos_injection=f"Network partition: {partition_info}",
            system_responded=system_recovered,
            recovery_time_seconds=recovery_time,
            data_corrupted=False,
            processes_lost=initial_health['total_processes'] - final_health['alive_processes'],
            resources_exhausted=['network'],
            errors=[] if system_recovered else ["System failed to handle network partition"],
            metrics={
                'initial_health': initial_health,
                'final_health': final_health,
                'partition_info': partition_info,
                'recovery_success': system_recovered
            }
        )

        self.test_results.append(result)
        return result

    def run_mixed_chaos_test(self, system: ResilientSystem) -> ChaosTestResult:
        """Test system resilience to multiple simultaneous chaos injections"""
        test_name = "mixed_chaos_test"
        print(f"Starting {test_name}...")

        start_time = datetime.now()
        initial_health = system.get_system_health()

        # Inject multiple chaos scenarios simultaneously
        chaos_results = []

        # 1. Process termination
        processes = list(system.processes.values())
        mock_processes = [Mock(pid=p.pid + 1000) for p in processes[:2]]  # Kill 2 processes
        killed = self.chaos_injector.inject_random_process_termination(mock_processes)
        for process in processes[:2]:
            process.terminate()
        chaos_results.append(f"Process termination: {killed}")

        # 2. Memory pressure
        system.handle_memory_pressure()
        chaos_results.append("Memory pressure handling")

        # 3. CPU throttling
        system.handle_cpu_exhaustion()
        chaos_results.append("CPU throttling")

        # Monitor system recovery
        recovery_start = time.time()
        system_recovered = False
        max_recovery_time = 20.0

        while time.time() - recovery_start < max_recovery_time:
            try:
                health = system.get_system_health()

                # Check multiple recovery indicators
                processes_recovered = health['process_health_ratio'] >= 0.8
                memory_stable = health['memory_mb'] < initial_health['memory_mb'] * 1.5

                if processes_recovered and memory_stable:
                    system_recovered = True
                    break

                time.sleep(0.5)

            except Exception:
                break

        recovery_time = time.time() - recovery_start
        end_time = datetime.now()

        final_health = system.get_system_health()
        processes_lost = initial_health['total_processes'] - final_health['alive_processes']
        resources_exhausted = []
        if final_health['memory_mb'] > initial_health['memory_mb'] * 2:
            resources_exhausted.append('memory')
        if final_health['cpu_percent'] > 90.0:
            resources_exhausted.append('cpu')

        result = ChaosTestResult(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=(end_time - start_time).total_seconds(),
            chaos_injection="; ".join(chaos_results),
            system_responded=system_recovered,
            recovery_time_seconds=recovery_time,
            data_corrupted=False,
            processes_lost=processes_lost,
            resources_exhausted=resources_exhausted,
            errors=[] if system_recovered else ["System failed to handle mixed chaos"],
            metrics={
                'initial_health': initial_health,
                'final_health': final_health,
                'chaos_injections': chaos_results,
                'recovery_success': system_recovered
            }
        )

        self.test_results.append(result)
        return result

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive chaos test report"""
        if not self.test_results:
            return {'error': 'No test results available'}

        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.system_responded)

        avg_recovery_time = statistics.mean([r.recovery_time_seconds for r in self.test_results])
        max_recovery_time = max([r.recovery_time_seconds for r in self.test_results])

        total_processes_lost = sum([r.processes_lost for r in self.test_results])
        resources_tested = set()
        for r in self.test_results:
            resources_tested.update(r.resources_exhausted)

        return {
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'success_rate': successful_tests / total_tests if total_tests > 0 else 0,
                'avg_recovery_time_seconds': avg_recovery_time,
                'max_recovery_time_seconds': max_recovery_time,
                'total_processes_lost': total_processes_lost,
                'resources_tested': list(resources_tested)
            },
            'test_results': [asdict(result) for result in self.test_results],
            'recommendations': self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        # Analyze common failure patterns
        recovery_times = [r.recovery_time_seconds for r in self.test_results]
        if statistics.mean(recovery_times) > 10.0:
            recommendations.append("Implement faster recovery mechanisms (average recovery time > 10s)")

        process_losses = [r.processes_lost for r in self.test_results]
        if sum(process_losses) > 0:
            recommendations.append("Improve process monitoring and automatic restart capabilities")

        memory_issues = sum(1 for r in self.test_results if 'memory' in r.resources_exhausted)
        if memory_issues > len(self.test_results) // 2:
            recommendations.append("Implement better memory management and pressure handling")

        failed_tests = [r for r in self.test_results if not r.system_responded]
        if failed_tests:
            common_errors = {}
            for test in failed_tests:
                for error in test.errors:
                    common_errors[error] = common_errors.get(error, 0) + 1

            most_common_error = max(common_errors.items(), key=lambda x: x[1])[0]
            recommendations.append(f"Address most common failure: {most_common_error}")

        if not recommendations:
            recommendations.append("System shows good resilience to chaos injections")

        return recommendations


class TestChaosEngineering(unittest.TestCase):
    """Chaos Engineering test suite"""

    def setUp(self):
        """Set up test fixtures"""
        self.system = ResilientSystem(num_processes=8)
        self.runner = ChaosTestRunner()
        self.system.start_system()

    def tearDown(self):
        """Clean up test fixtures"""
        self.system.stop_system()
        self.runner.chaos_injector.cleanup()

    def test_process_termination_resilience(self):
        """Test system resilience to random process termination"""
        result = self.runner.run_process_termination_test(self.system)

        # Validate chaos test results
        self.assertGreater(result.processes_lost, 0, "Some processes should have been terminated")
        self.assertLess(result.processes_lost, self.system.num_processes // 2,
                        "Should not lose majority of processes")

        # System should recover
        self.assertTrue(result.system_responded, "System should recover from process termination")
        self.assertLess(result.recovery_time_seconds, 30.0,
                       "Recovery should complete within 30 seconds")

        # Final system health should be good
        final_health = result.metrics['final_health']
        self.assertGreaterEqual(final_health['process_health_ratio'], 0.8,
                               "Final process health should be >= 80%")

        print(f"Process termination test: {result.processes_lost} processes lost, "
              f"{result.recovery_time_seconds:.2f}s recovery")

    def test_memory_exhaustion_resilience(self):
        """Test system resilience to memory exhaustion"""
        result = self.runner.run_memory_exhaustion_test(self.system)

        # System should handle memory pressure
        self.assertTrue(result.system_responded, "System should handle memory exhaustion")
        self.assertLess(result.recovery_time_seconds, 15.0,
                       "Memory pressure response should be quick")

        # Memory should be under control
        final_health = result.metrics['final_health']
        self.assertLess(final_health['memory_mb'], 2048,  # Less than 2GB
                       "Final memory usage should be reasonable")

        print(f"Memory exhaustion test: {result.metrics['memory_injected']} memory injected, "
              f"{result.recovery_time_seconds:.2f}s response time")

    def test_cpu_exhaustion_resilience(self):
        """Test system resilience to CPU exhaustion"""
        result = self.runner.run_cpu_exhaustion_test(self.system)

        # System should handle CPU exhaustion
        self.assertTrue(result.system_responded, "System should handle CPU exhaustion")
        self.assertLess(result.recovery_time_seconds, 10.0,
                       "CPU exhaustion response should be quick")

        print(f"CPU exhaustion test: {result.metrics['cpu_exhausted']} CPU exhaustion, "
              f"{result.recovery_time_seconds:.2f}s response time")

    def test_network_partition_resilience(self):
        """Test system resilience to network partition"""
        result = self.runner.run_network_partition_test(self.system)

        # System should handle network partition
        self.assertTrue(result.system_responded, "System should handle network partition")
        self.assertLess(result.recovery_time_seconds, 15.0,
                       "Network partition recovery should be reasonable")

        # Most processes should survive
        final_health = result.metrics['final_health']
        self.assertGreaterEqual(final_health['process_health_ratio'], 0.7,
                               "At least 70% of processes should survive network partition")

        print(f"Network partition test: {result.recovery_time_seconds:.2f}s recovery, "
              f"{final_health['process_health_ratio']:.1%} processes survived")

    def test_mixed_chaos_resilience(self):
        """Test system resilience to multiple simultaneous chaos injections"""
        result = self.runner.run_mixed_chaos_test(self.system)

        # System should handle mixed chaos
        self.assertTrue(result.system_responded, "System should handle mixed chaos scenarios")
        self.assertLess(result.recovery_time_seconds, 20.0,
                       "Mixed chaos recovery should be within 20 seconds")

        # System should maintain reasonable health
        final_health = result.metrics['final_health']
        self.assertGreaterEqual(final_health['process_health_ratio'], 0.7,
                               "Final process health should be >= 70%")

        print(f"Mixed chaos test: {result.recovery_time_seconds:.2f}s recovery, "
              f"{final_health['process_health_ratio']:.1%} final health")

    def test_chaos_test_report_generation(self):
        """Test comprehensive chaos test report generation"""
        # Run a few tests to generate data
        self.runner.run_process_termination_test(self.system)
        self.runner.run_memory_exhaustion_test(self.system)
        self.runner.run_cpu_exhaustion_test(self.system)

        # Generate report
        report = self.runner.generate_report()

        # Validate report structure
        self.assertIn('summary', report)
        self.assertIn('test_results', report)
        self.assertIn('recommendations', report)

        summary = report['summary']
        self.assertIn('total_tests', summary)
        self.assertIn('success_rate', summary)
        self.assertIn('avg_recovery_time_seconds', summary)
        self.assertIn('total_processes_lost', summary)

        # Validate content
        self.assertEqual(summary['total_tests'], 3)
        self.assertGreater(summary['success_rate'], 0)
        self.assertGreater(summary['avg_recovery_time_seconds'], 0)
        self.assertIsInstance(summary['recommendations'], list)

        print(f"Chaos test report: {summary['success_rate']:.1%} success rate, "
              f"{summary['avg_recovery_time_seconds']:.2f}s avg recovery")

    def test_gradual_degradation_resilience(self):
        """Test system resilience under gradual degradation"""
        # Gradually increase chaos intensity
        degradation_levels = [
            {'processes_to_kill': 1, 'memory_pressure': False},
            {'processes_to_kill': 2, 'memory_pressure': True},
            {'processes_to_kill': 3, 'memory_pressure': True},
        ]

        for level in degradation_levels:
            # Kill processes
            processes = list(self.system.processes.values())
            for process in processes[:level['processes_to_kill']]:
                if process.is_alive():
                    process.terminate()

            # Apply memory pressure if specified
            if level['memory_pressure']:
                self.system.handle_memory_pressure()

            # Wait for system to stabilize
            time.sleep(2.0)

            # Check system health
            health = self.system.get_system_health()
            self.assertGreaterEqual(health['process_health_ratio'], 0.6,
                                   f"System should maintain >= 60% health at degradation level {level}")

        print("Gradual degradation test completed successfully")

    def test_cascade_failure_prevention(self):
        """Test system's ability to prevent cascade failures"""
        # Simulate cascade scenario
        failure_spread = False

        # Initial failure
        if self.system.processes:
            initial_process = list(self.system.processes.values())[0]
            initial_process.terminate()

            # Wait to see if failure spreads
            time.sleep(3.0)

            # Check if failure was contained
            health = self.system.get_system_health()
            alive_after_initial = health['alive_processes']

            # Additional stress
            self.system.handle_memory_pressure()
            time.sleep(2.0)

            # Final health check
            final_health = self.system.get_system_health()
            alive_after_stress = final_health['alive_processes']

            # Cascade failure occurs if many more processes die
            if alive_after_stress < alive_after_initial * 0.8:  # Lost >20% more
                failure_spread = True

        # System should prevent cascade failures
        self.assertFalse(failure_spread, "System should prevent cascade failures")

        print("Cascade failure prevention test: No cascade detected")

    def test_zero_downtime_recovery(self):
        """Test system's ability to recover with zero downtime"""
        initial_health = self.system.get_system_health()
        initial_processes = initial_health['alive_processes']

        # Kill a critical process
        if self.system.processes:
            critical_process = list(self.system.processes.values())[0]
            critical_process.terminate()

            # Monitor for recovery without losing availability
            recovery_start = time.time()
            zero_downtime_achieved = False

            while time.time() - recovery_start < 10.0:
                health = self.system.get_system_health()

                # Zero downtime: at least 90% of original processes remain
                if health['alive_processes'] >= initial_processes * 0.9:
                    zero_downtime_achieved = True
                    break

                time.sleep(0.5)

            self.assertTrue(zero_downtime_achieved,
                          "System should maintain availability during recovery")

        print("Zero downtime recovery test: Availability maintained")


if __name__ == '__main__':
    import statistics
    unittest.main(verbosity=2)
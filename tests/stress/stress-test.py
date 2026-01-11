"""
Stress Testing Suite for CBSC Trading System
Tests system behavior under extreme conditions
"""

import asyncio
import aiohttp
import time
import json
import sys
import random
import threading
import queue
import psutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import List, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class StressTest:
    def __init__(self, base_url: str = "http://localhost:3003"):
        self.base_url = base_url
        self.results = {
            'tests': [],
            'system_metrics': [],
            'errors': [],
            'summary': {}
        }
        self.process = psutil.Process()
        self.stop_testing = False
        self.error_queue = queue.Queue()

    async def run_stress_tests(self):
        """Run comprehensive stress tests"""
        print("🔥 Starting Stress Tests\n")

        # Test 1: Maximum Concurrent Users
        await self.test_max_concurrent_users()

        # Test 2: Resource Exhaustion
        await self.test_resource_exhaustion()

        # Test 3: Sudden Traffic Spike
        await self.test_traffic_spike()

        # Test 4: Sustained High Load
        await self.test_sustained_load()

        # Test 5: Memory Leak Detection Under Stress
        await self.test_memory_under_stress()

        # Generate comprehensive report
        self.generate_stress_report()

    async def test_max_concurrent_users(self):
        """Test maximum number of concurrent users the system can handle"""
        print("📊 Test 1: Maximum Concurrent Users")
        print("-" * 40)

        concurrent_levels = [100, 200, 500, 1000, 2000]
        max_successful = 0

        for concurrent in concurrent_levels:
            if self.stop_testing:
                break

            print(f"\n  🔍 Testing with {concurrent} concurrent users...")

            # Monitor system resources
            initial_memory = self.process.memory_info().rss / 1024 / 1024

            try:
                # Create tasks for concurrent users
                tasks = []
                for i in range(concurrent):
                    task = asyncio.create_task(
                        self.simulate_user_session(f"user_{concurrent}_{i}")
                    )
                    tasks.append(task)

                # Wait for all tasks to complete with timeout
                done, pending = await asyncio.wait(
                    tasks,
                    timeout=60,
                    return_when=asyncio.ALL_COMPLETED
                )

                # Cancel any pending tasks
                for task in pending:
                    task.cancel()

                # Count successful sessions
                successful = sum(1 for task in done if not task.exception())

                # Check system health
                final_memory = self.process.memory_info().rss / 1024 / 1024
                memory_increase = final_memory - initial_memory
                cpu_usage = self.process.cpu_percent()

                print(f"    ✅ Successful sessions: {successful}/{concurrent}")
                print(f"    💾 Memory increase: {memory_increase:.2f}MB")
                print(f"    🔥 CPU usage: {cpu_usage:.1f}%")

                # Record results
                self.results['tests'].append({
                    'type': 'max_concurrent_users',
                    'concurrent_users': concurrent,
                    'successful_sessions': successful,
                    'success_rate': (successful / concurrent) * 100,
                    'memory_increase_mb': memory_increase,
                    'cpu_usage': cpu_usage,
                    'timestamp': datetime.now().isoformat()
                })

                if successful >= concurrent * 0.9:  # 90% success rate
                    max_successful = concurrent
                else:
                    print(f"    ⚠️ Success rate dropped below 90%")
                    break

            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
                self.error_queue.put(('max_concurrent_users', str(e)))
                break

        print(f"\n📈 Maximum concurrent users supported: {max_successful}")

    async def test_resource_exhaustion(self):
        """Test system behavior when resources are exhausted"""
        print("\n📊 Test 2: Resource Exhaustion")
        print("-" * 40)

        # Test memory exhaustion
        print("\n  💾 Testing memory exhaustion...")
        await self.test_memory_exhaustion()

        # Test CPU exhaustion
        print("\n  🔥 Testing CPU exhaustion...")
        await self.test_cpu_exhaustion()

        # Test connection pool exhaustion
        print("\n  🔗 Testing connection pool exhaustion...")
        await self.test_connection_exhaustion()

    async def test_memory_exhaustion(self):
        """Test memory exhaustion scenario"""
        memory_usage = []
        start_time = time.time()

        # Create memory-intensive tasks
        async def memory_intensive_task():
            large_data = []
            try:
                for i in range(1000):
                    large_data.append(np.random.random((1000, 1000)))
                    if i % 100 == 0:
                        current_memory = self.process.memory_info().rss / 1024 / 1024
                        memory_usage.append(current_memory)

                        # Stop if memory usage is critical
                        if current_memory > 2000:  # 2GB limit
                            break

                # Make some API calls to test response under memory pressure
                await self.client.get("/api/strategies")

            except MemoryError:
                print(f"    💥 Memory limit reached at {self.process.memory_info().rss / 1024 / 1024:.2f}MB")

        # Run multiple memory-intensive tasks
        tasks = [memory_intensive_task() for _ in range(10)]

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"    ❌ Memory exhaustion test failed: {str(e)}")

        test_duration = time.time() - start_time
        peak_memory = max(memory_usage) if memory_usage else 0

        self.results['tests'].append({
            'type': 'memory_exhaustion',
            'peak_memory_mb': peak_memory,
            'test_duration': test_duration,
            'memory_samples': memory_usage,
            'timestamp': datetime.now().isoformat()
        })

    async def test_cpu_exhaustion(self):
        """Test CPU exhaustion scenario"""
        print("    Starting CPU-intensive operations...")

        async def cpu_intensive_task():
            # CPU-bound computation
            result = 0
            for i in range(10**6):
                result += i * i
            return result

        start_time = time.time()
        cpu_usage = []

        # Monitor CPU usage
        def monitor_cpu():
            while not self.stop_testing:
                cpu_usage.append(self.process.cpu_percent())
                time.sleep(0.5)

        # Start monitoring in background
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()

        try:
            # Run CPU-intensive tasks
            tasks = [cpu_intensive_task() for _ in range(50)]
            await asyncio.gather(*tasks)

            # Make API calls during CPU stress
            api_start = time.time()
            await self.client.get("/api/strategies")
            api_response_time = time.time() - api_start

            print(f"    API response time under CPU stress: {api_response_time*1000:.2f}ms")

        except Exception as e:
            print(f"    ❌ CPU exhaustion test error: {str(e)}")

        finally:
            self.stop_testing = True
            monitor_thread.join()

        test_duration = time.time() - start_time
        avg_cpu = sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0
        max_cpu = max(cpu_usage) if cpu_usage else 0

        self.results['tests'].append({
            'type': 'cpu_exhaustion',
            'avg_cpu_usage': avg_cpu,
            'max_cpu_usage': max_cpu,
            'test_duration': test_duration,
            'cpu_samples': cpu_usage,
            'timestamp': datetime.now().isoformat()
        })

    async def test_connection_exhaustion(self):
        """Test connection pool exhaustion"""
        print("    Testing connection pool limits...")

        connections = []
        errors = 0
        successful = 0

        try:
            # Create many simultaneous connections
            for i in range(1000):
                try:
                    connector = aiohttp.TCPConnector(limit=None)
                    session = aiohttp.ClientSession(
                        base_url=self.base_url,
                        connector=connector
                    )
                    connections.append(session)

                    async with session.get("/api/strategies") as response:
                        if response.status == 200:
                            successful += 1
                        else:
                            errors += 1

                except Exception as e:
                    errors += 1
                    self.error_queue.put(('connection_exhaustion', str(e)))

                if errors > 100:  # Stop if too many errors
                    break

        finally:
            # Clean up connections
            for conn in connections:
                await conn.close()

        print(f"    Successful connections: {successful}")
        print(f"    Failed connections: {errors}")

        self.results['tests'].append({
            'type': 'connection_exhaustion',
            'successful_connections': successful,
            'failed_connections': errors,
            'success_rate': (successful / (successful + errors)) * 100 if (successful + errors) > 0 else 0,
            'timestamp': datetime.now().isoformat()
        })

    async def test_traffic_spike(self):
        """Test sudden traffic spike"""
        print("\n📊 Test 3: Sudden Traffic Spike")
        print("-" * 40)

        # Baseline measurement
        baseline_time = await self.measure_api_response_time()
        print(f"  📊 Baseline response time: {baseline_time*1000:.2f}ms")

        # Simulate traffic spike
        print("\n  🚀 Simulating traffic spike...")
        spike_levels = [
            (50, "Low spike"),
            (200, "Medium spike"),
            (500, "High spike"),
            (1000, "Extreme spike")
        ]

        for level, description in spike_levels:
            print(f"\n    Testing {description} ({level} concurrent requests)...")

            # Create spike
            tasks = [self.client.get("/api/strategies") for _ in range(level)]

            start_time = time.time()
            done, pending = await asyncio.wait(
                tasks,
                timeout=30,
                return_when=asyncio.ALL_COMPLETED
            )
            spike_time = time.time() - start_time

            # Cancel pending tasks
            for task in pending:
                task.cancel()

            # Calculate metrics
            successful = sum(1 for task in done if not task.exception())
            avg_response_time = spike_time / successful if successful > 0 else 0

            print(f"      ✅ Completed: {successful}/{level}")
            print(f"      ⏱️ Avg response time: {avg_response_time*1000:.2f}ms")
            print(f"      📈 Response time increase: {((avg_response_time/baseline_time)-1)*100:.1f}%")

            self.results['tests'].append({
                'type': 'traffic_spike',
                'spike_level': level,
                'description': description,
                'successful_requests': successful,
                'total_requests': level,
                'avg_response_time': avg_response_time,
                'baseline_response_time': baseline_time,
                'time_increase_percent': ((avg_response_time/baseline_time)-1)*100,
                'timestamp': datetime.now().isoformat()
            })

            # Wait for system to recover
            await asyncio.sleep(5)

    async def test_sustained_load(self):
        """Test sustained high load over time"""
        print("\n📊 Test 4: Sustained High Load")
        print("-" * 40)

        print("  Running sustained load for 10 minutes...")

        duration = 600  # 10 minutes
        concurrent_users = 200
        requests_per_second = 50

        metrics = {
            'response_times': [],
            'errors': [],
            'timestamps': [],
            'memory_usage': [],
            'cpu_usage': []
        }

        start_time = time.time()
        end_time = start_time + duration

        # Background monitoring
        def monitor_system():
            while time.time() < end_time:
                metrics['memory_usage'].append(self.process.memory_info().rss / 1024 / 1024)
                metrics['cpu_usage'].append(self.process.cpu_percent())
                time.sleep(5)

        monitor_thread = threading.Thread(target=monitor_system)
        monitor_thread.start()

        try:
            while time.time() < end_time:
                batch_start = time.time()

                # Create batch of requests
                tasks = [self.simulate_user_session(f"sustained_user_{int(time.time())}_{i}")
                        for i in range(concurrent_users)]

                # Wait for batch completion
                done, pending = await asyncio.wait(
                    tasks,
                    timeout=10,
                    return_when=asyncio.ALL_COMPLETED
                )

                # Cancel pending tasks
                for task in pending:
                    task.cancel()

                # Collect metrics
                batch_time = time.time() - batch_start
                successful = sum(1 for task in done if not task.exception())
                failed = len(tasks) - successful

                metrics['response_times'].append(batch_time / successful if successful > 0 else 0)
                metrics['errors'].append(failed)
                metrics['timestamps'].append(time.time() - start_time)

                # Rate limiting
                elapsed = time.time() - batch_start
                if elapsed < 1.0:
                    await asyncio.sleep(1.0 - elapsed)

        finally:
            monitor_thread.join()

        # Analyze results
        avg_response_time = sum(metrics['response_times']) / len(metrics['response_times'])
        max_response_time = max(metrics['response_times'])
        total_errors = sum(metrics['errors'])
        avg_memory = sum(metrics['memory_usage']) / len(metrics['memory_usage'])
        max_memory = max(metrics['memory_usage'])
        avg_cpu = sum(metrics['cpu_usage']) / len(metrics['cpu_usage'])
        max_cpu = max(metrics['cpu_usage'])

        print(f"\n  📊 Sustained Load Results:")
        print(f"    ⏱️ Avg response time: {avg_response_time*1000:.2f}ms")
        print(f"    ⚡ Max response time: {max_response_time*1000:.2f}ms")
        print(f"    ❌ Total errors: {total_errors}")
        print(f"    💾 Avg memory: {avg_memory:.2f}MB (Peak: {max_memory:.2f}MB)")
        print(f"    🔥 Avg CPU: {avg_cpu:.1f}% (Peak: {max_cpu:.1f}%)")

        self.results['tests'].append({
            'type': 'sustained_load',
            'duration_seconds': duration,
            'concurrent_users': concurrent_users,
            'avg_response_time': avg_response_time,
            'max_response_time': max_response_time,
            'total_errors': total_errors,
            'avg_memory_mb': avg_memory,
            'max_memory_mb': max_memory,
            'avg_cpu_usage': avg_cpu,
            'max_cpu_usage': max_cpu,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        })

    async def test_memory_under_stress(self):
        """Test memory behavior under stress"""
        print("\n📊 Test 5: Memory Leak Detection Under Stress")
        print("-" * 40)

        memory_snapshots = []
        iterations = 50

        for i in range(iterations):
            print(f"  🔍 Iteration {i+1}/{iterations}...")

            # Create memory pressure
            tasks = []
            for j in range(20):
                task = asyncio.create_task(
                    self.memory_stress_operation(f"mem_test_{i}_{j}")
                )
                tasks.append(task)

            # Wait for completion
            await asyncio.gather(*tasks, return_exceptions=True)

            # Force garbage collection
            import gc
            gc.collect()

            # Capture memory snapshot
            memory = self.process.memory_info().rss / 1024 / 1024
            memory_snapshots.append(memory)

            print(f"    💾 Memory: {memory:.2f}MB")

        # Analyze memory trend
        memory_trend = np.polyfit(range(len(memory_snapshots)), memory_snapshots, 1)[0]
        total_increase = memory_snapshots[-1] - memory_snapshots[0]

        print(f"\n  📈 Memory Analysis:")
        print(f"    Initial: {memory_snapshots[0]:.2f}MB")
        print(f"    Final: {memory_snapshots[-1]:.2f}MB")
        print(f"    Total increase: {total_increase:.2f}MB")
        print(f"    Trend per iteration: {memory_trend:.3f}MB")

        if memory_trend > 1:
            print("    ⚠️ Potential memory leak detected!")
        else:
            print("    ✅ No significant memory leak detected")

        self.results['tests'].append({
            'type': 'memory_stress_leak',
            'iterations': iterations,
            'initial_memory_mb': memory_snapshots[0],
            'final_memory_mb': memory_snapshots[-1],
            'total_increase_mb': total_increase,
            'trend_per_iteration_mb': memory_trend,
            'memory_snapshots': memory_snapshots,
            'leak_detected': memory_trend > 1,
            'timestamp': datetime.now().isoformat()
        })

    async def simulate_user_session(self, user_id: str):
        """Simulate a complete user session"""
        try:
            # Login
            async with self.client.post("/api/auth/login", json={
                "username": user_id,
                "password": "test123"
            }) as response:
                if response.status != 200:
                    return False
                token = await response.json()

            # Use token for authenticated requests
            headers = {'Authorization': f'Bearer {token.get("access_token")}'}

            # User operations
            operations = [
                self.client.get("/api/strategies", headers=headers),
                self.client.get("/api/monitoring/performance", headers=headers),
                self.client.get("/api/portfolio/summary", headers=headers),
                self.client.get("/api/trades/active", headers=headers)
            ]

            # Randomly execute operations
            for op in random.sample(operations, random.randint(1, len(operations))):
                async with op as response:
                    if response.status >= 400:
                        return False

            return True

        except Exception as e:
            self.error_queue.put(('user_session', str(e)))
            return False

    async def memory_stress_operation(self, operation_id: str):
        """Perform memory-intensive operation"""
        # Create temporary data structures
        data = []
        for i in range(100):
            data.append({
                'id': f"{operation_id}_{i}",
                'data': np.random.random((100, 100)).tolist(),
                'metadata': {
                    'timestamp': time.time(),
                    'random_value': random.random()
                }
            })

        # Simulate processing
        await asyncio.sleep(0.1)

        # Data will be garbage collected when function exits
        return len(data)

    async def measure_api_response_time(self, url: str = "/api/strategies") -> float:
        """Measure average API response time"""
        times = []
        for _ in range(10):
            start = time.time()
            async with self.client.get(url) as response:
                await response.text()
            times.append(time.time() - start)

        return sum(times) / len(times)

    async def client(self, method: str, url: str, **kwargs):
        """HTTP client wrapper"""
        async with aiohttp.ClientSession() as session:
            async with getattr(session, method.lower())(url, **kwargs) as response:
                return response

    def generate_stress_report(self):
        """Generate comprehensive stress test report"""
        print("\n📊 Generating Stress Test Report\n")

        # Collect errors
        errors = []
        while not self.error_queue.empty():
            errors.append(self.error_queue.get())

        # Generate summary
        self.results['summary'] = {
            'total_tests': len(self.results['tests']),
            'errors_detected': len(errors),
            'test_completion': datetime.now().isoformat(),
            'recommendations': self.generate_recommendations()
        }

        # Save report
        with open('stress-test-results.json', 'w') as f:
            json.dump(self.results, f, indent=2)

        # Create visualizations
        self.create_stress_visualizations()

        # Print summary
        self.print_stress_summary()

    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        for test in self.results['tests']:
            if test['type'] == 'max_concurrent_users':
                if test['success_rate'] < 90:
                    recommendations.append(
                        "Consider implementing connection pooling and load balancing "
                        "to handle higher concurrent user loads"
                    )

            elif test['type'] == 'memory_exhaustion':
                if test['peak_memory_mb'] > 1500:
                    recommendations.append(
                        "Memory usage exceeded 1.5GB. Implement memory optimization "
                        "strategies such as streaming responses and data pagination"
                    )

            elif test['type'] == 'cpu_exhaustion':
                if test['max_cpu_usage'] > 90:
                    recommendations.append(
                        "CPU usage peaked above 90%. Consider implementing task queues "
                        "and async processing for CPU-intensive operations"
                    )

            elif test['type'] == 'traffic_spike':
                if any(t['time_increase_percent'] > 500 for t in self.results['tests']
                      if t['type'] == 'traffic_spike'):
                    recommendations.append(
                        "Response times increased significantly during traffic spikes. "
                        "Implement caching and auto-scaling mechanisms"
                    )

            elif test['type'] == 'memory_stress_leak' and test['leak_detected']:
                recommendations.append(
                    "Potential memory leak detected. Review object lifecycle management "
                    "and ensure proper cleanup of resources"
                )

        return recommendations

    def create_stress_visualizations(self):
        """Create stress test visualizations"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Stress Test Results', fontsize=16)

        # Plot 1: Concurrent Users Success Rate
        concurrent_tests = [t for t in self.results['tests'] if t['type'] == 'max_concurrent_users']
        if concurrent_tests:
            users = [t['concurrent_users'] for t in concurrent_tests]
            success_rates = [t['success_rate'] for t in concurrent_tests]
            axes[0, 0].plot(users, success_rates, 'o-')
            axes[0, 0].set_title('Concurrent Users vs Success Rate')
            axes[0, 0].set_xlabel('Concurrent Users')
            axes[0, 0].set_ylabel('Success Rate (%)')
            axes[0, 0].grid(True)

        # Plot 2: Traffic Spike Response Times
        spike_tests = [t for t in self.results['tests'] if t['type'] == 'traffic_spike']
        if spike_tests:
            spike_levels = [t['spike_level'] for t in spike_tests]
            response_times = [t['avg_response_time'] * 1000 for t in spike_tests]
            axes[0, 1].bar(range(len(spike_levels)), response_times)
            axes[0, 1].set_title('Traffic Spike Response Times')
            axes[0, 1].set_xlabel('Spike Level')
            axes[0, 1].set_ylabel('Avg Response Time (ms)')
            axes[0, 1].set_xticks(range(len(spike_levels)))
            axes[0, 1].set_xticklabels([str(l) for l in spike_levels])

        # Plot 3: Memory Usage Over Time
        memory_test = next((t for t in self.results['tests'] if t['type'] == 'sustained_load'), None)
        if memory_test and 'metrics' in memory_test:
            metrics = memory_test['metrics']
            time_points = range(len(metrics['memory_usage']))
            axes[0, 2].plot(time_points, metrics['memory_usage'])
            axes[0, 2].set_title('Memory Usage During Sustained Load')
            axes[0, 2].set_xlabel('Time (5s intervals)')
            axes[0, 2].set_ylabel('Memory Usage (MB)')
            axes[0, 2].grid(True)

        # Plot 4: CPU Usage Over Time
        if memory_test and 'metrics' in memory_test:
            metrics = memory_test['metrics']
            time_points = range(len(metrics['cpu_usage']))
            axes[1, 0].plot(time_points, metrics['cpu_usage'], color='orange')
            axes[1, 0].set_title('CPU Usage During Sustained Load')
            axes[1, 0].set_xlabel('Time (5s intervals)')
            axes[1, 0].set_ylabel('CPU Usage (%)')
            axes[1, 0].grid(True)

        # Plot 5: Memory Leak Detection
        leak_test = next((t for t in self.results['tests'] if t['type'] == 'memory_stress_leak'), None)
        if leak_test:
            iterations = range(len(leak_test['memory_snapshots']))
            memory_snapshots = leak_test['memory_snapshots']
            axes[1, 1].plot(iterations, memory_snapshots, color='red')
            axes[1, 1].set_title('Memory Leak Detection')
            axes[1, 1].set_xlabel('Iteration')
            axes[1, 1].set_ylabel('Memory Usage (MB)')
            axes[1, 1].grid(True)

            # Add trend line
            trend = np.polyfit(iterations, memory_snapshots, 1)
            trend_line = np.polyval(trend, iterations)
            axes[1, 1].plot(iterations, trend_line, '--', color='black', label='Trend')
            axes[1, 1].legend()

        # Plot 6: Error Rate Over Time
        if memory_test and 'metrics' in memory_test:
            metrics = memory_test['metrics']
            time_points = range(len(metrics['errors']))
            axes[1, 2].plot(time_points, metrics['errors'], color='red')
            axes[1, 2].set_title('Error Rate During Sustained Load')
            axes[1, 2].set_xlabel('Time (1s intervals)')
            axes[1, 2].set_ylabel('Errors per Batch')
            axes[1, 2].grid(True)

        plt.tight_layout()
        plt.savefig('stress-test-charts.png', dpi=300, bbox_inches='tight')
        plt.close()

        print("📈 Stress test visualizations saved to: stress-test-charts.png")

    def print_stress_summary(self):
        """Print stress test summary"""
        print("="*60)
        print("🔥 STRESS TEST SUMMARY")
        print("="*60)

        print(f"\n📊 Tests Completed: {self.results['summary']['total_tests']}")
        print(f"❌ Errors Detected: {self.results['summary']['errors_detected']}")
        print(f"📅 Completion Time: {self.results['summary']['test_completion']}")

        # Key findings
        print("\n🎯 Key Findings:")
        print("-" * 20)

        # Max concurrent users
        concurrent_tests = [t for t in self.results['tests'] if t['type'] == 'max_concurrent_users']
        if concurrent_tests:
            max_successful = max(t['concurrent_users'] for t in concurrent_tests if t['success_rate'] >= 90)
            print(f"👥 Max Concurrent Users Supported: {max_successful}")

        # Performance degradation
        spike_tests = [t for t in self.results['tests'] if t['type'] == 'traffic_spike']
        if spike_tests:
            max_degradation = max(t['time_increase_percent'] for t in spike_tests)
            print(f"📈 Max Response Time Degradation: {max_degradation:.1f}%")

        # Resource usage
        sustained_test = next((t for t in self.results['tests'] if t['type'] == 'sustained_load'), None)
        if sustained_test:
            print(f"💾 Peak Memory Usage: {sustained_test['max_memory_mb']:.2f}MB")
            print(f"🔥 Peak CPU Usage: {sustained_test['max_cpu_usage']:.1f}%")

        # Recommendations
        if self.results['summary']['recommendations']:
            print("\n💡 Recommendations:")
            print("-" * 20)
            for i, rec in enumerate(self.results['summary']['recommendations'], 1):
                print(f"{i}. {rec}")

        print(f"\n📄 Detailed report saved to: stress-test-results.json")


async def main():
    """Main stress test runner"""
    # Create test instance
    test = StressTest()

    # Run tests
    try:
        await test.run_stress_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️ Stress tests interrupted by user")
        test.stop_testing = True
    except Exception as e:
        print(f"\n\n❌ Stress tests failed with error: {str(e)}")
        test.stop_testing = True


if __name__ == "__main__":
    # Run stress tests
    asyncio.run(main())
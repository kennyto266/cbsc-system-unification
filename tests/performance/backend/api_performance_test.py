"""
Backend API Performance Tests
Tests API response times, throughput, and resource usage
"""

import pytest
import asyncio
import time
import requests
import concurrent.futures
import psutil
import threading
from datetime import datetime
import json
import statistics
from typing import List, Dict, Any

# API base URL
API_BASE_URL = "http://localhost:3004"

class APIPerformanceTest:
    """API Performance Testing Framework"""

    def __init__(self):
        self.metrics = {
            response_times: [],
            throughput_data: [],
            error_rates: [],
            resource_usage: []
        }
        self.test_running = False

    async def measure_endpoint_performance(
        self,
        endpoint: str,
        method: str = "GET",
        payload: Dict = None,
        headers: Dict = None
    ) -> Dict[str, Any]:
        """Measure single endpoint performance"""
        url = f"{API_BASE_URL}{endpoint}"

        start_time = time.perf_counter()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=payload, headers=headers, timeout=30)
            elif method == "PUT":
                response = requests.put(url, json=payload, headers=headers, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)

            end_time = time.perf_counter()
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024  # MB

            return {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "response_time": (end_time - start_time) * 1000,  # ms
                "response_size": len(response.content),
                "memory_usage": memory_after - memory_before,
                "success": response.status_code < 400
            }

        except Exception as e:
            end_time = time.perf_counter()
            return {
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "response_time": (end_time - start_time) * 1000,
                "response_size": 0,
                "memory_usage": 0,
                "success": False,
                "error": str(e)
            }

    async def run_concurrent_requests(
        self,
        endpoint: str,
        concurrent_users: int = 10,
        requests_per_user: int = 5,
        delay_between_requests: float = 0.1
    ) -> Dict[str, Any]:
        """Run concurrent requests to test throughput"""

        def make_request(user_id: int, request_id: int):
            """Single request by a user"""
            return asyncio.run(
                self.measure_endpoint_performance(endpoint)
            )

        # Track start time
        test_start_time = time.perf_counter()

        # Execute concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []

            for user_id in range(concurrent_users):
                for request_id in range(requests_per_user):
                    future = executor.submit(make_request, user_id, request_id)
                    futures.append(future)

                    # Add delay between requests
                    time.sleep(delay_between_requests)

            # Collect results
            results = []
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)

        test_end_time = time.perf_counter()
        total_test_time = test_end_time - test_start_time

        # Calculate metrics
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]

        response_times = [r["response_time"] for r in successful_requests]

        return {
            "endpoint": endpoint,
            "concurrent_users": concurrent_users,
            "requests_per_user": requests_per_user,
            "total_requests": len(results),
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "error_rate": (len(failed_requests) / len(results)) * 100,
            "test_duration": total_test_time,
            "requests_per_second": len(results) / total_test_time,
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "median_response_time": statistics.median(response_times) if response_times else 0,
            "p95_response_time": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "errors": failed_requests
        }

    async def run_load_test(
        self,
        duration_seconds: int = 60,
        ramp_up_seconds: int = 10,
        max_users: int = 50
    ) -> Dict[str, Any]:
        """Run sustained load test"""

        endpoints_to_test = [
            "/api/strategies",
            "/api/strategies/1/performance",
            "/api/market/data/BTC/USDT"
        ]

        metrics = []
        start_time = time.perf_counter()
        user_threads = []

        def simulate_user_load(user_id: int):
            """Simulate a user making requests"""
            request_count = 0
            while self.test_running:
                endpoint = endpoints_to_test[request_count % len(endpoints_to_test)]

                result = asyncio.run(
                    self.measure_endpoint_performance(endpoint)
                )

                result["user_id"] = user_id
                result["timestamp"] = time.perf_counter() - start_time
                metrics.append(result)

                request_count += 1
                time.sleep(0.5)  # Request interval

        # Ramp up users gradually
        ramp_interval = ramp_up_seconds / max_users

        for i in range(max_users):
            thread = threading.Thread(target=simulate_user_load, args=(i + 1,))
            thread.daemon = True
            thread.start()
            user_threads.append(thread)
            time.sleep(ramp_interval)

        # Run for specified duration
        self.test_running = True
        time.sleep(duration_seconds)
        self.test_running = False

        # Wait for threads to finish
        for thread in user_threads:
            thread.join(timeout=5)

        # Analyze results
        total_requests = len(metrics)
        successful_requests = [m for m in metrics if m["success"]]

        # Group by time intervals (every 5 seconds)
        time_buckets = {}
        for metric in metrics:
            bucket = int(metric["timestamp"] / 5) * 5
            if bucket not in time_buckets:
                time_buckets[bucket] = []
            time_buckets[bucket].append(metric)

        # Calculate metrics per time bucket
        throughput_data = []
        for bucket, bucket_metrics in time_buckets.items():
            successful = [m for m in bucket_metrics if m["success"]]
            throughput = len(bucket_metrics) / 5  # requests per second

            throughput_data.append({
                "timestamp": bucket,
                "requests_per_second": throughput,
                "avg_response_time": statistics.mean([m["response_time"] for m in successful]) if successful else 0,
                "error_rate": (len(bucket_metrics) - len(successful)) / len(bucket_metrics) * 100
            })

        return {
            "test_duration": duration_seconds,
            "max_users": max_users,
            "total_requests": total_requests,
            "successful_requests": len(successful_requests),
            "error_rate": (total_requests - len(successful_requests)) / total_requests * 100,
            "avg_requests_per_second": total_requests / duration_seconds,
            "throughput_data": throughput_data,
            "performance_summary": {
                "avg_response_time": statistics.mean([m["response_time"] for m in successful_requests]) if successful_requests else 0,
                "p95_response_time": statistics.quantiles([m["response_time"] for m in successful_requests], n=20)[18] if len(successful_requests) >= 20 else 0,
                "max_response_time": max([m["response_time"] for m in successful_requests]) if successful_requests else 0
            }
        }

    async def run_stress_test(
        self,
        max_users: int = 100,
        step_size: int = 10,
        step_duration: int = 30
    ) -> Dict[str, Any]:
        """Run stress test to find breaking point"""

        results = []
        breaking_point = None

        for current_users in range(step_size, max_users + 1, step_size):
            print(f"Testing with {current_users} concurrent users...")

            result = await self.run_concurrent_requests(
                endpoint="/api/strategies",
                concurrent_users=current_users,
                requests_per_user=5,
                delay_between_requests=0.01  # Minimal delay for stress test
            )

            result["concurrent_users_tested"] = current_users
            results.append(result)

            # Check if we've reached breaking point
            if result["error_rate"] > 10 or result["avg_response_time"] > 5000:
                breaking_point = current_users
                break

            # Rest between test steps
            time.sleep(5)

        return {
            "max_users_tested": max_users,
            "breaking_point": breaking_point,
            "step_results": results,
            "recommendations": self._generate_stress_test_recommendations(breaking_point, results)
        }

    def _generate_stress_test_recommendations(self, breaking_point, results):
        """Generate recommendations based on stress test results"""
        recommendations = []

        if breaking_point:
            recommendations.append(
                f"System starts degrading at {breaking_point} concurrent users. "
                "Consider implementing rate limiting or auto-scaling."
            )

        # Check response time trends
        if len(results) > 1:
            response_times = [r["avg_response_time"] for r in results]
            if response_times[-1] > response_times[0] * 2:
                recommendations.append(
                    "Response times increase significantly under load. "
                    "Consider optimizing database queries and implementing caching."
                )

        # Check error rates
        high_error_results = [r for r in results if r["error_rate"] > 5]
        if high_error_results:
            recommendations.append(
                "High error rates detected under load. "
                "Review error handling and implement circuit breakers."
            )

        if not recommendations:
            recommendations.append("System performs well under stress conditions.")

        return recommendations

    async def monitor_resource_usage(self, duration_seconds: int = 60) -> Dict[str, Any]:
        """Monitor system resource usage during API operations"""

        resource_data = []
        start_time = time.perf_counter()

        while time.perf_counter() - start_time < duration_seconds:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()

            resource_data.append({
                "timestamp": time.perf_counter() - start_time,
                "system_cpu_percent": cpu_percent,
                "system_memory_percent": memory.percent,
                "system_memory_used_gb": memory.used / (1024**3),
                "disk_usage_percent": disk.percent,
                "process_memory_mb": process_memory.rss / (1024**2),
                "process_cpu_percent": process_cpu,
                "process_threads": process.num_threads(),
                "process_open_files": process.num_fds() if hasattr(process, 'num_fds') else 0
            })

        return {
            "duration": duration_seconds,
            "data_points": len(resource_data),
            "peak_cpu": max(r["system_cpu_percent"] for r in resource_data),
            "avg_cpu": statistics.mean(r["system_cpu_percent"] for r in resource_data),
            "peak_memory": max(r["system_memory_percent"] for r in resource_data),
            "avg_memory": statistics.mean(r["system_memory_percent"] for r in resource_data),
            "peak_process_memory": max(r["process_memory_mb"] for r in resource_data),
            "resource_timeline": resource_data
        }

# Test execution
@pytest.mark.asyncio
async def test_api_endpoint_performance():
    """Test individual API endpoint performance"""
    perf_test = APIPerformanceTest()

    # Test key endpoints
    endpoints = [
        ("/api/strategies", "GET"),
        ("/api/strategies/1/performance", "GET"),
        ("/api/market/data/BTC/USDT", "GET")
    ]

    results = {}
    for endpoint, method in endpoints:
        print(f"Testing {method} {endpoint}...")

        # Run multiple requests and average
        measurements = []
        for _ in range(10):
            measurement = await perf_test.measure_endpoint_performance(endpoint, method)
            measurements.append(measurement)
            time.sleep(0.1)

        successful_measurements = [m for m in measurements if m["success"]]

        if successful_measurements:
            results[endpoint] = {
                "method": method,
                "avg_response_time": statistics.mean(m["response_time"] for m in successful_measurements),
                "p95_response_time": statistics.quantiles([m["response_time"] for m in successful_measurements], n=20)[18],
                "success_rate": len(successful_measurements) / len(measurements) * 100
            }
        else:
            results[endpoint] = {
                "method": method,
                "error": "All requests failed"
            }

    print("Endpoint Performance Results:")
    for endpoint, result in results.items():
        print(f"{result['method']} {endpoint}: {result.get('avg_response_time', 'N/A'):.2f}ms avg")

    # Assertions
    for endpoint, result in results.items():
        if "avg_response_time" in result:
            assert result["avg_response_time"] < 1000, f"{endpoint} response time too high"
            assert result["success_rate"] > 95, f"{endpoint} success rate too low"

@pytest.mark.asyncio
async def test_concurrent_user_load():
    """Test API performance under concurrent load"""
    perf_test = APIPerformanceTest()

    print("Running concurrent user load test...")
    result = await perf_test.run_concurrent_requests(
        endpoint="/api/strategies",
        concurrent_users=20,
        requests_per_user=10
    )

    print(f"Total requests: {result['total_requests']}")
    print(f"Success rate: {100 - result['error_rate']:.2f}%")
    print(f"Avg response time: {result['avg_response_time']:.2f}ms")
    print(f"Requests per second: {result['requests_per_second']:.2f}")

    # Performance assertions
    assert result["error_rate"] < 5, "Error rate too high under load"
    assert result["avg_response_time"] < 2000, "Average response time too high under load"
    assert result["requests_per_second"] > 10, "Throughput too low"

@pytest.mark.asyncio
@pytest.mark.slow
async def test_sustained_load():
    """Test API performance under sustained load"""
    perf_test = APIPerformanceTest()

    print("Running sustained load test (60 seconds)...")
    result = await perf_test.run_load_test(
        duration_seconds=60,
        max_users=30
    )

    print(f"Sustained load results:")
    print(f"  Total requests: {result['total_requests']}")
    print(f"  Error rate: {result['error_rate']:.2f}%")
    print(f"  Avg RPS: {result['avg_requests_per_second']:.2f}")
    print(f"  Avg response time: {result['performance_summary']['avg_response_time']:.2f}ms")

    # Sustained load assertions
    assert result["error_rate"] < 2, "Error rate too high under sustained load"
    assert result["performance_summary"]["avg_response_time"] < 1500, "Response time degradation too high"

@pytest.mark.asyncio
@pytest.mark.slow
async def test_api_stress():
    """Find API breaking point"""
    perf_test = APIPerformanceTest()

    print("Running stress test...")
    result = await perf_test.run_stress_test(
        max_users=100,
        step_size=20
    )

    print(f"Stress test results:")
    print(f"  Breaking point: {result['breaking_point'] or 'Not found'} users")
    print(f"  Recommendations: {len(result['recommendations'])}")

    for rec in result['recommendations']:
        print(f"    - {rec}")

    # Stress test should identify breaking point or handle max users
    assert result["breaking_point"] is None or result["breaking_point"] > 50, \
        "Breaking point too low - system needs optimization"

if __name__ == "__main__":
    import asyncio

    async def run_all_performance_tests():
        print("=== API Performance Testing ===\n")

        try:
            await test_api_endpoint_performance()
            print("\n" + "="*50 + "\n")

            await test_concurrent_user_load()
            print("\n" + "="*50 + "\n")

            await test_sustained_load()
            print("\n" + "="*50 + "\n")

            await test_api_stress()
            print("\n=== Performance Testing Complete ===")

        except Exception as e:
            print(f"Performance testing failed: {e}")
            raise

    asyncio.run(run_all_performance_tests())
"""
Backend API Performance Tests
Tests API response times, throughput, and resource usage
"""

import asyncio
import aiohttp
import time
import statistics
import json
import sys
import psutil
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configure matplotlib for non-interactive use
plt.switch_backend('Agg')

class APIPerformanceTest:
    def __init__(self, base_url: str = "http://localhost:3003"):
        self.base_url = base_url
        self.results = {
            'test_cases': [],
            'summary': {},
            'system_metrics': []
        }
        self.process = psutil.Process()

    async def run_all_tests(self):
        """Run comprehensive API performance tests"""
        print("🚀 Starting API Performance Tests\n")

        # Test endpoints
        test_endpoints = [
            ('/api/strategies', 'GET', 'Get strategies list'),
            ('/api/strategies', 'POST', 'Create strategy'),
            ('/api/strategies/1', 'GET', 'Get single strategy'),
            ('/api/strategies/1', 'PUT', 'Update strategy'),
            ('/api/strategies/1/execute', 'POST', 'Execute strategy'),
            ('/api/monitoring/performance', 'GET', 'Get performance metrics'),
            ('/api/users/me', 'GET', 'Get current user'),
            ('/api/backtest/run', 'POST', 'Run backtest')
        ]

        for endpoint, method, description in test_endpoints:
            print(f"📊 Testing: {description}")
            await self.test_endpoint(endpoint, method, description)
            await asyncio.sleep(1)  # Brief pause between tests

        # Generate report
        self.generate_report()

    async def test_endpoint(self, endpoint: str, method: str, description: str):
        """Test individual endpoint performance"""
        url = f"{self.base_url}{endpoint}"
        response_times = []
        success_count = 0
        error_count = 0
        status_codes = {}

        # Capture initial system metrics
        initial_metrics = self.get_system_metrics()

        # Run requests
        num_requests = 100
        concurrent_requests = 10

        print(f"  🔨 Running {num_requests} requests with {concurrent_requests} concurrent...")

        semaphore = asyncio.Semaphore(concurrent_requests)

        async def make_request():
            async with semaphore:
                try:
                    start_time = time.time()
                    async with aiohttp.ClientSession() as session:
                        if method == 'GET':
                            async with session.get(url) as response:
                                await response.text()
                                end_time = time.time()
                                return {
                                    'response_time': end_time - start_time,
                                    'status_code': response.status,
                                    'success': 200 <= response.status < 400
                                }
                        elif method == 'POST':
                            # Create sample payload for POST requests
                            payload = self.get_sample_payload(endpoint)
                            async with session.post(url, json=payload) as response:
                                await response.text()
                                end_time = time.time()
                                return {
                                    'response_time': end_time - start_time,
                                    'status_code': response.status,
                                    'success': 200 <= response.status < 400
                                }
                        elif method == 'PUT':
                            payload = self.get_sample_payload(endpoint)
                            async with session.put(url, json=payload) as response:
                                await response.text()
                                end_time = time.time()
                                return {
                                    'response_time': end_time - start_time,
                                    'status_code': response.status,
                                    'success': 200 <= response.status < 400
                                }
                except Exception as e:
                    return {
                        'response_time': -1,
                        'status_code': 0,
                        'success': False,
                        'error': str(e)
                    }

        # Execute requests concurrently
        tasks = [make_request() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)

        # Process results
        for result in results:
            if result['success']:
                success_count += 1
                response_times.append(result['response_time'])
            else:
                error_count += 1

            status_code = result['status_code']
            status_codes[status_code] = status_codes.get(status_code, 0) + 1

        # Capture final system metrics
        final_metrics = self.get_system_metrics()

        # Calculate statistics
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
            min_time = min(response_times)
            max_time = max(response_times)
        else:
            avg_time = median_time = p95_time = p99_time = min_time = max_time = 0

        # Store results
        test_result = {
            'endpoint': endpoint,
            'method': method,
            'description': description,
            'total_requests': num_requests,
            'success_count': success_count,
            'error_count': error_count,
            'success_rate': (success_count / num_requests) * 100,
            'response_times': {
                'avg': avg_time,
                'median': median_time,
                'p95': p95_time,
                'p99': p99_time,
                'min': min_time,
                'max': max_time
            },
            'status_codes': status_codes,
            'throughput': success_count / sum(response_times) if response_times else 0,
            'system_metrics': {
                'cpu_diff': final_metrics['cpu'] - initial_metrics['cpu'],
                'memory_diff': final_metrics['memory'] - initial_metrics['memory']
            }
        }

        self.results['test_cases'].append(test_result)

        # Print results
        print(f"  ✅ Success rate: {test_result['success_rate']:.1f}%")
        print(f"  ⏱️ Avg response time: {avg_time*1000:.2f}ms")
        print(f"  📈 P95 response time: {p95_time*1000:.2f}ms")
        print(f"  🚀 Throughput: {test_result['throughput']:.2f} req/s\n")

    def get_sample_payload(self, endpoint: str) -> Dict[str, Any]:
        """Generate sample payload for POST/PUT requests"""
        if 'strategies' in endpoint:
            return {
                "name": "Test Strategy",
                "description": "Performance test strategy",
                "type": "momentum",
                "parameters": {
                    "lookback_period": 20,
                    "threshold": 0.02
                }
            }
        elif 'backtest' in endpoint:
            return {
                "strategy_id": 1,
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "initial_capital": 100000
            }
        return {}

    def get_system_metrics(self) -> Dict[str, float]:
        """Capture current system metrics"""
        return {
            'cpu': self.process.cpu_percent(),
            'memory': self.process.memory_info().rss / 1024 / 1024,  # MB
            'timestamp': datetime.now().isoformat()
        }

    def generate_report(self):
        """Generate performance test report"""
        print("📊 Generating Performance Report\n")

        # Calculate summary statistics
        all_avg_times = [tc['response_times']['avg'] for tc in self.results['test_cases']]
        all_p95_times = [tc['response_times']['p95'] for tc in self.results['test_cases']]
        all_success_rates = [tc['success_rate'] for tc in self.results['test_cases']]

        self.results['summary'] = {
            'total_endpoints_tested': len(self.results['test_cases']),
            'avg_response_time': statistics.mean(all_avg_times) if all_avg_times else 0,
            'p95_response_time': statistics.mean(all_p95_times) if all_p95_times else 0,
            'avg_success_rate': statistics.mean(all_success_rates) if all_success_rates else 0,
            'test_timestamp': datetime.now().isoformat()
        }

        # Save detailed results
        with open('api-performance-results.json', 'w') as f:
            json.dump(self.results, f, indent=2)

        # Generate visualizations
        self.create_visualizations()

        # Print summary
        self.print_summary()

    def create_visualizations(self):
        """Create performance visualization charts"""
        # Prepare data
        df_data = []
        for tc in self.results['test_cases']:
            df_data.append({
                'Endpoint': tc['description'],
                'Method': tc['method'],
                'Avg Time (ms)': tc['response_times']['avg'] * 1000,
                'P95 Time (ms)': tc['response_times']['p95'] * 1000,
                'Success Rate (%)': tc['success_rate'],
                'Throughput (req/s)': tc['throughput']
            })

        df = pd.DataFrame(df_data)

        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('API Performance Test Results', fontsize=16)

        # Response times chart
        sns.barplot(data=df, x='Avg Time (ms)', y='Endpoint', ax=axes[0, 0])
        axes[0, 0].set_title('Average Response Times')
        axes[0, 0].set_xlabel('Response Time (ms)')

        # P95 response times
        sns.barplot(data=df, x='P95 Time (ms)', y='Endpoint', ax=axes[0, 1])
        axes[0, 1].set_title('95th Percentile Response Times')
        axes[0, 1].set_xlabel('P95 Response Time (ms)')

        # Success rates
        sns.barplot(data=df, x='Success Rate (%)', y='Endpoint', ax=axes[1, 0])
        axes[1, 0].set_title('Success Rates')
        axes[1, 0].set_xlabel('Success Rate (%)')
        axes[1, 0].set_xlim(0, 100)

        # Throughput
        sns.barplot(data=df, x='Throughput (req/s)', y='Endpoint', ax=axes[1, 1])
        axes[1, 1].set_title('Request Throughput')
        axes[1, 1].set_xlabel('Throughput (requests/second)')

        # Adjust layout
        plt.tight_layout()
        plt.savefig('api-performance-charts.png', dpi=300, bbox_inches='tight')
        plt.close()

        print("📈 Visualization saved to: api-performance-charts.png")

    def print_summary(self):
        """Print performance test summary"""
        print("="*50)
        print("📊 API PERFORMANCE TEST SUMMARY")
        print("="*50)
        print(f"🔗 Endpoints tested: {self.results['summary']['total_endpoints_tested']}")
        print(f"⏱️ Average response time: {self.results['summary']['avg_response_time']*1000:.2f}ms")
        print(f"📈 P95 response time: {self.results['summary']['p95_response_time']*1000:.2f}ms")
        print(f"✅ Average success rate: {self.results['summary']['avg_success_rate']:.1f}%")
        print(f"📅 Test completed: {self.results['summary']['test_timestamp']}\n")

        # Performance targets check
        print("🎯 Performance Targets Check:")
        print("-" * 30)

        targets_met = 0
        total_targets = 0

        for tc in self.results['test_cases']:
            endpoint_name = tc['description']
            avg_time = tc['response_times']['avg'] * 1000
            p95_time = tc['response_times']['p95'] * 1000
            success_rate = tc['success_rate']

            # Check targets
            avg_target = avg_time < 200
            p95_target = p95_time < 500
            success_target = success_rate > 95

            if avg_target:
                targets_met += 1
            total_targets += 1
            if p95_target:
                targets_met += 1
            total_targets += 1
            if success_target:
                targets_met += 1
            total_targets += 1

            status = "✅" if (avg_target and p95_target and success_target) else "⚠️"
            print(f"{status} {endpoint_name}:")
            print(f"   Avg: {avg_time:.2f}ms {'✓' if avg_target else '✗'}")
            print(f"   P95: {p95_time:.2f}ms {'✓' if p95_target else '✗'}")
            print(f"   Success: {success_rate:.1f}% {'✓' if success_target else '✗'}")
            print()

        target_percentage = (targets_met / total_targets) * 100 if total_targets > 0 else 0
        print(f"📊 Overall Target Achievement: {target_percentage:.1f}%")

        # Recommendations
        print("\n💡 Recommendations:")
        print("-" * 20)

        slow_endpoints = [tc for tc in self.results['test_cases']
                         if tc['response_times']['avg'] * 1000 > 200]
        if slow_endpoints:
            print("🐌 Slow endpoints detected. Consider:")
            print("   • Database query optimization")
            print("   • Implementing caching")
            print("   • Response payload reduction")

        low_success = [tc for tc in self.results['test_cases']
                      if tc['success_rate'] < 95]
        if low_success:
            print("\n❌ Low success rates detected. Check:")
            print("   • Error handling and logging")
            print("   • Rate limiting configuration")
            print("   • Server resource allocation")

        print("\n📄 Detailed results saved to: api-performance-results.json")


async def main():
    """Main test runner"""
    test = APIPerformanceTest()
    await test.run_all_tests()


if __name__ == "__main__":
    # Run tests
    asyncio.run(main())
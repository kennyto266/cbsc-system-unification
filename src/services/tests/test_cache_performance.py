"""
Cache Performance Test Suite
===========================

Comprehensive performance testing for multi-level cache system
including load testing, stress testing, and benchmarking.
"""

import asyncio
import json
import logging
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
import concurrent.futures
from collections import defaultdict

import aioredis
import pandas as pd
import numpy as np
import pytest
import psutil
import matplotlib.pyplot as plt
import seaborn as sns

from ..multi_cache_integration import (
    MultiLevelCacheManager,
    CacheTier,
    get_cache_manager
)
from ..influxdb_optimizer import QueryOptimizer
from ..data_sync_manager import DataSyncManager

logger = logging.getLogger(__name__)


class TestType(str, Enum):
    """Types of performance tests"""
    BASIC = "basic"
    LOAD = "load"
    STRESS = "stress"
    ENDURANCE = "endurance"
    SPIKE = "spike"
    CONCURRENCY = "concurrency"


@dataclass
class TestResult:
    """Performance test result"""
    test_name: str
    test_type: TestType
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    total_operations: int
    successful_operations: int
    failed_operations: int
    throughput_ops_per_sec: float
    avg_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_rate: float
    memory_usage_mb: float
    cache_hit_rate: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestConfig:
    """Test configuration"""
    name: str
    test_type: TestType
    num_operations: int
    concurrency: int
    data_size_bytes: int
    duration_seconds: int
    warmup_seconds: int
    read_ratio: float = 0.7  # 70% reads, 30% writes
    key_prefix: str = "test"
    value_pattern: str = "random"
    ttl_seconds: int = 3600
    tier_distribution: Dict[CacheTier, float] = field(default_factory=lambda: {
        CacheTier.L1_REALTIME: 0.3,
        CacheTier.L2_QUERIES: 0.3,
        CacheTier.L3_SESSION: 0.3,
        CacheTier.L4_ARCHIVE: 0.1
    })


class CachePerformanceTester:
    """
    Comprehensive cache performance testing suite
    """

    def __init__(
        self,
        cache_manager: Optional[MultiLevelCacheManager] = None,
        redis_url: str = "redis://localhost:6379/1",
        influx_url: str = "http://localhost:8086"
    ):
        self.cache_manager = cache_manager
        self.redis_url = redis_url
        self.influx_url = influx_url

        # Test state
        self.active_tests = {}
        self.test_results = []
        self.test_data = {}

        # Metrics collection
        self.response_times = defaultdict(list)
        self.operation_counts = defaultdict(int)

    async def initialize(self):
        """Initialize test environment"""
        if not self.cache_manager:
            self.cache_manager = await get_cache_manager()

        logger.info("Cache performance tester initialized")

    async def run_test_suite(
        self,
        configs: List[TestConfig],
        generate_report: bool = True
    ) -> List[TestResult]:
        """
        Run complete test suite

        Args:
            configs: List of test configurations
            generate_report: Whether to generate HTML report

        Returns:
            List of test results
        """
        logger.info(f"Starting test suite with {len(configs)} tests")

        all_results = []

        for config in configs:
            logger.info(f"Running test: {config.name}")

            # Run individual test
            result = await self.run_single_test(config)
            all_results.append(result)

            # Brief pause between tests
            await asyncio.sleep(2)

        # Generate report if requested
        if generate_report:
            await self.generate_performance_report(all_results)

        logger.info(f"Test suite completed: {len(all_results)} tests run")
        return all_results

    async def run_single_test(self, config: TestConfig) -> TestResult:
        """
        Run a single performance test

        Args:
            config: Test configuration

        Returns:
            Test result
        """
        logger.info(f"Starting {config.test_type.value} test: {config.name}")

        # Initialize test state
        test_id = f"{config.name}_{int(time.time())}"
        self.active_tests[test_id] = {
            'config': config,
            'start_time': datetime.now(),
            'metrics': defaultdict(list)
        }

        # Pre-generate test data
        test_data = await self._generate_test_data(config)
        self.test_data[test_id] = test_data

        # Warmup phase
        if config.warmup_seconds > 0:
            await self._warmup_phase(config, test_data)

        # Main test phase
        result = await self._execute_test(test_id, config, test_data)

        # Cleanup
        del self.active_tests[test_id]
        del self.test_data[test_id]

        logger.info(
            f"Test completed: {config.name} - "
            f"Throughput: {result.throughput_ops_per_sec:.2f} ops/s, "
            f"Hit rate: {result.cache_hit_rate:.2%}, "
            f"P95: {result.p95_response_time_ms:.2f}ms"
        )

        return result

    async def _generate_test_data(self, config: TestConfig) -> Dict:
        """Generate test data based on configuration"""
        test_data = {
            'keys': [],
            'values': [],
            'operations': []
        }

        # Generate keys
        for i in range(config.num_operations):
            key = f"{config.key_prefix}_{i}"
            test_data['keys'].append(key)

        # Generate values
        if config.value_pattern == "random":
            # Random binary data
            for _ in range(config.num_operations):
                size = config.data_size_bytes
                value = b'x' * size
                test_data['values'].append(value)
        elif config.value_pattern == "json":
            # JSON objects
            for i in range(config.num_operations):
                value = {
                    'id': i,
                    'data': 'x' * (config.data_size_bytes // 10),
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {'test': True}
                }
                test_data['values'].append(json.dumps(value))
        elif config.value_pattern == "timeseries":
            # Time series data
            for i in range(config.num_operations):
                value = pd.DataFrame({
                    'timestamp': pd.date_range(
                        start=datetime.now(),
                        periods=100,
                        freq='1s'
                    ),
                    'value': np.random.randn(100),
                    'volume': np.random.randint(100, 1000, 100)
                })
                test_data['values'].append(value)

        # Generate operation sequence
        num_reads = int(config.num_operations * config.read_ratio)
        num_writes = config.num_operations - num_reads

        reads = [('read', i) for i in random.sample(range(config.num_operations), num_reads)]
        writes = [('write', i) for i in random.sample(range(config.num_operations), num_writes)]

        test_data['operations'] = reads + writes
        random.shuffle(test_data['operations'])

        return test_data

    async def _warmup_phase(self, config: TestConfig, test_data: Dict):
        """Execute warmup phase"""
        logger.info(f"Warmup phase: {config.warmup_seconds} seconds")

        # Pre-populate cache with some data
        warmup_ops = min(1000, config.num_operations // 10)

        for i in range(warmup_ops):
            key = test_data['keys'][i]
            value = test_data['values'][i]
            tier = self._select_tier(config.tier_distribution)

            await self.cache_manager.set(
                key,
                value,
                tier,
                ttl_seconds=config.ttl_seconds
            )

            await asyncio.sleep(0.001)  # Small delay

        logger.info(f"Warmup completed: {warmup_ops} items cached")

    async def _execute_test(
        self,
        test_id: str,
        config: TestConfig,
        test_data: Dict
    ) -> TestResult:
        """Execute the main test phase"""
        start_time = time.time()
        test_start = datetime.now()

        # Initialize counters
        successful = 0
        failed = 0
        response_times = []

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(config.concurrency)

        async def execute_operation(op_type: str, index: int) -> float:
            async with semaphore:
                op_start = time.time()
                key = test_data['keys'][index]
                value = test_data['values'][index]

                try:
                    if op_type == 'read':
                        # Read operation
                        tier = self._select_tier(config.tier_distribution)
                        await self.cache_manager.get(key, tier=tier)
                    else:
                        # Write operation
                        tier = self._select_tier(config.tier_distribution)
                        await self.cache_manager.set(
                            key,
                            value,
                            tier,
                            ttl_seconds=config.ttl_seconds
                        )

                    return (time.time() - op_start) * 1000

                except Exception as e:
                    logger.warning(f"Operation failed: {e}")
                    return -1

        # Create tasks for operations
        tasks = []
        for op_type, index in test_data['operations']:
            task = execute_operation(op_type, index)
            tasks.append(task)

        # Execute operations with timeout
        if config.test_type == TestType.ENDURANCE:
            # Duration-based test
            end_time = start_time + config.duration_seconds

            async def run_with_timeout():
                completed = 0
                while time.time() < end_time:
                    # Process in batches
                    batch = tasks[completed:completed + config.concurrency]
                    batch_times = await asyncio.gather(*batch, return_exceptions=True)

                    for t in batch_times:
                        if isinstance(t, float) and t >= 0:
                            response_times.append(t)
                            successful += 1
                        else:
                            failed += 1

                    completed += len(batch)
                    await asyncio.sleep(0.01)  # Small delay

            await run_with_timeout()
        else:
            # Operation count-based test
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, float) and result >= 0:
                    response_times.append(result)
                    successful += 1
                else:
                    failed += 1

        # Calculate metrics
        end_time = time.time()
        duration = end_time - start_time

        # Get cache metrics
        cache_metrics = await self.cache_manager.get_metrics()
        overall_hit_rate = cache_metrics.get('overall', {}).get('overall_hit_rate', 0)

        # Get memory usage
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024

        # Calculate percentiles
        if response_times:
            avg_time = statistics.mean(response_times)
            p50 = statistics.median(response_times)
            p95 = np.percentile(response_times, 95)
            p99 = np.percentile(response_times, 99)
        else:
            avg_time = p50 = p95 = p99 = 0

        # Create result
        result = TestResult(
            test_name=config.name,
            test_type=config.test_type,
            start_time=test_start,
            end_time=datetime.now(),
            duration_seconds=duration,
            total_operations=successful + failed,
            successful_operations=successful,
            failed_operations=failed,
            throughput_ops_per_sec=(successful + failed) / duration,
            avg_response_time_ms=avg_time,
            p50_response_time_ms=p50,
            p95_response_time_ms=p95,
            p99_response_time_ms=p99,
            error_rate=failed / (successful + failed) if (successful + failed) > 0 else 0,
            memory_usage_mb=memory_mb,
            cache_hit_rate=overall_hit_rate,
            metadata={
                'config': config,
                'response_times': response_times[:1000]  # Keep sample
            }
        )

        self.test_results.append(result)
        return result

    def _select_tier(self, distribution: Dict[CacheTier, float]) -> CacheTier:
        """Select cache tier based on distribution"""
        rand = random.random()
        cumulative = 0

        for tier, prob in distribution.items():
            cumulative += prob
            if rand <= cumulative:
                return tier

        return CacheTier.L3_SESSION  # Default

    async def generate_performance_report(
        self,
        results: List[TestResult],
        output_file: str = "cache_performance_report.html"
    ):
        """Generate HTML performance report"""
        # Create dataframes for analysis
        df_data = []
        for result in results:
            df_data.append({
                'Test': result.test_name,
                'Type': result.test_type.value,
                'Throughput': result.throughput_ops_per_sec,
                'Avg Response (ms)': result.avg_response_time_ms,
                'P95 (ms)': result.p95_response_time_ms,
                'P99 (ms)': result.p99_response_time_ms,
                'Hit Rate (%)': result.cache_hit_rate * 100,
                'Error Rate (%)': result.error_rate * 100,
                'Memory (MB)': result.memory_usage_mb
            })

        df = pd.DataFrame(df_data)

        # Create HTML report
        html_content = self._create_html_report(df, results)

        # Write to file
        with open(output_file, 'w') as f:
            f.write(html_content)

        logger.info(f"Performance report generated: {output_file}")

    def _create_html_report(self, df: pd.DataFrame, results: List[TestResult]) -> str:
        """Create HTML report content"""
        # Generate plots
        plots = self._generate_plots(df)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cache Performance Report</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .plot {{ margin: 20px 0; }}
                .summary {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>Cache Performance Test Report</h1>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

            <div class="summary">
                <h2>Executive Summary</h2>
                <p>Total Tests Run: {len(results)}</p>
                <p>Average Throughput: {df['Throughput'].mean():.2f} ops/s</p>
                <p>Average P95 Response: {df['P95 (ms)'].mean():.2f}ms</p>
                <p>Average Hit Rate: {df['Hit Rate (%)'].mean():.2f}%</p>
            </div>

            <h2>Test Results</h2>
            {df.to_html(index=False)}

            <h2>Performance Visualizations</h2>
            {plots}

            <h2>Detailed Test Results</h2>
        """

        # Add detailed results
        for result in results:
            html += f"""
            <h3>{result.test_name}</h3>
            <ul>
                <li>Type: {result.test_type.value}</li>
                <li>Duration: {result.duration_seconds:.2f}s</li>
                <li>Operations: {result.total_operations} (Success: {result.successful_operations}, Failed: {result.failed_operations})</li>
                <li>Throughput: {result.throughput_ops_per_sec:.2f} ops/s</li>
                <li>Avg Response: {result.avg_response_time_ms:.2f}ms</li>
                <li>P95: {result.p95_response_time_ms:.2f}ms</li>
                <li>P99: {result.p99_response_time_ms:.2f}ms</li>
                <li>Cache Hit Rate: {result.cache_hit_rate:.2%}</li>
                <li>Error Rate: {result.error_rate:.2%}</li>
                <li>Memory Usage: {result.memory_usage_mb:.2f}MB</li>
            </ul>
            """

        html += """
        </body>
        </html>
        """

        return html

    def _generate_plots(self, df: pd.DataFrame) -> str:
        """Generate performance plots"""
        plots_html = ""

        # Throughput comparison
        fig1 = px.bar(
            df,
            x='Test',
            y='Throughput',
            color='Type',
            title='Throughput by Test'
        )
        plots_html += fig1.to_html(include_plotlyjs=False, div_id="throughput-plot")

        # Response time comparison
        fig2 = px.bar(
            df,
            x='Test',
            y=['Avg Response (ms)', 'P95 (ms)', 'P99 (ms)'],
            title='Response Times by Test',
            barmode='group'
        )
        plots_html += fig2.to_html(include_plotlyjs=False, div_id="response-time-plot")

        # Hit rate vs Throughput
        fig3 = px.scatter(
            df,
            x='Hit Rate (%)',
            y='Throughput',
            color='Type',
            size='Memory (MB)',
            title='Hit Rate vs Throughput'
        )
        plots_html += fig3.to_html(include_plotlyjs=False, div_id="hitrate-throughput-plot")

        return plots_html


# Standard test configurations
BASIC_TEST_CONFIG = TestConfig(
    name="basic_operations",
    test_type=TestType.BASIC,
    num_operations=1000,
    concurrency=10,
    data_size_bytes=1024,
    duration_seconds=30,
    warmup_seconds=5
)

LOAD_TEST_CONFIG = TestConfig(
    name="load_test",
    test_type=TestType.LOAD,
    num_operations=10000,
    concurrency=50,
    data_size_bytes=2048,
    duration_seconds=60,
    warmup_seconds=10
)

STRESS_TEST_CONFIG = TestConfig(
    name="stress_test",
    test_type=TestType.STRESS,
    num_operations=100000,
    concurrency=200,
    data_size_bytes=4096,
    duration_seconds=120,
    warmup_seconds=30
)

CONCURRENCY_TEST_CONFIG = TestConfig(
    name="concurrency_test",
    test_type=TestType.CONCURRENCY,
    num_operations=5000,
    concurrency=100,
    data_size_bytes=1024,
    duration_seconds=60,
    warmup_seconds=10
)

# Pytest fixtures
@pytest.fixture
async def cache_tester():
    """Pytest fixture for cache performance tester"""
    tester = CachePerformanceTester()
    await tester.initialize()
    yield tester
    # Cleanup
    if tester.cache_manager:
        await tester.cache_manager.shutdown()


# Test cases
@pytest.mark.asyncio
async def test_basic_performance(cache_tester):
    """Test basic cache performance"""
    result = await cache_tester.run_single_test(BASIC_TEST_CONFIG)

    assert result.throughput_ops_per_sec > 100  # Should handle at least 100 ops/s
    assert result.p95_response_time_ms < 100  # P95 should be under 100ms
    assert result.error_rate < 0.01  # Error rate should be under 1%


@pytest.mark.asyncio
async def test_cache_tiers_performance(cache_tester):
    """Test performance across different cache tiers"""
    tier_configs = [
        {CacheTier.L1_REALTIME: 1.0},
        {CacheTier.L2_QUERIES: 1.0},
        {CacheTier.L3_SESSION: 1.0},
        {CacheTier.L4_ARCHIVE: 1.0}
    ]

    results = []
    for tier_dist in tier_configs:
        config = TestConfig(
            name=f"tier_test_{list(tier_dist.keys())[0].value}",
            test_type=TestType.BASIC,
            num_operations=1000,
            concurrency=10,
            data_size_bytes=1024,
            duration_seconds=30,
            warmup_seconds=5,
            tier_distribution=tier_dist
        )
        result = await cache_tester.run_single_test(config)
        results.append(result)

    # L1 should be fastest
    l1_result = next(r for r in results if CacheTier.L1_REALTIME.value in r.test_name)
    l4_result = next(r for r in results if CacheTier.L4_ARCHIVE.value in r.test_name)

    assert l1_result.avg_response_time_ms < l4_result.avg_response_time_ms


@pytest.mark.asyncio
async def test_cache_hit_rate(cache_tester):
    """Test cache hit rates with different access patterns"""
    configs = [
        TestConfig(
            name="sequential_access",
            test_type=TestType.BASIC,
            num_operations=1000,
            concurrency=10,
            data_size_bytes=1024,
            duration_seconds=30,
            warmup_seconds=5,
            read_ratio=1.0  # 100% reads
        ),
        TestConfig(
            name="random_access",
            test_type=TestType.BASIC,
            num_operations=1000,
            concurrency=10,
            data_size_bytes=1024,
            duration_seconds=30,
            warmup_seconds=5,
            read_ratio=1.0  # 100% reads
        )
    ]

    results = []
    for config in configs:
        # Modify test data generation for each pattern
        result = await cache_tester.run_single_test(config)
        results.append(result)

    # Sequential access should have better hit rate
    sequential = next(r for r in results if 'sequential' in r.test_name)
    random = next(r for r in results if 'random' in r.test_name)

    assert sequential.cache_hit_rate >= random.cache_hit_rate


# CLI interface
async def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Cache Performance Tester")
    parser.add_argument("--redis", default="redis://localhost:6379/1", help="Redis URL")
    parser.add_argument("--influx", default="http://localhost:8086", help="InfluxDB URL")
    parser.add_argument("--test", choices=['basic', 'load', 'stress', 'all'], default='all', help="Test type")
    parser.add_argument("--output", default="cache_performance_report.html", help="Output report file")

    args = parser.parse_args()

    # Initialize tester
    tester = CachePerformanceTester(redis_url=args.redis, influx_url=args.influx)
    await tester.initialize()

    # Select tests
    if args.test == 'all':
        configs = [BASIC_TEST_CONFIG, LOAD_TEST_CONFIG, STRESS_TEST_CONFIG, CONCURRENCY_TEST_CONFIG]
    elif args.test == 'basic':
        configs = [BASIC_TEST_CONFIG]
    elif args.test == 'load':
        configs = [LOAD_TEST_CONFIG]
    elif args.test == 'stress':
        configs = [STRESS_TEST_CONFIG]

    # Run tests
    results = await tester.run_test_suite(configs, generate_report=True)

    # Print summary
    print("\nTest Summary:")
    for result in results:
        print(f"{result.test_name}: {result.throughput_ops_per_sec:.2f} ops/s, "
              f"P95: {result.p95_response_time_ms:.2f}ms, "
              f"Hit Rate: {result.cache_hit_rate:.2%}")

    # Cleanup
    await tester.cache_manager.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
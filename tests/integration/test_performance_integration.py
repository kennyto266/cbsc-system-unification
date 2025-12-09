"""Performance integration tests for Hong Kong quantitative trading system.

This module provides comprehensive performance testing including load testing,
stress testing, scalability testing, and performance benchmarking.
"""

import asyncio
import logging
import pytest
import time
import psutil
import gc
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd

# Import system components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.integration.system_integration import SystemIntegration, IntegrationConfig
from src.data_adapters.data_service import DataService
from src.agents.real_agents.real_quantitative_analyst import RealQuantitativeAnalyst
from src.agents.real_agents.real_quantitative_trader import RealQuantitativeTrader
from src.strategy_management.strategy_manager import StrategyManager
from src.monitoring.real_time_monitor import RealTimeMonitor

from tests.helpers.test_utils import TestDataGenerator, MockComponentFactory, PerformanceMeasurer


class TestLoadIntegration:
    """Test load integration."""
    
    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup test environment."""
        self.logger = logging.getLogger(__name__)
        self.data_generator = TestDataGenerator()
        self.mock_factory = MockComponentFactory()
        self.performance_measurer = PerformanceMeasurer()
        
        yield
    
    @pytest.mark.asyncio
    async def test_concurrent_data_processing(self):
        """Test concurrent data processing performance."""
        # Test parameters
        num_concurrent_tasks = 100
        data_size = 1000
        
        # Create test data
        test_data = self.data_generator.generate_market_data(
            symbol="00700.HK",
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            frequency="1min"
        )
        
        # Mock data processor
        async def process_data(data):
            await asyncio.sleep(0.001)  # Simulate processing time
            return {'processed': True, 'size': len(data)}
        
        # Performance measurement
        self.performance_measurer.start_measurement("concurrent_processing")
        
        # Create concurrent tasks
        tasks = []
        for i in range(num_concurrent_tasks):
            task = asyncio.create_task(process_data(test_data))
            tasks.append(task)
        
        # Execute tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # End measurement
        duration = self.performance_measurer.end_measurement("concurrent_processing")
        
        # Verify results
        assert len(results) == num_concurrent_tasks
        assert all(result['processed'] for result in results)
        
        # Performance metrics
        throughput = num_concurrent_tasks / duration
        avg_response_time = duration / num_concurrent_tasks
        
        # Performance assertions
        assert throughput > 50, f"Throughput {throughput:.2f} tasks/sec is too low"
        assert avg_response_time < 0.1, f"Average response time {avg_response_time:.4f}s is too high"
        
        self.logger.info(f"Concurrent processing performance:")
        self.logger.info(f"  Tasks: {num_concurrent_tasks}")
        self.logger.info(f"  Duration: {duration:.4f}s")
        self.logger.info(f"  Throughput: {throughput:.2f} tasks/sec")
        self.logger.info(f"  Avg response time: {avg_response_time:.4f}s")
    
    @pytest.mark.asyncio
    async def test_high_frequency_data_processing(self):
        """Test high-frequency data processing performance."""
        # Test parameters
        num_data_points = 10000
        processing_interval = 0.001  # 1ms
        
        # Create high-frequency test data
        timestamps = [datetime.now() - timedelta(seconds=i) for i in range(num_data_points)]
        test_data = [
            {
                'timestamp': ts,
                'symbol': '00700.HK',
                'price': 300.0 + np.random.normal(0, 0.1),
                'volume': np.random.randint(1000, 10000)
            }
            for ts in timestamps
        ]
        
        # Mock high-frequency processor
        async def process_high_freq_data(data_point):
            await asyncio.sleep(processing_interval)
            return {
                'processed': True,
                'timestamp': data_point['timestamp'],
                'processed_price': data_point['price'] * 1.001
            }
        
        # Performance measurement
        self.performance_measurer.start_measurement("high_freq_processing")
        
        # Process data points
        results = []
        for data_point in test_data:
            result = await process_high_freq_data(data_point)
            results.append(result)
        
        # End measurement
        duration = self.performance_measurer.end_measurement("high_freq_processing")
        
        # Verify results
        assert len(results) == num_data_points
        assert all(result['processed'] for result in results)
        
        # Performance metrics
        throughput = num_data_points / duration
        expected_duration = num_data_points * processing_interval
        efficiency = expected_duration / duration
        
        # Performance assertions
        assert throughput > 1000, f"Throughput {throughput:.2f} points/sec is too low"
        assert efficiency > 0.8, f"Efficiency {efficiency:.2f} is too low"
        
        self.logger.info(f"High-frequency processing performance:")
        self.logger.info(f"  Data points: {num_data_points}")
        self.logger.info(f"  Duration: {duration:.4f}s")
        self.logger.info(f"  Throughput: {throughput:.2f} points/sec")
        self.logger.info(f"  Efficiency: {efficiency:.2f}")
    
    @pytest.mark.asyncio
    async def test_memory_efficient_processing(self):
        """Test memory-efficient processing performance."""
        # Test parameters
        num_batches = 100
        batch_size = 1000
        
        # Create large dataset
        large_dataset = []
        for i in range(num_batches * batch_size):
            large_dataset.append({
                'id': i,
                'data': 'x' * 100,  # 100 bytes per record
                'timestamp': datetime.now()
            })
        
        # Memory-efficient batch processor
        async def process_batch(batch):
            # Simulate processing
            await asyncio.sleep(0.01)
            return len(batch)
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Performance measurement
        self.performance_measurer.start_measurement("memory_efficient_processing")
        
        # Process in batches
        total_processed = 0
        for i in range(0, len(large_dataset), batch_size):
            batch = large_dataset[i:i + batch_size]
            processed_count = await process_batch(batch)
            total_processed += processed_count
            
            # Force garbage collection every 10 batches
            if i % (batch_size * 10) == 0:
                gc.collect()
        
        # End measurement
        duration = self.performance_measurer.end_measurement("memory_efficient_processing")
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Verify results
        assert total_processed == len(large_dataset)
        
        # Memory efficiency assertions
        assert memory_increase < 100, f"Memory increase {memory_increase:.2f}MB is too high"
        
        # Performance metrics
        throughput = total_processed / duration
        
        self.logger.info(f"Memory-efficient processing performance:")
        self.logger.info(f"  Total records: {total_processed}")
        self.logger.info(f"  Duration: {duration:.4f}s")
        self.logger.info(f"  Throughput: {throughput:.2f} records/sec")
        self.logger.info(f"  Memory increase: {memory_increase:.2f}MB")


class TestStressIntegration:
    """Test stress integration."""
    
    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup test environment."""
        self.logger = logging.getLogger(__name__)
        self.data_generator = TestDataGenerator()
        self.mock_factory = MockComponentFactory()
        self.performance_measurer = PerformanceMeasurer()
        
        yield
    
    @pytest.mark.asyncio
    async def test_system_under_extreme_load(self):
        """Test system performance under extreme load."""
        # Test parameters
        num_concurrent_requests = 1000
        request_duration = 0.1  # seconds
        
        # Mock system component
        async def mock_system_request(request_id):
            await asyncio.sleep(request_duration)
            return {
                'request_id': request_id,
                'status': 'processed',
                'timestamp': datetime.now()
            }
        
        # Performance measurement
        self.performance_measurer.start_measurement("extreme_load")
        
        # Create concurrent requests
        tasks = []
        for i in range(num_concurrent_requests):
            task = asyncio.create_task(mock_system_request(i))
            tasks.append(task)
        
        # Execute requests
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # End measurement
        duration = self.performance_measurer.end_measurement("extreme_load")
        
        # Analyze results
        successful_requests = [r for r in results if not isinstance(r, Exception)]
        failed_requests = [r for r in results if isinstance(r, Exception)]
        
        # Performance metrics
        success_rate = len(successful_requests) / num_concurrent_requests
        throughput = num_concurrent_requests / duration
        avg_response_time = duration / num_concurrent_requests
        
        # Stress test assertions
        assert success_rate > 0.95, f"Success rate {success_rate:.2f} is too low"
        assert throughput > 100, f"Throughput {throughput:.2f} requests/sec is too low"
        
        self.logger.info(f"Extreme load test results:")
        self.logger.info(f"  Total requests: {num_concurrent_requests}")
        self.logger.info(f"  Successful: {len(successful_requests)}")
        self.logger.info(f"  Failed: {len(failed_requests)}")
        self.logger.info(f"  Success rate: {success_rate:.2f}")
        self.logger.info(f"  Duration: {duration:.4f}s")
        self.logger.info(f"  Throughput: {throughput:.2f} requests/sec")
        self.logger.info(f"  Avg response time: {avg_response_time:.4f}s")
    
    @pytest.mark.asyncio
    async def test_memory_stress_test(self):
        """Test system behavior under memory stress."""
        # Test parameters
        num_objects = 10000
        object_size = 10000  # bytes
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create memory stress
        large_objects = []
        for i in range(num_objects):
            obj = {
                'id': i,
                'data': 'x' * object_size,
                'timestamp': datetime.now(),
                'nested': {
                    'value1': i * 2,
                    'value2': i * 3,
                    'value3': [j for j in range(100)]
                }
            }
            large_objects.append(obj)
            
            # Check memory usage every 1000 objects
            if i % 1000 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                self.logger.info(f"Created {i} objects, memory increase: {memory_increase:.2f}MB")
        
        # Get peak memory usage
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        peak_memory_increase = peak_memory - initial_memory
        
        # Cleanup
        del large_objects
        gc.collect()
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_recovered = peak_memory - final_memory
        
        # Memory stress test assertions
        assert peak_memory_increase > 0, "Memory should increase under stress"
        assert memory_recovered > 0, "Memory should be recovered after cleanup"
        assert final_memory < initial_memory * 2, "Final memory should not be too high"
        
        self.logger.info(f"Memory stress test results:")
        self.logger.info(f"  Objects created: {num_objects}")
        self.logger.info(f"  Initial memory: {initial_memory:.2f}MB")
        self.logger.info(f"  Peak memory: {peak_memory:.2f}MB")
        self.logger.info(f"  Final memory: {final_memory:.2f}MB")
        self.logger.info(f"  Peak increase: {peak_memory_increase:.2f}MB")
        self.logger.info(f"  Memory recovered: {memory_recovered:.2f}MB")
    
    @pytest.mark.asyncio
    async def test_cpu_stress_test(self):
        """Test system behavior under CPU stress."""
        # Test parameters
        num_cpu_intensive_tasks = 100
        task_duration = 0.1  # seconds
        
        # CPU-intensive task
        async def cpu_intensive_task(task_id):
            start_time = time.time()
            # Simulate CPU-intensive work
            result = 0
            for i in range(100000):
                result += i * i
            end_time = time.time()
            return {
                'task_id': task_id,
                'result': result,
                'duration': end_time - start_time
            }
        
        # Performance measurement
        self.performance_measurer.start_measurement("cpu_stress")
        
        # Create CPU-intensive tasks
        tasks = []
        for i in range(num_cpu_intensive_tasks):
            task = asyncio.create_task(cpu_intensive_task(i))
            tasks.append(task)
        
        # Execute tasks
        results = await asyncio.gather(*tasks)
        
        # End measurement
        duration = self.performance_measurer.end_measurement("cpu_stress")
        
        # Analyze results
        total_cpu_time = sum(result['duration'] for result in results)
        cpu_efficiency = total_cpu_time / duration
        
        # CPU stress test assertions
        assert len(results) == num_cpu_intensive_tasks
        assert all(result['result'] > 0 for result in results)
        assert cpu_efficiency > 0.5, f"CPU efficiency {cpu_efficiency:.2f} is too low"
        
        self.logger.info(f"CPU stress test results:")
        self.logger.info(f"  Tasks: {num_cpu_intensive_tasks}")
        self.logger.info(f"  Total duration: {duration:.4f}s")
        self.logger.info(f"  Total CPU time: {total_cpu_time:.4f}s")
        self.logger.info(f"  CPU efficiency: {cpu_efficiency:.2f}")


class TestScalabilityIntegration:
    """Test scalability integration."""
    
    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup test environment."""
        self.logger = logging.getLogger(__name__)
        self.data_generator = TestDataGenerator()
        self.mock_factory = MockComponentFactory()
        self.performance_measurer = PerformanceMeasurer()
        
        yield
    
    @pytest.mark.asyncio
    async def test_horizontal_scalability(self):
        """Test horizontal scalability performance."""
        # Test parameters
        num_workers = [1, 2, 4, 8, 16]
        tasks_per_worker = 100
        
        scalability_results = []
        
        for num_worker in num_workers:
            # Mock worker
            async def worker_task(worker_id, task_id):
                await asyncio.sleep(0.01)  # Simulate work
                return {
                    'worker_id': worker_id,
                    'task_id': task_id,
                    'completed_at': datetime.now()
                }
            
            # Performance measurement
            self.performance_measurer.start_measurement(f"scalability_{num_worker}_workers")
            
            # Create tasks for workers
            tasks = []
            for worker_id in range(num_worker):
                for task_id in range(tasks_per_worker):
                    task = asyncio.create_task(worker_task(worker_id, task_id))
                    tasks.append(task)
            
            # Execute tasks
            results = await asyncio.gather(*tasks)
            
            # End measurement
            duration = self.performance_measurer.end_measurement(f"scalability_{num_worker}_workers")
            
            # Calculate metrics
            total_tasks = num_worker * tasks_per_worker
            throughput = total_tasks / duration
            
            scalability_results.append({
                'workers': num_worker,
                'tasks': total_tasks,
                'duration': duration,
                'throughput': throughput
            })
            
            self.logger.info(f"Scalability test - {num_worker} workers:")
            self.logger.info(f"  Tasks: {total_tasks}")
            self.logger.info(f"  Duration: {duration:.4f}s")
            self.logger.info(f"  Throughput: {throughput:.2f} tasks/sec")
        
        # Analyze scalability
        baseline_throughput = scalability_results[0]['throughput']
        for result in scalability_results[1:]:
            expected_throughput = baseline_throughput * result['workers']
            actual_throughput = result['throughput']
            efficiency = actual_throughput / expected_throughput
            
            # Scalability assertions
            assert efficiency > 0.5, f"Scalability efficiency {efficiency:.2f} is too low for {result['workers']} workers"
            
            self.logger.info(f"Scalability efficiency for {result['workers']} workers: {efficiency:.2f}")
    
    @pytest.mark.asyncio
    async def test_data_volume_scalability(self):
        """Test data volume scalability performance."""
        # Test parameters
        data_sizes = [1000, 5000, 10000, 50000, 100000]
        
        scalability_results = []
        
        for data_size in data_sizes:
            # Create test data
            test_data = self.data_generator.generate_market_data(
                symbol="00700.HK",
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now(),
                frequency="1min"
            )
            
            # Take subset of data
            subset_data = test_data.head(data_size)
            
            # Mock data processor
            async def process_data(data):
                await asyncio.sleep(0.001)  # Simulate processing
                return len(data)
            
            # Performance measurement
            self.performance_measurer.start_measurement(f"data_volume_{data_size}")
            
            # Process data
            result = await process_data(subset_data)
            
            # End measurement
            duration = self.performance_measurer.end_measurement(f"data_volume_{data_size}")
            
            # Calculate metrics
            throughput = data_size / duration
            
            scalability_results.append({
                'data_size': data_size,
                'duration': duration,
                'throughput': throughput
            })
            
            self.logger.info(f"Data volume test - {data_size} records:")
            self.logger.info(f"  Duration: {duration:.4f}s")
            self.logger.info(f"  Throughput: {throughput:.2f} records/sec")
        
        # Analyze data volume scalability
        for i in range(1, len(scalability_results)):
            prev_result = scalability_results[i-1]
            curr_result = scalability_results[i]
            
            # Calculate throughput ratio
            throughput_ratio = curr_result['throughput'] / prev_result['throughput']
            data_ratio = curr_result['data_size'] / prev_result['data_size']
            
            # Scalability assertions
            assert throughput_ratio > 0.5, f"Throughput ratio {throughput_ratio:.2f} is too low"
            
            self.logger.info(f"Throughput ratio for {curr_result['data_size']} vs {prev_result['data_size']}: {throughput_ratio:.2f}")


class TestPerformanceBenchmarks:
    """Test performance benchmarks."""
    
    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup test environment."""
        self.logger = logging.getLogger(__name__)
        self.data_generator = TestDataGenerator()
        self.performance_measurer = PerformanceMeasurer()
        
        yield
    
    @pytest.mark.asyncio
    async def test_benchmark_data_processing_throughput(self):
        """Benchmark data processing throughput."""
        # Test parameters
        num_records = 10000
        batch_size = 1000
        
        # Create test data
        test_data = self.data_generator.generate_market_data(
            symbol="00700.HK",
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            frequency="1min"
        )
        
        # Mock data processor
        async def process_batch(batch):
            await asyncio.sleep(0.001)  # Simulate processing
            return len(batch)
        
        # Performance measurement
        self.performance_measurer.start_measurement("data_processing_throughput")
        
        # Process data in batches
        total_processed = 0
        for i in range(0, len(test_data), batch_size):
            batch = test_data.iloc[i:i + batch_size]
            processed_count = await process_batch(batch)
            total_processed += processed_count
        
        # End measurement
        duration = self.performance_measurer.end_measurement("data_processing_throughput")
        
        # Calculate metrics
        throughput = total_processed / duration
        
        # Benchmark assertions
        assert throughput > 1000, f"Throughput {throughput:.2f} records/sec is below benchmark"
        
        self.logger.info(f"Data processing throughput benchmark:")
        self.logger.info(f"  Records: {total_processed}")
        self.logger.info(f"  Duration: {duration:.4f}s")
        self.logger.info(f"  Throughput: {throughput:.2f} records/sec")
    
    @pytest.mark.asyncio
    async def test_benchmark_concurrent_request_handling(self):
        """Benchmark concurrent request handling."""
        # Test parameters
        num_requests = 1000
        concurrent_limit = 100
        
        # Mock request handler
        async def handle_request(request_id):
            await asyncio.sleep(0.01)  # Simulate processing
            return {
                'request_id': request_id,
                'status': 'processed',
                'timestamp': datetime.now()
            }
        
        # Performance measurement
        self.performance_measurer.start_measurement("concurrent_request_handling")
        
        # Process requests with concurrency limit
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        async def limited_request(request_id):
            async with semaphore:
                return await handle_request(request_id)
        
        tasks = [limited_request(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
        
        # End measurement
        duration = self.performance_measurer.end_measurement("concurrent_request_handling")
        
        # Calculate metrics
        throughput = num_requests / duration
        successful_requests = len([r for r in results if r['status'] == 'processed'])
        success_rate = successful_requests / num_requests
        
        # Benchmark assertions
        assert throughput > 100, f"Throughput {throughput:.2f} requests/sec is below benchmark"
        assert success_rate > 0.99, f"Success rate {success_rate:.2f} is below benchmark"
        
        self.logger.info(f"Concurrent request handling benchmark:")
        self.logger.info(f"  Requests: {num_requests}")
        self.logger.info(f"  Concurrent limit: {concurrent_limit}")
        self.logger.info(f"  Duration: {duration:.4f}s")
        self.logger.info(f"  Throughput: {throughput:.2f} requests/sec")
        self.logger.info(f"  Success rate: {success_rate:.2f}")
    
    @pytest.mark.asyncio
    async def test_benchmark_memory_usage(self):
        """Benchmark memory usage performance."""
        # Test parameters
        num_objects = 100000
        object_size = 1000  # bytes
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Performance measurement
        self.performance_measurer.start_measurement("memory_usage_benchmark")
        
        # Create objects
        objects = []
        for i in range(num_objects):
            obj = {
                'id': i,
                'data': 'x' * object_size,
                'timestamp': datetime.now()
            }
            objects.append(obj)
        
        # End measurement
        duration = self.performance_measurer.end_measurement("memory_usage_benchmark")
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Calculate metrics
        memory_per_object = memory_increase / num_objects
        memory_creation_rate = num_objects / duration
        
        # Benchmark assertions
        assert memory_per_object < 0.01, f"Memory per object {memory_per_object:.4f}MB is too high"
        assert memory_creation_rate > 1000, f"Memory creation rate {memory_creation_rate:.2f} objects/sec is too low"
        
        self.logger.info(f"Memory usage benchmark:")
        self.logger.info(f"  Objects: {num_objects}")
        self.logger.info(f"  Duration: {duration:.4f}s")
        self.logger.info(f"  Memory increase: {memory_increase:.2f}MB")
        self.logger.info(f"  Memory per object: {memory_per_object:.4f}MB")
        self.logger.info(f"  Creation rate: {memory_creation_rate:.2f} objects/sec")
        
        # Cleanup
        del objects
        gc.collect()


if __name__ == "__main__":
    # Run performance integration tests
    pytest.main([__file__, "-v", "--tb=short"])

#!/usr/bin/env python3
"""
Comprehensive Testing Suite for Parallel Processing System
Reliability, performance, and stress testing for 32-core parallel processing
"""

import os
import sys
import time
import unittest
import logging
import threading
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
import psutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .multi_process_scheduler import MultiProcessScheduler, TaskPriority, Task, TaskStatus
from .parallel_data_processor import ParallelDataProcessor, ProcessingFunctions
from .interprocess_communication import InterProcessCommunication, MessageType
from .parallel_backtesting_engine import ParallelBacktestingEngine, BacktestConfig
from .process_pool_manager import ProcessPoolManager
from .memory_optimizer import MemoryOptimizer
from .result_aggregator import ResultAggregator, AggregationConfig
from .performance_monitor import PerformanceMonitor, PerformanceThreshold, PerformanceMetric

logger = logging.getLogger(__name__)


class TestMultiProcessScheduler(unittest.TestCase):
    """Test suite for MultiProcessScheduler"""

    def setUp(self):
        """Set up test environment"""
        self.scheduler = MultiProcessScheduler(
            max_workers=4,  # Reduced for testing
            memory_limit_gb=2.0
        )
        self.scheduler.start()

    def tearDown(self):
        """Clean up test environment"""
        self.scheduler.stop()

    def test_scheduler_initialization(self):
        """Test scheduler initialization"""
        self.assertEqual(self.scheduler.max_workers, 4)
        self.assertTrue(self.scheduler.is_running)
        self.assertEqual(len(self.scheduler.workers), 4)

    def test_task_submission(self):
        """Test basic task submission"""
        def simple_function(x):
            return x * 2

        task_id = self.scheduler.submit_task(
            function=simple_function,
            args=(5,),
            priority=TaskPriority.NORMAL
        )

        self.assertIsNotNone(task_id)
        self.assertIn(task_id, self.scheduler.tasks)

        # Wait for completion
        time.sleep(1)
        status = self.scheduler.get_task_status(task_id)
        self.assertEqual(status, TaskStatus.COMPLETED)

    def test_batch_task_submission(self):
        """Test batch task submission"""
        def process_chunk(data_chunk, chunk_index):
            return len(data_chunk) + chunk_index

        data_chunks = [
            [1, 2, 3, 4],
            [5, 6, 7, 8],
            [9, 10, 11, 12]
        ]

        task_ids = self.scheduler.submit_batch_tasks(
            function=process_chunk,
            data_chunks=data_chunks,
            priority=TaskPriority.HIGH
        )

        self.assertEqual(len(task_ids), len(data_chunks))

        # Wait for completion
        results = self.scheduler.wait_for_completion(task_ids, timeout=10)
        self.assertEqual(len(results), len(data_chunks))

    def test_priority_ordering(self):
        """Test task priority ordering"""
        results = {}

        def priority_task(priority, results_dict):
            results_dict[priority] = time.time()
            time.sleep(0.1)  # Small delay
            return priority

        # Submit tasks with different priorities
        high_task = self.scheduler.submit_task(
            function=priority_task,
            args=("high", results),
            priority=TaskPriority.HIGH
        )

        low_task = self.scheduler.submit_task(
            function=priority_task,
            args=("low", results),
            priority=TaskPriority.LOW
        )

        time.sleep(1)  # Wait for processing

        # High priority task should complete first
        self.assertIn("high", results)
        self.assertIn("low", results)
        self.assertLess(results["high"], results["low"])

    def test_error_handling(self):
        """Test error handling in tasks"""
        def failing_function():
            raise ValueError("Test error")

        task_id = self.scheduler.submit_task(
            function=failing_function,
            priority=TaskPriority.NORMAL
        )

        time.sleep(1)  # Wait for processing
        task = self.scheduler.tasks.get(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertIsNotNone(task.error)


class TestParallelDataProcessor(unittest.TestCase):
    """Test suite for ParallelDataProcessor"""

    def setUp(self):
        """Set up test environment"""
        self.scheduler = MultiProcessScheduler(max_workers=4)
        self.scheduler.start()
        self.processor = ParallelDataProcessor(scheduler=self.scheduler)

    def tearDown(self):
        """Clean up test environment"""
        self.scheduler.stop()

    def test_data_chunking(self):
        """Test data chunking functionality"""
        # Create test data
        test_data = pd.DataFrame({
            'close': np.random.random(1000) * 100 + 50,
            'volume': np.random.randint(1000, 10000, 1000)
        }, index=pd.date_range('2020-01-01', periods=1000, freq='D'))

        # Process data in parallel
        result = self.processor.process_data_parallel(
            data=test_data,
            processing_function='calculate_technical_indicators',
            chunk_size=100
        )

        self.assertIsInstance(result, pd.DataFrame)
        self.assertGreater(len(result), 0)
        # Should have additional indicator columns
        self.assertGreater(len(result.columns), len(test_data.columns))

    def test_dataframe_chunking(self):
        """Test DataFrame chunking"""
        large_df = pd.DataFrame({
            'price': np.random.random(10000),
            'volume': np.random.randint(100, 1000, 10000)
        })

        chunks = self.processor._create_dataframe_chunks(
            job_id="test_job",
            df=large_df,
            chunk_size=1000,
            overlap_size=50
        )

        self.assertEqual(len(chunks), 10)  # 10000 / 1000 = 10
        self.assertEqual(chunks[0].chunk_index, 0)
        self.assertEqual(chunks[-1].chunk_index, 9)

    def test_time_based_chunking(self):
        """Test time-based chunking"""
        # Create 2 years of daily data
        date_index = pd.date_range('2020-01-01', '2021-12-31', freq='D')
        time_series_data = pd.DataFrame({
            'value': np.random.random(len(date_index))
        }, index=date_index)

        chunks = self.processor._create_time_based_chunks(
            df=time_series_data,
            date_column=None,  # Use index
            time_window_days=30
        )

        self.assertGreater(len(chunks), 20)  # Should have ~24 chunks (730 days / 30 days)

    def test_memory_usage_estimation(self):
        """Test memory usage estimation"""
        test_data = pd.DataFrame({
            'data': np.random.random(1000)
        })

        memory_mb = self.processor._estimate_chunk_memory_usage(test_data)
        self.assertGreater(memory_mb, 0)
        self.assertLess(memory_mb, 1000)  # Should be reasonable

    def test_cleanup(self):
        """Test cleanup functionality"""
        # Create a job
        job_id = self.processor.create_processing_job(
            data=pd.DataFrame({'test': [1, 2, 3]}),
            processing_function='validate_data_quality'
        )

        self.assertIn(job_id, self.processor.active_jobs)
        self.processor.cleanup_job(job_id)
        self.assertNotIn(job_id, self.processor.active_jobs)

        self.processor.cleanup_all_jobs()
        self.assertEqual(len(self.processor.active_jobs), 0)


class TestInterProcessCommunication(unittest.TestCase):
    """Test suite for InterProcessCommunication"""

    def setUp(self):
        """Set up test environment"""
        self.ipc = InterProcessCommunication(
            process_id=0,
            max_shared_memory_mb=100
        )
        self.ipc.start()

    def tearDown(self):
        """Clean up test environment"""
        self.ipc.stop()

    def test_message_sending(self):
        """Test message sending and receiving"""
        message_received = threading.Event()
        received_message = None

        def message_handler(message):
            nonlocal received_message
            received_message = message
            message_received.set()

        self.ipc.register_message_handler(MessageType.HEARTBEAT, message_handler)

        # Send a message to self (for testing)
        self.ipc.send_message(
            receiver_id=0,
            message_type=MessageType.HEARTBEAT,
            payload={'test': 'data'}
        )

        # Wait for message processing
        message_received.wait(timeout=2)
        self.assertIsNotNone(received_message)
        self.assertEqual(received_message.payload['test'], 'data')

    def test_shared_memory(self):
        """Test shared memory functionality"""
        test_data = np.random.random(1000)

        # Create shared memory block
        block_id = self.ipc.create_shared_memory(
            data=test_data,
            metadata={'test': 'shared_memory'}
        )

        self.assertIsNotNone(block_id)
        self.assertIn(block_id, self.ipc.shared_memory_blocks)

        # Access shared memory
        retrieved_data = self.ipc.access_shared_memory(block_id)
        np.testing.assert_array_equal(retrieved_data, test_data)

        # Release shared memory
        success = self.ipc.release_shared_memory(block_id)
        self.assertTrue(success)
        self.assertNotIn(block_id, self.ipc.shared_memory_blocks)

    def test_large_data_transfer(self):
        """Test large data transfer using shared memory"""
        large_data = pd.DataFrame({
            'random_data': np.random.random(10000),
            'timestamps': pd.date_range('2020-01-01', periods=10000, freq='H')
        })

        transfer_id = self.ipc.transfer_large_data(
            receiver_id=0,
            data=large_data,
            data_description="Large test DataFrame"
        )

        self.assertIsNotNone(transfer_id)

    def test_statistics(self):
        """Test statistics collection"""
        stats = self.ipc.get_statistics()
        self.assertIn('ipc_stats', stats)
        self.assertIn('is_running', stats)
        self.assertTrue(stats['is_running'])


class TestParallelBacktestingEngine(unittest.TestCase):
    """Test suite for ParallelBacktestingEngine"""

    def setUp(self):
        """Set up test environment"""
        self.config = BacktestConfig(
            symbols=['TEST1', 'TEST2'],
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2020, 12, 31),
            initial_cash=1000000,
            num_workers=2,  # Reduced for testing
            memory_limit_gb=2.0
        )

        # Create test data
        dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        self.test_data = pd.DataFrame({
            'close': np.random.random(len(dates)) * 100 + 50,
            'volume': np.random.randint(1000, 10000, len(dates))
        }, index=dates)

        self.engine = ParallelBacktestingEngine(config=self.config)

    def tearDown(self):
        """Clean up test environment"""
        self.engine.cleanup()

    def test_engine_initialization(self):
        """Test engine initialization"""
        self.assertEqual(len(self.config.symbols), 2)
        self.assertIsNotNone(self.engine.scheduler)
        self.assertIsNotNone(self.engine.data_processor)

    def test_chunk_creation(self):
        """Test backtest chunk creation"""
        # Create backtest chunks
        chunks = self.engine._create_backtest_chunks(
            data=self.test_data,
            strategy_params={'period': 20}
        )

        self.assertGreater(len(chunks), 0)
        self.assertEqual(chunks[0].symbols, self.config.symbols)

    def test_simple_backtest(self):
        """Test simple backtesting"""
        def simple_strategy(prices):
            return pd.DataFrame(
                np.random.choice([1, -1, 0], size=prices.shape),
                index=prices.index,
                columns=prices.columns
            )

        result = self.engine.run_parallel_backtest(
            data=self.test_data,
            strategy_function=simple_strategy
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result.total_return, float)
        self.assertIsInstance(result.sharpe_ratio, float)

    def test_symbol_parallel_backtest(self):
        """Test symbol-parallel backtesting"""
        data_dict = {
            'TEST1': self.test_data,
            'TEST2': self.test_data.copy() * 1.1  # Slightly different prices
        }

        results = self.engine.run_symbol_parallel_backtest(
            data_dict=data_dict,
            strategy_function=lambda df, **kwargs: pd.DataFrame(
                np.random.choice([1, -1, 0], size=(len(df), 1)),
                index=df.index,
                columns=['signal']
            )
        )

        self.assertEqual(len(results), 2)
        self.assertIn('TEST1', results)
        self.assertIn('TEST2', results)

    def test_parameter_sweep(self):
        """Test parameter sweep functionality"""
        parameter_grid = {
            'fast_period': [5, 10, 15],
            'slow_period': [20, 30, 40]
        }

        def ma_crossover_strategy(prices, fast_period=10, slow_period=30):
            return pd.DataFrame(
                np.random.choice([1, -1, 0], size=prices.shape),
                index=prices.index,
                columns=prices.columns
            )

        results = self.engine.run_parameter_sweep(
            data=self.test_data,
            strategy_function=ma_crossover_strategy,
            parameter_grid=parameter_grid,
            combination_limit=6  # Limit for testing
        )

        self.assertLessEqual(len(results), 6)
        # Results should be sorted by performance
        if len(results) > 1:
            self.assertGreaterEqual(results[0].sharpe_ratio, results[-1].sharpe_ratio)

    def test_statistics_collection(self):
        """Test statistics collection"""
        stats = self.engine.get_statistics()
        self.assertIn('engine_stats', stats)
        self.assertIn('config', stats)
        self.assertIn('scheduler_stats', stats)


class TestMemoryOptimizer(unittest.TestCase):
    """Test suite for MemoryOptimizer"""

    def setUp(self):
        """Set up test environment"""
        self.optimizer = MemoryOptimizer(
            target_memory_usage_percent=70.0,
            gc_threshold_percent=80.0,
            cleanup_interval=5.0  # Shorter for testing
        )
        self.optimizer.start()

    def tearDown(self):
        """Clean up test environment"""
        self.optimizer.stop()

    def test_memory_pool_creation(self):
        """Test memory pool creation"""
        success = self.optimizer.create_memory_pool(
            pool_name="test_pool",
            pool_size_mb=10.0
        )

        self.assertTrue(success)
        self.assertIn("test_pool", self.optimizer.memory_pools)

    def test_memory_pool_allocation(self):
        """Test memory allocation from pool"""
        self.optimizer.create_memory_pool("alloc_test", 50.0)

        allocated_array = self.optimizer.allocate_from_pool(
            pool_name="alloc_test",
            size_bytes=1024 * 1024  # 1MB
        )

        self.assertIsNotNone(allocated_array)
        self.assertEqual(len(allocated_array), 1024 * 1024 // 8)  # float64

    def test_dataframe_optimization(self):
        """Test DataFrame optimization"""
        # Create a non-optimized DataFrame
        df = pd.DataFrame({
            'int_col': [1, 2, 3, 4, 5] * 1000,
            'float_col': [1.1, 2.2, 3.3, 4.4, 5.5] * 1000,
            'str_col': ['a', 'b', 'c', 'd', 'e'] * 1000
        })

        original_memory = df.memory_usage(deep=True).sum()
        optimized_df = self.optimizer.optimize_dataframe(df, aggressive=True)
        optimized_memory = optimized_df.memory_usage(deep=True).sum()

        # Should use less memory after optimization
        self.assertLessEqual(optimized_memory, original_memory)

    def test_data_compression(self):
        """Test data compression functionality"""
        test_data = np.random.random(10000)

        compressed_data = self.optimizer.compress_data(test_data)
        decompressed_data = self.optimizer.decompress_data(compressed_data)

        np.testing.assert_array_equal(decompressed_data, test_data)

    def test_memory_report(self):
        """Test memory report generation"""
        report = self.optimizer.get_memory_report()
        self.assertIn('timestamp', report)
        self.assertIn('pressure_level', report)
        self.assertIn('process_memory_mb', report)
        self.assertIn('system_memory', report)


class TestResultAggregator(unittest.TestCase):
    """Test suite for ResultAggregator"""

    def setUp(self):
        """Set up test environment"""
        self.aggregator = ResultAggregator()
        self.aggregator.start()

    def tearDown(self):
        """Clean up test environment"""
        self.aggregator.stop()

    def test_job_creation(self):
        """Test aggregation job creation"""
        success = self.aggregator.create_aggregation_job(
            job_id="test_job",
            expected_results=3,
            aggregation_function="sum"
        )

        self.assertTrue(success)
        self.assertIn("test_job", self.aggregator.active_jobs)

    def test_partial_result_submission(self):
        """Test partial result submission"""
        self.aggregator.create_aggregation_job(
            job_id="partial_test",
            expected_results=2,
            aggregation_function="concatenate"
        )

        success1 = self.aggregator.submit_partial_result(
            job_id="partial_test",
            worker_id=1,
            task_id="task1",
            data=[1, 2, 3],
            processing_time=0.1
        )

        success2 = self.aggregator.submit_partial_result(
            job_id="partial_test",
            worker_id=2,
            task_id="task2",
            data=[4, 5, 6],
            processing_time=0.1
        )

        self.assertTrue(success1)
        self.assertTrue(success2)

        job = self.aggregator.active_jobs.get("partial_test")
        self.assertEqual(job.received_results, 2)
        self.assertEqual(job.completion_rate, 1.0)

    def test_result_aggregation(self):
        """Test result aggregation"""
        self.aggregator.create_aggregation_job(
            job_id="agg_test",
            expected_results=2,
            aggregation_function="sum"
        )

        # Submit partial results
        self.aggregator.submit_partial_result(
            job_id="agg_test",
            worker_id=1,
            task_id="task1",
            data=10.0,
            processing_time=0.1
        )

        self.aggregator.submit_partial_result(
            job_id="agg_test",
            worker_id=2,
            task_id="task2",
            data=15.0,
            processing_time=0.1
        )

        # Wait for processing
        time.sleep(1)

        result = self.aggregator.get_job_result("agg_test", timeout=5)
        self.assertEqual(result, 25.0)  # 10 + 15

    def test_dataframe_aggregation(self):
        """Test DataFrame aggregation"""
        self.aggregator.create_aggregation_job(
            job_id="df_test",
            expected_results=2,
            aggregation_function="merge_dataframe"
        )

        # Create test DataFrames
        df1 = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        df2 = pd.DataFrame({'A': [5, 6], 'B': [7, 8]})

        self.aggregator.submit_partial_result(
            job_id="df_test",
            worker_id=1,
            task_id="task1",
            data=df1,
            processing_time=0.1
        )

        self.aggregator.submit_partial_result(
            job_id="df_test",
            worker_id=2,
            task_id="task2",
            data=df2,
            processing_time=0.1
        )

        # Wait for processing
        time.sleep(1)

        result = self.aggregator.get_job_result("df_test", timeout=5)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 4)  # 2 + 2 rows


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete parallel system"""

    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up integration test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_backtesting(self):
        """Test complete end-to-end backtesting workflow"""
        # Create comprehensive test data
        symbols = ['AAPL', 'GOOGL', 'MSFT']
        date_range = pd.date_range('2020-01-01', '2020-06-30', freq='D')

        # Create multi-index DataFrame
        data_list = []
        for symbol in symbols:
            df = pd.DataFrame({
                'close': 100 + np.cumsum(np.random.random(len(date_range)) * 0.1),
                'volume': np.random.randint(1000000, 10000000, len(date_range))
            }, index=date_range)
            df['symbol'] = symbol
            data_list.append(df)

        test_data = pd.concat(data_list)

        # Configure backtesting
        config = BacktestConfig(
            symbols=symbols,
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2020, 6, 30),
            num_workers=4,
            memory_limit_gb=4.0
        )

        # Create and run backtesting engine
        engine = ParallelBacktestingEngine(config=config)

        try:
            # Define a simple strategy
            def simple_momentum_strategy(prices, period=10):
                returns = prices.pct_change(period)
                signals = pd.DataFrame(0, index=prices.index, columns=prices.columns)
                signals[returns > 0] = 1
                signals[returns < 0] = -1
                return signals

            # Run backtest
            result = engine.run_parallel_backtest(
                data=test_data,
                strategy_function=simple_momentum_strategy,
                strategy_params={'period': 5}
            )

            # Validate results
            self.assertIsNotNone(result)
            self.assertIsInstance(result.total_return, float)
            self.assertIsInstance(result.sharpe_ratio, float)
            self.assertGreater(len(result.equity_curve), 0)

            # Check statistics
            stats = engine.get_statistics()
            self.assertIn('engine_stats', stats)
            self.assertGreater(stats['engine_stats']['total_backtests_run'], 0)

        finally:
            engine.cleanup()

    def test_parameter_optimization_workflow(self):
        """Test parameter optimization workflow"""
        # Create test data
        dates = pd.date_range('2020-01-01', periods=500, freq='D')
        test_data = pd.DataFrame({
            'close': 100 + np.cumsum(np.random.random(500) * 0.5),
            'volume': np.random.randint(100000, 1000000, 500)
        }, index=dates)

        config = BacktestConfig(
            symbols=['TEST'],
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2021, 5, 1),
            num_workers=2,
            memory_limit_gb=2.0
        )

        engine = ParallelBacktestingEngine(config=config)

        try:
            # Define strategy with parameters
            def ma_strategy(prices, fast_period=10, slow_period=30):
                fast_ma = prices.rolling(window=fast_period).mean()
                slow_ma = prices.rolling(window=slow_period).mean()
                signals = pd.DataFrame(0, index=prices.index, columns=prices.columns)
                signals[fast_ma > slow_ma] = 1
                signals[fast_ma < slow_ma] = -1
                return signals

            # Run parameter sweep
            parameter_grid = {
                'fast_period': [5, 10, 15],
                'slow_period': [20, 30, 40]
            }

            results = engine.run_parameter_sweep(
                data=test_data,
                strategy_function=ma_strategy,
                parameter_grid=parameter_grid,
                combination_limit=9  # All combinations
            )

            # Validate results
            self.assertGreater(len(results), 0)

            # Results should be sorted by Sharpe ratio (descending)
            if len(results) > 1:
                for i in range(len(results) - 1):
                    self.assertGreaterEqual(results[i].sharpe_ratio, results[i + 1].sharpe_ratio)

        finally:
            engine.cleanup()

    def test_memory_efficiency(self):
        """Test memory efficiency with large datasets"""
        # Create large dataset
        large_data = pd.DataFrame({
            'close': np.random.random(10000) * 100,
            'volume': np.random.randint(1000, 10000, 10000),
            'high': np.random.random(10000) * 110,
            'low': np.random.random(10000) * 90,
            'open': np.random.random(10000) * 100
        }, index=pd.date_range('2020-01-01', periods=10000, freq='H'))

        config = BacktestConfig(
            symbols=['LARGE_TEST'],
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2023, 5, 1),
            num_workers=2,
            memory_limit_gb=2.0
        )

        engine = ParallelBacktestingEngine(config=config)

        try:
            # Monitor memory usage
            initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)

            # Run backtesting on large dataset
            def simple_strategy(prices):
                return pd.DataFrame(
                    np.random.choice([1, -1, 0], size=prices.shape),
                    index=prices.index,
                    columns=prices.columns
                )

            result = engine.run_parallel_backtest(
                data=large_data,
                strategy_function=simple_strategy
            )

            peak_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            memory_increase = peak_memory - initial_memory

            # Memory increase should be reasonable (< 500MB)
            self.assertLess(memory_increase, 500)

        finally:
            engine.cleanup()


class StressTest(unittest.TestCase):
    """Stress tests for the parallel system"""

    def test_high_concurrency_load(self):
        """Test system under high concurrency load"""
        scheduler = MultiProcessScheduler(max_workers=8)
        scheduler.start()

        try:
            # Submit many tasks concurrently
            task_ids = []
            for i in range(100):
                task_id = scheduler.submit_task(
                    function=lambda x, delay: time.sleep(delay) or x * x,
                    args=(i, 0.01),  # Very short tasks
                    priority=TaskPriority.NORMAL
                )
                task_ids.append(task_id)

            # Wait for all to complete
            start_time = time.time()
            results = scheduler.wait_for_completion(task_ids, timeout=60)
            completion_time = time.time() - start_time

            # All tasks should complete
            self.assertEqual(len(results), 100)
            # Should complete within reasonable time
            self.assertLess(completion_time, 30)

            # Check statistics
            stats = scheduler.get_statistics()
            self.assertGreater(stats['scheduler_stats']['completed_tasks'], 90)

        finally:
            scheduler.stop()

    def test_memory_pressure_handling(self):
        """Test system under memory pressure"""
        optimizer = MemoryOptimizer(
            target_memory_usage_percent=60.0,
            gc_threshold_percent=70.0,
            cleanup_interval=1.0  # Very frequent for testing
        )
        optimizer.start()

        try:
            # Create memory pressure
            large_objects = []
            for i in range(50):
                # Create progressively larger objects
                large_array = np.random.random(10000 * (i + 1))
                large_objects.append(large_array)

            # Check if optimizer handled the pressure
            memory_report = optimizer.get_memory_report()
            pressure_level = memory_report.get('pressure_level', 'low')

            # Should detect some level of pressure
            self.assertIn(pressure_level, ['medium', 'high', 'critical', 'low'])

        finally:
            optimizer.stop()


def run_all_tests():
    """Run all test suites"""
    # Configure logging for tests
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create test suite
    test_classes = [
        TestMultiProcessScheduler,
        TestParallelDataProcessor,
        TestInterProcessCommunication,
        TestParallelBacktestingEngine,
        TestMemoryOptimizer,
        TestResultAggregator,
        TestIntegration,
        StressTest
    ]

    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Exception:')[-1].strip()}")

    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
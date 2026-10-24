"""
Performance Benchmark Tests
性能基准测试

Comprehensive performance testing for CBSC VectorBT system.
CBSC VectorBT系统的综合性能测试。

Author: CBSC Backtesting System Team
Date: 2025-12-04
Version: 1.0
"""

import pytest
import time
import psutil
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import gc
from typing import Dict, Any, List, Tuple

from data_loader import CBSCDataLoader
from signal_generator import CBSCSignalGenerator
from cbsc_backtester import CBSCBacktester
from optimizer import CBSCOptimizer

class TestPerformanceBenchmarks:
    """Test system performance against established benchmarks"""

    @pytest.fixture(scope="class")
    def performance_targets(self):
        """Performance targets for testing"""
        return {
            'max_total_time': 30.0,      # Maximum end-to-end time
            'max_data_loading': 5.0,     # Maximum data loading time
            'max_signal_generation': 3.0, # Maximum signal generation time
            'max_backtesting': 20.0,     # Maximum backtesting time
            'max_optimization': 60.0,    # Maximum optimization time
            'max_memory_mb': 2048,       # Maximum memory usage
            'min_throughput': 100        # Minimum records per second
        }

    def measure_performance(self, func, *args, **kwargs) -> Dict[str, Any]:
        """Measure function performance metrics"""
        gc.collect()  # Clean up memory before measurement

        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)

        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        return {
            'result': result,
            'success': success,
            'error': error,
            'execution_time': end_time - start_time,
            'memory_used': end_memory - start_memory,
            'peak_memory': end_memory,
            'throughput': self._calculate_throughput(result, end_time - start_time)
        }

    def _calculate_throughput(self, result, execution_time) -> float:
        """Calculate throughput (records per second)"""
        if execution_time <= 0 or result is None:
            return 0.0

        if isinstance(result, pd.DataFrame):
            return len(result) / execution_time
        elif isinstance(result, dict):
            # For strategies or portfolios
            total_records = sum(len(v) if hasattr(v, '__len__') else 0 for v in result.values())
            return total_records / execution_time
        else:
            return 0.0

    @pytest.mark.performance
    def test_data_loading_performance(self, performance_targets):
        """Test TC-PERF-001: Data loading speed benchmark"""
        # Generate large test dataset
        large_dataset = self._generate_large_dataset(1000)  # 1000 records

        # Create temporary CSV file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        large_dataset.to_csv(temp_file.name, index=False)
        temp_file.close()

        try:
            loader = CBSCDataLoader(temp_file.name)

            # Measure loading performance
            perf = self.measure_performance(loader.load_sentiment_data)

            # Assertions
            assert perf['success'], f"Data loading failed: {perf['error']}"
            assert perf['execution_time'] <= performance_targets['max_data_loading'], \
                f"Data loading too slow: {perf['execution_time']:.2f}s (target: {performance_targets['max_data_loading']}s)"
            assert perf['memory_used'] <= performance_targets['max_memory_mb'] / 4, \
                f"Too much memory used for loading: {perf['memory_used']:.1f}MB"
            assert perf['throughput'] >= performance_targets['min_throughput'], \
                f"Throughput too low: {perf['throughput']:.1f} records/s"

            print(f"Data Loading Performance:")
            print(f"  Time: {perf['execution_time']:.3f}s")
            print(f"  Memory: {perf['memory_used']:.1f}MB")
            print(f"  Throughput: {perf['throughput']:.1f} records/s")

        finally:
            Path(temp_file.name).unlink()

    @pytest.mark.performance
    def test_signal_generation_performance(self, performance_targets, mock_features_data):
        """Test signal generation speed benchmark"""
        generator = CBSCSignalGenerator()

        # Measure signal generation performance
        perf = self.measure_performance(generator.generate_multiple_strategies, mock_features_data)

        # Assertions
        assert perf['success'], f"Signal generation failed: {perf['error']}"
        assert perf['execution_time'] <= performance_targets['max_signal_generation'], \
            f"Signal generation too slow: {perf['execution_time']:.2f}s (target: {performance_targets['max_signal_generation']}s)"
        assert perf['result'] is not None, "Should return strategy results"
        assert len(perf['result']) == 5, "Should generate 5 strategies"

        print(f"Signal Generation Performance:")
        print(f"  Time: {perf['execution_time']:.3f}s")
        print(f"  Strategies: {len(perf['result'])}")
        print(f"  Memory: {perf['memory_used']:.1f}MB")

    @pytest.mark.performance
    @pytest.mark.slow
    def test_backtesting_performance(self, performance_targets, mock_features_data):
        """Test backtesting speed benchmark"""
        # Create temporary data file for backtester
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        mock_sentiment = mock_features_data[['Date', 'Bull_Ratio', 'Bull_Bear_Ratio',
                                           'Bull_Turnover_HKD', 'Bear_Turnover_HKD',
                                           'Afternoon_Close', 'Signal', 'Sentiment_Level']]
        mock_sentiment.to_csv(temp_file.name, index=False)
        temp_file.close()

        try:
            backtester = CBSCBacktester(temp_file.name)

            # Prepare price data
            price_data = mock_features_data[['Date', 'open', 'high', 'low', 'close', 'volume']]
            price_data['Date'] = pd.to_datetime(price_data['Date'])
            backtester.features_df = mock_features_data
            backtester.price_data = price_data.set_index('Date')

            # Measure backtesting performance
            perf = self.measure_performance(backtester.run_multiple_strategies, "0700.HK")

            # Assertions
            assert perf['success'], f"Backtesting failed: {perf['error']}"
            assert perf['execution_time'] <= performance_targets['max_backtesting'], \
                f"Backtesting too slow: {perf['execution_time']:.2f}s (target: {performance_targets['max_backtesting']}s)"
            assert perf['result'] is not None, "Should return portfolio results"

            print(f"Backtesting Performance:")
            print(f"  Time: {perf['execution_time']:.3f}s")
            print(f"  Portfolios: {len(perf['result'])}")
            print(f"  Memory: {perf['memory_used']:.1f}MB")

        finally:
            Path(temp_file.name).unlink()

    @pytest.mark.performance
    @pytest.mark.slow
    def test_optimization_performance(self, performance_targets, mock_features_data):
        """Test optimization speed benchmark"""
        # Create temporary data file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        mock_sentiment = mock_features_data[['Date', 'Bull_Ratio', 'Bull_Bear_Ratio',
                                           'Bull_Turnover_HKD', 'Bear_Turnover_HKD',
                                           'Afternoon_Close', 'Signal', 'Sentiment_Level']]
        mock_sentiment.to_csv(temp_file.name, index=False)
        temp_file.close()

        try:
            config = {
                'backtest_config': {
                    'initial_cash': 1000000,
                    'fees': 0.003,
                    'slippage': 0.001
                },
                'optimization_ranges': {
                    'sentiment_threshold': [0.2, 0.3, 0.4],
                    'rsi_overbought': [65, 70, 75],
                    'rsi_oversold': [25, 30, 35]
                },
                'optimization_metric': 'sharpe_ratio',
                'max_combinations': 50  # Reduced for performance testing
            }

            optimizer = CBSCOptimizer(temp_file.name, config)

            # Measure optimization performance
            perf = self.measure_performance(optimizer.run_random_search, "0700.HK", n_iterations=20)

            # Assertions
            assert perf['success'], f"Optimization failed: {perf['error']}"
            assert perf['execution_time'] <= performance_targets['max_optimization'], \
                f"Optimization too slow: {perf['execution_time']:.2f}s (target: {performance_targets['max_optimization']}s)"
            assert not perf['result'].empty, "Should return optimization results"

            print(f"Optimization Performance:")
            print(f"  Time: {perf['execution_time']:.3f}s")
            print(f"  Results: {len(perf['result'])} parameter combinations")
            print(f"  Memory: {perf['memory_used']:.1f}MB")

        finally:
            Path(temp_file.name).unlink()

    @pytest.mark.performance
    def test_end_to_end_workflow_performance(self, performance_targets):
        """Test complete workflow performance against <30s target"""
        # Create test data
        test_data = self._generate_large_dataset(500)  # 500 records

        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        test_data.to_csv(temp_file.name, index=False)
        temp_file.close()

        try:
            def complete_workflow():
                """Complete end-to-end workflow"""
                # 1. Data loading
                loader = CBSCDataLoader(temp_file.name)
                sentiment_df = loader.load_sentiment_data()

                # 2. Feature creation (with mock price data)
                price_data = pd.DataFrame({
                    'Date': sentiment_df['Date'],
                    'open': sentiment_df['Afternoon_Close'] * 0.98,
                    'high': sentiment_df['Afternoon_Close'] * 1.02,
                    'low': sentiment_df['Afternoon_Close'] * 0.97,
                    'close': sentiment_df['Afternoon_Close'],
                    'volume': np.random.randint(1000000, 10000000, len(sentiment_df))
                })
                features_df = loader.create_cbsc_features(sentiment_df, price_data)

                # 3. Signal generation
                generator = CBSCSignalGenerator()
                strategies = generator.generate_multiple_strategies(features_df)

                # 4. Performance analysis
                performance_summary = {}
                for strategy_name, (entries, exits) in strategies.items():
                    quality = generator.analyze_signal_quality(features_df, entries, exits)
                    performance_summary[strategy_name] = quality

                return {
                    'records_processed': len(features_df),
                    'strategies_generated': len(strategies),
                    'performance_summary': performance_summary
                }

            # Measure complete workflow performance
            perf = self.measure_performance(complete_workflow)

            # Critical assertion for production readiness
            assert perf['success'], f"Complete workflow failed: {perf['error']}"
            assert perf['execution_time'] <= performance_targets['max_total_time'], \
                f"COMPLETE WORKFLOW TOO SLOW: {perf['execution_time']:.2f}s (target: {performance_targets['max_total_time']}s)"

            # Additional performance checks
            assert perf['memory_used'] <= performance_targets['max_memory_mb'], \
                f"Too much memory used: {perf['memory_used']:.1f}MB"

            workflow_result = perf['result']
            assert workflow_result['records_processed'] > 0, "Should process records"
            assert workflow_result['strategies_generated'] == 5, "Should generate 5 strategies"

            print(f"\n🎯 CRITICAL PERFORMANCE METRIC:")
            print(f"Complete Workflow Time: {perf['execution_time']:.3f}s")
            print(f"Target: <{performance_targets['max_total_time']}s")
            print(f"Status: {'✅ PASS' if perf['execution_time'] <= performance_targets['max_total_time'] else '❌ FAIL'}")
            print(f"Records Processed: {workflow_result['records_processed']}")
            print(f"Memory Used: {perf['memory_used']:.1f}MB")

        finally:
            Path(temp_file.name).unlink()

    @pytest.mark.performance
    def test_memory_scaling_performance(self, performance_targets):
        """Test memory usage scales appropriately with data size"""
        data_sizes = [100, 500, 1000]  # Different data sizes
        memory_results = []

        for size in data_sizes:
            # Generate test data
            test_data = self._generate_large_dataset(size)
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
            test_data.to_csv(temp_file.name, index=False)
            temp_file.close()

            try:
                # Measure memory usage
                perf = self.measure_performance(CBSCDataLoader, temp_file.name)

                memory_results.append({
                    'size': size,
                    'memory_used': perf['memory_used'],
                    'execution_time': perf['execution_time']
                })

            finally:
                Path(temp_file.name).unlink()

        # Check memory scaling (should be roughly linear)
        if len(memory_results) >= 2:
            size_ratio = memory_results[-1]['size'] / memory_results[0]['size']
            memory_ratio = memory_results[-1]['memory_used'] / max(memory_results[0]['memory_used'], 1)

            # Memory usage should not scale exponentially
            assert memory_ratio <= size_ratio * 2, \
                f"Memory scaling too aggressive: {memory_ratio:.2f}x for {size_ratio:.2f}x data increase"

            print(f"Memory Scaling Results:")
            for result in memory_results:
                print(f"  {result['size']} records: {result['memory_used']:.1f}MB, {result['execution_time']:.3f}s")

    @pytest.mark.performance
    def test_concurrent_processing_performance(self, performance_targets):
        """Test concurrent processing performance"""
        import threading
        import queue

        # Create test data
        test_data = self._generate_large_dataset(200)
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        test_data.to_csv(temp_file.name, index=False)
        temp_file.close()

        try:
            def worker_function():
                """Worker function for concurrent testing"""
                loader = CBSCDataLoader(temp_file.name)
                return loader.load_sentiment_data()

            # Test sequential processing
            sequential_start = time.time()
            sequential_results = []
            for _ in range(3):
                result = worker_function()
                sequential_results.append(result)
            sequential_time = time.time() - sequential_start

            # Test concurrent processing
            concurrent_start = time.time()
            concurrent_results = []
            threads = []

            for _ in range(3):
                thread = threading.Thread(target=lambda: concurrent_results.append(worker_function()))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            concurrent_time = time.time() - concurrent_start

            # Concurrent should be faster (or at least not significantly slower)
            speedup = sequential_time / max(concurrent_time, 0.001)

            print(f"Concurrent Processing Results:")
            print(f"  Sequential: {sequential_time:.3f}s")
            print(f"  Concurrent: {concurrent_time:.3f}s")
            print(f"  Speedup: {speedup:.2f}x")

            # Should have some benefit from concurrency
            assert speedup >= 0.8, f"Concurrent processing too slow: {speedup:.2f}x speedup"
            assert len(concurrent_results) == 3, "All concurrent operations should complete"

        finally:
            Path(temp_file.name).unlink()

    def _generate_large_dataset(self, num_records: int) -> pd.DataFrame:
        """Generate large test dataset for performance testing"""
        np.random.seed(42)  # For reproducible tests

        dates = pd.date_range('2020-01-01', periods=num_records, freq='D')

        return pd.DataFrame({
            'Date': dates,
            'Bull_Ratio': np.random.beta(2, 2, num_records),
            'Bull_Bear_Ratio': np.random.uniform(0.5, 2.0, num_records),
            'Bull_Turnover_HKD': np.random.uniform(1e6, 1e7, num_records),
            'Bear_Turnover_HKD': np.random.uniform(1e6, 1e7, num_records),
            'Afternoon_Close': 25000 + np.cumsum(np.random.randn(num_records) * 100),
            'Daily_Return': np.random.randn(num_records) * 0.02,
            'Signal': np.random.choice([-1, 0, 1], num_records),
            'Sentiment_Level': np.random.choice(['EXTREME BULL', 'MOD BULL', 'NEUTRAL', 'MOD BEAR', 'EXTREME BEAR'], num_records)
        })

    @pytest.mark.performance
    def test_performance_regression_detection(self, performance_targets):
        """Test to establish baseline for performance regression detection"""
        # This test establishes baseline metrics for future regression testing
        baseline_metrics = {}

        # Test data loading baseline
        test_data = self._generate_large_dataset(300)
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        test_data.to_csv(temp_file.name, index=False)
        temp_file.close()

        try:
            loader = CBSCDataLoader(temp_file.name)
            perf = self.measure_performance(loader.load_sentiment_data)
            baseline_metrics['data_loading'] = {
                'time': perf['execution_time'],
                'memory': perf['memory_used'],
                'throughput': perf['throughput']
            }

            # Test signal generation baseline
            generator = CBSCSignalGenerator()
            features_df = self._create_mock_features_data(200)
            perf = self.measure_performance(generator.generate_multiple_strategies, features_df)
            baseline_metrics['signal_generation'] = {
                'time': perf['execution_time'],
                'memory': perf['memory_used'],
                'strategies': len(perf['result']) if perf['success'] else 0
            }

            print("Baseline Performance Metrics Established:")
            for component, metrics in baseline_metrics.items():
                print(f"  {component}: {metrics}")

            # Save baseline for future regression testing
            baseline_path = Path("performance_baseline.json")
            import json
            with open(baseline_path, 'w') as f:
                json.dump(baseline_metrics, f, indent=2)

            print(f"Baseline saved to {baseline_path}")

            # Verify baseline meets targets
            assert baseline_metrics['data_loading']['time'] <= performance_targets['max_data_loading'], \
                "Data loading baseline exceeds target"
            assert baseline_metrics['signal_generation']['time'] <= performance_targets['max_signal_generation'], \
                "Signal generation baseline exceeds target"

        finally:
            Path(temp_file.name).unlink()

    def _create_mock_features_data(self, num_records: int) -> pd.DataFrame:
        """Create mock features data for testing"""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=num_records, freq='D')

        return pd.DataFrame({
            'Date': dates,
            'close': 25000 + np.cumsum(np.random.randn(num_records) * 100),
            'Returns': np.random.randn(num_records) * 0.02,
            'MA5': 25000 + np.cumsum(np.random.randn(num_records) * 50),
            'MA20': 25000 + np.cumsum(np.random.randn(num_records) * 20),
            'RSI': 50 + np.random.randn(num_records) * 10,
            'Bull_Ratio': np.random.beta(2, 2, num_records),
            'Bull_Bear_Ratio': np.random.uniform(0.5, 2.0, num_records),
            'Bull_Turnover_HKD': np.random.uniform(1e6, 1e7, num_records),
            'Bear_Turnover_HKD': np.random.uniform(1e6, 1e7, num_records),
            'Total_Turnover': np.random.uniform(2e6, 2e7, num_records),
            'Sentiment_Strength': np.random.randn(num_records) * 0.3,
            'Sentiment_Score': np.random.uniform(0, 100, num_records),
            'Sentiment_Level': np.random.choice(['EXTREME BULL', 'MOD BULL', 'NEUTRAL', 'MOD BEAR', 'EXTREME BEAR'], num_records)
        })
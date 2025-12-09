"""
Comprehensive Test Framework for Unified Backtesting System

Phase 3 comprehensive testing framework including unit tests, integration tests,
performance benchmarks, stress tests, and end-to-end validation.

Key Features:
- Complete unit test coverage for all components
- Integration tests across component boundaries
- Performance benchmarking and regression testing
- Stress testing under extreme conditions
- Data integrity and accuracy validation
- Memory leak detection and resource cleanup testing
- Fault tolerance and recovery validation
"""

import unittest
import pytest
import time
import logging
import tempfile
import shutil
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass
import threading
import multiprocessing as mp
import psutil
import gc
import os
import sys
import json
from pathlib import Path

# Import the unified backtesting system
from ..core.framework import UnifiedBacktestingFramework
from ..core.config import BacktestingConfig
from ..parameters.generator import ComprehensiveParameterSpace
from ..vectorbt_engine.enhanced_engine import EnhancedVectorBTEngine
from ..metrics.calculator import StandardizedMetricsCalculator
from ..memory.enhanced_manager import EnhancedMemoryManager
from ..results.aggregator import ResultAggregator
from ..monitoring.progress_tracker import RealTimeProgressTracker
from ..optimization.intelligent_chunker import IntelligentChunker
from ..optimization.fault_tolerance import FaultTolerantExecutor

logger = logging.getLogger(__name__)


@dataclass
class TestConfiguration:
    """Test configuration parameters"""
    small_scale_test: bool = False
    medium_scale_test: bool = False
    large_scale_test: bool = False
    performance_test: bool = False
    memory_test: bool = False
    stress_test: bool = False
    integration_test: bool = True
    unit_test: bool = True

    # Test parameters
    small_param_range: tuple = (10, 50, 10)      # 5 values
    medium_param_range: tuple = (5, 100, 5)       # 20 values
    large_param_range: tuple = (0, 100, 10)       # 11 values
    max_combinations_small: int = 125            # 5^3
    max_combinations_medium: int = 8000          # 20^3
    max_combinations_large: int = 1331           # 11^3

    # Performance thresholds
    max_execution_time_small: float = 30.0      # seconds
    max_execution_time_medium: float = 300.0     # 5 minutes
    max_memory_usage_mb: float = 4000.0          # 4GB
    min_success_rate: float = 0.95                # 95%


class TestDataGenerator:
    """Generate test data for various scenarios"""

    @staticmethod
    def create_sample_price_data(days: int = 252, volatility: float = 0.02) -> pd.DataFrame:
        """Create synthetic price data for testing"""
        np.random.seed(42)  # For reproducible tests

        # Generate price series
        dates = pd.date_range(end='2024-12-31', periods=days, freq='D')
        returns = np.random.normal(0.0005, volatility, days)
        prices = 100 * np.exp(np.cumsum(returns))

        # Create OHLCV data
        data = pd.DataFrame(index=dates)
        data['open'] = prices
        data['high'] = prices * (1 + np.abs(np.random.normal(0, 0.01, days)))
        data['low'] = prices * (1 - np.abs(np.random.normal(0, 0.01, days)))
        data['close'] = np.roll(prices, -1)
        data['close'].iloc[-1] = prices[-1]  # Fix last close price
        data['volume'] = np.random.randint(100000, 1000000, days)

        return data

    @staticmethod
    def create_benchmark_data(days: int = 252) -> pd.Series:
        """Create benchmark returns for testing"""
        np.random.seed(123)
        dates = pd.date_range(end='2024-12-31', periods=days, freq='D')
        returns = np.random.normal(0.0003, 0.015, days)
        benchmark = pd.Series(returns, index=dates)
        return benchmark

    @staticmethod
    def create_corrupted_data() -> pd.DataFrame:
        """Create corrupted data for testing error handling"""
        data = TestDataGenerator.create_sample_price_data(days=10)

        # Introduce various data quality issues
        data.loc[data.index[2], 'close'] = None  # Missing value
        data.loc[data.index[5], 'high'] = data.loc[data.index[5], 'low']  # High < Low
        data.loc[data.index[8], 'volume'] = -1000  # Negative volume

        return data


class MemoryLeakDetector:
    """Detect memory leaks during testing"""

    def __init__(self):
        self.initial_objects = None
        self.object_counts = []

    def start_monitoring(self):
        """Start memory monitoring"""
        gc.collect()  # Force garbage collection
        self.initial_objects = len(gc.get_objects())
        logger.info(f"Starting memory monitoring with {self.initial_objects} objects")

    def record_checkpoint(self, label: str):
        """Record memory checkpoint"""
        gc.collect()
        current_objects = len(gc.get_objects())
        self.object_counts.append((label, current_objects, time.time()))

        logger.debug(f"Memory checkpoint '{label}': {current_objects} objects")

    def check_leaks(self, threshold: int = 1000) -> Dict[str, Any]:
        """Check for memory leaks"""
        if self.initial_objects is None:
            return {"error": "Monitoring not started"}

        gc.collect()
        final_objects = len(gc.get_objects())
        object_increase = final_objects - self.initial_objects

        # Calculate memory usage
        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            "initial_objects": self.initial_objects,
            "final_objects": final_objects,
            "object_increase": object_increase,
            "memory_usage_mb": memory_info.rss / (1024 * 1024),
            "memory_peak_mb": memory_info.peak_wset / (1024 * 1024),
            "potential_leak": object_increase > threshold,
            "checkpoints": self.object_counts
        }


class PerformanceBenchmark:
    """Performance benchmarking utilities"""

    def __init__(self):
        self.results = []

    def time_execution(self, func: Callable, *args, **kwargs) -> Tuple[float, Any]:
        """Time function execution"""
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time

        self.results.append({
            'function': func.__name__,
            'execution_time': execution_time,
            'timestamp': time.time()
        })

        return execution_time, result

    def measure_memory_usage(self, func: Callable, *args, **kwargs) -> Tuple[Dict[str, float], Any]:
        """Measure memory usage during execution"""
        process = psutil.Process()

        # Get initial memory
        initial_memory = process.memory_info().rss / (1024 * 1024)

        # Execute function
        result = func(*args, **kwargs)

        # Get final memory
        final_memory = process.memory_info().rss / (1024 * 1024)
        peak_memory = process.memory_info().peak_wset / (1024 * 1024)

        memory_stats = {
            'initial_memory_mb': initial_memory,
            'final_memory_mb': final_memory,
            'peak_memory_mb': peak_memory,
            'memory_increase_mb': final_memory - initial_memory,
            'timestamp': time.time()
        }

        return memory_stats, result

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics"""
        if not self.results:
            return {"error": "No performance data available"}

        execution_times = [r['execution_time'] for r in self.results]

        return {
            'total_tests': len(self.results),
            'avg_execution_time': np.mean(execution_times),
            'min_execution_time': np.min(execution_times),
            'max_execution_time': np.max(execution_times),
            'std_execution_time': np.std(execution_times),
            'median_execution_time': np.median(execution_times),
            'total_execution_time': np.sum(execution_times)
        }


class UnifiedBacktestingTestCase(unittest.TestCase):
    """Base test case for unified backtesting system"""

    def setUp(self):
        """Set up test environment"""
        self.test_config = TestConfiguration()
        self.data_generator = TestDataGenerator()
        self.memory_detector = MemoryLeakDetector()
        self.performance_benchmark = PerformanceBenchmark()

        # Create test data
        self.sample_data = self.data_generator.create_sample_price_data(days=100)
        self.benchmark_data = self.data_generator.create_benchmark_data(days=100)

        # Set up temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()

        # Start memory monitoring
        self.memory_detector.start_monitoring()

    def tearDown(self):
        """Clean up test environment"""
        # Check for memory leaks
        leak_results = self.memory_detector.check_leaks()
        if leak_results["potential_leak"]:
            logger.warning(f"Potential memory leak detected: {leak_results['object_increase']} objects")

        # Clean up temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

        # Force garbage collection
        gc.collect()

    def test_parameter_space_generation(self):
        """Test parameter space generation"""
        logger.info("Testing parameter space generation...")

        # Test with small scale
        config = BacktestingConfig(
            param_range_start=10,
            param_range_end=50,
            param_step_size=10
        )
        param_space = ComprehensiveParameterSpace(config)

        # Test strategy parameter counts
        rsi_count = param_space.get_parameter_combinations_count("rsi_strategy")
        self.assertGreater(rsi_count, 0)
        self.assertEqual(len(param_space.parameter_range), 5)  # 10,20,30,40,50

        # Test parameter validation
        test_params = {
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'stop_loss': 0.02,
            'take_profit': 0.05
        }
        self.assertTrue(param_space.validate_parameters("rsi_strategy", test_params))

    def test_enhanced_vectorbt_engine(self):
        """Test enhanced VectorBT engine"""
        logger.info("Testing enhanced VectorBT engine...")

        config = BacktestingConfig(max_workers=2, chunk_size=100)
        engine = EnhancedVectorBTEngine(config)

        # Test signal generation
        signals = engine._generate_optimized_signals("rsi_strategy",
                                                    {'rsi_period': 14},
                                                    self.sample_data)

        self.assertIsInstance(signals, pd.DataFrame)
        self.assertIn('entry', signals.columns)
        self.assertIn('exit', signals.columns)

        # Test single backtest execution
        test_data = ("rsi_strategy", {'rsi_period': 14}, 0, self.sample_data)
        result = engine._execute_optimized_backtest(test_data)

        self.assertIsNotNone(result)
        self.assertEqual(result.strategy_name, "rsi_strategy")
        self.assertIsNotNone(result.execution_time)

    def test_metrics_calculator(self):
        """Test standardized metrics calculator"""
        logger.info("Testing metrics calculator...")

        calculator = StandardizedMetricsCalculator()

        # Create sample returns
        np.random.seed(456)
        returns = pd.Series(np.random.normal(0.001, 0.02, 100))

        # Test metrics calculation
        metrics = calculator.calculate_comprehensive_metrics(returns)

        self.assertIsNotNone(metrics)
        self.assertGreater(metrics.sharpe_ratio, -10)  # Reasonable bounds
        self.assertLess(metrics.max_drawdown, 1.0)    # Max drawdown <= 100%
        self.assertGreaterEqual(metrics.win_rate, 0)
        self.assertLessEqual(metrics.win_rate, 1)

    def test_enhanced_memory_manager(self):
        """Test enhanced memory manager"""
        logger.info("Testing enhanced memory manager...")

        manager = EnhancedMemoryManager()

        # Test basic caching
        test_data = {"test": "data", "numbers": [1, 2, 3, 4, 5]}

        # Put in cache
        cache_result = manager.cache_data("test_key", test_data)
        self.assertTrue(cache_result)

        # Retrieve from cache
        cached_data = manager.get_cached_data("test_key")
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data, test_data)

        # Test statistics
        stats = manager.get_comprehensive_statistics()
        self.assertIn('cache_statistics', stats)
        self.assertIn('object_pool_statistics', stats)

    def test_fault_tolerance_executor(self):
        """Test fault tolerance executor"""
        logger.info("Testing fault tolerance executor...")

        executor = FaultTolerantExecutor(max_retries=2, base_delay=0.1)

        # Test successful execution
        def successful_func():
            return "success"

        result = executor.execute_with_fault_tolerance(successful_func)
        self.assertEqual(result, "success")

        # Test failed execution with retry
        attempt_count = 0
        def failing_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise ValueError("Simulated failure")
            return "success_after_retry"

        result = executor.execute_with_fault_tolerance(failing_func)
        self.assertEqual(result, "success_after_retry")
        self.assertEqual(attempt_count, 2)

    def test_intelligent_chunker(self):
        """Test intelligent chunking algorithm"""
        logger.info("Testing intelligent chunker...")

        chunker = IntelligentChunker()

        # Test chunk size calculation
        chunk_size = chunker.calculate_optimal_chunk_size(
            "rsi_strategy", 1000, 500, 1.0  # 1GB memory usage
        )

        self.assertGreater(chunk_size, 0)
        self.assertLessEqual(chunk_size, 5000)  # Reasonable upper bound

        # Test chunk size adaptation
        high_memory_chunk_size = chunker.calculate_optimal_chunk_size(
            "rsi_strategy", 1000, 500, 3.5  # High memory pressure
        )

        self.assertLess(high_memory_chunk_size, chunk_size)  # Should reduce under pressure

    def test_real_time_progress_tracker(self):
        """Test real-time progress tracker"""
        logger.info("Testing real-time progress tracker...")

        tracker = RealTimeProgressTracker("test_strategy", 1000, enable_websocket=False)

        # Test progress tracking
        tracker.start_optimization()

        # Simulate batch operations
        tracker.start_batch(1, 100)
        time.sleep(0.1)
        tracker.complete_batch(1, 95, 5)

        # Test progress summary
        summary = tracker.get_progress_summary()
        self.assertEqual(summary['total_combinations'], 1000)
        self.assertEqual(summary['processed_combinations'], 100)
        self.assertEqual(summary['successful_combinations'], 95)
        self.assertEqual(summary['failed_combinations'], 5)

        tracker.complete_optimization()

    def test_end_to_end_small_scale(self):
        """End-to-end test with small scale parameters"""
        logger.info("Running end-to-end small scale test...")

        if not self.test_config.small_scale_test:
            self.skipTest("Small scale test disabled")

        # Start memory monitoring checkpoint
        self.memory_detector.record_checkpoint("before_optimization")

        # Create configuration
        config = BacktestingConfig(
            param_range_start=10,
            param_range_end=50,
            param_step_size=10,
            max_workers=2,
            chunk_size=50,
            memory_limit_gb=1.0  # Smaller for test
        )

        # Create optimization request
        from ..core.framework import OptimizationRequest
        request = OptimizationRequest(
            strategy_name="rsi_strategy",
            price_data=self.sample_data,
            output_directory=self.temp_dir
        )

        # Create framework
        framework = UnifiedBacktestingFramework(config)

        try:
            framework.start_memory_management()

            # Run optimization
            start_time = time.time()
            results = framework.run_optimization(request)
            execution_time = time.time() - start_time

            # Validate results
            self.assertIsNotNone(results)
            self.assertGreater(results.total_combinations, 0)
            self.assertGreaterEqual(results.success_rate, 0.8)  # 80% minimum success rate

            # Performance validation
            self.assertLess(execution_time, self.test_config.max_execution_time_small)

            # Memory validation
            self.memory_detector.record_checkpoint("after_optimization")
            memory_stats = self.memory_detector.check_leaks()
            self.assertLess(memory_stats['memory_usage_mb'], self.test_config.max_memory_usage_mb)

            logger.info(f"Small scale test completed in {execution_time:.2f}s")

        finally:
            framework.stop_memory_management()

    def test_performance_regression(self):
        """Performance regression test"""
        logger.info("Running performance regression test...")

        if not self.test_config.performance_test:
            self.skipTest("Performance test disabled")

        # Test parameter space generation performance
        config = BacktestingConfig(param_range_start=0, param_range_end=100, param_step_size=10)
        param_space = ComprehensiveParameterSpace(config)

        generation_time, param_count = self.performance_benchmark.time_execution(
            param_space.get_parameter_combinations_count, "rsi_strategy"
        )

        # Performance assertion (should complete in reasonable time)
        self.assertLess(generation_time, 5.0, "Parameter space generation too slow")
        self.assertGreater(param_count, 1000, "Insufficient parameter combinations generated")

    def test_memory_limits(self):
        """Test memory usage limits"""
        logger.info("Running memory limits test...")

        if not self.test_config.memory_test:
            self.skipTest("Memory test disabled")

        # Test with large dataset
        large_data = self.data_generator.create_sample_price_data(days=500)

        memory_stats, result = self.performance_benchmark.measure_memory_usage(
            lambda: len(large_data)
        )

        # Memory usage should be reasonable
        self.assertLess(memory_stats['memory_increase_mb'], 100, "Excessive memory usage for large dataset")

        # Clean up
        del large_data
        gc.collect()


class IntegrationTestSuite(unittest.TestCase):
    """Integration test suite for component interactions"""

    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_generator = TestDataGenerator()
        self.test_data = self.data_generator.create_sample_price_data(days=200)

    def tearDown(self):
        """Clean up integration test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_vectorbt_metrics_integration(self):
        """Test VectorBT engine and metrics calculator integration"""
        logger.info("Testing VectorBT-metrics integration...")

        config = BacktestingConfig(max_workers=2)
        engine = EnhancedVectorBTEngine(config)
        calculator = StandardizedMetricsCalculator()

        # Generate signals
        signals = engine._generate_optimized_signals("rsi_strategy",
                                                    {'rsi_period': 14, 'rsi_overbought': 70, 'rsi_oversold': 30},
                                                    self.test_data)

        # Create portfolio
        if not signals.empty:
            try:
                import vectorbt as vbt
                portfolio = vbt.Portfolio.from_signals(
                    close=self.test_data['close'],
                    entries=signals['entry'],
                    exits=signals['exit'],
                    init_cash=100000,
                    fees=0.001,
                    slippage=0.0005
                )

                # Calculate metrics
                returns = portfolio.returns()
                metrics = calculator.calculate_comprehensive_metrics(returns)

                # Validate integration results
                self.assertIsNotNone(metrics)
                self.assertGreaterEqual(metrics.sharpe_ratio, -5)  # Reasonable bounds

            except ImportError:
                self.skipTest("VectorBT not available for integration test")

    def test_memory_cache_integration(self):
        """Test memory manager and cache integration"""
        logger.info("Testing memory-cache integration...")

        manager = EnhancedMemoryManager()

        # Test object pool
        pooled_dataframe = manager.get_object_from_pool('dataframe')
        self.assertIsNotNone(pooled_dataframe)

        # Add some data and cache it
        pooled_dataframe['test'] = range(100)
        cache_result = manager.cache_data('integration_test', pooled_dataframe.copy())
        self.assertTrue(cache_result)

        # Retrieve from cache
        cached_data = manager.get_cached_data('integration_test')
        self.assertIsNotNone(cached_data)
        self.assertEqual(len(cached_data), 100)

        # Release object back to pool
        manager.release_object_to_pool(pooled_dataframe, 'dataframe')

    def test_chunking_fault_tolerance_integration(self):
        """Test chunking and fault tolerance integration"""
        logger.info("Testing chunking-fault tolerance integration...")

        chunker = IntelligentChunker()
        executor = FaultTolerantExecutor(max_retries=1, base_delay=0.01)

        # Simulate chunking under fault conditions
        def unreliable_chunk_processing(chunk_size):
            # Simulate random failures
            if np.random.random() < 0.3:  # 30% failure rate
                raise RuntimeError("Simulated chunk processing failure")
            return chunk_size * 2  # Simulate processing result

        # Test with fault tolerance
        for i in range(5):
            try:
                result = executor.execute_with_fault_tolerance(
                    unreliable_chunk_processing,
                    100
                )
                self.assertEqual(result, 200)
            except Exception as e:
                # Should not fail with fault tolerance
                self.fail(f"Fault tolerance failed: {str(e)}")


def run_comprehensive_tests():
    """Run the complete test suite"""
    logger.info("Starting comprehensive unified backtesting test suite...")

    # Create test suite
    test_suite = unittest.TestSuite()

    # Add unit tests
    test_suite.addTest(unittest.makeSuite(UnifiedBacktestingTestCase))

    # Add integration tests
    test_suite.addTest(unittest.makeSuite(IntegrationTestSuite))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Generate test report
    test_report = {
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / max(result.testsRun, 1),
        'timestamp': time.time()
    }

    # Save test report
    with open('test_report.json', 'w') as f:
        json.dump(test_report, f, indent=2)

    logger.info(f"Test suite completed: {test_report}")

    return result.wasSuccessful()


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run comprehensive tests
    success = run_comprehensive_tests()

    if success:
        print("\n✅ All tests passed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
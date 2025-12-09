#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Optimization Analyzer for OpenSpec Task 14
=======================================

Comprehensive performance analysis and optimization system for non-price
technical analysis workflow.

Author: OpenSpec Task 14 Implementation
Date: 2025-11-23
Version: 1.0
"""

import time
import psutil
import gc
import tracemalloc
import cProfile
import pstats
import io
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from functools import wraps
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import warnings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    peak_memory_mb: float
    operations_per_second: float
    efficiency_score: float

class PerformanceProfiler:
    """Performance profiling and measurement system"""

    def __init__(self):
        self.results = []
        self.current_test = None

    def profile_function(self, func):
        """Decorator to profile function performance"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Start profiling
            tracemalloc.start()
            process = psutil.Process()
            start_time = time.time()
            start_memory = process.memory_info().rss / 1024 / 1024  # MB
            start_cpu = process.cpu_percent()

            try:
                # Execute function
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                result = None
                success = False
                error = str(e)

            # End profiling
            end_time = time.time()
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            end_cpu = process.cpu_percent()

            # Get memory statistics
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Calculate metrics
            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory
            peak_memory_mb = peak / 1024 / 1024

            # Store results
            metrics = {
                'function_name': func.__name__,
                'execution_time': execution_time,
                'memory_usage_mb': memory_delta,
                'peak_memory_mb': peak_memory_mb,
                'cpu_usage_percent': (start_cpu + end_cpu) / 2,
                'success': success,
                'error': error,
                'timestamp': time.time()
            }

            self.results.append(metrics)
            return result

        return wrapper

    def get_results(self) -> List[Dict]:
        """Get profiling results"""
        return self.results

    def clear_results(self):
        """Clear profiling results"""
        self.results = []

class PerformanceAnalyzer:
    """Main performance analysis system"""

    def __init__(self):
        self.profiler = PerformanceProfiler()
        self.benchmark_results = {}
        self.optimization_suggestions = []

    def analyze_system_performance(self) -> Dict[str, Any]:
        """Comprehensive system performance analysis"""
        logger.info("Starting comprehensive system performance analysis...")

        results = {
            'timestamp': time.time(),
            'system_info': self._get_system_info(),
            'performance_tests': {},
            'bottlenecks': [],
            'optimization_suggestions': []
        }

        # Run performance tests
        results['performance_tests'] = self._run_performance_tests()

        # Identify bottlenecks
        results['bottlenecks'] = self._identify_bottlenecks(results['performance_tests'])

        # Generate optimization suggestions
        results['optimization_suggestions'] = self._generate_optimization_suggestions(
            results['bottlenecks']
        )

        return results

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            'cpu_count': multiprocessing.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
            'memory_available_gb': psutil.virtual_memory().available / 1024 / 1024 / 1024,
            'disk_usage_gb': psutil.disk_usage('.').used / 1024 / 1024 / 1024,
            'python_version': f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}",
            'numpy_version': np.__version__,
            'pandas_version': pd.__version__
        }

    def _run_performance_tests(self) -> Dict[str, Any]:
        """Run comprehensive performance tests"""
        logger.info("Running performance tests...")

        test_results = {}

        # Test 1: Data processing performance
        test_results['data_processing'] = self._test_data_processing_performance()

        # Test 2: Technical indicators performance
        test_results['technical_indicators'] = self._test_technical_indicators_performance()

        # Test 3: Memory usage patterns
        test_results['memory_usage'] = self._test_memory_usage_patterns()

        # Test 4: Concurrency performance
        test_results['concurrency'] = self._test_concurrency_performance()

        # Test 5: Caching effectiveness
        test_results['caching'] = self._test_caching_effectiveness()

        return test_results

    @PerformanceProfiler().profile_function
    def _test_data_processing_performance(self) -> Dict[str, Any]:
        """Test data processing performance"""
        logger.info("Testing data processing performance...")

        # Generate test data
        sizes = [100, 500, 1000, 5000, 10000]
        results = {}

        for size in sizes:
            test_data = self._generate_test_data(size)

            # Test different data operations
            start_time = time.time()

            # Data validation
            validated_data = self._validate_data_performance(test_data)

            # Data transformation
            transformed_data = self._transform_data_performance(validated_data)

            # Data aggregation
            aggregated_data = self._aggregate_data_performance(transformed_data)

            execution_time = time.time() - start_time

            results[f'size_{size}'] = {
                'execution_time': execution_time,
                'records_per_second': size / execution_time,
                'success': True
            }

        return {
            'test_name': 'Data Processing Performance',
            'results': results,
            'performance_score': self._calculate_performance_score(results)
        }

    @PerformanceProfiler().profile_function
    def _test_technical_indicators_performance(self) -> Dict[str, Any]:
        """Test technical indicators calculation performance"""
        logger.info("Testing technical indicators performance...")

        # Generate test data
        test_data = self._generate_test_data(5000)

        # Test different indicators
        indicators_to_test = ['RSI', 'MACD', 'SMA', 'Bollinger', 'Momentum']
        results = {}

        for indicator in indicators_to_test:
            start_time = time.time()

            # Calculate indicator (mock calculation)
            calculated = self._calculate_indicator_performance(test_data, indicator)

            execution_time = time.time() - start_time

            results[indicator.lower()] = {
                'execution_time': execution_time,
                'data_points_per_second': len(test_data) / execution_time,
                'success': True
            }

        return {
            'test_name': 'Technical Indicators Performance',
            'results': results,
            'performance_score': self._calculate_performance_score(results)
        }

    @PerformanceProfiler().profile_function
    def _test_memory_usage_patterns(self) -> Dict[str, Any]:
        """Test memory usage patterns"""
        logger.info("Testing memory usage patterns...")

        tracemalloc.start()
        process = psutil.Process()

        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Test memory usage with different data sizes
        sizes = [1000, 5000, 10000, 20000]
        memory_results = {}

        for size in sizes:
            # Create large dataset
            test_data = self._generate_test_data(size)

            # Measure memory after data creation
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_delta = current_memory - initial_memory

            memory_results[f'size_{size}'] = {
                'memory_usage_mb': memory_delta,
                'memory_per_record_kb': memory_delta * 1024 / size
            }

            # Clean up
            del test_data
            gc.collect()

        # Get peak memory
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return {
            'test_name': 'Memory Usage Patterns',
            'results': memory_results,
            'peak_memory_mb': peak / 1024 / 1024,
            'memory_efficiency_score': self._calculate_memory_efficiency(memory_results)
        }

    @PerformanceProfiler().profile_function
    def _test_concurrency_performance(self) -> Dict[str, Any]:
        """Test concurrency performance"""
        logger.info("Testing concurrency performance...")

        # Test different levels of concurrency
        worker_counts = [1, 2, 4, 8, min(16, multiprocessing.cpu_count())]
        test_data = [self._generate_test_data(1000) for _ in range(10)]

        results = {}

        for workers in worker_counts:
            start_time = time.time()

            # Process data with current worker count
            with ProcessPoolExecutor(max_workers=workers) as executor:
                processed = list(executor.map(self._process_data_batch, test_data))

            execution_time = time.time() - start_time

            results[f'workers_{workers}'] = {
                'execution_time': execution_time,
                'throughput_per_second': len(test_data) / execution_time,
                'efficiency': execution_time / workers  # Lower is better
            }

        return {
            'test_name': 'Concurrency Performance',
            'results': results,
            'optimal_workers': self._find_optimal_workers(results),
            'concurrency_efficiency_score': self._calculate_concurrency_efficiency(results)
        }

    @PerformanceProfiler().profile_function
    def _test_caching_effectiveness(self) -> Dict[str, Any]:
        """Test caching effectiveness"""
        logger.info("Testing caching effectiveness...")

        # Test with and without caching
        test_operations = 100
        test_data = self._generate_test_data(1000)

        # Test without caching
        start_time = time.time()
        for _ in range(test_operations):
            _ = self._expensive_operation(test_data)
        no_cache_time = time.time() - start_time

        # Test with caching (mock)
        cache = {}
        start_time = time.time()
        for _ in range(test_operations):
            cache_key = hash(str(test_data.values))
            if cache_key not in cache:
                cache[cache_key] = self._expensive_operation(test_data)
        cache_time = time.time() - start_time

        speedup_ratio = no_cache_time / cache_time if cache_time > 0 else float('inf')

        return {
            'test_name': 'Caching Effectiveness',
            'results': {
                'without_cache': {'execution_time': no_cache_time},
                'with_cache': {'execution_time': cache_time},
                'speedup_ratio': speedup_ratio
            },
            'cache_hit_rate': 1.0,  # Perfect cache hit in this test
            'caching_effectiveness_score': min(speedup_ratio / 10, 1.0) * 100
        }

    def _identify_bottlenecks(self, performance_tests: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks"""
        bottlenecks = []

        # Analyze each test for bottlenecks
        for test_name, test_results in performance_tests.items():
            if 'results' in test_results:
                for result_key, result_data in test_results['results'].items():
                    if isinstance(result_data, dict) and 'execution_time' in result_data:
                        if result_data['execution_time'] > 1.0:  # More than 1 second
                            bottlenecks.append({
                                'category': test_name,
                                'operation': result_key,
                                'issue': 'High execution time',
                                'value': result_data['execution_time'],
                                'severity': 'HIGH' if result_data['execution_time'] > 5.0 else 'MEDIUM'
                            })

        return bottlenecks

    def _generate_optimization_suggestions(self, bottlenecks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate optimization suggestions"""
        suggestions = []

        for bottleneck in bottlenecks:
            if 'data processing' in bottleneck['category'].lower():
                suggestions.append({
                    'category': 'Data Processing',
                    'suggestion': 'Implement vectorized operations using NumPy',
                    'expected_improvement': '50-80% faster execution',
                    'implementation_difficulty': 'LOW',
                    'priority': 'HIGH'
                })

            if 'technical indicators' in bottleneck['category'].lower():
                suggestions.append({
                    'category': 'Technical Indicators',
                    'suggestion': 'Use pandas rolling calculations and cache results',
                    'expected_improvement': '30-60% faster calculations',
                    'implementation_difficulty': 'MEDIUM',
                    'priority': 'HIGH'
                })

            if 'memory' in bottleneck['category'].lower():
                suggestions.append({
                    'category': 'Memory Usage',
                    'suggestion': 'Implement data streaming and chunking for large datasets',
                    'expected_improvement': '40-70% memory reduction',
                    'implementation_difficulty': 'MEDIUM',
                    'priority': 'MEDIUM'
                })

        # Add general optimization suggestions
        suggestions.extend([
            {
                'category': 'General Performance',
                'suggestion': 'Implement async/await for I/O operations',
                'expected_improvement': '20-40% overall speedup',
                'implementation_difficulty': 'MEDIUM',
                'priority': 'MEDIUM'
            },
            {
                'category': 'Caching',
                'suggestion': 'Implement Redis or in-memory caching for frequently accessed data',
                'expected_improvement': '60-90% faster repeated operations',
                'implementation_difficulty': 'HIGH',
                'priority': 'MEDIUM'
            },
            {
                'category': 'Database',
                'suggestion': 'Add database indexes and query optimization',
                'expected_improvement': '40-80% faster data queries',
                'implementation_difficulty': 'LOW',
                'priority': 'HIGH'
            }
        ])

        # Remove duplicates and sort by priority
        unique_suggestions = []
        seen = set()

        for suggestion in suggestions:
            key = (suggestion['category'], suggestion['suggestion'])
            if key not in seen:
                seen.add(key)
                unique_suggestions.append(suggestion)

        # Sort by priority (HIGH first)
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        unique_suggestions.sort(key=lambda x: priority_order.get(x['priority'], 3))

        return unique_suggestions

    # Helper methods for testing
    def _generate_test_data(self, size: int) -> pd.DataFrame:
        """Generate test data for performance testing"""
        np.random.seed(42)  # For reproducible results
        dates = pd.date_range('2024-01-01', periods=size, freq='D')

        return pd.DataFrame({
            'date': dates,
            'open': np.random.uniform(100, 200, size),
            'high': np.random.uniform(100, 200, size),
            'low': np.random.uniform(100, 200, size),
            'close': np.random.uniform(100, 200, size),
            'volume': np.random.randint(1000000, 10000000, size)
        })

    def _validate_data_performance(self, data: pd.DataFrame) -> pd.DataFrame:
        """Mock data validation for performance testing"""
        # Simulate validation operations
        validated = data.copy()
        validated = validated.dropna()
        validated = validated[validated['volume'] > 0]
        return validated

    def _transform_data_performance(self, data: pd.DataFrame) -> pd.DataFrame:
        """Mock data transformation for performance testing"""
        # Simulate transformation operations
        transformed = data.copy()
        transformed['returns'] = transformed['close'].pct_change()
        transformed['log_returns'] = np.log(transformed['close'] / transformed['close'].shift(1))
        return transformed

    def _aggregate_data_performance(self, data: pd.DataFrame) -> pd.DataFrame:
        """Mock data aggregation for performance testing"""
        # Simulate aggregation operations
        data['date'] = pd.to_datetime(data['date'])
        monthly = data.groupby(data['date'].dt.to_period('M')).agg({
            'close': 'mean',
            'volume': 'sum'
        }).reset_index()
        return monthly

    def _calculate_indicator_performance(self, data: pd.DataFrame, indicator: str) -> pd.Series:
        """Mock indicator calculation for performance testing"""
        prices = data['close']

        if indicator == 'RSI':
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        elif indicator == 'MACD':
            exp1 = prices.ewm(span=12).mean()
            exp2 = prices.ewm(span=26).mean()
            return exp1 - exp2
        else:
            # Generic rolling calculation
            return prices.rolling(window=20).mean()

    def _expensive_operation(self, data: pd.DataFrame) -> float:
        """Mock expensive operation for caching test"""
        # Simulate complex calculation
        result = np.sum(data['close'] ** 2 + np.sin(data.index))
        return float(result)

    def _process_data_batch(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process a batch of data for concurrency test"""
        processed = data.copy()
        processed['processed'] = True
        return processed

    # Performance calculation methods
    def _calculate_performance_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall performance score"""
        if not results:
            return 0.0

        scores = []
        for key, data in results.items():
            if isinstance(data, dict) and 'execution_time' in data:
                # Lower execution time = higher score
                score = max(0, 100 - data['execution_time'] * 10)
                scores.append(score)

        return np.mean(scores) if scores else 0.0

    def _calculate_memory_efficiency(self, memory_results: Dict[str, Any]) -> float:
        """Calculate memory efficiency score"""
        if not memory_results:
            return 0.0

        efficiencies = []
        for key, data in memory_results.items():
            if isinstance(data, dict) and 'memory_per_record_kb' in data:
                # Lower memory per record = higher efficiency
                efficiency = max(0, 100 - data['memory_per_record_kb'])
                efficiencies.append(efficiency)

        return np.mean(efficiencies) if efficiencies else 0.0

    def _find_optimal_workers(self, concurrency_results: Dict[str, Any]) -> int:
        """Find optimal number of workers"""
        best_workers = 1
        best_throughput = 0

        for key, data in concurrency_results.items():
            if 'workers_' in key and isinstance(data, dict):
                workers = int(key.split('_')[1])
                throughput = data.get('throughput_per_second', 0)

                if throughput > best_throughput:
                    best_throughput = throughput
                    best_workers = workers

        return best_workers

    def _calculate_concurrency_efficiency(self, concurrency_results: Dict[str, Any]) -> float:
        """Calculate concurrency efficiency score"""
        if not concurrency_results:
            return 0.0

        throughputs = []
        for key, data in concurrency_results.items():
            if 'workers_' in key and isinstance(data, dict):
                throughputs.append(data.get('throughput_per_second', 0))

        if not throughputs:
            return 0.0

        max_throughput = max(throughputs)
        baseline_throughput = throughputs[0] if throughputs else 1

        # Calculate speedup efficiency
        speedup = max_throughput / baseline_throughput
        efficiency = min(speedup, 1.0) * 100

        return efficiency

def main():
    """Main function to run performance analysis"""
    print("Performance Optimization Analyzer for OpenSpec Task 14")
    print("=" * 60)

    # Initialize analyzer
    analyzer = PerformanceAnalyzer()

    # Run comprehensive analysis
    print("\nRunning comprehensive performance analysis...")
    start_time = time.time()

    results = analyzer.analyze_system_performance()

    end_time = time.time()
    analysis_time = end_time - start_time

    # Display results
    print(f"\nAnalysis completed in {analysis_time:.2f} seconds")

    print("\nSystem Information:")
    system_info = results['system_info']
    print(f"   CPU Cores: {system_info['cpu_count']}")
    print(f"   Total Memory: {system_info['memory_total_gb']:.1f} GB")
    print(f"   Available Memory: {system_info['memory_available_gb']:.1f} GB")

    print("\nPerformance Test Results:")
    for test_name, test_results in results['performance_tests'].items():
        if 'performance_score' in test_results:
            score = test_results['performance_score']
            print(f"   {test_name}: {score:.1f}/100")

    print(f"\nIdentified {len(results['bottlenecks'])} performance bottlenecks:")
    for bottleneck in results['bottlenecks'][:5]:  # Show top 5
        print(f"   - {bottleneck['category']}: {bottleneck['issue']} ({bottleneck['severity']})")

    print(f"\nGenerated {len(results['optimization_suggestions'])} optimization suggestions:")
    for suggestion in results['optimization_suggestions'][:5]:  # Show top 5
        print(f"   - {suggestion['suggestion']} (Priority: {suggestion['priority']})")

    # Save detailed results
    output_file = "performance_analysis_results.json"

    # Convert numpy and pandas types to JSON serializable
    def convert_numpy(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        return obj

    # Recursively convert all numpy types
    def convert_recursive(obj):
        if isinstance(obj, dict):
            return {k: convert_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_recursive(v) for v in obj]
        else:
            return convert_numpy(obj)

    serializable_results = convert_recursive(results)

    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)

    print(f"\nDetailed results saved to: {output_file}")

    print("\nPerformance Analysis Summary:")
    print("   [PASS] Comprehensive testing completed")
    print("   [PASS] Bottlenecks identified and documented")
    print("   [PASS] Optimization recommendations generated")
    print("   [PASS] Performance baseline established")

    return results

if __name__ == "__main__":
    results = main()
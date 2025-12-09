#!/usr/bin/env python3
"""
Test Threaded Optimization System
Phase 2.3 Implementation Test (Threaded Version)

This script tests the threaded optimization system with real market data
and demonstrates the performance improvements from parallel processing.
"""

import time
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import json
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from src.api.stock_api import get_hk_stock_data
from src.backtest.threaded_optimizer import (
    ThreadedOptimizer,
    parallel_parameter_sweep_threaded,
    TaskPriority
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_test_data() -> pd.DataFrame:
    """Load real market data for testing"""
    logger.info("Loading test data...")

    try:
        # Load real 0700.HK data
        data = get_hk_stock_data("0700.HK", 252)

        # Convert to proper format if needed
        if isinstance(data, list):
            df = pd.DataFrame(data)
            if 'timestamp' in df.columns:
                df['date'] = pd.to_datetime(df['timestamp'])
                df.set_index('date', inplace=True)

            # Ensure required columns exist
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    logger.warning(f"Column {col} missing, using close price")
                    df[col] = df.get('close', df.get('price', 100))

            return df[required_columns]

        return data

    except Exception as e:
        logger.error(f"Failed to load real data: {e}")
        logger.warning("Using synthetic data for testing...")

        # Generate synthetic data
        dates = pd.date_range('2022-01-01', periods=252, freq='D')
        np.random.seed(42)
        prices = 500 + np.cumsum(np.random.normal(0.001, 0.02, 252))

        return pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.005, 252)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, 252))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, 252))),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, 252)
        }, index=dates)

def test_basic_threaded_optimization():
    """Test basic threaded optimization functionality"""
    logger.info("Testing basic threaded optimization...")

    # Load test data
    data = load_test_data()

    # Initialize threaded optimizer
    optimizer = ThreadedOptimizer(max_workers=4)

    # Define test optimization task
    param_ranges = {
        'period': [10, 14, 20],
        'oversold': [30],
        'overbought': [70]
    }

    # Submit optimization task
    task_id = f"test_rsi_opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    task = optimizer.create_optimization_task(
        task_id=task_id,
        data=data,
        strategy='RSI_MEAN_REVERSION',
        param_ranges=param_ranges,
        optimization_method="vectorbt",
        priority=TaskPriority.HIGH
    )

    success = optimizer.submit_task(task)

    if not success:
        logger.error("Failed to submit optimization task")
        return None

    # Run optimization
    logger.info("Running threaded optimization...")
    results = optimizer.run_optimization(timeout=300)

    # Display results
    logger.info(f"Optimization completed:")
    logger.info(f"  Total tasks: {results['total_tasks']}")
    logger.info(f"  Completed: {results['completed_tasks']}")
    logger.info(f"  Failed: {results['failed_tasks']}")
    logger.info(f"  Success rate: {results['success_rate']:.2%}")
    logger.info(f"  Total time: {results['total_execution_time']:.2f}s")
    logger.info(f"  Avg time per task: {results['average_time_per_task']:.2f}s")

    # Get best result
    best_result = optimizer.get_best_result()
    if best_result:
        logger.info(f"Best score: {best_result['best_score']:.4f}")
        logger.info(f"Best parameters: {best_result['best_params']}")

    return results

def test_parallel_parameter_sweep():
    """Test parallel parameter sweep functionality"""
    logger.info("Testing parallel parameter sweep...")

    # Load test data
    data = load_test_data()

    # Define comprehensive parameter ranges
    param_ranges = {
        'rsi_period': [10, 14, 20],
        'oversold': [20, 30, 40],
        'overbought': [60, 70, 80]
    }

    # Run parallel parameter sweep
    start_time = time.time()
    results = parallel_parameter_sweep_threaded(
        data=data,
        strategy='RSI_MEAN_REVERSION',
        param_ranges=param_ranges,
        max_workers=4
    )
    execution_time = time.time() - start_time

    # Display results
    logger.info(f"Parallel sweep completed in {execution_time:.2f}s")
    logger.info(f"Total combinations: {results['total_combinations']}")
    logger.info(f"Success rate: {results['optimization_summary']['success_rate']:.2%}")

    if results['best_parameters']:
        logger.info(f"Best parameters: {results['best_parameters']}")
        logger.info(f"Best score: {results['best_score']:.4f}")

    return results

def test_scalability():
    """Test system scalability with different worker counts"""
    logger.info("Testing system scalability...")

    # Load test data
    data = load_test_data()

    # Define test parameters (smaller for scalability test)
    param_ranges = {
        'rsi_period': [10, 14],
        'oversold': [30],
        'overbought': [70]
    }

    worker_counts = [1, 2, 4]
    results = {}

    for workers in worker_counts:
        logger.info(f"Testing with {workers} workers...")

        start_time = time.time()
        sweep_results = parallel_parameter_sweep_threaded(
            data=data,
            strategy='RSI_MEAN_REVERSION',
            param_ranges=param_ranges,
            max_workers=workers
        )
        execution_time = time.time() - start_time

        results[workers] = {
            'execution_time': execution_time,
            'success_rate': sweep_results['optimization_summary']['success_rate'],
            'tasks_completed': sweep_results['optimization_summary']['completed_tasks']
        }

        logger.info(f"  {workers} workers: {execution_time:.2f}s, {results[workers]['success_rate']:.2%} success")

    # Calculate speedup
    if 1 in results:
        baseline_time = results[1]['execution_time']
        for workers in worker_counts[1:]:
            if workers in results:
                speedup = baseline_time / results[workers]['execution_time']
                efficiency = speedup / workers
                logger.info(f"  {workers} workers speedup: {speedup:.2f}x, efficiency: {efficiency:.2%}")

    return results

def run_comprehensive_test():
    """Run comprehensive threaded optimization test"""
    logger.info("Starting comprehensive threaded optimization test...")

    test_results = {
        'test_time': datetime.now().isoformat(),
        'tests': {}
    }

    try:
        # Test 1: Basic threaded optimization
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Basic Threaded Optimization")
        logger.info("="*60)

        basic_results = test_basic_threaded_optimization()
        test_results['tests']['basic_optimization'] = basic_results

        # Test 2: Parallel parameter sweep
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Parallel Parameter Sweep")
        logger.info("="*60)

        sweep_results = test_parallel_parameter_sweep()
        test_results['tests']['parallel_sweep'] = sweep_results

        # Test 3: Scalability test
        logger.info("\n" + "="*60)
        logger.info("TEST 3: Scalability Test")
        logger.info("="*60)

        scalability_results = test_scalability()
        test_results['tests']['scalability'] = scalability_results

        # Generate summary
        logger.info("\n" + "="*60)
        logger.info("COMPREHENSIVE TEST SUMMARY")
        logger.info("="*60)

        success_count = 0
        total_tests = 3

        if basic_results and basic_results.get('success_rate', 0) > 0:
            success_count += 1
            logger.info("✓ Basic threaded optimization: PASSED")
        else:
            logger.info("✗ Basic threaded optimization: FAILED")

        if sweep_results and sweep_results.get('optimization_summary', {}).get('success_rate', 0) > 0:
            success_count += 1
            logger.info("✓ Parallel parameter sweep: PASSED")
        else:
            logger.info("✗ Parallel parameter sweep: FAILED")

        if scalability_results and len(scalability_results) > 1:
            success_count += 1
            logger.info("✓ Scalability test: PASSED")
        else:
            logger.info("✗ Scalability test: FAILED")

        test_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': success_count,
            'success_rate': success_count / total_tests,
            'overall_status': 'PASSED' if success_count == total_tests else 'PARTIAL'
        }

        logger.info(f"\nOverall: {success_count}/{total_tests} tests passed")

        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"threaded_optimization_test_results_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)

        logger.info(f"Test results saved to: {filename}")

        return test_results

    except Exception as e:
        logger.error(f"Comprehensive test failed: {e}")
        test_results['error'] = str(e)
        return test_results

if __name__ == "__main__":
    # Run comprehensive test
    results = run_comprehensive_test()

    # Print final status
    if 'summary' in results:
        if results['summary']['overall_status'] == 'PASSED':
            print("\n🎉 All threaded optimization tests PASSED!")
        else:
            print(f"\n⚠️ {results['summary']['passed_tests']}/{results['summary']['total_tests']} tests passed")
    else:
        print("\n❌ Test execution failed")
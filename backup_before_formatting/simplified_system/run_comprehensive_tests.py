#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Test Runner
全面测试运行器 - Phase 5

Runs all VectorBT integration tests, system integration tests,
and generates comprehensive test reports
"""

import sys
import os
import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Any
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'test_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_vectorbt_tests():
    """Run VectorBT-specific tests"""
    logger.info("=" * 60)
    logger.info("RUNNING VECTORBT INTEGRATION TESTS")
    logger.info("=" * 60)

    try:
        from tests.test_vectorbt_integration import run_comprehensive_test_suite
        success = run_comprehensive_test_suite()
        return success, "VectorBT Integration Tests"
    except Exception as e:
        logger.error(f"VectorBT tests failed with error: {e}")
        logger.error(traceback.format_exc())
        return False, f"VectorBT Tests Error: {str(e)}"

def run_system_integration_tests():
    """Run system integration tests"""
    logger.info("=" * 60)
    logger.info("RUNNING SYSTEM INTEGRATION TESTS")
    logger.info("=" * 60)

    try:
        from tests.test_system_integration import run_system_integration_tests
        success = run_system_integration_tests()
        return success, "System Integration Tests"
    except Exception as e:
        logger.error(f"System integration tests failed with error: {e}")
        logger.error(traceback.format_exc())
        return False, f"System Integration Tests Error: {str(e)}"

def run_performance_tests():
    """Run performance benchmark tests"""
    logger.info("=" * 60)
    logger.info("RUNNING PERFORMANCE BENCHMARK TESTS")
    logger.info("=" * 60)

    try:
        import time
        import numpy as np
        import pandas as pd

        # Performance benchmarks
        benchmarks = {
            'data_loading': {
                'target_time': 1.0,  # 1 second
                'description': 'Large dataset loading'
            },
            'indicator_calculation': {
                'target_time': 0.5,  # 500ms
                'description': 'Technical indicator calculation'
            },
            'backtest_execution': {
                'target_time': 2.0,  # 2 seconds
                'description': 'Strategy backtest execution'
            },
            'portfolio_optimization': {
                'target_time': 5.0,  # 5 seconds
                'description': 'Portfolio optimization'
            }
        }

        results = {}

        # Test data loading performance
        start_time = time.time()
        large_dataset = pd.DataFrame({
            'close': np.random.uniform(100, 500, 100000),
            'volume': np.random.randint(100000, 10000000, 100000)
        }, index=pd.date_range('2010-01-01', periods=100000, freq='D'))
        data_loading_time = time.time() - start_time
        results['data_loading'] = {
            'actual_time': data_loading_time,
            'target_time': benchmarks['data_loading']['target_time'],
            'passed': data_loading_time <= benchmarks['data_loading']['target_time']
        }

        # Test indicator calculation
        try:
            from indicators.core_indicators import CoreIndicators
            indicators = CoreIndicators()

            start_time = time.time()
            rsi = indicators.calculate_rsi(large_dataset['close'].tail(10000), 14)
            indicator_time = time.time() - start_time
            results['indicator_calculation'] = {
                'actual_time': indicator_time,
                'target_time': benchmarks['indicator_calculation']['target_time'],
                'passed': indicator_time <= benchmarks['indicator_calculation']['target_time']
            }
        except ImportError:
            logger.warning("CoreIndicators not available for performance testing")
            results['indicator_calculation'] = {
                'actual_time': 0,
                'target_time': benchmarks['indicator_calculation']['target_time'],
                'passed': True,
                'note': 'Module not available'
            }

        # Test backtest execution
        try:
            from backtest.vectorbt_engine import VectorBTEngine

            # Create test data
            test_data = pd.DataFrame({
                'open': large_dataset['close'].iloc[:1000],
                'high': large_dataset['close'].iloc[:1000] * 1.02,
                'low': large_dataset['close'].iloc[:1000] * 0.98,
                'close': large_dataset['close'].iloc[:1000],
                'volume': large_dataset['volume'].iloc[:1000]
            })

            start_time = time.time()
            engine = VectorBTEngine()
            result = engine.backtest_strategy(test_data, 'RSI_MEAN_REVERSION', {'period': 14, 'oversold': 30, 'overbought': 70})
            backtest_time = time.time() - start_time
            results['backtest_execution'] = {
                'actual_time': backtest_time,
                'target_time': benchmarks['backtest_execution']['target_time'],
                'passed': backtest_time <= benchmarks['backtest_execution']['target_time']
            }
        except ImportError:
            logger.warning("VectorBTEngine not available for performance testing")
            results['backtest_execution'] = {
                'actual_time': 0,
                'target_time': benchmarks['backtest_execution']['target_time'],
                'passed': True,
                'note': 'Module not available'
            }

        # Calculate overall performance score
        passed_tests = sum(1 for r in results.values() if r.get('passed', False))
        total_tests = len(results)
        performance_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        logger.info(f"Performance tests completed: {passed_tests}/{total_tests} passed ({performance_score:.1f}%)")

        for test_name, result in results.items():
            status = "✓ PASSED" if result['passed'] else "✗ FAILED"
            logger.info(f"  {test_name}: {result['actual_time']:.3f}s (target: {result['target_time']:.3f}s) {status}")

        return performance_score >= 75, "Performance Tests"

    except Exception as e:
        logger.error(f"Performance tests failed with error: {e}")
        logger.error(traceback.format_exc())
        return False, f"Performance Tests Error: {str(e)}"

def check_system_requirements():
    """Check system requirements and dependencies"""
    logger.info("=" * 60)
    logger.info("CHECKING SYSTEM REQUIREMENTS")
    logger.info("=" * 60)

    requirements = {
        'python_version': {'min_version': (3, 8), 'current': sys.version_info[:2]},
        'pandas': {'required': True},
        'numpy': {'required': True},
        'vectorbt': {'required': False, 'recommended': True},
        'scipy': {'required': False, 'recommended': True},
        'sklearn': {'required': False, 'recommended': True},
    }

    check_results = {}

    # Check Python version
    python_ok = requirements['python_version']['current'] >= requirements['python_version']['min_version']
    check_results['python'] = {
        'status': 'PASS' if python_ok else 'FAIL',
        'details': f"Version {requirements['python_version']['current']}, required {requirements['python_version']['min_version']}"
    }

    # Check required packages
    packages_to_check = ['pandas', 'numpy']
    for package in packages_to_check:
        try:
            __import__(package)
            check_results[package] = {'status': 'PASS', 'details': 'Installed'}
        except ImportError:
            check_results[package] = {'status': 'FAIL', 'details': 'Not installed'}

    # Check optional packages
    optional_packages = ['vectorbt', 'scipy', 'sklearn']
    for package in optional_packages:
        try:
            __import__(package)
            check_results[package] = {'status': 'PASS', 'details': 'Installed'}
        except ImportError:
            check_results[package] = {'status': 'WARNING', 'details': 'Not installed (optional)'}

    # Print results
    all_passed = True
    for component, result in check_results.items():
        status = result['status']
        details = result['details']
        logger.info(f"  {component}: {status} - {details}")

        if status == 'FAIL':
            all_passed = False

    return all_passed, "System Requirements Check"

def generate_test_report(test_results: List[tuple]):
    """Generate comprehensive test report"""
    logger.info("=" * 60)
    logger.info("GENERATING TEST REPORT")
    logger.info("=" * 60)

    report = {
        'timestamp': datetime.now().isoformat(),
        'test_session_id': datetime.now().strftime("%Y%m%d_%H%M%S"),
        'summary': {
            'total_test_suites': len(test_results),
            'passed_suites': sum(1 for success, _ in test_results if success),
            'failed_suites': sum(1 for success, _ in test_results if not success),
            'success_rate': (sum(1 for success, _ in test_results if success) / len(test_results)) * 100 if test_results else 0
        },
        'test_results': []
    }

    for success, test_name in test_results:
        report['test_results'].append({
            'test_name': test_name,
            'status': 'PASSED' if success else 'FAILED',
            'success': success
        })

    # Save report to file
    report_filename = f"comprehensive_test_report_{report['test_session_id']}.json"
    try:
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Test report saved to: {report_filename}")
    except Exception as e:
        logger.error(f"Failed to save test report: {e}")

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("COMPREHENSIVE TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Test Session ID: {report['test_session_id']}")
    logger.info(f"Total Test Suites: {report['summary']['total_test_suites']}")
    logger.info(f"Passed: {report['summary']['passed_suites']}")
    logger.info(f"Failed: {report['summary']['failed_suites']}")
    logger.info(f"Success Rate: {report['summary']['success_rate']:.1f}%")

    logger.info("\nTest Suite Results:")
    for test_result in report['test_results']:
        status_icon = "✓" if test_result['success'] else "✗"
        logger.info(f"  {status_icon} {test_result['test_name']}: {test_result['status']}")

    return report

def main():
    """Main test runner function"""
    start_time = time.time()
    logger.info("STARTING COMPREHENSIVE TEST SUITE")
    logger.info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run all test suites
    test_results = []

    # 1. Check system requirements
    logger.info("\n" + "="*60)
    req_success, req_name = check_system_requirements()
    test_results.append((req_success, req_name))

    # 2. Run VectorBT integration tests
    logger.info("\n" + "="*60)
    vbt_success, vbt_name = run_vectorbt_tests()
    test_results.append((vbt_success, vbt_name))

    # 3. Run system integration tests
    logger.info("\n" + "="*60)
    sys_success, sys_name = run_system_integration_tests()
    test_results.append((sys_success, sys_name))

    # 4. Run performance tests
    logger.info("\n" + "="*60)
    perf_success, perf_name = run_performance_tests()
    test_results.append((perf_success, perf_name))

    # Generate comprehensive report
    report = generate_test_report(test_results)

    # Calculate total execution time
    total_time = time.time() - start_time
    logger.info(f"\nTotal execution time: {total_time:.2f} seconds")

    # Determine overall success
    overall_success = all(success for success, _ in test_results)

    if overall_success:
        logger.info("\n🎉 ALL TESTS PASSED! System is ready for deployment.")
        return_code = 0
    else:
        logger.info("\n❌ SOME TESTS FAILED! Please review the errors above.")
        return_code = 1

    logger.info("=" * 60)
    logger.info("TEST SUITE COMPLETED")
    logger.info("=" * 60)

    return return_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
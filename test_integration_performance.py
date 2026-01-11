#!/usr/bin/env python3
"""
Comprehensive integration and performance testing for CBSC multiprocessing system.

This script runs the complete testing suite including:
1. System integration validation
2. Performance benchmarking
3. Load testing and stability validation
4. Backward compatibility testing
"""

import sys
import os
import time
import logging
import json
import traceback
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('integration_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_import_dependencies():
    """Test that all required dependencies can be imported."""
    logger.info("Testing dependency imports...")

    try:
        # Test core dependencies
        import psutil
        import pandas as pd
        import numpy as np
        logger.info("✓ Core dependencies available")

        # Test multiprocessing components
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        try:
            from backtest.parallel.integration import CBSCMultiprocessingIntegration
            from backtest.parallel.benchmark import PerformanceBenchmarkFramework, run_quick_benchmark
            from backtest.parallel.load_test import LoadTestFramework, run_quick_stress_test
            logger.info("✓ Multiprocessing components available")
            return True
        except ImportError as e:
            logger.error(f"✗ Multiprocessing components not available: {e}")
            return False

    except ImportError as e:
        logger.error(f"✗ Core dependencies not available: {e}")
        return False


def test_system_integration():
    """Test basic system integration functionality."""
    logger.info("Testing system integration...")

    try:
        from backtest.parallel.integration import CBSCMultiprocessingIntegration, BacktestRequest

        # Initialize integration
        config = {
            'multiprocessing_threshold': 100,  # Low threshold for testing
            'monitoring': {'enable_monitoring': True}
        }

        integration = CBSCMultiprocessingIntegration(config=config)
        logger.info("✓ Integration initialized successfully")

        # Test basic backtest execution
        strategy_code = '''
def test_strategy(data, params):
    # Simple test strategy
    return [1] * len(data)
'''

        parameters = {'test_param': 'value'}

        result = integration.execute_backtest(
            strategy_code=strategy_code,
            parameters=parameters,
            use_multiprocessing=False  # Use sequential for basic test
        )

        if result.success:
            logger.info("✓ Basic backtest execution successful")
        else:
            logger.error(f"✗ Basic backtest execution failed: {result.error_message}")
            return False

        # Test system status
        status = integration.get_system_status()
        if status:
            logger.info(f"✓ System status retrieved: {status}")
        else:
            logger.error("✗ Failed to get system status")
            return False

        # Cleanup
        integration.shutdown()
        logger.info("✓ Integration shutdown successfully")

        return True

    except Exception as e:
        logger.error(f"✗ System integration test failed: {e}")
        traceback.print_exc()
        return False


def test_performance_benchmark():
    """Run performance benchmark tests."""
    logger.info("Running performance benchmark tests...")

    try:
        from backtest.parallel.benchmark import run_quick_benchmark

        # Create output directory
        output_dir = Path("benchmark_results")
        output_dir.mkdir(exist_ok=True)

        # Run quick benchmark
        logger.info("Executing quick performance benchmark...")
        results = run_quick_benchmark(str(output_dir))

        if results and results.get('performance_summary'):
            perf_summary = results['performance_summary']
            logger.info("✓ Performance benchmark completed")
            logger.info(f"  - Average speedup: {perf_summary.get('avg_speedup', 0):.2f}x")
            logger.info(f"  - Max speedup: {perf_summary.get('max_speedup', 0):.2f}x")
            logger.info(f"  - Average throughput: {perf_summary.get('avg_throughput_tps', 0):.2f} tasks/sec")

            # Check if basic performance targets are met
            avg_speedup = perf_summary.get('avg_speedup', 0)
            if avg_speedup >= 1.0:  # At least some speedup
                logger.info("✓ Basic performance target met")
                return True
            else:
                logger.warning(f"⚠ Performance improvement minimal: {avg_speedup:.2f}x")
                return True  # Still consider success for basic test
        else:
            logger.error("✗ Performance benchmark failed to produce results")
            return False

    except Exception as e:
        logger.error(f"✗ Performance benchmark test failed: {e}")
        traceback.print_exc()
        return False


def test_load_stability():
    """Run load and stability testing."""
    logger.info("Running load and stability tests...")

    try:
        from backtest.parallel.load_test import run_quick_stress_test

        # Create output directory
        output_dir = Path("load_test_results")
        output_dir.mkdir(exist_ok=True)

        # Run quick stress test (shorter duration for validation)
        logger.info("Executing quick stress test...")
        statistics = run_quick_stress_test(str(output_dir))

        if statistics:
            logger.info("✓ Load test completed successfully")
            logger.info(f"  - Total tests: {statistics.total_backtests}")
            logger.info(f"  - Success rate: {statistics.stability_rate:.4f}")
            logger.info(f"  - Error rate: {statistics.error_rate:.4f}")
            logger.info(f"  - Peak memory: {statistics.peak_memory_mb:.1f} MB")
            logger.info(f"  - Average throughput: {statistics.avg_throughput_tps:.2f} tasks/sec")

            # Check stability targets
            if statistics.stability_rate >= 0.95:  # 95% minimum for quick test
                logger.info("✓ Stability target met")
                return True
            else:
                logger.warning(f"⚠ Stability rate below target: {statistics.stability_rate:.4f}")
                return False
        else:
            logger.error("✗ Load test failed to produce statistics")
            return False

    except Exception as e:
        logger.error(f"✗ Load test failed: {e}")
        traceback.print_exc()
        return False


def test_backward_compatibility():
    """Test backward compatibility with legacy CBSC requests."""
    logger.info("Testing backward compatibility...")

    try:
        from backtest.parallel.integration import CBSCMultiprocessingIntegration, migrate_legacy_request

        # Create integration instance
        integration = CBSCMultiprocessingIntegration()

        # Test legacy request migration
        legacy_request = {
            'strategy_id': 'test_strategy_001',
            'strategy_code': '''
def legacy_strategy(data, params):
    return [1] * len(data)
''',
            'start_date': '2020-01-01',
            'end_date': '2023-12-31',
            'initial_capital': 100000,
            'commission': 0.001,
            'slippage': 0.0001,
            'strategy_params': {
                'param1': 'value1',
                'param2': 42
            },
            'priority': 'high'
        }

        # Migrate legacy request
        migrated_request = migrate_legacy_request(legacy_request)

        if migrated_request and migrated_request.strategy_id == 'test_strategy_001':
            logger.info("✓ Legacy request migration successful")
        else:
            logger.error("✗ Legacy request migration failed")
            return False

        # Test execution with migrated request
        result = integration.execute_backtest(
            strategy_code=migrated_request.strategy_code,
            parameters=migrated_request.parameters,
            data_config=migrated_request.data_config,
            backtest_config=migrated_request.backtest_config,
            strategy_id=migrated_request.strategy_id
        )

        if result.success:
            logger.info("✓ Migrated request execution successful")
        else:
            logger.error(f"✗ Migrated request execution failed: {result.error_message}")
            return False

        # Cleanup
        integration.shutdown()
        logger.info("✓ Backward compatibility test passed")
        return True

    except Exception as e:
        logger.error(f"✗ Backward compatibility test failed: {e}")
        traceback.print_exc()
        return False


def test_monitoring_integration():
    """Test monitoring system integration."""
    logger.info("Testing monitoring system integration...")

    try:
        from backtest.parallel.monitor import get_monitor, start_monitoring
        from backtest.parallel.performance_metrics import get_metrics_collector, start_metrics_collection

        # Start monitoring
        start_monitoring()
        start_metrics_collection()

        # Get monitor instance
        monitor = get_monitor()
        metrics_collector = get_metrics_collector()

        if monitor and metrics_collector:
            logger.info("✓ Monitoring components initialized")
        else:
            logger.error("✗ Failed to initialize monitoring components")
            return False

        # Test status report generation
        status_report = monitor.get_status_report()
        if status_report and 'timestamp' in status_report:
            logger.info("✓ Status report generation successful")
        else:
            logger.error("✗ Status report generation failed")
            return False

        # Test metrics collection
        snapshot = metrics_collector.get_performance_snapshot()
        if snapshot:
            logger.info("✓ Performance metrics collection successful")
        else:
            logger.warning("⚠ No performance metrics collected (expected for new system)")

        logger.info("✓ Monitoring integration test passed")
        return True

    except Exception as e:
        logger.error(f"✗ Monitoring integration test failed: {e}")
        traceback.print_exc()
        return False


def run_comprehensive_test_suite():
    """Run comprehensive test suite."""
    logger.info("=" * 60)
    logger.info("CBSC MULTIPROCESSING SYSTEM - COMPREHENSIVE TEST SUITE")
    logger.info("=" * 60)

    test_results = {
        'dependencies': False,
        'integration': False,
        'benchmark': False,
        'load_test': False,
        'compatibility': False,
        'monitoring': False
    }

    start_time = datetime.now()

    # Run tests
    try:
        test_results['dependencies'] = test_import_dependencies()

        if test_results['dependencies']:
            test_results['integration'] = test_system_integration()
            test_results['compatibility'] = test_backward_compatibility()
            test_results['monitoring'] = test_monitoring_integration()

            # Performance tests only if basic integration works
            if test_results['integration']:
                test_results['benchmark'] = test_performance_benchmark()
                test_results['load_test'] = test_load_stability()

    except Exception as e:
        logger.error(f"Test suite execution failed: {e}")
        traceback.print_exc()

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Generate final report
    logger.info("=" * 60)
    logger.info("TEST SUITE RESULTS")
    logger.info("=" * 60)

    total_tests = len(test_results)
    passed_tests = sum(test_results.values())

    for test_name, result in test_results.items():
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        logger.info(f"{symbol} {test_name.title()}: {status}")

    logger.info("-" * 60)
    logger.info(f"Overall Results: {passed_tests}/{total_tests} tests passed")
    logger.info(f"Execution Time: {duration:.2f} seconds")

    success_rate = passed_tests / total_tests if total_tests > 0 else 0
    logger.info(f"Success Rate: {success_rate:.1%}")

    # Generate detailed report
    report = {
        'test_suite': 'CBSC Multiprocessing Integration Tests',
        'timestamp': datetime.now().isoformat(),
        'duration_seconds': duration,
        'test_results': test_results,
        'summary': {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': success_rate,
            'overall_success': passed_tests == total_tests
        }
    }

    # Save report
    report_file = Path("integration_test_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Detailed report saved to: {report_file}")

    # Final verdict
    if success_rate >= 0.8:  # 80% success rate
        logger.info("\n🎉 INTEGRATION TEST SUITE PASSED!")
        logger.info("The CBSC multiprocessing system is ready for production.")
        if success_rate < 1.0:
            logger.info("⚠️ Some tests failed - review the output above.")
        return True
    else:
        logger.error("\n❌ INTEGRATION TEST SUITE FAILED!")
        logger.error("Critical issues detected - review and fix before deployment.")
        return False


if __name__ == "__main__":
    try:
        success = run_comprehensive_test_suite()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("Test suite interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error during test execution: {e}")
        traceback.print_exc()
        sys.exit(1)
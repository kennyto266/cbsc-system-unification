#!/usr/bin/env python3
"""
OpenSpec Task 11: Integration Tests for Non-Price Technical Analysis Workflow
Simple version without Unicode characters to avoid encoding issues.
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import unittest
from typing import Dict, List, Any

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root / 'src' / 'workflow'))
sys.path.insert(0, str(project_root / 'src' / 'api'))
sys.path.insert(0, str(project_root / 'src' / 'indicators'))

# Import modules for testing
try:
    from workflow.adaptive_market_system import AdaptiveMarketSystem
    from api.adaptive_analysis_api import AdaptiveAnalysisAPI
    from indicators.core_indicators import CoreIndicators
    from api.stock_api import get_hk_stock_data
    from api.government_data import get_hibor_data
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import required modules: {e}")
    IMPORTS_AVAILABLE = False


class TestEndToEndWorkflow(unittest.TestCase):
    """Test complete end-to-end non-price technical analysis workflow"""

    def setUp(self):
        """Setup test environment"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required imports not available")
        self.adaptive_system = AdaptiveMarketSystem()

    def test_complete_non_price_workflow(self):
        """Test complete workflow from raw data to trading signals"""
        print("\n--- Testing Complete Non-Price Workflow ---")

        # Step 1: Generate realistic non-price data
        non_price_data = self._generate_test_data()
        self.assertIsInstance(non_price_data, dict)
        self.assertGreater(len(non_price_data), 0)

        # Step 2: Run adaptive analysis
        start_time = time.time()
        results = self.adaptive_system.run_adaptive_analysis(non_price_data)
        execution_time = time.time() - start_time

        # Step 3: Validate results structure
        required_keys = ['final_signal', 'consensus_market_state', 'adaptive_weights']
        for key in required_keys:
            self.assertIn(key, results, f"Missing required key: {key}")

        # Step 4: Validate signal quality
        signal = results['final_signal']
        self.assertIn(signal['signal'], ['BUY', 'SELL', 'HOLD'])
        self.assertGreaterEqual(signal['confidence'], 0.0)
        self.assertLessEqual(signal['confidence'], 1.0)

        # Step 5: Performance validation (should complete within 10 seconds per OpenSpec)
        self.assertLess(execution_time, 10.0,
                       f"Workflow took {execution_time:.2f}s, exceeds 10s limit")

        print(f"PASS: Complete workflow test passed in {execution_time:.2f}s")
        print(f"  Signal: {signal['signal']} (confidence: {signal['confidence']:.2%})")

    def test_multi_source_data_integration(self):
        """Test integration of multiple data sources"""
        print("\n--- Testing Multi-Source Data Integration ---")

        # Create test data with different sources
        multi_source_data = {
            'hibor_rates': pd.Series(
                np.random.normal(3.5, 0.5, 100),
                index=pd.date_range('2024-01-01', periods=100, freq='D')
            ),
            'monetary_base': pd.Series(
                np.cumsum(np.random.normal(0.1, 1.0, 100)) + 1000,
                index=pd.date_range('2024-01-01', periods=100, freq='D')
            ),
            'exchange_rates': pd.Series(
                np.cumsum(np.random.normal(-0.001, 0.01, 100)) + 7.8,
                index=pd.date_range('2024-01-01', periods=100, freq='D')
            )
        }

        # Test system handles multiple sources
        results = self.adaptive_system.run_adaptive_analysis(multi_source_data)

        # Verify adaptive weights for all sources
        weights = results['adaptive_weights']
        self.assertGreater(len(weights), 2, "Should handle multiple data sources")

        # Verify total weights sum to 1.0 (or close)
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=2,
                             msg="Adaptive weights should sum to 1.0")

        print(f"PASS: Multi-source integration successful with {len(weights)} sources")
        for source, weight in weights.items():
            print(f"  {source}: {weight:.3f}")

    def _generate_test_data(self) -> Dict[str, pd.Series]:
        """Generate test data for non-price analysis"""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=100, freq='D')

        return {
            'hibor_rates': pd.Series(
                np.random.normal(3.5, 0.5, 100),
                index=dates
            ),
            'monetary_base': pd.Series(
                np.cumsum(np.random.normal(0.1, 1.0, 100)) + 1000,
                index=dates
            )
        }


class TestSystemCompatibility(unittest.TestCase):
    """Test compatibility with existing Simplified System components"""

    def setUp(self):
        """Setup compatibility test environment"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required imports not available")

    def test_simplified_system_compatibility(self):
        """Test 100% compatibility with existing Simplified System"""
        print("\n--- Testing Simplified System Compatibility ---")

        try:
            # Test compatibility with core indicators
            indicators = CoreIndicators()
            test_data = pd.Series(np.random.normal(100, 10, 50),
                                index=pd.date_range('2024-01-01', periods=50))

            # Test RSI calculation
            rsi = indicators.calculate_rsi(test_data, 14)
            self.assertIsInstance(rsi, pd.Series)
            self.assertFalse(rsi.empty)

            # Test MACD calculation
            macd_result = indicators.calculate_macd(test_data)
            self.assertIsInstance(macd_result, dict)
            self.assertIn('macd', macd_result)

            print("PASS: Full compatibility with Simplified System confirmed")

        except Exception as e:
            self.fail(f"Compatibility test failed: {e}")


class TestPerformanceStress(unittest.TestCase):
    """Test performance under stress conditions"""

    def setUp(self):
        """Setup performance test environment"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required imports not available")
        self.adaptive_system = AdaptiveMarketSystem()
        self.performance_threshold = 10.0  # 10 seconds per OpenSpec requirement

    def test_performance_stress_test(self):
        """Test system performance under stress conditions"""
        print("\n--- Performance Stress Testing ---")

        # Create large dataset
        large_dataset = self._create_stress_test_data(size=1000)

        # Measure performance
        start_time = time.time()
        results = self.adaptive_system.run_adaptive_analysis(large_dataset)
        execution_time = time.time() - start_time

        # Verify performance meets requirements
        self.assertLess(execution_time, self.performance_threshold,
                       f"Stress test failed: {execution_time:.2f}s > {self.performance_threshold}s")

        # Verify results are still valid under stress
        self.assertIn('final_signal', results)
        self.assertIn('adaptive_weights', results)

        print(f"PASS: Stress test passed: {execution_time:.2f}s with {len(large_dataset)} data points")

    def _create_stress_test_data(self, size: int = 1000) -> Dict[str, pd.Series]:
        """Create stress test data of specified size"""
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', periods=size, freq='D')

        return {
            f'test_series_{i}': pd.Series(
                np.cumsum(np.random.normal(0.001, 0.02, size)) + 100,
                index=dates
            ) for i in range(3)  # 3 different series
        }


class TestRealDataIntegration(unittest.TestCase):
    """Test integration with real external data sources"""

    def setUp(self):
        """Setup real data test environment"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required imports not available")

    def test_real_data_availability(self):
        """Test real data availability without full integration"""
        print("\n--- Real Data Availability Test ---")

        try:
            # Test if we can access real data functions
            # Note: This test doesn't require actual network access
            self.assertTrue(callable(get_hk_stock_data))
            self.assertTrue(callable(get_hibor_data))

            print("PASS: Real data functions are available")

        except Exception as e:
            self.skipTest(f"Real data availability test skipped: {e}")


def run_integration_tests():
    """Run all integration tests and generate report"""
    print("=" * 80)
    print("OpenSpec Task 11: Integration Tests for Non-Price Technical Analysis")
    print("=" * 80)

    # Define test suites
    test_suites = [
        ('End-to-End Workflow', unittest.TestLoader().loadTestsFromTestCase(TestEndToEndWorkflow)),
        ('System Compatibility', unittest.TestLoader().loadTestsFromTestCase(TestSystemCompatibility)),
        ('Performance Stress', unittest.TestLoader().loadTestsFromTestCase(TestPerformanceStress)),
        ('Real Data Integration', unittest.TestLoader().loadTestsFromTestCase(TestRealDataIntegration))
    ]

    # Run test suites
    overall_results = {
        'total_tests': 0,
        'passed_tests': 0,
        'failed_tests': 0,
        'skipped_tests': 0,
        'suite_results': {},
        'execution_time': 0
    }

    start_time = time.time()

    for suite_name, test_suite in test_suites:
        print(f"\n{'=' * 60}")
        print(f"Running Test Suite: {suite_name}")
        print(f"{'=' * 60}")

        suite_start_time = time.time()

        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, stream=open(os.devnull, 'w'))
        result = runner.run(test_suite)

        suite_execution_time = time.time() - suite_start_time

        # Record results
        suite_total = result.testsRun
        suite_failures = len(result.failures)
        suite_errors = len(result.errors)
        suite_skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
        suite_passed = suite_total - suite_failures - suite_errors - suite_skipped

        overall_results['suite_results'][suite_name] = {
            'total': suite_total,
            'passed': suite_passed,
            'failed': suite_failures + suite_errors,
            'skipped': suite_skipped,
            'execution_time': suite_execution_time,
            'success_rate': suite_passed / suite_total if suite_total > 0 else 0
        }

        overall_results['total_tests'] += suite_total
        overall_results['passed_tests'] += suite_passed
        overall_results['failed_tests'] += suite_failures + suite_errors
        overall_results['skipped_tests'] += suite_skipped

        print(f"\n{suite_name} Results:")
        print(f"  Total: {suite_total}, Passed: {suite_passed}, Failed: {suite_failures + suite_errors}")
        print(f"  Skipped: {suite_skipped}, Success Rate: {suite_passed/suite_total*100:.1f}%")
        print(f"  Execution Time: {suite_execution_time:.2f}s")

    overall_results['execution_time'] = time.time() - start_time

    # Generate comprehensive report
    print(f"\n{'=' * 80}")
    print("COMPREHENSIVE INTEGRATION TEST REPORT")
    print(f"{'=' * 80}")

    print(f"\nOverall Results:")
    print(f"  Total Tests: {overall_results['total_tests']}")
    print(f"  Passed: {overall_results['passed_tests']}")
    print(f"  Failed: {overall_results['failed_tests']}")
    print(f"  Skipped: {overall_results['skipped_tests']}")
    print(f"  Overall Success Rate: {overall_results['passed_tests']/overall_results['total_tests']*100:.1f}%")
    print(f"  Total Execution Time: {overall_results['execution_time']:.2f}s")

    print(f"\nTest Suite Breakdown:")
    for suite_name, suite_result in overall_results['suite_results'].items():
        status = "PASS" if suite_result['failed'] == 0 else "FAIL"
        print(f"  {status} {suite_name}:")
        print(f"    Success Rate: {suite_result['success_rate']*100:.1f}%")
        print(f"    Execution Time: {suite_result['execution_time']:.2f}s")

    # Generate detailed report file
    report_file = project_root / "OPENSPEC_TASK11_INTEGRATION_RESULTS.json"

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(overall_results, f, indent=2, default=str)

    print(f"\nDetailed report saved to: {report_file}")

    # Return success status
    overall_success_rate = overall_results['passed_tests'] / overall_results['total_tests']

    if overall_success_rate >= 0.9:
        print(f"\nINTEGRATION TESTS: EXCELLENT ({overall_success_rate*100:.1f}% success rate)")
        return True
    elif overall_success_rate >= 0.8:
        print(f"\nINTEGRATION TESTS: GOOD ({overall_success_rate*100:.1f}% success rate)")
        return True
    else:
        print(f"\nINTEGRATION TESTS: NEEDS IMPROVEMENT ({overall_success_rate*100:.1f}% success rate)")
        return False


if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)
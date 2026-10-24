"""
CBSC Backtest System - Complete Acceptance Test Suite
======================================================

Comprehensive system acceptance testing covering:
1. Module import validation
2. Core functionality end-to-end tests
3. Performance verification
4. Data integrity checks
5. Integration validation

Author: CBSC Quant Team
Date: 2025-12-28
Version: 1.0.0
"""

import sys
import os
import time
import traceback
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ========================================
# Module-level objective functions for multiprocessing
# These must be at module level to be picklable
# ========================================

def _acceptance_test_objective_2d(params, data):
    """2D sphere function for acceptance testing"""
    return -(params['x']**2 + params['y']**2)


def _acceptance_test_objective_3d(params, data):
    """3D sphere function for acceptance testing"""
    return -(params['x']**2 + params['y']**2 + params['z']**2)


def _acceptance_test_objective_5d(params, data):
    """5D sphere function for acceptance testing"""
    return -sum(params[f'p{i}']**2 for i in range(5))


class TestStatus(Enum):
    """Test execution status"""
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


@dataclass
class TestResult:
    """Individual test result"""
    name: str
    category: str
    status: TestStatus
    message: str
    duration: float
    details: Dict[str, Any] = None


class SystemAcceptanceTest:
    """
    Complete system acceptance test suite
    Validates entire CBSC Backtest System for production readiness
    """

    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
        self.output_dir = Path(__file__).parent

    # ========================================
    # CATEGORY 1: Module Import Validation
    # ========================================

    def _test_imports(self) -> List[TestResult]:
        """Test 1: Validate all critical modules can be imported"""
        print("\n" + "="*70)
        print("CATEGORY 1: MODULE IMPORT VALIDATION")
        print("="*70)

        tests = []
        modules_to_test = {
            'parameter_optimizer': 'Parameter optimizer core module',
            'performance_optimizer': 'Performance optimization extensions',
            'performance_benchmark': 'Performance benchmark system',
            'optimization_visualization': 'Visualization module',
            'comprehensive_test_suite': 'Comprehensive test suite',
            'integration_runner': 'Integration test runner'
        }

        for module_name, description in modules_to_test.items():
            start = time.time()
            try:
                # Try importing the module
                module = __import__(module_name, fromlist=[''])
                duration = time.time() - start

                # Basic validation
                has_main_classes = hasattr(module, 'ParameterOptimizer') or \
                                  hasattr(module, 'PerformanceOptimizer') or \
                                  hasattr(module, 'PerformanceBenchmark')

                tests.append(TestResult(
                    name=f"Import: {module_name}",
                    category="Module Import",
                    status=TestStatus.PASSED if has_main_classes else TestStatus.SKIPPED,
                    message=f"Successfully imported {description}",
                    duration=duration,
                    details={'module': module_name, 'has_main_classes': has_main_classes}
                ))
                print(f"  [OK] {module_name}: {description}")

            except Exception as e:
                duration = time.time() - start
                tests.append(TestResult(
                    name=f"Import: {module_name}",
                    category="Module Import",
                    status=TestStatus.ERROR,
                    message=f"Failed to import: {str(e)}",
                    duration=duration,
                    details={'error': str(e), 'traceback': traceback.format_exc()}
                ))
                print(f"  [ERR] {module_name}: {str(e)}")

        return tests

    # ========================================
    # CATEGORY 2: Core Functionality E2E
    # ========================================

    def _test_core_functionality(self) -> List[TestResult]:
        """Test 2: End-to-end core functionality tests"""
        print("\n" + "="*70)
        print("CATEGORY 2: CORE FUNCTIONALITY (END-TO-END)")
        print("="*70)

        tests = []

        # Test 2.1: Complete parameter optimization workflow
        print("\n[Test 2.1] Complete Parameter Optimization Workflow")
        start = time.time()
        try:
            from parameter_optimizer import (
                ParameterOptimizer, ParameterSpace, OptimizationConfig,
                OptimizationMethod, OptimizationResult
            )

            # Setup
            param_spaces = [
                ParameterSpace(name='x', param_type='continuous', bounds=(-5, 5)),
                ParameterSpace(name='y', param_type='continuous', bounds=(-5, 5))
            ]

            config = OptimizationConfig(
                method=OptimizationMethod.GRID_SEARCH,
                max_iterations=50,
                random_state=42
            )

            optimizer = ParameterOptimizer(config)
            for ps in param_spaces:
                optimizer.add_parameter(ps)

            # Simple objective function
            def objective(params, data):
                return -(params['x']**2 + params['y']**2)

            # Run optimization
            result = optimizer.optimize(objective, None)
            duration = time.time() - start

            # Validate result
            success = (
                isinstance(result, OptimizationResult) and
                hasattr(result, 'best_params') and
                hasattr(result, 'best_score') and
                result.best_score > -1.0  # Should find good solution
            )

            tests.append(TestResult(
                name="E2E: Parameter Optimization Workflow",
                category="Core Functionality",
                status=TestStatus.PASSED if success else TestStatus.FAILED,
                message=f"Optimization completed, score: {result.best_score:.4f}",
                duration=duration,
                details={
                    'best_params': result.best_params,
                    'best_score': result.best_score,
                    'n_evaluations': result.n_evaluations
                }
            ))
            print(f"  [{'PASS' if success else 'FAIL'}] Score: {result.best_score:.4f}, Evaluations: {result.n_evaluations}")

        except Exception as e:
            duration = time.time() - start
            tests.append(TestResult(
                name="E2E: Parameter Optimization Workflow",
                category="Core Functionality",
                status=TestStatus.ERROR,
                message=f"Workflow failed: {str(e)}",
                duration=duration,
                details={'error': str(e), 'traceback': traceback.format_exc()}
            ))
            print(f"  [ERR] {str(e)}")

        # Test 2.2: Multi-method comparison
        print("\n[Test 2.2] Multi-Method Comparison")
        start = time.time()
        try:
            from parameter_optimizer import ParameterOptimizer, ParameterSpace, OptimizationConfig, OptimizationMethod

            methods = [
                OptimizationMethod.GRID_SEARCH,
                OptimizationMethod.RANDOM_SEARCH
            ]

            results = {}
            for method in methods:
                config = OptimizationConfig(
                    method=method,
                    max_iterations=100,
                    random_state=42
                )
                optimizer = ParameterOptimizer(config)
                for ps in param_spaces:
                    optimizer.add_parameter(ps)

                result = optimizer.optimize(objective, None)
                results[method.value] = result.best_score

            duration = time.time() - start

            # Both methods should find reasonable solutions
            success = all(score > -5.0 for score in results.values())

            tests.append(TestResult(
                name="E2E: Multi-Method Comparison",
                category="Core Functionality",
                status=TestStatus.PASSED if success else TestStatus.FAILED,
                message=f"Compared {len(results)} methods",
                duration=duration,
                details={'results': results}
            ))
            print(f"  [{'PASS' if success else 'FAIL'}] Methods: {list(results.keys())}")
            for method, score in results.items():
                print(f"    {method}: {score:.4f}")

        except Exception as e:
            duration = time.time() - start
            tests.append(TestResult(
                name="E2E: Multi-Method Comparison",
                category="Core Functionality",
                status=TestStatus.ERROR,
                message=f"Comparison failed: {str(e)}",
                duration=duration,
                details={'error': str(e)}
            ))
            print(f"  [ERR] {str(e)}")

        # Test 2.3: Visualization pipeline
        print("\n[Test 2.3] Visualization Pipeline")
        start = time.time()
        try:
            from optimization_visualization import OptimizationVisualizer
            from parameter_optimizer import OptimizationResult

            # Create mock results
            results = [
                OptimizationResult(
                    best_params={'x': 0, 'y': 0},
                    best_score=0.0,
                    best_iteration=10,
                    optimization_history=[],
                    convergence_curve=[-5, -3, -1, -0.5, 0],
                    n_evaluations=100
                ),
                OptimizationResult(
                    best_params={'x': 0.1, 'y': 0.1},
                    best_score=-0.02,
                    best_iteration=15,
                    optimization_history=[],
                    convergence_curve=[-4, -2, -1, -0.3, -0.02],
                    n_evaluations=150
                )
            ]

            viz = OptimizationVisualizer()
            fig = viz.plot_convergence(
                results,
                ['Method 1', 'Method 2'],
                save_path=None  # Don't save file
            )

            duration = time.time() - start
            success = fig is not None

            tests.append(TestResult(
                name="E2E: Visualization Pipeline",
                category="Core Functionality",
                status=TestStatus.PASSED if success else TestStatus.FAILED,
                message=f"Generated {len(results)} visualization(s)",
                duration=duration,
                details={'figure_created': success}
            ))
            print(f"  [{'PASS' if success else 'FAIL'}] Visualizations generated")

            # Clean up
            if fig:
                import matplotlib.pyplot as plt
                plt.close(fig)

        except Exception as e:
            duration = time.time() - start
            tests.append(TestResult(
                name="E2E: Visualization Pipeline",
                category="Core Functionality",
                status=TestStatus.ERROR,
                message=f"Visualization failed: {str(e)}",
                duration=duration,
                details={'error': str(e)}
            ))
            print(f"  [ERR] {str(e)}")

        return tests

    # ========================================
    # CATEGORY 3: Performance Verification
    # ========================================

    def _test_performance(self) -> List[TestResult]:
        """Test 3: Performance optimization verification"""
        print("\n" + "="*70)
        print("CATEGORY 3: PERFORMANCE VERIFICATION")
        print("="*70)

        tests = []

        # Test 3.1: Multi-method performance comparison
        print("\n[Test 3.1] Multi-Method Performance Comparison")
        start = time.time()
        try:
            from parameter_optimizer import (
                ParameterOptimizer, ParameterSpace, OptimizationConfig,
                OptimizationMethod
            )

            # Setup parameter spaces
            param_spaces = [
                ParameterSpace(name='x', param_type='continuous', bounds=(-5, 5)),
                ParameterSpace(name='y', param_type='continuous', bounds=(-5, 5))
            ]

            methods_to_test = [
                OptimizationMethod.GRID_SEARCH,
                OptimizationMethod.RANDOM_SEARCH,
                OptimizationMethod.PARTICLE_SWARM
            ]

            results = {}
            times = {}

            for method in methods_to_test:
                config = OptimizationConfig(
                    method=method,
                    max_iterations=100,
                    random_state=42
                )
                optimizer = ParameterOptimizer(config)
                for ps in param_spaces:
                    optimizer.add_parameter(ps)

                method_start = time.time()
                result = optimizer.optimize(_acceptance_test_objective_2d, None)
                method_time = time.time() - method_start

                results[method.value] = result.best_score
                times[method.value] = method_time

            duration = time.time() - start

            # All methods should find reasonable solutions
            success = all(score > -5.0 for score in results.values())

            tests.append(TestResult(
                name="Performance: Multi-Method Comparison",
                category="Performance",
                status=TestStatus.PASSED if success else TestStatus.FAILED,
                message=f"Tested {len(results)} methods",
                duration=duration,
                details={
                    'results': results,
                    'times': times
                }
            ))
            print(f"  [{'PASS' if success else 'FAIL'}] All methods completed")
            for method, score in results.items():
                print(f"    {method}: {score:.4f} ({times[method]:.3f}s)")

        except Exception as e:
            duration = time.time() - start
            tests.append(TestResult(
                name="Performance: Multi-Method Comparison",
                category="Performance",
                status=TestStatus.ERROR,
                message=f"Performance test failed: {str(e)}",
                duration=duration,
                details={'error': str(e)}
            ))
            print(f"  [ERR] {str(e)}")

        # Test 3.2: Scalability test
        print("\n[Test 3.2] Optimization Scalability")
        start = time.time()
        try:
            from parameter_optimizer import (
                ParameterOptimizer, ParameterSpace, OptimizationConfig,
                OptimizationMethod
            )

            # Test with different dimensions
            dimensions = [2, 3, 4]
            results = {}

            for dim in dimensions:
                if dim == 2:
                    param_spaces = [
                        ParameterSpace(name='x', param_type='continuous', bounds=(-3, 3)),
                        ParameterSpace(name='y', param_type='continuous', bounds=(-3, 3))
                    ]
                    objective = _acceptance_test_objective_2d
                elif dim == 3:
                    param_spaces = [
                        ParameterSpace(name='x', param_type='continuous', bounds=(-3, 3)),
                        ParameterSpace(name='y', param_type='continuous', bounds=(-3, 3)),
                        ParameterSpace(name='z', param_type='continuous', bounds=(-3, 3))
                    ]
                    objective = _acceptance_test_objective_3d
                else:  # dim == 4
                    param_spaces = [
                        ParameterSpace(name='p0', param_type='continuous', bounds=(-3, 3)),
                        ParameterSpace(name='p1', param_type='continuous', bounds=(-3, 3)),
                        ParameterSpace(name='p2', param_type='continuous', bounds=(-3, 3)),
                        ParameterSpace(name='p3', param_type='continuous', bounds=(-3, 3))
                    ]
                    # 4D objective function
                    def objective_4d(params, data):
                        return -(params['p0']**2 + params['p1']**2 + params['p2']**2 + params['p3']**2)
                    objective = objective_4d

                config = OptimizationConfig(
                    method=OptimizationMethod.RANDOM_SEARCH,
                    max_iterations=100,
                    random_state=42
                )
                optimizer = ParameterOptimizer(config)
                for ps in param_spaces:
                    optimizer.add_parameter(ps)

                dim_start = time.time()
                result = optimizer.optimize(objective, None)
                dim_time = time.time() - dim_start

                results[f'{dim}D'] = {
                    'score': result.best_score,
                    'time': dim_time,
                    'evaluations': result.n_evaluations
                }

            duration = time.time() - start

            # All optimizations should complete successfully
            success = all(r['score'] > -10 for r in results.values())

            tests.append(TestResult(
                name="Performance: Scalability Test",
                category="Performance",
                status=TestStatus.PASSED if success else TestStatus.FAILED,
                message=f"Tested {len(dimensions)} dimensions",
                duration=duration,
                details={'results': results}
            ))
            print(f"  [{'PASS' if success else 'FAIL'}] Scalability test passed")
            for dim, data in results.items():
                print(f"    {dim}: Score {data['score']:.4f}, Time {data['time']:.3f}s")

        except Exception as e:
            duration = time.time() - start
            tests.append(TestResult(
                name="Performance: Scalability Test",
                category="Performance",
                status=TestStatus.ERROR,
                message=f"Scalability test failed: {str(e)}",
                duration=duration,
                details={'error': str(e)}
            ))
            print(f"  [ERR] {str(e)}")

        return tests

    # ========================================
    # CATEGORY 4: Data Integrity Checks
    # ========================================

    def _test_data_integrity(self) -> List[TestResult]:
        """Test 4: Data integrity and validation"""
        print("\n" + "="*70)
        print("CATEGORY 4: DATA INTEGRITY")
        print("="*70)

        tests = []

        # Test 4.1: Result serialization
        print("\n[Test 4.1] Result Data Serialization")
        start = time.time()
        try:
            from parameter_optimizer import OptimizationResult
            import json
            from dataclasses import asdict

            # Create test result
            result = OptimizationResult(
                best_params={'x': 1.0, 'y': 2.0},
                best_score=-5.0,
                best_iteration=10,
                optimization_history=[
                    {'params': {'x': 0, 'y': 0}, 'score': 0},
                    {'params': {'x': 1, 'y': 2}, 'score': -5}
                ],
                convergence_curve=[0, -2, -4, -5],
                n_evaluations=100,
                runtime=1.5
            )

            # Serialize to JSON
            result_dict = asdict(result)
            json_str = json.dumps(result_dict)
            parsed_back = json.loads(json_str)

            duration = time.time() - start

            # Verify all fields preserved
            success = (
                parsed_back['best_params'] == result.best_params and
                parsed_back['best_score'] == result.best_score and
                len(parsed_back['optimization_history']) == 2
            )

            tests.append(TestResult(
                name="Data Integrity: Result Serialization",
                category="Data Integrity",
                status=TestStatus.PASSED if success else TestStatus.FAILED,
                message=f"Serialization successful, size: {len(json_str)} bytes",
                duration=duration,
                details={
                    'json_size': len(json_str),
                    'fields_preserved': success
                }
            ))
            print(f"  [{'PASS' if success else 'FAIL'}] JSON size: {len(json_str)} bytes")

        except Exception as e:
            duration = time.time() - start
            tests.append(TestResult(
                name="Data Integrity: Result Serialization",
                category="Data Integrity",
                status=TestStatus.ERROR,
                message=f"Serialization failed: {str(e)}",
                duration=duration,
                details={'error': str(e)}
            ))
            print(f"  [ERR] {str(e)}")

        # Test 4.2: Parameter validation
        print("\n[Test 4.2] Parameter Space Validation")
        start = time.time()
        try:
            from parameter_optimizer import ParameterSpace

            # Valid parameter space
            valid_ps = ParameterSpace(
                name='test_param',
                param_type='continuous',
                bounds=(0, 10)
            )

            # Invalid parameter type (should raise error)
            try:
                invalid_ps = ParameterSpace(
                    name='invalid',
                    param_type='invalid_type',
                    bounds=(0, 10)
                )
                # If we get here, validation didn't work
                validation_works = False
            except ValueError:
                # Expected behavior
                validation_works = True

            duration = time.time() - start

            tests.append(TestResult(
                name="Data Integrity: Parameter Validation",
                category="Data Integrity",
                status=TestStatus.PASSED if validation_works else TestStatus.FAILED,
                message=f"Parameter validation: {'Working' if validation_works else 'Failed'}",
                duration=duration,
                details={'validation_works': validation_works}
            ))
            print(f"  [{'PASS' if validation_works else 'FAIL'}] Validation: {'Working' if validation_works else 'Failed'}")

        except Exception as e:
            duration = time.time() - start
            tests.append(TestResult(
                name="Data Integrity: Parameter Validation",
                category="Data Integrity",
                status=TestStatus.ERROR,
                message=f"Validation test failed: {str(e)}",
                duration=duration,
                details={'error': str(e)}
            ))
            print(f"  [ERR] {str(e)}")

        return tests

    # ========================================
    # CATEGORY 5: Integration Validation
    # ========================================

    def _test_integration(self) -> List[TestResult]:
        """Test 5: Full system integration"""
        print("\n" + "="*70)
        print("CATEGORY 5: SYSTEM INTEGRATION")
        print("="*70)

        tests = []

        # Test 5.1: Complete workflow integration
        print("\n[Test 5.1] Complete Workflow Integration")
        start = time.time()
        try:
            from parameter_optimizer import (
                ParameterOptimizer, ParameterSpace, OptimizationConfig,
                OptimizationMethod, OptimizationResult
            )
            from optimization_visualization import OptimizationVisualizer

            # Setup
            param_spaces = [
                ParameterSpace(name='x', param_type='continuous', bounds=(-5, 5)),
                ParameterSpace(name='y', param_type='continuous', bounds=(-5, 5))
            ]

            def objective(params, data):
                return -(params['x']**2 + params['y']**2)

            methods_to_test = [
                OptimizationMethod.GRID_SEARCH,
                OptimizationMethod.RANDOM_SEARCH
            ]

            # Run multiple optimizations
            results = []
            for method in methods_to_test:
                config = OptimizationConfig(
                    method=method,
                    max_iterations=100,
                    random_state=42
                )
                optimizer = ParameterOptimizer(config)
                for ps in param_spaces:
                    optimizer.add_parameter(ps)

                result = optimizer.optimize(objective, None)
                results.append(result)

            # Create visualizations
            viz = OptimizationVisualizer()
            fig = viz.plot_convergence(
                results,
                [m.value for m in methods_to_test],
                save_path=None
            )

            duration = time.time() - start

            success = (
                len(results) == 2 and
                fig is not None and
                all(r.best_score > -5.0 for r in results)
            )

            tests.append(TestResult(
                name="Integration: Complete Workflow",
                category="Integration",
                status=TestStatus.PASSED if success else TestStatus.FAILED,
                message=f"Workflow: {len(results)} optimizations, {1 if fig else 0} visualization(s)",
                duration=duration,
                details={
                    'n_optimizations': len(results),
                    'visualization_created': fig is not None,
                    'scores': [r.best_score for r in results]
                }
            ))
            print(f"  [{'PASS' if success else 'FAIL'}] Complete workflow successful")

            # Clean up
            if fig:
                import matplotlib.pyplot as plt
                plt.close(fig)

        except Exception as e:
            duration = time.time() - start
            tests.append(TestResult(
                name="Integration: Complete Workflow",
                category="Integration",
                status=TestStatus.ERROR,
                message=f"Workflow failed: {str(e)}",
                duration=duration,
                details={'error': str(e)}
            ))
            print(f"  [ERR] {str(e)}")

        return tests

    # ========================================
    # Main Test Runner
    # ========================================

    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run complete system acceptance test suite

        Returns:
            Dict with test results and summary
        """
        print("\n" + "="*70)
        print("CBSC BACKTEST SYSTEM - ACCEPTANCE TEST SUITE")
        print("="*70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Python: {sys.version}")
        print(f"Working Directory: {os.getcwd()}")

        # Run all test categories
        all_test_runs = [
            self._test_imports(),
            self._test_core_functionality(),
            self._test_performance(),
            self._test_data_integrity(),
            self._test_integration()
        ]

        # Flatten results
        for test_results in all_test_runs:
            self.results.extend(test_results)

        # Calculate summary
        total_time = time.time() - self.start_time
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)

        # Print summary
        self._print_summary(total_time, total_tests, passed, failed, errors, skipped)

        # Save results
        self._save_results()

        return {
            'total_tests': total_tests,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'skipped': skipped,
            'success_rate': (passed / total_tests * 100) if total_tests > 0 else 0,
            'total_time': total_time,
            'results': [asdict(r) for r in self.results]
        }

    def _print_summary(self, total_time: float, total: int, passed: int,
                      failed: int, errors: int, skipped: int):
        """Print test summary"""
        print("\n" + "="*70)
        print("ACCEPTANCE TEST SUMMARY")
        print("="*70)

        print(f"\nTotal Tests: {total}")
        print(f"  Passed:  {passed} ({passed/total*100:.1f}%)" if total > 0 else "  Passed:  0")
        print(f"  Failed:  {failed} ({failed/total*100:.1f}%)" if total > 0 else "  Failed:  0")
        print(f"  Errors:  {errors} ({errors/total*100:.1f}%)" if total > 0 else "  Errors:  0")
        print(f"  Skipped: {skipped} ({skipped/total*100:.1f}%)" if total > 0 else "  Skipped: 0")

        print(f"\nSuccess Rate: {(passed/total*100):.1f}%")
        print(f"Total Time:   {total_time:.2f}s")

        # Results by category
        print("\nResults by Category:")
        print("-" * 70)
        categories = set(r.category for r in self.results)
        for category in sorted(categories):
            cat_results = [r for r in self.results if r.category == category]
            cat_passed = sum(1 for r in cat_results if r.status == TestStatus.PASSED)
            cat_total = len(cat_results)
            print(f"{category}:")
            print(f"  Total:   {cat_total}")
            print(f"  Passed:  {cat_passed}")
            print(f"  Failed:  {sum(1 for r in cat_results if r.status == TestStatus.FAILED)}")
            print(f"  Errors:  {sum(1 for r in cat_results if r.status == TestStatus.ERROR)}")

        print("\n" + "="*70)

        # Overall verdict
        success_rate = (passed / total * 100) if total > 0 else 0
        if errors > 0:
            verdict = "NOT ACCEPTED - Critical errors detected"
        elif failed > 0:
            verdict = "CONDITIONAL ACCEPTANCE - Some tests failed"
        elif success_rate >= 95:
            verdict = "FULLY ACCEPTED - System ready for production"
        else:
            verdict = "ACCEPTED - System meets minimum requirements"

        print(f"\nOVERALL VERDICT: {verdict}")
        print("="*70)

    def _save_results(self):
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"acceptance_test_results_{timestamp}.json"

        results_data = {
            'timestamp': datetime.now().isoformat(),
            'total_time': time.time() - self.start_time,
            'summary': {
                'total': len(self.results),
                'passed': sum(1 for r in self.results if r.status == TestStatus.PASSED),
                'failed': sum(1 for r in self.results if r.status == TestStatus.FAILED),
                'errors': sum(1 for r in self.results if r.status == TestStatus.ERROR),
                'skipped': sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
            },
            'results': [asdict(r) for r in self.results]
        }

        with open(output_path, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)

        print(f"\nResults saved to: {output_path}")


# ========================================
# Main Entry Point
# ========================================

if __name__ == "__main__":
    tester = SystemAcceptanceTest()
    results = tester.run_all_tests()

    # Exit with appropriate code
    if results['errors'] > 0:
        sys.exit(1)  # Critical errors
    elif results['failed'] > 0:
        sys.exit(2)  # Some tests failed
    else:
        sys.exit(0)  # All passed

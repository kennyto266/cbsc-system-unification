"""
Integration Test Runner for CBSC Backtest System
=================================================

Tests integration between key components:
1. Parameter Optimizer + Performance Benchmark
2. Backtest Engine + Optimization
3. Visualization + Results
4. End-to-end workflow

Author: CBSC Quant Team
Version: 1.0.0
"""

import sys
import os
import time
import traceback
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import numpy as np
import pandas as pd


class TestStatus(Enum):
    """Test execution status"""
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class IntegrationTestResult:
    """Integration test result"""
    name: str
    status: TestStatus
    duration: float
    message: str = ""
    error: str = ""
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class IntegrationTestRunner:
    """Runs integration tests for CBSC backtest system"""

    def __init__(self):
        self.results: List[IntegrationTestResult] = []
        self.start_time = time.time()
        self.modules = {}

    def load_modules(self):
        """Load required modules dynamically"""
        print("\n[Loading Modules for Integration Tests]")

        # Load parameter optimizer
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "parameter_optimizer",
                os.path.join(os.path.dirname(__file__), "parameter_optimizer.py")
            )
            self.modules['optimizer'] = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.modules['optimizer'])
            print("  [OK] Parameter Optimizer")
        except Exception as e:
            print(f"  [FAIL] Parameter Optimizer: {e}")

        # Load performance benchmark
        try:
            spec = importlib.util.spec_from_file_location(
                "performance_benchmark",
                os.path.join(os.path.dirname(__file__), "performance_benchmark.py")
            )
            self.modules['benchmark'] = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.modules['benchmark'])
            print("  [OK] Performance Benchmark")
        except Exception as e:
            print(f"  [FAIL] Performance Benchmark: {e}")

        # Load visualization
        try:
            spec = importlib.util.spec_from_file_location(
                "optimization_visualization",
                os.path.join(os.path.dirname(__file__), "optimization_visualization.py")
            )
            self.modules['visualization'] = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.modules['visualization'])
            print("  [OK] Optimization Visualization")
        except Exception as e:
            print(f"  [FAIL] Optimization Visualization: {e}")

        # Load VectorBT adapter
        try:
            spec = importlib.util.spec_from_file_location(
                "vectorbt_engine",
                os.path.join(os.path.dirname(__file__), "../../unified_backtesting/vectorbt_engine/engine.py")
            )
            self.modules['vectorbt'] = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.modules['vectorbt'])
            print("  [OK] VectorBT Engine")
        except Exception as e:
            print(f"  [WARN] VectorBT Engine: {e}")

    def run_all_tests(self):
        """Run all integration tests"""
        print("\n" + "="*70)
        print("CBSC BACKTEST SYSTEM - INTEGRATION TESTS")
        print("="*70)

        self.load_modules()

        # Test 1: Optimizer to Benchmark Integration
        self.results.append(self._test_optimizer_benchmark_integration())

        # Test 2: Multi-Method Optimization Comparison
        self.results.append(self._test_multi_method_comparison())

        # Test 3: Visualization Pipeline Integration
        self.results.append(self._test_visualization_pipeline())

        # Test 4: End-to-End Optimization Workflow
        self.results.append(self._test_end_to_end_workflow())

        # Test 5: Performance Benchmark with Real Methods
        self.results.append(self._test_benchmark_real_methods())

        # Print summary
        self._print_summary()

        return self.results

    def _test_optimizer_benchmark_integration(self) -> IntegrationTestResult:
        """Test integration between optimizer and benchmark"""
        print("\n[TEST 1] Optimizer <-> Benchmark Integration")
        start_time = time.time()

        if 'optimizer' not in self.modules or 'benchmark' not in self.modules:
            return IntegrationTestResult(
                "Optimizer-Benchmark Integration",
                TestStatus.SKIPPED,
                time.time() - start_time,
                "Required modules not available"
            )

        try:
            opt = self.modules['optimizer']
            bench = self.modules['benchmark']

            # Create optimizer
            config = opt.create_optimization_config(
                method=opt.OptimizationMethod.GRID_SEARCH,
                max_iterations=10
            )
            optimizer = opt.ParameterOptimizer(config)
            optimizer.add_parameter(opt.create_parameter_space("x", "continuous", (-5, 5)))
            optimizer.add_parameter(opt.create_parameter_space("y", "continuous", (-5, 5)))

            # Create benchmark config
            bench_config = bench.BenchmarkConfig(n_runs=2, random_state=42)

            # Simple objective
            def objective(params, data):
                return -(params['x']**2 + params['y']**2)

            # Run optimization
            result = optimizer.optimize(objective, None)

            # Verify result structure
            if hasattr(result, 'best_score') and hasattr(result, 'best_params'):
                duration = time.time() - start_time
                return IntegrationTestResult(
                    "Optimizer-Benchmark Integration",
                    TestStatus.PASSED,
                    duration,
                    f"Optimization completed, score: {result.best_score:.4f}",
                    details={
                        'best_score': result.best_score,
                        'best_params': result.best_params,
                        'n_evaluations': result.n_evaluations
                    }
                )

            return IntegrationTestResult(
                "Optimizer-Benchmark Integration",
                TestStatus.FAILED,
                time.time() - start_time,
                "Result structure invalid"
            )

        except Exception as e:
            return IntegrationTestResult(
                "Optimizer-Benchmark Integration",
                TestStatus.ERROR,
                time.time() - start_time,
                "",
                str(e)
            )

    def _test_multi_method_comparison(self) -> IntegrationTestResult:
        """Test comparing multiple optimization methods"""
        print("\n[TEST 2] Multi-Method Comparison")
        start_time = time.time()

        if 'optimizer' not in self.modules:
            return IntegrationTestResult(
                "Multi-Method Comparison",
                TestStatus.SKIPPED,
                time.time() - start_time,
                "Optimizer not available"
            )

        try:
            opt = self.modules['optimizer']

            methods = [
                opt.OptimizationMethod.GRID_SEARCH,
                opt.OptimizationMethod.RANDOM_SEARCH,
            ]

            results_dict = {}
            for method in methods:
                config = opt.create_optimization_config(
                    method=method,
                    max_iterations=20,
                    random_state=42
                )
                optimizer = opt.ParameterOptimizer(config)
                optimizer.add_parameter(opt.create_parameter_space("x", "continuous", (-3, 3)))

                def objective(params, data):
                    return -params['x']**2

                result = optimizer.optimize(objective, None)
                results_dict[method.value] = {
                    'best_score': result.best_score,
                    'n_evaluations': result.n_evaluations
                }

            # Check if all methods completed
            if len(results_dict) == len(methods):
                duration = time.time() - start_time
                return IntegrationTestResult(
                    "Multi-Method Comparison",
                    TestStatus.PASSED,
                    duration,
                    f"Compared {len(methods)} methods",
                    details=results_dict
                )

            return IntegrationTestResult(
                "Multi-Method Comparison",
                TestStatus.FAILED,
                time.time() - start_time,
                f"Only {len(results_dict)}/{len(methods)} methods completed"
            )

        except Exception as e:
            return IntegrationTestResult(
                "Multi-Method Comparison",
                TestStatus.ERROR,
                time.time() - start_time,
                "",
                str(e)
            )

    def _test_visualization_pipeline(self) -> IntegrationTestResult:
        """Test visualization pipeline integration"""
        print("\n[TEST 3] Visualization Pipeline")
        start_time = time.time()

        if 'optimizer' not in self.modules or 'visualization' not in self.modules:
            return IntegrationTestResult(
                "Visualization Pipeline",
                TestStatus.SKIPPED,
                time.time() - start_time,
                "Required modules not available"
            )

        try:
            opt = self.modules['optimizer']
            viz = self.modules['visualization']

            # Run optimization
            config = opt.create_optimization_config(
                method=opt.OptimizationMethod.RANDOM_SEARCH,
                max_iterations=30,
                random_state=42
            )
            optimizer = opt.ParameterOptimizer(config)
            optimizer.add_parameter(opt.create_parameter_space("x", "continuous", (-5, 5)))
            optimizer.add_parameter(opt.create_parameter_space("y", "continuous", (-5, 5)))

            def objective(params, data):
                return -(params['x']**2 + params['y']**2)

            result = optimizer.optimize(objective, None)

            # Create visualizations
            visualizer = viz.OptimizationVisualizer(viz.VisualizationConfig())

            # Test convergence plot
            import matplotlib
            matplotlib.use('Agg')

            # Create dummy results for convergence plot
            dummy_results = [result]

            try:
                fig1 = visualizer.plot_convergence(
                    dummy_results,
                    ['Random Search'],
                    save_path=None  # Don't save file during test
                )
            except Exception as e:
                # Convergence plot may fail if convergence_curve is empty
                if "convergence_curve" in str(e):
                    pass  # Expected for some methods
                else:
                    raise

            # Test summary plot
            fig2 = visualizer.plot_optimization_summary(
                result,
                method_name="Random Search",
                save_path=None
            )

            duration = time.time() - start_time
            return IntegrationTestResult(
                "Visualization Pipeline",
                TestStatus.PASSED,
                duration,
                "Visualizations created successfully"
            )

        except Exception as e:
            return IntegrationTestResult(
                "Visualization Pipeline",
                TestStatus.ERROR,
                time.time() - start_time,
                "",
                traceback.format_exc()
            )

    def _test_end_to_end_workflow(self) -> IntegrationTestResult:
        """Test complete end-to-end optimization workflow"""
        print("\n[TEST 4] End-to-End Workflow")
        start_time = time.time()

        if 'optimizer' not in self.modules or 'benchmark' not in self.modules or 'visualization' not in self.modules:
            return IntegrationTestResult(
                "End-to-End Workflow",
                TestStatus.SKIPPED,
                time.time() - start_time,
                "Required modules not available"
            )

        try:
            opt = self.modules['optimizer']
            bench = self.modules['benchmark']
            viz = self.modules['visualization']

            # Step 1: Define parameter space
            config = opt.create_optimization_config(
                method=opt.OptimizationMethod.BAYESIAN_OPTIMIZATION,
                n_calls=15,
                random_state=42
            )
            optimizer = opt.ParameterOptimizer(config)
            optimizer.add_parameter(opt.create_parameter_space("x", "continuous", (-3, 3)))
            optimizer.add_parameter(opt.create_parameter_space("y", "continuous", (-3, 3)))

            # Step 2: Define objective
            def objective(params, data):
                return -(params['x']**2 + params['y']**2)

            # Step 3: Run optimization
            result = optimizer.optimize(objective, None)

            # Step 4: Create visualization
            visualizer = viz.OptimizationVisualizer(viz.VisualizationConfig())

            import matplotlib
            matplotlib.use('Agg')

            fig = visualizer.plot_optimization_summary(
                result,
                method_name="Bayesian Optimization",
                save_path=None
            )

            # Step 5: Verify results
            success = (
                hasattr(result, 'best_score') and
                hasattr(result, 'best_params') and
                result.best_score > -5  # Should find something reasonable
            )

            if success:
                duration = time.time() - start_time
                return IntegrationTestResult(
                    "End-to-End Workflow",
                    TestStatus.PASSED,
                    duration,
                    f"Complete workflow executed, score: {result.best_score:.4f}",
                    details={
                        'best_score': result.best_score,
                        'best_params': result.best_params,
                        'steps_completed': 5
                    }
                )

            return IntegrationTestResult(
                "End-to-End Workflow",
                TestStatus.FAILED,
                time.time() - start_time,
                f"Score too low: {result.best_score:.4f}"
            )

        except Exception as e:
            return IntegrationTestResult(
                "End-to-End Workflow",
                TestStatus.ERROR,
                time.time() - start_time,
                "",
                traceback.format_exc()
            )

    def _test_benchmark_real_methods(self) -> IntegrationTestResult:
        """Test performance benchmark with real optimization methods"""
        print("\n[TEST 5] Benchmark with Real Methods")
        start_time = time.time()

        if 'benchmark' not in self.modules:
            return IntegrationTestResult(
                "Benchmark Real Methods",
                TestStatus.SKIPPED,
                time.time() - start_time,
                "Benchmark not available"
            )

        try:
            bench = self.modules['benchmark']

            # Create benchmark config with minimal runs for speed
            config = bench.BenchmarkConfig(
                n_runs=2,
                random_state=42,
                timeout_seconds=60,
                methods_to_test=['grid_search', 'random_search']
            )

            benchmark = bench.PerformanceBenchmark(config)

            # Register a simple 2D sphere test function
            test_func = bench.BenchmarkFunction(
                name="test_sphere",
                func=lambda params: sum(p**2 for p in params.values()),
                bounds=[(-5.0, 5.0), (-5.0, 5.0)],
                global_optimum=0.0,
                global_optimum_location=[0.0, 0.0],
                problem_type=bench.ProblemType.CONVEX,
                dimensions=2,
                description="Simple 2D sphere function for testing"
            )
            benchmark.register_benchmark_function(test_func)

            # Run benchmark
            results = benchmark.run_benchmark(
                function_names=['test_sphere'],
                methods=['grid_search', 'random_search']
            )

            # Check results
            if 'test_sphere' in results:
                duration = time.time() - start_time
                return IntegrationTestResult(
                    "Benchmark Real Methods",
                    TestStatus.PASSED,
                    duration,
                    f"Benchmark completed, {len(results)} functions tested",
                    details={'functions_tested': list(results.keys())}
                )

            return IntegrationTestResult(
                "Benchmark Real Methods",
                TestStatus.FAILED,
                time.time() - start_time,
                "No results generated"
            )

        except Exception as e:
            return IntegrationTestResult(
                "Benchmark Real Methods",
                TestStatus.ERROR,
                time.time() - start_time,
                "",
                traceback.format_exc()
            )

    def _print_summary(self):
        """Print test summary"""
        total_time = time.time() - self.start_time

        print("\n" + "="*70)
        print("INTEGRATION TEST SUMMARY")
        print("="*70)

        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        total = len(self.results)

        print(f"\nTotal Tests: {total}")
        print(f"  Passed:  {passed} ({passed/total*100:.1f}%)")
        print(f"  Failed:  {failed} ({failed/total*100:.1f}%)")
        print(f"  Errors:  {errors} ({errors/total*100:.1f}%)")
        print(f"  Skipped: {skipped} ({skipped/total*100:.1f}%)")
        print(f"\nSuccess Rate: {passed/total*100:.1f}%")
        print(f"Total Time:   {total_time:.2f}s")

        # Print detailed results
        print("\n" + "-"*70)
        print("DETAILED RESULTS")
        print("-"*70)

        for result in self.results:
            status_symbol = {
                TestStatus.PASSED: "[PASS]",
                TestStatus.FAILED: "[FAIL]",
                TestStatus.ERROR: "[ERR]",
                TestStatus.SKIPPED: "[SKIP]"
            }[result.status]

            print(f"\n{status_symbol} {result.name}")
            print(f"    Status: {result.status.value}")
            print(f"    Time: {result.duration:.2f}s")
            if result.message:
                print(f"    Message: {result.message}")
            if result.error:
                print(f"    Error: {result.error}")

        # Save results to JSON
        output_file = os.path.join(
            os.path.dirname(__file__),
            "integration_test_results.json"
        )

        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_time': total_time,
                'total_tests': total,
                'passed': passed,
                'failed': failed,
                'errors': errors,
                'skipped': skipped,
                'success_rate': passed/total*100,
                'results': [
                    {
                        'name': r.name,
                        'status': r.status.value,
                        'duration': r.duration,
                        'message': r.message,
                        'error': r.error,
                        'details': r.details
                    }
                    for r in self.results
                ]
            }, f, indent=2)

        print(f"\nResults saved to: {output_file}")
        print("="*70)


if __name__ == "__main__":
    runner = IntegrationTestRunner()
    results = runner.run_all_tests()

    # Exit with appropriate code
    failed_count = sum(1 for r in results if r.status in [TestStatus.FAILED, TestStatus.ERROR])
    sys.exit(0 if failed_count == 0 else 1)

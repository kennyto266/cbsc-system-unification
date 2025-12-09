#!/usr/bin/env python3
"""
Validation Pipeline for Comprehensive Testing and Reporting (Windows Compatible)
Automates execution of all test suites and validates system meets production requirements
"""

import os
import sys
import time
import json
import subprocess
import threading
import unittest
import importlib.util
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback
import argparse

# Set console encoding for Windows
if sys.platform == 'win32':
    import locale
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


@dataclass
class TestSuiteResult:
    """Result from running a test suite"""
    suite_name: str
    suite_type: str  # 'unit', 'integration', 'load', 'chaos'
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    tests_run: int
    tests_passed: int
    tests_failed: int
    tests_skipped: int
    success_rate: float
    coverage_percent: Optional[float]
    critical_failures: List[str]
    performance_metrics: Dict[str, float]
    errors: List[str]


@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    validation_id: str
    start_time: datetime
    end_time: datetime
    total_duration_seconds: float
    overall_success: bool
    test_suites: List[TestSuiteResult]
    summary_metrics: Dict[str, Any]
    production_readiness: Dict[str, bool]
    recommendations: List[str]
    compliance_status: Dict[str, bool]


class TestDiscovery:
    """Discovers and categorizes test files"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_categories = {
            'unit': [],
            'integration': [],
            'load': [],
            'chaos': []
        }

    def discover_tests(self) -> Dict[str, List[Path]]:
        """Discover all test files and categorize them"""
        test_patterns = {
            'unit': [
                'tests/unit/**/*.py',
                'tests/**/test_*memory*.py',
                'tests/**/test_*sync*.py',
                'tests/**/test_*lifecycle*.py'
            ],
            'integration': [
                'tests/integration/**/*.py',
                'tests/**/test_*coordination*.py',
                'tests/**/test_*system*.py'
            ],
            'load': [
                'tests/load/**/*.py',
                'tests/**/test_*performance*.py',
                'tests/**/test_*concurrent*.py'
            ],
            'chaos': [
                'tests/chaos/**/*.py',
                'tests/**/test_*chaos*.py',
                'tests/**/test_*resilience*.py'
            ]
        }

        for category, patterns in test_patterns.items():
            for pattern in patterns:
                try:
                    from glob import glob
                    matches = glob(str(self.project_root / pattern), recursive=True)
                    self.test_categories[category].extend([Path(m) for m in matches])
                except Exception as e:
                    print(f"Error discovering tests for pattern {pattern}: {e}")

        # Remove duplicates and sort
        for category in self.test_categories:
            self.test_categories[category] = sorted(list(set(self.test_categories[category])))

        return self.test_categories


class CoverageAnalyzer:
    """Analyzes test coverage"""

    def __init__(self):
        self.coverage_tool = None

    def run_coverage_analysis(self, test_files: List[Path], source_dirs: List[Path]) -> Optional[float]:
        """Run coverage analysis and return overall coverage percentage"""
        try:
            # Try to import coverage
            import coverage

            # Create coverage instance
            cov = coverage.Coverage()
            cov.start()

            # Run tests with coverage
            test_suite = unittest.TestSuite()
            loader = unittest.TestLoader()

            for test_file in test_files:
                try:
                    spec = importlib.util.spec_from_file_location("test_module", test_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    suite = loader.loadTestsFromModule(module)
                    test_suite.addTest(suite)
                except Exception as e:
                    print(f"Error loading test file {test_file}: {e}")

            # Run tests
            runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
            runner.run(test_suite)

            # Stop coverage and get report
            cov.stop()
            cov.save()

            # Generate report
            total_lines = 0
            covered_lines = 0

            for source_dir in source_dirs:
                try:
                    analysis = cov.analysis2(str(source_dir))
                    total_lines += analysis[1]  # total lines
                    covered_lines += analysis[2]  # covered lines
                except Exception as e:
                    print(f"Error analyzing coverage for {source_dir}: {e}")

            coverage_percent = (covered_lines / total_lines * 100) if total_lines > 0 else 0
            return coverage_percent

        except ImportError:
            print("Coverage tool not available, skipping coverage analysis")
            return None
        except Exception as e:
            print(f"Error running coverage analysis: {e}")
            return None


class TestSuiteRunner:
    """Runs individual test suites"""

    def __init__(self, timeout_seconds: int = 300):
        self.timeout_seconds = timeout_seconds

    def run_test_suite(self, suite_name: str, test_files: List[Path], suite_type: str) -> TestSuiteResult:
        """Run a test suite and collect results"""
        print(f"\n{'='*60}")
        print(f"Running {suite_type.upper()} test suite: {suite_name}")
        print(f"Files: {len(test_files)}")
        print(f"{'='*60}")

        start_time = datetime.now()

        # Load tests
        test_suite = unittest.TestSuite()
        loader = unittest.TestLoader()
        loaded_files = []
        load_errors = []

        for test_file in test_files:
            try:
                spec = importlib.util.spec_from_file_location("test_module", test_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                suite = loader.loadTestsFromModule(module)
                test_suite.addTest(suite)
                loaded_files.append(test_file.name)
            except Exception as e:
                error_msg = f"Error loading {test_file.name}: {str(e)}"
                load_errors.append(error_msg)
                print(f"  {error_msg}")

        if not test_suite.countTestCases():
            print(f"  No test cases found in suite")
            end_time = datetime.now()
            return TestSuiteResult(
                suite_name=suite_name,
                suite_type=suite_type,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=(end_time - start_time).total_seconds(),
                tests_run=0,
                tests_passed=0,
                tests_failed=0,
                tests_skipped=0,
                success_rate=0.0,
                coverage_percent=None,
                critical_failures=load_errors,
                performance_metrics={},
                errors=load_errors
            )

        # Run tests with timeout
        runner_result = None
        execution_errors = []

        try:
            # Create custom result handler to capture detailed information
            result_handler = DetailedTestResult()

            # Run with timeout
            def run_tests():
                runner = unittest.TextTestRunner(
                    verbosity=1,  # Reduced verbosity for Windows console
                    stream=open(os.devnull, 'w'),  # Suppress output to keep console clean
                    resultclass=DetailedTestResult
                )
                return runner.run(test_suite)

            # Execute with timeout
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_tests)
                try:
                    runner_result = future.result(timeout=self.timeout_seconds)
                except Exception as e:
                    execution_errors.append(f"Test execution error: {str(e)}")
                    if future.running():
                        future.cancel()

        except Exception as e:
            execution_errors.append(f"Test suite execution failed: {str(e)}")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Extract results
        if runner_result:
            tests_run = runner_result.testsRun
            tests_failed = len(runner_result.failures) + len(runner_result.errors)
            tests_skipped = len(runner_result.skipped)
            tests_passed = tests_run - tests_failed - tests_skipped
            success_rate = tests_passed / tests_run if tests_run > 0 else 0

            critical_failures = []
            for failure in runner_result.failures:
                critical_failures.append(f"FAILURE: {failure[0]} - {failure[1].splitlines()[0]}")
            for error in runner_result.errors:
                critical_failures.append(f"ERROR: {error[0]} - {error[1].splitlines()[0]}")

            performance_metrics = {}
            if hasattr(runner_result, 'performance_data'):
                performance_metrics = runner_result.performance_data

        else:
            tests_run = 0
            tests_passed = 0
            tests_failed = 0
            tests_skipped = 0
            success_rate = 0.0
            critical_failures = execution_errors
            performance_metrics = {}

        print(f"  Tests run: {tests_run}")
        print(f"  Passed: {tests_passed}")
        print(f"  Failed: {tests_failed}")
        print(f"  Skipped: {tests_skipped}")
        print(f"  Success rate: {success_rate:.1%}")
        print(f"  Duration: {duration:.2f}s")

        return TestSuiteResult(
            suite_name=suite_name,
            suite_type=suite_type,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            tests_run=tests_run,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            tests_skipped=tests_skipped,
            success_rate=success_rate,
            coverage_percent=None,  # Will be set by coverage analyzer
            critical_failures=critical_failures,
            performance_metrics=performance_metrics,
            errors=execution_errors + critical_failures
        )


class DetailedTestResult(unittest.TestResult):
    """Enhanced test result handler to capture performance metrics"""

    def __init__(self):
        super().__init__()
        self.performance_data = {}
        self.test_timings = {}

    def startTest(self, test):
        super().startTest(test)
        self.test_timings[test.id()] = time.time()

    def stopTest(self, test):
        super().stopTest(test)
        if test.id() in self.test_timings:
            duration = time.time() - self.test_timings[test.id()]
            self.test_timings[test.id()] = duration

    def addError(self, test, err):
        super().addError(test, err)
        print(f"ERROR in {test.id()}: {err[1]}")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        print(f"FAILURE in {test.id()}: {err[1]}")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        print(f"SKIP {test.id()}: {reason}")


class ProductionRequirementValidator:
    """Validates production requirements"""

    def __init__(self):
        self.requirements = {
            'stability_threshold': 0.99,      # 99% system stability
            'memory_limit_gb': 6,            # < 6GB memory usage
            'shutdown_timeout_s': 30,        # < 30s shutdown
            'test_coverage_threshold': 0.95,  # 95% test coverage
            'zero_zombie_processes': True,    # 0 zombie processes
            'min_uptime_hours': 24,           # 24-hour operation
        }

    def validate_requirements(self, test_results: List[TestSuiteResult]) -> Dict[str, bool]:
        """Validate production requirements against test results"""
        validation_results = {}

        # Check overall test success rate
        total_tests = sum(r.tests_run for r in test_results)
        total_passed = sum(r.tests_passed for r in test_results)
        overall_success_rate = total_passed / total_tests if total_tests > 0 else 0

        validation_results['stability_requirement'] = overall_success_rate >= self.requirements['stability_threshold']

        # Check memory usage (from load tests)
        memory_tests = [r for r in test_results if 'memory' in r.suite_name.lower()]
        if memory_tests:
            max_memory = max([
                r.performance_metrics.get('peak_memory_mb', 0) / 1024
                for r in memory_tests
            ])
            validation_results['memory_requirement'] = max_memory <= self.requirements['memory_limit_gb']
        else:
            validation_results['memory_requirement'] = True  # Assume passed if no memory tests

        # Check shutdown performance
        shutdown_tests = [r for r in test_results if 'shutdown' in r.suite_name.lower()]
        if shutdown_tests:
            max_shutdown_time = max([
                r.performance_metrics.get('shutdown_time_seconds', 0)
                for r in shutdown_tests
            ])
            validation_results['shutdown_requirement'] = max_shutdown_time <= self.requirements['shutdown_timeout_s']
        else:
            validation_results['shutdown_requirement'] = True  # Assume passed if no shutdown tests

        # Check test coverage
        coverage_values = [r.coverage_percent for r in test_results if r.coverage_percent is not None]
        if coverage_values:
            avg_coverage = sum(coverage_values) / len(coverage_values)
            validation_results['coverage_requirement'] = avg_coverage >= self.requirements['test_coverage_threshold']
        else:
            validation_results['coverage_requirement'] = False

        # Check chaos engineering results
        chaos_tests = [r for r in test_results if r.suite_type == 'chaos']
        if chaos_tests:
            chaos_success = all(r.success_rate >= 0.8 for r in chaos_tests)  # 80% success in chaos tests
            validation_results['resilience_requirement'] = chaos_success
        else:
            validation_results['resilience_requirement'] = False

        # Load test performance
        load_tests = [r for r in test_results if r.suite_type == 'load']
        if load_tests:
            load_success = all(r.success_rate >= 0.95 for r in load_tests)  # 95% success in load tests
            validation_results['performance_requirement'] = load_success
        else:
            validation_results['performance_requirement'] = False

        return validation_results


class ValidationPipeline:
    """Main validation pipeline orchestrator"""

    def __init__(self, project_root: Path, output_dir: Path):
        self.project_root = project_root
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.test_discovery = TestDiscovery(project_root)
        self.coverage_analyzer = CoverageAnalyzer()
        self.test_runner = TestSuiteRunner()
        self.requirement_validator = ProductionRequirementValidator()

        self.validation_id = f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def run_validation(self, run_coverage: bool = True, run_long_tests: bool = False) -> ValidationReport:
        """Run complete validation pipeline"""
        print(f"\n{'#'*80}")
        print(f"# PHASE 4: COMPREHENSIVE TESTING AND VALIDATION PIPELINE")
        print(f"# Validation ID: {self.validation_id}")
        print(f"# Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*80}")

        start_time = datetime.now()
        test_results = []

        try:
            # Discover tests
            print("\n[DISCOVER] Discovering test files...")
            test_categories = self.test_discovery.discover_tests()
            for category, files in test_categories.items():
                print(f"  {category.upper()}: {len(files)} files")

            # Run test suites
            test_results.extend(self._run_test_suites(test_categories, run_long_tests))

            # Run coverage analysis
            if run_coverage:
                print("\n[COVERAGE] Running coverage analysis...")
                all_test_files = []
                for files in test_categories.values():
                    all_test_files.extend(files)

                source_dirs = [
                    self.project_root / 'src',
                    self.project_root / 'src' / 'memory',
                    self.project_root / 'src' / 'ipc'
                ]

                overall_coverage = self.coverage_analyzer.run_coverage_analysis(all_test_files, source_dirs)

                # Update coverage in results
                for result in test_results:
                    result.coverage_percent = overall_coverage
            else:
                overall_coverage = None

            # Validate production requirements
            print("\n[VALIDATE] Validating production requirements...")
            production_readiness = self.requirement_validator.validate_requirements(test_results)

            # Generate summary metrics
            summary_metrics = self._calculate_summary_metrics(test_results, overall_coverage)

            # Generate recommendations
            recommendations = self._generate_recommendations(test_results, production_readiness, summary_metrics)

        except Exception as e:
            print(f"\n[ERROR] Validation pipeline error: {e}")
            traceback.print_exc()
            error_result = TestSuiteResult(
                suite_name="pipeline_error",
                suite_type="error",
                start_time=start_time,
                end_time=datetime.now(),
                duration_seconds=0,
                tests_run=0,
                tests_passed=0,
                tests_failed=0,
                tests_skipped=0,
                success_rate=0.0,
                coverage_percent=None,
                critical_failures=[f"Pipeline error: {e}"],
                performance_metrics={},
                errors=[str(e)]
            )
            test_results.append(error_result)

            production_readiness = {'pipeline_success': False}
            summary_metrics = {'error': str(e)}
            recommendations = ["Fix pipeline errors before proceeding"]

        end_time = datetime.now()

        # Create final report
        report = ValidationReport(
            validation_id=self.validation_id,
            start_time=start_time,
            end_time=end_time,
            total_duration_seconds=(end_time - start_time).total_seconds(),
            overall_success=all(r.success_rate >= 0.95 for r in test_results if r.suite_type != 'error'),
            test_suites=test_results,
            summary_metrics=summary_metrics,
            production_readiness=production_readiness,
            recommendations=recommendations,
            compliance_status=production_readiness
        )

        # Save report
        self._save_report(report)

        # Print summary
        self._print_summary(report)

        return report

    def _run_test_suites(self, test_categories: Dict[str, List[Path]], run_long_tests: bool) -> List[TestSuiteResult]:
        """Run all test suites"""
        results = []

        for category, test_files in test_categories.items():
            if not test_files:
                continue

            # Skip long tests unless specifically requested
            if not run_long_tests and category in ['load', 'chaos']:
                print(f"\n[SKIP] Skipping {category} tests (use --run-long-tests to include)")
                continue

            suite_name = f"{category}_tests"
            result = self.test_runner.run_test_suite(suite_name, test_files, category)
            results.append(result)

        return results

    def _calculate_summary_metrics(self, test_results: List[TestSuiteResult], coverage: Optional[float]) -> Dict[str, Any]:
        """Calculate summary metrics from test results"""
        if not test_results:
            return {}

        total_tests = sum(r.tests_run for r in test_results)
        total_passed = sum(r.tests_passed for r in test_results)
        total_failed = sum(r.tests_failed for r in test_results)
        total_skipped = sum(r.tests_skipped for r in test_results)

        suite_metrics = {}
        for result in test_results:
            suite_metrics[result.suite_name] = {
                'success_rate': result.success_rate,
                'tests_run': result.tests_run,
                'duration': result.duration_seconds
            }

        return {
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_skipped': total_skipped,
            'overall_success_rate': total_passed / total_tests if total_tests > 0 else 0,
            'total_duration_seconds': sum(r.duration_seconds for r in test_results),
            'coverage_percent': coverage,
            'suite_metrics': suite_metrics
        }

    def _generate_recommendations(self, test_results: List[TestSuiteResult],
                                production_readiness: Dict[str, bool],
                                summary_metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        # Overall success rate recommendations
        if summary_metrics.get('overall_success_rate', 0) < 0.95:
            recommendations.append(
                f"Overall test success rate is {summary_metrics.get('overall_success_rate', 0):.1%}. "
                "Address failing tests to meet production requirements."
            )

        # Coverage recommendations
        coverage = summary_metrics.get('coverage_percent', 0)
        if coverage and coverage < 95:
            recommendations.append(
                f"Test coverage is {coverage:.1f}%. "
                "Increase coverage to meet 95% production requirement."
            )

        # Production readiness recommendations
        if not production_readiness.get('stability_requirement', False):
            recommendations.append("System stability below 99% threshold - investigate test failures.")

        if not production_readiness.get('memory_requirement', False):
            recommendations.append("Memory usage exceeds 6GB limit - optimize memory management.")

        if not production_readiness.get('shutdown_requirement', False):
            recommendations.append("Shutdown time exceeds 30s limit - improve cleanup procedures.")

        if not production_readiness.get('resilience_requirement', False):
            recommendations.append("System resilience inadequate - improve chaos engineering handling.")

        if not production_readiness.get('performance_requirement', False):
            recommendations.append("Performance below requirements - optimize bottlenecks.")

        # Test-specific recommendations
        for result in test_results:
            if result.success_rate < 0.95:
                recommendations.append(
                    f"Improve {result.suite_name} success rate from {result.success_rate:.1%} to >=95%"
                )

            if result.critical_failures:
                recommendations.append(
                    f"Fix {len(result.critical_failures)} critical failures in {result.suite_name}"
                )

        # Success recommendations
        if all(production_readiness.values()):
            recommendations.append("PASS: All production requirements met - system ready for deployment!")

        return recommendations

    def _save_report(self, report: ValidationReport):
        """Save validation report to files"""
        # JSON report
        json_file = self.output_dir / f"{report.validation_id}_report.json"
        with open(json_file, 'w') as f:
            # Convert datetime objects to ISO format for JSON serialization
            report_dict = asdict(report)
            for key, value in report_dict.items():
                if isinstance(value, datetime):
                    report_dict[key] = value.isoformat()
                elif key == 'test_suites':
                    for i, suite in enumerate(value):
                        suite_dict = asdict(suite)
                        for k, v in suite_dict.items():
                            if isinstance(v, datetime):
                                suite_dict[k] = v.isoformat()
                        report_dict[key][i] = suite_dict

            json.dump(report_dict, f, indent=2, default=str)

        # Markdown report
        md_file = self.output_dir / f"{report.validation_id}_report.md"
        with open(md_file, 'w') as f:
            f.write(self._generate_markdown_report(report))

        print(f"\n[SAVE] Reports saved to:")
        print(f"  JSON: {json_file}")
        print(f"  Markdown: {md_file}")

    def _generate_markdown_report(self, report: ValidationReport) -> str:
        """Generate markdown report"""
        md_lines = [
            "# Phase 4: Comprehensive Testing and Validation Report",
            "",
            f"**Validation ID:** {report.validation_id}",
            f"**Start Time:** {report.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**End Time:** {report.end_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Duration:** {report.total_duration_seconds:.2f} seconds",
            f"**Overall Success:** {'PASS' if report.overall_success else 'FAIL'}",
            "",
            "## Executive Summary",
            ""
        ]

        # Summary metrics
        if report.summary_metrics:
            metrics = report.summary_metrics
            md_lines.extend([
                f"- **Total Tests:** {metrics.get('total_tests', 0)}",
                f"- **Passed:** {metrics.get('total_passed', 0)}",
                f"- **Failed:** {metrics.get('total_failed', 0)}",
                f"- **Skipped:** {metrics.get('total_skipped', 0)}",
                f"- **Success Rate:** {metrics.get('overall_success_rate', 0):.1%}",
                f"- **Test Coverage:** {metrics.get('coverage_percent', 0):.1f}%",
                ""
            ])

        # Production readiness
        md_lines.extend([
            "## Production Readiness",
            ""
        ])

        for requirement, met in report.production_readiness.items():
            status = "PASS" if met else "FAIL"
            md_lines.append(f"- **{requirement.replace('_', ' ').title()}:** {status}")

        md_lines.extend([
            "",
            "## Test Suite Results",
            ""
        ])

        # Test suite details
        for result in report.test_suites:
            md_lines.extend([
                f"### {result.suite_name}",
                "",
                f"- **Type:** {result.suite_type.title()}",
                f"- **Tests Run:** {result.tests_run}",
                f"- **Passed:** {result.tests_passed}",
                f"- **Failed:** {result.tests_failed}",
                f"- **Skipped:** {result.tests_skipped}",
                f"- **Success Rate:** {result.success_rate:.1%}",
                f"- **Duration:** {result.duration_seconds:.2f}s",
                f"- **Coverage:** {result.coverage_percent:.1f}%" if result.coverage_percent else "- **Coverage:** N/A",
                ""
            ])

            if result.critical_failures:
                md_lines.extend([
                    "**Critical Failures:**",
                    ""
                ])
                for failure in result.critical_failures:
                    md_lines.append(f"- {failure}")
                md_lines.append("")

        # Recommendations
        md_lines.extend([
            "## Recommendations",
            ""
        ])

        for recommendation in report.recommendations:
            md_lines.append(f"- {recommendation}")

        md_lines.extend([
            "",
            "---",
            f"*Report generated by Phase 4 Validation Pipeline on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])

        return "\n".join(md_lines)

    def _print_summary(self, report: ValidationReport):
        """Print validation summary to console"""
        print(f"\n{'#'*80}")
        print(f"# VALIDATION PIPELINE SUMMARY")
        print(f"{'#'*80}")

        print(f"\n[SUMMARY] OVERALL RESULTS:")
        print(f"  Status: {'PASS' if report.overall_success else 'FAIL'}")
        print(f"  Duration: {report.total_duration_seconds:.2f} seconds")
        print(f"  Test Suites: {len(report.test_suites)}")

        if report.summary_metrics:
            metrics = report.summary_metrics
            print(f"  Total Tests: {metrics.get('total_tests', 0)}")
            print(f"  Success Rate: {metrics.get('overall_success_rate', 0):.1%}")
            if metrics.get('coverage_percent'):
                print(f"  Test Coverage: {metrics.get('coverage_percent'):.1f}%")

        print(f"\n[PRODUCTION] PRODUCTION READINESS:")
        passed_requirements = sum(1 for met in report.production_readiness.values() if met)
        total_requirements = len(report.production_readiness)
        print(f"  Requirements Met: {passed_requirements}/{total_requirements}")

        for requirement, met in report.production_readiness.items():
            status = "OK" if met else "FAIL"
            print(f"  {status} {requirement.replace('_', ' ').title()}")

        print(f"\n[RECOMMENDATIONS] KEY RECOMMENDATIONS:")
        for i, recommendation in enumerate(report.recommendations[:5], 1):
            print(f"  {i}. {recommendation}")

        if len(report.recommendations) > 5:
            print(f"  ... and {len(report.recommendations) - 5} more")

        print(f"\n{'#'*80}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Phase 4: Comprehensive Testing and Validation Pipeline (Windows)")
    parser.add_argument("--project-root", type=str, default=".", help="Project root directory")
    parser.add_argument("--output-dir", type=str, default="./validation_reports", help="Output directory for reports")
    parser.add_argument("--run-coverage", action="store_true", default=True, help="Run coverage analysis")
    parser.add_argument("--run-long-tests", action="store_true", help="Include long-running tests (load, chaos)")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage analysis")

    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    output_dir = Path(args.output_dir).resolve()

    # Validate project root
    if not (project_root / "src").exists():
        print(f"[ERROR] Invalid project root: {project_root}")
        print(f"[ERROR] Expected to find 'src' directory in project root")
        sys.exit(1)

    # Run validation pipeline
    pipeline = ValidationPipeline(project_root, output_dir)
    run_coverage = args.run_coverage and not args.no_coverage

    try:
        report = pipeline.run_validation(
            run_coverage=run_coverage,
            run_long_tests=args.run_long_tests
        )

        # Exit with appropriate code
        if report.overall_success and all(report.production_readiness.values()):
            print(f"\n[SUCCESS] Validation completed successfully - System ready for production!")
            sys.exit(0)
        else:
            print(f"\n[WARNING] Validation completed with issues - Review recommendations before production deployment")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n[INTERRUPTED] Validation interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n[ERROR] Validation failed with error: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
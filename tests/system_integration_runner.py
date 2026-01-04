"""
System Integration Test Runner
Orchestrates all system integration tests and generates comprehensive reports
"""

import asyncio
import json
import logging
import time
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import sys
import os

# Import all test modules
from tests.integration.test_end_to_end_system import EndToEndTestSuite
from tests.api.comprehensive_api_test_suite import ComprehensiveAPITestSuite
from tests.integrity.data_flow_integrity_validator import DataFlowIntegrityValidator
from tests.performance.performance_benchmark_suite import PerformanceBenchmarkSuite
from tests.load.load_testing_framework import LoadTestingFramework, LoadTestType, LoadPattern
from tests.disaster.disaster_recovery_testing import DisasterRecoveryTester, DisasterType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"test_logs/system_integration_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TestSuiteConfig:
    """Configuration for test suite execution"""
    run_end_to_end: bool = True
    run_api_tests: bool = True
    run_integrity_tests: bool = True
    run_performance_tests: bool = True
    run_load_tests: bool = True
    run_disaster_tests: bool = False  # Disabled by default for safety

    # Test parameters
    test_timeout_minutes: int = 60
    parallel_execution: bool = False
    generate_reports: bool = True
    continue_on_failure: bool = True

    # Environment settings
    environment: str = "test"
    base_url: str = "http://localhost:3003"
    skip_slow_tests: bool = False


@dataclass
class TestSuiteResult:
    """Overall test suite execution result"""
    start_time: datetime
    end_time: datetime
    duration_seconds: float

    # Test suite results
    end_to_end_result: Optional[Dict] = None
    api_test_result: Optional[Dict] = None
    integrity_test_result: Optional[Dict] = None
    performance_test_result: Optional[Dict] = None
    load_test_result: Optional[Dict] = None
    disaster_test_result: Optional[Dict] = None

    # Overall metrics
    total_tests_run: int = 0
    total_tests_passed: int = 0
    total_tests_failed: int = 0
    overall_success: bool = True

    # Performance summary
    avg_response_time: float = 0.0
    peak_throughput: float = 0.0
    system_resources_peak: Dict[str, float] = None

    # Issues identified
    critical_issues: List[str] = None
    performance_issues: List[str] = None
    security_issues: List[str] = None
    reliability_issues: List[str] = None

    # Recommendations
    recommendations: List[str] = None

    def __post_init__(self):
        if self.system_resources_peak is None:
            self.system_resources_peak = {}
        if self.critical_issues is None:
            self.critical_issues = []
        if self.performance_issues is None:
            self.performance_issues = []
        if self.security_issues is None:
            self.security_issues = []
        if self.reliability_issues is None:
            self.reliability_issues = []
        if self.recommendations is None:
            self.recommendations = []


class SystemIntegrationTestRunner:
    """Main test runner for system integration testing"""

    def __init__(self, config: TestSuiteConfig):
        self.config = config
        self.result = TestSuiteResult(start_time=datetime.utcnow())

        # Ensure log directory exists
        os.makedirs("test_logs", exist_ok=True)
        os.makedirs("test_reports", exist_ok=True)

    async def run_all_tests(self) -> TestSuiteResult:
        """Run all configured test suites"""
        logger.info("="*60)
        logger.info("STARTING COMPREHENSIVE SYSTEM INTEGRATION TESTING")
        logger.info("="*60)

        try:
            # Test phases
            test_phases = []

            if self.config.run_end_to_end:
                test_phases.append(("End-to-End Integration Tests", self._run_end_to_end_tests))

            if self.config.run_api_tests:
                test_phases.append(("API Tests", self._run_api_tests))

            if self.config.run_integrity_tests:
                test_phases.append(("Data Integrity Tests", self._run_integrity_tests))

            if self.config.run_performance_tests:
                test_phases.append(("Performance Benchmarks", self._run_performance_tests))

            if self.config.run_load_tests:
                test_phases.append(("Load Tests", self._run_load_tests))

            if self.config.run_disaster_tests:
                test_phases.append(("Disaster Recovery Tests", self._run_disaster_tests))

            # Execute test phases
            for phase_name, phase_func in test_phases:
                logger.info(f"\n{'='*20} {phase_name} {'='*20}")

                try:
                    phase_start = time.time()
                    await phase_func()
                    phase_duration = time.time() - phase_start
                    logger.info(f"{phase_name} completed in {phase_duration:.1f} seconds")

                except Exception as e:
                    logger.error(f"{phase_name} failed: {str(e)}")
                    if not self.config.continue_on_failure:
                        raise
                    self.result.overall_success = False

            # Analyze results and generate recommendations
            self._analyze_results()
            self._generate_recommendations()

            # Generate comprehensive report
            if self.config.generate_reports:
                await self._generate_comprehensive_report()

        except Exception as e:
            logger.error(f"Test suite execution failed: {str(e)}")
            self.result.overall_success = False
            raise

        finally:
            self.result.end_time = datetime.utcnow()
            self.result.duration_seconds = (self.result.end_time - self.result.start_time).total_seconds()

        logger.info("="*60)
        logger.info("SYSTEM INTEGRATION TESTING COMPLETED")
        logger.info(f"Overall Success: {'PASS' if self.result.overall_success else 'FAIL'}")
        logger.info(f"Total Duration: {self.result.duration_seconds:.1f} seconds")
        logger.info("="*60)

        return self.result

    async def _run_end_to_end_tests(self):
        """Run end-to-end integration tests"""
        logger.info("Running end-to-end integration tests...")

        suite = EndToEndTestSuite()
        report = await suite.run_end_to_end_tests()

        self.result.end_to_end_result = report
        self.result.total_tests_run += report["test_summary"]["total_operations"]
        self.result.total_tests_passed += report["performance_analysis"]["success_rate"]

        if not report["overall_success"]:
            self.result.total_tests_failed += 1
            self.result.overall_success = False

        # Extract performance metrics
        self.result.avg_response_time = report["performance_analysis"]["avg_response_time"]

        # Identify issues
        for bottleneck in report["performance_analysis"]["bottlenecks"]:
            self.result.performance_issues.append(f"E2E: {bottleneck}")

        logger.info(f"End-to-end tests: {report['performance_analysis']['success_rate']:.1f}% success rate")

    async def _run_api_tests(self):
        """Run comprehensive API tests"""
        logger.info("Running comprehensive API tests...")

        suite = ComprehensiveAPITestSuite()
        report = await suite.run_all_tests()

        self.result.api_test_result = report
        total_endpoints = report["test_summary"]["total_endpoints"]
        successful_endpoints = report["test_summary"]["successful"]

        self.result.total_tests_run += total_endpoints
        self.result.total_tests_passed += successful_endpoints
        self.result.total_tests_failed += (total_endpoints - successful_endpoints)

        # Update peak throughput
        self.result.peak_throughput = max(self.result.peak_throughput, report["performance_metrics"]["max_response_time"])

        # Identify issues
        if report["test_summary"]["success_rate"] < 95:
            self.result.reliability_issues.append(f"API success rate low: {report['test_summary']['success_rate']:.1f}%")

        for test in report["failed_tests"]:
            self.result.reliability_issues.append(f"API Failure: {test['category']}.{test['endpoint']} - {test['error']}")

        logger.info(f"API tests: {successful_endpoints}/{total_endpoints} endpoints passed")

    async def _run_integrity_tests(self):
        """Run data integrity validation tests"""
        logger.info("Running data integrity validation...")

        async with DataFlowIntegrityValidator() as validator:
            report = await validator.run_comprehensive_integrity_validation()

        self.result.integrity_test_result = report
        summary = report["validation_summary"]

        # Count violations as failed tests
        total_violations = summary["total_violations"]
        critical_violations = summary["critical_violations"]

        self.result.total_tests_run += len(report["stage_results"])
        self.result.total_tests_passed += (len(report["stage_results"]) - len([r for r in report["stage_results"].values() if not r["passed"]]))

        # Identify critical issues
        if critical_violations > 0:
            self.result.critical_issues.append(f"Data integrity: {critical_violations} critical violations")
            self.result.overall_success = False

        for violation in report["critical_violations"]:
            self.result.security_issues.append(f"Integrity Violation: {violation['stage']} - {violation['description']}")

        logger.info(f"Integrity tests: {summary['total_violations']} violations detected")

    async def _run_performance_tests(self):
        """Run performance benchmark tests"""
        logger.info("Running performance benchmarks...")

        suite = PerformanceBenchmarkSuite()
        report = await suite.run_comprehensive_benchmark_suite()

        self.result.performance_test_result = report
        metadata = report["report_metadata"]

        self.result.total_tests_run += metadata["total_benchmarks"]
        self.result.total_tests_passed += metadata["passed_benchmarks"]
        self.result.total_tests_failed += metadata["failed_benchmarks"]

        # Update performance metrics
        self.result.avg_response_time = max(self.result.avg_response_time, report["performance_summary"]["avg_response_time"])
        self.result.peak_throughput = max(self.result.peak_throughput, report["performance_summary"]["peak_throughput"])

        # Update system resource metrics
        resources = report["system_resources"]
        self.result.system_resources_peak["cpu"] = max(self.result.system_resources_peak.get("cpu", 0), resources["max_cpu_usage"])
        self.result.system_resources_peak["memory"] = max(self.result.system_resources_peak.get("memory", 0), resources["max_memory_usage"])

        # Identify performance issues
        if metadata["pass_rate"] < 90:
            self.result.performance_issues.append(f"Performance benchmarks: {metadata['pass_rate']:.1f}% pass rate")

        for rec in report["recommendations"]:
            if "performance" in rec.lower():
                self.result.performance_issues.append(f"Performance: {rec}")

        logger.info(f"Performance tests: {metadata['passed_benchmarks']}/{metadata['total_benchmarks']} benchmarks passed")

    async def _run_load_tests(self):
        """Run load testing"""
        logger.info("Running load tests...")

        framework = LoadTestingFramework()

        # Define quick load test configuration (shorter for CI/CD)
        from tests.load.load_testing_framework import LoadTestConfig
        quick_test_config = LoadTestConfig(
            name="quick_load_test",
            test_type=LoadTestType.SMOKE_TEST,
            duration_seconds=60,  # 1 minute
            concurrent_users=20,
            requests_per_second=50,
            target_endpoints=["/health", "/api/strategies/v2/"],
            failure_rate_threshold=0.02
        )

        result = await framework.run_load_test(quick_test_config)

        self.result.load_test_result = {
            "test_name": result.config_name,
            "completed": result.completed,
            "total_requests": result.total_requests,
            "successful_requests": result.successful_requests,
            "error_rate": result.error_rate,
            "avg_response_time": result.avg_response_time,
            "requests_per_second": result.requests_per_second
        }

        # Update metrics
        self.result.total_tests_run += 1
        if result.completed and result.error_rate < quick_test_config.failure_rate_threshold:
            self.result.total_tests_passed += 1
        else:
            self.result.total_tests_failed += 1
            self.result.overall_success = False

        # Update performance metrics
        self.result.avg_response_time = max(self.result.avg_response_time, result.avg_response_time)
        self.result.peak_throughput = max(self.result.peak_throughput, result.requests_per_second)

        # Identify issues
        if result.error_rate > quick_test_config.failure_rate_threshold:
            self.result.reliability_issues.append(f"Load test error rate: {result.error_rate:.2%}")

        logger.info(f"Load tests: {result.successful_requests}/{result.total_requests} requests successful")

    async def _run_disaster_tests(self):
        """Run disaster recovery tests (only if explicitly enabled)"""
        logger.warning("Disaster recovery tests are disabled by default for safety")
        logger.info("Skipping disaster recovery tests - enable with --run-disaster-tests")
        return

    def _analyze_results(self):
        """Analyze all test results and identify issues"""
        logger.info("Analyzing test results...")

        # Aggregate issues from all test suites
        all_issues = []

        # End-to-end issues
        if self.result.end_to_end_result:
            for rec in self.result.end_to_end_result.get("recommendations", []):
                all_issues.append(("general", rec))

        # API test issues
        if self.result.api_test_result:
            for test in self.result.api_test_result.get("failed_tests", []):
                all_issues.append(("reliability", f"API: {test['category']}.{test['endpoint']}"))

        # Integrity issues
        if self.result.integrity_test_result:
            for violation in self.result.integrity_test_result.get("critical_violations", []):
                all_issues.append(("security", f"Integrity: {violation['description']}"))

        # Performance issues
        if self.result.performance_test_result:
            for rec in self.result.performance_test_result.get("recommendations", []):
                if "urgent" in rec.lower() or "critical" in rec.lower():
                    all_issues.append(("critical", f"Performance: {rec}"))
                else:
                    all_issues.append(("performance", f"Performance: {rec}"))

        # Load test issues
        if self.result.load_test_result and self.result.load_test_result["error_rate"] > 0.05:
            all_issues.append(("reliability", f"Load test high error rate: {self.result.load_test_result['error_rate']:.2%}"))

        # Categorize issues
        for issue_type, issue_desc in all_issues:
            if issue_type == "critical":
                if issue_desc not in self.result.critical_issues:
                    self.result.critical_issues.append(issue_desc)
            elif issue_type == "security":
                if issue_desc not in self.result.security_issues:
                    self.result.security_issues.append(issue_desc)
            elif issue_type == "performance":
                if issue_desc not in self.result.performance_issues:
                    self.result.performance_issues.append(issue_desc)
            elif issue_type == "reliability":
                if issue_desc not in self.result.reliability_issues:
                    self.result.reliability_issues.append(issue_desc)

    def _generate_recommendations(self):
        """Generate recommendations based on test results"""
        logger.info("Generating recommendations...")

        recommendations = []

        # Critical issues recommendations
        if self.result.critical_issues:
            recommendations.append(f"URGENT: Address {len(self.result.critical_issues)} critical issues immediately")

        # Performance recommendations
        if self.result.performance_issues:
            recommendations.append(f"Performance optimization needed - {len(self.result.performance_issues)} performance issues identified")

        # Reliability recommendations
        if self.result.reliability_issues:
            recommendations.append(f"Improve system reliability - {len(self.result.reliability_issues)} reliability issues found")

        # Security recommendations
        if self.result.security_issues:
            recommendations.append(f"Security review required - {len(self.result.security_issues)} security concerns identified")

        # Resource usage recommendations
        if self.result.system_resources_peak.get("cpu", 0) > 80:
            recommendations.append("Consider CPU optimization or scaling - peak CPU usage exceeded 80%")

        if self.result.system_resources_peak.get("memory", 0) > 1000:  # > 1GB
            recommendations.append("Monitor memory usage - peak memory usage was high")

        # Success rate recommendations
        if self.result.total_tests_run > 0:
            success_rate = (self.result.total_tests_passed / self.result.total_tests_run) * 100
            if success_rate < 95:
                recommendations.append(f"Overall test success rate ({success_rate:.1f}%) below target - address failing tests")
            elif success_rate >= 99:
                recommendations.append("Excellent system health - all tests passing")
            else:
                recommendations.append("Good system health with minor improvements possible")

        if not recommendations:
            recommendations.append("All systems performing within acceptable parameters")

        self.result.recommendations = recommendations

    async def _generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        logger.info("Generating comprehensive test report...")

        report = {
            "test_execution": {
                "start_time": self.result.start_time.isoformat(),
                "end_time": self.result.end_time.isoformat(),
                "duration_seconds": self.result.duration_seconds,
                "environment": self.config.environment,
                "overall_success": self.result.overall_success
            },
            "test_summary": {
                "total_tests_run": self.result.total_tests_run,
                "total_tests_passed": self.result.total_tests_passed,
                "total_tests_failed": self.result.total_tests_failed,
                "success_rate": (self.result.total_tests_passed / self.result.total_tests_run * 100) if self.result.total_tests_run > 0 else 0
            },
            "performance_metrics": {
                "avg_response_time": self.result.avg_response_time,
                "peak_throughput": self.result.peak_throughput,
                "system_resources_peak": self.result.system_resources_peak
            },
            "test_suite_results": {
                "end_to_end": self.result.end_to_end_result,
                "api_tests": self.result.api_test_result,
                "integrity_tests": self.result.integrity_test_result,
                "performance_tests": self.result.performance_test_result,
                "load_tests": self.result.load_test_result,
                "disaster_tests": self.result.disaster_test_result
            },
            "issues_summary": {
                "critical_issues": self.result.critical_issues,
                "performance_issues": self.result.performance_issues,
                "security_issues": self.result.security_issues,
                "reliability_issues": self.result.reliability_issues
            },
            "recommendations": self.result.recommendations
        }

        # Save comprehensive report
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        report_path = f"test_reports/comprehensive_integration_report_{timestamp}.json"

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Comprehensive test report saved to: {report_path}")

        # Generate human-readable summary
        summary_path = f"test_reports/integration_test_summary_{timestamp}.md"
        await self._generate_markdown_summary(report, summary_path)

        return report_path

    async def _generate_markdown_summary(self, report: Dict, summary_path: str):
        """Generate human-readable markdown summary"""
        summary_content = f"""# System Integration Test Summary

**Generated:** {report['test_execution']['start_time'][:19]}
**Duration:** {report['test_execution']['duration_seconds']:.1f} seconds
**Environment:** {report['test_execution']['environment']}
**Overall Status:** {'✅ PASS' if report['test_execution']['overall_success'] else '❌ FAIL'}

## Test Summary

| Metric | Value |
|--------|-------|
| Total Tests | {report['test_summary']['total_tests_run']} |
| Passed | {report['test_summary']['total_tests_passed']} |
| Failed | {report['test_summary']['total_tests_failed']} |
| Success Rate | {report['test_summary']['success_rate']:.1f}% |

## Performance Metrics

- **Average Response Time:** {report['performance_metrics']['avg_response_time']:.3f}s
- **Peak Throughput:** {report['performance_metrics']['peak_throughput']:.1f} RPS
- **Peak CPU Usage:** {report['performance_metrics']['system_resources_peak'].get('cpu', 0):.1f}%
- **Peak Memory Usage:** {report['performance_metrics']['system_resources_peak'].get('memory', 0):.1f}MB

## Test Suite Results

### End-to-End Tests
{'✅ Passed' if report['test_suite_results'].get('end_to_end', {}).get('overall_success', False) else '❌ Failed'}

### API Tests
**Endpoints:** {report['test_suite_results'].get('api_tests', {}).get('test_summary', {}).get('total_endpoints', 0)}
**Success Rate:** {report['test_suite_results'].get('api_tests', {}).get('test_summary', {}).get('success_rate', 0):.1f}%

### Data Integrity Tests
**Violations:** {report['test_suite_results'].get('integrity_tests', {}).get('validation_summary', {}).get('total_violations', 0)}
**Critical Violations:** {report['test_suite_results'].get('integrity_tests', {}).get('validation_summary', {}).get('critical_violations', 0)}

### Performance Benchmarks
**Benchmarks:** {report['test_suite_results'].get('performance_tests', {}).get('report_metadata', {}).get('total_benchmarks', 0)}
**Pass Rate:** {report['test_suite_results'].get('performance_tests', {}).get('report_metadata', {}).get('pass_rate', 0):.1f}%

### Load Tests
**Requests:** {report['test_suite_results'].get('load_tests', {}).get('total_requests', 0)}
**Success Rate:** {(1 - report['test_suite_results'].get('load_tests', {}).get('error_rate', 0)) * 100:.1f}%

## Issues Identified

### Critical Issues ({len(report['issues_summary']['critical_issues'])})
{chr(10).join(f"- {issue}" for issue in report['issues_summary']['critical_issues']) if report['issues_summary']['critical_issues'] else "None ✓"}

### Performance Issues ({len(report['issues_summary']['performance_issues'])})
{chr(10).join(f"- {issue}" for issue in report['issues_summary']['performance_issues']) if report['issues_summary']['performance_issues'] else "None ✓"}

### Security Issues ({len(report['issues_summary']['security_issues'])})
{chr(10).join(f"- {issue}" for issue in report['issues_summary']['security_issues']) if report['issues_summary']['security_issues'] else "None ✓"}

### Reliability Issues ({len(report['issues_summary']['reliability_issues'])})
{chr(10).join(f"- {issue}" for issue in report['issues_summary']['reliability_issues']) if report['issues_summary']['reliability_issues'] else "None ✓"}

## Recommendations

{chr(10).join(f"- {rec}" for rec in report['recommendations'])}

---

*Report generated by CBSC System Integration Test Runner*
"""

        with open(summary_path, "w") as f:
            f.write(summary_content)

        logger.info(f"Test summary saved to: {summary_path}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="CBSC System Integration Test Runner")
    parser.add_argument("--skip-e2e", action="store_true", help="Skip end-to-end tests")
    parser.add_argument("--skip-api", action="store_true", help="Skip API tests")
    parser.add_argument("--skip-integrity", action="store_true", help="Skip data integrity tests")
    parser.add_argument("--skip-performance", action="store_true", help="Skip performance tests")
    parser.add_argument("--skip-load", action="store_true", help="Skip load tests")
    parser.add_argument("--run-disaster-tests", action="store_true", help="Run disaster recovery tests")
    parser.add_argument("--skip-slow", action="store_true", help="Skip slow tests")
    parser.add_argument("--timeout", type=int, default=60, help="Test timeout in minutes")
    parser.add_argument("--environment", default="test", help="Test environment")
    parser.add_argument("--base-url", default="http://localhost:3003", help="Base URL for tests")

    args = parser.parse_args()

    # Create configuration
    config = TestSuiteConfig(
        run_end_to_end=not args.skip_e2e,
        run_api_tests=not args.skip_api,
        run_integrity_tests=not args.skip_integrity,
        run_performance_tests=not args.skip_performance,
        run_load_tests=not args.skip_load,
        run_disaster_tests=args.run_disaster_tests,
        test_timeout_minutes=args.timeout,
        environment=args.environment,
        base_url=args.base_url,
        skip_slow_tests=args.skip_slow
    )

    # Run tests
    runner = SystemIntegrationTestRunner(config)
    result = await runner.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if result.overall_success else 1)


if __name__ == "__main__":
    asyncio.run(main())
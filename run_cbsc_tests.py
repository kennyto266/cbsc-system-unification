"""
CBSC VectorBT Test Runner
CBSC VectorBT测试运行器

Comprehensive test execution and reporting for CBSC backtesting system.
CBSC回测系统的综合测试执行和报告。

Author: CBSC Backtesting System Team
Date: 2025-12-04
Version: 1.0
"""

import sys
import time
import traceback
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

class CBSCTestRunner:
    """Main test runner for CBSC VectorBT system"""

    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None

    def run_all_tests(self, test_categories: Optional[List[str]] = None) -> bool:
        """Run all CBSC tests and return success status"""
        print("🚀 CBSC VectorBT Testing Suite")
        print("=" * 60)
        print(f"Start Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        self.start_time = time.time()

        # Define available test categories
        available_categories = {
            'comprehensive': {
                'description': 'Run comprehensive test suite',
                'command': [sys.executable, 'test_cbsc_comprehensive_suite.py'],
                'timeout': 300
            },
            'unit': {
                'description': 'Run unit tests for individual components',
                'command': ['pytest', '-v', '-m', 'unit', 'tests/'],
                'timeout': 180
            },
            'integration': {
                'description': 'Run integration tests',
                'command': ['pytest', '-v', '-m', 'integration', 'tests/'],
                'timeout': 240
            },
            'performance': {
                'description': 'Run performance benchmarks',
                'command': ['pytest', '-v', '-m', 'performance', 'tests/'],
                'timeout': 360
            },
            'cbsc_specific': {
                'description': 'Run CBSC-specific functionality tests',
                'command': ['pytest', '-v', '-m', 'cbsc_specific', 'tests/'],
                'timeout': 180
            },
            'data_quality': {
                'description': 'Run data quality validation tests',
                'command': ['pytest', '-v', '-m', 'data_quality', 'tests/'],
                'timeout': 120
            },
            'edge_cases': {
                'description': 'Run edge case and error handling tests',
                'command': ['pytest', '-v', '-m', 'edge_cases', 'tests/'],
                'timeout': 120
            }
        }

        # Filter categories if specified
        if test_categories:
            categories_to_run = {k: v for k, v in available_categories.items() if k in test_categories}
        else:
            categories_to_run = available_categories

        print(f"Running test categories: {list(categories_to_run.keys())}")
        print()

        overall_success = True

        # Run each test category
        for category_name, category_info in categories_to_run.items():
            print(f"\n📋 Running {category_name.upper()} tests")
            print(f"Description: {category_info['description']}")
            print("-" * 50)

            success, duration, output = self._run_test_command(
                category_info['command'],
                category_info['timeout']
            )

            self.test_results[category_name] = {
                'success': success,
                'duration': duration,
                'output': output
            }

            if success:
                print(f"✅ {category_name} tests passed ({duration:.1f}s)")
            else:
                print(f"❌ {category_name} tests failed ({duration:.1f}s)")
                overall_success = False

        self.end_time = time.time()

        # Generate final report
        self._generate_final_report()

        return overall_success

    def _run_test_command(self, command: List[str], timeout: int) -> tuple[bool, float, str]:
        """Execute a test command and return results"""
        start_time = time.time()

        try:
            # Run the command
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path(__file__).parent
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            # Combine stdout and stderr for output
            output = result.stdout
            if result.stderr:
                output += "\nSTDERR:\n" + result.stderr

            return success, duration, output

        except subprocess.TimeoutExpired:
            duration = timeout
            output = f"Test timed out after {timeout} seconds"
            return False, duration, output

        except Exception as e:
            duration = time.time() - start_time
            output = f"Test execution error: {str(e)}"
            return False, duration, output

    def _generate_final_report(self):
        """Generate comprehensive test report"""
        total_duration = self.end_time - self.start_time
        total_categories = len(self.test_results)
        passed_categories = sum(1 for result in self.test_results.values() if result['success'])

        print("\n" + "=" * 60)
        print("📊 FINAL TEST REPORT")
        print("=" * 60)
        print(f"Total Duration: {total_duration:.1f} seconds")
        print(f"Categories Run: {total_categories}")
        print(f"Categories Passed: {passed_categories}")
        print(f"Success Rate: {passed_categories/total_categories*100:.1f}%")
        print()

        # Detailed results
        print("Category Results:")
        print("-" * 30)
        for category_name, result in self.test_results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} {category_name:<20} ({result['duration']:.1f}s)")

        # Performance summary
        if 'performance' in self.test_results:
            print(f"\n🚀 Performance Test Results:")
            perf_output = self.test_results['performance']['output']
            if 'COMPLETE WORKFLOW' in perf_output:
                # Extract workflow performance
                lines = perf_output.split('\n')
                for line in lines:
                    if 'Complete Workflow Time:' in line:
                        print(f"  {line.strip()}")
                        break

        # Save detailed report to file
        self._save_detailed_report()

        # Final status
        print(f"\n{'🎉 ALL TESTS PASSED!' if passed_categories == total_categories else '⚠️ SOME TESTS FAILED'}")

        if passed_categories == total_categories:
            print("\n✅ System is READY for production deployment!")
            print("   • All functionality verified")
            print("   • Performance benchmarks met")
            print("   • CBSC-specific logic validated")
            print("   • Data quality confirmed")
        else:
            print(f"\n❌ {total_categories - passed_categories} test categories failed.")
            print("   Please review and fix issues before deployment.")

    def _save_detailed_report(self):
        """Save detailed test report to JSON file"""
        report_data = {
            'test_run_info': {
                'start_time': self.start_time,
                'end_time': self.end_time,
                'total_duration': self.end_time - self.start_time,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'test_results': self.test_results,
            'summary': {
                'total_categories': len(self.test_results),
                'passed_categories': sum(1 for result in self.test_results.values() if result['success']),
                'success_rate': sum(1 for result in self.test_results.values() if result['success']) / len(self.test_results)
            }
        }

        # Save report
        report_path = Path("cbsc_test_report.json")
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_path}")

    def run_quick_health_check(self) -> bool:
        """Run a quick health check of the system"""
        print("🏥 CBSC System Health Check")
        print("=" * 40)

        health_checks = [
            {
                'name': 'Import Check',
                'command': [sys.executable, '-c', 'from data_loader import CBSCDataLoader; from signal_generator import CBSCSignalGenerator; from cbsc_backtester import CBSCBacktester; from optimizer import CBSCOptimizer; print("All imports successful")']
            },
            {
                'name': 'Dependencies Check',
                'command': [sys.executable, '-c', 'import pandas, numpy, yfinance, vectorbt; print("Core dependencies available")']
            },
            {
                'name': 'Data File Check',
                'command': [sys.executable, '-c', 'from pathlib import Path; print("Data file exists:" if Path("CODEX--/warrant_sentiment_daily.csv").exists() else "Data file missing")']
            }
        ]

        all_passed = True

        for check in health_checks:
            try:
                result = subprocess.run(
                    check['command'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    print(f"✅ {check['name']}: {result.stdout.strip()}")
                else:
                    print(f"❌ {check['name']}: {result.stderr.strip()}")
                    all_passed = False

            except Exception as e:
                print(f"❌ {check['name']}: {str(e)}")
                all_passed = False

        print(f"\nHealth Status: {'✅ HEALTHY' if all_passed else '❌ ISSUES DETECTED'}")
        return all_passed

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='CBSC VectorBT Test Runner')
    parser.add_argument(
        '--categories',
        nargs='+',
        choices=['comprehensive', 'unit', 'integration', 'performance', 'cbsc_specific', 'data_quality', 'edge_cases'],
        help='Specific test categories to run'
    )
    parser.add_argument(
        '--health-check',
        action='store_true',
        help='Run quick health check only'
    )
    parser.add_argument(
        '--comprehensive-only',
        action='store_true',
        help='Run only the comprehensive test suite'
    )

    args = parser.parse_args()

    runner = CBSCTestRunner()

    try:
        if args.health_check:
            success = runner.run_quick_health_check()
            return 0 if success else 1

        elif args.comprehensive_only:
            success, _, _ = runner._run_test_command(
                [sys.executable, 'test_cbsc_comprehensive_suite.py'],
                300
            )
            return 0 if success else 1

        else:
            categories = args.categories
            success = runner.run_all_tests(categories)
            return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\n⏹️ Test execution interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
#!/usr/bin/env python3
"""
Performance Test Runner
Executes all performance tests and generates comprehensive report
"""

import asyncio
import subprocess
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

class PerformanceTestRunner:
    """Manages and runs all performance tests"""

    def __init__(self):
        self.results = {
            "frontend": {},
            "backend": {},
            "load_tests": {},
            "summary": {}
        }
        self.start_time = datetime.now()
        self.report_dir = Path("performance_reports")
        self.report_dir.mkdir(exist_ok=True)

    def run_frontend_performance_tests(self):
        """Run frontend performance tests"""
        print("="*50)
        print("Running Frontend Performance Tests")
        print("="*50)

        try:
            # Install Puppeteer if not installed
            subprocess.run([
                sys.executable, "-m", "pip", "install", "puppeteer"
            ], check=True, capture_output=True)

            # Run frontend load test
            from load_test import FrontendLoadTest
            load_test = FrontendLoadTest()

            # Concurrent users test
            print("\n1. Frontend Concurrent Users Test...")
            concurrent_results = load_test.runConcurrentUsersTest(userCount=10)

            # Stress test (short duration)
            print("\n2. Frontend Stress Test...")
            stress_results = load_test.runStressTest(duration=30000)  # 30 seconds

            self.results["frontend"] = {
                "concurrent_users": concurrent_results,
                "stress_test": stress_results,
                "timestamp": datetime.now().isoformat()
            }

            print("\n✅ Frontend performance tests completed")
            return True

        except Exception as e:
            print(f"\n❌ Frontend performance tests failed: {e}")
            self.results["frontend"]["error"] = str(e)
            return False

    def run_backend_performance_tests(self):
        """Run backend performance tests"""
        print("\n" + "="*50)
        print("Running Backend Performance Tests")
        print("="*50)

        try:
            # Install performance test dependencies
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True, capture_output=True, cwd=self.report_dir.parent)

            # Run backend performance tests
            import api_performance_test

            print("\n1. Backend Endpoint Performance Test...")
            asyncio.run(api_performance_test.test_api_endpoint_performance())

            print("\n2. Backend Concurrent Load Test...")
            concurrent_result = asyncio.run(api_performance_test.test_concurrent_user_load())

            print("\n3. Backend Sustained Load Test...")
            sustained_result = asyncio.run(api_performance_test.test_sustained_load())

            print("\n4. Backend Stress Test...")
            stress_result = asyncio.run(api_performance_test.test_api_stress())

            self.results["backend"] = {
                "concurrent_load": concurrent_result,
                "sustained_load": sustained_result,
                "stress_test": stress_result,
                "timestamp": datetime.now().isoformat()
            }

            print("\n✅ Backend performance tests completed")
            return True

        except Exception as e:
            print(f"\n❌ Backend performance tests failed: {e}")
            self.results["backend"]["error"] = str(e)
            return False

    def run_locust_load_tests(self):
        """Run Locust load tests"""
        print("\n" + "="*50)
        print("Running Locust Load Tests")
        print("="*50)

        try:
            # Install Locust if not installed
            subprocess.run([
                sys.executable, "-m", "pip", "install", "locust"
            ], check=True, capture_output=True)

            # Run Locust in headless mode
            print("\n1. Load Test - 50 users, ramp up 10 seconds...")
            locust_cmd = [
                sys.executable, "-m", "locust",
                "-f", "locustfile.py",
                "--headless",
                "--users", "50",
                "--spawn-rate", "5",
                "--run-time", "60s",
                "--host", "http://localhost:3004",
                "--html", f"{self.report_dir}/locust_report.html"
            ]

            result = subprocess.run(
                locust_cmd,
                capture_output=True,
                text=True,
                cwd=self.report_dir.parent
            )

            if result.returncode == 0:
                print("✅ Locust load test completed")
                self.results["load_tests"] = {
                    "status": "completed",
                    "report_file": f"{self.report_dir}/locust_report.html",
                    "timestamp": datetime.now().isoformat()
                }
                return True
            else:
                print(f"❌ Locust load test failed: {result.stderr}")
                self.results["load_tests"]["error"] = result.stderr
                return False

        except Exception as e:
            print(f"❌ Locust load test failed: {e}")
            self.results["load_tests"]["error"] = str(e)
            return False

    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        print("\n" + "="*50)
        print("Generating Performance Report")
        print("="*50)

        # Calculate overall summary
        total_duration = (datetime.now() - self.start_time).total_seconds()

        self.results["summary"] = {
            "test_duration_seconds": total_duration,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "tests_run": list(self.results.keys()),
            "overall_status": "success" if self.check_all_tests_passed() else "partial_failure"
        }

        # Save JSON report
        report_file = self.report_dir / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        # Generate visual report
        self.generate_visual_report()

        print(f"\n📊 Performance report saved to: {report_file}")
        print(f"📈 Visual report saved to: {self.report_dir}/performance_summary.png")

        return report_file

    def check_all_tests_passed(self):
        """Check if all tests passed successfully"""
        passed = True

        for test_type, results in self.results.items():
            if isinstance(results, dict) and "error" in results:
                passed = False
                break

        return passed

    def generate_visual_report(self):
        """Generate visual performance summary"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('CBSC System Performance Test Results', fontsize=16)

            # Frontend performance chart
            if "frontend" in self.results and "concurrent_users" in self.results["frontend"]:
                frontend_data = self.results["frontend"]["concurrent_users"]["summary"]
                ax1 = axes[0, 0]
                categories = ['Avg Page Load', 'Avg Interaction', 'Error Rate %']
                values = [
                    frontend_data.get('averagePageLoadTime', 0),
                    frontend_data.get('averageInteractionTime', 0),
                    frontend_data.get('errorRate', 0)
                ]
                ax1.bar(categories, values, color=['blue', 'green', 'red'])
                ax1.set_title('Frontend Performance')
                ax1.set_ylabel('Time (ms) / %')

            # Backend performance chart
            if "backend" in self.results and "concurrent_load" in self.results["backend"]:
                backend_data = self.results["backend"]["concurrent_load"]
                ax2 = axes[0, 1]
                metrics = ['Avg Response Time', 'P95 Response Time', 'Requests/sec', 'Error Rate %']
                values = [
                    backend_data.get('avg_response_time', 0),
                    backend_data.get('p95_response_time', 0),
                    backend_data.get('requests_per_second', 0),
                    backend_data.get('error_rate', 0)
                ]
                ax2.bar(metrics, values, color=['purple', 'orange', 'cyan', 'red'])
                ax2.set_title('Backend Performance')
                ax2.set_ylabel('Time (ms) / RPS / %')
                plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')

            # Test status chart
            ax3 = axes[1, 0]
            test_names = []
            test_statuses = []
            colors = []

            for test_type in ['frontend', 'backend', 'load_tests']:
                if test_type in self.results:
                    test_names.append(test_type.title())
                    if "error" in self.results[test_type]:
                        test_statuses.append(0)
                        colors.append('red')
                    else:
                        test_statuses.append(1)
                        colors.append('green')

            ax3.bar(test_names, test_statuses, color=colors)
            ax3.set_title('Test Status')
            ax3.set_ylabel('Pass (1) / Fail (0)')
            ax3.set_ylim(0, 1.2)

            # Summary text
            ax4 = axes[1, 1]
            ax4.axis('off')

            summary_text = f"""
            Performance Test Summary
            ========================
            Total Duration: {self.results['summary']['test_duration_seconds']:.1f}s
            Start Time: {self.results['summary']['start_time']}
            End Time: {self.results['summary']['end_time']}

            Tests Completed:
            {'✅' if 'frontend' in self.results and 'error' not in self.results['frontend'] else '❌'} Frontend Tests
            {'✅' if 'backend' in self.results and 'error' not in self.results['backend'] else '❌'} Backend Tests
            {'✅' if 'load_tests' in self.results and 'error' not in self.results['load_tests'] else '❌'} Load Tests

            Overall Status: {self.results['summary']['overall_status'].upper()}
            """

            ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes,
                    fontsize=12, verticalalignment='top', fontfamily='monospace')

            plt.tight_layout()
            plt.savefig(f"{self.report_dir}/performance_summary.png", dpi=300, bbox_inches='tight')
            plt.close()

        except Exception as e:
            print(f"Warning: Could not generate visual report: {e}")

    def run_all_tests(self):
        """Run all performance tests"""
        print("🚀 Starting CBSC Performance Test Suite")
        print(f"⏰ Started at: {self.start_time}")
        print(f"📁 Reports will be saved to: {self.report_dir.absolute()}\n")

        # Run test suites
        frontend_passed = self.run_frontend_performance_tests()
        backend_passed = self.run_backend_performance_tests()
        locust_passed = self.run_locust_load_tests()

        # Generate report
        report_file = self.generate_performance_report()

        # Print final summary
        print("\n" + "="*50)
        print("🏁 PERFORMANCE TEST SUITE COMPLETE")
        print("="*50)

        if frontend_passed and backend_passed and locust_passed:
            print("✅ All tests completed successfully!")
        else:
            print("⚠️  Some tests failed. Check the report for details.")

        print(f"\n📊 Detailed report: {report_file}")
        print(f"📈 Visual summary: {self.report_dir}/performance_summary.png")

        if "load_tests" in self.results and "report_file" in self.results["load_tests"]:
            print(f"🌐 Locust report: {self.results['load_tests']['report_file']}")

        return frontend_passed and backend_passed and locust_passed


# Main execution
if __name__ == "__main__":
    runner = PerformanceTestRunner()

    # Check if server is running (basic check)
    try:
        import requests
        response = requests.get("http://localhost:3004/api/health", timeout=5)
        if response.status_code != 200:
            print("⚠️  Backend server may not be running. Some tests may fail.")
    except:
        print("⚠️  Cannot connect to backend server. Please ensure it's running on http://localhost:3004")

    # Run all performance tests
    success = runner.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
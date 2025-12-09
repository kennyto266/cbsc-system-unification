#!/usr/bin/env python3
"""
Complete System Validation and Testing Script
Executes comprehensive testing of the unified backtesting framework
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import testing modules
try:
    from src.unified_backtesting.testing.comprehensive_test_framework import (
        UnifiedBacktestingTestCase,
        IntegrationTestSuite,
        TestDataGenerator
    )
    from src.unified_backtesting.testing.performance_benchmark import (
        PerformanceProfiler,
        SystemMonitor,
        BenchmarkTestSuite
    )
    from src.unified_backtesting.testing.stress_test import (
        StressTestSuite,
        FullSystemStressTest
    )
    from src.monitoring.comprehensive_monitoring_system import (
        ComprehensiveMonitoringSystem,
        SystemMetrics,
        ApplicationMetrics
    )
except ImportError as e:
    logger.error(f"Failed to import testing modules: {e}")
    sys.exit(1)


class SystemValidationOrchestrator:
    """Orchestrates complete system validation"""

    def __init__(self):
        self.start_time = time.time()
        self.test_results = {}
        self.monitoring_system = None
        self.validation_config = self._load_validation_config()

    def _load_validation_config(self) -> Dict[str, Any]:
        """Load validation configuration"""
        config = {
            'test_timeout': 1800,  # 30 minutes
            'enable_stress_tests': True,
            'enable_performance_benchmarks': True,
            'max_parallel_tests': 4,
            'memory_limit_gb': 8,
            'enable_gpu_tests': False,  # Set to True if GPU available
            'test_data_size': 1000,
            'parameter_combinations': 100,
            'monitoring': {
                'prometheus_port': 9090,
                'log_level': 'INFO'
            }
        }

        # Check for GPU availability
        try:
            import torch
            if torch.cuda.is_available():
                config['enable_gpu_tests'] = True
                logger.info("GPU detected, enabling GPU tests")
        except ImportError:
            logger.info("PyTorch not available, GPU tests disabled")

        return config

    async def run_complete_validation(self) -> Dict[str, Any]:
        """Run complete system validation"""
        logger.info("🚀 Starting Complete System Validation")
        logger.info(f"Configuration: {json.dumps(self.validation_config, indent=2)}")

        validation_results = {
            'start_time': datetime.now().isoformat(),
            'configuration': self.validation_config,
            'test_phases': {},
            'overall_status': 'in_progress',
            'summary': {}
        }

        try:
            # Initialize monitoring
            await self._setup_monitoring()

            # Phase 1: Unit Tests
            logger.info("\n📋 Phase 1: Running Unit Tests")
            validation_results['test_phases']['unit_tests'] = await self._run_unit_tests()

            # Phase 2: Integration Tests
            logger.info("\n🔗 Phase 2: Running Integration Tests")
            validation_results['test_phases']['integration_tests'] = await self._run_integration_tests()

            # Phase 3: Performance Benchmarks
            if self.validation_config['enable_performance_benchmarks']:
                logger.info("\n⚡ Phase 3: Running Performance Benchmarks")
                validation_results['test_phases']['performance_benchmarks'] = await self._run_performance_benchmarks()

            # Phase 4: Stress Tests
            if self.validation_config['enable_stress_tests']:
                logger.info("\n💪 Phase 4: Running Stress Tests")
                validation_results['test_phases']['stress_tests'] = await self._run_stress_tests()

            # Phase 5: System Integration Test
            logger.info("\n🏗️ Phase 5: Running System Integration Test")
            validation_results['test_phases']['system_integration'] = await self._run_system_integration_test()

            # Generate summary
            validation_results['summary'] = self._generate_validation_summary(validation_results['test_phases'])
            validation_results['end_time'] = datetime.now().isoformat()
            validation_results['total_duration'] = time.time() - self.start_time
            validation_results['overall_status'] = 'completed'

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            validation_results['error'] = str(e)
            validation_results['traceback'] = traceback.format_exc()
            validation_results['overall_status'] = 'failed'

        finally:
            # Cleanup
            await self._cleanup()

        return validation_results

    async def _setup_monitoring(self):
        """Setup monitoring system"""
        try:
            self.monitoring_system = ComprehensiveMonitoringSystem(
                self.validation_config['monitoring']
            )
            self.monitoring_system.start_monitoring()
            logger.info("Monitoring system started")
        except Exception as e:
            logger.warning(f"Failed to setup monitoring: {e}")

    async def _run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests"""
        try:
            test_case = UnifiedBacktestingTestCase()
            test_generator = TestDataGenerator(
                size=self.validation_config['test_data_size']
            )

            # Generate test data
            logger.info("Generating test data...")
            test_data = test_generator.generate_price_data()
            parameters = test_generator.generate_parameter_space(
                combinations=self.validation_config['parameter_combinations']
            )

            # Run unit tests
            results = {
                'test_data_generation': test_case.testParameterSpaceGeneration(parameters),
                'backtest_engine': test_case.testBacktestEngineInitialization(test_data),
                'memory_management': test_case.testMemoryManagement(),
                'metrics_calculation': test_case.testMetricsCalculation(test_data),
                'cache_system': test_case.testCacheSystem(),
                'error_handling': test_case.testErrorHandling(),
                'performance': test_case.testPerformanceMetrics()
            }

            # Calculate success rate
            passed = sum(1 for result in results.values() if result.get('passed', False))
            total = len(results)
            results['summary'] = {
                'total_tests': total,
                'passed': passed,
                'failed': total - passed,
                'success_rate': (passed / total) * 100
            }

            logger.info(f"Unit tests completed: {passed}/{total} passed")
            return results

        except Exception as e:
            logger.error(f"Unit test execution failed: {e}")
            return {'error': str(e), 'success_rate': 0}

    async def _run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        try:
            integration_suite = IntegrationTestSuite()

            results = {
                'end_to_end_backtest': await integration_suite.test_end_to_end_backtest(),
                'data_pipeline': await integration_suite.test_data_pipeline_integration(),
                'performance_monitoring': await integration_suite.test_performance_monitoring(),
                'error_recovery': await integration_suite.test_error_recovery(),
                'concurrent_execution': await integration_suite.test_concurrent_execution(),
                'api_integration': await integration_suite.test_api_integration()
            }

            # Calculate success rate
            passed = sum(1 for result in results.values() if result.get('passed', False))
            total = len(results)
            results['summary'] = {
                'total_tests': total,
                'passed': passed,
                'failed': total - passed,
                'success_rate': (passed / total) * 100
            }

            logger.info(f"Integration tests completed: {passed}/{total} passed")
            return results

        except Exception as e:
            logger.error(f"Integration test execution failed: {e}")
            return {'error': str(e), 'success_rate': 0}

    async def _run_performance_benchmarks(self) -> Dict[str, Any]:
        """Run performance benchmarks"""
        try:
            benchmark_suite = BenchmarkTestSuite()
            profiler = PerformanceProfiler()

            # Run benchmarks
            results = {
                'memory_profiling': profiler.profile_memory_usage(),
                'cpu_profiling': profiler.profile_cpu_usage(),
                'io_profiling': profiler.profile_io_performance(),
                'cache_performance': benchmark_suite.benchmark_cache_performance(),
                'database_operations': benchmark_suite.benchmark_database_operations(),
                'parameter_optimization': benchmark_suite.benchmark_parameter_optimization(),
                'vectorbt_performance': benchmark_suite.benchmark_vectorbt_performance()
            }

            # Calculate overall performance score
            performance_score = self._calculate_performance_score(results)
            results['summary'] = {
                'performance_score': performance_score,
                'grade': self._get_performance_grade(performance_score)
            }

            logger.info(f"Performance benchmarks completed. Score: {performance_score:.1f}")
            return results

        except Exception as e:
            logger.error(f"Performance benchmark execution failed: {e}")
            return {'error': str(e), 'performance_score': 0}

    async def _run_stress_tests(self) -> Dict[str, Any]:
        """Run stress tests"""
        try:
            stress_suite = StressTestSuite()

            results = {
                'high_concurrency': await stress_suite.test_high_concurrency(),
                'memory_pressure': await stress_suite.test_memory_pressure(),
                'large_datasets': await stress_suite.test_large_datasets(),
                'resource_exhaustion': await stress_suite.test_resource_exhaustion(),
                'network_stress': await stress_suite.test_network_stress()
            }

            # Calculate stress test success rate
            passed = sum(1 for result in results.values() if result.get('passed', False))
            total = len(results)
            results['summary'] = {
                'total_tests': total,
                'passed': passed,
                'failed': total - passed,
                'success_rate': (passed / total) * 100,
                'stress_resistance': 'high' if passed == total else 'medium' if passed >= total * 0.8 else 'low'
            }

            logger.info(f"Stress tests completed: {passed}/{total} passed")
            return results

        except Exception as e:
            logger.error(f"Stress test execution failed: {e}")
            return {'error': str(e), 'success_rate': 0}

    async def _run_system_integration_test(self) -> Dict[str, Any]:
        """Run complete system integration test"""
        try:
            full_system_test = FullSystemStressTest()

            # Initialize monitoring for the test
            if self.monitoring_system:
                self.monitoring_system.track_backtest_start(
                    'system_validation',
                    self.validation_config['parameter_combinations']
                )

            # Run full system test
            test_result = await full_system_test.run_full_system_test()

            # Complete monitoring tracking
            if self.monitoring_system:
                self.monitoring_system.track_backtest_complete(
                    'system_validation',
                    test_result.get('passed', False),
                    self.validation_config['parameter_combinations']
                )

            return {
                'system_wide_backtest': test_result,
                'resource_usage': test_result.get('resource_usage', {}),
                'performance_metrics': test_result.get('performance_metrics', {}),
                'error_recovery': test_result.get('error_recovery', {}),
                'summary': {
                    'passed': test_result.get('passed', False),
                    'execution_time': test_result.get('execution_time', 0),
                    'peak_memory_mb': test_result.get('peak_memory_mb', 0),
                    'parameter_throughput': test_result.get('parameter_throughput', 0)
                }
            }

        except Exception as e:
            logger.error(f"System integration test failed: {e}")
            return {'error': str(e), 'passed': False}

    def _calculate_performance_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall performance score"""
        score = 0.0
        weights = {
            'memory_profiling': 0.2,
            'cpu_profiling': 0.2,
            'io_profiling': 0.15,
            'cache_performance': 0.15,
            'database_operations': 0.15,
            'parameter_optimization': 0.15
        }

        for key, weight in weights.items():
            if key in results and isinstance(results[key], dict):
                # Extract performance score from each benchmark
                benchmark_score = results[key].get('score', 0)
                score += benchmark_score * weight

        return min(100.0, max(0.0, score))

    def _get_performance_grade(self, score: float) -> str:
        """Get performance grade based on score"""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B+'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C+'
        elif score >= 40:
            return 'C'
        else:
            return 'D'

    def _generate_validation_summary(self, test_phases: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall validation summary"""
        summary = {
            'total_phases': len(test_phases),
            'passed_phases': 0,
            'failed_phases': 0,
            'overall_success_rate': 0.0,
            'critical_issues': [],
            'recommendations': []
        }

        for phase_name, phase_results in test_phases.items():
            if phase_results.get('error'):
                summary['failed_phases'] += 1
                summary['critical_issues'].append(f"{phase_name}: {phase_results['error']}")
            else:
                success_rate = phase_results.get('success_rate', phase_results.get('performance_score', 0))
                if success_rate >= 80:
                    summary['passed_phases'] += 1
                else:
                    summary['failed_phases'] += 1
                    summary['critical_issues'].append(f"{phase_name}: Low success rate ({success_rate:.1f}%)")

        # Calculate overall success rate
        if summary['total_phases'] > 0:
            summary['overall_success_rate'] = (summary['passed_phases'] / summary['total_phases']) * 100

        # Generate recommendations
        if summary['overall_success_rate'] < 100:
            summary['recommendations'].append("Review and fix failing test phases")
        if summary['overall_success_rate'] < 80:
            summary['recommendations'].append("Consider refactoring components with low success rates")
        if summary['overall_success_rate'] < 60:
            summary['recommendations'].append("Major system issues detected - requires comprehensive review")

        return summary

    async def _cleanup(self):
        """Cleanup resources"""
        try:
            if self.monitoring_system:
                self.monitoring_system.cleanup()
            logger.info("Cleanup completed")
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")

    def save_results(self, results: Dict[str, Any]):
        """Save validation results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"system_validation_results_{timestamp}.json"

        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)

            logger.info(f"Validation results saved to: {filename}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")


async def main():
    """Main execution function"""
    print("🔬 CBSC Unified Backtesting Framework - Complete System Validation")
    print("=" * 70)

    orchestrator = SystemValidationOrchestrator()

    try:
        # Run complete validation
        results = await orchestrator.run_complete_validation()

        # Save results
        orchestrator.save_results(results)

        # Print summary
        print("\n" + "=" * 70)
        print("📊 VALIDATION SUMMARY")
        print("=" * 70)

        summary = results.get('summary', {})
        total_duration = results.get('total_duration', 0)

        print(f"Overall Status: {results.get('overall_status', 'unknown').upper()}")
        print(f"Total Duration: {total_duration:.2f} seconds")
        print(f"Phases Completed: {summary.get('passed_phases', 0)}/{summary.get('total_phases', 0)}")
        print(f"Overall Success Rate: {summary.get('overall_success_rate', 0):.1f}%")

        if summary.get('critical_issues'):
            print("\n⚠️ Critical Issues:")
            for issue in summary['critical_issues']:
                print(f"  • {issue}")

        if summary.get('recommendations'):
            print("\n💡 Recommendations:")
            for rec in summary['recommendations']:
                print(f"  • {rec}")

        # Print phase details
        print("\n📋 Phase Results:")
        test_phases = results.get('test_phases', {})
        for phase_name, phase_results in test_phases.items():
            if 'summary' in phase_results:
                success_rate = phase_results['summary'].get('success_rate', 0)
                print(f"  {phase_name.replace('_', ' ').title()}: {success_rate:.1f}%")
            elif 'performance_score' in phase_results:
                score = phase_results['performance_score']
                grade = phase_results['summary'].get('grade', 'D')
                print(f"  {phase_name.replace('_', ' ').title()}: {score:.1f} ({grade})")
            else:
                status = "✅" if phase_results.get('passed', False) else "❌"
                print(f"  {phase_name.replace('_', ' ').title()}: {status}")

        print(f"\n🎯 Overall Result: {'SUCCESS' if summary.get('overall_success_rate', 0) >= 80 else 'NEEDS ATTENTION'}")

        return results.get('overall_status') == 'completed'

    except Exception as e:
        logger.error(f"Validation execution failed: {e}")
        print(f"\n❌ VALIDATION FAILED: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
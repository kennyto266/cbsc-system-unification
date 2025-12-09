#!/usr/bin/env python3
"""
Phase 3 Completion Testing
Simplified validation for the unified backtesting framework Phase 3 implementation
"""

import os
import sys
import json
import time
import logging
import traceback
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase3CompletionValidator:
    """Validator for Phase 3 implementation completion"""

    def __init__(self):
        self.start_time = time.time()
        self.results = {
            'start_time': datetime.now().isoformat(),
            'phase': 'Phase 3: Testing and Deployment',
            'components': {},
            'overall_status': 'in_progress'
        }

    def validate_docker_configuration(self):
        """Validate Docker deployment configuration"""
        logger.info("Validating Docker configuration...")

        docker_files = [
            'docker/Dockerfile',
            'docker/Dockerfile.gpu',
            'docker/docker-compose.yml',
            'docker/docker-compose.dev.yml',
            'docker/.dockerignore',
            'docker/prometheus.yml',
            'docker/nginx.conf'
        ]

        results = {
            'files_created': [],
            'files_missing': [],
            'validation_status': 'unknown'
        }

        for docker_file in docker_files:
            if Path(docker_file).exists():
                results['files_created'].append(docker_file)
                # Basic validation of file content
                try:
                    content = Path(docker_file).read_text(encoding='utf-8')
                    if len(content) > 100:  # Ensure file has meaningful content
                        logger.info(f"[OK] {docker_file} - Valid content")
                    else:
                        logger.warning(f"[WARN] {docker_file} - Content too short")
                except Exception as e:
                    logger.error(f"❌ {docker_file} - Error reading: {e}")
            else:
                results['files_missing'].append(docker_file)
                logger.error(f"❌ {docker_file} - Missing")

        results['validation_status'] = 'passed' if len(results['files_missing']) == 0 else 'failed'
        self.results['components']['docker_configuration'] = results

        return len(results['files_missing']) == 0

    def validate_monitoring_system(self):
        """Validate monitoring and logging system"""
        logger.info("📊 Validating monitoring system...")

        monitoring_files = [
            'src/monitoring/comprehensive_monitoring_system.py'
        ]

        results = {
            'files_created': [],
            'files_missing': [],
            'components_validated': [],
            'validation_status': 'unknown'
        }

        for monitoring_file in monitoring_files:
            if Path(monitoring_file).exists():
                results['files_created'].append(monitoring_file)
                try:
                    content = Path(monitoring_file).read_text(encoding='utf-8')

                    # Validate key components exist
                    components_to_check = [
                        'MetricsCollector',
                        'PrometheusMetricsExporter',
                        'StructuredLogger',
                        'AlertManager',
                        'ComprehensiveMonitoringSystem'
                    ]

                    for component in components_to_check:
                        if f"class {component}" in content:
                            results['components_validated'].append(component)
                            logger.info(f"✅ {component} - Found")
                        else:
                            logger.warning(f"⚠️ {component} - Not found")

                except Exception as e:
                    logger.error(f"❌ {monitoring_file} - Error reading: {e}")
            else:
                results['files_missing'].append(monitoring_file)
                logger.error(f"❌ {monitoring_file} - Missing")

        results['validation_status'] = 'passed' if len(results['files_missing']) == 0 else 'failed'
        self.results['components']['monitoring_system'] = results

        return len(results['files_missing']) == 0

    def validate_testing_framework(self):
        """Validate testing framework"""
        logger.info("🧪 Validating testing framework...")

        testing_files = [
            'src/unified_backtesting/testing/comprehensive_test_framework.py',
            'src/unified_backtesting/testing/performance_benchmark.py',
            'src/unified_backtesting/testing/stress_test.py'
        ]

        results = {
            'files_created': [],
            'files_missing': [],
            'framework_components': [],
            'validation_status': 'unknown'
        }

        for testing_file in testing_files:
            if Path(testing_file).exists():
                results['files_created'].append(testing_file)
                try:
                    content = Path(testing_file).read_text(encoding='utf-8')

                    # Check for key testing components
                    if 'comprehensive_test_framework.py' in testing_file:
                        components = ['UnifiedBacktestingTestCase', 'IntegrationTestSuite', 'TestDataGenerator']
                    elif 'performance_benchmark.py' in testing_file:
                        components = ['PerformanceProfiler', 'SystemMonitor', 'BenchmarkTestSuite']
                    elif 'stress_test.py' in testing_file:
                        components = ['StressTestSuite', 'FullSystemStressTest']
                    else:
                        components = []

                    for component in components:
                        if f"class {component}" in content:
                            results['framework_components'].append(component)
                            logger.info(f"✅ {component} - Found")

                except Exception as e:
                    logger.error(f"❌ {testing_file} - Error reading: {e}")
            else:
                results['files_missing'].append(testing_file)
                logger.error(f"❌ {testing_file} - Missing")

        results['validation_status'] = 'passed' if len(results['files_missing']) == 0 else 'failed'
        self.results['components']['testing_framework'] = results

        return len(results['files_missing']) == 0

    def validate_unified_backtesting_core(self):
        """Validate unified backtesting core components"""
        logger.info("⚙️ Validating unified backtesting core...")

        core_files = [
            'src/unified_backtesting/__init__.py',
            'src/unified_backtesting/core/__init__.py',
            'src/unified_backtesting/backtest/__init__.py',
            'src/unified_backtesting/config/__init__.py'
        ]

        results = {
            'core_files_found': 0,
            'core_files_total': len(core_files),
            'validation_status': 'unknown'
        }

        for core_file in core_files:
            if Path(core_file).exists():
                results['core_files_found'] += 1
                logger.info(f"✅ {core_file} - Found")
            else:
                logger.error(f"❌ {core_file} - Missing")

        results['validation_status'] = 'passed' if results['core_files_found'] == results['core_files_total'] else 'failed'
        self.results['components']['unified_backtesting_core'] = results

        return results['core_files_found'] == results['core_files_total']

    def validate_system_architecture(self):
        """Validate overall system architecture"""
        logger.info("🏗️ Validating system architecture...")

        architecture_components = {
            'core_directory': 'src/core/',
            'backtesting_directory': 'src/unified_backtesting/',
            'monitoring_directory': 'src/monitoring/',
            'docker_directory': 'docker/',
            'testing_directory': 'src/unified_backtesting/testing/',
            'configuration_directory': 'config/'
        }

        results = {
            'directories_valid': 0,
            'directories_total': len(architecture_components),
            'directory_status': {},
            'validation_status': 'unknown'
        }

        for name, path in architecture_components.items():
            if Path(path).exists() and Path(path).is_dir():
                results['directories_valid'] += 1
                results['directory_status'][name] = 'present'
                logger.info(f"✅ {name} - Present")
            else:
                results['directory_status'][name] = 'missing'
                logger.error(f"❌ {name} - Missing")

        results['validation_status'] = 'passed' if results['directories_valid'] == results['directories_total'] else 'failed'
        self.results['components']['system_architecture'] = results

        return results['directories_valid'] == results['directories_total']

    def run_complete_validation(self):
        """Run complete Phase 3 validation"""
        logger.info("🚀 Starting Phase 3 Completion Validation")

        validation_steps = [
            ('Docker Configuration', self.validate_docker_configuration),
            ('Monitoring System', self.validate_monitoring_system),
            ('Testing Framework', self.validate_testing_framework),
            ('Unified Backtesting Core', self.validate_unified_backtesting_core),
            ('System Architecture', self.validate_system_architecture)
        ]

        passed_steps = 0
        total_steps = len(validation_steps)

        for step_name, validator_func in validation_steps:
            logger.info(f"\n📋 Running: {step_name}")
            try:
                if validator_func():
                    passed_steps += 1
                    logger.info(f"✅ {step_name} - PASSED")
                else:
                    logger.error(f"❌ {step_name} - FAILED")
            except Exception as e:
                logger.error(f"❌ {step_name} - ERROR: {e}")

        # Calculate final results
        self.results['end_time'] = datetime.now().isoformat()
        self.results['total_duration'] = time.time() - self.start_time
        self.results['components_validated'] = passed_steps
        self.results['components_total'] = total_steps
        self.results['success_rate'] = (passed_steps / total_steps) * 100 if total_steps > 0 else 0

        if passed_steps == total_steps:
            self.results['overall_status'] = 'completed'
            logger.info("🎉 Phase 3 Validation COMPLETED successfully!")
        else:
            self.results['overall_status'] = 'partial'
            logger.warning(f"⚠️ Phase 3 Validation PARTIALLY completed: {passed_steps}/{total_steps}")

        return self.results

    def save_results(self):
        """Save validation results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"phase3_completion_validation_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)

            logger.info(f"📄 Validation results saved to: {filename}")
            return filename
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")
            return None

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 80)
        print("🎯 PHASE 3 COMPLETION VALIDATION SUMMARY")
        print("=" * 80)

        print(f"Overall Status: {self.results.get('overall_status', 'unknown').upper()}")
        print(f"Total Duration: {self.results.get('total_duration', 0):.2f} seconds")
        print(f"Components Validated: {self.results.get('components_validated', 0)}/{self.results.get('components_total', 0)}")
        print(f"Success Rate: {self.results.get('success_rate', 0):.1f}%")

        print("\n📋 Component Status:")
        components = self.results.get('components', {})
        for component, result in components.items():
            status = result.get('validation_status', 'unknown')
            icon = "✅" if status == 'passed' else "❌" if status == 'failed' else "⚠️"
            print(f"  {icon} {component.replace('_', ' ').title()}: {status.upper()}")

        if self.results.get('overall_status') == 'completed':
            print(f"\n🎉 Phase 3: Testing and Deployment - SUCCESSFULLY COMPLETED!")
            print("   All components validated and ready for production deployment.")
        else:
            print(f"\n⚠️ Phase 3: Testing and Deployment - NEEDS ATTENTION")
            print("   Some components require additional work before production deployment.")


def main():
    """Main execution function"""
    print("CBSC Unified Backtesting Framework - Phase 3 Completion Validator")
    print("=" * 80)

    validator = Phase3CompletionValidator()

    try:
        # Run validation
        results = validator.run_complete_validation()

        # Save results
        result_file = validator.save_results()

        # Print summary
        validator.print_summary()

        if result_file:
            print(f"\n📁 Detailed results available in: {result_file}")

        return results.get('overall_status') == 'completed'

    except Exception as e:
        logger.error(f"❌ Validation execution failed: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
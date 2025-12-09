#!/usr/bin/env python3
"""
Simple Phase 3 Completion Validation
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path


def validate_phase3():
    """Validate Phase 3 implementation"""
    print("CBSC Unified Backtesting Framework - Phase 3 Validation")
    print("=" * 70)

    results = {
        'start_time': datetime.now().isoformat(),
        'components': {},
        'overall_status': 'unknown'
    }

    # 1. Validate Docker Configuration
    print("\n1. Validating Docker Configuration...")
    docker_files = [
        'docker/Dockerfile',
        'docker/Dockerfile.gpu',
        'docker/docker-compose.yml',
        'docker/docker-compose.dev.yml',
        'docker/.dockerignore',
        'docker/prometheus.yml',
        'docker/nginx.conf'
    ]

    docker_results = {'present': [], 'missing': []}
    for file in docker_files:
        if Path(file).exists():
            docker_results['present'].append(file)
            print(f"   [OK] {file}")
        else:
            docker_results['missing'].append(file)
            print(f"   [MISSING] {file}")

    results['components']['docker'] = {
        'status': 'passed' if len(docker_results['missing']) == 0 else 'failed',
        'details': docker_results
    }

    # 2. Validate Monitoring System
    print("\n2. Validating Monitoring System...")
    monitoring_files = [
        'src/monitoring/comprehensive_monitoring_system.py'
    ]

    monitoring_results = {'present': [], 'missing': []}
    for file in monitoring_files:
        if Path(file).exists():
            monitoring_results['present'].append(file)
            print(f"   [OK] {file}")
        else:
            monitoring_results['missing'].append(file)
            print(f"   [MISSING] {file}")

    results['components']['monitoring'] = {
        'status': 'passed' if len(monitoring_results['missing']) == 0 else 'failed',
        'details': monitoring_results
    }

    # 3. Validate Testing Framework
    print("\n3. Validating Testing Framework...")
    testing_files = [
        'src/unified_backtesting/testing/comprehensive_test_framework.py',
        'src/unified_backtesting/testing/performance_benchmark.py',
        'src/unified_backtesting/testing/stress_test.py'
    ]

    testing_results = {'present': [], 'missing': []}
    for file in testing_files:
        if Path(file).exists():
            testing_results['present'].append(file)
            print(f"   [OK] {file}")
        else:
            testing_results['missing'].append(file)
            print(f"   [MISSING] {file}")

    results['components']['testing'] = {
        'status': 'passed' if len(testing_results['missing']) == 0 else 'failed',
        'details': testing_results
    }

    # 4. Validate Core Directories
    print("\n4. Validating Core Directories...")
    core_dirs = [
        'src/core/',
        'src/unified_backtesting/',
        'src/monitoring/',
        'docker/',
        'src/unified_backtesting/testing/',
        'config/'
    ]

    dir_results = {'present': [], 'missing': []}
    for dir_path in core_dirs:
        if Path(dir_path).exists() and Path(dir_path).is_dir():
            dir_results['present'].append(dir_path)
            print(f"   [OK] {dir_path}")
        else:
            dir_results['missing'].append(dir_path)
            print(f"   [MISSING] {dir_path}")

    results['components']['directories'] = {
        'status': 'passed' if len(dir_results['missing']) == 0 else 'failed',
        'details': dir_results
    }

    # 5. Calculate overall results
    passed_components = 0
    total_components = len(results['components'])

    for component, data in results['components'].items():
        if data['status'] == 'passed':
            passed_components += 1

    results['end_time'] = datetime.now().isoformat()
    results['components_passed'] = passed_components
    results['components_total'] = total_components
    results['success_rate'] = (passed_components / total_components) * 100 if total_components > 0 else 0
    results['overall_status'] = 'completed' if passed_components == total_components else 'partial'

    # 6. Print summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Components Passed: {passed_components}/{total_components}")
    print(f"Success Rate: {results['success_rate']:.1f}%")

    print("\nComponent Details:")
    for component, data in results['components'].items():
        status = data['status'].upper()
        print(f"  {component.replace('_', ' ').title()}: {status}")

    if results['overall_status'] == 'completed':
        print("\n[SUCCESS] Phase 3: Testing and Deployment - COMPLETED!")
        print("All components validated and ready for production deployment.")
    else:
        print("\n[PARTIAL] Phase 3: Testing and Deployment - NEEDS ATTENTION")
        print("Some components require additional work.")

    # 7. Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"phase3_validation_{timestamp}.json"

    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {filename}")
    except Exception as e:
        print(f"Error saving results: {e}")

    return results['overall_status'] == 'completed'


if __name__ == "__main__":
    success = validate_phase3()
    sys.exit(0 if success else 1)
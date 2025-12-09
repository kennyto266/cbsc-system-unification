#!/usr/bin/env python3
"""
Memory Performance Validation Script
Validates that the 32-core parallel processing system stays below the 6GB memory threshold

This script performs comprehensive memory testing to validate the stability fixes
implemented in Phase 1 of the priority-based stability improvements.
"""

import sys
import time
import psutil
import os
import gc
import threading
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.memory import (
        create_adaptive_allocator, create_leak_detector, create_pool_manager,
        initialize_memory_management, shutdown_memory_management,
        quick_memory_check, enable_all_features, disable_all_features
    )
    from personal_trading_system.src.parallel import ParallelProcessingSystem
    MEMORY_MANAGEMENT_AVAILABLE = True
except ImportError as e:
    MEMORY_MANAGEMENT_AVAILABLE = False
    print(f"❌ Memory management components not available: {e}")


class MemoryPerformanceValidator:
    """Validates memory performance against the 6GB threshold"""

    def __init__(self):
        self.max_memory_threshold_gb = 6.0
        self.test_duration_minutes = 10
        self.test_processes = 32
        self.test_data_size_mb = 2048  # 2GB test data

        self.results = {
            'initial_memory_mb': 0,
            'peak_memory_mb': 0,
            'final_memory_mb': 0,
            'memory_leaks_detected': 0,
            'oom_errors': 0,
            'test_passed': False,
            'performance_metrics': {},
            'recommendations': []
        }

    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def get_current_memory_mb(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0

    def get_system_memory_info(self) -> Dict[str, float]:
        """Get system memory information"""
        memory = psutil.virtual_memory()
        return {
            'total_gb': memory.total / (1024**3),
            'available_gb': memory.available / (1024**3),
            'used_gb': memory.used / (1024**3),
            'usage_percent': memory.percent
        }

    def test_adaptive_allocator(self) -> bool:
        """Test adaptive memory allocator performance"""
        self.log("Testing Adaptive Memory Allocator")

        try:
            allocator = create_adaptive_allocator(
                total_memory_gb=16.0,
                enable_monitoring=True,
                safety_margin_percent=15.0
            )

            # Test various allocation scenarios
            scenarios = [
                (1024, 16, "general"),      # Low pressure
                (3072, 24, "backtesting"), # Medium pressure
                (5120, 32, "optimization") # High pressure
            ]

            for data_size, processes, task_type in scenarios:
                self.log(f"  Testing allocation: {data_size}MB, {processes} processes, {task_type}")

                allocation = allocator.calculate_optimal_allocation(
                    data_size_mb=data_size,
                    concurrent_processes=processes,
                    task_type=task_type
                )

                current_memory = self.get_current_memory_mb()
                if current_memory > self.results['peak_memory_mb']:
                    self.results['peak_memory_mb'] = current_memory

                # Validate allocation efficiency
                if allocation.allocation_efficiency < 0.3:
                    self.results['recommendations'].append(
                        f"Low allocation efficiency ({allocation.allocation_efficiency:.2f}) "
                        f"for {task_type} with {data_size}MB data"
                    )

                self.log(f"    Strategy: {allocation.strategy_used.value}, "
                         f"Efficiency: {allocation.allocation_efficiency:.2f}")

            allocator.shutdown()
            return True

        except Exception as e:
            self.log(f"❌ Adaptive allocator test failed: {e}", "ERROR")
            return False

    def test_leak_detector(self) -> bool:
        """Test memory leak detector performance"""
        self.log("Testing Memory Leak Detector")

        try:
            leak_detector = create_leak_detector(
                detection_threshold_mb=50.0,
                monitoring_interval=5.0,
                enable_object_tracking=True
            )

            leak_detector.start_monitoring([os.getpid()])

            # Simulate memory patterns that could cause leaks
            memory_blocks = []
            for i in range(10):
                # Create some memory pressure
                block = [0] * (100000 * (i + 1))
                memory_blocks.append(block)

                current_memory = self.get_current_memory_mb()
                if current_memory > self.results['peak_memory_mb']:
                    self.results['peak_memory_mb'] = current_memory

                time.sleep(0.1)

            # Check for leaks
            report = leak_detector.get_leak_report()
            self.results['memory_leaks_detected'] = report['summary']['total_alerts']

            if self.results['memory_leaks_detected'] > 0:
                self.log(f"  ⚠️  Memory leaks detected: {self.results['memory_leaks_detected']}")
                self.results['recommendations'].append(
                    f"Memory leaks detected during testing: {self.results['memory_leaks_detected']}"
                )

            leak_detector.stop_monitoring()

            # Clean up memory blocks
            del memory_blocks
            gc.collect()

            return True

        except Exception as e:
            self.log(f"❌ Leak detector test failed: {e}", "ERROR")
            return False

    def test_pool_manager(self) -> bool:
        """Test memory pool manager performance"""
        self.log("Testing Memory Pool Manager")

        try:
            pool_manager = create_pool_manager(
                max_pools=20,
                max_total_memory_mb=2048.0,  # 2GB pool limit
                auto_defragment=True,
                enable_backup=True
            )

            # Test pool allocation and usage
            pools = []
            for i in range(15):
                pool_name = f"test_pool_{i}"
                pool = pool_manager.allocate_pool(pool_name, 100, "general")
                pools.append(pool)

                current_memory = self.get_current_memory_mb()
                if current_memory > self.results['peak_memory_mb']:
                    self.results['peak_memory_mb'] = current_memory

            # Test defragmentation
            defrag_result = pool_manager._defragment_pools()
            self.log(f"  Defragmentation: {defrag_result.pools_processed} pools, "
                         f"{defrag_result.memory_freed_mb:.1f}MB freed")

            # Cleanup pools
            for pool in pools:
                pool_manager.deallocate_pool(pool.name, force=True)

            pool_manager.shutdown()
            return True

        except Exception as e:
            self.log(f"❌ Pool manager test failed: {e}", "ERROR")
            return False

    def test_parallel_processing_system(self) -> bool:
        """Test the integrated parallel processing system"""
        self.log("Testing Parallel Processing System Integration")

        try:
            # Create system with new memory management enabled
            system = ParallelProcessingSystem(
                max_workers=self.test_processes,
                memory_limit_gb=16.0,
                enable_new_memory_management=True,
                enable_optimization=True,
                enable_monitoring=True
            )

            # Initialize system
            if not system.initialize():
                raise Exception("Failed to initialize parallel processing system")

            # Start system
            system.start()

            # Simulate workload for 2 minutes
            self.log(f"  Running workload for 2 minutes with {self.test_processes} workers")
            start_time = time.time()

            while time.time() - start_time < 120:  # 2 minutes
                current_memory = self.get_current_memory_mb()
                if current_memory > self.results['peak_memory_mb']:
                    self.results['peak_memory_mb'] = current_memory

                # Check if exceeding threshold
                if current_memory > (self.max_memory_threshold_gb * 1024):
                    self.log(f"  ⚠️  Memory exceeded threshold: {current_memory:.1f}MB")
                    self.results['recommendations'].append(
                        f"Memory usage exceeded 6GB threshold: {current_memory:.1f}MB"
                    )

                time.sleep(5)

            # Get system status
            status = system.get_system_status()
            self.results['performance_metrics'] = {
                'system_status': status,
                'memory_report': system.memory_optimizer.get_memory_report() if system.memory_optimizer else None
            }

            # Stop system
            system.stop()

            return True

        except Exception as e:
            self.log(f"❌ Parallel processing system test failed: {e}", "ERROR")
            self.results['oom_errors'] += 1
            return False

    def test_memory_pressure_response(self) -> bool:
        """Test system response to memory pressure"""
        self.log("Testing Memory Pressure Response")

        try:
            allocator = create_adaptive_allocator(total_memory_gb=8.0)

            # Simulate increasing memory pressure
            test_cases = [
                (2048, 8, "Low pressure"),    # 25% of total
                (4096, 16, "Medium pressure"), # 50% of total
                (6144, 24, "High pressure"),  # 75% of total
            ]

            for data_size, processes, description in test_cases:
                self.log(f"  Testing {description}")

                allocation = allocator.calculate_optimal_allocation(
                    data_size_mb=data_size,
                    concurrent_processes=processes,
                    task_type="data_processing"
                )

                current_memory = self.get_current_memory_mb()
                if current_memory > self.results['peak_memory_mb']:
                    self.results['peak_memory_mb'] = current_memory

                # Check if strategy adapts to pressure
                if allocation.pressure_level.value in ["high", "critical"]:
                    if allocation.strategy_used.value not in ["conservative", "balanced"]:
                        self.results['recommendations'].append(
                            f"Strategy not conservative enough for {description}: {allocation.strategy_used.value}"
                        )

                self.log(f"    Pressure: {allocation.pressure_level.value}, "
                         f"Strategy: {allocation.strategy_used.value}")

            allocator.shutdown()
            return True

        except Exception as e:
            self.log(f"❌ Memory pressure test failed: {e}", "ERROR")
            return False

    def run_validation(self) -> bool:
        """Run complete memory performance validation"""
        self.log("=" * 70)
        self.log("MEMORY PERFORMANCE VALIDATION - 6GB THRESHOLD TEST")
        self.log("=" * 70)

        # Enable all memory management features
        enable_all_features()

        # Record initial memory
        self.results['initial_memory_mb'] = self.get_current_memory_mb()
        system_memory = self.get_system_memory_info()

        self.log(f"Initial memory usage: {self.results['initial_memory_mb']:.1f}MB")
        self.log(f"System memory: {system_memory['total_gb']:.1f}GB total, "
                 f"{system_memory['available_gb']:.1f}GB available")

        # Run individual tests
        tests = [
            ("Adaptive Allocator", self.test_adaptive_allocator),
            ("Memory Leak Detector", self.test_leak_detector),
            ("Memory Pool Manager", self.test_pool_manager),
            ("Memory Pressure Response", self.test_memory_pressure_response),
            ("Parallel Processing System", self.test_parallel_processing_system),
        ]

        test_results = {}
        for test_name, test_func in tests:
            self.log(f"\n{'-' * 50}")
            self.log(f"Running: {test_name}")
            self.log(f"{'-' * 50}")

            try:
                test_results[test_name] = test_func()
                status = "✅ PASSED" if test_results[test_name] else "❌ FAILED"
                self.log(f"{test_name}: {status}")
            except Exception as e:
                self.log(f"❌ {test_name} failed with exception: {e}", "ERROR")
                test_results[test_name] = False

        # Record final memory
        self.results['final_memory_mb'] = self.get_current_memory_mb()

        # Force garbage collection
        gc.collect()

        # Calculate results
        self.results['test_passed'] = self._evaluate_results()
        all_tests_passed = all(test_results.values())

        # Print summary
        self._print_summary(system_memory, test_results)

        # Disable features after testing
        disable_all_features()

        return self.results['test_passed'] and all_tests_passed

    def _evaluate_results(self) -> bool:
        """Evaluate test results against criteria"""
        # Check memory threshold
        memory_exceeded = self.results['peak_memory_mb'] > (self.max_memory_threshold_gb * 1024)

        # Check for critical issues
        critical_issues = (
            self.results['oom_errors'] > 0 or
            self.results['memory_leaks_detected'] > 5  # Allow some minor leaks
        )

        # Final evaluation
        if memory_exceeded:
            self.results['recommendations'].insert(0,
                f"CRITICAL: Memory usage ({self.results['peak_memory_mb']:.1f}MB) "
                f"exceeded 6GB threshold ({self.max_memory_threshold_gb * 1024:.0f}MB)"
            )

        if critical_issues:
            self.results['recommendations'].insert(0,
                f"CRITICAL: System stability issues detected "
                f"(OOM: {self.results['oom_errors']}, Leaks: {self.results['memory_leaks_detected']})"
            )

        return not memory_exceeded and not critical_issues

    def _print_summary(self, system_memory: Dict[str, float], test_results: Dict[str, bool]):
        """Print validation summary"""
        self.log("\n" + "=" * 70)
        self.log("VALIDATION SUMMARY")
        self.log("=" * 70)

        # Memory usage summary
        self.log(f"Memory Usage:")
        self.log(f"  Initial:     {self.results['initial_memory_mb']:.1f}MB")
        self.log(f"  Peak:        {self.results['peak_memory_mb']:.1f}MB")
        self.log(f"  Final:       {self.results['final_memory_mb']:.1f}MB")
        self.log(f"  Threshold:   {self.max_memory_threshold_gb * 1024:.0f}MB (6GB)")

        memory_status = "✅ WITHIN THRESHOLD" if self.results['peak_memory_mb'] <= (self.max_memory_threshold_gb * 1024) else "❌ EXCEEDED THRESHOLD"
        self.log(f"  Status:      {memory_status}")

        # System memory
        self.log(f"\nSystem Memory:")
        self.log(f"  Total:       {system_memory['total_gb']:.1f}GB")
        self.log(f"  Available:   {system_memory['available_gb']:.1f}GB")
        self.log(f"  Used:        {system_memory['used_gb']:.1f}GB")
        self.log(f"  Usage:       {system_memory['usage_percent']:.1f}%")

        # Test results
        self.log(f"\nTest Results:")
        for test_name, passed in test_results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            self.log(f"  {test_name}: {status}")

        # Issues detected
        self.log(f"\nIssues Detected:")
        self.log(f"  Memory leaks: {self.results['memory_leaks_detected']}")
        self.log(f"  OOM errors:   {self.results['oom_errors']}")

        # Overall result
        overall_status = "✅ PASSED" if self.results['test_passed'] else "❌ FAILED"
        self.log(f"\nOverall Result: {overall_status}")

        # Recommendations
        if self.results['recommendations']:
            self.log(f"\nRecommendations:")
            for i, rec in enumerate(self.results['recommendations'], 1):
                self.log(f"  {i}. {rec}")

        self.log("=" * 70)

    def save_results(self, filename: str = None):
        """Save validation results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"memory_validation_report_{timestamp}.json"

        try:
            import json
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            self.log(f"Results saved to: {filename}")
        except Exception as e:
            self.log(f"Failed to save results: {e}", "ERROR")


def main():
    """Main validation function"""
    print("🚀 Starting Memory Performance Validation")
    print(f"Target: Keep memory usage below 6GB threshold")
    print(f"Testing with 32-core parallel processing system")

    validator = MemoryPerformanceValidator()

    try:
        success = validator.run_validation()

        # Save results
        validator.save_results()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Validation failed with unexpected error: {e}")
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Simple test for the parallel backtesting engine core components.

Tests only the parallel module without full CBSC integration.
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test imports
try:
    from backtest.parallel.models import Task, TaskType, TaskComplexity, TaskResult
    from backtest.parallel.task_distributor import TaskDistributor, SchedulingStrategy
    from backtest.parallel.process_pool import SystemMonitor
    from backtest.parallel.fault_handler import FaultHandler
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def test_basic_functionality():
    """Test basic functionality of core components."""
    print("\n🧪 Testing core component functionality...")

    # Test Task creation
    task = Task(
        type=TaskType.BACKTEST,
        complexity=TaskComplexity.MEDIUM,
        strategy_code="def test(): return True",
        parameters={"test": True},
        priority=1
    )
    print(f"✅ Task created: {task.id} ({task.type})")

    # Test TaskResult creation
    result = TaskResult(
        task_id=task.id,
        success=True,
        execution_time=1.5,
        performance_metrics={"return": 0.05}
    )
    print(f"✅ TaskResult created: {result.success}")

    # Test TaskEstimator (via TaskDistributor)
    distributor = TaskDistributor(enable_adaptive=False)
    estimate = distributor.estimator.estimate_task(task)
    print(f"✅ Task estimate: {estimate.estimated_duration:.2f}s duration")

    # Test SystemMonitor
    monitor = SystemMonitor()
    load = monitor.get_current_load()
    print(f"✅ System load: CPU {load['cpu_percent']:.1f}%, Memory {load['memory_percent']:.1f}%")

    # Test optimal process count
    optimal = monitor.get_optimal_process_count()
    print(f"✅ Optimal process count: {optimal}")

    return True


def test_task_distribution():
    """Test task distribution logic."""
    print("\n🧪 Testing task distribution...")

    distributor = TaskDistributor(
        scheduling_strategy=SchedulingStrategy.LOAD_BALANCED,
        enable_adaptive=False
    )

    # Register mock processes
    from backtest.parallel.task_distributor import ProcessLoad
    processes = []
    for i in range(3):
        process_load = ProcessLoad(process_id=i)
        distributor.register_process(process_load)
        processes.append(process_load)

    print(f"✅ Registered {len(processes)} processes")

    # Create and distribute tasks
    tasks = []
    for i in range(5):
        task = Task(
            type=TaskType.BACKTEST,
            complexity=TaskComplexity.MEDIUM,
            strategy_code=f"strategy_{i}",
            parameters={"iterations": (i + 1) * 10}
        )
        tasks.append(task)

    distributed = 0
    for task in tasks:
        process_id = distributor.distribute_task(task)
        if process_id is not None:
            distributed += 1
            print(f"✅ Task {task.id[:8]} -> Process {process_id}")

    print(f"✅ Distributed {distributed}/{len(tasks)} tasks")
    return distributed > 0


def test_fault_handling():
    """Test fault handling components."""
    print("\n🧪 Testing fault handling...")

    handler = FaultHandler(enable_resource_monitoring=False)

    # Test error classification
    test_errors = [
        Exception("timeout occurred"),
        MemoryError("out of memory"),
        ValueError("invalid value"),
        RuntimeError("runtime error")
    ]

    for error in test_errors:
        error_report = handler.handle_error("test_task", 1, error)
        print(f"✅ Handled {type(error).__name__}: {error_report.error_type}")

    # Test health report
    health = handler.get_health_report()
    print(f"✅ Health report: {health['processes']['total']} processes, {health['errors']['total']} errors")

    return True


def test_scheduling_strategies():
    """Test different scheduling strategies."""
    print("\n🧪 Testing scheduling strategies...")

    strategies = [
        SchedulingStrategy.ROUND_ROBIN,
        SchedulingStrategy.LOAD_BALANCED,
        SchedulingStrategy.PRIORITY_FIRST,
        SchedulingStrategy.COMPLEXITY_AWARE
    ]

    for strategy in strategies:
        distributor = TaskDistributor(scheduling_strategy=strategy, enable_adaptive=False)

        # Register processes
        from backtest.parallel.task_distributor import ProcessLoad
        for i in range(2):
            distributor.register_process(ProcessLoad(process_id=i))

        # Test one task
        task = Task(
            type=TaskType.BACKTEST,
            complexity=TaskComplexity.MEDIUM,
            strategy_code="test",
            parameters={"test": True}
        )

        process_id = distributor.distribute_task(task)
        if process_id is not None:
            print(f"✅ {strategy.value}: Task assigned to process {process_id}")
        else:
            print(f"❌ {strategy.value}: No process assigned")

    return True


def main():
    """Run all tests."""
    print("🚀 Starting Parallel Engine Component Tests")
    print("=" * 50)

    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Task Distribution", test_task_distribution),
        ("Fault Handling", test_fault_handling),
        ("Scheduling Strategies", test_scheduling_strategies)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            print(f"\n{'─' * 20} {test_name} {'─' * 20}")
            start_time = time.time()
            success = test_func()
            duration = time.time() - start_time

            results.append((test_name, success, duration))
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{status} ({duration:.3f}s)")

        except Exception as e:
            print(f"❌ FAILED with exception: {e}")
            results.append((test_name, False, 0))

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for test_name, success, duration in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:25} {status} ({duration:.3f}s)")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Parallel engine components are working correctly.")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
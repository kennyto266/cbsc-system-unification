#!/usr/bin/env python3
"""
Direct test of parallel engine components without complex imports.
"""

import sys
import os

# Set Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Test basic model imports directly
def test_models():
    """Test models directly."""
    try:
        # Import directly from the module file
        import importlib.util

        # Load models module
        models_path = os.path.join(src_dir, 'backtest', 'parallel', 'models.py')
        spec = importlib.util.spec_from_file_location("models", models_path)
        models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models)

        # Test basic functionality
        task = models.Task(
            type=models.TaskType.BACKTEST,
            complexity=models.TaskComplexity.MEDIUM,
            strategy_code="test",
            parameters={"test": True}
        )

        print("SUCCESS: Models import and basic functionality working")
        print(f"Task ID: {task.id}")
        print(f"Task type: {task.type}")
        print(f"Task complexity: {task.complexity}")

        return True

    except Exception as e:
        print(f"ERROR in models test: {e}")
        return False


def test_task_distributor():
    """Test task distributor directly."""
    try:
        import importlib.util

        # Load models first
        models_path = os.path.join(src_dir, 'backtest', 'parallel', 'models.py')
        spec = importlib.util.spec_from_file_location("models", models_path)
        models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models)

        # Load task distributor
        dist_path = os.path.join(src_dir, 'backtest', 'parallel', 'task_distributor.py')
        spec = importlib.util.spec_from_file_location("task_distributor", dist_path)
        task_distributor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(task_distributor)

        # Create estimator and test
        estimator = task_distributor.TaskEstimator()

        task = models.Task(
            type=models.TaskType.BACKTEST,
            complexity=models.TaskComplexity.MEDIUM,
            strategy_code="test",
            parameters={"iterations": 100}
        )

        estimate = estimator.estimate_task(task)
        print("SUCCESS: Task distributor working")
        print(f"Estimated duration: {estimate.estimated_duration:.2f}s")
        print(f"Memory requirement: {estimate.memory_requirement:.1f}MB")

        return True

    except Exception as e:
        print(f"ERROR in task distributor test: {e}")
        return False


def test_process_pool():
    """Test process pool directly."""
    try:
        import importlib.util

        # Load system monitor
        monitor_path = os.path.join(src_dir, 'backtest', 'parallel', 'process_pool.py')
        spec = importlib.util.spec_from_file_location("process_pool", monitor_path)
        process_pool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(process_pool)

        # Test system monitor
        monitor = process_pool.SystemMonitor()
        load = monitor.get_current_load()

        print("SUCCESS: Process pool working")
        print(f"CPU usage: {load['cpu_percent']:.1f}%")
        print(f"Memory usage: {load['memory_percent']:.1f}%")
        print(f"Optimal processes: {monitor.get_optimal_process_count()}")

        return True

    except Exception as e:
        print(f"ERROR in process pool test: {e}")
        return False


def main():
    """Run direct tests."""
    print("Direct Parallel Engine Component Tests")
    print("=" * 50)

    tests = [
        ("Models", test_models),
        ("Task Distributor", test_task_distributor),
        ("Process Pool", test_process_pool)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        try:
            success = test_func()
            results.append((test_name, success))
            status = "PASSED" if success else "FAILED"
            print(f"{test_name}: {status}")
        except Exception as e:
            print(f"{test_name}: FAILED - {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "PASSED" if success else "FAILED"
        print(f"{test_name}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("All tests passed!")
        return 0
    else:
        print(f"{total - passed} tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
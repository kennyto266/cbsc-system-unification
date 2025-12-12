#!/usr/bin/env python3
"""
Simple test script for the parallel backtesting engine components.

This script tests the basic functionality of the multiprocessing system
without requiring actual backtesting data.
"""

import time
import logging
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from backtest.parallel.models import Task, TaskType, TaskComplexity
from backtest.parallel.task_distributor import TaskDistributor, SchedulingStrategy
from backtest.parallel.process_pool import SystemMonitor
from backtest.parallel.fault_handler import FaultHandler
from backtest.parallel.parallel_engine import ParallelEngine, EngineConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_models():
    """Test the data models."""
    logger.info("Testing data models...")

    # Create a test task
    task = Task(
        type=TaskType.BACKTEST,
        complexity=TaskComplexity.MEDIUM,
        strategy_code="def test_strategy(): pass",
        parameters={"param1": "value1", "param2": [1, 2, 3]},
        priority=1
    )

    logger.info(f"Created task: {task.id}")
    logger.info(f"Task type: {task.type}")
    logger.info(f"Task complexity: {task.complexity}")
    logger.info(f"Task priority: {task.priority}")

    # Mark task as started
    task.mark_started()
    logger.info(f"Task started at: {task.started_at}")

    # Mark task as completed
    task.mark_completed(success=True)
    logger.info(f"Task completed at: {task.completed_at}")
    logger.info(f"Task execution time: {task.execution_time:.2f}s")

    return True


def test_system_monitor():
    """Test the system monitor."""
    logger.info("Testing system monitor...")

    monitor = SystemMonitor()
    load = monitor.get_current_load()

    logger.info(f"System load: {load}")
    logger.info(f"CPU usage: {load['cpu_percent']:.1f}%")
    logger.info(f"Memory usage: {load['memory_percent']:.1f}%")
    logger.info(f"Available memory: {load['memory_available_gb']:.1f}GB")

    optimal_count = monitor.get_optimal_process_count()
    logger.info(f"Optimal process count: {optimal_count}")

    can_spawn = monitor.can_spawn_process(1024.0)  # 1GB
    logger.info(f"Can spawn process with 1GB memory: {can_spawn}")

    return True


def test_task_distributor():
    """Test the task distributor."""
    logger.info("Testing task distributor...")

    distributor = TaskDistributor(
        scheduling_strategy=SchedulingStrategy.LOAD_BALANCED,
        enable_adaptive=False  # Disable for simple test
    )

    # Create test processes
    from backtest.parallel.task_distributor import ProcessLoad
    for i in range(4):
        process_load = ProcessLoad(process_id=i)
        distributor.register_process(process_load)

    # Create test tasks
    tasks = []
    for i in range(10):
        task = Task(
            type=TaskType.BACKTEST,
            complexity=TaskComplexity.MEDIUM if i % 2 == 0 else TaskComplexity.HIGH,
            strategy_code=f"strategy_{i}",
            parameters={"iterations": 100 * (i + 1)},
            priority=i % 3
        )
        tasks.append(task)

    # Test task distribution
    distributed_count = 0
    for task in tasks:
        process_id = distributor.distribute_task(task)
        if process_id is not None:
            distributed_count += 1
            logger.info(f"Task {task.id} assigned to process {process_id}")

    logger.info(f"Distributed {distributed_count} out of {len(tasks)} tasks")

    # Get status
    status = distributor.get_status()
    logger.info(f"Distributor status: {status}")

    return distributed_count > 0


def test_fault_handler():
    """Test the fault handler."""
    logger.info("Testing fault handler...")

    handler = FaultHandler(enable_resource_monitoring=False)
    handler.start()

    # Test error handling
    try:
        raise ValueError("Test error")
    except Exception as e:
        error_report = handler.handle_error("test_task", 1, e)
        logger.info(f"Error report created: {error_report.error_type}")
        logger.info(f"Recovery action: {error_report.recovery_action}")

    # Get health report
    health_report = handler.get_health_report()
    logger.info(f"Health report: {health_report}")

    handler.stop()
    return True


def test_parallel_engine():
    """Test the parallel engine (lightweight)."""
    logger.info("Testing parallel engine...")

    config = EngineConfig(
        min_processes=2,
        max_processes=4,
        auto_scaling=False,
        enable_monitoring=False,
        enable_metrics=False,
        enable_shared_memory=False,
        enable_network_transport=False
    )

    # Create engine without starting it (to avoid full process creation)
    engine = ParallelEngine(config)

    logger.info("Parallel engine created successfully")

    # Test task creation
    task = Task(
        type=TaskType.BACKTEST,
        complexity=TaskComplexity.LOW,
        strategy_code="def simple_strategy(): return True",
        parameters={"test": True}
    )

    logger.info(f"Test task created: {task.id}")

    return True


def main():
    """Run all tests."""
    logger.info("Starting parallel engine component tests...")

    tests = [
        ("Data Models", test_models),
        ("System Monitor", test_system_monitor),
        ("Task Distributor", test_task_distributor),
        ("Fault Handler", test_fault_handler),
        ("Parallel Engine", test_parallel_engine)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running {test_name} test")
            logger.info(f"{'='*50}")

            start_time = time.time()
            success = test_func()
            duration = time.time() - start_time

            results.append((test_name, success, duration))
            status = "✅ PASSED" if success else "❌ FAILED"
            logger.info(f"{test_name} test {status} ({duration:.3f}s)")

        except Exception as e:
            logger.error(f"{test_name} test failed with exception: {e}")
            results.append((test_name, False, 0))

    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for test_name, success, duration in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{test_name:20} {status} ({duration:.3f}s)")

    logger.info(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error(f"💥 {total - passed} tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
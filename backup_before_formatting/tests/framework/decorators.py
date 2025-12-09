"""
Test decorators for categorizing and configuring tests.
"""

import asyncio
import functools
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from .core import TestStatus, TestType
from .utils import MetricsCollector, TestLogger


def unit_test(timeout: Optional[float] = None, retries: int = 0):
    """Decorator for unit tests."""

    def decorator(func: Callable):
        func._test_type = TestType.UNIT
        func._timeout = timeout
        func._retries = retries
        return func

    return decorator


def integration_test(timeout: Optional[float] = None, retries: int = 1):
    """Decorator for integration tests."""

    def decorator(func: Callable):
        func._test_type = TestType.INTEGRATION
        func._timeout = timeout
        func._retries = retries
        return func

    return decorator


def e2e_test(timeout: Optional[float] = None, retries: int = 2):
    """Decorator for end - to - end tests."""

    def decorator(func: Callable):
        func._test_type = TestType.E2E
        func._timeout = timeout
        func._retries = retries
        return func

    return decorator


def performance_test(
    timeout: Optional[float] = None,
    max_duration: Optional[float] = None,
    max_memory_mb: Optional[float] = None,
):
    """Decorator for performance tests."""

    def decorator(func: Callable):
        func._test_type = TestType.PERFORMANCE
        func._timeout = timeout
        func._max_duration = max_duration
        func._max_memory_mb = max_memory_mb

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger = TestLogger()
            metrics = MetricsCollector()

            test_id = str(uuid.uuid4())
            logger.info(
                f"Starting performance test: {func.__name__}", {"test_id": test_id}
            )

            # Start monitoring
            metrics.start_monitoring(test_id)

            try:
                # Measure execution time
                start_time = time.time()
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Stop monitoring and get metrics
                test_metrics = metrics.stop_monitoring(test_id)

                # Check performance thresholds
                violations = []

                if max_duration and duration > max_duration:
                    violations.append(
                        f"Duration {duration:.2f}s exceeds max {max_duration}s"
                    )

                if max_memory_mb and test_metrics.get("max_memory", 0) > max_memory_mb:
                    violations.append(
                        f"Memory {test_metrics['max_memory']:.2f}MB exceeds max {max_memory_mb}MB"
                    )

                if violations:
                    logger.error(
                        f"Performance test failed: {func.__name__}",
                        {"violations": violations},
                    )
                    raise AssertionError(
                        f"Performance thresholds exceeded: {'; '.join(violations)}"
                    )

                logger.info(
                    f"Performance test passed: {func.__name__}",
                    {"duration": duration, "metrics": test_metrics},
                )

                return result

            except Exception as e:
                metrics.stop_monitoring(test_id)
                logger.error(
                    f"Performance test error: {func.__name__}", {"error": str(e)}
                )
                raise

        return wrapper

    return decorator


def security_test(timeout: Optional[float] = None, severity: str = "medium"):
    """Decorator for security tests."""

    def decorator(func: Callable):
        func._test_type = TestType.SECURITY
        func._timeout = timeout
        func._severity = severity
        return func

    return decorator


def load_test(
    timeout: Optional[float] = None,
    concurrent_users: int = 10,
    duration_seconds: int = 60,
):
    """Decorator for load tests."""

    def decorator(func: Callable):
        func._test_type = TestType.LOAD
        func._timeout = timeout
        func._concurrent_users = concurrent_users
        func._duration_seconds = duration_seconds

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger = TestLogger()
            logger.info(
                f"Starting load test: {func.__name__}",
                {"concurrent_users": concurrent_users, "duration": duration_seconds},
            )

            # Create semaphore to limit concurrent users
            semaphore = asyncio.Semaphore(concurrent_users)

            async def user_session(user_id: int):
                async with semaphore:
                    try:
                        result = await func(*args, user_id=user_id, **kwargs)
                        return {"user_id": user_id, "success": True, "result": result}
                    except Exception as e:
                        return {"user_id": user_id, "success": False, "error": str(e)}

            # Start user sessions
            start_time = time.time()
            tasks = [
                asyncio.create_task(user_session(i)) for i in range(concurrent_users)
            ]

            # Wait for completion or timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=duration_seconds,
                )
            except asyncio.TimeoutError:
                for task in tasks:
                    task.cancel()
                raise TimeoutError(
                    f"Load test exceeded duration of {duration_seconds}s"
                )

            # Analyze results
            successful_results = [
                r for r in results if isinstance(r, dict) and r.get("success")
            ]
            failed_results = [
                r for r in results if isinstance(r, dict) and not r.get("success")
            ]

            success_rate = len(successful_results) / len(results)
            actual_duration = time.time() - start_time

            logger.info(
                f"Load test completed: {func.__name__}",
                {
                    "success_rate": success_rate,
                    "successful_users": len(successful_results),
                    "failed_users": len(failed_results),
                    "duration": actual_duration,
                },
            )

            # Fail if success rate is too low
            if success_rate < 0.95:  # 95% success rate required
                raise AssertionError(
                    f"Load test failed: success rate {success_rate:.2%} is below 95%"
                )

            return {
                "success_rate": success_rate,
                "successful_users": len(successful_results),
                "failed_users": len(failed_results),
                "duration": actual_duration,
                "results": results,
            }

        return wrapper

    return decorator


def smoke_test(timeout: Optional[float] = None):
    """Decorator for smoke tests (basic health checks)."""

    def decorator(func: Callable):
        func._test_type = TestType.SMOKE
        func._timeout = timeout
        return func

    return decorator


def regression_test(timeout: Optional[float] = None):
    """Decorator for regression tests."""

    def decorator(func: Callable):
        func._test_type = TestType.REGRESSION
        func._timeout = timeout
        return func

    return decorator


def flaky_test(max_attempts: int = 3, delay_between_attempts: float = 1.0):
    """Decorator for flaky tests that may need retries."""

    def decorator(func: Callable):
        func._max_attempts = max_attempts
        func._delay_between_attempts = delay_between_attempts

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger = TestLogger()

            for attempt in range(max_attempts):
                try:
                    if attempt > 0:
                        logger.info(
                            f"Retrying flaky test: {func.__name__} (attempt {attempt + 1}/{max_attempts})"
                        )
                        await asyncio.sleep(delay_between_attempts)

                    return await func(*args, **kwargs)

                except Exception as e:
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"Flaky test failed after {max_attempts} attempts: {func.__name__}",
                            {"error": str(e)},
                        )
                        raise
                    else:
                        logger.warning(
                            f"Flaky test attempt {attempt + 1} failed: {func.__name__}",
                            {"error": str(e)},
                        )

        return wrapper

    return decorator


def timed_test(max_duration: Optional[float] = None):
    """Decorator that measures and optionally limits test execution time."""

    def decorator(func: Callable):
        func._max_duration = max_duration

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger = TestLogger()
            start_time = time.time()

            try:
                if max_duration:
                    result = await asyncio.wait_for(
                        func(*args, **kwargs), timeout=max_duration
                    )
                else:
                    result = await func(*args, **kwargs)

                duration = time.time() - start_time
                logger.info(f"Test completed: {func.__name__}", {"duration": duration})

                return result

            except asyncio.TimeoutError:
                duration = time.time() - start_time
                logger.error(f"Test timed out: {func.__name__}", {"duration": duration})
                raise TimeoutError(
                    f"Test {func.__name__} exceeded maximum duration of {max_duration}s"
                )

        return wrapper

    return decorator


def parameterized_test(*args):
    """Decorator for parameterized tests."""

    def decorator(func: Callable):
        func._parameterized = True
        func._parameter_args = args

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger = TestLogger()
            results = []

            for i, param_set in enumerate(args):
                try:
                    logger.info(
                        f"Running parameterized test {func.__name__} with params {i + 1}/{len(args)}"
                    )

                    # If parameters are a tuple, expand them
                    if isinstance(param_set, (list, tuple)):
                        result = await func(*(args + tuple(param_set)), **kwargs)
                    else:
                        result = await func(*(args + (param_set,)), **kwargs)

                    results.append(
                        {
                            "param_index": i,
                            "params": param_set,
                            "result": result,
                            "success": True,
                        }
                    )

                except Exception as e:
                    logger.error(
                        f"Parameterized test {func.__name__} failed with params {i + 1}",
                        {"params": param_set, "error": str(e)},
                    )
                    results.append(
                        {
                            "param_index": i,
                            "params": param_set,
                            "error": str(e),
                            "success": False,
                        }
                    )

            # Fail if any parameter set failed
            failed_results = [r for r in results if not r["success"]]
            if failed_results:
                failed_params = [r["params"] for r in failed_results]
                raise AssertionError(
                    f"Parameterized test failed for params: {failed_params}"
                )

            return results

        return wrapper

    return decorator


def depends_on(*dependencies):
    """Decorator to specify test dependencies."""

    def decorator(func: Callable):
        func._dependencies = dependencies
        return func

    return decorator


def skip_if(condition: bool, reason: str = ""):
    """Decorator to conditionally skip tests."""

    def decorator(func: Callable):
        if condition:
            func._skip_reason = reason
            func._skip = True
        return func

    return decorator


def skip_until(date: datetime, reason: str = ""):
    """Decorator to skip tests until a specific date."""

    def decorator(func: Callable):
        if datetime.now() < date:
            func._skip_reason = f"{reason} (skipped until {date.isoformat()})"
            func._skip = True
        return func

    return decorator


def mark_slow(func: Callable):
    """Decorator to mark tests as slow."""
    func._slow = True
    return func


def mark_expensive(func: Callable):
    """Decorator to mark tests as expensive (resource - intensive)."""
    func._expensive = True
    return func


def requires_network(func: Callable):
    """Decorator for tests that require network access."""
    func._requires_network = True
    return func


def requires_database(func: Callable):
    """Decorator for tests that require database access."""
    func._requires_database = True
    return func


def requires_external_service(service_name: str):
    """Decorator for tests that require external services."""

    def decorator(func: Callable):
        func._requires_external_service = service_name
        return func

    return decorator


def with_test_data(data_file: str):
    """Decorator to load test data from file."""

    def decorator(func: Callable):
        func._test_data_file = data_file

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            import json
            from pathlib import Path

            import yaml

            data_path = Path(data_file)
            if not data_path.exists():
                raise FileNotFoundError(f"Test data file not found: {data_file}")

            # Load data based on file extension
            if data_path.suffix.lower() in [".yaml", ".yml"]:
                with open(data_path, "r") as f:
                    test_data = yaml.safe_load(f)
            elif data_path.suffix.lower() == ".json":
                with open(data_path, "r") as f:
                    test_data = json.load(f)
            else:
                raise ValueError(
                    f"Unsupported test data file format: {data_path.suffix}"
                )

            return await func(*args, test_data=test_data, **kwargs)

        return wrapper

    return decorator


def cleanup_after(func: Callable):
    """Decorator that ensures cleanup after test execution."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        finally:
            # Perform cleanup operations
            logger = TestLogger()
            logger.info(f"Performing cleanup for test: {func.__name__}")

            # Add specific cleanup logic here
            # This could include:
            # - Cleaning up temporary files
            # - Closing database connections
            # - Stopping background services
            # - Resetting test environment

    return wrapper

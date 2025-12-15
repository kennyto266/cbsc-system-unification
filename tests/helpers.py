"""
Test helper functions and utilities
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from unittest.mock import AsyncMock, Mock
import json
import random
import string


def generate_test_id() -> str:
    """Generate a random test ID"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))


def async_test(func):
    """Decorator to mark async test functions"""
    func.__pytest_asyncio_tag__ = True
    return func


def create_mock_strategy(**overrides) -> Dict[str, Any]:
    """Create a mock strategy with optional overrides"""
    default_strategy = {
        "id": random.randint(1, 1000),
        "user_id": random.randint(1, 100),
        "name": f"Test Strategy {generate_test_id()}",
        "description": "A test strategy for unit testing",
        "strategy_type": "momentum",
        "status": "active",
        "parameters": {
            "timeframe": "1h",
            "risk_level": "medium",
            "max_position": 10000,
            "leverage": 1.0
        },
        "performance": {
            "total_return": 0.15,
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.05,
            "win_rate": 0.65,
            "profit_factor": 1.8
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True
    }

    if overrides:
        default_strategy.update(overrides)

    return default_strategy


def create_mock_user(**overrides) -> Dict[str, Any]:
    """Create a mock user with optional overrides"""
    default_user = {
        "id": random.randint(1, 1000),
        "email": f"test_{generate_test_id()}@example.com",
        "username": f"testuser_{generate_test_id()}",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    if overrides:
        default_user.update(overrides)

    return default_user


def create_mock_batch_result(
    operation: str,
    total: int,
    successful_count: Optional[int] = None,
    failed_count: Optional[int] = None
) -> Dict[str, Any]:
    """Create a mock batch operation result"""
    if successful_count is None:
        successful_count = total
    if failed_count is None:
        failed_count = total - successful_count

    successful = [f"strategy_{i}" for i in range(successful_count)]
    failed = [
        {
            "id": f"strategy_{i}",
            "error": f"Error processing strategy {i}"
        }
        for i in range(successful_count, total)
    ]

    return {
        "operation": operation,
        "total": total,
        "successful": successful,
        "failed": failed,
        "start_time": datetime.utcnow().isoformat(),
        "end_time": datetime.utcnow().isoformat(),
        "duration": random.uniform(1.0, 5.0),
        "progress": successful_count / total if total > 0 else 0
    }


def assert_valid_strategy_response(response_data: Dict[str, Any]) -> None:
    """Assert that strategy response data has valid format"""
    required_fields = [
        "id", "name", "description", "strategy_type",
        "status", "created_at", "updated_at"
    ]

    for field in required_fields:
        assert field in response_data, f"Missing required field: {field}"

    # Validate data types
    assert isinstance(response_data["id"], int)
    assert isinstance(response_data["name"], str)
    assert isinstance(response_data["status"], str)
    assert isinstance(response_data["created_at"], str)
    assert isinstance(response_data["updated_at"], str)


def assert_valid_error_response(error_data: Dict[str, Any]) -> None:
    """Assert that error response has valid format"""
    required_fields = ["detail"]

    for field in required_fields:
        assert field in error_data, f"Missing required error field: {field}"

    assert isinstance(error_data["detail"], str)


def assert_valid_paginated_response(response_data: Dict[str, Any]) -> None:
    """Assert that paginated response has valid format"""
    required_fields = ["items", "total", "page", "page_size"]

    for field in required_fields:
        assert field in response_data, f"Missing required pagination field: {field}"

    assert isinstance(response_data["items"], list)
    assert isinstance(response_data["total"], int)
    assert isinstance(response_data["page"], int)
    assert isinstance(response_data["page_size"], int)
    assert len(response_data["items"]) <= response_data["page_size"]


class AsyncContextManager:
    """Helper for async context management in tests"""

    def __init__(self, async_func):
        self.async_func = async_func
        self.result = None

    async def __aenter__(self):
        self.result = await self.async_func()
        return self.result

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup if needed
        pass


def mock_async_iterable(items: List[Any]):
    """Create a mock async iterable from a list"""
    async def async_iter():
        for item in items:
            yield item

    return async_iter()


class WebSocketMock:
    """Mock WebSocket for testing"""

    def __init__(self):
        self.messages = []
        self.accepted = False
        self.closed = False

    async def accept(self):
        self.accepted = True

    async def send_json(self, data):
        self.messages.append(data)

    async def send_text(self, text):
        self.messages.append({"type": "text", "data": text})

    async def receive_json(self):
        if self.messages:
            return self.messages.pop(0)
        return {"type": "ping"}

    async def close(self):
        self.closed = True


def create_test_event_loop():
    """Create and return a test event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


def run_async_test(test_func, *args, **kwargs):
    """Helper to run async test functions"""
    loop = create_test_event_loop()
    try:
        return loop.run_until_complete(test_func(*args, **kwargs))
    finally:
        loop.close()


# Data generators for testing

def generate_strategies_list(count: int = 10) -> List[Dict[str, Any]]:
    """Generate a list of mock strategies"""
    strategies = []
    strategy_types = ["momentum", "mean_reversion", "arbitrage", "market_making"]
    statuses = ["active", "inactive", "paused", "completed"]

    for i in range(count):
        strategy = create_mock_strategy(
            id=i + 1,
            name=f"Strategy {i + 1}",
            strategy_type=random.choice(strategy_types),
            status=random.choice(statuses)
        )
        strategies.append(strategy)

    return strategies


def generate_performance_metrics() -> Dict[str, float]:
    """Generate realistic performance metrics"""
    return {
        "total_return": round(random.uniform(-0.3, 0.5), 4),
        "sharpe_ratio": round(random.uniform(0.5, 3.0), 2),
        "max_drawdown": round(random.uniform(-0.3, -0.01), 4),
        "win_rate": round(random.uniform(0.4, 0.8), 2),
        "profit_factor": round(random.uniform(1.1, 2.5), 2),
        "sortino_ratio": round(random.uniform(0.7, 3.5), 2),
        "calmar_ratio": round(random.uniform(0.3, 2.0), 2)
    }


def generate_parameters() -> Dict[str, Any]:
    """Generate strategy parameters"""
    return {
        "timeframe": random.choice(["1m", "5m", "15m", "1h", "4h", "1d"]),
        "risk_level": random.choice(["low", "medium", "high"]),
        "max_position": random.randint(1000, 100000),
        "leverage": round(random.uniform(1.0, 5.0), 2),
        "stop_loss": round(random.uniform(0.01, 0.1), 4),
        "take_profit": round(random.uniform(0.02, 0.2), 4)
    }


# Validation helpers

def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Basic JSON schema validation"""
    # This is a simplified validator - in production, use jsonschema library
    required_fields = schema.get("required", [])

    for field in required_fields:
        if field not in data:
            return False

        field_type = schema.get("properties", {}).get(field, {}).get("type")
        if field_type and not isinstance(data[field], eval(field_type.title())):
            return False

    return True


def assert_validation_error_contains(error: Exception, expected_message: str):
    """Assert that validation error contains expected message"""
    error_str = str(error)
    assert expected_message.lower() in error_str.lower(), \
        f"Expected error message '{expected_message}' not found in '{error_str}'"


# Mock response helpers

def create_mock_api_response(
    status_code: int = 200,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
):
    """Create a mock API response"""
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = data or {}
    mock_response.headers = headers or {}
    return mock_response


def create_mock_http_error(status_code: int, detail: str):
    """Create a mock HTTP error"""
    from fastapi import HTTPException
    return HTTPException(status_code=status_code, detail=detail)


# Performance testing helpers

import time
from contextlib import contextmanager


@contextmanager
def measure_performance():
    """Context manager to measure execution time"""
    start_time = time.time()
    yield
    end_time = time.time()
    duration = end_time - start_time
    print(f"Execution time: {duration:.4f} seconds")
    return duration


def assert_performance_under(func, max_seconds: float, *args, **kwargs):
    """Assert that function executes under specified time"""
    with measure_performance() as duration:
        func(*args, **kwargs)

    assert duration < max_seconds, \
        f"Function took {duration:.4f} seconds, expected under {max_seconds}"


# Database testing helpers

def create_test_database_url():
    """Create test database URL"""
    return "sqlite+aiosqlite:///:memory:"


def create_test_redis_url():
    """Create test Redis URL"""
    return "redis://localhost:6379/1"  # Use different DB for tests
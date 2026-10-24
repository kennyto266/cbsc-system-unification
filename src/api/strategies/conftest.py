"""
pytest configuration for strategy API tests
策略API测试的pytest配置

This file contains fixtures and configuration for strategy module tests.
包含策略模块测试的fixtures和配置。
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
import tempfile
import os
from unittest.mock import Mock, AsyncMock

# Import strategy components
from .services.strategy_service import BaseStrategyService
from .repositories.strategy_repository import StrategyRepository
from .repositories.user_repository import UserRepository
from .utils.cache import CacheManager
from .utils.validators import StrategyValidator
from .models import Strategy, User, StrategyType, StrategyStatus
from .schemas import StrategyCreate, StrategyUpdate


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_strategy_repository():
    """Create a mock strategy repository"""
    repo = Mock(spec=StrategyRepository)

    # Mock async methods
    repo.list_strategies = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.name_exists = AsyncMock()
    repo.is_running = AsyncMock()
    repo.get_recent_signals = AsyncMock()
    repo.get_performance = AsyncMock()
    repo.get_execution_history = AsyncMock()
    repo.get_strategy_parameters = AsyncMock()

    return repo


@pytest.fixture
def mock_user_repository():
    """Create a mock user repository"""
    repo = Mock(spec=UserRepository)

    # Mock async methods
    repo.get_by_id = AsyncMock()

    # Create mock user
    mock_user = Mock(spec=User)
    mock_user.id = 1
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user.is_admin = False
    mock_user.is_active = True

    repo.get_by_id.return_value = mock_user

    return repo, mock_user


@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager"""
    cache = Mock(spec=CacheManager)

    # Mock async methods
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.delete_pattern = AsyncMock()

    return cache


@pytest.fixture
def mock_validator():
    """Create a mock validator"""
    validator = Mock(spec=StrategyValidator)

    # Mock async methods
    validator.validate_create_request = AsyncMock()
    validator.validate_update_request = AsyncMock()

    return validator


@pytest.fixture
def strategy_service(mock_strategy_repository, mock_user_repository, mock_cache_manager, mock_validator):
    """Create a strategy service instance with mocked dependencies"""
    user_repo, _ = mock_user_repository

    service = BaseStrategyService(
        strategy_repo=mock_strategy_repository,
        user_repo=user_repo,
        cache_manager=mock_cache_manager,
        validator=mock_validator
    )

    return service


@pytest.fixture
def sample_strategy():
    """Create a sample strategy for testing"""
    return Strategy(
        id="test_strategy_123",
        name="Test RSI Strategy",
        description="Test strategy for RSI trading",
        strategy_type=StrategyType.DIRECT_RSI,
        parameters={
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "stop_loss": 0.05,
            "take_profit": 0.1
        },
        user_id=1,
        status=StrategyStatus.INACTIVE,
        is_active=False,
        risk_level="MEDIUM"
    )


@pytest.fixture
def strategy_create_request():
    """Create a sample strategy creation request"""
    return StrategyCreate(
        name="New Test Strategy",
        description="A new test strategy",
        strategy_type=StrategyType.DIRECT_RSI,
        parameters={
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70
        },
        risk_level="MEDIUM",
        template_id=None
    )


@pytest.fixture
def strategy_update_request():
    """Create a sample strategy update request"""
    return StrategyUpdate(
        name="Updated Strategy Name",
        description="Updated description",
        parameters={
            "rsi_period": 21,
            "rsi_oversold": 25,
            "rsi_overbought": 75
        },
        risk_level="HIGH"
    )


@pytest.fixture
def temp_db_file():
    """Create a temporary database file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
        temp_path = f.name

    yield temp_path

    # Clean up
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass


# Custom pytest markers for strategy testing
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests for strategy components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for strategy API"
    )
    config.addinivalue_line(
        "markers", "performance: Performance tests for strategy operations"
    )
    config.addinivalue_line(
        "markers", "repository: Tests for data repository layer"
    )
    config.addinivalue_line(
        "markers", "service: Tests for business logic layer"
    )
    config.addinivalue_line(
        "markers", "api: Tests for API endpoints"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers dynamically"""
    for item in items:
        # Add markers based on test file/function names
        if "service" in item.nodeid:
            item.add_marker(pytest.mark.service)
        if "repository" in item.nodeid:
            item.add_marker(pytest.mark.repository)
        if "test_api" in item.nodeid or "endpoint" in item.nodeid:
            item.add_marker(pytest.mark.api)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "performance" in item.nodeid or "speed" in item.nodeid:
            item.add_marker(pytest.mark.performance)
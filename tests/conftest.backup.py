"""
Pytest configuration and shared fixtures
"""

import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any, Generator
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock
import json
import tempfile
import os
from pathlib import Path

# FastAPI related
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Database related
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Redis related
import redis.asyncio as redis
from redis.asyncio import Redis

# Project modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.api.main import app
from src.api.strategies.services.enhanced_strategy_service import EnhancedStrategyService
from src.api.strategies.services.enhanced_strategy_service import BatchOperationConfig, BatchOperationType
from src.api.strategies.utils.enhanced_validators import ValidatorFactory
from src.api.strategies.utils.cache import CacheManager
from src.api.strategies.repositories.strategy_repository import StrategyRepository
from src.api.strategies.repositories.user_repository import UserRepository


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db_engine():
    """Create a test database engine"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
    )
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    async_session = sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_strategy_repo():
    """Mock strategy repository"""
    repo = AsyncMock(spec=StrategyRepository)

    # Setup default return values
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_many = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.list = AsyncMock()
    repo.count = AsyncMock()

    return repo


@pytest.fixture
def mock_user_repo():
    """Mock user repository"""
    repo = AsyncMock(spec=UserRepository)

    # Setup default return values
    repo.get_by_id = AsyncMock()
    repo.get_by_email = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()

    return repo


@pytest.fixture
def mock_cache_manager():
    """Mock cache manager"""
    cache = AsyncMock(spec=CacheManager)

    # Setup default return values
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    cache.clear = AsyncMock()
    cache.get_many = AsyncMock(return_value={})
    cache.set_many = AsyncMock()

    return cache


@pytest.fixture
def mock_websocket_service():
    """Mock WebSocket service"""
    ws = AsyncMock()
    ws.broadcast = AsyncMock()
    ws.send_to_user = AsyncMock()
    ws.subscribe = AsyncMock()
    ws.unsubscribe = AsyncMock()

    return ws


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_strategy_data() -> Dict[str, Any]:
    """Sample strategy data for testing"""
    return {
        "id": 1,
        "user_id": 1,
        "name": "Test Strategy",
        "description": "A test strategy for unit testing",
        "strategy_type": "momentum",
        "status": "active",
        "parameters": {
            "timeframe": "1h",
            "risk_level": "medium",
            "max_position": 10000
        },
        "performance": {
            "total_return": 0.15,
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.05
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True
    }


@pytest.fixture
def sample_strategies_data() -> list:
    """Sample list of strategies for testing"""
    return [
        {
            "id": i,
            "user_id": 1,
            "name": f"Strategy {i}",
            "description": f"Test strategy number {i}",
            "strategy_type": "momentum" if i % 2 == 0 else "mean_reversion",
            "status": "active" if i % 3 != 0 else "inactive",
            "parameters": {
                "timeframe": "1h",
                "risk_level": "low" if i % 2 == 0 else "high",
                "max_position": i * 1000
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": i % 2 == 0
        }
        for i in range(1, 6)
    ]


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing"""
    return {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def batch_operation_config() -> BatchOperationConfig:
    """Batch operation configuration fixture"""
    return BatchOperationConfig(
        batch_size=10,
        max_retries=2,
        timeout_per_item=5.0,
        continue_on_error=True
    )


# =============================================================================
# Service Fixtures
# =============================================================================

@pytest.fixture
async def enhanced_strategy_service(
    mock_strategy_repo,
    mock_user_repo,
    mock_cache_manager,
    mock_websocket_service
) -> EnhancedStrategyService:
    """Create enhanced strategy service with mocked dependencies"""
    validator = ValidatorFactory.get_strategy_validator()
    service = EnhancedStrategyService(
        strategy_repo=mock_strategy_repo,
        user_repo=mock_user_repo,
        cache_manager=mock_cache_manager,
        validator=validator,
        websocket_service=mock_websocket_service
    )
    return service


# =============================================================================
# Test Client Fixtures
# =============================================================================

@pytest.fixture
def test_client() -> TestClient:
    """Create FastAPI test client"""
    return TestClient(app)


@pytest.fixture
async def async_test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# =============================================================================
# Authentication Fixtures
# =============================================================================

@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """Mock authentication headers"""
    return {
        "Authorization": "Bearer mock_token",
        "X-API-Key": "mock_api_key"
    }


@pytest.fixture
def mock_current_user(sample_user_data):
    """Mock current user dependency"""
    user_mock = Mock()
    user_mock.id = sample_user_data["id"]
    user_mock.email = sample_user_data["email"]
    user_mock.username = sample_user_data["username"]
    user_mock.is_active = sample_user_data["is_active"]
    user_mock.is_superuser = sample_user_data["is_superuser"]
    return user_mock


# =============================================================================
# Temporary Directory Fixture
# =============================================================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


# =============================================================================
# Redis Fixture (if needed)
# =============================================================================

@pytest.fixture
async def mock_redis():
    """Mock Redis client"""
    redis_mock = AsyncMock(spec=Redis)
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.exists = AsyncMock(return_value=False)
    redis_mock.expire = AsyncMock(return_value=True)
    return redis_mock


# =============================================================================
# Custom Markers
# =============================================================================

def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line(
        "markers", "database: Tests that require database interaction"
    )
    config.addinivalue_line(
        "markers", "cache: Tests that require cache interaction"
    )
    config.addinivalue_line(
        "markers", "websocket: Tests that require WebSocket"
    )
    config.addinivalue_line(
        "markers", "auth: Tests related to authentication"
    )
    config.addinivalue_line(
        "markers", "strategy: Strategy-related tests"
    )
    config.addinivalue_line(
        "markers", "batch: Batch operation tests"
    )
    config.addinivalue_line(
        "markers", "validation: Validation tests"
    )


# =============================================================================
# Hooks
# =============================================================================

@pytest.fixture(autouse=True)
async def cleanup_cache():
    """Cleanup cache after each test"""
    yield
    # Add any cleanup logic here if needed


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("SECRET_KEY", "test_secret_key_for_testing_only")
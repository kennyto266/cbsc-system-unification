"""
Pytest configuration and fixtures for CBSC Trading System tests
"""

import os
import sys
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

# Import application and dependencies
from core.database import get_db, Base
from main import app
from models.user import User
from models.strategy import Strategy


# =============================================================================
# Configuration
# =============================================================================

# Test database URL (in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Environment for testing
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["SECRET_KEY"] = "test-secret-key-for-jwt-tokens"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"


# =============================================================================
# Async Event Loop Configuration
# =============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session


# =============================================================================
# HTTP Client Fixtures
# =============================================================================

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with database override"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()


# =============================================================================
# User Fixtures
# =============================================================================

@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Create test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        is_active=True,
        is_verified=True,
        role="user",
    )
    user.set_password("testpass123")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_strategy(db_session: AsyncSession, test_user: User) -> Strategy:
    """Create test strategy"""
    strategy = Strategy(
        name="Test Strategy",
        description="A test strategy",
        strategy_type="momentum",
        user_id=test_user.id,
        status="active",
        config={
            "short_window": 5,
            "long_window": 20,
            "threshold": 0.02
        },
    )
    db_session.add(strategy)
    await db_session.commit()
    await db_session.refresh(strategy)
    return strategy


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def mock_websocket():
    """Mock WebSocket manager"""
    mock = AsyncMock()
    mock.connect = AsyncMock(return_value=None)
    mock.disconnect = AsyncMock(return_value=None)
    mock.subscribe = Mock(return_value=lambda: None)
    mock.publish = AsyncMock(return_value=None)
    return mock


@pytest.fixture(scope="function")
def mock_cache():
    """Mock cache service"""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.clear = AsyncMock(return_value=True)
    return mock


@pytest.fixture(scope="function")
def mock_event_bus():
    """Mock event bus"""
    mock = AsyncMock()
    mock.publish = AsyncMock(return_value=None)
    mock.subscribe = Mock(return_value=lambda: None)
    mock.unsubscribe = Mock(return_value=None)
    return mock


# =============================================================================
# Pytest Hooks
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "asyncio: Async tests")

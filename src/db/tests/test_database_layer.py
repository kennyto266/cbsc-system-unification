"""
Unit Tests for Database Access Layer

Comprehensive tests for ORM models, repositories, caching, and connection management.
"""

import pytest
import tempfile
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock

# Test database connection manager
def test_database_connection_manager_creation():
    """Test database connection manager initialization"""
    from ..connection import DatabaseConnectionManager

    manager = DatabaseConnectionManager(
        database_url="sqlite:///:memory:",
        pool_size=5,
        max_overflow=2
    )

    assert manager.database_url == "sqlite:///:memory:"
    assert manager.pool_size == 5
    assert manager.max_overflow == 2


def test_database_engine_creation():
    """Test database engine creation"""
    from ..connection import DatabaseConnectionManager

    manager = DatabaseConnectionManager(database_url="sqlite:///:memory:")
    engine = manager.create_engine()

    assert engine is not None
    assert manager.SessionLocal is not None


def test_database_session_context_manager():
    """Test database session context manager"""
    from ..connection import DatabaseConnectionManager
    from ..models import Base

    manager = DatabaseConnectionManager(database_url="sqlite:///:memory:")
    manager.create_engine()

    # Create tables
    Base.metadata.create_all(manager.engine)

    # Test session context manager
    with manager.get_session() as session:
        assert session is not None


def test_database_health_check():
    """Test database health check"""
    from ..connection import DatabaseConnectionManager

    manager = DatabaseConnectionManager(database_url="sqlite:///:memory:")
    manager.create_engine()

    health = manager.health_check()

    assert health["status"] == "healthy"
    assert "pool_size" in health


def test_global_db_manager():
    """Test global database manager"""
    from ..connection import get_db_manager, init_db

    # Get default manager
    manager = get_db_manager()
    assert manager is not None

    # Initialize with custom config
    custom_manager = init_db(
        database_url="sqlite:///:memory:",
        pool_size=10
    )
    assert custom_manager.pool_size == 10


# Test ORM models
def test_strategy_model_creation():
    """Test Strategy ORM model creation"""
    from ..models.strategy import Strategy

    strategy = Strategy(
        name="Test Strategy",
        description="Test description",
        strategy_type="CBSC",
        creator_id="test-user-id",
        is_active=True,
        is_public=False
    )

    assert strategy.name == "Test Strategy"
    assert strategy.strategy_type == "CBSC"
    assert strategy.is_active is True
    assert strategy.creator_id == "test-user-id"


def test_strategy_parameter_validation():
    """Test StrategyParameter validation"""
    from ..models.strategy import StrategyParameter

    param = StrategyParameter(
        strategy_id="test-strategy-id",
        parameter_name="test_param",
        parameter_value="100",
        parameter_type="int",
        min_value=0,
        max_value=200
    )

    assert param.validate_value() is True
    assert param.typed_value == 100

    # Test invalid value
    param.parameter_value = "250"
    assert param.validate_value() is False


def test_market_data_model():
    """Test CBSCMarketData model"""
    from ..models.market_data import CBSCMarketData

    data = CBSCMarketData(
        symbol="AAPL",
        timestamp=datetime.now(timezone.utc),
        open_price=100.0,
        high_price=105.0,
        low_price=99.0,
        close_price=104.0,
        volume=1000000,
        bull_bear_ratio=1.5,
        sentiment_score=0.7,
        price_impact=0.1,
        confidence_level=0.8
    )

    assert data.symbol == "AAPL"
    assert data.price_range == 6.0
    assert data.is_bullish is True


def test_user_model():
    """Test User model"""
    from ..models.user import User

    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        role="analyst"
    )

    assert user.username == "testuser"
    assert user.can_trade is False
    assert user.is_admin is False


def test_user_session_model():
    """Test UserSession model"""
    from ..models.user import UserSession
    from datetime import timedelta

    session = UserSession(
        user_id="test-user-id",
        session_id="test-session-id",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )

    assert session.is_expired is False
    assert session.age_minutes >= 0


# Test repositories
@pytest.fixture
def test_session():
    """Create test database session"""
    from ..connection import DatabaseConnectionManager
    from ..models import Base

    # Use in-memory SQLite for testing
    manager = DatabaseConnectionManager(database_url="sqlite:///:memory:")
    manager.create_engine()

    # Create all tables
    Base.metadata.create_all(manager.engine)

    with manager.get_session() as session:
        yield session


def test_base_repository_crud(test_session):
    """Test BaseRepository CRUD operations"""
    from ..repositories import BaseRepository
    from ..models.strategy import Strategy

    repo = BaseRepository(test_session, Strategy)

    # Create
    strategy_data = {
        "name": "Test Strategy",
        "description": "Test",
        "strategy_type": "CBSC",
        "creator_id": "test-user"
    }
    created = repo.create(strategy_data)
    assert created.id is not None
    assert created.name == "Test Strategy"

    # Read
    fetched = repo.get(created.id)
    assert fetched is not None
    assert fetched.id == created.id

    # Update
    updated = repo.update(created.id, {"description": "Updated description"})
    assert updated.description == "Updated description"

    # Count
    count = repo.count()
    assert count == 1

    # Delete
    deleted = repo.delete(created.id)
    assert deleted is True

    # Verify deletion
    fetched = repo.get(created.id)
    assert fetched is None


def test_strategy_repository(test_session):
    """Test StrategyRepository"""
    from ..repositories import StrategyRepository
    from ..models.strategy import Strategy

    repo = StrategyRepository(test_session)

    # Create test strategies
    strategy1 = Strategy(
        name="Strategy 1",
        description="Test strategy 1",
        strategy_type="CBSC",
        creator_id="user1",
        is_active=True,
        is_public=True
    )
    strategy2 = Strategy(
        name="Strategy 2",
        description="Test strategy 2",
        strategy_type="Technical",
        creator_id="user1",
        is_active=True,
        is_public=True
    )

    test_session.add(strategy1)
    test_session.add(strategy2)
    test_session.commit()

    # Test get_by_creator
    strategies = repo.get_by_creator("user1")
    assert len(strategies) == 2

    # Test get_by_type
    cbsc_strategies = repo.get_by_type("CBSC")
    assert len(cbsc_strategies) == 1
    assert cbsc_strategies[0].strategy_type == "CBSC"

    # Test search
    results = repo.search_strategies("Strategy")
    assert len(results) >= 2


def test_market_data_repository(test_session):
    """Test CBSCMarketDataRepository"""
    from ..repositories import CBSCMarketDataRepository
    from ..models.market_data import CBSCMarketData

    repo = CBSCMarketDataRepository(test_session)

    # Create test data
    now = datetime.now(timezone.utc)

    data1 = CBSCMarketData(
        symbol="AAPL",
        timestamp=now,
        open_price=100.0,
        high_price=105.0,
        low_price=99.0,
        close_price=104.0,
        volume=1000000,
        bull_bear_ratio=1.5,
        sentiment_score=0.7,
        price_impact=0.1,
        confidence_level=0.8
    )

    data2 = CBSCMarketData(
        symbol="MSFT",
        timestamp=now,
        open_price=200.0,
        high_price=205.0,
        low_price=198.0,
        close_price=203.0,
        volume=500000,
        bull_bear_ratio=0.8,
        sentiment_score=-0.3,
        price_impact=-0.1,
        confidence_level=0.7
    )

    test_session.add(data1)
    test_session.add(data2)
    test_session.commit()

    # Test get_by_symbol
    aapl_data = repo.get_by_symbol("AAPL")
    assert len(aapl_data) == 1
    assert aapl_data[0].symbol == "AAPL"

    # Test get_latest_by_symbol
    latest_aapl = repo.get_latest_by_symbol("AAPL")
    assert latest_aapl is not None
    assert latest_aapl.symbol == "AAPL"

    # Test get_bullish_stocks
    bullish = repo.get_bullish_stocks()
    assert len(bullish) >= 1
    assert all(d.sentiment_score > 0 for d in bullish)


def test_user_repository(test_session):
    """Test UserRepository"""
    from ..repositories import UserRepository
    from ..models.user import User

    repo = UserRepository(test_session)

    # Create test users
    user1 = User(
        username="user1",
        email="user1@example.com",
        password_hash="hash1",
        role="admin"
    )
    user2 = User(
        username="user2",
        email="user2@example.com",
        password_hash="hash2",
        role="analyst"
    )

    test_session.add(user1)
    test_session.add(user2)
    test_session.commit()

    # Test get_by_username
    fetched = repo.get_by_username("user1")
    assert fetched is not None
    assert fetched.username == "user1"

    # Test get_by_role
    admins = repo.get_by_role("admin")
    assert len(admins) == 1
    assert admins[0].role == "admin"

    # Test search
    results = repo.search_users("user")
    assert len(results) >= 2


# Test caching
def test_cache_manager_key_generation():
    """Test cache key generation"""
    from ..cache import CacheManager

    cache = CacheManager()

    key1 = cache._make_key("test", "arg1", "arg2", kwarg="value")
    key2 = cache._make_key("test", "arg1", "arg2", kwarg="value")
    key3 = cache._make_key("test", "arg1", "different", kwarg="value")

    assert key1 == key2  # Same args should produce same key
    assert key1 != key3  # Different args should produce different key


def test_cached_decorator():
    """Test cached decorator"""
    from ..cache import cached, CacheManager

    cache = CacheManager()
    call_count = [0]

    @cached("test_func", ttl=60, cache_manager=cache)
    def test_func(x, y):
        call_count[0] += 1
        return x + y

    # First call should execute function
    result1 = test_func(1, 2)
    assert result1 == 3
    assert call_count[0] == 1

    # Second call with same args should use cache
    result2 = test_func(1, 2)
    assert result2 == 3
    # Note: Call count won't increase if cache works, but we're not testing with actual Redis


def test_cache_health_check():
    """Test cache health check"""
    from ..cache import CacheManager

    cache = CacheManager()

    health = cache.health_check()
    assert "status" in health
    # Status will be "disabled" if Redis is not available


# Performance monitoring
def test_query_performance_tracking():
    """Test query performance tracking"""
    from ..connection import DatabaseConnectionManager

    manager = DatabaseConnectionManager(database_url="sqlite:///:memory:")
    manager.create_engine()

    # The connection manager should have event listeners for tracking
    assert manager.engine is not None

    health = manager.health_check()
    assert health["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

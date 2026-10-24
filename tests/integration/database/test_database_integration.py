"""Integration tests for database operations."""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import models
from src.models.strategy import Strategy
from src.models.user import User
from src.models.portfolio import Portfolio
from src.models.trade import Trade
from src.database import Base, get_db


# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create test database session."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create test user."""
    from src.core.security import get_password_hash
    
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def sample_strategy(db_session, test_user):
    """Create sample strategy."""
    strategy = Strategy(
        name="Test Strategy",
        description="A test strategy for database integration",
        user_id=test_user.id,
        parameters={
            "symbols": ["AAPL", "GOOGL"],
            "timeframe": "1d",
            "risk_level": 0.02
        },
        status="active",
        performance_metrics={
            "total_return": 0.15,
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.08
        }
    )
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)
    return strategy


@pytest.fixture(scope="function")
def sample_portfolio(db_session, test_user):
    """Create sample portfolio."""
    portfolio = Portfolio(
        name="Test Portfolio",
        user_id=test_user.id,
        total_value=100000.0,
        cash_balance=50000.0,
        positions=[
            {
                "symbol": "AAPL",
                "quantity": 100,
                "avg_cost": 150.0,
                "current_price": 155.0,
                "market_value": 15500.0,
                "unrealized_pnl": 500.0
            },
            {
                "symbol": "GOOGL",
                "quantity": 10,
                "avg_cost": 2800.0,
                "current_price": 2850.0,
                "market_value": 28500.0,
                "unrealized_pnl": 500.0
            }
        ]
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)
    return portfolio


@pytest.fixture(scope="function")
def sample_trades(db_session, test_user, sample_strategy, sample_portfolio):
    """Create sample trades."""
    trades = []
    
    # Create some sample trades
    trade_data = [
        {
            "symbol": "AAPL",
            "type": "buy",
            "quantity": 100,
            "price": 150.0,
            "timestamp": datetime.utcnow() - timedelta(days=1)
        },
        {
            "symbol": "GOOGL",
            "type": "buy",
            "quantity": 10,
            "price": 2800.0,
            "timestamp": datetime.utcnow() - timedelta(days=2)
        },
        {
            "symbol": "AAPL",
            "type": "sell",
            "quantity": 50,
            "price": 155.0,
            "timestamp": datetime.utcnow() - timedelta(hours=12)
        }
    ]
    
    for trade_info in trade_data:
        trade = Trade(
            user_id=test_user.id,
            strategy_id=sample_strategy.id,
            portfolio_id=sample_portfolio.id,
            symbol=trade_info["symbol"],
            type=trade_info["type"],
            quantity=trade_info["quantity"],
            price=trade_info["price"],
            timestamp=trade_info["timestamp"]
        )
        db_session.add(trade)
        trades.append(trade)
    
    db_session.commit()
    
    for trade in trades:
        db_session.refresh(trade)
    
    return trades


@pytest.mark.integration
class TestDatabaseIntegration:
    """Test database integration."""

    def test_user_crud_operations(self, db_session):
        """Test user CRUD operations."""
        # Create user
        from src.core.security import get_password_hash
        
        user = User(
            username="newuser",
            email="newuser@example.com",
            hashed_password=get_password_hash("newpassword"),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Read user
        retrieved_user = db_session.query(User).filter(User.username == "newuser").first()
        assert retrieved_user is not None
        assert retrieved_user.email == "newuser@example.com"
        
        # Update user
        retrieved_user.is_active = False
        db_session.commit()
        
        updated_user = db_session.query(User).filter(User.username == "newuser").first()
        assert updated_user.is_active is False
        
        # Delete user
        db_session.delete(updated_user)
        db_session.commit()
        
        deleted_user = db_session.query(User).filter(User.username == "newuser").first()
        assert deleted_user is None

    def test_strategy_crud_operations(self, db_session, test_user):
        """Test strategy CRUD operations."""
        # Create strategy
        strategy = Strategy(
            name="CRUD Test Strategy",
            description="Testing CRUD operations",
            user_id=test_user.id,
            parameters={"symbols": ["MSFT"], "timeframe": "1h"},
            status="inactive"
        )
        db_session.add(strategy)
        db_session.commit()
        
        # Read strategy
        retrieved = db_session.query(Strategy).filter(Strategy.name == "CRUD Test Strategy").first()
        assert retrieved is not None
        assert retrieved.status == "inactive"
        
        # Update strategy
        retrieved.status = "active"
        retrieved.performance_metrics = {"total_return": 0.10}
        db_session.commit()
        
        updated = db_session.query(Strategy).filter(Strategy.name == "CRUD Test Strategy").first()
        assert updated.status == "active"
        assert updated.performance_metrics["total_return"] == 0.10
        
        # Delete strategy
        db_session.delete(updated)
        db_session.commit()
        
        deleted = db_session.query(Strategy).filter(Strategy.name == "CRUD Test Strategy").first()
        assert deleted is None

    def test_portfolio_crud_operations(self, db_session, test_user):
        """Test portfolio CRUD operations."""
        # Create portfolio
        portfolio = Portfolio(
            name="CRUD Test Portfolio",
            user_id=test_user.id,
            total_value=200000.0,
            cash_balance=100000.0
        )
        db_session.add(portfolio)
        db_session.commit()
        
        # Read portfolio
        retrieved = db_session.query(Portfolio).filter(Portfolio.name == "CRUD Test Portfolio").first()
        assert retrieved is not None
        assert retrieved.total_value == 200000.0
        
        # Update portfolio
        retrieved.total_value = 210000.0
        retrieved.positions = [
            {
                "symbol": "TSLA",
                "quantity": 50,
                "avg_cost": 800.0,
                "current_price": 850.0,
                "market_value": 42500.0,
                "unrealized_pnl": 2500.0
            }
        ]
        db_session.commit()
        
        updated = db_session.query(Portfolio).filter(Portfolio.name == "CRUD Test Portfolio").first()
        assert updated.total_value == 210000.0
        assert len(updated.positions) == 1
        assert updated.positions[0]["symbol"] == "TSLA"
        
        # Delete portfolio
        db_session.delete(updated)
        db_session.commit()
        
        deleted = db_session.query(Portfolio).filter(Portfolio.name == "CRUD Test Portfolio").first()
        assert deleted is None

    def test_trade_crud_operations(self, db_session, test_user, sample_strategy, sample_portfolio):
        """Test trade CRUD operations."""
        # Create trade
        trade = Trade(
            user_id=test_user.id,
            strategy_id=sample_strategy.id,
            portfolio_id=sample_portfolio.id,
            symbol="AMZN",
            type="buy",
            quantity=20,
            price=3200.0,
            timestamp=datetime.utcnow()
        )
        db_session.add(trade)
        db_session.commit()
        
        # Read trade
        retrieved = db_session.query(Trade).filter(Trade.symbol == "AMZN").first()
        assert retrieved is not None
        assert retrieved.type == "buy"
        assert retrieved.quantity == 20
        
        # Update trade (typically trades are immutable, but we can test for status updates)
        retrieved.status = "executed"
        db_session.commit()
        
        updated = db_session.query(Trade).filter(Trade.symbol == "AMZN").first()
        assert updated.status == "executed"
        
        # Delete trade (soft delete by status)
        updated.status = "cancelled"
        db_session.commit()
        
        cancelled = db_session.query(Trade).filter(Trade.symbol == "AMZN").first()
        assert cancelled.status == "cancelled"

    def test_relationship_operations(self, db_session, test_user, sample_strategy):
        """Test database relationship operations."""
        # Create multiple strategies for the user
        strategies = []
        for i in range(3):
            strategy = Strategy(
                name=f"Strategy {i}",
                description=f"Strategy number {i}",
                user_id=test_user.id,
                parameters={"symbols": ["AAPL"], "timeframe": "1d"},
                status="active"
            )
            db_session.add(strategy)
            strategies.append(strategy)
        
        db_session.commit()
        
        # Test one-to-many relationship
        user_strategies = db_session.query(Strategy).filter(Strategy.user_id == test_user.id).all()
        assert len(user_strategies) >= 4  # 3 new + 1 from fixture
        
        # Test cascade delete
        db_session.delete(test_user)
        db_session.commit()
        
        orphaned_strategies = db_session.query(Strategy).filter(
            Strategy.user_id == test_user.id
        ).all()
        assert len(orphaned_strategies) == 0

    def test_transaction_rollback(self, db_session, test_user):
        """Test transaction rollback on error."""
        # Create initial strategy
        strategy = Strategy(
            name="Initial Strategy",
            description="Should survive rollback",
            user_id=test_user.id,
            parameters={"symbols": ["AAPL"]},
            status="active"
        )
        db_session.add(strategy)
        db_session.commit()
        
        # Start a new transaction that will fail
        try:
            # Create another strategy
            strategy2 = Strategy(
                name="Will be rolled back",
                description="This should not persist",
                user_id=test_user.id,
                parameters={"symbols": ["GOOGL"]},
                status="active"
            )
            db_session.add(strategy2)
            
            # Simulate an error
            raise ValueError("Simulated error")
            
        except ValueError:
            db_session.rollback()
        
        # Check that only the initial strategy exists
        strategies = db_session.query(Strategy).filter(Strategy.user_id == test_user.id).all()
        assert len(strategies) == 1
        assert strategies[0].name == "Initial Strategy"

    def test_query_performance(self, db_session, test_user):
        """Test query performance with indexes."""
        import time
        
        # Create many strategies
        strategies = []
        for i in range(1000):
            strategy = Strategy(
                name=f"Performance Test {i}",
                description=f"Strategy {i} for performance testing",
                user_id=test_user.id,
                parameters={"symbols": ["AAPL"]},
                status="active" if i % 2 == 0 else "inactive"
            )
            strategies.append(strategy)
        
        db_session.add_all(strategies)
        db_session.commit()
        
        # Test query performance
        start_time = time.time()
        
        # Query with filter
        active_strategies = db_session.query(Strategy).filter(
            Strategy.user_id == test_user.id,
            Strategy.status == "active"
        ).all()
        
        query_time = time.time() - start_time
        
        # Assertions
        assert len(active_strategies) == 500
        assert query_time < 0.1, f"Query took too long: {query_time} seconds"

    def test_json_field_operations(self, db_session, test_user):
        """Test JSON field operations."""
        strategy = Strategy(
            name="JSON Test Strategy",
            user_id=test_user.id,
            parameters={
                "symbols": ["AAPL", "GOOGL", "MSFT"],
                "timeframe": "1d",
                "risk_level": 0.02,
                "nested": {
                    "level1": {
                        "level2": "deep value"
                    }
                }
            },
            performance_metrics={
                "total_return": 0.15,
                "metrics_by_year": {
                    "2022": 0.10,
                    "2023": 0.05
                }
            }
        )
        db_session.add(strategy)
        db_session.commit()
        
        # Query nested JSON values
        retrieved = db_session.query(Strategy).filter(
            Strategy.parameters["nested"]["level1"]["level2"].astext == "deep value"
        ).first()
        
        assert retrieved is not None
        assert retrieved.parameters["symbols"] == ["AAPL", "GOOGL", "MSFT"]
        
        # Update JSON field
        retrieved.parameters["new_field"] = "new value"
        db_session.commit()
        
        updated = db_session.query(Strategy).filter(
            Strategy.parameters["new_field"].astext == "new value"
        ).first()
        
        assert updated is not None
        assert updated.parameters["new_field"] == "new value"

    def test_concurrent_operations(self, db_session, test_user):
        """Test concurrent database operations."""
        import threading
        import time
        
        results = []
        errors = []
        
        def create_strategy(index):
            try:
                # Use separate session for each thread
                session = TestingSessionLocal()
                strategy = Strategy(
                    name=f"Concurrent Strategy {index}",
                    description=f"Created in thread {index}",
                    user_id=test_user.id,
                    parameters={"symbols": ["AAPL"]},
                    status="active"
                )
                session.add(strategy)
                session.commit()
                results.append(index)
                session.close()
            except Exception as e:
                errors.append((index, e))
        
        # Create strategies concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_strategy, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10, f"Expected 10 results, got {len(results)}"
        
        # Verify all strategies were created
        strategies = db_session.query(Strategy).filter(
            Strategy.name.like("Concurrent Strategy%")
        ).all()
        assert len(strategies) == 10

    def test_database_constraints(self, db_session, test_user):
        """Test database constraints."""
        # Create a strategy
        strategy1 = Strategy(
            name="Unique Name",
            user_id=test_user.id,
            parameters={"symbols": ["AAPL"]},
            status="active"
        )
        db_session.add(strategy1)
        db_session.commit()
        
        # Try to create another with the same name for the same user
        strategy2 = Strategy(
            name="Unique Name",  # Same name
            user_id=test_user.id,  # Same user
            parameters={"symbols": ["GOOGL"]},
            status="active"
        )
        
        db_session.add(strategy2)
        
        # This should raise an integrity error due to unique constraint
        with pytest.raises(Exception):  # Could be IntegrityError or similar
            db_session.commit()
        
        db_session.rollback()

    def test_database_connection_pooling(self):
        """Test database connection pooling."""
        from sqlalchemy import text
        
        # Create multiple concurrent connections
        connections = []
        for _ in range(10):
            conn = engine.connect()
            connections.append(conn)
        
        # Execute queries on all connections
        for conn in connections:
            result = conn.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
        
        # Close all connections
        for conn in connections:
            conn.close()
        
        # Verify pool is working
        assert engine.pool.size() >= 10
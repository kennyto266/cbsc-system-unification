"""Integration tests for Strategy API endpoints."""

import pytest
import asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import application
from src.api.main import app
from src.database import get_db
from src.models.strategy import Strategy
from src.models.user import User
from src.core.security import get_password_hash


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Create test database tables."""
    Strategy.metadata.create_all(bind=engine)
    User.metadata.create_all(bind=engine)
    yield
    Strategy.metadata.drop_all(bind=engine)
    User.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_user(test_db):
    """Create test user."""
    db = TestingSessionLocal()
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_superuser=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Get authorization headers."""
    response = client.post(
        "/auth/token",
        data={"username": "testuser", "password": "testpassword"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestStrategyAPI:
    """Test Strategy API endpoints."""

    def test_create_strategy_success(self, test_db, auth_headers):
        """Test successful strategy creation."""
        strategy_data = {
            "name": "Test Strategy",
            "description": "A test strategy for integration testing",
            "parameters": {
                "symbols": ["AAPL", "GOOGL"],
                "timeframe": "1d",
                "risk_level": 0.02
            },
            "status": "inactive"
        }
        
        response = client.post(
            "/api/strategies",
            json=strategy_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == strategy_data["name"]
        assert data["data"]["status"] == strategy_data["status"]
        assert "id" in data["data"]
        assert "created_at" in data["data"]

    def test_create_strategy_validation_error(self, test_db, auth_headers):
        """Test strategy creation with invalid data."""
        invalid_data = {
            "name": "",  # Empty name should fail validation
            "parameters": {}
        }
        
        response = client.post(
            "/api/strategies",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_get_strategies_list(self, test_db, auth_headers, test_user):
        """Test getting list of strategies."""
        # Create a few test strategies
        db = TestingSessionLocal()
        for i in range(5):
            strategy = Strategy(
                name=f"Strategy {i}",
                description=f"Test strategy {i}",
                user_id=test_user.id,
                parameters={"symbols": ["AAPL"], "timeframe": "1d"},
                status="active"
            )
            db.add(strategy)
        db.commit()
        db.close()
        
        response = client.get("/api/strategies", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["strategies"]) >= 5
        assert "pagination" in data["data"]

    def test_get_strategy_by_id(self, test_db, auth_headers, test_user):
        """Test getting a specific strategy by ID."""
        # Create a test strategy
        db = TestingSessionLocal()
        strategy = Strategy(
            name="Test Strategy",
            description="Test description",
            user_id=test_user.id,
            parameters={"symbols": ["AAPL"], "timeframe": "1d"},
            status="active"
        )
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        strategy_id = strategy.id
        db.close()
        
        response = client.get(f"/api/strategies/{strategy_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == strategy_id
        assert data["data"]["name"] == "Test Strategy"

    def test_get_strategy_not_found(self, test_db, auth_headers):
        """Test getting a non-existent strategy."""
        response = client.get("/api/strategies/99999", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"]["message"].lower()

    def test_update_strategy(self, test_db, auth_headers, test_user):
        """Test updating a strategy."""
        # Create a test strategy
        db = TestingSessionLocal()
        strategy = Strategy(
            name="Original Name",
            description="Original description",
            user_id=test_user.id,
            parameters={"symbols": ["AAPL"], "timeframe": "1d"},
            status="inactive"
        )
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        strategy_id = strategy.id
        db.close()
        
        update_data = {
            "name": "Updated Name",
            "description": "Updated description",
            "status": "active"
        }
        
        response = client.put(
            f"/api/strategies/{strategy_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == update_data["name"]
        assert data["data"]["description"] == update_data["description"]
        assert data["data"]["status"] == update_data["status"]

    def test_delete_strategy(self, test_db, auth_headers, test_user):
        """Test deleting a strategy."""
        # Create a test strategy
        db = TestingSessionLocal()
        strategy = Strategy(
            name="To Delete",
            description="This will be deleted",
            user_id=test_user.id,
            parameters={"symbols": ["AAPL"], "timeframe": "1d"},
            status="inactive"
        )
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        strategy_id = strategy.id
        db.close()
        
        response = client.delete(f"/api/strategies/{strategy_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify deletion
        response = client.get(f"/api/strategies/{strategy_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_get_strategy_performance(self, test_db, auth_headers, test_user):
        """Test getting strategy performance metrics."""
        # Create a test strategy
        db = TestingSessionLocal()
        strategy = Strategy(
            name="Performance Test",
            description="Testing performance metrics",
            user_id=test_user.id,
            parameters={"symbols": ["AAPL"], "timeframe": "1d"},
            status="active",
            performance_metrics={
                "total_return": 0.15,
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.08,
                "win_rate": 0.55
            }
        )
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        strategy_id = strategy.id
        db.close()
        
        response = client.get(
            f"/api/strategies/{strategy_id}/performance",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "metrics" in data["data"]
        assert data["data"]["metrics"]["total_return"] == 0.15

    def test_run_backtest(self, test_db, auth_headers, test_user):
        """Test running a backtest for a strategy."""
        # Create a test strategy
        db = TestingSessionLocal()
        strategy = Strategy(
            name="Backtest Test",
            description="Testing backtest execution",
            user_id=test_user.id,
            parameters={"symbols": ["AAPL"], "timeframe": "1d"},
            status="active"
        )
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        strategy_id = strategy.id
        db.close()
        
        backtest_request = {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_capital": 100000
        }
        
        response = client.post(
            f"/api/strategies/{strategy_id}/backtest",
            json=backtest_request,
            headers=auth_headers
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["success"] is True
        assert "backtest_id" in data["data"]
        assert data["data"]["status"] == "pending"

    def test_get_backtest_results(self, test_db, auth_headers):
        """Test getting backtest results."""
        backtest_id = "bt-test-123"
        
        # Mock backtest results
        response = client.get(
            f"/api/backtest/{backtest_id}",
            headers=auth_headers
        )
        
        # This would normally query the database for results
        # For integration test, we expect either results or "not found"
        assert response.status_code in [200, 404]

    @pytest.mark.parametrize("status_filter,expected_count", [
        ("active", 3),
        ("inactive", 2),
        ("all", 5)
    ])
    def test_filter_strategies_by_status(
        self, test_db, auth_headers, test_user, status_filter, expected_count
    ):
        """Test filtering strategies by status."""
        # Create test strategies with different statuses
        db = TestingSessionLocal()
        for i in range(3):
            strategy = Strategy(
                name=f"Active Strategy {i}",
                description=f"Active test strategy {i}",
                user_id=test_user.id,
                parameters={"symbols": ["AAPL"], "timeframe": "1d"},
                status="active"
            )
            db.add(strategy)
        
        for i in range(2):
            strategy = Strategy(
                name=f"Inactive Strategy {i}",
                description=f"Inactive test strategy {i}",
                user_id=test_user.id,
                parameters={"symbols": ["GOOGL"], "timeframe": "1d"},
                status="inactive"
            )
            db.add(strategy)
        
        db.commit()
        db.close()
        
        params = {"status": status_filter} if status_filter != "all" else {}
        response = client.get("/api/strategies", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["strategies"]) >= expected_count

    def test_search_strategies_by_name(self, test_db, auth_headers, test_user):
        """Test searching strategies by name."""
        # Create test strategies
        db = TestingSessionLocal()
        search_term = "Special"
        
        # Create strategies with and without the search term
        for i in range(3):
            strategy = Strategy(
                name=f"{search_term} Strategy {i}",
                description=f"Strategy with search term {i}",
                user_id=test_user.id,
                parameters={"symbols": ["AAPL"], "timeframe": "1d"},
                status="active"
            )
            db.add(strategy)
        
        for i in range(2):
            strategy = Strategy(
                name=f"Regular Strategy {i}",
                description=f"Regular strategy {i}",
                user_id=test_user.id,
                parameters={"symbols": ["GOOGL"], "timeframe": "1d"},
                status="active"
            )
            db.add(strategy)
        
        db.commit()
        db.close()
        
        response = client.get(
            "/api/strategies",
            params={"search": search_term},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # All returned strategies should contain the search term
        for strategy in data["data"]["strategies"]:
            assert search_term in strategy["name"]

    def test_unauthorized_access(self, test_db):
        """Test that unauthorized requests are rejected."""
        response = client.get("/api/strategies")
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    def test_rate_limiting(self, test_db, auth_headers):
        """Test rate limiting on API endpoints."""
        # Make multiple rapid requests
        responses = []
        for _ in range(100):
            response = client.get("/api/strategies", headers=auth_headers)
            responses.append(response)
            if response.status_code == 429:
                break
        
        # Should eventually hit rate limit
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "Rate limiting should be enforced"

    @pytest.mark.slow
    def test_concurrent_strategy_creation(self, test_db, auth_headers):
        """Test creating multiple strategies concurrently."""
        import concurrent.futures
        
        def create_strategy(index):
            strategy_data = {
                "name": f"Concurrent Strategy {index}",
                "description": f"Created concurrently {index}",
                "parameters": {"symbols": ["AAPL"], "timeframe": "1d"},
                "status": "inactive"
            }
            response = client.post(
                "/api/strategies",
                json=strategy_data,
                headers=auth_headers
            )
            return response
        
        # Create 10 strategies concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_strategy, i) for i in range(10)]
            responses = [f.result() for f in futures]
        
        # All should succeed
        success_count = sum(1 for r in responses if r.status_code == 201)
        assert success_count == 10, f"Expected 10 successes, got {success_count}"
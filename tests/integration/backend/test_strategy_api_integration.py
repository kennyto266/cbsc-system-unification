"""
Strategy API Integration Tests
Tests backend API integration with database and external services
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Import the FastAPI app
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.api.main import app
from src.db.database import get_db, Base
from src.db.models import Strategy, StrategyParameter, StrategyPerformance
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def client():
    """Create test client"""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="function")
async def async_client():
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture(scope="function")
def test_db():
    """Setup test database with sample data"""
    db = TestingSessionLocal()

    # Create test strategies
    strategy1 = Strategy(
        name="Test Moving Average",
        description="Test MA crossover strategy",
        status="active",
        parameters={
            "short_period": 10,
            "long_period": 20,
            "symbol": "BTC/USDT"
        },
        created_by="test_user"
    )

    strategy2 = Strategy(
        name="Test RSI Strategy",
        description="Test RSI strategy",
        status="inactive",
        parameters={
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "symbol": "ETH/USDT"
        },
        created_by="test_user"
    )

    db.add_all([strategy1, strategy2])
    db.commit()

    yield db

    # Cleanup
    db.query(Strategy).delete()
    db.query(StrategyParameter).delete()
    db.query(StrategyPerformance).delete()
    db.commit()
    db.close()

class TestStrategyAPIIntegration:
    """Test Strategy API Integration"""

    def test_get_strategies_integration(self, client, test_db):
        """Test GET /api/strategies with database integration"""
        response = client.get("/api/strategies")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data
        assert "items" in data["data"]
        assert len(data["data"]["items"]) == 2

        # Verify strategy data
        strategy1 = data["data"]["items"][0]
        assert strategy1["name"] == "Test Moving Average"
        assert strategy1["status"] == "active"
        assert strategy1["parameters"]["short_period"] == 10

    def test_create_strategy_integration(self, client, test_db):
        """Test POST /api/strategies with database integration"""
        strategy_data = {
            "name": "Integration Test Strategy",
            "description": "Created from integration test",
            "parameters": {
                "test_param": "test_value",
                "another_param": 123
            },
            "status": "draft"
        }

        response = client.post("/api/strategies", json=strategy_data)

        assert response.status_code == 201
        data = response.json()

        assert data["success"] is True
        assert data["data"]["name"] == "Integration Test Strategy"
        assert data["data"]["status"] == "draft"

        # Verify in database
        db_strategy = test_db.query(Strategy).filter(
            Strategy.name == "Integration Test Strategy"
        ).first()

        assert db_strategy is not None
        assert db_strategy.description == "Created from integration test"

    def test_update_strategy_integration(self, client, test_db):
        """Test PUT /api/strategies/{id} with database integration"""
        # Get existing strategy
        strategy = test_db.query(Strategy).first()
        strategy_id = strategy.id

        update_data = {
            "name": "Updated Integration Strategy",
            "description": "Updated from integration test",
            "parameters": {
                "updated_param": "new_value"
            },
            "status": "active"
        }

        response = client.put(f"/api/strategies/{strategy_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["data"]["name"] == "Updated Integration Strategy"

        # Verify in database
        test_db.refresh(strategy)
        assert strategy.name == "Updated Integration Strategy"
        assert strategy.status == "active"

    def test_delete_strategy_integration(self, client, test_db):
        """Test DELETE /api/strategies/{id} with database integration"""
        # Create strategy to delete
        strategy = Strategy(
            name="Strategy to Delete",
            description="Will be deleted",
            status="inactive",
            parameters={},
            created_by="test_user"
        )
        test_db.add(strategy)
        test_db.commit()

        strategy_id = strategy.id

        response = client.delete(f"/api/strategies/{strategy_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True

        # Verify deletion in database
        deleted_strategy = test_db.query(Strategy).filter(
            Strategy.id == strategy_id
        ).first()

        assert deleted_strategy is None

    def test_strategy_performance_integration(self, client, test_db):
        """Test GET /api/strategies/{id}/performance with calculation"""
        strategy = test_db.query(Strategy).first()
        strategy_id = strategy.id

        # Add performance data
        performance = StrategyPerformance(
            strategy_id=strategy_id,
            date=datetime.now().date(),
            total_return=15.5,
            sharpe_ratio=1.85,
            max_drawdown=-8.2,
            win_rate=0.65,
            profit_factor=1.8,
            total_trades=125,
            profitable_trades=81,
            losing_trades=44
        )
        test_db.add(performance)
        test_db.commit()

        response = client.get(f"/api/strategies/{strategy_id}/performance")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["data"]["total_return"] == 15.5
        assert data["data"]["sharpe_ratio"] == 1.85
        assert data["data"]["win_rate"] == 0.65

class TestWebSocketIntegration:
    """Test WebSocket integration"""

    @pytest.mark.asyncio
    async def test_realtime_strategy_updates(self, async_client, test_db):
        """Test WebSocket real-time strategy updates"""
        strategy = test_db.query(Strategy).first()

        # Mock WebSocket connection
        with patch('src.api.websocket.websocket_manager.broadcast') as mock_broadcast:
            # Update strategy
            update_data = {
                "status": "running",
                "last_signal": "BUY"
            }

            response = await async_client.put(
                f"/api/strategies/{strategy.id}",
                json=update_data
            )

            assert response.status_code == 200

            # Verify WebSocket broadcast was called
            mock_broadcast.assert_called_once()

            # Check broadcast message
            call_args = mock_broadcast.call_args[0]
            message = json.loads(call_args[0])

            assert message["type"] == "STRATEGY_UPDATE"
            assert message["data"]["strategy_id"] == strategy.id
            assert message["data"]["status"] == "running"

    @pytest.mark.asyncio
    async def test_market_data_websocket(self, async_client):
        """Test market data WebSocket integration"""
        # Mock external market data service
        mock_market_data = {
            "symbol": "BTC/USDT",
            "price": 50000.0,
            "volume": 1000000,
            "timestamp": datetime.now().isoformat()
        }

        with patch('src.services.market_data_service.get_real_time_price') as mock_price:
            mock_price.return_value = mock_market_data

            response = await async_client.get("/api/market/data/BTC/USDT")

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["data"]["price"] == 50000.0

class TestExternalAPIIntegration:
    """Test integration with external APIs"""

    @patch('src.services.binance_service.get_historical_klines')
    def test_binance_api_integration(self, mock_klines, client, test_db):
        """Test Binance API integration"""
        # Mock Binance response
        mock_klines.return_value = [
            [1609459200000, "50000.0", "50500.0", "49500.0", "50250.0", "1000"],
            [1609459260000, "50250.0", "50750.0", "49750.0", "50500.0", "1100"],
        ]

        response = client.get("/api/external/binance/klines?symbol=BTCUSDT&interval=1h")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["data"][0][4] == "50250.0"

    @patch('src.services.news_service.get_market_news')
    def test_news_api_integration(self, mock_news, client):
        """Test news API integration"""
        # Mock news response
        mock_news.return_value = [
            {
                "title": "Bitcoin Hits New High",
                "description": "BTC reaches new all-time high",
                "url": "https://example.com/news1",
                "published_at": datetime.now().isoformat()
            }
        ]

        response = client.get("/api/external/news?category=crypto")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert len(data["data"]) == 1
        assert "Bitcoin Hits New High" in data["data"][0]["title"]

class TestErrorHandlingIntegration:
    """Test error handling in integration scenarios"""

    def test_database_connection_error(self, client):
        """Test handling of database connection errors"""
        with patch('src.db.database.get_db') as mock_get_db:
            # Simulate database error
            mock_get_db.side_effect = Exception("Database connection failed")

            response = client.get("/api/strategies")

            # Should return 500 error
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False

    def test_external_api_timeout(self, client):
        """Test handling of external API timeouts"""
        with patch('src.services.binance_service.get_historical_klines') as mock_klines:
            # Simulate timeout
            mock_klines.side_effect = asyncio.TimeoutError("Request timeout")

            response = client.get("/api/external/binance/klines?symbol=BTCUSDT&interval=1h")

            # Should handle gracefully
            assert response.status_code in [500, 504]
            data = response.json()
            assert data["success"] is False

    def test_rate_limiting(self, client):
        """Test API rate limiting"""
        responses = []

        # Make multiple rapid requests
        for _ in range(100):
            response = client.get("/api/strategies")
            responses.append(response)

        # At least some requests should be rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "Rate limiting should be active"

class TestPerformanceIntegration:
    """Test performance under load"""

    def test_bulk_strategy_operations(self, client, test_db):
        """Test bulk operations performance"""
        import time

        # Create multiple strategies
        strategies_data = []
        for i in range(50):
            strategies_data.append({
                "name": f"Bulk Strategy {i}",
                "description": f"Strategy {i} for bulk testing",
                "parameters": {"index": i},
                "status": "draft"
            })

        # Measure time for bulk creation
        start_time = time.time()

        for strategy_data in strategies_data:
            response = client.post("/api/strategies", json=strategy_data)
            assert response.status_code == 201

        creation_time = time.time() - start_time

        # Should complete within reasonable time (5 seconds)
        assert creation_time < 5.0, f"Bulk creation took too long: {creation_time}s"

        # Verify all strategies were created
        response = client.get("/api/strategies?per_page=100")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) >= 50

    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests"""
        import threading
        import time

        results = []

        def make_request():
            start_time = time.time()
            response = client.get("/api/strategies")
            end_time = time.time()
            results.append({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })

        # Make 20 concurrent requests
        threads = []
        for _ in range(20):
            thread = threading.Thread(target=make_request)
            threads.append(thread)

        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # All requests should succeed
        assert all(r["status_code"] == 200 for r in results)

        # Average response time should be reasonable
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        assert avg_response_time < 2.0, f"Average response time too high: {avg_response_time}s"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
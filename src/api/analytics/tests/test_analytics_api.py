"""
Analytics API Tests
Unit and integration tests for analytics endpoints
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..router import router
from ..services.performance import PerformanceService
from ..services.portfolio import PortfolioService
from ..cache import AnalyticsCache
from ...main import app  # Adjust based on your main app location


# Test fixtures
@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def db_session():
    """Create test database session"""
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    from ...database import Base
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def mock_performance_service():
    """Mock performance service"""
    service = Mock(spec=PerformanceService)
    service.calculate_performance = AsyncMock()
    service.get_historical_data = AsyncMock()
    service.get_realtime_metrics = AsyncMock()
    return service

@pytest.fixture
def mock_portfolio_service():
    """Mock portfolio service"""
    service = Mock(spec=PortfolioService)
    service.get_portfolio_analytics = AsyncMock()
    return service

@pytest.fixture
def mock_cache():
    """Mock cache service"""
    cache = Mock(spec=AnalyticsCache)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    cache.get_stats = AsyncMock(return_value={"connected": True, "hit_rate": 85.5})
    return cache

@pytest.fixture
def sample_performance_metrics():
    """Sample performance metrics data"""
    return {
        "strategy_id": "test_strategy_001",
        "period": "1M",
        "total_return": 12.5,
        "sharpe_ratio": 1.85,
        "sortino_ratio": 2.1,
        "max_drawdown": -8.3,
        "volatility": 15.2,
        "calmar_ratio": 1.51,
        "win_rate": 65.4,
        "profit_factor": 1.95,
        "avg_trade_duration": 2.4,
        "beta": 0.85,
        "alpha": 3.2
    }

@pytest.fixture
def sample_historical_data():
    """Sample historical data"""
    from datetime import date
    return [
        {
            "date": date(2024, 1, 1),
            "value": 100000,
            "benchmark": 98000,
            "volume": 1500000,
            "positions": 25
        },
        {
            "date": date(2024, 1, 2),
            "value": 100500,
            "benchmark": 98500,
            "volume": 1200000,
            "positions": 23
        }
    ]

@pytest.fixture
def sample_portfolio_analytics():
    """Sample portfolio analytics data"""
    return {
        "total_value": 1000000,
        "cash": 50000,
        "invested": 950000,
        "available_margin": 150000,
        "day_change": 2500,
        "day_change_percent": 0.25,
        "total_return": 125000,
        "total_return_percent": 12.5,
        "assets": [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "value": 150000,
                "weight": 15.0,
                "target_weight": 12.0,
                "sector": "Technology",
                "change": 1250,
                "change_percent": 0.84
            }
        ],
        "sectors": [
            {
                "name": "Technology",
                "value": 410000,
                "weight": 41.0,
                "target_weight": 37.0,
                "assets": ["AAPL", "MSFT", "GOOGL"]
            }
        ],
        "var_95": -25000,
        "cvar_95": -35000
    }


class TestPerformanceEndpoint:
    """Test performance analytics endpoint"""

    @patch('analytics.services.performance.PerformanceService')
    @patch('analytics.cache.get_cache')
    async def test_get_strategy_performance_success(
        self,
        mock_cache,
        mock_performance_service,
        sample_performance_metrics
    ):
        """Test successful performance metrics retrieval"""
        # Setup mocks
        cache_instance = Mock()
        cache_instance.get = AsyncMock(return_value=None)
        cache_instance.set = AsyncMock(return_value=True)
        mock_cache.return_value = cache_instance

        service_instance = Mock()
        service_instance.calculate_performance = AsyncMock(
            return_value=sample_performance_metrics
        )
        mock_performance_service.return_value = service_instance

        # Test request
        response = client.get(
            "/api/analytics/performance/test_strategy_001?period=1M"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["strategy_id"] == "test_strategy_001"
        assert data["period"] == "1M"
        assert data["total_return"] == 12.5

    @patch('analytics.cache.get_cache')
    async def test_get_strategy_performance_cache_hit(
        self,
        mock_cache,
        sample_performance_metrics
    ):
        """Test performance metrics retrieval from cache"""
        # Setup cache mock
        cache_instance = Mock()
        cache_instance.get = AsyncMock(return_value=sample_performance_metrics)
        mock_cache.return_value = cache_instance

        # Test request
        response = client.get(
            "/api/analytics/performance/test_strategy_001?period=1M"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["strategy_id"] == "test_strategy_001"

    async def test_get_strategy_performance_invalid_period(self):
        """Test performance metrics with invalid period"""
        response = client.get(
            "/api/analytics/performance/test_strategy_001?period=2X"
        )
        assert response.status_code == 422  # Validation error


class TestHistoricalDataEndpoint:
    """Test historical data endpoint"""

    @patch('analytics.services.performance.PerformanceService')
    async def test_get_strategy_history_success(
        self,
        mock_performance_service,
        sample_historical_data
    ):
        """Test successful historical data retrieval"""
        # Setup mock
        service_instance = Mock()
        service_instance.get_historical_data = AsyncMock(
            return_value=(sample_historical_data, 2)
        )
        mock_performance_service.return_value = service_instance

        # Test request
        start_date = "2024-01-01T00:00:00"
        end_date = "2024-01-02T00:00:00"
        response = client.get(
            f"/api/analytics/history/test_strategy_001?start_date={start_date}&end_date={end_date}"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["strategy_id"] == "test_strategy_001"
        assert len(data["data"]) == 2
        assert data["total_points"] == 2

    async def test_get_strategy_history_invalid_date_range(self):
        """Test historical data with invalid date range"""
        start_date = "2024-01-02T00:00:00"
        end_date = "2024-01-01T00:00:00"  # End before start
        response = client.get(
            f"/api/analytics/history/test_strategy_001?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 400

    async def test_get_strategy_history_date_range_too_large(self):
        """Test historical data with date range exceeding limit"""
        start_date = "2022-01-01T00:00:00"
        end_date = "2024-01-01T00:00:00"  # 2 years
        response = client.get(
            f"/api/analytics/history/test_strategy_001?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 400


class TestPortfolioEndpoint:
    """Test portfolio analytics endpoint"""

    @patch('analytics.services.portfolio.PortfolioService')
    @patch('analytics.cache.get_cache')
    async def test_get_portfolio_analytics_success(
        self,
        mock_cache,
        mock_portfolio_service,
        sample_portfolio_analytics
    ):
        """Test successful portfolio analytics retrieval"""
        # Setup mocks
        cache_instance = Mock()
        cache_instance.get = AsyncMock(return_value=None)
        cache_instance.set = AsyncMock(return_value=True)
        mock_cache.return_value = cache_instance

        service_instance = Mock()
        service_instance.get_portfolio_analytics = AsyncMock(
            return_value=sample_portfolio_analytics
        )
        mock_portfolio_service.return_value = service_instance

        # Test request
        response = client.get("/api/analytics/portfolio")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_value"] == 1000000
        assert data["day_change_percent"] == 0.25
        assert len(data["assets"]) == 1
        assert len(data["sectors"]) == 1

    async def test_get_portfolio_analytics_with_correlations(self):
        """Test portfolio analytics with correlation matrix"""
        response = client.get("/api/analytics/portfolio?include_correlations=true")
        # Should include correlations in response
        assert response.status_code == 200


class TestRealTimeEndpoint:
    """Test real-time metrics endpoint"""

    @patch('analytics.services.performance.PerformanceService')
    @patch('analytics.cache.get_cache')
    async def test_get_realtime_metrics_success(
        self,
        mock_cache,
        mock_performance_service
    ):
        """Test successful real-time metrics retrieval"""
        # Setup mocks
        cache_instance = Mock()
        cache_instance.get = AsyncMock(return_value=None)
        cache_instance.set = AsyncMock(return_value=True)
        mock_cache.return_value = cache_instance

        service_instance = Mock()
        service_instance.get_realtime_metrics = AsyncMock(
            return_value={
                "strategy_id": "test_strategy_001",
                "status": "active",
                "current_positions": 10,
                "total_exposure": 500000,
                "leverage": 2.0,
                "daily_pnl": 1250,
                "unrealized_pnl": 5000,
                "realized_pnl": -250,
                "last_updated": datetime.now(),
                "market_value": 500000
            }
        )
        mock_performance_service.return_value = service_instance

        # Test request
        response = client.get("/api/analytics/realtime/test_strategy_001")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["strategy_id"] == "test_strategy_001"
        assert data["status"] == "active"
        assert data["daily_pnl"] == 1250


class TestCacheEndpoint:
    """Test cache-related endpoints"""

    @patch('analytics.cache.get_cache')
    async def test_get_cache_stats(self, mock_cache):
        """Test cache statistics endpoint"""
        # Setup mock
        cache_instance = Mock()
        cache_instance.get_stats = AsyncMock(
            return_value={
                "connected": True,
                "hit_rate": 85.5,
                "total_keys": 1000
            }
        )
        mock_cache.return_value = cache_instance

        # Test request
        response = client.get("/api/analytics/cache/stats")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["hit_rate"] == 85.5


class TestRefreshEndpoint:
    """Test refresh endpoints"""

    @patch('analytics.background.get_task_manager')
    @patch('analytics.cache.get_cache')
    async def test_refresh_strategy_metrics(self, mock_cache, mock_task_manager):
        """Test strategy metrics refresh"""
        # Setup mocks
        cache_instance = Mock()
        cache_instance.delete = AsyncMock(return_value=True)
        mock_cache.return_value = cache_instance

        task_manager = Mock()
        task_manager.calculate_metrics_background = AsyncMock()
        mock_task_manager.return_value = task_manager

        # Test request
        response = client.post("/api/analytics/refresh/test_strategy_001")

        # Assertions
        assert response.status_code == 202
        data = response.json()
        assert "message" in data


class TestPerformanceLoad:
    """Performance and load testing"""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test API under concurrent load"""
        import asyncio
        import httpx

        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            # Create 100 concurrent requests
            tasks = []
            for i in range(100):
                task = client.get(
                    "/api/analytics/performance/test_strategy_001?period=1M"
                )
                tasks.append(task)

            # Execute all requests concurrently
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Check results
            success_count = sum(
                1 for r in responses
                if hasattr(r, 'status_code') and r.status_code == 200
            )
            error_count = len(responses) - success_count

            # Assertions
            assert success_count > 90  # At least 90% should succeed
            assert error_count < 10  # Less than 10% should fail

    @pytest.mark.asyncio
    async def test_response_time(self):
        """Test API response time requirements"""
        import time
        import httpx

        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            start_time = time.time()
            response = await client.get(
                "/api/analytics/performance/test_strategy_001?period=1D"
            )
            end_time = time.time()

            response_time_ms = (end_time - start_time) * 1000

            # Should respond in under 500ms for cached data
            assert response.status_code == 200
            assert response_time_ms < 500


# Integration tests
class TestAnalyticsIntegration:
    """Integration tests for analytics API"""

    @pytest.mark.asyncio
    async def test_full_analytics_workflow(self, client):
        """Test complete analytics workflow"""
        # 1. Get strategy performance
        perf_response = client.get("/api/analytics/performance/test_strategy_001")
        assert perf_response.status_code == 200

        # 2. Get historical data
        hist_response = client.get(
            "/api/analytics/history/test_strategy_001"
            "?start_date=2024-01-01T00:00:00"
            "&end_date=2024-01-31T00:00:00"
        )
        assert hist_response.status_code == 200

        # 3. Get real-time metrics
        realtime_response = client.get("/api/analytics/realtime/test_strategy_001")
        assert realtime_response.status_code == 200

        # 4. Get portfolio analytics
        portfolio_response = client.get("/api/analytics/portfolio")
        assert portfolio_response.status_code == 200

        # 5. Refresh strategy metrics
        refresh_response = client.post("/api/analytics/refresh/test_strategy_001")
        assert refresh_response.status_code == 202


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
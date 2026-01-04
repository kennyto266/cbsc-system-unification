"""
Integration tests for Strategy API endpoints
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestStrategyCRUDAPI:
    """Test Strategy CRUD API endpoints"""

    async def test_create_strategy_unauthorized(self, client: AsyncClient):
        """Test creating strategy without authentication"""
        response = await client.post(
            "/api/v1/strategies",
            json={
                "name": "Test Strategy",
                "strategy_type": "momentum",
                "config": {"short_window": 5}
            }
        )
        
        assert response.status_code in [401, 403]

    async def test_list_strategies(self, authenticated_client: AsyncClient, test_strategies):
        """Test listing strategies"""
        response = await authenticated_client.get("/api/v1/strategies")
        
        assert response.status_code == 200
        data = response.json()
        assert "strategies" in data or data is list
        assert len(data.get("strategies", data)) >= len(test_strategies)

    async def test_get_strategy_by_id(self, authenticated_client: AsyncClient, test_strategy):
        """Test getting strategy by ID"""
        response = await authenticated_client.get(f"/api/v1/strategies/{test_strategy.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_strategy.id)

    async def test_update_strategy(self, authenticated_client: AsyncClient, test_strategy):
        """Test updating strategy"""
        response = await authenticated_client.put(
            f"/api/v1/strategies/{test_strategy.id}",
            json={"name": "Updated Strategy", "status": "active"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Strategy"


@pytest.mark.integration
@pytest.mark.asyncio
class TestStrategyOperationsAPI:
    """Test Strategy operation endpoints"""

    async def test_execute_strategy(self, authenticated_client: AsyncClient, test_strategy):
        """Test executing a strategy"""
        response = await authenticated_client.post(
            f"/api/v1/strategies/{test_strategy.id}/execute"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_stop_strategy(self, authenticated_client: AsyncClient, test_strategy):
        """Test stopping a strategy"""
        response = await authenticated_client.post(
            f"/api/v1/strategies/{test_strategy.id}/stop"
        )
        
        assert response.status_code == 200

    async def test_get_strategy_status(self, authenticated_client: AsyncClient, test_strategy):
        """Test getting strategy status"""
        response = await authenticated_client.get(
            f"/api/v1/strategies/{test_strategy.id}/status"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

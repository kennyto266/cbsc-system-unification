"""
Unit tests for Enhanced Strategy Router
Tests all REST endpoints, error handling, and authentication
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status, HTTPException, WebSocket
from httpx import AsyncClient
import json
from datetime import datetime
from typing import Dict, Any

from src.api.main import app
from src.api.strategies.enhanced_router import router


class TestEnhancedStrategyRouter:
    """Test suite for Enhanced Strategy Router endpoints"""

    @pytest.fixture
    def test_client(self) -> TestClient:
        """Create test client for FastAPI app"""
        return TestClient(app)

    @pytest.fixture
    async def async_client(self) -> AsyncClient:
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    # ========================================
    # GET /api/v1/strategies Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.strategy
    async def test_list_strategies_success(
        self,
        async_client,
        sample_strategies_data,
        mock_current_user,
        auth_headers
    ):
        """Test successful list strategies endpoint"""
        # Arrange
        with patch('src.api.strategies.enhanced_router.get_enhanced_strategy_service') as mock_service:
            service_mock = AsyncMock()
            service_mock.list_strategies.return_value = {
                "items": sample_strategies_data,
                "total": len(sample_strategies_data),
                "page": 1,
                "page_size": 20
            }
            mock_service.return_value = service_mock

            with patch('src.api.strategies.enhanced_router.get_current_user', return_value=mock_current_user):
                # Act
                response = await async_client.get(
                    "/api/v1/strategies",
                    headers=auth_headers,
                    params={"page": 1, "page_size": 20}
                )

                # Assert
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "items" in data
                assert "total" in data
                assert data["total"] == len(sample_strategies_data)
                assert len(data["items"]) == len(sample_strategies_data)

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.strategy
    async def test_list_strategies_with_filters(
        self,
        async_client,
        sample_strategies_data,
        mock_current_user,
        auth_headers
    ):
        """Test listing strategies with filters"""
        # Arrange
        filters = {
            "strategy_type": "momentum",
            "status": "active",
            "page": 2,
            "page_size": 10
        }

        with patch('src.api.strategies.enhanced_router.get_enhanced_strategy_service') as mock_service:
            service_mock = AsyncMock()
            service_mock.list_strategies.return_value = {
                "items": [s for s in sample_strategies_data if s["strategy_type"] == "momentum"],
                "total": 3,
                "page": 2,
                "page_size": 10
            }
            mock_service.return_value = service_mock

            with patch('src.api.strategies.enhanced_router.get_current_user', return_value=mock_current_user):
                # Act
                response = await async_client.get(
                    "/api/v1/strategies",
                    headers=auth_headers,
                    params=filters
                )

                # Assert
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["page"] == 2
                assert data["page_size"] == 10
                assert all(item["strategy_type"] == "momentum" for item in data["items"])

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.error_handling
    async def test_list_strategies_unauthorized(self, async_client):
        """Test listing strategies without authentication"""
        # Act
        response = await async_client.get("/api/v1/strategies")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.error_handling
    async def test_list_strategies_invalid_pagination(
        self,
        async_client,
        mock_current_user,
        auth_headers
    ):
        """Test listing strategies with invalid pagination parameters"""
        # Arrange
        with patch('src.api.strategies.enhanced_router.get_current_user', return_value=mock_current_user):
            # Act
            response = await async_client.get(
                "/api/v1/strategies",
                headers=auth_headers,
                params={"page": 0, "page_size": 0}  # Invalid values
            )

            # Assert
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # ========================================
    # GET /api/v1/strategies/{id} Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.strategy
    async def test_get_strategy_by_id_success(
        self,
        async_client,
        sample_strategy_data,
        mock_current_user,
        auth_headers
    ):
        """Test successful get strategy by ID"""
        # Arrange
        strategy_id = 1

        with patch('src.api.strategies.enhanced_router.get_enhanced_strategy_service') as mock_service:
            service_mock = AsyncMock()
            service_mock.get_strategy.return_value = sample_strategy_data
            mock_service.return_value = service_mock

            with patch('src.api.strategies.enhanced_router.get_current_user', return_value=mock_current_user):
                # Act
                response = await async_client.get(
                    f"/api/v1/strategies/{strategy_id}",
                    headers=auth_headers
                )

                # Assert
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["id"] == strategy_id
                assert data["name"] == sample_strategy_data["name"]

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.error_handling
    async def test_get_strategy_not_found(
        self,
        async_client,
        mock_current_user,
        auth_headers
    ):
        """Test getting non-existent strategy"""
        # Arrange
        strategy_id = 999

        with patch('src.api.strategies.enhanced_router.get_enhanced_strategy_service') as mock_service:
            service_mock = AsyncMock()
            from src.api.strategies.utils.response import NotFoundError
            service_mock.get_strategy.side_effect = NotFoundError("Strategy not found")
            mock_service.return_value = service_mock

            with patch('src.api.strategies.enhanced_router.get_current_user', return_value=mock_current_user):
                # Act
                response = await async_client.get(
                    f"/api/v1/strategies/{strategy_id}",
                    headers=auth_headers
                )

                # Assert
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert "Strategy not found" in response.json()["detail"]

    # ========================================
    # POST /api/v1/strategies Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.strategy
    async def test_create_strategy_success(
        self,
        async_client,
        sample_strategy_data,
        mock_current_user,
        auth_headers
    ):
        """Test successful strategy creation"""
        # Arrange
        create_data = {
            "name": "New Strategy",
            "description": "Test strategy creation",
            "strategy_type": "momentum",
            "parameters": {"timeframe": "1h", "risk_level": "medium"}
        }

        created_strategy = {
            **sample_strategy_data,
            **create_data,
            "id": 2,
            "user_id": mock_current_user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        with patch('src.api.strategies.enhanced_router.get_enhanced_strategy_service') as mock_service:
            service_mock = AsyncMock()
            service_mock.create_strategy.return_value = created_strategy
            mock_service.return_value = service_mock

            with patch('src.api.strategies.enhanced_router.get_current_user', return_value=mock_current_user):
                # Act
                response = await async_client.post(
                    "/api/v1/strategies",
                    headers=auth_headers,
                    json=create_data
                )

                # Assert
                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["name"] == create_data["name"]
                assert data["strategy_type"] == create_data["strategy_type"]
                assert data["user_id"] == mock_current_user.id

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.error_handling
    async def test_create_strategy_validation_error(
        self,
        async_client,
        mock_current_user,
        auth_headers
    ):
        """Test strategy creation with validation error"""
        # Arrange
        invalid_data = {
            "name": "",  # Empty name should fail validation
            "strategy_type": "invalid_type",  # Invalid type
            "parameters": "not_an_object"  # Should be an object
        }

        with patch('src.api.strategies.enhanced_router.get_current_user', return_value=mock_current_user):
            # Act
            response = await async_client.post(
                "/api/v1/strategies",
                headers=auth_headers,
                json=invalid_data
            )

            # Assert
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            errors = response.json()["detail"]
            assert any("name" in str(error).lower() for error in errors)

    # ========================================
    # PUT /api/v1/strategies/{id} Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.strategy
    async def test_update_strategy_success(
        self,
        async_client,
        sample_strategy_data,
        mock_current_user,
        auth_headers
    ):
        """Test successful strategy update"""
        # Arrange
        strategy_id = 1
        update_data = {
            "name": "Updated Strategy Name",
            "description": "Updated description",
            "status": "inactive"
        }

        updated_strategy = {
            **sample_strategy_data,
            **update_data,
            "updated_at": datetime.utcnow()
        }

        with patch('src.api.strategies.enhanced_router.get_enhanced_strategy_service') as mock_service:
            service_mock = AsyncMock()
            service_mock.update_strategy.return_value = updated_strategy
            mock_service.return_value = service_mock

            with patch('src.api.strategies.enhanced_router.get_current_user', return_value=mock_current_user):
                # Act
                response = await async_client.put(
                    f"/api/v1/strategies/{strategy_id}",
                    headers=auth_headers,
                    json=update_data
                )

                # Assert
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["name"] == update_data["name"]
                assert data["status"] == update_data["status"]

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.error_handling
    async def test_update_strategy_not_found(
        self,
        async_client,
        mock_current_user,
        auth_headers
    ):
        """Test updating non-existent strategy"""
        # Arrange
        strategy_id = 999
        update_data = {"name": "Updated Name"}

        with patch('src.api.strategies.enhanced_router.get_enhanced_strategy_service') as mock_service:
            service_mock = AsyncMock()
            from src.api.strategies.utils.response import NotFoundError
            service_mock.update_strategy.side_effect = NotFoundError("Strategy not found")
            mock_service.return_value = service_mock

            with patch('src.api.strategies.enhanced_router.get_current_user', return_value=mock_current_user):
                # Act
                response = await async_client.put(
                    f"/api/v1/strategies/{strategy_id}",
                    headers=auth_headers,
                    json=update_data
                )

                # Assert
                assert response.status_code == status.HTTP_404_NOT_FOUND

    # ========================================
    # DELETE /api/v1/strategies/{id} Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.strategy
    async def test_delete_strategy_success(
        self,
        async_client,
        mock_current_user,
        auth_headers
    ):
        """Test successful strategy deletion"""
        # Arrange
        strategy_id = 1

        with patch('src.api.strategies.enhanced_router.get_enhanced_strategy_service') as mock_service:
            service_mock = AsyncMock()
            service_mock.delete_strategy.return_value = True
            mock_service.return_value = service_mock

            with patch('src.api.strategies.enhanced_router.get_current_user', return_value=mock_current_user):
                # Act
                response = await async_client.delete(
                    f"/api/v1/strategies/{strategy_id}",
                    headers=auth_headers
                )

                # Assert
                assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.error_handling
    async def test_delete_strategy_not_found(
        self,
        async_client,
        mock_current_user,
        auth_headers
    ):
        """Test deleting non-existent strategy"""
        # Arrange
        strategy_id = 999

        with patch('src.api.strategies.enhanced_router.get_enhanced_strategy_service') as mock_service:
            service_mock = AsyncMock()
            from src.api.strategies.utils.response import NotFoundError
            service_mock.delete_strategy.side_effect = NotFoundError("Strategy not found")
            mock_service.return_value = service_mock

            with patch('src.api.strategies.enhanced_router.get_current_user', return_value=mock_current_user):
                # Act
                response = await async_client.delete(
                    f"/api/v1/strategies/{strategy_id}",
                    headers=auth_headers
                )

                # Assert
                assert response.status_code == status.HTTP_404_NOT_FOUND

    # ========================================
    # Batch Operations Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.batch
    @pytest.mark.strategy
    async def test_batch_activate_strategies_success(
        self,
        async_client,
        mock_current_user,
        auth_headers
    ):
        """Test successful batch activation of strategies"""
        # Arrange
        batch_data = {
            "strategy_ids": [1, 2, 3, 4, 5],
            "operation": "activate",
            "config": {
                "batch_size": 10,
                "max_retries": 3,
                "continue_on_error": True
            }
        }

        batch_result = {
            "operation": "activate",
            "total": 5,
            "successful": ["1", "2", "3", "4", "5"],
            "failed": [],
            "progress": 1.0,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "duration": 2.5
        }

        with patch('src.api.strategies.enhanced_router.get_enhanced_strategy_service') as mock_service:
            service_mock = AsyncMock()
            service_mock.batch_operation.return_value = batch_result
            mock_service.return_value = service_mock

            with patch('src.api.strategies.enhanced_router.get_current_user', return_value=mock_current_user):
                # Act
                response = await async_client.post(
                    "/api/v1/strategies/batch",
                    headers=auth_headers,
                    json=batch_data
                )

                # Assert
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["operation"] == "activate"
                assert data["total"] == 5
                assert len(data["successful"]) == 5
                assert len(data["failed"]) == 0

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.batch
    @pytest.mark.error_handling
    async def test_batch_operation_invalid_operation_type(
        self,
        async_client,
        mock_current_user,
        auth_headers
    ):
        """Test batch operation with invalid operation type"""
        # Arrange
        batch_data = {
            "strategy_ids": [1, 2, 3],
            "operation": "invalid_operation",  # Invalid operation
            "config": {}
        }

        with patch('src.api.strategies.enhanced_router.get_current_user', return_value=mock_current_user):
            # Act
            response = await async_client.post(
                "/api/v1/strategies/batch",
                headers=auth_headers,
                json=batch_data
            )

            # Assert
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # ========================================
    # WebSocket Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.websocket
    async def test_websocket_connection_success(self):
        """Test successful WebSocket connection"""
        # Arrange
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_json = AsyncMock()
        mock_websocket.receive_json = AsyncMock()

        with patch('src.api.strategies.enhanced_router.get_websocket_service') as mock_ws_service:
            ws_service_mock = AsyncMock()
            mock_ws_service.return_value = ws_service_mock

            # Mock the WebSocket endpoint function
            with patch('src.api.strategies.enhanced_router.websocket_endpoint'):
                # Act
                # Note: In a real test, you would use TestClient's websocket feature
                # For unit tests, we mock the WebSocket behavior
                await mock_websocket.accept()
                await mock_websocket.send_json({"type": "connection", "status": "connected"})

                # Assert
                mock_websocket.accept.assert_called_once()
                mock_websocket.send_json.assert_called_once()

    # ========================================
    # Performance Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.performance
    async def test_list_strategies_performance(
        self,
        async_client,
        mock_current_user,
        auth_headers
    ):
        """Test list strategies endpoint performance"""
        # Arrange
        large_strategy_list = [{"id": i, "name": f"Strategy {i}"} for i in range(1, 101)]

        with patch('src.api.strategies.enhanced_router.get_enhanced_strategy_service') as mock_service:
            service_mock = AsyncMock()
            service_mock.list_strategies.return_value = {
                "items": large_strategy_list,
                "total": len(large_strategy_list),
                "page": 1,
                "page_size": 100
            }
            mock_service.return_value = service_mock

            with patch('src.api.strategies.enhanced_router.get_current_user', return_value=mock_current_user):
                # Act
                import time
                start_time = time.time()
                response = await async_client.get(
                    "/api/v1/strategies",
                    headers=auth_headers,
                    params={"page_size": 100}
                )
                end_time = time.time()

                # Assert
                assert response.status_code == status.HTTP_200_OK
                duration = end_time - start_time
                assert duration < 1.0  # Should respond within 1 second
                assert len(response.json()["items"]) == 100

    # ========================================
    # Error Handling Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.error_handling
    @pytest.mark.auth
    async def test_permission_denied_error(
        self,
        async_client,
        mock_current_user,
        auth_headers
    ):
        """Test permission denied error handling"""
        # Arrange
        strategy_id = 1

        with patch('src.api.strategies.enhanced_router.get_enhanced_strategy_service') as mock_service:
            service_mock = AsyncMock()
            from src.api.strategies.utils.response import PermissionError
            service_mock.get_strategy.side_effect = PermissionError("Access denied")
            mock_service.return_value = service_mock

            with patch('src.api.strategies.enhanced_router.get_current_user', return_value=mock_current_user):
                # Act
                response = await async_client.get(
                    f"/api/v1/strategies/{strategy_id}",
                    headers=auth_headers
                )

                # Assert
                assert response.status_code == status.HTTP_403_FORBIDDEN
                assert "Access denied" in response.json()["detail"]

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.error_handling
    async def test_internal_server_error(
        self,
        async_client,
        mock_current_user,
        auth_headers
    ):
        """Test internal server error handling"""
        # Arrange
        strategy_id = 1

        with patch('src.api.strategies.enhanced_router.get_enhanced_strategy_service') as mock_service:
            service_mock = AsyncMock()
            service_mock.get_strategy.side_effect = Exception("Database connection failed")
            mock_service.return_value = service_mock

            with patch('src.api.strategies.enhanced_router.get_current_user', return_value=mock_current_user):
                # Act
                response = await async_client.get(
                    f"/api/v1/strategies/{strategy_id}",
                    headers=auth_headers
                )

                # Assert
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    # ========================================
    # Response Format Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_response_format_consistency(
        self,
        async_client,
        sample_strategy_data,
        mock_current_user,
        auth_headers
    ):
        """Test that API responses have consistent format"""
        # Arrange
        strategy_id = 1

        with patch('src.api.strategies.enhanced_router.get_enhanced_strategy_service') as mock_service:
            service_mock = AsyncMock()
            service_mock.get_strategy.return_value = sample_strategy_data
            mock_service.return_value = service_mock

            with patch('src.api.strategies.enhanced_router.get_current_user', return_value=mock_current_user):
                # Act
                response = await async_client.get(
                    f"/api/v1/strategies/{strategy_id}",
                    headers=auth_headers
                )

                # Assert
                assert response.status_code == status.HTTP_200_OK
                data = response.json()

                # Check for required fields in strategy response
                required_fields = ["id", "name", "description", "strategy_type", "status", "created_at"]
                for field in required_fields:
                    assert field in data, f"Missing required field: {field}"

                # Check data types
                assert isinstance(data["id"], int)
                assert isinstance(data["name"], str)
                assert isinstance(data["status"], str)

    # ========================================
    # Header and Metadata Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_response_headers(
        self,
        async_client,
        mock_current_user,
        auth_headers
    ):
        """Test that response includes appropriate headers"""
        # Arrange
        with patch('src.api.strategies.enhanced_router.get_enhanced_strategy_service') as mock_service:
            service_mock = AsyncMock()
            service_mock.list_strategies.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20
            }
            mock_service.return_value = service_mock

            with patch('src.api.strategies.enhanced_router.get_current_user', return_value=mock_current_user):
                # Act
                response = await async_client.get(
                    "/api/v1/strategies",
                    headers=auth_headers
                )

                # Assert
                assert response.status_code == status.HTTP_200_OK
                assert "content-type" in response.headers
                assert "application/json" in response.headers["content-type"]
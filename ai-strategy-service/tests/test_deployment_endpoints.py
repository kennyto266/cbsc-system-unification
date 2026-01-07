"""
Tests for deployment endpoints in strategy router

Tests the FastAPI endpoints for deploying, validating, and syncing strategies.
"""
import pytest
import json
import tempfile
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from main import app
from services.cbsc_integration import cbsc_integration

client = TestClient(app)


@pytest.fixture
def sample_notebook():
    """Create a sample notebook for testing"""
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "metadata": {},
                "outputs": [],
                "source": [
                    "import pandas as pd\n",
                    "import numpy as np\n",
                    "SYMBOL = 'AAPL'\n",
                    "LOOKBACK = 20\n",
                    "THRESHOLD = 0.02\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Test Strategy"]
            }
        ],
        "nbformat": 4,
        "nbformat_minor": 4
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
        json.dump(notebook, f)
        return f.name


def test_deploy_strategy_endpoint(sample_notebook):
    """Test /api/strategy/deploy endpoint"""
    # Mock the CBSC integration
    with patch.object(cbsc_integration, 'deploy_strategy', new_callable=AsyncMock) as mock_deploy:
        mock_deploy.return_value = {
            "success": True,
            "strategy_id": "test-strategy-123",
            "message": "Strategy deployed successfully"
        }

        response = client.post(
            "/api/strategy/deploy",
            json={
                "notebook_path": sample_notebook,
                "strategy_name": "Test Strategy",
                "user_id": "user-123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True
        assert data['strategy_id'] == 'test-strategy-123'

        # Verify the integration was called correctly
        mock_deploy.assert_called_once_with(
            notebook_path=sample_notebook,
            strategy_name="Test Strategy",
            user_id="user-123"
        )


def test_deploy_strategy_missing_fields(sample_notebook):
    """Test deploy endpoint with missing required fields"""
    response = client.post(
        "/api/strategy/deploy",
        json={
            "notebook_path": sample_notebook,
            # Missing strategy_name and user_id
        }
    )

    assert response.status_code == 422  # Validation error


def test_validate_strategy_endpoint(sample_notebook):
    """Test /api/strategy/validate endpoint"""
    with patch.object(
        cbsc_integration,
        'validate_strategy_before_deployment',
        new_callable=AsyncMock
    ) as mock_validate:
        mock_validate.return_value = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "parameters_found": 3
        }

        response = client.post(
            "/api/strategy/validate",
            json={
                "notebook_path": sample_notebook
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['valid'] == True
        assert len(data['errors']) == 0
        assert data['parameters_found'] == 3


def test_validate_strategy_with_errors(sample_notebook):
    """Test validate endpoint when validation fails"""
    with patch.object(
        cbsc_integration,
        'validate_strategy_before_deployment',
        new_callable=AsyncMock
    ) as mock_validate:
        mock_validate.return_value = {
            "valid": False,
            "errors": ["Cell 3: Syntax error"],
            "warnings": ["Missing parameter: STOP_LOSS"],
            "parameters_found": 2
        }

        response = client.post(
            "/api/strategy/validate",
            json={
                "notebook_path": sample_notebook
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['valid'] == False
        assert len(data['errors']) == 1
        assert len(data['warnings']) == 1


def test_sync_strategies_endpoint():
    """Test /api/strategy/sync/{user_id} endpoint"""
    with patch.object(cbsc_integration, 'sync_to_dashboard', new_callable=AsyncMock) as mock_sync:
        mock_sync.return_value = {
            "strategies": [
                {"id": "s1", "name": "Strategy 1"},
                {"id": "s2", "name": "Strategy 2"}
            ],
            "total": 2
        }

        response = client.get("/api/strategy/sync/user-123")

        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 2
        assert len(data['strategies']) == 2

        mock_sync.assert_called_once_with("user-123")


def test_deploy_strategy_api_error(sample_notebook):
    """Test deploy endpoint when CBSC API returns error"""
    with patch.object(cbsc_integration, 'deploy_strategy', new_callable=AsyncMock) as mock_deploy:
        mock_deploy.side_effect = Exception("CBSC API unavailable")

        response = client.post(
            "/api/strategy/deploy",
            json={
                "notebook_path": sample_notebook,
                "strategy_name": "Test Strategy",
                "user_id": "user-123"
            }
        )

        assert response.status_code == 500
        assert "Strategy deployment failed" in response.json()['detail']


def test_validate_strategy_file_not_found():
    """Test validate endpoint with non-existent file"""
    response = client.post(
        "/api/strategy/validate",
        json={
            "notebook_path": "/nonexistent/file.ipynb"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data['valid'] == False
    assert 'not found' in data['errors'][0].lower()


def test_integration_endpoints_cooperation(sample_notebook):
    """Test that validate and deploy work together correctly"""
    # First validate
    with patch.object(
        cbsc_integration,
        'validate_strategy_before_deployment',
        new_callable=AsyncMock
    ) as mock_validate:
        mock_validate.return_value = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "parameters_found": 3
        }

        validation_response = client.post(
            "/api/strategy/validate",
            json={"notebook_path": sample_notebook}
        )

        assert validation_response.status_code == 200
        assert validation_response.json()['valid'] == True

    # Then deploy (since validation passed)
    with patch.object(cbsc_integration, 'deploy_strategy', new_callable=AsyncMock) as mock_deploy:
        mock_deploy.return_value = {
            "success": True,
            "strategy_id": "deployed-123",
            "message": "Strategy deployed successfully"
        }

        deploy_response = client.post(
            "/api/strategy/deploy",
            json={
                "notebook_path": sample_notebook,
                "strategy_name": "Validated Strategy",
                "user_id": "user-456"
            }
        )

        assert deploy_response.status_code == 200
        assert deploy_response.json()['strategy_id'] == 'deployed-123'

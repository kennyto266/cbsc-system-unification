"""
Tests for CBSC Integration Service

Tests the integration between AI-generated strategies and the existing CBSC system.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from services.cbsc_integration import CBSCIntegration, cbsc_integration


@pytest.mark.asyncio
async def test_extract_parameters_from_notebook():
    """Test parameter extraction from notebook"""
    # Create a test notebook with parameter definitions
    test_notebook = {
        "cells": [
            {
                "cell_type": "code",
                "metadata": {},
                "outputs": [],
                "source": [
                    "SYMBOL = 'AAPL'\n",
                    "LOOKBACK = 20\n",
                    "THRESHOLD = 0.02\n",
                    "START_DATE = '2023-01-01'\n",
                    "END_DATE = '2024-01-01'\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Strategy Description"]
            }
        ],
        "nbformat": 4,
        "nbformat_minor": 4
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
        json.dump(test_notebook, f)
        temp_path = f.name

    try:
        integration = CBSCIntegration()
        params = await integration._extract_parameters(temp_path)

        # Verify extracted parameters
        assert 'symbol' in params
        assert params['symbol'] == 'AAPL'
        assert 'lookback' in params
        assert params['lookback'] == 20  # Now integer type
        assert 'threshold' in params
        assert params['threshold'] == 0.02  # Now float type
        assert 'start_date' in params
        assert params['start_date'] == '2023-01-01'
        assert 'end_date' in params
        assert params['end_date'] == '2024-01-01'
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_extract_parameters_empty_notebook():
    """Test parameter extraction from notebook with no parameters"""
    test_notebook = {
        "cells": [
            {
                "cell_type": "code",
                "metadata": {},
                "outputs": [],
                "source": ["import pandas as pd\n", "import numpy as np\n"]
            }
        ],
        "nbformat": 4,
        "nbformat_minor": 4
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
        json.dump(test_notebook, f)
        temp_path = f.name

    try:
        integration = CBSCIntegration()
        params = await integration._extract_parameters(temp_path)

        # Should return empty dict if no parameters found
        assert isinstance(params, dict)
        assert len(params) == 0
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
@patch('services.cbsc_integration.httpx.AsyncClient')
async def test_deploy_strategy_success(mock_client_class):
    """Test successful strategy deployment to CBSC"""
    # Mock successful API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "strategy-123", "name": "Test Strategy"}
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client

    # Create test notebook
    test_notebook = {
        "cells": [
            {
                "cell_type": "code",
                "metadata": {},
                "outputs": [],
                "source": ["SYMBOL = 'AAPL'\n", "LOOKBACK = 20\n"]
            }
        ],
        "nbformat": 4,
        "nbformat_minor": 4
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
        json.dump(test_notebook, f)
        temp_path = f.name

    try:
        integration = CBSCIntegration()
        integration.client = mock_client

        result = await integration.deploy_strategy(
            notebook_path=temp_path,
            strategy_name="Test Strategy",
            user_id="user-123"
        )

        assert result['success'] == True
        assert result['strategy_id'] == 'strategy-123'
        assert 'deployed successfully' in result['message'].lower()

        # Verify the API was called correctly
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert '/api/strategies' in str(call_args)
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
@patch('services.cbsc_integration.httpx.AsyncClient')
async def test_deploy_strategy_api_error(mock_client_class):
    """Test strategy deployment with API error"""
    # Mock API error response
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = Exception("Internal Server Error")

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client

    # Create test notebook
    test_notebook = {
        "cells": [
            {
                "cell_type": "code",
                "metadata": {},
                "outputs": [],
                "source": ["SYMBOL = 'AAPL'\n"]
            }
        ],
        "nbformat": 4,
        "nbformat_minor": 4
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
        json.dump(test_notebook, f)
        temp_path = f.name

    try:
        integration = CBSCIntegration()
        integration.client = mock_client

        with pytest.raises(Exception) as exc_info:
            await integration.deploy_strategy(
                notebook_path=temp_path,
                strategy_name="Test Strategy",
                user_id="user-123"
            )

        assert "Internal Server Error" in str(exc_info.value)
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
@patch('services.cbsc_integration.httpx.AsyncClient')
async def test_sync_to_dashboard(mock_client_class):
    """Test syncing strategies to personal dashboard"""
    # Mock successful API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "strategies": [
            {"id": "s1", "name": "Strategy 1"},
            {"id": "s2", "name": "Strategy 2"}
        ],
        "total": 2
    }
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client

    integration = CBSCIntegration()
    integration.client = mock_client

    result = await integration.sync_to_dashboard("user-123")

    assert result['total'] == 2
    assert len(result['strategies']) == 2

    # Verify the API was called correctly
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert 'user-123' in str(call_args)
    assert '/strategies' in str(call_args)


@pytest.mark.asyncio
async def test_strategy_config_structure():
    """Test that strategy configuration is properly structured"""
    test_notebook = {
        "cells": [
            {
                "cell_type": "code",
                "metadata": {},
                "outputs": [],
                "source": [
                    "SYMBOL = 'TSLA'\n",
                    "RISK_TOLERANCE = 'aggressive'\n",
                    "CAPITAL = 50000\n"
                ]
            }
        ],
        "nbformat": 4,
        "nbformat_minor": 4
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
        json.dump(test_notebook, f)
        temp_path = f.name

    try:
        integration = CBSCIntegration()

        # Extract parameters
        params = await integration._extract_parameters(temp_path)

        # Build strategy config (simulate what deploy_strategy does)
        strategy_config = {
            "name": "Test Strategy",
            "type": "personal",
            "category": "other",
            "description": params.get("description", "Created with AI Assistant"),
            "parameters": {
                **params,
                "created_with_ai": True,
                "source_notebook": temp_path
            },
            "personalConfig": {
                "userId": "test-user",
                "riskTolerance": params.get("risk_tolerance", "moderate"),
                "capitalAllocation": params.get("capital", 10000),
                "maxPositionSize": params.get("max_position", 0.1),
                "stopLoss": params.get("stop_loss", 0.03),
                "takeProfit": params.get("take_profit", 0.1),
                "autoTrading": False
            }
        }

        # Verify structure
        assert strategy_config['type'] == 'personal'
        assert strategy_config['category'] == 'other'
        assert strategy_config['parameters']['created_with_ai'] == True
        assert strategy_config['personalConfig']['userId'] == 'test-user'
        assert strategy_config['personalConfig']['riskTolerance'] == 'aggressive'
        assert strategy_config['personalConfig']['capitalAllocation'] == 50000
        assert 'symbol' in strategy_config['parameters']

    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_close_client():
    """Test that HTTP client is properly closed"""
    integration = CBSCIntegration()

    # Mock the close method
    with patch.object(integration.client, 'aclose', new_callable=AsyncMock) as mock_close:
        await integration.close()
        mock_close.assert_called_once()

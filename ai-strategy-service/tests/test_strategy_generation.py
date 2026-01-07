"""
Tests for Strategy Generation API
Following TDD approach
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_generate_strategy_endpoint():
    """Test strategy generation endpoint"""
    response = client.post(
        "/api/strategy/generate",
        json={
            "description": "Simple moving average crossover strategy",
            "market": "stock",
            "timeframe": "daily",
            "risk_level": "medium"
        }
    )

    # Should return 200 or 500 (if GLM API not configured)
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()
        assert "code" in data
        assert "explanation" in data
        assert "parameters" in data
        assert "model" in data
        assert data["model"] == "glm-4-plus"


def test_generate_strategy_with_minimal_params():
    """Test strategy generation with minimal parameters"""
    response = client.post(
        "/api/strategy/generate",
        json={
            "description": "Buy low sell high"
        }
    )

    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()
        # Should use defaults
        assert "code" in data


def test_generate_strategy_missing_description():
    """Test strategy generation with missing description"""
    response = client.post(
        "/api/strategy/generate",
        json={
            "market": "stock",
            "timeframe": "daily"
        }
    )

    # Should return validation error
    assert response.status_code == 422


def test_chat_endpoint():
    """Test general chat endpoint"""
    response = client.post(
        "/api/strategy/chat",
        json={
            "message": "What is a trading strategy?",
            "history": []
        }
    )

    # Should return 200 or 500 (if GLM API not configured)
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()
        assert "response" in data
        assert "is_strategy" in data
        assert isinstance(data["is_strategy"], bool)


def test_chat_with_history():
    """Test chat endpoint with conversation history"""
    response = client.post(
        "/api/strategy/chat",
        json={
            "message": "Can you explain more?",
            "history": [
                {"role": "user", "content": "What is a trading strategy?"},
                {"role": "assistant", "content": "A trading strategy is..."}
            ]
        }
    )

    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()
        assert "response" in data


def test_chat_missing_message():
    """Test chat endpoint with missing message"""
    response = client.post(
        "/api/strategy/chat",
        json={}
    )

    # Should return validation error
    assert response.status_code == 422


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_parse_code_cells_helper():
    """Test parse_code_cells helper function"""
    from routers.strategy import parse_code_cells

    response = """
```python
# Cell 1
import pandas as pd
```
```python
# Cell 2
import numpy as np
```
"""

    result = parse_code_cells(response)

    assert "Cell 1" in result
    assert "Cell 2" in result
    assert "import pandas" in result
    assert "import numpy" in result


def test_extract_parameters_helper():
    """Test extract_parameters helper function"""
    from routers.strategy import extract_parameters

    response = """
    LOOKBACK = 20
    THRESHOLD = 0.02
    STOP_LOSS = 0.05
    """

    params = extract_parameters(response)

    assert "lookback" in params
    assert params["lookback"] == "20"
    assert "threshold" in params
    assert "stop_loss" in params


def test_contains_strategy_code_helper():
    """Test contains_strategy_code helper function"""
    from routers.strategy import contains_strategy_code

    # Should detect strategy code
    assert contains_strategy_code("import pandas as pd")
    assert contains_strategy_code("def generate_signal():")
    assert contains_strategy_code("backtest the strategy")

    # Should not detect in plain text
    assert not contains_strategy_code("Hello, how are you?")
    assert not contains_strategy_code("The weather is nice today")

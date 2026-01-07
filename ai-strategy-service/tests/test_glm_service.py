"""
Tests for GLM Service
Test the GLM API integration for strategy generation
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.glm_service import GLMService, GLMMessage, GLMRequest


@pytest.mark.asyncio
async def test_glm_service_initialization():
    """Test GLM service initializes correctly"""
    with patch.dict('os.environ', {'GLM_API_KEY': 'test-key'}):
        service = GLMService()
        assert service.api_key == 'test-key'
        assert service.base_url == "https://open.bigmodel.cn/api/paas/v4/"
        await service.close()


@pytest.mark.asyncio
async def test_glm_message_model():
    """Test GLM message data model"""
    message = GLMMessage(
        role="user",
        content="Test message"
    )
    assert message.role == "user"
    assert message.content == "Test message"


@pytest.mark.asyncio
async def test_glm_request_model():
    """Test GLM request data model"""
    messages = [
        GLMMessage(role="system", content="You are helpful"),
        GLMMessage(role="user", content="Hello")
    ]
    request = GLMRequest(messages=messages)

    assert request.model == "glm-4-plus"
    assert request.temperature == 0.7
    assert request.top_p == 0.9
    assert request.max_tokens == 2000
    assert len(request.messages) == 2


@pytest.mark.asyncio
@patch('services.glm_service.httpx.AsyncClient')
async def test_chat_method_success(mock_client_class):
    """Test successful chat request"""
    # Mock successful API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": "Test response from GLM"
            }
        }]
    }
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client

    with patch.dict('os.environ', {'GLM_API_KEY': 'test-key'}):
        service = GLMService()
        service.client = mock_client

        messages = [
            GLMMessage(role="user", content="Hello")
        ]

        response = await service.chat(messages)

        assert response == "Test response from GLM"
        mock_client.post.assert_called_once()

        # Verify request format
        call_args = mock_client.post.call_args
        assert "chat/completions" in call_args[0][0]
        request_data = call_args[1]['json']
        assert request_data['model'] == 'glm-4-plus'
        assert len(request_data['messages']) == 1

        await service.close()


@pytest.mark.asyncio
@patch('services.glm_service.httpx.AsyncClient')
async def test_generate_strategy_method(mock_client_class):
    """Test strategy generation with system prompt"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": "# Strategy Code\nimport pandas as pd\n..."
            }
        }]
    }
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client

    with patch.dict('os.environ', {'GLM_API_KEY': 'test-key'}):
        service = GLMService()
        service.client = mock_client

        result = await service.generate_strategy("moving average crossover")

        assert "# Strategy Code" in result
        assert "import pandas" in result

        # Verify system prompt was included
        call_args = mock_client.post.call_args
        request_data = call_args[1]['json']
        messages = request_data['messages']

        system_msg = next(m for m in messages if m['role'] == 'system')
        assert 'quantitative trading' in system_msg['content'].lower()
        assert 'jupyter notebook' in system_msg['content'].lower()

        user_msg = next(m for m in messages if m['role'] == 'user')
        assert 'moving average crossover' in user_msg['content']

        await service.close()


@pytest.mark.asyncio
@patch('services.glm_service.httpx.AsyncClient')
async def test_api_error_handling(mock_client_class):
    """Test error handling for API failures"""
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = Exception("Unauthorized")

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client

    with patch.dict('os.environ', {'GLM_API_KEY': 'test-key'}):
        service = GLMService()
        service.client = mock_client

        messages = [GLMMessage(role="user", content="Test")]

        with pytest.raises(Exception) as exc_info:
            await service.chat(messages)

        assert "Unauthorized" in str(exc_info.value)
        await service.close()


@pytest.mark.asyncio
async def test_close_method():
    """Test service cleanup"""
    with patch.dict('os.environ', {'GLM_API_KEY': 'test-key'}):
        service = GLMService()
        await service.close()
        # Should not raise any errors

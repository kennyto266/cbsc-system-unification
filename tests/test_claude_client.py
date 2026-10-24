"""
Tests for Claude API Client

Test suite for ClaudeClient class with mocked API calls.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from cbsc_strategy_sdk.claude.client import (
    ClaudeClient,
    ModelType,
    TokenUsage,
    RateLimiter,
)
from cbsc_strategy_sdk.exceptions import (
    APIError,
    APIQuotaExceededError,
)


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response."""
    mock_response = Mock()
    mock_response.content = [Mock(text="Generated code here")]
    mock_response.usage = Mock(
        input_tokens=100,
        output_tokens=200,
    )
    return mock_response


@pytest.fixture
def client():
    """Create ClaudeClient instance for testing."""
    return ClaudeClient(
        api_key="test-key-123",
        model=ModelType.SONNET.value,
        max_tokens=4096,
        timeout=60,
    )


class TestRateLimiter:
    """Test rate limiting functionality."""

    def test_initial_state(self):
        """Test initial rate limiter state."""
        limiter = RateLimiter(
            requests_per_minute=50,
            tokens_per_minute=40000,
        )

        assert len(limiter.request_times) == 0
        assert len(limiter.token_usage) == 0

    def test_can_make_request(self):
        """Test request availability check."""
        limiter = RateLimiter(
            requests_per_minute=50,
            tokens_per_minute=40000,
        )

        assert limiter.can_make_request(1000) is True

    def test_request_counting(self):
        """Test request tracking."""
        limiter = RateLimiter(
            requests_per_minute=1,
            tokens_per_minute=10000,
        )

        # First request should be allowed
        assert limiter.can_make_request() is True
        limiter.record_request(1000)

        # Second request should be blocked
        assert limiter.can_make_request() is False

    def test_token_limiting(self):
        """Test token-based limiting."""
        limiter = RateLimiter(
            requests_per_minute=100,
            tokens_per_minute=5000,
        )

        # First request uses most of budget
        assert limiter.can_make_request(4000) is True
        limiter.record_request(4000)

        # Second request should be blocked
        assert limiter.can_make_request(2000) is False


class TestTokenUsage:
    """Test token usage tracking."""

    def test_initial_state(self):
        """Test initial token usage."""
        usage = TokenUsage()

        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.total_tokens == 0
        assert usage.total_requests == 0

    def test_total_calculation(self):
        """Test total tokens calculation."""
        usage = TokenUsage(
            input_tokens=1000,
            output_tokens=500,
        )

        assert usage.total_tokens == 1500


class TestClaudeClient:
    """Test Claude API client."""

    def test_initialization(self):
        """Test client initialization."""
        client = ClaudeClient(api_key="test-key")

        assert client.api_key == "test-key"
        assert client.model == ModelType.SONNET.value
        assert client.max_tokens == 4096
        assert isinstance(client.usage, TokenUsage)

    def test_custom_initialization(self):
        """Test client with custom parameters."""
        client = ClaudeClient(
            api_key="test-key",
            model=ModelType.HAIKU.value,
            max_tokens=2048,
            timeout=30,
        )

        assert client.model == ModelType.HAIKU.value
        assert client.max_tokens == 2048
        assert client.timeout == 30

    @patch("cbsc_strategy_sdk.claude.client.anthropic")
    def test_generate_sync(self, mock_anthropic, mock_anthropic_response, client):
        """Test synchronous code generation."""
        # Setup mock
        mock_sync_client = Mock()
        mock_sync_client.messages.create.return_value = mock_anthropic_response
        mock_anthropic.Anthropic.return_value = mock_sync_client

        # Test generation
        result = client.generate("Test prompt")

        assert result == "Generated code here"
        mock_sync_client.messages.create.assert_called_once()

    @patch("cbsc_strategy_sdk.claude.client.anthropic")
    def test_generate_with_system_prompt(self, mock_anthropic, mock_anthropic_response, client):
        """Test generation with custom system prompt."""
        mock_sync_client = Mock()
        mock_sync_client.messages.create.return_value = mock_anthropic_response
        mock_anthropic.Anthropic.return_value = mock_sync_client

        custom_system = "You are a custom assistant"
        result = client.generate(
            "Test prompt",
            system_prompt=custom_system,
        )

        assert result == "Generated code here"
        call_args = mock_sync_client.messages.create.call_args
        assert call_args[1]["system"] == custom_system

    @pytest.mark.asyncio
    @patch("cbsc_strategy_sdk.claude.client.anthropic")
    async def test_generate_async(self, mock_anthropic, mock_anthropic_response, client):
        """Test asynchronous code generation."""
        # Setup mock
        mock_async_client = AsyncMock()
        mock_async_client.messages.create = AsyncMock(return_value=mock_anthropic_response)
        mock_anthropic.AsyncAnthropic.return_value = mock_async_client

        # Patch the lazy-loaded client
        client._async_client = mock_async_client

        # Test generation
        result = await client.generate_async("Test prompt")

        assert result == "Generated code here"
        mock_async_client.messages.create.assert_called_once()

    def test_usage_tracking(self, client):
        """Test token usage tracking."""
        initial_usage = client.get_usage_stats()
        assert initial_usage.total_requests == 0

        # Simulate usage update
        client.usage.input_tokens = 1000
        client.usage.output_tokens = 500
        client.usage.total_requests = 1

        updated_usage = client.get_usage_stats()
        assert updated_usage.total_requests == 1
        assert updated_usage.total_tokens == 1500

    def test_reset_usage(self, client):
        """Test usage reset."""
        client.usage.input_tokens = 1000
        client.usage.total_requests = 5

        client.reset_usage()

        assert client.usage.input_tokens == 0
        assert client.usage.total_requests == 0

    def test_default_system_prompt(self, client):
        """Test default system prompt content."""
        prompt = client._default_system_prompt()

        assert "quantitative trading" in prompt.lower()
        assert "python" in prompt.lower()

    @patch("cbsc_strategy_sdk.claude.client.anthropic", None)
    def test_anthropic_not_available():
        """Test error when anthropic package not available."""
        with patch("cbsc_strategy_sdk.claude.client.ANTHROPIC_AVAILABLE", False):
            with pytest.raises(ImportError):
                ClaudeClient(api_key="test-key")


class TestClientErrors:
    """Test client error handling."""

    @patch("cbsc_strategy_sdk.claude.client.anthropic")
    def test_api_error_handling(self, mock_anthropic, client):
        """Test API error handling."""
        from anthropic import APIError as AnthropicAPIError

        mock_sync_client = Mock()
        mock_sync_client.messages.create.side_effect = AnthropicAPIError("API Error")
        mock_anthropic.Anthropic.return_value = mock_sync_client

        with pytest.raises(APIError):
            client.generate("Test prompt")

    @patch("cbsc_strategy_sdk.claude.client.anthropic")
    def test_rate_limit_error(self, mock_anthropic, client):
        """Test rate limit error handling."""
        from anthropic import RateLimitError

        mock_sync_client = Mock()
        mock_sync_client.messages.create.side_effect = RateLimitError("Rate limit exceeded")
        mock_anthropic.Anthropic.return_value = mock_sync_client

        with pytest.raises(APIQuotaExceededError):
            client.generate("Test prompt")

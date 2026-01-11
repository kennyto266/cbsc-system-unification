"""
Claude API Client Wrapper

Async Anthropic API client with rate limiting, token management,
and error handling for CBSC strategy code generation.
"""

import asyncio
import time
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum

try:
    import anthropic
    from anthropic import Anthropic, AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from cbsc_strategy_sdk.exceptions import (
    ValidationError,
    APIError,
    APIQuotaExceededError,
)


class ModelType(Enum):
    """Available Claude models for code generation."""
    HAIKU = "claude-3-5-haiku-20241022"
    SONNET = "claude-3-5-sonnet-20241022"
    OPUS = "claude-3-5-opus-20241022"


@dataclass
class TokenUsage:
    """Track token usage for API calls."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_requests: int = 0
    total_cost_usd: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class RateLimiter:
    """Rate limiter for API calls."""
    requests_per_minute: int = 50
    tokens_per_minute: int = 40000
    window_seconds: int = 60

    request_times: list = field(default_factory=list)
    token_usage: list = field(default_factory=list)

    def can_make_request(self, estimated_tokens: int = 1000) -> bool:
        """Check if request is allowed under rate limits."""
        now = time.time()

        # Clean old entries outside window
        cutoff = now - self.window_seconds
        self.request_times = [t for t in self.request_times if t > cutoff]
        self.token_usage = [(t, tokens) for t, tokens in self.token_usage if t > cutoff]

        # Check request limit
        if len(self.request_times) >= self.requests_per_minute:
            return False

        # Check token limit
        window_tokens = sum(tokens for _, tokens in self.token_usage)
        if window_tokens + estimated_tokens > self.tokens_per_minute:
            return False

        return True

    def record_request(self, tokens_used: int):
        """Record a request for rate limiting."""
        self.request_times.append(time.time())
        self.token_usage.append((time.time(), tokens_used))

    async def acquire_slot(self, estimated_tokens: int = 1000, timeout: float = 60.0):
        """Wait for available rate limit slot."""
        start = time.time()

        while not self.can_make_request(estimated_tokens):
            if time.time() - start > timeout:
                raise APIQuotaExceededError("Rate limit timeout")

            # Wait before retrying
            await asyncio.sleep(0.5)

        self.record_request(estimated_tokens)


class ClaudeClient:
    """
    Async Anthropic API client wrapper with rate limiting.

    Handles communication with Anthropic's Claude API for code generation,
    with built-in rate limiting and token tracking.

    Args:
        api_key: Anthropic API key
        model: Claude model to use
        max_tokens: Maximum tokens per response
        timeout: Request timeout in seconds
        rpm_limit: Requests per minute limit
        tpm_limit: Tokens per minute limit

    Example:
        >>> client = ClaudeClient(api_key="sk-ant-...")
        >>> response = await client.generate_async(
        ...     "Generate a trading strategy",
        ...     system_prompt="You are a quant expert"
        ... )
        >>> print(response.content)
    """

    def __init__(
        self,
        api_key: str,
        model: str = ModelType.SONNET.value,
        max_tokens: int = 4096,
        timeout: int = 60,
        rpm_limit: int = 50,
        tpm_limit: int = 40000,
    ):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package is required. "
                "Install with: pip install anthropic>=0.18.0"
            )

        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.rate_limiter = RateLimiter(
            requests_per_minute=rpm_limit,
            tokens_per_minute=tpm_limit
        )
        self.usage = TokenUsage()

        # Initialize async client
        self._async_client: Optional[AsyncAnthropic] = None
        self._sync_client: Optional[Anthropic] = None

    @property
    def async_client(self) -> AsyncAnthropic:
        """Lazy initialization of async client."""
        if self._async_client is None:
            self._async_client = AsyncAnthropic(
                api_key=self.api_key,
                timeout=self.timeout,
            )
        return self._async_client

    @property
    def sync_client(self) -> Anthropic:
        """Lazy initialization of sync client."""
        if self._sync_client is None:
            self._sync_client = Anthropic(
                api_key=self.api_key,
                timeout=self.timeout,
            )
        return self._sync_client

    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate code asynchronously using Claude API.

        Args:
            prompt: User prompt for code generation
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Override max tokens for this request

        Returns:
            Generated text response

        Raises:
            APIQuotaExceededError: If rate limit exceeded
            APIError: If API call fails
        """
        # Estimate tokens for rate limiting (rough approximation)
        estimated_tokens = len(prompt.split()) * 1.3 + 100

        # Wait for rate limit slot
        await self.rate_limiter.acquire_slot(estimated_tokens)

        try:
            response = await self.async_client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature,
                system=system_prompt or self._default_system_prompt(),
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )

            # Extract content from response
            content = response.content[0].text

            # Update usage tracking
            self.usage.input_tokens += response.usage.input_tokens
            self.usage.output_tokens += response.usage.output_tokens
            self.usage.total_requests += 1

            # Update actual token usage in rate limiter
            self.rate_limiter.record_request(
                response.usage.input_tokens + response.usage.output_tokens
            )

            return content

        except anthropic.RateLimitError as e:
            raise APIQuotaExceededError(f"Rate limit exceeded: {e}")
        except anthropic.APIError as e:
            raise APIError(f"Claude API error: {e}")
        except Exception as e:
            raise APIError(f"Unexpected error: {e}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate code synchronously using Claude API.

        Args:
            prompt: User prompt for code generation
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Override max tokens for this request

        Returns:
            Generated text response
        """
        # Estimate tokens for rate limiting
        estimated_tokens = len(prompt.split()) * 1.3 + 100

        # Use asyncio for rate limiting in sync context
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Wait for rate limit slot
        loop.run_until_complete(
            self.rate_limiter.acquire_slot(estimated_tokens)
        )

        try:
            response = self.sync_client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature,
                system=system_prompt or self._default_system_prompt(),
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )

            content = response.content[0].text

            # Update usage tracking
            self.usage.input_tokens += response.usage.input_tokens
            self.usage.output_tokens += response.usage.output_tokens
            self.usage.total_requests += 1

            # Record actual token usage
            self.rate_limiter.record_request(
                response.usage.input_tokens + response.usage.output_tokens
            )

            return content

        except anthropic.RateLimitError as e:
            raise APIQuotaExceededError(f"Rate limit exceeded: {e}")
        except anthropic.APIError as e:
            raise APIError(f"Claude API error: {e}")
        except Exception as e:
            raise APIError(f"Unexpected error: {e}")

    def _default_system_prompt(self) -> str:
        """Default system prompt for code generation."""
        return """You are an expert quantitative trading strategy developer specializing in Python.

Your role is to generate clean, well-documented, and executable trading strategy code following CBSC best practices.

Code standards:
- Use type hints for all function signatures
- Include comprehensive docstrings
- Follow PEP 8 formatting
- Import required libraries (pandas, numpy, etc.)
- Handle edge cases and errors gracefully
- Provide clear comments for complex logic

Generated code should be:
- Syntactically correct Python
- Immediately executable
- Well-structured and maintainable
- Following modern Python patterns (dataclasses, type hints, etc.)"""

    def get_usage_stats(self) -> TokenUsage:
        """Get current token usage statistics."""
        return self.usage

    def reset_usage(self):
        """Reset token usage tracking."""
        self.usage = TokenUsage()

    def is_available(self) -> bool:
        """Check if Anthropic API is available."""
        if not ANTHROPIC_AVAILABLE:
            return False

        try:
            # Try a minimal API call
            response = self.sync_client.messages.create(
                model=ModelType.HAIKU.value,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return True
        except Exception:
            return False


# Convenience function for quick testing
def test_connection(api_key: str) -> bool:
    """Test connection to Anthropic API."""
    try:
        client = ClaudeClient(api_key=api_key)
        return client.is_available()
    except Exception:
        return False

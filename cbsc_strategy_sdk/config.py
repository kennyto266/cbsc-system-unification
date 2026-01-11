"""
Configuration management for CBSC Strategy SDK.

This module provides WorkspaceConfig class for managing SDK settings
with environment variable support and validation using Pydantic.
"""

from typing import Any, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import ConfigurationError


class WorkspaceConfig(BaseSettings):
    """Configuration for StrategyWorkspace.

    This class manages SDK configuration with support for:
    - Environment variables with CBSC_ prefix
    - Type validation and conversion
    - Default values
    - Runtime configuration updates

    Environment Variables:
        CBSC_API_BASE: Base URL for CBSC backend API (default: http://localhost:3003)
        CBSC_CACHE_TTL: Cache time-to-live in seconds (default: 300)
        CBSC_TIMEOUT: HTTP request timeout in seconds (default: 30)
        CBSC_MAX_RETRIES: Maximum retry attempts for failed requests (default: 3)

    Example:
        # Load from environment variables
        config = WorkspaceConfig()

        # Override specific values
        config = WorkspaceConfig(api_base="https://api.example.com")

        # Use with context
        with WorkspaceConfig(api_base="http://localhost:3003") as config:
            workspace = StrategyWorkspace(config=config)
    """

    # Core settings
    api_base: str = Field(
        default="http://localhost:3003",
        description="Base URL for CBSC backend API",
    )

    cache_ttl: int = Field(
        default=300,
        ge=0,
        le=86400,
        description="Cache time-to-live in seconds (0 = disabled)",
    )

    timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="HTTP request timeout in seconds",
    )

    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retry attempts for failed requests",
    )

    # Optional advanced settings
    connection_pool_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum size of HTTP connection pool",
    )

    enable_cache: bool = Field(
        default=True,
        description="Enable or disable data caching",
    )

    cache_max_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of cached items",
    )

    model_config = SettingsConfigDict(
        env_prefix="CBSC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("api_base")
    @classmethod
    def validate_api_base(cls, v: str) -> str:
        """Validate and normalize API base URL.

        Args:
            v: The API base URL to validate

        Returns:
            Normalized URL without trailing slash

        Raises:
            ValueError: If URL format is invalid
        """
        if not v:
            raise ValueError("API base URL cannot be empty")

        # Remove trailing slash for consistency
        v = v.rstrip("/")

        # Basic URL format validation
        if not v.startswith(("http://", "https://")):
            raise ValueError(
                f"API base URL must start with http:// or https://, got: {v}"
            )

        return v

    @field_validator("cache_ttl")
    @classmethod
    def validate_cache_ttl(cls, v: int) -> int:
        """Validate cache TTL value.

        Args:
            v: Cache TTL in seconds

        Returns:
            Validated cache TTL

        Raises:
            ValueError: If TTL is negative or too large
        """
        if v < 0:
            raise ValueError("Cache TTL cannot be negative")
        if v > 86400:
            raise ValueError("Cache TTL cannot exceed 24 hours (86400 seconds)")
        return v

    def get_api_url(self, path: str) -> str:
        """Build full API URL for a given endpoint path.

        Args:
            path: Endpoint path (e.g., "/api/data/symbols")

        Returns:
            Complete URL with base and path

        Example:
            config = WorkspaceConfig()
            url = config.get_api_url("/api/data/symbols")
            # Returns: "http://localhost:3003/api/data/symbols"
        """
        # Ensure path starts with /
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.api_base}{path}"

    def get_timeout_ms(self) -> int:
        """Get timeout in milliseconds for httpx.

        Returns:
            Timeout value in milliseconds
        """
        return self.timeout * 1000

    def is_cache_enabled(self) -> bool:
        """Check if caching is enabled.

        Returns:
            True if both enable_cache is True and cache_ttl > 0
        """
        return self.enable_cache and self.cache_ttl > 0

    def update(self, **kwargs) -> "WorkspaceConfig":
        """Create a new config with updated values.

        This method creates a copy of the current configuration
        with specified fields updated, useful for testing or
        temporary configuration changes.

        Args:
            **kwargs: Field names and new values

        Returns:
            New WorkspaceConfig instance with updated values

        Example:
            config = WorkspaceConfig()
            test_config = config.update(timeout=5, cache_ttl=0)
        """
        # Get current field values
        current_values = self.model_dump()

        # Update with new values
        current_values.update(kwargs)

        # Create new instance
        return WorkspaceConfig(**current_values)

    def validate(self) -> None:
        """Validate configuration and raise ConfigurationError if invalid.

        This method performs additional validation beyond Pydantic's
        built-in validation, checking for logical consistency.

        Raises:
            ConfigurationError: If configuration is invalid

        Example:
            config = WorkspaceConfig()
            try:
                config.validate()
            except ConfigurationError as e:
                print(f"Invalid config: {e}")
        """
        # Check if API base is accessible (basic DNS check)
        # This is optional and may be skipped in some environments
        # For now, we just validate the format which is done in field_validator

        # Check cache configuration consistency
        if self.enable_cache and self.cache_ttl == 0:
            raise ConfigurationError(
                "Cache is enabled but cache_ttl is 0 (disabled)",
                parameter="cache_ttl",
                value=str(self.cache_ttl),
            )

        # Check retry configuration
        if self.max_retries > 0 and self.timeout < 5:
            raise ConfigurationError(
                "Timeout too low for retries (should be >= 5 seconds when max_retries > 0)",
                parameter="timeout",
                value=str(self.timeout),
            )

    def model_post_init(self, __context: object) -> None:
        """Perform post-initialization validation."""
        try:
            self.validate()
        except ConfigurationError:
            # Re-raise ConfigurationError as-is
            raise
        except Exception as e:
            # Wrap other exceptions
            raise ConfigurationError(
                f"Configuration validation failed: {str(e)}",
                details={"original_error": str(e)},
            )

    def __repr__(self) -> str:
        """Return simplified representation (hide sensitive data if any)."""
        return (
            f"WorkspaceConfig(api_base='{self.api_base}', "
            f"cache_ttl={self.cache_ttl}, timeout={self.timeout}, "
            f"max_retries={self.max_retries})"
        )


# Convenience function for quick config creation
def create_config(
    api_base: Optional[str] = None,
    cache_ttl: Optional[int] = None,
    timeout: Optional[int] = None,
    max_retries: Optional[int] = None,
) -> WorkspaceConfig:
    """Create WorkspaceConfig with specified overrides.

    This helper function allows creating configuration with
    selective overrides while loading other values from
    environment variables.

    Args:
        api_base: Override API base URL
        cache_ttl: Override cache TTL
        timeout: Override timeout value
        max_retries: Override max retries

    Returns:
        Configured WorkspaceConfig instance

    Example:
        # Load from env, override API base
        config = create_config(api_base="https://api.example.com")
    """
    kwargs = {}
    if api_base is not None:
        kwargs["api_base"] = api_base
    if cache_ttl is not None:
        kwargs["cache_ttl"] = cache_ttl
    if timeout is not None:
        kwargs["timeout"] = timeout
    if max_retries is not None:
        kwargs["max_retries"] = max_retries

    return WorkspaceConfig(**kwargs)

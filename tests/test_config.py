"""
Unit tests for WorkspaceConfig.

Tests configuration validation, environment variable loading,
and helper methods.
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from cbsc_strategy_sdk.config import WorkspaceConfig, create_config
from cbsc_strategy_sdk.exceptions import ConfigurationError


class TestWorkspaceConfigDefaults:
    """Test default configuration values."""

    def test_default_api_base(self):
        """Test default API base URL."""
        config = WorkspaceConfig()
        assert config.api_base == "http://localhost:3003"

    def test_default_cache_ttl(self):
        """Test default cache TTL."""
        config = WorkspaceConfig()
        assert config.cache_ttl == 300

    def test_default_timeout(self):
        """Test default timeout."""
        config = WorkspaceConfig()
        assert config.timeout == 30

    def test_default_max_retries(self):
        """Test default max retries."""
        config = WorkspaceConfig()
        assert config.max_retries == 3

    def test_default_enable_cache(self):
        """Test default cache enabled."""
        config = WorkspaceConfig()
        assert config.enable_cache is True

    def test_default_cache_max_size(self):
        """Test default cache max size."""
        config = WorkspaceConfig()
        assert config.cache_max_size == 100


class TestWorkspaceConfigValidation:
    """Test configuration validation rules."""

    def test_api_base_with_trailing_slash(self):
        """Test trailing slash is removed from API base."""
        config = WorkspaceConfig(api_base="http://localhost:3003/")
        assert config.api_base == "http://localhost:3003"

    def test_api_base_with_multiple_trailing_slashes(self):
        """Test multiple trailing slashes are removed."""
        config = WorkspaceConfig(api_base="http://localhost:3003///")
        assert config.api_base == "http://localhost:3003"

    def test_api_base_must_start_with_http(self):
        """Test API base must start with http:// or https://."""
        with pytest.raises(ValidationError) as exc_info:
            WorkspaceConfig(api_base="ftp://localhost:3003")
        assert "must start with http:// or https://" in str(exc_info.value)

    def test_api_base_cannot_be_empty(self):
        """Test API base cannot be empty string."""
        with pytest.raises(ValidationError) as exc_info:
            WorkspaceConfig(api_base="")
        assert "cannot be empty" in str(exc_info.value)

    def test_cache_ttl_negative_rejected(self):
        """Test negative cache TTL is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkspaceConfig(cache_ttl=-1)
        assert "cannot be negative" in str(exc_info.value)

    def test_cache_ttl_exceeds_max(self):
        """Test cache TTL exceeding 24 hours is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkspaceConfig(cache_ttl=86401)
        assert "cannot exceed 24 hours" in str(exc_info.value)

    def test_cache_ttl_zero_allowed(self):
        """Test cache TTL of 0 is allowed (disables cache)."""
        config = WorkspaceConfig(cache_ttl=0)
        assert config.cache_ttl == 0

    def test_timeout_minimum_value(self):
        """Test timeout minimum value."""
        with pytest.raises(ValidationError):
            WorkspaceConfig(timeout=0)
        config = WorkspaceConfig(timeout=1)
        assert config.timeout == 1

    def test_timeout_maximum_value(self):
        """Test timeout maximum value."""
        with pytest.raises(ValidationError):
            WorkspaceConfig(timeout=301)
        config = WorkspaceConfig(timeout=300)
        assert config.timeout == 300

    def test_max_retries_range(self):
        """Test max retries valid range."""
        config = WorkspaceConfig(max_retries=0)
        assert config.max_retries == 0
        config = WorkspaceConfig(max_retries=10)
        assert config.max_retries == 10
        with pytest.raises(ValidationError):
            WorkspaceConfig(max_retries=11)


class TestWorkspaceConfigEnvironmentVariables:
    """Test environment variable loading."""

    @patch.dict(os.environ, {"CBSC_API_BASE": "https://api.example.com"})
    def test_load_api_base_from_env(self):
        """Test loading API base from environment variable."""
        config = WorkspaceConfig()
        assert config.api_base == "https://api.example.com"

    @patch.dict(os.environ, {"CBSC_CACHE_TTL": "600"})
    def test_load_cache_ttl_from_env(self):
        """Test loading cache TTL from environment variable."""
        config = WorkspaceConfig()
        assert config.cache_ttl == 600

    @patch.dict(os.environ, {"CBSC_TIMEOUT": "60"})
    def test_load_timeout_from_env(self):
        """Test loading timeout from environment variable."""
        config = WorkspaceConfig()
        assert config.timeout == 60

    @patch.dict(os.environ, {"CBSC_MAX_RETRIES": "5"})
    def test_load_max_retries_from_env(self):
        """Test loading max retries from environment variable."""
        config = WorkspaceConfig()
        assert config.max_retries == 5

    @patch.dict(os.environ, {
        "CBSC_API_BASE": "https://api.example.com",
        "CBSC_CACHE_TTL": "600",
        "CBSC_TIMEOUT": "60"
    })
    def test_load_multiple_from_env(self):
        """Test loading multiple values from environment."""
        config = WorkspaceConfig()
        assert config.api_base == "https://api.example.com"
        assert config.cache_ttl == 600
        assert config.timeout == 60

    @patch.dict(os.environ, {"CBSC_API_BASE": "https://env.com"})
    def test_constructor_overrides_env(self):
        """Test constructor values override environment variables."""
        config = WorkspaceConfig(api_base="https://override.com")
        assert config.api_base == "https://override.com"


class TestWorkspaceConfigHelperMethods:
    """Test WorkspaceConfig helper methods."""

    def test_get_api_url_with_leading_slash(self):
        """Test get_api_url with path starting with slash."""
        config = WorkspaceConfig(api_base="http://localhost:3003")
        url = config.get_api_url("/api/data/symbols")
        assert url == "http://localhost:3003/api/data/symbols"

    def test_get_api_url_without_leading_slash(self):
        """Test get_api_url adds leading slash if missing."""
        config = WorkspaceConfig(api_base="http://localhost:3003")
        url = config.get_api_url("api/data/symbols")
        assert url == "http://localhost:3003/api/data/symbols"

    def test_get_timeout_ms(self):
        """Test get_timeout_ms converts seconds to milliseconds."""
        config = WorkspaceConfig(timeout=30)
        assert config.get_timeout_ms() == 30000

    def test_is_cache_enabled_with_cache_enabled(self):
        """Test is_cache_enabled returns True when cache enabled."""
        config = WorkspaceConfig(enable_cache=True, cache_ttl=300)
        assert config.is_cache_enabled() is True

    def test_is_cache_enabled_disabled(self):
        """Test is_cache_enabled returns False when disabled."""
        config = WorkspaceConfig(enable_cache=False)
        assert config.is_cache_enabled() is False

    def test_is_cache_enabled_zero_ttl(self):
        """Test is_cache_enabled returns False when TTL is 0."""
        config = WorkspaceConfig(enable_cache=True, cache_ttl=0)
        assert config.is_cache_enabled() is False


class TestWorkspaceConfigUpdate:
    """Test config update method."""

    def test_update_single_field(self):
        """Test updating a single field."""
        config = WorkspaceConfig()
        updated = config.update(timeout=60)
        assert updated.timeout == 60
        assert updated.api_base == config.api_base
        assert updated.cache_ttl == config.cache_ttl

    def test_update_multiple_fields(self):
        """Test updating multiple fields."""
        config = WorkspaceConfig()
        updated = config.update(timeout=60, cache_ttl=600)
        assert updated.timeout == 60
        assert updated.cache_ttl == 600

    def test_update_creates_new_instance(self):
        """Test update creates new instance, doesn't modify original."""
        config = WorkspaceConfig(timeout=30)
        updated = config.update(timeout=60)
        assert config.timeout == 30
        assert updated.timeout == 60
        assert config is not updated

    def test_update_preserves_validation(self):
        """Test update still validates new values."""
        config = WorkspaceConfig()
        with pytest.raises(ValidationError):
            config.update(cache_ttl=-1)


class TestWorkspaceConfigValidate:
    """Test validate method for cross-field validation."""

    def test_validate_cache_consistency(self):
        """Test validate checks cache consistency."""
        config = WorkspaceConfig(enable_cache=True, cache_ttl=0)
        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()
        assert "Cache is enabled but cache_ttl is 0" in str(exc_info.value)

    def test_validate_retry_timeout_consistency(self):
        """Test validate checks retry and timeout consistency."""
        config = WorkspaceConfig(max_retries=5, timeout=2)
        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()
        assert "Timeout too low for retries" in str(exc_info.value)

    def test_validate_passes_with_good_config(self):
        """Test validate passes with valid configuration."""
        config = WorkspaceConfig()
        config.validate()  # Should not raise

    def test_model_post_init_calls_validate(self):
        """Test model_post_init calls validate automatically."""
        with pytest.raises(ConfigurationError):
            WorkspaceConfig(enable_cache=True, cache_ttl=0)


class TestWorkspaceConfigRepr:
    """Test string representation."""

    def test_repr_contains_key_fields(self):
        """Test repr includes key configuration fields."""
        config = WorkspaceConfig(api_base="http://localhost:3003", cache_ttl=600)
        repr_str = repr(config)
        assert "WorkspaceConfig" in repr_str
        assert "http://localhost:3003" in repr_str
        assert "cache_ttl=600" in repr_str


class TestCreateConfig:
    """Test create_config convenience function."""

    def test_create_config_with_no_args(self):
        """Test create_config with default values."""
        config = create_config()
        assert config.api_base == "http://localhost:3003"
        assert config.cache_ttl == 300

    def test_create_config_with_api_base(self):
        """Test create_config with API base override."""
        config = create_config(api_base="https://api.example.com")
        assert config.api_base == "https://api.example.com"

    def test_create_config_with_multiple_overrides(self):
        """Test create_config with multiple overrides."""
        config = create_config(
            api_base="https://api.example.com",
            cache_ttl=600,
            timeout=60
        )
        assert config.api_base == "https://api.example.com"
        assert config.cache_ttl == 600
        assert config.timeout == 60

    def test_create_config_none_values_not_applied(self):
        """Test None values don't override defaults."""
        config = create_config(api_base=None)
        assert config.api_base == "http://localhost:3003"

    @patch.dict(os.environ, {"CBSC_API_BASE": "https://env.com"})
    def test_create_config_respects_env(self):
        """Test create_config loads from environment."""
        config = create_config()
        assert config.api_base == "https://env.com"

    @patch.dict(os.environ, {"CBSC_API_BASE": "https://env.com"})
    def test_create_config_override_env(self):
        """Test create_config override environment value."""
        config = create_config(api_base="https://override.com")
        assert config.api_base == "https://override.com"

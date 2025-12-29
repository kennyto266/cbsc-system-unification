"""Test that the SDK can be imported successfully."""

import pytest


def test_import_sdk():
    """Test that the main SDK can be imported."""
    import cbsc_trading_api
    assert cbsc_trading_api.__version__ == "1.0.0"
    assert cbsc_trading_api.CBSCClient is not None


def test_import_client():
    """Test that the client can be imported."""
    from cbsc_trading_api import CBSCClient, AsyncCBSCClient
    assert CBSCClient is not None
    assert AsyncCBSCClient is not None


def test_import_exceptions():
    """Test that exceptions can be imported."""
    from cbsc_trading_api import (
        CBSCAPIError,
        AuthenticationError,
        RateLimitError,
        NotFoundError,
        ValidationError,
        ServerError,
    )
    assert CBSCAPIError is not None
    assert AuthenticationError is not None
    assert RateLimitError is not None
    assert NotFoundError is not None
    assert ValidationError is not None
    assert ServerError is not None


def test_import_models():
    """Test that models can be imported."""
    from cbsc_trading_api import (
        TokenResponse,
        User,
        Strategy,
        Portfolio,
        APIResponse,
    )
    assert TokenResponse is not None
    assert User is not None
    assert Strategy is not None
    assert Portfolio is not None
    assert APIResponse is not None


def test_client_instantiation():
    """Test that the client can be instantiated."""
    from cbsc_trading_api import CBSCClient

    # Test with no auth
    client = CBSCClient()
    assert client.base_url == "https://api.cbsc.com"
    assert client.client_id is None
    assert client.client_secret is None

    # Test with custom base URL
    client = CBSCClient(base_url="https://test.api.cbsc.com")
    assert client.base_url == "https://test.api.cbsc.com"

    # Test with credentials
    client = CBSCClient(
        client_id="test_id",
        client_secret="test_secret",
        base_url="https://test.api.cbsc.com"
    )
    assert client.client_id == "test_id"
    assert client.client_secret == "test_secret"
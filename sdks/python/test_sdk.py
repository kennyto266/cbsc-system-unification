#!/usr/bin/env python3
"""
Test script to verify CBSC Trading API Python SDK
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Test that the SDK can be imported"""
    try:
        import cbsc_trading_api
        print("✓ Successfully imported cbsc_trading_api")

        # Check main classes
        from cbsc_trading_api import CBSCClient
        print("✓ Successfully imported CBSCClient")

        from cbsc_trading_api import TokenResponse, User, Strategy
        print("✓ Successfully imported models")

        from cbsc_trading_api.exceptions import CBSCAPIError, AuthenticationError
        print("✓ Successfully imported exceptions")

        # Check version
        print(f"✓ SDK version: {cbsc_trading_api.__version__}")

        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_client_creation():
    """Test that a client can be created"""
    try:
        from cbsc_trading_api import CBSCClient

        # Create client with dummy credentials
        client = CBSCClient(
            base_url="http://localhost:3005",
            client_id="test",
            client_secret="test"
        )
        print("✓ Successfully created CBSCClient")

        # Check that resources are available
        assert hasattr(client, 'auth')
        assert hasattr(client, 'users')
        assert hasattr(client, 'strategies')
        assert hasattr(client, 'portfolio')
        assert hasattr(client, 'market_data')
        assert hasattr(client, 'backtests')
        assert hasattr(client, 'webhooks')
        print("✓ All API resources are available")

        client.close()
        return True
    except Exception as e:
        print(f"✗ Client creation error: {e}")
        return False

def test_models():
    """Test that models can be created"""
    try:
        from cbsc_trading_api.models import (
            TokenResponse, UserCreate, StrategyCreate,
            WebhookCreate, APIResponse
        )
        from cbsc_trading_api.models import StrategyType, WebhookEventType

        # Test TokenResponse
        token = TokenResponse(
            access_token="test_token",
            token_type="bearer",
            expires_in=3600
        )
        print("✓ TokenResponse model works")

        # Test UserCreate
        user = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        print("✓ UserCreate model works")

        # Test StrategyCreate
        strategy = StrategyCreate(
            name="Test Strategy",
            type=StrategyType.RSI,
            description="Test strategy",
            config={"param": "value"}
        )
        print("✓ StrategyCreate model works")

        # Test WebhookCreate
        webhook = WebhookCreate(
            url="https://example.com/webhook",
            events=[WebhookEventType.STRATEGY_CREATED]
        )
        print("✓ WebhookCreate model works")

        return True
    except Exception as e:
        print(f"✗ Model test error: {e}")
        return False

def main():
    """Run all tests"""
    print("=== CBSC Trading API Python SDK Test ===\n")

    tests = [
        ("Import Test", test_import),
        ("Client Creation Test", test_client_creation),
        ("Models Test", test_models),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        if test_func():
            passed += 1
        print()

    print(f"=== Test Results: {passed}/{total} passed ===")

    if passed == total:
        print("✓ All tests passed! Python SDK is working correctly.")
        return True
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
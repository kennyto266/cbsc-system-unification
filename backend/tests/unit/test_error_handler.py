"""
Unit tests for Error Handler.

Tests error classification, user messaging, and response formatting.
"""

import pytest
import traceback
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.error_handler import (
    CBAError,
    ErrorCategory,
    ErrorSeverity,
    NetworkError,
    APIRateLimitError,
    DatabaseError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ExternalServiceError,
    ErrorHandler,
    handle_exception
)


class TestCBAError:
    """Test CBAError base error class."""

    def test_basic_error_creation(self):
        """Test creating a basic CBAError."""
        error = CBAError("Something went wrong")

        assert error.message == "Something went wrong"
        assert error.category == ErrorCategory.UNKNOWN
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.error_id is not None
        assert len(error.error_id) == 36  # UUID format

    def test_error_with_category(self):
        """Test error with specific category."""
        error = CBAError(
            "Network failed",
            category=ErrorCategory.NETWORK
        )

        assert error.category == ErrorCategory.NETWORK

    def test_error_with_severity(self):
        """Test error with specific severity."""
        error = CBAError(
            "Critical failure",
            severity=ErrorSeverity.CRITICAL
        )

        assert error.severity == ErrorSeverity.CRITICAL

    def test_error_with_custom_user_message(self):
        """Test error with custom user message."""
        error = CBAError(
            "Internal error: DB connection failed",
            user_message="Unable to connect to database"
        )

        assert error.message == "Internal error: DB connection failed"
        assert error.user_message == "Unable to connect to database"

    def test_error_with_recovery_actions(self):
        """Test error with recovery actions."""
        actions = ["Check internet connection", "Try again later"]
        error = CBAError(
            "Network error",
            recovery_actions=actions
        )

        assert error.recovery_actions == actions

    def test_error_with_context(self):
        """Test error with additional context."""
        context = {"url": "https://api.example.com", "timeout": 30}
        error = CBAError(
            "API request failed",
            extra_context=context
        )

        assert error.context == context
        assert error.context["url"] == "https://api.example.com"

    def test_error_to_dict(self):
        """Test error serialization to dictionary."""
        error = CBAError(
            "Test error",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            user_message="Invalid input"
        )

        error_dict = error.to_dict()

        assert error_dict["message"] == "Test error"
        assert error_dict["category"] == "validation"
        assert error_dict["severity"] == "low"
        assert error_dict["user_message"] == "Invalid input"
        assert "error_id" in error_dict
        assert "timestamp" in error_dict

    def test_error_string_representation(self):
        """Test error string representation."""
        error = CBAError("Test message")
        error_str = str(error)

        assert "Test message" in error_str
        assert "CBAError" in error_str


class TestSpecializedErrors:
    """Test specialized error classes."""

    def test_network_error(self):
        """Test NetworkError class."""
        error = NetworkError("Connection refused")

        assert error.category == ErrorCategory.NETWORK
        assert error.user_message == "網絡連接失敗，請檢查您的網絡設置"
        assert "Check internet connection" in error.recovery_actions[0]

    def test_api_rate_limit_error(self):
        """Test APIRateLimitError class."""
        error = APIRateLimitError("Too many requests")

        assert error.category == ErrorCategory.API_RATE_LIMIT
        assert error.user_message == "API 調用次數超限，請稍後再試"
        assert "Wait a few minutes" in error.recovery_actions[0]

    def test_database_error(self):
        """Test DatabaseError class."""
        error = DatabaseError("Query failed")

        assert error.category == ErrorCategory.DATABASE
        assert error.user_message == "數據庫錯誤，請稍後重試"

    def test_validation_error(self):
        """Test ValidationError class."""
        error = ValidationError("Invalid email format")

        assert error.category == ErrorCategory.VALIDATION
        assert error.user_message == "輸入數據格式錯誤，請檢查後重試"

    def test_authentication_error(self):
        """Test AuthenticationError class."""
        error = AuthenticationError("Invalid credentials")

        assert error.category == ErrorCategory.AUTHENTICATION
        assert error.user_message == "身份驗證失敗，請重新登錄"

    def test_authorization_error(self):
        """Test AuthorizationError class."""
        error = AuthorizationError("Access denied")

        assert error.category == ErrorCategory.AUTHORIZATION
        assert error.user_message == "權限不足，無法執行此操作"

    def test_external_service_error(self):
        """Test ExternalServiceError class."""
        error = ExternalServiceError("yfinance API unavailable")

        assert error.category == ErrorCategory.EXTERNAL_SERVICE
        assert "External service unavailable" in error.user_message


class TestErrorHandler:
    """Test ErrorHandler class."""

    def test_classify_connection_error(self):
        """Test classification of connection errors."""
        handler = ErrorHandler()

        try:
            raise ConnectionError("Failed to connect")
        except Exception as e:
            cba_error = handler.classify(e)

            assert isinstance(cba_error, NetworkError)
            assert cba_error.category == ErrorCategory.NETWORK

    def test_classify_timeout_error(self):
        """Test classification of timeout errors."""
        handler = ErrorHandler()

        try:
            raise TimeoutError("Request timed out")
        except Exception as e:
            cba_error = handler.classify(e)

            assert isinstance(cba_error, NetworkError)
            assert cba_error.category == ErrorCategory.NETWORK

    def test_classify_value_error(self):
        """Test classification of value errors."""
        handler = ErrorHandler()

        try:
            raise ValueError("Invalid value")
        except Exception as e:
            cba_error = handler.classify(e)

            assert isinstance(cba_error, CBAError)
            assert cba_error.category == ErrorCategory.VALIDATION

    def test_classify_permission_error(self):
        """Test classification of permission errors."""
        handler = ErrorHandler()

        try:
            raise PermissionError("Access denied")
        except Exception as e:
            cba_error = handler.classify(e)

            assert cba_error.category == ErrorCategory.AUTHORIZATION

    def test_classify_unknown_error(self):
        """Test classification of unknown errors."""
        handler = ErrorHandler()

        try:
            raise RuntimeError("Unexpected error")
        except Exception as e:
            cba_error = handler.classify(e)

            assert isinstance(cba_error, CBAError)
            assert cba_error.category == ErrorCategory.UNKNOWN

    def test_handle_with_context(self):
        """Test handling error with context."""
        handler = ErrorHandler()

        try:
            raise ConnectionError("Failed to connect to API")
        except Exception as e:
            context = {"api": "yfinance", "url": "https://query2.finance.yahoo.com"}
            cba_error = handler.handle(e, extra_context=context)

            assert cba_error.context["api"] == "yfinance"
            assert cba_error.context["url"] == "https://query2.finance.yahoo.com"

    def test_get_recovery_actions_for_network(self):
        """Test getting recovery actions for network errors."""
        handler = ErrorHandler()
        error = NetworkError("Connection failed")

        actions = handler.get_recovery_actions(error)

        assert len(actions) > 0
        assert any("network" in action.lower() or "internet" in action.lower()
                   for action in actions)

    def test_get_recovery_actions_for_validation(self):
        """Test getting recovery actions for validation errors."""
        handler = ErrorHandler()
        error = ValidationError("Invalid input")

        actions = handler.get_recovery_actions(error)

        assert len(actions) > 0
        assert any("check" in action.lower() or "input" in action.lower()
                   for action in actions)


class TestHandleException:
    """Test handle_exception utility function."""

    def test_handle_basic_exception(self):
        """Test handling basic exception."""
        try:
            raise ValueError("Invalid value")
        except Exception as e:
            cba_error = handle_exception(e)

            assert isinstance(cba_error, CBAError)
            assert "Invalid value" in cba_error.message

    def test_handle_exception_with_context(self):
        """Test handling exception with additional context."""
        try:
            raise ConnectionError("Cannot connect")
        except Exception as e:
            cba_error = handle_exception(
                e,
                extra_context={"service": "database", "host": "localhost"}
            )

            assert cba_error.context["service"] == "database"
            assert cba_error.context["host"] == "localhost"

    def test_handle_exception_with_custom_user_message(self):
        """Test handling exception with custom user message."""
        try:
            raise TimeoutError("Request timeout")
        except Exception as e:
            cba_error = handle_exception(
                e,
                user_message="The request took too long"
            )

            assert cba_error.user_message == "The request took too long"

    def test_handle_exception_preserves_traceback(self):
        """Test that traceback is preserved."""
        try:
            def nested_function():
                raise ValueError("Nested error")

            nested_function()
        except Exception as e:
            cba_error = handle_exception(e)

            assert cba_error.traceback is not None
            assert "nested_function" in cba_error.traceback


class TestErrorSeverity:
    """Test error severity levels."""

    def test_low_severity_default(self):
        """Test that ValidationError has LOW severity."""
        error = ValidationError("Invalid input")

        assert error.severity == ErrorSeverity.LOW

    def test_high_severity_database(self):
        """Test that DatabaseError has HIGH severity."""
        error = DatabaseError("Database connection failed")

        assert error.severity == ErrorSeverity.HIGH

    def test_critical_severity_auth(self):
        """Test that AuthenticationError has MEDIUM severity."""
        error = AuthenticationError("Invalid credentials")

        assert error.severity == ErrorSeverity.MEDIUM


class TestErrorRecoveryActions:
    """Test error recovery action generation."""

    def test_network_error_recovery(self):
        """Test recovery actions for network errors."""
        error = NetworkError("Connection failed")

        actions = error.recovery_actions

        assert len(actions) > 0
        assert isinstance(actions, list)
        assert all(isinstance(action, str) for action in actions)

    def test_rate_limit_recovery(self):
        """Test recovery actions for rate limit errors."""
        error = APIRateLimitError("Rate limit exceeded")

        actions = error.recovery_actions

        assert len(actions) > 0
        assert any("wait" in action.lower() or "minute" in action.lower()
                   for action in actions)

    def test_custom_recovery_actions(self):
        """Test custom recovery actions override defaults."""
        custom_actions = ["Restart the application", "Contact support"]
        error = CBAError(
            "Custom error",
            recovery_actions=custom_actions
        )

        assert error.recovery_actions == custom_actions


class TestErrorResponseFormatting:
    """Test error response formatting for API responses."""

    def test_standard_response_format(self):
        """Test standard error response format."""
        error = CBAError(
            "Test error",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW
        )

        response = error.to_dict()

        # Check required fields
        assert "error_id" in response
        assert "category" in response
        assert "severity" in response
        assert "message" in response
        assert "user_message" in response
        assert "recovery_actions" in response
        assert "timestamp" in response

    def test_response_serializable(self):
        """Test that response is JSON serializable."""
        import json

        error = NetworkError("Connection failed")

        response = error.to_dict()

        # Should be able to serialize to JSON without errors
        json_str = json.dumps(response)
        assert isinstance(json_str, str)

    def test_response_with_context(self):
        """Test response formatting with context."""
        error = CBAError(
            "API error",
            extra_context={"endpoint": "/api/users", "method": "POST"}
        )

        response = error.to_dict()

        assert "context" in response
        assert response["context"]["endpoint"] == "/api/users"
        assert response["context"]["method"] == "POST"


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_empty_message(self):
        """Test error with empty message."""
        error = CBAError("")

        assert error.message == ""
        assert error.user_message is not None  # Should have default

    def test_none_context(self):
        """Test error with None context."""
        error = CBAError("Test", extra_context=None)

        # Should handle gracefully
        assert error.context is None or error.context == {}

    def test_unicode_in_message(self):
        """Test error with unicode characters."""
        error = CBAError("Error: 測試中文字符 🚀")

        assert "測試中文字符" in error.message
        assert "🚀" in error.message

    def test_very_long_message(self):
        """Test error with very long message."""
        long_message = "Error: " + "x" * 1000
        error = CBAError(long_message)

        assert len(error.message) == 1006  # "Error: " + 1000 chars

    def test_multiple_exception_types(self):
        """Test handling different exception types."""
        handler = ErrorHandler()

        exceptions_to_test = [
            (ConnectionError, ErrorCategory.NETWORK),
            (TimeoutError, ErrorCategory.NETWORK),
            (ValueError, ErrorCategory.VALIDATION),
            (PermissionError, ErrorCategory.AUTHORIZATION),
            (KeyError, ErrorCategory.UNKNOWN),
            (AttributeError, ErrorCategory.UNKNOWN),
        ]

        for exc_class, expected_category in exceptions_to_test:
            try:
                raise exc_class(f"Test {exc_class.__name__}")
            except Exception as e:
                cba_error = handler.classify(e)
                assert cba_error.category == expected_category, \
                    f"{exc_class.__name__} should map to {expected_category}"

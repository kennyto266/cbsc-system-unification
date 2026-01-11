"""
Custom exceptions for CBSC Strategy SDK.

This module defines the exception hierarchy used throughout the SDK
for consistent error handling and user-friendly error messages.
"""

from typing import Any, Optional


class StrategyWorkspaceError(Exception):
    """Base exception for all workspace-related errors.

    All custom exceptions in the SDK inherit from this base class,
    allowing users to catch all SDK errors with a single except clause.

    Example:
        try:
            workspace.get_historical_data("AAPL", start, end)
        except StrategyWorkspaceError as e:
            print(f"SDK error occurred: {e}")
    """

    def __init__(self, message: str, details: Optional[dict] = None):
        """Initialize the base exception.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return formatted error message."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class DataFetchError(StrategyWorkspaceError):
    """Raised when data retrieval operations fail.

    This exception is raised when the SDK cannot fetch data from
    the CBSC backend API, whether due to network issues, invalid
    parameters, or server errors.

    Example:
        try:
            data = workspace.get_historical_data("INVALID", start, end)
        except DataFetchError as e:
            print(f"Failed to fetch data: {e}")
    """

    def __init__(
        self,
        message: str,
        symbol: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[dict] = None,
    ):
        """Initialize data fetch error.

        Args:
            message: Error description
            symbol: Related trading symbol if applicable
            status_code: HTTP status code if API error
            details: Additional error context
        """
        error_details = details or {}
        if symbol:
            error_details["symbol"] = symbol
        if status_code:
            error_details["status_code"] = status_code
        super().__init__(message, error_details)
        self.symbol = symbol
        self.status_code = status_code


class APIConnectionError(StrategyWorkspaceError):
    """Raised when API connection cannot be established.

    This exception indicates network-level failures such as:
    - Cannot resolve host
    - Connection timeout
    - Connection refused
    - SSL/TLS errors

    Example:
        try:
            workspace = StrategyWorkspace(api_base="http://invalid:3003")
        except APIConnectionError as e:
            print(f"Cannot connect to API: {e}")
    """

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        timeout: Optional[float] = None,
        details: Optional[dict] = None,
    ):
        """Initialize API connection error.

        Args:
            message: Error description
            url: The URL that failed to connect
            timeout: Timeout value if applicable
            details: Additional error context
        """
        error_details = details or {}
        if url:
            error_details["url"] = url
        if timeout:
            error_details["timeout"] = timeout
        super().__init__(message, error_details)
        self.url = url
        self.timeout = timeout


class ConfigurationError(StrategyWorkspaceError):
    """Raised when workspace configuration is invalid.

    This exception is raised during initialization if the
    configuration parameters are invalid or conflicting.

    Example:
        try:
            config = WorkspaceConfig(cache_ttl=-1)  # Invalid
        except ConfigurationError as e:
            print(f"Invalid configuration: {e}")
    """

    def __init__(
        self,
        message: str,
        parameter: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[dict] = None,
    ):
        """Initialize configuration error.

        Args:
            message: Error description
            parameter: The invalid parameter name
            value: The invalid value
            details: Additional error context
        """
        error_details = details or {}
        if parameter:
            error_details["parameter"] = parameter
        if value is not None:
            error_details["value"] = str(value)
        super().__init__(message, error_details)
        self.parameter = parameter
        self.value = value

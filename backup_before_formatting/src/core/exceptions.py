"""
統一異常體系
Unified Exception System for Hong Kong Quantitative Trading System

This module provides a centralized exception hierarchy for better error handling,
debugging, and user experience across the entire trading system.
"""

from typing import Any, Dict, Optional
import traceback


class QuantSystemException(Exception):
    """Base exception for the entire quantitative trading system."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "cause": str(self.cause) if self.cause else None,
            "traceback": traceback.format_exc()
        }


# Data Related Exceptions
class DataAdapterError(QuantSystemException):
    """Exception raised for data adapter related errors."""
    pass


class DataValidationError(QuantSystemException):
    """Exception raised for data validation failures."""
    pass


class DataSourceError(QuantSystemException):
    """Exception raised when data sources are unavailable or corrupted."""
    pass


class DataProcessingError(QuantSystemException):
    """Exception raised during data processing operations."""
    pass


# Trading Related Exceptions
class TradingError(QuantSystemException):
    """Base exception for trading-related errors."""
    pass


class OrderExecutionError(TradingError):
    """Exception raised when order execution fails."""
    pass


class PortfolioError(TradingError):
    """Exception raised for portfolio management errors."""
    pass


class RiskManagementError(TradingError):
    """Exception raised for risk management violations."""
    pass


# Strategy and Backtesting Exceptions
class StrategyError(QuantSystemException):
    """Base exception for strategy-related errors."""
    pass


class BacktestError(StrategyError):
    """Exception raised during backtesting operations."""
    pass


class OptimizationError(StrategyError):
    """Exception raised during strategy optimization."""
    pass


class SignalGenerationError(StrategyError):
    """Exception raised during trading signal generation."""
    pass


# Technical Analysis Exceptions
class TechnicalIndicatorError(QuantSystemException):
    """Exception raised for technical indicator calculations."""
    pass


class IndicatorParameterError(TechnicalIndicatorError):
    """Exception raised for invalid indicator parameters."""
    pass


# API and Communication Exceptions
class APIError(QuantSystemException):
    """Base exception for API-related errors."""
    pass


class ValidationError(APIError):
    """Exception raised for API input validation failures."""
    pass


class AuthenticationError(APIError):
    """Exception raised for authentication failures."""
    pass


class RateLimitError(APIError):
    """Exception raised when API rate limits are exceeded."""
    pass


# Agent System Exceptions
class AgentError(QuantSystemException):
    """Base exception for agent system errors."""
    pass


class AgentCommunicationError(AgentError):
    """Exception raised for agent communication failures."""
    pass


class AgentConfigurationError(AgentError):
    """Exception raised for agent configuration issues."""
    pass


# Configuration and System Exceptions
class ConfigurationError(QuantSystemException):
    """Exception raised for configuration-related errors."""
    pass


class SystemInitializationError(QuantSystemException):
    """Exception raised during system initialization."""
    pass


class ResourceError(QuantSystemException):
    """Exception raised for resource allocation/access issues."""
    pass


# Performance and Monitoring Exceptions
class PerformanceError(QuantSystemException):
    """Exception raised for performance-related issues."""
    pass


class MonitoringError(QuantSystemException):
    """Exception raised during monitoring operations."""
    pass


# Utility Functions
def handle_exception(
    exception: Exception,
    context: Optional[str] = None,
    reraise: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Unified exception handler for consistent error responses.

    Args:
        exception: The exception to handle
        context: Additional context information
        reraise: Whether to reraise the exception

    Returns:
        Dictionary with exception details if not reraising
    """
    if isinstance(exception, QuantSystemException):
        error_dict = exception.to_dict()
    else:
        error_dict = {
            "error_type": exception.__class__.__name__,
            "message": str(exception),
            "error_code": None,
            "details": {"context": context} if context else {},
            "cause": None,
            "traceback": traceback.format_exc()
        }

    if context:
        error_dict["context"] = context

    if reraise:
        raise exception

    return error_dict


def create_error_response(
    error_type: str,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create standardized error response.

    Args:
        error_type: Type of error
        message: Error message
        error_code: Optional error code
        details: Additional error details

    Returns:
        Standardized error response dictionary
    """
    return {
        "success": False,
        "error": {
            "type": error_type,
            "message": message,
            "code": error_code,
            "details": details or {}
        }
    }


# Exception mapping for error codes
ERROR_CODE_MAP = {
    # Data errors (1000-1999)
    "DATA_001": DataValidationError,
    "DATA_002": DataSourceError,
    "DATA_003": DataProcessingError,

    # Trading errors (2000-2999)
    "TRADE_001": OrderExecutionError,
    "TRADE_002": PortfolioError,
    "TRADE_003": RiskManagementError,

    # Strategy errors (3000-3999)
    "STRAT_001": BacktestError,
    "STRAT_002": OptimizationError,
    "STRAT_003": SignalGenerationError,

    # API errors (4000-4999)
    "API_001": ValidationError,
    "API_002": AuthenticationError,
    "API_003": RateLimitError,

    # System errors (5000-5999)
    "SYS_001": ConfigurationError,
    "SYS_002": SystemInitializationError,
    "SYS_003": ResourceError,
}


def get_exception_class(error_code: str) -> type:
    """Get exception class from error code."""
    return ERROR_CODE_MAP.get(error_code, QuantSystemException)
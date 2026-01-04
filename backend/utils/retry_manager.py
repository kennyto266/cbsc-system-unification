"""
Retry manager with exponential backoff for external API calls.

Provides configurable retry logic with jitter, circuit breaker integration,
and comprehensive monitoring.
"""

import asyncio
import logging
import random
import time
from typing import Callable, TypeVar, Type, Any, Optional, List, Tuple
from functools import wraps
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from .error_handler import CBAError, ErrorCategory


# Configure logger
logger = logging.getLogger(__name__)


T = TypeVar('T')


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 5
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    exponential_base: float = 2.0  # Multiplier for exponential backoff
    jitter: bool = True  # Add randomness to delays
    jitter_factor: float = 0.1  # Jitter amount (0.1 = 10%)
    retryable_exceptions: Tuple[Type[Exception], ...] = (
        ConnectionError,
        TimeoutError,
        OSError,
    )

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given attempt using exponential backoff with jitter.

        Args:
            attempt: The attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )

        # Add jitter if enabled
        if self.jitter:
            jitter_range = delay * self.jitter_factor
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)


@dataclass
class RetryStats:
    """Statistics for retry attempts."""
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    total_delay: float = 0.0
    last_attempt_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    attempt_history: List[dict] = field(default_factory=list)

    def record_attempt(self, attempt: int, success: bool, delay: float, error: Optional[Exception] = None):
        """Record an attempt for monitoring."""
        self.total_attempts += 1
        self.total_delay += delay
        self.last_attempt_time = datetime.utcnow()

        if success:
            self.successful_attempts += 1
            self.last_success_time = datetime.utcnow()
        else:
            self.failed_attempts += 1
            self.last_failure_time = datetime.utcnow()

        self.attempt_history.append({
            "attempt": attempt,
            "success": success,
            "delay": delay,
            "error": str(error) if error else None,
            "timestamp": datetime.utcnow().isoformat()
        })

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_attempts == 0:
            return 0.0
        return self.successful_attempts / self.total_attempts

    @property
    def average_delay(self) -> float:
        """Calculate average delay per attempt."""
        if self.total_attempts == 0:
            return 0.0
        return self.total_delay / self.total_attempts


class RetryManager:
    """
    Manages retry logic with exponential backoff and monitoring.

    Usage:
        config = RetryConfig(max_attempts=3, base_delay=1.0)
        manager = RetryManager(config)

        result = await manager.retry_async(my_async_function, arg1, arg2)
        # or
        result = manager.retry_sync(my_sync_function, arg1, arg2)
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize retry manager.

        Args:
            config: Retry configuration (uses defaults if not provided)
        """
        self.config = config or RetryConfig()
        self.stats = RetryStats()

    def _should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if an error is retryable.

        Args:
            error: The exception that occurred
            attempt: Current attempt number

        Returns:
            True if should retry, False otherwise
        """
        # Check max attempts
        if attempt >= self.config.max_attempts:
            return False

        # Check if exception is retryable
        if isinstance(error, self.config.retryable_exceptions):
            return True

        # Check CBAError category
        if isinstance(error, CBAError):
            retryable_categories = [
                ErrorCategory.NETWORK,
                ErrorCategory.API_RATE_LIMIT,
                ErrorCategory.EXTERNAL_SERVICE,
            ]
            return error.category in retryable_categories

        return False

    def retry_sync(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any
    ) -> T:
        """
        Retry a synchronous function with exponential backoff.

        Args:
            func: The function to retry
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The function result

        Raises:
            The last exception if all retries fail
        """
        last_error = None

        for attempt in range(self.config.max_attempts):
            try:
                result = func(*args, **kwargs)
                self.stats.record_attempt(attempt, True, 0)
                logger.debug(
                    f"Retry success: {func.__name__} on attempt {attempt + 1}"
                )
                return result

            except Exception as e:
                last_error = e
                delay = self.config.get_delay(attempt)

                self.stats.record_attempt(attempt, False, delay, e)

                if self._should_retry(e, attempt):
                    logger.warning(
                        f"Retry attempt {attempt + 1}/{self.config.max_attempts} "
                        f"for {func.__name__} after {delay:.2f}s delay: {str(e)}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"Non-retryable error in {func.__name__}: {str(e)}"
                    )
                    raise

        # All retries failed
        logger.error(
            f"All {self.config.max_attempts} retry attempts failed for {func.__name__}"
        )
        raise last_error

    async def retry_async(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any
    ) -> T:
        """
        Retry an async function with exponential backoff.

        Args:
            func: The async function to retry
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The function result

        Raises:
            The last exception if all retries fail
        """
        last_error = None

        for attempt in range(self.config.max_attempts):
            try:
                result = await func(*args, **kwargs)
                self.stats.record_attempt(attempt, True, 0)
                logger.debug(
                    f"Retry success: {func.__name__} on attempt {attempt + 1}"
                )
                return result

            except Exception as e:
                last_error = e
                delay = self.config.get_delay(attempt)

                self.stats.record_attempt(attempt, False, delay, e)

                if self._should_retry(e, attempt):
                    logger.warning(
                        f"Retry attempt {attempt + 1}/{self.config.max_attempts} "
                        f"for {func.__name__} after {delay:.2f}s delay: {str(e)}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Non-retryable error in {func.__name__}: {str(e)}"
                    )
                    raise

        # All retries failed
        logger.error(
            f"All {self.config.max_attempts} retry attempts failed for {func.__name__}"
        )
        raise last_error

    def get_stats(self) -> dict:
        """
        Get retry statistics.

        Returns:
            Dictionary with retry statistics
        """
        return {
            "total_attempts": self.stats.total_attempts,
            "successful_attempts": self.stats.successful_attempts,
            "failed_attempts": self.stats.failed_attempts,
            "success_rate": self.stats.success_rate,
            "total_delay": self.stats.total_delay,
            "average_delay": self.stats.average_delay,
            "last_attempt_time": self.stats.last_attempt_time.isoformat() if self.stats.last_attempt_time else None,
            "last_success_time": self.stats.last_success_time.isoformat() if self.stats.last_success_time else None,
            "last_failure_time": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            "recent_history": self.stats.attempt_history[-10:]  # Last 10 attempts
        }

    def reset_stats(self):
        """Reset retry statistics."""
        self.stats = RetryStats()


# Decorators for easy retry integration

def retry_sync(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None
):
    """
    Decorator for adding retry logic to synchronous functions.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay for exponential backoff
        retryable_exceptions: Tuple of retryable exception types

    Usage:
        @retry_sync(max_attempts=3, base_delay=1.0)
        def my_function():
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            config = RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                retryable_exceptions=retryable_exceptions or RetryConfig().retryable_exceptions
            )
            manager = RetryManager(config)
            return manager.retry_sync(func, *args, **kwargs)
        return wrapper
    return decorator


def retry_async(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None
):
    """
    Decorator for adding retry logic to async functions.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay for exponential backoff
        retryable_exceptions: Tuple of retryable exception types

    Usage:
        @retry_async(max_attempts=3, base_delay=1.0)
        async def my_async_function():
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            config = RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                retryable_exceptions=retryable_exceptions or RetryConfig().retryable_exceptions
            )
            manager = RetryManager(config)
            return await manager.retry_async(func, *args, **kwargs)
        return wrapper
    return decorator


# Global retry manager instance with default configuration
_default_manager = None


def get_default_manager() -> RetryManager:
    """Get or create the global default retry manager."""
    global _default_manager
    if _default_manager is None:
        _default_manager = RetryManager()
    return _default_manager

"""
Circuit breaker pattern implementation for external service failures.

Prevents cascading failures by failing fast when a service is consistently failing.
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Callable, TypeVar, Optional, Any
from functools import wraps
from datetime import datetime, timedelta
from dataclasses import dataclass, field


# Configure logger
logger = logging.getLogger(__name__)


T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation, requests pass through
    OPEN = "open"           # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5  # Number of failures before opening
    success_threshold: int = 2  # Number of successes to close circuit
    timeout: float = 60.0  # Seconds before attempting recovery (open -> half_open)
    half_open_timeout: float = 30.0  # Max time in half_open state before reopening
    monitoring_window: float = 300.0  # Window for statistics (5 minutes)
    min_requests: int = 3  # Minimum requests before allowing circuit to open


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker monitoring."""
    total_requests: int = 0
    total_successes: int = 0
    total_failures: int = 0
    total_short_circuited: int = 0  # Requests failed fast due to open circuit
    last_state_change: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    open_count: int = 0  # Number of times circuit has opened
    close_count: int = 0  # Number of times circuit has closed

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate in monitoring window."""
        if self.total_requests == 0:
            return 0.0
        return self.total_failures / self.total_requests

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.total_successes / self.total_requests


class CircuitBreakerOpenError(Exception):
    """Raised when circuit is open and requests are blocked."""

    def __init__(
        self,
        service_name: str,
        last_failure: Optional[datetime] = None,
        reopen_time: Optional[datetime] = None
    ):
        self.service_name = service_name
        self.last_failure = last_failure
        self.reopen_time = reopen_time
        message = (
            f"Circuit breaker is OPEN for service '{service_name}'. "
            f"Failing fast to prevent cascading failures."
        )
        super().__init__(message)


class CircuitBreaker:
    """
    Circuit breaker implementation.

    Protects services from cascading failures by failing fast when
    a service is consistently failing.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests fail fast
    - HALF_OPEN: Testing if service has recovered

    Usage:
        breaker = CircuitBreaker("yfinance-api", failure_threshold=5)

        try:
            result = await breaker.call_async(external_service_function)
        except CircuitBreakerOpenError:
            # Handle open circuit
            pass
    """

    def __init__(
        self,
        service_name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        """
        Initialize circuit breaker.

        Args:
            service_name: Name of the service being protected
            config: Circuit breaker configuration
        """
        self.service_name = service_name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self.last_state_change = datetime.utcnow()
        self._half_open_deadline: Optional[datetime] = None

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should transition from OPEN to HALF_OPEN."""
        if self.state != CircuitState.OPEN:
            return False

        time_since_change = (datetime.utcnow() - self.last_state_change).total_seconds()
        return time_since_change >= self.config.timeout

    def _should_expire_half_open(self) -> bool:
        """Check if HALF_OPEN state has expired without recovery."""
        if self.state != CircuitState.HALF_OPEN:
            return False

        if self._half_open_deadline is None:
            return False

        return datetime.utcnow() >= self._half_open_deadline

    def _record_success(self):
        """Record a successful request."""
        self.stats.total_successes += 1
        self.stats.total_requests += 1
        self.stats.last_success_time = datetime.utcnow()
        self.stats.consecutive_successes += 1
        self.stats.consecutive_failures = 0

        # Handle state transitions
        if self.state == CircuitState.HALF_OPEN:
            if self.stats.consecutive_successes >= self.config.success_threshold:
                self._close()

    def _record_failure(self):
        """Record a failed request."""
        self.stats.total_failures += 1
        self.stats.total_requests += 1
        self.stats.last_failure_time = datetime.utcnow()
        self.stats.consecutive_failures += 1
        self.stats.consecutive_successes = 0

        # Handle state transitions
        if self.state == CircuitState.HALF_OPEN:
            self._open()
        elif self.state == CircuitState.CLOSED:
            if (self.stats.consecutive_failures >= self.config.failure_threshold
                    and self.stats.total_requests >= self.config.min_requests):
                self._open()

    def _open(self):
        """Transition to OPEN state."""
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.utcnow()
        self.stats.open_count += 1
        self._half_open_deadline = None
        logger.warning(
            f"Circuit breaker OPENED for service '{self.service_name}' "
            f"after {self.stats.consecutive_failures} consecutive failures"
        )

    def _half_open(self):
        """Transition to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self.last_state_change = datetime.utcnow()
        self._half_open_deadline = datetime.utcnow() + timedelta(
            seconds=self.config.half_open_timeout
        )
        logger.info(
            f"Circuit breaker HALF_OPEN for service '{self.service_name}' - "
            f"testing recovery"
        )

    def _close(self):
        """Transition to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.last_state_change = datetime.utcnow()
        self.stats.close_count += 1
        self._half_open_deadline = None
        logger.info(
            f"Circuit breaker CLOSED for service '{self.service_name}' - "
            f"service recovered after {self.stats.consecutive_successes} successes"
        )

    def call_sync(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Call a function with circuit breaker protection (synchronous).

        Args:
            func: The function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            The function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: The function exception if circuit allows it
        """
        # Check if we should attempt reset
        if self._should_attempt_reset():
            self._half_open()

        # Check if half-open expired
        if self._should_expire_half_open():
            self._open()

        # Fail fast if circuit is open
        if self.state == CircuitState.OPEN:
            self.stats.total_short_circuited += 1
            raise CircuitBreakerOpenError(
                service_name=self.service_name,
                last_failure=self.stats.last_failure_time,
                reopen_time=self.last_state_change + timedelta(seconds=self.config.timeout)
            )

        # Execute the function
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise

    async def call_async(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Call an async function with circuit breaker protection.

        Args:
            func: The async function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            The function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: The function exception if circuit allows it
        """
        # Check if we should attempt reset
        if self._should_attempt_reset():
            self._half_open()

        # Check if half-open expired
        if self._should_expire_half_open():
            self._open()

        # Fail fast if circuit is open
        if self.state == CircuitState.OPEN:
            self.stats.total_short_circuited += 1
            raise CircuitBreakerOpenError(
                service_name=self.service_name,
                last_failure=self.stats.last_failure_time,
                reopen_time=self.last_state_change + timedelta(seconds=self.config.timeout)
            )

        # Execute the function
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise

    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state

    def get_stats(self) -> dict:
        """
        Get circuit breaker statistics.

        Returns:
            Dictionary with circuit breaker metrics
        """
        return {
            "service_name": self.service_name,
            "state": self.state.value,
            "total_requests": self.stats.total_requests,
            "total_successes": self.stats.total_successes,
            "total_failures": self.stats.total_failures,
            "total_short_circuited": self.stats.total_short_circuited,
            "failure_rate": self.stats.failure_rate,
            "success_rate": self.stats.success_rate,
            "consecutive_failures": self.stats.consecutive_failures,
            "consecutive_successes": self.stats.consecutive_successes,
            "last_state_change": self.last_state_change.isoformat(),
            "last_failure_time": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            "last_success_time": self.stats.last_success_time.isoformat() if self.stats.last_success_time else None,
            "open_count": self.stats.open_count,
            "close_count": self.stats.close_count,
            "time_in_current_state": (datetime.utcnow() - self.last_state_change).total_seconds(),
        }

    def reset(self):
        """Reset circuit breaker to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.last_state_change = datetime.utcnow()
        self._half_open_deadline = None
        logger.info(f"Circuit breaker RESET for service '{self.service_name}'")


# Global circuit breaker registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    service_name: str,
    config: Optional[CircuitBreakerConfig] = None
) -> CircuitBreaker:
    """
    Get or create a circuit breaker for a service.

    Args:
        service_name: Name of the service
        config: Optional circuit breaker configuration

    Returns:
        CircuitBreaker instance
    """
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = CircuitBreaker(service_name, config)
    return _circuit_breakers[service_name]


# Decorators for circuit breaker integration

def circuit_breaker(
    service_name: Optional[str] = None,
    failure_threshold: int = 5,
    timeout: float = 60.0
):
    """
    Decorator for adding circuit breaker to functions.

    Args:
        service_name: Name of the service (defaults to function name)
        failure_threshold: Failures before opening circuit
        timeout: Seconds before attempting recovery

    Usage:
        @circuit_breaker(service_name="yfinance", failure_threshold=5)
        def fetch_stock_data(symbol):
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        name = service_name or func.__name__
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            timeout=timeout
        )
        breaker = get_circuit_breaker(name, config)

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            return breaker.call_sync(func, *args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            return await breaker.call_async(func, *args, **kwargs)

        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def get_all_circuit_breaker_stats() -> dict:
    """Get statistics for all registered circuit breakers."""
    return {
        name: breaker.get_stats()
        for name, breaker in _circuit_breakers.items()
    }


def reset_all_circuit_breakers():
    """Reset all circuit breakers to CLOSED state."""
    for breaker in _circuit_breakers.values():
        breaker.reset()

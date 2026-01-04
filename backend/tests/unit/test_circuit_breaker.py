"""
Unit tests for Circuit Breaker.

Tests circuit state transitions, failure tracking, timeout recovery, and stats.
"""

import pytest
import time
import asyncio
from unittest.mock import Mock
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.circuit_breaker import (
    CircuitState,
    CircuitBreakerConfig,
    CircuitBreakerStats,
    CircuitBreakerOpenError,
    CircuitBreaker,
    get_circuit_breaker,
    circuit_breaker,
    get_all_circuit_breaker_stats,
    reset_all_circuit_breakers
)


class TestCircuitState:
    """Test CircuitState enum."""

    def test_state_values(self):
        """Test circuit state values."""
        assert CircuitState.CLOSED == "closed"
        assert CircuitState.OPEN == "open"
        assert CircuitState.HALF_OPEN == "half_open"


class TestCircuitBreakerConfig:
    """Test CircuitBreakerConfig configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CircuitBreakerConfig()

        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout == 60.0
        assert config.half_open_max_calls == 3
        assert config.window_size == 100

    def test_custom_config(self):
        """Test custom configuration values."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=1,
            timeout=30.0
        )

        assert config.failure_threshold == 3
        assert config.success_threshold == 1
        assert config.timeout == 30.0


class TestCircuitBreakerStats:
    """Test CircuitBreakerStats statistics tracking."""

    def test_initial_stats(self):
        """Test initial statistics values."""
        stats = CircuitBreakerStats()

        assert stats.state == CircuitState.CLOSED
        assert stats.failure_count == 0
        assert stats.success_count == 0
        assert stats.total_calls == 0
        assert stats.consecutive_failures == 0
        assert stats.consecutive_successes == 0
        assert stats.open_count == 0

    def test_record_failure(self):
        """Test recording failures."""
        stats = CircuitBreakerStats()
        stats.record_failure()

        assert stats.failure_count == 1
        assert stats.total_calls == 1
        assert stats.consecutive_failures == 1
        assert stats.consecutive_successes == 0
        assert stats.last_failure_time is not None

    def test_record_success(self):
        """Test recording successes."""
        stats = CircuitBreakerStats()
        stats.record_success()

        assert stats.success_count == 1
        assert stats.total_calls == 1
        assert stats.consecutive_failures == 0
        assert stats.consecutive_successes == 1
        assert stats.last_success_time is not None

    def test_reset(self):
        """Test resetting statistics."""
        stats = CircuitBreakerStats()
        stats.record_failure()
        stats.record_success()
        stats.reset()

        assert stats.failure_count == 0
        assert stats.success_count == 0
        assert stats.total_calls == 0
        assert stats.consecutive_failures == 0
        assert stats.consecutive_successes == 0

    def test_failure_rate(self):
        """Test failure rate calculation."""
        stats = CircuitBreakerStats()

        # No calls yet
        assert stats.failure_rate == 0.0

        # Record some calls
        stats.record_failure()
        stats.record_failure()
        stats.record_success()

        assert stats.failure_rate == pytest.approx(2/3)

    def test_to_dict(self):
        """Test stats serialization to dictionary."""
        stats = CircuitBreakerStats()
        stats.record_failure()
        stats.record_success()

        stats_dict = stats.to_dict()

        assert stats_dict["state"] == "closed"
        assert stats_dict["failure_count"] == 1
        assert stats_dict["success_count"] == 1
        assert stats_dict["total_calls"] == 2


class TestCircuitBreakerSync:
    """Test CircuitBreaker with synchronous functions."""

    def test_initial_state_closed(self):
        """Test that circuit starts in CLOSED state."""
        breaker = CircuitBreaker("test")

        assert breaker.state == CircuitState.CLOSED

    def test_successful_call_no_state_change(self):
        """Test that successful calls don't change state."""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))
        mock_func = Mock(return_value="success")

        result = breaker.call_sync(mock_func)

        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert mock_func.call_count == 1

    def test_failures_open_circuit(self):
        """Test that repeated failures open the circuit."""
        breaker = CircuitBreaker(
            "test",
            CircuitBreakerConfig(failure_threshold=3, timeout=1.0)
        )
        mock_func = Mock(side_effect=ConnectionError("Failed"))

        # First failure
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_func)
        assert breaker.state == CircuitState.CLOSED

        # Second failure
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_func)
        assert breaker.state == CircuitState.CLOSED

        # Third failure - opens circuit
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_func)
        assert breaker.state == CircuitState.OPEN

    def test_open_circuit_blocks_calls(self):
        """Test that open circuit blocks calls."""
        breaker = CircuitBreaker(
            "test",
            CircuitBreakerConfig(failure_threshold=2, timeout=10.0)
        )
        mock_func = Mock(side_effect=ConnectionError("Failed"))

        # Open the circuit
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_func)
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_func)

        assert breaker.state == CircuitState.OPEN

        # Next call should fail with CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call_sync(mock_func)

        # Mock function should not be called again
        assert mock_func.call_count == 2

    def test_timeout_transition_to_half_open(self):
        """Test that timeout transitions to HALF_OPEN state."""
        breaker = CircuitBreaker(
            "test",
            CircuitBreakerConfig(failure_threshold=2, timeout=0.1, success_threshold=2)
        )

        # Open the circuit
        mock_fail = Mock(side_effect=ConnectionError("Failed"))
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_fail)
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_fail)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(0.2)

        # Next call should be allowed (transitions to HALF_OPEN)
        mock_success = Mock(return_value="success")
        result = breaker.call_sync(mock_success)

        assert result == "success"
        assert breaker.state == CircuitState.HALF_OPEN

    def test_half_open_success_closes_circuit(self):
        """Test that successful calls in HALF_OPEN close the circuit."""
        breaker = CircuitBreaker(
            "test",
            CircuitBreakerConfig(
                failure_threshold=2,
                timeout=0.1,
                success_threshold=2,
                half_open_max_calls=5
            )
        )

        # Open the circuit
        mock_fail = Mock(side_effect=ConnectionError("Failed"))
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_fail)
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_fail)

        # Wait for timeout
        time.sleep(0.2)

        # First success in HALF_OPEN
        mock_success = Mock(return_value="success")
        breaker.call_sync(mock_success)
        assert breaker.state == CircuitState.HALF_OPEN

        # Second success closes circuit
        breaker.call_sync(mock_success)
        assert breaker.state == CircuitState.CLOSED

    def test_half_open_failure_reopens_circuit(self):
        """Test that failures in HALF_OPEN reopen the circuit."""
        breaker = CircuitBreaker(
            "test",
            CircuitBreakerConfig(
                failure_threshold=2,
                timeout=0.1,
                success_threshold=2
            )
        )

        # Open the circuit
        mock_fail = Mock(side_effect=ConnectionError("Failed"))
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_fail)
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_fail)

        # Wait for timeout
        time.sleep(0.2)

        # First success in HALF_OPEN
        mock_success = Mock(return_value="success")
        breaker.call_sync(mock_success)
        assert breaker.state == CircuitState.HALF_OPEN

        # Failure reopens circuit
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_fail)
        assert breaker.state == CircuitState.OPEN

    def test_half_open_max_calls(self):
        """Test that HALF_OPEN has max calls limit."""
        breaker = CircuitBreaker(
            "test",
            CircuitBreakerConfig(
                failure_threshold=2,
                timeout=0.1,
                success_threshold=3,
                half_open_max_calls=2
            )
        )

        # Open the circuit
        mock_fail = Mock(side_effect=ConnectionError("Failed"))
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_fail)
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_fail)

        # Wait for timeout
        time.sleep(0.2)

        # Reach max calls in HALF_OPEN
        mock_success = Mock(return_value="success")
        breaker.call_sync(mock_success)
        breaker.call_sync(mock_success)

        # Circuit should still be HALF_OPEN after max calls
        # (not enough successes to close, but didn't fail either)
        assert breaker.state == CircuitState.HALF_OPEN

        # Third call should reopen circuit due to max_calls limit
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call_sync(mock_success)

    def test_get_stats(self):
        """Test getting circuit breaker statistics."""
        breaker = CircuitBreaker(
            "test",
            CircuitBreakerConfig(failure_threshold=3)
        )

        # Record some activity
        mock_func = Mock(side_effect=[ConnectionError("fail"), "success"])
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_func)
        breaker.call_sync(mock_func)

        stats = breaker.get_stats()

        assert stats["state"] == "closed"
        assert stats["failure_count"] == 1
        assert stats["success_count"] == 1
        assert stats["total_calls"] == 2
        assert stats["consecutive_failures"] == 0
        assert stats["consecutive_successes"] == 1

    def test_reset(self):
        """Test resetting circuit breaker."""
        breaker = CircuitBreaker(
            "test",
            CircuitBreakerConfig(failure_threshold=2)
        )

        # Open the circuit
        mock_fail = Mock(side_effect=ConnectionError("Failed"))
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_fail)
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_fail)

        assert breaker.state == CircuitState.OPEN

        # Reset
        breaker.reset()

        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.failure_count == 0
        assert breaker.stats.success_count == 0

    def test_get_name(self):
        """Test getting circuit breaker name."""
        breaker = CircuitBreaker("my-service")

        assert breaker.get_name() == "my-service"


class TestCircuitBreakerAsync:
    """Test CircuitBreaker with async functions."""

    @pytest.mark.asyncio
    async def test_successful_async_call(self):
        """Test successful async call."""
        breaker = CircuitBreaker("test")

        async def mock_func():
            return "async_success"

        result = await breaker.call_async(mock_func)

        assert result == "async_success"
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_async_failures_open_circuit(self):
        """Test that async failures open the circuit."""
        breaker = CircuitBreaker(
            "test",
            CircuitBreakerConfig(failure_threshold=2)
        )

        call_count = 0

        async def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Failed")
            return "success"

        # First failure
        with pytest.raises(ConnectionError):
            await breaker.call_async(mock_func)

        # Second failure - opens circuit
        with pytest.raises(ConnectionError):
            await breaker.call_async(mock_func)

        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_async_half_open_to_closed(self):
        """Test async transition from HALF_OPEN to CLOSED."""
        breaker = CircuitBreaker(
            "test",
            CircuitBreakerConfig(
                failure_threshold=2,
                timeout=0.1,
                success_threshold=2
            )
        )

        # Open the circuit
        async def mock_fail():
            raise ConnectionError("Failed")

        with pytest.raises(ConnectionError):
            await breaker.call_async(mock_fail)
        with pytest.raises(ConnectionError):
            await breaker.call_async(mock_fail)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.2)

        # Successful calls should close circuit
        async def mock_success():
            return "success"

        await breaker.call_async(mock_success)
        assert breaker.state == CircuitState.HALF_OPEN

        await breaker.call_async(mock_success)
        assert breaker.state == CircuitState.CLOSED


class TestCircuitBreakerDecorator:
    """Test circuit_breaker decorator."""

    def test_decorator_sync(self):
        """Test @circuit_breaker decorator with sync function."""
        call_count = 0

        @circuit_breaker("decorated-test", failure_threshold=2)
        def my_function(x):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("fail")
            return x * 2

        # First failure
        with pytest.raises(ConnectionError):
            my_function(5)

        # Second failure - opens circuit
        with pytest.raises(ConnectionError):
            my_function(5)

        # Circuit is open - should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            my_function(5)

    @pytest.mark.asyncio
    async def test_decorator_async(self):
        """Test @circuit_breaker decorator with async function."""
        call_count = 0

        @circuit_breaker("decorated-async-test", failure_threshold=2)
        async def my_async_function(x):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("fail")
            return x * 2

        # First failure
        with pytest.raises(ConnectionError):
            await my_async_function(5)

        # Second failure - opens circuit
        with pytest.raises(ConnectionError):
            await my_async_function(5)

        # Circuit is open
        assert call_count == 2


class TestGlobalCircuitBreakerRegistry:
    """Test global circuit breaker registry."""

    def test_get_circuit_breaker_same_instance(self):
        """Test that get_circuit_breaker returns same instance for same name."""
        breaker1 = get_circuit_breaker("service-a")
        breaker2 = get_circuit_breaker("service-a")

        assert breaker1 is breaker2

    def test_get_circuit_breaker_different_instances(self):
        """Test that different names return different instances."""
        breaker1 = get_circuit_breaker("service-a")
        breaker2 = get_circuit_breaker("service-b")

        assert breaker1 is not breaker2

    def test_get_all_circuit_breaker_stats(self):
        """Test getting stats for all circuit breakers."""
        # Create multiple circuit breakers
        get_circuit_breaker("service-a")
        get_circuit_breaker("service-b")
        get_circuit_breaker("service-c")

        all_stats = get_all_circuit_breaker_stats()

        assert "service-a" in all_stats
        assert "service-b" in all_stats
        assert "service-c" in all_stats

    def test_reset_all_circuit_breakers(self):
        """Test resetting all circuit breakers."""
        # Create and open some circuit breakers
        breaker_a = get_circuit_breaker("reset-test-a")
        breaker_b = get_circuit_breaker("reset-test-b")

        # Simulate opening circuits
        breaker_a.stats.record_failure()
        breaker_a.stats.record_failure()
        breaker_a.stats.record_failure()
        breaker_a._transition_to_open()

        breaker_b.stats.record_failure()
        breaker_b.stats.record_failure()
        breaker_b._transition_to_open()

        assert breaker_a.state == CircuitState.OPEN
        assert breaker_b.state == CircuitState.OPEN

        # Reset all
        reset_all_circuit_breakers()

        assert breaker_a.state == CircuitState.CLOSED
        assert breaker_b.state == CircuitState.CLOSED


class TestCircuitBreakerEdgeCases:
    """Test edge cases and error scenarios."""

    def test_function_with_arguments(self):
        """Test circuit breaker with function that takes arguments."""
        breaker = CircuitBreaker("test")

        def my_function(a, b, c=None):
            return a + b + (c or 0)

        result = breaker.call_sync(my_function, 1, 2, c=3)

        assert result == 6

    def test_return_value_propagation(self):
        """Test that return value is passed through correctly."""
        breaker = CircuitBreaker("test")

        def return_dict():
            return {"key": "value", "number": 42}

        result = breaker.call_sync(return_dict)

        assert result == {"key": "value", "number": 42}

    def test_exception_propagation(self):
        """Test that exceptions are propagated correctly."""
        breaker = CircuitBreaker("test")

        def raise_value_error():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            breaker.call_sync(raise_value_error)

    def test_consecutive_success_tracking(self):
        """Test consecutive success tracking."""
        breaker = CircuitBreaker("test")
        mock_func = Mock(return_value="success")

        breaker.call_sync(mock_func)
        breaker.call_sync(mock_func)
        breaker.call_sync(mock_func)

        assert breaker.stats.consecutive_successes == 3
        assert breaker.stats.consecutive_failures == 0

    def test_consecutive_failure_tracking(self):
        """Test consecutive failure tracking."""
        breaker = CircuitBreaker("test")
        mock_func = Mock(side_effect=ConnectionError("fail"))

        for _ in range(3):
            with pytest.raises(ConnectionError):
                breaker.call_sync(mock_func)

        assert breaker.stats.consecutive_failures == 3
        assert breaker.stats.consecutive_successes == 0

    def test_failure_threshold_of_one(self):
        """Test circuit breaker with failure threshold of 1."""
        breaker = CircuitBreaker(
            "test",
            CircuitBreakerConfig(failure_threshold=1)
        )
        mock_func = Mock(side_effect=ConnectionError("fail"))

        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_func)

        # Should open immediately
        assert breaker.state == CircuitState.OPEN

    def test_success_threshold_of_one(self):
        """Test circuit breaker closes with single success in HALF_OPEN."""
        breaker = CircuitBreaker(
            "test",
            CircuitBreakerConfig(
                failure_threshold=2,
                timeout=0.1,
                success_threshold=1
            )
        )

        # Open the circuit
        mock_fail = Mock(side_effect=ConnectionError("fail"))
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_fail)
        with pytest.raises(ConnectionError):
            breaker.call_sync(mock_fail)

        # Wait for timeout
        time.sleep(0.2)

        # Single success should close circuit
        mock_success = Mock(return_value="success")
        breaker.call_sync(mock_success)

        assert breaker.state == CircuitState.CLOSED

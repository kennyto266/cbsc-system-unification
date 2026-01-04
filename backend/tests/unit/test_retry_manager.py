"""
Unit tests for Retry Manager.

Tests exponential backoff timing, maximum attempts, jitter, and edge cases.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.retry_manager import (
    RetryConfig,
    RetryStats,
    RetryManager,
    retry_sync,
    retry_async
)


class TestRetryConfig:
    """Test RetryConfig configuration and delay calculation."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_attempts == 5
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert config.retryable_exceptions == (
            ConnectionError,
            TimeoutError,
            OSError,
        )

    def test_delay_calculation_exponential(self):
        """Test exponential backoff delay calculation."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)

        # Without jitter, delays should be exactly: 1, 2, 4, 8, 16...
        assert config.get_delay(0) == 1.0
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 4.0
        assert config.get_delay(3) == 8.0
        assert config.get_delay(4) == 16.0

    def test_delay_max_cap(self):
        """Test that delay is capped at max_delay."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, max_delay=10.0, jitter=False)

        assert config.get_delay(0) == 1.0
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 4.0
        assert config.get_delay(3) == 8.0
        assert config.get_delay(4) == 10.0  # Capped at max
        assert config.get_delay(5) == 10.0  # Stays capped

    def test_delay_with_jitter(self):
        """Test that jitter adds randomness to delays."""
        config = RetryConfig(base_delay=10.0, jitter=True, jitter_factor=0.1)

        delays = [config.get_delay(0) for _ in range(20)]

        # All delays should be close to 10.0 (within +/- 1.0)
        assert all(9.0 <= d <= 11.0 for d in delays)

        # There should be variation
        assert len(set(delays)) > 1

    def test_delay_no_negative(self):
        """Test that delays are never negative."""
        config = RetryConfig(base_delay=1.0, jitter=True, jitter_factor=0.5)

        for attempt in range(10):
            delay = config.get_delay(attempt)
            assert delay >= 0


class TestRetryStats:
    """Test RetryStats statistics tracking."""

    def test_initial_stats(self):
        """Test initial statistics values."""
        stats = RetryStats()
        assert stats.total_attempts == 0
        assert stats.successful_attempts == 0
        assert stats.failed_attempts == 0
        assert stats.total_delay == 0.0
        assert stats.last_attempt_time is None
        assert stats.last_success_time is None
        assert stats.last_failure_time is None

    def test_success_recording(self):
        """Test recording successful attempts."""
        stats = RetryStats()
        stats.record_attempt(0, True, 1.0)
        stats.record_attempt(1, True, 2.0)

        assert stats.total_attempts == 2
        assert stats.successful_attempts == 2
        assert stats.failed_attempts == 0
        assert stats.total_delay == 3.0
        assert stats.success_rate == 1.0
        assert stats.average_delay == 1.5

    def test_failure_recording(self):
        """Test recording failed attempts."""
        stats = RetryStats()
        stats.record_attempt(0, False, 1.0)
        stats.record_attempt(1, False, 2.0)
        stats.record_attempt(2, True, 4.0)

        assert stats.total_attempts == 3
        assert stats.successful_attempts == 1
        assert stats.failed_attempts == 2
        assert stats.total_delay == 7.0
        assert stats.success_rate == pytest.approx(1/3)
        assert stats.average_delay == pytest.approx(7/3)

    def test_consecutive_tracking(self):
        """Test consecutive success/failure tracking."""
        stats = RetryStats()

        # Three successes
        for i in range(3):
            stats.record_attempt(i, True, 1.0)
        assert stats.consecutive_successes == 3
        assert stats.consecutive_failures == 0

        # Two failures
        for i in range(3, 5):
            stats.record_attempt(i, False, 1.0)
        assert stats.consecutive_successes == 0
        assert stats.consecutive_failures == 2


class TestRetryManagerSync:
    """Test RetryManager with synchronous functions."""

    def test_successful_call_no_retry(self):
        """Test that successful calls don't retry."""
        manager = RetryManager()
        mock_func = Mock(return_value="success")

        result = manager.retry_sync(mock_func)

        assert result == "success"
        assert mock_func.call_count == 1  # Called once, no retries

    def test_retry_on_exception(self):
        """Test that retry happens on retryable exceptions."""
        manager = RetryManager(
            RetryConfig(max_attempts=3, base_delay=0.01, jitter=False)
        )
        mock_func = Mock(side_effect=[ConnectionError("fail1"), ConnectionError("fail2"), "success"])

        result = manager.retry_sync(mock_func)

        assert result == "success"
        assert mock_func.call_count == 3  # Initial + 2 retries

    def test_max_attempts_exceeded(self):
        """Test that retries stop after max_attempts."""
        manager = RetryManager(
            RetryConfig(max_attempts=3, base_delay=0.01, jitter=False)
        )
        mock_func = Mock(side_effect=ConnectionError("always fails"))

        with pytest.raises(ConnectionError):
            manager.retry_sync(mock_func)

        assert mock_func.call_count == 3  # Max attempts reached

    def test_non_retryable_exception(self):
        """Test that non-retryable exceptions are not retried."""
        manager = RetryManager(
            RetryConfig(
                max_attempts=5,
                retryable_exceptions=(ConnectionError,)  # Only retry ConnectionError
            )
        )
        mock_func = Mock(side_effect=ValueError("not retryable"))

        with pytest.raises(ValueError):
            manager.retry_sync(mock_func)

        assert mock_func.call_count == 1  # No retries for non-retryable

    def test_stats_tracking(self):
        """Test that retry statistics are tracked correctly."""
        manager = RetryManager(
            RetryConfig(max_attempts=5, base_delay=0.01, jitter=False)
        )

        # First call succeeds after 1 retry
        mock_func1 = Mock(side_effect=[ConnectionError("fail"), "success"])
        manager.retry_sync(mock_func1)

        # Second call fails all attempts
        mock_func2 = Mock(side_effect=ConnectionError("always fails"))
        try:
            manager.retry_sync(mock_func2)
        except ConnectionError:
            pass

        stats = manager.get_stats()
        assert stats["total_attempts"] == 6  # 2 + 4 (max attempts for second)
        assert stats["successful_attempts"] == 1
        assert stats["failed_attempts"] >= 4

    def test_reset_stats(self):
        """Test resetting statistics."""
        manager = RetryManager()
        mock_func = Mock(side_effect=[ConnectionError("fail"), "success"])
        manager.retry_sync(mock_func)

        manager.reset_stats()

        stats = manager.get_stats()
        assert stats["total_attempts"] == 0
        assert stats["successful_attempts"] == 0


class TestRetryManagerAsync:
    """Test RetryManager with async functions."""

    @pytest.mark.asyncio
    async def test_successful_async_call(self):
        """Test that successful async calls don't retry."""
        manager = RetryManager()

        async def mock_func():
            return "async_success"

        result = await manager.retry_async(mock_func)

        assert result == "async_success"

    @pytest.mark.asyncio
    async def test_retry_async_on_exception(self):
        """Test that retry works with async functions."""
        manager = RetryManager(
            RetryConfig(max_attempts=3, base_delay=0.01, jitter=False)
        )

        call_count = 0

        async def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError(f"fail {call_count}")
            return "success"

        result = await manager.retry_async(mock_func)

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_async_timing(self):
        """Test that async retry respects delay timing."""
        manager = RetryManager(
            RetryConfig(max_attempts=3, base_delay=0.05, jitter=False)
        )

        async def mock_func():
            raise ConnectionError("fail")

        start = time.time()
        try:
            await manager.retry_async(mock_func)
        except ConnectionError:
            pass
        elapsed = time.time() - start

        # Should have delays: 0.05 + 0.10 = 0.15 seconds minimum
        assert elapsed >= 0.14  # Allow small margin


class TestRetryDecorators:
    """Test retry decorators."""

    def test_retry_sync_decorator(self):
        """Test @retry_sync decorator."""
        call_count = 0

        @retry_sync(max_attempts=3, base_delay=0.01)
        def my_function(x):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("fail")
            return x * 2

        result = my_function(5)

        assert result == 10
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_async_decorator(self):
        """Test @retry_async decorator."""
        call_count = 0

        @retry_async(max_attempts=3, base_delay=0.01)
        async def my_async_function(x):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("fail")
            return x * 2

        result = await my_async_function(5)

        assert result == 10
        assert call_count == 2


class TestRetryManagerEdgeCases:
    """Test edge cases and error scenarios."""

    def test_function_with_arguments(self):
        """Test retry with function that takes arguments."""
        manager = RetryManager(RetryConfig(max_attempts=2, base_delay=0.01))

        mock_func = Mock(side_effect=[ConnectionError("fail"), "result"])

        result = manager.retry_sync(mock_func, "arg1", "arg2", kwarg="kwvalue")

        assert result == "result"
        mock_func.assert_called_with("arg1", "arg2", kwarg="kwvalue")

    def test_function_return_value(self):
        """Test that return value is passed through correctly."""
        manager = RetryManager()

        def return_dict():
            return {"key": "value"}

        result = manager.retry_sync(return_dict)

        assert result == {"key": "value"}

    def test_exception_propagation(self):
        """Test that final exception is propagated after retries."""
        manager = RetryManager(RetryConfig(max_attempts=2, base_delay=0.01))

        def always_fail():
            raise ValueError("always fails")

        with pytest.raises(ValueError, match="always fails"):
            manager.retry_sync(always_fail)

    def test_different_exception_types(self):
        """Test retry behavior with different exception types."""
        manager = RetryManager(
            RetryConfig(
                max_attempts=3,
                retryable_exceptions=(ConnectionError, TimeoutError)
            )
        )

        # Retryable exceptions
        for exc_class in [ConnectionError, TimeoutError]:
            mock_func = Mock(side_effect=[exc_class("fail"), "success"])
            result = manager.retry_sync(mock_func)
            assert result == "success"

        # Non-retryable exception
        mock_func2 = Mock(side_effect=ValueError("not retryable"))
        with pytest.raises(ValueError):
            manager.retry_sync(mock_func2)
        assert mock_func2.call_count == 1

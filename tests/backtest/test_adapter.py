"""
Unit tests for BacktestAdapter.

Tests the core adapter functionality including API integration,
progress tracking, and error handling.
"""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
import httpx

from cbsc_strategy_sdk.backtest.adapter import BacktestAdapter
from cbsc_strategy_sdk.backtest.models import (
    BacktestJob,
    BacktestMetrics,
    BacktestRequest,
    BacktestStatus,
    BacktestSubmitResponse,
)
from cbsc_strategy_sdk.exceptions import APIConnectionError, DataFetchError, StrategyWorkspaceError


class TestBacktestAdapter:
    """Test suite for BacktestAdapter class."""

    @pytest_asyncio.fixture
    async def adapter(self):
        """Create adapter instance for testing."""
        adapter = BacktestAdapter(api_base="http://localhost:3003")
        await adapter.__aenter__()
        yield adapter
        await adapter.__aexit__()

    @pytest.mark.asyncio
    async def test_adapter_initialization(self):
        """Test adapter initializes correctly."""
        adapter = BacktestAdapter(api_base="http://localhost:3003")

        assert adapter._config.api_base == "http://localhost:3003"
        assert adapter._is_initialized is False
        assert adapter._client is None

    @pytest.mark.asyncio
    async def test_adapter_context_manager(self):
        """Test adapter as context manager."""
        async with BacktestAdapter(api_base="http://localhost:3003") as adapter:
            assert adapter._is_initialized is True
            assert adapter._client is not None

        # After exiting context
        assert adapter._is_initialized is False
        assert adapter._client is None

    @pytest.mark.asyncio
    async def test_adapter_already_initialized_error(self):
        """Test error when initializing twice."""
        adapter = BacktestAdapter(api_base="http://localhost:3003")

        async with adapter:
            with pytest.raises(StrategyWorkspaceError, match="already initialized"):
                await adapter.__aenter__()

    @pytest.mark.asyncio
    async def test_not_initialized_error(self, adapter):
        """Test error when using adapter without initialization."""
        new_adapter = BacktestAdapter(api_base="http://localhost:3003")

        with pytest.raises(StrategyWorkspaceError, match="not initialized"):
            new_adapter._ensure_initialized()

    @pytest.mark.asyncio
    async def test_run_backtest_success(self, adapter):
        """Test successful backtest execution."""
        # Mock API responses
        submit_response = BacktestSubmitResponse(
            success=True,
            job_id="test-job-123",
            status=BacktestStatus.PENDING,
            message="Job submitted",
        )

        status_response = {
            "success": True,
            "job": {
                "job_id": "test-job-123",
                "status": "completed",
                "created_at": datetime.now().isoformat(),
                "started_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "progress": 100.0,
            },
            "result": {
                "job": {
                    "job_id": "test-job-123",
                    "status": "completed",
                    "created_at": datetime.now().isoformat(),
                    "progress": 100.0,
                },
                "metrics": {
                    "total_return": 15.5,
                    "annual_return": 18.2,
                    "sharpe_ratio": 1.5,
                    "sortino_ratio": 2.0,
                    "max_drawdown": 8.5,
                    "calmar_ratio": 2.1,
                    "win_rate": 65.0,
                    "profit_factor": 1.8,
                    "total_trades": 100,
                    "profit_trades": 65,
                    "avg_profit": 2.5,
                    "avg_loss": -1.8,
                },
                "trades": [],
                "equity_curve": [],
                "parameters": {},
            },
        }

        with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post, \
             patch.object(adapter._client, "get", new_callable=AsyncMock) as mock_get:

            # Mock submit response
            mock_post.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=submit_response.model_dump()),
            )

            # Mock status response
            mock_get.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=status_response),
            )

            # Run backtest
            result = await adapter.run_backtest(
                strategy_code="test_strategy",
                symbols=["AAPL"],
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
                parameters={"rsi_period": 14},
            )

            # Verify result
            assert result is not None
            assert result.metrics.total_return == 15.5
            assert result.metrics.sharpe_ratio == 1.5

    @pytest.mark.asyncio
    async def test_run_backtest_submit_failure(self, adapter):
        """Test handling of submit failure."""
        with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "400 Bad Request",
                request=MagicMock(),
                response=MagicMock(status_code=400),
            )

            with pytest.raises(DataFetchError, match="Failed to submit backtest"):
                await adapter.run_backtest(
                    strategy_code="test_strategy",
                    symbols=["AAPL"],
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 12, 31),
                    parameters={},
                )

    @pytest.mark.asyncio
    async def test_get_backtest_status(self, adapter):
        """Test getting backtest status."""
        status_response = {
            "success": True,
            "job": {
                "job_id": "test-job-123",
                "status": "running",
                "created_at": datetime.now().isoformat(),
                "started_at": datetime.now().isoformat(),
                "progress": 50.0,
                "current_step": "Processing data",
            },
        }

        with patch.object(adapter._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=status_response),
            )

            job = await adapter.get_backtest_status("test-job-123")

            assert job.job_id == "test-job-123"
            assert job.status == BacktestStatus.RUNNING
            assert job.progress == 50.0

    @pytest.mark.asyncio
    async def test_cancel_backtest(self, adapter):
        """Test cancelling a backtest."""
        with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                raise_for_status=MagicMock(),
            )

            result = await adapter.cancel_backtest("test-job-123")

            assert result is True

    @pytest.mark.asyncio
    async def test_cancel_backtest_failure(self, adapter):
        """Test handling of cancel failure."""
        with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            )

            with pytest.raises(DataFetchError, match="Failed to cancel backtest"):
                await adapter.cancel_backtest("test-job-123")

    @pytest.mark.asyncio
    async def test_poll_timeout(self, adapter):
        """Test poll timeout handling."""
        submit_response = BacktestSubmitResponse(
            success=True,
            job_id="test-job-123",
            status=BacktestStatus.PENDING,
        )

        status_response = {
            "success": True,
            "job": {
                "job_id": "test-job-123",
                "status": "running",
                "progress": 0.0,
                "created_at": datetime.now().isoformat(),
            },
        }

        with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post, \
             patch.object(adapter._client, "get", new_callable=AsyncMock) as mock_get:

            mock_post.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=submit_response.model_dump()),
            )

            # Always return running status
            mock_get.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=status_response),
            )

            # Should timeout
            with pytest.raises(DataFetchError, match="timeout"):
                await adapter.run_backtest(
                    strategy_code="test_strategy",
                    symbols=["AAPL"],
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 12, 31),
                    parameters={},
                    poll_timeout=0.1,  # Very short timeout
                )

    @pytest.mark.asyncio
    async def test_progress_callback(self, adapter):
        """Test progress callback is called."""
        progress_values = []

        def callback(progress: float) -> None:
            progress_values.append(progress)

        submit_response = BacktestSubmitResponse(
            success=True,
            job_id="test-job-123",
            status=BacktestStatus.PENDING,
        )

        status_response_running = {
            "success": True,
            "job": {
                "job_id": "test-job-123",
                "status": "running",
                "progress": 50.0,
                "created_at": datetime.now().isoformat(),
            },
        }

        status_response_complete = {
            "success": True,
            "job": {
                "job_id": "test-job-123",
                "status": "completed",
                "progress": 100.0,
                "created_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
            },
            "result": {
                "job": {
                    "job_id": "test-job-123",
                    "status": "completed",
                    "progress": 100.0,
                    "created_at": datetime.now().isoformat(),
                },
                "metrics": {
                    "total_return": 10.0,
                    "annual_return": 12.0,
                    "sharpe_ratio": 1.2,
                    "max_drawdown": 5.0,
                    "win_rate": 60.0,
                    "profit_factor": 1.5,
                    "total_trades": 50,
                    "profit_trades": 30,
                    "avg_profit": 2.0,
                    "avg_loss": -1.5,
                },
                "trades": [],
                "equity_curve": [],
                "parameters": {},
            },
        }

        call_count = [0]

        async def mock_get(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(
                    raise_for_status=MagicMock(),
                    json=MagicMock(return_value=status_response_running),
                )
            else:
                return MagicMock(
                    raise_for_status=MagicMock(),
                    json=MagicMock(return_value=status_response_complete),
                )

        with patch.object(adapter._client, "post", new_callable=AsyncMock) as mock_post, \
             patch.object(adapter._client, "get", new=mock_get):

            mock_post.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=submit_response.model_dump()),
            )

            await adapter.run_backtest(
                strategy_code="test_strategy",
                symbols=["AAPL"],
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
                parameters={},
                on_progress=callback,
                poll_interval=0.01,
            )

            # Verify callback was called
            assert len(progress_values) > 0


class TestBacktestAdapterEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_empty_symbols_list(self):
        """Test validation of empty symbols list."""
        adapter = BacktestAdapter(api_base="http://localhost:3003")
        await adapter.__aenter__()

        with pytest.raises(Exception):  # Pydantic validation error
            await adapter.run_backtest(
                strategy_code="test_strategy",
                symbols=[],
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
                parameters={},
            )

        await adapter.__aexit__()

    @pytest.mark.asyncio
    async def test_invalid_date_range(self):
        """Test validation of date range."""
        adapter = BacktestAdapter(api_base="http://localhost:3003")
        await adapter.__aenter__()

        with pytest.raises(Exception):  # Pydantic validation error
            await adapter.run_backtest(
                strategy_code="test_strategy",
                symbols=["AAPL"],
                start_date=date(2024, 12, 31),
                end_date=date(2024, 1, 1),  # End before start
                parameters={},
            )

        await adapter.__aexit__()

    @pytest.mark.asyncio
    async def test_connection_error_on_init(self):
        """Test handling of connection error during initialization."""
        with patch("httpx.AsyncClient", side_effect=Exception("Connection failed")):
            with pytest.raises(APIConnectionError, match="Failed to initialize"):
                async with BacktestAdapter(api_base="http://invalid:3003"):
                    pass

    def test_repr(self):
        """Test string representation."""
        adapter = BacktestAdapter(api_base="http://localhost:3003")
        repr_str = repr(adapter)

        assert "BacktestAdapter" in repr_str
        assert "http://localhost:3003" in repr_str
        assert "initialized=False" in repr_str

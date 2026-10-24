"""
BacktestAdapter for CBSC Integration.

This module provides the main adapter class that wraps the CBSC backtesting API
with a notebook-friendly interface for running backtests from Jupyter notebooks.
"""

import asyncio
import logging
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional

import httpx

from ..config import WorkspaceConfig, create_config
from ..exceptions import APIConnectionError, DataFetchError, StrategyWorkspaceError
from .models import (
    BacktestJob,
    BacktestRequest,
    BacktestResultData,
    BacktestStatus,
    BacktestStatusResponse,
    BacktestSubmitResponse,
)
from .progress import BacktestProgress
from .result import BacktestResult


# Configure logging
logger = logging.getLogger(__name__)

# API endpoints
BACKTEST_RUN_ENDPOINT = "/api/backtest/run"
BACKTEST_STATUS_ENDPOINT = "/api/backtest/status"
BACKTEST_CANCEL_ENDPOINT = "/api/backtest/cancel"

# Polling configuration
DEFAULT_POLL_INTERVAL = 2.0  # seconds
DEFAULT_POLL_TIMEOUT = 300.0  # seconds (5 minutes)


class BacktestAdapter:
    """Adapter for CBSC backtesting API with notebook-friendly interface.

    This class provides a clean interface for running backtests against
    the CBSC backend API, with support for async operations, progress
    tracking, and result visualization.

    The adapter should be used as an async context manager to ensure
    proper resource initialization and cleanup.

    Attributes:
        _config: Workspace configuration
        _client: HTTP client for API requests

    Example:
        >>> from cbsc_strategy_sdk import BacktestAdapter
        >>> from datetime import date
        >>>
        >>> async with BacktestAdapter() as adapter:
        ...     # Run backtest
        ...     result = await adapter.run_backtest(
        ...         strategy_code="my_strategy",
        ...         symbols=["AAPL"],
        ...         start_date=date(2024, 1, 1),
        ...         end_date=date(2024, 12, 31),
        ...         parameters={"rsi_period": 14}
        ...     )
        ...     # Plot results
        ...     result.plot_equity_curve()
    """

    def __init__(
        self,
        api_base: str = "http://localhost:3003",
        timeout: int = 30,
        auth_token: Optional[str] = None,
    ) -> None:
        """Initialize BacktestAdapter.

        Args:
            api_base: Base URL for CBSC backend API
            timeout: HTTP request timeout in seconds
            auth_token: Optional JWT token for authentication
        """
        self._config: WorkspaceConfig = create_config(api_base=api_base, timeout=timeout)
        self._auth_token: Optional[str] = auth_token
        self._client: Optional[httpx.AsyncClient] = None
        self._is_initialized: bool = False

    async def __aenter__(self) -> "BacktestAdapter":
        """Enter async context, initialize HTTP client.

        Returns:
            Self for context manager usage

        Raises:
            APIConnectionError: If initialization fails
        """
        if self._is_initialized:
            raise StrategyWorkspaceError("Adapter is already initialized")

        try:
            # Create HTTP client with auth if provided
            headers = {}
            if self._auth_token:
                headers["Authorization"] = f"Bearer {self._auth_token}"

            self._client = httpx.AsyncClient(
                base_url=self._config.api_base,
                timeout=self._config.get_timeout_ms() / 1000.0,
                headers=headers,
            )

            self._is_initialized = True
            logger.info(f"BacktestAdapter initialized for {self._config.api_base}")
            return self

        except Exception as e:
            self._client = None
            self._is_initialized = False

            raise APIConnectionError(
                f"Failed to initialize adapter: {e}",
                url=self._config.api_base,
                details={"error": str(e)},
            ) from e

    async def __aexit__(self, *args) -> None:
        """Exit async context, cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._is_initialized = False

    def _ensure_initialized(self) -> None:
        """Check if adapter is initialized.

        Raises:
            StrategyWorkspaceError: If adapter not initialized
        """
        if not self._is_initialized or self._client is None:
            raise StrategyWorkspaceError(
                "Adapter not initialized. Use 'async with BacktestAdapter() as adapter:'"
            )

    async def run_backtest(
        self,
        strategy_code: str,
        symbols: List[str],
        start_date: date,
        end_date: date,
        parameters: Dict[str, Any],
        initial_capital: float = 1000000.0,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005,
        on_progress: Optional[Callable[[float], None]] = None,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        poll_timeout: float = DEFAULT_POLL_TIMEOUT,
    ) -> BacktestResult:
        """Run backtest and return results.

        This method submits a backtest job to the CBSC API, polls for
        completion, and returns the parsed results.

        Args:
            strategy_code: Unique identifier for the strategy
            symbols: List of trading symbols
            start_date: Backtest start date
            end_date: Backtest end date
            parameters: Strategy parameters dictionary
            initial_capital: Starting capital (default 1M)
            commission_rate: Commission rate (default 0.1%)
            slippage_rate: Slippage rate (default 0.05%)
            on_progress: Optional callback for progress updates
            poll_interval: Seconds between status polls
            poll_timeout: Maximum time to wait for completion

        Returns:
            BacktestResult with metrics, trades, and visualization methods

        Raises:
            StrategyWorkspaceError: If adapter not initialized
            DataFetchError: If API request fails
            APIConnectionError: If connection fails
        """
        self._ensure_initialized()

        # Create request
        request = BacktestRequest(
            strategy_code=strategy_code,
            symbols=symbols,
            start_date=datetime.combine(start_date, datetime.min.time()),
            end_date=datetime.combine(end_date, datetime.min.time()),
            parameters=parameters,
            initial_capital=initial_capital,
            commission_rate=commission_rate,
            slippage_rate=slippage_rate,
        )

        # Submit job
        submit_response = await self._submit_backtest(request)
        job_id = submit_response.job_id

        logger.info(f"Backtest job submitted: {job_id}")

        # Poll for completion
        result_data = await self._poll_backtest(
            job_id=job_id,
            on_progress=on_progress,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )

        # Create BacktestResult
        return BacktestResult(raw_data=result_data)

    async def _submit_backtest(self, request: BacktestRequest) -> BacktestSubmitResponse:
        """Submit backtest job to API.

        Args:
            request: Backtest request

        Returns:
            Submit response with job ID

        Raises:
            DataFetchError: If submission fails
        """
        url = self._config.get_api_url(BACKTEST_RUN_ENDPOINT)

        try:
            response = await self._client.post(
                url,
                json=request.model_dump(),
                headers={"Content-Type": "application/json"},
            )

            response.raise_for_status()
            data = response.json()

            return BacktestSubmitResponse(**data)

        except httpx.HTTPStatusError as e:
            raise DataFetchError(
                f"Failed to submit backtest: {e.response.status_code}",
                status_code=e.response.status_code,
                details={"request": request.model_dump()},
            ) from e

        except httpx.RequestError as e:
            raise APIConnectionError(
                f"Connection error during submission: {e}",
                url=url,
            ) from e

        except Exception as e:
            raise DataFetchError(
                f"Unexpected error during submission: {e}",
                details={"error": str(e)},
            ) from e

    async def _poll_backtest(
        self,
        job_id: str,
        on_progress: Optional[Callable[[float], None]],
        poll_interval: float,
        poll_timeout: float,
    ) -> BacktestResultData:
        """Poll backtest status until completion.

        Args:
            job_id: Job identifier
            on_progress: Optional progress callback
            poll_interval: Seconds between polls
            poll_timeout: Maximum wait time

        Returns:
            Complete backtest result data

        Raises:
            DataFetchError: If polling fails or job fails
        """
        url = self._config.get_api_url(f"{BACKTEST_STATUS_ENDPOINT}/{job_id}")
        start_time = asyncio.get_event_loop().time()

        while True:
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > poll_timeout:
                raise DataFetchError(
                    f"Backtest timeout after {poll_timeout}s",
                    details={"job_id": job_id, "elapsed": elapsed},
                )

            # Get status
            try:
                response = await self._client.get(url)
                response.raise_for_status()
                data = response.json()
                status_response = BacktestStatusResponse(**data)

            except httpx.HTTPStatusError as e:
                raise DataFetchError(
                    f"Failed to get status: {e.response.status_code}",
                    status_code=e.response.status_code,
                    details={"job_id": job_id},
                ) from e

            except httpx.RequestError as e:
                # Retry on connection errors
                logger.warning(f"Connection error polling status, retrying: {e}")
                await asyncio.sleep(poll_interval)
                continue

            # Check job
            job = status_response.job
            if job is None:
                raise DataFetchError(
                    "Status response missing job data",
                    details={"job_id": job_id},
                )

            # Update progress
            if on_progress and job.progress:
                try:
                    on_progress(job.progress)
                except Exception as e:
                    logger.warning(f"Progress callback failed: {e}")

            # Check if complete
            if job.status == BacktestStatus.COMPLETED:
                if status_response.result is None:
                    raise DataFetchError(
                        "Job completed but no result data",
                        details={"job_id": job_id},
                    )
                return status_response.result

            if job.status == BacktestStatus.FAILED:
                raise DataFetchError(
                    f"Backtest job failed: {job.error_message or 'Unknown error'}",
                    details={"job_id": job_id, "error": job.error_message},
                )

            if job.status == BacktestStatus.CANCELLED:
                raise DataFetchError(
                    "Backtest job was cancelled",
                    details={"job_id": job_id},
                )

            # Wait before next poll
            await asyncio.sleep(poll_interval)

    async def get_backtest_status(self, job_id: str) -> BacktestJob:
        """Check status of running backtest.

        Args:
            job_id: Job identifier

        Returns:
            Current job status

        Raises:
            DataFetchError: If status check fails
        """
        self._ensure_initialized()

        url = self._config.get_api_url(f"{BACKTEST_STATUS_ENDPOINT}/{job_id}")

        try:
            response = await self._client.get(url)
            response.raise_for_status()
            data = response.json()
            status_response = BacktestStatusResponse(**data)

            if status_response.job is None:
                raise DataFetchError(
                    "Status response missing job data",
                    details={"job_id": job_id},
                )

            return status_response.job

        except httpx.HTTPStatusError as e:
            raise DataFetchError(
                f"Failed to get status: {e.response.status_code}",
                status_code=e.response.status_code,
                details={"job_id": job_id},
            ) from e

        except httpx.RequestError as e:
            raise APIConnectionError(
                f"Connection error getting status: {e}",
                url=url,
            ) from e

    async def cancel_backtest(self, job_id: str) -> bool:
        """Cancel running backtest.

        Args:
            job_id: Job identifier

        Returns:
            True if cancellation successful

        Raises:
            DataFetchError: If cancellation fails
        """
        self._ensure_initialized()

        url = self._config.get_api_url(f"{BACKTEST_CANCEL_ENDPOINT}/{job_id}")

        try:
            response = await self._client.post(url)
            response.raise_for_status()

            logger.info(f"Backtest job cancelled: {job_id}")
            return True

        except httpx.HTTPStatusError as e:
            raise DataFetchError(
                f"Failed to cancel backtest: {e.response.status_code}",
                status_code=e.response.status_code,
                details={"job_id": job_id},
            ) from e

        except httpx.RequestError as e:
            raise APIConnectionError(
                f"Connection error cancelling backtest: {e}",
                url=url,
            ) from e

    async def run_backtest_sync(
        self,
        strategy_code: str,
        symbols: List[str],
        start_date: date,
        end_date: date,
        parameters: Dict[str, Any],
        **kwargs,
    ) -> BacktestResult:
        """Synchronous wrapper for run_backtest.

        This method allows running backtests from synchronous code
        by handling the async execution internally.

        Args:
            strategy_code: Strategy identifier
            symbols: Trading symbols
            start_date: Start date
            end_date: End date
            parameters: Strategy parameters
            **kwargs: Additional arguments for run_backtest

        Returns:
            BacktestResult

        Example:
            >>> adapter = BacktestAdapter()
            >>> await adapter.__aenter__()
            >>> result = await adapter.run_backtest_sync(...)
            >>> await adapter.__aexit__()
        """
        return await self.run_backtest(
            strategy_code=strategy_code,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            parameters=parameters,
            **kwargs,
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"BacktestAdapter(api_base='{self._config.api_base}', initialized={self._is_initialized})"

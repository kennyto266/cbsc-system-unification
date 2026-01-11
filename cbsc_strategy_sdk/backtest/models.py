"""
Pydantic models for backtest API requests and responses.

This module defines the data models used for communicating with
the CBSC backtesting API, including requests, responses, and
status tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class BacktestStatus(str, Enum):
    """Status of a backtest job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BacktestRequest(BaseModel):
    """Request model for running a backtest.

    Attributes:
        strategy_code: Unique identifier for the strategy
        symbols: List of trading symbols to backtest
        start_date: Backtest start date
        end_date: Backtest end date
        parameters: Strategy parameters dictionary
        initial_capital: Starting capital for backtest
        commission_rate: Commission rate per trade (default 0.1%)
        slippage_rate: Slippage rate per trade (default 0.05%)
    """

    strategy_code: str = Field(
        ...,
        description="Unique identifier for the strategy to backtest",
        min_length=1,
    )
    symbols: List[str] = Field(
        ...,
        description="List of trading symbols (e.g., ['AAPL', '0700.HK'])",
        min_length=1,
    )
    start_date: datetime = Field(
        ...,
        description="Backtest start date",
    )
    end_date: datetime = Field(
        ...,
        description="Backtest end date",
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy parameters as key-value pairs",
    )
    initial_capital: float = Field(
        default=1000000.0,
        gt=0,
        description="Initial capital for backtest",
    )
    commission_rate: float = Field(
        default=0.001,
        ge=0,
        le=0.1,
        description="Commission rate per trade (0.1% = 0.001)",
    )
    slippage_rate: float = Field(
        default=0.0005,
        ge=0,
        le=0.05,
        description="Slippage rate per trade (0.05% = 0.0005)",
    )

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: datetime, info) -> datetime:
        """Validate that end_date is after start_date."""
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class BacktestMetrics(BaseModel):
    """Performance metrics from a backtest.

    Attributes:
        total_return: Total return percentage
        annual_return: Annualized return
        sharpe_ratio: Sharpe ratio
        sortino_ratio: Sortino ratio
        max_drawdown: Maximum drawdown percentage
        calmar_ratio: Calmar ratio
        win_rate: Win rate percentage
        profit_factor: Profit factor
        total_trades: Total number of trades
        profit_trades: Number of profitable trades
        avg_profit: Average profit per winning trade
        avg_loss: Average loss per losing trade
    """

    total_return: float = Field(..., description="Total return percentage")
    annual_return: float = Field(..., description="Annualized return percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    sortino_ratio: Optional[float] = Field(None, description="Sortino ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    calmar_ratio: Optional[float] = Field(None, description="Calmar ratio")
    win_rate: float = Field(
        ...,
        ge=0,
        le=100,
        description="Win rate percentage",
    )
    profit_factor: float = Field(..., description="Profit factor")
    total_trades: int = Field(..., ge=0, description="Total number of trades")
    profit_trades: int = Field(..., ge=0, description="Number of profitable trades")
    avg_profit: float = Field(..., description="Average profit per winning trade")
    avg_loss: float = Field(..., description="Average loss per losing trade")


class BacktestTrade(BaseModel):
    """Individual trade record from backtest.

    Attributes:
        trade_id: Unique trade identifier
        symbol: Trading symbol
        entry_time: Entry timestamp
        exit_time: Exit timestamp
        direction: Trade direction ('long' or 'short')
        entry_price: Entry price
        exit_price: Exit price
        quantity: Position size
        pnl: Profit/loss
        pnl_percent: Profit/loss percentage
    """

    trade_id: str = Field(..., description="Unique trade identifier")
    symbol: str = Field(..., description="Trading symbol")
    entry_time: datetime = Field(..., description="Entry timestamp")
    exit_time: datetime = Field(..., description="Exit timestamp")
    direction: str = Field(..., description="Trade direction ('long' or 'short')")
    entry_price: float = Field(..., gt=0, description="Entry price")
    exit_price: float = Field(..., gt=0, description="Exit price")
    quantity: float = Field(..., description="Position size")
    pnl: float = Field(..., description="Profit/loss amount")
    pnl_percent: float = Field(..., description="Profit/loss percentage")


class BacktestJob(BaseModel):
    """Backtest job status and metadata.

    Attributes:
        job_id: Unique job identifier
        status: Current job status
        created_at: Job creation timestamp
        started_at: Job start timestamp
        completed_at: Job completion timestamp
        progress: Progress percentage (0-100)
        current_step: Current step description
        error_message: Error message if failed
    """

    job_id: str = Field(..., description="Unique job identifier")
    status: BacktestStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Progress percentage",
    )
    current_step: str = Field(default="", description="Current step description")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    @property
    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.status == BacktestStatus.RUNNING

    @property
    def is_complete(self) -> bool:
        """Check if job is complete (success or failure)."""
        return self.status in (BacktestStatus.COMPLETED, BacktestStatus.FAILED, BacktestStatus.CANCELLED)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate job duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class BacktestResultData(BaseModel):
    """Complete backtest result data.

    Attributes:
        job: Job metadata
        metrics: Performance metrics
        trades: List of all trades
        equity_curve: List of equity values over time
        parameters: Strategy parameters used
    """

    job: BacktestJob = Field(..., description="Job metadata")
    metrics: BacktestMetrics = Field(..., description="Performance metrics")
    trades: List[BacktestTrade] = Field(default_factory=list, description="List of trades")
    equity_curve: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Equity curve data",
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy parameters used",
    )


# API Response Models
class BacktestSubmitResponse(BaseModel):
    """Response from backtest submission endpoint."""

    success: bool = Field(..., description="Request success status")
    job_id: str = Field(..., description="Submitted job ID")
    status: BacktestStatus = Field(..., description="Initial job status")
    message: str = Field(default="", description="Response message")


class BacktestStatusResponse(BaseModel):
    """Response from backtest status endpoint."""

    success: bool = Field(..., description="Request success status")
    job: Optional[BacktestJob] = Field(None, description="Job status")
    result: Optional[BacktestResultData] = Field(None, description="Result data if complete")
    message: str = Field(default="", description="Response message")

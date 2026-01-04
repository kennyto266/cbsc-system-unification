"""
Backtest-related schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class BacktestStatus(str, Enum):
    """Backtest status values"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BacktestBase(BaseModel):
    """Base backtest schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Backtest name")
    strategy_id: int = Field(..., description="Associated strategy ID")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: float = Field(..., gt=0, description="Initial capital amount")
    config: Dict[str, Any] = Field(default_factory=dict, description="Backtest configuration")


class BacktestCreate(BacktestBase):
    """Backtest creation request"""
    pass


class BacktestUpdate(BaseModel):
    """Backtest update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    config: Optional[Dict[str, Any]] = None


class BacktestMetrics(BaseModel):
    """Backtest performance metrics"""
    total_return: Optional[float] = Field(None, description="Total return percentage")
    annual_return: Optional[float] = Field(None, description="Annualized return")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    sortino_ratio: Optional[float] = Field(None, description="Sortino ratio")
    max_drawdown: Optional[float] = Field(None, description="Maximum drawdown percentage")
    win_rate: Optional[float] = Field(None, description="Win rate percentage")
    profit_factor: Optional[float] = Field(None, description="Profit factor")
    avg_trade: Optional[float] = Field(None, description="Average trade profit/loss")
    total_trades: Optional[int] = Field(None, description="Total number of trades")


class BacktestResponse(BacktestBase):
    """Backtest response"""
    id: int = Field(..., description="Backtest ID")
    user_id: int = Field(..., description="Owner user ID")
    status: BacktestStatus = Field(..., description="Backtest status")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Last update time")
    started_at: Optional[datetime] = Field(None, description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    metrics: Optional[BacktestMetrics] = Field(None, description="Performance metrics")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        from_attributes = True


class BacktestListResponse(BaseModel):
    """Backtest list item (simplified)"""
    id: int
    name: str
    strategy_id: int
    status: BacktestStatus
    start_date: datetime
    end_date: datetime
    created_at: datetime
    metrics: Optional[BacktestMetrics] = None

    class Config:
        from_attributes = True


class BacktestStartRequest(BaseModel):
    """Request to start a backtest"""
    config: Optional[Dict[str, Any]] = Field(None, description="Optional config overrides")


class TradeRecord(BaseModel):
    """Individual trade record"""
    entry_time: datetime = Field(..., description="Trade entry time")
    exit_time: Optional[datetime] = Field(None, description="Trade exit time")
    symbol: str = Field(..., description="Trading symbol")
    side: str = Field(..., description="Trade side (long/short)")
    entry_price: float = Field(..., description="Entry price")
    exit_price: Optional[float] = Field(None, description="Exit price")
    quantity: float = Field(..., description="Trade quantity")
    profit_loss: Optional[float] = Field(None, description="Trade profit/loss")
    profit_loss_pct: Optional[float] = Field(None, description="Profit/loss percentage")

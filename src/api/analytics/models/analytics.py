"""
Analytics data models for strategy performance metrics
"""
from datetime import datetime, date
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field
from decimal import Decimal


class Timeframe(str, Enum):
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1m"
    QUARTER = "1q"
    YEAR = "1y"
    YTD = "ytd"
    ALL = "all"


class MetricType(str, Enum):
    RETURN = "return"
    VOLATILITY = "volatility"
    SHARPE = "sharpe"
    DRAWDOWN = "drawdown"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"


class PerformanceMetrics(BaseModel):
    """Strategy performance metrics model"""
    strategy_id: str
    strategy_name: str

    # Return metrics
    total_return: Decimal = Field(..., description="Total return percentage")
    annualized_return: Decimal = Field(..., description="Annualized return percentage")
    daily_return: Optional[Decimal] = Field(None, description="Daily return percentage")
    weekly_return: Optional[Decimal] = Field(None, description="Weekly return percentage")
    monthly_return: Optional[Decimal] = Field(None, description="Monthly return percentage")

    # Risk metrics
    volatility: Decimal = Field(..., description="Annualized volatility")
    sharpe_ratio: Optional[Decimal] = Field(None, description="Sharpe ratio")
    sortino_ratio: Optional[Decimal] = Field(None, description="Sortino ratio")
    calmar_ratio: Optional[Decimal] = Field(None, description="Calmar ratio")
    max_drawdown: Decimal = Field(..., description="Maximum drawdown percentage")
    var_95: Optional[Decimal] = Field(None, description="95% Value at Risk")

    # Trading metrics
    win_rate: Optional[Decimal] = Field(None, description="Win rate percentage")
    profit_factor: Optional[Decimal] = Field(None, description="Profit factor")
    avg_trade_return: Optional[Decimal] = Field(None, description="Average trade return")
    total_trades: Optional[int] = Field(None, description="Total number of trades")
    winning_trades: Optional[int] = Field(None, description="Number of winning trades")

    # Timing
    inception_date: date = Field(..., description="Strategy inception date")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v) if v else None,
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }


class TimeSeriesPoint(BaseModel):
    """Time series data point"""
    date: date
    value: Decimal
    benchmark: Optional[Decimal] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else None,
            date: lambda v: v.isoformat()
        }


class ReturnsData(BaseModel):
    """Returns data over time"""
    strategy_id: str
    timeframe: Timeframe
    data: List[TimeSeriesPoint]

    # Summary statistics
    total_return: Decimal
    annualized_return: Decimal
    volatility: Decimal
    sharpe_ratio: Optional[Decimal] = None
    max_drawdown: Decimal

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else None
        }


class AssetAllocation(BaseModel):
    """Asset allocation for portfolio"""
    symbol: str
    name: str
    value: Decimal
    weight: Decimal
    sector: Optional[str] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else None
        }


class SectorAllocation(BaseModel):
    """Sector allocation for portfolio"""
    sector: str
    weight: Decimal
    value: Decimal

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else None
        }


class PortfolioOverview(BaseModel):
    """Portfolio overview data"""
    user_id: int
    total_value: Decimal
    cash_balance: Decimal
    invested_amount: Decimal

    # Allocations
    asset_allocations: List[AssetAllocation]
    sector_allocations: List[SectorAllocation]

    # Performance
    today_change: Decimal
    today_change_pct: Decimal
    total_return: Decimal
    total_return_pct: Decimal

    # Top performers
    top_gainers: List[AssetAllocation]
    top_losers: List[AssetAllocation]

    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else None,
            datetime: lambda v: v.isoformat()
        }


class RealTimeUpdate(BaseModel):
    """Real-time update message"""
    type: str  # 'strategy_status', 'performance', 'portfolio'
    strategy_id: Optional[str] = None
    user_id: Optional[int] = None
    data: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
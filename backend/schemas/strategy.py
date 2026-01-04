"""
Strategy-related schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class StrategyStatus(str, Enum):
    """Strategy status values"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ARCHIVED = "archived"


class StrategyCategory(str, Enum):
    """Strategy category types"""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    FUNDAMENTAL = "fundamental"
    TECHNICAL = "technical"
    PORTFOLIO = "portfolio"
    CUSTOM = "custom"


class StrategyBase(BaseModel):
    """Base strategy schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Strategy name")
    description: Optional[str] = Field(None, description="Strategy description")
    category: StrategyCategory = Field(..., description="Strategy category")
    config: Dict[str, Any] = Field(default_factory=dict, description="Strategy configuration")
    status: StrategyStatus = Field(StrategyStatus.DRAFT, description="Strategy status")


class StrategyCreate(StrategyBase):
    """Strategy creation request"""
    pass


class StrategyUpdate(BaseModel):
    """Strategy update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[StrategyCategory] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[StrategyStatus] = None


class PerformanceMetrics(BaseModel):
    """Strategy performance metrics"""
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    max_drawdown: Optional[float] = Field(None, description="Maximum drawdown")
    total_return: Optional[float] = Field(None, description="Total return")
    win_rate: Optional[float] = Field(None, description="Win rate")
    profit_factor: Optional[float] = Field(None, description="Profit factor")
    avg_return: Optional[float] = Field(None, description="Average return")


class StrategyResponse(StrategyBase):
    """Strategy response"""
    id: int = Field(..., description="Strategy ID")
    user_id: int = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Last update time")
    last_run: Optional[datetime] = Field(None, description="Last execution time")
    performance: Optional[PerformanceMetrics] = Field(None, description="Performance metrics")

    class Config:
        from_attributes = True


class StrategyListResponse(BaseModel):
    """Strategy list item (simplified)"""
    id: int
    name: str
    category: StrategyCategory
    status: StrategyStatus
    created_at: datetime
    last_run: Optional[datetime] = None

    class Config:
        from_attributes = True


class StrategyToggleRequest(BaseModel):
    """Strategy toggle request"""
    is_active: bool = Field(..., description="Desired active state")


class BatchOperationRequest(BaseModel):
    """Batch operation request"""
    strategy_ids: List[int] = Field(..., min_items=1, description="List of strategy IDs")
    operation: str = Field(..., description="Operation to perform: start, stop, delete")

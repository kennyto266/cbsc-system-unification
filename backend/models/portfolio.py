"""
投资组合模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Holding(BaseModel):
    """持仓信息"""
    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    quantity: float = Field(..., description="持仓数量")
    average_price: float = Field(..., description="平均成本")
    current_price: Optional[float] = Field(None, description="当前价格")
    value: Optional[float] = Field(None, description="当前价值")
    return_pct: Optional[float] = Field(None, description="收益率")

class Portfolio(BaseModel):
    """投资组合"""
    id: str = Field(..., description="投资组合ID")
    name: str = Field(..., description="投资组合名称")
    description: Optional[str] = Field(None, description="投资组合描述")
    total_value: float = Field(default=0, description="总价值")
    total_return: float = Field(default=0, description="总收益率")
    holdings: List[Holding] = Field(default=[], description="持仓列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

class CreatePortfolioRequest(BaseModel):
    """创建投资组合请求"""
    name: str = Field(..., description="投资组合名称")
    description: Optional[str] = Field(None, description="投资组合描述")

class UpdatePortfolioRequest(BaseModel):
    """更新投资组合请求"""
    name: Optional[str] = Field(None, description="投资组合名称")
    description: Optional[str] = Field(None, description="投资组合描述")

class AddHoldingRequest(BaseModel):
    """添加持仓请求"""
    symbol: str = Field(..., description="股票代码")
    quantity: float = Field(..., description="持仓数量")
    average_price: float = Field(..., description="平均成本")

class PortfolioSummary(BaseModel):
    """投资组合摘要"""
    total_portfolios: int = Field(..., description="投资组合总数")
    total_value: float = Field(..., description="总价值")
    total_return: float = Field(..., description="总收益率")
    best_performer: Optional[str] = Field(None, description="表现最佳的投资组合")
    worst_performer: Optional[str] = Field(None, description="表现最差的投资组合")

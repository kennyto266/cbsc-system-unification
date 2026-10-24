"""
策略模型
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, date

class Strategy(BaseModel):
    """策略"""
    id: str = Field(..., description="策略ID")
    name: str = Field(..., description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    strategy_type: str = Field(..., description="策略类型")
    parameters: Optional[Dict[str, Any]] = Field(None, description="策略参数")
    is_active: bool = Field(default=True, description="是否激活")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

class BacktestResult(BaseModel):
    """回测结果"""
    id: str = Field(..., description="回测结果ID")
    strategy_id: str = Field(..., description="策略ID")
    symbol: str = Field(..., description="股票代码")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    total_return: Optional[float] = Field(None, description="总收益率")
    annual_return: Optional[float] = Field(None, description="年化收益率")
    max_drawdown: Optional[float] = Field(None, description="最大回撤")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    win_rate: Optional[float] = Field(None, description="胜率")
    total_trades: Optional[int] = Field(None, description="总交易次数")
    profit_trades: Optional[int] = Field(None, description="盈利交易次数")
    loss_trades: Optional[int] = Field(None, description="亏损交易次数")
    avg_profit: Optional[float] = Field(None, description="平均盈利")
    avg_loss: Optional[float] = Field(None, description="平均亏损")
    profit_factor: Optional[float] = Field(None, description="盈利因子")
    status: str = Field(default="completed", description="状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

class BacktestRequest(BaseModel):
    """回测请求"""
    symbol: str = Field(..., description="股票代码")
    strategy: Dict[str, Any] = Field(..., description="策略配置")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")

class Trade(BaseModel):
    """交易记录"""
    date: datetime = Field(..., description="交易日期")
    symbol: str = Field(..., description="股票代码")
    action: str = Field(..., description="交易动作")
    quantity: float = Field(..., description="交易数量")
    price: float = Field(..., description="交易价格")
    value: float = Field(..., description="交易金额")
    return_pct: Optional[float] = Field(None, description="收益率")

class StrategyParameter(BaseModel):
    """策略参数"""
    name: str = Field(..., description="参数名称")
    type: str = Field(..., description="参数类型")
    default: Any = Field(..., description="默认值")
    min_value: Optional[float] = Field(None, description="最小值")
    max_value: Optional[float] = Field(None, description="最大值")
    description: Optional[str] = Field(None, description="参数描述")

class StrategyTemplate(BaseModel):
    """策略模板"""
    id: str = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    parameters: List[StrategyParameter] = Field(..., description="参数列表")
    category: str = Field(..., description="策略分类")

"""
市场数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class StockInfo(BaseModel):
    """股票基本信息"""
    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    sector: Optional[str] = Field(None, description="行业板块")
    industry: Optional[str] = Field(None, description="细分行业")
    market_cap: Optional[float] = Field(None, description="市值")
    pe_ratio: Optional[float] = Field(None, description="市盈率")
    dividend_yield: Optional[float] = Field(None, description="股息率")
    currency: str = Field(default="HKD", description="货币")
    exchange: str = Field(default="HKEX", description="交易所")

class MarketData(BaseModel):
    """市场数据"""
    symbol: str = Field(..., description="股票代码")
    timestamp: datetime = Field(..., description="时间戳")
    open_price: float = Field(..., description="开盘价")
    high_price: float = Field(..., description="最高价")
    low_price: float = Field(..., description="最低价")
    close_price: float = Field(..., description="收盘价")
    volume: int = Field(..., description="成交量")

class TechnicalIndicators(BaseModel):
    """技术指标"""
    symbol: str = Field(..., description="股票代码")
    timestamp: datetime = Field(..., description="时间戳")
    sma_20: Optional[float] = Field(None, description="20日简单移动平均")
    sma_50: Optional[float] = Field(None, description="50日简单移动平均")
    ema_12: Optional[float] = Field(None, description="12日指数移动平均")
    ema_26: Optional[float] = Field(None, description="26日指数移动平均")
    rsi: Optional[float] = Field(None, description="相对强弱指数")
    macd: Optional[float] = Field(None, description="MACD线")
    macd_signal: Optional[float] = Field(None, description="MACD信号线")
    macd_histogram: Optional[float] = Field(None, description="MACD柱状图")
    bollinger_upper: Optional[float] = Field(None, description="布林带上轨")
    bollinger_middle: Optional[float] = Field(None, description="布林带中轨")
    bollinger_lower: Optional[float] = Field(None, description="布林带下轨")
    atr: Optional[float] = Field(None, description="平均真实波幅")
    volume_sma: Optional[float] = Field(None, description="成交量移动平均")
    volume_ratio: Optional[float] = Field(None, description="成交量比率")

class MarketDataRequest(BaseModel):
    """市场数据请求"""
    symbol: str = Field(..., description="股票代码")
    period: str = Field(default="1mo", description="时间周期")
    interval: str = Field(default="1d", description="时间间隔")

class TechnicalAnalysisRequest(BaseModel):
    """技术分析请求"""
    symbol: str = Field(..., description="股票代码")
    data: List[MarketData] = Field(..., description="市场数据")

class StockSearchRequest(BaseModel):
    """股票搜索请求"""
    query: str = Field(..., description="搜索关键词")
    limit: int = Field(default=10, description="返回数量限制")

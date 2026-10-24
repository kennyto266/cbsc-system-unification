"""
市場數據模型

定義市場數據、技術指標、情緒數據等相關的數據模型。
"""

from datetime import datetime, timezone, date
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, NUMERIC
from pydantic import BaseModel, Field, validator
from decimal import Decimal

from .unified_base import UnifiedBaseModel, UnifiedSchema

class MarketData(UnifiedBaseModel):
    """市場數據模型"""

    __tablename__ = 'market_data'

    # 基本標識
    symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(20), nullable=False, index=True)
    asset_type = Column(String(20), nullable=False, index=True)  # stock, etf, future, forex, crypto

    # 時間和時間週期
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)  # 1m, 5m, 1h, 1d, 1w, 1M

    # 價格數據 (使用NUMERIC確保精度)
    open_price = Column(NUMERIC(15, 4), nullable=False)
    high_price = Column(NUMERIC(15, 4), nullable=False)
    low_price = Column(NUMERIC(15, 4), nullable=False)
    close_price = Column(NUMERIC(15, 4), nullable=False)
    adjusted_close = Column(NUMERIC(15, 4), nullable=True)

    # 成交數據
    volume = Column(Integer, nullable=False)
    turnover = Column(NUMERIC(20, 2), nullable=True)  # 成交額
    vwap = Column(NUMERIC(15, 4), nullable=True)  # 成交量加權平均價

    # 市值和估值
    market_cap = Column(NUMERIC(20, 2), nullable=True)
    shares_outstanding = Column(Integer, nullable=True)

    # 基本指標
    pe_ratio = Column(NUMERIC(10, 4), nullable=True)
    pb_ratio = Column(NUMERIC(10, 4), nullable=True)
    dividend_yield = Column(NUMERIC(8, 4), nullable=True)
    beta = Column(NUMERIC(6, 4), nullable=True)

    # 數據質量和來源
    data_source = Column(String(50), nullable=False, index=True)
    quality_score = Column(Float, default=1.0, nullable=False)
    is_adjusted = Column(Boolean, default=False, nullable=False)

    # 複合索引
    __table_args__ = (
        Index('idx_market_data_symbol_time', 'symbol', 'timestamp', 'timeframe'),
        Index('idx_market_data_exchange_symbol', 'exchange', 'symbol', 'timestamp'),
        Index('idx_market_data_timestamp_timeframe', 'timestamp', 'timeframe'),
    )

    def get_price_change(self) -> Optional[float]:
        """計算價格變化"""
        if self.open_price and self.close_price:
            return float((self.close_price - self.open_price) / self.open_price * 100)
        return None

    def get_price_range(self) -> Optional[float]:
        """計算價格區間"""
        if self.high_price and self.low_price:
            return float((self.high_price - self.low_price) / self.low_price * 100)
        return None

class TechnicalIndicator(UnifiedBaseModel):
    """技術指標模型"""

    __tablename__ = 'technical_indicators'

    # 關聯信息
    market_data_id = Column(String(36), ForeignKey('market_data.id'), nullable=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)

    # 指標分類和名稱
    indicator_type = Column(String(50), nullable=False, index=True)  # trend, momentum, volatility, volume
    indicator_name = Column(String(50), nullable=False, index=True)  # sma, ema, rsi, macd, bollinger
    period = Column(Integer, nullable=True, index=True)  # 計算週期

    # 指標值 (JSON格式支持多種指標)
    values = Column(JSONB, nullable=False)  # {"sma": 100.5, "signal": "buy", "strength": 0.8}
    parameters = Column(JSONB, nullable=True)  # {"period": 20, "std_dev": 2}

    # 指標狀態
    signal = Column(String(20), nullable=True)  # buy, sell, hold, neutral
    confidence = Column(Float, nullable=True)  # 0-1
    strength = Column(Float, nullable=True)  # 0-1

    # 計算信息
    calculated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    calculation_method = Column(String(50), nullable=True)
    data_points_used = Column(Integer, nullable=True)

    # 複合索引
    __table_args__ = (
        Index('idx_technical_symbol_time', 'symbol', 'timestamp', 'indicator_name'),
        Index('idx_technical_type_name', 'indicator_type', 'indicator_name', 'timestamp'),
    )

class SentimentData(UnifiedBaseModel):
    """情緒數據模型"""

    __tablename__ = 'sentiment_data'

    # 基本標識
    symbol = Column(String(20), nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)  # news, social, analyst, options
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # 情緒分數
    overall_score = Column(Float, nullable=False)  # -1 to 1
    sentiment_score = Column(Float, nullable=True)  # -1 to 1
    fear_greed_index = Column(Float, nullable=True)  # 0 to 100

    # 分類情緒
    news_sentiment = Column(Float, nullable=True)
    social_sentiment = Column(Float, nullable=True)
    analyst_sentiment = Column(Float, nullable=True)
    options_sentiment = Column(Float, nullable=True)

    # 統計數據
    mention_count = Column(Integer, default=0, nullable=False)
    positive_count = Column(Integer, default=0, nullable=False)
    negative_count = Column(Integer, default=0, nullable=False)
    neutral_count = Column(Integer, default=0, nullable=False)

    # 權重和可信度
    weight = Column(Float, default=1.0, nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    reliability_score = Column(Float, default=1.0, nullable=False)

    # 關鍵詞和主題
    keywords = Column(JSONB, nullable=True)
    topics = Column(JSONB, nullable=True)

    # 元數據
    collection_method = Column(String(50), nullable=True)
    processing_algorithm = Column(String(50), nullable=True)
    raw_data_reference = Column(String(500), nullable=True)

    # 複合索引
    __table_args__ = (
        Index('idx_sentiment_symbol_time', 'symbol', 'timestamp', 'source'),
        Index('idx_sentiment_overall_score', 'overall_score', 'timestamp'),
    )

class EconomicIndicator(UnifiedBaseModel):
    """經濟指標模型"""

    __tablename__ = 'economic_indicators'

    # 基本信息分類
    indicator_code = Column(String(50), nullable=False, index=True)
    indicator_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, index=True)  # gdp, inflation, employment, interest_rate
    country = Column(String(10), nullable=False, index=True)  # US, CN, HK, etc.

    # 數據值
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)
    period_type = Column(String(20), nullable=False)  # monthly, quarterly, yearly
    period_end_date = Column(DateTime(timezone=True), nullable=False, index=True)

    # 比較數據
    previous_value = Column(Float, nullable=True)
    change_percent = Column(Float, nullable=True)
    year_over_year = Column(Float, nullable=True)

    # 預測和共識
    forecast_value = Column(Float, nullable=True)
    consensus_value = Column(Float, nullable=True)
    surprise_percent = Column(Float, nullable=True)

    # 重要性和影響
    importance_level = Column(String(20), nullable=False)  # low, medium, high, critical
    market_impact = Column(JSONB, nullable=True)  # {"equity": 0.8, "bond": -0.3, "currency": 0.5}

    # 數據來源和質量
    source = Column(String(50), nullable=False)
    release_time = Column(DateTime(timezone=True), nullable=False)
    reliability_score = Column(Float, default=1.0, nullable=False)

    # 複合索引
    __table_args__ = (
        Index('idx_economic_code_date', 'indicator_code', 'period_end_date'),
        Index('idx_economic_category_date', 'category', 'period_end_date'),
        Index('idx_economic_importance_date', 'importance_level', 'period_end_date'),
    )

# Pydantic Schemas
class MarketDataBaseSchema(UnifiedSchema):
    """市場數據基礎Schema"""
    symbol: str = Field(..., min_length=1, max_length=20, description="交易代碼")
    exchange: str = Field(..., min_length=1, max_length=20, description="交易所")
    asset_type: str = Field(..., description="資產類型")
    timestamp: datetime
    timeframe: str = Field(..., description="時間週期")
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int = Field(..., ge=0, description="成交量")

class MarketDataCreateSchema(MarketDataBaseSchema):
    """創建市場數據Schema"""
    adjusted_close: Optional[Decimal] = None
    turnover: Optional[Decimal] = None
    market_cap: Optional[Decimal] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    data_source: str = Field(..., description="數據源")

class MarketDataResponseSchema(MarketDataBaseSchema):
    """市場數據響應Schema"""
    adjusted_close: Optional[Decimal] = None
    turnover: Optional[Decimal] = None
    vwap: Optional[float] = None
    market_cap: Optional[Decimal] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    beta: Optional[float] = None
    data_source: str
    quality_score: float
    price_change_percent: Optional[float] = None
    price_range_percent: Optional[float] = None

    class Config:
        from_attributes = True

class TechnicalIndicatorBaseSchema(UnifiedSchema):
    """技術指標基礎Schema"""
    symbol: str = Field(..., min_length=1, max_length=20)
    timestamp: datetime
    timeframe: str
    indicator_type: str
    indicator_name: str
    period: Optional[int] = None
    values: Dict[str, Any]
    parameters: Optional[Dict[str, Any]] = None
    signal: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)
    strength: Optional[float] = Field(None, ge=0, le=1)

class TechnicalIndicatorResponseSchema(TechnicalIndicatorBaseSchema):
    """技術指標響應Schema"""
    calculated_at: datetime
    calculation_method: Optional[str] = None
    data_points_used: Optional[int] = None

    class Config:
        from_attributes = True

class SentimentDataBaseSchema(UnifiedSchema):
    """情緒數據基礎Schema"""
    symbol: str = Field(..., min_length=1, max_length=20)
    source: str
    timestamp: datetime
    overall_score: float = Field(..., ge=-1, le=1)
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1)
    fear_greed_index: Optional[float] = Field(None, ge=0, le=100)

class SentimentDataResponseSchema(SentimentDataBaseSchema):
    """情緒數據響應Schema"""
    news_sentiment: Optional[float] = None
    social_sentiment: Optional[float] = None
    analyst_sentiment: Optional[float] = None
    options_sentiment: Optional[float] = None
    mention_count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    weight: float
    confidence: float
    reliability_score: float
    keywords: Optional[List[str]] = None
    topics: Optional[List[str]] = None

    class Config:
        from_attributes = True

class EconomicIndicatorBaseSchema(UnifiedSchema):
    """經濟指標基礎Schema"""
    indicator_code: str = Field(..., min_length=1, max_length=50)
    indicator_name: str
    category: str
    country: str = Field(..., min_length=2, max_length=10)
    value: float
    unit: Optional[str] = None
    period_type: str
    period_end_date: datetime

class EconomicIndicatorResponseSchema(EconomicIndicatorBaseSchema):
    """經濟指標響應Schema"""
    previous_value: Optional[float] = None
    change_percent: Optional[float] = None
    year_over_year: Optional[float] = None
    forecast_value: Optional[float] = None
    consensus_value: Optional[float] = None
    surprise_percent: Optional[float] = None
    importance_level: str
    market_impact: Optional[Dict[str, float]] = None
    source: str
    release_time: datetime
    reliability_score: float

    class Config:
        from_attributes = True
"""
统一数据模型

定义价格和非价格数据的统一数据结构和基础模型。

Task #31: Data Flow Unification - Price and Non-Price Integration
"""

from datetime import datetime, timezone
from typing import Optional, Any, Dict, List, Union
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.models.unified_base import UnifiedBaseModel, UnifiedBase

class DataSource(str, Enum):
    """数据源类型"""
    PRICE = "price"
    HKMA = "hkma"
    SENTIMENT = "sentiment"
    ALTERNATIVE = "alternative"
    NEWS = "news"
    SOCIAL = "social"
    ECONOMIC = "economic"

class DataType(str, Enum):
    """数据类型"""
    OHLCV = "ohlcv"  # 开高低收盘量
    MACRO = "macro"  # 宏观数据
    SENTIMENT = "sentiment"  # 情绪数据
    ALTERNATIVE = "alternative"  # 另类数据
    INDICATOR = "indicator"  # 技术指标

class PriceType(str, Enum):
    """价格类型"""
    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"
    ADJUSTED_CLOSE = "adjusted_close"
    VOLUME = "volume"

class HKMAIndicator(str, Enum):
    """HKMA指标类型"""
    HIBOR = "hibor"  # 香港银行同业拆借利率
    MONETARY_BASE = "monetary_base"  # 货币基础
    EXCHANGE_RATE = "exchange_rate"  # 汇率
    INTERBANK_RATE = "interbank_rate"  # 银行同业利率
    RESERVE_REQUIREMENTS = "reserve_requirements"  # 准备金要求

class SentimentType(str, Enum):
    """情绪类型"""
    NEWS_SENTIMENT = "news_sentiment"  # 新闻情绪
    SOCIAL_SENTIMENT = "social_sentiment"  # 社交媒体情绪
    ANALYST_SENTIMENT = "analyst_sentiment"  # 分析师情绪
    MARKET_SENTIMENT = "market_sentiment"  # 市场情绪

class UnifiedDataPointSchema(UnifiedBaseModel):
    """统一数据点Schema"""
    symbol: str = Field(..., description="股票代码或资产标识")
    timestamp: datetime = Field(..., description="数据时间戳")
    source: DataSource = Field(..., description="数据源")
    data_type: DataType = Field(..., description="数据类型")
    value: Union[float, Decimal, str] = Field(..., description="数据值")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    quality_score: float = Field(default=1.0, ge=0.0, le=1.0, description="质量评分")
    is_valid: bool = Field(default=True, description="数据是否有效")

    @validator('timestamp', pre=True)
    def parse_timestamp(cls, v):
        """解析时间戳"""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError("Invalid timestamp format")
        return v

    @validator('value', pre=True)
    def parse_value(cls, v):
        """解析数值"""
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                return v
        return v

class PriceDataSchema(UnifiedDataPointSchema):
    """价格数据Schema"""
    data_type: DataType = Field(DataType.OHLCV, const=True)
    source: DataSource = Field(DataSource.PRICE, const=True)
    open_price: Optional[float] = Field(None, description="开盘价")
    high_price: Optional[float] = Field(None, description="最高价")
    low_price: Optional[float] = Field(None, description="最低价")
    close_price: Optional[float] = Field(None, description="收盘价")
    adjusted_close: Optional[float] = Field(None, description="调整后收盘价")
    volume: Optional[int] = Field(None, ge=0, description="成交量")
    market_cap: Optional[float] = Field(None, ge=0, description="市值")

    @validator('high_price')
    def validate_high_price(cls, v, values):
        """验证最高价"""
        if v is not None and 'low_price' in values and values['low_price'] is not None:
            if v < values['low_price']:
                raise ValueError('最高价不能低于最低价')
        return v

    @validator('close_price')
    def validate_close_price(cls, v, values):
        """验证收盘价"""
        if v is not None:
            if 'high_price' in values and values['high_price'] is not None:
                if v > values['high_price']:
                    raise ValueError('收盘价不能高于最高价')
            if 'low_price' in values and values['low_price'] is not None:
                if v < values['low_price']:
                    raise ValueError('收盘价不能低于最低价')
        return v

class HKMADataSchema(UnifiedDataPointSchema):
    """HKMA数据Schema"""
    data_type: DataType = Field(DataType.MACRO, const=True)
    source: DataSource = Field(DataSource.HKMA, const=True)
    indicator: HKMAIndicator = Field(..., description="HKMA指标类型")
    currency: Optional[str] = Field(None, description="货币单位")
    period_type: Optional[str] = Field(None, description="周期类型")
    frequency: Optional[str] = Field(None, description="数据频率")

class SentimentDataSchema(UnifiedDataPointSchema):
    """情绪数据Schema"""
    data_type: DataType = Field(DataType.SENTIMENT, const=True)
    source: DataSource = Field(DataSource.SENTIMENT, const=True)
    sentiment_type: SentimentType = Field(..., description="情绪类型")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="置信度")
    sentiment_value: Optional[float] = Field(None, ge=-1.0, le=1.0, description="情绪值(-1到1)")
    source_count: Optional[int] = Field(None, ge=0, description="数据源数量")
    language: Optional[str] = Field(None, description="语言")

class AlternativeDataSchema(UnifiedDataPointSchema):
    """另类数据Schema"""
    data_type: DataType = Field(DataType.ALTERNATIVE, const=True)
    source: DataSource = Field(DataSource.ALTERNATIVE, const=True)
    category: Optional[str] = Field(None, description="数据类别")
    provider: Optional[str] = Field(None, description="数据提供者")
    granularity: Optional[str] = Field(None, description="数据粒度")

class UnifiedDataSeriesSchema(UnifiedBaseModel):
    """统一数据序列Schema"""
    symbol: str = Field(..., description="股票代码或资产标识")
    source: DataSource = Field(..., description="数据源")
    data_type: DataType = Field(..., description="数据类型")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    data_points: List[Union[PriceDataSchema, HKMADataSchema, SentimentDataSchema, AlternativeDataSchema]] = Field(..., description="数据点列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="序列元数据")
    quality_summary: Optional[Dict[str, Any]] = Field(None, description="质量汇总")

    @validator('data_points')
    def validate_data_points(cls, v):
        """验证数据点"""
        if not v:
            raise ValueError("数据点列表不能为空")
        return v

class QualityResultSchema(UnifiedBaseModel):
    """质量结果Schema"""
    data_type: str = Field(..., description="数据类型")
    symbol: str = Field(..., description="股票代码")
    total_points: int = Field(..., ge=0, description="总数据点数")
    valid_points: int = Field(..., ge=0, description="有效数据点数")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="总体质量评分")
    quality_level: str = Field(..., description="质量等级")
    checks: Dict[str, Any] = Field(default_factory=dict, description="检查结果")
    recommendations: List[str] = Field(default_factory=list, description="改进建议")
    timestamp: datetime = Field(default_factory=datetime.now, description="验证时间")

# SQLAlchemy Models

class UnifiedDataPoint(UnifiedBase):
    """统一数据点数据库模型"""
    __tablename__ = "unified_data_points"

    # 数据标识
    symbol = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    source = Column(String(20), nullable=False, index=True)
    data_type = Column(String(20), nullable=False, index=True)

    # 数据值
    value = Column(String(100), nullable=False)

    # 元数据和质量
    metadata = Column(JSON, nullable=True)
    quality_score = Column(Float, default=1.0)
    is_valid = Column(Boolean, default=True)

    # 复合索引
    __table_args__ = (
        {'schema': 'unified'}
    )

class PriceData(UnifiedBase):
    """价格数据数据库模型"""
    __tablename__ = "price_data"

    # 继承统一数据点字段
    data_point_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))

    # 价格特定字段
    symbol = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    open_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    close_price = Column(Float, nullable=True)
    adjusted_close = Column(Float, nullable=True)
    volume = Column(Integer, nullable=True)
    market_cap = Column(Float, nullable=True)

    __table_args__ = (
        {'schema': 'unified'}
    )

class HKMAData(UnifiedBase):
    """HKMA数据数据库模型"""
    __tablename__ = "hkma_data"

    # 基础字段
    symbol = Column(String(50), nullable=True, index=True)  # 可能为宏观经济指标
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    indicator = Column(String(50), nullable=False, index=True)
    value = Column(Float, nullable=False)

    # HKMA特定字段
    currency = Column(String(10), nullable=True)
    period_type = Column(String(20), nullable=True)
    frequency = Column(String(20), nullable=True)

    # 元数据
    metadata = Column(JSON, nullable=True)
    quality_score = Column(Float, default=1.0)

    __table_args__ = (
        {'schema': 'unified'}
    )

class SentimentData(UnifiedBase):
    """情绪数据数据库模型"""
    __tablename__ = "sentiment_data"

    # 基础字段
    symbol = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    sentiment_type = Column(String(50), nullable=False, index=True)
    value = Column(Float, nullable=False)

    # 情绪特定字段
    confidence = Column(Float, nullable=True)
    sentiment_value = Column(Float, nullable=True)
    source_count = Column(Integer, nullable=True)
    language = Column(String(10), nullable=True)

    # 元数据和质量
    metadata = Column(JSON, nullable=True)
    quality_score = Column(Float, default=1.0)

    __table_args__ = (
        {'schema': 'unified'}
    )

class AlternativeData(UnifiedBase):
    """另类数据数据库模型"""
    __tablename__ = "alternative_data"

    # 基础字段
    symbol = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)
    data_type = Column(String(50), nullable=False, index=True)
    value = Column(Float, nullable=False)

    # 另类数据特定字段
    category = Column(String(100), nullable=True)
    provider = Column(String(100), nullable=True)
    granularity = Column(String(50), nullable=True)

    # 元数据和质量
    metadata = Column(JSON, nullable=True)
    quality_score = Column(Float, default=1.0)

    __table_args__ = (
        {'schema': 'unified'}
    )

class DataSyncLog(UnifiedBase):
    """数据同步日志"""
    __tablename__ = "data_sync_log"

    # 同步信息
    task_id = Column(String(100), nullable=False, index=True)
    symbol = Column(String(50), nullable=True, index=True)
    source = Column(String(20), nullable=False, index=True)

    # 同步结果
    status = Column(String(20), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    records_processed = Column(Integer, default=0)
    records_success = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)

    # 错误信息
    error_message = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)

    __table_args__ = (
        {'schema': 'unified'}
    )

# 数据转换器

class ModelConverter:
    """模型转换器"""

    @staticmethod
    def schema_to_db_model(schema: UnifiedDataPointSchema) -> UnifiedDataPoint:
        """将Schema转换为数据库模型"""
        return UnifiedDataPoint(
            symbol=schema.symbol,
            timestamp=schema.timestamp,
            source=schema.source.value,
            data_type=schema.data_type.value,
            value=str(schema.value),
            metadata=schema.metadata,
            quality_score=schema.quality_score,
            is_valid=schema.is_valid
        )

    @staticmethod
    def db_model_to_schema(model: UnifiedDataPoint) -> UnifiedDataPointSchema:
        """将数据库模型转换为Schema"""
        try:
            value = float(model.value)
        except (ValueError, TypeError):
            value = model.value

        return UnifiedDataPointSchema(
            symbol=model.symbol,
            timestamp=model.timestamp,
            source=DataSource(model.source),
            data_type=DataType(model.data_type),
            value=value,
            metadata=model.metadata or {},
            quality_score=model.quality_score,
            is_valid=model.is_valid
        )

# 导出所有模型
__all__ = [
    # Enums
    'DataSource',
    'DataType',
    'PriceType',
    'HKMAIndicator',
    'SentimentType',

    # Pydantic Schemas
    'UnifiedDataPointSchema',
    'PriceDataSchema',
    'HKMADataSchema',
    'SentimentDataSchema',
    'AlternativeDataSchema',
    'UnifiedDataSeriesSchema',
    'QualityResultSchema',

    # SQLAlchemy Models
    'UnifiedDataPoint',
    'PriceData',
    'HKMAData',
    'SentimentData',
    'AlternativeData',
    'DataSyncLog',

    # Utilities
    'ModelConverter'
]
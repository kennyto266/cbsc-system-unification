#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非价格策略API响应模型 - Non-Price Strategy API Response Models
定义统一的API响应格式，支持HKMA宏观数据、情绪分析和策略集成
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class SignalType(str, Enum):
    """信号类型枚举"""
    HIBOR = "hibor"
    MONETARY_BASE = "monetary_base"
    EXCHANGE_RATE = "exchange_rate"
    LIQUIDITY = "liquidity"
    SENTIMENT = "sentiment"
    TECHNICAL = "technical"


class TrendDirection(str, Enum):
    """趋势方向枚举"""
    UP = "UP"
    DOWN = "DOWN"
    STABLE = "STABLE"
    NEUTRAL = "NEUTRAL"


class DataSource(str, Enum):
    """数据源枚举"""
    HKMA = "hkma"
    SENTIMENT_API = "sentiment_api"
    TECHNICAL_ANALYSIS = "technical_analysis"
    INTERNAL_CALCULATION = "internal_calculation"


# Base Response Models
class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(description="请求是否成功")
    message: str = Field(description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间戳")


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    success: bool = False
    error: Dict[str, Any] = Field(description="错误详情")


# HKMA Data Response Models
class HIBORRate(BaseModel):
    """HIBOR利率数据模型"""
    tenor: str = Field(description="期限，如1M、3M、6M、12M")
    rate: float = Field(description="利率值（百分比）")
    change: Optional[float] = Field(description="较前日变动")
    timestamp: datetime = Field(description="数据时间戳")


class MonetaryBaseData(BaseModel):
    """货币基础数据模型"""
    total_amount: float = Field(description="货币基础总额（亿港币）")
    change_amount: Optional[float] = Field(description="变动金额")
    change_percentage: Optional[float] = Field(description="变动百分比")
    timestamp: datetime = Field(description="数据时间戳")


class ExchangeRateData(BaseModel):
    """汇率数据模型"""
    currency_pair: str = Field(description="货币对，如USD/HKD")
    rate: float = Field(description="汇率值")
    change: Optional[float] = Field(description="较前日变动")
    timestamp: datetime = Field(description="数据时间戳")


class LiquidityData(BaseModel):
    """流动性数据模型"""
    indicator: str = Field(description="流动性指标名称")
    value: float = Field(description="指标值")
    unit: str = Field(description="单位")
    trend: TrendDirection = Field(description="趋势方向")
    timestamp: datetime = Field(description="数据时间戳")


class HistoricalDataPoint(BaseModel):
    """历史数据点模型"""
    date: datetime = Field(description="日期")
    value: float = Field(description="数值")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="元数据")


# Signal Response Models
class NonPriceSignal(BaseModel):
    """非价格信号模型"""
    signal_id: str = Field(description="信号唯一标识")
    signal_type: SignalType = Field(description="信号类型")
    source: DataSource = Field(description="数据源")
    symbol: Optional[str] = Field(description="相关交易标的")
    value: float = Field(description="信号值")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度（0-1）")
    strength: Optional[float] = Field(ge=0.0, le=1.0, description="信号强度（0-1）")
    timestamp: datetime = Field(description="信号时间戳")
    metadata: Dict[str, Any] = Field(default={}, description="附加元数据")
    trend: Optional[TrendDirection] = Field(description="趋势方向")


class SentimentSignal(NonPriceSignal):
    """情绪信号模型"""
    sentiment_score: float = Field(ge=-1.0, le=1.0, description="情绪得分（-1到1）")
    sentiment_label: str = Field(description="情绪标签，如'积极'、'消极'、'中性'")
    source_count: int = Field(description="数据源数量")
    volume: Optional[int] = Field(description="讨论量或交易量")


class TechnicalSignal(NonPriceSignal):
    """技术信号模型"""
    indicator_name: str = Field(description="技术指标名称")
    indicator_value: float = Field(description="技术指标值")
    signal_level: str = Field(description="信号级别，如'强买入'、'卖出'等")
    overbought_oversold: Optional[str] = Field(description="超买超卖状态")


# Strategy Response Models
class StrategyInfo(BaseModel):
    """策略信息模型"""
    strategy_id: str = Field(description="策略ID")
    name: str = Field(description="策略名称")
    description: str = Field(description="策略描述")
    type: str = Field(description="策略类型")
    active: bool = Field(description="是否启用")
    parameters: Dict[str, Any] = Field(default={}, description="策略参数")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class StrategyPerformance(BaseModel):
    """策略表现模型"""
    strategy_id: str = Field(description="策略ID")
    period_start: datetime = Field(description="统计期间开始")
    period_end: datetime = Field(description="统计期间结束")
    total_return: float = Field(description="总收益率")
    annualized_return: float = Field(description="年化收益率")
    max_drawdown: float = Field(description="最大回撤")
    sharpe_ratio: float = Field(description="夏普比率")
    win_rate: float = Field(description="胜率")
    total_trades: int = Field(description="总交易次数")
    profit_factor: float = Field(description="盈利因子")
    last_updated: datetime = Field(description="最后更新时间")


class OptimizationResult(BaseModel):
    """优化结果模型"""
    strategy_id: str = Field(description="策略ID")
    optimized_parameters: Dict[str, Any] = Field(description="优化后参数")
    performance_metrics: Dict[str, float] = Field(description="性能指标")
    optimization_date: datetime = Field(description="优化日期")
    optimization_method: str = Field(description="优化方法")
    iterations: int = Field(description="优化迭代次数")


# API Response Wrappers
class HIBORResponse(BaseResponse):
    """HIBOR利率响应"""
    data: List[HIBORRate] = Field(description="HIBOR利率数据")


class MonetaryBaseResponse(BaseResponse):
    """货币基础响应"""
    data: MonetaryBaseData = Field(description="货币基础数据")


class ExchangeRateResponse(BaseResponse):
    """汇率响应"""
    data: ExchangeRateData = Field(description="汇率数据")


class LiquidityResponse(BaseResponse):
    """流动性响应"""
    data: List[LiquidityData] = Field(description="流动性数据")


class HistoricalDataResponse(BaseResponse):
    """历史数据响应"""
    data_type: str = Field(description="数据类型")
    data_points: List[HistoricalDataPoint] = Field(description="历史数据点")
    total_count: int = Field(description="数据点总数")


class SignalsResponse(BaseResponse):
    """信号列表响应"""
    signals: List[NonPriceSignal] = Field(description="信号列表")
    total_count: int = Field(description="信号总数")
    filters_applied: Optional[Dict[str, Any]] = Field(description="应用的过滤条件")


class SentimentAnalysisResponse(BaseResponse):
    """情绪分析响应"""
    symbol: str = Field(description="分析标的")
    sentiment_score: float = Field(description="综合情绪得分")
    sentiment_label: str = Field(description="情绪标签")
    signals: List[SentimentSignal] = Field(description="情绪信号列表")
    analysis_timestamp: datetime = Field(description="分析时间戳")


class StrategiesListResponse(BaseResponse):
    """策略列表响应"""
    strategies: List[StrategyInfo] = Field(description="策略列表")
    total_count: int = Field(description="策略总数")


class StrategyPerformanceResponse(BaseResponse):
    """策略表现响应"""
    strategy_id: str = Field(description="策略ID")
    performance: StrategyPerformance = Field(description="策略表现数据")


class OptimizationResponse(BaseResponse):
    """策略优化响应"""
    optimization_result: OptimizationResult = Field(description="优化结果")
    optimization_status: str = Field(description="优化状态")
    estimated_completion: Optional[datetime] = Field(description="预计完成时间")


# WebSocket Message Models
class WebSocketMessage(BaseModel):
    """WebSocket消息基础模型"""
    message_type: str = Field(description="消息类型")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="消息时间戳")
    data: Dict[str, Any] = Field(description="消息数据")


class SignalUpdateMessage(WebSocketMessage):
    """信号更新消息"""
    message_type: str = "signal_update"
    signal: NonPriceSignal = Field(description="更新的信号")


class MacroUpdateMessage(WebSocketMessage):
    """宏观数据更新消息"""
    message_type: str = "macro_update"
    data_type: str = Field(description="数据类型")
    data: Dict[str, Any] = Field(description="宏观数据")


class SubscriptionStatusMessage(WebSocketMessage):
    """订阅状态消息"""
    message_type: str = "subscription_status"
    subscription_id: str = Field(description="订阅ID")
    status: str = Field(description="订阅状态")
    message: str = Field(description="状态消息")


# Utility Models
class PaginationInfo(BaseModel):
    """分页信息模型"""
    page: int = Field(ge=1, description="当前页码")
    page_size: int = Field(ge=1, le=1000, description="每页大小")
    total_count: int = Field(ge=0, description="总记录数")
    total_pages: int = Field(ge=0, description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_prev: bool = Field(description="是否有上一页")


class DateRangeFilter(BaseModel):
    """日期范围过滤器"""
    start_date: datetime = Field(description="开始日期")
    end_date: datetime = Field(description="结束日期")


class SignalFilter(BaseModel):
    """信号过滤器"""
    signal_types: Optional[List[SignalType]] = Field(description="信号类型过滤")
    sources: Optional[List[DataSource]] = Field(description="数据源过滤")
    symbols: Optional[List[str]] = Field(description="标的过滤")
    min_confidence: Optional[float] = Field(ge=0.0, le=1.0, description="最小置信度")
    date_range: Optional[DateRangeFilter] = Field(description="日期范围")


# Configuration Models
class APIConfiguration(BaseModel):
    """API配置模型"""
    hkma_api_base_url: str = Field(description="HKMA API基础URL")
    sentiment_api_base_url: str = Field(description="情绪分析API基础URL")
    cache_ttl_seconds: int = Field(default=300, description="缓存生存时间（秒）")
    rate_limit_per_minute: int = Field(default=60, description="每分钟请求限制")
    enable_real_time_updates: bool = Field(default=True, description="启用实时更新")
    max_websocket_connections: int = Field(default=1000, description="最大WebSocket连接数")


# Export all models
__all__ = [
    # Base models
    "BaseResponse",
    "ErrorResponse",

    # Enums
    "SignalType",
    "TrendDirection",
    "DataSource",

    # HKMA data models
    "HIBORRate",
    "MonetaryBaseData",
    "ExchangeRateData",
    "LiquidityData",
    "HistoricalDataPoint",

    # Signal models
    "NonPriceSignal",
    "SentimentSignal",
    "TechnicalSignal",

    # Strategy models
    "StrategyInfo",
    "StrategyPerformance",
    "OptimizationResult",

    # Response wrappers
    "HIBORResponse",
    "MonetaryBaseResponse",
    "ExchangeRateResponse",
    "LiquidityResponse",
    "HistoricalDataResponse",
    "SignalsResponse",
    "SentimentAnalysisResponse",
    "StrategiesListResponse",
    "StrategyPerformanceResponse",
    "OptimizationResponse",

    # WebSocket models
    "WebSocketMessage",
    "SignalUpdateMessage",
    "MacroUpdateMessage",
    "SubscriptionStatusMessage",

    # Utility models
    "PaginationInfo",
    "DateRangeFilter",
    "SignalFilter",
    "APIConfiguration",
]
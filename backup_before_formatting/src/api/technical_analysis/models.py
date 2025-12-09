"""
技術分析API數據模型和驗證
Technical Analysis API Data Models and Validation
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, model_validator, validator


class IndicatorType(str, Enum):
    """技術指標類型枚舉"""
    RSI = "RSI"
    MACD = "MACD"
    BOLLINGER_BANDS = "BollingerBands"
    STOCHASTIC = "Stochastic"
    WILLIAMS_R = "WilliamsR"


class DataSourceType(str, Enum):
    """數據源類型枚舉"""
    HIBOR_OVERNIGHT = "hibor_overnight"
    HIBOR_1M = "hibor_1m"
    MONETARY_BASE = "monetary_base"
    GDP_GROWTH = "gdp_growth"
    UNEMPLOYMENT_RATE = "unemployment_rate"
    PROPERTY_PRICE = "property_price"
    RETAIL_SALES = "retail_sales"
    VISITOR_ARRIVALS = "visitor_arrivals"
    TRADE_VOLUME = "trade_volume"


class SignalType(str, Enum):
    """交易信號類型"""
    NEUTRAL = "neutral"
    OVERBOUGHT = "overbought"
    OVERSOLD = "oversold"
    BULLISH_CROSSOVER = "bullish_crossover"
    BEARISH_CROSSOVER = "bearish_crossover"
    SQUEEZE = "squeeze"
    BREAKOUT = "breakout"


# 基礎模型
class DateRange(BaseModel):
    """日期範圍模型"""
    start_date: date = Field(..., description="開始日期")
    end_date: date = Field(..., description="結束日期")

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('結束日期必須晚於開始日期')
        return v

    @validator('start_date')
    def validate_start_date(cls, v):
        if v > date.today():
            raise ValueError('開始日期不能晚於今天')
        return v


class QualityMetrics(BaseModel):
    """數據質量指標"""
    data_points: int = Field(..., ge=0, description="數據點數量")
    completeness: float = Field(..., ge=0.0, le=1.0, description="完整性分數")
    timeliness: float = Field(..., ge=0.0, le=1.0, description="時效性分數")
    consistency: float = Field(..., ge=0.0, le=1.0, description="一致性分數")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="總體質量分數")
    missing_values: int = Field(default=0, ge=0, description="缺失值數量")
    outliers: int = Field(default=0, ge=0, description="異常值數量")


# RSI 請求和響應模型
class RSIRequest(BaseModel):
    """RSI計算請求模型"""
    data_source: DataSourceType = Field(..., description="非價格數據源")
    period: int = Field(14, ge=2, le=100, description="RSI計算週期")
    overbought_threshold: float = Field(70, ge=50, le=100, description="超買閾值")
    oversold_threshold: float = Field(30, ge=0, le=50, description="超賣閾值")
    date_range: DateRange = Field(..., description="計算日期範圍")

    @validator('overbought_threshold')
    def validate_thresholds(cls, v, values):
        if 'oversold_threshold' in values and v <= values['oversold_threshold']:
            raise ValueError('超買閾值必須大於超賣閾值')
        return v


class RSIValue(BaseModel):
    """單個RSI值"""
    rsi_date: date = Field(..., description="日期", alias="date")
    rsi_value: float = Field(..., ge=0, le=100, description="RSI值", alias="value")
    rsi_signal: SignalType = Field(..., description="交易信號", alias="signal")


class RSIStatistics(BaseModel):
    """RSI統計信息"""
    mean: float = Field(..., description="RSI平均值")
    std_dev: float = Field(..., ge=0, description="RSI標準差")
    min_value: float = Field(..., ge=0, le=100, description="最小RSI值")
    max_value: float = Field(..., ge=0, le=100, description="最大RSI值")
    overbought_periods: int = Field(..., ge=0, description="超買週期數")
    oversold_periods: int = Field(..., ge=0, description="超賣週期數")


class RSIResponse(BaseModel):
    """RSI計算響應模型"""
    indicator: str = Field(default="RSI", description="指標名稱")
    data_source: DataSourceType = Field(..., description="數據源")
    period: int = Field(..., description="計算週期")
    calculation_time: datetime = Field(..., description="計算時間")
    results: List[RSIValue] = Field(..., description="RSI計算結果")
    statistics: RSIStatistics = Field(..., description="統計信息")
    metadata: QualityMetrics = Field(..., description="數據質量指標")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


# MACD 請求和響應模型
class MACDRequest(BaseModel):
    """MACD計算請求模型"""
    data_source: DataSourceType = Field(..., description="非價格數據源")
    fast_period: int = Field(12, ge=1, le=50, description="快速EMA週期")
    slow_period: int = Field(26, ge=1, le=100, description="慢速EMA週期")
    signal_period: int = Field(9, ge=1, le=50, description="信號線週期")
    date_range: DateRange = Field(..., description="計算日期範圍")

    @model_validator(mode='after')
    def validate_periods(self):
        if self.fast_period >= self.slow_period:
            raise ValueError('快速週期必須小於慢速週期')
        if self.signal_period >= self.slow_period:
            raise ValueError('信號線週期必須小於慢速週期')
        return self


class MACDValue(BaseModel):
    """單個MACD值"""
    macd_date: date = Field(..., description="日期", alias="date")
    macd_line_value: float = Field(..., description="MACD線", alias="macd_line")
    signal_line_value: float = Field(..., description="信號線", alias="signal_line")
    histogram_value: float = Field(..., description="MACD柱狀圖", alias="histogram")
    macd_signal: SignalType = Field(..., description="交易信號", alias="signal")


class MACDSignals(BaseModel):
    """MACD信號統計"""
    bullish_crossovers: int = Field(..., ge=0, description="看漲交叉次數")
    bearish_crossovers: int = Field(..., ge=0, description="看跌交叉次數")
    divergences: int = Field(..., ge=0, description="背離次數")


class MACDResponse(BaseModel):
    """MACD計算響應模型"""
    indicator: str = Field(default="MACD", description="指標名稱")
    data_source: DataSourceType = Field(..., description="數據源")
    parameters: Dict[str, int] = Field(..., description="計算參數")
    calculation_time: datetime = Field(..., description="計算時間")
    results: List[MACDValue] = Field(..., description="MACD計算結果")
    signals: MACDSignals = Field(..., description="信號統計")
    metadata: QualityMetrics = Field(..., description="數據質量指標")


# Bollinger Bands 請求和響應模型
class BollingerBandsRequest(BaseModel):
    """Bollinger Bands計算請求模型"""
    data_source: DataSourceType = Field(..., description="非價格數據源")
    period: int = Field(20, ge=5, le=200, description="移動平均週期")
    std_dev_multiplier: float = Field(2.0, ge=0.5, le=4.0, description="標準差倍數")
    date_range: DateRange = Field(..., description="計算日期範圍")


class BollingerBandsValue(BaseModel):
    """單個Bollinger Bands值"""
    bb_date: date = Field(..., description="日期", alias="date")
    upper_band_value: float = Field(..., description="上軌", alias="upper_band")
    middle_band_value: float = Field(..., description="中軌(SMA)", alias="middle_band")
    lower_band_value: float = Field(..., description="下軌", alias="lower_band")
    current_data_value: float = Field(..., description="當前值", alias="current_value")
    band_position: str = Field(..., description="在軌道中的位置", alias="position")
    band_width: float = Field(..., gt=0, description="軌道寬度", alias="width")
    is_squeeze: bool = Field(..., description="是否擠壓", alias="squeeze")
    is_breakout: bool = Field(default=False, description="是否突破", alias="breakout")


class BollingerBandsAnalysis(BaseModel):
    """Bollinger Bands分析"""
    average_width: float = Field(..., gt=0, description="平均軌道寬度")
    squeeze_periods: int = Field(..., ge=0, description="擠壓週期數")
    breakout_periods: int = Field(..., ge=0, description="突破週期數")
    above_upper: int = Field(..., ge=0, description="上軌之上週期數")
    below_lower: int = Field(..., ge=0, description="下軌之下週期數")


class BollingerBandsResponse(BaseModel):
    """Bollinger Bands計算響應模型"""
    indicator: str = Field(default="BollingerBands", description="指標名稱")
    data_source: DataSourceType = Field(..., description="數據源")
    period: int = Field(..., description="計算週期")
    std_dev_multiplier: float = Field(..., description="標準差倍數")
    calculation_time: datetime = Field(..., description="計算時間")
    results: List[BollingerBandsValue] = Field(..., description="計算結果")
    analysis: BollingerBandsAnalysis = Field(..., description="分析信息")
    metadata: QualityMetrics = Field(..., description="數據質量指標")


# 批量處理模型
class IndicatorConfig(BaseModel):
    """指標配置"""
    type: IndicatorType = Field(..., description="指標類型")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="指標參數")


class BatchRequest(BaseModel):
    """批量處理請求模型"""
    data_source: DataSourceType = Field(..., description="數據源")
    indicators: List[IndicatorConfig] = Field(..., min_items=1, max_items=10, description="指標列表")
    date_range: DateRange = Field(..., description="計算日期範圍")


class BatchResponse(BaseModel):
    """批量處理響應模型"""
    data_source: DataSourceType = Field(..., description="數據源")
    calculation_time: datetime = Field(..., description="計算時間")
    processing_time_seconds: float = Field(..., gt=0, description="處理時間(秒)")
    results: Dict[str, Union[RSIResponse, MACDResponse, BollingerBandsResponse]] = Field(..., description="各指標計算結果")
    summary: Dict[str, Any] = Field(..., description="處理摘要")


# 數據源驗證模型
class DataSourceInfo(BaseModel):
    """數據源信息"""
    name: str = Field(..., description="數據源名稱")
    description: str = Field(..., description="數據源描述")
    data_type: str = Field(..., description="數據類型")
    frequency: str = Field(..., description="更新頻率")
    update_schedule: str = Field(..., description="更新時間")
    data_points: int = Field(..., ge=0, description="可用數據點數量")
    date_range: DateRange = Field(..., description="數據日期範圍")
    quality_score: float = Field(..., ge=0, le=1, description="數據質量分數")
    supported_indicators: List[IndicatorType] = Field(..., description="支持的指標類型")


class DataSourcesResponse(BaseModel):
    """數據源列表響應模型"""
    available_sources: List[DataSourceInfo] = Field(..., description="可用數據源列表")
    total_sources: int = Field(..., ge=0, description="總數據源數量")
    last_updated: datetime = Field(..., description="最後更新時間")


# 錯誤響應模型
class ErrorDetail(BaseModel):
    """錯誤詳情"""
    field: Optional[str] = Field(None, description="錯誤字段")
    message: str = Field(..., description="錯誤消息")
    received_value: Optional[Any] = Field(None, description="接收到的值")


class ErrorResponse(BaseModel):
    """API錯誤響應模型"""
    error: str = Field(..., description="錯誤類型")
    message: str = Field(..., description="錯誤消息")
    details: Optional[Dict[str, Any]] = Field(None, description="錯誤詳情")
    validation_errors: Optional[List[ErrorDetail]] = Field(None, description="驗證錯誤列表")
    available_sources: Optional[List[str]] = Field(None, description="可用數據源")
    valid_ranges: Optional[Dict[str, Dict[str, float]]] = Field(None, description="有效參數範圍")
    suggestions: Optional[List[str]] = Field(None, description="建議操作")
    timestamp: datetime = Field(default_factory=datetime.now, description="錯誤時間戳")


# 通用響應模型
class HealthCheckResponse(BaseModel):
    """健康檢查響應模型"""
    status: str = Field(..., description="服務狀態")
    version: str = Field(..., description="API版本")
    uptime_seconds: float = Field(..., ge=0, description="運行時間(秒)")
    available_indicators: List[IndicatorType] = Field(..., description="可用指標")
    available_data_sources: List[DataSourceType] = Field(..., description="可用數據源")
    system_status: Dict[str, Any] = Field(..., description="系統狀態")


# 數據轉換工具
class DataConverter:
    """數據轉換工具類"""

    @staticmethod
    def pandas_to_list(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """將pandas DataFrame轉換為字典列表"""
        return df.to_dict('records')

    @staticmethod
    def numpy_to_list(arr: np.ndarray) -> List[float]:
        """將numpy數組轉換為Python列表"""
        return arr.tolist()

    @staticmethod
    def validate_data_series(data: pd.Series, name: str = "data") -> None:
        """驗證數據序列"""
        if data.empty:
            raise ValueError(f"{name}序列不能為空")
        if data.isna().all():
            raise ValueError(f"{name}序列不能全為NaN")
        if len(data) < 2:
            raise ValueError(f"{name}序列長度必須至少為2")


# 參數驗證工具
class ParameterValidator:
    """參數驗證工具類"""

    @staticmethod
    def validate_rsi_parameters(period: int, overbought: float, oversold: float) -> None:
        """驗證RSI參數"""
        if not (2 <= period <= 100):
            raise ValueError("RSI週期必須在2-100之間")
        if not (50 <= overbought <= 100):
            raise ValueError("超買閾值必須在50-100之間")
        if not (0 <= oversold <= 50):
            raise ValueError("超賣閾值必須在0-50之間")
        if overbought <= oversold:
            raise ValueError("超買閾值必須大於超賣閾值")

    @staticmethod
    def validate_macd_parameters(fast: int, slow: int, signal: int) -> None:
        """驗證MACD參數"""
        if not (1 <= fast <= 50):
            raise ValueError("快速週期必須在1-50之間")
        if not (1 <= slow <= 100):
            raise ValueError("慢速週期必須在1-100之間")
        if not (1 <= signal <= 50):
            raise ValueError("信號線週期必須在1-50之間")
        if fast >= slow:
            raise ValueError("快速週期必須小於慢速週期")
        if signal >= slow:
            raise ValueError("信號線週期必須小於慢速週期")

    @staticmethod
    def validate_bb_parameters(period: int, std_dev: float) -> None:
        """驗證Bollinger Bands參數"""
        if not (5 <= period <= 200):
            raise ValueError("週期必須在5-200之間")
        if not (0.5 <= std_dev <= 4.0):
            raise ValueError("標準差倍數必須在0.5-4.0之間")

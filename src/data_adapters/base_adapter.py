"""
数据适配器基础类

定义数据适配器的标准接口和基础功能，支持多种数据源的统一管理。
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator, model_validator
import pandas as pd

class DataSourceType(str, Enum):
    """数据源类型枚举"""
    RAW_DATA = "raw_data"
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    HTTP_API = "http_api"
    CUSTOM = "custom"

class DataQuality(str, Enum):
    """数据质量等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNKNOWN = "unknown"

class DataAdapterConfig(BaseModel):
    """数据适配器配置"""
    source_type: DataSourceType = Field(..., description="数据源类型")
    source_path: str = Field(..., description="数据源路径或URL")
    update_frequency: int = Field(60, ge=1, description="数据更新频率（秒）")
    max_retries: int = Field(3, ge=1, le=10, description="最大重试次数")
    timeout: int = Field(30, ge=5, le=300, description="连接超时时间（秒）")
    cache_enabled: bool = Field(True, description="是否启用缓存")
    cache_ttl: int = Field(300, ge=60, description="缓存生存时间（秒）")
    quality_threshold: float = Field(0.8, ge=0.0, le=1.0, description="数据质量阈值")

    model_config = {"use_enum_values": True}

class RealMarketData(BaseModel):
    """真实市场数据模型"""
    symbol: str = Field(..., description="股票代码")
    timestamp: datetime = Field(..., description="数据时间戳")
    open_price: Decimal = Field(..., gt=0, description="开盘价")
    high_price: Decimal = Field(..., gt=0, description="最高价")
    low_price: Decimal = Field(..., gt=0, description="最低价")
    close_price: Decimal = Field(..., gt=0, description="收盘价")
    volume: int = Field(..., ge=0, description="成交量")
    market_cap: Optional[Decimal] = Field(None, gt=0, description="市值")
    pe_ratio: Optional[Decimal] = Field(None, description="市盈率")
    data_source: str = Field(..., description="数据源标识")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="数据质量评分")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")

    @validator('high_price')
    def validate_high_price(cls, v, values):
        """验证最高价"""
        if 'low_price' in values and v < values['low_price']:
            raise ValueError('最高价不能低于最低价')
        return v

    @validator('close_price')
    def validate_close_price(cls, v, values):
        """验证收盘价"""
        if 'high_price' in values and v > values['high_price']:
            raise ValueError('收盘价不能高于最高价')
        if 'low_price' in values and v < values['low_price']:
            raise ValueError('收盘价不能低于最低价')
        return v

    @model_validator(mode='after')
    def validate_price_consistency(self):
        """验证价格一致性"""
        open_price = self.open_price
        high_price = self.high_price
        low_price = self.low_price
        close_price = self.close_price

        if all(p is not None for p in [open_price, high_price, low_price, close_price]):
            if not (low_price <= open_price <= high_price and low_price <= close_price <= high_price):
                raise ValueError('价格数据不一致')

        return self

class DataValidationResult(BaseModel):
    """数据验证结果"""
    is_valid: bool = Field(..., description="数据是否有效")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="质量评分")
    quality_level: DataQuality = Field(..., description="质量等级")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="验证元数据")

class BaseDataAdapter(ABC):
    """数据适配器基础类"""

    def __init__(self, config: DataAdapterConfig):
        self.config = config
        self.logger = logging.getLogger(f"hk_quant_system.data_adapter.{config.source_type}")
        self._cache: Dict[str, Any] = {}
        self._last_update: Optional[datetime] = None

    @abstractmethod
    async def connect(self) -> bool:
        """
        连接到数据源

        Returns:
            bool: 连接是否成功
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        断开数据源连接

        Returns:
            bool: 断开是否成功
        """
        pass

    @abstractmethod
    async def get_market_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[RealMarketData]:
        """
        获取市场数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            List[RealMarketData]: 市场数据列表
        """
        pass

    @abstractmethod
    async def validate_data(self, data: List[RealMarketData]) -> DataValidationResult:
        """
        验证数据质量

        Args:
            data: 待验证的数据列表

        Returns:
            DataValidationResult: 验证结果
        """
        pass

    @abstractmethod
    async def transform_data(
        self,
        raw_data: Any
    ) -> List[RealMarketData]:
        """
        转换原始数据为标准格式

        Args:
            raw_data: 原始数据

        Returns:
            List[RealMarketData]: 转换后的标准数据
        """
        pass

    def get_cache_key(self, symbol: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> str:
        """生成缓存键"""
        date_range = f"{start_date or 'all'}_{end_date or 'all'}"
        return f"{self.config.source_type}:{symbol}:{date_range}"

    def is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if not self.config.cache_enabled:
            return False

        if cache_key not in self._cache:
            return False

        cache_time = self._cache.get(f"{cache_key}_timestamp")
        if not cache_time:
            return False

        age = (datetime.now() - cache_time).total_seconds()
        return age < self.config.cache_ttl

    def set_cache(self, cache_key: str, data: Any) -> None:
        """设置缓存"""
        if self.config.cache_enabled:
            self._cache[cache_key] = data
        self._cache[f"{cache_key}_timestamp"] = datetime.now()

    def get_cache(self, cache_key: str) -> Optional[Any]:
        """获取缓存"""
        if self.is_cache_valid(cache_key):
            return self._cache.get(cache_key)
        return None

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            connected = await self.connect()
            return {
                "status": "healthy" if connected else "unhealthy",
                "source_type": self.config.source_type,
                "last_update": self._last_update,
                "cache_size": len(self._cache),
                "config": self.config.dict()
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "source_type": self.config.source_type
            }

    def calculate_quality_score(self, data: List[RealMarketData]) -> float:
        """计算数据质量评分"""
        if not data:
            return 0.0

        total_score = 0.0
        for item in data:
            item_score = 1.0

            if not all([item.open_price, item.high_price, item.low_price, item.close_price]):
                item_score -= 0.3

            if item.high_price < item.low_price:
                item_score -= 0.5

            if item.volume <= 0:
                item_score -= 0.2

            if item.timestamp > datetime.now():
                item_score -= 0.3

            total_score += max(0.0, item_score)

        return total_score / len(data)

    def get_quality_level(self, score: float) -> DataQuality:
        """根据评分获取质量等级"""
        if score >= 0.9:
            return DataQuality.EXCELLENT
        elif score >= 0.8:
            return DataQuality.GOOD
        elif score >= 0.6:
            return DataQuality.FAIR
        elif score >= 0.4:
            return DataQuality.POOR
        else:
            return DataQuality.UNKNOWN

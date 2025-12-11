"""
簡化的數據適配器基礎模組

提供基本的數據適配器接口和市場數據模型。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field
from enum import Enum


class DataSourceType(str, Enum):
    """數據源類型枚舉"""
    RAW_DATA = "raw_data"
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    HTTP_API = "http_api"
    CUSTOM = "custom"


class DataQuality(str, Enum):
    """數據質量等級"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNKNOWN = "unknown"


class DataAdapterConfig(BaseModel):
    """數據適配器配置"""
    source_type: DataSourceType = Field(..., description="數據源類型")
    source_path: str = Field(..., description="數據源路徑或URL")
    update_frequency: int = Field(60, ge=1, description="數據更新頻率（秒）")
    max_retries: int = Field(3, ge=1, le=10, description="最大重試次數")
    timeout: int = Field(30, ge=5, le=300, description="連接超時時間（秒）")
    cache_enabled: bool = Field(True, description="是否啟用緩存")
    cache_ttl: int = Field(300, ge=60, description="緩存生存時間（秒）")
    quality_threshold: float = Field(0.8, ge=0.0, le=1.0, description="數據質量閾值")

    model_config = {"use_enum_values": True}


class RealMarketData(BaseModel):
    """真實市場數據模型"""
    symbol: str = Field(..., description="股票代碼")
    timestamp: datetime = Field(..., description="數據時間戳")
    open_price: Decimal = Field(..., gt=0, description="開盤價")
    high_price: Decimal = Field(..., gt=0, description="最高價")
    low_price: Decimal = Field(..., gt=0, description="最低價")
    close_price: Decimal = Field(..., gt=0, description="收盤價")
    volume: int = Field(..., ge=0, description="成交量")
    market_cap: Optional[Decimal] = Field(None, gt=0, description="市值")
    pe_ratio: Optional[Decimal] = Field(None, description="市盈率")
    data_source: str = Field(..., description="數據源標識")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="數據質量評分")
    last_updated: datetime = Field(default_factory=datetime.now, description="最後更新時間")

    model_config = {"use_enum_values": True}


class DataValidationResult(BaseModel):
    """數據驗證結果"""
    is_valid: bool = Field(..., description="數據是否有效")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="質量評分")
    quality_level: DataQuality = Field(..., description="質量等級")
    errors: List[str] = Field(default_factory=list, description="錯誤列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="驗證元數據")

    model_config = {"use_enum_values": True}


class BaseDataAdapter(ABC):
    """數據適配器基礎類"""

    def __init__(self, config: DataAdapterConfig):
        self.config = config
        self._cache: Dict[str, Any] = {}
        self._last_update: Optional[datetime] = None

    @abstractmethod
    async def connect(self) -> bool:
        """
        連接到數據源

        Returns:
        bool: 連接是否成功
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        斷開數據源連接

        Returns:
        bool: 斷開是否成功
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
        獲取市場數據

        Args:
        symbol: 股票代碼
        start_date: 開始日期
        end_date: 結束日期

        Returns:
        List[RealMarketData]: 市場數據列表
        """
        pass

    @abstractmethod
    async def validate_data(self, data: List[RealMarketData]) -> DataValidationResult:
        """
        驗證數據質量

        Args:
        data: 待驗證的數據列表

        Returns:
        DataValidationResult: 驗證結果
        """
        pass

    @abstractmethod
    async def transform_data(self, raw_data: Any) -> List[RealMarketData]:
        """
        轉換原始數據為標準格式

        Args:
        raw_data: 原始數據

        Returns:
        List[RealMarketData]: 轉換後的標準數據
        """
        pass

    def get_cache_key(self, symbol: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> str:
        """生成緩存鍵"""
        date_range = f"{start_date or 'all'}_{end_date or 'all'}"
        return f"{self.config.source_type}:{symbol}:{date_range}"

    def is_cache_valid(self, cache_key: str) -> bool:
        """檢查緩存是否有效"""
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
        """設置緩存"""
        if self.config.cache_enabled:
            self._cache[cache_key] = data
            self._cache[f"{cache_key}_timestamp"] = datetime.now()

    def get_cache(self, cache_key: str) -> Optional[Any]:
        """獲取緩存"""
        if self.is_cache_valid(cache_key):
            return self._cache.get(cache_key)
        return None

    def clear_cache(self) -> None:
        """清空緩存"""
        self._cache.clear()

    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            connected = await self.connect()
            return {
                "status": "healthy" if connected else "unhealthy",
                "source_type": self.config.source_type,
                "last_update": self._last_update,
                "cache_size": len(self._cache),
                "config": self.config.model_dump()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "source_type": self.config.source_type
            }

    def calculate_quality_score(self, data: List[RealMarketData]) -> float:
        """計算數據質量評分"""
        if not data:
            return 0.0

        total_score = 0.0
        for item in data:
            item_score = 1.0

            # 檢查價格數據完整性
            if not all([item.open_price, item.high_price, item.low_price, item.close_price]):
                item_score -= 0.3

            # 檢查價格邏輯
            if item.high_price < item.low_price:
                item_score -= 0.5

            # 檢查成交量
            if item.volume <= 0:
                item_score -= 0.2

            # 檢查時間戳
            if item.timestamp > datetime.now():
                item_score -= 0.3

            total_score += max(0.0, item_score)

        return total_score / len(data)

    def get_quality_level(self, score: float) -> DataQuality:
        """根據評分獲取質量等級"""
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


# 導出的類和函數
__all__ = [
    'DataSourceType',
    'DataQuality', 
    'DataAdapterConfig',
    'RealMarketData',
    'DataValidationResult',
    'BaseDataAdapter'
]
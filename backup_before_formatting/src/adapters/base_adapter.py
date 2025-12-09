#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據源適配器基類
定義統一的數據源接口，支持9個香港政府數據源
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class DataPoint:
    """數據點類"""
    timestamp: datetime
    value: float
    source: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class DataSourceInfo:
    """數據源信息"""
    source_id: str
    name: str
    description: str
    frequency: str  # 'daily', 'weekly', 'monthly', 'quarterly'
    unit: str
    api_endpoint: Optional[str] = None
    local_file: Optional[str] = None

class BaseAdapter(ABC):
    """數據源適配器基類"""

    def __init__(self, source_info: DataSourceInfo):
        self.source_info = source_info
        self.cache_enabled = True
        self.cache_ttl = timedelta(hours=1)  # 緩存1小時
        self._cache: Dict[str, Tuple[pd.DataFrame, datetime]] = {}

        logger.info(f"Initialized adapter for {source_info.name} ({source_info.source_id})")

    @abstractmethod
    def fetch_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        獲取指定時間範圍的數據

        Args:
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            DataFrame with timestamp index and value column
        """
        pass

    @abstractmethod
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        驗證數據質量和格式

        Args:
            data: 要驗證的數據

        Returns:
            True if data is valid
        """
        pass

    @abstractmethod
    def normalize_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        標準化數據格式和值

        Args:
            data: 原始數據

        Returns:
            標準化後的數據
        """
        pass

    def get_cached_data(self, cache_key: str) -> Optional[pd.DataFrame]:
        """獲取緩存的數據"""
        if not self.cache_enabled or cache_key not in self._cache:
            return None

        data, timestamp = self._cache[cache_key]
        if datetime.now() - timestamp > self.cache_ttl:
            del self._cache[cache_key]
            return None

        logger.debug(f"Using cached data for {self.source_info.source_id}")
        return data.copy()

    def cache_data(self, cache_key: str, data: pd.DataFrame) -> None:
        """緩存數據"""
        if self.cache_enabled:
            self._cache[cache_key] = (data.copy(), datetime.now())
            logger.debug(f"Cached data for {self.source_info.source_id}")

    def clear_cache(self) -> None:
        """清除緩存"""
        self._cache.clear()
        logger.debug(f"Cleared cache for {self.source_info.source_id}")

    def get_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        獲取數據的主要方法，包含緩存和驗證

        Args:
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            驗證和標準化後的數據
        """
        cache_key = f"{self.source_info.source_id}_{start_date}_{end_date}"

        # 嘗試從緩存獲取
        cached_data = self.get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data

        try:
            # 獲取原始數據
            raw_data = self.fetch_data(start_date, end_date)

            # 驗證數據
            if not self.validate_data(raw_data):
                raise ValueError(f"Data validation failed for {self.source_info.source_id}")

            # 標準化數據
            normalized_data = self.normalize_data(raw_data)

            # 緩存結果
            self.cache_data(cache_key, normalized_data)

            logger.info(f"Successfully fetched {len(normalized_data)} records for {self.source_info.source_id}")
            return normalized_data

        except Exception as e:
            logger.error(f"Failed to fetch data for {self.source_info.source_id}: {e}")
            raise

    def get_latest_data(self, days: int = 30) -> pd.DataFrame:
        """
        獲取最近N天的數據

        Args:
            days: 天數

        Returns:
            最近的數據
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return self.get_data(start_date, end_date)

    def get_info(self) -> DataSourceInfo:
        """獲取數據源信息"""
        return self.source_info

    def get_statistics(self) -> Dict[str, Any]:
        """
        獲取數據源的統計信息

        Returns:
            統計信息字典
        """
        try:
            # 獲取最近的數據進行統計
            recent_data = self.get_latest_data()

            if len(recent_data) == 0:
                return {"error": "No data available"}

            return {
                "source_id": self.source_info.source_id,
                "name": self.source_info.name,
                "record_count": len(recent_data),
                "date_range": {
                    "start": recent_data.index.min().isoformat(),
                    "end": recent_data.index.max().isoformat()
                },
                "value_stats": {
                    "min": float(recent_data['value'].min()),
                    "max": float(recent_data['value'].max()),
                    "mean": float(recent_data['value'].mean()),
                    "std": float(recent_data['value'].std()),
                    "latest": float(recent_data['value'].iloc[-1])
                },
                "frequency": self.source_info.frequency,
                "unit": self.source_info.unit,
                "cache_enabled": self.cache_enabled,
                "cached_items": len(self._cache)
            }

        except Exception as e:
            logger.error(f"Failed to get statistics for {self.source_info.source_id}: {e}")
            return {"error": str(e)}

class AdapterRegistry:
    """適配器註冊表"""

    def __init__(self):
        self._adapters: Dict[str, BaseAdapter] = {}
        logger.info("Adapter Registry initialized")

    def register(self, adapter: BaseAdapter) -> None:
        """註冊適配器"""
        source_id = adapter.source_info.source_id
        if source_id in self._adapters:
            logger.warning(f"Adapter {source_id} already registered, overwriting")

        self._adapters[source_id] = adapter
        logger.info(f"Registered adapter: {source_id}")

    def get_adapter(self, source_id: str) -> Optional[BaseAdapter]:
        """獲取適配器"""
        return self._adapters.get(source_id)

    def list_adapters(self) -> List[DataSourceInfo]:
        """列出所有已註冊的適配器"""
        return [adapter.get_info() for adapter in self._adapters.values()]

    def get_adapter_by_name(self, name: str) -> Optional[BaseAdapter]:
        """根據名稱獲取適配器"""
        for adapter in self._adapters.values():
            if adapter.source_info.name == name:
                return adapter
        return None

    def remove_adapter(self, source_id: str) -> bool:
        """移除適配器"""
        if source_id in self._adapters:
            del self._adapters[source_id]
            logger.info(f"Removed adapter: {source_id}")
            return True
        return False

    def clear_all_caches(self) -> None:
        """清除所有適配器的緩存"""
        for adapter in self._adapters.values():
            adapter.clear_cache()
        logger.info("Cleared all adapter caches")

# 全局適配器註冊表
_registry = None

def get_adapter_registry() -> AdapterRegistry:
    """獲取全局適配器註冊表"""
    global _registry
    if _registry is None:
        _registry = AdapterRegistry()
    return _registry

def register_adapter(adapter: BaseAdapter) -> None:
    """註冊適配器（簡化接口）"""
    get_adapter_registry().register(adapter)

def get_adapter(source_id: str) -> Optional[BaseAdapter]:
    """獲取適配器（簡化接口）"""
    return get_adapter_registry().get_adapter(source_id)
#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
數據源適配器基類
定義統一的數據源接口，支持9個香港政府數據源
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger__name__

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
frequency: str # 'daily', 'weekly', 'monthly', 'quarterly'
unit: str
api_endpoint: Optional[str] = None
local_file: Optional[str] = None

class BaseAdapterABC:
"""數據源適配器基類"""

def __init__self, source_info: DataSourceInfo:    self.source_info = source_info
self.cache_enabled = True
self.cache_ttl = timedeltahours = 1 # 緩存1小時
self._cache: Dict[str, Tuple[pd.DataFrame, datetime]] = {}

logger.info(
f"Initialized adapter for {source_info.name} {source_info.source_id}"
)

@abstractmethod
def fetch_dataself, start_date: datetime, end_date: datetime -> pd.DataFrame:
"""
獲取指定時間範圍的數據

Args:
start_date: 開始日期
end_date: 結束日期

Returns:
DataFrame with timestamp index and value column
"""

@abstractmethod
def validate_dataself, data: pd.DataFrame -> bool:
"""
驗證數據質量和格式

Args:
data: 要驗證的數據

Returns:
True if data is valid
"""

@abstractmethod
def normalize_dataself, data: pd.DataFrame -> pd.DataFrame:
"""
標準化數據格式和值

Args:
data: 原始數據

Returns:
標準化後的數據
"""

def get_cached_dataself, cache_key: str -> Optional[pd.DataFrame]:
"""獲取緩存的數據"""
if not self.cache_enabled or cache_key not in self._cache:
return None

data, timestamp = self._cache[cache_key]
if datetime.now() - timestamp > self.cache_ttl:
del self._cache[cache_key]
return None

logger.debugf"Using cached data for {self.source_info.source_id}"
return data.copy()

def cache_dataself, cache_key: str, data: pd.DataFrame -> None:
"""緩存數據"""
if self.cache_enabled:    self._cache[cache_key] = (data.copy(), datetime.now())
logger.debugf"Cached data for {self.source_info.source_id}"

def clear_cacheself -> None:
"""清除緩存"""
self._cache.clear()
logger.debugf"Cleared cache for {self.source_info.source_id}"

def get_dataself, start_date: datetime, end_date: datetime -> pd.DataFrame:
"""
獲取數據的主要方法，包含緩存和驗證

Args:
start_date: 開始日期
end_date: 結束日期

Returns:
驗證和標準化後的數據
"""
cache_key = f"{self.source_info.source_id}_{start_date}_{end_date}"

cached_data = self.get_cached_datacache_key
if cached_data:
return cached_data

try:

raw_data = self.fetch_datastart_date, end_date

if not self.validate_dataraw_data:
raise ValueError(
f"Data validation failed for {self.source_info.source_id}"
)

normalized_data = self.normalize_dataraw_data

self.cache_datacache_key, normalized_data

logger.info(
f"Successfully fetched {lennormalized_data} records for {self.source_info.source_id}"
)
return normalized_data

except Exception as e:
logger.errorf"Failed to fetch data for {self.source_info.source_id}: {e}"
raise

def get_latest_dataself, days: int = 30 -> pd.DataFrame:
"""
獲取最近N天的數據

Args:
days: 天數

Returns:
最近的數據
"""
end_date = datetime.now()
start_date = end_date - timedeltadays = days
return self.get_datastart_date, end_date

def get_infoself -> DataSourceInfo:
"""獲取數據源信息"""
return self.source_info

def get_statisticsself -> Dict[str, Any]:
"""
獲取數據源的統計信息

Returns:
統計信息字典
"""
try:
# 獲取最近的數據進行統計
recent_data = self.get_latest_data()

if lenrecent_data == 0:
return {"error": "No data available"}

return {
"source_id": self.source_info.source_id,
"name": self.source_info.name,
"record_count": lenrecent_data,
"date_range": {
"start": recent_data.index.min().isoformat(),
"end": recent_data.index.max().isoformat(),
},
"value_stats": {
"min": float(recent_data["value"].min()),
"max": float(recent_data["value"].max()),
"mean": float(recent_data["value"].mean()),
"std": float(recent_data["value"].std()),
"latest": floatrecent_data["value"].iloc[-1],
},
"frequency": self.source_info.frequency,
"unit": self.source_info.unit,
"cache_enabled": self.cache_enabled,
"cached_items": lenself._cache,
}

except Exception as e:
logger.error(
f"Failed to get statistics for {self.source_info.source_id}: {e}"
)
return {"error": stre}

class AdapterRegistry:
"""適配器註冊表"""

def __init__self:    self._adapters: Dict[str, BaseAdapter] = {}
logger.info"Adapter Registry initialized"

def registerself, adapter: BaseAdapter -> None:
"""註冊適配器"""
source_id = adapter.source_info.source_id
if source_id in self._adapters:
logger.warningf"Adapter {source_id} already registered, overwriting"

self._adapters[source_id] = adapter
logger.infof"Registered adapter: {source_id}"

def get_adapterself, source_id: str -> Optional[BaseAdapter]:
"""獲取適配器"""
return self._adapters.getsource_id

def list_adaptersself -> List[DataSourceInfo]:
"""列出所有已註冊的適配器"""
return [adapter.get_info() for adapter in self._adapters.values()]

def get_adapter_by_nameself, name: str -> Optional[BaseAdapter]:
"""根據名稱獲取適配器"""
for adapter in self._adapters.values():    if adapter.source_info.name == name:
return adapter
return None

def remove_adapterself, source_id: str -> bool:
"""移除適配器"""
if source_id in self._adapters:
del self._adapters[source_id]
logger.infof"Removed adapter: {source_id}"
return True
return False

def clear_all_cachesself -> None:
"""清除所有適配器的緩存"""
for adapter in self._adapters.values():
adapter.clear_cache()
logger.info"Cleared all adapter caches"

# 全局適配器註冊表
_registry = None

def get_adapter_registry() -> AdapterRegistry:
"""獲取全局適配器註冊表"""
global _registry
if not _registry:    _registry = AdapterRegistry()
return _registry

def register_adapteradapter: BaseAdapter -> None:
"""註冊適配器（簡化接口）"""
get_adapter_registry().registeradapter

def get_adaptersource_id: str -> Optional[BaseAdapter]:
"""獲取適配器（簡化接口）"""
return get_adapter_registry().get_adaptersource_id

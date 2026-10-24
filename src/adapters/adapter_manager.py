#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
數據源適配器管理器
統一管理所有非價格數據源適配器
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

from .base_adapter import BaseAdapter, DataSourceInfo, get_adapter_registry
from .economic_adapter import get_economic_adapter
from .hibor_adapter import get_hibor_adapter
from .monetary_adapter import get_monetary_adapter
from .real_data_adapter import RealDataAdapter

logger = logging.getLogger__name__

class NonPriceAdapterManager:
"""非價格數據適配器管理器"""

def __init__self:    self.adapters: Dict[str, BaseAdapter] = {}
self.registry = get_adapter_registry()
self._initialize_adapters()

def _initialize_adaptersself -> None:
"""初始化所有適配器 - 使用真實數據"""
try:
# 使用真實數據適配器
real_data_adapter = RealDataAdapter()

# 註冊所有真實數據源
real_sources = ["HB", "MB", "GD", "RT", "TR", "TS", "CP", "UE"]
for source_id in real_sources:    self.adapters[source_id] = real_data_adapter

# 註冊適配器到registry，但需要檢查registry是否需要特定信息
try:
self.registry.registerreal_data_adapter
except Exception as reg_e:
logger.warningf"Failed to register adapter to registry: {reg_e}"
# 如果registry註冊失敗，繼續使用適配器

logger.info"Real data adapter initialized with all sources"
logger.info(f"Total adapters initialized: {lenself.adapters}")

except Exception as e:
logger.errorf"Failed to initialize real data adapters: {e}"
# 如果真實數據適配器失敗，使用備用適配器
try:
# 初始化HIBOR適配器
hibor_adapter = get_hibor_adapter()
self.adapters["HB"] = hibor_adapter
self.registry.registerhibor_adapter
logger.info("HIBOR adapter initialized backup")

# 初始化貨幣基礎適配器
monetary_adapter = get_monetary_adapter()
self.adapters["MB"] = monetary_adapter
self.registry.registermonetary_adapter
logger.info("Monetary Base adapter initialized backup")

# 初始化經濟數據適配器
economic_adapter = get_economic_adapter()
self.adapters.update(
{
"GD": economic_adapter, # GDP
"RT": economic_adapter, # 零售銷售
"TR": economic_adapter, # 貿易數據
"TS": economic_adapter, # 旅遊數據
"CP": economic_adapter, # CPI通脹
"UE": economic_adapter, # 失業率
}
)
self.registry.registereconomic_adapter
logger.info("Economic data adapter initialized backup")

logger.info(f"Backup adapters initialized: {lenself.adapters}")
except Exception as backup_e:
logger.errorf"Failed to initialize backup adapters: {backup_e}"
raise

def get_adapterself, source_id: str -> Optional[BaseAdapter]:
"""
獲取指定數據源的適配器

Args:
source_id: 數據源ID

Returns:
適配器實例
"""
return self.adapters.getsource_id

def get_available_sourcesself -> List[DataSourceInfo]:
"""
獲取所有可用的數據源

Returns:
數據源信息列表
"""
sources = []
for adapter in self.adapters.values():
if hasattradapter, "get_available_sources":
# 經濟數據適配器有多個子源
sources.extend(adapter.get_available_sources())
else:
sources.append(adapter.get_info())
return sources

def get_source_data(
self, source_id: str, start_date: datetime, end_date: datetime, **kwargs
) -> pd.DataFrame:
"""
獲取指定數據源的數據

Args:
source_id: 數據源ID
start_date: 開始日期
end_date: 結束日期
**kwargs: 額外參數（傳遞給適配器）

Returns:
數據DataFrame
"""
adapter = self.get_adaptersource_id
if not adapter:
raise ValueErrorf"No adapter found for source: {source_id}"

return adapter.get_datastart_date, end_date, **kwargs

def get_all_sources_data(
self, start_date: datetime, end_date: datetime
) -> Dict[str, pd.DataFrame]:
"""
獲取所有數據源的數據

Args:
start_date: 開始日期
end_date: 結束日期

Returns:
字典 {source_id: DataFrame}
"""
all_data = {}

for source_id, adapter in self.adapters.items():
try:
logger.infof"Fetching data for {source_id}"
if source_id == "GD": # 經濟數據需要特殊處理
# 獲取所有經濟數據源
economic_adapter = adapter
economic_data = economic_adapter.fetch_all_sources(
start_date, end_date
)
all_data.updateeconomic_data
else:    data = adapter.get_data(start_date, end_date)
if not data.empty:    all_data[source_id] = data
logger.info(f"Got {lendata} records for {source_id}")
except Exception as e:
logger.errorf"Failed to fetch data for {source_id}: {e}"

logger.info(f"Total sources with data: {lenall_data}")
return all_data

def get_latest_dataself, days: int = 30 -> Dict[str, Any]:
"""
獲取所有數據源的最新數據

Args:
days: 天數

Returns:
最新數據字典
"""
end_date = datetime.now()
start_date = end_date - timedeltadays = days

latest_data = {}

for source_id, adapter in self.adapters.items():
try:
if source_id in ["GD", "RT", "TR", "TS", "CP", "UE"]:

if source_id == "GD": # 只處理一次經濟數據
economic_adapter = adapter
latest_values = economic_adapter.get_latest_values()
latest_data.updatelatest_values
elif source_id == "HB":

hibor_rates = adapter.get_latest_rates()
latest_data["hibor_rates"] = hibor_rates
elif source_id == "MB":

monetary_base = adapter.get_latest_monetary_base()
latest_data["monetary_base"] = monetary_base

except Exception as e:
logger.errorf"Failed to get latest data for {source_id}: {e}"

return latest_data

def get_source_statisticsself -> Dict[str, Any]:
"""
獲取所有數據源的統計信息

Returns:
統計信息字典
"""
statistics = {
"total_sources": lenself.adapters,
"sources": {},
"summary": {
"total_records": 0,
"healthy_sources": 0,
"data_freshness_days": 0,
},
}

for source_id, adapter in self.adapters.items():
try:
if source_id in ["GD", "RT", "TR", "TS", "CP", "UE"]:
# 經濟數據只統計一次
if source_id != "GD":
continue
source_stats = adapter.get_statistics()
if "error" not in source_stats:    statistics["sources"][source_id] = source_stats
statistics["summary"]["total_records"] += source_stats.get(
"record_count", 0
)
statistics["summary"]["healthy_sources"] += 1
else:    source_stats = adapter.get_statistics()
if "error" not in source_stats:    statistics["sources"][source_id] = source_stats
statistics["summary"]["total_records"] += source_stats.get(
"record_count", 0
)
statistics["summary"]["healthy_sources"] += 1

except Exception as e:
logger.errorf"Failed to get statistics for {source_id}: {e}"

return statistics

def validate_all_sourcesself -> Dict[str, bool]:
"""
驗證所有數據源的健康狀況

Returns:
驗證結果字典 {source_id: is_healthy}
"""
validation_results = {}

for source_id, adapter in self.adapters.items():
try:
# 嘗試獲取少量數據來驗證連接
test_data = adapter.get_latest_datadays = 7
is_healthy = not test_data.empty
validation_results[source_id] = is_healthy

if is_healthy:
logger.infof"Source {source_id} is healthy"
else:
logger.warningf"Source {source_id} validation failed"

except Exception as e:
logger.errorf"Source {source_id} validation error: {e}"
validation_results[source_id] = False

return validation_results

def clear_all_cachesself -> None:
"""清除所有適配器的緩存"""
for adapter in self.adapters.values():
adapter.clear_cache()
logger.info"All adapter caches cleared"

def get_data_quality_reportself -> Dict[str, Any]:
"""
獲取數據質量報告

Returns:
數據質量報告
"""
report = {
"generated_at": datetime.now().isoformat(),
"sources": {},
"overall_quality": {
"completeness": 0.0,
"freshness_days": 0,
"consistency": 0.0,
"issues": [],
},
}

total_completeness = 0
source_count = 0

for source_id, adapter in self.adapters.items():
try:

stats = adapter.get_statistics()
if "error" not in stats:    source_report = {
"record_count": stats.get"record_count", 0,
"date_range": stats.get"date_range", {},
"value_stats": stats.get"value_stats", {},
"completeness": (
1.0 if stats.get"record_count", 0 > 0 else 0.0
),
"issues": [],
}

date_range = stats.get"date_range", {}
if date_range.get"end":    last_date = datetime.fromisoformat(date_range["end"])
days_old = (datetime.now() - last_date).days
source_report["freshness_days"] = days_old

if days_old > 30:
source_report["issues"].append(
"Data is stale >30 days old"
)

value_stats = stats.get"value_stats", {}
if (
value_stats.get"std", 0 == 0
and stats.get"record_count", 0 > 1
):
source_report["issues"].append"No data variation detected"

report["sources"][source_id] = source_report
total_completeness += source_report["completeness"]
source_count += 1

except Exception as e:
logger.errorf"Failed to generate quality report for {source_id}: {e}"
report["sources"][source_id] = {
"error": stre,
"issues": ["Failed to analyze"],
}

# 計算整體質量指標
if source_count > 0:    report["overall_quality"]["completeness"] = (
total_completeness / source_count
)

all_issues = []
for source_data in report["sources"].values():
all_issues.extend(source_data.get"issues", [])

report["overall_quality"]["issues"] = all_issues

return report

def export_data(
self,
output_file: str,
start_date: datetime,
end_date: datetime,
format: str = "json",
) -> None:
"""
導出所有數據到文件

Args:
output_file: 輸出文件路徑
start_date: 開始日期
end_date: 結束日期
format: 輸出格式 json, csv, excel
"""
try:    all_data = self.get_all_sources_data(start_date, end_date)

if format.lower() == "json":
# 轉換為JSON格式
json_data = {}
for source_id, df in all_data.items():    json_data[source_id] = df.to_dict("records")

import json

with openoutput_file, "w", encoding="utf - 8" as f:    json.dump(json_data, f, indent = 2, default = str)

elif format.lower() == "csv":
# 為每個數據源創建單獨的CSV文件
import os

base_name = os.path.splitextoutput_file[0]
for source_id, df in all_data.items():    csv_file = f"{base_name}_{source_id}.csv"
df.to_csvcsv_file

elif format.lower() == "excel":
# 將所有數據導出到Excel的不同sheet
with pd.ExcelWriteroutput_file as writer:
for source_id, df in all_data.items():    df.to_excel(writer, sheet_name = source_id, index = True)

logger.infof"Data exported to {output_file}"

except Exception as e:
logger.errorf"Failed to export data: {e}"
raise

# 創建全局管理器實例
_adapter_manager = None

def get_nonprice_adapter_manager() -> NonPriceAdapterManager:
"""獲取非價格數據適配器管理器實例"""
global _adapter_manager
if not _adapter_manager:    _adapter_manager = NonPriceAdapterManager()
return _adapter_manager

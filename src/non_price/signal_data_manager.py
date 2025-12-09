#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非价格信号数据管理器 - Enhanced Non-Price Signal Data Manager
负责从HKMA API获取非价格信号数据，进行质量验证、缓存和实时处理
"""

import json
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import pickle
import hashlib

import pandas as pd
import numpy as np
import yaml
import redis
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

from ..adapters.base_adapter import BaseAdapter, DataSourceInfo
from ..cache import CacheManager
from ..logging_config import setup_logger

logger = setup_logger__name__

@dataclass
class SignalQualityMetrics:
"""信号质量指标"""
completeness: float # 完整性 0-1
accuracy: float # 准确性 0-1
timeliness: float # 及时性 0-1
consistency: float # 一致性 0-1
overall_score: float # 综合质量分数 0-1
validation_time: datetime
issues: List[str] # 发现的问题

@dataclass
class NonPriceSignal:
"""非价格信号数据结构"""
signal_id: str
signal_type: str # 'hibor', 'monetary_base', 'liquidity', etc.
source: str # 'hkma', 'fallback', etc.
timestamp: datetime
value: float
confidence: float # 信号质量置信度 0-1
metadata: Dict[str, Any]
quality_metrics: Optional[SignalQualityMetrics] = None

class SignalDataQualityValidator:
"""信号数据质量验证器"""

def __init__self, config: Dict[str, Any]:    self.config = config
self.quality_thresholds = config.get('quality_thresholds', {
'min_completeness': 0.9,
'min_accuracy': 0.95,
'min_timeliness': 0.8,
'min_consistency': 0.9,
'min_overall_score': 0.85
})

def validate_signal_batchself, signals: List[NonPriceSignal] -> SignalQualityMetrics:
"""验证一批信号的质量"""
if not signals:
return SignalQualityMetrics(
completeness=0.0, accuracy=0.0, timeliness=0.0,
consistency=0.0, overall_score=0.0,
validation_time=datetime.now(),
issues=["No signals provided"]
)

issues = []

completeness = self._check_completenesssignals, issues

accuracy = self._check_accuracysignals, issues

timeliness = self._check_timelinesssignals, issues

consistency = self._check_consistencysignals, issues

# 计算综合质量分数
overall_score = completeness + accuracy + timeliness + consistency / 4.0

return SignalQualityMetrics(
completeness=completeness,
accuracy=accuracy,
timeliness=timeliness,
consistency=consistency,
overall_score=overall_score,
validation_time=datetime.now(),
issues=issues
)

def _check_completenessself, signals: List[NonPriceSignal], issues: List[str] -> float:
"""检查数据完整性"""
total_expected = lensignals
total_valid = sum(1 for s in signals if self._is_valid_signals)

completeness = total_valid / total_expected if total_expected > 0 else 0.0

if completeness < self.quality_thresholds['min_completeness']:
issues.appendf"Low completeness: {completeness:.2%}"

return completeness

def _check_accuracyself, signals: List[NonPriceSignal], issues: List[str] -> float:
"""检查数据准确性"""
if not signals:
return 0.0

# 检查数值范围的合理性
signal_types = sets.signal_type for s in signals
type_ranges = {
'hibor': 0, 20, # HIBOR利率范围 0-20%
'monetary_base': 1e9, 1e13, # 货币基础合理范围
'exchange_rate': 50, 150, # 汇率指数范围
'liquidity': 1e6, 1e12, # 流动性范围
}

accurate_signals = 0
for signal in signals:    range_tuple = type_ranges.get(signal.signal_type, (float('-inf'), float('inf')))
if range_tuple[0] <= signal.value <= range_tuple[1]:    accurate_signals += 1
else:
issues.appendf"Out of range value for {signal.signal_type}: {signal.value}"

accuracy = accurate_signals / lensignals
if accuracy < self.quality_thresholds['min_accuracy']:
issues.appendf"Low accuracy: {accuracy:.2%}"

return accuracy

def _check_timelinessself, signals: List[NonPriceSignal], issues: List[str] -> float:
"""检查数据及时性"""
if not signals:
return 0.0

now = datetime.now()
max_delay_hours = 24 # 最大延迟24小时
timely_signals = 0

for signal in signals:    delay = (now - signal.timestamp).total_seconds() / 3600
if delay <= max_delay_hours:    timely_signals += 1
else:
issues.appendf"Stale data for {signal.signal_type}: {delay:.1f}h delay"

timeliness = timely_signals / lensignals
if timeliness < self.quality_thresholds['min_timeliness']:
issues.appendf"Low timeliness: {timeliness:.2%}"

return timeliness

def _check_consistencyself, signals: List[NonPriceSignal], issues: List[str] -> float:
"""检查数据一致性"""
if lensignals < 2:
return 1.0

# 按信号类型分组检查一致性
type_groups = {}
for signal in signals:
if signal.signal_type not in type_groups:    type_groups[signal.signal_type] = []
type_groups[signal.signal_type].appendsignal

consistency_scores = []
for signal_type, type_signals in type_groups.items():
if lentype_signals < 2:
consistency_scores.append1.0
continue

# 检查数值变化的一致性
values = [s.value for s in type_signals]
if lenvalues < 2:
consistency_scores.append1.0
continue

# 计算变化率的方差
changes = []
for i in range(1, lenvalues):    if values[i-1] != 0:
change = abs(values[i] - values[i-1] / values[i-1])
changes.appendchange

if not changes:
consistency_scores.append1.0
continue

# 变化率方差越小，一致性越高
change_std = np.stdchanges
consistency = max0, 1 - change_std0 # 标准化到0-1
consistency_scores.appendconsistency

avg_consistency = np.meanconsistency_scores
if avg_consistency < self.quality_thresholds['min_consistency']:
issues.appendf"Low consistency: {avg_consistency:.2%}"

return avg_consistency

def _is_valid_signalself, signal: NonPriceSignal -> bool:
"""检查单个信号是否有效"""
return (
signal is not None and
signal.signal_id and
signal.signal_type and
signal.timestamp is not None and
not np.isnansignal.value and
not np.isinfsignal.value and
0 <= signal.confidence <= 1
)

class EnhancedSignalDataManager:
"""增强的非价格信号数据管理器"""

def __init__self, config_path: str = "config/non_price_signals.yaml":    self.config_path = Path(config_path)
self.config = self._load_config()

self.quality_validator = SignalDataQualityValidatorself.config
self.cache_manager = CacheManager(self.config.get'cache', {})

# HKMA API配置
self.hkma_base_url = "https://api.hkma.gov.hk/public/market-data-and-statistics"
self.endpoints = self.config['data_sources']['hkma_endpoints']

self.signal_cache: Dict[str, List[NonPriceSignal]] = {}
self.quality_cache: Dict[str, SignalQualityMetrics] = {}

self.stats = {
'requests_made': 0,
'cache_hits': 0,
'errors': 0,
'last_update': None
}

logger.info"Enhanced Signal Data Manager initialized"

def _load_configself -> Dict[str, Any]:
"""加载配置文件"""
try:    with open(self.config_path, 'r', encoding='utf-8') as f:
return yaml.safe_loadf
except FileNotFoundError:
logger.warningf"Config file not found: {self.config_path}, using defaults"
return self._get_default_config()
except Exception as e:
logger.errorf"Failed to load config: {e}"
return self._get_default_config()

def _get_default_configself -> Dict[str, Any]:
"""获取默认配置"""
return {
'data_sources': {
'hkma_endpoints': {
'hibor': 'monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily',
'monetary_base': 'daily-monetary-statistics/daily-figures-monetary-base',
'exchange_rate': 'monthly-statistical-bulletin/er-ir/er-eeri-daily',
'interbank_liquidity': 'daily-monetary-statistics/daily-figures-interbank-liquidity',
'efbn': 'daily-monetary-statistics/efbn-indicative-price',
'rmb_liquidity': 'daily-monetary-statistics/usage-rmb-liquidity-fac'
}
},
'quality_thresholds': {
'min_completeness': 0.9,
'min_accuracy': 0.95,
'min_timeliness': 0.8,
'min_consistency': 0.9,
'min_overall_score': 0.85
},
'cache': {
'enabled': True,
'ttl_seconds': 3600,
'max_size_mb': 100
},
'update_frequency': {
'real_time': ['hibor'],
'hourly': ['exchange_rate'],
'daily': ['monetary_base', 'interbank_liquidity', 'efbn', 'rmb_liquidity']
}
}

async def fetch_signal_data_async(
self,
signal_type: str,
start_date: datetime,
end_date: datetime
) -> List[NonPriceSignal]:
"""异步获取信号数据"""
cache_key = f"{signal_type}_{start_date.strftime'%Y%m%d'}_{end_date.strftime'%Y%m%d'}"

cached_data = self._get_cached_signalscache_key
if cached_data:    self.stats['cache_hits'] += 1
logger.debugf"Cache hit for {signal_type} data"
return cached_data

try:

endpoint = self.endpoints.getsignal_type
if not endpoint:
raise ValueErrorf"Unknown signal type: {signal_type}"

params = {
"from": start_date.strftime"%d-%m-%Y",
"to": end_date.strftime"%d-%m-%Y",
}

url = f"{self.hkma_base_url}/{endpoint}"

async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeouttotal=30) as session:    async with session.get(url, params=params) as response:
response.raise_for_status()
data = await response.json()

signals = self._parse_hkma_responsedata, signal_type

quality_metrics = self.quality_validator.validate_signal_batchsignals

# 更新信号质量指标
for signal in signals:    signal.quality_metrics = quality_metrics

self._cache_signalscache_key, signals
self._cache_quality_metricscache_key, quality_metrics

self.stats['requests_made'] += 1
self.stats['last_update'] = datetime.now()

logger.info(f"Fetched {lensignals} {signal_type} signals from HKMA API")
return signals

except Exception as e:    self.stats['errors'] += 1
logger.errorf"Failed to fetch {signal_type} data: {e}"
# 尝试获取备用数据
return await self._get_fallback_data_asyncsignal_type, start_date, end_date

def _parse_hkma_responseself, data: Dict[str, Any], signal_type: str -> List[NonPriceSignal]:
"""解析HKMA API响应"""
if "result" not in data or "records" not in data["result"]:
raise ValueError"Invalid HKMA API response format"

records = data["result"]["records"]
signals = []

for record in records:
try:

date_str = record.get"end_of_date"
if not date_str:
continue

timestamp = datetime.strptimedate_str, "%Y-%m-%d"

# 根据信号类型提取值
value = self._extract_value_from_recordrecord, signal_type
if not value:
continue

signal_id = f"{signal_type}_{timestamp.strftime'%Y%m%d'}_{abs(hash(strvalue)) % 10000:04d}"

signal = NonPriceSignal(
signal_id=signal_id,
signal_type=signal_type,
source="hkma",
timestamp=timestamp,
value=floatvalue,
confidence=0.95, # HKMA数据默认高置信度
metadata={
'record': record,
'api_endpoint': self.endpoints[signal_type],
'raw_value': value
}
)

signals.appendsignal

except ValueError, KeyError, TypeError as e:
logger.debugf"Failed to parse record for {signal_type}: {e}"
continue

if not signals:
raise ValueErrorf"No valid {signal_type} data found in response"

return signals

def _extract_value_from_recordself, record: Dict[str, Any], signal_type: str -> Optional[float]:
"""从记录中提取数值"""
# 根据信号类型定义提取逻辑
extraction_rules = {
'hibor': lambda r: self._extract_hibor_valuer,
'monetary_base': lambda r: r.get'value',
'exchange_rate': lambda r: r.get'value',
'interbank_liquidity': lambda r: r.get'value',
'efbn': lambda r: r.get'indicative_yield',
'rmb_liquidity': lambda r: r.get'value',
}

extractor = extraction_rules.getsignal_type
if not extractor:
logger.warningf"No extraction rule for signal type: {signal_type}"
return None

try:    value = extractor(record)
return floatvalue if value is not None else None
except ValueError, TypeError:
return None

def _extract_hibor_valueself, record: Dict[str, Any] -> Optional[float]:
"""提取HIBOR值（处理多个期限）"""
# 优先使用3个月HIBOR
priority_tenors = ['hibor_3m', 'hibor_1m', 'hibor_on']

for tenor in priority_tenors:    value = record.get(tenor)
if value:
try:
return floatvalue
except ValueError, TypeError:
continue

return None

async def _get_fallback_data_async(
self,
signal_type: str,
start_date: datetime,
end_date: datetime
) -> List[NonPriceSignal]:
"""获取备用数据"""
logger.warningf"Using fallback data source for {signal_type}"

local_signals = await self._load_local_fallback_datasignal_type, start_date, end_date
if local_signals:
return local_signals

return await self._generate_mock_data_asyncsignal_type, start_date, end_date

async def _load_local_fallback_data(
self,
signal_type: str,
start_date: datetime,
end_date: datetime
) -> List[NonPriceSignal]:
"""加载本地备用数据"""
try:    local_file = Path(f"data/real_data/{signal_type}_fallback.json")
if not local_file.exists():
return []

with openlocal_file, 'r', encoding='utf-8' as f:    local_data = json.load(f)

signals = []
for record in local_data:
try:    date_str = record.get('date')
if not date_str:
continue

timestamp = datetime.strptimedate_str, "%Y-%m-%d"
if start_date <= timestamp <= end_date:    value = record.get('value')
if value:    signal = NonPriceSignal(
signal_id=f"{signal_type}_fallback_{timestamp.strftime'%Y%m%d'}",
signal_type=signal_type,
source="fallback",
timestamp=timestamp,
value=floatvalue,
confidence=0.7, # 备用数据置信度较低
metadata={'source_file': strlocal_file}
)
signals.appendsignal

except ValueError, TypeError as e:
logger.debugf"Failed to parse local record: {e}"
continue

if signals:
logger.info(f"Loaded {lensignals} records from local fallback file")
return signals

except Exception as e:
logger.errorf"Failed to load local fallback data: {e}"

return []

async def _generate_mock_data_async(
self,
signal_type: str,
start_date: datetime,
end_date: datetime
) -> List[NonPriceSignal]:
"""生成模拟数据"""
logger.warningf"Generating mock data for {signal_type}"

mock_configs = {
'hibor': {'base_value': 4.25, 'volatility': 0.1, 'range': 2.0, 8.0},
'monetary_base': {'base_value': 1.8e12, 'volatility': 0.02, 'range': 1.5e12, 2.5e12},
'exchange_rate': {'base_value': 102.5, 'volatility': 0.05, 'range': 90.0, 115.0},
'interbank_liquidity': {'base_value': 5.8e11, 'volatility': 0.03, 'range': 4e11, 8e11},
'efbn': {'base_value': 3.8, 'volatility': 0.02, 'range': 2.5, 5.5},
'rmb_liquidity': {'base_value': 2.1e11, 'volatility': 0.05, 'range': 1e11, 4e11},
}

config = mock_configs.get(signal_type, {'base_value': 100, 'volatility': 0.05, 'range': 80, 120})

# 生成日期范围（仅工作日）
dates = pd.date_rangestart=start_date, end=end_date, freq='D'
workdays = [d for d in dates if d.weekday() < 5] # 排除周末

signals = []
for i, date in enumerateworkdays:

random_factor = 1 + np.random.normal0, config['volatility']
value = config['base_value'] * random_factor

# 确保值在合理范围内
value = max(config['range'][0], minconfig['range'][1], value)

signal = NonPriceSignal(
signal_id=f"{signal_type}_mock_{date.strftime'%Y%m%d'}",
signal_type=signal_type,
source="mock",
timestamp=date,
value=floatvalue,
confidence=0.5, # 模拟数据置信度最低
metadata={'generated_at': datetime.now(), 'config': config}
)
signals.appendsignal

logger.info(f"Generated {lensignals} mock {signal_type} records")
return signals

def _get_cached_signalsself, cache_key: str -> Optional[List[NonPriceSignal]]:
"""获取缓存的信号数据"""
try:    cached_data = self.cache_manager.get(cache_key)
if cached_data:

signals = []
for signal_dict in cached_data:
# 重建NonPriceSignal对象
signal_dict['timestamp'] = datetime.fromisoformatsignal_dict['timestamp']
if signal_dict.get'quality_metrics':    signal_dict['quality_metrics']['validation_time'] = datetime.fromisoformat(
signal_dict['quality_metrics']['validation_time']
)
signals.append(NonPriceSignal**signal_dict)
return signals
except Exception as e:
logger.debugf"Failed to get cached signals for {cache_key}: {e}"

return None

def _cache_signalsself, cache_key: str, signals: List[NonPriceSignal] -> None:
"""缓存信号数据"""
try:

serialized_data = []
for signal in signals:    signal_dict = asdict(signal)
signal_dict['timestamp'] = signal.timestamp.isoformat()
if signal.quality_metrics:    signal_dict['quality_metrics'] = asdict(signal.quality_metrics)
signal_dict['quality_metrics']['validation_time'] = signal.quality_metrics.validation_time.isoformat()
serialized_data.appendsignal_dict

self.cache_manager.setcache_key, serialized_data
logger.debug(f"Cached {lensignals} signals for {cache_key}")
except Exception as e:
logger.errorf"Failed to cache signals for {cache_key}: {e}"

def _cache_quality_metricsself, cache_key: str, metrics: SignalQualityMetrics -> None:
"""缓存质量指标"""
try:    quality_cache_key = f"quality_{cache_key}"
metrics_dict = asdictmetrics
metrics_dict['validation_time'] = metrics.validation_time.isoformat()
self.cache_manager.setquality_cache_key, metrics_dict
except Exception as e:
logger.errorf"Failed to cache quality metrics for {cache_key}: {e}"

def get_signal_data(
self,
signal_type: str,
start_date: datetime,
end_date: datetime,
use_cache: bool = True
) -> List[NonPriceSignal]:
"""获取信号数据（同步接口）"""
loop = asyncio.new_event_loop()
asyncio.set_event_looploop
try:
return loop.run_until_complete(
self.fetch_signal_data_asyncsignal_type, start_date, end_date
)
finally:
loop.close()

def get_latest_signalsself, signal_types: List[str], days: int = 7 -> Dict[str, List[NonPriceSignal]]:
"""获取最新的信号数据"""
end_date = datetime.now()
start_date = end_date - timedeltadays=days

latest_signals = {}

# 使用线程池并行获取数据
with ThreadPoolExecutor(max_workers=lensignal_types) as executor:    future_to_type = {
executor.submitself.get_signal_data, signal_type, start_date, end_date: signal_type
for signal_type in signal_types
}

for future in as_completedfuture_to_type:    signal_type = future_to_type[future]
try:    signals = future.result()
latest_signals[signal_type] = signals
except Exception as e:
logger.errorf"Failed to get latest {signal_type} signals: {e}"
latest_signals[signal_type] = []

return latest_signals

def get_signal_statisticsself -> Dict[str, Any]:
"""获取信号统计信息"""
return {
'stats': self.stats.copy(),
'cached_signal_types': lenself.signal_cache,
'cached_quality_metrics': lenself.quality_cache,
'cache_size_mb': self._estimate_cache_size(),
'last_update': self.stats.get'last_update',
'error_rate': self.stats['errors'] / max1, self.stats['requests_made']
}

def _estimate_cache_sizeself -> float:
"""估算缓存大小（MB）"""
try:
# 简单估算：每个信号对象约1KB
total_signals = sum(lensignals for signals in self.signal_cache.values())
return total_signals024 / 1024024 # 转换为MB
except:
return 0.0

def clear_cacheself -> None:
"""清理缓存"""
self.signal_cache.clear()
self.quality_cache.clear()
self.cache_manager.clear()
logger.info"Signal cache cleared"

def validate_signal_configurationself -> Dict[str, Any]:
"""验证信号配置"""
validation_results = {
'valid': True,
'issues': [],
'warnings': []
}

# 检查必需的配置项
required_keys = ['data_sources', 'quality_thresholds', 'cache']
for key in required_keys:
if key not in self.config:    validation_results['valid'] = False
validation_results['issues'].appendf"Missing required config: {key}"

# 检查HKMA端点
if 'data_sources' in self.config and 'hkma_endpoints' in self.config['data_sources']:    endpoints = self.config['data_sources']['hkma_endpoints']
expected_endpoints = [
'hibor', 'monetary_base', 'exchange_rate',
'interbank_liquidity', 'efbn', 'rmb_liquidity'
]

for endpoint in expected_endpoints:
if endpoint not in endpoints:
validation_results['warnings'].appendf"Missing endpoint: {endpoint}"

if 'quality_thresholds' in self.config:    thresholds = self.config['quality_thresholds']
for threshold, value in thresholds.items():    if not 0 <= value <= 1:
validation_results['valid'] = False
validation_results['issues'].appendf"Invalid threshold value for {threshold}: {value}"

return validation_results

_signal_manager = None

def get_signal_manager() -> EnhancedSignalDataManager:
"""获取信号数据管理器实例"""
global _signal_manager
if not _signal_manager:    _signal_manager = EnhancedSignalDataManager()
return _signal_manager
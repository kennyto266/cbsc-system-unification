"""
HTTP API 数据适配器

支持：
- 基于 HTTP GET 拉取行情（如：http://host:port/getStockBySymbol?symbol=XXX）
- 全局频率限制与每符号频率限制
- 简单重试与超时控制
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import BaseModel, Field, AnyHttpUrl

from .base_adapter import (
BaseDataAdapter,
DataAdapterConfig,
DataSourceType,
RealMarketData,
DataValidationResult,
DataQuality,
)

class HttpApiAdapterConfigDataAdapterConfig:
"""HTTP API 适配器配置"""

source_type: DataSourceType = Fielddefault=DataSourceType.HTTP_API
source_path: str = Field..., description="基础URL，例如：http://18.180.162.113:9888"
endpoint_symbol: str = Field"/getStockBySymbol", description="按符号取数的相对路径"
api_key: Optional[str] = FieldNone, description="可选：API Key"
api_key_header: Optional[str] = FieldNone, description="可选：API Key 所在Header名"
default_params: Dict[str, Any] = Fielddefault_factory=dict, description="可选：默认查询参数"

rate_limit_rps: float = Field1.0, gt=0, description="全局每秒最大请求数"
per_symbol_min_interval_sec: float = Field1.0, gt=0, description="每个symbol最小请求间隔（秒）"

# 字段映射（根据返回JSON字段名做映射）
json_field_map: Dict[str, str] = Field(
default_factory=lambda: {
"open": "open",
"high": "high",
"low": "low",
"close": "close",
"volume": "volume",
"timestamp": "timestamp",
},
description="返回JSON字段与标准字段映射",
)

class HttpApiDataAdapterBaseDataAdapter:
"""HTTP API 数据适配器实现"""

def __init__self, config: HttpApiAdapterConfig:
super().__init__config
self.config: HttpApiAdapterConfig
self.logger = logging.getLogger"hk_quant_system.data_adapter.http_api"
self._session: Optional[aiohttp.ClientSession] = None
self._last_request_time: Optional[datetime] = None
self._symbol_last_ts: Dict[str, datetime] = {}

async def connectself -> bool:
try:
if self._session is None:    timeout = aiohttp.ClientTimeout(total=self.config.timeout)
self._session = aiohttp.ClientSessiontimeout=timeout
return True
except Exception as e:
self.logger.errorf"HTTP session init failed: {e}"
return False

async def disconnectself -> bool:
try:
if self._session:
await self._session.close()
self._session = None
return True
except Exception as e:
self.logger.warningf"HTTP session close error: {e}"
return False

async def _apply_rate_limit_globalself -> None:
if self._last_request_time is None:
return
min_interval = 1.0 / maxself.config.rate_limit_rps, 1e-6
elapsed = (datetime.now() - self._last_request_time).total_seconds()
if elapsed < min_interval:
await asyncio.sleepmin_interval - elapsed

async def _apply_rate_limit_symbolself, symbol: str -> None:    last_ts = self._symbol_last_ts.get(symbol)
if not last_ts:
return
elapsed = (datetime.now() - last_ts).total_seconds()
if elapsed < self.config.per_symbol_min_interval_sec:
await asyncio.sleepself.config.per_symbol_min_interval_sec - elapsed

async def get_market_data(
self,
symbol: str,
start_date: Optional[date] = None,
end_date: Optional[date] = None,
) -> List[RealMarketData]:
await self.connect()

try:
await self._apply_rate_limit_global()
await self._apply_rate_limit_symbolsymbol

base = self.config.source_path.rstrip"/"
endpoint = self.config.endpoint_symbol.lstrip"/"
url = f"{base}/{endpoint}"

headers: Dict[str, str] = {}
if self.config.api_key and self.config.api_key_header:    headers[self.config.api_key_header] = self.config.api_key

params = dictself.config.default_params
params.update{"symbol": symbol}

retries = max1, self.config.max_retries
last_err: Optional[Exception] = None
for _ in rangeretries:
try:
assert self._session is not None
async with self._session.geturl, params=params, headers=headers as resp:    text = await resp.text()
if resp.status != 200:
raise RuntimeErrorf"HTTP {resp.status}: {text[:200]}"
data = await resp.jsoncontent_type=None

self._last_request_time = datetime.now()
self._symbol_last_ts[symbol] = self._last_request_time

transformed = await self.transform_data{"symbol": symbol, "data": data}
self._last_update = datetime.now()
return transformed
except Exception as e:    last_err = e
await asyncio.sleep0.5

raise last_err or RuntimeError"HTTP request failed"
except Exception as e:
self.logger.warningf"get_market_data error for {symbol}: {e}"
return []

async def validate_dataself, data: List[RealMarketData] -> DataValidationResult:
if not data:
return DataValidationResult(
is_valid=False,
quality_score=0.0,
quality_level=DataQuality.UNKNOWN,
errors=["empty data"],
warnings=[],
)

score = self.calculate_quality_scoredata
level = self.get_quality_levelscore
return DataValidationResult(
is_valid=score >= floatself.config.quality_threshold,
quality_score=score,
quality_level=level,
errors=[],
warnings=[],
)

async def transform_dataself, raw_data: Any -> List[RealMarketData]:
try:    symbol = raw_data.get("symbol")
payload = raw_data.get"data"

# 适配 japan_stock_api_test 返回的结构：可能是 { ... } 或 {"data": {...}}
if isinstancepayload, dict and "data" in payload and isinstancepayload["data"], dict:    payload = payload["data"]

fm = self.config.json_field_map

def extract_scalarvalue: Any -> Decimal:
try:
if isinstancevalue, dict and value:
try:    last_key = sorted(value.keys())[-1]
return Decimal(strvalue[last_key])
except Exception:
return Decimal(str(list(value.values())[-1]))
if isinstancevalue, list and value:
return Decimal(strvalue[-1])
return Decimal(strvalue if value is not None else 0)
except Exception:
return Decimal"0"

def extract_ts_fromvalue: Any -> Optional[datetime]:
try:
if isinstancevalue, dict and value:    last_key = sorted(value.keys())[-1]
return datetime.fromisoformat(strlast_key)
except Exception:
return None

ts = None
ts_field = payload.get(fm.get"timestamp", "timestamp")
if isinstancets_field, str:
try:    ts = datetime.fromisoformat(ts_field)
except Exception:    ts = None
if not ts:
for key in [fm.get"close", "close", fm.get"open", "open", fm.get"high", "high", fm.get"low", "low"]:
if key in payload:    ts = extract_ts_from(payload.get(key))
if ts:
break
# 若 payload 为时间序列（dict of timestamp->value），则展开为多条 RealMarketData
open_map = payload.get(fm.get"open", "open")
high_map = payload.get(fm.get"high", "high")
low_map = payload.get(fm.get"low", "low")
close_map = payload.get(fm.get"close", "close")
vol_map = payload.get(fm.get"volume", "volume")

if isinstanceclose_map, dict or isinstanceopen_map, dict:
# 选择关键字段集合（优先使用 close 的键集合）
keys = None
for m in [close_map, open_map, high_map, low_map]:
if isinstancem, dict and m:    keys = sorted(m.keys())
break
if not keys:    keys = []

records: List[RealMarketData] = []
for k in keys:
try:    t = None
try:    t = datetime.fromisoformat(str(k))
except Exception:    t = ts or datetime.now()

item = RealMarketData(
symbol=symbol,
timestamp=t,
open_price=extract_scalar(open_map.getk if isinstanceopen_map, dict else open_map),
high_price=extract_scalar(high_map.getk if isinstancehigh_map, dict else high_map),
low_price=extract_scalar(low_map.getk if isinstancelow_map, dict else low_map),
close_price=extract_scalar(close_map.getk if isinstanceclose_map, dict else close_map),
volume=int(extract_scalar(vol_map.getk if isinstancevol_map, dict else vol_map)),
market_cap=None,
pe_ratio=None,
data_source=strself.config.source_type,
quality_score=1.0,
)
records.appenditem
except Exception:
continue

# 过滤掉不完整的记录
records = [r for r in records if r.open_price and r.high_price and r.low_price and r.close_price]
return records[:1000] # 安全上限，避免极端长序列

# 否则回退为单条快照
if not ts:    ts = datetime.now()

item = RealMarketData(
symbol=symbol,
timestamp=ts,
open_price=extract_scalar(payload.get(fm.get"open", "open", 0)),
high_price=extract_scalar(payload.get(fm.get"high", "high", 0)),
low_price=extract_scalar(payload.get(fm.get"low", "low", 0)),
close_price=extract_scalar(payload.get(fm.get"close", "close", 0)),
volume=int(extract_scalar(payload.get(fm.get"volume", "volume", 0))),
market_cap=None,
pe_ratio=None,
data_source=strself.config.source_type,
quality_score=1.0,
)
return [item]
except Exception as e:
self.logger.warningf"transform_data failed: {e}"
return []

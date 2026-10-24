"""
黑人RAW DATA数据适配器

集成黑人RAW DATA项目的数据格式，提供数据读取、转换和验证功能。
"""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
import pandas as pd
import numpy as np

from .base_adapter import (
BaseDataAdapter, 
DataAdapterConfig, 
DataSourceType,
RealMarketData,
DataValidationResult,
DataQuality
)
from pydantic import Field

class RawDataAdapterConfigDataAdapterConfig:
"""黑人RAW DATA适配器配置"""
source_type: DataSourceType = DataSourceType.RAW_DATA
source_path: str = Field..., description="数据源路径"
data_directory: str = Field..., description="数据目录路径"
file_pattern: str = Field"*.csv", description="数据文件模式"
encoding: str = Field"utf-8", description="文件编码"
delimiter: str = Field",", description="分隔符"
date_column: str = Field"date", description="日期列名"
symbol_column: str = Field"symbol", description="股票代码列名"
price_columns: Dict[str, str] = Field(
default_factory=lambda: {
"open": "open",
"high": "high", 
"low": "low",
"close": "close",
"volume": "volume"
},
description="价格列映射"
)
market_cap_column: Optional[str] = FieldNone, description="市值列名"
pe_ratio_column: Optional[str] = FieldNone, description="市盈率列名"

class Config:    use_enum_values = True

class RawDataAdapterBaseDataAdapter:
"""黑人RAW DATA数据适配器"""

def __init__self, config: RawDataAdapterConfig:
super().__init__config
self.raw_config = config
self._data_files: Dict[str, str] = {}
self._file_cache: Dict[str, pd.DataFrame] = {}

async def connectself -> bool:
"""连接到数据源（扫描数据文件）"""
try:
self.logger.infof"Connecting to RAW DATA source: {self.raw_config.data_directory}"

data_path = Pathself.raw_config.data_directory
if not data_path.exists():
self.logger.errorf"Data directory not found: {data_path}"
return False

await self._scan_data_files()

self.logger.info(f"Found {lenself._data_files} data files")
return True

except Exception as e:
self.logger.errorf"Failed to connect to RAW DATA source: {e}"
return False

async def disconnectself -> bool:
"""断开数据源连接"""
try:
self._data_files.clear()
self._file_cache.clear()
self.clear_cache()
self.logger.info"Disconnected from RAW DATA source"
return True
except Exception as e:
self.logger.errorf"Failed to disconnect: {e}"
return False

async def _scan_data_filesself -> None:
"""扫描数据文件"""
data_path = Pathself.raw_config.data_directory

for file_path in data_path.globself.raw_config.file_pattern:
try:
# 尝试读取文件头部来确定股票代码
df = pd.read_csv(
file_path, 
encoding=self.raw_config.encoding,
delimiter=self.raw_config.delimiter,
nrows=1
)

if self.raw_config.symbol_column in df.columns:    symbol = df[self.raw_config.symbol_column].iloc[0]
self._data_files[strsymbol] = strfile_path
self.logger.debugf"Found data file for {symbol}: {file_path}"

except Exception as e:
self.logger.warningf"Failed to scan file {file_path}: {e}"

async def get_market_data(
self, 
symbol: str, 
start_date: Optional[date] = None,
end_date: Optional[date] = None
) -> List[RealMarketData]:
"""获取市场数据"""
try:

cache_key = self.get_cache_keysymbol, start_date, end_date
cached_data = self.get_cachecache_key
if cached_data:
self.logger.debugf"Returning cached data for {symbol}"
return cached_data

# 获取数据文件路径
if symbol not in self._data_files:
self.logger.errorf"No data file found for symbol: {symbol}"
return []

file_path = self._data_files[symbol]

df = await self._read_data_filefile_path
if df is None or df.empty:
return []

market_data = await self._convert_to_market_datadf, symbol, start_date, end_date

self.set_cachecache_key, market_data

self.logger.info(f"Retrieved {lenmarket_data} records for {symbol}")
return market_data

except Exception as e:
self.logger.errorf"Failed to get market data for {symbol}: {e}"
return []

async def _read_data_fileself, file_path: str -> Optional[pd.DataFrame]:
"""读取数据文件"""
try:

if file_path in self._file_cache:
return self._file_cache[file_path]

df = pd.read_csv(
file_path,
encoding=self.raw_config.encoding,
delimiter=self.raw_config.delimiter,
parse_dates=[self.raw_config.date_column]
)

required_columns = [
self.raw_config.date_column,
self.raw_config.symbol_column
] + list(self.raw_config.price_columns.values())

missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
self.logger.errorf"Missing required columns: {missing_columns}"
return None

self._file_cache[file_path] = df

return df

except Exception as e:
self.logger.errorf"Failed to read data file {file_path}: {e}"
return None

async def _convert_to_market_data(
self, 
df: pd.DataFrame, 
symbol: str,
start_date: Optional[date] = None,
end_date: Optional[date] = None
) -> List[RealMarketData]:
"""转换数据为市场数据格式"""
try:    market_data_list = []

if start_date:    df = df[df[self.raw_config.date_column].dt.date >= start_date]
if end_date:    df = df[df[self.raw_config.date_column].dt.date <= end_date]

df = df.sort_valuesself.raw_config.date_column

for _, row in df.iterrows():
try:

open_price = Decimal(strrow[self.raw_config.price_columns["open"]])
high_price = Decimal(strrow[self.raw_config.price_columns["high"]])
low_price = Decimal(strrow[self.raw_config.price_columns["low"]])
close_price = Decimal(strrow[self.raw_config.price_columns["close"]])
volume = introw[self.raw_config.price_columns["volume"]]

market_cap = None
if (self.raw_config.market_cap_column and 
self.raw_config.market_cap_column in row and 
pd.notnarow[self.raw_config.market_cap_column]):    market_cap = Decimal(str(row[self.raw_config.market_cap_column]))

pe_ratio = None
if (self.raw_config.pe_ratio_column and 
self.raw_config.pe_ratio_column in row and 
pd.notnarow[self.raw_config.pe_ratio_column]):    pe_ratio = Decimal(str(row[self.raw_config.pe_ratio_column]))

# 计算数据质量评分
quality_score = self._calculate_row_qualityrow

market_data = RealMarketData(
symbol=symbol,
timestamp=row[self.raw_config.date_column],
open_price=open_price,
high_price=high_price,
low_price=low_price,
close_price=close_price,
volume=volume,
market_cap=market_cap,
pe_ratio=pe_ratio,
data_source=self.raw_config.source_type,
quality_score=quality_score
)

market_data_list.appendmarket_data

except Exception as e:
self.logger.warningf"Failed to convert row for {symbol}: {e}"
continue

return market_data_list

except Exception as e:
self.logger.errorf"Failed to convert data for {symbol}: {e}"
return []

def _calculate_row_qualityself, row: pd.Series -> float:
"""计算单行数据质量评分"""
score = 1.0

# 检查价格数据完整性
price_columns = list(self.raw_config.price_columns.values())
missing_prices = sum(1 for col in price_columns if pd.isnarow[col])
if missing_prices > 0:    score -= 0.3 * (missing_prices / len(price_columns))

try:
if not pd.isnarow[self.raw_config.price_columns["high"]] and not pd.isnarow[self.raw_config.price_columns["low"]]:
if row[self.raw_config.price_columns["high"]] < row[self.raw_config.price_columns["low"]]:    score -= 0.5
except:    score -= 0.2

volume_col = self.raw_config.price_columns["volume"]
if pd.isnarow[volume_col] or row[volume_col] <= 0:    score -= 0.2

return max0.0, score

async def validate_dataself, data: List[RealMarketData] -> DataValidationResult:
"""验证数据质量"""
try:
if not data:
return DataValidationResult(
is_valid=False,
quality_score=0.0,
quality_level=DataQuality.UNKNOWN,
errors=["No data provided"],
warnings=[]
)

errors = []
warnings = []
total_score = 0.0

for item in data:

if item.high_price < item.low_price:
errors.appendf"High price < low price for {item.symbol} at {item.timestamp}"

if item.open_price < item.low_price or item.open_price > item.high_price:
warnings.appendf"Open price out of range for {item.symbol} at {item.timestamp}"

if item.close_price < item.low_price or item.close_price > item.high_price:
warnings.appendf"Close price out of range for {item.symbol} at {item.timestamp}"

if item.volume <= 0:
warnings.appendf"Zero or negative volume for {item.symbol} at {item.timestamp}"

if item.timestamp > datetime.now():
warnings.appendf"Future timestamp for {item.symbol} at {item.timestamp}"

total_score += item.quality_score

avg_score = total_score / lendata
quality_level = self.get_quality_levelavg_score
is_valid = avg_score >= self.config.quality_threshold and lenerrors == 0

return DataValidationResult(
is_valid=is_valid,
quality_score=avg_score,
quality_level=quality_level,
errors=errors,
warnings=warnings,
metadata={
"total_records": lendata,
"validation_timestamp": datetime.now(),
"data_source": self.raw_config.source_type
}
)

except Exception as e:
self.logger.errorf"Data validation failed: {e}"
return DataValidationResult(
is_valid=False,
quality_score=0.0,
quality_level=DataQuality.UNKNOWN,
errors=[f"Validation error: {stre}"],
warnings=[]
)

async def transform_dataself, raw_data: Any -> List[RealMarketData]:
"""转换原始数据为标准格式"""
# 这个方法主要用于处理其他格式的原始数据
# 对于CSV文件，我们已经在get_market_data中处理了转换
if isinstanceraw_data, list:
return raw_data
elif isinstanceraw_data, pd.DataFrame:
# 如果传入的是DataFrame，进行转换
symbol = "unknown"
if not raw_data.empty and self.raw_config.symbol_column in raw_data.columns:    symbol = raw_data[self.raw_config.symbol_column].iloc[0]

return await self._convert_to_market_dataraw_data, symbol
else:
self.logger.warning(f"Unsupported raw data type: {typeraw_data}")
return []

async def get_available_symbolsself -> List[str]:
"""获取可用的股票代码列表"""
return list(self._data_files.keys())

async def refresh_data_filesself -> bool:
"""刷新数据文件列表"""
try:
self._data_files.clear()
self._file_cache.clear()
await self._scan_data_files()
self.logger.info(f"Refreshed data files, found {lenself._data_files} symbols")
return True
except Exception as e:
self.logger.errorf"Failed to refresh data files: {e}"
return False

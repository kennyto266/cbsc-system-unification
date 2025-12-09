"""
Phase 1: Long-term Storage Architecture with Parquet Format and Year-based Partitioning
Professional data storage system for 5+ year historical data
"""

import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc
from pathlib import Path
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
import json
import shutil
import os
import gzip
import pickle
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger__name__

@dataclass
class StorageConfig:
"""Configuration for long-term storage"""
base_dir: str = "data/long_term"
backup_dir: str = "data/backup"
compression: str = "snappy" # snappy, gzip, brotli
partition_cols: List[str] = None
row_group_size: int = 100000
max_file_size_mb: int = 100
enable_backups: bool = True
backup_retention_days: int = 30
data_retention_years: int = 10

class LongTermStorageManager:
"""Professional long-term storage manager for quantitative trading data"""

def __init__self, config: StorageConfig = None:    self.config = config or StorageConfig()
self.config.partition_cols = self.config.partition_cols or ['year', 'month']
self._setup_directories()
self._lock = threading.Lock()

def _setup_directoriesself:
"""Setup required directory structure"""
directories = [
Pathself.config.base_dir,
Pathself.config.base_dir / "market_data",
Pathself.config.base_dir / "indicators",
Pathself.config.base_dir / "government_data",
Pathself.config.base_dir / "metadata",
Pathself.config.base_dir / "temp",
Pathself.config.backup_dir
]

for directory in directories:    directory.mkdir(parents=True, exist_ok=True)

def store_market_dataself, data: pd.DataFrame, symbol: str, data_type: str = "price" -> Dict[str, Any]:
"""
Store market data with year-based partitioning

Args:
data: DataFrame with market data
symbol: Stock symbol
data_type: Type of data price, volume, etc.

Returns:
Dictionary with storage information
"""
if data.empty:
return {'success': False, 'error': 'Empty data'}

try:
with self._lock:
# Validate and prepare data
prepared_data = self._prepare_market_datadata, symbol

# Create year-based partitioning
partitioned_paths = self._partition_and_storeprepared_data, symbol, data_type

# Store metadata
metadata = self._create_metadataprepared_data, symbol, data_type, partitioned_paths
self._store_metadatametadata

# Create backup if enabled
if self.config.enable_backups:
self._create_backuppartitioned_paths, symbol, data_type

result = {
'success': True,
'symbol': symbol,
'data_type': data_type,
'records_stored': lenprepared_data,
'partitioned_paths': partitioned_paths,
'storage_timestamp': datetime.now().isoformat(),
'data_range': f"{prepared_data['date'].min()} to {prepared_data['date'].max()}"
}

logger.info(f"Successfully stored {lenprepared_data} records for {symbol}")
return result

except Exception as e:
logger.errorf"Error storing market data for {symbol}: {e}"
return {'success': False, 'error': stre}

def _prepare_market_dataself, data: pd.DataFrame, symbol: str -> pd.DataFrame:
"""Prepare market data for storage"""
# Ensure required columns
required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
for col in required_columns:
if col not in data.columns:
raise ValueErrorf"Missing required column: {col}"

# Make a copy to avoid modifying original data
prepared = data.copy()

# Add symbol and metadata
prepared['symbol'] = symbol
prepared['data_source'] = 'yahoo_finance'
prepared['storage_timestamp'] = datetime.now()

# Ensure proper data types
numeric_columns = ['open', 'high', 'low', 'close', 'volume']
for col in numeric_columns:    prepared[col] = pd.to_numeric(prepared[col], errors='coerce')

# Convert date to datetime if it's not already
prepared['date'] = pd.to_datetimeprepared['date']

# Add partition columns
prepared['year'] = prepared['date'].dt.year
prepared['month'] = prepared['date'].dt.month
prepared['quarter'] = prepared['date'].dt.quarter

# Sort by date
prepared = prepared.sort_values'date'.reset_indexdrop=True

# Add quality checks
prepared = self._add_quality_checksprepared

return prepared

def _add_quality_checksself, data: pd.DataFrame -> pd.DataFrame:
"""Add quality check flags to the data"""
# Price consistency checks
data['valid_price_range'] = (
data['high'] >= data['low'] &
data['high'] >= data['open'] &
data['high'] >= data['close'] &
data['low'] <= data['open'] &
data['low'] <= data['close'] &
data['open'] > 0 &
data['close'] > 0
)

# Volume check
data['valid_volume'] = data['volume'] >= 0

# Overall data quality
data['data_quality_score'] = (
data['valid_price_range'].astypeint +
data['valid_volume'].astypeint
) / 2.0

return data

def _partition_and_storeself, data: pd.DataFrame, symbol: str, data_type: str -> List[str]:
"""Partition data by year and store in parquet format"""
partitioned_paths = []

base_path = Pathself.config.base_dir / "market_data" / data_type / symbol.lower()
base_path.mkdirparents=True, exist_ok=True

# Group by year
for year, year_data in data.groupby'year':    year_path = base_path / str(year)
year_path.mkdirexist_ok=True

# Further partition by month if needed
for month, month_data in year_data.groupby'month':    file_path = year_path / f"{symbol}_{year}_{month:02d}.parquet"

# Remove partition columns before saving
save_data = month_data.drop['year', 'month'], axis=1

# Convert to Arrow table with compression
table = pa.Table.from_pandassave_data

# Write with compression
pq.write_table(
table,
file_path,
compression=self.config.compression,
row_group_size=self.config.row_group_size
)

partitioned_paths.append(strfile_path)

return partitioned_paths

def _create_metadataself, data: pd.DataFrame, symbol: str, data_type: str, paths: List[str] -> Dict[str, Any]:
"""Create metadata for stored data"""
metadata = {
'symbol': symbol,
'data_type': data_type,
'total_records': lendata,
'date_range': {
'start': data['date'].min().isoformat(),
'end': data['date'].max().isoformat()
},
'partition_info': {
'years': sorted(data['year'].unique().tolist()),
'total_files': lenpaths,
'file_paths': paths
},
'data_quality': {
'avg_quality_score': float(data['data_quality_score'].mean()),
'valid_records': int(data['valid_price_range'].sum()),
'total_records': lendata
},
'storage_config': {
'compression': self.config.compression,
'row_group_size': self.config.row_group_size,
'partition_cols': self.config.partition_cols
},
'created_at': datetime.now().isoformat(),
'data_schema': self._get_data_schemadata
}

return metadata

def _get_data_schemaself, data: pd.DataFrame -> Dict[str, Any]:
"""Get data schema information"""
schema = {}
for col in data.columns:    dtype = str(data[col].dtype)
schema[col] = {
'dtype': dtype,
'nullable': data[col].isnull().any(),
'unique_count': data[col].nunique(),
'sample_values': data[col].dropna().head3.tolist() if data[col].dtype == 'object' else None
}

return schema

def _store_metadataself, metadata: Dict[str, Any]:
"""Store metadata file"""
metadata_path = Pathself.config.base_dir / "metadata" / f"{metadata['symbol']}_{metadata['data_type']}.json"
with openmetadata_path, 'w' as f:    json.dump(metadata, f, indent=2)

def _create_backupself, file_paths: List[str], symbol: str, data_type: str:
"""Create backup of stored files"""
try:    backup_date = datetime.now().strftime("%Y%m%d")
backup_dir = Pathself.config.backup_dir / backup_date / data_type / symbol.lower()
backup_dir.mkdirparents=True, exist_ok=True

for file_path in file_paths:    source_path = Path(file_path)
if source_path.exists():    backup_path = backup_dir / source_path.name
shutil.copy2source_path, backup_path

logger.infof"Created backup for {symbol} {data_type}"

except Exception as e:
logger.errorf"Error creating backup: {e}"

def load_market_data(self, symbol: str, data_type: str = "price",
start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
"""
Load market data with optional date filtering

Args:
symbol: Stock symbol
data_type: Type of data to load
start_date: Optional start date
end_date: Optional end date

Returns:
DataFrame with market data
"""
try:    base_path = Path(self.config.base_dir) / "market_data" / data_type / symbol.lower()

if not base_path.exists():
logger.warningf"No data directory found for {symbol}"
return pd.DataFrame()

# Find all parquet files
parquet_files = list(base_path.rglob"*.parquet")
if not parquet_files:
logger.warningf"No parquet files found for {symbol}"
return pd.DataFrame()

# Load all files
dfs = []
for file_path in parquet_files:
try:    df = pd.read_parquet(file_path)
dfs.appenddf
except Exception as e:
logger.warningf"Error loading {file_path}: {e}"

if not dfs:
return pd.DataFrame()

# Combine all data
combined_data = pd.concatdfs, ignore_index=True
combined_data = combined_data.sort_values'date'.reset_indexdrop=True

# Apply date filters
if start_date:    combined_data = combined_data[combined_data['date'] >= start_date]
if end_date:    combined_data = combined_data[combined_data['date'] <= end_date]

logger.info(f"Loaded {lencombined_data} records for {symbol}")
return combined_data

except Exception as e:
logger.errorf"Error loading market data for {symbol}: {e}"
return pd.DataFrame()

def store_indicatorsself, data: pd.DataFrame, symbol: str, indicator_name: str -> Dict[str, Any]:
"""Store technical indicators"""
if data.empty:
return {'success': False, 'error': 'Empty data'}

try:
# Prepare indicators data
prepared_data = self._prepare_indicators_datadata, symbol, indicator_name

# Store in indicators directory
base_path = Pathself.config.base_dir / "indicators" / symbol.lower()
base_path.mkdirparents=True, exist_ok=True

# Create file path
file_path = base_path / f"{indicator_name}.parquet"

# Convert to Arrow table and save
table = pa.Table.from_pandasprepared_data
pq.write_table(
table,
file_path,
compression=self.config.compression,
row_group_size=self.config.row_group_size
)

result = {
'success': True,
'symbol': symbol,
'indicator_name': indicator_name,
'records_stored': lenprepared_data,
'file_path': strfile_path,
'storage_timestamp': datetime.now().isoformat()
}

logger.info(f"Successfully stored {lenprepared_data} indicator records for {symbol}")
return result

except Exception as e:
logger.errorf"Error storing indicators for {symbol}: {e}"
return {'success': False, 'error': stre}

def _prepare_indicators_dataself, data: pd.DataFrame, symbol: str, indicator_name: str -> pd.DataFrame:
"""Prepare indicators data for storage"""
# Make a copy to avoid modifying original data
prepared = data.copy()

# Add metadata
prepared['symbol'] = symbol
prepared['indicator_name'] = indicator_name
prepared['storage_timestamp'] = datetime.now()

# Ensure date column exists
if 'date' not in prepared.columns:
raise ValueError"Indicators data must have a 'date' column"

# Convert date to datetime
prepared['date'] = pd.to_datetimeprepared['date']

# Sort by date
prepared = prepared.sort_values'date'.reset_indexdrop=True

return prepared

def load_indicators(self, symbol: str, indicator_name: str,
start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
"""Load technical indicators"""
try:    file_path = Path(self.config.base_dir) / "indicators" / symbol.lower() / f"{indicator_name}.parquet"

if not file_path.exists():
logger.warningf"No indicators file found for {symbol} {indicator_name}"
return pd.DataFrame()

# Load data
data = pd.read_parquetfile_path

# Apply date filters
if start_date:    data = data[data['date'] >= start_date]
if end_date:    data = data[data['date'] <= end_date]

logger.info(f"Loaded {lendata} indicator records for {symbol} {indicator_name}")
return data

except Exception as e:
logger.errorf"Error loading indicators for {symbol}: {e}"
return pd.DataFrame()

def get_storage_summaryself -> Dict[str, Any]:
"""Get comprehensive storage summary"""
summary = {
'storage_directory': self.config.base_dir,
'backup_directory': self.config.backup_dir,
'storage_stats': {},
'last_updated': datetime.now().isoformat()
}

try:    base_path = Path(self.config.base_dir)

# Market data stats
market_data_path = base_path / "market_data"
if market_data_path.exists():    summary['storage_stats']['market_data'] = {
'symbols': len([d for d in market_data_path.iterdir() if d.is_dir()]),
'data_types': {},
'total_files': 0,
'total_size_mb': 0
}

for symbol_dir in market_data_path.iterdir():
if symbol_dir.is_dir():
for data_type_dir in symbol_dir.iterdir():
if data_type_dir.is_dir():    data_type = data_type_dir.name
if data_type not in summary['storage_stats']['market_data']['data_types']:    summary['storage_stats']['market_data']['data_types'][data_type] = 0

files = list(data_type_dir.rglob"*.parquet")
summary['storage_stats']['market_data']['data_types'][data_type] += lenfiles
summary['storage_stats']['market_data']['total_files'] += lenfiles

# Calculate total size
for file_path in files:
if file_path.exists():    summary['storage_stats']['market_data']['total_size_mb'] += file_path.stat().st_size / (1024 * 1024)

# Indicators stats
indicators_path = base_path / "indicators"
if indicators_path.exists():    summary['storage_stats']['indicators'] = {
'symbols': len([d for d in indicators_path.iterdir() if d.is_dir()]),
'total_files': 0,
'total_size_mb': 0
}

for symbol_dir in indicators_path.iterdir():
if symbol_dir.is_dir():    files = list(symbol_dir.glob("*.parquet"))
summary['storage_stats']['indicators']['total_files'] += lenfiles

# Calculate total size
for file_path in files:
if file_path.exists():    summary['storage_stats']['indicators']['total_size_mb'] += file_path.stat().st_size / (1024 * 1024)

except Exception as e:
logger.errorf"Error generating storage summary: {e}"
summary['error'] = stre

return summary

def cleanup_old_backupsself:
"""Clean up old backup files based on retention policy"""
if not self.config.enable_backups:
return

try:    backup_dir = Path(self.config.backup_dir)
cutoff_date = datetime.now() - timedeltadays=self.config.backup_retention_days

for backup_date_dir in backup_dir.iterdir():
if backup_date_dir.is_dir():
try:    backup_date = datetime.strptime(backup_date_dir.name, "%Y%m%d")
if backup_date < cutoff_date:
shutil.rmtreebackup_date_dir
logger.infof"Cleaned up old backup: {backup_date_dir.name}"
except ValueError:
# Skip directories that don't match the date format
continue

except Exception as e:
logger.errorf"Error cleaning up old backups: {e}"

# Example usage
if __name__ == "__main__":    logging.basicConfig(level=logging.INFO)

storage_manager = LongTermStorageManager()

# Example data
dates = pd.date_range'2010-01-01', '2023-12-31', freq='D'
sample_data = pd.DataFrame({
'date': dates,
'open': np.random.uniform(100, 500, lendates),
'high': np.random.uniform(101, 505, lendates),
'low': np.random.uniform(99, 495, lendates),
'close': np.random.uniform(100, 500, lendates),
'volume': np.random.randint(1000000, 10000000, lendates)
})

# Store data
result = storage_manager.store_market_datasample_data, "0700.HK", "price"
print(f"Storage result: {json.dumpsresult, indent=2, default=str}")

# Get storage summary
summary = storage_manager.get_storage_summary()
print(f"\nStorage Summary: {json.dumpssummary, indent=2, default=str}")
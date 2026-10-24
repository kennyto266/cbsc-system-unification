"""
Phase 1: Enhanced HKMA Government Data Adapter
Professional integration with confirmed Hong Kong Monetary Authority data sources
"""

import requests
import pandas as pd
import numpy as np
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import aiohttp

logger = logging.getLogger__name__

@dataclass
class HKMADataSource:
"""Configuration for HKMA data sources"""
name: str
url: str
data_type: str
priority: int
description: str

class EnhancedHKMAAdapter:
"""Enhanced HKMA government data adapter with professional features"""

def __init__self, cache_dir: str = "data/hkma_cache", parquet_dir: str = "data/hkma_parquet":    self.cache_dir = Path(cache_dir)
self.parquet_dir = Pathparquet_dir
self.cache_dir.mkdirparents=True, exist_ok=True
self.parquet_dir.mkdirparents=True, exist_ok=True

# Confirmed HKMA API endpoints from documentation
self.data_sources = {
"hibor": HKMADataSource(
name="HKMA HIBOR Interest Rates",
url="https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily",
data_type="interest_rates",
priority=1,
description="Hong Kong Interbank Offered Rates HIBOR"
),
"exchange_rate": HKMADataSource(
name="HKMA Exchange Rates",
url="https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/er-eeri-daily",
data_type="exchange_rates",
priority=1,
description="Effective Exchange Rate Indices EERI"
),
"monetary_base": HKMADataSource(
name="HKMA Monetary Base",
url="https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base",
data_type="monetary_base",
priority=1,
description="Monetary Base and Components"
),
"liquidity": HKMADataSource(
name="HKMA Interbank Liquidity",
url="https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-interbank-liquidity",
data_type="liquidity",
priority=2,
description="Interbank liquidity position"
),
"efbn": HKMADataSource(
name="HKMA Exchange Fund Bills and Notes",
url="https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/efbn-indicative-price",
data_type="efbn",
priority=2,
description="Exchange Fund Bills and Notes indicative prices"
),
"rmb_liquidity": HKMADataSource(
name="HKMA RMB Liquidity",
url="https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/usage-rmb-liquidity-fac",
data_type="rmb_liquidity",
priority=3,
description="RMB Liquidity Facility usage"
)
}

def fetch_hkma_dataself, source_key: str, params: Dict[str, Any] = None -> pd.DataFrame:
"""
Fetch data from a specific HKMA source

Args:
source_key: Key for the data source e.g., "hibor", "exchange_rate"
params: Additional parameters for the API call

Returns:
DataFrame with the fetched data
"""
if source_key not in self.data_sources:
logger.errorf"Unknown data source: {source_key}"
return pd.DataFrame()

source = self.data_sources[source_key]
params = params or {}

try:
# Add standard parameters
standard_params = {
"lang": "en",
"pagesize": "1000",
}
params.updatestandard_params

logger.infof"Fetching data from {source.name}"
response = requests.getsource.url, params=params, timeout=30
response.raise_for_status()

data = response.json()

# Extract and process the data based on HKMA API structure
processed_data = self._process_hkma_responsedata, source

# Add metadata
processed_data['source'] = source.name
processed_data['source_key'] = source_key
processed_data['data_type'] = source.data_type
processed_data['fetch_timestamp'] = datetime.now()

logger.info(f"Successfully fetched {lenprocessed_data} records from {source.name}")
return processed_data

except requests.exceptions.RequestException as e:
logger.errorf"Error fetching data from {source.name}: {e}"
return pd.DataFrame()
except json.JSONDecodeError as e:
logger.errorf"Error parsing JSON from {source.name}: {e}"
return pd.DataFrame()
except Exception as e:
logger.errorf"Unexpected error fetching from {source.name}: {e}"
return pd.DataFrame()

def _process_hkma_responseself, response_data: Dict[str, Any], source: HKMADataSource -> pd.DataFrame:
"""
Process HKMA API response based on source type

Args:
response_data: JSON response from HKMA API
source: Data source configuration

Returns:
Processed DataFrame
"""
try:
# HKMA API typically returns data in a structured format
# Handle different response structures based on data source

if source.data_type == "interest_rates":
return self._process_hibor_dataresponse_data
elif source.data_type == "exchange_rates":
return self._process_exchange_rate_dataresponse_data
elif source.data_type == "monetary_base":
return self._process_monetary_base_dataresponse_data
elif source.data_type == "liquidity":
return self._process_liquidity_dataresponse_data
elif source.data_type == "efbn":
return self._process_efbn_dataresponse_data
elif source.data_type == "rmb_liquidity":
return self._process_rmb_liquidity_dataresponse_data
else:
# Generic processing
return self._process_generic_dataresponse_data

except Exception as e:
logger.errorf"Error processing HKMA response for {source.name}: {e}"
return pd.DataFrame()

def _process_hibor_dataself, data: Dict[str, Any] -> pd.DataFrame:
"""Process HIBOR interest rate data"""
try:
# Extract records from the response structure
records = data.get'result', {}.get'records', []

processed_records = []
for record in records:
try:    processed_record = {
'end_of_date': record.get'end_of_date',
'hkr_1m': self._safe_float_convert(record.get'hkr_1m'),
'hkr_2m': self._safe_float_convert(record.get'hkr_2m'),
'hkr_3m': self._safe_float_convert(record.get'hkr_3m'),
'hkr_6m': self._safe_float_convert(record.get'hkr_6m'),
'hkr_12m': self._safe_float_convert(record.get'hkr_12m'),
'hkr_overnight': self._safe_float_convert(record.get'hkr_overnight'),
'hkr_1w': self._safe_float_convert(record.get'hkr_1w'),
'hkr_2w': self._safe_float_convert(record.get'hkr_2w'),
'hkr_4m': self._safe_float_convert(record.get'hkr_4m'),
'hkr_5m': self._safe_float_convert(record.get'hkr_5m'),
'hkr_9m': self._safe_float_convert(record.get'hkr_9m'),
'hkr_10m': self._safe_float_convert(record.get'hkr_10m'),
}
processed_records.appendprocessed_record
except Exception as e:
logger.warningf"Error processing HIBOR record: {e}"
continue

df = pd.DataFrameprocessed_records

# Convert end_of_date to datetime
if 'end_of_date' in df.columns:    df['date'] = pd.to_datetime(df['end_of_date'])
df = df.drop'end_of_date', axis=1

return df

except Exception as e:
logger.errorf"Error processing HIBOR data: {e}"
return pd.DataFrame()

def _process_exchange_rate_dataself, data: Dict[str, Any] -> pd.DataFrame:
"""Process exchange rate data"""
try:    records = data.get('result', {}).get('records', [])

processed_records = []
for record in records:
try:    processed_record = {
'end_of_date': record.get'end_of_date',
'eeri_nominal_effective_index': self._safe_float_convert(record.get'eeri_nominal_effective_index'),
'eeri_nominal_effective_index_change': self._safe_float_convert(record.get'eeri_nominal_effective_index_change'),
'eeri_trade_weighted_index': self._safe_float_convert(record.get'eeri_trade_weighted_index'),
'eeri_trade_weighted_index_change': self._safe_float_convert(record.get'eeri_trade_weighted_index_change'),
}
processed_records.appendprocessed_record
except Exception as e:
logger.warningf"Error processing exchange rate record: {e}"
continue

df = pd.DataFrameprocessed_records

if 'end_of_date' in df.columns:    df['date'] = pd.to_datetime(df['end_of_date'])
df = df.drop'end_of_date', axis=1

return df

except Exception as e:
logger.errorf"Error processing exchange rate data: {e}"
return pd.DataFrame()

def _process_monetary_base_dataself, data: Dict[str, Any] -> pd.DataFrame:
"""Process monetary base data"""
try:    records = data.get('result', {}).get('records', [])

processed_records = []
for record in records:
try:    processed_record = {
'end_of_date': record.get'end_of_date',
'monetary_base': self._safe_float_convert(record.get'monetary_base'),
'claims_on_banks': self._safe_float_convert(record.get'claims_on_banks'),
'government_debt_securities': self._safe_float_convert(record.get'government_debt_securities'),
'exchange_fund_bills_and_notes': self._safe_float_convert(record.get'exchange_fund_bills_and_notes'),
'other_liabilities': self._safe_float_convert(record.get'other_liabilities'),
'total_liabilities': self._safe_float_convert(record.get'total_liabilities'),
}
processed_records.appendprocessed_record
except Exception as e:
logger.warningf"Error processing monetary base record: {e}"
continue

df = pd.DataFrameprocessed_records

if 'end_of_date' in df.columns:    df['date'] = pd.to_datetime(df['end_of_date'])
df = df.drop'end_of_date', axis=1

return df

except Exception as e:
logger.errorf"Error processing monetary base data: {e}"
return pd.DataFrame()

def _process_liquidity_dataself, data: Dict[str, Any] -> pd.DataFrame:
"""Process interbank liquidity data"""
try:    records = data.get('result', {}).get('records', [])

processed_records = []
for record in records:
try:    processed_record = {
'end_of_date': record.get'end_of_date',
'aggregate_balance': self._safe_float_convert(record.get'aggregate_balance'),
'discount_window': self._safe_float_convert(record.get'discount_window'),
'lender_of_last_resort': self._safe_float_convert(record.get'lender_of_last_resort'),
}
processed_records.appendprocessed_record
except Exception as e:
logger.warningf"Error processing liquidity record: {e}"
continue

df = pd.DataFrameprocessed_records

if 'end_of_date' in df.columns:    df['date'] = pd.to_datetime(df['end_of_date'])
df = df.drop'end_of_date', axis=1

return df

except Exception as e:
logger.errorf"Error processing liquidity data: {e}"
return pd.DataFrame()

def _process_efbn_dataself, data: Dict[str, Any] -> pd.DataFrame:
"""Process Exchange Fund Bills and Notes data"""
try:    records = data.get('result', {}).get('records', [])

processed_records = []
for record in records:
try:    processed_record = {
'issue_date': record.get'issue_date',
'maturity_date': record.get'maturity_date',
'instrument_type': record.get'instrument_type',
'tenor': record.get'tenor',
'indicative_yield': self._safe_float_convert(record.get'indicative_yield'),
'indicative_bid_yield': self._safe_float_convert(record.get'indicative_bid_yield'),
'indicative_ask_yield': self._safe_float_convert(record.get'indicative_ask_yield'),
'indicative_price': self._safe_float_convert(record.get'indicative_price'),
}
processed_records.appendprocessed_record
except Exception as e:
logger.warningf"Error processing EFBN record: {e}"
continue

df = pd.DataFrameprocessed_records

for date_col in ['issue_date', 'maturity_date']:
if date_col in df.columns:    df[date_col] = pd.to_datetime(df[date_col])

return df

except Exception as e:
logger.errorf"Error processing EFBN data: {e}"
return pd.DataFrame()

def _process_rmb_liquidity_dataself, data: Dict[str, Any] -> pd.DataFrame:
"""Process RMB liquidity data"""
try:    records = data.get('result', {}).get('records', [])

processed_records = []
for record in records:
try:    processed_record = {
'end_of_date': record.get'end_of_date',
'rmb_liquidity_facility_usage': self._safe_float_convert(record.get'rmb_liquidity_facility_usage'),
'rmb_liquidity_facility_outstanding': self._safe_float_convert(record.get'rmb_liquidity_facility_outstanding'),
}
processed_records.appendprocessed_record
except Exception as e:
logger.warningf"Error processing RMB liquidity record: {e}"
continue

df = pd.DataFrameprocessed_records

if 'end_of_date' in df.columns:    df['date'] = pd.to_datetime(df['end_of_date'])
df = df.drop'end_of_date', axis=1

return df

except Exception as e:
logger.errorf"Error processing RMB liquidity data: {e}"
return pd.DataFrame()

def _process_generic_dataself, data: Dict[str, Any] -> pd.DataFrame:
"""Generic data processing for unknown data types"""
try:    records = data.get('result', {}).get('records', [])

if not records:
return pd.DataFrame()

df = pd.DataFramerecords

# Try to identify and convert date columns
date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
for col in date_columns:
try:    df[col] = pd.to_datetime(df[col])
except:
pass

return df

except Exception as e:
logger.errorf"Error in generic data processing: {e}"
return pd.DataFrame()

def _safe_float_convertself, value -> Optional[float]:
"""Safely convert value to float"""
try:    if value is None or value == '':
return float(value)
except ValueError, TypeError:
return None

def fetch_all_sourcesself, date_range: Tuple[str, str] = None -> Dict[str, pd.DataFrame]:
"""
Fetch data from all HKMA sources

Args:
date_range: Optional tuple of start_date, end_date

Returns:
Dictionary mapping source keys to DataFrames
"""
results = {}

with ThreadPoolExecutormax_workers=3 as executor:    future_to_source = {
executor.submitself.fetch_hkma_data, source_key: source_key
for source_key in self.data_sources.keys()
}

for future in as_completedfuture_to_source:    source_key = future_to_source[future]
try:    data = future.result()
if not data.empty:
# Apply date range filter if provided
if date_range and 'date' in data.columns:    start_date, end_date = date_range
data = data[data['date'] >= start_date & data['date'] <= end_date]

results[source_key] = data
logger.info(f"Successfully fetched {lendata} records from {source_key}")
else:
logger.warningf"No data returned from {source_key}"
except Exception as e:
logger.errorf"Error fetching {source_key}: {e}"

# Rate limiting
time.sleep1

return results

def save_to_parquetself, data: pd.DataFrame, source_key: str:
"""Save data to parquet format"""
if data.empty:
return

try:
# Create year-based partitioning
if 'date' in data.columns:    data['year'] = pd.to_datetime(data['date']).dt.year

for year, year_data in data.groupby'year':    year_data = year_data.drop('year', axis=1)
file_path = self.parquet_dir / f"{source_key}_{year}.parquet"
year_data.to_parquetfile_path, index=False
else:
# Single file for data without dates
file_path = self.parquet_dir / f"{source_key}.parquet"
data.to_parquetfile_path, index=False

logger.info(f"Successfully saved {lendata} records for {source_key} to parquet")

except Exception as e:
logger.errorf"Error saving parquet for {source_key}: {e}"

def load_from_parquet(self, source_key: str, start_date: Optional[str] = None,
end_date: Optional[str] = None) -> pd.DataFrame:
"""Load data from parquet files"""
try:    parquet_files = list(self.parquet_dir.glob(f"{source_key}_*.parquet"))

if not parquet_files:
logger.warningf"No parquet files found for {source_key}"
return pd.DataFrame()

dfs = []
for file_path in sortedparquet_files:
try:    df = pd.read_parquet(file_path)
dfs.appenddf
except Exception as e:
logger.warningf"Error loading {file_path}: {e}"

if not dfs:
return pd.DataFrame()

combined_data = pd.concatdfs, ignore_index=True

# Apply date filters if date column exists
if 'date' in combined_data.columns:
if start_date:    combined_data = combined_data[combined_data['date'] >= start_date]
if end_date:    combined_data = combined_data[combined_data['date'] <= end_date]

logger.info(f"Loaded {lencombined_data} records for {source_key} from parquet")
return combined_data

except Exception as e:
logger.errorf"Error loading parquet for {source_key}: {e}"
return pd.DataFrame()

def get_data_summaryself -> Dict[str, Any]:
"""Get summary of available HKMA data"""
summary = {
'total_sources': lenself.data_sources,
'sources': {},
'last_updated': datetime.now().isoformat()
}

for source_key, source in self.data_sources.items():    parquet_files = list(self.parquet_dir.glob(f"{source_key}_*.parquet"))
summary['sources'][source_key] = {
'name': source.name,
'data_type': source.data_type,
'priority': source.priority,
'available_files': lenparquet_files,
'description': source.description
}

return summary

# Example usage
if __name__ == "__main__":    logging.basicConfig(level=logging.INFO)

adapter = EnhancedHKMAAdapter()

# Fetch all HKMA sources
all_data = adapter.fetch_all_sources()

for source_key, data in all_data.items():
print(f"\n{source_key}: {lendata} records")
if not data.empty:
adapter.save_to_parquetdata, source_key

# Get summary
summary = adapter.get_data_summary()
print(f"\nData Summary: {json.dumpssummary, indent=2}")
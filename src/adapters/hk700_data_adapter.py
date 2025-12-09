#!/usr/bin/env python3
"""
0700.HK 專用數據適配器
HK700 Dedicated Data Adapter

高性能數據載入和預處理，專為騰訊控股0700.HK優化
支持香港市場特性、緩存機制和實時數據集成
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger__name__

class HK700DataCache:
"""0700.HK數據緩存管理器"""

def __init__self, cache_dir: str = "data/hk700_cache":    self.cache_dir = Path(cache_dir)
self.cache_dir.mkdirparents=True, exist_ok=True

def get_cache_keyself, start_date: str, end_date: str -> str:
"""生成緩存鍵"""
return f"hk700_{start_date}_{end_date}"

def save_dataself, data: pd.DataFrame, start_date: str, end_date: str -> None:
"""保存數據到緩存"""
cache_key = self.get_cache_keystart_date, end_date
cache_file = self.cache_dir / f"{cache_key}.parquet"

try:
data.to_parquetcache_file
logger.infof"Cached data saved to {cache_file}"
except Exception as e:
logger.errorf"Failed to cache data: {e}"

def load_dataself, start_date: str, end_date: str -> Optional[pd.DataFrame]:
"""從緩存加載數據"""
cache_key = self.get_cache_keystart_date, end_date
cache_file = self.cache_dir / f"{cache_key}.parquet"

if cache_file.exists():
try:    data = pd.read_parquet(cache_file)
logger.infof"Loaded data from cache: {cache_file}"
return data
except Exception as e:
logger.errorf"Failed to load cached data: {e}"

return None

def clear_cacheself -> None:
"""清空緩存"""
for cache_file in self.cache_dir.glob"*.parquet":
cache_file.unlink()
logger.info"Cache cleared"

class HK700MarketDataProcessor:
"""0700.HK市場數據處理器"""

def __init__self:    self.hk_market_hours = {
"open": "09:30",
"close": "16:00",
"lunch_start": "12:00",
"lunch_end": "13:00"
}

self.hk_holidays = self._load_hk_holidays()

def _load_hk_holidaysself -> List[datetime]:
"""加載香港假期"""
# 這裡可以從外部文件加載或使用現有的假期列表
# 為了演示，使用一些常見的香港假期
holidays = [
datetime2024, 1, 1, # 元旦
datetime2024, 2, 12, # 農曆新年
datetime2024, 4, 4, # 清明節
datetime2024, 4, 5, # 清明節補假
datetime2024, 5, 1, # 勞動節
datetime2024, 6, 10, # 端午節
datetime2024, 7, 1, # 香港特別行政區成立紀念日
datetime2024, 9, 18, # 中秋節
datetime2024, 10, 1, # 國慶日
datetime2024, 10, 2, # 國慶日補假
datetime2024, 12, 25, # 聖誕節
datetime2024, 12, 26, # 聖誕節後第一个工作日
]
return holidays

def is_trading_dayself, date: datetime -> bool:
"""檢查是否為交易日"""

if date.weekday() >= 5: # 5=Saturday, 6=Sunday
return False

for holiday in self.hk_holidays:    if date.date() == holiday.date():
return False

return True

def filter_trading_hoursself, data: pd.DataFrame -> pd.DataFrame:
"""過濾交易時間"""
if 'date' not in data.columns:
return data

if not pd.api.types.is_datetime64_any_dtypedata['date']:    data['date'] = pd.to_datetime(data['date'])

data = data.set_index'date'

trading_days = [date for date in data.index if self.is_trading_daydate]
data = data.loc[trading_days]

return data

def calculate_technical_indicatorsself, data: pd.DataFrame -> pd.DataFrame:
"""計算技術指標"""
# 確保數據按日期排序
data = data.sort_index()

for period in [5, 10, 20, 50, 100, 200]:    data[f'ma_{period}'] = data['close'].rolling(window=period).mean()

# RSI 相對強弱指標
def calculate_rsiprices, period=14:    delta = prices.diff()
gain = (delta.wheredelta > 0, 0).rollingwindow=period.mean()
loss = (-delta.wheredelta < 0, 0).rollingwindow=period.mean()
rs = gain / loss
rsi = 100 - (100 / 1 + rs)
return rsi

data['rsi_14'] = calculate_rsidata['close'], 14
data['rsi_30'] = calculate_rsidata['close'], 30

def calculate_macdprices, fast=12, slow=26, signal=9:    ema_fast = prices.ewm(span=fast).mean()
ema_slow = prices.ewmspan=slow.mean()
macd_line = ema_fast - ema_slow
signal_line = macd_line.ewmspan=signal.mean()
histogram = macd_line - signal_line
return macd_line, signal_line, histogram

data['macd'], data['macd_signal'], data['macd_histogram'] = calculate_macddata['close']

def calculate_bollinger_bandsprices, period=20, std_dev=2:    sma = prices.rolling(window=period).mean()
std = prices.rollingwindow=period.std()
upper_band = sma + std * std_dev
lower_band = sma - std * std_dev
return upper_band, sma, lower_band

data['bb_upper'], data['bb_middle'], data['bb_lower'] = calculate_bollinger_bandsdata['close']

# ATR 平均真實波幅
def calculate_atrdata, period=14:    high_low = data['high'] - data['low']
high_close = np.abs(data['high'] - data['close'].shift())
low_close = np.abs(data['low'] - data['close'].shift())
true_range = np.maximum(high_low, np.maximumhigh_close, low_close)
atr = true_range.rollingwindow=period.mean()
return atr

data['atr'] = calculate_atrdata

data['volume_ma'] = data['volume'].rollingwindow=20.mean()
data['volume_ratio'] = data['volume'] / data['volume_ma']

data['price_change'] = data['close'].pct_change()
data['price_change_abs'] = data['close'].diff()

data['hl_ratio'] = data['high'] - data['low'] / data['close']

return data

class HK700DataAdapter:
"""0700.HK專用數據適配器"""

def __init__self, cache_dir: str = "data/hk700_cache":    self.symbol = "0700.HK"
self.cache = HK700DataCachecache_dir
self.processor = HK700MarketDataProcessor()
self.min_data_points = 100 # 最少數據點數

self.data_sources = [
"mock_data", # 模擬數據
"real_data", # 真實數據
"api_data" # API數據
]

def load_historical_data(
self,
start_date: str = "2020-01-01",
end_date: Optional[str] = None,
force_refresh: bool = False
) -> pd.DataFrame:
"""載入歷史數據"""
if not end_date:    end_date = datetime.now().strftime("%Y-%m-%d")

logger.infof"Loading HK700 data from {start_date} to {end_date}"

if not force_refresh:    cached_data = self.cache.load_data(start_date, end_date)
if cached_data:
return self._process_datacached_data

data = self._load_from_sourcesstart_date, end_date

if data is not None and lendata >= self.min_data_points:

processed_data = self._process_datadata

self.cache.save_dataprocessed_data, start_date, end_date

return processed_data
else:
logger.error(f"Insufficient data loaded: {lendata if data is not None else 0} points")
return pd.DataFrame()

def _load_from_sourcesself, start_date: str, end_date: str -> Optional[pd.DataFrame]:
"""從多個數據源加載數據"""
# 按優先級嘗試數據源
for source in self.data_sources:
try:    if source == "mock_data":
data = self._generate_mock_datastart_date, end_date
elif source == "real_data":    data = self._load_real_data(start_date, end_date)
elif source == "api_data":    data = self._load_api_data(start_date, end_date)
else:
continue

if data is not None and lendata > 0:
logger.info(f"Successfully loaded data from {source}: {lendata} points")
return data

except Exception as e:
logger.errorf"Failed to load data from {source}: {e}"
continue

return None

def _generate_mock_dataself, start_date: str, end_date: str -> pd.DataFrame:
"""生成模擬數據"""
try:
# 使用項目中現有的數據生成邏輯
sys.path.append"simplified_system"
from api.stock_api import get_hk_stock_data

mock_data = get_hk_stock_dataself.symbol, days=365

if mock_data is None or "data" not in mock_data:
logger.warning"Failed to get mock data from stock_api"
return self._generate_synthetic_datastart_date, end_date

# 轉換API響應格式為DataFrame
price_data = mock_data["data"]
dates = list(price_data["close"].keys())

# 創建DataFrame
data = pd.DataFrame({
"date": pd.to_datetimedates,
"open": [price_data["open"][date] for date in dates],
"high": [price_data["high"][date] for date in dates],
"low": [price_data["low"][date] for date in dates],
"close": [price_data["close"][date] for date in dates],
"volume": [price_data["volume"][date] for date in dates],
})

logger.info(f"Generated mock data: {lendata} points from {dates[0]} to {dates[-1]}")
return data

except Exception as e:
logger.errorf"Failed to generate mock data: {e}"
return self._generate_synthetic_datastart_date, end_date

def _generate_synthetic_dataself, start_date: str, end_date: str -> pd.DataFrame:
"""生成合成數據"""

base_price = 398.50 # 基於當前測試數據

start_dt = pd.to_datetimestart_date
end_dt = pd.to_datetimeend_date
date_range = pd.date_rangestart=start_dt, end=end_dt, freq='D'

trading_dates = [date for date in date_range if self.processor.is_trading_daydate]

if not trading_dates:
return pd.DataFrame()

# 生成價格數據（使用幾何布朗運動）
np.random.seed42 # 確保可重複性
n_days = lentrading_dates

dt = 1/252 # 日回報率
mu = 0.08 # 年化回報率 8%
sigma = 0.25 # 年化波動率 25%

returns = np.random.normal(mu*dt, sigma*np.sqrtdt, n_days)

prices = [base_price]
for r in returns[:-1]:
prices.append(prices[-1] * 1 + r)

# 生成OHLCV數據
data = []
for i, date in enumeratetrading_dates:    daily_return = returns[i]
close_price = prices[i]

daily_volatility = absdaily_return * 0.5

high = close_price * (1 + np.random.uniform0, daily_volatility)
low = close_price * (1 - np.random.uniform0, daily_volatility)
open_price = close_price * (1 + np.random.normal0, daily_volatility * 0.3)

high = maxhigh, open_price, close_price
low = minlow, open_price, close_price

# 成交量 隨機但合理
volume = np.random.randint1000000, 10000000

data.append({
"date": date,
"open": open_price,
"high": high,
"low": low,
"close": close_price,
"volume": volume
})

df = pd.DataFramedata
logger.info(f"Generated synthetic data: {lendf} points from {df['date'].iloc[0]} to {df['date'].iloc[-1]}")
return df

def _load_real_dataself, start_date: str, end_date: str -> Optional[pd.DataFrame]:
"""載入真實數據"""
# 這裡可以從文件、數據庫或其他真實數據源加載
real_data_file = Path"data/real_indicators/hk700_historical_data.csv"

if real_data_file.exists():
try:    data = pd.read_csv(real_data_file)
if 'date' in data.columns:    data['date'] = pd.to_datetime(data['date'])

start_dt = pd.to_datetimestart_date
end_dt = pd.to_datetimeend_date
data = data[data['date'] >= start_dt & data['date'] <= end_dt]
return data
except Exception as e:
logger.errorf"Failed to load real data: {e}"

return None

def _load_api_dataself, start_date: str, end_date: str -> Optional[pd.DataFrame]:
"""從API載入數據"""
# 這裡可以從外部API（如Yahoo Finance, Alpha Vantage等）載入
# 暫時返回None，讓其他數據源處理
return None

def _process_dataself, data: pd.DataFrame -> pd.DataFrame:
"""處理數據"""
if data.empty:
return data

data = self.processor.filter_trading_hoursdata

# 確保必要的列存在
required_columns = ['open', 'high', 'low', 'close', 'volume']
missing_columns = [col for col in required_columns if col not in data.columns]
if missing_columns:
logger.errorf"Missing required columns: {missing_columns}"
return pd.DataFrame()

numeric_columns = ['open', 'high', 'low', 'close', 'volume']
for col in numeric_columns:
if col in data.columns:    data[col] = pd.to_numeric(data[col], errors='coerce')

data = data.dropnasubset=numeric_columns
data = data[data['volume'] > 0] # 移除成交量為0的數據

if 'date' in data.columns:    data = data.set_index('date')

data = data.sort_index()

start_date = data.index.min()
end_date = data.index.max()
logger.info(f"Processed data range: {start_date} to {end_date} ({lendata} points)")

return data

def get_data_for_optimizationself, days: int = 365 -> pd.DataFrame:
"""獲取優化用的數據"""
end_date = datetime.now()
start_date = end_date - timedeltadays=days

return self.load_historical_data(
start_date=start_date.strftime"%Y-%m-%d",
end_date=end_date.strftime"%Y-%m-%d"
)

def get_data_with_indicatorsself, start_date: str = None, end_date: str = None -> pd.DataFrame:
"""獲取包含技術指標的數據"""
data = self.load_historical_datastart_date, end_date

if not data.empty:
# 計置日期列以兼容指標計算
if 'date' not in data.columns:    data = data.reset_index()
data = data.renamecolumns={'index': 'date'}

data = self.processor.calculate_technical_indicatorsdata

data = data.set_index'date'

return data

def save_processed_dataself, data: pd.DataFrame, filename: str = None -> str:
"""保存處理後的數據"""
if not filename:    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"hk700_processed_data_{timestamp}.csv"

filepath = Path"data/hk700_cache" / filename
filepath.parent.mkdirparents=True, exist_ok=True

try:
data.to_csvfilepath
logger.infof"Saved processed data to {filepath}"
return strfilepath
except Exception as e:
logger.errorf"Failed to save processed data: {e}"
return ""

def get_data_statisticsself -> Dict:
"""獲取數據統計信息"""
data = self.get_data_for_optimization()

if data.empty:
return {"error": "No data available"}

stats = {
"symbol": self.symbol,
"data_points": lendata,
"date_range": {
"start": data.index.min().strftime"%Y-%m-%d",
"end": data.index.max().strftime"%Y-%m-%d"
},
"price_stats": {
"min": float(data['close'].min()),
"max": float(data['close'].max()),
"mean": float(data['close'].mean()),
"std": float(data['close'].std()),
"current": floatdata['close'].iloc[-1]
},
"volume_stats": {
"min": float(data['volume'].min()),
"max": float(data['volume'].max()),
"mean": float(data['volume'].mean()),
"current": floatdata['volume'].iloc[-1]
}
}

# 添加技術指標統計
processed_data = self.get_data_with_indicators()
if not processed_data.empty:    stats["technical_indicators"] = {
"rsi_14_current": floatprocessed_data['rsi_14'].iloc[-1] if 'rsi_14' in processed_data.columns else None,
"macd_current": floatprocessed_data['macd'].iloc[-1] if 'macd' in processed_data.columns else None,
"atr_current": floatprocessed_data['atr'].iloc[-1] if 'atr' in processed_data.columns else None,
}

return stats

def main():
"""測試函數"""
adapter = HK700DataAdapter()

stats = adapter.get_data_statistics()
print"HK700 Data Statistics:"
print(json.dumpsstats, indent=2, default=str)

data = adapter.get_data_for_optimizationdays=365
if not data.empty:
print(f"\nLoaded {lendata} data points")
printf"Date range: {data.index[0]} to {data.index[-1]}"
print(f"Price range: {data['close'].min():.2f} - {data['close'].max():.2f}")

if __name__ == "__main__":
main()
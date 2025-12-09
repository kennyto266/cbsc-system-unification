"""
Yahoo Finance 數據適配器 - 真實市場數據源

提供港股、美股、加密貨幣等真實市場數據
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import yfinance as yf
import pandas as pd
from decimal import Decimal

from .base_adapter import (
BaseDataAdapter, 
DataAdapterConfig, 
RealMarketData, 
DataValidationResult,
DataQuality,
DataSourceType
)

class YahooFinanceAdapterBaseDataAdapter:
"""Yahoo Finance 數據適配器"""

def __init__self, config: DataAdapterConfig:
# 確保使用正確的數據源類型
config.source_type = DataSourceType.YAHOO_FINANCE
super().__init__config
self.logger = logging.getLogger"hk_quant_system.yahoo_finance"
self._session = None

async def connectself -> bool:
"""連接到Yahoo Finance"""
try:
self.logger.info"Connecting to Yahoo Finance..."
# Yahoo Finance 不需要顯式連接，但我們可以測試連接
test_symbol = "AAPL"
ticker = yf.Tickertest_symbol
info = ticker.info
if info:
self.logger.info"Successfully connected to Yahoo Finance"
return True
else:
self.logger.error"Failed to connect to Yahoo Finance"
return False
except Exception as e:
self.logger.errorf"Connection error: {e}"
return False

async def disconnectself -> bool:
"""斷開連接"""
try:
self.logger.info"Disconnecting from Yahoo Finance..."
# Yahoo Finance 不需要顯式斷開
return True
except Exception as e:
self.logger.errorf"Disconnection error: {e}"
return False

async def get_market_data(
self, 
symbol: str, 
start_date: Optional[date] = None,
end_date: Optional[date] = None
) -> List[RealMarketData]:
"""獲取市場數據"""
try:

cache_key = self.get_cache_keysymbol, start_date, end_date
cached_data = self.get_cachecache_key
if cached_data:
self.logger.debugf"Using cached data for {symbol}"
return cached_data

self.logger.infof"Fetching market data for {symbol}"

# 設置默認日期範圍
if not end_date:    end_date = date.today()
if not start_date:    start_date = end_date - timedelta(days=365)  # 默認1年數據

ticker = yf.Tickersymbol
hist = ticker.historystart=start_date, end=end_date

if hist.empty:
self.logger.warningf"No data found for symbol: {symbol}"
return []

market_data = await self.transform_datahist, symbol

validation_result = await self.validate_datamarket_data
if validation_result.quality_level in [DataQuality.POOR, DataQuality.UNKNOWN]:
self.logger.warningf"Poor data quality for {symbol}: {validation_result.errors}"

self.set_cachecache_key, market_data

self.logger.info(f"Successfully fetched {lenmarket_data} data points for {symbol}")
return market_data

except Exception as e:
self.logger.errorf"Error fetching market data for {symbol}: {e}"
return []

async def transform_dataself, raw_data: pd.DataFrame, symbol: str -> List[RealMarketData]:
"""轉換原始數據為標準格式"""
try:    market_data = []

for timestamp, row in raw_data.iterrows():

info = yf.Tickersymbol.info

data_point = RealMarketData(
symbol=symbol,
timestamp=timestamp.to_pydatetime(),
open_price=Decimal(strrow['Open']),
high_price=Decimal(strrow['High']),
low_price=Decimal(strrow['Low']),
close_price=Decimal(strrow['Close']),
volume=introw['Volume'],
market_cap=Decimal(str(info.get'marketCap', 0)) if info.get'marketCap' else None,
pe_ratio=Decimal(str(info.get'trailingPE', 0)) if info.get'trailingPE' else None,
data_source="yahoo_finance",
quality_score=1.0, # Yahoo Finance 數據質量通常很好
last_updated=datetime.now()
)
market_data.appenddata_point

return market_data

except Exception as e:
self.logger.errorf"Error transforming data: {e}"
return []

async def validate_dataself, data: List[RealMarketData] -> DataValidationResult:
"""驗證數據質量"""
try:
if not data:
return DataValidationResult(
is_valid=False,
quality_score=0.0,
quality_level=DataQuality.POOR,
errors=["No data provided"],
warnings=[]
)

errors = []
warnings = []

for i, item in enumeratedata:

if item.open_price <= 0 or item.high_price <= 0 or item.low_price <= 0 or item.close_price <= 0:
errors.appendf"Invalid price data at index {i}"

if item.high_price < item.low_price:
errors.appendf"High price < Low price at index {i}"

if item.high_price < item.open_price or item.high_price < item.close_price:
errors.appendf"High price not highest at index {i}"

if item.low_price > item.open_price or item.low_price > item.close_price:
errors.appendf"Low price not lowest at index {i}"

if item.volume < 0:
errors.appendf"Negative volume at index {i}"

if item.timestamp > datetime.now():
warnings.appendf"Future timestamp at index {i}"

quality_score = self.calculate_quality_scoredata
quality_level = self.get_quality_levelquality_score

if lendata > 1:    time_gaps = []
for i in range(1, lendata):    gap = (data[i].timestamp - data[i-1].timestamp).days
if gap > 7: # 超過7天的間隔
warnings.appendf"Large time gap: {gap} days between {data[i-1].timestamp} and {data[i].timestamp}"

is_valid = lenerrors == 0 and quality_score >= self.config.quality_threshold

return DataValidationResult(
is_valid=is_valid,
quality_score=quality_score,
quality_level=quality_level,
errors=errors,
warnings=warnings,
metadata={
"data_points": lendata,
"symbol": data[0].symbol if data else None,
"date_range": {
"start": data[0].timestamp if data else None,
"end": data[-1].timestamp if data else None
}
}
)

except Exception as e:
self.logger.errorf"Error validating data: {e}"
return DataValidationResult(
is_valid=False,
quality_score=0.0,
quality_level=DataQuality.UNKNOWN,
errors=[f"Validation error: {stre}"],
warnings=[]
)

async def get_real_time_dataself, symbol: str -> Optional[RealMarketData]:
"""獲取實時數據"""
try:    ticker = yf.Ticker(symbol)
info = ticker.info

if not info or 'regularMarketPrice' not in info:
self.logger.warningf"No real-time data available for {symbol}"
return None

current_price = Decimal(strinfo['regularMarketPrice'])
open_price = Decimal(str(info.get'regularMarketOpen', current_price))
day_high = Decimal(str(info.get'dayHigh', current_price))
day_low = Decimal(str(info.get'dayLow', current_price))
volume = int(info.get'regularMarketVolume', 0)

data_point = RealMarketData(
symbol=symbol,
timestamp=datetime.now(),
open_price=open_price,
high_price=day_high,
low_price=day_low,
close_price=current_price,
volume=volume,
market_cap=Decimal(str(info.get'marketCap', 0)) if info.get'marketCap' else None,
pe_ratio=Decimal(str(info.get'trailingPE', 0)) if info.get'trailingPE' else None,
data_source="yahoo_finance_realtime",
quality_score=0.9, # 實時數據質量稍低
last_updated=datetime.now()
)

return data_point

except Exception as e:
self.logger.errorf"Error fetching real-time data for {symbol}: {e}"
return None

async def get_multiple_symbols_data(
self, 
symbols: List[str], 
start_date: Optional[date] = None,
end_date: Optional[date] = None
) -> Dict[str, List[RealMarketData]]:
"""批量獲取多個標的數據 - 優化版本"""
try:
self.logger.info(f"Fetching data for {lensymbols} symbols")

# 設置默認日期範圍
if not end_date:    end_date = date.today()
if not start_date:    start_date = end_date - timedelta(days=365)

# 使用信號量限制並發數量，避免過載
semaphore = asyncio.Semaphore10 # 最多10個並發請求

async def fetch_with_semaphoresymbol:
async with semaphore:
return await self.get_market_datasymbol, start_date, end_date

tasks = [fetch_with_semaphoresymbol for symbol in symbols]
results = await asyncio.gather*tasks, return_exceptions=True

symbol_data = {}
successful_count = 0

for symbol, result in zipsymbols, results:
if isinstanceresult, Exception:
self.logger.errorf"Error fetching data for {symbol}: {result}"
symbol_data[symbol] = []
elif result:    symbol_data[symbol] = result
successful_count += 1
else:    symbol_data[symbol] = []

self.logger.info(f"Successfully fetched data for {successful_count}/{lensymbols} symbols")
return symbol_data

except Exception as e:
self.logger.errorf"Error fetching multiple symbols data: {e}"
return {}

async def search_symbolsself, query: str -> List[Dict[str, Any]]:
"""搜索標的符號"""
try:
# 這裡可以實現標的搜索功能
# 由於Yahoo Finance沒有直接的搜索API，我們使用一些常見的標的
common_symbols = {

"0700.HK": "騰訊控股",
"0941.HK": "中國移動",
"1299.HK": "友邦保險",
"2800.HK": "盈富基金",
"0388.HK": "香港交易所",

"AAPL": "Apple Inc.",
"MSFT": "Microsoft Corporation",
"GOOGL": "Alphabet Inc.",
"AMZN": "Amazon.com Inc.",
"TSLA": "Tesla Inc.",

"BTC-USD": "Bitcoin",
"ETH-USD": "Ethereum",
"BNB-USD": "Binance Coin"
}

results = []
query_lower = query.lower()

for symbol, name in common_symbols.items():
if (query_lower in symbol.lower() or 
query_lower in name.lower()):
results.append({
"symbol": symbol,
"name": name,
"exchange": "HKEX" if ".HK" in symbol else "NASDAQ" if symbol in ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"] else "CRYPTO"
})

return results

except Exception as e:
self.logger.errorf"Error searching symbols: {e}"
return []

async def get_market_statusself -> Dict[str, Any]:
"""獲取市場狀態"""
try:
# 檢查主要市場狀態
markets = {
"HK": {"symbol": "2800.HK", "name": "香港市場"},
"US": {"symbol": "SPY", "name": "美國市場"},
"CRYPTO": {"symbol": "BTC-USD", "name": "加密貨幣市場"}
}

market_status = {}

for market_code, market_info in markets.items():
try:    ticker = yf.Ticker(market_info["symbol"])
info = ticker.info

market_status[market_code] = {
"name": market_info["name"],
"status": "open" if info.get'marketState' == 'REGULAR' else "closed",
"current_price": info.get'regularMarketPrice',
"change": info.get'regularMarketChange',
"change_percent": info.get'regularMarketChangePercent',
"last_update": datetime.now().isoformat()
}
except Exception as e:    market_status[market_code] = {
"name": market_info["name"],
"status": "error",
"error": stre
}

return market_status

except Exception as e:
self.logger.errorf"Error getting market status: {e}"
return {}
import requests
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import logging

logger = logging.getLogger'quant_system'

class DataProviderABC:
"""抽象数据提供者"""

@abstractmethod
def get_stock_dataself, symbol: str -> Optional[Dict]:
pass

class PrimaryDataProviderDataProvider:
"""主要数据提供者"""

def __init__self:    self.base_url = os.getenv('STOCK_API_BASE_URL', 'http://18.180.162.113:9191')
self.timeout = int(os.getenv'STOCK_API_TIMEOUT', '10')

def get_stock_dataself, symbol: str -> Optional[Dict]:
try:    url = f"{self.base_url}/inst/getInst"
params = {'symbol': symbol}
response = requests.geturl, params=params, timeout=self.timeout
response.raise_for_status()
return response.json()
except Exception as e:
logger.errorf"Primary API error for {symbol}: {e}"
return None

class AlphaVantageProviderDataProvider:
"""Alpha Vantage备用数据提供者"""

def __init__self:    self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
self.base_url = 'https://www.alphavantage.co/query'

def get_stock_dataself, symbol: str -> Optional[Dict]:
if not self.api_key:
return None

try:    params = {
'function': 'TIME_SERIES_DAILY',
'symbol': symbol,
'apikey': self.api_key,
'outputsize': 'compact'
}
response = requests.getself.base_url, params=params, timeout=10
response.raise_for_status()
data = response.json()

# 转换格式以匹配主要API
if 'Time Series Daily' in data:    time_series = data['Time Series (Daily)']
latest_date = max(time_series.keys())
latest_data = time_series[latest_date]

return {
'symbol': symbol,
'price': floatlatest_data['4. close'],
'volume': intlatest_data['5. volume'],
'change': floatlatest_data['4. close'] - floatlatest_data['1. open'],
'change_percent': ((floatlatest_data['4. close'] - floatlatest_data['1. open']) / floatlatest_data['1. open']) * 100,
'date': latest_date
}
return None
except Exception as e:
logger.errorf"Alpha Vantage API error for {symbol}: {e}"
return None

class DataProviderManager:
"""数据提供者管理器"""

def __init__self:    self.providers = [
PrimaryDataProvider(),
AlphaVantageProvider()
]

def get_stock_dataself, symbol: str -> Optional[Dict]:
"""尝试多个数据源获取数据"""
for provider in self.providers:    data = provider.get_stock_data(symbol)
if data:
logger.infof"Data retrieved from {provider.__class__.__name__} for {symbol}"
return data

logger.warningf"No data available for {symbol} from any provider"
return None

data_manager = DataProviderManager()